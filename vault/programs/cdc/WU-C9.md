# WU-C9 -- Extinction + CBR inheritance

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C9), 7.

Goal: one real retirement and proof that fresh work inherits the baseline without opt-in.
1. Find >= 1 hot rule/role whose semantics are now mechanically enforced with a live test (candidates: sections of
   `~/.claude/CLAUDE.md` duplicated by closer-guard, windows-bash-bridge-guard, agent-solo-guard). Back up to
   `~/.claude/backups/cdc-<ts>/`, replace the prose by a one-line pointer, keep the guard test green, record chars
   removed and the revert command. Never retire text whose guard is absent or untested.
2. Retire one cognitive role (e.g. green-path reviewer via C5 policy) and record it.
3. CBR: register C3/C4/C6/C7 in hookreg + matcher liveness; UKDL entries (dedup) for the brief's hard-rule
   candidates that are now enforced; mark the rest as candidates.
4. Fresh-repo inheritance test: `git init` a scratch repo, run a bounded `claude -p` slim session that tries a
   NO_WORK Agent spawn; observe the admission row. No opt-in flags.
Land via land_worktree.
