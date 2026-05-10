#!/usr/bin/env python3
"""lazarus_orphan_purge.py - retire .jsonl.live orphans across all projects (BL-0073).

Now that the BL-0013 hide-live hook is retired (resume-hide-live.js soft-deleted),
the `.jsonl.live` files left on disk are orphans. Decision matrix per .jsonl.live:

  | sibling .jsonl exists? | heartbeat | action                                |
  |------------------------|-----------|---------------------------------------|
  | yes                    | fresh     | SKIP (live writer; do not race)       |
  | yes                    | stale     | rename .live -> .jsonl.live.archive.<ISO>; keep both for manual review |
  | no                     | fresh     | SKIP (live writer)                    |
  | no                     | stale     | rename .live -> .jsonl (restore)      |

Conservative: when both files exist and writer has gone, archive (don't delete);
the Owner picks which content to keep.

Default --dry-run; pass --apply to mutate.

Usage:
  python lazarus_orphan_purge.py                   # dry-run, all projects
  python lazarus_orphan_purge.py --apply           # apply, all projects
  python lazarus_orphan_purge.py --project <id>    # restrict to one project
  python lazarus_orphan_purge.py --json            # machine-readable
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PROJECTS_DIR = HOME / ".claude" / "projects"
LAZARUS_DIR = HOME / ".claude" / "lazarus"
HEARTBEAT_FRESH_S = 5 * 60


def heartbeat_age(project_id: str, uuid: str) -> float | None:
    hb = LAZARUS_DIR / project_id / "heartbeats" / f"{uuid}.lock"
    try:
        return time.time() - hb.stat().st_mtime
    except OSError:
        return None


def iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def scan(target_project: str | None) -> list[dict]:
    rows: list[dict] = []
    if not PROJECTS_DIR.is_dir():
        return rows
    iso = iso_now()
    for proj in sorted(PROJECTS_DIR.iterdir()):
        if not proj.is_dir():
            continue
        if target_project and proj.name != target_project:
            continue
        for f in proj.iterdir():
            if not (f.is_file() and f.name.endswith(".jsonl.live")):
                continue
            uuid = f.name[:-len(".jsonl.live")]
            sibling = proj / f"{uuid}.jsonl"
            sibling_exists = sibling.is_file()
            age = heartbeat_age(proj.name, uuid)
            fresh = age is not None and age < HEARTBEAT_FRESH_S

            if fresh:
                action = "SKIP_LIVE"
                target = None
            elif sibling_exists:
                action = "ARCHIVE"
                target = proj / f"{uuid}.jsonl.live.archive.{iso}"
            else:
                action = "RESTORE"
                target = proj / f"{uuid}.jsonl"

            rows.append({
                "project": proj.name,
                "uuid": uuid,
                "live_path": str(f),
                "sibling_jsonl_exists": sibling_exists,
                "heartbeat_age_s": int(age) if age is not None else None,
                "fresh": fresh,
                "action": action,
                "target": str(target) if target else None,
            })
    return rows


def apply_one(row: dict) -> tuple[bool, str]:
    src = Path(row["live_path"])
    if row["action"] == "SKIP_LIVE":
        return True, "skip (live writer)"
    if row["action"] == "RESTORE":
        dst = Path(row["target"])
        if dst.exists():
            return False, f"target exists: {dst}"
        try:
            src.rename(dst)
            return True, f"restored -> {dst.name}"
        except OSError as e:
            return False, f"rename failed: {e}"
    if row["action"] == "ARCHIVE":
        dst = Path(row["target"])
        try:
            src.rename(dst)
            return True, f"archived -> {dst.name}"
        except OSError as e:
            return False, f"rename failed: {e}"
    return False, f"unknown action: {row['action']}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", default=None, help="restrict to one project_id")
    p.add_argument("--apply", action="store_true", help="actually mutate (default: dry-run)")
    p.add_argument("--json", action="store_true", help="machine-readable")
    args = p.parse_args(argv)

    rows = scan(args.project)
    summary = {
        "total": len(rows),
        "by_action": {},
        "applied_ok": 0,
        "applied_fail": 0,
        "dry_run": not args.apply,
    }
    for r in rows:
        summary["by_action"][r["action"]] = summary["by_action"].get(r["action"], 0) + 1

    if args.apply:
        for r in rows:
            ok, msg = apply_one(r)
            r["apply_ok"] = ok
            r["apply_msg"] = msg
            if r["action"] != "SKIP_LIVE":
                if ok:
                    summary["applied_ok"] += 1
                else:
                    summary["applied_fail"] += 1

    if args.json:
        sys.stdout.write(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n")
    else:
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"[orphan-purge] mode={mode}  total={summary['total']}  by_action={summary['by_action']}")
        for r in rows:
            tag = ""
            if args.apply:
                tag = "  OK" if r.get("apply_ok") else "  FAIL"
                if r.get("apply_msg"):
                    tag += f": {r['apply_msg']}"
            print(f"  {r['action']:<10} {r['project'][:40]:<40} {r['uuid']}  age={r['heartbeat_age_s']}s{tag}")
        if args.apply:
            print(f"[orphan-purge] applied: ok={summary['applied_ok']} fail={summary['applied_fail']}")
        else:
            print(f"[orphan-purge] dry-run only - pass --apply to mutate")
    return 0 if summary["applied_fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
