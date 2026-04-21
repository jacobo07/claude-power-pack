#!/usr/bin/env python3
"""
Mistake Frequency Counter — closes the Mistakes→Curriculum loop.

Counts how often each mistake from mistakes-registry.md recurs across sessions.
pre-task.md reads --top to surface a Recurring Mistake Watchlist.
post-output.md increments on failure capture.

Schema: modules/governance-overlay/mistake-frequency.json
    {
      "schema": "mistake-frequency-v1",
      "threshold": 3,
      "last_updated": "ISO-ts|null",
      "entries": {
        "M16": {"count": 3, "last": "ISO-ts", "projects": ["kobiicraft", "tua-x"]},
        ...
      }
    }

CLI:
    python mistake_frequency.py --show
    python mistake_frequency.py --top [N]
    python mistake_frequency.py --increment M16 [--project <name>]
    python mistake_frequency.py --reset M16
    python mistake_frequency.py --validate
"""

import argparse
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
_DEFAULT_LEDGER = HERE.parent / "modules" / "governance-overlay" / "mistake-frequency.json"
LEDGER_PATH = Path(os.environ.get("MISTAKE_FREQUENCY_LEDGER", str(_DEFAULT_LEDGER)))

MISTAKE_ID_RE = re.compile(r"^M\d+$", re.IGNORECASE)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def empty_ledger() -> dict:
    return {
        "schema": "mistake-frequency-v1",
        "threshold": 3,
        "last_updated": None,
        "entries": {},
    }


def load_ledger() -> dict:
    if not LEDGER_PATH.exists():
        return empty_ledger()
    with LEDGER_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Ensure required keys present (forward-compat if older file seeded earlier)
    for k, v in empty_ledger().items():
        data.setdefault(k, v)
    return data


def save_ledger(data: dict) -> None:
    data["last_updated"] = now_iso()
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def normalize_mid(mid: str) -> str:
    s = mid.strip().upper()
    if not MISTAKE_ID_RE.match(s):
        raise ValueError(f"mistake id must be M<number>, got: {mid}")
    return s


def cmd_show(_args) -> int:
    print(json.dumps(load_ledger(), indent=2, ensure_ascii=False))
    return 0


def cmd_top(args) -> int:
    data = load_ledger()
    threshold = data.get("threshold", 3)
    n = args.top if isinstance(args.top, int) and args.top > 0 else 3
    entries = data.get("entries", {})
    ranked = sorted(
        entries.items(),
        key=lambda kv: (kv[1].get("count", 0), kv[1].get("last") or ""),
        reverse=True,
    )
    surfaced = [(mid, e) for mid, e in ranked if e.get("count", 0) >= threshold][:n]
    if not surfaced:
        print(f"(none) — no mistake has count >= {threshold}")
        return 0
    print(f"Recurring mistakes (count >= {threshold}):")
    for mid, e in surfaced:
        projects = ",".join(e.get("projects", [])) or "-"
        print(f"  {mid}  count={e['count']}  last={e.get('last','-')}  projects={projects}")
    return 0


def cmd_increment(args) -> int:
    try:
        mid = normalize_mid(args.increment)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    data = load_ledger()
    entry = data["entries"].setdefault(mid, {"count": 0, "last": None, "projects": []})
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last"] = now_iso()
    project = (args.project or "").strip().lower()
    if project:
        projects = entry.setdefault("projects", [])
        if project not in projects:
            projects.append(project)
    save_ledger(data)
    print(f"OK: {mid} count={entry['count']} (threshold={data.get('threshold',3)})")
    return 0


def cmd_reset(args) -> int:
    try:
        mid = normalize_mid(args.reset)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    data = load_ledger()
    if mid not in data["entries"]:
        print(f"NO-OP: {mid} not in ledger")
        return 0
    del data["entries"][mid]
    save_ledger(data)
    print(f"OK: removed {mid}")
    return 0


def cmd_validate(_args) -> int:
    errors = []
    if not LEDGER_PATH.exists():
        print(f"ERROR: ledger missing at {LEDGER_PATH}", file=sys.stderr)
        return 1
    raw = LEDGER_PATH.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("UTF-8 BOM detected (violates CD#10)")
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        print(f"FAIL: invalid JSON: {exc}", file=sys.stderr)
        return 1
    for key in ("schema", "threshold", "entries"):
        if key not in data:
            errors.append(f"missing top-level key: {key}")
    for mid, entry in data.get("entries", {}).items():
        if not MISTAKE_ID_RE.match(mid):
            errors.append(f"invalid mistake id: {mid}")
        if not isinstance(entry.get("count"), int) or entry["count"] < 0:
            errors.append(f"{mid}: count must be non-negative int")
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print(f"OK: mistake-frequency ledger valid. {len(data.get('entries', {}))} entries, threshold={data.get('threshold',3)}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Mistake Frequency Counter — Mistakes→Curriculum loop")
    p.add_argument("--show", action="store_true")
    p.add_argument("--top", nargs="?", type=int, const=3, default=None, help="Show top N recurring mistakes (default 3)")
    p.add_argument("--increment", metavar="M<N>", default=None)
    p.add_argument("--project", default=None)
    p.add_argument("--reset", metavar="M<N>", default=None)
    p.add_argument("--validate", action="store_true")
    args = p.parse_args()

    if args.show:
        return cmd_show(args)
    if args.top is not None:
        return cmd_top(args)
    if args.increment:
        return cmd_increment(args)
    if args.reset:
        return cmd_reset(args)
    if args.validate:
        return cmd_validate(args)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
