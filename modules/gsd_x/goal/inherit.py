"""Proof inheritance (spec S3, S5): a claim proven at one tree stays proven at the next when nothing it
depends on changed.

Two halves, kept apart on purpose:

* **observe -> plan -> apply** runs in the sweep. It re-derives the six premises of the claim's live
  certificate from the working tree, and writes `proof.inherited` (all six equal and the claim opted in)
  or `proof.invalidated` (a premise changed). It never writes anything for an unknown premise: an
  unknown is a reason to run the gate, not a record.
* **inherited_ids** is pure over the log. The decision never reads the world; it asks which claims have
  a `proof.inherited` event for THIS candidate whose premises agree with the certificate and with what
  the log itself can derive. An event that disagrees is a claim nobody confirmed and is ignored.

Closure stays necessary-not-sufficient: the independent judge still re-runs every pinned gate.
"""
from __future__ import annotations

from datetime import datetime

from . import contract as gc
from . import convergence as cv
from . import git_state as gs
from . import proof as pf

INHERIT, INVALIDATE, RUN, FRESH = "INHERIT", "INVALIDATE", "RUN", "FRESH"
# Freshness classes a claim may be inherited under. TEMPORAL, FRESH_REQUIRED and UNKNOWN never are.
ELIGIBLE = frozenset({pf.DETERMINISTIC, pf.COMPOSITIONAL, pf.ENVIRONMENT_SENSITIVE})


def _seconds(ts):
    """A log timestamp as epoch seconds, or None when it cannot be read (observed as unknown)."""
    try:
        return datetime.fromisoformat(str(ts)).timestamp()
    except ValueError:
        return None


def _latest_live(ledger: pf.ProofLedger, cid: str):
    """(certificate id, payload, seq, ts) of the newest certificate of claim `cid` not invalidated."""
    live = set(pf.live_certificates(ledger, cid))
    for p in reversed(ledger.produced):
        cert = pf.certificate_id(cid, p["seq"])
        if p["data"].get("claim_id") == cid and cert in live:
            return cert, p["data"], p["seq"], p["ts"]
    return None


def ineligible(ob, contract: dict, cert_data: dict) -> str:
    """Why this claim may never be inherited, or '' when it opted in and its class allows it."""
    if ob.plane == cv.REALITY:
        return "REALITY plane evidence is always re-run"
    els = contract.get("elements")
    if contract.get("combine") != "AND" or not isinstance(els, list) or not els \
            or not all(isinstance(e, dict) for e in els):
        return "contract is not a plain AND of elements"
    if not all(e.get("inheritability") == "inheritable" for e in els):
        return "the contract did not opt in to inheritance"
    if any(e.get("nondeterministic") for e in els):
        return "the contract declares a nondeterministic element"
    cls = pf._strictest(pf.freshness_class(ob, ob.verdict, contract),
                        pf._class_from_word(cert_data.get("freshness_class")))
    if cls not in ELIGIBLE:
        return f"freshness class {cls} is never inherited"
    return ""


def observe_current(state, ob, contract: dict, root) -> dict:
    """The six premises as the working tree has them now. None marks a premise that could not be read."""
    els = [e for e in contract.get("elements", []) if isinstance(e, dict)]
    paths = sorted({p for e in els for p in (e.get("causal_paths") or [])})
    env_deps = sorted({d for e in els for d in (e.get("env_deps") or [])})
    try:
        pin = [list(p) for p in gs.file_pin(root, [p for p, _ in ob.gate_pin],
                                            scheme=gs.pin_scheme(ob.gate_pin))]
    except (OSError, ValueError):
        pin = None
    return {"claim": pf.claim_id(ob), "revision": state.revision, "gate_pin": pin,
            "fingerprint": pf.causal_fingerprint(root, paths) if paths else pf._unknown_fp("no causal paths"),
            "environment": pf.environment_fingerprint(env_deps), "policy": pf.POLICY_VERSION}


def plan(state, root, candidate: str, now: float) -> list:
    """One item per SATISFIED claim: {obligation, claim_id, certificate, action, reason, premises}."""
    ledger = pf.project_proofs(state)
    on = pf.inheritance_enabled()
    out = []
    for oid, ob in cv.project_convergence(state).obligations.items():
        if ob.disposition != cv.SATISFIED:
            continue
        cid = pf.claim_id(ob)
        item = {"obligation": oid, "claim_id": cid, "certificate": "", "action": RUN,
                "reason": "", "premises": {}}
        out.append(item)
        v = ob.verdict or {}
        live = _latest_live(ledger, cid)
        if not on:
            item["reason"] = "inheritance switch off"
        elif cv.tree_equal(v.get("tree_hash"), candidate) and v.get("revision") == state.revision:
            item.update(action=FRESH, reason="the verdict binds this candidate")
        elif pf._is_unknown(candidate):
            item["reason"] = "unknown candidate (R12)"
        elif live is None:
            item["reason"] = "no live certificate"
        else:
            cert, data, _seq, ts = live
            contract, _refused = pf.effective_contract(ledger, ob)
            current = observe_current(state, ob, contract, root)
            recorded = dict(data.get("premises") or {}, freshness_class=data.get("freshness_class"),
                            env_deps=data.get("env_deps"), ts=_seconds(ts))
            verdict, why = pf.state_from_premises(pf.observe_premises(recorded, current, now), True, on)
            item.update(certificate=cert, premises=current, reason=why)
            if verdict == pf.PS_STALE:
                item["action"] = INVALIDATE
            elif verdict == pf.PS_INHERITED:
                blocked = ineligible(ob, contract, data)
                if blocked:
                    item["reason"] = blocked
                else:
                    item["action"] = INHERIT
    return out


def apply(log, items: list, candidate: str, actor: str) -> list:
    """Write what `plan` decided; an item already recorded is skipped. Returns one line per event."""
    out = []
    if not pf.inheritance_enabled():
        return out
    for it in items:
        state = gc.project(log)
        if it["action"] == INHERIT:
            if it["obligation"] in inherited_ids(state, candidate):
                continue
            pf.append_pcc(log, state, pf.INHERITED_EV,
                          {"v": 1, "claim_id": it["claim_id"], "certificate": it["certificate"],
                           "candidate": candidate, "premises": it["premises"]}, actor)
            out.append(f"{log.goal_id}: {it['obligation']} inherits its proof at {candidate}")
        elif it["action"] == INVALIDATE:
            pf.append_pcc(log, state, pf.INVALIDATED,
                          {"v": 1, "claim_id": it["claim_id"], "certificate": it["certificate"],
                           "reason": it["reason"]}, actor)
            out.append(f"{log.goal_id}: {it['obligation']} certificate invalidated ({it['reason']})")
    return out


def _agrees(event_premises, cert_premises: dict, ob, state) -> bool:
    """The event repeats the certificate's six premises, and the four the log can derive hold today."""
    if not isinstance(event_premises, dict) or set(event_premises) != set(pf.PREMISES):
        return False
    for name in pf.PREMISES:
        if name == "gate_pin":
            continue
        if event_premises.get(name) != cert_premises.get(name):
            return False
    try:
        pins = {pf._pin_key(event_premises["gate_pin"]), pf._pin_key(cert_premises["gate_pin"])}
        if pins != {pf._pin_key(ob.gate_pin)}:
            return False
    except (KeyError, TypeError, ValueError):
        return False
    return (event_premises["claim"] == pf.claim_id(ob) and event_premises["revision"] == state.revision
            and event_premises["policy"] == pf.POLICY_VERSION
            and not pf._is_unknown(event_premises["fingerprint"])
            and not pf._is_unknown(event_premises["environment"]))


def inherited_ids(state, candidate: str) -> frozenset:
    """Obligation ids whose proof is inherited at `candidate`: a pure projection of the log."""
    if not pf.inheritance_enabled() or pf._is_unknown(candidate):
        return frozenset()
    ledger = pf.project_proofs(state)
    out = set()
    for oid, ob in cv.project_convergence(state).obligations.items():
        if ob.disposition != cv.SATISFIED or (ob.verdict or {}).get("revision") != state.revision:
            continue
        cid = pf.claim_id(ob)
        live = _latest_live(ledger, cid)
        if live is None:
            continue
        cert, data, seq, _ts = live
        contract, _refused = pf.effective_contract(ledger, ob)
        if ineligible(ob, contract, data):
            continue
        for e in ledger.inherited:
            d = e["data"]
            if (d.get("claim_id") == cid and d.get("certificate") == cert and d.get("candidate") == candidate
                    and e["seq"] > seq and _agrees(d.get("premises"), data.get("premises") or {}, ob, state)):
                out.add(oid)
                break
    return frozenset(out)
