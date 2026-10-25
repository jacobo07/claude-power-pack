# Unit W3b — stage tag over mission authority

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PATH). Python is
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.

## Goal
Owner authority on a mission is one undifferentiated ceiling. The programme needs stages: each Owner act opens
or resizes a named stage, the stage tag goes on the receipt and the ledger row, and moving to the NEXT stage is
refused without an Owner turn. `tools/gsd_mission.py` already owns all of this. Use `set_authority(...)`
(around line 2580): receipts, owner-turn verification, replay no-op, and the `recognize_overrun` path for an
in-flight overrun. Use the `authority` CLI too (around lines 6735-6880). Extend them, and add no new owner.

## Change (tools/gsd_mission.py only, plus one new test file)
1. `set_authority(..., stage: str | None = None, ...)`. Validate it with `re.fullmatch(r"[A-Za-z0-9._-]{1,40}")`
   and raise MissionError otherwise. The current stage is the `stage` of the last receipt in
   `rec["authority_receipts"]` (None when absent).
2. Opening a different stage (stage given and != current stage) with `owner_turn` None raises
   MissionError("refused: stage <new> opens after <cur>; a new stage needs --owner-turn ..."). Resizing the SAME
   stage keeps today's behaviour exactly. With `stage=None`, the behaviour is unchanged, the receipt carries the
   current stage, and every existing test stays green.
3. The receipt entry gets `"stage": <effective stage>` and `"stage_opened": <bool>`. The ledger row gets the same
   through the existing `ledger_extra={"receipt": entry}`. The replay rule changes so that the same owner turn
   with the same figure but a different stage is REFUSED, not treated as an idempotent no-op.
4. An in-flight overrun stays as it is. When `recognize_overrun` admits a ceiling at or below live spend, the
   receipt records it. Do not loosen that check.
5. CLI: `authority --stage <tag>` passed through. The `AUTHORITY SET` line prints `stage=<tag>`.

## Test (new file tools/test_w3_stage_authority.py, V-* gate style like tools/test_wake_progress.py)
Use the module's own test seams: read how tools/test_gsd_mission.py builds a mission in a temp state dir and fakes
the owner-turn finder (`finder=`) and spend (`spent_fn=`). Copy that setup; do not invent a new one.
Print `W3B_PASS=n/n`, exit 0 only if all pass:
- V-W3B-OPEN-NEEDS-OWNER: opening stage "s2" after "s1" with no owner_turn raises, and the record is unchanged.
- V-W3B-OPEN-WITH-OWNER: the same act with a verified owner turn succeeds, and the last receipt has stage "s2" with
  stage_opened True.
- V-W3B-RESIZE-SAME-STAGE: a resize within "s1" behaves as before.
- V-W3B-REPLAY-OTHER-STAGE: the same owner turn, the same figure and another stage are refused.
- V-W3B-OVERRUN-RECORDED: a ceiling below live spend is refused, and with recognize_overrun it is admitted, with
  receipt stage and recognize_overrun True.
- V-W3B-MUTATION-RED: show that your OPEN-NEEDS-OWNER check fails against a set_authority that skips the stage
  rule (monkeypatched mutant).

## Done
- `python tools/test_w3_stage_authority.py` exit 0 and `python tools/test_gsd_mission.py` exit 0.
- Commit with a pathspec: `git commit -m "<msg>" -- tools/gsd_mission.py tools/test_w3_stage_authority.py`.
- Receipt `vault/programs/factory-tranche-a/W3b-receipt.md`: what changed (file:line), the test counts, and the
  line `COMMITS: <hash>`, where the hash is reachable from HEAD.
