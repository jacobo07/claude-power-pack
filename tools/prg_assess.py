#!/usr/bin/env python3
"""prg_assess.py -- run the Production Reality Gate against collected evidence.

    python tools/prg_assess.py --claim PRODUCTION-REALITY-VERIFIED
    python tools/prg_assess.py --claim VERIFIED --evidence-file ev.json
    python tools/prg_assess.py --claim IMPLEMENTED --evidence has_caller=true

WHY THIS FILE EXISTS
--------------------
`modules/done_gate/strength_ladder.py` grades a completion claim against the evidence
actually collected, on thirteen cumulative rungs, and refuses a claim stronger than its
evidence. It is the one mechanism in this estate that can tell "claimed
PRODUCTION-REALITY VERIFIED" apart from "holding unit-test evidence".

It has never run. `vault/liveness/callable_inventory.json:571-573` records `assess` as
reached at PROSE_ONLY, `highest_supported` TEST_ONLY, `Assessment` NEVER -- its only
invoker is a sentence in `commands/usea.md:67`. Meanwhile the reachable gate surface,
`gsd_x/mission/closure.py:116`, is a self-declared string defaulting to "UNPROVEN".

So the estate wrote an honest grader and then graded itself with a string. This is the
caller.

EVIDENCE IS THREE-VALUED AND ABSENCE IS NOT A DEFAULT
-----------------------------------------------------
    true     collected, and positive
    false    collected, and negative
    absent   nobody looked  ->  UNDETERMINED, never a pass

`--probe` measures what this repo can actually measure for the surface_architecture
capability and DELIBERATELY leaves the rest absent. A probe that filled in the rungs it
could not observe would be the laundering this gate exists to refuse.

Exit codes: 0 SUPPORTED, 30 OVERSTATED, 31 UNDETERMINED, 32 LADDER_FAILED, 2 usage.
UNDETERMINED is not folded into OVERSTATED: "your claim outruns your evidence" and
"nobody collected the evidence" are different findings with different fixes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.done_gate.strength_ladder import (  # noqa: E402
    LADDER, LADDER_FAILED, OVERSTATED, SUPPORTED, UNDETERMINED, assess,
)

EXIT = {SUPPORTED: 0, OVERSTATED: 30, UNDETERMINED: 31, LADDER_FAILED: 32}

_PY = sys.executable


def _run(*args: str) -> tuple:
    """(exit_code, stdout). A tool that cannot be run returns (None, reason) so the
    caller records ABSENT rather than False -- 'we could not look' is not 'it failed'."""
    try:
        p = subprocess.run([_PY, *args], cwd=_PP_ROOT, capture_output=True,
                           text=True, timeout=300)
        return p.returncode, p.stdout
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def probe_surface_architecture(fast: bool = False) -> tuple:
    """Measure what this repo can observe. Returns (evidence, notes).

    Every key NOT set here is absent on purpose, and `notes` says why -- an unmeasured
    rung must be traceable to a reason, or the gap looks like an oversight.
    """
    ev: dict = {}
    notes: list = []

    pkg = _PP_ROOT / "modules" / "surface_architecture"
    cmd = _PP_ROOT / "commands" / "surface-architecture.md"
    gate = _PP_ROOT / "tools" / "test_surface_architecture.py"

    ev["spec_exists"] = cmd.is_file()
    ev["artifact_on_disk"] = pkg.is_dir() and (pkg / "resolver.py").is_file()

    # has_caller: a command file that literally names the module path. The reachability
    # scanner resolves a module from exactly this, so the same string is the evidence.
    named = cmd.is_file() and "modules/surface_architecture/resolver.py" in \
        cmd.read_text(encoding="utf-8-sig")
    ev["has_caller"] = named

    if fast:
        notes.append("reachable_from_entrypoint: ABSENT -- --fast skipped the "
                     "reachability scan, which is the only instrument for it")
    else:
        code, out = _run("modules/liveness/reachability.py")
        if code is None:
            notes.append(f"reachable_from_entrypoint: ABSENT -- scan could not run ({out})")
        else:
            orphaned = [ln for ln in out.splitlines()
                        if "surface_architecture" in ln and "ORPHAN" in ln]
            ev["reachable_from_entrypoint"] = not orphaned
            if orphaned:
                notes.append(f"reachable_from_entrypoint: FALSE -- {len(orphaned)} "
                             "orphan row(s) for this package")

    # activation_path_exists: the contract is registered AND a real mission reaches it.
    try:
        from modules.capability_runtime.applicability import (  # noqa: PLC0415
            MissionContext, compile_stack,
        )
        stack = compile_stack(MissionContext(
            description="design the entry surface and first-run for a new product"))
        ev["activation_path_exists"] = "surface_architecture" in stack["activate"]
    except Exception as exc:  # noqa: BLE001 -- inability to ask is not a negative
        notes.append(f"activation_path_exists: ABSENT -- could not evaluate ({exc})")

    code, out = _run(str(gate.relative_to(_PP_ROOT)))
    if code is None:
        notes.append(f"gate: ABSENT -- could not run ({out})")
    else:
        ev["ran_at_least_once"] = True
        ev["assertions_observed"] = code == 0 and "SURFACE_ARCHITECTURE_PASS=" in out
        # The suite drives paired controls (V-SA-*-CONTROL, -DETECTOR-LIVE) whose
        # whole purpose is the red branch, so this rung is observed, not assumed.
        ev["failure_branch_driven"] = "-CONTROL" in out and "-DETECTOR-LIVE" in out
        # The derivative was cut through the real specialization map and the real
        # capability_runtime registry -- two module boundaries, exercised for real.
        ev["integration_boundary_exercised"] = "V-SA-VERTICAL-COMPILES" in out
        ev["regression_case_pinned"] = ("V-SA-VERTICAL-INHERITS-BOUNDARIES" in out
                                        and "V-SA-INVALID-NOT-ABSENT" in out)

    notes.append("production_like_env_exercised: ABSENT -- no production-like "
                 "environment was exercised. Nobody looked; this is not a failure.")
    notes.append("real_boundary_exercised: ABSENT -- no real product consumes this "
                 "decision, so the real boundary has not been crossed.")
    return ev, notes


def _parse_kv(pairs) -> dict:
    out = {}
    for raw in pairs or []:
        if "=" not in raw:
            raise SystemExit(f"--evidence expects key=true|false, got {raw!r}")
        k, v = raw.split("=", 1)
        low = v.strip().lower()
        if low not in ("true", "false"):
            raise SystemExit(f"--evidence value must be true or false, got {v!r}")
        out[k.strip()] = low == "true"
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--claim", required=True,
                    help=f"one of: {', '.join(LADDER)}")
    ap.add_argument("--probe", action="store_true",
                    help="measure the surface_architecture capability in this repo")
    ap.add_argument("--fast", action="store_true",
                    help="with --probe, skip the reachability scan (leaves that rung ABSENT)")
    ap.add_argument("--evidence", action="append", default=[], metavar="KEY=BOOL")
    ap.add_argument("--evidence-file", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    evidence: dict = {}
    notes: list = []
    if args.probe:
        evidence, notes = probe_surface_architecture(fast=args.fast)
    if args.evidence_file:
        try:
            evidence.update(json.loads(
                Path(args.evidence_file).read_text(encoding="utf-8-sig")))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"unreadable evidence file: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            return 2
    evidence.update(_parse_kv(args.evidence))

    result = assess(args.claim, evidence)

    if args.json:
        print(json.dumps({"outcome": result.outcome, "claimed": result.claimed,
                          "highest_supported": result.highest_supported,
                          "missing": result.missing, "unknown": result.unknown,
                          "detail": result.detail, "evidence": evidence,
                          "notes": notes,
                          "exit_code": EXIT.get(result.outcome, 2)}, indent=2))
    else:
        print(result.render())
        if notes:
            print("  --")
            for n in notes:
                print(f"  {n}")
    return EXIT.get(result.outcome, 2)


if __name__ == "__main__":
    raise SystemExit(main())
