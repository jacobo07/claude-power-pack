#!/usr/bin/env python3
"""V-gates for goal-scoped obligation storage and the accepted-with-proof crash.

Two things the Goal Spine needs from GSD X that GSD X did not give it:

1. SEVERAL GOALS IN ONE ROOT. `store.store_path(root)` names exactly one file per
   project root, so two Goals in one repository would read and overwrite each
   other's obligations. The extension is an optional namespace; the default path
   must stay byte-for-byte what it was, because every existing mission uses it.

2. `contract.project()` RAISED on an ACCEPTED obligation that carries a proof.
   It read `o.id`; the dataclass field is `identifier`. Nothing had driven that
   combination -- and it is precisely the shape of every Production Reality
   obligation, whose proof is the verifier's verdict. Reproduced before the fix:
       SUBJECT accepted+proof: AttributeError -> 'Obligation' object has no attribute 'id'
   with the control (accepted, no proof) passing in the same run.

    python tools/test_gsd_x_mission_goal_scope.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.mission import contract as mc         # noqa: E402
from modules.gsd_x.mission import obligation as ob       # noqa: E402
from modules.gsd_x.mission import store as st            # noqa: E402


def _obl(ident: str, disposition: str = ob.ACCEPTED, proof: str = "") -> ob.Obligation:
    return ob.Obligation(ident, f"text {ident}", "TEST_OPERATOR", ["fact:x"],
                         "a named consequence", disposition=disposition, proof=proof)


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  OK   {g}  {ev}")

    def bad(g, ev):
        fails.append(g)
        print(f"  FAIL {g}  {ev}")

    # --- B11: accepted + proof must project, and must surface the proof -------
    root = Path(tempfile.mkdtemp())
    subject = _obl("DO-PROOF", proof="verify_change VERIFY_RESULT=DONE_VERIFIED")
    control = _obl("DO-NOPROOF")
    try:
        c = mc.project(root, intent="i", obligations=[subject, control])
        reqs = c.value("proof_requirements") or []
        if reqs == [{"obligation": "DO-PROOF", "proof": subject.proof}]:
            ok("V-GSDX-SCOPE-ACCEPTED-PROOF-PROJECTS", f"proof_requirements={reqs}")
        else:
            bad("V-GSDX-SCOPE-ACCEPTED-PROOF-PROJECTS", f"wrong requirements {reqs!r}")
    except AttributeError as exc:
        bad("V-GSDX-SCOPE-ACCEPTED-PROOF-PROJECTS", f"raised {exc}")

    # --- the default path is unchanged ---------------------------------------
    if st.store_path(root) == root / ".gsd-x" / "obligations.json":
        ok("V-GSDX-SCOPE-DEFAULT-PATH-UNCHANGED", str(st.store_path(root)))
    else:
        bad("V-GSDX-SCOPE-DEFAULT-PATH-UNCHANGED", str(st.store_path(root)))

    # --- two goals in one root are isolated ----------------------------------
    try:
        st.save(root, [_obl("DO-A")], namespace="goal-a")
        st.save(root, [_obl("DO-B"), _obl("DO-C")], namespace="goal-b")
        a = [o.identifier for o in st.load(root, namespace="goal-a")]
        b = [o.identifier for o in st.load(root, namespace="goal-b")]
        default = st.load(root)
        if a == ["DO-A"] and b == ["DO-B", "DO-C"] and default == []:
            ok("V-GSDX-SCOPE-TWO-GOALS-ISOLATED", f"a={a} b={b} default=[]")
        else:
            bad("V-GSDX-SCOPE-TWO-GOALS-ISOLATED", f"a={a} b={b} default={default}")
    except TypeError as exc:
        bad("V-GSDX-SCOPE-TWO-GOALS-ISOLATED", f"no namespace support: {exc}")

    # --- a namespace cannot escape the store ---------------------------------
    # Only ValueError counts. An earlier version also accepted TypeError and went
    # GREEN 6/6 against a store with no namespace support at all -- the unknown
    # keyword raised TypeError, which it read as a refusal. A gate that passes
    # when the feature is absent measures nothing.
    refused = []
    for hostile in ("../escape", "a/b", "..", "", "C:\\x", "goal a"):
        try:
            st.store_path(root, namespace=hostile)
        except ValueError:
            refused.append(hostile)
        except TypeError:
            pass
    if len(refused) == 6:
        ok("V-GSDX-SCOPE-HOSTILE-NAMESPACE-REFUSED", "6/6 refused")
    else:
        bad("V-GSDX-SCOPE-HOSTILE-NAMESPACE-REFUSED",
            f"refused only {refused!r}")

    # --- corrupt namespaced store raises, it is never an empty store ---------
    try:
        p = st.store_path(root, namespace="goal-corrupt")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{not json", encoding="utf-8")
        try:
            st.load(root, namespace="goal-corrupt")
            bad("V-GSDX-SCOPE-CORRUPT-RAISES", "a corrupt store read as empty")
        except RuntimeError:
            ok("V-GSDX-SCOPE-CORRUPT-RAISES", "RuntimeError")
    except TypeError as exc:
        bad("V-GSDX-SCOPE-CORRUPT-RAISES", f"no namespace support: {exc}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_SCOPE_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
