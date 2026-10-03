"""P3 judgement task TFPS-1 (rule under test: technical-failure-to-product-state -- classify a
failure at the one boundary that sees the status; EMPTY only from a SUCCESS; the failure arm carries
no transport text for the surface to print; a retry is unreachable from a non-retryable failure).
Hidden from the agent.

    python task_tfps1_orders_state.py grade <module path>
    python task_tfps1_orders_state.py selftest
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "judgement"))
from _p3j_common import main  # noqa: E402

MODULE = "p3j/orders_state.py"

STUB = '''"""State for the "Your orders" panel of the customer portal.

The panel calls `orders_state(fetch)` and renders the dict it returns:
  - kind "ready": the list in `orders`;
  - kind "empty": the sentence "You have no orders yet.";
  - any other kind: the text in `message` if present, else a generic apology;
  - a Retry button whenever `retryable` is true.
`fetch()` performs GET /api/orders and returns `(status_code, body)` where body is the decoded JSON
on 200 and the raw response text otherwise. It raises ConnectionError when the server is unreachable.
"""


def orders_state(fetch) -> dict:
    ...
'''

NAIVE = '''def orders_state(fetch):
    try:
        status, body = fetch()
    except ConnectionError as e:
        return {"kind": "error", "message": str(e), "retryable": True}
    if status != 200:
        return {"kind": "error", "message": f"Error {status}: {body}", "retryable": True}
    if not body:
        return {"kind": "empty"}
    return {"kind": "ready", "orders": body}
'''

REF = '''def orders_state(fetch):
    try:
        status, body = fetch()
    except ConnectionError:
        return {"kind": "offline", "retryable": True, "cause": {"kind": "connection"}}
    if status == 200:
        if isinstance(body, list):
            return {"kind": "ready", "orders": body} if body else {"kind": "empty"}
        return {"kind": "error", "retryable": False, "cause": {"status": status}}
    if status in (401, 403):
        return {"kind": "signed_out", "retryable": False, "cause": {"status": status}}
    if status >= 500 or status == 429:
        return {"kind": "unavailable", "retryable": True, "cause": {"status": status, "body": body}}
    return {"kind": "error", "retryable": False, "cause": {"status": status, "body": body}}
'''

TRACE = "Traceback (most recent call last):\n  File app.py\npsycopg2.OperationalError: could not connect"


def _f(status, body):
    return lambda: (status, body)


def _raise():
    raise ConnectionError("[WinError 10061] No connection could be made")


def _leaks(state, *needles):
    shown = str(state.get("message", ""))
    return [n for n in needles if n and n in shown]


def c_ready(m):
    s = m.orders_state(_f(200, [{"id": 1}]))
    return s.get("kind") == "ready" and s.get("orders") == [{"id": 1}], f"{s}"


def c_empty(m):
    s = m.orders_state(_f(200, []))
    return s.get("kind") == "empty", f"{s}"


def c_server_error_not_empty_no_leak(m):
    s = m.orders_state(_f(500, TRACE))
    leak = _leaks(s, "Traceback", "OperationalError", "500")
    return s.get("kind") not in ("empty", "ready") and not leak, f"kind={s.get('kind')} leaked={leak}"


def c_offline_no_leak_retryable(m):
    s = m.orders_state(_raise)
    leak = _leaks(s, "WinError", "10061", "ConnectionError")
    return s.get("kind") not in ("empty", "ready") and not leak and bool(s.get("retryable")), \
        f"kind={s.get('kind')} retryable={s.get('retryable')} leaked={leak}"


def c_signed_out_not_retryable(m):
    s = m.orders_state(_f(401, "Unauthorized"))
    return s.get("kind") not in ("empty", "ready") and not s.get("retryable") and not _leaks(s, "401"), f"{s}"


CHECKS = [("ready", c_ready), ("empty", c_empty), ("server_error", c_server_error_not_empty_no_leak),
          ("offline", c_offline_no_leak_retryable), ("signed_out", c_signed_out_not_retryable)]

if __name__ == "__main__":
    sys.exit(main(CHECKS, STUB, NAIVE, REF, __doc__))
