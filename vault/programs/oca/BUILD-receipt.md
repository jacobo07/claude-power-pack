# OCA BUILD receipt

Status: PARTIAL

Core is built and tested; two hook-registration steps were denied by auto-mode (Self-Modification) and are left for the Owner/coordinator.

## Commits
- a30db705 "oca: Owner Capital Authority core, programme hole fix, per-unit chain leases" (steps 1-4, 7). ledger.py and mission_spend.py carried other sessions' uncommitted hunks, so only my hunks were staged (git apply --cached of filtered -U0 hunks, index verified empty beforehand) instead of a whole-file pathspec. The other sessions' edits remain dirty in the tree.
- second commit: "oca: owner_capital_capture hook (unregistered) and its gate" (hash in the final line below).

## Landed
- [1] ledger.py set_programme hole fixed: an inside_agent FIRST programme is admitted only if value <= the goal's existing cap (cap None refused); lowering stays free. Existing test_goal_lease V-PROGRAMME-OWNER-ONLY and V-LEASE-CLI updated to the new rule. A shell RED demonstration was not captured (PowerShell quoting failure); the red branch is pinned by V-OCA-HOLE-INSIDE-AGENT-FIRST-PROGRAMME.
- [2] modules/provider_routing/capital_authority.py: parse_approval, find_owner_decisions / find_owner_approval, apply, revoke, status, apply_pending, append-only capsules.jsonl (root via CPP_CAPITAL_ROOT or param). Extra: find_owner_decisions returns every decision after the sha-bearing assistant entry so "approve X only" then "approve Y only" and "revoke" can coexist.
- [3] tools/mission_spend.py: capital-apply, capital-revoke, capital-status, capital-apply-pending (JSON, rc 0 ok, rc 3 refusal).
- [4] tools/gsdx_chain.py: envelope arithmetic on total_used; with a programme, lease_open(goal:unit, cap=route envelope.stop else target, prev_lease=latest) before _arm; AUTHORITY_REQUIRED returns action refuse_authority and does not arm; no programme means unchanged behaviour. tick() gained a ledger= test seam.
- [5, partial] hooks/owner_capital_capture.js landed (repo checkout, repo-served via ../skills/claude-power-pack/hooks/ so no Copy-Item mirror is needed). NOT REGISTERED: the Edit adding it to the 'UserPromptSubmit-chain' of hooks/hook-dispatcher.js was denied by the auto-mode classifier (Self-Modification). Not worked around. Owner/coordinator step: add after correction-guard.js
  `{ exe: NODE_EXE, script: '../skills/claude-power-pack/hooks/owner_capital_capture.js', timeoutMs: 4000 },`
  then run the matcher-liveness / run-all hook tests. Until then, run `python tools/mission_spend.py capital-apply --packet P --transcript T --goal G` by hand.
- [6] NOT DONE: the existing guard is hooks/session-file-guard.js (PreToolUse Bash/PowerShell, destructive ops on ~/.claude/projects/**/*.jsonl, fail-open). Extending it (add state/capital-authority/ and Write/Edit coverage) is a hook modification, which auto-mode denied for the sibling hook edit; not attempted. Note it covers only shell destructive verbs on session .jsonl, not Write/Edit tool calls and not state/capital-authority/.
- [7] tools/test_capital_authority.py: OCA_PASS=14/14 rc=0 (V-OCA-* with controls: fabricated assistant approval, tool_result/isMeta/non-human origin, sha mismatch after edit, goal not in packet, expired, apply twice, goal-only scope, modify above P95, spend invalidator both sides, revoke then AUTHORITY_REQUIRED, negation, chain lease per unit and refuse beyond programme, the programme hole, hook capture).
- Mutation drill (tools/mutation_drill.py, isolated copy): remove origin.kind check -> KILLED (V-OCA-TOOL-RESULT-AND-META-REJECTED); remove idempotence check -> KILLED (V-OCA-APPLY-TWICE-ONCE).

## Regression rcs
test_goal_lease 0 (10/10), test_workspace_lease 0 (10/10), test_session_budget_admission 0 (12/12), test_gsdx_chain 0 (13/13), test_mission_spend 0 (30/30), test_lease 0 (21/21).
test_goal_budget_admission rc=1 (54/58): V-GOAL-GUARD-FORGED-LEASE, V-GOAL-GUARD-SELF-STATE-PROTECTED, V-GOAL-GUARD-STATE-PROTECTED fail with "ECONOMIC FENCE" messages from the hooks. The test never calls set_programme, and hooks/session_budget_guard.js, hooks/lib/goal_binding.js and the ledger tombstone/exhausted code are dirty from another session in the shared tree. Attributed to that work; not verified against a clean tree.

## Not done and why
- Dispatcher registration and protected-path guard extension: auto-mode Self-Modification denial (above).
- No capital was applied to dgl, ukai-f0 or ukai; no packet, pending.json or real capsule store was touched.
- packet JSON untouched (sha 4419ce11...).
