# BCAP-2 Phase 5 — Synsation UX dispositions

Source: vault/backlog/2026-10-13_synsation-ux-patterns-absorption.md (UX-01..UX-20). The four source videos are NOT on GEX44, so every
claim that depends on wording rather than a visible frame stays INFERRED; re-inspection is a LAPTOP step (LAPTOP_STEPS.md).
Vocabulary: ALREADY OWNED, EXTEND (new content at the existing owner), IMPL-EXEC (new executable check in modules/cdio/ux_contracts.py),
HEURISTIC, REJECT, UNVERIFIED. Machine-checked by `tools/test_bcap2_synsation.py` (closed vocabulary, one row per UX id, owner path exists).

| id | concept | disposition | cpp owner | note |
|---|---|---|---|---|
| UX-01 | disabled hides why; blocked-by-validation is not unavailable | IMPL-EXEC | modules/cdio/ux_contracts.py | `check_disabled_control`: opaque-disabled-action, validation-block-with-no-error-path; false-positive guard: obvious short prerequisite passes |
| UX-02 | disabled-state contract (7 questions, 6 defect classes) | IMPL-EXEC | modules/cdio/ux_contracts.py | the six backlog defect classes are the checker's closed output vocabulary |
| UX-03 | long-form validation spatially discoverable | HEURISTIC | vault/knowledge_base/cdio/CDIO-02-ux-intelligence-engine.md | no browser on GEX44: scroll/focus/keyboard-cover scenarios are LAPTOP/browser plane; checker only flags a long form without error summary |
| UX-04 | glyph size != hit area | IMPL-EXEC | modules/cdio/ux_contracts.py | `check_hit_targets` measures the declared hit rect, not the icon; floor itself owned by CDIO-05/08 |
| UX-05 | proximity vs accidental activation | IMPL-EXEC | modules/cdio/ux_contracts.py | overlapping-hit-targets, hit-area-steals-neighbour; destructive-near-safe flagged |
| UX-06 | row/label is the target; nested controls | IMPL-EXEC | modules/cdio/ux_contracts.py | nested-interactive without stop-propagation flagged |
| UX-07 | waiting pattern chosen by scope/latency/truth | IMPL-EXEC | modules/cdio/ux_contracts.py | `waiting_pattern`; enum itself ALREADY OWNED by CDIO-07 |
| UX-08 | skeleton is a structural promise | EXTEND | vault/knowledge_base/visual-patterns/skeleton-structural-promise.md | new pattern entry with "when NOT to use" |
| UX-09 | inline spinner for local work | EXTEND | vault/knowledge_base/visual-patterns/inline-pending-control.md | new pattern entry |
| UX-10 | no spinner flash | ALREADY OWNED | vault/knowledge_base/cdio/CDIO-07-experience-contract.md | CDIO-07 spinner-flash defect; decision function encodes show-delay as input `latency_ms` below threshold -> none |
| UX-11 | optimistic UI is a truth contract | ALREADY OWNED | vault/knowledge_base/cdio/CDIO-07-experience-contract.md | reconciliation rule exists; `waiting_pattern` refuses optimistic for irreversible/low-success |
| UX-12 | perceived performance subordinate to truth | ALREADY OWNED | vault/knowledge_base/cdio/CDIO-07-experience-contract.md | fake numeric progress is refused: `progress` only when `progress_measurable` |
| UX-13 | waiting decision matrix | IMPL-EXEC | modules/cdio/ux_contracts.py | thresholds are inputs/defaults, labelled HEURISTIC; not external evidence |
| UX-14 | compliance UX is contextual workflow | UNVERIFIED | vault/knowledge_base/cdio/CDIO-03-trust-premium-intelligence.md | partly promotional video; transfer evidence absent |
| UX-15 | contextual requirements compiler | UNVERIFIED | vault/knowledge_base/cdio/CDIO-02-ux-intelligence-engine.md | promotion needs transfer evidence beyond compliance |
| UX-16 | readiness states, not binary badge | HEURISTIC | vault/knowledge_base/cdio/CDIO-03-trust-premium-intelligence.md | status vocabulary candidate only |
| UX-17 | evidence acquisition reduces toil | HEURISTIC | vault/knowledge_base/cdio/CDIO-03-trust-premium-intelligence.md | candidate process rule, not universal |
| UX-18 | compliance is continuous state | UNVERIFIED | vault/knowledge_base/cdio/CDIO-03-trust-premium-intelligence.md | domain-specific state machine |
| UX-19 | readiness/evidence/review/certification distinct | ALREADY OWNED | vault/knowledge_base/cdio/CDIO-03-trust-premium-intelligence.md | CDIO-03 trust-claim honesty; no legal taxonomy invented |
| UX-20 | trust removes blockers, promises no demand | ALREADY OWNED | vault/knowledge_base/cdio/CDIO-04-conversion-intelligence-engine.md | CDIO-04 conversion honesty |

Cross-cutting state-space ontology and negative corpus: NOT built; the executable checkers' defect vocabularies are the seed. Browser-real
scenarios remain BLOCKED-ON-LAPTOP.
