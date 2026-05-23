"""Java JUnit 5 test scaffold generator — ceiling-honest.

Spec ref: vault/specs/auto-testing-gate.md §7

The Java generator differs from the Python and Node generators in
one important way: even a syntactically perfect JUnit 5 class is
useless without a build system to execute it. KobiCraft on this
host (136 .java files, 0 tests, no pom.xml, no build.gradle) is the
canonical test case for that ceiling.

Posture:
  - If `build_system` is None (caller could not detect Maven/Gradle):
    return ok=False with reason "no build system; JUnit cannot
    execute even if generated". The upstream gate ceiling-allows.
  - If `build_system` is `maven` or `gradle`: generate the JUnit 5
    scaffold normally.

Validation: the LLM output MUST contain `@Test` and at least one
`assert` (assertEquals / assertTrue / assertNotNull / etc.).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

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
    "You generate JUnit 5 test scaffolds. You output ONLY Java source "
    "code, no preamble, no markdown fences, no commentary. Every "
    "generated test method carries the `@Test` annotation. Every test "
    "uses at least one JUnit 5 assertion (`assertEquals`, "
    "`assertTrue`, `assertNotNull`, `assertThrows`, etc.). Match the "
    "package declaration and import style of the example tests if "
    "provided. If you cannot generate a real callable test for the "
    "diff (e.g. the diff only modifies comments), output the single "
    "line `// NO_TEST_POSSIBLE: <reason>`."
)


def _build_prompt(diff: str, existing_tests: list[tuple[str, str]],
                  target_files: list[str], build_system: str) -> str:
    parts: list[str] = []
    parts.append("Staged Java diff to generate ONE happy-path "
                 "JUnit 5 test for:")
    parts.append("```diff")
    parts.append(truncate_diff(diff))
    parts.append("```")
    parts.append("")
    parts.append("Build system: " + build_system + ". Generated test "
                 "will be placed under src/test/java/ and run via the "
                 "project's standard test target.")
    if existing_tests:
        parts.append("")
        parts.append("Existing tests from this project (style "
                     "reference):")
        for relpath, content in existing_tests:
            parts.append("```java")
            parts.append("// " + relpath)
            parts.append(content)
            parts.append("```")
    if target_files:
        parts.append("")
        parts.append("Target source file(s): " + ", ".join(target_files))
    parts.append("")
    parts.append(
        "Output ONLY the test class. Start with `package` if the "
        "example tests have one (mirror the package). Use static "
        "imports for assertions: "
        "`import static org.junit.jupiter.api.Assertions.*;`."
    )
    return "\n".join(parts)


_ASSERTION_KEYWORDS = (
    "assertEquals", "assertTrue", "assertFalse", "assertNull",
    "assertNotNull", "assertThrows", "assertSame", "assertNotSame",
    "assertArrayEquals", "assertAll", "assertDoesNotThrow",
    "assertIterableEquals", "assertLinesMatch", "assertTimeout",
)


def _validate_java_test(text: str) -> tuple[bool, str]:
    if "NO_TEST_POSSIBLE" in text:
        idx = text.find("NO_TEST_POSSIBLE")
        return False, text[idx:idx + 200].strip()
    if "@Test" not in text:
        return False, "no `@Test` annotation found in LLM output"
    if not any(kw in text for kw in _ASSERTION_KEYWORDS):
        return (
            False,
            "no JUnit 5 assertion (assertEquals/assertTrue/...) "
            "found in LLM output",
        )
    return True, ""


def generate(diff: str, project_root: Path, call_llm,
             build_system: Optional[str] = None) -> GenerationResult:
    """Generate one JUnit 5 test from a staged Java diff.

    Args:
        diff: `git diff --cached` output.
        project_root: project root (used to find existing tests).
        call_llm: injected callable from llm_bridge.
        build_system: 'maven' or 'gradle'. None => CEILING.

    Reality contract: with no build system, a generated test is an
    inert artifact (cannot be executed). The function refuses to
    generate in that case.
    """
    t0 = time.monotonic()
    target_files = parse_diff_files(diff, (".java",))
    if not target_files:
        return GenerationResult(
            ok=False,
            reason="diff has no .java files",
            duration_sec=time.monotonic() - t0,
        )

    if build_system not in ("maven", "gradle"):
        return GenerationResult(
            ok=False,
            reason=(
                "CEILING: no build system detected at project root; "
                "JUnit 5 cannot execute even if generated. Add a "
                "pom.xml or build.gradle to enable the Java gate."
            ),
            duration_sec=time.monotonic() - t0,
        )

    existing = read_existing_tests(
        project_root,
        ("*Test.java", "*Tests.java"),
        limit=3,
        max_bytes=3000,
    )

    user_prompt = _build_prompt(diff, existing, target_files, build_system)
    res: "LLMResult" = call_llm(_SYSTEM, user_prompt, timeout=25)

    if not res.ok:
        return GenerationResult(
            ok=False,
            reason="LLM call failed: " + res.error,
            duration_sec=time.monotonic() - t0,
        )

    text = res.text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    valid, reason = _validate_java_test(text)
    if not valid:
        return GenerationResult(
            ok=False,
            reason=reason,
            duration_sec=time.monotonic() - t0,
            llm_text=text,
        )

    slug_seed = Path(target_files[0]).stem
    # Java class names must match filename, start with letter, no dots.
    cap = slug_seed.title().replace("_", "").replace("-", "")
    ts_safe = ts_slug().replace("-", "").replace("_", "")
    test = TestCase(
        filename="Auto" + cap + ts_safe + "Test.java",
        content=text + "\n",
        target_file=target_files[0],
        notes=("java_gen JUnit5 scaffold (" + build_system + "); "
               + str(len(existing)) + " style refs"),
    )
    return GenerationResult(
        ok=True,
        tests=[test],
        duration_sec=time.monotonic() - t0,
        llm_text=text,
    )
