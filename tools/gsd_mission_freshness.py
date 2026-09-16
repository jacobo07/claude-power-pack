#!/usr/bin/env python
"""gsd_mission_freshness — refuse to arm an autonomous run against a stale mission.

An autonomous executor can be mechanically sound and still execute the wrong thing: the
durable roadmap it obeys may describe a mission the Owner has since superseded. Measured
2026-09-16 (KobiiSports Resort): `.planning` was syntactically valid, `status: in_progress`,
`auto_advance: true` -- and held zero occurrences of `gameSelect`, `seam`, `Page 2` or `FIX-2`,
the campaign actually approved. Its Phase 2 recorded as *done* the very renderer that campaign
schedules for retirement. A runner obeying it would have extended the architecture being
replaced. Nothing about the run would have looked wrong.

So arming needs a mission declaration, and the active planning vocabulary must contain a
MAJORITY of it. "Any intersection" was the first rule and it failed on the real subject: the
stale roadmap shared one generic word ("slot") with the new mission. The check is on the ACTIVE
milestone's own files (`.planning/STATE.md` + `.planning/ROADMAP.md`), never archived history.
Declare distinctive terms; generic nouns weaken the check.

Four outcomes -- a gate that could not judge must not read as one that passed:
    FRESH        a majority of declared terms appear in the active planning vocabulary
    STALE        fewer do                                         -> refuse
    UNDECLARED   no mission terms were supplied                   -> refuse
    UNREADABLE   STATE.md / ROADMAP.md missing or unreadable      -> refuse

Matching is on normalised tokens, not substrings: `Page 2`, `page-2` and `page2` all match the
term `page2`, and camelCase `gameSelect` matches `gameselect`, but `seam` does not match
`seamless`. Adjacent-token joins are included so a two-word term written with a space still
matches.

CLI:
    python tools/gsd_mission_freshness.py --project . --mission "page2,gameselect,seam"
Exit 0 only on FRESH; 2 otherwise. Prints one JSON verdict line.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

FRESH, STALE, UNDECLARED, UNREADABLE = "FRESH", "STALE", "UNDECLARED", "UNREADABLE"

_TOKEN = re.compile(r"[a-z0-9]+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass
class Verdict:
    outcome: str
    mission_terms: list = field(default_factory=list)
    matched: list = field(default_factory=list)
    active_milestone: str = ""
    sources: list = field(default_factory=list)
    reason: str = ""

    @property
    def armable(self) -> bool:
        return self.outcome == FRESH


def normalise_term(term: str) -> str:
    return _NON_ALNUM.sub("", (term or "").lower())


def parse_terms(raw) -> list:
    if raw is None:
        return []
    items = raw.split(",") if isinstance(raw, str) else list(raw)
    seen, out = set(), []
    for item in items:
        t = normalise_term(str(item))
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def vocabulary(text: str) -> set:
    """Unigrams plus adjacent-token joins of the lower-cased text."""
    toks = _TOKEN.findall((text or "").lower())
    vocab = set(toks)
    vocab.update(a + b for a, b in zip(toks, toks[1:]))
    return vocab


def _frontmatter_value(text: str, key: str) -> str:
    m = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return m.group(1).strip().strip("'\"") if m else ""


def check(project_dir, mission_terms) -> Verdict:
    terms = parse_terms(mission_terms)
    if not terms:
        return Verdict(UNDECLARED, reason="no mission terms declared; an undeclared mission "
                                          "cannot be shown to match the roadmap")
    planning = Path(project_dir) / ".planning"
    sources = [planning / "STATE.md", planning / "ROADMAP.md"]
    texts = []
    for src in sources:
        try:
            texts.append(src.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError) as exc:
            return Verdict(UNREADABLE, mission_terms=terms,
                           sources=[str(s) for s in sources],
                           reason=f"cannot read {src.name}: {exc.__class__.__name__}: {exc}")
    state_text = texts[0]
    milestone = " ".join(v for v in (_frontmatter_value(state_text, "milestone"),
                                     _frontmatter_value(state_text, "milestone_name")) if v)
    vocab = vocabulary("\n".join(texts))
    matched = [t for t in terms if t in vocab]
    base = dict(mission_terms=terms, matched=matched, active_milestone=milestone,
                sources=[str(s) for s in sources])
    # A MAJORITY of the declared terms, not "any". Measured on the real subject that motivated
    # this gate: a stale v2.0 roadmap matched 1 of 5 Page-2 terms -- the generic word "slot" --
    # and "any intersection" called it FRESH. One shared common noun is not a shared mission.
    needed = len(terms) // 2 + 1
    if len(matched) >= needed:
        return Verdict(FRESH, reason=f"{len(matched)}/{len(terms)} mission terms present in the "
                                     f"active planning files (need {needed})", **base)
    return Verdict(STALE, reason=f"only {len(matched)}/{len(terms)} mission terms appear in the "
                                 f"active milestone '{milestone or '?'}' (need {needed}) -- it "
                                 f"describes a different mission; seed or switch the milestone "
                                 f"before arming", **base)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="GSD mission-freshness gate")
    ap.add_argument("--project", default=".")
    ap.add_argument("--mission", default="", help="comma-separated mission vocabulary")
    args = ap.parse_args(argv)
    try:
        verdict = check(args.project, args.mission)
    except Exception as exc:  # the gate itself failed: never a pass
        verdict = Verdict(UNREADABLE, reason=f"gate error: {exc.__class__.__name__}: {exc}")
    out = asdict(verdict)
    out["armable"] = verdict.armable
    sys.stdout.write(json.dumps(out) + "\n")
    return 0 if verdict.armable else 2


if __name__ == "__main__":
    sys.exit(main())
