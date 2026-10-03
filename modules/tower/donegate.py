"""Family done-gate (spec 2026-09-24, slice S6) -- REPORT-ONLY.

Judges every ACTIVE entry of a family's newest generation against a subject
repo. The spec keeps blocking as a separate Owner decision (§7: "arranca como
informe"), so this module has no enforce mode at all: `would_block` states
what enforcement would have done, and nothing here can refuse anything.

Per entry, one verdict:

  APPLIED_VERIFIED  an evaluable check (file/glob/regex) passed
  VIOLATED          an evaluable check failed
  DELEGATED         a registered verifier owns the verdict (the repo's)
  NOT_APPLICABLE    declared by the caller WITH a reason from NA_REASONS,
                    within NA_SHARE_CAP_PERCENT of the family
  UNJUDGED          prose or empty check, a `test:` check (the file exists but
                    is never executed here), an N/A without a usable reason,
                    an unreadable registry, or the instrument's own failure --
                    never counted as applied

A `test:` check whose file exists is UNJUDGED with `unjudged_reason`
"test-not-run", not DELEGATED: nothing on this path runs it, so a failing named
test must not read as handled (audit G13). `registry:` checks keep DELEGATED.
Every row carries `unjudged_reason` (None unless the verdict is UNJUDGED), and
the report's `counts` keeps UNJUDGED apart from VIOLATED, with `unjudged_tests`
naming the `test:` entries. `would_block` is a VIOLATED or UNJUDGED entry OR a
chain that is not ok (`would_block_on_chain`, WR-03: the chain hardening must
bite at the exit, not only in `chain_ok`); `would_block_on_violated` is the
VIOLATED-only reading.

Declaring an entry not applicable is a claim by the caller, so it is bounded
twice. The reason must carry a token from the closed vocabulary `NA_REASONS`
(`token` or `token: free-text note`); any other text is UNJUDGED
("na-not-in-vocabulary"). And the number of valid claims may not exceed
`(NA_SHARE_CAP_PERCENT * n) // 100` for n active entries (integer arithmetic);
over the cap EVERY claim is voided to UNJUDGED ("na-over-cap"), because choosing
which claims are legitimate would itself be gameable. A family of fewer than 4
entries therefore admits no N/A at all: deliberate and fail-closed. The report
carries `na_count`, `na_cap` and `na_over_cap`.

An honoured N/A does not skip the entry's check (WR-04). The check is evaluated
anyway, and when it FAILS the row keeps verdict NOT_APPLICABLE (a legitimate N/A is
typically a check that the surface exists, failing because the surface does not)
but carries `na_masked_violation`, and the report names it in `na_masked_violations`,
counts it in `counts["na_over_failing_check"]` and states `would_block_on_masked_na`,
so a claim can never make a failing runnable check invisible.

Every entry is judged whether or not the selection compiler injected it into
the prompt: the injection ceiling bounds what is shown, not what is
constitutive (select.py). Each report and each finding is stamped with
`judged_under` = "<family>/B<n>" and the generation's SHA-256, so a verdict
stays historically true when a later generation is stronger, and a finding
can be attributed to this path (`source`) rather than to any other gate that
happens to reach the same conclusion.
"""
from __future__ import annotations

from . import baselines as bl
from . import checks as ck
from . import ratchet as rt
from . import select as sel

SOURCE = "tower-baseline"
APPLIED_VERIFIED = "APPLIED_VERIFIED"
VIOLATED = "VIOLATED"
DELEGATED = "DELEGATED"
NOT_APPLICABLE = "NOT_APPLICABLE"
UNJUDGED = "UNJUDGED"
NO_BASELINE = "NO_BASELINE"
JUDGED = "JUDGED"

_FROM_CHECK = {ck.PASS: APPLIED_VERIFIED, ck.FAIL: VIOLATED, ck.DELEGATED: DELEGATED}

# Machine-readable `unjudged_reason` of an UNJUDGED row.
REASON_PROSE = "prose"
REASON_EMPTY = "empty"
REASON_TEST_NOT_RUN = "test-not-run"
REASON_NA_NO_REASON = "na-no-reason"
REASON_NA_NOT_IN_VOCABULARY = "na-not-in-vocabulary"
REASON_NA_OVER_CAP = "na-over-cap"
REASON_UNREADABLE = "unreadable"
REASON_OTHER = "other"
_REASON_FROM_OUTCOME = {ck.UNRUNNABLE_PROSE: REASON_PROSE, ck.EMPTY: REASON_EMPTY,
                        ck.UNREADABLE: REASON_UNREADABLE}

# Closed vocabulary for a not-applicable claim: one token per trait a baseline
# entry can be absent for (the traits of the capability surface), plus two
# structural ones. Deliberately absent: any reason that only defers the work to
# later or to someone else. A deferral is not non-applicability, and admitting
# one would reopen the excuse this vocabulary exists to close.
NA_REASONS = (
    "no-persistent-state",
    "single-actor",
    "no-bulk-operation",
    "no-destructive-operation",
    "not-distributed",
    "no-external-effect",
    "not-scheduled",
    "no-money",
    "single-policy-layer",
    "no-user-interface",
    "platform-not-targeted",
    "superseded-by-entry",
)
# At most this share of a family's active entries may be declared N/A.
NA_SHARE_CAP_PERCENT = 30

_COUNT_KEYS = ("applied", "violated", "delegated", "not_applicable", "unjudged",
               "unjudged_tests", "na_over_failing_check")
_COUNT_OF = {APPLIED_VERIFIED: "applied", VIOLATED: "violated", DELEGATED: "delegated",
             NOT_APPLICABLE: "not_applicable", UNJUDGED: "unjudged"}


def parse_na_reason(reason) -> tuple:
    """(token, note) when the reason leads with a NA_REASONS token, else (None, text).

    The text is split on the first ":"; only the stripped head is matched, so
    `no-money` and `no-money: internal tool has no billing` both yield the token.
    """
    text = str(reason or "").strip()
    head, _, note = text.partition(":")
    head = head.strip()
    if head in NA_REASONS:
        return (head, note.strip())
    return (None, text)


def _counts(rows: list) -> dict:
    out = {k: 0 for k in _COUNT_KEYS}
    for x in rows:
        out[_COUNT_OF[x["verdict"]]] += 1
        if x["unjudged_reason"] == REASON_TEST_NOT_RUN:
            out["unjudged_tests"] += 1
        if x.get("na_masked_violation"):
            out["na_over_failing_check"] += 1
    return out


def judge(family: str, repo_root: str, registry: str | None = None,
          root: str | None = None, not_applicable: dict | None = None) -> dict:
    gens = bl.generations(family, root)
    if not gens:
        return {"family": family, "judged_under": None, "generation_sha256": None,
                "chain_ok": None, "status": NO_BASELINE, "report_only": True,
                "would_block": False, "would_block_on_violated": False,
                "would_block_on_chain": False, "would_block_on_masked_na": False,
                "na_masked_violations": [],
                "counts": _counts([]), "unjudged_tests": [],
                "na_count": 0, "na_cap": 0, "na_over_cap": False,
                "entries": [], "deferred_from_prompt": []}
    n = gens[-1]
    stamp = "%s/B%d" % (family, n)
    active = bl.active_entries(family, root)
    injected = {e.get("id") for e in sel.select_for_injection(active).injected}
    na = not_applicable or {}
    n_active = len(active)
    na_cap = (NA_SHARE_CAP_PERCENT * n_active) // 100
    na_count = sum(1 for e in active
                   if e.get("id") in na and parse_na_reason(na[e.get("id")])[0])
    na_over_cap = na_count > na_cap
    out = []
    for e in active:
        ident = e.get("id")
        why = None
        masked = False
        if ident in na:
            outcome = None
            token, note = parse_na_reason(na[ident])
            if not str(na[ident] or "").strip():
                verdict, why = UNJUDGED, REASON_NA_NO_REASON
                detail = "declared not applicable with no reason"
            elif token is None:
                verdict, why = UNJUDGED, REASON_NA_NOT_IN_VOCABULARY
                detail = "N/A reason %r carries no token from NA_REASONS" % note
            elif na_over_cap:
                verdict, why = UNJUDGED, REASON_NA_OVER_CAP
                detail = "N/A share %d/%d over cap %d" % (na_count, n_active, na_cap)
            else:
                verdict = NOT_APPLICABLE
                detail = "%s: %s" % (token, note) if note else token
                # The claim is honoured, but the check is still evaluated: a claim
                # must not make a failing runnable check invisible (code review
                # WR-04). The honoured claim stays NOT_APPLICABLE because that is
                # the normal shape of a legitimate N/A (a check that the surface
                # exists, failing because the surface does not).
                r = ck.evaluate(e, repo_root, registry)
                outcome = r.outcome
                if r.outcome == ck.FAIL:
                    masked = True
                    detail += " [N/A claimed over a check that FAILS: %s]" % r.detail
        else:
            r = ck.evaluate(e, repo_root, registry)
            outcome = r.outcome
            if r.kind == "test" and r.outcome == ck.DELEGATED:
                # Nothing on this path runs the file: it must not read as handled.
                verdict, why = UNJUDGED, REASON_TEST_NOT_RUN
                detail = "test exists; never run on this path - judged UNJUDGED, not DELEGATED"
            else:
                verdict = _FROM_CHECK.get(r.outcome, UNJUDGED)
                detail = r.detail
                if verdict == UNJUDGED:
                    why = _REASON_FROM_OUTCOME.get(r.outcome, REASON_OTHER)
        out.append({"entry_id": ident, "verdict": verdict, "check_outcome": outcome,
                    "unjudged_reason": why, "na_masked_violation": masked,
                    "detail": detail, "requirement": e.get("requirement"),
                    "injected": ident in injected, "source": SOURCE,
                    "judged_under": stamp})
    masked_na = sorted(x["entry_id"] for x in out if x["na_masked_violation"])
    chain_ok = rt.verify_chain(family, root).ok
    # A chain that is not ok (TAMPERED, UNANCHORED, unrecorded regressions, missing
    # root) is a block on its own: the entries it carries are not trustworthy even
    # when every one of them passes (code review WR-03).
    would_block_on_chain = chain_ok is False
    return {"family": family, "judged_under": stamp,
            "generation_sha256": bl.generation_sha256(family, n, root),
            "chain_ok": chain_ok, "status": JUDGED,
            "report_only": True,
            "would_block": would_block_on_chain
            or any(x["verdict"] in (VIOLATED, UNJUDGED) for x in out),
            "would_block_on_chain": would_block_on_chain,
            # What blocking would be if N/A claims over a failing check were not
            # trusted. Informational: an honoured N/A (see above) does not block.
            "would_block_on_masked_na": bool(masked_na),
            "na_masked_violations": masked_na,
            "would_block_on_violated": any(x["verdict"] == VIOLATED for x in out),
            "counts": _counts(out),
            "unjudged_tests": sorted(x["entry_id"] for x in out
                                     if x["unjudged_reason"] == REASON_TEST_NOT_RUN),
            "na_count": na_count, "na_cap": na_cap, "na_over_cap": na_over_cap,
            "entries": out,
            "deferred_from_prompt": sorted(x["entry_id"] for x in out if not x["injected"])}
