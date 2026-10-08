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


# Running control (expected-completion E2). Chosen, not measured: a mission may forecast up to 25 %
# over its target before the forecast asks for a checkpoint; the 2 x hard trip is the real ceiling.
DEFAULT_EAC_TOLERANCE = 0.25
# Context rent: rotating costs one re-read of the floor to rehydrate a fresh session. Chosen as 1.0 x
# the profile floor F (a fresh session re-reads about F before its first useful call).
REHYDRATION_FLOORS = 1.0


def eac_forecast(spent: int, ctx_now: int, planned_calls: int, calls_done: int,
                 profile: dict | None) -> dict:
    """Estimate at completion: EAC = spent + r x (ctx_now + g x r / 2), r = remaining calls =
    max(0, planned_calls x (1 + calls_err) - calls_done). g (growth per call) and calls_err come from
    the route-floors profile. Absent g -> verdict UNKNOWN with eac None (absence is not zero); an absent
    calls_err is the one honest default, 0. Pure."""
    prof = profile or {}
    gv = (prof.get("growth_per_call") or {}).get("value")
    if gv is None:
        return {"eac": None, "r": None, "g": None, "basis": "UNKNOWN: profile has no growth_per_call",
                "verdict": "UNKNOWN", "rotate_recommended": None}
    g = float(gv)
    err = float((prof.get("calls_err") or {}).get("value") or 0.0)
    r = max(0.0, planned_calls * (1.0 + err) - calls_done)
    eac = spent + r * (ctx_now + g * r / 2.0)
    floor = prof.get("floor")
    rotate = None
    if floor:
        f = float(floor)
        rotate = (ctx_now - f) * r > f + REHYDRATION_FLOORS * f
    return {"eac": int(round(eac)), "r": r, "g": g,
            "basis": f"spent {spent:,} + r {r:g} x (ctx {ctx_now:,} + g {g:g} x r / 2); calls_err {err:g}",
            "verdict": "KNOWN", "rotate_recommended": rotate}


def judge(rec: dict, spent: int | None, fp: str | None, ctx_now: int | None = None,
          calls_done: int | None = None, profile: dict | None = None) -> dict:
    """{trip: reason|None, mark: new cost_mark|None, forecast: dict|None, decision: str|None}. Pure.

    The stall trip and the 2 x target hard trip are unchanged and win over any forecast. With a
    forecast input set (rec.planned_calls, ctx_now, calls_done) the decision is CONTINUE when
    EAC <= target x (1 + tolerance) AND the progress fingerprint moved since the last mark;
    CHECKPOINT otherwise; UNKNOWN when the profile has no growth_per_call (never CONTINUE)."""
    est = rec.get("token_estimate")
    if not est or spent is None:
        return {"trip": None, "mark": None, "forecast": None, "decision": None}
    est = int(est)
    ratio = float(rec.get("token_trip_ratio") or DEFAULT_TRIP_RATIO)
    if spent > ratio * est:
        return {"trip": (f"cost breaker: processed {spent:,} > {ratio:g} x estimate {est:,}; "
                         "explain the variance and recompute the remaining work before release"),
                "mark": None, "forecast": None, "decision": None}
    mark = rec.get("cost_mark") or {}
    forecast = decision = None
    planned = rec.get("planned_calls")
    if planned and ctx_now is not None and calls_done is not None:
        forecast = eac_forecast(spent, int(ctx_now), int(planned), int(calls_done), profile)
        tol = float(rec.get("eac_tolerance") if rec.get("eac_tolerance") is not None
                    else DEFAULT_EAC_TOLERANCE)
        if forecast["verdict"] == "UNKNOWN":
            decision = "UNKNOWN"
        else:
            moved = fp is not None and mark.get("fp") != fp
            decision = "CONTINUE" if (forecast["eac"] <= est * (1 + tol) and moved) else "CHECKPOINT"
    if fp is None:
        return {"trip": None, "mark": None, "forecast": forecast, "decision": decision}
    if mark.get("fp") != fp:
        return {"trip": None, "mark": {"fp": fp, "tokens": spent}, "forecast": forecast,
                "decision": decision}
    stall = int(rec.get("token_stall_budget") or est * DEFAULT_STALL_FRACTION)
    burned = spent - int(mark.get("tokens") or 0)
    if burned > stall:
        return {"trip": (f"cost breaker: {burned:,} processed since the work tree last changed "
                         f"(stall budget {stall:,}); semantic progress is not keeping up with spend"),
                "mark": None, "forecast": forecast, "decision": decision}
    return {"trip": None, "mark": None, "forecast": forecast, "decision": decision}


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


def _floor_path() -> Path:
    return state_dir() / "session-floors.jsonl"


def _read_floor_rows() -> list[dict]:
    try:
        text = _floor_path().read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict):
            rows.append(r)
    return rows


def record_floor(sid: str, transcript: Path) -> bool:
    """Append {sid, cwd_dir, first_context, at} once per sid. Never raises on I/O failure."""
    try:
        if any(r.get("sid") == sid for r in _read_floor_rows()):
            return False
        fc = _first_context(transcript)
        if not fc:
            return False
        import datetime as dt
        row = {"sid": sid, "cwd_dir": transcript.parent.name, "first_context": fc,
               "at": dt.datetime.now(dt.timezone.utc).isoformat()[:19]}
        p = _floor_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        return True
    except OSError:
        return False


def recent_floor(project_dir: Path, exclude: str | None = None, sample: int = FLOOR_SAMPLE) -> int | None:
    """Median first-call context of the most recent sessions in one project directory, or None.
    Prefers the floor ledger (cheap); falls back to scanning transcripts only when it has no rows."""
    import statistics
    rows = [r for r in _read_floor_rows() if r.get("cwd_dir") == project_dir.name
            and r.get("sid") != exclude and isinstance(r.get("first_context"), int) and r["first_context"] > 0]
    if rows:
        return int(statistics.median(r["first_context"] for r in rows[-sample:]))
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
        # per-call cost is the session's latest context over the WHOLE transcript: a window that
        # starts after the last row has context 0 and must not fall back to other sessions' floors.
        own = ref if not since_iso else session_tokens(t, None)
        if own["context"]:
            per_call, out["source"] = own["context"], f"this session's last context ({t.name})"
            record_floor(sid, t)
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


# --- Goal budget admission (A1 incident 2026-10-07, vault/specs/goal-budget-admission.md) ----------
# A session envelope judged one pane; A1 was spent by several panes and their subagents against one
# cap that nothing checked before a call. A GOAL is that cap: a GoalLedger journal under
# <state>/goal-budget/<goal>/, plus index.json (roots, hosts, lease size, since) that binds panes to it.
# session_budget_guard.js measures each bound session and asks `goal-renew` for a lease when the last
# one is spent; a refusal there is the pre-call stop.
GOAL_LEASE_CALLS = 5
GOAL_DEFAULT_PER_CALL = 150_000   # used only before a session has a measured context of its own


def goal_root() -> Path:
    return state_dir() / "goal-budget"


_GOAL_RE = re.compile(r"^(?!\.+$)[A-Za-z0-9._-]{1,128}$")   # '.' / '..' would root a ledger in state/


def _goal_ledger(goal: str):
    import sys
    if not _GOAL_RE.match(goal or ""):
        raise ValueError(f"invalid goal id: {goal!r}")
    repo = str(Path(__file__).resolve().parents[1])
    if repo not in sys.path:
        sys.path.insert(0, repo)
    from modules.provider_routing.ledger import GoalLedger
    return GoalLedger(goal_root() / goal, goal)


def read_index() -> dict:
    try:
        ix = json.loads((goal_root() / "index.json").read_text(encoding="utf-8-sig"))
        return ix if isinstance(ix, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_index(ix: dict) -> None:
    p = goal_root() / "index.json"
    tmp = p.with_name(f"index.json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(ix, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, p)


def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p)).rstrip("\\/")


def _overlaps(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    return a == b or a.startswith(b + os.sep) or b.startswith(a + os.sep)


def inside_agent() -> bool:
    """A backstop only: the agent's own child process can unset it (review H1, 31f1e714). The
    authority for a raise or a rebind is `owner` -- an interactive confirmation, see _main."""
    return bool(os.environ.get("CLAUDECODE"))


def goal_declare(goal: str, cap: int, source: str, roots: list[str] | None = None,
                 hosts: list[str] | None = None, lease_calls: int | None = None,
                 owner: bool = False) -> dict:
    """Create a goal or change its cap. Without `owner` (an interactive Owner confirmation) only a
    NEW goal or a LOWER cap is admitted; a goal's roots never overlap another goal's."""
    import datetime as dt
    import sys
    led = _goal_ledger(goal)            # validates the id and creates the goal directory
    repo = str(Path(__file__).resolve().parents[1])
    if repo not in sys.path:
        sys.path.insert(0, repo)
    from modules.lease.store import Exclusive
    unprivileged = not (owner and not inside_agent())   # the Owner confirmed it, outside any session
    with Exclusive(goal_root() / "index.lock", 10.0):
        ix = read_index()
        cur = ix.get(goal)
        roots = [_norm(r) for r in (roots or [])]
        if cur is not None and unprivileged and (roots and roots != cur.get("roots") or hosts and hosts != cur.get("hosts")
                                                 or lease_calls and lease_calls != cur.get("lease_calls")):
            return {"ok": False, "goal": goal,
                    "reason": "rebinding an existing goal needs the Owner's interactive confirmation (--owner)"}
        for other, e in ix.items():
            if other != goal and any(_overlaps(r, o) for r in roots for o in e.get("roots", [])):
                return {"ok": False, "goal": goal, "reason": f"roots overlap goal {other!r}"}
        out = led.declare_cap(cap, source, inside_agent=unprivileged)
        if not out["ok"]:
            return out
        entry = dict(cur or {"since": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                             "roots": [], "hosts": [], "lease_calls": GOAL_LEASE_CALLS})
        if roots:
            entry["roots"] = roots
        if hosts:
            entry["hosts"] = hosts
        if lease_calls:
            entry["lease_calls"] = lease_calls
        ix[goal] = entry
        _write_index(ix)
    return {**out, "binding": entry}


def _goal_entry(goal: str, host: str) -> tuple[dict | None, str]:
    e = read_index().get(goal)
    if e is None:
        return None, f"UNKNOWN: goal {goal!r} is not declared"
    if e.get("hosts") and host not in e["hosts"]:
        return None, f"UNKNOWN: host {host!r} is not one of goal {goal!r} hosts {e['hosts']}"
    return e, ""


def goal_renew(goal: str, sid: str, measured: int, per_call: int, host: str) -> dict:
    e, why = _goal_entry(goal, host)
    if e is None:
        return {"ok": False, "goal": goal, "reason": why}
    lease = int(e.get("lease_calls") or GOAL_LEASE_CALLS) * (per_call if per_call > 0 else GOAL_DEFAULT_PER_CALL)
    return _goal_ledger(goal).renew(sid, measured, lease)


def goal_spawn(goal: str, sid: str, estimate: int | None, per_call: int, host: str, measured: int = 0) -> dict:
    e, why = _goal_entry(goal, host)
    if e is None:
        return {"ok": False, "goal": goal, "reason": why}
    if not estimate or estimate <= 0:
        estimate = int(e.get("lease_calls") or GOAL_LEASE_CALLS) * (per_call if per_call > 0 else GOAL_DEFAULT_PER_CALL)
    return _goal_ledger(goal).spawn(sid, estimate, base=max(0, measured))


# --- Autopsy + forecast (cost-collapse T2, 2026-10-08) --------------------------------------------
# Where the processed tokens of a mission went, per session and per subagent, from the same
# transcripts and the same attribution as `processed_tokens`; then the inverse, a bottom-up forecast
# whose every missing input is `unmeasured`, never zero.
DEFAULT_STALL_SECONDS = 600


def _ts(s: str | None) -> float | None:
    if not s:
        return None
    import datetime as dt
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.timestamp()


def autopsy_transcript(path: Path, since_iso: str | None = None, stall_s: int = DEFAULT_STALL_SECONDS,
                       seen_global: set | None = None) -> dict:
    """One transcript. `processed` follows `_file_tokens` exactly (dedupe by message id inside the file),
    so the sum over a mission equals `processed_tokens`. A message id already in `seen_global` (counted in
    an earlier transcript: a forked copy replays its parent's history) is reported under `fork_*` and
    left out of `processed_unique`. Context = input + cache write + cache read of one call."""
    seen, tools_seen, tools = set(), set(), {}
    n = proc = uniq = fork_n = fork_tok = cr = cw = out = 0
    ctxs, times = [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            if since_iso and (r.get("timestamp") or "") < since_iso:
                continue
            m = r.get("message")
            if not isinstance(m, dict):
                continue
            if r.get("type") == "assistant" and isinstance(m.get("content"), list):
                for b in m["content"]:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        bid = b.get("id") or id(b)
                        if bid not in tools_seen:
                            tools_seen.add(bid)
                            tools[b.get("name") or "?"] = tools.get(b.get("name") or "?", 0) + 1
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            tok = sum(int(u.get(k) or 0) for k in _UK)
            n += 1
            proc += tok
            cr += int(u.get("cache_read_input_tokens") or 0)
            cw += int(u.get("cache_creation_input_tokens") or 0)
            out += int(u.get("output_tokens") or 0)
            ctxs.append(sum(int(u.get(k) or 0) for k in _UK[:3]))
            t = _ts(r.get("timestamp"))
            if t is not None:
                times.append(t)
            if seen_global is not None and mid in seen_global:
                fork_n += 1
                fork_tok += tok
            else:
                uniq += tok
                if seen_global is not None:
                    seen_global.add(mid)
    times.sort()
    stalls = [{"after": times[i - 1], "gap_s": round(times[i] - times[i - 1], 1)}
              for i in range(1, len(times)) if times[i] - times[i - 1] > stall_s]
    return {"calls": n, "processed": proc, "processed_unique": uniq, "fork_calls": fork_n,
            "fork_tokens": fork_tok, "cache_read": cr, "cache_write": cw, "output": out,
            "first_ctx": ctxs[0] if ctxs else None, "max_ctx": max(ctxs) if ctxs else None,
            "mean_ctx": round(sum(ctxs) / len(ctxs)) if ctxs else None,
            "tool_mix": dict(sorted(tools.items(), key=lambda kv: -kv[1])),
            "stalls": stalls, "stall_seconds": round(sum(s["gap_s"] for s in stalls), 1),
            "first_ts": times[0] if times else None}


def autopsy(rec: dict, root: Path | None = None, stall_s: int = DEFAULT_STALL_SECONDS,
            sessions: tuple[set[str], set[str]] | None = None) -> dict | None:
    """Per-session / per-subagent breakdown of the mission's OWN transcripts, or None when the mission
    cannot be measured (same rule as `processed_tokens`: absent is not zero). Attribution is
    `mission_sessions` + `_attributed`, not re-derived. Transcripts are walked oldest first so the
    original keeps a forked message and the copy is the one excluded."""
    root = root or projects_root()
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
    files = []
    for d in dirs:
        for p in d.rglob("*.jsonl"):
            if _attributed(p, d, ids, prefixes):
                files.append((d, p))
    seen_global: set = set()
    stats = []
    for d, p in files:
        s = autopsy_transcript(p, since, stall_s, seen_global=None)
        s["_p"], s["_d"] = p, d
        stats.append(s)
    stats.sort(key=lambda s: (s["first_ts"] is None, s["first_ts"] or 0, str(s["_p"])))
    rows = []
    for s in stats:
        # second pass with the shared id set, oldest transcript first: forks fall out of the later file
        full = autopsy_transcript(s["_p"], since, stall_s, seen_global=seen_global)
        rel = s["_p"].relative_to(s["_d"])
        kind = "subagent" if "subagents" in rel.parts else "session"
        full.update({"file": str(rel).replace("\\", "/"), "kind": kind,
                     "session": rel.parts[0] if kind == "subagent" else s["_p"].stem,
                     "agent": s["_p"].stem if kind == "subagent" else None})
        rows.append(full)
    tot = {k: sum(r[k] for r in rows) for k in
           ("calls", "processed", "processed_unique", "fork_calls", "fork_tokens",
            "cache_read", "cache_write", "output", "stall_seconds")}
    tot["mean_ctx"] = (round(sum((r["mean_ctx"] or 0) * r["calls"] for r in rows) / tot["calls"])
                       if tot["calls"] else None)
    return {"mission_id": rec.get("mission_id"), "since": since, "stall_threshold_s": stall_s,
            "rows": rows, "total": tot}


def _row_input(v):
    """(value|None, basis) from a bare number, a {value, basis} dict, or nothing."""
    if isinstance(v, dict):
        val, basis = v.get("value"), str(v.get("basis") or "declared")
    else:
        val, basis = v, "declared"
    if val is None or (isinstance(val, str) and val.strip() in ("", "?", "unmeasured")):
        return None, "unmeasured"
    return float(val), basis


_FORECAST_INPUTS = ("units", "calls_per_unit", "floor", "context_image", "repair")


def forecast(rows: list[dict]) -> dict:
    """Obligation rows: units x calls_per_unit x (floor + context_image) x (1 + repair) processed tokens.
    A row with any missing input is `unmeasured` with tokens None and the missing inputs named: absent is
    never zero (a repair rate of 0 must be stated, not omitted). Confidence is the weakest input basis:
    `measured` (every basis starts `measured`), `estimated` (anything else declared), `unmeasured`.
    The total is a LOWER BOUND whenever a row is unmeasured."""
    out, total, miss_rows = [], 0.0, 0
    for r in rows:
        vals, bases, missing = {}, {}, []
        for k in _FORECAST_INPUTS:
            v, b = _row_input(r.get(k))
            vals[k], bases[k] = v, b
            if v is None:
                missing.append(k)
        if missing:
            miss_rows += 1
            out.append({"name": r.get("name"), "tokens": None, "confidence": "unmeasured",
                        "missing": missing, "basis": bases})
            continue
        tokens = (vals["units"] * vals["calls_per_unit"] * (vals["floor"] + vals["context_image"])
                  * (1 + vals["repair"]))
        conf = "measured" if all(b.startswith("measured") for b in bases.values()) else "estimated"
        total += tokens
        out.append({"name": r.get("name"), "tokens": round(tokens), "confidence": conf,
                    "missing": [], "basis": bases})
    return {"rows": out, "total": round(total), "lower_bound": miss_rows > 0,
            "unmeasured_rows": miss_rows}


def _load_mission(mid: str) -> dict:
    import gsd_mission as gm
    rec = gm.load(mid)
    if rec is None:
        raise SystemExit(f"mission {mid} not found")
    return rec


def _main(argv: list[str]) -> int:
    import argparse
    import socket
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
    gd = sub.add_parser("goal-declare")
    gd.add_argument("--goal", required=True)
    gd.add_argument("--cap", type=int, required=True)
    gd.add_argument("--source", required=True, help="where this cap is decided, e.g. ledger.json@ab44236e")
    gd.add_argument("--root", action="append", default=[], help="a directory whose sessions bind to this goal")
    gd.add_argument("--host", action="append", default=[], help="a host allowed to spend (default: any)")
    gd.add_argument("--lease-calls", type=int)
    gd.add_argument("--owner", action="store_true",
                    help="raise a cap or rebind a goal: asks you to type the goal id on an interactive terminal")
    for name in ("goal-renew", "goal-spawn"):
        g = sub.add_parser(name)
        g.add_argument("--goal", required=True)
        g.add_argument("--session", required=True)
        g.add_argument("--per-call", type=int, default=0)
        g.add_argument("--host", default=socket.gethostname())
        g.add_argument("--measured", type=int, required=(name == "goal-renew"), default=0)
        if name == "goal-spawn":
            g.add_argument("--estimate", type=int)
    gs = sub.add_parser("goal-status")
    gs.add_argument("--goal", required=True)
    au = sub.add_parser("autopsy")
    au.add_argument("--mission", required=True)
    au.add_argument("--stall-seconds", type=int, default=DEFAULT_STALL_SECONDS)
    au.add_argument("--root", help="transcript projects root (default: ~/.claude/projects)")
    fc = sub.add_parser("forecast")
    fc.add_argument("--rows", required=True, help="JSON file: a list of obligation rows")
    a = ap.parse_args(argv)
    if a.cmd == "autopsy":
        res = autopsy(_load_mission(a.mission), Path(a.root) if a.root else None, a.stall_seconds)
        if res is None:
            print(json.dumps({"ok": False, "mission_id": a.mission, "reason": "unmeasurable: no transcript "
                              "directory or no attributable session"}))
            return 3
        print(json.dumps({"ok": True, **res}, sort_keys=True))
        return 0
    if a.cmd == "forecast":
        print(json.dumps(forecast(json.loads(Path(a.rows).read_text(encoding="utf-8-sig"))), sort_keys=True))
        return 0
    if a.cmd.startswith("goal-"):
        if a.cmd == "goal-declare":
            owner = False
            if a.owner:
                # The authority for a raise or a rebind is a person at a terminal: an agent's tool shell
                # has no interactive stdin, and an env var it can unset is not an authority (review H1).
                if not sys.stdin.isatty():
                    print(json.dumps({"ok": False, "goal": a.goal,
                                      "reason": "--owner needs an interactive terminal (stdin is not a TTY)"}))
                    return 3
                owner = input(f"Owner change to goal {a.goal!r}: type the goal id to confirm: ").strip() == a.goal
            out = goal_declare(a.goal, a.cap, a.source, a.root, a.host, a.lease_calls, owner=owner)
        elif a.cmd == "goal-renew":
            out = goal_renew(a.goal, a.session, a.measured, a.per_call, a.host)
        elif a.cmd == "goal-spawn":
            out = goal_spawn(a.goal, a.session, a.estimate, a.per_call, a.host, a.measured)
        else:
            out = {**_goal_ledger(a.goal).status(), "binding": read_index().get(a.goal)}
        print(json.dumps(out, sort_keys=True))
        return 0 if out.get("ok") else 3
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
