# Amendment A2: boundary-proportional context, self-hosted on econ-succession (PROPOSED)

Written 2026-10-11 by session 47f3da08. Status: **APPROVED at P95** (Owner "y go p95", 2026-10-11; goal `ctx-rent-a2` declared, hard cap 14,000,000; was proposed at 12M).
Supersedes the execution shape of `context-rent-same-pane-2026-10-10.md` + `-A1.md` (mission m-4d1b851262ff, goal
`ctx-same-pane`, over cap 16.77M/16M, on hold). Same architecture, new goal, new topology. Not a new Context OS (HR-NOVELTY-001).
Mode: EXECUTION. The architecture was settled by A1 section 2; nothing below needs ULTRA-PLAN.

## 1. Reality delta (measured 2026-10-11, transcript usage = input + cache_creation + cache_read)

| fact | value | source |
|---|---|---|
| fresh floor, this session call 1 | 122,093 (32,664 cache-read prefix shared across sessions + 89,427 session-specific) | 47f3da08.jsonl |
| fresh floor, 28a5bd61 call 1 | 139,327 (32,664 + 106,661) | 28a5bd61.jsonl |
| 28a5bd61 trajectory | 47 calls, 139,327 -> 247,022, sum 9,544,484 processed input, 53,948 output | same |
| always-loaded instruction files | 142,354 bytes, about 39.5K tokens (global CLAUDE.md 40,117; PP CLAUDE.md 40,832; MEMORY.md 17,214; ~/CLAUDE.md 6,025; rules 38,166) | file sizes |
| unattributed session-specific floor | about 50-67K tokens: skill listing, agent listing, deferred-tool list, MCP instructions, hook injections (SessionStart, UserPromptSubmit), first prompt | 89-107K minus files |
| rotation wall | 45 % (~450K) in context-watchdog.py + hooks/rollover_wall.js; at_boundary veto (rollover.py:680) | grep |
| pre-model admission | none; watchdog judges at Stop and PostToolUse, after the call is paid | rollover_wall.js header |
| SSM / working-set code | only modules/cognitive_os/{gc,memory}.py, offline; no caller on the model path | grep, 13 hits / 4 files |
| goal declare | a NEW goal is agent-declarable; rebinding an existing goal needs `--owner` on a TTY | mission_spend.py:571,1061 |

**What ~226,727 was:** a 28a5bd61 call late in S0 work = 32.7K host-cached prefix (harness prompt + built-in tool schemas)
+ ~107K CPP-authored session floor + ~87K accumulated epoch history (S0 scan tool results and outputs). About 61 % floor,
39 % history. Exact per-class split inside the floor is slice A; no provider-side breakdown exists (EXTERNAL_LIMITATION).

### 1.1 Floor census (slice A, `tools/context_floor_census.py 47f3da08 28a5bd61`, gate `tools/test_context_floor_census.py` 23/23)

Read-only, from the transcript alone. Chars are exact; tokens are estimates at 3.6 chars/token (prose bound) and at
the history-calibrated ~2.36 (dense bound, from tool output). The ranking is by chars, so it does not depend on the ratio.

| call-1 floor item (47f3da08) | chars | est. tokens 3.6 / 2.37 | lever |
|---|---:|---:|---|
| ~/.claude/CLAUDE.md | 39,809 | 11.1K / 16.8K | B: Windows bridge + closer-guard prose is hook-enforced |
| PP CLAUDE.md | 38,951 | 10.8K / 16.4K | B: inline HARD RULES mirror of vault/hard_rules |
| ~/.claude/rules/*.md (26 files) | 38,046 | 10.6K / 16.1K | B: 18 are moved-to-skill stubs (16,196 chars) that still load |
| skill listing (278 skills) | 30,103 | 8.4K / 12.7K | host; only plugin/skill enablement (Owner, settings) |
| agent listing (71 types) | 27,352 | 7.6K / 11.5K | host; same |
| MEMORY.md | 17,059 | 4.7K / 7.2K | B: index compaction |
| host system prompt | 7,470 | 2.1K / 3.2K | host |
| ~/CLAUDE.md | 5,956 | 1.7K / 2.5K | B: duplicates PP doctrine |
| instructions wrapper, deferred-tool list, MCP instructions, SessionStart superpowers, env/session/date, prompt | 22,578 | 6.3K / 9.5K | mostly host |
| **attributed** | 227,324 | 63.1K / 95.9K | |
| **measured call 1** | | **122,093** = 32,664 cross-session prefix + 89,429 session-specific | |

Session-specific 89,429: the items above explain 61.1K at 3.6 and all of it at 2.37 (remainder +28.4K / -3.3K), so the
true remainder is inside that bracket. The 32,664 prefix is identical in both sessions (tool schemas + static system
prompt; not in any transcript). 28a5bd61 differs only by its 68,616-char pasted prompt (+17,234 tokens = 3.4 chars/token).
**CPP-authored files are 139.8K chars, 61 % of the attributed floor; the host listings are 25 %.**
Hooks timed out before call 1 in both sessions (SessionStart chain 15 s, UserPromptSubmit 10-15 s), so PP's own hook
injections contributed nothing to these floors; only the superpowers SessionStart text (3,480 chars) arrived.

| growth over the epoch (measured deltas) | 47f3da08 (24 calls) | 28a5bd61 (47 calls) |
|---|---:|---:|
| total growth, call 1 -> last | 66,488 | 107,695 |
| assistant output carried forward | 24,735 | 53,943 |
| tool_result:PowerShell | 8,447 | 21,845 |
| tool_result:Read | 6,625 | 14,682 |
| pasted / queued prompts | 21,588 + 2,185 | 6,108 |
| everything else (reminders, hook notes, deltas) | ~3K | ~11K |

Conservation holds (charges + output = growth, V-CENSUS-REAL-CONSERVATION). In 28a5bd61 half the growth was the
model's own output carried forward, not tool results: carrier/rotation (C, D) cut that; trimming tool output alone cannot.

**Why the 150K stop-loss fired:** the floor alone is 122-139K, so any call carrying more than ~11-28K of work crosses it.
It was structurally unsatisfiable, a canary that measured the floor, not waste. It is not raised; it is replaced by a
per-boundary budget = measured floor of the channel + packet size.

## 2. Root-cause matrix

| class | verdict | evidence |
|---|---|---|
| ASER_IS_ROTATION_NOT_MINIMIZATION | CONFIRMED | rotation evicts the whole epoch, wall 45 %, never touches the floor |
| SSM_NOT_HOT_PATH | CONFIRMED (+HOST_LIMITATION) | no pre-model caller; host re-sends the epoch, CPP cannot omit messages inside it |
| SESSION_HISTORY_RENT | CONFIRMED | 139K -> 247K inside one epoch |
| COMPLETED_WORK_CARRY | CONFIRMED | S0 scan results stayed resident through the S0 seal |
| CONSTITUTIONAL_RENT | CONFIRMED | ~39.5K tokens of files on every call of every session |
| TOOL_SCHEMA_RENT | PARTIAL | MCP schemas already deferred by host; skill/agent listings remain (unmeasured) |
| DUPLICATED_CONTEXT | PARTIAL | e.g. PP CLAUDE.md inline HARD RULES mirror of vault/hard_rules; Windows doctrine in CLAUDE.md + MEMORY + rules; not yet quantified |
| RESUME_RENT | CONFIRMED | resume needed 3 calls / ~370K to certify a ~1.3K-token residual; A1: rotation overhead p50 388K |
| CONTEXT_ADMISSION_TOO_LATE | CONFIRMED | judged at Stop/PostToolUse only |
| WORKSTREAM_SESSION_COUPLING | PARTIAL | Owner rule rotates at sealed workstreams; planning + S0 shared one epoch |
| STOPLOSS_MASKS_ARCHITECTURE_DEFECT | CONFIRMED | 150K < floor + any work |

## 3. Owner map (no new component)

| capability | owner | class |
|---|---|---|
| epoch rotation / ASER | tools/rollover.py, hooks/rollover_wall.js, context-watchdog.py | ACTIVE -> EXTEND (boundary trigger) |
| certified-result carry | ctx/same-pane 018230b9 (rehydration basis + H1) | IMPLEMENTED_BUT_NOT_HOT_PATH -> MERGE to live |
| ContextImage / packet | modules/capability_runtime/agent_spec compile + cpp-carrier-* agents | PARTIAL -> EXTEND (read-necessity manifest) |
| boundary router | work-class tier routing 7b3e35e9 | PARTIAL -> EXTEND (A1-S8) |
| zero-model status | parent S4 | PARTIAL -> CONNECT |
| usage accounting | mission_spend.py, goal-autopsy | ACTIVE; autopsy misses subagents -> EXTEND |
| semantic GC (in-epoch) | none possible | HOST_LIMITATION; done by rotation/carrier |
| constitution | ~/.claude/CLAUDE.md, rules/, PP CLAUDE.md, MEMORY.md | ACTIVE -> RETIRE embodied prose to skill cards |
| skill/agent/tool listing | host | HOST_LIMITATION except via plugin/agent enablement |
| SSM as concept | rotation + carrier + zero-model | CONNECT, no new module |

## 4. Slices (all EXECUTION; no GSD plan-phase, no planner/checker subagents)

- **A Floor census.** Deterministic script: per-source token estimate of the fresh floor (files, listings, each hook's
  injected text), per-call history attribution by tool_result producer. Output: ranked table + JSON pinned in Context CI.
- **B Floor reduction (largest lever).** Move hook-enforced or duplicated doctrine out of the always-loaded files into
  skill cards / linked files with backups and revert lines (precedent: 2026-09/10 rule moves). Candidates: Windows Bash
  bridge block, closer-guard amendments, PP CLAUDE.md inline HARD RULES mirror, MEMORY.md index compaction.
  Target is measured, not promised; gate = re-measured call-1 floor.
- **C Boundary router + lean carrier (A1-S8/S9).** Narrow PROOF / IMPLEMENTATION / DEBUG boundaries go to a cpp-carrier-*
  with a compiled packet (= the ContextImage). Each packet page names its consuming obligation (read necessity); packet
  hash invalidates on file/HEAD change. Pre-call admission: predicted = carrier floor + packet; over class budget ->
  recompile, never pay first. Kill switch CPP_BOUNDARY_ROUTER.
- **D Boundary-aware rotation.** Rotate at a sealed boundary when predicted carry over the next boundary exceeds the
  rotation cost; carry only certified results + residual (carry necessity). 45 % wall stays as late fallback.
- **E Zero-model status** connected for goal/mission/status questions.
- **F Metrics.** Per boundary: actual provider input, estimated CWS, CRA = actual/CWS, survival, resume amplification;
  goal-autopsy counts subagent spend.
- **G Context CI.** Floor-regression gate, history-elasticity (same task, 10x unrelated history), knowledge-growth,
  resume, status-zero-model, ContextImage invalidation, over-budget recompile.
- **H S1 canary.** econ-succession S1 (provenance spike, 6 calls) from a fresh epoch + minimal packet. Pass = material
  measured drop vs 28a5bd61 (139-247K/call) with the remaining floor explained. Fail -> stop scaling, re-diagnose.
- **I Second canary.** S3 (capital_authority.py receipts, red tests first) via carrier: implementation class.
- **J S2-S10** under econ-succession's existing 20M authority, each boundary compiled, sealed, rotated.
- **K econ-contain-2 S9 canary** under the existing P80 approval; packet expiry 2026-10-14T00:00Z (approval predates it;
  S3 must persist the receipt first).
- **L** Knowledge Vault / UKDL / CBR: failure classes above, hard-rule candidates after proof, retirement of superseded hot prose.

Order: A -> B -> H (S1 canary on the reduced floor) -> C+F -> I -> D+E+G -> J -> K -> L. B before H because it
cuts every call, including the canary's.

## 5. Budget (processed input tokens incl. cache reads, subscription quota)

| item | tokens |
|---|---|
| reality + census (A) | 0.6M |
| provider-boundary instrumentation + metrics (F) | 0.8M |
| floor reduction (B) | 1.2M |
| router + carrier + ContextImage/delta (C) | 2.3M |
| boundary-aware rotation / semantic GC (D) | 0.9M |
| zero-model status (E) | 0.4M |
| Context CI (G) | 0.6M |
| S1 canary overhead (H) | 0.6M |
| second canary overhead (I) | 0.3M |
| S1-S10 continuation overhead (beyond econ-succession's own budget) | 0.5M |
| KV / UKDL / CBR (L) | 0.5M |
| recovery reserve | 1.0M |
| meta-optimisation tax (this scan ~0.85M + plan + rotations) | 1.3M |
| **semantic lower bound / LOWER / P50 / P80 / P95** | **3.5M / 5M / 8M / 11M / 14M** (confidence low-medium: the parent ran 13x over on S0) |
| **HARD AUTHORITY requested** | **12M** on new goal `ctx-rent-a2`; econ-succession work stays inside its existing 20M |

Stop-losses: a slice exceeding 3x its row; the canary showing no material reduction; any subagent topology above 2
concurrent; the 12M cap.

## 6. Approval surface

Approval covers: declare goal ctx-rent-a2 (12M), retire mission m-4d1b851262ff (merge 018230b9 work instead), slices
A-L, edits to always-loaded files under ~/.claude with backups and revert lines, autonomous continuation of
econ-succession S1-S10 and the econ-contain-2 canary under their existing approvals, micro-commits on
feature/knowledge-acquisition (pathspec-scoped; another writer is active).
Excluded: settings.json / plugin enablement changes, deploys, raising any existing goal cap, deleting worktrees.
Returns to Owner: a settings/plugin change proves necessary for listing rent; canary H fails twice; 12M or 20M would be
crossed; any hard-rule-gated action.
