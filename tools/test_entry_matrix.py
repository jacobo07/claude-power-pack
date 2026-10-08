"""V-EMX gates for tools/entry_matrix.py (A3b B0, salvaged in R0 of vault/plans/ce-a3b-recovery-2026-10-08.md).

Each gate plants a tiny repo and drives the scanner from both poles, so a scanner that matches nothing
cannot pass (positive controls) and one that matches everything cannot pass either (negative cases).
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import entry_matrix as em  # noqa: E402

passes = fails = 0


def _ok(gate, cond, detail):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}")
    else:
        fails += 1
        print(f"FAIL {gate}: {detail}")


def plant(root: Path, files: dict):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def files_in(rows, cls):
    return {r["file"]: r for r in rows[cls]}


HEADLESS = "claude --bg / -p (headless)"


def main():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        plant(root, {
            # Arrange: one real unbound launch, one bound launch, one docstring-only and one comment-only mention.
            "tools/launch_raw.py": 'import subprocess\nsubprocess.run(["claude", "-p", "x"])\n',
            "tools/launch_bound.py": 'import subprocess\n# mission_spend binds this\nsubprocess.run(["claude", "-p", "x"])\n',
            "tools/doc_only.py": '"""Runs like: claude -p "do it"\nnothing launched here\n"""\nX = 1\n',
            "hooks/comment_only.js": '// claude -p is how a worker starts\nmodule.exports = {};\n',
            "tools/entry_matrix.py": (Path(em.__file__).read_text(encoding="utf-8")),
        })
        # Act
        rows = em.scan(root)
        got = files_in(rows, HEADLESS)
        out1, out2 = em.render(rows), em.render(em.scan(root))

    # Assert
    _ok("V-EMX-PLANTED-UNBOUND-SEEN", "tools/launch_raw.py" in got, sorted(got))
    _ok("V-EMX-UNBOUND-LABEL-HONEST", em.UNSEEN_LABEL in out1 and "| unbounded |" not in out1,
        "label still claims unbounded")
    _ok("V-EMX-BOUND-CONTROL", got.get("tools/launch_bound.py", {}).get("binding") is True,
        "a file with a binding ref must be found AND marked bound")
    raw = got.get("tools/launch_raw.py", {})
    _ok("V-EMX-CODE-SITE-COUNTED", raw.get("n", 0) >= 1 and raw.get("mention_only") is False,
        f"a real launch line must count as a code site: {raw}")
    for gate, f in (("V-EMX-DOCSTRING-MENTION-ONLY", "tools/doc_only.py"),
                    ("V-EMX-COMMENT-MENTION-ONLY", "hooks/comment_only.js")):
        r = got.get(f)
        # Neither a site (n == 0) nor dropped: a described launch stays visible as UNJUDGED.
        _ok(gate, r is not None and r["n"] == 0 and r["mention_only"] is True, f"{f}: {r}")
    _ok("V-EMX-MENTION-LABELLED", "mention only -- " in out1, "mention-only rows not labelled")
    _ok("V-EMX-SELF-EXCLUDED", not any(f.endswith("entry_matrix.py") for c in rows for f in files_in(rows, c)),
        "scanner matched its own source")
    _ok("V-EMX-DETERMINISTIC", out1 == out2, "two runs differ")
    print(f"EMX_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
