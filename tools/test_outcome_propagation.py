"""V-OUTCOME-* -- a typed verification outcome must survive its wrapper.

The founding observation: verify_spp returned exit 4, printed REFUSED, and
named BLOCKED as the verdict ceiling -- and the estate's own provenance store
recorded that run as `passed=False`, which summary() renders as "last run
failed". A run that measured nothing about the code was described as a
judgement against the code, by the one store built to keep those apart.

The reader was three-valued from the day it was written. The writer took a
bool. That is the whole defect: a projection installed at the boundary where
the distinction was supposed to be preserved.

Two claims are made here and they are NOT the same strength:

  REAL      the BLOCKED path is driven end-to-end through the actual umbrella
            in a real subprocess, because a host that cannot carry the sweep is
            a state this machine can genuinely produce right now.
  SYNTHETIC PASS / FAIL / INCONCLUSIVE are driven through the real store with
            constructed records. Producing a real 84-row PASS requires a host
            that can carry the sweep, which is precisely what is unavailable.

Saying which is which is the point. A gate that presented all six as one
grade of evidence would be making the claim this file exists to refuse.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.cascade_prevention import verification_state as vs  # noqa: E402

PY = sys.executable
UMBRELLA = PP / "tools" / "verify_spp.py"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK  ] {gate:<38s} {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate:<38s} {diagnostic}")


def _run_refused(state_path: Path) -> tuple[int, str]:
    """Drive the REAL umbrella into its refusal branch.

    --peak-mb is inflated rather than the host being starved, because starving
    a real host to test a gate is the instrument consuming the resource it
    measures. The branch taken is identical; only the arithmetic differs.
    """
    env = dict(os.environ)
    env["CLAUDE_PP_VERIFICATION_STATE"] = str(state_path)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [PY, str(UMBRELLA), "--peak-mb", "999999", "--quiet"],
        cwd=str(PP), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=180)
    return proc.returncode, proc.stdout + proc.stderr


def _read_store(state_path: Path) -> dict:
    try:
        return json.loads(state_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


# --- REAL: the state this host can actually produce -------------------------

def test_blocked_survives_the_real_umbrella() -> None:
    with tempfile.TemporaryDirectory() as td:
        sp = Path(td) / "verification.json"
        rc, out = _run_refused(sp)
        if rc != 4 or "REFUSED" not in out:
            _fail("V-OUTCOME-BLOCKED-REAL",
                  f"umbrella did not refuse: rc={rc}")
            return
        last = _read_store(sp).get("last") or {}
        if last.get("outcome") == "BLOCKED":
            _ok("V-OUTCOME-BLOCKED-REAL",
                f"real rc=4 -> store outcome {last['outcome']!r}")
        else:
            _fail("V-OUTCOME-BLOCKED-REAL",
                  f"rc=4 but store recorded {last.get('outcome')!r} "
                  f"(record={last!r})")


def test_a_refusal_overwrites_a_stale_green() -> None:
    """THE DEFECT, PINNED. The refusal branch used to `return` before the
    provenance block, so the previous entry kept vouching for the tree for up
    to an hour -- a sweep the host could not start reading downstream as a
    green that merely had not expired yet."""
    with tempfile.TemporaryDirectory() as td:
        sp = Path(td) / "verification.json"
        os.environ["CLAUDE_PP_VERIFICATION_STATE"] = str(sp)
        try:
            vs.record_verification("verify_spp", True, "84/84 rows")
            if vs.was_verified() is not True:
                _fail("V-OUTCOME-STALE-GREEN", "fixture green never landed")
                return
            rc, _ = _run_refused(sp)
            still_green = vs.was_verified()
            outcome = vs.last_outcome()
        finally:
            os.environ.pop("CLAUDE_PP_VERIFICATION_STATE", None)
    if rc == 4 and still_green is not True and outcome == "BLOCKED":
        _ok("V-OUTCOME-STALE-GREEN",
            "a refusal replaced the standing green with BLOCKED")
    else:
        _fail("V-OUTCOME-STALE-GREEN",
              f"rc={rc} was_verified={still_green!r} outcome={outcome!r} "
              "-- a green survived a run that measured nothing")


# --- SYNTHETIC: states this host cannot legitimately produce today ----------

def _with_store(fn):
    with tempfile.TemporaryDirectory() as td:
        os.environ["CLAUDE_PP_VERIFICATION_STATE"] = str(
            Path(td) / "verification.json")
        try:
            return fn()
        finally:
            os.environ.pop("CLAUDE_PP_VERIFICATION_STATE", None)


def test_inconclusive_is_not_a_failure() -> None:
    def body():
        vs.record_verification("verify_spp", False, "3 rows unmeasured",
                               outcome="INCONCLUSIVE")
        return vs.was_verified(), vs.last_outcome(), vs.summary()["reason"]
    verified, outcome, reason = _with_store(body)
    if verified is None and outcome == "INCONCLUSIVE" and "failed" not in reason:
        _ok("V-OUTCOME-INCONCLUSIVE-NOT-FAIL",
            f"reads None, reason={reason!r}")
    else:
        _fail("V-OUTCOME-INCONCLUSIVE-NOT-FAIL",
              f"verified={verified!r} outcome={outcome!r} reason={reason!r}")


def test_a_real_failure_still_reads_as_a_failure() -> None:
    """THE HALF THAT MATTERS. Everything above widens what counts as "not a
    verdict". A store that answered None to everything would satisfy every
    assertion in this file and would have deleted the ability to report a
    genuine regression."""
    def body():
        vs.record_verification("verify_spp", False, "2 rows failed")
        return vs.was_verified(), vs.last_outcome(), vs.summary()["reason"]
    verified, outcome, reason = _with_store(body)
    if verified is False and outcome == "FAIL" and "failed" in reason:
        _ok("V-OUTCOME-FAIL-CONTROL", "a measured failure still accuses")
    else:
        _fail("V-OUTCOME-FAIL-CONTROL",
              f"verified={verified!r} outcome={outcome!r} -- a real defect "
              "was converted into a shrug")


def test_a_pass_still_vouches() -> None:
    def body():
        vs.record_verification("verify_spp", True, "84/84 rows")
        return vs.was_verified(), vs.last_outcome()
    verified, outcome = _with_store(body)
    if verified is True and outcome == "PASS":
        _ok("V-OUTCOME-PASS-CONTROL", "a green still vouches")
    else:
        _fail("V-OUTCOME-PASS-CONTROL",
              f"verified={verified!r} outcome={outcome!r}")


def test_a_legacy_record_still_reads() -> None:
    """Records written before `outcome` existed carry only `passed`, and were
    only ever written on a real verdict. Dropping them would silently turn
    every pre-change green into 'no record'."""
    def body():
        path = Path(os.environ["CLAUDE_PP_VERIFICATION_STATE"])
        path.parent.mkdir(parents=True, exist_ok=True)
        import time
        path.write_text(json.dumps({"last": {
            "suite": "verify_spp", "passed": True,
            "detail": "legacy", "ts": time.time()}}), encoding="utf-8")
        return vs.was_verified(), vs.last_outcome()
    verified, outcome = _with_store(body)
    if verified is True and outcome == "PASS":
        _ok("V-OUTCOME-LEGACY", "a pre-change record still reads as a pass")
    else:
        _fail("V-OUTCOME-LEGACY",
              f"verified={verified!r} outcome={outcome!r}")


# --- aperture: a new exit code must not default silently --------------------

def test_every_exit_code_has_an_outcome() -> None:
    """Govern the aperture, not today's callers. A fifth exit code added later
    would fall through `.get(rc, INCONCLUSIVE)` and be reported as a run that
    could not judge -- plausible, wrong, and completely silent."""
    src = UMBRELLA.read_text(encoding="utf-8-sig")
    declared = set(re.findall(r"^EXIT_[A-Z_]+ = (\d+)", src, re.M))
    mapped = set(re.findall(r"^\s+EXIT_[A-Z_]+: \"", src, re.M))
    from tools.verify_spp import _OUTCOME_FOR_EXIT
    missing = {int(d) for d in declared} - set(_OUTCOME_FOR_EXIT)
    if not declared:
        _fail("V-OUTCOME-APERTURE",
              "found no EXIT_* declarations -- the instrument is blind")
    elif missing:
        _fail("V-OUTCOME-APERTURE",
              f"exit code(s) {sorted(missing)} have no declared outcome")
    else:
        _ok("V-OUTCOME-APERTURE",
            f"{len(declared)} exit codes declared, {len(mapped)} mapped, "
            "none defaulting")


def main() -> int:
    print("=" * 72)
    print("test_outcome_propagation -- V-OUTCOME-* (1 real path, 4 synthetic)")
    print("=" * 72)
    for fn in (
        test_blocked_survives_the_real_umbrella,
        test_a_refusal_overwrites_a_stale_green,
        test_inconclusive_is_not_a_failure,
        test_a_real_failure_still_reads_as_a_failure,
        test_a_pass_still_vouches,
        test_a_legacy_record_still_reads,
        test_every_exit_code_has_an_outcome,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            # An instrument that crashed judged nothing, and says so louder
            # than any subject finding in the same run.
            _fail(fn.__name__, f"INSTRUMENT FAILED: {type(exc).__name__}: {exc}")
    total = _passes + _fails
    print("=" * 72)
    print(f"OUTCOME_PROPAGATION_PASS={_passes}/{total}  "
          f"threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
