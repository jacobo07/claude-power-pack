#!/usr/bin/env python
"""L1 classifier: sections.json (+ review.json overrides) -> l1/obligations.json for `gsd_dossier.py dispose`.

Deterministic. Rules in order: (1) older duplicate title -> SUPERSEDED; (2) doctrine title/lead lines -> ALREADY_SATISFIED
only when a grep probe finds the rule's phrase in an enforcing file NOW, else CHEAP_COGNITION "doctrine without an
enforcer"; (3) everything else UNKNOWN "needs review". review.json {id: {claimed, evidence?, merge_into?, ...}} wins last.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_dossier as gd  # noqa: E402

ROOT = HERE.parent
L1 = ROOT / "vault/specs/gsdx-factory/l1"
CPP = Path(r"C:\Users\User\.claude\skills\claude-power-pack")
ENFORCERS = [ROOT / "vault/plans/gsdx-factory-master-plan.md",
             CPP / "vault/knowledge_base/ukdl-universal.md",
             CPP / "vault/knowledge_base/clae/CLAE_PROCESS_RULES.md",
             CPP / "vault/knowledge_base/clae/CLAE_TRAPS.md",
             Path(r"C:\Users\User\knowledge_vault\core\HARD-RULES.md")]
DOCTRINE = re.compile(r"\b(law|rule|rules|trap|traps|kernel|principle|contract|mode|role|handoff|iteration|delegation|"
                      r"loops|concurrent writers|micro-?commits?|scope boundary)\b", re.I)
ALT = {"micro": r"micro-?commit", "concurrent": r"concurrent[\s-]+writ", "handoff": r"hand-?off",
       "trap": r"\btrap", "delegation": r"delegat", "iteration": r"iteration", "loops": r"\bloops?\b"}


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def phrase_rx(title: str) -> str:
    words = [re.escape(w) for w in norm(title).split()]
    return r"(?i)" + r"[\s\-_/]*".join(words)


def doctrine_probe(title: str):
    cands = [phrase_rx(title)]
    t = norm(title)
    for k, rx in ALT.items():
        if k in t:
            cands.append("(?i)" + rx)
    for rx in cands:
        for f in ENFORCERS:
            pr = {"kind": "grep", "path": str(f), "pattern": rx}
            if f.exists() and gd.run_probe(pr, ROOT)["ok"]:
                return [pr]
    return None


def build(sections: list, review: dict) -> dict:
    order = sorted({s for r in sections for s in r["sources"]})
    rank = {s: i for i, s in enumerate(order)}
    newest: dict = {}
    for r in sections:
        k = norm(r["title"])
        cur = newest.get(k)
        if cur is None or rank[r["sources"][0]] > rank[cur["sources"][0]]:
            newest[k] = r
    out = []
    for r in sections:
        i, k = r["id"], norm(r["title"])
        tgt = newest[k]
        lead = " ".join(r["body"].splitlines()[:3])
        if tgt["id"] != i:
            row = {"claimed": "SUPERSEDED", "superseded_by": tgt["id"], "reason": "newer prompt re-issues this title"}
        elif DOCTRINE.search(r["title"]) or DOCTRINE.search(lead):
            ev = doctrine_probe(r["title"])
            row = ({"claimed": "ALREADY_SATISFIED", "evidence": ev, "reason": "doctrine; phrase found in enforcing file"}
                   if ev else {"claimed": "CHEAP_COGNITION", "reason": "doctrine without an enforcer"})
        else:
            row = {"claimed": "UNKNOWN", "reason": "needs review"}
        row.update(id=i, block=r["sources"][0][:15], title=r["title"])
        if i in review and not (row["claimed"] == "SUPERSEDED"):
            row = {**review[i], "id": i, "block": row["block"], "title": row["title"]}
        out.append(row)
    return {"expect": [r["id"] for r in sections], "obligations": out}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sections", default=str(L1 / "sections.json"))
    ap.add_argument("--review", default=str(L1 / "review.json"))
    ap.add_argument("--out", default=str(L1 / "obligations.json"))
    a = ap.parse_args()
    secs = json.loads(Path(a.sections).read_text(encoding="utf-8-sig"))["rows"]
    rv = Path(a.review)
    review = json.loads(rv.read_text(encoding="utf-8-sig")) if rv.exists() else {}
    res = build(secs, review)
    Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    cnt: dict = {}
    for o in res["obligations"]:
        cnt[o["claimed"]] = cnt.get(o["claimed"], 0) + 1
    print("CLASSIFY", len(res["obligations"]), json.dumps(cnt, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
