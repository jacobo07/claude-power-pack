"""Which baseline entries enter the prompt, within the spec's injection ceiling.

Spec 2026-09-24 §4: at most 8 entries / 1,400 characters per family. Every
family's B0 already holds 15 entries (measured 2026-09-25), so the literal
reading -- "exceeding it is a compiler failure" -- would leave S4 unable to
inject for any family at all, and a silent top-8 would make seven
constitutive rules invisible. This compiler takes the third path:

  * the ceiling bounds what is SHOWN, never what is CONSTITUTIVE. The
    done-gate judges every applicable entry, injected or not;
  * selection is deterministic and explainable: entries whose check can be
    evaluated first (a rule the gate can verify is worth the prompt space),
    then delegated checks, then prose/empty; reviewed before auto-promoted;
    ties keep the generation's own order;
  * nothing is lost: injected + deferred == input, and every deferred entry
    carries its reason. `overflow` is True whenever anything was deferred.

`class` (C|D) is deliberately NOT a ranking key: the spec does not define it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import checks as ck

MAX_ENTRIES = 8
MAX_CHARS = 1400


@dataclass
class Selection:
    injected: list = field(default_factory=list)
    deferred: list = field(default_factory=list)
    reasons: dict = field(default_factory=dict)

    @property
    def overflow(self) -> bool:
        return bool(self.deferred)

    def as_dict(self) -> dict:
        return {"injected": [e.get("id") for e in self.injected],
                "deferred": [e.get("id") for e in self.deferred],
                "reasons": dict(self.reasons), "overflow": self.overflow}


def _rank(entry: dict) -> tuple:
    kind, _arg = ck.parse(entry.get("check") or "")
    runnable = 0 if kind in ck.STATIC_KINDS else 1 if kind in ck.DELEGATED_KINDS else 2
    reviewed = 0 if entry.get("status", "reviewed") == "reviewed" else 1
    return (runnable, reviewed)


def select_for_injection(entries: list, max_entries: int = MAX_ENTRIES,
                         max_chars: int = MAX_CHARS) -> Selection:
    order = sorted(range(len(entries)), key=lambda i: (_rank(entries[i]), i))
    out = Selection()
    used = 0
    for i in order:
        e = entries[i]
        size = len(e.get("requirement") or "")
        if size > max_chars:
            out.deferred.append(e)
            out.reasons[e.get("id")] = ("longer (%d chars) than the whole budget of %d"
                                        % (size, max_chars))
        elif len(out.injected) >= max_entries:
            out.deferred.append(e)
            out.reasons[e.get("id")] = "entry ceiling of %d reached" % max_entries
        elif used + size > max_chars:
            out.deferred.append(e)
            out.reasons[e.get("id")] = ("character budget: %d used, %d needed, %d allowed"
                                        % (used, size, max_chars))
        else:
            out.injected.append(e)
            used += size
    return out
