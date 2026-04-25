# Cascade Graph + Adversarial Replay (CGAR) — schema

**File:** `vault/audits/cascade_graph.json` (per project, schema v2)
**Consumer:** `tools/forensic_probes.py cgar_check()` + `tools/cascade_query.py`
**Goal:** model causal blast-radius of a delta and (eventually) replay real production inputs against the post-delta sandbox.

## Why this exists

A delta touches `auth.middleware.ts`. Static OVO sees the file changed and grades the delta on its own merits. It does NOT know that 47 endpoints invoke this middleware, that one of those endpoints is the payment-webhook handler, and that the payment-webhook handler is on a hot path with 1000 req/s. CGAR makes the blast radius first-class evidence.

## Schema v2 — backward-compatible extension of v1

v1 (commit `c88a602`) shape:
```json
{
  "schema": "ovo-cascade-graph-v1",
  "generated_at": "...",
  "classes": [],
  "event_to_listeners": {},
  "event_to_publishers": {}
}
```

v2 adds **`nodes`** and **`edges`** as the canonical surface, and **deprecates** `classes` / `event_to_*` (still readable for back-compat):

```json
{
  "schema": "ovo-cascade-graph-v2",
  "generated_at": "2026-04-25T18:00:00Z",
  "project": "claude-power-pack",
  "nodes": [
    {
      "id": "lib/license_gate.js",
      "kind": "module",
      "blast_radius": {
        "direct_callers": 3,
        "transitive_callers": 5,
        "downstream_systems": ["installer-sh","installer-ps1","tests"]
      }
    }
  ],
  "edges": [
    {"from": "lib/license_gate.js", "to": "tests/license_gate.test.js", "type": "consumed_by"},
    {"from": "lib/license_gate.js", "to": "install.sh", "type": "invoked_by"},
    {"from": "lib/license_gate.js", "to": "install.ps1", "type": "invoked_by"}
  ],
  "_legacy_v1": {
    "classes": [],
    "event_to_listeners": {},
    "event_to_publishers": {}
  }
}
```

## Node fields

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | stable identifier (usually relative file path; can also be class FQN, event name, etc.) |
| `kind` | string | `module` / `class` / `function` / `event` / `endpoint` / `migration` |
| `blast_radius.direct_callers` | int | count of distinct identifiers that directly reference this node |
| `blast_radius.transitive_callers` | int | count after walking the edges N hops (default N=2) |
| `blast_radius.downstream_systems` | string[] | named systems that depend on this node (free-form labels the project chooses) |

Optional node fields:
- `criticality` — `low` / `medium` / `high` / `core` (project-declared)
- `last_observed_traffic` — counter snapshot if available

## Edge types

| Type | Direction semantics |
|------|---------------------|
| `consumed_by` | `to` reads/imports `from` |
| `invoked_by` | `to` calls `from` |
| `subscribed_by` | `to` listens to `from` (event/topic) |
| `derived_from` | `to` is a derivative artifact of `from` (build product, generated code) |

## Verdict caps from CGAR (cascade-only; replay is separate)

| Finding | Cap |
|---------|-----|
| Delta touches a node with `criticality: core` | **B** unless the response addresses each downstream_system explicitly |
| Delta touches a node with `transitive_callers > 50` | **B** unless replay is configured AND ran clean |
| Delta touches a `migration` node without explicit reversibility note | **REJECT** |

## Adversarial replay (deferred — schema only this session)

Future addition (separate MC): `vault/audits/replay_log/` directory containing the last N production events. CGAR replay step runs them against the post-delta build in a sandbox and diffs the output. Schema for the replay event:

```json
{"iso_ts":"...","event_type":"http.request","input":{"method":"POST","path":"/x","body":{...}},"observed_output":{"status":200,"body":{...}}}
```

When replay is configured (directory exists with samples) and clean, verdict caps from blast-radius alone are relaxed by one tier (B → keep open, REJECT → B). When replay diffs against expected output, that's a finding regardless of static delta cleanliness.

## States

- **CONFIGURED + clean**: cascade graph is populated AND no delta-node hits a cap rule.
- **CONFIGURED + findings[]**: graph exists, delta hits one or more cap rules.
- **NOT_CONFIGURED**: cascade graph is empty (`nodes: []`) or v1 placeholder → advisory; no cap. *This is the current power-pack state.*

## How a project opts in

1. Provide a populator (stack-specific) that walks the codebase and writes nodes + edges. Power-pack will add a Python AST populator in a future MC; other projects need their own walker.
2. Run the populator at install/build time, append to `vault/audits/cascade_graph.json`.
3. Optional: declare `criticality` for known-core nodes manually.
4. Optional: drop production event samples into `vault/audits/replay_log/` to enable replay.

## Non-goals (this MC)

- Auto-population from source — populators are stack-specific work.
- Adversarial replay execution — schema only this MC; runtime is a separate session.
- Cross-project cascade graphs — each project owns its own graph.
