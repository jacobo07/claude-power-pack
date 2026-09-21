#!/usr/bin/env python3
"""Cut the signup derivative from the surface_architecture kernel contract.

    python tools/seed_signup_derivative.py [--dry-run] [--force]

This is the first real derivative in this estate: `vault/capability_runtime/
derivatives/` did not exist before it. The 6-component specialization map shipped
2026-08-04 and had never cut one.

THREE THINGS THIS DOES THAT A NAIVE SEED WOULD NOT
--------------------------------------------------
1. It CALLS `contaminates_kernel` against the real kernel contract, with a positive
   control. Nothing in `compile_overrides()` or `specialize()` invokes it -- it is
   reachable only from `audit()` -- and it is fail-open: pass it the wrong object and
   `not isinstance(kernel_fields, dict)` returns [], i.e. CLEAN. A green from a
   question never asked is indistinguishable from a green.

2. It persists ONLY through `save_derivative()`. `derive()` mints the child id as
   f"{parent.id}@{project}", so writing it with `save_contract()` would drop
   `surface_architecture@signup.json` into the flat `contracts/` directory, where
   `load_contracts()` globs `*.json` and `evaluate_all` would score a domain-specific
   capability against every unrelated mission -- exactly what the domain-blind kernel
   split exists to prevent.

3. It asserts `contracts/` is unchanged across the whole run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    CONTRACTS_DIR, load_contracts,
)
from modules.capability_runtime.derivatives import (  # noqa: E402
    DERIVATIVES_DIR, save_derivative,
)
from modules.surface_architecture.verticals import signup  # noqa: E402

PARENT_ID = "surface_architecture"


def _contracts_snapshot() -> set:
    return {p.name for p in CONTRACTS_DIR.glob("*.json")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing derivative record")
    args = ap.parse_args(argv)

    before = _contracts_snapshot()

    parents = {c.id: c for c in load_contracts()}
    parent = parents.get(PARENT_ID)
    if parent is None:
        print(f"REFUSED: parent contract {PARENT_ID!r} is not registered. "
              "Run tools/seed_surface_architecture_contract.py first.")
        return 1

    # The parent's non_scope is threaded in so the derivative INHERITS those
    # boundaries verbatim. HR-APA-017 compares by value, so a reworded boundary reads
    # as a dropped one -- which is exactly how this seed failed on its first real run.
    spec = signup.build_spec(parent.non_scope)
    sp = signup._load_specialization()

    report = sp.audit(spec, parent.to_dict())
    print(f"depth={report['depth']} of 6  components={report['populated_components']}")
    print(f"compiles={report['compiles']}  {report['reason']}")
    print(f"kernel_contamination={report['kernel_contamination']}")

    if report["name_level_only"] or not report["compiles"]:
        print("REFUSED: HR-APA-016 -- this is a rename, not a specialization.")
        return 1
    if report["kernel_contamination"]:
        print("REFUSED: HR-APA-017 -- domain vocabulary reaches a kernel field.")
        return 1

    # POSITIVE CONTROL. A detector that has stopped detecting reports the same clean
    # result as one that works, so prove it can still find something before trusting
    # the empty list above.
    probe = signup.build_spec(parent.non_scope)
    probe.domain_pack.vocabulary = dict(probe.domain_pack.vocabulary)
    probe.domain_pack.vocabulary["probe"] = "boundary placement"
    control = sp.contaminates_kernel(probe, parent.to_dict())
    if not control:
        print("REFUSED: the contamination detector found nothing in a deliberately "
              "contaminated spec. A clean result from it proves nothing.")
        return 1
    print(f"detector control: fired on {len(control)} field(s) -- it can still detect")

    if args.dry_run:
        print("dry run: nothing written")
        return 0

    child, record = sp.specialize(
        parent, spec,
        upgrade_path="re-run tools/seed_signup_derivative.py against the current "
                     "surface_architecture contract")
    print(f"child id: {child.id}")
    print(f"  inherited={len(record.inherited)} overridden={len(record.overridden)} "
          f"added={len(record.added)}")

    target = DERIVATIVES_DIR / f"{record.child_id.replace('/', '_').replace('@', '_at_')}.json"
    if target.exists() and not args.force:
        print(f"REFUSED: {target.name} already exists. Re-run with --force to replace.")
        return 1

    path = save_derivative(record)
    print(f"wrote {path.relative_to(_PP_ROOT)}")

    after = _contracts_snapshot()
    if after != before:
        print(f"FAILED INVARIANT: contracts/ changed: {sorted(after ^ before)}. "
              "A derivative must never land in the kernel registry.")
        return 1
    print(f"contracts/ unchanged ({len(after)} files) -- the derivative did not leak "
          "into cross-mission routing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
