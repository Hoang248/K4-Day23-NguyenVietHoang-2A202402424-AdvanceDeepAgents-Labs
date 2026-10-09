"""check_citations.py - STUDENT IMPLEMENTS `check`.   Runs INSIDE the sandbox (standard library only).

research.py uploads this file to the sandbox and the lead agent runs it with the `execute` tool:
    python3 /tmp/work/research/check_citations.py [report.md] [sources.json]
It must exit 0 and print "OK: ..." when the report is consistent, else print each problem and exit 1.
"""
import json
import re
import sys
from collections import Counter
from urllib.parse import urlsplit

REPORT = "/tmp/work/report/report.md"
SOURCES = "/tmp/work/research/sources.json"


def check(report_text, sources):
    """Return a list of problem strings (empty list = OK).

    PSEUDO-CODE:
      problems = []
      if sources is empty: return ["no sources in sources.json"]
      for each source entry:
          n must be an int                       -> problem if not
          url must start with http:// or https://-> problem if not
          the same url must not appear twice     -> problem if duplicated
      split report_text at the heading "## References":
          body = text before it; if the heading is missing -> problem
      cited = set of numbers found as [n] in the BODY only (not in the reference list; use a regex)
      every number in `cited` must exist in sources -> problem "[n] cited but missing from sources.json"
      every source number must be in `cited`        -> problem "source [n] never cited"
      the lines of the References section that start with "[n]" (regex) are the reference lines:
          every source needs exactly ONE reference line (none missing, no number twice, no number that is not a source)
          each reference line holds exactly ONE http(s) URL and it must equal that source's url
          (a line bundling several sources under one number is a problem)
      return problems
    """
    if not isinstance(sources, list) or not sources:
        return ["no sources in sources.json (expected a nonempty list)"]
    problems, by_n, urls = [], {}, set()
    for entry in sources:
        if not isinstance(entry, dict):
            problems.append("source must be an object")
            continue
        n, url = entry.get("n"), entry.get("url")
        if type(n) is not int or n < 1:
            problems.append("source n must be a positive integer")
            continue
        if n in by_n:
            problems.append(f"duplicate source number [{n}]")
        by_n[n] = entry
        try:
            valid_url = isinstance(url, str) and urlsplit(url).scheme in {"http", "https"} and bool(urlsplit(url).netloc)
        except ValueError:
            valid_url = False
        if not valid_url:
            problems.append(f"source [{n}] has invalid URL")
        elif url in urls:
            problems.append(f"duplicate URL for source [{n}]")
        else:
            urls.add(url)
        # If provenance is present, enforce the assignment's canonical tool/URL
        # contract in the sandbox so the lead can repair it before downloading.
        family = entry.get("source")
        if family is not None:
            if family not in {"arxiv", "hf-daily", "hf-search", "web"}:
                problems.append(f"source [{n}] has invalid source family")
            elif family != "web":
                identifier = entry.get("id")
                prefix = "https://arxiv.org/abs/" if family == "arxiv" else "https://huggingface.co/papers/"
                if not isinstance(identifier, str) or not identifier or url != prefix + identifier:
                    problems.append(f"source [{n}] family {family} requires canonical URL {prefix}<id>")
    # Remove code before looking for headings or citations. Links are not citations.
    visible = re.sub(r"(`{3,}.*?`{3,}|~{3,}.*?~{3,}|`+[^`\n]*`+)", "", report_text, flags=re.S)
    headings = list(re.finditer(r"(?m)^##[ \t]+References[ \t]*\r?$", visible))
    if not headings:
        problems.append("missing ## References heading")
        body, references = visible, ""
    else:
        if len(headings) != 1:
            problems.append("expected exactly one ## References heading")
        body, references = visible[:headings[0].start()], visible[headings[0].end():]
    cited = set()
    for match in re.finditer(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\](?![ \t]*\()", body):
        for part in re.split(r"\s*,\s*", match.group(1)):
            span = re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)", part)
            if span:
                a, b = map(int, span.groups())
                if not 0 <= b - a <= 200:
                    problems.append(f"invalid citation range [{part}]")
                else:
                    cited.update(range(a, b + 1))
            else:
                cited.add(int(part))
    for n in sorted(cited - by_n.keys()):
        problems.append(f"[{n}] cited but missing from sources.json")
    for n in sorted(by_n.keys() - cited):
        problems.append(f"source [{n}] never cited")
    counts = Counter()
    for match in re.finditer(r"(?m)^\[(\d+)\][ \t]+(.*)$", references):
        n, line = int(match.group(1)), match.group(2)
        counts[n] += 1
        found = re.findall(r"https?://[^\s<>\[\]()]+", line)
        if n not in by_n:
            problems.append(f"reference [{n}] has no source")
        elif len(found) != 1 or found[0] != by_n[n].get("url"):
            problems.append(f"reference [{n}] must contain exactly its source URL")
    for n in sorted(by_n):
        if counts[n] != 1:
            problems.append(f"source [{n}] needs exactly one reference line (found {counts[n]})")
    return problems


def main(argv):
    report_path = argv[1] if len(argv) > 1 else REPORT
    sources_path = argv[2] if len(argv) > 2 else SOURCES
    try:
        with open(report_path, encoding="utf-8") as f:
            report = f.read()
        with open(sources_path, encoding="utf-8") as f:
            sources = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"cannot read inputs: {exc}")
        return 1
    problems = check(report, sources)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"OK: {len(sources)} sources, all citations resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
