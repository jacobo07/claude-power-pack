---
plan: PLAN-KSR-EPOCH-REHYDRATION (vault/plans/ksr-epoch-rehydration-2026-10-03.md, commit 61698b13)
tasks: T1, T2
date: 2026-10-03
status: EXPERIMENTAL -- slice magnitude premise FALSIFIED before any generator code; T8 pre-registered INCONCLUSIVE
---

# KSR boot rehydration -- archaeology result (T1/T2)

## Verdict

The slice was selected because "epoch rehydration" looked like ~10% of weighted KSR spend with no
owner (plan s1, rank 3). Measured here, the part a generated continuation view could replace --
the hand-kept boot docs -- is **16.4% of boot-window tool output, read by 23 of 73 sessions**. The
remaining 83.6% is task-specific reading spread over many locations. The view's addressable lever
is therefore roughly **1.5-2.5% of weighted spend (ESTIMATE: 16.4% x ~10%, upper bound ~3%)**, not
~10%. Separately, the pre-registered replay eligibility yields **N = 1**, so T8 is INCONCLUSIVE by
the rule written before the first run. No KSR file, goal event or memory row was written.

Recommendation to the Owner: do not proceed to C2 (KSR generator) on this evidence alone. See s6.

## 1. Method (scratchpad tooling, copied here for reproducibility)

- `scripts/boot_facts.py` -- pre-registered rules in its header (boot window, boot-doc set,
  eligibility, sample, regime, fact, consumed, controls). Run 2026-10-03.
- `scripts/boot_share.py` -- boot-doc share of boot-window output; instrument validity at n=22.
- Inline breakdown by tool and location (command in s4).
- Corpus: `~/.claude/projects/C--Users-User-Desktop-Cursor-Projects-Wii-Projects-KobiiSports-Resort-CursorProjects/*.jsonl`
  (main sessions only; mega-session 489739e3 excluded by pre-registration).
- Output `boot_facts_out.json` sha256 `55b137cdc198af0dbda7840b6f7e98879292718e42ff74f9664d830dca5a2e14`
  (not copied: it holds raw identifiers from Owner messages; reproducible from the script).

## 2. Controls

| Control | Expected | Observed |
|---|---|---|
| A/A rerun | identical sha256 | identical (`55b137cd...`) |
| Planted fact in boot read + later use | consumed | consumed |
| Planted fact in boot read only | not consumed | not consumed |
| Self vs cross-session consumption (n=22 boot-doc sessions) | self >> cross | 0.172 vs 0.055 (3.1x) -- instrument discriminates |
| Shuffle at n=1 (the pre-registered sample) | -- | degenerate (compares a session with itself); not used as evidence |

## 3. Eligibility (pre-registered rule, unchanged after first run)

| Reason | Sessions |
|---|---|
| no boot-doc read before first Edit/Write | 50 |
| boot doc changed after it was read (RESUMPTION_PAGE2 8, RESUMPTION_FILE 4, SESSION_STATE 4, INTOCABLES 2, LESSONS 2, ROADMAP 1) | 21 |
| excluded (489739e3) | 1 |
| **eligible** | **1** (04b41ed7, 2026-09-24, PRE_STOP, first doc RESUMPTION_FILE) |

Consequence (pre-registered): eligible N < 6 -> T8 INCONCLUSIVE. Historical replay against the
bytes each session actually read is impossible for SESSION_STATE, INTOCABLES and LESSONS: they live
in auto-memory, outside git.

The one eligible session consumed 18 boot-window facts: 13 from Owner messages, 2 from git log,
3 from RESUMPTION_FILE. Even there, the doc supplied a minority of what was used.

## 4. Where boot-window reading actually goes (73 sessions, chars of tool output before first edit)

| Source | Share | Sessions |
|---|---|---|
| Read: unclassified locations | 25.4% | 58 |
| PowerShell output | 24.0% | -- |
| Read: hand-kept boot docs (this slice's target) | 16.4% | 23 |
| Read: `.ksr_vault/evidence` | 9.2% | 26 |
| Grep | 5.7% | -- |
| Read: caddie C++ source | 4.4% | 15 |
| Read: `.ksr_vault/frontier` | 4.1% | 7 |
| Read: `.ksr_vault` other | 3.8% | 18 |
| Read: `.planning` (non-boot) | 2.6% | 10 |

Median boot window: with boot docs 20 turns / +80.7k ctx; without 14.5 turns / +51.5k ctx
(confounded by task; not a causal effect of the docs).

## 5. Corrections to earlier claims

- E10 ("median 17 turns, +63k ctx of rehydration per session") measured the whole pre-first-edit
  window, not rehydration from hand-kept state. Attributing it to the boot docs was wrong; the docs
  are 16.4% of it.
- Plan s1 rank 3 lever "~10%" is withdrawn; replaced by "~1.5-2.5% (ESTIMATE), upper bound ~3%".
- Earlier finding stands: within-session rereads of unchanged files are negligible (18 events).

## 6. Decision options (Owner)

| Option | What | Lever | Cost | Note |
|---|---|---|---|---|
| A | Continue the slice as planned (C2-C5) | ~1.5-2.5% | generator + tests + goal reconciliation + 3 real boots | T8 cannot pass under the frozen rule; ceiling EXPERIMENTAL unless the rule is re-registered prospectively |
| B | Stop the slice; keep the reconciled-state idea only for the Owner STOP fact (no boot doc carries it) | small, safety-relevant | one doc pointer | cheapest correct fix for the missing-STOP finding |
| C | One more archaeology pass on the 25.4% unclassified reads + 24% PowerShell output to find a concentrated owner-less target | unknown | scratchpad only | only option that could find a lever comparable to ranks 1-2 |
| D | Return to ranks 1-2 (prefix floor, growth rent) | ~13% / 5-10% | owned by peer panes | coordination, not a build |

Promotion state: **EXPERIMENTAL**. Nothing reached CANDIDATE.

## 7. UKDL candidates (not promoted)

- TRAP candidate: attributing a whole pre-first-edit window to "rehydration" before splitting it by
  source. The window mixed hand-kept state (16%) with task reading (84%); the lever was inflated ~5x.
- PROCESS candidate: measure the addressable share of a bottleneck BEFORE selecting the slice that
  attacks it; the pre-registration + controls cost minutes and saved a generator, a goal migration and
  three Owner-started sessions.
