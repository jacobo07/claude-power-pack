"""V-gates for the providerless console + coordinator budget (Tramo A2 Phase 7). Run: python tools/test_mission_console.py

Prints MISSION_CONSOLE_PASS=n/m. The coordinator profile is synthetic (tools/ccr_bench/coordinator.py); no real session is read.
"""
from __future__ import annotations

import ast
import json
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.ccr_bench import coordinator as co  # noqa: E402

GATES: list = []


def _gate(name):
    def deco(fn):
        GATES.append((name, fn))
        return fn
    return deco


@_gate("V-COORD-FIXTURE-SHAPE")
def _():
    rows = co.fixture()
    ssh = sum(1 for r in rows if "ssh" in str(r["input"].get("command", "")))
    tot = sum(r["carried"] for r in rows)
    assert len(rows) == 304 and ssh == 85, (len(rows), ssh)
    assert abs(tot - 67_900_000) < 100_000 and abs(statistics.median(r["carried"] for r in rows) - 214_000) / 214_000 < 0.05, tot


@_gate("V-COORD-CLASSIFY-BOTH-POLES")
def _():
    c = co.classify
    assert c("Bash", {"command": "ssh gex44 'python3 tools/gsd_mission.py status'"}) == "status"
    assert c("Bash", {"command": "ssh gex44 'python3 tools/mission_spend.py goal-status --goal ccr --consumers'"}) == "status"
    assert c("Bash", {"command": "ssh gex44 'python3 tools/gsd_mission.py authority --mission m --tokens 9'"}) == "relay"
    assert c("SendMessage", {"to": "w", "message": "go"}) == "relay"
    # controls: a status-looking read that WRITES is not a status call; an unknown command is novel
    assert c("Bash", {"command": "cat STATE.md > /etc/x"}) == "novel"
    assert c("Bash", {"command": "ps aux | tee out.txt"}) == "novel"
    assert c("Bash", {"command": "python3 -m pytest -q"}) == "novel"
    assert c("Edit", {"file_path": "x"}) == "novel"


@_gate("V-COORD-STATUS-BUDGET-ZERO")
def _():
    rows = co.fixture()
    base = co.profile(rows, covered=frozenset())           # positive control: with no console the status calls cost boundaries
    with_console = co.profile(rows)
    assert base["status_boundaries"] > 100 and with_console["status_boundaries"] == 0, (base, with_console)
    assert with_console["model_boundaries"] == base["model_boundaries"] - base["status_boundaries"]
    assert with_console["carried_after"] < base["carried_after"]


@_gate("V-CONSOLE-NO-MODEL-BOUNDARY")
def _():
    src = (REPO / "tools" / "mission_console.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)} | \
           {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert not (mods & {"anthropic", "openai", "requests", "urllib", "http"}), mods
    for n in ast.walk(tree):                               # no subprocess argv names a claude binary
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            assert n.value not in ("claude", "codex"), n.value
    assert "BatchMode=yes" in src and "stdin=subprocess.DEVNULL" in src


@_gate("V-CONSOLE-COLLECT-AND-UNREACHABLE")
def _():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "mission_console.py"), "collect"], capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout)
    assert r.returncode == 0 and set(d) == {"missions", "goals", "census"}, r.stderr
    # an unreachable host is a row that says so, not a silent absence (target that cannot resolve)
    s = subprocess.run([sys.executable, str(REPO / "tools" / "mission_console.py"), "--host", "x=ssh:nohost.invalid:/nope"],
                       capture_output=True, text=True, timeout=120)
    assert "== x ==" in s.stdout and "UNREACHABLE" in s.stdout, s.stdout


if __name__ == "__main__":
    res = []
    for name, fn in GATES:
        try:
            fn()
            res.append((name, True, ""))
        except Exception as exc:  # noqa: BLE001 -- reported by name
            res.append((name, False, f"{type(exc).__name__}: {exc}"))
    for name, ok, why in res:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" -- {why}"))
    n = sum(1 for _, ok, _w in res if ok)
    print(f"MISSION_CONSOLE_PASS={n}/{len(res)}")
    raise SystemExit(0 if n == len(res) else 1)
