"""Mission cost circuit breaker (TOK-18 gen 2 D1).

A mission's budget was cycles and hours only (`gsd_mission.budget_exhausted`), so nothing saw tokens:
E1 (m-f011d7fdebc9) was estimated at 17M processed tokens and ran to 141M, 93 % Opus, before anything
stopped it. This module gives a mission an optional token envelope, measured deterministically from
its own transcripts. No model reads anything here.

Unit: processed tokens = input + cache_write + cache_read + output, deduplicated by message id within
a transcript, synthetic rows excluded, counted from the mission's `created_at`.

`judge` trips on either of two conditions, and the caller parks the mission with the existing
owner_hold (held, not halted, not renewed):
  * spend over `token_trip_ratio` x `token_estimate` (default ratio 2.0: E1 would have tripped at 34M);
  * burn without progress: more than `token_stall_budget` (default half the estimate) spent since the
    last change of the work tree's progress fingerprint.
A mission without `token_estimate` is never judged. An unmeasurable spend (no transcript directory)
is UNKNOWN and never trips: absence is not zero.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

DEFAULT_TRIP_RATIO = 2.0
DEFAULT_STALL_FRACTION = 0.5
_UK = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def projects_root() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return Path(base) / "projects"


def encode_cwd(path: str) -> str:
    """Claude Code's transcript directory name for a working directory."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def mission_dirs(work_dir: str, root: Path) -> list[Path]:
    """The project directory of `work_dir` plus its nested worktrees (`<enc>--claude-worktrees-...`).
    A sibling that merely shares the prefix (`...-e1` vs `...-e10`) is not included."""
    enc = encode_cwd(work_dir)
    if not root.is_dir():
        return []
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and (d.name == enc or d.name.startswith(enc + "--")))


def _file_tokens(path: Path, since_iso: str | None) -> int:
    seen, total = set(), 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = r.get("message") or {}
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            if since_iso and (r.get("timestamp") or "") < since_iso:
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            total += sum(int(u.get(k) or 0) for k in _UK)
    return total


def processed_tokens(rec: dict, root: Path | None = None, cache: dict | None = None) -> int | None:
    """Processed tokens the mission has spent, or None when no transcript directory exists.
    `cache` maps a file path to {size, mtime, tokens}; unchanged files are not re-read."""
    root = root or projects_root()
    # Both planes: the host files a worker's transcript under the dir it was LAUNCHED in (cwd), while the
    # work may live in a worktree (work_dir). Measured 2026-10-06, m-e935055d072d: work_dir alone found no
    # directory, so a 3,353,877-token worker read as unmeasurable and its breaker was blind.
    dirs: list[Path] = []
    for base in (rec.get("work_dir"), rec.get("cwd")):
        for d in (mission_dirs(base, root) if base else []):
            if d not in dirs:
                dirs.append(d)
    if not dirs:
        return None
    since = None
    if rec.get("created_at"):
        import datetime as dt
        since = dt.datetime.fromtimestamp(float(rec["created_at"]), dt.timezone.utc).isoformat()[:19]
    total = 0
    for d in dirs:
        for p in d.rglob("*.jsonl"):
            st = p.stat()
            key = str(p)
            hit = cache.get(key) if cache is not None else None
            if hit and hit.get("size") == st.st_size and hit.get("mtime") == st.st_mtime and hit.get("since") == since:
                total += hit["tokens"]
                continue
            n = _file_tokens(p, since)
            if cache is not None:
                cache[key] = {"size": st.st_size, "mtime": st.st_mtime, "since": since, "tokens": n}
            total += n
    return total


def judge(rec: dict, spent: int | None, fp: str | None) -> dict:
    """{trip: reason|None, mark: new cost_mark|None}. Pure."""
    est = rec.get("token_estimate")
    if not est or spent is None:
        return {"trip": None, "mark": None}
    est = int(est)
    ratio = float(rec.get("token_trip_ratio") or DEFAULT_TRIP_RATIO)
    if spent > ratio * est:
        return {"trip": (f"cost breaker: processed {spent:,} > {ratio:g} x estimate {est:,}; "
                         "explain the variance and recompute the remaining work before release"),
                "mark": None}
    mark = rec.get("cost_mark") or {}
    if fp is None:
        return {"trip": None, "mark": None}
    if mark.get("fp") != fp:
        return {"trip": None, "mark": {"fp": fp, "tokens": spent}}
    stall = int(rec.get("token_stall_budget") or est * DEFAULT_STALL_FRACTION)
    burned = spent - int(mark.get("tokens") or 0)
    if burned > stall:
        return {"trip": (f"cost breaker: {burned:,} processed since the work tree last changed "
                         f"(stall budget {stall:,}); semantic progress is not keeping up with spend"),
                "mark": None}
    return {"trip": None, "mark": None}
