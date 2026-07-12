#!/usr/bin/env python3
"""Artifact Done-Gate CLI (P2).

Declare the artifact a feature promises, then let the gate look at the
disk. Exit codes and green tests are not consulted.

  Inline, one artifact:
    python tools/done_gate.py --name embeddings \
        --path vault/embeddings/index.jsonl --kind jsonl \
        --min-count 1000 --keys id,vector

  From a contract file (list of contracts, or {"contracts": [...]}):
    python tools/done_gate.py --contracts vault/done_gate/myfeature.json

Exit 0 = DONE (artifacts observed). Exit 1 = NOT DONE.
`NEVER_OBSERVED_TO_WORK` is a defect status; it exits 1 like any other.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.done_gate import (  # noqa: E402
    ArtifactContract,
    Kind,
    Status,
    gate,
    write_receipt,
)

RECEIPTS = PP_ROOT / "vault" / "done_gate" / "receipts.jsonl"


def _contract_from(d: dict) -> ArtifactContract:
    return ArtifactContract(
        name=d["name"],
        path=d["path"],
        kind=Kind(d.get("kind", "file")),
        min_bytes=int(d.get("min_bytes", 1)),
        min_count=int(d.get("min_count", 1)),
        required_keys=tuple(d.get("required_keys", ())),
        table=d.get("table", ""),
        is_failure_branch=bool(d.get("is_failure_branch", False)),
    )


def load_contracts(path: Path) -> list[ArtifactContract]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    items = raw["contracts"] if isinstance(raw, dict) else raw
    return [_contract_from(d) for d in items]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Verify a feature produced its declared artifacts.")
    p.add_argument("--contracts", metavar="FILE")
    p.add_argument("--name")
    p.add_argument("--path")
    p.add_argument("--kind", default="file",
                   choices=[k.value for k in Kind])
    p.add_argument("--min-bytes", type=int, default=1)
    p.add_argument("--min-count", type=int, default=1)
    p.add_argument("--keys", default="",
                   help="comma-separated keys every record must carry")
    p.add_argument("--table", default="", help="table name for --kind sqlite")
    p.add_argument("--failure-branch", action="store_true",
                   help="mark as a graceful-failure check; it can never "
                        "substitute for the success branch")
    p.add_argument("--command", default="",
                   help="the command whose output is being gated (recorded "
                        "on the receipt)")
    p.add_argument("--no-receipt", action="store_true")
    a = p.parse_args(argv)

    if a.contracts:
        contracts = load_contracts(Path(a.contracts))
    elif a.name and a.path:
        keys = tuple(k.strip() for k in a.keys.split(",") if k.strip())
        contracts = [ArtifactContract(
            name=a.name, path=a.path, kind=Kind(a.kind),
            min_bytes=a.min_bytes, min_count=a.min_count,
            required_keys=keys, table=a.table,
            is_failure_branch=a.failure_branch,
        )]
    else:
        p.error("give --contracts FILE, or both --name and --path")

    res = gate(contracts)
    print("=== ARTIFACT DONE-GATE ===")
    for v in res.verdicts:
        mark = "PASS" if v.passed else "FAIL"
        branch = " [failure-branch]" if v.contract.is_failure_branch else ""
        print(f"\n[{mark}] {v.contract.name}{branch} -> {v.status.value}")
        print(f"  declared : {v.contract.path} ({v.contract.kind.value})")
        if v.resolved_path:
            print(f"  on disk  : {v.resolved_path}")
            print(f"  evidence : {v.size_bytes} bytes, {v.count} record(s)")
        if v.detail:
            print(f"  detail   : {v.detail}")
        if v.status is Status.NEVER_OBSERVED_TO_WORK:
            print("  NEVER_OBSERVED_TO_WORK is a defect status, not a pass.")

    print(f"\n{'DONE' if res.passed else 'NOT DONE'} -- {res.detail}")
    if not a.no_receipt:
        write_receipt(res, RECEIPTS, a.command)
        print(f"receipt  : {RECEIPTS}")
    return 0 if res.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
