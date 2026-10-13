# C5 receipt
Status: DONE

Slice done; remainder continues in C5b (chain.json, WU-C5b.md).

Commits: worktree 590ea5cd (affected closure + --affected + review_policy + tests); proof tooling/receipt in the following commit. Live landing: see LANDING line below.

PROVEN (tools/test_land_worktree.py 14/14, test_tier_routing 15/15, test_change_impact 9/9):
- change_impact.affected_closure/affected_tests: per-path closure, test file maps to itself, unjudged analyzer -> unjudged (never green).
- land_worktree --affected: union(explicit --test, closure); unmapped path -> REFUSED AFFECTED_NO_MAPPED_TEST; unjudged -> REFUSED; --exempt globs are listed in the receipt; closure in receipt.
- tier_routing.review_policy: reviewer skipped only for deterministic + all affected green; red/unobserved/non-deterministic -> reviewer.
NOT_PROVEN: step 4 (closure vs full agree on 3 past landings). tools/c5_proof.py ran 463 suites (wall 1226 s, 4917 checks) but under 10x parallelism + 90 s cap 125 suites were red (timeouts and real pre-existing reds mixed), so verdict agreement cannot be read. Raw: WU-C5-proof.json.
FINDINGS: (a) hub tools (tier_routing, land_worktree) reach ~272/463 suites -> "local" proof is not local for hubs; (b) hooks/*.js and vault/* are unmapped (not in the python graph) and refuse unless --exempt; (c) estate has a large pre-existing red baseline, so --affected needs a baseline-red input. All three are C5b steps 3-5.
Landing: standing rule "every CDC landing uses --affected" cannot be applied until C5b (hub closure would run 272 suites against a red baseline); this landing uses explicit --test of the three touched suites. Exception recorded, not silent.
Calls used: ~30.
Next unit must know: run the baseline once serially at 7aaff610; do not trust WU-C5-proof.json verdicts.LANDING: live 1ad11190 (explicit --test, exception above).
