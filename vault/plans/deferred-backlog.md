# PP Deferred Backlog â€” activation criteria

> Items that could NOT honestly close in the 2026-06-08 session-close
> sprint, each with an explicit activation criterion so a future session
> picks them up without re-discovery. Source audit:
> `vault/audits/session_close_2026-06-08.md`.

---

## D1 â€” apex-completion-standard.md bidirectional drift (verify_spp: `mirror-parity` + `drift-report`)

**State:** global `~/.claude/knowledge_vault/core/apex-completion-standard.md`
(174 350 B, LF-SHA `e553bcc`) â‰  repo copy (158 278 B, LF-SHA `03d9775`).
Both STRICT-FAIL rows share this single root cause.

**Why deferred (not a mechanical looseâ†’PP sync):** the divergence is
**bidirectional and cross-project**, so a blind copy in either direction
destroys content (HR-006: "sync direction propagates corruption
byte-perfectly"):
- **global-only (+195 substantive lines):** *other projects'* axes â€”
  KobiiCraft "NLâ†’DNA Axis" (SesiÃ³n 15), KobiMapEngine Sesiones 16-20,
  "Database Migration Doctrine". The global vault is a **shared
  multi-project accumulator**.
- **repo-only (+178 substantive lines):** PP-only clauses â€” C20
  MCP-Resilience, C21 Slash-Recovery, PP Dataset Baseline (v15),
  Security-First (v16), and now C26/C27 (this session).

**Activation criterion:** Owner decides the canonical model. Two options:
1. **Union-merge** â€” append the PP-only axes into global AND the
   cross-project axes into repo until LF-SHAs match. Tedious, must
   de-dup, must preserve both projects' content.
2. **De-scope the file from mirror-parity** â€” if the apex doc is
   *intentionally* a shared cross-project accumulator that cannot be
   kept in byte-parity, remove it from `verify_global_mirrors.py`'s
   PAIRS list and track PP clauses in a PP-exclusive ledger instead.

Recommended: option 2 (the file's content proves it serves multiple
projects; byte-parity is the wrong invariant for it). ~30-45 min once
the model is chosen.

---

## D2 â€” hooks-registration 6/7 (verify_spp: `hooks-registration`)

**State:** `verify_hooks_registration.py` reports `HOOKS_REG_PROBE=6/7`.
Sub-check `idempotency-mod` fails: 6 hook markers are built on disk but
absent from `~/.claude/settings.json`:
`restart_resume`, `output_contract_stop`, `budget_monitor`, `jit_warm`,
`cascade_check_bash`, `secret_firewall_gate`.

**Why deferred:** writing `~/.claude/settings.json` is **Owner-side** â€”
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

## D3 â€” paths+secrets residual: doc-class (35) + secret-class (9) (verify_spp: `paths+secrets`)

**State after this session's CODE-class fix:**
- `path-leak (code)`: **0** âœ… (3 benchmark JSONs allowlisted â€”
  machine-generated host-pinned records).
- `path-leak (doc)`: 35 in 26 files â€” narrative/command/setup docs that
  reference `C:\Users\User\...` (e.g. `commands/*.md`, `docs/HOOKS_SETUP.md`,
  `vault/knowledge_base/ukdl-universal.md`, dataset + audit `.md`).
- `secret hits`: 9 in 3 files â€” canonical **fake** AWS doc example
  access-key IDs in `tools/secret_rotation_advisor.py`, VPS-IP narrative
  in `vault/audits/manual_tools_audit_*.md`, ssh-alias narrative in
  `vault/knowledge_base/pp_dataset/pp_dataset_01_identity.md`.

`normalize_paths.py` exits 1 while `--check` sees any unallowed doc OR
secret hit, so the row stays RED until both classes reach 0.

**Why deferred:** all 35+9 are non-leaks (narrative / canonical fixtures),
but clearing them correctly means **surgical per-file allowlist entries**
(26 doc + 3 secret), not a broad glob â€” the allowlist is intentionally
file-specific so it never masks a *future* real leak. Doing 29 reviewed
entries exceeds the 30-min defer threshold. NOTE: the secret-class
allowlist edit also trips the HR-SECRET PreToolUse firewall when the
comment names the example-key literal â€” author comments without the
literal token.

**Activation criterion:** add 29 surgical allowlist entries to
`tools/normalize_paths.py::ALLOWLIST` ({"doc-path"} for the 26 narrative
docs, {"secret"} for the 3 fixture/narrative files), each with a one-line
justification matching the existing host-pinned/fixture precedent. Then
`python tools/normalize_paths.py --check` exits 0. ~30-45 min.

---

# Added 2026-09-30 (session 5fb53f17) â€” Owner: "leave everything remaining in the backlog"

## D4 â€” PP Self-Eval: observe the first night (acceptance Â§4.4)

**State:** scheduled task `PP-SelfEval` installed (daily 03:30), code at `e079c57`, gate
`tools/test_pp_eval.py` 38/38. No night has run yet.

**Why deferred:** it can only be observed after 03:30.

**Activation criterion:** after 2026-10-01 03:30, read `~/.claude/state/pp-eval/nights.jsonl`.
Pass = one row with a harvest block or a named skip reason (RAM < 6 GB, owner active). No row
at all = the task did not fire: check `schtasks /Query /TN PP-SelfEval /V` LastTaskResult.
Resumption: `vault/specs/pp-self-eval.RESUMPTION.md`.

**2026-10-01 â€” PASS on the criterion, and a defect it exposed, FIXED.** The task fired:
row `started 2026-10-01T01:30:01Z`, `SKIPPED: a session transcript changed in the last 15 min
(2639597a-....jsonl)`. That transcript is the worker of mission `m-20f1013db18c` (RUNNING), and
7 missions were RUNNING, so "owner active" would have skipped every night a mission was in
flight and D6 could never start. Fix in `nightly.owner_active`: a transcript whose session owns a
live mission (`gsd_mission.mission_for_session`) is not the Owner; an unavailable mission store
fails closed. Gates V-EVAL-MISSION-WORKER-NOT-OWNER, -ENDED-MISSION-IS-OWNER (control),
-MISSION-LOOKUP-FAILS-CLOSED; suite 41/41; isolated drill 2/2 KILLED, control 41/41. Note for
future drills: the harness must also copy `tools/gsd_mission.py` + `tools/gsd_long_run.py`, or
the control goes red. Next observable: tomorrow's row should not skip on a mission worker.

## D5 â€” PP Self-Eval: 5 mutation drills never ran

**State:** S1 4/4 and S2â€“S4 7/12 killed, 0 survived. Not run: quota mid-night stop, quota
ceiling, lock, owner-active skip, proposal gating (`drills_s2s4.json` entries 9â€“13; harness
`eval_drill.py` with a clean-copy control). Both lived in session scratchpad 5fb53f17; if it is
gone, rebuild from the drill list in commit `0ba8565`'s message and this entry.

**Why deferred:** Claude Code reaped the drill for host memory pressure (1.9 GB free of 31 GB)
and asked that it not be restarted unprompted.

**Activation criterion:** free RAM >= 6 GB. Run the 5 drills on isolated copies; each must
print KILLED and the live files must hash unchanged. ~20 min.

**2026-10-01 â€” 4 of 5 RUN on GEX44, all KILLED.** The handoff of 5fb53f17 listed 4 unrun
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

## D6 â€” PP Self-Eval: bank has 0 validated tasks (need >= 8)

**State:** first real harvest reaped after 2 legitimate rejections (an environment-dependent
mirror test; a 200-check suite red at its own fix). Nights harvest 5 per night on their own.

**Why deferred:** memory pressure; the nightly run will continue it without a session.

**Activation criterion:** `python tools/pp_eval.py status` shows `bank_tasks`. If still < 8 after
3 nights, PP's history is too environment-bound (many tests read the live install): add repos
whose tests read their own tree to `~/.claude/state/pp-eval/config.json` `"repos"`.

**2026-10-01:** `bank_tasks: 0, rejected: 2`. Night count toward the 3-night rule: 0 that ran
(the only night skipped on a mission worker, fixed in D4). Not harvested on GEX44 instead: the
bank validates tasks in the environment that ran them, and the nights run on Windows.

## D7 â€” Capability gaps 2â€“6 (audit `vault/audits/se-capability-gaps-2026-09-30.md`)

**State:** gap 1 (self-eval) built. Open, in the audit's order: (2) post-edit diagnostics â€”
`quality-gate.js` only reminds, nothing runs ruff/tsc on an edited file; (3) testing aimed at
user code â€” hypothesis and coverage installed, unused; mutation machinery points at PP only;
(4) SAST + dependency CVE scanning â€” semgrep, osv-scanner/pip-audit not installed; (5) symbol-
level code intelligence â€” no language server installed; (6) CI for PP's own 600+ gates.
Cheap alongside: wire `refcheck` and `done_gate` (built, no caller).

**Why deferred:** Owner chose gap 1 first; each is its own T2 spec.

**Activation criterion:** Owner picks the next gap. Gap 2 is the cheapest (ruff is installed).
Once D4â€“D6 give verdicts, re-rank using the self-eval's own data.

**2026-10-01: gap 2 DONE** â€” `hooks/post_edit_diagnostics.js`, spec
`vault/specs/post-edit-diagnostics.md` (LIVE rows + evidence), 88e8c91 / cfa3275, registered
and proven live. Open: gaps 3â€“6 (each its own T2 spec) and the cheap `refcheck` / `done_gate`
wiring; still waiting for the Owner to pick.

**2026-10-01: gap 3 v1 BUILT** (Owner: "3") â€” `tools/test_gaps.py` + `/test-gaps`, spec
`vault/specs/test-gaps.md`, dc7f781. Uncovered changed lines + surviving mutants on covered
changed lines, in an isolated copy; subprocess-driven tests measured. 14/14 gates; GEX44 drill
6/6 KILLED. Not in v1: hypothesis, fuzzing, flaky tests, non-Python. `/test-gaps` copied live
2026-10-01 (Owner "y"). Real project verified on GEX44 (75b0fd7).

**2026-10-01: gap 4 v1 BUILT** (Owner: "gap 4") â€” `tools/security_scan.py` + `/security-scan`
(live), spec `vault/specs/security-scan.md`. semgrep 1.178.0 (own venv `Apps\semgrep-venv`)
on changed lines + osv-scanner v2.6.0 (official release, SHA-256 verified, `Apps\osv-scanner`)
over lockfiles, `introduced` vs `existing`. UNCHECKED never reads as CLEAN. 12/12 gates (452 s,
needs network). Not in v1: done-gate wiring (blocking Stop hook + network scan = the starvation
shape), SBOM, licences. Open: gaps 5â€“6.

## D8 â€” Mission continuity: merge the UKDL candidates

**State:** `vault/knowledge_base/mission_continuity/UKDL_CANDIDATES_DURABLE_SUBSTRATE.md` not yet
merged into `ukdl-universal.md`. On 2026-09-30 another pane held 884 uncommitted lines there.

**Why deferred:** committing that file would sweep the other pane's hunks into this commit.

**Activation criterion:** `git status -- vault/knowledge_base/ukdl-universal.md` is clean. Then
merge by pathspec and check the hunk headers before committing.

**2026-10-01 check:** still blocked. `ukdl-universal.md` now carries 1248 uncommitted lines
(was 884) and was written 10:45, seven minutes before the check: a live writer.

## D9 â€” Delete the `gsd-long-smoke` worktree and branch `gsd-autonomous-run`

**State:** leftover from the M6 canary; obligation 3 of the 2026-09-30 rollover capsule.

**Why deferred:** destructive; needs an explicit Owner yes (a bare "y" to a two-option question
was not taken as one).

**Activation criterion:** Owner says delete. Then read both first (worktree status, unpushed
commits on the branch) and delete only if nothing unique would be lost.

**2026-10-01 â€” Owner said delete; NOT deleted, unique work found.** Repo
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

## D10 â€” `test_hook_mirror_identity` red 3/5 (other panes' files)

**State:** new live/repo drift in `hook-dispatcher.js`, `zero-issue-gate.js`; stale
KNOWN_DIVERGENCES entries `closer-guard.js`, `learning-sentinel.js`,
`windows-bash-bridge-guard.js`. `research-intent-detector.js` was reconciled in `55fe169`.

**Why deferred:** those files belong to live work in other panes.

**Activation criterion:** when those panes commit, decide per file which side wins (the gate's
own instruction), sync, and drop the stale entries so the ratchet turns.

**2026-10-01 â€” now 4/5.** Stale entries dropped (the three files are identical on both sides).
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

# Added 2026-10-10 â€” GSD X Reconstruction Fabric deferred program

## D11 â€” REA as Reconstruction Evidence Fabric / Static Oracle substrate

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
- Build Cross-Binary Entity Alignment / Cross-Title Homology over Reconstruction IR for WSR â†” Wii Sports and later titles/builds. Classify EXACT, RELOCATED, NEAR, STRUCTURAL, FAMILY and NOVEL across functions plus types/vtables/globals/TUs/strings/call neighborhoods.
- Add Differential Evidence / Differential Dossiers so homologous entities materialize only the delta, retained/common facts and compatible source transformations rather than two full dossiers.
- Adopt retained Evidence as the durable object and reconstruction-specific projections as the model-facing unit: triage, type, compiler, homology, runtime and proof projections. Full-read admission gate prefers facet/range/symbol/projection/query before whole evidence materialization.
- Evolve REA-style Reconstruction Obligation Ledger into a live Proof Graph/runtime state: claims, owners, dependencies, proof requirements, evidence, unknowns, contradictions, dispositions and completion level. New evidence may close, weaken, invalidate or unlock obligations.
- Keep fail-closed truth levels separate: IDENTIFIED, STRUCTURALLY_SUPPORTED, SEMANTICALLY_SUPPORTED, BUILD_PROVEN, BINARY_MATCHED, RUNTIME_PROVEN, HARDWARE_PROVEN, EXPERIENCE_PROVEN or evidence-equivalent repo-derived states. UNKNOWN/PARTIAL/CONTRADICTION never imply PASS.
- Make compiler, mwcceppc and objdiff first-class Evidence producers. Exact match is strong build proof; mismatch is also structured evidence with fingerprint, location, distance, candidate context and prior repair history.
- Make Negative Evidence first-class and persist reconstruction search trees: non-compiling candidates, mismatch classes, falsified hypotheses, non-applicable families, discarded branches, distances, diagnoses and remaining frontier. Hard rule: do not retry an equivalent disproven branch under the same dependency state.
- Every solved/matched entity checks for siblings/family opportunity. Family candidate path: detector -> template/candidate generation -> historical replay -> holdout/adversarial benchmark -> certification -> corpus scan -> exceptions only to reasoning.
- Add Reconstruction Obligation Economics: expected cognition/context/compile/runtime/hardware cost, probability of success, unlock count, product relevance, reuse/institutional value and proof criticality. KEOS buys information by Expected Total Verified Cost + Information Gain + downstream unlock rather than task order.
- Close staticâ†”runtime loop with Active Runtime Questions and an Experiment Compiler. Static ambiguity should generate the cheapest discriminating experiment; GEX44/Dolphin returns structured evidence into the same graph.
- Add Dolphin Runtime Evidence Adapter and retain Real Wii as higher authority where required. Never infer Wii PASS from Dolphin PASS.
- Make Behavioral Evidence first-class beside assembly: input traces, state transitions, racket/ball response, timing and observable effects. Build toward causal evidence rather than correlations only.
- Add Semantic ABI Mining / Interface Archaeology: discover and prove boundaries by inputs, outputs, state, ownership, timing, side effects, failure semantics and calling/memory contracts. Proven boundaries may allow internals to remain opaque.
- Add provider-agnostic Context ABI and zero-transcript reconstruction. The institution remains stateful while processors remain replaceable/stateless; Context Compiler emits only mission/state/unknown/evidence/capability/proof/output-contract projections.
- Prefer upstream REA vanilla/pinned initially. CONNECT -> MEASURE -> WRAP -> EXTEND. Fork/overlay only for a demonstrated Wii gap whose lifetime ROI beats upstream maintenance cost.

**Done gate for activation:** same target, same proof and authority as current champion; evidence/context/tool-call/rediscovery cost must improve or a unique capability must be demonstrated. No REA integration is promoted merely because the API exists.

---

## D12 â€” ADCR-Reconstruction â†’ Procedural Intelligence / Self-Compiling Reconstruction Institution

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

## D13 â€” Universal Modder X as Intervention + Experimental Reality Plane

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

## D14 â€” Unified Reconstruction compounding program: sequencing and non-duplication guard

**State:** D11â€“D13 are intentionally deferred as one coherent program, not three independent mega-systems.

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

---

# Added 2026-10-10 â€” KME Recon, Visual Reconstruction, Time-to-Ready and Derived Development

## D15 â€” KME Recon as Software Reality / Construction Reality Laboratory

**State:** design expanded from the KME/KSR optimization corpus. KME is treated as the digital-heavy reference workload for Reasoning Locality, Proof Locality, Invalidation Locality, source-navigation economics and repeated software construction. No claim that the full model below exists in production.

**Why deferred:** KME already has active optimization/reconstruction work and a measured cost baseline. Building a parallel "KME OS" would violate current ownership and compounding doctrine. The ideas below should be activated only as thin extensions/adapters to the existing universal runtime owners when a KME canary demonstrates a specific economic or quality win.

**Activation criterion:** choose one bounded KME Work Class with a measured old-path baseline, such as a repeated arena/map/generator/registry/lifecycle change. Before implementation, compile its semantic closure, current owner, mutation surface, proof closure and expected model boundaries. Promote only mechanisms that beat the champion on verified cost, reasoning radius, source-read burden and proof locality.

**Deferred scope (complete):**
- Position KME Recon as a Software Reality Compiler rather than a repo-reading workflow. Source remains authority; the default working surface becomes a typed Software Reality Model queried by symbol/owner/contract/state/proof rather than by whole-file archaeology.
- Build a KME Semantic Genome spanning symbols, types, registries, generators, state machines, events, ownership, configuration, serialization, runtime bindings, tests, proofs, failures, change families, effects and authority.
- Create Feature Genome and Registry Genome views. Registry semantics should capture producer -> registry -> consumer -> lifecycle -> proof, plus schema, writers, readers, initialization phase, invalidators, required invariants and known failure modes.
- Add Semantic Dominator / Registry Dominator analysis: identify upstream constraints whose resolution unlocks many downstream features rather than fixing leaves individually.
- Reconstruct Effective State Machines from AST/call graph/tests/logs/runtime traces/config. Distinguish legal, guarded, contradictory, unreachable and unobserved transitions. Lifecycle grammar/families should emerge from corpus evidence rather than be hard-coded prematurely.
- Strengthen the Construction Compiler: Desired Semantic Delta + Current Software Reality -> affected objects, known transformations, unknowns, mutation closure, proof closure, rollback and deopt conditions. Planning prose is not an execution authority.
- Discover Change Families such as arena/map/generator/registry/state/serialization/runtime-provider mutations from evidence. Mature families progress from manual -> procedure -> template -> certified transformation -> compiler primitive.
- Build a Structural Transform Library only after preconditions, negative cases, proof and rollback are established. Known transformation fast paths must deopt on novelty or violated assumptions.
- Replace source navigation with Semantic Source Queries: materialize only the definition, relevant callers, owners, invariants, registry/state relationships and tests needed by the active obligation.
- Keep Source-as-Authority / Model-as-Projection. Raw source is reread only for changed hash, missing derivation, contradiction, audit or deopt. Stable derivations are reused.
- Add source CAS / derived-state CAS: same source identity + parser/version -> same semantic derivations. Avoid reparse/reread/re-interpretation across workers.
- Build Commit -> Semantic Delta compilation. Each commit can derive changed symbols/contracts/registries/state transitions/tests/proof requirements and invalidated decisions.
- Add a Semantic Git layer: Git reports file deltas; the semantic layer reports contract/state/owner/proof impact. Add semantic blame and semantic time travel to recover why a contract exists, which decision introduced it, what proof certified it and what state existed before a migration without transcript archaeology.
- Counterfactual Change Planner: before mutating source, estimate affected feature/proof/owner/runtime closure for candidate changes and prune dominated routes.
- Build a Change E-Graph: configuration, reuse, adapter, new code, certified transform, no-work certificate and other routes can satisfy the same semantic postcondition; Cognitive Economics selects the non-dominated route with minimum Expected Total Verified Cost and risk.
- Dead Change Elimination / semantic partial evaluation: prove already-satisfied, implied, non-applicable and unreachable obligations before planning new work.
- Proof-of-Non-Change and preservation contracts become first-class: prove both intended delta and protected invariants.
- Add Change Blast Radius Budget and Cognitive Blast Radius. Unexpectedly large affected semantic closures or reasoning surfaces are architectural signals and can stop a mutation before waste compounds.
- Add Reconstruction Radius / Causal Cone Compiler for bugs: failure -> candidate causal cone -> cheapest discriminating probe -> narrowed reconstruction slice. Avoid whole-project comprehension.
- Failure Causal Fingerprints must contain causal discriminators such as last valid transition, first invalid transition, registry/config/runtime owner state and changed dependency class; never cache symptom -> fix as if causal identity were known.
- Failure Motif Compiler: first occurrence may require frontier diagnosis; recurrence should move toward structured diagnosis, compiled probe, test/guard, and eventually architectural impossibility where justified.
- Error -> Immunity: expensive failures should attempt to crystallize as typed invariant, detector, test, compiler check, migration rule, transaction guard or failure fast path.
- Runtime Spec Mining compares declared architecture with observed event/state/runtime behavior. Differences create Architecture Drift contradictions rather than silently stale docs.
- Registry Drift Detector and runtime-contract extraction should expose inputs, outputs, state transitions, owned effects, reload/error semantics and compatibility where justified.
- Contract Coverage and Proof Graph should measure which contracts are actually evidenced, not only line/test coverage.
- Predictive Proof Compiler learns which proofs normally catch regressions for each change family while mandatory invariants remain hard constraints.
- Proof Debt becomes visible when tiny changes require broad/full-suite revalidation because proof locality is missing.
- Build a Test Semantic Index: map tests to invariants/contracts/failure classes/semantic objects instead of relying on grep by name.
- Test Value Attribution may identify proof redundancy or blind spots, but quality/correctness constraints dominate token savings.
- Construction Transactions: once semantic decision is made, mutation -> format/lint -> affected tests -> evidence -> gate -> commit should be deterministic unless a semantic fault occurs.
- Transaction Templates for mature change families carry preconditions, effects, rollback, proof and failure semantics.
- Counterexample-Guided Construction: failed proof yields a minimal counterexample/refinement for the affected Work Unit, not a global replan.
- Use cheap software Mutation Sandboxes/worktrees for reversible causal experiments, candidate variants and speculative construction before high-cost review.
- Enable bounded speculative search only where expected value exceeds coordination cost. Survivors, not every branch, reach model/review boundaries.
- Semantic MVCC and semantic conflict detection: workers operate on state version N and commit only if semantic dependencies still hold. Detect conflicts even when Git files differ and permit safe coexistence when file overlap is semantically independent.
- Ownership Solver: before mutating a high-impact state/registry/serialization/runtime/proof surface, resolve actual owner and authority. Ownership Centrality increases proof and change caution for high-fanout owners.
- Architecture Refactoring by Cognitive OPEX: repeated high-context/high-call/high-repair subsystems become refactoring candidates because they impose future AI maintenance cost.
- AI-Operability becomes a measurable NFR: owner discoverability, contract explicitness, state queryability, mutation locality, proof locality, failure observability, incremental invalidation and cold-start correctness.
- Architecture documentation becomes a generated/reconstructible view of source/traces/tests, not a parallel authority.
- Build an Epistemic Software Twin: current source identity, contracts, states, owners, failures, proof freshness, unknowns and allowed transformations. Models reason over the twin and page raw repo evidence only under need.
- Semantic time travel and semantic regression analysis should use versioned state/proof/decision objects, not transcript search.
- Treat Reconstruction as Incremental Compilation: source delta -> invalidate affected semantic objects -> recompute derived objects -> invalidate affected proof -> compile next Work Units.
- Make-style cognition: unchanged dependencies mean no re-read, no re-reason, no re-proof.
- Build Semantic Build Cache for facts/contracts/decisions/transforms/proofs/test mappings keyed by dependency/version/applicability.
- Distinguish provider prompt-cache hits from institutional semantic hits. The stronger hit eliminates the model boundary entirely.
- Predict change shape before execution and compare predicted vs actual affected objects/proofs/risk/context to train Construction Compiler profiles.
- Measure Construction Regret: actual verified cost minus best known ex-post route for the same semantic postcondition.
- Work-Class/Change-Family Closure requires detector, preconditions, transform, negative cases, proof, rollback, context profile and deopt. Mature zones default to zero frontier.
- Pursue Zero-LLM Construction Zones and later Zero-Raw-Read Zones for dominated change families.
- Maintain a Reconstruction Frontier Map by maturity: known/compiled, known-family exceptions, structurally-known/transform-unknown, novel architecture. Frontier cognition should concentrate on truly novel areas.
- Novelty Concentration, not repo size, should drive model budget.
- Benchmark elasticities: registry-count, project-age, state-space, proof-estate and ownership-estate growth should not proportionally increase local Work Unit cognition.
- Create KME Reconstruction Gym from historical incidents and seeded mutants: registry/generator lifecycle, serialization mismatch, stale verification, runtime/config drift, concurrency and ownership ambiguity.
- Include cognitive/epistemic mutants too: missing critical semantic page, stale contract, wrong owner, hidden proof, misleading docs. Correct response is page/deopt/abstain, never hallucinated action.
- Source Evidence Fabric: every derived architecture fact carries source identity, parser/version, symbol refs, runtime corroboration where applicable, confidence and invalidators.
- Cross-version reconstruction should diff semantic state rather than reread entire releases. Cross-plugin/mode homology should identify reusable Feature/Change Families.
- Construction Compiler + ADCR: learn which construction procedure minimizes total verified cost for each Work Phenotype.
- Construction Procedure Genome records phenotype, preconditions, source slice, transform, proof, repairs, cost and failure envelope; procedural homology discovers shared construction skeletons.
- Construction JIT maturity: Claude change -> procedure -> template -> transformer -> compiler pass -> architectural primitive.
- Reuse Universal Modder X's Transactional Intervention contract for software-only changes: isolated state -> mutate -> test/runtime -> proof -> commit/rollback -> InterventionReceipt.
- Use REA only where binary/runtime reality adds information not available from authoritative source; no ceremonial binary RE.
- Every expensive KME incident returns project/domain/universal candidates through CBR, with cross-domain falsification before broad promotion.
- Add a fifth KME compiler above the existing Reality/Decision/Construction/Proof model: Reconstruction Compiler decides the minimum architecture slice that must actually be understood before action and may emit a No-Reconstruction Certificate when interfaces already suffice.
- Semantic-interface-first and opaque-island policy: reconstruct internals only when the desired change/proof cannot be achieved through a proven interface.
- Architecture Understanding Budget and Source-Read Budget limit curiosity-driven archaeology; growth requires causal justification.
- Metrics: Query-to-Read Ratio, Derived-State Hit Rate, Reconstruction Cache-Miss Reason, Architecture Read Amplification, Semantic Compression Ratio, Change/Failure/Proof Learning Curves, Fresh-Worker Time-to-First-Valid-Action.
- North Stars:
  - Repository Size Must Not Determine Reasoning Size.
  - Known Software Change Must Converge Toward Zero Raw Reads and Zero General Cognition.
  - Every Expensive Reconstruction Must Either Eliminate Future Reconstruction or Prove Why It Cannot.
  - Larger/more mature KME should make mastered changes cheaper, not more expensive.

**Done gate for activation:** one repeated KME change family is executed from cold birth with materially smaller raw-source read volume, reasoning closure, model-boundary count and proof closure than the current champion, while equal-or-better Production Reality and correctness are preserved.

---

## D16 â€” Visual Reconstruction Fabric / Image-to-System Reconstruction

**State:** conceptual extension of typed VisualEvidence, Experience Genome and Reconstruction/Intervention loops. Not implemented as an authoritative visual spec generator.

**Why deferred:** image/video evidence is partial and ambiguous. It becomes dangerous if treated as an exact specification or if visual similarity is allowed to substitute for behavioral/runtime proof. The layer should only be activated with explicit uncertainty, provenance and differential validation.

**Activation criterion:** choose one bounded KSR UI/scene or KME map/scene where known reference images/video and a candidate implementation exist. Demonstrate that structured visual constraints plus a differential oracle reduce implementation iterations without creating false certainty.

**Deferred scope (complete):**
- Treat image/video as partial observations of a hidden system, not as specifications. Every inferred property is typed as OBSERVED, ESTIMATED/CONSTRAINED, AMBIGUOUS or UNKNOWN with provenance/confidence.
- Ingest reference media into Visual Evidence Objects containing hash, resolution/aspect/crop, provenance, game/build/platform/state when known, camera hypothesis, regions, confidence and unknowns.
- Bind produced screenshots/video to exact build/config/assets/deployment/runtime/hardware identity. Unbound visual evidence cannot close Production Proof.
- Image -> Visual Scene Graph: derive components, hierarchy, bounds, layer/depth, alignment, anchors, visibility, occlusion, material/texture hypotheses and interaction state.
- Create Visual UI IR with primitives such as container/grid/card/icon/text/cursor/focus/mask/background/overlay/page indicator and typed relations such as aligned-with, anchored-to, inside, occludes, repeats-pattern, focused-by and transitions-to.
- Infer layout laws and constraints rather than copying absolute coordinates. Resolution-independent relationships are preferred when supported by evidence.
- Build a Visual Constraint Solver for repeated geometry, grids, spacing, anchor relationships, camera/layout parameters and other deterministic constraints.
- Convert repeated visual observations into semantic invariants and reuse them without rereading raw screenshots.
- Mine a Visual Grammar / Wii Visual Grammar from high-quality reference states: composition, hierarchy, density, focus affordances, page indicators, timing, depth, color/contrast relationships and other repeated laws. Grammar is evidence-backed and scoped, not style folklore.
- Maintain a Visual Genome for screens/scenes/features: layout topology, primitives, ratios, typography, palette relations, depth, state variants, animation families, interaction cues, camera, lighting and environmental mood.
- Cross-Screenshot Homology classifies SAME_COMPONENT, MOVED, RESIZED, STATE_CHANGED, ASSET_CHANGED, VISIBILITY_CHANGED, LIGHTING_ONLY, CAMERA_ONLY or repo-derived equivalents.
- Differential visual dossiers should extract the smallest state delta between normal/hover/confirmation/transition states.
- Image sequences/video -> Interaction State Machine: infer states, transition timing, easing, z-order changes, pointer movement, visual feedback and correlated audio/haptic events.
- Build Visual Motion Genome for recurrent animation families such as focus growth, hover glow, panel transitions, confirmation pulses and cursor settle.
- 3D visual reconstruction uses horizon/vanishing points, approximate camera pose/FOV, relative scale, occlusion/depth order, lighting/shadow constraints and surface hypotheses while preserving unknown geometry as unknown.
- Multi-view/video observations reduce ambiguity. Never hallucinate unseen geometry; maintain candidate hypotheses.
- Active Visual Reconstruction / Next-Best-View Compiler: when hypotheses remain, request or acquire the image/angle/frame/resolution/state with greatest expected information gain.
- Visual Causal Probing combines Mutation Sandbox with visual evidence: perturb candidate layout/camera/material/state parameters, render, compare, rollback and update hypotheses.
- Build Visual <-> Software Binding Graph: link visual nodes to candidate assets/materials/widgets/source/runtime draw owners using identity, dimensions, usage, instrumentation and graph evidence.
- Where instrumentation supports it, expose visual xrefs from rendered region/component -> render object -> asset/material/state -> source owner.
- Render provenance instrumentation can emit component IDs, asset IDs, transforms, state and z-order to make visual diagnosis causal rather than archaeological.
- Visual Differential Oracle compares by semantic layers: geometry, structure, style/material, typography, state, lighting, camera and temporal behavior, not only pixel MSE.
- Weight perceptual differences by semantic salience; thousands of background pixels must not hide a critical 2 px interaction alignment error.
- Keep human Experience Oracle for qualities that metrics cannot close: Wii soul, warmth, calm, delight, social readability. Objective visual metrics are supporting evidence, not replacements.
- Visual Fidelity Ladder distinguishes layout, structure, asset, state, motion, camera, render, hardware-visual and experience acceptance. A visually close image does not prove interaction parity.
- For KSR Page 2 and similar UI, reconstruct a reusable Visual/Interaction Contract and family rather than one screenshot.
- Mature KSR menu families can become deterministic development primitives with canonical grammar, state-machine behavior, content slots and affected proof.
- For KME maps/scenes, image -> spatial constraints may infer regions, landmarks, terrain/path relationships, visual hierarchy and candidate generator parameters.
- Multi-image/dataset analysis can infer latent generation grammar: recurring motifs, spacing distributions, connectivity, region hierarchy, spawn/landmark placement and symmetry/asymmetry.
- Build a Visual Family Solver across map/screen specimens, then correlate visual clusters with source/generator parameters.
- Visual Regression Compiler selects only affected visual states to recapture based on semantic dependency changes.
- Visual Proof Cache and Visual Invalidation Radius retain valid visual proofs until relevant layout/asset/camera/shader/state dependencies change.
- Image Evidence CAS deduplicates unchanged visual evidence and derived observations.
- Region-level visual paging: model only the relevant crop + surrounding context + scene metadata where full frame is unnecessary.
- Visual ContextImage and Visual Dead Rent apply the same Cognitive Economy principles to images/video; do not drag irrelevant visual assets across model boundaries.
- Visual Evidence Compiler maps a visual claim + available evidence + assurance level to the minimum missing observation.
- Synthetic Visual Evidence can use debug/wireframe/depth/hitbox/anchor/component-ID views for diagnosis but cannot silently replace Production Visual Evidence.
- Visual Instrumentation Mode should expose bounds, anchors, state, z-order, ownership and IDs where product architecture permits.
- Visual Semantic Bisect / temporal bisect aligns retail/reference and candidate sequences to identify first semantic divergence in component/state/timing rather than vague "feels off" diagnosis.
- Audio-visual-rumble alignment yields a Multimodal Experience Timeline; reconstruction can include sensory timing, not only frame appearance.
- Maintain Visual Confidence Map per region/property and spend additional acquisition only where uncertainty is decision-relevant.
- Value of Visual Information gate: do not request/acquire another visual reference if it cannot change an implementation/proof decision.
- ADCR learns a Visual Reconstruction Procedure Genome: best sequence of scene graph, layout solver, asset binding, runtime instrumentation, diff and proof per Work Phenotype.
- End-state: reference media -> Visual Evidence -> constraints/graphs -> unknowns -> minimal missing views -> software/assets/runtime bindings -> Construction Compiler -> candidate render -> semantic visual diff -> affected repair -> hardware/experience proof -> reusable Visual/Feature Family.
- Constitutional law: AN IMAGE IS NOT A SPECIFICATION. IT IS A PARTIAL OBSERVATION FROM WHICH THE MINIMUM SUFFICIENT SPECIFICATION MUST BE RECONSTRUCTED.
- Stronger endpoint for KME: image-to-reconstruction may become image-to-system-reconstruction by inferring a generator/grammar that can produce an entire family of high-quality outputs, not only one copied artifact.

**Done gate for activation:** a visual reconstruction canary reaches equal-or-better functional/visual proof with fewer manual iterations and no unsupported certainty; missing/unseen properties remain explicitly unknown or are resolved by new evidence.

---

## D17 â€” Universal Time-to-Ready Compression / Readiness Compiler

**State:** conceptual extension over Mission Compiler, Cognitive Economy, Readiness/Production Reality, hardware batching and cold-birth work. No separate Ready OS should be created.

**Why deferred:** Time-to-Ready is cross-cutting. Implementing a broad scheduler before measuring actual blockers could create another control layer. Activate only by integrating readiness semantics into existing universal owners and by targeting dominant measured blockers.

**Activation criterion:** instrument one KME, one reconstruction and one KSR/game workload to measure time from intent to first valid action / first observable / first discriminating evidence. Use the profiler to identify the dominant readiness blocker and prove that one minimal intervention shortens the critical path without weakening proof.

**Deferred scope (complete):**
- Define formal readiness states such as INTENT_READY, REALITY_READY, KNOWLEDGE_READY, ENVIRONMENT_READY, CONSTRUCTION_READY, EXPERIMENT_READY, PROOF_READY, DEPLOYMENT_READY, HARDWARE_READY, OWNER_READY, PRODUCTION_READY and ACTION_READY, allowing repo-derived refinement.
- Every Work Unit has a Readiness Contract: required facts, tools, environment, assets, authority, proof path, external resources, hardware/human interaction and downstream outputs.
- Add Readiness Graph alongside Execution/Epistemic/Proof graphs. Readiness expresses prerequisites preventing productive action.
- Add Readiness Dominator analysis: prioritize blockers whose resolution unlocks many downstream Work Units. Use Unlock Multiplier = downstream work made ready / cost.
- Compute Ready Critical Path and target earliest first useful reality interaction, not just earliest planner output.
- Metrics: Time-to-First-Valid-Action, Time-to-First-Observable, Time-to-First-Discriminating-Evidence, Intent-to-Proven-Ready and Intent-to-First-Proven-Delta.
- Ready-first planning: ask what preparation makes the most valuable work ready earliest, rather than simply "what task is first".
- Preflight Compiler deterministically checks identity/version, environment, dependencies, tool availability, build health, tests, disk/RAM, remote resources, hardware availability, indexes, artifacts and known blockers before expensive cognition.
- Fail-fast readiness: unknown prerequisites are planning defects. Missing toolchain/authority/hardware/data should be discovered before a large mission boundary.
- Ready Snapshot and Golden Environments for recurrent KME, Reconstruction, Dolphin and Wii workflows. Environment state is versioned, reproducible and invalidated by dependency changes.
- Environment CAS / readiness cache: reuse proof that a toolchain/environment/precondition is ready while its dependency envelope remains valid.
- Readiness freshness is dependency-based, not session/time based unless reality inherently drifts.
- Prewarming and pipeline overlap: while upstream reasoning/implementation runs, prepare likely build/test/proof/deployment/evidence prerequisites that are safe and high-VoI.
- Separate concurrent lanes for reasoning, build, evidence, proof and deployment where dependencies/effect isolation permit.
- Next-step prediction and Readiness Prefetch use ADCR profiles to prepare likely fixtures/indexes/proofs outside model context without speculative irreversible mutation.
- Readiness TLB: mature Work Classes know common prerequisite object IDs/projections and validate fingerprints instead of rediscovering setup.
- Ready Packets: expensive model workers spawn only after deterministic prerequisites, semantic state, source/evidence projection, environment, tools, sandbox, proof and budgets are prepared.
- Hard law: expensive workers should not prepare themselves when preparation can be deterministic or done in advance.
- Readiness Admission Gate rejects a frontier spawn if unresolved deterministic prerequisites remain.
- Agent warm-up tax should trend toward zero; "missing prerequisite after spawn" becomes telemetry for Readiness Compiler improvement.
- Ready once, consume many: common architecture facts/builds/proof maps/reference states are shared by semantic identity rather than copied into each worker.
- Shared Readiness Services may expose Symbol Index, Proof Map, Build, Asset, Scenario/Reference and Deployment capabilities under universal ownership.
- One Build -> many consumers; do not rebuild identical artifacts separately for tests, runtime, visual capture or experiments.
- One Boot / one expensive external action -> maximum compatible evidence/proof/readiness via safe evidence multiplexing.
- Human/Hardware Critical Path and Owner Batch Compiler prepare all compatible Owner/hardware-only actions before scarce availability windows.
- Authority Readiness is explicit from the start; late discovery that Owner permission is required is a planning defect.
- Asset Readiness for games includes textures/models/animations/audio/collision/fonts/references and should run in parallel with code reconstruction where independent.
- Image-to-Reconstruction readiness: ingest references, scene/constraint graph, missing-view questions, state alignment and asset candidates before implementation begins.
- Reconstruction dual lane: Code/Behavior lane and Experience/Visual/Audio/Input lane advance in parallel and join at integration proof.
- Binary Reconstruction readiness performs AOT cheap corpus processing: hashes/sections/symbol seeds/signatures/family candidates/compiler patterns/type clues/strings/imports/homology before function-level hot work.
- AOT + JIT Reconstruction: precompute cheap global knowledge once; strong reasoning occurs only on product-critical or novel hot closures.
- Product-critical prefetch and semantic-closure forecast stage likely homologues/types/compiler families before downstream consumers discover them.
- Ready-by-family and Ready-by-homology: certified family/homologue immediately links procedure, proof and context profiles.
- Unknown staging: frontier workers receive hypotheses, available oracles, costs and expected discrimination rather than naked "investigate".
- Hypothesis-ready packets minimize model warm-up and maximize immediate causal reasoning.
- Proof-first readiness: if success cannot be observed/proven, a Goal is not Construction Ready. Build observability/proof first.
- Debug readiness requires reproducible failure, artifact identity, expected invariant, sufficient observability and rollback.
- Reproduction Compiler turns manual bug reproduction into reusable fixtures.
- Distinguish Ready-to-Code and Ready-to-Prove. Work can be construction-ready but proof-blocked; do not let implementation consume proof capacity.
- Proof Preparation / Proof Escrow: prepare fixtures, baseline and proof plan before implementation finishes.
- Capture baselines before changing systems when later comparison may be necessary.
- A/A readiness precedes A/B when the environment/path has meaningful nondeterminism.
- Make readiness monotonic where possible: unrelated changes do not reset ready states.
- Readiness Invalidation Radius measures how many ready facts/fixtures become stale after a change; broad invalidation signals coupling.
- Readiness Debt = implemented inventory that cannot yet be tested/deployed/observed/proven/released.
- Control WIP to reduce cycle time; prefer closing shared readiness chains over opening many leaves blocked by the same prerequisite.
- Explicit queue states: READY, RUNNING, WAITING_REALITY, WAITING_AUTHORITY, WAITING_BUILD, WAITING_PROOF, BLOCKED_DEPENDENCY, DONE or repo-derived equivalents. "In progress" alone is insufficient.
- Waiting consumes zero model cognition. Events such as BUILD_READY / INDEX_READY / EVIDENCE_READY / HARDWARE_AVAILABLE / OWNER_DECISION_RECEIVED wake exact consumers.
- Build a Time-to-Ready profiler and Readiness Flamegraph: dependency discovery, setup, build, human waiting, archaeology, proof setup, novelty and other components.
- Readiness Roofline classes: KNOWLEDGE_BOUND, ENVIRONMENT_BOUND, BUILD_BOUND, HARDWARE_BOUND, AUTHORITY_BOUND, OBSERVABILITY_BOUND, PROOF_BOUND, NOVELTY_BOUND.
- Critical-path Amdahl: after each optimization, reprofile and attack the next dominant readiness bottleneck.
- Readiness Resource Vector includes tokens, wall time, compute, network, hardware, human attention, money, risk and proof.
- Time-to-Ready Superoptimizer chooses equivalent routes by Expected Time to Verified Ready State, not merely coding time or token cost.
- Fastest implementation may be dominated by a slower initial analysis that avoids long debugging/repair loops.
- ADCR stores historical TTR profiles by Work Class; future planning learns empirical setup/build/proof/repair/human-wait distributions.
- Readiness Regret = actual TTR minus best known ex-post route; repeated high regret becomes a Procedure/Capability candidate.
- Readiness learning curve: occurrence 1 expensive -> recurrence progressively cheaper -> mature family immediate or near-immediate.
- Zero-Setup, Zero-Discovery, Zero-Planning, Zero-Wait and Zero-Proof-Setup zones are maturity endpoints where economics justify them.
- Continuous Ready State for high-frequency infrastructure only if warm-maintenance cost < recurring cold-start cost; otherwise Just-in-Time / Just-ahead-of-time readiness.
- Safe speculative readiness may precompute indexes/fixtures/assets/reference extraction without irreversible effects.
- Ready-path common-subexpression elimination and Goal-level singleflight coalesce shared build/tool/index prerequisite work.
- Estate-wide Readiness Graph lets KEOS prioritize one common capability that unlocks multiple goals/projects.
- Capability Demand x Readiness Impact is a stronger platform-investment signal than architecture enthusiasm.
- Readiness Bottleneck Mining detects recurring setup/tool/owner/baseline/fixture waits and proposes shared machinery.
- Constitutional pressure law: repeated blocker -> readiness capability.
- Experience/Game-Feel Ready Packs, Reconstruction Ready Packs and KME Ready Packs precompile domain-specific prerequisites under the same universal readiness semantics.
- Fresh-worker Ready Cold-Start Score measures time/tokens/wrong actions/page faults/manual asks until first correct useful action.
- Ready-state portability requires snapshots/manifests/CAS so a worker/machine/GEX44 can restore productive state without tribal laptop/session context.
- Disaster Recovery Readiness is also Time-to-Ready: measure productive recovery after machine/process/session loss.
- Core laws:
  - NO EXPENSIVE INTELLIGENCE SHOULD BE SPENT PREPARING CONDITIONS THAT CAN BE PREPARED DETERMINISTICALLY OR IN ADVANCE.
  - THE BEST OPTIMIZATION IS NOT MAKING WORK FASTER; IT IS MAKING THE NEXT CORRECT ACTION READY EARLIER.
  - AS CPP LEARNS, INTENT-TO-PROVEN-READY SHOULD APPROACH THE IRREDUCIBLE LATENCY OF ACQUIRING GENUINELY NEW REALITY.

**Done gate for activation:** at least one reference workload reaches first valid/proven action materially sooner because deterministic readiness preparation/blocker-dominator elimination moved work off the critical path, with no increase in wrong first actions, stale evidence or proof debt.

---

## D18 â€” Universal Derived Development Fabric: image-, dataset-, reconstruction-, idea- and expectation-driven development

**State:** conceptual generative layer built on Feature IR, Reconstruction/Construction/Proof/Readiness and CBR/ADCR. No separate per-source runtime should be created.

**Why deferred:** these modules can become a speculative design cathedral if activated before Feature Genome, evidence provenance, quality/proof semantics and reusable families are measurable. They must compile into the same universal Feature IR and reuse existing owners.

**Activation criterion:** select one KME map/feature or KSR sport/UI where at least two input modes (for example reconstructed feature + image reference, or dataset + idea/expectation) can be compiled into a Feature IR and shown to reduce Time-to-Ready or raise measurable quality without copying unrelated implementation.

**Core architecture:**
- Inputs may include Image, Video, Dataset, Reconstructed Feature/Map/System, Behavior Trace, Human Demonstration, Idea, Expectation, Failure, Preference and Outcome.
- Source-specific frontends compile into one Canonical Feature IR; there are not five parallel development OSes.
- Canonical Feature IR should include Intent, desired user/emotional outcome, Expectations, Interaction Contract, Behavioral Contract, Visual Contract, Audio/Haptic Contract, Spatial Contract, System Interfaces, State Machine, Invariants, Failure Semantics, Performance Envelope, Quality Vector, Reference Evidence, Ancestry, Allowed Innovation, Unknowns, Construction Obligations and Proof Obligations.
- Development Source Compilers include Visual/Image Compiler, Dataset Pattern Compiler, Reconstruction/Feature-Derivation Compiler, Map Grammar Compiler, Behavior/Demonstration Compiler, Idea Compiler and Expectation Compiler.
- All source claims retain provenance and authority. Desired/expected/inferred/observed/proven are never silently conflated.

**Image-Derived Development:**
- Derive design laws, visual grammar, composition, interaction states, timing, camera and constraints from image/video evidence rather than only copying pixels.
- Use Visual Reconstruction Fabric outputs as donors to new Feature IR. A reference can teach hierarchy/spacing/focus/depth/warmth without forcing the same surface design.
- Image-derived development may create wholly new interfaces/maps/features that preserve proven visual/interaction laws while changing content and identity.

**Dataset-Derived Development:**
- Datasets become generative knowledge sources, not retrieval-only corpora.
- Pipeline: dataset -> observations -> clusters/families -> invariants/distributions -> candidate causal correlates -> failure boundaries/outliers -> quality frontier -> design laws -> construction heuristics -> capability candidates.
- Avoid "average-product" collapse. Discover champion clusters/Pareto frontiers and maintain contextual applicability.
- Infer Latent Generator IR where enough outputs exist: map grammar, terrain/route/landmark placement, UI layout grammar, gameplay timing/difficulty, behavior distributions or other generator families.
- A repeated dataset-derived pattern may mature OBSERVATION -> HYPOTHESIS -> CROSS-VALIDATED PATTERN -> DESIGN LAW -> CONSTRUCTION HEURISTIC -> CERTIFIED TRANSFORMATION -> COMPILER PRIMITIVE.
- Dataset-derived maps can mine connectivity, distances, encounter frequency, spawn safety, sightlines, density and travel-time distributions and correlate them with quality/player behavior.

**Reconstruction-Derived Development (RDD):**
- Every reconstructed feature should become potential generative capital: mechanism/contract/interaction/timing/visual/audio/haptic/spatial/experience/proof/failure/procedure knowledge.
- Reconstruction should "pay twice": reproduce/understand the original target and return reusable development capital for future features.
- Create Feature Genome plus specialized Mechanism Genome, Experience Genome, Visual Genome, Interaction Genome, Quality Genome, Failure Genome and Proof Genome where evidence justifies them.
- Feature Homology discovers abstract reusable families even when surface implementations differ.
- Mechanism decomposition splits sensing/intent/gesture/mapping/assist/physics/feedback or equivalent domain layers so features can be recombined at meaningful seams.
- Reconstructed quality becomes a floor: new derived features cannot silently regress must-preserve dimensions.
- Parity-first, superiority-second: first close Reference Quality; only then claim improvement on explicit dimensions.
- "Superior" means a Pareto improvement or explicit tradeoff across defined dimensions plus human acceptance where subjective quality matters; complexity/feature count is not superiority.
- Quality Vector may include responsiveness, clarity, precision, accessibility, physical expressiveness, visual fidelity, feedback richness, stability, learnability, sociality, emotional warmth or domain-specific dimensions.
- Quality Dominance: candidate dominates a reference only if all must-preserve properties are equal/better and at least one allowed target dimension improves without violating compatibility/soul constraints.
- Add Quality Regression Firewall so new derived features cannot repeat known degraded latency, noise, frustration, lost warmth or other certified anti-patterns.

**Feature/Map families and synthesis:**
- Build Feature Families from homologous reconstructed mechanisms: physical swing, selection feedback, round-start ritual, family co-op, soft celebration, spatial discovery, ambient social presence or evidence-derived equivalents.
- Each family carries detector, applicability, parameters, quality envelope, exemplars, failures, proof and deopt.
- Build Map Genome: topology, landmarks, terrain, routes, spawn logic, resources, verticality, sightlines, rhythm, visual language and generator parameters.
- Cluster Map Families and Map Motifs such as central landmark, ring route, safe spawn pocket, risky shortcut, visual anchor, rejoin point, soft boundary and vertical reward when evidence supports them.
- Map Grammar Compiler takes desired experience and assembles known spatial motifs/families, then exposes only residual novelty.
- Feature Algebra / Recombination Compiler can compose certified mechanisms/families but must run Feature Composition Proof to catch incompatible assumptions in control, timing, camera, UI density, state ownership or feedback.
- Development Linker behaves like a library linker for behavior/quality capabilities: link only applicable families/ABIs and tree-shake unused ones.
- Feature E-Graph represents alternative architectures that satisfy the same Feature IR/Expectation set; Development Superoptimizer chooses non-dominated routes.
- Quality-Constrained Synthesis rejects candidates violating must-preserve expectations/quality/soul/performance/architecture before implementation.
- Maintain Pareto design frontier instead of one scalar "best".

**Quality DNA / reusable quality structures:**
- Extract Quality DNA: verified structural causes/conditions that support clarity, delight, precision, trust, warmth, accessibility or other quality dimensions.
- Reuse verified quality structures, not only code/functions/classes.
- Quality-carrying feature capabilities expose implementation contract + quality evidence + experience evidence + transfer conditions.
- Feature Capability ABI: preconditions, experience goal, functional/control/visual contracts, effects, quality envelope, adaptation points, proof, failure modes and deopt.

**Idea-Driven Development:**
- Idea Compiler transforms a raw idea into desired experience, actors/behaviors, implied systems, constraints, quality expectations, applicable Feature Families, unknowns and true novelty before coding.
- Idea decomposition distinguishes already-known, composable, adaptable, experiment-needed and genuinely novel obligations.
- Idea -> Existing Capability Alignment attempts reuse/extension before creating new systems.
- Idea Novelty Compiler outputs Genuine Novelty Frontier rather than a giant prose plan.
- Intent Genome preserves why the feature exists, who it serves, what moments matter and what must not happen.
- Ideas produce hypotheses rather than dogma; uncertain assumptions can be tested in cheap prototypes.
- Idea portfolio generation produces a small set of semantically distinct architectures, compared by emotional value, quality, reuse, cost, risk and Time-to-Ready.
- Novelty budget can deliberately keep most dimensions inherited while reserving selected dimensions for genuine innovation.

**Expectation-Driven Development:**
- Expectation is first-class even when user cannot specify implementation: "when X, I expect Y" becomes a contract.
- Expectation Compiler maps language to triggers, expected observations, tolerance, importance, authority and proof method.
- Expectation types include functional, behavioral, visual, performance, emotional, quality, compatibility, social, production and domain-specific classes.
- Build Expectation Graph / Acceptance Graph before completion. Feature cannot be certified while material expectations remain unproven or undispositioned.
- Infer candidate implicit expectations from tests/bugs/reference systems/history, but label them INFERRED_EXPECTATION rather than inventing user intent.
- Expectation Mining discovers recurring hidden contracts such as save compatibility, deterministic seeds, latency floors or familiar input semantics.
- Expectation Coverage tracks implementation/evidence/proof per relevant expectation.
- Expectation Gap = desired expectations - proven candidate behavior. Development compiles and closes the gap.
- Expectation Debt is visible when a feature works functionally but key quality/experience/production expectations are unproven.
- Expectation-driven debugging starts from violated expectation -> observable contract -> supporting mechanism -> changed evidence, narrowing causal search.
- If an expectation is not observable, Observability Compiler first creates a probe/measurement or keeps it explicitly subjective.
- Expectation hierarchy resolves tradeoffs. Detect conflicts such as maximum physical precision vs immediate family accessibility before implementation.
- Expectation equivalence permits different internal implementations to satisfy the same user contract, enabling cheaper/more robust routes.

**Additional derived-development inputs:**
- Behavior-Derived Development: infer control response, timing, player/AI behavior or difficulty shape from traces.
- Demonstration-Derived Development: human demonstration/video/controller traces can define desired behavioral/experience contracts, especially for WMOS/game-feel work.
- Failure-Derived Development: failures become negative design constraints and generative anti-patterns, not only debugging notes.
- Counterexample-Derived Development: good vs bad candidate differentials can reveal missing quality genes faster than more positive exemplars.
- Preference-Derived Development: repeated Owner choices may create scoped/confidence-weighted priors, never immutable assumptions.
- Outcome-Derived Development: shipped behavior/player outcomes feed the next generation.
- Experience-Derived Development: laughter, pauses, cooperative gestures, replay, delight and other human rituals may become scoped social/experience evidence when collectable and appropriate.
- Emotional Feature Genome may represent anticipation/tension/impact/celebration/social opening/reset calm or other evidenced experience arcs.
- Experience Homology discovers shared emotional architecture between mechanically different features.

**Feature ancestry and evolution:**
- Every feature records ancestry: donor families/genomes, dataset/image/reference inputs, idea lineage, expectation lineage, adaptations and novel obligations.
- Reuse contracts/patterns/capabilities/grammars rather than blindly copying implementation.
- Feature lineage/phylogeny lets successful branches become new champions and failed branches become negative knowledge.
- New features can rejuvenate old donor families if a new mechanism proves superior; improvement is bidirectional, not only inheritance downward.
- Every finished feature returns new dataset/eval evidence so Dataset-Derived Development improves continuously.
- Self-reinforcing loop: Reconstruction -> Feature Genome -> Derived Development -> New Feature -> Evidence/Dataset -> Better Grammar/Family -> Better future Derived Development.
- Quality Frontier is allowed to surpass retail/reference. Retail is a teacher and donor, not a permanent ceiling.
- Superior-quality certification requires explicit improved dimensions plus preserved must-have dimensions and human/experience acceptance where needed.
- Generational Quality Ratchet: each feature generation inherits best proven genes unless an explicit tradeoff is authorized.
- Development Theorem Mining promotes repeated cross-feature laws only after transfer/falsification. Negative knowledge is equally first-class.
- Quality causality should distinguish correlation from mechanism using experiments/challengers where feasible.

**Multi-source fusion / truth discipline:**
- Feature IR fields can be supported by multiple sources: image, dataset, reconstruction, runtime, idea, expectation, human demonstration or outcome.
- Authority is field-specific: visual reference may be authoritative for layout, runtime trace for physics, user for intended experience, usability evidence for human comfort.
- Feature truth lattice distinguishes OBSERVED, INFERRED, EXPECTED, DESIRED, HYPOTHESIZED, PROVEN, EXPERIENCE_ACCEPTED and INVALIDATED.
- Never confuse "we want", "retail does", "dataset correlates", "model infers" and "proof demonstrated".
- Preserve exemplar vs dataset distinction: population averages must not erase a high-quality exemplar without evidence.

**Readiness/economics integration:**
- Derived Readiness measures how much of a new Feature IR is already covered by certified ancestry.
- Inherited Readiness Ratio: percentage of feature obligations that are construction/proof-ready at birth through inherited capabilities/families.
- Development Distance: distance from new Feature IR to nearest certified combination of existing genomes/capabilities.
- Novelty Distance drives cognition; feature size does not.
- Quality Distance measures remaining gap to reference/target quality.
- Expectation Distance measures unclosed acceptance contracts.
- Conceptual Ready Distance = Novelty Gap + Knowledge Gap + Construction Gap + Quality Gap + Expectation Gap + Proof Gap + Reality Gap; Readiness Compiler attacks the dominant component.
- Before new feature design, applicable reconstructed/dataset/visual/institutional knowledge must be considered, but reuse may resolve as NOT_APPLICABLE. Do not force transfer.
- Preserve novelty reservation so derived development does not collapse into repetitive sameness. Inherit soul/quality mechanisms while allowing unique fantasy/mastery/signature symbols.
- Feature Birth Record: intent, expectations, ancestry, inherited families, quality targets, known risks, residual novelty and proof plan before implementation.
- Feature Birth Maturity measures how much verified development machinery exists at birth and should rise for recurring domains.
- Cold-birth benchmark: fresh worker with no transcript receives Feature Birth Record + Project Genome + current state; ability to produce a high-quality first slice measures institutionalization.
- Quality transfer tests verify whether a family proven in one feature retains quality under another phenotype; failed transfers narrow scope.
- Automatic donor selection ranks reconstructed features/families by semantic similarity, quality relevance, transfer compatibility and proof strength.
- Cross-game/cross-domain donor graph tracks successful transfers and rejected applicability.
- Reconstruction + dataset + image + idea + expectation fusion may be stronger than any single source; preserve independent provenance.
- Development Information Gain chooses cheap prototypes by uncertainty reduction / cost, not by polish.
- Fidelity ladder: CONCEPT -> GREYBOX -> STRUCTURAL -> BEHAVIORAL -> VISUAL -> INTEGRATED -> HARDWARE -> EXPERIENCE -> PRODUCTION, escalating only when previous layer justifies it.
- Minimum Sufficient Prototype resolves the largest unknown rather than maximizing appearance/completeness.

**Constitutional rules:**
- EVERY RECONSTRUCTED FEATURE MUST BECOME A POTENTIAL DONOR FOR FUTURE DEVELOPMENT.
- DEVELOPMENT SHOULD BEGIN FROM THE BEST VERIFIED APPLICABLE ANCESTRY, NOT A BLANK PAGE.
- RECONSTRUCTED QUALITY MUST BECOME REUSABLE DEVELOPMENT CAPITAL.
- DATASETS MUST PRODUCE GENERATIVE KNOWLEDGE AND BOUNDARIES, NOT ONLY RETRIEVABLE EXAMPLES.
- DATASET-DERIVED DEVELOPMENT MUST LEARN FROM QUALITY FRONTIERS/CHAMPIONS, NOT FORCE PRODUCTS TOWARD THE AVERAGE.
- AN IDEA DEFINES A POSSIBLE FUTURE; AN EXPECTATION DEFINES THE CONDITIONS UNDER WHICH THAT FUTURE COUNTS AS SUCCESS.
- EXPECTATIONS MUST EXIST BEFORE COMPLETION CAN BE CLAIMED.
- SUPERIOR QUALITY MEANS PRESERVING THE PROVEN QUALITY FLOOR WHILE ADVANCING EXPLICIT DIMENSIONS, NOT ADDING COMPLEXITY.
- A NEW FEATURE SHOULD PAY ONLY FOR THE DISTANCE BETWEEN WHAT THE INSTITUTION ALREADY KNOWS HOW TO CREATE AND WHAT IS GENUINELY NEW.
- THE ENDPOINT OF RECONSTRUCTION IS GENERATIVE UNDERSTANDING: KNOWING ENOUGH ABOUT WHY SOMETHING WORKS TO BUILD SOMETHING NEW THAT WORKS AT LEAST AS WELL.

**Done gate for activation:** one new feature/map/UI/sport created from mixed derived sources starts with measurable inherited readiness, reaches equal-or-better target quality/proof faster than the blank-page champion, and returns a reusable Feature/Quality/Procedure asset that lowers the cost of a subsequent related feature.

---

## D19 â€” Extreme Nuclear Endpoint: Generative Reconstruction Civilization / Feature Evolution Kernel

**State:** long-horizon constitutional direction combining D11â€“D18. This is not authorization to build a new monolithic subsystem.

**Why deferred:** the endpoint only becomes economically real after lower layers have produced proven Feature Genomes, Procedure Families, typed evidence, quality vectors, readiness telemetry and transfer benchmarks. Building the "civilization" before those specimens exist would be premature abstraction.

**Activation criterion:** D15â€“D18 have at least one successful canary each or equivalent evidence that the core abstractions are real. Then evaluate whether a thin universal Feature Evolution Kernel can replace repeated local implementations.

**Extreme target:**
- Reconstruction, development and quality improvement become one continuous compounding loop rather than separate disciplines.
- The institution maintains verified reusable genomes/families/quality structures/procedures/proofs/expectations and can synthesize new features by linking them under explicit intent and quality constraints.
- General intelligence is reserved for the residual novelty that cannot be derived, composed, transformed or proven through existing institutional machinery.
- Every expensive discovery must attempt to reduce the distance-to-ready of future work.
- Every expensive feature must attempt to increase the quality frontier or add a reusable capability; otherwise its learning return is incomplete.
- Reconstructed systems stop being dead-end archaeology and become parents in a generative ancestry graph.
- Product creation becomes evolutionary but proof-carrying: candidate -> shadow/greybox -> canary -> certified family/quality gene -> ratcheted donor, with explicit retirement/deprecation when superseded.
- Feature/Quality/Procedure genomes may evolve schemas as new evidence reveals missing dimensions; historical artifacts are re-indexed rather than frozen into obsolete representations.
- Build a Feature/Quality Market concept under Cognitive Economics: donor capabilities compete by applicability, quality, proof, adaptation cost, Time-to-Ready and future reuse. "Market" is an optimization abstraction, not necessarily a literal auction implementation.
- Quality inheritance is compositional but never assumed: Feature Composition Proof checks control/timing/state/camera/visual/social/experience compatibility.
- Keep separate what must be exact, what may be adapted and what is intentionally novel.
- Add a Novelty Reservation to protect unique identity so reuse does not produce homogenized derivative products.
- Preserve "Wii soul"/product essence as explicit high-level expectation/experience contracts where KSR applies; for other domains use domain-specific quality contracts.
- Build a Development Theorem / Anti-Theorem layer only after cross-feature/cross-domain transfer evidence. Theorems are executable guards/policies when possible, prose last.
- Feature synthesis can propose multiple Pareto candidates and surface only genuine tradeoffs to the Owner/human; routine decisions should compile away.
- New features may improve old features through rejuvenation if new evidence proves a superior mechanism; inheritance is bidirectional and versioned.
- Outcome/Evidence/Failure feeds back into Dataset-Derived Development, which improves family selection and generator reconstruction.
- Add Feature Evolution Regret: after outcome evidence, compare chosen ancestry/composition against best known ex-post route. Repeated regret becomes compiler/policy improvement.
- Add Quality Gene Attribution: identify which donor mechanism actually contributed to a quality improvement; avoid crediting decorative or incidental inheritance.
- Add Causal Quality Graph: when evidence allows, connect mechanism -> observable behavior -> expectation -> human/product quality, enabling safer transfer.
- Add Quality Counterfactuals: remove/substitute a donor mechanism in controlled prototypes to test whether the claimed quality contribution is causal.
- Add Quality Mutation Testing: deliberately perturb timing/layout/assist/feedback/flow and verify that quality or proof contracts detect meaningful regressions.
- Add Feature Robustness Envelope: certify where parameter changes preserve quality and where the family deopts to frontier design.
- Add Feature Family Specialization / Partial Evaluation: general family + known environment/intent/constraints -> specialized compact implementation/proof route.
- Add Feature JIT: novel design -> repeatable family -> compiled feature procedure -> certified transform -> architecture primitive -> continuous invariant where appropriate.
- Add Design Decision Extinction: recurrent design questions move from model judgment -> profile -> family rule -> compiler pass -> architectural invariant.
- Add Quality Decision Extinction: once a quality failure is causally understood and enforceable, prevent it mechanically instead of reminding future models.
- Add Generative Cold Birth: a fresh project/feature with no transcript inherits applicable Feature/Quality/Procedure maturity and can produce a high-quality first slice rapidly.
- Add Feature-Estate Elasticity: 100x more reconstructed features, datasets, proofs and incidents should not expand the active context of an equivalent feature task; it should improve donor selection and reduce cost.
- Add Quality-Frontier Elasticity: as the donor estate grows, selecting the best applicable quality structures should become more precise without proportional cognitive load.
- Add Ancestry Compression: a feature may have many historical ancestors but workers receive only the minimal live donor contracts/projections, not lineage narratives.
- Add Feature Semantic CSE: if multiple new features need the same derivation/donor adaptation, derive once and share by identity.
- Add Feature Singleflight: equivalent derived-development obligations coalesce unless deliberate independence is required.
- Add Generative Proof Reuse: quality/behavioral proofs remain valid under dependency envelopes and only affected closure reruns after adaptation.
- Add Experience Proof Reuse for KSR/social/physical features when hardware/input/environment dependencies remain stable.
- Add Donor Depreciation/Retirement: donors whose environment vanished, quality frontier was superseded or transfer performance degraded move out of active selection.
- Add Donor Fitness by Work/Feature Class and Provider Fitness for the cognition needed to close residual novelty.
- Add Derived Development PGO: learn best donor sets, context profiles, prototype modalities, proof recipes, adaptation costs and deopt patterns.
- Add Feature Amdahl profiling: after a major source of development time is removed, reprofile the remaining Time-to-Ready bottleneck instead of over-optimizing one layer forever.
- Add Development Roofline: classify new-feature work as ANCESTRY_BOUND, NOVELTY_BOUND, QUALITY_BOUND, PROOF_BOUND, ASSET_BOUND, ENVIRONMENT_BOUND, EXPERIENCE_BOUND or AUTHORITY_BOUND and allocate capital accordingly.
- Add Generative Readiness Compiler integration: ancestry/dataset/image/expectation processing should occur before expensive construction so feature births begin as close to READY as possible.
- Add autonomous opportunity detection: when repeated reconstructed features expose the same transferable mechanism or quality law, open a candidate Feature Family/Quality Gene for offline replay/benchmark rather than waiting for an Owner request.
- Add Development CAPEX discipline: build new general feature machinery only when lifetime avoided cost/quality gain across consumers exceeds construction/maintenance/risk.
- Add Anti-Goodhart constraints: quality cannot be optimized only through proxy metrics; hard functional/proof/reality constraints plus human experience evidence remain authoritative where required.
- Add cross-domain falsification matrix for feature/design theorems so one game's successful pattern does not become universal folklore.
- Preserve thin project adapters. Universal kernel owns state/dependency/evidence/proof/learning/selection; KME/KSR/game-specific semantics stay userland.
- Ultimate architecture:
  Input Evidence/Intent/Expectation
  -> Source Compiler
  -> Canonical Feature IR
  -> Feature/Quality Ancestry
  -> Novelty/Quality/Expectation/Proof/Reality Gap
  -> Readiness Compiler
  -> Feature E-Graph / Superoptimizer
  -> Construction/Experiment/Proof Compilers
  -> Transactional Intervention
  -> Production/Experience Reality
  -> Outcome Evidence
  -> Feature/Quality/Procedure Genome update
  -> ADCR/CBR promotion
  -> next feature starts closer to ready and at a higher quality floor.

**Extreme North Stars:**
- Reconstructed systems become generative parents, not archives.
- Institutional knowledge growth must reduce, not increase, active development context.
- Equivalent mastered feature creation gets cheaper with project age and donor-estate size.
- Time-to-Ready approaches only irreducible new-reality acquisition + genuine novelty + required proof.
- Quality floor ratchets upward generation by generation.
- General cognition concentrates almost exclusively on novel experience/mechanism design.
- A new feature pays only for what is genuinely new relative to verified applicable ancestry.
- Development, reconstruction and learning become one continuous proof-carrying evolutionary loop.

**Constitutional formulation:**
- EVERY REPEATED DESIGN DECISION MUST CREATE PRESSURE TOWARD A FEATURE FAMILY, QUALITY GENE, PROCEDURE OR ARCHITECTURAL INVARIANT.
- EVERY VERIFIED QUALITY MECHANISM MUST BECOME POTENTIALLY INHERITABLE UNDER AN EXPLICIT APPLICABILITY ENVELOPE.
- EVERY NEW FEATURE MUST BEGIN WITH THE BEST PROVEN APPLICABLE ANCESTRY AND AN EXPLICIT NOVELTY RESERVATION.
- EVERY CLAIM OF SUPERIOR QUALITY MUST NAME THE DIMENSIONS IMPROVED, THE DIMENSIONS PRESERVED AND THE EVIDENCE SUPPORTING BOTH.
- EVERY FEATURE MUST RETURN INSTITUTIONAL CAPITAL PROPORTIONAL TO ITS REUSE POTENTIAL.
- THE INSTITUTION SHOULD BECOME MORE CREATIVE, NOT MORE HOMOGENEOUS, AS ITS MEMORY GROWS: REUSE REMOVES KNOWN BURDEN SO NOVELTY CAN CONCENTRATE WHERE IDENTITY MATTERS.
- THE ENDPOINT IS NOT A SYSTEM THAT COPIES THE BEST EXISTING PRODUCTS. IT IS A SYSTEM THAT UNDERSTANDS ENOUGH OF THEIR CAUSAL QUALITY TO CREATE NEW PRODUCTS THAT PRESERVE WHAT MADE THEM EXCELLENT WHILE ADVANCING THE FRONTIER.

**Global done criterion:** this direction is validated only when a genuinely new feature with explicit novelty is produced faster from inherited evidence/feature families, meets or exceeds its declared quality floor and expectations, survives Production/Experience Reality, and measurably reduces the Time-to-Ready or raises the quality frontier for the next related feature.

---

## D20 â€” Sequencing guard for D15â€“D19

**State:** D15â€“D19 extend the existing D11â€“D14 reconstruction program. They are not five independent permission slips for new mega-systems.

**Why deferred:** building the endpoint before the measured primitives exist would create exactly the architectural/context/meta-work tax the programme is designed to eliminate.

**Activation order:**
1. Use current owners and Reality Scan. Reuse/extend/merge/connect before new system creation.
2. Prove one KME Software Reality / Construction canary from a repeated Work Class.
3. Prove one Visual Reconstruction canary where visual constraints materially reduce iteration.
4. Instrument Time-to-Ready and identify the actual critical blocker before adding broad readiness machinery.
5. Compile one mixed-source Feature IR (at least two source types) and measure inherited readiness / quality / proof.
6. Promote only the smallest mechanisms that produce measured cost, quality or TTR lift.
7. Only after repeated feature-family evidence exists, evaluate a thin Feature Evolution Kernel.
8. Every expansion must pass economic gate: lifetime avoided cost + quality/frontier value > build + maintenance + risk.
9. Every universalization must pass scope/transfer/falsification; KME/KSR remain reference workloads, not proof of universal truth by themselves.
10. Reprofile after each major improvement. If a new bottleneck dominates, stop optimizing the old one.

**Shared ownership target:** Universal Engineering Kernel owns identity/state/dependency/evidence/proof/effects/learning; REA supplies static/binary evidence where applicable; Universal Modder X supplies actuation/experimental reality; KME adapter supplies software-domain semantics; KSR adapter supplies cyber-physical/game semantics; ADCR learns procedures; CBR ratchets certified inheritance; Cognitive Economics/KEOS allocates capital; Mission/Readiness/Construction/Experiment/Proof compilers coordinate without becoming duplicated OSes.

**Final programme metric:** not number of frameworks, playbooks, genomes or datasets. The proof is whether a fresh future feature/reconstruction/change begins closer to READY, requires less raw evidence/context/general cognition, reaches equal-or-better quality faster, and leaves more reusable institutional capital than its predecessor.


---

## D21 â€” Wii Sports Tennis reconstruction with Wii Motion OS integrated (Owner, 2026-10-08) (was D11 on feature/knowledge-acquisition)

**Goal:** reconstruct the Tennis of Wii Sports from `E:\wbfs\Wii Sports + Wii Sports Resort [SP2P01]\SP2P01.wbfs`
(present, 1,549,795,328 bytes; the brackets in the folder name need `-LiteralPath` in PowerShell) into
`C:\Users\User\Desktop\Cursor Projects\Wii Projects\KobiiSports + KobiiSports Resort` (exists, EMPTY on 2026-10-08), so its
motion handling can be improved with Wii Motion OS integrated at source level.

**Known on 2026-10-08:**
- Wii Motion OS is a T3 spec plus 19 datasets (`KobiiSports Resort/_ksr_clean_repo/vault/specs/t3-wii-motion-os-compendium.md`,
  non-goal "implementation"), and `_ksr_clean_repo/tools/wmos_adapter` is at V0A. U1 (the injection substrate) is unresolved.
  With reconstructed source, motion code is changed in source, so the U1 study is not on this path.
- The recon factory is built for the Wii Sports Resort main.dol (34,159 functions). Wii Sports is a different executable,
  so it needs its own corpus, census, split and oracle-parity setup.
- Unknown and decisive: how Tennis's code is packaged (module vs main executable), its function count, and how many of
  its functions are shape-identical to already-solved Resort functions (shared engine and library families).

**Recommended scope:** a closure-scoped reconstruction, not a full matching rebuild. Reconstruct the motion closure
(Wiimote read, swing detection, racket and ball response), relink it with retail objects for everything else
(`relink.py` / `lcf2ld.py` exist in the decomp core), then integrate WMOS in that source. Validate in Dolphin on GEX44
(D7), then on hardware.

**Cost:** hypothesis until recon-factory CP50 measures the cost per function. See the Owner estimate of 2026-10-08 in
the gen3 session. Step 0 is zero-model: extract the disc, locate Tennis, count its functions, measure shape overlap
with the Resort census.

**Step 0 DONE 2026-10-08** (zero-model, `vault/plans/d11-tennis-step0.md`):
- Tennis is inside `files/EU/sys/sports/SportsPackEP.dol` (no RELs). DTK finds 14,885 functions.
- 63% of the DOL's functions have an exact shape match in the Resort factory split; only 23% of the Tennis candidate
  does (1,797 functions, an upper bound).
- The disc's Resort DOL is not the factory's binary.

**Step 1 DONE 2026-10-09** (zero-model, `vault/plans/d11-tennis-step1.md`):
- The novel closure inside the Tennis units is 1,323 functions, which agrees with step 0.
- Only 3 game functions call KPAD, and none of them is reachable from Tennis. Tennis gets motion through stored
  controller state (data), not through calls, so a call walk cannot size the motion closure.
- A DTK unit is not an SDK library: the 3,900-function SDK object made a first count meaningless. Libraries are now
  bounded by their version-string anchors.

**Step 2 DONE 2026-10-09** (zero-model probe, `vault/plans/d11-tennis-step2.md`):
- It corrected step 1: the 3 callers only call setters. KPADRead is inferred to be fn_800DB250.
- The read result lands in a per-channel controller object (~0xFB8 bytes), not in a global. The manager is published
  in SDA globals lbl_805133B8 and lbl_80513DF0.
- 51 Tennis functions (122 in the game) load the manager global directly, which is a floor. One-indirection field
  reads: Tennis 0. Inline reads through `this` are UNRESOLVED.

**Step 3 DONE 2026-10-09** (zero-model probe, `vault/plans/d11-tennis-step3.md`):
- Each controller is a 0xFC0-byte object at mgr+0x1C[ch]. The two getters are fn_800B7AD4 and fn_801DDEC8.
- Tennis has 50 getter callers. 20 of them read controller fields, mostly the raw buffer and low offsets. The derived
  state is read in 1. All of these are floors.
- Controls: positive met; negative 0/50.
Optional step 4: one level of argument propagation, then subtract the Resort-shape overlap.

**Activation criterion:** recon-factory CP50 has reported its cost per function and the learning-curve result (the
per-game cost model needs both). Step 0 may run earlier, because it is zero-model.

**TRF reforecast (2026-10-12, W8/W9):** the measured budget is `vault/plans/d21-tennis-token-budget-2026-10-11.md` (Scope A P50 103-122M tokens, hard authority ~380M in 25-function tranches, confidence LOW; Scope B P50 1,739-1,949M, confidence VERY LOW; every figure tagged M/D/H/U). **Scope-B admission: NOT YET** (curve slope UNKNOWN, 90.7 % model-needed, 0 verified Tennis functions, compiler flags unknown). Scope definition above is unchanged. Admit when a Tennis A/A passes, >=20 verified functions carry measured tokens, a >=3-member family curve falls, and a >=20-insn discriminator confirms the compiler. Programme handoff: `vault/programs/tennis-rf/HANDOFF.md` (written W9, 2026-10-12).

---

## D22 â€” cost-collapse / expected-completion admission: the rest of the mission (Owner, 2026-10-10) (was D12 on feature/knowledge-acquisition)

**Goal:** finish the expected-completion admission program (`vault/specs/expected-completion-admission.md`, APPROVED)
and continue cost-collapse T2 reconciliation -> T3-T7 (`vault/specs/cost-collapse.md`). Work tree
`C:\Users\User\Apps\pp-cost-collapse`, branch cost-collapse/main (local, never pushed). Binding plan:
`vault/plans/cost-collapse-convergence-plan.md` there (Owner y 2026-10-08; E3C is split into E3C1/E3C2; D-C = stop for an
Owner cap decision after E4b).

**Done (all in that work tree):** T1 f3b503e6, T2 2b5b0ea5, E1, E2, E3-A 3f2ff5c4, E3R (D3 flip 14879ab0 + RECEIPT-E3
8350d524: 45 calls / 7.62M vs 34 / 6M), E3G 0ea29fc7 (call checkpoint + receipt survives the stop), E4a work-tree half
42ac887c (LAUNCHABLE_VERDICTS / KNOWN_VERDICTS / verdict_unknown, V-VERDICT 14/14).

**Stopped where:**
- E4a live half: PARTIAL on the laptop (session guard). On 2026-10-09 the laptop had 0.7 GB free; the Owner moved the
  chain to GEX44 ("Todo en GEX44"). Handoff 067af7c2. WU-E4a2, mission m-16bde3ea1101 on GEX44, ended
  **BLOCKED_PREMISE** (receipt 44a2a6f3, fetched as `gex44/cost-collapse` in the work tree): GEX44's live install
  (`~/.claude/skills/claude-power-pack` @1872e9a1) has **no route admission at all** (no route_admission.py, no `admit`).
  Nothing was applied and nothing was armed. Any mission armed on GEX44 would launch ungated.
- Not started: E3C1, E3C2, E4b/E4 landing, T2 reconciliation, T3a/T3b, T4-T7. gsdx-pcc m-53847a002b65 stays held until T7.

**Loose state to settle first:**
- **This live tree carries uncommitted E4a edits** to `tools/route_admission.py` and `tools/gsd_mission.py`, plus untracked
  `tools/test_verdict_contract.py` (rollback tag `cc-e4a-pre`). The live sweep serves that code. Snapshot:
  `vault/plans/expected-completion-E4a-live.patch` in the work tree (sha256 6DD6ABC9...5129C1). Live gates there were
  admission 43/43, envelope 55/55, owner_hold 32/32, test_gsd_mission 226/227 (V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED,
  unattributed vs cc-e4a-pre), test_verdict_contract RED (no live envelope_fixture.py). Land or revert; do not leave it.
- Work tree: the E4a worker's uncommitted test edit is snapshotted as `vault/plans/expected-completion-E4a-worktree-test.patch`.
- GEX44: clone `/home/kobii/missions/cost-collapse`, tag `cc-e4a2-pre` on its live tree, mission m-16bde3ea1101 BLOCKED.
  GEX44 has no session_budget_guard.
- Open points: E2's EAC reforecast is inert live (the only call site, gsd_mission.py:2778, passes no usage) -> E3C2.
  On GEX44 `admit` printed expected=None safety=None: verify the UNKNOWN fail-closed path before trusting a GEX44 verdict.

**Remaining units, in order:** E4a live (WATCHED contract on the plane whose sweep runs the chain) -> E3C1 (guard latency
offset/high-water, E3G drills d2-d5 + d4 diagnosis, 4 unrun suites, slim-t2 borrowed g/calls_err) -> E3C2 (EAC usage
wiring, recalibration with the E3 pair, promotion Cognitive CI check, route-E4) -> E4b/E4 (land T1, T2, E1-E3C here with
a rollback tag, KV/UKDL/CBR ratchet) -> **D-C Owner cap decision** -> T2 reconciliation -> T3a/T3b -> T4-T7.
Packets: `vault/specs/packets/` in the work tree (WU-E3C1 is still to be written from WU-E4a section 3).

**Activation criterion:** the Owner picks a plane:
(a) laptop, once free RAM >= 4 GB: resume E4a's live half here (`RESUMPTION_FILE.md` E4a block in the work tree);
(b) GEX44: first a scoped unit that ports the E1-E3 admission stack + E4a contract to GEX44 live; or
(c) GEX44 with the sweep for cost-collapse run from the clone's tools instead of live.
Budget: goal `cost-collapse` cap 69,774,423 declared 2026-10-08. What the E-units spent against it is not summed here; read
it from the goal ledger, do not estimate.

**Update 2026-10-10 (pane 5d6a315c, measured):**
- The live-tree E4a edits are no longer loose. They landed as `16ac3a2d` "WU-E4a (live port)", with tag `cc-e4a-pre` kept.
  `tools/test_verdict_contract.py` is still untracked on live, and no canonical RECEIPT-E4a exists on the laptop (only `.partial.json`).
- GEX44 clone head is `c6bbad94` (receipt plus resumption note). `m-16bde3ea1101` is BLOCKED.
- All 8 laptop cost-collapse missions are HALTED (CC1, CC2, E1, E2, E3, E3R, E3G, E4a).
- Goal ledger: used 61,770,653 of 69,774,423, remaining 8,003,770
  (`mission_spend.py goal-status --goal cost-collapse`). T3-T7 at the old economics was about 43M, so D-C is certain.
- Option (a) now starts at closing E4a: commit the test, run the live gates and drill, write the receipt, then arm E3C1 without launching it.
  That launch is the WATCHED production canary.
- Debt: on 2026-10-08 the live sweep's adopt raised `MarkerError: resume command must start with '/'` (`m-302d70eabd59`).
- Cost rule: coordinator panes were 27.97M of 57.2M (49%). Resume from a fresh pane that arms and ends.

---

## D23 â€” EDD full-convergence mission: everything after P2-B-R (Owner, 2026-10-10) (was D12 on feature/knowledge-acquisition)

**Owner:** "put the rest of the mission in the backlog of claude power pack". Parked, not cancelled.

**Where it runs:** GEX44, worktree `/home/kobii/missions/edd/.claude/worktrees/edd-run` (branch `mission/edd-run`),
workstream `.planning/workstreams/edd`. The resume prompt there is `RESUMPTION_FILE.md`, and the plan with decisions
D-01..D-05 is `ROADMAP.md`. The execution log of record is `vault/specs/edd-compiled-execution-canary.md`.

**Sealed as of 2026-10-10:**
- **Heads:** edd-run `594a36c1`, GEX44 live PP `30fdbf0f`, laptop `72f4dcdf`.
- **Phase 1:** done, except criterion 4.
- **Phase 2, P2-B v1:** FREEZE because the H01/H02 keys were incomplete.
- **Phase 2, P2-B-R (gold repair):**
  - Holdouts v2 sealed at `95a47e80`.
  - The independent re-audit found H01, H02 and H07 all correct, with 0 leaks.
  - The judge returned FREEZE on cost only: the re-auditor's tokens were 38.4 % under forecast (5 calls against 7 forecast); the author was âˆ’17.6 %.
- **Built and live:**
  - The breaker meter attributes per session on GEX44.
  - Contamination scan: `edd_p2b.py scan`.
  - Gold lineage/reseal: `edd_p2b.py reseal`.
  - The arming guard refuses learnings marked "not built" without a disposition, which is the UC-19 effect path.

**Remaining, in order:**
1. **Estimator residual for P2-B-R-AUDIT.** Find which two steps the 5-call audit skipped, then correct the audit cost
   model. The Â±30 % rule requires this before the next unit is armed.
2. **Phase 1 criterion 4.** Write D-01..D-05 as DRK DecisionRecords (`modules/decision_review/decision_record.py`).
3. **P2-C, V-EDD-BENCH runner and BEFORE baseline:**
   - B0 is the deterministic pipeline (structural zero).
   - B1 is a model baseline, one isolated call per case.
   - Matches come from a blind scorer unit, and metrics are computed deterministically from them.
   - Packet, done-check and a frozen forecast are committed before arming. Arming goes only through `tools/edd_p2_chain.py`.
4. **Close Phase 2** (ceiling 16M), then re-forecast Phases 3â€“7 against what is left of the ~65M envelope (D-05).
5. **Phases 3â€“7 to Goal convergence.** Phase 3 includes the answer-leak transcript detector, which reuses `scan`. Close with the full handoff from the mission prompt.

**Open debt carried with it:**
- No push alert when the sweep is FAILING.
- UC-13: the generic `gsd_mission` arm is unbounded (PARTIAL, deferred to its owner).
- The iteration standard `Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` has not been read.
- Known reds stay explicit:
  - Laptop: V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED (`_auto_budget` refreshes `updated_at`).
  - GEX44: V-MC-PLAN-FACTS-REFUSES-OVERLAP (pre-existing).
- `m-e3ed7e14a5e2` stays untouched.

**Cost rule (D-05, binding):**
- Pane 24ca0218 coordinated 25.36M / 109 calls against a 2.0M forecast. Never coordinate from a long-context laptop pane.
- Use a fresh pane per phase. Measure its per-call cost (`mission_spend.session_tokens` on its own transcript) before
  budgeting, and hard-cap the coordinator per phase (1.0M for the rest of Phase 2).
- About 26M of the ~65M envelope is spent.

**Activation criterion:** the Owner says to resume EDD. Then, in a fresh pane, read the RESUMPTION_FILE on GEX44 and start at item 1. Never run `/gsd-autonomous --ws edd`.

---

## D24 â€” dgl durable goal / disposable lease: W3-W8 (Owner, 2026-10-10) (was D13 on feature/knowledge-acquisition)

**Owner:** "put the rest of the mission in the backlog of claude power pack" (pane 42ce1ae6). Parked, not cancelled.
(Was D13: two panes had both written a D12 the same day. Renumbered with the rest after merging main's D11-D20.)

**Where it lives:** worktree `C:\Users\User\Apps\pp-dgl`, branch `dgl/durable-goal-lease` (pushed to origin by the W1b
worker, unprompted). Plan: `vault/plans/durable-goal-lease-2026-10-09.md` (d0c2077b). Chain: `vault/programs/dgl/chain.json`
+ `CHAIN.md` (unit table, authoring rule). Goal `dgl`, cap 17.0M, chain envelope 16.0M.

**Sealed (head eaadf11f):**
- W1 PARTIAL (read-only, design recorded), W1b DONE: ledger lease epochs, programme, lease_open CAS + idempotent
  succession, lineage CLI; `tools/test_goal_lease.py` 10/10, 4 mutants killed.
- W2 DONE: `modules/provider_routing/workspace_registry.py` (generation CAS, fenced settle), registry-first binding
  precedence, cwd entry OBSERVE-only once the registry journal exists, closed-lease fence in the hooks;
  `tools/test_workspace_lease.py` 10/10, 4 mutants killed, regressions 0/0. Nothing installed live yet (that is W5).
- P3b-2 itself was run by main pane a5308810 (SRC PROVEN 294, P3B2_CHECK=PASS); see `vault/programs/dgl/D2-owner.md`.

**Stopped where:** the chain refused W3 on envelope (`used 11,154,078 + need 5,100,000 > 16,000,000`, tick log
`~/.claude/state/dgl-chain-tick.log`). Task `PP-DglChain-Tick` is **Disabled**. W3 packet + route are written and committed.

**Remaining, in order** (rows in CHAIN.md):
1. W3 â€” terminal reconciliation (TERMINAL_PROVEN vs UNKNOWN_RESERVED) + atomic succession `tools/goal_succession.py`.
2. W4 â€” predictive drain, SessionEnd wake, autopsy against binding records, crash matrix.
3. W5 â€” install to the live tree (DEPLOY class; never touch `tools/gsd_mission.py` / `tools/mission_steward.py` while
   ce-lifecycle-v3 has them dirty); re-point the tick to the live `tools/goal_chain.py`.
4. W6 â€” P3b self-host: lineage rf-p3b (L1, immutable) -> rf-p3b2 (L2); reconcile c2ae4b5c's hold by measured transcript.
5. W7 â€” VERIFY-ONLY of P3b-2 + lineage. 6. W8 â€” fresh-project canary, UKDL/CBR, retire the manual succession instructions.

**Gaps found live, owned by W3-W5:** a held/parked mission reads as "running" to the chain for ever; packet missions
without `done_check` stall on GSD NO_PHASES (bootstrap: `vault/programs/dgl/unit_done.py`, attached by the tick wrapper);
the tick borrows `gsdx_chain.py` from `Apps\pp-gsdx-factory-2`; W2 left no workspace-claim CLI (W6 needs one).

**Activation criterion:** the Owner raises the dgl budget. Units cost ~4-5M each (W1b 4.5M, W2 5.1M routes), so W3-W8 need
roughly 20-25M more against 4.85M left; a raise needs `--owner` on a TTY (`mission_spend.py`). Then `Enable-ScheduledTask
PP-DglChain-Tick`; the next tick arms W3. Read `vault/programs/dgl/RESUMPTION.md` in the worktree first.

---

## D25 â€” goal budget admission (A1 containment): the rest of the mission (Owner, 2026-10-10) (was D14 on feature/knowledge-acquisition)

**Goal:** the pre-call goal reservation that A1 lacked (`vault/specs/goal-budget-admission.md`, status done).
Evidence and every number below: `vault/programs/cognitive-economy/gen2/evidence/goal-admission/CANARY.md`.

**Done (branch feature/knowledge-acquisition, local, not pushed):** closeout fix 19240f98, final-reply headroom a3aaa515,
output margin ac6af297, unwritten issuing request ffd8f9e9; Owner "done" on live canary #6 (2,912,243 of a 3M cap,
two panes + Agents, one reply each after the deny) 8259a97e. Capsule debt closed 2026-10-10: renewal churn b15a1792,
hookreg StopIteration 182fc46b. Gates at close: GOAL_PASS=58/58, HOOKREG_PASS=16/16 --live, ADMIT 12/12, ROUTE 33/33.

**Remaining, in order:**
1. **GEX44 has no goal admission.** Per D22 (2026-10-09) GEX44's live install has no session_budget_guard; spend there is
   UNKNOWN and fails closed only for a goal that lists hosts. Not re-verified here. Owner of the port: A3 U4
   (`gen2/AMENDMENT-A3-2026-10-07.md`) / D22 option (b). Done = a GEX44 worker bound to a goal is admitted and settled in the
   laptop journal, and an unlisted host is refused.
2. **agent-solo-guard is machine-global.** `~/.claude/hooks/agent-solo-guard.js` keys its in-flight tracker on the host, so
   an Agent in one session blocks Agents in unrelated sessions for 30 s (canary #4: a worker blocked twice, ended its turn
   with a question, never reached the cap). Key it by session (or goal); it lives in `~/.claude` (HR-001: Owner step).
3. **V-SBG-LATENCY is load-sensitive.** `tools/test_session_budget_guard.py` asserts < 50 ms wall time; measured 13 ms to
   3,183 ms on identical code under host load. Make it judge CPU time or a median of N, so a red means the guard got slower.
4. **Residual reply margin (accepted).** A final reply can exceed its hold by a few hundred tokens (+187 in #6); the cap held
   only because leftover room absorbed it. Fix if a canary ever crosses: pad each final hold (~2%).
5. **The canary is not a recurring instrument.** `canary2.py` + `check3.py`/`check5.py` sit in the evidence folder. Promote to
   `tools/` (stagger, `final`-aware refusal detector) and decide a cadence. Each run costs ~3M processed: Owner decision.
6. **A1 itself is still ECONOMIC_CONTAINMENT** (A1 amendment: 42,307,381 / 20M, T3 + T7 frozen). A crossed cap is never
   raised: resuming means a new goal id the Owner declares. a1/u1 + a1/a1-2 are carried in `ce/a3*` and were never merged
   into `ce/gen2-completion`.
7. **AO phases 2-7 were paused "until pre-call budget admission exists"** (A1 amendment, AO exception). That condition is now
   met; they need a declared goal before they run.
8. **A1-6 (resume exam `next`).** Seen again 2026-10-10: `rollover.py certify` rejected an abbreviated first obligation and
   accepted only the capsule's verbatim text. Evidence for the A1-6 follow-up on next-action matching.

**Activation criterion:** item 1 when the Owner arms any unit on GEX44 (before arming, not after); item 2 when the Owner
approves a `~/.claude/hooks` diff; items 3-5 on any free PP slot (3 and 5 are zero-quota except 5's runs); items 6-7 when the
Owner declares the next goal for A1 or AO. Read CANARY.md's closing verdict first.

---

## D26 â€” GSD X Reconstruction Factory (gsdx-factory-2): the rest of the programme (Owner, 2026-10-10) (was D15 on feature/knowledge-acquisition)

**Goal:** finish the Master Plan v1 (`vault/plans/gsdx-factory-master-plan.md` in the work tree, Owner "y" 2026-10-09:
Part A + recon-factory through Phase 9, Full WSR excluded, envelope 40M / hard 55M inside the 100M ledger cap). Work
tree `C:\Users\User\Apps\pp-gsdx-factory-2`, branch gsdx-factory/v2 (local, never pushed). Goal `gsdx-factory-2`.

**Done:** S1 economics (55ced1e8 ledger settle_stopped/correct, 006c8b7b steward, RECEIPT-S1 DONE); L1 obligations
595 rows disposed, unknown 0 (DONE_WITH_LIMITS); PLAN-1; DOCTRINE (41 rows enforced, 8626dadc); W3 PARTIAL, accepted
because dgl took over what it left (0b05acb7); PLAN-2; AG2R (Part A rows 11/11, 99446b7c); W4 live re-forecast tool
(610808c5, forecast.json 239120ec); PLAN-3 (6cf33a0a). Deterministic chain tick `tools/gsdx_chain.py`, CHAIN_PASS=13/13,
scheduled task PP-GsdxChain-Tick (every 15 min). Spent 8,817,916 measured, open 0 (goal-status 2026-10-10).

**Parked (unarmed, `chain.json` â†’ `parked`):** AGMIN â†’ AGCAN â†’ AGECON â†’ AGDONE â†’ PLAN-4 (Part A G2..G5 + next planner).
Each also waits on `C:\Users\User\Apps\pp-dgl\vault\programs\dgl\W5-receipt.md` and ce-lifecycle-v3 WU-INST2.

**Not in the chain yet:** W5 GEX44 control-plane port (DEPLOY class: read the hard rules first; also resolves
cost-collapse E4a2 as option (a), see D22 cost-collapse); W6 rows not mapped to a phase; W8 closeout = promote KNOWLEDGE
K1-K7 (`vault/specs/gsdx-factory/KNOWLEDGE.md`) to UKDL/CBR; Part B; Production Reality. Recon-factory phases are
the Owner's CP50 track (C1 re-armed as m-4e2364edc538, goal cp50-c1b, in wt_cp50_c1); they are not gsdx units.

**Forecast (W4, forecast.json):** remaining 12.7M expected / 5.1M lower / 22.1M safety; total 21.4M expected, inside 40M.

**Open debt carried with it:**
- K7: live admission (ce-lifecycle-v3 L3) charges growth per tool call, so it over-prices ~2.8x. Routes are written
  in declared steps to fit; the fix belongs to ce-lifecycle-v3.
- K6: the supervisor still renews a worker whose receipt is not exactly DONE (91K and 98K wasted renewals). The chain
  side is fixed (5e835a8a); the packet template and supervisor side belong to ce-lifecycle-v3.
- Holds kept as UNKNOWN: old goal 530d9700 232,321; cp50-c1 150,000 (seq 6, old C1 session c021de1c).

**Activation criterion:** the Owner says to resume gsdx-factory. Then, in a fresh pane (never this long one), move the
`parked` units back into `units` in order, read RESUMPTION_FILE.md in the work tree, and let the chain tick arm them.
Before W5, run `hardrule_compile.py --class DEPLOY`.


---

## D27 â€” REA Wii/PPC Enablement Program: REA as Evidence Plane under the Recon Factory (Owner, 2026-10-11)

**Origin:** TRF W4 (`vault/programs/tennis-rf/REA-DISPOSITION.md`) returned REJECT for native PPC on rea-agents 6.3.0
(`rea --help` hangs > 45 s importing `dist/cli.js` on Win11/Node 24.15; no DOL / ELF32-PPC lane in `dist/`). Owner
direction: the REJECT is a **capability gap with a certification path**, not "REA discarded", and not "patch REA for
50M before Tennis". HR-NOVELTY-001 class: EXTEND_EXISTING_OWNER (cpx R6 evidence dossier + TRF W4 disposition).

**Boundary.** Upstream in REA: CLI bootstrap reliability, provider lifecycle and process ownership, DOL + PPC BE target
support, generic Ghidra target admission, deterministic native evidence, bounded function dossiers, snapshots/cache,
target readiness, bounded agent projections, diagnostics. Stays in CPP: Binary Semantic Genome, family clustering,
semantic novelty, cross-game theorem transfer, compiler inversion, Function Family Compiler, Proof of Model Necessity,
information-gain scheduler, Cognitive P&L, learning curves, model routing, CBR, Tennis economics.

**Units (each a bounded packet; stop at the first conclusive answer):**
- P0 Revalidation: pin the CURRENT upstream release (claimed 6.4.0 on main 2026-10-11, UNVERIFIED here: read
  `server.json` and the release tag first). Re-run the W4 hang probe. Hang gone -> P1 shrinks to a regression gate.
- P1 CLI cold-start contract: a non-analysis command (help/version/capabilities) must not load an analysis provider;
  startup budget per OS/Node as a permanent verification lane (upstream PR candidate).
- P2 Target Readiness Certificate (generic; also CPP-side for every tool): REA version -> CLI bootstrap -> provider
  health -> format -> architecture -> endianness -> loader -> profile -> required operations -> fixture check. Verdicts
  SUPPORTED / PARTIAL / UNSUPPORTED / BROKEN_ENVIRONMENT / BROKEN_REA. Host capability (OS, JDK, Ghidra, process
  ownership) separate from target capability (format, arch, endian, loader, operations). An unsupported target fails in
  milliseconds with UNSUPPORTED_TARGET + format/arch/provider/missing capability/remediation, never a hang.
  Rule: TOOL INSTALLED != CAPABILITY AVAILABLE FOR THE CURRENT WORK CLASS.
- P3 DOL + PPC BE Ghidra lane, controlled fixture first, then SportsPackEP.dol. Proves DOL identity/hash, sections and
  offsets, load addresses, BSS, entry point, PowerPC:BE:32 (Gekko) language/profile, file-offset <-> memory mapping,
  function/address identity, headless reproducibility. Rule: PROVIDER READY != TARGET CORRECTLY LOADED.
- P4 Evidence conformance vs DTK + m2c + Ghidra (instrumental truth): calls/branches, register/data refs, SDA (r2/r13),
  globals, constants, xrefs, call graph, load addresses. Surface decided against our corpus, not a prompt.
- P5 Bounded function dossier, same contract as cpx R6 (upstream-compatible). Rule: every native evidence producer has
  a bounded agent-facing projection.
- P6 Bulk + cache: analyse once -> compact global index -> dossiers projected on demand; content-addressed key = binary
  hash + provider version + loader/profile + operation + params + evidence version; same inputs -> zero analysis, zero
  model. Performance contract in CI: cold start, provider discovery, cached and uncached dossier, snapshot hit, provider
  startup, evidence bytes, projection size.
- P7 Tennis canary on draw 1-5: REA dossier vs CPP R6 dossier, same outputs/evidence, measured EVC.

**Gate (Technical Capital Allocator):** USE_REA for Tennis only if P7 shows lower Expected Verified Cost than the R6
evidence plane; until then KEEP_CPP + EXTEND_UPSTREAM. D21 never waits on this programme. Price P0-P7 CAPEX against
savings over Tennis and future Wii games once R6 and C3 measure what the dossier already buys; if R6 gives ~95% of the
value, REA improves upstream without blocking anything. File the upstream PPC/DOL issue (draft in REA-DISPOSITION.md)
once P0 confirms the gap on the current release; keep the adapter/patch clean enough to contribute.

**Activation criterion:** cpx R6 receipt DONE plus the C3 two-arm result; P0 may run earlier (zero-model, small).
Decision owner: cpx R5 admission table (plan `cpx-control-plane-extinction-cp50-2026-10-11.md` section 9).
## D28 -- Tennis Frontier Collapse + global corrections (Owner, 2026-10-12) (QUEUED, awaiting one-click approval)

**Owner:** "before continuing add this to the queue and implement it as a global optimization (for CCR too)" + the
`/cpp-gsd-long` Frontier Collapse prompt (pane TRF-C). Supersedes the narrow W12a -> W12R -> W13 sequence.

**Plan (approval surface):** `vault/plans/tennis-frontier-collapse-2026-10-12.md` (Reality Delta Scan, root-cause matrix,
owner map, Ph0-Ph11, 27 master done-gates, budget P50 25.5M / P80 31M / P95 38M, GEX44 job 4 + 5-6).

**Global pieces (all goals, CCR included):** (1) authoritative result = ledger, worker prose = claim, typed
CLAIM_EVIDENCE_DIVERGENCE; (2) automatic successor lease inside Programme Authority (connects `ledger.lease_open`;
overlaps D24 dgl W3 -- implement once, D24 W3 consumes it); (3) deterministic-first gate (WU class + launcher-run `pre`
steps before model admission; connects CCR Work-Class/PoCN); (4) frontier-collapse-before-leaf-execution as CBR after proof.

**Activation:** Owner approves the plan's section 8 in one reply. TRF-C then opens tennis-rf L2 (8M tranche) and starts Ph0.

**Separate debt found while running it (Owner, 2026-10-13: register, do not block D5):**
- D28-DEBT-1, multi-lease `halt_authority` ungated. cf24e4af stopped `tools/gsd_mission.py halt_authority` counting
  an open hold twice; its gate `V-LIFE-HALT-OPEN-COUNTED-ONCE` covers one lease only. The case that actually failed
  (a leaked hold in a CLOSED lease must not reduce a NEW lease's authority, while the programme's `executable` still
  counts it) has no gate. Close with a test that opens a programme, leaks a hold in L1, opens L2, and asserts
  halt_authority == L2 cap and executable == programme - settled - open. No longer contaminating the ledger: the
  three leaked holds (1,130,211) were settled from their transcripts 2026-10-13 (capped at mark + hold, total_used
  unchanged at 79,053,296, open 0).
- D28-DEBT-2, owner hold vs launch race. `gsd_mission.py hold` on a PREPARED mission (m-13e710106e99, 14:40) did not
  stop its launch: it reached epoch 1, spent ~144k and halted "owner hold, owner DEAD". Either the launch had already
  claimed it or the launcher does not re-read the hold. Reproduce before fixing.
- D28-DEBT-3, a renewal does not count as a residual. m-13e710106e99 was a renewal (`renewed_from`), so the chain
  armed one more residual (m-f3fa70353c8e, route L, need 6.4M) for a unit the Owner had just decided to close.
  Halted before launch.
- D28-DEBT-4, D1c limits 1-2 (carried to D11): DETERMINISTIC_USED_MODEL not fed the ledger's per-unit model-call
  count; the `.pre.json` path is not put in the worker's card.
- D28-DEBT-5, a unit whose route is not in `route_ladder` never climbs (`tools/gsdx_chain.py:99`, idx None keeps
  the route): D8 on gate-only route-G (4 calls) stopped twice on the same call breaker, 0.41M for nothing; the
  third attempt would have been identical. Workaround: D8v2 on route-M, D9 on route-S. Proposed gate: a residual
  whose route is off the ladder goes to `human_gate` on the FIRST repeat, and a chain lint refuses a unit whose
  packet has post-gate work on a gate route.