# D1 spend meter -- execution-economics program (processed = input + cache_write + cache_read + output)

Instrument: `tools/usage_index.py refresh` (status OK, pending 0), then SUM over `calls` filtered by `session`
(per-program, not estate-wide: an estate window would charge other panes' work to this cap). Subagent calls carry
the parent session id (is_sub), so children are included. GEX44-side model calls are NOT in this laptop index and
must be added from GEX44 transcripts when any occur (none yet: GEX44 work so far was ssh + deterministic python).

| reading (UTC) | scope | calls | processed |
|---|---|---|---|
| 2026-10-05 ~09:46 | pane c85f3eb9 since brief receipt 08:55:43 (first prompt after it 09:00:44: 19,366,817) | 54 | 21,804,560 |
| 2026-10-05 ~09:46 | pane e1cb7fc6 whole session so far (resume, Phase 1 close, Phase 2-4, auditor in flight) | 34 | 5,283,903 |
| | **total since brief** | 88 | **27,088,463** |

Reading: pane c85f3eb9 averaged ~404 k processed per call after the brief (a long-lived parent carrying ~400 k of
context). That is the program's own largest cost so far and is exactly the "long-lived session carrying context
after last use" the brief targets. Whether the D1 cap counts pre-decision spend is an Owner question (asked
2026-10-05); until answered, the conservative reading applies.
