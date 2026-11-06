"""Family done-gate (spec 2026-09-24, slice S6) -- REPORT-ONLY.

Judges every ACTIVE entry of a family's newest generation against a subject
repo. The spec keeps blocking as a separate Owner decision (§7: "arranca como
informe"), so this module has no enforce mode at all: `would_block` states
what enforcement would have done, and nothing here can refuse anything.

Per entry, one verdict:

  APPLIED_VERIFIED  an evaluable check (file/glob/regex) passed
  VIOLATED          an evaluable check failed
  DELEGATED         a registered verifier / test owns the verdict (the repo's)
  NOT_APPLICABLE    declared by the caller WITH a reason
  UNJUDGED          prose or empty check, an N/A without a reason, an
                    unreadable registry, or the instrument's own failure --
                    never counted as applied

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
# Rule content reachability (spec baseline-rule-content-reachability): how the entry's TEXT reached the builder.
INJECTED = "INJECTED"      # shown in the prompt block
RETRIEVED = "RETRIEVED"    # deferred, then read through `family_baseline.py rule` (ledgered for this generation)
NAME_ONLY = "NAME_ONLY"    # deferred and never read: only its id was ever supplied

_FROM_CHECK = {ck.PASS: APPLIED_VERIFIED, ck.FAIL: VIOLATED, ck.DELEGATED: DELEGATED}


def judge(family: str, repo_root: str, registry: str | None = None,
          root: str | None = None, not_applicable: dict | None = None) -> dict:
    gens = bl.generations(family, root)
    if not gens:
        return {"family": family, "judged_under": None, "generation_sha256": None,
                "chain_ok": None, "status": NO_BASELINE, "report_only": True,
                "would_block": False, "entries": [], "deferred_from_prompt": [], "knowledge_unmet": []}
    n = gens[-1]
    stamp = "%s/B%d" % (family, n)
    sha = bl.generation_sha256(family, n, root)
    active = bl.active_entries(family, root)
    injected = {e.get("id") for e in sel.select_for_injection(active).injected}
    retrieved = bl.retrieved_ids(family, sha)   # spec baseline-rule-content-reachability
    na = not_applicable or {}
    out = []
    for e in active:
        ident = e.get("id")
        reason = na.get(ident)
        if ident in na and str(reason or "").strip():
            verdict, detail, outcome = NOT_APPLICABLE, str(reason).strip(), None
        elif ident in na:
            verdict, detail, outcome = UNJUDGED, "declared not applicable with no reason", None
        else:
            r = ck.evaluate(e, repo_root, registry)
            outcome = r.outcome
            verdict = _FROM_CHECK.get(r.outcome, UNJUDGED)
            detail = r.detail
        content = INJECTED if ident in injected else (RETRIEVED if ident in retrieved else NAME_ONLY)
        out.append({"entry_id": ident, "verdict": verdict, "check_outcome": outcome,
                    "detail": detail, "requirement": e.get("requirement"),
                    "injected": ident in injected, "content": content, "source": SOURCE,
                    "judged_under": stamp})
    return {"family": family, "judged_under": stamp,
            "generation_sha256": sha,
            "chain_ok": rt.verify_chain(family, root).ok, "status": JUDGED,
            "report_only": True,
            "would_block": any(x["verdict"] in (VIOLATED, UNJUDGED) for x in out),
            "entries": out,
            "deferred_from_prompt": sorted(x["entry_id"] for x in out if not x["injected"]),
            # A rule seen only by NAME and not otherwise proven applied/not-applicable is an explicit unmet knowledge
            # obligation, never a silent pass (brief XXIX: "a name in a prompt is not proof its rule was supplied").
            "knowledge_unmet": sorted(x["entry_id"] for x in out if x["content"] == NAME_ONLY
                                      and x["verdict"] not in (APPLIED_VERIFIED, NOT_APPLICABLE))}
