#!/usr/bin/env python3
"""Incumbent-measurement instrument for the GSD X goal suites (gsdx-pcc phase 1, R01).

Times suites serially under a hermetic environment, with a before/after fingerprint
guard around the live goal state, and appends one durable JSONL row per run.

    python tools/gsdx_reality_baseline.py fingerprint --dir D --out F
    python tools/gsdx_reality_baseline.py fingerprint --dir D --against F
    python tools/gsdx_reality_baseline.py suites --out F.jsonl --log-dir L [--suite P]... [--runs N]
        [--timeout S] [--guard-dir D]... [--in-copy] [--repo-root R] [--label T] [--keep-temp]
    python tools/gsdx_reality_baseline.py unknown --out F.jsonl --suite NAME --reason TEXT
    python tools/gsdx_reality_baseline.py table --in F.jsonl [--baseline NAME=n/m]... [--md-out M]

Exit codes. fingerprint --against: 0 SAME, 1 CHANGED, 2 UNKNOWN. suites: 0 every run passed,
1 any run failed / printed no summary / timed out, 2 usage or refusal, 3 guard CHANGED or UNKNOWN.

Analogs: the summary grammar extends tools/evidence_bundle.py:43 with `_CAUGHT`
(tools/test_gsd_x_goal_mutation.py prints GSDX_GOAL_MUTATIONS_CAUGHT=); the hermetic
HOME/USERPROFILE redirect follows tools/test_family_injection.py:78-84; the timed child
and own-mkdtemp cleanup follow tools/mutation_drill.py:142-156. Stdlib only.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REAL_HOME = Path.home()
DEFAULT_GUARD = REAL_HOME / ".claude" / "state" / "gsd-x"
# The scheduler rewrites its heartbeat on every sweep whether or not a suite runs
# (measured confound, 01-01 Task 1). Only these exact file names are excluded; a change
# to one is still recorded on the guard row as `excluded_changed`.
DEFAULT_GUARD_EXCLUDE = ("sweep_heartbeat.json",)
SUMMARY_RE = re.compile(r"\b([A-Z][A-Z0-9_]*_(?:PASS|CAUGHT))=(\d+)/(\d+)")


def parse_summary(text: str) -> dict | None:
    """Last `<SUITE>_PASS=n/m` or `<SUITE>_CAUGHT=n/m` in text; None when absent (never 0/0)."""
    matches = list(SUMMARY_RE.finditer(text or ""))
    if not matches:
        return None
    m = matches[-1]
    return {"text": m.group(0), "token": m.group(1), "passed": int(m.group(2)), "total": int(m.group(3))}


def _walk(path: Path, exclude=DEFAULT_GUARD_EXCLUDE):
    """(listing {rel: [size, mtime_ns]}, excluded listing, error count)."""
    listing, excluded, errors = {}, {}, 0

    def onerror(_exc):
        nonlocal errors
        errors += 1

    for dirpath, _dirs, files in os.walk(path, onerror=onerror):
        for name in files:
            full = Path(dirpath) / name
            rel = full.relative_to(path).as_posix()
            try:
                st = full.stat()
            except OSError:
                errors += 1
                continue
            (excluded if name in exclude else listing)[rel] = [st.st_size, st.st_mtime_ns]
    return listing, excluded, errors


def fingerprint(path, exclude=DEFAULT_GUARD_EXCLUDE) -> dict:
    path = Path(path)
    if not path.exists():
        return {"dir": str(path), "exists": False, "files": 0, "max_mtime_ns": 0, "errors": 0,
                "digest": None, "excluded": {}}
    listing, excluded, errors = _walk(path, exclude)
    digest = hashlib.sha256(json.dumps(sorted(listing.items())).encode("utf-8")).hexdigest()
    return {"dir": str(path), "exists": True, "files": len(listing),
            "max_mtime_ns": max((v[1] for v in listing.values()), default=0), "errors": errors,
            "digest": digest, "excluded": excluded}


_FP_KEYS = ("dir", "exists", "files", "max_mtime_ns", "errors", "digest")


def compare(before, after, exclude=DEFAULT_GUARD_EXCLUDE) -> dict:
    """SAME / CHANGED / UNKNOWN. UNKNOWN when either side is malformed or saw walk errors."""
    if not (isinstance(before, dict) and isinstance(after, dict)
            and all(k in before for k in _FP_KEYS) and all(k in after for k in _FP_KEYS)):
        return {"verdict": "UNKNOWN", "reason": "malformed fingerprint", "changed": [], "delta": None,
                "excluded_changed": []}
    if before["errors"] or after["errors"]:
        return {"verdict": "UNKNOWN", "reason": f"walk errors before={before['errors']} after={after['errors']}",
                "changed": [], "delta": None, "excluded_changed": []}
    ex_b, ex_a = before.get("excluded") or {}, after.get("excluded") or {}
    excluded_changed = sorted(k for k in set(ex_b) | set(ex_a) if ex_b.get(k) != ex_a.get(k))
    delta = after["files"] - before["files"]
    changed = []
    if after["exists"]:
        listing, _ex, _err = _walk(Path(after["dir"]), exclude)
        changed = sorted(k for k, v in listing.items() if v[1] > before["max_mtime_ns"])
    same = (before["exists"] == after["exists"] and before["digest"] == after["digest"])
    return {"verdict": "SAME" if same else "CHANGED", "reason": None, "changed": changed, "delta": delta,
            "excluded_changed": excluded_changed}


def hermetic_env(tmp: Path) -> dict:
    env = dict(os.environ)
    home = tmp / "home"
    home.mkdir(parents=True, exist_ok=True)
    env.update(HOME=str(home), USERPROFILE=str(home), GSDX_GOALS_ROOT=str(tmp / "goals"),
               PYTHONIOENCODING="utf-8")
    env.pop("GSDX_GOAL_EPOCH", None)  # a set epoch makes the judge refuse (judge.py:125-128)
    return env


def free_ram_mb():
    try:
        if os.name == "nt":
            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = MS()
            ms.dwLength = ctypes.sizeof(MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                return ms.ullAvailPhys // (1024 * 1024)
            return None
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, AttributeError):
        return None
    return None


def _load_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cmd_fingerprint(a) -> int:
    fp = fingerprint(a.dir)
    if a.out:
        Path(a.out).write_text(json.dumps(fp, indent=1), encoding="utf-8")
        print(f"fingerprint written: {a.out} files={fp['files']} errors={fp['errors']}")
        return 0
    try:
        before = json.loads(Path(a.against).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"UNKNOWN: cannot read fingerprint {a.against}: {exc}")
        return 2
    res = compare(before, fp)
    print(f"{res['verdict']}: files {before.get('files')} -> {fp['files']} (delta {res['delta']:+d})"
          if res["delta"] is not None else f"{res['verdict']}: {res['reason']}")
    for c in res["changed"]:
        print(f"  changed: {c}")
    for c in res["excluded_changed"]:
        print(f"  excluded (ignored) changed: {c}")
    return {"SAME": 0, "CHANGED": 1}.get(res["verdict"], 2)


def _resolve_suites(a, repo: Path) -> list[Path]:
    if a.suite:
        return [(repo / s).resolve() for s in a.suite]
    return sorted(p for p in (repo / "tools").glob("test_gsd_x_goal*.py"))


def cmd_suites(a) -> int:
    repo = Path(a.repo_root).resolve() if a.repo_root else ROOT
    suites = _resolve_suites(a, repo)
    missing = [str(s) for s in suites if not s.is_file()]
    if missing or not suites:
        print(f"refused: suite file(s) missing: {missing or 'none selected'}")
        return 2
    guards = [Path(g) for g in (a.guard_dir or [DEFAULT_GUARD])]
    out, log_dir = Path(a.out), Path(a.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    before = {str(g): fingerprint(g) for g in guards}
    any_fail = False
    for suite in suites:
        rel = suite.relative_to(repo).as_posix() if suite.is_relative_to(repo) else suite.as_posix()
        for _ in range(a.runs):
            prior = [r for r in _load_rows(out) if r.get("kind") == "run" and r.get("suite") == suite.name]
            k = len(prior) + 1
            log = log_dir / f"{suite.stem}-{k}.log"
            tmp = Path(tempfile.mkdtemp(prefix="gsdx_rb_run_"))
            env = hermetic_env(tmp)
            argv = [sys.executable, str(suite)]
            started = _now()
            t0 = time.perf_counter()
            timed_out, rc = False, None
            with log.open("w", encoding="utf-8", errors="replace") as fh:
                try:
                    rc = subprocess.run(argv, cwd=str(repo), env=env, stdout=fh, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL, timeout=a.timeout).returncode
                except subprocess.TimeoutExpired:
                    timed_out = True
            wall = round(time.perf_counter() - t0, 3)
            summ = parse_summary(log.read_text(encoding="utf-8", errors="replace"))
            row = {"kind": "run", "label": a.label, "suite": suite.name, "path": rel, "argv": argv,
                   "in_copy": False, "run_index": k, "cold": not prior, "started_at": started,
                   "wall_s": wall, "returncode": rc, "timed_out": timed_out,
                   "summary": summ["text"] if summ else None,
                   "passed": summ["passed"] if summ else None, "total": summ["total"] if summ else None,
                   "log": str(log), "free_ram_mb": free_ram_mb(),
                   "hermetic": {k2: env[k2] for k2 in ("HOME", "USERPROFILE", "GSDX_GOALS_ROOT")}}
            _append(out, row)
            ok = rc == 0 and not timed_out and summ is not None and summ["passed"] == summ["total"]
            any_fail |= not ok
            print(f"{'ok  ' if ok else 'FAIL'} {suite.name} run {k}: {wall}s rc={rc} "
                  f"summary={row['summary']}{' TIMEOUT' if timed_out else ''}")
            if not a.keep_temp:
                shutil.rmtree(tmp, ignore_errors=True)
    guard_bad = False
    for g in guards:
        after = fingerprint(g)
        res = compare(before[str(g)], after)
        _append(out, {"kind": "guard", "label": a.label, "dir": str(g), "recorded_at": _now(),
                      "before": before[str(g)], "after": after, "verdict": res["verdict"],
                      "changed": res["changed"], "delta": res["delta"],
                      "excluded_changed": res["excluded_changed"], "reason": res["reason"]})
        print(f"guard {g}: {res['verdict']} changed={res['changed']} excluded_changed={res['excluded_changed']}")
        guard_bad |= res["verdict"] != "SAME"
    if guard_bad:
        return 3
    return 1 if any_fail else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fingerprint")
    f.add_argument("--dir", required=True)
    g = f.add_mutually_exclusive_group(required=True)
    g.add_argument("--out")
    g.add_argument("--against")
    s = sub.add_parser("suites")
    s.add_argument("--out", required=True)
    s.add_argument("--log-dir", required=True)
    s.add_argument("--suite", action="append")
    s.add_argument("--runs", type=int, default=3)
    s.add_argument("--timeout", type=float, default=900)
    s.add_argument("--guard-dir", action="append")
    s.add_argument("--in-copy", action="store_true")
    s.add_argument("--repo-root")
    s.add_argument("--label")
    s.add_argument("--keep-temp", action="store_true")
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return {"fingerprint": cmd_fingerprint, "suites": cmd_suites}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
