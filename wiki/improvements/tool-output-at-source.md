---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research, 2026-10-02-token-economy-internal-inventory]
status: IDEA
effort: M
graduated_to:
---

# Shrink tool output at its source (main thread)

## Problem

Tool results are 78.4 % of context growth (Read 56.5 %, PowerShell 26.0 %, Grep 9.3 %)
([[2026-10-02-token-economy-internal-inventory]]). Once in context, each result is re-read by
every later call. The main thread is 72 % of estimated spend with context p50 305k
([[token-economy-levers]]).

## Evidence

- Hiding old tool outputs (10-turn window) cut cost 52 % and raised solve rate 2.6 % on
  SWE-bench Verified; as good as LLM summarising and cheaper (JetBrains, tier A)
  ([[2026-10-02-token-economy-external-research]], Q4).
- Context editing cut tokens 84 % in a 100-turn vendor eval (same, Q4).

## Why PP cannot copy that directly

Claude Code exposes no switch to mask old tool results in an interactive session (ABSENT as a PP
lever; the API's context editing is not a Claude Code setting). CCP C5 owns growth inside
subagents only, as a plan. So the reachable form is to make outputs small before they land.

## Proposed steps

1. Measure which calls produce the largest results: top 20 by tokens over 7 d, by tool and
   argument shape (full-file Read vs paged, unbounded PowerShell output).
2. For the top shapes, pick the cheapest fix: a hook that refuses or trims (e.g. a Read of a large
   file without `limit`), a filtered wrapper, or routing the work to a subagent that returns a path.
3. A/B on the same task before claiming a saving (cache effects make per-call estimates misleading).

Risk: refusing large reads can cause extra calls; step 3 decides.

Related: [[rtk-powershell-gap]], [[lean-always-loaded-context]].
