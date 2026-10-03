"""V-CAPDIR gates for modules.skill_router.skill_index.directory_rows (K4 gateway index, audit G9).

    python tools/test_capability_directory.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.skill_router.skill_index import SkillEntry, build_index, directory_rows  # noqa: E402

passes = fails = 0


def gate(name, ok, ev):
    global passes, fails
    passes, fails = passes + ok, fails + (not ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}: {ev}")


def main():
    # Arrange: a real SKILL.md on disk, one whose file is gone, one synthetic CLI card
    tmp = Path(tempfile.mkdtemp(prefix="capdir-"))
    real = tmp / "alpha" / "SKILL.md"
    real.parent.mkdir()
    real.write_text("---\nname: alpha\ndescription: x\n---\n", encoding="utf-8")
    entries = [
        SkillEntry(name="alpha", path=str(real), description="Decompile APKs. Second sentence.", domain="x"),
        SkillEntry(name="gone", path=str(tmp / "gone" / "SKILL.md"), description="Gone.", domain="x"),
        SkillEntry(name="cli card", path=str(tmp / "tool.py"), description="Synthetic.", domain="spec"),
    ]
    # Act
    rows, missing = directory_rows(["alpha", "gone", "cli card", "never-installed"], entries)
    # Assert
    gate("V-CAPDIR-ROW", rows == [{"name": "alpha", "line": "Decompile APKs.", "path": str(real)}], str(rows))
    gate("V-CAPDIR-NO-DANGLING", missing == ["gone", "cli card", "never-installed"], str(missing))
    # Positive control on the real estate: an installed skill resolves to a SKILL.md that exists.
    live_rows, _ = directory_rows(["android-reverse-engineering"], build_index())
    gate("V-CAPDIR-LIVE-ESTATE", len(live_rows) == 1 and Path(live_rows[0]["path"]).is_file(),
         live_rows[0]["path"] if live_rows else "android-reverse-engineering not resolved")
    print(f"CAPDIR_PASS={passes}/{passes + fails}  threshold=3/3")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
