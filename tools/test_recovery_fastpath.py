#!/usr/bin/env python3
"""V-RFP-* -- parity between hooks/recovery_fastpath.js and tools/recovery_epoch_gate.py (C3,
vault/plans/pillar-k-resident-prefix-2026-10-05.md, audit gap 6).

The fast path may SKIP the gate only when running the gate would change nothing that matters:
same printed line, no new epoch, no new verdict. So every case drives BOTH on the same temp
state dir: the real node predicate and the real python gate (subprocess, --state-dir), never
a re-implementation of either. Skip cases run the gate on a COPY and compare its output with
the line the fast path would print; run cases assert the gate does real work there.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
FASTPATH = PP / "hooks" / "recovery_fastpath.js"
GATE = PP / "tools" / "recovery_epoch_gate.py"
REAL_HIST = Path.home() / ".claude" / "state" / "pane_map_history"
PASS = FAIL = 0


def check(gate: str, ok: bool, ev: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS {gate}")
    else:
        FAIL += 1
        print(f"  FAIL {gate} -- {ev}")


def node(state: Path, env: dict | None = None) -> dict:
    js = ("const r=require(process.argv[1]).recoveryFastPath(process.argv[2]);"
          "process.stdout.write(JSON.stringify(r));")
    p = subprocess.run(["node", "-e", js, str(FASTPATH), str(state)], capture_output=True, text=True,
                       encoding="utf-8", timeout=60, env=dict(os.environ, **(env or {})))
    return json.loads(p.stdout or "{}")


def gate(state: Path) -> str:
    p = subprocess.run([sys.executable, str(GATE), "--state-dir", str(state)], capture_output=True,
                       text=True, encoding="utf-8", timeout=120,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return p.stdout.strip()


def epoch_of(state: Path) -> dict:
    p = state / "recovery_epoch.json"
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.is_file() else {}


def beacon(state: Path, kind: str, ts: str) -> None:
    (state / "power_beacon.json").write_text(json.dumps({"kind": kind, "ts": ts}), encoding="utf-8")


def gate_on_copy(state: Path) -> tuple[str, dict]:
    with tempfile.TemporaryDirectory() as td:
        c = Path(td) / "s"
        shutil.copytree(state, c)
        return gate(c), epoch_of(c)


def main() -> int:
    refs = sorted(REAL_HIST.glob("pane_map_*.json")) if REAL_HIST.is_dir() else []
    ref_src = next((r for r in reversed(refs) if r.stat().st_size > 1000), None)
    if ref_src is None:
        print("  FAIL V-RFP-PRECONDITION -- no real pane_map snapshot to build a non-trivial reference")
        return 1
    now = datetime.now(timezone.utc)
    recent = now.isoformat(timespec="seconds")          # after boot: not an interruption
    ancient = "2000-01-01T00:00:00+00:00"                # before boot: an interruption

    with tempfile.TemporaryDirectory() as td:
        s = Path(td) / "state"
        s.mkdir()

        # 1. Nothing on disk: both silent, gate writes nothing.
        r = node(s)
        out = gate(s)
        check("V-RFP-EMPTY-SKIP-SILENT", r.get("run") is False and r.get("line") is None and out == ""
              and not (s / "recovery_epoch.json").exists(), f"{r} {out!r}")

        # 2./3. Graceful old beacon, and active beacon written after boot: no interruption possible.
        beacon(s, "graceful", ancient)
        r, out = node(s), gate(s)
        check("V-RFP-GRACEFUL-SKIP", r.get("run") is False and out == "" and not epoch_of(s), f"{r} {out!r}")
        beacon(s, "active", recent)
        r, out = node(s), gate(s)
        check("V-RFP-ACTIVE-AFTER-BOOT-SKIP", r.get("run") is False and out == "" and not epoch_of(s),
              f"{r} {out!r}")

        # 4. Active beacon from BEFORE boot: the gate opens an epoch, so the fast path MUST run it.
        beacon(s, "active", ancient)
        r = node(s)
        check("V-RFP-INTERRUPTION-RUNS", r.get("run") is True, str(r))
        gate(s)
        check("V-RFP-INTERRUPTION-IS-REAL", epoch_of(s).get("status") == "open",
              "control: the gate did not open an epoch, so case 4 proved nothing")
        # Naive timestamp (no zone) is UTC to python; must still read as before-boot here.
        beacon(s, "active", "2000-01-01T00:00:00")
        check("V-RFP-NAIVE-TS-UTC", node(s).get("run") is True, "naive ts read as local time?")

        # Fresh open epoch with a real reference, beacon after boot (only branch b can apply).
        shutil.rmtree(s)
        s.mkdir()
        hist = s / "pane_map_history"
        hist.mkdir()
        ref_name = ref_src.name
        shutil.copyfile(ref_src, hist / ref_name)
        (s / "pane_map.json").write_text(json.dumps({"panes": []}), encoding="utf-8")
        (s / "recovery_epoch.json").write_text(json.dumps({
            "schema_version": 1, "status": "open", "interrupted_at": "2026-10-03T01:35:59+00:00",
            "reference_file": ref_name, "verdict": None, "missing": [], "judged_at": None}), encoding="utf-8")
        beacon(s, "active", recent)

        # 5. Open but never judged with a hash -> run; the gate prints the FULL line once.
        r = node(s)
        check("V-RFP-UNJUDGED-RUNS", r.get("run") is True, str(r))
        full = gate(s)
        ep = epoch_of(s)
        check("V-RFP-FULL-LINE-ONCE", "did not come back whole" in full and ep.get("announced_at")
              and ep.get("judged_input_sha") and ep.get("reminder_line"), f"{full[:120]!r} {list(ep)}")

        # 6. Nothing changed -> skip with the stored reminder; the gate on a copy prints the SAME line.
        r = node(s)
        copy_out, copy_ep = gate_on_copy(s)
        check("V-RFP-UNCHANGED-SKIPS", r.get("run") is False and r.get("line") == ep.get("reminder_line"), str(r))
        check("V-RFP-SKIP-PARITY-LINE", copy_out == r.get("line"), f"gate={copy_out!r} fastpath={r.get('line')!r}")
        check("V-RFP-SKIP-PARITY-VERDICT", copy_ep.get("verdict") == ep.get("verdict")
              and copy_ep.get("judged_input_sha") == ep.get("judged_input_sha")
              and copy_ep.get("status") == ep.get("status"), f"{copy_ep.get('verdict')} vs {ep.get('verdict')}")

        # 7. pane_map bytes change -> run; the re-judged line is the reminder, not the full one.
        (s / "pane_map.json").write_text(json.dumps({"panes": []}) + "\n", encoding="utf-8")
        check("V-RFP-CHANGED-RUNS", node(s).get("run") is True, "changed pane_map skipped")
        out = gate(s)
        check("V-RFP-REMINDER-AFTER-ANNOUNCE", out.startswith("[recovery] still") and "did not come back" not in out,
              repr(out[:120]))

        # 8. BOM-prefixed epoch (PS 5.1 writers) still parses on the node side.
        raw = (s / "recovery_epoch.json").read_text(encoding="utf-8")
        (s / "recovery_epoch.json").write_text("﻿" + raw, encoding="utf-8")
        r = node(s)
        check("V-RFP-BOM-EPOCH", r.get("run") is False and r.get("line"), str(r))
        (s / "recovery_epoch.json").write_text(raw, encoding="utf-8")

        # 9. A verdict written by another path (the manual CLI) drops the hash -> the next start re-judges.
        subprocess.run([sys.executable, "-c",
                        "import sys; sys.path.insert(0, sys.argv[1]);"
                        "from modules.session_resilience import epoch;"
                        "epoch.record_verdict(sys.argv[2], 'FAILED', ['x'])", str(PP), str(s)],
                       check=True, timeout=60)
        check("V-RFP-FOREIGN-VERDICT-RUNS", node(s).get("run") is True and not epoch_of(s).get("judged_input_sha"),
              str(epoch_of(s).get("judged_input_sha")))

        # 10. Kill switch.
        gate(s)  # re-judge so the skip branch would otherwise apply
        check("V-RFP-KILL-SWITCH", node(s).get("run") is False
              and node(s, {"CPP_RECOVERY_FASTPATH": "off"}).get("run") is True, "switch ignored")

        # 11. The board comes back -> RECOVERED closes the epoch; afterwards both are silent.
        shutil.copyfile(hist / ref_name, s / "pane_map.json")
        check("V-RFP-RECOVERY-RUNS", node(s).get("run") is True, "restored board skipped")
        out = gate(s)
        r = node(s)
        check("V-RFP-RECOVERED-CLOSES", out == "" and epoch_of(s).get("status") == "closed"
              and r.get("run") is False and r.get("line") is None, f"{out!r} {epoch_of(s).get('status')} {r}")

    print(f"RFP_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
