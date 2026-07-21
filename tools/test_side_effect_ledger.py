#!/usr/bin/env python3
"""V-gate runner for the Undeclared Side-Effect Ledger (DAIF-04 PART XXI).

Reproducible, hermetic (timestamps are supplied, never read from a wall-clock). Verifies
the ledger's whole operation — UNDECLARED = OBSERVED - DECLARED — plus its default-record,
severity, append-only, and attribution invariants. Designed to be observed to refuse: the
declared-silent and scope-entailment gates fail loudly if the reconciliation over-records.

  V-SEL-UNDECLARED-RECORDED   an observed effect absent from the declared surface is recorded
  V-SEL-DECLARED-SILENT       an observed effect the surface entails produces NO entry
  V-SEL-SCOPE-ENTAILMENT      a wider declared reach entails a narrower observed one; not vice-versa
  V-SEL-ESCALATION            an undeclared effect beyond the authorized scope is an escalation
  V-SEL-DOC-IN-SCOPE          an undeclared effect within the authorized scope is a documentation debt
  V-SEL-APPEND-ONLY           record() accumulates; entries() hands back a copy, never the live list
  V-SEL-ATTRIBUTION           every entry carries contract id/version, provider, scope, and ts
  V-SEL-PROVIDER-VIEW         for_provider() isolates one provider's undeclared effects across contracts

Run:  python tools/test_side_effect_ledger.py
Exit: 0 iff every gate passes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.contract_fabric import Effect, SideEffectLedger, reconcile  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK  ] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def test_undeclared_recorded() -> None:
    # Arrange — a contract that declares one file-mutation; the provider also writes state.
    declared = [Effect("file-mutation", "src/app.py", "file")]
    observed = [Effect("file-mutation", "src/app.py", "file"),
                Effect("state-write", "cache/session", "file")]
    ledger = SideEffectLedger()
    # Act
    appended = ledger.record("C-1", "v1", "provider.alpha", "repo", declared, observed, "t0")
    # Assert — exactly the undeclared state-write is recorded.
    if len(appended) == 1 and appended[0].effect.kind == "state-write":
        _ok("V-SEL-UNDECLARED-RECORDED", "1 undeclared effect (state-write) recorded")
    else:
        _fail("V-SEL-UNDECLARED-RECORDED", f"expected 1 state-write, got {appended}")


def test_declared_silent() -> None:
    # Arrange — every observed effect is entailed by the declared surface.
    declared = [Effect("file-mutation", "src/app.py", "repo"),
                Effect("external-call", "api.internal", "repo")]
    observed = [Effect("file-mutation", "src/app.py", "file"),
                Effect("external-call", "api.internal", "repo")]
    ledger = SideEffectLedger()
    # Act
    appended = ledger.record("C-2", "v1", "provider.beta", "repo", declared, observed, "t0")
    # Assert — nothing recorded; the ledger is silent on the compliant.
    if not appended and not ledger.entries():
        _ok("V-SEL-DECLARED-SILENT", "0 entries for a fully-declared run")
    else:
        _fail("V-SEL-DECLARED-SILENT", f"expected silence, recorded {appended}")


def test_scope_entailment() -> None:
    # Arrange — declared at 'repo' entails observed at 'file'; declared at 'file' does NOT
    # entail observed at 'project'.
    wider = reconcile([Effect("file-mutation", "x", "repo")],
                      [Effect("file-mutation", "x", "file")])
    narrower = reconcile([Effect("file-mutation", "x", "file")],
                         [Effect("file-mutation", "x", "project")])
    # Assert
    if wider == [] and len(narrower) == 1:
        _ok("V-SEL-SCOPE-ENTAILMENT", "wider declared entails narrower; narrower does not entail wider")
    else:
        _fail("V-SEL-SCOPE-ENTAILMENT", f"wider={wider} narrower={narrower}")


def test_escalation_out_of_scope() -> None:
    # Arrange — an undeclared effect reaching 'universal' under a 'repo'-authorized contract.
    ledger = SideEffectLedger()
    observed = [Effect("config-change", "~/.claude/settings.json", "universal")]
    # Act
    appended = ledger.record("C-3", "v1", "provider.gamma", "repo", [], observed, "t0")
    # Assert
    escs = ledger.escalations()
    if appended and appended[0].severity == "escalation" and len(escs) == 1:
        _ok("V-SEL-ESCALATION", "out-of-scope undeclared effect classed escalation")
    else:
        _fail("V-SEL-ESCALATION", f"expected escalation, got {appended}")


def test_documentation_in_scope() -> None:
    # Arrange — an undeclared but in-scope effect ('file' reach under 'repo' authority).
    ledger = SideEffectLedger()
    observed = [Effect("state-write", "cache/x", "file")]
    # Act
    appended = ledger.record("C-4", "v1", "provider.delta", "repo", [], observed, "t0")
    # Assert — documentation debt, not an escalation.
    if appended and appended[0].severity == "documentation" and not ledger.escalations():
        _ok("V-SEL-DOC-IN-SCOPE", "in-scope undeclared effect classed documentation debt")
    else:
        _fail("V-SEL-DOC-IN-SCOPE", f"expected documentation, got {appended}")


def test_append_only() -> None:
    # Arrange
    ledger = SideEffectLedger()
    ledger.record("C-5", "v1", "p", "repo", [], [Effect("dispatch", "agent.x", "file")], "t0")
    ledger.record("C-5", "v2", "p", "repo", [], [Effect("dispatch", "agent.y", "file")], "t1")
    # Act — mutate the returned copy; the live ledger must not change.
    snapshot = ledger.entries()
    snapshot.clear()
    # Assert
    if len(ledger.entries()) == 2:
        _ok("V-SEL-APPEND-ONLY", "two records accumulate; entries() is a copy")
    else:
        _fail("V-SEL-APPEND-ONLY", f"expected 2 durable entries, got {len(ledger.entries())}")


def test_attribution() -> None:
    # Arrange
    ledger = SideEffectLedger()
    ledger.record("C-6", "v3", "provider.epsilon", "feature", [],
                  [Effect("external-call", "svc", "project")], "2026-07-21T00:00:00Z")
    # Act
    e = ledger.entries()[0]
    # Assert — every attribution field is populated.
    ok = all([e.contract_id == "C-6", e.contract_version == "v3",
              e.provider == "provider.epsilon", e.authorized_scope == "feature",
              e.ts == "2026-07-21T00:00:00Z", e.severity == "escalation"])
    if ok:
        _ok("V-SEL-ATTRIBUTION", "contract id/version, provider, scope, ts all present")
    else:
        _fail("V-SEL-ATTRIBUTION", f"attribution incomplete: {e}")


def test_provider_view() -> None:
    # Arrange — two providers, two contracts, three undeclared effects.
    ledger = SideEffectLedger()
    ledger.record("C-7", "v1", "prov.a", "repo", [], [Effect("state-write", "a", "file")], "t0")
    ledger.record("C-8", "v1", "prov.b", "repo", [], [Effect("state-write", "b", "file")], "t1")
    ledger.record("C-9", "v1", "prov.a", "repo", [], [Effect("state-write", "c", "file")], "t2")
    # Act
    a_view = ledger.for_provider("prov.a")
    # Assert
    if len(a_view) == 2 and all(x.provider == "prov.a" for x in a_view):
        _ok("V-SEL-PROVIDER-VIEW", "for_provider isolates one provider's effects across contracts")
    else:
        _fail("V-SEL-PROVIDER-VIEW", f"expected 2 for prov.a, got {len(a_view)}")


def main() -> int:
    print("== side_effect_ledger (DAIF-04 PART XXI) ==")
    for t in (test_undeclared_recorded, test_declared_silent, test_scope_entailment,
              test_escalation_out_of_scope, test_documentation_in_scope, test_append_only,
              test_attribution, test_provider_view):
        t()
    total = _passes + _fails
    print(f"\nSEL_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
