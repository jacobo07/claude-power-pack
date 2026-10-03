---
plan: PLAN-KSR-EPOCH-REHYDRATION s12 (B + C), Owner-approved 2026-10-03
instrumentation: scripts/ctx_admission.py, scripts/ctx_dead.py, scripts/ctx_manifest.json (commit 99d76964, frozen before measurement)
result_sha256: 117d042cf17a0702b6aad50c9b67eab964ad58aaede3c6f09d88f36ca10d9471 (ctx_dead_out.json)
decision: TOOL-I/O FIREWALL NOT EARNED; LIFETIME (dead carriage) is the material horizontal lever -> OWNER_EXISTS_ELSEWHERE
status: EXPERIMENTAL (findings); nothing built
---

# KSR context admission -- what produced the context, what lived too long

## 0. B (state correctness) -- done

KSR commit `9dcb68a`: `.planning/STATE.md` heading parenthetical "(active)" -> "(current milestone — work HALTED by
Owner STOP 2026-10-01; resume only on Owner instruction: .ksr_vault/frontier/BACKLOG_OWNER_STOP_20261001.md)".
Authority: `BACKLOG_OWNER_STOP_20261001.md` (commit 14f7840). One line (+1/-1); built in the index from HEAD's blob;
parent = pre-read HEAD; pre-commit hook passed (no --no-verify); the foreign uncommitted GSD edits in the same
file kept the same `git patch-id --stable` (e4f2821c) before and after; EOL i/lf w/lf; re-read of the real file
shows no bare "(active)". Not touched: RESUMPTION_FILE / VIS surfaces, MEMORY / SESSION_STATE, ROADMAP, goal store.

## 1. Denominators (never mixed)

| Name | Value | Population |
|---|---|---|
| D-corpus | 758.8M weighted | all 129 files incl. subagents + srclink (first audit) |
| D-stage1 | 701.4M | 73 main files, deduped calls incl. sidechain lines |
| **D-decision** | **616.0M** | 73 main files, calls = distinct message.id, non-sidechain, non-synthetic |
| D-decision excl. 489739e3 | 513.7M | same, without the mega-session |

Every share below is against D-decision (or its excl. variant), priced per call from that call's usage
(read share x0.1). The write-priced part of carriage is reported separately as overlap with rank 4
(idle/expiry rewrite, peer-owned) and excluded from the decision.

## 2. Instrument validity

| Control | Result |
|---|---|
| Classifier self-test (real paths, both separators, near-miss `memoryx`) | 16/16 |
| T2 classifier bug | `cls()` raw strings like `r"\memory\\"` (two backslashes) never matched -> inflated "unclassified". Fixed, regression cases added. |
| Planted probe, later used | detected USED |
| Planted probe, never used | NOT_OBSERVED |
| Self vs cross-session use of distinctive probes | read 0.407 vs 0.015 (27.6x); tool 0.206 vs 0.006 (35.5x); PowerShell 0.422 vs 0.001 (294x); bash 0.418 vs 0 -- all valid (>= 2x) |
| Token calibration (estimated resident tool-output tokens / actual context tokens) | 0.128 -- tool output is ~13% of what the model carries; the rest is prefix, model text and harness attachments |
| Determinism | stage 1 sha256 cf126c13 reproduced; manifest frozen by size+sha256, reads capped at frozen size |

Limits stated, not hidden: observable use is an external proxy (a distinctive token or line echoed later);
model attention is not observable. NOT_OBSERVED is a LOWER bound on use, so dead carriage is an UPPER bound
on waste. Items with < 3 distinctive probes are UNMEASURED (2.89% of D-decision), never counted as dead.

## 3. Whole-corpus result (decision input)

| Tool-output measure | All | Excl. 489739e3 |
|---|---|---|
| Carriage (resident after admission) | 9.88% | 9.31% |
| **Dead carriage after last observable use (upper bound)** | **<= 6.34%** | **<= 5.83%** |
| Unmeasured (< 3 probes) | 2.89% | 2.90% |
| Replaceable at admission (>= 8k tok, <= 10% probes used) | 0.56% | 0.58% |
| Identical repeats (same input, same sha256, no compaction between) | 0.00% | 0.00% |

Largest single classes by carriage (all): KSR tools reads 1.20%, Grep 0.95%, boot docs 0.61%, file-content-via-shell
0.60%, harness-temp reads 0.59%, caddie C++ 0.58%, python scripts 0.55%, git status/log 0.49%. No class reaches 1.3%.
Every class shows the same shape: most of its carriage happens after the last observable use.

## 4. Answers to the plan's questions

- **Unknown 25%:** mostly an instrument artefact. After the classifier fix, `read:unclassified` is 0.17% of D-stage1
  carriage. The rest was auto-memory, `tools\`, `~/.claude` and harness-temp reads hidden by the raw-string bug.
- **PowerShell 24%:** a share of pre-first-edit TOOL OUTPUT only. Against D-decision the whole PowerShell family
  carries ~2.6% (stage 1) and no command class exceeds 0.7%. Heavy hitters: file-content-via-shell, python
  scripts, git status/log, ssh. Not concentrated.
- **Admission vs lifetime:** lifetime. Admission-replaceable 0.56% vs dead carriage <= 6.34% (> 10x).
- **Rereads / repeated cognition:** identical repeats 0.00%; within-session unchanged rereads were already
  negligible (T1). No derived-fact or negative-cache candidate with direct evidence in this pass.
- **Turn amplification:** not measured (no advancement labels exist); instrumentation gap recorded.
- **Model-produced context:** assistant tool inputs (Write/Edit bodies) carry ~6.2% of D-stage1 -- larger than all
  PowerShell. A lifetime question too (a written file body stays resident after the write lands).

## 5. Decision (pre-registered rule applied unchanged)

| Candidate | Rule | Verdict |
|---|---|---|
| Tool-I/O firewall (digest/pointer) for any class | class dead/immediate carriage >= 3% and unowned | **NOT EARNED** (max class < 1%; replaceable 0.56%) |
| Semantic GC / lifetime of tool output | dead >= 2x admission-replaceable | **MATERIAL, HORIZONTAL** (<= 5.8-6.3%, upper bound) |
| Ownership of the lifetime lever | -- | **OWNER_EXISTS_ELSEWHERE**: the harness cannot evict single tool results; residency ends only at compaction or a fresh epoch, which belong to the rollover / context-rent / CO-06 (`cognitive_os/gc.py`) owners. This result is part of plan rank 2 (growth rent 5-10%), not additive to it. |

Handoff to the lifetime owner: "tool output is ~10% of weighted KSR spend in carriage and <= ~6% of it is carried
after its last observable use, across every class; identical repeats are ~0; admission-side replacement is
~0.6%. A semantic boundary (edit cluster / commit) is the natural eviction point. Source: this file."

## 6. Economics after B + C (ranges, not additive)

Already-identified levers (KSR, weighted): resident prefix ~13% (peer), growth rent / lifetime 5-10% (peer; this
pass places tool-output dead carriage at <= ~6% within it), idle-return ~4% (peer), boot docs 1.5-2.5%, tool-output
admission ~0.6%. The 20-30% band stays plausible, but every lever above ~3% is owned by another pane. This pane
found no new unowned lever >= 3%.

## 7. Capital accounting

- OPEX: two read-only analysis passes, two audits by sub-agents, one one-line state fix.
- CAPEX kept: a reusable, validated context-admission instrument (classifier + dead-carriage + controls).
- AVOIDED CAPEX: generated continuation view (T3-T10) and a tool-output firewall -- both built on premises the
  measurements falsified (~10% -> ~2%; ~24% -> < 1% per class).

## 8. UKDL candidates (NOT promoted; doctrine on denominators already exists: NEVER-GATE-ON-A-RATIO, T-REFERENCE-SHRINK-001)

- TRAP: a pre-first-edit share of tool output read as an estate saving ("PowerShell 24%" -> ~2.6% of weighted).
- TRAP: an "unclassified" bucket read as a source class when the classifier itself was broken (raw-string `\\`).
- PROCESS: measure admission AND lifetime before choosing an admission optimization; here lifetime dominated > 10x.

CBR: EXPERIMENTAL for all findings. Nothing ratcheted.
