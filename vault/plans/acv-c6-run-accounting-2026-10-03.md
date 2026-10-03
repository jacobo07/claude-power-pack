---
covers: [agent-run-accounting, agent-telemetry, model-usage-attribution]
date: 2026-10-03
status: approved (Owner "y" = 1A 2A 3A 4:one live run 5A 6A; push as C5)
parent: vault/specs/agent-capability-virtualization.md (D3/D4, C6)
head_at_scan: 74c344e2
---

# ACV C6 -- run accounting: agent_run joined on resolution_id

## Reality (measured 2026-10-03, read-only)

- HEAD 74c344e2, 3 ahead / 0 behind origin (other panes); 710b834a (C5) in history. C6 surfaces
  clean; UKDL carries another pane's uncommitted hunk (not touched). Policy id 430c38f3552556d2.
  Live corpus: 0 agent_resolution rows, 7 historical torn lines.
- The ONLY ACV executor is tools/agent_carrier_run.py: a headless `claude -p` parent (stream-json)
  makes one Agent call to the carrier. Callers: tools/agent_bench.py and manual use. It takes a
  spec_id and never calls the resolver; no retry; it reads result.usage, not modelUsage; every
  early exit after the process ran (no tool call, dispatch blocked, empty reply) returns NO usage
  although tokens were spent; its `status` (MEASURED/UNMEASURED/DISPATCH_BLOCKED) is about the
  reply capture, not the execution.
- Interactive sessions dispatch carriers with the Agent tool and never call the resolver: that
  path is unobserved by ACV today.
- result event (CLI 2.1.285, all 4 saved real streams): `modelUsage` keyed by model, per model
  inputTokens / outputTokens / cacheReadInputTokens / cacheCreationInputTokens / thinkingTokens /
  webSearchRequests + costUSD (costBasis "list") + context/limits; it covers the WHOLE session
  (parent + carrier). `session_id`, `uuid`, `subtype` (success | error_*), `is_error` present.
  Carrier and parent models are observable per assistant event (`message.model`, sidechain =
  `parent_tool_use_id`). Carrier share separable only when the models differ (mech.stream: both
  haiku -> one merged entry). Local CLI 2.1.288.

## Decisions

1. Scope (1A): instrument agent_carrier_run (resolve-first mode + bench + manual). Agent-tool
   dispatches from interactive sessions stay OUTSIDE the envelope, named as unobserved; a
   SubagentStop hook integration is a later slice whose registration is the Owner's (HR-001).
2. Usage (2A): the run's cost = result.modelUsage per model, token fields copied verbatim
   (inputTokens, outputTokens, cacheReadInputTokens, cacheCreationInputTokens, thinkingTokens,
   webSearchRequests). usage_state: MEASURED (every entry has the four core token ints) |
   PARTIAL (modelUsage present, some entry lacks a core int) | UNMEASURED (no result event, no or
   empty modelUsage). Never zero-filled, never estimated, never summed into a new total.
   carrier_share: SEPARABLE (sidechain models observed, disjoint from parent models, and present
   as modelUsage keys) | UNSEPARABLE (overlap) | UNKNOWN (no sidechain message observed).
3. Price (3A): costUSD, costBasis, contextWindow, maxOutputTokens not recorded.
4. Identity: run_id = the executor's result.session_id (EXTEND, no new id); null when no result
   event (timeout) -> the signal still records that a process ran. resolution_id comes only from
   C5's resolve_and_record; never minted here. Agent identity = spec id + spec_hash (never paths).
   Model provenance: models_observed {parent, carrier} from message.model (OBSERVED) beside
   carrier_model_configured (CONFIGURED).
5. Cardinality: one resolution -> 0..n runs (0 when no candidate, refused, or never started;
   each invocation is its own run; no retry inside run()). One run -> exactly one terminal
   agent_run signal. No start event: the harness is one synchronous process, and every exit after
   the subprocess started (incl. TimeoutExpired and an unexpected exception) emits the terminal
   signal; a hard kill of the harness itself is the residual blind spot (named, not hidden).
   "Never started" (CLI missing, typed spec error) emits no run.
6. Signal: kind agent_run, schema agent-telemetry/1, via CO-12 record_signal (locked writer):
   resolution_id|null, run_id|null, spec, spec_hash, permission_class, carrier, purpose
   (manual|benchmark|resolved), executor_status (result.subtype | TIMEOUT | NO_RESULT),
   harness_status (existing record status), usage_state, model_usage (per model, tokens only),
   carrier_share, models_observed, carrier_model_configured, seconds. Never: prompt, mission,
   reply, transcript. Sink injectable (C5 pattern); telemetry failure -> rec["run_recorded"]=False
   + stderr line in the CLI, never a changed run record.
7. Unlinked (6A): a direct spec_id run emits resolution_id null and counts as unlinked.
8. Bench (5A): agent_bench passes purpose="benchmark".
9. Report: agent_metrics gains `runs` (derived from the same signals): total, linked / unlinked /
   dangling (resolution_id not in the corpus), by purpose, by executor_status, by usage_state,
   carrier_share counts, measured token sums per model and category over MEASURED runs only
   (labelled so), linked runs whose resolution was fresh vs cached, resolutions with zero runs,
   max runs per resolution. Refused labels: waste, saving, value, ROI, demand, necessary, cost.
10. C7 boundary: result consumption, verified advancement, goal outcome, marginal contribution,
    displacement -- none implemented; run_id + resolution_id are the join keys left for them.

## Commits

| # | scope | verification |
|---|---|---|
| C6-1 | agent_telemetry: usage_from_result, run_payload, record_run; agent_metrics `runs`; co_12 --report line; agent_carrier_run: parse_stream keeps result event + observed models, every post-start exit emits one terminal agent_run; tools/test_agent_run_accounting.py | real recorded streams as executor output (subprocess boundary replays them); timeout, no-tool-call, blocked, empty-reply, PARTIAL, UNMEASURED, SEPARABLE/UNSEPARABLE; one signal per run; sink failure; isolation guard + nonce; policy id unchanged; C5 suites green |
| C6-2 | resolve-first: agent_carrier_run `--resolve "<task>" --max-class`; resolve_and_run; bench purpose=benchmark | real resolver + replayed stream -> resolution row and run row share resolution_id; no candidate -> resolution row, zero runs; zero-run metric |
| C6-3 | mutation drills c6-* | each killed by its named gate |
| C6-4 | ONE live run (haiku parent, sonnet read-only investigator, tiny fixture) + docs (plan record, spec status, RESUMPTION) | live co_12 --report shows 1 resolution, 1 linked run with MEASURED usage |

Push after C6-4 green, linear history, no force.

## Execution state (context rollover, 2026-10-03)

C6-1 written, NOT yet run or committed (all uncommitted, all owned by this pane):
- agent_telemetry.py: RUN_KIND, USAGE_FIELDS/CORE_USAGE, usage_from_result, usage_from_results
  (last result; disagreement -> PARTIAL + usage_reason), carrier_share, run_payload, record_run
  (CO12.record_signal looked up at call time), _run_metrics -> agent_metrics()["runs"].
- tools/agent_carrier_run.py: parse_stream adds results / init_session / models; old body is
  _run_body(box); new run(..., *, purpose, resolution_id, sink) emits one terminal agent_run in a
  finally keyed on box["started"]; _account; _text; resolve_and_run; main --resolve/--max-class,
  RUN_NOT_RECORDED stderr.
- tools/agent_bench.py: purpose="benchmark" by keyword.
- co_12_telemetry.main: agent-runs text line.
- tools/test_agent_run_accounting.py drafted BEFORE the audit fixes: add to RUN_FIELDS
  run_id_source, executor_error, result_events; add gates for two-result disagreement (PARTIAL),
  executor_error (subtype success + is_error), post-start AgentSpecError (raise A.AgentSpecError
  from a patched carrier_reply -> exactly 1 agent_run), timeout with init session id in
  TimeoutExpired.output bytes (run_id_source init).
C6-1 SEALED (successor session e4701f02): the 4 audit gates landed (V-RUN-RESULTS-DISAGREE,
V-RUN-EXECUTOR-ERROR, V-RUN-POST-START-SPEC-ERROR, V-RUN-TIMEOUT-INIT-ID), each with its control.
Instrument fix found on the way: Replay patched the GLOBAL subprocess.run, so the resolver's own
subprocess probes were answered with the stream and counted as executor calls (V-RUN-RESOLVE-JOIN
saw 3 calls); now only argv[0] == "claude" is replayed, everything else passes through.
Measured: test_agent_run_accounting 19/19, agent_carrier_run 19/19, agent_telemetry 20/20,
agent_resolver 33/33, agent_bench 16/16, co12_telemetry 8/8, co12_readiness 8/8, co12_signal_race
5/5; policy id 430c38f3552556d2 unchanged. resolve_and_run + --resolve + bench purpose shipped in
this commit, so C6-2 is reduced to its gates beyond V-RUN-RESOLVE-JOIN / V-RUN-NO-CANDIDATE-NO-RUN
(zero-run metric is in V-RUN-METRICS). NEXT: C6-2 residue check, then C6-3 drills.

## Phase-4 audit (oneshot-architect-auditor, 7 gaps, none unsafe) -> all accepted

Supersedes the decisions above wherever they disagree.

| # | sev | gap | fix |
|---|---|---|---|
| 1 | MED-HIGH | every real stream has TWO result events (same session_id, same cumulative modelUsage, different per-turn usage / subtype / denials); "the result event" was undefined | use the LAST result; signal carries `result_events: n`; n > 1 with differing session_id or modelUsage -> usage_state PARTIAL (`usage_reason: result_events_disagree`); gate on the real two-result streams |
| 2 | MED | the CLI reports API failures as subtype success + is_error true | `executor_error` = last result's is_error verbatim (null without a result); metrics split executor_status by it |
| 3 | MED | AgentSpecError can be raised AFTER the process ran (bundle validation, state version) | `started = True` right before subprocess.run; emission in one try/finally keyed on `started`, never on the exception class; every exception re-raised unchanged; gate: post-start AgentSpecError -> exactly one agent_run |
| 4 | MED | C5's leak gate keys on query_fp, which agent_run lacks; a from-import would bypass the guard | record_run looks CO12.record_signal up at call time; replays get nonce session ids; V-RUN-LIVE-ISOLATION on run_id + resolution_id with a positive control |
| 5 | LOW-MED | a timed-out run had run_id null though the init event carries session_id; Windows communicate() after kill can hang on a pipe-holding grandchild | decode TimeoutExpired.stdout (bytes), take the first session_id; `run_id_source: result|init|none`; post-timeout hang named as a blind spot beside the hard kill |
| 6 | LOW | agent_bench calls run() positionally | new params keyword-only (`*, purpose, resolution_id, sink`); bench passes purpose by keyword |
| 7 | LOW | live totals are not stable evidence (shared corpus); run_recorded only on failure; seconds/spec_hash only on the MEASURED path | C6-4 keyed on the returned resolution_id (1 resolution + 1 agent_run carrying it, MEASURED); run_recorded always True/False; seconds + spec_hash on every post-start path |

Clean: modelUsage keys == message.model ids (SEPARABLE well-defined; keep the configured alias out
of equality tests); modelUsage is session-cumulative (mech: summed distinct message.usage == it);
policy id cannot move (agent_telemetry is NOT_POLICY, runner in tools/); no double emitter today;
replay proves parser + accounting, the live run proves the CLI boundary.
