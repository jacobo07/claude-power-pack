#!/usr/bin/env python3
"""Structural differ for the PP dataset re-exports (Sprint 1 / M1).

The source dataset exports are large (up to ~631 KB). To respect token
austerity we never read them into the agent context; instead this script
parses them in-process and emits a compact structural diff + a markdown
report under vault/audits/.

Compares:
  * source (1).md  -- the variant v1 was originally ingested FROM
  * source (2).md  -- the Owner-chosen "v2" candidate
  * the ingested v1 vault files (vault/knowledge_base/pp_dataset/*.md)

"Structural" = top-level section headers (``## N. TITLE`` / ``# TITLE``)
with their line span and byte size. This tells us empirically whether
(2) is a superset of (1) (truncation recovery), a duplicate, or genuinely
divergent -- without speculation.

Deterministic + stdlib-only. Run:
  python tools/dataset_v2_diff.py \
    --v1-src "<downloads>/PP_DATASET_20260531T122242Z (1).md" \
    --v2-src "<downloads>/PP_DATASET_20260531T122242Z (2).md" \
    --vault  vault/knowledge_base/pp_dataset \
    --iso    20260607T000000Z
"""
from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

# A top-level section header: "## 1. IDENTIDAD" or "# Title".
_SECTION_RE = re.compile(r"^(#{1,2})\s+(.*\S)\s*$")
# Numbered section like "## 12. FOO" -> capture the leading number for
# stable cross-file matching even if the title wording drifts slightly.
_NUM_RE = re.compile(r"^\s*(\d+)\s*[.\)]\s*(.*)$")


@dataclass
class Section:
    level: int
    title: str
    num: str | None          # leading section number if present
    start_line: int          # 1-based, inclusive
    end_line: int            # 1-based, inclusive
    n_lines: int
    n_bytes: int


@dataclass
class FileParse:
    path: str
    exists: bool
    total_lines: int = 0
    total_bytes: int = 0
    sha256: str = ""
    sections: list[Section] = field(default_factory=list)


def _read_lines(p: Path) -> tuple[list[str], int, str]:
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="replace")
    return text.splitlines(), len(raw), sha


def parse_file(path: Path) -> FileParse:
    if not path.is_file():
        return FileParse(path=str(path), exists=False)
    lines, nbytes, sha = _read_lines(path)
    fp = FileParse(path=str(path), exists=True, total_lines=len(lines),
                   total_bytes=nbytes, sha256=sha)

    # Identify header line indices (0-based) for top-level sections.
    headers: list[tuple[int, int, str, str | None]] = []
    for i, line in enumerate(lines):
        m = _SECTION_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        num = None
        nm = _NUM_RE.match(title)
        if nm:
            num = nm.group(1)
        headers.append((i, level, title, num))

    # Build sections by spanning each header to the next header start.
    for idx, (i, level, title, num) in enumerate(headers):
        end = headers[idx + 1][0] - 1 if idx + 1 < len(headers) else len(lines) - 1
        span = lines[i:end + 1]
        nbytes_sec = sum(len(s.encode("utf-8")) + 1 for s in span)
        fp.sections.append(Section(
            level=level, title=title, num=num,
            start_line=i + 1, end_line=end + 1,
            n_lines=len(span), n_bytes=nbytes_sec))
    return fp


def _key(sec: Section) -> str:
    """Stable cross-file key: section number if present, else lowered title."""
    if sec.num is not None:
        return f"#{sec.num}"
    return sec.title.lower()[:48]


def diff_sources(a: FileParse, b: FileParse) -> dict:
    """Diff two parsed source files by top-level (level-1/2 numbered) section."""
    def top_map(fp: FileParse) -> dict[str, Section]:
        out: dict[str, Section] = {}
        for s in fp.sections:
            if s.num is None and s.level > 1:
                continue  # skip un-numbered sub-headers for the top diff
            k = _key(s)
            # keep the largest occurrence if a key repeats
            if k not in out or s.n_bytes > out[k].n_bytes:
                out[k] = s
        return out

    ma, mb = top_map(a), top_map(b)
    only_a = sorted(set(ma) - set(mb))
    only_b = sorted(set(mb) - set(ma))
    common = sorted(set(ma) & set(mb))
    grown, shrunk, same = [], [], []
    for k in common:
        da, db = ma[k].n_bytes, mb[k].n_bytes
        if db > da * 1.10:
            grown.append((k, da, db))
        elif db < da * 0.90:
            shrunk.append((k, da, db))
        else:
            same.append((k, da, db))
    return {
        "only_a": [(k, ma[k]) for k in only_a],
        "only_b": [(k, mb[k]) for k in only_b],
        "grown": grown, "shrunk": shrunk, "same": same,
        "ma": ma, "mb": mb,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1-src", required=True)
    ap.add_argument("--v2-src", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--out-dir", default="vault/audits")
    args = ap.parse_args()

    v1 = parse_file(Path(args.v1_src))
    v2 = parse_file(Path(args.v2_src))
    vault_dir = Path(args.vault)
    vault_files = sorted(vault_dir.glob("pp_dataset_*.md")) if vault_dir.is_dir() else []

    print("=== SOURCE PARSE ===")
    for tag, fp in (("(1) v1-src", v1), ("(2) v2-src", v2)):
        if not fp.exists:
            print(f"{tag}: MISSING {fp.path}")
            continue
        print(f"{tag}: {fp.total_lines} lines / {fp.total_bytes} bytes / "
              f"{len(fp.sections)} headers / sha {fp.sha256[:12]}")

    if not (v1.exists and v2.exists):
        print("ABORT: a source file is missing.")
        return 2

    d = diff_sources(v1, v2)
    same_sha = v1.sha256 == v2.sha256
    print("\n=== (1) vs (2) TOP-LEVEL DIFF ===")
    print(f"identical bytes: {same_sha}")
    print(f"sections only in (1): {len(d['only_a'])}")
    print(f"sections only in (2): {len(d['only_b'])}")
    print(f"common: {len(d['same']) + len(d['grown']) + len(d['shrunk'])} "
          f"(grown {len(d['grown'])}, shrunk {len(d['shrunk'])}, same {len(d['same'])})")
    for k, da, db in d["grown"]:
        print(f"  GROWN {k}: {da} -> {db} bytes (+{db - da})")
    for k, da, db in d["shrunk"]:
        print(f"  SHRUNK {k}: {da} -> {db} bytes ({db - da})")
    for k, s in d["only_b"]:
        print(f"  ONLY-IN-(2) {k}: {s.title!r} {s.n_bytes} bytes")
    for k, s in d["only_a"]:
        print(f"  ONLY-IN-(1) {k}: {s.title!r} {s.n_bytes} bytes")

    print("\n=== INGESTED v1 VAULT FILES ===")
    vault_total = 0
    for f in vault_files:
        b = f.stat().st_size
        vault_total += b
        print(f"  {f.name}: {b} bytes")
    print(f"  vault total: {vault_total} bytes across {len(vault_files)} files")

    # Verdict heuristic.
    verdict = "UNKNOWN"
    if same_sha:
        verdict = "IDENTICAL -- (2) == (1); Sprint 1 is a no-op (already ingested)."
    elif d["only_b"] or d["grown"]:
        verdict = ("(2) ADDS CONTENT vs (1) -- v1 ingestion may be incomplete; "
                   "Sprint 1 = completeness recovery of new/grown sections.")
    elif d["only_a"] or d["shrunk"]:
        verdict = ("(2) HAS LESS than (1) -- (2) is likely truncated; the "
                   "originally-ingested (1) is more complete. Do NOT downgrade.")
    else:
        verdict = ("Same sections, similar sizes, different bytes -- cosmetic/"
                   "reformat only; Sprint 1 likely a no-op.")
    print(f"\n=== VERDICT ===\n{verdict}")

    # Write markdown report.
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / f"dataset_v2_diff_{args.iso}.md"
    lines_out: list[str] = []
    lines_out.append(f"# PP Dataset v2 Structural Diff -- {args.iso}\n")
    lines_out.append("Sprint 1 / M1 done-gate artifact. Generated by "
                     "`tools/dataset_v2_diff.py` (deterministic, stdlib-only).\n")
    lines_out.append("## Sources\n")
    lines_out.append(f"- (1) v1-src: `{v1.path}` -- {v1.total_lines} lines / "
                     f"{v1.total_bytes} B / sha `{v1.sha256[:12]}`")
    lines_out.append(f"- (2) v2-src: `{v2.path}` -- {v2.total_lines} lines / "
                     f"{v2.total_bytes} B / sha `{v2.sha256[:12]}`")
    lines_out.append(f"- identical bytes: **{same_sha}**\n")
    lines_out.append("## Verdict\n")
    lines_out.append(f"**{verdict}**\n")
    lines_out.append("## Top-level section diff ((1) -> (2))\n")
    lines_out.append("| change | section | (1) bytes | (2) bytes | delta |")
    lines_out.append("|---|---|---|---|---|")
    for k, da, db in d["grown"]:
        lines_out.append(f"| GROWN | {k} | {da} | {db} | +{db - da} |")
    for k, da, db in d["shrunk"]:
        lines_out.append(f"| SHRUNK | {k} | {da} | {db} | {db - da} |")
    for k, s in d["only_b"]:
        lines_out.append(f"| ONLY-(2) | {k} {s.title} | - | {s.n_bytes} | new |")
    for k, s in d["only_a"]:
        lines_out.append(f"| ONLY-(1) | {k} {s.title} | {s.n_bytes} | - | lost |")
    if not (d["grown"] or d["shrunk"] or d["only_a"] or d["only_b"]):
        lines_out.append("| (none) | all top-level sections match within 10% | | | |")
    lines_out.append("\n## Ingested v1 vault files\n")
    lines_out.append("| file | bytes |")
    lines_out.append("|---|---|")
    for f in vault_files:
        lines_out.append(f"| {f.name} | {f.stat().st_size} |")
    lines_out.append(f"| **total** | **{vault_total}** |")
    report.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    print(f"\nReport written: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
