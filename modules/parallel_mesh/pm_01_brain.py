#!/usr/bin/env python3
"""pm_01_brain.py -- PM-01: Repo Shared Brain.

The largest duplicated cognition is "understand this repo again." A second pane
opening the same repo re-reads CLAUDE.md, re-greps the modules, and rebuilds the
mental model the first pane already built. PM-01 makes that derivation happen
ONCE per repo (per time window) and be consumed by every pane, so N panes pay the
context-building cost of one.

Parent CO-04 (memory.py): the Brain is a WARM-tier artifact (indexed, instantly
recoverable, ~zero context cost, full trust) -- one per repo. This module does
not invent a tier; it defines a specific occupant of CO-04's WARM tier.

Honest (CO-10): the Brain is a FILE ON DISK (repo_brain_<slug>.md) polled at pane
boundaries, not shared memory. It is a CACHE of understanding, never the source of
truth: a pane acting on a specific file still verifies against live source
(HR-PREMISE-001). Fail-open ABSOLUTE: any error -> behave as if no brain exists
(the pane cold-reads the repo -- the safe direction, never a stale-trust).

Storage: ~/.claude/state/parallel_mesh/repo_brain_<slug>.md
Header:  <!-- pm01-brain {"repo":..,"generated_ts":..,"head":..,"tokens":N} -->
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cognitive_os import memory as _mem  # noqa: E402  (WARM-tier lineage)

DEFAULT_TTL_MIN = 60.0
DEFAULT_MAX_TOKENS = 2000
BRAIN_TIER = _mem.WARM  # a Repo Brain lives in CO-04's WARM tier

_HEADER_RE = re.compile(r"^<!--\s*pm01-brain\s*(\{.*\})\s*-->\s*$")


def _slug(repo: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", repo or "")


def _default_state_dir() -> Path:
    return Path.home() / ".claude" / "state" / "parallel_mesh"


def estimate_tokens(text: str) -> int:
    return int(len(str(text).split()) * 1.33)


def _parse_iso(s):
    if not isinstance(s, str) or not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


@dataclass
class Brain:
    repo: str
    generated_ts: str
    head: str = ""          # repo HEAD commit at generation (freshness anchor)
    tokens: int = 0
    content: str = ""       # the briefing


def git_head(repo: str) -> str | None:
    """Current HEAD sha of a repo, or None (fail-open). Tries PATH `git`, then the
    known Windows install path. Best-effort: staleness falls back to TTL on None."""
    exe = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    try:
        out = subprocess.run([exe, "-C", repo, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        sha = (out.stdout or "").strip()
        return sha or None
    except (OSError, subprocess.SubprocessError):
        return None


class RepoBrainGenerator:
    """Builds the repo briefing ONCE. `scan_fn` is the expensive repo read (the
    thing PM-01 exists to run only once); it is injected so this stays pure and
    testable. Output is truncated to a token budget so the Brain never becomes its
    own context cost."""

    def __init__(self, *, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max_tokens

    def generate(self, repo: str, scan_fn, *, head: str | None = None,
                 now: datetime | None = None) -> Brain:
        now = now or datetime.now(timezone.utc)
        content = str(scan_fn() or "")
        if estimate_tokens(content) > self.max_tokens:
            # Budget-bound: keep the head of the briefing (structure/decisions come
            # first by convention), mark the truncation honestly.
            words = content.split()
            keep = int(self.max_tokens / 1.33)
            content = " ".join(words[:keep]) + "\n\n[brain truncated to budget]"
        return Brain(repo=repo, generated_ts=now.isoformat(), head=head or "",
                     tokens=estimate_tokens(content), content=content)


class BrainStore:
    """Disk persistence for the per-repo Brain (single .md with a JSON header)."""

    def __init__(self, state_dir=None):
        self.state_dir = Path(state_dir) if state_dir else _default_state_dir()

    def path_for(self, repo: str) -> Path:
        return self.state_dir / f"repo_brain_{_slug(repo)}.md"

    def save(self, brain: Brain) -> bool:
        """Best-effort write. Single-writer-by-anchor: a full rewrite tagged with
        HEAD+ts (not in-place mutation). Fail-open -> False."""
        try:
            p = self.path_for(brain.repo)
            p.parent.mkdir(parents=True, exist_ok=True)
            header = json.dumps({"repo": brain.repo,
                                 "generated_ts": brain.generated_ts,
                                 "head": brain.head, "tokens": brain.tokens},
                                ensure_ascii=False)
            p.write_text(f"<!-- pm01-brain {header} -->\n{brain.content}",
                         encoding="utf-8")
            return True
        except OSError:
            return False

    def load(self, repo: str) -> Brain | None:
        """Read the Brain, or None if absent/corrupt (fail-open)."""
        p = self.path_for(repo)
        if not p.is_file():
            return None
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        lines = text.split("\n", 1)
        m = _HEADER_RE.match(lines[0]) if lines else None
        if not m:
            return None
        try:
            meta = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            return None
        content = lines[1] if len(lines) > 1 else ""
        return Brain(repo=str(meta.get("repo", repo)),
                     generated_ts=str(meta.get("generated_ts", "")),
                     head=str(meta.get("head", "")),
                     tokens=int(meta.get("tokens", 0) or 0),
                     content=content)


def is_stale(brain: Brain, *, now: datetime | None = None,
             ttl_min: float = DEFAULT_TTL_MIN, current_head: str | None = None) -> bool:
    """Stale iff older than ttl_min OR a new commit landed since generation.
    Fail-open: an unknown current_head falls back to TTL only (never crashes)."""
    now = now or datetime.now(timezone.utc)
    gen = _parse_iso(brain.generated_ts)
    if gen is None:
        return True
    age_min = (now - gen).total_seconds() / 60.0
    if age_min > ttl_min:
        return True
    if current_head and brain.head and current_head != brain.head:
        return True
    return False


class RepoBrainConsumer:
    """Consume-before-cold-read. A pane calls get_or_generate BEFORE reading the
    repo directly: a valid non-stale Brain is consumed (scan_fn NOT called); a
    missing/stale Brain is (re)generated once, then consumed."""

    def __init__(self, *, store: BrainStore | None = None,
                 generator: RepoBrainGenerator | None = None,
                 head_fn=git_head):
        self.store = store or BrainStore()
        self.generator = generator or RepoBrainGenerator()
        self.head_fn = head_fn

    def get_or_generate(self, repo: str, scan_fn, *, now: datetime | None = None,
                        current_head: str | None = None,
                        ttl_min: float = DEFAULT_TTL_MIN):
        """Returns (Brain, generated: bool). generated=False means an existing
        fresh Brain was consumed with NO repo scan. Fail-open: on any error, fall
        through to a fresh generation (cold-read equivalent)."""
        now = now or datetime.now(timezone.utc)
        head = current_head if current_head is not None else (
            self.head_fn(repo) if self.head_fn else None)
        try:
            existing = self.store.load(repo)
            if existing and not is_stale(existing, now=now, ttl_min=ttl_min,
                                         current_head=head):
                return (existing, False)
        except Exception:  # noqa: BLE001 -- fail-open to regeneration
            pass
        brain = self.generator.generate(repo, scan_fn, head=head, now=now)
        self.store.save(brain)
        return (brain, True)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--repo", default=None)
    ap.add_argument("--show", action="store_true",
                    help="print the current brain (does not generate)")
    ap.add_argument("--head", action="store_true", help="print repo HEAD")
    args = ap.parse_args(argv)
    repo = args.repo or os.getcwd()
    if args.head:
        print(git_head(repo) or "(unknown)")
        return 0
    b = BrainStore().load(repo)
    if b is None:
        print(f"# no brain for {repo} (would generate on first consume)")
    else:
        fresh = "stale" if is_stale(b, current_head=git_head(repo)) else "fresh"
        print(f"# brain {repo} [{fresh}] head={b.head[:8]} tokens={b.tokens}\n")
        print(b.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
