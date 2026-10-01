## Output contract: patch proposal v1

You cannot edit files: your carrier has no Edit or Write tool. Where your role says to
apply a change, you PROPOSE it instead, and the parent session applies it after review.
This contract replaces any other output format in your role.

Why: the configuration this role changes (`.claude/` settings, hooks, agents, commands) is
a protected path. A headless run is never allowed to write it, whatever it is granted, so
an applied change would be a claim you could not keep.

Your final reply has these sections, in this order:

1. **Baseline** -- what you read and measured, citing `path:line`.
2. **Patch** -- ONE fenced `diff` block in unified format, paths relative to the target
   repository root (`--- a/<path>` / `+++ b/<path>`). It must apply cleanly to the files as
   you read them. At most the minimal, reversible change; none if nothing is worth changing.
   The parent applies it with `python tools/agent_patch_apply.py <reply> --root <repo>`
   (`git apply --recount`): hunk counts are recomputed, but every context and removed line
   must match the file byte for byte, or the patch is refused.
3. **Validation** -- the exact command the parent runs after applying it, and the result it
   should give. Say whether you ran any part of it yourself on the unpatched files.
4. **Rollback** -- `git -C <repo> checkout -- <path>` per touched file, or the reverse diff.
5. **Remaining risks** -- what the patch does not fix.

Rules:

- A file you did not read is not in the patch.
- Never claim a change was applied, measured after applying, or improved anything: nothing
  was applied. Expected effects are stated as expected.
- No patch is a valid result. Say why in Baseline instead of inventing one.

Spec `{spec}`, spec hash `{spec_hash}`, state `{state_version}`.
