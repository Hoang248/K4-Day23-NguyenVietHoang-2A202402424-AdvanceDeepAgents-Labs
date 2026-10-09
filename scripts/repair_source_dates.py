"""Restore two verified source dates in a validated sandbox, without an LLM call.

Model usage metadata is preserved; this deterministic correction is recorded
separately. Report and source bytes are downloaded verbatim after validation.
"""
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agents import FINALIZER_PATH, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH, WORKDIR
from sandbox import download, open_sandbox, upload


def main():
    stem = "survey-about-efficient-inference-and-small-language-models"
    fixes = [
        {"n": 14, "url": "https://huggingface.co/papers/2504.00002", "date": "2025-03-10",
         "visible_evidence": "Published on Mar 10, 2025"},
        {"n": 18, "url": "https://arxiv.org/html/2401.02385v2", "date": "2024-06-04",
         "visible_evidence": "arXiv:2401.02385v2 [cs.CL] 04 Jun 2024"},
    ]
    paths = {suffix: ROOT / "reports" / (stem + suffix) for suffix in (".md", ".sources.json", ".meta.json")}
    before = {suffix: path.read_bytes() for suffix, path in paths.items()}
    meta = json.loads(before[".meta.json"])
    if "citation_metadata_repair" in meta:
        raise RuntimeError("dates already repaired; inspect before repeating")
    for fix in fixes:
        response = httpx.get(fix["url"], timeout=30, follow_redirects=True)
        response.raise_for_status()
        # Strip tags without changing the verified text or parsing generated summaries.
        from audit_sources import Page
        page = Page()
        page.feed(response.text)
        if fix["visible_evidence"] not in " ".join(page.text):
            raise RuntimeError("primary date evidence unavailable; write nothing")
    code = """import json
from pathlib import Path
path = Path('/tmp/work/research/sources.json')
sources = json.loads(path.read_text())
fixes = json.loads(Path('/tmp/work/date-fixes.json').read_text())
for fix in fixes:
    source = next(s for s in sources if s['n'] == fix['n'])
    assert source['url'] == fix['url'] and source['date'] == '', 'unexpected source baseline'
    source['date'] = fix['date']
path.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')
"""
    with open_sandbox() as backend:
        upload(backend, {REPORT_PATH: before[".md"], SOURCES_PATH: before[".sources.json"],
                         FINALIZER_PATH: (ROOT / "finalize_citations.py").read_bytes(),
                         VALIDATOR_PATH: (ROOT / "check_citations.py").read_bytes(),
                         f"{WORKDIR}/date-fixes.json": json.dumps(fixes).encode(),
                         f"{WORKDIR}/repair_dates.py": code.encode()})
        for script in (f"{WORKDIR}/repair_dates.py", FINALIZER_PATH, VALIDATOR_PATH):
            result = backend.execute(f"python3 {script}")
            if result.exit_code:
                raise RuntimeError(result.output)
        files = download(backend, [REPORT_PATH, SOURCES_PATH])
        if not files.get(REPORT_PATH) or not files.get(SOURCES_PATH):
            raise RuntimeError("missing sandbox output; write nothing")
        meta["citation_metadata_repair"] = {
            "recorded_at": datetime.now(timezone.utc).isoformat(), "kind": "deterministic sandbox source-date correction",
            "changes": fixes, "llm_calls": 0,
            "before_sha256": {suffix: hashlib.sha256(raw).hexdigest() for suffix, raw in before.items()},
        }
        payloads = {".md": files[REPORT_PATH], ".sources.json": files[SOURCES_PATH],
                    ".meta.json": json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8")}
        replaced = []
        with tempfile.TemporaryDirectory(prefix=".date-repair-", dir=ROOT / "reports") as staging:
            for suffix, raw in payloads.items():
                (Path(staging) / (stem + suffix)).write_bytes(raw)
            try:
                for suffix, target in paths.items():
                    os.replace(Path(staging) / (stem + suffix), target)
                    replaced.append(suffix)
            except OSError:
                for suffix in reversed(replaced):
                    paths[suffix].write_bytes(before[suffix])
                raise
    print("Restored two verified dates; sandbox finalizer and validator passed; no LLM usage added.")


if __name__ == "__main__":
    main()
