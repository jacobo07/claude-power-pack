# JIT Reference-Correlator — Canonical Activation Procedure

> Sealed 2026-05-19. Permanent procedure for wiring
> `tools/jit_ref_correlate.py` into Stop. Replaces the earlier (wrong)
> raw-`settings.json` instructions that lived in the source comment.

## Why this lives in vault/standards, not a code comment

A wrong activation comment is a deferred bug — the next Owner who
follows it spends an hour wondering why `jit_refs_*.jsonl` never
appears. Reality-Contract gate: the canonical procedure must be the
*one place* the operator looks, and it must match the host's real
registration mechanism. The code carries a 6-line pointer; the
detail lives here.

## Why a raw settings.json Stop entry will NOT work on this host

On Windows, registering ≥3 separate `type:"command"` hooks on one
event makes Claude Code spawn N near-simultaneous shell wrappers; the
Git-Bash msys2 mount-table init collapses (`add_item("\??\…","/") errno
1`) and the hooks never run. The durable mitigation collapses every
event into ONE dispatcher process that runs sub-hooks sequentially via
`spawnSync(shell:false)`. For Stop specifically, the live settings is:

```jsonc
// ~/.claude/settings.json — hooks.Stop (the dispatcher entry, not the sub-hook list)
{ "type": "command",
  "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/hook-dispatcher.js\" --event=Stop-chain",
  "timeout": 300,
  "statusMessage": "Stop chain (N hooks, fork-storm-safe)" }
```

Adding a second `type:"command"` entry alongside it would re-introduce
the fork-storm. **Therefore the correlator is NOT registered in
settings.json — it is registered inside the dispatcher's own
`CHAIN_MAP['Stop-chain']` array.**

## The exact line to insert

File: `~/.claude/hooks/hook-dispatcher.js`
Find the existing `const CHAIN_MAP = { 'Stop-chain': [ … ], };` block.
Add this as the **last** array entry (so all blocking gates and
critical hooks run first; telemetry is end-of-chain by design):

```js
{ exe: PY_EXE, script: '../skills/claude-power-pack/tools/jit_ref_correlate.py', timeoutMs: 8000 },
```

### Why each field is what it is

| Field | Value | Reason |
|---|---|---|
| `exe` | `PY_EXE` | python.exe — the correlator is Python (matches the sibling `context-watchdog.py` entry). |
| `script` | `../skills/claude-power-pack/tools/jit_ref_correlate.py` | script paths are resolved relative to `~/.claude/hooks/`; `../skills/…` reaches `~/.claude/skills/…`. |
| `timeoutMs` | `8000` | Reads a transcript JSONL + globs telemetry; 8 s is conservative (matches `vault-heartbeat.js`). |
| **no `block: true`** | omitted | A telemetry correlator must NEVER wedge Stop. Without `block`, a failure is logged and the chain continues — fail-open by structural design, not by `try/except` luck. |
| **position** | last | Blocking gates (`zero-issue-gate.js`, `scaffold-auditor.js`) run first; the correlator only writes telemetry, so it never has to block downstream hooks. |

## Post-apply verification gate (Owner runs after editing)

These four checks define DONE. All four green or the activation is not
considered live.

### 1. Dispatcher still parses

```powershell
& "C:\Program Files\nodejs\node.exe" -e "require('C:/Users/User/.claude/hooks/hook-dispatcher.js')" 2>&1
```

No output (or a clean `require` return) = the new array entry is
syntactically valid. Any `SyntaxError` / `Unexpected token` surfaces
here BEFORE a real Stop fires; abort and re-check the comma/braces.

### 2. Cold-load boundary acknowledged (BL-0067)

The dispatcher is read **once at session start**. The new entry is
**inert until the next `/restart`**. Do not expect it to fire in the
session where you applied the edit — that is by design, not a bug.

### 3. Live proof — `jit_refs_<sid>.jsonl` appears after one real Stop

After `/restart`, run a turn that injects at least one JIT module
(any GraphQL/Apollo prompt will do — easiest: a prompt with
`>5 learnings` like a /compound run, but any real Stop suffices).
Then:

```bash
ls ~/.claude/skills/claude-power-pack/vault/telemetry/jit_refs_*.jsonl
```

A new `jit_refs_<sid>.jsonl` with a valid `ref_ratio` float in `[0,1]`
== loop closed. **Zero `jit_refs_*` files after a real Stop ==
correlator never fired**; do not declare the closed loop until this
file exists with real data. (Mistake #17: static analysis is not
runtime evidence.)

### 4. Telemetry join is real, not phantom

```bash
python -c "import json,glob; rows=[json.loads(l) for f in glob.glob('vault/telemetry/jit_refs_*.jsonl') for l in open(f) if l.strip()]; print(len(rows), 'rows; sids:', sorted({r['session_id'] for r in rows}))"
```

The `session_id` in those rows must match the RAW Claude Code
`session_id` written by `jit_skill_loader.py:_telemetry` into
`jit_usage_*.jsonl`. If the sids diverge, the join is broken (see
session_lessons Addendum 12 / Mistake #6 sid mismatch). Treat a
mismatch as a defect, not a curiosity.

## Rollback (if anything misbehaves)

The change is one array entry. Remove that single line from
`CHAIN_MAP['Stop-chain']`, `/restart`. The chain returns to its prior
shape; no other state is touched. (The correlator never mutates
`settings.json`, never writes outside `vault/telemetry/`, and
fail-opens on every error — rollback is purely cosmetic.)

## Status as of seal

- Capability: agent-built + standalone-verified (4-case gate, ratio
  2/3 on a synthetic transcript, zero settings.json mutation).
- Empirical loop closure: already observed once via a parallel-pane
  session — `vault/telemetry/jit_refs_7b7cd78e….jsonl` carries a real
  `ref_ratio=0.0` that drove the `graphql-operations` profile tighten
  (`d251ac9`). So the correlator + loop are proven; the only
  permanent Owner step is making the dispatcher entry above survive
  every `/restart`.
- Cross-reference: BL-0067 (cold-load), BL-0069 (JIT activation law),
  Authorization Boundary in `knowledge_vault/core/apex-completion-standard.md`.
