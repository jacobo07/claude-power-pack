# CCP §16: longitudinal economics -- replay the existing rollover policy on measured costs (pane da)

Status: PROPOSED 2026-10-03, awaiting one Owner approval. Extends `ccp-s15-harness-validity-2026-10-03.md`.
Owners are unchanged: `vault/specs/interactive-context-rollover.md`, `economic-rollover-trigger.md`, `parent-context-epoch-rotation.md`.

## Reality (measured 2026-10-03 ~08:30 local)
- HEAD `b48a1393`, origin `07cb0adc`. 6 local commits: mine `b4935494` and `27d932d4`, plus 2a's `98875df2`, `bad37268`
  (C4.1 rent ranking), `6f5c3cf9` and `b48a1393`. 758 dirty paths.
- Rollover ownership: interactive = `tools/rollover.py` (`decide` break-even, shadow, SAFE_TO_FORGET gate, capsule,
  claim/refresh/exam/certify) + `context-watchdog.py` (45 % wall; economic trigger `139b19d0`/`65bb95be` evaluating at
  commits from 20 %). Missions = `tools/gsd_epoch.py` (turn end: continue < 300k, rotate above). The economic
  trigger's session `e4c2d161` has been silent since 04:01. `rollover.py`, `test_rollover.py` and `rollover_autotype.js`
  hold ORPHAN uncommitted hunks (mtime 09-30/10-01, f3b5ff1d refresh fix): UNOWNED, untouched.
- Ledger `state/rollover/rollover-ledger.jsonl`: 1,076 rows (09-28..10-03). 478 shadow decisions (econ 81, 47 would);
  reasons: not-at-boundary 248, usage 114, would 60, growth 26, >horizon 19, pressure 11. Break-even p10/p50/p90
  14.3/18.0/32.5 calls vs a FIXED horizon of 30 (`HORIZON_CALLS`, labelled ESTIMATE). Gates: 129 SAFE_TO_FORGET /
  13 NO_CAPSULE / 12 REFUSED; 130 resumes certified, 7 failed.
- Measured fresh epoch (128/130 certified successors, joined via `successor_claimed.claimant`): first call
  p10/p50/p90 118,744 / 127,876 / 147,781; median 16 calls and ~144k context before the first mutation.
  `decide` prices a fresh epoch as floor + capsule/4 (~150 tokens), with no rehydration term.
- Golden f319ce75 (session `8b2c7516`, 2026-10-01): 214 parent calls, 7 commits, first call 140,072, median 364,413,
  surface 76.2M, 46.3M above floor. It predates the economic trigger: only the 45 % wall fired, 3 min before the end.

## Findings
- F1 Remaining work is a constant (30) inside the decision band; it decides outcomes (latest econ row: 35.2 > 30 -> NO).
- F2 Fresh cost omits rehydration (16 calls median), so the break-even is understated.
- F3 BUG: 6 torn ledger rows. `rollover.ledger` appends large rows with a buffered text write; concurrent sessions
  interleave. Fix belongs in rollover.py, which is blocked by the orphan hunks -> deferred, readers count torn rows.
- F4 OBSERVABILITY: `resume_certified` carries only the predecessor (`rollover.py:877`); a successor needs a join.
  My first probe measured predecessors by mistake; caught by reading the writer.

## Architecture: B/C -- CONNECT, no new controller
`rollover.decide` stays the single policy. A NEW read-only tool `tools/rollover_replay.py` feeds it measured inputs
and replays it at hindsight-free boundaries. It writes receipts to a file, never to the ledger, and never clears.
Changing `decide` itself (a horizon range, a rehydration term) is a later commit, after the orphan hunks are resolved.

## Commits (EXECUTION after approval)
- C1 `fresh-cost`: successor first-call / calls-to-first-mutation distribution from the ledger + transcripts.
- C2 `boundaries <root>`: commit events by full-text match (RCA §17 fault), each with the context and call index at T only.
- C3 `replay <root>`: at each boundary, `decide` three ways: (a) as shipped, (b) horizon = leave-one-out range of
  calls-after-boundary from OTHER roots (PRIOR), (c) + measured rehydration. Verdict CONTINUE / WOULD_ROLLOVER /
  INSUFFICIENT_EVIDENCE. Exposure is a MECHANICAL interval, never a saving.
- C4 Real set: f319ce75 + 2 high-depth + 1 high-width + 2 short roots (negative controls must stay CONTINUE).
- C5 Mutants via the standard harness: horizon ignored, rehydration dropped, a boundary reading the future, exposure
  summed as saving. Then KV + UKDL (horizon-constant trap, successor-join trap, torn-append trap).

## Results (2026-10-03, Owner "y")
- C1 SEALED `7933ddc7` fresh-cost (n=129): first call 118,744/127,876/147,781; calls to first mutation 7/14/28;
  carried before it 0.79M/1.86M/4.53M (UPPER bound on rehydration).
- C2+C3 audit `vault/audits/ccp-s16-c3-audit.md` EXECUTE-WITH-FIXES, folded: prior = 878 index sessions ended
  before T (rolled ones excluded and counted, own capsule chain out), price book in force at T, capsule median
  before T, used_pct None (pressure NOT evaluated), model at call i, hook-denied / dry-run commits not boundaries,
  every verdict a `decide` call (survival share >= .75 / <= .25), exposure carries the write premium.
  `test_rollover_replay` 27/27 incl. positive control WOULD and short-horizon CONTINUE.
- C4 real index (read-only):
  | session | calls | boundaries | shipped would | prior W/C/I | +rehydration W/C/I |
  |---|---|---|---|---|---|
  | GOLDEN 8b2c7516 | 214 | 5 | 5 | 5/0/0 | 2/0/3 (first WOULD call 168) |
  | DEEP 26ff693c | 594 | 23 | 12 | 14/3/6 | 9/3/11 |
  | DEEP-FAST eace25b0 | 488 | 16 | 3 | 4/9/3 | 2/9/5 |
  | WIDE 5151270e | 194 | 7 | 4 | 6/1/0 | 1/1/5 |
  | SHORT b620e9e2 | 27 | 2 | 0 | 0/2/0 | 0/2/0 |
  | SHORT c69c0ac3 | 46 | 0 | - | - | - |
  Golden: first commit at call 96 (resident 353,751, n*=25.6); mechanical exposure if rolled there 17.5M-19.7M
  read-token eq (hindsight, NOT a saving; total excess 46.3M); at call 168: 5.9M-8.1M.
- NEGATIVE CONTROL: PARTIAL. Every CONTINUE in the set comes from decide's 150k growth gate; no CONTINUE was
  produced by the remaining-work prior (its shares stayed >= .71 at every gated boundary). A horizon-driven
  NO_CHANGE is shown only on the fixture. Open: find a real short-horizon, high-growth boundary.
- FALSIFIED (RCA §17 "7 git commit commands"): the golden session has 5 successful commits; the other 2 matches
  are handoff texts ("Committed: ..."). RCA text kept; correction lives here.
- C5 drills (tools/mutation_drill.py, isolated copy + control, 2026-10-03): m1 horizon ignored KILLED by
  V-RR-SHORT-HORIZON-CONTINUE; m2 rehydration dropped KILLED by V-RR-REHYDRATION-COUNTS; m3 boundary reads the
  future (resident = max ctx) KILLED by V-RR-BOUNDARY-NO-FUTURE; m4 exposure as saving (no premium, no C, label)
  KILLED by V-RR-EXPOSURE-NOT-A-SAVING. Each 26/27, only the named gate red. Extra probe m5 write premium dropped
  SURVIVED (27/27: the gate checked label + interval only) -> new V-RR-EXPOSURE-CARRIES-WRITE-PREMIUM pins the value;
  m5 re-drilled KILLED (27/28) `736c0075`.
- UKDL SEALED `63908e7f`: T-HORIZON-CONSTANT-DECIDES-INSIDE-ITS-BAND-001,
  T-SUCCESSOR-JOIN-CERTIFIED-ROW-NAMES-PREDECESSOR-001, T-TORN-APPEND-CONCURRENT-JSONL-001.
  OPEN: a real horizon-driven CONTINUE (negative control PARTIAL); decide change + torn-append writer fix
  wait on the orphan rollover.py hunks (Owner call).

## §16.1 C6-C9 -- revised plan (Owner "y" to Q1-Q6, 2026-10-03)

Reality scan (read-only, 2026-10-03 ~09:40 local, HEAD `fa0babac`, 15 ahead of origin, 769 dirty):
- OWNERSHIP. rollover.py refresh() hunks (~562-580, ~844) + 2 tests in test_rollover.py were written by session
  `a4849588` (Orca-X, Edit 2026-09-30T08:06Z, 52/52), never committed in PP; its chain a4849588 -> 7e4bd310 ->
  b5a94e97 is silent since 10-01 and no open obligation carries the change; 3 peer commits hunk-isolated around it.
  Owner RELEASED them to this pane (Q1). `hooks/rollover_autotype.js` hunk (stdin budget 45 s): author not traced,
  NOT released, stays untouched.
- F5 AUTHORITY. decide() is live: rollover_econ.py writes decisions/<sid>.json, the watchdog asks /kclear on
  would_rollover. The ledger is CONTROL state: `_last_seal` (rollover.py:422) reads capsule_sealed rows for the gate.
- F6 MECHANISM (corrects T-TORN-APPEND in 63908e7f). Every fragment follows a COMPLETE shadow row and is the tail of
  another, longer row: two writers seek to the same end, the second overwrites the first. One fragment = one whole
  lost event; an overwrite by an equal-or-longer row leaves no trace. Scratch reproducer (6 procs x 400 rows):
  open("a") lost 676-701 / 318-329 fragments; os.open(O_APPEND)+os.write lost 748 (NOT a fix on Windows); exclusive
  lock lost 0. A lost capsule_sealed row fails CLOSED at the gate (availability, not safety).
- F7 CUSTODY LEAK (new). a4849588 sealed SAFE_TO_FORGET with uncommitted edits in another repo: capsule `writes`
  keeps the last 15 paths (rollover.py:328) and dirty state is read for the cwd repo only.
- F8 the 14.3-36.9 band (n=383 priced shadow rows) is the spread of n* ACROSS states, not one decision's
  uncertainty. One decision is uncertain by rehydration (C/G, C measured p50 1.86M upper bound) and by horizon.
- Fresh cost re-measured (correct successor join, n=134): first call 119,188/128,099/147,972; calls to first
  mutation 7/14/28; carried 0.87M/1.86M/4.53M.
- Same-path constants: MIN_GROWTH 150k (operational, unmeasured default; produced every CONTINUE), chars/4
  (estimate), pressure 70 % (safety default), HORIZON_CALLS 30 (unmeasured default). Only HORIZON changes now.

Decisions: Q2 UNDETERMINED/UNKNOWN -> no economic ask (45 % wall stays); Q3 custody leak REFUSES safe-to-forget;
Q4 lock timeout drops the row and reports it; Q5 0.75/0.25 survival shares kept as declared policy parameters;
Q6 historical replay is evidence level HISTORICAL_REAL, closure still needs a live shadow.

Commits (EXECUTION):
- K1 UKDL dated amendment to T-TORN-APPEND (mechanism + wrong O_APPEND fix), hunk-isolated.
- R1 rollover_replay `prior --write`: artifact {values, n, sessions, censored, window, computed_at, expires,
  rehydration p50/p90, source} under the rollover state dir; tests + drills.
- R2 historical negative-control search (all index sessions with commits, hindsight-free) -> vault/audits.
- H0 the released refresh() hunks committed as-is, attributed to a4849588, after test_rollover passes.
- W1 ledger(): exclusive lock around the append (reuse an existing lock idiom), bounded wait; on timeout or OSError
  the row is dropped and reported (stderr + `ledger_write_failed` sidecar count), never written torn. Multi-process
  race gate (old shape red as control); drill lock-removed -> KILLED.
- D1 decide(): horizon/rehydration as evidence (basis MEASURED / UPPER_BOUND / UNKNOWN). ROBUST_ROLLOVER iff share
  >= .75 at n*+C/G; ROBUST_CONTINUE iff share <= .25 at n*; else UNDETERMINED. would_rollover True only for
  ROBUST_ROLLOVER at a boundary (pressure/growth unchanged). An int horizon (replay sweep) stays accepted, labelled.
  Rows record obligations count (Stage-2 evidence only). Drills: UNKNOWN coerced to 30, range ignored, C dropped.
- S1 custody: safe_to_forget refuses when any session-written path outside the capsule repo is dirty in its repo;
  writes no longer truncated for the check.
- P1 Production Reality: live ledger fragment count unchanged after W1 over real concurrent sessions + one real
  shadow receipt carrying the new evidence fields.
- V1 plan / KV / UKDL / CBR review.

Audit `vault/audits/ccp-s16-1-audit.md`: EXECUTE-WITH-FIXES, 12 gaps (3 HIGH). Folded:
- G1 decide() stays PURE: callers (observe, rollover_econ.evaluate) load the evidence and pass it; decide's
  default int horizon and V-ROLLOVER-BREAKEVEN unchanged. Missing artifact -> UNKNOWN, never 30.
- G2/G3 G >= 150k after the growth gate caps C/G at 12.4 (p50) / 30.2 (p90) calls; ROBUST_ROLLOVER stays
  reachable (C4 set: 14 WOULD vs 29). Basis label `UPPER_BOUND_P50`. No ROBUST_CONTINUE claimed.
- G4 the prior artifact needs a named refresher and records the usage-index freshness.
- G5/G6/G11 folded into W1 (callers check ledger's return; 2 s; docstring cites gsd_mission._Lock,
  sealed_receipt -- `_last_seal` above was a wrong name).
- G7 S1 amends interactive-context-rollover.md §4 ("dirty recorded, not refused"); D1b rewrites §5 (horizon).
- G8 S1 predicate: the session's FULL write list; for paths in a repo other than the capsule's, one path-scoped
  `git status --porcelain --untracked-files=all -- <paths>` sealed into the capsule and judged in completeness();
  non-repo paths warn, git failure refuses; Bash-written files are invisible (declared).
- G9 P1 states a window and expected count (baseline ~0.56 % torn rows/row) or reads INCONCLUSIVE; the race
  gate with its old-shape control is the primary evidence.
- G10 new order: W1 -> S1 -> R1 -> D1a (pure, evidence in) -> D1b (loader + refresher + spec §5).
- G12 debt: shadow/econ seal() overwrites a /kclear capsule (predates this plan); W1 writes LF rows.

Progress: K1 `455c3514`, H0 `1703e609`, W1 `38fc418c` (race gate 6/6, 3 drills KILLED, rollover 52/52,
econ 19/19, replay 28/28). R2 `vault/audits/ccp-s16-r2-negative-control.md`: 80 real sessions, 471
boundaries, 169 growth-gated, 302 judged by the prior -> 0 CONTINUE (prior or rehydrated); rehydration
moves 113/225 WOULD to INSUFFICIENT. Negative check stays PARTIAL; Stage 2 (state-conditioned prior) is
the evidence-earning step.

Progress 2 (2026-10-03): S1 `d34a0b4d` (custody 8/8, 2 drills KILLED; 4/40 recent sealed sessions would be
refused now, all uncommitted vault plans in the TUA-X-brand001 worktree), R1 `70fbb600` (prior 33/33, 2 drills;
real artifact n=2519 / 525 sessions / 127 censored, rehydration p50 1,856,237, build 177 s), D1a `7fefbc46`
(decide evidence 11/11, 3 drills), D1b `4bc970d6` (wiring 11/11, 3 drills; spec §5 rewritten, it said <= 20 while
the code shipped 30), UKDL `409efa3f` (T-CHECKPOINT-CUSTODY-SCOPED-TO-CWD-REPO-001,
T-UNCONDITIONED-PRIOR-CANNOT-SAY-CONTINUE-001).
P1 Production Reality:
- Decision: real shadow on session cf503730 -> economics ROBUST_ROLLOVER from evidence, n* 19.3, n*+C/G 26.0,
  share 0.79 / 0.753 at the pessimistic end (margin 0.003 over 0.75), would_rollover false (shadow has no start
  head -> no boundary). The fixed 30 no longer appears in the decision. POSITIVE control: real, shadow.
- Writer: 22 live rows since W1 (08:06Z), torn still 6, 0 ledger-failures; 0.12 fragments expected at the old
  rate -> INCONCLUSIVE (window too short). Primary evidence stays the race gate + its old-shape control.
- NEGATIVE control: PARTIAL. Synthetic reachability (V-DEV-ROBUST-CONTINUE); historical-real 0/302 (R2).
Ratchet: EXPERIMENTAL -- evidence-interval decide, custody check. CANDIDATE (one incident each, not promoted):
HR "an economic control decision must not hide decision-reversing uncertainty behind a point estimate"; PR
"concurrent event writer -> reproduce with a control -> repair -> reader compat -> failure observability -> PRG".
Debt: agent-solo-guard FP-AGENT-CONTRACT-IDENTIFIER hit 3x today (guard fix belongs to ~/.claude/hooks);
shadow/econ seal() overwrites a /kclear capsule (G12, predates this plan); hooks/rollover_autotype.js hunk
(author untraced, not released) still uncommitted.
NEXT: Stage 2 -- condition the prior on open obligations at the boundary (goal file at the boundary commit),
replay it hindsight-free, and look for the first real horizon-driven CONTINUE.

## §16.2 Stage 2 -- state-conditioned horizon (Owner "y" 2026-10-03; pre-registered before the data)

Hypothesis: open obligations in the session's goal file at a commit predict the calls left after it.
Reconstruction (hindsight-free): goal = last plan/spec/RESUMPTION file the session wrote at or before
the boundary call; content = the version COMMITTED at or before the boundary time (git log --before);
count = rollover.obligations_from (the same parser the live capsule uses, capped at 10).
Pre-registered falsification -- Stage 2 is NOT built if any holds:
- F-a coverage < 30 % of real boundaries (the evidence is too rare to condition a live decision on);
- F-b remaining-call distributions do not separate: the "0 or 1 obligation" bucket p50 is not below
  the 4+ bucket p25 (the count carries no usable signal);
- F-c the conditioned prior still yields 0 CONTINUE among growth-gate-passing boundaries.
If all pass: a conditioned prior (leave-own-session-out, sessions ended before T, same censoring as R1)
replays R2 hindsight-free; any CONTINUE found is HISTORICAL_REAL evidence, and live wiring waits for one.
Known bias: a plan committed with progress lags the working copy at T; a session that never commits its
plan is UNKNOWN, never zero obligations.

Instrument check (10:45, before the feasibility result): `rollover.obligations_from` parses 0 items from 33 of
the 40 most recent vault/plans files -- most plans keep open work in prose ("NEXT:", "Open:") rather than
under a next/pending heading. So a count of 0 cannot mean "nothing left": 0 must be split from
"no heading found" before any bucket is trusted, or F-a/F-b will read a parser gap as a signal.
In flight at the rollover: scratchpad `s2_feasibility.py` (output `s2_summary.txt`, rows `s2_rows.jsonl`)
and the prepared `s2_replay.py`; both under the session scratchpad of cf503730. NEXT: read s2_summary,
judge F-a/F-b with the parser caveat; if the parser is the limit, measure obligations with a parser that
reports NO_HEADING separately (do not change the live capsule parser without its own gate).

Stage 2 verdict (2026-10-03, session 84a5bc3c): NOT BUILT -- F-a FAILS, F-b FAILS/underpowered, F-c not run.
The cf503730 run left a 0-byte s2_summary and no rows (died before printing), so it was rerun as
`s2_feasibility2.py` with a local three-state reader (NO_HEADING / heading-empty / N; live parser untouched).
Sample: 60 most recent commit-bearing sessions in the 14-day window, 360 boundaries, wall-capped at 432 s,
so this is a sample of the window, not the whole window.
- F-a: COUNTED (heading found) 62/360 = 17.2 % < 30 % -> FAIL. Blind/unknown: 101 no goal written before T,
  66 goal never committed before T, 131 NO_HEADING (26 of them carry prose "NEXT:"). Ceiling even for a perfect
  prose reader = goal readable at T, 193/360 = 54 %.
- F-b: bucket 0-1 n=3 from ONE session (p50 132) vs 4+ p25 34 -> FAIL as worded, but n=1 session is no evidence
  either way. The stronger reading is 2-3 vs 4+: p50 52 (10 sessions) vs 48 (4 sessions), per-session medians
  52 vs 79 -- no monotone separation where there is data.
- F-c: moot (pre-registration: any falsifier holding stops Stage 2), so s2_replay.py was not run.
Not done, on purpose: rescoring with a prose "NEXT:" reader after seeing these numbers would be a new
instrument chosen post hoc. If wanted, it is a NEW pre-registration (instrument fixed first), and its F-a
ceiling is 54 %, while F-b already shows no signal among the counted rows.
Consequence: T-UNCONDITIONED-PRIOR-CANNOT-SAY-CONTINUE-001 stands; the negative control stays PARTIAL.

Stage 2 CLOSED (Owner "rec", 2026-10-06): no prose-reader re-registration. Reopen only with a new
pre-registration whose instrument is fixed before any data, and only if goal-file coverage at T rises
(today's ceiling is 54 %: most boundaries have no committed goal file yet). Live rollover wiring stays on the
evidence-interval decide from D1a/D1b; no horizon-driven CONTINUE path is built.
Remaining debt: hooks/rollover_autotype.js hunk unreleased; identity backup deleted only on the typed phrase.
G12 CLOSED (2026-10-06): shadow (`observe`) and econ (`rollover_econ.evaluate`) now seal into
`<state>/shadow-capsules/`, so the /kclear capsule the gate and /kresume read is never overwritten.
V-ROLLOVER-SHADOW-KEEPS-KCLEAR-CAPSULE + its control V-ROLLOVER-SHADOW-SEALS-ELSEWHERE went red on the old code
(gate: "capsule on disk is not the bytes that were sealed"), green after; rollover 57/57, econ 19/19, active 15/15,
capsule-v2 36/36, host-affinity 10/10, mission-capsule 49/49. test_mission_watchdog 14/15: its
V-MCW-CONTROL-PLAIN-ROLLOVER-KCLEAR fails identically on a clean HEAD worktree -- pre-existing, not this change.

## Not now
NEXT: the `decide` horizon/rehydration change (owner rollover.py); `gsd_epoch` 300k static threshold (c2/e9 lane);
the torn-append fix. LATER: live shadow on new sessions, bounded live experiment. RESEARCH: context live-range
eviction. REJECT: a new longitudinal controller, a new epoch type, a static % threshold.
