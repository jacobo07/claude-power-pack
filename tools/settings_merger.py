#!/usr/bin/env python3
"""settings_merger.py - safe deep-merge into ~/.claude/settings.json.

Owner-authorized self-modification tool (operator answered Q2=(a) on
2026-05-15). Reads the live settings.json (utf-8-sig — strips any BOM
introduced by PowerShell tools), validates JSON, writes a timestamped
backup, deep-merges a single hook block into hooks.<EVENT>[], then writes
atomically via os.replace().

Contract:
  - Round-trip preserves every existing field byte-equivalent (json.loads
    comparison, not raw bytes — comments aren't legal in JSON anyway).
  - Idempotent: if an entry with the same `command` already exists under
    hooks.<EVENT>[], the merge is a no-op and exits 0.
  - The diff is bounded: ONLY hooks.<EVENT>[] grows by exactly one
    element. Any other delta fails the post-write assertion (exit 5).

Usage:
  settings_merger.py register-stop --node-script <abs/path/to/hook.js>
                                   [--timeout 5]

Why not jq: PowerShell tooling regularly writes the file with a UTF-8
BOM, breaking strict jq. Python json+utf-8-sig is universally robust on
Win+POSIX.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
import shutil
import sys
import tempfile
import time

DEFAULT_SETTINGS = os.path.join(
    os.path.expandvars(r"%USERPROFILE%"), ".claude", "settings.json"
)
NODE_CMD = '"/c/Program Files/nodejs/node.exe"'


def _normalize_cmd(cmd: str) -> str:
    """Match heuristic — strip outer quotes + collapse path separators."""
    return cmd.replace("\\", "/").replace('"', "").strip().lower()


def _block_exists(event_arr, node_script: str) -> bool:
    target = _normalize_cmd(node_script)
    for entry in event_arr:
        for hook in entry.get("hooks", []):
            if hook.get("type") == "command":
                if target in _normalize_cmd(hook.get("command", "")):
                    return True
    return False


def register_stop(settings_path: str, node_script: str, timeout: int) -> int:
    if not os.path.isfile(settings_path):
        print(f"settings_merger: settings.json not found at {settings_path}",
              file=sys.stderr)
        return 5

    # Read with utf-8-sig so any BOM is stripped (PowerShell trap).
    with open(settings_path, "r", encoding="utf-8-sig") as fh:
        original_text = fh.read()
    try:
        data = json.loads(original_text)
    except ValueError as e:
        print(f"settings_merger: malformed JSON: {e}", file=sys.stderr)
        return 5
    if not isinstance(data, dict):
        print("settings_merger: top-level must be an object", file=sys.stderr)
        return 5

    hooks = data.setdefault("hooks", {})
    stop = hooks.setdefault("Stop", [])
    if not isinstance(stop, list):
        print("settings_merger: hooks.Stop is not a list", file=sys.stderr)
        return 5

    # Idempotency: same command already present -> no-op exit 0.
    if _block_exists(stop, node_script):
        print(f"settings_merger: already registered ({node_script})")
        return 0

    # Build new entry. node-script path is forced into forward slashes for
    # Git-Bash/POSIX parser compatibility; the surrounding outer string is
    # double-quoted so spaces in the path (rare) survive shell parsing.
    fwd = node_script.replace("\\", "/")
    new_entry = {
        "hooks": [
            {
                "type": "command",
                "command": f'{NODE_CMD} "{fwd}"',
                "timeout": int(timeout),
            }
        ]
    }
    # Round-trip safety: snapshot pre-merge, mutate copy, write copy.
    before_snapshot = copy.deepcopy(data)
    stop.append(new_entry)

    # Atomic write: tmp in same dir -> os.replace().
    backup_path = f"{settings_path}.bak-{int(time.time())}"
    shutil.copy2(settings_path, backup_path)

    fd, tmp_path = tempfile.mkstemp(
        prefix=".settings_merger.", suffix=".json",
        dir=os.path.dirname(settings_path)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            json.dump(data, out, indent=2, ensure_ascii=False)
            out.write("\n")
        os.replace(tmp_path, settings_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        # restore backup on failure
        shutil.copy2(backup_path, settings_path)
        raise

    # Post-write validation: parse, confirm bounded diff.
    with open(settings_path, "r", encoding="utf-8-sig") as fh:
        after = json.loads(fh.read())

    # Bounded-diff: subtract before from after at top level.
    # Only allowed change: hooks.Stop grew by exactly one element matching
    # the new entry. Every other field is byte-equivalent under json.loads.
    fail = []
    for k in set(before_snapshot.keys()) | set(after.keys()):
        if k == "hooks":
            continue
        if before_snapshot.get(k) != after.get(k):
            fail.append(k)
    if fail:
        print(f"settings_merger: unexpected diff outside hooks: {fail}",
              file=sys.stderr)
        # rollback
        shutil.copy2(backup_path, settings_path)
        return 5
    # hooks must differ only in the Stop event array's tail.
    bh = before_snapshot.get("hooks", {})
    ah = after.get("hooks", {})
    for k in set(bh.keys()) | set(ah.keys()):
        if k == "Stop":
            continue
        if bh.get(k) != ah.get(k):
            fail.append(f"hooks.{k}")
    if fail:
        print(f"settings_merger: unexpected diff inside hooks: {fail}",
              file=sys.stderr)
        shutil.copy2(backup_path, settings_path)
        return 5
    before_stop = bh.get("Stop", [])
    after_stop = ah.get("Stop", [])
    if len(after_stop) != len(before_stop) + 1:
        print(f"settings_merger: Stop length delta != +1 "
              f"({len(before_stop)} -> {len(after_stop)})", file=sys.stderr)
        shutil.copy2(backup_path, settings_path)
        return 5
    if after_stop[:-1] != before_stop:
        print("settings_merger: Stop prefix mutated (not append-only)",
              file=sys.stderr)
        shutil.copy2(backup_path, settings_path)
        return 5

    print(f"settings_merger: OK  registered={node_script}  "
          f"backup={os.path.basename(backup_path)}  "
          f"stop_len={len(before_stop)}->{len(after_stop)}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    rs = sub.add_parser("register-stop",
                        help="Register a Stop-event command hook")
    rs.add_argument("--node-script", required=True,
                    help="absolute path to the Node hook script")
    rs.add_argument("--timeout", type=int, default=5,
                    help="hook timeout in seconds (default 5)")
    rs.add_argument("--settings", default=DEFAULT_SETTINGS,
                    help="path to settings.json (default ~/.claude/...)")
    a = ap.parse_args()
    if a.cmd == "register-stop":
        return register_stop(a.settings, a.node_script, a.timeout)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
