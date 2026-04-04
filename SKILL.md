---
name: claude-power-pack
description: "Universal AI execution framework — tiered loading, zero-issue delivery, self-healing"
---

# Claude Power Pack v8.0

Universal AI execution framework. Project-agnostic. Tiered loading.

**ALWAYS read** `./parts/core.md` and `./parts/execution.md` — these contain all always-active rules.

## Token Budget

| Tier | When | Load |
|------|------|------|
| LIGHT | Fix, lookup, single file | core.md only (~800 tok) |
| STANDARD | Feature, 1-5 files | core + execution (~1600 tok) |
| DEEP | Architecture, 5+ files | core + execution + relevant sleepy |
| FORENSIC | Production risk, prior failures | all parts |

**Never load all files. Match task to tier first.**

## Sleepy Parts (load ONLY when triggered)

| Trigger | Part | File |
|---------|------|------|
| React, Next.js, Vue, CSS, frontend | F: Frontend | `parts/sleepy/frontend.md` |
| /autoresearch, competitive research | G: Autoresearch | `parts/sleepy/autoresearch.md` |
| token audit, compress, dedup, optimize | C+H+R: Token Tools | `parts/sleepy/token-tools.md` |
| load ExecutionOS, governance overlay | I: ExecutionOS | `parts/sleepy/executionos.md` |
| daemon, dispatch, omnicapture, infra, VPS | O+P+S+V+X: Infra | `parts/sleepy/infrastructure.md` |
| agent governance, AGT, OWASP ASI | W: Agent Gov | `parts/sleepy/agent-governance.md` |
| zero-crash, TTY, sandbox, process isolation | ZC: Zero-Crash | `parts/sleepy/zero-crash.md` |
| reverse engineer, video analysis, YouTube, competitor, SOTA | VRE: Video-RE | `parts/sleepy/video-re.md` |

## Quick Reference

| Trigger | Action | Source |
|---------|--------|--------|
| (every task) | OBSERVE→PLAN→EXECUTE→VERIFY→HARDEN | core.md A |
| (>1 file) | STOP after PLAN, wait approval | core.md B |
| "done"/"complete" | Zero-issue gate: compile+test+E2E | core.md D |
| (on correction) | RCA: HALT→TRACE→HEAL→FIX | execution.md K |
| (new system) | Challenge→Reverse-engineer→Decompose→Tooling | execution.md N |
| (new backend) | Elixir-First if >=2 criteria match | execution.md T |
| (>10 files) | Micro-batch, checkpoint, pause | execution.md U |
| `!kclear` | Dump memory+task, clean restart | execution.md M |
| "token audit" | Load sleepy/token-tools.md | on demand |
| "runtime check" | Load sleepy/infrastructure.md | on demand |
