"""V-COMBINED test: auto_test.py --gate with a code-review BLOCK diff.

Verifies that:
1. A synthetic diff containing a hardcoded AWS key triggers the
   code-review BLOCK path inside auto_test.py.
2. The combined verdict becomes "fail" (so auto-test-gate.js exit 2).
3. extra.code_review.verdict is "block".
4. The reason string mentions code-review.

A clean diff produces verdict=skip (no testable files), extra empty.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent.parent
AUTO_TEST = PP_ROOT / "modules" / "auto-testing" / "auto_test.py"

BLOCK_DIFF = textwrap.dedent("""\
    diff --git a/src/leak.py b/src/leak.py
    new file mode 100644
    --- /dev/null
    +++ b/src/leak.py
    @@ -0,0 +1,2 @@
    +# Hardcoded credential -- code-review BLOCK target
    +AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
""")

CLEAN_DIFF = textwrap.dedent("""\
    diff --git a/docs/note.md b/docs/note.md
    new file mode 100644
    --- /dev/null
    +++ b/docs/note.md
    @@ -0,0 +1,2 @@
    +# Note
    +Just a tiny doc change with no code.
""")


def run_gate(cwd: Path, diff_text: str) -> dict:
    """Write the diff to a temp file and pass to auto_test --gate."""
    with tempfile.NamedTemporaryFile("w", suffix=".diff",
                                     encoding="utf-8",
                                     delete=False) as tf:
        tf.write(diff_text)
        diff_path = tf.name
    try:
        proc = subprocess.run(
            [sys.executable, str(AUTO_TEST), "--gate",
             "--cwd", str(cwd), "--mode", "fast",
             "--diff", diff_path],
            capture_output=True,
            timeout=60,
        )
        raw = proc.stdout.decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"verdict": "ERROR", "raw": raw,
                    "stderr": proc.stderr.decode("utf-8", "replace"),
                    "returncode": proc.returncode}
    finally:
        try:
            Path(diff_path).unlink()
        except OSError:
            pass


def main() -> int:
    # Use a temp dir as cwd so auto-test detects nothing testable.
    with tempfile.TemporaryDirectory() as td:
        cwd = Path(td)

        print("--- V-COMBINED-BLOCK ---")
        result_block = run_gate(cwd, BLOCK_DIFF)
        print(json.dumps({
            "verdict": result_block.get("verdict"),
            "project_type": result_block.get("project_type"),
            "reason": (result_block.get("reason") or "")[:200],
            "extra_code_review_verdict": (result_block.get("extra") or {})
                .get("code_review", {}).get("verdict"),
        }, indent=2))

        ok_block = (
            result_block.get("verdict") == "fail"
            and (result_block.get("extra") or {}).get("code_review", {})
                .get("verdict") == "block"
            and "code-review" in (result_block.get("reason") or "").lower()
        )
        print(f"V-COMBINED-BLOCK: {'PASS' if ok_block else 'FAIL'}")

        print("\n--- V-COMBINED-PASS ---")
        result_clean = run_gate(cwd, CLEAN_DIFF)
        print(json.dumps({
            "verdict": result_clean.get("verdict"),
            "project_type": result_clean.get("project_type"),
            "extra_code_review_verdict": (result_clean.get("extra") or {})
                .get("code_review", {}).get("verdict"),
        }, indent=2))

        ok_clean = result_clean.get("verdict") in ("skip", "pass", "ceiling")

        print(f"V-COMBINED-PASS: {'PASS' if ok_clean else 'FAIL'}")

        return 0 if (ok_block and ok_clean) else 1


if __name__ == "__main__":
    sys.exit(main())
