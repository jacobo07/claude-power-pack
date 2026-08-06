#!/usr/bin/env python3
"""Done-gate for CDICF's graph integration (V-CDICF-GRAPH-*).

E3 was proposed as "graphify +component node/edge types". It is not built that
way, and the reason is on the record: in July an identical proposal for CDIO
was reality-scanned and the Owner approved **riding the existing types**
instead, because tools/graphify_knowledge.py fixes NODE_TYPES/EDGE_TYPES and
editing them re-indexes 722 coordinates for every repo
(vault/plans/cdio-build-2026-07-05.md, decision 1). CDICF follows that
precedent rather than re-litigating it: one governance token, zero ontology
change.

So this suite asserts two things at once -- that CDICF's artifacts became
promotable, and that the ontology did NOT move. The second matters more. A
later session that "helpfully" adds a component node type would pass every
CDICF test while silently taking the blast radius the Owner declined.

Blast radius is measured, not assumed: prose mentioning the word must NOT
promote, only the identifier form.

Hermetic: pure predicate calls, no global store is opened or written.

Run:  python tools/test_cdicf_graph.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "modules", "graphify"))
sys.path.insert(0, HERE)

import global_store as gs  # noqa: E402
import graphify_knowledge as gk  # noqa: E402

PASSES = 0
FAILS = 0

# The ontology as the Owner approved it in July, MEASURED from
# tools/graphify_knowledge.py rather than assumed. A change here is not a test
# failure to be updated -- it is the decision being reversed, and it needs the
# same Owner sign-off the original had.
FROZEN_NODE_TYPES = 10


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _node(name: str, ntype: str = "dataset", summary: str = "") -> dict:
    return {"node_id": name.lower().replace(" ", "-"), "name": name,
            "node_type": ntype, "summary": summary, "edges": []}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    print("V-CDICF-GRAPH -- graph integration by riding the existing types\n")

    # -- 01 CDICF decision docs promote
    n = _node("CDICF_DECISION_LOG", "decision",
              "D-016: the adversarial corpus found four defects")
    if gs._is_promotable(n):
        _ok("V-CDICF-GRAPH-01-DOCS-PROMOTE",
            "CDICF_DECISION_LOG promotes as a cross-repo decision node")
    else:
        _fail("V-CDICF-GRAPH-01-DOCS-PROMOTE", "not promotable")

    # -- 02 the gate ids promote too
    if gs._is_promotable(_node("V-CDICF-IDX-04", "trap", "isolation refusal")):
        _ok("V-CDICF-GRAPH-02-GATE-IDS", "V-CDICF-IDX-04 carries the token")
    else:
        _fail("V-CDICF-GRAPH-02-GATE-IDS", "gate id not recognised")

    # -- 03 the sealed traps were ALREADY covered by T-[A-Z]. Asserted so the
    #    change is not credited with coverage that predates it.
    trap = _node("T-DECLARED-BUT-UNRESOLVED-DEPENDENCY-001", "trap",
                 "a declared dependency passes every gate and fails at render")
    pre_existing = bool(gs.re.compile(r"\bT-[A-Z]", gs.re.IGNORECASE)
                        .search(trap["name"]))
    if gs._is_promotable(trap) and pre_existing:
        _ok("V-CDICF-GRAPH-03-TRAPS-ALREADY-COVERED",
            "A5's traps promote under the pre-existing T-[A-Z] token, not this "
            "change")
    else:
        _fail("V-CDICF-GRAPH-03-TRAPS-ALREADY-COVERED",
              f"promotable={gs._is_promotable(trap)} pre_existing={pre_existing}")

    # -- 04 blast radius: prose is not an identifier. 106 files mention the
    #    word; promoting all of them would make the signal gate meaningless.
    prose = _node("Some design note", "dataset",
                  "we should probably use CDICF for this surface one day")
    if not gs._is_promotable(prose):
        _ok("V-CDICF-GRAPH-04-PROSE-EXCLUDED",
            "a passing mention of the word does not promote -- the token "
            "requires CDICF- or CDICF_")
    else:
        _fail("V-CDICF-GRAPH-04-PROSE-EXCLUDED",
              "prose mention promoted; the token is too broad")

    # -- 05 the pre-existing vocabulary still behaves
    unchanged = {"CDIO-3": "dataset", "HR-SECRET-001": "hard_rule",
                 "GK-10": "dataset", "BL-0068": "decision",
                 "SCS C95": "scs_seal", "CO-12": "contract",
                 "PM-03": "contract"}
    broke = [k for k, t in unchanged.items()
             if not gs._is_promotable(_node(k, t))]
    if not broke:
        _ok("V-CDICF-GRAPH-05-EXISTING-TOKENS",
            f"all {len(unchanged)} pre-existing token families still promote")
    else:
        _fail("V-CDICF-GRAPH-05-EXISTING-TOKENS", f"broke: {broke}")

    # -- 06 a node with no governance identity is still refused
    plain = _node("random helper", "dataset", "a local utility")
    if not gs._is_promotable(plain):
        _ok("V-CDICF-GRAPH-06-GATE-STILL-REFUSES",
            "an ungoverned node does not promote -- the gate did not become a "
            "blanket yes")
    else:
        _fail("V-CDICF-GRAPH-06-GATE-STILL-REFUSES", "ungoverned node promoted")

    # -- 07 THE ONTOLOGY DID NOT MOVE. This is the July decision, pinned.
    n_types = len(gk.NODE_TYPES)
    invented = [t for t in gk.NODE_TYPES
                if t in ("component", "design_standard", "manifest")]
    if n_types == FROZEN_NODE_TYPES and not invented:
        _ok("V-CDICF-GRAPH-07-ONTOLOGY-FROZEN",
            f"NODE_TYPES still {n_types}; no component/design node type was "
            f"added (cdio-build-2026-07-05 decision 1 upheld)")
    else:
        _fail("V-CDICF-GRAPH-07-ONTOLOGY-FROZEN",
              f"NODE_TYPES={n_types} (expected {FROZEN_NODE_TYPES}), "
              f"invented={invented} -- reversing an Owner-approved decision "
              f"needs the same sign-off the original had")

    # -- 08 promotion remains type-gated: the right token on the wrong type
    #    is still refused.
    wrong_type = _node("CDICF_NEXT_ACTIONS", "session_note", "next actions")
    if not gs._is_promotable(wrong_type):
        _ok("V-CDICF-GRAPH-08-TYPE-GATED",
            f"a CDICF token on a non-promotable type is refused; PROMOTABLE "
            f"is still {len(gs.PROMOTABLE)} types")
    else:
        _fail("V-CDICF-GRAPH-08-TYPE-GATED", "token bypassed the type gate")

    total = PASSES + FAILS
    print(f"\nCDICF_GRAPH_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
