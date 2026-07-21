# CRAIF Contamination Audit

Run 2026-07-21 against all three sealed datasets, post-sealing (after all expansion passes).

| File | Words | Excluded-vocabulary hits | Markdown bullets | Markdown headers | Code fences | Code-like lines |
|---|---|---|---|---|---|---|
| `craif_00_constitution_v1.txt` | 20,618 | 0 | 0 | 0 | 0 | 0 |
| `craif_01_repair_runtime_v1.txt` | 21,501 | 0 | 0 | 0 | 0 | 0 |
| `craif_02_activation_integrity_v1.txt` | 19,236 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **61,355** | **0** | **0** | **0** | **0** | **0** |

**Excluded-vocabulary terms checked** (per PREFLIGHT anti-contamination mandate): ecommerce,
e-commerce, brandshipping, customer acquisition, revenue system, market mechanic,
conversion funnel, checkout flow, SKU, shopping cart. Zero hits across all three datasets,
checked case-insensitively via regex against the full raw text.

**Structural checks**: no `#`-prefixed markdown header line, no `-`/`*`-prefixed bullet
line, no triple-backtick code fence, and no line matching a common code-statement pattern
(`def `, `function `, `import `, `const `, `class X:`, `<?php`, `SELECT *`) anywhere in any
of the three sealed files — consistent with the family's own fabrication contract (dense
numbered-subsection prose only, zero executable code, zero markdown formatting inside a
dataset).

**Governance artifacts excluded from this check by design**: `CRAIF_INDEX.md`,
`CRAIF_D2A_REINFORCEMENT_PACKAGES.md`, and `CRAIF_ADVERSARIAL_REVIEW.md` are markdown
manifests, not sealed datasets, and are expected to use markdown formatting — the
fabrication contract's no-markdown rule applies only to the three `.txt` datasets
themselves.

**Method note**: this audit re-ran the identical per-dataset checks already performed
inline during each dataset's own sealing (visible in this session's tool history), rather
than introducing a new methodology at Phase 3 — a Phase 3 contamination audit run against a
different check than the one used at authoring time would not be a stronger verification,
only a different one, and this corpus's own evidence discipline (CRAIF-00 Part XV) requires
the reproduction be named rather than merely asserted. Reproduction: the check is a
five-line PowerShell script reading each file raw, regex-matching the excluded-term list
case-insensitively, and regex-matching the four structural patterns — rerunnable by any
future session against the same three file paths.

**Verdict**: PASS. Zero contamination, zero markdown, zero code, across all 61,355 words of
sealed CRAIF content.
