#!/usr/bin/env python3
"""lookup_name.py -- Query the mapping produced by recover_kotlin_names.py.

Extracted from upstream ``scripts/lookup-name.sh``
(android-reverse-engineering-skill, Apache-2.0, (c) Simone Avogadro), whose
body was already Python embedded in a bash heredoc. See ../NOTICE.md.

One behavioural change, forced by the target platform: upstream's ``--grep``
mode shelled out to POSIX ``grep -rEn``, which does not exist on a stock
Windows host, so the search is done in-process instead. Same output shape,
same annotation suffix.

Modes:
    lookup_name.py <mapping-dir> <substring>          search by real-FQN substring
    lookup_name.py <mapping-dir> -o <obf>             resolve obf -> real
    lookup_name.py <mapping-dir> -p <pkg>             list a real package
    lookup_name.py <mapping-dir> --grep <regex> <sources-dir>
        search decompiled sources, annotating each hit with the real class name
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

SOURCE_SUFFIXES = (".java", ".kt")


def load(mapping_dir: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    path = os.path.join(mapping_dir, "mapping.json")
    if not os.path.isfile(path):
        print(f"no mapping.json in {mapping_dir}", file=sys.stderr)
        raise SystemExit(1)
    with open(path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    reverse: dict[str, list[str]] = {}
    for obf, real in mapping.items():
        reverse.setdefault(real, []).append(obf)
    return mapping, reverse


def _print_group(real: str, obfs: list[str]) -> None:
    print(real)
    for o in sorted(obfs):
        print(f"    {o}")


def search(reverse: dict[str, list[str]], query: str) -> int:
    q = query.lower()
    hits = 0
    for real in sorted(reverse):
        if q in real.lower():
            _print_group(real, reverse[real])
            hits += 1
    return hits


def by_obf(mapping: dict[str, str], reverse: dict[str, list[str]], obf: str) -> int:
    if obf not in mapping:
        print(f"no mapping for {obf}", file=sys.stderr)
        return 1
    real = mapping[obf]
    print(f"{obf}  ->  {real}")
    for sibling in sorted(s for s in reverse[real] if s != obf):
        print(f"    sibling: {sibling}")
    return 0


def by_pkg(reverse: dict[str, list[str]], pkg: str) -> int:
    p = pkg.lower()
    for real in sorted(reverse):
        if p in real.rsplit(".", 1)[0].lower():
            _print_group(real, reverse[real])
    return 0


def grep_annotated(mapping: dict[str, str], pattern: str, sources: str) -> int:
    """Search *sources* for *pattern*, annotating hits with the real class name.

    Upstream delegated to ``grep -rEn --include=*.java``; this walks the tree
    in-process so the mode works identically on Windows.
    """
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        print(f"bad regex {pattern!r}: {exc}", file=sys.stderr)
        return 2

    for dp, _dirs, files in os.walk(sources):
        for name in files:
            if not name.endswith(SOURCE_SUFFIXES):
                continue
            path = os.path.join(dp, name)
            rel = os.path.relpath(path, sources)
            obf = os.path.splitext(rel)[0].replace(os.sep, ".")
            suffix = f"  // {mapping[obf]}" if obf in mapping else ""
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    for lineno, line in enumerate(fh, 1):
                        if rx.search(line):
                            print(f"{rel}:{lineno}:{line.rstrip()}{suffix}")
            except OSError:
                continue
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Query a recovered Kotlin class-name mapping."
    )
    ap.add_argument("mapping_dir", help="directory produced by recover_kotlin_names.py")
    ap.add_argument("-o", "--obf", help="resolve an obfuscated FQN to its real name")
    ap.add_argument("-p", "--package", help="list a real package by substring")
    ap.add_argument(
        "--grep",
        nargs=2,
        metavar=("REGEX", "SOURCES_DIR"),
        help="search sources, annotating each hit with the owning real class",
    )
    ap.add_argument("query", nargs="*", help="real-FQN substring to search for")
    args = ap.parse_args(argv)

    mapping, reverse = load(args.mapping_dir)

    if args.grep:
        return grep_annotated(mapping, args.grep[0], args.grep[1])
    if args.obf:
        return by_obf(mapping, reverse, args.obf)
    if args.package:
        return by_pkg(reverse, args.package)
    if args.query:
        search(reverse, " ".join(args.query))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
