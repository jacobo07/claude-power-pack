#!/usr/bin/env python3
"""TIS observed source -- real model usage read from Claude Code transcripts.

`tis.py` logs an ESTIMATE (chars/4 of the JIT injection, see
jit_skill_loader._tis_log_call). This module reads what the model API
actually reported, from the `message.usage` block of each assistant line
in ~/.claude/projects/<project>/*.jsonl. The two sources are never mixed:
every figure here carries source="observed".

Measured 2026-09-27 on this estate, and the reason for the dedupe below:
the harness writes one transcript line per content block and repeats the
message's usage verbatim on each (381 usage lines = 150 API calls in one
session). Summing lines overcounts ~2.5x. A call is keyed by
(message.id, requestId); the last copy wins.

Three states per session, never collapsed:
  MEASURED       at least one real call with usage
  MEASURED_ZERO  the transcript parsed and holds no real call
  UNMEASURED     the transcript could not be read at all
`<synthetic>` model entries (harness-authored, e.g. limit notices) are not
API calls and are counted separately, never summed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional

PROJECTS_DIR = Path.home() / ".claude" / "projects"
SYNTHETIC_MODEL = "<synthetic>"
USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens",
              "cache_read_input_tokens", "output_tokens")


@dataclass
class SessionUsage:
    session_id: str
    path: str
    state: str = "UNMEASURED"
    source: str = "observed"
    calls: int = 0
    input_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    # Context size of the first real call = startup payload, independent of
    # whether the cache was warm (input + cache_creation + cache_read).
    first_call_context: Optional[int] = None
    # How much of that startup prefix was already cached by an EARLIER session.
    # 2026-09-27 baseline: median 1.9% (sdk-cli) / 16.4% (cli) -- each session
    # re-writes almost its whole prefix, and on sdk-cli that is 80% of spend.
    first_call_cache_read: Optional[int] = None
    entrypoint: Optional[str] = None
    max_call_context: int = 0
    models: dict = field(default_factory=dict)
    usage_lines: int = 0
    synthetic_skipped: int = 0
    bad_lines: int = 0
    subagent_files: int = 0
    subagent_calls: int = 0
    subagent_context_tokens: int = 0
    error: str = ""

    @property
    def context_tokens(self) -> int:
        return (self.input_tokens + self.cache_creation_tokens
                + self.cache_read_tokens)


def _int(v) -> int:
    return v if isinstance(v, int) and v >= 0 else 0


def _calls_in(path: Path) -> tuple[list[dict], int, int, int]:
    """Return (ordered unique real calls, usage_lines, synthetic, bad).

    Each call: {model, usage, ts (ISO str or None), entrypoint}. The
    entrypoint is the session's launch surface -- 'cli' (interactive) or
    'sdk-cli' (claude -p / SDK, the programmatic credit) -- one per file
    across 400 transcripts measured 2026-09-27."""
    calls: dict = {}
    order: list = []
    usage_lines = synthetic = bad = 0
    entrypoint = None
    with open(path, encoding="utf-8-sig") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                bad += 1
                continue
            if isinstance(obj, dict) and entrypoint is None and obj.get("entrypoint"):
                entrypoint = obj["entrypoint"]
            msg = obj.get("message") if isinstance(obj, dict) else None
            if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                continue
            usage_lines += 1
            if msg.get("model") == SYNTHETIC_MODEL:
                synthetic += 1
                continue
            key = (msg.get("id"), obj.get("requestId"))
            if key == (None, None):
                key = ("line", usage_lines)  # no identity: count once as-is
            if key not in calls:
                order.append(key)
            calls[key] = {"model": msg.get("model") or "", "usage": msg["usage"],
                          "ts": obj.get("timestamp"), "key": key}
    ordered = [calls[k] for k in order]
    for c in ordered:
        c["entrypoint"] = entrypoint
    return ordered, usage_lines, synthetic, bad


def calls_from(path: Path, offset: int = 0,
               on_line=None) -> tuple[list[dict], int, Optional[str]]:
    """Incremental twin of _calls_in: real calls in the COMPLETE lines after `offset`.

    Same filters and identity as _calls_in (synthetic skipped, last copy of a
    (message.id, requestId) wins). Returns (calls, end_offset, entrypoint): the
    end offset stops before a trailing line with no newline yet, so a line the
    harness is still writing is read whole on the next pass, never half. An
    identity-less call is keyed by its byte offset, which is stable across passes
    where _calls_in's line counter is not. Used by tools/usage_index.py; the
    agreement of both readers is pinned in tools/test_usage_index.py.

    `on_line(obj, start_offset)` sees every parsed JSON line in file order, so an
    indexer can read ancestry (promptId, origin, quotaLimits) in the same pass."""
    calls: dict = {}
    order: list = []
    entrypoint = None
    pos = offset
    with open(path, "rb") as fh:
        fh.seek(offset)
        for raw in fh:
            if not raw.endswith(b"\n"):
                break
            start, pos = pos, pos + len(raw)
            text = raw.decode("utf-8", errors="replace").lstrip("\ufeff").strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and entrypoint is None and obj.get("entrypoint"):
                entrypoint = obj["entrypoint"]
            if on_line is not None and isinstance(obj, dict):
                on_line(obj, start)
            msg = obj.get("message") if isinstance(obj, dict) else None
            if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                continue
            if msg.get("model") == SYNTHETIC_MODEL:
                continue
            key = (msg.get("id"), obj.get("requestId"))
            if key == (None, None):
                key = ("off", start)
            if key not in calls:
                order.append(key)
            calls[key] = {"model": msg.get("model") or "", "usage": msg["usage"],
                          "ts": obj.get("timestamp"), "key": key}
    return [calls[k] for k in order], pos, entrypoint


def iter_calls(project_dirs: Iterable[Path], include_subagents: bool = True,
               modified_since: Optional[float] = None):
    """Yield every deduplicated real call, subagent calls included, each with
    `ts`, `model`, `usage`, `entrypoint` and `session_id`.

    modified_since (epoch s) skips files whose mtime is older: a transcript not
    written since then cannot hold a call from then. Callers still filter on
    each call's own `ts` -- mtime only prunes, it never admits."""
    for d in project_dirs:
        for p in sorted(Path(d).glob("*.jsonl")):
            paths = [p]
            sub = p.parent / p.stem / "subagents"
            if include_subagents and sub.is_dir():
                paths += sorted(sub.glob("*.jsonl"))
            for fp in paths:
                if modified_since is not None:
                    try:
                        if fp.stat().st_mtime < modified_since:
                            continue
                    except OSError:
                        continue
                try:
                    calls, _, _, _ = _calls_in(fp)
                except OSError:
                    continue
                for c in calls:
                    c["session_id"] = p.stem
                    yield c


def cost_usd(usage: dict, prices: Optional[dict]) -> tuple[Optional[float], bool]:
    """Price one call from a per-MTok price row (vault/pricing schema).

    Returns (usd, ttl_assumed). usd is None when the model has no price --
    unpriced is not free. Cache writes use the 5m/1h breakdown when the usage
    carries one; otherwise all writes are priced as 5m and ttl_assumed=True,
    which UNDER-states cost if any were 1h writes (2x vs 1.25x)."""
    if not prices:
        return None, False
    m = 1_000_000.0
    cc_total = _int(usage.get("cache_creation_input_tokens"))
    br = usage.get("cache_creation")
    if isinstance(br, dict) and ("ephemeral_5m_input_tokens" in br
                                 or "ephemeral_1h_input_tokens" in br):
        w5 = _int(br.get("ephemeral_5m_input_tokens"))
        w1 = _int(br.get("ephemeral_1h_input_tokens"))
        assumed = False
    else:
        w5, w1, assumed = cc_total, 0, cc_total > 0
    usd = (_int(usage.get("input_tokens")) * prices["input"]
           + w5 * prices["cache_write_5m"] + w1 * prices["cache_write_1h"]
           + _int(usage.get("cache_read_input_tokens")) * prices["cache_read"]
           + _int(usage.get("output_tokens")) * prices["output"]) / m
    return usd, assumed


def _context_of(usage: dict) -> int:
    return sum(_int(usage.get(k)) for k in USAGE_KEYS[:3])


def read_session(path: Path, include_subagents: bool = True) -> SessionUsage:
    s = SessionUsage(session_id=path.stem, path=str(path))
    try:
        calls, s.usage_lines, s.synthetic_skipped, s.bad_lines = _calls_in(path)
    except OSError as exc:
        s.error = f"{type(exc).__name__}: {exc}"
        return s
    for c in calls:
        u = c["usage"]
        s.calls += 1
        s.input_tokens += _int(u.get("input_tokens"))
        s.cache_creation_tokens += _int(u.get("cache_creation_input_tokens"))
        s.cache_read_tokens += _int(u.get("cache_read_input_tokens"))
        s.output_tokens += _int(u.get("output_tokens"))
        details = u.get("output_tokens_details")
        if isinstance(details, dict):
            s.thinking_tokens += _int(details.get("thinking_tokens"))
        ctx = _context_of(u)
        if s.first_call_context is None:
            s.first_call_context = ctx
            s.first_call_cache_read = _int(u.get("cache_read_input_tokens"))
            s.entrypoint = c.get("entrypoint")
        s.max_call_context = max(s.max_call_context, ctx)
        s.models[c["model"]] = s.models.get(c["model"], 0) + 1
    s.state = "MEASURED" if s.calls else "MEASURED_ZERO"
    if include_subagents:
        sub_dir = path.parent / path.stem / "subagents"
        if sub_dir.is_dir():
            for sp in sorted(sub_dir.glob("*.jsonl")):
                s.subagent_files += 1
                try:
                    sub_calls, _, _, _ = _calls_in(sp)
                except OSError:
                    continue
                s.subagent_calls += len(sub_calls)
                s.subagent_context_tokens += sum(_context_of(c["usage"])
                                                 for c in sub_calls)
    return s


def scan(project_dirs: Iterable[Path], include_subagents: bool = True) -> list[SessionUsage]:
    out = []
    for d in project_dirs:
        for p in sorted(Path(d).glob("*.jsonl")):
            out.append(read_session(p, include_subagents))
    return out


def _shared_by_entrypoint(measured: list[SessionUsage]) -> dict:
    out: dict = {}
    for s in measured:
        if s.first_call_context:
            out.setdefault(s.entrypoint or "unknown", []).append(
                (s.first_call_cache_read or 0) / s.first_call_context)
    return out


def summarize(sessions: list[SessionUsage]) -> dict:
    measured = [s for s in sessions if s.state == "MEASURED"]
    firsts = [s.first_call_context for s in measured if s.first_call_context]
    by_state: dict = {}
    for s in sessions:
        by_state[s.state] = by_state.get(s.state, 0) + 1

    def tot(attr):
        return sum(getattr(s, attr) for s in measured)
    main_ctx = sum(s.context_tokens for s in measured)
    sub_ctx = tot("subagent_context_tokens")
    return {
        "source": "observed",
        "sessions": len(sessions),
        "by_state": by_state,
        "calls": tot("calls"),
        "subagent_calls": tot("subagent_calls"),
        "context_tokens_main": main_ctx,
        "context_tokens_subagents": sub_ctx,
        "cache_read_tokens": tot("cache_read_tokens"),
        "cache_creation_tokens": tot("cache_creation_tokens"),
        "input_tokens_uncached": tot("input_tokens"),
        "output_tokens": tot("output_tokens"),
        "thinking_tokens": tot("thinking_tokens"),
        "startup_context_median": int(statistics.median(firsts)) if firsts else None,
        "startup_context_min": min(firsts) if firsts else None,
        "startup_context_max": max(firsts) if firsts else None,
        # The startup prefix rides in EVERY call's context (re-read from
        # cache), so its share is first_call_context x calls, not counted
        # once. ESTIMATE: assumes the prefix is unchanged for the whole
        # session, which compaction violates. A once-per-session ratio
        # read 0.32% on the 2026-09-27 baseline where this reads ~50%.
        "startup_prefix_share_estimate": (
            round(sum(s.first_call_context * s.calls for s in measured
                      if s.first_call_context) / main_ctx, 4)
            if main_ctx else None),
        # Share of each session's startup prefix served by a cache an EARLIER
        # session wrote, median per launch surface. Low = the prefix differs
        # between sessions and is re-written every time.
        "startup_shared_share_median": {
            ep: round(statistics.median(v), 4)
            for ep, v in _shared_by_entrypoint(measured).items()},
        "synthetic_skipped": sum(s.synthetic_skipped for s in sessions),
        "bad_lines": sum(s.bad_lines for s in sessions),
        "duplicate_usage_lines_collapsed": sum(
            s.usage_lines - s.calls - s.synthetic_skipped for s in sessions),
    }


def project_key(path: Path) -> str:
    """Claude Code's transcript dir name for a cwd: every non-alphanumeric
    character becomes '-'. Replacing only ':' and separators leaves the '.'
    of '.claude' in place -- and a directory with that wrong name exists on
    this host holding zero transcripts, so the wrong key read as an empty,
    successful measurement (2026-09-27)."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def store_identity(base=None) -> tuple[list[Path], dict[str, str]]:
    """(each transcript store under `base` once, {listed spelling: resolved path}).

    THE producer of store identity; `store_dirs` is its first half. A directory
    junction aliases a project dir (projects/C--Users-User-Apps-mcp-video-analyzer
    -> the PP dir): walked as listed, 152 transcripts were read twice on
    2026-10-02. Identity is the RESOLVED path, so it never depends on listing
    order. A junction to a dir OUTSIDE `base` is a distinct store, kept under its
    resolved path, and its listed spelling is an alias of that path too. The
    alias map is what a path-keyed consumer (usage_index) needs to move rows
    recorded under a link spelling onto the store's identity. This is STORE
    identity: a reader that counts sessions dedupes by session id instead."""
    base = Path(base or PROJECTS_DIR)
    if not base.is_dir():
        return [], {}
    seen: dict[str, Path] = {}
    aliases: dict[str, str] = {}
    for sub in sorted(base.iterdir()):
        if sub.is_dir():
            real = Path(os.path.realpath(sub))
            seen.setdefault(os.path.normcase(str(real)), real)
            if os.path.normcase(str(sub)) != os.path.normcase(str(real)):
                aliases[str(sub)] = str(real)
    return list(seen.values()), aliases


def store_dirs(base=None) -> list[Path]:
    """Each transcript store under `base` once, by resolved path (store_identity)."""
    return store_identity(base)[0]


def _project_dirs(args) -> list[Path]:
    if args.project_dir:
        return [Path(p) for p in args.project_dir]
    if args.all_projects:
        return store_dirs()
    return [PROJECTS_DIR / project_key(Path.cwd().resolve())]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project-dir", action="append",
                    help="transcript dir (repeatable); default = this cwd's project")
    ap.add_argument("--all-projects", action="store_true")
    ap.add_argument("--no-subagents", action="store_true")
    ap.add_argument("--sessions", action="store_true", help="emit per-session rows")
    args = ap.parse_args(argv)
    dirs = _project_dirs(args)
    missing = [str(d) for d in dirs if not d.is_dir()]
    if missing:
        print(json.dumps({"state": "UNMEASURED", "reason": "no transcript dir",
                          "missing": missing}))
        return 2
    sessions = scan(dirs, include_subagents=not args.no_subagents)
    if not sessions:
        # A dir with no transcripts is a failed look, not a quiet project.
        print(json.dumps({"state": "UNMEASURED", "reason": "no transcripts in dir",
                          "project_dirs": [str(d) for d in dirs]}))
        return 2
    out = {"summary": summarize(sessions),
           "project_dirs": [str(d) for d in dirs]}
    if args.sessions:
        out["sessions"] = [dict(asdict(s), context_tokens=s.context_tokens)
                           for s in sessions]
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
