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
from .contract import DECLARED, REVISED, GoalState, project
from .epoch import DISPATCHING, ENDED, UNSUCCESSFUL, _debris
from .convergence import SATISFIED, project_convergence
from .log import GoalLog, GoalLogCorrupt, GoalLogError
from .log import _canonical

CONTRACT = "obligation.contract"
PRODUCED = "proof.produced"
INHERITED_EV = "proof.inherited"
INVALIDATED = "proof.invalidated"
PROMOTED = "candidate.promoted"       # Phase 4 (spec S7: moved from the frozen table)
NEW_TYPES = (CONTRACT, PRODUCED, INHERITED_EV, INVALIDATED, PROMOTED)

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
    PROMOTED: ("v", "candidate", "tree", "fingerprint"),
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
    promoted: list = field(default_factory=list)
    unsupported: list = field(default_factory=list)       # seqs of events with a newer v


def project_proofs(state: GoalState) -> ProofLedger:
    ledger = ProofLedger()
    slots = {CONTRACT: ledger.contracts, PRODUCED: ledger.produced,
             INHERITED_EV: ledger.inherited, INVALIDATED: ledger.invalidated,
             PROMOTED: ledger.promoted}
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
                          "causal_paths": [], "env_deps": [],
                          "freshness_class": freshness_class(obligation, obligation.verdict, None),
                          "risk_tags": [], "nondeterministic": False, "inheritability": "never"}]}


def binding(tree_hash: str, fingerprint: str | None = None) -> dict:
    """A scheme-tagged candidate binding: the whole tree today, a causal fingerprint in Phase 4."""
    if fingerprint is not None and not _is_unknown(fingerprint):
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


# --- freshness classes and the typed contract (S5, S6) -----------------------------------
# Freshness is a SECOND axis. convergence.GATE_CLASSES stays pinned: extending it would
# change which inputs acceptance takes.

DETERMINISTIC, COMPOSITIONAL, TEMPORAL = "DETERMINISTIC", "COMPOSITIONAL", "TEMPORAL"
FRESH_REQUIRED, FR_UNKNOWN = "FRESH_REQUIRED", "UNKNOWN"
FRESHNESS_CLASSES = (DETERMINISTIC, COMPOSITIONAL, ENVIRONMENT_SENSITIVE, TEMPORAL, FRESH_REQUIRED)
# UNKNOWN routes to a full run exactly like FRESH_REQUIRED, so it ranks at least as strict.
FRESHNESS_RANK = {c: i for i, c in enumerate(FRESHNESS_CLASSES)} | {FR_UNKNOWN: len(FRESHNESS_CLASSES)}
_GATE_TO_FRESHNESS = {"unit": DETERMINISTIC, "integration": ENVIRONMENT_SENSITIVE,
                      "in_game": FRESH_REQUIRED, "live": FRESH_REQUIRED}
RISK_TAGS = frozenset({"security", "authorization", "tenant", "destructive", "migration",
                       "upload", "reality", "authority"})
# Stems whose presence in an obligation's text may only ADD FRESH_REQUIRED.
RISK_KEYWORDS = ("auth", "permission", "tenant", "delete", "drop", "migrat", "upload",
                 "secret", "credential", "destroy", "wipe", "payment")
_REALITY_PLANE = "REALITY"


def _strictest(*classes: str) -> str:
    return max(classes, key=lambda c: FRESHNESS_RANK[c])


def _class_from_word(word) -> str:
    """A contract may name a freshness class directly or by the legacy gate-class vocabulary."""
    if word in FRESHNESS_RANK:
        return word
    return _GATE_TO_FRESHNESS.get(word, FR_UNKNOWN)


def _element_class(el: dict) -> str:
    tags = el.get("risk_tags")
    if not isinstance(tags, list) or any(t not in RISK_TAGS for t in tags):
        return FR_UNKNOWN
    own = _class_from_word(el.get("freshness_class"))
    return _strictest(own, FRESH_REQUIRED) if tags else own


def freshness_class(obligation, verdict, contract) -> str:
    """The freshness class of one claim; never lower than what its gate class implies.

    Legacy map: the verdict's gate class (falling back to the obligation's) gives the base;
    a REALITY-plane obligation is FRESH_REQUIRED whatever its class. A typed contract can
    raise the class (its elements, risk tags) or make it UNKNOWN (combine other than AND,
    a missing or unknown risk tag list). The keyword scan only ever escalates.
    """
    gate = (verdict or {}).get("gate_class") or obligation.gate_class
    cls = _GATE_TO_FRESHNESS.get(gate, FR_UNKNOWN)
    if obligation.plane == _REALITY_PLANE:
        cls = _strictest(cls, FRESH_REQUIRED)
    if contract:
        if contract.get("combine") != "AND":
            return FR_UNKNOWN
        els = contract.get("elements")
        if not isinstance(els, list) or not els or not all(isinstance(e, dict) for e in els):
            return FR_UNKNOWN
        cls = _strictest(cls, *(_element_class(e) for e in els))
    text = (obligation.text or "").lower()
    if cls != FR_UNKNOWN and any(k in text for k in RISK_KEYWORDS):
        cls = _strictest(cls, FRESH_REQUIRED)
    return cls


def _facets(contract: dict) -> dict:
    els = [e for e in contract.get("elements", []) if isinstance(e, dict)]
    return {"risk": {t for e in els for t in (e.get("risk_tags") or [])},
            "paths": {p for e in els for p in (e.get("causal_paths") or [])},
            "env": {p for e in els for p in (e.get("env_deps") or [])},
            "rank": max((FRESHNESS_RANK[_class_from_word(e.get("freshness_class"))] for e in els), default=0),
            "never": any(e.get("inheritability") == "never" for e in els)}


def _not_weaker(new: dict, old: dict) -> bool:
    a, b = _facets(new), _facets(old)
    return (a["risk"] >= b["risk"] and a["paths"] >= b["paths"] and a["env"] >= b["env"]
            and a["rank"] >= b["rank"] and (a["never"] or not b["never"]))


def effective_contract(ledger: ProofLedger, obligation) -> tuple:
    """(contract data, refused seqs). Later contracts for the claim may only strengthen.

    A weaker contract is ignored and its seq reported, mirroring the weakening refusal of
    `contract.revise`. With no contract at all the obligation is its legacy one-element form.
    """
    cid = claim_id(obligation)
    eff, refused = None, []
    for c in ledger.contracts:
        if c["data"].get("claim_id") != cid:
            continue
        if eff is None or _not_weaker(c["data"], eff["data"]):
            eff = c
        else:
            refused.append(c["seq"])
    return (dict(eff["data"]) if eff else legacy_contract(obligation)), refused


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


# --- conservation laws (02-05) -------------------------------------------------------
# Pure checks over a projected state. A violation is a dict; an empty list is a pass.

def law_semantic_conservation(state: GoalState) -> list:
    """Revisions that drop an acceptance criterion or constraint without a stated reason."""
    out: list = []
    prev = None
    for ev in state.events:
        if ev.type not in (DECLARED, REVISED):
            continue
        sem = ev.data.get("semantic") or {}
        if prev is not None and ev.type == REVISED:
            dropped = {k: [x for x in prev.get(k, []) if x not in sem.get(k, [])]
                       for k in ("acceptance", "constraints")}
            dropped = {k: v for k, v in dropped.items() if v}
            reason = str(ev.data.get("weakening_reason") or "").strip()
            if dropped and not (ev.data.get("weakened") and reason):
                out.append({"seq": ev.seq, "dropped": dropped, "law": "semantic"})
        prev = sem
    return out


def law_work_conservation(state: GoalState) -> list:
    """A later epoch that re-attempts an info_key an earlier epoch already ended unsuccessfully."""
    out: list = []
    key_of: dict = {}
    failed: dict = {}
    for ev in state.events:
        d = ev.data
        if ev.type == DISPATCHING:
            key = d.get("info_key")
            key_of[d.get("epoch_id")] = key
            if key in failed:
                out.append({"earlier": failed[key], "later": d.get("epoch_id"),
                            "info_key": key, "law": "work"})
        elif ev.type == ENDED and d.get("outcome") in UNSUCCESSFUL:
            key = key_of.get(d.get("epoch_id"))
            if key is not None:
                failed.setdefault(key, d.get("epoch_id"))
    return out


def certificate_id(cid: str, seq) -> str:
    """Identity of one `proof.produced` event: the claim and the seq it landed at."""
    return f"cert:{cid}:{seq}"


def live_certificates(ledger: ProofLedger, cid: str) -> list:
    """The certificate ids of claim `cid` not yet named by a later `proof.invalidated`."""
    dead = {i["data"].get("certificate") for i in ledger.invalidated if i["data"].get("claim_id") == cid}
    return [certificate_id(cid, p["seq"]) for p in ledger.produced
            if p["data"].get("claim_id") == cid and certificate_id(cid, p["seq"]) not in dead]


def certificate_payload(obligation, verdict: dict, contract: dict, root, source: dict) -> dict:
    """The `proof.produced` payload for one satisfied claim: a causal binding when the contract
    declares causal paths and they fingerprint cleanly, the whole-tree binding otherwise."""
    els = [e for e in contract.get("elements", []) if isinstance(e, dict)]
    paths = sorted({p for e in els for p in (e.get("causal_paths") or [])})
    env_deps = sorted({d for e in els for d in (e.get("env_deps") or [])})
    fp = causal_fingerprint(root, paths) if (paths and root is not None) else _unknown_fp("no causal paths")
    pin = [list(p) for p in (verdict.get("gate_pin") or obligation.gate_pin)]
    cid = claim_id(obligation)
    return {"v": 1, "claim_id": cid, "candidate": verdict.get("tree_hash", ""),
            "binding": binding(verdict.get("tree_hash", ""), fp), "revision": verdict.get("revision", ""),
            "strength": verdict.get("gate_class") or obligation.gate_class, "source": source,
            "premises": {"claim": cid, "revision": verdict.get("revision", ""), "gate_pin": pin,
                         "fingerprint": fp, "environment": environment_fingerprint(env_deps),
                         "policy": POLICY_VERSION},
            "freshness_class": freshness_class(obligation, verdict, contract), "env_deps": env_deps,
            "contract_hash": hashlib.sha256(_canonical(contract)).hexdigest()}


def law_proof_conservation(ledger: ProofLedger) -> list:
    """A second proof.produced for one (claim, binding) with no proof.invalidated between them."""
    out: list = []
    live: dict = {}
    for ev in sorted(ledger.produced + ledger.invalidated, key=lambda e: e["seq"]):
        d = ev["data"]
        if "binding" not in d:
            for k in [k for k in live if k[0] == d["claim_id"]]:
                del live[k]
            continue
        key = (d["claim_id"], _canonical(d["binding"]))
        if key in live:
            out.append({"claim_id": d["claim_id"], "first_seq": live[key], "second_seq": ev["seq"],
                        "law": "proof"})
        else:
            live[key] = ev["seq"]
    return out


def independent(a: dict, b: dict) -> bool:
    """Two units of work may run concurrently only when both declare reads, writes and resources
    and neither writes what the other reads or writes, nor shares a resource. Undeclared is not independent."""
    sets = []
    for unit in (a, b):
        parts = []
        for k in ("reads", "writes", "resources"):
            v = unit.get(k) if isinstance(unit, dict) else None
            if not isinstance(v, (list, tuple, set, frozenset)):
                return False
            parts.append(set(v))
        sets.append(parts)
    (ra, wa, xa), (rb, wb, xb) = sets
    return not (wa & (rb | wb) or wb & ra or xa & xb)


def law_unknown_escalates() -> tuple:
    """(cells, violations) over every premise combination x event x switch: unknown never skips a gate."""
    import itertools  # noqa: PLC0415
    out: list = []
    cells = 0
    for combo in itertools.product((EQUAL, CHANGED, UNKNOWN_OBS), repeat=len(PREMISES)):
        obs = dict(zip(PREMISES, combo))
        for has_ev, on in itertools.product((True, False), repeat=2):
            cells += 1
            got = state_from_premises(obs, has_ev, on)[0]
            doubt = CHANGED not in combo and (UNKNOWN_OBS in combo or not has_ev or not on)
            if doubt and got in (PS_FRESH, PS_INHERITED):
                out.append({"premises": combo, "event": has_ev, "switch": on, "got": got,
                            "law": "unknown"})
    return cells, out
