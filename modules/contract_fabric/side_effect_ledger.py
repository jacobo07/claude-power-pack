"""Undeclared Side-Effect Ledger — DAIF-04 PART XXI runtime.

The contract fabric types what a provider PROMISES (outputs, postconditions) and the
breach detector catches a promise found false. Neither can see an action about which no
promise was ever made. This ledger closes that blind spot — the dual of the starved
field — by reconciling a provider's FULL observed effect set against its contract's
declared surface and recording every effect that was performed but never declared.

Operation (PART XXI §21.3):  UNDECLARED = OBSERVED - DECLARED.
Discipline: DEFAULT-RECORD (the inverse of the contract object's default-refuse) — an
observed effect the declared surface does not entail is recorded, never silently dropped;
absence of a declaration is never read as authorization.

Severity (§21.5):
  - undeclared effect WITHIN the authorized scope  -> "documentation" (amend the contract)
  - undeclared effect OUTSIDE the authorized scope  -> "escalation"    (a scope breach)

The ledger records and classifies; it neither authorizes nor punishes (§21.9). It is
append-only (§21.6): an entry, once recorded, is never deleted, because a repeated
undeclared effect is a design defect in the contract that is only legible across time.

Deterministic and stdlib-only: timestamps are caller-supplied, never read from a
wall-clock, so a run is reproducible and hermetically testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# DAIF-01 nested scope ladder, narrow -> wide. An effect's reach is one of these rungs.
SCOPE_LADDER = ["function", "file", "feature", "repo", "project", "power-pack", "universal"]

# The closed set of effect kinds a side effect may take (PART XXI §21.2).
EFFECT_KINDS = frozenset(
    {"state-write", "file-mutation", "external-call", "dispatch", "config-change"}
)

DOCUMENTATION = "documentation"  # in-scope undeclared effect
ESCALATION = "escalation"        # out-of-scope undeclared effect


def _rung(scope: str) -> int:
    """Rung index of a scope on the ladder. An unknown scope sorts as the widest rung —
    an effect whose reach cannot be placed is treated as the most suspicious, never the
    least, so a typo in a scope name can never silently narrow an effect into compliance.
    """
    try:
        return SCOPE_LADDER.index(scope)
    except ValueError:
        return len(SCOPE_LADDER)


@dataclass(frozen=True)
class Effect:
    """A typed side effect: what kind of action, on which resolvable target, reaching how
    far. Frozen so a declared surface and an observed set are compared by value, not identity.
    """

    kind: str
    target: str
    scope: str


@dataclass(frozen=True)
class LedgerEntry:
    """One recorded undeclared effect, fully attributed (§21.6)."""

    contract_id: str
    contract_version: str
    provider: str
    effect: Effect
    within_scope: bool
    authorized_scope: str
    severity: str
    ts: str


def reconcile(declared: Iterable[Effect], observed: Iterable[Effect]) -> list[Effect]:
    """UNDECLARED = OBSERVED - DECLARED.

    An observed effect is DECLARED iff the declared surface entails it: an identical kind
    and target whose declared reach is at least as wide as the effect's actual reach
    (a contract authorized to write at 'repo' reach entails a write observed at 'file'
    reach). Everything the surface does not entail is returned, in observed order.
    """
    dset = list(declared)
    undeclared: list[Effect] = []
    for eff in observed:
        entailed = any(
            d.kind == eff.kind and d.target == eff.target and _rung(d.scope) >= _rung(eff.scope)
            for d in dset
        )
        if not entailed:
            undeclared.append(eff)
    return undeclared


class SideEffectLedger:
    """Append-only ledger of undeclared side effects. Silent on the compliant, loud on
    the surprise: an effect the provider both performed and declared produces no entry.
    """

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    def record(
        self,
        contract_id: str,
        contract_version: str,
        provider: str,
        authorized_scope: str,
        declared: Iterable[Effect],
        observed: Iterable[Effect],
        ts: str,
    ) -> list[LedgerEntry]:
        """Reconcile observed against declared, record every undeclared effect classified
        by severity, and return the entries appended by this call (never the whole ledger).
        """
        cap = _rung(authorized_scope)
        appended: list[LedgerEntry] = []
        for eff in reconcile(declared, observed):
            within = _rung(eff.scope) <= cap
            entry = LedgerEntry(
                contract_id=contract_id,
                contract_version=contract_version,
                provider=provider,
                effect=eff,
                within_scope=within,
                authorized_scope=authorized_scope,
                severity=DOCUMENTATION if within else ESCALATION,
                ts=ts,
            )
            self._entries.append(entry)
            appended.append(entry)
        return appended

    def entries(self) -> list[LedgerEntry]:
        """A copy of the full ledger; the internal list is never exposed for mutation."""
        return list(self._entries)

    def escalations(self) -> list[LedgerEntry]:
        """Out-of-scope undeclared effects — scope breaches bound for owner_queue."""
        return [e for e in self._entries if e.severity == ESCALATION]

    def for_provider(self, provider: str) -> list[LedgerEntry]:
        """Every recorded undeclared effect attributed to one provider, across contracts —
        the view that makes a chronic, repeated undeclared effect legible (§21.6).
        """
        return [e for e in self._entries if e.provider == provider]
