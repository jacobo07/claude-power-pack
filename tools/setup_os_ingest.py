#!/usr/bin/env python3
"""Ingest the CPP Setup OS dataset into vault/knowledge_base/setup_os/ (M10).

Source `Dataset CPP Setup 1.txt` is plain text in FOUR parts, delimited
by ``... PROPOSITO DE LA PARTE <N>`` section headers (Part I has no such
header -- it runs from the top to the Part II marker). Slices by part +
writes a MASTER. Deterministic + stdlib-only; source parsed in-process.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

# Matches "41. PROPOSITO DE LA PARTE II" etc. (accent-insensitive on O).
_PARTE_RE = re.compile(r"PROP[OÓ]SITO DE LA PARTE\s+([IVXLC0-9]+)", re.I)
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def to_int(s: str) -> int:
    if s.isdigit():
        return int(s)
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = _ROMAN.get(ch, 0)
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


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

    # Boundaries: Part I starts at line 0; each PROPOSITO marker for
    # parts >= 2 opens a new part.
    bounds: list[tuple[int, int]] = [(0, 1)]  # (line_idx0, part_num)
    for i, ln in enumerate(lines):
        m = _PARTE_RE.search(ln)
        if m:
            num = to_int(m.group(1))
            if num >= 2 and num > bounds[-1][1]:
                bounds.append((i, num))

    titles = {
        1: "Setup OS Foundations -- Scanner, ROI, Dry-Run, Operating Loop",
        2: "Setup Transaction, Registry, Rollback, Kill-Switch, Validation",
        3: "Setup Oracle, Policy, Autonomy, Decision Journal, Value Density",
        4: "Setup Observability, Doctor/Lint, Drift, Recovery, Command Center",
    }
    vault = Path(args.vault)
    vault.mkdir(parents=True, exist_ok=True)
    written = []
    for idx, (start, num) in enumerate(bounds):
        end = bounds[idx + 1][0] - 1 if idx + 1 < len(bounds) else len(lines) - 1
        body = lines[start:end + 1]
        title = titles.get(num, f"Part {num}")
        fname = f"setup_os_{num:02d}_{re.sub(r'[^a-z0-9]+', '_', title.lower().split('--')[0].strip())[:36]}.md"
        header = [
            f"# CPP Setup OS -- PART {num}: {title}",
            "",
            f"**Source:** {args.source_label}",
            f"**Source sha256:** {sha[:16]}",
            f"**Source line range:** {start + 1}-{end + 1} ({len(body)} lines)",
            "**Ingested by:** tools/setup_os_ingest.py (Sprint 3 / M10).",
            "",
            "---",
            "",
        ]
        content = "\n".join(header + body) + "\n"
        if not args.dry_run:
            (vault / fname).write_text(content, encoding="utf-8")
        written.append((fname, num, len(body), len(content.encode("utf-8"))))

    toc = [
        "# CPP Setup OS -- Master Index",
        "",
        f"**Source:** {args.source_label}",
        f"**Source sha256:** {sha[:16]}  ({len(lines)} source lines)",
        "**Ingested by:** tools/setup_os_ingest.py (Sprint 3 / M10).",
        "",
        "Superior-to-official-plugin setup OS: it EXECUTES (scan -> ROI -> "
        "secure install + rollback), not just recommends. 10 pillars; "
        "pillars 1-3 implemented (scanner / ROI / secure installer), 4-10 "
        "in setup_os_ROADMAP.md.",
        "",
        "## Parts",
        "",
        "| File | Part | Lines | Bytes |",
        "|---|---|---|---|",
    ]
    total = 0
    for fname, num, nl, nb in written:
        total += nb
        toc.append(f"| [{fname}]({fname}) | {num} | {nl} | {nb} |")
    toc.append(f"| **total** | | | **{total}** |")
    toc += [
        "",
        "## Implemented modules (Sprint 3)",
        "- `modules/setup_os/scanner.py` -- Project Intelligence Scanner "
        "(source secs. 7 PROJECT PROFILE SCANNER, 9 AUTOMATION SURFACE).",
        "- `modules/setup_os/roi_analyzer.py` -- ROI ranking (secs. 10-11).",
        "- `modules/setup_os/secure_installer.py` -- dry-run + rollback "
        "(secs. 13 DRY-RUN FIRST, 54 ROLLBACK SYSTEM); secret scan first.",
        "",
    ]
    if not args.dry_run:
        (vault / "setup_os_MASTER.md").write_text("\n".join(toc) + "\n",
                                                  encoding="utf-8")

    print(f"=== CPP SETUP OS INGEST {'(DRY RUN)' if args.dry_run else ''} ===")
    print(f"source: {src} ({len(lines)} lines, sha {sha[:12]})")
    print(f"parts: {len(bounds)} {[b[1] for b in bounds]}")
    for fname, num, nl, nb in written:
        print(f"  {fname}  PART {num}  {nl} lines  {nb} bytes")
    print(f"MASTER + {len(written)} content files = {len(written) + 1} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
