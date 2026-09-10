#!/usr/bin/env python3
"""V-gates for constitutional baseline inheritance.

The Phase I audit proved cited owners resolve on disk and said so honestly:
that is presence, not reachability, and this estate has confused the two before.
This gate closes that distinction by walking each obligation up four rungs:

    PRESENT     the artifact is on disk
    REACHABLE   it imports without side effects
    ACTIVATED   the documented entry point is callable
    EFFECTIVE   calling it produces the behaviour the baseline advertises

Only EFFECTIVE counts as inherited. A grader that imports but returns the same
answer for every input has every clause removed and reports the same green.

It also pins the inheritance CHAIN itself, because the obligations are only
inherited while the router keeps saying core.md is always loaded. Delete that
row and every obligation below silently becomes opt-in, with nothing red.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

PASSES = 0
FAILS = 0

# core.md's always-loaded budget was deliberately compressed (-19%, BL-0060).
# An obligation added there must stay lean or it taxes every single session.
CORE_MAX_BYTES = 12000


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def main() -> int:
    core = REPO / "parts" / "core.md"
    router = REPO / "SKILL.md"

    # ---- The chain: obligations are inherited only while this holds --------
    router_text = router.read_text(encoding="utf-8-sig")
    check("V-INHERIT-CHAIN",
          "ALWAYS read" in router_text and "parts/core.md" in router_text,
          "router still declares parts/core.md ALWAYS read")

    core_text = core.read_text(encoding="utf-8-sig")

    # ---- Universal obligations present in the always-loaded surface -------
    check("V-INHERIT-LAW2", "LAW II" in core_text and "PROXY" in core_text.upper(),
          "LAW II architectural-truth obligation is in the always-loaded file")
    check("V-INHERIT-LAW9", "LAW IX" in core_text and "REGRESSION-PROVEN" in core_text,
          "LAW IX graded-completion ladder is in the always-loaded file")
    check("V-INHERIT-CORPUS", "vault/constitution/usea" in core_text,
          "the sealed corpus is discoverable from the always-loaded file")

    # ---- Conditional instantiation must survive ---------------------------
    # Universal in obligation, conditional in domain instantiation. If the
    # domain map disappears, the baseline has become one-size-fits-all, which
    # the constitution explicitly rejects.
    check("V-INHERIT-CONDITIONAL",
          "Domain map" in core_text or "overlays/" in core_text,
          "conditional domain instantiation still present (not universal ceremony)")

    # ---- Context economy: universal effect, non-universal cost ------------
    size = len(core_text.encode("utf-8"))
    check("V-INHERIT-BUDGET", size <= CORE_MAX_BYTES,
          f"always-loaded core is {size} bytes (ceiling {CORE_MAX_BYTES})")

    # ---- Presence -> reachable -> activated -> EFFECTIVE -------------------
    graders = (
        ("modules.done_gate.architectural_truth", "assess_state"),
        ("modules.done_gate.strength_ladder", "assess"),
    )
    for modname, fn in graders:
        short = modname.rsplit(".", 1)[-1]
        path = REPO / Path(modname.replace(".", "/") + ".py")
        check(f"V-REACH-PRESENT-{short}", path.exists(), f"{path.name} on disk")
        try:
            mod = importlib.import_module(modname)
            reachable = True
        except Exception as exc:  # noqa: BLE001
            mod, reachable = None, False
            print(f"       import error: {type(exc).__name__}: {exc}")
        check(f"V-REACH-IMPORT-{short}", reachable, f"{modname} imports")
        callable_ok = bool(mod) and callable(getattr(mod, fn, None))
        check(f"V-REACH-CALLABLE-{short}", callable_ok, f"{fn}() is callable")

    # EFFECTIVE: the graders must actually discriminate, not just answer.
    from modules.done_gate.architectural_truth import assess_state  # noqa: E402
    from modules.done_gate.strength_ladder import assess  # noqa: E402

    bad = assess_state({"http_200": True, "operation_happened_exactly_once": False})
    good = assess_state({"http_200": True, "operation_happened_exactly_once": True})
    check("V-REACH-EFFECTIVE-law2",
          bad.outcome != good.outcome and bad.ceiling and not good.ceiling,
          f"LAW II discriminates: invalid->{bad.outcome}, valid->{good.outcome}")

    over = assess("PRODUCTION-REALITY-VERIFIED", {"spec_exists": True, "artifact_on_disk": False})
    under = assess("IDEA", {})
    check("V-REACH-EFFECTIVE-law9",
          over.outcome != under.outcome,
          f"LAW IX discriminates: overclaim->{over.outcome}, honest->{under.outcome}")

    # ---- Positive control: the sweep can fail -----------------------------
    # A checker that reports green against a subject that should fail is not a
    # checker. Drive the chain assertion against a document that lacks the row.
    synthetic = "# Router with no always-loaded declaration\n| Trigger | Part |\n"
    control_fires = not ("ALWAYS read" in synthetic and "parts/core.md" in synthetic)
    check("V-INHERIT-CONTROL", control_fires,
          "chain predicate returns FALSE on a router missing the declaration")

    print(f"INHERITANCE_PASS={PASSES}/{PASSES + FAILS}  threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
