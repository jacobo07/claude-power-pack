#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KobiiDistillerOS output validator.

Walks <output_dir>/Tier_<T>/Seccion_<N>.md, enforces the contract declared
in tools/distiller/schema.json (verbatim markers + per-section required
blocks + Tandas & Partes structural layer + forbidden tokens + redaction
patterns + tier-end + dataset-final markers + voice gate).

Exit codes (highest wins when multiple errors land):
    0   pass — every section materialized, every block present, structural
        markers present, no forbidden tokens, no leaked secrets, voice gate
        clean.
    1   missing-marker — a section file is absent, gap-marked, or missing
        its heading / ROI block / closing line / oracle aside / Tanda /
        Parte / tier-end marker / dataset-final marker.
    2   forbidden-token — a literal forbidden token (TODO, FIXME, Coming
        Soon, <TU_URL_REAL>, ...) slipped into output.
    3   redaction-violation — a secret pattern surfaced in output. This
        should be impossible post-ingestor; if it fires, treat as an audit
        incident and stop the entire pipeline run.
    4   schema-parse error — schema.json itself is malformed or missing.
    5   voice-gate violation — when schema.voice_gate.mode == "enforcing"
        and at least one blacklist token appears across the aggregated
        output AND zero anchor tokens appear (global scope per
        schema.voice_gate.scope). Strict Mode per Q2.a Sovereign Sealing.

Usage:
    python tools/distiller/validate.py <output_dir>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _load_schema() -> dict:
    if not SCHEMA_PATH.is_file():
        print(f"[validate] schema.json not found at {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(4)
    try:
        return json.loads(_read_text(SCHEMA_PATH))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[validate] schema.json parse error: {exc}", file=sys.stderr)
        sys.exit(4)


def _heading_present(body: str, n: int, title: str) -> bool:
    pattern = rf"^##\s+{n}\.\s+{re.escape(title)}\s*$"
    return bool(re.search(pattern, body, re.MULTILINE))


_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```|`[^`\n]+`")


def _strip_code_fences(body: str) -> str:
    """Forbidden-token and redaction scans must ignore literal references
    inside Markdown code fences. A section that documents the contract
    by writing the words ``TODO`` or ``FIXME`` inside backticks is
    enumerating, not violating."""
    return _CODE_FENCE_RE.sub(" ", body)


def _roi_field_present(body: str, field: str) -> bool:
    # Match `**Field:**`, `**Field**:`, or bare `Field:` line-starts.
    pattern = rf"(?im)^\s*[*+-]?\s*\*?\*?{re.escape(field)}\*?\*?\s*:"
    return bool(re.search(pattern, body))


_TANDA_CAPTURE_RE = re.compile(r"^###\s+Tanda\s+(T[123])\b", re.MULTILINE)
_PARTE_CAPTURE_RE = re.compile(r"^####\s+Parte\s+(I{1,3})\b", re.MULTILINE)


def _check_tandas_partes(body: str, rel) -> List[Tuple[int, str]]:
    """Enforce schema.tandas_partes_spec per section body: every section
    must declare all three depth-tandas (T1/T2/T3) and all three orthogonal
    partes (I/II/III). Returns a list of (exit_code, message) tuples."""
    errors: List[Tuple[int, str]] = []
    tandas_seen = set(_TANDA_CAPTURE_RE.findall(body))
    partes_seen = set(_PARTE_CAPTURE_RE.findall(body))
    needed_tandas = {"T1", "T2", "T3"}
    needed_partes = {"I", "II", "III"}
    if tandas_seen != needed_tandas:
        missing = sorted(needed_tandas - tandas_seen)
        errors.append((1, f"{rel}: Tandas check — missing {missing} (found {sorted(tandas_seen)})"))
    if partes_seen != needed_partes:
        missing = sorted(needed_partes - partes_seen)
        errors.append((1, f"{rel}: Partes check — missing {missing} (found {sorted(partes_seen)})"))
    return errors


def _check_voice_gate(all_text: str, schema: dict) -> List[Tuple[int, str]]:
    """Global-scope voice gate. When schema.voice_gate.mode == "enforcing",
    the aggregated text across all materialized section files is scanned for
    corporate-vocabulary blacklist hits and nostalgic-anchor hits. If at
    least one blacklist token appears AND zero anchor tokens appear → exit 5.

    Code fences are stripped before scanning so contract documents that
    enumerate the blacklist by name (inside backticks) don't trip the gate."""
    vg = schema.get("voice_gate", {})
    if vg.get("mode") != "enforcing":
        return []
    scan = _strip_code_fences(all_text)
    blacklist_hits = [tok for tok in vg.get("blacklist_candidates", []) if tok in scan]
    anchor_hits = [tok for tok in vg.get("anchors_candidates", []) if tok in scan]
    if blacklist_hits and not anchor_hits:
        return [
            (
                vg.get("exit_code_when_enforcing", 5),
                (
                    "voice gate — "
                    f"{len(blacklist_hits)} blacklist hit(s) {blacklist_hits[:5]} "
                    "AND zero anchor hits across entire output (global scope). "
                    "Either remove the corporate vocabulary or add nostalgic anchors "
                    "(Refugio / MCPE / 2014 / cabaña / linterna / Helsinki / etc.)."
                ),
            )
        ]
    return []


def validate(output_dir: Path) -> int:
    schema = _load_schema()

    forbidden_tokens: List[str] = schema["forbidden_tokens"]
    redaction_patterns = {
        name: re.compile(pat) for name, pat in schema["redaction_patterns"].items()
    }
    blocks = schema["required_section_blocks"]
    roi_marker: str = blocks["roi_block"]["marker"]
    roi_fields: List[str] = blocks["roi_block"]["required_fields"]
    closing_marker: str = blocks["closing_marker"]
    oracle_marker: str = blocks["oracle_aside"]
    section_titles: dict = schema["section_titles"]
    tier_layout: dict = schema["tier_layout"]
    dataset_final: str = schema["dataset_final_marker"]

    errors: List[Tuple[int, str]] = []

    # Build expected paths from tier_layout — single source of truth for layout.
    expected_files: dict = {}
    for tier_name, tier in tier_layout.items():
        for n in tier["sections"]:
            expected_files[n] = output_dir / tier_name / f"Seccion_{n}.md"

    materialized_bodies: List[str] = []

    for n in sorted(expected_files):
        fpath = expected_files[n]
        rel = fpath.relative_to(output_dir.parent if fpath.is_absolute() else Path.cwd())
        if not fpath.is_file():
            errors.append((1, f"missing file: {rel}"))
            continue

        body = _read_text(fpath)
        materialized_bodies.append(body)

        if "<<AWAITING OWNER VERBATIM" in body:
            errors.append(
                (1, f"{rel}: contains <<AWAITING OWNER VERBATIM>> gap marker — section not yet materialized")
            )
            continue

        expected_title = section_titles.get(str(n), "")
        if not _heading_present(body, n, expected_title):
            errors.append((1, f"{rel}: missing heading '## {n}. {expected_title}'"))

        if roi_marker not in body:
            errors.append((1, f"{rel}: missing ROI block marker '{roi_marker}'"))
        else:
            for field in roi_fields:
                if not _roi_field_present(body, field):
                    errors.append((1, f"{rel}: ROI block missing field '{field}'"))

        if closing_marker not in body:
            errors.append((1, f"{rel}: missing closing marker '{closing_marker}'"))
        if oracle_marker not in body:
            errors.append((1, f"{rel}: missing oracle aside '{oracle_marker}'"))

        errors.extend(_check_tandas_partes(body, rel))

        scan_body = _strip_code_fences(body)
        for token in forbidden_tokens:
            if token in scan_body:
                errors.append((2, f"{rel}: forbidden token '{token}'"))
                break

        for name, pat in redaction_patterns.items():
            m = pat.search(scan_body)
            if m:
                snippet = m.group(0)[:40].replace("\n", " ")
                errors.append((3, f"{rel}: leaked secret pattern '{name}' — '{snippet}...'"))
                break

    # Tier-end markers attach to the LAST section file of each tier.
    for tier_name, tier in tier_layout.items():
        last_n = tier["sections"][-1]
        marker = tier["end_marker"]
        last_path = expected_files[last_n]
        if last_path.is_file():
            body = _read_text(last_path)
            if marker not in body:
                rel = last_path.relative_to(output_dir.parent if last_path.is_absolute() else Path.cwd())
                errors.append((1, f"{rel}: missing tier-end marker '{marker}'"))

    # Dataset-final marker lives on the very last section file.
    last_overall = expected_files[max(expected_files)]
    if last_overall.is_file():
        body = _read_text(last_overall)
        if dataset_final not in body:
            rel = last_overall.relative_to(output_dir.parent if last_overall.is_absolute() else Path.cwd())
            errors.append((1, f"{rel}: missing dataset-final marker '{dataset_final}'"))

    # Voice gate (global scope) — aggregates across every materialized body.
    if materialized_bodies:
        errors.extend(_check_voice_gate("\n".join(materialized_bodies), schema))

    if not errors:
        print(f"[validate] OK — {len(expected_files)} sections validated against schema v{schema.get('version','?')}")
        return 0

    max_code = max(code for code, _ in errors)
    for code, msg in errors:
        print(f"[validate] (exit {code}) {msg}", file=sys.stderr)
    print(f"[validate] FAIL — {len(errors)} error(s); highest exit code {max_code}", file=sys.stderr)
    return max_code


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: validate.py <output_dir>", file=sys.stderr)
        sys.exit(1)
    output_dir = Path(sys.argv[1]).resolve()
    if not output_dir.is_dir():
        print(f"[validate] not a directory: {output_dir}", file=sys.stderr)
        sys.exit(1)
    sys.exit(validate(output_dir))


if __name__ == "__main__":
    main()
