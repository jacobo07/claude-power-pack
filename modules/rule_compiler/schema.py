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


class Binding(str, Enum):
    """WHERE a rule binds -- the consequence, not the seriousness.

    `severity` says how bad the incident was. It does not say whether the
    rule stops a build, stops a deploy, or merely advises, so a
    documentation-grade rule and a deploy blocker are indistinguishable in
    the compiled DB and the digest cannot route by consequence.

    UNDECLARED and UNRECOGNIZED are states, never levels, and neither is a
    rejection reason. 149 rules bind today and declare nothing; making the
    field required would inert the whole corpus -- the disarmed kill switch
    this package exists because of. Absence is reported, never enforced.

    They are also kept apart on purpose. Folding an unknown value into
    UNDECLARED would let a typo read as "nobody has declared this yet",
    which is the shape where an unrecognised idiom scores zero and zero
    never falls.
    """
    ADVISORY = "ADVISORY"
    WARN = "WARN"
    REQUIRE_EVIDENCE = "REQUIRE_EVIDENCE"
    BLOCK_BUILD = "BLOCK_BUILD"
    BLOCK_DEPLOY = "BLOCK_DEPLOY"
    BLOCK_RUNTIME_ACTION = "BLOCK_RUNTIME_ACTION"
    REQUIRE_HUMAN_AUTHORIZATION = "REQUIRE_HUMAN_AUTHORIZATION"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    UNDECLARED = "UNDECLARED"
    UNRECOGNIZED = "UNRECOGNIZED"


#: The declarable ladder, weakest consequence first. UNDECLARED and
#: UNRECOGNIZED are deliberately absent -- they are not levels.
BINDING_LADDER: tuple[Binding, ...] = (
    Binding.ADVISORY,
    Binding.WARN,
    Binding.REQUIRE_EVIDENCE,
    Binding.BLOCK_BUILD,
    Binding.BLOCK_DEPLOY,
    Binding.BLOCK_RUNTIME_ACTION,
    Binding.REQUIRE_HUMAN_AUTHORIZATION,
    Binding.EMERGENCY_STOP,
)
_LADDER_BY_NAME = {b.value: b for b in BINDING_LADDER}


def read_binding(raw: str) -> Binding:
    """Text -> Binding. Absent is UNDECLARED; present-but-unknown is
    UNRECOGNIZED. The corpus writes `BLOCK-DEPLOY`, `block deploy` and
    `**BLOCK_DEPLOY**`, so separators and emphasis are normalised -- but
    only those. Anything still unmatched is surfaced, not guessed."""
    text = (raw or "").strip().strip("*_`").strip()
    if not text:
        return Binding.UNDECLARED
    key = re.sub(r"[\s\-]+", "_", text).upper()
    return _LADDER_BY_NAME.get(key, Binding.UNRECOGNIZED)


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
    enforcement: str = ""
    body: str = ""
    rejections: list[Reason] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.rejections

    @property
    def binding(self) -> Binding:
        """Where this rule binds. Never participates in `valid`."""
        return read_binding(self.enforcement)

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
            "enforcement": self.enforcement,
            "binding": self.binding.value,
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


def binding_coverage(rules: list[Rule]) -> dict:
    """Which rules declare where they bind, and which do not.

    Counts and NAMED ids only -- never a percentage. A ratio of declared
    rules is satisfied by deleting undeclared ones, so it can improve
    while the corpus gets worse; a named list can only shorten because a
    rule actually declared.

    `unrecognized` is reported apart from `undeclared` because they are
    different defects with different fixes: one is a rule nobody has
    classified, the other is a rule someone classified wrongly, and only
    the second is already someone's mistake to correct.
    """
    by_binding: dict[str, list[str]] = {}
    for r in rules:
        by_binding.setdefault(r.binding.value, []).append(r.rule_id)
    for ids in by_binding.values():
        ids.sort()
    return {
        "total": len(rules),
        "declared": sorted(
            rid for b, ids in by_binding.items()
            if b in _LADDER_BY_NAME for rid in ids
        ),
        "undeclared": by_binding.get(Binding.UNDECLARED.value, []),
        "unrecognized": by_binding.get(Binding.UNRECOGNIZED.value, []),
        "by_binding": {b: len(ids) for b, ids in sorted(by_binding.items())},
    }
