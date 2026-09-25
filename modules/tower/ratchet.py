"""Anti-downgrade for constitutive baselines: changing a rule is allowed only on the record.

Generations are immutable, but a new generation may say anything, so without
this module "make the gate pass" is one raw `write_generation` away. Same idea
as `modules/intent_verified/ratchet.py`: standing debt is a named set, and a
change to it must be named.

Between two consecutive generations, a change to an entry that was ACTIVE in
the parent is a regression unless the child's `changes[<id>]` records it with a
non-empty `reason` and `authority`:

  WITHDRAWN      the entry is gone
  REVERTED       its status became `reverted`
  WEAKENED       its check dropped a rung: evaluable -> delegated -> prose/empty
  CHECK_CHANGED  its check string changed at the same or a higher rung
  REWORDED       its requirement text changed

CHECK_CHANGED exists because a rung is a KIND, not a strength: swapping
`regex:gate.py::must_refuse_stale` for `regex:gate.py::.` stays at rung 0 and
passes on any file (code review 2026-09-25, HIGH). The same holds for "raising"
prose to `glob:**` -- a new green nobody earned. So every change to a check,
upward included, carries a reason and an authority; only ADDING an entry is
free. A generation holding two entries with one id is DUPLICATE_ID: the dicts
below would silently keep one and hide a withdrawal of the other.

Each child anchors its parent's exact bytes (`parent_sha256`), so an older
generation edited after the fact reads TAMPERED at the child. The newest
generation has no child to anchor it; its integrity is the repo's history.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from . import baselines as bl
from . import checks as ck

WITHDRAWN = "WITHDRAWN"
REVERTED = "REVERTED"
WEAKENED = "WEAKENED"
CHECK_CHANGED = "CHECK_CHANGED"
REWORDED = "REWORDED"
DUPLICATE_ID = "DUPLICATE_ID"


class RatchetRefusal(ValueError):
    """A promote/revert that cannot be justified; nothing was written."""


def check_rung(check: str) -> int:
    """0 = evaluable, 1 = delegated, 2 = prose or empty. Lower is stronger."""
    kind, _arg = ck.parse(check or "")
    if kind in ck.STATIC_KINDS:
        return 0
    if kind in ck.DELEGATED_KINDS:
        return 1
    return 2


def _squash(s) -> str:
    return " ".join(str(s or "").split())


def duplicate_ids(entries: list) -> list:
    return sorted(i for i, n in Counter(e.get("id") for e in entries).items() if n > 1)


def _active(entries: list) -> dict:
    return {e["id"]: e for e in entries if e.get("status") != "reverted"}


def diff(parent: dict, child: dict) -> list:
    """[(id, kind)] for every change to a parent-active entry in the child."""
    before = _active(parent.get("entries", []))
    after = {e["id"]: e for e in child.get("entries", [])}
    out = []
    for ident, old in before.items():
        new = after.get(ident)
        if new is None:
            out.append((ident, WITHDRAWN))
            continue
        if new.get("status") == "reverted":
            out.append((ident, REVERTED))
            continue
        if check_rung(new.get("check")) > check_rung(old.get("check")):
            out.append((ident, WEAKENED))
        elif _squash(new.get("check")) != _squash(old.get("check")):
            out.append((ident, CHECK_CHANGED))
        if _squash(new.get("requirement")) != _squash(old.get("requirement")):
            out.append((ident, REWORDED))
    return out


def _recorded(child: dict, ident: str, kind: str) -> bool:
    rec = (child.get("changes") or {}).get(ident) or {}
    kinds = rec.get("kind")
    kinds = kinds if isinstance(kinds, list) else [kinds]
    return (kind in kinds and str(rec.get("reason") or "").strip() != ""
            and str(rec.get("authority") or "").strip() != "")


@dataclass
class ChainReport:
    family: str
    generations: list = field(default_factory=list)
    regressions: list = field(default_factory=list)   # {generation, id, kind}
    tampered: list = field(default_factory=list)      # child generations
    unanchored: list = field(default_factory=list)    # children with no parent hash

    @property
    def ok(self) -> bool:
        return not self.regressions and not self.tampered

    def as_dict(self) -> dict:
        return {"family": self.family, "generations": self.generations,
                "regressions": self.regressions, "tampered": self.tampered,
                "unanchored": self.unanchored, "ok": self.ok}


def verify_chain(family: str, root: str | None = None) -> ChainReport:
    rep = ChainReport(family, bl.generations(family, root))
    docs = {n: bl.load_generation(family, n, root) for n in rep.generations}
    for n, doc in docs.items():
        for ident in duplicate_ids(doc.get("entries", [])):
            rep.regressions.append({"generation": n, "id": ident, "kind": DUPLICATE_ID})
    for prev, cur in zip(rep.generations, rep.generations[1:]):
        parent, child = docs[prev], docs[cur]
        anchor = child.get("parent_sha256")
        if not anchor:
            rep.unanchored.append(cur)
        elif anchor != bl.generation_sha256(family, prev, root):
            rep.tampered.append(cur)
        for ident, kind in diff(parent, child):
            if not _recorded(child, ident, kind):
                rep.regressions.append({"generation": cur, "id": ident, "kind": kind})
    return rep


def _need(reason: str, authority: str) -> None:
    if not str(reason or "").strip():
        raise RatchetRefusal("a reason is required")
    if not str(authority or "").strip():
        raise RatchetRefusal("an authority is required")


def revert(family: str, entry_id: str, reason: str, authority: str,
           root: str | None = None) -> str:
    """Write B<n+1> with `entry_id` reverted and the change on the record."""
    _need(reason, authority)
    cur = bl.latest(family, root)
    if not cur:
        raise RatchetRefusal("%s has no generation to revert from" % family)
    if entry_id not in _active(cur["entries"]):
        raise RatchetRefusal("%s is not an active entry of %s B%d"
                             % (entry_id, family, cur["generation"]))
    entries = [dict(e, status="reverted") if e["id"] == entry_id else e
               for e in cur["entries"]]
    return bl.write_generation(
        family, entries, "revert %s: %s" % (entry_id, reason), root=root,
        extra={"changes": {entry_id: {"kind": REVERTED, "reason": reason,
                                      "authority": authority}}})


def promote(family: str, new_entries: list, reason: str, authority: str,
            root: str | None = None) -> str:
    """Write B<n+1> = current entries + `new_entries` (status default `auto`)."""
    _need(reason, authority)
    cur = bl.latest(family, root)
    existing = {e["id"] for e in (cur or {}).get("entries", [])}
    added = []
    for e in new_entries:
        missing = [k for k in bl.REQUIRED if k not in e]
        if missing:
            raise RatchetRefusal("entry %s lacks %s" % (e.get("id", "?"), missing))
        if e["id"] in existing or e["id"] in {a["id"] for a in added}:
            raise RatchetRefusal("entry id %s already exists" % e["id"])
        added.append(dict({"status": "auto", "check": ""}, **e))
    if not added:
        raise RatchetRefusal("nothing to promote")
    return bl.write_generation(
        family, list((cur or {}).get("entries", [])) + added,
        "promote %s: %s" % (", ".join(a["id"] for a in added), reason), root=root,
        extra={"promoted_by": authority})
