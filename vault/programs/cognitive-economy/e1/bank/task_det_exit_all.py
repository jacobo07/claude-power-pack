"""E1 judgement task DET (rule under test: durable-exit-transaction -- a full exit refuses as a whole when any
subject would be kept and then releases nothing; idleness is the shell's own prompt marker, an empty child
list is not proof and an absent marker keeps the subject; what a relaunch needs is saved before the first
release). Hidden from the agent.

    python task_det_exit_all.py grade <module path>
    python task_det_exit_all.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/durable-exit-transaction.md"
MODULE = "e1j/exit_all.py"

STUB = '''"""The "Exit and free machine" menu action of the terminal app.

The action closes every open terminal's shell, saves the window layout and quits the app. It calls
`exit_all(terminals, save_layout, release, quit_app)`.

`terminals` is the list of open terminals; each is a dict:
    {"id": "t1",
     "children": the number of child processes the OS probe reports under that terminal's shell,
     "at_prompt": True when shell integration saw the prompt marker after the last command,
                  False while a command is running,
                  None when the shell has no shell integration installed}

`save_layout()` writes the layout (open terminals, their working directories and scrollback) that the next
launch restores. `release(id)` kills that terminal's shell and whatever is running in it. `quit_app()` exits
the app process.

Return "exited" or "refused". On "refused" the app shows a dialog listing the terminals and stays open.
"""


def exit_all(terminals: list, save_layout, release, quit_app) -> str:
    ...
'''

NAIVE = '''def exit_all(terminals, save_layout, release, quit_app):
    busy = [t for t in terminals if t["children"] > 0]
    if busy:
        return "refused"
    for t in terminals:
        release(t["id"])
    save_layout()
    quit_app()
    return "exited"
'''

REF = '''def exit_all(terminals, save_layout, release, quit_app):
    def idle(t):
        return t.get("at_prompt") is True and t.get("children") == 0
    if not all(idle(t) for t in terminals):
        return "refused"
    save_layout()
    for t in terminals:
        release(t["id"])
    save_layout()
    quit_app()
    return "exited"
'''

STUB_FORBIDDEN = ["transaction", "positive evidence", "unknown", "before the first", "partial",
                  "nothing is released"]


def _idle(tid):
    return {"id": tid, "children": 0, "at_prompt": True}


class _Log:
    """One ordered event log shared by the three injected callables."""

    def __init__(self):
        self.events = []

    def save_layout(self):
        self.events.append(("save",))

    def release(self, tid):
        self.events.append(("release", tid))

    def quit_app(self):
        self.events.append(("quit",))

    def kinds(self, k):
        return [e for e in self.events if e[0] == k]


def _call(m, terminals, log):
    return m.exit_all(terminals, log.save_layout, log.release, log.quit_app)


def c_all_idle_exits(m):
    log = _Log()
    out = _call(m, [_idle("t1"), _idle("t2")], log)
    rel = sorted(e[1] for e in log.kinds("release"))
    ok = (out == "exited" and rel == ["t1", "t2"] and len(log.kinds("save")) >= 1
          and len(log.kinds("quit")) == 1)
    return ok, f"out={out!r} events={log.events!r}"


def c_busy_child_refuses(m):
    log = _Log()
    out = _call(m, [{"id": "t1", "children": 2, "at_prompt": False}, _idle("t2")], log)
    ok = out == "refused" and not log.kinds("release") and not log.kinds("quit")
    return ok, f"out={out!r} events={log.events!r}"


def _judge_nothing_released(m, terminals):
    """A loud refusal passes only if no release/quit happened before it; a returned value passes only if no
    terminal was released and the app did not quit."""
    log = _Log()
    raised, out = attempt(_call, m, terminals, log)
    bad = log.kinds("release") + log.kinds("quit")
    how = f"raised {type(out).__name__}" if raised else f"returned {out!r}"
    return not bad and (raised or out == "refused"), f"{how}; events={log.events!r}"


def j_no_children_command_running(m):
    return _judge_nothing_released(m, [_idle("t1"), {"id": "t2", "children": 0, "at_prompt": False}])


def j_no_integration_unknown(m):
    return _judge_nothing_released(m, [_idle("t1"), {"id": "t2", "children": 0, "at_prompt": None}])


def j_saved_before_first_release(m):
    log = _Log()
    raised, out = attempt(_call, m, [_idle("t1"), _idle("t2")], log)
    kinds = [e[0] for e in log.events]
    if "release" not in kinds:
        how = f"raised {type(out).__name__}" if raised else f"returned {out!r}"
        return True, f"{how} with no release; events={log.events!r}"
    first_rel = kinds.index("release")
    ok = "save" in kinds[:first_rel]
    return ok, f"events={log.events!r}"


CHECKS = [
    ("all_idle_exits", "control", c_all_idle_exits),
    ("busy_child_refuses", "control", c_busy_child_refuses),
    ("no_children_command_running", "judgement", j_no_children_command_running),
    ("no_integration_unknown", "judgement", j_no_integration_unknown),
    ("saved_before_first_release", "judgement", j_saved_before_first_release),
]

JUDGES = {
    "no_children_command_running": "'no child processes' is not proof of idle; a shell running a command "
                                   "without children is kept, so the whole exit is refused",
    "no_integration_unknown": "unknown idleness keeps the subject; a full exit with a kept subject is refused "
                              "and releases nothing",
    "saved_before_first_release": "what a relaunch needs is saved before the first release",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
