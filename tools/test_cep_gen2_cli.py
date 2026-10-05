"""Regression: tools/cep_gen2.py accepts a leading `--` on its mode (selftest/final/status).
Before the fix `--selftest` fell through to the final check and printed CEP2_VERDICT, not CEP2_SELFTEST."""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "cep_gen2.py"
FIX = 'sys.argv[1].lstrip("-")'


def run(script: Path, arg: str) -> str:
    p = subprocess.run([sys.executable, str(script), arg], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    return p.stdout


def main() -> int:
    fails = []
    for arg in ("--selftest", "selftest"):
        out = run(SRC, arg)
        if "CEP2_SELFTEST=" not in out:
            fails.append(f"{arg}: CEP2_SELFTEST missing")
        if "CEP2_VERDICT" in out:
            fails.append(f"{arg}: CEP2_VERDICT must not print")
    body = SRC.read_text(encoding="utf-8")
    if FIX not in body:
        fails.append("fix text not found in cep_gen2.py (mutant cannot be built)")
    else:
        with tempfile.TemporaryDirectory() as d:
            mut = Path(d) / "cep_gen2.py"
            mut.write_text(body.replace(FIX, "sys.argv[1]"), encoding="utf-8")
            out = run(mut, "--selftest")
            if "CEP2_VERDICT" not in out or "CEP2_SELFTEST=" in out:
                fails.append("mutant (raw flag) was not detected: the test cannot see the defect")
    for f in fails:
        print("  FAIL", f)
    print(f"CEP2_CLI_TEST={'PASS' if not fails else 'FAIL'} (2 positive, 1 mutant)")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())