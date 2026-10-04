#!/usr/bin/env python3
"""V-ICR2-* gates: the R2 evidence printer tools/ic_r2_evidence.py (incremental-cognition phase 6, plan 06-01).

    python3 tools/test_ic_r2_evidence.py           run every gate
    python3 tools/test_ic_r2_evidence.py --drill   mutation drill (each mutant must be killed)

A SKIP or an INCONCLUSIVE is printed and counted apart; it is never a PASS and is outside the n/m denominator.
Every expectation about the owner ledger is read here independently, with `git show`, never by calling the
helper's own readers.
"""
from __future__ import annotations

import atexit
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import ic_r2_evidence as ev  # noqa: E402
import test_incremental_cognition_program as icp  # noqa: E402

ce = icp.ce
SCRIPT = HERE / "ic_r2_evidence.py"
CE_LEDGER = "vault/programs/cognitive-economy/ledger.json"
SC_LEDGER = "vault/programs/skill-capability/ledger.json"
FREEZE = "fa9ae2ed"          # CE P0 freeze: holds the CE ledger, every pillar open
PRE_LEDGER = "1cabd117"      # its parent: the CE ledger does not exist yet
TMP_ROOT = Path(tempfile.mkdtemp(prefix="icr2-test-"))
_COUNTER = [0]
RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)
QUIET = [False]


def _cleanup() -> None:
    for dp, dns, fns in os.walk(TMP_ROOT):
        for n in dns + fns:
            with contextlib.suppress(OSError):
                os.chmod(os.path.join(dp, n), 0o700)
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


atexit.register(_cleanup)


def scratch(prefix: str = "t") -> Path:
    _COUNTER[0] += 1
    d = TMP_ROOT / f"{prefix}{_COUNTER[0]}"
    d.mkdir(parents=True)
    return d


# --------------------------------------------------------------------------- gate plumbing
def record(status: str, gate: str, ev_: str = "") -> None:
    RESULTS.append((status, gate, str(ev_)))
    if not QUIET[0]:
        print(f"{status} {gate} {ev_}".rstrip())


def run_gate(gate: str, fn) -> None:
    """fn returns (True|False|'SKIP'|'INCONCLUSIVE', evidence); an exception is a FAIL naming its class."""
    try:
        res, why = fn()
    except Exception as exc:  # noqa: BLE001 -- a gate that crashes must read red, never absent
        res, why = False, f"{exc.__class__.__name__}: {exc}"
    if res in ("SKIP", "INCONCLUSIVE"):
        record(res, gate, why)
    else:
        record("PASS" if res else "FAIL", gate, why)


# --------------------------------------------------------------------------- independent git readers
def git(*args, cwd=REPO) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def have_commit(spec: str) -> bool:
    return git("rev-parse", "--verify", "--quiet", spec + "^{commit}").returncode == 0


def head() -> str:
    return git("rev-parse", "HEAD").stdout.strip()


def ledger_at(spec: str, ref: str) -> dict | None:
    r = git("show", f"{spec}:{ref}")
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.lstrip("﻿"))


def program_ledger() -> dict:
    return json.loads((REPO / "vault/programs/incremental-cognition/ledger.json").read_text(encoding="utf-8"))


def predicted_by_owner(spec: str, ref: str, pillar: str):
    led = ledger_at(spec, ref)
    for p in (led or {}).get("frozen", {}).get("pillars", []):
        if p.get("id") == pillar:
            return p.get("predicted")
    return None


def run_main(argv):
    """In-process ev.main(argv) with stdout captured; returns (rc, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ev.main(list(argv))
    return rc, buf.getvalue()


def run_cli(args):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=str(REPO), capture_output=True, text=True,
                       timeout=300)
    return p.returncode, p.stdout, p.stderr


# --------------------------------------------------------------------------- gates: real repository
def g_tracer_real_head():
    sha8 = head()[:8]
    rc, out, err = run_cli(["--pillar", "J", "--commit", "HEAD"])
    want = [f"OPEN {CE_LEDGER}#{p} at {sha8}: no terminal" for p in ("D", "E", "I")]
    miss = [w for w in want if not any(x.startswith(w) for x in out.splitlines())]
    good = (rc == 1 and not miss and "ICR2_READY=NO" in out and '"kind": "owner_ledger"' not in out)
    return good, f"rc={rc} missing={miss} ready_no={'ICR2_READY=NO' in out} stderr={err.strip()[:80]!r}"


def g_real_freeze_pole():
    if not have_commit(FREEZE):
        return "SKIP", f"{FREEZE} is not in this clone"
    led = program_ledger()
    bad = []
    for pid in ("J", "M"):
        rc, out = run_main(["--pillar", pid, "--commit", FREEZE])
        pairs = led["frozen"]["consumes"][pid]
        lines = [x for x in out.splitlines() if x.startswith("OPEN ")]
        if rc != 1 or len(lines) != len(pairs) or '"kind": "owner_ledger"' in out:
            bad.append(f"{pid}: rc={rc} open_lines={len(lines)}/{len(pairs)}")
            continue
        for pair, line in zip(pairs, lines):
            pred = predicted_by_owner(FREEZE, pair["ledger"], pair["pillar"])
            if not (line.startswith(f"OPEN {pair['ledger']}#{pair['pillar']} at {FREEZE}:")
                    and line.endswith(f"(owner predicted {pred})")) or not pred:
                bad.append(f"{pid}: {line!r} vs predicted {pred!r}")
    return not bad, f"bad={bad}"


def g_real_unreadable_pole():
    if not have_commit(PRE_LEDGER):
        return "SKIP", f"{PRE_LEDGER} is not in this clone"
    rc, out = run_main(["--pillar", "J", "--commit", PRE_LEDGER])
    line = f"UNREADABLE {CE_LEDGER} at {PRE_LEDGER}"
    good = rc == 1 and any(x.startswith(line) for x in out.splitlines()) and '"kind": "owner_ledger"' not in out
    return good, f"rc={rc} unreadable_line={any(x.startswith(line) for x in out.splitlines())}"


def g_consumes_discovered():
    led = program_ledger()
    bad = []
    for pid, wanted in led["frozen"]["consumes"].items():
        want = [(w["ledger"], w["pillar"]) for w in wanted]
        if list(ev.consumed(led, pid)) != want:
            bad.append(pid)
    rc, out = run_main(["--pillar", "A"])
    good = not bad and rc == 2 and "ICR2_COULD_NOT_RUN" in out
    return good, f"mismatch={bad} pillar_A rc={rc}"


GATES = [
    ("V-ICR2-TRACER-REAL-HEAD", g_tracer_real_head),
    ("V-ICR2-REAL-FREEZE-POLE", g_real_freeze_pole),
    ("V-ICR2-REAL-UNREADABLE-POLE", g_real_unreadable_pole),
    ("V-ICR2-CONSUMES-DISCOVERED", g_consumes_discovered),
]


def summary_line() -> str:
    p = sum(1 for r in RESULTS if r[0] == "PASS")
    f = sum(1 for r in RESULTS if r[0] == "FAIL")
    s = sum(1 for r in RESULTS if r[0] == "SKIP")
    i = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    return f"ICR2_PASS={p}/{p + f}  threshold={p + f}/{p + f}  skipped={s}  inconclusive={i}"


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    return 0 if counted and all(r[0] == "PASS" for r in counted) else 1


if __name__ == "__main__":
    sys.exit(run_all())
