# Cascade Populator — schema + contract (MC-OVO-107)

**Purpose:** turn a project's source tree into a populated `vault/audits/cascade_graph.json` v2. Per-stack walker pluggability so any language can opt in. The graph is what CGAR consumes for blast-radius decisions.

## Walker contract (per-stack)

A walker is a script under `tools/` named `cascade_populate_<stack>.py` (or `.js`, `.go`, etc.) that:

1. Accepts `--project <path>` (defaults to cwd) and `--write` flag.
2. Walks the project's source tree for files matching its stack's patterns (e.g., `*.js`/`*.mjs`/`*.cjs` for JavaScript).
3. Parses each file using a real AST library — no regex shortcuts for structural logic per the v11500 Reality Shield mandate.
4. Extracts: imports/requires (edges of type `consumed_by`), function/class definitions (nodes of kind `function`/`class`), call expressions (edges of type `invoked_by`).
5. Computes `blast_radius` per node: `direct_callers` = inbound edge count, `transitive_callers` = inbound edges within N hops (default N=2).
6. Without `--write`: emits the v2 graph JSON to stdout for inspection.
7. With `--write`: merges its findings into `vault/audits/cascade_graph.json` (preserving v1 legacy block, replacing the populator's own stack-tagged subset).

## ANALYSIS_STALEMATE — the honest failure mode

Per the v11500 Reality Shield: "Si el AST no puede resolver una dependencia, el OVO debe reportar `ANALYSIS_STALEMATE`."

A walker hits stalemate when:
- A file refuses to parse (syntax error, unsupported language version) — that file gets no node, but the populator records the parse failure in the graph metadata under `_stalemates`.
- A reference can't be resolved to a known node (e.g., `require('./dynamic-' + envVar)`) — emit the node but mark the edge with `unresolved: true` and reason. CGAR treats unresolved edges as advisory, not as confirmed callers.
- A whole stack has zero files — populator exits 0 with `{"_stalemates": ["no JS files matched in this project"]}`. NOT a fake-success.

The populator's exit code:
- 0 = walked successfully (even with stalemates — they're documented, not hidden).
- 2 = argv error.
- 3 = I/O error (can't write graph file, etc.).

A walker MUST NEVER:
- Synthesize a node it didn't observe.
- Drop a stalemate silently.
- Use regex to detect what a real parser would catch differently.

## v2 graph shape after population

```json
{
  "schema": "ovo-cascade-graph-v2",
  "generated_at": "2026-04-26T...",
  "project": "claude-power-pack",
  "nodes": [
    {
      "id": "lib/license_gate.js",
      "kind": "module",
      "blast_radius": {
        "direct_callers": 3,
        "transitive_callers": 5,
        "downstream_systems": []
      },
      "_populator": "cascade_populate_js"
    }
  ],
  "edges": [
    {"from": "lib/license_gate.js", "to": "tests/license_gate.test.js",
     "type": "consumed_by", "_populator": "cascade_populate_js"}
  ],
  "_stalemates": [
    {"file": "lib/broken.js", "reason": "esprima parse error: Unexpected token (line 14)",
     "_populator": "cascade_populate_js"}
  ],
  "_legacy_v1": {"classes": [], "event_to_listeners": {}, "event_to_publishers": {}}
}
```

## Per-stack populator status

| Stack | Walker | Library | Status | Caveats |
|-------|--------|---------|--------|---------|
| JavaScript (CJS+ESM) | `tools/cascade_populate_js.py` | `esprima` (pure Python) | **shipped MC-OVO-107** | dynamic require/import strings → unresolved edges |
| TypeScript | `tools/cascade_populate_ts.py` | `tsc --listFilesOnly` subprocess OR esprima after type-stripping | **deferred** — needs Node toolchain assumption decision | TS-specific syntax (interfaces, type-only imports) needs handling |
| Python | `tools/cascade_populate_py.py` | stdlib `ast` | **deferred** | walks `import`/`from`/`def`/`call` |
| Go | `tools/cascade_populate_go.py` | `go list -json` subprocess | **deferred** | requires Go toolchain |
| Java | `tools/cascade_populate_java.py` | `javap` or javalang | **deferred** | KobiiCraft has explicit needs here |

## How CGAR consumes a populated graph

Per `CGAR_SCHEMA.md` §"Verdict caps from CGAR":

- Delta touches a populated node with `criticality: core` → cap **B**
- Delta touches a node with `transitive_callers > 50` → cap **B**
- Delta touches a `kind: migration` node → cap **REJECT**

`_stalemates` are surfaced as advisory in the OVO Council block but do not directly cap the verdict (they're "we don't know" not "we found a problem"). A high stalemate ratio (>20% of files) escalates to a probe finding.

## Re-population cadence

Populators are designed to be **idempotent and cheap to re-run**. Recommended flow:

- After significant refactors: `python tools/cascade_populate_js.py --project . --write`
- As a pre-commit hook (project's choice): same command, fail commit if `_stalemates` grow vs the prior graph.
- On every OVO cycle: NOT re-run by default — cycle reads the committed graph. Re-population is an explicit decision.

Avoiding re-population on every audit keeps the graph as a *signed-off* artifact. A delta touching a cascade node is a real signal because the graph reflects the last human-approved structure, not whatever the parser picked up this minute.

## Non-goals (this MC)

- Cross-stack cascade resolution (a JS file calling a Python service via HTTP) — out of scope; populators are stack-local.
- Runtime call graph (which edges actually fire under load) — that's RLP/replay territory, not static populator.
- Auto-criticality classification — `criticality: core` stays human-declared.
