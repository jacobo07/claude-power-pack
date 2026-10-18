"""Promote the DWS rows 59/70 standards into multi_host_fabric B1 through the ratchet's own entry point."""
from __future__ import annotations

import os
import sys

_PP_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import ratchet as rt  # noqa: E402

ORCA = r"C:\Users\User\Apps\orca-rb-live-wt"
ENTRIES = [
    {
        "id": "multi_host_fabric-live-leg-never-answers-bypass-consent",
        "requirement": "A live leg changes the launch so Bypass Permissions is never asked and asserts it was not; it never answers the consent dialog.",
        "why": "Consent to Bypass Permissions on a real account persists there and belongs to the Owner.",
        "origin": {"file": ORCA + r"\docs\dws\live-2026-10-18-row-59-model-turn-evidence.md", "line": 29,
                   "quote": "HWF59M_ARGV_BYPASS_FLAG=absent"},
        "class": "D",
        "check": r"regex:docs/dws/live-2026-10-18-row-59-model-turn-evidence.md::HWF59M_ARGV_BYPASS_FLAG=absent",
        "status": "reviewed",
    },
    {
        "id": "multi_host_fabric-transfer-is-read-back-on-the-target",
        "requirement": "A session transfer is proved by reading the transferred bytes on the target host with a tool the product does not use.",
        "why": "A transfer's own status cannot witness itself; a product that lies about writing stays green.",
        "origin": {"file": ORCA + r"\docs\dws\live-2026-10-18-row-70-resume-evidence.md", "line": 20,
                   "quote": "stat` on GEX44"},
        "class": "D",
        "check": r"regex:tests/e2e/hwf-two-host-continue-here-resume.spec.ts::XFER_BYTES=\[1-9\]",
        "status": "reviewed",
    },
]

if __name__ == "__main__":
    print(rt.promote("multi_host_fabric", ENTRIES,
                     "DWS rows 59 and 70 standards (UKDL T-A-TEST-DOES-NOT-ACCEPT-BYPASS-PERMISSIONS-001, "
                     "T-SESSION-TRANSFER-NEEDS-AN-INDEPENDENT-READ-BACK-001)",
                     "dws rows milestone phase 7, Owner-approved row 54"))
