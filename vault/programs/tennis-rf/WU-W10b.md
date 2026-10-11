# WU-W10b -- Tennis capsule, part 2: a Tennis judge and custody that do not disturb Resort (zero jobs)

Common brief: `PROGRAMME.md`. Prerequisite: `WU-W10a-receipt.md` (profile + local Tennis capsule). Blockers 3-5 of
`WU-W3b-receipt.md` are yours.

Facts (verify with one read each):
- `match.py:189` reads the module-global `K.DOL` (Resort retail). It is reached via candidate.judge / l0_row
  (L0_PATH = main_L0.jsonl). No Tennis L0 exists.
- `F\CURRENT_CAPSULE.json` is a single shared pointer (custody.current_capsule; stage.py:416/440/1112/1155). The W1
  guard refuses a send unless it equals the sent capsule. Resort and the cp50-c2 jobs use it too.
- Hard constraint: no GEX44 live-install change, and goal cp50-c2 is not this programme's.

Steps:
1. Judge: thread the W10a profile into match.py / candidate.judge, so a Tennis judge reads the Tennis DOL words and
   Tennis DTK operands. If the judge needs an L0 row, build the minimal Tennis L0 for the capsule's functions from
   the Tennis split (read-only on SportsPackEP), never by editing main_L0.jsonl.
2. Local judge control BEFORE any job (RED first, gates in test_tennis_profile.py or a sibling):
   positive = W3b donor source object vs its Tennis target is MATCH; negative = the same pair with one flipped word
   is not MATCH. Then the Resort judge control: a known Resort MATCH still matches under the default profile.
3. Custody: choose how a Tennis send satisfies CURRENT_CAPSULE without disturbing Resort or cp50-c2 jobs, and
   without changing the GEX44 live install. Read how the GEX44-side runner/custody resolves the F root BEFORE
   choosing. Options to weigh: a per-programme F root, if the runner already accepts one per job; or a bounded
   time-slice switch with a refusal when any non-Tennis job is in flight, restoring the pointer afterwards and
   verifying by reading it back. Write the choice and the evidence into the receipt. If every safe option needs a
   GEX44 live-install change, stop with `Status: BLOCKED_HUMAN` naming the exact change.
4. Re-run the suites W10a listed; Resort must stay exactly as green as before. Mutation drill: the Tennis judge reads
   the Resort DOL; the in-flight refusal is ignored. Each must go RED.
Zero GEX44 jobs, zero local compiles. Continuation rule as in PROGRAMME.md step 4 (id W10b-b).
Receipt (write it to vault/programs/tennis-rf/WU-W10b-receipt.md, Status line per PROGRAMME.md step 3; the chain
reads only that file): commits, judge-control results, the custody route and why, suite counts, drill.
