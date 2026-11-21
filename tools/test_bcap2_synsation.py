"""test_bcap2_synsation.py -- BCAP2-05 Synsation UX gate (V-SYN-*). Run: python3 tools/test_bcap2_synsation.py ; exit 0 iff all pass.

Poles: waiting_pattern / check_disabled_control / check_hit_targets are driven to both answers on declared records;
seeded-red mutants (source text of ux_contracts.py weakened, re-executed) must make a pole assertion FAIL, proving the
assertions can fail; ledger integrity (closed vocabulary, UX-01..20 once each, owner path exists); the two new VP-SYN
patterns parse clean and are withheld on checkout; design_route.ux_findings reaches the module.
Scope honesty: browser-real behaviour (real hitboxes, focus/scroll to first error, CLS, rollback) is NOT verified here; the
source videos are not on GEX44 so wording-dependent claims stay INFERRED.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.cdio import design_route as dr  # noqa: E402
from modules.cdio import motion_patterns as mp  # noqa: E402
from modules.cdio import ux_contracts as ux  # noqa: E402

P = F = 0
VOCAB = {"ALREADY OWNED", "EXTEND", "IMPL-EXEC", "HEURISTIC", "REJECT", "UNVERIFIED"}
HI = {"expressiveness": "high", "motion_budget": "high", "reduced_motion": "equivalent"}
SRC = (ROOT / "modules" / "cdio" / "ux_contracts.py").read_text(encoding="utf-8")


def check(name, cond, detail=""):
    global P, F
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
    if cond:
        P += 1
    else:
        F += 1


def load(src):
    ns = {"__name__": "mutant"}
    exec(compile(src, "ux_mutant", "exec"), ns)
    return ns


def poles(m):
    """The pole assertions as booleans keyed by name, against a module namespace/obj getter m(name)."""
    wp, cd, ch = m("waiting_pattern"), m("check_disabled_control"), m("check_hit_targets")
    t = lambda x, y, w, h, **k: dict(id=k.pop("id"), hit=dict(x=x, y=y, w=w, h=h), **k)  # noqa: E731
    return {
        "flash": wp("control", 80)["pattern"] == "none",
        "skeleton": wp("page", 900, geometry_known=True)["pattern"] == "skeleton",
        "spinner": wp("control", 900)["pattern"] == "spinner",
        "no-fake-progress": wp("page", 5000)["pattern"] != "progress",
        "real-progress": wp("page", 5000, progress_measurable=True)["pattern"] == "progress",
        "optimistic": wp("control", 900, reversible=True, success_likely=True)["pattern"] == "optimistic",
        "no-optimistic-irreversible": wp("control", 900, reversible=True, success_likely=True,
                                         irreversible_critical=True)["pattern"] == "pending-settlement",
        "latency-absent": wp("page", None)["pattern"] is None,
        "opaque": "opaque-disabled-action" in cd({"disabled": True}),
        "obvious-passes": cd({"disabled": True, "reason_visible": True}) == [],
        "pending-visible-passes": cd({"disabled": True, "pending_submission": True, "pending_visible": True}) == [],
        "pending-unseen-opaque": "opaque-disabled-action" in cd({"disabled": True, "pending_submission": True}),
        "clickable": "disabled-but-clickable" in cd({"disabled": True, "reason_visible": True, "click_handler_fires": True}),
        "val-block": "validation-block-with-no-error-path" in cd(
            {"disabled": True, "reason_visible": True, "blocked_by_validation": True}),
        "small": any(d["defect"] == "undersized-hit-target" for d in ch([t(0, 0, 20, 20, id="a")])),
        "big-passes": ch([t(0, 0, 44, 44, id="a")]) == [],
        "absent-rect": any(d["defect"] == "undersized-hit-target" for d in ch([{"id": "a"}])),
        "overlap": any(d["defect"] == "overlapping-hit-targets" for d in ch([t(0, 0, 44, 44, id="a"), t(40, 0, 44, 44, id="b")])),
        "apart-passes": ch([t(0, 0, 44, 44, id="a"), t(60, 0, 44, 44, id="b")]) == [],
        "destructive": any(d["defect"] == "accidental-destructive-hit" for d in
                           ch([t(0, 0, 44, 44, id="a"), t(40, 0, 44, 44, id="b", destructive=True)])),
        "nested": any(d["defect"] == "nested-interactive-steals-tap" for d in
                      ch([t(0, 0, 100, 100, id="card", interactive=True), t(5, 5, 44, 44, id="cta", parent="card")])),
        "nested-stopped-passes": not any(d["defect"] == "nested-interactive-steals-tap" for d in
                                         ch([t(0, 0, 100, 100, id="card", interactive=True),
                                             t(5, 5, 44, 44, id="cta", parent="card", stops_propagation=True)])),
    }


def test_poles():
    print("test_poles")
    res = poles(lambda n: getattr(ux, n))
    for k, v in res.items():
        check(f"V-SYN-POLE[{k}]", v)


def test_mutants():
    print("test_mutants (seeded red: each weakening must flip a named pole)")
    muts = [
        ("flash-guard-off", "latency_ms < SHOW_DELAY_MS", "latency_ms < -1", "flash"),
        ("fake-progress", "progress_measurable and latency_ms >= LONG_MS", "latency_ms >= LONG_MS", "no-fake-progress"),
        ("optimistic-irreversible", "if irreversible_critical:", "if False:", "no-optimistic-irreversible"),
        ("floor-zero", "FLOOR_PX = 44", "FLOOR_PX = 0", "small"),
        ("absent-rect-passes", 'out.append({"id": t.get("id"), "defect": "undersized-hit-target", "detail": "no hit rect declared"})',
         "pass", "absent-rect"),
        ("opaque-ignored", 'out.append("opaque-disabled-action")', "pass", "opaque"),
        ("pending-unseen-exempt", 'rec.get("pending_submission") and rec.get("pending_visible")',
         'rec.get("pending_submission")', "pending-unseen-opaque"),
        ("nested-ignored", 'byid[p].get("interactive") and not t.get("stops_propagation")', "False", "nested"),
        ("overlap-blind", "if _overlap(rects[a], rects[b]):", "if False:", "overlap"),
    ]
    for name, old, new, pole in muts:
        applied = SRC.count(old) >= 1
        res = poles(lambda n, s=SRC.replace(old, new): load(s)[n]) if applied else {}
        check(f"V-SYN-MUTANT[{name}]", applied and res.get(pole) is False,
              f"applied={applied} pole {pole} -> {res.get(pole)}")


def test_ledger():
    print("test_ledger")
    text = (ROOT / "vault/programs/bcap-2/synsation/DISPOSITIONS.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (UX-\d\d) \|[^|]*\| ([A-Z -]+?) \| (\S+) \|", text, re.M)
    ids = [r[0] for r in rows]
    check("V-SYN-LEDGER-COMPLETE", ids == ["UX-%02d" % i for i in range(1, 21)], f"{len(ids)} rows")
    check("V-SYN-LEDGER-VOCAB", all(r[1] in VOCAB for r in rows), str(sorted({r[1] for r in rows} - VOCAB)))
    check("V-SYN-LEDGER-NO-UNVERIFIED-LEFT", not [r[0] for r in rows if r[1] == "UNVERIFIED"], "every UX row has a final disposition")
    missing = [r[2] for r in rows if not (ROOT / r[2]).exists()]
    check("V-SYN-LEDGER-OWNERS-EXIST", not missing, str(missing))


def test_corpus_and_wiring():
    print("test_corpus_and_wiring")
    entries, errs = mp.load_corpus()
    found = {e["id"] for e in entries}
    check("V-SYN-CORPUS-CLEAN", not errs and {"VP-SYN-001", "VP-SYN-002"} <= found, f"errors={errs}")
    dash = {p["id"] for p in mp.resolve(HI, "app/dashboard/orders.tsx")["patterns"]}
    check("V-SYN-POS-DASHBOARD", {"VP-SYN-001", "VP-SYN-002"} <= dash, str(sorted(dash & {"VP-SYN-001", "VP-SYN-002"})))
    pay = {p["id"] for p in mp.resolve(HI, "app/checkout/page.tsx")["patterns"]}
    check("V-SYN-NEG-CHECKOUT", not (pay & {"VP-SYN-001", "VP-SYN-002"}), str(sorted(pay)))
    r = dr.ux_findings(waiting=dict(scope="page", latency_ms=900, geometry_known=True), disabled={"disabled": True}, targets=[])
    check("V-SYN-WIRED-VIA-DESIGN-ROUTE", r["waiting"]["pattern"] == "skeleton" and r["disabled"] == ["opaque-disabled-action"]
          and r["targets"] == [] and set(dr.ux_findings()) == set(), str(r))


if __name__ == "__main__":
    test_poles()
    test_mutants()
    test_ledger()
    test_corpus_and_wiring()
    print(f"\n{P} passed, {F} failed")
    sys.exit(1 if F else 0)
