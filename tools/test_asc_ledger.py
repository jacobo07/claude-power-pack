"""V-ASC-LED gate: reconciliation ledger, both poles. python3 tools/test_asc_ledger.py (exit 0 == PASS)"""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.backlog_autopilot import inventory as inv, ledger as led  # noqa: E402

FAILS = []


def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (f" -- {d}" if d and not c else ""))
    if not c:
        FAILS.append(n)


def w(d, rel, txt):
    p = d / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt)


with tempfile.TemporaryDirectory() as t:
    d = Path(t)
    # a real, wired, tested capability
    w(d, "modules/realcap/__init__.py", "")
    w(d, "modules/realcap/core.py", "def main():\n    return 1\nif __name__ == '__main__':\n    main()\n")
    w(d, "tools/test_realcap.py", "from modules.realcap import core  # modules/realcap/core\n")
    w(d, "hooks/user.js", "require('modules/realcap/core')\n")
    w(d, "vault/backlog/2026-10-01_realcap.md", "# Absorb realcap\nStatus: DONE\nSee `modules/realcap/core.py`.\n")
    # false absorption: claims done, names a module that does not exist
    w(d, "vault/backlog/2026-10-02_ghostcap.md", "# Absorb ghostcap\nStatus: DONE\nImplemented in `modules/ghostcap/engine.py`.\n")
    # pure backlog
    w(d, "vault/backlog/2026-10-03_pending-thing.md", "# Pending thing\nStatus: PENDING\n")
    # blocked item
    w(d, "vault/backlog/2026-10-04_laptop-blocked.md", "# Laptop BLOCKED item\nStatus: BLOCKED\n")
    # source-found only (impl exists, no test/consumer)
    w(d, "modules/loner/x.py", "X = 1\n")
    w(d, "vault/backlog/2026-10-05_loner.md", "# Loner capability\nStatus: PARTIAL\nCode: `modules/loner/x.py`\n")

    iv = inv.build(d)
    L = led.build(d, iv)
    by = {r["title"]: r for r in L["rows"]}

    check("clean ledger verifies PASS", led.verify(L, iv) == [], str(led.verify(L, iv)))
    check("real wired capability is ACTIVATED", by["Absorb realcap"]["state"] == "ACTIVATED", by["Absorb realcap"]["state"])
    check("seeded FALSE ABSORPTION is rejected", by["Absorb ghostcap"]["state"] == "CLAIM_REJECTED")
    check("pure backlog stays BACKLOG_ONLY (not available)", by["Pending thing"]["state"] == "BACKLOG_ONLY")
    check("impl with no entrypoint/test is only SOURCE_FOUND", by["Loner capability"]["state"] == "SOURCE_FOUND")
    check("ACTIVATED without execution evidence is NOT operational",
          L["operational"]["numerator"] == 0 and L["operational"]["denominator"] >= 3, str(L["operational"]))

    # execution evidence moves operational numerator only with a real recorded exit 0
    import json
    rid = by["Absorb realcap"]["id"]
    w(d, led.EVIDENCE_FILE, json.dumps({rid: {"exit": 1}}))
    check("failed evidence (exit 1) does not count", led.build(d, iv)["operational"]["numerator"] == 0)
    w(d, led.EVIDENCE_FILE, json.dumps({rid: {"exit": 0, "cmd": "python3 tools/test_realcap.py"}}))
    check("recorded exit 0 evidence counts", led.build(d, iv)["operational"]["numerator"] == 1)
    (d / led.EVIDENCE_FILE).unlink()

    # POSITIVE pole: a blocked item dropped from the ledger -> FAIL (denominator cannot shrink)
    check("blocked item present in denominator", by["Laptop BLOCKED item"]["blocked"] and L["blocked_in_denominator"] == 1)
    bad = copy.deepcopy(L)
    bad["rows"] = [r for r in bad["rows"] if not r["blocked"]]
    bad.update(led.coverage(bad["rows"]))
    f = led.verify(bad, iv)
    check("dropping a BLOCKED row fails the gate", any(x.startswith("DROPPED") for x in f), str(f))

    # POSITIVE pole: forged false absorption accepted as SOURCE_FOUND w/o impl -> FAIL
    forged = copy.deepcopy(L)
    for r in forged["rows"]:
        if r["title"] == "Absorb ghostcap":
            r["state"] = "SOURCE_FOUND"
    check("forged accepted false absorption fails", any("NO_IMPL" in x for x in led.verify(forged, iv)))

    # POSITIVE pole: forged ACTIVATED without consumer -> FAIL
    forged2 = copy.deepcopy(L)
    for r in forged2["rows"]:
        if r["title"] == "Loner capability":
            r["state"] = "ACTIVATED"
    check("forged ACTIVATED without proof fails", any("UNPROVEN_ACTIVATED" in x for x in led.verify(forged2, iv)))

    # POSITIVE pole: stored ratio inflated by hand -> FAIL
    inflated = copy.deepcopy(L)
    inflated["operational"]["numerator"] = inflated["operational"]["denominator"]
    check("hand-inflated ratio fails", any(x.startswith("RATIO") for x in led.verify(inflated, iv)))

# real tree
iv = inv.build(ROOT)
L = led.build(ROOT, iv)
check("real tree: ledger verifies PASS", led.verify(L, iv) == [], str(led.verify(L, iv))[:300])
check("real tree: every state in the closed set", set(r["state"] for r in L["rows"]) <= set(led.STATES))
check("real tree: reconciliation denominator == obligation identities",
      L["reconciliation"]["denominator"] == iv["obligation_identities"])
check("real tree: deterministic", led.build(ROOT, iv) == L)
print("V-ASC-LED", "FAIL" if FAILS else "PASS", FAILS or "")
sys.exit(1 if FAILS else 0)
