# C1 receipt
Status: DONE

Commits: worktree 815338a8 (feat/cdc); live landing 170083e7 (land_worktree rc=0, tests_after rc=0).

- PROVEN: `session_autopsy.py --roles` classifies every call (12 roles + unattributed), incl. subagents tagged `sub:<file>`; CLI otherwise unchanged (test_session_autopsy 15/15).
- PROVEN: tools/test_session_autopsy_roles.py 21/21: 3 goldens, one mutant per role + epoch mutant, all flip RED.
- PROVEN: QL Phase-1 table stored in vault/programs/cdc/evidence/ql-phase1-roles.json (807 calls, 126,255,827 processed tokens, main + 7 subagent files).
  READ 31.8%, IMPLEMENT 11.1%, NOVELTY 9.5%, CONTROL 5.0%, CONTEXT_FAULT 4.3%, RECOVERY 2.6%, PLAN 2.6%, REREAD 2.4%, RESEARCH 0.6%,
  PROOF/STATUS/REPAIR 0%. UNATTRIBUTED 30.1% (238 calls). Transitions: 12 commits, 77 new files, 8 claims, 0 red->green; 1,301,606 tokens/transition.
- NOT_PROVEN: the 0% PROOF is not verified against the raw commands (QL was a legal-text pipeline; its checks may not match the test regexes).
- Heuristics (for C12): NOVELTY = Write to a path not read earlier; REPAIR = edit after a red proof run; CONTEXT_FAULT = Read of a path named in the first user message; PLAN-by-text = >=600 chars with no tool before any edit. Bash and PowerShell are both scanned; git is matched through $g variables.
- Calls used: ~25.