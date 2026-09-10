#!/usr/bin/env python3
"""Architectural truth -- LAW II.

    Reaching the target is not enough; the system must reach it through a
    valid architectural state.

Section 8 states the law as seven pairs, and every one has the same shape: a
cheap, visible signal that is routinely mistaken for an expensive, invisible
fact.

    function returned success   is not   side effect committed correctly
    file loaded                 is not   mounted, parsed, validated, linked,
                                         initialized and consumed correctly
    screen appeared             is not   application state initialized correctly
    HTTP 200                    is not   business operation happened exactly once
    row exists                  is not   valid domain transition occurred
    test passed                 is not   intended execution path was exercised
    process exited 0            is not   external durable side effect succeeded

The left column is a PROXY. The right column is the CORROBORANT. A proxy is not
worthless -- it is usually necessary. It is just never sufficient, and the whole
failure class is treating it as if it were.

Why this module exists rather than more prose
---------------------------------------------
Power Pack's always-loaded core already says "File exists != works (observable
output required)". That is the right instinct aimed at the wrong half of the
problem: it addresses existence, not validity of the state the system passed
through on its way to the result. A capability can be observably producing
output and still have reached it through an invalid state -- which is precisely
the case that costs a day to debug, because every visible signal is green.

Connection to LAW IX
--------------------
This does not issue its own completion verdict. It CAPS one. A claim resting on
a proxy alone cannot honestly exceed EXECUTED, because what was observed is that
something ran -- not that it ran correctly. The cap is handed to the strength
ladder rather than duplicating its vocabulary, so there is one grader of
completion claims in this repo and this is an input to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VALID = "VALID"
PROXY_ONLY = "PROXY_ONLY"
UNDETERMINED = "UNDETERMINED"
GATE_FAILED = "GATE_FAILED"

# The rung a proxy-only claim may not exceed. "It ran" is an honest reading of a
# proxy; "it was verified" is not.
PROXY_ONLY_CEILING = "EXECUTED"


@dataclass(frozen=True)
class Pair:
    proxy: str
    corroborant: str
    why: str


# Section 8, verbatim in structure. Domain-specific pairs are registered by
# callers rather than hardcoded here -- the law is universal, its instances are
# not, and baking one domain's vocabulary in would make the others second-class.
CANONICAL_PAIRS: tuple[Pair, ...] = (
    Pair("function_returned_success", "side_effect_committed",
         "a return value describes control flow, not durability"),
    Pair("file_loaded", "file_consumed_correctly",
         "loading is the first of mount, parse, validate, link, initialize, consume"),
    Pair("screen_appeared", "app_state_initialized",
         "a rendered surface can be painted over invalid state"),
    Pair("http_200", "operation_happened_exactly_once",
         "200 survives a retry that committed twice"),
    Pair("row_exists", "valid_domain_transition",
         "a row can be written by a path the domain forbids"),
    Pair("test_passed", "intended_path_exercised",
         "a test can pass without reaching the code it names"),
    Pair("process_exit_zero", "external_effect_durable",
         "exit 0 reports the process, not the world it was supposed to change"),
)


@dataclass
class TruthVerdict:
    outcome: str
    ceiling: str | None
    proxy_only: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    corroborated: list[str] = field(default_factory=list)
    detail: str = ""

    def render(self) -> str:
        lines = [f"architectural truth: {self.outcome}"]
        if self.ceiling:
            lines.append(f"  caps any completion claim at: {self.ceiling}")
        for p in self.corroborated:
            lines.append(f"  ok         {p}")
        for p in self.proxy_only:
            lines.append(f"  PROXY-ONLY {p}")
        for p in self.unknown:
            lines.append(f"  UNKNOWN    {p}  (corroborant never checked)")
        if self.detail:
            lines.append(f"  {self.detail}")
        return "\n".join(lines)


def assess_state(
    observed: dict[str, bool] | None = None,
    extra_pairs: tuple[Pair, ...] = (),
) -> TruthVerdict:
    """Judge whether observed signals establish architectural validity.

    `observed` is three-valued exactly as the strength ladder is: present-and-
    True, present-and-False, or absent meaning nobody checked. An absent
    corroborant yields UNDETERMINED and never a pass -- a proxy whose
    corroborant was never looked for is the entire failure class, so resolving
    it toward "fine" would defeat the module.
    """
    try:
        observed = dict(observed or {})
        pairs = CANONICAL_PAIRS + tuple(extra_pairs)

        proxy_only: list[str] = []
        unknown: list[str] = []
        corroborated: list[str] = []

        for pair in pairs:
            if observed.get(pair.proxy) is not True:
                continue  # this proxy was not claimed; the pair is not in play
            corr = observed.get(pair.corroborant)
            if corr is True:
                corroborated.append(f"{pair.proxy} + {pair.corroborant}")
            elif corr is False:
                proxy_only.append(f"{pair.proxy}: {pair.why}")
            else:
                unknown.append(f"{pair.proxy} -> {pair.corroborant}: {pair.why}")

        if proxy_only:
            return TruthVerdict(
                PROXY_ONLY, PROXY_ONLY_CEILING, proxy_only, unknown, corroborated,
                detail="a proxy signal was observed and its corroborant was "
                       "checked and absent: the target was reached, the state "
                       "it was reached through was not valid",
            )
        if unknown:
            return TruthVerdict(
                UNDETERMINED, PROXY_ONLY_CEILING, proxy_only, unknown, corroborated,
                detail="corroborant never checked; this is not a failure of the "
                       "work, and it is not a pass either",
            )
        if not corroborated:
            return TruthVerdict(
                UNDETERMINED, None,
                detail="no proxy signal claimed; LAW II has nothing to judge here",
            )
        return TruthVerdict(VALID, None, corroborated=corroborated)
    except Exception as exc:  # noqa: BLE001 - the checker's own failure branch
        return TruthVerdict(
            GATE_FAILED, None,
            detail=f"{type(exc).__name__}: {exc}; architectural validity was NOT judged",
        )


def ceiling_for(observed: dict[str, bool] | None = None,
                extra_pairs: tuple[Pair, ...] = ()) -> str | None:
    """The rung a completion claim may not exceed given these signals.

    Returned for the strength ladder to apply. None means LAW II imposes no cap,
    which is not the same as endorsing the claim -- the ladder still grades it.
    """
    return assess_state(observed, extra_pairs).ceiling
