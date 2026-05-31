# jit_skill_loader lazy / fast-path plan

**Generated:** 2026-05-31 from `tools/bench_jit_loader.py` + `tools/_profile_step.py`.
**Hypothesis going in:** heavy top-level imports cause the first-prompt lag.
**Reality from the profile:** the heavy imports were already lazy. The slow path
is the decorator chain + tiktoken cold load + Python subprocess startup.

## Empirical numbers (warm in-process, ms)

| Step | First call | Second call | Notes |
|---|---|---|---|
| `_walk_has_graphql` | 0.8 | 0.3 | Already cached via 1h disk cache (BL-walk-cache, applied 2026-05-31). |
| `_active_spec` | 1.0 | 1.0 | Cheap glob, no cache yet. **Action**: skip — not a bottleneck. |
| `_tok` (tiktoken first hit) | **238.9** | 0.1 | Tiktoken BPE load is heavy but already lazy; only fires on discovery tier. Not in hot path for empty / summary tier. |
| `_match_modules` | 0.6 | 0.2 | Already cheap. |
| `import proactive_dispatcher` | **26.6** | n/a | Decorator-side; pays per subprocess. |
| `dispatch_to_additional_context` | **39.1** | n/a | Runs even when no signal will fire — wasted cost. |
| `run()` warm in-process | 81-137 | 135-137 | Steady-state run cost without subprocess overhead. |
| End-to-end subprocess | **475-1036** | 475-1036 | What UserPromptSubmit actually pays. |

## Import time -X breakdown (top self-time, microseconds)

| us | module |
|---|---|
| 7335 | `tools.jit_skill_loader` itself |
| 4975 | `_hashlib` |
| 4105 | `site` |
| 3000 | `urllib.parse` |
| 1971 | `encodings` |
| 1875 | `enum` |
| ... | (no single import > 8 ms self-time) |

No import is fat enough to deserve a lazy-load rewrite. The total cold
import is ~20-50 ms — Python startup itself dominates.

## What is actually slow

The 475-1036 ms end-to-end subprocess cost decomposes as:

| Phase | Cost (ms) | Fixable? |
|---|---|---|
| Python interpreter startup | 20-50 | No — OS-level. Pre-warm masks this. |
| Module imports (stdlib + jit) | 20-50 | No — already minimal. |
| Subprocess + I/O scheduling variance | 100-500 | No — Windows scheduling noise. |
| `_pp_proactive_inject` decorator | 65 | **Yes** — pre-check before import+dispatch. |
| `_tco_inject_routing` JSON load | ~5 | Trivial. |
| `_tis_log_call` log read+append | ~10-30 | Marginal — keep batching. |
| `run()` body (match+walk+spec+read SKILL.md) | 80-150 | Partial — _active_spec one-call cache. |
| Subprocess wall variance | 50-200 | No — OS scheduler. |

## Concrete fixes (the only ones that actually pay)

### F1 — `_pp_proactive_inject` cheap pre-check (highest win per LOC)
**Before:** wrapper imports `proactive_dispatcher` and calls
`dispatch_to_additional_context` on every prompt — 65 ms wasted per call when
no agent will fire.
**After:** read a single small status file (or check `tis` log size) BEFORE
importing the dispatcher. If no signal hint, return immediately. The dispatcher
itself only fires for ~5% of prompts in steady state (per BL-PROACTIVE-001
throttle + signal threshold contract).
**Expected gain:** ~50-60 ms per call (~10% of end-to-end).

### F2 — `_active_spec` one-call disk cache (small win, cheap)
**Before:** `iterdir` over `.specify/specs/` and `vault/specs/` on every call.
**After:** mirror the walk-cache pattern — sha1(cwd) keyed JSON at
`STATE_DIR/jit-spec-<sha>.json` with 5-min TTL (specs change inside a working
session, so 5 min not 1 h).
**Expected gain:** ~1 ms warm; ~5-10 ms on slow filesystems / cold OS cache.

### F3 — SessionStart pre-warmer (real first-prompt fix)
**Before:** the first prompt pays Python interpreter cold start + OS file
cache cold + Python bytecode discovery — all on the user's wall clock.
**After:** detached `python jit_skill_loader.py` with `PP_WARM_RUN=1` on
SessionStart. Python interpreter warms the OS file cache for the .py file,
the .pyc bytecode files get touched, and the walk cache + spec cache get
primed for the user's cwd. By the time the user types, the subprocess
spawn finds everything in the page cache.
**Expected gain:** ~200-400 ms on the FIRST prompt of a new pane (the one
the Owner specifically complained about). No effect on subsequent prompts
(which already enjoy the warm page cache from the previous prompt).

### F4 — Honest non-fixes (documented so future-me doesn't try again)
- **Lazy-load tiktoken**: already lazy. Cold load is 240 ms but only on
  discovery tier (rare path).
- **Cache model-routing.json across processes**: subprocess boundary kills
  per-process cache. Moving to a parsed pickle wouldn't help — the JSON is
  ~3 KB, parse is ~1 ms.
- **Defer decorator imports**: already `import functools as _ft` inside
  the wrapper bodies. Nothing else to defer at module top.
- **Rewrite to a long-lived daemon**: would help but breaks the
  UserPromptSubmit hook contract (it expects a one-shot subprocess that
  reads stdin and writes stdout). Out of scope.

## Net plan

- **M2** = implement F1 + F2 (lazy proactive dispatch + spec cache).
- **M3** = telemetry already 1 write per call; leave alone, but consolidate
  the two `_save_state` + `_telemetry` writes if they target the same dir.
- **M4** = implement F3 (SessionStart pre-warmer).

Expected end-to-end improvement: 50-60 ms (F1) + 200-400 ms (F3, first
prompt only). On a fresh pane's first prompt: ~250-460 ms saved (target
≥ 20 % from 475-1036 baseline = ≥ 95-207 ms saved → MET).
