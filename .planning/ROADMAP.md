# Roadmap: Claude Power Pack

## Milestones

- ✅ **v1 continuation-proven-live** — Phases 1-5 (shipped 2026-09-21)
- 🚧 **v2 econ-safex — economic safe exhaustion** — Phases 6-17 (Owner-approved 2026-10-13, programme 32M)

## v2 econ-safex (active)

Design, budget and contracts: [`vault/plans/econ-safe-exhaustion-2026-10-13.md`](../vault/plans/econ-safe-exhaustion-2026-10-13.md)
(commit `2eb07637`). Read §4 (target design) before planning any phase.

**Invariants for every phase (from the Owner's mission prompt):** never raise a cap to
make work fit; never weaken or override hard economic enforcement; never overspend;
UNKNOWN closeout cost is not zero; tests that passed before a mutation are not proof
after it; never commit or touch foreign dirty state (PRR worktree `C:\Users\User\Apps\pp-prr`
is touched ONLY by Phase 14, ONLY after Phases 7-11 are green). Micro-commit every
coherent causal unit. Kill switches: `CPP_LEASE_EDGE=off` (exists), `CPP_SAFEX=off` (new,
Phase 7 introduces it and every new enforcement path honours it).

**Economics:** goal `econ-safex`, programme 32,000,000 (capital sha `8d518345…`), lease L1
4,000,000. Open each successor with `tools/mission_spend.py goal-lease-open` at cap
≤ 6,000,000 and reserves `--proof 300000 --closeout 600000 --recovery 300000`; never
open the last 1,200,000 of programme. Programme exhaustion = AUTHORITY_REQUIRED → stop
and hand to the Owner. Stop-loss: a unit settling > 1.5x its target twice → Owner.

- [ ] Phase 6 (W0): Incident reconstruction — replay transcript `0917a65c` (last 10 boundaries, per-call cost, horizon) into `vault/programs/econ-safex/evidence/W0-prr-incident.md`; numbers carry their command. (P50 1.0M)
- [ ] Phase 7 (W1): Reserve accounting — `productive_spendable` in the ledger fold; non-zero reserve floor (6 calls × max(fresh floor, 60K) when no history); packet/lease reserves can never be 0; `CPP_SAFEX` switch. (2.5M)
- [ ] Phase 8 (W2): Goal-mode pre-boundary admission + checkpoint horizon in `hooks/session_budget_guard.js` `decideGoal` (ADMIT/DEFLATE/CLOSEOUT_ONLY/SETTLE_AND_RENEW/RECOVERY_SEAL/DENY/OWNER_BOUNDARY); existing deny kept as defence in depth. (2.5M)
- [ ] Phase 9 (W3): Lease state fold OPEN→APPROACHING_RESERVE→CLOSEOUT_ONLY→SEALED→SUCCESSOR_READY→EXHAUSTED; invariant EXHAUSTED ⇒ SEALED; `lease_close` refuses without outcome receipt; one liveness record per lease end. Plan the ownership question before coding. (2.5M)
- [ ] Phase 10 (W4): `tools/closeout_recipe.py compile|run|verify` — JSON recipe (paths, sha256 per dirty file, tests, gates, pathspec, msg file, rollback ref, postcondition); `run` makes zero model calls. (3.0M)
- [ ] Phase 11 (W5): Recovery capsule — extend the kclear capsule schema (HEAD, dirty hashes, diff id, test receipts, gates, ownership, next obligation, rollback ref, authority state, invalidators); /kresume validates hashes; model-free writer fired on dirty tombstone. (1.5M)
- [ ] Phase 12 (W6): Successor compiler + zero-progress guard + `authority_fingerprint` / `authority_divergence`; successor needs prior lease SEALED, same goal/scope/fingerprint, non-zero progress. Plan authority semantics before coding. (3.0M)
- [ ] Phase 13 (W7): V-SAFEX fault suite (plan §7, 17 cases, each refusal paired with an admitted control) + PRR replay fixture: productive admission stops ≈19.0M with ≥1.0M protected. (2.5M)
- [ ] Phase 14 (W8): PRR stranded-work recovery per plan §6 — patch bundle FIRST, recovery-only lease L3 inside PRR's own programme, verify hashes/HEAD `f6455676`, commit scope exactly as §6, certificate `vault/programs/prr/evidence/F-stranded-recovery.md`. Fallback SEALED_RECOVERABLE capsule. (0.45M of PRR's programme)
- [ ] Phase 15 (W9): UserPromptSubmit hook — measure per-member P50/P80/P95 first; `dead-closer-recovery.js` stat-only fast path; bounded critical lane inside the 15 s harness; do NOT raise the timeout. Global `~/.claude/hooks` edits are Owner-approved for this phase (HR-001: back up, mirror-sync, prove the live copy). (2.0M)
- [ ] Phase 16 (W10): Knowledge — UKDL HR/PR/Traps, FIOS, CBR entries for this incident class. (1.5M)
- [ ] Phase 17 (W11): Self-host canary — evidence that this mission's own leases ran under the new protocol (reserves funded, admission decisions logged, seals on every lease end). (1.0M)

**Done-gate for v2:** V-SAFEX suite exit 0; existing ledger/guard suites exit 0;
`python modules/liveness/reachability.py` exit 0; PRR certificate written; hook P50/P80/P95
before/after recorded; every lease of `econ-safex` ends SEALED.

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
