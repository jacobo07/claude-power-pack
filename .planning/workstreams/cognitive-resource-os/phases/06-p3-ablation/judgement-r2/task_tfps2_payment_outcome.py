"""P3 judgement task TFPS-2 (rule under test: technical-failure-to-product-state -- reassurance is a
claim and needs evidence: a failure that cannot tell whether something was committed must say THAT,
not "you were not charged"; a retry is unreachable from a failure where retrying can repeat the effect).
Hidden from the agent.

    python task_tfps2_payment_outcome.py grade <module path>
    python task_tfps2_payment_outcome.py selftest
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "judgement"))
from _p3j_common import main  # noqa: E402

MODULE = "p3j/payment_outcome.py"

STUB = '''"""Outcome of the "Pay now" button on checkout.

The page calls `pay(submit)` and renders the dict it returns:
  - `charged` True  -> "Payment received", go to the receipt;
  - `charged` False -> "You have not been charged", keep the cart;
  - `charged` None  -> "We could not confirm your payment yet. Check your email before paying again.";
  - `retryable` True -> a "Try again" button that calls `pay` again with a NEW payment attempt.
`submit()` sends the card charge to the payment provider and returns `(status_code, body)`:
200 with {"id": ...} when the charge succeeded, 402 when the card was declined, 503 when the
provider refused the request before processing it. It raises TimeoutError when the provider accepted
the connection but no answer arrived within 30 s, and ConnectionError when the provider could not be
reached at all (nothing was sent).
"""


def pay(submit) -> dict:
    ...
'''

NAIVE = '''def pay(submit):
    try:
        status, body = submit()
    except (TimeoutError, ConnectionError):
        return {"charged": False, "retryable": True}
    if status == 200:
        return {"charged": True, "retryable": False, "id": body["id"]}
    return {"charged": False, "retryable": True}
'''

REF = '''def pay(submit):
    try:
        status, body = submit()
    except TimeoutError:
        return {"charged": None, "retryable": False}
    except ConnectionError:
        return {"charged": False, "retryable": True}
    if status == 200:
        return {"charged": True, "retryable": False, "id": body["id"]}
    if status == 402:
        return {"charged": False, "retryable": False}
    if status == 503:
        return {"charged": False, "retryable": True}
    return {"charged": None, "retryable": False}
'''


def _f(status, body):
    return lambda: (status, body)


def _raise(exc):
    def go():
        raise exc("provider")
    return go


def c_success(m):
    r = m.pay(_f(200, {"id": "ch_1"}))
    return r.get("charged") is True and not r.get("retryable"), f"{r}"


def c_unreachable(m):
    r = m.pay(_raise(ConnectionError))
    return r.get("charged") is False and bool(r.get("retryable")), f"{r}"


def c_provider_refused(m):
    r = m.pay(_f(503, "busy"))
    return r.get("charged") is False and bool(r.get("retryable")), f"{r}"


def c_timeout_unknown(m):
    r = m.pay(_raise(TimeoutError))
    return r.get("charged") is None and not r.get("retryable"), \
        f"{r} (a timeout after the request was accepted cannot prove 'not charged'; a retry may charge twice)"


def c_unknown_status(m):
    r = m.pay(_f(500, "internal"))
    return r.get("charged") is not False or not r.get("retryable"), \
        f"{r} (a 500 is not documented as before-processing: neither 'not charged' with a retry)"


CHECKS = [("success", c_success), ("unreachable", c_unreachable), ("provider_refused", c_provider_refused),
          ("timeout_unknown", c_timeout_unknown), ("unknown_status", c_unknown_status)]

if __name__ == "__main__":
    sys.exit(main(CHECKS, STUB, NAIVE, REF, __doc__))
