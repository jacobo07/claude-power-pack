---
status: APPROVED (Owner one-click, 2026-10-07, session 9de9bf3b) -- executing as Ralph mission, workstream gsdx-pcc
tier: T3 (new execution semantics for GSD X; cross-repo baseline)
covers: [gsdx-pcc, proof-conserving-convergence, causal-proof-binding, execution-frontier, verification-amortization, constitutive-baseline-ratchet, proof-certificate, minimal-sufficient-verification, impact-adapter-contract, mutant-farm, latency-observatory]
source: C:\Users\User\Downloads\Dataset GSD X Incremental Construction Runtime 1.md (2111 lines, 46 sections) -- design INPUT, not implementation truth
base: branch gsdx/pcc from feature/knowledge-acquisition@fbca24fc, worktree C:\Users\User\Apps\pp-gsdx-pcc
denominator: .planning/workstreams/gsdx-pcc/DENOMINATOR.md
---

# GSD X -- proof-conserving convergence

## Root function

GSD X minimizes TIME TO PROVEN CONVERGENCE. Quality is a constraint, never a variable:
semantic completeness, proof completeness, evidence strength, Production Reality, judge
independence, security and authority never decrease; UNKNOWN never becomes PASS; unmapped
impact never becomes "unaffected"; fresh-required evidence is never inherited; and no
optimization may hide a failure the incumbent full path detects. Wall-clock is the target;
compute/tokens are budgeted resources (posture ECONOMY | BALANCED | WALL_CLOCK, owned by
the goal budget, never authorising spend the existing policy forbids).

## Reality Scan (2026-10-07; P = read in source, O = observed by running)

1. P `goal/reconcile.decide` returns ONE Decision; WAIT on the first running epoch (reconcile.py:148); only `ungated[0]` is dispatched (:205).
2. P `goal/sweep.sweep_goal` applies one decision per pass (sweep.py:308-390).
3. P `goal/judge.judge` re-runs every SATISFIED gate serially; no VALIDATE path (judge.py:146-179).
4. P Binding is coarser than the dataset assumed: a clean `tree_id` is `HEAD^{tree}` of the WHOLE repository (git_state.py:129-133). Any commit anywhere stales every proof; the reconciler then re-runs them all (`_needs_a_gate_here`).
5. P `tools/change_impact.py` is Python-only (rglob *.py, :37-49), no adapter abstraction; its UNKNOWN is the vendored analyzer's `gaps[]` (exit 3) / UNJUDGED (exit 2).
6. P GK-13 (additive/widening/narrowing/replacing; direct/transitive/frontier) exists ONLY as `vault/knowledge_base/graphify/graphify_13_change_impact_compatibility.md` -- no code. Its classes and the "frontier is undetermined, never clean" rule are adopted here as the adapter contract's vocabulary.
7. P `tools/evidence_bundle.py` binds checks/reviews to sha256 artifact proofs + review ticket nonce; stale review detected by re-reading bytes; NO reusable certificate. Known hole (:140-141): A->B->A between ticket and read passes.
8. P `tools/mutation_probe.py` mutates the LIVE module for 8/10 ratchet pairs; `tools/mutation_drill.py` always works in an isolated temp copy with a control run. The farm builds on the drill's discipline, never the probe's live path.
9. P `modules/parallel_mesh` + `cognitive_os/scheduler` are advisory, fail-open, keyed on Claude pane sids; usable only as pure functions (`decide`, `CollisionDetector`) with synthetic ids.
10. P Constitutive Baseline Ratchet owner = `modules/tower/` (baselines, families, select, ratchet, donegate) + `tools/family_baseline.py`; effect path UserPromptSubmit -> gsd_x_tier.js -> `gsd_x/cli.family_block`. Families: kobiicraft_mode, persistent_state, web_surface, wii_homebrew. donegate is REPORT-ONLY by spec. GOAL WORKERS (`claude -p <brief>`, providers/claude.py:102-139) receive NO family baseline unless hooks fire in -p mode and the brief happens to match vocabulary -> a ratchet gap this mission closes.
11. P UCR-CIF, EDD/Semantic Reality Compiler and SSM/UCWSM/ContextImage have NO code owner on this branch (UCR-CIF "Verification Amortization" lives only in `vault/knowledge_base/ucr_cif/SOURCE_INVENTORY_FULL.json:30150-30169`). Not invented here: the frontier consumes obligations as they exist; brief.py is the ContextImage seam.
12. P UKDL canonical owner = `vault/knowledge_base/ukdl-universal.md` (ids `HR-`/`PR-`/`T-`). The prompt's `knowledge-vault/UKDL/universal-knowledge.md` does not exist.
13. O Baseline suites at fbca24fc: reconcile 22/22, judge 11/11, convergence 29/29, sweep 14/14, epoch 19/19, chaos 15/15, mutation_safety 8/8, **gate_provider 17/18 RED** (pre-existing, 3/3 runs).
14. P+O Root cause of 13: the gate supervisor's `subprocess.run(cmd)` (providers/gate.py:72) passes no std handles; on Windows the grandchild's output never reaches the log -> every gate verdict carries `observed: ''`. Scratch reproduction: 0 B; with explicit `stdout=sys.stdout, stderr=sys.stderr`: 11 B.
15. P Elixir pilot: Owner chose `C:\Users\User\Apps\io-chatgpt-plugin` (InfinityOps umbrella). Scout evidence places the historical "Phase 6" (W4b backlog file targets, MCP writer endpoints) in `C:\Users\User\Apps\io-ucg` (feat/universal-context-gateway, phases 01-09); no "image upload" was found there. Pilot runs on io-chatgpt-plugin; io-ucg is the historical-replay corpus. Neither tree is ever written: both are exercised only through fresh worktrees/copies.
16. O A live Ralph mission (m-9bee7894f20f) writes the main checkout -> this mission lives in its own worktree.
17. P Ecosystem denominator: sdd_os/scaffold.py (Python, Elixir/OTP, Rust, Go, Java Maven/Gradle, Kotlin, Node) + hook-runtime.js markers (composer.json, Gemfile). `auto-testing/detectors.py` knows only Java/Python/Node.

## Owner decisions (2026-10-07)

- D-O1 Arm `/cpp-gsd-long` in worktree `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`.
- D-O2 Baseline promotion target: NEW tower family `software_construction` (universal software triggers), entries checked by this mission's V-gates through the existing ratchet/select/report-only donegate; ExecutionOS tier untouched.
- D-O3 Elixir pilot: io-chatgpt-plugin (see Reality 15).
- D-O4 Adapter authority ceiling: PROBATION. TRUSTED needs an explicit Owner go with the shadow report attached; the mission records PENDING_OWNER and continues.
- Budget: 12 cycles / 24 h per marker; re-arming the SAME mission after an honest budget halt is pre-authorised.

## Semantics (resolved by W1 on 2026-10-07; audit record: .planning/workstreams/gsdx-pcc/phases/02-w1-convergence-semantics-ultra-plan-the-only-one/02-AUDIT.md)

### S1 Candidate identity
In Phase 2 `candidate_id` is exactly today's `tree_id` string (`git:<oid>` | `work:<hash>` | `unknown:...`, git_state.py:124-142). A certificate binding is `{"scheme": "tree" | "causal", "value": ...}`. The legacy whole-tree case is the `tree` value of the same field that Phase 4 fills with `causal`, so "unknown premise set -> whole-tree binding" is a value, not a branch, and no schema changes later. Candidate snapshots on git objects are Phase 4 (D23).

Resolved: a candidate is today's tree_id string and a binding is a scheme-tagged value, so the causal binding of Phase 4 reuses the same field.
Gates: V-PCC-STATE-LEGACY-MAP
Sources: 02-RESEARCH G1; DENOMINATOR D01

### S2 Proof states and precedence
Proof state is a projection on a NEW axis, computed per `(claim_id, candidate_id)` by a pure function in `modules/gsd_x/goal/proof.py`. It never assigns `o.disposition`, and `goal_closure` is untouched in Phase 2 (the STALE disposition name in `mission/obligation.py:40` is a different axis). Only FRESH and INHERITED could ever count toward closure, and in Phase 2 nothing consumes the projection.

States: FRESH | INHERITED | SUPERSEDED | STALE | UNKNOWN. Each of the six premises (claim, revision, gate_pin, fingerprint, environment, policy) is observed `equal | changed | unknown`.

- Precedence: any `changed` -> STALE; else any `unknown`, an `unknown:` candidate, an empty premise set, or `GSDX_PROOF_INHERITANCE` off -> UNKNOWN; else (all six equal) -> INHERITED only when a `proof.inherited` event names the certificate, otherwise UNKNOWN. STALE and UNKNOWN both route to FULL re-run and differ only in the recorded reason.
- FRESH = a `proof.produced` (or a legacy `obligation.satisfied`) whose binding equals the candidate and whose revision equals the goal revision.
- Legacy mapping with no PCC events: SATISFIED with `verdict.tree_hash == candidate`, `verdict.revision == revision` and `o.revision == revision` -> FRESH; SATISFIED with a different tree -> STALE; ACCEPTED never satisfied, or a STALE/CANDIDATE disposition -> no proof (not applicable, not UNKNOWN). This reproduces `reconcile._needs_a_gate_here` (reconcile.py:101-121) except for `unknown:` trees (S14, R12). The `o.revision == revision` clause is a no-op over logs written through the public writers (`satisfy` refuses a stale `ob.revision`, convergence.py:264); a raw log where `o.revision` differs maps to UNKNOWN, never FRESH.
- SUPERSEDED is derived, never evented: a certificate is SUPERSEDED iff a later FRESH certificate for the same `claim_id` at an equal-or-later binding has strength >= its own under `unit < integration < in_game < live`. An empty or unknown class is incomparable and never supersedes. Supersession never lowers strength.
- Adjacency: two certificates for one `claim_id` at an identical binding and equal strength -> the later supersedes the earlier, so exactly one is live. Two `unknown:` bindings never compare equal.
- Empty: no verdict -> no proof. A log with no PCC events -> legacy mapping only.
- Ordering: proof records in log seq order, obligations in `cv.obligations` insertion order. Two projections of one log are byte-identical in canonical JSON (`log._canonical` parameters).

Resolved: proof state is a pure per-(claim, candidate) projection with changed > unknown > all-equal-with-event precedence, derived SUPERSEDED, and a legacy mapping equal to `_needs_a_gate_here`.
Gates: V-PCC-STATE-TRUTH-TABLE, V-PCC-STATE-LEGACY-MAP, V-PCC-STATE-NO-EVENT-NOT-INHERITED, V-PCC-STATE-UNKNOWN-TREE, V-PCC-STATE-NOT-IN-DISPOSITION, V-PCC-STATE-SUPERSEDED-STRENGTH, V-PCC-STATE-ORDER-STABLE
Sources: 02-RESEARCH G3 G4 G5; DENOMINATOR D01

### S3 Certificate validity
A certificate is valid for a candidate only when all six premises are `equal`:

- claim: `claim_id = sha256(canonical({id, plane, text, done_gate, gate_pin, gate_class}))[:24]`. It is not the obligation id: a second `obligation.accepted` with the same id replaces the obligation (`project_convergence`, convergence.py:117), so a re-accept with another gate changes the claim.
- revision: `GoalState.revision`, never crossed (convergence.py:264-267; `carry_obligation` resets SATISFIED, :131-132).
- gate pin: exact `_pin` tuple equality (convergence.py:102-103) in its own `pin_scheme`; mixed schemes -> unknown.
- fingerprint: S4.
- environment: `env1:` + sha256 over canonical `{python: sys.version_info[:3], system, machine, tools: env_deps}`. ENVIRONMENT_SENSITIVE with an empty `env_deps` -> unknown.
- policy: module constant `POLICY_VERSION = 1`; any difference -> changed (bumping it invalidates every inherited certificate on purpose).
- time: judged against the injected `ctx.now`, never `time.time()`; a certificate dated more than 300 s in the future -> unknown.

Producer authority: `proof.produced` is appended only from the gate-receipt path with `source`; `proof.inherited` only by the reconciler/validator after re-deriving the premises from the worktree; a worker epoch writes neither. The event is a CLAIM: the state is computed from caller-supplied OBSERVED premises, never from the event's stored values. `actor` is self-asserted (log.py:180), so the chain proves integrity, not authorship; the defence is recompute-on-validate (Phase 5).

Resolved: validity is a pure function of six observed premises with claim_id (not the obligation id) as the claim, and the event is a claim that is never trusted for its own stored premises.
Gates: V-PCC-CERT-CLAIM-REACCEPT, V-PCC-CERT-GATE-PIN-SCHEME, V-PCC-CERT-REVISION, V-PCC-CERT-POLICY-BUMP, V-PCC-CERT-ENV-UNDECLARED, V-PCC-CERT-FUTURE-DATED
Sources: 02-RESEARCH G6 G16; DENOMINATOR D01

### S4 Causal fingerprint
`cf1:` + sha256 over canonical sorted `[[posix_relpath, blob_oid | "ABSENT"]]`, with `blob_oid` = `git_state.blob_oid` (eol-normalised, git_state.py:62-75) and paths POSIX-relative to the scope root.

- A missing premise file is the token `ABSENT`, never an exception (`file_pin` raises, git_state.py:117, so it is not reused).
- A directory expands to its files minus `epoch._debris` and `.git`.
- An absolute path, a `..` path, a symlink escaping the root, a path outside the root, an unreadable file, or an EMPTY premise set -> an `unknown:` fingerprint -> the whole-tree binding of S1.
- Phase 2-4 premises are gate pin files plus declared `causal_paths` only; an adapter at SHADOW contributes nothing.

Resolved: the fingerprint is a canonical hash of per-file blob ids with ABSENT as a value and every doubt collapsing to the whole-tree binding.
Gates: V-PCC-FINGERPRINT-ABSENT, V-PCC-FINGERPRINT-OUTSIDE-ROOT, V-PCC-FINGERPRINT-EMPTY, V-PCC-FINGERPRINT-EOL
Sources: 02-RESEARCH G7; DENOMINATOR D01

### S5 Freshness classes
Freshness is a SECOND axis computed by `freshness_class(obligation, verdict, contract)`. `GATE_CLASSES` (convergence.py:45) is NOT extended and is pinned by a gate: it is validated at acceptance and dispatch, so extending it changes accepted inputs.

Classes: DETERMINISTIC | COMPOSITIONAL | ENVIRONMENT_SENSITIVE | TEMPORAL | FRESH_REQUIRED, plus UNKNOWN. Legacy map from the verdict's class, falling back to the obligation's: unit -> DETERMINISTIC (binding stays whole-tree until a causal set exists); integration -> ENVIRONMENT_SENSITIVE; in_game, live and any REALITY-plane obligation -> FRESH_REQUIRED; empty class -> UNKNOWN. TEMPORAL and COMPOSITIONAL only by contract.

`risk_tags` is the closed vocabulary `security, authorization, tenant, destructive, migration, upload, reality, authority`; any tag forces FRESH_REQUIRED. A contract element without `risk_tags` -> UNKNOWN. A keyword scan of the obligation text may only ADD FRESH_REQUIRED, never remove it. FRESH_REQUIRED is never inherited.

Resolved: freshness is a separate pure axis with a pinned GATE_CLASSES and an asymmetric risk-tag rule that can only escalate.
Gates: V-PCC-FRESHNESS-MAP, V-PCC-GATE-CLASSES-PINNED, V-PCC-FRESHNESS-RISK-TAGS, V-PCC-FRESHNESS-SCAN-ESCALATES-ONLY
Sources: 02-RESEARCH G9 G10; DENOMINATOR D01

### S6 Typed proof contract
Additive event `obligation.contract` with `{"v": 1, "claim_id", "obligation", "elements": [{"oracle", "command", "gate_pin", "causal_paths", "env_deps", "freshness_class", "risk_tags", "nondeterministic", "inheritability"}], "combine": "AND"}`. Only `AND` in Phase 2; any other `combine` -> the contract is UNKNOWN -> FULL.

`legacy_contract(obligation)` is one element: `oracle` = gate_class, `command` = done_gate, `gate_pin` = gate_pin, `causal_paths` = [], `inheritability` = "never". A later contract may only be equal-or-stronger (more risk tags, stricter freshness, more causal paths); a weakening is ignored and reported, mirroring the weakening refusal of `contract.revise` (contract.py:141-151).

Resolved: a legacy done_gate is a one-element AND contract and a typed contract is attached by a new additive event that can only strengthen.
Gates: V-PCC-CONTRACT-LEGACY-ONE-ELEMENT, V-PCC-CONTRACT-WEAKENING-IGNORED, V-PCC-CONTRACT-COMBINE-UNKNOWN
Sources: 02-RESEARCH G8; DENOMINATOR D10

### S7 Event vocabulary
Landed as code in Phase 2, all owned by `modules/gsd_x/goal/proof.py`, all with `"v": 1`:

| name | required data fields | producer |
|---|---|---|
| obligation.contract | claim_id, obligation, elements, combine | accept path (typed contract) |
| proof.produced | claim_id, candidate, binding, revision, strength, source | gate receipt path |
| proof.inherited | claim_id, certificate, candidate, premises | reconciler/validator |
| proof.invalidated | claim_id, certificate, reason | reconciler/validator |
| candidate.promoted | candidate, tree, fingerprint | reconciler (landed in Phase 4, moved from the frozen table) |
| review.received | claim_id, candidate, ticket | review intake, `modules/gsd_x/goal/review.py` (landed in Phase 5, moved from the frozen table) |

Frozen (spec table only, no code in Phase 2; a bare constant with no projection is vapor under the Reality Contract):

<!-- pcc-frozen-events:begin -->
| name | owner phase | required fields | v |
|---|---|---|---|
| adapter.maturity | 7 | adapter, maturity, reason | 1 |
| continuation.sealed | 8 | goal, epoch, frontier | 1 |
<!-- pcc-frozen-events:end -->

Rules: the envelope stays the 7-field `Event` (no new top-level key; `Event.from_dict` reads exactly those keys, log.py:126-128). Every payload carries `"v"`. A malformed v1 payload of an own type raises `GoalLogCorrupt` only inside proof.py. A `v` greater than supported is recorded UNKNOWN and never raised (a raise would make `autonomous_goals` skip the goal, sweep.py:202-204). New type strings never reuse the 22 legacy ones. Any new event type must first be declared in one of the two tables above. Frontier, critical path and scheduling are projections, not events.

Resolved: four types land with real projections, four are frozen in a machine-read table, and a higher `v` degrades to UNKNOWN instead of raising.
Gates: V-PCC-ENVELOPE, V-PCC-CONTRACT-MALFORMED-RAISES, V-PCC-CONTRACT-HIGHER-V-UNKNOWN, V-PCC-ADDITIVE-ONLY, V-PCC-VOCAB-DECLARED
Sources: 02-RESEARCH G11 G12; DENOMINATOR D44

### S8 Frontier semantics
`compile_frontier(ctx) -> Frontier` is a pure projection over the GoalLog (Phase 3): expectation, execution (all justified actions with prerequisites, read/write sets, resource class, exclusivity), proof (what closure still needs), invalidation (what the last candidate staled), critical path (measured priors only; UNKNOWN duration allowed).

`decide` keeps its signature: `decide(ctx: Context) -> Decision`. `Decision` fields: `kind, reason, epoch_id, spec, provider, hypothesis, info_key, packet`. `Context` fields: `state, tree_hash, scope_hash, observations, judge, now, budget, providers, blocked_on, engine` (reconcile.py:49-74). Phase 3 keeps a verbatim legacy path for `GSDX_FRONTIER` off and must equal it on every field, including `reason`, whenever no PCC events exist. With the switch on, the only allowed difference is a WAIT replaced by the first independent justified action, in legacy order (insertion order of `cv.obligations`). Undeclared read/write/resource sets conflict with everything.

The one-open-epoch rule of `epoch.begin` (epoch.py:280-286) is pinned in Phase 2 and relaxed only by Phase 3 under Law 4: a goal runs one epoch at a time unless every open epoch and the new one declare provably independent write sets and non-colliding resource classes. Fences stay strictly increasing per goal and receipts are compared against their own epoch's fence (epoch.py:348-355). WAIT only when the execution frontier is empty while epochs are in flight.

Resolved: decide() keeps its exact signature and legacy equality, and the one-open-epoch rule is pinned so that Phase 3's relaxation is a visible red-to-green.
Gates: V-PCC-DECIDE-SIG, V-PCC-ONE-OPEN-EPOCH-PINNED, V-PCC-LAW-CONCURRENCY-DEF
Sources: 02-RESEARCH G13 G14 G15; DENOMINATOR D43

### S9 Judge
VALIDATE an inherited certificate independently (re-derive the fingerprint at the judged tree, re-verify pins, policy, freshness class) or REPLAY. Independent REPLAYs run concurrently under a resource bound. Builder-cannot-judge, pin re-verification, worktree==tree and PASS/REFUSED/UNJUDGEABLE all stay. Phase 2 changes nothing in `judge.py`; the VALIDATE path is Phase 5.

Resolved: the judge paragraph is kept verbatim and Phase 2 touches no judge code.
Gates: V-PCC-NO-LEGACY-EDIT
Sources: 02-RESEARCH section 2; DENOMINATOR D43

### S10 Kill switches
Env-only in Phase 2 (STATE decision 4). `GSDX_FRONTIER` and `GSDX_PROOF_INHERITANCE` are read at CALL time (never import time; tests flip `os.environ` in-process) by one shared parser `switch_on(name)`: strip, lower-case; ON iff unset/empty or one of `on, 1, true, yes`; any other value, including `off`, `0`, `false` and a typo such as `of`, is OFF, because OFF is the legacy, stronger path and Unknown Escalates (the opposite of `CPP_FAMILY_BASELINES`, whose typo leaves the feature on).

The switch decides at the consumer boundary: with `GSDX_PROOF_INHERITANCE` off the proof-state projection returns UNKNOWN for every certificate (whole-tree binding, FULL re-run). Events already in the log stay readable and replayable whatever the switch; off ignores `proof.inherited`, never deletes or rewrites it. In Phase 2 `GSDX_FRONTIER` has no consumer, so `on` and `off` are observably identical, which the replay suite proves. Flag files (the codex.py:52-53 pattern) are decided with Phase 3's first consumer, because the scheduled `PP-GoalSweep` cannot easily inherit an interactive env var.

Resolved: one call-time parser where anything but an explicit on-value is off, so a typo falls toward the legacy path.
Gates: V-PCC-SWITCH-PARSE, V-PCC-SWITCH-OFF-IS-LEGACY, V-PCC-SWITCH-FRONTIER-INERT
Sources: 02-RESEARCH section 5; STATE decision 4

### S11 Legacy-log replay
A byte copy of g-002-router-surface (50 events) and g-001-smoke-runner (123 events), `NNNNNN.json` files only, under `tools/fixtures/gsdx_legacy_goals/<repo-id>/<goal-id>/`, each with a `MANIFEST.json` (sha256 per file, chain tip digest, source store path, capture HEAD); `-text` in `.gitattributes` because the clone runs `core.autocrlf=true`. A golden `tools/fixtures/gsdx_legacy_replay_golden.json` is captured from the UNMODIFIED engine and committed before `proof.py` exists (capture refuses when the golden exists). The test copies the fixture into a temp `GSDX_GOALS_ROOT` and reads the copy, never the committed tree in place and never the live store. Every prefix is replayed (a prefix of a valid chain is a valid chain). A synthetic generator through the public writers covers the 9 legacy types the corpus lacks (`goal.revised`, `goal.budget_set`, `goal.authority_set`, `obligation.carried`, four `operator.*`, `evidence.hypothesis`). The union of corpus and synthetic types must equal the legacy type set DISCOVERED by scanning `modules/gsd_x/goal/*.py`, not hand-listed. Appending new-type events leaves every legacy output equal except `last_seq`, and the events survive an export/restore round trip.

Resolved: old logs replay unchanged, proven by a committed byte-copy corpus, a pre-change golden, a synthetic generator and a discovered-population floor.
Gates: V-PCC-REPLAY-G002, V-PCC-REPLAY-G001, V-PCC-REPLAY-SYNTHETIC, V-PCC-REPLAY-POPULATION, V-PCC-REPLAY-IGNORE-NEW-TYPES-FUTURE, V-PCC-REPLAY-IGNORE-NEW-TYPES-PCC, V-PCC-GOLDEN-PRE-CHANGE, V-PCC-FIXTURE-MANIFEST
Sources: 02-RESEARCH section 4; STATE decision 2

### S12 The five laws as executable invariants
- Semantic Conservation: a read-side re-check that every `goal.revised` which drops an acceptance or constraint item carries `weakened` + `weakening_reason` (writer rule at contract.py:141-151). Vacuous on the recorded logs, driven red on a synthetic log.
- Proof Conservation: a pure detector `duplicate_payment(ledger)` over the new proof events (a second `proof.produced` for the same claim and fingerprint with no `proof.invalidated` between). Vacuous on legacy logs. The behavioural half (not re-running a gate) is Phase 4 and the gate name says ledger.
- Work Conservation: no two epochs share an `info_key` where the first ended UNSUCCESSFUL (`epoch.begin` refuses it, epoch.py:273-279). Measured on the corpus as a NAMED SET of legacy exceptions, never an assumed pass.
- Concurrency by Proof: only the definition lands. `independent(a, b)` is true only when both declare disjoint write sets and non-colliding resource classes; any undeclared set is not independent. The scheduler is Phase 3.
- Unknown Escalates: certificate validity is a pure function of six premises each in {equal, changed, unknown}; all 3^6 = 729 combinations are enumerated, INHERITED iff all six equal and a `proof.inherited` event names it, and both switches off give FULL for every combination.

Each law has a synthetic violating input that turns its gate red. Baseline entries are Phase 10 (R09).

Resolved: every law is a pure checkable invariant with a driven red case, and the parts that need later behaviour say so in their gate names.
Gates: V-PCC-LAW-SEMANTIC, V-PCC-LAW-PROOF-CONSERVATION-LEDGER, V-PCC-LAW-WORK-CONSERVATION, V-PCC-LAW-CONCURRENCY-DEF, V-PCC-LAW-UNKNOWN-ESCALATES
Sources: 02-RESEARCH 3.1; DENOMINATOR D03

### S13 Event log, not a second DB
Proof state is written only through `GoalLog.append` (CAS). Projections are pure. No file, cache, sqlite, shelve or pickle store exists for proof state. Concurrency: a concurrent writer gets `LostRace` and the log is unchanged; an interrupted append leaves the whole event or none (`publish`). Idempotency: a projection run twice returns equal results and changes no file; a writer called twice appends two events, and the Proof Conservation ledger flags the duplicate.

Resolved: the GoalLog is the only store, written by CAS append and read by pure projections.
Gates: V-PCC-NO-SECOND-STORE, V-PCC-PROJECTION-PURE, V-PCC-WRITER-CAS, V-PCC-EXPORT-RESTORE-ROUNDTRIP
Sources: 02-RESEARCH section 1; DENOMINATOR D44

### S14 Known legacy defects and side effects
- G2: two `unknown:not-a-git-tree` trees compare equal in `goal_closure` (convergence.py:350) and `_needs_a_gate_here` (reconcile.py:115). It is DENOMINATOR R12, fixed red-first in Phase 4; fixing it in the zero-change seam would change a legacy output. The new projection already treats any `unknown:` tree as UNKNOWN.
- G17: landing any `.py` under `modules/gsd_x/goal/` changes `engine_identity` (engine_identity.py:34-39), which stales the recorded autonomy record and enters `info_key`. `record-gates` is re-run after merge and never against the live store from this worktree.
- A7: the live `PP-GoalSweep` task is assumed to run the main checkout; verify before merge.

Resolved: three known legacy effects are named, owned by a later phase or by the merge step, and none is fixed inside the seam.
Gates: V-PCC-STATE-UNKNOWN-TREE, V-PCC-NO-LEGACY-EDIT
Sources: 02-RESEARCH G2 G17; DENOMINATOR R12

### S15 Shadow law
If the incumbent full path detects a failure the optimized path would have declared covered, the optimization path failed: regression fixture, adapter -> DEGRADED, certificate invalidation, UKDL candidate. Selective omission is never authorised above the adapter's maturity (ceiling PROBATION, D-O4).

Resolved: the shadow law is kept verbatim.
Gates: V-PCC-LAW-UNKNOWN-ESCALATES
Sources: Owner decision D-O4

### S16 Suite list
Phase 2 adds `tools/test_gsd_x_goal_pcc_semantics.py` (summary `GSDX_PCC_SEMANTICS_PASS`) and `tools/test_gsd_x_goal_pcc_replay.py` (summary `GSDX_PCC_REPLAY_PASS`). The later suites keep the ROADMAP names (`test_gsd_x_goal_frontier`, `_certificate`, `_invalidation`, `_judge_validate`, `_mutant_farm`, `test_gsd_x_impact_adapters`, `test_gsd_x_goal_latency`, `_shadow`, `test_gsd_x_baseline_inheritance_pcc`). All match the done-gate glob `tools/test_gsd_x_goal_*.py` except the two named otherwise there. `test_gsd_x_goal_mutation.py` stays out of Phase 2 gates (R11).

Resolved: the suite names for the done-gate are final and the mutation suite stays out of Phase 2.
Gates: V-PCC-NO-LEGACY-EDIT
Sources: ROADMAP Final done-gate item 2; DENOMINATOR R11

## Done-gate (final)
`python tools/gsdx_pcc_done.py` exit 0 -- aggregates the named gates in ROADMAP "Final done-gate", requires every DENOMINATOR row dispositioned with evidence, and a clean worktree. Never weakened to finish.

## Rollback / kill switches
`GSDX_FRONTIER=off` -> decide() uses the legacy scalar path; `GSDX_PROOF_INHERITANCE=off` -> every proof re-runs (whole-tree binding); adapter state DISABLED by event. The parse rule is S10: only unset, empty, `on`, `1`, `true` or `yes` leaves a switch on, and any other value is off. All new events are additive; old goal logs replay unchanged, proven by V-PCC-REPLAY-* (S11).
</content>
</invoke>
