---
name: sdd-os
description: SDD-OS control surface — classify a task into a tier (0-3), generate the tier-appropriate spec, scaffold a repo's spec substrate, detect spec drift, or check adoption status. Spec First. Execution Second. Validation Always. Works in ANY repo, not just the Power Pack. Backed by modules/sdd_os/ and tools/sdd_os_cli.py. Source. SDD-OS PARTE I; activation sealed BL-SDD-ACT-001.
---

# /cpp-sdd-os — Spec-Driven Development OS control surface

**Core law: Spec First. Execution Second. Validation Always.**

SDD-OS classifies every task before execution and refuses Tier 2+ work
without a spec that actually covers that task. It runs automatically on
every prompt via `tools/jit_skill_loader.py::_sdd_os_activation_inject`.
This command is the manual surface for the same engine.

## Usage

```bash
# Which tier is this, and does a spec cover it?
python tools/sdd_os_cli.py classify "add a billing endpoint"

# Generate the tier-appropriate spec skeleton (non-destructive)
python tools/sdd_os_cli.py spec "add a billing endpoint" --repo <path>

# Give a repo its SDD-OS substrate (ARCHITECTURE.md, ROADMAP.md, specs/)
python tools/sdd_os_cli.py scaffold [--repo <path>] [--dry-run]

# Which specs have stopped describing the code?
python tools/sdd_os_cli.py drift [--repo <path>]

# Adoption state of a repo
python tools/sdd_os_cli.py status [--repo <path>]

# Roll the substrate out to many repos at once
python tools/sdd_os_cli.py rollout --repos-file vault/sdd_os/active_repos.txt [--dry-run]
```

Exit codes: `0` clean · `1` action required · `2` usage error.

## Tiers

| Tier | Name | Required before the first code edit |
|---|---|---|
| 0 | Micro | inline mini-spec: objective, scope, acceptance |
| 1 | Standard | brief spec: + impact map, regression risk |
| 2 | Feature / System | **written**: PRD + Architecture Spec + AC + rollback |
| 3 | Strategic / Platform | Tier 2 set + governance, cross-repo, migration, kill switches |

At Tier 2+, executing without a spec is prohibited (PARTE I §4).
Per-tier PRD templates: `/prd-tier0` … `/prd-tier3`.

## How a spec covers a task

Front matter declares it:

```yaml
---
title: Waitlist gate rework
covers: [waitlist, signup-flow, gate]
tier: 2
---
```

A task binds when its tokens contain **every** sub-token of at least one
`covers` entry. **A spec with no `covers` binds to nothing** — a repo full
of old plan files does not satisfy the gate. That was the defect
(TUA-X passed on 50 unrelated files, KobiiCraft on 131).

## Doctrine

`governance/SDD_OS_GOVERNANCE.md` · root-cause record
`SDD_OS_REALITY_REPORT.md` · dataset `vault/knowledge_base/sdd_os/`.
Done-gate: `python tools/test_sdd_os_activation.py`.
