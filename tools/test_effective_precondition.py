"""V-PRECOND-* -- can a perfect score still buy its way past delivery?

`is_done` was a weighted score with a threshold, so every question it
asked was about the artifact in the repository and none about the artifact
that runs. Replayed against a claim a prior session actually made -- the
quoted-path leadingExe fix is shipped -- the score model returns OQS 100
and Done, while the bytes executing that hook are measurably a different
version and have been for six days.

A weight cannot express that. Losing one check and clearing 70 on the rest
is right for quality and wrong for delivery: a change that does not govern
behaviour is not 70% delivered. So the veto is a precondition evaluated
beside the score, never inside it.

These gates exist because the failure mode of a delivery gate is not that
it misses a shadow -- it is that it fires on documentation, gets called
noise, and is switched off. Every "blocks X" below is therefore paired
with a "does NOT block Y", and the applicability boundary is pinned from
both directions.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

from modules.output_contracts import certify, get_contract  # noqa: E402
from modules.output_contracts import preconditions as pre  # noqa: E402
from modules.output_contracts import is_done, is_done_for_tier  # noqa: E402

EXPECTED_GATES = 23
_passes: list[str] = []
_fails: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


PERFECT = {"file_path": "hooks/x.js", "content": "clean source",
           "syntax_test_passed": True, "tests_test_passed": True}


def _ctx(scope: str, artifacts=("hooks/x.js",)) -> dict:
    return dict(PERFECT, claim_scope=scope, artifacts=list(artifacts))


def _res(mapping: dict):
    return lambda arts: {a: mapping[a] for a in arts if a in mapping}


def _boom(_arts):
    raise RuntimeError("detector unavailable")


def main() -> int:
    shadow = _res({"hooks/x.js": "SHADOWED"})
    live = _res({"hooks/x.js": "EFFECTIVE"})
    gone = _res({"hooks/x.js": "ABSENT_RUNNING"})

    # --- direction: the verdict was right, the advice was backwards -----
    # Every one of these still blocks a runtime claim -- the claimed bytes
    # are not the executing ones under any of them. What must differ is
    # what the message tells the reader to DO, because for two of the four
    # the previous single sentence pointed at overwriting newer committed
    # work belonging to somebody else.
    for status, want, forbid in (
        ("STRANDED", "has not reached the running tree", "overwrite"),
        ("AHEAD_OF_HERE", "integrate here", "has not reached"),
        ("DIVERGED", "is a decision", "has not reached"),
        ("FOREIGN_EDIT", "uncommitted work", "has not reached"),
    ):
        v = certify("code", _ctx("runtime"), _res({"hooks/x.js": status}))
        msg = v["preconditions"][0]["message"]
        if not v["done"] and want in msg and forbid not in msg:
            _ok("V-PRECOND-DIRECTION-" + status.replace("_", "-"),
                f"blocks, and says {want!r} rather than {forbid!r}")
        else:
            _fail("V-PRECOND-DIRECTION-" + status.replace("_", "-"),
                  f"done={v['done']} msg={msg!r}")

    # A status this module has never heard of must not pass by falling off
    # the end of a list. The detector is free to grow verdicts; learning
    # about them late has to cost a false red, never a false green.
    v = certify("code", _ctx("runtime"), _res({"hooks/x.js": "BRAND_NEW"}))
    if not v["done"] and "unrecognised" in v["preconditions"][0]["message"]:
        _ok("V-PRECOND-UNKNOWN-STATUS-FAILS-CLOSED",
            "an unmapped effective-state verdict blocks and names itself")
    else:
        _fail("V-PRECOND-UNKNOWN-STATUS-FAILS-CLOSED",
              f"done={v['done']} msg={v['preconditions'][0]['message']!r}")

    # What runs is this checkout's last COMMIT. If the claimed file has
    # uncommitted changes, the claim is about bytes nobody executes -- and
    # the honest verdict is that it cannot be confirmed, not that delivery
    # failed.
    v = certify("code", _ctx("runtime"), _res({"hooks/x.js": "LOCAL_EDIT"}))
    p = v["preconditions"][0]
    if not v["done"] and p["verdict"] == pre.UNVERIFIED:
        _ok("V-PRECOND-LOCAL-EDIT-UNVERIFIED",
            "an uncommitted working copy yields UNVERIFIED and blocks; it "
            "used to pass, because the audit's 'nothing owed to production' "
            "answered a different question than the claim did")
    else:
        _fail("V-PRECOND-LOCAL-EDIT-UNVERIFIED",
              f"done={v['done']} verdict={p['verdict']}")

    # --- the core claim: score cannot buy out delivery -----------------
    v = certify("code", _ctx("runtime"), shadow)
    if v["oqs"] == 100 and v["oqs_pass"] and not v["done"]:
        _ok("V-PRECOND-SCORE-CANNOT-BUY-DELIVERY",
            "OQS 100 clears the threshold and Done is still withheld -- the "
            "veto is beside the score, not a weight inside it")
    else:
        _fail("V-PRECOND-SCORE-CANNOT-BUY-DELIVERY",
              f"oqs={v['oqs']} oqs_pass={v['oqs_pass']} done={v['done']}")

    v = certify("code", _ctx("runtime"), live)
    if v["done"] and v["preconditions"][0]["verdict"] == pre.PASS:
        _ok("V-PRECOND-EFFECTIVE-PASSES",
            "the same claim over EFFECTIVE bytes is Done -- the gate is not "
            "simply refusing every runtime claim")
    else:
        _fail("V-PRECOND-EFFECTIVE-PASSES",
              f"done={v['done']} verdict={v['preconditions'][0]['verdict']}")

    v = certify("code", _ctx("runtime"), gone)
    if not v["done"]:
        _ok("V-PRECOND-ABSENT-VETOES",
            "an artifact missing from the executing tree blocks too; only "
            "SHADOWED was ever driven by live data")
    else:
        _fail("V-PRECOND-ABSENT-VETOES", "ABSENT_RUNNING certified as Done")

    # --- applicability, pinned from both sides -------------------------
    for scope, want_done in (("source", True), ("repository", True),
                             ("integration", True), ("production", False)):
        v = certify("code", _ctx(scope), shadow)
        gate = f"V-PRECOND-SCOPE-{scope.upper()}"
        if v["done"] is want_done:
            verd = v["preconditions"][0]["verdict"]
            _ok(gate, f"scope {scope!r} -> done={want_done} ({verd})")
        else:
            _fail(gate, f"scope {scope!r} gave done={v['done']}, "
                        f"wanted {want_done}")

    v = certify("docs", _ctx("runtime"), shadow)
    if v["done"] and not v["preconditions"]:
        _ok("V-PRECOND-DOCS-EXEMPT",
            "a documentation contract declares no precondition, so a runtime "
            "scope cannot make prose owe delivery proof")
    else:
        _fail("V-PRECOND-DOCS-EXEMPT",
              f"docs blocked: done={v['done']} preconds={v['preconditions']}")

    if not (get_contract("docs") or {}).get("preconditions") and \
            (get_contract("code") or {}).get("preconditions"):
        _ok("V-PRECOND-DECLARED-NARROWLY",
            "code declares the precondition and docs does not -- a primitive "
            "declared on no contract protects nothing, and on every contract "
            "gets disabled")
    else:
        _fail("V-PRECOND-DECLARED-NARROWLY",
              "the declaration set is wrong in one direction or the other")

    # --- unknown is never pass -----------------------------------------
    v = certify("code", _ctx("runtime", artifacts=()), shadow)
    r = v["preconditions"][0]
    if r["verdict"] == pre.UNVERIFIED and not v["done"]:
        _ok("V-PRECOND-NO-ARTIFACT-UNVERIFIED",
            "a live claim naming no artifact is UNVERIFIED and blocks; "
            "nothing to compare is not the same as nothing wrong")
    else:
        _fail("V-PRECOND-NO-ARTIFACT-UNVERIFIED",
              f"verdict={r['verdict']} done={v['done']}")

    v = certify("code", _ctx("runtime"), _boom)
    r = v["preconditions"][0]
    if r["verdict"] == pre.UNVERIFIED and not v["done"]:
        _ok("V-PRECOND-DETECTOR-FAILURE-UNVERIFIED",
            "a detector that raises yields UNVERIFIED, not PASS -- an "
            "unavailable instrument must never certify")
    else:
        _fail("V-PRECOND-DETECTOR-FAILURE-UNVERIFIED",
              f"verdict={r['verdict']} done={v['done']}")

    r = pre.evaluate({"type": "time_travel"}, _ctx("runtime"), live)
    if r["verdict"] == pre.VETO:
        _ok("V-PRECOND-UNKNOWN-TYPE-VETOES",
            "an unrecognised precondition blocks, inverting the scorer's "
            "fail-open: a newer contract handed this validator a requirement "
            "it cannot evaluate")
    else:
        _fail("V-PRECOND-UNKNOWN-TYPE-VETOES",
              f"unknown precondition returned {r['verdict']}")

    unknown_scope = certify("code", _ctx("banana"), shadow)
    if unknown_scope["claim_scope"] == pre.DEFAULT_SCOPE and \
            unknown_scope["done"]:
        _ok("V-PRECOND-BAD-SCOPE-NOT-PROMOTED",
            f"an unrecognised scope falls back to {pre.DEFAULT_SCOPE!r}, not "
            "to the strongest -- defaulting to runtime would make every "
            "deliverable owe proof and the veto would be turned off")
    else:
        _fail("V-PRECOND-BAD-SCOPE-NOT-PROMOTED",
              f"scope={unknown_scope['claim_scope']} done={unknown_scope['done']}")

    # --- the legacy API inherits it, unedited --------------------------
    done, oqs = is_done("code", _ctx("runtime", artifacts=()))
    if oqs == 100 and not done:
        _ok("V-PRECOND-LEGACY-IS-DONE-INHERITS",
            "is_done() blocks without any caller being edited; a protection "
            "reaching only updated callers is the prose problem with an API")
    else:
        _fail("V-PRECOND-LEGACY-IS-DONE-INHERITS", f"done={done} oqs={oqs}")

    passed, oqs, floor = is_done_for_tier("code", _ctx("runtime",
                                                       artifacts=()), 1)
    if oqs >= floor and not passed:
        _ok("V-PRECOND-TIER-INHERITS",
            f"the tier path blocks too (oqs {oqs} >= floor {floor}); a second "
            "entry point that skipped the veto would be the whole hole")
    else:
        _fail("V-PRECOND-TIER-INHERITS",
              f"passed={passed} oqs={oqs} floor={floor}")

    # --- no precondition declared -> byte-for-byte prior behaviour -----
    # The claim is that an undeclared contract is UNAFFECTED -- which is a
    # statement about blockers, not about Done. The first spelling asserted
    # done is True and failed, because a code-shaped ctx scores 30 against
    # the test contract: a score failure read as a precondition failure,
    # which is exactly the conflation this whole file exists to separate.
    before = certify("test", _ctx("runtime"), shadow)
    if not before["preconditions"] and not before["blockers"] \
            and before["done"] == before["oqs_pass"]:
        _ok("V-PRECOND-UNDECLARED-UNCHANGED",
            f"the test contract declares no precondition, contributes no "
            f"blocker, and its Done still equals its score verdict "
            f"(oqs={before['oqs']}) -- untouched by this change")
    else:
        _fail("V-PRECOND-UNDECLARED-UNCHANGED",
              f"preconds={before['preconditions']} "
              f"blockers={before['blockers']} done={before['done']} "
              f"oqs_pass={before['oqs_pass']}")

    # --- live coherence: the real resolver, real state -----------------
    try:
        real = certify("code", _ctx("runtime",
                                    artifacts=("hooks/bug-hunter-ceps-bridge.js",)))
        verd = real["preconditions"][0]["verdict"]
        known = {pre.PASS, pre.VETO, pre.UNVERIFIED, pre.NOT_APPLICABLE}
        if verd in known:
            _ok("V-PRECOND-LIVE-MEASURED",
                f"the real detector answers {verd} for a real registered hook "
                f"(done={real['done']}) -- the default resolver is wired, not "
                "just the injected one")
        else:
            _fail("V-PRECOND-LIVE-MEASURED", f"unknown verdict {verd}")
    except Exception as exc:
        _fail("V-PRECOND-LIVE-MEASURED",
              f"default resolver raised {exc.__class__.__name__}: {exc}")

    ran = len(_passes) + len(_fails)
    print(f"\nPRECOND_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


def pre_score(name: str, ctx: dict) -> int:
    from modules.output_contracts import score
    return score(name, ctx)


if __name__ == "__main__":
    raise SystemExit(main())
