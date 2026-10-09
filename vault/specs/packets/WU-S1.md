done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_mission_steward.py
work_tree: C:\Users\User\Apps\pp-gsdx-factory-2
receipt: vault/specs/gsdx-factory.RECEIPT-S1.json

# WU-S1 -- Mission steward: a stopped worker is settled, salvaged and handed on, deterministically

Plan (binding, Owner "y"): LIVE tree `C:\Users\User\.claude\skills\claude-power-pack\vault\plans\gsdx-steward-recovery-plan.md`
sections 2-4 (units S1, R0). Owner decision 2026-10-09 ("b"): S1 is a NEW module `tools/mission_steward.py`; the only edit to
`tools/gsd_mission.py` is ONE guarded call at the end of `supervise()`. Fresh worker; no Agents, no GSD commands; never push;
never Set-Location / cd (git -C and absolute paths only).

## 0. Facts (verified 2026-10-09 by the coordinator; re-check before relying on one)
- This tree = branch `gsdx-factory/v2` on top of cost-collapse head 42ac887c. Goal `gsdx-factory-2` binds this root.
- `modules/provider_routing/ledger.py` `GoalLedger`: journal ops `cap`, `reserve` (kinds `lease` | `agent` | `final`),
  `leak`, `settle {sid, measured, closes}`. `_gfold` keeps `marks[sid] = max(...)`; a hold is open while RESERVED/LEAKED and
  not listed in a settle's `closes`. `renew()` settles THEN reserves a new lease (or a `final` hold on refusal): there is no
  way to close a finished sid without opening something new. Measured: R0 left a phantom 150,000 `final` hold on goal
  `gsdx-factory` (`goal_renew` maps `--per-call 0` to the 150,000 default); S4's two probe sids left 838,615 of open
  lease on `gsdx-factory-2` against 130,061 real.
- `tools/mission_spend.py`: `find_transcript(sid, projects_root())`, `session_tokens(path)` -> {tokens, calls (tool_use
  blocks), context}; `_goal_ledger(goal)`, `read_index()`; `goal-declare --owner` asks for the goal id on a TTY and refuses
  when stdin is not a TTY (copy that pattern).
- `tools/gsd_mission.py`: states PREPARED LAUNCHING RUNNING HANDOFF BLOCKED + `TERMINAL` {COMPLETED HALTED ORPHANED}; `LIVE == "ALIVE"`; `_scan()`, `load()`,
  `transition(mid, expect_epoch=, expect_state=, event=, now=, **changes)` (CAS; fields without `state` keep the state;
  raises `CasConflict`), `liveness(owner, sessions, pid_alive)[0] == LIVE`, `packet_receipt_path(rec)` (packet `receipt:`
  line resolved inside `work_tree:`), `supervise()` ends `return unreadable + out` (~line 3210). Records carry `cwd`,
  `goal` (GGMC dict {repo, workstream, unit} -- NOT the spend-goal id), `wu_packet` {path, sha256}, `owner` {session_id},
  `owner_hold`, `admission`, `updated_at`. Map a mission to its SPEND goal by `cwd` against `read_index()` roots
  (lower-cased paths); no binding -> the steward settles nothing for it (row says why).
- The LIVE sweep runs the live tree's gsd_mission.py, which lacks `packet_receipt_path`: nothing here goes live until the
  branch lands. Do not touch the live tree.
- Windows: PowerShell tool; git `C:\Program Files\Git\cmd\git.exe`; python = done_gate path; `$env:PYTHONIOENCODING='utf-8'`;
  test output to a log file, read only `_PASS=` and FAIL lines.

## 1. Ledger (ledger.py + mission_spend.py)
- `GoalLedger.settle_stopped(sid, measured, reason)`: append `settle {sid, measured, closes, stopped: true, reason}` where
  `closes` = EVERY RESERVED/LEAKED hold of that sid, any kind. Never reserves. Idempotent: a second call books nothing new.
- `GoalLedger.correct(sid, measured, reason, authority)`: new op `correct`; `_gfold` sets `marks[sid] = measured` (may
  LOWER it; later settles watermark from there). The base SpendLedger fold must keep ignoring it.
- CLI `goal-settle --goal --session [--measured N]`: default `measured` = transcript processed tokens; no transcript and no
  `--measured` -> refuse (exit 3), nothing written. CLI `goal-correct --goal --session --measured --reason --owner`: TTY-only,
  same refusal shape as `goal-declare --owner`.

## 2. Steward (`tools/mission_steward.py`, deterministic, zero model)
`steward_pass(missions, now, *, sessions, pid_alive, dry_run=False, ledger_for=..., transcript_for=...) -> list[row]`.
Every effect is recorded on the mission as `steward: {...}` via `transition` (state unchanged), and re-read before acting,
so a repeated or restarted pass does nothing twice. Kill switch `CPP_MISSION_STEWARD=off` -> no rows, no effects.
- R1 stopped worker: state HALTED or BLOCKED, owner not LIVE, `wu_packet` + `goal` set, canonical receipt absent ->
  (a) `settle_stopped` the owner sid at transcript-measured tokens (transcript missing -> row `UNKNOWN`, NOTHING settled);
  (b) partial receipt `<receipt>.partial.json` (never the canonical path): git log in work_tree since admission time,
  transcript tokens, tool calls, model calls deduped by message.id, salvage list;
  (c) salvage: every tool_use whose tool_result is an error containing `SESSION BUDGET BREAKER` -> its input JSON to
  `vault/specs/salvage/<mission_id>/<tool_use_id>.json` in work_tree;
  (d) residual packet `<packet>.residual.md` = original packet + `## Residual` naming partial receipt, RESUMPTION_FILE,
  salvage. PROPOSE ONLY: the steward never arms, admits or launches (that is spend authority).
- R2 forgotten goal: a goal in `read_index()` with remaining > 0 and no non-terminal, non-held mission updated within
  30 min -> one incident row per goal per 24 h in `<state_dir>/steward-incidents.jsonl`. An `owner_hold` mission is
  deliberate, never forgotten.
- R3 unarmed successor: a canonical receipt or packet that names a successor packet with no mission whose `wu_packet`
  is it -> row `successor_unarmed` (proposal only).
- Hook: end of `supervise()`, `if not dry_run:` extend `out` with `mission_steward.steward_pass(...)` inside try/except;
  any exception becomes ONE row `{action: "steward_error", error}`, never a failed sweep.

## 3. Gates (`tools/test_mission_steward.py`, hermetic temp state + temp ledger, BOTH poles; print `STEWARD_PASS=n/n`)
V-STEWARD-SETTLE-CLOSES-ALL (lease + final closed, used = measured) · -SETTLE-IDEMPOTENT · -NO-TRANSCRIPT-UNKNOWN (no
settle row written) · -LIVE-OWNER-UNTOUCHED · -CANONICAL-RECEIPT-UNTOUCHED (receipt present -> no action; partial never
overwrites it) · -SALVAGE (refused input extracted byte-exact) · -DUP-PASS-ONE-EFFECT · -RESTART-MIDWAY (steward field
half-written -> completes once) · -NEVER-ARMS (mission count unchanged) · -HOLD-NOT-FORGOTTEN · -FORGOTTEN-ONCE-PER-24H ·
-KILL-SWITCH · -CORRECT-LOWERS · -CORRECT-NEEDS-TTY · -CLI-SETTLE-REFUSES-BLIND · -SUPERVISE-ERROR-ISOLATED · a control
where nothing qualifies -> zero effects. Regression: `tools/test_goal_budget_admission.py` and
`tools/test_gsd_mission_admission.py` still pass (record their counts; a pre-existing red is recorded, not fixed).
Mutation drills (`tools/mutation_drill.py`, isolated copy): settle_stopped closes only leases -> -SETTLE-CLOSES-ALL red;
steward skips the re-read -> -DUP-PASS-ONE-EFFECT red.

## 4. Close
Pathspec commits in this tree (ledger+CLI, steward+hook, test). Receipt: gate lines, regression counts, drill results,
shas, metered calls, attribution (plan section 2 vocabulary), avoidable calls. Update `RESUMPTION_FILE.md` top section
(S1 done; next S2 on slim-t2; the live landing of S1 is a coordinator step). Do not arm anything.

## Budget
At most 34 model calls (route-S1.json). On checkpoint: write the receipt and stop. End with `HANDOFF NOTE:` and one line.
