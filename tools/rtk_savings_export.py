#!/usr/bin/env python3
"""rtk_savings_export.py — thin, decoupled JSON exporter of RTK savings.

Combines two real, already-shipped data sources:

  1. `rtk gain --format json` — global summary aggregates
     (total_commands, total_input, total_output, total_saved,
     avg_savings_pct). No per-cmd breakdown — verified.
  2. `vault/telemetry/rtk_<sid>.jsonl` — the parallel-stream adoption
     telemetry written by `modules/rtk-core/rtk-rewrite.js` on every
     PreToolUse(Bash) call. Rows carry `cmd_first_token` and a
     `rewritten:bool` flag, never a fabricated per-call savings figure.

Emits `vault/telemetry/rtk_savings_<sid>.json` with a stable schema so
future consumers (e.g. budget_monitor.py) can read RTK adoption +
summary without reaching into rtk internals. The exporter NEVER invents
a per-call savings number — only counts adoption and republishes the
honest summary that rtk itself produced.

Session-id precedence: `CLAUDE_SESSION_ID` env -> hostname-pid-startts.
Never cwd-hash (would collide across parallel panes in the same cwd).
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TELEMETRY_DIR = REPO / "vault" / "telemetry"
RTK_BIN = Path(os.environ.get("RTK_BIN") or
               Path.home() / ".claude" / "bin" / "rtk.exe")
SCHEMA_VERSION = "1.0"


def _resolve_sid() -> str:
    """CLAUDE_SESSION_ID env -> hostname-pid-startts(ms). Never cwd-hash."""
    raw = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    if raw:
        return _sanitize(raw)
    host = socket.gethostname() or "host"
    return _sanitize(f"{host}-{os.getpid()}-{int(time.time() * 1000)}")


def _sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "-", s)[:64] or "no-sid"


def _rtk_gain_summary() -> dict:
    """`rtk gain --format json` -> {'summary': {...}} or {} on any failure."""
    if not RTK_BIN.is_file():
        return {"_note": "rtk-binary-absent"}
    try:
        r = subprocess.run([str(RTK_BIN), "gain", "--format", "json"],
                            capture_output=True, timeout=20)
    except Exception as exc:  # noqa: BLE001
        return {"_note": f"rtk-gain-spawn-error:{exc}"}
    if r.returncode != 0:
        return {"_note": f"rtk-gain-exit:{r.returncode}"}
    try:
        d = json.loads(r.stdout.decode("utf-8", "replace"))
    except Exception as exc:  # noqa: BLE001
        return {"_note": f"rtk-gain-parse:{exc}"}
    summary = d.get("summary") or {}
    if not isinstance(summary, dict):
        return {"_note": "rtk-gain-bad-shape"}
    return {
        "total_commands": int(summary.get("total_commands") or 0),
        "total_input_tokens": int(summary.get("total_input") or 0),
        "total_output_tokens": int(summary.get("total_output") or 0),
        "saved_tokens": int(summary.get("total_saved") or 0),
        "saved_pct": float(summary.get("avg_savings_pct") or 0.0),
        "total_time_ms": int(summary.get("total_time_ms") or 0),
    }


def _aggregate_adoption(sid: str) -> dict:
    """Aggregate vault/telemetry/rtk_<sid>.jsonl rows for THIS session.

    If no row exists for the resolved sid, fall back to merging ALL
    rtk_*.jsonl files (cross-session aggregate — explicitly labeled).
    Always honest: rows count rewrites/passthroughs by cmd_first_token,
    never per-call savings.
    """
    by_cmd: Counter = Counter()
    rewrites = 0
    passthroughs = 0
    rows = 0
    scope = "this-session"

    target = TELEMETRY_DIR / f"rtk_{sid}.jsonl"
    files: list[Path]
    if target.is_file():
        files = [target]
    else:
        files = sorted(TELEMETRY_DIR.glob("rtk_*.jsonl"))
        if files:
            scope = "all-sessions"
        else:
            return {
                "scope": "no-telemetry",
                "rows": 0, "rewrites": 0, "passthroughs": 0, "by_cmd": [],
            }

    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            rows += 1
            tok = (row.get("cmd_first_token") or "").lower()
            if tok and not tok.startswith("rtk"):
                by_cmd[tok] += 1
            if row.get("rewritten"):
                rewrites += 1
            else:
                passthroughs += 1

    by_cmd_list = [{"cmd": c, "count": n}
                   for c, n in by_cmd.most_common(20)]
    return {
        "scope": scope,
        "rows": rows,
        "rewrites": rewrites,
        "passthroughs": passthroughs,
        "by_cmd": by_cmd_list,
    }


def main() -> int:
    sid = _resolve_sid()
    summary = _rtk_gain_summary()
    adoption = _aggregate_adoption(sid)

    out = {
        "schema_version": SCHEMA_VERSION,
        "ts": int(time.time()),
        "session_id": sid,
        "session_id_source": ("env-CLAUDE_SESSION_ID"
                              if os.environ.get("CLAUDE_SESSION_ID")
                              else "hostname-pid-startts"),
        "rtk_summary": summary,
        "adoption": adoption,
        "source_note": (
            "rtk_summary from `rtk gain --format json`; adoption.by_cmd "
            "from vault/telemetry/rtk_<sid>.jsonl row aggregation "
            "(cmd_first_token + rewritten flag). Adoption never claims "
            "per-call output savings — those are unmeasurable at "
            "PreToolUse time. Any future budget tool combines adoption "
            "counts with the static benchmark in measure_compression.py "
            "/ verify_rtk_fusion.py."
        ),
    }

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TELEMETRY_DIR / f"rtk_savings_{sid}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")

    print(f"rtk_savings_export: wrote {out_path}")
    print(f"  session_id={sid}  ({out['session_id_source']})")
    if "_note" in summary:
        print(f"  rtk_summary: {summary['_note']}")
    else:
        print(f"  rtk_summary: total_cmds={summary['total_commands']}  "
              f"saved={summary['saved_tokens']}t  "
              f"avg_pct={summary['saved_pct']:.1f}%")
    print(f"  adoption: scope={adoption['scope']}  rows={adoption['rows']}  "
          f"rewrites={adoption['rewrites']}  "
          f"passthroughs={adoption['passthroughs']}  "
          f"unique_cmds={len(adoption['by_cmd'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
