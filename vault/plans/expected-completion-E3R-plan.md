status: APPROVED (Owner "y", 2026-10-08, pane c0338e7b) -- WU-0 executed; E3G split into E3G (guard) + E3C (forecast wiring, recalibration, promotion gate)
covers: [e3-recovery, d3-certification, receipt-closeout-path, call-drift-checkpoint, forecast-recalibration]

# E3 recovery + forecast-miss globalisation -- Master Plan

## Verified state (Reality Delta, 2026-10-08)
- Worktree C:\Users\User\Apps\pp-cost-collapse, branch cost-collapse/main, HEAD 3f2ff5c4 = E3-A sealed
  (gsd_mission.py, route_admission.py, test_dependent_admission.py; V-DEP 15/15 + 3 drills per its message).
- D3 dirty, uncommitted: tools/route_admission.py (CHALLENGER_AUTHORITATIVE False->True), tools/test_route_admission.py,
  tools/test_gsd_mission_admission.py. Also dirty: vault/progress.md, vault/knowledge_base/session_lessons.md.
  Untracked: vault/plans/expected-completion.RECEIPT-E3.md (fallback receipt), .pp-capabilities.
- Canonical receipt vault/specs/expected-completion.RECEIPT-E3.json: ABSENT (E1, E2 JSON receipts present).
- Mission m-7310776922c0: BLOCKED, terminal HALTED, owner session b35651f5. No live writer found.
- Three forecasts for one unit: spec ~25 calls / 4M; packet <=32 calls / 6M; route envelope calls 34. Actual 52.
- Guard hooks/session_budget_guard.js: calls > 1.5 x estimate = deny (52 > 51). Token warn -> checkpoint advice
  exists (E2); calls have NO checkpoint tier. Closeout allowance (4 calls) admits only vault/plans/*.md,
  memory/handoffs/*.md, RESUMPTION_FILE.md -- the packet's JSON receipt path is excluded by construction.
- Live guard (PP repo) hash != worktree guard hash; same ratio and closeout regex. Reconcile before E4 landing.

## Root causes
R1 CANONICAL_RECEIPT_BLOCKED: packet receipt path and guard closeout regex are two contracts that disagree. (code)
R2 HARD_BREAKER_AS_STEERING: call drift has only the airbag; tokens have warn->checkpoint, calls do not. (code)
R3 FORECAST_NOT_PRICING_KNOWN_REPAIR: packet itself declared 15+ known reds in section 2, inside a 3-section unit,
   with three inconsistent call forecasts. (files) Per-category split of the 52 calls: UNMEASURED until autopsy.
R4 RESERVE_TOO_SMALL_FOR_PROOF: closeout = 4 calls, enough for notes, not for proof/commit/receipt. (code)

## Work units (each a fresh packet worker; no parent transcript)
WU-0 (this pane, ~8 calls): snapshot D3 diff to a patch + sha256; write packets WU-E3R, WU-E3G; admit E3R with
  --depends-on m-7310776922c0 (expect ESCALATE if E3 metered over target; the Owner approval of this plan is the
  recorded escalation answer); arm E3R --supersedes m-7310776922c0. Then this pane ends (SAFE_TO_FORGET).
WU-E3R (frontier: D3 patch, 3 files, 7 suites, UNKNOWN invariant, receipt duty): run test_route_admission +
  test_gsd_mission_admission; repair only D3-causal reds; then test_route_admission_expected,
  test_gsd_mission_envelope, test_grammar_default, test_autopsy, test_running_control; rerun
  test_dependent_admission (15/15 + 3 drills); verify route-floors.json unchanged for slim-t2/gsd-executor
  calls_err; pathspec commit of the 3 files; mission_spend autopsy of b35651f5; write RECEIPT-E3.json FIRST after
  commit; last act: arm WU-E3G. Expected ~22 calls, band from measured E3 calls_err.
WU-E3G: (a) call-trajectory checkpoint at calls > estimate (deny stays 1.5x), earlier when no progress since last
  mark; (b) budget declares receipt_path from the packet, closeout admits exactly that path, reserve sized for
  receipt+checkpoint+handoff, execution still denied; (c) add E3 planned-vs-metered pair to calibration, confidence
  stays LOW (widen, not overfit); (d) Cognitive CI + one mutation drill per guarantee; canaries drift, reserve,
  promotion, unknown, dependent, rotation. Last act: arm E4.
WU-E4 (spec unit, re-forecast from recalibrated model, split if over target): reconcile live guard diff, land
  T1, T2, E1-E3, E3G on feature/knowledge-acquisition locally with rollback tag; D3 becomes ACTIVE only here;
  KV + UKDL + CBR. Then T2 reconciliation -> T3a/T3b per spec.

## WU-0 result (measured)
- D3 patch: vault/plans/expected-completion-E3-D3.patch, sha256 A354803EF7A459CF3045761A9A341D776A1EC296A3FEE62937CFC0E213527774,
  `git apply --check -R` exit 0.
- E3R mission m-bb14cd34e793 (supersedes m-7310776922c0). Dependent admission: ESCALATE -- E3 metered 7,622,341 >
  target 6,000,000 (+27% tokens; calls 52 vs 34 = +53%). Owner directive recorded; re-admitted on own forecast:
  ADMISSIBLE, lower 2,482,370 / expected 3,015,980 / safety 4,389,900 / hard 8,000,000, confidence LOW n=2.
- Finding: E2's EAC forecast is inert live -- gsd_mission.py:2778 calls _cost_breaker without usage. Owned by WU-E3C.
- Packets: WU-E3R, WU-E3G, WU-E3C, WU-E4 (+ route-E3R/E3G/E3C; route-E4 computed by E3C).

## Chain (each worker's last act; MID = own mission, NEXT = next unit letter)
python = C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe, cwd = this worktree:
1. `tools/gsd_mission.py arm --cwd C:\Users\User\Apps\pp-cost-collapse --command "Execute the work unit in the wu_packet"
   --workstream cost-collapse --no-launch --supersedes MID --authority "vault/plans/expected-completion-E3R-plan.md (Owner y 2026-10-08)"`
2. `tools/gsd_mission.py envelope --mission NEW --token-estimate <route target> --model sonnet --autocompact 250k
   --wu-packet vault/specs/packets/WU-NEXT.md`
3. `tools/gsd_mission.py admit --mission NEW --route vault/specs/packets/route-NEXT.json --depends-on MID`
   ADMISSIBLE/WATCHED -> step 4. ESCALATE -> do NOT re-admit without --depends-on; write the reason into your receipt
   and stop (that is an Owner decision; only the Owner's y on this plan answered E3's).
4. `tools/gsd_mission.py supervise --actions-only` (one pass; it launches the admitted PREPARED mission).
Order: E3R -> E3G -> E3C -> E4 -> T2 reconciliation -> T3a/T3b.

## Promotion gate
D3 = IMPLEMENTED_BUT_UNCERTIFIED until all 7 suites + dependent suite + drills pass in one run on one tree.
Commit = certified-in-worktree. ACTIVE = after E4 landing (champion stays live until then, per spec Rollback).
