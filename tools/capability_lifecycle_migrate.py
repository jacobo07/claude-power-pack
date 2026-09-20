#!/usr/bin/env python3
"""capability_lifecycle_migrate.py -- backfill lifecycle, by evidence (W3).

Ten capability contracts predate `contract.lifecycle`. The tempting migration
writes ACTIVE across all of them: every one is in the store, the store is in
use, so they must be current. That reasoning legitimises whatever happens to be
on disk, and it is exactly what §X refuses -- an existing row is not evidence
of active authority, it is evidence that nobody has looked.

So this reuses the evidence the estate already produces. `retirement.py`
evaluates each contract's `retirement_condition` against real repository state
and returns a verdict whose statuses are already honest about their own limits.
Mapping those verdicts to a lifecycle is the whole migration:

    retirement verdict          lifecycle written   why
    ------------------          -----------------   ---
    ACTIVE                      active              a probe RAN and the
                                                    retirement condition is
                                                    measurably NOT met
    NEVER                       active              the contract declares its
                                                    condition permanent
    RETIRED_BY_EVIDENCE         (none -- reported)  the condition HAS come
                                                    true; retiring it is an
                                                    Owner act, not a migration
    UNEVALUABLE                 (none -- unknown)   probe debt: no evaluator
    NO_CONDITION                (none -- unknown)   the contract never said
    EXTERNAL + named owner      active              see below
    EXTERNAL, owner unnamed     (none -- unknown)   who decides is itself
                                                    unknown

W3 mapped EXTERNAL to UNKNOWN, and that was one distinction too few.
`retirement.py` separates EXTERNAL from UNEVALUABLE on purpose -- "we owe a
measurement" is a gap, "this repo cannot measure it" is a permanent structural
fact -- and mapping both to UNKNOWN here re-merged them one layer up.

When the external party is NAMED, the currency of the authority is a deduction,
not an absence: nothing in this repository can retire the capability, only an
Owner attestation about that named party's facts can, and no such attestation
exists. So it is the current authority. When no owner is named, who decides is
itself unknown and the contract stays UNKNOWN -- which is the fail-closed
default and the mutation that proves this is machinery rather than two
hardcoded ids.

This classifies AUTHORITY and says nothing about AVAILABILITY. That the pricing
market exists does not make cost routing healthy, reachable or correct; the
transition's evidence says so in words, because a future reader of
`lifecycle=active` must not read it as "the external thing works".

Only the first two rows and the named-owner external row write. Everything else stays UNKNOWN, which is a state
this system can carry -- UNKNOWN activates, reports `lifecycle_verified=False`,
and is counted by a shrink-only ratchet. Absence is never promoted to ACTIVE to
make a number look better.

RETIRED_BY_EVIDENCE deliberately does NOT auto-revoke. `retirement.py` is
propose-only by design -- "a capability that retires itself is a gate that
grades itself" -- and a migration that revoked on its own authority would be
that gate, wearing a different hat.

PROPERTIES
  deterministic   the same repository state yields the same classification
  idempotent      a classified contract is skipped, not re-transitioned; a
                  second run writes nothing and returns the same report
  re-runnable     each contract is independent and the log is append-only, so
                  a run killed halfway completes on the next invocation
  auditable       every write goes through `lifecycle.transition`, so it lands
                  in lifecycle_log.jsonl with actor, reason and evidence

CLI
  python tools/capability_lifecycle_migrate.py            # report only
  python tools/capability_lifecycle_migrate.py --apply    # write
  python tools/capability_lifecycle_migrate.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime import retirement as R  # noqa: E402
from modules.capability_runtime.contract import load_contracts  # noqa: E402
from modules.capability_runtime.lifecycle import (  # noqa: E402
    Lifecycle, LifecycleError, state_of, transition,
)

ACTOR = "migration:ucr-cif-w3"
# The external-owner classification is a separate institutional act from the
# W3 backfill and carries its own actor, so the lifecycle log can answer "which
# pass decided this?" without anyone reading commit dates.
ACTOR_EXTERNAL = "owner-classification:ucr-cif-w4-external"

# Stated once, attached to every external classification. A lifecycle of
# `active` on an externally-owned capability is a claim about AUTHORITY -- that
# nothing has withdrawn it and nothing in this repository could. It is not a
# claim that the external party's capability is available, healthy or correct.
_EXTERNAL_DISCLAIMER = ("authority-only: EXTERNAL != AVAILABLE. This records "
                        "that no repository signal can retire the capability "
                        "and that no Owner attestation has, not that the "
                        "external provider is reachable or healthy")

# Retirement statuses that constitute POSITIVE evidence of live authority.
_WRITES_ACTIVE = {R.ACTIVE, R.NEVER}
_REASON = {
    R.ACTIVE: ("retirement condition probed against real repository state and "
               "measurably not met"),
    R.NEVER: "contract declares its retirement condition permanent",
}
# Why a contract stays UNKNOWN. Named individually: "insufficient evidence"
# sends someone to check everything, these send them to one thing.
_WHY_UNKNOWN = {
    R.UNEVALUABLE: ("no deterministic probe exists for this condition "
                    "(probe debt -- this repository could pay it)"),
    R.NO_CONDITION: "the contract declares no retirement condition",
    R.EXTERNAL: ("the condition is external AND no external owner is named, "
                 "so who decides it is itself unknown -- name the owner in "
                 "retirement.EXTERNAL_CONDITIONS to close this"),
    R.RETIRED: ("the retirement condition HAS come true -- an Owner decides "
                "SUPERSEDED vs REVOKED; a migration may not"),
}


def _why_unknown(row: dict) -> str:
    """Why this contract stays UNKNOWN, derived from the verdict rather than
    asserted from a table.

    UNEVALUABLE covers two different debts and the W3 ratchet froze the wrong
    one against `spec_depth_selection`: it recorded "no deterministic probe
    exists" for a capability whose probe existed, was registered, and had run.
    A reason that is a constant cannot notice when it stops being true, so the
    probe field decides -- absent means nobody wrote a probe, present means one
    ran and honestly could not conclude, which is an evidence frontier and not
    a coding task.
    """
    status = row["retirement_status"]
    if status == R.UNEVALUABLE:
        if row.get("probe"):
            return ("a deterministic probe EXISTS, ran, and could not "
                    f"conclude: {row['evidence']}. This is an evidence "
                    "frontier, not probe debt -- writing another probe would "
                    "not move it")
        return ("no deterministic probe is registered for this condition "
                "(probe debt -- this repository could pay it)")
    return _WHY_UNKNOWN.get(status, f"unmapped status {status!r}")


def plan(contracts=None, contracts_dir=None, root=None) -> dict:
    """Classify every contract. Pure: reads state, writes nothing."""
    cs = contracts if contracts is not None else load_contracts(contracts_dir)
    verdicts = {v.contract_id: v for v in
                R.evaluate_all(contracts=cs, root=root)}

    to_write, already, unknown, needs_owner = [], [], [], []
    for c in sorted(cs, key=lambda x: x.id):
        current = state_of(c)
        v = verdicts.get(c.id)
        status = v.status if v is not None else R.UNEVALUABLE
        row = {
            "id": c.id,
            "current": current.value,
            "retirement_status": status,
            "condition": (v.condition if v is not None else ""),
            "evidence": (v.evidence if v is not None else "no verdict produced"),
            "probe": (v.probe if v is not None else ""),
        }
        if current is not Lifecycle.UNKNOWN:
            row["action"] = "skip"
            row["why"] = f"already classified as {current.value}"
            already.append(row)
        elif status in _WRITES_ACTIVE:
            row["action"] = "write"
            row["to"] = Lifecycle.ACTIVE.value
            # `.get`, not `[...]`: _WRITES_ACTIVE and _REASON are two tables that
            # must agree, and a KeyError here would abort the whole migration
            # over a bookkeeping slip. A status admitted without a stated reason
            # is still a defect, so it is written into the row where the plan
            # shows it and `V-W3-MIG-REASON-IS-NAMED` can see it -- not hidden
            # behind a crash that reads like the tool being broken.
            row["why"] = _REASON.get(
                status, f"admitted by _WRITES_ACTIVE with no stated reason "
                        f"({status!r}) -- reason table is out of step")
            to_write.append(row)
        elif status == R.EXTERNAL and R.external_owner(c.id):
            owner = R.external_owner(c.id)
            row["action"] = "write"
            row["to"] = Lifecycle.ACTIVE.value
            row["actor"] = ACTOR_EXTERNAL
            row["external_owner"] = owner
            row["why"] = (f"retirement condition is owned by {owner}; no "
                          "repository signal can settle it and no Owner "
                          "attestation has retired it, so this remains the "
                          "current authority")
            row["evidence_extra"] = [f"external_owner:{owner}",
                                     _EXTERNAL_DISCLAIMER]
            to_write.append(row)
        else:
            row["action"] = "leave-unknown"
            row["why"] = _why_unknown(row)
            (needs_owner if status == R.RETIRED else unknown).append(row)

    return {
        "total": len(cs),
        "to_write": to_write,
        "already_classified": already,
        "stays_unknown": unknown,
        "needs_owner_decision": needs_owner,
    }


def apply(p: dict, contracts=None, contracts_dir=None, log_path=None) -> dict:
    """Execute a plan. Every write goes through `transition`, so a contract
    somebody classified between plan and apply is REFUSED, not overwritten."""
    written, refused = [], []
    for row in p["to_write"]:
        try:
            ev = transition(
                row["id"], row["to"],
                expected=Lifecycle.UNKNOWN,
                actor=row.get("actor", ACTOR),
                reason=row["why"],
                evidence=[f"retirement:{row['retirement_status']}",
                          str(row["evidence"])[:300]] +
                         ([f"probe:{row['probe']}"] if row["probe"] else []) +
                         list(row.get("evidence_extra", [])),
                contracts=contracts, contracts_dir=contracts_dir,
                log_path=log_path,
            )
            written.append({"id": ev.capability_id, "to": ev.to_state})
        except LifecycleError as exc:
            refused.append({"id": row["id"], "refused": str(exc)})
    return {"written": written, "refused": refused}


def _print(p: dict, applied=None) -> None:
    print(f"capability lifecycle migration -- {p['total']} contract(s)\n")

    def block(title, rows, extra=""):
        print(f"{title}: {len(rows)}")
        for r in rows:
            tail = f" -> {r['to']}" if "to" in r else ""
            print(f"  {r['id']}{tail}")
            print(f"      {r['why']}")
            if extra and r.get(extra):
                print(f"      evidence: {str(r[extra])[:150]}")
        print()

    block("WRITE (evidence of live authority)", p["to_write"], "evidence")
    block("ALREADY CLASSIFIED", p["already_classified"])
    block("STAYS UNKNOWN (each names the fact that would resolve it)",
          p["stays_unknown"])
    block("NEEDS AN OWNER DECISION", p["needs_owner_decision"], "evidence")

    if applied is not None:
        print(f"APPLIED: {len(applied['written'])} written, "
              f"{len(applied['refused'])} refused")
        for r in applied["refused"]:
            print(f"  REFUSED {r['id']}: {r['refused']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true",
                    help="write the classifications (default: report only)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--contracts-dir", default=None)
    args = ap.parse_args(argv)

    p = plan(contracts_dir=args.contracts_dir)
    applied = None
    if args.apply:
        # Re-read so `apply` transitions against the state on disk now, not the
        # snapshot the plan was built from.
        applied = apply(p, contracts_dir=args.contracts_dir)

    if args.json:
        print(json.dumps({"plan": p, "applied": applied}, indent=2,
                         ensure_ascii=False))
    else:
        _print(p, applied)
    if applied and applied["refused"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
