"""Strip the `conhost.exe --headless` wrapper from Claude Code hook commands.

MEASURED 2026-09-11, and the measurement is the whole argument:

    conhost.exe --headless cmd.exe /d /c "echo hi"   ->  0 bytes captured
    cmd.exe /d /c "echo hi"                          ->  4 bytes ("hi\\r\\n")

`conhost --headless` allocates a pseudoconsole. Its output does not travel back
through the parent's stdout pipe -- it is written DIRECTLY to the attached
terminal, out of band, and that write carries the console init/teardown escape
sequences: `ESC[?25l`, `ESC[2J`, `ESC[H`, `ESC]0;title`. `ESC[2J` erases the
display and `ESC[H` homes the cursor.

So a hook wrapped this way does two things nobody asked it to do:

  1. It CLEARS THE OWNER'S SCREEN on every event it is registered for. Wired on
     PreToolUse with matcher "*", that is every tool call in every repository --
     which is exactly the shape of "me pasa en todos mis repos".
  2. It DISCARDS the wrapped command's output, so whatever the hook wanted to
     report never reaches the agent. The integration is half-dead and silent
     about it.

The repair keeps the integration and removes the wrapper: the wrapped argv is
promoted to the hook command itself. A console child of an already-console
process inherits the console, so no window is created and nothing flashes --
which is the only thing `--headless` was buying.

Idempotent by construction: a second run finds nothing to change.

Usage:
    python tools/fix_conhost_hook_leak.py                 # report only
    python tools/fix_conhost_hook_leak.py --apply         # rewrite + backup
    python tools/fix_conhost_hook_leak.py --settings PATH
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import os
import shutil
import sys
from pathlib import Path

DEFAULT_SETTINGS = Path(os.path.expanduser("~")) / ".claude" / "settings.json"


def _is_conhost_wrapper(entry: dict) -> bool:
    """A hook entry whose command is conhost.exe and whose first arg is --headless.

    Deliberately narrow. It matches the WRAPPER, never a hook that legitimately
    runs conhost for its own sake, and never a bare `--headless` on some other
    executable.
    """
    cmd = entry.get("command")
    args = entry.get("args")
    if not isinstance(cmd, str) or not isinstance(args, list) or len(args) < 2:
        return False
    if Path(cmd).name.lower() != "conhost.exe":
        return False
    return isinstance(args[0], str) and args[0].lower() == "--headless"


def _unwrap(entry: dict) -> dict:
    """Promote the wrapped argv into the entry itself. Every other key survives."""
    args = entry["args"]
    out = dict(entry)
    out["command"] = args[1]
    rest = args[2:]
    if rest:
        out["args"] = rest
    else:
        out.pop("args", None)
    return out


def scan(settings: dict) -> list[tuple[str, int, int, str]]:
    """Every wrapped entry, as (event, matcher_index, hook_index, wrapped_command).

    Read-only. The caller decides whether to act on it.
    """
    found: list[tuple[str, int, int, str]] = []
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return found
    for event, matchers in hooks.items():
        if not isinstance(matchers, list):
            continue
        for mi, matcher in enumerate(matchers):
            if not isinstance(matcher, dict):
                continue
            entries = matcher.get("hooks")
            if not isinstance(entries, list):
                continue
            for hi, entry in enumerate(entries):
                if isinstance(entry, dict) and _is_conhost_wrapper(entry):
                    found.append((event, mi, hi, str(entry["args"][1])))
    return found


def repair(settings: dict) -> int:
    """Unwrap in place. Returns the number of entries rewritten."""
    n = 0
    for event, mi, hi, _ in scan(settings):
        entries = settings["hooks"][event][mi]["hooks"]
        entries[hi] = _unwrap(entries[hi])
        n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--settings", default=str(DEFAULT_SETTINGS),
                    help=f"settings.json to inspect (default: {DEFAULT_SETTINGS})")
    ap.add_argument("--apply", action="store_true",
                    help="rewrite the file; without it this reports and changes nothing")
    args = ap.parse_args(argv)

    path = Path(args.settings)
    if not path.is_file():
        print(f"fix_conhost_hook_leak: no such file: {path}", file=sys.stderr)
        return 2

    # utf-8-sig: a BOM here is ordinary on Windows and plain utf-8 chokes on it.
    raw = path.read_text(encoding="utf-8-sig")
    try:
        settings = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"fix_conhost_hook_leak: {path} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    found = scan(settings)
    print(f"settings : {path}")
    print(f"wrapped  : {len(found)} hook entr{'y' if len(found) == 1 else 'ies'}")
    if not found:
        print("nothing to do -- no conhost --headless wrapper present")
        return 0

    by_event: dict[str, int] = {}
    for event, _, _, wrapped in found:
        by_event[event] = by_event.get(event, 0) + 1
    for event in sorted(by_event):
        print(f"  {event:<22s} {by_event[event]}")
    print(f"  wrapped command: {found[0][3]}")

    if not args.apply:
        print("\nreport only. re-run with --apply to rewrite (a backup is written first).")
        return 0

    before = copy.deepcopy(settings)
    n = repair(settings)
    broken = argv_violations(before, settings, {(e, m, h) for e, m, h, _ in found})
    if broken:
        # Incident 2026-09-16: an ad-hoc settings rewrite kept the script path and dropped
        # every argument after it (six --event= routing identities), and all Power Pack
        # hooks went dark for ~42 h. A settings writer must prove argv survives, or not write.
        print("\nREFUSED: the rewrite would change hook argv beyond the unwrap:", file=sys.stderr)
        for b in broken:
            print(f"  {b}", file=sys.stderr)
        return 3

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(path.name + f".bak-{stamp}")
    shutil.copy2(path, backup)

    # Compare-and-swap: Orca X's installer also rewrites this file at its own launch.
    # If the bytes moved since we read them, do not overwrite the other writer's work.
    tmp = path.with_name(path.name + f".tmp-conhost-{os.getpid()}")
    tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if path.read_text(encoding="utf-8-sig") != raw:
        tmp.unlink()
        print("fix_conhost_hook_leak: settings.json changed while repairing; not written", file=sys.stderr)
        return 4
    os.replace(tmp, path)

    print(f"\nbackup   : {backup}")
    print(f"rewrote  : {n} entr{'y' if n == 1 else 'ies'}")
    print("running sessions pick up hook changes live on current Claude Code (measured 2026-09-18).")
    return 0


def _argv(entry: dict) -> list:
    return [entry.get("command")] + list(entry.get("args") or [])


def argv_violations(before: dict, after: dict, targets: set) -> list[str]:
    """Every hook entry keeps its argv, except targets, whose argv must equal the wrapped tail."""
    out: list[str] = []
    for event, groups in (before.get("hooks") or {}).items():
        for mi, group in enumerate(groups or []):
            for hi, old in enumerate(group.get("hooks") or []):
                try:
                    new = after["hooks"][event][mi]["hooks"][hi]
                except (KeyError, IndexError, TypeError):
                    out.append(f"{event}[{mi}][{hi}]: entry disappeared")
                    continue
                want = list(old.get("args") or [])[1:] if (event, mi, hi) in targets else _argv(old)
                if _argv(new) != want:
                    out.append(f"{event}[{mi}][{hi}]: argv {_argv(old)} -> {_argv(new)}")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
