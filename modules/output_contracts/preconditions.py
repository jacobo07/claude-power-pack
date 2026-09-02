"""Preconditions -- the veto the OQS score could not express.

`is_done` scores a deliverable and passes it at 70. Every check is a
WEIGHT, so a deliverable can fail any single check and still be Done by
earning the rest. That is correct for quality, where a missing docstring
should not outrank passing tests, and it is wrong for delivery: a change
whose executing bytes are a DIFFERENT VERSION is not partially done, and
no amount of passing tests on the version nobody runs makes it so.

Measured 2026-09-02 in this repo: 5 registered hooks execute bytes that
differ from the committed ones, and one of them is a fix a prior session
declared shipped six days earlier. The score model would have rated that
session's deliverable highly -- correct file, correct syntax, passing
tests, no slop -- because every one of those questions is about the
artifact in the repository, and none is about the artifact that runs.

A precondition therefore VETOES independently of score. Contracts opt in;
a contract declaring none behaves exactly as before.

APPLICABILITY IS THE WHOLE DESIGN. Blocking every commit on runtime proof
would tax documentation, libraries and anything not intended for
deployment, and a gate that fires where it does not belong gets disabled
rather than obeyed. So the claim declares its own scope, and only a claim
that asserts the change is LIVE has to prove it. Widening the applicable
set is a deliberate act, never a side effect.

UNKNOWN IS NOT PASS. `validator._run_check` returns True for a check type
it does not recognise -- fail-open, appropriate for a scorer that must
never fabricate a failure. Preconditions invert that: an unrecognised
precondition VETOES. The asymmetry is deliberate. A scorer meeting an
unknown check loses information about quality; a done-gate meeting an
unknown precondition has been handed a requirement by a newer contract
than itself, and answering "fine" is precisely how a version-skewed gate
certifies what it cannot see.
"""
from __future__ import annotations

from typing import Callable, Iterable

PASS = "PASS"
VETO = "VETO"
NOT_APPLICABLE = "NOT_APPLICABLE"
UNVERIFIED = "UNVERIFIED"

# Claim scopes, weakest to strongest. Each asserts everything to its left.
CLAIM_SCOPES = ("source", "repository", "integration", "installation",
                "runtime", "production")

# Scopes whose claim is that the change GOVERNS REAL BEHAVIOUR. Only these
# owe effective-state evidence. "integration" deliberately does not: a
# branch merged to main is a true statement about the repository and says
# nothing about which bytes execute, which is the distinction that cost a
# session six days.
RUNTIME_SCOPES = frozenset({"runtime", "production"})

# A claim that names no scope is not silently promoted to the strongest.
# Defaulting to "runtime" would make every unscoped deliverable owe
# delivery proof and the veto would be disabled within a week.
DEFAULT_SCOPE = "repository"

# Every effective-state verdict meaning "the bytes you claim are live are
# not the bytes that run". All of them veto a runtime claim -- the claim is
# false under each -- but WHAT TO DO differs so sharply that reporting one
# sentence for all of them is how a gate teaches the wrong repair. Measured
# 2026-09-02: two artifacts were undelivered work of this checkout, two
# were another lineage's NEWER commits already running, and one was that
# tree's uncommitted edit. The single message this file used to emit --
# "committed is not installed" -- was true for the first pair, backwards
# for the second, and the action it implied would have overwritten
# twenty-two commits of somebody else's work to deliver two files that
# needed no delivery.
_REMEDY = {
    "STRANDED": ("this checkout's committed work has not reached the "
                 "running tree; delivering needs that tree's owner"),
    "AHEAD_OF_HERE": ("the running tree holds NEWER committed bytes from "
                      "another lineage and this checkout has not changed "
                      "the file; integrate here -- do not overwrite"),
    "DIVERGED": ("both lineages changed this file since the merge base; "
                 "which one governs production is a decision, not a "
                 "measurement"),
    "FOREIGN_EDIT": ("the running tree carries uncommitted work for this "
                     "path; it is legitimate state until its owner says "
                     "otherwise"),
    "SHADOWED": ("the bytes differ and the direction could not be "
                 "established; unmeasured is not delivered"),
    "ABSENT_RUNNING": "no file exists at the registered path in the running tree",
}
NOT_EFFECTIVE = frozenset(_REMEDY)


def _status_of(state) -> str:
    """Accept a bare status or a detector row. The detector returns rows
    carrying a remediation class; injected test resolvers return the status
    alone, and neither should have to know about the other."""
    if isinstance(state, dict):
        return str(state.get("status") or "")
    return str(state or "")


def claim_scope(ctx: dict) -> str:
    scope = str(ctx.get("claim_scope") or DEFAULT_SCOPE).strip().lower()
    return scope if scope in CLAIM_SCOPES else DEFAULT_SCOPE


def _effective_state(ctx: dict, resolver: Callable | None) -> tuple[str, str]:
    """Do the artifacts this claim delivers match the ones that execute?

    Evidence comes from the estate's existing effective-state detector,
    never from a second implementation living here -- a done-gate that
    computes its own answer can agree with itself while both are wrong.
    The resolver is injectable so tests drive real verdicts without
    reaching production state, and so this module stays importable where
    the detector's dependencies are absent.
    """
    scope = claim_scope(ctx)
    if scope not in RUNTIME_SCOPES:
        return NOT_APPLICABLE, (
            f"claim scope {scope!r} does not assert the change is live")

    artifacts = [str(a) for a in (ctx.get("artifacts") or []) if str(a).strip()]
    if not artifacts:
        return UNVERIFIED, (
            f"claim scope {scope!r} asserts the change is live but names no "
            "artifact, so there is nothing to compare against the executing "
            "tree")

    if resolver is None:
        resolver = _default_resolver
    try:
        states = resolver(artifacts)
    except Exception as exc:                       # detector unavailable
        return UNVERIFIED, (
            f"effective state could not be determined ({exc.__class__.__name__})"
            " -- unmeasured is not measured-equal")

    missing = [a for a in artifacts if a not in states]
    # Anything not positively EFFECTIVE blocks, so a status this module has
    # never heard of cannot pass by falling off the end of a list. The
    # detector may grow new verdicts; this file learning about them late
    # must cost a false red, never a false green.
    bad = sorted((a, _status_of(s)) for a, s in states.items()
                 if _status_of(s) != "EFFECTIVE")

    unconfirmable = [(a, st) for a, st in bad if st == "LOCAL_EDIT"]
    if len(unconfirmable) == len(bad) and bad:
        return UNVERIFIED, (
            "the working copy of " + ", ".join(a for a, _ in unconfirmable)
            + " differs from the bytes that run, and the difference is "
            "uncommitted here -- what executes is this checkout's last "
            "COMMIT, so a claim about the current file cannot be confirmed")
    if bad:
        detail = "; ".join(
            f"{a} [{st}: {_REMEDY.get(st, 'unrecognised effective state')}]"
            for a, st in bad if st != "LOCAL_EDIT")
        return VETO, (
            f"{len(bad)} artifact(s) claimed live are not the executing "
            f"bytes: {detail}")
    if missing:
        return UNVERIFIED, (
            "the detector returned no verdict for: " + ", ".join(sorted(missing))
            + " -- it may not be a registered executable, in which case the "
            "claim scope is wrong rather than the artifact")
    return PASS, f"{len(states)} artifact(s) are the executing bytes"


def _default_resolver(artifacts: Iterable[str]) -> dict:
    """Repo-relative path -> effective-state verdict, from the real detector."""
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tools import mirror_unpaired_audit as mu   # noqa: PLC0415

    live = mu.resolve_live_root(None)
    res = mu.effective_state(root, mu._read(live / "settings.json"))
    if not res.get("resolved"):
        raise RuntimeError("no registered checkout resolved")
    by_rel = {r["rel"].replace("\\", "/"): r["status"] for r in res["rows"]}
    return {a: by_rel[a.replace("\\", "/")]
            for a in artifacts if a.replace("\\", "/") in by_rel}


_HANDLERS = {"effective_state": _effective_state}


def evaluate(precondition: dict, ctx: dict,
             resolver: Callable | None = None) -> dict:
    kind = str(precondition.get("type") or "").strip()
    handler = _HANDLERS.get(kind)
    if handler is None:
        return {"type": kind or "<unnamed>", "verdict": VETO,
                "message": (
                    f"unrecognised precondition {kind!r}. This contract "
                    "requires something this validator cannot evaluate; "
                    "certifying it would be a version-skewed pass.")}
    verdict, message = handler(ctx, resolver)
    return {"type": kind, "verdict": verdict, "message": message}


def check(contract: dict, ctx: dict,
          resolver: Callable | None = None) -> list[dict]:
    """Every precondition result, in declaration order.

    Returns results rather than a boolean so a blocked claim can say what
    failed, what was expected, what is effective and who resolves it. An
    opaque red teaches nobody which of six things went wrong.
    """
    return [evaluate(p, ctx, resolver)
            for p in (contract.get("preconditions") or [])]


def blocking(results: Iterable[dict], strict_unverified: bool = True) -> list:
    """Which results stop Done.

    UNVERIFIED blocks by default. The alternative is to coerce "could not
    tell" into "fine", which is the exact move that let a producer report
    healthy while blind to three quarters of its subject.
    """
    stop = {VETO, UNVERIFIED} if strict_unverified else {VETO}
    return [r for r in results if r["verdict"] in stop]
