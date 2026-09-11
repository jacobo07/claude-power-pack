"""V-CONHOST-* -- drills for the conhost --headless hook-wrapper repair.

The subjects are SYNTHETIC. A drill pinned to the Owner's real settings.json has
an interest in that file staying broken: fix it and the drill asserts about a
condition that no longer exists. A synthetic fixture represents the CLASS, so it
keeps working on the day the last real wrapper is gone.

Both directions are driven. Half of these cases must NOT fire -- a detector
exercised only where it should trip would pass with every clause deleted.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.fix_conhost_hook_leak import (  # noqa: E402
    _is_conhost_wrapper, _unwrap, main, repair, scan,
)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK  ] {gate:<34s} {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate:<34s} {diagnostic}")


def _wrapped(cmd: str = "node", *rest: str) -> dict:
    return {
        "type": "command",
        "command": "C:\\WINDOWS\\System32\\conhost.exe",
        "args": ["--headless", cmd, *rest],
        "timeout": 5,
    }


def _settings(*events: tuple[str, dict]) -> dict:
    hooks: dict = {}
    for event, entry in events:
        hooks.setdefault(event, []).append({"matcher": "*", "hooks": [entry]})
    return {"hooks": hooks, "model": "opus"}


def test_detects_the_wrapper() -> None:
    if _is_conhost_wrapper(_wrapped()):
        _ok("V-CONHOST-DETECT", "conhost.exe + --headless recognised")
    else:
        _fail("V-CONHOST-DETECT", "the exact production shape was not matched")


def test_negative_controls() -> None:
    """The half that matters. Each of these MUST NOT match."""
    cases = {
        "plain node hook": {"type": "command", "command": "node", "args": ["x.js"]},
        "conhost, no --headless": {
            "type": "command",
            "command": "C:\\WINDOWS\\System32\\conhost.exe",
            "args": ["cmd.exe", "/c", "x"],
        },
        "--headless on another exe": {
            "type": "command",
            "command": "chrome.exe",
            "args": ["--headless", "about:blank"],
        },
        "no args at all": {"type": "command", "command": "conhost.exe"},
        "args too short": {
            "type": "command",
            "command": "conhost.exe",
            "args": ["--headless"],
        },
    }
    bad = [name for name, entry in cases.items() if _is_conhost_wrapper(entry)]
    if bad:
        _fail("V-CONHOST-NEGATIVE", f"false positives: {bad}")
    else:
        _ok("V-CONHOST-NEGATIVE", f"{len(cases)} non-wrapper shapes all passed through")


def test_unwrap_preserves_everything_else() -> None:
    out = _unwrap(_wrapped("cmd.exe", "/d", "/c", "hook.cmd"))
    ok = (
        out["command"] == "cmd.exe"
        and out["args"] == ["/d", "/c", "hook.cmd"]
        and out["timeout"] == 5
        and out["type"] == "command"
    )
    if ok:
        _ok("V-CONHOST-UNWRAP", "argv promoted; type/timeout survived")
    else:
        _fail("V-CONHOST-UNWRAP", f"unexpected entry: {out}")


def test_unwrap_drops_empty_args() -> None:
    out = _unwrap(_wrapped("hook.exe"))
    if out["command"] == "hook.exe" and "args" not in out:
        _ok("V-CONHOST-UNWRAP-BARE", "no residual empty args list")
    else:
        _fail("V-CONHOST-UNWRAP-BARE", f"unexpected entry: {out}")


def test_scan_finds_every_event() -> None:
    s = _settings(
        ("PreToolUse", _wrapped("cmd.exe", "/c", "a")),
        ("Stop", _wrapped("cmd.exe", "/c", "b")),
        ("PostToolUse", {"type": "command", "command": "node", "args": ["clean.js"]}),
    )
    found = scan(s)
    events = sorted(e for e, _, _, _ in found)
    if events == ["PreToolUse", "Stop"]:
        _ok("V-CONHOST-SCAN", "2 wrapped found, the clean entry untouched")
    else:
        _fail("V-CONHOST-SCAN", f"expected PreToolUse+Stop, got {events}")


def test_repair_is_idempotent() -> None:
    s = _settings(("PreToolUse", _wrapped("cmd.exe", "/d", "/c", "h.cmd")))
    first = repair(s)
    second = repair(s)
    entry = s["hooks"]["PreToolUse"][0]["hooks"][0]
    if first == 1 and second == 0 and entry["command"] == "cmd.exe":
        _ok("V-CONHOST-IDEMPOTENT", "1 then 0; second run is a no-op")
    else:
        _fail("V-CONHOST-IDEMPOTENT", f"first={first} second={second} entry={entry}")


def test_clean_file_is_left_alone() -> None:
    """The negative control at file level: refusing everything must not score."""
    s = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "node"}]}]}}
    before = json.dumps(s, sort_keys=True)
    n = repair(s)
    if n == 0 and json.dumps(s, sort_keys=True) == before:
        _ok("V-CONHOST-CLEAN-NOOP", "clean settings byte-identical after repair()")
    else:
        _fail("V-CONHOST-CLEAN-NOOP", f"repaired {n} on a clean file")


def test_end_to_end_writes_backup_and_valid_json() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "settings.json"
        s = _settings(("PreToolUse", _wrapped("cmd.exe", "/d", "/c", "h.cmd")))
        p.write_text(json.dumps(s, indent=2), encoding="utf-8")

        rc_report = main(["--settings", str(p)])
        untouched = json.loads(p.read_text(encoding="utf-8"))
        if rc_report != 0 or scan(untouched) == []:
            _fail("V-CONHOST-DRYRUN", "report-only run modified the file")
            return
        _ok("V-CONHOST-DRYRUN", "report-only left the wrapper in place")

        rc = main(["--settings", str(p), "--apply"])
        after = json.loads(p.read_text(encoding="utf-8"))
        backups = list(Path(td).glob("settings.json.bak-*"))
        entry = after["hooks"]["PreToolUse"][0]["hooks"][0]
        if (rc == 0 and len(backups) == 1 and scan(after) == []
                and entry["command"] == "cmd.exe" and after["model"] == "opus"):
            _ok("V-CONHOST-E2E", f"rewritten, 1 backup, unrelated keys intact")
        else:
            _fail("V-CONHOST-E2E",
                  f"rc={rc} backups={len(backups)} left={scan(after)} entry={entry}")


def main_gate() -> int:
    print("=" * 68)
    print("test_conhost_hook_leak -- V-CONHOST-* (synthetic subjects)")
    print("=" * 68)
    for fn in (
        test_detects_the_wrapper,
        test_negative_controls,
        test_unwrap_preserves_everything_else,
        test_unwrap_drops_empty_args,
        test_scan_finds_every_event,
        test_repair_is_idempotent,
        test_clean_file_is_left_alone,
        test_end_to_end_writes_backup_and_valid_json,
    ):
        fn()
    total = _passes + _fails
    print("=" * 68)
    print(f"CONHOST_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main_gate())
