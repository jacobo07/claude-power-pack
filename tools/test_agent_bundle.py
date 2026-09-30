#!/usr/bin/env python3
"""V-BUN-* gates for modules/capability_runtime/agent_bundle.py (virtualization S2).

Each verdict is driven from a reply that must produce it. A validator that
returned VALID for everything fails every negative gate; one that rejected
everything fails the two controls (full bundle, empty-claims bundle).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.capability_runtime import agent_bundle as B  # noqa: E402
from modules.capability_runtime import agent_spec as A  # noqa: E402

passes = fails = 0
HEAD = "a" * 40


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def reply(spec, **over):
    b = {"bundle": "proof-bundle/v1", "spec": f"{spec.id}@{spec.contract.version}",
         "spec_hash": spec.spec_hash(), "state_version": HEAD, "summary": "One swallowed error.",
         "claims": [{"id": "C1", "statement": "except: pass hides IO errors", "status": "OBSERVED",
                     "severity": "high", "evidence": ["tools/x.py:42"]}],
         "counterevidence": [], "unknowns": [], "recommendation": "log and re-raise",
         "artifacts": [], "pages_read": []}
    b.update(over)
    return "Some prose the parent discards.\n```json\n" + json.dumps(b) + "\n```\n"


def main() -> int:
    spec = A.load("silent-failure-hunter")
    v = lambda text, cur=HEAD: B.validate(text, spec, cur)  # noqa: E731
    check("V-BUN-VALID", v(reply(spec))["verdict"] == "VALID", "full bundle")
    check("V-BUN-EMPTY-CLAIMS-VALID", v(reply(spec, claims=[]))["verdict"] == "VALID", "nothing found is a result")
    check("V-BUN-MISSING", v("I looked and it seems fine.")["verdict"] == "MISSING", "no json block")
    check("V-BUN-UNPARSEABLE", v("```json\n{not json\n```")["verdict"] == "INVALID", "bad json")
    r = v(reply(spec, spec_hash="0" * 16))
    check("V-BUN-FOREIGN-COMPILATION", r["verdict"] == "INVALID" and "spec_hash" in " ".join(r["reasons"]), r["reasons"])
    r = v(reply(spec, claims=[{"id": "C1", "statement": "x", "status": "OBSERVED", "severity": "high", "evidence": []}]))
    check("V-BUN-OBSERVED-NEEDS-CITATION", r["verdict"] == "INVALID", r["reasons"])
    r = v(reply(spec, claims=[{"id": "C1", "statement": "x", "status": "INFERRED", "severity": "low", "evidence": []}]))
    check("V-BUN-INFERRED-MAY-LACK-CITATION", r["verdict"] == "VALID", r["verdict"])
    r = v(reply(spec, claims=[{"id": "C1", "statement": "x", "status": "SURE", "severity": "high"}]))
    check("V-BUN-STATUS-ENUM", r["verdict"] == "INVALID", r["reasons"])
    r = v(reply(spec), cur="b" * 40)
    check("V-BUN-STALE", r["verdict"] == "STALE", r["reasons"])
    r = v(reply(spec, state_version="none"), cur="b" * 40)
    check("V-BUN-UNVERSIONED-NOT-STALE", r["verdict"] == "VALID", "typed absence is not a mismatch")
    r = v(reply(spec, summary="x" * 900))
    check("V-BUN-SUMMARY-BOUNDED", r["verdict"] == "INVALID", "900-char summary refused")
    with tempfile.TemporaryDirectory() as t:
        res = B.accept(reply(spec), "silent-failure-hunter", HEAD, Path(t))
        stored = Path(res.get("stored", ""))
        line = B.compact(res)
        check("V-BUN-PERSIST-AND-COMPACT", stored.is_file() and line.startswith("BUNDLE VALID claims=1")
              and len(line) < 400, line)
        bad = B.accept("no json here", "silent-failure-hunter", HEAD, Path(t))
        check("V-BUN-INVALID-NOT-PERSISTED", "stored" not in bad, bad["verdict"])
    compiled = spec.compile("Review x.", state_version=HEAD)
    check("V-BUN-CONTRACT-FILLED", spec.spec_hash() in compiled and HEAD in compiled and "{spec_hash}" not in compiled,
          "compile fills spec, hash and state into the contract")
    print(f"AGENT_BUNDLE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
