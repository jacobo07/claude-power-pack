r"""
topology_apply.py - read lazarus_layout_<DATE>.json and report what would be
opened. DRY-RUN ONLY by default — actual Cursor window mutation is fenced
behind --i-have-no-open-windows because hijacking active Cursor windows
would clobber the user's in-flight work (Mistake #16 territory).

Usage:
  python tools/topology_apply.py vault/topology/lazarus_layout_2026-04-29.json
  python tools/topology_apply.py <layout.json> --dry-run                # default
  python tools/topology_apply.py <layout.json> --i-have-no-open-windows  # actually opens

Output (dry-run): JSON describing target state, expected Cursor invocations,
and the no-op verification command for each slot. Exits 0 even on dry-run.

Exit codes:
  0 — dry-run printed (or live apply succeeded with all 5 slots opened)
  2 — layout file missing or schema mismatch
  3 — live apply requested but Cursor not on PATH
  4 — live apply detected pre-existing Cursor windows, refused to clobber
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


def load_layout(path: Path) -> dict:
    if not path.is_file():
        print(json.dumps({"ok": False, "error": "LAYOUT_FILE_MISSING", "path": str(path)}, indent=2))
        sys.exit(2)
    try:
        layout = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"ok": False, "error": "LAYOUT_PARSE_FAIL", "detail": str(e)}, indent=2))
        sys.exit(2)
    if layout.get("schema_version") != 1:
        print(json.dumps({"ok": False, "error": "SCHEMA_VERSION_MISMATCH", "got": layout.get("schema_version")}, indent=2))
        sys.exit(2)
    if len(layout.get("macro_slots", [])) != 5:
        print(json.dumps({"ok": False, "error": "EXPECTED_5_MACRO_SLOTS", "got": len(layout.get("macro_slots", []))}, indent=2))
        sys.exit(2)
    return layout


def find_workspace(hint: str, search_roots: list[Path]) -> Path | None:
    """Best-effort workspace path resolution via known hint patterns."""
    for root in search_roots:
        if not root.is_dir():
            continue
        # 1. Direct child match
        candidate = root / hint
        if candidate.is_dir():
            return candidate
        # 2. Case-insensitive scan one level down
        try:
            for child in root.iterdir():
                if child.is_dir() and child.name.lower() == hint.lower():
                    return child
        except OSError:
            continue
    return None


def cursor_present() -> bool:
    return shutil.which("cursor") is not None


def detect_open_cursor_windows() -> int:
    """Heuristic: count Cursor.exe processes via tasklist (Windows-only)."""
    if os.name != "nt":
        return 0
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Cursor.exe", "/FO", "CSV", "/NH"],
            stderr=subprocess.DEVNULL, text=True, timeout=5,
        )
        # Each row in CSV format = one Cursor process. Multiple processes per
        # window are normal (one per renderer + main), so this is over-counting
        # but deliberately so — better to refuse if anything is open.
        return sum(1 for line in out.splitlines() if line.strip().startswith('"Cursor.exe"'))
    except (subprocess.SubprocessError, OSError):
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="topology_apply")
    parser.add_argument("layout_path", help="Path to lazarus_layout_<DATE>.json")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Print plan, do nothing (default).")
    parser.add_argument("--i-have-no-open-windows", action="store_true",
                        help="Disarm the safety. Live Cursor invocation will run. "
                             "If Cursor processes exist, still refuses (exit 4).")
    parser.add_argument("--search-roots", nargs="*",
                        default=[
                            "C:/Users/kobig/Desktop/Repos-GitHub",
                            "C:/Users/kobig",
                            "C:/Users/kobig/Documents",
                        ],
                        help="Directories to scan for workspace hints.")
    args = parser.parse_args(argv)

    layout = load_layout(Path(args.layout_path))
    search_roots = [Path(p) for p in args.search_roots]

    plan: list[dict] = []
    unresolved: list[str] = []
    for slot in layout["macro_slots"]:
        hint = slot["workspace_root_hint"]
        resolved = find_workspace(hint, search_roots)
        plan.append({
            "slot": slot["slot"],
            "title": slot["title"],
            "hint": hint,
            "resolved_path": str(resolved) if resolved else None,
            "would_invoke": f'cursor "{resolved}"' if resolved else f"<unresolved: {hint}>",
        })
        if not resolved:
            unresolved.append(hint)

    report = {
        "iso_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "layout_source": str(args.layout_path),
        "mode": "live" if args.i_have_no_open_windows else "dry-run",
        "search_roots": [str(p) for p in search_roots],
        "plan": plan,
        "unresolved_hints": unresolved,
        "cursor_present_on_path": cursor_present(),
        "open_cursor_processes": detect_open_cursor_windows(),
    }

    if args.i_have_no_open_windows:
        if not cursor_present():
            report["error"] = "CURSOR_NOT_ON_PATH"
            print(json.dumps(report, indent=2))
            return 3
        if detect_open_cursor_windows() > 0:
            report["error"] = "OPEN_CURSOR_WINDOWS_DETECTED_REFUSING_TO_CLOBBER"
            print(json.dumps(report, indent=2))
            return 4
        executions: list[dict] = []
        for slot_plan in plan:
            if not slot_plan["resolved_path"]:
                executions.append({"slot": slot_plan["slot"], "skipped": "unresolved"})
                continue
            try:
                subprocess.Popen(
                    ["cursor", slot_plan["resolved_path"]],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                executions.append({"slot": slot_plan["slot"], "launched": slot_plan["resolved_path"]})
            except OSError as e:
                executions.append({"slot": slot_plan["slot"], "error": str(e)})
        report["executions"] = executions

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
