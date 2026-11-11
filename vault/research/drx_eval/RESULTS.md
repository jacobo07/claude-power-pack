# DRX U6 — v0.3.1 vs v0.4.0 on 3 fixed missions (2026-11-11)

Raw numbers: `COMPARISON.json` (from `python tools/drx_compare.py baseline_v031 v040 --json COMPARISON.json`).
Same missions, same config (12-query cap, depth 2, breadth 3, Haiku 4.5 via isolated `claude -p`), engines
run from frozen snapshots, sequentially, same afternoon. **n = 3 per version, one run each: no variance
estimate. Read every difference below as a hypothesis, not a measured effect.**

| | v0.3.1 (baseline) | v0.4.0 (ledger) |
|---|---|---|
| Runs ending INSUFFICIENT | 0/3 | **1/3** (SQLite: DDG reset + 2 extraction timeouts) |
| Persisted learnings | **36** | 15 |
| Cited URLs | **55** | 15 |
| Queries used | 17 | 12 |
| Wall time | 3565 s | **1656 s** |
| Number-support (version-agnostic) | **24/25 = 0.96** | 9/10 = 0.90 |
| Claims with a verbatim quote in a hashed snapshot | not measurable (no ledger) | **14/15 = 0.93** |
| Ledger audit from disk | n/a | 3/3 ok (after the CRLF fix `c4030169`) |

## What v0.4.0 demonstrably adds
- Every persisted claim but one is bound to a verbatim passage, with offsets, in a stored, hashed snapshot,
  re-verifiable by `evidence_ledger.py audit` without trusting the run.
- Of 26 quotes the extractor offered, 9 were not where it said. Triage by replay: **0 invented**, 4 verbatim
  in a different source of the same run (the report would have cited the wrong URL), 5 near-verbatim.
  The 4 are now re-pointed with the correction recorded (`290cdd3a`).

## Where v0.4.0 is worse, and the leading hypotheses
- **Yield (36 -> 15 learnings, 1 empty run).** Extraction LLM timeouts occurred only in v0.4.0 (2 vs 0;
  report error logs are truncated at 20, so these are floors). Leading hypothesis: asking for verbatim quotes
  lengthens the extraction output past the 120 s child timeout. Search failures were equal (3 vs 3).
  Not yet tested: a run with a longer extraction timeout, or smaller content blocks, at n >= 3.
- **Number-support 0.96 -> 0.90** is 1 unsupported claim in each version over very different denominators; it
  does not distinguish the versions.

## Verdict
v0.4.0 is NOT shown to be a better research engine overall. It is shown to make its claims auditable and to
catch misattributed citations; it currently pays for that with yield. Next experiment (owner of the next
slice): extraction timeout / content-size sweep, n >= 3 per arm, judged on yield AND verified-quote rate,
before any HELD_OUT case in `EVAL_SET.json` is run.
