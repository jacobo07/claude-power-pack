#!/usr/bin/env python
"""Held-out Consumption Law (Tennis Generation S11, Lane A3).

A sealed held-out must not be consumed by an instrument that has not passed BOTH its positive and its negative
controls. Origin 2026-11-02 (Tennis S10b, mission m-f41146776f2b): the frozen method c631de1e returned OFF_SHAPE for
the 3 functions known to be C++, so a sealed H2 run could only have measured 0 and spent the one clean held-out. The
Owner kept H2 unspent; this check makes that decision mechanical.

The sealed runner calls `release(request)` (or the CLI) BEFORE it reads the manifest's members. Every condition is a
refusal reason of its own; RELEASE needs all of them:
  manifest present and its sha256 equal to the frozen one;  method frozen by commit;
  positive controls all pass (and there is at least one);  negative controls all refuse (and at least one);
  the predeclared development minimum met;  no open instrument-blindness note;  no SEAL yet (not already consumed).

CLI: python tools/heldout_release.py <request.json>   -> prints RELEASE|REFUSE + reasons, exit 0|1
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release(req: dict) -> dict:
    """Pure over the request plus the two paths it names. -> {verdict, reasons}."""
    why: list[str] = []
    man = Path(str(req.get("manifest") or ""))
    if not req.get("manifest") or not man.is_file():
        why.append("manifest missing")
    elif _sha256(man) != str(req.get("manifest_sha256") or ""):
        why.append("manifest sha256 differs from the frozen one")
    mf = req.get("method_frozen") or {}
    if not mf.get("commit"):
        why.append("method not frozen by commit")
    pos = (req.get("controls") or {}).get("positive") or {}
    if int(pos.get("total") or 0) < 1 or int(pos.get("pass") or 0) != int(pos.get("total") or 0):
        why.append(f"positive controls {pos.get('pass', 0)}/{pos.get('total', 0)}: the instrument cannot say yes")
    neg = (req.get("controls") or {}).get("negative") or {}
    if int(neg.get("total") or 0) < 1 or int(neg.get("refused") or 0) != int(neg.get("total") or 0):
        why.append(f"negative controls {neg.get('refused', 0)}/{neg.get('total', 0)} refused: the instrument cannot say no")
    dev = req.get("dev_minimum") or {}
    if dev.get("required") is None or int(dev.get("observed") or 0) < int(dev["required"]):
        why.append(f"development minimum {dev.get('observed', 0)}/{dev.get('required')} not met")
    if req.get("blindness"):
        why.append(f"open instrument-blindness notes: {req['blindness']}")
    seal = req.get("seal_dir")
    if not seal:
        why.append("no seal_dir declared")
    elif (Path(str(seal)) / "SEAL").exists():
        why.append("SEAL already present: the held-out was consumed")
    return {"verdict": "REFUSE" if why else "RELEASE", "reasons": why}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[-1])
        return 2
    out = release(json.loads(Path(argv[0]).read_text(encoding="utf-8")))
    print(out["verdict"])
    for r in out["reasons"]:
        print(f"  - {r}")
    return 0 if out["verdict"] == "RELEASE" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
