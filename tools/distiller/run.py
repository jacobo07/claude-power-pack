#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KobiiDistillerOS orchestrator — Phase D.

Single-shot prep + verify driver. The actual distillation step is
performed in-session by the running Claude Code agent (see
`commands/distill.md`); this script handles every step that does not
require an LLM:

    1. Run the atomic ingestor (`ingest.py`) on the source.
    2. Resolve the output root (default project-local, `--global`
       overrides to `~/.claude/knowledge_vault/distilled/...`).
    3. Create Tier_1 / Tier_2 / Tier_3 directories.
    4. Emit a READY.md manifest combining the ingestor sidecar summary,
       the Mother Prompt body, and an <<INSTRUCTION TO CLAUDE>> block
       that the in-session driver consumes.
    5. With `--verify`, run `validate.py` against the output root and
       return its exit code unchanged.

Without `--verify`, exit code is 0 on a clean prep regardless of
materialization progress (because materialization is not this
script's job).

Usage:
    python tools/distiller/run.py <source> [--global] [--force]
                                  [--scope-only] [--verify]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INGEST = HERE / "ingest.py"
VALIDATE = HERE / "validate.py"
MOTHER_PROMPT = ROOT / "parts" / "sleepy" / "distiller.md"


def _python() -> str:
    return sys.executable


def _resolve_output_root(source: Path, use_global: bool) -> Path:
    stem = source.stem
    if use_global:
        return Path.home() / ".claude" / "knowledge_vault" / "distilled" / stem
    return Path.cwd() / ".knowledge_vault" / "distilled" / stem


def _emit_ready(output_root: Path, source: Path, sidecar_path: Path) -> Path:
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8-sig"))
    mother_prompt_body = (
        MOTHER_PROMPT.read_text(encoding="utf-8-sig")
        if MOTHER_PROMPT.is_file()
        else "<<MOTHER PROMPT MISSING — see parts/sleepy/distiller.md>>"
    )

    redaction_summary = ", ".join(
        f"{r['type']}×{r['count']}" for r in sidecar.get("redactions", [])
    ) or "none"
    overrides = sidecar.get("overrides") or []
    placeholder_warnings = sidecar.get("placeholder_warnings") or []

    chunk_lines = []
    for chunk in sidecar.get("chunks", []):
        chunk_lines.append(
            f"  · chunk #{chunk['index']:>2}  bytes {chunk['byte_start']}–{chunk['byte_end']}"
            f"  ({chunk['char_count']} chars)  heading: {chunk['heading']}"
        )

    body = f"""# READY — KobiiDistillerOS prep manifest

**Source:** `{source}`
**Output root:** `{output_root}`
**Size:** {sidecar['size_bytes']} bytes
**Chunks:** {sidecar['chunk_count']}
**Redactions:** {redaction_summary}
**Overrides:** {overrides if overrides else 'none'}
**Placeholder warnings (meta-discourse):** {placeholder_warnings if placeholder_warnings else 'none'}

---

## Chunk index

{chr(10).join(chunk_lines) if chunk_lines else '  (no chunks emitted)'}

The redacted source body is the input to the distillation step. The
ingestor sidecar lives at:

    {sidecar_path}

---

## <<INSTRUCTION TO CLAUDE>>

You are the in-session driver. Materialize 19 markdown files under
`{output_root}` following the tier layout declared in
`tools/distiller/schema.json#tier_layout`:

- Tier_1: Secciones 1–7  (end marker `-- FIN DE TIER 1 --` on Sección 7)
- Tier_2: Secciones 8–13 (end marker `-- FIN DE TIER 2 --` on Sección 13)
- Tier_3: Secciones 14–19 (end marker `-- FIN DE TIER 3 --` on Sección 19)
- Final marker `-- FIN DE DATASET v1.0 --` on Sección 19 after the
  tier-end marker.

Each section file MUST contain, in order:
  1. Heading `## <N>. <SECTION_TITLE>` (titles from schema).
  2. Distilled body — no filler, no forbidden tokens.
  3. `🧮 Calculadora de ROI` block with fields
     `Tipo` / `ROI Temporal` / `ROI Riesgo` / `Escenario` / `Explicación`.
  4. `🏁 Cierre patrimonial` closing line.
  5. `🦅 Comentario del Oráculo` aside.

Sections 7–19 are currently gap-marked in the Mother Prompt
(`<<AWAITING OWNER VERBATIM — Q1.a>>`). DO NOT materialize them
until the Owner has pasted the verbatim Mother Prompt body and the
gap markers are gone from `parts/sleepy/distiller.md`.

After writing the section files, run:
    python tools/distiller/validate.py "{output_root}"

The validator must exit 0 before this run is considered Done.

---

## MOTHER PROMPT (verbatim — single source of truth)

{mother_prompt_body}
"""
    ready_path = output_root / "READY.md"
    ready_path.write_text(body, encoding="utf-8")
    return ready_path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="KobiiDistillerOS prep orchestrator",
    )
    parser.add_argument("source", help="path to raw input file")
    parser.add_argument(
        "--global",
        dest="use_global",
        action="store_true",
        help="write output under ~/.claude/knowledge_vault/distilled/",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="bypass ingestor size cap + placeholder reject",
    )
    parser.add_argument(
        "--scope-only",
        action="store_true",
        help="emit READY.md only; skip directory scaffolding",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="after prep, run validate.py against the output root",
    )
    args = parser.parse_args()

    src = Path(args.source).resolve()
    if not src.is_file():
        print(f"[run] not a file: {src}", file=sys.stderr)
        sys.exit(1)

    output_root = _resolve_output_root(src, args.use_global)

    if not args.scope_only:
        for tier in ("Tier_1", "Tier_2", "Tier_3"):
            (output_root / tier).mkdir(parents=True, exist_ok=True)
    else:
        output_root.mkdir(parents=True, exist_ok=True)

    sidecar_path = output_root / f"{src.stem}.ingest.json"
    ingest_cmd = [_python(), str(INGEST), str(src), "-o", str(sidecar_path)]
    if args.force:
        ingest_cmd.append("--force")
    print(f"[run] ingest: {' '.join(ingest_cmd)}")
    rc = subprocess.call(ingest_cmd)
    if rc != 0:
        print(f"[run] ingest failed (exit {rc}). Aborting prep.", file=sys.stderr)
        sys.exit(rc)

    ready_path = _emit_ready(output_root, src, sidecar_path)
    print(f"[run] READY: {ready_path}")
    print(f"[run] output root: {output_root}")
    print("[run] Next: the in-session driver materializes 19 section files; "
          "then run validate.py.")

    if args.verify:
        validate_cmd = [_python(), str(VALIDATE), str(output_root)]
        print(f"[run] verify: {' '.join(validate_cmd)}")
        sys.exit(subprocess.call(validate_cmd))

    sys.exit(0)


if __name__ == "__main__":
    main()
