#!/usr/bin/env python3
"""usage_index.py -- incremental usage index + estate burn alarm (C1).

Plan: vault/plans/cognitive-control-plane-2026-10-02.md (C1, audit G6/G7).
Incident: vault/plans/weekly-limit-burn-rca-2026-10-02.md.

Why it exists. The old alarm (cost_gate.weekly_burn) watched OUTPUT only, while
cache re-reads were ~98 % of tokens in the 2026-09-30..10-02 incident, and it
re-scanned the whole transcript corpus (6.8 GB / 2,940 files for three weeks)
under a 40 s budget that failed open to silence. This module keeps a SQLite index
that reads only the bytes appended since the last pass, prices EVERY usage
category per model, and reports a typed state. It never reports silence for a
failed look: a refresh that did not finish, or an index that is stale, is
MONITOR_FAILURE.

Parser: tis_observed.calls_from (the incremental twin of tis_observed._calls_in;
same filters, same identity). Calls are deduplicated across files by
(message.id, requestId); a streamed call keeps its largest output.

Unit: API-equivalent USD from the dated pricing file. It is NOT the subscription
meter: the meter's weighting is UNKNOWN. A percentage is shown only through a
calibration made from an Owner meter reading paired with a measured window, and
it is labelled ESTIMATED.

CLI:
  refresh [--deadline S]          index new bytes (default 600 s for a first build)
  window START END                aggregate for an ISO interval
  burn                            refresh (bounded) + current state
  replay --at ISO [--step-h 1]    state at past instants, from the index only
  holdout                         calibrate on pair A, score on pair B (done-gate G6)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PP_ROOT = _HERE.parent
for _p in (str(_HERE), str(_PP_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import tis_observed as _tis  # noqa: E402
from pricing_source import current_pricing_path  # noqa: E402

DEFAULT_DB = Path(os.environ.get(
    "CPP_USAGE_INDEX", Path.home() / ".claude" / "state" / "usage_index" / "index.sqlite"))
DEFAULT_PROJ = Path.home() / ".claude" / "projects"
METER_FILE = _PP_ROOT / "vault" / "config" / "weekly_meter_readings.json"

# Typed states, ordered by severity.
STATES = ("NORMAL", "ELEVATED", "CONSTRAINED", "CRITICAL")
MONITOR_FAILURE = "MONITOR_FAILURE"
STALE_AFTER_S = float(os.environ.get("CPP_USAGE_INDEX_STALE_S", "7200"))
RATE_WINDOW_H = 6.0
ANOMALY_FACTOR = 1.5      # 24 h rate vs the median daily rate of the prior 14 days

SCHEMA_VERSION = 4
V2 = 2          # the version whose upgrade re-reads every file; never re-run for a later bump
SCHEMA = """
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, offset INTEGER, size INTEGER,
  mtime_ns INTEGER, is_sub INTEGER, entrypoint TEXT);
CREATE TABLE IF NOT EXISTS calls(k TEXT PRIMARY KEY, file TEXT, ts REAL, model TEXT,
  is_sub INTEGER, entrypoint TEXT, inp INTEGER, cw INTEGER, cw5 INTEGER, cw1 INTEGER,
  cr INTEGER, out INTEGER);
CREATE INDEX IF NOT EXISTS calls_ts ON calls(ts);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
-- v2 (C1b/C2): provider quota events and causal ancestry.
CREATE TABLE IF NOT EXISTS quota(file TEXT, off INTEGER, ts REAL, type TEXT, status TEXT,
  resets_at REAL, overage_reason TEXT, PRIMARY KEY(file, off));
CREATE INDEX IF NOT EXISTS quota_ts ON quota(ts);
CREATE TABLE IF NOT EXISTS prompts(prompt_id TEXT PRIMARY KEY, session TEXT, file TEXT,
  ts REAL, kind TEXT, source TEXT, is_sub INTEGER);
CREATE TABLE IF NOT EXISTS spawns(tool_use_id TEXT PRIMARY KEY, parent_k TEXT, session TEXT,
  ts REAL, subagent_type TEXT, model_req TEXT, prompt_id TEXT, file TEXT,
  result_ts REAL, is_error INTEGER, result_head TEXT, input_hash TEXT);
CREATE TABLE IF NOT EXISTS subagents(file TEXT PRIMARY KEY, session TEXT, agent_type TEXT,
  tool_use_id TEXT, depth INTEGER, model_meta TEXT);
"""
_V2_COLUMNS = (("calls", "session", "TEXT"), ("calls", "prompt_id", "TEXT"),
               ("calls", "agent_id", "TEXT"), ("files", "cur_prompt", "TEXT"),
               ("files", "title", "TEXT"))


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _epoch(s) -> float | None:
    if isinstance(s, (int, float)):
        return float(s)
    if not isinstance(s, str) or len(s) < 19:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()


def connect(db: Path = DEFAULT_DB) -> sqlite3.Connection:
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db), timeout=30)
    con.executescript(SCHEMA)
    row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    # Only the v1 -> v2 upgrade re-reads every file. Later versions migrate inside
    # refresh() (_migrate_v3): a reader must never trigger a write-locked rewrite
    # (audit G2), and comparing against SCHEMA_VERSION here would re-run this
    # full re-read on every future bump.
    if row is None or int(row[0]) < V2:
        for table, col, typ in _V2_COLUMNS:
            have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
            if col not in have:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
        # Backfill: re-read every file from byte 0 so ancestry and quota rows exist
        # for history. Call rows are upserts on the same key, so totals cannot move.
        con.execute("UPDATE files SET offset=0, size=-1, cur_prompt=NULL")
        con.execute("INSERT OR REPLACE INTO meta VALUES('schema_version', ?)", (str(V2),))
        con.commit()
    return con


# v3 (audit G4): spawn outcomes. v4 (audit G7): input_hash, the equivalence key of a
# spawn request, stored at index time so a pre-spawn policy can ask "is an equivalent
# spawn already running?" without reading transcripts.
_SPAWN_COLUMNS = (("result_ts", "REAL"), ("is_error", "INTEGER"), ("result_head", "TEXT"),
                  ("input_hash", "TEXT"))
RESULT_HEAD = 200       # chars of the parent's tool_result kept per spawn


def spawn_input_hash(inp: dict) -> str:
    """Equivalence key of a spawn request: requested agent type + exact prompt text.
    Exact by design: a near-duplicate is NOT equivalent (no fuzzy merging of work)."""
    raw = f"{inp.get('subagent_type') or ''}\0{inp.get('prompt') or ''}"
    return hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:16]


def _migrate_spawns(con) -> None:
    """-> v4: adds any missing spawn columns and queues ONLY the transcripts that hold
    a spawn lacking a result or an input hash for a backfill; no file offset is
    touched, so totals cannot move (audit G2). One BEGIN IMMEDIATE, version
    re-checked inside it, so two concurrent refreshes migrate once."""
    row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    if row is not None and int(row[0]) >= SCHEMA_VERSION:
        return
    con.commit()
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
        if row is None or int(row[0]) < SCHEMA_VERSION:
            have = {r[1] for r in con.execute("PRAGMA table_info(spawns)")}
            for col, typ in _SPAWN_COLUMNS:
                if col not in have:
                    con.execute(f"ALTER TABLE spawns ADD COLUMN {col} {typ}")
            old = json.loads((con.execute("SELECT v FROM meta WHERE k='spawn_backfill'")
                              .fetchone() or ["[]"])[0])
            todo = sorted(set(old) | {r[0] for r in con.execute(
                "SELECT DISTINCT file FROM spawns WHERE (result_ts IS NULL OR input_hash IS NULL) "
                "AND file IS NOT NULL")})
            con.execute("INSERT OR REPLACE INTO meta VALUES('spawn_backfill', ?)", (json.dumps(todo),))
            con.execute("INSERT OR REPLACE INTO meta VALUES('schema_version', ?)",
                        (str(SCHEMA_VERSION),))
        con.commit()
    except BaseException:
        con.rollback()
        raise


def _spawn_results(con, o: dict) -> None:
    """Record the parent's tool_result for any spawn it answers. A user line that
    carries a tool_result may ALSO carry a promptId, so this runs before that branch.
    First result wins; an id that is not a spawn updates nothing."""
    msg = o.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, list):
        return
    ts = _epoch(o.get("timestamp"))
    for c in content:
        if not (isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id")):
            continue
        body = c.get("content")
        if isinstance(body, list):
            body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
        con.execute("UPDATE spawns SET result_ts=?, is_error=?, result_head=? "
                    "WHERE tool_use_id=? AND result_ts IS NULL",
                    (ts, 1 if c.get("is_error") else 0, str(body or "").strip()[:RESULT_HEAD],
                     c["tool_use_id"]))


def _spawn_hashes(con, o: dict) -> None:
    """Backfill only: input_hash for spawns recorded before v4."""
    msg = o.get("message") if isinstance(o.get("message"), dict) else {}
    for c in msg.get("content") or []:
        if (isinstance(c, dict) and c.get("type") == "tool_use"
                and c.get("name") in SPAWN_TOOLS and c.get("id")):
            inp = c.get("input") if isinstance(c.get("input"), dict) else {}
            con.execute("UPDATE spawns SET input_hash=? WHERE tool_use_id=? AND input_hash IS NULL",
                        (spawn_input_hash(inp), c["id"]))


def _backfill_spawns(con, t_end: float) -> int:
    """Resumable one-time scan of the queued transcripts for spawn results.
    Returns how many files remain; bounded by the caller's deadline."""
    row = con.execute("SELECT v FROM meta WHERE k='spawn_backfill'").fetchone()
    todo = json.loads(row[0]) if row else []
    while todo and time.monotonic() < t_end:
        fp = todo[0]
        try:
            with open(fp, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    is_result = '"tool_result"' in line
                    if not (is_result or any(f'"{t}"' in line for t in SPAWN_TOOLS)):
                        continue
                    try:
                        o = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(o, dict):
                        continue
                    if o.get("type") == "user" and is_result:
                        _spawn_results(con, o)
                    elif o.get("type") == "assistant":
                        _spawn_hashes(con, o)
        except OSError:
            pass                                    # gone: its spawns stay without a result
        todo.pop(0)
        con.execute("INSERT OR REPLACE INTO meta VALUES('spawn_backfill', ?)", (json.dumps(todo),))
        con.commit()
    return len(todo)


# Store identity is CONSUMED, never derived here: `tis_observed.store_identity` is the
# one producer (resolved path; a link's listed spelling is an alias of it, including a
# link to a dir outside the store). Until 2026-10-03 this module carried its own copy,
# which kept an out-of-store link under its own spelling while every other consumer
# used the resolved path: one fact, two answers.


def _iter_files(proj: Path):
    """(path, is_subagent), one spelling per physical transcript (store_identity)."""
    if not proj.is_dir():
        return
    for sub in _tis.store_identity(proj)[0]:
        for jf in sub.glob("*.jsonl"):
            yield jf, 0
        for jf in sub.glob("*/subagents/*.jsonl"):
            yield jf, 1


# Every column that carries a transcript path (audit G1, plus spawns.parent_k).
# (table, column, kind): "pk" columns may collide with a canonical twin, which wins;
# "key" columns embed the path after an `off|` prefix.
_PATH_COLUMNS = (("files", "path", "pk"), ("calls", "k", "key"), ("calls", "file", "plain"),
                 ("quota", "file", "pk"), ("prompts", "file", "plain"),
                 ("spawns", "file", "plain"), ("spawns", "parent_k", "key"),
                 ("subagents", "file", "pk"))


def _alias_rows(con, alias: str) -> int:
    n = 0
    for table, col, kind in _PATH_COLUMNS:
        pre = ("off|" + alias) if kind == "key" else alias
        n += con.execute(f"SELECT count(*) FROM {table} WHERE substr({col},1,?)=?",
                         (len(pre), pre)).fetchone()[0]
    return n


def _backup(con) -> dict:
    """sha256-verified snapshot of the index, taken before any row is rewritten."""
    db = Path(con.execute("PRAGMA database_list").fetchone()[2])
    bak = db.with_name(f"{db.stem}.identity-{int(time.time())}.bak")
    dst = sqlite3.connect(str(bak))
    con.backup(dst)
    dst.close()
    digest = hashlib.sha256(bak.read_bytes()).hexdigest()
    chk = sqlite3.connect(str(bak))
    try:
        integrity = chk.execute("PRAGMA integrity_check").fetchone()[0]
        n = chk.execute("SELECT count(*) FROM calls").fetchone()[0]
    finally:
        chk.close()
    live = con.execute("SELECT count(*) FROM calls").fetchone()[0]
    if integrity != "ok" or n != live:
        raise RuntimeError(f"identity backup unverified: integrity={integrity} rows {n}/{live}")
    return {"path": str(bak), "sha256": digest, "calls": n, "at": time.time()}


def _canonicalize(con, proj: Path) -> dict:
    """Rewrite rows recorded under an alias spelling to the canonical one.

    Runs only where alias rows exist, so a clean index costs one count per column.
    Destructive (alias duplicates are deleted), hence: a verified backup first, the
    alias map re-read from the filesystem after the backup (an alias that stopped
    resolving to its canonical dir is dropped), and every rewrite inside one
    BEGIN IMMEDIATE, so no other writer interleaves and a failure rolls back whole.
    A canonical twin always wins; an alias row without one moves whole. Re-reading
    a transcript afterwards is idempotent, so a discarded alias offset loses nothing."""
    if not proj.is_dir():
        return {"aliases": 0, "rewritten": 0}
    aliases = _tis.store_identity(proj)[1]
    todo = {a + os.sep: c + os.sep for a, c in aliases.items()
            if _alias_rows(con, a + os.sep)}
    if not todo:
        return {"aliases": len(aliases), "rewritten": 0}
    con.commit()
    bk = _backup(con)
    now = _tis.store_identity(proj)[1]             # re-authorize against the disk now
    todo = {a: c for a, c in todo.items() if now.get(a[:-1]) == c[:-1]}
    rewritten = 0
    con.execute("BEGIN IMMEDIATE")
    try:
        for a, c in todo.items():
            for table, col, kind in _PATH_COLUMNS:
                pa, pc = (("off|" + a, "off|" + c) if kind == "key" else (a, c))
                where = f"substr({col},1,{len(pa)})=?"
                verb = "UPDATE OR IGNORE" if kind in ("pk", "key") else "UPDATE"
                rewritten += con.execute(
                    f"{verb} {table} SET {col}=?||substr({col},{len(pa) + 1}) WHERE {where}",
                    (pc, pa)).rowcount
                if kind in ("pk", "key") and table != "spawns":
                    con.execute(f"DELETE FROM {table} WHERE {where}", (pa,))
        con.execute("INSERT OR REPLACE INTO meta VALUES('identity_backup', ?)", (json.dumps(bk),))
        con.execute("INSERT OR REPLACE INTO meta VALUES('identity_migration', ?)",
                    (json.dumps({"at": time.time(), "aliases": sorted(todo),
                                 "rewritten": rewritten}),))
        con.commit()
    except BaseException:
        con.rollback()
        raise
    return {"aliases": len(aliases), "rewritten": rewritten, "backup": bk["path"]}


def _key(fp: str, key) -> str:
    if key and key[0] == "off":
        return f"off|{fp}|{key[1]}"
    return f"{key[0]}|{key[1]}"


def _num(u: dict, k: str) -> int:
    v = u.get(k)
    return v if isinstance(v, int) and v >= 0 else 0


SPAWN_TOOLS = ("Agent", "Task")      # the harness renamed Task -> Agent; accept both


def _ancestry_line(con, path: str, is_sub: int, state: dict, o: dict, start: int) -> None:
    """Causal ancestry from one transcript line (C2). Never infers from time.

    - user line with promptId: the prompt every later call in this file belongs
      to, until the next promptId. The turn-opening line carries origin.kind /
      turnOrigin / promptSource (human, task-notification, peer, sdk, system).
    - assistant line: binds its call key to (session, prompt, agentId); an
      Agent/Task tool_use becomes a spawn row with the model the caller asked
      for (None = inherited from the parent -- the 53.5 % of RCA §6).
    - any line with quotaLimits: a provider-side quota event (C1b)."""
    t = o.get("type")
    ts = _epoch(o.get("timestamp"))
    if isinstance(o.get("quotaLimits"), dict):
        q = o["quotaLimits"]
        con.execute("INSERT OR IGNORE INTO quota VALUES(?,?,?,?,?,?,?)",
                    (path, start, ts, q.get("rateLimitType"), q.get("status"),
                     _epoch(q.get("resetsAt")), q.get("overageDisabledReason")))
    if t == "user":
        _spawn_results(con, o)
    if t == "user" and o.get("promptId"):
        pid = o["promptId"]
        state["prompt"] = pid
        origin = o.get("origin")
        kind = origin.get("kind") if isinstance(origin, dict) else o.get("turnOrigin")
        con.execute("INSERT INTO prompts VALUES(?,?,?,?,?,?,?) ON CONFLICT(prompt_id) DO UPDATE "
                    "SET kind=coalesce(prompts.kind, excluded.kind), "
                    "source=coalesce(prompts.source, excluded.source)",
                    (pid, o.get("sessionId"), path, ts, kind, o.get("promptSource"), is_sub))
    elif t == "custom-title" and o.get("customTitle"):
        state["title"] = o["customTitle"]
    elif t == "assistant":
        msg = o.get("message") if isinstance(o.get("message"), dict) else {}
        key = (msg.get("id"), o.get("requestId"))
        if key == (None, None):
            key = ("off", start)
        state["call_meta"][key] = (o.get("sessionId"), state["prompt"], o.get("agentId"))
        for c in msg.get("content") or []:
            if (isinstance(c, dict) and c.get("type") == "tool_use"
                    and c.get("name") in SPAWN_TOOLS and c.get("id")):
                inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                # Upsert, not REPLACE: a re-read must not erase a recorded result.
                con.execute("INSERT INTO spawns(tool_use_id,parent_k,session,ts,subagent_type,"
                            "model_req,prompt_id,file,input_hash) VALUES(?,?,?,?,?,?,?,?,?) "
                            "ON CONFLICT(tool_use_id) DO UPDATE SET parent_k=excluded.parent_k, "
                            "session=excluded.session, ts=excluded.ts, "
                            "subagent_type=excluded.subagent_type, model_req=excluded.model_req, "
                            "prompt_id=excluded.prompt_id, file=excluded.file, "
                            "input_hash=excluded.input_hash",
                            (c["id"], _key(path, key), o.get("sessionId"), ts,
                             inp.get("subagent_type"), inp.get("model"), state["prompt"], path,
                             spawn_input_hash(inp)))


def _index_subagent_meta(con, fp: Path) -> None:
    """agentType / toolUseId / spawnDepth from <agent>.meta.json. A missing or
    unreadable meta is recorded with NULLs: typed unknown, never a guess."""
    meta = Path(str(fp)[:-len(".jsonl")] + ".meta.json")
    md = {}
    try:
        md = json.loads(meta.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        md = {}
    con.execute("INSERT OR REPLACE INTO subagents VALUES(?,?,?,?,?,?)",
                (str(fp), fp.parent.parent.name, md.get("agentType"), md.get("toolUseId"),
                 md.get("spawnDepth"), md.get("model")))


def refresh(con: sqlite3.Connection, proj: Path = DEFAULT_PROJ, *,
            since_epoch: float | None = None, deadline_s: float = 20.0) -> dict:
    """Index the bytes appended since the last pass. Bounded by `deadline_s`.

    Returns {status: OK|PARTIAL|FAILED, files_read, calls_upserted, pending}.
    PARTIAL is resumable: offsets are committed per file, so the next pass
    continues where this one stopped. The outcome is recorded in meta so that a
    reader can tell a missed run from a quiet one."""
    t_end = time.monotonic() + deadline_s
    files_read = upserts = pending = 0
    backfill_pending = None
    status = "OK"
    err = ""
    try:
        _canonicalize(con, Path(proj))
        _migrate_spawns(con)
        known = {r[0]: r[1:] for r in con.execute(
            "SELECT path, offset, size, mtime_ns, entrypoint FROM files")}
        for fp, is_sub in _iter_files(Path(proj)):
            try:
                st = fp.stat()
            except OSError:
                continue
            if since_epoch is not None and st.st_mtime < since_epoch:
                continue
            path = str(fp)
            prev = known.get(path)
            if prev and prev[1] == st.st_size and prev[2] == st.st_mtime_ns:
                continue
            if time.monotonic() >= t_end:      # >=: Windows' clock ticks ~15 ms
                pending += 1
                status = "PARTIAL"
                continue
            offset = prev[0] if prev else 0
            entry = prev[3] if prev else None
            if prev and st.st_size < offset:            # rewritten: start over
                for t in ("calls", "quota"):
                    con.execute(f"DELETE FROM {t} WHERE file=?", (path,))
                offset, entry = 0, None
            srow = con.execute("SELECT cur_prompt, title FROM files WHERE path=?",
                               (path,)).fetchone()
            state = {"prompt": srow[0] if srow and offset else None,
                     "title": srow[1] if srow else None, "call_meta": {}}
            if is_sub and offset == 0:
                _index_subagent_meta(con, fp)
            calls, end, ep = _tis.calls_from(
                fp, offset, on_line=lambda o, s: _ancestry_line(con, path, is_sub, state, o, s))
            entry = entry or ep
            for c in calls:
                u = c["usage"]
                cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
                sess, pid, aid = state["call_meta"].get(c["key"], (None, None, None))
                con.execute(
                    "INSERT INTO calls(k,file,ts,model,is_sub,entrypoint,inp,cw,cw5,cw1,cr,out,"
                    "session,prompt_id,agent_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(k) DO UPDATE SET "
                    "ts=excluded.ts, inp=max(inp,excluded.inp), cw=max(cw,excluded.cw), "
                    "cw5=max(cw5,excluded.cw5), cw1=max(cw1,excluded.cw1), "
                    "cr=max(cr,excluded.cr), out=max(out,excluded.out), "
                    "session=coalesce(excluded.session,session), "
                    "prompt_id=coalesce(excluded.prompt_id,prompt_id), "
                    "agent_id=coalesce(excluded.agent_id,agent_id)",
                    (_key(path, c["key"]), path, _epoch(c.get("ts")), c.get("model") or "",
                     is_sub, entry, _num(u, "input_tokens"),
                     _num(u, "cache_creation_input_tokens"),
                     _num(cc, "ephemeral_5m_input_tokens"),
                     _num(cc, "ephemeral_1h_input_tokens"),
                     _num(u, "cache_read_input_tokens"), _num(u, "output_tokens"),
                     sess, pid, aid))
                upserts += 1
            if entry:
                con.execute("UPDATE calls SET entrypoint=? WHERE file=? AND entrypoint IS NULL",
                            (entry, path))
            con.execute("INSERT OR REPLACE INTO files(path,offset,size,mtime_ns,is_sub,entrypoint,"
                        "cur_prompt,title) VALUES(?,?,?,?,?,?,?,?)",
                        (path, end, st.st_size, st.st_mtime_ns, is_sub, entry,
                         state["prompt"], state["title"]))
            con.commit()
            files_read += 1
        # Historical spawn results (v3 backfill) use only the time left. They are not
        # freshness: pending files here never make the pass PARTIAL, which would turn
        # the burn alarm into MONITOR_FAILURE while the live index is current.
        backfill_pending = _backfill_spawns(con, t_end)
    except Exception as e:  # noqa: BLE001 -- typed, never silent
        status, err = "FAILED", f"{type(e).__name__}: {e}"
    now = time.time()
    con.execute("INSERT OR REPLACE INTO meta VALUES('last_refresh_status', ?)",
                (json.dumps({"status": status, "at": now, "error": err,
                             "pending": pending, "backfill_pending": backfill_pending}),))
    if status == "OK":
        con.execute("INSERT OR REPLACE INTO meta VALUES('last_ok_at', ?)", (str(now),))
    con.commit()
    return {"status": status, "files_read": files_read, "calls_upserted": upserts,
            "pending": pending, "backfill_pending": backfill_pending, "error": err}


# -- pricing -----------------------------------------------------------------

def load_prices() -> dict:
    return json.loads(current_pricing_path().read_text(encoding="utf-8"))["models"]


def price_for(model: str, prices: dict):
    """(price row, how). Exact id, else drop trailing -N segments (family fallback:
    claude-sonnet-5-5 -> claude-sonnet-5). None when nothing matches: the caller
    counts those calls as UNPRICED, never as zero."""
    if model in prices:
        return prices[model], "exact"
    parts = model.split("-")
    while len(parts) > 2:
        parts = parts[:-1]
        cand = "-".join(parts)
        if cand in prices:
            return prices[cand], f"family:{cand}"
    return None, "unpriced"


def window(con: sqlite3.Connection, start: float, end: float, prices: dict | None = None) -> dict:
    """Aggregate for calls with start < ts <= end. Tokens are MEASURED; usd is an
    ESTIMATE at list price. calls == 0 is a measured zero only if the index is
    fresh -- that judgement belongs to assess(), which sees the refresh status."""
    prices = prices if prices is not None else load_prices()
    agg = dict(calls=0, subagent_calls=0, sdk_calls=0, input=0, cache_write=0,
               cache_read=0, output=0, usd=0.0, unpriced_calls=0, fallbacks={})
    rows = con.execute(
        "SELECT model, is_sub, entrypoint, count(*), sum(inp), sum(cw), sum(cw5), sum(cw1), "
        "sum(cr), sum(out) FROM calls WHERE ts > ? AND ts <= ? GROUP BY model, is_sub, entrypoint",
        (start, end)).fetchall()
    for model, is_sub, ep, n, inp, cw, cw5, cw1, cr, out in rows:
        agg["calls"] += n
        agg["subagent_calls"] += n if is_sub else 0
        agg["sdk_calls"] += n if ep == "sdk-cli" else 0
        agg["input"] += inp
        agg["cache_write"] += cw
        agg["cache_read"] += cr
        agg["output"] += out
        p, how = price_for(model, prices)
        if p is None:
            agg["unpriced_calls"] += n
            continue
        if how != "exact":
            agg["fallbacks"][model] = how
        # Writes without a TTL split are priced at the 1h rate (79.9 % of writes
        # were 1h on 2026-09-27); the split is used whenever the transcript has it.
        unsplit = max(0, cw - cw5 - cw1)
        agg["usd"] += (inp * p["input"] + cw5 * p["cache_write_5m"]
                       + (cw1 + unsplit) * p["cache_write_1h"]
                       + cr * p["cache_read"] + out * p["output"]) / 1e6
    return agg


# -- calibration + assessment ------------------------------------------------

def load_readings(path: Path = METER_FILE) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def week_start(t: float, anchor: float, period_s: float = 7 * 86400) -> float:
    return anchor + ((t - anchor) // period_s) * period_s


def calibrate(con, reading: dict, anchor: float, prices: dict) -> float | None:
    """Weekly allowance in API-equivalent USD implied by one meter reading:
    usd(week start -> reading time) / fraction. ESTIMATED; None if unmeasured."""
    t = _epoch(reading["at"])
    used = window(con, week_start(t, anchor), t, prices)
    if not used["calls"] or reading["fraction"] <= 0:
        return None
    return used["usd"] / reading["fraction"]


def assess(con, now: float, *, allowance_usd: float | None, anchor: float,
           prices: dict | None = None, refresh_status: dict | None = None) -> dict:
    """Typed burn state at `now` from the index only (no refresh here).

    MONITOR_FAILURE when the last refresh did not finish or the index is older
    than STALE_AFTER_S: a failed look is never reported as a quiet week."""
    prices = prices if prices is not None else load_prices()
    out: dict = {"at": _iso(now), "state": None, "reasons": [], "estimated_pct": None}
    rs = refresh_status
    if rs is None:
        row = con.execute("SELECT v FROM meta WHERE k='last_refresh_status'").fetchone()
        rs = json.loads(row[0]) if row else None
    if rs is not None and rs.get("status") in ("FAILED", "PARTIAL"):
        out.update(state=MONITOR_FAILURE,
                   reasons=[f"last refresh {rs['status']}: {rs.get('error') or rs.get('pending')}"])
        return out
    live = abs(time.time() - now) < 60          # a replay is never judged stale
    if live and (rs is None or time.time() - float(rs.get("at", 0)) > STALE_AFTER_S):
        when = _iso(float(rs["at"])) if rs and rs.get("at") else "never"
        out.update(state=MONITOR_FAILURE, reasons=[f"index stale: last refresh {when}"])
        return out
    ws = week_start(now, anchor)
    we = ws + 7 * 86400
    wk = window(con, ws, now, prices)
    r6 = window(con, now - RATE_WINDOW_H * 3600, now, prices)
    r24 = window(con, now - 86400, now, prices)
    daily = [window(con, now - (d + 1) * 86400, now - d * 86400, prices)["usd"]
             for d in range(1, 15)]
    daily = sorted(x for x in daily if x > 0)
    base = daily[len(daily) // 2] if daily else None
    rate_h = r6["usd"] / RATE_WINDOW_H
    hours_left = (we - now) / 3600
    out.update(week_start=_iso(ws), hours_to_reset=round(hours_left, 1),
               week_usd=round(wk["usd"], 2), week_calls=wk["calls"],
               rate_6h={"usd_h": round(rate_h, 2), "calls_h": round(r6["calls"] / RATE_WINDOW_H),
                        "subagent_calls_h": round(r6["subagent_calls"] / RATE_WINDOW_H),
                        "cache_read_h": round(r6["cache_read"] / RATE_WINDOW_H),
                        "cache_write_h": round(r6["cache_write"] / RATE_WINDOW_H),
                        "output_h": round(r6["output"] / RATE_WINDOW_H)},
               anomaly_24h=(round(r24["usd"] / base, 2) if base else None),
               unpriced_calls=wk["unpriced_calls"])
    state = "NORMAL"
    reasons = []
    if base and r24["usd"] / base >= ANOMALY_FACTOR:
        state = "ELEVATED"
        reasons.append(f"24h burn {r24['usd'] / base:.1f}x the 14-day median day")
    if allowance_usd:
        pct = wk["usd"] / allowance_usd
        proj = (wk["usd"] + rate_h * hours_left) / allowance_usd
        left_h = ((allowance_usd - wk["usd"]) / rate_h) if rate_h > 0 else None
        out.update(estimated_pct=round(100 * pct, 1), projected_pct_at_reset=round(100 * proj, 1),
                   hours_to_exhaust=(round(left_h, 1) if left_h is not None else None))
        if proj >= 1.0:
            state = max(state, "ELEVATED", key=STATES.index)
            reasons.append(f"projected {100 * proj:.0f}% at reset")
        if (pct >= 0.6 and proj >= 1.0) or (left_h is not None and left_h < 24 < hours_left):
            state = max(state, "CONSTRAINED", key=STATES.index)
            reasons.append(f"~{100 * pct:.0f}% used, exhaust in ~{left_h:.0f}h" if left_h else
                           f"~{100 * pct:.0f}% used")
        if pct >= 0.85 or (left_h is not None and left_h < 12 < hours_left):
            state = "CRITICAL"
            reasons.append(f"~{100 * pct:.0f}% used (ESTIMATED)")
    else:
        reasons.append("no meter calibration: percentage UNKNOWN, anomaly only")
    out.update(state=state, reasons=reasons)
    return out


WEEK_S = 7 * 86400


def _anchor_label(resets_at: float) -> str:
    """Weekly window identity: weekday + time of its reset (UTC). Two different
    labels live at once = two different accounts/orgs (one account, one window)."""
    d = datetime.fromtimestamp(resets_at, timezone.utc)
    return d.strftime("%a %H:%MZ")


def quota_status(con, now: float, lookback_days: float = 21.0) -> dict:
    """C1b provider adapter: what the PROVIDER said, from `quotaLimits` rows.

    Provider truth, never fitted: rejections, resets, overage reasons. No row in
    the lookback = NO_SIGNAL (unknown), never "fine". Weekly windows are told
    apart by their reset anchor; `weekly_windows` counts distinct anchors seen,
    a lower bound on the accounts writing into this transcript store."""
    rows = con.execute(
        "SELECT ts, type, status, resets_at, overage_reason FROM quota "
        "WHERE ts > ? AND ts <= ? ORDER BY ts", (now - lookback_days * 86400, now)).fetchall()
    if not rows:
        return {"signal": "NO_SIGNAL", "lookback_days": lookback_days}
    windows: dict = {}
    for ts, typ, st, reset, reason in rows:
        if typ == "seven_day" and reset:
            label = _anchor_label(reset)
            w = windows.setdefault(label, {"resets": set(), "reasons": set(),
                                           "first_reject": None, "last_event": None})
            w["resets"].add(reset)
            w["reasons"].add(reason)
            if st == "rejected" and w["first_reject"] is None:
                w["first_reject"] = ts
            w["last_event"] = ts
    live = []
    for ts, typ, st, reset, reason in rows:
        if st == "rejected" and reset and reset > now:
            item = {"type": typ, "window": _anchor_label(reset) if typ == "seven_day" else None,
                    "rejected_since": _iso(ts), "until": _iso(reset)}
            if item not in live and not any(x["type"] == typ and x["until"] == item["until"]
                                            for x in live):
                live.append(item)
    return {"signal": "PRESENT", "events": len(rows),
            "weekly_windows": len(windows),
            "windows": {k: {"resets": [_iso(r) for r in sorted(v["resets"])],
                            "overage_reasons": sorted(x for x in v["reasons"] if x),
                            "last_event": _iso(v["last_event"])} for k, v in windows.items()},
            "rejected_now": live}


def advisory_line(a: dict) -> str | None:
    """One human line for launch advisories, or None when NORMAL and no live
    provider rejection."""
    prov = (a.get("provider") or {}).get("rejected_now") or []
    prov_txt = "; ".join(f"proveedor: ventana {p['window'] or p['type']} RECHAZADA hasta {p['until']}"
                         for p in prov)
    if a["state"] == MONITOR_FAILURE:
        return f"PP burn monitor FAILED -- {'; '.join(a['reasons'])}. Usage is UNKNOWN, not low."
    if a["state"] in (None, "NORMAL"):
        return f"PP quota: {prov_txt}." if prov_txt else None
    pct = f" ~{a['estimated_pct']:.0f}% semana (estimado)" if a.get("estimated_pct") is not None else ""
    r = a.get("rate_6h") or {}
    return (f"PP burn {a['state']}{pct}: {'; '.join(a['reasons'])}. "
            f"Ritmo 6h: {r.get('calls_h')} llamadas/h ({r.get('subagent_calls_h')} subagente), "
            f"{(r.get('cache_read_h') or 0) / 1e6:.0f}M cache-read/h. "
            + (f"{prov_txt}. " if prov_txt else "")
            + "Prioriza cerrar trabajo abierto antes de lanzar mas agentes/misiones en segundo plano.")


def current_allowance(con, prices=None) -> tuple[float | None, float]:
    """(allowance_usd, anchor_epoch) from the newest calibration reading."""
    cfg = load_readings()
    anchor = _epoch(cfg["reset_anchor"])
    cal = [r for r in cfg["readings"] if r.get("use") == "calibration"]
    if not cal:
        return None, anchor
    newest = max(cal, key=lambda r: _epoch(r["at"]))
    return calibrate(con, newest, anchor, prices or load_prices()), anchor


def burn(db: Path = DEFAULT_DB, proj: Path = DEFAULT_PROJ, deadline_s: float = 8.0) -> dict:
    """Bounded refresh + assessment. Never raises; a failure is MONITOR_FAILURE."""
    try:
        con = connect(db)
        rs = refresh(con, proj, since_epoch=time.time() - 15 * 86400, deadline_s=deadline_s)
        rs["at"] = time.time()
        prices = load_prices()
        allowance, anchor = current_allowance(con, prices)
        a = assess(con, time.time(), allowance_usd=allowance, anchor=anchor,
                   prices=prices, refresh_status=rs)
        a["provider"] = quota_status(con, time.time())
        return a
    except Exception as e:  # noqa: BLE001
        return {"state": MONITOR_FAILURE, "reasons": [f"{type(e).__name__}: {e}"],
                "estimated_pct": None}


def holdout(con) -> dict:
    """Done-gate G6: allowance from the 'calibration' reading of week A, frozen,
    then the 'holdout' reading of week B predicted from week B's usage alone."""
    cfg = load_readings()
    anchor = _epoch(cfg["reset_anchor"])
    prices = load_prices()
    cal = [r for r in cfg["readings"] if r.get("use") == "calibration"]
    hold = [r for r in cfg["readings"] if r.get("use") == "holdout"]
    if not cal or not hold:
        return {"verdict": "UNMEASURED", "reason": "need one calibration and one holdout reading"}
    a = min(cal, key=lambda r: _epoch(r["at"]))
    allowance = calibrate(con, a, anchor, prices)
    res = []
    for h in hold:
        t = _epoch(h["at"])
        used = window(con, week_start(t, anchor), t, prices)
        pred = used["usd"] / allowance if allowance else None
        res.append({"at": h["at"], "owner_pct": 100 * h["fraction"],
                    "predicted_pct": None if pred is None else round(100 * pred, 1),
                    "week_usd": round(used["usd"], 2), "calls": used["calls"]})
    return {"calibrated_on": a["at"], "allowance_usd_est": allowance and round(allowance, 2),
            "results": res}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("cmd", choices=["refresh", "window", "burn", "replay", "holdout"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--proj", default=str(DEFAULT_PROJ))
    ap.add_argument("--deadline", type=float, default=600.0)
    ap.add_argument("--since-days", type=float, default=21.0)
    ap.add_argument("--at", default=None)
    ap.add_argument("--until", default=None)
    ap.add_argument("--step-h", type=float, default=1.0)
    a = ap.parse_args(argv)
    con = connect(Path(a.db))
    if a.cmd == "refresh":
        r = refresh(con, Path(a.proj), since_epoch=time.time() - a.since_days * 86400,
                    deadline_s=a.deadline)
        print(json.dumps(r))
        return 0 if r["status"] == "OK" else 2
    if a.cmd == "window":
        print(json.dumps(window(con, _epoch(a.args[0]), _epoch(a.args[1])), indent=1))
        return 0
    if a.cmd == "burn":
        r = burn(Path(a.db), Path(a.proj), deadline_s=min(a.deadline, 30.0))
        print(json.dumps(r, indent=1))
        line = advisory_line(r)
        if line:
            print(line)
        return 3 if r["state"] == MONITOR_FAILURE else 0
    if a.cmd == "replay":
        prices = load_prices()
        allowance, anchor = current_allowance(con, prices)
        if a.args and a.args[0] == "frozen":
            allowance = holdout(con).get("allowance_usd_est")
        t, end = _epoch(a.at), _epoch(a.until or a.at)
        ok = {"status": "OK", "at": end}
        while t <= end:
            r = assess(con, t, allowance_usd=allowance, anchor=anchor, prices=prices,
                       refresh_status=ok)
            print(json.dumps({k: r.get(k) for k in ("at", "state", "estimated_pct",
                                                    "projected_pct_at_reset", "anomaly_24h",
                                                    "reasons")}))
            t += a.step_h * 3600
        return 0
    if a.cmd == "holdout":
        print(json.dumps(holdout(con), indent=1))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
