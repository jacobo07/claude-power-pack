# DRK Proactive Scan -- decisions the stack did not ask about

Generated 2026-07-11T20:04:02.640908+00:00 | repo `claude-power-pack` | 9 suggestion(s): 0 high, 4 medium, 5 low.

Every row cites a real path or ledger row. A finding without evidence is not published (T-DRK-PROACTIVE-NOISE-001). `high` requires a verifiable blast radius, not a heuristic.

| Urgency | Type | Where | Hint | Finding | Evidence |
|---|---|---|---|---|---|
| MEDIUM | decision_needed | `modules/cognitive_os/` | REQUEST-EVIDENCE | modules/cognitive_os/ is a Tipo-B module with no Decision Record -- the reasoning behind it is unrecorded | modules/cognitive_os/__init__.py exists and its docstring touches 3 blast surface(s) (code, agents, data); 0 records in the decision registry name it (0 records scanned) |
| MEDIUM | orphan | `liveness:audits/drk-proactive` | REQUEST-EVIDENCE | drk-proactive is WIRED-BUT-SILENT: DRK proactive scanner -- daily sweep proposing decisions nobody asked about | D1 liveness audit -> WIRED-BUT-SILENT: no file matching vault/audits/drk_proactive_*.md (surface produced nothing) |
| MEDIUM | orphan | `liveness:decision-registry/drk-kernel` | REQUEST-EVIDENCE | drk-kernel is WIRED-BUT-SILENT: DRK review kernel -- every reviewed decision appends a record | D1 liveness audit -> WIRED-BUT-SILENT: no file matching vault/decision_registry/records.jsonl (surface produced nothing) |
| MEDIUM | orphan | `liveness:pm-bus/pm-03-bus` | REQUEST-EVIDENCE | pm-03-bus is WIRED-BUT-SILENT: PM-03 findings bus -- written every session, consumer wiring pending | D1 liveness audit -> WIRED-BUT-SILENT: 5 producer file(s); consumer is the SessionStart hub read but emits no 'pm03_consume' signal -- consumption unmeasured |
| LOW | decision_needed | `modules/ads/` | REQUEST-EVIDENCE | modules/ads/ is a Tipo-C module with no Decision Record -- the reasoning behind it is unrecorded | modules/ads/__init__.py exists and its docstring touches 2 blast surface(s) (code, agents); 0 records in the decision registry name it (0 records scanned) |
| LOW | decision_needed | `modules/cpc_os/` | REQUEST-EVIDENCE | modules/cpc_os/ is a Tipo-C module with no Decision Record -- the reasoning behind it is unrecorded | modules/cpc_os/__init__.py exists and its docstring touches 2 blast surface(s) (workflows, data); 0 records in the decision registry name it (0 records scanned) |
| LOW | decision_needed | `modules/deployment/` | REQUEST-EVIDENCE | modules/deployment/ is a Tipo-B module with no Decision Record -- the reasoning behind it is unrecorded | modules/deployment/__init__.py exists and its docstring touches 2 blast surface(s) (code, infra); 0 records in the decision registry name it (0 records scanned) |
| LOW | decision_needed | `modules/sdd_os/` | REQUEST-EVIDENCE | modules/sdd_os/ is a Tipo-C module with no Decision Record -- the reasoning behind it is unrecorded | modules/sdd_os/__init__.py exists and its docstring touches 2 blast surface(s) (code, roadmap); 0 records in the decision registry name it (0 records scanned) |
| LOW | opportunity | `modules/` | DEFER | 14 further unrecorded-decision candidate(s) were not listed (cap=5) | scan cap reached: 14 candidate(s) beyond the top 5 |

Zero findings is a valid scan.
