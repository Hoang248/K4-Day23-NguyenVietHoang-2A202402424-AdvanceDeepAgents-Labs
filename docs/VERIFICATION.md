# Verification — 2026-10-09

The four student modules and all five genuine GPT-6 Luna + Docker surveys were reviewed and repaired. [FINAL_RUN.md](FINAL_RUN.md) links reports; [REPORT_REVIEW.md](REPORT_REVIEW.md) records factual corrections and retrieval limitations.

| Check | Observed result | Receipt |
|---|---|---|
| Offline unittest suite | 35 tests passed | final-verification.json includes native output and code/test hashes |
| scripts/verify_submission.py | Exit 0 | final-verification.json |
| Supplied self_check.py | Five topics OK; git/secrets OK | final-verification.json |
| git diff --check | Exit 0 | final-verification.json |
| Supplied model/sandbox/self_check/finalizer | Unchanged, diff exit 0 | final-verification.json |
| Submission text and all local Git history secret-pattern scans | No flagged paths or history matches | final-verification.json |
| Initial world-model triplet | Validated repair retains authentic original metadata and exact baseline hashes | final-verification.json |
| Lab Docker containers after review | No remaining names/status entries | docker-cleanup.json |
| Full report/reference reading and source-based review | Confirmed errors repaired; limited retrieval and conflicting paper values documented | REPORT_REVIEW.md and source-review-receipt.json |

Regression coverage includes retries, HTTP failures, arXiv shared spacing, HF records, JSON/SSE MCP, HTTP-200 limits, successful source prose mentioning rate limits, key redaction, primary HTML before transformed extraction, public fetch/search fallbacks, incomplete-evidence rejection, provenance URLs, citation consistency, downloaded bytes, rollback, actual metadata and sandbox lifecycle. Fixtures do not count as submission reports.

Anonymous Exa sometimes returned HTTP 429. Direct academic HTML preserves metadata and avoids transformed footnotes becoming benchmark digits. Other transient fetch failures use public-page reads; search can use the same OpenAI model/key. Genuine research runs exercised the fallbacks. No other provider key was required.

Two LLM-agents generation attempts failed (OpenAIConnectionError and checker tool-limit exhaustion). Neither produced an accepted triplet. A diagnostic candidate went into a fresh sandbox; new researchers retrieved evidence, and the lead repaired, finalized, validated and spot-checked it. Successful metadata counts that accepted run only. Bounded review runs likewise retain original generation metadata separately.

Each accepted report/source pair was authored or repaired in a network-isolated sandbox, finalized and validated there, then downloaded verbatim. Two source dates were restored deterministically inside a fresh sandbox after checking exact primary date evidence; no LLM usage was invented. .gitattributes prevents Git line-ending conversion of report/source bytes.

This is regression/structural validation, pattern scanning and same-assistant source review with model checker samples. It is not independent scientific replication or proof of every interpretation. Model review notes contain an explicit correction for an unsupported 7.47% table assertion; the submitted report does not repeat it. Manual rubric grading still applies. Lead token totals exclude subagents, fallback search and failed runs; total cost is unknown.

Historical verification-before-luna.json, verification.json, world-model-run.json, continuation-baseline.json, offline-final-tests.json and REPORT_SPOT_CHECKS.md describe earlier states. Current outputs/hashes are in final-verification.json. The user authorized commit/push after review; publication is evidenced by GitHub history.