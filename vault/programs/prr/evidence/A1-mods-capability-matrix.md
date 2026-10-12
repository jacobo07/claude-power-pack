# A1 -- Runtime + Mods memory/lifecycle capability matrix (Claude Code 2.1.296)

Sources: GEX44 binary fingerprint (2026-10-12 14:5x) and the engine-written Mods types
`bundled-skills/2.1.296/.../plugin-authoring/types/claude-code.d.ts` (read, not inferred).

## Runtime
- `~/.local/share/claude/versions/2.1.296` is a 257 MB ELF holding the string `Bun v1.4.3` (x2), `JavaScriptCore` (x11),
  `BUN_JSC_` (x4), and zero `v8::Isolate` / `node:internal/bootstrap`. **The engine is Bun + JavaScriptCore, not V8.**
  The memory note "native V8 heap" (feedback_ram_crash_is_claude_native_not_pp) has the engine wrong; its numbers stand.
- Consequence: `--max-old-space-size` / V8 heap flags are not the control surface. JSC/bmalloc page return behaviour
  is the open question for Root Q3, and it is measured in B, not assumed.
- Windows build assumed same engine (same version string); not fingerprinted on the laptop (host starved). Plane: GEX44.

## Mods sandbox
"The module runs in an environment of its own, with no DOM and no Node: `$` reaches everything outside it."
A mod cannot reach `Bun.gc`, `bun:jsc.heapStats` or `process.memoryUsage` of the host. A grep of the 2.1.296 types for
`rss|heap|memoryUsage|resident|privateBytes|workingSet` returns **zero** hits.

## Matrix
| Surface | Class | Evidence |
|---|---|---|
| host heap / RSS / private bytes | NOT_SUPPORTED (direct); OBSERVE only via `$.process.run` of an OS tool | no memory field in the API |
| force GC / release pages | NOT_SUPPORTED | sandbox, no Bun global |
| `$.session.messages` | OBSERVE (frozen projection) | `SessionMessage` value type |
| transcript prune/archive in place | REWRITE only through `session.compact` kept-set; sealed limits: refused headless, mixed kept-set silent no-op (CCR M2) | ccr RESUMPTION_FILE |
| `$.session.usage` / `session.measure` | OBSERVE tokens, rate limits, cost; no memory | SessionMeasureInput |
| `session.end` / `session.detach` | OBSERVE (1.5 s bound); carries `resume` for `claude --resume` | SessionEndInput |
| end / exit own session | NOT_SUPPORTED via `$` (only `turn.abort`) | session method list |
| `$.agent.spawn` / `agent.list` | START, OBSERVE | no stop/kill method |
| terminate an agent | NOT_SUPPORTED | agent method list |
| `$.mcp.connect` / `mcp.call` | START, CONTROL (call) | no disconnect method |
| MCP evict / stop | NOT_SUPPORTED: hiding a tool cannot reclaim the server | mcp method list |
| `$.process.run` / `spawn` | START (mod-owned children) | process methods |
| `$.store` / `$.state` | CONTROL (mod-owned, host-held) | reference |

## Verdict for Root Q4/Q5
Mods cannot shrink live engine state beyond what `compact` rebuilds, and cannot observe whether it did.
Same-PID rejuvenation is **not reachable from Mods**. Whether `compact` returns memory to the OS is a host
question measured in B. The terminal architecture is **physical epoch recycling under one logical session**,
supervised outside the process (kclaude wrapper / FASE A hibernate_runner), resuming with `--resume <sid>`.

## Upstream gaps (candidate primitives)
1. `$.session.memory()` -> `{ rss, heapUsed, heapCommitted, external }` (JSC heapStats) -- observation.
2. `$.mcp.disconnect(server)` -- reclaim an idle server.
3. `$.agent.stop(id)` -- end an idle agent loop.
4. `$.session.recycle()` -- seal + re-exec the same session id in a fresh process (host-owned epoch recycling).
