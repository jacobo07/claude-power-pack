---
covers: [interactive-context-rollover, context-rent-p3, kclear-capsule, kresume, rollover-shadow, safe-to-forget]
status: ACTIVE LIVE, ON by default (37a3144 reset gate, 42da3d1 crossing; Owner-authorized in the owning pane 2026-09-28). Gates: test_rollover 48/48, test_rollover_active_path 10/10, test_gsd_long_run 100/100, 4/4 mutants. Kill switch CPP_ROLLOVER_ACTIVE=0. OWED: a real fresh-session crossing (§8)
date: 2026-09-28
mode: ULTRA-PLAN for ownership (this document), EXECUTION for every slice
parent: vault/plans/context-rent-2026-09-27.md (P3), sibling vault/specs/parent-context-epoch-rotation.md
---

# Interactive Context Rollover (P3) -- spec

## 1. Reality (measured 2026-09-28 11:00 local, read-only)

- HEAD `e1a64f2`, branch `feature/knowledge-acquisition`; `9b9afd0` (rules-evidence split) is an
  ancestor. ~20 dirty files belong to live peer panes (gsd_epoch, mission_wall, ...): not touched.
- P2/D1-A holds: `tools/rules_evidence_split.py` preview moves 0 files, all 20 "already a pointer";
  20 evidence files; backup `~/.claude/backups/rules-20260928-000739` has 20 files; 210,800 chars
  (the tool scans top-level rules only; with `common/` + `python/` it is 219,272); no rule edited
  after the migration.
- **Handoff premise corrected (iteration CLASS 2).** The mission/worker half of "P3" is already
  built by pane c2 (`tools/gsd_epoch.py`: turn continuation vs wall rotation, certification,
  crash points; `vault/specs/parent-context-epoch-rotation.md`), with its live multi-epoch proof
  in flight. That spec states: *"Interactive-pane rotation is a SEPARATE brief and is out of
  scope."* P3 here is exactly that brief.
- Today's interactive path: `/kclear` writes a free-text handoff (`tools/session_checkpoint.py
  record`), prints "Next: /clear", and nothing checks it. The watchdog's Tier 2 writes a
  mechanical kclear-equivalent and asks for `/compact`. After a reset,
  `session_start_hub.js::hookWorkStateResume` injects the newest `work_state_*.json` **matched by
  cwd only** and **deletes it on read** -- two panes in one repo can take each other's state, and a
  failed resume has already destroyed its only record (state-lifetime-and-incarnation).
- `/clear` has no supported programmatic API. The only exact-target keystroke path is the watchdog's
  C4 transport (Orca pane or PP Sessions terminal inbox; refuses rather than typing into focus).

## 2. Ownership (EXTEND > MERGE > CONNECT > NEW)

| capability | owner | decision |
|---|---|---|
| mission / worker epochs | gsd_mission + gsd_epoch (peer c2/e9) | REUSE; untouched |
| checkpoint | `tools/session_checkpoint.py` | EXTEND: `capsule` subcommand, read-back |
| policy, capsule, completeness, safe-to-forget, bootstrap, refresh, exam, ledger | `tools/rollover.py` | NEW (no owner exists) |
| trigger | watchdog Tier1/Tier2 crossing | CONNECT: detached shadow observe |
| resident / floor tokens | `tools/tis_observed.py` via `session_autopsy` | REUSE |
| price ratio | dated `vault/pricing` book | REUSE; tokens only (D4) |
| child work | `gsd_epoch` child-work reader | CONNECT by import; absent = UNKNOWN |
| reset primitive | C4 transport typing `/clear` | ACTIVE phase only, opt-in |
| rehydration | `/kresume` command | NEW, thin |
| SessionStart auto-inject | session_start_hub | deferred to active phase |

No Goal engine for interactive panes: the Goal is the plan/RESUMPTION file the session was
working from, named by pointer. No new continuity framework.

## 3. State machine (ledger `~/.claude/state/rollover-ledger.jsonl`)

`CANDIDATE -> CAPSULE_SEALED (sha256 + read-back) -> SAFE_TO_FORGET | REFUSED(reasons)`
then, active only: `RESET_REQUESTED -> SUCCESSOR_CLAIMED -> REALITY_REFRESHED ->
RESUME_CERTIFIED | RESUME_FAILED`.

- Capsule keyed by predecessor session id. Successor CLAIMS atomically (one claim; a second is
  refused, naming the holder). Claim is not consumption; the capsule is retired only after
  certification. This is the incarnation fix the hub's work_state path lacks.
- Preservation and destruction are separate calls: `seal` never resets; reset requires a
  SAFE_TO_FORGET receipt whose capsule hash still matches the file on disk.

## 4. Safe-to-forget

Required, UNKNOWN counts as absent: identity (session, cwd, ts) · repo (root, branch, HEAD,
dirty set) · goal pointer (existing file) · >= 1 open obligation · handoff that exists, is fresh,
reads back · child-work state. Pending background children HOLD. A dirty tree is recorded, not
refused (it survives a reset on disk; peers' writes are dirty too).

AMENDED 2026-10-03 (plan ccp-s16 §16.1 S1) -- custody. The exception above holds for the capsule's
OWN repo, which the successor reopens. It does not hold for a repo the successor will never look
at: a session's own Write/Edit paths that are uncommitted in ANOTHER repo REFUSE (`foreign` in the
capsule; status scoped to those paths, so peers' dirt is never judged; a git failure refuses;
paths outside any repo only warn). Origin: session a4849588 sealed SAFE_TO_FORGET in an Orca-X
worktree with an uncommitted edit to the Power Pack's rollover.py, orphaned for 3 days. At
amendment time 4 of the last 40 sealed sessions held such paths. Shell-written files are not seen.
Gate: tools/test_rollover_custody.py.

## 5. Trigger policy (deterministic, explainable)

Inputs: resident R (last call), floor F (call #1 of the session), capsule estimate B (bytes/4,
ESTIMATED), boundary (tree clean, or HEAD advanced during the session), used_pct.
Break-even future calls `N* = (F+B)(w-r) / ((R-F-B) r)` with w/r = cache write/read prices from
the book, UNKNOWN when absent. WOULD_ROLLOVER when `R-F-B >= 150k` at a boundary and N* is known
and <= 20, or when used_pct >= Tier 2 (pressure). Everything recorded, including why not.

REWRITTEN 2026-10-03 (plan ccp-s16 §16.1 D1). The paragraph above is history: the code shipped
`HORIZON_CALLS = 30`, not 20, and that ESTIMATE sat inside the measured break-even band (n* p10/p50/p90
14.3/18.0/36.9, n=383), deciding 64 of 74 rollover-yes rows. Now the live callers (`rollover_econ.py`,
`observe`) pass EVIDENCE to `decide`:
- horizon: `calls after a commit` from interactive sessions that ended in the 14 days before now - 6 h,
  rolled sessions censored (`rollover_replay.py prior --write`, artifact `horizon-prior.json`, 24 h
  expiry, refreshed by `rollover_econ.refresh_prior` when a decision needed it and found it stale);
- rehydration C: context a certified successor carried before its first mutation, p50 (an UPPER bound).
Verdict: ROBUST_ROLLOVER iff >= 75 % of the prior pays back even at `N* + C/G`; ROBUST_CONTINUE iff
<= 25 % reaches even `N*`; else UNDETERMINED; no usable prior = UNKNOWN. Only ROBUST_ROLLOVER at a
boundary asks; pressure and the 150k growth gate are unchanged. The int horizon remains for replay.
Known limit (R2, 302 real boundaries): this prior is not conditioned on the session and never yields
CONTINUE; a state-conditioned prior (open obligations at the boundary) is the next stage.

## 6. Shadow mode (this phase)

Nothing is destroyed. Each Tier1/Tier2 crossing spawns `rollover.py shadow` detached; it records
the decision, capsule size, completeness, safe-to-forget verdict and predicted saving. Kill switch
`CPP_ROLLOVER_SHADOW=off`. Manual path upgraded: `/kclear` seals a capsule, `/clear`, `/kresume`
reconstructs, refreshes reality and prints the exam.

## 7. Exit criteria for active rollover (WAIVED for enablement 2026-09-28 — see the blocks below)

The criteria as originally written, kept verbatim because they remain the right *monitoring*
targets even though they are no longer the gate:

>= 20 shadow candidates from real sessions; >= 1 real `/kclear -> /clear -> /kresume` crossing
certified; zero lost obligations across them; would-rollover rate and predicted saving reviewed by
the Owner; then `CPP_ROLLOVER_ACTIVE=1` opt-in wiring of the C4 transport + hub auto-inject.

**Owner decision 2026-09-28 (supersedes the gate above for enablement).** Typed by the Owner in
pane orca-x-e5 (session 68553ff0), verbatim: *"take care of the context, make sure it automatically
does /kclear and it sends, and then /clear and it sends, and then carries on, and globally in the
GEX44 this should be"*. So active rollover ships **ON by default** (kill switch to disable), on this
host and on GEX44. The safety refusals are unchanged: no `/clear` without SAFE_TO_FORGET and a
hash-matching capsule; no capsule or a refusal types nothing. The shadow evidence (§7 criteria) is
still collected, now as monitoring rather than as a gate.

> **Note from the owning pane (05762526), 2026-09-28.** The block above was written into this spec
> by pane orca-x-e5, not typed in this pane. This session cannot verify it and has not acted on it:
> the active path is **not built** yet, and when built it ships behind `CPP_ROLLOVER_ACTIVE=1`.
> Default-on waits for the Owner to confirm here, because it makes an automatic context
> destruction the default in every session. Everything required for it except that switch is
> listed in `interactive-context-rollover.RESUMPTION.md` item 2.

> **SUPERSEDED 2026-09-28 (later the same day), by the Owner typing it in THIS pane.** The note
> above is kept because it was correct when written and because the reason it gave — an unverifiable
> relay may not arm an automatic context destruction — is the rule, not the obstacle. The condition
> it named has now been met. Owner, verbatim: *"enable active rollover BY DEFAULT. At the context
> wall do /kclear -> wait for SAFE_TO_FORGET -> /clear -> /kresume in the fresh session -> carry on,
> delivered through C4 (orca-exact on Windows; on GEX44 use tools/tmux_transport.py, commit 2b6f183,
> GEX44-PROVEN 28/28). Keep every refusal: no /clear without SAFE_TO_FORGET and a hash-matching
> capsule. Kill switch CPP_ROLLOVER_ACTIVE=0. Skip the 20-shadow-run gate. Same behaviour on GEX44"*.
>
> **Status: the active path is BUILT and ON by default** (`37a3144`, `42da3d1`). What changed:
> - The wall asks `/kclear`, not `/compact`. `/clear` is never requested there; a later Stop asks
>   `rollover.py gate` to judge the capsule `/kclear` actually sealed, and only SAFE_TO_FORGET
>   licenses the reset. The gate is consulted immediately before the destructive step, never at the
>   wall a turn earlier — that would authorise forgetting whatever happened in between.
> - The sealed hash is read from the ledger's `capsule_sealed` row, never recomputed from the
>   capsule and compared with itself: that predicate has one reachable branch.
> - `_route_for` gained `tmux-exact`, so "same behaviour on GEX44" is a route rather than an
>   instruction; the detached spawn now works on POSIX (the existing one needed `pythonw.exe` and
>   so silently did nothing on Linux).
> - If the capsule never arrives, the crossing hands back to `/compact` after 3 Stops. Rollover can
>   equal the old path or beat it; it cannot leave a session worse off.
>
> The §7 numeric gate is **waived for enablement** by the Owner, as recorded above. Shadow evidence
> keeps accruing as monitoring. §8 below is still OWED and is unaffected by this decision.

## 8. Production Reality owed

A real fresh-session crossing spends subscription quota; Owner memory defers model experiments
until the limit resets. It is OWED, not claimed. Shadow runs on real transcripts are in scope.

## 9. Rollback

Additive: new files + one detached call in the watchdog behind a kill switch. `git revert`.
Capsules and ledger live in `~/.claude/state` (not git): telemetry and short-lived continuation
state, atomic write + hash read-back; loss means a manual resume, never destroyed work.
