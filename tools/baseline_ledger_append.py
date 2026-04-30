r"""
baseline_ledger_append.py - append a row to vault/baseline_ledger.jsonl after
a successful pre-compact dump or after a /verdict A+ that elevates a baseline.

Each row is a "Hardware Law" — a fact / decision / wiring that future sessions
treat as settled, not re-debatable. The ledger is append-only and human-
readable; post-compact lazarus restore reads it BEFORE doing anything else,
so any logic already validated does not get re-discussed.

Schema per row:
  {
    "iso_ts": "2026-04-30T13:15:00Z",
    "ledger_id": "BL-0042",        // monotonically increasing
    "law": "Plugin scanner must enumerate <plugin>/skills/* (MC-SA-02)",
    "evidence": ["vault/audits/skill_collisions_2026-04-30.md", "ovo verdict A 9304089b"],
    "session_id": "...",
    "trigger": "ovo-A-verdict|pre-compact|manual",
    "scope": "global|repo:<name>"
  }

CLI:
  python tools/baseline_ledger_append.py --law "<text>" --evidence p1,p2 \
      [--trigger manual] [--scope global] [--session-id <sid>]

  python tools/baseline_ledger_append.py --show           # tail last 10
  python tools/baseline_ledger_append.py --show --all     # full ledger
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER = REPO_ROOT / "vault" / "baseline_ledger.jsonl"


def next_id() -> str:
    if not LEDGER.is_file():
        return "BL-0001"
    n = 0
    with LEDGER.open("r", encoding="utf-8", errors="replace") as h:
        for line in h:
            if line.strip():
                n += 1
    return f"BL-{n + 1:04d}"


def append_row(row: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False) + "\n"
    # Append-only — atomic at the OS level for typical row sizes (<4KB).
    with LEDGER.open("a", encoding="utf-8", newline="\n") as h:
        h.write(line)


def show(limit: int | None) -> None:
    if not LEDGER.is_file():
        print(json.dumps({"ledger": str(LEDGER), "rows": [], "count": 0}, indent=2))
        return
    rows: list[dict] = []
    with LEDGER.open("r", encoding="utf-8", errors="replace") as h:
        for line in h:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    out = rows if limit is None else rows[-limit:]
    print(json.dumps({
        "ledger": str(LEDGER.relative_to(REPO_ROOT)).replace("\\", "/"),
        "count_total": len(rows),
        "count_shown": len(out),
        "rows": out,
    }, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="baseline_ledger_append")
    parser.add_argument("--law", help="One-sentence Hardware Law")
    parser.add_argument("--evidence", help="Comma-separated evidence paths or refs", default="")
    parser.add_argument("--trigger", default="manual",
                        choices=["manual", "ovo-A-verdict", "ovo-Aplus-verdict", "pre-compact"])
    parser.add_argument("--scope", default="global", help="global | repo:<name>")
    parser.add_argument("--session-id", default=os.environ.get("CLAUDE_SESSION_ID", "unknown"))
    parser.add_argument("--show", action="store_true", help="Print rows instead of appending")
    parser.add_argument("--all", action="store_true", help="With --show: print full ledger")
    args = parser.parse_args(argv)

    if args.show:
        show(None if args.all else 10)
        return 0

    if not args.law:
        print("error: --law is required when not using --show", file=sys.stderr)
        return 2

    row = {
        "iso_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ledger_id": next_id(),
        "law": args.law.strip(),
        "evidence": [e.strip() for e in args.evidence.split(",") if e.strip()],
        "session_id": args.session_id,
        "trigger": args.trigger,
        "scope": args.scope,
        "schema_version": 1,
    }
    append_row(row)
    print(json.dumps({"ok": True, "ledger_id": row["ledger_id"], "law": row["law"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
