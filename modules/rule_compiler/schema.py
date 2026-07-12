"""Hard-rule schema + the validation gate.

A hard rule is a machine artifact, not prose. It is admitted to the
active archive only if it can actually stop the agent at a trigger
point. This module decides that, per rule, per field, with a named
reason for every rejection.

Three forms are recognised (form is decided BEFORE content is judged --
rejecting a well-written rule for wearing the wrong shape is the bug
this file exists to avoid):

  FIELDED     TRIGGER: / ACCION:|STOP: / ORIGEN:|EVIDENCE:  -- the
              generated form used by the global corpus and the PP
              archive.
  IMPERATIVE  '### HR-N -- Never <X> without <Y>' + prose body. The
              title fuses trigger and action; the body carries the
              verification ritual. Hand-written, and the strongest
              rules in the corpus.
  UNKNOWN     neither -- there is nothing here that can fire. Rejected.

Sealed by the AKOS macro audit (2026-07-12): 5 of 9 active PP rules
were heading-scrapes, including HR-002, whose TRIGGER was 'Test
recognizer for pipeline' and whose EVIDENCE was a literal ZZZ smoke
fixture -- sealed at SEVERITY: CRITICAL.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

MIN_TRIGGER_CHARS = 20
MIN_STOP_CHARS = 12

# A trigger that is really a document heading the generator scraped.
_DOC_MARKERS = (
    "ukdl", "never_again", "session_lessons", "osa absorption",
    "iteration log", "delivery_report", "sprint", "handoff",
)
# A smoke-test fixture that was sealed as a production kill switch.
_SMOKE_MARKERS = ("zzz", "test recognizer", "test critical bug", "foobar")
# ISO-ish date or timestamp carrying no condition.
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# An imperative rule's title carries a normative operator -- somewhere,
# not necessarily at the front. The corpus writes them mid-sentence:
# 'the SGE never fabricates data the operator did not provide'. Anchoring
# to the start would mass-reject the best hand-written rules on grammar.
_NORMATIVE_RE = re.compile(
    r"\b(never|always|must|only|cannot|can't|do not|don't|forbidden|"
    r"prohibited|required|refuse|no\b|not\b|before|stop)\b",
    re.I,
)
# A markdown table row/separator masquerading as an action.
_TABLE_RE = re.compile(r"^\s*\|")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}")


class Form(str, Enum):
    FIELDED = "FIELDED"
    IMPERATIVE = "IMPERATIVE"
    UNKNOWN = "UNKNOWN"


class Reason(str, Enum):
    """Every rejection names one of these. No unexplained rejects."""
    NO_ENFORCEABLE_FORM = "no_enforceable_form"
    TRIGGER_MISSING = "trigger_missing"
    TRIGGER_IS_HEADING_SCRAPE = "trigger_is_heading_scrape"
    TRIGGER_IS_SMOKE_FIXTURE = "trigger_is_smoke_fixture"
    TRIGGER_IS_DATE = "trigger_is_date"
    TRIGGER_TOO_SHORT = "trigger_too_short"
    STOP_MISSING = "stop_missing"
    STOP_IS_TABLE_FRAGMENT = "stop_is_table_fragment"
    STOP_IS_BOILERPLATE = "stop_is_boilerplate"
    STOP_TOO_SHORT = "stop_too_short"
    EVIDENCE_MISSING = "evidence_missing"
    EVIDENCE_IS_SMOKE_FIXTURE = "evidence_is_smoke_fixture"


REASON_HELP: dict[Reason, str] = {
    Reason.NO_ENFORCEABLE_FORM:
        "neither a TRIGGER/ACTION block nor an imperative title -- "
        "nothing here can fire at a trigger point",
    Reason.TRIGGER_MISSING: "no TRIGGER field",
    Reason.TRIGGER_IS_HEADING_SCRAPE:
        "TRIGGER is a document heading the generator scraped "
        "(a doc title is not an observable condition)",
    Reason.TRIGGER_IS_SMOKE_FIXTURE:
        "TRIGGER is a smoke-test fixture, not a production condition",
    Reason.TRIGGER_IS_DATE:
        "TRIGGER is a date/timestamp -- it names when someone wrote "
        "something, not when the agent must stop",
    Reason.TRIGGER_TOO_SHORT:
        f"TRIGGER under {MIN_TRIGGER_CHARS} chars -- too vague to match",
    Reason.STOP_MISSING: "no ACCION/STOP field",
    Reason.STOP_IS_TABLE_FRAGMENT:
        "ACCION/STOP is a markdown table fragment, not an imperative "
        "action -- the generator captured the wrong lines",
    Reason.STOP_IS_BOILERPLATE:
        "ACCION/STOP is generator boilerplate shared verbatim with "
        "another rule -- it prescribes nothing rule-specific",
    Reason.STOP_TOO_SHORT:
        f"ACCION/STOP under {MIN_STOP_CHARS} chars",
    Reason.EVIDENCE_MISSING: "no ORIGEN/EVIDENCE field -- cites no incident",
    Reason.EVIDENCE_IS_SMOKE_FIXTURE:
        "EVIDENCE cites a smoke-test fixture, not a real incident",
}


@dataclass
class Rule:
    rule_id: str
    title: str
    form: Form
    source: str
    trigger: str = ""
    stop: str = ""
    evidence: str = ""
    exception: str = ""
    severity: str = ""
    body: str = ""
    rejections: list[Reason] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.rejections

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "form": self.form.value,
            "source": self.source,
            "trigger": self.trigger,
            "stop": self.stop,
            "evidence": self.evidence,
            "exception": self.exception,
            "severity": self.severity,
            "valid": self.valid,
            "rejections": [r.value for r in self.rejections],
        }


def _has(markers: tuple[str, ...], text: str) -> bool:
    low = text.lower()
    return any(m in low for m in markers)


def _first_line(text: str) -> str:
    for ln in text.splitlines():
        if ln.strip():
            return ln.strip()
    return ""


def validate(rule: Rule, boilerplate_stops: frozenset[str]) -> Rule:
    """Stamp rule.rejections. Returns the same rule for chaining.

    `boilerplate_stops` is computed corpus-wide: any ACCION/STOP text
    that appears verbatim on two or more distinct rules is template
    filler by definition -- a real action is rule-specific. This is a
    measured signal, not a hardcoded blacklist.
    """
    rule.rejections = []

    if rule.form is Form.UNKNOWN:
        rule.rejections.append(Reason.NO_ENFORCEABLE_FORM)
        return rule

    if rule.form is Form.IMPERATIVE:
        # The title IS the condition and the action. It must still be
        # normative, and it must carry a body that says how to comply.
        if not _NORMATIVE_RE.search(rule.title):
            rule.rejections.append(Reason.NO_ENFORCEABLE_FORM)
        if len(rule.body.strip()) < MIN_STOP_CHARS:
            rule.rejections.append(Reason.STOP_TOO_SHORT)
        if _has(_SMOKE_MARKERS, rule.title):
            rule.rejections.append(Reason.TRIGGER_IS_SMOKE_FIXTURE)
        return rule

    # --- FIELDED -----------------------------------------------------
    trig = rule.trigger.strip()
    if not trig:
        rule.rejections.append(Reason.TRIGGER_MISSING)
    elif _has(_SMOKE_MARKERS, trig):
        rule.rejections.append(Reason.TRIGGER_IS_SMOKE_FIXTURE)
    else:
        # 'Before: <doc title>' -- the generator's signature defect.
        scraped = trig.lower().startswith("before:")
        if scraped and (_has(_DOC_MARKERS, trig) or _DATE_RE.search(trig)):
            rule.rejections.append(Reason.TRIGGER_IS_HEADING_SCRAPE)
        elif _DATE_RE.search(trig) and len(_DATE_RE.sub("", trig).strip()) < 15:
            rule.rejections.append(Reason.TRIGGER_IS_DATE)
        elif len(trig) < MIN_TRIGGER_CHARS:
            rule.rejections.append(Reason.TRIGGER_TOO_SHORT)

    stop = rule.stop.strip()
    head = _first_line(stop)
    if not stop:
        rule.rejections.append(Reason.STOP_MISSING)
    elif _TABLE_RE.match(head) or _TABLE_SEP_RE.match(head) or head == "|":
        rule.rejections.append(Reason.STOP_IS_TABLE_FRAGMENT)
    elif stop in boilerplate_stops:
        rule.rejections.append(Reason.STOP_IS_BOILERPLATE)
    elif len(stop) < MIN_STOP_CHARS:
        rule.rejections.append(Reason.STOP_TOO_SHORT)

    ev = rule.evidence.strip()
    if not ev:
        rule.rejections.append(Reason.EVIDENCE_MISSING)
    elif _has(_SMOKE_MARKERS, ev):
        rule.rejections.append(Reason.EVIDENCE_IS_SMOKE_FIXTURE)

    return rule


def find_boilerplate_stops(rules: list[Rule]) -> frozenset[str]:
    """ACCION/STOP text shared verbatim by >=2 rules is filler."""
    seen: dict[str, int] = {}
    for r in rules:
        s = r.stop.strip()
        if s:
            seen[s] = seen.get(s, 0) + 1
    return frozenset(s for s, n in seen.items() if n >= 2)
