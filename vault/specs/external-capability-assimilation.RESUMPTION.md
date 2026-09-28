# External Capability Assimilation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/external-capability-assimilation.md`.
Worktree `C:\Users\User\Apps\pp-assim`, branch `feat/external-assimilation`; live checkout
`C:\Users\User\.claude\skills\claude-power-pack` on `feature/knowledge-acquisition` (hooks and every
running mission load code from THERE). Last live + pushed: `8ee41c6`; this branch is ahead of it.

## Go-live pattern
Commit in pp-assim; re-read main HEAD; branch files vs main's dirty set must not overlap (another
writer keeps ~590 hook/doc paths dirty there -- never commit in main); `merge --ff-only` in main;
rerun there: test_gsd_mission, test_handoff_packet, test_mission_watchdog, test_gsd_long_run,
test_gsd_epoch, test_rollover_active_path, `node tools/test_gsd_stop_continuation.js`; push both.

## State (2026-09-28 ~20:10 Madrid)
- T8 closed (`c9f750d`): items 29 routing metrics (-> gsd_epoch certify), 30 verified reuse
  (-> batch_drafts), 31 paired experiments (exp-successor-packet-002), 12 packets by reference on
  `gsd_mission.py handoff --packet`. Decision: `vault/experiments/exp-successor-packet-002/REPORT.md`.
- Item 22 task ledger `fe2be9c`, item 32 adaptation `8ee41c6`: merged into Goal Spine, PLANNED --
  the Goal Spine engine has NO live invoker (UWCP S6). Item 33 charter lab: seam note `ffc0685`.
- Test isolation ratchet `tools/test_state_isolation.py` (29 suites, audit-hook instrument).
- Reviewer contract installer `25bf4c0`: Owner runs `python tools/install_reviewer_contract.py --install`.
- Rollover RESUMPTION reconciled `75276d2` (a real crossing is on the ledger).
- T10 night research `38441fc`, deployed to VPS (`~/pp-night`, Node 24.21.0 user-level,
  systemd user timer, linger enabled). Real pass: first eligible fire after 21:00 Madrid; read
  `~/.claude/state/night-research/reports/` on the VPS.
- T11 smoke mission `m-27f9f1ab9fb6` armed 19:57 in `Desktop\Cursor Projects\gsd-long-smoke`
  (phase 09 added), wall 22/24/20, max 3 cycles / 1.5 h. Certify: `python tools/gsd_epoch.py
  certify --mission m-27f9f1ab9fb6` (from the live checkout).
- T12: lessons + UCR-CIF stages `f6fe86b`; red team R1 -> `_logs/redteam/R1.md`, then R2.

## Next 3 actions
1. Read R1; fix any HIGH/CRITICAL; run R2 (adversarial on claims: manifest/docs vs code).
2. Certify the smoke mission's rotation; read the VPS night-research report.
3. Go-live merge + push; final handoff block (mission is PARTIAL on items 22/32/33 by owner state).

## Update ~20:35 Madrid (supersedes the lines above where they differ)
- LIVE + pushed `5037f36` (both branches; merged the other pane's quota fixes 9b4c64d/2f4e724).
- R1 done (0 crit/0 high), repaired in `58629ff`; isolation ratchet 38 suites.
- R2 (claims vs code) dispatched ~20:30 -> `_logs/redteam/R2.md` in pp-assim; if incomplete,
  re-dispatch ONE agent with the same brief. Fix every confirmed claim, go-live, push.
- T11 OWED: `m-27f9f1ab9fb6` cannot rotate (phase was uncommitted; fixed in smoke repo e6275c3),
  halts by budget ~21:27. Then from the live checkout: `python tools/gsd_mission.py arm --cwd
  "C:\Users\User\Desktop\Cursor Projects\gsd-long-smoke" --command /gsd-autonomous --max-cycles 3
  --max-hours 1.5 --wall 22,24,20`, later `python tools/gsd_epoch.py certify --mission <id>`.
- VPS: read `~/.claude/state/night-research/reports/` (kobicraft@204.168.166.63) after 21:05 Madrid.
- Owner step: `python tools/install_reviewer_contract.py --install` (HR-001).

## Start instruction
`git -C C:\Users\User\Apps\pp-assim log --oneline -12`, `python tools/test_assimilation_manifest.py`,
then action 1.
