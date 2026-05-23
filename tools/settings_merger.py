#!/usr/bin/env python3
"""settings_merger.py - safe deep-merge into ~/.claude/settings.json.

Owner-authorized self-modification tool (operator answered Q2=(a) on
2026-05-15). Reads the live settings.json (utf-8-sig — strips any BOM
introduced by PowerShell tools), validates JSON, writes a timestamped
backup, appends a single hook block into hooks.<EVENT>[], then writes
atomically via os.replace().

Contract:
  - Round-trip preserves every existing field byte-equivalent (json.loads
    comparison, not raw bytes — comments aren't legal in JSON anyway).
  - Idempotent: if an entry with the same `command` already exists under
    hooks.<EVENT>[], the merge is a no-op and exits 0.
  - The diff is bounded: ONLY hooks.<EVENT>[] grows by exactly one
    element (append-only). Any other delta fails the post-write
    assertion (exit 5) and the timestamped backup is restored.

Usage:
  settings_merger.py register-stop --node-script <abs/path/to/hook.js>
                                   [--timeout 5]
  settings_merger.py register-userprompt --py-interp <abs/python.exe>
                                   --py-script <abs/loader.py> [--timeout 10]

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


def _block_exists(event_arr, needle: str) -> bool:
    target = _normalize_cmd(needle)
    for entry in event_arr:
        for hook in entry.get("hooks", []):
            if hook.get("type") == "command":
                if target in _normalize_cmd(hook.get("command", "")):
                    return True
    return False


def _register(settings_path: str, event: str, command_str: str,
              match_needle: str, timeout: int, match_key: str = "") -> int:
    """Append one {hooks:[{command}]} block to hooks.<event>[], bounded.

    match_needle: substring used for idempotency + the only allowed delta
    is hooks.<event> growing by exactly one append-only element.
    match_key: optional Claude Code tool matcher (e.g. "Bash"). When
    non-empty it is injected as the entry's "matcher" so the hook fires
    only for matching tools instead of behaving as a global dispatcher.
    """
    if not os.path.isfile(settings_path):
        print(f"settings_merger: settings.json not found at {settings_path}",
              file=sys.stderr)
        return 5

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
    arr = hooks.setdefault(event, [])
    if not isinstance(arr, list):
        print(f"settings_merger: hooks.{event} is not a list", file=sys.stderr)
        return 5

    if _block_exists(arr, match_needle):
        print(f"settings_merger: already registered ({match_needle})")
        return 0

    new_entry = {
        "hooks": [
            {"type": "command", "command": command_str, "timeout": int(timeout)}
        ]
    }
    if match_key:
        # Insertion order keeps "matcher" first to mirror existing entries.
        new_entry = {"matcher": match_key, **new_entry}
    before_snapshot = copy.deepcopy(data)
    arr.append(new_entry)

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
        shutil.copy2(backup_path, settings_path)
        raise

    with open(settings_path, "r", encoding="utf-8-sig") as fh:
        after = json.loads(fh.read())

    fail = []
    for k in set(before_snapshot.keys()) | set(after.keys()):
        if k == "hooks":
            continue
        if before_snapshot.get(k) != after.get(k):
            fail.append(k)
    if fail:
        print(f"settings_merger: unexpected diff outside hooks: {fail}",
              file=sys.stderr)
        shutil.copy2(backup_path, settings_path)
        return 5

    bh = before_snapshot.get("hooks", {})
    ah = after.get("hooks", {})
    for k in set(bh.keys()) | set(ah.keys()):
        if k == event:
            continue
        if bh.get(k) != ah.get(k):
            fail.append(f"hooks.{k}")
    if fail:
        print(f"settings_merger: unexpected diff inside hooks: {fail}",
              file=sys.stderr)
        shutil.copy2(backup_path, settings_path)
        return 5

    before_arr = bh.get(event, [])
    after_arr = ah.get(event, [])
    if len(after_arr) != len(before_arr) + 1:
        print(f"settings_merger: {event} length delta != +1 "
              f"({len(before_arr)} -> {len(after_arr)})", file=sys.stderr)
        shutil.copy2(backup_path, settings_path)
        return 5
    if after_arr[:-1] != before_arr:
        print(f"settings_merger: {event} prefix mutated (not append-only)",
              file=sys.stderr)
        shutil.copy2(backup_path, settings_path)
        return 5

    print(f"settings_merger: OK  event={event}  registered={match_needle}  "
          f"backup={os.path.basename(backup_path)}  "
          f"{event}_len={len(before_arr)}->{len(after_arr)}")
    return 0


def register_stop(settings_path: str, node_script: str, timeout: int) -> int:
    fwd = node_script.replace("\\", "/")
    return _register(settings_path, "Stop",
                      f'{NODE_CMD} "{fwd}"', fwd, timeout)


def register_sessionstart(settings_path: str, node_script: str,
                          timeout: int) -> int:
    # SessionStart carries no tool matcher (like Stop): the hook fires once
    # per session start. Refuse a dangling command pointing at a missing
    # script — it would error on every session start.
    if not os.path.isfile(node_script):
        print(f"settings_merger: hook script not found: {node_script}",
              file=sys.stderr)
        return 5
    fwd = node_script.replace("\\", "/")
    return _register(settings_path, "SessionStart",
                     f'{NODE_CMD} "{fwd}"', fwd, timeout)


def register_userprompt(settings_path: str, py_interp: str,
                        py_script: str, timeout: int) -> int:
    # G6 preflight: refuse to write a hook command pointing at a
    # non-existent interpreter (would silently degrade every prompt).
    if not os.path.isfile(py_interp):
        print(f"settings_merger: python interpreter not found: {py_interp}",
              file=sys.stderr)
        return 5
    if not os.path.isfile(py_script):
        print(f"settings_merger: hook script not found: {py_script}",
              file=sys.stderr)
        return 5
    interp_fwd = py_interp.replace("\\", "/")
    script_fwd = py_script.replace("\\", "/")
    cmd = f'"{interp_fwd}" "{script_fwd}"'
    return _register(settings_path, "UserPromptSubmit", cmd, script_fwd,
                     timeout)


def register_zero_command(settings_path: str, dry_run: bool) -> int:
    """Register the four Zero-Command Layer hooks in one call.

    Wires (in order, idempotent):
      SessionStart -> ~/.claude/hooks/zero-command-bootstrap.js   (Component A)
      SessionStart -> ~/.claude/hooks/first-time-project.js       (Component D)
      Stop         -> ~/.claude/hooks/background-verifier.js      (Component C)

    Component B.2 lives inside the existing UserPromptSubmit hook
    (jit_skill_loader.py) — no additional registration needed.
    Component B.3 daemon spawns from a separate Stop entry the
    Owner installs via the auto-compact-sendkeys pattern; not
    wired here to keep risk surface tight.

    Exit codes mirror _register: 0 = all 3 entries newly wired or
    already present (idempotent); non-zero = first failing call.
    """
    home = os.path.expanduser("~")
    deploys = [
        ("SessionStart", os.path.join(home, ".claude", "hooks", "zero-command-bootstrap.js"), 5),
        ("SessionStart", os.path.join(home, ".claude", "hooks", "first-time-project.js"), 5),
        ("Stop",         os.path.join(home, ".claude", "hooks", "background-verifier.js"), 5),
    ]
    if dry_run:
        print("settings_merger: register-zero-command --dry-run")
        for event, script, timeout in deploys:
            present = "yes" if os.path.isfile(script) else "no"
            print(f"  would register {event} -> {script}  (script-present={present})")
        return 0
    for event, script, timeout in deploys:
        if not os.path.isfile(script):
            print(f"settings_merger: deployed hook missing: {script}",
                  file=sys.stderr)
            print(f"  Hint: copy from claude-power-pack/hooks/<name> "
                  f"to ~/.claude/hooks/ first, then re-run.",
                  file=sys.stderr)
            return 5
        fn = register_stop if event == "Stop" else register_sessionstart
        rc = fn(settings_path, script, timeout)
        if rc != 0:
            return rc
    print("settings_merger: register-zero-command OK (3 hooks wired/idempotent)")
    return 0


def register_mark_live_session(settings_path: str, dry_run: bool) -> int:
    """Register the mark-live-session hook (SessionStart + Stop) in one call.

    Replaces the legacy ~/.claude/hooks/resume-hide-live.js cloaking
    pattern (which renamed `<uuid>.jsonl` -> `<uuid>.jsonl.live` to hide
    live sessions). The marker hook leaves the .jsonl visible and tags
    the latest ai-title with a leading "[live]" glyph so the native
    /resume picker shows every session and the user can tell at a glance
    which ones are currently open in another pane.

    Source-of-truth path (registered directly into settings.json — no
    copy to ~/.claude/hooks/, matching the RTK pattern):
      ~/.claude/skills/claude-power-pack/hooks/mark-live-session.js

    Idempotent: if either event already references the script, that
    event registration is a no-op (handled by _register's _block_exists
    check).

    Exit codes mirror _register: 0 = both entries newly wired or
    already present; non-zero = first failing call.
    """
    home = os.path.expanduser("~")
    hook = os.path.join(home, ".claude", "skills",
                        "claude-power-pack", "hooks", "mark-live-session.js")
    deploys = [
        ("SessionStart", hook, 5),
        ("Stop",         hook, 5),
    ]
    if dry_run:
        print("settings_merger: register-mark-live-session --dry-run")
        for event, script, timeout in deploys:
            present = "yes" if os.path.isfile(script) else "no"
            print(f"  would register {event} -> {script}  "
                  f"(script-present={present})")
        return 0
    if not os.path.isfile(hook):
        print(f"settings_merger: hook script not found: {hook}",
              file=sys.stderr)
        print("  Hint: pull the latest claude-power-pack first.",
              file=sys.stderr)
        return 5
    for event, script, timeout in deploys:
        fn = register_stop if event == "Stop" else register_sessionstart
        rc = fn(settings_path, script, timeout)
        if rc != 0:
            return rc
    print("settings_merger: register-mark-live-session OK "
          "(2 hooks wired/idempotent)")
    return 0


def register_session_safety(settings_path: str, dry_run: bool) -> int:
    """Register the session-safety stack in one idempotent call.

    Wires (in order, idempotent):
      PreToolUse(matcher=Bash|PowerShell) -> ~/.claude/hooks/session-file-guard.js
      SessionStart                          -> ~/.claude/hooks/lazarus-stub-recover.js

    The _oneshot_solitary_empty_shell_cleanup.js hook is intentionally
    NOT auto-registered — per the contract it's Owner-on-demand only
    (the 4a600525 incident showed why automatic cleanup of "empty
    shells" is dangerous). The Owner runs it explicitly when they want
    archival, not on every SessionStart.

    Exit codes mirror _register: 0 = both newly wired or already
    present (idempotent); non-zero = first failing call.

    Contract: SESSION_SAFETY_CONTRACT.md (BL-SESSION-SAFETY-001).
    """
    home = os.path.expanduser("~")
    guard = os.path.join(home, ".claude", "hooks", "session-file-guard.js")
    stub_recover = os.path.join(home, ".claude", "hooks",
                                "lazarus-stub-recover.js")
    deploys = [
        # (event, script, matcher_or_None, timeout)
        ("PreToolUse",   guard,        "Bash|PowerShell", 5),
        ("SessionStart", stub_recover, None,              5),
    ]
    if dry_run:
        print("settings_merger: register-session-safety --dry-run")
        for event, script, matcher, _t in deploys:
            present = "yes" if os.path.isfile(script) else "no"
            mp = f" (matcher={matcher})" if matcher else ""
            print(f"  would register {event}{mp} -> {script}  "
                  f"(script-present={present})")
        return 0
    for _event, script, _m, _t in deploys:
        if not os.path.isfile(script):
            print(f"settings_merger: hook script not found: {script}",
                  file=sys.stderr)
            print("  Hint: copy from claude-power-pack/hooks/<name> to "
                  "~/.claude/hooks/ first (see install-global.ps1 "
                  "checklist).", file=sys.stderr)
            return 5
    for event, script, matcher, timeout in deploys:
        if event == "PreToolUse":
            rc = register_pretool(settings_path, script, matcher, timeout)
        else:
            rc = register_sessionstart(settings_path, script, timeout)
        if rc != 0:
            return rc
    print("settings_merger: register-session-safety OK "
          "(2 hooks wired/idempotent)")
    return 0


def register_deep_research(settings_path: str, dry_run: bool) -> int:
    """Register the deep-research sleepy-spawn Stop hook in one call.

    Wires:
      Stop  ->  ~/.claude/hooks/research-intent-detector.js  (timeout 5 s)

    The hook is fail-OPEN — if it crashes or the spawn target script
    is missing, the Stop chain continues unimpeded. Single hook keeps
    the registration symmetrical with register-session-safety + the
    register-mark-live-session pattern.

    Spec: claude-power-pack/vault/specs/deep-research-agent.md §7.2
    Plan: claude-power-pack/vault/plans/deep-research-agent-2026-05-23.md

    Idempotent: re-running on a host where the hook is already wired
    is a no-op (handled by _register's _block_exists check).
    """
    home = os.path.expanduser("~")
    hook = os.path.join(home, ".claude", "hooks",
                         "research-intent-detector.js")
    if dry_run:
        present = "yes" if os.path.isfile(hook) else "no"
        print("settings_merger: register-deep-research --dry-run")
        print(f"  would register Stop -> {hook}  "
              f"(script-present={present})")
        return 0
    if not os.path.isfile(hook):
        print(f"settings_merger: hook script not found: {hook}",
              file=sys.stderr)
        print("  Hint: copy from "
              "claude-power-pack/hooks/research-intent-detector.js to "
              "~/.claude/hooks/ first (Mirror-Sync-Direction doctrine: "
              "the installer prints, the Owner pastes).", file=sys.stderr)
        return 5
    rc = register_stop(settings_path, hook, 5)
    if rc != 0:
        return rc
    print("settings_merger: register-deep-research OK "
          "(1 hook wired/idempotent)")
    return 0


def register_auto_test_gate(settings_path: str, dry_run: bool) -> int:
    """Register the Auto-Testing Quality Gate PreToolUse hook.

    Wires:
      PreToolUse(matcher=Bash|PowerShell) ->
        ~/.claude/skills/claude-power-pack/hooks/auto-test-gate.js
      (timeout: 30 s — matches the hook's 28 s budget guard with 2 s
      margin for spawn + parse)

    The hook is fail-OPEN: any internal error, missing python, missing
    module, etc. results in exit 0 (commit proceeds). A broken gate
    must never block real commits. The hook intercepts only
    `git commit` invocations (excluding -h / --help variants).

    Spec: claude-power-pack/vault/specs/auto-testing-gate.md
    Plan: claude-power-pack/vault/plans/auto-testing-skill-2026-05-23.md

    Idempotent: re-running on a host where the hook is already wired
    is a no-op (handled by _register's _block_exists check).

    Mirror-Sync-Direction: the registered path points at the PP repo
    directly (no copy to ~/.claude/hooks/ required), same pattern as
    register-mark-live-session.
    """
    home = os.path.expanduser("~")
    hook = os.path.join(home, ".claude", "skills",
                        "claude-power-pack", "hooks", "auto-test-gate.js")
    if dry_run:
        present = "yes" if os.path.isfile(hook) else "no"
        print("settings_merger: register-auto-test-gate --dry-run")
        print(f"  would register PreToolUse(matcher=Bash|PowerShell) -> {hook}  "
              f"(script-present={present})")
        return 0
    if not os.path.isfile(hook):
        print(f"settings_merger: hook script not found: {hook}",
              file=sys.stderr)
        print("  Hint: pull the latest claude-power-pack first; "
              "the hook lives at hooks/auto-test-gate.js in this repo.",
              file=sys.stderr)
        return 5
    rc = register_pretool(settings_path, hook, "Bash|PowerShell", 30)
    if rc != 0:
        return rc
    print("settings_merger: register-auto-test-gate OK "
          "(PreToolUse Bash|PowerShell wired/idempotent)")
    return 0


def register_pretool(settings_path: str, node_script: str,
                      matcher: str, timeout: int) -> int:
    # Refuse to register a hook command pointing at a missing script —
    # a dangling PreToolUse entry would fire (and fail) on every match.
    if not os.path.isfile(node_script):
        print(f"settings_merger: hook script not found: {node_script}",
              file=sys.stderr)
        return 5
    fwd = node_script.replace("\\", "/")
    return _register(settings_path, "PreToolUse",
                      f'{NODE_CMD} "{fwd}"', fwd, timeout,
                      match_key=matcher)


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

    ru = sub.add_parser("register-userprompt",
                        help="Register a UserPromptSubmit Python hook")
    ru.add_argument("--py-interp", required=True,
                    help="absolute path to python.exe (must exist)")
    ru.add_argument("--py-script", required=True,
                    help="absolute path to the Python hook script")
    ru.add_argument("--timeout", type=int, default=10,
                    help="hook timeout in seconds (default 10)")
    ru.add_argument("--settings", default=DEFAULT_SETTINGS,
                    help="path to settings.json (default ~/.claude/...)")

    rss = sub.add_parser("register-sessionstart",
                         help="Register a SessionStart Node hook")
    rss.add_argument("--node-script", required=True,
                     help="absolute path to the Node hook script (must exist)")
    rss.add_argument("--timeout", type=int, default=5,
                     help="hook timeout in seconds (default 5)")
    rss.add_argument("--settings", default=DEFAULT_SETTINGS,
                     help="path to settings.json (default ~/.claude/...)")

    rzc = sub.add_parser("register-zero-command",
                         help="Register the Zero-Command Layer hooks "
                              "(Components A + C + D) in one idempotent call")
    rzc.add_argument("--dry-run", action="store_true",
                     help="print what would be wired without modifying settings.json")
    rzc.add_argument("--settings", default=DEFAULT_SETTINGS,
                     help="path to settings.json (default ~/.claude/...)")

    rdr = sub.add_parser("register-deep-research",
                          help="Register the deep-research sleepy-spawn "
                               "Stop hook (research-intent-detector.js). "
                               "Spec: vault/specs/deep-research-agent.md.")
    rdr.add_argument("--dry-run", action="store_true",
                     help="print what would be wired without modifying settings.json")
    rdr.add_argument("--settings", default=DEFAULT_SETTINGS,
                     help="path to settings.json (default ~/.claude/...)")

    rss2 = sub.add_parser("register-session-safety",
                          help="Register the session-safety stack: "
                               "PreToolUse(Bash|PowerShell)->session-file-guard "
                               "+ SessionStart->lazarus-stub-recover. "
                               "BL-SESSION-SAFETY-001.")
    rss2.add_argument("--dry-run", action="store_true",
                      help="print what would be wired without modifying settings.json")
    rss2.add_argument("--settings", default=DEFAULT_SETTINGS,
                      help="path to settings.json (default ~/.claude/...)")

    rmls = sub.add_parser("register-mark-live-session",
                          help="Register the mark-live-session hook "
                               "(SessionStart + Stop) — visible /resume "
                               "marker, replaces resume-hide-live.js")
    rmls.add_argument("--dry-run", action="store_true",
                      help="print what would be wired without modifying settings.json")
    rmls.add_argument("--settings", default=DEFAULT_SETTINGS,
                      help="path to settings.json (default ~/.claude/...)")

    ratg = sub.add_parser("register-auto-test-gate",
                          help="Register the Auto-Testing Quality Gate "
                               "PreToolUse hook (Bash|PowerShell git commit). "
                               "Spec: vault/specs/auto-testing-gate.md.")
    ratg.add_argument("--dry-run", action="store_true",
                      help="print what would be wired without modifying settings.json")
    ratg.add_argument("--settings", default=DEFAULT_SETTINGS,
                      help="path to settings.json (default ~/.claude/...)")

    rp = sub.add_parser("register-pretool",
                        help="Register a PreToolUse Node hook with a matcher")
    rp.add_argument("--node-script", required=True,
                    help="absolute path to the Node hook script (must exist)")
    rp.add_argument("--matcher", default="Bash",
                    help="Claude Code tool matcher (default Bash)")
    rp.add_argument("--timeout", type=int, default=10,
                    help="hook timeout in seconds (default 10)")
    rp.add_argument("--settings", default=DEFAULT_SETTINGS,
                    help="path to settings.json (default ~/.claude/...)")

    a = ap.parse_args()
    if a.cmd == "register-stop":
        return register_stop(a.settings, a.node_script, a.timeout)
    if a.cmd == "register-userprompt":
        return register_userprompt(a.settings, a.py_interp, a.py_script,
                                   a.timeout)
    if a.cmd == "register-sessionstart":
        return register_sessionstart(a.settings, a.node_script, a.timeout)
    if a.cmd == "register-pretool":
        return register_pretool(a.settings, a.node_script, a.matcher,
                                a.timeout)
    if a.cmd == "register-zero-command":
        return register_zero_command(a.settings, a.dry_run)
    if a.cmd == "register-mark-live-session":
        return register_mark_live_session(a.settings, a.dry_run)
    if a.cmd == "register-session-safety":
        return register_session_safety(a.settings, a.dry_run)
    if a.cmd == "register-deep-research":
        return register_deep_research(a.settings, a.dry_run)
    if a.cmd == "register-auto-test-gate":
        return register_auto_test_gate(a.settings, a.dry_run)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
