"""Node (vitest / jest) test scaffold generator.

Spec ref: vault/specs/auto-testing-gate.md §7

Reads up to 3 existing test files (`*.test.{js,ts}` /
`*.spec.{js,ts}`) to infer framework (vitest vs jest, ESM vs CJS,
TS vs JS) and asks the LLM for ONE happy-path test per modified
JS/TS file in the diff.

Output validation: the generated test MUST contain `describe(`,
`it(` or `test(`, and `expect(` — the shared idiom for vitest and
jest. If any is missing, returns ok=False and the gate ceiling-
allows the commit.
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
    "You generate vitest or jest test scaffolds. You output ONLY "
    "JavaScript or TypeScript source code, no preamble, no markdown "
    "fences, no commentary. You inspect the example tests provided to "
    "decide between vitest and jest (look at the imports: "
    "`from 'vitest'` => vitest; `@jest/globals` or no framework "
    "import => jest). Every generated test uses `describe(...)`, "
    "`it(...)` or `test(...)`, and `expect(...).to...(...)`. If you "
    "cannot generate a real callable test for the diff, output the "
    "single line `// NO_TEST_POSSIBLE: <reason>`."
)


_NODE_EXTS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")


def _build_prompt(diff: str, existing_tests: list[tuple[str, str]],
                  target_files: list[str]) -> str:
    parts: list[str] = []
    parts.append("Staged JS/TS diff to generate ONE happy-path test for:")
    parts.append("```diff")
    parts.append(truncate_diff(diff))
    parts.append("```")
    if existing_tests:
        parts.append("")
        parts.append("Existing tests from this project (framework + style reference):")
        for relpath, content in existing_tests:
            parts.append("```ts")
            parts.append("// " + relpath)
            parts.append(content)
            parts.append("```")
    if target_files:
        parts.append("")
        parts.append("Target source file(s) being tested: " + ", ".join(target_files))
    parts.append("")
    parts.append(
        "Output ONLY the test file contents. Start with the necessary "
        "imports (matching the example tests' framework). End with the "
        "last `})`. No explanations, no markdown fences."
    )
    return "\n".join(parts)


def _validate_node_test(text: str) -> tuple[bool, str]:
    if "NO_TEST_POSSIBLE" in text:
        idx = text.find("NO_TEST_POSSIBLE")
        return False, text[idx:idx + 200].strip()
    if "describe(" not in text:
        return False, "no `describe(` block found in LLM output"
    if "it(" not in text and "test(" not in text:
        return False, "no `it(` or `test(` block found in LLM output"
    if "expect(" not in text:
        return False, "no `expect(` assertion found in LLM output"
    return True, ""


def _pick_extension(target_file: str, existing_tests: list[tuple[str, str]]) -> str:
    """Mirror the project's primary test extension."""
    if target_file.endswith((".ts", ".tsx")):
        return ".test.ts"
    if target_file.endswith((".jsx",)):
        return ".test.jsx"
    if existing_tests:
        first = existing_tests[0][0]
        if first.endswith(".test.ts") or first.endswith(".spec.ts"):
            return ".test.ts"
    return ".test.js"


def generate(diff: str, project_root: Path, call_llm) -> GenerationResult:
    t0 = time.monotonic()
    target_files = parse_diff_files(diff, _NODE_EXTS)
    if not target_files:
        return GenerationResult(
            ok=False,
            reason="diff has no JS/TS files",
            duration_sec=time.monotonic() - t0,
        )

    existing = read_existing_tests(
        project_root,
        ("*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js"),
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

    text = res.text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    valid, reason = _validate_node_test(text)
    if not valid:
        return GenerationResult(
            ok=False,
            reason=reason,
            duration_sec=time.monotonic() - t0,
            llm_text=text,
        )

    ext = _pick_extension(target_files[0], existing)
    slug_seed = Path(target_files[0]).stem
    test = TestCase(
        filename=ts_slug() + "_" + slugify(slug_seed) + ext,
        content=text + "\n",
        target_file=target_files[0],
        notes="node_gen vitest/jest scaffold; " + str(len(existing)) + " style refs",
    )
    return GenerationResult(
        ok=True,
        tests=[test],
        duration_sec=time.monotonic() - t0,
        llm_text=text,
    )
