"""Authoritative result contract (D28 Ph1a): a work unit's numbers come from a deterministic certificate, not prose.

    python tools/claim_evidence.py certify <receipt> -- <command ...>   # command prints one JSON object (last line)
    python tools/claim_evidence.py check <receipt>

`certify` runs the command, writes `<receipt>.certificate.json` {values, command, rc, at}, then judges the receipt
through receipt_judge (the one receipt reader): a `Claims:` value or `Status:` the certificate contradicts makes the
receipt DIVERGENT, which every layer (mission, chain, steward) reads as not closed. Exit 0 agree, 3 DIVERGENT,
2 the certifying command failed or printed no JSON object (no certificate is written then: an unrun check certifies
nothing). Origin: W12, worker prose "14 MATCH", ledger 12.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import receipt_judge as rj  # noqa: E402


def _last_json_object(out: str) -> dict | None:
    for line in reversed(out.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict):
                return obj
    try:
        obj = json.loads(out)
        return obj if isinstance(obj, dict) else None
    except ValueError:
        return None


def judge(receipt: str) -> dict:
    return {"receipt": receipt, "status": rj.receipt_status(receipt), "divergences": rj.divergences(receipt)}


def certify(receipt: str, cmd: list[str], timeout: int = 600) -> tuple[int, dict]:
    if not Path(receipt).exists():
        return 2, {"receipt": receipt, "error": "receipt absent"}
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    values = _last_json_object(p.stdout) if p.returncode == 0 else None
    if values is None:
        return 2, {"receipt": receipt, "error": "certifying command failed or printed no JSON object",
                   "rc": p.returncode, "stderr": p.stderr[-800:]}
    cert = {"values": values, "command": cmd, "rc": p.returncode,
            "at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    rj.certificate_path(receipt).write_text(json.dumps(cert, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    out = judge(receipt)
    return (3 if out["divergences"] else 0), out


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "check":
        out = judge(argv[1])
        print(json.dumps(out, sort_keys=True))
        return 3 if out["divergences"] else 0
    if len(argv) >= 4 and argv[0] == "certify" and "--" in argv:
        i = argv.index("--")
        rc, out = certify(argv[1], argv[i + 1:])
        print(json.dumps(out, sort_keys=True))
        return rc
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
