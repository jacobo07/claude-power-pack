# External capability assimilation, T4–T12 — failures met and what each taught

2026-09-28, branch `feat/external-assimilation` (live on `feature/knowledge-acquisition`). Each entry:
symptom · root cause · why the existing defence missed it · repair · proof · pattern · status.
UKDL candidates are named; none is promoted here (`vault/assimilation/genesis-2026-09/UCR_CIF_STAGES.md`).

---

## T-TEST-LIVE-STATE-RECURRED-001 — a lesson written as a reading rule did not stop the writer (CLASS 0)

- **Symptom.** `test_gsd_long_run` wrote 46 `gsd-autorun-gsdlr-*` markers into the real
  `~/.claude/state` per run; `test_mission_watchdog` wrote the LIVE checkout's
  `vault/sleepy/context_snapshots.jsonl` from a worktree; `test_rollover_active_path` appended the
  real long-run ledger; three suites advanced the live `context-watchdog.log`.
- **Recurrence.** `T-LIVE-LOG-IS-NOT-LIVE-PRODUCER-001` (ukdl-universal) already recorded ~150 test
  rows in that same log — as a rule for *reading* the log. d10bd31 then fixed the capsules only.
- **Why the defences missed it.** Both earlier fixes were keyed to the symptom that surfaced. The
  writes came from module-level defaults (`gsd_autorun_marker.STATE_DIR`, the watchdog's `ROOT` and
  `HEARTBEAT_LOG`), which no grep for `Path.home()` in a test can see, and nothing executed a check.
- **Repair.** `4f27cff`: env overrides read only when set; suites redirect them.
- **Proof / regression.** `tools/test_state_isolation.py` loads an audit hook into every Python
  process a suite spawns and fails on any write under the real `~/.claude`; controls prove a
  synthetic write and a grandchild's write are seen; a named-but-missing suite fails. 29 suites.
- **Pattern.** When a lesson recurs, the missing artifact was an executable check, not better prose.
- **Status.** Candidate HR for CPP-wide (tests never mutate live operational state). Aperture: Python
  only — a node child is not observed.

## T-VACUOUS-MISS-GATES-001 — every "refused" gate passed because the setup had failed

- **Symptom.** First run of `test_verified_reuse`: all MISS gates green, HIT red.
- **Root cause.** `admit()` was refused (vendor accepts only `toISOString()` UTC, not `isoformat()`),
  so every lookup missed with "no admitted draft" — the right answer for the wrong reason.
- **Why missed.** A refusal assertion is satisfied by a subject that never reached the state under test.
- **Repair / proof.** `96f753c`: JS-canonical timestamps; tamper gate now demands the vendor's own
  re-hash refusal, plus a restore-control. 13/13.
- **Pattern.** Pair every refusal with a positive control on the same fixture (instrument-before-claim).
  Instance, not a new rule.

## T-WHOLE-FILE-FILTER-EMPTIES-EVIDENCE-001 — a fail-closed credential filter blocks 40 % of the source

- **Symptom.** A source packet of `tools/gsd_mission.py` held 0 of its 100,299 bytes.
- **Root cause.** The vendor's credential-line regex matches `pass` followed by `:`/`=`
  (`X_PASS=3/3`, `last pass: {x}`) and blocks the WHOLE file. Measured: 441 / 1,091 Python files,
  322 of them only for that word.
- **Decision.** Not worked around: loosening a credential filter is not a call for a measurement
  tranche, and the vendor bytes are provenance-locked. Recorded in the manifest and REPORT.md.
- **Status.** Owner-visible limitation; a night-research question now asks how scanners cut it.

## T-VENDOR-WINDOW-PAST-EOF-001 — an anchor near the end of a file never attached

- **Root cause.** genesis-task-context refuses a context window that runs past either end of a file
  (`range-out-of-bounds`) instead of clipping it — so the newest code, usually at the end, is the
  region that fails. Found by `test_handoff_packet` on its first run.
- **Repair.** `handoff_packet` resolves a unique anchor to a clipped line range (`c9f750d`).

## T-CARD-COMMAND-IN-THE-WRONG-REPO-001 — a documented command that only runs in one checkout

- **Root cause.** The packet reference told the successor to run `python tools/source_packet.py
  --verify`, relative; mission workers run in OTHER repositories.
- **Repair / proof.** Absolute path; `V-HPKT-VERIFY-*` executes the command exactly as the card prints it.
- **Pattern.** documented-capability-must-be-executable, applied to generated text.

## T-PREREGISTERED-BUT-UNTESTABLE-001 — an experiment whose candidate arm could not hold the answer

- **Symptom.** exp-successor-packet-001's packets: one cut at the excerpt budget, one blocked whole.
- **Why missed.** Registration froze hashes, not usefulness. Nothing checked that the candidate arm
  contained what it was meant to deliver.
- **Repair.** 001 withdrawn before any run (WITHDRAWN.md); 002 refuses to register unless every
  candidate packet is COMPLETE.
- **Pattern.** Inspect the registered material of each arm before the first run; make "the arm
  carries its treatment" a registration precondition.

## F-REFERENCE-IS-NOT-A-LEVER-001 — finding, diagnostic scope

A hash-bound packet reference on the successor card was cost-neutral (+0.08 % tokens) and
quality-neutral (4/4 vs 4/4). Each fresh headless successor re-read ≈ 167 k resident tokens per turn
in both arms. Card bytes are noise; turn count and bootstrap size are the lever. Two cases: refutes a
large effect, cannot establish a small one.

## T-CANONICAL-OWNER-UNWIRED-001 — the right owner can itself be dead

- **Symptom.** The Task Ledger's canonical owner (Goal Spine, `gsd_x/goal`) has no live invoker: no
  command, hook or scheduled task reaches `tools/gsd_x_goal.py` (positive control found
  gsd_mission's three), no VPS cron either.
- **Decision.** Merge into the owner anyway (attribution + AST ratchet, `fe2be9c`), status PLANNED,
  mission PARTIAL on that item. A parallel ledger would have been live and wrong.

## T-USER-TIMER-WITHOUT-LINGER-001 — a scheduled job with no runner

- **Symptom.** The night-research timer installed and listed, `linger=no`: a systemd user instance
  stops with the last session, so the timer would never fire at night.
- **Repair.** `loginctl enable-linger` on the VPS; verified `linger=yes`.
- **Pattern.** "Installed" is not "will run"; check the substrate that executes the schedule.

## T-ANCHOR-ON-A-MOVING-HEAD-001 — a resumption anchor that rotted, and a repair that almost repeated it

- **Symptom.** The rollover RESUMPTION's anchor named the branch's last three commits; 20 later they
  were wrong, and its "no crossing observed" was contradicted by six `resume_certified` rows.
- **Near-repeat.** The first rewrite named `42da3d1` as a rollover.py commit; the file's own log
  showed it never touched rollover.py. Verified before committing (`75276d2`).
- **Pattern.** Anchor a resumption on the subject's own history (`git log -- <file>`), and measure
  every anchor you write.

## T-UNCOMMITTED-PHASE-INVISIBLE-TO-WORKTREE-001 — the smoke mission that could not start (T11)

- **Symptom.** Mission `m-27f9f1ab9fb6` ran one worker, made no commit, then the supervisor held
  the relay every 5 min: "GSD parses 0 phases from ROADMAP.md".
- **Root cause.** The phase was added with `gsd-tools phase add` but not committed. `/gsd-autonomous`
  works in a fresh git worktree cut from HEAD, so its roadmap never had the phase; the supervisor
  judges that worktree (correctly) and holds on NO_PHASES.
- **Why missed.** `gsd-tools query progress` on the main checkout listed the phase: the instrument
  asked the wrong tree -- the one the worker would never read.
- **Repair.** Committed in the smoke repo (`e6275c3`); the stuck mission ends at its own 1.5 h budget.
- **System trap left open.** A persistent NO_PHASES hold has no escalation short of the mission
  budget; a mission can idle its whole budget on a setup error.
- **SUPERSEDED 2026-09-28 ~21:05Z** by T-FIX-IN-THE-TREE-THE-JUDGE-DOES-NOT-READ-001 below: the
  root cause above was wrong and its repair landed in a tree the supervisor never judged.

## T-FIX-IN-THE-TREE-THE-JUDGE-DOES-NOT-READ-001 — the second T11 smoke stalled identically (CLASS 0)

- **Symptom.** `m-860e4176f1d6` (armed 19:49Z) — worker `0704c6a9` crossed the smoke's 22 % test
  wall 90 s into its first turn (flag `pct 26`), handed off, went idle. Every sweep pass then held
  the relay on `gsd NO_PHASES` with the mission RUNNING; 5.7 M input tokens, 0 commits. The handoff
  read it as "turn ended and nothing re-invoked the model; Ralph not opted in". Both false: the
  sweep (the documented continuation owner) judged the idle worker every pass and refused.
- **Root cause (measured, `gsd-tools query init.manager` run in each tree).** The worker works in the
  worktree `.claude/worktrees/gsd-autonomous-run`. Its STATE.md named milestone v1, shipped and
  collapsed into `<details>`, and Phase 9 sat outside any milestone, so GSD scoped the phase list to
  a finished milestone: 0 phases. The root checkout parsed 9. The first repair (`e6275c3`) edited
  the ROOT roadmap -- the tree the judge never reads -- so nothing changed. Switching the worktree's
  STATE to v2.0 with GSD's own `state.milestone-switch` made GSD answer 1 phase at once.
- **Failed defenses.** (1) The earlier entry's instrument asked the root tree (the lesson it wrote
  down, "ask the tree the worker reads", was not applied to its own repair). (2) The supervisor's
  refusal was correct but unbounded: RUNNING for the whole budget. (3) The T11 wall (22 %) sat
  barely above the 16.4 % fresh-session floor (164 k of 1 M measured at the first call), so no epoch
  could ever end a turn below the wall: same-epoch continuation was unobservable by design.
- **Repairs.** `551bdee` bounded hold (NO_PHASES x2 / UNAVAILABLE x6 -> BLOCKED; only OK relays;
  8 V-MC-GSD gates, 2 mutation drills KILLED). `ad8f398` a `<synthetic>` quota row no longer reads
  as context 0 (m-d82c7cb6b87e continued a ~336 k worker on "context 0"). Fixture: v2.0 milestone
  via the SDK handler.
- **Race I caused.** The STATE switch landed 40 s before a sweep pass; GSD answered OK and the
  supervisor rotated m-860 to epoch 2 (CONTEXT_ROTATION, trigger wall) with its old 22 % wall. The
  hazard was named one step earlier; the order "retire the mission, then repair" was not applied in
  time. Rule: never repair a fixture a live mission's judge reads until that mission is terminal.
- **Pattern.** Before repairing what a judge refused, run the judge's own query in the tree the judge
  reads, and make the repair there. A green instrument run in another tree is not evidence.

## Red team R1 (0 critical, 0 high, 4 medium, 6 low) -- repaired in this session

M1 hand-off packet rooted at a stale `work_dir` (now the transcript's `effective_workdir`,
`V-HPKT-LIVE-WORKDIR`) · M2 a later continuation cause relabelled an epoch's route (founding cause
kept, `V-ROUTE-FOUNDING-CAUSE`) · M3 reuse admitted a draft under bytes it was not written about
(compile-time hashes, `V-REUSE-COMPILE-BYTES`) · M4 the night-research host-refusal gate would run a
real pass on the VPS (status mode; not applicable there) · L six more watchdog suites wrote the real
~/.claude (shared `_live_state_isolation.isolate`, `CPP_WORK_STATE_DIR`; ratchet now 38 suites) ·
L admit exception crashed a VALID validate (caught) · L installer rewrote line endings (both kept).
Open LOWs, recorded: refused launches absent from routing metrics; packet block before the note in a
tail-truncated card; revisions narrowing scope paths not flagged as weakening.

## For the rollover owner (not repaired here)

Session `8167513f`: `reset_gate` REFUSED ("capsule on disk is not the bytes that were sealed"), then
the capsule was claimed and certified. Whether /kresume must refuse a capsule its own gate refused is
that spec's decision.

---

## T4–T7 families (reported in the handoff, captured here for the first time)

| id | failure | repair |
|---|---|---|
| T-REVIEW-BINDS-THE-MOMENT-NOT-THE-READ-001 | approval tied to the bytes on disk when the bundle was built, then when `--ticket` ran; an old approval could pass | one-time nonce the reply must echo (`8f82e11`); known limit A->B->A recorded in code |
| T-UNKNOWN-SEVERITY-APPROVES-001 | modules/code_review approved a review whose finding said "Major" | unrecognised severity -> INCOMPLETE (`2faeeaf`) |
| T-IMPACT-BY-FILENAME-001 | audit_cache `depends_on` is stem-resolved; 8 of 25 suites linked to their subject | change impact from AST imports (`6fd3102`) |
| T-UNSTATED-WORKER-CONSTRAINT-001 | a batch reviewer refused for an output bound its contract never stated | bounds in the task contract, pinned to the vendor literals (`d71f615`, `358f7e5`) |
| T-PATH-IDENTITY-001 | symlink vs target, relative vs absolute, other repo vs same path string: missed and invented overlaps | one keying path, repo namespace by common git dir (`358f7e5`) |
| T-STALE-EXPECTATION-AFTER-MIGRATION-001 | watchdog control still expected compaction after rollover became default | inverted in place, kill-switch control keeps the old path (`6fdd61a`) |
| T-CLAIM-BEFORE-CERTIFIABLE-001 | /kresume claimed capsules no successor could certify, starving real sessions | refuse before claiming, report skips (`d10bd31`) |
