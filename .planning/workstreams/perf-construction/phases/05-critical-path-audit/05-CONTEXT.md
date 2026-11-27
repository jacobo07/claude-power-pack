# Phase 5: Critical-path audit - Context

**Gathered:** 2026-11-23 (unattended; no discuss step, research skipped; this file is the evidence base, read from code on GEX44)
**Status:** Ready for planning
**Plane:** GEX44 (kobicraft-gex44, Linux, node v18, Python 3.12). Every statement below was read from the repo checkout unless it says otherwise. Anything about `~/.claude/settings.json` or a laptop timing is LAPTOP-ONLY and UNKNOWN here.

<domain>
## Phase Boundary

PERF-05: "Name what runs synchronously while the user waits and what could move."
Depends on Phase 3 (metrology sample states) and Phase 4 (host pressure).

ROADMAP success criteria, verbatim in substance:
1. An inventory of hooks per event from the repo's hook registry, each classed BLOCKING-SAFETY, DEFERRABLE or UNKNOWN.
2. Any change moves only DEFERRABLE work and keeps `tools/test_hook_boundary.py` green.
3. A laptop measurement procedure (before/after, host-state matched) written and marked LAPTOP-ONLY / UNJUDGED.

Out of scope: changing what any hook does, wiring `SessionEnd` in `settings.json` (Owner-owned, HR-001), any timing number presented as a laptop result, the live `~/.claude` install, ROADMAP.md.
</domain>

<facts>
## Facts read from the repo (base e887448c)

**F1. The repo's hook registry is `hooks/hook-dispatcher.js`.** Two maps: `EVENT_MAP` (event name -> list of in-process hook modules, run sequentially inside the dispatcher process) and `CHAIN_MAP` (chain name -> list of `{exe, script, timeoutMs, block?, critical?}`, run as shell-free child processes by `runChain`). `CHAIN_MAP`, `CHAIN_NAMES`, `EVENT_NAMES`, `NO_EVENT_ROUTES` are exported; `EVENT_MAP` is NOT exported, and `main` runs only under `require.main === module`.

**F2. The registry has two layers and only one is in the repo.** The dispatcher maps are repo-owned. Which events and matchers call the dispatcher, and every standalone hook, live in `~/.claude/settings.json`, which is Owner/laptop-owned (HR-001) and absent from the repo. So any "this chain fires on this event" statement, and every standalone registration, is UNKNOWN / LAPTOP-ONLY here. Entries written `./x.js` resolve to the live loose `~/.claude/hooks/`; entries written `../skills/claude-power-pack/...` resolve to this checkout.

**F3. A structural load works (planning-session prototype, NOT recorded evidence; Plan 05-01 re-measures and records).** Appending `module.exports.EVENT_MAP = EVENT_MAP;` to the dispatcher source in memory through a `Module.prototype._compile` wrapper, with `HOME` pointed at an empty temp directory, loaded the dispatcher on node v18 with rc 0 and no file written. It reported 113 entries in 20 containers: Stop-chain 27, SessionEnd-chain 5, PreToolUse-Bash-chain 15, PreToolUse-Edit-chain 13, PreToolUse-Read-chain 3, SessionStart-chain 4, UserPromptSubmit-chain 8, PostToolUse-Bash-chain 4, three drill chains of 2 each, and nine `EVENT_MAP` keys of 3, 7, 3, 3, 3, 3, 4, 1, 1 entries. 18 of the 113 do not resolve to a file in this checkout (11 `./x.js` loose live hooks in `EVENT_MAP`, counting `turn-boundary-breadcrumb.js` once per container; `host-memory-floor.js`; and 6 drill fixtures under `./tests/fixtures/`). These counts are a prototype reading; treat them as a cross-check target, not a result.

**F4. Mechanical blocking signals exist in the registry and in source.** Entries carry `block: true` (a nonzero exit becomes a deny) and `critical: true` (runs in the priority lane before the pool). The prototype found 4 block and 3 critical in Stop-chain, 5 and 2 in PreToolUse-Bash-chain, 4 and 3 in PreToolUse-Edit-chain, 1 critical each in SessionStart-chain and UserPromptSubmit-chain. In addition, a planning-session regex scan of resolvable source found 27 container-script pairs that carry NO block/critical flag but whose source contains a deny shape (permissionDecision, a block decision, continue:false, or exit code 2): for example `quality-skill-gate.js`, `rtk-rewrite.js`, `cascade_check_bash.js`, `legal_deploy_gate.js`, `anti-thrash.js`, `jobs-woz-gatekeeper.js`, `session_budget_guard.js`, `semantic_breaker.js`, `research_reuse.js`. A flag-only classifier would call these deferrable. That is the reason classification has a source-reading floor.

**F5. The deferral that the dispatcher already prepares.** `SessionEnd-chain` is inert and duplicates five accounting hooks that also sit in Stop-chain: `ads_sync.py`, `session_writeback.py`, `trace-flusher.js`, `session_delta_stop.js`, `learning-sentinel.js`. The dispatcher comment states the Owner must wire `SessionEnd` in `settings.json` first and only then remove the Stop-chain duplicates ("land the new surface before deleting the old"). Moving them changes durability from per-turn to per-session: a session that dies abnormally never reaches `SessionEnd`. That risk is the first falsifier of the deferral, not a footnote.

**F6. Deadlines are deliberately absent on blocking chains.** `CHAIN_DEADLINE_MS` is set only on SessionStart-chain (4000), UserPromptSubmit-chain (3000) and two drill chains (1500), never on blocking PreToolUse chains, because an abandoned `block: true` gate fails open. A change that adds a deadline to a chain holding a blocking gate weakens safety and must be refused by the guard.

**F7. `tools/test_hook_boundary.py` (536 lines, footer `HOOK_PASS=n/N  threshold=N/N`).** Gates V-HOOK-* for `hooks/cdio_visual_advisory.js`: block denies, approve allows, revise does not deny, non-surface inert, gate-unavailable fails open, registry detector works, trigger registered. It writes markers under `~/.claude/state/cdio` (cleaned in `finally`) and V-HOOK-TRIGGER-REGISTERED reads live `settings.json` and the dispatcher through `live_root()` = `Path.home()/.claude`, reporting UNEVALUATED on a read failure. Its baseline has NOT been run yet. Running it under an isolated `HOME` keeps the live install untouched; it may then report UNEVALUATED for the trigger gate, and that outcome is data, not a pass.

**F8. The existing timing owners are laptop-shaped.** `tools/measure_hook_event.py` enumerates from `~/.claude/settings.json` and parses commands with a regex that accepts only `C:\`, `C:/` or `/c/` paths. A probe on this host: `parse_command` on a node command naming a Linux-form path to the dispatcher with `--event=Stop-chain` returns None, while the same command in the Windows/msys form parses (to the Linux node path with a Windows script path). It times each hook individually, not the chain through the dispatcher, carries no host state and has no timeout/censoring vocabulary. `tools/measure_session_start.py` is the same source with `shell=True`. Neither is a registry inventory and neither can judge a before/after. The dispatcher's own comments quote Stop-chain "about 54.9 s per turn end sequential", Edit chain about 10 s, Bash about 5.8 s, Read about 1.4 s; those are laptop-era historical claims in a comment, not measurements here and not evidence.

**F9. Owners to reuse (Phases 1-4).**
- `tools/bench_all.py`: `HOST_SCHEMA` 2, `read_host_state()`, `host_pressure(host_state)` -> (class, detail), `host_bucket(host_state)` -> tuple or None, `WINDOW_N` 7, `MIN_WINDOW` 3. RED or UNKNOWN pressure is INCONCLUSIVE.
- `tools/verify_bench_all.py`: `percentile(values, q)` (linear interpolation, None on empty, never 0), `summarize`.
- `modules/capability_runtime/construction_metrology.py`: `STATES` (MEASURED, FAILED, TIMED_OUT, INCONCLUSIVE, SKIPPED_BY_POLICY, NOT_APPLICABLE, UNOBSERVED, UNAVAILABLE) and `CENSORED_STATES` (TIMED_OUT, UNOBSERVED, FAILED). Phase 3 D1 owner of sample vocabulary.
- `.planning/workstreams/perf-construction/phases/02-benchmark-integrity/record_run.py` (run with `python3 -I`): verbatim command capture with header and `# exit=N` footer.
- `tools/test_hook_replay_isolation.py`: precedent that replaying a chain under a fake `HOME` is how a hook replay stays isolated (its incident: an unisolated replay wrote synthetic rows into production state).
- `modules/liveness/reachability.py` and `vault/liveness/reachability_registry.json`: 56 pre-phase offenders (Phase 4 record), gate success = offender set unchanged by name.

**F10. Laptop item numbering.** LP-01..LP-08 are taken by Phases 3-4. Phase 5 uses LP-09 onward.
</facts>

<decisions>
## Implementation Decisions (locked for the plans; unattended picks are reversible and recorded in STATE.md)

- **D5-01 Zero registration change in Phase 5.** No edit to `hooks/`, to the dispatcher maps, to `~/.claude/settings.json` or to any hook source. Criterion 2 is made non-vacuous by a guard that compares the dispatcher inventory to a recorded baseline (nothing moved, nothing weakened) with planted mutants proving it can fail, plus `tools/test_hook_boundary.py` run before and after. Reason: the only deferrable move on offer (F5) needs `settings.json` wiring the repo does not own, and a durability trade the Owner must accept.
- **D5-02 Inventory source is the dispatcher, loaded structurally, never by regex.** A node child with an in-memory append wrapper (F3) under an empty temp `HOME`, cross-checked against the exported `CHAIN_MAP` lengths by an independent route. A load that cannot produce `EVENT_MAP` exits nonzero; an empty inventory is never a result. The `settings.json` layer is declared UNKNOWN / LAPTOP-ONLY (LP-09), not read.
- **D5-03 Three classes, closed, with basis codes and a mechanical floor.** BLOCKING-SAFETY, DEFERRABLE, UNKNOWN. Rule order: (1) `block` or `critical` flag -> BLOCKING-SAFETY (FLAG_BLOCK_OR_CRITICAL); (2) resolvable source with a deny shape -> BLOCKING-SAFETY (DENY_SHAPE_IN_SOURCE); (3) source not resolvable in this checkout -> UNKNOWN (UNRESOLVED_LIVE_ONLY); (4) a declared table row in `vault/config/hook-critical-path-classes.json` keyed `container|script`; (5) no row -> UNKNOWN (NO_TABLE_ROW). The table can raise a no-flag entry to BLOCKING-SAFETY or lower it to DEFERRABLE only when the entry passes the DEFERRABLE guards (resolvable, no flags, no deny shape, source never emits additional context to the model, non-empty evidence with file:line, and for DEF_ACCOUNTING_DUP the script is also present in SessionEnd-chain). A table row that contradicts a mechanical floor is a table violation and the audit fails. A table row whose key is not in the live inventory is stale and the audit fails (coverage by construction, PR-COVERAGE-BY-CONSTRUCTION-001: subjects are discovered, the table only annotates).
- **D5-04 One new thin tool, with the reason EXTEND fails.** `tools/hook_critical_path_audit.py` (stdlib only) plus `tools/test_hook_critical_path.py`. Reason: `measure_hook_event.py` sources from the laptop-owned `settings.json`, its regex cannot parse a Linux path (F8 probe), and it has no classification, host state or censoring; extending it would couple the repo registry audit to a file the repo does not own and change a tool the laptop uses unchanged for LP-09. The new tool CONNECTS to the owners in F9 (host state, percentile, sample states) and does not redefine them. `measure_hook_event.py` stays unedited.
- **D5-05 Depth of classification.** Stop-chain (the documented longest wait) is classified entry by entry with evidence. The other containers get the mechanical classes plus table rows only where the evidence is cheap and cited; every remaining entry is UNKNOWN (NO_TABLE_ROW or UNRESOLVED_LIVE_ONLY) and is printed as a named residual set in the evidence, not a count.
- **D5-06 Guard semantics (criterion 2).** Compare current inventory to the recorded baseline snapshot. Violations: a non-DEFERRABLE entry removed from or moved out of its container (MOVED_NON_DEFERRABLE); `block` or `critical` true->false on any entry (FLAG_WEAKENED); a DEFERRABLE entry removed without the same script present in SessionEnd-chain (DROPPED_WORK); a deadline added to a chain that holds a BLOCKING-SAFETY entry (DEADLINE_ON_BLOCKING_CHAIN). Five planted mutants and two controls on snapshots (hermetic, no repo edit) prove each violation is reachable and the pass path is reachable.
- **D5-07 Boundary suite before and after under an isolated HOME.** Verdict for "keeps green": PASS only if the before run is exit 0 with full-count footer and the after run matches it gate by gate; if the before run is not green, "keeps green" is NOT SHOWN (UNKNOWN) while "unchanged" can still hold; the real-`HOME` run is LP-12 on the laptop.
- **D5-08 Before/after judge is a pure function that refuses a non-laptop plane.** `ab_verdict` takes A, A-replicate and B arms of sample dicts (state from `STATES`, `wall_ms`, bench_all `host_state`) and returns one of B_FASTER, B_SLOWER, NO_DIFFERENCE_DETECTED, INCONCLUSIVE, UNKNOWN. UNKNOWN for fewer than 7 MEASURED samples per arm (PROPOSED, uncalibrated, equals `WINDOW_N`), no A/A control, moved work not shown preserved, or plane not LAPTOP. INCONCLUSIVE for non-GREEN pressure leaving an arm short, mismatched `host_bucket`, or more censored samples in B than in A. B_FASTER requires both p50 and p95 to improve by more than the A/A spread. The CLI exposes no plane override; tests use a test-only parameter so a GEX44 number can never be passed off as a laptop result.
- **D5-09 Laptop items.** LP-09 settings.json registry enumeration; LP-10 A/A then A/B Stop-chain wall under host-state matching; LP-11 durability and work-preserved check including abnormal-exit falsifier; LP-12 `test_hook_boundary.py` with real `HOME` before and after. Each carries command, falsifier and the mark LAPTOP-ONLY / UNJUDGED.
- **D5-10 Privacy.** Records carry repo-relative script paths, flags, classes and counts only. No process ids, command lines, session ids, transcript content or user paths (HR-SECRET-002 spirit). Isolated-HOME runs use fixed scratch directories under `/tmp`, never `~/.claude`.
- **D5-11 Liveness.** Run `python3 modules/liveness/reachability.py` before the first new file and after the last; the offender set must be unchanged by name. If the new tool or suite appears as a new offender, declare it in `vault/liveness/reachability_registry.json` as LIBRARY with a one-line reason and re-run; otherwise make no registry edit.
- **D5-12 Historical timings are claims, never measurements.** The 54.9 s and similar figures in dispatcher comments may be quoted only as "claimed in a comment, laptop era, unmeasured here".

### Claude's Discretion
Exact JSON field order, table row prose, how the audit CLI lays out text output, and whether the isolated-HOME wrapper is a shell variable or a Python argument.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/workstreams/perf-construction/ROADMAP.md` Phase 5 section (read from git HEAD; never edit)
- `hooks/hook-dispatcher.js` (EVENT_MAP, CHAIN_MAP, CHAIN_CONCURRENCY, CHAIN_DEADLINE_MS, SessionEnd-chain comment)
- `tools/test_hook_boundary.py`, `tools/test_hook_registration_integrity.py` (loader precedent), `tools/test_hook_replay_isolation.py`
- `tools/measure_hook_event.py`, `tools/measure_session_start.py` (unchanged owners, laptop use)
- `tools/bench_all.py`, `tools/verify_bench_all.py`, `modules/capability_runtime/construction_metrology.py`
- `.planning/workstreams/perf-construction/phases/04-host-pressure-admission/04-EVIDENCE.md` and `04-VERIFICATION.md` (evidence format, LP-07 / LP-08, unknowns)
- `.planning/workstreams/perf-construction/phases/02-benchmark-integrity/record_run.py`
</canonical_refs>

<deferred>
## Deferred Ideas (not in any plan)

- Applying the Stop-chain to SessionEnd move (needs Owner wiring on the laptop; recorded as a candidate only).
- Folding standalone `settings.json` hooks into the dispatcher (laptop-owned layer).
- Changing hook concurrency or timeouts.
- Phase 6 work (the integrated verdict).
</deferred>
