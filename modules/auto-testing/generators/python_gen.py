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


_SYSTEM = (
    "You generate pytest test scaffolds. You output ONLY Python source "
    "code, no preamble, no markdown fences, no commentary. Every "
    "generated test function name starts with `test_`. Every test "
    "contains at least one `assert` statement. You match the import "
    "style and assertion idiom shown in the example tests you are "
    "given. If you cannot generate a real callable test for the diff "
    "(e.g. the diff has no Python functions, only comments or "
    "renames), output the single line `# NO_TEST_POSSIBLE: <reason>`."
)


def _build_prompt(diff: str, existing_tests: list[tuple[str, str]],
                  target_files: list[str]) -> str:
    parts: list[str] = []
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


def _validate_python_test(text: str) -> tuple[bool, str]:
    """Verify the LLM returned a real callable test."""
    if "NO_TEST_POSSIBLE" in text:
        idx = text.find("NO_TEST_POSSIBLE")
        return False, text[idx:idx + 200].strip()
    if "def test_" not in text:
        return False, "no `def test_` function found in LLM output"
    if "assert" not in text:
        return False, "no `assert` statement found in LLM output"
    return True, ""


def generate(diff: str, project_root: Path, call_llm) -> GenerationResult:
    """Generate one pytest happy-path test from a staged Python diff.

    Args:
        diff: output of `git diff --cached`.
        project_root: absolute Path to the project root.
        call_llm: the call_llm callable from llm_bridge (injected so
                  this module stays free of cross-package coupling
                  in tests).
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

    user_prompt = _build_prompt(diff, existing, target_files)
    res: "LLMResult" = call_llm(_SYSTEM, user_prompt, timeout=25)

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

    valid, reason = _validate_python_test(text)
    if not valid:
        return GenerationResult(
            ok=False,
            reason=reason,
            duration_sec=time.monotonic() - t0,
            llm_text=text,
        )

    slug_seed = Path(target_files[0]).stem
    test = TestCase(
        filename=ts_slug() + "_" + slugify(slug_seed) + ".test.py",
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
