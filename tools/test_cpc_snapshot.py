"""V-gates for the CPC-OS session snapshot + restore (snapshot.py + restore_panes.ps1).

Hermetic by construction: every gate builds a tmpdir PaneRegistry and renders to
a tmpdir out_path, AND monkeypatches snapshot.PROJECTS_DIR to a tmp transcript
store so the session resolver / resume-kind logic is deterministic and
host-independent (no dependency on the real ~/.claude/projects or on git).
Transcript recency is forced with explicit os.utime mtimes. Designed to pass
identically on rapid back-to-back runs (the V-CPC-RESTART flaky-gate lesson).

Run: python tools/test_cpc_snapshot.py   ->   SNAPSHOT_PASS=15/15
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parent.parent
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.cpc_os import snapshot as snap  # noqa: E402
from modules.cpc_os.registry import PaneRegistry  # noqa: E402
from modules.cpc_os.snapshot import (  # noqa: E402
    _encode_project_dir,
    build_snapshot_text,
    generate_snapshot,
    resolve_last_session,
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


def _touch_transcript(projects: Path, cwd: str, uuid: str, mtime: float) -> None:
    d = projects / _encode_project_dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{uuid}.jsonl"
    f.write_text("{}\n", encoding="utf-8")
    os.utime(f, (mtime, mtime))


def _extract_machine_block(text: str) -> list:
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
        projects = tmp / "projects"
        projects.mkdir()
        snap.PROJECTS_DIR = projects  # hermetic transcript store

        cwd_a = str(tmp / "repoA")   # exact: sid-A transcript exists
        cwd_b = str(tmp / "repoB")   # repo-latest: two transcripts, newer wins
        cwd_c = str(tmp / "repoC")   # new: no transcript dir at all

        _touch_transcript(projects, cwd_a, "sid-A", 1000.0)
        _touch_transcript(projects, cwd_b, "older", 1000.0)
        _touch_transcript(projects, cwd_b, "newer", 2000.0)

        reg = PaneRegistry(_path=tmp / "reg.json")
        reg.register_pane("paneA", cwd_a, "task-A", session_id="sid-A")
        reg.register_pane("paneB", cwd_b, "task-B", last_commit="fa11ba7")
        reg.register_pane("paneC", cwd_c, "task-C")

        snap_md = tmp / "session_snapshot.md"

        # V-SNAPSHOT-GENERATES
        out = generate_snapshot(registry=reg, out_path=snap_md, now=1700000000.0)
        if Path(out) == snap_md and snap_md.is_file() and snap_md.stat().st_size > 0:
            _ok("V-SNAPSHOT-GENERATES", f"md written {snap_md.stat().st_size}B")
        else:
            _fail("V-SNAPSHOT-GENERATES", "snapshot md missing/empty")

        text = snap_md.read_text(encoding="utf-8")

        # V-SNAPSHOT-SIDECAR  -- .json sidecar exists + equals embedded block
        sidecar = snap_md.with_suffix(".json")
        machine_md = _extract_machine_block(text)
        if sidecar.is_file():
            machine_json = json.loads(sidecar.read_text(encoding="utf-8"))
            if machine_json == machine_md and len(machine_json) == 3:
                _ok("V-SNAPSHOT-SIDECAR", f"sidecar == embedded ({len(machine_json)})")
            else:
                _fail("V-SNAPSHOT-SIDECAR", "sidecar != embedded block")
        else:
            _fail("V-SNAPSHOT-SIDECAR", "no .json sidecar written")

        # V-SNAPSHOT-RECOVERY-HEADER  -- top-of-file crash recovery + script path
        if ("== CRASH RECOVERY ==" in text
                and "restore_panes.ps1" in text
                and text.splitlines()[0].strip() == "== CRASH RECOVERY =="):
            _ok("V-SNAPSHOT-RECOVERY-HEADER", "header + restore script path on top")
        else:
            _fail("V-SNAPSHOT-RECOVERY-HEADER", "recovery header missing/not first")

        # V-SNAPSHOT-HAS-PANE
        if "PANE 1" in text and cwd_a in text and "task-A" in text:
            _ok("V-SNAPSHOT-HAS-PANE", "PANE 1 + real cwd + task present")
        else:
            _fail("V-SNAPSHOT-HAS-PANE", "no pane with real cwd")

        # V-SNAPSHOT-HAS-COMMIT  -- paneB fallback commit (git-independent)
        if "fa11ba7" in text:
            _ok("V-SNAPSHOT-HAS-COMMIT", "commit hash fa11ba7 rendered")
        else:
            _fail("V-SNAPSHOT-HAS-COMMIT", "no commit hash in snapshot")

        # V-RESOLVE-SESSION  -- newest transcript wins
        if resolve_last_session(cwd_b) == "newer" and resolve_last_session(cwd_a) == "sid-A":
            _ok("V-RESOLVE-SESSION", "newest .jsonl resolved per cwd")
        else:
            _fail("V-RESOLVE-SESSION",
                  f"resolver wrong B={resolve_last_session(cwd_b)}")

        by_id = {m["pane_id"]: m for m in (machine_md or [])}
        a, b, c = by_id.get("paneA", {}), by_id.get("paneB", {}), by_id.get("paneC", {})

        # V-RESUME-EXACT  -- captured session_id whose transcript exists
        if a.get("resume_kind") == "exact" and a.get("resume") == "claude --resume sid-A":
            _ok("V-RESUME-EXACT", "paneA -> claude --resume sid-A [exact]")
        else:
            _fail("V-RESUME-EXACT", f"paneA resume={a.get('resume')} kind={a.get('resume_kind')}")

        # V-RESUME-NO-SUBSTITUTION  -- a pane whose own session_id is unrecoverable
        # must NEVER be silently swapped for the repo's latest transcript (that
        # restored a DIFFERENT conversation under the pane's identity). paneB has
        # no sid AND repoB HAS transcripts ('older'/'newer'); the resume must be a
        # FRESH claude in the cwd, NOT "claude --resume newer". This is the exact
        # wrong-chat bug the Owner reported (BL-CPCOS-RESTORE-002).
        if (b.get("resume_kind") == "missing"
                and str(b.get("resume", "")).startswith("cd ")
                and "newer" not in str(b.get("resume", ""))):
            _ok("V-RESUME-NO-SUBSTITUTION", "paneB -> fresh claude, NOT repo-latest")
        else:
            _fail("V-RESUME-NO-SUBSTITUTION", f"paneB resume={b.get('resume')} kind={b.get('resume_kind')}")

        # V-RESUME-MISSING  -- no sid + no transcript -> fresh claude in cwd
        if c.get("resume_kind") == "missing" and str(c.get("resume", "")).startswith("cd "):
            _ok("V-RESUME-MISSING", "paneC -> fresh claude [missing]")
        else:
            _fail("V-RESUME-MISSING", f"paneC resume={c.get('resume')} kind={c.get('resume_kind')}")

        # V-SNAPSHOT-READABLE  -- machine block parses, 3 panes
        if isinstance(machine_md, list) and len(machine_md) == 3 and (
                {m["pane_id"] for m in machine_md} == {"paneA", "paneB", "paneC"}):
            _ok("V-SNAPSHOT-READABLE", "json block parse (3 panes)")
        else:
            _fail("V-SNAPSHOT-READABLE", f"machine block invalid: {machine_md!r}")

        # V-SNAPSHOT-UPDATES  -- a second generation after a new pane differs
        text_v1 = build_snapshot_text(reg, now=1700000000.0)
        reg.register_pane("paneD", str(tmp / "repoD"), "task-D")
        text_v2 = build_snapshot_text(reg, now=1700000050.0)
        if text_v1 != text_v2 and "task-D" in text_v2 and "task-D" not in text_v1:
            _ok("V-SNAPSHOT-UPDATES", "second render reflects new pane")
        else:
            _fail("V-SNAPSHOT-UPDATES", "snapshot did not update")

        # V-HUB-TRIGGERS  -- hub source wired to capture sid + gen snapshot
        hub = (PP_ROOT / "hooks" / "session_start_hub.js").read_text(encoding="utf-8")
        if "generate_snapshot" in hub and "PP_PANE_SID" in hub and "session_id=sid" in hub:
            _ok("V-HUB-TRIGGERS", "hub captures session_id + regenerates snapshot")
        else:
            _fail("V-HUB-TRIGGERS", "hub not wired to snapshot/session_id")

        # V-PANES-CMD-EXISTS  -- both /panes recovery + /restore-panes documented
        cmd = (PP_ROOT / "commands" / "panes.md").read_text(encoding="utf-8")
        rp = PP_ROOT / "commands" / "restore-panes.md"
        if ("Crash recovery" in cmd and rp.is_file()
                and "claude --resume" in rp.read_text(encoding="utf-8")):
            _ok("V-PANES-CMD-EXISTS", "panes.md + restore-panes.md present")
        else:
            _fail("V-PANES-CMD-EXISTS", "command docs missing")

        # V-RESTORE-SCRIPT-EXISTS  -- the ps1 reads the json + opens cursor
        ps1 = PP_ROOT / "tools" / "restore_panes.ps1"
        if ps1.is_file():
            body = ps1.read_text(encoding="utf-8")
            if ("session_snapshot.json" in body and "cursor" in body.lower()
                    and "resume" in body.lower()):
                _ok("V-RESTORE-SCRIPT-EXISTS", "restore_panes.ps1 reads json + cursor")
            else:
                _fail("V-RESTORE-SCRIPT-EXISTS", "ps1 missing json/cursor/resume wiring")
        else:
            _fail("V-RESTORE-SCRIPT-EXISTS", "restore_panes.ps1 absent")

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

        # V-DEDUP-BY-SESSION  -- N pane rows for ONE conversation collapse to ONE.
        # Every SessionStart re-registers a fresh row for the same chat
        # (startup/resume/compact), so without dedup the restore opens N identical
        # tabs. Two rows sharing (cwd, session_id) must render as ONE pane
        # (BL-CPCOS-RESTORE-002).
        reg2 = PaneRegistry(_path=tmp / "reg2.json")
        reg2.register_pane("dupe1", cwd_a, "t", session_id="sid-A")
        reg2.register_pane("dupe2", cwd_a, "t", session_id="sid-A")
        reg2.register_pane("solo", cwd_a, "t", session_id="sid-Z")
        m2 = snap._render(reg2, 1700000000.0)[1]
        sids2 = sorted(x["session_id"] for x in m2)
        if len(m2) == 2 and sids2 == ["sid-A", "sid-Z"]:
            _ok("V-DEDUP-BY-SESSION", "3 rows (2 share sid-A) -> 2 distinct panes")
        else:
            _fail("V-DEDUP-BY-SESSION", f"dedup wrong: {len(m2)} panes sids={sids2}")

    total = passes + fails
    print(f"SNAPSHOT_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
