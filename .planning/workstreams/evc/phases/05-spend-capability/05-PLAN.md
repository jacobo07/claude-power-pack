# Phase 5: Spend capability and precise lease states -- compact plan

Disposition SHRINK. An Owner hold, SUSPENDED or cost-breaker trip writes the live worker's
`session-budget-<sid>.json` with stop=1 (the U0 mechanism) so the guard refuses its next gated call.
RELAY_HELD is never shown as paused. The envelope guard counts subagent transcripts.
All gates hermetic (temp dirs, injected state). No live canary here (Phase 9).

Shared test file: `tools/test_evc_spend_capability.py` (new; plain-assert runner like `tools/test_gsd_mission_owner_hold.py`).
Python: `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'` with `$env:PYTHONIOENCODING='utf-8'`.
Hermetic state: every test points `mission_spend.state_dir` (monkeypatch) and the mission store at a `tempfile.mkdtemp()`.
Anchors are line numbers at commit 417229aa; re-find the `def` by Grep if they moved.

### Task 1: Hold and breaker trip write the worker deny file; release restores it

Files: `tools/gsd_mission.py` (set_owner_hold 1281, _cost_breaker trip site 1443, release_owner_hold 1465),
`tools/mission_spend.py` (budget_path 515, declare 552), `tools/test_evc_spend_capability.py`.

Gates first (write, run, see RED):
- V-EVC-05-01 hold denies: mission with `owner.session_id=S` and a declared budget file (stop=900000). Call
  `set_owner_hold`. RED input: before the code the file still has stop=900000. GREEN: file has `stop==1`, and
  `deny_marker` field names the mission id and the hold reason.
- V-EVC-05-02 breaker trip denies: drive `_cost_breaker` with a verdict whose `trip` is set (inject `usage_truth`
  and spent). RED: stop unchanged. GREEN: stop==1 for the owner sid.
- V-EVC-05-03 release restores: after V-01, `release_owner_hold` puts back the original stop/target/warn
  (saved under `restore` in the file). RED: stop stays 1.
- V-EVC-05-04 positive control: a mission with no `owner.session_id` (not yet launched) hold succeeds, writes no file,
  raises nothing; an invalid sid (fails `_SID_RE`) is recorded in the ledger as `deny_write_skipped`, hold still set.
- V-EVC-05-05 SUSPENDED: the transition into SUSPENDED (grep `SUSPENDED` in transition callers) writes the same deny.

Steps:
1. In `mission_spend.py` add `deny_budget(sid, why) -> Path|None`: read the existing budget file (if any),
   keep its original `target/warn/stop` under `restore`, write `stop=1, target=1, warn=1, deny_marker=why`
   atomically (same tmp + `os.replace` as `declare` 566-570). If no file exists, create via `declare(sid,1,1,1,extra=...)`.
2. Add `restore_budget(sid) -> bool`: when `restore` exists, rewrite with those values and drop `deny_marker`; else no-op.
3. In `set_owner_hold` (after the `transition` at 1297, not before: write only when the CAS won) call
   `deny_budget(rec["owner"]["session_id"], f"owner hold: {reason}")`. Wrap in try/except, ledger `deny_write_failed`
   (fail visible, hold still stands).
4. `_cost_breaker` reaches `set_owner_hold` at 1443, so it is covered; add the V-02 assertion to prove it, no extra code.
5. In `release_owner_hold` (after the transition at 1472) call `restore_budget`.
6. SUSPENDED entry: call `deny_budget` where the mission enters SUSPENDED; `restore_budget` on leaving it.

Verify:
- `python tools\test_evc_spend_capability.py`
- `python tools\test_gsd_mission_owner_hold.py`, `python tools\test_mission_spend.py`, `python tools\test_gsd_mission.py`

### Task 2: spend_state() -- RELAY_HELD is never displayed as paused

Files: `tools/gsd_mission.py` (renewal_refusal hold display 2218, relay_held events 3362 and 3410, status_surface 4157),
`tools/mission_surface.py` (classify, only if the label lives there), `tools/test_evc_spend_capability.py`.

Gates first:
- V-EVC-05-06 pure function `spend_state(rec) -> str` returns one of `RUNNING, DRAINING, OWNER_HELD, BREAKER_TRIPPED,
  SUSPENDED, RELAY_HELD, TERMINAL`. Table-driven over six record fixtures. RED: `AttributeError` (function absent).
- V-EVC-05-07 relay hold: record with `gsd_hold` set and no `owner_hold` -> `RELAY_HELD`; assert the label
  is not in `{"OWNER_HELD","SUSPENDED","PAUSED"}`. RED input: same record through today's `status_surface`
  row, whose text says paused (capture that string first as the RED evidence).
- V-EVC-05-08 precedence: owner_hold + gsd_hold together -> `OWNER_HELD`; breaker trip text (`owner_hold.measured` present
  and reason starts with the breaker prefix) -> `BREAKER_TRIPPED`. Positive control: a plain RUNNING record stays `RUNNING`.
- V-EVC-05-09 DRAINING: `lease_state=="DRAINING"` with no hold -> `DRAINING` (the 1451 edge stays unchanged).

Steps:
1. Add `spend_state(rec)` next to `status_surface`; ordered checks: TERMINAL, SUSPENDED, BREAKER_TRIPPED, OWNER_HELD,
   RELAY_HELD, DRAINING, RUNNING. Pure, no I/O.
2. `status_surface` (4157): add `spend_state` to each output row (line 4166 dict). Do not change existing keys.
3. Where the relay hold is shown (3362 event text, 3410 `row["held"]`), keep the event names but make `row` carry
   `spend_state="RELAY_HELD"`; remove any "paused" wording for it.
4. Leave `renewal_refusal` 2218 text; add `spend_state` only to its caller's message if V-07 needs it.

Verify:
- `python tools\test_evc_spend_capability.py`
- `python tools\test_gsd_mission_surface.py`, `python tools\test_gsd_mission_sleep.py`, `python tools\test_gsd_mission_chain.py`

### Task 3: The envelope guard counts subagent transcripts

Files: `hooks/session_budget_guard.js` (advance 58-98, measureGoal 310-316 as the model, judge 113),
`tools/mission_spend.py` (session_tokens 521-549, the Python mirror), `tools/test_evc_spend_capability.py`.

Context: the goal path (`measureGoal` 310) already folds `<transcript-dir>/<session>/subagents/*.jsonl`; the
session-envelope path (`advance`) reads only the main transcript, so a worker that spawns subagents escapes its stop.

Gates first:
- V-EVC-05-10 JS parity: temp dir with main transcript (200K tokens) and `<sid>/subagents/a.jsonl` (900K tokens, distinct
  message ids); budget stop=1,000,000. Run `node hooks/session_budget_guard.js` with the PreToolUse event on stdin
  and the state dir env the guard reads (see its top 20 lines). RED: no deny (main alone = 200K). GREEN: deny, reason
  names `1,100,000`.
- V-EVC-05-11 dedupe: the same message id in main and subagent file counts once. RED/positive control: total stays 1,100,000.
- V-EVC-05-12 Python mirror: `session_tokens(main)` with a subagents dir returns the sum; RED today returns 200000.
- V-EVC-05-13 offset safety: a second call after appending to a subagent file adds only the new lines (per-file offsets
  kept in the state under `sub_offsets`); positive control: unchanged files add 0.

Steps:
1. In the guard, extend the state (`fresh`) with `sub_offsets: {}`; factor `advance(st, transcript)` so it can fold a file
   with its own offset key. After folding main, list `subagents/*.jsonl` as `measureGoal` does (312-315) and fold each,
   sharing `st.ids` for dedupe (MAX_IDS cap 97 unchanged).
2. Calls from subagents count into `st.calls`; `progress_at` only moves on main-transcript progress tools.
3. Mirror in `mission_spend.session_tokens`: add subagent files to the total, same dedupe set; keep the return keys.
4. A missing or unreadable subagents dir changes nothing (fail-open as in 314).

Verify:
- `python tools\test_evc_spend_capability.py`
- `python tools\test_session_budget_admission.py`, `python tools\test_mission_spend.py`, `python tools\test_gsd_mission_envelope.py`
- `node --check hooks\session_budget_guard.js`
