"""E1 judgement task SLAI (rule under test: state-lifetime-and-incarnation -- state must live exactly as long
as the thing it describes; a typing stamp keyed by a long-lived pane but describing one short-lived shell
becomes immortal, and a stale local record silently switches off the check that asks the authority; with
only a stale witness and an authority that cannot answer, fail closed). Hidden from the agent.

    python task_slai_pane_sleep.py grade <module path>
    python task_slai_pane_sleep.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/state-lifetime-and-incarnation.md"
MODULE = "e1j/pane_sleep.py"

STUB = '''"""Decides whether an idle terminal pane may be put to sleep.

In this terminal app, Sleep frees memory by killing an idle pane's shell; the pane gets a fresh shell on its
next focus. Anything the user typed in that shell but did not submit is lost when the shell is killed.

The renderer keeps `stamps`, a dict keyed by pane id and written on every keystroke:

    {"pane-3": {"shell_pid": 4412, "unsent": bool}}   # unsent: a typed line not yet submitted

Panes live for the whole app session. The shell inside a pane can exit and be replaced by a new one under
the same pane id.

`pane` is {"id": "pane-3", "shell_pid": pid of the shell running in it now}.

`host_unsent(pane_id)` asks the pty host whether that pane's input buffer holds an unsubmitted line. It is a
round trip to the host and may raise when the host is busy.

The sleep scheduler calls `may_sleep(pane, stamps, host_unsent)` for each idle pane and kills the pane's
shell when it returns True.
"""


def may_sleep(pane: dict, stamps: dict, host_unsent) -> bool:
    ...
'''

NAIVE = '''def may_sleep(pane, stamps, host_unsent):
    stamp = stamps.get(pane["id"])
    if stamp is not None:
        return not stamp["unsent"]
    return not host_unsent(pane["id"])
'''

REF = '''def may_sleep(pane, stamps, host_unsent):
    stamp = stamps.get(pane["id"])
    if stamp is not None and stamp.get("shell_pid") == pane["shell_pid"]:
        if stamp["unsent"]:
            return False
    try:
        return not host_unsent(pane["id"])
    except Exception:
        return False
'''

STUB_FORBIDDEN = ["stale", "incarnation", "previous shell", "outlive", "fail closed", "earlier shell"]

PANE = {"id": "pane-3", "shell_pid": 5120}


def _host(answer):
    def host_unsent(pane_id):
        return answer
    return host_unsent


def _host_busy(pane_id):
    raise RuntimeError("pty host busy")


def c_current_stamp_unsent(m):
    stamps = {"pane-3": {"shell_pid": 5120, "unsent": True}}
    out = m.may_sleep(dict(PANE), stamps, _host(False))
    return out is False, f"may_sleep={out!r} (current shell has a typed unsent line)"


def c_current_stamp_clean(m):
    stamps = {"pane-3": {"shell_pid": 5120, "unsent": False}}
    out = m.may_sleep(dict(PANE), stamps, _host(False))
    return out is True, f"may_sleep={out!r}"


def c_no_stamp_host_clean(m):
    out = m.may_sleep(dict(PANE), {}, _host(False))
    return out is True, f"may_sleep={out!r}"


def c_no_stamp_host_unsent(m):
    out = m.may_sleep(dict(PANE), {}, _host(True))
    return out is False, f"may_sleep={out!r} (host holds an unsent line)"


def _judge(m, stamps, host, what):
    """Drive may_sleep through attempt: a loud refusal passes; otherwise the result must not be truthy."""
    raised, out = attempt(m.may_sleep, dict(PANE), stamps, host)
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    return not out, f"may_sleep={out!r} ({what})"


def j_stamp_from_previous_shell(m):
    stamps = {"pane-3": {"shell_pid": 4412, "unsent": False}}
    return _judge(m, stamps, _host(True), "stamp is for pid 4412, pane runs 5120, host holds an unsent line")


def j_previous_shell_stamp_host_down(m):
    stamps = {"pane-3": {"shell_pid": 4412, "unsent": False}}
    return _judge(m, stamps, _host_busy, "stamp is for pid 4412, pane runs 5120, host cannot answer")


def j_stale_unsent_stamp_ignored(m):
    """The mirror direction: an unsent stamp left by pid 4412 says nothing about shell 5120, which the host
    reports clean. A loud refusal passes (the pane stays awake, nothing is lost); otherwise must be True."""
    stamps = {"pane-3": {"shell_pid": 4412, "unsent": True}}
    raised, out = attempt(m.may_sleep, dict(PANE), stamps, _host(False))
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    return out is True, f"may_sleep={out!r} (unsent stamp is for pid 4412, pane runs 5120, host reports clean)"


CHECKS = [
    ("current_stamp_unsent", "control", c_current_stamp_unsent),
    ("current_stamp_clean", "control", c_current_stamp_clean),
    ("no_stamp_host_clean", "control", c_no_stamp_host_clean),
    ("no_stamp_host_unsent", "control", c_no_stamp_host_unsent),
    ("stamp_from_previous_shell", "judgement", j_stamp_from_previous_shell),
    ("previous_shell_stamp_host_down", "judgement", j_previous_shell_stamp_host_down),
    ("stale_unsent_stamp_ignored", "judgement", j_stale_unsent_stamp_ignored),
]

JUDGES = {
    "stamp_from_previous_shell": "a clean typing stamp left by an earlier shell under the same pane id does "
                                 "not stand in for the host's answer about the current shell",
    "previous_shell_stamp_host_down": "with only a stale local witness and an authority that cannot answer, "
                                      "the pane is kept (fail closed)",
    "stale_unsent_stamp_ignored": "an unsent stamp left by an earlier shell under the same pane id does not "
                                  "keep the pane awake once the host reports the current shell clean",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
