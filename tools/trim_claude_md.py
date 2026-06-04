#!/usr/bin/env python3
"""Conservative char-trimmer for the GLOBAL ~/.claude/CLAUDE.md.

Goal: clear Claude Code's ">40.0k chars will impact performance" warning by
removing ONLY non-operative provenance metadata. Every operative rule and the
PRIMARY vault pointer for each topic are preserved verbatim.

Mechanism: a small set of EXPLICIT, documented regex removals. Each removal
targets justification/provenance prose (incident dates, "sealed YYYY-MM-DD",
trailing "Full doctrine: `path`" deep-links, redundant blank runs) -- never a
TRIGGER/STOP/rule clause.

Usage:
  python trim_claude_md.py --dry-run   # print every removed span, write nothing
  python trim_claude_md.py --apply     # write back UTF-8 no-BOM, assert <40000

Reversible: a verified .bak is created by the caller before --apply.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

TARGET_MAX = 40000          # Claude Code hard warning threshold (chars)
# Recalibrated 2026-06-04 (BL-CLAUDEMD-ROUTER): the file is ~all operative
# always-on safety doctrine (Bash-Bridge, Parallel-Subagent caps, Anti-Waiting)
# that must NOT move to vault. Safe provenance-only trimming bottoms out at
# ~39,658 chars -- the operative floor. A 39,000 margin (old "1k buffer") is
# unreachable without cutting safety rules, so the margin is set one typical
# append (~250 chars) below the hard limit: WARN when an append would breach.
TARGET_MARGIN = 39750

CM = Path.home() / ".claude" / "CLAUDE.md"

# --- Conservative removal rules. Order matters. Each is (name, pattern, repl). ---
# R1: trailing deep-link cross-refs to MORE detail. The rule above them is
#     self-contained; this only removes the "see also <file>" pointer.
R1 = re.compile(
    r"\s*(?:Full doctrine|Full lesson|Full law|Cross-ref|Vaccine|Spec|"
    r"Architecture detail|Doctrine|UKDL cross-repo)\s*:\s*`[^`]+`\.?",
    re.IGNORECASE,
)
# R2: parenthetical provenance whose content is ONLY a seal/incident tag + date.
#     e.g. "(sealed 2026-06-01, transversal/cross-repo)". Keeps the sentence.
R2 = re.compile(
    r"\s*\((?:sealed|added|refined|caught|observed|post-[\w-]+|Owner-sealed|"
    r"Owner-requested|re-sealed)[^()]*?20\d\d-\d\d-\d\d[^()]*?\)",
    re.IGNORECASE,
)
# R3: collapse 3+ consecutive blank lines to a single blank line.
R3 = re.compile(r"\n{3,}")
# R4: a SELF-CONTAINED parenthetical that contains a YYYY-MM-DD date and is led
#     by a provenance token (caught/sealed/BL-/MC-/post-/a date). [^()] cannot
#     cross a paren boundary, so it can NEVER eat an operative clause that lives
#     outside the paren -- unlike an em-dash-to-EOL rule. The date lookahead
#     means only dated provenance parens are removed; "(BL-0063 / MC-SYS-118)"
#     (no date) is kept. Examples removed: "(caught 2026-05-04 LaptOps)",
#     "(BL-0036, 2026-05-03)", "(MC-LAZ-29/30, 2026-04-29)".
R4 = re.compile(
    r"\s*\((?=[^()]*\d{4}-\d\d-\d\d)"
    r"(?:caught|sealed|added|refined|observed|post-[\w-]+|"
    r"BL-[\w/]+|MC-[\w/]+|\d{4}-\d\d-\d\d)[^()]*?\)",
    re.IGNORECASE,
)

# R5: header-label paren provenance -- "(LABEL — <provenance incl date>)" where
#     LABEL is the operative tag (MANDATORY, Apex Standard, ...). Keeps "(LABEL)",
#     strips the "— ...date..." tail. Bounded by [^()] so it stays inside ONE
#     paren and cannot reach operative text outside it; requires a date so only
#     dated provenance is cut. "(MANDATORY — every project)" (no date) is kept.
# The kept label (group 1) excludes commas: a header label is short and comma-
#   free ("MANDATORY", "Apex Standard"), whereas an OPERATIVE paren that happens
#   to contain a dated clause is a comma-separated list (e.g. "(mix compile, mix
#   test, ... — sealed 2026-...)") -- excluding commas leaves those untouched.
R5 = re.compile(r"(\([^()—\n,]*?)\s*—\s*[^()\n]*?\d{4}-\d\d-\d\d[^()\n]*?(\))")

RULES = [("R1-deeplink", R1), ("R2-provenance", R2),
         ("R4-paren-date", R4), ("R5-header-label", (R5, r"\1\2"))]


def trim(text: str, verbose: bool = False) -> str:
    removed_total = 0
    for name, spec in RULES:
        # spec is a compiled pattern (delete) OR (pattern, replacement).
        pat, repl = spec if isinstance(spec, tuple) else (spec, "")
        matches = list(pat.finditer(text))
        if verbose and matches:
            cut = sum(len(m.group(0)) - len(m.expand(repl)) for m in matches)
            print(f"\n--- {name}: {len(matches)} removals ({cut} chars) ---")
            for m in matches:
                print(f"  [{m.start()}:{m.end()}] {m.group(0).strip()[:100]!r}")
        removed_total += sum(
            len(m.group(0)) - len(m.expand(repl)) for m in matches)
        text = pat.sub(repl, text)
    text = R3.sub("\n\n", text)
    if verbose:
        print(f"\nProvenance chars removed: {removed_total}")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--check", action="store_true",
                   help="firewall linter: report size, exit 1 if >= margin, "
                        "2 if >= hard 40k threshold")
    ap.add_argument("--path", default=str(CM))
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"NOT FOUND: {p}", file=sys.stderr)
        return 2

    if args.check:
        n = len(p.read_text(encoding="utf-8-sig"))
        if n >= TARGET_MAX:
            print(f"FIREWALL FAIL: {p.name} = {n} chars >= {TARGET_MAX} "
                  f"(Claude Code performance warning ACTIVE). Run --dry-run "
                  f"then --apply, or trim manually.")
            return 2
        if n >= TARGET_MARGIN:
            print(f"FIREWALL WARN: {p.name} = {n} chars >= margin "
                  f"{TARGET_MARGIN} (approaching {TARGET_MAX} hard limit). "
                  f"Trim provenance soon.")
            return 1
        print(f"FIREWALL OK: {p.name} = {n} chars "
              f"(margin {TARGET_MARGIN}, hard {TARGET_MAX}).")
        return 0

    original = p.read_text(encoding="utf-8-sig")
    trimmed = trim(original, verbose=args.dry_run)

    before, after = len(original), len(trimmed)
    print(f"\nbefore: {before} chars | after: {after} chars | cut: {before-after}")
    print(f"under {TARGET_MAX}: {after < TARGET_MAX} | under margin "
          f"{TARGET_MARGIN}: {after < TARGET_MARGIN}")

    if args.dry_run:
        print("\nDRY RUN -- nothing written. Review removals above.")
        return 0

    if after >= TARGET_MAX:
        print(f"REFUSING: result {after} still >= {TARGET_MAX}. "
              f"Trim more manually.", file=sys.stderr)
        return 1
    # Write UTF-8 NO BOM, preserve newline style as \n.
    p.write_text(trimmed, encoding="utf-8", newline="\n")
    print(f"APPLIED -> {p} ({after} chars, warning cleared)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
