#!/usr/bin/env python
"""Commit-card ledger -> CO-12 `capability_opportunity` signals, OFFLINE (PLAN-SKILL-RESIDENCY C5,
audit G'4/G'7). The card (hooks/doctrine_cards.js) is node on the hook path and writes only its own
ledger; this adapter runs outside any hook, reads that ledger from a cursor, and appends one CO-12
signal per commit judgement through `record_signal` -- the single locked writer of signals.jsonl
(never a second writer, never a new ledger).

    python tools/skill_opportunity_signals.py sync      # ledger rows since the cursor -> CO-12
    python tools/skill_opportunity_signals.py report    # the consumer: judgements by decision

delivered_by: "card" ONLY for a deny-card row (the model was shown the hunks); every other row is
"none" -- a ledger-only row is a measurement, never delivery (audit G'3). A Skill call before the
commit is not visible in the ledger and is joined later from the transcript (tools/skill_invocations.py).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))
from modules.cognitive_os.co_12_telemetry import load_signals, record_signal  # noqa: E402

KIND = "capability_opportunity"
CAPABILITY = "concurrent-writers-shared-tree"
DECISIONS = {"opportunity", "no_opportunity", "unknown", "timeout", "deny-card", "pass-after-card",
             "pass-unrecordable"}


def card_state_dir() -> Path:
    return Path(os.environ.get("DOCTRINE_CARDS_STATE_DIR")
                or Path.home() / ".claude" / "state" / "doctrine-cards")


def sync(card_dir: Path, co12_dir=None) -> dict:
    """Emit one signal per new commit-card row. Idempotent: the byte cursor advances only past rows
    that were written (a dropped write is retried next sync, never skipped)."""
    led, cur = card_dir / "ledger.jsonl", card_dir / "co12-cursor.json"
    if not led.exists():
        return {"state": "NO_LEDGER", "emitted": 0}
    try:
        start = json.loads(cur.read_text(encoding="utf-8")).get("offset", 0) if cur.exists() else 0
    except (OSError, ValueError):
        return {"state": "CURSOR_UNREADABLE", "emitted": 0}
    data = led.read_bytes()
    if start > len(data):                       # ledger rotated or truncated: never re-emit silently
        return {"state": "CURSOR_AHEAD_OF_LEDGER", "emitted": 0}
    pos, emitted, skipped = start, 0, 0
    for raw in data[start:].splitlines(keepends=True):
        if not raw.endswith(b"\n"):             # a row still being written: stop before it
            break
        try:
            row = json.loads(raw)
        except ValueError:
            pos += len(raw); skipped += 1
            continue
        if row.get("card") == "commit" and row.get("decision") in DECISIONS:
            ok = record_signal(KIND, {
                "capability": CAPABILITY, "session": row.get("session"), "decision": row["decision"],
                "delivered_by": "card" if row["decision"] == "deny-card" else "none",
                "basis": row.get("basis"), "source": row.get("source"), "mode": row.get("mode"),
                "foreign_files": len(row.get("foreign") or []), "unknown_files": len(row.get("unknown_files") or []),
                "card_ts": row.get("ts")}, state_dir=co12_dir)
            if not ok:
                break                           # lock timeout: keep the cursor here, retry next sync
            emitted += 1
        else:
            skipped += 1
        pos += len(raw)
    tmp = cur.with_suffix(".tmp")
    tmp.write_text(json.dumps({"offset": pos}), encoding="utf-8")
    os.replace(tmp, cur)
    return {"state": "OK", "emitted": emitted, "skipped": skipped, "offset": pos}


def report(co12_dir=None) -> dict:
    """The named consumer of the kind: commit judgements by decision, and how many were delivered."""
    rows = [r for r in load_signals(state_dir=co12_dir) if r.get("kind") == KIND]
    by = Counter(r.get("decision") for r in rows)
    return {"rows": len(rows), "by_decision": dict(by),
            "opportunities": by["opportunity"] + by["deny-card"] + by["pass-after-card"],
            "delivered_by_card": sum(1 for r in rows if r.get("delivered_by") == "card"),
            "unknown": by["unknown"] + by["timeout"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("sync", "report"))
    a = ap.parse_args(argv)
    out = sync(card_state_dir()) if a.cmd == "sync" else report()
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
