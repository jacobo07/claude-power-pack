---
name: investment-ready-audit
description: "Project-agnostic Investment-Ready Audit (IRA) — scores current repo on Scalability / Resilience / Traceability / Zero-Stub / ROI-Wiring and emits a Series-A / Seed / Angel / Not-Investable verdict."
allowed-tools:
  - Read
  - Bash
argument-hint: "[<N|id>]   — optional: drill into subsystem #N or by id"
---

# Investment-Ready Audit — /investment-ready-audit  (alias `/ira`)

Project-agnostic Due-Diligence gate. Same discovery engine as `/audit-all`, but lifts the raw benchmarks into the five axes that seed / Series-A reviewers actually score against. Works on any repo the command is invoked from (TUAX, LuckyFly, KobiiCraft, KobiiSports Resort, SaaS frontends, anything with a manifest).

## Five axes

| Axis | What it measures | Source |
|------|------------------|--------|
| **Scalability** | Toolchain presence + deployability signals (Dockerfile, k8s, CI, `.env.example`) | `lib/score.js` env-mapping + filesystem probes |
| **Resilience** | Fraction of runtime files that contain language-appropriate error handling (try/except, try/catch, `if err != nil`, `Result<>/?`, `rescue`, …) | `lib/investment_ready.js` heuristic |
| **Traceability** | Fraction of runtime files emitting log calls (`logger.`, `log.`, `console.log`, `println!`, `Logger.info`, etc.) | `lib/investment_ready.js` heuristic |
| **Zero-Stub** | Reality-Contract placeholder density (`TODO:`, `FIXME:`, `Coming Soon`, `NotImplementedError`, `@stub`, …) | `lib/score.js` completion, weight 3× |
| **ROI-Wiring** | Producer-consumer connectivity — every new runtime file should be referenced by another file in the repo. Inverted drift score. | `lib/score.js` drift, weight 2× |

Overall = weighted mean (Zero-Stub 3×, ROI-Wiring 2×, others 1×).

## Verdict thresholds

- `≥ 85`  🏆 **SERIES A READY**  — investable, technical integrity proven
- `75–84` 🌱 **SEED READY**       — ship a bit more Zero-Stub + Resilience
- `60–74` 🪽 **ANGEL / F&F**       — early-stage, fixable gaps
- `< 60`  ❌ **NOT INVESTABLE**    — placeholders or disconnected code dominate

## Run

Summary (no argument):

!`node ~/.claude/skills/claude-power-pack/lib/investment_ready.js --project .`

Drill-down (pass `$ARGUMENTS` — a subsystem index like `2` or an id like `root`):

!`node ~/.claude/skills/claude-power-pack/lib/investment_ready.js --project . $ARGUMENTS`

## Relationship to other audit commands

- `/audit-all`  — developer-facing health score (edit-thrashing, drift, completion, env).
- `/ira`        — investor-facing readiness score (scalability, resilience, traceability, zero-stub, ROI).
- `/ovo-audit`  — forensic delta review + 5-advisor Council verdict with push-gate.

Order of use on a fresh repo: `/audit-all` → fix reds → `/ira` → fix orange axes → `/ovo-audit` before merging.

## Exit summary (Claude must emit this inline — don't summarize away the table)

Render these four blocks **inline in the response** (do not collapse behind "+N lines"):

1. **Headline** — one line with overall %, progress bar, verdict emoji + label.
2. **AXES (repo-wide mean)** — the five-axis progress-bar block exactly as printed by the script.
3. **SUBSYSTEMS TABLE** — the full per-subsystem row grid (id, stack, each axis %, overall, verdict).
4. **Next-step** — one sentence naming the weakest axis and the drill-down command to run (`/ira <N>`).
