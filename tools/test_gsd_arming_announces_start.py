#!/usr/bin/env python3
"""ARMING IS NOT STARTING -- the arm step must say so, at the moment it arms.

WHY THIS TEST EXISTS. /cpp-gsd-long has three steps: retune the context fire-points,
record the autorun marker, and START the run. The first two make a run SURVIVE a
compaction; neither launches anything. On 2026-09-19 a session did steps 1 and 2,
reported "ARMED", and hand-drove the work instead -- and that was not a novel slip.

Measured the same day over `~/.claude/state/gsd-autorun-ledger.jsonl` and the live
marker set: **4 of 9 markers had been armed with no evidence a run ever began**, three
of them belonging to different sessions. The mechanism of the failure is structural,
not careless:

  * `gsd_long_run.py status` reports an armed-and-idle run exactly the way it reports
    a healthy one, so the obvious "is it working?" instrument cannot tell them apart;
  * every ledger event that WOULD distinguish them -- `crossing`, `resume_requested`,
    `resume_confirmed` -- fires only at the FIRST compaction, which can be hours away.
    Until then the two states are indistinguishable by construction.

The command doc did carry the instruction, in prose, in a different section from the
runnable block. Three sessions proved prose does not travel to the moment you type the
command. A print at the arming instant does, which is what this test pins.

WHAT IS PINNED. On a successful `--write`, stdout must (a) keep the marker path as its
FIRST line, because that is the machine-readable result callers parse, and (b) carry an
unmissable instruction naming THE ACTUAL resume command the marker recorded -- not a
generic "remember to start it", which would be useless when the command is
`/gsd-autonomous --from 13` and the reader types the bare form.

NOTHING REAL IS ARMED. The mission check, the GSD preflight and the ledger write are
stubbed, and the marker is written into a throwaway temp directory that this test owns
and deletes. It never touches `~/.claude/state/`.

Run: python tools/test_gsd_arming_announces_start.py
Exit 0 all gates hold; 1 a gate failed.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import contextlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gsd_autorun_marker as marker  # noqa: E402

_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"FAIL {gate}: {diagnostic}")


class _Verdict:
    """Stands in for gsd_mission_freshness.check()'s result on the armable path."""
    armable = True
    outcome = "FRESH"
    reason = "stubbed by test"
    mission_terms = ["alpha", "beta", "gamma"]
    matched = ["alpha", "beta", "gamma"]
    active_milestone = "Stub Milestone"


def drive_write(command: str, tmpdir: Path) -> tuple[int, str]:
    """Run marker.main(--write) with every external dependency stubbed.

    Returns (exit_code, stdout). Writes only inside tmpdir.
    """
    written = tmpdir / "marker.json"

    def fake_write_marker(session, cmd, cwd, phase, max_cycles, max_hours):
        written.write_text(json.dumps({
            "session_id": session, "resume_command": cmd, "cwd": cwd,
            "phase": phase, "cycles": 0,
            "max_cycles": max_cycles or 12, "max_hours": max_hours or 24.0,
            "schema_version": 2,
        }, indent=2), encoding="utf-8")
        return written

    import gsd_mission_freshness as mf
    import gsd_long_run as lr

    saved = (marker.write_marker, mf.check, lr.arm_preflight, lr.ledger_append)
    marker.write_marker = fake_write_marker
    mf.check = lambda cwd, mission, workstream=None: _Verdict()
    lr.arm_preflight = lambda session, cwd, cmd, workstream=None: (True, "stubbed")
    lr.ledger_append = lambda *a, **k: None
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = marker.main([
                "--write", "--session", "test-session-0000", "--command", command,
                "--cwd", ".", "--mission", "alpha,beta,gamma",
                "--legacy-compact",  # the v2 path under test is opt-in since 2026-09-24
            ])
        return code, buf.getvalue()
    finally:
        marker.write_marker, mf.check, lr.arm_preflight, lr.ledger_append = saved


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kelb-arm-test-") as td:
        tmpdir = Path(td)
        command = "/gsd-autonomous --from 13"
        code, out = drive_write(command, tmpdir)

        if code == 0:
            _ok("V-ARM-WRITE-SUCCEEDS", "stubbed --write returned 0")
        else:
            _fail("V-ARM-WRITE-SUCCEEDS",
                  f"exit {code}; the harness could not reach the success path, so every "
                  f"gate below is UNMEASURED rather than clean. stdout={out!r}")
            print(f"\nARM_ANNOUNCE_PASS={len(_passes)}/{len(_passes) + len(_fails)}")
            return 1

        lines = [ln for ln in out.splitlines() if ln.strip()]

        # (a) the machine-readable result must stay first
        if lines and lines[0].strip().endswith("marker.json"):
            _ok("V-ARM-PATH-STAYS-FIRST-LINE",
                f"first line is the marker path ({lines[0].strip()[-24:]}) -- callers that "
                "parse stdout[0] are unaffected")
        else:
            _fail("V-ARM-PATH-STAYS-FIRST-LINE",
                  f"first non-empty line is {lines[0] if lines else '<none>'!r}, not the "
                  "marker path; this breaks every caller that parses the path")

        # (b) the instruction must exist at all
        if "NEXT STEP" in out:
            _ok("V-ARM-ANNOUNCES-NEXT-STEP", "stdout carries a NEXT STEP instruction")
        else:
            _fail("V-ARM-ANNOUNCES-NEXT-STEP",
                  "arming succeeded and said nothing about starting the run. This is the "
                  "exact defect: 4 of 9 markers were armed and never started.")

        # (c) and it must name THE REAL command, not a generic reminder
        if command in out:
            _ok("V-ARM-NAMES-THE-ACTUAL-COMMAND",
                f"the recorded command {command!r} appears verbatim -- a generic reminder "
                "would leave a reader typing the bare form and re-entering another "
                "session's first incomplete phase")
        else:
            _fail("V-ARM-NAMES-THE-ACTUAL-COMMAND",
                  f"{command!r} absent from stdout; a reminder that does not name the "
                  "command is not actionable")

        # (d) it must say plainly that nothing is running yet
        said_not_running = any(
            phrase in out for phrase in
            ("NOTHING IS RUNNING YET", "starts nothing", "It starts nothing")
        )
        if said_not_running:
            _ok("V-ARM-STATES-NOTHING-IS-RUNNING",
                "stdout states that arming launched nothing")
        else:
            _fail("V-ARM-STATES-NOTHING-IS-RUNNING",
                  "stdout never says the run has not started; 'ARMED' alone reads as done")

        # POSITIVE CONTROL: this harness can observe stdout at all. Without it, a subject
        # that printed nothing and a redirect that captured nothing look identical.
        if len(out.strip()) > 40:
            _ok("V-ARM-HARNESS-SEES-STDOUT",
                f"captured {len(out)} chars -- the observation path works, so an absence "
                "above is the subject's and not the instrument's")
        else:
            _fail("V-ARM-HARNESS-SEES-STDOUT",
                  f"captured only {len(out)} chars; the redirect may be broken, which would "
                  "make every absence assertion above meaningless")

    total = len(_passes) + len(_fails)
    print(f"\nARM_ANNOUNCE_PASS={len(_passes)}/{total}  threshold={total}/{total}")
    if _fails:
        print("FAILED GATES: " + ", ".join(_fails))
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
