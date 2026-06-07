#!/usr/bin/env python3
"""verify_rules.py -- RULES_TAXONOMY probe (verify_spp row).

Confirms the absorbed ECC rules taxonomy is present and well-formed.
Exit 0 iff every sub-check passes.

  R1 rules/common/ has >=5 files (we expect 7)
  R2 rules/python/ has >=4 files (we expect 5)
  R3 rules/elixir/ has >=4 files (we expect 5)
  R4 Each common file carries ECC MIT attribution footer
  R5 rules/common/code-review.md has 'Pre-Report Gate' section

Source: ECC absorption (MIT (c) 2026 Affaan Mustafa).
"""
from __future__ import annotations
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
RULES = PP / "rules"


def r1():
    common = RULES / "common"
    if not common.is_dir():
        return False, "rules/common/ missing"
    md = list(common.glob("*.md"))
    if len(md) >= 5:
        return True, f"rules/common/ has {len(md)} files"
    return False, f"rules/common/ only {len(md)} files (need >=5)"


def r2():
    py = RULES / "python"
    if not py.is_dir():
        return False, "rules/python/ missing"
    md = list(py.glob("*.md"))
    if len(md) >= 4:
        return True, f"rules/python/ has {len(md)} files"
    return False, f"rules/python/ only {len(md)} files"


def r3():
    ex = RULES / "elixir"
    if not ex.is_dir():
        return False, "rules/elixir/ missing"
    md = list(ex.glob("*.md"))
    if len(md) >= 4:
        return True, f"rules/elixir/ has {len(md)} files"
    return False, f"rules/elixir/ only {len(md)} files"


def r4():
    common = RULES / "common"
    if not common.is_dir():
        return False, "rules/common/ missing"
    md = list(common.glob("*.md"))
    missing = []
    for f in md:
        body = f.read_text(encoding="utf-8", errors="replace")
        if "Affaan Mustafa" not in body or "MIT" not in body:
            missing.append(f.name)
    if not missing:
        return True, f"{len(md)} files carry ECC MIT attribution"
    return False, f"missing attribution in: {missing}"


def r5():
    crf = RULES / "common" / "code-review.md"
    if not crf.is_file():
        return False, "rules/common/code-review.md missing"
    body = crf.read_text(encoding="utf-8", errors="replace")
    if "Pre-Report Gate" in body and "Common False Positives" in body:
        return True, "Pre-Report Gate + Common False Positives present"
    return False, "code-review.md missing key sections"


# Languages mirrored from ECC in the 2026-06-06 gap pass (elixir is PP-only,
# common/python pre-existed -> covered by R1/R2/R4).
ABSORBED_LANGS = ["angular", "arkts", "cpp", "csharp", "dart", "fsharp",
                  "golang", "java", "kotlin", "perl", "php", "react", "ruby",
                  "rust", "swift", "typescript", "web"]


def r6():
    """Every absorbed language dir exists and every mirrored file carries the
    ECC MIT attribution (proves the gap-pass mirror is complete + well-formed)."""
    missing_lang = [l for l in ABSORBED_LANGS if not (RULES / l).is_dir()]
    if missing_lang:
        return False, f"absorbed langs missing: {missing_lang}"
    no_attrib = []
    nfiles = 0
    for lang in ABSORBED_LANGS:
        for f in (RULES / lang).glob("*.md"):
            nfiles += 1
            body = f.read_text(encoding="utf-8", errors="replace")
            if "Affaan Mustafa" not in body or "MIT" not in body:
                no_attrib.append(f"{lang}/{f.name}")
    if no_attrib:
        return False, (f"{len(no_attrib)} absorbed files miss attribution: "
                       f"{no_attrib[:5]}")
    return True, (f"{len(ABSORBED_LANGS)} absorbed langs present; all {nfiles} "
                  f"files carry ECC MIT attribution")


def main() -> int:
    checks = [("R1-common-files", r1),
              ("R2-python-files", r2),
              ("R3-elixir-files", r3),
              ("R4-attribution", r4),
              ("R5-code-review-sections", r5),
              ("R6-absorbed-langs", r6)]
    ok = 0
    for name, fn in checks:
        try:
            passed, msg = fn()
        except Exception as exc:
            passed, msg = False, f"unhandled {type(exc).__name__}: {exc}"
        tag = "PASS" if passed else "FAIL"
        print(f"  [{tag}] {name:<25s} {msg}")
        if passed:
            ok += 1
    total = len(checks)
    print(f"RULES_PROBE = {ok}/{total}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
