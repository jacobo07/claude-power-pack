#!/usr/bin/env python3
"""V-BLR-* -- the SessionStart backlog-ledger refresh (spec vault/specs/backlog-ledger-refresh.md), both poles.

Hermetic: every state dir and root is a temp dir. The gate is driven through node (its real code), the worker
as a subprocess against a synthetic root that carries the REAL ledger/inventory modules.
Run: python tools/test_backlog_ledger_refresh.py   (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "hooks" / "backlog_ledger_refresh.js"
WORKER = ROOT / "tools" / "backlog_ledger_refresh.py"
NODE = shutil.which("node") or "node"
_TMP = tempfile.mkdtemp(prefix="v-blr-")
RESULTS: list = []
GB = 1 << 30


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-34s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:300]))


def gate(payload: dict, root: str, state: str, free: int = 8 * GB, now_ms: float | None = None, env: dict | None = None):
    js = ("const g=require(%s);const d=g.decide(%s,{root:%s,freemem:%d,now:%s,env:%s});"
          "process.stdout.write(JSON.stringify(d));") % (
        json.dumps(str(GATE)), json.dumps(payload), json.dumps(root), free,
        json.dumps(now_ms if now_ms is not None else time.time() * 1000),
        json.dumps(dict({"CPP_BACKLOG_STATE_DIR": state}, **(env or {}))))
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("node gate failed: %s" % r.stderr[-400:])
    return json.loads(r.stdout)


def synthetic_root(with_module: bool = True) -> str:
    r = tempfile.mkdtemp(dir=_TMP)
    pkg = Path(r, "modules", "backlog_autopilot")
    # The real package cannot be lifted out (its __init__ -> engine -> modules.ias_c2 ...), so the worker's CONTRACT
    # (lock, snapshot, history row, verify verdict) is driven here through a stub with the same interface. The real
    # build is evidenced by one end-to-end run on the repo itself (spec, "Evidence") and by V-ASC-LEDGER.
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    if with_module:
        (pkg / "inventory.py").write_text("def build(root):\n    return {'identities': []}\n", encoding="utf-8")
        (pkg / "ledger.py").write_text(
            "def build(root, inventory):\n"
            "    m = {'numerator': 0, 'denominator': 0, 'ratio': None}\n"
            "    return {'rows': [], 'reconciliation': m, 'operational': m, 'by_state': {}, 'blocked_in_denominator': 0}\n"
            "def verify(led, inventory):\n    return []\n", encoding="utf-8")
    else:
        (pkg / "ledger.py").write_text("raise ImportError('broken on purpose')\n", encoding="utf-8")
    os.makedirs(os.path.join(r, "sub"))
    return r


def worker(root: str, state: str, slug: str = "s1") -> int:
    env = dict(os.environ, CPP_BACKLOG_STATE_DIR=state)
    return subprocess.run([sys.executable, str(WORKER), "--root", root, "--slug", slug], env=env,
                          capture_output=True, text=True, timeout=300).returncode


def rows(state: str, slug: str) -> list:
    p = Path(state, "%s.history.jsonl" % slug)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def test_gate() -> None:
    root = synthetic_root()
    st = tempfile.mkdtemp(dir=_TMP)
    inside = {"cwd": os.path.join(root, "sub")}
    d = gate(inside, root, st)
    ok("V-BLR-GATE-SPAWN", d["action"] == "spawn" and d["why"] == "never refreshed", d)
    ok("V-BLR-GATE-KILL", gate(inside, root, st, env={"CPP_BACKLOG_REFRESH": "off"})["why"] == "kill switch")
    ok("V-BLR-GATE-OUTSIDE", gate({"cwd": _TMP}, root, st)["why"] == "cwd outside the tree")
    sib = root + "x"                                          # a sibling sharing the prefix is outside
    os.makedirs(sib)
    ok("V-BLR-GATE-PREFIX-SIBLING", gate({"cwd": sib}, root, st)["why"] == "cwd outside the tree")
    ok("V-BLR-GATE-NO-MODULE", gate({"cwd": _TMP}, _TMP, st)["why"] == "no ledger module")
    low = gate(inside, root, st, free=1 * GB)
    gl = Path(st, "%s.gate.jsonl" % d["slug"])
    ok("V-BLR-GATE-LOWMEM", low["action"] == "skip" and low["why"] == "low memory" and gl.exists()
       and '"low memory"' in gl.read_text(encoding="utf-8"), low)
    lock = Path(st, "%s.lock" % d["slug"])
    lock.write_text("1", encoding="utf-8")
    ok("V-BLR-GATE-LOCKED", gate(inside, root, st)["why"] == "worker running")
    old = time.time() - 7200
    os.utime(lock, (old, old))
    ok("V-BLR-GATE-STALE-LOCK", gate(inside, root, st)["action"] == "spawn")
    lock.unlink()
    # a refresh row 1 h old: fresh (no spawn) AND announced once, with the delta vs the row before
    hist = Path(st, "%s.history.jsonl" % d["slug"])
    base = {"verify": "PASS", "head": "abc", "operational": {"numerator": 3, "denominator": 374, "ratio": 0.008}}
    with open(hist, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(base, ts=time.time() - 90000, reconciliation={"numerator": 372, "denominator": 471,
                                                                               "ratio": 0.7898})) + "\n")
        fh.write(json.dumps(dict(base, ts=time.time() - 3600, reconciliation={"numerator": 373, "denominator": 472,
                                                                              "ratio": 0.7903})) + "\n")
    first = gate(inside, root, st)
    ok("V-BLR-GATE-FRESH", first["action"] == "skip" and first["why"] == "fresh", first)
    ok("V-BLR-ANNOUNCE", "373/472" in first["context"] and "[+1/+1]" in first["context"] and "VERIFY PASS"
       in first["context"], first["context"])
    ok("V-BLR-ANNOUNCE-ONCE", gate(inside, root, st)["context"] == "")
    stale = gate(inside, root, st, now_ms=(time.time() + 86400 * 2) * 1000)
    ok("V-BLR-GATE-STALE", stale["action"] == "spawn" and stale["why"] == "stale", stale)
    with open(hist, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": time.time(), "error": "ImportError: boom", "head": "def"}) + "\n")
    failed = gate(inside, root, st)
    ok("V-BLR-ANNOUNCE-FAILURE", "FAILED" in failed["context"] and "boom" in failed["context"]
       and failed["why"] == "fresh", failed)


def test_worker() -> None:
    st = tempfile.mkdtemp(dir=_TMP)
    root = synthetic_root()
    rc = worker(root, st)
    r = rows(st, "s1")
    snap = Path(st, "s1.json")
    ok("V-BLR-WORKER-REAL", rc == 0 and len(r) == 1 and r[0].get("verify") == "PASS" and "reconciliation" in r[0]
       and snap.exists() and "rows" in json.loads(snap.read_text(encoding="utf-8")), "rc=%s rows=%s" % (rc, r))
    ok("V-BLR-WORKER-UNLOCKED", not Path(st, "s1.lock").exists())
    bad = synthetic_root(with_module=False)
    rc = worker(bad, st, "s2")
    r2 = rows(st, "s2")
    ok("V-BLR-WORKER-FAIL-VISIBLE", rc == 1 and len(r2) == 1 and "error" in r2[0] and not Path(st, "s2.lock").exists(),
       "rc=%s rows=%s" % (rc, r2))
    Path(st, "s3.lock").write_text("held", encoding="utf-8")
    rc = worker(root, st, "s3")
    ok("V-BLR-WORKER-SINGLE-FLIGHT", rc == 2 and rows(st, "s3") == [] and Path(st, "s3.lock").exists(), "rc=%s" % rc)


def test_wired() -> None:
    disp = (ROOT / "hooks" / "hook-dispatcher.js").read_text(encoding="utf-8")
    i = disp.find("'SessionStart-chain': [")
    seg = disp[i:disp.find("],", i)]
    ok("V-BLR-WIRED", i >= 0 and "hooks/backlog_ledger_refresh.js" in seg, "SessionStart-chain lacks the gate")


def main() -> int:
    try:
        for t in (test_gate, test_worker, test_wired):
            try:
                t()
            except Exception as exc:  # noqa: BLE001 -- a crashed section is a FAIL, never a skip
                ok("V-BLR-CRASH-%s" % t.__name__, False, "%s: %s" % (type(exc).__name__, exc))
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    passed = sum(1 for _, c in RESULTS if c)
    print("V-BLR: %d passed, %d failed" % (passed, len(RESULTS) - passed))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
