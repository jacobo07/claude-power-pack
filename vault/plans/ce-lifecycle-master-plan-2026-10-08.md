---
id: PLAN-CE-LIFECYCLE
title: Process Lifecycle + Context Rent -- one lifecycle, zero Owner supervision
status: APPROVED (Owner "y" 2026-10-08, all section-10 defaults accepted; item 4 TTY rebind is the Owner's to run)
date: 2026-10-08
pane: bf948408-340e-4be1-99b5-db2a4be48834 (cwd main checkout, UNBOUND to any goal -- itself evidence)
covers: [ce-lifecycle, process-lease, pre-model-admission, goal-binding, checkpoint-reserve, lifecycle-decide, successor-arm, dead-session-trap]
consolidates: vault/specs/context-rent-extinction.md (ctx-rent, APPROVED) + A4 L0 packet (pp-ce-a4, unrun) + presence seed ce-lifecycle-hard-budget-reality-scan-seed.md
bootstrap: the Owner's ULTRA prompt of 2026-10-08 is retired by this file. Successors read THIS file's section 9 packet only, never the prompt.
---

# 1. Reality (every row has a source; labels MEASURED / ESTIMATED / INFERRED / UNKNOWN)

| # | Fact | Label | Source |
|---|---|---|---|
| F1 | Goal binding precedence is env `CPP_GOAL` > cwd under a goal's roots > `session-budget-<sid>.json`.goal | MEASURED | hooks/session_budget_guard.js:193-206 |
| F2 | The goal guard runs only at PreToolUse (`decide()` per tool call). No budget hook exists on UserPromptSubmit, so every refused turn is paid for in full before the deny | MEASURED | session_budget_guard.js:390-402; grep UserPromptSubmit hooks/ (correction-guard, d2a_gate, dead-closer-recovery, gsd_x_tier only) |
| F3 | Dead-session trap: session b1d0da50 (cwd pp-ce-presence) was measured under ce-presence-3, at 293,479 used and ~146K context per refused call. ce-presence-3 is at 5,871,336 of 2,000,000 (294 %) and ce-presence at 9,813,571 of 6,000,000 (164 %) | MEASURED | goal-status; state/session-budget-b1d0da50*.goal.json; goal-budget/ce-presence-3/spend.journal.jsonl seq 27-29 |
| F4 | ce-presence-3 and ce-lifecycle have `roots: []`. The pane's cwd root maps to `ce-presence`, yet it was bound to ce-presence-3 and survived `/clear`. Only env `CPP_GOAL` (process-scoped, which `/clear` does not reset) explains that; no launcher sets it | INFERRED (strong) | index.json; grep CPP_GOAL (tests only) |
| F5 | Self-declared authority: the f5f5a496 pane declared `ce-lifecycle` cap 8,000,000 ("owner-diy-1008") on its own. A NEW goal needs no Owner proof; only a raise or rebind needs `--owner` on a TTY. That pane then spent 1,354,978 at ~132-137K per call looking for a plan that did not exist, and wrote nothing | MEASURED | goal-budget/ce-lifecycle journal; transcript f5f5a496 tail; `goal-declare --help` |
| F6 | Owner-as-supervisor: A4 coordinator f883c056 was stopped by its session breaker at 651,154 > 0.6M (~51K overshoot) and told the Owner to open a fresh pane, although goal ce-a4 had 21.59M remaining | MEASURED | pp-ce-a4/vault/plans/ce-a4-RESUMPTION.md; goal-status ce-a4 |
| F7 | The zero-Owner successor substrate already exists for missions: `gsd_mission.py arm` -> PREPARED -> the PP-GsdLongRun-Sweep launches it within 5 min. The sweep is alive (last run 11:21, result 0) | MEASURED | Get-ScheduledTaskInfo; state/gsd-sweep-heartbeat.json 11:22 |
| F8 | Semantic rotation already exists for interactive panes: /kclear -> SAFE_TO_FORGET -> /clear -> /kresume (510 seals, 201 safe resets, 207 certified, 22 failed in 7 days), typed by `rollover_autotype.js` only into Orca/PP-Sessions-owned panes. Provider /compact is already fallback-only | MEASURED by ctx-rent S0 (re-measured in S1) | vault/specs/context-rent-extinction.md section 1 |
| F9 | Rotation is late: maximum resident context before a safe reset is p50 450,053 / p90 482,706. Causes: MIN_GROWTH_TOKENS=150K (RC1), evaluation only on a new HEAD at >=20 % (RC2), an unconditioned prior that makes CONTINUE unreachable (RC3), successor rehydration p50 1.78M before the first mutation (RC5) | ESTIMATED | same spec, RC1-RC6 |
| F10 | Fresh floor: first call ~105K (MEASURED, gen2 S1). CPP instruction files ~52K of it (ESTIMATED). This pane's own calls cost ~130-150K: floor plus the ~11K bootstrap prompt | MEASURED / ESTIMATED | gen2 S1-decomposition.md; ce-lifecycle per_call 132,233 / 136,887 |

**Root-cause reconstruction of the "hundreds of thousands per ordinary turn":**
- Hard floor: ~105K. Host-controlled for the system and tools part; CPP-controllable for ~52K of instruction files.
- Dead-context rent: in a long pane, everything between the floor and the frontier. At the p50 rotation point that is ~450K - 105K - frontier ≈ 300K+ per call, carried because RC1/RC2 forbid an earlier rotation.
- Dead-pane tax: ~150K per refused turn, all floor plus prompt (F2, F3).
- Calls that never needed a model: goal-status, plan search, binding, arming and closeout (F5: 1.35M on a lookup with no target).
- Why nothing intervened: lease edges and context edges are two separate mechanisms with different executors, neither acts before the model, and binding is an ambient env var.

# 2. Ownership map (extend, never duplicate)

| Concern | Canonical owner (existing) | This plan |
|---|---|---|
| Goal authority / leases | tools/mission_spend.py GoalLedger | extend: supersession, terminal state, Owner proof on NEW caps |
| Per-call admission | hooks/session_budget_guard.js | extend: checkpoint reserve; shared binding resolver |
| Pre-model admission | (none) | NEW chain entry in the existing UserPromptSubmit-chain of hook-dispatcher.js |
| Context-edge decision | tools/rollover_econ.py + hooks/rollover_wall.js | ctx-rent S1-S4, S6-S8 (unchanged, approved) |
| Semantic checkpoint | commands/kclear.md, capsule-v2 card | reused as the checkpoint for BOTH edges |
| Focused resume | commands/kresume.md | ctx-rent S2 (obligation-scoped projection, page on miss) |
| In-place physical clear | hooks/rollover_autotype.js | reused (owned panes) |
| Process successor | tools/gsd_mission.py arm + sweep | reused for non-owned panes and workers |
| Process identity | modules/cpc_os/beacon.py (ancestor claude.exe pid) | reused as the binding key |
| ContextImage | capsule-v2 card + /kresume projection | no new store. "ContextImage" = the compiled /kresume projection |
| Telemetry | rollover ledger + goal journals (FIOS feed) | add event kinds only |

**De-duplication decisions (part of the approval):**
- (D1) A4's L0 lifecycle packet is SUPERSEDED by this plan. A4 keeps W0-W3, the estate rearm.
- (D2) ctx-rent S5 (budget edge / pre-model admission) moves to track L here and is removed from ctx-rent.
- (D3) The ce-presence seed is closed by section 1.

# 3. Contracts

- **Semantic compaction = kclear-equivalent.** The capsule-v2 card holds goal, obligation, state fingerprint (HEAD + dirty set), sealed decisions, facts, effects, proof frontier, unknowns, authority snapshot, budget lineage, refs and next frontier. SAFE_TO_FORGET = the card was written, re-read from disk and hash-verified, and every required field is present. A missing field means NOT safe (mutation-tested, canary 3).
- **Clear = physical deallocation.** The success test is that the successor's first request does not contain the predecessor's transcript: a new sid and a first-call size near the floor. An owned pane gets autotyped `/clear`. Any other pane is made QUIESCENT (see L1) and replaced by an armed successor. Summarizing in place never counts as deallocation.
- **Focused resume = /kresume projection.** It carries the goal projection, the exact Work Unit, live decisions and facts, open unknowns, the affected proof, authority, budget and minimal refs. It never replays the transcript. A miss pages one exact ref (ctx-rent S2). Rehydration C must fall >=30 %, otherwise PLAN mode.
- **Provider compact** is a fallback only. Each one becomes a `compact_fallback` ledger event, counted as lifecycle debt (ctx-rent S6).

# 4. One lifecycle decision (L4): `lifecycle.decide(state) -> KEEP | ROTATE | DETERMINISTIC | WAIT | HANDOFF | APPROVAL`

Inputs (all already measured or measurable): resident tokens, measured floor, live frontier estimate (capsule size + refs touched in this epoch), Marginal Context Rent (MCR = resident - floor - frontier, per call), recent per_call p90, successor cost C (measured rehydration), next Work Class, lease remaining minus reserve, goal remaining, boundary kind (commit / clean tree / task done / Owner question / BLOCKED / WAITING).

Rule (no fixed N; the 45 % wall and autocompact stay as safety nets):
- ROTATE when, at a boundary, `MCR × expected_remaining_calls_in_epoch > C + expected_page_cost`. The expected remaining calls come from the Work Class profile (ctx-rent S4 state-conditioned prior). Also ROTATE on lease edge (lease remaining <= reserve) or on a Work Class change, for example research -> implementation.
- KEEP when the next unit's refs overlap the current epoch's refs (locality) and the inequality fails. This guard exists so a high-locality pane is not rotated just to move a metric (canary 2). The derived minimum growth replaces MIN_GROWTH_TOKENS, which blocks micro-epochs.
- DETERMINISTIC when the next unit is a runnable command (proof run, arm, status, receipt check). Run it below the model and start no successor (canary 8).
- WAIT on BLOCKED or WAITING: checkpoint, then QUIESCENT, then nothing hot. Resume only on an event (sweep / notification), never by polling (canary 7).
- APPROVAL when goal authority is exhausted. Exactly one semantic question to the Owner; on no, the goal becomes durably quiescent.
- Anti-Goodhart: the policy judges total verified cost per epoch (calls × tokens + page faults + repair). If page faults per epoch go above the profile bound, the profile's minimum epoch is raised by data, never by hand (Semantic PGO, rollover_replay.py).

Executors, chosen by pane class (no new executor): an owned interactive pane gets autotype /kclear -> /clear -> /kresume. A non-owned pane, worker or coordinator gets /kclear, then `gsd_mission.py arm` of the successor under the SAME goal with the card as packet, then the old pane goes QUIESCENT. A deterministic next unit goes to its runner. Parent/Agent: a parent with no semantic work while a child runs returns WAIT (canary 12). Child results come back as receipts (decision, effect, proof, unknowns, refs), never as transcripts.

# 5. Process authority + hard budget (L1-L3)

- **L1 Pre-model admission (UserPromptSubmit).** It uses the shared binding resolver. If the bound goal is exhausted, terminal or superseded, or the session is QUIESCENT, it returns `decision:"block"` with a deterministic one-line status ("goal X exhausted -- successor m-… running" / "approval needed: …"), and no model turn is bought. It must first prove that the dispatcher passes UserPromptSubmit blocks through (memory: the dispatcher has swallowed blocks before) by driving the red branch end-to-end. Residual, documented: autonomous turns after a tool result never pass UserPromptSubmit. They stay bounded by the PreToolUse deny plus one closing reply (already measured at 1 reply per pane after a deny, canaries #2-#6).
- **L2 Canonical binding.** At SessionStart the binding is resolved once, written to `state/goal-binding/<sid>.json` keyed by beacon pid lineage, and then immutable for the process. Precedence: launcher/arm record > cwd root > none. Ambient `CPP_GOAL` is accepted only from a launcher that writes the record (gsd_mission arm, kclaude) and is otherwise ignored, with a ledger warning. The goal entry gains `state: live|exhausted|quiescent|superseded` and `superseded_by`; a successor binding never inherits authority it does not have. **Anti-laundering:** a NEW goal cap needs the same `--owner` proof as a raise, or an Owner-approved plan id in `--source` that the resolver verifies exists in vault/plans with status APPROVED. Overlapping roots between two live goals are refused at declare time.
- **L3 Checkpoint reserve + preemptive checkpoint.** Each lease = work portion + reserve, with reserve = max(2 × recent p90 per_call, measured kclear cost). When `measured + next > base + work portion`, the session enters CHECKPOINT. The only calls admitted are kclear writes and the successor arm, which generalizes today's fixed "1 closeout call" into a measured reserve. The reserve can never fund substantive work. Lease edge with goal remaining -> L4 HANDOFF, zero Owner operations (canary 9).

# 6. Floor, prompt, read and transport extinction

- **Floor** (ctx-rent S8, Owner "y+floor" already given): decompose the 105K into host / CPP / frontier, then trim the CPP instruction files. Candidate retirements once L4 enforces them:
  - project CLAUDE.md "Session Cost Discipline #1 /compact al 70%";
  - the global "Context Pressure Response /compact line";
  - manual "/kclear when …" guidance.
  At least one is retired; the measured floor delta is the proof.
- **Read extinction:** /kresume reads the card, not the source docs. The A4 / ctx-rent RESUMPTION files become projections of the card.
- **Transport extinction:** successors receive refs and deltas, never this prompt (frontmatter `bootstrap:`).
- **Prompt extinction of THIS mission:** section 9 is the only successor input, under 6K tokens.

# 7. Telemetry, CI, knowledge, CBR

- **FIOS / ledger:** new event kinds `epoch_close{reason}`, `premodel_block`, `checkpoint_reserve_enter`, `successor_armed`, `quiescent`, `compact_fallback`, `page_fault{ref}`, each carrying a MEASURED/ESTIMATED/INFERRED/UNKNOWN label. MCR and Semantic Payload Efficiency (frontier ÷ resident) are computed by `rollover_replay.py` offline and deterministically. No new store.
- **Cognitive CI:**
  - `tools/test_context_economics.py` (ctx-rent S7) plus `tools/test_process_lifecycle.py` (V-LIFE-*), with positive controls and mutants;
  - regressions flagged: a dead pane accepting a model turn, rotation p50 regressing above the frozen baseline, compact_fallback becoming the dominant reason, /kresume over the projection budget, lease exhausted before a checkpoint, a manual successor required while goal authority remains;
  - registered in `/liveness`.
- **Knowledge Vault / UKDL:** failure classes are deduplicated into existing ids where they exist (grep T-UNBOUNDED-SESSION-001, T-PANE-MAP-*, CLAE traps first). The candidate hard rules from the prompt land as at most 4 HR, 1 PR and N T entries after dedupe. Origin evidence goes to wiki/.
- **CBR:** each verified guarantee becomes a gate in the completion baseline (test file + reachability). The always-on text it replaces is retired in the same commit.

# 8. Units, authority, rollback

Authority: goal **ce-lifecycle** (cap 8,000,000; 6,645,022 remaining; the open 684K lease of dead pane f5f5a496 settles at its actual). The cap is CONFIRMED by the Owner's reply, because it was self-declared (F5). ctx-rent units stay under goal ctx-rent (6M). Coordinator: this pane, <= 0.4M more, then it ends (section 9).

| Unit | Track | Deliverable | Proof | Cap |
|---|---|---|---|---|
| ctx-S1 | ctx-rent | rent meter + frozen baseline | baseline-2026-10-08.md, labels | per ctx-rent spec |
| L1 | lifecycle | UserPromptSubmit pre-model block + dispatcher pass-through | V-LIFE-PREMODEL-* red/green; canary 10 live on a quiescent test goal | 1.0M |
| L2 | lifecycle | binding record + goal state/supersession + anti-laundering declare | V-LIFE-BIND-*; replay of F3/F4/F5 now refused | 0.8M |
| L3 | lifecycle | checkpoint reserve + CHECKPOINT state | V-LIFE-RESERVE-*; mutant "reserve funds work" goes red | 0.8M |
| ctx-S2..S4,S6 | ctx-rent | /kresume diet, wide boundary, policy, fallback event | per spec | per spec |
| L4 | lifecycle | `lifecycle.decide` + executors wired into rollover_wall and session_budget_guard | canaries 7,8,9,12,15 live | 1.5M |
| L5 + ctx-S7/S8 | both | CI, KV/UKDL/CBR, floor trim, prompt retirement | test files exit 0; floor delta MEASURED | 0.8M |

Order: S1 and L1 run in parallel (disjoint files), then L2 -> L3 -> L4. S2-S4 can run alongside L2/L3, with at most 2 live missions. Each unit is a slim-worker mission armed with a packet; each lands as micro-commits on `ce/lifecycle` (worktree `C:\Users\User\Apps\pp-ce-lifecycle` off 86ad6f16). No push.
Rollback: each unit is one revertible commit series plus kill switches `CPP_PREMODEL_GATE=0`, `CPP_LIFECYCLE_DECIDE=0`, `CPP_CHECKPOINT_RESERVE=0`, and the existing `CPP_ROLLOVER_*`. Hooks deploy through the existing copy-and-verify path with a `~/.claude/backups` snapshot (HR-001 applies to ~/.claude writes).

**Canaries:**
- ctx-rent: 1, 2, 3, 4, 5, 6, 11, 13, 14.
- lifecycle: 7, 8, 9, 10, 12, 15.

Canary 15 (self-host) means two things. First, this pane's own end is the first zero-Owner handoff: it arms L1/S1 through the sweep and then stops, and no Owner command follows. Second, the full form: after L4 lands, a mission epoch boundary goes through decide -> kclear -> deallocate -> armed successor, with no coordinator pane alive.

**Master Done-Gate:** every clause of the prompt maps to one of the following.
- (a) V-LIFE-* and the context-economics gates exit 0.
- (b) Ledger evidence from real panes: p50 resident-before-rotation below 450K, C down >=30 %, >=1 KEEP, >=1 ROTATE, >=1 DETERMINISTIC, >=1 WAIT, >=1 premodel_block, >=1 zero-Owner HANDOFF while the goal had authority.
- (c) A before/after economics table: calls, processed tokens, floor, rehydration, page faults, repair, latency.
- (d) /liveness and the router freshness gate.

Any clause not reached is reported UNKNOWN/DEFERRED, never PASS.

# 9. Successor packet (the ONLY input for the next epoch)

Goal ce-lifecycle. Worktree pp-ce-lifecycle, branch ce/lifecycle. Read this file's sections 4, 5 and 8 only. Unit = the next unarmed row of section 8. Do not read the bootstrap prompt, the A4 card or the presence seed. On completion, write the receipt `vault/programs/cognitive-economy/lifecycle/<unit>-receipt.md` (decision / effect / proof / unknowns / refs) and arm the next row. Coordinator panes do not wait on workers.

# 10. Owner decisions folded into the one reply (defaults in brackets)

1. Confirm the ce-lifecycle cap at 8M [yes].
2. D1: A4 L0 superseded, A4 keeps W0-W3 [yes].
3. D2: ctx-rent S5 moves here [yes].
4. One TTY command, needed once because rebind is Owner-gated by design: `python tools\mission_spend.py goal-declare --goal ce-lifecycle --cap 8000000 --source vault/plans/ce-lifecycle-master-plan-2026-10-08.md --root C:\Users\User\Apps\pp-ce-lifecycle --owner` [the Owner runs it]. L2 removes the need for this step in future missions.
5. Production canaries spend subscription quota, and are deferred if the weekly limit is near [yes].
