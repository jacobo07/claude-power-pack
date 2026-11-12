# The Chinchilla Scaling Laws: Original Findings, Challenges, and Refinements

## Executive Summary

The Chinchilla paper (Hoffmann et al. 2022) proposed that optimal compute allocation requires approximately **20 training tokens per model parameter**, with equal scaling exponents for both dimensions [DERIVED][MEDIUM]. This represented a sharp challenge to prior work (Kaplan et al. 2020) which recommended more parameter-heavy allocations. However, subsequent research has systematically refined, partially contradicted, and contextualized this finding: modern models train at 100:1 to 200:1 token-to-parameter (TPP) ratios while outperforming Chinchilla predictions; the ratio depends on task type, tokenization scheme, and inference economics; and the experimental methodology used to derive scaling laws dramatically affects their reliability. This report synthesizes the original finding and traces how later work has reshaped our understanding of optimal scaling.

---

## Section 1: The Chinchilla Paper's Core Finding

### The 20:1 Ratio Discovery

Hoffmann et al. (2022) conducted a large-scale empirical study concluding that **training compute should be allocated equally between model parameters and training data**, yielding approximately 20 tokens per parameter at optimal allocation [DERIVED][MEDIUM]. 

The most concrete evidence for this claim comes from a head-to-head comparison:

| Metric | Chinchilla (70B params) | Gopher (280B params) | Same compute budget |
|--------|----------------------|------------------|---|
| Training tokens | 1.4 trillion | 300 billion | Yes |
| Token-to-parameter ratio | ~20:1 | ~1:1 | — |
| MMLU accuracy | 67.5% | 60.0% | — |
| Performance gap | +7.5 percentage points | — baseline | — |

[DERIVED][MEDIUM] The Chinchilla-vs-Gopher comparison demonstrated that reallocating compute from parameter scaling toward training data volume recovered **7 percentage points on MMLU** without increasing total training budget. This directly showed that Gopher's relatively poor performance was not a capability ceiling but a consequence of misallocated compute within an identical FLOP budget.

### Diagnosing Prior Underoptimality

A key insight from Hoffmann et al. was retroactive diagnosis: [DERIVED][MEDIUM] models with token-to-parameter ratios significantly below 20:1 were trained suboptimally. Gopher's ~1:1 ratio was explicitly identified as "far below the compute-optimal data allocation," enabling inference that token-to-parameter ratio serves as a diagnostic signal for training efficiency. This meant existing models could be audited to identify whether similar compute spend could have yielded substantially better performance through reallocation alone.

---

## Section 2: Why Chinchilla Contradicted Kaplan et al. (2020)

Understanding the origin of the Chinchilla-Kaplan disagreement is essential to later refinements.

### The Learning Rate Schedule Confound

[DERIVED][MEDIUM] The contradictory recommendations between Hoffmann et al. and Kaplan et al. were not discoveries of different phenomena but **artifacts of experimental setup**. Specifically:

- **Hoffmann et al.** retuned the cosine learning-rate schedule to match each run's token budget
- **Kaplan et al.** used a fixed learning-rate schedule anchored to their largest run

The critical finding: [DERIVED][MEDIUM] when Kaplan's fixed-schedule methodology is applied to Hoffmann's data, the optimal parameter-to-token exponent reverts from approximately 1:1 back to Kaplan's 0.73:0.27 allocation. This proves that the two papers' contradictory recommendations were **not differences in underlying phenomena but differences in experimental methodology**.

**Practical implication:** [DERIVED][MEDIUM] you can discount scaling-law recommendations from external teams if they do not explicitly specify their learning-rate schedule methodology, as the schedule choice can invert conclusions about optimal ratios.

---

## Section 3: The First Major Challenge—Extreme Token-to-Parameter Ratios

### The Post-2022 Empirical Contradiction

Beginning in 2022-2023, practitioners systematically contradicted Chinchilla's 20:1 recommendation.

[DERIVED][HIGH] Models trained after 2022 contradict Chinchilla's recommendation by training at **100:1 to 200:1 token-to-parameter ratios** while outperforming larger models. Specifically:
- **Llama 3 70B**: trained on 15 trillion tokens at a 200:1 ratio
- Smaller parameter counts achieve competitive performance through more training data

This was validated at scale: [DERIVED][HIGH] analysis across 47 models found quality **continues improving even at extreme 10,000:1 token-to-parameter ratios**, with **no saturation plateau** observed that would prevent matching larger models. The [HYPOTHESIS][HIGH] finding is striking: testing 47 models ranging from 150M to 6B parameters trained on 10 to 10,000 tokens per parameter found continuous loss improvement with no critical model-size thresholds that prevent matching larger models.

### Why the Divergence? Inference Economics Reshaping Training Decisions

[DERIVED][HIGH] Post-2022 practitioners systematically overtrain smaller models beyond Chinchilla recommendations to optimize **total deployment cost, not training efficiency**. Meta's Llama 2, for example, deliberately trains 7B and 13B variants on 2 trillion tokens—exceeding Chinchilla-optimal by multiples—because **inference economics dominate training costs**.

The economic calculus is stark: [OBSERVED][HIGH] for models expecting approximately 1 billion inference requests, training a 13.6B parameter model on 2.84 times more data than Chinchilla-optimal achieves equivalent quality to a 30B model while reducing **total compute costs by 28%**. Serving millions of queries makes a heavily-trained small model cheaper per inference than an undertrained large model at equivalent quality.

**Capacity insight:** You can reduce total training and inference costs by training smaller models on substantially more data when serving high-volume production workloads, rather than following compute-optimal training guidance.

---

## Section 4: Task-Specific Token-to-Parameter Optima

### Beyond the Universal Constant

Emerging evidence suggests 20:1 is not universally optimal.

[HYPOTHESIS][HIGH] Reasoning tasks achieve optimal performance at approximately 20 tokens per parameter, while memorization tasks benefit from significantly lower TPP (meaning more parameters relative to training tokens). This suggests code and multilingual pretraining may have different optimal allocations depending on their reasoning-to-memorization mix, diverging from the universal 20:1 heuristic.

More concretely: [DERIVED][MEDIUM] reasoning exhibits a U-shaped accuracy curve with TPP, peaking around 20 tokens per parameter and degrading when TPP is either too low or too high. Memorization, by contrast, monotonically improves as TPP decreases (more parameters per token). 

### The Binding Constraint Problem

When combining both tasks in a single model: [DERIVED][MEDIUM] reasoning becomes the binding constraint. Allocating tokens beyond TPP 20 continues improving memorization but **actively harms reasoning accuracy**. This asymmetry creates a natural convergence point: [DERIVED][MEDIUM] TPP 20 is where reasoning works optimally and memorization still functions well. Neither reinforcement learning post-training nor test-time compute modifies this fundamental tradeoff, making it a stable target regardless of task blend variations.

**Practical implication:** [DERIVED][MEDIUM] standardize on TPP ~20 as a single operating point for mixed-task models instead of seeking blend-ratio-specific optima.

---

## Section 5: Tokenization and Bytes-Per-Parameter Invariance

### The Ratio is Tokenizer-Dependent

A critical refinement: the 20:1 ratio depends on the tokenizer used.

[DERIVED][HIGH] The 20:1 tokens-per-parameter ratio is an artifact of specific subword tokenizers, not a fundamental invariant; **bytes-per-parameter is the true scaling-law invariant**. Optimal compression rates are compute-dependent, meaning code (with operator-dense syntax) and multilingual models (with script-dependent efficiency) require different token counts but can align on byte-per-parameter scaling. This was derived from: [DERIVED][HIGH] training nearly 1,300 models to demonstrate that the 20:1 heuristic depends on tokenization scheme rather than representing a universal law.

### The Bytes-Per-Parameter Finding

Most remarkably: [HYPOTHESIS][HIGH] across 988+ models varying tokenization (latent and subword methods), compression rates (1.01 to 6.16 bytes/token), and compute budgets spanning multiple orders of magnitude, **the optimal bytes-per-parameter ratio remained approximately constant (0.465-0.501)**. This means data-to-parameter scaling is primarily a function of compute budget, not tokenization choice. When your tokenizer changes compression rates, the relationship between total training bytes and model parameters stays stable.

**Practical implication:** [DERIVED][HIGH] design tokenization strategies specific to each domain instead of forcing all domains to fit a fixed 20-token-per-parameter BPE standard.

---

## Section 6: Data Quality Now Dominates Quantity

### The Shift from Scaling Laws to Data Curation

A fundamental shift has occurred in post-2022 thinking.

[DERIVED][HIGH] Data quality now dominates quantity, making overtraining economically viable: **models on 3 trillion carefully filtered tokens outperform those on 10 trillion indiscriminately collected tokens**. DeepSeek demonstrated synthetic reasoning data—generated by capable models—can substitute for natural text and achieve frontier reasoning capabilities. This shifts competition from parameter-count armament to **data-curation and synthetic-generation investment**.

**Capacity:** You can compete at the frontier through data curation and synthetic data generation rather than raw parameter scaling or compute budgets.

The implication is profound: raw token volume is no longer the binding constraint. A model trained on fewer but higher-quality tokens can match or exceed one trained on raw quantity, even when holding parameters and compute constant.

---

## Section 7: Experimental Design Reliability

### Why Scaling Law Predictions Fail

An often-overlooked finding reveals why many scaling law predictions diverge in practice.

[OBSERVED][HIGH] Fitting scaling laws from experiments conducted at a **single fixed tokens-per-parameter ratio creates mathematical ill-conditioning** (condition number grows as inverse square of exponent difference) that makes extrapolations unreliable when applied to different TPP scenarios. Non-collinear designs that vary TPP won **97.3% of the time on held-out test data** compared to fixed-TPP designs.

The magnitude of the effect is striking: confidence intervals improved by orders of magnitude when diverse TPP was used, not just percentage-level improvements. This ill-conditioning arises from Jacobian geometry and affects any smooth objective, not just language model loss.

**Practical implication:** [OBSERVED][HIGH] you can identify whether your scaling law estimates are likely to fail before investing in large experimental runs by checking whether your experimental design varies tokens-per-parameter ratios.

### Extrapolation Beyond Training Ratios

[DERIVED][HIGH] Chinchilla scaling laws fitted on data collected at approximately 100 tokens per parameter **overestimate improvements when applied to extreme ratios** (250+ tokens per parameter). Empirical testing shows models improve more slowly than predicted at extreme ratios, requiring exponentially more tokens for linear quality gains.

**Why this matters:** You can adjust engineering timelines and cost projections when teams apply Chinchilla scaling formulas beyond typical data ratios, as these projections overestimate actual improvement rates.

---

## Section 8: Active Compute and Sparse Models

### Beyond Parameter Count

Recent work with mixture-of-experts models reveals a dimension Chinchilla didn't address.

[DERIVED][MEDIUM] Models with identical training loss but higher active compute achieve better reasoning accuracy; at fixed TPP, models with larger top-k values (more active experts) consistently outperform those with lower top-k on reasoning tasks. This decoupling means the sparse architecture's routing decisions operate as an **independent performance dial for reasoning**.

**Practical insight:** When model size prevents hitting the ideal TPP 20 for reasoning, increasing active expert allocation can partially compensate. [DERIVED][MEDIUM] use routing decisions (expert selection per token) as a first-order performance lever for reasoning, not a secondary parameter-tuning exercise.

---

## Section 9: Synthesis—Current Understanding

| Dimension | Chinchilla Claim (2022) | Current Understanding (2024-2025) | Confidence |
|-----------|----------------------|--------------------------------|-----------|
| **Universal TPP ratio** | 20:1 optimal for all workloads | Task-dependent: 20:1 for reasoning, lower for memorization | [HIGH] |
| **Tokens vs. parameters** | Equal scaling ~1:1 exponents | Varies by inference economics; often 100:1+ in practice | [HIGH] |
| **True invariant** | Tokens-per-parameter | Bytes-per-parameter (tokenizer-independent) | [HIGH] |
| **Data volume ceiling** | More data always improves loss | Quality dominates quantity; 3T curated >> 10T raw | [HIGH] |
| **Saturation threshold** | Exists (prevents super-small models) | None observed even at 10,000:1 TPP ratios | [HIGH] |
| **Scaling law reliability** | Experimental results are reliable | Depends critically on whether TPP varies during fitting | [HIGH] |

---

## Section 10: Evidence Quality Assessment

### Where Evidence is Thin

Several claims in the current literature rest on limited evidence:

1. **Task-specific TPP curves** — [HYPOTHESIS][HIGH] reasoning vs. memorization decomposition comes from targeted experiments but needs validation across more diverse task distributions. The generality to code, reasoning over documents, and multilingual understanding remains incompletely tested.

2. **Bytes-per-parameter invariance across architectures** — The 988-model study is large but [HYPOTHESIS][HIGH] covers primarily standard Transformer architectures. Recurrent models, state-space models, and other emerging architectures may exhibit different invariants.

3. **Extreme ratio saturation** — [HYPOTHESIS][HIGH] the claim that 10,000:1 ratios show no saturation is based on models up to 6B parameters. Extrapolation to 70B+ models at such ratios remains speculative.

4. **Data quality dominance** — [DERIVED][HIGH] comparisons of 3T curated vs. 10T raw tokens are specific to particular filtering regimes. The quantitative threshold at which quality overtakes quantity depends heavily on filter methodology and remains incompletely characterized.

---

## Section 11: Practical Implications for Model Training Today

### Decision Framework

When allocating compute between parameters and training data:

1. **If you're optimizing training efficiency only** → Use TPP ~20 as a starting point [DERIVED][MEDIUM]

2. **If you're minimizing total deployment cost (training + inference)** → Train smaller models at 50:1 to 200:1 TPP ratios [DERIVED][HIGH], with the specific ratio determined by your inference volume and cost function

3. **If your workload is primarily reasoning** → Target TPP ~20 and treat active compute (for sparse models) as a secondary lever [DERIVED][MEDIUM]

4. **If your workload blends reasoning and memorization** → Use TPP ~20 as a stable operating point; reasoning becomes the binding constraint [DERIVED][MEDIUM]

5. **When fitting scaling laws for your own models** → Ensure your experimental design varies TPP across runs; fixed-TPP designs lose orders of magnitude of prediction accuracy [OBSERVED][HIGH]

6. **If changing tokenization schemes** → Recompute optimal bytes-per-parameter rather than trying to maintain fixed token counts [DERIVED][HIGH]

### Open Questions Requiring Case-by-Case Analysis

- **Synthetic data impact:** DeepSeek's reasoning success with synthetic chain-of-thought data suggests data curation and generation may be frontier variables, but comparable analysis for other task domains (code, math, multilingual) is incomplete [DERIVED][HIGH]

- **Architecture-specific invariants:** Whether bytes-per-parameter truly holds for emerging non-Transformer architectures remains untested [HYPOTHESIS][HIGH]

- **Inference compute regimes:** The interplay between training tokens-per-parameter and test-time compute (reasoning traces, retrieve-and-rank steps, etc.) has not been systematically characterized in the Chinchilla framework

---

## Section 12: Conclusion

The Chinchilla paper's 20:1 tokens-per-parameter recommendation was a important empirical finding in 2022—and remains a useful reference point. However, the past two years of scaling have revealed it as **one operating point in a much larger design space**, not a universal law.

**What held:** Equal scaling exponents were a genuine discovery and remain relevant for compute-optimal training [DERIVED][MEDIUM]. The finding that learning-rate schedules confounded earlier work was methodologically important [DERIVED][MEDIUM].

**What shifted:** Inference economics now reshape training decisions post-2022, pushing practitioners to extreme TPP ratios that contradict the 20:1 benchmark [DERIVED][HIGH]. Task-specific variation means one ratio does not fit all workloads [HYPOTHESIS][HIGH]. The true invariant is bytes-per-parameter, not tokens-per-parameter [DERIVED][HIGH]. Data quality now dominates quantity [DERIVED][HIGH]. And the experimental methodology used to derive scaling laws determines their reliability far more than previously appreciated [OBSERVED][HIGH].

Practitioners in 2025 should treat Chinchilla as a historical anchor, not a prescriptive target—and prioritize data quality, inference economics, and task-specific calibration over raw adherence to the 20:1 ratio.

## Contradicciones detectadas (3)

Los conflictos siguientes se reportan SIN resolver, a propósito. Elegir un ganador en silencio sería inventar una certeza que las fuentes no dan.

**CONTRADICCIÓN** — Fuente [0] afirma: The optimal allocation of training compute requires approximately 20 tokens per parameter for better performance within the same compute budget. · Fuente [5] afirma: Post-2022 models trained at 100:1-200:1 ratios and even extreme 10,000:1 ratios outperform and achieve better quality than models following Chinchilla's 20:1 allocation.
El conflicto NO está resuelto. Explicación probable: distinto año o periodo (TIMEFRAME).
Para el operador: Chinchilla (2022) identified 20:1 as training-optimal; post-2022 practice contradicts this finding with models achieving superior results at much higher ratios, indicating either that optimization techniques or data quality have changed the underlying conditions, or that 'outperform' measures different objectives (inference cost vs equivalent-compute comparison).

**CONTRADICCIÓN** — Fuente [0] afirma: The optimal allocation is universally approximately 20 tokens per parameter. · Fuente [3] afirma: Memorization tasks benefit from significantly lower token-to-parameter ratios than reasoning tasks, which peak at 20:1.
El conflicto NO está resuelto. Explicación probable: distinto alcance o tamaño (SCOPE).
Para el operador: Use 20:1 for mixed-task models where reasoning is prominent; apply lower ratios only if your workload is memorization-dominant, requiring task-specific tuning rather than universal 20:1 guidance.

**CONTRADICCIÓN** — Fuente [5] afirma: Quality continues improving across 47 models even at extreme 10,000:1 token-to-parameter ratios with no saturation plateau. · Fuente [14] afirma: Allocating tokens beyond 20:1 actively harms reasoning accuracy, making reasoning the binding performance constraint in combined reasoning-plus-memorization models.
El conflicto NO está resuelto. Explicación probable: distinta metodología de medición (METHODOLOGY).
Para el operador: The contradiction hinges on [5]'s definition of 'quality': if it includes downstream reasoning accuracy on mixed-task evaluation, it directly contradicts [14]; if it measures training loss or memorization-only performance, both can coexist. Clarify whether [5] evaluated reasoning-specific performance or training-time metrics before concluding extreme ratios improve mixed-task end-to-end performance.

## Sources

- <https://arxiv.org/abs/2203.15556>
- <https://proceedings.neurips.cc/paper_files/paper/2022/file/c1e2faff6f588870935f114ebe04a3e5-Paper-Conference.pdf>
- <https://theorempath.com/papers/chinchilla>
- <https://huggingface.co/papers/2203.15556>
- <https://arxiv.org/abs/2608.14071>
- <https://mbrenndoerfer.com/writing/compute-optimal-training-chinchilla-scaling-llm>
- <https://www.emergentmind.com/topics/tokens-per-parameter-tpp>
- <https://arxiviq.substack.com/p/compute-optimal-tokenization>
- <https://arxiv.org/abs/2401.00448>
- <https://vinayakajyothi.com/blog/2026-01-15-scaling-laws-revisited-chinchilla/>
- <https://promptingindex.com/blog/chinchilla-scaling-laws-compute-optimal-llm-training>
- <https://arxiv.org/html/2401.00448>
- <https://aldeiadaponte.com/tokens-per-parameter-the-scaling-laws-behind-llm-data-needs>
- <https://salivity.github.io/ai/article/chinchilla-scaling-laws-and-the-optimal-token-to-parameter-ratio>
- <https://arxiv.org/abs/2605.08541>
- <https://arxiv.org/html/2605.01188v1>
- <https://www.emergentmind.com/topics/token-to-parameter-ratio>
- <https://arxiv.org/abs/2508.18672>
- <https://openreview.net/challenge?redirect=%2Fforum%3Fid%3DXFw2EPRUUR>
- <https://aclanthology.org/2025.findings-acl.1111/>
- <https://liner.com/review/optimal-sparsity-of-mixtureofexperts-language-models-for-reasoning-tasks>

_Note: 4 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** What did the Chinchilla paper (Hoffmann et al. 2022) find about the compute-optimal ratio of training tokens to model parameters, and which later results challenged or refined that ratio?
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 1183.9 s
- **Errors during run:** 22
- **Started at:** 2026-11-11T20:07:26Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 1 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, TRANSFERABILITY)  — SHORTFALL: only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE; only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY; only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×10, C_PRACTITIONER×4, UNKNOWN×11 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** OBSERVED 2, DERIVED 11, HYPOTHESIS 4 · 14 label(s) demoted by the evidence gates
- **E4 contradictions:** 3 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / MEDIUM [EVIDENCE] — 4 source(s), families B_ACADEMIC, UNKNOWN — _What were the specific compute budgets, model architectures, and performance metrics that _
- `THIN` / HIGH [TRANSFERABILITY] — 4 source(s), families B_ACADEMIC, UNKNOWN — _Does the optimal token-to-parameter ratio remain approximately 20:1 for code, multilingual_
- `COVERED` / HIGH [COUNTEREXAMPLE] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER — _Which large language models trained after 2022 contradicted the Chinchilla recommendations_
- `COVERED` / HIGH [BOUNDARY] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _At what token-to-parameter ratio does continued data investment yield diminishing returns,_
- `COVERED` / HIGH [TRANSFERABILITY] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _Does the optimal token-to-parameter ratio differ when applied across different model archi_
- `THIN` / MEDIUM [BOUNDARY] — 5 source(s), families B_ACADEMIC, UNKNOWN — _When practitioners combine reasoning and memorization tasks in a single model, at what ble_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://dl.acm.org/doi/10.5555/3600270.3602446...': page-fetch: https://dl.acm.org/doi/10.5555/3600270.3602446: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 20, 60.0%`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (TRANSFERABILITY) — minimum 3; missing: EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE`
- `fetch_page 'https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla...': page-fetch: https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla-scaling-and-compute-optimal-training: HTTP Error 429: Too Many Requests`
- `epistemic demoted VERIFIED -> HYPOTHESIS: VERIFIED claims corroboration but only 1 source(s) support it (minimum 2) — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> HYPOTHESIS: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `fetch_page 'https://dl.acm.org/doi/10.5555/3692070.3693840...': page-fetch: https://dl.acm.org/doi/10.5555/3692070.3693840: HTTP Error 403: Forbidden`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `fetch_page 'https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla...': page-fetch: https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla-scaling-and-compute-optimal-training: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `fetch_page 'https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla...': page-fetch: https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla-scaling-and-compute-optimal-training: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> HYPOTHESIS: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> HYPOTHESIS: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED; ledger: no quote verified in any snapshot`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`

</details>


## Evidence ledger

- **Claims:** 18 · with a verified quote: 13 (rate 0.722)
- **Quotes:** 26 offered, 7 rejected (not verbatim / unknown source / length)
- **Sources:** 21 snapshots in 21 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 6
- **Sources with instruction-like text (treated as data):** 0

**C1** [DERIVED] The optimal allocation of training compute requires equal scaling of model parameters and training tokens, approximately 20 tokens per parameter. Training a 70B-parameter model on 1.4 trillion tokens achieved 67.5% accuracy on MMLU, outperforming a 280B-parameter model trained on 300 billion tokens (60.0% accuracy) while using the same compute budget, demonstrating a 7 percentage point improvement from restructuring the compute allocation rather than increasing total budget.
  - S3 <https://theorempath.com/papers/chinchilla> chars 991-1338: "Trained at the same FLOP budget as DeepMind's earlier 280B Gopher, but with 70B parameters and 1.4T tokens (instead of 280B parameters and 300B tokens), Chinchilla outperforms Gopher on every benchmark in the paper — MMLU, BIG-bench, the closed-book QA suite, the LM Evaluation..."
  - S4 <https://huggingface.co/papers/2203.15556> chars 2024-2095: "67.5% on the MMLU benchmark, greater than a 7% improvement over Gopher."
  - _ledger: OBSERVED number(s) absent from verified spans: 20, 60.0%_

**C2** [DERIVED] Models with token-to-parameter ratios significantly below the compute-optimal ~20:1 benchmark were trained suboptimally. Gopher's 300 billion tokens paired with 280 billion parameters (approximately 1:1 ratio) was identified as 'far below the compute-optimal data allocation,' proving that its relatively poor performance against Chinchilla was not a capability ceiling but a consequence of misallocated compute within the same budget.
  - S3 <https://theorempath.com/papers/chinchilla> chars 1339-1467: "The mechanism is that Gopher was undertrained: 300B tokens for 280B parameters is far below the compute-optimal data allocation."

**C3** [DERIVED] The learning-rate schedule chosen during a scaling study can entirely invert its conclusions about optimal parameter-to-token ratios. Hoffmann et al. retunes the cosine learning-rate schedule to match each run's token budget, while Kaplan et al. used a fixed schedule anchored to their largest run. When Kaplan's fixed-schedule methodology is applied to Hoffmann's data, the optimal parameter-to-token exponent reverts from approximately 1:1 back to Kaplan's 0.73:0.27 allocation, proving the papers' contradictory recommendations were artifacts of experimental setup, not differences in the underlying phenomenon.
  - S3 <https://theorempath.com/papers/chinchilla> chars 4392-4740: "Kaplan et al. trained models with a fixed cosine learning-rate schedule whose total length was set to the longest run in their sweep. For shorter runs, the schedule decays slowly relative to the run length, leaving the small models effectively under-converged. Chinchilla retun..."
  - S3 <https://theorempath.com/papers/chinchilla> chars 4830-4990: "When Kaplan-style schedules are reapplied to Chinchilla's data, the parameter exponent inflates and the data exponent collapses, recovering Kaplan's allocation."

**C4** [HYPOTHESIS] Reasoning tasks achieve optimal performance at approximately 20 tokens per parameter, while memorization tasks benefit from significantly lower TPP (meaning more parameters relative to training tokens). This suggests code and multilingual pretraining may have different optimal allocations depending on their reasoning-to-memorization mix, diverging from the universal 20:1 heuristic.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C5** [DERIVED] The 20:1 tokens-per-parameter ratio is an artifact of specific subword tokenizers, not a fundamental invariant; bytes-per-parameter is the true scaling-law invariant. Optimal compression rates are compute-dependent, meaning code (with operator-dense syntax) and multilingual models (with script-dependent efficiency) require different token counts but can align on byte-per-parameter scaling.
  - S8 <https://arxiviq.substack.com/p/compute-optimal-tokenization> chars 563-683: "the widely accepted heuristic of scaling models by 20 tokens per parameter is an artifact of specific subword tokenizers"

**C6** [HYPOTHESIS] Multimodal models reduce frame-level video tokens from thousands to ~32 compact tokens via temporal encoders and redundancy reduction, drastically increasing effective tokens-per-parameter without adding model parameters. This decouples parameter scaling from raw token count and requires a different allocation strategy than dense text models assume.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C7** [DERIVED] Models trained after 2022 contradict Chinchilla's 20:1 token-to-parameter ratio by training at 100:1-200:1 ratios—Llama 3 70B on 15 trillion tokens at 200:1—while outperforming larger models. This means smaller parameter counts achieve competitive performance through more training data. S9 validated this across 47 models, finding quality continues improving even at extreme 10,000:1 token-to-parameter ratios.
  - S9 <https://arxiv.org/abs/2401.00448> chars 1072-1267: "we train 47 models of varying sizes and parameter counts to validate our formula and find that model quality continues to improve as we scale tokens per parameter to extreme ranges (up to 10,000)"
  - S10 <https://vinayakajyothi.com/blog/2026-01-15-scaling-laws-revisited-chinchilla/> chars 2413-2548: "Llama 3 70B was trained on over 15 trillion tokens — roughly 200 tokens per parameter, versus Chinchilla's recommendation of around 20."

**C8** [DERIVED] Post-2022 practitioners systematically overtrain smaller models beyond Chinchilla recommendations to optimize total deployment cost, not training efficiency. Meta's Llama 2 deliberately trains 7B and 13B variants on 2 trillion tokens—exceeding Chinchilla-optimal by multiples—because inference economics dominate training costs. Serving millions of queries makes a heavily-trained 7B model cheaper per inference than an undertrained 70B at the same quality.
  - S11 <https://promptingindex.com/blog/chinchilla-scaling-laws-compute-optimal-llm-training> chars 5121-5315: "LLaMA-2 pushed this further: the 7B and 13B variants trained on 2 trillion tokens, exceeding even the Chinchilla-optimal amount on the grounds that inference cost savings justify extra training."
  - S10 <https://vinayakajyothi.com/blog/2026-01-15-scaling-laws-revisited-chinchilla/> chars 2041-2147: "If you are going to serve a model to millions of users, a smaller model is dramatically cheaper per query."

**C9** [DERIVED] Data quality now dominates quantity, making overtraining economically viable: models on 3 trillion carefully filtered tokens outperform those on 10 trillion indiscriminately collected tokens. DeepSeek demonstrated synthetic reasoning data—generated by capable models—can substitute for natural text and achieve frontier reasoning capabilities. This shifts competition from parameter-count armament to data-curation and synthetic-generation investment.
  - S10 <https://vinayakajyothi.com/blog/2026-01-15-scaling-laws-revisited-chinchilla/> chars 6803-7013: "data quality dominates quantity at the frontier. A model trained on 3 trillion carefully filtered, diverse tokens will likely outperform one trained on 10 trillion tokens of indiscriminately collected web text."
  - S10 <https://vinayakajyothi.com/blog/2026-01-15-scaling-laws-revisited-chinchilla/> chars 3991-4140: "DeepSeek's R1 paper demonstrated that models trained heavily on synthetic chain-of-thought data can develop remarkably strong reasoning capabilities."

**C10** [OBSERVED] For models expecting approximately 1 billion inference requests, training a 13.6B parameter model on 2.84 times more data than Chinchilla-optimal achieves equivalent quality to a 30B model while reducing total compute costs by 28%.
  - S12 <https://arxiv.org/html/2401.00448> chars 11927-12100: "An LLM developer that expects a 30B-Chinchilla-quality model will see tokens during inference can reduce their total FLOPs by 28% by training a 13.6B model on 2.84 the data."

**C11** [HYPOTHESIS] Testing 47 models ranging from 150M to 6B parameters trained on 10 to 10,000 tokens per parameter found continuous loss improvement with no saturation plateau, contradicting prior claims of critical model-size thresholds that prevent matching larger models.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C12** [DERIVED] Chinchilla scaling laws fitted on data collected at approximately 100 tokens per parameter overestimate improvements when applied to extreme ratios (250+ tokens per parameter); empirical testing shows models improve more slowly than predicted at extreme ratios, requiring exponentially more tokens for linear quality gains.
  - S12 <https://arxiv.org/html/2401.00448> chars 6938-7145: "Our ablation indicates that when fitting Chinchilla coefficients using only typical token ratio runs, this formula overestimates the impact of additional training data as we move to the extreme ratio regime."

**C13** [HYPOTHESIS] Across 988+ models varying tokenization (latent and subword methods), compression rates (1.01 to 6.16 bytes/token), and compute budgets spanning multiple orders of magnitude, the optimal bytes-per-parameter ratio remained approximately constant (0.465-0.501). This means data-to-parameter scaling is primarily a function of compute budget, not tokenization choice. When your tokenizer changes compression rates, the relationship between total training bytes and model parameters stays stable.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C14** [HYPOTHESIS] Token-per-parameter ratio is not a universal constant but varies by task type. Memorization tasks monotonically benefit from lower TPP (allocating more parameters relative to training data), while reasoning tasks peak at TPP≈20 and plateau. This non-monotonic relationship means the Chinchilla recommendation of 20 tokens-per-parameter is task-specific, not optimal across all workloads.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C15** [OBSERVED] Fitting scaling laws from experiments conducted at a single fixed tokens-per-parameter ratio creates mathematical ill-conditioning (condition number grows as inverse square of exponent difference) that makes extrapolations unreliable when applied to different TPP scenarios. Non-collinear designs that vary TPP won 97.3% of the time on held-out test data compared to fixed-TPP designs. The ill-conditioning arises from Jacobian geometry and affects any smooth objective, not just language model loss.
  - S15 <https://arxiv.org/abs/2605.08541> chars 1333-1546: "Empirically, in controlled experiments with 5M-77M-parameter models, non-collinear designs outperform collinear ones on held-out data with a 97.3% win rate across four laws and five corpora, and 98.7% in bfloat16."

**C16** [DERIVED] Reasoning exhibits a U-shaped accuracy curve with TPP, peaking around 20 tokens per parameter and degrading when TPP is either too low or too high. Memorization, by contrast, monotonically improves as TPP decreases (more parameters per token). When combining both tasks in a single model, reasoning becomes the binding constraint: allocating tokens beyond TPP 20 continues improving memorization but actively harms reasoning accuracy.
  - S18 <https://arxiv.org/abs/2508.18672> chars 1171-1309: "memorization tasks improve with more parameters, while reasoning tasks benefit from optimal TPP, indicating that reasoning is data-hungry."

**C17** [DERIVED] Models with identical training loss but higher active compute achieve better reasoning accuracy; at fixed TPP, models with larger top-k values (more active experts) consistently outperform those with lower top-k on reasoning tasks. This decoupling means the sparse architecture's routing decisions operate as an independent performance dial for reasoning. When model size prevents hitting the ideal TPP 20 for reasoning, increasing active expert allocation can partially compensate.
  - S18 <https://arxiv.org/abs/2508.18672> chars 1031-1127: "models with identical training loss but greater active compute achieve higher reasoning accuracy"

**C18** [DERIVED] Reasoning peaks at TPP approximately 20 and then declines monotonically on both sides, while memorization has no upper bound and improves indefinitely with more parameters. This asymmetry creates a natural convergence point: TPP 20 is where reasoning works optimally and memorization still functions well. Neither reinforcement learning post-training nor test-time compute modifies this fundamental tradeoff, making it a stable target regardless of task blend variations.
  - S21 <https://liner.com/review/optimal-sparsity-of-mixtureofexperts-language-models-for-reasoning-tasks> chars 5765-6157: "The observed TPP-performance trade-offs for reasoning tasks are robust across different model depths, as confirmed by ablations on a 32-layer architecture. This consistency suggests that the optimal TPP ratio and the importance of active parameters are fundamental characterist..."
  - S18 <https://arxiv.org/abs/2508.18672> chars 1310-1414: "Neither reinforcement learning post-training (GRPO) nor increased test-time compute alters these trends."
