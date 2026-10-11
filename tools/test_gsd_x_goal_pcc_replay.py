"""Legacy replay suite for the proof-conserving convergence seam (GSD X, Phase 2, plan 02-02).

Replays the recorded legacy goal logs (a committed, hash-verified byte copy) and a set of
synthetic scenarios through every legacy projection and compares the result with a golden
captured from the UNMODIFIED engine. The seam (modules/gsd_x/goal/proof.py) must change
no legacy output, and every legacy reader must ignore the new event types.

Modes:
  (default)                  run every gate
  --capture-fixture --store <dir> --repo <id> --goal <id>
                             copy a live goal log into tools/fixtures after verify + scan
  --capture                  write tools/fixtures/gsdx_legacy_replay_golden.json (once)
  --amend <scenario> --why <text>
                             recapture one scenario, recording why

Hermetic: HOME, USERPROFILE and GSDX_GOALS_ROOT are redirected before any engine import;
the live store is only ever read, and only by --capture-fixture.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import dataclasses
import hashlib
import inspect
import io
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

REAL_HOME = Path.home()
_TMP_HOME = Path(tempfile.mkdtemp(prefix="pcc-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="pcc-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)

import gsdx_reality_baseline as grb                      # noqa: E402
from modules.gsd_x.goal import git_state                 # noqa: E402
from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import convergence as cv         # noqa: E402
from modules.gsd_x.goal import engine_identity as eid    # noqa: E402
from modules.gsd_x.goal import epoch as ep               # noqa: E402
from modules.gsd_x.goal import evidence as evd           # noqa: E402
from modules.gsd_x.goal import intervention as iv        # noqa: E402
from modules.gsd_x.goal import judge as jd               # noqa: E402
from modules.gsd_x.goal import log as gl                 # noqa: E402
from modules.gsd_x.goal import reconcile as rc           # noqa: E402
from modules.gsd_x.goal import sweep as sw               # noqa: E402
from modules.gsd_x.goal.log import EVENT_RE, GoalLog, GoalLogError  # noqa: E402
from modules.gsd_x.mission import closure as mcl        # noqa: E402
from modules.secret_firewall import detector             # noqa: E402

FIXTURE_ROOT = ROOT / "tools" / "fixtures" / "gsdx_legacy_goals"
FIXTURE_GOALS = (
    ("4a226561feb32dc7df40388410bbde2f67e83614", "g-002-router-surface", 50),
    ("1f924bcabb838f1387a2afe5729e29b61891a3b4", "g-001-smoke-runner", 123),
)
LIVE_STATE = REAL_HOME / ".claude" / "state" / "gsd-x"
ALLOWED_EMAIL = "noreply@anthropic.com"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}".rstrip())
    else:
        fails += 1
        print(f"FAIL {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    """Run one gate body; a raise is a FAIL line, never an escape (audit G2).

    The summary line must always print: a gate that raises under a mutant would
    otherwise leave the drill UNJUDGED instead of KILLED.
    """
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- the point is to survive any gate body
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def refuse_live_root(path) -> bool:
    """True when `path` resolves under the real ~/.claude (same rule as gsdx_goal_timeline)."""
    try:
        resolved = Path(path).resolve()
        resolved.relative_to((REAL_HOME / ".claude").resolve())
        return True
    except ValueError:
        return False


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _event_files(goal_dir: Path) -> list[Path]:
    return sorted(p for p in goal_dir.iterdir() if EVENT_RE.match(p.name))


def verify_manifest(goal_dir: Path) -> tuple[bool, str]:
    """Every NNNNNN.json listed, every sha256 equal, count equal to `events`."""
    mpath = goal_dir / "MANIFEST.json"
    if not mpath.is_file():
        return False, "MANIFEST.json missing"
    try:
        man = json.loads(mpath.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"MANIFEST.json unreadable: {exc}"
    files = man.get("files") or {}
    present = {p.name: p for p in _event_files(goal_dir)}
    if set(present) != set(files):
        return False, f"file set differs: only-present={sorted(set(present) - set(files))[:3]} only-listed={sorted(set(files) - set(present))[:3]}"
    for name, want in sorted(files.items()):
        if _sha256(present[name]) != want:
            return False, f"sha256 mismatch {name}"
    if len(present) != man.get("events"):
        return False, f"count {len(present)} != events {man.get('events')}"
    return True, f"{len(present)} files verified"


def fixture_copy(repo: str, goal: str) -> GoalLog:
    """Copy the committed fixture goal dir into the hermetic goals root; return a GoalLog on the copy."""
    src = FIXTURE_ROOT / repo / goal
    dst = _TMP_GOALS / repo / goal
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for p in _event_files(src):
        shutil.copyfile(p, dst / p.name)
    return GoalLog(repo, goal)


def _scan(paths: list[Path]) -> list[str]:
    """File name + pattern name + line only; never a raw value (HR-SECRET-002)."""
    out = []
    for p in paths:
        for h in detector.scan_file(p):
            out.append(f"{p.name}:{h.pattern_name}:line{h.line_no}")
        text = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), start=1):
            for m in EMAIL_RE.finditer(line):
                if m.group(0).lower() != ALLOWED_EMAIL:
                    out.append(f"{p.name}:email:line{i}")
    return out


def capture_fixture(store: Path, repo: str, goal: str) -> int:
    dest = FIXTURE_ROOT / repo / goal
    if dest.exists():
        print(f"REFUSED: fixture {goal} already exists; delete it deliberately to recapture")
        return 2
    src = Path(store) / repo / goal
    if not src.is_dir():
        print(f"REFUSED: source {src} is not a directory")
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="pcc-capture-"))
    try:
        tdir = tmp / repo / goal
        tdir.mkdir(parents=True)
        for p in sorted(src.iterdir()):
            if EVENT_RE.match(p.name):
                shutil.copyfile(p, tdir / p.name)
        try:
            events = GoalLog(repo, goal, base=tmp).read()
        except GoalLogError as exc:
            print(f"REFUSED: {exc}")
            return 2
        if not events:
            print("REFUSED: no events")
            return 2
        hits = _scan(_event_files(tdir))
        if hits:
            print("REFUSED: secret/PII scan -- " + "; ".join(hits[:20]))
            return 2
        dest.mkdir(parents=True)
        files = {}
        for p in _event_files(tdir):
            shutil.copyfile(p, dest / p.name)
            files[p.name] = _sha256(dest / p.name)
        man = {
            "source_store": str(store),
            "repo": repo,
            "goal": goal,
            "events": len(events),
            "tip_digest": events[-1].digest,
            "files": files,
            "captured_on_head": git_state.head(ROOT),
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "secret_scan": "clean",
        }
        with open(dest / "MANIFEST.json", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(man, indent=1, sort_keys=True) + "\n")
        print(f"CAPTURED {goal} events={len(events)} tip={events[-1].digest[:12]}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gates_fixture() -> None:
    def home():
        ok = Path.home() == _TMP_HOME or str(Path.home()) == str(_TMP_HOME)
        g = Path(os.environ["GSDX_GOALS_ROOT"]).resolve()
        return ok and _TMP_GOALS.parent.resolve() in g.parents, f"home={_TMP_HOME.name}"
    run_gate("V-PCC-HERMETIC-HOME", home)

    def root_refusal():
        pos = refuse_live_root(REAL_HOME / ".claude" / "state" / "gsd-x" / "goals")
        neg = not refuse_live_root(_TMP_GOALS)
        return pos and neg, f"live-refused={pos} hermetic-allowed={neg}"
    run_gate("V-PCC-HERMETIC-ROOT-REFUSAL", root_refusal)

    def manifest():
        res = []
        for repo, goal, _n in FIXTURE_GOALS:
            ok, why = verify_manifest(FIXTURE_ROOT / repo / goal)
            res.append((ok, f"{goal}: {why}"))
        return all(r[0] for r in res), "; ".join(r[1] for r in res)
    run_gate("V-PCC-FIXTURE-MANIFEST", manifest)

    def tamper():
        repo, goal, _n = FIXTURE_GOALS[0]
        tmp = Path(tempfile.mkdtemp(prefix="pcc-tamper-"))
        try:
            dst = tmp / goal
            shutil.copytree(FIXTURE_ROOT / repo / goal, dst)
            first = dst / "000001.json"
            data = bytearray(first.read_bytes())
            data[len(data) // 2] ^= 0x01
            first.write_bytes(bytes(data))
            ok, why = verify_manifest(dst)
            return (not ok), f"tampered copy refused: {why}"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    run_gate("V-PCC-FIXTURE-TAMPER-REFUSED", tamper)

    for repo, goal, n in FIXTURE_GOALS:
        def chain(repo=repo, goal=goal, n=n):
            events = fixture_copy(repo, goal).read()
            man = json.loads((FIXTURE_ROOT / repo / goal / "MANIFEST.json").read_text(encoding="utf-8"))
            return (len(events) == n and events[-1].digest == man["tip_digest"]), f"events={len(events)} tip={events[-1].digest[:12]}"
        run_gate(f"V-PCC-REPLAY-CHAIN-{goal}", chain)


# --- discovery, snapshot, replay --------------------------------------------------

GOAL_PKG = ROOT / "modules" / "gsd_x" / "goal"
GOLDEN = ROOT / "tools" / "fixtures" / "gsdx_legacy_replay_golden.json"
T_FIXED = "git:pcc-replay-fixed-tree"
VOLATILE = "<volatile>"
# 7-64 lower-case hex, the GoalLog repo-id rule (audit G3).
SYN_REPO = "5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e"
SYN_PIN = (("tools/gate.py", "9" * 64),)
SYN_TREE = "git:" + "a" * 40
PROVIDERS = ("gate", "codex", "claude-headless")
FILE_SUFFIXES = {"json", "py", "lock", "sum", "yaml", "yml", "bundle", "tar", "log", "md",
                 "txt", "toml"}
TYPE_RE = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*$")
BOUNDARY_TYPES = frozenset({"epoch.receipt", "goal.judged", "failure.recorded",
                            "failure.dispositioned", "obligation.satisfied",
                            "obligation.dispositioned"})
RECORDED = {"g002": FIXTURE_GOALS[0], "g001": FIXTURE_GOALS[1]}
SYNTHETIC = ("syn_contract", "syn_carry", "syn_operator", "syn_evidence")
SCENARIOS = tuple(RECORDED) + SYNTHETIC


def discover_event_types(pkg_dir: Path) -> list[str]:
    """Module-level dotted string constants under `pkg_dir`, minus file names."""
    found: set[str] = set()
    for p in sorted(Path(pkg_dir).rglob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            v = node.value
            vals = [v] if isinstance(v, ast.Constant) else (list(v.elts) if isinstance(v, ast.Tuple) else [])
            for c in vals:
                if (isinstance(c, ast.Constant) and isinstance(c.value, str)
                        and TYPE_RE.match(c.value)
                        and c.value.split(".")[1] not in FILE_SUFFIXES):
                    found.add(c.value)
    return sorted(found)


def legacy_event_types() -> list[str]:
    """Discovered types, less the types the seam itself adds once `proof` exists."""
    found = set(discover_event_types(GOAL_PKG))
    try:
        from modules.gsd_x.goal import proof  # noqa: PLC0415
    except ImportError:
        return sorted(found)
    return sorted(found - set(proof.NEW_TYPES))


def pre_change_marker() -> list[str]:
    """Goal-package files that already name a PCC type (a golden taken now would postdate the seam)."""
    hits = []
    for p in sorted(GOAL_PKG.rglob("*.py")):
        text = p.read_text(encoding="utf-8")
        if re.search(r"""["']proof\.""", text) or re.search(r"""["']obligation\.contract["']""", text):
            hits.append(p.relative_to(ROOT).as_posix())
    return hits


def plain(o):
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        return {f.name: plain(getattr(o, f.name)) for f in dataclasses.fields(o)}
    if isinstance(o, dict):
        return {str(k): plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [plain(x) for x in o]
    if isinstance(o, (set, frozenset)):
        return sorted((plain(x) for x in o), key=lambda x: json.dumps(x, sort_keys=True))
    return o


def _try(fn):
    try:
        return plain(fn())
    except Exception as exc:  # noqa: BLE001 -- a raising projection is a diff, not a crash
        return {"__raised__": f"{type(exc).__name__}: {exc}"}


def _context(state, tree: str):
    obs = {e.epoch_id: ep.Observation(ep.OBS_RUNNING, "", "pcc-replay")
           for e in ep.project_epochs(state).values() if e.state == "running"}
    now = datetime.fromisoformat(state.events[-1].ts).timestamp() + 60
    return rc.Context(state=state, tree_hash=tree, scope_hash="scope:pcc-replay",
                      observations=obs, judge=jd.current(state, tree, state.revision),
                      now=now, budget=state.budget, providers=PROVIDERS,
                      engine="engine:pcc-replay")


def snapshot(log, tree: str) -> dict:
    """Every legacy projection of `log`, plain JSON. A raising projection is a value."""
    try:
        state = gc.project(log)
    except Exception as exc:  # noqa: BLE001
        return {"project": {"__raised__": f"{type(exc).__name__}: {exc}"}}
    snap = {"state": plain({f.name: getattr(state, f.name)
                            for f in dataclasses.fields(state) if f.name != "events"})}
    snap["convergence"] = _try(lambda: cv.project_convergence(state))
    snap["epochs"] = _try(lambda: ep.project_epochs(state))
    snap["open_epochs"] = _try(lambda: ep.open_epochs(state))
    snap["closure"] = _try(lambda: cv.goal_closure(state, tree, ep.open_epochs(state)))
    snap["operator"] = _try(lambda: iv.project_operator(state))
    snap["hypotheses"] = _try(lambda: evd.project_hypotheses(state))
    snap["judge"] = _try(lambda: jd.current(state, tree, state.revision))
    snap["autonomous"] = _try(lambda: sw.is_autonomous(state))
    snap["decide"] = _try(lambda: rc.decide(_context(state, tree)))
    return snap


def _t_last(events) -> str:
    for e in reversed(events):
        if e.type == cv.OB_SATISFIED:
            t = (e.data.get("verdict") or {}).get("tree_hash")
            if t:
                return t
    return T_FIXED


def prefix_record(log, events) -> dict:
    tl = _t_last(events)
    return {"tree_last": tl, "fixed": snapshot(log, T_FIXED), "last": snapshot(log, tl)}


def replay_raw(files, repo: str, goal: str) -> dict:
    """Grow a hermetic copy one event at a time; snapshot every prefix."""
    base = Path(tempfile.mkdtemp(prefix="pcc-replay-"))
    try:
        log = GoalLog(repo, goal, base=base)
        log.dir.mkdir(parents=True)
        types, recs = [], []
        for src in files:
            shutil.copyfile(src, log.dir / Path(src).name)
            events = log.read()
            types.append(events[-1].type)
            recs.append(prefix_record(log, events))
        return {"types": types, "recs": recs}
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _walk_set(rec, path, value) -> None:
    node = rec
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


def _resolvable(rec, path) -> bool:
    node = rec
    for key in path:
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            return False
    return True


def mask(rec: dict, paths) -> dict:
    out = copy.deepcopy(rec)
    for p in paths:
        p = list(p)
        if p and _resolvable(out, p):
            _walk_set(out, p, VOLATILE)
    return out


def diff_paths(a, b, path=()) -> list[list]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(list(path) + [k])
            else:
                out.extend(diff_paths(a[k], b[k], path + (k,)))
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff_paths(x, y, path + (i,)))
        return out
    return [] if a == b else [list(path)]


def digest_of(rec: dict) -> str:
    return hashlib.sha256(gl._canonical(rec)).hexdigest()


def finalize(raw: dict, volatile) -> dict:
    types, digests, full = raw["types"], [], {}
    n = len(types)
    for k, rec in enumerate(raw["recs"], start=1):
        m = mask(rec, volatile)
        digests.append(digest_of(m))
        if k % 10 == 0 or types[k - 1] in BOUNDARY_TYPES or k == n:
            full[str(k)] = m
    return {"n": n, "types": types, "digests": digests, "full": full}


# --- synthetic scenarios (public writers only) ------------------------------------

def _st(log):
    return gc.project(log)


def syn_contract(log, after) -> None:
    gc.declare(log, "Ship the replay corpus", ["a replay passes", "a mutant is caught"],
               ["no network", "no new deps"], {"paths": ["src"]}, actor="founder")
    after(log)
    st = _st(log)
    gc.revise(log, st.last_seq + 1, "Ship the replay corpus", ["a replay passes"],
              ["no network", "no new deps"], {"paths": ["src"]}, actor="founder",
              weakening_reason="the mutant check moved to its own goal")
    after(log)
    gc.set_budget(log, _st(log).last_seq + 1, {"max_epochs": 5}, "founder")      # no max_hours (audit G5)
    after(log)
    gc.set_authority(log, _st(log).last_seq + 1, {"mode": "supervised"}, "founder")
    after(log)


def syn_carry(log, after) -> None:
    gc.declare(log, "Carry obligations", ["it works"], [], {"paths": ["src"]}, actor="founder")
    after(log)
    for plane in cv.PLANES:
        cv.set_plane(log, _st(log), plane, plane in cv.ALWAYS,
                     "" if plane in cv.ALWAYS else "not claimed by this goal", "founder")
        after(log)
    for ob in ("ob-one", "ob-two"):
        cv.accept_obligation(log, _st(log), ob, cv.OUTCOME, f"do {ob}", "python tools/gate.py",
                             SYN_PIN, "founder")
        after(log)
    st = _st(log)
    res = cv.satisfy(log, st, "ob-one",
                     mcl.Verdict("tools/gate.py", 0, "ok", SYN_TREE, st.revision, "unit", SYN_PIN),
                     "founder", source={"epoch": "ep-syn", "provider": "gate"})
    if not res.allowed:
        raise RuntimeError(f"syn_carry: satisfy refused: {res.reason}")
    after(log)
    gc.revise(log, _st(log).last_seq + 1, "Carry obligations", ["it works", "it carries"], [],
              {"paths": ["src"]}, actor="founder")
    after(log)
    cv.carry_obligation(log, _st(log), "ob-one", "still means the same thing", "founder")
    after(log)


def syn_operator(log, after) -> None:
    gc.declare(log, "Operator control", ["it works"], [], {"paths": ["src"]}, actor="founder")
    after(log)
    for kind, kw in ((iv.PAUSE, {"reason": "hold for review"}),
                     (iv.NOTE, {"text": "checked the gate by hand"}),
                     (iv.RESUME, {"reason": "review done"}),
                     (iv.CANCEL, {"reason": "superseded by another goal"})):
        iv.intervene(log, _st(log), kind, "operator-1", **kw)
        after(log)


def syn_evidence(log, after) -> None:
    gc.declare(log, "Record hypotheses", ["it works"], [], {"paths": ["src"]}, actor="founder")
    after(log)
    evd.record(log, _st(log), "h-1", "The cache is stale", evd.OPEN, "analyst")
    after(log)
    evd.record(log, _st(log), "h-2", "The gate is flaky", evd.OPEN, "analyst")
    after(log)
    evd.record(log, _st(log), "h-1", "The cache is stale", evd.ESTABLISHED, "analyst",
               supporting=["ref-1"])
    after(log)
    evd.record(log, _st(log), "h-2", "The gate is flaky", evd.REJECTED, "analyst",
               contradicting=["ref-2"])
    after(log)


SYN_BUILDERS = {"syn_contract": syn_contract, "syn_carry": syn_carry,
                "syn_operator": syn_operator, "syn_evidence": syn_evidence}


def build_synthetic(name: str, after=None):
    """(event files, base dir to remove). `after(log)` runs after every public writer call."""
    base = Path(tempfile.mkdtemp(prefix="pcc-syn-"))
    log = GoalLog(SYN_REPO, name.replace("_", "-"), base=base)
    SYN_BUILDERS[name](log, after or (lambda _log: None))
    return _event_files(log.dir), base


def scenario_raw(name: str) -> dict:
    if name in RECORDED:
        repo, goal, _n = RECORDED[name]
        return replay_raw(_event_files(FIXTURE_ROOT / repo / goal), repo, goal)
    files, base = build_synthetic(name)
    try:
        return replay_raw(files, SYN_REPO, name.replace("_", "-"))
    finally:
        shutil.rmtree(base, ignore_errors=True)


# --- golden ------------------------------------------------------------------------

def load_golden():
    if not GOLDEN.is_file():
        return None
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def _write_golden(obj: dict) -> None:
    with open(GOLDEN, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=1, sort_keys=True) + "\n")


def _capture_scenario(name: str) -> tuple[dict, list]:
    """Build twice; paths that differ between the two builds are volatile and masked."""
    a, b = scenario_raw(name), scenario_raw(name)
    vol: list[list] = []
    for ra, rb in zip(a["recs"], b["recs"]):
        for p in diff_paths(ra, rb):
            if p not in vol:
                vol.append(p)
    if a["types"] != b["types"]:
        raise RuntimeError(f"{name}: two builds disagree on event types")
    return finalize(a, vol), vol


def capture_golden() -> int:
    if GOLDEN.exists():
        print("REFUSED: golden exists; use --amend <scenario> --why <text>")
        return 2
    marker = pre_change_marker()
    if marker:
        print("REFUSED: the goal package already names a PCC type: " + ", ".join(marker))
        return 2
    scenarios, volatile = {}, {}
    for name in SCENARIOS:
        scenarios[name], volatile[name] = _capture_scenario(name)
    meta = {
        "captured_on_head": git_state.head(ROOT),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "engine_identity": eid.engine_identity(ROOT),
        "goal_pkg_names_pcc": False,
        "legacy_goal_sha256": {p.relative_to(ROOT).as_posix(): _sha256(p)
                               for p in sorted(GOAL_PKG.rglob("*.py"))},
        "legacy_event_types": legacy_event_types(),
        "tree_contexts": {"T_FIXED": T_FIXED,
                          "T_LAST": "tree_hash of the latest satisfied verdict in the prefix, else T_FIXED"},
        "volatile_paths": volatile,
        "amendments": [],
    }
    _write_golden({"meta": meta, "scenarios": scenarios})
    print(f"CAPTURED golden scenarios={len(scenarios)} legacy_types={len(meta['legacy_event_types'])} "
          f"volatile={sum(len(v) for v in volatile.values())}")
    return 0


def amend_golden(name: str, why: str) -> int:
    golden = load_golden()
    if golden is None or name not in SCENARIOS or not (why or "").strip():
        print("REFUSED: --amend needs an existing golden, a known scenario and --why")
        return 2
    golden["scenarios"][name], golden["meta"]["volatile_paths"][name] = _capture_scenario(name)
    golden["meta"]["amendments"].append({
        "scenario": name, "why": why.strip(), "head": git_state.head(ROOT),
        "engine_identity": eid.engine_identity(ROOT),
        "at": datetime.now(timezone.utc).isoformat()})
    _write_golden(golden)
    print(f"AMENDED {name}")
    return 0


def compare_scenario(name: str, raw: dict, golden: dict) -> tuple[bool, str]:
    g = golden["scenarios"].get(name)
    if g is None:
        return False, f"{name}: not in golden"
    vol = golden["meta"]["volatile_paths"].get(name, [])
    fin = finalize(raw, vol)
    if fin["n"] != g["n"]:
        return False, f"{name}: {fin['n']} prefixes, golden has {g['n']}"
    for k, (have, want) in enumerate(zip(fin["digests"], g["digests"]), start=1):
        if have != want:
            where = ""
            if str(k) in g["full"]:
                where = " diff=" + "; ".join("/".join(str(x) for x in p)
                                            for p in diff_paths(fin["full"].get(str(k), mask(raw["recs"][k - 1], vol)),
                                                                g["full"][str(k)])[:4])
            return False, f"{name}: prefix {k} ({fin['types'][k - 1]}) differs{where}"
    return True, f"{name}: {fin['n']} prefixes equal"


def gates_replay() -> None:
    golden = load_golden()
    names = ("V-PCC-GOLDEN-PRE-CHANGE", "V-PCC-GOLDEN-RECORDED-NOT-VOLATILE", "V-PCC-REPLAY-G002",
             "V-PCC-REPLAY-G001", "V-PCC-REPLAY-SYNTHETIC", "V-PCC-REPLAY-POPULATION")
    if golden is None:
        for n in names:
            check(n, False, "golden absent: run --capture on the unmodified engine")
        return
    meta = golden["meta"]
    run_gate("V-PCC-GOLDEN-PRE-CHANGE",
             lambda: (meta.get("goal_pkg_names_pcc") is False and bool(meta.get("legacy_goal_sha256")),
                      f"head={str(meta.get('captured_on_head'))[:12]} legacy_files={len(meta.get('legacy_goal_sha256') or {})}"))
    run_gate("V-PCC-GOLDEN-RECORDED-NOT-VOLATILE",
             lambda: (not any(meta["volatile_paths"].get(n) for n in RECORDED),
                      f"volatile recorded={[n for n in RECORDED if meta['volatile_paths'].get(n)]}"))
    raws: dict[str, dict] = {}

    def raw_of(name):
        if name not in raws:
            raws[name] = scenario_raw(name)
        return raws[name]

    run_gate("V-PCC-REPLAY-G002", lambda: compare_scenario("g002", raw_of("g002"), golden))
    run_gate("V-PCC-REPLAY-G001", lambda: compare_scenario("g001", raw_of("g001"), golden))

    def synthetic():
        res = [compare_scenario(n, raw_of(n), golden) for n in SYNTHETIC]
        return all(r[0] for r in res), "; ".join(r[1] for r in res)
    run_gate("V-PCC-REPLAY-SYNTHETIC", synthetic)

    def population():
        corpus = set()
        for n in SCENARIOS:
            corpus |= set(raw_of(n)["types"])
        legacy = set(legacy_event_types())
        gold = set(meta["legacy_event_types"])
        return corpus == legacy == gold, f"corpus={len(corpus)} discovered={len(legacy)} golden={len(gold)} missing={sorted(legacy - corpus)}"
    run_gate("V-PCC-REPLAY-POPULATION", population)


# --- ignore-new-types, interleaving, mutants --------------------------------------

def load_proof():
    try:
        from modules.gsd_x.goal import proof  # noqa: PLC0415
        return proof
    except ImportError:
        return None


PROOF_ABSENT = "RED-first: modules.gsd_x.goal.proof absent"
_PIN_LIST = [["tools/gate.py", "9" * 64]]
_CAND = "cf1:" + "c" * 64


def pcc_sample_payloads() -> dict:
    """One well-formed v1 payload per PCC type, from spec S6/S7 field lists."""
    return {
        "obligation.contract": {
            "v": 1, "claim_id": "claim-1", "obligation": "ob-one", "combine": "AND",
            "elements": [{"oracle": "unit", "command": "python tools/gate.py", "gate_pin": _PIN_LIST,
                          "causal_paths": ["src"], "env_deps": [], "freshness_class": "unit",
                          "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}]},
        "proof.produced": {
            "v": 1, "claim_id": "claim-1", "candidate": _CAND, "binding": {"tree_hash": SYN_TREE},
            "revision": 1, "strength": "exact", "source": {"epoch": "ep-syn", "provider": "gate"}},
        "proof.inherited": {
            "v": 1, "claim_id": "claim-1", "certificate": "cert-1", "candidate": _CAND,
            "premises": {"claim": "equal", "oracle": "equal", "inputs": "equal", "env": "equal",
                         "gate_pin": "equal", "revision": "equal"}},
        "proof.invalidated": {
            "v": 1, "claim_id": "claim-1", "certificate": "cert-1", "reason": "premise changed"},
    }


def scenario_log(name: str):
    """(GoalLog on a hermetic copy, base dir to remove)."""
    if name in RECORDED:
        repo, goal, _n = RECORDED[name]
        base = Path(tempfile.mkdtemp(prefix="pcc-probe-"))
        log = GoalLog(repo, goal, base=base)
        log.dir.mkdir(parents=True)
        for src in _event_files(FIXTURE_ROOT / repo / goal):
            shutil.copyfile(src, log.dir / src.name)
        return log, base
    _files, base = build_synthetic(name)
    return GoalLog(SYN_REPO, name.replace("_", "-"), base=base), base


def append_event(log, type_: str, data: dict) -> None:
    log.append(log.read()[-1].seq + 1, type_, data, "pcc-replay")


def final_pair(log) -> dict:
    tl = _t_last(log.read())
    return {"tree_last": tl, "fixed": snapshot(log, T_FIXED), "last": snapshot(log, tl)}


def _get(node, path):
    for k in path:
        node = node[k]
    return node


def _set(node, path, value) -> bool:
    try:
        parent = _get(node, path[:-1])
        parent[path[-1]] = value
        return True
    except (KeyError, IndexError, TypeError):
        return False


def seq_mask_view(view: dict) -> dict:
    """Mask exactly the seq-valued fields (RESEARCH Pitfall 3) in one snapshot view."""
    v = copy.deepcopy(view)
    _set(v, ["state", "last_seq"], "<seq>")
    try:
        for i in range(len(v["state"]["revisions"])):
            _set(v, ["state", "revisions", i, 0], "<seq>")
    except (KeyError, TypeError):
        pass
    op_masked = _set(v, ["operator", "last_seq"], "<seq>")
    try:
        for i in range(len(v["operator"]["notes"])):
            _set(v, ["operator", "notes", i, 0], "<seq>")
    except (KeyError, TypeError):
        pass
    try:
        for fid in v["convergence"]["failures"]:
            _set(v, ["convergence", "failures", fid, "seq"], "<seq>")
    except (KeyError, TypeError):
        pass
    try:
        for hid, h in v["hypotheses"].items():
            for i in range(len(h["history"])):
                _set(v, ["hypotheses", hid, "history", i, 0], "<seq>")
    except (KeyError, TypeError, AttributeError):
        pass
    if op_masked:       # audit G1: the operator seq is also spelled inside decide.reason
        try:
            v["decide"]["reason"] = re.sub(r"at seq \d+", "at seq <seq>", v["decide"]["reason"])
        except (KeyError, TypeError):
            pass
    return v


def seq_mask(pair: dict) -> dict:
    return {"tree_last": pair["tree_last"], "fixed": seq_mask_view(pair["fixed"]),
            "last": seq_mask_view(pair["last"])}


def _golden_final(golden: dict, name: str) -> dict:
    g = golden["scenarios"][name]
    return g["full"][str(g["n"])]


def gate_ignore_new(extra) -> tuple[bool, str]:
    """Append `extra` [(type, data)] to every corpus log; legacy views equal the golden final prefix."""
    golden = load_golden()
    if golden is None:
        return False, "golden absent"
    bad = []
    for name in SCENARIOS:
        log, base = scenario_log(name)
        try:
            for t, d in extra:
                append_event(log, t, d)
            have = seq_mask(final_pair(log))
        finally:
            shutil.rmtree(base, ignore_errors=True)
        want = seq_mask(_golden_final(golden, name))
        if have != want:
            bad.append(f"{name}:{['/'.join(map(str, p)) for p in diff_paths(have, want)[:3]]}")
    return not bad, "all six scenarios equal" if not bad else "; ".join(bad)


def gate_ignore_pcc() -> tuple[bool, str]:
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    samples = pcc_sample_payloads()
    extra = [(t, samples[t]) for t in proof.NEW_TYPES]
    ok, ev = gate_ignore_new(extra)
    if not ok:
        return ok, ev
    log, base = scenario_log("syn_carry")
    try:
        for t, d in extra:
            append_event(log, t, d)
        led = proof.project_proofs(gc.project(log))
        n = len(led.contracts) + len(led.produced) + len(led.inherited) + len(led.invalidated)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return n == len(extra), f"{ev}; project_proofs records={n} appended={len(extra)}"


def gate_interleaved() -> tuple[bool, str]:
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    samples = pcc_sample_payloads()
    types = list(proof.NEW_TYPES)
    bad = []
    for name in SYNTHETIC:
        plain_snaps: list = []
        files, base = build_synthetic(name, lambda log: plain_snaps.append(
            seq_mask(final_pair(log))))
        shutil.rmtree(base, ignore_errors=True)
        inter: list = []
        counter = [0]

        def after(log, inter=inter, counter=counter):
            inter.append(seq_mask(final_pair(log)))
            t = types[counter[0] % len(types)]
            counter[0] += 1
            append_event(log, t, samples[t])
        _f, base2 = build_synthetic(name, after)
        shutil.rmtree(base2, ignore_errors=True)
        if len(plain_snaps) != len(inter):
            bad.append(f"{name}: {len(plain_snaps)} vs {len(inter)} steps")
            continue
        for k, (a, b) in enumerate(zip(plain_snaps, inter), start=1):
            if a != b:
                bad.append(f"{name} step {k}: {['/'.join(map(str, p)) for p in diff_paths(a, b)[:3]]}")
                break
    return not bad, "four synthetic scenarios equal at every writer step" if not bad else "; ".join(bad)


def gate_decide_sig() -> tuple[bool, str]:
    params = list(inspect.signature(rc.decide).parameters)
    dfields = [f.name for f in dataclasses.fields(rc.Decision)]
    cfields = [f.name for f in dataclasses.fields(rc.Context)]
    want_d = ["kind", "reason", "epoch_id", "spec", "provider", "hypothesis", "info_key", "packet"]
    want_c = ["state", "tree_hash", "scope_hash", "observations", "judge", "now", "budget",
              "providers", "blocked_on", "engine"]
    frozen = rc.Decision.__dataclass_params__.frozen is True
    return (params == ["ctx"] and dfields == want_d and cfields == want_c and frozen,
            f"params={params} decision={len(dfields)} context={len(cfields)} frozen={frozen}")


@contextlib.contextmanager
def patched(orig, factory):
    """Replace `orig` on EVERY module object holding it (Pitfall 5); always restore."""
    holders = []
    for mod in list(sys.modules.values()):
        try:
            for attr in (orig.__name__,):
                if getattr(mod, attr, None) is orig:
                    holders.append((mod, attr))
        except Exception:  # noqa: BLE001 -- lazy or exotic modules
            continue
    repl = factory(orig)
    try:
        for mod, attr in holders:
            setattr(mod, attr, repl)
        yield len(holders)
    finally:
        for mod, attr in holders:
            setattr(mod, attr, orig)


def _legacy_set() -> set:
    return set(legacy_event_types())


def _has_foreign(state) -> bool:
    return any(e.type not in _legacy_set() for e in state.events)


def mut_m1(orig):
    def fn(state):
        if _has_foreign(state):
            raise gl.GoalLogCorrupt("mutant M1: foreign event type")
        return orig(state)
    return fn


def mut_m2(orig):
    def fn(state):
        cvx = orig(state)
        for e in state.events:
            if e.type not in _legacy_set():
                cvx.failures["pcc-phantom"] = {"summary": "phantom", "disposition": None,
                                               "reason": "", "seq": e.seq}
        return cvx
    return fn


def mut_m3(orig):
    def fn(ctx):
        if _has_foreign(ctx.state):
            return rc.Decision("WAIT", "pcc")
        return orig(ctx)
    return fn


def mut_m4(orig):
    def fn(state):
        cvx = orig(state)
        cvx.obligations = dict(reversed(list(cvx.obligations.items())))
        return cvx
    return fn


def _probe(name: str, extra) -> dict:
    log, base = scenario_log(name)
    try:
        for t, d in extra:
            append_event(log, t, d)
        return final_pair(log)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def gate_mutant(label: str, orig, factory, scenario: str, extra, expect) -> tuple[bool, str]:
    clean = _probe(scenario, extra)
    with patched(orig, factory) as held:
        mutated = _probe(scenario, extra)
    hits = ["/".join(map(str, p)) for p in diff_paths(clean, mutated)]
    ok = held > 0 and any(expect(h) for h in hits)
    return ok, f"{label}: holders={held} hits={hits[:3]}"


def gate_gate_raise_survives() -> tuple[bool, str]:
    global passes, fails
    saved = (passes, fails)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            run_gate("V-PCC-SELFTEST-RAISES", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        line = buf.getvalue().strip()
        counted = fails == saved[1] + 1
    finally:
        passes, fails = saved
    return counted and line.startswith("FAIL V-PCC-SELFTEST-RAISES raised RuntimeError: boom"), line


def gates_seam() -> None:
    run_gate("V-PCC-DECIDE-SIG", gate_decide_sig)
    run_gate("V-PCC-GATE-RAISE-SURVIVES", gate_gate_raise_survives)
    fut = [("zz.future_event", {"v": 1})]
    run_gate("V-PCC-REPLAY-IGNORE-NEW-TYPES-FUTURE", lambda: gate_ignore_new(fut))
    run_gate("V-PCC-REPLAY-IGNORE-NEW-TYPES-PCC", gate_ignore_pcc)
    run_gate("V-PCC-REPLAY-INTERLEAVED", gate_interleaved)
    run_gate("V-PCC-MUTANT-M1", lambda: gate_mutant(
        "M1", cv.project_convergence, mut_m1, "g002", fut, lambda h: "__raised__" in h))
    run_gate("V-PCC-MUTANT-M2", lambda: gate_mutant(
        "M2", cv.project_convergence, mut_m2, "g002", fut, lambda h: "failures" in h))
    run_gate("V-PCC-MUTANT-M3", lambda: gate_mutant(
        "M3", rc.decide, mut_m3, "g002", fut, lambda h: h.split("/")[1:2] == ["decide"] or "decide" in h))
    run_gate("V-PCC-MUTANT-M4", lambda: gate_mutant(
        "M4", cv.project_convergence, mut_m4, "syn_carry", [],
        lambda h: "decide" in h or "obligations" in h))

    def clean():
        golden = load_golden()
        if golden is None:
            return False, "golden absent"
        res = [compare_scenario(n, scenario_raw(n), golden) for n in ("g002", "syn_carry")]
        return all(r[0] for r in res), "; ".join(r[1] for r in res)
    run_gate("V-PCC-CLEAN-AFTER-MUTANTS", clean)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--amend")
    ap.add_argument("--why", default="")
    ap.add_argument("--capture-fixture", action="store_true")
    ap.add_argument("--store")
    ap.add_argument("--repo")
    ap.add_argument("--goal")
    args = ap.parse_args()
    if args.capture_fixture:
        if not (args.store and args.repo and args.goal):
            print("REFUSED: --capture-fixture needs --store, --repo and --goal")
            return 2
        return capture_fixture(Path(args.store), args.repo, args.goal)
    if args.capture:
        return capture_golden()
    if args.amend:
        return amend_golden(args.amend, args.why)

    live_before = grb.fingerprint(LIVE_STATE)
    gates_fixture()
    gates_replay()
    gates_seam()

    def live_untouched():
        after = grb.fingerprint(LIVE_STATE)
        cmp = grb.compare(live_before, after)
        return cmp["verdict"] == "SAME", f"verdict={cmp['verdict']} changed={cmp['changed'][:3]}"
    run_gate("V-PCC-LIVE-STORE-UNTOUCHED", live_untouched)

    total = passes + fails
    print(f"\nGSDX_PCC_REPLAY_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
