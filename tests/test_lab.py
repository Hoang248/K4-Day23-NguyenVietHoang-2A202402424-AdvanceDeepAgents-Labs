"""Offline regression tests; fixtures are synthetic and never submission reports."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from langchain_core.messages import AIMessage

import agents
import research
import tools
from check_citations import check
from finalize_citations import finalize


def fixture():
    sources = [
        {"n": 1, "id": "2401.00001", "url": "https://arxiv.org/abs/2401.00001", "title": "A", "date": "2024-01-01", "source": "arxiv"},
        {"n": 2, "id": "2401.00002", "url": "https://huggingface.co/papers/2401.00002", "title": "B", "date": "2024-01-02", "source": "hf-search"},
        {"n": 3, "id": "page", "url": "https://example.org/page", "title": "C", "date": "", "source": "web"},
    ]
    report, sources, problems = finalize("# Synthetic test\nClaims [1, 2][3].", sources)
    assert not problems
    return report, sources


class CitationTests(unittest.TestCase):
    def test_source_family_urls_must_match_before_download(self):
        report, sources = fixture()
        wrong_hf = [dict(source) for source in sources]
        wrong_hf[1]["url"] = "https://arxiv.org/abs/2401.00002"
        self.assertTrue(any("family hf-search requires canonical URL" in p for p in check(report, wrong_hf)))
        wrong_arxiv = [dict(source) for source in sources]
        wrong_arxiv[0]["url"] += "v2"
        self.assertTrue(any("family arxiv requires canonical URL" in p for p in check(report, wrong_arxiv)))
        invalid_family = [dict(source) for source in sources]
        invalid_family[0]["source"] = "unknown"
        self.assertTrue(any("invalid source family" in p for p in check(report, invalid_family)))

    def test_valid_finalizer_output_and_groups(self):
        report, sources = fixture()
        self.assertEqual(check(report.replace("[1][2][3]", "[1-3]"), sources), [])

    def test_missing_sources_and_heading(self):
        self.assertTrue(check("", []))
        self.assertTrue(check("Fact [1]", [{"n": 1, "url": "https://example.org"}]))

    def test_unknown_and_uncited(self):
        report, sources = fixture()
        problems = check(report.replace("Claims [1][2][3]", "Claims [9]"), sources)
        self.assertTrue(any("[9] cited" in p for p in problems))
        self.assertTrue(any("never cited" in p for p in problems))

    def test_duplicate_number_url_and_invalid_schema(self):
        report, sources = fixture()
        self.assertTrue(check(report, sources + [sources[0]]))
        for value in ({}, [None], [{"n": True, "url": "https://example.org"}], [{"n": 1, "url": "ftp://x"}]):
            self.assertTrue(check(report, value))

    def test_reference_mismatch_multiple_urls_missing_and_duplicate(self):
        report, sources = fixture()
        for changed in (report.replace("https://example.org/page", "https://example.org/wrong"),
                        report + "[3] extra https://example.org/page\n",
                        report.replace("C. web.", "C. https://example.org/other web."),
                        report[:report.index("[3] C.")]):
            self.assertTrue(check(changed, sources))

    def test_code_and_links_do_not_count(self):
        report, sources = fixture()
        report = report.replace("Claims [1][2][3]", "Claims [1][2]. `inline [3]`\n```\n[3]\n```\n~~~\n[3]\n~~~\n[3](https://example.org)")
        self.assertTrue(any("source [3] never cited" in p for p in check(report, sources)))


class RetryTests(unittest.TestCase):
    @patch("tools.time.sleep")
    @patch("tools.random.uniform", return_value=0.5)
    def test_backoff_cap_no_last_sleep(self, jitter, sleep):
        call = Mock(side_effect=tools.RetryableError("busy"))
        with self.assertRaises(tools.RetryableError):
            tools.with_retry(call, attempts=4, base=1, cap=3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1.5, 2.5, 3])
        self.assertEqual(call.call_count, 4)

    @patch("tools.time.sleep")
    def test_retry_after_and_recovery(self, sleep):
        call = Mock(side_effect=[tools.RetryableError("busy", 8), "ok"])
        self.assertEqual(tools.with_retry(call, cap=5), "ok")
        sleep.assert_called_once_with(5)

    def test_permanent_error_and_invalid_attempts(self):
        call = Mock(side_effect=ValueError("bad"))
        with self.assertRaises(ValueError):
            tools.with_retry(call)
        self.assertEqual(call.call_count, 1)
        with self.assertRaises(ValueError):
            tools.with_retry(call, attempts=0)

    @patch("tools.httpx.request")
    def test_http_transient_vs_permanent_and_transport(self, request):
        for status in (429, 500, 502, 503, 504):
            request.return_value = httpx.Response(status, headers={"Retry-After": "2"}, request=httpx.Request("GET", tools.ARXIV_URL))
            with self.assertRaises(tools.RetryableError) as caught:
                tools._request("GET", tools.ARXIV_URL)
            self.assertEqual(caught.exception.retry_after, 2)
        request.return_value = httpx.Response(401, request=httpx.Request("GET", tools.ARXIV_URL))
        with self.assertRaises(httpx.HTTPStatusError):
            tools._request("GET", tools.ARXIV_URL)
        request.side_effect = httpx.ConnectError("offline")
        with self.assertRaises(tools.RetryableError):
            tools._request("GET", tools.ARXIV_URL)


class SourceTests(unittest.TestCase):
    @patch("tools._request")
    def test_arxiv_normalization_and_sanitization(self, request):
        request.return_value = Mock(text='<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2401.12345v2</id><title> A\n B </title><summary> finding </summary><published>2024-01-02T00:00:00Z</published></entry></feed>')
        with patch("tools._last_arxiv_call", None):
            records = json.loads(tools.arxiv_search.invoke({"query": 'all:"world" AND model OR'}))
        self.assertEqual(records[0]["url"], "https://arxiv.org/abs/2401.12345")
        self.assertEqual(records[0]["title"], "A B")
        self.assertEqual(request.call_args.kwargs["params"]["search_query"], "all:world AND all:model")
        request.reset_mock()
        self.assertEqual(tools.arxiv_search.invoke({"query": '" : AND OR'}), "NO RESULTS")
        request.assert_not_called()

    @patch("tools._request", return_value=Mock())
    @patch("tools.time.monotonic", side_effect=[10, 11, 13])
    @patch("tools.time.sleep")
    def test_arxiv_spacing(self, sleep, monotonic, request):
        with patch("tools._last_arxiv_call", None):
            tools._arxiv_request({})
            tools._arxiv_request({})
        sleep.assert_called_once_with(2)

    @patch("tools._request")
    def test_hf_filter_sort_ai_summary_and_missing_id(self, request):
        request.return_value = Mock(json=lambda: [{"paper": {"id": "a", "title": "World Model", "summary": "old", "ai_summary": "new", "upvotes": 2}},
                                                  {"paper": {"id": "b", "title": "WORLD", "upvotes": 5}}, {"paper": {"title": "missing"}}])
        records = json.loads(tools.hf_daily_papers.invoke({"keyword": "world"}))
        self.assertEqual([r["id"] for r in records], ["b", "a"])
        self.assertEqual(json.loads(tools.hf_search_papers.invoke({"query": "world"}))[0]["summary"], "new")
        self.assertEqual(tools.hf_daily_papers.invoke({"keyword": "unrelated"}), "NO RESULTS")

    @patch("tools._request")
    def test_mcp_json_and_sse(self, request):
        payload = {"id": 1, "result": {"content": [{"type": "text", "text": "Evidence"}]}}
        for text in (json.dumps(payload), "event: message\ndata: " + json.dumps(payload) + "\n\n"):
            request.return_value = Mock(text=text, json=lambda: payload, headers={})
            self.assertEqual(tools._mcp("web_fetch_exa", {"urls": ["https://example.org"]}), "Evidence")

    @patch("tools._request")
    def test_mcp_rate_limit_200_and_errors(self, request):
        for payload in ({"id": 1, "result": {"_meta": {"rateLimited": True}, "content": []}},
                        {"id": 1, "result": {"content": [{"type": "text", "text": "Rate limit exceeded"}]}},
                        {"id": 1, "result": {"isError": True, "content": [{"type": "text", "text": "Service error: rate limit reached"}]}}):
            request.return_value = Mock(text=json.dumps(payload), json=lambda: payload, headers={})
            with self.assertRaises(tools.RetryableError):
                tools._mcp("web_search_exa", {})
        payload = {"id": 1, "error": {"code": -1, "message": "invalid"}}
        request.return_value = Mock(text=json.dumps(payload), json=lambda: payload, headers={})
        with self.assertRaises(ValueError):
            tools._mcp("web_search_exa", {})

    @patch("tools._request")
    def test_inactive_rate_limit_flag_is_success(self, request):
        payload = {"id": 1, "result": {"_meta": {"rateLimited": False}, "content": [{"type": "text", "text": "Evidence"}]}}
        request.return_value = Mock(text=json.dumps(payload), json=lambda: payload, headers={})
        self.assertEqual(tools._mcp("web_fetch_exa", {}), "Evidence")

    @patch("tools._request")
    def test_source_prose_about_rate_limits_is_not_a_service_error(self, request):
        text = "API evaluation: rate limit exceeded errors are measured in the benchmark."
        payload = {"id": 1, "result": {"content": [{"type": "text", "text": text}]}}
        request.return_value = Mock(text=json.dumps(payload), json=lambda: payload, headers={})
        self.assertEqual(tools._mcp("web_fetch_exa", {}), text)

    @patch("tools._mcp")
    @patch("tools._direct_fetch", return_value="Primary abstract: 4 NLP benchmarks.")
    def test_primary_academic_html_precedes_mcp_extraction(self, direct, mcp):
        self.assertEqual(tools.web_fetch.invoke({"url": "https://arxiv.org/abs/2305.02301"}),
                         "Primary abstract: 4 NLP benchmarks.")
        direct.assert_called_once_with("https://arxiv.org/abs/2305.02301")
        mcp.assert_not_called()

    @patch("tools._mcp")
    def test_exa_arguments_truncation_and_redaction(self, mcp):
        mcp.return_value = "x" * 13000
        self.assertEqual(len(tools.web_fetch.invoke({"url": "https://example.org"})), 12000)
        self.assertEqual(mcp.call_args.args[1], {"urls": ["https://example.org"]})
        tools.web_search.invoke({"query": "world"})
        self.assertTrue(mcp.call_args.args[1]["objective"])
        with patch.dict("os.environ", {"EXA_API_KEY": "fixture/private"}):
            mcp.side_effect = ValueError("fixture/private fixture%2Fprivate")
            self.assertNotIn("fixture", tools.web_fetch.invoke({"url": "https://example.org"}))

    @patch("tools._request", side_effect=ValueError("bad response"))
    def test_all_tools_return_error_not_raise(self, request):
        with patch("tools._last_arxiv_call", None):
            for tool, args in ((tools.arxiv_search, {"query": "a"}), (tools.hf_daily_papers, {}),
                               (tools.hf_search_papers, {"query": "a"}), (tools.web_search, {"query": "a"}),
                               (tools.web_fetch, {"url": "https://example.org"})):
                self.assertTrue(tool.invoke(args).startswith("ERROR:"))

    @patch("tools.time.sleep")
    @patch("tools._request")
    @patch("tools._mcp", side_effect=tools.RetryableError("HTTP 429"))
    def test_fetch_transient_fallback_reads_visible_html(self, mcp, request, sleep):
        request.return_value = httpx.Response(200, headers={"Content-Type": "text/html"},
            text='<title>Paper</title><script>fake claim</script><style>hidden</style><p>Result &amp; scope.</p>',
            request=httpx.Request("GET", "https://example.org/paper"))
        result = tools.web_fetch.invoke({"url": "https://example.org/paper"})
        self.assertIn("Result & scope.", result)
        self.assertNotIn("fake claim", result)
        self.assertNotIn("hidden", result)
        self.assertEqual(mcp.call_count, 3)

    @patch("tools._request")
    def test_direct_fetch_rejects_binary_and_empty_pages(self, request):
        for kind, body in (("application/pdf", "binary"), ("text/html", "<script>hidden</script>")):
            request.return_value = httpx.Response(200, headers={"Content-Type": kind}, text=body,
                request=httpx.Request("GET", "https://example.org/page"))
            if kind == "application/pdf":
                with self.assertRaises(ValueError):
                    tools._direct_fetch("https://example.org/page")
            else:
                self.assertEqual(tools._direct_fetch("https://example.org/page"), "NO RESULTS")

    @patch("tools.time.sleep")
    @patch("tools._request")
    @patch("tools._mcp", side_effect=tools.RetryableError("HTTP 429"))
    def test_search_uses_same_openai_model_and_cited_urls_after_exa_limit(self, mcp, request, sleep):
        data = {"status": "completed", "output": [{"type": "web_search_call", "status": "completed"},
            {"type": "message", "content": [{"type": "output_text", "text": "Evidence", "annotations": [
                {"type": "url_citation", "url": "https://example.org/paper", "title": "Paper"}]}]}]}
        request.return_value = Mock(json=lambda: data)
        with patch.dict("os.environ", {"LAB_MODEL": "openai:gpt-6-luna", "OPENAI_API_KEY": "fixture", "LAB_BASE_URL": "", "OPENAI_ENDPOINT": ""}):
            result = json.loads(tools.web_search.invoke({"query": "topic"}))
        self.assertEqual(result["sources"][0]["url"], "https://example.org/paper")
        self.assertEqual(request.call_args.kwargs["json"]["model"], "gpt-6-luna")
        self.assertEqual(mcp.call_count, 3)
        data["status"] = "incomplete"
        with patch.dict("os.environ", {"OPENAI_API_KEY": "fixture"}):
            with self.assertRaises(ValueError):
                tools._openai_search("topic", "", 3, "gpt-6-luna")


class RunnerTests(unittest.TestCase):
    def test_luna_uses_responses_for_tool_calling(self):
        from langchain_openai import ChatOpenAI
        original = ChatOpenAI(model="gpt-6-luna", api_key="fixture")
        configured = research.configure_model(original)
        self.assertTrue(configured.use_responses_api)
        self.assertEqual(configured.model_name, "gpt-6-luna")
        self.assertEqual(configured.root_client.timeout, 120)
        self.assertEqual(configured.root_async_client.timeout, 120)
        self.assertEqual(configured.root_client.max_retries, 2)
        bound = configured.bind_tools([tools.web_search])
        payload = configured._get_request_payload([{"role": "user", "content": "Search"}], **bound.kwargs)
        self.assertIn("input", payload)
        self.assertEqual(payload["tools"][0]["type"], "function")
        other = ChatOpenAI(model="gpt-4.1-mini", api_key="fixture")
        self.assertIs(research.configure_model(other), other)

    def messages(self):
        return [AIMessage(content="", tool_calls=[{"name": "task", "args": {}, "id": str(i)} for i in range(3)],
                          usage_metadata={"input_tokens": 5, "output_tokens": 2, "total_tokens": 7})]

    def test_slug_safe_and_bounded(self):
        for text in ("../../x", "", "a" * 100, "こんにちは world", "___"):
            slug = research.slugify(text)
            self.assertTrue(slug and len(slug) <= 60 and "/" not in slug and "\\" not in slug)

    def test_summary_actual_usage_and_unknown(self):
        meta = research.summarize(self.messages(), 1.26, "fixture")
        self.assertEqual((meta["subagent_calls"], meta["tokens"], meta["elapsed_s"]), (3, {"input": 5, "output": 2}, 1.3))
        self.assertIsNone(research.summarize([], 0, "fixture")["tokens"]["input"])

    @patch("research.download")
    def test_save_preserves_sandbox_bytes_and_meta(self, download):
        report, sources = fixture()
        raw = json.dumps(sources).encode()
        download.return_value = {research.REPORT_PATH: report.encode(), research.SOURCES_PATH: raw}
        with tempfile.TemporaryDirectory() as directory:
            path = research.save_outputs(None, "Fixture", self.messages(), 1, "fixture", directory)
            self.assertEqual(path.read_bytes(), report.encode())
            self.assertEqual(path.with_suffix(".sources.json").read_bytes(), raw)
            meta = json.loads(path.with_suffix(".meta.json").read_text())
            self.assertEqual(meta["source_families"], ["arxiv", "hf-search", "web"])

    @patch("research.download")
    def test_invalid_run_writes_nothing(self, download):
        report, sources = fixture()
        for files in ({}, {research.REPORT_PATH: b" ", research.SOURCES_PATH: b"[]"},
                      {research.REPORT_PATH: report.encode(), research.SOURCES_PATH: b"bad"},
                      {research.REPORT_PATH: report.encode(), research.SOURCES_PATH: b"{}"}):
            download.return_value = files
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(RuntimeError):
                    research.save_outputs(None, "fixture", [], 1, "fixture", directory)
                self.assertEqual(list(Path(directory).iterdir()), [])

    @patch("research.download")
    def test_save_failure_rolls_back(self, download):
        report, sources = fixture()
        download.return_value = {research.REPORT_PATH: report.encode(), research.SOURCES_PATH: json.dumps(sources).encode()}
        real_replace = research.os.replace
        calls = 0
        def fail_second(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("fixture write failure")
            real_replace(source, destination)
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "fixture.md"
            original.write_bytes(b"original")
            with patch("research.os.replace", side_effect=fail_second):
                with self.assertRaises(OSError):
                    research.save_outputs(None, "fixture", self.messages(), 1, "fixture", directory)
            self.assertEqual(original.read_bytes(), b"original")
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    @patch("research.make_model", side_effect=RuntimeError("missing config"))
    def test_cli_failures(self, make_model):
        self.assertEqual(research.main(""), 2)
        self.assertEqual(research.main("fixture"), 1)

    def test_agent_limits_and_compilation(self):
        specs = agents.build_subagents()
        self.assertTrue(all(len(s["middleware"]) == 2 for s in specs))
        from langchain_openai import ChatOpenAI
        from deepagents.backends import StateBackend
        graph = agents.build_lead_agent(StateBackend(), ChatOpenAI(model="fixture", api_key="fixture"))
        self.assertIsNotNone(graph)

    @patch("research.save_outputs", return_value=Path("fixture.md"))
    @patch("research.build_lead_agent")
    @patch("research.upload")
    @patch("research.open_sandbox")
    @patch("research.make_model", return_value=Mock())
    def test_main_sandbox_lifecycle_and_validation_order(self, model, sandbox, upload, build, save):
        backend = Mock()
        backend.execute.return_value = Mock(exit_code=0, output="OK")
        context = sandbox.return_value
        context.__enter__.return_value = backend
        build.return_value.invoke.return_value = {"messages": self.messages()}
        self.assertEqual(research.main("fixture"), 0)
        commands = [call.args[0] for call in backend.execute.call_args_list]
        self.assertIn("mkdir -p", commands[0])
        self.assertEqual(commands[1:], [f"python3 {research.FINALIZER_PATH}", f"python3 {research.VALIDATOR_PATH}"])
        self.assertEqual(set(upload.call_args.args[1]), {research.FINALIZER_PATH, research.VALIDATOR_PATH})
        self.assertEqual(build.return_value.invoke.call_args.kwargs["config"]["recursion_limit"], 1000)
        context.__exit__.assert_called_once()

    @patch("research.save_outputs")
    @patch("research.build_lead_agent")
    @patch("research.upload")
    @patch("research.open_sandbox")
    @patch("research.make_model", return_value=Mock())
    def test_main_failure_cleans_up_and_does_not_save(self, model, sandbox, upload, build, save):
        backend = Mock()
        backend.execute.return_value = Mock(exit_code=0)
        context = sandbox.return_value
        context.__enter__.return_value = backend
        build.return_value.invoke.side_effect = RuntimeError("graph failed")
        self.assertEqual(research.main("fixture"), 1)
        context.__exit__.assert_called_once()
        save.assert_not_called()

    @patch("research.save_outputs")
    @patch("research.build_lead_agent")
    @patch("research.upload")
    @patch("research.open_sandbox")
    @patch("research.make_model", return_value=Mock())
    def test_invalid_recovery_candidate_stops_before_agent_and_cleans_up(self, model, sandbox, upload, build, save):
        backend = Mock()
        backend.execute.return_value = Mock(exit_code=0)
        context = sandbox.return_value
        context.__enter__.return_value = backend
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "report.md").write_bytes(b"Unvalidated candidate")
            (Path(directory) / "sources.json").write_bytes(b"{}")
            self.assertEqual(research.main("fixture", directory), 1)
        build.assert_not_called()
        save.assert_not_called()
        context.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
