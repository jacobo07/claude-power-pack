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
- ~~The mirrored extension is on disk and not loaded until a window reload.~~
  **Closed by observation 2026-09-21T21:44:48Z**, not by a file comparison. The
  delivery ack for `…:compact:1790027070` reads `"enters":3` with
  `"arg_tail":"focus on v1 milestone shipped, archived, tagged, merged to main"`
  — both fields exist only in the build that carries `argumentTail`, so the
  RUNNING module is the mirrored one. Behaviour, not bytes on disk: a hash match
  would have said the file arrived, which is the claim that was never in doubt.
  The same delivery also measures the argument tail's *redundant* branch, which
  `extension.js:149-154` predicts as "a stray user message — a wasted turn,
  visible, not destructive". Observed instead: the two-Enter path had already
  submitted `/compact` **with** its argument (the command ran carrying
  `focus on v1 milestone shipped, archived, tagged, merged to main`), and the
  harness discarded the third submission mid-compaction, reporting
  `"focus on …\n" never got sent`. Cheaper than the predicted branch — no turn
  was spent — and the notice is about the redundant copy, not about the
  delivery. Worth correcting in that comment; the tail itself stays
  unconditional, because the extension still cannot observe whether the first
  submission landed (PR-CONT-06).
- Five pre-existing mirror DRIFT pairs, none introduced by v1. (Six before the
  v1 merge; advancing `main` closed `hook-dispatcher.js` on its own, because
  that pair was only drifting while `main` sat 95 commits behind.)
- The durable `/cpp-compound` fix (Steps 7+8 owned in-process) is blocked behind
  another writer's abandoned change in `tools/compound_unattended.py`.
- **The parity census cannot see a PowerShell hook.** `modules/mirror_discovery`
  declares the hooks domain as `("hooks", "*.js")`, so the three auto-compact
  chain scripts mirrored in `14b2894` are structurally invisible to
  `verify_global_mirrors.py` — measured: all three are present on both sides and
  byte-identical (`001ACACEB31DEB55`, `E6B9D21CD69DA01B`, `1BC35366C09F60DF`),
  and none appears in the census as OK or as DRIFT. Merging to `main` made them
  *tracked*; it did not make them *visible*, and those are different claims.
  The obvious fix is a trap: a second `("hooks", "*.ps1")` tuple collapses under
  `dict(DOMAINS)`, which `install_global_core._repo_population` resolves through
  (`discovery.py:84-92` says so in its own warning), so the second entry would
  silently REPLACE `*.js` rather than extend it. Deployment risk is separately
  zero — `SHIPPABLE_KINDS = ("agents", "commands")` excludes hooks — so this is
  a census-shape problem, not a safety one. It needs a multi-glob domain, not a
  second tuple.
