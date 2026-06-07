#!/usr/bin/env python3
"""absorb_ecc_rules.py -- mirror ECC's rules taxonomy into the power-pack.

ECC absorption gap pass (2026-06-06). The 2026-05-27 absorption took ECC's 12
universal PRINCIPLES (-> modules/uqf) + the rules taxonomy for python/elixir.
ECC's rules/ has since grown to 19 languages; P10 (Rules Taxonomy) explicitly
said "future cycles add typescript, rust, go, etc." -- this completes it.

Method (matches the existing PP rule headers, e.g. rules/common/code-review.md
"Mirrored from ... ECC MIT"): rules are reference DOCTRINE (markdown), so they
are MIRRORED with MIT attribution -- not rewritten. The YAML frontmatter
(`paths:` globs that scope each rule) is preserved at the top so path-matching
still works; the attribution is inserted right after it.

SKIP-IF-EXISTS is the idempotency + safety contract: a PP rule file that already
exists (e.g. PP's customized common/python files) is NEVER overwritten. So a
re-run is a no-op, and PP-specific edits survive. elixir (PP-only) is untouched.

  python tools/absorb_ecc_rules.py --ecc <ECC/rules> [--apply]
  (default dry-run; --apply writes)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
PP_RULES = PP_ROOT / "rules"

# Fixed provenance (deterministic: re-running yields byte-identical files).
ATTRIB = (
    "<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License "
    "(c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules "
    "taxonomy during the ECC absorption gap pass (2026-06-06). Adapt in place "
    "as PP doctrine evolves. -->"
)


def _split_frontmatter(text: str) -> tuple[str, str]:
    """(frontmatter_block_incl_fences, body). Empty frontmatter if none."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            if nl != -1:
                return text[: nl + 1], text[nl + 1:]
    return "", text


def _mirror(ecc_file: Path) -> str:
    raw = ecc_file.read_text(encoding="utf-8")
    front, body = _split_frontmatter(raw)
    if front:
        return f"{front}{ATTRIB}\n\n{body.lstrip(chr(10))}"
    return f"{ATTRIB}\n\n{raw}"


def absorb(ecc_rules: Path, apply: bool) -> dict:
    added: list[str] = []
    skipped: list[str] = []
    new_langs: list[str] = []

    for lang_dir in sorted(p for p in ecc_rules.iterdir() if p.is_dir()):
        lang = lang_dir.name
        pp_lang = PP_RULES / lang
        if not pp_lang.exists():
            new_langs.append(lang)
        for ecc_file in sorted(lang_dir.glob("*.md")):
            target = pp_lang / ecc_file.name
            rel = f"{lang}/{ecc_file.name}"
            if target.exists():
                skipped.append(rel)            # never clobber PP's own files
                continue
            added.append(rel)
            if apply:
                pp_lang.mkdir(parents=True, exist_ok=True)
                target.write_text(_mirror(ecc_file), encoding="utf-8")

    return {"added": added, "skipped": skipped, "new_langs": new_langs}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--ecc", required=True, help="path to ECC rules/ dir")
    ap.add_argument("--apply", action="store_true", help="write (default dry-run)")
    args = ap.parse_args(argv)

    ecc_rules = Path(args.ecc)
    if not ecc_rules.is_dir():
        print(f"[ERROR] not a dir: {ecc_rules}")
        return 1

    r = absorb(ecc_rules, apply=args.apply)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] ECC rules absorption")
    print(f"  new languages ({len(r['new_langs'])}): {', '.join(r['new_langs'])}")
    print(f"  files added   : {len(r['added'])}")
    print(f"  files skipped (already in PP, preserved): {len(r['skipped'])}")
    if r["skipped"]:
        print(f"    preserved: {', '.join(r['skipped'])}")
    for f in r["added"]:
        print(f"    + {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
