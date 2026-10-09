"""Retrieve public primary-source metadata for review; never modify reports."""
import concurrent.futures
import json
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.text = []
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.meta[attrs.get("name", attrs.get("property", ""))] = attrs.get("content", "")
        if tag in {"script", "style", "noscript", "template"}:
            self.hidden.append(tag)

    def handle_endtag(self, tag):
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.text.append(" ".join(data.split()))


def retrieve(url):
    result = {"url": url}
    for attempt in range(2):
        try:
            # Do not download large proceedings PDFs just to inspect headers.
            with httpx.stream("GET", url, timeout=25, follow_redirects=True) as response:
                result.update(status=response.status_code, final_url=str(response.url))
                if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                    time.sleep(3)
                    continue
                response.raise_for_status()
                if "html" not in response.headers.get("content-type", ""):
                    result["review_status"] = "non-HTML; verify with publisher abstract or full paper"
                    return result
                chunks, length = [], 0
                for chunk in response.iter_bytes():
                    chunks.append(chunk)
                    length += len(chunk)
                    if length > 2_000_000:
                        break
                html = b"".join(chunks).decode("utf-8", errors="replace")
            parser = Page()
            parser.feed(html)
            text = "\n".join(parser.text)
            meta = parser.meta
            title = meta.get("citation_title") or meta.get("og:title", "")
            result.update(title=title, metadata={k: v for k, v in meta.items()
                          if k.startswith("citation_") or k in {"article:published_time", "description"}},
                          text=text[:24000], review_status="retrieved; support still requires claim review")
            if "Verifying your browser" in text:
                result["review_status"] = "browser challenge; content unverified"
            if "arxiv.org/abs/" in str(response.url):
                match = re.search(r"Abstract:\s*(.*?)\n(?:Comments:|Subjects:|Cite as:)", text, re.S)
                result["abstract"] = match.group(1) if match else ""
                result["submission_history"] = text[text.find("Submission history"):][:1300]
            return result
        except (httpx.HTTPError, ValueError) as exc:
            result["review_status"] = "unverified retrieval failure"
            result["error_type"] = type(exc).__name__
    return result


def main():
    sources = {}
    for path in sorted((ROOT / "reports").glob("*.sources.json")):
        for source in json.loads(path.read_text(encoding="utf-8")):
            sources.setdefault(source["url"], []).append({"report": path.name, **source})
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(retrieve, url): refs for url, refs in sources.items()}
        for future in concurrent.futures.as_completed(futures):
            item = future.result()
            item["references"] = futures[future]
            results.append(item)
            print(f"{len(results)}/{len(sources)} {item.get('status')} {item['url']}", flush=True)
    target = ROOT / "docs/source-audit.json"
    recorded_at = datetime.now(timezone.utc).isoformat()
    target.write_text(json.dumps({"recorded_at": recorded_at,
                                 "sources": sorted(results, key=lambda x: x["url"]),
                                 "scope": "Public retrieval evidence, not an automatic factual endorsement."},
                                ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
    # Publish compact identity/retrieval evidence, not copied article bodies.
    fields = {"citation_title", "citation_author", "citation_publication_date", "citation_online_date",
              "citation_date", "citation_doi", "citation_conference_title", "citation_journal_title",
              "article:published_time"}
    compact = {"retrieved_at": recorded_at, "unique_urls": len(sources),
               "scope": "Retrieval and source identity evidence; see REPORT_REVIEW.md for claim review. HTTP 200 alone is not verification.",
               "sources": [{"url": item["url"], "final_url": item.get("final_url"),
                            "http_status": item.get("status"), "retrieved_title": item.get("title"),
                            "retrieval_status": item["review_status"],
                            "metadata": {k: v for k, v in item.get("metadata", {}).items() if k in fields},
                            "citations": [{"report": ref["report"], "n": ref["n"], "cited_date": ref.get("date")}
                                          for ref in item["references"]]} for item in sorted(results, key=lambda x: x["url"])]}
    (ROOT / "docs/source-review-receipt.json").write_text(json.dumps(compact, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
