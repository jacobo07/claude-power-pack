# Phase 1 -- HR-PREMISE-001 premise record

Date 2026-10-07, worktree HEAD `f42928f6` (branch gsdx/pcc).

| Run | Command | Result |
|---|---|---|
| real set (8 files, 54 attrs) | `python modules/error_prevention/premise_verifier.py --premises PHASE_DIR/01-premises.json` | `EXIT=0` (silent on success) -- `01-premises.log` |
| control (known false) | `python modules/error_prevention/premise_verifier.py --premises PHASE_DIR/01-premises-control.json` | `[FAIL] decide in modules.parallel_mesh.pm_02_intent`, `EXIT=1` -- `01-premises-control.log` |

The control proves the verifier can say no on this input, so the green run of the real set means something. No corrections were needed: `01-premises-corrected.*` do not exist.

Signatures were read from source by a line-anchored scan (`^(def|class) ATTR\b`, `^ATTR\s*[:=]`, `^    def ATTR\b`) in this task; wrapped `def` lines are joined, and lines over 160 characters are cut with `...`.

| API | kind | real signature | file:line | spec reference |
|---|---|---|---|---|
| `tools.evidence_bundle.run_check` | function | `def run_check(root: Path, plan: str, task: str, criterion: str, command: str, artifacts: list[str], timeout: float = 600) -> str:` | tools/evidence_bundle.py:55 | Reality 10 / Phase 4 |
| `tools.evidence_bundle.ticket_line` | function | `def ticket_line(nonce: str) -> str:` | tools/evidence_bundle.py:90 | Reality 10 / Phase 4 |
| `tools.evidence_bundle.ticket` | function | `def ticket(root: Path, plan: str, task: str, artifacts: list[str]) -> tuple[str, str]:` | tools/evidence_bundle.py:95 | Reality 10 / Phase 4 |
| `tools.evidence_bundle.write_review` | function | `def write_review(root: Path, plan: str, task: str, reply: str, reviewer: dict, artifacts: list[str], check_paths: list[str]) -> tuple[str, ri.Intake]:` | tools/evidence_bundle.py:111 | Reality 10 / Phase 4 |
| `tools.evidence_bundle.collect` | function | `def collect(root: Path, plan: str, task: str, worker: str, criteria: list[str], artifacts: list[str], check_paths: list[str], review_path: str \| None = None...` | tools/evidence_bundle.py:134 | Reality 10 / Phase 4 |
| `tools.evidence_bundle.main` | function | `def main(argv=None) -> int:` | tools/evidence_bundle.py:159 | Reality 10 / Phase 4 |
| `tools.mutation_drill.drill` | function | `def drill(spec: dict, timeout_s: int = 900) -> tuple[str, str]:` | tools/mutation_drill.py:159 | Phase 9 mutant farm |
| `tools.mutation_drill.gate_line` | function | `def gate_line(gate: str, word: str, out: str) -> bool:` | tools/mutation_drill.py:65 | Phase 9 mutant farm |
| `tools.mutation_drill.detail_lines` | function | `def detail_lines(out: str) -> list[str]:` | tools/mutation_drill.py:74 | Phase 9 mutant farm |
| `tools.mutation_drill.HarnessError` | class | `class HarnessError(Exception):` | tools/mutation_drill.py:57 | Phase 9 mutant farm |
| `tools.mutation_drill.main` | function | `def main(argv=None) -> int:` | tools/mutation_drill.py:196 | Phase 9 mutant farm |
| `tools.change_impact.SCOPES` | constant | `SCOPES = ("tools", "modules", "hooks", "lib")` | tools/change_impact.py:37 | Phase 5 impact adapter |
| `tools.change_impact.FLOOR` | constant | `FLOOR = 50  # a sweep that found fewer Python files has stopped seeing code` | tools/change_impact.py:39 | Phase 5 impact adapter |
| `tools.change_impact.edges_of` | function | `def edges_of(root: Path, rel: str, known: set[str]) -> set[str]:` | tools/change_impact.py:60 | Phase 5 impact adapter |
| `tools.change_impact.manifest` | function | `def manifest(root: Path) -> dict:` | tools/change_impact.py:90 | Phase 5 impact adapter |
| `tools.change_impact.analyze` | function | `def analyze(root: Path, changed: list[str]) -> dict:` | tools/change_impact.py:98 | Phase 5 impact adapter |
| `tools.change_impact.main` | function | `def main(argv=None) -> int:` | tools/change_impact.py:108 | Phase 5 impact adapter |
| `modules.cognitive_os.scheduler.decide` | function | `def decide(hot, cwd, *, is_new=True, cap: int = HOT_CAP, same_repo_cap: int = SAME_REPO_CAP, declared=None, hot_scopes=None) -> CapVerdict:` | modules/cognitive_os/scheduler.py:94 | Reality 9 |
| `modules.cognitive_os.scheduler.CapVerdict` | class | `class CapVerdict:` | modules/cognitive_os/scheduler.py:70 | Reality 9 |
| `modules.parallel_mesh.pm_02_intent.CollisionDetector` | class | `class CollisionDetector:` | modules/parallel_mesh/pm_02_intent.py:187 | Reality 9 |
| `modules.parallel_mesh.pm_02_intent.Intent` | class | `class Intent:` | modules/parallel_mesh/pm_02_intent.py:80 | Reality 9 |
| `modules.parallel_mesh.pm_02_intent.norm_scope` | function | `def norm_scope(scope) -> tuple:` | modules/parallel_mesh/pm_02_intent.py:58 | Reality 9 |
| `modules.tower.baselines.generations` | function | `def generations(family: str, root: str \| None = None) -> list:` | modules/tower/baselines.py:104 | Phase 10 baseline ratchet |
| `modules.tower.baselines.load_generation` | function | `def load_generation(family: str, n: int, root: str \| None = None) -> dict:` | modules/tower/baselines.py:111 | Phase 10 baseline ratchet |
| `modules.tower.baselines.latest` | function | `def latest(family: str, root: str \| None = None) -> dict \| None:` | modules/tower/baselines.py:117 | Phase 10 baseline ratchet |
| `modules.tower.baselines.active_entries` | function | `def active_entries(family: str, root: str \| None = None) -> list:` | modules/tower/baselines.py:122 | Phase 10 baseline ratchet |
| `modules.tower.baselines.generation_sha256` | function | `def generation_sha256(family: str, n: int, root: str \| None = None) -> str:` | modules/tower/baselines.py:130 | Phase 10 baseline ratchet |
| `modules.tower.baselines.write_generation` | function | `def write_generation(family: str, entries: list, reason: str, root: str \| None = None, extra: dict \| None = None) -> str:` | modules/tower/baselines.py:141 | Phase 10 baseline ratchet |
| `modules.tower.baselines.verify_origin` | function | `def verify_origin(entry: dict, window: int = 3) -> str:` | modules/tower/baselines.py:62 | Phase 10 baseline ratchet |
| `modules.tower.baselines.REQUIRED` | constant | `REQUIRED = ("id", "requirement", "why", "origin", "class")` | modules/tower/baselines.py:34 | Phase 10 baseline ratchet |
| `modules.tower.baselines.BASELINES_DIR` | constant | `BASELINES_DIR = os.path.join(_PP_ROOT, "vault", "tower", "baselines")` | modules/tower/baselines.py:26 | Phase 10 baseline ratchet |
| `modules.tower.families.load_families` | function | `def load_families(directory: str \| None = None) -> list:` | modules/tower/families.py:65 | Phase 10 |
| `modules.tower.families.classify_prompt` | function | `def classify_prompt(text: str, families: list \| None = None) -> list:` | modules/tower/families.py:88 | Phase 10 |
| `modules.tower.families.repo_family_report` | function | `def repo_family_report(path: str, families: list \| None = None) -> dict:` | modules/tower/families.py:136 | Phase 10 |
| `modules.tower.families.Family` | class | `class Family:` | modules/tower/families.py:46 | Phase 10 |
| `modules.tower.families.FAMILIES_DIR` | constant | `FAMILIES_DIR = os.path.join(_PP_ROOT, "vault", "tower", "families")` | modules/tower/families.py:33 | Phase 10 |
| `modules.tower.select.select_for_injection` | function | `def select_for_injection(entries: list, max_entries: int = MAX_ENTRIES, max_chars: int = MAX_CHARS) -> Selection:` | modules/tower/select.py:53 | Phase 10 |
| `modules.tower.select.Selection` | class | `class Selection:` | modules/tower/select.py:31 | Phase 10 |
| `modules.tower.select.MAX_ENTRIES` | constant | `MAX_ENTRIES = 8` | modules/tower/select.py:26 | Phase 10 |
| `modules.tower.select.MAX_CHARS` | constant | `MAX_CHARS = 1400` | modules/tower/select.py:27 | Phase 10 |
| `modules.tower.ratchet.verify_chain` | function | `def verify_chain(family: str, root: str \| None = None) -> ChainReport:` | modules/tower/ratchet.py:120 | Phase 10 |
| `modules.tower.ratchet.revert` | function | `def revert(family: str, entry_id: str, reason: str, authority: str, root: str \| None = None) -> str:` | modules/tower/ratchet.py:146 | Phase 10 |
| `modules.tower.ratchet.promote` | function | `def promote(family: str, new_entries: list, reason: str, authority: str, root: str \| None = None) -> str:` | modules/tower/ratchet.py:164 | Phase 10 |
| `modules.tower.ratchet.RatchetRefusal` | class | `class RatchetRefusal(ValueError):` | modules/tower/ratchet.py:46 | Phase 10 |
| `modules.tower.donegate.judge` | function | `def judge(family: str, repo_root: str, registry: str \| None = None, root: str \| None = None, not_applicable: dict \| None = None) -> dict:` | modules/tower/donegate.py:45 | Phase 10 |
| `tools.family_baseline.main` | function | `def main(argv: list) -> int:` | tools/family_baseline.py:143 | Phase 10 |
| `modules.gsd_x.goal.reconcile.decide` | function | `def decide(ctx: Context) -> Decision:` | modules/gsd_x/goal/reconcile.py:124 | Reality 1 |
| `modules.gsd_x.goal.sweep.sweep_goal` | function | `def sweep_goal(log: gl.GoalLog, root: Path, providers=("gate",), run_dir: Path \| None = None, dry_run: bool = False, actor: str = "sweep") -> list[str]:` | modules/gsd_x/goal/sweep.py:278 | Reality 2 |
| `modules.gsd_x.goal.judge.judge` | function | `def judge(state: GoalState, tree_hash: str, worktree: Path, scope_paths: list \| None = None, timeout_s: float = DEFAULT_GATE_TIMEOUT_S, env: dict \| None = ...` | modules/gsd_x/goal/judge.py:120 | Reality Scan (judge) |
| `modules.gsd_x.goal.git_state.tree_id` | function | `def tree_id(root: Path, paths: list[str] \| None = None) -> str:` | modules/gsd_x/goal/git_state.py:124 | Reality Scan (pins) |
| `modules.gsd_x.goal.git_state.blob_oid` | function | `def blob_oid(data: bytes) -> str:` | modules/gsd_x/goal/git_state.py:62 | Reality Scan (pins) |
| `modules.gsd_x.goal.git_state.file_pin` | function | `def file_pin(root: Path, files: list[str], scheme: str = SHA256) -> tuple:` | modules/gsd_x/goal/git_state.py:101 | Reality Scan (pins) |
| `modules.gsd_x.goal.log.GoalLog` | class | `class GoalLog:` | modules/gsd_x/goal/log.py:138 | Reality Scan (log) |
| `modules.gsd_x.cli.family_block` | function | `def family_block(prompt: str, payload: dict, families=None, root=None) -> str:` | modules/gsd_x/cli.py:99 | Reality Scan (family injection) |

## Findings

- **`decide` lives in `modules/cognitive_os/scheduler.py:94`**, not in `modules/parallel_mesh`. `pm_02_intent` only wraps it: its docstring says the collision decision "lives in the parent `scheduler.decide`" (pm_02_intent.py:7), and the wrapper at :220-233 calls `_sched.decide(hot, cwd, is_new=True, ...)` (:233). The spec's Reality 9 wording places `decide` beside `CollisionDetector`; the control premise confirms that it is absent there. Phase 3 imports it from `modules.cognitive_os.scheduler`.
- **`CollisionDetector.overlap` is exact-token intersection** (`return sorted(a & b)`, pm_02_intent.py:193-196; the docstring at :189 calls it the "same exact-token intersection rule scheduler.decide applies"). So `tools` and `tools/x.py` do not collide. Phase 3 needs its own prefix/containment rule.
- **`tools/family_baseline.py` has subcommands build-b0 / show / review / verify / revert** (:144-152) **and no promote.** Promotion happens in-process through `modules.tower.ratchet.promote` (ratchet.py:164). This is a Phase 10 note.
- **`modules/tower/donegate.py` is REPORT-ONLY** (docstring :1; `"report_only": True` at :50 and :77). It never blocks.
- **`tools/evidence_bundle.py` binds bytes at ISSUE time.** The A->B->A edit limit is recorded at :140-141 (DENOMINATOR R05). `run_check` captures output explicitly (`capture_output=True`, :68), so the R01 handle-loss fix does not affect it.
- **`tools/change_impact.py` scans only `*.py`** (`base.rglob("*.py")`, :47, inside the :42-49 sweep; DENOMINATOR D21/R06). A non-Python input is invisible to it.
- **`tools/mutation_drill.py`'s CLI is `--spec` only.** Its exit map is `{"KILLED": 0, "SURVIVED": 1, "UNJUDGED": 2, "CONTROL_INVALID": 4}.get(verdict, 3)` (:205).