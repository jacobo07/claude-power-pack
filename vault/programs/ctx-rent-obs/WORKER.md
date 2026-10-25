# ctx-rent-obs tranche 1: worker contract

You are the worker for goal `ctx-rent-obs` (Owner approval `approve ctx-rent-obs only`, 2026-10-25, packet sha256
c93018c6873bf73f3ead806426872a6712a87fcc6589a87eecbba8fdcdcd4411, authority 7,000,000, no top-ups).
The plan is `vault/plans/context-rent-observatory-2026-10-25.md` (commit 1be23133). Sections 2, 4, 5 and 6 are the
spec; do units W1-W4 of section 6 in order. Nothing outside section 6.

## First, before any edit
1. Bind this session: write `~/.claude/state/goal-binding/<your session id>.json` =
   `{"goal":"ctx-rent-obs","since_ts":"<now, UTC, %Y-%m-%dT%H:%M:%S>","source":"mission ctx-rent-obs W1-W4","pid":0}`.
2. Run `python tools/mission_spend.py goal-status --goal ctx-rent-obs` and `python tools/cpp_fsck.py`. Keep both outputs.

## Rules
- Shared tree: other sessions write here (over 1,200 dirty paths). Commit ONLY by pathspec, with `git` at
  `C:\Program Files\Git\cmd\git.exe`; never stash, reset, checkout or add -A. After each commit verify
  `git log -1 --format=%s`.
- Do not edit `ccr_*`, `mods/`, `tools/gsd_mission.py`, settings.json or `vault/knowledge_base/ukdl-universal.md`.
- Every test change is red first: show it failing, then passing.
- UNKNOWN is never zero and never PASS. Do not invent a number; write UNKNOWN and why.
- Stop-loss: a unit over 2x its P80 (section 8) stops the run; write why in `vault/programs/ctx-rent-obs/STATUS.md`.

## W1 closure (do the ledger moves LAST, after the receipts are committed)
1. `vault/programs/ctx-rent-a2/TAKEOVER.json`: one object per slice A-L, with the fields original_programme,
   obligation, intent, implementation_owner, evidence_owner, implementation_state, evidence_state, transfer_basis
   (file:line or commit), residual_proof, open_measurement, old_path_status, effective_date, invalidators. Take the
   values from plan section 2. Re-verify every cited file:line first.
2. `vault/programs/ctx-rent-a2/CLOSURE.md`: class DELIVERED_WITH_TRANSFERRED_OBLIGATIONS, the authority lineage
   (plan section 1), the TAKEOVER.json sha256.
3. Rewrite `vault/programs/ctx-rent-a2/RESUMPTION_FILE.md` as a sealed record: closure class, no NEXT action,
   fingerprint = CLOSURE commit + TAKEOVER.json sha256.
4. Prepend to `vault/programs/econ-succession/RESUMPTION_FILE.md` one STALE banner: S2/S3 af7ec647 and S4 44396331
   landed after its anchor 4e9953a7; its "do S1" line is stale; NEXT is its owner's decision. Change nothing else there.
5. `tools/cpp_fsck.py` stale_resumption: also report a FINDING when a RESUMPTION_FILE's next-actions block names an
   obligation that a TAKEOVER.json beside it marks TRANSFERRED or SUPERSEDED. Red-first test in `tools/test_cpp_fsck.py`.
6. `tools/econ_plane.py` owner raise: the programme row source carries the approving transcript entry uuid when one is
   known. Red-first test in that module's existing test file (find it with Grep).
7. Ledger, last:
   - book pane 36d35fab-bc56-4c68-bccc-d4487d7db2c2 on ctx-rent-a2 with mission_spend goal-settle and its measured
     option, value = `session_tokens(transcript, since_iso="2026-10-23T15:20:10")["tokens"]` read at that moment;
   - then lower the ctx-rent-a2 programme to settled + open (a lowering; record the released amount in CLOSURE.md).
   Do not use the released amount for anything.

## W2 baseline B1
- Commit the census JSON of slice B. If the scratchpad copy is gone, rerun `tools/context_floor_census.py` on sessions
  36d35fab 5cadebe8 and commit that output.
- Three fresh probes, same prompt, same model: `tools/floor_regression_gate.py` probe mode (it appends a row to
  `wiki/tools/listing_floor_probe.results.jsonl`; set env CPP_FLOOR_PROBE_RESULTS to a file under
  `vault/programs/ctx-rent-obs/b1/` instead).
- Write `vault/programs/ctx-rent-obs/B1.json` and `B1.md` per plan section 4: the claim types, the N=3 spread, every
  unobservable field as UNKNOWN.

## W3 certification canary C1
1. Commit `vault/programs/ctx-rent-obs/contracts/C1.json` BEFORE reading any data. It names: the CCR claim (M1 trivial
   subagent 47,591 -> 15,571 with instructions and skill_listing dropped, `vault/plans/ccr-mods-backend-2026-10-11.md`
   lines 35-36), the instrument (a Context Rent tool, not a ccr_* tool), the population, the denominator, and the verdict
   rule (CERTIFIED / REFUTED / UNMEASURABLE).
2. Measure. If the raw transcripts are gone and a fresh matched pair needs a settings or plugin change, the verdict is
   UNMEASURABLE: say so and do not change settings.
3. Commit `contracts/C1.verdict.json`. The contract commit must precede the data commit.

## W4 Context CI drill
- If `tools/test_floor_regression_gate.py` already drives an injected resident addition to exit 1, cite the gate name
  and output in STATUS.md and stop.
- Otherwise add one such drill, red first.

## Done
- Write `vault/programs/ctx-rent-obs/STATUS.md`: each unit's done-gate (plan section 6) with the real command output,
  and the goal-status of ctx-rent-obs and ctx-rent-a2.
- Then stop. Tranche 2 needs a new Owner approval.
