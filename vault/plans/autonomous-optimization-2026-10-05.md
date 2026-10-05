---
id: PLAN-AUTONOMOUS-OPTIMIZATION
date: 2026-10-05
status: APPROVED 2026-10-05 (Owner "Approve (Recommended)" to the inline plan; this file mirrors it)
covers: [autonomous-optimization, zero-rescan, opportunity-lifecycle, kme-l-challenger, usage-index-v5, optimization-ratchet]
parents: [vault/plans/incremental-cognition-program-2026-10-03.md, vault/plans/zero-rescan-reality-scan-2026-10-05.md]
mode: /cpp-gsd-long Ralph mission; EXECUTION by default, PLAN for P1, no ULTRA unless a slice proves it needs one
run_plane: GEX44 (Owner decision 2026-10-05; laptop 1.84 GB free < 4 GB arming gate)
done_gate: python tools/test_incremental_cognition_program.py --final (extended by P0 for the gen2 pillars) + P6 PRG
workstream: .planning/workstreams/autonomous-optimization
---

# Autonomous Optimization -- IC gen2 (reopen pillar M + pillars O-R)

Owner brief: the pasted /cpp-gsd-long "Autonomous Optimization" mission (2026-10-05). Its source datasets are
requirements and hypotheses, not proof. Reality wins.

## Reality at approval (laptop HEAD 7ea78fa3, branch feature/knowledge-acquisition), measured

| capability | owner | state |
|---|---|---|
| KME-L full-scan diagnosis | `vault/plans/zero-rescan-reality-scan-2026-10-05.md` | CONFIRMED. Unscoped population 869 s / 101.5 GB (10 scans of 9.5 GB); scoped 24 s / 2.83 GB (~36x from scope alone) |
| corpus identity | same | 4,368 paths -> 4,007 realpaths -> 3,884 contents; 3 junctions (mcp-video-analyzer doubles one PP session); CostaLuz 22 files / 99 MB |
| incremental ingest | `tools/usage_index.py` schema v4 | LIVE (offset cursor, size+mtime_ns skip). LACKS tool events, cwd, project attribution, content identity |
| champion path | `wiki/tools/kme_pillars.py`, `kme_token_audit.py` | full rescan per run, `--until auto` repeats it, never reads usage_index |
| duplicate parsers | ~10 parsers, 12+ globs, 3 freshness vocabularies | 1 automatic full-corpus scan: `tools/sovereign_miner.py` daily 03:00; 13 manual |
| programme home | incremental-cognition (IC) | E/G/L cover KME-L; M (optimizer) was "dispositions only" |
| opportunity signals | `modules/cognitive_os/co_12_telemetry.py`, `tools/skill_opportunity_signals.py` | skills only, not wired to pricing/promotion |
| baseline ratchet | `modules/tower/ratchet.py` (promote/revert/verify_chain) | LIVE; no second ratchet |
| quality-loss instrument | CE gen2 owner_map row 25 | ABSENT; live champion/challenger DEFERRED_BY_OWNER_QUOTA (IC row 11) |
| TOK-18 cost planner / PGO / model-boundary accounting | cognitive-economy Gen3 | documented; Gen3 T2-1 canary not before 2026-10-11 -- NOT touched |

Documented-only (no executable owner): Technical Capital Allocator, opportunity lifecycle, factory evolution.

## Ownership decision

No new OS / runtime / DB / scheduler (HR-NOVELTY-001 expected EXTEND_EXISTING_OWNER, run in P0).
- Programme: IC gen2 ledger (the IC `frozen` object is immutable, so new pillars live in a gen2 ledger with its own
  FROZEN_AT -- skill-capability/gen2 precedent). Reopen M as executable; add O-R.
- Substrate: `usage_index` v5 (tool events, cwd, project attribution, realpath + content identity via
  `tis_observed.store_identity`). G7 "one parser".
- Detectors: extend CO-12 opportunity rows to cost classes.
- Promotion: `modules/tower/ratchet.promote`, families scoped to evidence.
- Retirement: duplicate parsers, each by measured disposition.

## Proof slices

- P0 spec + gen2 freeze + novelty gate + reconcile IC gen1 state.
- P1 usage_index v5 (PLAN mode): incremental migration, mixed attribution, junction/_archived dedup; negative controls.
- P2 KME-L challenger: index -> project-scoped raw -> global only for explicit cross-project; deopt with reason;
  invalidation by parser/metric/watermark. Equivalence = the 7 KME-L measurement files reproduce identically. The
  challenger may lose to plain scoping.
- P3 generic detectors over tool events; discovery eval with seeded, no-opt and low-ROI controls.
- P4 opportunity rows + lifecycle + pricing + autonomy envelope; predicted vs realized dividend.
- P5 second workload, taken by the loop itself: `sovereign_miner` onto the index (shadow -> canary -> certify).
- P6 CBR at project scope; family scope only on P5 transfer; fresh-worker inheritance test; bypass regression gate;
  overhead vs savings.
- P7 red team, UKDL 3 levels, Vault, IC ledger N, handoff.

## Economics (honest prior)

Automatic full-corpus recurrence is ~1/day; the burden is manual measurement runs (bundle rows up to 9 scans each).
Expected dividend: measurement runs minutes -> seconds, daily miner full parse -> delta. Not a large standing token
saving. P4 records this and stops below break-even. Champion/challenger is offline replay (IC rows 11/12).

## Boundaries

GEX44 plane; laptop-only items (live scheduled-task deploy, laptop install inheritance test, `~/.claude/` settings)
go to the owner bundle as `[<P>]` lines. Pathspec-scoped commits, no push from the laptop shared checkout.
