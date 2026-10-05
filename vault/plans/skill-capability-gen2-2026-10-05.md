---
id: PLAN-SKILL-CAPABILITY-GEN2
status: APPROVED (Owner "y" 2026-10-05; amendments: run on GEX44; arm after the weekly quota reset)
covers: [skill-capability-gen1-close, skill-capability-gen2, skill-activation, skill-evolution, skill-lifecycle, skill-contribution, skill-fitness]
parents: [vault/plans/skill-capability-program-2026-10-03.md]
brief: vault/programs/skill-capability/gen2/OWNER-BRIEF-2026-10-05.md
date: 2026-10-05
---

# Skill Capability -- Gen 1 close + Gen 2 Skill Activation & Evolution

## Reality scan at approval (laptop pane c85f3eb9, 2026-10-05, read-only)
- Gen 1 run: `mission/skill-capability-run` tip 4b74882c, 212 commits (all jacobo07) on top of 287b360a, only in the
  GEX44 clone; bare `mission/skill-capability` still 287b360a. Ledger: 13/14 terminal (each = its prediction), N open,
  0 violations. Mission m-e06956b05759 HALTED "owner BLOCKED and budget: older than 24.0 h" after its last commit.
- Laptop shared checkout: 80 peer commits since 287b360a, 859 dirty paths. Overlap of the run's 181 changed files with
  laptop committed changes 0, with laptop dirty paths 0 -> integration cannot conflict. tools/ is dirty with peers'
  work -> the laptop closeout needs its own clean worktree (runbook step 1 requires a clean tools/ + program dir).
- R1 (retained settings) clean on 2026-10-05. Laptop RAM 4.8 GB free (floor 4 GB).
- Pillar E harness `.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py` (arms N0 N1 R P C;
  `run --arm X --reps N`; claude -p, Opus 5.5, max 40 turns, timeout 1500 s; Windows paths). Laptop rows: N0 0/2,
  R 0/2, P 1/2 (amended shape), C-old 0/2, C-fixed 2/2 (8a79561d, 87a4d014: UNCOMMITTED in results-delivery.jsonl).
  Per-session cumulative context 0.52-0.94 M tokens, 90-310 s.
- 7 invalid-YAML SKILL.md (all "mapping values are not allowed here" = unquoted ': ' in description):
  concurrent-writers-shared-tree (a card source), develop-here-prove-there, evaluation-corpus-governance,
  guard-event-reachability, monetary-quantity-integrity, presence-is-not-residency, recurring-work-cardinality.
- Filename sweep for Gen 2 owners: no file named for a capability genome, fitness arena, activation ledger, context
  MMU or knowledge paging; candidates exist under other names (modules/capability_runtime, modules/skill_router,
  tools/skill_invocations.py, CO-12, tools/reconstructor.py, cognitive_os residency). Resolution = the Gen 2 scan.

## Token estimate given before approval (measured base: Gen 1, 81 transcripts of m-e06956b05759)
Gen 1 actual: 488.6 M processed (cache read 473.7 M, cache write 14.4 M, output 0.45 M, input 5.5 k), 2,759 calls
(84 % subagent), 24 h, 212 commits, ~78 M weighted (CE weighting). Projection: pillar E 8 sessions ~6 M; Gen 1 GEX44
remainder 45-70 M; laptop remainder 10-20 M; Gen 2 scan 30-60 M; Gen 2 execution 400 M-1.1 B. Total ~0.5-1.25 B,
central ~0.8 B (~130 M weighted), ~36 h. n=1 base; the dominant uncertainty is the scan's BUILD vs CONNECT ratio.
Subscription quota only (account Max 20x; both hosts report the same 7-day window, reset 2026-10-11T18:00Z).

## Planes
- GEX44 mission (armed by a GEX44 one-shot timer at 2026-10-11T18:15Z, --max-cycles 16 --max-hours 48):
  phase 10 (Gen 1 GEX44 remainder), phase 11 (Gen 2 scan + successor ledger), phases 12+ (Gen 2 waves written by 11).
- Laptop pane (after the mission, not by it): fetch the run branch from the GEX44 clone (refs only, no force, no
  squash); clean closeout worktree; laptop-plane bundle measurements (items 4, 5, 6, 8, 18); skill-creator declaration
  (item 16, HR-001 backup first); pillar N per LAPTOP-CLOSEOUT (--closeout, --final with R1, CLOSE.md); push to the GEX44
  bare `mission/skill-capability` under boundary 4; --no-ff merge into feature/knowledge-acquisition (hook suites first);
  laptop live-skill sync (overwrite only copies equal to their previous repo blob; ABSENT_LIVE stay absent).
  GitHub publication of feature/knowledge-acquisition stays an Owner boundary (boundary 4: peer commits interleave).

## Pillar E on GEX44 (Owner Q2 authorizes <= 8 fresh sessions)
Plane change: the Owner authorized laptop sessions; the run moved to GEX44 by Owner amendment 1. GEX44 rows form their
own plane: never pooled with laptop rows, laptop rows reported beside. Before session 1, commit a pre-registration:
arms (C = card in deny mode vs N0), n per arm (<= 4, total <= 8), grade rule = the harness's, decision rule fixed in
advance (the separation rule the run computed: 4 vs 4 separates only the 100-point effect), environment record per row
(claude version, model id, card sha256, host), no peeking, no extension, stop conditions (harness invalid on GEX44,
quota five-hour window > 80 %, three consecutive invalid runs). Port only the harness's host paths, behaviour unchanged,
proven by a dry-run on a fixture before any counted session. Terminal by the pre-registered rule; INSUFFICIENT_EVIDENCE
is a valid end; if E's terminal changes, update the E rows of reviews/cbr.md and ledger deltas in the same commit, and
LAPTOP-CLOSEOUT's state.N hashes follow (it pins cbr.md).

## Q4 (7 YAML)
Classify each; repair only where the parsed description is byte-identical to what the host reads today (quote or block
scalar); concurrent-writers-shared-tree is a card source -> bundle item 12 sequence (card text + trailer, --record-cards,
re-render G and H, move state.G/state.H pins) in the same unit. The J gate and --pillar A..M stay PASS.

## Gen 2
Successor ledger `vault/programs/skill-capability/gen2/` (Gen 1 FROZEN_AT is immutable and the verifier requires exactly
A-N) with explicit lineage to Gen 1, verified by the same wrapper pattern. Scan: /d2a-family over the brief's 20 frontier
items, NON_DUPLICATION_LEDGER, HR-NOVELTY-001 13-question proof against a discovered sweep, the iteration prompt if
readable from GEX44 (else note it), one oneshot-architect-auditor pass on the mapping. Mode PLAN; ULTRA only if D2A finds a
genuinely new system. Evidence order: existing telemetry, replay, shadow, natural experiments before fresh sessions.
Every item ends at an honest terminal; laptop-plane Production Reality proofs go to a laptop hand-off file.
