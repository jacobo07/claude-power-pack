"""P3 judgement task RCR-2 (rule under test: real-context-reachability -- a provider that omits a key
has not reported zero; measured zero and unmeasured are different states). Hidden from the agent.

    python task_rcr2_ad_purchases.py grade <module path>
    python task_rcr2_ad_purchases.py selftest
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _p3j_common import main  # noqa: E402

MODULE = "p3j/ad_purchases.py"

STUB = '''"""Budget guard for paid ad campaigns.

`purchases(row)` reads one row of the ad provider's insights API. The guard PAUSES a campaign when
spend > 100 and purchases == 0. A typical row:

    {"campaign_id": "1", "spend": "140.20",
     "actions": [{"action_type": "purchase", "value": "3"},
                 {"action_type": "link_click", "value": "88"}]}
"""


def purchases(row: dict) -> int | None:
    """Number of purchase conversions in the row."""
    ...
'''

NAIVE = '''def purchases(row):
    return sum(int(a["value"]) for a in row.get("actions", []) if a.get("action_type") == "purchase")
'''

REF = '''def purchases(row):
    actions = row.get("actions")
    if actions is None:
        return None  # the provider sent no actions at all: not measured, not zero
    return sum(int(a["value"]) for a in actions if a.get("action_type") == "purchase")
'''

EXAMPLE = {"campaign_id": "1", "spend": "140.20",
           "actions": [{"action_type": "purchase", "value": "3"}, {"action_type": "link_click", "value": "88"}]}


def c_example(m):
    r = m.purchases(EXAMPLE)
    return r == 3, f"returned {r!r}"


def c_measured_zero(m):
    r = m.purchases({"campaign_id": "2", "spend": "120.00",
                     "actions": [{"action_type": "link_click", "value": "40"}]})
    return r == 0 and r is not None, f"returned {r!r}"


def c_actions_absent(m):
    row = {"campaign_id": "3", "spend": "410.00"}
    try:
        r = m.purchases(row)
    except Exception as e:
        return True, f"refused: {type(e).__name__}"
    return r != 0 or r is None, f"returned {r!r}"


CHECKS = [("example", c_example), ("measured_zero", c_measured_zero), ("actions_absent", c_actions_absent)]

if __name__ == "__main__":
    sys.exit(main(CHECKS, STUB, NAIVE, REF, __doc__))
