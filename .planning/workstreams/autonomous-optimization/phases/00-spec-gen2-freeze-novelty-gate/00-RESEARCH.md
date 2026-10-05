# Phase 0: Spec, gen2 freeze, novelty gate - Research

**Researched:** 2026-10-05
**Domain:** programme pre-registration on an existing verifier stack (Python V-gates, git-pinned JSON ledgers, SDD-OS spec gate, HR-NOVELTY-001, a read-only env preflight)
**Confidence:** HIGH (every discrete value below was read from the source file this session; every command marked MEASURED was run this session in this worktree on GEX44, git 2.43.0, Python 3.12.3)
**Run plane:** gex44 (`/home/kobii/missions/autonomous-optimization/.claude/worktrees/ao-gen2`, HEAD `79f71693b2699c84deb62599e9af64d5b0ef2e45`)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Locked by the approved plan (vault/plans/autonomous-optimization-2026-10-05.md):
- New pillars live in an IC gen2 ledger (skill-capability/gen2 precedent); gen1 `frozen` object is immutable.
- EXTEND before NEW: no new OS / runtime / DB / scheduler / ratchet.
- Never edit: CE/SC/IC-gen1 ledgers' `frozen` objects, `tools/test_cognitive_economy_program.py`, `tools/test_skill_capability_program.py`, root `.planning/STATE.md`. `tools/gsd_mission.py` out of scope.
- Commits: explicit pathspec, one falsifiable increment each; verify `git log -1 --format=%s`.
- Laptop-only work -> one `[<P>]` line in `vault/programs/incremental-cognition/gen2/owner-bundle.md`.
- Every phase commits EVIDENCE.md (Product Delta + Intelligence Delta) and its ledger rows.
- UNKNOWN / INCONCLUSIVE / UNMEASURED are never PASS.

### Claude's Discretion
All other implementation choices: follow repo conventions (skill-capability gen2 ledger shape, IC gen1 ledger, existing V-gate test style).

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AO-01 | ownership reconciled; no parallel OS/runtime/DB/ratchet (gate 1-2) | Section "Novelty gate" (how `check_novelty_gate` works, why it returns `applies=False` for this programme, the 13-question record convention, discovered-sweep anchors) + Section "Spec" (T3 spec shape and `covers:` tie hazard) |
| AO-02 | executable optimization contract + gen2 ledger (gate 3, 6) | Section "gen2 ledger + FROZEN_AT + wrapper" (CE verifier rebinding, measured prototype, FROZEN_AT two-commit freeze, mutant-per-rule table) + Section "Opportunity row" + Section "Preflight instrument fix" (first row) |
</phase_requirements>

## Summary

Phase 0 is pre-registration work on top of an already-built verifier stack, and the stack is reusable without editing any frozen file. The IC done-gate (`tools/test_incremental_cognition_program.py`) is a thin wrapper that rebinds module globals of the CE verifier and calls CE's `check_ledger`. The same trick, applied inside a context manager with `PILLARS = [M,O,P,Q,R]` and the gen2 paths, makes CE's L1-L9 clauses judge a gen2 ledger. This was prototyped this session (see Pattern 1): status mode returned `[]`, final mode returned exactly L2 (no FROZEN_AT), L3 x5 (no terminals), L8 x4 (no reviews/deltas), and the global bindings were restored afterwards.

Five facts the planner must not assume away. (1) **There is no pillar-shaped gen2 ledger precedent.** `vault/programs/skill-capability/gen2/` holds only prose files (no `ledger.json`, no `FROZEN_AT`); the only gen2 ledger in the repo is `vault/programs/cognitive-economy/gen2/ledger.json`, which has a different shape (`work_units`, no `frozen`) and its own verifier `tools/cep_gen2.py`. The gen2 ledger for this programme must therefore copy the **gen1 IC shape** (`frozen.pillars`, `state`, `reviews`, `deltas`) with its own `FROZEN_AT`, and the `--generation 2` CLI flag convention from CE (`tools/test_cognitive_economy_program.py` main). (2) **`check_novelty_gate` is advisory and keyword-triggered**: it returns `applies=False` for the plan text and the ROADMAP (MEASURED), it has no CLI of its own, no classification output and no record file; the "recorded novelty check" is a prose audit file with 13 file:line answers plus the keyword result and a positive control. (3) **The preflight bug is reproduced here**: `python3 tools/gex44_env_preflight.py --current --checks pp_install` prints `floor 5962571c is not in this install's history (head 79f71693)` and exits 1 (MEASURED), because the floor commit object is **absent** from this repository (`git cat-file -t 5962571c` -> `fatal: Not a valid object name`), while the pick `25a10ce5` exists and carries `(cherry picked from commit 5962571c840943ae0a3aa901efb08e69a04434da)`. With the floor object absent, a patch-id comparison against the floor is impossible; the trailer path is the operative fix on GEX44. (4) **The existing preflight suite is already red in this plane**: `ENVPF_PASS=55/57` (V-ENVPF-PP-REAL-READY and V-ENVPF-PP-STALE-REAL fail), and `--drill` reports `FAIL DRILL-CONTROL` with M3 "KILLED" only because its target gate was already red (a false kill). (5) **`python3 tools/test_incremental_cognition_program.py --final` is red today** for reasons outside this programme (gen1 pillars A,B,C,I,J,K,M,N have no terminal; L8 reviews/deltas empty): `CEP_VERDICT=FAIL failures=12` (MEASURED). "Done-gate exit 0" in ROADMAP Phase 7 is unreachable unless gen1 closes or the done-gate is defined as gen2-only; the planner must surface this, not hide it.

**Primary recommendation:** Build `tools/ic_gen2.py` (gen2 judge: rebinding context manager + pre-registration rules + own selftest with one mutant per rule) wired into the IC wrapper as `--generation 2 [--status|--selftest|--final]` and into the wrapper's `--final`/`--selftest`; fix the preflight with three accept paths (ancestry OR exact `(cherry picked from commit <floor>)` trailer OR equal `git patch-id --stable`) red-test-first against hermetic fixtures (never against the live clone); write the spec with `covers:` entries that do not tie with the plan's; freeze in two commits (ledger, then `FROZEN_AT`).

## Architectural Responsibility Map

(No browser/SSR tiers apply; the tiers here are the repo's real ones.)

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pre-registration (pillars, predicted terminals, rules, champion numbers) | `vault/programs/incremental-cognition/gen2/ledger.json` (`frozen` object, git-pinned) | `FROZEN_AT` (commit sha) | `frozen` is compared to its copy at that commit (CE L2); the ledger is the only place the verifier reads |
| Judging gen2 | `tools/ic_gen2.py` (new, lazy-imported, like `tools/cep_gen2.py`) | `tools/test_incremental_cognition_program.py` (dispatch only) | keeps the IC wrapper diff small; CE file never edited |
| Spec authority | `vault/specs/autonomous-optimization.md` (SDD-OS front matter) | `modules/sdd_os/readiness.py` + `spec_binding.py` (judges, read-only) | readiness/binding are the existing gate; no new spec tool |
| Novelty record | `vault/audits/` prose record (HR-NOVELTY-001 convention) | `modules/spec_gate/gate.py::check_novelty_gate` (keyword advisory) | the gate only emits questions; evidence is the audit file |
| Preflight fix | `tools/gex44_env_preflight.py::check_pp_install` | `tools/test_gex44_env_preflight.py` (V-ENVPF-*, `--drill`) | pillar-B instrument; consumed by `tools/mission_launch_gate.py` |
| Opportunity row (first) | gen2 `ledger.json` top-level `opportunities` (git-tracked) | CO-12 `record_signal` (optional, untracked state dir) | CO-12 rows live under `~/.claude/state/co12_readiness/` (not in git) and cannot be the durable record |
| Champion evidence | `vault/programs/incremental-cognition/gen2/evidence/` copies with sha256 | GEX44 `/home/kobii/missions/zero-rescan-out*` (host-local, outside git) | the raw summaries are outside the repo and ephemeral; freezing means copying them in |

## Standard Stack

No external packages. All work is stdlib Python 3.12.3 + git 2.43.0 + existing repo modules. [VERIFIED: `python3 --version` -> `Python 3.12.3`; `git --version` -> `git version 2.43.0`, run this session]

### Core (existing in-repo owners to EXTEND)
| Component | Path | Purpose |
|-----------|------|---------|
| CE verifier (reused by rebinding, never edited) | `tools/test_cognitive_economy_program.py` | `check_ledger` L1-L9, `check_disposition` X1-X3, `Resolver` |
| IC wrapper (extend dispatch only) | `tools/test_incremental_cognition_program.py` | `--final/--status/--pillar/--selftest`, R2-R4, B1 |
| gen2 judge (new file) | `tools/ic_gen2.py` | precedent: `tools/cep_gen2.py` (CE gen2, lazy import from CE `main`) |
| Spec judges | `modules/sdd_os/readiness.py`, `modules/sdd_os/spec_binding.py` | readiness + `covers:` binding |
| Novelty gate | `modules/spec_gate/gate.py` | 13 questions + keyword trigger |
| Preflight | `tools/gex44_env_preflight.py` + `tools/test_gex44_env_preflight.py` | `check_pp_install` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `tools/ic_gen2.py` | Inline gen2 code in the IC wrapper | The wrapper is already 1,338 lines; CE's own precedent (`tools/cep_gen2.py`, 40+ lines of docstring contract, lazy-imported) keeps gen2 isolated and independently testable |
| `git cherry` | `git patch-id --stable` over `git show` / `git log -p` | Same answer on the MEASURED fixtures (below); the roadmap names `--stable`, so implement with `patch-id --stable` and keep `git cherry` as a cross-check only (equivalence for non-trivial diffs is `[ASSUMED]`) |

**Package legitimacy:** no external packages are installed by this phase. Package Legitimacy Audit: none required. [VERIFIED: phase scope reads only stdlib + repo files]

## Architecture Patterns

### System Architecture Diagram

```
 plan of record ──► spec (vault/specs/autonomous-optimization.md, T3, covers/readiness front matter)
        │                    │ judged by modules/sdd_os/readiness.assess(.., 3) + spec_binding.find_bound_spec
        ▼                    ▼
 novelty record  ◄── check_novelty_gate(proposal text) -> applies? + 13 questions ──► audit file (13 x path:line "quote")
        │ classification EXTEND_EXISTING_OWNER (else slice STOPS)
        ▼
 champion evidence: /home/kobii/missions/zero-rescan-out{,2}/summary.txt + r4-population.log + gex44_ic_rows.sh
        │ copied into gen2/evidence/champion/ with sha256
        ▼
 gen2/ledger.json  (frozen: pillars M,O,P,Q,R + champion + denominators; state {} ; opportunities [OPP-001])
        │ commit A (pre-registration)  ──►  commit B writes gen2/FROZEN_AT = sha(A)
        ▼
 python3 tools/test_incremental_cognition_program.py --generation 2 {--status|--selftest|--final}
        │ ic_gen2: bind ce globals -> ce.check_ledger(...) -> restore  (+ G2 rules: gen1-frozen pin, champion, owners, spec link)
        ▼
 preflight fix (independent branch of work):
   check_pp_install: accepted = ancestor(floor,HEAD) OR trailer "(cherry picked from commit <floor>)" OR equal patch-id
        │ red tests first (hermetic temp repos) ─► green ─► OPP-001 row cites the fix commit
```

### Recommended file layout (all new files are additive)
```
vault/specs/autonomous-optimization.md                       # T3 spec
vault/audits/autonomous-optimization-novelty-2026-10-05.md   # 13-question record (HR-NOVELTY-001 convention)
vault/programs/incremental-cognition/gen2/
├── ledger.json            # pillars M,O,P,Q,R frozen + state + opportunities
├── FROZEN_AT              # written in a SECOND commit
├── owner-bundle.md        # [<P>] lines (laptop-only items)
├── evidence/champion/     # run5-summary.txt, run6-summary.txt, run5-population.log, gex44_ic_rows.sh (+ sha256 in ledger)
├── evidence/OPP-001-pp-install-hash-floor.md
└── handoffs/              # CE handoff_landed needs commits AFTER FROZEN_AT
tools/ic_gen2.py                 # gen2 judge + selftest
tools/test_ao_p0.py              # spec / novelty / champion V-gates (optional: can live in ic_gen2 selftest)
.planning/workstreams/autonomous-optimization/phases/00-.../EVIDENCE.md   # Product Delta + Intelligence Delta
```

### Pattern 1: judge a second ledger by rebinding CE globals (MEASURED prototype)
**What:** CE clauses read module globals at call time (`PILLARS`, `LEDGER_REL`, `FROZEN_AT_REL`, `HANDOFF_DIR`, `REQS_REL`, `REQ_ROW`). The IC wrapper already relies on this (`tools/test_incremental_cognition_program.py:84-93`: `ce.LEDGER_REL = PROGRAM_DIR + "ledger.json"`, `ce.FROZEN_AT_REL = PROGRAM_DIR + "FROZEN_AT"`, `ce.PILLARS = [chr(c) for c in range(ord("A"), ord("N") + 1)]`).
**Prototype run this session** (`/tmp/gen2proto.py`, scratch, not in repo) with `ce.PILLARS=["M","O","P","Q","R"]`, `ce.LEDGER_REL="vault/programs/incremental-cognition/gen2/ledger.json"`, `ce.FROZEN_AT_REL="vault/programs/incremental-cognition/gen2/FROZEN_AT"`, `ce.HANDOFF_DIR="vault/programs/incremental-cognition/gen2/handoffs/"`:
```
status mode (final=False): []
final mode: ['L2 not frozen: FROZEN_AT missing, the pre-registration was never committed', 'L3 M: no terminal disposition', ... 'L3 R: no terminal disposition', 'L8 review ukdl: missing or its file does not exist', 'L8 review cbr: ...', 'L8 delta product: empty', 'L8 delta intelligence: empty']
extra pillar: ["L1 frozen pillars must be exactly A-T in order, got ['M', 'O', 'P', 'Q', 'R', 'S']"]
restored: ['A', 'B', 'C'] vault/programs/incremental-cognition/ledger.json
```
[VERIFIED: ran this session]
**How to apply:** `ic_gen2.bound()` as a `contextlib.contextmanager` with `try/finally` restore. A leaked binding is caught by the wrapper's own B1 clause (`check_binding`, `tools/test_incremental_cognition_program.py:201-211`, mutants at `:824-837`), so add a gen2 gate that asserts the globals equal the gen1 values after a gen2 run (V-IC2-BINDING-RESTORED).
**CE's own selftest cannot run under the gen2 binding**: `_clean_fixture()` reads `REPO / LEDGER_REL` and indexes `state["A"]`, `pillars[4]`, `pillars[7]` etc. (`tools/test_cognitive_economy_program.py:500-515`, `:559-585`). The gen2 selftest must therefore be its own (fixtures built from the gen2 ledger shape), exactly as `cep_gen2.py` has its own `selftest`. Never run CE's selftest inside the context manager.

### Pattern 2: FROZEN_AT is a commit sha, frozen in two commits
[VERIFIED: `tools/test_cognitive_economy_program.py` `Resolver.frozen_at_commit` reads `FROZEN_AT_REL`, takes the stripped text as `sha`, runs `git show {sha}:{LEDGER_REL}` and returns `json.loads(r.stdout)["frozen"]`; `check_ledger` L2 compares `json.dumps(ref, sort_keys=True)` with the current `frozen`]. Contents of the live files, verbatim: IC `vault/programs/incremental-cognition/FROZEN_AT` = `18e928af8c489f9d29dd1e76e0c7aa3c6a6975eb`; SC `vault/programs/skill-capability/FROZEN_AT` = `217d72b5944a664fbc0baa1060c04617ff10f481`.
- It is **not** a hash of file content. It names the pre-registration commit; the check is "`frozen` now == `frozen` at that commit". Only `frozen` is pinned: `state`, `reviews`, `deltas` and any new top-level key (e.g. `opportunities`) may change after the freeze.
- A commit cannot contain its own sha, so the precedent is two commits: `18e928af feat(incremental-cognition): P0 freeze -- ledger A-N, KME denominators, wrapper done-gate, phase-4 audit` then `d4d35059 chore(incremental-cognition): FROZEN_AT = 18e928af (pre-registration commit)` (the second touches only `FROZEN_AT`, 1 insertion). SC did the same: `217d72b5` then `28b27367 feat(skill-capability): FROZEN_AT -> 217d72b5 (pre-registration sealed)`. [VERIFIED: `git show --stat` this session]
- Consequence for planning: everything that belongs in `frozen` (pillars, rules, champion numbers, denominators, the cited spec path) must be final and reviewed **before** commit A. After A, a typo in `frozen` can only be fixed by a new generation (CE L2 fails on any edit; V-CEP-MUT-frozen-edited).
- `Resolver.handoff_landed` (used by MERGED/DEFERRED terminals) requires a handoff commit that is **not** an ancestor of the freeze commit, so gen2 handoffs must land after commit A. They must live under `ce.HANDOFF_DIR` (`vault/programs/incremental-cognition/gen2/handoffs/`) and name `[<pillar>]` and one frozen owner path.

### Pattern 3: gen2 ledger shape (copy IC gen1, not CE gen2)
IC gen1 top-level keys, read this session: `['schema', 'program', 'plan', 'terminal_vocabulary', 'frozen', 'state', 'reviews', 'deltas']`; `schema` = `"cognitive-program-ledger/1 (verifier: tools/test_cognitive_economy_program.py via tools/test_incremental_cognition_program.py)"`, `program` = `"incremental-cognition"`, `plan` = `"vault/plans/incremental-cognition-program-2026-10-03.md"`, `terminal_vocabulary` = `['IMPLEMENTED_AND_VERIFIED', 'MERGED_INTO_EXISTING_OWNER', 'FALSIFIED_OR_REJECTED_BY_EVIDENCE', 'DEFERRED_STRONGER_OWNER', 'AUTHORIZATION_BOUND', 'EXTERNAL_BLOCKED', 'RESEARCH_INSUFFICIENT_EVIDENCE']`; `frozen` keys `['frozen_note', 'materiality', 'denominators', 'consumes', 'pillars']`; each pillar `{id, name, owner[], predicted, rule}`; `state` = `{<id>: {}}` until closed, then `{terminal, reason, evidence[], savings[]}`; `reviews` = `{'ukdl': None, 'cbr': None}`; `deltas` = `{'product': [], 'intelligence': []}`. [VERIFIED: parsed `vault/programs/incremental-cognition/ledger.json` this session]
Recommended gen2 differences: `program` stays `"incremental-cognition"` (the wrapper's B1 binds program); add `"generation": 2`, `"plan": "vault/plans/autonomous-optimization-2026-10-05.md"`, `frozen.champion`, `frozen.reopens` (M: gen1 predicted `MERGED_INTO_EXISTING_OWNER`, gen1 rule "dispositions only"), top-level `opportunities`.

Gen1 pillar M, verbatim, to be reopened (not edited): `"predicted": "MERGED_INTO_EXISTING_OWNER"`, `"rule": "dispositions only: CE Q/N/O/M and the pre-registration pattern of this verifier already own them; an unrestricted optimizer is rejected"`, owners `["vault/programs/cognitive-economy/ledger.json", "tools/baseline_ledger.py"]`. Gen1 `state.M` is `{}` (open).

L1 requires every frozen owner path to exist at P0 (`res.path_exists`), so owners must be files that exist now. [VERIFIED: existence checked this session] `tools/usage_index.py`, `tools/tis_observed.py`, `modules/tower/ratchet.py`, `wiki/tools/kme_pillars.py`, `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_replay.py`, `tools/sovereign_miner.py`, `modules/cognitive_os/co_12_telemetry.py`, `tools/skill_opportunity_signals.py`, `tools/baseline_ledger.py`, `modules/spec_gate/gate.py`, `tools/gex44_env_preflight.py` all exist. `modules/tis_observed` does NOT exist (it is `tools/tis_observed.py`).

Suggested pre-registration (Claude's discretion; the planner may adjust, but predicted + rule are what become immutable):

| id | name | owners | predicted | rule (falsifiable) |
|----|------|--------|-----------|--------------------|
| M | optimizer lifecycle (reopened): durable priced opportunity rows, lifecycle, autonomy envelope | `tools/baseline_ledger.py`, `modules/cognitive_os/co_12_telemetry.py`, `modules/tower/ratchet.py` | IMPLEMENTED_AND_VERIFIED | rows carry the P4 field list; no direct jump to promoted; envelope tests drive both sides; a branch below break-even stops and is recorded; predicted never labelled realized |
| O | usage_index v5 substrate | `tools/usage_index.py`, `tools/tis_observed.py` | IMPLEMENTED_AND_VERIFIED | incremental migration with zero re-read of ingested files; 6 negative controls red when they should; population parity 102 / 34,871 / 11,549,646,300 on the GEX44 copy; cold and delta refresh cost measured |
| P | KME-L challenger | `wiki/tools/kme_pillars.py`, `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_replay.py` | IMPLEMENTED_AND_VERIFIED | 7 KME-L measurement files reproduce identically; beats scoped path (24 s / 2.83 GB) on repeated queries, else narrowed/rejected with a falsification artifact naming [P] (CE L6) |
| Q | generic detectors + discovery eval | `modules/cognitive_os/co_12_telemetry.py`, `tools/skill_opportunity_signals.py` | IMPLEMENTED_AND_VERIFIED | KME-L hotspot found without a KME signature; seeded hit, no-opt control not flagged, low-ROI rejected; detected/missed/false-positive reported; overhead measured |
| R | second workload taken by the loop | `tools/sovereign_miner.py`, `modules/tower/ratchet.py` | IMPLEMENTED_AND_VERIFIED | loop raises/prices/accepts the candidate itself; shadow agreement + GEX44 canary + realized dividend; laptop scheduled-task deploy is an owner-bundle `[R]` line |

`[ASSUMED]` that all five predict IMPLEMENTED_AND_VERIFIED: the plan's "Economics (honest prior)" says the standing token saving may be small and P "may lose to plain scoping", so a pre-registered IMPLEMENT that ends narrowed/rejected needs a falsification artifact (CE L6, `tools/test_cognitive_economy_program.py` clause `L6`). The rule text must carry that exit explicitly. This is a discretion item for the planner, not a locked decision.

### Pattern 4: spec readiness grammar (T3)
[VERIFIED: `modules/sdd_os/readiness.py` module docstring and `_judge_readiness_format`] A spec is judged READY (authorizes) when the front matter has: `status: ready` (exactly `ready`), `scope:` (non-blank list), `open_questions:` items `Q<n> | RESOLVED|ASSUMED|NONE | <answer written>` (an `OWNER_DECISION`, `RESEARCH` or `BLOCKING` item blocks), `acceptance:` items each `AC-n <text> | verify: <command or V-gate id>` (`verify:` must match a command like `python3 tools/x.py` or a `V-XXX-...` id), `must_still_pass:` runnable commands or `none: <reason>`, and, at effective tier 3, `checkpoints:` items `CP-n | <falsifiable checkpoint>`. Nested YAML is MALFORMED. A spec with none of those keys is judged under the LEGACY format, which stops authorizing after `LEGACY_WINDOW_ENDS = date(2026, 11, 1)`. Use the readiness format.
Working T3 exemplar in this repo: `vault/specs/agent-capability-virtualization.md` (front matter keys `covers`, `date`, `updated`, `tier: T3`, `status: ready`, `scope`, `open_questions`, `acceptance`, `must_still_pass`, `checkpoints`). Another T3 with a different, older shape: `vault/specs/gex44-mission-plane.md` (`covers`, `tier: T3`, `status: SPEC (...)`, `owner_decisions`).
The Tier 3 skeleton the generator emits (`modules/sdd_os/pre_exec_gate.py` `_full_spec_body`) lists the required sections: `## 1. Problem`, `## 2. Objective`, `## 3. Non-goals`, `## 4. Actors`, `## 5. Functional requirements`, `## 6. Non-functional requirements`, `## 7. Acceptance criteria`, `## 8. Architecture spec` (`8.1 Components affected`, `8.2 System flow`, `8.3 Contracts`, `8.4 Failure modes`, `8.5 Rollback plan`), `## 9. Test plan`, `## 10. Validation`, and the Tier-3 extras `## Governance spec (Tier 3)`, `## Cross-repo applicability (Tier 3)`, `## Compatibility matrix and migration strategy (Tier 3)`, `## Kill switches (Tier 3)`, `## Standardization rule (Tier 3)`, `## 11. Completion gate`. Map ROADMAP's "PRD, arch, acceptance, rollback, kill switches" onto these headings (PRD = 1-6; arch = 8; acceptance = 7; rollback = 8.5; kill switches = Tier 3 section).
**`covers:` binding rule** [VERIFIED: `modules/sdd_os/spec_binding.py` `entry_matches`, `find_bound_spec`]: a task binds to a spec when its tokens contain ALL sub-tokens of at least one `covers` entry; REFERENCED (task names the spec path) > STRONG (multi-token entry or 2 entries) > WEAK; a tie at the top level is `AMBIGUOUS` and the gate blocks T2+ tasks (`modules/sdd_os/pre_exec_gate.py` lines ~371-377). Candidates come from `SPEC_GLOBS` which includes BOTH `vault/specs/*.md` and `vault/plans/*.md`.
**Hazard (MEASURED):** the approved plan `vault/plans/autonomous-optimization-2026-10-05.md` already declares `covers: [autonomous-optimization, zero-rescan, opportunity-lifecycle, kme-l-challenger, usage-index-v5, optimization-ratchet]`; today `find_bound_spec("autonomous optimization zero-rescan kme-l challenger")` -> `STRONG vault/plans/autonomous-optimization-2026-10-05.md`. If the new spec repeats any of those entries, every task about the programme ties plan-vs-spec -> `AMBIGUOUS` -> blocked. Also `find_bound_spec("opportunity lifecycle ratchet")` is already `AMBIGUOUS` against `vault/plans/skill-capability-program-2026-10-03.md`. Recommendation: the spec's `covers:` entries must be multi-token and absent from the plan (e.g. `[gen2-freeze, optimization-opportunity-row, optimization-autonomy-envelope, usage-index-v5-substrate]` - verify with `find_bound_spec` before committing), and every phase PLAN/task text should name `vault/specs/autonomous-optimization.md` literally (REFERENCED outranks STRONG). Do not edit the approved plan's front matter to resolve this.

### Pattern 5: novelty gate = questions + keyword advisory, record is prose
[VERIFIED: `modules/spec_gate/gate.py:330-344` `NOVELTY_PROOF_QUESTIONS` (13 strings, first: "What concrete problem has no owner today?", last: "Why is this not a rhetorical layer over systems that already exist?"); `:348-354` `_NOVELTY_TRIGGER` = ("fabric", "compendium", "institutional operating system", "kernel", "civilization", "governance layer", "intelligence platform", "operating system", "meta-system", "mega-system", "new dataset family", "universal runtime", "constitutional layer"); `:365-370` `_NOVELTY_SHAPE` (an enumerated-catalog count regex); `:373-377` `NoveltyGateResult(applies: bool, matched: str|None, questions: tuple[str,...], message: str)`; `:380-415` `check_novelty_gate(task_description: str) -> NoveltyGateResult`]. It is **advisory**: the docstring says it "Does not itself decide the verdict"; it never returns a classification. The six classifications named in its message: `EXTEND_EXISTING_OWNER, NEW_MODULE, NEW_VIEW, NEW_POLICY_PACK, NEW_SCANNER_OR_GATE, or REJECT`. It is not exported by `modules/spec_gate/__init__.py` (import `modules.spec_gate.gate`). The only CLI is `echo "<text>" | python3 -m modules.rule_compiler.detectors novelty` (`modules/rule_compiler/detectors.py:11,32-35`, wraps `check_novelty_gate`).
**MEASURED here:** `check_novelty_gate(<plan text>)` -> `applies=False matched=None`; same for the ROADMAP text; positive controls `"new autonomous optimization operating system"` -> `True 'operating system'` and `"... governance layer"` -> `True 'governance layer'`. So the keyword instrument is silent on this programme; per the repo's own note (`gate.py:355-364`) silence is a vocabulary limit, not evidence of non-novelty. The record must therefore (a) record the gate output including the positive controls (proof the instrument can fire), and (b) answer the 13 questions from a **discovered** sweep anyway, because the plan itself says "HR-NOVELTY-001 expected EXTEND_EXISTING_OWNER, run in P0".
**Record convention** [VERIFIED: `vault/audits/ucr_cif/12_HR_NOVELTY_13Q_FAMILY_CLASSIFIER.md` read this session]: an audit file in `vault/audits/` with front matter (`title`, `date`, `status: MEASURED - 13/13 respondidas contra barrido descubierto`, `subject`, `verdict: <classification>`), a section on what the trigger did, then a 13-row table `| # | question | measured answer |` where each answer cites measurement or `file:line`. There is no schema or checker for it. Recommend the new record cite as `path:LINE "verbatim fragment"` and that a V-gate resolve every citation (file exists, line <= length, fragment occurs on that line) - that turns "file:line evidence" into something that can fail (see Validation Architecture).
**Discovered-sweep anchors already read this session** (starting denominator; the executor must re-grep, not copy):
- Substrate owner: `tools/usage_index.py:65` `SCHEMA_VERSION = 4`; `:67-90` SCHEMA (`files, calls, meta, quota, prompts, spawns, subagents`) - no tool-event / cwd / project / content-identity columns; `:422` `def refresh(...)` (incremental, `deadline_s=20.0`); `tools/tis_observed.py:349` `def store_identity(base=None)`.
- Champion path: plan cites `wiki/tools/kme_pillars.py` scan `:1629-1648` and `wiki/tools/kme_token_audit.py:212-230` (zero-rescan plan "Ownership sweep", flagged there as unverified by its author - re-check).
- Ratchet owner: `modules/tower/ratchet.py:120` `verify_chain`, `:146` `revert`, `:164` `promote(family, new_entries, reason, authority, root=None)`; consumers `tools/family_baseline.py:115,128`. No second ratchet is needed.
- Opportunity signal owners: `modules/cognitive_os/co_12_telemetry.py` (`record_signal(kind, payload, *, state_dir=None, now=None)`), `tools/skill_opportunity_signals.py:34-36` (`KIND = "capability_opportunity"`).
- "challenger" occurs in `wiki/tools/kme_replay.py`, `wiki/tools/kme_pillars.py`, `modules/cognitive_os/scheduler.py`, `tools/estate_shadow.py` (grep this session) - the vocabulary already has owners.
- Documented-only: `opportunity lifecycle`, `technical capital`, `realized/predicted dividend` appear only in `vault/plans/autonomous-optimization-2026-10-05.md` and `vault/plans/cognitive-microkernel-brief-2026-10-04.md` (grep over modules/tools/wiki/vault/specs/vault/plans): no executable owner, which is the honest "no owner today" answer for Q1.

### Anti-Patterns to Avoid
- **Editing `frozen` after commit A** (CE L2 fails; no repair short of a new generation).
- **Running CE's selftest under the gen2 binding** (hardcoded A-T fixtures).
- **Letting a drill count an already-red gate as "killed"** (see Pitfall 4).
- **Testing the preflight fix against the live clone** (its HEAD and object store are the thing being fixed; fixtures must be hermetic temp repos).
- **Naming the gen2 pillar letters without the programme**: M, O, P, Q, R collide with CE pillars of the same letters (IC gen1 `frozen.consumes.M` consumes CE Q, N, O, M). Any `[<P>]`-tagged evidence/handoff/owner-bundle text must also name the programme (CE L4 only checks that `[<pid>]` occurs in the file).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pre-registration immutability | a new hash/lock scheme | CE L2 via `FROZEN_AT` + `git show` | already enforced and mutant-tested (V-CEP-MUT-frozen-edited) |
| Terminal/evidence validation | new clause set | `ce.check_ledger` under the rebinding | L1-L9 incl. sha-pinned evidence, falsification-on-demotion, saving labels |
| Spec readiness / binding | a bespoke spec checker | `modules/sdd_os/readiness.assess` + `spec_binding.find_bound_spec` | the same gate that blocks T2+ tasks |
| Patch equivalence | diff text comparison | `git patch-id --stable` (or `git cherry`) | ignores line numbers/whitespace; commit-hash independent |
| Opportunity persistence in P0 | a database / new ledger class | a top-level `opportunities` list in gen2 `ledger.json` | "no new database"; P4 formalizes the schema |
| Atomic JSON/append writes for CO-12 | a second writer | `record_signal` (locked, fail-open) | single locked writer of `signals.jsonl` (`skill_opportunity_signals.py` header says "never a second writer") |

**Key insight:** every Phase 0 deliverable has an existing judge; the work is to feed them correctly and to add mutants proving each new rule can fail.

## Runtime State Inventory

Not a rename/refactor phase. One adjacent fact the planner must carry: the **live GEX44 install is never updated by hand** (CONTEXT, ROADMAP criterion 5); the preflight fix reaches it only through its normal fast-forward sync. Stored data / services / OS state / secrets: none touched by this phase (verified by scope: only repo files plus `/tmp` scratch). Build artifacts: none. The champion evidence files live **outside git** on this host (`/home/kobii/missions/zero-rescan-out/summary.txt`, `/home/kobii/missions/zero-rescan-out2/summary.txt`, `/home/kobii/missions/gex44_ic_rows.sh`); copying them into the repo is the freeze action, and the Run 5 script text is already overwritten (the script on disk is the Run 6 version).

## Champion numbers (criterion 4) - what to freeze, with sources

All read this session.
- Frozen KME-L denominator (gen1 file `vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`, sha256 pinned in measurement front matter as `38493644e142413c79ff0defebd79bec70a5a0605e490c25961e5f8a9c76c1da`): `"calls": 34871`, `"cache_read": 11549646300`, sessions 102 (ledger `frozen.denominators["KME-L"]` in gen1: `"calls": 34871, "cache_read": 11549646300, "cache_write": 209909403, "output": 37878881`). Phase 1 criterion 3 quotes "102 sessions / 34,871 calls / cache_read 11,549,646,300".
- **Run 5 (unscoped champion, GEX44 copy):** `STEP r4-population exit=3 killed=no wall_s=869 peak_rss_MB=184 read_GB=101.53` (verbatim from `/home/kobii/missions/zero-rescan-out/summary.txt`, sha256 `a91bcbd477ebc9a13942bb470aa9a767539ace29b3bf6e3c0266a284b0c98dbe`); the log `/home/kobii/missions/zero-rescan-out/r4-population.log` shows `"until_located": {"method": "not_found", "scans": 10, ...}`, `"population_match": "drifted"`, population 105 sessions / 35,776 calls, `"corpus": {"roots": 1, "project_dirs": 344, "sessions_scanned": 2538, "project_filter": null}` (the null filter is the proof the run was unscoped). Command (reconstructed, tag `[ASSUMED]` for exact quoting because the Run 5 script text was overwritten; its START line `START 2026-10-05T12:13:26+02:00 head=61909502 root=/home/kobii/kme-corpus/projects` and the `run_step` pattern fix everything except spacing): `python3 wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects` in `/home/kobii/missions/zero-rescan-run` at HEAD `61909502`.
- **Run 6 (scoped, same corpus copy):** `/home/kobii/missions/zero-rescan-out2/summary.txt` (sha256 `75e10e10f2e6a9de8280a22cb256c06f74ce9009b790be73ed3cb1c81205793e`): `START 2026-10-05T20:09:57+02:00 head=61909502 root=/home/kobii/kme-corpus/projects project_filter=KobiiCraft-Core-Files|kme-wt-arena2`; population `exit=0 wall_s=24 peak_rss_MB=99 read_GB=2.83`; d-kmel `26 s / 2.85 GB / 159 MB`; d-w7 `exit=3 54 s / 10.04 GB / 169 MB`; e/f/g `24/24/28 s`, `2.77/2.73/2.85 GB`, `106/99/114 MB`; h/i/l-rank `24/25/26 s`, `2.65/2.80/2.82 GB`, `110/99/104 MB`; DONE `20:14:12+02:00`. Runner `/home/kobii/missions/gex44_ic_rows.sh` (sha256 `151338eade13d6306b4d9cb27b6660fb7f48f95b3948e327333115f5a45721f7`) with `PF='KobiiCraft-Core-Files|kme-wt-arena2'` and the nine `run_step` lines. The seven KME-L measurement commands are recorded verbatim in `vault/programs/incremental-cognition/measurements/{D,E,F,G,H,I}-KME-L-2026-10-05.md` front matter (`command: "python3 wiki/tools/kme_pillars.py d --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2'"`) and `L-KME-L-2026-10-05.md` (`python3 wiki/tools/kme_replay.py rank ...`); `plane: "gex44"`; D-KME-L has `population_match: "exact"` and `terminal_evidence: true`.
- **Drift decomposition (plan text, zero-rescan plan Run 5 result):** 34,871 + 649 + 128 + 128 = 35,776 calls; extras = `_archived` (1 session / 649 calls / 271,001,260 cache_read) + one PP session counted twice through the `mcp-video-analyzer` junction alias (128 calls / 34,065,113 x2). The log's `per_project` list agrees (`_archived` 649 / 271001260; `C--Users-User--claude-skills-claude-power-pack` 128 / 34065113; `C--Users-User-Apps-mcp-video-analyzer` 128 / 34065113; `KobiiCraft-Core-Files` 34870 / 11549645760; `kme-wt-arena2` 1 / 540). [VERIFIED: read `r4-population.log` this session]
- Ratio, derived: 869 s / 24 s = 36.2x; 101.53 GB / 2.83 GB = 35.9x (the plan states "~36x from scope alone").
- **Freeze action:** copy the two summary files, `r4-population.log` (Run 5 log), and `gex44_ic_rows.sh` into `gen2/evidence/champion/`, record each sha256 and the command in `frozen.champion`. Rule for the gate: `frozen.champion.run5.command` and `.run6.command` non-empty, numeric fields equal the copied summary lines, sha256 matches the copied files. The CE evidence kind `measurement` demands `command:` in the file text and a frozen denominator name (`_check_evidence`), so a copied summary used as `measurement` evidence needs a `command:` line and the denominator key (e.g. `KME-L`) written into it - or cite it only from `frozen`, not as terminal evidence.

## Preflight instrument fix (criterion 5)

**Reproduction (MEASURED):** `python3 tools/gex44_env_preflight.py --current --checks pp_install` -> `NOT_READY    pp_install    floor 5962571c is not in this install's history (head 79f71693)` / `PREFLIGHT=NOT_READY reasons=pp_install_stale`, exit 1. `python3 tools/test_gex44_env_preflight.py` -> `ENVPF_PASS=55/57`; failing: `V-ENVPF-PP-REAL-READY` (`state=NOT_READY head=79f71693... floor=5962571c...`) and `V-ENVPF-PP-STALE-REAL` (`rc=1 verdict=NOT_READY ... head=01199995 floor=5962571c`, fails on its extra assertion `"does not contain the floor" in inproc["why"]`, `:441`, because with the floor object absent the message is the "not in this install's history" one). `--drill`: `FAIL DRILL-CONTROL unmutated run: 55/57 gates green`, `DRILL killed=6/6`.
**Object-store facts (MEASURED):** `git cat-file -t 5962571c` -> `fatal: Not a valid object name 5962571c`; `git cat-file -t 25a10ce5` -> `commit`; `git cat-file -t 4856b50d` -> `commit`; `60e7947d` is also unknown here. `25a10ce5` message ends `(cherry picked from commit 5962571c840943ae0a3aa901efb08e69a04434da)` (equals `PP_COMMIT_FLOOR`), `308da56b` ends `(cherry picked from commit 60e7947dcf3cf0f9c660e412ec6276a8b2922f99)`; `git branch -a --contains 25a10ce5` lists `mission/autonomous-optimization-gen2`.
**Code (verbatim values, `tools/gex44_env_preflight.py`):** `:56` `PP_COMMIT_FLOOR = "5962571c840943ae0a3aa901efb08e69a04434da"`; `:57` `PP_REQUIRED_FILES = ("tools/gsd_mission.py", "tools/provider_breaker.py")`; `:48` `REASONS = ("auth_expired", "auth_missing", "pp_install_stale", "hooks_broken", "interpreter_unsupported")`; `:50` `FINDINGS = ("access_token_lapsed_refreshable", "hooks_foreign_env", "install_modified", "hook_entries_unjudged")`; `:255-259` `_is_ancestor(sbx, git, install, floor)` runs `[git, "merge-base", "--is-ancestor", floor, "HEAD"]` and maps rc 0 -> True, 1 -> False, other -> None; `:262-318` `check_pp_install(env, floor=None)`: at `:288-293` `rev-parse --verify --quiet {floor}^{{commit}}` rc 1 appends the problem `floor {floor[:8]} is not in this install's history (head ...)`, rc not in (0,1) -> UNMEASURABLE; else `_is_ancestor` (`:295-300`, `None` -> UNMEASURABLE "git could not compare HEAD with the floor", False -> problem `head ... does not contain the floor ...`); required files `:301-303`; `install_modified` finding `:304-311`; NOT_READY with `reasons=["pp_install_stale"]` `:312-314`; READY message `head {head[:8]} contains the floor {floor[:8]}` `:315`. All git calls go through `_Sandbox.run` (`:185-208`: argv list, throwaway HOME, `GIT_OPTIONAL_LOCKS=0`, no shell, per-probe timeout `PROBE_TIMEOUT_S = 15`, run budget `BUDGET_S = 120`). The aggregator passes findings through unfiltered (`:632-656`), so a new finding string needs no table change (add it to `FINDINGS` for documentation).
**Probes run this session** (`/tmp/pickprobe.py`, scratch repos, git 2.43.0; outputs verbatim):
```
pick -x, floor on a side branch, main diverged:  merge-base --is-ancestor rc 1
  trailer: git log -F --grep "(cherry picked from commit <floor>)" --format=%H --max-count=1 HEAD -> <pick sha>
  git cherry HEAD <floor> <floor>^  -> "- <floor sha>"      (equivalent patch exists)
  git show <floor> | git patch-id --stable   and   git log -p --max-count=50 HEAD | git patch-id --stable   -> same patch-id on floor and on the pick
pick WITHOUT -x onto a diverged branch: ancestor rc 1; trailer grep -> ''  ; git cherry -> "- <floor sha>"
unrelated commit on a diverged branch:       git cherry -> "+ <floor sha>"
git clone --no-local --single-branch --branch main (floor object genuinely absent):
  git cat-file -e <floor>^{commit} -> rc 128 ; trailer grep still finds the pick ; git cherry HEAD <floor> <floor>^ -> rc 128 "fatal: unknown commit"
```
Fixture pitfalls found: (a) a plain `git clone <path>` of a local repo copies **all** objects (floor stays present); use `--no-local` to model the GEX44 install where the floor object is absent. (b) A no-`-x` `git cherry-pick` of a commit whose parent is HEAD reproduces the same commit hash (same tree, parent, author, time) and so IS an ancestor - give the pick branch an unrelated commit first so the pick is a different commit. The fixture helper `git()` at `tools/test_gex44_env_preflight.py:259-266` (argv list, throwaway identity, `GIT_CONFIG_GLOBAL=/dev/null`) and `make_install` `:273-290` (base -> floor -> tip, required files from the base) are reusable; the install must be the **root** of a checkout (`rev-parse --show-toplevel` realpath equals install, `:278-281`).
**Recommended design (three accept paths, one verdict):**
1. ancestry (unchanged).
2. trailer: `git log -F --grep "(cherry picked from commit {floor})" --format=%H --max-count=1 HEAD`; require the **full 40-hex floor** in the pattern (an abbreviated or different sha must not match). Works with the floor object absent (the real GEX44 case).
3. equal patch-id: only when the floor object is present (`rev-parse --verify` rc 0) and it is not an ancestor: `git show <floor>` -> `git patch-id --stable` vs `git log -p --max-count=N HEAD` -> `git patch-id --stable` (bound N to keep it cheap; or the equivalent `git cherry HEAD <floor> <floor>^`). Needs the pipe done in Python (two `sbx.run` calls, feed stdout as stdin) because `_Sandbox.run` has no stdin parameter - extend it minimally or call `subprocess.run` with the same sandbox env.
Verdict rules to preserve: any measured refusal stays `NOT_READY` + `pp_install_stale`; "git could not ask" stays `UNMEASURABLE` (never READY); `PP_REQUIRED_FILES` still checked on every path (a pick without the required files is still stale); report which path accepted in `detail["floor_via"]` and a non-refusing finding (`floor_by_pick`) so a pick is visible, not silent; when all three fail the `why` must contain `does not contain the floor` (keeps `V-ENVPF-PP-STALE-REAL`'s assertion true for the a7 head).
**Honest limit to record:** a trailer asserts a pick, it does not prove the code is identical (a conflict-resolved pick has a different patch-id). On GEX44 the floor object is absent, so patch-id equality **cannot** be evaluated there; only the trailer path can accept. A committed constant `PP_FLOOR_PATCH_ID` would enable path 3 without the object, but it can only be computed where the floor object exists (not on this host) - that is an Owner/laptop action to log as a `[P0]` owner-bundle line, not something to fabricate.
**Red-test-first plan (hermetic, in `grp_pp()` `tools/test_gex44_env_preflight.py:351-444`)** - gates and the mutant each must kill:
| gate | fixture | expect | killed mutant |
|------|---------|--------|---------------|
| V-ENVPF-PP-PICK-TRAILER-READY | floor on side branch, `cherry-pick -x` on a diverged main, floor object present | READY, `floor_via=cherry_pick_trailer` | M7 trailer path always False |
| V-ENVPF-PP-PICK-FLOOR-ABSENT-READY | same history cloned with `--no-local --single-branch --branch main` (floor absent) | READY | M7 |
| V-ENVPF-PP-PICK-PATCHID-READY | `cherry-pick` without `-x` onto a diverged branch, floor present | READY, `floor_via=patch_id` | M8 patch-id path always False |
| V-ENVPF-PP-UNRELATED-STALE | diverged unrelated history, no trailer | NOT_READY, `pp_install_stale`, why contains `does not contain the floor` | M9 trailer path always True / M3 |
| V-ENVPF-PP-TRAILER-SPOOF-STALE | commit message trailer naming a different 40-hex sha, and an 8-hex abbreviation of the floor | NOT_READY | M9 |
| V-ENVPF-PP-PICK-REQUIRED-FILE | pick present but `tools/provider_breaker.py` removed | NOT_READY | missing-file check dropped |
Red first means: add these gates, run, record `ENVPF_PASS` showing the new READY gates FAIL against the unfixed `check_pp_install` (and UNRELATED/SPOOF passing), commit the red tests, then fix. Existing `V-ENVPF-PP-STALE-NOT-ANCESTOR` (`:370-374`, floor present, detached at base) is the hermetic gate for the ancestry path.
**Drill hygiene (Pitfall 4):** `MUTANTS` at `:809-817` lists M3 `_m_ancestor_always_true` with target `V-ENVPF-PP-STALE-REAL`; on this plane that gate never reaches `_is_ancestor` (floor absent), so after the fix M3 could survive or "die" for the wrong reason. Retarget M3 to the hermetic `V-ENVPF-PP-STALE-NOT-ANCESTOR`, add M7/M8/M9, and require `DRILL-CONTROL` green (the run-all must be 100 % before the drill means anything; `:823-825`).
**Evidence the claim in the criterion:** ROADMAP/STATE say the live install `4856b50d` holds `25a10ce5`/`308da56b`; `4856b50d` exists in this repository (`git cat-file -t` -> `commit`); the "PFP 28/28, LG 20/20 on GEX44" numbers were not re-run in this research (they are `tools/test_persistent_failure_park.py` and `tools/test_mission_launch_gate.py`; commit messages say 24 V-PFP gates and 19 V-LG gates at authoring time, so the 28/20 counts are later totals - re-run both as `must_still_pass`).

## gen2 ledger + FROZEN_AT + wrapper (criterion 2)

**Dispatch design** (mirrors CE: `tools/test_cognitive_economy_program.py` `main` has `ap.add_argument("--generation", type=int, choices=(1, 2), default=1, ...)` and for 2 does `sys.path.insert(0, str(REPO / "tools")); import cep_gen2; return cep_gen2.main("selftest" if a.selftest else "status" if a.status else "final")`; `--pillar` is refused for gen 2):
- `python3 tools/test_incremental_cognition_program.py --generation 2 --status` -> pre-registration valid (L1, L2 once FROZEN_AT exists) -> exit 0 at P0 completion.
- `--generation 2 --selftest` -> gen2 mutants (below) -> `IC_GEN2_SELFTEST=PASS`.
- `--generation 2 --final` -> all clauses, red until the programme closes (L3 per pillar, L8) - this is correct, not a defect.
- wrapper `--selftest` also runs the gen2 selftest; wrapper `--final` also runs gen2 and prints a distinct `ICP_GEN2_VERDICT=...` line so a gen2 failure cannot hide inside gen1's `failures=` count.
The wrapper's existing `main` shape to extend: `tools/test_incremental_cognition_program.py:1283-1337` (selftest branch `:1286-1291`, `--final` branch `:1292-1320`, `--pillar` branch `:1321-1335`); `ce.main(argv)` argparse would reject an unknown `--generation 2` combined with IC-only flags, so parse `--generation` in the IC `main` before delegating.
**New rules and the mutant that must kill each** (`--selftest` "kills a mutant per new rule"; label `V-IC2-*`, same `say()` style as the wrapper selftest at `:820-837`; each rule gets a clean control first so a clause that refuses everything cannot pass):
| rule | statement | mutant |
|------|-----------|--------|
| G2-B1 | gen2 ledger `program == "incremental-cognition"`, `generation == 2`, path/FROZEN_AT bound to `gen2/`, and CE globals are restored after a gen2 run | ledger with `program` other; `ce.LEDGER_REL` left rebound after the call |
| G2-L1 | frozen pillars exactly `[M,O,P,Q,R]` in order, every `predicted` a terminal, every owner exists (CE L1 under binding) | extra pillar `S`; unknown owner path; `predicted: "DONE"` |
| G2-L2 | gen2 `frozen` equals its copy at `gen2/FROZEN_AT`; `--final` with no `FROZEN_AT` fails | edit one `rule` string; delete FROZEN_AT |
| G2-GEN1 | gen1 `frozen` still equals its copy at gen1 `FROZEN_AT` (`18e928af...`) and gen2 does not redefine A-L, N | gen1 `frozen` pillar rule edited in a temp copy; gen2 carrying pillar `D` |
| G2-CHAMP | `frozen.champion.run5` and `.run6` each carry non-empty `command`, numeric `wall_s` / `read_GB`, `plane == "gex44"`, and sha256 of the copied evidence files equals the files | champion without `command`; sha256 flipped; `read_GB` changed to a value not in the copied summary |
| G2-REOPEN | `frozen.reopens.M.gen1_predicted` equals gen1's frozen M `predicted` (read from gen1 ledger) | gen1_predicted misquoted |
| G2-L3/L6 | an IMPLEMENTED prediction that ends otherwise needs a falsification artifact naming `[<pid>]` (CE L6) | pillar P ends FALSIFIED without artifact |
| G2-OPP | every `opportunities[]` row has the P0-minimal fields, a status from a closed set, evidence files that exist with sha256, and a realized dividend is never set while status is `observed`/`priced` (predicted != realized) | row with realized set at observed; row with missing evidence file |
| G2-X2 | traceability: closed gen2 pillars need a row in `REQUIREMENTS.md` naming the terminal (bind `ce.REQS_REL=".planning/workstreams/autonomous-optimization/REQUIREMENTS.md"` and a `REQ_ROW` regex such as `^\|\s*AOP-([MOPQR])\s*\|[^|\n]*\|([^|\n]*)\|\s*$`); add `AOP-M..R` rows (current table only has `AO-01..AO-17`, which CE's X2 regex does not match) | wrong terminal in the row; missing row |
The CE clause texts L1-L9 / X1-X3 are reused, not reimplemented; the mutants above only need to assert the right clause label appears (`any(x.startswith("L2") ...)`), the same way `tools/test_cognitive_economy_program.py` does (`mutants = {name: (led, clause)}` loop).
**Scope trap:** the wrapper's gen1-only checks (R2 consumed owners, R3 measurement scope, R4 owner decisions, B1) are bound to `PROGRAM_DIR` of gen1; do not run R3 on gen2 (it keys on D-I/L pillar ids). R4 (`check_owner_decisions`, `:643-654`) refuses any `owner_decision` that names the gen1 bundle path and accepts others only with an `attest <sha256> <file>` line in `vault/programs/incremental-cognition/OWNER-ATTESTATIONS.md`; if a later gen2 phase uses `AUTHORIZATION_BOUND`, R4's `names_the_bundle` must also learn `gen2/owner-bundle.md` (`OWNER_BUNDLE_REL` is `PROGRAM_DIR + "owner-bundle.md"`, `:277`). Not needed in Phase 0; log it.
**Baseline of the gate today (MEASURED):** `--selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS` (0.4 s). `--final` -> `L3` for A,B,C,I,J,K,M,N, `L8` x4, `CEP_VERDICT=FAIL failures=12`, `ICP_VERDICT=FAIL failures=1`. gen1 L2 (frozen pin) is currently clean. The `python` executable named in gate argv is replaced by `sys.executable` (`Resolver.run_gate`), and this host has no `python` binary (`which python` empty; `python3` is `/usr/bin/python3`): type every command here as `python3`.

## Opportunity row (criterion 5, "first opportunity row")

[VERIFIED: read `modules/cognitive_os/co_12_telemetry.py` and `tools/skill_opportunity_signals.py`] The repo has no durable opportunity-row format. CO-12 `record_signal(kind, payload, *, state_dir=None, now=None)` appends `{"kind", "ts", **payload}` JSONL under `~/.claude/state/co12_readiness/signals.jsonl` (`_default_state_dir`), with a sidecar lock (`SIGNAL_LOCK_TIMEOUT_S = 2.0`), fail-open `False` on any error. The only producer kind is `capability_opportunity` (`tools/skill_opportunity_signals.py:34-36`) with fields `capability, session, decision, delivered_by, basis, source, mode, foreign_files, unknown_files, card_ts`. That store is host-local runtime state, untracked, and skill-specific: not a ledger. Phase 4's field list (ROADMAP P4 criterion 1): evidence, scope, workload class, frequency, current cost, hypothesis, owner search result, predicted dividend, build + proof + carrying cost, risk, reversibility, champion, challenger, status, retirement condition, realized dividend; lifecycle observed -> priced -> shadow -> canary -> certified -> promoted, plus rejected / narrowed / superseded / retired.
**Recommendation:** record `OPP-001` as an object in a top-level `opportunities` array of `gen2/ledger.json` (outside `frozen`, so it stays editable and the CE verifier ignores it) using the P4 field names, `status` = the lifecycle word that is true (the fix is built and proven, but there is no priced dividend and nothing promoted: use `certified` only if the planner defines it; otherwise the honest state is `observed` -> `priced` with `realized_dividend: null`), a `workload_class: "mission-env-preflight"`, `current_cost`: the false `NOT_READY` on the default env (STATE.md decision: "default env with CPP_NODE_EXE=/opt/node-v24.14.0/bin/node NOT_READY on pp_install_stale only = hash-floor false positive"), `evidence` = the fix commit sha + `evidence/OPP-001-pp-install-hash-floor.md` with sha256, `owner_search_result` = `tools/gex44_env_preflight.py` (EXTEND, the owner exists), `reversibility` = revert one commit, and `retirement_condition` = floor commit present in the install's ancestry. Mark the schema `provisional until P4` so the P4 schema is not pre-empted. Optionally emit one CO-12 signal through `record_signal` with an explicit `state_dir` for coherence, but it is not the record. Do **not** invent a dividend: a predicted saving is never a realized one (CONTEXT).

## Validation Architecture

> nyquist_validation is not set in `.planning/config.json` (file contains only `hooks` and `workflow.skip_discuss`), so this section is included. security_enforcement is also unset (enabled).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | repo V-gate scripts: plain Python, `PASS/FAIL V-XXX` lines, exit code, `--selftest`/`--drill` mutant modes (stdlib only; not pytest) |
| Config file | none |
| Quick run command | `python3 tools/test_gex44_env_preflight.py` (~4.4 s MEASURED); `python3 tools/test_incremental_cognition_program.py --selftest` (0.4 s MEASURED) |
| Full suite command | `python3 tools/test_gex44_env_preflight.py --drill && python3 tools/test_incremental_cognition_program.py --selftest && python3 tools/test_incremental_cognition_program.py --generation 2 --selftest && python3 tools/test_incremental_cognition_program.py --generation 2 --status` |

### Phase Requirements -> Test Map
| Criterion | Behavior | Test type | Automated command | File exists? |
|-----------|----------|-----------|-------------------|-------------|
| 1 spec | spec READY at tier 3, binds to its own task text without AMBIGUOUS, has PRD/arch/acceptance/rollback/kill-switch headings | unit | `python3 tools/test_ao_p0.py` (V-AOP0-SPEC-READY via `modules.sdd_os.readiness.assess(path, 3).state == "READY"`, V-AOP0-SPEC-BINDS via `find_bound_spec(<phase task text>, ".")` -> `.strength in ("STRONG","REFERENCED")` and `.spec_path` is the spec, V-AOP0-SPEC-SECTIONS, plus a mutant: spec with `status: draft` -> NOT_READY, spec whose covers tie with the plan -> AMBIGUOUS) | no - Wave 0 |
| 2 gen2 freeze | pre-registration valid, frozen immutable, gen1 untouched, mutant per rule | unit | `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` ; `python3 tools/test_incremental_cognition_program.py --generation 2 --status` ; `python3 tools/test_incremental_cognition_program.py --selftest` (gen1 + gen2, must stay PASS) | no - Wave 0 (`tools/ic_gen2.py`) |
| 3 novelty | record exists, verdict `EXTEND_EXISTING_OWNER`, 13 answers, every citation resolves, gate positive control fires | unit | `python3 tools/test_ao_p0.py` (V-AOP0-NOVELTY-13, V-AOP0-NOVELTY-CITES-RESOLVE: for each `path:LINE "fragment"` the file exists, line <= length, fragment on that line; V-AOP0-NOVELTY-GATE-CONTROL: `check_novelty_gate("new autonomous optimization operating system").applies is True`; mutants: 12 answers -> red; a citation with a wrong fragment -> red; verdict `NEW_MODULE` without the slice-stops note -> red) | no - Wave 0 |
| 4 champion | numbers frozen with commands and pinned evidence | unit | `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` (G2-CHAMP) and `--generation 2 --status` (real ledger: copied files exist, sha256 match, `read_GB`/`wall_s` match the copied summary lines) | no - Wave 0 |
| 5 preflight | pick-only -> READY; unrelated -> NOT_READY; mutant dropping the hash path -> red; first opportunity row | unit + drill | `python3 tools/test_gex44_env_preflight.py` (expect `ENVPF_PASS=N/N`), `python3 tools/test_gex44_env_preflight.py --drill` (expect `DRILL killed=9/9` with `DRILL-CONTROL` PASS), `python3 tools/gex44_env_preflight.py --current --checks pp_install` (expect `READY` on this clone: HEAD contains the pick `25a10ce5`), `python3 tools/test_persistent_failure_park.py`, `python3 tools/test_mission_launch_gate.py` (must still pass), G2-OPP via `--generation 2 --status` | partially: extend `tools/test_gex44_env_preflight.py` |

### Sampling Rate
- Per task commit: the single suite that task touches (each is < 30 s).
- Per wave merge: Full suite command above plus `python3 tools/test_incremental_cognition_program.py --selftest`.
- Phase gate: all of the above green; `--final` is **expected red** (gen1 L3 on A,B,C,I,J,K,M,N, L8) and gen2 `--final` red for L3/L8 until later phases; record the exact red lines in EVIDENCE.md rather than claiming green (UNKNOWN/INCONCLUSIVE are never PASS).

### Wave 0 Gaps
- [ ] `tools/ic_gen2.py` - gen2 judge + selftest (G2-* rules)
- [ ] `tools/test_ao_p0.py` - spec/novelty/champion V-gates with mutants (or fold into `ic_gen2` selftest; one file is simpler)
- [ ] `tools/test_gex44_env_preflight.py` - six new gates + M7/M8/M9 + M3 retarget, written red first
- [ ] `.planning/workstreams/autonomous-optimization/REQUIREMENTS.md` - `AOP-M..R` traceability rows (X2)
- [ ] Framework install: none (stdlib)

## Common Pitfalls

### Pitfall 1: the `covers:` tie
**What goes wrong:** a spec reusing the plan's tokens makes every programme task `AMBIGUOUS` and blocks T2+ execution (`pre_exec_gate.py` ~371-377). **Why:** `SPEC_GLOBS` includes both `vault/specs/` and `vault/plans/`. **Avoid:** distinct multi-token `covers`, name the spec path in task text, test with `find_bound_spec` (V-AOP0-SPEC-BINDS). **Warning sign:** `find_bound_spec` returns `AMBIGUOUS` with two alternatives.

### Pitfall 2: freezing too early
**What goes wrong:** a mistake in `frozen` after commit A is unrepairable (CE L2). **Avoid:** audit the pre-registration (an independent read of pillars/rules/champion) before commit A; keep everything non-frozen (`opportunities`, `state`, `reviews`, `deltas`) outside `frozen`; write `FROZEN_AT` in commit B only after `--generation 2 --status` is green.

### Pitfall 3: the champion evidence lives outside git
**What goes wrong:** the Run 5/6 summaries, logs and runner are at `/home/kobii/missions/...` on one host; if not copied and hashed, the "frozen numbers" cannot be re-verified and the Run 5 script is already overwritten. **Avoid:** copy + sha256 + record `plane: gex44` and the reconstruction note for the Run 5 command (tag it, do not present it as verbatim).

### Pitfall 4: a drill that counts a pre-red gate as a kill
**What goes wrong:** `KILLED M3 ... by V-ENVPF-PP-STALE-REAL` while `DRILL-CONTROL` is `FAIL` (55/57): the target gate was already red (`_quiet` returns `ok False` and `seen.get(t) is False` counts it killed, `tools/test_gex44_env_preflight.py:833-835`). **Avoid:** require control 100 % green before trusting kills; target hermetic gates only; add a positive control per mutant (the mutant is green-unmutated, red-mutated).

### Pitfall 5: trailer/patch-id accepted without the required files, or with a lookalike sha
**What goes wrong:** accepting any `cherry picked from commit` text (an abbreviated sha, a different commit, a revert note) makes the preflight fail open. **Avoid:** exact 40-hex match with `-F`, required files still checked, `floor_via` + `floor_by_pick` finding reported, spoof gate in the test table.

### Pitfall 6: fixture realism
**What goes wrong:** `git clone <local path>` keeps every object, so a "floor absent" fixture is not absent; a no-`-x` pick onto HEAD's parent yields the identical commit. **Avoid:** `--no-local`, and diverge before picking (both MEASURED above).

### Pitfall 7: the done-gate is red for reasons outside Phase 0
**What goes wrong:** claiming "gate extended, done-gate green". **Avoid:** report `--final` verbatim; escalate the gen1 open pillars as a programme-level risk (see Open Questions 3).

## Code Examples

### Rebinding context manager (shape; verified in prototype)
```python
# Source: prototype /tmp/gen2proto.py, patterned on tools/test_incremental_cognition_program.py:84-93
import contextlib, test_cognitive_economy_program as ce

GEN2_DIR = "vault/programs/incremental-cognition/gen2/"

@contextlib.contextmanager
def bound():
    saved = (ce.PILLARS, ce.LEDGER_REL, ce.FROZEN_AT_REL, ce.HANDOFF_DIR, ce.REQS_REL, ce.REQ_ROW)
    ce.PILLARS = ["M", "O", "P", "Q", "R"]
    ce.LEDGER_REL = GEN2_DIR + "ledger.json"
    ce.FROZEN_AT_REL = GEN2_DIR + "FROZEN_AT"
    ce.HANDOFF_DIR = GEN2_DIR + "handoffs/"
    try:
        yield
    finally:
        ce.PILLARS, ce.LEDGER_REL, ce.FROZEN_AT_REL, ce.HANDOFF_DIR, ce.REQS_REL, ce.REQ_ROW = saved
```

### Pick-trailer probe (argv list, no shell; fits `_Sandbox.run`)
```python
# Source: probes run this session (git 2.43.0)
rc, out, _ = sbx.run([git, "log", "-F", "--grep", f"(cherry picked from commit {floor})",
                      "--format=%H", "--max-count=1", "HEAD"], cwd=install)
via_trailer = rc == 0 and bool(out.strip())   # rc != 0 -> could not ask -> UNMEASURABLE, never READY
```

### Hermetic pick-only fixture (extends `make_install`)
```python
# floor on a side branch; main diverges; pick -x puts the trailer on main
git(inst, "checkout", "-q", "-b", "side", base);  ...commit floor...;  floor = git(inst, "rev-parse", "HEAD")
git(inst, "checkout", "-q", "main");  ...commit unrelated...;  git(inst, "cherry-pick", "-x", floor)
# floor-absent variant: git(tmp, "clone", "-q", "--no-local", "--single-branch", "--branch", "main", str(src), str(install_of(tmp)))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| preflight judges `pp_install` by `merge-base --is-ancestor` only | ancestry OR exact pick trailer OR equal patch-id | this phase | stops false `NOT_READY` on picked installs without hand-updating the live install |
| IC wrapper judges one ledger | wrapper dispatches `--generation 2` to `tools/ic_gen2.py` | this phase | pillars M,O,P,Q,R judged without touching gen1 `frozen` |
| `opportunity` = CO-12 skill signal in untracked state | durable git-tracked `opportunities[]` row | this phase (provisional), P4 (schema) | first row is auditable |

**Deprecated/outdated:** the plan's phrase "skill-capability/gen2 precedent" - SC's gen2 directory has no ledger; the real precedent for a gen2 *ledger* is CE gen2 (different shape) and for *shape* IC/SC gen1. LEGACY spec grammar stops authorizing after 2026-11-01 (`LEGACY_WINDOW_ENDS`).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | All five pillars should predict IMPLEMENTED_AND_VERIFIED | Pattern 3 | `frozen` is immutable; a wrong prediction forces a falsification artifact (L6) later. Owner/planner should confirm, especially P and R |
| A2 | The Run 5 command is `python3 wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects` (reconstructed; script overwritten) | Champion numbers | frozen command text slightly off; mitigated by tagging it reconstructed and by the log's `"project_filter": null` |
| A3 | `git cherry` is equivalent to `git patch-id --stable` for non-trivial diffs | Preflight | only matters if `git cherry` is used instead of the roadmap's `--stable` pipe; recommended to use `--stable` |
| A4 | Spec `covers:` entries like `gen2-freeze`, `optimization-opportunity-row` will bind phase task text without tying | Pattern 4 | must be checked with `find_bound_spec` on the actual phase task texts before commit |
| A5 | The "PFP 28/28, LG 20/20" counts (STATE.md/ROADMAP) are current | Preflight | not re-run here; re-run both suites as `must_still_pass` |

## Open Questions

1. **`covers:` tie between spec and plan**
   - Known: plan and spec dirs are both in `SPEC_GLOBS`; identical tokens -> AMBIGUOUS (MEASURED analogous case for "opportunity lifecycle ratchet").
   - Unclear: whether the Owner accepts the plan's front matter being left as is while the spec uses disjoint tokens.
   - Recommendation: disjoint multi-token covers + name the spec path in task text; verify with `find_bound_spec`.
2. **patch-id path cannot run on GEX44**
   - Known: floor object `5962571c` absent here; trailer path works; patch-id needs the floor object or a stored constant.
   - Unclear: whether the Owner can supply `PP_FLOOR_PATCH_ID` (computed where the object exists).
   - Recommendation: implement the object-present patch-id path, ship the trailer path as the GEX44-operative one, log a `[P0]` owner-bundle line asking for the constant; do not claim patch-id acceptance on GEX44.
3. **`--final` exit 0 is unreachable from this programme alone**
   - Known: gen1 pillars A,B,C,I,J,K,M,N have no terminal and L8 is empty (MEASURED `CEP_VERDICT=FAIL failures=12`); ROADMAP Phase 7 says "Done-gate exit 0".
   - Unclear: whether the programme's done-gate means gen1+gen2 (needs the incremental-cognition mission to close its own pillars) or gen2 only.
   - Recommendation: define and print both (`ICP_VERDICT` and `ICP_GEN2_VERDICT`); put gen1's M closure (gen2 M supersedes the "dispositions only" rule) in the Phase 7 handoff and ask the Owner which verdict is the programme's done-gate.
4. **Where the gen2 owner bundle sits relative to R4**
   - Known: R4 recognises only the gen1 bundle path.
   - Recommendation: no Phase 0 action; note for any later `AUTHORIZATION_BOUND` pillar.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | all V-gates | yes | 3.12.3 (`/usr/bin/python3`) | - |
| `python` (bare) | commands typed in older docs | no | - | use `python3` everywhere; the CE gate runner substitutes `sys.executable` |
| git | preflight, FROZEN_AT, fixtures | yes | 2.43.0 | - |
| node | `tools/gex44_env_preflight.py` interpreter check, `gsd_x_runtime_preflight.js` | system v18; `/opt/node-v24.14.0/bin/node` via `CPP_NODE_EXE` | - | judge MC/HPKT gates only with `CPP_NODE_EXE` (STATE.md) |
| floor commit `5962571c` | patch-id path on GEX44 | no (object absent) | - | trailer path |
| KME corpus copy | not needed in Phase 0 | `/home/kobii/kme-corpus/projects` | - | - |

**Missing dependencies with no fallback:** none for Phase 0. **Missing with fallback:** floor object (trailer path).

## Project Constraints (from CLAUDE.md)

Directives that bind this phase (from `./CLAUDE.md` of the mission checkout and the global `~/.claude/CLAUDE.md`):
- Reality Contract: zero placeholders, stubs, mocks, empty catch blocks in shipped code; if a feature cannot be wired end to end, state the gap and stop (applies to `tools/ic_gen2.py`: every rule must have a live judge and a mutant).
- Test doctrine (`~/.claude/rules/python/testing.md`): AAA sections, RED before GREEN, `V-<DOMAIN>-<NAME>` gate ids with a `*_PASS=n/n` summary line, mock only at boundaries, each fail-open/exhausted branch tested, evidence is test output not description.
- Instrument-before-claim: could this instrument have returned the other answer? (drill control green; novelty gate positive control; every "absent" claim has a fixture where it is present.)
- Never-hang doctrine: foreground, bounded commands for verification; no `run_in_background` for results needed this turn.
- Commits: explicit pathspec only, one coherent falsifiable increment each; verify `git log -1 --format=%s` matches the intended subject (shared `COMMIT_EDITMSG` race); end commit messages with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; commit bodies via a tempfile and `git commit -F` (HR-003, no heredoc into argv).
- HR-001: nothing under the laptop's `~/.claude/`; GEX44's own `~/.claude/state` must not be written by tests (use `state_dir=` scratch if any CO-12 signal is emitted).
- HR-NOVELTY-001: 13 answers with cited file:line from a discovered sweep, or classify as EXTEND_EXISTING_OWNER / NEW_MODULE / NEW_VIEW / NEW_POLICY_PACK / NEW_SCANNER_OR_GATE / REJECT.
- SDD-OS: this is T3 (new standard/framework layer + persisted ledger + cross-repo evidence); spec before the first edit, `covers:` front matter, `status: ready` via the readiness grammar.
- Liveness Standard: no new `modules/` package is planned; if one is added, `python3 modules/liveness/reachability.py` must be clean. `tools/ic_gen2.py` is reached from the IC wrapper dispatch.
- UKDL entries (later phases) are inserted in their section, never at the tail.
- ROADMAP constraints: GEX44 plane; never push from inside an ssh body; no Agent Teams unless an independent uncertainty with a consumer, solo, bounded, durable-output; no identical retry (Regla 12: second identical failure -> pivot); record low-ROI items as deferred, do not polish.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (preflight reads credential *expiry* only; no change) | existing `provider_breaker` reader; canary tests already assert no token appears in output |
| V3 Session Management | no | - |
| V4 Access Control | yes (autonomy envelope is Phase 4; here: tests must not write real `~/.claude`) | scratch HOME/state dirs |
| V5 Input Validation | yes | argv lists only (no shell), 40-hex floor regex `[0-9a-f]{40}` (`check_pp_install` `:269`), `SAFE_ARG` for gate argv (CE), JSON via `json.loads` |
| V6 Cryptography | no (sha256 via `hashlib` for evidence pins; never hand-rolled) | `hashlib.sha256`, LF-normalised like `ce.lf_sha256` |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Fail-open accept on a forged trailer | Spoofing / Elevation | exact 40-hex `-F` match; required files still checked; `floor_by_pick` finding; spoof gate |
| Command injection through a floor/commit string into git | Tampering | argv list via `_Sandbox.run`, 40-hex validated first |
| Editing the pre-registration after the fact | Tampering | CE L2 vs `FROZEN_AT` commit; mutant `frozen-edited` |
| Evidence swapped after citation | Tampering | sha256 pins (CE L4 `sha256 changed since it was cited`); champion copies hashed |
| Credential leakage via evidence copies | Information disclosure | champion files hold counts and paths only; run a secret grep before committing the copied logs (HR-SECRET-004/005) |

## Sources

### Primary (HIGH confidence) - read or executed this session
- `tools/test_incremental_cognition_program.py` (lines 1-330, 443-660, 820-900, 1283-1338), `tools/test_cognitive_economy_program.py` (1-262, 263-430, 500-733), `tools/cep_gen2.py` (1-80)
- `vault/programs/incremental-cognition/ledger.json` (parsed), `.../FROZEN_AT`, `vault/programs/skill-capability/ledger.json` (parsed), `.../FROZEN_AT`, `vault/programs/cognitive-economy/gen2/ledger.json` (parsed), `vault/programs/skill-capability/gen2/` (listing, SPEND.md head)
- `git show --stat` of `d4d35059`, `18e928af`; `git log` of the picks `25a10ce5`, `308da56b`
- `modules/spec_gate/gate.py:316-466`, `modules/sdd_os/readiness.py` (module docstring, `_judge_readiness_format`, `assess`), `modules/sdd_os/spec_binding.py` (docstring, `entry_matches`, `find_bound_spec`), `modules/sdd_os/pre_exec_gate.py:214-336`
- `vault/specs/agent-capability-virtualization.md` (front matter), `vault/specs/gex44-mission-plane.md` (head), `vault/audits/ucr_cif/12_HR_NOVELTY_13Q_FAMILY_CLASSIFIER.md` (head)
- `tools/gex44_env_preflight.py` (1-70, 183-322, 632-734), `tools/test_gex44_env_preflight.py` (1-72, 256-310, 349-447, 743-847); command runs: preflight `--current`, test suite, `--drill`
- `modules/cognitive_os/co_12_telemetry.py` (1-120), `tools/skill_opportunity_signals.py` (all), `tools/usage_index.py` (60-110, 420-440), `modules/tower/ratchet.py` (160-200)
- `/home/kobii/missions/zero-rescan-out/{summary.txt,r4-population.log}`, `/home/kobii/missions/zero-rescan-out2/summary.txt`, `/home/kobii/missions/gex44_ic_rows.sh`, `vault/programs/incremental-cognition/measurements/D-KME-L-2026-10-05.md` (head) and the `command:` lines of the six KME-L files
- Scratch probes: `/tmp/pickprobe.py` (git patch-id/trailer/cherry), `/tmp/gen2proto.py` (CE rebinding)

### Secondary (MEDIUM)
- `vault/plans/zero-rescan-reality-scan-2026-10-05.md` ownership-sweep claims about `kme_pillars.py:1629-1648` and `kme_token_audit.py:212-230` (the plan says "unverified by me beyond citations"; not re-read here)

### Tertiary (LOW)
- none

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all in-repo, read this session
- Architecture (rebinding, FROZEN_AT, dispatch): HIGH - prototype executed
- Preflight fix: HIGH for diagnosis and git behaviour (executed); MEDIUM for patch-id on GEX44 (object absent, constant not available)
- Pre-registration predictions: MEDIUM - discretion items tagged A1

**Research date:** 2026-10-05
**Valid until:** 2026-10-12 (the preflight tests, wrapper and ledgers are in active mission use; re-run the three baseline commands before planning if HEAD moves)
