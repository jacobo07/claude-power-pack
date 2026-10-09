"""L1 step 1 (deterministic, zero model): segment the Owner's GSD X source prompts into obligation sections.

A section is a `=====` banner, a title line, a `=====` banner, then the body up to the next banner. Each section
gets a stable id from its normalized title; identical bodies across prompts collapse into one row that lists every
source. Output: vault/specs/gsdx-factory/l1/sections.json (rows to be dispositioned by L1 step 2).

    python tools/gsdx_obligation_extract.py [--check]
--check exits 1 if sections.json is missing or stale against the current sources (sha mismatch).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "vault" / "specs" / "gsdx-factory" / "sources"
OUT = ROOT / "vault" / "specs" / "gsdx-factory" / "l1" / "sections.json"
BANNER = re.compile(r"^\s*={8,}\s*$")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "untitled"


def segment(text: str) -> list[tuple[str, str]]:
    """[(title, body)] in order; text before the first banner is the preamble."""
    lines = text.split("\n")
    out, title, body, i = [], "PREAMBLE", [], 0
    while i < len(lines):
        if BANNER.match(lines[i]) and i + 2 < len(lines) and BANNER.match(lines[i + 2]) and lines[i + 1].strip():
            out.append((title, "\n".join(body).strip()))
            title, body, i = lines[i + 1].strip(), [], i + 3
            continue
        body.append(lines[i])
        i += 1
    out.append((title, "\n".join(body).strip()))
    return [(t, b) for t, b in out if b]


def build() -> dict:
    srcs = sorted(SRC.glob("*.txt"))
    rows: dict[str, dict] = {}
    by_body: dict[str, str] = {}
    for p in srcs:
        for title, body in segment(p.read_text(encoding="utf-8")):
            bsha = hashlib.sha256(_norm(body).encode()).hexdigest()[:16]
            rid = by_body.get(bsha)
            if rid is None:
                base, k = f"S-{_slug(title)}", 2
                rid = base
                while rid in rows:
                    rid, k = f"{base}-{k}", k + 1
                rows[rid] = {"id": rid, "title": title, "body_sha": bsha, "lines": body.count("\n") + 1,
                             "sources": [], "body": body}
                by_body[bsha] = rid
            rows[rid]["sources"].append(p.name)
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in srcs}
    return {"sources": manifest, "count": len(rows), "rows": list(rows.values())}


def main(argv: list[str]) -> int:
    doc = build()
    if "--check" in argv:
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 -- missing or unreadable is stale
            print("L1_SECTIONS STALE: sections.json missing or unreadable")
            return 1
        ok = old.get("sources") == doc["sources"] and old.get("count") == doc["count"]
        print(f"L1_SECTIONS {'FRESH' if ok else 'STALE'} count={doc['count']}")
        return 0 if ok else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    multi = sum(1 for r in doc["rows"] if len(r["sources"]) > 1)
    print(f"L1_SECTIONS WROTE count={doc['count']} shared_across_prompts={multi} sources={len(doc['sources'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
