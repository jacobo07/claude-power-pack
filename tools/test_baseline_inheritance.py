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


class _ProbeDecision:
    """Shaped like any capability result: an outcome and an exit code."""

    outcome = "PROBE_OK"
    exit_code = 0

    def to_dict(self) -> dict:
        return {"outcome": self.outcome, "exit_code": self.exit_code}


def _probe_adapter(artifact):
    """Generic adapter protocol: (payload | None, reason).

    Module-level because the contract reaches these by DOTTED PATH. Note that
    this file is `__main__` when run as a script and is imported again under its
    dotted name, so these functions execute in a second module object -- which
    is harmless here only because the assertions read the returned RECORD and
    never a counter living in one copy's globals.
    """
    title = str((artifact or {}).get("title", "")).lower()
    if "inherit-probe" in title:
        return {"probe": True}, "synthetic capability claims this artifact"
    return None, "synthetic capability does not claim this artifact"


def _probe_capability(payload):
    return _ProbeDecision()


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

    # ---- UACF construction obligations: inherited, or merely available? ----
    #
    # WHAT IS *NOT* ASSERTED HERE, AND WHY.
    #
    # `test_capability_consumption.py` already owns "an applicable PRD gets a
    # decision and a non-applicable one does not", behaviourally, and its
    # mutation drill (sever the call in parse() -> 5/11) is STRICTER than any
    # source-level chain check would be. Re-asserting it here would be a looser
    # duplicate, and a looser duplicate can satisfy the stricter gate's subject
    # and disarm its drill while every suite stays green.
    #
    # So this section asserts only what makes the mechanism INHERITANCE rather
    # than an integration -- two properties nothing else covers:
    #
    #   UNNAMED     the construction stage names no capability, so nobody has
    #               to remember one by name;
    #   GENERIC     a capability the stage has never heard of is picked up from
    #               its declared fields alone, with zero edits to the stage.
    #
    # Together with the consumption gate's behavioural proof that the stage
    # calls the boundary at all, those compose into inheritance.
    import json
    import tempfile

    from modules.capability_runtime.enrichment import (  # noqa: E402
        decisions_for_artifact)

    enrich_path = REPO / "modules" / "capability_runtime" / "enrichment.py"
    check("V-INHERIT-UACF-PRESENT", enrich_path.exists(),
          "the generic enrichment boundary is on disk")
    check("V-INHERIT-UACF-CALLABLE", callable(decisions_for_artifact),
          "decisions_for_artifact() is callable")

    # UNNAMED. The PRD stage must not mention any capability. If it does, the
    # baseline is inherited only by whoever remembered to write the name.
    stage_src = (REPO / "modules" / "karimo-harness" / "prd_parser.py").read_text(
        encoding="utf-8-sig")
    named = [w for w in ("surface_architecture", "UACF", "signup") if w in stage_src]
    check("V-INHERIT-UACF-UNNAMED", not named,
          f"construction stage names no capability (found: {named or 'none'})")

    # GENERIC / EFFECTIVE. A synthetic capability the estate has never seen is
    # inherited from its contract alone. This is the rung that separates a
    # generic boundary from one capability wired into one subsystem: nothing in
    # enrichment.py or prd_parser.py knows this contract exists.
    #
    # Written to a TEMP contracts dir, never the real one -- another session is
    # live in this tree, and a gate that drops files into a shared registry is
    # a gate that breaks somebody else's run.
    probe_id = "inherit_probe_synthetic"
    self_mod = "tools.test_baseline_inheritance"
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / f"{probe_id}.json").write_text(json.dumps({
            "id": probe_id,
            "name": "synthetic inheritance probe",
            "owner": "test_baseline_inheritance",
            "triggers": ["a synthetic artifact the estate has never seen"],
            "consumers": ["this gate"],
            "inputs": ["prd_baseline"],
            "entrypoint": f"{self_mod}:_probe_capability",
            "adapter": f"{self_mod}:_probe_adapter",
            "authority": "decision",
        }), encoding="utf-8")

        claimed = decisions_for_artifact(
            "prd_baseline", {"title": "PRD: inherit-probe subject"},
            contracts_dir=Path(tmp))
        ignored = decisions_for_artifact(
            "prd_baseline", {"title": "PRD: something else entirely"},
            contracts_dir=Path(tmp))

    got = (claimed.get(probe_id) or {})
    skipped = (ignored.get(probe_id) or {})
    check("V-INHERIT-UACF-EFFECTIVE",
          got.get("status") == "invoked" and got.get("outcome") == "PROBE_OK"
          and skipped.get("status") == "not_callable",
          f"an unknown capability is inherited from its contract alone "
          f"(claimed->{got.get('status')}, unclaimed->{skipped.get('status')})")

    # ---- Positive control: the sweep can fail -----------------------------
    # A checker that reports green against a subject that should fail is not a
    # checker. Drive the chain assertion against a document that lacks the row.
    synthetic = "# Router with no always-loaded declaration\n| Trigger | Part |\n"
    control_fires = not ("ALWAYS read" in synthetic and "parts/core.md" in synthetic)
    check("V-INHERIT-CONTROL", control_fires,
          "chain predicate returns FALSE on a router missing the declaration")

    # Same discipline for the UNNAMED predicate. Driven against a SYNTHETIC
    # source rather than by editing the real stage: a drill that mutates a live
    # file must put it back, and a restore that goes wrong costs more than the
    # drill is worth. It cannot decay either -- it depends on no real file
    # continuing to name, or not name, a capability.
    dirty_stage = "baseline = schema_map(...)\nfrom modules.surface_architecture import x\n"
    named_control = [w for w in ("surface_architecture", "UACF", "signup")
                     if w in dirty_stage]
    check("V-INHERIT-UACF-UNNAMED-CONTROL", bool(named_control),
          f"unnamed predicate returns FALSE on a stage that names one "
          f"(caught: {named_control})")

    print(f"INHERITANCE_PASS={PASSES}/{PASSES + FAILS}  threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
