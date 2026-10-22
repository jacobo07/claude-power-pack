#!/usr/bin/env python
"""Code-map page for large files (CCR v5 E3; UCRE first rung, plan ccr-v2-addendum: a repeated Read of an
unchanged sha is served from a page store).

A 5,600-line file read in chunks costs a call per chunk and the context carries every chunk on every later
call (boundary ledger, 49c0ae70: gsd_mission.py read 24x). A map page is the file's symbol index with line
ranges: one small read says WHERE to read, so later reads are ranges, not pages.

  code_map.py map FILE                 print the map (Python only; any other suffix is refused, not guessed)
  code_map.py page FILE --store DIR    same, kept in DIR/<sha256>.map; a hit means the sha did not change

The page is keyed by the sha256 of the file's bytes, so an edited file can never be served a stale map.
Pure and read-only on FILE; writes only inside --store.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import sys
from pathlib import Path


class MapError(ValueError):
    pass


def _doc1(node) -> str:
    d = ast.get_docstring(node) or ""
    return d.strip().splitlines()[0][:100] if d.strip() else ""


def _entries(body, depth: int, out: list) -> None:
    for n in body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(n, ast.ClassDef) else ("async def" if isinstance(n, ast.AsyncFunctionDef) else "def")
            out.append((n.lineno, n.end_lineno or n.lineno, depth, f"{kind} {n.name}", _doc1(n)))
            if isinstance(n, ast.ClassDef):
                _entries(n.body, depth + 1, out)


def build_map(path: Path | str) -> str:
    p = Path(path)
    if p.suffix != ".py":
        raise MapError(f"{p.name}: only .py files are mapped; a map of anything else would be a guess")
    raw = p.read_bytes()
    try:
        tree = ast.parse(raw.decode("utf-8-sig"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise MapError(f"{p.name}: cannot parse ({type(exc).__name__}: {exc})") from exc
    entries: list = []
    _entries(tree.body, 0, entries)
    total = raw.count(b"\n") + (0 if raw.endswith(b"\n") or not raw else 1)
    lines = [f"# code map {p.name}  sha256 {hashlib.sha256(raw).hexdigest()[:16]}  {total} lines  {len(entries)} symbols",
             "# read a symbol by its line range; do not page the file"]
    for lo, hi, depth, name, doc in entries:
        lines.append(f"L{lo}-{hi} ({hi - lo + 1}) {'  ' * depth}{name}" + (f" - {doc}" if doc else ""))
    return "\n".join(lines) + "\n"


def page(path: Path | str, store: Path | str) -> dict:
    """{map, sha256, hit, bytes_file, bytes_map}. A hit = a page for exactly this sha was already stored."""
    raw = Path(path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    sp = Path(store) / f"{sha}.map"
    if sp.is_file():
        text = sp.read_text(encoding="utf-8")
        hit = True
    else:
        text = build_map(path)
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(text, encoding="utf-8")
        hit = False
    return {"map": text, "sha256": sha, "hit": hit, "bytes_file": len(raw), "bytes_map": len(text.encode("utf-8"))}


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="code_map")
    ap.add_argument("cmd", choices=["map", "page"])
    ap.add_argument("file")
    ap.add_argument("--store")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "map":
            sys.stdout.write(build_map(args.file))
            return 0
        if not args.store:
            ap.error("page needs --store")
        r = page(args.file, args.store)
    except (MapError, OSError) as exc:
        print(f"code_map: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(r["map"])
    print(f"# page {'HIT' if r['hit'] else 'MISS'} sha256 {r['sha256'][:16]} file {r['bytes_file']:,} B map {r['bytes_map']:,} B")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
