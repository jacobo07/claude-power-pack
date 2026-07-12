#!/usr/bin/env python3
"""Reference Integrity Linter CLI (P4).

  python tools/refcheck.py                      # governance/ + vault/ + CLAUDE.md
  python tools/refcheck.py --root <path> ...    # any doc tree
  python tools/refcheck.py --no-secrets         # references only
  python tools/refcheck.py --out report.md      # write the report

Exit 0 = clean. Exit 1 = broken references or credentials found.
A root that does not exist is a loud failure, never a clean report.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.refcheck import lint, render  # noqa: E402

DEFAULT_ROOTS = ["governance", "vault", "CLAUDE.md"]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Resolve every path a doc names against the "
                    "filesystem. Flag broken refs, stale-user paths, "
                    "and credential-shaped files.")
    p.add_argument("--root", action="append", default=None, metavar="PATH")
    p.add_argument("--no-secrets", action="store_true")
    p.add_argument("--out", metavar="FILE")
    a = p.parse_args(argv)

    raw = a.root if a.root else DEFAULT_ROOTS
    roots = [Path(r) if Path(r).is_absolute() else PP_ROOT / r for r in raw]

    try:
        rep = lint(roots, scan_secrets=not a.no_secrets)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    text = render(rep)
    print(text)

    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, out)
        print(f"report written: {out}")

    return 0 if rep.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
