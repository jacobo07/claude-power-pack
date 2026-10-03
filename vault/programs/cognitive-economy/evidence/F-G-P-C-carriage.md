# [F] [G] [P] [C] Re-derivation, verification and tool-schema carriage on D-W7

Frozen rules.
- F: "sibling re-derivation is a lever only if identical-dependency re-reads across sibling subagents are >= 3 % of
  D-W7 weighted".
- G: "reopened only if F finds recurrence with a valid identity boundary (same inputs, same dependency hashes)".
- P: "build only if verification (test/gate tool calls + their output carriage) >= 3 % of D-W7 weighted".
- C (tool half): "tool schemas: build lazy loading only if MCP/tool schema residency >= 3 % of D-W7 weighted".

## Instrument

`vault/programs/cognitive-economy/measure/carriage.py` (zero model calls). Decision inputs written in its docstring
and committed at `73d97127` BEFORE the run. Population: every transcript holding a D-W7 call, sidechain lines
included (the KSR original skipped them, which would drop every subagent transcript). Only D-W7 calls carry a price,
so every numerator sits inside the frozen D-W7 weighted denominator (3,325,101,725).

Carriage is the KSR construction (`vault/audits/ksr_archaeology/scripts/ctx_dead.py`): a tool result of T tokens
(chars / 3.6, ESTIMATE) is resident from the call after admission to the next compaction or file end; each resident
D-W7 call prices it by its own mix, T x 0.1 x cache_read/ctx + T x 2 x cache_write/ctx.

command: `cd vault/programs/cognitive-economy/measure && python carriage.py --measure --json carriage_out.json`
(result sha256 `a73745337c5251503a0859ce57a34456c8ff58d2734e4d1b74596f9e3d98ddbf`; full output
`measure/carriage_out.json`).

## Controls

- Population: 75,969 calls positioned = D-W7's 75,969; 1,541 transcripts, 0 unreadable; 183 sibling groups holding
  566 subagent transcripts.
- Detector selftest `python carriage.py --selftest` 6/6 PASS: a planted identical sibling re-read is found (weight
  exact), differing content is not an identity re-read (but is path-only), different parents are never siblings,
  pytest and a campaign gate are tagged as tests, a directory listing is not.

## Result (% of D-W7 weighted)

| pillar | decision input | value | rule |
|---|---|---|---|
| P | test/gate result carriage 0.3041 + issuing tool_use x5 0.1966 | **0.5007** | < 3 % |
| F | Read results in a subagent identical (path, offset, limit, sha256) to an earlier-spawned sibling's, 1,124 re-reads | **1.8793** | < 3 % |
| C-tools | ToolSearch results (deferred schemas loaded into context) | **0.0020** | < 3 % |

Reported, not deciding: F path-only matches 2.2314 %; parent->child identical reads 0.3584 %; all tool-output
carriage 25.71 % (of which Read 21.02 %, PowerShell 2.18 %, Grep 1.26 %); H's proof-class whole-turn weight 6.13 %,
which prices each turn's entire prefix (paid by any turn) and is not verification's own cost.

## Decisions

- **P: FALSIFIED_OR_REJECTED_BY_EVIDENCE.** Verification's own cost is 0.50 % of D-W7. Even the whole-turn figure
  (6.13 %) would not be the saving of proof reuse: a reused verdict removes the test call and its output, not the
  prefix the turn carries.
- **F: FALSIFIED_OR_REJECTED_BY_EVIDENCE.** 1.88 % < 3 %, and it is an upper bound on any saving: a sibling handed
  a shared materialization would still carry that content in its own context. Path-only (2.23 %) is also below.
- **G: FALSIFIED_OR_REJECTED_BY_EVIDENCE.** Its reopening condition is F >= 3 % with a valid identity boundary. F
  measured the identity boundary exactly (same inputs, same content hash) and found 1.88 %.
- **C (tool half): no build.** Lazy loading of MCP/tool schemas already exists in the harness (deferred tools +
  ToolSearch); what it loads costs 0.002 % of D-W7. Always-on built-in schemas live in the system prompt, which no
  transcript records: UNMEASURED here, and they are part of the floor owned by the skill-residency / K-slice
  programs. C's terminal is written with its skill/agent half (Phase 7).

Displacement: not applicable (no lever built). Saving: none claimed.
