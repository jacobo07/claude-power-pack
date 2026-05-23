"""Auto-Testing orchestrator — detect, generate, run, report.

Spec ref: vault/specs/auto-testing-gate.md §8

Two modes:

- fast (default, invoked by the PreToolUse gate hook): 1 LLM call,
  1 happy-path test, 30s hard wall-clock budget.
- deep (invoked by /auto-test): up to 3 tests including edge cases,
  no hard budget cap (the Owner is interactively waiting).

CLI:
  python auto_test.py --gate --cwd <root> [--mode fast|deep]
  -> writes one JSON object to stdout describing the verdict.

The verdict is one of {pass, fail, ceiling, timeout, skip}. The gate
hook (D1) translates this:
  pass     -> exit 0 + result artifact
  fail     -> exit 2 + result artifact + failure ledger row
  ceiling  -> exit 0 + warn-line in .auto-spawned.log
  timeout  -> exit 0 + warn-line in .auto-spawned.log
  skip     -> exit 0 (diff has no testable file changes)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Local imports must work both as a package (`python -m
# modules.auto-testing.auto_test`) and as a script. We rely on
# importlib because the dash in "auto-testing" forbids the package
# form anyway.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "generators"))

import detectors  # noqa: E402
import llm_bridge  # noqa: E402
import vault_io  # noqa: E402
from generators import _common as gen_common  # noqa: E402
from generators import python_gen, node_gen, java_gen  # noqa: E402


GATE_BUDGET_SEC = 30
DEEP_BUDGET_SEC = 120


@dataclass
class GateVerdict:
    verdict: str           # pass | fail | ceiling | timeout | skip
    project_type: str
    project_root: Optional[str]
    reason: str
    test_files: list[str] = field(default_factory=list)
    test_output: str = ""
    duration_sec: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        d = {
            "verdict": self.verdict,
            "project_type": self.project_type,
            "project_root": self.project_root,
            "reason": self.reason,
            "test_files": self.test_files,
            "test_output": self.test_output[:4096],
            "duration_sec": round(self.duration_sec, 2),
            "extra": self.extra,
        }
        return json.dumps(d, ensure_ascii=False)


def _read_staged_diff(cwd: Path) -> str:
    """Run `git diff --cached` and return stdout. Empty string on
    any failure (no git, not a repo, etc.)."""
    git = "git"
    if os.name == "nt":
        for candidate in (r"C:\Program Files\Git\cmd\git.exe",
                          r"C:\Program Files (x86)\Git\cmd\git.exe"):
            if Path(candidate).exists():
                git = candidate
                break
    try:
        r = subprocess.run(
            [git, "-C", str(cwd), "diff", "--cached"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace",
        )
        return r.stdout or ""
    except (subprocess.TimeoutExpired, OSError):
        return ""


def _pick_generator(det: detectors.Detection,
                     diff_files: list[str]) -> tuple[str, Any, dict[str, Any]]:
    """Choose a generator + run-time kwargs based on detection + diff.

    Returns (lang_tag, generator_module, runner_kwargs). Defers
    Java's build-system kwarg here so java_gen.generate() receives
    the right `build_system`.
    """
    t = det.type
    if t == detectors.ProjectType.PYTHON:
        return "python", python_gen, {}
    if t in (detectors.ProjectType.NODE_VITEST,
             detectors.ProjectType.NODE_JEST,
             detectors.ProjectType.NODE_MOCHA):
        return "node", node_gen, {}
    if t == detectors.ProjectType.NODE_GENERIC:
        return "node", node_gen, {}  # gate will ceiling on missing test script
    if t == detectors.ProjectType.JAVA_MAVEN:
        return "java", java_gen, {"build_system": "maven"}
    if t == detectors.ProjectType.JAVA_GRADLE:
        return "java", java_gen, {"build_system": "gradle"}
    return "unknown", None, {}


def _run_pytest(test_path: Path, project_root: Path,
                 timeout: int) -> tuple[int, str]:
    """Run pytest on a single test file. Returns (exit_code, output)."""
    py = sys.executable or "python"
    try:
        r = subprocess.run(
            [py, "-m", "pytest", str(test_path), "-v", "--no-header",
             "-p", "no:cacheprovider"],
            cwd=str(project_root),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return 124, str(out) + "\n[TIMEOUT after " + str(timeout) + "s]"
    except OSError as e:
        return 127, "pytest subprocess error: " + str(e)


def _run_vitest_or_jest(test_path: Path, project_root: Path,
                          variant: str, timeout: int) -> tuple[int, str]:
    cmd_map = {
        "vitest": ["npx", "vitest", "run", str(test_path), "--no-coverage"],
        "jest": ["npx", "jest", str(test_path), "--no-coverage"],
        "mocha": ["npx", "mocha", str(test_path)],
    }
    cmd = cmd_map.get(variant)
    if not cmd:
        return 126, "no runner for variant " + variant
    try:
        r = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            shell=(os.name == "nt"),
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "[TIMEOUT after " + str(timeout) + "s]"
    except OSError as e:
        return 127, "node subprocess error: " + str(e)


def _run_mvn_test(test_class: str, project_root: Path,
                   timeout: int) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["mvn", "test", "-Dtest=" + test_class, "-q"],
            cwd=str(project_root),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            shell=(os.name == "nt"),
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "[TIMEOUT after " + str(timeout) + "s]"
    except OSError as e:
        return 127, "mvn subprocess error: " + str(e)


def _run_test(lang: str, det: detectors.Detection, test_path: Path,
               project_root: Path, timeout: int) -> tuple[int, str]:
    if lang == "python":
        return _run_pytest(test_path, project_root, timeout)
    if lang == "node":
        variant = det.type.value.split("_")[-1] if det.type.value.startswith("node_") else "vitest"
        if variant == "generic":
            variant = "vitest"
        return _run_vitest_or_jest(test_path, project_root, variant, timeout)
    if lang == "java":
        # Maven test class name from file: strip Test.java -> class.
        class_name = test_path.stem  # e.g. "CalculatorTest"
        return _run_mvn_test(class_name, project_root, timeout)
    return 126, "no runner for lang " + lang


def run_gate(cwd: Path, diff: str, mode: str = "fast",
             budget_sec: Optional[int] = None) -> GateVerdict:
    """Single-shot gate evaluation.

    Args:
        cwd: project working directory (commit happens here).
        diff: `git diff --cached` content. If empty, returns skip.
        mode: 'fast' (1 test) or 'deep' (multi-test, no budget cap).
        budget_sec: total wall-clock budget. Defaults to
                    GATE_BUDGET_SEC (fast) or DEEP_BUDGET_SEC (deep).
    """
    t_start = time.monotonic()
    if budget_sec is None:
        budget_sec = GATE_BUDGET_SEC if mode == "fast" else DEEP_BUDGET_SEC

    det = detectors.detect_project_type(cwd)
    project_root_str = str(det.project_root) if det.project_root else str(cwd)

    if det.is_ceiling():
        return GateVerdict(
            verdict="ceiling",
            project_type=det.type.value,
            project_root=project_root_str,
            reason="CEILING: " + det.reason
                    + (" (framework binary missing)"
                       if not det.framework_binary_available else ""),
            duration_sec=time.monotonic() - t_start,
        )

    if not diff.strip():
        return GateVerdict(
            verdict="skip",
            project_type=det.type.value,
            project_root=project_root_str,
            reason="no staged diff",
            duration_sec=time.monotonic() - t_start,
        )

    if len(diff) > 8192:
        return GateVerdict(
            verdict="ceiling",
            project_type=det.type.value,
            project_root=project_root_str,
            reason="diff exceeds 8 KB; run /auto-test for deep sweep",
            duration_sec=time.monotonic() - t_start,
        )

    lang, gen_module, gen_kwargs = _pick_generator(det, [])
    if gen_module is None:
        return GateVerdict(
            verdict="ceiling",
            project_type=det.type.value,
            project_root=project_root_str,
            reason="no generator for project type " + det.type.value,
            duration_sec=time.monotonic() - t_start,
        )

    project_root = det.project_root or cwd
    gen_res = gen_module.generate(diff, project_root, llm_bridge.call_llm,
                                   **gen_kwargs)
    if not gen_res.ok:
        # No test could be generated. Treat as ceiling (we cannot
        # honestly evaluate the commit), allow it through.
        return GateVerdict(
            verdict="ceiling",
            project_type=det.type.value,
            project_root=project_root_str,
            reason="generator: " + gen_res.reason,
            duration_sec=time.monotonic() - t_start,
            extra={"llm_text": gen_res.llm_text[:1000]},
        )

    elapsed = time.monotonic() - t_start
    remaining = max(1, int(budget_sec - elapsed))

    test_case = gen_res.tests[0]
    test_path = vault_io.write_test_file(
        project_root, test_case.filename, test_case.content,
    )

    # Java test class name must match filename. Strip the timestamp +
    # slug prefix that we use for uniqueness.
    if lang == "java":
        # File looks like 2026-05-23_153624_calculatorTest.java
        # mvn -Dtest needs the class name, but it's wrapped in a unique
        # filename. For real Maven runs, the class name should equal
        # the file stem. Honor that here.
        stem = test_path.stem
        # If the LLM emitted `class CalculatorTest`, use that.
        import re as _re
        m = _re.search(r"\bclass\s+(\w+)", test_case.content)
        class_name = m.group(1) if m else stem
        exit_code, output = _run_mvn_test(class_name, project_root, remaining)
    else:
        exit_code, output = _run_test(lang, det, test_path, project_root,
                                       remaining)

    duration = time.monotonic() - t_start

    if exit_code == 124:
        return GateVerdict(
            verdict="timeout",
            project_type=det.type.value,
            project_root=project_root_str,
            reason="test runner exceeded " + str(remaining) + "s",
            test_files=[str(test_path)],
            test_output=output,
            duration_sec=duration,
        )

    if exit_code == 0:
        return GateVerdict(
            verdict="pass",
            project_type=det.type.value,
            project_root=project_root_str,
            reason="generated test passed",
            test_files=[str(test_path)],
            test_output=output,
            duration_sec=duration,
        )

    return GateVerdict(
        verdict="fail",
        project_type=det.type.value,
        project_root=project_root_str,
        reason="generated test failed (exit " + str(exit_code) + ")",
        test_files=[str(test_path)],
        test_output=output,
        duration_sec=duration,
        extra={
            "test_text_sha256": vault_io._sha256_short(test_case.content),
            "target_file": test_case.target_file,
        },
    )


def _opt_out_active() -> bool:
    return os.environ.get("CLAUDEPP_AUTOTEST_DISABLE") == "1"


def _maybe_fake_sleep() -> None:
    """Debug helper: when CLAUDEPP_AUTOTEST_FAKE_SLEEP_SEC=N is set,
    sleep N seconds before any real work. Used by D2 done-gate to
    prove the hook-side 28s budget guard kills slow runners."""
    n = os.environ.get("CLAUDEPP_AUTOTEST_FAKE_SLEEP_SEC")
    if n:
        try:
            time.sleep(float(n))
        except (ValueError, OSError):
            pass


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Auto-Testing gate / deep run")
    p.add_argument("--gate", action="store_true",
                   help="emit one JSON object to stdout for the hook")
    p.add_argument("--cwd", default=os.getcwd(),
                   help="project working directory (default: cwd)")
    p.add_argument("--mode", choices=["fast", "deep"], default="fast")
    p.add_argument("--budget", type=int, default=None,
                   help="override wall-clock budget in seconds")
    p.add_argument("--diff", default=None,
                   help="path to a diff file (default: git diff --cached)")
    args = p.parse_args(argv)

    # Recursion guard for the subprocess chain (claude.exe inside the
    # generator runs its own Stop hooks).
    if os.environ.get("CLAUDEPP_AUTOTEST_RUNNING") == "1" and args.gate:
        verdict = GateVerdict(
            verdict="skip",
            project_type="unknown",
            project_root=args.cwd,
            reason="recursion-guard: nested gate invocation",
        )
        if args.gate:
            print(verdict.to_json())
        return 0

    if _opt_out_active() and args.gate:
        vault_io.log_auto_spawn({
            "verdict": "skipped-by-env",
            "cwd": args.cwd,
            "mode": args.mode,
        })
        verdict = GateVerdict(
            verdict="skip",
            project_type="unknown",
            project_root=args.cwd,
            reason="opt-out via CLAUDEPP_AUTOTEST_DISABLE=1",
        )
        print(verdict.to_json())
        return 0

    _maybe_fake_sleep()

    cwd = Path(args.cwd).resolve()
    if args.diff:
        diff_text = Path(args.diff).read_text(encoding="utf-8-sig")
    else:
        diff_text = _read_staged_diff(cwd)

    verdict = run_gate(cwd, diff_text, mode=args.mode, budget_sec=args.budget)

    # Side-effect log + result artifact.
    vault_io.log_auto_spawn({
        "verdict": verdict.verdict,
        "project_type": verdict.project_type,
        "project_root": verdict.project_root,
        "duration_sec": verdict.duration_sec,
        "reason": verdict.reason[:200],
    })

    if verdict.verdict in ("pass", "fail", "timeout"):
        # Only write a full artifact when we ran a real test.
        body = "## Test output\n\n```\n" + verdict.test_output[:8000] + "\n```\n"
        if verdict.test_files:
            body = ("## Test file\n\n`" + verdict.test_files[0] + "`\n\n" + body)
        vault_io.write_result_artifact(
            Path(verdict.project_root or args.cwd),
            verdict.verdict,
            verdict.reason,
            body,
            extra={"project_type": verdict.project_type},
        )

    if verdict.verdict == "fail":
        # Closed-loop ledger row.
        target = verdict.extra.get("target_file", "")
        # Re-read the test file we just wrote to capture content.
        try:
            test_text = Path(verdict.test_files[0]).read_text(encoding="utf-8")
        except (OSError, IndexError):
            test_text = ""
        vault_io.write_failure(
            Path(verdict.project_root or args.cwd),
            target_file=target,
            test_text=test_text,
            failure_output=verdict.test_output,
            diff_excerpt=diff_text[:2048],
        )

    print(verdict.to_json())
    # Exit codes: 0 for everything except hard FAIL, which is 2.
    return 2 if verdict.verdict == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
