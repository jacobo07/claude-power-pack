# Roadmap: Claude Power Pack

## Milestones

- ✅ **v1 continuation-proven-live** — Phases 1-5 (shipped 2026-09-21)

## Phases

<details>
<summary>✅ v1 continuation-proven-live (Phases 1-5) — SHIPPED 2026-09-21</summary>

- [x] Phase 1: Two-pane exactness drill — the continuation reaches A's own terminal and never B's (completed 2026-09-21)
- [x] Phase 2: UserPromptSubmit chain deadline — is the cap or the clock discarding hook output (completed 2026-09-21)
- [x] Phase 3: Promote the exact-target lessons — the CONT rules into the UKDL, the router sentence corrected (completed 2026-09-21)
- [x] Phase 4: Reap the stale autorun markers — reap by the session's own clock, not the file's (completed 2026-09-21)
- [x] Phase 5: Close the continuation debts — the three this milestone exposed, plus a fifth found in-phase (completed 2026-09-21)

**Acceptance gate — met, and it was produced by the run rather than planned:**
`gsd_long_run.py report` returns `PROVEN` — 4 crossings, 2 confirmed,
`window_confirmed 2`.

Full detail: [`milestones/v1-ROADMAP.md`](milestones/v1-ROADMAP.md) ·
Audit: [`milestones/v1-MILESTONE-AUDIT.md`](milestones/v1-MILESTONE-AUDIT.md) ·
Integration: [`INTEGRATION-CHECK.md`](INTEGRATION-CHECK.md)

</details>

## Carried into the next milestone

Named in the v1 audit's `tech_debt` block, listed here so they have somewhere to
be picked up from rather than only somewhere to be recorded:

- No re-derivable instrument for the chain-deadline measurement (phase 2).
- The reap path has never deleted a real marker (phase 4).
- `continuation_transport`'s own delivery and confirmation path is unexercised —
  this host routes through the terminal inbox, so a second producer of
  `resume_confirmed` has never fired.
- The mirrored extension is on disk and not loaded until a window reload.
- Six pre-existing mirror DRIFT pairs, none introduced by v1.
- The durable `/cpp-compound` fix (Steps 7+8 owned in-process) is blocked behind
  another writer's abandoned change in `tools/compound_unattended.py`.
