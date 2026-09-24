# Mission Continuity — resumption contract (in flight)

**Read this first; it is self-contained.** Spec: `vault/specs/mission-continuity.md` (APPROVED
2026-09-23, autonomous W0→W10). Evidence: `.planning/mission-continuity/W0-EVIDENCE.md`.

## Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`,
worktree = repo root. Other panes commit here constantly: re-read HEAD before every commit,
commit by pathspec, check diff hunk headers (UKDL is edited by others concurrently).

## Owner decisions (do not re-litigate)
1. **Ralph is the primary path of /cpp-gsd-long**: at the wall a FRESH `claude --bg` session
   continues; native autocompact is only a safety net (`--autocompact 600k`). Reason: RAM.
2. Probe workers run `acceptEdits`, scratch only. REAL mission workers run **`auto`**
   (Owner, 2026-09-24; `arm --permission-mode` default since `18c7299`).
3. M6 runs NOW (Owner: "Sí, ahora").

## UPDATE 2026-09-24 09:5x — review closed, M6 in flight
`3c2116f` closes the adversarial review (H1–H3, M1–M3; L1 stale-lock race = debt; report
in scratchpad `ADVERSARIAL-REVIEW.md`, summary in W0-EVIDENCE). `18c7299` auto default.
Gates: test_gsd_mission 92/92, watchdog 12/12, hub 8/8, wall 7/7, GSDLR 99/99, GSDAC 26/26.
W8 closed HALTED on budget: 41 rows, 0 dupes, writers disjoint (E25).
**M6**: mission `m-7f6d988e3c93`, cwd `C:\Users\User\Desktop\Cursor Projects\gsd-long-smoke`
(trusted canary, 1/8 phases at HEAD `4f09667`, snapshot in scratchpad `m6-smoke-snapshot`),
worker 1 `f3c0b67e`, budget 5 iterations / 8 h. Proven when: ≥ 2 relays, each successor
continues the roadmap (phase count strictly increases, no phase redone), `git log` shows
commits from ≥ 3 workers, and the mission ends COMPLETED or HALTED-on-budget — never
two workers at once. Judge with `python tools/gsd_mission.py status`, the ledger rows for
the mission, `gsd_status`, and the smoke repo's `git log`.

## SEALED (commits, all pathspec-scoped)
`f3b9896` mission record/CAS/liveness/relay core · `1f445e0` watchdog asks hand-off at the
wall · `204c486` SessionStart ack + card (hub) · `256af91` sweep supervises out of band ·
`cb6356f` tool-free hand-off (`HANDOFF NOTE:`), relay budget · `758a3a0` adopt on host witness
· `9355f8e` variadic-argv prompt fix + name-anchored id parse · `46739ca` halt stops workers
(orphan reaping) + card rendered at relay time.
Gates: `tools/test_gsd_mission.py` 74/74 · `tools/test_mission_watchdog.py` 11/11 ·
`node tools/test_hub_mission_start.js` 8/8 · regression GSDAC 26/26, GSDLR 99/99, OVLY 4/4.
Mutations driven (all caught, SHA-256 restores): 6 core + 2 watchdog + 2 note/budget + 1 adopt.

## UPDATE 2026-09-24 00:5x — W8 PROVEN LIVE (see W0-EVIDENCE E18–E24, CERTIFICATION §11)
Later commits: `fdf32fc` card via `--append-system-prompt` · `4616039` mid-turn wall
(PostToolUse, `hooks/mission_wall.js`, registered in the LIVE dispatcher and the repo mirror)
· `9ea9a92` Stop does not re-ask · `567b1f0` GSD asked before replace too.
Relay proven: worker ef5fe657 handed off at f23 (mid-turn wall), successor 88525fc9 continued
at f24 as sole writer. Remaining: M6 (real /gsd-autonomous, needs Owner's permission mode).

## (history) W8 clean E2E (attempt 3)
Mission `m-7cebf2b33bf3`, worker 1 `ef5fe657`, armed 00:10:27Z 2026-09-24, cwd
`C:\Users\User\AppData\Local\Temp` (trusted), command `/mc-task`
(`Temp\.claude\commands\mc-task.md`), sandbox `<scratchpad>\mc-w0\p1repo` (60 files,
progress.txt reset to empty). max-cycles 2. Expected: ack or adopt → ~f33 crosses 40 % →
`handoff_asked` → worker ends with `HANDOFF NOTE:` → sweep relays (stop, pid gone, launch e2
with card) → e2 finishes f60 → turn ends → budget → HALTED.
Judge with `scratchpad\mc-w0\verify.py` (in order, 0 dupes, 0 wrong) and
`scratchpad\mc-w0\writers.py <id> <id>` (write attribution). Attempts 1–2 are recorded
failures (prompt swallowed; orphan contamination) — see commit messages.

## Known debt (not caused here, recorded)
ACPS daemon suite flaky 29–32/38 at HEAD too · SessionStart hub ~9 s vs 10 s budget on this
host · synthetic id `not-a-mission-0000` left in power_beacon/session_snapshot/cpc_os_registry
(last-writer-wins, self-heals) · the 9 legacy v2 markers are still NO_CROSSINGS/stalled.

## Next 3 actions
1. Watch W8: `python tools/gsd_mission.py status`; ledger rows for `m-7cebf2b33bf3`.
2. On success: W0-EVIDENCE E18+ rows, certification addendum, commit
   `commands/cpp-gsd-long.md` (v3 section already written, uncommitted) + UKDL hunk.
3. Ask the Owner the worker permission-mode question; then a real GSD run (`/gsd-autonomous`).
