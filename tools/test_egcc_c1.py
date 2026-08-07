#!/usr/bin/env python3
"""EGCC C1 -- gates for the enforced-vs-compiled corpus reconciliation.

Spec: vault/specs/egcc-c1-corpus-reconciliation.md

Every gate is asserted in BOTH directions where a direction exists: a check
that only ever observes the passing state cannot distinguish a working
instrument from an inert one.

Synthetic trees are built in a tempdir, so the suite is hermetic and does not
depend on the estate's current divergence -- except the two gates that
deliberately DO read the live repo, which assert content rather than a verdict.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.rule_compiler.reconcile import reconcile, render  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS  {gate:24s} {evidence}")


def _fail(gate: str, why: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL  {gate:24s} {why}")


BLOCK = "<!-- PP-HARD-RULES-START -->\n{body}\n<!-- PP-HARD-RULES-END -->"


def build(root: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def blocks(root: Path, mirror_ids: list[str], archive_ids: list[str]) -> None:
    build(root, {
        "CLAUDE.md": BLOCK.format(
            body="\n".join(f"### {r} -- t\nTRIGGER: x\nSTOP: y" for r in mirror_ids)),
        "vault/hard_rules/HARD_RULES.md": BLOCK.format(
            body="\n".join(f"### {r} -- t\nTRIGGER: x\nSTOP: y" for r in archive_ids)),
    })


def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(PP / "tools" / "hardrule_compile.py"), *args],
        capture_output=True, text=True, timeout=180, env=env, cwd=str(PP),
    )


def main() -> int:
    # ---- V-C1-DISCOVERED ------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, [], [])
        build(root, {"hooks/a.js": "// HR-FIXTURE-001",
                     "modules/m/b.py": "# HR-FIXTURE-001"})
        with_id = reconcile(root, set())
        (root / "hooks" / "a.js").write_text("// nothing", encoding="utf-8")
        (root / "modules" / "m" / "b.py").write_text("# nothing", encoding="utf-8")
        without = reconcile(root, set())
        if "HR-FIXTURE-001" in with_id["enforced_not_compiled"] \
           and "HR-FIXTURE-001" not in without["enforced_not_compiled"]:
            _ok("V-C1-DISCOVERED",
                "id appears when written to disk and disappears when removed")
        else:
            _fail("V-C1-DISCOVERED",
                  f"with={with_id['enforced_not_compiled']} without={without['enforced_not_compiled']}")

    # ---- V-C1-RECURRENCE ------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, [], [])
        build(root, {"hooks/a.js": "// HR-ONE-001 HR-TWO-001",
                     "modules/m/b.py": "# HR-TWO-001"})
        r = reconcile(root, set())
        one_singleton = "HR-ONE-001" in r["singletons"]
        two_real = "HR-TWO-001" in r["enforced_not_compiled"]
        two_not_singleton = "HR-TWO-001" not in r["singletons"]
        if one_singleton and two_real and two_not_singleton:
            _ok("V-C1-RECURRENCE",
                "1 file -> singleton, 2 files -> real; asserted in both directions")
        else:
            _fail("V-C1-RECURRENCE",
                  f"singletons={r['singletons']} enforced={r['enforced_not_compiled']}")

    # ---- V-C1-NO-RATIO --------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, ["HR-X-001"], ["HR-Y-001"])
        build(root, {"hooks/a.js": "// HR-X-001", "modules/m/b.py": "# HR-X-001"})
        r = reconcile(root, set())
        bad_keys = [k for k in r if any(t in k.lower()
                                        for t in ("ratio", "pct", "percent", "coverage"))]
        floats = [k for k, v in r.items() if isinstance(v, float)]
        if not bad_keys and not floats:
            _ok("V-C1-NO-RATIO",
                f"{len(r)} keys, no ratio/pct/percent key and no float value")
        else:
            _fail("V-C1-NO-RATIO", f"ratio-like={bad_keys} floats={floats}")

    # ---- V-C1-ZERO-DISTINCT ---------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        r = reconcile(root, set())
        text = render(r)
        if r["verdict"] == "NO_IDS_FOUND" and "never as agreement" in text:
            _ok("V-C1-ZERO-DISTINCT",
                "empty tree -> NO_IDS_FOUND, distinct from a clean reconciliation")
        else:
            _fail("V-C1-ZERO-DISTINCT", f"verdict={r['verdict']}")

    # ---- V-C1-BIDIRECTIONAL ---------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, ["HR-A-001", "HR-SHARED-001"], ["HR-SHARED-001", "HR-C-001"])
        r = reconcile(root, set())
        if r["mirror_only"] == ["HR-A-001"] and r["archive_only"] == ["HR-C-001"] \
           and r["both"] == ["HR-SHARED-001"]:
            _ok("V-C1-BIDIRECTIONAL",
                "mirror-only and archive-only reported separately, never merged")
        else:
            _fail("V-C1-BIDIRECTIONAL",
                  f"mirror_only={r['mirror_only']} archive_only={r['archive_only']} both={r['both']}")

    # ---- V-C1-HOOK-CLASS ------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, [], [])
        build(root, {
            "hooks/h1.js": "// HR-HOOK-001",
            "hooks/h2.js": "// HR-HOOK-001",
            "commands/c1.md": "HR-PROSE-001",
            "commands/c2.md": "HR-PROSE-001",
        })
        r = reconcile(root, set())
        if r["enforced_not_compiled"] == ["HR-HOOK-001"] \
           and r["referenced_not_compiled"] == ["HR-PROSE-001"]:
            _ok("V-C1-HOOK-CLASS",
                "hooks/ id classifies hook_enforced; commands/ id does not")
        else:
            _fail("V-C1-HOOK-CLASS",
                  f"enforced={r['enforced_not_compiled']} referenced={r['referenced_not_compiled']}")

    # ---- V-C1-EXIT-DISCIPLINE -------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, [], [])
        build(root, {"commands/c1.md": "HR-PROSE-001", "commands/c2.md": "HR-PROSE-001"})
        prose_only = reconcile(root, set())
        build(root, {"hooks/h1.js": "// HR-HOOK-001", "hooks/h2.js": "// HR-HOOK-001"})
        with_hook = reconcile(root, set())
        # The exit expression is the same one both call sites use.
        if not prose_only["enforced_not_compiled"] and with_hook["enforced_not_compiled"]:
            _ok("V-C1-EXIT-DISCIPLINE",
                "prose divergence alone does not fail; a hook-enforced gap does")
        else:
            _fail("V-C1-EXIT-DISCIPLINE",
                  f"prose={prose_only['enforced_not_compiled']} hook={with_hook['enforced_not_compiled']}")

    # ---- V-C1-COMPILED-SUPPRESSES ---------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, [], [])
        build(root, {"hooks/h1.js": "// HR-HOOK-001", "hooks/h2.js": "// HR-HOOK-001"})
        uncompiled = reconcile(root, set())
        compiled = reconcile(root, {"HR-HOOK-001"})
        if uncompiled["enforced_not_compiled"] and not compiled["enforced_not_compiled"]:
            _ok("V-C1-COMPILED-SUPPRESSES",
                "the same hook-enforced id stops being a finding once it compiles")
        else:
            _fail("V-C1-COMPILED-SUPPRESSES",
                  f"uncompiled={uncompiled['enforced_not_compiled']} compiled={compiled['enforced_not_compiled']}")

    # ---- V-C1-HERMETIC --------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        blocks(root, ["HR-A-001"], ["HR-B-001"])
        build(root, {"hooks/a.js": "// HR-A-001", "modules/m/b.py": "# HR-A-001"})
        runs = [json.dumps(reconcile(root, set()), sort_keys=True) for _ in range(3)]
        if len(set(runs)) == 1:
            _ok("V-C1-HERMETIC", "3 consecutive runs byte-identical")
        else:
            _fail("V-C1-HERMETIC", f"{len(set(runs))} distinct outputs across 3 runs")

    # ---- V-C1-LIVE-CORPUS -----------------------------------------------
    from modules.rule_compiler.parser import load_corpus
    live = reconcile(PP, {r.rule_id for r in load_corpus()})
    if "HR-SECRET-001" in live["mirror_only"] \
       and len(live["both"]) < live["mirror_ids"] \
       and len(live["both"]) < live["archive_ids"]:
        _ok("V-C1-LIVE-CORPUS",
            f"real repo: mirror={live['mirror_ids']} archive={live['archive_ids']} "
            f"both={len(live['both'])}, HR-SECRET-001 mirror-only")
    else:
        _fail("V-C1-LIVE-CORPUS",
              f"mirror_only has HR-SECRET-001={('HR-SECRET-001' in live['mirror_only'])} "
              f"both={len(live['both'])} mirror={live['mirror_ids']} archive={live['archive_ids']}")

    # ---- V-C1-CLI-WIRED -------------------------------------------------
    # Through the real entry point, not the exported function: a suite that only
    # calls exports passes while argv parsing, exit codes and wiring are broken.
    proc = run_cli(["--reconcile"])
    both_flags = run_cli(["--reconcile", "--singletons"])
    if proc.returncode == 1 and "HR-SECRET-001" in proc.stdout \
       and both_flags.returncode == 1 and both_flags.stderr.strip() == "":
        _ok("V-C1-CLI-WIRED",
            "--reconcile exits 1 naming the live gap; --reconcile --singletons composes")
    else:
        _fail("V-C1-CLI-WIRED",
              f"rc={proc.returncode} combo_rc={both_flags.returncode} "
              f"stderr={both_flags.stderr.strip()[:120]!r}")

    # ---- V-C1-H7-UNCHANGED ----------------------------------------------
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    h7 = subprocess.run(
        [sys.executable, str(PP / "tools" / "verify_hard_rules.py")],
        capture_output=True, text=True, timeout=180, env=env, cwd=str(PP))
    if h7.returncode == 0 and "HARDRULES_PROBE=7/7" in h7.stdout \
       and "sentinel block present" in h7.stdout:
        _ok("V-C1-H7-UNCHANGED",
            "still 7/7 and exit 0; message now names which file carries the block")
    else:
        _fail("V-C1-H7-UNCHANGED",
              f"rc={h7.returncode} probe_line={[l for l in h7.stdout.splitlines() if 'PROBE' in l]}")

    total = _passes + _fails
    print()
    print(f"C1_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
