#!/usr/bin/env python3
"""Capture-layer liveness gate.

Answers one question no other gate in this repo asks: **did the failure
corpus actually record what the producers observed?**

Origin (vault/specs/capture-layer-liveness.md): between 2026-05-26 and
2026-08-14 the CEPS bridge fired 63 times and recorded 0 events. Every
component reported healthy -- the hook was registered, the module
imported, its unit tests passed, and `events.jsonl` existed. The corpus
was simply empty, and an empty corpus is indistinguishable from a clean
run unless something compares fires against records.

Three rules, each learned from a failure this repo already paid for:

1. **Gate the absolute divergence, never a ratio.** A ratio is satisfied
   by shrinking its denominator (feedback_never_gate_on_a_ratio).
2. **Classify producers by trigger.** MANUAL and SCOPED producers are
   silent by design; scoring them as dead makes the gate cry wolf until
   nobody reads it. Measure what a filter rejects before shipping it
   (feedback_presence_is_not_identity).
3. **Zero fires is not proof of health.** An unwired producer fires zero
   times forever and would pass on divergence alone, so registration in
   the live settings.json is checked independently (feedback_zero_cannot_fall).

Exit 0 = every AUTOMATIC producer is registered and recording.
Exit 1 = at least one is unwired, or fired without recording.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
SETTINGS = HOME / ".claude" / "settings.json"

AUTOMATIC = "AUTOMATIC"
MANUAL = "MANUAL"
SCOPED = "SCOPED"

# Producers are DISCOVERED against the live settings.json rather than
# trusted from this table: a hand-curated audit measures memory, not
# reality (feedback_hand_curated_audit_measures_memory). The table
# declares intent; `registered` is measured.
PRODUCERS = [
    {
        "name": "bug-hunter-ceps-bridge",
        "trigger": AUTOMATIC,
        "hook_marker": "bug-hunter-ceps-bridge.js",
        "fires": PP_ROOT / "vault" / "ceps" / "fires.jsonl",
        "sink": PP_ROOT / "vault" / "ceps" / "events.jsonl",
        "rejections": PP_ROOT / "vault" / "ceps" / "rejections.jsonl",
        # Only losses this producer caused; the ledger is shared with the
        # test suites, which reject invalid input by design.
        "rejection_origin": "hook",
        "note": "PostToolUse failure capture on Bash/PowerShell + harness sentinel",
    },
    {
        "name": "mistake-ingest",
        "trigger": MANUAL,
        "hook_marker": "mistake-ingest.js",
        "sink": PP_ROOT / "vault" / "knowledge_base" / "errors.md",
        "note": "fires only when a human edits mistakes-registry.md -- "
                "a registry mirror, not an automatic observer",
    },
    {
        "name": "bug-hunter-learning",
        "trigger": SCOPED,
        "hook_marker": "bug-hunter-learning.js",
        "sink": HOME / ".claude" / "knowledge_vault" / "02_Doctrine" / "LEARNINGS",
        "note": "emits only inside the InfinityOps holding root; a no-op "
                "in every other repo by design",
    },
    {
        "name": "never-again",
        "trigger": MANUAL,
        "hook_marker": None,
        "sink": PP_ROOT / "vault" / "osa" / "never_again_log.jsonl",
        "note": "written by the pp-never-again agent on Owner request",
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(raw: str) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def count_since(path: Path, cutoff: datetime, origin: str | None = None) -> int:
    """Rows in a .jsonl whose `ts` is at or after cutoff.

    `origin` restricts the count to rows a given caller produced. The
    rejection ledger is shared: test_ceps_edge_cases feeds invalid input on
    purpose, and counting those as production loss would fail this gate on a
    healthy repo until nobody read it.
    """
    if not path or not path.is_file():
        return 0
    total = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if origin is not None and row.get("origin") != origin:
            continue
        ts = _parse_ts(row.get("ts", ""))
        if ts and ts >= cutoff:
            total += 1
    return total


def last_write(path: Path) -> str:
    if not path:
        return "n/a"
    if path.is_dir():
        files = [f for f in path.iterdir() if f.is_file()]
        if not files:
            return "empty-dir"
        newest = max(files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(
            newest.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")
    if not path.exists():
        return "ABSENT"
    return datetime.fromtimestamp(
        path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")


def registered_markers() -> set[str]:
    """Hook basenames present in the LIVE settings.json.

    Canonical-repo presence is not evidence: a hook committed here but
    absent from settings.json is unwired
    (feedback_hook_dispatcher_split_brain_mirror).
    """
    try:
        blob = json.loads(SETTINGS.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return set()
    found: set[str] = set()
    for matchers in (blob.get("hooks") or {}).values():
        for matcher in matchers or []:
            for hook in matcher.get("hooks") or []:
                command = str(hook.get("command", ""))
                found.add(command.replace("\\", "/"))
    return found


def evaluate(window_days: int) -> dict:
    cutoff = _now() - timedelta(days=window_days)
    live = registered_markers()
    rows, failures = [], []

    for spec in PRODUCERS:
        marker = spec.get("hook_marker")
        wired = None
        if marker:
            wired = any(marker in cmd for cmd in live)

        fires = count_since(spec.get("fires"), cutoff)
        records = count_since(spec.get("sink"), cutoff) if str(
            spec.get("sink", "")).endswith(".jsonl") else None
        rejected = count_since(spec.get("rejections"), cutoff,
                               origin=spec.get("rejection_origin"))

        row = {
            "producer": spec["name"],
            "trigger": spec["trigger"],
            "registered": wired,
            "fires_in_window": fires if spec.get("fires") else None,
            "records_in_window": records,
            "rejections_in_window": rejected if spec.get("rejections") else None,
            "sink_last_write": last_write(spec.get("sink")),
            "note": spec["note"],
            "verdict": "OK",
        }

        if spec["trigger"] == AUTOMATIC:
            if wired is False:
                row["verdict"] = "UNWIRED"
                failures.append(
                    f"{spec['name']}: AUTOMATIC producer is absent from "
                    f"{SETTINGS} -- it cannot fire at all")
            elif fires > 0 and (records or 0) == 0:
                row["verdict"] = "FIRES-WITHOUT-RECORDS"
                failures.append(
                    f"{spec['name']}: {fires} fire(s) in {window_days}d "
                    f"produced 0 record(s) in {spec['sink'].name} "
                    f"({rejected} rejection(s) logged)")
            elif rejected > 0:
                row["verdict"] = "PARTIAL-LOSS"
                failures.append(
                    f"{spec['name']}: {rejected} capture(s) rejected in "
                    f"{window_days}d -- see vault/ceps/rejections.jsonl")
        else:
            row["verdict"] = f"EXEMPT-{spec['trigger']}"

        rows.append(row)

    return {
        "window_days": window_days,
        "generated": _now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producers": rows,
        "failures": failures,
        "exit_code": 1 if failures else 0,
    }


def render(report: dict) -> str:
    lines = [
        f"CAPTURE LIVENESS -- {report['window_days']}d window "
        f"({report['generated']})",
        "",
        f"{'producer':<26} {'trigger':<10} {'wired':<6} {'fires':>6} "
        f"{'recs':>6} {'rej':>5}  verdict",
    ]
    for row in report["producers"]:
        def show(value):
            return "-" if value is None else str(value)
        lines.append(
            f"{row['producer']:<26} {row['trigger']:<10} "
            f"{show(row['registered']):<6} {show(row['fires_in_window']):>6} "
            f"{show(row['records_in_window']):>6} "
            f"{show(row['rejections_in_window']):>5}  {row['verdict']}")
    lines.append("")
    if report["failures"]:
        lines.append("FAILURES:")
        lines.extend(f"  - {f}" for f in report["failures"])
    else:
        lines.append("All AUTOMATIC producers registered and recording.")
    lines.append("")
    lines.append(
        f"CAPTURE_LIVENESS={'PASS' if report['exit_code'] == 0 else 'FAIL'}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window-days", type=int, default=7,
                    help="Lookback window in days (default 7).")
    ap.add_argument("--json", action="store_true",
                    help="Emit the report as JSON.")
    args = ap.parse_args()

    report = evaluate(args.window_days)
    print(json.dumps(report, indent=2, default=str) if args.json
          else render(report))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
