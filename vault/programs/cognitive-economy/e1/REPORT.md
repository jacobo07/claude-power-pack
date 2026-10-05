# E1 report

Rendered by `e1_report.py` from `results.jsonl` (56 records). Contract: `ADDENDUM-E1.md`.

**Stop condition: `ALL_DECIDED`** (stop record at 2026-10-05T11:16:32.416885+00:00).

- Runs counted: 22; valid pairs: 11; losses in the first 8 valid pairs: 2
- Model `claude-opus-5-5`, CLI `2.1.289 (Claude Code)`, BASE `78ba9e7414c3e046b1e91ce7b7fde86c78f205f5`

## Decisions

| rule | decision | basis | task | A run | B run | A pass | B pass |
|---|---|---|---|---|---|---|---|
| `rules/generated-content-needs-an-evidence-gate.md` | STAYS | A passed, B failed: the loss is charged to this task's rule | J-gceg_product_page | J-gceg_product_page-A-a1 | J-gceg_product_page-B-a1 | True | False |
| `rules/effect-authority-across-transports.md` | STAYS | A passed, B failed: the loss is charged to this task's rule | J-eaat_session_launch | J-eaat_session_launch-A-a1 | J-eaat_session_launch-B-a1 | True | False |
| `rules/human-facing-external-effects.md` | RELOCATION_CANDIDATE | A passed, B passed | J-hfee_outbox | J-hfee_outbox-A-a1 | J-hfee_outbox-B-a1 | True | True |
| `rules/documented-capability-must-be-executable.md` | RELOCATION_CANDIDATE | A passed, B passed | J-dcme_doc_status | J-dcme_doc_status-A-a1 | J-dcme_doc_status-B-a1 | True | True |
| `rules/validation-planes-do-not-transfer.md` | RELOCATION_CANDIDATE | A passed, B passed | J-vpdt_verified_level | J-vpdt_verified_level-A-a1 | J-vpdt_verified_level-B-a1 | True | True |
| `rules/capability-preserving-compaction.md` | RELOCATION_CANDIDATE | A passed, B passed | J-cpc_compact_row | J-cpc_compact_row-A-a1 | J-cpc_compact_row-B-a1 | True | True |
| `rules/state-lifetime-and-incarnation.md` | RELOCATION_CANDIDATE | A passed, B passed | J-slai_pane_sleep | J-slai_pane_sleep-A-a1 | J-slai_pane_sleep-B-a1 | True | True |
| `rules/post-effect-resource-truth.md` | RELOCATION_CANDIDATE | A passed, B passed | J-pert_freed_memory | J-pert_freed_memory-A-a1 | J-pert_freed_memory-B-a1 | True | True |
| `rules/durable-exit-transaction.md` | STAYS | A passed, B failed: the loss is charged to this task's rule | J-det_exit_all | J-det_exit_all-A-a1 | J-det_exit_all-B-a1 | True | False |
| `rules/python/testing.md` | STAYS | A passed, B failed: the loss is charged to this task's rule | J-pyt_test_gate | J-pyt_test_gate-A-a1 | J-pyt_test_gate-B-a1 | True | False |
| `rules/common/code-review.md` | NO_INFORMATION | A failed: no information, the rule stays | J-cr_review_verdict | J-cr_review_verdict-A-a1 | J-cr_review_verdict-B-a1 | False | False |
| `rules/scoped-side-effect-authority.md` | R2_CARRIED | decided by R2, carried in by reference | - | - | - | - | - |
| `rules/technical-failure-to-product-state.md` | R2_CARRIED | decided by R2, carried in by reference | - | - | - | - | - |

Decisions are the contract's (clause 4); no token count breaks a tie. No task where B passed and A failed.

Losses whose B run also failed control checks (the solution broke the task's plain behaviour, not only its judgement; the decision stands, attribution to the rule is weaker): J-eaat_session_launch (E1J_PASS=0/6 control=0/4 judgement=0/2), J-pyt_test_gate (E1J_PASS=6/7 control=3/4 judgement=3/3).

## Positive control (gate 1, first valid pair)

Task J-gceg_product_page: A first-call context 92,347, B 70,714, delta 21,633 (needs >= 15,000): OK.

## Spend

- Counted context summed over all runs (valid and invalid): 9,172,196 of the 17,000,000 cap; over the cap by 0; largest run 1,234,809
- First-call delta A - B over 11 valid pairs: mean 19,276, min 19,012, max 21,633
- Logical transcript tokens only; the account meter's weighting is not derived from them.

## Runs

| run | valid | invalid reasons | grade | first-call ctx | total ctx | output tokens |
|---|---|---|---|---|---|---|
| J-gceg_product_page-A-a1 | True | - | E1J_PASS=8/8 control=4/4 judgement=4/4 | 92,347 | 1,234,809 | 10,744 |
| J-gceg_product_page-B-a1 | True | - | E1J_PASS=7/8 control=4/4 judgement=3/4 | 70,714 | 297,949 | 2,478 |
| J-eaat_session_launch-B-a1 | True | - | E1J_PASS=0/6 control=0/4 judgement=0/2 | 73,328 | 301,967 | 3,771 |
| J-eaat_session_launch-A-a1 | True | - | E1J_PASS=6/6 control=4/4 judgement=2/2 | 92,364 | 471,510 | 3,165 |
| J-hfee_outbox-A-a1 | True | - | E1J_PASS=5/5 control=2/2 judgement=3/3 | 92,349 | 379,962 | 4,211 |
| J-hfee_outbox-B-a1 | True | - | E1J_PASS=5/5 control=2/2 judgement=3/3 | 73,304 | 301,906 | 3,736 |
| J-dcme_doc_status-B-a1 | True | - | E1J_PASS=5/5 control=2/2 judgement=3/3 | 73,312 | 378,479 | 3,412 |
| J-dcme_doc_status-A-a1 | True | - | E1J_PASS=5/5 control=2/2 judgement=3/3 | 92,350 | 374,393 | 2,305 |
| J-vpdt_verified_level-A-a1 | True | - | E1J_PASS=7/7 control=4/4 judgement=3/3 | 92,355 | 766,607 | 4,967 |
| J-vpdt_verified_level-B-a1 | True | - | E1J_PASS=7/7 control=4/4 judgement=3/3 | 73,314 | 298,604 | 2,142 |
| J-cpc_compact_row-B-a1 | True | - | E1J_PASS=9/9 control=4/4 judgement=5/5 | 73,335 | 462,251 | 3,949 |
| J-cpc_compact_row-A-a1 | True | - | E1J_PASS=9/9 control=4/4 judgement=5/5 | 92,375 | 377,181 | 2,897 |
| J-slai_pane_sleep-A-a1 | True | - | E1J_PASS=7/7 control=4/4 judgement=3/3 | 92,352 | 376,081 | 2,467 |
| J-slai_pane_sleep-B-a1 | True | - | E1J_PASS=7/7 control=4/4 judgement=3/3 | 73,340 | 222,995 | 2,089 |
| J-pert_freed_memory-B-a1 | True | - | E1J_PASS=6/6 control=3/3 judgement=3/3 | 73,335 | 298,538 | 2,293 |
| J-pert_freed_memory-A-a1 | True | - | E1J_PASS=6/6 control=3/3 judgement=3/3 | 92,355 | 374,313 | 2,278 |
| J-det_exit_all-A-a1 | True | - | E1J_PASS=5/5 control=2/2 judgement=3/3 | 92,339 | 374,148 | 2,088 |
| J-det_exit_all-B-a1 | True | - | E1J_PASS=4/5 control=2/2 judgement=2/3 | 73,302 | 298,120 | 2,319 |
| J-pyt_test_gate-B-a1 | True | - | E1J_PASS=6/7 control=3/4 judgement=3/3 | 73,328 | 297,954 | 2,123 |
| J-pyt_test_gate-A-a1 | True | - | E1J_PASS=7/7 control=4/4 judgement=3/3 | 92,373 | 374,346 | 2,401 |
| J-cr_review_verdict-A-a1 | True | - | E1J_PASS=7/8 control=4/4 judgement=3/4 | 92,352 | 375,769 | 3,104 |
| J-cr_review_verdict-B-a1 | True | - | E1J_PASS=4/8 control=4/4 judgement=0/4 | 73,256 | 534,314 | 3,731 |

## Bank-access audit

Each run's transcript tool calls were searched for the bank's markers (Phase 1 limit: the shared object store makes the bank reachable by git from a run tree). A hit is reported against its pair; it changes no decision.

- No marker hit in any audited run.

## Proposed move list (for the Owner)

- `rules/capability-preserving-compaction.md`
- `rules/documented-capability-must-be-executable.md`
- `rules/human-facing-external-effects.md`
- `rules/post-effect-resource-truth.md`
- `rules/scoped-side-effect-authority.md`
- `rules/state-lifetime-and-incarnation.md`
- `rules/technical-failure-to-product-state.md`
- `rules/validation-planes-do-not-transfer.md`

Each move is a global config write under `~/.claude/rules` (rule -> skill + one-line pointer) and needs the Owner's yes on this exact list (HR-001). This report changed nothing under `~/.claude`.
After a move, a one-call gate-1 probe confirms the billed floor fell by the relocated rules' share.

## Known limits (ADDENDUM-E1, verbatim)

- n = 1 pair per rule detects gross losses only. R1 and R2 both hit ceilings.
- One host, one model, one CLI version, this repository. GEX44's prefix is ~16.5k tokens smaller than the
  laptop's (fewer hooks). The rule bodies and the measured delta are the same on both hosts.
- Logical transcript tokens only. The account meter's weighting is unknown and is not derived from these numbers.
- Prior: R1 and R2 judged 6 rules with 0 losses in 56 counted runs. A ceiling is the likely outcome. Gate 3 still
  holds, because without E1 the status quo is to keep all 11 resident; E1 is what can move them. But the
  experiment buys "no gross loss observed", not proof of zero effect.
