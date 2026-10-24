"""V-S5-* gates: terminal reconciliation -- a worker that stops is not a mission that ended (flow-compression S5).

Every gate runs through `gates()` against whatever implementation is currently installed, so the mutant drills at
the bottom can swap a broken function in and require at least one gate to go red. UNKNOWN never counts as a pass.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="s5-reconcile-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ.pop("CPP_TERMINAL_RECONCILE", None)
os.environ["CPP_HALT_CONTINUE"] = "off"
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import gsd_epoch as ge  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402
import mission_reconcile as mrc  # noqa: E402
import mission_steward as st  # noqa: E402
import receipt_judge as rj  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
ROOT = Path(TMP).resolve()
NOW = time.time()
_n = [0]
RESULTS: list[tuple[str, bool, str]] = []


def uid(tag: str) -> str:
    _n[0] += 1
    return f"m-s5{tag}{_n[0]:04d}"


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), str(detail)[:200]))


def write(rel: str, text: str) -> Path:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def mission(tag: str, declared: str | None = "x.RECEIPT.json", created: float | None = None) -> dict:
    """A RUNNING mission with a packet; `declared` is its receipt: line (None = no line)."""
    mid = uid(tag)
    pkt = write(f"{mid}/WU.md", f"# WU\nwork_tree: {ROOT}\n" + (f"receipt: {mid}/{declared}\n" if declared else ""))
    gm.create(str(ROOT), "/gsd-autonomous --ws wsx", mission_id=mid, now=created or NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=created or NOW,
                  state=gm.RUNNING, epoch=1)
    gm.set_envelope(mid, wu_packet=str(pkt), now=created or NOW)
    lr.ledger_append(mid, "launch_claimed", mission_id=mid, epoch=1, reason="armed")
    return gm.load(mid)


def receipt(rec: dict, text: str, where: str = "declared") -> Path:
    mid = rec["mission_id"]
    if where == "declared":
        return write(f"{mid}/x.RECEIPT.json", text)
    return gm.stem_receipt(rec["wu_packet"]["path"]).write_text(text, encoding="utf-8") or gm.stem_receipt(
        rec["wu_packet"]["path"])


def slim_finish(rec: dict) -> dict:
    """Drive the real supervise path with a finished slim worker."""
    real = gm.plan_next
    gm.plan_next = lambda r, now, sessions, pid_alive, **k: (
        {"action": "slim_finished", "slim": {"status": "finished", "is_error": False, "tripped": None, "tokens": 1,
                                             "session_id": "s-" + r["mission_id"], "result": "ok"},
         "reason": "slim worker finished"} if r["mission_id"] == rec["mission_id"] else
        {"action": "none", "reason": "other"})
    try:
        gm.supervise(now=NOW + 5, sessions=[], pid_alive=lambda p: False)
    finally:
        gm.plan_next = real
    return gm.load(rec["mission_id"])


def rows_of(mid: str) -> list[dict]:
    return [e for e in lr.ledger_events() if e.get("mission_id") == mid or e.get("session_id") == mid]


def done_text(extra: str = "") -> str:
    return "# receipt\nStatus: DONE\n" + extra


def gates() -> None:
    # ------------------------------------------------------------------ tracer
    a = mission("a")
    receipt(a, done_text())
    fa = slim_finish(a)
    ra = rows_of(a["mission_id"])
    check("V-S5-TRACER-DECLARED-RECEIPT-COMPLETES",
          fa["state"] == gm.COMPLETED and not any(e.get("event") == "mission_halted" for e in ra)
          and sum(e.get("event") == "slim_worker_finished" for e in ra) == 1, fa["state"])
    ea = ge.epochs(a["mission_id"])
    check("V-S5-TRACER-EPOCH-CLOSED", len(ea) == 1 and ea[0]["end"] is not None and ea[0]["end_cause"] == "COMPLETED"
          and ea[0]["end_event"] == "slim_worker_finished", ea)
    check("V-S5-TRACER-RECONCILE-DONE", (r := mrc.reconcile(fa))["outcome"] == mrc.RECOVERED_DONE
          and r["evidence"]["resolver"]["source"] == "PACKET_DECLARED", r)
    b = mission("b")
    fb = slim_finish(b)
    eb = ge.epochs(b["mission_id"])
    check("V-S5-TRACER-MISSING-HALTS", fb["state"] == gm.HALTED and eb[0]["end_cause"] == "HALTED"
          and mrc.reconcile(fb)["outcome"] != mrc.RECOVERED_DONE, (fb["state"], eb[0]["end_cause"]))
    evs = [{"mission_id": "m-z", "event": "launch_claimed", "epoch": 1, "ts": "2026-01-01T00:00:00+00:00"},
           {"mission_id": "m-z", "event": "hold_settled", "state": "HALTED", "seq": 3, "ts": "2026-01-01T01:00:00+00:00"},
           {"mission_id": "m-z", "event": "launch_claimed", "epoch": 2, "ts": "2026-01-01T02:00:00+00:00"}]
    ez = ge.epochs("m-z", evs)
    check("V-S5-TRACER-NOT-OVERWRITTEN", len(ez) == 2 and ez[0]["end_cause"] == "HALTED"
          and ez[0]["end"] == "2026-01-01T01:00:00+00:00" and ez[1]["end"] is None, ez)
    check("V-S5-EPOCH-EVERY-TERMINAL-EVENT", all(
        (ge.epochs("m-y", [{"mission_id": "m-y", "event": "launch_claimed", "epoch": 1, "ts": "t0"},
                           {"mission_id": "m-y", "event": ev, "state": s, "seq": 4, "ts": "t1"}])[0]["end"] == "t1")
        for ev, s in [("slim_worker_finished", "COMPLETED"), ("hold_settled", "HALTED"),
                      ("mission_superseded", "ORPHANED"), ("unit_completed", "COMPLETED"),
                      ("unit_complete", "COMPLETED"), ("owner_hold_released", "HALTED")]), "6 events")
    check("V-S5-EPOCH-MENTION-IS-NOT-TERMINAL", ge.epochs("m-y", [
        {"mission_id": "m-y", "event": "launch_claimed", "epoch": 1, "ts": "t0"},
        {"mission_id": "m-y", "event": "note", "state": "HALTED", "ts": "t1"}])[0]["end"] is None)

    # ------------------------------------------------------------------ resolver
    c = mission("c")                       # declared receipt exists, stem does not
    receipt(c, done_text())
    rc = gm.resolve_receipt(c["wu_packet"]["path"], c)
    check("V-S5-RESOLVER-DECLARED-WINS-OVER-ABSENT-STEM", rc["present"] and rc["source"] == "PACKET_DECLARED"
          and not rc["conflict"] and gm._receipt_present(c), rc)
    d = mission("d", declared=None)
    rd = gm.resolve_receipt(d["wu_packet"]["path"], d)
    check("V-S5-RESOLVER-STEM-DEFAULT-WHEN-NONE-EXIST", rd["source"] == "STEM" and not rd["present"]
          and rd["path"].endswith(gm.receipt_name("WU")), rd)
    pk = write("resid/X.md", "# X\n")
    chain = write("resid/chain.json", json.dumps({"units": [{"packet": str(pk), "receipt": str(ROOT / "resid/unit.rcpt")}]}))
    real_dc = None
    try:
        import gsdx_chain as gc
        real_dc = gc.discover_chains
        gc.discover_chains = lambda base, pd=None: [chain] if str(base) == str(pk) else []
        rr = gm.resolve_receipt(str(pk) + ".residual.md", None)
        check("V-S5-RESOLVER-CHAIN-BEATS-STEM-WHEN-NONE-EXIST", rr["source"] == "CHAIN_UNIT"
              and rr["path"].endswith("unit.rcpt"), rr)
    finally:
        if real_dc:
            gc.discover_chains = real_dc
    e = mission("e")
    receipt(e, done_text())
    gm.stem_receipt(e["wu_packet"]["path"]).write_text("# r\nStatus: PARTIAL\n", encoding="utf-8")
    re_ = gm.resolve_receipt(e["wu_packet"]["path"], e)
    check("V-S5-RESOLVER-CONFLICT", re_["conflict"] and not gm._receipt_present(e), re_)
    for nm, line in (("dotdot", "../../escape.json"), ("abs", "/etc/hostname")):
        t = mission("t" + nm[:1])
        write(f"{t['mission_id']}/WU.md", f"# WU\nwork_tree: {ROOT}\nreceipt: {line}\n")
        r = gm.resolve_receipt(t["wu_packet"]["path"], t)
        check(f"V-S5-RESOLVER-TRAVERSAL-REFUSED-{nm.upper()}", all(x["source"] != "PACKET_DECLARED" for x in r["candidates"]), r)
    outside = Path(tempfile.mkdtemp(prefix="s5-out-"))
    (outside / "o.json").write_text(done_text(), encoding="utf-8")
    t = mission("tl")
    link = ROOT / t["mission_id"] / "link"
    link.symlink_to(outside)
    write(f"{t['mission_id']}/WU.md", f"# WU\nwork_tree: {ROOT}\nreceipt: {t['mission_id']}/link/o.json\n")
    r = gm.resolve_receipt(t["wu_packet"]["path"], t)
    check("V-S5-RESOLVER-TRAVERSAL-REFUSED-SYMLINK", all(x["source"] != "PACKET_DECLARED" for x in r["candidates"]) and not r["present"], r)
    amr_pkt = write("amr/succ.md", f"# S\nwork_tree: {ROOT}\nreceipt: amr/succ.RECEIPT.json\n")
    write("amr/succ.RECEIPT.json", done_text())
    r = gm.resolve_receipt(str(amr_pkt), {**c, "wu_packet": {"path": str(amr_pkt)}})
    check("V-S5-RESOLVER-AMR-SUCCESSOR", r["present"] and r["source"] == "PACKET_DECLARED", r)
    f = mission("f")
    receipt(f, done_text())
    check("V-S5-STEWARD-SEES-RESOLVER-CLOSED", st._r1(gm, f, NOW, ledger_for=lambda *a: [], transcript_for=lambda s: None,
                                                     dry_run=True, index={}) is None)
    receipt(e, "# r\nStatus: DONE\n")  # keep e conflicted via stem PARTIAL
    ro = st._r1(gm, e, NOW, ledger_for=lambda *a: [], transcript_for=lambda s: None, dry_run=True, index={})
    check("V-S5-STEWARD-CONFLICT-IS-UNKNOWN", ro and ro["action"] == "UNKNOWN" and "conflicting" in ro["reason"], ro)

    # ------------------------------------------------------------------ reconcile rules
    pos = mission("p", created=NOW - 100)
    receipt(pos, done_text())
    check("V-S5-RECONCILE-POSITIVE", mrc.reconcile(pos)["outcome"] == mrc.RECOVERED_DONE)
    # continuation variants
    def stopped(tag):
        m = mission(tag)
        gm.transition(m["mission_id"], expect_epoch=1, expect_state=gm.RUNNING, event="mission_halted",
                      state=gm.HALTED, reason="owner BLOCKED", now=NOW)
        return gm.load(m["mission_id"])
    s1, succ = stopped("c1"), mission("c2")
    lr.ledger_append(s1["mission_id"], "mission_renewed", mission_id=s1["mission_id"], successor=succ["mission_id"])
    r1 = mrc.reconcile(s1)
    s2, succ2 = stopped("c3"), mission("c4")
    lr.ledger_append(s2["mission_id"], "mission_superseded", mission_id=s2["mission_id"], superseded_by=succ2["mission_id"])
    r2 = mrc.reconcile(s2)
    s3, succ3 = stopped("c5"), mission("c6")
    gm.transition(s3["mission_id"], expect_epoch=1, expect_state=gm.HALTED, event="t_amr", amr={"packet": succ3["wu_packet"]["path"]}, now=NOW)
    r3 = mrc.reconcile(gm.load(s3["mission_id"]))
    check("V-S5-RECONCILE-CONTINUATION", all(x["outcome"] == mrc.CONTINUATION for x in (r1, r2, r3))
          and r1["evidence"]["tail"] == succ["mission_id"], [x["outcome"] for x in (r1, r2, r3)])
    # failed
    fl = stopped("f1")
    rfl = mrc.reconcile(fl)
    clo = mission("f2")
    receipt(clo, "# r\nStatus: BLOCKED_HUMAN\n")
    check("V-S5-RECONCILE-FAILED", rfl["outcome"] == mrc.FAILED and mrc.reconcile(clo)["outcome"] == mrc.FAILED
          and mrc.reconcile(clo)["evidence"]["status"] == "BLOCKED_HUMAN", (rfl["outcome"], mrc.reconcile(clo)["outcome"]))
    # ambiguous, one case per bullet
    amb = []
    amb.append(mrc.reconcile(e)["outcome"])                                       # conflict
    for stt in ("IN_PROGRESS", "PARTIAL", "STUB"):
        m = mission("a" + stt[:2].lower())
        receipt(m, f"# r\nStatus: {stt}\n" if stt != "STUB" else "stub\nStatus: DONE\n")
        amb.append(mrc.reconcile(m)["outcome"])
    m = mission("au")
    receipt(m, "no verdict here\n")
    amb.append(mrc.reconcile(m)["outcome"])                                       # UNREADABLE
    m = mission("ad")
    p_ = receipt(m, done_text("Claims: n=5\n"))
    rj.certificate_path(p_).write_text(json.dumps({"measured": {"n": 9}}), encoding="utf-8")
    amb.append(mrc.reconcile(m)["outcome"])                                       # DIVERGENT (if sidecar is read)
    old = mission("ao", created=NOW + 10_000)
    receipt(old, done_text())
    amb.append(mrc.reconcile(old)["outcome"])                                     # DONE older than the mission
    nos = stopped("an")
    lr.ledger_append(nos["mission_id"], "mission_renewed", mission_id=nos["mission_id"], successor="m-ghost")
    amb.append(mrc.reconcile(nos)["outcome"])                                     # successor without a record
    cy1, cy2 = stopped("y1"), stopped("y2")
    lr.ledger_append(cy1["mission_id"], "mission_renewed", mission_id=cy1["mission_id"], successor=cy2["mission_id"])
    lr.ledger_append(cy2["mission_id"], "mission_renewed", mission_id=cy2["mission_id"], successor=cy1["mission_id"])
    amb.append(mrc.reconcile(cy1)["outcome"])                                     # cycle
    chain_ids = [stopped(f"h{i}") for i in range(10)]
    for i in range(9):
        lr.ledger_append(chain_ids[i]["mission_id"], "mission_renewed", mission_id=chain_ids[i]["mission_id"],
                         successor=chain_ids[i + 1]["mission_id"])
    deep = mrc.reconcile(chain_ids[0])
    amb.append(deep["outcome"])                                                   # depth > 8
    nopk = {**pos, "wu_packet": None}
    amb.append(mrc.reconcile(nopk)["outcome"])
    amb.append(mrc.reconcile(pos, events=[None])["outcome"] if False else mrc.reconcile({"mission_id": "m-x", "wu_packet": {"path": 5}})["outcome"])
    check("V-S5-RECONCILE-AMBIGUOUS", all(x == mrc.AMBIGUOUS for x in amb), amb)
    # no false DONE matrix
    statuses = {"missing": None, "STUB": "stub\nStatus: DONE\n", "UNREADABLE": "nothing\n", "IN_PROGRESS": "Status: IN_PROGRESS\n",
                "PARTIAL": "Status: PARTIAL\n", "FAILED": "Status: FAILED\n", "BLOCKED_HUMAN": "Status: BLOCKED_HUMAN\n",
                "DONE_WITH_LIMITS": "Status: DONE_WITH_LIMITS\n", "DONE": "Status: DONE\n"}
    cells = bad = 0
    for name, text in list(statuses.items()) + [("DONE_STALE", "Status: DONE\n"), ("DIVERGENT", "Status: DONE\nClaims: n=5\n")]:
        for succ_ in (False, True):
            for conf in (False, True):
                m = stopped("x")
                if name == "DONE_STALE":
                    m = {**m, "created_at": NOW + 99999}
                if text is not None:
                    p_ = receipt(m, text)
                    if name == "DIVERGENT":
                        rj.certificate_path(p_).write_text(json.dumps({"measured": {"n": 9}}), encoding="utf-8")
                if conf:
                    gm.stem_receipt(m["wu_packet"]["path"]).write_text("Status: PARTIAL\n", encoding="utf-8")
                if succ_:
                    sx = mission("xs")
                    lr.ledger_append(m["mission_id"], "mission_renewed", mission_id=m["mission_id"], successor=sx["mission_id"])
                got = mrc.reconcile(m)["outcome"]
                want = (name == "DONE" and not conf)
                cells += 1
                bad += (got == mrc.RECOVERED_DONE) != want
    check("V-S5-NO-FALSE-DONE-MATRIX", cells == 44 and bad == 0, f"cells={cells} wrong={bad}")

    # ------------------------------------------------------------------ inventory
    mods = [TOOLS / n for n in ("gsd_mission.py", "mission_steward.py", "mission_recovery.py", "mission_reconcile.py")]
    check("V-S5-RECEIPT-INVENTORY", inventory(mods) == ["receipt_name"], inventory(mods))
    ctl = ast.parse('def good():\n    """x-receipt.md in doc"""\n    return 1\ndef bad():\n    return "a-receipt.md"\n')
    check("V-S5-RECEIPT-INVENTORY-CONTROL", walk_literals(ctl) == ["bad"], walk_literals(ctl))

    # ------------------------------------------------------------------ dispose / read-only / switch
    dispose_gates()


def walk_literals(tree: ast.AST) -> list[str]:
    hits: list[str] = []

    def visit(node, fn, doc_ids):
        for ch in ast.iter_child_nodes(node):
            f = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and ch.body \
                    and isinstance(ch.body[0], ast.Expr) and isinstance(getattr(ch.body[0], "value", None), ast.Constant):
                doc_ids.add(id(ch.body[0].value))
            if isinstance(ch, ast.Constant) and isinstance(ch.value, str) and "-receipt.md" in ch.value \
                    and id(ch) not in doc_ids:
                hits.append(fn or "<module>")
            visit(ch, f, doc_ids)
    visit(tree, None, set())
    return sorted(set(hits))


def inventory(mods: list[Path]) -> list[str]:
    out: list[str] = []
    for m in mods:
        out += walk_literals(ast.parse(m.read_text(encoding="utf-8")))
    return sorted(set(out))


def snapshot() -> str:
    h = hashlib.sha256()
    for p in sorted(Path(TMP).rglob("*")):
        if p.is_file() and (p.name.endswith(".jsonl") or p.name.endswith(".json") and "missions" in str(p)):
            h.update(p.read_bytes())
    lp = lr.ledger_path()
    h.update(lp.read_bytes() if lp.is_file() else b"")
    return h.hexdigest()


def dispose_gates() -> None:
    # fixture: dedicated event list + records, independent of the live temp ledger
    T = 1_800_000_000.0
    iso = lambda t: time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(t))  # noqa: E731
    recs, ev = [], []

    def rec(mid, state, pkt=None):
        r = {"mission_id": mid, "state": state, "created_at": T, "cwd": str(ROOT),
             "wu_packet": {"path": str(pkt)} if pkt else None}
        recs.append(r)
        return r

    def row(mid, name, t, **kw):
        ev.append({"ts": iso(t), "session_id": mid, "mission_id": mid, "event": name, **kw})

    # D done
    pd = write("disp/d.md", f"# WU\nwork_tree: {ROOT}\nreceipt: disp/d.json\n")
    write("disp/d.json", done_text())
    os.utime(ROOT / "disp/d.json", (T + 500, T + 500))
    rec("m-dd", "HALTED", pd)
    row("m-dd", "launch_claimed", T)
    row("m-dd", "mission_halted", T + 3600, state="HALTED", seq=2, reason="x")
    # C continuation
    pc = write("disp/c.md", f"# WU\nwork_tree: {ROOT}\n")
    rec("m-cc", "HALTED", pc)
    rec("m-cs", "RUNNING", None)
    row("m-cc", "launch_claimed", T)
    row("m-cc", "mission_halted", T + 3600, state="HALTED", seq=2, reason="x")
    row("m-cc", "mission_renewed", T + 3700, successor="m-cs")
    row("m-cs", "launch_claimed", T + 3600 + 1800)
    # F failed
    pf = write("disp/f.md", f"# WU\nwork_tree: {ROOT}\n")
    rec("m-ff", "HALTED", pf)
    row("m-ff", "launch_claimed", T)
    row("m-ff", "mission_halted", T + 7200, state="HALTED", seq=2, reason="budget")
    # U ambiguous (halted, no reason)
    pu = write("disp/u.md", f"# WU\nwork_tree: {ROOT}\n")
    rec("m-uu", "ORPHANED", pu)
    row("m-uu", "launch_claimed", T)
    row("m-uu", "mission_superseded", T + 1000, state="ORPHANED", seq=2)
    # N no terminal row
    rec("m-nn", "HALTED", pu)
    row("m-nn", "launch_claimed", T + 10)
    now = T + 4 * 3600
    h0 = snapshot()
    rep = mrc.dispose(events=ev, now=now, missions=recs)
    per = {p["id"]: p for p in rep["per_mission"]}
    cons = all(abs(sum(p[b] for b in mrc.BUCKETS) - (now - {"m-dd": T + 3600, "m-cc": T + 3600, "m-ff": T + 7200,
                                                          "m-uu": T + 1000}[p["id"]]) / 3600) < 1e-3 for p in rep["per_mission"])
    outs = {i: per[i]["outcome"] for i in per}
    check("V-S5-DISPOSE-PARTITION-CONSERVES", cons and len(per) == 4 and outs == {
        "m-dd": mrc.RECOVERED_DONE, "m-cc": mrc.CONTINUATION, "m-ff": mrc.FAILED, "m-uu": mrc.AMBIGUOUS}
          and abs(per["m-cc"]["idle_to_successor_h"] - 0.5) < 1e-3, outs)
    check("V-S5-DISPOSE-UNMEASURED-SEPARATE", [u["id"] for u in rep["unmeasured"]] == ["m-nn"] and "m-nn" not in per, rep["unmeasured"])
    ev2 = [{"ts": iso(T), "session_id": "m-o1", "mission_id": "m-o1", "event": "launch_claimed"},
           {"ts": iso(T + 3600), "session_id": "m-o2", "mission_id": "m-o2", "event": "launch_claimed"},
           {"ts": iso(T + 7200), "session_id": "m-o1", "mission_id": "m-o1", "event": "mission_halted", "state": "HALTED", "seq": 1},
           {"ts": iso(T + 7200), "session_id": "m-o2", "mission_id": "m-o2", "event": "mission_halted", "state": "HALTED", "seq": 1}]
    r2 = mrc.dispose(events=ev2, now=T + 7200, missions=[{"mission_id": "m-o1", "state": "HALTED", "wu_packet": None},
                                                         {"mission_id": "m-o2", "state": "HALTED", "wu_packet": None}])
    check("V-S5-DISPOSE-SUMMED-VS-UNION", abs(r2["summed_mission_h"] - 3.0) < 1e-3 and abs(r2["union_wall_h"] - 2.0) < 1e-3, (r2["summed_mission_h"], r2["union_wall_h"]))
    check("V-S5-DISPOSE-149-NOT-MEASURED", "LAPTOP-ONLY" in rep["quoted_not_measured"] and "149" not in json.dumps(
        {k: v for k, v in rep.items() if k != "quoted_not_measured"}), "")
    # read-only on the live temp ledger/records
    x = mission("ro")
    receipt(x, done_text())
    before = snapshot()
    mrc.reconcile(x)
    mrc.dispose()
    check("V-S5-READONLY", snapshot() == before and h0 == h0, "")
    # supervisor: annotation and switch
    k1 = mission("k1")
    f1 = slim_finish(k1)
    n_on = sum(e.get("event") == "terminal_reconciled" for e in rows_of(k1["mission_id"]))
    os.environ["CPP_TERMINAL_RECONCILE"] = "off"
    try:
        k2 = mission("k2")
        f2 = slim_finish(k2)
        n_off = sum(e.get("event") == "terminal_reconciled" for e in rows_of(k2["mission_id"]))
    finally:
        os.environ.pop("CPP_TERMINAL_RECONCILE", None)
    check("V-S5-KILL-SWITCH", n_on == 1 and n_off == 0 and f1["state"] == f2["state"] == gm.HALTED, (n_on, n_off, f1["state"], f2["state"]))
    k3 = mission("k3")
    receipt(k3, done_text())
    slim_finish(k3)
    names = {e.get("event") for e in rows_of(k3["mission_id"]) + rows_of(k1["mission_id"])}
    allowed = {"launch_claimed", "slim_worker_finished", "terminal_reconciled", "mission_prepared", "t_setup",
               "mission_created", "envelope_set", "mission_envelope_set"}
    extra = {n for n in names if n not in allowed and not str(n).startswith(("mission_", "envelope", "t_"))}
    check("V-S5-NO-SPEND-NO-TRANSITION", not extra and "mission_renewed" not in names, sorted(extra))
    check("V-S5-FC10-NO-NEW-STATE", set(gm.STATES) == {"PREPARED", "LAUNCHING", "RUNNING", "HANDOFF_REQUESTED", "BLOCKED",
                                                       "COMPLETED", "HALTED", "ORPHANED"}, sorted(gm.STATES))


def run_once() -> tuple[int, int]:
    RESULTS.clear()
    gates()
    p = sum(1 for _, ok, _ in RESULTS if ok)
    return p, len(RESULTS) - p


def mutant(name: str, install, restore) -> None:
    install()
    try:
        _, f = run_once()
    except Exception as exc:  # noqa: BLE001 -- a crash is a red run, which is what a mutant must produce
        f = 1
        print(f"  ({name} crashed: {type(exc).__name__})")
    finally:
        restore()
    DRILLS.append((name, f > 0))


DRILLS: list[tuple[str, bool]] = []


def main() -> int:
    p, f = run_once()
    for n, ok, d in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'} {n} {'' if ok else d}")
    base_ok = f == 0
    keep = list(RESULTS)
    real = {k: getattr(gm, k) for k in ("resolve_receipt", "_receipt_present")}
    real_term, real_rec = ge.is_terminal_row, mrc.reconcile

    def swap(obj, attr, fn):
        old = getattr(obj, attr)
        setattr(obj, attr, fn)
        return lambda: setattr(obj, attr, old)
    r = {}

    def inst(obj, attr, fn):
        return lambda: r.__setitem__(attr, swap(obj, attr, fn))
    rs = lambda: r.pop("x", None) and None  # noqa: E731

    def drill(name, obj, attr, fn):
        old = getattr(obj, attr)
        mutant(name, lambda: setattr(obj, attr, fn(old)), lambda: setattr(obj, attr, old))

    drill("M-EPOCH-ONLY-HALTED", ge, "is_terminal_row", lambda o: (lambda e: e.get("event") in ("mission_halted", "mission_completed")))
    drill("M-RESOLVER-STEM-ONLY", gm, "resolve_receipt", lambda o: (lambda pkt, rec=None, pd=None: {
        **o(pkt, rec, pd), **{"path": str(gm.stem_receipt(pkt)), "source": "STEM", "present": rj.receipt_status(gm.stem_receipt(pkt)) is not None,
                              "status": rj.receipt_status(gm.stem_receipt(pkt)), "conflict": False}}))
    drill("M-RESOLVER-FIRST-NOT-PRESENT", gm, "resolve_receipt", lambda o: (lambda pkt, rec=None, pd=None: (
        lambda x: {**x, "path": x["candidates"][-1]["path"], "status": x["candidates"][-1]["status"],
                   "present": x["candidates"][-1]["status"] is not None, "source": x["candidates"][-1]["source"]})(o(pkt, rec, pd))))
    drill("M-RECONCILE-ALWAYS-DONE", mrc, "reconcile", lambda o: (lambda rec, **k: (
        lambda x: {**x, "outcome": mrc.RECOVERED_DONE} if x["evidence"].get("resolver", {}).get("status") is not None else x)(o(rec, **k))))
    drill("M-RECONCILE-IGNORE-CONFLICT", gm, "resolve_receipt", lambda o: (lambda pkt, rec=None, pd=None: {**o(pkt, rec, pd), "conflict": False}))
    drill("M-RECONCILE-NO-SUCCESSOR", mrc, "_successor_id", lambda o: (lambda *a, **k: (None, None)))
    drill("M-RECONCILE-STALE-OK", mrc, "reconcile", lambda o: (lambda rec, **k: o({**rec, "created_at": 0}, **k)))
    drill("M-DISPOSE-ALL-LOST", mrc, "reconcile", lambda o: (lambda rec, **k: {"outcome": mrc.FAILED, "reason": "m", "evidence": {}}))
    drill("M-WIRING-LEGACY-PRESENT", gm, "_receipt_present", lambda o: (lambda rec, programs_dir=None: gm.rj.is_closed(
        gm.stem_receipt((rec.get("wu_packet") or {}).get("path") or "x")) if (rec.get("wu_packet") or {}).get("path") else True))
    real_inv = globals()["inventory"]
    mutant("M-INVENTORY-SECOND-SITE", lambda: globals().__setitem__("inventory", lambda mods: real_inv(mods) + ["second_builder"]),
           lambda: globals().__setitem__("inventory", real_inv))
    RESULTS.clear()
    RESULTS.extend(keep)
    for name, red in DRILLS:
        print(f"{'PASS' if red else 'FAIL'} V-S5-MUTANT-{name} {'went red' if red else 'STAYED GREEN'}")
        RESULTS.append((name, red, ""))
    passes = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    fails = total - passes
    print(f"S5_PASS={passes}/{total}")
    return 0 if fails == 0 and base_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
