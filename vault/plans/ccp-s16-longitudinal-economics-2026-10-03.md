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
  m5 re-drilled KILLED (27/28). NEXT: UKDL (horizon-constant, successor-join, torn-append traps).

## Not now
NEXT: the `decide` horizon/rehydration change (owner rollover.py); `gsd_epoch` 300k static threshold (c2/e9 lane);
the torn-append fix. LATER: live shadow on new sessions, bounded live experiment. RESEARCH: context live-range
eviction. REJECT: a new longitudinal controller, a new epoch type, a static % threshold.
