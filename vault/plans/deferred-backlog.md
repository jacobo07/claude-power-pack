# PP Deferred Backlog — activation criteria

> Items that could NOT honestly close in the 2026-06-08 session-close
> sprint, each with an explicit activation criterion so a future session
> picks them up without re-discovery. Source audit:
> `vault/audits/session_close_2026-06-08.md`.

---

## D1 — apex-completion-standard.md bidirectional drift (verify_spp: `mirror-parity` + `drift-report`)

**State:** global `~/.claude/knowledge_vault/core/apex-completion-standard.md`
(174 350 B, LF-SHA `e553bcc`) ≠ repo copy (158 278 B, LF-SHA `03d9775`).
Both STRICT-FAIL rows share this single root cause.

**Why deferred (not a mechanical loose→PP sync):** the divergence is
**bidirectional and cross-project**, so a blind copy in either direction
destroys content (HR-006: "sync direction propagates corruption
byte-perfectly"):
- **global-only (+195 substantive lines):** *other projects'* axes —
  KobiiCraft "NL→DNA Axis" (Sesión 15), KobiMapEngine Sesiones 16-20,
  "Database Migration Doctrine". The global vault is a **shared
  multi-project accumulator**.
- **repo-only (+178 substantive lines):** PP-only clauses — C20
  MCP-Resilience, C21 Slash-Recovery, PP Dataset Baseline (v15),
  Security-First (v16), and now C26/C27 (this session).

**Activation criterion:** Owner decides the canonical model. Two options:
1. **Union-merge** — append the PP-only axes into global AND the
   cross-project axes into repo until LF-SHAs match. Tedious, must
   de-dup, must preserve both projects' content.
2. **De-scope the file from mirror-parity** — if the apex doc is
   *intentionally* a shared cross-project accumulator that cannot be
   kept in byte-parity, remove it from `verify_global_mirrors.py`'s
   PAIRS list and track PP clauses in a PP-exclusive ledger instead.

Recommended: option 2 (the file's content proves it serves multiple
projects; byte-parity is the wrong invariant for it). ~30-45 min once
the model is chosen.

---

## D2 — hooks-registration 6/7 (verify_spp: `hooks-registration`)

**State:** `verify_hooks_registration.py` reports `HOOKS_REG_PROBE=6/7`.
Sub-check `idempotency-mod` fails: 6 hook markers are built on disk but
absent from `~/.claude/settings.json`:
`restart_resume`, `output_contract_stop`, `budget_monitor`, `jit_warm`,
`cascade_check_bash`, `secret_firewall_gate`.

**Why deferred:** writing `~/.claude/settings.json` is **Owner-side** —
the classifier hard-denies agent edits to it (HR-001,
`feedback_automode_denies_self_modification`). The PP-internal half
(hook scripts) is shipped; only the registration step remains.

**Activation criterion (Owner runs):**
```
python tools/verify_hooks_registration.py        # re-run WITHOUT --dry-run to commit
```
The probe already prints "Re-run without --dry-run to commit." Once the
Owner applies it (or runs the documented `settings_merger.py register-*`
commands), the marker set reaches 11/11 and the row passes.

---

## D3 — paths+secrets residual: doc-class (35) + secret-class (9) (verify_spp: `paths+secrets`)

**State after this session's CODE-class fix:**
- `path-leak (code)`: **0** ✅ (3 benchmark JSONs allowlisted —
  machine-generated host-pinned records).
- `path-leak (doc)`: 35 in 26 files — narrative/command/setup docs that
  reference `C:\Users\User\...` (e.g. `commands/*.md`, `docs/HOOKS_SETUP.md`,
  `vault/knowledge_base/ukdl-universal.md`, dataset + audit `.md`).
- `secret hits`: 9 in 3 files — canonical **fake** AWS doc example
  access-key IDs in `tools/secret_rotation_advisor.py`, VPS-IP narrative
  in `vault/audits/manual_tools_audit_*.md`, ssh-alias narrative in
  `vault/knowledge_base/pp_dataset/pp_dataset_01_identity.md`.

`normalize_paths.py` exits 1 while `--check` sees any unallowed doc OR
secret hit, so the row stays RED until both classes reach 0.

**Why deferred:** all 35+9 are non-leaks (narrative / canonical fixtures),
but clearing them correctly means **surgical per-file allowlist entries**
(26 doc + 3 secret), not a broad glob — the allowlist is intentionally
file-specific so it never masks a *future* real leak. Doing 29 reviewed
entries exceeds the 30-min defer threshold. NOTE: the secret-class
allowlist edit also trips the HR-SECRET PreToolUse firewall when the
comment names the example-key literal — author comments without the
literal token.

**Activation criterion:** add 29 surgical allowlist entries to
`tools/normalize_paths.py::ALLOWLIST` ({"doc-path"} for the 26 narrative
docs, {"secret"} for the 3 fixture/narrative files), each with a one-line
justification matching the existing host-pinned/fixture precedent. Then
`python tools/normalize_paths.py --check` exits 0. ~30-45 min.

---

# Added 2026-09-30 (session 5fb53f17) — Owner: "leave everything remaining in the backlog"

## D4 — PP Self-Eval: observe the first night (acceptance §4.4)

**State:** scheduled task `PP-SelfEval` installed (daily 03:30), code at `e079c57`, gate
`tools/test_pp_eval.py` 38/38. No night has run yet.

**Why deferred:** it can only be observed after 03:30.

**Activation criterion:** after 2026-10-01 03:30, read `~/.claude/state/pp-eval/nights.jsonl`.
Pass = one row with a harvest block or a named skip reason (RAM < 6 GB, owner active). No row
at all = the task did not fire: check `schtasks /Query /TN PP-SelfEval /V` LastTaskResult.
Resumption: `vault/specs/pp-self-eval.RESUMPTION.md`.

**2026-10-01 — PASS on the criterion, and a defect it exposed, FIXED.** The task fired:
row `started 2026-10-01T01:30:01Z`, `SKIPPED: a session transcript changed in the last 15 min
(2639597a-....jsonl)`. That transcript is the worker of mission `m-20f1013db18c` (RUNNING), and
7 missions were RUNNING, so "owner active" would have skipped every night a mission was in
flight and D6 could never start. Fix in `nightly.owner_active`: a transcript whose session owns a
live mission (`gsd_mission.mission_for_session`) is not the Owner; an unavailable mission store
fails closed. Gates V-EVAL-MISSION-WORKER-NOT-OWNER, -ENDED-MISSION-IS-OWNER (control),
-MISSION-LOOKUP-FAILS-CLOSED; suite 41/41; isolated drill 2/2 KILLED, control 41/41. Note for
future drills: the harness must also copy `tools/gsd_mission.py` + `tools/gsd_long_run.py`, or
the control goes red. Next observable: tomorrow's row should not skip on a mission worker.

## D5 — PP Self-Eval: 5 mutation drills never ran

**State:** S1 4/4 and S2–S4 7/12 killed, 0 survived. Not run: quota mid-night stop, quota
ceiling, lock, owner-active skip, proposal gating (`drills_s2s4.json` entries 9–13; harness
`eval_drill.py` with a clean-copy control). Both lived in session scratchpad 5fb53f17; if it is
gone, rebuild from the drill list in commit `0ba8565`'s message and this entry.

**Why deferred:** Claude Code reaped the drill for host memory pressure (1.9 GB free of 31 GB)
and asked that it not be restarted unprompted.

**Activation criterion:** free RAM >= 6 GB. Run the 5 drills on isolated copies; each must
print KILLED and the live files must hash unchanged. ~20 min.

**2026-10-01 — 4 of 5 RUN on GEX44, all KILLED.** The handoff of 5fb53f17 listed 4 unrun
(`d5_b.json` + `d5_c.json`); `d5_a.json` (quota ceiling) is not re-verified here and its
earlier result is not on record in this entry. Method: `git archive` of HEAD `8a7cfaa`
(subject paths last changed `caeec1a`) for `modules/pp_eval`, `modules/owner_queue`,
`tools/test_pp_eval.py` and its fixture, copied to `kobii@gex44:~/drills/d5-<ts>/`; the
harness was `eval_drill.py` with its hardcoded `PP = ~/.claude/...` replaced by an argument,
because on GEX44 that path is the host's own live install, not the laptop's HEAD. Result:
CONTROL clean copy `PP_EVAL_PASS=38/38`; KILLED V-EVAL-QUOTA-STOPS-NIGHT,
V-EVAL-LOCK-REFUSES-SECOND, V-EVAL-OWNER-ACTIVE-SKIPS,
V-EVAL-PROPOSAL-QUEUED-ONLY-WHEN-ACTIONABLE; exported tree hash unchanged. Laptop files never
touched. Remaining: re-run V-EVAL-QUOTA-CEILING-SKIPS (`d5_a.json`) if its first result
cannot be found.

## D6 — PP Self-Eval: bank has 0 validated tasks (need >= 8)

**State:** first real harvest reaped after 2 legitimate rejections (an environment-dependent
mirror test; a 200-check suite red at its own fix). Nights harvest 5 per night on their own.

**Why deferred:** memory pressure; the nightly run will continue it without a session.

**Activation criterion:** `python tools/pp_eval.py status` shows `bank_tasks`. If still < 8 after
3 nights, PP's history is too environment-bound (many tests read the live install): add repos
whose tests read their own tree to `~/.claude/state/pp-eval/config.json` `"repos"`.

**2026-10-01:** `bank_tasks: 0, rejected: 2`. Night count toward the 3-night rule: 0 that ran
(the only night skipped on a mission worker, fixed in D4). Not harvested on GEX44 instead: the
bank validates tasks in the environment that ran them, and the nights run on Windows.

## D7 — Capability gaps 2–6 (audit `vault/audits/se-capability-gaps-2026-09-30.md`)

**State:** gap 1 (self-eval) built. Open, in the audit's order: (2) post-edit diagnostics —
`quality-gate.js` only reminds, nothing runs ruff/tsc on an edited file; (3) testing aimed at
user code — hypothesis and coverage installed, unused; mutation machinery points at PP only;
(4) SAST + dependency CVE scanning — semgrep, osv-scanner/pip-audit not installed; (5) symbol-
level code intelligence — no language server installed; (6) CI for PP's own 600+ gates.
Cheap alongside: wire `refcheck` and `done_gate` (built, no caller).

**Why deferred:** Owner chose gap 1 first; each is its own T2 spec.

**Activation criterion:** Owner picks the next gap. Gap 2 is the cheapest (ruff is installed).
Once D4–D6 give verdicts, re-rank using the self-eval's own data.

**2026-10-01: gap 2 DONE** — `hooks/post_edit_diagnostics.js`, spec
`vault/specs/post-edit-diagnostics.md` (LIVE rows + evidence), 88e8c91 / cfa3275, registered
and proven live. Open: gaps 3–6 (each its own T2 spec) and the cheap `refcheck` / `done_gate`
wiring; still waiting for the Owner to pick.

**2026-10-01: gap 3 v1 BUILT** (Owner: "3") — `tools/test_gaps.py` + `/test-gaps`, spec
`vault/specs/test-gaps.md`, dc7f781. Uncovered changed lines + surviving mutants on covered
changed lines, in an isolated copy; subprocess-driven tests measured. 14/14 gates; GEX44 drill
6/6 KILLED. Not in v1: hypothesis, fuzzing, flaky tests, non-Python. `/test-gaps` copied live
2026-10-01 (Owner "y"). Real project verified on GEX44 (75b0fd7).

**2026-10-01: gap 4 v1 BUILT** (Owner: "gap 4") — `tools/security_scan.py` + `/security-scan`
(live), spec `vault/specs/security-scan.md`. semgrep 1.178.0 (own venv `Apps\semgrep-venv`)
on changed lines + osv-scanner v2.6.0 (official release, SHA-256 verified, `Apps\osv-scanner`)
over lockfiles, `introduced` vs `existing`. UNCHECKED never reads as CLEAN. 12/12 gates (452 s,
needs network). Not in v1: done-gate wiring (blocking Stop hook + network scan = the starvation
shape), SBOM, licences. Open: gaps 5–6.

## D8 — Mission continuity: merge the UKDL candidates

**State:** `vault/knowledge_base/mission_continuity/UKDL_CANDIDATES_DURABLE_SUBSTRATE.md` not yet
merged into `ukdl-universal.md`. On 2026-09-30 another pane held 884 uncommitted lines there.

**Why deferred:** committing that file would sweep the other pane's hunks into this commit.

**Activation criterion:** `git status -- vault/knowledge_base/ukdl-universal.md` is clean. Then
merge by pathspec and check the hunk headers before committing.

**2026-10-01 check:** still blocked. `ukdl-universal.md` now carries 1248 uncommitted lines
(was 884) and was written 10:45, seven minutes before the check: a live writer.

## D9 — Delete the `gsd-long-smoke` worktree and branch `gsd-autonomous-run`

**State:** leftover from the M6 canary; obligation 3 of the 2026-09-30 rollover capsule.

**Why deferred:** destructive; needs an explicit Owner yes (a bare "y" to a two-option question
was not taken as one).

**Activation criterion:** Owner says delete. Then read both first (worktree status, unpushed
commits on the branch) and delete only if nothing unique would be lost.

**2026-10-01 — Owner said delete; NOT deleted, unique work found.** Repo
`Desktop\Cursor Projects\gsd-long-smoke` (no remote), worktree
`.claude\worktrees\gsd-autonomous-run`, branch head `806f202`. The branch carries **78 commits on
no other ref** (`rev-list --count master..gsd-autonomous-run`; a first query with `--exclude`
returned 0 and was wrong), and the worktree holds uncommitted work: 4 modified files (+76/-17)
and untracked `smoketext/reverse.py`, `tests/test_reverse.py`, phase `09-word-count`, last
written 2026-09-29. Needs a second answer: archive first (git bundle of the branch + a copy of
the dirty worktree under `~/.claude/backups/`) then delete, or keep.

**DONE 2026-10-01 16:2x** (Owner: "delete"). State re-verified first (head 806f202, 78 unique,
same diff, no write since 09-29, no process). Archived to
`~/.claude/backups/d9-gsd-long-smoke-20261001-162241/`: `gsd-autonomous-run.bundle` (verify OK,
head 806f202) + `worktree/` (190/190 files, uncommitted files hash-identical). Then
`git worktree remove --force` and `git update-ref -d refs/heads/gsd-autonomous-run 806f202`
(deletes only at the expected head). Restore drill: cloning the bundle gives head 806f202, 91
commits, 78 not on master. Restore with `git fetch <bundle> gsd-autonomous-run:gsd-autonomous-run`.

## D10 — `test_hook_mirror_identity` red 3/5 (other panes' files)

**State:** new live/repo drift in `hook-dispatcher.js`, `zero-issue-gate.js`; stale
KNOWN_DIVERGENCES entries `closer-guard.js`, `learning-sentinel.js`,
`windows-bash-bridge-guard.js`. `research-intent-detector.js` was reconciled in `55fe169`.

**Why deferred:** those files belong to live work in other panes.

**Activation criterion:** when those panes commit, decide per file which side wins (the gate's
own instruction), sync, and drop the stale entries so the ratchet turns.

**2026-10-01 — now 4/5.** Stale entries dropped (the three files are identical on both sides).
Decisions on the two drifts, neither applied:
- `zero-issue-gate.js`: **repo wins.** Committed (6f897bf 09-28, 745cc3b 09-27) and a behavioural
  superset of live (live is the 09-16 build; its 42 "unique" lines are the pre-refactor shapes,
  and MIX_ENV, jwExemptionGranted and the BLOCKED_DELIVERY notice all survive in repo; only the
  footer wording changed). Never deployed, so the "never starve the host" fix is not live.
  Deploy = back up `~/.claude/hooks/zero-issue-gate.js`, copy the repo file over it, `node
  --check`. Refused twice by the auto-mode classifier (self-modification). **DEPLOYED
  2026-10-01 15:33** after the Owner left auto mode ("try the hook thing again"): live == repo
  (SHA-256), `node --check` OK, old 09-16 build at `~/.claude/backups/hooks-20261001-153359/`.
  Mirror gate still 4/5, now only on `hook-dispatcher.js`.
- `hook-dispatcher.js`: **repo is ahead, not applied.** Its only difference is uncommitted work of
  another pane (names the abandoned scripts in `CHAIN-DEADLINE-ABANDONED before pool`; `node
  --check` OK, `restSteps` in scope). Idle since 09-30 20:27. Deploy after that pane commits it.

---

# Added 2026-10-10 — GSD X Reconstruction Fabric deferred program

## D11 — REA as Reconstruction Evidence Fabric / Static Oracle substrate

**State:** architectural program defined in session; not yet implemented or benchmarked against the live Reconstruction Factory. REA is treated as a donor/provider layer, not as a new reconstruction owner.

**Why deferred:** this is a multi-phase substrate change touching evidence identity, oracle abstraction, proof, Wii/PPC admission and cross-title analysis. It should not interrupt active reconstruction work until a bounded canary proves concrete ROI.

**Activation criterion:** run a read-only WSR DOL canary against current REA + available Ghidra/Hopper path. Continue only if binary/load truth and evidence quality are good enough to preserve or improve current DTK/compiler/objdiff authority.

**Deferred scope (complete):**
- Keep ownership boundaries explicit: GSD X/KEOS govern; Reconstruction Fabric/Mission Compiler decides; `decomp` remains capability engine; REA sits behind a Static Oracle/Evidence adapter rather than becoming a fourth pipeline.
- Build a canonical Reconstruction IR spanning functions, basic blocks, calls, globals, strings, relocations, types, vtables, TU/object identity, compiler facts, semantic hypotheses, runtime observations and proof. Preserve provider/version, binary hash, analysis profile, evidence identity, provenance, truth status and invalidation dependencies.
- Add explicit Multi-Oracle Consensus without silent fallback. Ghidra/Hopper/DTK/compiler/runtime disagreement creates a contradiction object; agreement is weighted by lineage so derived evidence is not double-counted as independent.
- Add dependency fingerprints to evidence and incremental invalidation. Reuse remains valid only while binary/toolchain/provider/type/runtime assumptions remain valid; invalidate only the affected closure.
- Introduce typed reconstruction unknowns such as TYPE, COMPILER_BEHAVIOR, SEMANTIC_ROLE, RUNTIME_EFFECT, HOMOLOGY, SOURCE_SHAPE, OWNERSHIP, INTERFACE and PROOF_AUTHORITY, with repo-derived extension rather than a permanently closed enum.
- Wii/PPC admission gate: verify DOL/REL, Broadway PPC big-endian, section/load/BSS truth, entrypoint, relocations/import/module relations, functions, assembly, xrefs, callers/callees, pseudocode and reproducibility before trusting the substrate.
- If the canary passes, create a Wii/Broadway PPC evidence-backed profile/overlay for DOL/REL, ABI/compiler/runtime facts. Do not encode folklore as fact; only evidence-backed RVL SDK/RFL/NW4R/EGG/CodeWarrior knowledge enters.
- Build Cross-Binary Entity Alignment / Cross-Title Homology over Reconstruction IR for WSR ↔ Wii Sports and later titles/builds. Classify EXACT, RELOCATED, NEAR, STRUCTURAL, FAMILY and NOVEL across functions plus types/vtables/globals/TUs/strings/call neighborhoods.
- Add Differential Evidence / Differential Dossiers so homologous entities materialize only the delta, retained/common facts and compatible source transformations rather than two full dossiers.
- Adopt retained Evidence as the durable object and reconstruction-specific projections as the model-facing unit: triage, type, compiler, homology, runtime and proof projections. Full-read admission gate prefers facet/range/symbol/projection/query before whole evidence materialization.
- Evolve REA-style Reconstruction Obligation Ledger into a live Proof Graph/runtime state: claims, owners, dependencies, proof requirements, evidence, unknowns, contradictions, dispositions and completion level. New evidence may close, weaken, invalidate or unlock obligations.
- Keep fail-closed truth levels separate: IDENTIFIED, STRUCTURALLY_SUPPORTED, SEMANTICALLY_SUPPORTED, BUILD_PROVEN, BINARY_MATCHED, RUNTIME_PROVEN, HARDWARE_PROVEN, EXPERIENCE_PROVEN or evidence-equivalent repo-derived states. UNKNOWN/PARTIAL/CONTRADICTION never imply PASS.
- Make compiler, mwcceppc and objdiff first-class Evidence producers. Exact match is strong build proof; mismatch is also structured evidence with fingerprint, location, distance, candidate context and prior repair history.
- Make Negative Evidence first-class and persist reconstruction search trees: non-compiling candidates, mismatch classes, falsified hypotheses, non-applicable families, discarded branches, distances, diagnoses and remaining frontier. Hard rule: do not retry an equivalent disproven branch under the same dependency state.
- Every solved/matched entity checks for siblings/family opportunity. Family candidate path: detector -> template/candidate generation -> historical replay -> holdout/adversarial benchmark -> certification -> corpus scan -> exceptions only to reasoning.
- Add Reconstruction Obligation Economics: expected cognition/context/compile/runtime/hardware cost, probability of success, unlock count, product relevance, reuse/institutional value and proof criticality. KEOS buys information by Expected Total Verified Cost + Information Gain + downstream unlock rather than task order.
- Close static↔runtime loop with Active Runtime Questions and an Experiment Compiler. Static ambiguity should generate the cheapest discriminating experiment; GEX44/Dolphin returns structured evidence into the same graph.
- Add Dolphin Runtime Evidence Adapter and retain Real Wii as higher authority where required. Never infer Wii PASS from Dolphin PASS.
- Make Behavioral Evidence first-class beside assembly: input traces, state transitions, racket/ball response, timing and observable effects. Build toward causal evidence rather than correlations only.
- Add Semantic ABI Mining / Interface Archaeology: discover and prove boundaries by inputs, outputs, state, ownership, timing, side effects, failure semantics and calling/memory contracts. Proven boundaries may allow internals to remain opaque.
- Add provider-agnostic Context ABI and zero-transcript reconstruction. The institution remains stateful while processors remain replaceable/stateless; Context Compiler emits only mission/state/unknown/evidence/capability/proof/output-contract projections.
- Prefer upstream REA vanilla/pinned initially. CONNECT -> MEASURE -> WRAP -> EXTEND. Fork/overlay only for a demonstrated Wii gap whose lifetime ROI beats upstream maintenance cost.

**Done gate for activation:** same target, same proof and authority as current champion; evidence/context/tool-call/rediscovery cost must improve or a unique capability must be demonstrated. No REA integration is promoted merely because the API exists.

---

## D12 — ADCR-Reconstruction → Procedural Intelligence / Self-Compiling Reconstruction Institution

**State:** conceptual design captured; no claim that these layers are connected or production-proven today.

**Why deferred:** this is a second-order learning system. Building it before the evidence/procedure telemetry and benchmark corpus exist would create meta-architecture without measurable payback.

**Activation criterion:** enough reconstruction traces exist to show at least one repeated Work Class where procedure reuse, model-boundary extinction or routing changes can be evaluated champion/challenger against the same proof target.

**Deferred scope (complete):**
- Split durable intelligence into Knowledge Memory (what is known) and Procedural Memory (how to resolve each class of uncertainty cheaply and reliably).
- Add Reconstruction Work Recognition before reasoning. Candidate classes include FUNCTION_MATCH, FUNCTION_FAMILY_DISCOVERY, TYPE_RECOVERY, VTABLE_RECOVERY, HOMOLOGY_RESOLUTION, COMPILER_MISMATCH, SEMANTIC_ROLE_DISCOVERY, RUNTIME_DISCRIMINATION, SOURCE_OWNERSHIP_SEARCH, SEMANTIC_SEAM_DISCOVERY, INTERVENTION_PROOF, HARDWARE_VALIDATION and KNOWLEDGE_CONTRADICTION; final taxonomy must emerge from corpus evidence.
- Build Delegation/Procedure Compiler from Work Phenotype + Evidence + available capabilities + current resource state + proof target. Known work should compile to the minimal procedure, not trigger generic planning.
- Treat ADCR as the how-layer: GSD X retains persistent objective/meta-control; KEOS allocates resources; decomp executes reconstruction capabilities; REA/other oracles observe; Proof Graph establishes why success is believed; CBR propagates maturity.
- Create Reconstruction Procedure Genome recording phenotype, preconditions, evidence signature, applicable capabilities, execution trace, actual reasoning boundaries, proof path, economic profile, failure envelope, transfer scope and outcome.
- Add Procedural Homology so differently named Work Classes can share the same abstract strategy when their causal structure is equivalent.
- Create structured Procedure IR; Markdown is a human view, not authority. Procedures must carry identity/version/owner, applicability, preconditions, execution strategy, verification contract, failure semantics, provenance/confidence, dependencies and supersession.
- Learn conditional policies rather than one global procedure. Example TYPE_RECOVERY may route to global type solver, local solve, cross-title alignment or runtime discrimination depending on fan-out/evidence/oracle cost.
- Add Procedure E-Graph for semantically equivalent paths and Procedure Economics for expected success, tokens/context, compile/runtime/proof cost, repair probability, latency, human attention and future reuse.
- Treat procedures as capital assets with acquisition cost, evidence, usage, success rate, avoided spend, maintenance, scope, confidence, depreciation and supersession. Detect Procedural Debt when repeated manual/LLM workflows should already be mechanized.
- Procedure Mining: cluster repeated tool sequences, evidence patterns, decisions, failures, repairs and proof paths. Compile raw traces into candidate Procedure IR by causal contribution analysis, dead-step removal, deterministic sequence merge, guard/deopt extraction and proof contract.
- Apply compiler-style optimization to procedures: dead procedure code elimination, partial evaluation, JIT, inlining, fusion/fission by semantic locality, batching, singleflight, caching and speculation only when measured to reduce total verified cost.
- Automatic model-boundary compilation: DETERMINISTIC / MODEL_OPTIONAL / MODEL_REQUIRED / HUMAN_AUTHORITY. Mature classes should move MODEL_REQUIRED -> optional -> deterministic.
- Learn Procedure Context Profiles and procedure-specific epoch lifetimes for UCVM/SSM. Working set, not mission age, should determine residency and semantic epoch rotation.
- Give each procedure a proof recipe. Mutate/fuzz procedures with missing/stale/contradictory evidence, unavailable providers, wrong homologues and bad candidates. Correct response is deopt/abstain/escalate, never invented PASS.
- Procedure maturity: OBSERVED -> REPEATABLE -> BENCHMARKED -> TRANSFER_PROVEN -> CERTIFIED -> CONSTITUTIVE, with DEPRECATE/RETIRE as real lifecycle states.
- Store Negative Procedures and invalidation conditions. Known-bad routing patterns must be reusable knowledge, not forgotten anecdotes.
- Build Procedural Causal Graph and Causal Credit Assignment so success credits only the evidence/procedure/capability steps that materially changed outcome, preventing accidental bureaucracy from being promoted.
- Add counterfactual procedure replay, Procedural Regret and learned Procedure Selection Policy. Routing can eventually become rules/statistics/small classifiers/decision tables rather than a giant LLM call.
- Formalize seven learning levels: Task, Procedure, Capability, Meta-Learning, Policy Learning, Capability Portfolio Learning and Architecture Learning. Evidence burden increases with blast radius; architecture changes require cross-campaign proof + rollback.
- Evolutionary Reconstruction: champion/challenger procedures/capabilities/policies via historical replay, live shadow, canary, mutation, holdouts and transfer. Fitness is Pareto-constrained by correctness, proof, false seals, latency, tokens, compute, human attention, reuse and maintainability.
- Preserve niches and Negative Transfer Memory. A PPC/CodeWarrior procedure does not become universal because it won locally.
- Add Procedural Compositionality/Algebra and Procedure Synthesis from proven operations such as SEQUENCE, PARALLEL, RACE, RETRY, FALLBACK, DEOPT, GUARD, CACHE, SINGLEFLIGHT, BATCH, SPECULATE, PROVE and ABSTAIN; synthesized workflows require shadow/replay before use.
- Production pain generates Autonomous Curriculum. GSD X should identify dominant reasoning tax, build the smallest challenger, replay/canary, measure, promote/reject, redrain and measure work disappeared.
- Self-Improvement ROI Gate: expected lifetime saving must exceed CAPEX + maintenance + risk. RECURSIVE mode is triggered by measured repeated reasoning/failure/model-boundary/human-correction/context tax or flat learning curve, not by enthusiasm.
- Prevent recursion runaway: no optimizer-of-optimizer chain without demonstrated downstream lift.
- Constitutive Procedure Baseline becomes part of Reconstruction Birth. Campaigns inherit materialized defaults such as homology-before-novel, proof-of-non-work-before-work, type-dominator-before-leaf, compiler oracle before semantic escalation, runtime discrimination when static ambiguity remains, cheap solvers before frontier, consult negative evidence and prove only affected closure.
- Measure Procedural Birth Advantage and Procedural Cold-Start Cost. New campaigns should increasingly begin with execution already compiled.
- Support procedural rejuvenation mid-campaign with versioned/MVCC policy rollout; workers/results remain attributable to the procedure/capability/context versions that produced them.
- Every Work Unit emits procedural telemetry: chosen route/procedure, alternatives rejected, expected vs actual cost, model boundaries, page faults, proof, deopt and human intervention.
- Add selection telemetry/A-B across corpus. Promotion needs measured lift, not prose claims.
- Redefine delegation: executors can be deterministic solver, cache, compiler, local model, frontier model, Dolphin, Wii or human. Multi-agent count is not an autonomy KPI.
- Parentless procedural execution: typed receipts + state machine advance known work; only semantic faults wake general cognition.
- Semantic interrupts become training examples. Measure Interrupt Extinction Rate and classify repeated interrupts as automation candidates.
- Work Class Closure: once variants/failures/proof/context/procedure/deopt/benchmark are covered, default frontier use is forbidden unless contradiction reopens the class.
- Expand Zero-Frontier Zones and eventually Zero-Procedure Zones where a fully dominated operation becomes a primitive/invariant.
- Automatic abstraction-level selection/root-cause elevation: decide whether a repeated problem belongs at function, family, type, compiler, runtime, procedure, capability or architecture level; stop whack-a-mole.
- Maintain Knowledge + Procedure twin: What Model + How Model evolve independently but cross-inform each other.
- Build a Factory Twin / Counterfactual Factory for replay/simulation of policies, resources, queueing, cost, proof and failure before changing production routing.
- Conceptual markets for Procedure/Capability/Knowledge/Proof selection all share one KEOS/Cognitive Economics objective: Minimum Total Verified Cost under hard proof/correctness constraints.
- UCR-CIF Construction Return must capture facts, capabilities, procedures, procedure failures, routing improvements, context profiles, proof recipes and architecture lessons, not just summaries.
- Hard institutional rule: no procedural experience counts as capital until it changes future execution measurably.
- Extreme transfer tests: fresh agent, fresh institution, provider swap, new title, later new architecture and cross-domain applicability. Known-work performance should not collapse because a particular model process disappeared.
- North Stars: Reconstruction Procedural Deflation; Procedural Novelty Concentration; Interrupt Extinction Rate; Work Class Closure; Knowledge Escape Velocity + Procedural Escape Velocity.
- Constitutional pressure laws: repeated reasoning -> procedure; repeated procedure -> capability; repeated capability composition -> architecture compilation; every improvement must prove future execution lift; ultimate delegation means known work stops requiring general intelligence.

**Done gate for activation:** at least one comparable Work Class demonstrates lower verified cost in generation N+1 with equal-or-better proof and no increase in false seals. No increase in playbook/skill count counts as success by itself.

---

## D13 — Universal Modder X as Intervention + Experimental Reality Plane

**State:** Universal Modder audited as a useful donor corpus/runtime concept. Current repo remains external; no decision to install it globally or place `um` in the active WSR critical path.

**Why deferred:** its highest-value contribution is not another reverse-engineering layer but actuation, route selection, experimental reality, safe mutation and real-world verification. This should be built only after ownership boundaries with REA/Proof/KEOS are explicit.

**Activation criterion:** choose one KSR/WSR target where a reversible intervention/experiment can close a real uncertainty or prove a vertical slice faster than static reconstruction alone. Run it as a bounded adapter/canary, not as a global plugin install.

**Deferred scope (complete):**
- Treat Universal Modder X as Intervention & Experimental Reality Plane, complementing REA. REA observes; Intervention Runtime mutates/experiments; Reconstruction Fabric decides; ADCR learns; KEOS allocates; CBR ratchets.
- Build Universal Intervention Runtime: given Desired Behavioral Delta, safely realize the cheapest proven intervention against an executable system through configuration/data/retail interface reuse/adapter/relink/patch/rebuilt subsystem/semantic transplant/runtime replacement/minimal source ownership/residual reconstruction/full source as justified.
- Add Route Compiler + Route Drift Detector. Compare routes using Expected Total Verified Cost, blast radius, source ownership, proof availability, reversibility, latency, reuse and risk. Recompile route when new evidence changes dominance; never continue because of sunk cost.
- Convert Safe Lab into Transactional Intervention: target identity, original state/snapshot, affected artifacts, expected/allowed effects and rollback contract before mutation; mutate -> observe -> prove -> commit/rollback.
- Create an Actuation Plane with adapters such as compiler, relink, patch, runtime adapter, Dolphin input/state, Wii deployment, asset/data and build actuators under one contract. Implement adapters only where the live stack proves the need.
- Make InterventionReceipt a first-class durable object with initial state, target fingerprint, intervention identity/version, route, inputs, allowed effects, mutated artifacts, build/runtime identity, outcome, rollback, proof refs and unexpected deltas.
- Add Allowed Delta Enforcement + Behavioral Differential Testing. Success means changed exactly what was authorized while preserved behavior remains inside contract.
- Add Experiment Runtime receiving Unknown/Hypothesis from Evidence/Uncertainty Graph, performing controlled perturbations and returning structured observations/evidence to the same graph.
- Active Learning Intervention Design chooses the experiment/input that maximizes information gain among competing hypotheses and runs it through the cheapest sufficient oracle.
- Oracle Liveness Certification is mandatory. ORACLE_LIVE / STALE / UNVERIFIED (or repo-derived equivalents) gate proof. Freshness must be shown for screenshots, traces, compiler, objdiff, GEX44, Dolphin, deployment and hardware capture before their output can close obligations.
- Reality Scenario Compiler turns a proof obligation into a minimal reproducible launch/state/input/capture/measurement scenario. Scenarios become reusable fixtures with content-addressed identity.
- Scenario CAS / behavioral baseline reuse allows identical scenarios against retail, reconstructed and multiple KSR/WMOS versions with dependency-aware invalidation.
- Behavioral Corpus Factory generates structured runtime corpus: controller traces, state transitions, motion/racket/ball outcomes, timings, audio/rumble and other observables. Build a Retail Behavioral Genome instead of requiring source understanding first.
- Experience Corpus extends behavior to sensory manifestation: animation, camera, sound, rumble, latency and human/perceived response, feeding Experience Genome and Wii Soul/Experience validation.
- Semantic Transplant Compiler: given source/behavior contract A and Semantic ABI B, normalize, adapt, greybox when useful, integrate into host and prove differential behavior. Especially relevant to WSR/Wii Sports/WMOS motion reuse.
- Build Intervention Genome recording phenotype, desired delta, chosen/rejected routes, changed surface, proof, cost, failures, rollback and reuse. Discover Route/Intervention Families by evidence rather than freezing a taxonomy.
- Intervention JIT maturity: Claude-designed intervention -> Procedure IR -> intervention template -> compiled primitive -> zero-planning known route.
- Real-World Vertical Slice Compiler: every large Goal attempts the smallest intervention proving artifact identity, build, deployment, call path, runtime observation and rollback before deeper archaeology.
- Experimental Escrow reserves budget for rollback, validation, unexpected deltas and real-hardware proof. Mutation may not consume the entire mission budget.
- Mutation Sandbox + Causal Binary Archaeology + Automated Behavior Bisect: reversible changes to constants/branches/state/mappings/interfaces, observe, rollback, update hypotheses and localize minimum causal surface.
- Intervention Coverage distinguishes IMPLEMENTED, OBSERVED, PROVEN, HARDWARE_PROVEN and EXPERIENCE_PROVEN (or evidence-equivalent states). Build existence never equals done.
- Production Reality for interventions requires load, execution, real behavioral effect, restart/recovery behavior, preservation contract, rollback and target-hardware proof where applicable.
- Transform Universal Modder field notes/case studies from prose into external specimens: facts, failure patterns, Procedure IR candidates, scenario fixtures, route priors and regression/adversarial tests. External material begins as EXTERNAL_OBSERVED and must pass applicability/replay/proof/CBR before baseline promotion.
- Add adversarial Reconstruction SPEC cases inspired by real failures: stale screenshot/oracle, false route assumption, fake-host pass/real-game fail, wrong fidelity metric, wrong version, route drift, retried dead end and unverified community claim.
- Keep Universal Modder external initially. Do not install globally or make `um` critical-path infrastructure unless a measured adapter capability beats the incumbent.
- Unified loop target: KSR Intent -> Causal Change Graph -> REA Evidence/Unknowns -> candidate seams -> Route Compiler -> transactional intervention/experiment -> REA+Dolphin observations -> Proof Graph -> Allowed Delta verification -> Wii/Experience reality -> InterventionReceipt -> Procedure/Intervention Genome -> ADCR learning -> CBR promotion -> next feature starts cheaper.

**Done gate for activation:** one real bounded intervention closes a product/reconstruction uncertainty faster or more safely than the champion route while preserving truth/proof/rollback. Otherwise keep Universal Modder as donor corpus only.

---

## D14 — Unified Reconstruction compounding program: sequencing and non-duplication guard

**State:** D11–D13 are intentionally deferred as one coherent program, not three independent mega-systems.

**Why deferred:** implementing all concepts simultaneously would violate the same economics they are intended to enforce.

**Activation criterion:** activate by evidence/ROI, one vertical slice at a time.

**Required sequencing:**
1. Reality Scan current Reconstruction owners/call chains first. Reuse/merge/connect before creating.
2. Prove REA/Wii Evidence canary and projection economics before deep Evidence Fabric work.
3. Instrument current reconstruction traces sufficiently to measure Work Classes, model boundaries, repeated procedures, proof and cost.
4. Use that telemetry to activate the smallest ADCR Procedure Compiler canary on one repeated Work Class.
5. Use one real KSR/WSR uncertainty to prove Intervention/Experiment Runtime value.
6. Only promote winning capabilities through CBR after replay/canary/transfer evidence.
7. Expand only where marginal verified cost falls; freeze any layer whose maintenance/meta-cost exceeds demonstrated lifetime saving.

**Constitutional ownership:** REA = observation/evidence sensor; Reconstruction IR/Knowledge/Proof Graph = durable epistemic state; Universal Modder X = actuation/experimental reality; ADCR = procedural learning/how-layer; Cognitive Economics + KEOS = resource and route allocation; GSD X = persistent objective/meta-control; decomp = reconstruction capability execution; CBR/UCR-CIF = maturity/inheritance/ratchet.

**Global done criterion:** the program succeeds only if future comparable reconstruction work is measurably cheaper, faster or safer at equal-or-better proof. Architectural sophistication, component count or documentation volume are not success metrics.

