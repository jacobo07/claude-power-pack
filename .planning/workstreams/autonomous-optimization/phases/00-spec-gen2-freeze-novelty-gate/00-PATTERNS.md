# Phase 0: Spec, gen2 freeze, novelty gate - Pattern Map

**Mapped:** 2026-10-05
**Files analyzed:** 15 new/modified (rows below)
**Analogs found:** 15 / 15 (13 exact or role-match with excerpts, 2 weak: `tools/test_ao_p0.py`, `evidence/*`)
**Tracked-source gate:** every analog path below was verified with `git ls-files` (tracked). No gitignored mirror paths are used.
**Run plane:** gex44, worktree `/home/kobii/missions/autonomous-optimization/.claude/worktrees/ao-gen2`. Type `python3`, never bare `python`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `vault/specs/autonomous-optimization.md` | spec (config/doc) | static doc, judged by readiness + binding | `vault/specs/agent-capability-virtualization.md` | exact (T3, `status: ready`) |
| `vault/audits/autonomous-optimization-novelty-2026-10-05.md` | audit record | doc, 13-row table | `vault/audits/ucr_cif/12_HR_NOVELTY_13Q_FAMILY_CLASSIFIER.md` | exact |
| `tools/ic_gen2.py` | utility / verifier | transform (ledger -> failure list), rebinding | `tools/cep_gen2.py` (shape) + `tools/test_incremental_cognition_program.py:79-97` (rebinding) | role-match (composite) |
| `tools/test_incremental_cognition_program.py` (modify: `--generation 2` dispatch) | test / CLI wrapper | request-response (argv -> exit code) | `tools/test_cognitive_economy_program.py:679-695` (`main` dispatch) | exact |
| `tools/test_ao_p0.py` | test (V-gates) | batch (spec/novelty/champion checks + mutants) | `tools/test_sdd_os_evolution.py` | role-match |
| `vault/programs/incremental-cognition/gen2/ledger.json` | config / ledger | static JSON, git-pinned | `vault/programs/incremental-cognition/ledger.json` | exact (shape) |
| `vault/programs/incremental-cognition/gen2/FROZEN_AT` | config | 1-line sha | `vault/programs/incremental-cognition/FROZEN_AT` | exact |
| `vault/programs/incremental-cognition/gen2/owner-bundle.md` | doc | table rows `[<P>]` | `vault/programs/incremental-cognition/owner-bundle.md` | exact |
| `vault/programs/incremental-cognition/gen2/evidence/champion/*` (+ `OPP-001-...md`) | evidence | file copy + sha256 pin | `vault/programs/incremental-cognition/measurements/D-KME-L-2026-10-05.md` (front-matter shape) | partial |
| `tools/gex44_env_preflight.py` (modify `check_pp_install`) | utility / probe | request-response (git probes in sandbox) | itself (`:255-320`) | exact |
| `tools/test_gex44_env_preflight.py` (modify `grp_pp`, `MUTANTS`) | test | batch + mutation drill | itself (`:259-290`, `:351-444`, `:809-843`) | exact |
| `.planning/workstreams/autonomous-optimization/REQUIREMENTS.md` (add `AOP-M..R` rows) | doc | traceability table (X2) | `.planning/workstreams/incremental-cognition/REQUIREMENTS.md:33-47` | exact |
| `.../phases/00-.../EVIDENCE.md` | doc | Product Delta + Intelligence Delta | `vault/programs/incremental-cognition/handoffs/I.md` (prose-with-source style); no EVIDENCE.md analog read | weak |
| `vault/programs/incremental-cognition/gen2/handoffs/*` | doc | handoff after FROZEN_AT | `vault/programs/incremental-cognition/handoffs/I.md` | exact (not needed in P0) |
| opportunity row OPP-001 (top-level `opportunities[]` in gen2 ledger) | config | static JSON row | none in repo (CO-12 rows are untracked); see "No Analog Found" | none |

---

## Pattern Assignments

### `tools/ic_gen2.py` (verifier, ledger -> failure list)

**Analog A (module shape, selftest, `main(mode)`):** `tools/cep_gen2.py`
**Analog B (rebinding of CE globals):** `tools/test_incremental_cognition_program.py:79-97`

**Header / imports / REPO / lazy-import contract** (`tools/cep_gen2.py:11-21`):
```python
from __future__ import annotations

import copy
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER_REL = "vault/programs/cognitive-economy/gen2/ledger.json"
```
Copy this shape; set `LEDGER_REL = "vault/programs/incremental-cognition/gen2/ledger.json"`. Add the CE import the way the IC wrapper does (`:79-80`): `sys.path.insert(0, str(Path(__file__).resolve().parent)); import test_cognitive_economy_program as ce`.

**Rebinding pattern to wrap in a context manager** (`tools/test_incremental_cognition_program.py:82-97`):
```python
PROGRAM = "incremental-cognition"
PROGRAM_DIR = f"vault/programs/{PROGRAM}/"
ce.SELF_REL = "tools/test_incremental_cognition_program.py"
ce.LEDGER_REL = PROGRAM_DIR + "ledger.json"
ce.FROZEN_AT_REL = PROGRAM_DIR + "FROZEN_AT"
ce.HANDOFF_DIR = PROGRAM_DIR + "handoffs/"
ce.PILLARS = [chr(c) for c in range(ord("A"), ord("N") + 1)]
CE_REQS = (ce.REQS_REL, ce.REQ_ROW)
ce.REQS_REL =".planning/workstreams/incremental-cognition/REQUIREMENTS.md"
ce.REQ_ROW = re.compile(r"^\|\s*IC-([A-N])\s*\|[^|\n]*\|([^|\n]*)\|\s*$", re.M)
```
gen2 differences (RESEARCH Pattern 1 / Code Examples): do NOT mutate at import time (gen1 B1 would see the leak). Use `@contextlib.contextmanager bound()` with `try/finally` restore of `(PILLARS, LEDGER_REL, FROZEN_AT_REL, HANDOFF_DIR, REQS_REL, REQ_ROW)`, `ce.PILLARS = ["M","O","P","Q","R"]`, `REQS_REL=".planning/workstreams/autonomous-optimization/REQUIREMENTS.md"`, `REQ_ROW = re.compile(r"^\|\s*AOP-([MOPQR])\s*\|[^|\n]*\|([^|\n]*)\|\s*$", re.M)`. Note the AO REQUIREMENTS table already has 3 columns; `AO-nn` rows do not match `AOP-`.

**Core call to reuse** (CE `check_ledger`, `tools/test_cognitive_economy_program.py:182-207`): signature `check_ledger(led, res, final, only=None, run_gates=True) -> list[str]`; clause strings start with `L1`..`L9`. L1 returns early with `"L1 frozen pillars must be exactly A-T in order, got {ids}"` if `ids != PILLARS` (the message text says A-T even under rebinding; assert on the `L1` prefix only). L2 body:
```python
    ref = res.frozen_at_commit()
    if ref is None:
        if final:
            f.append("L2 not frozen: FROZEN_AT missing, the pre-registration was never committed")
    elif json.dumps(ref, sort_keys=True) != json.dumps(fr, sort_keys=True):
        f.append("L2 frozen pre-registration differs from its copy at FROZEN_AT")
```
Status mode in CE `main` is `check_ledger(led, res, final=False, run_gates=False) + check_disposition(led, res)` (`:708`); `res = ce.Resolver()`.

**Selftest/mutant loop to copy** (`tools/cep_gen2.py:139-172`; clean control first, then each mutant on a deepcopy must be killed):
```python
def selftest(verbose=True) -> bool:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = _fixture(root)
        clean = check(base, root)
        ok &= not clean
        if verbose:
            print(f"  {'ok' if not clean else 'FAIL'}   V-CEP2-CLEAN (positive control green) {clean or ''}")
        for name, mutate in MUTANTS.items():
            d = copy.deepcopy(base)
            mutate(d)
            killed = bool(check(d, root))
            ok &= killed
            if verbose:
                print(f"  {'ok' if killed else 'FAIL'}   V-CEP2-MUT-{name} {'killed' if killed else 'SURVIVED'}")
    return ok
```
Rename labels `V-IC2-CLEAN` / `V-IC2-MUT-<rule>`. For clause-label mutants (L1, L2, L6) use CE's assertion style (`tools/test_cognitive_economy_program.py:594-597`): `say(any(x.startswith(clause) for x in got), f"V-CEP-MUT-{name} killed by {clause}")` with a fixture Resolver (`FakeResolver(frozen)` at ~`:595`) so L2 can be driven without git. CE's own `selftest` must NOT run under the gen2 binding (hardcoded A-T fixtures, RESEARCH Pattern 1).

**main(mode) + exit codes** (`tools/cep_gen2.py:175-200`): `selftest` -> prints `CEP2_SELFTEST=PASS|FAIL`; ledger unreadable -> `...VERDICT=COULD_NOT_RUN` exit 2; `status` prints JSON `{"open": [...], "violations": [...]}` and returns 1 if violations; final inserts `"S0 selftest failed: the verifier cannot be trusted"` when selftest is red. Use labels `IC2_SELFTEST`, `IC2_VERDICT` (wrapper prints `ICP_GEN2_VERDICT`). `ledger unreadable` / unknown -> exit 2, never 0 (UNKNOWN is never PASS).

**Binding self-check (G2-B1)** copy from `check_binding` (`tools/test_incremental_cognition_program.py:201-211`):
```python
def check_binding(led: dict) -> list:
    f = []
    now = {"SELF_REL": ce.SELF_REL, "LEDGER_REL": ce.LEDGER_REL, ...}
    for k, v in BINDING.items():
        if now[k] != v:
            f.append(f"B1 CE global {k} rebound away from this program: {now[k]!r}")
    if led.get("program") != PROGRAM:
        f.append(f"B1 ledger program is {led.get('program')!r}, not {PROGRAM!r}")
    return f
```
Gen2 additions: V-IC2-BINDING-RESTORED asserts that after a gen2 run the CE globals equal the gen1 values (so gen1 `check_binding` still passes).

**Evidence sha helper to reuse (G2-CHAMP):** `ce.lf_sha256(path)` (`tools/test_cognitive_economy_program.py:90-91`) = `hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()` (LF-normalised).

**Error-handling convention:** no try/except swallowing; all failures are strings in a list; `main` converts unreadable input to exit 2.

---

### `tools/test_incremental_cognition_program.py` (modify: `--generation 2` dispatch only)

**Analog:** `tools/test_cognitive_economy_program.py:679-695`
```python
    ap.add_argument("--generation", type=int, choices=(1, 2), default=1,
                    help="2 = TOK-18 v2 ledger (tools/cep_gen2.py); generation 1 is unchanged")
    a = ap.parse_args(argv)

    if a.generation == 2:
        if a.pillar:
            ap.error("--pillar applies to generation 1 only")
        sys.path.insert(0, str(REPO / "tools"))
        import cep_gen2
        return cep_gen2.main("selftest" if a.selftest else "status" if a.status else "final")
```
**Adaptation point:** IC `main` (`tools/test_incremental_cognition_program.py:1283-1337`) hand-parses argv (`"--selftest" in argv`, `"--final" in argv`, `--pillar`) and delegates the rest to `ce.main(argv)`, whose argparse would reject IC-only combos. Parse `--generation` (both `--generation 2` and `--generation=2`) at the top of IC `main`, before the `--selftest` branch at `:1285`, and return `ic_gen2.main(...)`. Existing branch shape to extend (`:1285-1290`):
```python
    if "--selftest" in argv:
        own = selftest()
        rc = ce.main(["--selftest"])
        good = own and rc == 0
        print(f"ICP_SELFTEST={'PASS' if good else 'FAIL'}")
        return 0 if good else 1
```
Add gen2 selftest to this branch (`good = own and rc == 0 and ic_gen2.selftest(verbose=False)`), and in the `--final` branch (`:1291-1312`) print a distinct `ICP_GEN2_VERDICT=` line so gen2 failures do not hide in gen1's `failures=` count. Lazy import `ic_gen2` inside the branch (same as `import cep_gen2`). Do NOT touch `tools/test_cognitive_economy_program.py` or any `frozen` object.

---

### `vault/programs/incremental-cognition/gen2/ledger.json` (ledger, git-pinned)

**Analog:** `vault/programs/incremental-cognition/ledger.json` (shape verified by parse this session)
Top-level keys: `['schema','program','plan','terminal_vocabulary','frozen','state','reviews','deltas']`. `frozen` keys: `['frozen_note','materiality','denominators','consumes','pillars']`. Pillar object (gen1 M, verbatim, the one being reopened):
```json
{
 "id": "M",
 "name": "optimizer, experiment compilation, negative capital, routing, events, reality model",
 "owner": ["vault/programs/cognitive-economy/ledger.json", "tools/baseline_ledger.py"],
 "predicted": "MERGED_INTO_EXISTING_OWNER",
 "rule": "dispositions only: CE Q/N/O/M and the pre-registration pattern of this verifier already own them; an unrestricted optimizer is rejected"
}
```
Open state / closed state / reviews / deltas (gen1): `state: {"<id>": {}}` until closed; closed = `{"terminal","reason","evidence":[{"kind":"measurement","ref":"<path>","sha256":"<64hex>"}],"savings":[]}`; `reviews = {"ukdl": null, "cbr": null}`; `deltas = {"product": [], "intelligence": []}`. `frozen.denominators["KME-L"]` carries `file`, `source`, `calls: 34871`, `cache_read: 11549646300`, `cache_write`, `output`, ... (gen1 `denominators/kme_audit_2026-10-03.json`).
**gen2 differences (RESEARCH Pattern 3):** `program` stays `"incremental-cognition"` (B1), add `"generation": 2`, `plan: vault/plans/autonomous-optimization-2026-10-05.md`, `frozen.champion` (run5/run6: command, wall_s, read_GB, plane, sha256 of copied evidence), `frozen.reopens.M.gen1_predicted`, top-level `opportunities` (OUTSIDE `frozen`). Every `owner` path must exist today (CE L1 `res.path_exists`). `state` must hold exactly `M,O,P,Q,R`. There is NO pillar-shaped gen2 ledger in the repo: `vault/programs/cognitive-economy/gen2/ledger.json` has `work_units` and no `frozen`; do not copy it.

---

### `vault/programs/incremental-cognition/gen2/FROZEN_AT`

**Analog:** `vault/programs/incremental-cognition/FROZEN_AT` = one line, a 40-hex commit sha with trailing newline (`18e928af8c489f9d29dd1e76e0c7aa3c6a6975eb`). It names the pre-registration commit, not a content hash. Reader (`tools/test_cognitive_economy_program.py:170-179`):
```python
        sha = fa.read_text(encoding="utf-8").strip()
        r = _git("show", f"{sha}:{LEDGER_REL}")
        ...
        return json.loads(r.stdout)["frozen"]
```
Two-commit protocol, precedent `18e928af feat(incremental-cognition): P0 freeze ...` then `d4d35059 chore(incremental-cognition): FROZEN_AT = 18e928af (pre-registration commit)` (second touches only `FROZEN_AT`). Subject convention for gen2: `feat(autonomous-optimization): P0 gen2 freeze ...` then `chore(autonomous-optimization): FROZEN_AT = <sha8> (pre-registration commit)`. Pathspec-scoped commits; verify `git log -1 --format=%s`.

---

### `vault/programs/incremental-cognition/gen2/owner-bundle.md`

**Analog:** `vault/programs/incremental-cognition/owner-bundle.md:1-30` (521 lines; copy header + table shape only)
```markdown
# Incremental Cognition -- Owner bundle

One line per pillar that needs an Owner action. The mission never asks mid-run (ROADMAP operating
constraints); it records the action here and continues with other phases. ...

Run plane: GEX44 clone `~/missions/incremental-cognition`, branch `mission/incremental-cognition-run`
(never pushed; fetch it back).

| # | pillar | source | action | exact command | what closes when it lands |
|---|---|---|---|---|---|
| 2 | C | [C]#1 "laptop deploy of" ; UAT 02#1 | On the laptop ..., cherry-pick the seven pillar-C commits ... | `git cherry-pick 5962571c840943ae0a3aa901efb08e69a04434da ...` | pillar C IMPLEMENTED_AND_VERIFIED: gate ... |
```
gen2 rows: tag `[<P>]` and name the programme (RESEARCH Anti-Pattern: letters M,O,P,Q,R collide with CE letters). Phase 0 row: `[P0]` ask for `PP_FLOOR_PATCH_ID` computed where the floor object exists (RESEARCH Open Question 2). R4 caveat (not needed in P0): `check_owner_decisions` only recognises the gen1 bundle path (`OWNER_BUNDLE_REL`, `tools/test_incremental_cognition_program.py:277`).

---

### `vault/programs/incremental-cognition/gen2/evidence/champion/*` (+ `OPP-001-pp-install-hash-floor.md`)

**Analog:** `vault/programs/incremental-cognition/measurements/D-KME-L-2026-10-05.md` (front matter; kme_pillars output, not a hand file). Copy the *front-matter field names* when a copied summary is used as `measurement` evidence (CE `_check_evidence` demands `command:` text in the file and a frozen denominator name):
```yaml
---
instrument: "wiki/tools/kme_pillars.py"
denominator: "KME-L"
denominator_kind: "frozen"
plane: "gex44"
measured_at: "2026-10-05T18:10:45Z"
command: "python3 wiki/tools/kme_pillars.py d --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2'"
population_match: "exact"
---
```
Sha pin convention: evidence entries are `{kind, ref, sha256}`; compute with `ce.lf_sha256`. Raw champion files live outside git at `/home/kobii/missions/zero-rescan-out{,2}/summary.txt`, `r4-population.log`, `/home/kobii/missions/gex44_ic_rows.sh`: copy in, hash, tag the Run 5 command as reconstructed (RESEARCH A2). Run a secret grep before committing the copies (HR-SECRET-004/005).

---

### `tools/gex44_env_preflight.py` (modify `check_pp_install`)

**Analog:** itself. Insertion point: the `anc = _is_ancestor(...)` branch and the `rc == 1` (floor object absent) branch.

**Current code to extend** (`tools/gex44_env_preflight.py:255-259`, `288-300`):
```python
def _is_ancestor(sbx: _Sandbox, git: str, install: str, floor: str):
    rc, _, _ = sbx.run([git, "merge-base", "--is-ancestor", floor, "HEAD"], cwd=install)
    return True if rc == 0 else False if rc == 1 else None
...
        rc, _, _ = sbx.run([git, "rev-parse", "--verify", "--quiet", f"{floor}^{{commit}}"], cwd=install)
        if rc not in (0, 1):
            return _result("pp_install", UNMEASURABLE, "git could not look up the floor commit", detail=detail)
        problems = []
        if rc == 1:
            problems.append(f"floor {floor[:8]} is not in this install's history (head {detail['head'][:8]})")
        else:
            anc = _is_ancestor(sbx, git, install, floor)
            if anc is None:
                return _result("pp_install", UNMEASURABLE, "git could not compare HEAD with the floor", detail=detail)
            if not anc:
                problems.append(f"head {detail['head'][:8]} does not contain the floor {floor[:8]}")
```
**Probe plumbing to reuse** (`:185-208`): all git via `_Sandbox.run(argv_list, cwd=...)` (throwaway HOME, `GIT_OPTIONAL_LOCKS=0`, no shell, `PROBE_TIMEOUT_S`, run budget; `TimeoutError` -> UNMEASURABLE at `:317-318`). `_Sandbox.run` has no stdin parameter; patch-id path needs a minimal stdin extension (or `subprocess.run` with `sbx.env`).
**New helper pattern (trailer, exact 40-hex, `-F`)** from RESEARCH Code Examples:
```python
rc, out, _ = sbx.run([git, "log", "-F", "--grep", f"(cherry picked from commit {floor})",
                      "--format=%H", "--max-count=1", "HEAD"], cwd=install)
via_trailer = rc == 0 and bool(out.strip())   # rc != 0 -> could not ask -> UNMEASURABLE, never READY
```
Restructure so a refusal only becomes a `problem` when all three paths (ancestry, trailer, patch-id when floor object present) fail. Preserve: `PP_REQUIRED_FILES` check (`:301-303`) on every path; `rc == 1` floor-absent must still reach the trailer path (real GEX44 case); final stale message must contain `does not contain the floor` (asserted by `V-ENVPF-PP-STALE-REAL`, test `:441`); record `detail["floor_via"]`; add non-refusing finding `floor_by_pick` (add to `FINDINGS` at `:50`; the aggregator needs no table change). `UNMEASURABLE` on "git could not ask" stays. Result helper usage: `_result("pp_install", READY|NOT_READY|UNMEASURABLE, why, reasons=[...], findings=[...], detail=...)`.

---

### `tools/test_gex44_env_preflight.py` (modify `grp_pp`, `MUTANTS`; red tests first)

**Analog:** itself.

**Gate registration helpers** (`:44-63`): `check(name, cond, ev)` records to `RESULTS`; `guarded(name, fn)` runs a body returning `(ok, evidence)` and turns exceptions into a FAIL. Summary line: `print(f"ENVPF_PASS={passed}/{total}  threshold={total}/{total}")` (`:750`).

**Hermetic git fixture helpers to reuse** (`:259-290`):
```python
def git(cwd: Path, *args: str, check=True) -> str:
    env = {**os.environ, "HOME": str(TMP_ROOT), "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
           "GIT_AUTHOR_NAME": "t", ...}
def make_install(tmp: Path) -> dict:
    """A PP install that is a git checkout: base -> floor -> tip, required files present from the base."""
    ...
    return {"inst": inst, "base": base, "floor": floor, "tip": git(inst, "rev-parse", "HEAD")}
```

**Case pattern to copy for the six new gates** (`:352-374`):
```python
    def case(name, build, expect_state, expect_reason=None, expect_finding=None, floor_of=None):
        def body():
            tmp = make_env(scratch(), expires_at_ms=FUTURE_MS)
            ctx = build(tmp)
            env = ep.env_from_root(tmp)
            floor = floor_of(ctx) if floor_of else ctx["floor"]
            r = ep.check_pp_install(env, floor=floor)
            ok = r["state"] == expect_state
            ...
            return ok, f"state={r['state']} reasons={r['reasons']} findings={r['findings']} why={r['why']}"
        guarded(name, body)

    def sibling(tmp):
        c = make_install(tmp)
        git(c["inst"], "checkout", "-q", "--detach", c["base"])
        (c["inst"] / "side.txt").write_text("side\n", encoding="utf-8")
        git(c["inst"], "add", "-A")
        git(c["inst"], "commit", "-q", "-m", "side")
        return c
    case("V-ENVPF-PP-STALE-SIBLING", sibling, ep.NOT_READY, "pp_install_stale")
```
New gates (RESEARCH table): `V-ENVPF-PP-PICK-TRAILER-READY`, `-PICK-FLOOR-ABSENT-READY` (clone with `git clone --no-local --single-branch --branch main` so the floor object is truly absent), `-PICK-PATCHID-READY`, `-UNRELATED-STALE` (why contains `does not contain the floor`), `-TRAILER-SPOOF-STALE` (different 40-hex sha and 8-hex abbreviation), `-PICK-REQUIRED-FILE`. The pick-fixture pitfall: give the pick branch an unrelated commit first so the pick is a different commit (a no-`-x` pick onto HEAD's parent reproduces the same hash and is an ancestor). Add the pick-only fixtures to the `case(...)` use (the `floor_of` kwarg lets a case pass a non-ctx floor).

**Mutant pattern + drill** (`:767-817`, `:820-843`):
```python
def _patch(obj, attr, value):
    saved = getattr(obj, attr)
    setattr(obj, attr, value)
    return lambda: setattr(obj, attr, saved)

def _m_ancestor_always_true():
    return _patch(ep, "_is_ancestor", lambda sbx, git, install, floor: True)

MUTANTS = [
    ...
    ("M3 ancestor test always passes", _m_ancestor_always_true, [grp_pp], ["V-ENVPF-PP-STALE-REAL"]),
```
Add M7 (trailer path always False), M8 (patch-id path always False), M9 (trailer always True), each with a new helper function name patched via `_patch(ep, "<new_helper>", ...)` -- so the new probe logic must live in named module-level helpers (like `_is_ancestor`) to be patchable. Retarget M3 to the hermetic `V-ENVPF-PP-STALE-NOT-ANCESTOR` (current target `V-ENVPF-PP-STALE-REAL` never reaches `_is_ancestor` on this plane: false kill). Drill control rule (`:823-825`): `control_ok = bool(control) and all(control.values())`; kills are only trusted when control is 100 % green. Note: baseline `ENVPF_PASS=55/57` is red on this plane BEFORE the fix (REAL-READY and STALE-REAL); the red-first record must show the six new gates failing / the control state, then green after the fix.

---

### `tools/test_ao_p0.py` (spec / novelty / champion V-gates)

**Analog:** `tools/test_sdd_os_evolution.py` (role-match; same gate helper, `_PASS=n/m` summary, isolated state dir, mutants)

**Imports + gate helper** (`tools/test_sdd_os_evolution.py:25-56`):
```python
from __future__ import annotations
import json, os, shutil, sys, tempfile
from pathlib import Path
...
from modules.sdd_os.spec_binding import find_bound_spec  # noqa: E402
from modules.spec_gate.gate import classify_tier  # noqa: E402

results: list[tuple[str, bool, str]] = []

def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, bool(cond), evidence))
    print(f"{'PASS' if cond else 'FAIL'} {name}  {evidence}")
```
(Check the file's lines 33-47 for the `sys.path` / repo-root insertion before the `modules.` imports.)

**Temp-repo spec fixture for mutants** (`:70-75`, `:100-113`): `_make_repo(base, names, specs)` writes `vault/specs/<name>.md` under a `tempfile.mkdtemp`, then `find_bound_spec(case["task"], repo)` and compare `.strength` / `.spec_path.stem`. Use it for the covers-tie mutant (spec whose `covers` duplicates the plan's -> expect `AMBIGUOUS`) and the `status: draft` -> NOT_READY mutant via `modules.sdd_os.readiness.assess(path, 3)` (`Readiness.state`, `.authorizes` property, `modules/sdd_os/readiness.py:90-101`; `assess` at `:247`).
**Summary/exit** (`:361-374`): `print(f"SDDEVO_PASS={passes}/{len(results)}")`; `return 0 if passes == len(results) else 1`. Use `AOP0_PASS=n/n`. Gate ids: `V-AOP0-SPEC-READY`, `V-AOP0-SPEC-BINDS`, `V-AOP0-SPEC-SECTIONS`, `V-AOP0-NOVELTY-13`, `V-AOP0-NOVELTY-CITES-RESOLVE`, `V-AOP0-NOVELTY-GATE-CONTROL` (RESEARCH Validation table).
**Novelty gate positive control:** `from modules.spec_gate.gate import check_novelty_gate, NOVELTY_PROOF_QUESTIONS` (13 strings, `modules/spec_gate/gate.py:330-344`); `check_novelty_gate("new autonomous optimization operating system").applies is True` while the plan text returns `applies=False` (MEASURED in RESEARCH). The gate is advisory and returns `NoveltyGateResult(applies, matched, questions, message)`; there is no classification output, so the verdict lives only in the audit prose.
**Isolation rule:** this analog pins the live ledger line count before/after (`V-SDDEVO-STATE-ISOLATED`, `_finish`, `:361-370`) so a test cannot pollute real state; copy the idea (tests must not write real `~/.claude`, RESEARCH V4).
Optionally fold into `ic_gen2` selftest (RESEARCH says one file is simpler); if kept separate, copy this structure.

---

### `vault/specs/autonomous-optimization.md` (T3 spec)

**Analog:** `vault/specs/agent-capability-virtualization.md:1-39` (working T3 in readiness grammar)
```yaml
---
covers: [agent-virtualization, agent-spec, ...]
date: 2026-09-30
updated: 2026-10-03
tier: T3
status: ready
scope: [modules/capability_runtime/, ..., tools/test_agent_patch_apply.py]
open_questions:
  - Q1 | RESOLVED | symbol names are fixed inside the shared applicability._hits (D1), not resolver-local
  - Q4 | ASSUMED | S5f runs after the weekly reset or an explicit Owner go; S5a-S5e do not wait (D8)
acceptance:
  - AC-1 symbol names route and ordinary phrases keep identical hits | verify: python tools/test_capability_runtime.py
must_still_pass:
  - python tools/test_agent_spec.py
checkpoints:
  - CP-1 | C1 identity property test passes over phrases discovered from contracts, ...
---
```
Rules (RESEARCH Pattern 4): `status: ready` exactly; `scope:` non-blank list; `open_questions` items `Q<n> | RESOLVED|ASSUMED|NONE | <answer>` (no `OWNER_DECISION`/`RESEARCH`/`BLOCKING`); `acceptance` items `AC-n <text> | verify: <command or V-XXX id>`; `must_still_pass` runnable commands or `none: <reason>`; `checkpoints` `CP-n | <falsifiable>` required at tier 3; no nested YAML. Use `python3` in `verify:` commands. Required body sections: `## 1. Problem` .. `## 8. Architecture spec` (`8.5 Rollback plan`), `## Kill switches (Tier 3)`, `## 11. Completion gate` (skeleton from `modules/sdd_os/pre_exec_gate.py` `_full_spec_body`; map PRD=1-6, arch=8, acceptance=7, rollback=8.5, kill switches=Tier 3 section). Prose style of the body: baseline-measurements-first headings with dated, measured facts (`## Measured baseline (...)`, `## S0 results (...)`).
**HAZARD (covers tie):** the approved plan `vault/plans/autonomous-optimization-2026-10-05.md` already declares `covers: [autonomous-optimization, zero-rescan, opportunity-lifecycle, kme-l-challenger, usage-index-v5, optimization-ratchet]` and both `vault/specs/` and `vault/plans/` are in `SPEC_GLOBS`. The new spec's `covers:` must be disjoint multi-token entries (e.g. `gen2-freeze`, `optimization-opportunity-row`, ...), verified with `find_bound_spec` on the real phase task text before commit; task text must name `vault/specs/autonomous-optimization.md` literally (REFERENCED outranks STRONG). Do not edit the plan's front matter.

---

### `vault/audits/autonomous-optimization-novelty-2026-10-05.md` (HR-NOVELTY-001 record)

**Analog:** `vault/audits/ucr_cif/12_HR_NOVELTY_13Q_FAMILY_CLASSIFIER.md:1-62` (verified tracked)
```markdown
---
title: UCR-CIF — HR-NOVELTY-001 corrido entero contra el sujeto real: ...
date: 2026-09-23
status: MEASURED — 13/13 respondidas contra barrido descubierto, no contra lista curada
subject: ...
verdict: NEW_SCANNER_OR_GATE + EXTEND_EXISTING_OWNER — NO es un sistema institucional nuevo
closes: ...
---
# HR-NOVELTY-001 — 13/13, contra un sujeto concreto
## 0. Por qué contra ESTE sujeto y no en abstracto
## 1. (what the trigger did / correction to the keyword gate)
## 2. Las trece, contra <sujeto>
| # | pregunta | respuesta medida |
|---|---|---|
| **1** | ¿Qué problema concreto no tiene dueño hoy? | Clasificar ... Sonda por nombre sobre `modules/`+`tools/`: `system_family` · ... → **0 ficheros**. ... **Sin dueño.** |
...
## 3. Veredicto
> **`NEW_SCANNER_OR_GATE` + `EXTEND_EXISTING_OWNER`. NO es un sistema institucional nuevo.**
```
Adapt: `verdict: EXTEND_EXISTING_OWNER` (ROADMAP criterion 3; else the slice stops). The 13 questions' exact text is `NOVELTY_PROOF_QUESTIONS` (`modules/spec_gate/gate.py:330-344`); keep the same order. Section 1 must record the gate's actual output: `applies=False` for plan/ROADMAP text and the positive controls firing (`"... operating system"` -> `'operating system'`, `"... governance layer"`), because silence is a vocabulary limit, not evidence (`gate.py:355-364`; the analog's §1 makes the same point about `_NOVELTY_SHAPE`). Upgrade over the analog: cite each answer as `path:LINE "verbatim fragment"` so `V-AOP0-NOVELTY-CITES-RESOLVE` can mechanically resolve it (file exists, line <= length, fragment on that line). Discovered-sweep anchors to re-grep (do not copy): `tools/usage_index.py:65` `SCHEMA_VERSION = 4`, `modules/tower/ratchet.py:120,146,164`, `modules/cognitive_os/co_12_telemetry.py` `record_signal`, `tools/skill_opportunity_signals.py:34-36`; Q1 honest answer: `opportunity lifecycle` / `technical capital` exist only in plans (no executable owner).

---

### `.planning/workstreams/autonomous-optimization/REQUIREMENTS.md` (add `AOP-M..R` rows)

**Analog:** `.planning/workstreams/incremental-cognition/REQUIREMENTS.md` traceability table
```markdown
| Req | Pillar | Status |
|---|---|---|
| IC-D | Silent-success hooks | Complete -- FALSIFIED_OR_REJECTED_BY_EVIDENCE |
| IC-M | Optimizer, experiments, routing, events, reality model | Pending |
```
CE X2 reads rows through `ce.REQ_ROW`; the bound IC regex is `^\|\s*IC-([A-N])\s*\|[^|\n]*\|([^|\n]*)\|\s*$` (3-column rows: id | pillar | status; the status cell must name the ledger terminal once closed). Current AO file has only `| id | requirement | phase |` rows `AO-01..AO-17` (`REQUIREMENTS.md:5-23`), which an `AOP-` regex will not match. Add a separate "Traceability" table with `| AOP-M | <name> | Pending |` rows so the bound `ce.REQ_ROW` for gen2 matches only these.

---

### `EVIDENCE.md` (phase) and `gen2/handoffs/*`

No dedicated analog of EVIDENCE.md was read (CONTEXT requires Product Delta + Intelligence Delta sections). For handoff style copy `vault/programs/incremental-cognition/handoffs/I.md:1-17`: `# Handoff [I] -- <title>`, names the pillar, the owner path(s) from `frozen`, quotes the frozen rule, cites the measurement file with its fields, then `## Finding`. CE `handoff_landed` needs the handoff commit to land AFTER `FROZEN_AT`, live under `ce.HANDOFF_DIR` (`gen2/handoffs/`), name `[<pillar>]` and one frozen owner path. Not needed in Phase 0.

---

## Shared Patterns

### Hermetic V-gate harness (all new tests)
**Source:** `tools/test_gex44_env_preflight.py:44-63` (`check`/`guarded`) and `tools/test_sdd_os_evolution.py:50-56` (`gate`)
**Apply to:** `tools/test_ao_p0.py`, preflight tests, `ic_gen2` selftest
Rules: gate id `V-<DOMAIN>-<NAME>`, summary `*_PASS=n/n`, exit 0 only when all pass; exceptions inside a gate are FAIL, never a crash; a clean positive control runs before mutants; a skipped gate is printed `SKIP`, never counted as pass (`skip()` at `:51-54`); scratch dirs only, never the real `~/.claude` (HR-001, RESEARCH V4).

### Pre-registration immutability (CE L2)
**Source:** `tools/test_cognitive_economy_program.py:170-207` + `vault/programs/incremental-cognition/FROZEN_AT`
**Apply to:** `gen2/ledger.json`, `gen2/FROZEN_AT`, `ic_gen2.py`
Only `frozen` is pinned; `state`, `reviews`, `deltas`, `opportunities` may change post-freeze. Two commits; audit `frozen` before commit A (unrepairable after).

### Evidence pins
**Source:** `ce.lf_sha256` (`tools/test_cognitive_economy_program.py:90-91`); evidence entry `{"kind","ref","sha256"}` in IC ledger `state.D.evidence`
**Apply to:** champion copies, OPP-001 evidence, any new ledger evidence

### Argv-list, no-shell, sandboxed git
**Source:** `tools/gex44_env_preflight.py:185-208` (`_Sandbox.run`), `tools/test_gex44_env_preflight.py:259-266` (`git()` fixture)
**Apply to:** preflight fix, preflight fixtures, any git use in `ic_gen2.py` (CE side uses `ce._git(...)` at `:94`)

### UNKNOWN / UNMEASURABLE is never PASS
**Source:** `tools/gex44_env_preflight.py:262-320` (UNMEASURABLE on any "could not ask"), `tools/cep_gen2.py:180-184` (`COULD_NOT_RUN`, exit 2)
**Apply to:** every new check (git cannot ask -> UNMEASURABLE; unreadable ledger -> exit 2; a count of zero from an absent input is not green)

### Gen1 immutability / scope guard
**Source:** CONTEXT.md locked decisions; `tools/test_incremental_cognition_program.py:79-97` (wrapper rebinds, never edits CE)
**Apply to:** all plans. Never edit: gen1 / CE / SC ledgers' `frozen`, `tools/test_cognitive_economy_program.py`, `tools/test_skill_capability_program.py`, root `.planning/STATE.md`, `tools/gsd_mission.py`.

### Commit discipline
Explicit pathspec per commit, one falsifiable increment, verify `git log -1 --format=%s`, message via tempfile + `git commit -F` (HR-003), end with the Co-Authored-By line given in the session attribution reminder.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| OPP-001 row in `gen2/ledger.json` `opportunities[]` | config | static JSON | No durable, git-tracked opportunity-row format exists. CO-12 `record_signal` rows (`modules/cognitive_os/co_12_telemetry.py`; producer `tools/skill_opportunity_signals.py:34-36`, kind `capability_opportunity`) are host-local JSONL under `~/.claude/state/co12_readiness/`, untracked and skill-specific. Use RESEARCH "Opportunity row" design (P4 field names, `provisional until P4`, `realized_dividend: null`). Validator rule G2-OPP lives in `ic_gen2.py` (no analog; follow the `cep_gen2.check` list-of-strings style). |
| `tools/ic_gen2.py` G2-GEN1 / G2-CHAMP / G2-REOPEN / G2-OPP rules | utility | transform | No existing rule that compares one ledger against another generation's `frozen` or against sha-pinned copied summaries; build in `cep_gen2.check` style with a mutant each. |
| gen2 `--generation 2` flag on the IC wrapper | CLI | request-response | Only CE has it (`tools/test_cognitive_economy_program.py:686-695`); SC wrapper's gen2 dir (`vault/programs/skill-capability/gen2/`) is prose only, so "skill-capability/gen2 precedent" in CONTEXT is NOT a ledger/verifier precedent (RESEARCH Deprecated note). |
| Patch-id acceptance on GEX44 | probe | request-response | Floor object `5962571c` is absent here; only the trailer path can operate on this host. Patch-id path is testable only with hermetic fixtures. |

## Metadata

**Analog search scope:** `tools/`, `vault/specs/`, `vault/audits/`, `vault/programs/{incremental-cognition,cognitive-economy}/`, `.planning/workstreams/{incremental-cognition,autonomous-optimization}/`, `modules/{spec_gate,sdd_os}/`
**Files read for excerpts:** ~19 (including the two phase documents); all analog paths verified `git ls-files` tracked.
**Pattern extraction date:** 2026-10-05
