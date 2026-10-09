#!/usr/bin/env python3
"""Prompt Recall -- the knowledge relevant to THIS prompt, not a constant reminder.

Spec: vault/specs/prompt-recall.md. Owner of the effect is modules/gsd_x/cli.py (one
injection owner on UserPromptSubmit); this module is its index and its query.

A session used to start with pointers only. Memories without an index line (~912 across
12 projects, 2026-10-09) were unreachable, and UKDL / HARD-RULES reached a session only if
the model happened to open them. Recall indexes every entry into an isolated FTS5 sidecar
and returns the few that share rare terms with the prompt.

The hook path never builds the index: building costs seconds and the prompt chain has a
3000 ms deadline. A stale or missing index launches ONE detached refresh (lock file) and
the prompt is served from whatever index exists. Fail-open everywhere: any error is "".

    python -m modules.gsd_x.recall --refresh            # (re)index changed files
    python -m modules.gsd_x.recall --query "<text>"     # what a prompt would see
    python -m modules.gsd_x.recall --stats
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

HOME = Path.home()
PP_ROOT = Path(__file__).resolve().parents[2]
SWITCH = "CPP_RECALL"
STALE_S = 600              # index older than this triggers one background refresh
LOCK_STALE_S = 600         # a lock older than this belongs to a dead refresh
READ_TIMEOUT_S = 0.2       # hook-side readers: give up fast rather than eat the chain deadline
TOP_K = 5
SNIPPET = 260
MAX_TERMS = 12
COMMON_DF = 0.15           # a term in more than 15% of chunks carries no signal
MIN_MATCHED = 3            # distinct query terms a hit must contain
SHOWN_KEEP_S = 7 * 86400
# The 2,000-answer SEO/GEO corpus every project must consult (rule seo-geo-corpus-methodology).
SEO_CORPUS = HOME / "Desktop" / "Cursor Projects" / "GEO-audit" / "docs" / "corpus"
# Kinds that are not institutional truth: labelled in the block, at most one hit per prompt.
UNVALIDATED = {"candidate": "UNVALIDATED external answer, KACQ candidate (HR-ACQ-NO-AUTOPROMOTION-001)",
               "seo-geo": "SEO/GEO corpus: METHOD not DATA, grade E1-E2, cite the SG-ID"}
MAX_UNVALIDATED = 1
# Bump whenever chunk_file's output for an existing kind changes: refresh() then re-cuts all.
CHUNKER = "2"

STOP = set("""
a about above after again all also am an and any are as at be because been before being
below between both but by can could did do does doing done down during each else even
every few for from further get got had has have having he her here hers him his how i if
in into is it its itself just let like make many may me more most much must my need no
nor not now of off on once only or other our out over own please same she should show so
some such than that the their them then there these they this those through to too try
under until up use used using very want was way we well were what when where which while
who why will with would yes you your yours
al algo ante antes aqui asi aun bien cada como con contra cual cuando de del desde donde
dos el ella ellas ellos en entre era eres es esa ese eso esta estan estas este esto estos
fue haber hace hacer hay hasta la las le les lo los mas me mi mis mucho muy nada ni no nos
nuestro o otra otro para pero poco por porque puede que quien se sea ser si sin sobre solo
son su sus tambien te tengo ti tiene todo todos tu tus un una uno unos ya yo
""".split())

_HEADING = re.compile(r"^#{1,4}\s+(.+)")
_BOLD_ID = re.compile(r"^\*\*`?([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)`?\*\*")
_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
_WORD = re.compile(r"[^\W_]+", re.U)


def state_dir() -> Path:
    d = Path(os.environ.get("CPP_RECALL_DIR") or (HOME / ".claude" / "state" / "recall"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return state_dir() / "recall.db"


def default_sources() -> list:
    """(path, kind, scope) for every file the index covers. Discovered, never curated."""
    out = []
    projects = HOME / ".claude" / "projects"
    if projects.is_dir():
        for mem in projects.glob("*/memory"):
            for f in mem.glob("*.md"):
                if not f.name.startswith("MEMORY"):     # indexes, sub-indexes, catalog
                    out.append((f, "memory", mem.parent.name))
    kb = PP_ROOT / "vault" / "knowledge_base"
    for f, kind in ((kb / "ukdl-universal.md", "ukdl"),
                    (HOME / ".claude" / "knowledge_vault" / "core" / "HARD-RULES.md", "hard-rules"),
                    (kb / "clae" / "CLAE_PROCESS_RULES.md", "clae"),
                    (kb / "clae" / "CLAE_TRAPS.md", "clae")):
        if f.is_file():
            out.append((f, kind, "global"))
    # Plans carry sealed ids that never reached UKDL (F6: 23 plans), so they are a source too.
    plans = PP_ROOT / "vault" / "plans"
    if plans.is_dir():
        out.extend((f, "plan", "global") for f in plans.glob("*.md"))
    # UNVALIDATED kinds (see UNVALIDATED): captured external answers stop at a validation
    # queue (HR-ACQ-NO-AUTOPROMOTION-001); showing one labelled as a candidate is not
    # promoting it.
    raw = PP_ROOT / "vault" / "knowledge_acquisition" / "raw" / "response"
    if raw.is_dir():
        out.extend((f, "candidate", "kacq") for f in raw.glob("*/*.md"))
    seo = Path(os.environ.get("CPP_RECALL_SEO_CORPUS") or SEO_CORPUS)
    if seo.is_dir():
        out.extend((f, "seo-geo", "global") for f in (seo / "mapping").glob("corpus_map_*.md"))
        out.extend((f, "seo-geo", "global") for f in (seo / "answers").glob("*-full.jsonl"))
    return out


def project_scope(cwd: str) -> str:
    """The ~/.claude/projects directory name the harness derives from a cwd."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd or "")


def fold(text: str) -> str:
    """Lowercase, diacritics removed: the same folding the FTS5 tokenizer applies."""
    t = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# --------------------------------------------------------------------- chunking

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def chunk_memory(text: str, fallback_title: str) -> list:
    title, desc, body = fallback_title, "", text
    m = _FRONT.match(text)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if k.strip() == "name" and v.strip():
                title = v.strip()
            elif k.strip() == "description":
                desc = v.strip()
    joined = (desc + "\n" + body).strip()
    return [(title, joined[:6000])] if joined else []


def chunk_rules(text: str) -> list:
    """Split at a heading or a bold-id paragraph; long sections split again at blank lines."""
    text = _FRONT.sub("", text, count=1)
    chunks, title, section, buf = [], "", "", []

    def flush():
        body = "\n".join(buf).strip()
        if len(re.sub(r"\s", "", body)) >= 40:
            chunks.append((title or section, body[:6000]))

    for line in text.splitlines():
        h, b = _HEADING.match(line), _BOLD_ID.match(line)
        if h or b:
            flush()
            buf = [line]
            if h:
                section = title = h.group(1).strip()
            else:
                title = b.group(1)
            continue
        if not line.strip() and sum(len(x) for x in buf) > 1200:
            flush()
            buf, title = [], section
            continue
        buf.append(line)
    flush()
    return chunks


def chunk_candidate(path: Path) -> list:
    """A KACQ response, titled by the question it answers (the response alone has none). The
    question lives in raw/prompt/<id[:2]>/<id>.md, named by the response's .meta.json."""
    body = _read(path).strip()
    question = ""
    try:
        meta = json.loads(_read(path.with_suffix("").with_suffix(".meta.json")))
        pid = str(meta.get("prompt_id") or "")
        q = path.parents[2] / "prompt" / pid[:2] / ("%s.md" % pid)
        question = " ".join(_read(q).split()) if pid and q.is_file() else ""
    except (OSError, ValueError):
        pass
    if not body:
        return []
    return [((question or path.stem)[:160], (question + "\n" + body).strip()[:6000])]


def chunk_jsonl(path: Path) -> list:
    """One record per line ({id, question, answer}), as the SEO/GEO corpus stores it."""
    out = []
    for line in _read(path).splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        q, a = str(rec.get("question") or ""), str(rec.get("answer") or "")
        if q or a:
            out.append(("%s %s" % (rec.get("id", ""), q[:140]), (q + "\n" + a).strip()[:6000]))
    return out


def chunk_file(path: Path, kind: str) -> list:
    if kind == "candidate":
        return chunk_candidate(path)
    if path.suffix == ".jsonl":
        return chunk_jsonl(path)
    text = _read(path)
    return chunk_memory(text, path.stem) if kind == "memory" else chunk_rules(text)


# ------------------------------------------------------------------------ index

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, mtime_ns INTEGER, size INTEGER,
                                  kind TEXT, scope TEXT);
CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, path TEXT, title TEXT, body TEXT);
CREATE INDEX IF NOT EXISTS chunks_path ON chunks(path);
CREATE VIRTUAL TABLE IF NOT EXISTS recall_fts USING fts5(title, body,
    tokenize = 'unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE IF NOT EXISTS recall_vocab USING fts5vocab(recall_fts, 'row');
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""


def connect(path: Path) -> sqlite3.Connection:
    """Writer connection. WAL is persistent in the file, so the hook's readers never wait on a
    refresh that holds its write transaction for seconds (review M1)."""
    con = sqlite3.connect(str(path), timeout=2.0)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def _reader(path) -> sqlite3.Connection:
    return sqlite3.connect(str(path), timeout=READ_TIMEOUT_S)


def _drop(con, path: str) -> None:
    ids = [r[0] for r in con.execute("SELECT id FROM chunks WHERE path=?", (path,))]
    con.executemany("DELETE FROM recall_fts WHERE rowid=?", [(i,) for i in ids])
    con.execute("DELETE FROM chunks WHERE path=?", (path,))
    con.execute("DELETE FROM files WHERE path=?", (path,))


def refresh(sources=None, db=None) -> dict:
    """Re-chunk changed files, drop removed ones. Returns counts.

    A file is unchanged only if its (mtime, size, kind) AND the chunker that cut it are the
    same: a file indexed by an older chunker is never touched again otherwise (measured: the
    KACQ answers and the SEO jsonl stayed rule-split after their own chunkers landed)."""
    sources = default_sources() if sources is None else sources
    con = connect(db or db_path())
    seen, changed, removed = set(), 0, 0
    try:
        known = {r[0]: (r[1], r[2], r[3])
                 for r in con.execute("SELECT path, mtime_ns, size, kind FROM files")}
        row = con.execute("SELECT v FROM meta WHERE k='chunker'").fetchone()
        stale_chunker = not row or row[0] != CHUNKER
        con.execute("BEGIN")
        for path, kind, scope in sources:
            p = str(path)
            try:
                st = os.stat(p)
            except OSError:
                continue
            seen.add(p)
            if not stale_chunker and known.get(p) == (st.st_mtime_ns, st.st_size, kind):
                continue
            _drop(con, p)
            try:
                parts = chunk_file(Path(p), kind)
            except OSError:
                continue
            for title, body in parts:
                cur = con.execute("INSERT INTO chunks(path, title, body) VALUES (?,?,?)",
                                  (p, title, body))
                con.execute("INSERT INTO recall_fts(rowid, title, body) VALUES (?,?,?)",
                            (cur.lastrowid, title, body))
            con.execute("INSERT INTO files VALUES (?,?,?,?,?)",
                        (p, st.st_mtime_ns, st.st_size, kind, scope))
            changed += 1
        for p in set(known) - seen:
            _drop(con, p)
            removed += 1
        con.execute("INSERT OR REPLACE INTO meta VALUES ('last_refresh', ?)", (str(time.time()),))
        con.execute("INSERT OR REPLACE INTO meta VALUES ('chunker', ?)", (CHUNKER,))
        con.execute("COMMIT")
        n = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
    finally:
        con.close()
    return {"files": len(seen), "changed": changed, "removed": removed, "chunks": n}


# ------------------------------------------------------------------------ query

def prompt_terms(prompt: str) -> list:
    out = []
    for w in _WORD.findall(fold(prompt)):
        if len(w) >= 3 and not w.isdigit() and w not in STOP and w not in out:
            out.append(w)
    return out[:60]


def select_terms(con, terms: list) -> list:
    """Keep terms the index knows and that are not common; rarest first."""
    total = con.execute("SELECT count(*) FROM chunks").fetchone()[0] or 1
    df = {}
    for t in terms:
        row = con.execute("SELECT doc FROM recall_vocab WHERE term=?", (t,)).fetchone()
        if row and 0 < row[0] <= max(3, COMMON_DF * total):
            df[t] = row[0]
    return sorted(df, key=lambda t: df[t])[:MAX_TERMS]


def query(prompt: str, cwd: str = "", db=None, exclude=(), k: int = TOP_K) -> list:
    """Ranked hits [{id, path, kind, title, snippet, matched}] -- [] when nothing earns a place."""
    path = Path(db or db_path())
    if not path.is_file():
        return []
    con = _reader(path)
    try:
        terms = select_terms(con, prompt_terms(prompt))
        if len(terms) < 2:
            return []
        # Two shared words is how "weather in madrid today" matched a marketing memory, so a
        # hit needs three, or every term of a two-term prompt.
        need = min(len(terms), max(MIN_MATCHED, math.ceil(0.3 * len(terms))))
        match = " OR ".join('"%s"' % t for t in terms)
        # Two row windows: one jsonl file holds 2,000 seo-geo chunks, so a single window could
        # fill with rows that collapse to one capped hit and push every validated rule out of
        # reach before Python ever scores it (review 2026-10-09, MEDIUM).
        unval = sorted(UNVALIDATED)
        marks = ",".join("?" * len(unval))
        sql = ("SELECT c.id, c.path, c.title, c.body, f.kind, f.scope, bm25(recall_fts, 4.0, 1.0) "
               "FROM recall_fts JOIN chunks c ON c.id = recall_fts.rowid "
               "JOIN files f ON f.path = c.path WHERE recall_fts MATCH ? AND f.kind %s IN (%s) "
               "ORDER BY bm25(recall_fts, 4.0, 1.0) LIMIT %d")
        rows = con.execute(sql % ("NOT", marks, 80), (match, *unval)).fetchall()
        rows += con.execute(sql % ("", marks, 20), (match, *unval)).fetchall()
    finally:
        con.close()
    here = project_scope(cwd)
    scored = []
    for cid, p, title, body, kind, scope, rank in rows:
        if cid in exclude:
            continue
        hay = set(_WORD.findall(fold(title + " " + body)))
        matched = [t for t in terms if t in hay]
        if len(matched) < need:
            continue
        boost = 1.5 if (kind == "memory" and scope == here) else 1.0
        scored.append((-rank * boost * (len(matched) / len(terms)) ** 0.5,
                       cid, p, title, body, kind, matched))
    scored.sort(key=lambda s: s[0], reverse=True)
    hits, files, unvalidated = [], set(), 0
    for _, cid, p, title, body, kind, matched in scored:
        if p in files:
            continue
        if kind in UNVALIDATED:
            if unvalidated >= MAX_UNVALIDATED:          # never crowd out validated knowledge
                continue
            unvalidated += 1
        files.add(p)
        hits.append({"id": cid, "path": p, "kind": kind, "title": title,
                     "snippet": " ".join(body.split())[:SNIPPET], "matched": matched})
        if len(hits) >= k:
            break
    return hits


# ----------------------------------------------------------------- hook support

def _age_s(db) -> float:
    if not Path(db).is_file():                          # connect() would create an empty file
        return float("inf")
    try:
        con = _reader(db)
        try:
            row = con.execute("SELECT v FROM meta WHERE k='last_refresh'").fetchone()
        finally:
            con.close()
        return time.time() - float(row[0]) if row else float("inf")
    except Exception:                                   # noqa: BLE001
        return float("inf")


def spawn_refresh_if_stale(db) -> bool:
    """At most one detached refresh across every pane, and at most one per STALE_S even when
    every refresh fails -- a failing refresh never advances last_refresh, so without the
    attempt stamp each prompt would relaunch a full scan (review L1). True when launched."""
    if os.environ.get("CPP_RECALL_NO_SPAWN") or _age_s(db) < STALE_S:
        return False
    lock = state_dir() / "refresh.lock"
    attempt = state_dir() / "last_attempt"
    try:
        if attempt.exists() and time.time() - attempt.stat().st_mtime < STALE_S:
            return False
        if lock.exists() and time.time() - lock.stat().st_mtime < LOCK_STALE_S:
            return False
        lock.unlink(missing_ok=True)
        os.close(os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        attempt.write_text(str(time.time()))
    except OSError:
        return False
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    flags = 0
    if os.name == "nt":
        flags = 0x00000200 | 0x08000000                 # NEW_PROCESS_GROUP | NO_WINDOW
    try:
        subprocess.Popen([str(pyw if pyw.is_file() else exe), "-m", "modules.gsd_x.recall",
                          "--refresh", "--release-lock"],
                         cwd=str(PP_ROOT), stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         close_fds=True, creationflags=flags)
        return True
    except OSError:
        lock.unlink(missing_ok=True)
        return False


def _shown_file(sid: str) -> Path:
    safe = "".join(c if c.isalnum() or c == "-" else "_" for c in sid)
    d = state_dir() / "shown"
    d.mkdir(parents=True, exist_ok=True)
    return d / ("%s.txt" % safe)


def _short(p: str) -> str:
    h = str(HOME)
    return "~" + p[len(h):].replace("\\", "/") if p.startswith(h) else p


def recall_block(prompt: str, payload: dict) -> str:
    """The text the model sees, or "" -- never raises."""
    try:
        if os.environ.get(SWITCH, "").strip().lower() in ("off", "0", "false"):
            return ""
        db = db_path()
        spawn_refresh_if_stale(db)
        sid = str(payload.get("session_id") or payload.get("sessionId") or "")
        shown = set()
        sf = _shown_file(sid) if sid else None
        if sf and sf.exists():
            shown = {int(x) for x in sf.read_text().split() if x.isdigit()}
        hits = query(prompt, str(payload.get("cwd") or ""), db, exclude=shown)
        if not hits:
            return ""
        if sf:
            with sf.open("a") as fh:
                fh.write(" ".join(str(h["id"]) for h in hits) + "\n")
        lines = ["Recall -- entries from memories, UKDL, HARD-RULES, CLAE, plans and labelled "
                 "corpora that share rare terms with this prompt (BM25, not judged for truth). "
                 "Open the path for the full entry and verify it before relying on it:"]
        for h in hits:
            tag = h["kind"] if h["kind"] not in UNVALIDATED else \
                "%s | %s" % (h["kind"], UNVALIDATED[h["kind"]])
            lines.append("- [%s] %s -- %s (%s)" % (tag, h["title"], h["snippet"],
                                                   _short(h["path"])))
        return "\n".join(lines)
    except Exception:                                   # noqa: BLE001
        return ""


def prune_shown(now=None) -> int:
    now = now or time.time()
    n = 0
    for f in (state_dir() / "shown").glob("*.txt"):
        try:
            if now - f.stat().st_mtime > SHOWN_KEEP_S:
                f.unlink()
                n += 1
        except OSError:
            pass
    return n


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--refresh" in argv:
        try:
            r = refresh()
            r["pruned_sessions"] = prune_shown()
            print(json.dumps(r))
        finally:
            if "--release-lock" in argv:
                (state_dir() / "refresh.lock").unlink(missing_ok=True)
        return 0
    if "--query" in argv:
        text = argv[argv.index("--query") + 1]
        t0 = time.perf_counter()
        hits = query(text, os.getcwd())
        ms = (time.perf_counter() - t0) * 1000
        for h in hits:
            print("[%s] %s  %s\n    %s\n    matched=%s" % (h["kind"], h["title"], _short(h["path"]),
                                                      h["snippet"], ",".join(h["matched"])))
        print("hits=%d query_ms=%.1f" % (len(hits), ms))
        return 0
    if "--stats" in argv:
        con = sqlite3.connect(str(db_path()))
        try:
            for kind, n in con.execute("SELECT f.kind, count(*) FROM chunks c JOIN files f "
                                       "ON f.path=c.path GROUP BY f.kind"):
                print("%-10s %d chunks" % (kind, n))
        finally:
            con.close()
        print("age_s=%.0f" % _age_s(db_path()))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
