"""V-SPKT-*: tools/source_packet.py -- bounded, hashed excerpts with expected-hash staleness.

Hermetic temp root. Each gap class has a green control (a clean file packed COMPLETE).
    python tools/test_source_packet.py
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import source_packet as sp  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="spkt_t_"))
    try:
        (tmp / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
        sha = hashlib.sha256((tmp / "a.py").read_bytes()).hexdigest()
        pk = sp.build(str(tmp), ["a.py"], {"a.py": sha})
        check("V-SPKT-GREEN", pk.verdict == sp.COMPLETE and "return 1" in pk.prompt and not pk.gaps, pk.gaps)
        stale = sp.build(str(tmp), ["a.py"], {"a.py": "0" * 64})
        check("V-SPKT-STALE", stale.verdict == sp.PARTIAL and any("STALE" in g for g in stale.gaps), stale.gaps)
        (tmp / "cfg.py").write_text("api_key = 'x'\n", encoding="utf-8")
        cred = sp.build(str(tmp), ["a.py", "cfg.py"])
        check("V-SPKT-CREDENTIAL-BLOCKED", cred.verdict == sp.PARTIAL and "api_key" not in cred.prompt
              and any("credential" in g for g in cred.gaps), cred.gaps)
        (tmp / "b.py").write_text("x = 1\n# see C:\\Users\\someone\\notes\n", encoding="utf-8")
        red = sp.build(str(tmp), ["b.py"])
        check("V-SPKT-PRIVATE-LINE-REDACTED", red.verdict == sp.PARTIAL and "someone" not in red.prompt
              and any("redacted" in g for g in red.gaps), red.gaps)
        miss = sp.build(str(tmp), ["nope.py"])
        check("V-SPKT-MISSING-NAMED", miss.verdict == sp.PARTIAL and any("missing" in g for g in miss.gaps), miss.gaps)
        esc = sp.build(str(tmp), ["../outside.py"])
        check("V-SPKT-ESCAPE-BLOCKED", esc.verdict == sp.PARTIAL and any("blocked" in g for g in esc.gaps), esc.gaps)
        (tmp / "big.py").write_text("x = 1\n" * 3000, encoding="utf-8")
        big = sp.build(str(tmp), ["big.py"])
        check("V-SPKT-TRUNCATION-NAMED", big.verdict == sp.PARTIAL and any("truncated" in g for g in big.gaps), big.gaps)
        saved = os.environ.get("CPP_NODE_EXE")
        os.environ["CPP_NODE_EXE"] = str(tmp / "no-node.exe")
        try:
            down = sp.build(str(tmp), ["a.py"])
        finally:
            if saved is None:
                os.environ.pop("CPP_NODE_EXE", None)
            else:
                os.environ["CPP_NODE_EXE"] = saved
        check("V-SPKT-BRIDGE-DOWN-UNJUDGED", down.verdict == sp.UNJUDGED and not down.prompt, down.gaps)
        check("V-SPKT-CLI-EXIT", sp.main(["--root", str(tmp), "a.py", "--expect", f"a.py={sha}"]) == 0
              and sp.main(["--root", str(tmp), "a.py", "--expect", "a.py=" + "0" * 64]) == 3, "0 / 3")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = passes + fails
    print(f"SPKT_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
