# Interactive Context Rollover (P3) — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/interactive-context-rollover.md`.
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Sibling owners: `gsd_epoch`/`gsd_mission` (panes c2/e9) own MISSION worker rotation; do not edit them.

## Thesis
A long Goal must not need a long context. For ordinary interactive sessions: /kclear seals a
capsule (hash + read-back), SAFE_TO_FORGET gates /clear, /kresume claims it (one successor),
refreshes reality and runs an exam; only the claim holder can certify; certification retires it.

## Sealed
`5624c17` rollover.py + /kclear capsule + /kresume + spec · `440bce4` watchdog Tier1/Tier2 shadow
(pythonw, detached, `CPP_ROLLOVER_SHADOW=off`), per-session handoff `memory/handoffs/<sid>.md`,
BOM strip, fenced certify with one flag per answer.

**ACTIVE ROLLOVER IS ON BY DEFAULT** — Owner authorization typed in the owning pane 2026-09-28
(spec §7, superseding block). Kill switch `CPP_ROLLOVER_ACTIVE=0`. The 20-shadow-run gate is
waived for enablement and now runs as monitoring.

- `37a3144` **the reset gate**. `rollover.py gate` is the ONE authority for whether `/clear` may
  be typed. It judges the capsule that was sealed and shown, never one recompiled at the moment of
  destruction. The sealed hash comes from the ledger's `capsule_sealed` row — hashing the capsule
  and comparing it with itself has one reachable branch. Verdicts/exits: SAFE_TO_FORGET 0,
  REFUSED 3 (moved, stale, certified, or the seal itself refused), NO_CAPSULE 4 (nothing sealed).
- `42da3d1` **the crossing**. Wall asks `/kclear`; a later Stop consults the gate and only then
  asks for `/clear`; `session_start_hub` emits a `/kresume` card on `source=clear` for an
  unretired capsule naming this repo. `_route_for` gained `tmux-exact` (GEX44 parity is a route,
  not an instruction) and `_detached` spawns on POSIX too — the shadow spawn needed `pythonw.exe`
  and so silently did nothing on Linux. No capsule after 3 Stops → hands back to `/compact`, so
  rollover can equal the old path or beat it, never leave a session worse off.
- `d10bd31` (peer pane) /kresume never claims a capsule no successor could certify.

Gates: `python tools/test_rollover.py` 48/48 · `python tools/test_rollover_active_path.py` 10/10
(owns the destructive half) · `python tools/test_gsd_long_run.py` 100/100, with the old
`V-GSDLR-WD-COMPACT-EXPECTS-PREFIX` INVERTED in place to `/kclear` plus a kill-switch control
proving `/compact` returns byte-identical · 4/4 mutants, run as a differential against the
unmutated copy's own baseline · hub driven for real across 4 cases (clear/startup/killswitch/
other-repo). Untouched: continuation_transport 28/28, wiring 14/14, cold start 11/11, drills 9/9.

## Open
1. **§8 Production Reality is still OWED**: no real fresh-session `/kclear -> /clear -> /kresume`
   crossing has been observed end to end. Everything above is unit- and hub-proven, not
   crossing-proven. An idle worktree (e.g. `TUA-X-cross-angle`, which carries no SGE work) is the
   safe place to drive it without risking live work.
2. Shadow calibration continues as monitoring: `python tools/rollover.py status`.
3. GEX44 has the `tmux-exact` route wired but it has **not** been exercised on GEX44 itself;
   `tmux_transport` is GEX44-PROVEN 28/28 as a transport, which is not the same claim.

## Known-not-mine
`test_autocompact_per_session` is a load-sensitive flake (its daemon is a 3 s-TTL PowerShell
script read from `~/.claude/hooks`, i.e. the SAME file in every tree, so no change in this repo
is in its observation domain). Measured 38/38 twice at 7.2 GB free after failing at low headroom.
`test_two_pane_exactness` 6/7 is pre-existing, reproduced on a HEAD worktree.

## Coherence anchor
`python tools/rollover.py status` shows `shadow_candidate`, `capsule_sealed`, `reset_gate` and
`resume_certified` rows; `git log --oneline -4` shows `d10bd31 42da3d1 37a3144`.

## Start instruction
`git log --oneline -5`, then `python tools/test_rollover.py && python tools/test_rollover_active_path.py`,
then Open item 1. Trust git + the ledger over this file.
