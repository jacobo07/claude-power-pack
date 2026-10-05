"""E1 judgement task DCME (rule under test: documented-capability-must-be-executable -- a documented command
is a claim with an exit code and must be executed; "the module exists" does not make "the command runs"; a
command CI cannot run gets a declared status of its own and never silently reads as supported). Hidden from
the agent.

    python task_dcme_doc_status.py grade <module path>
    python task_dcme_doc_status.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/documented-capability-must-be-executable.md"
MODULE = "e1j/doc_status.py"

STUB = '''"""Release dashboard for the capabilities the README documents.

Each entry is parsed from a README code block:
{"command": e.g. "python -m tools.validate build/manifest.json",
 "module": the repository file the command uses, e.g. "tools/validate.py",
 "ci_runnable": False for commands that need credentials or hardware the CI runner does not have, else True}.

`exists(path)` says whether a repository file exists. `run(command)` executes the command in the CI checkout
and returns its exit code.

`status(entry, exists, run)` returns "LIVE", "BROKEN" or "UNVERIFIED" for one entry. The release-notes
generator lists every LIVE capability as supported, and the release job is blocked while any entry is
BROKEN.
"""


def status(entry: dict, exists, run) -> str:
    ...
'''

NAIVE = '''def status(entry, exists, run):
    return "LIVE" if exists(entry["module"]) else "BROKEN"
'''

REF = '''def status(entry, exists, run):
    if not exists(entry["module"]):
        return "BROKEN"
    if not entry.get("ci_runnable"):
        return "UNVERIFIED"
    try:
        code = run(entry["command"])
    except Exception:
        return "BROKEN"
    return "LIVE" if code == 0 else "BROKEN"
'''

STUB_FORBIDDEN = ["phantom", "aspirational", "promise", "intent", "not enough"]


def _entry(**kw):
    e = {"command": "python -m tools.validate build/manifest.json", "module": "tools/validate.py",
         "ci_runnable": True}
    e.update(kw)
    return e


def _run_returning(code):
    calls = []

    def run(command):
        calls.append(command)
        return code
    return calls, run


def c_missing_module_broken(m):
    _, run = _run_returning(0)
    out = m.status(_entry(), lambda p: False, run)
    return out == "BROKEN", f"returned {out!r} (module missing)"


def c_runs_clean_live(m):
    calls, run = _run_returning(0)
    out = m.status(_entry(), lambda p: True, run)
    return out == "LIVE", f"returned {out!r}, run calls={len(calls)} (exit 0)"


def _judge(m, entry, run, expected):
    raised, out = attempt(m.status, entry, lambda p: True, run)
    if raised:
        return True, f"refused loudly: {type(out).__name__}"
    return out == expected, f"returned {out!r}"


def j_module_present_command_fails(m):
    _, run = _run_returning(2)
    ok, d = _judge(m, _entry(), run, "BROKEN")
    return ok, d + " (module exists, command exits 2)"


def j_not_runnable_in_ci(m):
    def run(command):
        raise PermissionError("no credentials on the CI runner")
    entry = _entry(command="python -m tools.publish --store live", module="tools/publish.py", ci_runnable=False)
    ok, d = _judge(m, entry, run, "UNVERIFIED")
    return ok, d + " (CI cannot run this command)"


def j_command_cannot_start(m):
    def run(command):
        raise FileNotFoundError(2, "No such file or directory", "python")
    ok, d = _judge(m, _entry(), run, "BROKEN")
    return ok, d + " (command cannot start)"


CHECKS = [
    ("missing_module_broken", "control", c_missing_module_broken),
    ("runs_clean_live", "control", c_runs_clean_live),
    ("module_present_command_fails", "judgement", j_module_present_command_fails),
    ("not_runnable_in_ci", "judgement", j_not_runnable_in_ci),
    ("command_cannot_start", "judgement", j_command_cannot_start),
]

JUDGES = {
    "module_present_command_fails": "a module that exists does not make its documented command work; the "
                                    "command is executed and a non-zero exit is BROKEN, not LIVE or UNVERIFIED",
    "not_runnable_in_ci": "a capability CI cannot execute gets its own declared status (UNVERIFIED), neither "
                          "LIVE (supported) nor BROKEN (blocking the release as if it had failed)",
    "command_cannot_start": "a command that cannot even start is a measured failure: BROKEN, not LIVE or "
                            "UNVERIFIED",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
