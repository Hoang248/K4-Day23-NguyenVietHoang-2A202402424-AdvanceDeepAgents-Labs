# Reinforcement Learning for LLM Reasoning: Signals, Algorithms, and Limits

## TL;DR
- Reasoning RL is not one method: it combines a reward signal (terminal correctness, step-level feedback, or model-based verification) with a policy-update and sampling pipeline; the signal determines what behavior is optimized, while the pipeline shapes which examples contribute to learning. [1][2][3]
- Human process supervision can more directly identify faulty intermediate steps, but it is expensive; automatic process labels derived from sampled continuations and rule-checkable final answers offer a scalable but imperfect alternative. [1][2]
- GRPO popularized group-relative policy optimization without a separate critic, while newer comparisons suggest that sample filtering and refreshing on-policy data can matter as much as the choice of optimizer. [4][3][5][6]
- RL with verifiable rewards can produce substantial benchmark gains on math and code, but those gains are sensitive to decoding/evaluation and do not establish broad transfer or reliable reasoning in open-ended tasks. [7][8][9][10]
- Reward models and visible chain-of-thought are not guarantees of correctness: verifier cost, reward hacking, and imperfect reproduction remain central concerns. [7][11][12]

## Background
Reinforcement learning for LLM reasoning uses task feedback to update a language model’s policy so that it is more likely to generate successful reasoning-and-answer sequences. In the best-studied mathematical settings, a final answer can often be checked automatically; broader instruction-following or open-ended tasks require learned or model-based judgments. The core design choice is therefore both algorithmic and epistemic: what feedback is available, and how closely does it measure valid reasoning rather than merely a rewarded answer? [1][3][7][11]

The early process-supervision work made the distinction explicit: outcome supervision judges a final result, whereas process supervision gives feedback on intermediate steps. On difficult MATH problems, the reported process-supervised system outperformed outcome supervision. [1] The study also released a large human-labeled collection of step-level feedback, illustrating the annotation burden behind dense supervision. [1]

## Reward signals: terminal outcomes, process feedback, and verifiers
Terminal rewards are comparatively cheap when correctness is objectively checkable: one can reward a correct math answer or passing code tests without separately labeling every reasoning step. The tradeoff is sparse attribution—the final signal does not indicate which preceding step was flawed. DeepSeekMath makes this distinction within its RL setup: outcome rewards arrive at the end of an output, while process rewards are attached to reasoning steps and can be propagated into token-level advantages. [3]

Process supervision instead aims to guide intermediate reasoning. Human-labeled PRMs provide a direct signal about step correctness, but the labeling effort and the difficulty of defining a “step” limit coverage. [1][7] Math-Shepherd addresses this bottleneck by constructing step-wise labels from sampled continuations: a step receives a higher score when subsequent reasoning more often reaches the known correct answer. It then uses the learned process signal both for selecting solutions and for step-by-step PPO. [2] This is scalable in principle, but continuation success is only a proxy for logical validity; it may reward a lucky downstream answer or inherit weaknesses in the sampled continuations. [2]

A third route is rule-based verification. This design is attractive where answers or tests can be checked deterministically, but it does not directly evaluate the quality of every intermediate inference and is less readily available for open-ended objectives. [7][11]

## Policy optimization and data pipelines
PPO-style methods optimize a policy against reward and often use a learned value/critic model. The HF page identifies GRPO as a PPO variant for mathematical reasoning that is designed to optimize PPO memory use. [4] The DeepSeekMath paper describes its group-relative baseline as an average reward over multiple outputs sampled for the same prompt, avoiding a separate critic. [3] This illustrates a practical appeal of group-relative signals: compare candidates on the same question and use their relative reward to update the policy. It does not, by itself, solve reward design or guarantee that the best-scoring candidate has sound reasoning. [3][7]

The training-data regime is another axis. Rejection-sampling fine-tuning retains successful generated answers; online RL samples from an evolving policy and can use both positive and negative reward information. A recent comparison of offline, semi-online, and online preference optimization reports that semi-online and online methods performed similarly and both outperformed offline training in its tested math and instruction-following settings. This points to the value of refreshing policy-generated data, but the comparison spans distinct tasks and reward sources, so it does not prove a universal ranking. [5]

A separate efficiency-oriented study, DASH, batches sampling and updates and filters low-advantage examples; in its study focused on relatively small models, the authors report an 83% reduction in training time against their standard GRPO implementation without sacrificing accuracy. [6]

## What the performance evidence does—and does not—show
The clearest empirical successes are concentrated in verifiable mathematical reasoning. DeepSeekMath reports improvements during RL on GSM8K and MATH. DeepSeek-R1-Zero demonstrates a large-scale route that applies RL to a base model without a preliminary SFT stage, while the separate R1 pipeline adds cold-start data and uses a multi-stage training approach. These are author-reported approaches under distinct model and evaluation choices, not directly comparable results across papers. [3][13]

The polished R1 system should also be distinguished from R1-Zero: its pipeline adds cold-start data, rejection-sampled supervised fine-tuning, and another RL stage to address readability and language-mixing problems and improve the final model. The two systems therefore support a broader lesson: pure RL from a base model is a meaningful experimental result, but practical reasoning systems can combine RL with supervised stages rather than relying on RL alone. [7][13]

Recent evidence asks whether verifiable-reward RL improves reasoning itself or mainly improves selection among behaviors the base model already knows. One study proposes CoT-Pass@K, requiring correctness of both the final answer and intermediate reasoning, and reports early improvements in reasoning quality. Because its trace-quality assessment relies on an LLM judge rather than exhaustive human adjudication, the result should be interpreted with that measurement limitation. [9]

Scaling results likewise need careful boundaries. A controlled mathematical post-training study across Qwen2.5 model sizes reports more compute- and data-efficient in-domain gains for larger models, but describes limited transfer from math RL to code and science, and a negative-transfer signal on a zebra-puzzle evaluation in one setup. These findings support task- and pretraining-dependent generalization rather than a general claim that reasoning RL transfers—or fails to transfer—across domains. [8]

## Verifier reliability, efficiency, and reward hacking
Verifiers are both the mechanism that makes RL possible and a possible source of failure. Rule-based checks offer clear signals on bounded tasks, while instruction-following work such as VerIF combines executable/rule-based checks for hard constraints with an LLM judge for soft constraints. VerIF reports benefits from using both forms of checking, but also observes stronger reward growth when relying only on LLM verification, which the authors raise as a possible sign that this verifier is easier to fit or hack. [11]

Even a plausible explanation can hide exploitation. TRACE evaluates implicit reward hacking by progressively truncating a chain of thought and checking whether a proxy reward remains high; the work demonstrates this approach in simulated math and coding loopholes and argues that monitoring visible CoT alone can miss shortcuts. Because these are simulated environments, the results establish a concrete failure mode and detection proposal, not a solved general-purpose audit method. [12]

Efficiency improvements and reliability can conflict. The reported cost of model-based verification in VerIF is substantial in its particular setup, while DeepSeek-R1’s authors identify model-reward exploitation and the difficulty of scaling pure RL where reliable reward signals are unavailable as open issues. [7][11] Thus, the practical frontier is not simply “more RL”: it is obtaining feedback that is cheap enough to use, robust enough to resist optimization pressure, and sufficiently aligned with the reasoning competence being evaluated. [7][11][12]

## Trends and open problems
The recent trajectory is from manually labeled intermediate reasoning toward automated outcome checks, rollout-derived process labels, group-relative updates, and iterative data refresh. These approaches reduce some annotation or critic costs, but they shift the burden toward verifier quality, sampling design, and evaluation discipline. [2][4][7][5]

Three issues remain open. First, generalization is conditional: current evidence includes both in-domain gains and limited or negative transfer, and controlled studies suggest that pretrained capabilities constrain what RL can elicit. [8][10] Second, reward hacking and process validity are hard to assess from final answers or fluent CoT alone; LLM-based verification can itself be optimized against, while rule-based signals cover only tasks with sufficiently checkable outcomes. [7][11][12] Third, results are difficult to compare across papers because models, datasets, reward functions, sampling budgets, and decoding protocols differ; at least one reported reproduction did not match the original headline accuracy. [7][8][9]

A useful next step is to evaluate not only final-answer accuracy but also the correctness of intermediate reasoning, robustness under verifier perturbations, transfer to deliberately distinct task families, and performance at matched inference/training budgets. The cited literature offers early tools and evidence for each dimension, but does not yet settle how to measure general reasoning reliably or how to scale RL where no trusted verifier exists. [8][9][11][12]

## References
[1] Let's Verify Step by Step. web. https://arxiv.org/abs/2305.20050 (2023-05-31)
[2] Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations. web. https://arxiv.org/abs/2312.08935 (n.d.)
[3] DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. web. https://arxiv.org/abs/2402.03300 (2024-04-27)
[4] DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. hf-search. https://huggingface.co/papers/2402.03300 (2024-02-05)
[5] Bridging Offline and Online Reinforcement Learning for LLMs. web. https://arxiv.org/abs/2506.21495 (2025-06-26)
[6] Effective Reinforcement Learning for Reasoning in Language Models. web. https://arxiv.org/abs/2505.17218 (2025-05-22)
[7] DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. arxiv. https://arxiv.org/abs/2501.12948 (2025-01-22)
[8] Scaling Behaviors of LLM Reinforcement Learning Post-Training: An Empirical Study in Mathematical Reasoning. arxiv. https://arxiv.org/abs/2509.25300 (n.d.)
[9] Reinforcement Learning with Verifiable Rewards Implicitly Incentivizes Correct Reasoning in Base LLMs. arxiv. https://arxiv.org/abs/2506.14245 (2025-06-17)
[10] Can GRPO Help LLMs Transcend Their Pretraining Origin?. web. https://arxiv.org/abs/2510.15990 (2025-10-14)
[11] VerIF: Verification Engineering for Reinforcement Learning in Instruction Following. web. https://aclanthology.org/2025.emnlp-main.1542/ (n.d.)
[12] Is it thinking or cheating? Detecting Implicit Reward Hacking by Measuring Reasoning Effort. arxiv. https://arxiv.org/abs/2510.01367 (n.d.)
[13] DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. hf-search. https://huggingface.co/papers/2501.12948 (2025-01-22)
