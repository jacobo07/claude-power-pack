#!/usr/bin/env python3
"""V-gates for the FD-04 cross-model contrast harness (FAITP round 2026-07-14).

The instrument's whole value is that it can REFUSE. A rubric that cannot fail an
empty answer, or that passes a vacuous case, would report portability that was
never measured -- the exact failure the round was opened to end. These gates
observe the refusal, not just the pass.

Hermetic: every write goes to a temp state dir. No model is called (the substrate
runner is exercised by the live run, not by the suite -- a gate that spends money
per invocation is a gate nobody runs).
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_04_contrast import (  # noqa: E402
    controls_hold, load_cases, score)
from modules.fable_distillation.fd_04_prover import (  # noqa: E402
    _latest_by_fp, _proofs_path, _read_jsonl, record_cross_model)
from modules.fable_distillation.fd_07_flywheel import (  # noqa: E402
    _append_jsonl, _deposits_path)

_CASES = _PP_ROOT / "vault" / "fd04" / "contrast_cases.json"
_REPO = str(_PP_ROOT)
_NOW = datetime(2026, 7, 14, tzinfo=timezone.utc)

_passes, _fails = 0, 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS  {gate}  --  {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL  {gate}  --  {diag}")


def _seed(state_dir: Path, fp: str) -> None:
    _append_jsonl(_deposits_path(_REPO, state_dir),
                  {"fingerprint": fp, "claim": "seeded", "ts": _NOW.isoformat()})


def gate_controls_both_poles() -> None:
    """Every live case's rubric must reproduce Fable's own answer AND fail an
    empty one. Either pole unreachable => the rubric measures nothing."""
    cases = load_cases(str(_CASES))
    if not cases:
        return _fail("V-FAITP-CONTROLS", "no cases loaded")
    bad = [c.get("fingerprint") for c in cases if not controls_hold(c)["ok"]]
    if bad:
        return _fail("V-FAITP-CONTROLS", f"controls did not hold: {bad}")
    _ok("V-FAITP-CONTROLS",
        f"{len(cases)} cases: gold=REPRODUCED and empty=FAILED on every rubric")


def gate_vacuous_case_is_error() -> None:
    """An empty conjunction must never read as reproduced (the all([]) trap)."""
    r = score("literally anything", [])
    if r["verdict"] == "ERROR":
        _ok("V-FAITP-VACUOUS", "case with zero required_elements => ERROR, not a pass")
    else:
        _fail("V-FAITP-VACUOUS", f"empty rubric returned {r['verdict']}")


def gate_rubric_is_absolute() -> None:
    """Hitting most elements is PARTIAL, never REPRODUCED -- no ratio threshold."""
    els = [{"id": "a", "patterns": ["alpha"]}, {"id": "b", "patterns": ["beta"]},
           {"id": "c", "patterns": ["gamma"]}]
    partial = score("alpha and beta", els)
    full = score("alpha beta gamma", els)
    none = score("nothing relevant", els)
    if (partial["verdict"] == "PARTIAL" and full["verdict"] == "REPRODUCED"
            and none["verdict"] == "FAILED"):
        _ok("V-FAITP-ABSOLUTE",
            "2/3 => PARTIAL, 3/3 => REPRODUCED, 0/3 => FAILED (all three reachable)")
    else:
        _fail("V-FAITP-ABSOLUTE",
              f"2/3={partial['verdict']} 3/3={full['verdict']} 0/3={none['verdict']}")


def gate_no_reproducer_is_failed(state_dir: Path) -> None:
    """A judgment no cheap substrate reached is FAILED (real residue), not PROVEN."""
    fp = "deadbeefdeadbeef"
    _seed(state_dir, fp)
    rec = record_cross_model(
        _REPO, fp, state_dir=state_dir, now=_NOW,
        results=[{"model": "sonnet", "substrate": "small-model", "verdict": "FAILED"},
                 {"model": "opus", "substrate": "mid-model", "verdict": "PARTIAL"}])
    if rec["verdict"] == "FAILED" and rec["achieved_target"] == "none":
        _ok("V-FAITP-RESIDUE-IS-FAILED",
            "no substrate reproduced => FAILED/none (residue recorded, never PROVEN)")
    else:
        _fail("V-FAITP-RESIDUE-IS-FAILED",
              f"got {rec['verdict']}/{rec.get('achieved_target')}")


def gate_cheapest_substrate_wins(state_dir: Path) -> None:
    """When both reproduce, the capability retires to the CHEAPEST rung."""
    fp = "cafebabecafebabe"
    _seed(state_dir, fp)
    rec = record_cross_model(
        _REPO, fp, state_dir=state_dir, now=_NOW,
        results=[{"model": "sonnet", "substrate": "small-model", "verdict": "REPRODUCED"},
                 {"model": "opus", "substrate": "mid-model", "verdict": "REPRODUCED"}])
    if rec["verdict"] == "PROVEN" and rec["achieved_target"] == "small-model":
        _ok("V-FAITP-CHEAPEST", "sonnet+opus both reproduced => retires to small-model")
    else:
        _fail("V-FAITP-CHEAPEST", f"got {rec.get('achieved_target')}")


def gate_undeposited_is_error(state_dir: Path) -> None:
    """Contrast only covers deposited claims -- an unknown fingerprint is fail-closed."""
    rec = record_cross_model(
        _REPO, "0000000000000000", state_dir=state_dir, now=_NOW,
        results=[{"model": "sonnet", "substrate": "small-model",
                  "verdict": "REPRODUCED"}])
    if rec["verdict"] == "ERROR":
        _ok("V-FAITP-FAILCLOSED", "undeposited fingerprint => ERROR, never PROVEN")
    else:
        _fail("V-FAITP-FAILCLOSED", f"got {rec['verdict']}")


def gate_live_ledger_has_no_unproven() -> None:
    """The round's own done-gate: every live deposit carries a portability verdict."""
    from modules.fable_distillation.fd_07_flywheel import _load_deposits
    deps = {d["fingerprint"] for d in _load_deposits(_REPO) if d.get("fingerprint")}
    latest = _latest_by_fp(_read_jsonl(_proofs_path(_REPO)))
    unjudged = sorted(d for d in deps if d not in latest)
    if not deps:
        return _fail("V-FAITP-LEDGER-CLOSED", "no deposits found -- cannot measure")
    if unjudged:
        return _fail("V-FAITP-LEDGER-CLOSED",
                     f"{len(unjudged)}/{len(deps)} deposits still unjudged: {unjudged}")
    _ok("V-FAITP-LEDGER-CLOSED",
        f"{len(deps)}/{len(deps)} live deposits carry a portability verdict")


def main() -> int:
    print("FAITP contrast harness -- V-gates")
    with tempfile.TemporaryDirectory(prefix="faitp_gates_") as td:
        sd = Path(td)
        gate_controls_both_poles()
        gate_vacuous_case_is_error()
        gate_rubric_is_absolute()
        gate_no_reproducer_is_failed(sd)
        gate_cheapest_substrate_wins(sd)
        gate_undeposited_is_error(sd)
        gate_live_ledger_has_no_unproven()
    total = _passes + _fails
    print(f"FAITP_CONTRAST_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
