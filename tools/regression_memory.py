"""Regression memory (assimilation item 25, genesis-regression-memory -> EXTEND the lessons).

A lesson says "this broke once". A regression record PROVES it: a confirmed failing run of a named
suite, a later independent passing run with the same check identities, and a lifecycle that
reopens the record the moment any of those bytes move -- the test, the artifacts it covered, or
the evidence itself. The lifecycle is the vendored module's, reached through the one bridge;
this file is the runner it deliberately does not have.

CPP suites print V-gate lines, the vendored module reads TAP. The conversion is lossless and
mechanical: every `PASS V-X` / `FAIL V-X` line becomes one TAP test, and the RAW output is kept
beside it and hashed into the run receipt, so the TAP can always be checked against what the
suite actually printed. A suite that crashed before judging (exit != 0 with no FAIL) cannot
become a record: the module refuses an exit code that disagrees with its checks.

Evidence is committed under vault/regressions/<id>/ -- evidence that exists only on one disk
would reopen every record on every fresh clone.

    python tools/regression_memory.py run    --id ID --test tools/test_x.py [--artifact PATH ...]
    python tools/regression_memory.py create --id ID --summary TEXT --run RUN_ID
    python tools/regression_memory.py resolve --id ID --run RUN_ID
    python tools/regression_memory.py reopen-all
exit 0 ok · 3 refused (reason printed) · 2 bridge could not answer · 5 reopen-all reopened something
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.external_assimilation import node_bridge as nb  # noqa: E402

_GATE = re.compile(r"^\s*(PASS|FAIL)\s+(V-[A-Za-z0-9_.-]+)")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def store(root: Path) -> Path:
    return root / "vault" / "regressions"


def to_tap(raw: str) -> tuple[str, int, int]:
    gates = [(m.group(1), m.group(2)) for m in (_GATE.match(line) for line in raw.splitlines()) if m]
    lines = ["TAP version 13"]
    for i, (state, name) in enumerate(gates, 1):
        lines += [f"# Subtest: {name}", f"{'ok' if state == 'PASS' else 'not ok'} {i} - {name}",
                  "  ---", "  duration_ms: 0", "  type: 'test'", "  ..."]
    passed = sum(1 for s, _ in gates if s == "PASS")
    failed = len(gates) - passed
    lines += [f"1..{len(gates)}", f"# tests {len(gates)}", "# suites 0", f"# pass {passed}", f"# fail {failed}",
              "# cancelled 0", "# skipped 0", "# todo 0", "# duration_ms 0"]
    return "\n".join(lines) + "\n", passed, failed


def run(root: Path, rid: str, test: str, artifacts: list[str], timeout: float = 600) -> dict:
    """Execute the suite once and write its receipt. Returns the receipt (with its run id)."""
    run_id = f"r{int(time.time() * 1000)}"
    p = subprocess.run([sys.executable, test], cwd=root, capture_output=True, timeout=timeout)
    raw = p.stdout + p.stderr
    tap, passed, failed = to_tap(raw.decode("utf-8", errors="replace"))
    d = store(root) / rid / "runs" / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "raw.txt").write_bytes(raw)
    (d / "output.tap").write_text(tap, encoding="utf-8", newline="\n")
    scope = sorted(set([test, *artifacts]))
    rel = lambda q: q.relative_to(root).as_posix()  # noqa: E731
    receipt = {"schema": "regression-run-v1", "runId": run_id, "command": "python", "argv": [test],
               "testPath": test, "exitCode": p.returncode, "checkedCount": passed + failed, "failedCount": failed,
               "artifacts": [{"path": a, "sha256": _sha((root / a).read_bytes())} for a in scope],
               "output": {"path": rel(d / "output.tap"), "sha256": _sha((d / "output.tap").read_bytes())},
               "rawOutput": {"path": rel(d / "raw.txt"), "sha256": _sha(raw)}}
    (d / "receipt.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8", newline="\n")
    return receipt


def _receipt_proof(root: Path, rid: str, run_id: str) -> dict:
    p = store(root) / rid / "runs" / run_id / "receipt.json"
    return {"path": p.relative_to(root).as_posix(), "sha256": _sha(p.read_bytes())}


def _record_path(root: Path, rid: str) -> Path:
    return store(root) / rid / "record.json"


def create(root: Path, rid: str, summary: str, run_id: str) -> tuple[bool, str]:
    rec = json.loads((store(root) / rid / "runs" / run_id / "receipt.json").read_text(encoding="utf-8"))
    others = [json.loads(p.read_text(encoding="utf-8")) for p in store(root).glob("*/record.json")]
    r = nb.call("regressionMemory", "createRegression",
                [{"id": rid, "summary": summary, "failure": _receipt_proof(root, rid, run_id),
                  "reproducer": {"command": rec["command"], "argv": rec["argv"], "testPath": rec["testPath"],
                                 "artifacts": [a["path"] for a in rec["artifacts"]]}},
                 {"root": str(root), "records": others}], timeout=60)
    if not r.ok:
        return False, f"{r.outcome}: {r.error}"
    _record_path(root, rid).write_text(json.dumps(r.value, indent=1), encoding="utf-8", newline="\n")
    return True, "open"


def resolve(root: Path, rid: str, run_id: str) -> tuple[bool, str]:
    record = json.loads(_record_path(root, rid).read_text(encoding="utf-8"))
    r = nb.call("regressionMemory", "resolveRegression",
                [record, {"root": str(root), "passing": _receipt_proof(root, rid, run_id)}], timeout=60)
    if not r.ok:
        return False, f"{r.outcome}: {r.error}"
    _record_path(root, rid).write_text(json.dumps(r.value, indent=1), encoding="utf-8", newline="\n")
    return True, "resolved"


def reopen_all(root: Path) -> list[dict]:
    """Re-check every resolved record against today's bytes; a moved byte reopens it."""
    out = []
    for p in sorted(store(root).glob("*/record.json")):
        record = json.loads(p.read_text(encoding="utf-8"))
        r = nb.call("regressionMemory", "reopenRegression", [record, {"root": str(root)}], timeout=60)
        if not r.ok:
            out.append({"id": record.get("id"), "status": "UNJUDGED", "reason": f"{r.outcome}: {r.error}"})
            continue
        nxt = r.value
        reopened = record.get("status") == "resolved" and nxt.get("status") == "open"
        if reopened:
            p.write_text(json.dumps(nxt, indent=1), encoding="utf-8", newline="\n")
        out.append({"id": nxt.get("id"), "status": "REOPENED" if reopened else nxt.get("status"),
                    "reason": (nxt.get("reopenings") or [{}])[-1].get("reason", "") if reopened else ""})
    return out


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--id", required=True)
    r.add_argument("--test", required=True)
    r.add_argument("--artifact", action="append", default=[])
    c = sub.add_parser("create")
    c.add_argument("--id", required=True)
    c.add_argument("--summary", required=True)
    c.add_argument("--run", required=True)
    v = sub.add_parser("resolve")
    v.add_argument("--id", required=True)
    v.add_argument("--run", required=True)
    sub.add_parser("reopen-all")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    if a.cmd == "run":
        rc = run(root, a.id, a.test.replace("\\", "/"), [x.replace("\\", "/") for x in a.artifact])
        print(f"run {rc['runId']} exit={rc['exitCode']} checked={rc['checkedCount']} failed={rc['failedCount']}")
        return 0
    if a.cmd in ("create", "resolve"):
        ok, msg = (create(root, a.id, a.summary, a.run) if a.cmd == "create" else resolve(root, a.id, a.run))
        print(("OK " if ok else "REFUSED ") + msg)
        return 0 if ok else (2 if msg.startswith(("BRIDGE_FAILED", "UNREADABLE")) else 3)
    rows = reopen_all(root)
    for x in rows:
        print(f"{x['status']:9} {x['id']}  {x['reason']}")
    return 5 if any(x["status"] == "REOPENED" for x in rows) else (2 if any(x["status"] == "UNJUDGED" for x in rows) else 0)


if __name__ == "__main__":
    sys.exit(main())
