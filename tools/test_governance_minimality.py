#!/usr/bin/env python3
"""V-gate for governance minimality (SEIP-EXT-H3).

The load-bearing property is V-MIN-UNDECLARED-IS-UNMEASURABLE. A rule that declares no
forbidden object forbids nothing *as far as this vocabulary can see*, and calling that
REDUNDANT would be an artifact of the vocabulary rather than a fact about the corpus --
the sealed `feedback_zero_cannot_fall` shape, where an unrecognised idiom reads as zero
and zero never falls. The probe must say UNMEASURABLE and name the count.

    python tools/test_governance_minimality.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.hard_rules import residual as R   # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _rule(rid: str, *forbids: str) -> R.FiredRule:
    return R.FiredRule(rule_id=rid, forbids=list(forbids))


def main() -> int:
    print("GOVERNANCE MINIMALITY V-GATE (SEIP-EXT-H3)")

    corpus = [_rule("HR-A", "DEPLOY", "COMMIT"), _rule("HR-B", "DESTRUCTIVE_FS_OP")]

    # --- the vocabulary trap -------------------------------------------------------
    m = R.minimality(_rule("HR-NEW"), corpus)
    if m["verdict"] == R.UNMEASURABLE and "declare" in m["reason"]:
        _ok("V-MIN-UNDECLARED-IS-UNMEASURABLE",
            "a candidate with no declared `forbids` returns UNMEASURABLE, never "
            "REDUNDANT -- an unmeasured zero is not a measured zero")
    else:
        _fail("V-MIN-UNDECLARED-IS-UNMEASURABLE", f"got {m['verdict']}")

    # --- redundant vs constraining --------------------------------------------------
    m = R.minimality(_rule("HR-C", "DEPLOY"), corpus)
    if m["verdict"] == R.REDUNDANT and m["already_forbidden_by"].get("DEPLOY") == ["HR-A"]:
        _ok("V-MIN-REDUNDANT",
            "a rule forbidding only DEPLOY is REDUNDANT and names HR-A as the "
            "incumbent, so the finding is checkable rather than asserted")
    else:
        _fail("V-MIN-REDUNDANT", f"got {m['verdict']} / {m.get('already_forbidden_by')}")

    m = R.minimality(_rule("HR-D", "DEPLOY", "ROTATE_CREDENTIAL"), corpus)
    if m["verdict"] == R.CONSTRAINING and m["adds"] == ["ROTATE_CREDENTIAL"]:
        _ok("V-MIN-CONSTRAINING",
            "one new forbidden move is enough to be CONSTRAINING, and only the "
            "genuinely new move is reported as the addition")
    else:
        _fail("V-MIN-CONSTRAINING", f"got {m['verdict']} adds={m.get('adds')}")

    # --- a rule may not cover itself --------------------------------------------------
    self_rule = _rule("HR-A", "DEPLOY", "COMMIT")
    m = R.minimality(self_rule, corpus)
    if m["verdict"] == R.CONSTRAINING and set(m["adds"]) == {"DEPLOY", "COMMIT"}:
        _ok("V-MIN-NO-SELF-COVER",
            "a rule already in the corpus is excluded from its own comparison; "
            "otherwise every rule would be redundant with itself")
    else:
        _fail("V-MIN-NO-SELF-COVER", f"got {m['verdict']} adds={m.get('adds')}")

    # --- admission and minimality stay separate ----------------------------------------
    g = R.gate_new_rule(_rule("HR-C", "DEPLOY"), corpus)
    if g["admitted"] is True and g["minimality"]["verdict"] == R.REDUNDANT:
        _ok("V-MIN-ADMISSION-DECOUPLED",
            "a REDUNDANT rule is still admitted -- minimality reports, it does not "
            "veto, so no second authority is created")
    else:
        _fail("V-MIN-ADMISSION-DECOUPLED", f"admitted={g.get('admitted')}")

    g = R.gate_new_rule(_rule("HR-BAD", R.RESIDUAL), corpus)
    if g["admitted"] is False and "minimality" not in g:
        _ok("V-MIN-RESIDUAL-STILL-VETOED",
            "the constitutional veto still fires first and short-circuits; adding a "
            "reading did not weaken the one rule that was already enforced")
    else:
        _fail("V-MIN-RESIDUAL-STILL-VETOED", f"got {g}")

    # --- the live corpus -----------------------------------------------------------------
    try:
        live = R.audit_minimality()
    except Exception as e:                                   # noqa: BLE001
        _fail("V-MIN-LIVE-CORPUS", f"raised {type(e).__name__}: {e}")
        live = None

    if live is not None:
        if live["total"] > 0 and live["declared"] + live["undeclared"] == live["total"]:
            _ok("V-MIN-LIVE-CORPUS",
                f"{live['total']} compiled rules reconcile exactly: "
                f"{live['declared']} declared + {live['undeclared']} undeclared; "
                f"verdict {live['verdict']}")
        else:
            _fail("V-MIN-LIVE-CORPUS", f"arithmetic does not close: {live}")

        blob = json.dumps(live)
        if "%" not in blob and "ratio" not in blob and "pct" not in blob:
            _ok("V-MIN-NO-RATIO",
                "the corpus reading carries absolute counts only -- a coverage ratio "
                "would improve by deleting rules")
        else:
            _fail("V-MIN-NO-RATIO", "a ratio-shaped field is present")

    total = _passes + _fails
    print(f"\nMINIMALITY_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
