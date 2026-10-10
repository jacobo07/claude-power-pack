STATUS: DONE
COMMITS: 09c31f84
Packet sha256 3edc0e09ab8b verified. Scope: tools/reality_cover.py, tools/test_a5_u4.py, A/REALITY-PLAN.md, A/inputs/dws-reality-obs.json.
GATE tools/test_a5_u4.py: A5_U4_PASS=13/13
Tool: greedy weighted set cover over sessions (setup cost); obs deduped by obs_id and (host,surface,preconditions), once per epoch, fanned out.
Bound: setup <= H(m) x OPT (m = max session size); obs minutes constant across covers. Exhaustive optimum checked on 60 random + 1 fixture.
Claims never PROVEN by planning; missing/unschedulable obs -> OPEN; PROVEN only with same-epoch capture.
Mutant dedupe off -> red (5 instances vs 2).
DWS (source: REALITY-PLAN.md, minutes are ESTIMATES): 14 observations, 11 claims, 1 session, Owner 55 min vs per-claim 35 acquisitions / 11 sessions / Owner 220 min.
Deviations: observation map hand-derived from ROADMAP phase 25 (budget JSON has no observation fields); candidate sessions per host + all-in (setup 10/15 min) are assumptions.
Not run: no real-capture check; epoch invalidation beyond string equality UNKNOWN.
HANDOFF NOTE: U4 done; U10 can consume reality_cover.compile_plan output; session setup minutes need Owner calibration.
