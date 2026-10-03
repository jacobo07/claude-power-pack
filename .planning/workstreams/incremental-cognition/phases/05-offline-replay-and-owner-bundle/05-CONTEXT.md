# Phase 5: Offline replay and owner bundle - Context

**Gathered:** 2026-10-03 (GEX44, orchestrator; discuss skipped via workflow.skip_discuss)
**Status:** Ready for planning
**Mode:** Auto-generated from ROADMAP + frozen rule L. Pillar L; owner bundle consolidation.

<domain>
## Phase Boundary

Goal: offline replay ranks the live experiments; every Owner item is in one bundle.
Depends on: Phase 3 (its KME instruments: rereads, residency, retries).

Frozen rule L (owner CE ledger): "offline replay of KME-L (late rollover, identical rereads,
unchanged-precondition retries) ranks live experiments; live champion/challenger sessions spend quota and need an
Owner decision". Predicted RESEARCH_INSUFFICIENT_EVIDENCE.

Run plane: KME-L is laptop-plane. On GEX44: build the offline replay ranker over the Phase 3 instrument outputs
(`wiki/tools/kme_pillars.py` subcommand outputs / measurement JSON), test it on fixtures from both poles, smoke it
on KME-G (`plane: gex44`, denominator KME-G, not the frozen one), and record the KME-L run as a `[L]` owner-bundle
line. Live champion/challenger sessions: `[L]` owner-bundle line asking for the quota decision (never spend quota
from this run).
</domain>

<decisions>
## Implementation Decisions

- Replay ranker: new subcommand `rank` in `wiki/tools/kme_pillars.py` (or `wiki/tools/kme_replay.py` if Phase 3's
  module shape makes that cleaner). Three candidate experiments scored on the same denominator: (1) late rollover
  (context residency past a threshold that an earlier compaction/rollover would have cut), (2) identical rereads
  (Phase 3 E numerator), (3) unchanged-precondition retries (a tool call repeated with identical input and no
  intervening state change -- e.g. same test command rerun with no Edit/Write between). Output: ranked list with
  each upper bound as an UPPER BOUND (never a realized saving -- frozen displacement rule), denominator named, and
  `command:`.
- Tests `tools/test_kme_replay.py` (V-KMER-*): each candidate detected on a positive fixture and absent on a
  negative one; ranking order deterministic; "UNMEASURED" when an input is missing, never 0.
- Owner bundle consolidation: `vault/programs/incremental-cognition/owner-bundle.md` gets a summary table at the
  top (pillar, action, exact command, what closes when it lands) covering every `[X]` line from phases 1-5;
  include the a7 re-login, the env deploy, node upgrade, laptop deploy of gsd_mission.py at >= 4 GB free, each
  KME-L command, the K reference, and the L quota decision.
- Ledger: `state.L` stays OPEN unless the Owner decision is recorded (then AUTHORIZATION_BOUND needs an
  `owner_decision` evidence file naming `[L]` -- only the Owner's own words count; never fabricate a decision).
- Evidence `vault/programs/incremental-cognition/evidence/L.md` (Product Delta + Intelligence Delta).
- Commits: explicit pathspec, `git commit -F <msgfile>`, plain single git commands, verify `git log -1`. Never push.

### Claude's Discretion
Thresholds for "late rollover" (state them), module layout.
</decisions>
