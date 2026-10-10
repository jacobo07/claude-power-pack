---
covers: [economic-containment, session-economic-binding, pre-model-admission, budget-tombstone, recovery-egress, detach-rebind, final-reply-rearm, ctx-same-pane-recovery]
status: AWAITING_OWNER_APPROVAL
goal: econ-contain (to be declared on approval; NOT charged to ctx-same-pane)
---

# Economic Failure Containment: Master Plan (2026-10-10)

The approval surface is the inline plan in chat. This file is the durable copy of it.

## Reality Delta (observed this session, read-only tools, zero shell)

Observation path: Read/Grep/Glob only. Those tools are `isReadOnlyCall`
(hooks/lib/goal_binding.js:73-84), so they cannot write a binding record. The PP repo is not under
any goal root (index.json), so this session is unbound.

### Causal chain, proven from code and ledger

1. **Binding source = cwd, then sticky by session id.** `goalBinding()` (goal_binding.js:114-150):
   when no record exists and the cwd is under `index[goal].roots`, the first MUTATING call writes
   `<state>/goal-binding/<sid>.json` with flag `wx`, which makes it immutable. From then on the record
   wins over env and cwd (lines 119-123). Records on disk:
   - `6d8f3412…` → ctx-same-pane, source `cwd`, since 13:07:52
   - `d5063bac…` → ctx-same-pane, source `cwd`, since 15:34:11
2. **Why cd did not free the pane.** The cwd is never consulted again once the record exists. There
   is no detach verb: `touchesGoalState` (session_budget_guard.js:208) denies any command naming
   goal-budget/session-budget, and the record is `wx`-immutable. STALE_CWD is REJECTED as the cause:
   a fresh cwd would not have helped either.
3. **Why even `Set-Location` was refused.** In goal mode the only exemption is a bare
   `mission_spend.py goal-status --goal X` (line 199). Every other call goes to renew → refused →
   `closeout(goal=true)`, which admits exactly one write to vault/plans, handoffs or RESUMPTION (lines
   158-176). Escaping therefore needed authority from the exhausted domain itself: a confirmed deadlock.
4. **Admission comes after the model.** The guard is PreToolUse. The model request that generated the
   tool call is already bought when the hook runs, so the provider cost of every refused attempt is
   real and is settled.
5. **Re-arming final reply (the amplification engine).** ledger.py:458-472: each renew closes the
   previous `final` once `mark > base`, then reserves a NEW `final` because none is held. "One final
   reply per live pane" is therefore one per TURN, without end. d5063bac shows final reserves of
   150,000 → 206,592 → 207,129 → 209,251 (the reported ~200K per click).
6. **Bound after exhaustion.** d5063bac wrote its cwd binding at 15:34, 50 minutes after the goal
   had crossed 16M (seq 50, 16.10M). Nothing refuses BINDING a session to an exhausted goal, so the
   trap was armed by entering the worktree.

### Overshoot decomposition (journal seq 1-63)

| component | tokens |
|---|---|
| cap | 16,000,000 |
| 6d8f settled (crossed 16M between seq 48 → 50) | 16,634,417 |
| of which post-cap (seq 50-54, final turns) | ~634,417 |
| d5063bac settled, ALL post-cap (bound after exhaustion) | 1,089,380 |
| open final reserves (6d8f 139,426 + d5063bac 209,251) | 348,677 |
| **used + reserved** | **18,072,474** (matches the reported 18.07M) |
| d5063bac prebind (PRE_BINDING capex, not goal spend) | 7,794,222 |
| subagent spend in the window | not separable from the journal; will be decomposed from `<sid>/subagents/*.jsonl` in WS-A |

Settled post-cap spend after exhaustion was already known: about 1.72M (634K + 1,089K).

### Root-cause matrix

| class | verdict | evidence |
|---|---|---|
| CWD_ECONOMIC_OWNERSHIP | CONFIRMED | both records source=cwd |
| SESSION_STICKY_GOAL_BINDING | CONFIRMED | goal_binding.js:119-123, `wx` |
| STALE_CWD_BINDING | REJECTED (as cause) | record wins regardless of cwd |
| BUDGET_ADMISSION_TOO_LATE | CONFIRMED | PreToolUse only |
| PRETOOLUSE_ONLY_ENFORCEMENT | CONFIRMED | UserPromptSubmit chain has no economic member (dispatcher:563-596) |
| REFUSED_MODEL_BOUNDARY_BILLED | CONFIRMED | settles 345K/530K/1.09M on d5063bac |
| POST_CAP_REFUSAL_AMPLIFICATION | CONFIRMED | final re-arm, ledger.py:458-472 |
| RECOVERY_DOMAIN_DEADLOCK | CONFIRMED | only goal-status exempt; no detach |
| RECOVERY_SPEND_AMPLIFICATION | CONFIRMED | each escape probe = one ~200K settle |
| ONE_FINAL_REPLY_INSUFFICIENT | CONFIRMED | re-arms per turn |
| CLOSEOUT_ALLOWANCE_INSUFFICIENT | PARTIAL | 1 write; cannot reconcile or detach |
| NEW_PANE_REQUIRED | PARTIAL | `/clear` mints a new sid in the same pane, but a new sid in a goal cwd re-binds to the exhausted goal at its first mutation |
| ECONOMIC_BINDING_SPLIT_BRAIN | PARTIAL | JS + Python twin share one precedence, but the registry, cwd roots and record are 3 sources |
| OWNER_MANUAL_EGRESS | CONFIRMED | incident |
| NO_BUDGET_TOMBSTONE | CONFIRMED | no exhausted-session state exists |
| BIND_TO_EXHAUSTED_GOAL (new) | CONFIRMED | d5063bac bound 50 min post-cap |

### Earliest controllable boundary

The **UserPromptSubmit** hook runs before the model request. The dispatcher already propagates
`decision:"block"` for non-PreToolUse families (hook-dispatcher.js:1668-1670). A block stops the
prompt before any model call and shows `reason` to the Owner. That gives pre-model admission at zero
model tokens, with a deterministic status as the reason. Harness slash commands (`/clear`,
`/kclear`) do not travel through it, so a tombstone cannot trap them.

PROVEN 2026-10-10 (econ-contain-2), with an amendment. In-chain, the block was honoured but NOT
reliable: under RAM starvation the harness killed the whole dispatcher at its 15 s timeout (5e764b5a:
19,283 / 18,768 ms) and a killed hook fails OPEN, so two Owner messages reached a tombstoned pane's
model. Admission is now its OWN UserPromptSubmit entry (settings.json, timeout 30 s; d3170d43; pinned by
V-ECON-ADMISSION-STANDALONE / -NOT-IN-CHAIN). Live drill: headless `claude -p --session-id f7e8f485...`
bound to tombstoned goal `econ-drill` -> "UserPromptSubmit operation blocked by hook", num_turns 0,
all usage 0, total_cost_usd 0. Rule: a fail-closed gate never shares a hook process whose timeout fails open.

Remaining unavoidable floor: the first boundary that DISCOVERS exhaustion mid-turn (PreToolUse) is
already bought. Every later Owner message can be blocked pre-model.

## Owner map

| capability | class | owner |
|---|---|---|
| session binding record | EXTEND | hooks/lib/goal_binding.js + mission_spend.py twin |
| binding generations / supersede | IMPLEMENT (inside existing record dir) | goal_binding |
| workspace registry fencing (gen/lease) | ALREADY_DONE (dgl W2) / CONNECT | goal-lineage, workspace.journal |
| pre-model admission | IMPLEMENT as a UserPromptSubmit-chain member | new hook `econ_admission.js` (critical lane) |
| tombstone | IMPLEMENT as a GoalLedger journal op | modules/provider_routing/ledger.py |
| final-reply re-arm | EXTEND (once per sid per exhaustion) | ledger.py renew |
| bind-to-exhausted refusal | EXTEND | goal_binding + ledger fold |
| recovery/egress verbs | EXTEND mission_spend CLI + admission hook | mission_spend.py |
| deterministic status | EXTEND `goal-status` renderer | mission_spend.py |
| successor / ContextImage | CONNECT | dgl (durable goal / disposable lease), /kclear capsule-v2, SessionStart hub |
| Owner capital decision | CONNECT | existing `goal-declare --owner` interactive path |
| PreToolUse guard | NO_WORK except calling shared binding ABI | session_budget_guard.js |
| FIOS/UKDL/CBR | EXTEND | vault/knowledge_base, ukdl-universal.md |
| same-pane visible process replacement | EXTERNAL_LIMITATION (host owns the pane; `/clear` is the in-pane epoch swap) | Claude Code |

## Architecture (smallest coherent extension)

- **Economic identity ABI.** `resolveEconomicBinding(sid, event)` returns
  `{programme, goal, lease, role: productive|recovery|neutral, gen, source, state}`. It is exported
  once from goal_binding.js, with a Python twin, and used by the PreToolUse guard, the admission hook,
  the scheduler and status. Records become generational: `<sid>.json` stays immutable, and a
  supersede writes `<sid>.g<N>.json` through a recovery verb only, journaled with old → new, reason,
  checkpoint and authority. cwd stays a hint for the FIRST bind only, and never binds to a goal that
  is tombstoned or over its cap (that is refused and the session becomes `neutral` with a quarantine
  notice).
- **Pre-model admission (`econ_admission.js`, critical, UserPromptSubmit).** It resolves the binding
  below the model, reads `used + reserved` from the journal, and predicts the next floor
  (`nextRequest`). If the floor is not admissible, it blocks the prompt with a rendered deterministic
  status (goal, cap, settled, reserved, unknown, next legal transition, Owner requirement). Recovery
  verbs typed as a prompt (`econ detach`, `econ status`, `econ successor`) are executed by the hook
  itself and blocked with their result: 0 model tokens, outside goal authority.
- **Tombstone.** A journal op `{op:"tombstone", sid, gen}` written at the first refused renew. Later
  renews for that sid return the tombstone at once, with NO new final reserve. Admission blocks
  tombstoned sids. Singleflight comes from the journal being shared: every pane reads one truth.
- **Final reply once.** One final per (sid, exhaustion epoch), never re-armed after settle.
- **Recovery capability.** Recovery verbs never edit product paths. While a session is detached or
  neutral, the PreToolUse guard denies mutation under ANY root of a tombstoned or over-cap goal
  unless it is bound to a successor lease of that goal's lineage. That is the anti-laundering fence,
  and it is keyed by subject (goal roots and lineage), never by sid, pane, cwd or host.
- **Accounting roles.** Recovery spend goes in its own journal role (`recovery`) under the parent
  programme reserve. It is never productive spend on the historical lease. Refused-but-billed
  boundaries stay settled as real cost.
- **Succession.** If parent authority remains, the lease is sealed → successor lease → capsule-v2
  ContextImage (goal, residual, receipts, next WU) → `/clear` in the same pane, and the SessionStart
  hub binds the new sid to the successor. Otherwise WAITING_OWNER_CAPITAL: zero resident worker, one
  semantic decision, and the Owner's approval wakes the goal through an event, not polling.

## Workstreams, modes and token budget (this mission only, goal `econ-contain`)

| WS | content | mode | P50 |
|---|---|---|---|
| A | binding archaeology close-out + subagent decomposition | EXECUTION | 0.3M |
| B | pre-model admission hook + live block drill | PLAN→EXEC (drill first) | 1.4M |
| C | tombstone + final-once + bind-to-exhausted refusal (ledger) | EXECUTION | 1.2M |
| D | recovery/egress verbs + deterministic status | EXECUTION | 1.0M |
| E | generational detach/rebind + fencing | EXECUTION | 0.9M |
| F | in-flight/reserve accounting roles (recovery, refused-billed) | EXECUTION | 0.5M |
| G | recovery ContextImage via capsule-v2 + /clear epoch | EXECUTION | 0.6M |
| H | successor + Owner-capital wake (CONNECT dgl) | PLAN→EXEC | 0.9M |
| I | canaries: trapped-pane, cwd, stale-cwd, bypass, zero-burn, laundering ×4, successor, parent-capital, pane-loss | EXECUTION | 1.3M |
| J | real ctx-same-pane recovery | EXECUTION | 0.4M |
| K | cross-domain validation (one unrelated goal) | EXECUTION | 0.3M |
| L | Knowledge Vault / FIOS / UKDL / CBR | EXECUTION | 0.4M |
| — | recovery reserve | | 0.8M |
| — | Meta-Optimization Tax (iteration passes, reviews) | | 0.6M |

Semantic lower bound 4.5M · LOWER 6M · **P50 10.6M** · P80 13.5M · P95 17M · **HARD AUTHORITY 14M**
(goal cap). Worker panes, fresh panes per WS: the coordinator pane is the known overrun
(memory: coordinator 18.4M vs workers 6.08M).

### Baseline → target

| metric | baseline (measured) | target |
|---|---|---|
| post-cap tokens per Owner interaction | ~200K (final per_call 206-209K) | 0 (pre-model block) |
| model boundaries to detect exhaustion | ≥1 per turn, without end | 1 per sid, ever |
| manual Owner escape actions | 5+ (cd ×2, path fix, retry, fresh pane) | 0 (one authority decision only when capital is genuinely short) |
| Recovery Amplification Ratio | >1 (each probe +~200K on the violated cap) | 0 on the historical lease |
| context rent during exhausted status | full history (~150-210K) per message | 0 model; status from journal |
| overshoot after first known exhaustion | ~1.72M settled + 0.35M reserved | ≤ one in-flight boundary |
| Owner mechanical tax | shell syntax + pane recreation | none |

## Real ctx-same-pane recovery (WS-J)

Seal the historical lease at its measured truth. Tombstone 6d8f + d5063bac. Release the two open
finals (348,677) as `leak`/released with reason. The cap is never raised. Remaining approved
ctx-same-pane work resumes only under a successor goal id that the Owner capitalises in one semantic
decision, with the residual compiled from receipts and commits in Apps\pp-ctx-same-pane (no re-proof
of committed work).

## Done-gates

Master Done-Gates 1-28 from the mission prompt, each with a V-ECON-* gate in
`tools/test_econ_containment.py` driven from both poles, plus a live drill (UserPromptSubmit block
observed in the real harness) and /liveness for every new module.
