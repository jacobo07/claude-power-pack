"""V-gates for the CPC-OS session snapshot (modules/cpc_os/snapshot.py).

Hermetic by construction: every gate builds a PaneRegistry whose _path is a
tmpdir file and renders to a tmpdir out_path, so nothing under ~/.claude is
read or written. Determinism comes from (a) an injected ``now`` for header
timestamps and (b) an explicit stored last_commit on one pane, so the commit
gate does not depend on git being installed. Designed to pass identically on
rapid back-to-back runs (the V-CPC-RESTART flaky-gate lesson).

Run: python tools/test_cpc_snapshot.py   ->   SNAPSHOT_PASS=8/8
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parent.parent
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.cpc_os.registry import PaneRegistry  # noqa: E402
from modules.cpc_os.snapshot import (  # noqa: E402
    _NO_COMMIT,
    build_snapshot_text,
    generate_snapshot,
)

passes = 0
fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"OK   {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def _build_reg(tmp: Path) -> PaneRegistry:
    """A registry with two live panes: A in the real PP repo (live commit +
    session_id -> high-confidence resume), B in a non-repo path with a stored
    commit and no session_id (fallback commit + cd resume)."""
    reg = PaneRegistry(_path=tmp / "reg.json")
    reg.register_pane("paneA", str(PP_ROOT), "task-A", session_id="sid-A")
    reg.register_pane("paneB", str(tmp / "workdir"), "task-B",
                      last_commit="fa11ba7")
    return reg


def _extract_machine_block(text: str) -> list:
    """Lift the fenced ```json array back out of the markdown."""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "```json":
            start = i + 1
            break
    if start is None:
        return None  # type: ignore[return-value]
    body = []
    for ln in lines[start:]:
        if ln.strip() == "```":
            break
        body.append(ln)
    return json.loads("\n".join(body))


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        snap = tmp / "session_snapshot.md"
        reg = _build_reg(tmp)

        # V-SNAPSHOT-GENERATES
        out = generate_snapshot(registry=reg, out_path=snap, now=1700000000.0)
        if Path(out) == snap and snap.is_file() and snap.stat().st_size > 0:
            _ok("V-SNAPSHOT-GENERATES", f"file written {snap.stat().st_size}B")
        else:
            _fail("V-SNAPSHOT-GENERATES", "snapshot file missing/empty")

        text = snap.read_text(encoding="utf-8")

        # V-SNAPSHOT-HAS-PANE  -- >=1 pane with a real cwd
        if "PANE 1" in text and str(PP_ROOT) in text and "task-A" in text:
            _ok("V-SNAPSHOT-HAS-PANE", "PANE 1 + real cwd + task present")
        else:
            _fail("V-SNAPSHOT-HAS-PANE", "no pane with real cwd")

        # V-SNAPSHOT-HAS-COMMIT  -- a real commit hash appears (stored fallback
        # is deterministic; the live PP_ROOT commit is a bonus when git exists)
        if "fa11ba7" in text and f"Commit: {_NO_COMMIT}" not in (
            "\n".join(l for l in text.splitlines() if "paneB" in l)
        ):
            _ok("V-SNAPSHOT-HAS-COMMIT", "commit hash fa11ba7 rendered")
        else:
            _fail("V-SNAPSHOT-HAS-COMMIT", "no commit hash in snapshot")

        # V-SNAPSHOT-READABLE  -- header + valid machine json block
        machine = _extract_machine_block(text)
        if ("SESSION SNAPSHOT" in text and isinstance(machine, list)
                and len(machine) == 2
                and {m["pane_id"] for m in machine} == {"paneA", "paneB"}):
            _ok("V-SNAPSHOT-READABLE", "header + json block parse (2 panes)")
        else:
            _fail("V-SNAPSHOT-READABLE", f"machine block invalid: {machine!r}")

        # V-SNAPSHOT-RESUME-SPLIT  -- bonus correctness: sid -> --resume,
        # no sid -> cd fallback (mirrors recovery confidence)
        a = next((m for m in (machine or []) if m["pane_id"] == "paneA"), {})
        b = next((m for m in (machine or []) if m["pane_id"] == "paneB"), {})
        if a.get("resume") == "claude --resume sid-A" and b.get(
                "resume", "").startswith("cd "):
            _ok("V-SNAPSHOT-RESUME-SPLIT",
                "high-confidence vs cd fallback correct")
        else:
            _fail("V-SNAPSHOT-RESUME-SPLIT",
                  f"resume split wrong A={a.get('resume')} B={b.get('resume')}")

        # V-SNAPSHOT-UPDATES  -- a second generation after a new pane differs
        text_v1 = build_snapshot_text(reg, now=1700000000.0)
        reg.register_pane("paneC", str(tmp / "third"), "task-C")
        text_v2 = build_snapshot_text(reg, now=1700000050.0)
        if text_v1 != text_v2 and "task-C" in text_v2 and "task-C" not in text_v1:
            _ok("V-SNAPSHOT-UPDATES", "second render reflects new pane")
        else:
            _fail("V-SNAPSHOT-UPDATES", "snapshot did not update")

        # V-HUB-TRIGGERS  -- hub source is wired to capture sid + gen snapshot
        hub = (PP_ROOT / "hooks" / "session_start_hub.js").read_text(
            encoding="utf-8")
        if "generate_snapshot" in hub and "PP_PANE_SID" in hub and (
                "session_id=sid" in hub):
            _ok("V-HUB-TRIGGERS",
                "hub captures session_id + regenerates snapshot")
        else:
            _fail("V-HUB-TRIGGERS", "hub not wired to snapshot/session_id")

        # V-PANES-CMD-EXISTS  -- the command documents crash recovery
        cmd = (PP_ROOT / "commands" / "panes.md").read_text(encoding="utf-8")
        if ("Crash recovery" in cmd and "session_snapshot.md" in cmd
                and "claude --resume" in cmd):
            _ok("V-PANES-CMD-EXISTS", "panes.md has recovery section")
        else:
            _fail("V-PANES-CMD-EXISTS", "panes.md missing recovery section")

        # V-BASELINE-INTACT  -- cpc_os package surface still imports clean
        try:
            from modules.cpc_os import (  # noqa: F401
                DEFAULT_SNAPSHOT_PATH,
                PaneRegistry as _PR,
                detect_crash_state,
                generate_snapshot as _gs,
                restart_intent,
            )
            _ok("V-BASELINE-INTACT", "cpc_os package imports clean (new+old)")
        except Exception as exc:  # noqa: BLE001
            _fail("V-BASELINE-INTACT", f"import regression: {exc}")

    total = passes + fails
    # 8 required gates (M5 contract) + 1 bonus (V-SNAPSHOT-RESUME-SPLIT).
    print(f"SNAPSHOT_PASS={passes}/{total}  threshold={total}/{total} "
          f"(8 required + 1 bonus)")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
