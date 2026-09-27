#!/usr/bin/env python3
"""Move the `## Source` incident narrative of each ~/.claude/rules file into the
knowledge vault, leaving the rule text byte-identical and a one-line pointer.

Why: ~/.claude/rules loads into every call of every project (no file carries
`paths:`). The Source sections are evidence of where a rule came from, not the
rule; the model does not need them resident to follow it. Rule TEXT is never
moved: a pointer is not loaded, so a rule moved behind one stops governing
(Owner decision D1-A, vault/plans/context-rent-2026-09-27.md).

Only the Source section itself moves -- from its heading to the next `## `
heading or EOF. Several rules carry more doctrine AFTER Source
(guard-event-reachability has four sections), and those stay.

Dry-run by default. --apply: backup every file first, write the evidence file,
read it back, rewrite the rule, then re-verify that everything outside the
Source section is byte-identical to the backup. Any mismatch restores the
backup and exits non-zero.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

RULES = Path.home() / ".claude" / "rules"
VAULT = Path.home() / ".claude" / "knowledge_vault" / "rules-evidence"
BACKUPS = Path.home() / ".claude" / "backups"
_HEAD = re.compile(r"^## Source\b.*$", re.M)
_NEXT = re.compile(r"^## ", re.M)
POINTER = ("## Source\n\nIncident evidence moved to `~/.claude/knowledge_vault/rules-evidence/{name}` "
           "(2026-09-28) so it is not re-read on every call. The rule text above is unchanged.\n")


def split(text: str):
    """(before, source, after) or None. source runs from the heading to the next ## or EOF."""
    m = _HEAD.search(text)
    if not m:
        return None
    nxt = _NEXT.search(text, m.end())
    end = nxt.start() if nxt else len(text)
    return text[:m.start()], text[m.start():end], text[end:]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--rules", type=Path, default=RULES)
    ap.add_argument("--vault", type=Path, default=VAULT)
    ap.add_argument("--backups", type=Path, default=BACKUPS)
    a = ap.parse_args(argv)

    files = sorted(p for p in a.rules.glob("*.md") if p.is_file())
    if not files:
        print(f"REFUSED: no rules under {a.rules}")
        return 2
    plan, tot, moved = [], 0, 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        tot += len(text)
        parts = split(text)
        if not parts:
            print(f"  skip  {p.name}: no ## Source section")
            continue
        before, source, after = parts
        if source.startswith("## Source\n\nIncident evidence moved"):
            print(f"  done  {p.name}: already a pointer")
            continue
        moved += len(source)
        plan.append((p, text, before, source, after))
        print(f"  move  {p.name}: source {len(source):>6,} chars; kept after-source {len(after):>6,}")
    print(f"TOTAL rules {tot:,} chars; would move {moved:,} ({moved / max(tot, 1):.0%}) from {len(plan)} files")
    if not a.apply:
        print("dry run: nothing written (use --apply)")
        return 0

    bdir = a.backups / f"rules-{datetime.now():%Y%m%d-%H%M%S}"
    bdir.mkdir(parents=True, exist_ok=False)
    for p in files:
        shutil.copy2(p, bdir / p.name)
    a.vault.mkdir(parents=True, exist_ok=True)
    for p, text, before, source, after in plan:
        ev = a.vault / p.name
        body = (f"# Evidence: {p.stem}\n\nRule: `~/.claude/rules/{p.name}`. Moved verbatim from the rule's "
                f"`## Source` section on 2026-09-28 (backup `{bdir}`).\n\n{source}")
        ev.write_text(body, encoding="utf-8")
        if source not in ev.read_text(encoding="utf-8"):
            print(f"ABORT {p.name}: evidence read-back mismatch; rule untouched")
            return 1
        new = before + POINTER.format(name=p.name) + ("\n" + after if after else "")
        p.write_text(new, encoding="utf-8")
        again = split(p.read_text(encoding="utf-8"))
        ok = again and sha(again[0]) == sha(before) and again[2].lstrip("\n") == after.lstrip("\n")
        if not ok:
            shutil.copy2(bdir / p.name, p)
            print(f"ABORT {p.name}: rule text changed outside Source; restored from backup")
            return 1
    after_tot = sum(len(p.read_text(encoding="utf-8")) for p in files)
    print(f"APPLIED: rules {tot:,} -> {after_tot:,} chars; evidence in {a.vault}; backup {bdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
