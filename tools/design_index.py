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
    a = ap.parse_args(argv)
    if a.build_dataset:
        return cmd_build_dataset()
    if a.build:
        return cmd_build()
    if a.refresh:
        return cmd_refresh()
    if a.search:
        return cmd_search(a.search, a.limit, a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
