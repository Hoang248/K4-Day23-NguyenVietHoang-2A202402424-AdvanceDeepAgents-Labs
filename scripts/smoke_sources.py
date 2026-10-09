"""Live, bounded source smoke test; no LLM, no submission artifacts.

Run from the repository root: python scripts/smoke_sources.py.
Use one attempt per endpoint to diagnose setup without long rate-limit waits.
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
import tools


def main():
    load_dotenv()
    retry = tools.with_retry
    failed = False
    with patch.object(tools, "with_retry", lambda fn, **kwargs: retry(fn, attempts=1)):
        for source, arguments in [
            (tools.arxiv_search, {"query": "world model", "max_results": 1}),
            (tools.hf_daily_papers, {"limit": 1}),
            (tools.hf_search_papers, {"query": "world model", "limit": 1}),
            (tools.web_search, {"query": "world models survey", "num_results": 1}),
            (tools.web_fetch, {"url": "https://arxiv.org/abs/1803.10122"}),
        ]:
            result = source.invoke(arguments)
            failed |= result.startswith("ERROR:")
            print(source.name + ": " + result[:350], flush=True)
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
