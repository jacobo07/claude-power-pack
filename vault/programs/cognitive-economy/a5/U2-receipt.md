STATUS: DONE
COMMITS: 4fd5444a
Packet sha256 176d42c0f3bd verified.
Gate: python3 -I tools/test_a5_u2.py -> A5_U2_PASS=12/12 (mutant "rotation ignores capsule" is red; controls admit).
Best combined policy: f = slim floor + rotate@20 + read-once + STATE projection + poll->event: 322,165,170 vs actual 3,100,841,244 processed tokens = -89.6% (calls 10,985 -> 9,780). Source: A/COUNTERFACTUAL.md, A/data/counterfactual.json.
Singles: slim -39.7%, rotate 12/20/40 -50.0/-46.4/-38.6%, read-once -8.1%, STATE -11.6%, poll->event -9.3%.
Assumes (A1-A11 in COUNTERFACTUAL.md): ctx-only currency; growth per call independent of policy; slim floor 13,507 applied to every session; 2.5K capsule, its authoring cost and information loss NOT modelled; U1 labels are proxies; event wake cost not modelled. f is a replay upper bound, LOW confidence, not realized savings.
Duplicate derivations: 242 CSE-candidate groups, 419 redundant occurrences of 3,802 reads (crude key: read target + next 3 first tools).
Tool-schema share of floor: UNKNOWN (transcripts give totals only, no per-component counts).
Negative results: none (no policy < 3%); vault/config/a5-negative-investments.json written with empty entries.
Deviations: none. Model calls: none from code.
HANDOFF NOTE: U3 can consume COUNTERFACTUAL.md; treat f's -89.6% as bound, rotation fidelity is the key unknown.
