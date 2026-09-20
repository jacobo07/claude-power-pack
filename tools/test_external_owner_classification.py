#!/usr/bin/env python3
"""External-owner classification gates -- UCR-CIF W4.

Two capabilities sat UNKNOWN for a reason the estate had already rejected one
layer down. `retirement.py` deliberately separates EXTERNAL from UNEVALUABLE --
"this repo cannot measure it" is a permanent structural fact, "we owe a
measurement" is a gap -- and W3's migration mapped both to UNKNOWN, re-merging
them.

The classification these gates pin is a deduction, not a promotion:

    nothing in this repository can retire the capability
    only an Owner attestation about a NAMED external party could
    no such attestation exists
    -> it is still the current authority

The load-bearing word is NAMED. An external condition whose owner nobody has
written down leaves "who decides this?" unanswered, and that stays UNKNOWN.
That branch is driven by a SYNTHETIC subject, never by whichever real entry
happens to be incomplete today -- a drill pinned to a real defect has an
interest in the defect surviving, and decays the moment it is fixed.

The other half is the one a future reader is most likely to get wrong:
`lifecycle=active` on an externally-owned capability is a claim about
AUTHORITY. It is not a claim that the pricing market is reachable or that a
language server is installed. EXTERNAL != AVAILABLE, and
V-EXT-AUTHORITY-NOT-AVAILABILITY is what stops the two collapsing.

Run: python tools/test_external_owner_classification.py   (exit 0 = all green)
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.capability_runtime import retirement as R  # noqa: E402
from modules.capability_runtime.contract import from_dict  # noqa: E402
from modules.capability_runtime.lifecycle import Lifecycle, load_log  # noqa: E402
from tools import capability_lifecycle_migrate as M  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"[PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {diagnostic}")


def _synthetic(cid: str):
    """A contract that exists only inside this test, with an external-shaped
    retirement condition and no lifecycle."""
    return from_dict({
        "id": cid,
        "name": f"synthetic {cid}",
        "owner": "test",
        "triggers": ["a synthetic trigger so the contract validates"],
        "consumers": ["this test, and nothing else"],
        "retirement_condition": "a fact outside this repository changes",
    })


def _with_external(cid: str, owner: str):
    """Temporarily register a synthetic external condition."""
    class _Ctx:
        def __enter__(self):
            R.EXTERNAL_CONDITIONS[cid] = R.ExternalOwner(
                owner=owner, why="synthetic condition for the drill")

        def __exit__(self, *a):
            R.EXTERNAL_CONDITIONS.pop(cid, None)
            return False
    return _Ctx()


def _row(p: dict, cid: str):
    for bucket in ("to_write", "stays_unknown", "already_classified",
                   "needs_owner_decision"):
        for r in p[bucket]:
            if r["id"] == cid:
                return bucket, r
    return None, None


# --------------------------------------------------------------------------- #
def t_real_externals_are_named() -> None:
    gate = "V-EXT-OWNER-NAMED"
    unnamed = [k for k in R.EXTERNAL_CONDITIONS if not R.external_owner(k)]
    if not R.EXTERNAL_CONDITIONS:
        _fail(gate, "EXTERNAL_CONDITIONS is empty -- the registry sweep may "
                    "have stopped seeing entries")
        return
    if unnamed:
        _fail(gate, f"external conditions with no named owner: {unnamed}")
        return
    _ok(gate, f"{len(R.EXTERNAL_CONDITIONS)} external condition(s), every one "
              "naming the party whose facts decide it")


def t_named_owner_classifies() -> None:
    gate = "V-EXT-NAMED-OWNER-CLASSIFIES"
    p = M.plan()
    ids = {r["id"] for r in p["to_write"]}
    ext = {k for k in R.EXTERNAL_CONDITIONS if R.external_owner(k)}
    missing = ext - ids - {r["id"] for r in p["already_classified"]}
    if missing:
        _fail(gate, f"named-owner externals not classified: {sorted(missing)}")
        return
    _ok(gate, f"every named-owner external is classified: {sorted(ext)}")


def t_unnamed_owner_stays_unknown() -> None:
    """The fail-closed default, on a synthetic subject so it survives the day
    every real entry is named."""
    gate = "V-EXT-UNNAMED-STAYS-UNKNOWN"
    cid = "zzyzx-synthetic-unowned"
    with _with_external(cid, owner=""):
        p = M.plan(contracts=[_synthetic(cid)])
        bucket, row = _row(p, cid)
    if bucket == "stays_unknown" and "owner" in (row or {}).get("why", ""):
        _ok(gate, f"external with an empty owner -> {bucket}; "
                  f"why names the gap: {row['why'][:70]}…")
    else:
        _fail(gate, f"bucket={bucket} why={(row or {}).get('why')}")


def t_named_owner_is_not_hardcoded() -> None:
    """The green pole of the gate above. Without it, a classifier that refused
    everything would pass the red branch and look like working machinery."""
    gate = "V-EXT-MACHINERY-NOT-TWO-IDS"
    cid = "zzyzx-synthetic-owned"
    with _with_external(cid, owner="a third-party registry nobody here owns"):
        p = M.plan(contracts=[_synthetic(cid)])
        bucket, row = _row(p, cid)
    if bucket == "to_write" and row["to"] == Lifecycle.ACTIVE.value:
        _ok(gate, "a capability this session never heard of classifies purely "
                  "from a named owner -- machinery, not two hardcoded ids")
    else:
        _fail(gate, f"bucket={bucket} row={row}")


def _classification_events():
    """Every recorded classification, read from the DURABLE log.

    The first version of the two gates below read `plan()["to_write"]`, and
    they went red the moment the migration was applied -- because an applied
    plan has nothing left to write. That is the population trap in miniature:
    an instrument pointed at a transient queue reports either "nothing to
    check" or, if the assertion had been phrased the other way, a permanent
    clean bill over an empty set. What was classified is a fact about the log,
    which survives the apply, so the log is what these gates read.
    """
    return [e for e in load_log() if e.to_state == Lifecycle.ACTIVE.value]


def t_live_path_still_disclaims() -> None:
    """The log gates below audit what WAS decided. This one audits what the
    code would decide NEXT, which the log cannot see once a migration has been
    applied and its queue is empty. Without it, the disclaimer could be deleted
    today and the omission would only surface on the next external capability
    the estate acquires."""
    gate = "V-EXT-PATH-STILL-DISCLAIMS"
    cid = "zzyzx-synthetic-owned"
    with _with_external(cid, owner="a third-party registry nobody here owns"):
        p = M.plan(contracts=[_synthetic(cid)])
        _, row = _row(p, cid)
    extra = " ".join(str(x) for x in (row or {}).get("evidence_extra", []))
    if (row and row.get("action") == "write"
            and "EXTERNAL != AVAILABLE" in extra
            and f"external_owner:" in extra):
        _ok(gate, "the live classification path still attaches a named owner "
                  "and the authority-only disclaimer")
    else:
        _fail(gate, f"row={row}")


def t_authority_not_availability() -> None:
    """The distinction a future reader is most likely to lose."""
    gate = "V-EXT-AUTHORITY-NOT-AVAILABILITY"
    ext = [e for e in _classification_events() if e.actor == M.ACTOR_EXTERNAL]
    if not ext:
        _fail(gate, "no external classification recorded in the lifecycle log "
                    "-- population floor of 1 not met")
        return
    bad = []
    for e in ext:
        blob = " ".join(str(x) for x in (e.evidence or []))
        if "EXTERNAL != AVAILABLE" not in blob:
            bad.append((e.capability_id, "no authority-only disclaimer"))
        if not any(str(x).startswith("external_owner:") and len(str(x)) > 16
                   for x in (e.evidence or [])):
            bad.append((e.capability_id, "no named owner in the evidence"))
        for word in ("available", "healthy", "reachable", "installed"):
            if word in e.reason.lower():
                bad.append((e.capability_id, f"reason asserts {word!r}"))
    if bad:
        _fail(gate, f"{bad}")
        return
    _ok(gate, f"{len(ext)} recorded external classification(s) carry a named "
              "owner and the authority-only disclaimer, and claim no "
              "availability")


def t_external_actor_is_distinct() -> None:
    """A classification made by an external-ownership argument and one made by
    a probe are different institutional acts. The log must be able to say
    which, without anyone reading commit dates."""
    gate = "V-EXT-ACTOR-IS-DISTINCT"
    evs = _classification_events()
    ext = {e.capability_id for e in evs if e.actor == M.ACTOR_EXTERNAL}
    probed = {e.capability_id for e in evs if e.actor == M.ACTOR}
    if ext and probed and not (ext & probed):
        _ok(gate, f"external={sorted(ext)} actor={M.ACTOR_EXTERNAL}; "
                  f"probe-backed={sorted(probed)} actor={M.ACTOR}")
    else:
        _fail(gate, f"ext={sorted(ext)} probed={sorted(probed)}")


def t_external_is_not_probe_debt() -> None:
    gate = "V-EXT-NOT-PROBE-DEBT"
    vs = {v.contract_id: v.status for v in R.evaluate_all()}
    ext = {k for k, s in vs.items() if s == R.EXTERNAL}
    uneval = {k for k, s in vs.items() if s == R.UNEVALUABLE}
    if ext and not (ext & uneval):
        _ok(gate, f"EXTERNAL={sorted(ext)} disjoint from "
                  f"UNEVALUABLE={sorted(uneval)}")
    else:
        _fail(gate, f"ext={sorted(ext)} uneval={sorted(uneval)}")


def t_plan_is_deterministic() -> None:
    gate = "V-EXT-PLAN-DETERMINISTIC"
    a, b = M.plan(), M.plan()
    ka = [(r["id"], r.get("to"), r["why"]) for r in a["to_write"]]
    kb = [(r["id"], r.get("to"), r["why"]) for r in b["to_write"]]
    if ka == kb and a["total"] == b["total"]:
        _ok(gate, f"two consecutive plans identical over {a['total']} contracts")
    else:
        _fail(gate, "plan is not deterministic")


def main() -> int:
    for fn in (t_real_externals_are_named, t_named_owner_classifies,
               t_unnamed_owner_stays_unknown, t_named_owner_is_not_hardcoded,
               t_live_path_still_disclaims,
               t_authority_not_availability, t_external_actor_is_distinct,
               t_external_is_not_probe_debt, t_plan_is_deterministic):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 -- harness failure, not a finding
            _fail(f"HARNESS-FAILED:{fn.__name__}", f"{type(exc).__name__}: {exc}")
    total = _passes + _fails
    print(f"EXTERNAL_OWNER_PASS={_passes}/{total}  threshold={total}/{total}  "
          f"VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
