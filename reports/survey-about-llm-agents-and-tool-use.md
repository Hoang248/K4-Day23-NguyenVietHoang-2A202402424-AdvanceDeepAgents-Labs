# LLM Agents and Tool Use: Architectures, Evaluation, and Safety

## TL;DR
- Tool use spans modular routing, prompted reasoning–action loops, and models trained to decide when and how to call APIs; these are distinct control designs rather than a demonstrated universal ranking. [1][2][3]
- Retrieval-grounded API generation supports call construction from evolving documentation, while multi-step planning and generated reusable tools broaden the action space in different ways. [4][5][6][7]
- Benchmarks have expanded from checking API-call behavior to stateful agent–user interaction and repeatable large-catalog evaluation, but each measures a different slice of capability. [8][9][10]
- Security evaluations show that indirect prompt injection can influence agents under tested conditions; benchmark mitigations and protocol-level recommendations do not by themselves establish protection in deployment. [11][12][13][14]

## Background
An LLM agent using tools is a system in which a model selects, constructs, or invokes external capabilities and uses returned observations in producing subsequent actions or answers. The design problem therefore extends beyond fluent response generation: systems need to map requests to capabilities, respect tool interfaces, interpret results, and control the effects of actions. MRKL describes an explicit router over specialist and symbolic modules, while ReAct makes action and observation part of an iterative language-model trajectory. [1][2]

External tools can supply information or operations beyond the model's immediate text generation, but tool use also introduces interface errors, stateful outcomes, and untrusted returned content. The survey distinguishes architecture and action-space design, evaluation scope, and the security boundary around tools; evidence from one benchmark or task type should not be treated as a general comparison across all agents. [4][8][11]

## Architectures: routing, interaction loops, and learned calls
MRKL treats tool use as a modular system: a router directs input to an expert, such as a specialist model or symbolic resource, and can pass results onward. ReAct instead describes a sequential loop in which the model interleaves reasoning traces with task-specific actions, then conditions subsequent reasoning on observations. These choices place control differently—at an orchestration/router layer versus within a prompted trajectory—and the retrieved work does not establish a head-to-head winner across equivalent tasks. [1][2]

Toolformer shifts some tool decisions into model training. Its self-supervised method samples candidate API calls and retains calls when their results improve future-token prediction, training the model to decide which API to call, when, and with what arguments, and to incorporate returned results. This differs from ReAct's prompted interaction pattern and MRKL's explicit router, although Toolformer's evidence is tied to its fixed text-oriented APIs and training setup rather than arbitrary long-horizon environments. [2][3]

Tool use can also be distributed across specialized model roles. A recent multi-LLM design described in the retrieved HF Papers record separates planning, calling, and summarization; this decomposes responsibilities rather than treating tool selection solely as a single model's sequential loop. The available record establishes the design but does not provide enough experimental detail here to compare its performance with the other architectures. [15]

## Grounding and expanding the action space
A fixed or changing API catalog creates a grounding problem: the model must identify relevant interfaces and produce compatible calls. Gorilla retrieves API documentation into the prompt and frames retrieval-aware training as a way to adapt to documentation changes and reduce API hallucination. ToolLLM combines a neural API retriever with multi-round tool-use training and a search procedure that explores alternative reasoning/action paths, addressing catalog discovery and multi-step decisions together. ToolBench covers 16,464 REST APIs across 49 categories, but that scale describes the benchmark corpus, not the number of tools any agent can reliably use in an open deployment. [4][5]

Other work changes what counts as an available action. CREATOR has an LLM create tools using documentation and code realization, then separates tool creation from later task solving. Large Language Models as Tool Makers separates a tool-making model that creates reusable Python functions from a tool-using model that applies them, and includes caching generated utilities. These approaches may reduce reliance on a fixed predefined inventory, but their reported evaluations concern particular mathematical, tabular, or reasoning workloads and do not by themselves establish safe or reliable synthesis for arbitrary stateful services. [6][7]

These approaches suggest a spectrum: retrieve and call a documented interface, search over multi-step API sequences, or synthesize reusable operations. Greater action flexibility also makes validation and control of execution more consequential; the tool-generation papers establish their respective methods, not a security guarantee for generated code. [4][5][6][7][13]

## Evaluation: call correctness, repeatability, and interaction
Benchmarks operationalize different notions of tool competence. API-Bank explicitly targets planning, retrieval, and calling, with an executable evaluation set of 73 tools and 314 annotated dialogues. StableToolBench addresses instability from changing online API availability by combining cached responses with an LLM API simulator, and reports solvable-task-oriented measures. Together these illustrate a tradeoff: runnable API tasks can test call behavior, while simulation can improve repeatability but is not identical to interacting with live APIs. [8][9]

τ-bench broadens the unit of analysis to dynamic user-agent conversations under domain policies: it scores end-of-episode database state against a goal and uses pass^k to measure consistency across repeated trials. This focuses on policy-compliant interaction and outcome state rather than only whether an individual call is syntactically correct. Its initial retail and airline scope does not make it a general benchmark for every API domain. [10]

The benchmarks are therefore complementary, not interchangeable. A call-generation score, a simulated solvable-task score, and repeated success in an interactive episode answer different questions; they should not be ranked against one another without accounting for task distribution, environment, and scoring rule. In particular, success alone does not necessarily describe how reliably a system repeats a task or what happened along the action trajectory. [8][9][10]

## Safety: untrusted results, permissions, and side effects
Indirect prompt injection occurs when instructions embedded in external content influence an agent that processes that content. InjecAgent evaluates this risk in a constructed benchmark of 1,054 cases with 17 user tools and 62 attacker tools; it reports that ReAct-prompted GPT-4 was vulnerable in 24% of those benchmark cases. That figure characterizes the tested agent and cases, not the prevalence or success rate of attacks in deployed systems. [11]

AgentDojo similarly tests prompt-injection attacks and defenses in a dynamic benchmark. In a GPT-4o evaluation against the paper’s strongest attack, tool filtering lowered targeted attack success rate to 7.5% (the fraction of security cases in which the attacker’s goal was met); the paper also reports benign-task failures and a utility cost from some defenses. These results illustrate that attack resistance and task utility can trade off within a benchmark; they do not establish a general guarantee against adaptive attacks or real-world prevalence. [12]

The boundary between model guidance and enforced controls matters. The Model Context Protocol specification recommends that applications present confirmation prompts to users for tool operations, but leaves interaction patterns to implementations; the specification therefore does not establish that any particular deployment presents such prompts. [13]

A more recent HF-indexed benchmark, WASP, reports partial success for prompt-injection attacks in up to 86% of cases, while agents often struggled to complete the attackers' full objectives. Partial compromise is not equivalent to completing a harmful action, and the abstract-level evidence is benchmark-specific. Read together, these security benchmarks support evaluating both the influence of injected content and resulting side effects, while avoiding claims that benchmark rates predict real-world incident frequency. [14][11][12]

## Trends and open problems
The retrieved work moves from explicit modular routing and prompted interaction loops toward learned call decisions, retrieval-conditioned APIs, search over multi-step plans, and creation or caching of tools. In parallel, evaluation shifts from call-oriented benchmark tasks toward stable large-catalog testing and repeated, stateful agent-user interaction. This is a broadening of research targets, not evidence that one architecture has superseded the others. [1][2][3][4][5][6][7][8][9][10]

Several questions remain open in this evidence base. First, comparisons are difficult because tool sets, task distributions, and metrics differ; call correctness, task completion, repeatability, and side effects are not a single measure. Second, large catalogs and dynamic tool creation require robust interface grounding and safe execution, while the retrieved sources do not demonstrate a general method that solves both. Third, defenses must preserve benign utility as well as constrain harmful actions, and benchmark defenses cannot establish deployment-wide security. [4][5][6][8][9][10][11][12][14]

A practical research direction is to evaluate agents end to end: whether they select appropriate tools, use documented parameters, recover from failure, reach intended state consistently, and remain within authorized effects. Protocol-level recommendations cannot establish which safeguards a particular deployment implements. The available evidence motivates this integrated evaluation, but does not yet provide a universally accepted combined standard. [8][9][10][12][13]

## References
[1] MRKL Systems: A modular, neuro-symbolic architecture that combines large language models, external knowledge sources and discrete reasoning. arxiv. https://arxiv.org/abs/2205.00445 (2022-05-01)
[2] ReAct: Synergizing Reasoning and Acting in Language Models. arxiv. https://arxiv.org/abs/2210.03629 (2023-03-10)
[3] Toolformer: Language Models Can Teach Themselves to Use Tools. arxiv. https://arxiv.org/abs/2302.04761 (2023-02-09)
[4] Gorilla: Large Language Model Connected with Massive APIs. arxiv. https://arxiv.org/abs/2305.15334 (n.d.)
[5] ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs. arxiv. https://arxiv.org/abs/2307.16789 (n.d.)
[6] Large Language Models as Tool Makers. arxiv. https://arxiv.org/abs/2305.17126 (n.d.)
[7] CREATOR: Tool Creation for Disentangling Abstract and Concrete Reasoning of Large Language Models. arxiv. https://arxiv.org/abs/2305.14318 (n.d.)
[8] API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs. web. https://arxiv.org/abs/2304.08244 (n.d.)
[9] StableToolBench: Towards Stable Large-Scale Benchmarking on Tool Learning of Large Language Models. web. https://aclanthology.org/2024.findings-acl.664/ (2024-08)
[10] τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains. arxiv. https://arxiv.org/abs/2406.12045 (n.d.)
[11] InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents. web. https://aclanthology.org/2024.findings-acl.624/ (2024)
[12] AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. arxiv. https://arxiv.org/abs/2406.13352 (2024-06-19)
[13] Tools - Model Context Protocol. web. https://modelcontextprotocol.io/specification/2025-03-26/server/tools (2025-03-26)
[14] WASP: Benchmarking Web Agent Security Against Prompt Injection Attacks. hf-search. https://huggingface.co/papers/2504.18575 (2025-04-22)
[15] Small LLMs Are Weak Tool Learners: A Multi-LLM Agent. hf-search. https://huggingface.co/papers/2401.07324 (2024-01-14)
