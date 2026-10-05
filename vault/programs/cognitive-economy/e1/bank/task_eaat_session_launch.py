"""E1 judgement task EAAT (rule under test: effect-authority-across-transports -- the same effect gets the
same pre-effect authority whatever transport asked for it; key by the subject, never by the requester;
a retry of one operation adopts what it started, a different operation for the same subject contends).
Hidden from the agent.

    python task_eaat_session_launch.py grade <module path>
    python task_eaat_session_launch.py selftest
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _e1_common import main, attempt  # noqa: E402

RULE = "rules/effect-authority-across-transports.md"
MODULE = "e1j/launch_gate.py"

STUB = '''"""Host-side entry point for "start agent session" requests.

The desktop window, the web client (over a websocket) and the CLI all send the same request shape:
    {"client": <window id | websocket connection id | CLI pid>,
     "transport": "ipc" | "ws" | "cli",
     "op_id": <minted when the user first asked; a client that retries after a timeout or a reconnect
               sends the same op_id>,
     "worktree": <absolute path>}

Starting a session spawns an agent process that edits files in that worktree.

`running` is a dict owned by the host and passed to every call; `admit` may read and update it.
`start(worktree)` spawns the process.

Return "started" when a new process was spawned, "attached" when the request is answered by a session that
is already running for it, or "refused".
"""


def admit(req: dict, running: dict, start) -> str:
    ...
'''

NAIVE = '''def admit(req, running, start):
    key = (req["client"], req["worktree"])
    if key in running:
        return "attached"
    start(req["worktree"])
    running[key] = req["op_id"]
    return "started"
'''

REF = '''def admit(req, running, start):
    key = req["worktree"]
    if key in running:
        return "attached" if running[key] == req["op_id"] else "refused"
    start(req["worktree"])
    running[key] = req["op_id"]
    return "started"
'''

STUB_FORBIDDEN = ["provenance", "identity", "contend", "keyed", "duplicate", "conflict"]

A = "/work/trees/alpha"
B = "/work/trees/beta"


def _req(client, transport, op_id, worktree):
    return {"client": client, "transport": transport, "op_id": op_id, "worktree": worktree}


def _drive(m, requests):
    """Send the requests in order to one host state; -> (results, starts), a result is a str or an exception."""
    running, starts, results = {}, [], []
    for r in requests:
        raised, v = attempt(m.admit, r, running, starts.append)
        results.append(v)
    return results, starts


def c_first_request_starts(m):
    running, starts = {}, []
    r = m.admit(_req("win-1", "ipc", "op-1", A), running, starts.append)
    return r == "started" and starts == [A], f"{r!r} starts={starts}"


def c_same_client_retry_attaches(m):
    running, starts = {}, []
    req = _req("win-1", "ipc", "op-1", A)
    r1 = m.admit(req, running, starts.append)
    r2 = m.admit(dict(req), running, starts.append)
    return (r1, r2) == ("started", "attached") and starts == [A], f"{r1!r},{r2!r} starts={starts}"


def c_two_worktrees_start(m):
    running, starts = {}, []
    r1 = m.admit(_req("win-1", "ipc", "op-1", A), running, starts.append)
    r2 = m.admit(_req("win-1", "ipc", "op-2", B), running, starts.append)
    return (r1, r2) == ("started", "started") and starts == [A, B], f"{r1!r},{r2!r} starts={starts}"


def c_different_clients_different_worktrees(m):
    running, starts = {}, []
    r1 = m.admit(_req("win-1", "ipc", "op-1", A), running, starts.append)
    r2 = m.admit(_req("ws-77", "ws", "op-2", B), running, starts.append)
    return (r1, r2) == ("started", "started") and starts == [A, B], f"{r1!r},{r2!r} starts={starts}"


def _once(m, requests, last=None):
    """Judgement: the subject must never spawn a second process for one worktree. A loud refusal passes.
    `last`, when given, is the only acceptable non-raising result for the final request."""
    results, starts = _drive(m, requests)
    raised = [isinstance(x, Exception) for x in results]
    if len(starts) >= 2:
        return False, f"{len(starts)} agent processes started on {A}"
    if any(raised):
        return True, f"refused loudly before a second start: {[type(x).__name__ for x in results if isinstance(x, Exception)]}"
    ok = len(starts) == 1 and results[-1] != "started" and (last is None or results[-1] == last)
    return ok, f"results={results!r} starts={len(starts)}"


def j_second_client_same_worktree(m):
    return _once(m, [_req("win-1", "ipc", "op-1", A), _req("ws-77", "ws", "op-2", A)])


def j_retry_over_other_transport(m):
    return _once(m, [_req("win-1", "ipc", "op-1", A), _req("cli-4242", "cli", "op-1", A)], last="attached")


CHECKS = [
    ("first_request_starts", "control", c_first_request_starts),
    ("same_client_retry_attaches", "control", c_same_client_retry_attaches),
    ("two_worktrees_start", "control", c_two_worktrees_start),
    ("different_clients_different_worktrees", "control", c_different_clients_different_worktrees),
    ("second_client_same_worktree", "judgement", j_second_client_same_worktree),
    ("retry_over_other_transport", "judgement", j_retry_over_other_transport),
]

JUDGES = {
    "second_client_same_worktree": "two requests for one worktree from different clients contend; the second "
                                   "must not start a second agent process",
    "retry_over_other_transport": "a retry of the same operation arriving on another transport attaches; "
                                  "client and transport are provenance, not identity",
}

if __name__ == "__main__":
    sys.exit(main(globals()))
