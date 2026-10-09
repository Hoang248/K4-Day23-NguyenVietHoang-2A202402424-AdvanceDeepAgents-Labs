"""Read-only submission checks and a durable receipt; no network or LLM calls."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import self_check


def main():
    commands = [
        [sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "self_check.py"],
        ["git", "diff", "--check"],
        ["git", "diff", "--exit-code", "--", "model.py", "sandbox.py", "self_check.py", "finalize_citations.py"],
    ]
    checks = []
    for argv in commands:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        checks.append({"command": argv, "exit_code": result.returncode,
                       "stdout": result.stdout, "stderr": result.stderr})
        print(f"exit {result.returncode}: {' '.join(argv)}")
        if result.stdout:
            print(result.stdout.strip())
    # Native self_check checks tracked files only. Also scan the untracked text
    # artifacts that will be submitted, without reading .env or printing matches.
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    suspicious = []
    for name in files:
        if name == ".env.example" or Path(name).suffix in {".png", ".jpg", ".pdf"}:
            continue
        try:
            content = (ROOT / name).read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        if self_check.KEY_LIKE.search(content):
            suspicious.append(name)
    checks.append({"check": "tracked and untracked submission text secret-pattern scan",
                   "exit_code": int(bool(suspicious)), "flagged_paths": suspicious})
    history = subprocess.run(["git", "log", "--all", "-p", "--format=commit %H"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    # Scan without printing matches; a receipt records only pass/fail.
    history_flagged = bool(self_check.KEY_LIKE.search(history.stdout))
    checks.append({"check": "all local Git history secret-pattern scan",
                   "exit_code": history.returncode or int(history_flagged),
                   "secret_pattern_detected": history_flagged})
    artifacts = []
    names = ["tools.py", "agents.py", "research.py", "check_citations.py", "model.py", "sandbox.py",
             "self_check.py", "finalize_citations.py", "tests/test_lab.py", "run_topics.py"]
    names += [str(path.relative_to(ROOT)).replace("\\", "/") for path in sorted((ROOT / "reports").glob("*")) if path.is_file()]
    for name in names:
        raw = (ROOT / name).read_bytes()
        artifacts.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    baseline = json.loads((ROOT / "docs/continuation-baseline.json").read_text(encoding="utf-8"))
    original_world = [item for item in baseline["artifacts"] if item["path"].startswith("reports/")]
    preserved = all(hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"] for item in original_world)
    world_meta = json.loads((ROOT / "reports/survey-about-world-model.meta.json").read_text(encoding="utf-8"))
    # An authorized later review can supersede the initial run. Preserve its
    # authentic metadata and baseline hashes in the measured repair lineage.
    lineage = world_meta.get("previous_artifacts", {})
    reviewed = world_meta.get("run_kind") == "bounded review repair of a genuine prior run" and all(
        lineage.get(item["path"].removeprefix("reports/survey-about-world-model")) == item["sha256"]
        for item in original_world)
    checks.append({"check": "initial world-model preserved or linked to validated review repair",
                   "exit_code": int(not (preserved or reviewed)),
                   "unchanged": preserved, "review_lineage_matches_baseline": reviewed})
    reports = []
    for topic in self_check.load_topics():
        path, meta = self_check.find_meta(topic, ROOT / "reports")
        reports.append({"topic": topic, "meta_path": str(path.relative_to(ROOT)) if path else None, "metadata": meta})
    receipt = {"recorded_at": datetime.now(timezone.utc).isoformat(), "checks": checks,
               "reports": reports, "artifacts": artifacts,
               "limits": "Regression tests, structural validation and pattern scan; see REPORT_REVIEW.md for claim review."
                         " Lead tokens exclude subagents, fallback search and failed runs; total cost is unknown."}
    target = ROOT / "docs/final-verification.json"
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Receipt: {target}")
    return int(any(check["exit_code"] for check in checks))


if __name__ == "__main__":
    sys.exit(main())
