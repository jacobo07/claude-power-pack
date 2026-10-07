# Phase 1: W0 Reality, baseline and incumbent measurement - Research

**Researched:** 2026-10-07
**Domain:** GSD X goal runtime (Python, stdlib only); Windows subprocess handle inheritance; mutation drill discipline
**Confidence:** HIGH for in-repo facts (all read this session), MEDIUM for timing methodology (not yet run)

<user_constraints>
## User Constraints (from 01-CONTEXT.md)

### Locked Decisions
- R01 root cause is already characterised (spec Reality 14): `providers/gate.py:72` `subprocess.run(cmd)` passes no std handles; on Windows the grandchild's output never reaches the log, so every gate verdict carries `observed: ''`. Fix must land RED-first (drive the failing gate_provider case red, then green), be mutation-drilled through `tools/mutation_drill.py` (isolated copy + control, never `mutation_probe` live mode), and get a UKDL T-entry in `vault/knowledge_base/ukdl-universal.md`.
- Baseline suite counts at fbca24fc (spec Reality 13): reconcile 22/22, judge 11/11, convergence 29/29, sweep 14/14, epoch 19/19, chaos 15/15, mutation_safety 8/8, gate_provider 17/18 RED. Done = gate_provider 18/18.
- Premise verification (HR-PREMISE-001) covers: evidence_bundle, mutation_drill, change_impact, parallel_mesh pure fns (`decide`, `CollisionDetector`), tower (baselines/families/select/ratchet/donegate) + `tools/family_baseline.py`. Record real signatures with file:line.
- Incumbent measurement: per-suite wall time of every `tools/test_gsd_x_goal_*.py`, judge replay time, one real goal's sweep->judge timeline. Anything unmeasurable is recorded UNKNOWN, never estimated.
- Phase output: `EVIDENCE.md` in this phase dir (commands, exit codes, observed output, Production Reality verdict, denominator rows moved, UKDL entries written). DENOMINATOR R01 row updated with evidence.
- Operating constraints in ROADMAP.md apply verbatim (worktree-only writes, PowerShell for git/python, absolute git path, hermetic tests, one msgfile per commit, never push, liveness exit 0 at phase end).

### Claude's Discretion
How the incumbent timeline is captured (existing GoalLog vs a hermetic fixture goal), as long as the source is named.

### Deferred Ideas (OUT OF SCOPE)
None -- everything else belongs to phases 2-10.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| R01 | Gate output lost on Windows (gate.py:72) -- FIX red-first + drill + UKDL | Sections 1-3, 6: exact line, red case, drill spec, UKDL shape |
</phase_requirements>

## Section 1. R01 -- exact current code and the red case

### 1.1 Where the code lives [VERIFIED: modules/gsd_x/goal/providers/gate.py:66-75]

GSD X goal package: `modules/gsd_x/goal/` containing `bind_mission.py brief.py contract.py convergence.py engine_identity.py epoch.py evidence.py git_state.py intervention.py judge.py log.py reconcile.py sweep.py workspace.py` and `providers/{claude,codex,gate,long_run}.py` [VERIFIED: Glob modules/gsd_x/**/*.py]. CLI = `modules/gsd_x/cli.py`.

The supervisor is a staticmethod returning a Python source string (`GateProvider._supervisor`). Line 72 is the `rc=` line:

```python
    @staticmethod
    def _supervisor() -> str:
        """Run the real gate, then record its exit status where anyone can read it."""
        return (
            "import json,subprocess,sys,time\n"
            "res=sys.argv[1]; cmd=sys.argv[2:]\n"
            "rc=subprocess.run(cmd).returncode\n"                      # <- gate.py:72  (R01)
            "json.dump({'exit_status':rc,'ended_at':time.time()}, open(res,'w'))\n"
            "sys.exit(rc)\n"
        )
```

It is launched at gate.py:126-135: `argv = [sys.executable, "-c", self._supervisor(), str(result), *g["command"]]`, `subprocess.Popen(argv, cwd=str(root), stdout=out, stderr=subprocess.STDOUT, env={..."PYTHONIOENCODING": "utf-8", ...}, start_new_session=os.name != "nt")` with `out = open(log, "wb")` (gate.py:127). `harvest` reads the log tail into `observed` (gate.py:178-181: `tail[-1][:200]`), which is the only consumer: the verdict carries `"observed": observed` (gate.py:197).

Mechanism [ASSUMED -- consistent with spec Reality 14 scratch repro 0 B vs 11 B, but not re-derived this session]: on Windows `subprocess.Popen` with all three std args `None` and default `close_fds=True` does not mark the parent's std handles inheritable, so the grandchild gets no usable stdout. Passing `stdout=sys.stdout, stderr=sys.stderr` makes Popen duplicate the supervisor's own (log-file) handles into the child.

**Recommended fix (one line, gate.py:72):**
`"rc=subprocess.run(cmd,stdout=sys.stdout,stderr=sys.stderr).returncode\n"` -- `sys` is already imported by the supervisor line 70. Do not change `Popen` at gate.py:128 (stdout/stderr already wired to the log).

### 1.2 The red case [VERIFIED: ran the suite once, output read from file this session]

`python tools/test_gsd_x_goal_gate_provider.py` -> exactly one FAIL, 17/18:

```
  FAIL V-GATE-VERDICT-FIELDS: verdict={'gate': 'gate_ok.py', 'exit_status': 0, 'observed': '', 'tree_hash': 'git:5633b7...', 'revision': 'rev1', 'gate_class': 'unit', 'gate_pin': [[...]]}
GSDX_GATE_PROVIDER_PASS=17/18  threshold=18/18
```

What it asserts [VERIFIED: tools/test_gsd_x_goal_gate_provider.py:138-143]:

```python
    check("V-GATE-VERDICT-FIELDS",
          v.get("exit_status") == 0 and v.get("tree_hash", "").startswith("git:")
          and v.get("revision") == "rev1" and v.get("gate_class") == "unit"
          and v.get("gate_pin") and "passed" in v.get("observed", ""),
```
The gate is `gate_ok.py` = `print('12 passed')` (test file :34). The only failing conjunct is `"passed" in observed` (observed == ''). So the RED is ALREADY driven by the existing suite; no new test is needed to see red. The suite has exactly 18 checks (TREE x3, PIN x2, OBSERVE-ENDED, VERDICT-FIELDS, NO-FAILURE-ON-PASS, FAILING-IS-EVIDENCE, 3 refusals, RUNNING, CANCEL-PRECONDITION, CANCEL-KILLS, CANCELLED-NO-VERDICT, PROBE-NOTHING, PROBE-FINDS).

Planning note: the one existing gate asserts several things (exit, tree, revision, class, pin, observed) in one conjunction, so a mutant that breaks *only* `observed` and a mutant that breaks another field both kill it. For a mutation drill of the R01 fix that is fine (the reverted fix makes `observed==''`), but a sharper regression is cheap and recommended: add one new gate (e.g. `V-GATE-OBSERVED-CAPTURES-GRANDCHILD`) asserting `r.verdicts[0]["observed"] == "12 passed"` AND for a failing gate `"1 failed" in r2.verdicts[0]["observed"]` (gate_bad prints `1 failed`, test :35-36). That would make the suite 19/19, which conflicts with the literal "done = 18/18" -- so recommend: keep VERDICT-FIELDS untouched (18/18 stays literally true) and put the sharper assertion in a NEW file or accept 19/19 with an EVIDENCE note. Decision for planner; default = do NOT add a gate to this suite (preserve the done criterion), drill against `V-GATE-VERDICT-FIELDS`.

### 1.3 Hermeticity of this suite [VERIFIED: tools/test_gsd_x_goal_gate_provider.py:26-47,99-101,180-181]
Uses `tempfile.mkdtemp` for the repo (`gsdx_gate_repo_`), run dir (`gsdx_gate_runs_`) and pidfile dir; sets only `os.environ["GSDX_TEST_PIDFILE"]`. It does NOT touch `GSDX_GOALS_ROOT`/HOME (it never imports the goal store). It is already hermetic for the live goal store; no redirect needed. The summary line is `GSDX_GATE_PROVIDER_PASS=n/m  threshold=m/m` (:219).

## Section 2. HR-PREMISE-001 -- real public signatures (all read this session)

**Result: every spec-named API exists. ONE spec-named symbol is in a different module than the spec's wording implies:** `decide` is NOT in `modules/parallel_mesh/`; it is `modules/cognitive_os/scheduler.py:94` (spec Reality 9 groups "parallel_mesh + cognitive_os/scheduler" and names `decide`, `CollisionDetector` together -- `CollisionDetector` IS in parallel_mesh). Record this in EVIDENCE.md so Phase 3 imports from the right module. The `modules/parallel_mesh/` package has no function named `decide` [VERIFIED: Grep `def decide` over modules/{parallel_mesh,cognitive_os}/*.py returned only process_governor.py:119, scheduler.py:94, scheduler.py:336 (`decide_spawn`), :396 (`decide_spawn_v2`)].

### 2.1 tools/evidence_bundle.py [VERIFIED: tools/evidence_bundle.py:47-205]
```python
def _proofs(root: Path, paths: list[str]) -> list[dict]                                   # :47  [{"path","sha256"}]
def run_check(root: Path, plan: str, task: str, criterion: str, command: str,
              artifacts: list[str], timeout: float = 600) -> str                          # :55  returns receipt rel path
def ticket_line(nonce: str) -> str                                                        # :90  "REVIEW-TICKET: {nonce}"
def ticket(root: Path, plan: str, task: str, artifacts: list[str]) -> tuple[str, str]     # :95  (rel path, nonce)
def write_review(root, plan, task, reply: str, reviewer: dict, artifacts: list[str],
                 check_paths: list[str]) -> tuple[str, ri.Intake]                         # :111
def collect(root: Path, plan: str, task: str, worker: str, criteria: list[str],
            artifacts: list[str], check_paths: list[str], review_path: str | None = None,
            required_reviewer: dict | None = None) -> dict                                # :134
def main(argv=None) -> int                                                                # :159
```
Receipts under `<root>/_logs/evidence/<plan>/<task>/` (:16, :80, :87). Check status = `"passed" if code == 0 and expected > 0 and checked == expected and not moved` (:77) and `_SUMMARY = re.compile(r"\b[A-Z][A-Z0-9_]*_PASS=(\d+)/(\d+)")` (:43) -- i.e. the same `<SUITE>_PASS=n/m` line the suites print is what evidence_bundle parses. CLI: `python tools/evidence_bundle.py --plan P --task T --worker W --artifact A --check "crit=cmd" [--ticket] [--review F --reviewer R --reviewer-model M --reviewer-effort E]`; exit 0 ok / 3 failures / 2 bridge down (:22, :205). `collect` goes through the Node bridge (`nb.call("evidenceCollector","collectEvidence",...)`, :153); it needs node.
The A->B->A hole is the comment at :140-141 (spec cited it as ":140"; confirmed). `run_check` uses `subprocess.run(argv, cwd=root, capture_output=True, ...)` (:68) -- NOTE this one captures output explicitly, so it is NOT affected by R01.

### 2.2 tools/mutation_drill.py [VERIFIED: tools/mutation_drill.py:159-209]
```python
def drill(spec: dict, timeout_s: int = 900) -> tuple[str, str]       # :159  -> (verdict, detail)
def main(argv=None) -> int                                           # :196  CLI: --spec <json file> ONLY
def gate_line(gate: str, word: str, out: str) -> bool                # :65
def detail_lines(out: str) -> list[str]                              # :74
class HarnessError(Exception)                                        # :57
```
Verdicts/exit codes (:205): `{"KILLED":0,"SURVIVED":1,"UNJUDGED":2,"CONTROL_INVALID":4}`, anything else (HARNESS) = 3. See Section 3 for how to use it.

### 2.3 tools/change_impact.py [VERIFIED: tools/change_impact.py:42-135]
```python
SCOPES = ("tools", "modules", "hooks", "lib")                        # :37
FLOOR = 50                                                           # :39
def _py_files(root: Path) -> list[str]                               # :42  rglob *.py, skips __pycache__ and "vendor"
def _resolve(name: str, known: set[str]) -> str | None               # :52
def edges_of(root: Path, rel: str, known: set[str]) -> set[str]      # :60  AST imports + literal tools|modules|hooks|lib/*.py paths
def manifest(root: Path) -> dict                                     # :90  {"schemaVersion":1,"entries":[{"path","kind":"test"|"file","dependsOn"}]}
def analyze(root: Path, changed: list[str]) -> dict                  # :98  via node bridge nb.call("changeImpact","analyzeChangeImpact",...)
def main(argv=None) -> int                                           # :108 --root --changed (repeatable) --since REF
```
Exit 0 coverage complete / 3 gaps / 2 bridge down or unjudged (:21, :128, :135). Python-only confirmed (:42-49 `rglob("*.py")`). `analyze()` returns `{"unjudged": True, "gaps": [...]}` on sweep-floor or bridge failure, else the analyzer's value with `["affected"]["test"]`, `["gaps"]`, `["coverageComplete"]` (:129-135).

### 2.4 parallel_mesh / scheduler pure functions
```python
# modules/cognitive_os/scheduler.py:94  [VERIFIED]
def decide(hot, cwd, *, is_new=True, cap: int = HOT_CAP, same_repo_cap: int = SAME_REPO_CAP,
           declared=None, hot_scopes=None) -> CapVerdict
@dataclass class CapVerdict: verdict: str ("proceed"|"refuse"), reasons: list, satisfy: list,
           hot_count: int, same_repo_count: int, cap: int = HOT_CAP, source: str   # :69-77
# modules/parallel_mesh/pm_02_intent.py  [VERIFIED]
def norm_scope(scope) -> tuple                                       # :58  sorted unique lowercased tokens; empty -> ()
@dataclass class Intent: sid: str; cwd: str; scope: tuple = (); objective: str = ""; mode: str = "";
                         model: str = ""; ts: str = ""               # :79-87  (to_json/from_json)
class CollisionDetector:                                             # :187
    @staticmethod overlap(declared, scope) -> list                   # :193  sorted(set(norm_scope(a)) & set(norm_scope(b)))
    @classmethod  collisions(cls, declared, intents, *, exclude_sid: str | None = None) -> list   # :199  [(sid, overlap_tokens)]
```
Pure-function caveats for Phase 3: `decide` treats a hot incumbent whose scope is UNKNOWN as a collision (:137-139 docstring) and is fail-safe to a blunt same-repo cap when `declared is None`; `CollisionDetector.collisions` consumes objects with `.sid` and `.scope` (so synthetic `Intent(sid="epoch:ep-1", cwd="", scope=(...))` works with no registry/filesystem). `overlap` is exact-token (file/dir string) intersection, NOT prefix-aware: `tools` and `tools/x.py` do NOT collide (set intersection of normalised tokens, :193-196) -- relevant to W2 "unsafe parallel writes" RED (planner: Phase 3 must add its own path-prefix rule or resource keys; do not assume `CollisionDetector` catches dir-vs-file overlap). [VERIFIED by reading :47-66,:187-209]

### 2.5 modules/tower [VERIFIED: file:line below]
```python
# baselines.py
BASELINES_DIR = <PP_ROOT>/vault/tower/baselines                                   # :26
REQUIRED = ("id", "requirement", "why", "origin", "class")                        # :34
def generations(family: str, root: str | None = None) -> list                      # :104
def load_generation(family, n, root=None) -> dict                                   # :111
def latest(family, root=None) -> dict | None                                        # :117
def active_entries(family, root=None) -> list   # newest gen, status != "reverted"  # :122
def generation_sha256(family, n, root=None) -> str                                  # :130
def write_generation(family, entries: list, reason: str, root=None, extra: dict|None=None) -> str  # :141  hard-link create-if-absent
def verify_origin(entry: dict, window: int = 3) -> str   # VERIFIED|WEAK|LINE_MISSING|FILE_MISSING|MALFORMED|MOVED|QUOTE_MISSING   # :62
# families.py
FAMILIES_DIR = <PP_ROOT>/vault/tower/families                                      # :33
@dataclass class Family: id, name, triggers, anti_triggers, repo_markers, delegate    # :46-54
def load_families(directory: str | None = None) -> list                            # :65
def classify_prompt(text: str, families: list | None = None) -> list               # :88  [(family_id, [hits])]
def repo_family_report(path, families=None) -> dict                                # :136 ; repo_families :178
# select.py
MAX_ENTRIES = 8 ; MAX_CHARS = 1400                                                 # :26-27
@dataclass class Selection: injected, deferred, reasons ; .overflow ; .as_dict()    # :30-43
def select_for_injection(entries: list, max_entries: int = MAX_ENTRIES, max_chars: int = MAX_CHARS) -> Selection   # :53
# ratchet.py
class RatchetRefusal(ValueError)                                                   # :46
def verify_chain(family: str, root: str | None = None) -> ChainReport              # :120  .ok .regressions .tampered .unanchored .generations
def revert(family, entry_id, reason, authority, root=None) -> str                  # :146
def promote(family, new_entries: list, reason: str, authority: str, root=None) -> str   # :164 (requires bl.REQUIRED keys per entry; default status "auto", check "")
# donegate.py  (REPORT-ONLY, no enforce mode, :1-6)
def judge(family: str, repo_root: str, registry: str | None = None, root: str | None = None, not_applicable: dict | None = None) -> dict   # :45
```
`tools/family_baseline.py` [VERIFIED :1-23, :143-155]: subcommands `build-b0 <family> <candidates.jsonl>`, `show`, `review`, `verify`, `revert <family> <id> --reason R --authority A`. There is NO `promote` subcommand (promotion is only `ratchet.promote` in-process) -- Phase 10 (R09) must build B0 via `build-b0` (needs a JSONL of candidates whose `origin` citations pass `verify_origin(window=0)`). Exit: 0 written/shown, 1 nothing verified, 2 usage / family already has B0 (:20-22). `verify` exits 0 iff `rep.ok` (:124). Families on disk are a directory of JSON files in `vault/tower/families/` (a new family = a new JSON file; no code change).

## Section 3. Mutation drill of the R01 fix (tools/mutation_drill.py, isolated copy + control)

CLI is `python tools/mutation_drill.py --spec <json>` only (:196-201); anchors travel in JSON because PowerShell 5.1 strips double quotes from native argv (:39). Run from the repo root (the drill resolves `file`/`test` with `Path(...).resolve()`, :160-161).

Spec for the R01 revert-mutant (write it with the Write tool under the phase dir, e.g. `.planning/workstreams/gsdx-pcc/phases/01-.../r01-drill.json`, UTF-8 no BOM -- the drill reads with `utf-8-sig` so a BOM is tolerated, :201):
```json
{"file": "modules/gsd_x/goal/providers/gate.py",
 "test": "tools/test_gsd_x_goal_gate_provider.py",
 "gate": "V-GATE-VERDICT-FIELDS",
 "old": "rc=subprocess.run(cmd,stdout=sys.stdout,stderr=sys.stderr).returncode",
 "new": "rc=subprocess.run(cmd).returncode"}
```
Why this works [VERIFIED by reading mutation_drill.py:93-139,159-193]:
- test (`tools/`) is NOT beside the subject (`modules/gsd_x/goal/providers/`) -> the "repo layout" branch (:134-139) copies `modules`, `tools`, `vault/pricing`, `vault/config` into a temp dir and runs the COPY of the test. The test sets `ROOT = Path(__file__).resolve().parents[1]` and `sys.path.insert(0, str(ROOT))` (test :19-20), so it imports the MUTANT from the copy. No `root_env` needed.
- The anchor must occur exactly once (`text.count(o) != 1` -> HARNESS, :167-169). Grep over `*.py` repo-wide: the only `_supervisor` / `rc=subprocess` hits are gate.py:67,72,126, so the anchor is unique both before (old text `rc=subprocess.run(cmd).returncode`) and after the fix.
- Control = clean copy must exit 0, print a `*_PASS=` line, show `PASS V-GATE-VERDICT-FIELDS` (:178-181). `gate_line` matches `PASS <gate>` after the test prints `  PASS V-GATE-VERDICT-FIELDS: ...` (test :90). Therefore:
  - BEFORE the fix, the drill (with old/new swapped, i.e. mutating the buggy line is a no-op) cannot be run meaningfully; run the *suite* for the red (17/18 observed).
  - AFTER the fix the control passes and the mutant (revert) must print `FAIL V-GATE-VERDICT-FIELDS` -> `MUTANT KILLED gate=V-GATE-VERDICT-FIELDS`, exit 0.
- Expected exit codes: KILLED 0, SURVIVED 1, UNJUDGED 2, HARNESS 3, CONTROL_INVALID 4 (:205). Anything but KILLED/0 is a stop, not a retry.
- The drill asserts the LIVE file's SHA-256 is unchanged (:185-186). Never use `tools/mutation_probe.py` (live-tree mutation; R04).
- Honest limit to record in EVIDENCE.md: `V-GATE-VERDICT-FIELDS` only checks stdout (`"passed" in observed`, `observed` = LAST log line, gate.py:181). A second mutant that drops only `stderr=sys.stderr` would SURVIVE (the supervisor's own stderr is merged into the log by `stderr=subprocess.STDOUT` at gate.py:129, but the grandchild's stderr would be lost). If the planner wants stderr covered, add a gate to a NEW test file or accept 19/19 (see 1.2); default: record the survivor as a known limit rather than weaken the "18/18" done criterion.
- Wall time: the drill runs the gate_provider suite twice (control + mutant), each includes two 120 s-sleep grandchildren killed by cancel; the suite itself takes seconds (cancel is exercised), so expect well under the 900 s default timeout (:159). Actual time = UNKNOWN until measured.

## Section 4. Incumbent measurement -- what exists and how to time it

### 4.1 Suites [VERIFIED: Glob tools/test_gsd_x_goal_*.py + Grep `_PASS=`]
17 files match `tools/test_gsd_x_goal_*.py`: `bind_mission chaos claude_providers cli codex_provider convergence engine_identity epoch gate_class gate_provider judge long_run_provider mutation mutation_safety reconcile sweep sweep_all`. All standalone scripts (`if __name__ == "__main__": sys.exit(main())`, e.g. gate_provider :223-224) printing `<SUITE>_PASS=n/m  threshold=n/m`:

| file | summary token (verified) |
|---|---|
| bind_mission | `GSDX_BIND_MISSION_PASS` (:154) |
| chaos | `GSDX_GOAL_CHAOS_PASS` (:276) |
| claude_providers | `GSDX_CLAUDE_PROVIDERS_PASS` (:206) |
| cli | `GSDX_GOAL_CLI_PASS` (:235) |
| codex_provider | `GSDX_CODEX_PROVIDER_PASS` (:235) |
| convergence | `GSDX_GOAL_CONV_PASS` (:237) |
| engine_identity | `GSDX_ENGINE_ID_PASS` (:149) |
| epoch | `GSDX_GOAL_EPOCH_PASS` (:205) |
| gate_class | `GSDX_GATE_CLASS_PASS` (:187) |
| gate_provider | `GSDX_GATE_PROVIDER_PASS` (:219) |
| judge | `GSDX_JUDGE_PASS` (:194) |
| long_run_provider | `GSDX_LONGRUN_PROVIDER_PASS` (:138) |
| mutation_safety | `GSDX_GOAL_MUTATION_SAFETY_PASS` (:115) |
| reconcile | `GSDX_RECONCILE_PASS` (:198) |
| sweep | `GSDX_GOAL_SWEEP_PASS` (:193) |
| sweep_all | `GSDX_SWEEP_ALL_PASS` (:143) |
| **mutation** | **NO `_PASS=` line** (Grep found none) -- see warning |

Also: `tools/test_gsd_x_goal.py` (the base V-GOAL- suite) exists but does NOT match the glob `test_gsd_x_goal_*.py` (no underscore after `goal`); it is the suite `test_gsd_x_goal_mutation.py` maps `V-GOAL-` to (mutation.py:45). Time it too, flagged as outside the roadmap's glob.

**WARNING -- `tools/test_gsd_x_goal_mutation.py`** [VERIFIED :1-45,:159-163]: it mutates the LIVE goal-package files in place (anchors in `log.py contract.py convergence.py epoch.py providers/gate.py long_run.py codex.py git_state.py`, restores by SHA-256) and prints no `_PASS=` summary. Roadmap done-gate item 1 says "every `tools/test_gsd_x_goal_*.py` exit 0", so it counts. Do NOT time it in the worktree proper. Time it inside a throwaway copy (copy `modules/`, `tools/`, `vault/pricing`, `vault/config` to a temp dir; its `ROOT = Path(__file__).resolve().parents[1]` then points at the copy) or record UNKNOWN. Its gate.py anchors (:159 `"        if self._was_cancelled(handle):\n            rc = None\n"`, :163 `'if g.get("class") not in GATE_CLASSES:'`) do not overlap line 72, so the R01 fix does not invalidate them. [VERIFIED: Grep GATEP]

### 4.2 Hermeticity (spec/roadmap constraint) [VERIFIED by Grep, partial]
Per-suite redirect evidence: `chaos:236` env `GSDX_GOALS_ROOT`, `sweep:77` `os.environ["GSDX_GOALS_ROOT"] = str(goals_root)`, `cli:63` env `GSDX_GOALS_ROOT`; `claude_providers:74-75` sandbox `LEDGER_ENV`/`DISABLE_FLAG_ENV`. The remaining suites show `mkdtemp`/HOME matches only by count (not read line by line) -> hermeticity of each of the other suites is [ASSUMED]. Cheap proof for the planner: before/after fingerprint of `C:\Users\User\.claude\state\gsd-x\` (file count + max mtime) around the whole timing run must be unchanged; and run each suite with `GSDX_GOALS_ROOT=<tmp>\goals`, `HOME`/`USERPROFILE=<tmp>` (pattern tools/test_family_injection.py:78-82: `env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONIOENCODING="utf-8")`, `os.environ.update(HOME=home, USERPROFILE=home)`). Note `GSDX_GOALS_ROOT` semantics: `log.goals_root()` (log.py:100-102) returns the env value AS the goals dir; `sweep.state_dir()` (sweep.py:52-55) strips a trailing `goals` -> set it to `<tmp>\goals` so `autonomy_gates.json` lands in `<tmp>` and not beside the tmp root.

### 4.3 How to time (no code change needed)
Each suite: PowerShell `Stopwatch` around `& python tools\test_gsd_x_goal_X.py *> <tmp>\X.log` (file redirect, no pipe: project rule), record `$LASTEXITCODE`, wall seconds, and the `_PASS=` line read back from the log. Serial, one at a time (the machine is shared and RAM-starved sessions skew numbers: record `Get-CimInstance Win32_OperatingSystem FreePhysicalMemory` before the run). Report min of N=3 plus the first run (cold). Never time in parallel with the drill. [Method = ASSUMED recommendation; numbers = UNKNOWN until Phase 1 executes.] Total of the 16 summary-bearing suites + gate_provider is the "incumbent full goal-suite wall".

### 4.4 Judge replay time -- ALREADY INSTRUMENTED [VERIFIED: modules/gsd_x/goal/judge.py:162-173]
`judge()` re-runs every SATISFIED obligation's pinned gate SERIALLY (`for o in satisfied:` :147; `subprocess.run(argv, cwd=..., capture_output=True, text=True, timeout=...)` :165) and stores `"seconds": round(time.time() - started, 1)` per gate (:173) plus the receipt `ts`. So replay time = sum of per-gate `seconds` in a `goal.judged` event (+ pin checks). `judge` is NOT affected by R01 (it uses `capture_output=True`).
CLI: `python tools/gsd_x_goal.py judge --goal <id> --root <repo> [--worktree <path>] [--record]` [VERIFIED tools/gsd_x_goal.py:20,319-330]. WITHOUT `--record` it only prints the receipt JSON and writes nothing (record is gated on `if args.record:` :325). It refuses (UNJUDGEABLE) when the process env has `GSDX_GOAL_EPOCH` (judge.py:125-128), when the worktree does not exist, or when `tree_id(worktree)` != the state's tree (judge.py:132-136). Exit 0 iff PASS.

### 4.5 A REAL recorded goal exists (read-only) [VERIFIED: files read this session]
Live store `C:\Users\User\.claude\state\gsd-x\goals\` holds three goals: `1f924bc.../g-001-smoke-runner` (>=123 events, `goal.judged` at seq 90 and 123), `4a22656.../g-002-router-surface` (50 events), `8f11bb0.../ksr-p2w25-fp028`. Best candidate: **g-002-router-surface** (small, complete, ends in a judge PASS):
- seq 1 `goal.declared` ts `2026-09-22T20:39:03.273427+00:00` (actor owner), scope paths `LEARNINGS.md gates router.py` (000001.json)
- epoch events seen (type via Grep): dispatching 18,33,38,43; running 19,24,29,34,39,44; ended 22,27,32,37,47 (6 gate epochs)
- seq 50 `goal.judged` ts `2026-09-22T20:41:39.028391+00:00`, receipt ts `20:41:38.937218`, verdict PASS, "6 pinned gate(s) re-run and passed", per-gate seconds 0.7 + 0.8 + 0.5 + 0.1 + 0.4 + 0.4 = **2.9 s judge replay** (000050.json). Declare->judge = 2 min 36 s of wall (20:39:03 -> 20:41:39), for 6 tiny gates.
Timeline source options: (a) read-only reader `GoalLog(repo_id, goal_id).read()` (log.py:152-178, pure read, verifies the digest chain) over the live path -- allowed (no write); `GoalLog.__init__(repo, goal_id, base=None)` takes a `base` Path (log.py:141-147) so a COPY of the store can be passed instead -- safest (copy the goal dir to temp first). Print `ts` deltas per `type` (`goal.declared`, `epoch.dispatching`, `epoch.running`, `epoch.ended`, `epoch.receipt`, `goal.judged`; type constants epoch.py:43-46, judge.py:44). Per-epoch gate wall = `cost.seconds` of the receipt (gate.py:209). (b) Hermetic fixture goal through the real CLI (below) to get a controlled sweep->judge timeline that includes the R01-fixed `observed`.
NOTE: g-001/g-002 predate this branch's engine at fbca24fc; their gates were measured on the Owner's machine at that time -- cite them as "recorded goals, 2026-09-22", not as current-engine measurements.

### 4.6 Hermetic fixture goal via the REAL CLI (no autonomy gate needed) [VERIFIED: tools/gsd_x_goal.py:66-97,286-330; sweep.py:278-391]
`sweep_goal` is the one-pass driver and is what `reconcile --apply` calls (gsd_x_goal.py:311); it does NOT call `autonomy_verdict` (only `sweep()` does, sweep.py:394-400), so a fixture run needs no `record-gates` (which would run the judge+chaos suites, sweep.py:86-109). Sequence in a temp git repo `R` with a gate file (e.g. copy of the `gate_ok.py` pattern, test :34) and `GSDX_GOALS_ROOT=<tmp>\goals`:
1. `declare --goal g-w0 --root R --intent "..." --scope-path gates`  (prints `store:` path)
2. `plane --goal g-w0 --root R --plane REALITY --not-applicable --reason "..."` (docstring example, gsd_x_goal.py:6-7; REALITY must be dispositioned or a runtime-class gate named -- sweep.py:352-362 refuses to dispatch a REALITY obligation without a runtime gate class)
3. `oblige --goal g-w0 --root R --id ob-1 --plane OUTCOME --text "..." --gate "<python> gates/gate_ok.py" --gate-file gates/gate_ok.py`
4. repeat `reconcile --goal g-w0 --root R --apply --provider gate` : pass1 dispatches an epoch (non-blocking, returns immediately, sweep.py:382-385), later passes harvest (sweep.py:324-345), until `status` shows the obligation SATISFIED; each call prints what it did.
5. `judge --goal g-w0 --root R --worktree R` (read-only) then optionally `--record`; read the log's `ts` series with `GoalLog(...).read()`.
Wait cadence between passes is the harness' (`wait_ended` in the suite polls `observe` every 0.05 s, gate_provider test :50-57); for the incumbent timeline record BOTH the pass-granular wall (what a five-minute scheduler would see) and the gate's own `cost.seconds`. Anything not observable (e.g. real scheduler cadence on this host) = UNKNOWN.
Caveat: the repo must have a single root commit (`log.repo_id` refuses otherwise, log.py:84-97) and `file_pin` needs the gate file committed/present (git_state). Reuse the test's `make_repo()` shape (test :31-47).

## Section 5. UKDL T-entry [VERIFIED: vault/knowledge_base/ukdl-universal.md:246-260, 15262-15285]
File is 15285 lines, 146 `##` sections. Two coexisting shapes: `### T-<SLUG>-001` under a topic `## ` section (e.g. :246 `### T-DRILL-VERDICT-WITHOUT-CONTROL-001`) and `## T-<SLUG>-001 — <title>` (e.g. :844). Newest section (tail, :15262-15285) is the model to copy:
```
## <Program / topic> (<date>)

Source: <where it came from>. ... Status: ...

### Traps

### T-<LONG-DESCRIPTIVE-SLUG>-001

<one paragraph: what the instrument/behaviour did wrong, measured date, owner file:line @ commit, how it was
proven, the fix, then a "PR:" one-liner> #CROSS-PROJECT
```
(real example, :246-260: measured date, `file` + commit `94c55903`, the symptom list, "Fix:", "Pinned by `test_...`", then `PR: control -> mutate -> named discriminator -> explicit verdict; ... #CROSS-PROJECT`).
**There is no next-free-id counter**: ids are `T-<descriptive-slug>-001` (uniqueness by slug; a repeat of the same slug would be `-002`). Grep for `T-(SUBPROCESS|CHILD|GATE-OUTPUT|STD|HANDLE|WINDOWS-GRANDCHILD|OBSERVED)...` found NO existing id, so a new slug is free. Suggested id: `T-SUBPROCESS-WITHOUT-INHERITED-STD-HANDLES-LOSES-GRANDCHILD-OUTPUT-ON-WINDOWS-001`. Append a new `## GSD X proof-conserving convergence, W0 (2026-10-07)` section at end of file (do not renumber/insert mid-file: file is 15k lines, append is the convention at :15262). Content must cite: `modules/gsd_x/goal/providers/gate.py:72`, the commit of the fix, the red `17/18 V-GATE-VERDICT-FIELDS`, the 0 B vs 11 B scratch repro, the drill verdict (KILLED + control), and the PR line ("a supervisor that spawns a child must pass its std handles explicitly; absence of output is a measurement defect, assert on a non-empty observed value"). Router freshness: `tools/router_freshness_gate.py` is store-level (walks rule stores off disk, :1-17) and does not require a per-id pointer, so a new id needs no MEMORY.md/router edit [CITED: its docstring]; run it only if the planner wants belt-and-braces. Never edit the user's global `~/.claude` files (roadmap constraint).

## Section 6. Liveness (modules/liveness/reachability.py) -- IMPORTANT BASELINE FINDING

- Usage [VERIFIED :725-736]: `python modules/liveness/reachability.py` -> exit 0 iff no offenders, else 1; `--json` prints `{"passed","offenders","rows"}`; `--baseline` writes the CURRENT unreachable-and-unclassified set into `vault/liveness/reachability_registry.json` `known_orphans` (:705-722) and returns 0.
- APERTURE: only packages under `modules/` are inventoried (`module_inventory`, :268-296; the report prints "tools/ is NOT scanned", :687-690). **New `tools/test_*.py` files or new `tools/*.py` scripts need NO registry entry.** Phase 1 adds no module (it edits `providers/gate.py` and adds files under `tools/` and `.planning/`), so Phase 1 itself creates no new liveness debt.
- **MEASURED baseline in this worktree (ran once, output read from file): exit 1, 57 offenders** (offenders listed at json lines 4-459, 8 lines each). Names include all `gsd_x/goal/*` (17 units incl. `providers/*`), all `gsd_x/mission/*` (9), `tower/donegate`, `tower/ratchet`, `knowledge_acquisition/*`, `keos_qwen/*`, `capability_runtime/agent_bundle`, `surface_architecture/verticals/*`. `gsd_x/cli` is NOT an offender (reachable through `hooks/gsd_x_tier.js`). Likely cause [ASSUMED]: the goal/mission packages are reached only via `tools/gsd_x_goal.py` / `tools/gsd_x_mission.py`, which are not seed surfaces, and this branch's `vault/liveness/reachability_registry.json` `known_orphans` predates them. So the ROADMAP constraint "liveness exit 0 at every phase end" is **already violated at the base commit fbca24fc, independent of this mission**. The planner must not discover this at phase end. Options (decision needed, record in EVIDENCE.md, do not block): (a) run `--baseline` once in its own commit, labelled "freeze pre-existing standing debt (57 named modules) so new orphans fail", then verify exit 0 and that the diff of `known_orphans` equals exactly the 57 named offenders (this is the module's documented use, :706-711) -- but it also freezes `tower/donegate`/`ratchet` which Phase 10 wants to wire, so pair the commit with an OWNER_QUEUE note; or (b) declare the 57 in the registry classes with notes. Default recommendation: (a), because it is the documented ratchet and changes no behaviour; record as a denominator row if one is added.
- Why this matters for the pass criterion: running the gate costs one command (~seconds) and must be re-run after the baseline commit as the actual phase-end check.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Gate execution + output capture | Gate supervisor (providers/gate.py, OS process tier) | Run-dir log file | Output must be captured where the process is spawned; the log is the only durable record |
| Evidence verdict (`observed`) | Gate provider harvest (gate.py:162-210) | convergence.evaluate | Provider reports, convergence judges (module docstring :9-11) |
| Judge replay | goal/judge.py | tools/gsd_x_goal.py CLI | Independent re-run by the judge process (builder may not judge, judge.py:125-128) |
| Premise/impact/mutation tooling | tools/ (evidence_bundle, change_impact, mutation_drill) | modules/external_assimilation node_bridge | Python wrappers over a Node collector/analyzer |
| Baseline ratchet | modules/tower | tools/family_baseline.py | Library + CLI; donegate is report-only |
| Incumbent measurement | Phase-1 scripts (tools/ or temp) + GoalLog reader | goal CLI | Read-only projection over existing logs |

## Standard Stack

No external packages. Python 3.12 stdlib only (`subprocess`, `json`, `tempfile`, `time`); Git 2.x via `C:\Program Files\Git\cmd\git.exe`; Node only through the existing bridge (evidence_bundle/change_impact). **Package Legitimacy Audit: no external packages installed in this phase -- N/A.**

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mutation evidence | A private revert-and-run script | `tools/mutation_drill.py --spec` | Isolated copy, control run, live SHA assertion; private replicas are the documented failure (UKDL T-DRILL-VERDICT-WITHOUT-CONTROL-001 :246-260) |
| Suite pass accounting | Parsing prose | the `<SUITE>_PASS=n/m` line (same regex as evidence_bundle.py:43) | one grammar for suites, drill and evidence bundle |
| Goal timeline | Re-parsing event JSON by hand | `GoalLog.read()` (verifies the chain, log.py:152-178) | chain verification for free; hand parsing can read a corrupt log as valid |
| Hermetic temp repo | New git fixture scaffolding | `make_repo()` shape (gate_provider test :31-47) | already proven in 17/18 |
| UKDL ids | A counter/registry | slug convention + append at tail | no counter exists |

## Common Pitfalls

1. **Fix without red.** The red already exists (17/18). Run and capture it BEFORE editing gate.py:72, commit nothing until the red output is saved in EVIDENCE.md (Regla: every optimisation lands RED-first).
2. **Drill with a bad control.** If run before the fix the control is CONTROL_INVALID (exit 4) -- that is correct, not a bug; do not "fix" the drill. After the fix expect KILLED/0.
3. **PowerShell strips quotes from argv** (drill docstring :39): put anchors in the JSON spec file, never on the command line.
4. **`git` not on PowerShell PATH** (project rule): always `& 'C:\Program Files\Git\cmd\git.exe' -C C:\Users\User\Apps\pp-gsdx-pcc ...`; `tools/change_impact.py:122` already hard-codes this path.
5. **This research session had no PowerShell tool.** Python was run through Bash with output redirected to a file; the executing agent should use PowerShell per the roadmap. The Windows Bash guard blocks `cat`; read logs with the Read tool.
6. **Timing the mutation suite in the worktree** mutates live goal code; use a copy (4.1 warning).
7. **Liveness gate is red at baseline** (Section 6); do not claim "exit 0" without first deciding the baseline commit.
8. **observed is only the LAST log line (`tail[-1][:200]`, gate.py:179-181)**; the fix makes it non-empty for `gate_ok.py` (`12 passed`), but a gate whose last line is blank/noise yields a noisy `observed`. Out of scope for R01; note for D13 certificates (Phase 4).
9. **Stale temp dirs**: the gate_provider suite creates `gsdx_gate_*` temp dirs and never removes them; harmless, but a `Remove-Item` cleanup is a destructive action -- only delete dirs this mission created, by exact name.
10. **`decide` module location** (Section 2): importing `modules.parallel_mesh.decide` fails; use `modules.cognitive_os.scheduler.decide`.

## Code Examples

R01 fix (the whole production change) [source: modules/gsd_x/goal/providers/gate.py:72]:
```python
            "rc=subprocess.run(cmd,stdout=sys.stdout,stderr=sys.stderr).returncode\n"
```
Read-only timeline over a COPY of a recorded goal (pattern for the Phase 1 measurement script; `GoalLog` verifies the hash chain on read):
```python
# Source: modules/gsd_x/goal/log.py:141-178 (GoalLog.__init__(repo, goal_id, base), .read())
from pathlib import Path
from datetime import datetime
from modules.gsd_x.goal.log import GoalLog
base = Path(r"<TEMP>\copy-of-goals")                # a copy, never the live store
ev = GoalLog("4a226561feb32dc7df40388410bbde2f67e83614", "g-002-router-surface", base=base).read()
t0 = datetime.fromisoformat(ev[0].ts)
for e in ev:
    print(f"{(datetime.fromisoformat(e.ts) - t0).total_seconds():9.3f}s  #{e.seq:03d}  {e.type}")
```
Hermetic env pattern [source: tools/test_family_injection.py:78-82]:
```python
home = tempfile.mkdtemp(prefix="finj-home-")
env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONIOENCODING="utf-8")
os.environ.update(HOME=home, USERPROFILE=home)
```

## State of the Art

N/A (internal runtime). The one external fact -- Windows `subprocess.Popen` with all std handles `None` and `close_fds=True` not inheriting the parent's std handles -- is [ASSUMED] from the measured 0 B / 11 B repro (spec Reality 14), not re-derived; the red/green suite result is the authoritative proof, not the mechanism.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Windows handle-inheritance mechanism explains R01 | 1.1 | Low: fix is validated empirically by the suite (17/18 -> 18/18) and the spec's 0 B/11 B repro |
| A2 | The other 15 suites are hermetic (only 4 checked line-level) | 4.2 | Medium: a suite could write the live store; mitigated by the before/after fingerprint of `~/.claude/state/gsd-x` |
| A3 | `gsd_x/goal` + `gsd_x/mission` orphan status is due to tools/ not being a seed and a stale registry | 6 | Low: only affects the explanation; the 57-offender red is measured |
| A4 | Timing method (serial, min of 3, free-RAM note) is sufficient for an "honest baseline" | 4.3 | Low/Medium: noisy shared host; keep first-run + min and say so |
| A5 | `claude_providers`/`codex_provider`/`long_run_provider` suites do not spawn real `claude`/`codex` accounts | 4.2 | Medium: a real spawn would spend quota; executor must read their sandbox sections (claude_providers:74-75 sandboxes the ledger) before running |
| A6 | A stderr-only mutant would survive `V-GATE-VERDICT-FIELDS` | 3 | Low: reasoned from reading the gate, not run |

## Open Questions

1. **Liveness baseline red (57 offenders).** Freeze via `--baseline` (recommended) or declare per module? Needs a recorded decision (not an Owner block per roadmap: record and continue). Does the same red exist on the main checkout's branch? UNKNOWN (not probed; main checkout is off-limits for writes, read-only probe possible).
2. **Add a sharper regression gate (19/19) or keep 18/18 literal?** Recommendation: keep 18/18, record the stderr survivor.
3. **Does `observed` for `gate_bad.py` also fill (`1 failed`)?** Expected yes (same path); confirm in the post-fix run output.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | everything | yes | C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe (ran the gate_provider suite and liveness with it) | -- |
| Git | suite fixtures, drill repo-root | yes (suite ran) | `C:\Program Files\Git\cmd\git.exe` | -- |
| Node (bridge) | evidence_bundle.collect / change_impact.analyze premise runs | NOT PROBED | -- | premise = signature read only (done); a runtime probe of the bridge is optional |
| PowerShell tool | roadmap-mandated shell | NOT available in this research session | -- | executor session expected to have it; Bash fallback used here for 2 python runs |
| Live goal store | recorded timeline | yes (3 goals, read) | `~/.claude/state/gsd-x/goals/` | hermetic fixture goal (4.6) |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | none (project convention): standalone Python scripts printing `<SUITE>_PASS=n/m  threshold=n/m`, exit 0 iff all pass |
| Config file | none |
| Quick run command | `python tools/test_gsd_x_goal_gate_provider.py` (red/green for R01) |
| Full suite command | each `tools/test_gsd_x_goal_*.py` serially (+ `tools/test_gsd_x_goal.py`); mutation suite only in a throwaway copy |

### Phase Requirements -> Test Map
| Req / Success criterion | Behavior | Test Type | Automated Command | Failing signal | File Exists? |
|--------|----------|-----------|-------------------|----------------|-------------|
| SC1 premise check | every spec-named API exists with recorded signature | static read + import smoke | `python -c "import tools.evidence_bundle, tools.change_impact, tools.mutation_drill; from modules.parallel_mesh.pm_02_intent import CollisionDetector; from modules.cognitive_os.scheduler import decide; from modules.tower import baselines, families, select, ratchet, donegate"` run from repo root with `python -I`-safe cwd (note tools/ siblings import `review_intake` via sys.path insert) | ImportError / AttributeError names the missing symbol | commands only |
| R01 red | gate_provider RED before fix | existing suite | `python tools/test_gsd_x_goal_gate_provider.py` | `FAIL V-GATE-VERDICT-FIELDS`, `GSDX_GATE_PROVIDER_PASS=17/18`, exit 1 (OBSERVED this session) | yes |
| R01 green | gate_provider 18/18 | existing suite | same | any FAIL line / exit != 0 / summary != `18/18` | yes |
| R01 mutation | revert of fix is killed for the right reason, with control | drill | `python tools/mutation_drill.py --spec <phase>\r01-drill.json` | `MUTANT SURVIVED` (exit 1), `CONTROL_INVALID` (4), `UNJUDGED` (2), `HARNESS` (3); only `MUTANT KILLED gate=V-GATE-VERDICT-FIELDS` + exit 0 passes | spec file = Wave 0 |
| R01 no collateral | other goal suites unchanged | existing suites | each of the 16 summary suites; compare to the spec baseline counts (reconcile 22/22, judge 11/11, convergence 29/29, sweep 14/14, epoch 19/19, chaos 15/15, mutation_safety 8/8) | count differs from baseline | yes |
| R01 UKDL | T-entry written | grep | `Select-String -Path vault\knowledge_base\ukdl-universal.md -Pattern '^### T-SUBPROCESS-'` | no match | entry = Wave 0 |
| SC3 incumbent table | per-suite wall time, judge replay, sweep->judge timeline | measurement script + EVIDENCE.md | timing loop (4.3); `judge` w/o `--record` (4.4); `GoalLog.read()` timeline (4.5/4.6) | a number without its command + exit code; an estimated value instead of UNKNOWN | script = Wave 0 |
| Liveness | phase-end gate | liveness | `python modules/liveness/reachability.py` | exit 1 + named offenders (baseline today: 57) | yes |
| Hermeticity | no live-store write | before/after fingerprint | file count + max mtime of `C:\Users\User\.claude\state\gsd-x` equal before and after the run | any change | script = Wave 0 |

### Sampling Rate
- Per task commit: `python tools/test_gsd_x_goal_gate_provider.py` (fast).
- Per wave merge: all 16 summary suites serially + `tools/test_gsd_x_goal.py`.
- Phase gate: gate_provider 18/18, drill KILLED, liveness decision recorded, EVIDENCE.md complete.

### Wave 0 Gaps
- [ ] `r01-drill.json` (drill spec, Section 3)
- [ ] timing/timeline script (throwaway under a temp dir or `tools/`; `tools/` needs no liveness entry)
- [ ] baseline-fingerprint step for `~/.claude/state/gsd-x`
- [ ] UKDL entry text

## Security Domain

security_enforcement not read from config this session (absent => enabled). Phase scope is local tooling; no auth/session/crypto surface.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication / V3 Session | no | -- |
| V4 Access Control | no (but: worktree-only writes, never the main checkout or `~/.claude`) | roadmap operating constraints |
| V5 Input Validation | yes (gate command argv) | argv list, never shell string (`_argv` judge.py:97-111; supervisor passes `cmd` list) |
| V6 Cryptography | no (sha256 pins only, stdlib) | -- |

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Mutation drill touching live files | Tampering | drill works in an isolated copy and asserts live SHA unchanged (drill :185-186) |
| Captured gate output leaking secrets into goal log | Information disclosure | `observed` is `tail[-1][:200]`; EVIDENCE.md must not paste env or tokens (HR-SECRET-002) |
| Timing run writing the live goal store | Tampering | hermetic env + before/after fingerprint |

## Project Constraints (from CLAUDE.md)
- Windows: PowerShell tool for git/python/mix; absolute git path; no `cat/head/grep` via Bash; Bash only for POSIX; never `Agent` parallel batches >2; no background dev servers.
- Reality Contract: no stubs/placeholders in shipped files; DONE = observed evidence (HR-OUTPUT-002); HR-PREMISE-001 premise check before acting on a plan (this document is that record for the spec's APIs).
- Hard rules: never edit `~/.claude/settings.json|CLAUDE.md|rules|hooks`; secrets never logged; commit with `git commit -F <msgfile>`, one msgfile per commit, verify `git log -1 --format=%s`, end message with the session Co-Authored-By line, never push.
- Liveness Standard: wire or declare each new module; `python modules/liveness/reachability.py` (see Section 6 for the red baseline).
- Roadmap: hermetic tests (`GSDX_GOALS_ROOT`/HOME redirect), summary line `<SUITE>_PASS=n/m  threshold=n/m`, RED-first, drill never probe, EVIDENCE.md with commands/exit codes/observed output/Production Reality verdict.

## Sources

### Primary (HIGH) -- all read in-session
- modules/gsd_x/goal/providers/gate.py, judge.py, sweep.py, log.py; tools/gsd_x_goal.py
- tools/test_gsd_x_goal_gate_provider.py, test_gsd_x_goal_mutation.py (header), test_family_injection.py
- tools/mutation_drill.py, evidence_bundle.py, change_impact.py, family_baseline.py
- modules/cognitive_os/scheduler.py, modules/parallel_mesh/pm_02_intent.py, modules/tower/{baselines,families,select,ratchet,donegate}.py
- modules/liveness/reachability.py; vault/knowledge_base/ukdl-universal.md
- Live goal log files `~/.claude/state/gsd-x/goals/4a22.../g-002-router-surface/000001.json, 000050.json`
### Observed by running (this session)
- `python tools/test_gsd_x_goal_gate_provider.py` -> 17/18, FAIL V-GATE-VERDICT-FIELDS (`observed: ''`)
- `python modules/liveness/reachability.py --json` -> passed=false, 57 offenders, exit 1

## Metadata
**Confidence:** Standard stack N/A (stdlib); architecture/premise HIGH (read); R01 fix HIGH (one line, red already observed, mechanism MEDIUM); timing numbers NOT YET MEASURED (UNKNOWN by design).
**Research date:** 2026-10-07 · **Valid until:** until gate.py/judge.py/mutation_drill.py change on gsdx/pcc (check `git log` on those files).

