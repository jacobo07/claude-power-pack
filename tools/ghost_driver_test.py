#!/usr/bin/env python
"""BL-0057 — Synthetic tier-2 advisory injector for ghost_input_driver.ps1.

Appends a fake `tier=advisory` row to the context_snapshots.jsonl ledger so
the driver detects + reacts (DRY-RUN mode logs only). Use this to verify
the driver pipeline without actually crossing the 70% context threshold.

Usage:
    python tools/ghost_driver_test.py [--cwd <path>] [--used-pct <float>]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "vault" / "sleepy" / "context_snapshots.jsonl"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cwd", default=str(ROOT))
    p.add_argument("--used-pct", type=float, default=72.0)
    p.add_argument("--session-id", default="ghost-test-" + _dt.datetime.now().strftime("%H%M%S"))
    args = p.parse_args()

    row = {
        "iso_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "kind": "context_snapshot",
        "tier": "advisory",
        "session_id": args.session_id,
        "used_pct": args.used_pct,
        "remaining_pct": 100 - args.used_pct,
        "tokens_used": int(200000 * args.used_pct / 100),
        "tokens_total": 200000,
        "transcript_path": f"<test>/{args.session_id}.jsonl",
        "cwd": args.cwd,
        "trigger": "ghost-driver-test",
        "ledger_law_ref": "BL-0057",
        "schema_version": 2,
    }

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

    print(f"injected tier-2 advisory row at {LEDGER}")
    print(f"  session_id={args.session_id} used_pct={args.used_pct} cwd={args.cwd}")
    print(f"  if ghost_input_driver.ps1 is running, it should detect within ~2s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
