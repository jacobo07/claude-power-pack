#!/usr/bin/env python3
"""Done-gate for callable liveness (V-CALLABLE-*).

Every behavioural gate here runs against a SYNTHETIC repository built in a temp dir.
That is deliberate. A drill pinned to a real offender has an interest in that offender
surviving: fix the real one and the assertion either goes vacuous or goes red for the
wrong reason, and re-pointing it every time the inventory turns is how a drill quietly
stops testing anything. A synthetic subject represents the CLASS, cannot be fixed out
from under the assertion, and still exercises the real predicates.

The one gate that touches the real repo is a POSITIVE CONTROL: it asserts the sweep
found a plausible number of symbols and both poles of the classification. A detector
that silently matched nothing would otherwise report the same clean bill as one that
works.

Run:  python tools/test_callable_reach.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.liveness import callable_reach as cr  # noqa: E402

PASSES = 0
FAILS = 0


def _ok(gate: str, evidence: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _mk(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _synthetic(root: Path) -> None:
    """A repo with one subject module and callers in every shape that matters."""
    _mk(root, "modules/widget/engine.py", """
def called_plainly():
    return 1


def called_via_alias():
    return 2


def called_through_module_attr():
    return 3


def called_after_rebinding():
    return 4


def never_called_anywhere():
    return 5


def only_a_test_calls_me():
    return 6


def only_prose_mentions_me():
    return 7
""")
    # Each caller uses a DIFFERENT import shape. If the resolver understands only the
    # obvious one, the others are reported dead and this suite says so.
    _mk(root, "tools/caller_a.py", """
from modules.widget.engine import called_plainly
called_plainly()
""")
    _mk(root, "tools/caller_b.py", """
from modules.widget.engine import called_via_alias as aliased
aliased()
""")
    _mk(root, "tools/caller_c.py", """
from modules.widget import engine
engine.called_through_module_attr()
""")
    _mk(root, "tools/caller_d.py", """
import modules.widget.engine as eng
shortcut = eng
shortcut.called_after_rebinding()
""")
    _mk(root, "tools/test_widget.py", """
from modules.widget.engine import only_a_test_calls_me
only_a_test_calls_me()
""")
    _mk(root, "commands/widget.md",
        "Run `modules.widget.engine.only_prose_mentions_me()` by hand when needed.\n")


def gate_resolver_shapes(root: Path) -> None:
    """Every import shape resolves, or the sweep accuses live code of being dead.

    This is the gate that would have caught the alias miss recorded 2026-09-10 and made
    again 2026-09-11: both times a sweep matched the receiver against a hardcoded set of
    plausible names instead of the module's own bindings.
    """
    rows = {r["symbol"]: r["state"] for r in cr.scan(root) if r["unit"] == "widget/engine"}
    expect = {
        "called_plainly": cr.CALLED,
        "called_via_alias": cr.CALLED,
        "called_through_module_attr": cr.CALLED,
        "called_after_rebinding": cr.CALLED,
        "never_called_anywhere": cr.NEVER,
        "only_a_test_calls_me": cr.TEST_ONLY,
        "only_prose_mentions_me": cr.PROSE_ONLY,
    }
    wrong = {k: (rows.get(k), v) for k, v in expect.items() if rows.get(k) != v}
    if not wrong:
        _ok("V-CALLABLE-RESOLVER-SHAPES",
            "plain / aliased / module-attr / rebound imports all resolve CALLED; "
            "uncalled, test-only and prose-only each classify distinctly")
    else:
        _fail("V-CALLABLE-RESOLVER-SHAPES",
              "; ".join(f"{k}: got {got}, want {want}" for k, (got, want) in wrong.items()))


def gate_ratchet_growth(root: Path) -> None:
    """New unreached debt fails the gate; the frozen set alone does not."""
    inv = root / cr.INVENTORY
    inv.parent.mkdir(parents=True, exist_ok=True)
    frozen = {r["id"]: "frozen for the drill" for r in cr.gaps(root)}
    inv.write_text(json.dumps({"frozen": frozen}, indent=2), encoding="utf-8")

    clean = cr.ratchet(root)
    _mk(root, "modules/widget/engine.py",
        (root / "modules/widget/engine.py").read_text(encoding="utf-8")
        + "\n\ndef newly_added_and_uncalled():\n    return 8\n")
    grown = cr.ratchet(root)

    if clean["ok"] and not grown["ok"] \
            and "widget/engine::newly_added_and_uncalled" in grown["new"]:
        _ok("V-CALLABLE-RATCHET-GROWTH",
            f"frozen set alone is OK; one new uncalled export fails the gate "
            f"and is named ({len(grown['new'])} new)")
    else:
        _fail("V-CALLABLE-RATCHET-GROWTH",
              f"clean_ok={clean['ok']} grown_ok={grown['ok']} new={grown['new'][:3]}")


def gate_ratchet_stale(root: Path) -> None:
    """An entry that became reachable must fail, or the list becomes a permanent excuse.

    Held from one side only, an inventory rots: entries outlive their debts and the
    ratchet stops turning while still reporting green.
    """
    inv = root / cr.INVENTORY
    frozen = {r["id"]: "frozen for the drill" for r in cr.gaps(root)}
    frozen["widget/engine::called_plainly"] = "a debt that no longer exists"
    inv.write_text(json.dumps({"frozen": frozen}, indent=2), encoding="utf-8")

    res = cr.ratchet(root)
    if not res["ok"] and "widget/engine::called_plainly" in res["stale"]:
        _ok("V-CALLABLE-RATCHET-STALE",
            "an inventory entry whose symbol is now CALLED fails the gate by name")
    else:
        _fail("V-CALLABLE-RATCHET-STALE",
              f"ok={res['ok']} stale={res['stale'][:3]}")


def gate_store_context_is_not_a_call(root: Path) -> None:
    """Assigning to a name is not using it.

    `engine.dead = replacement` and `saved = engine.dead` both parse as an Attribute on a
    bound receiver. Counting the first marked a function CALLED by the act of OVERWRITING
    it -- an EXCUSING error, which is the direction nobody ever revisits.

    The control is the second half: a Load-context reference that is not a call (passing a
    function as a callback) must still count, or the repair would swing into accusing
    every legitimate non-invoking use.
    """
    _mk(root, "modules/widget/store.py", """
def overwritten_only():
    return 1


def read_but_not_called():
    return 2
""")
    _mk(root, "tools/caller_store.py", """
import modules.widget.store as st
st.overwritten_only = None
handler = st.read_but_not_called
""")
    rows = {r["symbol"]: r["state"] for r in cr.scan(root) if r["unit"] == "widget/store"}
    if rows.get("overwritten_only") == cr.NEVER \
            and rows.get("read_but_not_called") == cr.CALLED:
        _ok("V-CALLABLE-STORE-IS-NOT-USE",
            "assigning to a symbol does not mark it CALLED; reading one as a callback "
            "still does")
    else:
        _fail("V-CALLABLE-STORE-IS-NOT-USE",
              f"overwritten={rows.get('overwritten_only')} (want NEVER) "
              f"read={rows.get('read_but_not_called')} (want CALLED)")


def gate_freeze_refuses_new_debt(root: Path) -> None:
    """--freeze must not be the bypass that makes any red gate green.

    The ratchet compares against an editable snapshot, so re-freezing absorbed every new
    offender silently, with no wiring change and no record. A control anyone can disable
    by running one documented command is not a control.
    """
    inv = root / cr.INVENTORY
    inv.parent.mkdir(parents=True, exist_ok=True)
    inv.write_text(json.dumps({"frozen": {}}, indent=2), encoding="utf-8")

    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        # repo_root injected so this drill never touches the real tree. It did, once:
        # main() resolved _repo_root() unconditionally, and the first version of this
        # test rewrote the committed inventory as a side effect of asserting about it.
        code = cr.main(["--freeze"], repo_root=root)
    refused = code == 1 and "REFUSING" in buf.getvalue()
    # It must refuse WITHOUT having rewritten anything.
    still_empty = json.loads(inv.read_text(encoding="utf-8"))["frozen"] == {}
    if refused and still_empty:
        _ok("V-CALLABLE-FREEZE-REFUSES-NEW",
            "--freeze with unfrozen debt exits 1, names what it would absorb, and "
            "leaves the inventory untouched; --absorb-new is the explicit opt-in")
    else:
        _fail("V-CALLABLE-FREEZE-REFUSES-NEW",
              f"exit={code} refused={refused} inventory_untouched={still_empty}")


def gate_real_repo_positive_control() -> None:
    """The sweep must find a plausible population and a working resolver.

    NOT a floor on unreached count. That version penalised legitimate improvement: wire
    enough functions or delete enough dead code and the gate would go red for getting
    BETTER, which is a test that fights its own product. Detection capability is proven
    synthetically above, where it cannot decay; this control exists only to catch an
    enumerator or resolver that has stopped working, which shows up as an empty
    population or zero resolved callers.
    """
    rows = cr.scan()
    states = {r["state"] for r in rows}
    called = sum(1 for r in rows if r["state"] == cr.CALLED)
    unreached = sum(1 for r in rows if r["state"] in cr.UNREACHED)
    if len(rows) >= 500 and called >= 50:
        _ok("V-CALLABLE-REAL-REPO-CONTROL",
            f"{len(rows)} public symbols under modules/: {called} CALLED, "
            f"{unreached} unreached, states={sorted(states)}")
    else:
        _fail("V-CALLABLE-REAL-REPO-CONTROL",
              f"enumerator or resolver has stopped working: {len(rows)} symbols "
              f"(want >=500), {called} called (want >=50), states={sorted(states)}")


def main() -> int:
    print("V-CALLABLE gates (callable liveness: an exported function is not a called one)")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _synthetic(root)
        gate_resolver_shapes(root)
        gate_store_context_is_not_a_call(root)
        gate_ratchet_growth(root)
        gate_ratchet_stale(root)
        gate_freeze_refuses_new_debt(root)
    gate_real_repo_positive_control()

    total = PASSES + FAILS
    print(f"CALLABLE_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
