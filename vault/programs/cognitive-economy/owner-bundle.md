# Cognitive Economy Program -- Owner bundle

One line per Owner decision, tagged with its pillar. Nothing here was asked mid-run; each item is what the
campaign could not do itself under its envelope.

- [RUN] Merge branch `cognitive-economy/autonomous-run` (worktree `.claude/worktrees/cognitive-economy`, created
  from 8b62b6ce) into `feature/knowledge-acquisition`. The harness refuses background edits in the shared
  checkout, so every campaign commit lives on that branch; the done-gate passes there, and passes on
  `feature/knowledge-acquisition` only after the merge. Command:
  `git -C <repo> merge --no-ff cognitive-economy/autonomous-run`.
- [L] Apply compound steps 7+8 to the live state and switch the call site: make `/cpp-compound` step 7 and `tools/compound_unattended.py` call `python vault/programs/cognitive-economy/compound/steps78.py --state ~/.claude/state/compound-learnings.json --project <pid> --marker <cwd>/LEARNINGS_PENDING.md` instead of doing the mutex/merge/rename/unlink by hand. Proven on temp copies by `gates/gate_compound78.py` (green, and red under `--break-rollback`); the live file was never written.
