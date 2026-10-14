#!/usr/bin/env python3
"""Phase 5.2 / 05-2-02: certificate forgery (N16) driven through the REAL judge.

Each attack appends a forged `proof.produced` certificate to a real GoalLog of a real tmp git repo, moves a
non-causal file, and calls `judge.judge`. The gate drops a marker file when it runs, so the outcome is
observed, not inferred: a VALIDATEd obligation leaves no run, a refused certificate forces the pinned gate
to re-run. Every attack has a CONTROL on the same fixture in which the legitimate certificate is admitted --
a gate that refuses everything would pass every refusal assertion. Attacks on a `proof.inherited` event
(F1 F2 F10) are driven through `inherit.inherited_ids`, the only reader of that event; F12 is the pure
premise observation.

Summary line: GSDX_TRUST_FORGERY_PASS=n/m  threshold=n/m
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import test_gsd_x_goal_judge_validate as jv                 # noqa: E402  (hermetic HOME, JV fixture)
from modules.gsd_x.goal import convergence as cv           # noqa: E402
from modules.gsd_x.goal import inherit as ih                # noqa: E402
from modules.gsd_x.goal import judge as jd                  # noqa: E402
from modules.gsd_x.goal import proof as pf                  # noqa: E402
from modules.gsd_x.goal import trust                        # noqa: E402

passes = 0
fails = 0
refused_attacks: list = []


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
    except Exception as exc:  # noqa: BLE001 -- a raise is a FAIL line, never an escape
        check(gate, False, f"raised {type(exc).__name__}: {exc}")
        return
    check(gate, bool(cond), ev)


OBS = (("ob-one", ["src"]), ("ob-two", ["src"]))


class FG:
    """A legacy-satisfied goal (no certificate) whose two claims get certificates appended by hand."""

    def __init__(self, name, gate_class="unit"):
        self.w = jv.JV(name, obs=OBS, gate_class=gate_class, pcc=False)
        self.contracts = {}
        self.cids = {}
        for oid, paths in OBS:
            st = jv._st(self.w.log)
            ob = cv.project_convergence(st).obligations[oid]
            cid = pf.claim_id(ob)
            self.cids[oid] = cid
            el = {"oracle": gate_class, "command": jv.GATE_CMD, "gate_pin": [list(p) for p in self.w.pin],
                  "causal_paths": list(paths), "env_deps": [], "freshness_class": "DETERMINISTIC",
                  "risk_tags": [], "nondeterministic": False, "inheritability": "inheritable"}
            data = {"v": 1, "claim_id": cid, "obligation": oid, "combine": "AND", "elements": [el]}
            pf.append_pcc(self.w.log, st, pf.CONTRACT, data, "founder")
            self.contracts[oid] = data

    def cert(self, oid, mutate=None, sign=True) -> str:
        """Append one certificate of `oid` (stamped as the sweep would) after `mutate(payload, own_id)`."""
        w = self.w
        st = jv._st(w.log)
        ob = cv.project_convergence(st).obligations[oid]
        verdict = dict(ob.verdict, revision=st.revision)
        p = pf.certificate_payload(ob, verdict, self.contracts[oid], w.repo, {"epoch": "ep-fg", "provider": "gate"})
        seq = st.last_seq + 1
        p = trust.stamp(p, self.cids[oid], seq)
        own = pf.certificate_id(self.cids[oid], seq)
        if mutate is not None:
            p = mutate(p, own) or p
        pf.append_pcc(w.log, st, pf.PRODUCED, p, "hand")
        return own

    def settle(self):
        """Move a file no claim depends on, and forget the marker the fixture's own setup left."""
        self.w.edit("docs/n.txt", "changed notes\n")
        if self.w.mark.exists():
            self.w.mark.unlink()

    def row(self, oid):
        rec = self.w.judge()
        for g in rec.gates:
            if g.get("obligation") == oid:
                return rec, g
        return rec, {}

    def close(self):
        self.w.close()


def mode_of(fg, oid="ob-one"):
    rec, row = fg.row(oid)
    return rec, row.get("mode")


def attack_vs_control(attack, control, gate_class="unit", ctl_gate_class=None):
    """(refused, admitted, evidence): the forged certificate forces a gate run, the control is validated."""
    a = FG("fg-atk", gate_class)
    try:
        a.cert("ob-two")
        attack(a)
        a.settle()
        rec_a, mode_a = mode_of(a)
        ran_a = a.w.ran()
    finally:
        a.close()
    c = FG("fg-ctl", ctl_gate_class or gate_class)
    try:
        c.cert("ob-two")
        control(c)
        c.settle()
        rec_c, mode_c = mode_of(c)
        ran_c = c.w.ran()
    finally:
        c.close()
    refused = mode_a is None and rec_a.verdict == jd.PASS and ran_a >= 1
    admitted = mode_c == "VALIDATE" and rec_c.verdict == jd.PASS and ran_c == 0
    return refused, admitted, f"forged: mode={mode_a} verdict={rec_a.verdict} runs={ran_a}; control: mode={mode_c} runs={ran_c}"


def plain(fg):
    fg.cert("ob-one")


def authority(**kw):
    def m(p, _own):
        p["authority"] = dict(p["authority"], **kw)
    return m


def lineage(parent=None, depth=0, root=None, via="produced"):
    def m(p, own):
        p["lineage"] = {"root": root or (parent or own), "parent": parent, "depth": depth, "via": via}
    return m


# --- certificate attacks (through the judge) -------------------------------------------

def a_f3(fg):                     # unit claim stamped `live`
    def m(p, _own):
        p["strength"] = "live"
        p["authority"] = dict(p["authority"], strength="live")
    fg.cert("ob-one", m)


def a_f4(fg):                     # lineage parent is a certificate of ANOTHER claim
    other = pf.certificate_id(fg.cids["ob-two"], 0)
    led = pf.project_proofs(jv._st(fg.w.log))
    for e in led.produced:
        if e["data"].get("claim_id") == fg.cids["ob-two"]:
            other = pf.certificate_id(fg.cids["ob-two"], e["seq"])
    fg.cert("ob-one", lineage(parent=other, depth=1, root=other))


def c_f4(fg):                     # parent is an earlier certificate of the SAME claim
    first = fg.cert("ob-one")
    fg.cert("ob-one", lineage(parent=first, depth=1, root=first))


def a_f5_cycle(fg):               # the certificate is its own parent
    fg.cert("ob-one", lambda p, own: lineage(parent=own, depth=1, root=own)(p, own))


def a_f5_depth(fg):               # depth disagrees with the chain
    # the predecessor is itself unusable (unregistered authority) so no older certificate can validate instead
    first = fg.cert("ob-one", authority(id="builder-own"))
    fg.cert("ob-one", lineage(parent=first, depth=7, root=first))


def c_f5(fg):
    first = fg.cert("ob-one")
    fg.cert("ob-one", lineage(parent=first, depth=1, root=first))


def a_f6(fg):
    fg.cert("ob-one", authority(id="builder-own"))


def a_f6_version(fg):
    fg.cert("ob-one", authority(version=99))


def c_f6(fg):                     # an older REGISTERED version is still trusted
    fg.cert("ob-one", authority(version=1))


def a_f7(fg):                     # the current authority is revoked, then it signs a replayed certificate
    trust.revoke(fg.w.log, jv._st(fg.w.log), "gsdx-sweep", trust.current_version(), "drill", "founder")
    fg.cert("ob-one")


def c_f7(fg):                     # a DIFFERENT version is revoked: the current one is untouched
    trust.revoke(fg.w.log, jv._st(fg.w.log), "gsdx-sweep", 1, "drill", "founder")
    fg.cert("ob-one")


def a_f8(fg):
    fg.cert("ob-one", lambda p, _o: p.__setitem__("contract_hash", "0" * 64))


def a_f9(fg):
    def m(p, _own):
        p["premises"] = dict(p["premises"], claim="cross-claim-replay")
    fg.cert("ob-one", m)


def plane(claim, planes, tree):
    def m(p, _own):
        p["plane"] = {"claim": claim, "planes": planes, "modules_tree": tree}
    return m


def a_f11_one(fg):
    fg.cert("ob-one", plane("PORTABILITY", ["windows"], {"windows": "t1"}))


def a_f11_trees(fg):
    fg.cert("ob-one", plane("PORTABILITY", ["windows", "linux"], {"windows": "t1", "linux": "t2"}))


def a_f11_unknown(fg):
    fg.cert("ob-one", plane("PORTABILITY", ["windows", "linux"], {"windows": "t1", "linux": "unknown:dirty"}))


def c_f11(fg):
    fg.cert("ob-one", plane("PORTABILITY", ["windows", "linux"], {"windows": "t1", "linux": "t1"}))


CERT_ATTACKS = [
    ("F3", "unit claim stamped live", a_f3, plain, {"ctl_gate_class": None}),
    ("F4", "lineage parent of another claim", a_f4, c_f4, {}),
    ("F5a", "lineage cycle", a_f5_cycle, c_f5, {}),
    ("F5b", "lineage depth disagrees", a_f5_depth, c_f5, {}),
    ("F6a", "unregistered authority id", a_f6, c_f6, {}),
    ("F6b", "unregistered authority version", a_f6_version, c_f6, {}),
    ("F7", "revoked authority signs again", a_f7, c_f7, {}),
    ("F8", "contract hash names no ledger contract", a_f8, plain, {}),
    ("F9", "premises.claim of another claim", a_f9, plain, {}),
    ("F11a", "PORTABILITY with one plane", a_f11_one, c_f11, {}),
    ("F11b", "PORTABILITY over two different trees", a_f11_trees, c_f11, {}),
    ("F11c", "PORTABILITY over an unknown tree", a_f11_unknown, c_f11, {}),
]


def cert_gate(fid, desc, attack, control, kw):
    memo: dict = {}

    def once():
        if "r" not in memo:
            memo["r"] = attack_vs_control(attack, control)
        return memo["r"]

    def refuse():
        refused, _admitted, ev = once()
        if refused:
            refused_attacks.append(fid)
        return refused, f"{desc}: {ev}"

    def ctl():
        _refused, admitted, ev = once()
        return admitted, ev
    return refuse, ctl


def gate_f3_live_control():
    """F3's control: an obligation whose accepted gate class REALLY is live admits a live certificate."""
    # A live-class claim is never inherited by the judge (its freshness class forbids it), so the strength
    # rule is asked of the verifier directly: it admits a live certificate on a live claim and refuses a
    # certificate stamped live on a unit claim.
    def verdict_of(gate_class, stamp_live):
        fg = FG("fg-strength", gate_class)
        try:
            fg.cert("ob-one")
            led = pf.project_proofs(jv._st(fg.w.log))
            ob = cv.project_convergence(jv._st(fg.w.log)).obligations["ob-one"]
            ev = led.produced[-1]
            if stamp_live:
                ev = dict(ev, data=dict(ev["data"], strength="live"))
            return trust.verify_certificate(led, ev, fg.cids["ob-one"], ob, trust.contract_hashes(led, ob))
        finally:
            fg.close()
    ok_live, why_live = verdict_of("live", False)
    ok_forged, why_forged = verdict_of("unit", True)
    return ok_live and not ok_forged, f"live claim, live cert: {ok_live} ({why_live}); unit claim stamped live: {ok_forged} ({why_forged})"


# --- event / pure attacks ---------------------------------------------------------------

def inherited_case(mutate_event, raw=False):
    """(admitted in inherited_ids) for one forged `proof.inherited` event on a legitimately certified claim."""
    fg = FG("fg-ev")
    try:
        cert = fg.cert("ob-one")
        fg.settle()
        st = jv._st(fg.w.log)
        led = pf.project_proofs(st)
        d = next(e["data"] for e in led.produced if e["data"]["claim_id"] == fg.cids["ob-one"])
        ob = cv.project_convergence(st).obligations["ob-one"]
        current = ih.observe_current(st, ob, fg.contracts["ob-one"], fg.w.repo)
        ev = {"v": 1, "claim_id": fg.cids["ob-one"], "certificate": cert, "candidate": fg.w.tree(),
              "premises": dict(current), "authority": dict(d["authority"])}
        ev = mutate_event(ev) or ev
        if raw:                       # bypass append_pcc: a hand-written event file the writer never vetted
            fg.w.log.append(st.last_seq + 1, pf.INHERITED_EV, ev, "hand")
        else:
            pf.append_pcc(fg.w.log, st, pf.INHERITED_EV, ev, "hand")
        return "ob-one" in ih.inherited_ids(jv._st(fg.w.log), fg.w.tree())
    finally:
        fg.close()


def gate_f1():
    atk = inherited_case(lambda e: e["premises"].__setitem__("fingerprint", "sha256:tampered"))
    ctl = inherited_case(lambda e: None)
    if not atk:
        refused_attacks.append("F1")
    return (not atk) and ctl, f"forged admitted={atk} control admitted={ctl}"


def gate_f2():
    atk = inherited_case(lambda e: e.__setitem__("certificate", "cert:never-produced:1"), raw=True)
    ctl = inherited_case(lambda e: None, raw=True)
    if not atk:
        refused_attacks.append("F2")
    return (not atk) and ctl, f"forged admitted={atk} control admitted={ctl}"


def gate_f10():
    atk = inherited_case(lambda e: e["authority"].__setitem__("strength", "live"), raw=True)
    ctl = inherited_case(lambda e: None, raw=True)
    if not atk:
        refused_attacks.append("F10")
    return (not atk) and ctl, f"forged admitted={atk} control admitted={ctl}"


def gate_f12():
    prem = {"claim": "c", "revision": "r", "gate_pin": [["gate.py", "d"]], "fingerprint": "fp",
            "environment": "env", "policy": 1}
    now = time.time()
    rec = dict(prem, freshness_class="DETERMINISTIC", env_deps=[])
    future = pf.observe_premises(dict(rec, ts=now + 10 * pf.FUTURE_SKEW_S), prem, now)
    fresh = pf.observe_premises(dict(rec, ts=now), prem, now)
    ok = pf.EQUAL not in future.values() and all(v == pf.EQUAL for v in fresh.values())
    if pf.EQUAL not in future.values():
        refused_attacks.append("F12")
    return ok, f"future={sorted(set(future.values()))} control={sorted(set(fresh.values()))}"


def gate_count():
    n = len(set(refused_attacks))
    return n >= 8, f"{n} distinct attacks refused: {sorted(set(refused_attacks))}"


def main() -> int:
    run_gate("V-FORGERY-HERMETIC-HOME", lambda: (jv.Path.home().resolve() == jv._TMP_HOME.resolve(), "tmp home"))
    run_gate("V-FORGERY-F1-REFUSED-WITH-CONTROL", gate_f1)
    run_gate("V-FORGERY-F2-REFUSED-WITH-CONTROL", gate_f2)
    for fid, desc, attack, control, kw in CERT_ATTACKS:
        refuse, ctl = cert_gate(fid, desc, attack, control, kw)
        run_gate(f"V-FORGERY-{fid}-REFUSED", refuse)
        run_gate(f"V-FORGERY-{fid}-CONTROL-ADMITTED", ctl)
    run_gate("V-FORGERY-F3-LIVE-CLASS-CONTROL", gate_f3_live_control)
    run_gate("V-FORGERY-F10-REFUSED-WITH-CONTROL", gate_f10)
    run_gate("V-FORGERY-F12-REFUSED-WITH-CONTROL", gate_f12)
    run_gate("V-FORGERY-COUNT", gate_count)
    total = passes + fails
    print(f"GSDX_TRUST_FORGERY_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
