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
    work_dir = rec.get("work_dir") or rec.get("cwd")
    if not work_dir:
        return None
    dirs = mission_dirs(work_dir, root)
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


# --- Session scope (W1, 2026-10-05) -------------------------------------------------------------
# A mission is not the only thing that burns: an ordinary interactive session ran 131 calls to
# 35.45M processed with nothing measuring it (skyparty-spawn closeout, transcript b9dbdfe2).
# A session declares an envelope in `session-budget-<sid>.json`; hooks/session_budget_guard.js
# enforces it on PreToolUse with the SAME unit as above, read incrementally. This side owns the
# declaration and the reference count the guard is parity-tested against.

_SID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
DEFAULT_CALL_RATIO = 1.5
DEFAULT_NOPROGRESS_CALLS = 25


def state_dir() -> Path:
    return Path(os.environ.get("GSD_LONG_RUN_STATE_DIR")
                or os.path.join(os.path.expanduser("~"), ".claude", "state"))


def budget_path(sid: str) -> Path:
    if not _SID_RE.match(sid or ""):
        raise ValueError(f"invalid session id: {sid!r}")
    return state_dir() / f"session-budget-{sid}.json"


def session_tokens(transcript: Path, since_iso: str | None = None) -> dict:
    """Reference count for one transcript: processed tokens (same rule as _file_tokens), tool_use
    blocks, and the context size of the last counted assistant message."""
    seen, total, calls, ctx = set(), 0, 0, 0
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            if since_iso and (r.get("timestamp") or "") < since_iso:
                continue
            m = r.get("message") or {}
            if not isinstance(m, dict):
                continue
            if r.get("type") == "assistant" and isinstance(m.get("content"), list):
                calls += sum(1 for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_use")
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            total += sum(int(u.get(k) or 0) for k in _UK)
            ctx = sum(int(u.get(k) or 0) for k in _UK[:3])
    return {"tokens": total, "calls": calls, "context": ctx}


def declare(sid: str, target: int, warn: int, stop: int, calls_estimate: int | None = None,
            context_ceiling: int | None = None, noprogress_calls: int = DEFAULT_NOPROGRESS_CALLS,
            call_ratio: float = DEFAULT_CALL_RATIO, since_iso: str | None = None,
            per_child_stop: int | None = None, child_reserve: int | None = None) -> Path:
    """All amounts are PROCESSED tokens (the unit above). per_child_stop judges one subagent on its
    own transcript; child_reserve is held for a new child at Agent dispatch (guard default 2M)."""
    if not (0 < target <= warn <= stop):
        raise ValueError("need 0 < target <= warn <= stop")
    for name, v in (("per_child_stop", per_child_stop), ("child_reserve", child_reserve)):
        if v is not None and not 0 < v <= stop:
            raise ValueError(f"need 0 < {name} <= stop")
    import datetime as dt
    rec = {"session_id": sid, "unit": "processed_tokens", "target": target, "warn": warn, "stop": stop,
           "per_child_stop": per_child_stop, "child_reserve": child_reserve,
           "calls_estimate": calls_estimate, "call_ratio": call_ratio,
           "context_ceiling": context_ceiling, "noprogress_calls": noprogress_calls,
           "since": since_iso,
           "declared_at": dt.datetime.now(dt.timezone.utc).isoformat()[:19]}
    p = budget_path(sid)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    os.replace(tmp, p)
    return p


def _main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="mission_spend")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("session-declare")
    d.add_argument("--session", required=True)
    d.add_argument("--target", type=int, required=True)
    d.add_argument("--warn", type=int, required=True)
    d.add_argument("--stop", type=int, required=True)
    d.add_argument("--calls-estimate", type=int)
    d.add_argument("--context-ceiling", type=int)
    d.add_argument("--noprogress-calls", type=int, default=DEFAULT_NOPROGRESS_CALLS)
    d.add_argument("--since", help="ISO timestamp; count only from here (default: whole transcript)")
    d.add_argument("--per-child-stop", type=int, help="processed tokens one subagent may spend")
    d.add_argument("--child-reserve", type=int, help="processed tokens held for a new child at dispatch")
    s = sub.add_parser("session-status")
    s.add_argument("--transcript", required=True)
    s.add_argument("--since")
    a = ap.parse_args(argv)
    if a.cmd == "session-declare":
        print(declare(a.session, a.target, a.warn, a.stop, a.calls_estimate, a.context_ceiling,
                      a.noprogress_calls, since_iso=a.since, per_child_stop=a.per_child_stop, child_reserve=a.child_reserve))
        return 0
    print(json.dumps(session_tokens(Path(a.transcript), a.since)))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
