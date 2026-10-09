# Historical initial world-model run — 2026-10-09

This receipt describes the initial run and the user's stop request at that time. Later authorization resumed the other topics and reviewed all reports. Current status is in [FINAL_RUN.md](FINAL_RUN.md); the original world-model metadata and hashes remain in its repair lineage.

User authorized GPT-6 Luna + Docker execution, then narrowed the current session
to finishing world model and stopping. The other four topics remain for later.

Command: `.venv/Scripts/python.exe research.py "survey about world model"`.
Executed outside Codex's Windows sandbox because Docker's engine pipe and network
access are restricted inside it. Process exited 0. Actual model: openai:gpt-6-luna;
Responses API; Docker python:3.12-slim with network disabled by sandbox.py.

Outputs are authentic downloaded bytes, not manually edited:

- reports/survey-about-world-model.md
- reports/survey-about-world-model.sources.json
- reports/survey-about-world-model.meta.json

Metadata: elapsed 406.6 seconds, six task calls, 12 cited sources, source families
arxiv/hf-search/web. Lead tokens: 485881 input and 9210 output. These exclude
subagent consumption and do not establish total spend or billed uncached tokens.

Validation: check_citations.py prints `OK: 12 sources, all citations resolve`.
Native self_check accepts this topic; four missing topics keep full submission
pending. Protected supplied files remain unchanged; git diff --check passes.
Container deepresearch-f7721c85 is absent from docker ps -a after completion.

Read-only spot-check by the same implementation assistant, not independent review:

| Citation | Checked claim | Source evidence / result |
|---|---|---|
| 3 | DreamerV3 reports one configuration across over 150 tasks and learns through imagined scenarios. | [Author abstract](https://arxiv.org/abs/2301.04104) supports both claims. |
| 4 | Robust representations use masking, bisimulation, reconstruction and a hybrid recurrent state-space model. | [Paper abstract on HF](https://huggingface.co/papers/2405.06263) supports the method description. |
| 8 | Oasis uses a spatial autoencoder and latent diffusion backbone, generating user-conditioned frames autoregressively. | [Project architecture](https://oasis-model.github.io/) supports the description. |

The report is structured as TL;DR, Background, four thematic comparisons, Trends
and open problems, References. Claims are qualified as author-reported where
appropriate. A sample check does not certify every claim; teacher review remains.

To continue later from the repository root, run these separately or sequentially:

```powershell
.venv/Scripts/python.exe research.py "survey about reinforcement learning for LLM reasoning"
.venv/Scripts/python.exe research.py "survey about LLM agents and tool use"
.venv/Scripts/python.exe research.py "survey about video and multimodal generation"
.venv/Scripts/python.exe research.py "survey about efficient inference and small language models"
.venv/Scripts/python.exe self_check.py
```

`run_topics.py` runs all five, so it would also regenerate world model; use the
commands above to retain this run. No commit or push was performed. Snapshot
hashes for code and downloaded artifacts are in world-model-run.json.
