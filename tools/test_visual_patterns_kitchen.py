#!/usr/bin/env python3
"""test_visual_patterns_kitchen.py -- done-gate for REF-KITCHEN-001 (V-VPK-*).

Spec: vault/specs/cdio-kitchen-absorption.md. Hermetic and read-only: it reads the
visual-patterns corpus and drives the real motion resolver. It writes nothing.

  V-VPK-ENTRIES      VP-019..027 exist, carry provenance, a real "Cuando NO usar"
                     (HR-VP-01) and browser support (HR-VP-02)
  V-VPK-NO-CODE      no fenced code in any absorbed file: the source has no
                     license, so principles only (red drill on a fenced sample)
  V-VPK-CORPUS       the motion loader accepts VP-019..024 with zero errors
  V-VPK-EVIDENCE     nothing from this single unlicensed reference claims more
                     than 'research' (red drill on a synthetic 'local')
  V-VPK-ROUTING      the real resolver serves VP-019 on a delete page, withholds
                     every Kitchen pattern from a restrained onboarding page, and
                     serves VP-022/024 on a moderate landing (red drill: a
                     resolver that serves everything must fail)
  V-VPK-PROVENANCE   the observation record holds 15 component rows, the license
                     disposition and the rejected component
  V-VPK-INDEXED      README indexes VP-019..027 and VP-007 cites the new source
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules.cdio import motion_patterns as mp  # noqa: E402

CORPUS = mp.CORPUS_DIR
REF = "REF-KITCHEN-001"
OBS = os.path.join(CORPUS, "evidence", REF, "OBSERVATION.md")
ENTRIES = {
    "VP-019": "hold-to-confirm.md",
    "VP-020": "magnetic-drop-zone.md",
    "VP-021": "content-fit-dynamic-button.md",
    "VP-022": "scramble-text-reveal.md",
    "VP-023": "state-driven-physical-process.md",
    "VP-024": "self-drawing-stroke.md",
    "VP-025": "scroll-overflow-fade.md",
    "VP-026": "perforated-paper-silhouette.md",
    "VP-027": "tactile-skeuomorphic-object.md",
}
MOTION_IDS = {"VP-019", "VP-020", "VP-021", "VP-022", "VP-023", "VP-024"}
CEILING = "research"

HI = {"expressiveness": "moderate", "motion_budget": "medium", "reduced_motion": "equivalent"}
LO = {"expressiveness": "restrained", "motion_budget": "low", "reduced_motion": "equivalent"}

_passes = 0
_fails = 0


def _ok(name, detail):
    global _passes
    _passes += 1
    print(f"[PASS] {name}: {detail}")


def _fail(name, detail):
    global _fails
    _fails += 1
    print(f"[FAIL] {name}: {detail}")


def _read(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return fh.read()


def _front_matter(text):
    m = re.match(r"^---(.*?)---", text, flags=re.S)
    return m.group(1) if m else ""


def _section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    return m.group(1).strip() if m else ""


def has_fenced_code(text):
    return re.search(r"^\s*(```|~~~)", text, flags=re.M) is not None


def evidence_level(text):
    m = re.search(r"^\s*evidence_level:\s*(\S+)", _front_matter(text), flags=re.M)
    return m.group(1) if m else None


def over_ceiling(levels):
    """Return the ids whose evidence level is above the single-reference ceiling."""
    cap = mp.EVIDENCE_LEVELS.index(CEILING)
    return sorted(i for i, lvl in levels.items()
                  if lvl not in mp.EVIDENCE_LEVELS or mp.EVIDENCE_LEVELS.index(lvl) > cap)


def v_entries():
    bad = []
    for vid, fname in ENTRIES.items():
        path = os.path.join(CORPUS, fname)
        if not os.path.isfile(path):
            bad.append(f"{vid}: missing {fname}")
            continue
        text = _read(path)
        fm = _front_matter(text)
        if f"id: {vid}" not in fm:
            bad.append(f"{vid}: id not in front matter")
        if REF not in fm:
            bad.append(f"{vid}: provenance {REF} not in front matter")
        if len(_section(text, "Cuando NO usar")) < 40:
            bad.append(f"{vid}: 'Cuando NO usar' empty (HR-VP-01)")
        if not _section(text, "Soporte de navegador"):
            bad.append(f"{vid}: no browser support (HR-VP-02)")
    if bad:
        _fail("V-VPK-ENTRIES", "; ".join(bad))
    else:
        _ok("V-VPK-ENTRIES", f"{len(ENTRIES)} entries with provenance, HR-VP-01 and HR-VP-02")


def v_no_code():
    files = [os.path.join(CORPUS, f) for f in ENTRIES.values()] + [OBS]
    fenced = [os.path.basename(p) for p in files if os.path.isfile(p) and has_fenced_code(_read(p))]
    drill = has_fenced_code("text\n```tsx\nexport function X() {}\n```\n")
    if fenced or not drill:
        _fail("V-VPK-NO-CODE", f"fenced code in {fenced}; drill_ok={drill}")
    else:
        _ok("V-VPK-NO-CODE", f"{len(files)} files carry no fenced code; drill caught a fenced sample")


def v_corpus():
    entries, errors = mp.load_corpus()
    got = {e["id"] for e in entries}
    missing = sorted(MOTION_IDS - got)
    if errors or missing:
        _fail("V-VPK-CORPUS", f"errors={errors} missing={missing}")
    else:
        _ok("V-VPK-CORPUS", f"{len(entries)} motion entries, 0 errors, Kitchen ids all discovered")


def v_evidence():
    levels = {vid: evidence_level(_read(os.path.join(CORPUS, f)))
              for vid, f in ENTRIES.items() if os.path.isfile(os.path.join(CORPUS, f))}
    over = over_ceiling(levels)
    drill = over_ceiling({"VP-SYNTH": "local"}) == ["VP-SYNTH"]
    if over or len(levels) != len(ENTRIES) or not drill:
        _fail("V-VPK-EVIDENCE", f"over={over} n={len(levels)} drill_ok={drill}")
    else:
        _ok("V-VPK-EVIDENCE", f"{len(levels)} entries at or below '{CEILING}'; drill caught 'local'")


def routing_ok(resolve):
    ids = lambda r: {p["id"] for p in r["patterns"]}  # noqa: E731
    delete = resolve(LO, "app/settings/danger/delete-project.tsx")
    onboarding = resolve(LO, "app/onboarding/page.tsx")
    landing = resolve(HI, "app/landing/hero.tsx")
    return ("VP-019" in ids(delete)
            and "VP-020" not in ids(delete)
            and not ids(onboarding) & MOTION_IDS
            and {"VP-022", "VP-024"} <= ids(landing)
            and "VP-019" not in ids(landing))


def mutant_serves_everything(experience, surface, corpus_dir=CORPUS):
    entries, _ = mp.load_corpus(corpus_dir)
    return {"state": "applicable", "patterns": [{"id": e["id"]} for e in entries]}


def v_routing():
    real = routing_ok(mp.resolve)
    drill = not routing_ok(mutant_serves_everything)
    if not real or not drill:
        _fail("V-VPK-ROUTING", f"real_ok={real} drill_ok={drill}")
    else:
        _ok("V-VPK-ROUTING", "delete page gets VP-019, restrained onboarding gets none, "
                             "landing gets VP-022/024; serve-everything mutant went red")


def v_provenance():
    if not os.path.isfile(OBS):
        _fail("V-VPK-PROVENANCE", f"missing {OBS}")
        return
    text = _read(OBS)
    rows = set(int(n) for n in re.findall(r"^\|\s*(\d+)\s*\|", text, flags=re.M))
    markers = {
        "15 rows": rows == set(range(1, 16)),
        "license disposition": "## License disposition" in text and "Principles only" in text,
        "rejected component": "## Rejected: Advanced Model Selector" in text,
    }
    absent = [k for k, ok in markers.items() if not ok]
    if absent:
        _fail("V-VPK-PROVENANCE", f"absent: {absent} (rows={sorted(rows)})")
    else:
        _ok("V-VPK-PROVENANCE", "15 component rows, license disposition and rejection recorded")


def v_indexed():
    readme = _read(os.path.join(CORPUS, "README.md"))
    vp007 = _read(os.path.join(CORPUS, "holographic-iridescent-foil-text.md"))
    missing = [vid for vid in ENTRIES if f"| {vid} |" not in readme]
    if missing or REF not in vp007:
        _fail("V-VPK-INDEXED", f"README missing {missing}; VP-007 cites {REF}={REF in vp007}")
    else:
        _ok("V-VPK-INDEXED", f"README indexes {len(ENTRIES)} entries; VP-007 cites {REF}")


def main():
    v_entries()
    v_no_code()
    v_corpus()
    v_evidence()
    v_routing()
    v_provenance()
    v_indexed()
    total = _passes + _fails
    print(f"VPK_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
