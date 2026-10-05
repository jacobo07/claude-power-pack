---
phase: 02-e1-runner-with-the-stopping-contract-as-tested-code
plan: 02
requirements: [E1-RUNNER]
status: complete (uncommitted; the orchestrator commits after review)
files_modified:
  - vault/programs/cognitive-economy/e1/e1_contract.py
  - vault/programs/cognitive-economy/e1/test_e1_runner.py
---

# 02-02 Summary: the ADDENDUM-E1 stopping contract as pure, replayable code

## What was built

- `e1_contract.py` (still stdlib-only: its one import is `sys`; it opens no file and uses no subprocess or clock):
  - Primitives: `contract_order` (rule bytes descending; refuses >11 tasks, a non-E1 rule, a repeated id or rule,
    equal bytes), `arm_order` (A,B on even positions, B,A on odd), `decide` (the clause-4 table, booleans only),
    `positive_control_ok` (B <= A - 15,000; None is False), `harm_fired` (>= 4 STAYS in the first 8 valid pairs),
    `spend_reached` (kept for the record only), `spend_stop_due(spent, max_seen)` (the predictive clause-6 gate
    from the ORCHESTRATOR AMENDMENT).
  - State machine: `replay(order, records)` recomputes validity, pass and spend from the raw fields with
    run_valid / task_pass / run_spend. It refuses impossible record sets incrementally: unknown task, bad arm,
    attempt outside 1..2, run_id mismatch, duplicate, a run on a terminal task, a run while an earlier task is
    PENDING, the second arm before the first is valid, any other out-of-sequence attempt. `next_action` uses the
    fixed order HALTED, RECONCILE, POSITIVE_CONTROL_STOP, HARM_STOP, ALL_DECIDED, SPEND_UNMEASURED, SPEND_STOP,
    RUN. `final_decisions`, `pair_record` and `stop_record` (with over_cap_by, cap_reached and max_seen) produce
    the records.
- `test_e1_runner.py`: 19 new gates (6 primitive, 13 state-machine), all inserted before V-E1-NO-MODEL-END. Helpers:
  `mk_order`, `mk_run`, `pair`, `noinfo`, `pairs`, `nxt`, and `simulate(order, script, limit=60)`, the pure twin
  of 02-04's drive(); hitting its limit raises.

## Verify output

`python3 vault/programs/cognitive-economy/e1/test_e1_runner.py V-E1-ORDER V-E1-ALTERNATION V-E1-DECIDE V-E1-POSCTL-FN V-E1-HARM-FN V-E1-SPEND-FN`
ended `E1_PASS=8/8` with exit 0. Full run, exit 0 (02-01 gates unchanged and still PASS):

```
PASS V-E1-ORDER order_ok=True first=J-gceg_product_page refused_with_reason={'twelve': True, 'r2_rule': True, 'same_rule': True, 'same_bytes': True, 'not_allowed': True}
PASS V-E1-POSCTL-FN 85000=True 85001=False 120000=False None=[False, False]
PASS V-E1-SPEND-FN due(16.0M,1M)=False due(16.000001M,1M)=True due(16.999999M,None)=False due(17M,None)=True reached(16.999999M)=False reached(17M)=True
PASS V-E1-RERUN-ONCE A-invalid1=('RUN', 'J-gceg_product_page', 'A', 2) | A-invalid2: NO_INFORMATION 'arm A invalid twice' next=('RUN', 'J-eaat_session_launch', 'B', 1) B-after-refused=True | B-invalid2: NO_INFORMATION 'arm B invalid twice' | control ...
PASS V-E1-ONE-PAIR refused_with_reason={'attempt3': True, 'duplicate': True, 'after_decided': True, 'later_task': True, 'second_arm_first': True, 'unknown_task': True, 'bad_run_id': True} legal_set_refused=None
PASS V-E1-POSCTL-SM delta15000=RUN delta14999=POSITIVE_CONTROL_STOP 2nd_pair_delta0=RUN noinfo_then_14999=POSITIVE_CONTROL_STOP
PASS V-E1-HARM-SM 3losses=RUN 4losses=HARM_STOP loss_in_9th=('RUN', 'J-pyt_test_gate', 'B', 1) noinfo_between: next=('RUN', 'J-cr_review_verdict', 'A', 1) losses_in_window=3 valid_pairs=9
PASS V-E1-SPEND-SM 16.0M/1M=RUN 16.000001M/1M=SPEND_STOP 16.999999M/None=RUN 16.999999M/1M=SPEND_STOP invalid-crossing=SPEND_STOP@17500000 unknown=SPEND_UNMEASURED unlaunched=('RUN', ..., 'A', 2) all-terminal@17600000=ALL_DECIDED
PASS V-E1-ALL-DECIDED-SM next=('STOP', 'ALL_DECIDED') mismatched=[] r2=['R2_CARRIED', 'R2_CARRIED'] n=13
PASS V-E1-FINAL harm=['STAYS']/13 posctl=STAYS:'arms did not differ' r2=R2_CARRIED spend=['RELOCATION_CANDIDATE', 'STAYS', 'UNDECIDED_STAYS'].. afail_bpass=NO_INFORMATION/True
PASS V-E1-TOKENS-NO-TIEBREAK same_decisions=True tokens_differ=True spent=15400000/6600000
PASS V-E1-HALTED-SM with_stop=('HALTED', 'SPEND_STOP') without=RUN
PASS V-E1-RECONCILE-SM start_only=RECONCILE start+run=RUN before_posctl=RECONCILE
PASS V-E1-CAMPAIGN all_pass=ALL_DECIDED/22r/11p all_loss=HARM_STOP/8r/4p no_delta=POSITIVE_CONTROL_STOP/2r/1p million=SPEND_STOP/17r/8p/spent=17000000/over=0 million_then_999999=SPEND_STOP/17r/8p/spent=16999999/over=0 task2_A_invalid=ALL_DECIDED/22r/11p/t2=NO_INFORMATION reactive-gate-mutant=18r/over=999998
PASS V-E1-NO-MODEL-END blocked=1 with -p=1
E1_PASS=36/36  threshold=36/36
```

(Lines are abridged here; every one of the 36 lines printed PASS.) `validate_bank.py freeze-check` printed
`FREEZE-CHECK OK d68871742a`. `git worktree list | grep -c e1test` printed 0, and `/home/kobii/e1-runs` held 0
entries both before and after the run. No model session was started; the only blocked argv is the positive
control.

## Red drills (throwaway monkeypatches, not shipped except the campaign one)

- harm_fired with no window: V-E1-HARM-SM went RED. harm_fired counting NO_INFORMATION as a loss: HARM-SM stayed
  green, because a NO_INFORMATION *task* never enters the valid-pair list. The mutant is caught at function level
  by V-E1-HARM-FN (`[NO_INFORMATION]*8` -> False).
- positive_control_ok always True: V-E1-POSCTL-SM went RED. spend_stop_due always False: V-E1-SPEND-SM went RED.
- Shipped in V-E1-CAMPAIGN: with the reactive gate (spend_reached alone) the 16 x 1M + 999,999 script starts an
  18th run and ends 999,998 over the cap. The predictive gate stops after 17 runs, over_cap_by 0.
- decide relocating on an A failure: V-E1-ALL-DECIDED-SM first stayed GREEN (see deviation 2), then went RED after
  the fix.

## Deviations from Plan

1. **[Rule 1 - Bug, test side] Wrong mutant arithmetic in my own drill.** I expected the reactive-gate mutant to
   end over_cap_by 999,999. It actually runs two 999,999 runs after the sixteen 1,000,000 runs, so the total is
   17,999,998 and the excess is 999,998. I corrected the expectation and left a comment. The contract code was
   not changed.
2. **[Rule 1 - Bug, test side] V-E1-ALL-DECIDED-SM was self-referential.** The plan says "each of the 11 rules
   its decide() result", and the first draft compared final_decisions against `K.decide`, so a mutated decide
   could not fail the gate (the drill proved it). The gate now compares against a literal clause-4 table
   (`CLAUSE4`).
3. **[Addition] The amendment's control campaign is in V-E1-CAMPAIGN as a sixth script**
   (`million_then_999999`: 17 runs, spent 16,999,999, over_cap_by 0), as the ORCHESTRATOR AMENDMENT asks. The
   five plan scripts are unchanged.
4. **[Discretion] Strict sequencing in replay.** Besides the six listed refusals, replay refuses any run that is
   not exactly the expected next (arm, attempt) for its task, for example a rerun of an arm that is already
   valid or a skipped attempt. It also refuses an arm outside A/B. `final_decisions(ALL_DECIDED)` refuses a
   state with a PENDING task, and an unknown condition raises ContractError. NO_INFORMATION tasks carry
   decision NO_INFORMATION in the state; they are not in valid_pairs, so they never reach the harm window or the
   positive control.
5. **[Discretion] V-E1-ORDER asserts the refusal reason**, not just that a refusal happened, so each refusal case
   tests the clause it names.
6. **[Note] next_action order puts HALTED before RECONCILE.** The behavior list says a pending start is
   reconciled "before any other check". The action text fixes HALTED first, so HALTED stays first. RECONCILE
   still outranks every STOP (pinned by `before_posctl` in V-E1-RECONCILE-SM).

Not touched: e1_runner.py, the bank, BANK_FROZEN_AT, STATE/ROADMAP. `.planning/.../STATE.md` shows as modified in
`git status`, but this executor did not write it.

## Review (orchestrator, after execution)
pp-code-reviewer adversarial review of the contract (snapshot): APPROVE, 1 MEDIUM / 1 LOW / 1 INFO.
- F1 MEDIUM (SPEND_UNMEASURED instead of rerun on a missing transcript): kept; recorded in STATE.md as a decision.
- F2 LOW (replay accepted a run after a stop record / a non-object line): fixed in e1_contract.replay, gated in
  V-E1-ONE-PAIR (non_object, run_after_stop) with a stop-last control; drill red without the check.
- INFO: validity readings (a)/(b) already in the live file (02-01 review fixes).
Suite: E1_PASS=40/40; freeze-check OK d68871742a.
