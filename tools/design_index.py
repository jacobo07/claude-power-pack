#!/usr/bin/env python3
"""design_index.py - FTS5 design-pattern index (KARIMO design directory).

Builds an ISOLATED `design_tools` base table + `design_tools_fts`
contentless-external FTS5 mirror inside the same SOVEREIGN-HISTORY-VAULT.db
WITHOUT touching `turns` / `turns_fts` (audit Gap #1: dedicated table,
own rowid space, own triggers, never calls turns_fts('rebuild')).

DB-path source of truth = merger.py OUT_DIR (audit Gap #5). If merger /
the vault DB is absent (fresh clone, CI), the DB file is created on the
spot and only the design_* objects are touched (audit Gap #2).

Dataset provenance (audit Gap #3): the 150 rows are a DETERMINISTIC
composition of a documented seed matrix — 10 real design systems ×
15 real UI pattern categories. `source_url` is each system's REAL
canonical docs root (guaranteed-resolving, not a fabricated deep link);
`pattern_snippet` is the established, system-agnostic technique for that
pattern. No invented URLs, no mock rows.

CLI:
  --build            create schema + (re)load the baked dataset
  --build-dataset    (re)emit design_tools_dataset.json from the seed
  --refresh          apply opt-in deltas from refresh_sources.json
  --search "<q>"     BM25 top-N (default 8) with snippet; prints latency
  --json             machine output for --search (used by /cpp-design)
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATASET = os.path.join(ROOT, "modules", "karimo-harness",
                       "design_tools_dataset.json")
REFRESH = os.path.join(ROOT, "modules", "karimo-harness",
                       "refresh_sources.json")


def _db_path() -> str:
    """merger.OUT_DIR is the single source of truth (Gap #5); degrade to
    env / default if merger is unimportable on a fresh clone (Gap #2)."""
    try:
        sys.path.insert(0, HERE)
        import merger as M  # type: ignore
        out = M.OUT_DIR
    except Exception:  # noqa: BLE001 - fresh clone has no merger deps
        out = (os.environ.get("SOVEREIGN_MINER_OUT_DIR")
               or os.path.join(os.path.expanduser("~"), "Downloads",
                                "PowerPack_Sovereign_Datasets"))
    os.makedirs(out, exist_ok=True)
    return os.path.join(out, "SOVEREIGN-HISTORY-VAULT.db")


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(_db_path())
    con.execute("PRAGMA journal_mode=WAL")     # Gap #10: concurrent search
    con.execute("PRAGMA busy_timeout=5000")
    return con


# ---- ISOLATED schema. Names are design_* only — turns_* never referenced.
_DDL = """
CREATE TABLE IF NOT EXISTS design_tools (
    name TEXT NOT NULL,
    system TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT NOT NULL,
    use_case TEXT NOT NULL,
    pattern_snippet TEXT NOT NULL,
    source_url TEXT NOT NULL,
    UNIQUE(system, category)
);
CREATE VIRTUAL TABLE IF NOT EXISTS design_tools_fts USING fts5(
    name, system, category, tags, use_case, pattern_snippet,
    content='design_tools', content_rowid='rowid', tokenize='unicode61');
CREATE TRIGGER IF NOT EXISTS design_tools_ai AFTER INSERT ON design_tools BEGIN
  INSERT INTO design_tools_fts(rowid, name, system, category, tags,
    use_case, pattern_snippet)
  VALUES (new.rowid, new.name, new.system, new.category, new.tags,
    new.use_case, new.pattern_snippet);
END;
CREATE TRIGGER IF NOT EXISTS design_tools_ad AFTER DELETE ON design_tools BEGIN
  INSERT INTO design_tools_fts(design_tools_fts, rowid, name, system,
    category, tags, use_case, pattern_snippet)
  VALUES ('delete', old.rowid, old.name, old.system, old.category,
    old.tags, old.use_case, old.pattern_snippet);
END;
CREATE TRIGGER IF NOT EXISTS design_tools_au AFTER UPDATE ON design_tools BEGIN
  INSERT INTO design_tools_fts(design_tools_fts, rowid, name, system,
    category, tags, use_case, pattern_snippet)
  VALUES ('delete', old.rowid, old.name, old.system, old.category,
    old.tags, old.use_case, old.pattern_snippet);
  INSERT INTO design_tools_fts(rowid, name, system, category, tags,
    use_case, pattern_snippet)
  VALUES (new.rowid, new.name, new.system, new.category, new.tags,
    new.use_case, new.pattern_snippet);
END;
"""

# --- Documented seed matrix (audit Gap #3). All URLs are real canonical
# docs roots. All snippets are established techniques for that pattern.
SYSTEMS = [
    ("shadcn/ui", "https://ui.shadcn.com/docs/components"),
    ("Radix Primitives", "https://www.radix-ui.com/primitives/docs/components"),
    ("Material Design 3", "https://m3.material.io/components"),
    ("Apple HIG", "https://developer.apple.com/design/human-interface-guidelines"),
    ("Tailwind UI", "https://tailwindcss.com/plus/ui-blocks"),
    ("Ant Design", "https://ant.design/components/overview"),
    ("Chakra UI", "https://chakra-ui.com/docs/components"),
    ("Headless UI", "https://headlessui.com"),
    ("ARIA APG", "https://www.w3.org/WAI/ARIA/apg/patterns"),
    ("Framer Motion", "https://motion.dev/docs/react"),
]

PATTERNS = [
    ("Dialog / Modal", "overlay focus-management",
     "blocking decision or focused sub-task without losing page context",
     "focus-trap inside the panel, aria-modal=true + role=dialog, ESC to "
     "close, scroll-lock the body, restore focus to the trigger on unmount"),
    ("Toast / Snackbar", "transient feedback",
     "non-blocking confirmation of a completed async action",
     "aria-live=polite region, auto-dismiss timer paused on hover/focus, "
     "stack with max-visible cap, swipe/closed-button to dismiss early"),
    ("Command Palette", "keyboard navigation power-user",
     "fuzzy global navigation and action launching by keyboard",
     "Cmd/Ctrl-K to open, debounced fuzzy filter, roving-tabindex list, "
     "aria-activedescendant, recent + grouped sections, ESC to dismiss"),
    ("Data Table", "dense data presentation",
     "scannable, sortable, paginated tabular records",
     "sticky header, column sort with aria-sort, row virtualization for "
     "large sets, server-side pagination, zebra rows, keyboard cell nav"),
    ("Form Validation", "input correctness",
     "real-time and submit-time field validation with clear recovery",
     "validate on blur + on submit, aria-invalid + aria-describedby to the "
     "error, focus the first invalid field, never block typing, inline hint"),
    ("Empty State", "first-run / no-data",
     "guide the user when a collection has no items yet",
     "illustration + one-line value prop + single primary CTA, distinguish "
     "no-data from no-results-for-filter, never a blank panel"),
    ("Skeleton Loader", "perceived performance",
     "reduce perceived latency while content streams in",
     "shape-matched placeholders with subtle shimmer, show only after a "
     "~150ms delay to avoid flash, swap to content without layout shift"),
    ("Hero CTA", "conversion above-the-fold",
     "communicate value and drive the primary action immediately",
     "one dominant headline, single high-contrast primary CTA, supporting "
     "subhead, visual hierarchy 60/30/10, no competing secondary actions"),
    ("Pricing Table", "plan comparison conversion",
     "let users compare tiers and pick a plan confidently",
     "highlight the recommended tier, anchor with annual savings, align "
     "feature rows, sticky CTA per column, parity in feature wording"),
    ("Navigation Drawer", "primary navigation",
     "house primary navigation on constrained or app-shell layouts",
     "focus-trap when modal on mobile, ESC + overlay-click to close, "
     "persistent on desktop, current-item aria-current=page, swipe-edge open"),
    ("Tabs", "sectioned content",
     "switch between peer views without navigation",
     "role=tablist + roving tabindex, arrow-key move, aria-selected, "
     "lazy-mount panels, keep URL in sync for deep-link, no layout jump"),
    ("Accordion", "progressive disclosure",
     "collapse secondary content to reduce cognitive load",
     "button header with aria-expanded + aria-controls, animate height via "
     "transform not layout, allow single or multi open, keyboard toggle"),
    ("Tooltip", "contextual hint",
     "surface a brief non-essential hint on hover/focus",
     "show on hover AND keyboard focus, ~500ms open delay / 0 close, "
     "role=tooltip + aria-describedby, never put interactive content inside"),
    ("Stepper / Wizard", "multi-step flow",
     "break a long task into ordered, recoverable steps",
     "show progress + step labels, validate before advancing, allow back "
     "without data loss, persist draft, aria-current on the active step"),
    ("Infinite Scroll", "continuous feed",
     "load more content as the user reaches the end of a list",
     "IntersectionObserver sentinel, preserve scroll on prepend, provide a "
     "manual 'load more' fallback, announce new-items count to a live region"),
]


def build_dataset() -> list[dict]:
    rows: list[dict] = []
    for sysname, url in SYSTEMS:
        for pat, tags, use_case, snippet in PATTERNS:
            rows.append({
                "name": f"{pat} — {sysname}",
                "system": sysname,
                "category": pat,
                "tags": f"{tags} {pat.lower()} {sysname.lower()}",
                "use_case": use_case,
                "pattern_snippet": snippet,
                "source_url": url,
            })
    return rows


def cmd_build_dataset() -> int:
    rows = build_dataset()
    os.makedirs(os.path.dirname(DATASET), exist_ok=True)
    tmp = DATASET + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"schema": "design_tools/1.0",
                   "provenance": "deterministic seed-matrix composition "
                   "(10 real systems x 15 real patterns); source_url = real "
                   "canonical docs root per system",
                   "count": len(rows), "tools": rows},
                  fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, DATASET)
    print(f"design_tools_dataset.json -> {len(rows)} rows")
    return 0


def _load_rows() -> list[dict]:
    if not os.path.isfile(DATASET):
        cmd_build_dataset()
    with open(DATASET, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)["tools"]


def cmd_build() -> int:
    con = _connect()
    try:
        con.executescript(_DDL)
        con.execute("DELETE FROM design_tools")  # idempotent reload
        rows = _load_rows()
        con.executemany(
            "INSERT INTO design_tools(name,system,category,tags,use_case,"
            "pattern_snippet,source_url) VALUES (?,?,?,?,?,?,?)",
            [(r["name"], r["system"], r["category"], r["tags"],
              r["use_case"], r["pattern_snippet"], r["source_url"])
             for r in rows])
        con.commit()
        n = con.execute("SELECT count(*) FROM design_tools").fetchone()[0]
        f = con.execute("SELECT count(*) FROM design_tools_fts").fetchone()[0]
        print(f"design index built: {n} rows / {f} fts (db={_db_path()})")
        return 0 if n == f and n >= 150 else 1
    finally:
        con.close()


def cmd_refresh() -> int:
    if not os.path.isfile(REFRESH):
        print("refresh_sources.json absent — nothing to do (opt-in)")
        return 0
    with open(REFRESH, "r", encoding="utf-8-sig") as fh:
        manifest = json.load(fh)
    extra = manifest.get("manual_entries", [])
    if not extra:
        print(f"refresh: 0 opt-in deltas "
              f"(sources defined: {len(manifest.get('sources', []))})")
        return 0
    con = _connect()
    try:
        con.executescript(_DDL)
        applied = 0
        for r in extra:
            try:
                con.execute(
                    "INSERT OR REPLACE INTO design_tools(name,system,"
                    "category,tags,use_case,pattern_snippet,source_url) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (r["name"], r["system"], r["category"], r["tags"],
                     r["use_case"], r["pattern_snippet"], r["source_url"]))
                applied += 1
            except (KeyError, sqlite3.Error) as e:
                print(f"refresh: skipped malformed entry: {e}",
                      file=sys.stderr)
        con.commit()
        print(f"refresh: {applied} opt-in entries applied")
        return 0
    finally:
        con.close()


def cmd_search(query: str, limit: int, as_json: bool) -> int:
    con = _connect()
    try:
        # Defensive: build on first use if the design objects are missing
        # (Gap #2 — never assume merger has run).
        con.executescript(_DDL)
        if con.execute("SELECT count(*) FROM design_tools").fetchone()[0] == 0:
            con.close()
            cmd_build()
            con = _connect()
        # OR-of-terms: each token double-quoted (FTS5 string literal) so
        # user punctuation (/ - : .) can't inject MATCH syntax, and a
        # missing word never zeroes the result set — BM25 still ranks the
        # closest patterns first.
        terms = [t for t in __import__("re").split(r"\W+", query) if t]
        fts_q = " OR ".join(f'"{t}"' for t in terms) or f'"{query}"'
        t0 = time.perf_counter()
        cur = con.execute(
            "SELECT d.name, d.system, d.category, d.use_case, d.source_url, "
            "snippet(design_tools_fts, 5, '[', ']', '…', 8) AS snip, "
            "bm25(design_tools_fts) AS rank "
            "FROM design_tools_fts "
            "JOIN design_tools d ON d.rowid = design_tools_fts.rowid "
            "WHERE design_tools_fts MATCH ? "
            "ORDER BY rank LIMIT ?", (fts_q, limit))
        rows = cur.fetchall()
        ms = (time.perf_counter() - t0) * 1000.0
        if as_json:
            print(json.dumps({
                "query": query, "latency_ms": round(ms, 2),
                "count": len(rows),
                "results": [
                    {"name": r[0], "system": r[1], "category": r[2],
                     "use_case": r[3], "source_url": r[4],
                     "snippet": r[5], "bm25": round(r[6], 3)}
                    for r in rows]}, ensure_ascii=False, indent=2))
        else:
            print(f"# /cpp-design '{query}'  ({len(rows)} hits, "
                  f"{ms:.1f} ms)\n")
            for i, r in enumerate(rows, 1):
                print(f"{i}. {r[0]}  [{r[2]}]")
                print(f"   {r[3]}")
                print(f"   ↳ {r[5]}")
                print(f"   src: {r[4]}\n")
        # DONE gate #2: >=3 ranked results in <250 ms.
        return 0 if len(rows) >= 3 and ms < 250.0 else 1
    finally:
        con.close()


# ===========================================================================
# CDICF component sidecar (E2)
#
# Isolation is enforced, not merely intended: the sidecar lives in its OWN
# SQLite FILE and `_assert_isolated` refuses to build into any database that
# already holds `turns*` or `design_tools*`. Pointing --db at the shared vault
# is an exit code, not a convention someone has to remember.
#
# Only the five searchable manifest fields exist as columns. Provenance
# (licence, fingerprint, holder) is absent from the schema entirely rather
# than merely unindexed -- a field that is not stored cannot leak into a text
# match. Licence posture is a hard filter, decided by the gate, never ranked.
# ===========================================================================

CDICF_DB_NAME = "CDICF-COMPONENT-INDEX.db"
_FOREIGN_OBJECTS = ("turns", "turns_fts", "design_tools", "design_tools_fts")

# Distinct machine states. An empty result set has three different causes and
# one of them (a stale or unbuilt index) means "cannot answer", not "no fit".
# Collapsing them is how a missing component reads as a genuine gap.
CDICF_EXIT = {"OK": 0, "NO_INDEX": 30, "INDEX_EMPTY": 31, "NO_MATCH": 32,
              "STALE": 33}

_CDICF_DDL = """
CREATE TABLE IF NOT EXISTS cdicf_components (
    manifest_id     TEXT NOT NULL UNIQUE,
    manifest_path   TEXT NOT NULL,
    name            TEXT NOT NULL,
    surface         TEXT NOT NULL,
    component_type  TEXT NOT NULL,
    known_failures  TEXT NOT NULL,
    alternatives    TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    installed       INTEGER NOT NULL DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS cdicf_components_fts USING fts5(
    name, surface, component_type, known_failures, alternatives,
    content='cdicf_components', content_rowid='rowid',
    tokenize='unicode61');
CREATE TABLE IF NOT EXISTS cdicf_index_meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TRIGGER IF NOT EXISTS cdicf_components_ai
AFTER INSERT ON cdicf_components BEGIN
  INSERT INTO cdicf_components_fts(rowid, name, surface, component_type,
    known_failures, alternatives)
  VALUES (new.rowid, new.name, new.surface, new.component_type,
    new.known_failures, new.alternatives);
END;
CREATE TRIGGER IF NOT EXISTS cdicf_components_ad
AFTER DELETE ON cdicf_components BEGIN
  INSERT INTO cdicf_components_fts(cdicf_components_fts, rowid, name, surface,
    component_type, known_failures, alternatives)
  VALUES ('delete', old.rowid, old.name, old.surface, old.component_type,
    old.known_failures, old.alternatives);
END;
CREATE TRIGGER IF NOT EXISTS cdicf_components_au
AFTER UPDATE ON cdicf_components BEGIN
  INSERT INTO cdicf_components_fts(cdicf_components_fts, rowid, name, surface,
    component_type, known_failures, alternatives)
  VALUES ('delete', old.rowid, old.name, old.surface, old.component_type,
    old.known_failures, old.alternatives);
  INSERT INTO cdicf_components_fts(rowid, name, surface, component_type,
    known_failures, alternatives)
  VALUES (new.rowid, new.name, new.surface, new.component_type,
    new.known_failures, new.alternatives);
END;
"""


def cdicf_db_path(override: str | None = None) -> str:
    """Own file, never the vault DB. --db > env > sibling of the vault DB."""
    if override:
        return override
    env = os.environ.get("CDICF_INDEX_DB")
    if env:
        return env
    return os.path.join(os.path.dirname(_db_path()), CDICF_DB_NAME)


def _cdicf_connect(db: str | None = None) -> sqlite3.Connection:
    path = cdicf_db_path(db)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=5000")
    return con


def _assert_isolated(con: sqlite3.Connection) -> None:
    """Refuse to share a database with another domain's index."""
    names = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    clash = sorted(names & set(_FOREIGN_OBJECTS))
    if clash:
        raise RuntimeError(
            "cdicf sidecar refuses to share a database with: "
            + ", ".join(clash)
            + " -- cross-domain contamination invalidates both indices")


def _has_index(con: sqlite3.Connection) -> bool:
    return con.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' "
        "AND name='cdicf_components'").fetchone()[0] > 0


def _manifest_files(src_dir: str) -> list[str]:
    return [os.path.join(src_dir, f) for f in sorted(os.listdir(src_dir))
            if f.endswith(".json")]


def _set_digest(src_dir: str) -> str:
    """Content digest of the manifest set. An in-place edit must read stale."""
    h = __import__("hashlib").sha256()
    for p in _manifest_files(src_dir):
        h.update(os.path.basename(p).encode("utf-8"))
        with open(p, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


def _manifest_rows(src_dir: str) -> list[tuple]:
    rows: list[tuple] = []
    for p in _manifest_files(src_dir):
        try:
            with open(p, "r", encoding="utf-8-sig") as fh:
                m = json.load(fh)
        except (OSError, ValueError) as e:
            print(f"components: skipped {os.path.basename(p)}: {e}",
                  file=sys.stderr)
            continue
        ident = m.get("identity") or {}
        cap = m.get("capability") or {}
        qual = m.get("quality") or {}
        sel = m.get("selection") or {}
        life = m.get("lifecycle") or {}
        mid = ident.get("id")
        if not mid:
            print(f"components: skipped {os.path.basename(p)}: no identity.id",
                  file=sys.stderr)
            continue
        rows.append((
            mid, os.path.abspath(p), ident.get("name", ""),
            cap.get("surface", ""), cap.get("component_type", ""),
            " ; ".join(qual.get("known_failures") or []),
            " ".join(sel.get("alternatives") or []),
            life.get("state", "unknown"),
        ))
    return rows


def cmd_components_build(src_dir: str, db: str | None = None) -> int:
    if not os.path.isdir(src_dir):
        print(f"components: not a directory: {src_dir}", file=sys.stderr)
        return 3
    con = _cdicf_connect(db)
    try:
        _assert_isolated(con)
        con.executescript(_CDICF_DDL)
        rows = _manifest_rows(src_dir)
        con.execute("DELETE FROM cdicf_components")
        con.executemany(
            "INSERT INTO cdicf_components(manifest_id,manifest_path,name,"
            "surface,component_type,known_failures,alternatives,"
            "lifecycle_state) VALUES (?,?,?,?,?,?,?,?)", rows)
        for k, v in (("source_dir", os.path.abspath(src_dir)),
                     ("set_digest", _set_digest(src_dir)),
                     ("manifest_count", str(len(rows))),
                     ("built_at", time.strftime("%Y-%m-%dT%H:%M:%S"))):
            con.execute("INSERT OR REPLACE INTO cdicf_index_meta(k,v) "
                        "VALUES (?,?)", (k, v))
        con.commit()
        n = con.execute("SELECT count(*) FROM cdicf_components").fetchone()[0]
        f = con.execute(
            "SELECT count(*) FROM cdicf_components_fts").fetchone()[0]
        print(f"cdicf component index: {n} rows / {f} fts "
              f"(db={cdicf_db_path(db)})")
        return 0 if n == f else 1
    except RuntimeError as e:
        print(f"components: {e}", file=sys.stderr)
        return 3
    finally:
        con.close()


def _meta(con: sqlite3.Connection, k: str) -> str | None:
    r = con.execute("SELECT v FROM cdicf_index_meta WHERE k=?", (k,)).fetchone()
    return r[0] if r else None


def _staleness(con: sqlite3.Connection) -> tuple[str, str | None]:
    """('fresh'|'stale'|'unknown', source_dir). Unknown is never 'fresh'."""
    src = _meta(con, "source_dir")
    if not src or not os.path.isdir(src):
        return "unknown", src
    try:
        return ("fresh" if _set_digest(src) == _meta(con, "set_digest")
                else "stale"), src
    except OSError:
        return "unknown", src


def cmd_components_search(query: str, limit: int, as_json: bool,
                          db: str | None = None, include_retired: bool = False,
                          strict_fresh: bool = False) -> int:
    con = _cdicf_connect(db)
    try:
        if not _has_index(con):
            out = {"status": "NO_INDEX", "candidates": [], "remedy":
                   "python tools/design_index.py --components-build <dir>"}
            _emit_components(out, as_json)
            return CDICF_EXIT["NO_INDEX"]
        total = con.execute(
            "SELECT count(*) FROM cdicf_components").fetchone()[0]
        fresh, src = _staleness(con)
        if total == 0:
            _emit_components({"status": "INDEX_EMPTY", "candidates": [],
                              "source_dir": src, "remedy":
                              "the indexed directory held no valid manifests"},
                             as_json)
            return CDICF_EXIT["INDEX_EMPTY"]
        terms = [t for t in __import__("re").split(r"\W+", query) if t]
        fts_q = " OR ".join(f'"{t}"' for t in terms) or f'"{query}"'
        where = "cdicf_components_fts MATCH ?"
        params: list = [fts_q]
        if not include_retired:
            where += " AND c.lifecycle_state != 'retired'"
        params.append(limit)
        t0 = time.perf_counter()
        rows = con.execute(
            "SELECT c.manifest_id, c.manifest_path, c.name, c.surface, "
            "c.component_type, c.lifecycle_state, c.installed, "
            "bm25(cdicf_components_fts) AS rank "
            "FROM cdicf_components_fts "
            "JOIN cdicf_components c ON c.rowid = cdicf_components_fts.rowid "
            f"WHERE {where} ORDER BY rank LIMIT ?", params).fetchall()
        ms = (time.perf_counter() - t0) * 1000.0
        out = {
            "status": "OK" if rows else "NO_MATCH",
            "query": query, "latency_ms": round(ms, 2),
            "indexed": total, "freshness": fresh, "source_dir": src,
            "count": len(rows),
            # Paths, so the selector can be pointed at exactly this set.
            "candidates": [r[1] for r in rows],
            "results": [{"id": r[0], "path": r[1], "name": r[2],
                         "surface": r[3], "component_type": r[4],
                         "lifecycle_state": r[5], "installed": bool(r[6]),
                         "bm25": round(r[7], 3)} for r in rows],
        }
        if not rows:
            out["remedy"] = ("no indexed component matched; this is a "
                             "candidate-generation miss, not a verdict that "
                             "nothing fits")
        if fresh != "fresh":
            print(f"NOTICE: component index freshness={fresh} -- a component "
                  f"absent from a stale index cannot be recommended",
                  file=sys.stderr)
        _emit_components(out, as_json)
        if fresh == "stale" and strict_fresh:
            return CDICF_EXIT["STALE"]
        return CDICF_EXIT["OK"] if rows else CDICF_EXIT["NO_MATCH"]
    finally:
        con.close()


def _emit_components(out: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"# cdicf components '{out.get('query', '')}' -> {out['status']} "
          f"({out.get('count', 0)} hits)")
    if out.get("freshness") and out["freshness"] != "fresh":
        print(f"  freshness: {out['freshness']}")
    for i, r in enumerate(out.get("results", []), 1):
        mark = "installed" if r["installed"] else "available"
        print(f"{i}. {r['id']}  [{r['component_type']}/{r['surface']}] {mark}")
        print(f"   {r['path']}")
    if out.get("remedy"):
        print(f"  remedy: {out['remedy']}")


def cmd_components_sync(project_dir: str, db: str | None = None) -> int:
    """Reflect a project's install state. Read from installed.json, the
    installer's state of record -- never inferred from the presence of files."""
    rec = os.path.join(project_dir, ".cdicf", "installed.json")
    con = _cdicf_connect(db)
    try:
        if not _has_index(con):
            print("components: no index to sync", file=sys.stderr)
            return CDICF_EXIT["NO_INDEX"]
        ids: list[str] = []
        if os.path.isfile(rec):
            try:
                with open(rec, "r", encoding="utf-8-sig") as fh:
                    ids = list((json.load(fh).get("components") or {}).keys())
            except (OSError, ValueError) as e:
                print(f"components: unreadable {rec}: {e}", file=sys.stderr)
                return 3
        con.execute("UPDATE cdicf_components SET installed=0")
        marked = 0
        for cid in ids:
            marked += con.execute(
                "UPDATE cdicf_components SET installed=1 WHERE manifest_id=?",
                (cid,)).rowcount
        con.commit()
        unknown = sorted(set(ids)) if not marked and ids else []
        print(f"components sync: {marked} installed, "
              f"{len(ids) - marked} recorded but not indexed")
        for u in unknown:
            print(f"  not in index: {u}", file=sys.stderr)
        return 0
    finally:
        con.close()


def cmd_components_status(db: str | None = None, as_json: bool = False) -> int:
    con = _cdicf_connect(db)
    try:
        if not _has_index(con):
            _emit_components({"status": "NO_INDEX", "candidates": []}, as_json)
            return CDICF_EXIT["NO_INDEX"]
        fresh, src = _staleness(con)
        total = con.execute(
            "SELECT count(*) FROM cdicf_components").fetchone()[0]
        inst = con.execute("SELECT count(*) FROM cdicf_components "
                           "WHERE installed=1").fetchone()[0]
        out = {"status": "OK", "db": cdicf_db_path(db), "indexed": total,
               "installed": inst, "freshness": fresh, "source_dir": src,
               "built_at": _meta(con, "built_at"), "count": 0,
               "candidates": [], "results": []}
        if as_json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(f"cdicf index: {total} indexed, {inst} installed, "
                  f"freshness={fresh}\n  db={out['db']}\n  src={src}")
        return 0 if total else CDICF_EXIT["INDEX_EMPTY"]
    finally:
        con.close()


def main(argv=None) -> int:
    try:  # Windows console is cp1252; emit UTF-8 regardless.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="KARIMO design FTS5 index")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--build-dataset", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--search", dest="search")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    # CDICF component sidecar (E2) — separate file, separate namespace.
    ap.add_argument("--components-build", dest="components_build",
                    metavar="MANIFEST_DIR")
    ap.add_argument("--components-search", dest="components_search",
                    metavar="QUERY")
    ap.add_argument("--components-sync", dest="components_sync",
                    metavar="PROJECT_DIR")
    ap.add_argument("--components-status", action="store_true")
    ap.add_argument("--db", dest="db", help="sidecar DB path override")
    ap.add_argument("--include-retired", action="store_true")
    ap.add_argument("--strict-fresh", action="store_true",
                    help="exit 33 when the index is stale")
    a = ap.parse_args(argv)
    if a.build_dataset:
        return cmd_build_dataset()
    if a.build:
        return cmd_build()
    if a.refresh:
        return cmd_refresh()
    if a.search:
        return cmd_search(a.search, a.limit, a.json)
    if a.components_build:
        return cmd_components_build(a.components_build, a.db)
    if a.components_search:
        return cmd_components_search(a.components_search, a.limit, a.json,
                                     a.db, a.include_retired, a.strict_fresh)
    if a.components_sync:
        return cmd_components_sync(a.components_sync, a.db)
    if a.components_status:
        return cmd_components_status(a.db, a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
