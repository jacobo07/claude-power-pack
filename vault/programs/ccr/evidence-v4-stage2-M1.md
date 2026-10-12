# Evidence v4 stage 2 -- M1: continuation capsule + resume-rent gate

Budget: E1 receipt names none -> 8,000 tokens = 13,675 chars (0.585 tok/char, B5). Over-budget items become `REF path sha256=...`, never truncated.
Owner extended: mission-card idea (tools/gsd_mission.py card, tools/mission_capsule.py) -- no persistent format added; tools/gsd_mission.py untouched.

## Commands
- `python -I tools/test_ccr_continuation.py` (V-CCRCONT-01..06, exit 0). Reds driven: a mutant with unbounded note + always-inline receipts fails V-02 and V-04.
- `python -I tools/ccr_continuation.py build --repo <path> --obligation <text> [--receipt <p>...] [--transcript <jsonl>]`
- `python -I tools/ccr_continuation.py rent --capsule <file>` (exit 1 if over budget)

## Elasticity (synthetic transcripts, 300-char assistant turns; build with no receipts)
| history | messages | transcript bytes | capsule bytes | est tokens |
|---|---|---|---|---|
| H | 100 | 19,140 | 564 | 330 |
| 2H | 200 | 38,290 | 564 | 330 |
| 4H | 400 | 76,690 | 565 | 331 |
| 8H | 800 | 153,490 | 565 | 331 |
Growth H->8H: +0.2 % (gate +5 %). Gate also holds with a receipt present (V-01).

## Real data
| case | capsule bytes | est tokens | predecessor last-call ctx (input+cache) | ratio |
|---|---|---|---|---|
| Madzia p4p2a13 (repo CursorProjects, obligation "next p4p2 attempt", receipt WU-E1) | 2,447 | 1,430 | 58,770 | 2.4 % |
| Lobby session 837d43a5 (largest KobiiCraft-Core-Files transcript, 99.9 MB; repo = power-pack, obligation "next lobby step") | 1,918 | 1,121 | 518,662 | 0.22 % |
Notes: Madzia dirty list is 40 names + "(+120 more)" (repo is very dirty) and dominates the bytes; the final note is a ref (worker last text >1,500 chars). Lobby capsule uses the power-pack repo for HEAD/dirty because the Lobby cwd is not a single repo; ctx comparison is the transcript's final call.
Caveat: capsule carries pointers and certified rows only; whether a successor works from 1.1-1.4k tokens instead of re-reading is not tested here (no model calls).
