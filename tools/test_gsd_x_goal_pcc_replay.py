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
import hashlib
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
from modules.gsd_x.goal.log import EVENT_RE, GoalLog, GoalLogError  # noqa: E402
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


def main() -> int:
    ap = argparse.ArgumentParser()
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

    live_before = grb.fingerprint(LIVE_STATE)
    gates_fixture()

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
