---
covers: [incremental-intelligence-kernel, recomputation-without-causal-invalidation, aser-disposition, ctx-rent-a2-reconcile, slice-b-receipt, zombie-worktree, cpp-fsck, stranded-lease]
status: AWAITING OWNER APPROVAL 2026-10-23. One approval; nothing below is armed or mutated.
tier: SDD T2 (residual scope only; the T3 part of the brief is already owned by the UEK plan)
backs: the inline Master Plan shown to the Owner (inline = approval surface, this file = backup)
owner_of_overlap: vault/plans/ccr-v5-uek-master-plan-2026-10-23.md (branch ccr/v5, c8cb192f), mission m-8ed9da30553c (GEX44, goal uek 38M, RUNNING since 15:09)
---

# Incremental Kernel brief: residual plan (2026-10-23)

Labels: MEASURED (command this session), READ (source read this session), ESTIMATE.

## 0. Ownership verdict (the falsifier was already in hand)
The brief arrived ~2 minutes after the Owner approved `approve uek only` (packet uek-capex-38m, sha bdc4bfba...c9ce)
and the UEK mission started on GEX44. The UEK plan already owns, with stages and budget:
- P0 stop the E4b2 loop: DONE by chain park d81ca446 (14:56). `gsdx_chain.py:669` arms nothing on a parked chain. MEASURED: no `arm_refused` after 14:41.
- P1 E4b2 formula: diagnosed as an admission split-brain (UEK plan s1, s25-26): the arm path refuses at floor 2,983,656 x 1.2 = 3,580,388 > 3,500,000, while standalone `route_admission.admit` says ADMISSIBLE, need 3,458,564. Fix = UEK-1c-2 (one admission reader, admission rows carry a floors-sha invalidator).
- Retry-without-invalidation: UEK s27-32 (RETRY_EQUIVALENT denied, declared causal-dimension diff) + s25 (admission invalidators). That is the dependency-fingerprint primitive for the one observed incident.
- P2 evidence deflation: UEK s14-17, s33 (per-obligation attempts, CSE, blocked-sibling law).
- P3 WAIT_RESOURCE: UEK s23-24 (two-sample RAM gate UEK-1b live; WAIT_RESOURCE ledger state).
- P4 false COMPLETE: UEK-1c (F1-F4), closure compiler s39-43, 15-mutation suite s55.
Running a second plan over those files would be two writers on ccr/v5 (`gsdx_chain.py`, `route_admission.py`, `chain.json`). This plan does NOT touch them.

### 0.1 The 20-vs-26 incoherence (READ, arithmetic only)
2,983,656 / 20 calls = 149,183 per call. At that rate 3,500,000 / 1.2 = 2,916,667 fits 19 calls, not 26. So the
refusal's hint and its check use different per-call floors inside one message: the same split-brain, visible in
the text. No Owner choice of 3.5M vs 3.6M exists; UEK-1c-2 derives the single number.

### 0.2 One residual poll (MEASURED), handed to UEK, not edited here
`chain_tick.ps1` samples RAM before reading `parked`: `ram_hold` at 14:51 and 15:01 on a parked chain. Zero model
cost, one process per 10 min. Line for the UEK coordinator: "read `parked` before the RAM pre-check". Not a reason
for a second writer in the ccr-v5 worktree.

## 1. Residual reality (what UEK does not own)

### 1.1 ASER (MEASURED, rollover-ledger.jsonl, join capsule -> session -> verdict)
- 2026-10-22: 19 capsules sealed; **19/19 certified** eventually; 3 of them failed one exam before certifying.
- The "3 unexplained" in the 14:45 status were a counting artifact: events grouped by DAY, not joined per capsule
  (certifications landed on other days). Disposition gap = 0. Unreconciled capsules = 0.
- Both `resume_failed` rows have `wrong: ["next"]`: the successor misnamed the next open obligation (exam item
  `rollover.py:953`). Class = EXAM_NEXT_MISMATCH (a typed continuation-truth miss), self-healed on retry.
- Event vocabulary already typed: capsule_sealed, successor_claimed, resume_certified, resume_failed,
  certify_refused, certify_stale_refresh, claim_refused, claim_taken_over, reset_gate, shadow_candidate.
- Rotation trigger: economic/context (`_rollover_step`, 45% wall + boundary), not a timer. "Daily" was observation.
- Residual: no per-capsule disposition VIEW exists, which is why a status reader mis-counted. That is the fix.

### 1.2 ctx-rent-a2 economics (MEASURED)
`programme-status`: programme 30,000,000 (capital 9e7616c29691), settled 10,117,468, open 2,762,810,
executable 17,119,722. `goal-status`: cap 14,000,000 (lease L1), used 12,880,278 = settled + open, remaining 1,119,722.
- **No Lease Admission Integrity Failure.** The open 2.76M is already inside `used`; `remaining` is LEASE-scoped
  (L1 14M), `executable` is PROGRAMME-scoped (30M). Two "remaining" denominators, unlabeled: that is the real defect
  (AMBIGUOUS_ECONOMIC_STATUS).
- The open 2.76M is **stranded**: journal last write 2026-10-11 17:47; leases held by dead sessions 262be369 (:12,
  1,060,540) and b8ff709c (:1, 750,000) plus one more row. Capital liveness = none.
- Same ambiguity on ccr: `goal-status` cap 70,748,921 = current lease L30, not the programme (653M, executable 358.3M).

### 1.3 ctx-rent-a2 frontier (READ)
RESUMPTION_FILE (10-11 11:26) says "do Slice B". Slice B was applied 10-11 (rules index, CLAUDE.md compaction,
backup `~/.claude/backups/rules-20261011-114632`). STALE. No re-measure recorded in plan s1.1.

### 1.4 Slice B, controlled file component (MEASURED, same five sources Slice A attributed)
| source | Slice A | now | delta |
|---|---|---|---|
| global CLAUDE.md | 39.8K | 19.2K | -20.6K |
| PP CLAUDE.md | 39.0K | 23.1K | -15.9K |
| rules/ (all .md) | 38.0K | 26.4K | -11.6K |
| MEMORY.md | 17.1K | 21.3K | **+4.2K (regrowth)** |
| ~/CLAUDE.md | 6.0K | 6.0K | 0 |
| total chars | 139.8K | 96.0K | **-43.8K (-31%)** |
Deterministic, host-independent, no session. ESTIMATE ~-12K tokens per call at ~3.6 chars/token. Not yet measured:
the provider-side call-1 floor (Slice A: 122,093). Host listings (57.5K, 25%) untouched (settings = Owner).

### 1.5 Dirty worktrees (MEASURED, `git status --porcelain`)
- `Apps\pp-ctx-rent` (ctx/rent, HEAD 0f8713fe): M rollover.py, M rollover_replay.py, M ctx-rent-RESUMPTION.md;
  ?? .pp-capabilities, ?? ce-lifecycle-amendment-A1-...-PROPOSED.md, ?? ctx-rent-s2-recovery.md.
  The S2 half-edit targets a rollover.py the live PP has since superseded (ASER live; ctx-same-pane closed).
  Class: OWNED_UNVALIDATED (2) + doc (4) -> worktree SUPERSEDED.
- `Apps\pp-ce-lifecycle-v3` (ce/lifecycle-v3): M RESUMPTION_FILE.md; 22 `WU-*.partial.json|residual.md` (steward
  output, GENERATED_REPRODUCIBLE); ?? vault/specs/salvage/. Programme parked in backlog 6d9afbb0. Worktree DURABLE_WAIT.

### 1.6 Existing owners (READ)
| need | owner | class |
|---|---|---|
| settle dead holds, forgotten goals (R2), unarmed successors | tools/mission_steward.py | PRODUCTION |
| pure next-action from durable state | modules/gsd_x/goal/reconcile.py | PRODUCTION |
| settle a session lease | `mission_spend goal-settle --measured` | PRODUCTION |
| cross-ledger consistency (ASER x goal ledger x worktrees x resumption) | none | MISSING |
| spawn replay, agent listing | estate_shadow.py, agent_estate_audit.py | unrelated |

## 2. Root-cause matrix
| incident | primitive | owner |
|---|---|---|
| 58 E4b2 retries | admission without invalidator + split-brain | UEK-1c-2, s27 |
| ~30 RAM holds | poll as wake | UEK s23 (+ 0.2 hand-off) |
| false E4 complete | unit word as closure | UEK-1c, s39-43 |
| ASER "3 unexplained" | status read without a per-subject view | R4 view + fsck |
| 2 resume_failed | EXAM_NEXT_MISMATCH | R4 (record class) |
| ctx-same-pane -9.17M | coordinator pane unbound / plan-phase overrun | fixture only (R5) |
| ctx-rent-a2 "lease > remaining" | two unlabeled denominators + stranded lease | R1 |
| stale RESUMPTION | hand-written view, no anchor check | R1 + fsck |
| Slice B unmeasured | no receipt step after a slice | R2 |
| dirty worktrees | no lifecycle state | R3 |
One shared root: **a derived answer read without checking whether its inputs moved** (or whether it had a view at
all). Candidate FIOS/UKDL pattern RECOMPUTATION_WITHOUT_CAUSAL_INVALIDATION, deduplicated in R6 against existing
entries before writing.

## 3. Residual stages (EXECUTION mode; no GSD plan-phase; no subagents)
| stage | content | commits |
|---|---|---|
| R1 | ctx-rent-a2: settle the stranded leases with `goal-settle --measured` from `goal-autopsy`; label the two denominators in `goal-status` output (`lease_remaining`, `programme_executable`; additive keys, old keys kept); regenerate RESUMPTION_FILE from ledger + git anchor; close the goal or leave it DURABLE_WAIT per frontier | 3 |
| R2 | Slice B receipt: the table in 1.4 + ONE fresh headless session censused with `tools/context_floor_census.py` (call-1 floor vs 122,093); MEMORY.md regrowth recorded as debt | 1 |
| R3 | worktrees: `git diff` + untracked saved as patches under `vault/salvage/<worktree>-2026-10-23/`, a lifecycle row each (SUPERSEDED / DURABLE_WAIT). No deletion, no branch removal | 2 |
| R4 | ASER: `rollover.py dispositions` read-only view (capsule -> claim -> verdict -> failure class), cold ledger stays cold | 1 |
| R5 | `tools/cpp_fsck.py`, zero model, read-only, 6 checks: stranded session lease (dead sid > 24 h), parked chain still polled, dirty worktree without lifecycle row, RESUMPTION anchor not in HEAD ancestry or naming sealed work, capsule without disposition, goal-status denominator unlabeled. Each with a production fixture (today's incidents), a paired admitting control, and a mutation drill on a copy. Repairs = existing verbs only, printed, never auto-run | 2 |
| R6 | KV/FIOS/UKDL: dedupe-check, then one pattern + traps; CBR only after R5 is green on a second run | 1 |

Not in scope, by the anti-abstraction gate (no observed incident needs it today): universal truth fabric, context
ABI/tool ABI/memory ABI, knowledge linker/symbol table, state-transition kernel, CBR coverage audit. They reopen
when UEK lands and a SECOND consumer of its invalidator/blocker primitive exists. HR-NOVELTY-001 applies.

## 4. Budget (ESTIMATE; slim formula as UEK s60: ~19.5K/call lower; confidence LOW-MEDIUM)
| stage | calls | lower | P50 | P80 | P95 |
|---|---|---|---|---|---|
| R1 | 10 | 0.20M | 0.6M | 0.8M | 1.1M |
| R2 | 4 + probe | 0.08M | 0.35M | 0.5M | 0.7M |
| R3 | 6 | 0.12M | 0.3M | 0.45M | 0.6M |
| R4 | 6 | 0.12M | 0.35M | 0.5M | 0.7M |
| R5 | 16 | 0.31M | 0.9M | 1.2M | 1.6M |
| R6 | 4 | 0.08M | 0.2M | 0.3M | 0.3M |
| **total** | 46 | 0.9M | 2.7M | 3.75M | **5.0M hard** |
Funding: ctx-rent-a2 programme (30M applied, executable 17.1M). No new capital. R1 itself frees up to 2.76M of
stranded reservation (net of measured spend).

## 5. Vehicle
This pane, bound to goal ctx-rent-a2, /kclear at every sealed stage. Not `/cpp-gsd-long`: every subject (goal
ledgers, ASER ledger, the two worktrees) is laptop-local, and the laptop is below the 3 GB launch floor (MEASURED
2.9 GB free at 15:11) — the same reason UEK moved to GEX44, where these subjects do not exist.

## 6. Owner variable (exactly one)
ScopeChoice: let goal ctx-rent-a2 (programme 30M) fund this residual estate/fsck work, hard 5.0M. Everything else
(settling dead leases, stale views, classification, the poll hand-off) is runtime correctness.

## 7. Return-to-Owner conditions
5.0M hard reached; any deletion or branch removal; settings.json/hook registration (HR-001); a dirty file whose
owner is a live pane; a ledger mutation the existing verbs refuse; UEK coordinator reports a conflict with R-paths.
