"""UCR-CIF W7 -- replay the activation funnel over the real prompt history.

Every stage is evaluated by the PRODUCTION function, in the production
order, against the real `(prompt, cwd)` pair the live hook received. No
stage is modelled, reimplemented or approximated: a funnel built from a
copy of the logic would measure the copy.

    prompt non-empty          sdd_tier.evaluate  guard
    classify_tier(prompt)     spec_gate.classify_tier
    tier >= 2                 sdd_tier.evaluate  guard
    check_spec_gate(...)      spec_gate.check_spec_gate
    action == create_spec     sdd_tier.evaluate  guard   <-- the door
    routing -> owners         disposition_consumer via the gate
    ProactiveSignal emitted   sdd_tier.evaluate

The gate computes `routing` on EVERY branch, including `read_spec`. That
is what makes the silent-useful-match rate measurable at all: the owners
are already known at the moment the signal declines to speak, so this
module can count exactly how much adjudicated authority is computed and
then discarded.

Cost note: `sdd_tier.evaluate` re-derives the tier and re-calls the gate,
so a faithful replay pays for each stage twice. That is deliberate --
reading the intermediate stages off the signal's internals instead would
make the instrument depend on the subject's private shape.
"""
from __future__ import annotations

from pathlib import Path

from modules.ucr_cif.prompt_population import (
    DerivedCase, _bucket, _digest, _SLASH, semantic_class)
from modules.ucr_cif.reach_calibration import repo_group

#: Every distinguishable way a prompt can fail to put an authoritative
#: owner in front of the agent. Named separately because the fix differs
#: per layer -- collapsing them into "recall failure" would point every
#: repair at the trigger vocabulary, which is the one change the brief
#: forbids.
MISS_LAYERS = (
    "none",                        # an owner reached the agent
    "empty_prompt",
    "tier_below_2",                # ordinary small work; correct silence
    "cwd_unreadable",              # cannot judge; NOT a negative
    "knowledge_first_required",    # DFP pre-empts the spec question
    "spec_present_door_shut",      # action=read_spec -> signal declines
    "door_open_no_owner",          # create_spec reached, corpus silent
    "owners_routed_signal_silent",  # computed, never rendered  <-- gap
    "error",
)


def _cwd_state(cwd: str) -> tuple[Path | None, str, str]:
    """Resolve the recorded cwd to a usable path plus its group identity."""
    if not cwd:
        return None, "", ""
    p = Path(cwd)
    try:
        if not p.is_dir():
            return None, "", p.name
    except OSError:
        return None, "", p.name
    gid, _gname = repo_group(p)
    return p, gid, p.name


def replay(text: str, cwd: str, session_id: str,
           timestamp: str) -> DerivedCase:
    """Run one historical prompt through the live activation chain."""
    case = DerivedCase(
        prompt_sha=_digest(text),
        n_chars=len(text),
        length_bucket=_bucket(len(text)),
        date=(timestamp or "")[:10],
        session_sha=_digest(session_id),
        cwd_group_id="",
        cwd_name="",
        semantic_class=semantic_class(text),
        is_slash_command=bool(_SLASH.match(text)),
    )

    path, gid, name = _cwd_state(cwd)
    case.cwd_group_id, case.cwd_name = gid, name

    if not text.strip():
        case.miss_layer = "empty_prompt"
        return case

    try:
        from modules.pp_agents.signals import sdd_tier
        from modules.spec_gate.gate import check_spec_gate, classify_tier
    except Exception as exc:  # noqa: BLE001
        case.error = f"import: {type(exc).__name__}"
        case.miss_layer = "error"
        return case

    try:
        tier = classify_tier(text)
    except Exception as exc:  # noqa: BLE001
        case.error = f"classify_tier: {type(exc).__name__}"
        case.miss_layer = "error"
        return case
    case.tier, case.tier_size, case.tier_signal = (
        tier.tier, tier.size, tier.reason)
    case.reached_tier2 = tier.tier >= 2

    if not case.reached_tier2:
        case.miss_layer = "tier_below_2"
        return case

    if path is None:
        # The recorded cwd no longer exists. This is NOT evidence that the
        # door was shut; it is evidence that we cannot say, and it gets its
        # own layer so it can never be silently counted as a negative.
        case.miss_layer = "cwd_unreadable"
        return case

    try:
        gate = check_spec_gate(text, cwd=path, task_size=tier.size)
    except Exception as exc:  # noqa: BLE001
        case.error = f"check_spec_gate: {type(exc).__name__}"
        case.miss_layer = "error"
        return case

    case.cwd_spec_present = gate.has_spec
    case.gate_action = gate.action
    routed = getattr(gate.routing, "owners", ()) or ()
    case.selector_consulted = gate.routing is not None
    case.owners_routed = [o.owner for o in routed]
    case.precap_owners = list(getattr(gate.routing, "precap_owners", ()) or ())
    case.owner_units = sum(o.units for o in routed)

    try:
        signal = sdd_tier.evaluate(prompt=text, cwd=str(path))
    except Exception as exc:  # noqa: BLE001
        case.error = f"sdd_tier: {type(exc).__name__}"
        case.miss_layer = "error"
        return case

    case.signal_emitted = signal is not None
    if signal is not None:
        case.signal_named_owners = "ADJUDICATED evidence" in (
            signal.advisory or "")

    if case.signal_emitted and case.signal_named_owners:
        case.miss_layer = "none"
    elif case.owners_routed and not case.signal_emitted:
        case.miss_layer = "owners_routed_signal_silent"
    elif gate.action == "knowledge_first_required":
        case.miss_layer = "knowledge_first_required"
    elif gate.action == "read_spec":
        case.miss_layer = "spec_present_door_shut"
    elif gate.action == "create_spec":
        case.miss_layer = "door_open_no_owner"
    else:
        case.miss_layer = "error"
        case.error = f"unmapped action {gate.action!r}"
    return case


__all__ = ["MISS_LAYERS", "replay"]
