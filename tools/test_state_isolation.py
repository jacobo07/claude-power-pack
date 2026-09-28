"""V-ISO-*: the long-run / rollover / assimilation suites must not write the REAL ~/.claude.

Origin: d10bd31. test_gsd_long_run armed the context watchdog against the live state dir and
wrote goal-less gsdlr capsules there -- nine in seven minutes -- which /kresume then claimed,
starving real sessions. A grep for Path.home() could not have found it: the path came from a
module-level STATE_DIR default. So this gate observes writes at runtime instead
(tools/state_write_audit/sitecustomize.py, an audit hook every Python child inherits).

Instrument aperture: Python processes only. A node child that writes ~/.claude is NOT seen.

A write is allowed only if DECLARED below with a reason someone can disagree with. The
declaration list may only shrink (stale entries fail).

Usage: python tools/test_state_isolation.py            # judge
       python tools/test_state_isolation.py --measure  # print every write, judge nothing
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT_DIR = REPO / "tools" / "state_write_audit"
REAL_ROOT = Path(os.environ.get("CPP_STATE_AUDIT_REAL_ROOT") or (Path.home() / ".claude"))

SUITES = [
    "test_gsd_mission.py", "test_gsd_mission_freshness.py", "test_gsd_epoch.py",
    "test_gsd_epoch_context_budget.py", "test_gsd_long_run.py", "test_mission_watchdog.py",
    "test_rollover.py", "test_rollover_active_path.py", "test_autonomy_gate.py",
    "test_provider_breaker.py", "test_context_budget.py", "test_fresh_context_tax.py",
    "test_genesis_bridge.py", "test_vendor_provenance.py", "test_task_contract.py",
    "test_source_packet.py", "test_plan_graph_check.py", "test_regression_memory.py",
    "test_batch_drafts.py", "test_review_intake.py", "test_evidence_bundle.py",
    "test_change_impact.py", "test_routing_metrics.py", "test_verified_reuse.py",
    "test_paired_experiment.py", "test_handoff_packet.py", "test_task_ledger_seam.py",
    "test_task_adaptation.py",
]
SUITE_FLOOR = 25

# (suite, path relative to REAL_ROOT with forward slashes, prefix match) -> reason.
DECLARED: dict[tuple[str, str], str] = {}

_passes = 0
_fails = 0


def _ok(gate: str, msg: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS {gate}: {msg}")


def _fail(gate: str, msg: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}: {msg}")


def _env(log: Path, root: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(AUDIT_DIR) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["CPP_STATE_AUDIT_LOG"] = str(log)
    env["CPP_STATE_AUDIT_ROOT"] = str(root)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _read(log: Path) -> list[tuple[str, str]]:
    if not log.exists():
        return []
    out = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            out.append((parts[1], parts[2]))
    return out


def _rel(path: str) -> str:
    try:
        return Path(path).resolve().relative_to(REAL_ROOT.resolve()).as_posix()
    except (ValueError, OSError):
        return Path(path).as_posix()


def run_suite(name: str, work: Path, timeout: int = 900) -> tuple[int | None, list[tuple[str, str]], float]:
    log = work / f"{name}.audit"
    t0 = time.monotonic()
    try:
        proc = subprocess.run([sys.executable, str(REPO / "tools" / name)], cwd=str(REPO),
                              env=_env(log, REAL_ROOT), capture_output=True, timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = None
    return rc, _read(log), time.monotonic() - t0


def controls(work: Path) -> None:
    """The instrument must be able to return the other answer."""
    fake = work / "fake_home_root"
    fake.mkdir()
    log = work / "control.audit"
    code = ("import os,pathlib;r=pathlib.Path(os.environ['CPP_STATE_AUDIT_ROOT']);"
            "(r/'state').mkdir();(r/'state'/'x.json').write_text('1');"
            "os.replace(r/'state'/'x.json', r/'state'/'y.json');"
            "open(r/'state'/'y.json').read()")
    subprocess.run([sys.executable, "-c", code], env=_env(log, fake), check=True)
    # os.replace raises the "os.rename" audit event on this platform; either name is the rename.
    kinds = ["os.rename" if k == "os.replace" else k for k, _ in _read(log)]
    if sorted(kinds) == ["open", "os.mkdir", "os.rename"]:
        _ok("V-ISO-CONTROL-SEES", f"synthetic writes observed {kinds}; the read-only open was not")
    else:
        _fail("V-ISO-CONTROL-SEES", f"instrument did not observe the synthetic writes exactly: {kinds}")
    log2 = work / "control2.audit"
    subprocess.run([sys.executable, "-c", "import subprocess,sys,os,pathlib;"
                    "subprocess.run([sys.executable,'-c',\"import os,pathlib;"
                    "(pathlib.Path(os.environ['CPP_STATE_AUDIT_ROOT'])/'child.txt').write_text('c')\"],check=True)"],
                   env=_env(log2, fake), check=True)
    if any(p.endswith("child.txt") for _, p in _read(log2)):
        _ok("V-ISO-CONTROL-CHILD", "a Python grandchild's write is observed")
    else:
        _fail("V-ISO-CONTROL-CHILD", "a Python grandchild's write was NOT observed")


def main(argv: list[str]) -> int:
    measure = "--measure" in argv
    only = [a for a in argv if a.endswith(".py")]
    suites = only or SUITES
    with tempfile.TemporaryDirectory(prefix="cpp-iso-") as tmp:
        work = Path(tmp)
        controls(work)
        present = [s for s in suites if (REPO / "tools" / s).exists()]
        missing = [s for s in suites if s not in present]
        if missing:
            # A renamed or deleted suite must not silently leave the ratchet's scope.
            _fail("V-ISO-NAMED-SUITES", f"named in scope but not found: {missing}")
        if only or len(present) >= SUITE_FLOOR:
            _ok("V-ISO-FLOOR", f"{len(present)} suites in scope")
        else:
            _fail("V-ISO-FLOOR", f"only {len(present)} suites found, expected >= {SUITE_FLOOR}")
        used: set[tuple[str, str]] = set()
        for s in present:
            rc, writes, secs = run_suite(s, work)
            rels = sorted({_rel(p) for _, p in writes})
            if measure:
                print(f"--- {s} rc={rc} {secs:.0f}s writes={len(rels)}")
                for r in rels:
                    print(f"    {r}")
                continue
            undeclared = []
            for r in rels:
                hit = next((k for k in DECLARED if k[0] == s and r.startswith(k[1])), None)
                if hit:
                    used.add(hit)
                else:
                    undeclared.append(r)
            if undeclared:
                _fail(f"V-ISO-{s}", f"writes the real ~/.claude: {undeclared[:6]}"
                      f"{' ...' if len(undeclared) > 6 else ''}")
            else:
                _ok(f"V-ISO-{s}", f"no undeclared live-state write (rc={rc}, {secs:.0f}s)")
        if not measure and not only:
            stale = [k for k in DECLARED if k not in used]
            if stale:
                _fail("V-ISO-STALE", f"declared writes no longer observed, delete them: {stale}")
            else:
                _ok("V-ISO-STALE", "no stale declaration")
    print(f"ISO_PASS={_passes}/{_passes + _fails}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
