"""Shared helpers for per-language test generators.

Spec ref: vault/specs/auto-testing-gate.md §7
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestCase:
    """One generated test, ready to write to disk."""
    filename: str       # relative to project's tests/auto-generated/
    content: str        # full file contents
    target_file: str    # the source file the test exercises (relative)
    notes: str = ""     # one-line provenance


@dataclass
class GenerationResult:
    ok: bool
    tests: list[TestCase] = field(default_factory=list)
    reason: str = ""    # populated when ok=False
    duration_sec: float = 0.0
    llm_text: str = ""  # raw LLM output for forensic debugging


def ts_slug() -> str:
    return time.strftime("%Y-%m-%d_%H%M%S", time.localtime())


_SLUG_BAD = re.compile(r"[^a-z0-9\-]+")


def slugify(s: str, maxlen: int = 48) -> str:
    s = s.strip().lower()
    s = _SLUG_BAD.sub("-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:maxlen] or "test"


def parse_diff_files(diff: str, ext_filter: tuple[str, ...]) -> list[str]:
    """Extract file paths from `git diff --cached` output.

    Returns paths matching any of `ext_filter` (e.g. (".py",) or
    (".js", ".ts")). Honors `+++ b/<path>` lines for added/modified
    files; ignores `--- /dev/null` deletions.
    """
    out: list[str] = []
    for line in diff.splitlines():
        if not line.startswith("+++ b/"):
            continue
        path = line[6:].strip()
        if path == "/dev/null":
            continue
        if any(path.endswith(ext) for ext in ext_filter):
            out.append(path)
    return out


def read_existing_tests(project_root: Path,
                        glob_patterns: tuple[str, ...],
                        limit: int = 3,
                        max_bytes: int = 4096) -> list[tuple[str, str]]:
    """Read up to `limit` existing test files for style inference.

    Returns list of (relpath, content) tuples. Each content is
    truncated to `max_bytes` to keep the LLM prompt bounded.
    """
    out: list[tuple[str, str]] = []
    seen: set[Path] = set()
    for pat in glob_patterns:
        for p in project_root.rglob(pat):
            if not p.is_file():
                continue
            try:
                if p.stat().st_size > max_bytes * 4:
                    continue
            except OSError:
                continue
            if p in seen:
                continue
            seen.add(p)
            try:
                txt = p.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            rel = p.relative_to(project_root).as_posix()
            out.append((rel, txt[:max_bytes]))
            if len(out) >= limit:
                return out
    return out


def truncate_diff(diff: str, max_chars: int = 6000) -> str:
    """Bound the diff fed to the LLM so the prompt fits in 8 KB total.

    Hard cap from the Win argv lesson is 8 KB; we route via STDIN so
    the cap doesn't apply mechanically, but a too-large prompt makes
    the LLM slow + the response noisy. 6 KB of diff + ~2 KB of
    context = a ~8 KB prompt, which empirically lands in ~17-30s.
    """
    if len(diff) <= max_chars:
        return diff
    head = diff[: max_chars // 2]
    tail = diff[-max_chars // 2 :]
    return head + "\n\n[... truncated " + str(len(diff) - max_chars) + " chars ...]\n\n" + tail
