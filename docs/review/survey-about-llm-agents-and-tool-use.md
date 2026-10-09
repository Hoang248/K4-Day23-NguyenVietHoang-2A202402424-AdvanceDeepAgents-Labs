# Review result

## Minimal changes made
- Corrected MRKL [1] date from 2022-05-03 to 2022-05-01, verified against the official arXiv v1 PDF header (the May 3 date is a manuscript title-page date).
- Corrected AgentDojo [12] date from 2024-12-16 to its verified first-submission date, 2024-06-19.
- Clarified the AgentDojo 7.5% result as GPT-4o's targeted attack success rate against the paper's strongest tested attack, defining it as the share of security cases where the attacker goal was met. The paper's table reports 7.47% (rounded in prose to 7.5%).
- Preserved the survey's structure, unaffected prose, URLs, and source-family labels. Final sources retain 15 citations across arxiv, web, and hf-search.

## Verification and verdicts
- Focused researchers independently reviewed the MRKL date, AgentDojo date, and AgentDojo metric/setup. The retrieved primary evidence supported both corrected dates and the qualified 7.5% claim; no unsupported replacement claim was added.
- Citation checker follow-up verdicts: MRKL date [1] — SUPPORTED; AgentDojo first-submission date [12] — SUPPORTED; qualified AgentDojo 7.5% claim [12] — SUPPORTED; WASP claim [14] — SUPPORTED (based on HF paper-page summary, as the survey already qualifies it as HF-indexed/abstract-level evidence).
- The checker's initial scrape marked the first three claims UNVERIFIABLE because the fetched page text omitted relevant metadata/table details; focused primary-source evidence was supplied for re-review, and all four follow-up verdicts were SUPPORTED.
- Finalization: kept 15/15 sources. Validation: `OK: 15 sources, all citations resolve`. Re-ran both finalizer and validator after edits; both passed.
## Implementing-assistant source audit addendum
The agent-generated note above mentions a 7.47% table value. That value was not found in the inspected v2/v3 primary HTML. Section 4.3 explicitly reports 7.5%, whereas Table 5 in v3 reports 6.84% for tool filtering. The submitted report attributes 7.5% to the author-reported setup and does not repeat 7.47%. The two paper values are not reconciled here. Primary text: https://arxiv.org/html/2406.13352v3 .
