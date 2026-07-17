#!/usr/bin/env python3
"""test_wave_stagger.py -- V-gates for the folderOpen wave stagger.

Origin (T-FOLDEROPEN-STAMPEDE-001): every restored pane is a task with
``runOn: folderOpen``, and Cursor fires ALL of a repo's folderOpen tasks at
once. The 30-pane claude-power-pack window therefore spawned 30 concurrent
`claude --resume` handshakes. dependsOrder:sequence cannot fix it -- a Claude
session never exits, so the chain would deadlock on task 1 forever. The delay
lives inside each task's command instead.

Hermetic: every write goes to a tmp dir; nothing touches a real .vscode/.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.cpc_os.vscode_autorun import (  # noqa: E402
    WAVE_INTERVAL_S_DEFAULT,
    WAVE_SIZE_DEFAULT,
    build_cpc_tasks,
    wave_delay_s,
    write_autorun_for_cwd,
)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _panes(n: int, cwd: str = "C:/repo") -> list[dict]:
    return [
        {
            "cwd": cwd,
            "session_id": f"{i:08x}-aaaa-bbbb-cccc-dddddddddddd",
            "resume": f"claude --resume {i:08x}-aaaa-bbbb-cccc-dddddddddddd",
            "topic": f"pane {i}",
            "repo": "repo",
        }
        for i in range(n)
    ]


def _delay_of(task: dict) -> int:
    """Recover the delay a task encodes. Wave 0 tasks carry no wrapper at all."""
    if task["type"] == "shell":
        return 0
    body = task["args"][1]                       # ["/c", "timeout /t N ..."]
    return int(body.split("timeout /t ", 1)[1].split(" ", 1)[0])


# ---------------------------------------------------------------- V-gates


def v_revival_order() -> None:
    """The delay ladder is monotonic and steps exactly once per wave."""
    tasks = build_cpc_tasks(_panes(12), wave_size=5, wave_interval_s=8)
    got = [_delay_of(t) for t in tasks]
    want = [0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 16, 16]
    if got == want:
        _ok("V-REVIVAL-ORDER", f"12 panes, waves of 5 -> delays {got}")
    else:
        _fail("V-REVIVAL-ORDER", f"expected {want}, got {got}")


def v_revival_throttle() -> None:
    """No wave ever exceeds wave_size panes -- that IS the concurrency cap.
    Checked against the real 30-pane claude-power-pack shape."""
    tasks = build_cpc_tasks(_panes(30), wave_size=5, wave_interval_s=8)
    buckets: dict[int, int] = {}
    for t in tasks:
        d = _delay_of(t)
        buckets[d] = buckets.get(d, 0) + 1
    worst = max(buckets.values())
    if worst <= 5 and len(buckets) == 6:
        _ok("V-REVIVAL-THROTTLE",
            f"30 panes -> {len(buckets)} waves, max {worst} concurrent (cap 5)")
    else:
        _fail("V-REVIVAL-THROTTLE",
              f"buckets={buckets} -> max {worst} concurrent (cap 5)")


def v_revival_failopen() -> None:
    """The chain is `&` (unconditional), never `&&`. If timeout ever fails,
    kclaude must STILL launch: the stagger degrades to 'no delay', never to
    'the pane never came back'."""
    tasks = build_cpc_tasks(_panes(8), wave_size=5, wave_interval_s=8)
    delayed = [t for t in tasks if t["type"] == "process"]
    if not delayed:
        _fail("V-REVIVAL-FAILOPEN", "no delayed task produced; nothing to check")
        return
    body = delayed[0]["args"][1]
    if "&&" in body:
        _fail("V-REVIVAL-FAILOPEN", f"conditional chain would strand the pane: {body!r}")
    elif "&" in body and "kclaude.cmd" in body:
        _ok("V-REVIVAL-FAILOPEN", "unconditional `&`: timeout failure still launches kclaude")
    else:
        _fail("V-REVIVAL-FAILOPEN", f"no launch chain found in {body!r}")


def v_revival_wave0_unchanged() -> None:
    """Wave 0 keeps the EXACT pre-stagger task shape (type shell, command =
    bin/kclaude.cmd, args = --resume <sid>). Zero regression for the common case
    of a repo with <= wave_size panes."""
    tasks = build_cpc_tasks(_panes(3), wave_size=5, wave_interval_s=8)
    bad = [t for t in tasks
           if t["type"] != "shell" or not str(t["command"]).endswith("kclaude.cmd")]
    if not bad and all(t["args"][0] == "--resume" for t in tasks):
        _ok("V-REVIVAL-WAVE0", "3 panes -> 3 undelayed shell/kclaude tasks (shape unchanged)")
    else:
        _fail("V-REVIVAL-WAVE0", f"wave-0 shape drifted: {bad or tasks}")


def v_revival_disable() -> None:
    """wave_size=0 (or interval 0) disables the stagger entirely -- the escape
    hatch. Every task returns to the immediate shape."""
    a = build_cpc_tasks(_panes(12), wave_size=0, wave_interval_s=8)
    b = build_cpc_tasks(_panes(12), wave_size=5, wave_interval_s=0)
    if all(_delay_of(t) == 0 for t in a + b):
        _ok("V-REVIVAL-DISABLE", "wave_size=0 and interval=0 both -> zero delays")
    else:
        _fail("V-REVIVAL-DISABLE",
              f"stagger not disabled: {[_delay_of(t) for t in a + b]}")


def v_revival_dryrun() -> None:
    """--dry-run computes the full doc but writes NOTHING to disk."""
    with tempfile.TemporaryDirectory() as td:
        vdir = Path(td) / ".vscode"
        res = write_autorun_for_cwd("C:/repo", _panes(12), vscode_dir=vdir,
                                    dry_run=True)
        wrote = (vdir / "tasks.json").exists()
        if not wrote and res["action"] == "dry-run" and res["n_tasks"] == 12:
            _ok("V-REVIVAL-DRYRUN", "12 tasks planned, tasks.json absent on disk")
        else:
            _fail("V-REVIVAL-DRYRUN",
                  f"wrote={wrote} action={res['action']} n={res['n_tasks']}")


def v_revival_persisted() -> None:
    """A real write round-trips: the on-disk JSON carries the delay ladder."""
    with tempfile.TemporaryDirectory() as td:
        vdir = Path(td) / ".vscode"
        write_autorun_for_cwd("C:/repo", _panes(7), vscode_dir=vdir,
                              wave_size=5, wave_interval_s=8)
        doc = json.loads((vdir / "tasks.json").read_text(encoding="utf-8"))
        delays = [_delay_of(t) for t in doc["tasks"]]
        if delays == [0, 0, 0, 0, 0, 8, 8]:
            _ok("V-REVIVAL-PERSISTED", f"tasks.json round-trips delays {delays}")
        else:
            _fail("V-REVIVAL-PERSISTED", f"on-disk delays {delays}")


def v_revival_defaults() -> None:
    """The shipped defaults are the ones the doctrine names (waves of 5 / 8s)."""
    if (WAVE_SIZE_DEFAULT, WAVE_INTERVAL_S_DEFAULT) == (5, 8) \
            and wave_delay_s(7, 5, 8) == 8 and wave_delay_s(0, 5, 8) == 0:
        _ok("V-REVIVAL-DEFAULTS", "defaults = waves of 5 every 8s")
    else:
        _fail("V-REVIVAL-DEFAULTS",
              f"defaults drifted: size={WAVE_SIZE_DEFAULT} int={WAVE_INTERVAL_S_DEFAULT}")


def main() -> int:
    print("test_wave_stagger -- folderOpen wave stagger V-gates")
    for fn in (v_revival_order, v_revival_throttle, v_revival_failopen,
               v_revival_wave0_unchanged, v_revival_disable, v_revival_dryrun,
               v_revival_persisted, v_revival_defaults):
        fn()
    total = _passes + _fails
    print(f"\nWAVE_STAGGER_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
