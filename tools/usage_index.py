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
  population [--until ISO] [--project-filter S] [--select S] [--include-archived]
             [--expect JSON|FILE] [--plane NAME]   typed population verdict (exit 0/1/3)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import ntpath
import os
import posixpath
import re
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

SCHEMA_VERSION = 5
SPAWN_SCHEMA = 4   # the version _migrate_spawns stamps; it never writes SCHEMA_VERSION (a bump must not re-queue the backfill)
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
-- v5 (phase 1, pillar O): the occurrence view, tool events, attribution, patterns. Additive
-- only: the new `files` columns are added by _migrate_v5, never here (a reader takes no write lock).
CREATE TABLE IF NOT EXISTS call_files(k TEXT, file TEXT, ts REAL, model TEXT, inp INTEGER,
  cw INTEGER, cw5 INTEGER, cw1 INTEGER, cr INTEGER, out INTEGER, PRIMARY KEY(k, file));
CREATE INDEX IF NOT EXISTS call_files_file ON call_files(file);
CREATE TABLE IF NOT EXISTS tool_events(file TEXT, tool_use_id TEXT, off INTEGER, ts REAL,
  tool TEXT, input_hash TEXT, input_bytes INTEGER, path TEXT, pat_hits TEXT,
  result_bytes INTEGER, result_chars INTEGER, is_error INTEGER, result_off INTEGER,
  PRIMARY KEY(file, tool_use_id));
CREATE TABLE IF NOT EXISTS user_hits(file TEXT, off INTEGER, ts REAL, pat_hits TEXT,
  PRIMARY KEY(file, off));
CREATE TABLE IF NOT EXISTS file_cwds(file TEXT, cwd TEXT, first_off INTEGER, first_ts REAL,
  PRIMARY KEY(file, cwd));
CREATE TABLE IF NOT EXISTS file_attribution(file TEXT, kind TEXT, name TEXT, role TEXT,
  n INTEGER, PRIMARY KEY(file, kind, name, role));
CREATE TABLE IF NOT EXISTS patterns(name TEXT PRIMARY KEY, regex TEXT, flags INTEGER,
  source TEXT, version TEXT);
"""
_V2_COLUMNS = (("calls", "session", "TEXT"), ("calls", "prompt_id", "TEXT"),
               ("calls", "agent_id", "TEXT"), ("files", "cur_prompt", "TEXT"),
               ("files", "title", "TEXT"))
# v5 `files` columns. `resolved` is produced by tis_observed (plan 02), never computed here.
# v5_from = byte offset from which this file's v5 rows are complete: 0 for a file first read
# under v5, the old offset for a legacy file that grows, NULL for a legacy file never re-read
# (typed UNMEASURED for every v5 fact, never "no tools").
_V5_COLUMNS = (("files", "resolved", "TEXT"), ("files", "store", "TEXT"),
               ("files", "project", "TEXT"), ("files", "archived", "INTEGER"),
               ("files", "session_key", "TEXT"), ("files", "first_ts", "REAL"),
               ("files", "last_ts", "REAL"), ("files", "parse_errors", "INTEGER"),
               ("files", "error", "TEXT"), ("files", "v5_from", "INTEGER"),
               ("files", "head_sha", "TEXT"), ("files", "tail_sha", "TEXT"),
               ("files", "content_id", "TEXT"), ("files", "dup_of", "TEXT"),
               ("files", "pat_ver", "TEXT"))
_V5_FILE_TABLES = ("call_files", "tool_events", "user_hits", "file_cwds", "file_attribution")


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
    """-> v4 (SPAWN_SCHEMA, its own gate: a later bump never re-queues this): adds any
    missing spawn columns and queues ONLY the transcripts that hold
    a spawn lacking a result or an input hash for a backfill; no file offset is
    touched, so totals cannot move (audit G2). One BEGIN IMMEDIATE, version
    re-checked inside it, so two concurrent refreshes migrate once."""
    row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    if row is not None and int(row[0]) >= SPAWN_SCHEMA:
        return
    con.commit()
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
        if row is None or int(row[0]) < SPAWN_SCHEMA:
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
                        (str(SPAWN_SCHEMA),))
        con.commit()
    except BaseException:
        con.rollback()
        raise


def _migrate_v5(con) -> None:
    """-> v5: additive only. Adds the missing `files` columns and stamps the version; opens
    no transcript, touches no offset, deletes nothing (pillar O rule 2). One BEGIN
    IMMEDIATE, version re-checked inside it, so two concurrent refreshes migrate once.
    The v5 tables themselves come from SCHEMA (CREATE TABLE IF NOT EXISTS)."""
    row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    if row is not None and int(row[0]) >= SCHEMA_VERSION:
        return
    con.commit()
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
        if row is None or int(row[0]) < SCHEMA_VERSION:
            have = {r[1] for r in con.execute("PRAGMA table_info(files)")}
            for table, col, typ in _V5_COLUMNS:
                if col not in have:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
            con.execute("INSERT OR REPLACE INTO meta VALUES('v5_migration', ?)",
                        (json.dumps({"at": time.time(), "files_opened": 0}),))
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


ARCHIVED_DIR = "_archived"
ARCHIVED_RULE = (
    "_archived/<project>/ transcripts are indexed with archived=1 and project=<project> into "
    "the v5 tables only (files, call_files, tool_events, user_hits, file_cwds, "
    "file_attribution), never into calls, quota, prompts, spawns or subagents, so every v4 "
    "reader keeps its v4 answer; population excludes them unless include_archived is set; a "
    "live file with the same project and session_key wins over its archived twin.")
SKIPPED_SHAPES = ("_preserved", "_empty_shells", "other")   # the census keys, always present
SKIPPED_SAMPLES = 5


def _store_files(store: Path):
    """The two ingested transcript shapes of one store dir: <store>/<sid>.jsonl and
    <store>/<sid>/subagents/<agent>.jsonl. Yields (path, is_subagent)."""
    for jf in store.glob("*.jsonl"):
        yield jf, 0
    for jf in store.glob("*/subagents/*.jsonl"):
        yield jf, 1


def _session_key(jf: Path, is_sub: int) -> str:
    """A session is its main file plus its <sid>/subagents/* files (the champion's rule,
    wiki/tools/kme_token_audit.py): the first path component under the store."""
    return jf.parent.parent.name if is_sub else jf.stem


def _iter_files_v5(proj: Path):
    """(path, is_sub, store, project, archived, session_key), one spelling per physical
    transcript. Store dirs come from `store_identity` (consumed, never re-derived); the
    `_archived` store is opened one level down through the same producer, so an aliased
    archived project is counted once too. store is the canonical store dir's name;
    project equals store for live files and is the child dir's name for archived ones."""
    if not proj.is_dir():
        return
    for store in _tis.store_identity(proj)[0]:
        if store.name == ARCHIVED_DIR:
            for child in _tis.store_identity(store)[0]:
                for jf, is_sub in _store_files(child):
                    yield jf, is_sub, ARCHIVED_DIR, child.name, 1, _session_key(jf, is_sub)
            continue
        for jf, is_sub in _store_files(store):
            yield jf, is_sub, store.name, store.name, 0, _session_key(jf, is_sub)


def _iter_files(proj: Path):
    """(path, is_subagent) of the LIVE transcripts: the v4 reader view of _iter_files_v5.
    No caller outside this module (grep 2026-10-06: the other `_iter_files` in the repo are
    unrelated functions of their own modules)."""
    for jf, is_sub, _store, _project, archived, _skey in _iter_files_v5(proj):
        if not archived:
            yield jf, is_sub


def _path_identity(path: str, is_sub: int) -> tuple[str, str, int, str]:
    """(store, project, archived, session_key) from the transcript path string alone, the
    same facts _iter_files_v5 yields from the directory structure. Pure string work."""
    p = Path(path)
    sid_dir = p.parent.parent if is_sub else p      # the <sid> dir, or the main file itself
    store_dir = sid_dir.parent                      # <store> or <_archived>/<project>
    if store_dir.parent.name == ARCHIVED_DIR:
        return ARCHIVED_DIR, store_dir.name, 1, _session_key(p, is_sub)
    return store_dir.name, store_dir.name, 0, _session_key(p, is_sub)


def _fill_path_identity(con) -> int:
    """Fill resolved/store/project/archived/session_key for files rows that lack them (a
    migrated v4 index) from the path string and `_tis.resolved_path`. Stat-level only: no
    transcript is opened. Returns how many rows were filled."""
    rows = con.execute("SELECT path, is_sub FROM files WHERE session_key IS NULL").fetchall()
    for path, is_sub in rows:
        store, project, archived, skey = _path_identity(path, is_sub or 0)
        con.execute("UPDATE files SET resolved=?, store=?, project=?, archived=?, session_key=? "
                    "WHERE path=?", (_tis.resolved_path(path), store, project, archived, skey, path))
    con.commit()
    return len(rows)


def _census_skipped(proj: Path, matched: set) -> dict:
    """Every *.jsonl under a store that no ingested shape matched (_preserved,
    _empty_shells, others), counted and never silently absent: count, bytes (os.stat),
    per-shape counts and up to SKIPPED_SAMPLES sample paths. A listing walk only (no file is
    opened). A tree with none records count 0; unreadable directories are counted too."""
    by = {s: 0 for s in SKIPPED_SHAPES}
    skipped: list = []
    nbytes = walk_errors = 0
    roots = []
    for store in _tis.store_identity(proj)[0]:
        roots.append(store)
        if store.name == ARCHIVED_DIR:
            roots += [c for c in _tis.store_identity(store)[0]
                      if not str(c).startswith(str(store) + os.sep)]

    def _err(_e):
        nonlocal walk_errors
        walk_errors += 1

    for root in roots:
        for dirpath, _dirs, names in os.walk(root, onerror=_err):
            for n in names:
                p = os.path.join(dirpath, n)
                if not n.endswith(".jsonl") or p in matched:
                    continue
                first = os.path.relpath(p, root).split(os.sep)[0]
                by[first if first in ("_preserved", "_empty_shells") else "other"] += 1
                try:
                    nbytes += os.stat(p).st_size
                except OSError:
                    walk_errors += 1
                skipped.append(p)
    skipped.sort()
    return {"count": len(skipped), "bytes": nbytes, "by_shape": by,
            "samples": skipped[:SKIPPED_SAMPLES], "walk_errors": walk_errors}


# Every column that carries a transcript path (audit G1, plus spawns.parent_k).
# (table, column, kind): "pk" columns may collide with a canonical twin, which wins;
# "key" columns embed the path after an `off|` prefix.
_PATH_COLUMNS = (("files", "path", "pk"), ("calls", "k", "key"), ("calls", "file", "plain"),
                 ("quota", "file", "pk"), ("prompts", "file", "plain"),
                 ("spawns", "file", "plain"), ("spawns", "parent_k", "key"),
                 ("subagents", "file", "pk"),
                 ("call_files", "k", "key"), ("call_files", "file", "pk"),
                 ("tool_events", "file", "pk"), ("user_hits", "file", "pk"),
                 ("file_cwds", "file", "pk"), ("file_attribution", "file", "pk"),
                 ("files", "dup_of", "plain"), ("files", "resolved", "plain"))


def _path_columns(con):
    """_PATH_COLUMNS minus the columns this index does not have yet: canonicalization
    runs before _migrate_v5, so a v4 index has no files.dup_of to rewrite."""
    have: dict = {}
    out = []
    for table, col, kind in _PATH_COLUMNS:
        if table not in have:
            have[table] = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        if col in have[table]:
            out.append((table, col, kind))
    return out


def _alias_rows(con, alias: str) -> int:
    n = 0
    for table, col, kind in _path_columns(con):
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
            for table, col, kind in _path_columns(con):
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


_WIN_ABS = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


def _norm_path(p, cwd=None):
    """A tool-input path as one comparable string. Pure string work: never touches the
    disk and never resolves against this host's file system (T-01-05). Windows-shaped
    strings go through ntpath then forward slashes; POSIX absolute through posixpath; a
    relative path is joined onto the current cwd when one is known, else kept relative."""
    if not isinstance(p, str) or not p:
        return None
    if _WIN_ABS.match(p):
        return ntpath.normpath(p).replace("\\", "/")
    if p.startswith("/"):
        return posixpath.normpath(p)
    if isinstance(cwd, str) and cwd:
        if _WIN_ABS.match(cwd):
            return ntpath.normpath(ntpath.join(cwd, p)).replace("\\", "/")
        if cwd.startswith("/"):
            return posixpath.normpath(posixpath.join(cwd, p))
    return posixpath.normpath(p.replace("\\", "/"))


def _result_text(content) -> str:
    """Flatten a tool_result body exactly like wiki/tools/kme_token_audit.py::text_of:
    str as is; a list joins with newline the `text` of text items, the flattening of
    nested tool_result items, `[image]` for image items and bare strings. The text is
    only measured, never stored."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    out.append(c.get("text", ""))
                elif c.get("type") == "tool_result":
                    out.append(_result_text(c.get("content")))
                elif c.get("type") == "image":
                    out.append("[image]")
            elif isinstance(c, str):
                out.append(c)
        return "\n".join(out)
    return ""


def _v5_line(con, path: str, state: dict, o: dict, start: int) -> None:
    """v5 facts from one transcript line, in the same parse as _ancestry_line (one read
    pass, no second reader). A tool_use becomes a tool_events row (hash, sizes and a
    normalized path only: never the input or result text, HR-SECRET-002); the tool_result
    that answers it fills the result columns, which stay NULL until one is seen."""
    cwd = o.get("cwd")
    if isinstance(cwd, str) and cwd:
        state["cwd"] = cwd
    msg = o.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, list):
        return
    t = o.get("type")
    ts = _epoch(o.get("timestamp"))
    if t == "assistant":
        for i, c in enumerate(content):
            if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                continue
            inp = c.get("input")
            if inp is None:
                inp = {}
            raw = json.dumps(inp, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            raw_b = raw.encode("utf-8", "replace")
            fpath = None
            if isinstance(inp, dict):
                for fld in ("file_path", "notebook_path", "path"):
                    if inp.get(fld):
                        fpath = _norm_path(inp[fld], state.get("cwd"))
                        break
            con.execute(
                "INSERT INTO tool_events(file,tool_use_id,off,ts,tool,input_hash,input_bytes,path) "
                "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(file,tool_use_id) DO UPDATE SET "
                "off=excluded.off, ts=excluded.ts, tool=excluded.tool, "
                "input_hash=excluded.input_hash, input_bytes=excluded.input_bytes, "
                "path=excluded.path",
                (path, c.get("id") or f"off|{start}|{i}", start, ts, c.get("name"),
                 hashlib.sha256(raw_b).hexdigest()[:16], len(raw_b), fpath))
    elif t == "user":
        for c in content:
            if not (isinstance(c, dict) and c.get("type") == "tool_result" and c.get("tool_use_id")):
                continue
            text = _result_text(c.get("content"))
            con.execute("UPDATE tool_events SET result_chars=?, result_bytes=?, is_error=?, "
                        "result_off=? WHERE file=? AND tool_use_id=?",
                        (len(text), len(text.encode("utf-8", "replace")),
                         1 if c.get("is_error") else 0, start, path, c["tool_use_id"]))


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


def _content_id(end: int, head_sha: str, tail_sha: str) -> str:
    """Content identity of a transcript's ingested bytes: its end offset plus the hashes of its
    first and last complete lines. Two files with a shared prefix but different content differ
    in the tail hash or the end; two byte-identical files agree on all three."""
    return hashlib.sha256(f"{end}|{head_sha}|{tail_sha}".encode()).hexdigest()[:32]


def _call_key_set(con, path: str) -> set:
    """The call identities a file holds, comparable across copies: an id-less call's key embeds
    the file path (`off|<path>|<offset>`), so the path is blanked."""
    return {("off||" + k.rsplit("|", 1)[1]) if k.startswith("off|") else k
            for (k,) in con.execute("SELECT k FROM call_files WHERE file=?", (path,))}


def _dup_groups(con, content_ids) -> None:
    """Recompute dup_of for every file of each given content id. A group is the files sharing
    a content_id; within it, every member whose call-key set equals the lexicographically
    smallest member's gets dup_of = that path, the others NULL (never a merge on content_id or
    sessionId alone). A group of one clears its member. Order-independent: the result is a
    function of the rows now in the index."""
    for cid in sorted({c for c in content_ids if c}):
        members = [r[0] for r in con.execute(
            "SELECT path FROM files WHERE content_id=? ORDER BY path", (cid,))]
        canon = members[0] if members else None
        canon_keys = _call_key_set(con, canon) if len(members) > 1 else None
        for p in members:
            dup = canon if (len(members) > 1 and p != canon
                            and _call_key_set(con, p) == canon_keys) else None
            con.execute("UPDATE files SET dup_of=? WHERE path=?", (dup, p))


def _record_file_error(con, path: str, is_sub: int, st, exc: Exception, ident: tuple) -> None:
    """A transcript that cannot be read: typed `files.error` ("<Class>: <message>"), the offset
    never advanced, size set to -1 so the next pass retries it. A file never read before gets a
    row with v5_from NULL (its v5 facts are unknown, not zero)."""
    store, project, archived, skey = ident
    con.execute(
        "INSERT INTO files(path,offset,size,mtime_ns,is_sub,error,resolved,store,project,archived,"
        "session_key) VALUES(?,0,-1,?,?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET "
        "error=excluded.error, size=-1",
        (path, st.st_mtime_ns, is_sub, f"{type(exc).__name__}: {exc}", _tis.resolved_path(path),
         store, project, archived, skey))
    con.commit()


def refresh(con: sqlite3.Connection, proj: Path = DEFAULT_PROJ, *,
            since_epoch: float | None = None, deadline_s: float = 20.0) -> dict:
    """Index the bytes appended since the last pass. Bounded by `deadline_s`.

    Returns {status: OK|PARTIAL|FAILED, files_read, calls_upserted, pending, ...} plus the
    pass's own measurements: files_opened (opens attempted), bytes_read (raw bytes
    iterated), bytes_ingested (end minus offset), files_seen, wall_s. PARTIAL is
    resumable: offsets are committed per file, so the next pass continues where this one
    stopped. The outcome is recorded in meta so that a reader can tell a missed run from
    a quiet one."""
    t0 = time.monotonic()
    t_end = t0 + deadline_s
    files_read = upserts = pending = 0
    files_opened = bytes_read = bytes_ingested = files_seen = 0
    parse_errors = 0
    backfill_pending = None
    skipped_shapes = None
    files_with_errors = None
    status = "OK"
    err = ""
    try:
        _canonicalize(con, Path(proj))
        _migrate_spawns(con)
        _migrate_v5(con)
        _fill_path_identity(con)
        con.execute("CREATE INDEX IF NOT EXISTS files_content ON files(content_id)")
        con.execute("INSERT OR REPLACE INTO meta VALUES('archived_rule', ?)", (ARCHIVED_RULE,))
        con.commit()
        matched: set = set()
        known = {r[0]: r[1:] for r in con.execute(
            "SELECT path, offset, size, mtime_ns, entrypoint, v5_from FROM files")}
        for fp, is_sub, store, project, archived, skey in _iter_files_v5(Path(proj)):
            files_seen += 1
            matched.add(str(fp))
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
                for t in ("calls", "quota") + _V5_FILE_TABLES:
                    con.execute(f"DELETE FROM {t} WHERE file=?", (path,))
                offset, entry = 0, None
            # v5_from: where this file's v5 rows start being complete.
            if offset == 0:
                v5_from = 0
            elif prev and prev[4] is not None:
                v5_from = prev[4]
            else:
                v5_from = offset                        # a legacy file that grows
            srow = con.execute("SELECT cur_prompt, title, parse_errors, head_sha, tail_sha, "
                               "content_id FROM files WHERE path=?", (path,)).fetchone()
            old_pe = (srow[2] or 0) if srow and offset else 0
            old_head = srow[3] if srow and offset else None
            old_tail = srow[4] if srow and offset else None
            old_cid = srow[5] if srow else None
            state = {"prompt": srow[0] if srow and offset else None,
                     "title": srow[1] if srow else None, "call_meta": {}, "cwd": None}
            if is_sub and offset == 0 and not archived:
                _index_subagent_meta(con, fp)

            def on_line(o, s, path=path, is_sub=is_sub, state=state, archived=archived):
                if not archived:                        # ARCHIVED_RULE: no ancestry rows
                    _ancestry_line(con, path, is_sub, state, o, s)
                _v5_line(con, path, state, o, s)

            stats: dict = {}
            files_opened += 1
            try:
                calls, end, ep = _tis.calls_from(fp, offset, on_line=on_line, stats=stats)
            except OSError as e:                # this file only: typed, the others go on
                con.rollback()
                _record_file_error(con, path, is_sub, st, e, (store, project, archived, skey))
                continue
            bytes_read += stats.get("bytes_seen", 0)
            bytes_ingested += end - offset
            parse_errors += stats.get("bad", 0)
            head_sha = stats.get("head_sha") if offset == 0 else old_head
            tail_sha = stats.get("tail_sha") or old_tail
            cid = _content_id(end, head_sha, tail_sha) if head_sha and tail_sha else None
            entry = entry or ep
            for c in calls:
                u = c["usage"]
                cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
                sess, pid, aid = state["call_meta"].get(c["key"], (None, None, None))
                k = _key(path, c["key"])
                vals = (_epoch(c.get("ts")), c.get("model") or "", _num(u, "input_tokens"),
                        _num(u, "cache_creation_input_tokens"),
                        _num(cc, "ephemeral_5m_input_tokens"),
                        _num(cc, "ephemeral_1h_input_tokens"),
                        _num(u, "cache_read_input_tokens"), _num(u, "output_tokens"))
                if not archived:  # ARCHIVED_RULE: v5 tables only
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
                        (k, path, vals[0], vals[1], is_sub, entry, vals[2], vals[3], vals[4],
                         vals[5], vals[6], vals[7], sess, pid, aid))
                # The occurrence view: this file's own values, order-independent (calls.file
                # is first-writer-wins).
                con.execute(
                    "INSERT INTO call_files(k,file,ts,model,inp,cw,cw5,cw1,cr,out) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(k,file) DO UPDATE SET "
                    "ts=excluded.ts, model=excluded.model, inp=max(inp,excluded.inp), "
                    "cw=max(cw,excluded.cw), cw5=max(cw5,excluded.cw5), cw1=max(cw1,excluded.cw1), "
                    "cr=max(cr,excluded.cr), out=max(out,excluded.out)",
                    (k, path) + vals)
                upserts += 1
            if entry and not archived:
                con.execute("UPDATE calls SET entrypoint=? WHERE file=? AND entrypoint IS NULL",
                            (entry, path))
            con.execute("INSERT INTO files(path,offset,size,mtime_ns,is_sub,entrypoint,"
                        "cur_prompt,title,v5_from,resolved,store,project,archived,session_key,"
                        "parse_errors,error,head_sha,tail_sha,content_id) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?) "
                        "ON CONFLICT(path) DO UPDATE SET offset=excluded.offset, "
                        "size=excluded.size, mtime_ns=excluded.mtime_ns, is_sub=excluded.is_sub, "
                        "entrypoint=excluded.entrypoint, cur_prompt=excluded.cur_prompt, "
                        "title=excluded.title, v5_from=excluded.v5_from, "
                        "resolved=excluded.resolved, store=excluded.store, "
                        "project=excluded.project, archived=excluded.archived, "
                        "session_key=excluded.session_key, parse_errors=excluded.parse_errors, "
                        "error=NULL, head_sha=excluded.head_sha, tail_sha=excluded.tail_sha, "
                        "content_id=excluded.content_id",
                        (path, end, st.st_size, st.st_mtime_ns, is_sub, entry,
                         state["prompt"], state["title"], v5_from, _tis.resolved_path(path),
                         store, project, archived, skey, old_pe + stats.get("bad", 0),
                         head_sha, tail_sha, cid))
            con.execute("UPDATE files SET dup_of=NULL WHERE path=?", (path,))
            _dup_groups(con, {old_cid, cid})
            con.commit()
            files_read += 1
        # Historical spawn results (v3 backfill) use only the time left. They are not
        # freshness: pending files here never make the pass PARTIAL, which would turn
        # the burn alarm into MONITOR_FAILURE while the live index is current.
        backfill_pending = _backfill_spawns(con, t_end)
        files_with_errors = con.execute(
            "SELECT count(*) FROM files WHERE error IS NOT NULL").fetchone()[0]
        skipped_shapes = _census_skipped(Path(proj), matched) if Path(proj).is_dir() else None
        if skipped_shapes is not None:
            con.execute("INSERT OR REPLACE INTO meta VALUES('skipped_shapes', ?)",
                        (json.dumps(skipped_shapes),))
            con.commit()
    except Exception as e:  # noqa: BLE001 -- typed, never silent
        status, err = "FAILED", f"{type(e).__name__}: {e}"
    now = time.time()
    wall_s = round(time.monotonic() - t0, 3)
    con.execute("INSERT OR REPLACE INTO meta VALUES('last_refresh_status', ?)",
                (json.dumps({"status": status, "at": now, "error": err,
                             "pending": pending, "backfill_pending": backfill_pending,
                             "files_opened": files_opened, "bytes_read": bytes_read,
                             "bytes_ingested": bytes_ingested, "files_seen": files_seen,
                             "parse_errors": parse_errors, "files_with_errors": files_with_errors,
                             "wall_s": wall_s}),))
    if status == "OK":
        con.execute("INSERT OR REPLACE INTO meta VALUES('last_ok_at', ?)", (str(now),))
    con.commit()
    return {"status": status, "files_read": files_read, "calls_upserted": upserts,
            "pending": pending, "backfill_pending": backfill_pending, "error": err,
            "files_opened": files_opened, "bytes_read": bytes_read,
            "bytes_ingested": bytes_ingested, "files_seen": files_seen, "wall_s": wall_s,
            "skipped_shapes": skipped_shapes, "parse_errors": parse_errors,
            "files_with_errors": files_with_errors}


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


POP_FIELDS = ("sessions_active", "sessions_dead", "calls", "input", "cache_write",
              "cache_read", "output")
POP_EXIT = {"MEASURED": 0, "EXACT": 0, "DRIFTED": 1, "UNMEASURED": 3}


def _session_of(path: str, is_sub: int) -> tuple[str, str]:
    """(project, session_key) from the transcript path alone (pure string work). A main
    transcript is <store>/<session>.jsonl; a subagent one is
    <store>/<session>/subagents/<agent>.jsonl and belongs to its parent session."""
    p = Path(path)
    if is_sub:
        return p.parent.parent.parent.name, p.parent.parent.name
    return p.parent.name, p.stem


def population(con, *, until=None, project_filter=None, select=None, include_archived=False,
               expected=None, host=None) -> dict:
    """Typed answer to "what does the index say about this population of sessions".

    A session is (archived, project, session_key); it is ACTIVE when it has at least one
    call occurrence (call_files, ts <= until when given), DEAD otherwise. The verdict is
    UNMEASURED, never zero, when nothing is in scope, when the index is below v5, or when
    an in-scope file was never read under v5 (its v5 facts are unknown). MEASURED when
    `expected` is None; EXACT or DRIFTED against `expected` (a dict of POP_FIELDS).
    `project_filter` is a substring of the project name; `select` None or "all" is every
    session (richer selectors arrive with plan 04 and are refused, not guessed)."""
    zero = {k: 0 for k in POP_FIELDS}
    out = {"verdict": "UNMEASURED", "reasons": [], "host": host, "population": dict(zero),
           "per_project": {}}
    cols = {r[1] for r in con.execute("PRAGMA table_info(files)")}
    if not {"v5_from", "archived", "project", "session_key"} <= cols:
        out["reasons"].append("index is below schema v5 (files.v5_from absent): run refresh")
        return out
    if select not in (None, "all"):
        out["reasons"].append(f"selector {select!r} is not available in this build")
        return out
    rows = con.execute(
        "SELECT f.path, f.is_sub, f.v5_from, f.archived, f.project, f.session_key, "
        "count(c.k), coalesce(sum(c.inp),0), coalesce(sum(c.cw),0), coalesce(sum(c.cr),0), "
        "coalesce(sum(c.out),0) FROM files f "
        "LEFT JOIN call_files c ON c.file = f.path AND (? IS NULL OR c.ts <= ?) "
        "GROUP BY f.path", (until, until)).fetchall()
    sessions: dict = {}
    in_scope = unknown = 0
    live_keys = {(r[4] or _session_of(r[0], r[1] or 0)[0], r[5] or _session_of(r[0], r[1] or 0)[1])
                 for r in rows if not r[3]}
    for path, is_sub, v5_from, archived, project, skey, n, inp, cw, cr, outp in rows:
        d_proj, d_sess = _session_of(path, is_sub or 0)
        project, skey = project or d_proj, skey or d_sess
        if archived and not include_archived:
            continue
        if archived and (project, skey) in live_keys:      # ARCHIVED_RULE: the live twin wins
            continue
        if project_filter and project_filter not in project:
            continue
        in_scope += 1
        unknown += v5_from is None
        s = sessions.setdefault((int(bool(archived)), project, skey), [0, 0, 0, 0, 0])
        for i, v in enumerate((n, inp, cw, cr, outp)):
            s[i] += v
    if not in_scope:
        out["reasons"].append("no file in scope")
    if unknown:
        out["reasons"].append(f"{unknown} in-scope file(s) were never read under v5 "
                              "(v5_from NULL): their v5 facts are unknown, not zero")
    pop = dict(zero)
    per: dict = {}
    for (_arch, project, _skey), (n, inp, cw, cr, outp) in sessions.items():
        pp = per.setdefault(project, dict(zero))
        for tgt in (pop, pp):
            tgt["sessions_active" if n else "sessions_dead"] += 1
            tgt["calls"] += n
            tgt["input"] += inp
            tgt["cache_write"] += cw
            tgt["cache_read"] += cr
            tgt["output"] += outp
    out["population"], out["per_project"] = pop, per
    if out["reasons"]:
        return out
    if expected is None:
        out["verdict"] = "MEASURED"
        return out
    drift = {k: {"expected": expected[k], "got": pop.get(k)} for k in expected
             if pop.get(k) != expected[k]}
    out["verdict"] = "DRIFTED" if drift else "EXACT"
    if drift:
        out["drift"] = drift
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("cmd", choices=["refresh", "window", "burn", "replay", "holdout", "population"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--proj", default=str(DEFAULT_PROJ))
    ap.add_argument("--deadline", type=float, default=600.0)
    ap.add_argument("--since-days", type=float, default=21.0)
    ap.add_argument("--at", default=None)
    ap.add_argument("--until", default=None)
    ap.add_argument("--step-h", type=float, default=1.0)
    ap.add_argument("--project-filter", default=None)
    ap.add_argument("--select", default=None)
    ap.add_argument("--include-archived", action="store_true")
    ap.add_argument("--expect", default=None, help="JSON object of population fields, or a file of it")
    ap.add_argument("--plane", default=None, help="host/plane label carried into the answer")
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
    if a.cmd == "population":
        expected = None
        if a.expect:
            src = Path(a.expect)
            expected = json.loads(src.read_text(encoding="utf-8") if src.is_file() else a.expect)
        res = population(con, until=_epoch(a.until) if a.until else None,
                         project_filter=a.project_filter, select=a.select,
                         include_archived=a.include_archived, expected=expected, host=a.plane)
        print(json.dumps(res, indent=1))
        return POP_EXIT[res["verdict"]]
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
