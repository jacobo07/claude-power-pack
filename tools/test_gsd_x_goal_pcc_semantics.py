"""Semantics suite for the proof-conserving convergence seam (GSD X, Phase 2, plan 02-03+).

Drives modules/gsd_x/goal/proof.py through the real GoalLog: envelope, payload checks,
the CAS writer, transport, kill switches. Hermetic: HOME, USERPROFILE and GSDX_GOALS_ROOT
are redirected before any engine import; the live store is never touched.

Summary line: GSDX_PCC_SEMANTICS_PASS=n/m  threshold=m/m
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

REAL_HOME = Path.home()
_TMP_HOME = Path(tempfile.mkdtemp(prefix="pcc-sem-home-"))
_TMP_GOALS = Path(tempfile.mkdtemp(prefix="pcc-sem-goals-")) / "goals"
os.environ["HOME"] = str(_TMP_HOME)
os.environ["USERPROFILE"] = str(_TMP_HOME)
os.environ["GSDX_GOALS_ROOT"] = str(_TMP_GOALS)

from modules.gsd_x.goal import contract as gc            # noqa: E402
from modules.gsd_x.goal import log as gl                 # noqa: E402
from modules.gsd_x.goal.log import GoalLog              # noqa: E402

SEM_REPO = "5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e"
PROOF_ABSENT = "RED-first: modules.gsd_x.goal.proof absent"
ENVELOPE_KEYS = {"seq", "type", "ts", "actor", "data", "prev_digest", "digest"}

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
    """A raise is a FAIL line, never an escape (audit G2): the summary line always prints."""
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- survive any gate body
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def load_proof():
    try:
        from modules.gsd_x.goal import proof  # noqa: PLC0415
        return proof
    except ImportError:
        return None


def sample_payloads() -> dict:
    pin = [["tools/gate.py", "9" * 64]]
    cand = "cf1:" + "c" * 64
    return {
        "obligation.contract": {
            "v": 1, "claim_id": "claim-1", "obligation": "ob-one", "combine": "AND",
            "elements": [{"oracle": "unit", "command": "python tools/gate.py", "gate_pin": pin,
                          "causal_paths": ["src"], "env_deps": [], "freshness_class": "unit",
                          "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}]},
        "proof.produced": {
            "v": 1, "claim_id": "claim-1", "candidate": cand, "binding": {"tree_hash": "git:" + "a" * 40},
            "revision": 1, "strength": "exact", "source": {"epoch": "ep-syn", "provider": "gate"}},
        "proof.inherited": {
            "v": 1, "claim_id": "claim-1", "certificate": "cert-1", "candidate": cand,
            "premises": {"claim": "equal", "oracle": "equal", "inputs": "equal", "env": "equal",
                         "gate_pin": "equal", "revision": "equal"}},
        "proof.invalidated": {
            "v": 1, "claim_id": "claim-1", "certificate": "cert-1", "reason": "premise changed"},
    }


def new_goal(name: str = "sem-goal"):
    """(GoalLog with one declared goal, state, base dir to remove)."""
    base = Path(tempfile.mkdtemp(prefix="pcc-sem-"))
    log = GoalLog(SEM_REPO, name, base=base)
    gc.declare(log, "Exercise the PCC seam", ["it works"], [], {"paths": ["src"]}, actor="founder")
    return log, gc.project(log), base


def gate_hermetic():
    home = Path.home()
    root = Path(os.environ["GSDX_GOALS_ROOT"]).resolve()
    ok = (home.resolve() == _TMP_HOME.resolve() and home.resolve() != REAL_HOME.resolve()
          and root.parent.parent == Path(tempfile.gettempdir()).resolve())
    return ok, f"home={home.name} goals_root_under_temp={root.parent.parent == Path(tempfile.gettempdir()).resolve()}"


def gate_envelope():
    proof = load_proof()
    if proof is None:
        return False, PROOF_ABSENT
    log, state, base = new_goal("sem-envelope")
    try:
        data = sample_payloads()["proof.produced"]
        ledger = proof.append_pcc(log, state, proof.PRODUCED, data, "gate-receipt")
        ev = log.read()[-1]
        keys_ok = set(ev.to_dict()) == ENVELOPE_KEYS
        digest_ok = gl.event_digest(ev.to_dict()) == ev.digest
        rec = ledger.produced[-1] if ledger.produced else {}
        rec_ok = len(ledger.produced) == 1 and rec.get("seq") == ev.seq and rec.get("data") == data
        return keys_ok and digest_ok and rec_ok, f"keys={keys_ok} digest={digest_ok} ledger={rec_ok} seq={ev.seq}"
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main() -> int:
    run_gate("V-PCC-HERMETIC-HOME", gate_hermetic)
    run_gate("V-PCC-ENVELOPE", gate_envelope)
    total = passes + fails
    print(f"\nGSDX_PCC_SEMANTICS_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
