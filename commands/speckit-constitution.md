# /speckit-constitution

Create or update the **project constitution** — the per-project governance layer that sits below global `~/.claude/CLAUDE.md` and above the feature spec. Power-Pack-flavoured wrapper around the SDD `/speckit.constitution` command from `github.com/github/spec-kit`.

## When to use

- First action on a brand-new project.
- After a major scope shift that invalidates prior principles.
- When `/speckit-analyze` reports project-vs-feature drift.

NOT for: ad-hoc tweaks to specific features (that goes in `spec.md`), or global doctrine changes (that goes in `~/.claude/knowledge_vault/core/`).

## What it produces

`./.specify/memory/constitution.md` (canonical Spec Kit path), populated from `vault/templates/speckit/constitution.md.template`.

## Process

1. **Pre-flight.** If `.specify/memory/constitution.md` already exists, READ it before any edit. A constitution rewrite is a heavy action — confirm intent with the Owner if a version bump is implied.
2. **Gather principles.** Collect 3-7 NON-NEGOTIABLE principles for THIS project. Examples: Library-First, CLI Interface, Test-First, Integration Testing, Observability, Versioning, Simplicity. The Power Pack defaults: Reality Contract, Micro-Commit Discipline, OVO Push Gate, Intent-Lock Mutex, Mirror Parity.
3. **Fill the template.** Copy `vault/templates/speckit/constitution.md.template` to `.specify/memory/constitution.md`. Replace `[PROJECT_NAME]`, each `[PRINCIPLE_N_NAME]`, each `[PRINCIPLE_N_DESCRIPTION]`, the additional sections, and the governance block. Stamp `Version`, `Ratified`, and `Last Amended`.
4. **Validate.** Read the result top-to-bottom. Every `[BRACKETED]` marker MUST be replaced. Any remaining marker = iterate.
5. **Commit.** `git add .specify/memory/constitution.md && git commit -m "chore(constitution): initial ratification" -m "Principles: <list>"` (or `amend: <reason>` for updates).
6. **Next.** Hand off to `/speckit-spec` for the first feature.

## Done-Gate

- `.specify/memory/constitution.md` exists, all bracketed markers replaced.
- Version/Ratified/Last-Amended stamped.
- Committed; subject line starts with `chore(constitution):`.
- `/speckit-analyze` (run later) shows no project-vs-template drift.

## PP layering

- The constitution is the project's PASO -1 of the Apex Onboarding Standard. It does NOT replace the global apex doctrine; it specializes it for this project.
- Intent-Lock applies: if another pane is mid-constitution edit, this run yields per `feedback_mirror_sync_direction_and_hooks_dir_deny.md`.
- The Owner can vary template structure but MUST preserve the four PP non-negotiables (Reality Contract, Micro-Commit, OVO Gate, Mirror Parity) as principles in the constitution.

## Chain

→ `/speckit-spec "<feature description>"`
