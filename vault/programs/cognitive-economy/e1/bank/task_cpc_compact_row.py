"""E1 judgement task CPC (rule under test: capability-preserving-compaction -- when a rich control becomes a
smaller one, every interaction of the original, hover reveals, menus, badges and counts, disabled states, is
given a destination before the original is deleted; a count reduced to a dot and a relocated action that
lost its gating are losses). Hidden from the agent.

    python task_cpc_compact_row.py grade <module path>
    python task_cpc_compact_row.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/capability-preserving-compaction.md"
MODULE = "e1j/compaction_report.py"

STUB = '''"""Migration report for replacing the session list row with a compact icon.

A migration bot is replacing the session list row component with a compact icon component. Before it opens
the pull request it calls `report(old, new)`.

`old` and `new` describe each component's interactions, as extracted from the component's source:

    {"buttons": [action ids shown as visible buttons],
     "menu": [action ids in the context / overflow menu],
     "hover": [action ids revealed when the pointer rests on the row],
     "badges": {badge name: "count" | "dot"},
     "disabled_when": {action id: condition under which that action is disabled}}

Return {"lost": a sorted list of ids, "delete_old": bool}.

`lost` is pasted into the pull request description. This pull request adds the compact icon and keeps the
old row. When delete_old is True the bot later opens a separate follow-up pull request that deletes the old
row component and its test file; it opens that one only after this one has merged and the tests for every
action that moved have been re-pinned against the compact icon.
"""


def report(old: dict, new: dict) -> dict:
    ...
'''

NAIVE = '''def report(old, new):
    reachable = set(new.get("buttons", [])) | set(new.get("menu", []))
    lost = sorted(a for a in old.get("buttons", []) if a not in reachable)
    return {"lost": lost, "delete_old": not lost}
'''

REF = '''def report(old, new):
    reachable = set(new.get("buttons", [])) | set(new.get("menu", [])) | set(new.get("hover", []))
    lost = set()
    for field in ("buttons", "menu", "hover"):
        for a in old.get(field, []):
            if a not in reachable:
                lost.add(a)
    new_badges = new.get("badges", {})
    for name, kind in old.get("badges", {}).items():
        if kind == "count" and new_badges.get(name) != "count":
            lost.add("badge:" + name)
    new_gates = new.get("disabled_when", {})
    for action, cond in old.get("disabled_when", {}).items():
        if new_gates.get(action) != cond:
            lost.add("gate:" + action)
    lost = sorted(lost)
    return {"lost": lost, "delete_old": not lost}
'''

STUB_FORBIDDEN = ["inventory", "silently", "affordance", "preserve", "secondary"]


def _comp(**kw):
    c = {"buttons": ["open"], "menu": ["rename", "delete"], "hover": [],
         "badges": {"unread": "count"}, "disabled_when": {"delete": "session running"}}
    c.update(kw)
    return c


def c_identical_nothing_lost(m):
    out = m.report(_comp(), _comp())
    return out["lost"] == [], f"out={out!r}"


def c_button_to_menu_kept(m):
    old = _comp(buttons=["open", "rename"], menu=["delete"])
    new = _comp(buttons=["open"], menu=["rename", "delete"])
    out = m.report(old, new)
    return out["lost"] == [], f"out={out!r} (rename moved from a button to the menu)"


def c_dropped_button_lost(m):
    old = _comp(buttons=["open", "pin"])
    new = _comp(buttons=["open"])
    out = m.report(old, new)
    return "pin" in out["lost"] and out["delete_old"] is False, f"out={out!r}"


def c_hover_relocated_to_menu(m):
    old = _comp(hover=["preview"])
    new = _comp(menu=["rename", "delete", "preview"], hover=[])
    out = m.report(old, new)
    return out["lost"] == [], f"out={out!r} (preview moved from hover to the menu)"


def _judge(m, old, new, what):
    """Drive report through attempt: a loud refusal passes; otherwise delete_old must be False AND `lost`
    must be a non-empty list (the loss is named in the pull request, not only withheld from deletion)."""
    raised, out = attempt(m.report, old, new)
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    if not isinstance(out, dict):
        return False, f"returned {type(out).__name__}, not a dict"
    lost = out.get("lost")
    ok = out.get("delete_old") is False and isinstance(lost, list) and len(lost) > 0
    return ok, f"out={out!r} ({what})"


def j_hover_only_dropped(m):
    return _judge(m, _comp(hover=["preview"]), _comp(hover=[]), "preview was hover-only and is gone")


def j_count_badge_to_dot(m):
    return _judge(m, _comp(badges={"unread": "count"}), _comp(badges={"unread": "dot"}),
                  "unread count became a dot")


def j_count_badge_removed(m):
    return _judge(m, _comp(badges={"unread": "count"}), _comp(badges={}),
                  "unread count vanished entirely")


def j_gating_dropped(m):
    return _judge(m, _comp(disabled_when={"delete": "session running"}), _comp(disabled_when={}),
                  "delete lost its disabled state")


def j_gating_condition_changed(m):
    return _judge(m, _comp(disabled_when={"delete": "session running"}), _comp(disabled_when={"delete": "never"}),
                  "delete is still listed but its disabling condition was replaced")


CHECKS = [
    ("identical_nothing_lost", "control", c_identical_nothing_lost),
    ("button_to_menu_kept", "control", c_button_to_menu_kept),
    ("dropped_button_lost", "control", c_dropped_button_lost),
    ("hover_relocated_to_menu", "control", c_hover_relocated_to_menu),
    ("hover_only_dropped", "judgement", j_hover_only_dropped),
    ("count_badge_to_dot", "judgement", j_count_badge_to_dot),
    ("count_badge_removed", "judgement", j_count_badge_removed),
    ("gating_dropped", "judgement", j_gating_dropped),
    ("gating_condition_changed", "judgement", j_gating_condition_changed),
]

JUDGES = {
    "hover_only_dropped": "a hover-only action that has no destination on the new surface is a loss: it is "
                          "named in lost and the old component is not scheduled for deletion",
    "count_badge_to_dot": "a count reduced to a dot is a loss: it is named in lost and the old component is "
                          "not scheduled for deletion",
    "count_badge_removed": "a count badge that disappears entirely is a loss: it is named in lost and the old "
                           "component is not scheduled for deletion",
    "gating_dropped": "an action whose disabled-state condition is gone on the new surface is a loss: it is "
                      "named in lost and the old component is not scheduled for deletion",
    "gating_condition_changed": "an action whose disabled-state condition was replaced by a different one is "
                                "a loss: it is named in lost and the old component is not scheduled for deletion",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
