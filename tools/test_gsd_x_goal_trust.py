#!/usr/bin/env python3
"""Phase 5.2 / 05-2-01: trust substrate -- revocation, lineage, authority monotonicity (N01 N02 N05 N23).

Every gate builds a REAL certificate through the real sweep path (the JV fixture of
test_gsd_x_goal_judge_validate.py), then appends the event under test. Revocation never rewrites a byte
of the log: the hash of every existing event file is compared before and after.

Summary line: GSDX_TRUST_PASS=n/m  threshold=n/m
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import test_gsd_x_goal_judge_validate as jv                 # noqa: E402  (hermetic HOME/GOALS env set on import)
from modules.gsd_x.goal import inherit as inh               # noqa: E402
from modules.gsd_x.goal import proof as pf                  # noqa: E402
from modules.gsd_x.goal import trust as tr                  # noqa: E402

JV = jv.JV
passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}".rstrip())
    else:
        fails += 1
        print(f"FAIL {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    try:
        cond, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a raise is a FAIL line, the summary always prints
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


def snapshot(w) -> dict:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(w.log.dir.iterdir()) if p.is_file() and p.suffix == ".json"}


def ledger_of(w):
    return pf.project_proofs(jv._st(w.log))


def action(w):
    items = inh.plan(jv._st(w.log), w.repo, w.tree(), time.time())
    return items[0]["action"] if items else None


def live(w):
    d = ledger_of(w).produced[0]["data"]
    return pf.live_certificates(ledger_of(w), d["claim_id"])


def revoke(w, version, reason="drill"):
    tr.revoke(w.log, jv._st(w.log), tr.DEFAULT_AUTHORITY, version, reason, "owner")


def gate_revoked_invalid_bytes_unchanged():
    w = JV("tr-rev")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        before_action = action(w)
        first = ledger_of(w).produced[0]["seq"]
        before = snapshot(w)
        revoke(w, 1)                                    # CONTROL: another version is revoked, ours stays live
        control_live = live(w)
        control_action = action(w)
        revoke(w, tr.current_version())
        after = snapshot(w)
        name = f"{first:06d}.json"
        bytes_same = all(after.get(k) == v for k, v in before.items()) and name in after
        ok = (before_action == inh.INHERIT and len(control_live) == 1 and control_action == inh.INHERIT
              and live(w) == [] and action(w) == inh.RUN and bytes_same)
        return ok, (f"before={before_action} control_live={len(control_live)} control={control_action} "
                    f"after_live={len(live(w))} after={action(w)} bytes_same={bytes_same}")
    finally:
        w.close()


def gate_revoked_cascades_lineage():
    w = JV("tr-lin")
    try:
        led = ledger_of(w)
        d = dict(led.produced[0]["data"])
        root = pf.certificate_id(d["claim_id"], led.produced[0]["seq"])
        d["authority"] = dict(d["authority"], version=1)
        d["lineage"] = {"root": root, "parent": root, "depth": 1, "via": "derived"}
        pf.append_pcc(w.log, jv._st(w.log), pf.PRODUCED, d, "hand")
        both = live(w)
        revoke(w, tr.current_version())                 # kills the root's authority; the child's is version 1
        left = live(w)
        ok = len(both) == 2 and left == []
        return ok, f"before={len(both)} after_revoking_root={len(left)}"
    finally:
        w.close()


def gate_lineage_field():
    w = JV("tr-field", gate_class="integration")
    try:
        p = ledger_of(w).produced[0]
        own = pf.certificate_id(p["data"]["claim_id"], p["seq"])
        ln = p["data"].get("lineage")
        ok = ln == {"root": own, "parent": None, "depth": 0, "via": "produced"}
        return ok, f"lineage={ln}"
    finally:
        w.close()


def gate_authority_field():
    w = JV("tr-auth", gate_class="integration")
    try:
        a = ledger_of(w).produced[0]["data"].get("authority")
        ok = a == {"id": tr.DEFAULT_AUTHORITY, "version": tr.current_version(), "strength": "integration"}
        return ok, f"authority={a}"
    finally:
        w.close()


def _inherited(w, strength):
    d = ledger_of(w).produced[0]["data"]
    seq = ledger_of(w).produced[0]["seq"]
    body = {"v": 1, "claim_id": d["claim_id"], "certificate": pf.certificate_id(d["claim_id"], seq),
            "candidate": w.tree(), "premises": dict(d["premises"])}
    if strength is not None:
        body["authority"] = {"id": d["authority"]["id"], "version": d["authority"]["version"],
                             "strength": strength}
    return body


def _forge_raw(w, body):
    st = jv._st(w.log)
    w.log.append(st.last_seq + 1, pf.INHERITED_EV, body, "hand")


def gate_monotonic_refused():
    w = JV("tr-mono", gate_class="integration")
    try:
        w.edit("docs/n.txt", "changed notes\n")
        inflated = _inherited(w, "live")
        refused = False
        try:
            pf.append_pcc(w.log, jv._st(w.log), pf.INHERITED_EV, inflated, "hand")
        except pf.ProofRefused:
            refused = True
        _forge_raw(w, inflated)                                    # a hand-forged event the writer never saw
        forged_ignored = inh.inherited_ids(jv._st(w.log), w.tree()) == frozenset()
        # CONTROLS: equal and lower strength are admitted by the writer and counted by the reader
        pf.append_pcc(w.log, jv._st(w.log), pf.INHERITED_EV, _inherited(w, "integration"), "hand")
        equal_ok = len(inh.inherited_ids(jv._st(w.log), w.tree())) == 1
        w2 = JV("tr-mono2", gate_class="integration")
        try:
            w2.edit("docs/n.txt", "changed notes\n")
            pf.append_pcc(w2.log, jv._st(w2.log), pf.INHERITED_EV, _inherited(w2, "unit"), "hand")
            lower_ok = len(inh.inherited_ids(jv._st(w2.log), w2.tree())) == 1
            pf.append_pcc(w2.log, jv._st(w2.log), pf.INHERITED_EV, _inherited(w2, None), "hand")  # no authority
        finally:
            w2.close()
        ok = refused and forged_ignored and equal_ok and lower_ok
        return ok, f"refused={refused} forged_ignored={forged_ignored} equal={equal_ok} lower={lower_ok}"
    finally:
        w.close()


def gate_legacy_cert_untrusted():
    saved = tr.stamp
    tr.stamp = lambda payload, *a, **k: payload                    # build a pre-5.2 certificate: no authority/lineage
    try:
        w = JV("tr-legacy")
    finally:
        tr.stamp = saved
    try:
        d = ledger_of(w).produced[0]["data"]
        w.edit("docs/n.txt", "changed notes\n")
        projected = len(ledger_of(w).produced) == 1 and d.get("v") == 1
        act = action(w)
        w.forge()
        ids = inh.inherited_ids(jv._st(w.log), w.tree())
        ok = ("authority" not in d and "lineage" not in d and projected and act == inh.RUN
              and ids == frozenset())
        return ok, f"stamped={'authority' in d} projected={projected} action={act} inherited={sorted(ids)}"
    finally:
        w.close()


def gate_ledger_seed():
    w = JV("tr-ledger")
    try:
        rows0 = {(r["authority"], r["version"]): r for r in tr.ledger(ledger_of(w))}
        cur = rows0[(tr.DEFAULT_AUTHORITY, tr.current_version())]
        snap = snapshot(w)
        tr.ledger(ledger_of(w))
        pure = snapshot(w) == snap
        revoke(w, tr.current_version())
        revoke(w, tr.current_version(), "again")
        rows1 = {(r["authority"], r["version"]): r for r in tr.ledger(ledger_of(w))}
        row = rows1[(tr.DEFAULT_AUTHORITY, tr.current_version())]
        names = " ".join(pf.NEW_TYPES).lower()
        no_inverse = not any(w_ in names for w_ in ("restor", "unrevoke", "reinstat", "reinstate"))
        once = len(tr.revoked_set(ledger_of(w))) == 1
        ok = (cur["state"] == "ACTIVE" and cur["issued"] == 1 and cur["live"] == 1 and pure
              and row["state"] == "REVOKED" and row["issued"] == 1 and row["live"] == 0
              and no_inverse and once)
        return ok, f"active={cur} revoked={row} pure={pure} no_inverse={no_inverse} once={once}"
    finally:
        w.close()


GATES = [
    ("V-TRUST-REVOKED-INVALID-BYTES-UNCHANGED", gate_revoked_invalid_bytes_unchanged),
    ("V-TRUST-REVOKED-CASCADES-LINEAGE", gate_revoked_cascades_lineage),
    ("V-TRUST-LINEAGE-FIELD", gate_lineage_field),
    ("V-TRUST-AUTHORITY-FIELD", gate_authority_field),
    ("V-TRUST-MONOTONIC-REFUSED", gate_monotonic_refused),
    ("V-TRUST-LEGACY-CERT-UNTRUSTED", gate_legacy_cert_untrusted),
    ("V-TRUST-LEDGER-SEED", gate_ledger_seed),
]


def main() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    total = passes + fails
    print(f"GSDX_TRUST_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
