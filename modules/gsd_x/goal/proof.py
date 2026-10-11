#!/usr/bin/env python3
"""Proof-conserving convergence: the additive event vocabulary (spec S2-S13).

Four event types, owned here and nowhere else:

  * `obligation.contract` -- the typed proof contract for an obligation (spec S7)
  * `proof.produced`      -- a gate receipt: a proof exists for a candidate (spec S6)
  * `proof.inherited`     -- the reconciler re-derived the premises and inherits it
  * `proof.invalidated`   -- a certificate stopped holding, with the reason

Forward-compat contract (the words of evidence.py): old readers skip these types
(contract.project and every legacy projection ignore an unknown type), and no
pre-PCC code ever consulted them, so an old reader loses nothing it ever had. In
Phase 2 no legacy caller consumes this module either: zero behaviour change.

A payload carries `v`. A `v` greater than SUPPORTED_V is UNKNOWN to this engine: it
is listed in `ProofLedger.unsupported` and never raised, because a newer engine's
event must not stop an older one from reading or sweeping the goal. A malformed
payload of an own type raises GoalLogCorrupt, but only from `project_proofs`.

The event is a CLAIM. State is computed from observed premises, never from what an
event says about itself; `actor` is self-asserted, so the chain proves integrity,
not authorship.
"""
from __future__ import annotations

import hashlib
import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import git_state
from .contract import GoalState, project
from .epoch import _debris
from .convergence import SATISFIED, project_convergence
from .log import GoalLog, GoalLogCorrupt, GoalLogError
from .log import _canonical

CONTRACT = "obligation.contract"
PRODUCED = "proof.produced"
INHERITED_EV = "proof.inherited"
INVALIDATED = "proof.invalidated"
NEW_TYPES = (CONTRACT, PRODUCED, INHERITED_EV, INVALIDATED)

SUPPORTED_V = 1

# Rollback switches (spec S10). Env only, read at CALL time, never cached. ON iff the
# variable is unset/empty or one of on|1|true|yes (after strip + lower); every other
# value -- off, 0, false, a typo -- is OFF, so a typo falls back to the legacy path.
FRONTIER_SWITCH = "GSDX_FRONTIER"
INHERITANCE_SWITCH = "GSDX_PROOF_INHERITANCE"
_ON_VALUES = frozenset({"", "on", "1", "true", "yes"})


def switch_on(name: str) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return True
    return raw.strip().lower() in _ON_VALUES


def inheritance_enabled() -> bool:
    return switch_on(INHERITANCE_SWITCH)

REQUIRED_FIELDS = {
    CONTRACT: ("v", "claim_id", "obligation", "elements", "combine"),
    PRODUCED: ("v", "claim_id", "candidate", "binding", "revision", "strength", "source"),
    INHERITED_EV: ("v", "claim_id", "certificate", "candidate", "premises"),
    INVALIDATED: ("v", "claim_id", "certificate", "reason"),
}


class ProofRefused(GoalLogError):
    """The PCC event would be unreadable or unwritable by this engine."""


def check_payload(type_: str, data) -> bool:
    """True for a readable v1 payload, False for a newer `v`, ValueError when malformed."""
    if type_ not in REQUIRED_FIELDS:
        raise ValueError(f"{type_!r} is not a PCC event type")
    if not isinstance(data, dict):
        raise ValueError("payload is not an object")
    v = data.get("v")
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError("v is missing or not an int")
    if v > SUPPORTED_V:
        return False
    missing = [k for k in REQUIRED_FIELDS[type_] if k not in data]
    if missing:
        raise ValueError(f"missing {', '.join(missing)}")
    if type_ == CONTRACT:
        el = data["elements"]
        if not isinstance(el, list) or not el or not all(isinstance(x, dict) for x in el):
            raise ValueError("elements must be a non-empty list of objects")
    return True


@dataclass
class ProofLedger:
    contracts: list = field(default_factory=list)
    produced: list = field(default_factory=list)
    inherited: list = field(default_factory=list)
    invalidated: list = field(default_factory=list)
    unsupported: list = field(default_factory=list)       # seqs of events with a newer v


def project_proofs(state: GoalState) -> ProofLedger:
    ledger = ProofLedger()
    slots = {CONTRACT: ledger.contracts, PRODUCED: ledger.produced,
             INHERITED_EV: ledger.inherited, INVALIDATED: ledger.invalidated}
    for ev in state.events:
        if ev.type not in NEW_TYPES:
            continue
        try:
            readable = check_payload(ev.type, ev.data)
        except (ValueError, KeyError, TypeError) as exc:
            raise GoalLogCorrupt(f"{state.goal_id} seq {ev.seq}: malformed {ev.type} "
                                 f"({exc})") from exc
        if not readable:
            ledger.unsupported.append(ev.seq)
            continue
        slots[ev.type].append({"seq": ev.seq, "actor": ev.actor, "ts": ev.ts,
                               "data": dict(ev.data)})
    return ledger


def append_pcc(log: GoalLog, state: GoalState, type_: str, data: dict, actor: str) -> ProofLedger:
    """Append one PCC event through the CAS writer, or refuse it with the reason."""
    if type_ not in NEW_TYPES:
        raise ProofRefused(f"{type_!r} is not a PCC event type")
    try:
        readable = check_payload(type_, data)
    except ValueError as exc:
        raise ProofRefused(f"{type_}: {exc}") from exc
    if not readable:
        raise ProofRefused(f"{type_}: v {data.get('v')} is newer than SUPPORTED_V={SUPPORTED_V}; "
                           "a writer never writes a version it cannot read")
    log.append(state.last_seq + 1, type_, data, actor)
    return project_proofs(project(log))


# --- proof states (spec S1, S2, S6) ---------------------------------------------------
# A state is DERIVED from observed premises and never stored on an obligation; the
# disposition machinery of convergence.py is not touched.

PS_FRESH, PS_INHERITED, PS_SUPERSEDED = "FRESH", "INHERITED", "SUPERSEDED"
PS_STALE, PS_UNKNOWN = "STALE", "UNKNOWN"
PROOF_STATES = (PS_FRESH, PS_INHERITED, PS_SUPERSEDED, PS_STALE, PS_UNKNOWN)
NOT_APPLICABLE = "NOT_APPLICABLE"          # the obligation is not an open or proven claim
UNKNOWN_PREFIX = "unknown:"


def claim_id(obligation) -> str:
    """Identity of WHAT is claimed: id, plane, text, gate command, gate pin and class."""
    body = {"id": obligation.identifier, "plane": obligation.plane, "text": obligation.text,
            "done_gate": obligation.done_gate, "gate_pin": [list(p) for p in obligation.gate_pin],
            "gate_class": obligation.gate_class}
    return hashlib.sha256(_canonical(body)).hexdigest()[:24]


def legacy_contract(obligation) -> dict:
    """The contract every pre-PCC obligation already is: one gate command, never inherited."""
    return {"v": 1, "claim_id": claim_id(obligation), "obligation": obligation.identifier,
            "combine": "AND",
            "elements": [{"oracle": obligation.gate_class, "command": obligation.done_gate,
                          "gate_pin": [list(p) for p in obligation.gate_pin],
                          "causal_paths": [], "env_deps": [], "risk_tags": [],
                          "nondeterministic": False, "inheritability": "never"}]}


def binding(tree_hash: str, fingerprint: str | None = None) -> dict:
    """A scheme-tagged candidate binding: the whole tree today, a causal fingerprint in Phase 4."""
    if fingerprint is not None:
        return {"scheme": "causal", "value": fingerprint}
    return {"scheme": "tree", "value": tree_hash}


def _is_unknown(value) -> bool:
    return not isinstance(value, str) or not value or value.startswith(UNKNOWN_PREFIX)


# --- certificate validity (S3), fingerprints (S4), supersession (S2) --------------------

EQUAL, CHANGED, UNKNOWN_OBS = "equal", "changed", "unknown"
PREMISES = ("claim", "revision", "gate_pin", "fingerprint", "environment", "policy")
POLICY_VERSION = 1               # bumping it invalidates every inherited certificate on purpose
FUTURE_SKEW_S = 300
STRENGTH_ORDER = ("unit", "integration", "in_game", "live")
ENVIRONMENT_SENSITIVE = "ENVIRONMENT_SENSITIVE"


def _pin_key(pin) -> tuple:
    return tuple(sorted((str(p), str(d)) for p, d in pin))


def _observe_one(name: str, recorded, current) -> str:
    if recorded is None or current is None:
        return UNKNOWN_OBS
    if name in ("fingerprint", "environment") and (_is_unknown(recorded) or _is_unknown(current)):
        return UNKNOWN_OBS
    if name == "gate_pin":
        try:
            if git_state.pin_scheme(recorded) != git_state.pin_scheme(current):
                return UNKNOWN_OBS
        except ValueError:
            return UNKNOWN_OBS
        return EQUAL if _pin_key(recorded) == _pin_key(current) else CHANGED
    return EQUAL if recorded == current else CHANGED


def observe_premises(cert: dict, current: dict, now: float) -> dict:
    """Compare a certificate's recorded premises with the ones the caller re-derived.

    Pure: values come from the two arguments only. A premise is `unknown` when either
    side is missing or itself unknown, when an ENVIRONMENT_SENSITIVE claim declares no
    env_deps, and for every premise when the certificate is dated beyond `now` + skew.
    """
    obs = {p: _observe_one(p, cert.get(p), current.get(p)) for p in PREMISES}
    if cert.get("freshness_class") == ENVIRONMENT_SENSITIVE and not cert.get("env_deps"):
        obs["environment"] = UNKNOWN_OBS
    ts = cert.get("ts")
    if isinstance(ts, bool) or not isinstance(ts, (int, float)) or ts > now + FUTURE_SKEW_S:
        obs = {p: (UNKNOWN_OBS if v == EQUAL else v) for p, v in obs.items()}
    return obs


def state_from_premises(obs: dict, has_inherited_event: bool, inheritance_on: bool) -> tuple:
    """(state, reason): any changed -> STALE; any unknown, no premises or switch off -> UNKNOWN;
    all six equal -> INHERITED only when a proof.inherited event names the certificate."""
    values = [obs.get(p, UNKNOWN_OBS) for p in PREMISES]
    changed = [p for p in PREMISES if obs.get(p) == CHANGED]
    if changed:
        return PS_STALE, "premise changed: " + ", ".join(changed)
    if not obs or UNKNOWN_OBS in values:
        return PS_UNKNOWN, "premise unknown: " + ", ".join(
            p for p in PREMISES if obs.get(p, UNKNOWN_OBS) == UNKNOWN_OBS)
    if not inheritance_on:
        return PS_UNKNOWN, "inheritance switch off"
    if not has_inherited_event:
        return PS_UNKNOWN, "premises equal but no proof.inherited event names the certificate"
    return PS_INHERITED, "all six premises equal and inherited"


def requires_full(state_name: str) -> bool:
    """Only FRESH and INHERITED let a gate be skipped; everything else re-runs in full."""
    return state_name not in (PS_FRESH, PS_INHERITED)


def supersedes(newer: dict, older: dict) -> bool:
    """Does the later certificate make the earlier one redundant? Never lowers strength.

    Phase 2 can only order identical bindings; a differing or unknown binding is
    incomparable and never supersedes.
    """
    if newer.get("claim_id") != older.get("claim_id"):
        return False
    bn, bo = newer.get("binding") or {}, older.get("binding") or {}
    if bn != bo or _is_unknown(bn.get("value")):
        return False
    sn, so = newer.get("strength"), older.get("strength")
    if sn not in STRENGTH_ORDER or so not in STRENGTH_ORDER:
        return False
    return STRENGTH_ORDER.index(sn) >= STRENGTH_ORDER.index(so)


def _unknown_fp(reason: str) -> str:
    return f"{UNKNOWN_PREFIX}{reason}"


def causal_fingerprint(root, paths) -> str:
    """`cf1:` + sha256 over sorted [posix path, blob id | ABSENT]; any doubt -> `unknown:`."""
    try:
        if not paths:
            return _unknown_fp("empty premise set")
        base = Path(root).resolve()
        rows: dict = {}
        for rel in paths:
            if not isinstance(rel, str) or not rel:
                return _unknown_fp("bad path")
            p = Path(rel)
            if p.is_absolute() or p.drive or ".." in p.parts:
                return _unknown_fp(f"path {rel!r} is absolute or climbs")
            target = base / p
            if not target.resolve().is_relative_to(base):
                return _unknown_fp(f"path {rel!r} resolves outside the root")
            if not target.exists():
                rows[p.as_posix()] = "ABSENT"
                continue
            files = [target] if target.is_file() else [
                q for q in sorted(target.rglob("*")) if q.is_file() and not _debris(q.relative_to(base))]
            for f in files:
                if not f.resolve().is_relative_to(base):
                    return _unknown_fp(f"{f.name} resolves outside the root")
                rows[f.relative_to(base).as_posix()] = git_state.blob_oid(f.read_bytes())
        body = [[k, rows[k]] for k in sorted(rows)]
        return "cf1:" + hashlib.sha256(_canonical(body)).hexdigest()
    except (OSError, ValueError) as exc:
        return _unknown_fp(f"unreadable ({type(exc).__name__})")


def environment_fingerprint(env_deps) -> str:
    body = {"python": list(sys.version_info[:3]), "system": platform.system(),
            "machine": platform.machine(), "tools": sorted(env_deps or [])}
    return "env1:" + hashlib.sha256(_canonical(body)).hexdigest()


def _via_events(state, ledger: ProofLedger, cid: str, candidate: str, observed, now):
    """(state, reason) decided by PCC events for this claim, or None to use the legacy mapping."""
    mine = [p for p in ledger.produced if p["data"].get("claim_id") == cid]
    inherited = [e for e in ledger.inherited if e["data"].get("claim_id") == cid]
    want = binding(candidate)
    for p in reversed(mine):
        d = p["data"]
        b = d.get("binding") or {}
        if b == want and not _is_unknown(b.get("value")) and d.get("revision") == state.revision:
            return PS_FRESH, f"proof.produced seq {p['seq']} binds this candidate and revision"
    pair = (observed or {}).get(cid)
    if not (mine or inherited) or not pair:
        return None
    obs = observe_premises(pair.get("cert") or {}, pair.get("current") or {},
                           now if now is not None else 0.0)
    has_event = any(e["data"].get("candidate") == candidate for e in inherited)
    return state_from_premises(obs, has_event, inheritance_enabled())


def proof_states(state: GoalState, candidate: str, observed: dict | None = None,
                 now: float | None = None) -> dict:
    """{obligation id: {"state", "reason", "claim_id"}} in projection order.

    Legacy mapping (S2): a SATISFIED verdict about this candidate and this revision is
    FRESH, SATISFIED about anything else is STALE, any other disposition is not a claim.
    An unknown candidate or an unattributable revision is UNKNOWN, never FRESH.

    With PCC events and the inheritance switch on, a `proof.produced` that binds this
    candidate at this revision is FRESH; otherwise `observed[claim_id]` =
    {"cert": recorded premises, "current": re-derived premises} decides INHERITED /
    STALE / UNKNOWN. The events are claims: premises come only from `observed`.
    """
    out: dict = {}
    ledger = project_proofs(state) if inheritance_enabled() else ProofLedger()
    for oid, o in project_convergence(state).obligations.items():
        cid = claim_id(o)
        if o.disposition != SATISFIED:
            out[oid] = {"state": NOT_APPLICABLE, "reason": f"disposition {o.disposition}",
                        "claim_id": cid}
            continue
        if not _is_unknown(candidate):
            via = _via_events(state, ledger, cid, candidate, observed, now)
            if via is not None:
                out[oid] = {"state": via[0], "reason": via[1], "claim_id": cid}
                continue
        v = o.verdict or {}
        tree = v.get("tree_hash")
        if _is_unknown(candidate) or _is_unknown(tree):
            st, why = PS_UNKNOWN, "unknown candidate (R12)"
        elif tree != candidate:
            st, why = PS_STALE, f"proven at tree {tree}, candidate is {candidate}"
        elif v.get("revision") != state.revision:
            st, why = PS_STALE, f"proven under revision {v.get('revision')}, goal is {state.revision}"
        elif o.revision != state.revision:
            st, why = PS_UNKNOWN, f"obligation revision {o.revision} differs from goal {state.revision}"
        else:
            st, why = PS_FRESH, "verdict binds this candidate and revision"
        out[oid] = {"state": st, "reason": why, "claim_id": cid}
    return out
