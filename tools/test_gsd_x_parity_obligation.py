#!/usr/bin/env python3
"""V-PARITY-* -- the derived obligation a reconstruction mission owes.

DO-4 says: parity judged only on the traces the implementation was fitted to is
the one result a memorising reconstruction and a generalising one both produce,
so it cannot tell them apart.

THE CONTROL THAT MATTERS IS TRANSFER. This module's own file records GSDX-M04:
its earlier patterns encoded the FIXTURE'S PHRASING rather than the fact, and
each unseen domain cost exactly one more verb -- the signature of a lookup table
wearing a rule's name. So the first APK/Wii case proves almost nothing on its
own, and V-PARITY-TRANSFER (a pricing engine, no platform, no game, no port)
is the gate that can actually fail. V-PARITY-NO-PLATFORM guards the same
property from the other side by reading the operator's own source.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.gsd_x.mission import obligation as ob_mod  # noqa: E402
from modules.gsd_x.mission.obligation import (  # noqa: E402
    ACCEPTED, STALE, derive, extract_facts, invalidate_if_parent_gone, judge,
)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _do4(intent: str, reality: str = ""):
    obs, facts = derive(intent, reality)
    for o in obs:
        if o.identifier == "DO-4":
            return o, facts
    return None, facts


def main() -> int:
    # 1. The mission the Owner would actually type.
    intent = "Port this APK game to Wii faithfully"
    o, _ = _do4(intent)
    if o is not None:
        _ok("V-PARITY-DERIVES", f"{intent!r} -> DO-4 {o.operator}")
    else:
        _fail("V-PARITY-DERIVES", f"{intent!r} derived no DO-4")

    # 2. TRANSFER. A different domain entirely: no platform, no game, no port.
    #    If this needs a new verb, the rule is a lookup table.
    other = ("reimplement the legacy pricing engine in Rust as a drop-in "
             "with identical behaviour")
    o2, _ = _do4(other)
    if o2 is not None:
        _ok("V-PARITY-TRANSFER", f"unseen domain -> DO-4 on {len(o2.evidence)} fact(s)")
    else:
        _fail("V-PARITY-TRANSFER", f"{other!r} derived no DO-4 -- fitted to the fixture")

    # 3+4. BOTH facts are necessary. One of two must not buy the obligation, or
    #      the conjunction is decoration.
    o3, _ = _do4("port the renderer to the new backend")          # relation only
    o4, _ = _do4("we need exact behaviour here")                  # fidelity only
    if o3 is None and o4 is None:
        _ok("V-PARITY-NEEDS-BOTH", "relation-only and fidelity-only both derive nothing")
    else:
        _fail("V-PARITY-NEEDS-BOTH",
              f"relation-only={o3 is not None}, fidelity-only={o4 is not None}")

    # 5. Materiality gate: it must survive judge(), not merely be produced.
    o5, _ = _do4(intent)
    j = judge(o5) if o5 else None
    if j is not None and j.disposition == ACCEPTED:
        _ok("V-PARITY-ACCEPTED", f"judge() -> {j.disposition}")
    else:
        d = j.disposition if j else "no obligation"
        _fail("V-PARITY-ACCEPTED", f"judge() -> {d}, expected ACCEPTED")

    # 6. Enrichment: an executable reference can GENERATE unseen cases, which
    #    changes the consequence from a limitation into a choice.
    reality = "The original game still runs on the reference handset."
    o6, facts6 = _do4(intent, reality)
    names = {f.name for f in facts6}
    if o6 is not None and "reference_is_executable" in names \
            and "generated" in o6.consequence.lower():
        _ok("V-PARITY-ENRICHED", "executable reference strengthens the consequence")
    else:
        _fail("V-PARITY-ENRICHED",
              f"facts={sorted(names)}, enriched={'generated' in (o6.consequence.lower() if o6 else '')}")

    # 7. Derived once is not true forever.
    o7, _ = _do4(intent)
    o7 = judge(o7)
    o7 = invalidate_if_parent_gone(o7, extract_facts("tidy up the readme", ""))
    if o7.disposition == STALE:
        _ok("V-PARITY-STALE", f"parent gone -> {o7.disposition}")
    else:
        _fail("V-PARITY-STALE", f"parent gone -> {o7.disposition}, expected STALE")

    # 8. GSDX-M04 GUARD. The operator must not name a platform, a vendor or a
    #    game: a rule that does is fitted to one mission by construction.
    src = inspect.getsource(ob_mod.op_unfalsifiable_parity_consequence).lower()
    banned = [w for w in ("apk", "wii", "android", "dolphin", "nintendo",
                          "emulator", "game", "console") if w in src]
    if not banned:
        _ok("V-PARITY-NO-PLATFORM", "operator source names no platform or vendor")
    else:
        _fail("V-PARITY-NO-PLATFORM", f"operator source names {banned}")

    total = _passes + _fails
    print(f"\nPARITY_PASS={_passes}/{total}  threshold=7/7")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
