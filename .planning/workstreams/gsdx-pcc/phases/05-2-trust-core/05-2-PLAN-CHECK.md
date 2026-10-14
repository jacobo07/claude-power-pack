# 05-2 PLAN-CHECK (persisted by WU-P52a)

Source: the WU-P52 plan-checker (a937c5b6391d8ade3), partial (its breaker fired at ~22 calls), findings taken verbatim from `packets/WU-P52-receipt.md`. Verdict: revise plans, no hard blocker.

| id | finding (verbatim) | disposition | applied to |
|---|---|---|---|
| a | inherited events with no authority field (JV:172, Inh:372) must be admitted as "claims nothing above original" and inherit.apply must stamp authority | ACCEPTED | 05-2-01-PLAN.md |
| b | add test_gsd_x_goal_certificate.py to regression list | ACCEPTED | 05-2-05-PLAN.md |
| c | route inherit.ineligible and verification_set for D11, name verification_set in 05-2-04 | ACCEPTED | 05-2-04-PLAN.md |
| d | define legacy contract_hash for F8 | ACCEPTED (sha256 of the first declared contract) | 05-2-02-PLAN.md |
| e | add V-DONE-COUNT>=40 and a MIGRATION-ONCE task | ACCEPTED | 05-2-05-PLAN.md |
| f | F3 needs a control with a legitimately different verdict gate class | ACCEPTED | 05-2-02-PLAN.md |
| g | F1/F12 are baseline, never RED | ACCEPTED | 05-2-02-PLAN.md |

Plans 05-2-03 needed no change. Each amendment is an appended section in its PLAN file.