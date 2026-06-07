# Sovereign Epics Roadmap (PP Dataset v2 Parts XIX-XXIII)

Status: **ALL DEFERRED 2026-06-07** by the SCS C42 ROI gate (triage:
build-everything follow-up). None passed "solves a problem the Owner has
TODAY". Each entry below carries an explicit **activation criterion** --
the concrete condition that flips it from DEFER to BUILD.

The 5 epics form a dependency chain (XX needs XIX -> XXI -> XXII -> XXIII),
all XL, all targeting autonomous multi-agent fleets across many repos --
a scenario the solo, <=2-pane Owner does not operate today. Building any
one in isolation yields an orphan (its dependents don't exist).

---

## PART XIX -- Sovereign Stack Governance Network (SSGN)
- **Purpose:** distributed governance mesh -- propagate Hard Rules,
  Process Rules, Traps, Secret Firewall, Output Contracts across every
  repo in the stack as policy-as-code.
- **Verdict:** DEFER. Today the global `~/.claude/CLAUDE.md` +
  `verify_global_mirrors` already propagate the core rules; the write
  side (mutating other repos' config) is HR-001 Owner-side.
- **Activation criterion:** Owner runs >=4 repos that need *divergent*
  rule sets AND has hit a real cross-repo rule-drift incident.

## PART XX -- Sovereign Control Plane OS (SCP-OS)
- **Purpose:** control plane coordinating all projects' policies,
  standards, failure events, dashboards; trust boundaries; signed standards.
- **Verdict:** DEFER. `tools/pp_health_report.py` + `modules/monitoring`
  already give cross-project status; no centralized policy coordination
  need while solo.
- **Activation criterion:** >=5 active repos requiring synchronized
  policy + a second operator (team > 1).

## PART XXI -- Sovereign Agent Fleet OS
- **Purpose:** work orders, agent routing, multi-repo execution, global
  locks, evidence vault, merge queue for a coordinated agent fleet.
- **Verdict:** DEFER. `modules/cpc_os` already provides a pane registry +
  `plan_parallel_backlog` lock-collision detection; no autonomous fleet
  runs today (<=2 panes, human-driven).
- **Activation criterion:** Owner runs >=3 concurrent *autonomous* agents
  needing work-order arbitration (not human-in-the-loop panes).

## PART XXII -- Sovereign Execution Runtime (SER)
- **Purpose:** leases, worktrees, sagas, scheduler, validator quorum,
  queue reconciliation -- the runtime under the fleet.
- **Verdict:** DEFER. No fleet (XXI) -> nothing to schedule. Worktree-per-
  pane is currently a manual Owner workflow choice, not a module.
- **Activation criterion:** PART XXI is built AND a real multi-agent
  workload exists to run on it.

## PART XXIII -- Sovereign Assurance OS (SAO)
- **Purpose:** executable contracts, attestations, proof chains,
  deterministic replay, certification gates, anti-false-done verifier.
- **Verdict:** SKIP-heavy / EXISTS-core. The anti-false-done intent is
  already enforced by `modules/output_contracts` (OQS / `is_done_for_tier`)
  + HR-OUTPUT-001/002/003 + the V-gate suites. Proof chains / attestations
  / deterministic replay are overkill for solo work.
- **Activation criterion:** a multi-agent fleet (XXI/XXII) ships and needs
  cross-agent attestation that one agent cannot forge another's "done".

---

## Build order if activated
XIX -> XX -> XXI -> XXII -> XXIII (strict; each consumes the prior). Do
not build out of order -- an upper layer with no lower layer is an orphan.
