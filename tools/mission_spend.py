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
import time
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


# --- Lineage (UCDA A2, 2026-10-09) -----------------------------------------------------------------
# A renewal used to carry a FRESH token_estimate: a lineage renewed three times could spend 4x its
# envelope while every single mission stayed under its own. The lineage is the unit of budget.

def _lineage_id(m: dict) -> str:
    return m.get("lineage_id") or m["mission_id"]


def lineage_members(mission_id: str, all_missions=None, extra: dict | None = None) -> list[dict]:
    """Every mission of the lineage `mission_id` belongs to, root first. `extra` is a record not yet
    persisted (the one being renewed)."""
    if all_missions is None:
        import gsd_mission as gm
        all_missions = gm.all_missions
    recs = {m["mission_id"]: m for m in all_missions()}
    if extra:
        recs.setdefault(extra["mission_id"], extra)
    target = recs.get(mission_id)
    if target is None:
        return []
    lid = _lineage_id(target)
    members = [m for m in recs.values() if _lineage_id(m) == lid]
    return sorted(members, key=lambda m: (int(m.get("renewal") or 0), float(m.get("created_at") or 0)))


def lineage_head(mission_id: str, all_missions=None) -> str:
    """The newest mission of the lineage of `mission_id`; the id itself when it is unknown."""
    members = lineage_members(mission_id, all_missions)
    return members[-1]["mission_id"] if members else mission_id


def lineage_spend(mission_id: str, all_missions=None, extra: dict | None = None,
                  root: Path | None = None, cache: dict | None = None) -> dict:
    """{processed, unmeasured, members}: sum over the measurable members; a member that cannot be
    measured is listed in `unmeasured`, never counted as zero."""
    total, unmeasured, ids = 0, [], []
    for m in lineage_members(mission_id, all_missions, extra):
        ids.append(m["mission_id"])
        n = processed_tokens(m, root, cache)
        if n is None:
            unmeasured.append(m["mission_id"])
        else:
            total += n
    return {"processed": total, "unmeasured": unmeasured, "members": ids}


def lineage_remaining(rec: dict, all_missions=None, root: Path | None = None, cache: dict | None = None) -> dict:
    """Remaining token budget of the lineage `rec` belongs to: {budget, spent, remaining, unmeasured}.
    `remaining` is None when there is no budget or any member is unmeasurable (absence is not zero)."""
    budget = rec.get("lineage_token_budget") or rec.get("token_estimate")
    out = {"budget": int(budget) if budget else None, "spent": None, "remaining": None, "unmeasured": []}
    if not budget:
        return out
    sp = lineage_spend(rec["mission_id"], all_missions, extra=rec, root=root, cache=cache)
    out["unmeasured"] = sp["unmeasured"]
    if sp["unmeasured"]:
        return out
    out["spent"] = sp["processed"]
    out["remaining"] = int(budget) - sp["processed"]
    return out


MAX_SNAPSHOT_AGE_S = 900


def stale_usage_guard(snapshot_at: float | None, now: float, max_age: float = MAX_SNAPSHOT_AGE_S) -> str | None:
    """U1: a usage number is only as good as its measurement time. Returns the STALE text, or None
    when fresh. A missing watermark is stale too (unknown age is not fresh). Pure."""
    if snapshot_at is None:
        return "STALE: usage snapshot has no as_of watermark; re-measure before acting on it"
    age = now - float(snapshot_at)
    if age > max_age or age < 0:
        return (f"STALE: usage snapshot as_of {_iso(snapshot_at)} is {age:,.0f}s old "
                f"(limit {max_age:,.0f}s); re-measure before acting on it")
    return None


def _iso(ts: float) -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(float(ts), _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


DEFAULT_CLOSEOUT_TOKENS = 1_000_000


def closeout_reserve(rec: dict) -> int:
    """Capital kept back from productive work for the closeout after a stop: the record's `closeout_tokens`, else
    1M, never more than a twentieth of the authority (a 3M canary keeps 150K, not a third of its budget)."""
    auth = int(rec.get("authority_tokens") or 0)
    own = rec.get("closeout_tokens")
    if own is not None:
        return max(0, int(own))
    return min(DEFAULT_CLOSEOUT_TOKENS, auth // 20) if auth else 0


def authority_kind(rec: dict) -> str:
    """Whose ceiling binds: OWNER (declared authority), DEFAULT_POLICY (auto envelope only), else OPERATOR_ESTIMATE."""
    if rec.get("authority_tokens"):
        return "OWNER"
    return "DEFAULT_POLICY" if rec.get("token_estimate_src") == "auto" else "OPERATOR_ESTIMATE"


def judge(rec: dict, spent: int | None, fp: str | None, as_of: float | None = None,
          now: float | None = None) -> dict:
    """{trip: reason|None, mark: new cost_mark|None}. Pure. When `as_of` (measurement time) is given
    with `now`, a stale snapshot never trips (it returns `stale`) and a trip names its watermark."""
    est = rec.get("token_estimate")
    auth = rec.get("authority_tokens")
    if (not est and not auth) or spent is None:
        return {"trip": None, "mark": None}
    stale = stale_usage_guard(as_of, now) if now is not None else None
    if stale:
        return {"trip": None, "mark": None, "stale": stale}
    if auth:
        # 2026-10-15 m-ce2bacd4cbb0: authority 45M, estimate 45M, breaker at 2 x 45M; it spent 83.8M before a person
        # noticed. The Owner's authority is the ceiling whatever the estimate says, minus a closeout reserve that
        # productive work may not consume (commit, state, settlement after the hold).
        auth = int(auth)
        closeout = closeout_reserve(rec)
        if spent >= auth - closeout:
            wm = f" (as of {_iso(as_of)})" if as_of is not None else ""
            return {"trip": (f"cost breaker (mission authority): processed {spent:,}{wm} >= authority {auth:,} "
                             f"minus closeout reserve {closeout:,}; only closeout may run, new authority is the "
                             "Owner's"), "mark": None, "level": "MISSION_AUTHORITY"}
    if not est:
        return {"trip": None, "mark": None}
    est = int(est)
    ratio = float(rec.get("token_trip_ratio") or DEFAULT_TRIP_RATIO)
    if spent > ratio * est:
        wm = f" (as of {_iso(as_of)})" if as_of is not None else ""
        if rec.get("token_estimate_src") == "auto":
            # An auto envelope is the default allowance, not a forecast the operator made (m-3f1feb210a74).
            if auth:   # Owner capital remains (the authority check above passed): the forecast is stale, recompile it
                return {"trip": None, "mark": None,
                        "recompile": {"spent": spent, "estimate": est, "authority": auth, "ratio": ratio}}
            return {"trip": (f"cost breaker: processed {spent:,}{wm} > default policy ceiling ({ratio:g} x estimate "
                             f"{est:,}, an auto envelope); no Owner authority was ever declared for this mission, so "
                             "this is the default allowance, not a forecast miss; declare authority to continue"),
                    "mark": None, "level": "DEFAULT_CEILING", "authority_kind": "DEFAULT_POLICY"}
        return {"trip": (f"cost breaker: processed {spent:,}{wm} > {ratio:g} x estimate {est:,}; "
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
def _noprogress_default() -> int:
    """ce-a5 U7: 14 (smallest K with <=5% false trips on the DWS corpus, A/STALL.md); env CPP_NOPROGRESS_K overrides."""
    try:
        v = int(os.environ.get("CPP_NOPROGRESS_K", ""))
        return v if v >= 1 else 14
    except ValueError:
        return 14


DEFAULT_NOPROGRESS_CALLS = _noprogress_default()


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


def session_tree_tokens(transcript: Path) -> dict:
    """Processed tokens of a session AND its subagents (`<sid>/subagents/agent-*.jsonl`), one dedup set
    over every file: a message id is counted once wherever it appears. Measured 2026-10-15: subagents
    were 79% of an 80M incident, and a main-transcript count alone books the other 21%."""
    files = [transcript] + sorted((transcript.parent / transcript.stem / "subagents").glob("agent-*.jsonl"))
    seen, total, subs = set(), 0, 0
    for f in files:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                m = r.get("message") if isinstance(r, dict) else None
                u = m.get("usage") if isinstance(m, dict) else None
                if not u or m.get("model") == "<synthetic>":
                    continue
                mid = m.get("id") or r.get("uuid")
                if mid in seen:
                    continue
                seen.add(mid)
                n = sum(int(u.get(k) or 0) for k in _UK)
                total += n
                if f is not transcript:
                    subs += n
    return {"tokens": total, "subagent_tokens": subs, "files": len(files)}


def session_tree_report(transcript: Path) -> dict:
    """The cost tree of one session: a node per transcript (main + each subagent, typed from its meta.json),
    with turns, processed tokens and context per turn, under the SAME dedup as session_tree_tokens, so the
    node sum equals that total. Measured 2026-10-16 (m-f9290d78278f): a hand sum of `usage` per transcript
    LINE read 65.4M for a 29.9M session tree (Claude repeats a message's usage on each content-block line)."""
    files = [transcript] + sorted((transcript.parent / transcript.stem / "subagents").glob("agent-*.jsonl"))
    seen, nodes = set(), []
    for f in files:
        node = {"file": f.name, "kind": "main" if f is transcript else "subagent", "turns": 0, "tokens": 0,
                "ctx_sum": 0, "peak_ctx": 0}
        meta = f.with_name(f.stem + ".meta.json")
        if meta.is_file():
            try:
                m = json.loads(meta.read_text(encoding="utf-8"))
                node["agent_type"], node["description"] = m.get("agentType"), m.get("description")
            except ValueError:
                node["agent_type"] = "unreadable meta"
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                m = r.get("message") if isinstance(r, dict) else None
                u = m.get("usage") if isinstance(m, dict) else None
                if not u or m.get("model") == "<synthetic>":
                    continue
                mid = m.get("id") or r.get("uuid")
                if mid in seen:
                    continue
                seen.add(mid)
                n = sum(int(u.get(k) or 0) for k in _UK)
                ctx = n - int(u.get("output_tokens") or 0)
                node["turns"] += 1
                node["tokens"] += n
                node["ctx_sum"] += ctx
                node["peak_ctx"] = max(node["peak_ctx"], ctx)
        node["avg_ctx"] = node.pop("ctx_sum") // node["turns"] if node["turns"] else 0
        nodes.append(node)
    return {"tokens": sum(n["tokens"] for n in nodes), "turns": sum(n["turns"] for n in nodes), "nodes": nodes}


def goal_settle(goal: str, sid: str, measured: int | None = None, reason: str = "goal-settle",
                transcripts_root: Path | None = None, tree: bool = False) -> dict:
    """Settle a STOPPED session and close all of its holds (never reserves). Blind -> refused.
    `tree` also counts its subagents' transcripts (the supervisor's stop path sets it)."""
    if not _SID_RE.match(sid or ""):
        raise ValueError(f"invalid session id: {sid!r}")
    led = _goal_ledger(goal)
    capped = None
    if measured is None:
        tp = find_transcript(sid, transcripts_root)
        if tp is None:
            return {"ok": False, "goal": goal, "reason": "no transcript for the session and no --measured: "
                    "refusing to settle blind"}
        measured = int((session_tree_tokens(tp) if tree else session_tokens(tp))["tokens"])
        # A pane the guard already booked is charged only for what it booked plus its open holds: the
        # transcript total also holds its pre-binding and off-goal calls (a coordinator that left the
        # worktree was overcharged 18.6M this way, ctx-same-pane 2026-10-11).
        g = led._gfold(led._read())
        mark = g["marks"].get(sid, 0)
        if mark:
            ceiling = mark + sum(r["hold"] for r in g["res"].values() if r["sid"] == sid)
            # The transcript also holds the pre-binding history booked as capex: the ceiling alone charged
            # it again whenever it was wider than post-binding spend (ctx-rent-a2 2026-10-24, ~14.8M).
            post = measured - g["prebind"].get(sid, 0)
            if measured > min(ceiling, post):
                capped, measured = measured, max(mark, min(ceiling, post))
        elif g["prebind"].get(sid, 0) and measured > g["prebind"][sid]:
            # No mark, but its pre-binding history was booked as programme capex: never charge it again as
            # goal spend (a leaked pane was charged 1,021,626 of history this way, ctx-rent-a2 2026-10-23).
            capped, measured = measured, measured - g["prebind"][sid]
    out = led.settle_stopped(sid, int(measured), reason)
    if capped is not None:
        out["capped_from_transcript"] = capped
    return out


def correction_apply_pending(ledger_factory=None, root=None, timeout: float = 60.0, sleep=time.sleep,
                             now: float | None = None) -> list[dict]:
    """Same-pane Owner correction of a misbooked mark. A packet in corrections.json names one goal, one
    session, the mark it expects to find and a LOWER value; it applies only after an Owner-typed `approve`
    that follows an assistant entry showing the packet hash (the OCA rule). Never raises a mark."""
    from modules.provider_routing import capital_authority as ca
    ledger_factory = ledger_factory or _goal_ledger
    base = ca.capital_root(root)
    try:
        pend = json.loads((base / "corrections.json").read_text(encoding="utf-8-sig"))
        ap = [json.loads(x) for x in (base / "approvals.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    except (OSError, ValueError):
        return []
    if not ap or not isinstance(pend, list):
        return []
    log = base / "corrections.jsonl"
    done = set()
    if log.exists():
        for ln in log.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("state") == "APPLIED":
                done.add(r.get("sha"))
    transcript = ap[-1]["transcript_path"]
    if ap[-1].get("kind") != "approval":
        timeout = 0                                      # a sweep row is not an Owner approval: do not wait
    deadline, results = time.time() + timeout, []
    for path in pend:
        sha = ca.packet_sha(path)
        if sha in done:
            results.append({"sha": sha[:12], "ok": True, "applied": False, "reason": "already applied"})
            continue
        pk = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        goal, sid = pk["goal"], pk["session"]
        while True:
            appr = next((d for d in ca.find_owner_decisions(transcript, sha)
                         if d["decision"]["action"] == "approve" and d["decision"].get("goal") in (None, goal)), None)
            if appr is not None or time.time() >= deadline:
                break
            sleep(1.0)
        row = {"ts": time.time() if now is None else now, "sha": sha, "goal": goal, "session": sid}
        if appr is None:
            results.append({"sha": sha[:12], "ok": False, "applied": False,
                            "reason": "no Owner-typed approval for this packet hash"})
            continue
        led = ledger_factory(goal)
        mark = led._gfold(led._read())["marks"].get(sid, 0)
        if ca._expired(pk, row["ts"]):
            reason = "packet expired"
        elif mark != int(pk["expected_mark"]):
            reason = f"mark moved: {mark:,} != expected {int(pk['expected_mark']):,}"
        elif not 0 <= int(pk["measured"]) < mark:
            reason = f"a correction only lowers a mark: {int(pk['measured']):,} vs {mark:,}"
        else:
            reason = ""
        if reason:
            with log.open("a", encoding="utf-8") as f:
                f.write(json.dumps({**row, "state": "REJECTED", "reason": reason, "approval": appr["uuid"]}) + "\n")
            results.append({"sha": sha[:12], "ok": False, "applied": False, "reason": reason})
            continue
        out = led.correct(sid, int(pk["measured"]), pk["reason"], f"owner-same-pane:{sha[:12]}:{appr['uuid']}")
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({**row, "state": "APPLIED", "previous": mark, "measured": int(pk["measured"]),
                                "approval": appr["uuid"]}) + "\n")
        results.append({"sha": sha[:12], "ok": bool(out.get("ok")), "applied": True, "reason": ""})
    return results


def _real_console_stdin() -> bool:
    """A person at a terminal. On Windows the NUL device reports isatty() True, so ask the console."""
    import sys
    if not sys.stdin or not sys.stdin.isatty():
        return False
    if os.name == "nt":
        try:
            import ctypes
            mode = ctypes.c_uint32()
            h = ctypes.windll.kernel32.GetStdHandle(-10)
            return bool(ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(mode)))
        except Exception:  # noqa: BLE001
            return False
    return True


def goal_correct(goal: str, sid: str, measured: int, reason: str, authority: str) -> dict:
    return _goal_ledger(goal).correct(sid, int(measured), reason, authority)


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
    pc = per_call if per_call > 0 else GOAL_DEFAULT_PER_CALL
    # Accounting role (econ-contain WS-F): carried by the session's binding record, never by a CLI flag the
    # caller could set; any other value, or a binding to another goal, is productive spend.
    rec = read_binding(sid) or {}
    role = "recovery" if rec.get("goal") == goal and rec.get("role") == "recovery" else "productive"
    return _goal_ledger(goal).renew(sid, measured, int(e.get("lease_calls") or GOAL_LEASE_CALLS) * pc,
                                    per_call=pc, role=role)


def goal_spawn(goal: str, sid: str, estimate: int | None, per_call: int, host: str, measured: int = 0) -> dict:
    e, why = _goal_entry(goal, host)
    if e is None:
        return {"ok": False, "goal": goal, "reason": why}
    if not estimate or estimate <= 0:
        estimate = int(e.get("lease_calls") or GOAL_LEASE_CALLS) * (per_call if per_call > 0 else GOAL_DEFAULT_PER_CALL)
    return _goal_ledger(goal).spawn(sid, estimate, base=max(0, measured))


def goal_prebind(goal: str, sid: str, measured: int) -> dict:
    """Journal op {op:"prebind", sid, measured, goal}: PRE_BINDING_PROGRAM_CAPEX, never goal spend."""
    if not _SID_RE.match(sid or ""):
        return {"ok": False, "goal": goal, "reason": f"invalid session id: {sid!r}"}
    return _goal_ledger(goal).prebind(sid, int(measured))


# --- Prospective binding: Python twin of hooks/lib/goal_binding.js (same precedence, same record) ----
def prospective_bind() -> bool:
    """CPP_PROSPECTIVE_BIND=0|off|false restores the old (retroactive, cwd-by-lookup) behaviour."""
    return os.environ.get("CPP_PROSPECTIVE_BIND", "").strip().lower() not in ("0", "off", "false")


def binding_path(sid: str, gen: int = 1) -> Path:
    return state_dir() / "goal-binding" / (f"{sid}.g{gen}.json" if gen > 1 else f"{sid}.json")


def _now_ts() -> str:
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _read_rec(p: Path) -> dict | None:
    try:
        r = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return r if isinstance(r, dict) and isinstance(r.get("goal"), str) and r["goal"] else None


def read_binding(sid: str) -> dict | None:
    """The highest binding generation (econ-contain WS-E): <sid>.json is generation 1, a recovery
    transition writes <sid>.g<N>.json and never edits an earlier one. Twin of goal_binding.readBinding."""
    rec = _read_rec(binding_path(sid))
    if rec is None:
        return None
    rec = {"gen": 1, **rec}
    for n in range(2, 1000):
        r = _read_rec(binding_path(sid, n))
        if r is None:
            break
        rec = {"gen": n, **r}
    return rec


def supersede_binding(sid: str, goal: str, source: str, reason: str) -> dict | None:
    """Write the next generation ('x'); the goal being left joins `fenced`. None on a lost race."""
    cur = read_binding(sid)
    gen = cur["gen"] + 1 if cur else 1
    fenced = list(dict.fromkeys([*((cur.get("fenced") or []) if cur else []),
                                 *([cur["goal"]] if cur and cur["goal"] not in ("none", goal) else [])]))
    rec = {"goal": goal, "since_ts": _now_ts(), "source": source, "pid": os.getpid(), "gen": gen,
           "prev": cur["goal"] if cur else None, "reason": reason, "fenced": fenced}
    p = binding_path(sid, gen)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "x", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")))
        with open(p.parent / "transitions.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": rec["since_ts"], "sid": sid, "from": rec["prev"], "to": goal, "gen": gen,
                                 "source": source, "reason": reason, "fenced": fenced}, separators=(",", ":")) + "\n")
        return rec
    except OSError:
        return None


def goal_exhausted(goal: str) -> bool:
    """The current lease carries an `exhausted` marker. Twin of goal_binding.goalExhausted."""
    try:
        g = _goal_ledger(goal)
        with g._lock:
            return bool(g._gfold(g._read())["exhausted_now"])
    except (OSError, ValueError):
        return False


def write_binding(sid: str, goal: str, source: str) -> dict:
    """Immutable: exclusive create; if the record exists, the existing one wins."""
    rec = {"goal": goal, "since_ts": _now_ts(), "source": source, "pid": os.getpid()}
    p = binding_path(sid)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "x", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")))
        return rec
    except OSError:
        return read_binding(sid) or rec


def _warn_binding(sid: str, text: str) -> None:
    try:
        p = binding_path("x").parent
        p.mkdir(parents=True, exist_ok=True)
        with open(p / "warnings.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now_ts(), "sid": sid, "warning": text}, separators=(",", ":")) + "\n")
    except OSError:
        pass


_READ_TOOLS = {"Read", "Grep", "Glob"}
_READ_ONLY_CMD = re.compile(
    r"""^\s*(?:&\s*)?(?:(?:['"]?[^\s'"]*[\\/])?git(?:\.exe)?['"]?\s+(?:-C\s+\S+\s+)?(?:log|status|show)\b"""
    r"""|(?:['"]?[^\s'"]*[\\/])?(?:python3?|py)(?:\.exe)?['"]?\s+['"]?(?:[^\s'"]*[\\/])?"""
    r"""(?:mission_spend\.py['"]?\s+(?:goal-status|goal-lineage)|econ_plane\.py['"]?\s+status)\b)""",
    re.I)


def is_read_only_call(event: dict) -> bool:
    if str((event or {}).get("tool_name") or "") in _READ_TOOLS:
        return True
    ti = (event or {}).get("tool_input")
    cmd = ti.get("command") if isinstance(ti, dict) else ""
    if not isinstance(cmd, str) or not cmd:
        return False
    if re.search(r"[;&|<>`\n]|\$\(", re.sub(r"^\s*&\s*", "", cmd, count=1)):
        return False
    return bool(_READ_ONLY_CMD.search(cmd))


def _legacy_binding(event: dict, sid: str, ix: dict) -> dict | None:
    env = os.environ.get("CPP_GOAL", "").strip()
    if env:
        return {"goal": env, "entry": ix.get(env)}
    cwd = event.get("cwd")
    if cwd:
        for g, e in ix.items():
            if isinstance(e, dict) and any(_norm(cwd) == _norm(r) or _norm(cwd).startswith(_norm(r) + os.sep)
                                           for r in e.get("roots", [])):
                return {"goal": g, "entry": e}
    try:
        b = json.loads((state_dir() / f"session-budget-{sid}.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        b = None
    if isinstance(b, dict) and isinstance(b.get("goal"), str) and b["goal"]:
        return {"goal": b["goal"], "entry": ix.get(b["goal"])}
    return None


def _workspace_registry():
    """The registry when at least one workspace was ever claimed; None keeps the pre-W2 behaviour."""
    import sys
    repo = str(Path(__file__).resolve().parents[1])
    if repo not in sys.path:
        sys.path.insert(0, repo)
    from modules.provider_routing.workspace_registry import WorkspaceRegistry
    if not (goal_root() / "workspace.journal.jsonl").exists():
        return None
    return WorkspaceRegistry(goal_root())


def resolve_binding(event: dict, sid: str) -> dict | None:
    """(a) immutable record wins; (b) CPP_GOAL, a disagreeing record logs a warning; (c) cwd under a goal
    root WRITES the record at the first mutating call (a read-only call is bound in memory only);
    (d) the budget file's legacy `goal`. CPP_PROSPECTIVE_BIND=0 -> old resolver, no record read/written."""
    ix = read_index()
    if not prospective_bind():
        return _legacy_binding(event, sid, ix)
    env = os.environ.get("CPP_GOAL", "").strip()
    rec = read_binding(sid)
    if rec:
        if env and env != rec["goal"]:
            _warn_binding(sid, f"CPP_GOAL={env} ignored: the binding record names {rec['goal']} ({rec.get('source')})")
        if rec["goal"] == "none":
            return None
        return {"goal": rec["goal"], "entry": ix.get(rec["goal"]), "record": rec, "sinceTs": rec.get("since_ts")}
    if env:
        return {"goal": env, "entry": ix.get(env)}
    cwd = event.get("cwd")
    reg = _workspace_registry()
    if cwd and reg is not None:
        h = reg.holder_for_cwd(cwd)                  # (W2) an explicit registry holder beats the roots
        if h and h["goal"] in ix:
            if goal_exhausted(h["goal"]):            # QUARANTINE: never bind to an exhausted goal
                return {"goal": h["goal"], "entry": ix.get(h["goal"]), "record": None, "sinceTs": _now_ts(),
                        "provisional": True, "quarantine": True}
            if is_read_only_call(event):
                return {"goal": h["goal"], "entry": ix.get(h["goal"]), "record": None, "sinceTs": _now_ts(),
                        "provisional": True, "gen": h["gen"], "lease": h["lease"]}
            w = write_binding(sid, h["goal"], "registry")
            return {"goal": w["goal"], "entry": ix.get(w["goal"]), "record": w, "sinceTs": w.get("since_ts"),
                    "gen": h["gen"], "lease": h["lease"]}
    if cwd:
        for g, e in ix.items():
            if isinstance(e, dict) and any(_norm(cwd) == _norm(r) or _norm(cwd).startswith(_norm(r) + os.sep)
                                           for r in e.get("roots", [])):
                if goal_exhausted(g):                # QUARANTINE (twin of goal_binding.js)
                    return {"goal": g, "entry": e, "record": None, "sinceTs": _now_ts(),
                            "provisional": True, "quarantine": True}
                if reg is not None or is_read_only_call(event):
                    # observe only: once the registry exists, entering a goal worktree never binds, claims
                    # or settles (the 32.8M coordinator mis-attribution)
                    return {"goal": g, "entry": e, "record": None, "sinceTs": _now_ts(), "provisional": True}
                w = write_binding(sid, g, "cwd")
                return {"goal": w["goal"], "entry": e if w["goal"] == g else ix.get(w["goal"]),
                        "record": w, "sinceTs": w.get("since_ts")}
    return _legacy_binding(event, sid, ix)


def _under(cwd: str | None, roots: list[str]) -> bool:
    if not cwd:
        return False
    c = _norm(cwd)
    return any(c == r or c.startswith(r + os.sep) for r in map(_norm, roots))


def _session_autopsy(path: Path, roots: list[str]) -> dict:
    """Port of gen2/a3b-r/forensics/autopsy.py: calls and processed tokens per unique message id,
    split by whether the cwd was inside the goal's roots when the call was made."""
    seen, calls, processed, bound, refusals, human = set(), 0, 0, 0, 0, 0
    last_cwd, first_cwd = None, None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            if r.get("cwd"):
                last_cwd = r["cwd"]
                first_cwd = first_cwd or last_cwd
            m = r.get("message") or {}
            if not isinstance(m, dict):
                continue
            if r.get("type") == "user" and not r.get("isMeta") and (
                    isinstance(m.get("content"), str) or (isinstance(m.get("content"), list) and any(
                        isinstance(b, dict) and b.get("type") == "text" for b in m["content"])
                        and not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in m["content"]))):
                human += 1
            if r.get("type") == "user" and isinstance(m.get("content"), list):
                for b in m["content"]:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        txt = json.dumps(b.get("content"))[:400]
                        if "GOAL BUDGET" in txt or "SESSION BUDGET" in txt:
                            refusals += 1
            u = m.get("usage")
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            n = sum(int(u.get(k) or 0) for k in _UK)
            calls += 1
            processed += n
            if _under(last_cwd, roots):
                bound += n
    return {"calls": calls, "processed": processed, "bound": bound, "pre_bind": processed - bound,
            "refusals": refusals, "human_prompts": human, "first_cwd": first_cwd,
            "role": "worker" if _under(first_cwd, roots) else "pane"}


def _git_facts(root: str | None) -> dict:
    import shutil
    import subprocess
    exe = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    if not root or not os.path.isdir(root):
        return {"root": root, "head": None, "dirty": None}

    def run(*a):
        try:
            p = subprocess.run([exe, "-C", root, *a], capture_output=True, text=True, timeout=30)
            return p.stdout if p.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None
    head, st = run("rev-parse", "HEAD"), run("status", "--porcelain")
    return {"root": root, "head": head.strip() if head else None,
            "dirty": len([x for x in st.splitlines() if x.strip()]) if st is not None else None}


def goal_autopsy(goal: str, *, projects: Path | None = None) -> dict:
    """Deterministic, read-only post-mortem of a goal: per session calls, processed, pre-bind vs bound,
    refusals, open holds; git HEAD and dirty count of the goal root. Reads the journal WITHOUT the leak
    sweep (status() appends `leak` rows), so it adds nothing to a spent goal."""
    ent = read_index().get(goal)
    if ent is None:
        return {"ok": False, "goal": goal, "reason": f"UNKNOWN: goal {goal!r} is not declared", "sessions": []}
    led = _goal_ledger(goal)
    with led._lock:
        g = led._gfold(led._read())
    roots = list(ent.get("roots") or [])
    sids = sorted({r["sid"] for r in g["res"].values()} | set(g["marks"]))
    rows = []
    for sid in sids:
        holds = sum(1 for r in g["res"].values() if r["sid"] == sid and r["state"] in ("RESERVED", "LEAKED"))
        try:
            tx = find_transcript(sid, projects)
            a = _session_autopsy(tx, roots) if tx else None
        except OSError:
            a = None
        row = {"sid": sid, "transcript": a is not None, "open_holds": holds,
               **(a or {"calls": 0, "processed": 0, "bound": 0, "pre_bind": 0, "refusals": 0, "role": "unknown"})}
        rows.append(row)
    tot = lambda k, role=None: sum(r[k] for r in rows if role is None or r["role"] == role)
    return {"ok": True, "goal": goal, "cap": g["cap"], "used": g["used"], "sessions": rows,
            "workers_processed": tot("processed", "worker"), "panes_processed": tot("processed", "pane"),
            "pre_bind_processed": tot("pre_bind"), "bound_processed": tot("bound"),
            "git": _git_facts(roots[0] if roots else None)}


def autopsy_table(out: dict) -> str:
    """The incident table as fixed-width text (byte-stable for a given journal and transcripts)."""
    w = (8, 5, 11, 9, 10, 8)

    def line(cells):
        return " ".join(str(c).ljust(n) for c, n in zip(cells[:-1], w)) + " " + str(cells[-1]) + "\n"
    rows = out.get("sessions") or []
    s = line(("sid", "calls", "processed", "pre_bind", "bound", "refusals", "open_holds"))
    for r in rows:
        s += line((r["sid"][:8], r["calls"], f"{r['processed']:,}", f"{r['pre_bind']:,}", f"{r['bound']:,}",
                   r["refusals"], r["open_holds"]))
    t = lambda k: sum(r[k] for r in rows)
    return s + line(("TOTAL", t("calls"), f"{t('processed'):,}", f"{t('pre_bind'):,}", f"{t('bound'):,}",
                     t("refusals"), t("open_holds")))


def goal_fault_capsule(goal: str, sid: str, cwd: str, reason: str, *, sd=None, transcript=None,
                       ask=None, children=None) -> dict | None:
    """A bound session's terminal refusal / SessionEnd -> a Fault Capsule through mission_capsule.
    None for a session whose cwd is outside the goal's roots (unbound sessions leave nothing)."""
    ent = read_index().get(goal)
    if ent is None or not _under(cwd, list(ent.get("roots") or [])):
        return None
    import mission_capsule as mc
    if transcript is None:
        tx = find_transcript(sid)
        transcript = str(tx) if tx else None
    return mc.fault_capsule(goal, sid, cwd, reason, sd=sd, transcript=transcript, ask=ask, children=children)


def goal_for_cwd(cwd: str | None) -> str | None:
    """The declared goal whose root contains `cwd` (None when none). Keyed by ROOT, never by mission id."""
    if not cwd:
        return None
    for g, e in sorted(read_index().items()):
        if isinstance(e, dict) and _under(cwd, list(e.get("roots") or [])):
            return g
    return None


MATERIAL_TOKENS = 100_000


def programme_spend(goal: str, *, projects: Path | None = None, mission_sids: set[str] | None = None,
                    material: int | None = None) -> dict:
    """ONE programme spend view of a goal: settled / reserved / unknown / available, measured from the
    ledger journal and transcripts (no pane arithmetic). It is keyed by the goal, so a new mission id
    under the same root cannot reset it. Roles: worker (mission-owner session), control (ledger session
    that is no mission), interactive (Owner chat under the roots: attributed, never productive spend).
    Material spend no role/ledger entry explains is a telemetry failure, not a rounding error."""
    ent = read_index().get(goal)
    if ent is None:
        return {"ok": False, "goal": goal, "reason": f"UNKNOWN: goal {goal!r} is not declared"}
    material = MATERIAL_TOKENS if material is None else material
    mission_sids = set(mission_sids or ())
    roots = list(ent.get("roots") or [])
    led = _goal_ledger(goal)
    with led._lock:
        g = led._gfold(led._read())
    proot = projects or projects_root()
    in_ledger = set(g["marks"]) | {r["sid"] for r in g["res"].values()}
    on_disk: dict[str, Path] = {}
    for r in roots:
        enc = encode_cwd(r).lower()      # roots are stored lowercased (_norm); dir names keep their case
        for d in (sorted(proot.iterdir()) if proot.is_dir() else []):
            if not (d.is_dir() and (d.name.lower() == enc or d.name.lower().startswith(enc + "--"))):
                continue
            for p in d.glob("*.jsonl"):
                on_disk[p.stem] = p
    sids = sorted(in_ledger | mission_sids | set(on_disk))
    rows, failures = [], []
    unknown = 0
    for sid in sids:
        tx = on_disk.get(sid) or find_transcript(sid, proot)
        try:
            a = _session_autopsy(tx, roots) if tx else None
        except OSError:
            a = None
        mark = int(g["marks"].get(sid, 0))
        if sid in mission_sids:
            role = "worker"
        elif sid in in_ledger:
            role = "control"
        elif a and a["human_prompts"] > 0:
            role = "interactive"
        else:
            role = "unattributed"
        proc = a["processed"] if a else None
        row = {"sid": sid, "role": role, "settled": mark, "processed": proc, "transcript": a is not None}
        rows.append(row)
        if role in ("worker", "control") and a is None and (sid in in_ledger):
            unknown += mark          # the ledger holds a charge nobody can re-measure
            row["unknown"] = mark
        if role == "unattributed" and proc is not None and proc >= material:
            unknown += proc
            row["unknown"] = proc
            failures.append({"sid": sid, "kind": "unattributed_material_spend", "processed": proc})
        if role == "worker" and sid not in in_ledger and proc is not None and proc >= material:
            unknown += proc
            row["unknown"] = proc
            failures.append({"sid": sid, "kind": "worker_not_in_ledger", "processed": proc})
    cap = g["cap"]
    reserved = int(g["open"])
    settled = int(sum(g["marks"].values()))
    avail = None if cap is None else cap - settled - reserved - unknown
    prod = lambda k: sum(r["settled"] for r in rows if r["role"] == k)
    return {"ok": True, "goal": goal, "cap": cap, "settled": settled, "reserved": reserved,
            "unknown": unknown, "available": avail, "available_certain": unknown == 0,
            "productive": {"worker": prod("worker"), "control": prod("control")},
            "interactive_processed": sum(r["processed"] or 0 for r in rows if r["role"] == "interactive"),
            "telemetry_ok": not failures, "telemetry_failures": failures, "sessions": rows}


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
    gp = sub.add_parser("goal-prebind")
    gp.add_argument("--goal", required=True)
    gp.add_argument("--session", required=True)
    gp.add_argument("--measured", type=int, required=True)
    gt = sub.add_parser("goal-settle")
    gt.add_argument("--goal", required=True)
    gt.add_argument("--session", required=True)
    gt.add_argument("--measured", type=int)
    gc = sub.add_parser("goal-correct")
    gc.add_argument("--goal", required=True)
    gc.add_argument("--session", required=True)
    gc.add_argument("--measured", type=int, required=True)
    gc.add_argument("--reason", required=True)
    gc.add_argument("--owner", action="store_true")
    gs = sub.add_parser("goal-status")
    gs.add_argument("--goal", required=True)
    ga = sub.add_parser("goal-autopsy")
    ga.add_argument("--goal", required=True)
    ga.add_argument("--projects")
    ga.add_argument("--table", action="store_true")
    gl = sub.add_parser("goal-lease-open")
    gl.add_argument("--goal", required=True)
    gl.add_argument("--succession-id", required=True)
    gl.add_argument("--cap", type=int, required=True)
    gl.add_argument("--prev-lease", help="the lease being succeeded; refused if it is not the latest (CAS)")
    for k in ("proof", "closeout", "recovery"):
        gl.add_argument(f"--{k}", type=int, default=0)
    sub.add_parser("goal-lineage").add_argument("--goal", required=True)
    sub.add_parser("programme-status").add_argument("--goal", required=True)
    ps = sub.add_parser("programme-spend")
    ps.add_argument("--goal", required=True)
    ps.add_argument("--projects")
    gg = sub.add_parser("goal-programme")
    gg.add_argument("--goal", required=True)
    gg.add_argument("--value", type=int, required=True)
    gg.add_argument("--source", required=True)
    gg.add_argument("--owner", action="store_true",
                    help="raise the programme: asks you to type the goal id on an interactive terminal")
    gs = sub.add_parser("goal-succession")                   # D28 Ph1b: automatic successor leases
    gs.add_argument("--goal", required=True)
    gs.add_argument("--tranche", type=int, required=True, help="cap of each automatic lease; 0 turns it off")
    gs.add_argument("--keep", type=int, default=0, help="programme held back, never opened automatically")
    gs.add_argument("--source", required=True)
    gs.add_argument("--owner", action="store_true",
                    help="enable or loosen: asks you to type the goal id on an interactive terminal")
    for name in ("capital-apply", "capital-revoke"):         # OCA: Owner Capital Authority
        cp = sub.add_parser(name)
        cp.add_argument("--packet", required=True)
        cp.add_argument("--transcript", required=True)
        cp.add_argument("--goal", required=True)
    sub.add_parser("capital-status")
    sub.add_parser("capital-apply-pending")
    sub.add_parser("session-tree", help="cost tree of one session: main + subagents, deduped by message id"
                   ).add_argument("--transcript", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "session-tree":
        print(json.dumps(session_tree_report(Path(a.transcript)), indent=1))
        return 0
    if a.cmd.startswith("capital-"):
        import sys as _sys
        _repo = str(Path(__file__).resolve().parents[1])
        if _repo not in _sys.path:
            _sys.path.insert(0, _repo)
        from modules.provider_routing import capital_authority as ca
        try:
            if a.cmd == "capital-status":
                out = ca.status()
            elif a.cmd == "capital-apply-pending":
                res = ca.apply_pending(_goal_ledger)
                cor = correction_apply_pending(_goal_ledger)
                out = {"ok": all(r["ok"] for r in res + cor), "results": res, "corrections": cor}
            else:
                fn = ca.apply if a.cmd == "capital-apply" else ca.revoke
                r = fn(a.packet, a.transcript, a.goal, _goal_ledger)
                out = {k: v for k, v in r.items() if k != "row"}
        except (OSError, ValueError, KeyError) as exc:      # a refusal is data, never a traceback
            out = {"ok": False, "reason": f"{type(exc).__name__}: {exc}"[:300]}
        print(json.dumps(out, sort_keys=True))
        return 0 if out.get("ok") else 3
    if a.cmd == "programme-spend":
        sids: set[str] = set()
        try:
            import gsd_mission as _gm
            for r in _gm.all_missions():
                if goal_for_cwd(r.get("cwd")) == a.goal and (r.get("owner") or {}).get("session_id"):
                    sids.add(r["owner"]["session_id"])
        except Exception:  # noqa: BLE001 -- no mission store: roles degrade to control/interactive
            pass
        out = programme_spend(a.goal, projects=Path(a.projects) if a.projects else None, mission_sids=sids)
        print(json.dumps(out, sort_keys=True))
        return 0 if out.get("ok") and out.get("telemetry_ok") else 3
    if a.cmd in ("goal-lineage", "programme-status", "goal-lease-open", "goal-programme", "goal-succession"):
        led = _goal_ledger(a.goal)
        if a.cmd == "goal-lineage":
            out = led.lineage()          # read-only: never status(), which appends leak rows
        elif a.cmd == "programme-status":
            out = led.programme_status()
        elif a.cmd == "goal-lease-open":
            out = led.lease_open(a.succession_id, a.cap, prev_lease=a.prev_lease,
                                 reserves={"proof": a.proof, "closeout": a.closeout, "recovery": a.recovery})
        else:
            owner = False
            if a.owner:
                if not _real_console_stdin():
                    print(json.dumps({"ok": False, "goal": a.goal,
                                      "reason": "--owner needs an interactive terminal (stdin is not a TTY)"}))
                    return 3
                what = "succession policy" if a.cmd == "goal-succession" else "programme"
                owner = input(f"Owner change to {what} of {a.goal!r}: type the goal id to confirm: ").strip() == a.goal
            unprivileged = not (owner and not inside_agent())
            if a.cmd == "goal-succession":
                out = led.set_succession(a.tranche, a.keep, a.source, inside_agent=unprivileged)
            else:
                out = led.set_programme(a.value, a.source, inside_agent=unprivileged)
        print(json.dumps(out, sort_keys=True))
        return 0 if out.get("ok") else 3
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
        elif a.cmd == "goal-prebind":
            out = goal_prebind(a.goal, a.session, a.measured)
        elif a.cmd == "goal-settle":
            out = goal_settle(a.goal, a.session, a.measured)
        elif a.cmd == "goal-correct":
            if not a.owner or not _real_console_stdin():
                print(json.dumps({"ok": False, "goal": a.goal,
                                  "reason": "goal-correct needs --owner on an interactive terminal "
                                  "(stdin is not a TTY)"}))
                return 3
            if input(f"Owner correction of goal {a.goal!r}: type the goal id to confirm: ").strip() != a.goal:
                print(json.dumps({"ok": False, "goal": a.goal, "reason": "not confirmed"}))
                return 3
            out = goal_correct(a.goal, a.session, a.measured, a.reason, "owner-tty")
        elif a.cmd == "goal-autopsy":
            out = goal_autopsy(a.goal, projects=Path(a.projects) if a.projects else None)
            if a.table and out.get("ok"):
                print(autopsy_table(out), end="")
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
