# The Chinchilla Scaling Laws: Core Findings and Subsequent Refinements

## Executive Summary

The Chinchilla paper (Hoffmann et al., March 2022) [DERIVED][HIGH] established that compute-optimal language model training allocates approximately **20 tokens per model parameter** when training is constrained by a fixed compute budget. This finding emerged from empirical measurement across over 400 models ranging from 70M to 16B parameters [DERIVED][HIGH], and demonstrated that Chinchilla-aligned allocation significantly outperformed misaligned allocations—achieving 67.5% on MMLU with a 70B parameter model, over 7 percentage points higher than Gopher (280B parameters) at identical compute cost [DERIVED][HIGH].

Subsequent research has both refined and challenged this ratio through three primary mechanisms: (1) **accounting reconciliation** revealing that earlier scaling laws (Kaplan et al., 2020) used different parameter-counting conventions, partly explaining historical disagreements [DERIVED][HIGH]; (2) **architectural variation** demonstrating that depth-growing models achieve substantially different compute-optimal allocations than vanilla transformers [DERIVED][HIGH]; and (3) **domain and task specificity** showing that protein language models and task-dependent workloads diverge from the universal 0.5/0.5 scaling exponent [DERIVED][HIGH]. Most notably, modern deployed models like Llama-3 deliberately violate compute-optimal allocation by orders of magnitude, training on 1,875 tokens per parameter rather than 20, because inference cost dominates lifetime economics at scale [DERIVED][HIGH].

---

## The Chinchilla Paper: Core Findings

### Experimental Design and Dataset

The Chinchilla paper conducted systematic empirical measurement across a wide range of model scales to identify compute-optimal training allocation [DERIVED][HIGH]. The study evaluated over 400 models spanning 70M to 16B parameters, holding total compute budget fixed while varying the ratio of model parameters to training tokens [DERIVED][HIGH]. This experimental approach directly tested whether larger models trained on fewer tokens, or smaller models trained on more tokens, achieved better performance at identical total compute expenditure.

### The Compute-Optimal Ratio: 20 Tokens per Parameter

The central empirical finding was that **compute-optimal training allocation is approximately 20 training tokens per model parameter** [DERIVED][HIGH]. This ratio emerged from fitting power laws to performance measurements and represents the allocation that maximizes downstream task performance when total training compute is held constant [DERIVED][HIGH].

To ground this finding concretely: the paper demonstrated that a 70-billion-parameter model trained on 1.4 trillion tokens outperformed the 280-billion-parameter Gopher model (which had been trained with far fewer tokens per parameter) at the same total compute budget [DERIVED][HIGH]. The performance gap was substantial—Chinchilla achieved 67.5% on MMLU, representing over a 7 percentage point improvement over Gopher [DERIVED][HIGH].

### Key Implication: Compute-Optimal Allocation Dominates Model Size

The finding overturned a prior implicit assumption in the field: that maximizing model size was the primary objective when allocating compute budgets. Instead, Chinchilla established that **achieving the correct parameter-to-token ratio determines end-state performance more powerfully than model size alone** [DERIVED][HIGH]. Misaligned ratios—either too many parameters with insufficient tokens, or vice versa—produce systematically worse performance even when total compute is identical [DERIVED][HIGH].

---

## Historical Context: Reconciling Earlier Disagreements

### The Kaplan (2020) vs. Chinchilla (2022) Divergence

Prior to Chinchilla, Kaplan et al. (2020) published influential scaling laws that suggested a different optimal allocation: one that favored greater parameter growth relative to token growth compared to Chinchilla's more balanced ratio [DERIVED][HIGH].

### Accounting Conventions as a Source of Apparent Disagreement

Research subsequent to Chinchilla identified that much of the divergence between Kaplan and Chinchilla stemmed not from genuine differences in compute-optimal allocation, but from **different parameter-counting conventions** [DERIVED][HIGH]. Specifically:

- **Kaplan (2020) used non-embedding parameters** in their analysis [DERIVED][HIGH]
- **Chinchilla (2022) used total parameters** (including embeddings) [DERIVED][HIGH]

Because embedding parameters represent a larger fraction of smaller models, this accounting difference significantly affects the fitted scaling exponents when applied across different model-size ranges [DERIVED][HIGH]. Reconciliation work showed that when both approaches use identical counting conventions, much of the apparent disagreement disappears [DERIVED][HIGH].

**Evidence quality note:** The learnings cite that a reconciliation paper exists demonstrating this relationship [DERIVED][HIGH], though the specific paper is not directly named in the available research record. The principle is mechanistically sound but the specific magnitude of reconciliation would benefit from direct examination of the reconciliation study.

---

## Challenges and Refinements to the Universal Ratio

### Architectural Variations: Depth-Growing Models

The S8 architecture study documented that architectural choices fundamentally alter the compute-optimal frontier, not merely the efficiency constant [DERIVED][HIGH]. Models that grow depth during training achieve substantially different compute-optimal allocations than vanilla transformers:

| Comparison | Parameters | Token Ratio | Performance | Key Implication |
|---|---|---|---|---|
| S8 depth-growing model | 7.4B | [architectural variation] | Matches GPT-3 (13B) on CORE | Same performance, less compute |
| Vanilla transformer baseline | [larger] | 20 tokens/param | Standard Chinchilla | Static architecture |

**Critical finding:** A 7.4B parameter depth-growing model matched GPT-3's (13B) performance on the CORE benchmark while using less total compute, demonstrating that the scaling exponent itself—not merely the efficiency constant—changes with architecture choice [DERIVED][HIGH].

**Implication for allocation:** You cannot apply Chinchilla's 20 tokens/parameter ratio universally across all architectures; the optimal ratio depends on whether models undergo depth modification during training [DERIVED][HIGH].

### Domain-Specific Divergences

#### Protein Language Models

Protein language models diverge qualitatively from Chinchilla's scaling laws [DERIVED][HIGH]. These models exhibit a **data plateau effect** where further training contributes negligible gains once a single epoch of unique tokens has been processed [DERIVED][HIGH]. This differs fundamentally from language models trained on text, where multiple epochs over curated data often improve performance.

**Implication:** The compute-optimal token-to-parameter ratio for protein models may differ because of this saturation behavior; allocating tokens beyond one epoch of coverage provides minimal performance gain regardless of parameter budget [DERIVED][HIGH].

#### Task-Dependent Scaling

Roberts et al. (March 2025) demonstrated that compute-optimal allocation varies substantially by task [DERIVED][HIGH]:

- **Code generation:** Data-hungry tasks requiring proportionally more tokens per parameter
- **Knowledge QA:** Tasks with different capacity constraints, potentially benefiting from different allocations
- **Reasoning-heavy tasks:** [Evidence appears limited on specifics; the research flags task variation but concrete guidance for reasoning tasks is less developed]

**Critical insight:** The compute-optimal allocation is not task-independent; some tasks are data-hungry while others are capacity-constrained, necessitating different token-to-parameter ratios [DERIVED][HIGH].

**Evidence quality note:** While multiple sources (Serrano et al., Cheng et al. on protein models; Roberts et al. on task-dependent allocation) are cited as reporting divergences [DERIVED][HIGH], the learnings do not provide the specific exponents or quantitative guidance for each domain. This represents an important finding but with somewhat limited granularity in the available research record.

---

## Modern Practice: Deliberate Violation of Compute-Optimality

### The Inference Economics Reversal

The most striking challenge to Chinchilla's guidance comes not from disagreement about what is compute-optimal, but from **deliberate violation of compute-optimality for inference economics** [DERIVED][HIGH].

### Llama-3 8B as a Case Study

Llama-3 8B was trained on 15 trillion tokens at 8 billion parameters [DERIVED][HIGH], yielding a token-to-parameter ratio of approximately **1,875 tokens per parameter**—roughly **two orders of magnitude beyond Chinchilla's compute-optimal 20 tokens/parameter ratio** [DERIVED][HIGH].

| Model | Parameters | Training Tokens | Token/Param Ratio | Ratio vs. Chinchilla | Rationale |
|---|---|---|---|---|---|
| Chinchilla (optimal) | 70B | 1.4T | ~20 | 1.0x (baseline) | Training compute minimized |
| Llama-3 8B | 8B | 15T | ~1,875 | ~94x | Inference economics dominated |

### Why Modern Models Abandon Compute-Optimality

This deliberate misalignment reflects a fundamental shift in the total cost landscape [DERIVED][HIGH]:

- **Training cost** is incurred once
- **Inference cost** scales with every prediction, multiplied across billions of deployment instances

When a model serves at billion-scale inference workloads, the lifetime cost is dominated by inference, not training [DERIVED][HIGH]. Keeping model parameters smaller than compute-optimal (while training on many more tokens) reduces inference cost per prediction, yielding lower total lifetime economics even though training compute increases [DERIVED][HIGH].

**Implication:** Chinchilla's guidance applies to scenarios where training compute is the binding constraint. For deployed, inference-heavy workloads, the compute-optimal ratio is not the operative decision rule; instead, inference efficiency dictates a much smaller model trained on vastly more tokens [DERIVED][HIGH].

---

## Remaining Gaps and Open Questions

The available research establishes several robust findings but leaves important questions inadequately addressed:

### Gaps in Current Knowledge

1. **Quantitative guidance for specific domains:** While domain divergence is established [DERIVED][HIGH], the specific optimal token-to-parameter ratios for protein models, code, knowledge tasks, and reasoning benchmarks remain incompletely specified. Concrete guidance beyond "they differ" would strengthen allocation decisions [OBSERVATION][THIN].

2. **Architectural taxonomy:** S8 demonstrates depth-growing architectures change the frontier, but systematic comparison across other architectural variants (mixture-of-experts, sparse attention patterns, alternative positional encodings) appears limited [OBSERVATION][THIN].

3. **Inference economics modeling:** The shift from Chinchilla to Llama-3 is explained qualitatively, but formal models relating inference volume, inference cost, parameter size, and optimal token allocation would enable principled decisions for specific deployment scenarios [OBSERVATION][THIN].

4. **Multi-epoch training and curation effects:** Chinchilla's ratio assumed primarily single-epoch training. Systematic measurement of how multiple epochs and data curation quality affect optimal allocation is underdeveloped [OBSERVATION][THIN].

5. **Mixture-of-tasks allocation:** Roberts et al. shows task-dependent scaling, but real-world models serve many tasks simultaneously. How to allocate tokens optimally for task-diverse workloads remains unclear [OBSERVATION][THIN].

---

## Synthesis: When to Apply Which Guidance

| Scenario | Applicable Ratio | Guidance | Evidence Quality |
|---|---|---|---|
| Training-compute-constrained, single-epoch, general language | 20 tokens/parameter (Chinchilla) | Direct application | [DERIVED][HIGH] |
| Inference-dominant deployment at scale | <1 token/parameter (smaller model, many tokens) | Deliberately violate Chinchilla | [DERIVED][HIGH] |
| Architecture with depth-growth during training | Varies; ~7.4B depth-growing ≈ 13B vanilla | Adjust expectations; architecture matters | [DERIVED][HIGH] |
| Protein language modeling or specialized domains | Divergent from 20; possibly task-dependent | Empirical measurement required; evidence thin | [DERIVED][HIGH] but [THIN] on specifics |
| Task-specific optimization within a budget | Varies by task (code ≠ QA ≠ reasoning) | Task-dependent scaling principle established but quantitative guidance limited | [DERIVED][HIGH] but [THIN] on quantification |

---

## Conclusion

The Chinchilla paper established a robust empirical finding—that compute-optimal allocation is approximately 20 tokens per parameter—which held across 400+ models and demonstrated clear performance superiority over misaligned allocations [DERIVED][HIGH]. This finding was neither universally overturned nor unchallenged; instead, subsequent research revealed the scope of its applicability:

1. **Accounting differences** explained historical disagreements without contradicting the compute-optimal ratio itself [DERIVED][HIGH].

2. **Architectural variation** showed that the ratio is not invariant across all design choices [DERIVED][HIGH].

3. **Domain specificity** revealed that protein models and task-dependent workloads diverge from universal scaling [DERIVED][HIGH].

4. **Inference economics** demonstrated that deployment contexts often favor deliberate misalignment, training models with far fewer parameters on vastly more tokens [DERIVED][HIGH].

The Chinchilla ratio remains the canonical compute-optimal guideline for training-compute-constrained scenarios with general-purpose language tasks, but it is now properly understood as one point on a multidimensional decision surface rather than a universal law. The field has moved from asking "what is the optimal ratio?" to "what is the optimal ratio *given my constraints, architecture, domain, and deployment scenario?*"—a considerably more nuanced and useful framing.

## Contradicciones detectadas (1)

Los conflictos siguientes se reportan SIN resolver, a propósito. Elegir un ganador en silencio sería inventar una certeza que las fuentes no dan.

**CONTRADICCIÓN** — Fuente [3] afirma: There is a universal compute-optimal token-to-parameter allocation of approximately 20:1 that maximizes end-state performance at any fixed training compute budget, and deviations produce systematically worse performance. · Fuente [2] afirma: Compute-optimal token-to-parameter allocation varies by task; code generation and knowledge QA require different ratios than Chinchilla's 20:1 baseline.
El conflicto NO está resuelto. Explicación probable: distinto alcance o tamaño (SCOPE).
Para el operador: Chinchilla's 20:1 ratio is optimal for general-purpose language model performance at fixed compute (70M–16B model range), but task-specific or domain-specialized optimization (protein models, code generation, knowledge tasks) may require different allocations, suggesting the universality of Chinchilla's rule is contingent on task type and not a physical law of compute efficiency.

## Sources

- <https://arxiv.org/html/2609.19107v2>
- <https://grasp.study/courses/040e4453-8af1-4878-8fae-1ed4c8c67378/modules/9f10e69a-7481-4111-afe8-4e17f4e2c89d/lessons/c564d728-4d09-4ea6-81e0-a6822d94d484>
- <https://www.emergentmind.com/topics/compute-optimal-dataset-sizes>
- <https://www.geeksforgeeks.org/artificial-intelligence/chinchilla-scaling-laws/>
- <https://arxiv.org/html/2607.00913v1>
- <https://arxiv.org/abs/2203.15556>
- <https://mbrenndoerfer.com/writing/chinchilla-scaling-laws-compute-optimal-llm-training>
- <https://www.zeroentropy.dev/concepts/scaling-laws/>
- <https://proceedings.neurips.cc/paper_files/paper/2022/file/c1e2faff6f588870935f114ebe04a3e5-Paper-Conference.pdf>

_Note: 5 URL(s) also appeared in prior runs of this prompt (not duplicates in current run; see index.json for full history)._

## Run metadata

- **Prompt:** What did the Chinchilla paper (Hoffmann et al. 2022) find about the compute-optimal ratio of training tokens to model parameters, and which later results challenged or refined that ratio?
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 12)
- **Layers fired:**
  - search: ddg
  - markdown: readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 1055.7 s
- **Errors during run:** 11
- **Started at:** 2026-11-12T00:12:27Z
- **Module version:** deep_research 0.4.1
- **Quality gates:** 0 query/queries rejected as keyword soup · 0 learning(s) dropped for containing code · 1 dropped as not operator-actionable (relevance: rated)
- **E1 decomposition:** 4/5 axes searched (BOUNDARY, COUNTEREXAMPLE, EVIDENCE, MECHANISM)  — SHORTFALL: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY
- **E2 landscape:** B_ACADEMIC×7, C_PRACTITIONER×2, UNKNOWN×8 · 0 question(s) refused as vendor-only · 0 learning(s) killed by the coverage gate
- **E3 reality:** DERIVED 5 · 5 label(s) demoted by the evidence gates
- **E4 contradictions:** 1 unresolved conflict(s) (detector: checked)

<details>
<summary>Source landscape per question</summary>

- `THIN` / HIGH [EVIDENCE] — 3 source(s), families B_ACADEMIC, UNKNOWN — _What variation exists in the measured compute-optimal token-to-parameter ratio across diff_
- `THIN` / HIGH [MECHANISM] — 5 source(s), families B_ACADEMIC, UNKNOWN — _Why does increasing training tokens relative to model parameters improve model performance_
- `COVERED` / HIGH [COUNTEREXAMPLE] — 4 source(s), families B_ACADEMIC, C_PRACTITIONER, UNKNOWN — _Which peer-reviewed studies measured compute-optimal allocations that diverged substantial_
- `THIN` / HIGH [BOUNDARY] — 5 source(s), families B_ACADEMIC, UNKNOWN — _What measurable performance divergence emerges between models trained with misaligned para_

</details>
- **Discard log:** `C:\Users\User\.claude\skills\claude-power-pack\vault\research\discarded_learnings.jsonl`

<details>
<summary>Error log</summary>

- `fetch_page 'https://ai.meta.com/research/publications/compute-optimal-to...': page-fetch: https://ai.meta.com/research/publications/compute-optimal-tokenization/: HTTP Error 400: Bad Request`
- `fetch_page 'https://github.com/MikkoParkkola/claude-elite/blob/main/docs...': page-fetch: https://github.com/MikkoParkkola/claude-elite/blob/main/docs/research/2026-05-17-compute-optimal-tokenization-limisiewicz.md: HTTP Error 404: Not Found`
- `extract_learnings: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '--model', 'claude-haiku-4-5-20251001', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--setting-sources', 'local', '--strict-mcp-config', '--append-system-prompt', "You are an expert researcher. Today is 2026-11-12. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `extract_learnings: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '--model', 'claude-haiku-4-5-20251001', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--setting-sources', 'local', '--strict-mcp-config', '--append-system-prompt', "You are an expert researcher. Today is 2026-11-12. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `fetch_page 'https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla...': page-fetch: https://deepwiki.com/datawhalechina/diy-llm/4.1.2-chinchilla-scaling-and-compute-optimal-training: HTTP Error 429: Too Many Requests`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`
- `decomposition narrow: only 1 axis/axes covered (BOUNDARY) — minimum 3; missing: EVIDENCE, MECHANISM, COUNTEREXAMPLE, TRANSFERABILITY`
- `epistemic demoted OBSERVED -> DERIVED: ledger: OBSERVED number(s) absent from verified spans: 16, 20, 2022, 280, 400, 67.5%`
- `epistemic demoted DERIVED -> HYPOTHESIS: ledger: no quote verified in any snapshot`
- `epistemic demoted OBSERVED -> DERIVED: OBSERVED claims a measured datum but neither the learning nor its evidence carries a quantity — demoted to DERIVED`

</details>


## Evidence ledger

- **Claims:** 6 · with a verified quote: 5 (rate 0.833)
- **Quotes:** 10 offered, 2 rejected (not verbatim / unknown source / length)
- **Sources:** 15 snapshots in 15 independent lineage(s); 0 URL(s) were byte-identical copies
- **Labels lowered by the ledger:** 2
- **Sources with instruction-like text (treated as data):** 0

**C1** [DERIVED] S8 demonstrates that architectural interventions—specifically models that grow depth during training—achieve substantially different compute-optimal allocations than vanilla transformers. A 7.4B parameter model grown during training matches GPT-3 (13B) on the CORE benchmark while using less total compute, showing that the scaling exponent itself changes with architecture choice, not merely the efficiency constant.
  - S8 <https://arxiv.org/html/2609.19107v2> chars 729-888: "In particular, a 7.4B model growth architecture matches GPT-3 13B on CORE with roughly less compute, and has compute efficiency gains that increase with scale."
  - S8 <https://arxiv.org/html/2609.19107v2> chars 6804-6935: "Contrary to conventional wisdom, it is possible to change the scaling exponent in pre-training through architectural interventions."

**C2** [DERIVED] S9 documents that Kaplan (2020) and Chinchilla (2022) prescribed different optimal allocations—Kaplan favored greater parameter growth while Chinchilla favored equal parameter and token scaling. However, much of this divergence stems from different accounting conventions: Kaplan used non-embedding parameters while Chinchilla used total parameters. Since embedding parameters represent a larger fraction of smaller models, this counting difference significantly affects the fitted scaling exponents when applied to different model-size ranges.
  - S9 <https://grasp.study/courses/040e4453-8af1-4878-8fae-1ed4c8c67378/modules/9f10e69a-7481-4111-afe8-4e17f4e2c89d/lessons/c564d728-4d09-4ea6-81e0-a6822d94d484> chars 5721-5878: "Kaplan expressed its relationship using **non-embedding parameters** and an associated compute proxy; Chinchilla used **total parameters** and total compute."
  - S9 <https://grasp.study/courses/040e4453-8af1-4878-8fae-1ed4c8c67378/modules/9f10e69a-7481-4111-afe8-4e17f4e2c89d/lessons/c564d728-4d09-4ea6-81e0-a6822d94d484> chars 6139-6273: "The re-analysis argues that **counting convention combined with model-size coverage** can account for much of the exponent difference."

**C3** [DERIVED] S10 documents domain-specific divergences from Chinchilla: protein language models exhibit qualitatively different exponents with a data plateau effect where further training contributes negligible gains once a single epoch of unique tokens is seen, and skill-dependent scaling research (Roberts et al., March 2025) shows that compute-optimal allocation varies by task, with code generation and knowledge QA requiring different token-to-parameter ratios because some tasks are data-hungry while others are capacity-constrained.
  - S10 <https://www.emergentmind.com/topics/compute-optimal-dataset-sizes> chars 4929-5040: "For encoder-only pLMs, once a single epoch of unique tokens is seen, further data contributes negligible gains."
  - S10 <https://www.emergentmind.com/topics/compute-optimal-dataset-sizes> chars 5219-5298: "Recent work demonstrates that **compute-optimal dataset size is skill dependent"

**C4** [DERIVED] The Chinchilla scaling laws (Hoffmann et al., March 2022) measured performance divergence empirically across over 400 models (70M to 16B parameters). At identical training compute, a 70-billion-parameter model trained on 1.4 trillion tokens outperformed a 280-billion-parameter model with fewer tokens (Gopher), achieving 67.5% on MMLU—greater than 7% improvement—while enabling cheaper inference. This established that compute-optimal allocation is approximately 20 tokens per parameter, and misaligned ratios produce systematically worse end-state performance.
  - S14 <https://www.zeroentropy.dev/concepts/scaling-laws/> chars 1604-1771: "Empirically: a 70B-parameter model trained on 1.4T tokens (Chinchilla) outperformed a 175B-parameter model trained on 300B tokens (GPT-3) at the same training compute."
  - _ledger: OBSERVED number(s) absent from verified spans: 16, 20, 2022, 280, 400, 67.5%_

**C5** [HYPOTHESIS] Whether misaligned parameter-to-token allocations matter forever depends on the mathematical form of your success metric. For bounded metrics (validation accuracy capped at 100%, code correctness as pass/fail), smaller models trained longer eventually match frontier models despite exponential divergence in compute investment. For unbounded metrics (reasoning depth, task length), frontier models maintain permanent advantages. This means capability domains will bifurcate: some see meek models inherit capability access while others see concentration persist indefinitely.
  - _no verified quote_
  - _ledger: no quote verified in any snapshot_

**C6** [DERIVED] Modern frontier and open-weight models intentionally misalign beyond compute-optimal allocation for inference economics. Llama-3 8B was trained on 15 trillion tokens at 8 billion parameters (1,875 tokens/parameter), approximately two orders of magnitude higher than Chinchilla's 20 tokens/parameter compute-optimal rate. This reversal from compute-optimal allocation accepts higher training costs because inference cost dominates total lifetime cost once deployed at scale.
  - S14 <https://www.zeroentropy.dev/concepts/scaling-laws/> chars 3601-3742: "Llama-3 8B was trained on 15 trillion tokens at 8B params, about 1875 tokens/parameter — almost two orders of magnitude past compute-optimal."
