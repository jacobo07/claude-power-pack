# /speckit-implement

Execute the task list. Power-Pack-flavoured wrapper around the SDD `/speckit.implement` command from `github.com/github/spec-kit`.

## When to use

- After `/speckit-tasks` (and ideally `/speckit-analyze`).
- This is the ONLY command that writes implementation code. No other SDD command modifies source files.

NOT for: writing code without a parent `tasks.md`. If you find yourself wanting to, run `/speckit-spec` first.

## What it produces

Real source-file changes plus one micro-commit per completed task (`T-###`). The `tasks.md` is updated in-place to mark each task `[x]` as it lands.

## Process

1. **Read.** Load `constitution.md`, `spec.md`, `plan.md`, `tasks.md` in order. The active spec auto-injects via the JIT loader if `.specify/spec.md` is present.
2. **Verify pre-conditions.** For the next unchecked task, confirm every pre-condition holds (file exists, prior test passes, library installed). If not, STOP and surface to the Owner — do NOT assume.
3. **Execute the action.** Single action only — create the file, edit the function, run the command. Do NOT bundle additional changes into the same step.
4. **Run the verification command.** The exact command in `tasks.md` post-condition. If it returns non-zero, the task is NOT done; debug or roll back.
5. **Commit.** `git commit -m "<type>(<scope>): T-### <one-line>"`. The commit message MUST cite the task ID.
6. **Mark.** Update `tasks.md`: `- [x] T-###`.
7. **Loop.** Next task. Stop only when every `T-###` is `[x]` OR when a verification command fails three times in a row (then STOP and surface, do not bypass).
8. **Final gate.** Run the plan's Done-Gate commands. All must exit 0.
9. **OVO.** `/ovo-audit`. On A/A+, push gate-authorized.

## Done-Gate

- Every `T-###` in `tasks.md` is `[x]`.
- Every micro-commit cites a task ID.
- Plan-level Done-Gate commands all exit 0.
- OVO verdict ≥ A on the feature scope.
- `git push origin <feature-id>` succeeds without bypass.

## PP layering

- Reality Contract: NEVER mark a task `[x]` without running its verification command and capturing exit 0.
- Mistake #16 (Scaffold Illusion): "code compiles" ≠ "feature works". The verification command is what proves the feature; trust it, not the compiler.
- Mistake #17: static checks (type, lint) prove form, not function. Don't skip the runtime verification.
- Intent-Lock: if another pane holds the worktree, yield read-only per `feedback_mirror_sync_direction_and_hooks_dir_deny.md`.
- Anomalous tool result: deny / internal-error / timeout → probe-or-surface in the SAME turn (same memory file).

## Chain

→ `/ovo-audit` then push.
