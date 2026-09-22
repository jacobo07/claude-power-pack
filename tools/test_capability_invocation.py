#!/usr/bin/env python3
"""V-gates for the capability invocation seam (Mission 002, Slice 1).

WHAT THIS GATE CLAIMS, AND WHAT IT DOES NOT
-------------------------------------------
It claims the seam is CALLABLE and that it preserves the capability's own
result semantics. It does NOT claim anything is CONSUMED -- no downstream stage
is exercised here, and a gate that implied otherwise would be collapsing the
two claims the seam exists to keep apart.

The division of labour is deliberate:

  * `test_surface_architecture.py` owns "input X produces outcome Y". Pinning
    that again here would be a looser duplicate of a stricter gate, which can
    disarm the stricter one's mutation drill while every suite stays green.
  * THIS gate owns "the seam entered the capability, carried its answer back
    without renaming it, and kept every failure mode distinguishable".

So the four outcome classes are driven through SYNTHETIC capabilities whose
answer is known by construction. That is not a weaker test of the seam -- it is
the only way to drive REQUIRE_APPROVAL and UNDETERMINED deterministically
without encoding the resolver's policy into a second place.

PROVING ENTRY, NOT PLAUSIBILITY
-------------------------------
A capability that was never called and one that was called and abstained leave
similar-looking records. Every positive case here therefore counts CALLS on a
sentinel, so "it was entered" is a measurement rather than an inference from a
plausible return value.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CapabilityContract, load_contracts)
from modules.capability_runtime.invocation import (  # noqa: E402
    Authority, InvocationError, Status, invoke, resolve_entrypoint)

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {gate}: {diag}")


# --------------------------------------------------------------------------
# Synthetic capabilities. Module-level so a dotted entrypoint can find them.
# --------------------------------------------------------------------------

CALLS: list = []


@dataclass
class _Decision:
    """Shaped like the real Decision: an `outcome` and an `exit_code`."""

    outcome: str
    exit_code: int

    def to_dict(self) -> dict:
        return {"outcome": self.outcome, "exit_code": self.exit_code}


_VOCAB = {
    "RECOMMEND": 0,
    "ABSTAIN": 20,
    "REQUIRE_APPROVAL": 21,
    "UNDETERMINED": 22,
}


def cap_recommend(payload):
    CALLS.append(("recommend", payload))
    return _Decision("RECOMMEND", 0)


def cap_abstain(payload):
    CALLS.append(("abstain", payload))
    return _Decision("ABSTAIN", 20)


def cap_require_approval(payload):
    CALLS.append(("require_approval", payload))
    return _Decision("REQUIRE_APPROVAL", 21)


def cap_undetermined(payload):
    CALLS.append(("undetermined", payload))
    return _Decision("UNDETERMINED", 22)


def cap_explodes(payload):
    CALLS.append(("explodes", payload))
    raise RuntimeError("capability blew up on purpose")


_SELF = "tools.test_capability_invocation"


def _contract(cid: str, entrypoint: str = "", authority: str = "decision",
              budget_ms: int = 0) -> CapabilityContract:
    # triggers/consumers are non-optional: HR-APA-006 refuses a contract that
    # declares neither, on the grounds that its activation would be invisible.
    # The estate had already encoded this mission's own thesis as a validator.
    return CapabilityContract(
        id=cid, name=cid, owner="gate",
        triggers=["synthetic gate trigger"], consumers=["the gate itself"],
        entrypoint=entrypoint, authority=authority, budget_ms=budget_ms)


# --------------------------------------------------------------------------
def gate_not_callable() -> None:
    """No entrypoint is a DEFINED outcome, not an error and not a crash."""
    before = len(CALLS)
    rec = invoke(_contract("no_entry"), {"x": 1}, requested_by="gate")
    if rec.status is not Status.NOT_CALLABLE:
        _fail("V-INV-NOT-CALLABLE", f"status={rec.status}")
    elif rec.invoked:
        _fail("V-INV-NOT-CALLABLE", "record claims invoked")
    elif len(CALLS) != before:
        _fail("V-INV-NOT-CALLABLE", "something was entered")
    else:
        _ok("V-INV-NOT-CALLABLE",
            "no entrypoint -> not_callable, nothing entered, no raise")


def gate_unresolvable_is_not_not_callable() -> None:
    """A BROKEN entrypoint must not read as an ABSENT one.

    Collapsing these hides a contract defect behind a legitimate state: one
    means "this capability is advisory by design", the other means "somebody
    renamed a function and nothing noticed".
    """
    rec = invoke(_contract("bad", f"{_SELF}:does_not_exist"), {})
    if rec.status is not Status.UNRESOLVABLE:
        _fail("V-INV-UNRESOLVABLE", f"status={rec.status}")
    elif "does_not_exist" not in rec.error:
        _fail("V-INV-UNRESOLVABLE", f"error does not name the symbol: {rec.error}")
    else:
        _ok("V-INV-UNRESOLVABLE",
            "broken entrypoint -> unresolvable, distinct from not_callable")


def gate_four_outcomes_distinct() -> None:
    """All four classes survive the seam, verbatim, and none collapses."""
    seen = {}
    for name, fn in (("RECOMMEND", "cap_recommend"),
                     ("ABSTAIN", "cap_abstain"),
                     ("REQUIRE_APPROVAL", "cap_require_approval"),
                     ("UNDETERMINED", "cap_undetermined")):
        before = len(CALLS)
        rec = invoke(_contract(name.lower(), f"{_SELF}:{fn}"), {"k": name})
        if rec.status is not Status.INVOKED:
            _fail("V-INV-FOUR-OUTCOMES", f"{name}: status={rec.status}")
            return
        if len(CALLS) != before + 1:
            _fail("V-INV-FOUR-OUTCOMES", f"{name}: capability not entered")
            return
        seen[name] = (rec.outcome, rec.exit_code)

    wrong = {k: v for k, v in seen.items()
             if v[0] != k or v[1] != _VOCAB[k]}
    if wrong:
        _fail("V-INV-FOUR-OUTCOMES", f"renamed or recoded: {wrong}")
    elif len({v[0] for v in seen.values()}) != 4:
        _fail("V-INV-FOUR-OUTCOMES", "outcomes collapsed into fewer than four")
    else:
        _ok("V-INV-FOUR-OUTCOMES",
            "RECOMMEND/ABSTAIN/REQUIRE_APPROVAL/UNDETERMINED all verbatim, "
            "exit codes 0/20/21/22 preserved")


def gate_status_and_outcome_are_independent() -> None:
    """"never called" and "called, abstained" must be tellable apart.

    This is the axis that a single-field design destroys, and it is the whole
    reason `status` and `outcome` are separate on the record.
    """
    never = invoke(_contract("never"), {})
    called = invoke(_contract("abst", f"{_SELF}:cap_abstain"), {})
    if never.status is called.status:
        _fail("V-INV-STATUS-AXIS", "same status for never-called and abstained")
    elif never.invoked or not called.invoked:
        _fail("V-INV-STATUS-AXIS",
              f"invoked flags wrong: {never.invoked} / {called.invoked}")
    elif never.outcome != "":
        _fail("V-INV-STATUS-AXIS",
              f"uninvoked record carries an outcome: {never.outcome!r}")
    else:
        _ok("V-INV-STATUS-AXIS",
            "not_callable(outcome='') vs invoked(outcome='ABSTAIN') -- "
            "absence of a call never reads as a decision")


def gate_failure_isolated() -> None:
    """A capability that raises must not propagate into its caller."""
    before = len(CALLS)
    try:
        rec = invoke(_contract("boom", f"{_SELF}:cap_explodes"), {})
    except Exception as e:  # noqa: BLE001
        _fail("V-INV-FAILURE-ISOLATED", f"exception escaped the seam: {e!r}")
        return
    if rec.status is not Status.FAILED:
        _fail("V-INV-FAILURE-ISOLATED", f"status={rec.status}")
    elif len(CALLS) != before + 1:
        _fail("V-INV-FAILURE-ISOLATED", "capability was never entered")
    elif "RuntimeError" not in rec.error:
        _fail("V-INV-FAILURE-ISOLATED", f"error type lost: {rec.error!r}")
    else:
        _ok("V-INV-FAILURE-ISOLATED",
            "raise -> status=failed, error preserved, caller unharmed")


def gate_authority_refused_before_entry() -> None:
    """Authority is checked BEFORE the call -- a reply cannot un-mutate."""
    before = len(CALLS)
    rec = invoke(_contract("dec", f"{_SELF}:cap_recommend", authority="decision"),
                 {}, granted_authority=Authority.MUTATING.value)
    if rec.status is not Status.REFUSED_BY_AUTHORITY:
        _fail("V-INV-AUTHORITY", f"status={rec.status}")
    elif len(CALLS) != before:
        _fail("V-INV-AUTHORITY", "capability was ENTERED despite refusal")
    else:
        _ok("V-INV-AUTHORITY",
            "mutating asked of a decision capability -> refused, not entered")

    # Control: the same call within declared authority must succeed, or the
    # gate above is satisfied by a seam that refuses everything.
    before = len(CALLS)
    okrec = invoke(_contract("dec2", f"{_SELF}:cap_recommend", authority="decision"),
                   {}, granted_authority=Authority.DECISION.value)
    if okrec.status is Status.INVOKED and len(CALLS) == before + 1:
        _ok("V-INV-AUTHORITY-CONTROL",
            "decision asked of a decision capability -> invoked")
    else:
        _fail("V-INV-AUTHORITY-CONTROL",
              f"in-authority call did not run: {okrec.status}")


def gate_kill_switch() -> None:
    """The env var the contract NAMES must actually stop the call."""
    before = len(CALLS)
    os.environ["CPP_CAPABILITY_INVOKE"] = "off"
    try:
        rec = invoke(_contract("k", f"{_SELF}:cap_recommend"), {})
    finally:
        os.environ.pop("CPP_CAPABILITY_INVOKE", None)
    if rec.status is not Status.NOT_CALLABLE:
        _fail("V-INV-KILLSWITCH", f"status={rec.status}")
    elif len(CALLS) != before:
        _fail("V-INV-KILLSWITCH", "capability ran with the kill switch off")
    elif "kill switch" not in rec.error:
        _fail("V-INV-KILLSWITCH", f"reason not recorded: {rec.error!r}")
    else:
        _ok("V-INV-KILLSWITCH",
            "CPP_CAPABILITY_INVOKE=off -> not entered, reason recorded")

    # Control: with the switch absent the same call runs.
    before = len(CALLS)
    rec2 = invoke(_contract("k2", f"{_SELF}:cap_recommend"), {})
    if rec2.status is Status.INVOKED and len(CALLS) == before + 1:
        _ok("V-INV-KILLSWITCH-CONTROL", "switch absent -> invoked")
    else:
        _fail("V-INV-KILLSWITCH-CONTROL", f"status={rec2.status}")


def gate_real_contract_is_callable() -> None:
    """THE end-to-end claim: the on-disk contract reaches the real resolver.

    Loaded from the real contracts dir, so a JSON key dropped by `from_dict`
    (which filters to known dataclass fields) fails here rather than silently.
    """
    contracts = [c for c in load_contracts() if c.id == "surface_architecture"]
    if not contracts:
        _fail("V-INV-REAL-CONTRACT", "surface_architecture contract not loaded")
        return
    c = contracts[0]
    if not c.entrypoint:
        _fail("V-INV-REAL-CONTRACT",
              "contract carries no entrypoint -- DISCOVERABLE only")
        return
    _ok("V-INV-REAL-CONTRACT-ENTRYPOINT",
        f"contract declares entrypoint={c.entrypoint!r} authority={c.authority!r}")

    try:
        fn = resolve_entrypoint(c.entrypoint)
    except InvocationError as e:
        _fail("V-INV-REAL-CONTRACT", f"entrypoint does not resolve: {e}")
        return

    from modules.surface_architecture.context import SurfaceContext
    ctx = SurfaceContext(source="V-INV-REAL-CONTRACT")
    rec = invoke(c, ctx, requested_by="test_capability_invocation",
                 selected_because="gate drives the real contract",
                 input_provenance="SurfaceContext(all-unknown)",
                 granted_authority="decision")

    if rec.status is not Status.INVOKED:
        _fail("V-INV-REAL-CONTRACT",
              f"real resolver not invoked: status={rec.status} err={rec.error}")
        return
    if rec.outcome not in _VOCAB:
        _fail("V-INV-REAL-CONTRACT",
              f"outcome outside the declared vocabulary: {rec.outcome!r}")
        return
    _ok("V-INV-REAL-CONTRACT",
        f"real resolver invoked via contract -> outcome={rec.outcome} "
        f"exit={rec.exit_code} in {rec.elapsed_ms:.1f}ms "
        f"(fn={fn.__module__}.{fn.__name__})")

    # An all-unknown context must NOT yield a confident recommendation. Absence
    # of evidence is not evidence for a topology.
    if rec.outcome == "RECOMMEND":
        _fail("V-INV-REAL-CONTRACT-ABSENCE",
              "all-unknown context produced RECOMMEND")
    else:
        _ok("V-INV-REAL-CONTRACT-ABSENCE",
            f"all-unknown context -> {rec.outcome}, never a confident winner")


def gate_record_is_reconstructable() -> None:
    """One decision must be reconstructable from its record alone."""
    rec = invoke(_contract("prov", f"{_SELF}:cap_recommend"), {"p": 1},
                 requested_by="mission-002",
                 selected_because="applicability said MANDATORY",
                 input_provenance="fixture://prov")
    d = rec.to_dict()
    need = ("capability_id", "status", "requested_by", "selected_because",
            "entrypoint", "authority", "input_provenance", "outcome",
            "exit_code", "elapsed_ms", "at")
    missing = [k for k in need if k not in d or d[k] in ("", None)]
    if missing:
        _fail("V-INV-PROVENANCE", f"record cannot answer: {missing}")
    else:
        _ok("V-INV-PROVENANCE",
            "who/why/entrypoint/authority/input/outcome/when all present")


def main() -> int:
    print("V-INV -- capability invocation seam")

    # THE COUNTER MUST LIVE IN THE MODULE THE ENTRYPOINT ACTUALLY RESOLVES TO.
    # Run as a script this file is `__main__`, and `resolve_entrypoint` imports
    # it again under its dotted name -- so the process holds TWO module objects
    # with two separate `CALLS` lists. The sentinels append to the imported
    # copy's list while the assertions read `__main__`'s, which reports
    # "capability not entered" for a call that demonstrably happened
    # (status=INVOKED, in 0.0ms, with the right outcome).
    #
    # That is an INSTRUMENT failure, not a product failure, and the distinction
    # is the whole point: read the wrong way it looks like the seam never calls
    # anything, which is exactly the defect this gate exists to detect. Same
    # family as the dynamic-import trap recorded as S7 in the UACF
    # adjudication -- a module loaded under two names is two modules.
    # Binding both names to ONE list object is what makes the counter mean
    # anything at all.
    import importlib
    globals()["CALLS"] = importlib.import_module(_SELF).CALLS

    gate_not_callable()
    gate_unresolvable_is_not_not_callable()
    gate_four_outcomes_distinct()
    gate_status_and_outcome_are_independent()
    gate_failure_isolated()
    gate_authority_refused_before_entry()
    gate_kill_switch()
    gate_real_contract_is_callable()
    gate_record_is_reconstructable()
    total = _PASS + _FAIL
    print(f"INV_PASS={_PASS}/{total}  threshold={total}/{total}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
