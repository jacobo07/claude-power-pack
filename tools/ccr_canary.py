#!/usr/bin/env python
"""CCR v5 canary (E3): drive the Envelope 0-3 mechanisms end to end through their REAL entry points on a
throwaway mission, zero model calls, and print one CANARY line per mechanism. Exit 0 only if all hold.

  ccr_canary.py [FILE_TO_MAP]     (default: tools/gsd_mission.py)

Mechanisms, each with the refusal and its control:
  forecast gate   set_envelope refuses a phase forecast below max_calls x floor, admits one at the bound
  boundary        a mission over its max_calls is held by the phase breaker; at the cap it runs
  fresh epoch     a lease for another phase moves wu_packet_epoch; the same phase does not
  code map        a page is a MISS first and a HIT for the same sha; an edited file is a MISS again
The mission machinery is the one tools/test_boundary_authority.py builds (temp state dir, injected meters),
so the canary shares its setup with the gate instead of re-implementing it.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_boundary_authority as tb  # noqa: E402  (sets the temp state env on import)
import code_map  # noqa: E402
import gsd_mission as gm  # noqa: E402
import route_admission as ra  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def line(name: str, ok: bool, ev: str) -> None:
    RESULTS.append((name, ok, ev))
    print(f"CANARY {'OK  ' if ok else 'FAIL'} {name} {ev}")


def lease_arg(forecast: int, phase: str = "1", max_calls: int = tb.CAP) -> dict:
    return {"phase": phase, "forecast": forecast, "state_file": str(tb.STATE), "max_calls": max_calls}


def main(argv: list[str]) -> int:
    target = Path(argv[0]) if argv else HERE / "gsd_mission.py"
    tb.STATE.write_text("---\ncurrent_phase: 1 - canary\n---\n", encoding="utf-8")
    floors = ra.load_floors()
    floor = floors["profiles"][ra.TOP_LEVEL]["floor"]
    bound = tb.CAP * floor

    rec = tb.running("m-canary")
    try:
        gm.set_envelope("m-canary", phase_lease=lease_arg(bound - 1), now=tb.NOW)
        line("forecast-gate-refuses", False, "accepted a forecast below calls x floor")
    except gm.MissionError as exc:
        line("forecast-gate-refuses", "forecast gate UNDERPRICED" in str(exc), str(exc)[:110])
    ok = gm.set_envelope("m-canary", phase_lease=lease_arg(bound), now=tb.NOW)
    line("forecast-gate-control-admits", (ok.get("phase_lease") or {}).get("forecast") == bound,
         f"forecast {bound:,} = {tb.CAP} calls x {floor:,}")

    same = gm.set_envelope("m-canary", phase_lease=lease_arg(bound), now=tb.NOW)
    line("epoch-same-phase-keeps", same.get("wu_packet_epoch") == rec.get("wu_packet_epoch"),
         f"wu_packet_epoch {same.get('wu_packet_epoch')}")
    tb.STATE.write_text("---\ncurrent_phase: 2 - canary\n---\n", encoding="utf-8")
    nxt = gm.set_envelope("m-canary", phase_lease=lease_arg(bound, phase="2"), now=tb.NOW)
    line("epoch-new-phase-moves", nxt.get("wu_packet_epoch") == rec["epoch"],
         f"wu_packet_epoch {nxt.get('wu_packet_epoch')} owner epoch {rec['epoch']}")

    tb.STATE.write_text("---\ncurrent_phase: 1 - canary\n---\n", encoding="utf-8")
    stops: list = []
    tb.running("m-canary-ok")
    tb.CALLS["m-canary-ok"] = tb.CALL_BASE + tb.CAP
    held = tb.sweep("m-canary-ok", stops)
    line("boundary-at-cap-runs", not held.get("owner_hold") and not stops, "6 of 6 calls")
    tb.running("m-canary-trip")
    tb.CALLS["m-canary-trip"] = tb.CALL_BASE + tb.CAP + 1
    held = tb.sweep("m-canary-trip", stops)
    line("boundary-over-cap-holds", bool((held.get("owner_hold") or {}).get("phase_breaker")) and bool(stops),
         "7 of 6 calls")

    with tempfile.TemporaryDirectory(prefix="canary-map-") as d:
        copy = Path(d) / "f.py"
        copy.write_text(target.read_text(encoding="utf-8-sig"), encoding="utf-8")
        store = Path(d) / "store"
        first = code_map.page(copy, store)
        again = code_map.page(copy, store)
        copy.write_text(copy.read_text(encoding="utf-8") + "\n\ndef _canary_added():\n    return 1\n", encoding="utf-8")
        edited = code_map.page(copy, store)
        line("code-map-miss-then-hit", (first["hit"], again["hit"]) == (False, True),
             f"{target.name}: file {first['bytes_file']:,} B -> map {first['bytes_map']:,} B")
        line("code-map-edit-misses", edited["hit"] is False and edited["sha256"] != first["sha256"], "new sha, new page")

    bad = [n for n, ok_, _ in RESULTS if not ok_]
    print(f"CANARY_RESULT={'PASS' if not bad else 'FAIL'} {len(RESULTS) - len(bad)}/{len(RESULTS)}"
          + (f" failed: {', '.join(bad)}" if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
