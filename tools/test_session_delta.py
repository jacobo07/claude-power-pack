#!/usr/bin/env python3
"""test_session_delta.py -- V-gates for the Session Delta Gate.

Hermetic: every gate runs in its own temp git repo and its own temp OWNER_QUEUE
state dir, so the suite gives the same result on every run and never touches
~/.claude/state or this repo's working tree.

Run:  python tools/test_session_delta.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.session_delta import delta as SD          # noqa: E402
from modules.owner_queue import owner_queue as OQ      # noqa: E402

# The exact probe hooks/learning-sentinel.js applies to decide whether a file is
# a learning file. Duplicated deliberately: if the sentinel's regex changes and
# this copy does not, the gate fails, which is the signal we want.
HEADER_PROBE_RE = re.compile(
    r"## Patterns|\*\*Takeaway:\*\*|\*\*Actionable takeaway:\*\*|## What Worked|## What Failed"
)

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _git(repo: Path, *args) -> int:
    exe = SD._git_exe()
    if not exe:
        return 1
    proc = subprocess.run([exe, "-C", str(repo), *args],
                          capture_output=True, text=True, timeout=20)
    return proc.returncode


def _new_repo(tmp: Path, name: str) -> Path:
    repo = tmp / name
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    return repo


# --------------------------------------------------------------------------- #
def gate_empty_is_silent(tmp: Path) -> None:
    """A session that changed nothing and left no residual writes NOTHING."""
    # Arrange
    repo = _new_repo(tmp, "empty")
    state = tmp / "state-empty"

    # Act
    res = SD.run(repo, "sid-empty", state_dir=state, min_interval_s=0)

    # Assert
    wrote_any = list((repo / SD.LEARNINGS_REL).glob("*.md")) if (repo / SD.LEARNINGS_REL).is_dir() else []
    if res["written"] is None and res["skipped"] == "empty-delta" and not wrote_any:
        _ok("V-SDELTA-EMPTY-SILENT", "clean repo + empty queue -> no file, skipped=empty-delta")
    else:
        _fail("V-SDELTA-EMPTY-SILENT",
              f"written={res['written']} skipped={res['skipped']} files={len(wrote_any)}")


def gate_writes_on_real_delta(tmp: Path) -> None:
    """A touched path produces exactly one artifact at the derived path."""
    # Arrange
    repo = _new_repo(tmp, "touched")
    (repo / "tools").mkdir(parents=True, exist_ok=True)
    (repo / "tools" / "thing.py").write_text("x = 1\n", encoding="utf-8")
    state = tmp / "state-touched"

    # Act
    res = SD.run(repo, "sid-touch", state_dir=state, min_interval_s=0)

    # Assert
    expected = SD.target_path(repo, "sid-touch")
    files = sorted((repo / SD.LEARNINGS_REL).glob("*.md"))
    if res["written"] == str(expected) and len(files) == 1 and files[0].stat().st_size > 0:
        _ok("V-SDELTA-WRITES", f"one artifact at {files[0].name} ({files[0].stat().st_size} B)")
    else:
        _fail("V-SDELTA-WRITES", f"written={res['written']} expected={expected} files={files}")


def gate_schema_matches_sentinel(tmp: Path) -> None:
    """The artifact is recognised by learning-sentinel's own header probe."""
    # Arrange
    repo = _new_repo(tmp, "schema")
    (repo / "modules").mkdir(parents=True, exist_ok=True)
    (repo / "modules" / "x.py").write_text("y = 2\n", encoding="utf-8")
    state = tmp / "state-schema"

    # Act
    SD.run(repo, "sid-schema", state_dir=state, min_interval_s=0)
    body = SD.target_path(repo, "sid-schema").read_text(encoding="utf-8")

    # Assert
    required = ["## Patterns", "## What Worked", "## What Failed", "**Takeaway:**"]
    missing = [h for h in required if h not in body]
    if HEADER_PROBE_RE.search(body) and not missing:
        _ok("V-SDELTA-SCHEMA", "all four gather-path headers present; sentinel probe matches")
    else:
        _fail("V-SDELTA-SCHEMA", f"probe={bool(HEADER_PROBE_RE.search(body))} missing={missing}")


def gate_orphan_escalates(tmp: Path) -> None:
    """An orphaned output reaches OWNER_QUEUE -- the only escalating condition."""
    # Arrange
    state = tmp / "state-orphan"
    d = SD.SessionDelta(repo=str(tmp), sid="sid-orphan", ts="2026-08-03T00:00:00+00:00",
                        created=["modules/ghost/ghost.py"], orphans=["ghost/ghost"])

    # Act
    ids = SD.escalate(d, state_dir=state)
    rows = OQ.load(state)

    # Assert
    named = [r for r in rows if "modules/ghost/ghost" in r.get("action", "")]
    if len(ids) == 1 and len(named) == 1 and named[0]["source"] == "session_delta":
        _ok("V-SDELTA-ORPHAN-ESCALATES",
            f"OWNER_QUEUE row {ids[0]}: \"{named[0]['action']}\"")
    else:
        _fail("V-SDELTA-ORPHAN-ESCALATES", f"ids={ids} matching_rows={len(named)}")


def gate_escalation_idempotent(tmp: Path) -> None:
    """Stop fires per turn; two escalations of the same orphan stay one row."""
    # Arrange
    state = tmp / "state-idem"
    d = SD.SessionDelta(repo=str(tmp), sid="sid-idem", orphans=["ghost/ghost"])

    # Act
    first = SD.escalate(d, state_dir=state)
    second = SD.escalate(d, state_dir=state)
    rows = [r for r in OQ.load(state) if "modules/ghost/ghost" in r.get("action", "")]

    # Assert
    if first == second and len(rows) == 1:
        _ok("V-SDELTA-IDEMPOTENT", f"two escalations, same id {first}, exactly 1 row")
    else:
        _fail("V-SDELTA-IDEMPOTENT", f"first={first} second={second} rows={len(rows)}")


def gate_throttle_blocks_rewrite(tmp: Path) -> None:
    """A second Stop in the same window is a no-op; a later one is not."""
    # Arrange
    repo = _new_repo(tmp, "throttle")
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    state = tmp / "state-throttle"
    SD.run(repo, "sid-thr", state_dir=state, min_interval_s=0)

    # Act
    blocked = SD.run(repo, "sid-thr", state_dir=state, min_interval_s=300)
    later = SD.run(repo, "sid-thr", state_dir=state, min_interval_s=300,
                   now=datetime.now(timezone.utc) + timedelta(seconds=600))

    # Assert
    if blocked["skipped"] == "throttled" and later["written"]:
        _ok("V-SDELTA-THROTTLE",
            "immediate re-run skipped=throttled; +600s re-run rewrote the artifact")
    else:
        _fail("V-SDELTA-THROTTLE",
              f"blocked={blocked['skipped']} later_written={later['written']}")


def gate_new_package_is_seen(tmp: Path) -> None:
    """A brand-new module PACKAGE reaches the orphan check.

    Regression gate: plain `git status --porcelain` collapses an untracked
    directory to one `modules/pkg/` row, which silently skipped the exact case
    the orphan check exists for. Found by the live-payload proof, 2026-08-03."""
    # Arrange
    repo = _new_repo(tmp, "newpkg")
    pkg = repo / "modules" / "brandnew"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "engine.py").write_text("z = 3\n", encoding="utf-8")

    # Act
    created, modified, _ = SD.git_status(repo)
    units = SD._touched_module_units(created + modified)

    # Assert
    if {"brandnew/engine", "brandnew/__init__"} <= units:
        _ok("V-SDELTA-NEW-PACKAGE-SEEN",
            f"untracked package expanded to files; units={sorted(units)}")
    else:
        _fail("V-SDELTA-NEW-PACKAGE-SEEN",
              f"units={sorted(units)} created={created}")


def gate_truncation_is_visible(tmp: Path) -> None:
    """A capped collection says so in the artifact -- no silent truncation."""
    # Arrange
    d = SD.SessionDelta(repo=str(tmp), sid="sid-trunc", ts="2026-08-03T00:00:00+00:00",
                        created=["tools/a.py"], truncated=7)

    # Act
    body = SD.render(d)

    # Assert
    if "7 changed path(s) exceeded" in body and str(SD.MAX_PATHS) in body:
        _ok("V-SDELTA-TRUNCATION-VISIBLE", "dropped-path count and cap both named in the body")
    else:
        _fail("V-SDELTA-TRUNCATION-VISIBLE", "truncation not reported in the rendered body")


def gate_takeaway_is_actionable(tmp: Path) -> None:
    """The Takeaway states a verdict owed, never a narration of the session."""
    # Arrange
    orphaned = SD.SessionDelta(orphans=["ghost/ghost"], created=["modules/ghost/ghost.py"])
    clean = SD.SessionDelta(created=["tools/a.py"])

    # Act
    t_orphan = SD.takeaway(orphaned)
    t_clean = SD.takeaway(clean)

    # Assert
    if ("WIRE / DECLARE / DELETE" in t_orphan and t_orphan.startswith("**Takeaway:**")
            and "delta is zero" in t_clean):
        _ok("V-SDELTA-TAKEAWAY-ACTIONABLE",
            "orphan -> a named verdict owed; clean -> an explicit zero, not filler")
    else:
        _fail("V-SDELTA-TAKEAWAY-ACTIONABLE", f"orphan={t_orphan[:60]!r} clean={t_clean[:60]!r}")


def gate_failopen(tmp: Path) -> None:
    """A nonexistent repo is a silent no-op and main() still exits 0."""
    # Arrange
    missing = tmp / "does-not-exist"
    state = tmp / "state-missing"

    # Act
    res = SD.run(missing, "sid-missing", state_dir=state, min_interval_s=0)
    code = SD.main(["--repo", str(missing), "--sid", "sid-missing", "--dry-run",
                    "--json", "--state-dir", str(state)])

    # Assert
    if res["written"] is None and code == 0:
        _ok("V-SDELTA-FAILOPEN", f"missing repo -> no write, skipped={res['skipped']}, main() exit 0")
    else:
        _fail("V-SDELTA-FAILOPEN", f"written={res['written']} exit={code}")


def main() -> int:
    print("== session_delta (Session Delta Gate) ==")
    with tempfile.TemporaryDirectory(prefix="pp-sdelta-") as td:
        tmp = Path(td)
        gate_empty_is_silent(tmp)
        gate_writes_on_real_delta(tmp)
        gate_schema_matches_sentinel(tmp)
        gate_orphan_escalates(tmp)
        gate_escalation_idempotent(tmp)
        gate_throttle_blocks_rewrite(tmp)
        gate_new_package_is_seen(tmp)
        gate_truncation_is_visible(tmp)
        gate_takeaway_is_actionable(tmp)
        gate_failopen(tmp)
    total = _PASS + _FAIL
    print(f"\nSESSION_DELTA_PASS={_PASS}/{total}  threshold={total}/{total}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
