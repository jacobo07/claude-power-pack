"""Family done-gate (spec 2026-09-24, slice S6) -- REPORT-ONLY.

Judges every ACTIVE entry of a family's newest generation against a subject
repo. The spec keeps blocking as a separate Owner decision (§7: "arranca como
informe"), so this module has no enforce mode at all: `would_block` states
what enforcement would have done, and nothing here can refuse anything.

Per entry, one verdict:

  APPLIED_VERIFIED  an evaluable check (file/glob/regex) passed
  VIOLATED          an evaluable check failed
  DELEGATED         a registered verifier owns the verdict (the repo's)
  NOT_APPLICABLE    declared by the caller WITH a reason
  UNJUDGED          prose or empty check, a `test:` check (the file exists but
                    is never executed here), an N/A without a reason, an
                    unreadable registry, or the instrument's own failure --
                    never counted as applied

A `test:` check whose file exists is UNJUDGED with `unjudged_reason`
"test-not-run", not DELEGATED: nothing on this path runs it, so a failing named
test must not read as handled (audit G13). `registry:` checks keep DELEGATED.
Every row carries `unjudged_reason` (None unless the verdict is UNJUDGED), and
the report's `counts` keeps UNJUDGED apart from VIOLATED, with `unjudged_tests`
naming the `test:` entries. `would_block` is unchanged (VIOLATED or UNJUDGED);
`would_block_on_violated` is the VIOLATED-only reading.

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

_COUNT_KEYS = ("applied", "violated", "delegated", "not_applicable", "unjudged",
               "unjudged_tests")
_COUNT_OF = {APPLIED_VERIFIED: "applied", VIOLATED: "violated", DELEGATED: "delegated",
             NOT_APPLICABLE: "not_applicable", UNJUDGED: "unjudged"}


def _counts(rows: list) -> dict:
    out = {k: 0 for k in _COUNT_KEYS}
    for x in rows:
        out[_COUNT_OF[x["verdict"]]] += 1
        if x["unjudged_reason"] == REASON_TEST_NOT_RUN:
            out["unjudged_tests"] += 1
    return out


def judge(family: str, repo_root: str, registry: str | None = None,
          root: str | None = None, not_applicable: dict | None = None) -> dict:
    gens = bl.generations(family, root)
    if not gens:
        return {"family": family, "judged_under": None, "generation_sha256": None,
                "chain_ok": None, "status": NO_BASELINE, "report_only": True,
                "would_block": False, "would_block_on_violated": False,
                "counts": _counts([]), "unjudged_tests": [],
                "entries": [], "deferred_from_prompt": []}
    n = gens[-1]
    stamp = "%s/B%d" % (family, n)
    active = bl.active_entries(family, root)
    injected = {e.get("id") for e in sel.select_for_injection(active).injected}
    na = not_applicable or {}
    out = []
    for e in active:
        ident = e.get("id")
        reason = na.get(ident)
        why = None
        if ident in na and str(reason or "").strip():
            verdict, detail, outcome = NOT_APPLICABLE, str(reason).strip(), None
        elif ident in na:
            verdict, detail, outcome = UNJUDGED, "declared not applicable with no reason", None
            why = REASON_NA_NO_REASON
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
                    "unjudged_reason": why,
                    "detail": detail, "requirement": e.get("requirement"),
                    "injected": ident in injected, "source": SOURCE,
                    "judged_under": stamp})
    return {"family": family, "judged_under": stamp,
            "generation_sha256": bl.generation_sha256(family, n, root),
            "chain_ok": rt.verify_chain(family, root).ok, "status": JUDGED,
            "report_only": True,
            "would_block": any(x["verdict"] in (VIOLATED, UNJUDGED) for x in out),
            "would_block_on_violated": any(x["verdict"] == VIOLATED for x in out),
            "counts": _counts(out),
            "unjudged_tests": sorted(x["entry_id"] for x in out
                                     if x["unjudged_reason"] == REASON_TEST_NOT_RUN),
            "entries": out,
            "deferred_from_prompt": sorted(x["entry_id"] for x in out if not x["injected"])}
