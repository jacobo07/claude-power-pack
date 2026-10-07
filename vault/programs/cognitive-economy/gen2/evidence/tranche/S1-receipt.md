# S1 receipt -- S1 floor decomposition (tranche context-runtime-2)
verdict: PASS (deliverables 1-4 shipped). One class split is UNDECIDED, which the packet allows: the host-forced floor.
session: ef762cbd-6e41-4a41-a6cc-1b8c2695832e (laptop, worktree C:\Users\User\Apps\cr3-wt, branch tranche/cr3-workers)

## Premise
The packet's corrected premise holds: `wiki/tools/listing_floor_probe.py` existed and `tools/floor_regression_gate.py`
imports it (`load_lfp`). I extended the probe with `decompose`, `attribute`, `rank` and `--pair/--off-settings/--off-env/--out`.
I wrote no second probe. The window is read by the gate's own `read_window` + `classify`.

## Commands run (exit codes)
- `python tools/test_listing_floor_probe.py` -> exit 0, `FLOOR_PROBE_PASS=13/13`. Both poles: ON>OFF attributes 200
  CPP tokens; OFF missing / zero / absent row / unread window / still carrying hooks / exceeding ON -> UNDECIDED with
  cpp_added None (never 0); `--pair` with nothing switched off -> rc 2 and no session spawned.
- `python tools/test_floor_regression_gate.py` -> exit 0, `FLOOR_PASS=61/61 skipped=10 inconclusive=0` (no regression).
- `python wiki/tools/listing_floor_probe.py --label s1-floor --prompt "Reply with the single word OK." --pair
  --off-settings vault/programs/cognitive-economy/gen2/evidence/tranche/S1-off-settings.json --out
  vault/programs/cognitive-economy/gen2/evidence/tranche/S1-probe-pairs.jsonl` -> exit 0. The ON session ran 26.4 s at
  $0.72 and the OFF session 9.6 s at $0.68.
- `python s1_files.py 80072f9f-... a7e9e17f-...` -> exit 0. This is the read-only file-level listing; its script body is in S1-decomposition.md.

## Measured numbers (class minimal-prompt@claude-power-pack; all from the pair command unless noted)
- ON first-call tokens 105,454 (session 80072f9f-470a-4079-aba1-39cf61f52b3d).
- OFF (`disableAllHooks` via --settings) 102,403 (session a7e9e17f-124f-46d3-9207-eb22855a854e). The OFF window has 0 hook chars.
- CPP hooks added = 3,051 tokens, MEASURED. They come from 7,772 hook chars (SessionStart 5,526 + UserPromptSubmit 2,246,
  per the files command).
- host-forced = UNDECIDED. No kill switch removes the instruction files without editing ~/.claude config. 102,403 is
  therefore an upper bound on the host-forced floor: it still holds 133,536 chars of CPP instruction files.
- ON window chars: memory_global 39,809 · memory_project 40,434 · rules 36,831 · skill_listing 29,999 · agent_listing 25,996 ·
  other_instructions (MEMORY.md) 16,462 · harness_other 17,073 · hooks 7,772 · system_prompt 7,003.

## Biggest controllable item
`~/.claude/CLAUDE.md`, 39,809 chars: REJECTED. The packet forbids editing ~/.claude config, and HR-001 stops writes there.
Before: 39,809 (session 80072f9f). After: unchanged, because no edit was made. Owner decision.
The next in-repo candidate is the project CLAUDE.md HARD RULES mirror (21,230 chars). It is generated from
`vault/hard_rules/HARD_RULES.md` and includes the stubs HR-001..007, among them the test entry HR-002. The fix belongs in the compiler source.

## Files
wiki/tools/listing_floor_probe.py (extended), tools/test_listing_floor_probe.py (new),
tranche/S1-off-settings.json, S1-probe-pairs.jsonl, S1-floor-reference.json, S1-decomposition.md, S1-receipt.md.

COMMITS: 18c95053 936a4495 (this receipt lands in the next commit on tranche/cr3-workers)
