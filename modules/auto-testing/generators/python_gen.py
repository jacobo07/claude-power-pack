"""Python pytest scaffold generator.

Spec ref: vault/specs/auto-testing-gate.md §7

Reads up to 3 existing test files (test_*.py / *_test.py) to infer
the project's style (assertion library, fixture conventions, import
roots), then asks the LLM for ONE happy-path test per modified Python
file in the diff.

Output validation: each generated test MUST contain a `def test_`
function and at least one `assert` statement, or the result is
flagged ok=False. The runner upstream translates ok=False to CEILING
(generator returned no usable test) and ALLOWS the commit.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from ._common import (
    GenerationResult,
    TestCase,
    parse_diff_files,
    read_existing_tests,
    slugify,
    truncate_diff,
    ts_slug,
)

if TYPE_CHECKING:
    from ..llm_bridge import LLMResult


_SYSTEM_FAST = (
    "You generate pytest test scaffolds. You output ONLY Python source "
    "code, no preamble, no markdown fences, no commentary. Every "
    "generated test function name starts with `test_`. Every test "
    "contains at least one `assert` statement. You match the import "
    "style and assertion idiom shown in the example tests you are "
    "given. If you cannot generate a real callable test for the diff "
    "(e.g. the diff has no Python functions, only comments or "
    "renames), output the single line `# NO_TEST_POSSIBLE: <reason>`."
)

_SYSTEM_DEEP = (
    "You generate pytest test scaffolds (DEEP mode). You output ONLY "
    "Python source code, no preamble, no markdown fences, no "
    "commentary. You generate AT LEAST THREE distinct test functions: "
    "one happy path, and two edge cases (typical edges: empty input, "
    "boundary value, None / 0, negative value, type mismatch). Every "
    "test function name starts with `test_`. Every test contains at "
    "least one `assert` statement. You match the import style and "
    "assertion idiom shown in the example tests you are given. If "
    "you cannot generate THREE real callable tests for the diff, "
    "output the single line `# NO_TEST_POSSIBLE: <reason>`."
)


def _build_prompt(diff: str, existing_tests: list[tuple[str, str]],
                  target_files: list[str], mode: str = "fast") -> str:
    parts: list[str] = []
    if mode == "deep":
        parts.append("Staged Python diff to generate THREE tests for "
                     "(1 happy path + 2 edge cases):")
    else:
        parts.append("Staged Python diff to generate ONE happy-path test for:")
    parts.append("```diff")
    parts.append(truncate_diff(diff))
    parts.append("```")
    if existing_tests:
        parts.append("")
        parts.append("Existing tests from this project (style reference):")
        for relpath, content in existing_tests:
            parts.append("```python")
            parts.append("# " + relpath)
            parts.append(content)
            parts.append("```")
    if target_files:
        parts.append("")
        parts.append("Target source file(s) being tested: " + ", ".join(target_files))
    parts.append("")
    parts.append(
        "Output ONLY the test file contents. Start with `import pytest` "
        "or your project's convention. End with the last assert. No "
        "explanations, no markdown."
    )
    return "\n".join(parts)


def _validate_python_test(text: str, mode: str = "fast") -> tuple[bool, str]:
    """Verify the LLM returned real callable tests.

    Fast mode requires >=1 `def test_` + >=1 `assert`.
    Deep mode requires >=3 `def test_` (matching the multi-test
    prompt).
    """
    if "NO_TEST_POSSIBLE" in text:
        idx = text.find("NO_TEST_POSSIBLE")
        return False, text[idx:idx + 200].strip()
    test_count = text.count("def test_")
    if test_count < 1:
        return False, "no `def test_` function found in LLM output"
    if mode == "deep" and test_count < 3:
        return False, ("deep mode wants >=3 tests, got " + str(test_count))
    if "assert" not in text:
        return False, "no `assert` statement found in LLM output"
    return True, ""


def generate(diff: str, project_root: Path, call_llm,
             mode: str = "fast") -> GenerationResult:
    """Generate pytest tests from a staged Python diff.

    Args:
        diff: output of `git diff --cached`.
        project_root: absolute Path to the project root.
        call_llm: the call_llm callable from llm_bridge (injected so
                  this module stays free of cross-package coupling
                  in tests).
        mode: 'fast' (1 happy-path test, 25 s timeout) or 'deep'
              (>=3 tests with edge cases, 60 s timeout).
    """
    t0 = time.monotonic()
    target_files = parse_diff_files(diff, (".py",))
    if not target_files:
        return GenerationResult(
            ok=False,
            reason="diff has no .py files",
            duration_sec=time.monotonic() - t0,
        )

    existing = read_existing_tests(
        project_root,
        ("test_*.py", "*_test.py"),
        limit=3,
        max_bytes=3000,
    )

    user_prompt = _build_prompt(diff, existing, target_files, mode=mode)
    system_prompt = _SYSTEM_DEEP if mode == "deep" else _SYSTEM_FAST
    llm_timeout = 60 if mode == "deep" else 25
    res: "LLMResult" = call_llm(system_prompt, user_prompt, timeout=llm_timeout)

    if not res.ok:
        return GenerationResult(
            ok=False,
            reason="LLM call failed: " + res.error,
            duration_sec=time.monotonic() - t0,
            llm_text="",
        )

    text = res.text
    # Strip surrounding code fences if the LLM still emitted them.
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    valid, reason = _validate_python_test(text, mode=mode)
    if not valid:
        return GenerationResult(
            ok=False,
            reason=reason,
            duration_sec=time.monotonic() - t0,
            llm_text=text,
        )

    slug_seed = Path(target_files[0]).stem
    # Filename must be a valid Python module name (starts with letter,
    # no embedded dots) for pytest discovery. Empirically caught E2
    # done-gate first-run: `2026-05-23_153216_calc.test.py` was
    # rejected by pytest collector with ModuleNotFoundError.
    ts_safe = ts_slug().replace("-", "").replace("_", "")
    test = TestCase(
        filename="test_auto_" + slugify(slug_seed) + "_" + ts_safe + ".py",
        content=text + "\n",
        target_file=target_files[0],
        notes="python_gen pytest scaffold; " + str(len(existing)) + " style refs",
    )
    return GenerationResult(
        ok=True,
        tests=[test],
        duration_sec=time.monotonic() - t0,
        llm_text=text,
    )
