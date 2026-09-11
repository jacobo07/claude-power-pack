"""V-PREFLIGHT-* -- the umbrella's host-capacity gate and its verdict ladder.

Drives the REAL verify_spp.py through a real subprocess. Every branch is forced
by a flag rather than by the weather:

  * refusal branches   -- ask for an absurd peak; no host has 100 GB free.
  * the PASSING branch -- ask for 1 MB with a 0 MB reserve. Without a declarable
                          reserve this branch is reachable only on a machine
                          that happens to be idle, which makes it a weather
                          report rather than a gate.

The must-not-fire half is the half that matters. A preflight that refused
everything would satisfy every refusal assertion here and be useless; the
QUALIFIED case is what stops that from scoring.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
UMBRELLA = PP / "tools" / "verify_spp.py"
CHEAP_ROW = "rules-taxonomy"

EXIT_OK = 0
EXIT_MEASURED_FAILURE = 1
EXIT_INCONCLUSIVE = 3
EXIT_PREFLIGHT_REFUSED = 4

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK  ] {gate:<32s} {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate:<32s} {diagnostic}")


def _run(*flags: str, timeout: int = 240) -> tuple[int, str]:
    cp = subprocess.run(
        [sys.executable, str(UMBRELLA), *flags, "--quiet"],
        cwd=str(PP), capture_output=True, text=True,
        timeout=timeout, errors="replace",
    )
    return cp.returncode, (cp.stdout or "") + (cp.stderr or "")


def test_wide_sweep_refuses_when_host_cannot_carry_it() -> None:
    rc, out = _run("--peak-mb", "100000")
    if rc == EXIT_PREFLIGHT_REFUSED and "REFUSED" in out:
        _ok("V-PREFLIGHT-REFUSE", f"exit {rc}, sweep never dispatched")
    else:
        _fail("V-PREFLIGHT-REFUSE",
              f"expected exit {EXIT_PREFLIGHT_REFUSED} + REFUSED, got {rc}")


def test_refusal_names_a_real_alternative() -> None:
    """A refusal that leaves the Owner no move gets overridden by habit."""
    _, out = _run("--peak-mb", "100000")
    named = [s for s in ("--row", "--parallel", "--ignore-preflight") if s in out]
    if len(named) == 3:
        _ok("V-PREFLIGHT-ALTERNATIVE", "refusal names row/parallel/override")
    else:
        _fail("V-PREFLIGHT-ALTERNATIVE", f"only named: {named}")


def test_scoped_run_is_not_refused() -> None:
    """A caller who already scoped down must not be punished for it."""
    rc, out = _run("--row", CHEAP_ROW, "--peak-mb", "100000")
    if rc != EXIT_PREFLIGHT_REFUSED and CHEAP_ROW in out:
        _ok("V-PREFLIGHT-SCOPED", f"row ran, exit {rc} (not a refusal)")
    else:
        _fail("V-PREFLIGHT-SCOPED", f"scoped run was refused: exit {rc}")


def test_override_suppresses_the_refusal_never_the_finding() -> None:
    """The defect this file was written for.

    MEASURED 2026-09-11: --ignore-preflight on a host the gate had just declared
    BLOCKED printed STRICT PASS and exited 0. The flag's own help promised the
    opposite. An override changes what a run DOES, never what it may CLAIM.
    """
    rc, out = _run("--row", CHEAP_ROW, "--peak-mb", "100000", "--ignore-preflight")
    if rc == EXIT_INCONCLUSIVE and "STRICT PASS" not in out and "INCONCLUSIVE" in out:
        _ok("V-PREFLIGHT-OVERRIDE", f"exit {rc}, no pass claimed on a blocked host")
    else:
        _fail("V-PREFLIGHT-OVERRIDE",
              f"exit {rc}; STRICT PASS present: {'STRICT PASS' in out}")


def test_blocked_host_is_named_in_the_verdict() -> None:
    _, out = _run("--row", CHEAP_ROW, "--peak-mb", "100000", "--ignore-preflight")
    if "overridden" in out and "insufficient host memory" in out:
        _ok("V-PREFLIGHT-VERBATIM", "blocker carried verbatim into the verdict")
    else:
        _fail("V-PREFLIGHT-VERBATIM", "the verdict did not name the blocker")


def test_healthy_host_qualifies_and_does_not_refuse() -> None:
    """THE NEGATIVE CONTROL. Without it, a gate that refused everything would
    pass every assertion above and look like a working detector."""
    rc, out = _run("--row", CHEAP_ROW, "--peak-mb", "1", "--reserve-mb", "0")
    qualified = "QUALIFIED" in out and "REFUSED" not in out
    # exit 0 is the expectation; exit 3 is legitimate ONLY if the tree moved
    # under the run, which this repo's own doctrine says must not read as a pass.
    tree_moved = "TREE MOVED" in out
    if qualified and (rc == EXIT_OK or (rc == EXIT_INCONCLUSIVE and tree_moved)):
        why = "exit 0" if rc == EXIT_OK else "exit 3 (tree moved mid-run, correctly)"
        _ok("V-PREFLIGHT-QUALIFIED", f"host QUALIFIED, no refusal, {why}")
    else:
        _fail("V-PREFLIGHT-QUALIFIED",
              f"exit {rc}, QUALIFIED={'QUALIFIED' in out}, "
              f"REFUSED={'REFUSED' in out}, tree_moved={tree_moved}")


def test_preflight_reports_the_tree_before_running() -> None:
    _, out = _run("--row", CHEAP_ROW, "--peak-mb", "1", "--reserve-mb", "0")
    if "dirty path(s) at open" in out or "NOT READABLE" in out:
        _ok("V-PREFLIGHT-BRACKET", "tree state recorded at open")
    else:
        _fail("V-PREFLIGHT-BRACKET", "no bracket reading was taken")


def test_estimate_is_labelled_as_an_estimate() -> None:
    """Requested is not observed. The per-row peak is declared, never measured,
    and a number that cannot say which it is will be read as the stronger one."""
    _, out = _run("--row", CHEAP_ROW, "--peak-mb", "1", "--reserve-mb", "0")
    if "estimated" in out:
        _ok("V-PREFLIGHT-ESTIMATE", "per-row peak printed as an estimate")
    else:
        _fail("V-PREFLIGHT-ESTIMATE", "the estimate was presented unqualified")


def main() -> int:
    print("=" * 70)
    print("test_verify_spp_preflight -- V-PREFLIGHT-*")
    print("=" * 70)
    if not UMBRELLA.is_file():
        print(f"  [FAIL] umbrella missing: {UMBRELLA}")
        return 1
    for fn in (
        test_wide_sweep_refuses_when_host_cannot_carry_it,
        test_refusal_names_a_real_alternative,
        test_scoped_run_is_not_refused,
        test_override_suppresses_the_refusal_never_the_finding,
        test_blocked_host_is_named_in_the_verdict,
        test_healthy_host_qualifies_and_does_not_refuse,
        test_preflight_reports_the_tree_before_running,
        test_estimate_is_labelled_as_an_estimate,
    ):
        try:
            fn()
        except subprocess.TimeoutExpired as exc:
            # An instrument that timed out has not judged its subject. Say so;
            # do not let it read as a product failure.
            _fail(fn.__name__, f"INSTRUMENT TIMEOUT, not a verdict: {exc}")
    total = _passes + _fails
    print("=" * 70)
    print(f"PREFLIGHT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
