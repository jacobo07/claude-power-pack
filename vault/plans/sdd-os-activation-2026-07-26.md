---
title: SDD-OS Automatic Activation — PLAN MODE
date: 2026-07-26
status: STOP #1 delivered inline; awaiting Owner approval before any execution
mode: PLAN MODE (not ULTRA-PLAN) — justified in SDD_OS_REALITY_REPORT.md § F
source: Dataset SDD-OS 1.txt (sha256 a6c8f6bcd83a8230) via vault/knowledge_base/sdd_os/
reality_report: ../../SDD_OS_REALITY_REPORT.md
---

# SDD-OS Automatic Activation

Institutional backup of the inline plan (PARTE I §13: the Owner approves inline; the
plan file is a backup, never the substitute).

## Root causes being closed

- **RC-1** `~/.claude/CLAUDE.md` has zero SDD-OS content → the agent is never told to classify.
- **RC-2** `check_spec_gate` accepts `vault/plans/*.md`, so 27 repos (incl. TUA-X 50,
  KobiiCraft 131) pass forever on unrelated files. No task↔spec binding.
- **RC-3** `sdd_tier` is advisory at slot 10/13 under a 3-advisory cap; generates nothing;
  zero production firings on record.
- **RC-4** No scaffold on first contact with a repo; no spec-drift repair.

## Scopes

| Scope | Closes | Deliverable |
|---|---|---|
| S1-A | RC-1 | Explicit activation criteria block for global `CLAUDE.md` (+ PP mirror). HR-001: Owner registers. |
| S1-B | RC-2 | `spec_binding.py` — task↔spec relevance, not repo-has-a-file. Narrows the gate, fail-open. |
| S1-C | RC-3 | Tier-proportional pre-execution gate that *generates* the minimal spec, not a nudge. |
| S1-D | RC-4 | Non-destructive scaffold on first contact + spec-drift check post-change. |
| S1-E | — | Apply to active repos; generate initial Architecture Specs. |

## Open decision escalated to the Owner

**OD-1 — how does a spec bind to a task?** Options: (a) freshness+keyword overlap
scoring, (b) explicit front-matter `covers:` declaration, (c) per-task spec file keyed
by a task slug. Affects every repo; chosen before S1-B is written.

## Done-gate

`tools/test_sdd_os_activation.py` — V-SDDOS-CLAUDE-MD, V-SDDOS-TIER-CLASSIFICATION,
V-SDDOS-SPEC-BEFORE-CODE, V-SDDOS-SPEC-UPDATE, V-SDDOS-SCAFFOLD, V-SDDOS-ACTIVE-REPOS.
All ×3 hermetic. Plus: `python modules/liveness/reachability.py` clears `modules/sdd_os/*`
and `pp_agents/signals/sdd_tier` by WIRING, not by declaring.

## UKDL to seal

T-SDD-OS-IMPLICIT-ACTIVATION-001, PR-SDD-OS-SPEC-BEFORE-EXECUTION-001,
T-SDD-OS-SPEC-DRIFT-001 — plus the finding this scan produced:
T-SDD-OS-GATE-SATISFIED-BY-UNRELATED-ARTIFACT-001.
