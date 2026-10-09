# Historical read-only report spot-checks

This receipt describes the initial report runs, before the authorized full-report review and repairs. Current findings and limitations are in [REPORT_REVIEW.md](REPORT_REVIEW.md); current artifact hashes and metadata are in [final-verification.json](final-verification.json).

Checks performed by the implementing assistant against retrieved primary texts;
this is not independent review or certification of every claim. Report files
are not edited on the host. Any unsupported content must be repaired by the
agent in its sandbox and validated before download.

## World model

See WORLD_MODEL_RUN.md for citations 3, 4 and 8: DreamerV3 task breadth,
robust-representation components and Oasis architecture. All three sampled
claims are supported by the retrieved texts.

## Reinforcement learning for LLM reasoning

| Final citation | Sampled claim | Evidence | Result |
|---|---|---|---|
| 1 | Process supervision outperforms outcome supervision on the paper's MATH evaluation. | [Author abstract](https://arxiv.org/abs/2305.20050) explicitly reports that comparison and its evaluation scope. | Supported |
| 4 | DeepSeekMath introduces GRPO as a PPO variant that improves mathematical reasoning while optimizing memory usage. | [Author abstract on HF](https://huggingface.co/papers/2402.03300) states the method and memory motivation. | Supported |
| 7 | R1-Zero applies RL without preliminary supervised fine-tuning; the separate R1 system has a multi-stage pipeline. | [Original v1 author abstract](https://arxiv.org/abs/2501.12948v1) distinguishes those two systems. The current v2 abstract was rewritten. | Supported in v1 |

Final downloaded RL report: 13 sources, arxiv/hf-search/web, eight task calls;
citation validator OK. It contains four thematic sections plus the required
TL;DR, Background, Trends and open problems, and References. Results are
qualified by task/evaluation scope. Missing source dates remain unknown.

## LLM agents and tool use

The accepted report is the fresh recovery run, not the diagnostic candidate.

| Final citation | Sampled claim | Evidence | Result |
|---|---|---|---|
| 3 | Toolformer learns API choice, call timing, arguments and use of returned results. | [Author abstract](https://arxiv.org/abs/2302.04761) explicitly lists those learned decisions and self-supervision. | Supported |
| 11 | InjecAgent has 1,054 cases, 17 user tools and 62 attacker tools; its tested ReAct GPT-4 agent is vulnerable in 24% of cases. | [ACL author abstract](https://aclanthology.org/2024.findings-acl.624/) reports these numbers. The report limits their interpretation to the tested benchmark. | Supported |
| 14 | WASP reports partial attack success up to 86%, while complete attacker goals are often not achieved. | [Author abstract on HF](https://huggingface.co/papers/2504.18575) distinguishes partial success from full objective completion. | Supported |

Downloaded report: 15 sources, arxiv/hf-search/web, six actual lead task calls,
314.7 seconds. It contains four thematic sections. Prior failed-run usage is
unknown and is not included in this run's metadata.

## Video and multimodal generation

| Final citation | Sampled claim | Evidence | Result |
|---|---|---|---|
| 1 | Video Diffusion Models extends image diffusion and jointly trains on images and video. | [Author abstract](https://arxiv.org/abs/2204.03458) explicitly describes both points. | Supported |
| 9 | MotionCtrl independently controls camera and object motion. | The HF URL returned 429 during this read-only check; the [same paper's author abstract on arXiv](https://arxiv.org/abs/2312.03641) states independent control of both. | Supported via alternate primary text |
| 15 | The Matrix reports 720p streams up to 16 FPS and training using limited game data. | The linked PDF exceeds the browser's size limit; the [matching NeurIPS proceedings abstract](https://proceedings.neurips.cc/paper_files/paper/2025/hash/7e810b2c75d69be186cadd2fe3febeab-Abstract-Conference.html) reports these values, plus complementary real-world footage. The survey attributes throughput to the authors rather than an independent measurement. | Supported via proceedings abstract |

Downloaded report: 16 sources, arxiv/hf-search/web, 13 task calls, 427.8 seconds,
five thematic sections. The checks above do not certify every technical detail.

## Efficient inference and small language models

| Final citation | Sampled claim | Evidence | Result |
|---|---|---|---|
| 1 | Pretraining remains important for compact architectures; pretrained distillation adds improvements. | [Author abstract on HF](https://huggingface.co/papers/1908.08962) reports both. The survey limits this precedent to representation models. | Supported |
| 5 | vLLM reports 2–4× throughput over FasterTransformer and Orca at the same latency. | [Author abstract](https://arxiv.org/abs/2309.06180) gives these baselines, range and qualification. | Supported |
| 6 | KIVI quantizes keys per channel and values per token, with 2.6× less peak memory and 2.35–3.47× throughput. | [Author abstract](https://arxiv.org/abs/2402.02750) reports these dimensions and values in its tested workloads. | Supported |

Downloaded report: 20 sources, arxiv/hf-search/web, four task calls, 312.0 seconds,
four thematic sections. This completes three read-only samples per accepted report.
