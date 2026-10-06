# Lesson: a GSD phase researcher paid 26.8M tokens for answers a 6-second search produces

Date: 2026-10-06/07. Mission: EDD (`m-ee81e1595007`, GEX44, workstream `edd`). Instrument:
`.planning/workstreams/edd/canary/autopsy/edd_autopsy.py` (transcript parse, message-id dedupe, tool-shape
classification, no model). Spec: laptop `vault/specs/edd-compiled-execution-canary.md`.

## Symptom
Armed with no token envelope (`token_estimate` None; only 40 cycles / 72 h). In 18 minutes it processed
32,062,568 tokens over 132 calls with zero obligations closed. The main worker (Opus, 30 calls, 5.22M) sat idle from
21:44:31 waiting on ONE `gsd-phase-researcher` (Sonnet) that made 102 calls for 26.84M.

## Evidence
- Classes (132 calls): evidence acquisition 99 calls / 23.98M (75%); state reads 15 / 2.82M; planning-file writes
  9 / 2.82M; tests 5 / 1.67M; control, spawn, narrative 4 / 0.77M. Semantic decisions: <= 3 calls.
- Researcher context per call 77k -> 407k; each call issued one grep, sed or Read.
- Main context 99k at call 0 (host floor) -> 224k after reading two GSD workflow documents into itself.
- The same questions (owners, importers, keyword locations for 81 concepts) were answered by
  `tools/gsd_dossier.py` in 6 s with no model: 67 KB dossier + refs.jsonl.

## Root cause
Context-residency rent, not model choice. A worker that acquires evidence one tool call at a time re-sends its
whole accumulated context on every call, so cost grows roughly with calls x average context (~quadratic in calls).
The GSD grammar routes deterministic repository archaeology through that worker, and then pays it again in the
planner and the executor (Orca replay: planner 121 calls/spawn, 23.5% of spend).

## Contributing causes
- No economic admission: cycle and hour limits are liveness limits and never judged tokens.
- The cost breaker and `hold` park; neither stops a turn already in flight. Only `claude stop` cut the spend.
- A phase was treated as a cognitive unit: Phase 1 is a scan, and a scan is mostly deterministic.

## Fix (this mission)
Stop + hold; supersede with `m-99b4cc7104f9` (6M estimate, 12M trip, Sonnet, 120k autocompact, compiled WU-1
packet); a zero-model dossier compiler; a done-gate written first and seen red.

## Prevention depth
Before: Owner question about cost after 16M. After: the dossier removes the evidence-acquisition class for scan
phases; the envelope bounds the attempt. Not yet automatic: arming an unbounded mission is still possible
(see UKDL candidates UC-13..).

## Gate traps found while building the fix
- A liveness check through `modules/liveness/reachability.py` cannot see `tools/` (it scans `modules/`): a check
  of a new tool through it passes by construction. Replaced by produced -> named -> consumed.

## Failure inside the fix: canary attempt 1 (m-99b4cc7104f9) BLOCKED by autocompact thrash
- Envelope set autocompact 120k from the plan's guessed "context ceiling 120k". Measured worker floor: 95,695 at call 1.
  Reading the 67 KB dossier crossed 120k; the host compacted at 22:08:08, 22:08:41 and 22:09:16, each time back to
  ~95k, and reported "request too large -- Autocompact is thrashing" -> mission BLOCKED at 22:13:27Z, 0 commits.
- Measured: 5 real calls, 489,159 processed. Compaction calls carry no usage rows in the transcript: their cost is
  UNKNOWN, not zero.
- Root cause: a context window chosen without subtracting the measured floor. Same class as the 2026-10-06 session
  cap set from a call-count guess (laptop memory feedback_budget_cap_must_be_projected_from_measured_floor).
  Second observation of the class -> immunity candidate: `gsd_mission envelope` should refuse an autocompact window
  below (profile floor from vault/config/route-floors.json + packet bytes + working margin).
- Repair: superseded by m-51b4175db047 with autocompact 250k (floor 95k + dossier ~25k + ~130k working).