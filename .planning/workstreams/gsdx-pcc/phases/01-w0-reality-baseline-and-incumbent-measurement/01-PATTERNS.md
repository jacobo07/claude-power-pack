# Phase 1: W0 Reality, baseline and incumbent measurement - Pattern Map

**Mapped:** 2026-10-07
**Files analyzed:** 8
**Analogs found:** 7 / 8
(Tracked-source gate: `git ls-files` could not be run, no PowerShell tool and the Bash guard blocks git. All analog paths are ordinary repo paths under tools/, modules/, vault/, .planning/, none under a `.gsd/capabilities` mirror. Planner/executor should run `git ls-files` once before relying on them.)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `modules/gsd_x/goal/providers/gate.py` (line 72, modify) | service (supervisor source string) | request-response / subprocess | itself (RESEARCH 1.1); `tools/evidence_bundle.py:68` shows the explicit-capture style | exact |
| `<phase>/r01-drill.json` (new) | config (drill spec) | batch | spec schema in `tools/mutation_drill.py:5-11`; usage in `tools/test_mutation_drill.py:70-80` | role-match (no committed spec JSON exists, Glob `**/*drill*.json` empty) |
| `tools/gsdx_w0_timing.py` (new, timing + timeline script) | utility / measurement | batch, file-I/O | `tools/test_family_injection.py:78-82` (hermetic env) + `GoalLog.read()` `modules/gsd_x/goal/log.py:152-178` | role-match |
| `vault/knowledge_base/ukdl-universal.md` (append T-entry) | doc | append | tail of same file `:15262-15285`; `:246-260` | exact |
| `<phase>/01-EVIDENCE.md` (new) | doc | report | `.planning/workstreams/cognitive-economy/phases/01-baseline-gate-and-owner-reconciliation/01-EVIDENCE.md` | exact |
| `.planning/workstreams/gsdx-pcc/DENOMINATOR.md` (row R01 update) | doc | table edit | itself, line 57 | exact |
| `vault/liveness/reachability_registry.json` (via `--baseline`) | config | batch | `modules/liveness/reachability.py:705-722` (writes `known_orphans`) | exact |
| `<phase>/premise record` (inside EVIDENCE.md) | doc | report | RESEARCH Section 2 signatures | exact |

## Pattern Assignments

### `modules/gsd_x/goal/providers/gate.py` line 72 (one-line fix)

Current (gate.py:66-75, from RESEARCH 1.1):
```python
"import json,subprocess,sys,time\n"
"res=sys.argv[1]; cmd=sys.argv[2:]\n"
"rc=subprocess.run(cmd).returncode\n"                      # gate.py:72  (R01)
```
Target: `"rc=subprocess.run(cmd,stdout=sys.stdout,stderr=sys.stderr).returncode\n"` (`sys` already imported on line 70). Do not touch the `Popen` at gate.py:126-135. Sequence: run `python tools/test_gsd_x_goal_gate_provider.py`, save the 17/18 RED (`FAIL V-GATE-VERDICT-FIELDS`) first, then edit, then 18/18. Do not add a gate to the suite (keeps "18/18" literal).

### `r01-drill.json` (config, batch)

**Schema** (`tools/mutation_drill.py:5-11`): `{"file","test","gate","old","new"[, "copy_dirs","repo_root","root_env"]}`. Anchor must occur exactly once (`:167-169`). CLI takes only `--spec` (`:196`); drill reads `utf-8-sig`. Write with the Write tool.
```json
{"file": "modules/gsd_x/goal/providers/gate.py",
 "test": "tools/test_gsd_x_goal_gate_provider.py",
 "gate": "V-GATE-VERDICT-FIELDS",
 "old": "rc=subprocess.run(cmd,stdout=sys.stdout,stderr=sys.stderr).returncode",
 "new": "rc=subprocess.run(cmd).returncode"}
```
Run only AFTER the fix (before it the control is CONTROL_INVALID exit 4). Pass = `MUTANT KILLED gate=V-GATE-VERDICT-FIELDS`, exit 0. Exit map `:205`: KILLED 0, SURVIVED 1, UNJUDGED 2, HARNESS 3, CONTROL_INVALID 4. Test-side examples of spec dicts: `tools/test_mutation_drill.py:70-80`. Never `tools/mutation_probe.py`. Record the stderr-only survivor as a known limit.

### `tools/gsdx_w0_timing.py` (measurement script; tools/ is not scanned by liveness)

**Hermetic env pattern** (`tools/test_family_injection.py:78-82`):
```python
home = tempfile.mkdtemp(prefix="finj-home-")
env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONIOENCODING="utf-8")
os.environ.update(HOME=home, USERPROFILE=home)
```
Add `GSDX_GOALS_ROOT=<tmp>\goals` (semantics: `log.py:100-102`, `sweep.py:52-55`).

**Per-suite timing:** for each `tools/test_gsd_x_goal_*.py` run `subprocess.run([sys.executable, f], env=env, stdout=<file>, stderr=STDOUT)` with `time.perf_counter()`, record returncode and the `*_PASS=n/m` line using the grammar in `tools/evidence_bundle.py:43`: `re.compile(r"\b[A-Z][A-Z0-9_]*_PASS=(\d+)/(\d+)")`. Redirect to a file, no pipes. Serial, first run plus min of 3. Skip/copy `test_gsd_x_goal_mutation.py` (mutates live files, no `_PASS` line; time only inside a copy of modules/tools/vault/pricing/vault/config, else UNKNOWN). Fingerprint (file count + max mtime) of `C:\Users\User\.claude\state\gsd-x` before and after.

**Timeline over a COPY of a recorded goal** (`log.py:141-178`; RESEARCH Code Examples):
```python
ev = GoalLog(repo_id, "g-002-router-surface", base=Path(copy_dir)).read()
t0 = datetime.fromisoformat(ev[0].ts)
for e in ev: print(f"{(datetime.fromisoformat(e.ts)-t0).total_seconds():9.3f}s #{e.seq:03d} {e.type}")
```
Judge replay: sum of per-gate `seconds` in the receipt (`judge.py:162-173`), or `python tools/gsd_x_goal.py judge --goal <id> --root <repo> --worktree <path>` without `--record`. Summary line convention if the script self-checks: `<SUITE>_PASS=n/m  threshold=n/m` (e.g. gate_provider test :219). Anything unobserved is recorded `UNKNOWN`.

### `vault/knowledge_base/ukdl-universal.md` (append at tail)

**Shape** (tail `:15262-15285`, example `:246-260`): new `## GSD X proof-conserving convergence, W0 (2026-10-07)` section, `Source:` paragraph, `### Traps`, then
```
### T-SUBPROCESS-WITHOUT-INHERITED-STD-HANDLES-LOSES-GRANDCHILD-OUTPUT-ON-WINDOWS-001
<one paragraph: symptom, measured date, gate.py:72 @ commit, red 17/18 -> 18/18, 0 B vs 11 B repro,
drill KILLED + control, fix, "PR: ..."> #CROSS-PROJECT
```
No id counter; slug is free (grep found no collision). Append only, do not renumber. No router edit needed.

### `01-EVIDENCE.md` (phase dir)

**Analog:** `.planning/workstreams/cognitive-economy/phases/01-baseline-gate-and-owner-reconciliation/01-EVIDENCE.md` (header with commit, results table, `command:` + fenced verifier output, red drill with rc, "Product Delta"/"Intelligence Delta"). Also see `cognitive-resource-os/phases/01-gate-verdict-on-the-big-host/EVIDENCE.md`. Required contents here: red output, green output, drill verdict with exit code, premise signatures table (note `decide` lives in `modules/cognitive_os/scheduler.py:94`, not parallel_mesh), incumbent timing table, liveness decision, Production Reality verdict, denominator rows moved, UKDL entries. No env/tokens pasted.

### `DENOMINATOR.md` row R01 (line 57)

Current: `| R01 | Gate output lost on Windows (gate.py:72) | gate provider | FIX red-first + drill + UKDL | 1 | OPEN | |`
Edit the last two columns only: status `DONE`, evidence = commit hash, `GSDX_GATE_PROVIDER_PASS=18/18`, drill KILLED, UKDL id, EVIDENCE.md ref. Rows are never deleted; new gaps are appended.

### Liveness baseline (`vault/liveness/reachability_registry.json`)

`python modules/liveness/reachability.py` exits 1 with 57 offenders at base (RESEARCH 6). `--baseline` (`reachability.py:705-722`) writes the current unreachable set into `known_orphans`. Land it in its own commit, verify the diff equals exactly the 57 named offenders, re-run to exit 0. Phase 1 adds no module, so it creates no new debt. Record the decision in EVIDENCE.md.

## Shared Patterns

- **Command discipline:** PowerShell, absolute git `& 'C:\Program Files\Git\cmd\git.exe' -C C:\Users\User\Apps\pp-gsdx-pcc ...`, file redirect not pipes, one msgfile per commit, `git commit -F`, never push.
- **Suite grammar:** every suite prints `<SUITE>_PASS=n/m  threshold=n/m` (parsed by `tools/evidence_bundle.py:43`).
- **Drill discipline:** control then mutant then named gate; anything but KILLED/0 is a stop.

## No Analog Found

| File | Role | Reason |
|---|---|---|
| committed drill spec JSON | config | none exists in repo; use the schema docstring (`mutation_drill.py:5-11`) |

## Metadata

**Analog search scope:** tools/, modules/gsd_x, modules/liveness, .planning/workstreams/*/phases, vault/knowledge_base
**Files scanned:** ~12 (plus RESEARCH-verified reads)
**Extraction date:** 2026-10-07

## PATTERN MAPPING COMPLETE
