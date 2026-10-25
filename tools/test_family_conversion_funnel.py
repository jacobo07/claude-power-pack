"""V-CONVF-* -- a FRESH session that builds a checkout or funnel inherits the conversion rules.

The seam is the real UserPromptSubmit hook (`hooks/gsd_x_tier.js` -> `modules/gsd_x/cli.py::
family_block`), spawned exactly as Claude Code spawns it: a JSON payload on stdin, a new session
id, and HOME pointed at an empty temp dir so no earlier offer counter or ledger can help or hide.
No prompt below mentions QuickLease or the mission that wrote the rules.

Mutation drill (run by hand 2026-10-25): removing vault/tower/families/conversion_funnel.json
turned V-CONVF-IN-en and V-CONVF-IN-es red (1/3), so the gate can return the other answer.

Run: python tools/test_family_conversion_funnel.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import uuid

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
HOOK = os.path.join(_PP_ROOT, "hooks", "gsd_x_tier.js")
STAMP = "Family baseline conversion_funnel/B"
RULES = [
    "conversion_funnel-synthetic-never-counted",
    "conversion_funnel-attribution-before-optimizing",
    "conversion_funnel-paid-is-a-server-event",
    "conversion_funnel-no-rate-below-sample",
    "conversion_funnel-name-the-emitting-page",
    "conversion_funnel-price-needs-exposure",
    "conversion_funnel-text-checks-have-goldens",
    "conversion_funnel-same-price-paid-metric",
]
CASES = [
    ("IN-en", "Build a pricing page and a Stripe checkout for my SaaS product", True),
    ("IN-es", "monta el onboarding y el embudo de compra de la nueva app", True),
    # A landing with no commercial funnel must not pay for these rules.
    ("OUT-control", "hazme una landing para un restaurante con reservas online", False),
]

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print("  PASS %-28s %s" % (gate, evidence))


def _fail(gate: str, diagnostic: str) -> None:
    global _FAIL
    _FAIL += 1
    print("  FAIL %-28s %s" % (gate, diagnostic))


def main() -> int:
    with tempfile.TemporaryDirectory() as home:
        env = dict(os.environ, HOME=home, USERPROFILE=home)
        for name, prompt, want in CASES:
            payload = {"prompt": prompt, "session_id": str(uuid.uuid4()), "cwd": home}
            p = subprocess.run(["node", HOOK], input=json.dumps(payload), capture_output=True,
                               text=True, encoding="utf-8", env=env, timeout=120)
            out = (p.stdout or "") + (p.stderr or "")
            got = STAMP in out
            shown = [r for r in RULES if r in out]
            gate = "V-CONVF-%s" % name
            if got == want and (not want or len(shown) == len(RULES)):
                _ok(gate, "block=%s rules=%d/%d" % (got, len(shown), len(RULES)))
            else:
                _fail(gate, "block=%s (want %s) rules=%d/%d exit=%s head=%r"
                      % (got, want, len(shown), len(RULES), p.returncode, out[:300]))
    print("CONVF_PASS=%d/%d  threshold=%d/%d" % (_PASS, _PASS + _FAIL, len(CASES), len(CASES)))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
