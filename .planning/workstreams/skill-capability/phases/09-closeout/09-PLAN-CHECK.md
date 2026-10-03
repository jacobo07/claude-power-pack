# Phase 9 plan check (2026-10-04, gex44, HEAD ce9e7a25)

Verdict: ISSUES FOUND -- 0 BLOCKER, 1 WARNING, 3 INFO. Execution may proceed; W-01 is recommended before 09-01 Task 1.

## Premises verified (HR-PREMISE-001)
- CE: `gate_argv_problem` (L99), `class Resolver` (L116; frozen_sha/frozen_at_commit/handoff_landed/run_gate as described), `check_ledger(led,res,final,only,run_gates)` (L182), L8 (L251-258, needs `reviews.<k>.file` + truthy deltas), `FILE_KINDS`, `DEFERRAL_PROSE`, `lf_sha256`, `_git` -- all present.
- Wrapper: `check_retained` L66, rebinding L38-43, `--selftest` -> `SCP_SELFTEST`, `--final` -> `SCP_VERDICT`, `--pillar` -> `CEP_PILLAR_X` (CE L536), `--status` JSON (CE L529). Measured now: `--pillar N` rc 1 with exactly `FAIL L3 N: no terminal disposition`; `--status` open ["N"].
- Ledger: lines 125/126 are exactly ` "reviews": {"ukdl": null, "cbr": null},` / ` "deltas": {"product": [], "intelligence": []}`; only `state` differs from FROZEN_AT; state.N equals its frozen copy. owner-bundle 19 `[X]` lines; 5 STATE decision lines match the regex. origin mission/skill-capability = 287b360a. `git status -- tools vault/programs/skill-capability` clean.
- `tools/test_skill_handoffs.py` `record` (L46), `modules/liveness/reachability.py` exist.
- frontmatter.validate --schema plan: 09-01/02/03 all valid.

## L5 question (does `--closeout` satisfy CE gate rules on the laptop?)
Yes. Argv `["python","tools/test_skill_capability_prefinal.py","--closeout"]` passes `gate_argv_problem` (under tools/, not SELF_REL, safe args). Inside `--final`, run_gate starts it; it calls check_ledger(final=True, run_gates=False) so no recursion. It returns [] only if state.N is COMMITTED (CommittedResolver reads HEAD), and 09-03 Task 1 section 4 orders it correctly: write state.N -> commit -> `--closeout` PASS -> `--final`. Gate+prg kinds satisfy REQUIRED_KINDS for IMPLEMENTED_AND_VERIFIED.

## Ledger edit vs phase 7/8 fingerprints
Pillar gates that read ledger.json (test_skill_coverage/delivery/drift/card_lineage/listing_floor_verdict) read state/frozen, not reviews/deltas; and 09-02's gate re-runs V-PF-PILLARS A..M after the edit, so any dependency would surface red. No gate pins ledger.json's sha. owner-bundle.md is not edited. OK.

## WARNING
W-01 [key_links / robustness] `--closeout` must stay green on the laptop at `--final` time; it reads the LIVE HEAD STATE.md.
- 09-01-PLAN.md interfaces C-CLOSEOUT (decisions); 09-03-PLAN.md Task 1 preamble.
- Evidence: V-PF-CLOSEOUT-DECISIONS discovers decision lines from HEAD STATE.md each run and requires each `L[2:82]` prefix in LAPTOP-CLOSEOUT.md. STATE.md is rewritten after 09-03 (GSD phase-complete/state updates, Phase 9 decision lines, Owner's own laptop notes). Any new line matching `OWNER DECISION|\(decision\)`, or any reword of an existing one, turns the state.N gate red inside `--final` (L5 rc 1) with nothing to fix in the closeout itself. The preamble only warns.
- Fix (example): in closeout mode read STATE.md at the commit that last touched LAPTOP-CLOSEOUT.md (or at the record's `commit:`), not at HEAD; keep HEAD discovery for gex44 mode. Add a selftest mutant for a later-added line.

## INFO
I-01 D-02 literally says "run --final, then write state.N"; --final cannot pass before state.N exists. 09-03 correctly orders state.N -> commit -> --final -> CLOSE.md. Say so in 09-03-SUMMARY as a justified ordering.
I-02 C-CBR keeps the N row `open` in closeout mode, so after state.N is closed cbr.md still says N open. Consistent with the gate; the preamble should say the N row records the gex44 run status.
I-03 On the Windows laptop checkout, autocrlf/stat noise on the three narrowed code files would make V-PF-COMMITTED INCONCLUSIVE (rc 2) inside --final. LAPTOP-CLOSEOUT could add `git status --porcelain -- tools` as an expected-empty step before --final.
