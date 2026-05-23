#!/usr/bin/env python3
"""research_discovery.py — SessionStart auto-discovery for deep-research.

Spec: claude-power-pack/vault/specs/deep-research-agent.md §8
Plan: claude-power-pack/vault/plans/deep-research-agent-2026-05-23.md Paso 3.2

Standalone library — no side effects on import. The Stop-hook /
SessionStart-hook callers (a small wiring layer in learning-sentinel.js
or similar — Wave-5b) decide how to surface the discovery payload.

Discovery contract (matches spec §8):
  * Read vault/research/index.json (JSONL).
  * Filter to entries written within RECENT_WINDOW_HOURS (default 24).
  * Of those, keep entries whose `prompt` contains tokens that match the
    current cwd's basename OR any top-level filename (case-insensitive,
    word-boundary).
  * Return the most recent matching entry as the "research-ready" payload
    for the SessionStart compound-proposal slot.

Why this is a separate module, not inline in learning-sentinel.js:
  * Reusable across Stop and SessionStart wiring.
  * Independently testable (the function returns a value; no hook
    contract entanglement).
  * If the wiring drifts, the discovery logic stays canonical.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, TypedDict


HOME = Path.home()
PP_REPO = HOME / ".claude" / "skills" / "claude-power-pack"
INDEX_PATH = PP_REPO / "vault" / "research" / "index.json"

RECENT_WINDOW_HOURS = 24
MIN_TOKEN_LEN = 3  # too-short tokens match too much


class DiscoveryHit(TypedDict):
    ts: str
    slug: str
    prompt: str
    report_path: str
    age_hours: float
    matched_tokens: list[str]


def _load_index() -> list[dict[str, Any]]:
    if not INDEX_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with INDEX_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows


def _parse_iso(ts: str) -> float | None:
    """Parse an ISO-8601 'Z' timestamp into a POSIX-seconds float.
    Returns None on parse failure."""
    if not ts:
        return None
    try:
        # 2026-05-23T12:44:45Z -> handle Z suffix manually.
        if ts.endswith("Z"):
            ts = ts[:-1]
        # time.strptime is locale-sensitive; use a known format.
        tup = time.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        return time.mktime(tup) - time.timezone
    except (ValueError, OSError):
        return None


_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")
_STOP_WORDS = {
    "the", "and", "for", "src", "lib", "bin", "doc", "docs", "tmp", "test",
    "tests", "build", "dist", "node_modules", "target", "out", "log", "logs",
    "config", "cache", "tmp", "temp", "cursor", "projects", "workspace",
    "claude", "skills", "user", "users", "appdata", "local", "programs",
}


def _split_tokens(text: str) -> set[str]:
    """Break `text` into lowercased alpha-num tokens, drop stop words +
    short tokens. Used for both cwd derivation AND prompt matching."""
    if not text:
        return set()
    parts = _TOKEN_SPLIT_RE.split(text.lower())
    return {
        p for p in parts
        if len(p) >= MIN_TOKEN_LEN
        and p not in _STOP_WORDS
        and not p.isdigit()  # year tokens like "2026" pollute matches
    }


def _cwd_tokens(cwd: Path) -> set[str]:
    """Build the match-token set for `cwd`:
      * basename of cwd  (split on non-alnum, stop words dropped)
      * parent dir basename (catches "Minecraft Projects" wrapping a
        non-minecraft inner dir)
      * top-level dir + file names inside cwd (one level, no recursion)
    Stop-words ("workspace", "projects", "src", "build", ...) are dropped
    so they don't match every prompt indiscriminately.
    """
    tokens: set[str] = set()
    tokens |= _split_tokens(cwd.name)
    # Parent dir name (widens matching for nested projects like
    # "Minecraft Projects/KobiiCraft Workspace")
    if cwd.parent != cwd:
        tokens |= _split_tokens(cwd.parent.name)
    try:
        for entry in cwd.iterdir():
            stem = entry.name.split(".", 1)[0]
            tokens |= _split_tokens(stem)
    except OSError:
        pass
    return tokens


def _prompt_matches(prompt: str, tokens: set[str]) -> list[str]:
    """Return the subset of tokens that appear in `prompt` as whole words."""
    if not tokens or not prompt:
        return []
    lower = prompt.lower()
    matched: list[str] = []
    for tok in tokens:
        # Word-boundary match. Escape tok in case it has regex specials
        # (won't happen given _cwd_tokens's filter, but defensive).
        if re.search(rf"\b{re.escape(tok)}\b", lower):
            matched.append(tok)
    return matched


def discover_for_cwd(
    cwd: Path | str | None = None,
    window_hours: int = RECENT_WINDOW_HOURS,
) -> DiscoveryHit | None:
    """Return the most-recent research entry that's relevant to `cwd`.

    Returns None if no entry matches (the common case — the SessionStart
    proposal slot stays empty).
    """
    cwd_path = Path(cwd) if cwd else Path.cwd()
    if not cwd_path.is_dir():
        return None

    tokens = _cwd_tokens(cwd_path)
    if not tokens:
        return None

    rows = _load_index()
    if not rows:
        return None

    now = time.time()
    window_s = window_hours * 3600
    candidates: list[tuple[float, dict[str, Any], list[str]]] = []
    for r in rows:
        ts = _parse_iso(r.get("ts", ""))
        if ts is None or (now - ts) > window_s:
            continue
        matched = _prompt_matches(r.get("prompt", ""), tokens)
        if not matched:
            continue
        candidates.append((ts, r, matched))

    if not candidates:
        return None

    # Most-recent first.
    candidates.sort(key=lambda c: -c[0])
    ts, row, matched = candidates[0]
    age_hours = (now - ts) / 3600
    return {
        "ts": row.get("ts", ""),
        "slug": row.get("slug", ""),
        "prompt": row.get("prompt", ""),
        "report_path": row.get("report_path", ""),
        "age_hours": round(age_hours, 1),
        "matched_tokens": matched,
    }


def render_proposal_line(hit: DiscoveryHit) -> str:
    """Format a one-liner for the SessionStart compound-proposal slot."""
    return (
        f"RESEARCH READY: {hit['slug']} "
        f"(age {hit['age_hours']} h, matched: "
        f"{', '.join(hit['matched_tokens'][:3])}) -> {hit['report_path']}"
    )


def main(argv: list[str]) -> int:
    """CLI mode for empirical testing + future hook wiring.

    Usage:
      python research_discovery.py                  # discover in $cwd
      python research_discovery.py --cwd <path>     # discover for path
      python research_discovery.py --window 168     # 7-day window
    """
    cwd = None
    window = RECENT_WINDOW_HOURS
    i = 0
    while i < len(argv):
        if argv[i] == "--cwd" and i + 1 < len(argv):
            cwd = argv[i + 1]; i += 2
        elif argv[i] == "--window" and i + 1 < len(argv):
            try: window = int(argv[i + 1])
            except ValueError: pass
            i += 2
        else:
            i += 1
    hit = discover_for_cwd(cwd, window_hours=window)
    if hit is None:
        print(json.dumps({"verdict": "no-recent-relevant-research",
                           "cwd": str(Path(cwd) if cwd else Path.cwd()),
                           "window_hours": window}))
        return 0
    print(json.dumps(hit, indent=2))
    print(file=sys.stderr)
    print(render_proposal_line(hit), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
