#!/usr/bin/env python3
"""lost_chat_recovery.py — safe probe for "lost" Claude session jsonls (BL-0073).

When the Owner reports "I lost my chat" after Alt+F4 / reboot / Lazarus
mismapping, the chat itself is almost never deleted — the .jsonl is still
on disk under ~/.claude/projects/<sanitized-cwd>/. The "loss" is one of:

  (a) Lazarus pointed `claude --resume` at the wrong UUID (T1/T2/T3 miss
      -> T4 fallback `--continue` -> fresh session.)
  (b) BL-0013 hide-live renamed `<uuid>.jsonl` to `<uuid>.jsonl.live`,
      hiding it from the native /resume picker.
  (c) Two simultaneous panes raced to write the same .jsonl, producing
      `<uuid>.jsonl.conflict.<ISO>` siblings.

Read-only. Prints a `claude --resume <uuid>` command IF safe; refuses if
the UUID is currently live (would race the writer -> third .conflict.*).

Usage:
  python lost_chat_recovery.py <uuid>
  python lost_chat_recovery.py --cwd <path> <uuid>
  python lost_chat_recovery.py --force-after-merge <uuid>
  python lost_chat_recovery.py --json <uuid>

Exit codes:
  0  - safe to resume; resume command printed
  10 - UUID is the current session (no recovery needed)
  11 - UUID is live in another pane (refuse)
  12 - UUID has .conflict.* siblings without --force-after-merge
  13 - UUID not found anywhere
  2  - argument error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PROJECTS_DIR = HOME / ".claude" / "projects"
LAZARUS_DIR = HOME / ".claude" / "lazarus"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
HEARTBEAT_FRESH_S = 60


def sanitize_cwd_to_project_id(cwd: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9-]", "-", str(cwd))


def find_jsonls(uuid: str) -> dict:
    out: dict[str, dict] = {}
    if not PROJECTS_DIR.is_dir():
        return out
    for proj in PROJECTS_DIR.iterdir():
        if not proj.is_dir():
            continue
        bucket: dict = {"conflicts": []}
        plain = proj / f"{uuid}.jsonl"
        live = proj / f"{uuid}.jsonl.live"
        if plain.is_file():
            bucket["jsonl"] = plain
        if live.is_file():
            bucket["live"] = live
        for f in proj.iterdir():
            if f.is_file() and f.name.startswith(f"{uuid}.jsonl.conflict."):
                bucket["conflicts"].append(f)
        if any(k in bucket for k in ("jsonl", "live")) or bucket["conflicts"]:
            out[proj.name] = bucket
    return out


def find_heartbeat(uuid: str) -> tuple[Path | None, dict | None, float | None]:
    if not LAZARUS_DIR.is_dir():
        return None, None, None
    for proj in LAZARUS_DIR.iterdir():
        if not proj.is_dir():
            continue
        hb = proj / "heartbeats" / f"{uuid}.lock"
        if not hb.is_file():
            continue
        try:
            mtime = hb.stat().st_mtime
            age = time.time() - mtime
        except OSError:
            return hb, None, None
        try:
            data = json.loads(hb.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            data = None
        return hb, data, age
    return None, None, None


def emit(payload: dict, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
        return
    print(f"[lost-chat] uuid     : {payload['uuid']}")
    print(f"[lost-chat] verdict  : {payload['verdict']}")
    if payload.get("reason"):
        print(f"[lost-chat] reason   : {payload['reason']}")
    files = payload.get("files", {})
    if files:
        print(f"[lost-chat] files    :")
        for proj, bucket in files.items():
            print(f"  project: {proj}")
            if bucket.get("jsonl"):
                print(f"    .jsonl       -> {bucket['jsonl']}")
            if bucket.get("live"):
                print(f"    .jsonl.live  -> {bucket['live']}")
            for c in bucket.get("conflicts", []):
                print(f"    .conflict    -> {c}")
    if payload.get("heartbeat"):
        hb = payload["heartbeat"]
        print(f"[lost-chat] heartbeat: cwd={hb.get('cwd')}  age={hb.get('age_s', '?')}s")
    if payload.get("resume_command"):
        print()
        print(f"[lost-chat] safe to resume - run from a fresh terminal:")
        print(f"    {payload['resume_command']}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("uuid", help="session UUID to probe")
    p.add_argument("--cwd", default=None, help="cwd of the calling pane (default: $PWD)")
    p.add_argument("--force-after-merge", action="store_true",
                   help="bypass .conflict.* refusal - only after manual review")
    p.add_argument("--json", action="store_true", help="machine-readable JSON")
    args = p.parse_args(argv)

    if not UUID_RE.match(args.uuid):
        sys.stderr.write(f"lost_chat_recovery: not a UUID v4: {args.uuid!r}\n")
        return 2

    cwd = Path(args.cwd or os.getcwd())
    cwd_pid = sanitize_cwd_to_project_id(cwd)

    files = find_jsonls(args.uuid)
    hb_path, hb_data, hb_age = find_heartbeat(args.uuid)

    files_serial = {
        proj: {
            **({"jsonl": str(b["jsonl"])} if b.get("jsonl") else {}),
            **({"live": str(b["live"])} if b.get("live") else {}),
            "conflicts": [str(c) for c in b.get("conflicts", [])],
        }
        for proj, b in files.items()
    }

    payload: dict = {"uuid": args.uuid, "files": files_serial, "heartbeat": None}
    if hb_path is not None:
        payload["heartbeat"] = {
            "path": str(hb_path),
            "age_s": int(hb_age) if hb_age is not None else None,
            "cwd": (hb_data or {}).get("cwd"),
            "pid": (hb_data or {}).get("pid"),
        }

    if not files and hb_path is None:
        payload["verdict"] = "NOT_FOUND"
        payload["reason"] = "no .jsonl, no .jsonl.live, no heartbeat anywhere"
        emit(payload, args.json)
        return 13

    if hb_path is not None and hb_age is not None and hb_age < HEARTBEAT_FRESH_S:
        hb_cwd = (hb_data or {}).get("cwd") or ""
        try:
            same = Path(hb_cwd).resolve() == cwd.resolve()
        except (OSError, ValueError):
            same = (hb_cwd == str(cwd))
        if same:
            payload["verdict"] = "CURRENT_SESSION"
            payload["reason"] = (
                "heartbeat fresh AND cwd matches - this UUID IS the session you are in. "
                "No recovery needed; the chat is not lost. The .jsonl.live (if present) "
                "is the live writer's open fd target. After this session ends gracefully, "
                "lazarus_orphan_purge.py will rename .jsonl.live -> .jsonl so the native "
                "/resume picker shows it again."
            )
            emit(payload, args.json)
            return 10
        else:
            total = sum(len(b["conflicts"]) for b in files.values())
            payload["verdict"] = "LIVE_ELSEWHERE"
            payload["reason"] = (
                f"heartbeat fresh ({int(hb_age)}s) in another pane (cwd={hb_cwd}). "
                f"Refusing to suggest a resume - would race the live writer and "
                f"likely produce a third .conflict.* sibling (already {total} priors)."
            )
            emit(payload, args.json)
            return 11

    total_conflicts = sum(len(b["conflicts"]) for b in files.values())
    if total_conflicts > 0 and not args.force_after_merge:
        payload["verdict"] = "PRIOR_CONFLICTS"
        payload["reason"] = (
            f"{total_conflicts} .jsonl.conflict.* sibling(s) on disk. This UUID "
            f"has been double-written before - resuming without manual merge "
            f"risks losing whichever branch you don't pick. Pass --force-after-merge "
            f"AFTER you have reviewed the conflicts."
        )
        emit(payload, args.json)
        return 12

    chosen_project: str | None = None
    for proj, b in files.items():
        if proj == cwd_pid and (b.get("jsonl") or b.get("live")):
            chosen_project = proj
            break
    if chosen_project is None:
        for proj, b in files.items():
            if b.get("jsonl") or b.get("live"):
                chosen_project = proj
                break

    if chosen_project is None:
        payload["verdict"] = "NOT_FOUND"
        payload["reason"] = "found .conflict.* siblings but no usable .jsonl or .jsonl.live"
        emit(payload, args.json)
        return 13

    payload["verdict"] = "RESUMEABLE"
    payload["resume_command"] = f"claude --resume {args.uuid}"
    payload["chosen_project"] = chosen_project
    emit(payload, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
