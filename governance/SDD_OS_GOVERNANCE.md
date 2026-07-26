# SDD-OS Governance — explicit activation criteria

> Source: `Dataset SDD-OS 1.txt` (sha256 `a6c8f6bcd83a8230`) via
> `vault/knowledge_base/sdd_os/`. Sealed BL-SDD-ACT-001, 2026-07-26.
> Root-cause record: `SDD_OS_REALITY_REPORT.md`.

## Why this file exists

SDD-OS was sealed on 2026-06-07 with a working tier classifier, per-tier PRD
templates and per-tier quality floors. On 2026-07-26 a scan of 91 project
directories found **zero** carrying any SDD-OS instruction, spec scaffold or tier
classification, and **zero** production firing records for its signal agent.

The system was complete and inert. The reason was not a missing component — it was
that activation depended on the agent judging, per session, that SDD-OS applied.
An implicit criterion is not a criterion.

**T-SDD-OS-IMPLICIT-ACTIVATION-001** — *A governance system that depends on the
agent's judgment to activate is not a system; it is a suggestion. "When it seems
necessary" is not a criterion — it is the reason the system never activates.*

## The activation criteria — explicit and verifiable

SDD-OS classifies **every** task before execution. It is not opt-in per session.

| Tier | Name | Trigger | Required before the first code edit |
|---|---|---|---|
| 0 | Micro | typo, rename, comment, label, formatting | inline mini-spec: objective / scope / acceptance |
| 1 | Standard | add an option or command, fix a bug with a clear cause, extend an existing flow | brief spec: + impact map, regression risk |
| 2 | Feature / System | new agent, workflow, module, endpoint, integration, persistence, auth, billing, migration | **written spec: PRD + Architecture Spec + AC + rollback** |
| 3 | Strategic / Platform | new internal OS, global standard, agent system, universal framework, security layer, execution mode, anything affecting all repos | **Tier 2 set + governance, cross-repo applicability, migration, kill switches** |

A PRD is **forced** to at least Tier 2 when the task creates a feature, changes user
behaviour, touches persisted data, creates or modifies agents or workflows, affects
security / auth / permissions / secrets, touches billing or provisioning, spans
multiple files, can cause regressions, affects architecture, introduces a reusable
standard, or when the word *system / OS / framework / pipeline / universal /
cross-repo / platform* appears — or when "done" cannot be stated clearly
(PARTE I §4). At Tier 2+, **execution without a spec is not permitted.**

## How a spec binds to a task (OD-1, sealed 2026-07-26)

A spec declares what it covers in front matter:

```yaml
---
title: Waitlist gate rework
covers: [waitlist, signup-flow, gate]
tier: 2
---
```

A task binds when its tokens contain **every** sub-token of at least one `covers`
entry. Multi-word entries are conjunctive on purpose.

**A spec with no `covers` declaration binds to nothing.** This is deliberate and it
is the whole fix. The previous gate accepted any `vault/plans/*.md`, so TUA-X (50
files) and KobiiCraft (131 files) passed the spec gate forever, for every future
task, on documents describing unrelated work.

**T-SDD-OS-GATE-SATISFIED-BY-UNRELATED-ARTIFACT-001** — *A gate whose predicate is
satisfiable by something other than the thing it must prove does not gate. Asking
"does this repo contain a spec-shaped file?" is not asking "does this task have a
spec?" — and the repos with the most history pass most easily, so the gate is
weakest exactly where the stakes are highest.*

## The spec update loop

**T-SDD-OS-SPEC-DRIFT-001** — *A spec that is not updated when the code changes is
worse than no spec: it is a false source of truth that future agents and developers
will use to make wrong decisions. The update loop belongs in the done-gate of every
change, not in a separate task that is deferred indefinitely.*

`modules/sdd_os/scaffold.py::check_drift()` reports any bound spec whose mtime
predates the newest source file. It detects staleness — a necessary condition for
drift, not proof of it — and it never edits a spec on its own.

## Enforcement surfaces (all live)

| Surface | Path | Role |
|---|---|---|
| Prompt chokepoint | `tools/jit_skill_loader.py::_sdd_os_activation_inject` | classifies + resolves the spec on every prompt, in every repo |
| Binding | `modules/sdd_os/spec_binding.py` | task ↔ spec via `covers` |
| Gate | `modules/sdd_os/pre_exec_gate.py` | tier-proportional; **generates** the spec skeleton |
| Scaffold | `modules/sdd_os/scaffold.py` | non-destructive substrate on first contact |
| Command | `/cpp-sdd-os` | manual classify / scaffold / drift / rollout |
| Tests | `tools/test_sdd_os_activation.py` | six V-gates |

The injection is **not** routed through the capped proactive-advisory queue.
That queue emits at most three advisories per turn and ranked SDD-OS tenth of
thirteen — a rule that only speaks when nothing else does is not a rule.

## Consent model for generation

The directive is instruction-only until a repo has been scaffolded
(`ARCHITECTURE.md` present). Adoption is the consent signal. A hook that writes
spec files into repos nobody opted into would be correctly read as littering, and a
tool read that way gets switched off — which is how SDD-OS became inert the
first time.

---

## Owner registration step — DONE 2026-07-26

**Status: registered.** The Owner explicitly authorized the write, lifting HR-001
for that single operation. `~/.claude/CLAUDE.md` now carries the block; verified by
`V-SDDOS-GLOBAL-REGISTERED` (exactly one `## SDD-OS` section, all six required
clauses present). Backup at `~/.claude/CLAUDE.md.bak.20260726_130720`; the
pre-existing content was byte-identical after the append.

Two facts worth carrying forward:

1. **The registered block is density-matched, not the verbatim text below.**
   `CLAUDE.md` was at 39,306 chars against Claude Code's 40,000-char performance
   warning — 694 chars of headroom for a 1,646-char block — and
   `tools/trim_claude_md.py --dry-run` reclaimed **0** (it had already been run,
   so that headroom was spent). The block was compressed to ~970 chars keeping
   every normative clause: the core law, all four tier triggers, the escalation
   list, the `covers` rule, and the pointer here. Compression stopped there
   deliberately — the next thing to cut was the trigger list, and a tier ladder
   without triggers is a judgment call again, which is precisely
   `T-SDD-OS-IMPLICIT-ACTIVATION-001`. The file sits at 40,275 (275 over a soft
   warning); the durable fix is relocating an unrelated section to the vault
   behind a pointer, which needs its own Owner decision.
2. **The verbatim block below stays authoritative.** It is what the hook chain
   injects and what a fresh host should register.

Under HR-001 the agent may not otherwise write `~/.claude/CLAUDE.md` (agent-owned
global config) in auto-mode; a future re-registration needs the same explicit
authorization. On a new host, paste this block into `~/.claude/CLAUDE.md`:

```markdown
## SDD-OS — Spec-Driven Development OS (MANDATORY, every repo)

Core law: **Spec First. Execution Second. Validation Always.**

Classify EVERY task into a tier before executing. This is not a judgment call:

- **Tier 0** (typo, rename, comment, label) → inline mini-spec: objective, scope, acceptance.
- **Tier 1** (add an option/command, bug with clear cause, extend a flow) → brief spec: + impact map, regression risk.
- **Tier 2** (new agent/workflow/module/endpoint/integration/persistence/auth/billing/migration) → **written spec REQUIRED before the first code edit**: PRD + Architecture Spec + acceptance criteria + rollback.
- **Tier 3** (new OS, global standard, agent system, universal framework, security layer, anything cross-repo) → Tier 2 set + governance, cross-repo applicability, migration strategy, kill switches.

Escalate to Tier 2+ whenever the task creates a feature, changes user behaviour,
touches persisted data, creates/modifies agents or workflows, affects
security/auth/secrets, touches billing or provisioning, spans multiple files, can
cause regressions, affects architecture, introduces a reusable standard, or when
you cannot state clearly what "done" means. At Tier 2+, executing without a spec
is prohibited (PARTE I §4).

A spec covers a task only if its front matter declares it:
`covers: [tokens]`. A spec without `covers` binds to nothing — a repo full of old
plan files does NOT satisfy the gate.

Tooling: `/cpp-sdd-os classify|scaffold|drift` ·
`modules/sdd_os/pre_exec_gate.py::enforce()` generates the tier-appropriate
skeleton · full doctrine `skills/claude-power-pack/governance/SDD_OS_GOVERNANCE.md`.
```

Verify registration afterwards with:

```
python tools/test_sdd_os_activation.py
```

which reports global registration status as an explicit line — registered or not,
never silently assumed.
