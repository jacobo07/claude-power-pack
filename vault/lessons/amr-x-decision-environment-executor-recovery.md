---
covers: [amr-x, owner-escalation-gate, config-enforced-topology, decision-recovery, blocked-state-validity]
status: CANDIDATES (promote after the production recovery of m-5cd1a041bc0f is observed)
source: vault/plans/amr-addendum-decision-env-executor-20261013.md
---

# AMR-X — a question is not a wait

## Incident (machine evidence, 2026-10-12 14:03 → 10-13 12:06)
Mission m-5cd1a041bc0f (kobicraft-web, SEO+GEO t1). Repo `.planning/config.json` `workflow.use_worktrees: false`.
Worker 1659fc31 called EnterWorktree first (pre-approved by `worker_argv` for every mission), which failed:
"Command 'git' not found or is in an unsafe location" (git is not on Machine/User PATH; every estate script uses
`C:\Program Files\Git\cmd\git.exe`). It created a worktree by hand (`git worktree add`, 0 unique commits), then
ended its turn: "Decision for you: …absolute path, or `! cd` … and restart the session?". The host wrote that
question to `~/.claude/jobs/1659fc31/state.json` as `needs` (with a `suggestedReply`!) and listed the job
`blocked`, no `waitingFor`. `liveness()` read every bare `blocked` as WAITING_HUMAN (rule from 09-28, correct for
login/startup gates); the sweep logged `surface_blocked` every 5 min for 21 h 43 min. Cost of the failed epoch
0.45 USD; cost of the wait: a day of an approved mission.

## Failure patterns (FIOS)
| Pattern | Trigger | Corrective architecture | Regression guard |
|---|---|---|---|
| CONFIG_AVAILABLE_BUT_NOT_CONTROL_PLANE | repo policy file exists, runtime never reads it | `mission_policy.topology_for` compiled into `worker_argv` | V-AMRX-ARGV-NO-WORKTREE, V-MPOL-TOPO-* |
| OWNER_ESCALATION_FOR_LOCAL_DECISION | worker ends on a question policy answers | Owner Escalation Gate on the host's `needs`, Owner classes first | V-MPOL-GATE-*, V-AMRX-PLAN-REPLACE |
| BLOCKED_STATE_WITHOUT_VALID_WAIT | bare host `blocked` parked forever | plan_next types it; QUESTION_RESOLVABLE → replace with answer | V-AMRX-SUCCESSOR-LAUNCHED |
| SAFE_FALLBACK_NOT_COMPILED | optional tool broken, worker improvises | topology fallback = main tree when EnterWorktree unhealthy | V-AMRX-ENV-FALLBACK |
| WORKTREE_POLICY_VIOLATION propagated | relay follows predecessor into a forbidden worktree | `worktree_not_followed` when policy forbids | V-AMRX-WORKTREE-NOT-FOLLOWED |
| ANSWER_LOST_ON_FAILED_LAUNCH (review F2) | stop overwrites the job file before a launch that fails | `pending_decision` persisted with the counter, re-injected, cleared on adoption | V-AMRX-ANSWER-* |

## Negative knowledge
- A manual worktree is not a fallback where `use_worktrees` is false; the fallback is the main tree.
- Fixing git on PATH is NOT required to continue a mission that must not use worktrees (PATH defect stays debt).
- A host `blocked` row is not evidence a human is needed: read the job's `needs` first.
- A policy match must never outrank an Owner class in the same question (review F1: "main checkout … deploy?").
- New session alone is not recovery: the successor must carry the answer, or it asks again.

## UKDL candidates
- HR candidate: A mission worker's question reaches the Owner only if it matches an Owner class (deploy/push/
  live write, credential, external property, irreversible, product scope, authority); every other question is
  answered by policy, then by the worker's own recommended option.
- PR candidate: On a blocked mission: host row `waitingFor`? → human. Else read job `needs` → gate → Owner class →
  surface with class; else replace with the runtime answer persisted on the record; cap 2 per mission.
- Trap: "BLOCKED means a human must answer" — the host uses `blocked` for a model's own trailing question.
- Trap: pre-approving a tool for every mission overrides each repo's policy against that tool.

## Known residual (debt, by decision)
- A shell `git worktree add` by a mission worker is not denied at tool admission: a Bash|PowerShell chain hook
  costs a node spawn on every shell call of every session (hook-chain latency is a measured cross-repo fault).
  Covered instead by: EnterWorktree disallowed, answer in the card, supervisor never follows a forbidden worktree.
- git absent from PATH machine-wide: EnterWorktree UNHEALTHY for every repo that allows worktrees (fallback main).
