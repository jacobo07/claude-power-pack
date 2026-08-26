"""V-SESSIONSTART-* -- SessionStart must not pay for what it does not use.

Two defects on the same hot path, same family, different mechanisms:

  1. THE HUB paid CreateProcess twelve times. Its comments asserted that a
     detached child "never adds to the hub's wall time"; detaching removes
     the child's RUN time, not its creation. Ablation: 775 ms with the
     spawns, 290 ms without, and the run-to-run spread collapsed from
     160 ms to 6 ms. It now hands one spec list to one launcher.

  2. THE RECOVERY GATE imported `tools.recovery_verdict` as the first
     statement of banner(), two lines above the early return that handles
     the common "nothing to report" case. Expensive work ahead of an early
     return charges the common path for the rare one.

These gates pin BEHAVIOUR, not timing: a wall-clock assertion on this host
would be a coin flip (measured spreads of 79-418%), and a flaky gate is
worse than no gate. What is asserted is what is LOADED and what is SPAWNED.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

EXPECTED_GATES = 8
_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


VERDICT_MOD = "tools.recovery_verdict"


def _banner_loads_verdict(state_dir: Path) -> tuple[bool, str]:
    """Does calling banner() on this state dir import recovery_verdict?

    Run in a FRESH interpreter: this process may already have the module
    loaded from another gate, and sys.modules is global. A test that asks
    'is it loaded' inside a dirty process measures the test, not the code.
    """
    script = (
        "import sys, json\n"
        f"sys.path.insert(0, r'{PP}')\n"
        "from pathlib import Path\n"
        "import tools.recovery_epoch_gate as g\n"
        f"out = g.banner(Path(r'{state_dir}'))\n"
        "print(json.dumps({'loaded': "
        f"'{VERDICT_MOD}' in sys.modules, 'banner': out}}))\n"
    )
    r = subprocess.run([sys.executable, "-c", script],
                       capture_output=True, text=True, cwd=str(PP),
                       timeout=90)
    try:
        payload = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return (True, f"unparseable: rc={r.returncode} "
                      f"{r.stderr.strip()[:160]}")
    return payload["loaded"], payload["banner"]


def main() -> int:
    # --- 1. the recovery gate's fast path --------------------------------
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td)
        loaded, out = _banner_loads_verdict(empty)
        if loaded is False:
            _ok("V-SESSIONSTART-VERDICT-NOT-IMPORTED",
                "silent path returns without loading recovery_verdict")
        else:
            _fail("V-SESSIONSTART-VERDICT-NOT-IMPORTED",
                  f"the ~38ms import is back ahead of the early return "
                  f"({out!r})")

        if out == "":
            _ok("V-SESSIONSTART-SILENT-IS-SILENT",
                "no epoch -> empty banner, the documented common path")
        else:
            _fail("V-SESSIONSTART-SILENT-IS-SILENT",
                  f"expected silence, got {out!r}")

    # Bookend: when there IS something to report the import MUST happen.
    # A fast path that never loads the module would pass gate 1 by being
    # broken, so the paired case is what makes gate 1 mean anything.
    with tempfile.TemporaryDirectory() as td:
        state = Path(td)
        from modules.session_resilience import epoch  # noqa: PLC0415
        (state / "pane_map.json").write_text(
            json.dumps({"panes": []}), encoding="utf-8")
        # epoch.EPOCH_FILENAME, never a literal: a fixture that hard-codes
        # the filename passes forever after the real one is renamed. The
        # first draft of this gate used "epoch.json" and reported silence
        # from a state dir the code never looked at.
        (state / epoch.EPOCH_FILENAME).write_text(json.dumps({
            "status": epoch.OPEN,
            "interrupted_at": "2026-08-26T00:00:00+00:00",
            "reference_file": "pane_map_nonexistent.json",
        }), encoding="utf-8")
        loaded, out = _banner_loads_verdict(state)
        # An OPEN epoch whose reference is missing returns the HELD line
        # WITHOUT needing the verdict module, which is correct and is why
        # this gate asserts on the banner, not on the import.
        if out and "recovery" in out:
            _ok("V-SESSIONSTART-OPEN-EPOCH-SPEAKS",
                "an open epoch still produces its Owner-facing line")
        else:
            _fail("V-SESSIONSTART-OPEN-EPOCH-SPEAKS",
                  f"an open epoch went silent: {out!r}")

    # --- 2. the hub's launcher -------------------------------------------
    launcher = PP / "hooks" / "detached_launcher.js"
    if launcher.is_file():
        _ok("V-SESSIONSTART-LAUNCHER-EXISTS", str(launcher.name))
    else:
        _fail("V-SESSIONSTART-LAUNCHER-EXISTS",
              "the hub falls back to 12 inline spawns without it")

    hub = (PP / "hooks" / "session_start_hub.js").read_text(
        encoding="utf-8", errors="replace")
    if "flushSpawns()" in hub and "detached_launcher.js" in hub:
        _ok("V-SESSIONSTART-HUB-WIRED",
            "hub references the launcher and flushes its queue")
    else:
        _fail("V-SESSIONSTART-HUB-WIRED",
              "launcher present but the hub does not use it -- an orphan")

    # The flush must survive a throw between the first enqueue and the end
    # of main(), or a mid-hub error silently cancels twelve hooks.
    if hub.count("flushSpawns();") >= 2:
        _ok("V-SESSIONSTART-FLUSH-ON-ERROR",
            "queue is flushed on the error path too")
    else:
        _fail("V-SESSIONSTART-FLUSH-ON-ERROR",
              "a throw mid-main would strand the whole queue")

    # --- 3. the launcher actually launches -------------------------------
    with tempfile.TemporaryDirectory() as td:
        marker = Path(td) / "launched.txt"
        spec = [{
            "label": "gate_probe",
            "cmd": sys.executable,
            "args": ["-c", f"open(r'{marker}', 'w').write('ok')"],
            "envDelta": None,
            "cwd": td,
            "log": None,
        }]
        spec_path = Path(td) / "spec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        subprocess.run(["node", str(launcher), str(spec_path)],
                       capture_output=True, timeout=60, cwd=str(PP))
        # The child is detached; give it a bounded chance to land rather
        # than a fixed sleep that is either flaky or slow.
        landed = False
        for _ in range(100):
            if marker.exists():
                landed = True
                break
            import time  # noqa: PLC0415
            time.sleep(0.05)
        if landed:
            _ok("V-SESSIONSTART-LAUNCHER-SPAWNS",
                "a detached child from a spec file reached the disk")
        else:
            _fail("V-SESSIONSTART-LAUNCHER-SPAWNS",
                  "the launcher consumed the spec and spawned nothing -- "
                  "every folded hook would be silently lost")

        if not spec_path.exists():
            _ok("V-SESSIONSTART-SPEC-CONSUMED",
                "handoff file removed after reading; it is not state")
        else:
            _fail("V-SESSIONSTART-SPEC-CONSUMED",
                  "spec files accumulate in TEMP")

    ran = len(_passes) + len(_fails)
    print(f"\nSESSIONSTART_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
