#!/usr/bin/env python3
"""cdc_handoff.py -- CDC C11: render vault/programs/cdc/HANDOFF.md from state. No free-form text.

Inputs: chain.json, WU-*-receipt.md (status + landing shas + last-line), evidence/cdc-gate.json.
  cdc_handoff.py [--root R] [--out FILE]
Deterministic: same inputs -> same bytes (no clock).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROG = Path("vault/programs/cdc")


def _read(p: Path):
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None


def render(root: Path) -> str:
    root = Path(root)
    prog = root / PROG
    chain = json.loads(_read(prog / "chain.json") or "{}")
    gate = json.loads(_read(prog / "evidence" / "cdc-gate.json") or "{}")
    L = ["# CDC handoff", "",
         "<!-- rendered by tools/cdc_handoff.py from chain.json, WU-*-receipt.md, evidence/cdc-gate.json; do not edit -->", "",
         f"Goal `{chain.get('goal', '?')}`, envelope {chain.get('envelope', '?')}.", "",
         "## Units", "", "| unit | receipt status | landing | not proven |", "|---|---|---|---|"]
    for u in chain.get("units", []):
        rid = u["id"]
        t = _read(prog / f"WU-{rid}-receipt.md")
        if t is None:
            L.append(f"| {rid} | NO_RECEIPT | - | - |")
            continue
        st = re.search(r"^Status:\s*(\S+)", t, re.M)
        shas = re.findall(r"(?:landing|live HEAD|live landing(?: sha)?)\s*[:`]?\s*`?([0-9a-f]{7,40})", t)
        npc = len(re.findall(r"NOT_PROVEN|INCONCLUSIVE", t))
        L.append(f"| {rid} | {st.group(1) if st else '?'} | {shas[-1] if shas else '-'} | {npc} |")
    L += ["", "## Done-gates", ""]
    if not gate:
        L.append("evidence/cdc-gate.json missing: run `python tools/cdc_gate.py`.")
    else:
        s = gate.get("summary", {})
        L.append(f"PASS {s.get('PASS', 0)} / FAIL {s.get('FAIL', 0)} / UNKNOWN {s.get('UNKNOWN', 0)} / EXTERNAL_LIMITATION {s.get('EXTERNAL_LIMITATION', 0)}"
                 f"; FAIL in scope {s.get('fail_in_scope', [])}; FAIL out of scope {s.get('fail_out_of_scope', [])}.")
        L += ["", "| gate | status | name | reason |", "|---|---|---|---|"]
        for g in gate.get("gates", []):
            L.append(f"| {g['gate']} | {g['status']} | {g['name']} | {str(g['reason']).replace('|', '/')} |")
    L += ["", "## Pending Owner acts (from gate FAIL out of scope)", ""]
    pend = [g for g in gate.get("gates", []) if g["status"] == "FAIL" and not g.get("in_scope", True)]
    L += [f"- gate {g['gate']}: {g['reason']}" for g in pend] or ["- none"]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    root = Path(a.root)
    out = Path(a.out) if a.out else root / PROG / "HANDOFF.md"
    out.write_text(render(root), encoding="utf-8", newline="\n")
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
