---
phase: 04-cognitive-cost-regression-gate
plan: 02
subsystem: floor-regression-gate
tags: [pillar-K, IC-K, scope-attribution, hooks, skills, agents, mutation-drill]
requires: ["04-01"]
provides:
  - "tools/floor_regression_gate.py: PLUGIN_ROOT_TOKEN, host_has, registrations, AttributionContext (is_file / agent_names caches, project_regs, user_regs), command_label, command_scope, correlate_hook, hook_scope, scope_for_name; classify routes hook_additional_context, hook_system_message, skill_listing entries and agent_listing_delta entries through them; every component carries scope_basis"
  - "tools/test_floor_regression_gate.py: write_settings, attr_check, hook_cmds, touch, measure_floor, comp, skill_sizes helpers; build_floor params hookrows / skill_entries / agents / sysmsg / hook_event / hook_name; 14 new V-FLOOR-HOOK-* / -SETTINGS-UNREADABLE / -CWD-ABSENT-UNATTRIBUTED / -SKILL-* / -LISTING-SPLIT-EXACT / -AGENT-SCOPE / -RELABEL-NO-RISE gates; drill mutants M9-M11"
affects: ["04-03", "04-04"]
tech-stack:
  added: []
  patterns: ["attribution by REGISTRATION (which settings file names the command), never by where a script lives", "absent is not zero: unreadable settings are None (unknown), a cwd / install_home missing on this host leaves everything unattributed", "one patchable host seam (host_has) and one patchable name seam (scope_for_name) so a drill can attack them", "deltas stay per source, so a later relabel of the same chars costs nothing", "a merge of two components with different scopes is unattributed, never the first one's"]
key-files:
  created: []
  modified: [tools/floor_regression_gate.py, tools/test_floor_regression_gate.py]
decisions:
  - "Attribution is computed on the measuring host at measure time from the settings and skill / agent files present then (recorded in the reference caveats); per-source deltas make a relabel cost-neutral (V-FLOOR-RELABEL-NO-RISE)"
  - "A plugin `ns:name` skill or agent with no file under the project is filed universal (the plan's rule): the stricter side of the 1,000-char rule, so a project-scoped plugin is over-reported, never under-reported; recorded as a caveat"
  - "When the host check fails, even the `${CLAUDE_PLUGIN_ROOT}` rule returns unattributed (the plan says every rule); a plugin string is host-independent proof, so this is the conservative reading"
  - "A skill or agent name that could leave its directory (a path separator, `.` or `..` part) is unattributed with basis bad_name; names from a transcript are untrusted"
  - "Hook command sources longer than 200 chars are labelled by their first 120 chars + `...#` + 12 hex of the sha256 (stable and short)"
status: complete
commits: 2
plan_head_before: 63a4082bc48158c8d1a174dfedeb8cda6203b32b
actuals:
  tokens: 10066
  tasks: 2
  commits: 2
metrics:
  completed: 2026-10-04
requirements: [IC-K]
requirements-completed: []
---

# Phase 4 Plan 02: scope attribution for hooks, skills and agents (pillar K) Summary

The four rows 04-01 left `unattributed` (hook_additional_context, hook_system_message, skill_listing entries, agent_listing_delta entries) now carry an evidence-based scope and a recorded `scope_basis`: a +1,024-char rise in a project-registered hook exits 0 and reads `scope=project`; the same rise in a user-registered hook, a universal skill or a universal agent exits 1 naming the layer and `scope=universal`. Anything unprovable (a built-in, a command registered in both settings files, unreadable settings, a cwd that is not on this host) stays `unattributed` under the 1,000-char rule. **IC-K is addressed, not satisfied** (laptop reference is 04-04); ledger `state.K` is still `{}` and IC-K is not ticked.

**Code commits:** `13f3bffe` (Task 1 tracer, hooks), `11686c8d` (Task 2 expansion). Each touches only `tools/floor_regression_gate.py` and `tools/test_floor_regression_gate.py`.

## Observed results

- `python3 tools/test_floor_regression_gate.py` -> `FLOOR_PASS=40/40  threshold=40/40  skipped=0  inconclusive=0`, exit 0, 1.9 s (limit 60 s). Every 04-01 gate still PASS, including `V-FLOOR-WINDOW-APPEND-STABLE`.
- `python3 tools/test_floor_regression_gate.py --drill` -> `PASS DRILL-CONTROL 39/39`, eleven `KILLED` lines (M1-M8 from 04-01; M9 correlate_hook returns no producing command by V-FLOOR-HOOK-CORRELATED; M10 scope_for_name never returns project by V-FLOOR-SKILL-PROJECT; M11 host_has always True by V-FLOOR-CWD-ABSENT-UNATTRIBUTED), `PASS DRILL-CLEAN-AFTER-MUTANTS 39/39`, `PASS DRILL-RESTORE gate file sha256 2b1a03002e7134bd before == after`, `DRILL killed=11/11`.
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`; ledger `state.K` still `{}`.
- Read-only real-transcript smoke (not a gate; the real gates are 04-03's): the gate measured the GEX44 session 34f03871 (cwd `/home/kobii/missions/incremental-cognition`, written to /tmp, never under `~/.claude`): total 207,245 chars; hook_context 4,393 universal/user_settings (the dispatcher), 3,405 universal/plugin (`${CLAUDE_PLUGIN_ROOT}` hook; both equal the planning measurements), 2,299 universal/event_fallback (the UserPromptSubmit row with no producing success row); skill_listing 22,382 universal/install_file + 6,632 unattributed/no_file (built-ins and the `osa` name present in both homes); the project CLAUDE.md 34,478 stays project.
- `grep -c 'def correlate_hook' tools/floor_regression_gate.py` -> `1`. `grep -c USERPROFILE tools/test_floor_regression_gate.py` -> `3`. The helper that points HOME and USERPROFILE at a scratch home and restores both in a `finally` is `with_home` (used by every in-process attribution gate; `run_cli` sets both for the subprocess legs).

## RED outputs (recorded before each build)

- Task 1: `FAIL V-FLOOR-HOOK-CORRELATED cli project hook +1024: rc=1 layer=['LAYER hook_context:SessionStart:SessionStart scope=unattributed ref=4000 now=5024 delta=+1024'] ... MATERIAL_RISE` (case (a) exited 1: 04-01 files every hook element as unattributed); `FLOOR_PASS=26/27`. The in-process legs failed identically.
- Task 2 (31/40 PASS): FAIL V-FLOOR-HOOK-SYSTEM-MESSAGE (`LAYER hook_system_message... scope=unattributed ... delta=+1024`, rc=1), V-FLOOR-CWD-ABSENT-UNATTRIBUTED (`cwd present skill ps: ('unattributed', 'origin_unprovable') want ('project', 'project_file')` and the same for us / pa / ua), V-FLOOR-SKILL-PROJECT (`rc=1 ... scope=unattributed`), V-FLOOR-SKILL-UNIVERSAL (`rc=1 rise=[]`: red but not attributed), V-FLOOR-SKILL-NAMESPACE, V-FLOOR-SKILL-BUILTIN-UNATTRIBUTED (basis `origin_unprovable` not `no_file` / `ambiguous` / `bad_name`), V-FLOOR-LISTING-SPLIT-EXACT (all entries unattributed), V-FLOOR-AGENT-SCOPE (a test bug: the second `attr_check` reused a root and hit `reference_exists`; fixed by a fresh root, not a gate-code change), V-FLOOR-RELABEL-NO-RISE (skill did not relabel). The plugin, event-fallback, ambiguous and settings-unreadable gates were already green after Task 1 (its code already carried those rules).

## Gate list added

V-FLOOR-HOOK-CORRELATED (CLI + in-process; +1,024 project green / universal red), V-FLOOR-HOOK-SYSTEM-MESSAGE, V-FLOOR-HOOK-PLUGIN, V-FLOOR-HOOK-EVENT-FALLBACK (user only / project only / both / other event), V-FLOOR-HOOK-AMBIGUOUS (one command in both settings; two commands, equal text), V-FLOOR-SETTINGS-UNREADABLE (project not JSON, project a JSON list, user not JSON, plus a readable control), V-FLOOR-CWD-ABSENT-UNATTRIBUTED (every hook / skill / agent attribution with the cwd present, then with it removed; verdict green then red), V-FLOOR-SKILL-PROJECT, -SKILL-UNIVERSAL, -SKILL-NAMESPACE (commands/ns/rest.md, nested `carl:tasks:add-rule`, plugin namespace, both homes), -SKILL-BUILTIN-UNATTRIBUTED (`init`, `osa` in both, `../escape` traversal), V-FLOOR-LISTING-SPLIT-EXACT (per-entry chars sum to the listing's), V-FLOOR-AGENT-SCOPE (nested `agents/sub/ua.md`, built-in, plugin), V-FLOOR-RELABEL-NO-RISE (settings and skill file added after the reference: scopes differ, no rise).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] V-FLOOR-LAYER-TABLE expected the 04-01 attribution**
- **Found during:** Task 1 and Task 2
- **Issue:** the 04-01 layer table asserted `hook_context` and `hook_system_message` as `unattributed`; with no producing row and no registrations the plan's event fallback now files them `universal`.
- **Fix:** the expected rows in `g_layer_table` now say `universal` (commented as the event fallback). No gate-code change.
- **Files modified:** tools/test_floor_regression_gate.py
- **Commits:** 13f3bffe, 11686c8d

**2. [Rule 2 - Missing critical] merge of components with different scopes**
- **Found during:** Task 1 (design)
- **Issue:** `classify` merges components by (layer, source); with scope now varying per element a merge could silently keep the first element's scope.
- **Fix:** a merge of two different scopes becomes `unattributed` (basis `ambiguous`); ambiguous hook sources get their own key `ambiguous:<Event>`.
- **Commit:** 13f3bffe

**3. [Rule 2 - Missing critical] untrusted names**
- **Found during:** Task 2 (design)
- **Issue:** a skill or agent name comes from a transcript and is joined into a path.
- **Fix:** `_name_parts` rejects any part that is empty, `.`, `..` or contains a path separator or NUL: unattributed, basis `bad_name`; pinned by V-FLOOR-SKILL-BUILTIN-UNATTRIBUTED.
- **Commit:** 11686c8d

**4. [Plan interpretation] V-FLOOR-HOOK-CORRELATED runs twice**
- The plan wants a real-subprocess pair and also names M9 (an in-process monkeypatch) as its killer, which a subprocess cannot see. The gate runs each case through `run_cli` and through `run_main`; the in-process leg is what M9 breaks.

**5. [Plan interpretation] extra `scope_basis` values**
- Beyond the plan's list the code records `no_registration` (command registered nowhere), `project_file` / `install_file` / `plugin_namespace` / `no_file` / `bad_name` (skills and agents), `header`, `file_type`, `harness_type`, `origin_unprovable`.

**6. [Attribution line]** The dispatch text asked for the `Co-Authored-By: Claude Opus 5.5 (1M context)` trailer; the harness's attribution reminder for this session names `Claude Sonnet 5.5`, which is the model that ran, so both commits carry that one.

## Known Stubs

None.

## Threat Flags

None. All lookups are reads (`Path.exists`, `is_file`, `os.walk` over two `.claude` directories, once per context); no settings, skill, agent or command file is written; the attribution gates run under scratch homes.

## Self-Check: PASSED

Files exist (tools/floor_regression_gate.py, tools/test_floor_regression_gate.py); commits `13f3bffe` and `11686c8d` found in `git log`; `FLOOR_PASS=40/40` and `DRILL killed=11/11` observed after the last code commit.
