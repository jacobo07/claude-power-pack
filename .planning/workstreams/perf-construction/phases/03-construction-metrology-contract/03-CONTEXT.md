# Phase 3: Construction metrology contract - Context

**Gathered:** 2026-11-22 (unattended; no discuss step; decisions below are the planner inputs, recorded for traceability)
**Status:** Ready for planning
**Plane:** GEX44 (Linux, Python 3.12.3, stdlib only). The Owner's complaint is the LAPTOP; anything judging laptop hooks, RAM or transcripts is LAPTOP-ONLY / UNJUDGED and gets a procedure plus a falsifier, never a GEX44 number standing in for it.

<domain>
## Phase Boundary

Requirement PERF-03: TTFMC / TTFUR / TTVD events with p50/p90/p95 and censored samples, implemented in the owner chosen by D1.

ROADMAP success criteria (binding):
1. Start/end points of TTFMC, TTFUR, TTVD defined in writing; implemented as events in the D1 owner.
2. Distribution report (p50/p90/p95, N, censored count) runs over real transcripts of THIS host and says GEX44 plane.
3. States MEASURED / FAILED / TIMED_OUT / INCONCLUSIVE / SKIPPED_BY_POLICY / NOT_APPLICABLE / UNOBSERVED / UNAVAILABLE reachable, each tested.

Out of scope: Phase 4 (host-pressure admission, host state on each sample deciding INCONCLUSIVE), Phase 5 (hook critical-path audit), editing tools/bench_all.py or tools/test_bench_*.py (plan 02-03 owns them), the ROOT milestone, the live ~/.claude/skills/claude-power-pack install.
</domain>

<decisions>
## Implementation Decisions (locked for the executors)

- **D-01 (owner, from Phase 1 D1):** EXTEND `modules/capability_runtime` (01-EVIDENCE.md section 3). trace_context is disqualified by its authority rule (modules/trace_context/context.py:15-17) and has 0 production consumers. Fit caveats Phase 3 inherits and must handle: (a) the package scope is declared narrow and does not persist activation records (modules/capability_runtime/__init__.py:8-10): widening it is written down in the contract, with agent_telemetry as the signal-adapter precedent (modules/capability_runtime/agent_telemetry.py:2-15); (b) `invoke` has 0 production callers and no TIMED_OUT/censored/INCONCLUSIVE vocabulary, so the vocabulary is ADDED, `InvocationRecord` is not reused; (c) every *.py in the package except NOT_POLICY is hashed into the resolver policy id (modules/capability_runtime/agent_resolver.py:132-158), so a new metrology module must be added to NOT_POLICY, with a test proving the policy id does not move.
- **D-02 (definitions are not in the repo):** The expansions of TTFMC / TTFUR / TTVD appear nowhere on this host (no definition in the clone beyond ROADMAP/REQUIREMENTS/01-EVIDENCE; the Owner's source text iteracion-avanzada-universal.txt is NOT ADMITTED, LP-02). The plan must NOT claim the Owner defined them. Task 1 writes the contract as PROPOSED operational definitions (start event, end event, unit, censoring rule, meaning of a missing end), each tied to events that exist in a Claude Code transcript JSONL (user message timestamp, first assistant message, first tool_use, first user-visible assistant text, first deliverable evidence). The Owner or laptop confirms the mapping (record as an LP item). The names are kept verbatim as labels.
- **D-03 (eight states):** the sample state vocabulary is exactly MEASURED, FAILED, TIMED_OUT, INCONCLUSIVE, SKIPPED_BY_POLICY, NOT_APPLICABLE, UNOBSERVED, UNAVAILABLE. Rules: only MEASURED enters a percentile's value set; every other state stays in the denominator N_total and the censored count is reported next to it (TIMED_OUT and a start with no end are censored, never dropped, never zero); UNKNOWN is never MEASURED; an unreadable transcript is UNAVAILABLE, not an empty distribution. Each state needs a test where it is REACHED from a real input shape (not only a constant) and one where a wrong classification changes the output (both poles).
- **D-04 (percentiles):** p50/p90/p95 over MEASURED values only, with N, censored count and N_total printed; fewer than a declared minimum N prints the percentile as UNJUDGED. Reuse the Phase 2 convention in tools/verify_bench_all.py (`percentile`/`summarize`: linear interpolation, None on empty, never 0) if plan 02-02 landed it: read that owner first and CONNECT, or state in writing why it cannot be imported; no second copy unless EXTEND/CONNECT fails in writing.
- **D-05 (real transcripts, GEX44 plane):** the report runs over transcripts under `/home/kobii/.claude/projects/*/*.jsonl` on this host. Content is never printed or stored: only timestamps, event types and counts are read (these files hold private conversation and secrets; HR-SECRET-002). The report header says `plane: GEX44` and carries host, sample size and transcript root. Sampling is bounded (explicit cap on files and bytes), the cap is reported, and a capped run is labelled as such, never as the whole population. A GEX44 distribution is not evidence about the laptop.
- **D-06 (reuse owners, build only with a written reason):** tools/measure_hook_event.py, tools/measure_session_start.py, tools/session_autopsy.py and the bench_all ledger are INPUT sources, read at header level only in Phase 1: the plan reads them before deciding what to connect. New files are allowed only inside modules/capability_runtime (D-01) and one thin CLI under tools/ for the report, each with a written reason why EXTEND/CONNECT of an existing tool fails.
- **D-07 (gates):** existing capability_runtime tests (for example tools/test_capability_invocation.py) keep passing, baseline taken before any edit and recorded. Liveness: the new module is reachable or declared in `vault/liveness/reachability_registry.json` (`python3 modules/liveness/reachability.py`), never silent. The tools/test_git_invocation.py failing set must not change (baseline 6/7, 14 pre-existing offenders, see 02-CONTEXT.md).
- **D-08 (evidence discipline):** each new test has a recorded failing run against pre-change code or a mutant (Phase 2 pattern: `.planning/workstreams/perf-construction/phases/02-benchmark-integrity/record_run.py`), recorded verbatim; every number in the phase evidence names its instrument, plane (GEX44) and sample size. The phase ends with `phases/03-*/03-EVIDENCE.md` (commands, exit codes, verdicts, P-ids touched, LAPTOP-ONLY items).
- **D-09 (commit hygiene):** commit by explicit pathspec on branch mission/perf-construction; never push; never edit ~/.claude/settings.json, rules or CLAUDE.md; never touch the live claude-power-pack install; another executor edits tools/bench_all.py and tools/test_bench_*.py concurrently, so no Phase 3 plan lists those files in files_modified.
</decisions>

<canonical_refs>
- .planning/workstreams/perf-construction/ROADMAP.md (Phase 3), REQUIREMENTS.md (PERF-03), STATE.md
- .planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-EVIDENCE.md (section 3 D1, section 7 LP items)
- .planning/workstreams/perf-construction/phases/02-benchmark-integrity/02-CONTEXT.md (percentile convention, record_run pattern)
- modules/capability_runtime/{__init__,invocation,agent_telemetry,agent_resolver}.py
- vault/audits/perf_campaign_w0_reality.md
</canonical_refs>
