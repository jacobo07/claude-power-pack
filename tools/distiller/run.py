#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KobiiDistillerOS orchestrator — Phase D (Sovereign Sealing v1.2).

Two subcommands:

  ingest <source>    Prep + (optional) verify. Runs ingest.py on the source,
                     scaffolds the Tier_N output tree, emits READY.md, and
                     optionally chains validate.py via --verify.

  check <path>       Walk an arbitrary directory and validate it against the
                     22-section schema. Wraps validate.py; same exit codes.

Back-compat shim: if argv[1] is neither `ingest` nor `check` nor a help flag,
the dispatcher injects `ingest` as the default subcommand so legacy callers
(`python run.py <source>`) keep working without migration. Algorithm:

    SUBCMDS = {"ingest", "check", "-h", "--help"}
    if len(argv) >= 2 and argv[1] not in SUBCMDS:
        argv.insert(1, "ingest")

The actual distillation step (materialization of the 22 section files) is
performed in-session by the running Claude Code agent against the Mother
Prompt at `parts/sleepy/distiller.md`; this script handles every step that
does NOT require an LLM.

Usage:
    python tools/distiller/run.py ingest <source> [--global] [--force]
                                                  [--scope-only] [--verify]
    python tools/distiller/run.py check <output-dir>
    python tools/distiller/run.py <source> ...       # back-compat → ingest
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

_SUBCMDS = {"ingest", "check", "-h", "--help"}


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

    body = f"""# READY — KobiiDistillerOS prep manifest (v1.2 Sovereign Sealing)

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

You are the in-session driver. Materialize 22 markdown files under
`{output_root}` following the tier layout declared in
`tools/distiller/schema.json#tier_layout`:

- Tier_1: Secciones 1–7   (end marker `-- FIN DE TIER 1 --` on Sección 7)
- Tier_2: Secciones 8–13  (end marker `-- FIN DE TIER 2 --` on Sección 13)
- Tier_3: Secciones 14–22 (end marker `-- FIN DE TIER 3 --` on Sección 22)
- Final marker `-- FIN DE DATASET v1.2 --` on Sección 22 after the
  tier-end marker.

Each section file MUST contain, in order:
  1. Heading `## <N>. <SECTION_TITLE>` (titles from schema).
  2. Tandas & Partes body (mandatory per `schema.tandas_partes_spec`):
     three depth-tandas (T1 / T2 / T3) × three orthogonal partes
     (I Narrativa / II Estructura / III ROI) per tanda.
  3. `🧮 Calculadora de ROI` block with fields
     `Tipo` / `ROI Temporal` / `ROI Riesgo` / `Escenario` / `Explicación`.
  4. `🏁 Cierre patrimonial` closing line.
  5. `🦅 Comentario del Oráculo` aside.

The canonical `🧨 KILL-SWITCH` marker appears once, inside §16
(Antifragilidad), inside its T3 tanda.

After writing the section files, run:
    python tools/distiller/run.py check "{output_root}"

The validator must exit 0 before this run is considered Done. Exit 5
is voice-gate enforcing mode (blacklist hit AND zero anchor hits across
the aggregated output — see schema.voice_gate).

---

## MOTHER PROMPT (verbatim — single source of truth)

{mother_prompt_body}
"""
    ready_path = output_root / "READY.md"
    ready_path.write_text(body, encoding="utf-8")
    return ready_path


def _run_ingest(args: argparse.Namespace) -> int:
    src = Path(args.source).resolve()
    if not src.is_file():
        print(f"[run] not a file: {src}", file=sys.stderr)
        return 1

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
        return rc

    ready_path = _emit_ready(output_root, src, sidecar_path)
    print(f"[run] READY: {ready_path}")
    print(f"[run] output root: {output_root}")
    print("[run] Next: the in-session driver materializes 22 section files; "
          "then run `python tools/distiller/run.py check <output_root>`.")

    if args.verify:
        validate_cmd = [_python(), str(VALIDATE), str(output_root)]
        print(f"[run] verify: {' '.join(validate_cmd)}")
        return subprocess.call(validate_cmd)

    return 0


def _run_check(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    if not target.is_dir():
        print(f"[run] not a directory: {target}", file=sys.stderr)
        return 1
    validate_cmd = [_python(), str(VALIDATE), str(target)]
    print(f"[run] check: {' '.join(validate_cmd)}")
    return subprocess.call(validate_cmd)


def main() -> None:
    # Back-compat shim: legacy positional callers (`run.py <source>`) get
    # `ingest` injected so they keep working. Documented in the module
    # docstring above. The set of recognized subcommand keywords is
    # _SUBCMDS — anything else is treated as a positional source path.
    if len(sys.argv) >= 2 and sys.argv[1] not in _SUBCMDS:
        sys.argv.insert(1, "ingest")

    parser = argparse.ArgumentParser(
        prog="run.py",
        description="KobiiDistillerOS prep + check orchestrator (v1.2 Sovereign Sealing)",
    )
    subparsers = parser.add_subparsers(dest="subcmd", required=True)

    p_ingest = subparsers.add_parser(
        "ingest",
        help="Run atomic ingestor + scaffold output tree + emit READY.md",
    )
    p_ingest.add_argument("source", help="path to raw input file")
    p_ingest.add_argument(
        "--global",
        dest="use_global",
        action="store_true",
        help="write output under ~/.claude/knowledge_vault/distilled/",
    )
    p_ingest.add_argument(
        "--force",
        action="store_true",
        help="bypass ingestor size cap + placeholder reject",
    )
    p_ingest.add_argument(
        "--scope-only",
        action="store_true",
        help="emit READY.md only; skip Tier_N directory scaffolding",
    )
    p_ingest.add_argument(
        "--verify",
        action="store_true",
        help="after prep, chain validate.py against the output root",
    )

    p_check = subparsers.add_parser(
        "check",
        help="Validate an existing output directory against the 22-section schema",
    )
    p_check.add_argument("path", help="output directory to validate")

    args = parser.parse_args()

    if args.subcmd == "ingest":
        sys.exit(_run_ingest(args))
    elif args.subcmd == "check":
        sys.exit(_run_check(args))
    else:
        parser.error(f"unknown subcommand: {args.subcmd}")


if __name__ == "__main__":
    main()
