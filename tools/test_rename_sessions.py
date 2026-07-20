#!/usr/bin/env python3
"""V-gate tests for rename_sessions.py -- proves the append is non-corrupting.

Reality Contract: the evidence is the observed output, not the description.
Runs against a TEMP COPY of a real transcript (never a live one), verifying that
the append preserves every original byte, adds exactly one valid record, and
leaves the whole file JSON-parseable line by line.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rename_sessions as R  # noqa: E402

passes = 0
fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global fails
    fails += 1
    print(f"  FAIL {gate}: {diag}")


def pick_sample() -> Path | None:
    proj = R.DEFAULT_PROJECT
    for p in sorted(proj.glob("*.jsonl")):
        if p.stat().st_size > 0:
            return p
    return None


try:  # pytest is optional -- this file also runs standalone via main().
    import pytest

    @pytest.fixture
    def sample() -> Path:
        """Supply the transcript main() picks at line ~145.

        pick_sample() returns None on a machine with no non-empty
        transcript; skip rather than fail, since that is an environment
        property and not a defect in rename_sessions.
        """
        picked = pick_sample()
        if picked is None:
            pytest.skip("no non-empty transcript available to sample")
        return picked

except ImportError:  # pragma: no cover - standalone execution path
    pass


def test_append_intact(sample: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / sample.name
        shutil.copy2(sample, tmp)
        original = tmp.read_bytes()
        n = len(original)
        pre = hashlib.sha256(original).hexdigest()

        uuid = tmp.stem
        title = "V-GATE — rename safety proof ⚡ áéí"  # non-ascii to exercise UTF-8
        ok, msg = R.apply_one(tmp, uuid, title)
        if not ok:
            _fail("V-RENAME-APPEND-OK", f"apply_one returned False: {msg}")
            return
        _ok("V-RENAME-APPEND-OK", msg)

        after = tmp.read_bytes()
        # Prefix byte-identity.
        if hashlib.sha256(after[:n]).hexdigest() == pre:
            _ok("V-RENAME-PREFIX-SHA256", f"original {n}B unchanged ({pre[:12]}...)")
        else:
            _fail("V-RENAME-PREFIX-SHA256", "original bytes mutated by append")

        # Exactly one record added, decoding to the expected object.
        added = after[n:]
        expected = R.build_record(uuid, title)
        if added == expected:
            _ok("V-RENAME-EXACT-LINE", f"+{len(added)}B == expected record")
        else:
            _fail("V-RENAME-EXACT-LINE", f"tail {added!r} != {expected!r}")

        # No BOM, LF terminator.
        if not added.startswith(b"\xef\xbb\xbf") and added.endswith(b"\n") and b"\r" not in added:
            _ok("V-RENAME-ENCODING", "UTF-8 no-BOM, LF terminator, no CR")
        else:
            _fail("V-RENAME-ENCODING", "BOM/CRLF contamination in appended line")

        # Whole file still parses line by line.
        bad = 0
        for ln in after.decode("utf-8").split("\n"):
            if not ln.strip():
                continue
            try:
                json.loads(ln)
            except Exception:
                bad += 1
        if bad == 0:
            _ok("V-RENAME-FULL-PARSE", "every non-empty line is valid JSON post-append")
        else:
            _fail("V-RENAME-FULL-PARSE", f"{bad} unparseable line(s) after append")

        # The appended record is the one the picker will now show.
        parsed = json.loads(added.decode("utf-8"))
        if (parsed.get("type") == "custom-title"
                and parsed.get("customTitle") == title
                and parsed.get("sessionId") == uuid):
            _ok("V-RENAME-PICKER-RECORD", f"custom-title={parsed['customTitle']!r}")
        else:
            _fail("V-RENAME-PICKER-RECORD", f"unexpected record: {parsed}")


def test_format_matches_harness() -> None:
    rec = R.build_record("abc", "hi").decode("utf-8")
    if rec == '{"type":"custom-title","customTitle":"hi","sessionId":"abc"}\n':
        _ok("V-RENAME-HARNESS-SHAPE", "no-space separators, key order type/customTitle/sessionId")
    else:
        _fail("V-RENAME-HARNESS-SHAPE", f"got {rec!r}")


def test_classifiers() -> None:
    # is_reclaimable_title(base, repo): machine-derived / legacy-residue titles are
    # reclaimable (True); a genuine human Ctrl+R name is not (False). Includes the
    # exact legacy patterns the 2026-07-06 reconciliation had to reclaim.
    repo = "claude-power-pack"
    cases = {
        "": True,                                          # empty
        "1a2b3c4d": True, "ABCDEF01": True,                # bare 8-hex fallback
        "0d3d7cb2-7d8d-4c75-a839-1e29a772022c": True,      # full UUID
        "claude-power-pack": True,                          # bare repo token
        "claude-power-pack — PREFLIGHT: git fetch": True,   # legacy '<repo> — ' residue
        "SUB - SERP: erlang otp": True,                     # our own SUB label -> refine
        "Optimize RAM footprint": False,                    # real name
        "Fix bug 12345": False,                             # real name
    }
    bad = {k: R.is_reclaimable_title(k, repo) for k, v in cases.items()
           if R.is_reclaimable_title(k, repo) != v}
    _ok("V-RENAME-RECLAIM-DETECT", f"{len(cases)}/{len(cases)} reclaim cases correct") \
        if not bad else _fail("V-RENAME-RECLAIM-DETECT", f"misclassified: {bad}")

    proj = R.DEFAULT_PROJECT
    canon = R.is_canonical_location(proj, str(Path.home() / ".claude" / "skills" / "claude-power-pack"))
    ghost = R.is_canonical_location(proj, r"C:\Users\User\Apps\mcp-video-analyzer")
    if canon and not ghost:
        _ok("V-RENAME-CANONICAL", "own cwd canonical; foreign cwd flagged mislocated")
    else:
        _fail("V-RENAME-CANONICAL", f"canon={canon} ghost={ghost}")


def main() -> int:
    print("V-gate: rename_sessions safety")
    sample = pick_sample()
    if sample is None:
        _fail("V-RENAME-SAMPLE", "no non-empty transcript to test against")
    else:
        print(f"  sample: {sample.name} ({sample.stat().st_size} B, temp copy only)")
        test_append_intact(sample)
    test_format_matches_harness()
    test_classifiers()
    print(f"RENAME_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
