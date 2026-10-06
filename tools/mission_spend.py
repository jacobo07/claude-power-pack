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


def mission_sessions(rec: dict, ledger: Path | None = None) -> tuple[set[str], set[str]]:
    """(session ids, session-id prefixes) the mission spent through: the current owner, every
    worker its own ledger rows name (worker_acked / worker_adopted / ...), and -- prefix only -- the
    pending `bg_id` of a launch the worker has not acked yet.

    The directory alone is not the mission (2026-10-05, m-8bbdf725cd52): an interactive session
    planning in the same cwd landed in the same project directory and the meter read 70.7M for a
    mission whose own sessions had spent 53.7M."""
    ids = set()
    owner_sid = (rec.get("owner") or {}).get("session_id")
    if owner_sid:
        ids.add(owner_sid)
    mid = rec.get("mission_id")
    if mid:
        if ledger is None:
            import gsd_long_run as lr
            ledger = lr.ledger_path()
        if ledger.is_file():
            needle = f'"session_id": "{mid}"'
            with open(ledger, encoding="utf-8-sig", errors="replace") as fh:
                for line in fh:
                    if needle not in line or '"worker"' not in line:
                        continue
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(r, dict) and r.get("session_id") == mid and r.get("worker"):
                        ids.add(str(r["worker"]))
    bg = (rec.get("pending") or {}).get("bg_id")
    return ids, ({str(bg)} if bg else set())


def _attributed(path: Path, base: Path, ids: set[str], prefixes: set[str]) -> bool:
    """A transcript belongs to a session when its own stem, or a directory between the project
    directory and it (`<sid>/subagents/agent-*.jsonl`), is that session."""
    names = [path.stem] + [p.name for p in path.relative_to(base).parents if p.name]
    return any(n in ids or any(n.startswith(px) for px in prefixes) for n in names)


def processed_tokens(rec: dict, root: Path | None = None, cache: dict | None = None,
                     sessions: tuple[set[str], set[str]] | None = None) -> int | None:
    """Processed tokens the mission's OWN sessions have spent, or None when it cannot be measured:
    no transcript directory, or no session attributable to the mission (absence is not zero).
    `sessions` overrides `mission_sessions(rec)`. `cache` maps a file path to {size, mtime, tokens};
    unchanged files are not re-read."""
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
    ids, prefixes = sessions if sessions is not None else mission_sessions(rec)
    if not ids and not prefixes:
        return None
    since = None
    if rec.get("created_at"):
        import datetime as dt
        since = dt.datetime.fromtimestamp(float(rec["created_at"]), dt.timezone.utc).isoformat()[:19]
    total = 0
    for d in dirs:
        for p in d.rglob("*.jsonl"):
            if not _attributed(p, d, ids, prefixes):
                continue
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
            extra: dict | None = None) -> Path:
    if not (0 < target <= warn <= stop):
        raise ValueError("need 0 < target <= warn <= stop")
    import datetime as dt
    rec = {"session_id": sid, "target": target, "warn": warn, "stop": stop,
           "calls_estimate": calls_estimate, "call_ratio": call_ratio,
           "context_ceiling": context_ceiling, "noprogress_calls": noprogress_calls,
           "since": since_iso,
           "declared_at": dt.datetime.now(dt.timezone.utc).isoformat()[:19]}
    if extra:
        rec.update(extra)
    p = budget_path(sid)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    os.replace(tmp, p)
    return p


# --- Admission (TOK-18 Slice A2, 2026-10-06) ----------------------------------------------------
# An envelope was declared without ever being compared with what the pane costs per call. Session
# 1fd598fe declared stop 800K for ~6 calls right after /kresume; at ~110K context per call the resume
# had already spent most of it, and the breaker tripped on the next call with zero work done. A
# declaration is now projected from MEASURED per-call cost and refused before any call is spent on it.
DEFAULT_GROWTH_PER_CALL = 2_100   # context growth per call, measured over the 49 calls of post-E1 Phase 1
DEFAULT_RESERVE_CALLS = 2         # closeout: the spend row and the handoff
FLOOR_SAMPLE = 10                 # recent same-cwd sessions sampled when this session has no transcript yet


def find_transcript(sid: str, root: Path | None = None) -> Path | None:
    root = root or projects_root()
    if not root.is_dir():
        return None
    hits = [p for p in root.glob(f"*/{sid}.jsonl") if p.is_file()]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def _first_context(path: Path) -> int | None:
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            m = r.get("message") if isinstance(r, dict) else None
            if not isinstance(m, dict):
                continue
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            n = sum(int(u.get(k) or 0) for k in _UK[:3])
            if n:
                return n
    return None


def recent_floor(project_dir: Path, exclude: str | None = None, sample: int = FLOOR_SAMPLE) -> int | None:
    """Median first-call context of the most recent sessions in one project directory, or None."""
    if not project_dir.is_dir():
        return None
    files = sorted((p for p in project_dir.glob("*.jsonl") if p.stem != exclude),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:sample]
    floors = [f for f in (_first_context(p) for p in files) if f]
    if not floors:
        return None
    import statistics
    return int(statistics.median(floors))


def feasibility(sid: str, stop: int, calls_estimate: int | None, cwd: str | None = None,
                since_iso: str | None = None, root: Path | None = None,
                growth: int = DEFAULT_GROWTH_PER_CALL, reserve_calls: int = DEFAULT_RESERVE_CALLS) -> dict:
    """Project spent + n x per-call context + growth against `stop`. Per-call cost comes from this
    session's own last context, else the median first call of recent same-cwd sessions. Unknown cost
    or no call count is refused: an envelope that cannot be projected is not admitted."""
    root = root or projects_root()
    out = {"feasible": False, "stop": stop, "calls": None, "spent": None, "per_call": None,
           "projected": None, "source": None, "reason": None}
    if not calls_estimate or calls_estimate <= 0:
        out["reason"] = "no --calls-estimate: an envelope cannot be projected without a call count"
        return out
    spent, per_call = 0, None
    t = find_transcript(sid, root)
    if t is not None:
        ref = session_tokens(t, since_iso)
        spent = ref["tokens"]
        if ref["context"]:
            per_call, out["source"] = ref["context"], f"this session's last context ({t.name})"
    if per_call is None:
        d = root / encode_cwd(cwd or os.getcwd())
        per_call = recent_floor(d, exclude=sid)
        if per_call is not None:
            out["source"] = f"median first-call context of recent sessions in {d.name}"
    if per_call is None:
        out["reason"] = ("per-call cost unknown (no transcript for this session and no recent session "
                         "in this cwd): unknown is never admitted")
        return out
    n = int(calls_estimate) + reserve_calls
    projected = spent + n * per_call + growth * n * (n + 1) // 2
    ok = projected <= stop
    out.update(calls=n, spent=spent, per_call=per_call, projected=projected, feasible=ok)
    out["reason"] = (f"projected {projected:,} = spent {spent:,} + {n} calls x {per_call:,} + growth "
                     f"{growth:,}/call; {'<=' if ok else '>'} stop {stop:,}")
    return out


def _main(argv: list[str]) -> int:
    import argparse
    import sys
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
    d.add_argument("--skip-feasibility", action="store_true",
                   help="declare without the admission projection (the override is recorded in the budget file)")
    s = sub.add_parser("session-status")
    s.add_argument("--transcript", required=True)
    s.add_argument("--since")
    a = ap.parse_args(argv)
    if a.cmd == "session-declare":
        if a.skip_feasibility:
            f = {"skipped": True}
        else:
            f = feasibility(a.session, a.stop, a.calls_estimate, since_iso=a.since)
            if not f["feasible"]:
                print(f"REFUSED: {f['reason']}. Raise --stop, cut --calls-estimate, or pass "
                      "--skip-feasibility (recorded).", file=sys.stderr)
                return 3
        print(declare(a.session, a.target, a.warn, a.stop, a.calls_estimate, a.context_ceiling,
                      a.noprogress_calls, since_iso=a.since, extra={"feasibility": f}))
        return 0
    print(json.dumps(session_tokens(Path(a.transcript), a.since)))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
