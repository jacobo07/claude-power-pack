---
covers: [two-builders, m2-phases-5-14, n1-n4, christmas-2026-deadline]
status: PROPOSED 2026-10-17 (Owner "y" to estimate N1-N4 and date the plan; dates and numbers below are NOT approved budgets)
owner_surface: chat (this file is the backup)
---

# Two Builders: whole mod by 25 Dec 2026 (estimate + dated checkpoints)

Target (Owner 2026-10-17): the WHOLE mod on 25 Dec, i.e. M2 phases 5-14 plus N1-N4 of `.planning/ROADMAP.md` in the TB repo.
Today is 2026-10-17, so 69 days remain.

## Inputs, with their source
- Measured: worker probes P25-P31b cost 26.9M processed over 8 runs = **3.4M mean** (range 1.5-5.5M). Source: STATE.md of the
  experiment-admission workstream, W1 corpus. P31c-P38 coordinator cost is UNMEASURED (laptop transcripts).
- Measured: the admission mission burned ~55M in ~4.3 h = ~12M/h, with one long Opus pane as the main cost. Throughput of a
  small-context Sonnet worker is NOT measured.
- Measured: M2 phases 5-14 reforecast (E6, from P25): P50 50M, P80 72M, P95 116M.
- Derived here (the estimate): N1-N4 = (assumed number of probes) x 3.4M. The probe counts are my assumption. **Confidence LOW.**

## N1-N4 estimate (derived, not measured)
| Item | Assumed probes | P50 (M) | P80 (M) | Depends on | Notes |
|---|---|---|---|---|---|
| N1 co-op slice (Naboo) | 4 (roster, player-2 input, co-op interaction, full timeline) | 14 | 24 | phases 3-4 (done) | can start NOW; player 2 input on GEX44 is unproven |
| N2 five levels | 5 levels x ~1.5 | 25 | 40 | phase 5 | what a text re-theme cannot change is listed, not faked |
| N3 custom systems | 3 (Creature Companion + declare the rest) | 10 | 18 | phase 5 | each system: implemented through data or recorded as needing DOL work |
| N4 package + hand over | 3 + docs | 10 | 18 | phases 5-7 | the DOL->ISO->WBFS wrap is UNPROVEN in this project |
| **N1-N4** | | **~59** | **~100** | | |
| M2 5-14 (E6) | | 50 | 72 | | |
| **Whole mod** | | **~109** | **~172** | | |

At ~12M/h that is ~9 h (P50) to ~14 h (P80) of worker time. The binding constraints are NOT compute:
1. Dolphin slots are serial (`/run/kobii/audit.lock` on GEX44); only offline work (phase 7, tooling, docs) runs in parallel.
2. Phase 5 (creature spawn in the hub) is unresolved after P36-P39; phases 12 and N3's Creature Companion probably need the same contract.
3. The weekly quota of the GEX44 account is UNMEASURED; the previous account hit its weekly limit on 2026-10-17.
4. The "1:1" judgement of hair and kitten is the Owner's, on full-resolution frames (a model reading is a candidate).
5. No real-Wii proof exists for this project; the proven path is the rebuilt disc booting in Dolphin on GEX44.

## Dated checkpoints (proposed; a missed checkpoint cuts scope, it does not slide the date)
| Date | Must be true | If it fails |
|---|---|---|
| 24 Oct | Experiment Admission closed; this table recomputed from measured P25-P39; M2 re-armed; N1 and phase 7 started in parallel | Owner decides the tranche |
| 15 Nov | Phase 5 resolved (a creature appears in-level) AND N1 verified (two characters seen moving, one co-op interaction) | choose: move the spawn to another level, or drop the kitten from the gift |
| 1 Dec | Phases 7-8 done (writer proven in play), N2 five levels boot with frames | ship Madzia with her hair and no kitten; N2 shrinks to the levels that boot |
| 15 Dec | Hair, kitten and Kitten Call judged by the Owner; WBFS builds in one command and boots on GEX44 | freeze scope; ship what is green |
| 20 Dec | Final disc + `PLAY_GUIDE.md` + `STATUS_FOR_OWNER.md`; real-Wii attempt if the Owner has the console | ship the Dolphin-proven build and say so |
| 25 Dec | Delivery | |

Floor ("minimum safe"): a WBFS that boots with Jacobo and Madzia playable in co-op (N1) plus Madzia's hair and the guide.
Stretch: N2 five levels, kitten and Kitten Call. N3 is declared, not promised.

## Rules that stay in force
Jacobo and Madzia are NEW added characters, never a rename or replacement. Every slot runs through the experiment-admission gate
(`prereg_lint --disc` receipt, `tb_local`). Workers are headless Sonnet with a watchdog, never an Opus pane.
Visual target: `docs/OWNER_TARGET_MADZIA_KITTEN_CALL.png` in the TB repo.

## Open questions for the Owner
1. Is a real Wii part of the 25 Dec delivery, or is a disc that runs in Dolphin enough?
2. Approve a budget for 24 Oct to 15 Nov only (P50 ~35M for phase 5 + N1 + phase 7), then re-forecast at the checkpoint?
