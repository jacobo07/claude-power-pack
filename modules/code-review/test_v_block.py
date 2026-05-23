"""V-block runner for code_reviewer.py.

Builds synthetic unified diffs and pipes each into code_reviewer.py
--fast --diff <text>, asserting expected verdict + finding categories.

V-tests:
  V-BLOCK-SECRET   -- AWS-key literal
  V-BLOCK-EVAL     -- eval(<dynamic>)
  V-WARN-LENGTH    -- 90-line function
  V-WARN-DOCTRINE-1 -- execSync('python')
  V-WARN-DOCTRINE-2 -- cd <dir> && git status
  V-PASS           -- clean helper diff
  V-SKIP-MVN       -- .java diff (mvn not on PATH)
  V-TIMING         -- 10 FAST runs, p05<2s p95<30s
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVIEWER = HERE / "code_reviewer.py"

PP_ROOT = HERE.parent.parent


def _diff(file_path: str, new_lines: list[str], start_line: int = 1) -> str:
    """Build a minimal unified diff that adds `new_lines` to a new file."""
    hunk_size = len(new_lines)
    header = (
        f"diff --git a/{file_path} b/{file_path}\n"
        f"new file mode 100644\n"
        f"--- /dev/null\n"
        f"+++ b/{file_path}\n"
        f"@@ -0,0 +{start_line},{hunk_size} @@\n"
    )
    body = "\n".join("+" + line for line in new_lines)
    return header + body + "\n"


def run_reviewer(diff_text: str, cwd: Path | None = None) -> tuple[dict, float]:
    cwd = cwd or PP_ROOT
    t0 = time.monotonic()
    proc = subprocess.run(
        [sys.executable, str(REVIEWER), "--fast", "--cwd", str(cwd)],
        input=diff_text.encode("utf-8"),
        capture_output=True,
        timeout=60,
    )
    elapsed = time.monotonic() - t0
    raw = proc.stdout.decode("utf-8", errors="replace")
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        out = {"verdict": "ERROR", "raw": raw,
               "stderr": proc.stderr.decode("utf-8", "replace")}
    return out, elapsed


def main() -> int:
    results = []
    fails = 0

    # V-BLOCK-SECRET: AWS-key literal pattern with valid format.
    diff = _diff("src/leak.py", ['AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'])
    out, _ = run_reviewer(diff)
    ok = out.get("verdict") == "block" and any(
        f.get("category", "").startswith("security-aws")
        for f in out.get("findings", []))
    results.append(("V-BLOCK-SECRET", "block", out.get("verdict"), ok))

    # V-BLOCK-EVAL: dynamic eval.
    diff = _diff("src/danger.py", [
        "def handle(request):",
        "    return eval(request)",
    ])
    out, _ = run_reviewer(diff)
    ok = out.get("verdict") == "block" and any(
        f.get("category") == "security-eval-dynamic"
        for f in out.get("findings", []))
    results.append(("V-BLOCK-EVAL", "block", out.get("verdict"), ok))

    # V-WARN-LENGTH: 90-line function (no doctrine / no security).
    body = ["def big_function():"] + [f"    x_{i} = {i}" for i in range(90)]
    diff = _diff("src/big.py", body)
    out, _ = run_reviewer(diff)
    ok = out.get("verdict") == "warn" and any(
        f.get("category") == "complexity-long-function"
        for f in out.get("findings", []))
    results.append(("V-WARN-LENGTH", "warn", out.get("verdict"), ok))

    # V-WARN-DOCTRINE-1: execSync('python', ...) in a JS file.
    diff = _diff("hooks/bad.js", [
        "const result = execSync('python', ['script.py']);",
    ])
    out, _ = run_reviewer(diff)
    ok = out.get("verdict") == "warn" and any(
        f.get("category") == "doctrine-bare-python-spawn"
        for f in out.get("findings", []))
    results.append(("V-WARN-DOCTRINE-1", "warn", out.get("verdict"), ok))

    # V-WARN-DOCTRINE-2: cd <dir> && git in PS file.
    diff = _diff("scripts/bad.ps1", [
        "cd C:\\Users\\User\\.claude && git status",
    ])
    out, _ = run_reviewer(diff)
    ok = out.get("verdict") == "warn" and any(
        f.get("category") == "doctrine-cd-prefix-git"
        for f in out.get("findings", []))
    results.append(("V-WARN-DOCTRINE-2", "warn", out.get("verdict"), ok))

    # V-PASS: clean diff (small helper, nothing suspicious).
    diff = _diff("src/clean.py", [
        "def add(a, b):",
        "    return a + b",
    ])
    out, _ = run_reviewer(diff)
    ok = out.get("verdict") == "pass" and not out.get("findings")
    results.append(("V-PASS", "pass", out.get("verdict"), ok))

    # V-SKIP-MVN: .java diff (PP repo has no pom.xml, so mvn skip won't
    # fire; we craft a diff against a synthetic cwd that DOES have
    # pom.xml structure. Use the KobiCraft path if it exists, else
    # skip with SKIP-honest.)
    kobicraft_root = Path(
        r"C:\Users\User\Desktop\Cursor Projects\Minecraft Projects"
        r"\KobiiCraft Workspace\KobiiCraft Core Files\KobiCraftServer"
    )
    if kobicraft_root.is_dir():
        diff = _diff("plugins/foo/src/Foo.java", [
            "public class Foo {",
            "    public void bar() {}",
            "}",
        ])
        out, _ = run_reviewer(diff, cwd=kobicraft_root)
        ok = out.get("verdict") == "pass" and any(
            f.get("source_class") == "linter-mvn"
            and f.get("category") == "skip-tool"
            for f in out.get("findings", []))
        results.append(("V-SKIP-MVN", "pass+skip-tool", out.get("verdict"), ok))
    else:
        results.append(("V-SKIP-MVN", "n/a (KobiCraft path absent)", "skipped", True))

    # Print table.
    print(f"{'TEST':24s} {'EXPECTED':24s} {'ACTUAL':12s} {'OK':4s}")
    for tid, exp, act, ok in results:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"{tid:24s} {exp:24s} {act or '-':12s} {mark:4s}")

    # V-TIMING: 10 runs of V-BLOCK-SECRET.
    print("\nV-TIMING: 10 runs (V-BLOCK-SECRET payload)")
    timings = []
    diff = _diff("src/leak.py", ['AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'])
    for _ in range(10):
        _, e = run_reviewer(diff)
        timings.append(int(e * 1000))
    timings.sort()
    p05 = timings[0]
    p50 = timings[len(timings) // 2]
    p95 = timings[-1]
    print(f"  p05={p05}ms  p50={p50}ms  p95={p95}ms  all={timings}")
    timing_ok = p95 < 30000 and p05 < 2000
    if not timing_ok:
        fails += 1
    print(f"  V-TIMING {'PASS' if timing_ok else 'FAIL'}")

    # Persist for audit.
    out_dir = PP_ROOT / "vault" / "reviews"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_v_block.json").write_text(json.dumps({
        "results": [
            {"id": tid, "expected": exp, "actual": act, "ok": ok}
            for tid, exp, act, ok in results
        ],
        "timing": {"p05": p05, "p50": p50, "p95": p95, "all": timings},
    }, indent=2), encoding="utf-8")

    if fails == 0:
        print(f"\nV-BLOCK: ALL {len(results) + 1} TESTS PASSED")
        return 0
    print(f"\nV-BLOCK: {fails} FAILURES (of {len(results) + 1} total)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
