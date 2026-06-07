#!/usr/bin/env python3
"""Ingest the SDD-OS dataset into vault/knowledge_base/sdd_os/ (Sprint 2 / M4).

The source `Dataset SDD-OS 1.txt` is plain text structured as
``PARTE <roman> -- <TITLE>`` top-level dividers (NOT markdown). This
slicer splits on those dividers and writes one vault file per PARTE plus
a MASTER index. Deterministic + stdlib-only; the source is parsed
in-process (never enters the agent context).

The dataset defines FOUR task tiers (0-3), not five -- Tier 3
("Strategic / Platform Task") already covers new-OS / framework /
cross-repo work. Downstream code (spec_gate.classify_tier, prd-tier
commands, per-tier OQS) is built to these four tiers.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

_PARTE_RE = re.compile(r"^PARTE\s+([IVXLC]+)\s*[—-]\s*(.*\S)", re.I)
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = _ROMAN.get(ch, 0)
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def slugify(title: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return t[:42] or "parte"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--source-label", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.src)
    if not src.is_file():
        print(f"ABORT: source missing: {src}")
        return 2
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    lines = raw.decode("utf-8", errors="replace").splitlines()

    partes: list[tuple[int, str, int, str]] = []  # line_idx0, roman, num, title
    for i, ln in enumerate(lines):
        m = _PARTE_RE.match(ln)
        if m:
            roman = m.group(1).upper()
            partes.append((i, roman, roman_to_int(roman), m.group(2).strip()))
    if not partes:
        print("ABORT: no PARTE headers found.")
        return 2

    vault = Path(args.vault)
    vault.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, int, int, int]] = []
    for idx, (start, roman, num, title) in enumerate(partes):
        # Part I absorbs the document preamble (lines before it).
        slice_start = 0 if idx == 0 else start
        end = partes[idx + 1][0] - 1 if idx + 1 < len(partes) else len(lines) - 1
        body = lines[slice_start:end + 1]
        fname = f"sdd_os_{num:02d}_{slugify(title)}.md"
        header = [
            f"# SDD-OS PARTE {roman} -- {title}",
            "",
            f"**Source:** {args.source_label}",
            f"**Source sha256:** {sha[:16]}",
            f"**Source line range:** {slice_start + 1}-{end + 1} "
            f"({len(body)} lines)",
            "**Ingested by:** tools/sdd_os_ingest.py (Sprint 2 / M4).",
            "**Tiers:** this OS defines FOUR tiers (0 Micro, 1 Standard, "
            "2 Feature/System, 3 Strategic/Platform).",
            "",
            "---",
            "",
        ]
        content = "\n".join(header + body) + "\n"
        if not args.dry_run:
            (vault / fname).write_text(content, encoding="utf-8")
        written.append((fname, num, len(body), len(content.encode("utf-8"))))

    # MASTER index.
    toc = [
        "# SDD-OS -- Master Index",
        "",
        f"**Source:** {args.source_label}",
        f"**Source sha256:** {sha[:16]}",
        f"**Source total lines:** {len(lines)}",
        "**Ingested by:** tools/sdd_os_ingest.py (Sprint 2 / M4).",
        "",
        "Spec-Driven Development OS. Core law: **Spec First. Execution "
        "Second. Validation Always.** Defines FOUR task tiers (0-3); Tier "
        ">= 2 requires a PRD before execution.",
        "",
        "## Parts",
        "",
        "| File | PARTE | Lines | Bytes |",
        "|---|---|---|---|",
    ]
    total = 0
    roman_by_num = {num: roman for (_, roman, num, _) in partes}
    for fname, num, nl, nb in written:
        total += nb
        toc.append(f"| [{fname}]({fname}) | {roman_by_num[num]} | {nl} | {nb} |")
    toc.append(f"| **total** | | | **{total}** |")
    toc += [
        "",
        "## Downstream wiring",
        "",
        "- `modules/spec_gate/gate.py::classify_tier()` -- free-text -> Tier 0-3.",
        "- `commands/prd-tier{0,1,2,3}.md` -- per-tier PRD templates.",
        "- `modules/skill_router/intent_classifier.py` -- `spec` domain "
        "extended with SDD-OS trigger keywords.",
        "- `modules/output_contracts` -- per-tier OQS floors (Tier0 60 / "
        "Tier1 70 / Tier2 80 / Tier3 90).",
        "",
    ]
    if not args.dry_run:
        (vault / "sdd_os_MASTER.md").write_text("\n".join(toc) + "\n",
                                                encoding="utf-8")

    print(f"=== SDD-OS INGEST {'(DRY RUN)' if args.dry_run else ''} ===")
    print(f"source: {src} ({len(lines)} lines, sha {sha[:12]})")
    print(f"PARTE headers: {len(partes)}")
    for fname, num, nl, nb in written:
        print(f"  {fname}  PARTE {roman_by_num[num]}  {nl} lines  {nb} bytes")
    print(f"MASTER + {len(written)} content files = {len(written) + 1} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
