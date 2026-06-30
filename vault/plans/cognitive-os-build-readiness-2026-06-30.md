# Cognitive OS — BUILD READINESS MAP (PASO -1)

**Mode:** EXECUTION (architecture sealed SCS C61; this is faithful implementation).
**Date:** 2026-06-30. **Preflight HEAD:** `67c5e68`. Working tree clean of my surface
(the `M`/`??` files are hook/heartbeat output — handoffs, ceps, research, ledgers —
never `git add -A`; every commit pathspec-scoped).

## Parent-module premises — ALL VERIFIED (read, not assumed)

| Parent | Path | Real API surface | Lives where |
|---|---|---|---|
| W6 launcher | `tools/kclaude.ps1` ≡ `~/.claude/bin/kclaude.ps1` | calls `prelaunch.py`, prints advisories, never blocks | **mirrored** (repo==live now) |
| cmd shim | `~/.claude/bin/kclaude.cmd` | `powershell -File kclaude.ps1 %*` | same chokepoint |
| W6 core | `modules/wrapper/prelaunch.py` | `run(cwd,desc)->{advisories,coord,resume,known_sids}` | **repo = live** (read from skills path) |
| W4 | `modules/wrapper/repo_coordinator.py` | `coordinate()` (same-repo), `parallel_burn()` (2+ panes >8k prompts <60min) — **advisory** | repo=live |
| W5 | `modules/wrapper/cost_gate.py` | `cost_gate()`, `weekly_burn()`, `_latest_context_tokens(cwd)` (real live ctx tokens) | repo=live |
| classify | `modules/spec_gate/gate.py` | `classify_tier(desc)->TierResult(tier 0-3)` | repo=live |
| router | `modules/cost_collapse/router.py` | `route(desc)->RouteResult(NANO/MICRO/MACRO/ULTRA)` | repo=live |
| ctx state | `modules/cpc_os/context_monitor.py` | `assess(cwd,sid)->{state,signals}` (RAM+jsonl+turns; HEALTHY/COMPACT/KCLEAR) | repo=live |
| token truth | `tools/token_ground_truth.py` | `window_output(h)`, `today_output_tokens()`, `analyze()`, `iter_transcripts()` | repo=live |

**Key wiring fact:** the only surface that needs a mirror-copy to `~/.claude/bin` is
`kclaude.ps1`. Everything else (all Python) goes live the moment it's saved, because the
live launcher imports from the repo skills path. So the build keeps **maximum logic in
Python (prelaunch + a new kernel package)** and the `.ps1` delta **minimal** (read one new
`gate` field, act on it). HR-001: the mirror step is the one Owner-side/global write.

## Honest enforcement reality (CO-10 ladder, confirmed against the host)

- **Rung-3 (the only true block)** = the kclaude launch boundary. Real, but ONLY for
  kclaude-launched sessions. A bare `claude` in a Cursor terminal escapes it → **un-gated
  path** (CO-10 flags, never hides). `kclaude` IS registered (`Get-Command kclaude` →
  ExternalScript), so the gate is reachable; coverage depends on the Owner launching
  through it.
- **CO-00 primary signal is stale** right now (ctx bridge files ~3h old). The build MUST
  cross-check jsonl+turns and report `unknown` honestly — never fabricate GREEN. This is
  exactly the failure mode CO-00.III.3 names.

## Build order (confirmed, with one engineering-elegance note)

CO-08 cap (Sprint 1 N1) and the CO-00 60% gate (Sprint 2) **share the same wrapper
plumbing** (prelaunch emits a verdict → kclaude acts once). So Sprint 1 builds a single
**admission-gate** structure (`modules/cognitive_os/`) that N1 fills with the hot-session
cap; Sprint 2 adds the 60% projection into the same structure; Sprint 3+ (CO-09 loop
budget) plug into it too. One chokepoint, built once. (Woz: less code, one gate.)

| Sprint | Item | Verdict | Build | Mirror? |
|---|---|---|---|---|
| 1 N1 | CO-08 hard hot-session cap | NEW | `cognitive_os/scheduler.py` (imports W4 detectors) + prelaunch `gate` + kclaude block | yes (kclaude.ps1, minimal) |
| 1 N2 | CO-01 WU/MTok metric | EXTEND | `cognitive_os/economics.py` over `token_ground_truth` + Reality-Gate signal | no |
| 1 N3 | CO-09 loop/subagent budget | NEW | `cognitive_os/loop_budget.py` (7-part admission) → same gate | no |
| 2 | CO-00 60% projective gate | NEW root | extend the gate with effective-ctx projection | yes (kclaude, same field) |
| 3 | CO-03 router cascade | EXTEND | `cognitive_os/router.py` unifies classify_tier + route + vault/asset short-circuit | no |
| 4 | CO-02,04,05,06,07,10 EXTEND | EXTEND | one micro-commit each over named parent | mixed |

**Cap (CO-08):** default = TCO doctrine "2 hot; a 3rd frees one first" → `HOT_CAP=2`.
Hibernated sessions don't count. Hot-session count = transcripts touched within the hot
window (ground truth, global across cwds). Same-repo 2nd hot session = strong sequence
signal (W4 `coordinate()` already detects). Non-destructive ideal = hibernate-to-displace
(needs CO-07); honest MVP = **refuse-with-satisfy-instruction** (free a slot via
/compact-or-hibernate), no bypass flag — upgraded to auto-displace when CO-07 lands (Sprint 4).

## STOP cadence (anti-monolith, per the prompt + CO-00's own thesis)

PASO -1 map (here) → **N1 built+tested+wired+committed → STOP, report empirical** →
N2 → N3 → STOP #2 (full Sprint 1) → Sprint 2 (the critical 60% gate) → STOP #3 → 3 → 4 → seal C62.
Each item is its own bounded, committed, hermetically-tested unit. No single mega-turn.
