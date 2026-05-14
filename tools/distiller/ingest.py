#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KobiiDistillerOS atomic ingestor — pre-LLM adversarial gate.

Reads a single source file. Enforces, in order:
  1. Size cap (schema.ingestor_limits.max_input_bytes, default 1 MB).
     `--force` bypasses; the decision is recorded in the sidecar.
  2. Placeholder rejection. Any literal forbidden token from
     schema.forbidden_tokens appearing OUTSIDE Markdown code fences
     is a hard reject (exit 2). `--force` demotes the reject to a
     warning logged in the sidecar — used for meta-discourse inputs
     (the canonical fixture is one such input: it documents the
     placeholder contract by naming the tokens).
  3. Secret redaction. Every schema.redaction_patterns regex is
     replaced in the redacted body with `[REDACTED:<type>]`. The
     ORIGINAL file is never mutated. Replacement is performed on the
     redacted body, never logged with the raw secret value.
  4. Chunking. Splits on `^## ` headings, falling back to
     `chunk_fallback_block_bytes` (default 50 KB) when a chunk
     exceeds the fallback budget. Sub-split boundaries snap to the
     last newline within the window for readability.

Emits a sidecar JSON describing the operation. The sidecar is
deterministic: running the ingestor twice on the same input with the
same schema produces byte-identical output. This is what makes
`fixtures/expected/ingest_sample.json` a useful golden.

`--scan-only` is the lightweight mode: runs gates 2 and 3 only and
prints a JSON summary instead of writing a sidecar. Returns exit 2
if any forbidden token survives the code-fence-aware scan, else 0.
Reuses the same regex stack so it cannot diverge from full ingest.

Exit codes:
  0  OK — sidecar written (default) or scan-only clean.
  1  usage / file-not-found.
  2  placeholder reject (input contains a forbidden token outside
     code fences and `--force` was not passed).
  3  size > cap and `--force` not passed.
  4  schema.json parse / load error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.json"

_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```|`[^`\n]+`")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _load_schema() -> dict:
    if not SCHEMA_PATH.is_file():
        print(f"[ingest] schema.json not found at {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(4)
    try:
        return json.loads(_read_text(SCHEMA_PATH))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[ingest] schema.json parse error: {exc}", file=sys.stderr)
        sys.exit(4)


def _strip_code_fences(body: str) -> str:
    return _CODE_FENCE_RE.sub(" ", body)


def _find_placeholders(text: str, tokens: List[str]) -> List[str]:
    scan = _strip_code_fences(text)
    return [tok for tok in tokens if tok in scan]


def _apply_redactions(text: str, patterns: dict) -> Tuple[str, List[dict]]:
    redacted = text
    log: List[dict] = []
    for name, pattern in patterns.items():
        compiled = re.compile(pattern)
        count = len(compiled.findall(redacted))
        if count:
            log.append({"type": name, "count": count})
        redacted = compiled.sub(f"[REDACTED:{name}]", redacted)
    return redacted, log


def _chunk(text: str, heading_re: re.Pattern, fallback_bytes: int) -> List[dict]:
    chunks: List[dict] = []
    matches = list(heading_re.finditer(text))
    boundaries: List[Tuple[int, str]] = []
    if not matches:
        boundaries.append((0, "<MONOBLOCK>"))
    else:
        if matches[0].start() > 0:
            boundaries.append((0, "<PREAMBLE>"))
        for m in matches:
            boundaries.append((m.start(), m.group(0).strip()))

    end_positions = [pos for pos, _ in boundaries[1:]] + [len(text)]

    for (start, heading), end in zip(boundaries, end_positions):
        block = text[start:end]
        block_bytes = block.encode("utf-8")
        if len(block_bytes) <= fallback_bytes:
            chunks.append({
                "index": len(chunks),
                "heading": heading,
                "byte_start": start,
                "byte_end": end,
                "char_count": len(block),
            })
            continue
        offset = 0
        while offset < len(block_bytes):
            window = block_bytes[offset:offset + fallback_bytes]
            if offset + fallback_bytes < len(block_bytes):
                last_nl = window.rfind(b"\n")
                if last_nl > 0:
                    window = window[:last_nl]
            sub_text = window.decode("utf-8", errors="replace")
            chunks.append({
                "index": len(chunks),
                "heading": f"{heading} (split)",
                "byte_start": start + offset,
                "byte_end": start + offset + len(window),
                "char_count": len(sub_text),
            })
            offset += len(window)
    return chunks


def _run_scan_only(src: Path, schema: dict) -> int:
    """Run gates 2 + 3 (placeholder reject + redaction probe) without
    writing a sidecar. Used to validate arbitrary input files against the
    Reality Contract — e.g. parts/sleepy/distiller.md before commit."""
    text = _read_text(src)
    forbidden_tokens = schema["forbidden_tokens"]
    redaction_patterns = schema["redaction_patterns"]

    placeholder_hits = _find_placeholders(text, forbidden_tokens)
    _, redaction_log = _apply_redactions(text, redaction_patterns)

    summary = {
        "mode": "scan-only",
        "source": str(src),
        "placeholder_hits": placeholder_hits,
        "redaction_log": redaction_log,
        "result": "FAIL" if placeholder_hits else "OK",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 2 if placeholder_hits else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ingest.py",
        description="KobiiDistillerOS atomic ingestor",
    )
    parser.add_argument("source", help="path to raw input file")
    parser.add_argument(
        "--force",
        action="store_true",
        help="bypass size cap AND placeholder reject (logged in sidecar)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="path for sidecar JSON (default: <source>.ingest.json)",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="scan input for forbidden tokens and secret patterns (code-fence-aware); print JSON summary; exit 0 if clean / 2 if dirty. No sidecar written.",
    )
    args = parser.parse_args()

    src = Path(args.source).resolve()
    if not src.is_file():
        print(f"[ingest] not a file: {src}", file=sys.stderr)
        sys.exit(1)

    schema = _load_schema()

    if args.scan_only:
        sys.exit(_run_scan_only(src, schema))

    limits = schema["ingestor_limits"]
    size_cap = limits["max_input_bytes"]
    fallback_bytes = limits["chunk_fallback_block_bytes"]
    heading_re = re.compile(limits["chunk_heading_regex"], re.MULTILINE)
    forbidden_tokens = schema["forbidden_tokens"]
    redaction_patterns = schema["redaction_patterns"]

    raw_bytes = src.read_bytes()
    size = len(raw_bytes)
    overrides: List[str] = []

    if size > size_cap:
        if not args.force:
            print(
                f"[ingest] REJECT — size {size} bytes > cap {size_cap}. "
                f"Use --force to override (decision is logged).",
                file=sys.stderr,
            )
            sys.exit(3)
        overrides.append(f"size_cap (size {size} > cap {size_cap})")

    text = _read_text(src)
    placeholder_hits = _find_placeholders(text, forbidden_tokens)
    if placeholder_hits:
        if not args.force:
            print(
                f"[ingest] REJECT — placeholder token(s) detected outside code fences: "
                f"{placeholder_hits}. Use --force for meta-discourse inputs.",
                file=sys.stderr,
            )
            sys.exit(2)
        overrides.append(f"placeholder_reject (tokens: {placeholder_hits})")

    redacted_text, redaction_log = _apply_redactions(text, redaction_patterns)
    chunks = _chunk(redacted_text, heading_re, fallback_bytes)

    out_path = (
        Path(args.output).resolve()
        if args.output
        else src.with_suffix(src.suffix + ".ingest.json")
    )

    sidecar = {
        "schema_version": schema.get("version", "?"),
        "source": str(src),
        "size_bytes": size,
        "forced": bool(overrides),
        "overrides": overrides,
        "redactions": redaction_log,
        "placeholder_warnings": placeholder_hits if overrides else [],
        "chunk_strategy": limits["chunk_strategy"],
        "chunk_count": len(chunks),
        "chunks": chunks,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"[ingest] OK — {size} bytes -> {len(chunks)} chunk(s) -> {out_path}"
    )
    if overrides:
        print(f"[ingest]   overrides: {overrides}")
    if redaction_log:
        print(f"[ingest]   redactions: {redaction_log}")
    sys.exit(0)


if __name__ == "__main__":
    main()
