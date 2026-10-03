#!/usr/bin/env python
"""ledger_write.py -- write one pillar's `state.<P>` in the campaign ledger.

The only writer the campaign uses for `state.<P>`. It never touches `frozen`, and it
computes every file evidence's sha256 itself (LF-normalized, the form the done-gate
checks), so a pin is never typed by hand.

    python vault/programs/cognitive-economy/ledger_write.py SPEC.json

SPEC.json: {"pillar": "A", "terminal": "...", "reason": "...",
            "evidence": [{"kind": "gate", "argv": [...]}, {"kind": "prg", "ref": "path"}, ...],
            "savings": [...], "capital": {...}}
`sha256` is filled for every evidence whose kind is a file kind. Exit 1 if a cited file
is missing, the pillar is unknown, or `frozen` would change.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LEDGER = REPO / "vault/programs/cognitive-economy/ledger.json"
FILE_KINDS = ("file", "measurement", "falsification", "prg", "owner_decision", "handoff")


def lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main(argv) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 1
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    pid = spec.pop("pillar")
    if pid not in led["state"]:
        print(f"unknown pillar {pid!r}")
        return 1
    frozen_before = json.dumps(led["frozen"], sort_keys=True)
    for e in spec.get("evidence", []):
        if e.get("kind") in FILE_KINDS:
            p = Path(e["ref"]).expanduser()
            p = p if p.is_absolute() else REPO / e["ref"]
            if not p.is_file():
                print(f"cited file missing: {e['ref']}")
                return 1
            e["sha256"] = lf_sha256(p)
    led["state"][pid] = spec
    if json.dumps(led["frozen"], sort_keys=True) != frozen_before:
        print("refused: frozen would change")
        return 1
    LEDGER.write_text(json.dumps(led, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"state.{pid} written: {spec['terminal']} with {len(spec.get('evidence', []))} evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
