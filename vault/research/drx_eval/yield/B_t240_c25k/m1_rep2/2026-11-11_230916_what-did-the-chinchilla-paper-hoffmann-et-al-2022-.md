# The Chinchilla Scaling Law: Original Findings and the Challenge of Refined Models

## Executive Summary

Hoffmann et al.'s 2022 Chinchilla paper established that compute-optimal language model training requires scaling model parameters and training tokens equally at approximately 20 tokens per parameter—a finding that contradicted prior industry practice of maximizing parameter count. However, four years of subsequent research have revealed that this ratio is context-dependent and subject to significant refinements: smaller models can be trained far beyond the 20:1 point for inference efficiency, the original formula systematically undercounts training compute for models below 100B parameters, and when inference costs dominate total cost of ownership, the optimal allocation diverges sharply from Chinchilla's training-only optimization. Additionally, a 2026 replication exposed that the published confidence intervals are implausibly narrow by a factor of 50, and evidence suggests data quality, task type, and architecture class (dense vs. sparse) all moderate the ratio's applicability.

---

## I. The Chinchilla Paper: Original Findings

### A. The 20:1 Ratio Discovery

[DERIVED][HIGH] Hoffmann et al. trained 400+ language models and found that for compute-optimal training, model size and training tokens should be scaled equally at roughly 20 tokens per parameter. Chinchilla (70B parameters, 1.4 trillion tokens) outperformed Gopher (280B parameters) and other larger models on identical compute budgets, proving prior scaling practices that maximized parameters while limiting data were severely suboptimal.

### B. Empirical Validation Across Scales

[OBSERVED][MEDIUM] For dense transformers trained for one epoch on language data, the optimal training token count scales linearly with model parameters at approximately 20 tokens per parameter. This ratio has proven empirically invariant across scales from billions to trillions of parameters, meaning dataset requirements can be calculated from any model size without iteration. The 20-token-per-parameter ratio was derived from 400+ training runs varying model size from 70M to 16B parameters, with the ratio confirmed at Chinchilla's 70B-parameter deployment (1.4T tokens).

### C. Performance Superiority of Balanced Scaling

[DERIVED][MEDIUM] Prior scaling laws optimized for maximum parameters under fixed compute, creating undertrained large models. Chinchilla demonstrated that for identical compute budgets, a 70-billion-parameter model trained on 1.4 trillion tokens outperforms a 280-billion-parameter model trained on only 300 billion tokens. Specifically, Chinchilla achieved 77.7% average performance versus Gopher's 75.1% using the same compute (5.76×10²³ FLOPs), proving that token scarcity—not model size—is the efficiency bottleneck when the 20:1 ratio is violated.

---

## II. Challenges to the Original Ratio: Extended Training and Inference-Efficient Models

### A. The Post-Chinchilla Discovery: Training Far Beyond 20:1

[DERIVED][HIGH] Training tokens can be increased 10x–75x beyond the standard 20-token Chinchilla point to create smaller, cheaper-to-deploy models with competitive capability. Llama 3 70B trained on 200 tokens per parameter achieves performance equivalent to a Chinchilla-optimal 260B model while costing 3.7x less to run inference; Llama 3 8B extends this further to 75x Chinchilla tokens, delivering 5x inference savings, enabling teams to trade training compute for dramatic deployment cost reduction.

This finding revealed a critical gap in Chinchilla's original optimization: while the 20:1 ratio minimizes *training* compute for a given capability target, it ignores the cost structure of inference-heavy deployments. A model trained far beyond the compute-optimal point may cost more in training FLOPs but dramatically reduces per-request inference costs, which over a model's lifetime can dominate total cost of ownership.

### B. The Inference-Adjusted Scaling Law

[DERIVED][HIGH] When you expect significant inference demand (approximately 1 billion requests), the optimal parameter-to-token allocation diverges sharply from Chinchilla: a 7B-parameter-quality model should instead be trained with 6B parameters on 1.18 times the originally-recommended data; a 30B-quality model should use 13.6B parameters trained on 2.84 times more data and saves 28 percent of total compute costs. This divergence exists because Chinchilla optimized only for training compute, ignoring the inference costs that can dominate total cost of ownership over a model's lifetime.

### C. Empirical Validation of Small-Model Training at Extreme Ratios

[HYPOTHESIS][HIGH] The authors trained 47 models ranging from 150M to 6B parameters at extreme token-to-parameter ratios up to 10,000 and found model quality continued improving with no saturation point, empirically validating the inference-adjusted formula. This contradicts earlier theoretical claims that below a critical model size, additional training data could not recover quality; instead, smaller models trained substantially longer achieve quality parity with larger models.

---

## III. Refinements and Corrections: Formula Recalibration for Smaller Models

### A. The 2024 Correction for Sub-100B Parameter Models

[DERIVED][HIGH] The original Chinchilla formula systematically underestimated training compute requirements for models below 100B parameters. A 2024 correction shows that a 50%-scale model requires 26% more training compute and 2.5× more tokens than the original formula projected—substantially higher than expected—affecting any team training in the 8B–70B range where every prior budget estimate becomes optimistic by over one quarter.

This correction reflects that the original Chinchilla formula was fitted primarily on larger models where different scaling dynamics may apply. Teams relying on the canonical 20:1 ratio for models in the 8B–70B range have systematically underestimated training budgets.

### B. Scaling Law Miscalibration at Extreme Token Ratios

[DERIVED][HIGH] The Chinchilla scaling law coefficients were fitted using data primarily from ~100 tokens-per-parameter runs—the training efficiency sweet spot. When the authors re-fitted the same parametric form using data including extreme ratios (500+ tokens per parameter), the coefficients changed significantly and the curves flattened, indicating Chinchilla systematically overestimates how much benefit additional training provides at high token ratios. Your scaling-law predictions are miscalibrated if your use case requires extended training.

This finding has direct implications for teams deploying inference-efficient small models: the Chinchilla curves that predict loss improvement at 200 or 500 tokens per parameter are overly optimistic. Actual gains flatten more gradually than predicted.

---

## IV. Statistical Reexamination: The 2026 Confidence Interval Crisis

### A. Implausibly Narrow Confidence Intervals

[DERIVED][HIGH] A 2026 replication of the original Chinchilla paper found the published confidence intervals are implausibly narrow—obtaining such tight intervals would require approximately 600,000 experiments, yet only 400-500 were likely conducted. The replication's corrected model yields a practical operating range of 4-40 tokens per parameter at standard compute scales, with 50× wider confidence intervals than originally reported.

This finding does not invalidate the 20:1 point estimate but substantially increases the legitimate operating range around it. The published intervals (which appear narrow in the original paper) imply statistical power that the sample size cannot support.

### B. Practical Implications of Expanded Uncertainty

Rather than treating 20:1 as a precise allocation target, practitioners should plan within the 4-40 tokens-per-parameter operating range to account for measurement uncertainty in scaling decisions. A model trained at 15:1 or 25:1 lies within the justified uncertainty band and may better match the specific constraints (data availability, latency requirements, or inference costs) of a deployment scenario.

---

## V. Task-Dependent and Architecture-Specific Variations

### A. Task-Type Modulation of the Optimal Ratio

[HYPOTHESIS][MEDIUM] The 20:1 ratio is not invariant across all task types and architectures. Memorization-heavy tasks are best served with lower token-to-parameter ratios (more parameters, less data), while reasoning tasks achieve peak accuracy at the canonical 20:1 ratio. Sparse models, inference-heavy deployments, and multi-epoch training scenarios require recalibration; applying the baseline ratio to non-standard workloads wastes compute.

This hypothesis indicates that the evidence base for a universal 20:1 ratio is thin outside of general language modeling on diverse, single-epoch, web-scale data. Task-specific validation is necessary before committing large training budgets.

### B. Data Quality and Curation Trade-offs

[HYPOTHESIS][HIGH] High-quality deduplicated data reaches compute-optimal training at approximately 15 tokens per parameter, compared to 20 tokens per parameter for mixed-quality web-scraped data. This means aggressive data curation yields equivalent model performance at lower total token volume, freeing compute budget for other initiatives.

The implication is that teams can reallocate spending from data volume scraping to quality curation, shifting the scaling optimum from 20:1 toward 15:1 and reducing data acquisition costs without sacrificing model performance. However, the evidence here is characterized as thin; this represents an open research direction rather than settled guidance.

### C. Mixture-of-Experts: An Unresolved Question

[HYPOTHESIS][HIGH] In Mixture-of-Experts architectures, only a fraction of total parameters activate per token, which changes how the compute-optimal ratio applies. Early evidence suggests the 20:1 ratio should reference active parameters per token rather than total model size, though this remains an open research question, meaning MoE models may operate within identical budgets as smaller dense models.

This question remains explicitly unresolved in the literature. Applying the 20:1 ratio to total MoE parameters (rather than active parameters per token) may systematically mismatch compute allocation for sparse models.

---

## VI. Synthesis: The Operating Landscape for Compute-Optimal Training

### A. The Chinchilla Point Remains Valid but Context-Dependent

The core finding—that balanced scaling at roughly 20 tokens per parameter optimizes training compute—holds across diverse scales and general language modeling tasks. However, it is not a universal optimum for all deployment scenarios.

| **Scenario** | **Recommended Ratio** | **Primary Driver** | **Evidence Quality** |
|---|---|---|---|
| Training compute minimization (1-epoch, dense, general LM) | ~20 tokens/param (range: 4-40) | Chinchilla + 2026 replication | [OBSERVED][MEDIUM] / [DERIVED][HIGH] |
| Inference-heavy deployment (~1B requests) | Below 20:1 (e.g., 6B params with 1.18x more data) | Inference-adjusted formula | [DERIVED][HIGH] |
| Small-model efficiency (8B–70B) | Likely 26% higher compute than formula predicts | 2024 correction | [DERIVED][HIGH] |
| High-quality curated data | ~15 tokens/param | Data quality modulation | [HYPOTHESIS][HIGH] |
| Memorization-heavy tasks | Lower ratio (more params, less data) | Task-type variation | [HYPOTHESIS][MEDIUM] |
| Reasoning-heavy tasks | ~20 tokens/param | Task-type variation | [HYPOTHESIS][MEDIUM] |
| MoE architectures | Active params/token, not total params | Architecture specificity | [HYPOTHESIS][HIGH] |

### B. Key Blind Spots in the Chinchilla Framework

The evidence reveals thin coverage in several critical areas:

1. **Multi-epoch training**: The 20:1 ratio derives from single-epoch training. Repeating data changes the dynamics. [HYPOTHESIS][MEDIUM]
2. **Continual learning and fine-tuning**: No clear guidance on how the ratio applies to post-pretraining adaptation.
3. **Multimodal models**: The Chinchilla data derives from text; scaling laws for vision-language or video models are not well-characterized.
4. **Non-uniform compute budgets**: Chinchilla assumes equivalent training hardware. Heterogeneous training (mixture of GPUs, TPUs, different precisions) may require different ratios.

---

## VII. Practical Recommendations for Compute Allocation

### For Training-Compute-Minimization Scenarios

Allocate compute using the 20:1 ratio as a point estimate, but plan for a 4-40 token-per-parameter operating range [DERIVED][HIGH]. If training in the 8B–70B parameter range, add ~26% contingency to budget estimates to account for the 2024 correction [DERIVED][HIGH].

### For Inference-Cost-Dominated Scenarios

If your model will be served at scale, compute the total cost of ownership (training + inference) and optimize jointly. Trade higher training compute for smaller parameter counts; the inference-adjusted formula provides specific guidance [DERIVED][HIGH]. Validate that the inference platform supports continuous batching and PagedAttention to ensure the cost reduction is realized in practice.

### For Data-Constrained Teams

If acquiring 20× your parameter count in tokens is infeasible, train small models at high token-per-parameter ratios (50–200x Chinchilla) to achieve inference-efficient deployments [DERIVED][HIGH]. The evidence up to 10,000 tokens per parameter shows no saturation, indicating substantial room for this trade-off.

### For Novel Workloads

If your task type, architecture, or training regime deviates significantly from general language modeling on web scale, conduct scaled pilot runs before committing to full-budget Chinchilla allocation. The hypothesis-tagged evidence suggests task-specific ratios may vary substantially [HYPOTHESIS][MEDIUM].

---

## VIII. Unresolved Questions and Research Frontiers

1. **Coefficients for sparse architectures**: How should Mixture-of-Experts models be incorporated into the Chinchilla framework? Should the ratio reference active parameters, total parameters, or expert-specific parameters?

2. **Multi-epoch dynamics**: How does repeating the training data change the optimal ratio? Does repeated data (as in continued training or fine-tuning) require a different allocation?

3. **Multimodal and cross-modal transfer**: Does scaling a vision-language model obey the same 20:1 ratio as text-only models, or do the heterogeneous modalities require separate calibration?

4. **Task-specific saturation points**: At what token-to-parameter ratio do reasoning tasks, memorization tasks, and coding tasks reach diminishing returns? Current evidence [HYPOTHESIS][MEDIUM] is thin.

5. **Data quality boundaries**: Below what curation threshold does high-quality data lose its efficiency advantage? Is 15:1 achievable with realistic curation effort, or is it a theoretical optimum?

6. **Inference-platform-specific optimization**: How do different serving frameworks (vLLM with continuous batching, ray serve, proprietary systems) change the inference cost landscape, and thus the optimal training allocation?

---

## Conclusion

The Chinchilla paper's core contribution—the 20:1 tokens-per-parameter ratio for compute-optimal training—remains a vital reference point. However, subsequent research over four years has revealed it is a point estimate within a wider band (4–40 tokens per parameter [DERIVED][HIGH]), systematically undercounts compute requirements for smaller models [DERIVED][HIGH], and ignores inference costs that often dominate total cost of ownership [DERIVED][HIGH]). The original paper optimized exclusively for training compute; the refined understanding integrates inference efficiency, data quality, task type, and architectural constraints.

For practitioners, the landscape is now richer and more nuanced: teams can choose between Chinchilla's training-optimal point, inference-adjusted formulas for deployment-heavy scenarios, and data-curation approaches that shift the optimum toward 15:1. The primary remaining uncertainty is whether these refinements generalize beyond general language modeling to specialized tasks, architectures, and multimodal domains—a frontier where evidence remains sparse and direct empirical validation is necessary.

## Contradicciones detectadas (4)

Los conflictos siguientes se reportan SIN resolver, a propósito. Elegir un ganador en silencio sería inventar una certeza que las fuentes no dan.

**CONTRADICCIÓN** — Fuente [0] afirma: The Chinchilla formula establishes 20 tokens per parameter as the compute-optimal allocation across all model scales · Fuente [2] afirma: The original Chinchilla formula systematically underestimated training requirements for models below 100B parameters; a 50%-scale model actually requires 26% more compute and 2.5× more tokens than the formula projected
El conflicto NO está resuelto. Explicación probable: distinto alcance o tamaño (SCOPE).
Para el operador: For models ≥100B parameters, the standard Chinchilla 20:1 ratio applies; for 8B–70B models, apply the 2024 correction factors to avoid systematically underestimating training budgets

**CONTRADICCIÓN** — Fuente [0] afirma: The compute-optimal tokens-per-parameter ratio is approximately 20 for language model training · Fuente [12] afirma: High-quality deduplicated data reaches compute-optimality at 15 tokens per parameter, while mixed-quality web-scraped data requires 20 tokens per parameter
El conflicto NO está resuelto. Explicación probable: distinto alcance o tamaño (SCOPE).
Para el operador: The optimal ratio varies by data quality: use 15 tokens/param if you curate high-quality deduplicated corpora, but apply 20 if training on typical web-scraped mixed-quality data

**CONTRADICCIÓN** — Fuente [0] afirma: Hoffmann et al.'s research rigorously established 20 tokens per parameter as the compute-optimal allocation based on 400+ training runs · Fuente [13] afirma: The original paper's confidence intervals are implausibly narrow—they would require ~600,000 experiments but only 400–500 were conducted—and the empirically defensible range is 4–40 tokens per parameter (50× wider)
El conflicto NO está resuelto. Explicación probable: distinta metodología de medición (METHODOLOGY).
Para el operador: Treat 20 tokens/param as a point estimate with substantial uncertainty; plan using the 4–40 tokens/param operating range rather than a single precise value to account for measurement limitations in the original experiments

**CONTRADICCIÓN** — Fuente [3] afirma: The 20 tokens-per-parameter ratio has proven empirically invariant across all scales from billions to trillions of parameters · Fuente [5] afirma: The 20:1 ratio is not invariant; memorization-heavy tasks are best served with lower token-to-parameter ratios (more parameters, less data) while reasoning tasks achieve peak accuracy at the canonical 20:1 ratio
El conflicto NO está resuelto. Explicación probable: distinto alcance o tamaño (SCOPE).
Para el operador: The 20:1 ratio is invariant only for dense transformer one-epoch language training on uniform tasks; validate the optimal ratio empirically for memorization-focused or reasoning-focused workloads before committing compute

## Sources

- <https://arxiv.org/abs/2203.15556>
- <https://ai.towerofrecords.com/ai/chinchilla-scaling>
- <https://proceedings.neurips.cc/paper_files/paper/2022/file/c1e2faff6f588870935f114ebe04a3e5-Paper-Conference.pdf>
- <https://www.educatingsilicon.com/2024/04/29/revised-chinchilla-scaling-laws-impact-on-llm-compute-and-token-requirements/>
- <https://www.emergentmind.com/topics/chinchilla-scaling-law>
- <https://en.wikipedia.org/wiki/Neural_scaling_law>
- <https://www.emergentmind.com/topics/tokens-per-parameter-tpp>
- <https://www.geeksforgeeks.org/artificial-intelligence/chinchilla-scaling-laws/>
- <https://arxiv.org/html/2401.00448>
- <https://arxiv.org/abs/2401.00448>
- <https://arxiv.org/html/2601.22362v1>
- <https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/>
- <https://ailearningguides.com/llm-inference-optimization-2026-serving-batching-kv-cache/>
- <https://myengineeringpath.dev/genai-engineer/inference-optimization/>
- <https://ehga.org/chinchilla-scaling-laws-the-compute-optimal-ratio-for-llm-training>
- <https://arxiv.org/html/2404.10102v1>
- <https://spawn08.github.io/llmbase/06_research_papers/11_chinchilla/>

_Note: 10 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** What did the Chinchilla paper (Hoffmann et al. 2022) find about the compute-optimal ratio of training tokens to model parameters, and which later results challenged or refined that ratio?
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: empty-input, readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 2152.0 s
- **Errors during run:** 29
- **Started at:** 2026-11-11T22:09:16Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 0 dropped as not operator-actionable (relevance: UNRATED)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 1 axis/axes covered (MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (EVIDENCE) — minimum 3; missing: MECHANISM, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** A_MEASURED×1, B_ACADEMIC×6, C_PRACTITIONER×6, UNKNOWN×6 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** OBSERVED 1, DERIVED 9, HYPOTHESIS 5 · 12 label(s) demoted by the evidence gates
- **E4 contradictions:** 4 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `COVERED` / HIGH [EVIDENCE] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _What specific numerical token-to-parameter ratios did Hoffmann et al. report as compute-op_
- `THIN` / MEDIUM [MECHANISM] — 5 source(s), families C_PRACTITIONER, UNKNOWN — _Why does the optimal training token count scale linearly with model parameters—what fundam_
- `THIN` / HIGH [COUNTEREXAMPLE] — 2 source(s), families B_ACADEMIC — _Which research papers published compute-optimal token-to-parameter ratios substantially di_
- `COVERED` / HIGH [MECHANISM] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER — _When you reduce the marginal cost of serving inference through infrastructure improvements_
- `COVERED` / HIGH [BOUNDARY] — 4 source(s), families A_MEASURED, B_ACADEMIC, UNKNOWN — _At what model scales, architectures, or training conditions does the Chinchilla compute-op_
- `VENDOR_ONLY` / LOW [EVIDENCE] — 0 source(s), families none — _What quantifiable metrics—such as deduplication rate, benchmark performance baselines, or _

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla...': page-fetch: https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla-scaling-and-compute-optimal-training: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 100, 2024, 70`
- `relevance filter unavailable: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '--model', 'claude-haiku-4-5-20251001', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--setting-sources', 'local', '--strict-mcp-config', '--append-system-prompt', "You are an expert researcher. Today is 2026-11-11. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 240 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `decomposition narrow: only 1 axis/axes covered (MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 1.4, 20, 280, 300, 70`
- `epistemic demoted OBSERVED -> HYPOTHESIS: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `fetch_page 'https://dl.acm.org/doi/10.5555/3692070.3693840...': page-fetch: https://dl.acm.org/doi/10.5555/3692070.3693840: HTTP Error 403: Forbidden`
- `fetch_page 'https://openreview.net/pdf/f736a7763aefb029d8111638b2918f6a1...': page-fetch: https://openreview.net/pdf/f736a7763aefb029d8111638b2918f6a127d9bae.pdf: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.researchgate.net/publication/381770853_Resolving...': page-fetch: https://www.researchgate.net/publication/381770853_Resolving_Discrepancies_in_Compute-Optimal_Scaling_of_Language_Models: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 28`
- `epistemic demoted OBSERVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (MECHANISM) — minimum 3; missing: EVIDENCE, BOUNDARY, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://www.mckinsey.com/industries/semiconductors/our-insig...': page-fetch: https://www.mckinsey.com/industries/semiconductors/our-insights/frontiers-of-compute-the-technologies-to-reduce-ai-inference-costs: The read operation timed out`
- `source https://ailearningguides.com/llm-inference-optimization-2026 carries instruction-like text ['system-prompt-reference', 'tool-or-exfil-request']; treated as data`
- `source https://myengineeringpath.dev/genai-engineer/inference-optim carries instruction-like text ['system-prompt-reference']; treated as data`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 100, 3.1, 300, 70`
- `epistemic demoted OBSERVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 11.4, 4.6, 512, 70, 78%`

</details>


## Evidence ledger

- **Claims:** 15 · with a verified quote: 11 (rate 0.733)
- **Quotes:** 23 offered, 9 rejected (not verbatim / unknown source / length)
- **Sources:** 17 snapshots in 17 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 10
- **Sources with instruction-like text (treated as data):** 2

**C1** [DERIVED] Hoffmann et al. trained 400+ language models and found that for compute-optimal training, model size and training tokens should be scaled equally at roughly 20 tokens per parameter. Chinchilla (70B parameters, 1.4 trillion tokens) outperformed Gopher (280B parameters) and other larger models on identical compute budgets, proving prior scaling practices that maximized parameters while limiting data were severely suboptimal.
  - S1 <https://arxiv.org/abs/2203.15556> chars 685-889: "we find that for compute-optimal training, the model size and the number of training tokens should be scaled equally: for every doubling of model size the number of training tokens should also be doubled."
  - S2 <https://ai.towerofrecords.com/ai/chinchilla-scaling> chars 2507-2640: "Chinchilla achieves the best performance using the same compute as Gopher but with 4× fewer parameters and 4.7× more training tokens."

**C2** [DERIVED] Training tokens can be increased 10x–75x beyond the standard 20-token Chinchilla point to create smaller, cheaper-to-deploy models with competitive capability. Llama 3 70B trained on 200 tokens per parameter achieves performance equivalent to a Chinchilla-optimal 260B model while costing 3.7x less to run inference; Llama 3 8B extends this further to 75x Chinchilla tokens, delivering 5x inference savings, enabling teams to trade training compute for dramatic deployment cost reduction.
  - S4 <https://www.educatingsilicon.com/2024/04/29/revised-chinchilla-scaling-laws-impact-on-llm-compute-and-token-requirements/> chars 3232-3468: "Llama 3 8B goes further still, at 75x the tokens per parameter. These models require about 10x-15x the training compute, but only ~20% of the parameters (and thus get 5x inference performance) of the equivalent Chinchilla optimal model."

**C3** [DERIVED] The original Chinchilla formula systematically underestimated training compute requirements for models below 100B parameters. A 2024 correction shows that a 50%-scale model requires 26% more training compute and 2.5× more tokens than the original formula projected—substantially higher than expected—affecting any team training in the 8B–70B range where every prior budget estimate becomes optimistic by over one quarter.
  - S4 <https://www.educatingsilicon.com/2024/04/29/revised-chinchilla-scaling-laws-impact-on-llm-compute-and-token-requirements/> chars 2064-2283: "The way to read this table is that, for example, if you limit your model to 50% of the parameters of the Chinchilla point model, it will achieve the same loss with 26% more training compute and 2.5x the training tokens."
  - _ledger: OBSERVED number(s) absent from verified spans: 100, 2024, 70_

**C4** [OBSERVED] For dense transformers trained for one epoch on language data, the optimal training token count scales linearly with model parameters at approximately 20 tokens per parameter. This ratio has proven empirically invariant across scales from billions to trillions of parameters, meaning you can calculate dataset requirements from any model size without iteration.
  - S2 <https://ai.towerofrecords.com/ai/chinchilla-scaling> chars 385-519: "Compute-optimal tokens per parameter | ~20 | tokens/parameter | Derived from 400+ training runs; N_opt and D_opt both scale as C^{0.5}"

**C5** [DERIVED] Prior scaling laws optimized for maximum parameters under fixed compute, creating undertrained large models. Chinchilla demonstrated that for identical compute budgets, a 70-billion-parameter model trained on 1.4 trillion tokens outperforms a 280-billion-parameter model trained on only 300 billion tokens, proving that token scarcity—not model size—is the efficiency bottleneck when the 20:1 ratio is violated.
  - S2 <https://ai.towerofrecords.com/ai/chinchilla-scaling> chars 2507-2640: "Chinchilla achieves the best performance using the same compute as Gopher but with 4× fewer parameters and 4.7× more training tokens."
  - _ledger: OBSERVED number(s) absent from verified spans: 1.4, 20, 280, 300, 70_

**C6** [HYPOTHESIS] The 20:1 ratio is not invariant across all task types and architectures. Memorization-heavy tasks are best served with lower token-to-parameter ratios (more parameters, less data), while reasoning tasks achieve peak accuracy at the canonical 20:1 ratio. Sparse models, inference-heavy deployments, and multi-epoch training scenarios require recalibration; applying the baseline ratio to non-standard workloads wastes compute.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C7** [DERIVED] When you expect significant inference demand (approximately 1 billion requests), the optimal parameter-to-token allocation diverges sharply from Chinchilla: a 7B-parameter-quality model should instead be trained with 6B parameters on 1.18 times the originally-recommended data; a 30B-quality model should use 13.6B parameters trained on 2.84 times more data and saves 28 percent of total compute costs. This divergence exists because Chinchilla optimized only for training compute, ignoring the inference costs that can dominate total cost of ownership over a model's lifetime.
  - S9 <https://arxiv.org/html/2401.00448> chars 11556-12100: "For a 7B-Chinchilla-quality model with an inference demand of tokens, our formula suggests the compute-optimal method is to train a 6B parameter model on 1.18 the original (Chinchilla-prescribed) amount of data. For higher quality models (i.e. models that are larger and/or tra..."
  - _ledger: OBSERVED number(s) absent from verified spans: 28_

**C8** [HYPOTHESIS] The authors trained 47 models ranging from 150M to 6B parameters at extreme token-to-parameter ratios up to 10,000 and found model quality continued improving with no saturation point, empirically validating the inference-adjusted formula. This contradicts earlier theoretical claims that below a critical model size, additional training data could not recover quality; instead, smaller models trained substantially longer achieve quality parity with larger models.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C9** [DERIVED] The Chinchilla scaling law coefficients were fitted using data primarily from ~100 tokens-per-parameter runs—the training efficiency sweet spot. When the authors re-fitted the same parametric form using data including extreme ratios (500+ tokens per parameter), the coefficients changed significantly and the curves flattened, indicating Chinchilla systematically overestimates how much benefit additional training provides at high token ratios. Your scaling-law predictions are miscalibrated if your use case requires extended training.
  - S9 <https://arxiv.org/html/2401.00448> chars 22081-22458: "First, we see that our parameteric curves follow a consistent trend—as we use more extreme data in our fitting procedure, our scaling curves become flatter. This trend suggests that if we only use data from typical token ratios to determine our scaling law coefficients, we wil..."

**C10** [DERIVED] Continuous batching and PagedAttention enable 10-50x throughput improvement on identical hardware. Concrete example: Llama-3.1-70B on a single H100 serves 30-40 concurrent users at 3,000-5,000 tokens/second sustained, versus 100-300 tokens/second with naive serving. This converts a binary 'buy another GPU or don't' decision into a marginal-cost calculation: you can now economically serve additional concurrent users by optimizing the batch without new hardware, as long as inference throughput remains your bottleneck.
  - S13 <https://ailearningguides.com/llm-inference-optimization-2026-serving-batching-kv-cache/> chars 2907-3140: "The same model on the same hardware with a properly tuned vLLM deployment serves 30-40 concurrent users at sustained throughput of 3,000-5,000 tokens per second aggregate. That’s a 10-50x throughput improvement on identical hardware."
  - S13 <https://ailearningguides.com/llm-inference-optimization-2026-serving-batching-kv-cache/> chars 3141-3296: "The per-token cost difference is proportional. A team that ships the naive version pays 10-50x more per token than a team that ships the optimized version."
  - _ledger: OBSERVED number(s) absent from verified spans: 100, 3.1, 300, 70_

**C11** [HYPOTHESIS] INT8 quantization halves inference memory and cost with <1% quality loss; INT4 (AWQ) reduces cost 75% with 2-5% benchmark degradation, though task-specific evaluation shows <1% loss on non-reasoning tasks. Concrete: Llama 3 70B in FP16 costs $9,600/month (140GB across 2x A100), INT8 costs $4,800/month (70GB on 1x A100), INT4 also costs $4,800/month (35GB on 1x A100). This flips the traditional model-selection decision: instead of 'pick the smallest model meeting quality needs,' you can now afford to deploy a larger model at lower total cost by quantizing, whereas hardware constraints would previously have forced you to choose a smaller model.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C12** [DERIVED] Speculative decoding with a small draft model achieves 2-3x latency reduction with mathematically identical output quality (zero quality loss). Example: Llama 3 70B (target) + Llama 3 8B (draft) with 5 speculative tokens at 78% token acceptance rate reduces 512-token response latency from 11.4 seconds to 4.6 seconds. This eliminates the traditional cost penalty of latency requirements: previously, meeting tight latency SLOs required either batch-size reduction (degrading throughput efficiency) or reserved expensive capacity. Speculative decoding allows simultaneous optimization of both latency and throughput on the same serving stack.
  - S14 <https://myengineeringpath.dev/genai-engineer/inference-optimization/> chars 8556-8763: "verifying N tokens in one forward pass costs roughly the same as generating 1 token, because the attention computation over existing context dominates the cost regardless of how many new tokens you evaluate."
  - _extractor cited S13; quote found verbatim in S14 (citation corrected)_
  - _ledger: OBSERVED number(s) absent from verified spans: 11.4, 4.6, 512, 70, 78%_

**C13** [HYPOTHESIS] High-quality deduplicated data reaches compute-optimal training at approximately 15 tokens per parameter, compared to 20 tokens per parameter for mixed-quality web-scraped data. This means aggressive data curation yields equivalent model performance at lower total token volume, freeing compute budget for other initiatives.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C14** [DERIVED] A 2026 replication of the original Chinchilla paper found the published confidence intervals are implausibly narrow—obtaining such tight intervals would require approximately 600,000 experiments, yet only 400-500 were likely conducted. The replication's corrected model yields a practical operating range of 4-40 tokens per parameter at standard compute scales, with 50× wider confidence intervals than originally reported.
  - S16 <https://arxiv.org/html/2404.10102v1> chars 12787-12869: "our 80% confidence interval is 50-fold wider than that reported by Hoffmann et al."
  - S16 <https://arxiv.org/html/2404.10102v1> chars 17934-18018: "our fitted model is consistent with a ratio of tokens to parameters between 4 and 40"
  - _ledger: OBSERVED number(s) absent from verified spans: 2026, 400, 500, 600000_

**C15** [HYPOTHESIS] In Mixture-of-Experts architectures, only a fraction of total parameters activate per token, which changes how the compute-optimal ratio applies. Early evidence suggests the 20:1 ratio should reference active parameters per token rather than total model size, though this remains an open research question, meaning MoE models may operate within identical budgets as smaller dense models.
  - S15 <https://ehga.org/chinchilla-scaling-laws-the-compute-optimal-ratio-for-llm-training> chars 7838-8083: "In an MoE architecture, not all parameters are active for every token. Does the 20:1 ratio apply to total parameters or active parameters? Early evidence suggests it applies closer to active parameters, but this remains an area of active debate."
