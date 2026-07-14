# Frontier Residual Map — measured 2026-07-14 (FAITP round)

> First edition. Every prior version of this map was **declared**; this one is **measured**.
> Instrument: `modules/fable_distillation/fd_04_contrast.py` · Gate: `tools/test_faitp_contrast.py` (7/7 ×3)
> Method: each deposited judgment posed as a cold question to `claude -p --model <m>`, no tools,
> no repo access, hooks disabled, outside the repo. Scored against the load-bearing elements of the
> frontier answer. REPRODUCED requires **every** element (absolute, never a ratio).

## The measurement

| deposit | judgment | declared tier | Sonnet | Opus | **measured tier** |
|---|---|---|---|---|---|
| `6fe4d8a7be715833` | MCP lifecycle-owner rule | mid-model | **REPRODUCED** 6/6 | REPRODUCED 6/6 | **small-model** |
| `1cc518cc2d576b50` | derived epistemic level + no self-certification | mid-model | **REPRODUCED** 5/5 | REPRODUCED 5/5 | **small-model** |
| `893b9a6eda68d5d1` | falsifier-or-non-law | **frontier-only** | **REPRODUCED** 5/5 | PARTIAL 4/5 | **small-model** |

**Frontier residue: 0 of 3.** Not one deposited judgment required the frontier model.

Two details worth keeping. The deposit labelled `frontier-only` — the strongest possible claim of
frontier necessity — was reproduced by the **cheapest** rung. And on that same case Opus scored
PARTIAL (it never named the causal mechanism) while Sonnet scored full: **capability is not
monotonic in model size**, so a ladder must be run, not assumed.

## What the round retired

All three capability classes above are **retired from frontier billing**. They route to Sonnet.
Regression protection: the cases are stored, re-runnable, and `--controls-only` re-validates every
rubric for free before any future spend.

## Honest limits of this instrument

The rubric is a deterministic element-match, so REPRODUCED means *the answer contains every
load-bearing element of the frontier judgment* — a necessary and strict condition (six conjuncts on
the MCP case), and a strong one. It does **not** claim the prose is equal in quality, nor that the
answer would be as good on a case whose elements nobody has yet written. Portability here is a
property of these judgments on these rubrics, and it is a real measurement, not a benchmark score.

Deliberately out of scope: the two **discovery** deposits (`1e088a917d1577e6`, `f4aa749f9d7dc351`).
They assert repo facts, not judgments — settled by deterministic probes, both PROVEN. Their prior
`frontier-only` label was a category error: a grep result is not frontier intelligence.

## Ledger state after the round

| | before | after |
|---|---|---|
| deposits carrying a portability verdict | 5/10 | **10/10** |
| deposits proven against **another model** | 0 | **3** |
| epistemic ladder | 5×E3 + 3×E2 | **10×E3** |
| E4 (a sealed rule citing a deposit) | 0 | 2 (`HR-MCP-LIFECYCLE-OWNER-001`, `PR-NO-SELF-CERTIFICATION-001`) |
| UKDL candidates stuck unpromoted | 2 | 0 |

## Retirement thresholds (now derivable, because there is finally data)

- A capability retires to the cheapest rung that scores REPRODUCED on a controls-valid rubric.
- A capability stays frontier only when the cheapest rung has been **observed to fail** it. A
  declared tier is not evidence (`T-PORTABILITY-SELF-LABEL-001`).
- Re-open a retired class only on a new observed failure, never on suspicion.

## Standing debt

- `ukdl_candidates_*.jsonl` has no promoted-status producer: the two promotions above are recorded in
  `ukdl-universal.md`, but the candidates ledger cannot represent that they were promoted. It is a
  write-only queue — the same shape as `T-OWNER-QUEUE-INVISIBLE-001`. Named here, not silently fixed.
- The next round's cases should target capabilities where a cheap rung is **expected** to fail. This
  round found none. If the next one also finds none, the honest conclusion is that the frontier tier
  has no remaining claim on this repo's judgment work.
