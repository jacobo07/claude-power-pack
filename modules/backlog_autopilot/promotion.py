"""Constitutive Promotion Gate (campaign 1, law 5) -- classify a delta, promote only through the tower owner.

EXTENDS modules.tower (baselines / ratchet / donegate); it adds no baseline store, no second ledger. A delta found
while building a web surface is classified INCIDENTAL, PRODUCT_SPECIFIC, ARCHETYPE_ENHANCING or CONSTITUTIVE.
Only the last two may be promoted, and only when ALL of these hold (each is a named refusal otherwise):

  * not a duplicate of an active entry of the family (token overlap or an identical check);
  * not enforced by another owner at another time (`enforced_elsewhere`);
  * not tied to one product, brand or harness (`product_tokens`, `applies_to_all_members`);
  * its check is STATIC (file / glob / regex): a done-gate over prose judges nothing;
  * the evidence passes modules.tower.ratchet.evidence_problems (a measured before != after on a named run, negative
    controls that really failed, a later different run that reused it).

CAVEAT (stated, not hidden): the attributes of a Delta (applies_to_all_members, floor, enforced_elsewhere) are
DECLARED by the proposer; the gate checks their consistency and the objective facts (duplicate, check kind,
evidence), not the declarations' truth. A mislabelled delta is caught only by the inheritance proof.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from modules.tower import baselines as bl
from modules.tower import checks as ck
from modules.tower import ratchet as rt

INCIDENTAL = "INCIDENTAL"
PRODUCT_SPECIFIC = "PRODUCT_SPECIFIC"
ARCHETYPE_ENHANCING = "ARCHETYPE_ENHANCING"
CONSTITUTIVE = "CONSTITUTIVE"
CLASSES = (INCIDENTAL, PRODUCT_SPECIFIC, ARCHETYPE_ENHANCING, CONSTITUTIVE)
PROMOTABLE = (ARCHETYPE_ENHANCING, CONSTITUTIVE)
DUP_JACCARD = 0.5


@dataclass
class Delta:
    id: str
    requirement: str
    why: str
    check: str = ""
    origin: dict = field(default_factory=dict)      # {file, line, quote}
    applies_to_all_members: bool = True
    floor: bool = False                              # absence is a legal / safety / accessibility floor breach
    enforced_elsewhere: str = ""                     # owner that already enforces it (name), else ""
    product_tokens: list = field(default_factory=list)


@dataclass
class Verdict:
    id: str
    klass: str
    reason: str
    duplicate_of: str = ""

    @property
    def promotable(self) -> bool:
        return self.klass in PROMOTABLE

    def as_dict(self) -> dict:
        return {"id": self.id, "class": self.klass, "reason": self.reason,
                "duplicate_of": self.duplicate_of, "promotable": self.promotable}


def _tok(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{4,}", (s or "").lower())}


def _squash(s: str) -> str:
    return " ".join(str(s or "").split())


def duplicate_of(d: Delta, active: list) -> str:
    """Id of the active entry this delta repeats (identical non-empty check, or heavy vocabulary overlap), else ''."""
    mine = _tok(d.requirement)
    for e in active:
        if d.check and _squash(d.check) == _squash(e.get("check")):
            return str(e.get("id"))
        theirs = _tok(e.get("requirement"))
        if mine and theirs and len(mine & theirs) / len(mine | theirs) >= DUP_JACCARD:
            return str(e.get("id"))
    return ""


def classify(d: Delta, active: list) -> Verdict:
    dup = duplicate_of(d, active)
    if dup:
        return Verdict(d.id, INCIDENTAL, "repeats active entry %s; promoting it adds no rule" % dup, dup)
    if d.enforced_elsewhere.strip():
        return Verdict(d.id, INCIDENTAL, "already enforced by %s, at the time and place it applies" % d.enforced_elsewhere)
    text = (d.requirement + " " + d.check).lower()
    hit = [t for t in d.product_tokens if t and t.lower() in text]
    if hit:
        return Verdict(d.id, PRODUCT_SPECIFIC, "tied to one product/harness: %s" % ", ".join(hit))
    if not d.applies_to_all_members:
        return Verdict(d.id, PRODUCT_SPECIFIC, "not every member of the family needs it")
    return Verdict(d.id, CONSTITUTIVE if d.floor else ARCHETYPE_ENHANCING,
                   "applies to every member of the family" + ("; its absence breaches a floor" if d.floor else ""))


def check_problem(d: Delta) -> str:
    kind, _ = ck.parse(d.check)
    if kind not in ck.STATIC_KINDS:
        return "check must be static (file/glob/regex); got %s" % kind
    return ""


@dataclass
class Outcome:
    verdicts: list = field(default_factory=list)
    refused: dict = field(default_factory=dict)      # id -> reason
    generation: str = ""

    @property
    def promoted(self) -> list:
        return [v.id for v in self.verdicts if v.id not in self.refused]

    def as_dict(self) -> dict:
        return {"verdicts": [v.as_dict() for v in self.verdicts], "refused": dict(self.refused),
                "promoted": self.promoted, "generation": self.generation}


def promote(family: str, deltas: list, evidence: dict, authority: str, reason: str,
            root: str | None = None) -> Outcome:
    """Classify every delta, refuse by name, and write ONE generation for the survivors via the tower owner.

    Nothing is written when no delta survives. A promotion the tower ratchet refuses (evidence) refuses ALL
    survivors with the owner's message: a half-evidenced batch is not a baseline."""
    active = bl.active_entries(family, root)
    out = Outcome()
    keep = []
    for d in deltas:
        v = classify(d, active)
        out.verdicts.append(v)
        if not v.promotable:
            out.refused[d.id] = "%s: %s" % (v.klass, v.reason)
            continue
        prob = check_problem(d)
        if prob:
            out.refused[d.id] = "UNCHECKABLE: " + prob
            continue
        keep.append(d)
    if not keep:
        return out
    entries = [{"id": d.id, "requirement": d.requirement, "why": d.why, "origin": d.origin,
                "class": "C", "check": d.check, "status": "auto"} for d in keep]
    try:
        path = rt.promote_with_evidence(family, entries, reason, authority, evidence, root)
    except rt.RatchetRefusal as exc:
        for d in keep:
            out.refused[d.id] = "EVIDENCE: %s" % exc
        return out
    out.generation = path
    return out


def load_deltas(path: str) -> list:
    import json
    with open(path, "r", encoding="utf-8") as fh:
        return [Delta(**{k: v for k, v in row.items() if k in Delta.__dataclass_fields__}) for row in json.load(fh)]


def main(argv=None) -> int:
    """python3 -m modules.backlog_autopilot.promotion <family> --deltas F --evidence F --authority A --reason R [--root R]
    exit 0 something promoted, 1 nothing promoted (every refusal printed by name)."""
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="promotion")
    ap.add_argument("family")
    ap.add_argument("--deltas", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--authority", required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--root")
    a = ap.parse_args(argv)
    with open(a.evidence, "r", encoding="utf-8") as fh:
        ev = json.load(fh)
    out = promote(a.family, load_deltas(a.deltas), ev, a.authority, a.reason, a.root)
    print(json.dumps(out.as_dict(), indent=1))
    return 0 if out.generation else 1


if __name__ == "__main__":
    raise SystemExit(main())
