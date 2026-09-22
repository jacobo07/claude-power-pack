#!/usr/bin/env python3
"""V-gates for capability CONSUMPTION (Mission 002, Slice 3).

`test_capability_invocation.py` proved CALLABLE. This gate proves the next rung
and refuses to let it be confused with the previous one: a real construction
stage invokes the capability and a real downstream artifact CHANGES because of
the answer.

The stage is KARIMO's PRD parser -- the only place in this estate where product
constraints actually exist. Both of its renderers are pure functions of the
baseline, and one of them (`constraints_block`) is what the live
`UserPromptSubmit` sentinel emits, so consumption reaches the running system
rather than a CLI nobody invokes.

WHAT IS PINNED HERE
-------------------
  * an applicable PRD gets a decision, and a NON-applicable one does not;
  * the decision reaches BOTH renderers -- the artifact and the live block;
  * `content_sha256` does NOT move, so no previously-stored baseline is
    invalidated by this feature existing;
  * the rendering cannot lie: a set is never collapsed to a winner, an approval
    requirement never reads as approved, and a conflict names no leader;
  * a broken capability cannot break a PRD parse.

The rendering rules are driven through SYNTHETIC decision entries. That is
deliberate: `REQUIRE_APPROVAL` and a multi-topology `RECOMMEND` cannot be
produced on demand from prose without encoding the resolver's policy into a
second place, and a renderer that mishandles them would otherwise go unmeasured
until the day it matters.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_PASS = 0
_FAIL = 0


def _ok(gate: str, evidence: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _FAIL
    _FAIL += 1
    print(f"  FAIL {gate}: {diag}")


def _load_prd_parser():
    """Load a module whose package directory name `import` cannot spell.

    `karimo-harness` contains a hyphen. The module MUST be registered in
    `sys.modules` BEFORE `exec_module`, because `@dataclass` resolves
    `sys.modules.get(cls.__module__).__dict__` and a module absent from the
    table raises an AttributeError pointing nowhere near the cause. Recorded as
    S7 in the UACF adjudication; applied here rather than rediscovered.
    """
    path = _ROOT / "modules" / "karimo-harness" / "prd_parser.py"
    name = "karimo_prd_parser"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


P = _load_prd_parser()

SIGNUP_PRD = """PRD: QuickLease tenant portal
- The product must support sign up for new landlords.
- Users create an account before listing a property.
- The system must handle personal data under GDPR.
- Multi-tenant workspace for agencies.
"""

BATCH_PRD = """PRD: Nightly batch reconciliation job
- The job must reconcile ledger rows every night at 02:00.
- It must not exceed 400 ms per row.
- Output a CSV report to the archive bucket.
"""

CAP = "surface_architecture"


def gate_applicable_gets_a_decision() -> None:
    b = P.parse(SIGNUP_PRD, source_label="V-CON")
    found = (b.get("capability_decisions") or {}).get(CAP)
    if not found:
        _fail("V-CON-APPLICABLE", "no decision attached to a signup PRD")
        return
    if found.get("status") != "invoked":
        _fail("V-CON-APPLICABLE",
              f"status={found.get('status')} note={found.get('note')}")
        return
    if not found.get("outcome"):
        _fail("V-CON-APPLICABLE", "invoked but carries no outcome")
        return
    _ok("V-CON-APPLICABLE",
        f"signup PRD -> {CAP} invoked, outcome={found['outcome']}, "
        f"because: {found.get('selected_because', '')[:60]}")


def gate_non_applicable_is_not_polluted() -> None:
    """A batch job must not inherit entry-surface obligations."""
    b = P.parse(BATCH_PRD, source_label="V-CON")
    found = (b.get("capability_decisions") or {}).get(CAP)
    if not found:
        _fail("V-CON-NOT-APPLICABLE", "capability was never even considered")
        return
    if found.get("status") == "invoked":
        _fail("V-CON-NOT-APPLICABLE",
              "batch PRD was handed a surface decision")
        return
    if "not applicable" not in (found.get("note") or ""):
        _fail("V-CON-NOT-APPLICABLE", f"no reason recorded: {found}")
        return
    block = P.constraints_block(b)
    leaked = [w for w in ("topologies", "NOT APPROVED", "abstained")
              if w in block]
    if leaked:
        _fail("V-CON-NOT-APPLICABLE", f"decision vocabulary leaked: {leaked}")
        return
    _ok("V-CON-NOT-APPLICABLE",
        "batch PRD -> not applicable, reason recorded, no obligations rendered")


def gate_both_legs_carry_it() -> None:
    b = P.parse(SIGNUP_PRD, source_label="V-CON")
    live = P.constraints_block(b)
    art = P.blueprint_from_baseline(b)
    if "CAPABILITY DECISIONS" not in live:
        _fail("V-CON-LIVE-LEG", "the block the hook emits carries no decision")
    else:
        _ok("V-CON-LIVE-LEG",
            "constraints_block (emitted by the live UserPromptSubmit sentinel) "
            "carries the decision")
    if "Capability decisions" not in art:
        _fail("V-CON-ARTIFACT-LEG", "BLUEPRINT.md unchanged by the decision")
    else:
        _ok("V-CON-ARTIFACT-LEG", "BLUEPRINT.md renders the decision")


def gate_hash_is_stable() -> None:
    """Enrichment must not move `content_sha256`.

    Computed the same way the parser does, minus the enrichment step. If these
    diverge, every baseline stored before this feature existed is retroactively
    invalidated -- a silent, unrecoverable break in a content-addressed record.
    """
    sections = P.classify(P.tokenize(SIGNUP_PRD))
    buckets = P.extract(sections)
    bare = P.schema_map(SIGNUP_PRD, sections, buckets, "V-CON", True)
    rich = P.parse(SIGNUP_PRD, source_label="V-CON")
    if bare["content_sha256"] != rich["content_sha256"]:
        _fail("V-CON-HASH-STABLE",
              f"{bare['content_sha256'][:12]} != {rich['content_sha256'][:12]}")
    elif "capability_decisions" not in rich:
        _fail("V-CON-HASH-STABLE", "hash stable because nothing was attached")
    else:
        _ok("V-CON-HASH-STABLE",
            f"sha {rich['content_sha256'][:12]} unchanged WITH a decision "
            "attached -- prior baselines stay valid")


def gate_schema_accepts_it() -> None:
    b = P.parse(SIGNUP_PRD, source_label="V-CON")
    ok, why = P._validate(b)
    if not ok:
        _fail("V-CON-SCHEMA", f"enriched baseline fails its own schema: {why}")
    elif "jsonschema" not in why:
        _fail("V-CON-SCHEMA",
              f"validated by the FALLBACK, which does not enforce "
              f"additionalProperties: {why}")
    else:
        _ok("V-CON-SCHEMA", f"enriched baseline validates strictly ({why})")


def _synthetic(entry: dict) -> list:
    return P.capability_lines({"capability_decisions": {CAP: entry}})


def gate_set_is_not_collapsed() -> None:
    """Composability must survive the rendering boundary."""
    lines = "\n".join(_synthetic({
        "status": "invoked", "outcome": "RECOMMEND",
        "decision": {"archetype": "", "archetypes": ["artifact_first",
                                                     "work_first"]}}))
    if "artifact_first" in lines and "work_first" in lines:
        _ok("V-CON-SET-NOT-WINNER",
            "both justified topologies rendered; no winner invented")
    else:
        _fail("V-CON-SET-NOT-WINNER", f"set collapsed: {lines!r}")


def gate_approval_is_not_approval() -> None:
    lines = "\n".join(_synthetic({
        "status": "invoked", "outcome": "REQUIRE_APPROVAL",
        "decision": {"reason": "regulated surface"}}))
    if "NOT APPROVED" in lines:
        _ok("V-CON-APPROVAL",
            "REQUIRE_APPROVAL renders as unapproved -- dispatch grants nothing")
    else:
        _fail("V-CON-APPROVAL", f"approval requirement rendered as: {lines!r}")


def gate_conflict_names_no_leader() -> None:
    lines = "\n".join(_synthetic({
        "status": "invoked", "outcome": "UNDETERMINED",
        "decision": {"archetype": "artifact_first",
                     "archetypes": ["artifact_first", "work_first"],
                     "reason": "contradictory evidence"}}))
    if "artifact_first" in lines:
        _fail("V-CON-CONFLICT",
              "UNDETERMINED rendered a leader -- conflict silently resolved")
    elif "no leader named" in lines:
        _ok("V-CON-CONFLICT",
            "UNDETERMINED names no leader even when one is present on the record")
    else:
        _fail("V-CON-CONFLICT", f"unexpected rendering: {lines!r}")


def gate_broken_capability_cannot_break_the_parse() -> None:
    """The PRD stage owes nothing to a capability."""
    import modules.capability_runtime.enrichment as E
    original = E.decisions_for_artifact

    def explode(*a, **k):
        raise RuntimeError("capability layer is down")

    E.decisions_for_artifact = explode
    try:
        b = P.parse(SIGNUP_PRD, source_label="V-CON")
    except Exception as e:  # noqa: BLE001
        _fail("V-CON-FAILOPEN", f"a broken capability broke the parse: {e!r}")
        return
    finally:
        E.decisions_for_artifact = original

    if b.get("capability_decisions"):
        _fail("V-CON-FAILOPEN", "decisions attached despite the failure")
    elif not b.get("content_sha256"):
        _fail("V-CON-FAILOPEN", "baseline damaged by the failure")
    else:
        _ok("V-CON-FAILOPEN",
            "capability layer down -> PRD parses normally, no decision, no raise")

    # Control: with the real function restored, a decision comes back. Without
    # this, a permanently-broken enrichment would satisfy the gate above.
    b2 = P.parse(SIGNUP_PRD, source_label="V-CON")
    if b2.get("capability_decisions"):
        _ok("V-CON-FAILOPEN-CONTROL", "restored -> decision attached again")
    else:
        _fail("V-CON-FAILOPEN-CONTROL", "no decision after restore")


def main() -> int:
    print("V-CON -- capability consumption through the PRD construction stage")
    gate_applicable_gets_a_decision()
    gate_non_applicable_is_not_polluted()
    gate_both_legs_carry_it()
    gate_hash_is_stable()
    gate_schema_accepts_it()
    gate_set_is_not_collapsed()
    gate_approval_is_not_approval()
    gate_conflict_names_no_leader()
    gate_broken_capability_cannot_break_the_parse()
    total = _PASS + _FAIL
    print(f"CON_PASS={_PASS}/{total}  threshold={total}/{total}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
