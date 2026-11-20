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

## Audio re-inspection 2026-11-20 (laptop pane adcdff7b)

The four videos were supplied in the laptop's Downloads; all four sha256 match the backlog table. Audio extracted with
the vendored ffmpeg, transcribed offline by the video-analyzer bundled whisper.cpp (tiny q4_0, every run TRANSCRIPT_OK)
on GEX44. Transcripts: `synsation/transcripts/<id>.txt` (machine transcription: names garbled, e.g. "Scalance" =
skeleton, "sock-to" = SOC 2, "hip-hop" = HIPAA). Verdict per wording-dependent claim:

| id | audio verdict | quote (timestamp) |
|---|---|---|
| UX-07 | CONFIRMED (scope); latency thresholds NOT in source (CPP heuristic) | skeleton "entire page or a large section"; progress "when you know how long"; inline spinner "small contained actions" (7de80ae3 0:11-0:42) |
| UX-08 | CONFIRMED | "the layout is here, the data is coming" (7de80ae3 0:16) |
| UX-09 | CONFIRMED | "a button you just clicked or one part of the page that's refreshing" (0:37) |
| UX-10 | NOT IN SOURCE (CPP-derived from CDIO-07) | the source's spinner warning is different: "a spinner on a file upload people might assume that it's stuck" (0:34) |
| UX-11 | CONFIRMED incl. rollback | "doesn't wait for the server ... Later it fails it rolls back" (0:52-0:55) |
| UX-12 | CPP-DERIVED: the source praises "it feels instant"; truth-first is CPP's constraint | (0:55) |
| UX-13 | CONFIRMED as a 4-way choice; numbers are CPP heuristics | "skeleton screen, a spinner, a progress bar or no loader at all" (0:01) |
| UX-14 | CONFIRMED, SPONSORED | "depending on your product your data your customers your location" (86392f83 0:13); "I'm partnering with Vanta for this video" (1:22) |
| UX-15 | PARTIAL: framework choice is the vendor's feature; the general compiler is CPP's generalisation | "you choose the framework you're working towards" (0:53) |
| UX-16 | CONFIRMED | "what is up to standard and what still needs to be fixed" (0:53) |
| UX-17 | CONFIRMED (vendor claim) | "connect ... to the systems that your company already uses ... organize the evidence" (0:48-1:04) |
| UX-18 | CONFIRMED | "this work doesn't really end after the first audit" (1:04) |
| UX-19 | CONFIRMED (evidence vs independent review) | "the evidence an independent auditor will eventually need to review" (1:00) |
| UX-20 | CONFIRMED | "compliance will not automatically [win] customers ... but being prepared can stop it from becoming the reason that you lose them" (1:18) |

Also confirmed by audio, UX-01..06: fe97b0a1 ("take them directly to those so they don't have to scroll", 0:33; keyboard
and screen-reader discoverability, 0:38) and 14a28c4c (Fitts's law, invisible padding, clickable label/card, scroll-vs-tap
on whole-card targets, 0:14-0:55). NEW from audio: disabled is correct "when you click a button and you're waiting
... prevent duplicate submissions" (fe97b0a1 0:49). `check_disabled_control` flagged that case as opaque; it now exempts
`pending_submission` only when `pending_visible` (poles + seeded mutant in test_bcap2_synsation). Evidence grade for
UX-14..18: one sponsored source, so it is a vendor workflow, not independent UX evidence; dispositions above unchanged.

Cross-cutting state-space ontology and negative corpus: NOT built; the executable checkers' defect vocabularies are the seed. Browser-real
scenarios remain BLOCKED-ON-LAPTOP.
