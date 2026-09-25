#!/usr/bin/env python3
"""Derived obligations: requirements the human did not state that follow from
the intent plus the project's own reality.

A derived obligation is not an idea, a nice-to-have or a generic best practice.
It is a requirement whose OMISSION HAS A NAMED CONSEQUENCE, traceable to the
facts and the rule that made it material. If it cannot name the consequence it
is a wish, and it is refused at intake -- the same bar DAIF applies to a stated
obligation, reached from the opposite direction.

VOCABULARY IS REUSED, NOT REINVENTED. `closure_condition`, `done_gate`, `owner`,
`authority` and `evidence` are DAIF's field names with DAIF's meanings
(modules/daif/obligation_extractor.py). DAIF is not the owner of this
population: it extracts obligations someone STATED, requiring a commitment
frame and refusing wishes, so every obligation here -- defined by never having
been stated -- would be discarded by its intake. Same noun, inverted predicate.
What transfers is the shape, and the discipline that a candidate naming no
closure condition is not an obligation.

CANDIDATE IS NOT AUTHORITY. Derivation proposes; the materiality gate
dispositions. Nothing reaches ACCEPTED because a rule fired -- it reaches
ACCEPTED because a rule fired AND a consequence was named AND the evidence for
applicability was found in the project's own reality. One hallucinated
consequence must not become code.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- dispositions ----------------------------------------------------------
# Derived once does not mean true forever, so SATISFIED and STALE are both
# reachable and STALE is reachable FROM satisfied.
CANDIDATE = "CANDIDATE"          # derived, not yet judged
ACCEPTED = "ACCEPTED"            # material and applicable: real work
NOT_APPLICABLE = "NOT_APPLICABLE"  # the rule fired, the reality does not support it
REJECTED = "REJECTED"            # material somewhere, not here, with a reason
DEFERRED = "DEFERRED"            # real and out of this mission's scope
SATISFIED = "SATISFIED"          # proof observed by the done gate
STALE = "STALE"                  # a causal parent no longer holds

OPEN_DISPOSITIONS = frozenset({CANDIDATE, ACCEPTED, STALE})
CLOSED_DISPOSITIONS = frozenset({NOT_APPLICABLE, REJECTED, DEFERRED, SATISFIED})


@dataclass
class Obligation:
    identifier: str
    text: str
    operator: str                          # which rule produced it
    parents: list[str]                     # the facts/intent it follows FROM
    consequence: str                       # what omitting it costs -- required
    evidence: list[str] = field(default_factory=list)   # why it applies HERE
    owner: str = "unassigned"
    authority: str = "derived"
    closure_condition: str = ""            # DAIF 2.7: without this it is a wish
    done_gate: str = ""
    proof: str = ""
    invalidated_by: list[str] = field(default_factory=list)
    disposition: str = CANDIDATE
    disposition_reason: str = ""
    revisit_when: str = ""

    @property
    def is_accepted(self) -> bool:
        return self.disposition == ACCEPTED

    @property
    def is_open(self) -> bool:
        return self.disposition in OPEN_DISPOSITIONS

    def to_dict(self) -> dict:
        return {
            "id": self.identifier, "text": self.text, "operator": self.operator,
            "parents": list(self.parents), "consequence": self.consequence,
            "evidence": list(self.evidence), "owner": self.owner,
            "authority": self.authority,
            "closure_condition": self.closure_condition, "done_gate": self.done_gate,
            "proof": self.proof, "invalidated_by": list(self.invalidated_by),
            "disposition": self.disposition,
            "disposition_reason": self.disposition_reason,
            "revisit_when": self.revisit_when,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Obligation":
        return cls(
            identifier=d["id"], text=d["text"], operator=d["operator"],
            parents=list(d.get("parents") or []), consequence=d.get("consequence", ""),
            evidence=list(d.get("evidence") or []), owner=d.get("owner", "unassigned"),
            authority=d.get("authority", "derived"),
            closure_condition=d.get("closure_condition", ""),
            done_gate=d.get("done_gate", ""), proof=d.get("proof", ""),
            invalidated_by=list(d.get("invalidated_by") or []),
            disposition=d.get("disposition", CANDIDATE),
            disposition_reason=d.get("disposition_reason", ""),
            revisit_when=d.get("revisit_when", ""),
        )


# --- facts ------------------------------------------------------------------
# A rule fires on FACTS, never on the fixture. Each extractor is a named,
# deterministic predicate over the intent and the project's own description, and
# each records the span it matched so a human can check the extraction rather
# than trust it.
#
# HONEST BOUNDARY. Reading project reality out of prose is the weakest link in
# this whole path and it is fixture-shaped: a real mission's reality is a
# codebase, an infrastructure description and a runbook, not one README. The
# rules below are general over FACTS; the fact extraction is not general over
# SOURCES. That limitation is the first thing the next wave should attack, and
# it is recorded rather than hidden behind a passing benchmark.

# --- how a fact is known ----------------------------------------------------
# ONE owner for this vocabulary, and it lives here because `Fact` lives here.
# tools/gsd_x_fact_producer.py imported to define its own OBSERVED/DERIVED/
# DECLARED/UNKNOWN; two spellings of one vocabulary is the second truth this
# wave exists to remove, and it would be absurd to leave it in the same wave
# that makes freshness single-owner.
#
# EXTRACTED is deliberately NOT DECLARED. A fact mined out of prose by the regex
# adapter was not declared by anybody. Stamping it DECLARED would give every
# prose fact a provenance it does not have -- the same class of untruth this
# module exists to refuse, committed by its own default value.
OBSERVED = "OBSERVED"      # measured directly from an authoritative source
DERIVED = "DERIVED"        # computed deterministically from authoritative evidence
DECLARED = "DECLARED"      # a human asserted it; nothing mechanical established it
EXTRACTED = "EXTRACTED"    # mined out of prose by the regex adapter
UNKNOWN = "UNKNOWN"        # the evidence to decide does not exist

FACT_STATES = frozenset({OBSERVED, DERIVED, DECLARED, EXTRACTED, UNKNOWN})


@dataclass(frozen=True)
class Fact:
    name: str
    matched: str
    source: str
    # Defaulted so every existing construction keeps working unchanged. `Fact`
    # is frozen but is never hashed, sorted, compared or serialized outside
    # dump(), so a trailing defaulted field breaks no contract.
    #
    # The default is DECLARED rather than EXTRACTED: the prose extractor passes
    # EXTRACTED explicitly, so a caller that reaches this default asserted a
    # fact without saying how it knows -- which is exactly what DECLARED means.
    state: str = DECLARED


# GENERALISED 2026-09-20 after the transfer control caught them fitted. The
# first version of these patterns encoded the FIXTURE'S PHRASING rather than the
# fact: the destructive object had to be spelled "local|copy|file|original|
# source", so "drops the staging rows" did not match; and the frequency digit
# had to follow the word "outages", because the fixture happened to say "3 to 12
# short outages per week, most under 90 seconds" while an unseen domain said
# "2 to 5 outages per week". Both operators then failed to transfer, which is
# what a lookup table wearing a rule's name looks like from outside.
#
# The patterns below express the FACT and not a sentence. Two consequences worth
# stating: `transfer_then_destroy` is now structural (a transfer verb followed
# by a destructive verb) rather than lexical, and frequency may appear on either
# side of the failure noun.
# A CLOSED VOCABULARY, and that is the honest name for it. Domain 2 of the
# transfer control needed "drop ... rows"; domain 3 needed "publish". Each new
# wording has cost exactly one more verb, which is the signature of a list that
# is fitted by construction rather than a rule that generalises. The OPERATORS
# above are general over facts; getting facts out of prose is not general over
# sources, and no number of verbs added here will make it so. This is the first
# thing the next wave should replace with structured reality input -- it is
# recorded as GSDX-M04 debt rather than left to be discovered by whoever writes
# domain four and sees a silent miss instead of a failing gate.
_TRANSFER_VERB = (r"(?:upload|copy|copies|move|archive|send|transfer|sync|push"
                  r"|publish|write)")
_DESTRUCTIVE_VERB = r"(?:delete|remove|erase|drop|purge|discard|truncate|clear)"
_TRANSFORM_VERB = (r"(?:port|reimplement|re-implement|rewrite|recreate|reproduce"
                   r"|replicate|clone|migrate|reconstruct|emulate)")

_FACT_PATTERNS: tuple[tuple[str, str, str], ...] = (
    # name, where, regex
    # The fact is "the intent transfers something and THEN destroys the source",
    # which is a structure, not a noun. Ordering is load-bearing: destroying and
    # then transferring is a different (and worse) intent.
    ("destructive_act_commanded", "intent",
     rf"\b{_TRANSFER_VERB}\w*\b[^.]{{0,120}}?\b{_DESTRUCTIVE_VERB}\w*\b"),
    # The fact is "no mechanism exists to get the data back".
    ("no_recovery_mechanism", "reality",
     r"\b(?:versioning|recovery|backups?|point-in-time\s+recovery)\b[^.\n]{0,40}?"
     r"\b(?:off|disabled|none|absent|not\s+enabled)\b"
     r"|\bno\s+(?:backups?|recovery|versioning)\b"
     r"|\blifecycle\s+rules:?\s*none\b"),
    # The fact is "the producer does not announce that it has finished".
    ("no_completion_signal", "reality",
     r"\b(?:emits?|sends?|provides?|gives?)\s+no\s+\w*\s*(?:completion|done|finish)\w*\s*\w*\b"
     r"|\bno\s+completion\s+signal\b"
     r"|\bwritten\s+to\b[^.]{0,100}\bcontinuously\b"),
    # The fact is "a downstream reader assumes whatever it sees is finished".
    ("consumer_assumes_complete", "reality",
     r"\btreats?\s+every\s+\w+\s+present\s+as\s+(?:a\s+)?complete\b"),
    # The fact is "a failure mode with a MEASURED frequency". The number may sit
    # on either side of the noun; requiring one order is how this got fitted.
    ("measured_failure_mode", "reality",
     r"\b\d+[^.\n]{0,60}?\b(?:outages?|drops?|failures?|disconnects?)\b"
     r"|\b(?:outages?|drops?|failures?|disconnects?)\b[^.\n]{0,60}?\b\d+\b"),
    # The fact is "a local resource has a known exhaustion horizon".
    ("bounded_local_capacity", "reality",
     r"\bfills?\s+(?:up\s+)?in\s+(?:roughly\s+|about\s+|approximately\s+)?\d+\s+\w+\b"
     r"|\bcapped\s+at\s+\d+\b"),
    ("unattended_operation", "reality",
     r"\bunattended\b|\bnobody\s+logs?\s+in(?:to)?\b|\brestarted\s+by\s+nobody\b"),
    # The fact is "one artifact is being made to stand in for another", which is
    # a DIRECTIONAL STRUCTURE (a transformation verb reaching a target), not a
    # noun. Written as a bare list of domain words -- "APK", "Wii", "emulator" --
    # this would be the GSDX-M04 defect in a new place: a lookup table that
    # transfers to nothing. The verb list is still closed and still costs one
    # entry per unseen wording; what it does NOT do is name a platform.
    ("reconstruction_relation", "intent",
     rf"\b{_TRANSFORM_VERB}\w*\b[^.]{{0,120}}?\b(?:to|onto|into|as|against)\b"),
    # The fact is "the two are required to agree", not any particular tolerance.
    ("fidelity_requirement", "intent",
     r"\b(?:faithful\w*|exact\w*|identical\w*|equivalen\w*|parity|fidelity"
     r"|1:1|bit-for-bit|bit-exact|bit-level|pixel-perfect)\b"),
    # Enrichment only. A reference that RUNS can be interrogated on inputs
    # nobody has tried yet; a reference that is only a document cannot, and the
    # holdout obligation is weaker because there is nothing to hold out against.
    ("reference_is_executable", "reality",
     r"\b(?:reference|original|donor|legacy|incumbent)\b[^.\n]{0,60}?"
     r"\b(?:runs?|running|boots?|playable|executable|still\s+in\s+use)\b"
     r"|\b(?:runs?|running|boots?|playable|executable)\b[^.\n]{0,60}?"
     r"\b(?:reference|original|donor|legacy|incumbent)\b"),
)


def extract_facts(intent: str, reality: str) -> list[Fact]:
    out: list[Fact] = []
    for name, where, pat in _FACT_PATTERNS:
        text = intent if where == "intent" else reality
        m = re.search(pat, text or "", re.IGNORECASE | re.DOTALL)
        if m:
            # EXTRACTED, explicitly: nobody declared this, a regex found it.
            out.append(Fact(name, " ".join(m.group(0).split())[:160], where,
                            state=EXTRACTED))
    return out


# --- derivation operators ---------------------------------------------------
# Three, chosen because the fixture's reality supports exactly these and no
# more. Each is a rule over facts and states its own consequence; none contains
# the text of the obligation it is expected to produce, because an operator that
# spells out its answer is a lookup table wearing a rule's name.

def _has(facts: list[Fact], *names: str) -> bool:
    got = {f.name for f in facts}
    return all(n in got for n in names)


def _cite(facts: list[Fact], *names: str) -> list[str]:
    return [f"{f.name}: {f.matched!r} ({f.source})" for f in facts if f.name in names]


def op_irreversibility_consequence(facts, intent, _reality) -> Obligation | None:
    """An intent that commands destruction of data with no other recovery path
    owes an authorization: what state is being destroyed, and is it safe yet?"""
    if not _has(facts, "destructive_act_commanded", "no_recovery_mechanism"):
        return None
    return Obligation(
        identifier="DO-1",
        text="The destructive step must not execute until the state it makes "
             "unrecoverable is durably established elsewhere, verified rather "
             "than assumed.",
        operator="IRREVERSIBILITY_CONSEQUENCE",
        parents=["human_intent", "fact:destructive_act_commanded",
                 "fact:no_recovery_mechanism"],
        consequence="The only surviving copy is destroyed on every path where "
                    "the transfer did not actually complete. Unrecoverable, and "
                    "undetectable afterwards -- nothing remains to compare.",
        evidence=_cite(facts, "destructive_act_commanded", "no_recovery_mechanism"),
        authority="~/.claude/rules/destructive-state-authorization.md",
        closure_condition="the destructive call is reachable only from a verified-"
                          "success branch, and from no error path",
        done_gate="a test in which the transfer fails and the local state survives",
        invalidated_by=["a recovery mechanism is introduced (versioning, backup, "
                        "lifecycle retention)",
                        "the destructive step is removed from the intent"],
    )


def op_absent_signal_consequence(facts, _intent, _reality) -> Obligation | None:
    """A plan that acts on an event owes the question: does the environment
    actually signal that event, or is the trigger a guess that looks like one?"""
    if not _has(facts, "no_completion_signal"):
        return None
    ob = Obligation(
        identifier="DO-2",
        text="The work must not act on a subject whose readiness the environment "
             "does not signal; readiness has to be established by observation "
             "before the subject is consumed.",
        operator="ABSENT_SIGNAL_CONSEQUENCE",
        parents=["human_intent", "fact:no_completion_signal"],
        consequence="An incomplete subject is processed as though it were "
                    "complete.",
        evidence=_cite(facts, "no_completion_signal"),
        authority="~/.claude/rules/real-context-reachability.md "
                  "(unmeasured is not measured)",
        closure_condition="a readiness test runs before the subject is consumed, "
                          "and consumption cannot be reached without it",
        done_gate="a test in which a subject still being written is not consumed",
        invalidated_by=["the producer starts emitting a completion signal"],
    )
    if _has(facts, "consumer_assumes_complete"):
        ob.consequence += (" A downstream consumer treats whatever it finds as "
                           "complete, so the defect is silent: nothing errors, "
                           "and the truncated result is used as though it were "
                           "the real one.")
        ob.evidence += _cite(facts, "consumer_assumes_complete")
        ob.parents.append("fact:consumer_assumes_complete")
    return ob


def op_failure_consequence(facts, _intent, _reality) -> Obligation | None:
    """A failure mode the environment has MEASURED is not a hypothetical, and a
    plan whose critical path crosses it owes a response to it."""
    if not _has(facts, "measured_failure_mode"):
        return None
    ob = Obligation(
        identifier="DO-3",
        text="The measured failure mode must be survivable: work is retained "
             "until it succeeds, and retrying must not be unbounded in the "
             "resource the environment limits.",
        operator="FAILURE_CONSEQUENCE",
        parents=["human_intent", "fact:measured_failure_mode"],
        consequence="During a failure window the work is either lost or "
                    "accumulates without limit.",
        evidence=_cite(facts, "measured_failure_mode"),
        authority="the environment's own measurements",
        closure_condition="failures retain the work and retry, and the retained "
                          "backlog is bounded or alarmed",
        done_gate="a test across an induced failure window",
        invalidated_by=["the failure mode stops being measured in the environment"],
    )
    if _has(facts, "bounded_local_capacity"):
        ob.consequence += (" The limited resource is exhausted, which stops the "
                           "producer as well as the consumer.")
        ob.evidence += _cite(facts, "bounded_local_capacity")
        ob.parents.append("fact:bounded_local_capacity")
    return ob


def op_unfalsifiable_parity_consequence(facts, _intent, _reality) -> Obligation | None:
    """A mission that requires one artifact to behave as another owes the
    question nobody states: measured against WHAT, and could it have failed?

    Agreement on the traces the implementation was built from is the one result
    a memorising reconstruction and a generalising one both produce, so it
    cannot tell them apart. The obligation is evidence the implementation path
    never saw.
    """
    if not _has(facts, "reconstruction_relation", "fidelity_requirement"):
        return None
    ob = Obligation(
        identifier="DO-4",
        text="Parity must be judged on evidence the implementation path did not "
             "see: a holdout withheld before the work starts, and kept withheld.",
        operator="UNFALSIFIABLE_PARITY_CONSEQUENCE",
        parents=["human_intent", "fact:reconstruction_relation",
                 "fact:fidelity_requirement"],
        consequence="The candidate is accepted on the evidence it was fitted to. "
                    "A reconstruction that matches every observed trace and "
                    "fails on unseen input is indistinguishable at acceptance "
                    "time from one that generalises, so the defect is found by "
                    "the first user to do something nobody recorded.",
        evidence=_cite(facts, "reconstruction_relation", "fidelity_requirement"),
        authority="~/.claude/rules/evaluation-corpus-governance.md "
                  "(partition before ingestion; a corpus cannot be un-taught)",
        closure_condition="a holdout was partitioned BEFORE the implementation "
                          "began, the implementation path cannot read it, and "
                          "the candidate is judged on it",
        done_gate="a parity verdict over the holdout, reported beside the "
                  "known-trace verdict rather than merged into it",
        invalidated_by=["the fidelity requirement is withdrawn",
                        "the reference stops being available to generate "
                        "unseen cases"],
    )
    if _has(facts, "reference_is_executable"):
        ob.consequence += (" The reference is executable here, so unseen cases "
                           "can be GENERATED rather than merely waited for -- "
                           "which makes the omission a choice rather than a "
                           "limitation.")
        ob.evidence += _cite(facts, "reference_is_executable")
        ob.parents.append("fact:reference_is_executable")
    return ob


OPERATORS = (
    op_irreversibility_consequence,
    op_absent_signal_consequence,
    op_failure_consequence,
    op_unfalsifiable_parity_consequence,
)


# The fact vocabulary the operators understand. A second fact source
# (structured_facts.py, GSDX-M04) validates against this set, so a name the
# operators cannot read is refused at load rather than silently dropping an
# obligation. Derived from the prose table so the two can never disagree.
FACT_NAMES: frozenset[str] = frozenset(name for name, _, _ in _FACT_PATTERNS)


def derive_from_facts(facts: list[Fact], intent: str,
                      reality: str) -> tuple[list[Obligation], list[Fact]]:
    """Run the operators over facts from ANY source.

    The operators were always general over facts; only the prose extractor was
    fitted. Separating the two is the whole of GSDX-M04's seam: a structured
    source feeds this directly and never passes through a regex."""
    out = []
    for op in OPERATORS:
        ob = op(facts, intent, reality)
        if ob is not None:
            out.append(ob)
    return out, facts


def derive(intent: str, reality: str) -> tuple[list[Obligation], list[Fact]]:
    """Propose candidates from PROSE. Nothing here decides anything: every
    obligation comes back as CANDIDATE, and a candidate is evidence, not
    authority."""
    return derive_from_facts(extract_facts(intent, reality), intent, reality)


# --- materiality gate -------------------------------------------------------

def judge(ob: Obligation) -> Obligation:
    """Candidate -> disposition. The only door to ACCEPTED.

    Three independent conditions, because collapsing them loses which one
    failed -- and they need different fixes. A candidate with no named
    consequence is a wish; one with no evidence is an assertion about a project
    it was never checked against; one with no closure condition can never be
    closed and would block a mission forever.
    """
    if ob.disposition != CANDIDATE:
        return ob
    if not ob.consequence.strip():
        ob.disposition = REJECTED
        ob.disposition_reason = ("no consequence named -- a requirement whose "
                                 "omission costs nothing is a preference")
        return ob
    if not ob.evidence:
        ob.disposition = NOT_APPLICABLE
        ob.disposition_reason = ("the rule fired but this project's own reality "
                                 "supplied no evidence that it applies here")
        return ob
    if not ob.closure_condition.strip():
        ob.disposition = REJECTED
        ob.disposition_reason = ("no closure condition -- an obligation that "
                                 "cannot be closed blocks the mission forever")
        return ob
    ob.disposition = ACCEPTED
    ob.disposition_reason = (f"{ob.operator} fired on {len(ob.evidence)} piece(s) "
                             "of project evidence, and omission has a named "
                             "consequence")
    return ob


def invalidate_if_parent_gone(ob: Obligation, live_facts: list[Fact]) -> Obligation:
    """Derived once is not true forever.

    An obligation whose causal parent has stopped holding does not stay required
    by inertia -- it goes STALE, including from SATISFIED, because a proof of
    something that is no longer required is not a reason to keep requiring it.

    Only `fact:`-prefixed parents participate. `human_intent` is a parent too and
    is deliberately NOT invalidatable here: an intent that changed is a different
    mission, and silently retiring its obligations would hide that rather than
    surface it. The prefix is the contract, and a parent written without it is
    inert -- which cost this suite a failing gate, because the first version of
    its own test asserted invalidation using a bare parent name.
    """
    if ob.disposition in (REJECTED, NOT_APPLICABLE, DEFERRED):
        return ob
    live = {f.name for f in live_facts}
    gone = [p for p in ob.parents
            if p.startswith("fact:") and p[len("fact:"):] not in live]
    if gone:
        ob.disposition = STALE
        ob.disposition_reason = ("causal parent no longer holds: "
                                 + ", ".join(gone))
    return ob
