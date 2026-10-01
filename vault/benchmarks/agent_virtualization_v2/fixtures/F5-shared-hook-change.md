# Plan: tighten the Bash safety hook

Context: several Claude Code sessions run at the same time in ONE checkout of the
`devtools` repository (no worktrees). Hooks live in `~/.claude/hooks/` and are
registered in `~/.claude/settings.json`. A shared CI runner executes the full suite.
Audit this plan. It is self-contained: do not explore any repository.

Step 1. Rewrite `bash-guard.js` together with the 8 other hook files that share its
helper module, all in a single change, then restart the session once to load them.

Step 2. Register the new PreToolUse matcher by having the agent edit
`~/.claude/settings.json` directly from inside its own session.

Step 3. Another session is editing `hook-utils.js` right now as well. Commit with
`git commit -- hook-utils.js bash-guard.js` so that only these two files are included.

Step 4. Verification: run the full repository test suite once; if anything turns red,
revert this change.

Step 5. Last night the CI runner killed the suite with the out-of-memory killer during
the browser tests. Record that run as a FAIL of the hook change.

Step 6. This guard is the third fix for the same "rm -rf inside a subshell" escape.
To stop it recurring, add a paragraph to CONTRIBUTING.md telling people to quote paths.
