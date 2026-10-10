# CPP inventory for ce-a5 (read-only scan of the laptop CPP tree, 2026-10-09; ~75 reads; cite, re-verify before acting)

| # | Capability | Status | Owner / evidence |
|---|---|---|---|
| 1 | Cognitive Economy program | ACTIVE, realized savings none (CLOSE.md "EFFECTIVENESS_NOT_CERTIFIED") | vault/programs/cognitive-economy/ (Gen1 CLOSE.md, gen2/ MISSION/ledger/COMPLETION-PLAN, gen3/, e1/REPORT.md). Gen1 falsified F 1.88 %, G (CSE), K 2.67 %, P 0.50 %; C (tool schemas) 0.002 %. gen2 W4-W9, R open |
| 2 | TOK-18 Context Compiler / SSM / UCVM / UCR-CIF | Context Compiler SPEC-ONLY (S5 UNDECIDED); SSM, UCVM absent as code; UCR-CIF not promoted | vault/plans/tok18-tranche-context-runtime-2026-10-06.md; tools/wu3_packets.py |
| 3 | Ralph gsd_mission, mission_steward, goal sweep | LIVE (sweep every 5 min); mission compiler (gsd_compile, gsd_dossier) only on branch cost-collapse | tools/gsd_mission.py, tools/mission_steward.py, modules/gsd_x/goal/* |
| 4 | Proof reuse / Proof of Non-Work / No Cognition | verified_reuse.py BUILT-NOT-WIRED; Non-Work SPEC-ONLY; No-Cognition ABSENT | tools/verified_reuse.py, tools/evidence_bundle.py, tools/tranche_driver.py |
| 5 | FIOS, CBR, UKDL, Graphify, Findings Bus | Graphify LIVE; FIOS gated; CBR manual, unreachable for CE; UKDL a document; Bus read LIVE, publish unwired | modules/frontier_intelligence, modules/tower, vault/knowledge_base/ukdl-universal.md, modules/graphify |
| 6 | Singleflight / derivation cache | goal singleflight LIVE (gsd_mission "singleflight: ... live attempt of this goal"); semantic/derivation cache ABSENT | tools/gsd_mission.py |
| 7 | Routing / tool virtualization | model-routing.json advisory and split-brain with cost_collapse/router.py; route_admission missions-only; jit_skill_loader LIVE; tool schemas already lazy | vault/config/model-routing.json, tools/route_admission.py |
| 8 | cost_to_completion / usage_index / autopsy | cost_to_completion DORMANT (test-only caller); usage_index CLI on demand; goal-autopsy LIVE in mission_spend | tools/cost_to_completion.py, tools/usage_index.py, tools/mission_spend.py |
| 9 | Resource admission (RAM) | ABSENT as a refusal: host-memory-floor.js warns; gsd_long_run wait-ram is a soft wait | hooks host-memory-floor.js, tools/gsd_long_run.py |
| 10 | Economic CI | floor_regression_gate nightly, report-only; cep_gen2 --tranche manual | tools/floor_regression_gate.py, tools/cep_gen2.py |
| 11 | Trace mining | indexers built (usage_index, tis_observed, token_corpus_audit, measure/turns.py); sequence mining ABSENT | tools/* |
| 12 | Model-call firewall / provenance | ABSENT; concurrency/budget guards LIVE | hooks agent-solo-guard.js, session_budget_guard.js |
| 13 | Theorem registry / negative investment | paired_experiment.py registry and goal evidence negative-hypothesis log BUILT, no production caller | tools/paired_experiment.py, modules/gsd_x/goal/evidence.py |
| 14 | Visual diff | CPP verdict is a vision model (sleepless_qa/verdict/visual.py); numeric box gate lives in skill image-calco (gate_boxes.py) | — |

GEX44 facts (arming pane, 2026-10-09): live CPP tree /home/kobii/.claude/skills/claude-power-pack at 1872e9a1 lacks
route_admission, tranche_driver, cost_to_completion, route-floors; no session budget guard in its dispatcher. ce-a5 runs
on its own runtime /home/kobii/ce5-env/pp (laptop CPP cd389b50 + Linux slim settings 6d8ca5c4) with its own state dir.
Laptop-identical gates there: ADM 43/43, GOAL 54/54, ENVELOPE 55/55; RADM 19/21 (same 2 reds on the laptop at HEAD:
pre-existing); DRIVER 26/27 (V-DRIVER-REAL-METER needs a laptop transcript: host fixture); SBG 19/21 (the 2 reds check
the live ~/.claude dispatcher, which ce-a5 does not use; the standalone runner was drilled: deny over cap, silent under
cap and with no budget file).
