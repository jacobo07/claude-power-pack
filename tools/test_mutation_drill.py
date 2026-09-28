#!/usr/bin/env python
"""V-MD-* gates for tools/mutation_drill.py, on a SYNTHETIC subject so the drill represents the
class and cannot be fixed out from under its assertions. All four outcomes are driven, and the
live subject's bytes are checked after every drill."""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutation_drill as md  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="md-subject-")) / "pkg"
    d.mkdir()
    subj, test = d / "subj.py", d / "test_subj.py"
    subj.write_text("def f():\n    return 1  # anchor\n", encoding="utf-8")
    test.write_text(
        "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent))\n"
        "import subj\nok = subj.f() == 1\nprint(('PASS' if ok else 'FAIL') + ' V-S-ONE')\n"
        "print(f'S_PASS={int(ok)}/1')\n", encoding="utf-8")
    sha = hashlib.sha256(subj.read_bytes()).hexdigest()
    base = {"file": str(subj), "test": str(test), "gate": "V-S-ONE"}

    v, _ = md.drill({**base, "old": "return 1", "new": "return 2"})
    check("V-MD-KILLED", v == "KILLED", v)
    v, _ = md.drill({**base, "old": "# anchor", "new": "# renamed"})
    check("V-MD-SURVIVED-IS-NOT-KILLED", v == "SURVIVED", v)
    v, _ = md.drill({**base, "old": "return 1", "new": "return ("})
    check("V-MD-CRASH-IS-UNJUDGED", v == "UNJUDGED", v)
    v, why = md.drill({**base, "old": "not in the file", "new": "x"})
    check("V-MD-MISSING-ANCHOR-HARNESS", v == "HARNESS" and "0x" in why, why)
    check("V-MD-LIVE-SUBJECT-NEVER-WRITTEN", hashlib.sha256(subj.read_bytes()).hexdigest() == sha)
    print(f"MD_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
