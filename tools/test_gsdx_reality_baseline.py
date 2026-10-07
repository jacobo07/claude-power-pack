#!/usr/bin/env python3
"""V-RB-* gates for tools/gsdx_reality_baseline.py -- every detector driven from both poles.

    python tools/test_gsdx_reality_baseline.py

Hermetic: HOME/USERPROFILE point at a temp dir for this process and every child; the
guard is always a temp dir (never the real ~/.claude/state/gsd-x); synthetic suites live
under a temp --repo-root. Summary line: GSDX_REALITY_BASELINE_PASS=n/m  threshold=n/m.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "gsdx_reality_baseline.py"
TMP = Path(tempfile.mkdtemp(prefix="gsdx_rb_test_"))
HOME = TMP / "home"
HOME.mkdir()
os.environ.update(HOME=str(HOME), USERPROFILE=str(HOME), PYTHONIOENCODING="utf-8")

passes = 0
fails = 0


def check(gate: str, ok: bool, detail) -> None:
    global passes, fails
    if ok:
        passes += 1
        print(f"  PASS {gate}: {detail}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {detail}")


def tool(*args, env=None):
    r = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env or dict(os.environ), timeout=300)
    return r.returncode, r.stdout + r.stderr


def repo(name: str, suites: dict[str, str]) -> Path:
    root = TMP / name
    (root / "tools").mkdir(parents=True)
    for fname, body in suites.items():
        (root / "tools" / fname).write_text(body, encoding="utf-8")
    return root


def rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def guard_dir(name: str) -> Path:
    g = TMP / name
    g.mkdir()
    (g / "seed.json").write_text("{}", encoding="utf-8")
    return g


def run_suite(root: Path, suite: str, out: Path, guard: Path, *extra, env=None):
    return tool("suites", "--repo-root", root, "--suite", f"tools/{suite}", "--runs", "1",
                "--out", out, "--log-dir", out.parent / (out.stem + "-logs"), "--guard-dir", guard,
                *extra, env=env)


def main() -> int:
    if not TOOL.is_file():
        print(f"  FAIL V-RB-TOOL-EXISTS: {TOOL} is missing")
        print(f"\nGSDX_REALITY_BASELINE_PASS=0/16  threshold=16/16")
        return 1
    sys.path.insert(0, str(ROOT / "tools"))
    import gsdx_reality_baseline as rb  # noqa: E402

    # --- fingerprint ---------------------------------------------------------------
    fp_dir = guard_dir("fp")
    snap = TMP / "fp.json"
    rc0, _ = tool("fingerprint", "--dir", fp_dir, "--out", snap)
    rc, out = tool("fingerprint", "--dir", fp_dir, "--against", snap)
    check("V-RB-FP-SAME", rc0 == 0 and rc == 0, f"rc={rc} {out.strip()[:80]}")
    (fp_dir / "added.txt").write_text("x", encoding="utf-8")
    rc, out = tool("fingerprint", "--dir", fp_dir, "--against", snap)
    check("V-RB-FP-DETECTS-WRITE", rc == 1 and "added.txt" in out, f"rc={rc} {out.strip()[:120]}")
    (fp_dir / "added.txt").unlink()
    (fp_dir / "seed.json").unlink()
    rc, out = tool("fingerprint", "--dir", fp_dir, "--against", snap)
    check("V-RB-FP-DETECTS-DELETE", rc == 1 and "-1" in out, f"rc={rc} {out.strip()[:120]}")
    bad = TMP / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    rc, out = tool("fingerprint", "--dir", fp_dir, "--against", bad)
    check("V-RB-FP-UNREADABLE-IS-UNKNOWN", rc == 2 and "SAME" not in out, f"rc={rc} {out.strip()[:120]}")

    # --- summary parse ---------------------------------------------------------------
    a = rb.parse_summary("x\nOLD_PASS=1/9\nX_PASS=3/4  threshold=4/4\n")
    b = rb.parse_summary("Y_CAUGHT=5/5  threshold=5/5")
    c = rb.parse_summary("no summary here")
    check("V-RB-SUMMARY-PARSE",
          a and a["token"] == "X_PASS" and (a["passed"], a["total"]) == (3, 4)
          and b and b["token"] == "Y_CAUGHT" and (b["passed"], b["total"]) == (5, 5) and c is None,
          f"{a} {b} {c}")

    # --- timed suite runs ---------------------------------------------------------------
    env_probe = ("import json,os\nprint('ENV='+json.dumps({k:os.environ.get(k) for k in "
                 "('HOME','USERPROFILE','GSDX_GOALS_ROOT')}))\nprint('SYN_PASS=1/1')\n")
    guard_write = ("import os,pathlib\npathlib.Path(os.environ['RB_TEST_GUARD'],'leak.txt').write_text('x')\n"
                   "print('SYN_PASS=1/1')\n")
    heartbeat = ("import os,pathlib\npathlib.Path(os.environ['RB_TEST_GUARD'],'sweep_heartbeat.json')"
                 ".write_text('{}')\nprint('SYN_PASS=1/1')\n")
    root = repo("r1", {"syn_ok.py": "print('SYN_PASS=2/2')\n",
                       "syn_fail.py": "import sys\nprint('SYN_PASS=1/2')\nsys.exit(1)\n",
                       "syn_silent.py": "pass\n",
                       "syn_env.py": env_probe,
                       "syn_guard.py": guard_write,
                       "syn_heartbeat.py": heartbeat})
    g = guard_dir("g1")
    out1 = TMP / "ok.jsonl"
    rc, txt = run_suite(root, "syn_ok.py", out1, g)
    rc2, _ = run_suite(root, "syn_ok.py", out1, g)
    runs = [r for r in rows(out1) if r["kind"] == "run"]
    first = runs[0] if runs else {}
    check("V-RB-SUITE-TIMED",
          rc == 0 and rc2 == 0 and len(runs) == 2 and first.get("wall_s", 0) > 0
          and first.get("returncode") == 0 and (first.get("passed"), first.get("total")) == (2, 2)
          and Path(first.get("log", "")).is_file() and first.get("cold") is True
          and runs[1].get("cold") is False,
          f"rc={rc}/{rc2} rows={len(runs)} first={ {k: first.get(k) for k in ('wall_s', 'returncode', 'passed', 'total', 'cold')} } {txt.strip()[:100]}")

    out2 = TMP / "fail.jsonl"
    rc, txt = run_suite(root, "syn_fail.py", out2, g)
    r = [x for x in rows(out2) if x["kind"] == "run"]
    check("V-RB-SUITE-FAIL-RECORDED", rc == 1 and r and r[0]["returncode"] == 1,
          f"rc={rc} row_rc={r[0]['returncode'] if r else None}")

    out3 = TMP / "silent.jsonl"
    rc, txt = run_suite(root, "syn_silent.py", out3, g)
    r = [x for x in rows(out3) if x["kind"] == "run"]
    check("V-RB-NO-SUMMARY-UNJUDGED", rc == 1 and r and r[0]["summary"] is None and r[0]["returncode"] == 0,
          f"rc={rc} summary={r[0]['summary'] if r else 'no row'}")

    out4 = TMP / "env.jsonl"
    rc, txt = run_suite(root, "syn_env.py", out4, g)
    r = [x for x in rows(out4) if x["kind"] == "run"]
    seen = {}
    if r:
        for line in Path(r[0]["log"]).read_text(encoding="utf-8").splitlines():
            if line.startswith("ENV="):
                seen = json.loads(line[4:])
    tmp_root = Path(tempfile.gettempdir()).resolve()
    vals = [seen.get(k) for k in ("HOME", "USERPROFILE", "GSDX_GOALS_ROOT")]
    check("V-RB-HERMETIC-ENV",
          rc == 0 and all(vals) and all(Path(v).resolve().is_relative_to(tmp_root) for v in vals)
          and all(Path(v).resolve() != HOME.resolve() for v in vals[:2])
          and Path(vals[2]).name == "goals",
          f"rc={rc} {seen}")

    g2 = guard_dir("g2")
    out5 = TMP / "guard.jsonl"
    env = dict(os.environ, RB_TEST_GUARD=str(g2))
    rc, txt = run_suite(root, "syn_guard.py", out5, g2, env=env)
    gr = [x for x in rows(out5) if x["kind"] == "guard"]
    check("V-RB-GUARD-TRIPS",
          rc == 3 and gr and gr[0]["verdict"] == "CHANGED" and any("leak.txt" in c for c in gr[0]["changed"]),
          f"rc={rc} guard={gr[0] if gr else None}")

    # The guard ignores ONLY the named scheduler heartbeat (measured confound, 01-01 Task 1):
    # the heartbeat changing reads SAME (and is recorded), any other file still trips it.
    g3 = guard_dir("g3")
    out6 = TMP / "heartbeat.jsonl"
    env = dict(os.environ, RB_TEST_GUARD=str(g3))
    rc, txt = run_suite(root, "syn_heartbeat.py", out6, g3, env=env)
    gr = [x for x in rows(out6) if x["kind"] == "guard"]
    hb_ok = rc == 0 and gr and gr[0]["verdict"] == "SAME" and gr[0].get("excluded_changed")
    out7 = TMP / "heartbeat-ctl.jsonl"
    rc_c, _ = run_suite(root, "syn_guard.py", out7, g3, env=env)
    gc = [x for x in rows(out7) if x["kind"] == "guard"]
    check("V-RB-GUARD-EXCLUDES-ONLY-NAMED",
          hb_ok and rc_c == 3 and gc and gc[0]["verdict"] == "CHANGED",
          f"heartbeat rc={rc} verdict={gr[0]['verdict'] if gr else None} "
          f"excluded_changed={gr[0].get('excluded_changed') if gr else None}; control rc={rc_c}")

    # --- Task 2 gates ---------------------------------------------------------------
    if hasattr(rb, "LIVE_MUTATING"):
        task2(rb)

    total = passes + fails
    print(f"\nGSDX_REALITY_BASELINE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


def task2(rb) -> None:
    root = repo("r2", {"syn_sleep.py": "import time\ntime.sleep(30)\nprint('SYN_PASS=1/1')\n"})
    g = guard_dir("g4")
    out = TMP / "timeout.jsonl"
    rc, txt = run_suite(root, "syn_sleep.py", out, g, "--timeout", "1")
    r = [x for x in rows(out) if x["kind"] == "run"]
    check("V-RB-TIMEOUT",
          rc == 1 and r and r[0]["timed_out"] is True and r[0]["returncode"] is None and r[0]["summary"] is None,
          f"rc={rc} row={ {k: r[0].get(k) for k in ('timed_out', 'returncode', 'summary')} if r else None}")

    # A synthetic suite carrying the live-mutating name: it overwrites <its ROOT>/modules/target.txt.
    mut = ("import pathlib\nroot = pathlib.Path(__file__).resolve().parents[1]\n"
           "(root / 'modules' / 'target.txt').write_text('MUTATED', encoding='utf-8')\n"
           "print('SYN_CAUGHT=1/1')\n")
    root = repo("r3", {"test_gsd_x_goal_mutation.py": mut})
    (root / "modules").mkdir()
    target = root / "modules" / "target.txt"
    target.write_text("original", encoding="utf-8")
    sha0 = hashlib.sha256(target.read_bytes()).hexdigest()
    out = TMP / "mut.jsonl"
    rc, txt = run_suite(root, "test_gsd_x_goal_mutation.py", out, g)
    check("V-RB-LIVE-MUTATING-REFUSED",
          rc == 2 and not [x for x in rows(out) if x["kind"] == "run"]
          and hashlib.sha256(target.read_bytes()).hexdigest() == sha0,
          f"rc={rc} rows={len(rows(out))} {txt.strip()[:120]}")

    rc, txt = run_suite(root, "test_gsd_x_goal_mutation.py", out, g, "--in-copy")
    r = [x for x in rows(out) if x["kind"] == "run"]
    sha1 = hashlib.sha256(target.read_bytes()).hexdigest()
    check("V-RB-IN-COPY-ISOLATED",
          rc == 0 and r and r[0]["in_copy"] is True and (r[0]["summary"] or "").split("=")[0].endswith("_CAUGHT")
          and sha1 == sha0,
          f"rc={rc} in_copy={r[0]['in_copy'] if r else None} summary={r[0]['summary'] if r else None} "
          f"live_sha_unchanged={sha1 == sha0} {txt.strip()[:120]}")

    out = TMP / "unknown.jsonl"
    rc, _ = tool("unknown", "--out", out, "--suite", "S", "--reason", "R")
    u = rows(out)
    check("V-RB-UNKNOWN-ROW",
          rc == 0 and len(u) == 1 and u[0].get("kind") == "unknown" and u[0].get("suite") == "S"
          and u[0].get("reason") == "R",
          f"rc={rc} rows={u}")

    src = TMP / "table.jsonl"
    hand = [
        {"kind": "run", "suite": "A", "path": "tools/A.py", "in_copy": False, "cold": True, "wall_s": 2.0,
         "returncode": 0, "timed_out": False, "summary": "A_PASS=2/2", "passed": 2, "total": 2},
        {"kind": "run", "suite": "A", "path": "tools/A.py", "in_copy": False, "cold": False, "wall_s": 1.5,
         "returncode": 0, "timed_out": False, "summary": "A_PASS=2/2", "passed": 2, "total": 2},
        {"kind": "unknown", "suite": "B", "reason": "needs a live host"},
    ]
    src.write_text("".join(json.dumps(h) + "\n" for h in hand), encoding="utf-8")
    md = TMP / "table.md"
    rc, txt = tool("table", "--in", src, "--baseline", "A=3/3", "--md-out", md)
    a_line = next((l for l in txt.splitlines() if l.startswith("| A ")), "")
    b_line = next((l for l in txt.splitlines() if l.startswith("| B ")), "")
    cells = [c.strip() for c in a_line.strip("|").split("|")]
    check("V-RB-TABLE",
          rc == 0 and cells[1:6] == ["2", "2.000", "1.500", "2.000", "0"] and "A_PASS=2/2" in a_line
          and "DIFFERS (baseline 3/3)" in a_line and "UNKNOWN (needs a live host)" in b_line
          and md.is_file() and md.read_text(encoding="utf-8").strip() in txt,
          f"rc={rc} A={a_line} B={b_line}")


if __name__ == "__main__":
    sys.exit(main())
