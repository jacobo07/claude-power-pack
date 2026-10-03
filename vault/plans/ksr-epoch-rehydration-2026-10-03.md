---
id: PLAN-KSR-EPOCH-REHYDRATION
date: 2026-10-03
status: HALTED AT OWNER DECISION -- approved 2026-10-03; T1/T2 done (26e5cdf0) and falsified the s1 rank-3 lever (boot docs = 16.4% of boot reads, ~1.5-2.5% weighted, not ~10%); T8 pre-registered INCONCLUSIVE (N=1); C2+ not started. Options A-D: vault/audits/ksr_archaeology/2026-10-03-boot-rehydration.md s6
covers: [ksr-epoch-rehydration, continuation-view, cognitive-archaeology-pilot]
mode: ULTRA-PLAN for this reconciliation only; EXECUTION MODE from the first approved action
promotion_ceiling: CANDIDATE (never BASELINE in this slice)
---

# KSR epoch rehydration — first vertical slice of the "transcript -> state" programme

## 1. Why this slice (evidence, not taste)

Measured read-only on the KSR transcript corpus (126 files, 599.1 MB) on 2026-10-03. Evidence
E1-E14 and scripts: session scratchpad `ksr_evidence.md`; durable copy lands at C1 in
`vault/audits/ksr_archaeology/`. Weights are input-equivalent ESTIMATES (read 0.1, write-1h 2,
output 5); no dollar figures.

| Rank | Bottleneck | Lever (weighted) | Owner | Decision |
|---|---|---|---|---|
| 1 | Resident prefix 90k -> 140-180k (instructions ~55k, agents ~12.5k, skills ~5.9k) | ~13% | PLAN-SKILL-RESIDENCY / R2 / ACV (peer panes) | CITE ONLY |
| 2 | Growth rent: 12.6% of cache reads above 350k | 5-10% net | rollover decider (SHADOW, peer) | CITE ONLY |
| 3 | **Epoch rehydration: median 17 turns, 5 reads, +63k ctx before first edit, x73 sessions** | **~10%** | **none — overlapping hand-kept stores** | **THIS SLICE** |
| 4 | Idle>1h cold rewrite (87 events) | ~4% avoidable | idle-return-rollover proposal (peer) | CITE ONLY |
| 5 | Opus 97.7% of weighted | price-dependent | cost_collapse / provider_routing | LATER |
| - | In-session rereads of unchanged files | ~0 (18 events) | - | FALSIFIED |

Rank 3 is the only measured lever with a present consumer and no active owner. It exercises the
whole loop by EXTENDING `modules/gsd_x/goal/brief.py::compile_brief` (deterministic, refuses rather
than truncates) — no new store, engine, ledger or parser.

## 2. Owner answers (Q&A 2026-10-03), as amended by the phase-4 audit

1. Write to KSR: EXPERIMENTAL, reversible, bounded — generate the view, wire boot to it.
2. Goal Spine is the durable owner. The only KSR goal, `ksr-p2w25-fp028` (5 events, 2026-09-25),
   is a narrow sub-investigation; it is kept intact and referenced (1 established, 2 rejected,
   1 open hypothesis; constraints "static first", "never touch the foreign autopilot.py edit").
   A programme goal `ksr-programme` is declared after reconciliation.
3. GENERATED: RESUMPTION_FILE, RESUMPTION_PAGE2, STATE, operational handoff; SESSION_STATE only
   its KSR section (see T10 — it is cross-programme and outside git). NORMATIVE: INTOCABLES,
   ROADMAP — referenced by path + sha256, never rewritten. RESUMPTION_FILE's pane-scoped sections
   (VIS pane, §§3-8) stay pane-owned.
4. Gates: 100% recall on critical classes (invariants, authority, blockers, open obligations, next
   legal action); >=95% on all consumed facts over the pre-registered replay; 3 real boots <=5 turns
   and <=15k growth to endpoint (T9); 0 missing-context incidents. Any miss = EXPERIMENTAL; a full
   pass earns CANDIDATE at most.
5. Archaeology = experimental scratchpad tooling; durable results in `vault/`. CRO-owned
   `usage_index.py` / `root_progress.py` are read-only.
6. Skill residency, rollover decider, idle-return: cite only. This file committed alone. No GEX44,
   credentials or env vars (the test fixture env var in T5 is test-local).

## 3. Verified premises (2026-10-03; corrected by audit)

- CPP HEAD `123c96cc`, `feature/knowledge-acquisition`, ahead 11, dirty tree owned by peers.
- KSR HEAD `5345ca1` on `master`, 120 dirty entries. Owner STOP 2026-10-01 (commit 14f7840):
  all 4 KSR missions halted; remaining work KSR-B-060..073. **No boot doc mentions the STOP.**
- `.planning/STATE.md:20` says "Milestone v3.0 page2-native-gameselect (active)" -> CONTRADICTED
  by the STOP. `RESUMPTION_FILE.md:1` is the VIS-pane resumption, not the programme's.
- `SESSION_STATE.md` lives in auto-memory (no git), spans every programme, mtime 2026-09-23 vs its
  own "Last synced 2026-08-06" stamp -> CONTRADICTED input.
- Boot entry points (audit gap 4): RESUMPTION_FILE read at boot in 14 sessions (global CLAUDE.md
  RESUMPTION_FILE law), SESSION_STATE in 6 (`MEMORY.md:13`). Both must be rewired.
- `compile_brief` with empty `closure_blocking` prints "nothing is blocking closure"
  (`brief.py:92`) and always renders an epoch task + executor Boundaries (`brief.py:77,134-141`);
  `BriefTooLarge` caps only the brief (16 KB). `retire` disposes an obligation, not a goal
  (`gsd_x_goal.py:100-117`). `oblige` needs a real gate file. `--root` targets any repo.

## 4. Tasks (order is binding: pre-registration before any generator code)

| # | Path | Action | Purpose | Verification |
|---|---|---|---|---|
| T0 | `vault/plans/ksr-epoch-rehydration-2026-10-03.md` (CPP) | create | this plan | committed alone (C0) |
| T1 | scratchpad `arch/boot_facts.py` | create (experimental) | per session: first boot-doc read + what instructed it; boot reads before first Edit/Write; consumed facts from boot docs AND git log AND Owner messages; read amplification | positive control (planted fact found), negative control (shuffled sessions score low), A/A rerun identical |
| T2 | `vault/audits/ksr_archaeology/2026-10-03-boot-rehydration.md` (CPP) | create | **pre-registration, frozen before T4**: eligibility rule + seed + eligible N; labelled critical-fact set (each quoted with file:line or transcript uuid) + sha256 + n per class; reconciliation ledger (each doc fact CURRENT/STALE/CONTRADICTED); KSR-B mapping table; MEMORY row original text; SESSION_STATE backup sha256; H0 class-overlap result | sha256 of the frozen sets recorded in the commit message of C1 |
| T3 | goal store via `gsd_x_goal.py --root <KSR>` | `export` snapshot, then `declare` | `ksr-programme`: intent, acceptance, constraints incl. Owner STOP, `reconciled-at: <KSR sha>`, INTOCABLES/ROADMAP refs + sha256, fp028 ref; blockers as `--constraint` naming the external condition; KSR-B items as constraint/acceptance text; **no obligations and no stand-in gate file** until T8 passes | `status --json`: autonomous OFF; `explain` lists every mapped item |
| T4 | KSR `tools/governance/continuation_view.py` | create | `closure_blocking` computed exactly as `status` does; explicit `task` ("boot orientation only; programme HALTED by Owner STOP 2026-10-01; next legal action = ...") and `authority={'ceiling': <KSR authority in force>}`; header: GENERATED, goal revision, tree_id, KSR HEAD, CPP HEAD + sha256 of brief/contract/convergence, "autonomous: OFF"; one CPP-root constant, exit 2 if missing | whole-file `estimate_tokens` <= 8,000 else exit 1, no write, previous file kept; refuses if `git rev-list <reconciled-at>..HEAD -- . ':!.planning/CONTINUATION.md'` > 0; refuses on ROLLED-BACK marker; same (goal, tree_id) -> same bytes |
| T5 | KSR `tools/governance/test_continuation_view.py` | create | plain-script `_ok/_fail`, pass + fail controls; goals-root env var -> temp fixture store; live store byte-identical after run | mutants each RED: empty closure; drop each critical section; inflate past 8k (refusal + file unchanged); commit after reconcile; CPP root missing; rolled-back marker |
| T6 | KSR `.planning/CONTINUATION.md` | generate | first materialization | header digests match; size <= 8k tok |
| T7 | KSR auto-memory `MEMORY.md` row + one GENERATED pointer line atop `RESUMPTION_FILE.md` | edit | both boot entry points read CONTINUATION first; old docs stay (both surfaces) | MEMORY.md <= 4,096 bytes before/after; re-read immediately before the single Edit; originals stored in T2 |
| T8 | replay (scratchpad) -> T2 | run | recall of CONTINUATION vs frozen consumed/critical sets on the pre-registered sample | critical 100% with n>=3 per class and >=20 total, else INCONCLUSIVE; total >=95%; eligible N<6 -> INCONCLUSIVE; drop-section mutation lowers recall in every class with n>=1 |
| T9 | PRG: 3 real KSR boots, deadline 2026-10-17 | observe | endpoint = first Edit/Write OR first substantive Owner-facing plan/answer; boot counts only if CONTINUATION was its first boot read (others reported off-path) | <=5 turns, <=15k growth, 0 incidents; a proposal that breaks the STOP = incident; no boots by deadline -> EXPERIMENTAL |
| T10 | KSR projections (ONLY if T8+T9 pass, separate commit) | edit | RESUMPTION_PAGE2, STATE, handoff -> generated; RESUMPTION_FILE programme sections only; SESSION_STATE KSR section only, after copying the file to `vault/audits/ksr_archaeology/` with sha256 | assertion: no hand-written duplicate of a projected fact remains |
| T11 | `vault/knowledge_base/ukdl-universal.md` + CBR note (CPP) | append | candidates only, evidence-cited | promotion state recorded |

## 5. Science plan

- H1: a <=8k-token view compiled from durable goal state carries every fact the boot consumes.
- H0: consumed detail differs per session; cross-session overlap is low. Tested in T2 before T4.
- Controls: positive (planted fact), negative (shuffled sets; empty-goal view must fail T8), A/A.
- Mutation: section 4 T5 list; every mutant must be RED, clean control GREEN, no live-store writes,
  no HARNESS_INVALID counted as KILLED.
- PRG boundary: real Owner-started KSR sessions (T9). Offline results never satisfy T9.
- Rollback: revert the MEMORY row and RESUMPTION pointer from T2 payloads; delete CONTINUATION.md
  and the generator commit; append constraint "EXPERIMENT ROLLED BACK <date>" to `ksr-programme`
  (no verb deletes a goal; the generator refuses on that marker). The T3 export snapshot is the
  pre-state record.
- Promotion: EXPERIMENTAL now; CANDIDATE only if all gates pass; BASELINE needs a second project.

## 6. Anti-Goodhart

- Small because it omits -> T8 recall against sets frozen BEFORE the generator exists.
- Author grades own labels -> frozen sha256 set, n minima, INCONCLUSIVE below them.
- Cherry-picked sessions -> eligibility rule + seed pre-registered; stratified pre/post-STOP and pane.
- Fewer turns because nobody edits under the STOP -> endpoint includes Owner-facing answer; a
  STOP-violating proposal is an incident.
- Stale view -> reconciled-at refusal; tree_id + CPP digests in header; empty-closure mutant.
- Write amplification merely moves -> after T10 count hand edits to projected facts (must be 0).

## 7. Concurrent-writer safety

KSR: 120 dirty entries; commit new files by explicit pathspec; verify `git log -1 --format=%s`.
MEMORY.md: re-read right before the single edit (three panes contended on it before). CPP: only
this plan, `vault/audits/ksr_archaeology/`, and the separate KNOWN_FALSE_POSITIVES recurrence line
are mine. `modules/gsd_x/goal/` is read-only here (peer worktrees active).

## 8. Micro-commits

C0 CPP plan (this file only) -> C1 CPP pre-registration + archaeology (T1-T2) -> T3 goal events
(store, not git) -> C2 KSR generator + tests -> C3 KSR first CONTINUATION.md -> T7 boot wiring
(memory row not in git; RESUMPTION pointer in C3) -> C4 CPP replay + PRG results -> C5 KSR
projections (gated) -> C6 CPP UKDL/CBR candidates. Separate: C-FP CPP KNOWN_FALSE_POSITIVES line.

## 9. Not built

New context engine, new IR, new ROI ledger, 13th transcript parser, digital twin, portfolio
scheduler, capability ISA, ML/learned routing, autonomous self-modification, event-driven goal wake,
digest+pointer tool firewall (RESEARCH; RTK PowerShell T6 is the owner path).

## 10. Risks

- T9 needs 3 real KSR sessions while the programme is halted; deadline 2026-10-17.
- Lexical extraction misses identifier-free facts; critical classes are labelled and frozen in T2,
  blind spot stated there.
- Reconciliation may surface contradictions that change authority -> Owner decides, never silent.
- CPP library drift between runs -> header digests make it visible; no pin beyond that in EXPERIMENTAL.

## 11. Ultra phase-4 audit (2026-10-03)

Auditor role via `general-purpose` (fix (1) of FP-AGENT-CONTRACT-IDENTIFIER; the read-only
specialist was refused by the guard's UNBOUND branch). Verdict EXECUTE-WITH-FIXES, 15 gaps, all
injected above: 1 closure_blocking (T4/T5), 2 epoch task/boundaries (T4), 3 whole-file bound (T4/T5),
4 two boot entry points (T1/T7/T9), 5 SESSION_STATE outside git (T10/T2), 6 STOP absent from docs +
pane-scoped RESUMPTION (T1/T3/T10), 7 obligations need real gates (T3), 8 rollback verb (s5),
9 CPP import (T4/T5), 10 frozen labels + n minima (T2/T8), 11 pre-registered sample (T2/T8),
12 T9 endpoint under STOP (T9), 13 reconciled-at refusal (T3/T4), 14 MEMORY 4 KB + re-read (T7),
15 autonomous OFF (T3). Gaps 1, 2, 4, 6, 8 re-verified by the parent against source lines.
Full gap list: session scratchpad `phase4_gaps.md`.
