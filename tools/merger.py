#!/usr/bin/env python3
"""merger.py - Sovereign History Vault unifier.

Merges all Cursor SQLite chat turns (live + .backup + reconstructed .old +
reconstructed .fix-copy + workspaces) with the .jsonl transcript corpus
into SOVEREIGN-HISTORY-VAULT.jsonl + sidecar .db. Precedence ladder with
longest-text tiebreak; jsonl is a disjoint id-space (source=jsonl).
"""
from __future__ import annotations

import os
import re
import sys
import glob
import json
import shutil
import sqlite3
import hashlib
import argparse
import tempfile
import subprocess
from collections import Counter
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sovereign_miner as v1  # reuse iter_lines + line_text

OUT_DIR = (os.environ.get("SOVEREIGN_MINER_OUT_DIR")
           or r"C:\Users\User\Downloads\PowerPack_Sovereign_Datasets")
RECON_DIR = os.path.join(OUT_DIR, "_reconstructed")
CURSOR_USER = (os.environ.get("SOVEREIGN_MINER_CURSOR_DIR")
               or os.path.expandvars(r"%APPDATA%\Cursor\User"))
GLOBAL_DIR = os.path.join(CURSOR_USER, "globalStorage")
WORKSPACE_DIR = os.path.join(CURSOR_USER, "workspaceStorage")
PROJECTS_DIR = r"C:\Users\User\.claude\projects"

# Source priority: lower number = higher precedence.
P_LIVE = 10
P_BACKUP = 20
P_REC_OLD = 30
P_REC_FIX = 40
P_WORKSPACE = 50
P_JSONL = 90

# Dedup store for SQLite turns: (composer_id, bubble_id) -> Record dict.
SQL_TURNS: dict[tuple, dict] = {}
# Per-source counters for honest manifest.
PER_SOURCE: Counter = Counter()
DEGRADED: list[str] = []
EXCLUSIVE_PROBE = {"live_backup_cids": set(), "recovered_cids": set()}


def _copy_trio(src: str, tmpd: str) -> str:
    dst = os.path.join(tmpd, os.path.basename(src))
    shutil.copy2(src, dst)
    for sfx in ("-wal", "-shm"):
        if os.path.isfile(src + sfx):
            try:
                shutil.copy2(src + sfx, dst + sfx)
            except OSError:
                pass
    return dst


def _record(cid: str, bid: str, role: str, text: str, source: str,
            priority: int, ts: Optional[str], ts_source: str,
            project: Optional[str]):
    key = (cid, bid)
    existing = SQL_TURNS.get(key)
    if existing is None:
        SQL_TURNS[key] = {
            "composer_id": cid, "bubble_id": bid, "role": role,
            "text": text, "text_len": len(text), "source": source,
            "source_priority": priority, "ts": ts, "ts_source": ts_source,
            "project": project,
        }
        return True
    # Same-priority -> longest-text tiebreak (ans#3).
    if priority < existing["source_priority"]:
        SQL_TURNS[key].update({
            "role": role, "text": text, "text_len": len(text),
            "source": source, "source_priority": priority, "ts": ts,
            "ts_source": ts_source, "project": project,
        })
        return True
    if priority == existing["source_priority"] and len(text) > existing["text_len"]:
        SQL_TURNS[key].update({
            "role": role, "text": text, "text_len": len(text),
        })
        return True
    return False


def _deep_text(obj, depth=0):
    """Walk nested JSON for the longest non-empty text-bearing string.
    Cursor bubbles often have top-level text='' and the real content
    nested in codeBlocks, toolFormerData.params, etc."""
    if depth > 8 or obj is None:
        return ""
    best = ""
    if isinstance(obj, dict):
        for k in ("text", "streamingContent", "content", "richText"):
            v = obj.get(k)
            if isinstance(v, str) and len(v) > len(best):
                best = v
        for v in obj.values():
            cand = _deep_text(v, depth + 1)
            if len(cand) > len(best):
                best = cand
    elif isinstance(obj, list):
        for item in obj:
            cand = _deep_text(item, depth + 1)
            if len(cand) > len(best):
                best = cand
    return best


def _harvest_pair(rows, source: str, priority: int, composer_ts: dict,
                  project: Optional[str]):
    """Process (key,value) rows from cursorDiskKV or lost_and_found."""
    new = 0
    for key, val in rows:
        if not val:
            continue
        if isinstance(val, (bytes, bytearray)):
            try:
                val = val.decode("utf-8", "replace")
            except Exception:
                continue
        try:
            obj = json.loads(val)
        except (ValueError, TypeError):
            continue
        if not isinstance(obj, dict):
            continue
        # composerData rows: record createdAt for ts mapping.
        if isinstance(key, str) and key.startswith("composerData:"):
            cid = (obj.get("composerId")
                   or key.split(":", 1)[1] if ":" in key else None)
            if cid and obj.get("createdAt"):
                composer_ts[cid] = obj["createdAt"]
            continue
        # bubbleId rows: extract role + text (deep-walk for nested content).
        bid = obj.get("bubbleId")
        cid = obj.get("composerId")
        if not bid:
            if isinstance(key, str) and key.startswith("bubbleId:"):
                parts = key.split(":")
                if len(parts) >= 3:
                    cid = cid or parts[1]
                    bid = parts[-1]
        text = obj.get("text") or _deep_text(obj)
        if not (text and isinstance(text, str) and text.strip()):
            continue
        cid = cid or "_unknown"
        role = "assistant" if obj.get("type") == 2 else "user"
        ts_raw = composer_ts.get(cid)
        ts_source = "composerData.createdAt" if ts_raw else "absent"
        if _record(cid, bid or hashlib.md5(text.encode()).hexdigest(),
                   role, text, source, priority, ts_raw, ts_source, project):
            new += 1
    return new


def _safe_open(db_path: str):
    """Open RO with WAL replay if possible; immutable as fallback."""
    for uri in (f"file:{db_path}?mode=ro",
                f"file:{db_path}?immutable=1&mode=ro"):
        try:
            con = sqlite3.connect(uri, uri=True, timeout=5)
            con.cursor().execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
            return con
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            continue
    return None


_SCRAPE_TEXT = re.compile(
    r'"text"\s*:\s*"((?:[^"\\]|\\.){10,4000})"')
_SCRAPE_BID = re.compile(r'"bubbleId"\s*:\s*"([0-9a-f-]{8,})"')
_SCRAPE_CID = re.compile(r'"composerId"\s*:\s*"([0-9a-f-]{8,})"')


def _byte_scrape_db(db_path: str, source_name: str, priority: int,
                    project: Optional[str]) -> int:
    """Raw-byte regex floor pass — recovers `text` field matches from
    nested objects, hex blobs and pages the structured cursor missed.
    Same source/priority as the structured pass +5 sub-priority so
    structured wins ties via the ladder."""
    new = 0
    try:
        with open(db_path, "rb") as fh:
            blob = fh.read()
    except OSError:
        return 0
    decoded = blob.decode("utf-8", "replace")
    cids = _SCRAPE_CID.findall(decoded)
    bids = _SCRAPE_BID.findall(decoded)
    cid_default = cids[0] if cids else "_scraped"
    for i, m in enumerate(_SCRAPE_TEXT.finditer(decoded)):
        text = m.group(1)
        if len(text) < 10:
            continue
        cid = cids[min(i, len(cids) - 1)] if cids else cid_default
        bid = (bids[i] if i < len(bids)
               else hashlib.md5(text.encode()).hexdigest()[:16])
        if _record(cid, bid, "user", text,
                   source_name + ":scrape", priority + 5,
                   None, "absent", project):
            new += 1
    PER_SOURCE[source_name + ":scrape"] += new
    return new


def _mine_db(db_path: str, source_name: str, priority: int,
             project: Optional[str] = None) -> int:
    con = _safe_open(db_path)
    if con is None:
        DEGRADED.append(f"{source_name}: open-failed")
        # Still byte-scrape the file as a recovery floor.
        return _byte_scrape_db(db_path, source_name, priority, project)
    composer_ts: dict = {}
    new_total = 0
    try:
        cur = con.cursor()
        try:
            cur.execute("SELECT key,value FROM cursorDiskKV WHERE "
                        "key LIKE 'bubbleId:%' OR key LIKE 'composerData:%'")
            rows = []
            while True:
                try:
                    batch = cur.fetchmany(200)
                except (sqlite3.DatabaseError, sqlite3.OperationalError):
                    break
                if not batch:
                    break
                rows.extend(batch)
            new_total += _harvest_pair(rows, source_name, priority,
                                       composer_ts, project)
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            pass
        # lost_and_found extraction (reconstructed DBs surface orphan pages here).
        try:
            cur.execute("SELECT c0,c1 FROM lost_and_found WHERE "
                        "c0 LIKE 'bubbleId:%' OR c0 LIKE 'composerData:%'")
            laf = cur.fetchall()
            new_total += _harvest_pair(laf, source_name + "+laf", priority,
                                       composer_ts, project)
        except (sqlite3.DatabaseError, sqlite3.OperationalError):
            pass
    finally:
        try:
            con.close()
        except Exception:
            pass
    PER_SOURCE[source_name] += new_total
    # Byte-scrape floor: recover text from nested fields / hex blobs the
    # structured walker misses (mirrors miner_v2 baseline).
    new_total += _byte_scrape_db(db_path, source_name, priority, project)
    return new_total


def mine_sqlite(skip_live: bool = False):
    tmpd = tempfile.mkdtemp(prefix="merger_")
    try:
        # P2 backup (clean superset) first to avoid live trio-copy until needed.
        for name, prio in (("state.vscdb.backup", P_BACKUP),):
            src = os.path.join(GLOBAL_DIR, name)
            if os.path.isfile(src):
                dst = _copy_trio(src, tmpd)
                _mine_db(dst, name, prio)
        # P1 live (trio-copy with SHA pre/post retry x3 for atomicity).
        if not skip_live:
            live = os.path.join(GLOBAL_DIR, "state.vscdb")
            if os.path.isfile(live):
                for attempt in range(3):
                    attempt_dir = os.path.join(tmpd, f"live_{attempt}")
                    os.makedirs(attempt_dir, exist_ok=True)
                    pre = hashlib.sha256(open(live, "rb").read()).hexdigest()
                    dst = _copy_trio(live, attempt_dir)
                    post = hashlib.sha256(open(live, "rb").read()).hexdigest()
                    if pre == post:
                        _mine_db(dst, "live", P_LIVE)
                        break
                    DEGRADED.append(f"live: mid-copy hash drift attempt {attempt}")
        # P3 + P4 reconstructed.
        for name, prio in (("state.vscdb.old.fixed.db", P_REC_OLD),
                           ("state.vscdb.fix-copy.fixed.db", P_REC_FIX)):
            src = os.path.join(RECON_DIR, name)
            if os.path.isfile(src):
                dst = _copy_trio(src, tmpd)
                tag = "recovered.old" if "old" in name else "recovered.fix-copy"
                before = len(SQL_TURNS)
                _mine_db(dst, tag, prio)
                # Track composerIds added by recovered sources for verdict (iii).
                for (cid, _bid), rec in SQL_TURNS.items():
                    if rec["source"].startswith("recovered"):
                        EXCLUSIVE_PROBE["recovered_cids"].add(cid)
        # Probe live+backup composerIds for exclusion check.
        for (cid, _bid), rec in SQL_TURNS.items():
            if rec["source"] in ("live", "state.vscdb.backup"):
                EXCLUSIVE_PROBE["live_backup_cids"].add(cid)
        # P6 workspace DBs (integrity-checked first).
        wss = sorted(glob.glob(os.path.join(WORKSPACE_DIR, "*", "state.vscdb")))
        for i, ws in enumerate(wss[:25]):  # Gap 6 cap
            if i % 5 == 0:
                sys.stderr.write(f"[merger] workspace {i}/{len(wss[:25])}\n")
                sys.stderr.flush()
            con = _safe_open(ws)
            if con is None:
                DEGRADED.append(f"workspace:{os.path.basename(os.path.dirname(ws))}")
                continue
            try:
                chk = con.cursor().execute("PRAGMA quick_check;").fetchone()
                if chk and chk[0] == "ok":
                    con.close()
                    dst = _copy_trio(ws, tmpd)
                    _mine_db(dst, "workspace",
                             P_WORKSPACE + (i % 10),
                             project=os.path.basename(os.path.dirname(ws)))
                else:
                    con.close()
                    DEGRADED.append(f"workspace:integrity_fail")
            except Exception:
                try:
                    con.close()
                except Exception:
                    pass
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)


def mine_jsonl():
    """Separate union (disjoint id-space, source=jsonl, ans#5)."""
    files = sorted(
        glob.glob(os.path.join(PROJECTS_DIR, "**", "*.jsonl"), recursive=True)
        + glob.glob(os.path.join(PROJECTS_DIR, "**", "*.jsonl.live"),
                    recursive=True))
    jsonl_records = []
    for i, path in enumerate(files):
        if i % 200 == 0:
            sys.stderr.write(f"[merger] jsonl {i}/{len(files)}\n")
            sys.stderr.flush()
        proj = os.path.relpath(path, PROJECTS_DIR).split(os.sep)[0]
        idx = 0
        try:
            for obj in v1.iter_lines(path):
                role, text = v1.line_text(obj)
                if role in ("user", "assistant") and text.strip():
                    jsonl_records.append({
                        "source": "jsonl",
                        "source_priority": P_JSONL,
                        "composer_id": proj,
                        "bubble_id": f"{os.path.basename(path)}#{idx}",
                        "role": role,
                        "text": text,
                        "text_len": len(text),
                        "project": proj,
                        "ts": None,
                        "ts_source": "absent",
                    })
                    idx += 1
        except OSError:
            DEGRADED.append(f"jsonl:{os.path.basename(path)}")
    PER_SOURCE["jsonl"] = len(jsonl_records)
    return jsonl_records


def write_vault(jsonl_records, exclude_live=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    vault_jsonl = os.path.join(OUT_DIR, "SOVEREIGN-HISTORY-VAULT.jsonl")
    vault_db = os.path.join(OUT_DIR, "SOVEREIGN-HISTORY-VAULT.db")
    if os.path.isfile(vault_db):
        os.remove(vault_db)

    sql_records = list(SQL_TURNS.values())
    sql_records.sort(key=lambda r: (r["source_priority"], r["composer_id"],
                                    r["bubble_id"]))
    jsonl_records.sort(key=lambda r: (r["composer_id"], r["bubble_id"]))
    all_records = sql_records + jsonl_records

    with open(vault_jsonl, "w", encoding="utf-8", newline="\n") as fh:
        for r in all_records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    con = sqlite3.connect(vault_db)
    con.execute("""CREATE TABLE turns (
        source TEXT, source_priority INTEGER, composer_id TEXT,
        bubble_id TEXT, role TEXT, text TEXT, text_len INTEGER,
        project TEXT, ts TEXT, ts_source TEXT,
        PRIMARY KEY (source, composer_id, bubble_id))""")
    con.execute("CREATE INDEX idx_composer ON turns(composer_id)")
    con.executemany(
        "INSERT OR REPLACE INTO turns VALUES "
        "(:source,:source_priority,:composer_id,:bubble_id,:role,:text,"
        ":text_len,:project,:ts,:ts_source)", all_records)
    con.commit()
    con.close()
    return vault_jsonl, vault_db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--exclude-live", action="store_true",
                    help="for deterministic SHA verification")
    args = ap.parse_args()
    if not args.build:
        print("usage: merger.py --build [--exclude-live]")
        return 2

    mine_sqlite(skip_live=args.exclude_live)
    jsonl_records = mine_jsonl()
    vault_jsonl, vault_db = write_vault(jsonl_records,
                                         exclude_live=args.exclude_live)

    # Verdict-A hard gates.
    sql_unique = len(SQL_TURNS)
    total_unique = sql_unique + len(jsonl_records)
    exclusive = (EXCLUSIVE_PROBE["recovered_cids"]
                 - EXCLUSIVE_PROBE["live_backup_cids"])

    print("=== MERGER COMPLETE ===")
    print(f"SQL turns (unique): {sql_unique}")
    print(f"JSONL records:      {len(jsonl_records)}")
    print(f"TOTAL unique:       {total_unique}")
    print(f"Per-source: {dict(PER_SOURCE)}")
    print(f"Degraded: {len(DEGRADED)}")
    print(f"Recovered composerIds NOT in live/backup: {len(exclusive)}")
    if exclusive:
        for c in sorted(exclusive)[:5]:
            print(f"  exclusive: {c}")

    sha = hashlib.sha256(open(vault_jsonl, "rb").read()).hexdigest()
    print(f"VAULT_JSONL_SHA256={sha}")
    print(f"VAULT_JSONL_BYTES={os.path.getsize(vault_jsonl)}")
    print(f"VAULT_DB_BYTES={os.path.getsize(vault_db)}")

    fails = []
    if sql_unique <= 434:
        fails.append(f"sql_unique={sql_unique} not > 434")
    if not exclusive:
        fails.append("no composerIds exclusive to recovered sources")
    if fails:
        print("VERDICT-A FAILS:", " | ".join(fails))
        return 5
    print("VERDICT-A PASSES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
