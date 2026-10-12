# Master Continuation Plan — Economic Safe Exhaustion (goal `econ-safex`, proposed)

Status: PROPOSED, awaiting Owner approval (first-response contract). Written 2026-10-13 by session 42372faf.
Nothing was implemented, no cap was raised, no PRR file was touched.

## 1. Reality Delta (measured 2026-10-13 ~00:45, read-only)

| Fact | Value | Source |
|---|---|---|
| PRR programme authority | 38,000,000 (`capital:3fabd7adb96b:prr:59c71317…`) | `mission_spend.py goal-lineage --goal prr` |
| PRR total used | 37,500,018 = settled 35,521,782 + open 1,978,236 | same |
| Programme left for any successor | about 499,982 | 38,000,000 − 37,500,018 |
| Lease L1 | cap 18,000,000, used 17,696,016, closed "succeeded" | lineage |
| Lease L2 (`prr:D:r2`) | cap 20,000,000, used 19,804,002, OPEN, reserves `{proof:0, closeout:0, recovery:0}` | lineage |
| L2 remaining | 195,998; recovery reserve 0 | `goal-status` |
| Succession policy | `null` (PRR never opted into automatic successors) | lineage |
| Tombstoned PRR sessions | 0917a65c, 53ab0382, f6c19b3d | `goal-status` |
| Capital packet | `prr-l2-successor-20m-2026-10-12.json`: `"proof_reserve": 0`, stop_loss includes "L2 exhausted" | state/capital-authority/packets |
| Last PRR pane context | 244,704 tokens resident; next request estimated about 245.6K (lastTotal 245,566 + max delta) | session-budget-0917a65c….goal.json |
| PRR HEAD | `f6455676` on `prr/main` (evidence E), worktree `C:\Users\User\Apps\pp-prr` | git |
| PRR dirty files | M `vault/knowledge_base/ukdl-universal.md`, M `vault/liveness/reachability_registry.json`; ?? `modules/prr/__init__.py`, `modules/prr/bench/__init__.py` (the two init files), `modules/prr/pgo.py`, `tests/test_prr_pgo.py`, `vault/programs/prr/pgo/profiles.jsonl`, `.pp-capabilities`, 12 generated `docs/{arch,changelog,constitution,prd}/*` | `git status` |
| PRR proof state | "tests green" is a claim from the dead pane only. The liveness gate (`modules/liveness/reachability.py`) has not run on these files. | prompt + RESUMPTION_FILE |
| Concurrent writers on pp-prr | none observed. Coordinator pane ce64704d and the 3 PRR sids are tombstoned. | goal-status |
| This session's economic binding | NONE (no goal-binding, no session-budget file): this mission has no envelope yet | state/goal-binding |
| UserPromptSubmit | 3 entries: `econ_admission.js` (30 s), `hook-dispatcher.js --event=UserPromptSubmit-chain` ("Loading Power Pack…", **15 s**), orca hook (10 s) | settings.json |
| Hook failures (tail of dispatcher log) | `CHAIN-DEADLINE-ABANDONED before pool: critical lane used 6,560–12,321 ms of 3,000 ms`; `dead-closer-recovery.js ETIMEDOUT after 6000ms` (CRITICAL-GUARD-INERT, 198 rows in the last 4,000 lines); host free RAM 2,193 MB of 32,061 MB (6.8 %) | `~/.claude/logs/hook-dispatcher-errors.log` (117 MB itself) |

**Premise corrections (iteration protocol, CLASE 2):**
1. "Programme Authority may remain above the exhausted lease" is mostly false. About 0.5M remains, so it can fund a small cold recovery lease and nothing productive.
2. The guard did not fail. Reserve classes already exist (`RESERVE_KEYS = proof, closeout, recovery`, `lease_open(reserves=…)`, RECOVERY role, `_auto_succeed`), but every one was funded at **0**.

## 2. Incident reconstruction and root cause

The refusal text comes from `ledger.py:649-650` (`budget_spent … after one final reply per live pane, N is left, less than one call`).
1. **Unfunded reserves (root).** The packet compiler wrote `proof_reserve: 0`, and L2 opened with all three reserves at 0. Productive renewals therefore drew on capital that closeout needed.
2. **Closeout cost scales with resident context.** One boundary cost about 245K because the pane held about 245K of context. The proof/commit tail (liveness gate, test rerun, pathspec commit: about 4–6 calls) needed about 1.0–1.5M in that pane, but only about 30–60K per call in a fresh session. Nothing priced closeout or rotated to a cheap closeout epoch.
3. **Goal mode has no predictive edge.** The `LEASE EDGE` advisory (`session_budget_guard.js:132-139`) runs only in session-envelope `judge()`, not in `decideGoal()`. A goal-bound pane learns of exhaustion only at the refusal, and its closeout allowance is then 1 handoff write with no reads (`closeout(..., goal=true)`).
4. **No successor path.** `succession: null` plus about 0.5M of programme left means `_auto_succeed` could not run, and the packet's own stop-loss names "L2 exhausted" as terminal. Exhaustion ended the goal, not just the lease.
5. **`/clear` does not help, by design.** The tombstone is per sid, and a new session in the worktree binds by cwd to the exhausted L2. This is correct (cognitive epoch ≠ economic authority), but no recovery lease existed for the new session to bind to.

| Incident class | Verdict |
|---|---|
| LEASE_EXHAUSTED_BEFORE_DURABLE_CLOSEOUT | CONFIRMED |
| CLOSEOUT_RESERVE_UNDERPROVISIONED | CONFIRMED (0) |
| PRODUCTIVE_SPEND_CONSUMED_CLOSEOUT | CONFIRMED |
| PRE_BOUNDARY_ECONOMIC_ADMISSION_TOO_LATE | CONFIRMED (goal mode has no edge) |
| MODEL_DEPENDENT_DETERMINISTIC_CLOSEOUT | CONFIRMED (closeout lived in model memory + RESUMPTION prose) |
| DIRTY_WORKTREE_AT_CAP_EXHAUSTION | CONFIRMED (18 paths) |
| SUCCESSOR_LEASE_NOT_COMPILED | CONFIRMED (policy null; programme about 0.5M) |
| PROGRAMME_AUTHORITY_LEASE_DIVERGENCE | REJECTED for PRR (lineage coherent); keep a guard |
| COGNITIVE_ROTATION_CONFUSED_WITH_ECONOMIC_AUTHORITY | PARTIAL (runtime is correct; the deny text offers `/clear` without saying it cannot fund closeout) |
| RECOVERY_CAPSULE_MISSING | CONFIRMED (no structured capsule; RESUMPTION_FILE predates the dirty PGO work) |
| CHECKPOINT_HORIZON_MISSING | CONFIRMED |
| USER_PROMPT_HOOK_INITIALIZATION_TIMEOUT | CONFIRMED. Causal hypothesis: a sequential critical lane that the 3 s chain deadline does not bound, plus RAM starvation → node cold start + `dead-closer-recovery.js` child > 15 s harness kill |

## 3. Owner map

| Capability | State | Action |
|---|---|---|
| GoalLedger / lease epochs / programme (`provider_routing/ledger.py`) | ACTIVE | EXTEND (reserve floor, state fold, authority fingerprint) |
| Reserve classes proof/closeout/recovery | IMPLEMENTED, funded 0 | EXTEND: non-zero floor; UNKNOWN ≠ 0 |
| Pre-boundary admission (goal mode, `session_budget_guard.js decideGoal`) | ACTIVE, reactive only | EXTEND with checkpoint horizon + CLOSEOUT_ONLY verdict |
| Pre-model admission (`econ_admission.js`) | ACTIVE | CONNECT (reads lease state) |
| Closeout allowance | PARTIAL (1 write) | MERGE into CLOSEOUT_ONLY |
| RECOVERY role | IMPLEMENTED_NOT_HOT_PATH | CONNECT to recovery capsule + closeout executor |
| Automatic successor (`_auto_succeed`, `set_succession`) | IMPLEMENTED, opt-in, unused by PRR | EXTEND: packets compile a policy by default; zero-progress guard |
| Capital packets (`state/capital-authority`) | ACTIVE | EXTEND: reserves required, successor tranche from P80 |
| Mission Recompiler / `gsd_epoch` no_progress halt | ACTIVE | CONNECT (zero-progress renewal guard) |
| CCR boundary forecast | ACTIVE (installed 2026-10-11) | CONNECT (P50/P80 next boundary); no duplicate forecaster |
| /kclear capsule + /kresume | ACTIVE | CONNECT as the Recovery Capsule substrate |
| UWCP | NO_WORK (no positive ROI shown) | — |
| Hook dispatcher / Hook Guardian (CRITICAL-GUARD-INERT, chain deadline) | ACTIVE | EXTEND: bounded critical lane + fast path |
| dgl (durable goal lease, W5 PARTIAL, deploy pending Owner) | PARTIAL | VERIFY first (lease epochs are already live in the ledger) |
| Knowledge Vault / FIOS / UKDL / CBR | ACTIVE | EXTEND at the end |

## 4. Target design (compact)

- **Protected capital:** `productive_spendable = lease_cap − used − Σ(unconsumed reserves) − headroom(final replies)`. Productive renew draws only from productive_spendable. Reserves are spent only by the CLOSEOUT/RECOVERY roles. One fold in `_gfold`, no second ledger.
- **Dynamic reserve sizing:** `closeout_reserve = P80(closeout calls by work class) × per_call(fresh-epoch floor)`. Missing history means a floor of 6 calls × max(measured fresh-session floor, 60K) and never 0. `mutation_liability` rises with each dirty path (tests to rerun, gates, commit). The proof reserve covers the gates in the compiled recipe.
- **States (derived fold over journal + worktree probe, no new store):** OPEN → APPROACHING_RESERVE (horizon < 2 × P80 next boundary) → CLOSEOUT_ONLY (productive_spendable < P80 next boundary) → SEALED (outcome receipt ∈ {VERIFIED_COMMITTED, SEALED_RECOVERABLE, ROLLED_BACK, EXPLICIT_EXTERNAL_WAIT}) → SUCCESSOR_READY → EXHAUSTED. **Invariant: EXHAUSTED ⇒ SEALED.** `lease_close` refuses without an outcome receipt. A tombstone on a dirty, unsealed tree fires the model-free capsule writer.
- **Pre-boundary admission (goal mode):** ADMIT / DEFLATE (advise smaller step) / CLOSEOUT_ONLY (only recipe paths, gates, commit, capsule) / SETTLE_AND_RENEW / RECOVERY_SEAL / DENY / OWNER_BOUNDARY. All are decided before the call. The current deny stays as defence in depth.
- **Checkpoint horizon:** expected tokens to the next coherent commit = remaining recipe steps × P80 per-call. Admission refuses to start a new branch of work when horizon + reserve > spendable.
- **Closeout compiler + deterministic executor:** `tools/closeout_recipe.py compile|run|verify`. The recipe is JSON: allowed paths, exact test commands, gates, pathspec, message file, rollback ref, postcondition, sha256 of each dirty file. `run` executes with zero model calls. The economic role is CLOSEOUT, paid from the closeout reserve (tool time only).
- **Recovery capsule:** the kclear capsule schema extended with HEAD, dirty paths + hashes, diff id, test receipts, gates passed/missing, ownership, next obligation, safe ops, rollback ref, commit scope, authority state, invalidators. /kresume validates the hashes before use.
- **Programme/lease coherence:** an `authority_fingerprint = sha256(programme value + source + succession policy)` appears in lineage. Each lease records the fingerprint it was opened under. A mismatch emits `authority_divergence` (typed incident), and the lease refuses to grow until the mismatch is reconciled.
- **Successor compiler:** extends `_auto_succeed`. Size = min(policy tranche, P80(residual) + reserves) and never the whole programme. A successor requires the prior lease SEALED, the same goal, scope and fingerprint, and a non-zero-progress classification (no commit or tree change across the last lease means no renewal, which hands the run to the Mission Recompiler).
- **Goal liveness:** each lease end records exactly one of ACTIVE / SUCCESSOR / DURABLE_WAIT / OWNER_BOUNDARY / EXTERNAL_WAIT / TERMINAL. Anything else is a typed liveness incident.
- **Hook fast path:** measure first (P50/P80/P95 from a new per-member latency row, plus the existing log). `dead-closer-recovery.js` gets a stat-only fast path that spawns or parses only when the heartbeat shows a dead turn. The critical lane gets its own bounded budget inside the 15 s harness. Advisory members move after admission or stay best effort. The timeout is not raised unless measurement after the fix proves a host floor.

## 5. Mode by workstream and token budget (tokens processed)

| WS | Work | Mode | P50 |
|---|---|---|---|
| W0 | Incident reconstruction from transcript 0917a65c (last 10 boundaries, horizon replay) | EXECUTION | 1.0M |
| W1 | Reserve accounting, floor, packet compiler | PLAN→EXECUTION | 2.5M |
| W2 | Goal-mode pre-boundary admission + checkpoint horizon | EXECUTION | 2.5M |
| W3 | Lease state fold + transactional expiry + liveness record | ULTRA-PLAN (ownership) → EXECUTION | 2.5M |
| W4 | Closeout compiler + deterministic executor | PLAN→EXECUTION | 3.0M |
| W5 | Recovery capsule (kclear extension) | EXECUTION | 1.5M |
| W6 | Successor compiler, zero-progress guard, authority fingerprint | ULTRA-PLAN (authority semantics) → EXECUTION | 3.0M |
| W7 | Fault-injection suite (17 cases) + PRR regression fixture (V-SAFEX-*) | EXECUTION | 2.5M |
| W8 | PRR stranded-work recovery | EXECUTION | 0.45M (PRR's own programme) |
| W9 | Hook root cause + fast path + P50/P80/P95 | EXECUTION | 2.0M |
| W10 | Knowledge / FIOS / UKDL (HR, PR, Traps) / CBR | EXECUTION | 1.5M |
| W11 | Self-host canary: this mission's leases run under the new protocol | EXECUTION | 1.0M |
| — | Meta-optimization tax (coordination, iteration passes, reviews) | — | 2.0M |
| — | Recovery reserve | — | 1.5M |

**Budget:** semantic lower bound 9M · LOWER 15M · **P50 24M** · **P80 31M** · P95 42M · confidence medium-low (±35 %; this estate's measured floor is 100–215K per call).
**Hard authority requested:** programme **32,000,000** for goal `econ-safex`, issued as leases of at most 6M. Each lease carries reserves proof 300K + closeout 600K + recovery 300K. Automatic succession is ON (tranche 6M, keep 1.2M) so the mission self-hosts. P95 overrun means an AUTHORITY_REQUIRED Owner boundary, never a silent raise.

## 6. PRR recovery contract (W8, executed only after W1–W5 are green)

- **Authority:** a new recovery-only lease L3 inside the existing PRR programme (executable about 499,982; no new PRR authority), role RECOVERY, run in a fresh cold session (small context) using a compiled recipe.
- **Verify:** recompute the hashes of the 18 dirty paths; confirm HEAD = `f6455676` and no other writer; read the diffs; run `tests/test_prr_pgo.py` + the PRR suite; run `python modules/liveness/reachability.py` (the missing gate); run the control check named in the PRR plan.
- **Commit scope:** commit 1 = `modules/prr/__init__.py`, `modules/prr/bench/__init__.py`, `modules/prr/pgo.py`, `tests/test_prr_pgo.py`, `vault/programs/prr/pgo/profiles.jsonl`, `vault/liveness/reachability_registry.json`. Commit 2 = the `ukdl-universal.md` hunks, after inspection. The 12 generated `docs/*` and `.pp-capabilities` are inspected, then committed separately or left untracked with a reason. Nothing is committed blind.
- **Rollback:** `f6455676`, plus a patch bundle of the dirty state saved before anything else.
- **Fallback:** if a gate fails or capital runs short, write a SEALED_RECOVERABLE capsule.
- **Certificate:** `vault/programs/prr/evidence/F-stranded-recovery.md` records the outcome class, commit hashes, gate receipts and a ledger delta.

## 7. Fault-injection matrix (V-SAFEX-*, deterministic, no provider calls)

Clean, validated-dirty and unvalidated-dirty tree at the reserve; next call > forecast; tests > forecast; final gate failure; commit failure; crash before seal; crash after seal; programme remaining vs exhausted; stale authority cache; successor issuance failure; zero-progress lease; external wait; hook startup timeout; capsule resumed by a fresh successor; **PRR replay** (20M lease, about 245K per call, dirty validated + 1 gate pending). The replay must show productive admission stopping at about 19.0M with 1.0M+ protected, and closeout running or the capsule being sealed with no stranded state. Each refusal case is paired with an admitted control.

## 8. Self-host sequence

1. Owner approves.
2. Declare goal `econ-safex` (programme 32M, succession policy) from a fresh worktree `C:\Users\User\Apps\pp-econ-safex` (branch `econ/safe-exhaustion` off `b4dc16ea`).
3. Arm a Ralph mission (`gsd_mission.py arm`) over the W0–W11 roadmap.
4. W1–W3 land; from W4 on, the mission's own leases run under the new protocol (W11 evidence).
5. W8, then W9, then W10.

## 9. Owner approval surface (one reply)

- **Scope:** W0–W11 as above. Global impact: ledger, goal guard, capital packets, hook dispatcher (`~/.claude/hooks`, HR-001 global config).
- **New authority genuinely required:** (a) programme 32M for `econ-safex` (no existing authority covers this mission; this session is unbound); (b) open PRR recovery lease L3 inside PRR's remaining about 0.5M (no PRR raise); (c) edits to the global hook dispatcher.
- **Rollback:** every unit is a revertible micro-commit; the ledger changes are additive journal ops; kill switches are `CPP_LEASE_EDGE=off` (existing) and `CPP_SAFEX=off` (new).
- **Canary:** fixture suite → self-host mission leases → PRR recovery → one other live goal in observe mode only.
- **Returns to the Owner only on:** AUTHORITY_REQUIRED above 32M, a PRR gate failure needing a scope decision, a merge to main, or turning safe-exhaustion from observe to enforce on other live goals.

Reply **"approve econ-safex 32M"** to approve all of it, or name the items to strike.
