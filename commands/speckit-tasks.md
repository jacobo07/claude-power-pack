# /speckit-tasks

Break the technical plan into an **ordered task list** that an agent can execute mechanically. Power-Pack-flavoured wrapper around the SDD `/speckit.tasks` command from `github.com/github/spec-kit`.

## When to use

- After `/speckit-plan`.
- Before `/speckit-implement` — implementation reads `tasks.md` as its instruction sheet.

NOT for: planning open-ended exploration (that's a new spec + plan cycle).

## What it produces

`./.specify/specs/<feature-id>/tasks.md`, populated from `vault/templates/speckit/tasks.md.template`. Numbered tasks with: ID, action, target file(s), pre-condition, post-condition, verification command, parent FR / user-story link.

## Process

1. **Read.** Load `constitution.md` + `spec.md` + `plan.md` fully.
2. **Decompose.** Walk the plan's sequencing graph. For each node, emit one or more `T-###` tasks. Each task is single-action: create-file, edit-function, run-command, write-test, etc.
3. **Pre/post-conditions.** What must exist BEFORE the task runs? What proves it ran correctly? These are not optional.
4. **Trace.** Every task links back to a `FR-###` or `US-###` (user story). Tasks that don't trace = scope creep, remove or surface.
5. **Parallelism.** Mark tasks that can run in parallel with `[P]`. Independent leaf tasks should parallelize; dependent tasks must serialize.
6. **Verification command.** Every task's post-condition includes the EXACT shell command (or absence-of-error condition) that proves it.
7. **Commit.** `git commit -m "feat(tasks): <feature-id> N tasks across M micro-commits"`.
8. **Next.** `/speckit-analyze` (recommended before implement) then `/speckit-implement`.

## Done-Gate

- `tasks.md` exists; every task has ID + action + file + pre + post + verification + trace.
- Total commit count predicted in `tasks.md` matches the count of `T-###` entries (Micro-Commit discipline).
- Zero tasks lack a parent FR/US link.
- Parallel tasks `[P]` share no file targets (no write races).

## PP layering

- Reality Contract: each task's verification command is REAL. "Tests pass" is not enough — it must say `pytest tests/feature/test_x.py::test_y -v` returns 0.
- Micro-Commit Discipline: `T-###` IDs map 1:1 to commits, no batching of unrelated tasks.
- OVO Gate: a feature whose tasks all complete with green verification commands is the minimum viable input to OVO.

## Chain

→ `/speckit-analyze` (consistency check) OR
→ `/speckit-implement` (when confident in spec ↔ plan ↔ tasks alignment)
