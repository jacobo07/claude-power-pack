#!/usr/bin/env python3
"""
test_mistake_frequency_xplat.py -- MC-OVO-34-V cross-platform parity test.

Exercises the full mistake-frequency ingestion round-trip against a temp
ledger on the current host. Designed to produce identical output on Windows
and Linux so we can prove parity once the same script runs on the VPS.

Run:
    python tests/test_mistake_frequency_xplat.py

Exits 0 on full pass, non-zero on any assertion failure.
Emits a compact PARITY receipt line the Owner can diff between hosts.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TOOL = REPO / "tools" / "mistake_frequency.py"


def run(args: list[str], ledger: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["MISTAKE_FREQUENCY_LEDGER"] = str(ledger)
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def assert_eq(label: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(label: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{label}: false" + (f" -- {detail}" if detail else ""))


def main() -> int:
    if not TOOL.exists():
        print(f"FAIL: tool missing at {TOOL}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="mf_xplat_") as tmp:
        ledger = Path(tmp) / "mistake-frequency.json"

        # 1. --show on empty ledger -> empty entries, valid schema
        res = run(["--show"], ledger)
        assert_eq("show exit", res.returncode, 0)
        data = json.loads(res.stdout)
        assert_eq("schema", data["schema"], "mistake-frequency-v1")
        assert_eq("entries empty", data["entries"], {})

        # 2. --increment M16 -> count=1, project recorded
        res = run(["--increment", "M16", "--project", "xplat-test"], ledger)
        assert_eq("inc1 exit", res.returncode, 0)
        assert_true("inc1 stdout has count=1", "count=1" in res.stdout, res.stdout)

        # 3. --increment M16 twice more -> count=3 (crosses threshold)
        run(["--increment", "M16", "--project", "xplat-test"], ledger)
        res = run(["--increment", "M16", "--project", "xplat-test"], ledger)
        assert_true("inc3 count=3", "count=3" in res.stdout, res.stdout)

        # 4. --top 5 -> M16 surfaces since count>=threshold(3)
        res = run(["--top", "5"], ledger)
        assert_eq("top exit", res.returncode, 0)
        assert_true("top shows M16", "M16" in res.stdout, res.stdout)
        assert_true("top shows count=3", "count=3" in res.stdout, res.stdout)
        assert_true("top shows project", "xplat-test" in res.stdout, res.stdout)

        # 5. --increment with invalid id -> exit 1
        res = run(["--increment", "NotAnId"], ledger)
        assert_eq("bad-id exit", res.returncode, 1)

        # 6. --validate -> exit 0, OK line
        res = run(["--validate"], ledger)
        assert_eq("validate exit", res.returncode, 0)
        assert_true("validate OK", res.stdout.startswith("OK"), res.stdout)

        # 7. --reset M16 -> removed
        res = run(["--reset", "M16"], ledger)
        assert_eq("reset exit", res.returncode, 0)
        res = run(["--show"], ledger)
        data = json.loads(res.stdout)
        assert_eq("entries empty after reset", data["entries"], {})

        # 8. Ledger file byte-level sanity: no BOM, trailing newline, indent=2
        raw = ledger.read_bytes()
        assert_true("no BOM", not raw.startswith(b"\xef\xbb\xbf"))
        assert_true("trailing newline", raw.endswith(b"\n"))
        assert_true("indent=2", b'\n  "schema"' in raw)

    # Parity receipt -- Owner diffs this line between Windows and Linux runs
    print(
        "PARITY host={host} py={py} platform={plat} tool_sha={sha} tests=8 status=PASS".format(
            host=platform.node(),
            py=sys.version.split()[0],
            plat=platform.system().lower(),
            sha=_short_sha(TOOL),
        )
    )
    return 0


def _short_sha(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as err:
        print(f"FAIL: {err}", file=sys.stderr)
        sys.exit(1)
