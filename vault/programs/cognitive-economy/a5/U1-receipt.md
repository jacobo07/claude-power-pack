STATUS: DONE
COMMITS: 579db9aa
GATE: python3 -I tools/test_a5_u1.py -> A5_U1_PASS=15/15 (incl. mutant: broken dedupe key -> check red; byte-identical regen)
GATE: regen on corpus twice -> sha256 identical for data/calls.jsonl.gz, data/sessions.json, TRACE-REPORT.md (2.6 s)
Deliverables: tools/a5_trace.py, tools/test_a5_u1.py, A/data/calls.jsonl.gz, A/data/sessions.json, A/TRACE-REPORT.md
Headline (source: A/TRACE-REPORT.md section 0; corpus D/dws-transcripts, 311 files with calls):
- calls 10,985 (plan 10,985); ctx total 3.1008B (3.10B); p50 265,345 (265K); p90 429,546 (430K)  -> reproduces
- subagent share: calls 86.1% (86%), tokens 87.1% (87%)  -> reproduces
- files >60 calls: 64 carry 84.4% (64 / 84%); >150 calls: 14 carry 45.6% (14 / 46%)  -> reproduces
- first-call floor p50 102,225 (102K); floor = p50 x calls = 1.123B = 36.2% (1.1B / 36%) -> reproduces under that definition;
  sum(first ctx of file x calls of file) = 1.380B = 44.5% (alternative definition, reported separately)
- reads 3,946 / 1,060 paths; STATE.md 123; matrix 85; ROADMAP 35; `sleep 1` (shell head) 157; `until` loops 37 -> all exact
- tools per call 1.19 (plan "about 1"); 362 calls have no tool_use after the streamed-join (the old figure was invalid)
Labels (proxy, rule outcomes; ctx share): NOVELTY 38.4, MUTATION 22.3, PROOF 10.5, RECOVERY 9.8, CONTROL_LOOP 7.1, REDISCOVERY 5.4, STATE_READ 5.2, DELEGATION 1.3
Matrix: 20 commits of config/dws-completion-matrix.jsonc, 40 row-state changes, 10,789 calls in windows -> 269.7 calls per state change
  (plan quotes 424 calls per step: a different step definition, not reproduced; mine counts rows whose `state` field changed between commits).
Deviations: "session" = one transcript file (311 with calls; plan counts 311). Label priority DELEGATION>MUTATION>RECOVERY>STATE_READ>
  REDISCOVERY>CONTROL_LOOP>PROOF>NOVELTY (documented in tool header). poll flag includes Monitor tool (56 calls) and `status` word.
  Context rent object size is estimated from ctx growth on the next call (approximation, compaction ignored).
Not done / UNKNOWN: call-level matrix delta is window-based (by commit time), not causal.
HANDOFF NOTE: U2/U3/U7 can read A/data/calls.jsonl.gz (fields: session,parent,side,agent,seq,ctx,out,tools,reads,edits,sh,cmd,poll,proof,err,label).
