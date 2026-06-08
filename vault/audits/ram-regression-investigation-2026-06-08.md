# RAM Regression Investigation — FASE -1 Evidence

**Date:** 2026-06-08
**Question:** "Antes funcionaba con 10+ panes + Minecraft. Ahora no. ¿Qué cambió?"
**Status:** STOP #1 — diagnosis emitted, no fix built yet.
**Prior art:** `memory/feedback_ram_crash_is_claude_native_not_pp.md` (BL-RAM-OPT-001, 2026-06-04).

---

## REGRESSION TIMELINE (empirical)

| Axis | At install (≈Mar 30 → Apr 19) | Now (Jun 8) | Δ |
|---|---|---|---|
| PP first commit | 2026-03-30 (`b000e5e` v5.0) | — | ~2.3 months |
| settings.json size | 5.7 KB (Apr 19) | 16.8 KB (peak 21.8 KB Jun 4) | ~3× |
| Hook entries | 22 (Apr 19) | 28 (peak **44** Jun 4, cut to 28 by hub-fold Jun 7) | +6 net, +22 at peak |
| MCP servers (settings.json) | — | **0** | — |
| MCP servers (~/.claude.json top-level) | — | **3 DEAD**: coplay-mcp, magic-ui, notion | +3 spawn-attempts |
| Plugins | (few) | **15** (8 enabled) | grew |
| Per-prompt context injection | minimal | JIT loader ~28 KB/prompt (Apollo 15 KB + spec 13 KB) + CLAUDE.md ~40 KB | large |

### Hook-count detail across backups
- `2026-04-19` (ovo4): **22** (Pre6 Post6 Stop6 UPS2 SS2)
- `2026-05-14` (pre-abs-paths): **31** (Pre10 Post4 Stop10 UPS2 SS5)
- `2026-06-04`: **44** (Pre11 Post6 Stop9 UPS4 SS11 SE3) ← PEAK
- `2026-06-08` (live): **28** (Pre8 Post6 Stop2 UPS1 SS8 SE3) — hub-fold already cut SS+Pre 11→8

---

## CURRENT PROCESS CENSUS (Get-Process, resident WorkingSet)

| Process | Count | Total RAM |
|---|---|---|
| **claude.exe** | 16 | **6,187 MB** (261–608 MB each) |
| **node** | **0** | **0 MB** |
| **python** | **0** | **0 MB** |

`ram_guard.py`: `claude.exe working set 6.02 GB (< 20.0 GB warn)`.

**This is the decisive evidence:** at rest the PP's persistent footprint (node + python) is **0 MB**. All RAM is claude.exe native V8 heap — exactly the 2026-06-04 finding, now reconfirmed from the regression angle. No runaway 25 GB heap right now; heap scales with context × pane count.

---

## PER-EVENT HOOK SPAWN COST (measure_hook_event.py)

| Event | Spawns/event | Notable |
|---|---|---|
| PreToolUse | 8 (3 dispatcher + 5 standalone) | ~41–45 ms each |
| PostToolUse | 6 (1 dispatcher + 5 standalone) | ~46–57 ms each |
| SessionStart | 8 standalone | **`terminal-slot-recorder.js` = 4,561 ms** (SLOW) |
| UserPromptSubmit | 1 dispatcher chain | **840 ms** (SLOW) |

**Per tool call = 14 transient node spawns.** ×10 active panes = ~140 concurrent short-lived node procs during activity — CPU/transient-RAM spikes that compete with Minecraft, then self-clean (hence node=0 at rest).

**Per pane open = 8 SessionStart spawns + one 4.5 s hook.** ×10 panes opened = ~45 s of startup churn.

---

## CANDIDATE VERDICT (vs prompt A–E)

- **A) Hook proliferation** — REAL but TRANSIENT. 22→44→28 hooks. node=0 at rest → contributes **0 steady-state MB**, but causes spawn-storm spikes (14/toolcall × N panes). Manifests as stutter/lag, not OOM. Disabling hooks would free ≈0 steady-state RAM (nothing persistent to disable).
- **B) Dead MCPs** (coplay/magic/notion) — CONFIRMED configured, NOT running (node=0). Minor spawn-attempt churn at session start. ≈0 steady-state RAM.
- **C) SessionStart hub spawn** — the 4.5 s `terminal-slot-recorder.js` is the single biggest per-pane startup cost. Transient.
- **D) JIT loader I/O** — 840 ms/prompt; injected 28 KB of *irrelevant* context (Apollo GraphQL + rollback spec) into this RAM-investigation prompt. Inflates per-pane heap (the dominant consumer).
- **E) Transcripts / context** — the steady-state heap driver. claude.exe heap scales with context. CLAUDE.md ~40 KB + JIT 28 KB/prompt + 15 plugins + accumulated transcripts × 10 panes = the real "what changed since March."

**Per the prompt's own I4 rule:** no single technical candidate is a ≥500 MB steady-state delta. The 6.2 GB is native heap scaling with context × panes. → The regression is **predominantly architectural/behavioral (context size × pane count × native heap)**, with PP-attributable amplifiers (spawn churn + per-prompt context injection) that grew Mar→Jun.

---

## CONTROLLABLE LEVERS (near-zero risk, restore baseline behavior)
1. Remove 3 dead MCPs from `~/.claude.json` (coplay, magic, notion) — kills dead spawn attempts. Owner-side config edit.
2. Fix/defer the 4.5 s `terminal-slot-recorder.js` SessionStart hook — biggest per-pane startup cost.
3. Trim per-prompt JIT injection (don't inject 28 KB Apollo+spec into unrelated prompts) + CLAUDE.md at the 40 KB firewall — shrinks per-pane heap.
4. (Already shipped) hub-fold cut hooks 44→28.

These reduce churn + per-pane heap; none is a 500 MB steady-state win. The GB-scale number stays governed by `/kclear` + pane count (native, not PP-shrinkable).

---

## FIXES APPLIED (2026-06-08, Owner-approved "apply 3 controllable fixes")

### Fix 2 — terminal-slot-recorder.js SessionStart timeout (APPLIED + verified)
`modules/zero-crash/hooks/terminal-slot-recorder.js:88` — `setTimeout(...,4500)` → `800`.
Root cause: the 4,561 ms measured was the stdin-wait fallback firing every session-open. Fast path (stdin `end`) unchanged; only the fallback shrank.
Effect: ~3.7 s/pane → ~37 s less startup churn across a 10-pane open.
Verify: `node --check` OK. Hook registered at repo path (settings.json SessionStart) → edit is directly live, no mirror sync.

### Fix 3 — jit_skill_loader.py test-fixture false-trigger (APPLIED + verified)
`tools/jit_skill_loader.py:58` — added `tests, test, __tests__, fixtures, testdata` to `SKIP_DIRS`.
Root cause: the only `.graphql` in the repo is `tests/fixtures/apollo-corrupted/src/queries.graphql` (a test fixture). `tests/` was walked → repo classed as GraphQL → ~15 KB Apollo force-injected on EVERY prompt in this repo (this very investigation got it). Walk cache `jit-walk-c4e6c094bbe7.json` held the stale `found:true`; cleared.
Verify (direct import): `walk_has_graphql(PP_ROOT)=False`, `match_modules(RAM prompt)=[]` → **V-RAM-JIT-FIX3 PASS**. `py_compile` OK.
This is the steady-state heap fix: it removes ~15 KB of irrelevant per-prompt context injection in any repo whose only `.graphql` files are test fixtures.

### Fix 1 — remove 3 dead MCPs (NOT auto-applied; Owner command provided)
`~/.claude.json` top-level `mcpServers`: `coplay-mcp`, `magic-ui`, `notion` — all dead (node=0 at rest), spawn-attempted per session. `magic-ui` and `notion` embed **live credentials** (21st-dev API key, Notion token) in plaintext config.
NOT auto-applied because: (a) HR-001 (writing global config under ~/.claude/), (b) 16 live claude.exe panes → read-modify-write lost-update race on the Owner's master config, (c) credential handling.
Owner command (run when panes are idle; backs up first):
```powershell
$cj="$env:USERPROFILE\.claude.json"
Copy-Item $cj "$cj.bak.pre-mcp-purge-$(Get-Date -Format yyyyMMdd-HHmmss)"
$py='C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
& $py -c "import json,os;p=os.path.expanduser('~/.claude.json');d=json.load(open(p,encoding='utf-8-sig'));m=d.get('mcpServers',{});[m.pop(k,None) for k in ('coplay-mcp','magic-ui','notion')];json.dump(d,open(p,'w',encoding='utf-8'),indent=2);print('remaining mcpServers:',list(m))"
```
Security follow-up (HR-SECRET-003): if the Notion token / 21st-dev key were ever real, rotate them at the provider — they sat in plaintext for dead servers.

