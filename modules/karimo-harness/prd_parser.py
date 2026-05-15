#!/usr/bin/env python3
"""prd_parser.py - KARIMO PRD constraint extractor (deterministic state machine).

Intercepts /ultra Phase 1: ingests a raw-text PRD, extracts hard
constraints with pure regex/heuristics (NO LLM calls), emits a
schema-validated PRD_BASELINE.json plus a derived BLUEPRINT.md.

State machine:
    S1 TOKENIZE       split into header-anchored sections
    S2 CLASSIFY       tag each section intent from a bilingual keyword bank
    S3 EXTRACT        bucket constraints (must/must_not/perf/auth/deadline/integ)
    S4 SCHEMA_MAP     assemble + sha256 the canonical payload -> baseline dict
    S5 BLUEPRINT_EMIT blueprint_from_baseline() is a PURE function of S4 output

Exit codes:
    0  success
    2  schema mismatch (baseline failed self-validation)
    3  parser ambiguity (empty/unparseable input)

CLI:
    --in <file> | --text "<inline>" | (stdin)
    --out <baseline.json>            default: alongside input or ./PRD_BASELINE.json
    --blueprint <BLUEPRINT.md>       default: sibling of --out
    --emit-constraints               print <prd-constraints> block (for hook), no files
    --check                          round-trip determinism self-test, exit 0/2/3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

SCHEMA_VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "schema.json")

# --- Bilingual (EN/ES) keyword banks. Lowercased, word-ish matched. ---
KW = {
    "MUST_NOT": [
        "must not", "shall not", "may not", "cannot", "prohibited",
        "forbidden", "never", "no debe", "prohibido", "prohibo",
        "prohíbo", "terminantemente", "jamas", "jamás", "sin ",
        "zero ", "cero ", "ningun", "ningún", "ninguna",
    ],
    "MUST_HAVE": [
        "must ", "shall ", "will ", "required", "requires", "ha de ",
        "debe ", "debera", "deberá", "necesita", "obligatorio",
        "mandatory", "tiene que",
    ],
    "AUTH": [
        "auth", "authentication", "authorization", "login", "token",
        "credential", "401", "403", "oauth", "jwt", "session",
        "autenticacion", "autenticación", "credencial", "wiring real",
    ],
    "DEADLINE": [
        "deadline", "due ", "by end of", "before ", "eta", "antes de",
        "fecha limite", "fecha límite", "plazo", "due date",
    ],
    "INTEGRATION": [
        "integrate", "integration", "api", "webhook", "endpoint",
        "fts5", "hook", "cli", "frontend", "backend", "integra",
        "conectar", "conexion", "conexión", "pipeline", "sidecar",
    ],
}

# perf:  <op> <number> <unit>  OR  "less than 250 ms" / "en menos de 250ms"
_PERF_OP = re.compile(
    r"(<=|>=|≤|≥|<|>|==)\s*(\d+(?:\.\d+)?)\s*"
    r"(ms|s|sec|secs|seconds|segundos|tokens|token|kb|mb|gb|%|x)?",
    re.IGNORECASE,
)
_PERF_PHRASE = re.compile(
    r"(?:less than|under|faster than|at most|no more than|"
    r"menos de|en menos de|maximo de|máximo de|hasta)\s+"
    r"(\d+(?:\.\d+)?)\s*"
    r"(ms|s|sec|secs|seconds|segundos|tokens|token|kb|mb|gb|%)?",
    re.IGNORECASE,
)
_PHRASE_OP = "<="

_HEADER = re.compile(r"^\s*(#{1,6}\s+.*|\d+[.)]\s+.*|[-*]\s+\*\*.+\*\*.*|\[[^\]]+\].*)$")


def _norm(text: str) -> str:
    """Deterministic normalization: unify newlines, strip trailing ws,
    drop a UTF-8 BOM. No locale, no time — pure function."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text and text[0] == "﻿":
        text = text[1:]
    return "\n".join(ln.rstrip() for ln in text.split("\n")).strip()


# ---------- S1 TOKENIZE ----------
def tokenize(raw: str) -> list[dict]:
    norm = _norm(raw)
    sections: list[dict] = []
    cur = {"header": "(preamble)", "lines": []}
    for ln in norm.split("\n"):
        if _HEADER.match(ln) and ln.strip():
            if cur["lines"] or cur["header"] != "(preamble)":
                sections.append(cur)
            cur = {"header": ln.strip(), "lines": []}
        else:
            if ln.strip():
                cur["lines"].append(ln.strip())
    if cur["lines"] or cur["header"] != "(preamble)":
        sections.append(cur)
    return sections


# ---------- S2 CLASSIFY ----------
def _hits(text: str, bank: list[str]) -> bool:
    low = text.lower()
    return any(k in low for k in bank)


def classify(sections: list[dict]) -> list[dict]:
    out = []
    for s in sections:
        blob = (s["header"] + "\n" + "\n".join(s["lines"])).lower()
        if _hits(blob, KW["MUST_NOT"]):
            intent = "PROHIBITION"
        elif _PERF_OP.search(blob) or _PERF_PHRASE.search(blob):
            intent = "TARGET"
        elif _hits(blob, KW["AUTH"]):
            intent = "AUTH"
        elif _hits(blob, KW["DEADLINE"]):
            intent = "DEADLINE"
        elif _hits(blob, KW["INTEGRATION"]):
            intent = "INTEGRATION"
        elif _hits(blob, KW["MUST_HAVE"]):
            intent = "REQUIREMENT"
        else:
            intent = "NARRATIVE"
        out.append({**s, "intent": intent})
    return out


# ---------- S3 EXTRACT ----------
def _iter_units(sections: list[dict]):
    """Yield (section_header, unit_text) for every line and the header."""
    for s in sections:
        for ln in s["lines"]:
            yield s["header"], ln


def extract(sections: list[dict]) -> dict:
    must_have, must_not, integrations = [], [], []
    perf, auth, deadlines = [], [], []
    seen_mh, seen_mn, seen_int = set(), set(), set()

    for _hdr, ln in _iter_units(sections):
        low = ln.lower()

        if _hits(low, KW["MUST_NOT"]):
            if ln not in seen_mn:
                must_not.append(ln)
                seen_mn.add(ln)
        elif _hits(low, KW["MUST_HAVE"]):
            if ln not in seen_mh:
                must_have.append(ln)
                seen_mh.add(ln)

        for m in _PERF_OP.finditer(ln):
            perf.append({
                "raw": m.group(0).strip(),
                "op": {"≤": "<=", "≥": ">="}.get(m.group(1), m.group(1)),
                "value": float(m.group(2)),
                "unit": (m.group(3) or "").lower() or "unit",
            })
        for m in _PERF_PHRASE.finditer(ln):
            perf.append({
                "raw": m.group(0).strip(),
                "op": _PHRASE_OP,
                "value": float(m.group(1)),
                "unit": (m.group(2) or "").lower() or "unit",
            })

        if _hits(low, KW["AUTH"]):
            sig = next((k for k in KW["AUTH"] if k in low), "auth")
            auth.append({"raw": ln, "signal": sig.strip()})

        if _hits(low, KW["DEADLINE"]):
            mk = next((k for k in KW["DEADLINE"] if k in low), "deadline")
            deadlines.append({"raw": ln, "marker": mk.strip()})

        if _hits(low, KW["INTEGRATION"]):
            tok = next((k for k in KW["INTEGRATION"] if k in low), "integration")
            tok = tok.strip()
            if tok not in seen_int:
                integrations.append(tok)
                seen_int.add(tok)

    # Deterministic perf dedup (preserve first-seen order).
    pseen, pperf = set(), []
    for p in perf:
        key = (p["op"], p["value"], p["unit"])
        if key not in pseen:
            pseen.add(key)
            pperf.append(p)

    return {
        "must_have": must_have,
        "must_not": must_not,
        "perf_targets": pperf,
        "auth_required": auth,
        "deadlines": deadlines,
        "integrations": integrations,
    }


# ---------- S4 SCHEMA_MAP ----------
def _title_of(sections: list[dict]) -> str:
    for s in sections:
        h = s["header"]
        if h and h != "(preamble)":
            return re.sub(r"^[#\d.)\-*\s\[\]]+", "", h).strip() or "PRD"
        for ln in s["lines"]:
            if ln:
                return ln[:120]
    return "PRD"


def _canonical(payload: dict) -> str:
    """Stable serialization for hashing: sorted keys, no volatile fields."""
    return json.dumps(payload, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"))


def schema_map(raw: str, sections: list[dict], buckets: dict,
                source_label: str, stamp: bool) -> dict:
    core = {
        "title": _title_of(sections),
        "must_have": buckets["must_have"],
        "must_not": buckets["must_not"],
        "perf_targets": buckets["perf_targets"],
        "auth_required": buckets["auth_required"],
        "deadlines": buckets["deadlines"],
        "integrations": buckets["integrations"],
        "sections": [
            {"header": s["header"], "intent": s["intent"], "lines": s["lines"]}
            for s in sections
        ],
    }
    digest = hashlib.sha256(_canonical(core).encode("utf-8")).hexdigest()
    baseline = {
        "schema_version": SCHEMA_VERSION,
        "content_sha256": digest,
        "generated_at_utc": (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if stamp else None
        ),
        "source_label": source_label,
        **core,
    }
    return baseline


# ---------- S5 BLUEPRINT_EMIT (pure fn of baseline) ----------
def blueprint_from_baseline(b: dict) -> str:
    L = []
    L.append(f"# BLUEPRINT — {b['title']}")
    L.append("")
    L.append(f"<!-- derived purely from PRD_BASELINE.json "
             f"content_sha256={b['content_sha256']} -->")
    L.append("")
    L.append("## Hard Requirements (MUST)")
    for i, x in enumerate(b["must_have"] or ["(none extracted)"], 1):
        L.append(f"{i}. {x}")
    L.append("")
    L.append("## Prohibitions (MUST NOT)")
    for i, x in enumerate(b["must_not"] or ["(none extracted)"], 1):
        L.append(f"{i}. {x}")
    L.append("")
    L.append("## Performance Targets")
    if b["perf_targets"]:
        for p in b["perf_targets"]:
            L.append(f"- `{p['op']} {p['value']:g} {p['unit']}` "
                     f"(from: {p['raw']})")
    else:
        L.append("- (none extracted)")
    L.append("")
    L.append("## Auth / Wiring Signals")
    for x in b["auth_required"] or []:
        L.append(f"- [{x['signal']}] {x['raw']}")
    if not b["auth_required"]:
        L.append("- (none extracted)")
    L.append("")
    L.append("## Deadlines")
    for x in b["deadlines"] or []:
        L.append(f"- [{x['marker']}] {x['raw']}")
    if not b["deadlines"]:
        L.append("- (none extracted)")
    L.append("")
    L.append("## Integrations Surface")
    L.append(", ".join(b["integrations"]) if b["integrations"]
             else "(none extracted)")
    L.append("")
    L.append("## Implementation Seed Tasks")
    seed = 1
    for x in b["must_have"]:
        L.append(f"{seed}. Implement & verify: {x}")
        seed += 1
    for p in b["perf_targets"]:
        L.append(f"{seed}. Add measured gate: {p['op']} {p['value']:g} "
                 f"{p['unit']}")
        seed += 1
    if seed == 1:
        L.append("1. (no actionable seed tasks extracted — narrative PRD)")
    L.append("")
    return "\n".join(L)


def constraints_block(b: dict) -> str:
    parts = ['<prd-constraints rules="strict">']
    parts.append(f"TITLE: {b['title']}")
    if b["must_not"]:
        parts.append("PROHIBITED:")
        parts += [f"  - {x}" for x in b["must_not"]]
    if b["must_have"]:
        parts.append("REQUIRED:")
        parts += [f"  - {x}" for x in b["must_have"]]
    if b["perf_targets"]:
        parts.append("PERF:")
        parts += [f"  - {p['op']} {p['value']:g} {p['unit']}"
                  for p in b["perf_targets"]]
    parts.append(f"SOURCE_SHA256: {b['content_sha256']}")
    parts.append("</prd-constraints>")
    return "\n".join(parts)


# ---------- pipeline ----------
def parse(raw: str, source_label: str = "inline", stamp: bool = True) -> dict:
    sections = classify(tokenize(raw))
    buckets = extract(sections)
    return schema_map(raw, sections, buckets, source_label, stamp)


def _validate(baseline: dict) -> tuple[bool, str]:
    try:
        import jsonschema  # type: ignore
        with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
            schema = json.load(fh)
        jsonschema.validate(baseline, schema)
        return True, "jsonschema OK"
    except ImportError:
        # Fallback structural check — required keys + sha pattern.
        req = ["schema_version", "content_sha256", "title", "must_have",
               "must_not", "perf_targets", "auth_required", "deadlines",
               "integrations", "sections"]
        missing = [k for k in req if k not in baseline]
        if missing:
            return False, f"missing keys: {missing}"
        if not re.fullmatch(r"[0-9a-f]{64}", baseline["content_sha256"]):
            return False, "content_sha256 not a sha256 hex"
        return True, "structural OK (jsonschema not installed)"
    except Exception as e:  # noqa: BLE001  - validation failure is a result
        return False, f"schema mismatch: {e}"


def _atomic_write(path: str, data: str) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="KARIMO PRD parser")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--in", dest="infile")
    src.add_argument("--text", dest="text")
    ap.add_argument("--out", dest="out")
    ap.add_argument("--blueprint", dest="blueprint")
    ap.add_argument("--emit-constraints", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    if a.infile:
        with open(a.infile, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
        label = os.path.basename(a.infile)
    elif a.text:
        raw = a.text
        label = "inline"
    else:
        raw = sys.stdin.read()
        label = "stdin"

    if not raw or not raw.strip():
        print("prd_parser: empty input (ambiguity)", file=sys.stderr)
        return 3

    if a.check:
        b1 = parse(raw, label, stamp=False)
        b2 = parse(raw, label, stamp=False)
        if _canonical(b1) != _canonical(b2):
            print("CHECK FAIL: non-deterministic parse", file=sys.stderr)
            return 2
        bp1, bp2 = blueprint_from_baseline(b1), blueprint_from_baseline(b2)
        if bp1 != bp2 or bp1 != blueprint_from_baseline(json.loads(
                json.dumps(b1))):
            print("CHECK FAIL: blueprint not pure fn of baseline",
                  file=sys.stderr)
            return 2
        ok, msg = _validate(b1)
        if not ok:
            print(f"CHECK FAIL: {msg}", file=sys.stderr)
            return 2
        print(f"CHECK OK: deterministic + pure-blueprint + {msg} "
              f"(sha={b1['content_sha256'][:12]})")
        return 0

    baseline = parse(raw, label, stamp=True)
    ok, msg = _validate(baseline)
    if not ok:
        print(f"prd_parser: {msg}", file=sys.stderr)
        return 2

    if a.emit_constraints:
        print(constraints_block(baseline))
        return 0

    out = a.out or os.path.join(os.getcwd(), "PRD_BASELINE.json")
    bp = a.blueprint or os.path.join(os.path.dirname(os.path.abspath(out)),
                                     "BLUEPRINT.md")
    _atomic_write(out, json.dumps(baseline, indent=2, ensure_ascii=False,
                                  sort_keys=True) + "\n")
    _atomic_write(bp, blueprint_from_baseline(baseline))
    print(f"PRD_BASELINE -> {out}")
    print(f"BLUEPRINT    -> {bp}")
    print(f"content_sha256={baseline['content_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
