"""V-CLOSED-LOOP test: two DEEP runs on the same diff write +
surface patterns.jsonl rows.

Run 1: writes a patterns.jsonl row (verdict != PASS).
Run 2: should surface that row in `patterns_history`.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent.parent
REVIEWER = HERE / "code_reviewer.py"
PATTERNS_LOG = PP_ROOT / "vault" / "reviews" / "patterns.jsonl"

# A doctrine WARN diff (avoids the AWS-key path so the patterns log
# row carries a category we can reason about).
LOOP_DIFF = textwrap.dedent("""\
    diff --git a/hooks/bad.js b/hooks/bad.js
    new file mode 100644
    --- /dev/null
    +++ b/hooks/bad.js
    @@ -0,0 +1,3 @@
    +const { execSync } = require('child_process');
    +const result = execSync('python', ['script.py']);
    +console.log(result.toString());
""")


def run_deep(diff_text: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(REVIEWER), "--deep", "--cwd", str(PP_ROOT)],
        input=diff_text.encode("utf-8"),
        capture_output=True,
        timeout=60,
    )
    raw = proc.stdout.decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"verdict": "ERROR", "raw": raw,
                "stderr": proc.stderr.decode("utf-8", "replace")}


def main() -> int:
    # Snapshot the patterns log length so we can detect a new row.
    before_count = 0
    if PATTERNS_LOG.is_file():
        before_count = sum(
            1 for line in PATTERNS_LOG.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    print(f"patterns.jsonl rows before run 1: {before_count}")

    print("\n--- Run 1 ---")
    r1 = run_deep(LOOP_DIFF)
    print(f"verdict={r1.get('verdict')}  findings={len(r1.get('findings', []))}  "
          f"history_rows_returned={len(r1.get('patterns_history', []))}")

    # Verify a new row was appended.
    after_count = 0
    if PATTERNS_LOG.is_file():
        after_count = sum(
            1 for line in PATTERNS_LOG.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    print(f"patterns.jsonl rows after run 1: {after_count}")
    appended_ok = (after_count == before_count + 1)

    print("\n--- Run 2 (same diff) ---")
    r2 = run_deep(LOOP_DIFF)
    history_rows = r2.get("patterns_history", [])
    print(f"verdict={r2.get('verdict')}  findings={len(r2.get('findings', []))}  "
          f"history_rows_returned={len(history_rows)}")

    if history_rows:
        print(f"  First history row: category={history_rows[0].get('category')}")
        print(f"                     verdict={history_rows[0].get('verdict')}")
        print(f"                     file={history_rows[0].get('file')}")

    # The new row from run 1 should appear in run 2's patterns_history.
    found_self = any(
        row.get("category") == "doctrine-bare-python-spawn"
        and row.get("file") == "hooks/bad.js"
        for row in history_rows
    )

    print("\nClosed-loop checks:")
    print(f"  Row appended after run 1:        {'PASS' if appended_ok else 'FAIL'}")
    print(f"  Run 2 surfaces run 1's row:      {'PASS' if found_self else 'FAIL'}")

    ok = appended_ok and found_self
    print(f"\nV-CLOSED-LOOP: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
