"""Trust substrate for proof certificates: authority, lineage, revocation, monotonicity (05-2-01).

A certificate is produced by an AUTHORITY (a registered gate-running component at a version) and sits in
a LINEAGE (its own root at depth 0, or a descendant of another certificate). Revoking an authority makes
every certificate it issued, and every descendant of one, not live -- by appending `authority.revoked`;
no certificate byte is ever rewritten and no event un-revokes. An inherited claim may never carry more
strength than the certificate it inherits from (N05); an event with no `authority` claims nothing above
the original and is admitted.

Pure: nothing here writes, except `revoke`, which goes through the proof writer gate.
"""
from __future__ import annotations

import hashlib

from . import proof as pf

# id -> versions the engine knows. A certificate naming another (id, version) is untrusted (05-2-02 F6).
AUTHORITIES = {"gsdx-sweep": (1, 2)}
DEFAULT_AUTHORITY = "gsdx-sweep"


def current_version(authority_id: str = DEFAULT_AUTHORITY) -> int:
    return max(AUTHORITIES[authority_id])


def strength_ok(inherited, original) -> bool:
    """True when `inherited` is not above `original` in STRENGTH_ORDER. An unknown word is never ok."""
    order = pf.STRENGTH_ORDER
    if inherited not in order or original not in order:
        return False
    return order.index(inherited) <= order.index(original)


def stamp(payload: dict, claim_id: str, seq: int, authority_id: str = DEFAULT_AUTHORITY,
          version: int | None = None) -> dict:
    """Return `payload` with `authority` and a depth-0 `lineage` (its own root) for the event landing at `seq`."""
    own = pf.certificate_id(claim_id, seq)
    out = dict(payload)
    out["authority"] = {"id": authority_id,
                        "version": current_version(authority_id) if version is None else version,
                        "strength": payload.get("strength")}
    out["lineage"] = {"root": own, "parent": None, "depth": 0, "via": "produced"}
    return out


def is_trusted(cert_data: dict) -> bool:
    """A certificate carrying both an authority and a lineage. A pre-5.2 certificate carries neither."""
    a, ln = cert_data.get("authority"), cert_data.get("lineage")
    return (isinstance(a, dict) and "id" in a and "version" in a
            and isinstance(ln, dict) and "root" in ln and "depth" in ln)


def revoked_set(ledger) -> frozenset:
    """{(authority id, version)} named by an `authority.revoked` event. A set: revoking twice is one state."""
    return frozenset((e["data"].get("authority"), e["data"].get("version")) for e in ledger.revoked)


def dead_certificates(ledger) -> frozenset:
    """Certificate ids revoked directly (their authority is revoked) or by lineage (root or parent dead)."""
    revoked = revoked_set(ledger)
    by_id = {}
    dead = set()
    for p in ledger.produced:
        d = p["data"]
        cert = pf.certificate_id(d.get("claim_id"), p["seq"])
        by_id[cert] = d
        a = d.get("authority")
        if isinstance(a, dict) and (a.get("id"), a.get("version")) in revoked:
            dead.add(cert)
    changed = True
    while changed:
        changed = False
        for cert, d in by_id.items():
            ln = d.get("lineage")
            if cert in dead or not isinstance(ln, dict):
                continue
            if ln.get("root") in dead or ln.get("parent") in dead:
                dead.add(cert)
                changed = True
    return frozenset(dead)


def inherited_event_ok(ledger, event_data: dict) -> bool:
    """False when the event's authority strength is above the certificate it names. No authority: admitted."""
    a = event_data.get("authority")
    if a is None:
        return True
    if not isinstance(a, dict):
        return False
    cert = event_data.get("certificate")
    for p in ledger.produced:
        if pf.certificate_id(p["data"].get("claim_id"), p["seq"]) == cert:
            return strength_ok(a.get("strength"), p["data"].get("strength"))
    return False


def contract_hashes(ledger, obligation) -> frozenset:
    """Every contract hash a certificate of this claim may legitimately carry: each contract the ledger
    holds for it, plus the legacy one (the single-gate contract every obligation already is, 05-2-02 (d))."""
    cid = pf.claim_id(obligation)
    hs = {hashlib.sha256(pf._canonical(c["data"])).hexdigest()
          for c in ledger.contracts if c["data"].get("claim_id") == cid}
    hs.add(hashlib.sha256(pf._canonical(pf.legacy_contract(obligation))).hexdigest())
    return frozenset(hs)


def _tree_known(tree) -> bool:
    return isinstance(tree, str) and bool(tree) and not pf._is_unknown(tree) and "dirty" not in tree


def plane_ok(plane) -> tuple:
    """(ok, reason) for a certificate's `plane` field (N19). Absent is admitted (pre-plane certificates).

    PLATFORM names exactly one plane. PORTABILITY names >= 2 distinct planes and one `modules_tree` per plane,
    all known (clean) and identical; anything less is a platform result wearing a portability stamp."""
    if plane is None:
        return True, ""
    if not isinstance(plane, dict):
        return False, "plane is not an object"
    planes, tree = plane.get("planes"), plane.get("modules_tree")
    if not isinstance(planes, list) or not planes or not all(isinstance(p, str) and p for p in planes):
        return False, "plane.planes is not a list of plane ids"
    kind = plane.get("claim")
    if kind == "PLATFORM":
        return (len(set(planes)) == 1), "" if len(set(planes)) == 1 else "PLATFORM names exactly one plane"
    if kind != "PORTABILITY":
        return False, f"plane.claim {kind!r} is neither PLATFORM nor PORTABILITY"
    if len(set(planes)) < 2:
        return False, "PORTABILITY needs at least two distinct planes"
    if not isinstance(tree, dict) or set(tree) != set(planes):
        return False, "PORTABILITY needs one modules_tree per plane"
    if not all(_tree_known(t) for t in tree.values()):
        return False, "a modules_tree is unknown or dirty"
    if len(set(tree.values())) != 1:
        return False, "the planes ran different modules trees"
    return True, ""


def _lineage_ok(ledger, own: str, claim_id: str, seq, ln: dict) -> tuple:
    parent, depth, root = ln.get("parent"), ln.get("depth"), ln.get("root")
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 0:
        return False, "lineage depth is not a non-negative int"
    if parent is None:
        ok = depth == 0 and root == own
        return ok, "" if ok else "a root certificate is its own root at depth 0"
    by_id = {pf.certificate_id(p["data"].get("claim_id"), p["seq"]): p for p in ledger.produced}
    pe = by_id.get(parent)
    if pe is None:
        return False, "lineage parent is not a certificate of the ledger"
    if pe["seq"] >= seq:
        return False, "lineage parent does not precede the certificate"
    if pe["data"].get("claim_id") != claim_id:
        return False, "lineage parent belongs to another claim"
    pl = pe["data"].get("lineage")
    if not isinstance(pl, dict) or depth != pl.get("depth", -2) + 1 or root != pl.get("root"):
        return False, "lineage depth or root disagrees with the chain"
    return True, ""


def verify_certificate(ledger, cert_event: dict, claim_id: str, obligation, contract_hashes) -> tuple:
    """(ok, reason): may this `proof.produced` event be read as a certificate of `claim_id`? Pure.

    Refuses: a missing authority/lineage, an unregistered authority, a certificate filed under another claim,
    a contract hash the ledger never held, a strength above the obligation's accepted gate class, a lineage
    that disagrees with the chain, and a plane stamp that fails the N19 predicate. Revocation is
    `dead_certificates`' business and stays there."""
    d = cert_event["data"]
    if not is_trusted(d):
        return False, "no authority or lineage"
    a = d["authority"]
    if a.get("version") not in AUTHORITIES.get(a.get("id"), ()):
        return False, f"authority {a.get('id')!r} v{a.get('version')!r} is not registered"
    if d.get("claim_id") != claim_id or (d.get("premises") or {}).get("claim") != claim_id:
        return False, "certificate is filed under another claim"
    if d.get("contract_hash") not in contract_hashes:
        return False, "contract_hash names no contract the ledger holds for this claim"
    cls = getattr(obligation, "gate_class", None)
    if cls in pf.STRENGTH_ORDER:
        if not strength_ok(d.get("strength"), cls) or not strength_ok(a.get("strength"), d.get("strength")):
            return False, f"strength {d.get('strength')!r} is above the accepted gate class {cls!r}"
    elif d.get("strength") != cls:
        return False, "strength differs from an accepted gate class outside the strength order"
    ok, why = _lineage_ok(ledger, pf.certificate_id(claim_id, cert_event["seq"]), claim_id, cert_event["seq"],
                          d["lineage"])
    if not ok:
        return False, why
    return plane_ok(d.get("plane"))


def revoke(log, state, authority_id: str, version: int, reason: str, actor: str):
    """Append `authority.revoked`. There is no inverse event."""
    return pf.append_pcc(log, state, pf.AUTHORITY_REVOKED,
                         {"v": 1, "authority": authority_id, "version": version, "reason": reason}, actor)


def ledger(proofs) -> list:
    """Per (authority, version): state ACTIVE|REVOKED, certificates issued and live. Pure."""
    revoked = revoked_set(proofs)
    dead = dead_certificates(proofs)
    invalidated = {i["data"].get("certificate") for i in proofs.invalidated}
    rows = {}
    for aid, versions in AUTHORITIES.items():
        for v in versions:
            rows[(aid, v)] = {"authority": aid, "version": v,
                              "state": "REVOKED" if (aid, v) in revoked else "ACTIVE",
                              "issued": 0, "live": 0}
    for p in proofs.produced:
        a = p["data"].get("authority")
        if not isinstance(a, dict):
            continue
        row = rows.setdefault((a.get("id"), a.get("version")),
                              {"authority": a.get("id"), "version": a.get("version"),
                               "state": "REVOKED" if (a.get("id"), a.get("version")) in revoked else "ACTIVE",
                               "issued": 0, "live": 0})
        cert = pf.certificate_id(p["data"].get("claim_id"), p["seq"])
        row["issued"] += 1
        if cert not in dead and cert not in invalidated:
            row["live"] += 1
    return [rows[k] for k in sorted(rows, key=lambda k: (str(k[0]), str(k[1])))]
