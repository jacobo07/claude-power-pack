---
status: DONE 2026-10-18 -- Owner "rec both": implement AC-4, and orca.node-manifest/1 supersedes KSR capabilities.json
opened: 2026-10-18
branch: dws/pp-rows
covers: [uwcp-s4-22, node-adapter, node-manifest-consumer, goal-node, known-heads, manifest-freshness]
extends: [uwcp.md §17-18 S4 step 22 ("22 node adapter + freshness (CPP)"), uwcp.md line 74]
consumers: [uwcp.md S4 step 23 placement.py, uwcp.md §10 capsule bundle "incremental against node-known heads"]
producer: Orca src/shared/node-manifest.ts (orca.node-manifest/1), schema config/schemas/orca-node-manifest-1.schema.json, contract test src/shared/node-manifest-schema.contract.test.ts
---

# UWCP S4-22 -- goal node adapter + freshness

## Why this file exists
`uwcp.md` named S4-22 in one line ("22 node adapter + freshness (CPP)") and one table row
("node manifest | KSR capabilities.json | EXTEND via goal/node.py adapter (measured_at, known heads,
max age)"). Nothing defined acceptance, so Orca's DWS matrix row 17 could only say "BLOCKED on UWCP
S4-22" and nobody could tell when it was unblocked. This file is that definition.

## Objective
A goal (gsd_x) can ask "what does host H look like right now?" and get either a typed, fresh view of
H or a refusal with a code. It never gets a repaired, defaulted or stale view.

## Interface (`modules/gsd_x/goal/node.py`)
`read_node_manifest(doc, now_ms, max_age_ms) -> NodeView` or raises `NodeManifestError(code)`.
`doc` is a dict, JSON text or a path. Read-only: the adapter never writes, probes or contacts a host.

`NodeView`: `address`, `observed_at`, `measured` (name -> value, measured only), `unknown`
(name -> reason), `known_heads` (tuple in producer order, or None when the node did not say).

## Acceptance criteria
| AC | Rule | State |
|---|---|---|
| AC-1 | `schema` must equal `orca.node-manifest/1`; any other top-level key, or a missing `observed_at`/`node`/`measurements`, refuses `malformed` | MET (8b776241) |
| AC-2 | Manifest freshness: `now - observed_at > max_age_ms` refuses `stale_manifest`; `observed_at` more than 60 s ahead refuses `from_future` | MET (8b776241) |
| AC-3 | Measurement freshness (`measured_at`, `max_age`): each of memory/disk/vram/resident_model is `measured` (exact 5 fields, `max_age_ms` > 0, `now - measured_at <= max_age_ms` else `stale_measurement`) or `unknown` with a non-empty reason. Unknown is never read as zero | MET (8b776241) |
| AC-4 | **Known heads**, exactly as the producer schema: absent -> `known_heads is None` (unknown); present -> a non-empty list of non-empty strings, exposed as a tuple in order, duplicates allowed (the schema has no uniqueItems; a stricter consumer would refuse valid manifests). `[]`, `null`, a non-list, an empty or non-string entry refuse `malformed` | MET |
| AC-5 | Tested against the real producer's output: the absent case is `tools/fixtures/orca_node_manifest_real.json` itself. Orca never emits `known_heads` today (its contract test asserts it is absent), so the present case is that manifest plus the field. Owed: regenerate a producer fixture the day Orca emits it | MET for today's producer |
| AC-6 | Every refusal code has a test whose input differs from an accepted control in one field (V-* style), and each of AC-2/3/4 has a mutant that turns its gate red | MET: GSDX_NODE 23/23; AC-4 mutants red: M1 ignore known_heads (8b776241 code) 8 gates, M2 no validation 5, M3 empty list accepted 1 |

## Done
AC-1..AC-6 MET. Orca matrix row 17 no longer has S4-22 as a blocker; its laptop ssh -L tunnel leg was
measured 2026-10-18 (4/4 MATCH, evidence C:\Users\User\Apps\rbl\d4-ev-r17t2-20261018-1828).

## Out of scope
Placement decisions (S4-23 `placement.py`), producing `known_heads` in Orca (an Orca change), capsule
bundle construction (§10), any host contact.

## Decision (Owner, 2026-10-18)
`uwcp.md` had named **KSR capabilities.json** as the artifact to extend. The source is
**orca.node-manifest/1** instead, the node manifest producer DWS phase 5 built. uwcp.md line 74 amended.

## Rollback
The adapter is a leaf with no production caller (only its test imports it); reverting this change set
returns S4-22 to AC-1..3 only.
