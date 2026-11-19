# RESUMPTION — BCAP-2 absorption campaign (coordinator, laptop)

**Identity.** Owner 2026-11-19 (pane 2cf9ec6d, turn uuid b1db4459): "continua esa mision de absorcion hasta terminarlo
todo". Plan of record `vault/plans/bcap-2-absorption-2026-11-19.md`; workstream `.planning/workstreams/bcap2/`.

**Live.** GEX44 mission `m-b56eba15695b`, armed 2026-11-19 ~13:10Z, RUNNING (worker session ea6857df, epoch 1).
Worktree `/home/kobii/missions/bcap2/.claude/worktrees/bcap2`, branch `mission/bcap-2-run`, base `73c7f32c`
(pushed to the GEX44 bare repo as `mission/bcap-2`). Authority 120M (receipt owner_turn b1db4459), model sonnet,
max 40 cycles / 72 h, pivot autonomy on. Owner transcript copy: GEX44 `~/.claude/projects/laptop-pane-2cf9ec6d/`.

**Top-ups.** 3 x 40M, each only when the branch has commits outside `.planning/` since the last grant:
`python3 tools/gsd_mission.py authority --mission m-b56eba15695b --tokens <new total> --owner-turn
2cf9ec6d-2c19-44ba-870d-ff85597e0e7e:2026-11-19T12:57:50.218Z --reason "BCAP-2 top-up n/3"`.

**Check.** On GEX44 (LF no-BOM script via `cmd /c "ssh -o BatchMode=yes gex44 bash -s < file"`):
`python3 tools/gsd_mission.py status` row for m-b56eba15695b; `git -C <worktree> log --oneline`;
`.planning/workstreams/bcap2/STATE.md` phase log; `vault/programs/bcap-2/LAPTOP_STEPS.md`.

**Next.** Watch phase 1 (CPP-DBG-001) land; grant top-ups by the rule above; at closeout fetch `mission/bcap-2-run`,
review, merge (Owner-gated), then run LAPTOP_STEPS (incl. Ruflo laptop activation).
