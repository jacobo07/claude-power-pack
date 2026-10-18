---
status: DRAFT 2026-10-18 -- Owner asked for this spec ("Redactar spec S4-22"); implementation needs the Owner's "y"
opened: 2026-10-18
branch: dws/pp-rows
covers: [uwcp-s4-22, node-adapter, node-manifest-consumer, goal-node, known-heads, manifest-freshness]
extends: [uwcp.md §17-18 S4 step 22 ("22 node adapter + freshness (CPP)"), uwcp.md line 74]
consumers: [uwcp.md S4 step 23 placement.py, uwcp.md §10 capsule bundle "incremental against node-known heads"]
producer: Orca src/shared/node-manifest.ts (orca.node-manifest/1), contract test src/shared/node-manifest-schema.contract.test.ts
---

# UWCP S4-22 -- goal node adapter + freshness

## Why this file exists
`uwcp.md` names S4-22 in one line ("22 node adapter + freshness (CPP)") and one table row
("node manifest | KSR capabilities.json | EXTEND via goal/node.py adapter (measured_at, known heads,
max age)"). Nothing defined acceptance, so Orca's DWS matrix row 17 could only say "BLOCKED on UWCP
S4-22" and nobody could tell when it was unblocked. This file is that definition.

## Objective
A goal (gsd_x) can ask "what does host H look like right now?" and get either a typed, fresh view of
H or a refusal with a code. It never gets a repaired, defaulted or stale view.

## Interface (exists: `modules/gsd_x/goal/node.py`, PP 8b776241)
`read_node_manifest(doc, now_ms, max_age_ms) -> NodeView` or raises `NodeManifestError(code)`.
`doc` is a dict, JSON text or a path. Read-only: the adapter never writes, probes or contacts a host.

`NodeView`: `address`, `observed_at`, `measured` (name -> value, measured only), `unknown`
(name -> reason), and **`known_heads`** (see AC-4; not yet present).

## Acceptance criteria
| AC | Rule | State at 8b776241 |
|---|---|---|
| AC-1 | `schema` must equal `orca.node-manifest/1`; any other top-level key, or a missing `observed_at`/`node`/`measurements`, refuses `malformed` | MET |
| AC-2 | Manifest freshness: `now - observed_at > max_age_ms` refuses `stale_manifest`; `observed_at` more than 60 s ahead refuses `from_future` | MET |
| AC-3 | Measurement freshness (`measured_at`, `max_age`): each of memory/disk/vram/resident_model is `measured` (exact 5 fields, `max_age_ms` > 0, `now - measured_at <= max_age_ms` else `stale_measurement`) or `unknown` with a non-empty reason. Unknown is never read as zero | MET |
| AC-4 | **Known heads.** Absent `known_heads` -> `NodeView.known_heads is None` (unknown). Present -> a non-empty list of distinct non-empty strings, exposed as a tuple; `[]`, a non-list, a non-string or empty entry refuses `malformed`. Mirrors the producer: "Absent means unknown; an empty list is never emitted" | **NOT MET**: the key is admitted at top level, never validated, never exposed |
| AC-5 | Tested against the real producer's output, not only hand fixtures: `tools/fixtures/orca_node_manifest_real.json` is regenerated from Orca's `buildNodeManifests`, and one fixture carries `known_heads` | PARTIAL: the real fixture exists, none carries `known_heads` (Orca never emits it today) |
| AC-6 | Every refusal code has a test whose input differs from an accepted control in that one field (V-* style), and each of AC-2/3/4 has a mutant that turns its gate red | PARTIAL: 15/15 + 3 mutants for AC-1..3; AC-4 has none |

## Done
S4-22 is DONE when AC-1..AC-6 are all MET, the V-* suite is green, and the AC-4 mutant
(`known_heads` ignored again) is red. At that point Orca matrix row 17 stops citing S4-22 as a blocker.
Row 17 still also owes the laptop ssh -L tunnel leg, which is a separate, RAM-gated item.

## Out of scope
Placement decisions (S4-23 `placement.py`), producing `known_heads` in Orca (an Orca change; this adapter
must already handle both absent and present), capsule bundle construction (§10), any host contact.

## Open decision (Owner)
`uwcp.md` named **KSR capabilities.json** as the artifact to extend; the adapter consumes
**orca.node-manifest/1** instead, which DWS phase 5 built as the node manifest producer. Either
(a) orca.node-manifest/1 supersedes KSR capabilities.json as S4-22's source (recorded here, uwcp.md
line 74 amended), or (b) the adapter must also read KSR capabilities.json. This spec assumes (a)
until the Owner says otherwise; AC-1..6 do not change under (b), it adds a second reader.

## Rollback
The adapter is a leaf with no production caller (only its test imports it); reverting 8b776241 and
this file removes S4-22 with no other effect.
