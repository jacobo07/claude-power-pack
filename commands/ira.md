---
name: ira
description: "Alias for /investment-ready-audit. Project-agnostic Series-A / Seed / Angel / Not-Investable verdict based on 5 axes — scalability, resilience, traceability, zero-stub, ROI-wiring."
allowed-tools:
  - Read
  - Bash
argument-hint: "[<N|id>]   — optional: drill into subsystem #N or by id"
---

# /ira — Investment-Ready Audit (alias)

Short-form invocation of `/investment-ready-audit`. Same engine, same axes, same verdict thresholds. Use this for quick invocations; use the full name for discoverability in command-palette lookups.

## Run

Summary:

!`node ~/.claude/skills/claude-power-pack/lib/investment_ready.js --project .`

Drill-down (`$ARGUMENTS` = `<N>` or `<id>`):

!`node ~/.claude/skills/claude-power-pack/lib/investment_ready.js --project . $ARGUMENTS`

## Five axes (recap)

1. **Scalability** — toolchain + Docker/k8s/CI/config signals
2. **Resilience** — language-appropriate error handling coverage
3. **Traceability** — logging-call coverage across runtime files
4. **Zero-Stub** — Reality-Contract placeholder density (weight 3×)
5. **ROI-Wiring** — producer-consumer connectivity (weight 2×)

## Verdict thresholds

| Band | Score | Label |
|------|-------|-------|
| 🏆 | ≥ 85 | SERIES A READY |
| 🌱 | 75–84 | SEED READY |
| 🪽 | 60–74 | ANGEL / F&F |
| ❌ | < 60 | NOT INVESTABLE |

## Exit summary (Claude must emit inline)

Print the full output block from the script — headline, five-axis bar grid, per-subsystem table, and a one-line next-step naming the weakest axis. Do **not** collapse the table behind `+N lines (ctrl+o to expand)`; paste it verbatim so the investor (or Owner) can read it at a glance.
