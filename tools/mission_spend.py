"""Mission cost circuit breaker (TOK-18 gen 2 D1).

A mission's budget was cycles and hours only (`gsd_mission.budget_exhausted`), so nothing saw tokens:
E1 (m-f011d7fdebc9) was estimated at 17M processed tokens and ran to 141M, 93 % Opus, before anything
stopped it. This module gives a mission an optional token envelope, measured deterministically from
its own transcripts. No model reads anything here.

Unit: processed tokens = input + cache_write + cache_read + output under the canonical rule: the last
copy of each (message.id, requestId) per transcript, per-column maximum across transcripts, synthetic
rows excluded, subagent transcripts included, counted from the mission's `created_at`.

NAMED DEBT (Phase 5): hooks/session_budget_guard.js, _file_tokens and session_tokens still keep the first
copy of each message id and read the main transcript only, so they undercount by 0.8 - 1.0 % (streaming)
plus all subagent tokens; they are pinned by V-SBG-REAL-PARITY (tools/test_session_budget_guard.py:242)
and are NOT changed in Phase 1.

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
import stat as stat_mod
import time
import datetime as dt
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


def _n(v) -> int:
    """A transcript field as a count: the value when it is an int (not a bool) and >= 0, else 0."""
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else 0


def _ts_epoch(s):
    """ISO-8601 string (Z or offset) to epoch seconds; None when it is not one."""
    if not isinstance(s, str) or len(s) < 19:
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.timestamp()


def _epoch_ts(e: float) -> str:
    return dt.datetime.fromtimestamp(e, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _since_iso(rec: dict) -> str | None:
    if rec.get("created_at"):
        return dt.datetime.fromtimestamp(float(rec["created_at"]), dt.timezone.utc).isoformat()[:19]
    return None


def _dirs_both_planes(rec: dict, root: Path) -> list[Path]:
    # Both planes: the host files a worker's transcript under the dir it was LAUNCHED in (cwd), while the
    # work may live in a worktree (work_dir). Measured 2026-10-06, m-e935055d072d: work_dir alone found no
    # directory, so a 3,353,877-token worker read as unmeasurable and its breaker was blind.
    dirs: list[Path] = []
    for base in (rec.get("work_dir"), rec.get("cwd")):
        for d in (mission_dirs(base, root) if base else []):
            if d not in dirs:
                dirs.append(d)
    return dirs


def _session_of(path: Path, base: Path, ids: set[str], prefixes: set[str]) -> str | None:
    """The session a transcript belongs to: its own stem, or a directory between the project directory
    and it (`<sid>/subagents/agent-*.jsonl`), that is in ids or starts with a prefix. Names are only compared."""
    names = [path.stem] + [p.name for p in path.relative_to(base).parents if p.name]
    for n in names:
        if n in ids or any(n.startswith(px) for px in prefixes):
            return n
    return None


def _attributed(path: Path, base: Path, ids: set[str], prefixes: set[str]) -> bool:
    return _session_of(path, base, ids, prefixes) is not None


def _read_file(path: Path, st, cache: dict | None) -> dict:
    """Unfiltered per-call tuples of one transcript, cached by size and mtime. Entry: {size, mtime, calls}
    with calls = {key: (input, cache_write, cache_read, output, cw5, cw1, ts, model)}."""
    k = str(path)
    hit = cache.get(k) if cache is not None else None
    if hit and hit.get("size") == st.st_size and hit.get("mtime") == st.st_mtime \
            and isinstance(hit.get("calls"), dict):
        return hit
    import tis_observed   # lazy attribute call: a drill mutant of tis_observed is the one that runs
    calls, _end, _ep = tis_observed.calls_from(path, 0)
    out: dict = {}
    for c in calls:
        u = c.get("usage") or {}
        key = c.get("key")
        if isinstance(key, tuple) and len(key) == 2 and key[0] == "off":
            key = ("off", k, key[1])
        cc = u.get("cache_creation")
        cw5 = _n(cc.get("ephemeral_5m_input_tokens")) if isinstance(cc, dict) else 0
        cw1 = _n(cc.get("ephemeral_1h_input_tokens")) if isinstance(cc, dict) else 0
        out[key] = (_n(u.get("input_tokens")), _n(u.get("cache_creation_input_tokens")),
                    _n(u.get("cache_read_input_tokens")), _n(u.get("output_tokens")),
                    cw5, cw1, c.get("ts"), c.get("model") or "")
    entry = {"size": st.st_size, "mtime": st.st_mtime, "calls": out}
    if cache is not None:
        cache[k] = entry
    return entry


def usage_truth(rec: dict, root: Path | None = None, cache: dict | None = None,
                sessions: tuple[set[str], set[str]] | None = None, now: float | None = None) -> dict | None:
    """The canonical reader of a mission's spend, or None when it cannot be measured (no transcript
    directory, or no session attributable: absence is not zero). Per transcript the last copy of each
    (message.id, requestId) wins and synthetic rows are excluded; across transcripts the per-column
    maximum wins. Main transcripts are read before subagents. The since filter applies after the merge."""
    root = root or projects_root()
    dirs = _dirs_both_planes(rec, root)
    if not dirs:
        return None
    ids, prefixes = sessions if sessions is not None else mission_sessions(rec)
    if not ids and not prefixes:
        return None
    since = _since_iso(rec)
    files = []
    for d in dirs:
        for p in d.rglob("*.jsonl"):
            nm = _session_of(p, d, ids, prefixes)
            if nm is not None:
                files.append((p, nm))
    files.sort(key=lambda p: (p[0].parent.name == "subagents", str(p[0])))
    merged: dict = {}
    read_n = unreadable = 0
    mtime_max = None
    sess_b: dict = {}
    sub_b: dict = {}
    for p, name in files:
        is_sub = p.parent.name == "subagents"
        (sub_b if is_sub else sess_b).setdefault(name, None)
        try:
            st = p.stat()
            if not stat_mod.S_ISREG(st.st_mode):
                raise OSError("not a regular file")
            calls = _read_file(p, st, cache)["calls"]
        except OSError:
            unreadable += 1   # skipped, never zero: the truth is then a lower bound
            continue
        read_n += 1
        mtime_max = st.st_mtime if mtime_max is None else max(mtime_max, st.st_mtime)
        for key, t in calls.items():
            m = merged.get(key)
            if m is None:
                merged[key] = [list(t), is_sub, name]
                continue
            m = m[0]
            for i in range(6):
                m[i] = max(m[i], t[i])
            a, b = _ts_epoch(m[6]), _ts_epoch(t[6])
            if (a is None and t[6]) or (a is not None and b is not None and b > a):
                m[6] = t[6]

    def _new() -> dict:
        return {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0, "processed": 0, "calls": 0,
                "_last": None}

    def _add(b: dict, m: list) -> None:
        b["input"] += m[0]
        b["cache_write"] += m[1]
        b["cache_read"] += m[2]
        b["output"] += m[3]
        b["calls"] += 1
        e = _ts_epoch(m[6])
        if e is not None and (b["_last"] is None or e > b["_last"]):
            b["_last"] = e

    tree = _new()
    sessions_out = {n: _new() for n in sess_b}
    subs_out = {n: _new() for n in sub_b}
    by_model: dict = {}
    for (m, is_sub, name) in merged.values():
        if since and (m[6] or "") < since:
            continue
        _add(tree, m)
        _add((subs_out if is_sub else sessions_out)[name], m)
        bm = by_model.setdefault(m[7], {"calls": 0, "input": 0, "cache_write": 0, "cache_read": 0,
                                        "output": 0, "cw5": 0, "cw1": 0})
        bm["calls"] += 1
        for i, c in enumerate(("input", "cache_write", "cache_read", "output", "cw5", "cw1")):
            bm[c] += m[i]
    last_epoch = tree["_last"]
    for b in [tree, *sessions_out.values(), *subs_out.values()]:
        b["processed"] = b["input"] + b["cache_write"] + b["cache_read"] + b["output"]
        b["last_call_ts"] = None if b["_last"] is None else _epoch_ts(b["_last"])
        del b["_last"]
    tree["last_call_epoch"] = last_epoch
    return {"measured_at": time.time() if now is None else now, "since": since,
            "files": read_n, "unreadable": unreadable, "files_mtime_max": mtime_max, "tree": tree,
            "sessions": sessions_out, "subagents": subs_out, "by_model": by_model}


def truth_age(truth: dict, now: float) -> dict:
    """Three separate ages (seconds) of a usage_truth result; each None when its source is None. Pure."""
    def _age(v):
        return None if v is None else now - v
    return {"measured_age_s": _age(truth.get("measured_at")),
            "last_call_age_s": _age((truth.get("tree") or {}).get("last_call_epoch")),
            "files_age_s": _age(truth.get("files_mtime_max"))}


def processed_tokens(rec: dict, root: Path | None = None, cache: dict | None = None,
                     sessions: tuple[set[str], set[str]] | None = None) -> int | None:
    """Processed tokens the mission's OWN sessions have spent, or None when it cannot be measured:
    no transcript directory, or no session attributable to the mission (absence is not zero).
    Int projection of usage_truth. Unit rule: last copy per (message.id, requestId) per transcript and
    per-column maximum across transcripts; the breaker therefore reads about 1 % higher than the old
    first-copy rule and trips about 1 % earlier (accepted). `sessions` overrides `mission_sessions(rec)`.
    `cache` maps a transcript path to its per-key tuples; unchanged files are not re-read."""
    t = usage_truth(rec, root, cache, sessions)
    return None if t is None else t["tree"]["processed"]


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


def judge_predictive(rec: dict, spent: int | None, p95_remaining: float | None, tail: float = 0) -> dict:
    """{drain: reason|None}. Pure. Fires when spent + P95 remaining + tail > authority; missing data never drains."""
    est = rec.get("token_estimate")
    if not est or spent is None or p95_remaining is None:
        return {"drain": None}
    est = int(est)
    ratio = float(rec.get("token_trip_ratio") or DEFAULT_TRIP_RATIO)
    authority = est * ratio
    tail = tail or 0
    if spent + p95_remaining + tail > authority:
        return {"drain": (f"predictive drain: spent {spent:,} + P95 remaining {int(p95_remaining):,} + tail {int(tail):,} "
                          f"> authority {int(authority):,}; spend may continue until the hard breaker; "
                          "new work is not started")}
    return {"drain": None}


# Liveness verdicts as plan_next computes them. They mirror gsd_mission.py LIVE/WAITING_HUMAN/DEAD/UNKNOWN;
# this module must not import gsd_mission at import time (a gate pins the equality).
V_LIVE = "ALIVE"
V_BLOCKED = "BLOCKED"
V_DEAD = "DEAD"
V_UNKNOWN = "UNKNOWN"


def format_age(seconds) -> str:
    """Closed age format: 45s, 1m, 2h02m, 3d1h; None is 'unknown'; negative clamps to zero."""
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        return "unknown"
    s = int(max(0, seconds))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 86400}d{(s % 86400) // 3600}h"


def snapshot_of(truth, spent=None, now=None):
    """JSON-safe measured snapshot (numbers and strings only). The truth wins over `spent`."""
    if isinstance(truth, dict):
        tr = truth.get("tree") or {}
        return {"processed": tr.get("processed"), "input": tr.get("input"),
                "cache_write": tr.get("cache_write"), "cache_read": tr.get("cache_read"),
                "output": tr.get("output"), "calls": tr.get("calls"),
                "measured_at": truth.get("measured_at"), "last_call_ts": tr.get("last_call_ts"),
                "files_mtime_max": truth.get("files_mtime_max"), "files": truth.get("files"),
                "unreadable": truth.get("unreadable")}
    if spent is None:
        return None
    return {"processed": spent, "input": None, "cache_write": None, "cache_read": None, "output": None,
            "calls": None, "measured_at": now, "last_call_ts": None, "files_mtime_max": None,
            "files": None, "unreadable": None}


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def spend_statement(snap, verdicts, now, fresh=False) -> str:
    """One sentence from a closed set; pure. 'final' is printed only for a fresh measurement: a stored
    snapshot was not re-measured, so it says calls after T are not counted."""
    nm = "spend UNKNOWN (not measurable)"
    if not isinstance(snap, dict) or snap.get("files") == 0:
        return nm
    x = snap.get("processed")
    if not isinstance(x, int) or isinstance(x, bool) or x < 0:
        return nm
    mat = snap.get("measured_at")
    t = _epoch_ts(mat) if _num(mat) else "an unknown time"
    age = format_age(now - mat) if _num(mat) and _num(now) else "unknown"
    head = f"measured {x:,} as of {t} (age {age}); "
    unread = snap.get("unreadable")
    if _num(unread) and unread > 0:
        return head + f"{int(unread)} transcript(s) unreadable -> total UNKNOWN, >= {x:,}"
    vs = [v[0] if isinstance(v, (tuple, list)) and v else v for v in (verdicts or [])]
    if V_LIVE in vs:
        return head + f"worker LIVE -> total current UNKNOWN, >= {x:,}"
    if not vs or any(v != V_DEAD for v in vs):
        return head + f"worker liveness UNKNOWN -> total current UNKNOWN, >= {x:,}"
    last = snap.get("last_call_ts") or "unknown"
    if fresh:
        return head + f"no live worker -> {x:,} is final as of last call {last}"
    return head + (f"no live worker -> {x:,} was the total as of last call {last}; "
                   f"calls after {t} not counted (not re-measured)")


def hold_text(hold, verdicts, now, limit=None) -> str:
    """Body of an owner-hold sentence (callers keep their own 'owner hold: ' prefix); pure."""
    h = hold if isinstance(hold, dict) else {}
    prose = str(h.get("reason"))
    if limit is not None:
        prose = prose[:limit]
    sa = h.get("set_at")
    t = _epoch_ts(sa) if _num(sa) else "an unknown time"
    age = format_age(now - sa) if _num(sa) and _num(now) else "unknown"
    meas = h.get("measured")
    tail = spend_statement(meas, verdicts, now) if isinstance(meas, dict) else "not re-measured"
    return f"recorded at {t} (age {age}): {prose}; {tail}"


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


def goal_settle(goal: str, sid: str, measured: int | None = None, reason: str = "goal-settle",
                transcripts_root: Path | None = None) -> dict:
    """Settle a STOPPED session and close all of its holds (never reserves). Blind -> refused."""
    if not _SID_RE.match(sid or ""):
        raise ValueError(f"invalid session id: {sid!r}")
    if measured is None:
        tp = find_transcript(sid, transcripts_root)
        if tp is None:
            return {"ok": False, "goal": goal, "reason": "no transcript for the session and no --measured: "
                    "refusing to settle blind"}
        measured = int(session_tokens(tp)["tokens"])
    return _goal_ledger(goal).settle_stopped(sid, int(measured), reason)


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
    return _goal_ledger(goal).renew(sid, measured, int(e.get("lease_calls") or GOAL_LEASE_CALLS) * pc, per_call=pc)


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



def goal_prebind(goal: str, sid: str, measured: int) -> dict:
    """Journal op {op:"prebind", sid, measured, goal}: PRE_BINDING_PROGRAM_CAPEX, never goal spend."""
    if not _SID_RE.match(sid or ""):
        return {"ok": False, "goal": goal, "reason": f"invalid session id: {sid!r}"}
    return _goal_ledger(goal).prebind(sid, int(measured))


# --- Prospective binding: Python twin of hooks/lib/goal_binding.js (same precedence, same record) ----
def prospective_bind() -> bool:
    """CPP_PROSPECTIVE_BIND=0|off|false restores the old (retroactive, cwd-by-lookup) behaviour."""
    return os.environ.get("CPP_PROSPECTIVE_BIND", "").strip().lower() not in ("0", "off", "false")


def binding_path(sid: str) -> Path:
    return state_dir() / "goal-binding" / f"{sid}.json"


def _now_ts() -> str:
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def read_binding(sid: str) -> dict | None:
    try:
        r = json.loads(binding_path(sid).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return r if isinstance(r, dict) and isinstance(r.get("goal"), str) and r["goal"] else None


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
    r"""|(?:['"]?[^\s'"]*[\\/])?(?:python3?|py)(?:\.exe)?['"]?\s+['"]?(?:[^\s'"]*[\\/])?mission_spend\.py['"]?\s+goal-status\b)""",
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
    seen, calls, processed, bound, refusals = set(), 0, 0, 0, 0
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
            "refusals": refusals, "role": "worker" if _under(first_cwd, roots) else "pane"}


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
    au = sub.add_parser("autopsy")
    au.add_argument("--mission", required=True)
    au.add_argument("--stall-seconds", type=int, default=DEFAULT_STALL_SECONDS)
    au.add_argument("--root", help="transcript projects root (default: ~/.claude/projects)")
    fc = sub.add_parser("forecast")
    fc.add_argument("--rows", required=True, help="JSON file: a list of obligation rows")
    gl =sub.add_parser("goal-lease-open")
    gl.add_argument("--goal", required=True)
    gl.add_argument("--succession-id", required=True)
    gl.add_argument("--cap", type=int, required=True)
    gl.add_argument("--prev-lease", help="the lease being succeeded; refused if it is not the latest (CAS)")
    for k in ("proof", "closeout", "recovery"):
        gl.add_argument(f"--{k}", type=int, default=0)
    sub.add_parser("goal-lineage").add_argument("--goal", required=True)
    sub.add_parser("programme-status").add_argument("--goal", required=True)
    gg = sub.add_parser("goal-programme")
    gg.add_argument("--goal", required=True)
    gg.add_argument("--value", type=int, required=True)
    gg.add_argument("--source", required=True)
    gg.add_argument("--owner", action="store_true",
                    help="raise the programme: asks you to type the goal id on an interactive terminal")
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
    if a.cmd in ("goal-lineage", "programme-status", "goal-lease-open", "goal-programme"):
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
                owner = input(f"Owner change to programme of {a.goal!r}: type the goal id to confirm: ").strip() == a.goal
            out = led.set_programme(a.value, a.source, inside_agent=not (owner and not inside_agent()))
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
