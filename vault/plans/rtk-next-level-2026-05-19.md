# RTK Next Level — Cycle Plan (2026-05-19)

> /ultra ONESHOT Phase 5 — corrected scope after 1 architecture probe
> (claude-code-guide) + 1 forensic auditor pass (11 gaps). Owner-accepted
> for autonomous execution.

## Pre-state (verified, not asserted)

- RTK live: `~/.claude/bin/rtk.exe` v0.40.0, PreToolUse(Bash) hook
  registered to repo path `modules/rtk-core/rtk-rewrite.js`. Pinned-SHA
  DONE gate (`tools/verify_rtk_fusion.py`) reproducibly ≥77% (80.2% ×2,
  af8da66).
- Adoption telemetry shipped (parallel stream): every `rtk-rewrite.js`
  call appends one row to `vault/telemetry/rtk_<sid>.jsonl` —
  `{ts, session_id, rtk_exit, rewritten, cmd_len_pre, cmd_len_post,
  cmd_first_token}`. The row never claims per-call savings (the command
  hasn't run yet at PreToolUse); `budget_monitor.py` (incoming) is
  designed to combine these adoption counts with the static benchmark.

## Drops (with empirical evidence — not silent)

| Vector | Reason |
|---|---|
| V1 multi-tool RTK | claude-code-guide cited Claude Code docs: `PostToolUse` cannot mutate the `tool_result` sent to the LLM; only `additionalContext` annotation or `decision:block` suppression. Every existing PostToolUse hook in `~/.claude/hooks/` uses `additionalContext`, none mutate `tool_response`. Compressing Read/Write/Edit/TodoWrite output is architecturally impossible. |
| V2 RTK×JIT semantic coordination | `strings rtk.exe \| grep RTK_PROFILE` = empty; `RTK_PROFILE=x rtk rewrite "git status"` byte-identical to unset. `rtk rewrite --help` exposes no profile flag. The env-var coordination would be a config file that does nothing — Reality Contract violation. The post-processor alternative (rewriting rtk's emitted command string post-hoc) is a new design, deferred to its own cycle. |
| PASO 0 (tool-cost ranking) | Orphaned by V1 drop. |
| V2.1 active-profile.json / V2.2 / V2.3 profile_flags.json | Orphaned by V2 drop. |

## Final scope — 2 vectors, ~4 files

### V3 — Real-corpus benchmark

**V3.1** `tools/rtk_corpus.py` (new)
- Source: `rtk discover --format json` (per-cmd, JSON-clean — auditor-verified alternative to dead-end `rtk gain --format json`).
- **Two-tier partition** per corpus entry (Gap 6 fix):
  - `tier: "heavy"` — raw_tokens ≥ 200 AND historical avg savings ≥ 30%.
  - `tier: "light"` — the rest. Tracked but exempt from the cliff.
- **Static variance classifier** (Gap 7 fix) — explicit map, no heuristics:
  ```
  STATIC_CLASSIFIER = {
    "git log": "sha-pin",          "git status": "skip",
    "git diff": "sha-pin-pair",     "git branch": "skip",
    "ls": "skip",                   "rg": "include",
    "grep": "include",              "cat": "include",
    "tree": "include",              "find": "include",
    "docker ps": "skip",            "pytest": "include",
    "cargo test": "include",        "npm test": "include",
  }
  ```
  Unknown commands → skip with logged reason; never included in deterministic corpus.
- Output: `tests/fixtures/rtk_corpus.json` — deterministic (sorted by frequency desc, tier-partitioned). Includes `pin_strategy` per entry.

**V3.2** `tools/verify_rtk_fusion.py` (edit, `--corpus` flag)
- Iterates the **heavy** set, computes weighted-avg reduction.
- Gate: `heavy_weighted >= 80% AND each heavy cmd >= 60%`.
- **Light** set executed and logged but exempt from cliff; only a "did not regress to negative" assertion (each light cmd: comp ≤ raw, no inflation).
- Existing single-cmd pinned-SHA mode (`af8da66`, ≥77%) unchanged.
- Honest failure messages distinguish "binary missing" vs "cmd not in corpus" vs "real regression".

### V4 — Thin RTK savings exporter

**V4** `tools/rtk_savings_export.py` (new)
- Inputs: (a) **existing** `vault/telemetry/rtk_<sid>.jsonl` rows (parallel-stream adoption telemetry — aggregate `cmd_first_token` frequencies); (b) `rtk gain --format json` (summary aggregates).
- Schema (v1.0):
  ```json
  {
    "schema_version": "1.0",
    "ts": <epoch_s>,
    "session_id": "<from CLAUDE_SESSION_ID env, else hostname-pid-startts>",
    "rtk_summary": { "total_commands": N, "saved_tokens": K, "saved_pct": P },
    "adoption": { "rewrites": N, "passthroughs": M, "by_cmd": [{cmd,count}, ...] },
    "source_note": "rtk_summary from `rtk gain --format json`; adoption.by_cmd from vault/telemetry/rtk_<sid>.jsonl row aggregation"
  }
  ```
- session_id precedence (Gap 9 fix): `CLAUDE_SESSION_ID` env → `hostname-pid-startTimeMs`. **Never** cwd-hash (collides under parallel panes).
- Decoupled — any future `budget_monitor.py` consumes via this schema; never reaches into rtk internals.
- File: `vault/telemetry/rtk_savings_<sid>.json` (one per session, idempotent overwrite within a session).

## Cross-cutting (in execution)

- **Pre-push scope check** (Gap 10 fix): `git diff --name-only HEAD` ∩ declared-file-list `{rtk_corpus.py, verify_rtk_fusion.py, rtk_savings_export.py, plan.md, session_lessons.md, tests/fixtures/rtk_corpus.json}` — any extra path → STOP, list it, ask Owner. Prevents scope-bleed at push.
- **Live-hook edit pattern** (Gap 8 — not used this cycle since `rtk-rewrite.js` isn't edited; documented in lessons for next time): write `<file>.next` → `node --check` → verify → `os.replace`. Atomic, reversible.

## Cycle gates (all must pass; honest failure halts)

| Gate | Pass condition |
|---|---|
| node --check on edited JS | exit 0 |
| `python tools/verify_rtk_fusion.py` (pinned single-cmd) | ≥77% deterministic (unchanged) |
| `python tools/verify_rtk_fusion.py --corpus` | heavy weighted ≥80% AND each heavy ≥60%; light set non-regressive |
| `python tools/rtk_savings_export.py` | emits valid JSON; schema fields present; `saved_pct` within ±1% of `rtk gain` |
| OVO `/ovo-audit` | A or A+ on the clean delta |
| `git rev-list origin/feat/rtk-compressor-fusion..HEAD` | 0 (synced after push) |

## Reality Contract for this cycle

The corpus thresholds (≥80% heavy weighted, ≥60% per-heavy) are
measured numbers reported AS measured. If the real corpus yields 78%
heavy-weighted: the verdict is 78%, not 80%. **No floor is enforced
that the measurement can't defend.** The light-set non-regression
clause is the honest fallback for commands rtk doesn't compress —
they're tracked but don't sink the gate.

Sealed for execution 2026-05-19. Owner Accept: "write file + execute".
