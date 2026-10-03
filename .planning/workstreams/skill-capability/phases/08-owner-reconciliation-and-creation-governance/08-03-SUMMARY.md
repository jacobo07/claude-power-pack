---
phase: 08-owner-reconciliation-and-creation-governance
plan: 03
status: complete
subsystem: skill-capability pillars I, K, L, M (owner reconciliation handoffs)
tags: [handoff, pillar-I, pillar-K, pillar-L, pillar-M, owner-reconciliation]
requires: [tools/skill_mirror_drift.py, tools/skill_opportunity_signals.py, modules/liveness/reachability.py, modules/capability_runtime/retirement.py]
provides: [tools/skill_handoffs.py, tools/test_skill_handoffs.py, vault/programs/skill-capability/handoffs/I.md, vault/programs/skill-capability/handoffs/K.md, vault/programs/skill-capability/handoffs/L.md, vault/programs/skill-capability/handoffs/M.md]
affects: [08-04 (ledger lines I/K/L/M cite these handoffs with an LF sha256 pin; owner-bundle [I] [K] [L] items)]
tech-stack:
  added: []
  patterns: [committed-blob measurement at a resolved sha, git-archive export with empty HOME, content-pinned adjudication list, exact fail-set drills on a fixture repo]
key-files:
  created: [tools/skill_handoffs.py, tools/test_skill_handoffs.py, vault/programs/skill-capability/handoffs/I.md, vault/programs/skill-capability/handoffs/K.md, vault/programs/skill-capability/handoffs/L.md, vault/programs/skill-capability/handoffs/M.md]
  modified: []
decisions:
  - "M cost-marker hits on this program's own files are adjudicated in a content-pinned list (M_ADJUDICATED: path + exact line + reason), never by narrowing the fixed DH-04 marker; an open hit is FAIL, a stale pin UNMEASURED"
  - "I skill candidates read the coverage class from the committed D-coverage.md `## Plane gex44` table, cross-checked for set equality against D-live-gex44.json, because D-live-gex44.json carries no per-skill coverage key"
  - "K's CO-12 row count is host-state information, not a claim part: HANDOFF_K is PASS with rows=UNMEASURED and --check exits 0 (the Task 2 verify allows exactly that)"
  - "Handoffs were re-measured after the test commit so the K and M tables list both new files (DH-03 acceptance); final measured commit 1e32ae7a"
metrics:
  duration: 815s
  completed: 2026-10-03
plan_head_before: 2e934fdd73c34b8e5d6ed5ac0673d3c4378f1f74
actuals:
  tokens: 23600
  tasks: 3
  commits: 7
---

# Phase 8 Plan 03: handoffs I/K/L/M Summary

`tools/skill_handoffs.py` is a read-only tool. It measures the evidence that each frozen owner of pillars I, K, L
and M needs, reading committed blobs at a named commit. It renders four handoffs, one per pillar, each with line 1
`[<P>] -> <owner>`. `--check` re-measures every claim at HEAD and checks the handoff contract. 23 drills drive each
sweep to its red branch on a fixture repo.

## Commits

| # | Commit | Subject |
|---|---|---|
| 1 | a9177a05 | feat(08-03): skill_handoffs measures pillar handoffs from committed blobs |
| 2 | 2723ac3c | docs(08-03): handoff L measured at a9177a05 (Context Compiler absent by name) |
| 3 | d91ececd | fix(08-03): handoff tool -- no bytecode in the export, adjudicated cost hits |
| 3b | d0f7bab7 | fix(08-03): handoff text states adjudicated hits and the export plane exactly |
| 4 | 9af782b4 | docs(08-03): handoffs I, K, M (and L refreshed) measured at d0f7bab7 |
| 5 | 1e32ae7a | test(08-03): drills for every handoff sweep, both poles (SKH_PASS=23/23) |
| 6 | 466df5bd | docs(08-03): handoffs I, K, L, M re-measured at 1e32ae7a (test file in aperture) |

`commits: 7` is `git rev-list --count 2e934fdd..HEAD`, measured before this SUMMARY's own commit. All seven are
this plan's commits. The plan named five. The extra two are 3b (a text fix found while reviewing the rendered
handoffs) and 6 (the DH-03 acceptance needs the test file listed in the K and M tables).

## Handoffs (final state, measured at 1e32ae7a, host kobicraft-gex44)

| Handoff | Line 1 | Claim |
|---|---|---|
| handoffs/I.md | `[I] -> modules/liveness/reachability.py` | PASS reachability, retirement, nowrite, skills |
| handoffs/K.md | `[K] -> modules/capability_runtime/agent_spec.py` | PASS aperture, router, control (CO-12 rows UNMEASURED, reported) |
| handoffs/L.md | `[L] -> modules/cognitive_os/co_12_telemetry.py` | PASS absence, control, writer |
| handoffs/M.md | `[M] -> tools/usage_index.py` | PASS aperture, cost, control |

The owner on line 1 is derived by a fixed rule: the first frozen owner that is a repo `.py` path, taken from the
ledger's `frozen.pillars` at the measured commit. It is not typed per pillar.

## Figures as measured (commit 1e32ae7a, each with its command)

- **I modules**: `HOME=<empty tmp> python3 modules/liveness/reachability.py --json`, run in a `git archive` export:
  rc=1, 490 rows (REACHABLE 299, ORPHAN 191), 75 gate offenders. Not reachable, counted by class: LIBRARY 56,
  PLANNED 52, undeclared 83. Candidates (DH-02): 83. Row keys `unit`/`status`/`klass` matched the plan, so no
  adaptation was needed. The archive was 72,939,520 bytes with 5004 members, and the data filter refused 0.
- **Plane check (W1 confirmed)**: the same scanner on the live plane (`python3 modules/liveness/reachability.py
  --json` from the worktree, which merges the live ~/.claude seeds) reports 64 offenders. The export with an empty
  HOME reports 75. The 11-module difference comes only from the plane. The handoff names its plane.
- **I retirement**: `HOME=<empty tmp> python3 modules/capability_runtime/retirement.py --json` (export, never
  `--record`): rc=0, 13 verdicts (UNEVALUABLE 5, ACTIVE 4, EXTERNAL 2, NEVER 2).
- **I nowrite**: `git status --porcelain -- vault/capability_runtime vault/liveness vault/programs/cognitive-economy`
  was the same before and after. The export tree and HOME were unchanged too.
- **I skills**: coverage `none` on plane gex44 = 159 of 161 skills (from D-coverage.md, cross-checked against
  D-live-gex44.json). Invoked in window G (2026-09-26T18:05Z..2026-10-03T18:05Z, host kobicraft-gex44, 189 files):
  gsd-autonomous, gsd-code-review, gsd-execute-phase, gsd-plan-phase. That leaves 155 candidates. CE pillar T is
  read from the CE ledger: "institutional GC / simplification", predicted AUTHORIZATION_BOUND. I.md says verbatim:
  "A candidate is not a deletion verdict. This program deleted nothing."
- **K**: `git diff --name-only --diff-filter=A 217d72b5 1e32ae7a -- modules tools` returned 16 added files. Router
  hits: 0. Controls hit by content: modules/cost_collapse/router.py:65, modules/cognitive_os/router.py:75 and
  modules/knowledge_acquisition/routing.py:189. `report()` returned `{"rows": 0, ...}` and the file is absent, so
  the row count is UNMEASURED: "gex44 has no card ledger".
- **L**: `git ls-tree` found 0 of 4294 tracked paths matching `(?i)context[_-]?compiler`. The identifier
  `git grep -nIE` over `*.py`/`*.js` returned 0 lines (rc 1). The contrary-claim grep returned 3 lines: the USIRC
  matrix line 63 (the control), frontier28 VERDICTS.md line 253, and genesis-batch-drafts.cjs line 3. 15 lines name
  the CO-12 file, 3 of them writers (the controls co_12_telemetry.py:111, test_agent_telemetry.py:271,
  test_co12_signal_race.py:47). Of the 14257 `*.py`/`*.js` lines added since the freeze, 0 are writer lines.
- **M**: the ledger `savings[]` has 2 entries: A, 5 turns, upper_bound, D-CARD; B, 9000 tokens, upper_bound,
  D-LISTING. 4 delta lines are quoted: B-listing-floor.md lines 21, 45 and 46 (D-LISTING) and E-contribution.md
  line 45 (D-SESSIONS, a pass-rate difference, stated as not a token or turn delta). The cost sweep over 16 files
  has 2 hits, 0 open and 2 adjudicated. The control tools/usage_index.py hits 3 times (import :51, def :520, def
  :524).

## Gate outputs (verbatim)

- Task 1 verify: `HANDOFF_L PASS absence=PASS control=PASS writer=PASS contract=PASS` and line 1
  `[L] -> modules/cognitive_os/co_12_telemetry.py`.
- Task 2 / final `python3 tools/skill_handoffs.py --check; echo rc=$?` (after commit 6):
  ```
  HANDOFF_I PASS reachability=PASS retirement=PASS nowrite=PASS skills=PASS contract=PASS
  HANDOFF_K PASS aperture=PASS router=PASS control=PASS contract=PASS rows=UNMEASURED(gex44 has no card ledger (file present: False, rows 0))
  HANDOFF_L PASS absence=PASS control=PASS writer=PASS contract=PASS
  HANDOFF_M PASS aperture=PASS cost=PASS control=PASS contract=PASS
  SKILL_HANDOFFS PASS pillars=4
  rc=0
  ```
- Task 3 `timeout 600 python3 tools/test_skill_handoffs.py | tail -1` returned `SKH_PASS=23/23`, rc=0. Wall time
  4.5 s (`/usr/bin/time` wall=4.52s).
- Independent instrument: the CE verifier's `_check_evidence` (L4) was run on a synthetic handoff entry per pillar,
  with the sha from `Resolver.file_sha`. It returned 0 findings for I, K, L and M. As a negative control, each file
  was also judged as pillar J and was refused each time ("does not name pillar [J]").
- Regression `python3 tools/test_skill_capability_program.py --pillar <P>`: A through H each print
  `CEP_PILLAR_<P>=PASS` with rc 0. I, K, L and M are still `FAIL L3 <P>: no terminal disposition`, as expected,
  because 08-04 writes those ledger lines.
- `git status --porcelain -- vault/capability_runtime vault/liveness vault/programs/cognitive-economy` was empty
  after every run.

## Drill table (expected = observed for every row)

| Drill | Expected non-PASS set |
|---|---|
| BASELINE | {} |
| ROUTER-BASENAME (tools/x_router.py) | K:router=FAIL |
| ROUTER-DEF (line starting with a route definition, built from fragments) | K:router=FAIL |
| PRICING-IMPORT | M:cost=FAIL |
| CO12-APPEND (open for append on the CO-12 file) | L:writer=FAIL |
| NAMED-MODULE (modules/ + the searched name) | L:absence=FAIL |
| ROUTER-CONTROLS-REMOVED | K:control=UNMEASURED |
| COST-CONTROL-REMOVED | M:control=UNMEASURED |
| WRITER-CONTROL-REMOVED | L:control=UNMEASURED |
| CLAIM-CONTROL-REMOVED (USIRC file) | L:control=UNMEASURED |
| ZERO-ADDED | K:aperture=UNMEASURED, M:aperture=UNMEASURED |
| CONTRACT-NON-OWNER (line 1 names a non-owner path) | K:contract=FAIL |
| CONTRACT-NO-TAG (`[M]` removed) | M:contract=FAIL |
| ADJUDICATED-ADMITTED (pinned line exact) | {} |
| ADJUDICATED-EDITED (pinned line changed) | M:cost=FAIL |
| ADJUDICATED-STALE (file in population, line gone) | M:cost=UNMEASURED |
| WORKTREE-ONLY (router file never committed) | {} |
| I-NO-SCANNERS (export without the two scanners) | I:reachability=UNMEASURED, I:retirement=UNMEASURED |

Further gates:
- V-SKH-EVERY-PART-RED `driven=11/11`.
- V-SKH-GIT-MISSING `rc=1 last='SKILL_HANDOFFS INCONCLUSIVE pillars=4'` with no Traceback.
- V-SKH-LIVE: rc 0 on this checkout.
- V-SKH-NO-SELF-ENROL: 0 `KIND =`/`CAPABILITY =` lines in either file; the real adapter control has 2.
- V-SKH-SELF-CLEAN: both files have 0 router, cost, writer and name hits. This gate was observed red once
  (cost=1, from the constant `PRICING_IMPORT` in the test) and the constant was renamed before commit 5.

## Acceptance criteria

- `head -1` of the four handoffs equals the four required lines (table above).
- The watched porcelain stayed empty after every run, so nothing was written to vault/capability_runtime,
  vault/liveness or the CE dir.
- The K and M sweep tables list `tools/skill_handoffs.py` and `tools/test_skill_handoffs.py`, both with 0 hits
  (K.md lines 51 and 61, M.md lines 70 and 80).

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 - Bug] Bytecode written into the export made I's nowrite part FAIL**
- Found during: Task 2, first full `--check`.
- Fix: the exported scripts run with `PYTHONDONTWRITEBYTECODE=1`. Commit d91ececd.

**2. [Rule 1 - Bug, judgement recorded] The fixed cost marker hits two of this program's files**
- `tools/skill_dedup_sweep.py:324 def _line_cost(` is a listing char count (pillar F).
  `tools/test_card_precision.py:330 def write_unborn_pricing(` is a drill fixture (pillar A). Neither is a cost
  model.
- Unattended, I took the safest honest option. The DH-04 marker is unchanged. Each hit is pinned in
  `M_ADJUDICATED` by path, exact line and reason, and is shown in M.md under "Marker hits adjudicated not a cost
  model". Editing the line re-opens the hit (FAIL). A pin whose file is in the population but no longer hits is
  stale (UNMEASURED). Both cases are drilled. The Owner may disagree with a reason. 08-04 may surface this.

**3. [Rule 1 - Bug] Handoff text defects**
- M said no marker hit was found, which contradicted the adjudicated hits. I asserted an unmeasured "would mark
  more reachable". One command cell nested backticks. Table pipes were rewritten instead of escaped.
- Fixed in commits d91ececd and d0f7bab7.

**4. [Plan premise] D-live-gex44.json carries no per-skill coverage key**
- Its keys are command, counts, evidence, host, measured_at, node, non_skill_dirs, schema and skills (a list of
  names). Coverage is computed by pillar D's gate and rendered into D-coverage.md.
- Fix: the I skill rule reads the committed `## Plane gex44` table of D-coverage.md and refuses (UNMEASURED)
  unless its skill set equals D-live-gex44.json `skills`. The invocation set is C-window-G.json `skills` (a dict
  keyed by skill).

**5. [Scope] Widened CO-12 writer marker**
- The marker also counts JS fs writes (`appendFileSync`, `writeFileSync`, `appendFile`, `writeFile`,
  `createWriteStream`) on a line naming the file. It is strictly wider than DH-04. At the measured commit no `.js`
  line names the file, so no figure changed.

**6. [Scope] Contrary-claim grep is case-insensitive**
- The USIRC control is matched case-sensitively on "Context Compiler". The VERDICTS.md and genesis lines write
  "context compiler" in lower case, so locating all three by one grep needs `-i -F`.

**7. [Scope] K's CO-12 row count is information, not a claim part**
- This keeps `--check` at rc 0 while the count is UNMEASURED on gex44, as the Task 2 verify allows.

**8. [Process] Seven commits instead of five**
- See the Commits section. L.md was refreshed in commit 4 and all four handoffs again in commit 6, so the final
  handoffs share one measured commit, 1e32ae7a.

### Not done (by design)
- No ledger line, owner-bundle line, STATE.md or ROADMAP.md edit. The ledger and bundle belong to 08-04; the
  orchestrator owns STATE.md and ROADMAP.md.
- No `--baseline`, `--record` or `sync` was run.

## Known Stubs

None.

## Self-Check: PASSED

- The six created files exist and are committed. The working copies equal HEAD (`git status --porcelain` on them
  was empty).
- All seven commits are present in `git log 2e934fdd..HEAD`: a9177a05, 2723ac3c, d91ececd, d0f7bab7, 9af782b4,
  1e32ae7a and 466df5bd.
