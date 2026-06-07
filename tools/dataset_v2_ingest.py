#!/usr/bin/env python3
"""Ingest the NEW Parts (XI..XXIII) of the v2 dataset re-export (Sprint 1 / M2).

The v2 export `(2).md` is a clean APPEND over the variant v1 was ingested
from: `(2)` == `(1)` + Parts XI..XXIII (empirically confirmed by
tools/dataset_v2_diff.py -- 0 grown / 0 shrunk common sections, 160
sections only-in-(2), PART XI begins exactly where (1) ended).

This script therefore:
  * NEVER touches the existing pp_dataset_01..10 files (Parts I-X are
    byte-stable);
  * slices `(2).md` at its own ``# ... EXTENSION DATASET PART <roman>``
    headers;
  * writes each new Part (number > 10) as pp_dataset_<NN>_<slug>.md with
    a provenance header (source, part label, source line range, sha);
  * regenerates pp_dataset_MASTER.md from real file stats.

Deterministic + stdlib-only. The 631 KB source is parsed in-process and
never enters the agent context (token austerity).
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

_PART_RE = re.compile(r"^#\s+.*EXTENSION DATASET PART\s+([IVXLC]+)\b", re.I)
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = _ROMAN.get(ch, 0)
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def slugify(title: str) -> str:
    t = title.lstrip("#").strip().lower()
    # take the part before the first colon (the OS name) for a tight slug
    head = t.split(":", 1)[0]
    head = re.sub(r"[^a-z0-9]+", "_", head).strip("_")
    return head[:48] or "part"


def descriptive_title(lines: list[str], part_header_idx: int) -> str:
    """First non-empty line after the PART header (the OS descriptor)."""
    for j in range(part_header_idx + 1, min(part_header_idx + 6, len(lines))):
        if lines[j].strip():
            return lines[j].lstrip("#").strip()
    return f"Part at line {part_header_idx + 1}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2-src", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--source-label", required=True,
                    help="human source label recorded in headers")
    ap.add_argument("--min-part", type=int, default=11,
                    help="lowest part NUMBER to ingest (default 11 = XI)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.v2_src)
    if not src.is_file():
        print(f"ABORT: source missing: {src}")
        return 2
    raw = src.read_bytes()
    src_sha = hashlib.sha256(raw).hexdigest()
    lines = raw.decode("utf-8", errors="replace").splitlines()

    # Collect PART headers: (line_idx0, roman, number).
    parts: list[tuple[int, str, int]] = []
    for i, ln in enumerate(lines):
        m = _PART_RE.match(ln)
        if m:
            roman = m.group(1).upper()
            parts.append((i, roman, roman_to_int(roman)))

    if not parts:
        print("ABORT: no PART headers found.")
        return 2

    # Build slices: each part spans to the next part header (or EOF).
    vault = Path(args.vault)
    vault.mkdir(parents=True, exist_ok=True)
    written: list[tuple[str, int, int, int, int]] = []  # name, num, lines, bytes, (s,e)

    for idx, (start, roman, num) in enumerate(parts):
        if num < args.min_part:
            continue
        end = parts[idx + 1][0] - 1 if idx + 1 < len(parts) else len(lines) - 1
        body = lines[start:end + 1]
        title = descriptive_title(lines, start)
        slug = slugify(title)
        fname = f"pp_dataset_{num:02d}_{slug}.md"
        fpath = vault / fname

        header = [
            f"# PP Dataset Part {roman} -- {title}",
            "",
            f"**Source:** {args.source_label}",
            f"**Source sha256:** {src_sha[:16]}",
            f"**Source line range:** {start + 1}-{end + 1} "
            f"({len(body)} lines)",
            f"**Part number:** {num} (roman {roman})",
            "**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 "
            "completeness recovery -- Parts XI-XXIII were absent from v1).",
            "",
            "---",
            "",
        ]
        content = "\n".join(header + body) + "\n"
        nbytes = len(content.encode("utf-8"))
        if not args.dry_run:
            fpath.write_text(content, encoding="utf-8")
        written.append((fname, num, len(body), nbytes, (start + 1, end + 1)))

    # Regenerate MASTER from real file stats (all pp_dataset_*.md).
    all_files = sorted(
        (p for p in vault.glob("pp_dataset_*.md") if p.name != "pp_dataset_MASTER.md"),
        key=lambda p: p.name)
    toc = [
        "# PP Dataset -- Master Index",
        "",
        f"**Source (v2):** {args.source_label}",
        f"**Source sha256:** {src_sha[:16]}",
        "**Updated:** Sprint 1 / M2 -- Parts XI-XXIII ingested (completeness "
        "recovery; Parts I-X unchanged from v1).",
        f"**Files:** {len(all_files)} content files + this master",
        "",
        "## Table of Contents",
        "",
        "| File | Lines | Bytes |",
        "|---|---|---|",
    ]
    total_bytes = 0
    for p in all_files:
        b = p.stat().st_size
        total_bytes += b
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        toc.append(f"| [{p.name}]({p.name}) | {n} | {b} |")
    toc.append(f"| **total** | | **{total_bytes}** |")
    toc += [
        "",
        "## Provenance",
        "",
        "- Parts I-X: ingested from the (1) 328 KB export, sealed 2026-06-01 "
        "BL-DATASET-001 (byte-stable, untouched here).",
        "- Parts XI-XXIII: ingested from the (2) 631 KB export by "
        "`tools/dataset_v2_ingest.py`. Verified a clean append over (1) by "
        "`tools/dataset_v2_diff.py` (0 grown / 0 shrunk common sections).",
        "",
    ]
    master = vault / "pp_dataset_MASTER.md"
    if not args.dry_run:
        master.write_text("\n".join(toc) + "\n", encoding="utf-8")

    print(f"=== INGEST {'(DRY RUN)' if args.dry_run else ''} ===")
    print(f"source: {src} ({len(lines)} lines, sha {src_sha[:12]})")
    print(f"PART headers: {len(parts)}; ingested (num >= {args.min_part}): "
          f"{len(written)}")
    for name, num, nl, nb, (s, e) in written:
        print(f"  {name}  part {num}  src L{s}-{e}  {nl} lines  {nb} bytes")
    print(f"MASTER regenerated: {len(all_files)} content files, "
          f"{total_bytes} total bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
