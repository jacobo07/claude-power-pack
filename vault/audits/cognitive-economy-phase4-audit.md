# Cognitive Economy Program -- Phase-4 Adversarial Audit

Subject: `vault/plans/cognitive-economy-program-2026-10-03.md` (APPROVED). HEAD 1cabd117.
Auditor: oneshot phase-4 (read-only except this file). Date 2026-10-03.

VERDICT: EXECUTE-WITH-FIXES -- do NOT arm until G1-G4 are injected (each alone makes `--final`
unreachable or closable falsely); G5-G7 before arming a 24 h unattended run; G8-G11 in P0.
11 gaps: 3 CRITICAL (G1-G3), 4 HIGH (G4-G7), 3 MEDIUM (G8-G10), 1 LOW (G11).

## Gaps (appended as confirmed)

### G1 -- CRITICAL -- bind-mission deadlocks the goal: no obligation can be SATISFIED and closure is blocked while the mission runs

Claim: plan s9 binds the Ralph mission to the goal "observe-only via `bind-mission`", and s5 makes the
mission's done-gate require `may_close` + judge PASS. A bound mission is an epoch in state `running`
for the whole mission. While any epoch is running, the reconciler returns WAIT before it ever reaches
gate dispatch, and `goal_closure` lists every open epoch as blocking. So during the mission: no gate
epoch is dispatched -> no obligation reaches SATISFIED (only a harvested gate receipt reaches it) ->
`goal_closure` blocks ("epoch ... is still open") -> `--final` cannot exit 0 -> the mission can never
reach its own DONE; it can only end by budget / no_progress halt. Circular by construction.

Evidence:
- `modules/gsd_x/goal/bind_mission.py:54-58` -- `ep.begin(... LongRunProvider ...)` then `ep.mark_running`.
- `modules/gsd_x/goal/epoch.py:262-263` -- `open_epochs` = every epoch whose state != "ended".
- `modules/gsd_x/goal/convergence.py:331-332` -- `for ep in open_epochs: blocking.append("epoch {ep} is still open")`.
- `modules/gsd_x/goal/reconcile.py:138-150` -- step 2 returns WAIT for a running observed epoch before
  step 5 (gate NEXT_EPOCH, lines 182-213) is reachable.
- `modules/gsd_x/goal/sweep.py:269` + `convergence.py:289-310` -- SATISFIED is written only by
  `sweep._apply_verdicts` from a harvested gate receipt (no CLI path to it; `retire` refuses SATISFIED,
  `convergence.py:227-231`).

Fix: do NOT `bind-mission` during the run (or bind it only after the mission ends, as an audit record).
Instead the worker drives obligations itself with `gsd_x_goal.py reconcile --apply` (one gate epoch per
call, `tools/gsd_x_goal.py:286-316`) followed by a second `reconcile --apply` to harvest, looping until
`status` shows no ACCEPTED obligations. Add a P1 selftest that asserts `status --json` has
`epochs` with no `running` entry of provider `long_run` before `--final` is evaluated. If observation
of the mission is still wanted, record it in the ledger, not as a goal epoch.

### G2 -- CRITICAL -- goal tree identity moves with every peer commit/edit in the shared checkout; may_close is a treadmill

Claim: every SATISFIED verdict must carry the tree hash of the tree being closed
(`convergence.py:347-352`), and the judge refuses UNJUDGEABLE if the worktree's tree differs
(`judge.py:132-136`). `tree_id` returns `git:<HEAD^{tree}>` (the WHOLE repo's HEAD tree, whatever the
scope paths) when the scope is clean, or a content hash of the scope paths when dirty
(`git_state.py:124-142`). The plan runs in the main checkout with 7 peer panes, a running peer Ralph
mission, 815 dirty peer entries and +15 peer commits since approval (plan s1). Any peer commit moves
HEAD^{tree} -> every banked verdict becomes "proven at tree X, not at the tree being closed" -> the
reconciler re-dispatches it (`reconcile.py:186-203`). Satisfying ~20 obligations takes ~40
reconcile passes (one dispatch + one harvest each, `sweep.py:278-391`), so the chance no peer commit
lands across the whole window is ~0. Also, with the default scope `["."]` and a dirty repo,
`tree_id` rglob-hashes every file in the repo (`git_state.py:135-141`) -- slow on this tree, and it
changes on any peer keystroke.

Fix (pre-arm):
(a) Run the mission in its OWN git worktree on its own branch (precedent: `.claude/worktrees/gsd-x`,
`.../ucep`; cognitive-resource-os ran in an isolated clone, its `ROADMAP.md:11-17`), declare the goal
with `--root <that worktree>`, and arm with `--cwd <that worktree>`. Peer commits then cannot move
the tree.
(b) Also `declare --scope-path` limited to campaign-owned paths (`vault/programs/cognitive-economy/`,
`.planning/workstreams/cognitive-economy/`, `tools/test_cognitive_economy_program.py`) -- fixes the
dirty-case rglob cost, but NOT the clean case (whole-repo HEAD^{tree}), so (a) is required.
(c) P6 order: commit everything -> reconcile/harvest every gate at that final tree -> `judge --record`
-> `--final`, with no commit in between (judge receipts land in the goal log under ~/.claude/state,
not in the tree; the ledger's final write must precede the gate run).

### G3 -- CRITICAL -- the existing verifier reads an `obligations` key that `status --json` never emits; every IMPLEMENTED pillar fails L5 forever

Claim: `tools/test_cognitive_economy_program.py` (already on disk, untracked) builds the SATISFIED set
from `data.get("obligations", [])` of `gsd_x_goal.py status --json`. That JSON has exactly the keys
goal, revision, tree, may_close, blocking, planes, epochs, last_seq -- no obligations. So `satisfied`
is always `[]`, and every pillar ending IMPLEMENTED_AND_VERIFIED (A, H, L, R are predicted so in the
frozen ledger) fails L5 at `--final`, however real its proof. The selftest cannot see this: it passes
a hand-built goal dict `{"may_close": True, "satisfied": ["ob-A"]}` (line 290), never the real
CLI output. Worse than a false RED: the only exit from an un-closable L5 is demoting the pillar,
which L6 permits with any existing "falsification" file -- the verifier pressures an unattended worker
toward fabricating falsifications of work that actually succeeded (a Goodhart path the plan s5 does
not name).

Evidence: `tools/test_cognitive_economy_program.py:244-246` (reads `data.get("obligations")`) and
`:290` (fixture); `tools/gsd_x_goal.py:145-152` (the JSON written; no obligations key);
`:160-162` (obligations are printed only in the non-JSON human form).
Fix: in the verifier, derive SATISFIED ids by importing the projection directly
(`modules.gsd_x.goal.convergence.project_convergence(gc.project(GoalLog(repo_id(root), GOAL_ID)))`,
disposition == SATISFIED) -- the verifier is campaign-owned, so no peer file is edited. Add a selftest
case that runs the REAL `status --json` against a throwaway goal store (`GSDX` goal-store env override
read at `modules/gsd_x/goal/log.py:102`) holding one SATISFIED obligation and asserts the verifier
sees it -- a positive control on the real producer, not a fixture.

### G4 -- HIGH -- plane coverage and obligation ordering are unspecified; P0 cannot oblige against a P1 verifier

Claim: closure blocks on (i) any plane never judged applicable/N-A, (ii) any ALWAYS plane (OUTCOME,
EVIDENCE, REGRESSION, UCR_CIF_LEARNING; FAILURE is event-carried) with no obligation or with every
obligation retired, (iii) any unretired, unsatisfied obligation, (iv) any undispositioned failure
event. ALWAYS planes cannot be declared N/A. The plan says only "one obligation per pillar" (P0); it
never maps pillars to planes, never declares the five optional planes (REALITY, SETUP_LEARNING,
TRANSFER, RECOVERY, OPERATIONAL) N/A, and gives no gate per obligation. `oblige` pins gate files at
acceptance and raises if a file does not exist, and the pin is immutable (a changed gate file ->
judge REFUSED). So a P0 obligation cannot name a gate that P1/P2 will write, and any later edit of a
pinned gate (e.g. fixing G3 in the verifier after obliging on it) breaks the obligation permanently
(only retire, which then reopens the plane).
Also: an obligation whose gate is `test_cognitive_economy_program.py --final` would make `judge`
re-run `--final`, which re-runs `judge` -- unbounded recursion (each level has timeout 3600 s,
verifier line 240-241).

Evidence: `modules/gsd_x/goal/convergence.py:42, 151-152, 333-346, 356-364`;
`tools/gsd_x_goal.py:86-97` + `modules/gsd_x/goal/git_state.py:114-117` (FileNotFoundError);
`modules/gsd_x/goal/judge.py:150-160` (pin mismatch -> REFUSED).
Fix: add to P0 a written plane map, e.g. OUTCOME = per-pillar ledger-clause gates; EVIDENCE = evidence
resolver gate; REGRESSION = `--selftest` of the verifier + named existing suites the campaign touches
(compound pipeline tests for R); UCR_CIF_LEARNING = a gate that checks the UKDL/CBR review record;
REALITY/SETUP_LEARNING/TRANSFER/RECOVERY/OPERATIONAL declared N/A with reasons (or REALITY obliged
with a `live` gate class if P4 builds anything). Order: P1 must land and commit the gate scripts
(and fix G3) BEFORE `oblige`; obligations that need P2 artifacts are accepted in P2 after their gate
script exists. Never use `--final` itself as an obligation gate; per-pillar gates should call
`check_ledger` scoped to one pillar (`--pillar X` mode) so a pillar can be proven independently.

### G5 -- HIGH -- Ralph no_progress halt is blind in the shared checkout (peer churn reads as progress); a stalled 24 h mission will not halt

Claim: the no_progress guard hashes HEAD + `git status --porcelain` + `git diff HEAD --shortstat` of
the WHOLE work dir. In the main checkout, 7 peer panes and a peer Ralph mission change that
fingerprint continuously, so `stalls` resets to 0 on peer activity and the mission is never halted for
non-progress, whatever its own worker does. The plan lists "live no_progress halt" as unproven (s1)
and relies on Ralph as the non-convergence owner (pillar J / N) -- in this configuration it cannot
fire. The converse risk the parent asked about (read-only measurement phases tripping the halt) is
low: GSD commits PLAN/SUMMARY/EVIDENCE per phase, which moves HEAD; but a measurement phase whose
worker writes nothing for 3 epochs WOULD halt in an isolated worktree, so measurement workers must
commit their EVIDENCE.md per epoch.
Evidence: `tools/gsd_mission.py:1649-1673` (fingerprint), `:1676-1686` (stall counting),
`:1549-1564` (halt at `NO_PROGRESS_EPOCHS = 3`, `:1646`).
Fix: same as G2(a) -- arm with `--cwd <dedicated worktree>`; then the fingerprint measures only this
mission. Add to every P2 measurement plan an explicit "commit EVIDENCE.md + ledger row" step so a
read-only phase still advances HEAD. Set `--max-hours 24` and a `--max-cycles` bound at arm
(`tools/gsd_mission.py:1915-1916`) so a non-halting loop is still bounded.

### G6 -- HIGH -- P3 /cpp-compound repair: the defect is real, but both repair surfaces are outside the approved envelope as written

Claim: the stall is real and recurring (memory: STUCK at steps 7+8 on 2026-09-21, 10-01, 10-02,
10-03; ~1/day; 220 files now sit in `.claude/cache/learnings/`). The memory names two fixes: (1)
`tools/compound_unattended.py` owns steps 7+8 in-process; (2) the producer stops emitting Session
Deltas as learnings. (1) `tools/compound_unattended.py` carries an UNCOMMITTED foreign diff
(measured now: `1 file changed, 118 insertions(+), 13 deletions(-)`, last commit ae106965 2026-09-01);
editing it entangles the mission with another writer's hunks and a pathspec commit would take them
under the mission's message (file-granular isolation). (2) The Session Delta producer is in
`~/.claude/hooks/hook-dispatcher.js` (grep "Session Delta"), the live, globally-loaded dispatcher
for every pane on the host -- a live-loaded edit is a production change for all 7 peer panes, of
the same class as the settings.json edits the Owner kept out of scope (s7.2). Steps 7+8 also mutate
`~/.claude/state/compound-learnings.json` (shared by ~280 project keys) and delete
`LEARNINGS_PENDING.md` -- destructive global state the Write tool refuses (memory 2026-10-03).
Evidence: memory `project_compound_loop_sticks_at_steps_7_and_8.md:21-64`;
`tools/compound_unattended.py:49, 153-158, 229-256`; git diff --shortstat measured this audit.
Fix: scope P3 to a NEW campaign-owned module (e.g. `tools/compound_steps78.py`: Node-equivalent
mkdir mutex at `compound-learnings.json.lock`, backup, sibling .tmp + rename, unlink marker,
rollback on unlink failure, case-sensitive JSON -- in Python `json` is case-sensitive, so the
PowerShell collapse does not apply) plus its test against a temp state dir; do NOT edit
`compound_unattended.py` (record the call-site change as a P5 Owner item, or as a handoff to that
diff's owner) and do NOT edit `hook-dispatcher.js` (producer fix -> P5 decision bundle). Running
steps 78 against the REAL global state file is a destructive effect: P3 proves it on a temp copy;
the live clear is either one Owner-authorized step in P5 or explicitly the existing manual Node
recipe. Pillar R's predicted IMPLEMENTED then needs either this narrower slice to count, or a
falsification artifact (L6) -- decide which in P0 before freezing.

### G7 -- HIGH -- the verifier's MERGED/DEFERRED evidence is trivially satisfiable (Goodhart path s5 misses)

Claim: 13 of 20 pillars are predicted MERGED_INTO_EXISTING_OWNER / DEFERRED_STRONGER_OWNER /
FALSIFIED / RESEARCH. For MERGED/DEFERRED the verifier accepts `{owner: <any existing path>,
commit: <any commit that is an ancestor of HEAD>}` -- HEAD itself qualifies, and every owner path in
the frozen ledger already exists. It does not check that the commit touches the owner or a handoff
file, that it postdates the freeze, or that the "handoff that landed" (docstring line 20) exists.
`measurement`/`falsification` kinds only need an existing file; `sha256` is optional (checked only if
present). The `all-deferred` mutant (line 300-303) is killed only because its evidence list is EMPTY;
an all-deferred ledger citing HEAD + an existing path passes L4. The judge is also run by the same
worker that authored the ledger (no `GSDX_GOAL_EPOCH` in a Ralph worker, `judge.py:125-128`), so
"independent judge" is nominal.
Evidence: `tools/test_cognitive_economy_program.py:61-69, 87-92, 153-157, 187-208, 300-303`.
Fix (verifier is campaign-owned): (1) `commit` evidence for MERGED/DEFERRED must be a commit that
(a) is not an ancestor of FROZEN_AT (i.e. landed after the freeze) and (b) touches a declared
`handoff` file under `vault/programs/cognitive-economy/handoffs/<pillar>.md` that names `[<pid>]`
and the owner path; (2) `sha256` mandatory for file/measurement/falsification/prg/owner_decision;
(3) `measurement` files must carry the frozen denominator id and the command that produced them;
(4) add mutants "deferred-citing-HEAD", "measurement-without-denominator", "evidence-without-sha".
(5) the P6 judge runs in a fresh session or as a gate epoch via `reconcile --apply`, not in the
worker that wrote the ledger.

### G8 -- MEDIUM -- frozen pre-registration carries a dangling owner path; once frozen it cannot be corrected

Claim: pillars L and R name owner `commands/cpp-compound.md`; it does not exist in the repo (the
command lives at `~/.claude/commands/cpp-compound.md`). L2 forbids any change to `frozen` after the
FROZEN_AT commit, so a P0 freeze makes the bad pointer permanent and any evidence citing the frozen
owner fails L4 "owner ... does not exist" if copied verbatim.
Evidence: `vault/programs/cognitive-economy/ledger.json:61, 67`; Glob: only
`C:\Users\User\.claude\commands\cpp-compound.md` exists; verifier `:138-139` (L2), `:199-200`.
Fix: before the P0 freeze, run an owner-path existence check over `frozen.pillars[].owner` (add it as
an L1 clause in the verifier so it is permanent) and correct L/R to the real paths
(`tools/compound_unattended.py` + the absolute `~/.claude/commands/cpp-compound.md`, which the
Resolver accepts via `Path(rel).exists()`).

### G9 -- MEDIUM -- workstream bootstrap is under-specified for /gsd-autonomous; arm does not run the freshness gate

Claim: (a) `arm` accepts `--workstream` and the worker DOES receive `--ws cognitive-economy`
(`bind_workstream`, appended to the command, and a card line instructing `workstream.set`) -- this
part is sound. (b) `arm` never calls `gsd_mission_freshness.py`; the CLI has no mission-terms flag
(`create()` accepts `mission_terms` but `_cli` never passes it), so freshness is a separate manual
step whose result arm does not read. Since the same author writes ROADMAP.md and picks the terms, it
is close to tautological; it guards only against arming the wrong workstream name. (c) The plan
creates only ROADMAP.md + STATE.md; the precedent workstream also has REQUIREMENTS.md, which GSD
init reads per-workstream (`requirements_path`) for plan/verify. Phases are named P0..P6; GSD
discovers phases from `### Phase N:` headings and checkbox bullets, so the P-labels must be written
as `### Phase 1: ...` with Goal / Depends on / Requirements / Success Criteria blocks like the
precedent, or discovery returns nothing and the worker reports "All phases complete" on epoch 1
(`autonomous.md:173-181`) -- a false DONE of the GSD layer (the done-gate would still fail, so the
mission would then churn).
Evidence: `tools/gsd_mission.py:192-210, 213-238, 893-897, 1911-1953`;
`tools/gsd_mission_freshness.py:107-139`; `C:\Users\User\.claude\gsd-core\bin\lib\init.cjs:1228`;
`.planning/workstreams/cognitive-resource-os/ROADMAP.md:25-49`.
Fix: create ROADMAP.md (precedent format, phases numbered from 1; avoid Phase 0), STATE.md (precedent
front-matter incl. `workstream:`), REQUIREMENTS.md (one ID per pillar/obligation); before arming run
`node ~/.claude/gsd-core/bin/gsd-tools.cjs query init.manager --ws cognitive-economy` (or with
`workstream.set`) and assert `phases` length == 7; then freshness with distinctive terms (pillar
names, `cognitive-economy`, `ledger`), then arm with `--workstream cognitive-economy --max-hours 24`.

### G10 -- MEDIUM -- P6 writes the peer-hot UKDL file; with G2's isolation there is also no merge-back step

Claim: P6 "UKDL 3-level review" edits `vault/knowledge_base/ukdl-universal.md`, which is dirty with
peer hunks right now and received 5 peer commits in the last 7 h. In the shared checkout a pathspec
commit of that file takes the peers' uncommitted hunks under the mission's message (file-granular
isolation). In an isolated worktree (G2 fix) the edit instead lands on a side branch that conflicts
with that churn, and the plan has no merge-back step ("Push: none"), so the review either never
reaches the canonical UKDL or is merged by hand later.
Evidence: `git status --porcelain` (this audit): ` M vault/knowledge_base/ukdl-universal.md`,
` M .planning/STATE.md`, ` M tools/rollover.py`; `git log -- vault/knowledge_base/ukdl-universal.md`:
b826a504, 097613b1, 409efa3f, 455c3514, 63908e7f (3-7 h ago).
Fix: the mission writes UKDL/CBR entries only to campaign-owned files
(`vault/programs/cognitive-economy/ukdl-proposals.md`, `.../cbr-review.md`) -- the verifier's L8
already only needs a review FILE to exist; promotion into `ukdl-universal.md` and the merge of the
mission branch into `feature/knowledge-acquisition` become explicit items of the P5 Owner bundle
(or a post-mission interactive step), never an unattended edit.

### G11 -- LOW -- driver for gate epochs is unstated; PP-GoalSweep + the worker can both drive the goal

Claim: obligations reach SATISFIED only through a gate epoch dispatched and harvested by the sweep
driver (`sweep_goal`), reachable from either the scheduled PP-GoalSweep (only for goals marked
`autonomous --on`) or `reconcile --apply`. The plan does not say which. If the goal is marked
autonomous AND the worker calls `reconcile --apply`, two drivers act on one goal; epochs are CAS-
guarded by sequence numbers, so the likely result is a refused append and a confused worker rather
than corruption, but it is avoidable.
Evidence: `modules/gsd_x/goal/sweep.py:394-414` (autonomous filter), `tools/gsd_x_goal.py:286-316`.
Fix: pick one in P0 and write it into the ROADMAP. Recommended: do NOT mark autonomous; the worker
drives with `reconcile --apply` (dispatch) + `reconcile --apply` (harvest) in a bounded loop, which
also lets it control the "no commit between proving and judging" order of G2(c).

## Checked and sound (no gap)

- `arm --workstream X`: the worker's command gets `--ws X` appended and the card tells it to run
  `workstream.set X` (`tools/gsd_mission.py:192-210, 893-897`). A mismatching `--ws` is refused.
- `gsd_x_goal.py declare` writes only the goal log under `~/.claude/state/gsd-x/goals/<repo-id>/`
  (`modules/gsd_x/goal/log.py:6-8, 100-102`); repo-id is the root commit, so a worktree shares it.
- No planned step edits `tools/rollover.py`, `context-watchdog.py`, `tools/gsd_mission.py`,
  `tools/usage_index.py`, `tools/fanout_ledger.py`, root `.planning/STATE.md`, `settings.json` or
  `modules/gsd_x/goal/*` provided G6 (compound_unattended.py, hook-dispatcher.js) and G10 (UKDL) are
  applied. `usage_index.py window` is read-only; `refresh`/`burn` write the shared index
  (`tools/usage_index.py:783-818`) -- P0/P6 should use `window` only.
- `oblige` does require existing gate files (pinned at acceptance) -- see G4 for the consequence.
- `retire` cannot reach SATISFIED and a plane whose every obligation is retired stays blocked
  (`convergence.py:227-231, 344-346`): the spine alone cannot be closed by retiring everything, but
  it CAN be closed with one trivially-passing gate per ALWAYS plane plus everything else retired --
  hence the ledger layer, and hence G7.

