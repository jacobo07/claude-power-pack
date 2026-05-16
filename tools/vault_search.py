#!/usr/bin/env python3
"""vault_search.py - FTS5 fuzzy search + composer retrieval + dedup picker.

CLI surface:
  --build-index           one-shot DDL: FTS5 table + sync triggers
  --search "<q>"          BM25-ranked top-20 with snippet
  --get <composer_id>     all bubbles for one composer, sorted by bubble_id
  --list-open-composers   composer UUIDs currently bound to a Cursor pane
  --list-resumeable [N]   vault composers MINUS open MINUS fresh .jsonl.live

Path source of truth: imports from merger.py (audit Gap #11). FTS5 stays
in sync via triggers; the heartbeat never rebuilds (audit Gap #9).
"""
from __future__ import annotations
import os, sys, json, glob, time, sqlite3, argparse, tempfile, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merger as M

# G3: Windows console is cp1252; the [REC] glyph would raise
# UnicodeEncodeError and crash the picker. Force utf-8 stdout.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

VAULT_DB = os.path.join(M.OUT_DIR, "SOVEREIGN-HISTORY-VAULT.db")
STATE_DIR = os.path.expandvars(r"%USERPROFILE%\.claude\state")
OPEN_CACHE = os.path.join(STATE_DIR, "open-composers.json")
OPEN_TTL = 30  # seconds
RECOVERED_CACHE = os.path.join(STATE_DIR, "recovered-composers.json")
RECOVERED_TTL = 300  # G5: recompute-on-read after 5 min
import re as _re
_UUID_RE = _re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", _re.IGNORECASE)


_FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
    text, content='turns', content_rowid='rowid', tokenize='unicode61');
CREATE TRIGGER IF NOT EXISTS turns_fts_ai AFTER INSERT ON turns BEGIN
  INSERT INTO turns_fts(rowid, text) VALUES (new.rowid, new.text);
END;
CREATE TRIGGER IF NOT EXISTS turns_fts_ad AFTER DELETE ON turns BEGIN
  INSERT INTO turns_fts(turns_fts, rowid, text)
    VALUES ('delete', old.rowid, old.text);
END;
CREATE TRIGGER IF NOT EXISTS turns_fts_au AFTER UPDATE ON turns BEGIN
  INSERT INTO turns_fts(turns_fts, rowid, text)
    VALUES ('delete', old.rowid, old.text);
  INSERT INTO turns_fts(rowid, text) VALUES (new.rowid, new.text);
END;
"""


def ensure_fts():
    """Idempotent schema check. Called by merger.py at end of every
    --build / --incremental run (audit Gap #1)."""
    if not os.path.isfile(VAULT_DB):
        print(f"vault_search: vault not found at {VAULT_DB}", file=sys.stderr)
        return 0
    con = sqlite3.connect(VAULT_DB)
    cur = con.cursor()
    cur.executescript(_FTS_DDL)
    n_idx = cur.execute("SELECT count(*) FROM turns_fts").fetchone()[0]
    n_src = cur.execute("SELECT count(*) FROM turns").fetchone()[0]
    if n_idx < n_src:
        cur.execute("INSERT INTO turns_fts(turns_fts) VALUES ('rebuild')")
        con.commit()
        n_idx = cur.execute("SELECT count(*) FROM turns_fts").fetchone()[0]
    con.close()
    print(f"FTS5 ensure: {n_idx} indexed / {n_src} source rows")
    return 0


def build_index():
    if not os.path.isfile(VAULT_DB):
        print(f"vault_search: vault not found at {VAULT_DB}", file=sys.stderr)
        return 5
    con = sqlite3.connect(VAULT_DB)
    cur = con.cursor()
    # FTS5 contentless-shadow over the existing turns(text) column.
    cur.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
        text, content='turns', content_rowid='rowid', tokenize='unicode61')""")
    # Sync triggers — incremental writes propagate automatically (audit #1).
    cur.executescript("""
    CREATE TRIGGER IF NOT EXISTS turns_fts_ai AFTER INSERT ON turns BEGIN
      INSERT INTO turns_fts(rowid, text) VALUES (new.rowid, new.text);
    END;
    CREATE TRIGGER IF NOT EXISTS turns_fts_ad AFTER DELETE ON turns BEGIN
      INSERT INTO turns_fts(turns_fts, rowid, text)
        VALUES ('delete', old.rowid, old.text);
    END;
    CREATE TRIGGER IF NOT EXISTS turns_fts_au AFTER UPDATE ON turns BEGIN
      INSERT INTO turns_fts(turns_fts, rowid, text)
        VALUES ('delete', old.rowid, old.text);
      INSERT INTO turns_fts(rowid, text) VALUES (new.rowid, new.text);
    END;
    """)
    # Initial population (one-shot 'rebuild' against the current `turns`).
    cur.execute("INSERT INTO turns_fts(turns_fts) VALUES ('rebuild')")
    con.commit()
    n = cur.execute("SELECT count(*) FROM turns_fts").fetchone()[0]
    con.close()
    print(f"FTS5 index built: {n} rows indexed at {VAULT_DB}")
    return 0


def search(query, limit=20):
    if not os.path.isfile(VAULT_DB):
        return 5
    con = sqlite3.connect(VAULT_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    try:
        rows = cur.execute("""
            SELECT t.composer_id, t.bubble_id, t.project, t.role,
                   snippet(turns_fts, 0, '[[', ']]', '...', 16) AS snip,
                   bm25(turns_fts) AS rank
            FROM turns_fts JOIN turns t ON t.rowid = turns_fts.rowid
            WHERE turns_fts MATCH ? ORDER BY rank LIMIT ?
        """, (query, limit)).fetchall()
    except sqlite3.OperationalError as e:
        print(f"vault_search: FTS5 not built? {e}", file=sys.stderr)
        con.close()
        return 5
    con.close()
    print(f"# search: {query!r} -> {len(rows)} hits")
    for r in rows:
        proj = (r["project"] or "")[:30]
        print(f"  rank={r['rank']:+.2f}  {r['composer_id'][:10]}.. "
              f"[{r['role'][:5]:5}] {proj:30} {r['snip']}")
    return 0


def get_composer(cid):
    if not os.path.isfile(VAULT_DB):
        return 5
    con = sqlite3.connect(VAULT_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rows = cur.execute(
        "SELECT role,text,bubble_id,source,project FROM turns "
        "WHERE composer_id=? ORDER BY bubble_id", (cid,)).fetchall()
    con.close()
    if not rows:
        print(f"# no bubbles for composer_id={cid}", file=sys.stderr)
        return 5
    print(f"# composer_id={cid}  bubbles={len(rows)}  "
          f"project={rows[0]['project'] or '?'}")
    print('<retrieved-history readonly="true" composer_id="' + cid + '">')
    for r in rows:
        print(f"\n## [{r['role']}]  bubble={r['bubble_id'][:24]}  "
              f"src={r['source']}")
        print(r["text"])
    print("</retrieved-history>")
    return 0


def list_open_composers():
    """Scan all Cursor workspace DBs for registered composer panes.
    Returns set of UUIDs. Cached at OPEN_CACHE for 30s (audit Gap #6).
    """
    if (os.path.isfile(OPEN_CACHE)
            and time.time() - os.path.getmtime(OPEN_CACHE) < OPEN_TTL):
        try:
            return set(json.load(open(OPEN_CACHE, encoding="utf-8-sig")))
        except (OSError, ValueError):
            pass
    open_ids = set()
    ws_pattern = os.path.join(M.WORKSPACE_DIR, "*", "state.vscdb")
    tmpd = tempfile.mkdtemp(prefix="vs_open_")
    try:
        for ws in sorted(glob.glob(ws_pattern)):
            try:
                d = os.path.join(tmpd, os.path.basename(os.path.dirname(ws)) + ".db")
                shutil.copy2(ws, d)
            except OSError:
                continue
            con = M._safe_open(d)
            if con is None:
                continue
            try:
                cur = con.cursor()
                cur.execute(
                    "SELECT key, value FROM ItemTable WHERE "
                    "key LIKE 'workbench.panel.composerChatViewPane.%'")
                for key, val in cur.fetchall():
                    uuid = key.rsplit(".", 1)[-1].split(".hidden")[0]
                    # Try to parse value; default to "open" if parse fails.
                    visible = True
                    if val:
                        try:
                            obj = json.loads(val.decode() if isinstance(
                                val, (bytes, bytearray)) else val)
                            if isinstance(obj, list) and obj:
                                visible = not obj[0].get("isHidden", False)
                            elif isinstance(obj, dict):
                                visible = not obj.get("isHidden", False)
                        except (ValueError, AttributeError):
                            pass
                    if visible:
                        open_ids.add(uuid)
            except (sqlite3.DatabaseError, sqlite3.OperationalError):
                pass
            finally:
                try:
                    con.close()
                except Exception:
                    pass
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump(sorted(open_ids), open(OPEN_CACHE, "w", encoding="utf-8",
                                     newline="\n"))
    return open_ids


def _live_jsonl_uuids():
    """UUIDs that appear as a .jsonl / .jsonl.live filename under projects.
    These are the live-counterpart UUIDs (id-space matches SQLite cids)."""
    uuids = set()
    base = r"C:\\Users\\User\\.claude\\projects"
    for pat in ("*.jsonl", "*.jsonl.live"):
        for p in glob.glob(os.path.join(base, "**", pat), recursive=True):
            stem = os.path.basename(p)
            if stem.endswith(".jsonl.live"):
                stem = stem[: -len(".jsonl.live")]
            elif stem.endswith(".jsonl"):
                stem = stem[: -len(".jsonl")]
            uuids.add(stem.lower())
    return uuids


def compute_recovered():
    """Return {cid: {"project": str, "bubbles": int}} for RECOVERED-orphan
    composers. G2: orphan-only signal (no bubble-count branch — id-space
    split makes a live-counterpart join undefined). A cid qualifies iff:
      - it is UUID-shaped, AND
      - it has >=1 vault row with source LIKE 'recovered.old%', AND
      - its UUID is NOT a live .jsonl/.jsonl.live filename, AND
      - it has 0 vault rows from source live%/backup/workspace."""
    if not os.path.isfile(VAULT_DB):
        return {}
    con = sqlite3.connect(VAULT_DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rec_rows = cur.execute(
        "SELECT composer_id, project, count(*) AS n FROM turns "
        "WHERE source LIKE 'recovered.old%' GROUP BY composer_id"
    ).fetchall()
    # Same-id-space 'live counterpart' presence set.
    live_present = set(r[0] for r in cur.execute(
        "SELECT DISTINCT composer_id FROM turns WHERE "
        "source LIKE 'live%' OR source LIKE 'state.vscdb.backup%' "
        "OR source LIKE 'workspace%'"
    ).fetchall())
    con.close()
    live_files = _live_jsonl_uuids()
    out = {}
    for r in rec_rows:
        cid = r["composer_id"]
        if not cid or not _UUID_RE.match(cid):
            continue
        if cid.lower() in live_files:
            continue
        if cid in live_present:
            continue
        out[cid] = {"project": r["project"] or "?", "bubbles": int(r["n"])}
    return out


def _read_recovered_cache():
    try:
        if (os.path.isfile(RECOVERED_CACHE)
                and time.time() - os.path.getmtime(RECOVERED_CACHE)
                < RECOVERED_TTL):
            with open(RECOVERED_CACHE, encoding="utf-8-sig") as fh:
                obj = json.load(fh)
            if isinstance(obj, dict) and "composers" in obj:
                return obj["composers"]
    except (OSError, ValueError):
        pass
    return None


def write_recovered_cache():
    rec = compute_recovered()
    os.makedirs(STATE_DIR, exist_ok=True)
    payload = {
        "generated": time.time(),
        "ttl_sec": RECOVERED_TTL,
        "count": len(rec),
        "composers": rec,
        # project -> list[cid] reverse map for the SessionStart hook (G1:
        # SessionStart has no composerId, only cwd/project).
        "projects": _projects_map(rec),
    }
    tmp = RECOVERED_CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, sort_keys=True, indent=1)
    os.replace(tmp, RECOVERED_CACHE)
    return rec


def _projects_map(rec):
    pm = {}
    for cid, meta in rec.items():
        pm.setdefault(meta["project"], []).append(cid)
    for k in pm:
        pm[k] = sorted(pm[k])
    return pm


def recovered_set():
    """Cached membership set for callers (hook, picker). Recompute on TTL."""
    cached = _read_recovered_cache()
    if cached is not None:
        return cached
    return write_recovered_cache()


def list_recovered(top_n=40):
    rec = write_recovered_cache()  # always fresh on explicit list
    items = sorted(rec.items(), key=lambda kv: (-kv[1]["bubbles"], kv[0]))
    print("# RECOVERED-orphan composers (source=recovered.old%, "
          "UUID-shaped, no live .jsonl/.jsonl.live, no live/backup/ws row)")
    shown = 0
    for cid, meta in items[:top_n]:
        proj = (meta["project"] or "")[:32]
        print(f"  [REC] \U0001f7e9 {cid}  bubbles={meta['bubbles']:>3}  "
              f"proj={proj}")
        shown += 1
    print(f"# total recovered-orphan: {len(rec)}  (cache: {RECOVERED_CACHE})")
    return 0 if rec else 5


def list_resumeable(top_n=40):
    if not os.path.isfile(VAULT_DB):
        return 5
    open_ids = list_open_composers()
    # Fresh .jsonl.live exclusion (mtime < 60s).
    fresh = set()
    now = time.time()
    for p in glob.glob(os.path.join(
            r"C:\Users\User\.claude\projects", "**", "*.jsonl.live"),
            recursive=True):
        if now - os.path.getmtime(p) < 60:
            fresh.add(os.path.basename(p).rsplit(".", 2)[0])  # strip .jsonl.live
    con = sqlite3.connect(VAULT_DB)
    con.row_factory = sqlite3.Row
    rows = con.cursor().execute("""
        SELECT composer_id, project, count(*) AS n,
               max(text_len) AS longest
        FROM turns WHERE source != 'jsonl'
        GROUP BY composer_id ORDER BY n DESC LIMIT ?
    """, (top_n,)).fetchall()
    con.close()
    rec = recovered_set()
    print(f"# resumeable composers (vault SQL turns, "
          f"excluding {len(open_ids)} open + {len(fresh)} live; "
          f"{len(rec)} flagged [REC])")
    shown = 0
    for r in rows:
        if r["composer_id"] in open_ids or r["composer_id"] in fresh:
            continue
        proj = (r["project"] or "")[:32]
        # G3/Q5a: ASCII '[REC]' first then the glyph, so a cp1252 fallback
        # still shows the marker even if the emoji is replaced.
        mark = "[REC] \U0001f7e9 " if r["composer_id"] in rec else ""
        print(f"  {mark}{r['composer_id'][:36]}  bubbles={r['n']:>3}  "
              f"longest={r['longest']:>5}  proj={proj}")
        shown += 1
    print(f"# total resumeable: {shown}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-index", action="store_true")
    ap.add_argument("--ensure-fts", action="store_true",
                    help="idempotent schema check (called by merger.py)")
    ap.add_argument("--search", metavar="QUERY")
    ap.add_argument("--get", metavar="COMPOSER_ID")
    ap.add_argument("--list-open-composers", action="store_true")
    ap.add_argument("--list-resumeable", type=int, nargs="?", const=40)
    ap.add_argument("--list-recovered", type=int, nargs="?", const=40,
                    help="RECOVERED-orphan composers from .old (G1/G2)")
    ap.add_argument("--write-recovered-cache", action="store_true",
                    help="refresh ~/.claude/state/recovered-composers.json")
    a = ap.parse_args()
    if a.build_index:
        return build_index()
    if a.ensure_fts:
        return ensure_fts()
    if a.search:
        return search(a.search)
    if a.get:
        return get_composer(a.get)
    if a.list_open_composers:
        ids = list_open_composers()
        print(f"# open composers: {len(ids)}")
        for u in sorted(ids):
            print(f"  {u}")
        return 0
    if a.write_recovered_cache:
        rec = write_recovered_cache()
        print(f"recovered-composers.json written: {len(rec)} composers")
        return 0
    if a.list_recovered is not None:
        return list_recovered(a.list_recovered)
    if a.list_resumeable is not None:
        return list_resumeable(a.list_resumeable)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
