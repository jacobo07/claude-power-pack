# Phase 2: W1 Convergence semantics - Pattern Map

**Mapped:** 2026-10-07
**Files analyzed:** 9 (7 new, 3 edited; spec edit has no code analog)
**Analogs found:** 8 / 9
All analog paths are git-tracked repo source (modules/, tools/, vault/). No `.gsd/capabilities` mirrors are named.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `modules/gsd_x/goal/proof.py` (NEW) | model/projection + kill-switch reader | event-driven, pure transform over GoalLog | `modules/gsd_x/goal/evidence.py`, `intervention.py` | exact |
| `tools/test_gsd_x_goal_pcc_semantics.py` (NEW) | test | transform, truth tables | `tools/test_family_injection.py` (hermetic) + `tools/test_gsd_x_goal_reconcile.py` (layout, per RESEARCH 3.2) | role-match |
| `tools/test_gsd_x_goal_pcc_replay.py` (NEW) | test | file-I/O, golden compare, in-process mutants | `tools/test_gsd_mission_legacy_characterization.py` | exact |
| `tools/fixtures/gsdx_legacy_goals/<repo>/<goal>/NNNNNN.json` + `MANIFEST.json` (NEW) | fixture | file-I/O byte copy | `tools/gsdx_goal_timeline.py` `cmd_recorded` (copy-then-verify) | role-match |
| `tools/fixtures/gsdx_legacy_replay_golden.json` (NEW) | fixture/golden | batch | `tools/fixtures/gsd_mission_legacy_golden.json` | exact |
| mutation drill spec `*.json` (NEW, per drill) | config | batch | `.planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/r01-drill.json` | exact |
| `.gitattributes` (EDIT) | config | n/a | existing `vendor/genesis-suite/** -text` (line 6) | exact |
| `vault/liveness/reachability_registry.json` (EDIT) | config | n/a | entries `gsd_x/goal/evidence`, `intervention` (lines 442-449) | exact |
| `vault/specs/gsdx-proof-conserving-convergence.md` (EDIT) | spec | n/a | none (amend in place) | none |

## Pattern Assignments

### `modules/gsd_x/goal/proof.py` (projection, event-driven)

**Analog:** `modules/gsd_x/goal/evidence.py` (module-owned constant + pure projection), `intervention.py` (skip-foreign-types ladder).

**Imports** (evidence.py:28-34):
```python
from __future__ import annotations
import re
from dataclasses import dataclass, field
from .contract import GoalState, project
from .log import GoalLog, GoalLogCorrupt, GoalLogError
```

**Constants + own refusal class** (evidence.py:36-44; intervention.py:34-42):
```python
HYPOTHESIS = "evidence.hypothesis"
class HypothesisRefused(GoalLogError):
    """The hypothesis event would lose or fake negative knowledge."""
```
New: `CONTRACT="obligation.contract"`, `PRODUCED="proof.produced"`, `INHERITED_EV="proof.inherited"`, `INVALIDATED="proof.invalidated"`, `NEW_TYPES=frozenset(...)`, `SUPPORTED_V=1`. Never reuse any of the 22 legacy type strings.

**Core projection: skip foreign, raise GoalLogCorrupt only on own malformed types** (evidence.py:66-85, intervention.py:56-75):
```python
for ev in state.events:
    if ev.type != HYPOTHESIS:
        continue
    d = ev.data
    try:
        ...
    except (KeyError, TypeError) as exc:
        raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {HYPOTHESIS} "
                             f"({exc})") from exc
```
Deviation required by RESEARCH G12: `data["v"] > SUPPORTED_V` -> record as UNKNOWN, do NOT raise (a raise makes sweep skip the goal, sweep.py:202-204).

**Writer pattern (CAS append, D44: no second store)** (evidence.py:130-134):
```python
log.append(state.last_seq + 1, HYPOTHESIS, {...}, actor)
return project_hypotheses(project(log))[hyp_id]
```

**Kill-switch reader** (cli.py:91, 112; DIFFERENT polarity required): analog parses `os.environ.get(FAMILY_SWITCH, "").strip().lower() in ("off", "0", "false")`. RESEARCH section 5 requires the inverse: ON iff unset/empty or in `on|1|true|yes`; any other non-empty value is OFF. Read at call time, one shared parser for `GSDX_FRONTIER` and `GSDX_PROOF_INHERITANCE`, never raise.

**Hard rule:** no legacy file under `modules/gsd_x/goal/` is edited (a diff there other than the new file is the red case).

---

### `tools/test_gsd_x_goal_pcc_replay.py` (test, golden + mutants)

**Analog:** `tools/test_gsd_mission_legacy_characterization.py`

**Gate counters + check helper** (lines 53-69):
```python
passes = fails = 0
def _ok(gate, ev=""):
    global passes; passes += 1; print(f"PASS {gate} {ev}")
def _fail(gate, ev=""):
    global fails; fails += 1; print(f"FAIL {gate} {ev}")
def check(gate, cond, ev=""):
    (_ok if cond else _fail)(gate, ev)
```

**Capture refuses re-capture; meta records pre-change marker** (lines 491-503):
```python
if "--capture" in argv:
    if GOLDEN.exists() and "--force" not in argv:
        print(f"REFUSED: {GOLDEN.name} exists; a re-capture needs --force and a reviewed diff")
        return 2
    meta = {"captured_on_head": _git_head(),
            "gsd_mission_sha256": hashlib.sha256(src).hexdigest(),
            "gsd_mission_has_rollover_protocol": b"rollover_protocol" in src, ...}
    GOLDEN.write_text(json.dumps({"meta": meta, **snap}, indent=1, ensure_ascii=False) + "\n",
                      encoding="utf-8", newline="\n")
```
Adapt: marker = "goal package names PCC" (any `proof.`/`obligation.contract` string under `modules/gsd_x/goal/`); also record `engine_identity.engine_identity(ROOT)` (RESEARCH 4 step 6). Capture BEFORE the first new `.py`, commit golden first (Pitfall 1).

**Pre-change gate + population floor + per-scenario diff** (lines 518-528):
```python
check("V-G23-GOLDEN-PRE-CHANGE", meta.get("gsd_mission_has_rollover_protocol") is False, ...)
check("V-G23-POPULATION", len(want["scenarios"] or {}) == len(SCENARIOS) >= 20, ...)
for name, got in snap["scenarios"].items():
    d = diff(want["scenarios"].get(name), got, f"/{name}")
    check(f"V-G23-LEGACY {name}", not d, "; ".join(d[:4]))
```

**In-process mutants, restore in finally, clean run after** (lines 435-438, 533-545):
```python
def _mut_argv_mcp():
    orig = gm.worker_argv
    gm.worker_argv = lambda rec, prompt: ...
    return lambda: setattr(gm, "worker_argv", orig)
for name, apply, marker in MUTANTS:
    undo = apply()
    try: m = snapshot()
    finally: undo()
    d = diff(want, {...}); hit = [x for x in d if marker in x]
    check(f"V-G23-MUTANT-{name}", bool(hit), ...)
again = snapshot()
check("V-G23-CLEAN-AFTER-MUTANTS", not d, ...)
print(f"G23_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
return 0 if fails == 0 else 1
```
Phase 2 mutants: make a legacy projection (`project_convergence`/`goal_closure`/`decide`) react to a new type; each must turn the replay red.

**Summary-line shape** per RESEARCH 3.2: `print(f"\nGSDX_<X>_PASS={n}/{m}  threshold={m}/{m}")`.

---

### `tools/test_gsd_x_goal_pcc_semantics.py` (test, truth tables / laws / switches)

**Analog:** `tools/test_family_injection.py` (hermetic HOME) plus layout of `tools/test_gsd_x_goal_reconcile.py` (RESEARCH 3.2; not re-read here).

**Hermetic HOME with self-proving first gate** (test_family_injection.py:78-84):
```python
home = tempfile.mkdtemp(prefix="finj-home-")
env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONIOENCODING="utf-8")
os.environ.update(HOME=home, USERPROFILE=home)
os.environ.pop(cli.FAMILY_SWITCH, None)
check("V-FINJ-HERMETIC-HOME", Path.home() == Path(home), Path.home())
```
Also set `GSDX_GOALS_ROOT` to `mkdtemp(...)/"goals"` (log.py:43; sweep state_dir lands in parent) and add a gate refusing a goals root under live `~/.claude` (gsdx_goal_timeline.py:172-174). Pop both kill switches before each switch case (pop pattern at :80,82). Add a 3^6 = 729 premise truth-table gate with a positive control (RESEARCH Pattern 2).

---

### Fixture byte copy + MANIFEST (`tools/fixtures/gsdx_legacy_goals/`)

**Analog:** `tools/gsdx_goal_timeline.py` `cmd_recorded` (lines 118-129)
```python
src = Path(a.store) / a.repo / a.goal
base = Path(tempfile.mkdtemp(prefix="gsdx_tl_copy_"))
shutil.copytree(src, base / a.repo / a.goal)
try:
    events = GoalLog(a.repo, a.goal, base=base).read()
except GoalLogError as exc:
    print(f"REFUSED: {exc}")
    return 2
```
Copy only `NNNNNN.json` (skip `runs/`), verify chain via `GoalLog.read()` before writing, write MANIFEST with per-file sha256 + tip digest (g-002 seq 50, g-001 seq 123). The replay test copies the committed fixture to a temp root and reads that copy.

---

### Drill specs (`*-drill.json`)

**Analog:** `phases/01-.../r01-drill.json` (all 7 lines):
```json
{ "file": "modules/gsd_x/goal/providers/gate.py",
  "test": "tools/test_gsd_x_goal_gate_provider.py",
  "gate": "V-GATE-VERDICT-FIELDS",
  "old": "rc=subprocess.run(cmd,stdout=sys.stdout,stderr=sys.stderr).returncode",
  "new": "rc=subprocess.run(cmd).returncode" }
```
Committed JSON because PS 5.1 strips quotes from argv. Fixture beside suite in `tools/fixtures/` is copied with the suite; elsewhere needs `copy_dirs`.

---

### `.gitattributes` (EDIT)
**Analog:** lines 6-7: `vendor/genesis-suite/** -text`. Append with a dated comment (same style as line 3-5):
`tools/fixtures/gsdx_legacy_goals/** -text` (clone has autocrlf=true; manifest sha256 is byte-level). Also consider the golden JSON if it is byte-compared.

### `vault/liveness/reachability_registry.json` (EDIT)
**Analog:** lines 442-449, inside the same object, alphabetical position after `gsd_x/goal/intervention`-style siblings:
```json
"gsd_x/goal/evidence": {
  "class": "PLANNED",
  "note": "UWCP S1-5 ... OWNER_QUEUE: UWCP S6 wires it ...; re-classify then"
},
```
New key `"gsd_x/goal/proof"` with `class: PLANNED` and a note naming Phase 4/5 consumers plus OWNER_QUEUE. Exit gate: `python modules/liveness/reachability.py` returns 0.

## Shared Patterns

### Event-type safety (all new projections)
Source: contract.py:93-109, intervention.py:57-58. Legacy ladders have no `else`; new types are ignored. New module alone may raise `GoalLogCorrupt` (evidence.py:83-84 message format). Seq-valued fields (`last_seq`, `cv.failures[id]["seq"]`, `OperatorState.last_seq`, `Hypothesis.history`) shift under interleaving; mask them in any ignore-new-types gate (RESEARCH Pitfall 3).

### Hermetic test state
Source: test_family_injection.py:78-84; characterization test lines 35-39 (redirect env BEFORE import). Every suite: temp HOME + `GSDX_GOALS_ROOT`, first gate proves it took effect.

### Gate naming / summary
`V-<DOMAIN>-<NAME>`, `PASS/FAIL` lines, `..._PASS=n/m  threshold=n/m`, nonzero exit on any fail. Planned names: `V-PCC-GOLDEN-PRE-CHANGE`, `V-PCC-HERMETIC-HOME`, `V-PCC-LAW-*`, `V-PCC-REPLAY-*`, `V-PCC-DECIDE-SIG`, `V-PCC-NO-SECOND-STORE`.

### Discovery over hand lists
Legacy event types (22) must be discovered by scanning `modules/gsd_x/goal/*.py` (RESEARCH section 4; PR-COVERAGE-BY-CONSTRUCTION), not hand-listed.

## No Analog Found

| File | Role | Reason |
|---|---|---|
| `vault/specs/gsdx-proof-conserving-convergence.md` | spec | Amend in place; follow RESEARCH G1-G19 recommendations as ULTRA Q&A decisions recorded in STATE.md; persist the auditor's output to `02-AUDIT.md` (auditor is read-only, RESEARCH G19) |
| Synthetic legacy-log generator (inside replay suite) | test helper | Drives public writers (`contract.revise`, `set_budget`, `set_authority`, `convergence.carry_obligation`, `intervention.intervene`, `evidence.record`) per RESEARCH section 4; use reconcile suite builders (`gc.declare`, `cv.accept_obligation`, `cv.satisfy`) as the model |
| Kill-switch reader with inverted polarity | utility | Closest is cli.py:112 but its typo behaviour is the opposite of what the spec needs |

## Metadata

**Analog search scope:** modules/gsd_x/goal, modules/gsd_x/cli.py, tools/, vault/liveness, .gitattributes, phase 01 drill spec.
**Files read this pass:** ~12 (evidence.py, intervention.py, characterization test, family_injection test, cli.py excerpt, timeline tool excerpt, registry excerpt, .gitattributes, r01-drill.json, CONTEXT, RESEARCH 1-460). reconcile/sweep suites were taken from RESEARCH's verified excerpts, not re-read.
**Pattern extraction date:** 2026-10-07
