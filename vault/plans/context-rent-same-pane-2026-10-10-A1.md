# Amendment A1 to "Context Rent in one pane" -- boundary-proportional context (PROPOSED)

Written 2026-10-10 17:10. Status: **APPROVED, BLOCKED** (Owner "y", 2026-10-10; A1 hard stop 10M, programme 26M, stop-loss active).

**Blocker, measured at approval time:** the parent goal `ctx-same-pane` had already used **16,773,843 of 16,000,000**
(`mission_spend.py goal-status`). The ledger rows are real, not phantom:
- worker 6d8f3412 main transcript: 5.60M over 33 calls;
- its subagents: 11.73M (gsd-executor 7.21M / 45 calls, gsd-planner 4.28M / 28 calls, gsd-plan-checker 0.23M).

S0 was budgeted at 1.2M as "the 3-line fix" and ate the whole 16M, roughly 13x over. GSD plan-phase plus executor
subagents at about 160K per call are themselves the boundary-rent pathology this programme targets.

Also found: `goal-autopsy` counts only the main transcript (5.6M) and misses subagent spend. It cannot explain its
own ledger.

Per parent section 8, the mission was put on owner hold (`gsd_mission.py hold`, rc=0). A1 cannot start before
parent S1. Owner decision required: raise the goal cap (`goal-declare --owner`, TTY), or re-shape execution so that
no GSD plan-phase runs for small slices. Approval surface = chat; this file is the durable copy.
Parent: `vault/plans/context-rent-same-pane-2026-10-10.md` (APPROVED, commit 06d25261, hard stop 16M),
running as mission m-4d1b851262ff in `Apps\pp-ctx-same-pane` (branch ctx/same-pane).
Mode: EXECUTION amendment (PR-MODE-SELECTION-001). The architecture is already settled by the parent plan, so
this is not a new programme and not a new Context OS (HR-NOVELTY-001).

## 1. Reality delta since the parent plan (read-only, measured)

| fact | value | source |
|---|---|---|
| parent mission | running; S0 patch applied, replay suite 33/33, phase-1 plans 02/03 written, last write 17:01 | `vault/programs/ctx-same-pane/LOG.md`, worktree git log |
| rotation protocol overhead | p50 387,598 tokens, p90 593,098 (n=298); calls to certify p50 3 | `s0/fresh-cost-real.json` |
| main-session floor (call #1) | p50 125K, p90 146K | parent plan section 1 |
| subagent floor (first call) | opus n=16: min 25.7K, p50 72.5K, max 104.7K; sonnet n=24: min 25.3K, p50 99.5K, max 105.9K | last 40 `agent-*.jsonl` transcripts |
| MCP tool schemas | already deferred by the host (ToolSearch); schemas are not hot | this session's tool list |
| skill listing | descriptions only, not bodies (still part of the floor) | this session |
| ROI history | week of 4-7/10: ~24 % of quota went to token optimisation, measured payback about 10x smaller | memory `project_token_audit_week_2026-10-04` |

## 2. Exact root cause: why successive calls cost about the same

1. **The host re-sends the whole epoch transcript on every call.** CPP cannot leave out a past message
   inside an epoch. This is an EXTERNAL_LIMITATION.
   Consequence: cost(call n) = floor + everything accumulated so far, which only grows. Call B pays for
   call A's working set by construction.
2. **The floor is about 125K, and most of it is CPP-authored.** It is made of global and project CLAUDE.md,
   rules, MEMORY.md, the skill and agent listings and hook injections. This part is controllable, but nothing
   has attributed it yet; that is S1.
3. **Rotation, the only eviction, fires late.** It triggers at the 45 % wall, and the boundary veto blocked
   it 449 times. It also costs about 388K per rotation, so it only pays off after about 1.5 or more calls
   at the lower resident. This is parent slice S2.
4. **Nothing routes a boundary to a cheaper materialisation.** The host has two such channels, and neither
   is used for routine work:
   - a lean compiled subagent, measured as low as about 25K;
   - a zero-model status path (parent S4).
   Narrow work therefore runs in the resident pane at full rent. This is the part that is new in A1.

Per-boundary independence inside one visible pane is achievable on this host in exactly three ways:
rotation (evicts everything), a subagent (a fresh context per boundary that returns a receipt), and
zero-model (no context). In-epoch GC, paging and projection pushdown are carried out through those three.

## 3. Added slices (folded into the running mission after the parent's S1)

- **A1-S8 Boundary router.** This extends the existing `capability_runtime.agent_spec compile` and the
  work-class tier routing (7b3e35e9); no new component is built.
  - Classify each boundary: STATUS goes zero-model (S4); PROOF, narrow IMPLEMENTATION and DEBUG go to a
    compiled carrier subagent with a bounded packet that returns a structured receipt; ARCHITECTURE stays
    resident.
  - Pre-call admission: predicted = measured floor of the agent type + packet size. If the packet exceeds
    the class budget, recompile the packet; never pay first and measure afterwards.
  - Kill switch: `CPP_BOUNDARY_ROUTER`.
- **A1-S9 Lean carrier floor.** Find out what separates the 25K agents from the 100K ones (tool set, injected
  context, agent body), make the cpp-carrier-* types inherit the lean floor, and pin the result with a test.
- **A1-S10 Lifetime and producer rent.** Extend S1's autopsy so each tool_result is charged to its producer
  (tool plus path) and the number of times it is carried or re-read across calls and epochs is counted.
  Output: the top-N lifetime-rent producers, plus a receipt-first output contract for the top producer.
- **A1-S11 Embodiment.** Take at least one hot doctrine block that S1 shows to be high-rent AND already
  enforced by a hook (candidate: the Windows Bash bridge section, enforced by `windows-bash-bridge-guard.js`)
  and move it to a skill card, keeping its tests. Edits to `~/.claude` are an Owner-side step under HR-001,
  following the precedent of the 2026-10-05 rule moves.
- **A1-S12 Proportionality benchmark** in a 300K+ resident pane:
  - Sequence: architecture (resident), implementation (carrier), status (zero-model), proof (receipt),
    debug (carrier), closeout.
  - The boundaries must reach different provider-facing sizes; every number comes from transcript usage.
  - The benchmark FAILS if every boundary lands within ±15 % of the resident.

**Stop-loss after parent S1.** If the S1 census shows less than 25K of controllable floor, AND the projected
weekly saving of S8-S11 is below one quarter of their budget, A1 stops there with a receipt. This gate exists
because of the ROI history above.

## 4. Done-gates and limitations

The prompt's 29 Master Done-Gates apply, with these EXTERNAL_LIMITATION declarations made up front:

- Gates 6, 7, 8, 10 (SSM, delta, GC, TTL) are met at the rotation, subagent and zero-model boundaries, not
  inside an epoch.
- Gate 2 (attribution) is met by transcript usage plus a static census; no provider-side per-class breakdown
  exists.
- Gate 16 (tool/skill rent): MCP schemas are ALREADY_DONE by the host; the residue is measured and reduced.

## 5. Budget (subscription-quota tokens, in addition to the parent's 16M)

| item | tokens |
|---|---|
| host investigation (floor by agent type, router channel) | 0.3M |
| novel architecture (router contract, class budgets) | 0.5M |
| deterministic implementation (S8 1.5M, S9 0.8M, S10 0.8M, S11 0.6M) | 3.7M |
| proof | 0.8M |
| mixed-boundary benchmark (S12) | 0.8M |
| long-pane and adversarial rotation canaries | 0 (parent S6) |
| tool/skill rent (measure plus residue) | 0.3M |
| cross-domain extra (one non-PP repo through the router) | 0.3M |
| UKDL / CBR | 0.3M |
| recovery reserve | 0.8M |
| meta-optimisation tax (router classification is deterministic, zero-model) | 0.4M |
| **semantic lower bound / LOWER / P50 / P80 / P95** | **3M / 4.5M / 7M / 9M / 12M** |
| **HARD STOP (A1)** | **10M**; the combined programme stops at 26M |

## 6. Savings opportunity (ESTIMATE, low-to-medium confidence; S1 and S12 measure it)

- Narrow boundaries moved from a resident of about 384K to a carrier at about 25-100K: roughly 70-90 % cut on
  those calls.
- Status check-ins: from 300K+ to about 0.
- Every 10K removed from the 125K floor: about 8 % on every main-session call.
- The estate-wide figure depends on what share of calls are narrow, which is unmeasured; S1 provides it.
  No figure is claimed before then.
