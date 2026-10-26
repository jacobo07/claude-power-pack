#!/usr/bin/env python3
"""V-LATEST-* gates: `rollover.py seal` leaves rollover/latest/<repo-key>.json for the CCR frontier reader (Tramo A2, Phase 2).

Hermetic: throwaway state dir. Each refusal has a control where the pointer is written.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rollover as ro  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
    else:
        fails += 1
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="latest_t_"))
    cap = {"schema": ro.SCHEMA, "session_id": "cccccccc-0001", "cwd": "/w/Repo",
           "repo": {"state": "OK", "root": "/w/Repo"}, "obligations": ["fix the parser"], "summary": "s", "writes": ["/w/Repo/a.py"]}
    rc = ro.seal(cap, tmp)
    ptr = ro.write_latest_pointer(cap, rc, tmp)
    check("V-LATEST-WRITTEN", ptr is not None and ptr.parent == tmp / "latest" and ptr.is_file(), str(ptr))
    o = json.loads(ptr.read_text(encoding="utf-8"))
    check("V-LATEST-FIELDS", set(o) == {"capsule", "sha256", "sealed_at"} and o["capsule"] == rc["path"]
          and o["sha256"] == hashlib.sha256(Path(rc["path"]).read_bytes()).hexdigest(), o)
    # key parity with policy.ts repoKey(): FNV-1a 32 over the lowercased, slash-normalised root
    check("V-LATEST-KEY-PARITY", ro.repo_key("C:\\Work\\Repo") == ro.repo_key("c:/work/repo") and ptr.name == f"{ro.repo_key('/w/Repo')}.json"
          and ro.repo_key(None) == ro.repo_key("no-repo") and ro.repo_key("a") == "e40c292c", ro.repo_key("a"))
    # refusal + control: an unsealed receipt gets no pointer
    check("V-LATEST-UNSEALED-NONE", ro.write_latest_pointer(cap, {"sealed": False, "reason": "x"}, tmp) is None, "no pointer for a failed seal")
    # a second seal replaces the pointer (newest wins)
    cap2 = dict(cap, session_id="cccccccc-0002")
    rc2 = ro.seal(cap2, tmp)
    ro.write_latest_pointer(cap2, rc2, tmp)
    check("V-LATEST-NEWEST", json.loads(ptr.read_text(encoding="utf-8"))["capsule"] == rc2["path"], "second seal replaced the pointer")
    print(f"LATEST_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
