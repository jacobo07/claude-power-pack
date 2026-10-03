#!/usr/bin/env python
"""V-SKOPP gates for tools/skill_opportunity_signals.py (PLAN-SKILL-RESIDENCY C5).
Hermetic: card ledger and CO-12 state live in temp dirs; the LIVE signals.jsonl must be byte-identical
after the run (ACV CP-4)."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_opportunity_signals as so  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1; print(f"PASS {gate}: {ev}")
    else:
        fails += 1; print(f"FAIL {gate}: {ev}")


def row(decision, **kw):
    return json.dumps({"ts": "2026-10-03T12:00:00Z", "card": "commit", "mode": "ledger", "source": "cli",
                       "session": "s1", "decision": decision, "basis": "index", **kw}) + "\n"


LIVE = Path.home() / ".claude" / "state" / "co12_readiness" / "signals.jsonl"
live_before = hashlib.sha256(LIVE.read_bytes()).hexdigest() if LIVE.exists() else None

with tempfile.TemporaryDirectory() as td:
    card, co12 = Path(td) / "card", Path(td) / "co12"
    card.mkdir()
    led = card / "ledger.jsonl"
    led.write_text(row("opportunity", foreign=[{"file": "a.py"}]) + row("no_opportunity") + row("deny-card", foreign=[{"file": "a.py"}])
                   + json.dumps({"card": "other", "decision": "opportunity"}) + "\n" + "{torn", encoding="utf-8")

    r1 = so.sync(card, co12)
    check("V-SKOPP-EMITS-COMMIT-ROWS", r1["emitted"] == 3, f"emitted={r1['emitted']} skipped={r1.get('skipped')}")
    check("V-SKOPP-STOPS-BEFORE-TORN-ROW", r1["offset"] == len(led.read_bytes()) - len(b"{torn"),
          "an unterminated last row is left for the next sync")
    rep = so.report(co12)
    check("V-SKOPP-DELIVERY-ONLY-DENY-CARD", rep["delivered_by_card"] == 1 and rep["opportunities"] == 2,
          f"report={rep}")

    r2 = so.sync(card, co12)
    check("V-SKOPP-IDEMPOTENT", r2["emitted"] == 0 and so.report(co12)["rows"] == 3, f"second sync emitted={r2['emitted']}")

    with open(led, "ab") as fh:              # the torn row completes, a new row follows
        fh.write(b"\n" + row("unknown", reason="commit --amend").encode())
    r3 = so.sync(card, co12)
    check("V-SKOPP-RESUMES-AFTER-CURSOR", r3["emitted"] == 1 and so.report(co12)["unknown"] == 1,
          f"emitted={r3['emitted']} (torn line skipped as unparsable, new row emitted)")

    # Positive control for the consumer: an empty store reports zero, a filled one does not.
    check("V-SKOPP-REPORT-DISCRIMINATES", so.report(Path(td) / "empty")["rows"] == 0 and so.report(co12)["rows"] == 4,
          "empty store 0 rows, filled store 4")

    (card / "co12-cursor.json").write_text(json.dumps({"offset": 10 ** 9}), encoding="utf-8")
    check("V-SKOPP-CURSOR-AHEAD-REFUSED", so.sync(card, co12)["state"] == "CURSOR_AHEAD_OF_LEDGER", "no silent re-emit")

live_after = hashlib.sha256(LIVE.read_bytes()).hexdigest() if LIVE.exists() else None
check("V-SKOPP-LIVE-UNTOUCHED", live_before == live_after, "live CO-12 signals.jsonl byte-identical")
print(f"SKOPP_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
