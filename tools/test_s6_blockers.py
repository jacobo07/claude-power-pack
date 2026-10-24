#!/usr/bin/env python
"""V-S6-* gates: the blocker compiler -- every BLOCKED / Owner-hold park is typed (flow-compression S6, FC-08).

Every gate runs through `gates()` against whatever implementation is installed, so the mutant drills at the bottom
can swap a broken function in and require at least one gate to go red. UNKNOWN / INCONCLUSIVE never count as a pass.

Controls checked against the REAL reader before they count (Phase 5 incident): the OLD_* key sets below were captured
by running the HEAD (cea6b85b) writer through the real supervise seam; the census strings are copied from the host
ledger's own mission_blocked reasons; the kill-switch twin runs the same real writer with the switch off.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="s6-blockers-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["PP_OWNER_QUEUE_STATE_DIR"] = str(Path(TMP) / "owner-queue")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ.pop("CPP_BLOCKER_COMPILE", None)
os.environ.pop("CPP_FORESEEABLE_DECISIONS", None)
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS.parent))
import blocker_compiler as bc  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402

ROOT = Path(TMP).resolve()
NOW = 1_800_000_000.0
_n = [0]
RESULTS: list[tuple[str, bool, str]] = []

# Captured from the HEAD (cea6b85b) writer through the real supervise seam, BEFORE block_mission existed.
OLD_RECORD_KEYS = {"add_dirs", "allowed_tools", "blocked_intent", "code_id", "created_at", "cwd", "epoch",
                   "failed_launches", "iterations", "last_progress_at", "max_cycles", "max_hours", "mission_id",
                   "mission_terms", "mode", "note", "owner", "pending", "permission_mode", "progress_unknown",
                   "reason", "resume_command", "schema_version", "seq", "state", "token_estimate",
                   "token_estimate_basis", "token_estimate_src", "updated_at", "wall", "workstream"}
OLD_LEDGER_KEYS = {"code", "epoch", "event", "mission_id", "reason", "seq", "session_id", "state", "ts"}
OLD_HOLD_KEYS = {"reason", "set_at"}
NEW_LEDGER_KEYS = {"blocker_class", "independent_work", "owner_required", "unblock_kind"}


class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), str(detail)[:200]))


def uid(tag: str) -> str:
    _n[0] += 1
    return f"m-s6{tag}{_n[0]:04d}"


def fresh_missions() -> None:
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()


def supervised_block(needs: str, tag: str = "b") -> tuple[str, dict]:
    """A RUNNING background mission whose host row says blocked, supervised once with the host's ask `needs`."""
    fresh_missions()
    mid = uid(tag)
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING, epoch=1,
                  owner={"session_id": f"s-{mid}", "pid": 5151, "kind": "background"})
    hs = [{"sessionId": f"s-{mid}", "status": "waiting", "waitingFor": "owner", "state": "blocked",
           "kind": "background", "id": f"s-{mid}"[:8], "pid": 999}]
    real = gm.host_job_needs
    gm.host_job_needs = lambda sid: needs
    try:
        gm.supervise(now=NOW, sessions=hs, gsd_status=lambda c, workstream=None: {"outcome": "OK", "reason": "ok"},
                     runner=lambda argv, cwd: R("backgrounded · 9e9e9e9e · x"),
                     stop_runner=lambda argv: R("stopped"), pid_alive=lambda p: True)
    finally:
        gm.host_job_needs = real
    return mid, gm.load(mid)


def ledger_rows(mid: str, event: str) -> list[dict]:
    return [r for r in lr.ledger_events(mid) if r.get("event") == event]


def held_mission(tag: str = "h") -> str:
    fresh_missions()
    mid = uid(tag)
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING, epoch=1,
                  owner={"session_id": f"s-{mid}", "pid": 5151, "kind": "background"})
    return mid


def tracer_gates() -> None:
    # --- the thinnest real path: host-blocked worker -> supervise -> surface_blocked -> block_mission -> compiler
    mid, rec = supervised_block("Choose 1 or run /compact")
    b = rec.get("blocker") or {}
    cb = gm.current_blocker(rec) or {}
    rows = ledger_rows(mid, "mission_blocked")
    check("V-S6-TRACER-SURFACE-BLOCKED-TYPED",
          rec["state"] == gm.BLOCKED and b.get("class") == "DECISION_REQUEST"
          and (b.get("unblock_condition") or {}).get("kind") == "owner_act" and b.get("owner_required") is True
          and b.get("independent_work") is False and bool(b.get("independent_reason"))
          and cb.get("class") == "DECISION_REQUEST" and len(rows) == 1
          and rows[0].get("blocker_class") == "DECISION_REQUEST" and rows[0].get("independent_work") is False,
          f"class={b.get('class')} cond={b.get('unblock_condition')} row={ {k: rows[0].get(k) for k in NEW_LEDGER_KEYS} if rows else None}")

    # --- kill switch: the exact old record and ledger shape, from the same real writer
    on_rec_keys, on_row_keys = set(rec), set(rows[0]) if rows else set()
    os.environ["CPP_BLOCKER_COMPILE"] = "off"
    try:
        mid_off, rec_off = supervised_block("Choose 1 or run /compact", "k")
        rows_off = ledger_rows(mid_off, "mission_blocked")
    finally:
        os.environ.pop("CPP_BLOCKER_COMPILE", None)
    off_ok = (set(rec_off) == OLD_RECORD_KEYS and bool(rows_off) and set(rows_off[0]) == OLD_LEDGER_KEYS
              and "blocker" not in rec_off)
    on_differs = on_rec_keys == OLD_RECORD_KEYS | {"blocker"} and on_row_keys == OLD_LEDGER_KEYS | NEW_LEDGER_KEYS
    check("V-S6-TRACER-KILLSWITCH-OLD-SHAPE", off_ok and on_differs,
          f"off_extra={sorted(set(rec_off) - OLD_RECORD_KEYS)} off_missing={sorted(OLD_RECORD_KEYS - set(rec_off))} "
          f"on_extra={sorted(on_rec_keys - OLD_RECORD_KEYS)}")

    # --- a compiler fault never stops the BLOCKED write; it lands as UNKNOWN naming the exception class
    real = bc.compile_blocker

    def boom(*a, **k):
        raise RuntimeError("compiler exploded")
    bc.compile_blocker = boom
    try:
        mid_f, rec_f = supervised_block("Choose 1 or run /compact", "f")
    finally:
        bc.compile_blocker = real
    bf = rec_f.get("blocker") or {}
    check("V-S6-TRACER-FAIL-OPEN",
          rec_f["state"] == gm.BLOCKED and bf.get("class") == "UNKNOWN" and bf.get("compile_error") == "RuntimeError"
          and bf.get("independent_work") is False,
          f"state={rec_f['state']} blocker={bf.get('class')}/{bf.get('compile_error')}")

    # --- UNKNOWN is reachable and is never independent work, even with a runnable next unit on offer
    runnable = {"measured": True, "reason": "ok", "current": 1.0, "units": [1.0, 2.0], "candidates": [2.0]}
    u = bc.compile_blocker("host lists session blocked (no waitingFor); host needs: open this session to continue setup",
                           evidence=runnable)
    check("V-S6-TRACER-UNKNOWN-REACHABLE",
          u["class"] == "UNKNOWN" and u["independent_work"] is False and u["owner_required"] is True
          and u["independent_reason"] == "unclassified", f"{u['class']} {u['independent_reason']}")

    # --- census over a ledger written by the real writer shape: populations and compiled counts agree
    led = Path(TMP) / "census-fixture.jsonl"
    reasons = ["host: waiting for permission prompt", "host: waiting for input needed",
               "host lists session blocked (no waitingFor); host needs: rate limited — wait and retry · You've hit your weekly limit · resets Oct 7, 7am (Europe/Berlin)",
               "host lists session blocked (no waitingFor); host needs: run /clear",
               "gsd NO_PHASES on 2 consecutive passes (300 s): GSD parses 0 phases from ROADMAP.md -- no relay until GSD answers OK",
               "totally unrecognised reason text"]
    with led.open("w", encoding="utf-8") as fh:
        for r in reasons:
            fh.write(json.dumps({"event": "mission_blocked", "reason": r, "session_id": "m-x"}) + "\n")
        fh.write(json.dumps({"event": "owner_hold_set", "reason": "owner hold: Owner reviewing", "session_id": "m-x"}) + "\n")
        fh.write("not json\n")
        fh.write(json.dumps({"event": "unrelated"}) + "\n")
    c = bc.census(led)
    cls = {k: v["count"] for k, v in c["classes"].items()}
    host = bc.census()
    host_ok = host["rows"] == 0 or (sum(v["count"] for v in host["classes"].values())
                                    == sum(n for e, n in host["populations"].items() if e != "blocked_intent"))
    check("V-S6-TRACER-CENSUS-POPULATION",
          c["populations"]["mission_blocked"] == 6 and c["populations"]["owner_hold_set"] == 1
          and cls == {"HOST_GATE": 2, "PROVIDER_LIMIT": 1, "COMMAND_REQUEST": 1, "GSD_HOLD": 1, "UNKNOWN": 1,
                      "OWNER_PARK": 1} and c["rows"] == 8 and host_ok, f"{cls} host_rows={host['rows']}")


# ------------------------------------------------------------------------------------------------ Task 2: batching
from modules.owner_queue import owner_queue as oq  # noqa: E402

ASK = {"push": "OWNER DECISION NEEDED: push the branch to origin",
       "deploy": "Owner must approve the deploy to production",
       "capital": "awaiting the Owner: raise the capital ceiling by 30M tokens",
       "protect": "requires the Owner to remove the branch protection on main"}
PREF = "Owner must decide the preferred worktree layout, your call"
REPO = TOOLS.parent
WS = "fx"


def fixture(lines=(), roadmap: bool = True, config: dict | None = None) -> str:
    _n[0] += 1
    cwd = ROOT / f"fx-{_n[0]}"
    (cwd / "vault" / "specs").mkdir(parents=True)
    (cwd / ".planning" / "workstreams" / WS).mkdir(parents=True)
    (cwd / "vault" / "specs" / f"{WS}.md").write_text("# spec\n\n" + "\n".join(f"- {x}" for x in lines) + "\n",
                                                      encoding="utf-8")
    if roadmap:
        (cwd / ".planning" / "workstreams" / WS / "ROADMAP.md").write_text("# roadmap\n", encoding="utf-8")
    (cwd / ".planning" / "workstreams" / WS / "STATE.md").write_text("---\ncurrent_phase: 1\n---\n", encoding="utf-8")
    if config is not None:
        (cwd / ".planning" / "config.json").write_text(json.dumps(config), encoding="utf-8")
    return str(cwd)


def qdir() -> str:
    d = Path(TMP) / f"oq-{_n[0]}-{time.time_ns()}"
    os.environ["PP_OWNER_QUEUE_STATE_DIR"] = str(d)
    return str(d)


def batched_rows(cwd: str) -> list[dict]:
    return [r for r in lr.ledger_events("arm-preflight") if r.get("event") == "owner_decisions_batched"
            and r.get("cwd") == str(cwd)]


def arm_once(cwd: str) -> dict:
    fresh_missions()   # one non-terminal attempt per goal: the previous attempt is gone, its ledger rows are not
    return gm.arm(cwd, "/gsd-autonomous", launch=False, workstream=WS)["mission"]


def sort_ids(fd):
    return sorted(i["id"] for i in fd["items"])


def batch_gates() -> None:
    cwd = fixture(ASK.values())
    fd = bc.foreseeable_decisions(cwd, WS)
    cat = {i["text"]: i for i in fd["items"]}
    push, dep = cat.get(ASK["push"], {}), cat.get(ASK["deploy"], {})
    fd2 = bc.foreseeable_decisions(fixture(["", *ASK.values()]), WS)
    verdicts_ok = (bc._autonomy_for(ASK["push"]).get("owner") == "OWNER"
                   and bc._autonomy_for(ASK["deploy"]).get("owner") == "OWNER"
                   and bool(bc.PROTECTED.search(ASK["capital"])) and bool(bc.PROTECTED.search(ASK["protect"])))
    import re as _re
    check("V-S6-BATCH-ITEMS",
          verdicts_ok and fd["measured"] and len(fd["items"]) == 4
          and all(_re.fullmatch(r"OD-[0-9a-f]{8}", i["id"]) and i["resolution"] == "OWNER" and i["line"] > 0
                  and i["source"].endswith(f"{WS}.md") for i in fd["items"])
          and push.get("kind") == "git-push" and dep.get("kind") == "deploy"
          and sort_ids(fd) == sort_ids(fd2) and sorted(i["line"] for i in fd2["items"]) != sorted(i["line"] for i in fd["items"]),
          f"n={len(fd['items'])} verdicts_ok={verdicts_ok} ids_stable={sort_ids(fd) == sort_ids(fd2)}")

    # the REAL FC-06 line: the generic classifier calls it OWNER (so only the ask-form filter keeps it out)
    req = (REPO / ".planning/workstreams/flow-compression/REQUIREMENTS.md").read_text(encoding="utf-8").splitlines()
    fc06 = next((ln for ln in req if ln.startswith("- FC-06")), "")
    fx = fixture([fc06[2:]])
    fire = bool(fc06) and bc._autonomy_for(fc06).get("owner") == "OWNER" and not bc.ASK_MARKERS.search(fc06)
    unfiltered = bc.foreseeable_decisions(fx, WS, use_filters=False)
    check("V-S6-BATCH-NEGATIVE-FC06",
          fire and bc.foreseeable_decisions(fx, WS)["items"] == [] and any(i["text"].startswith("FC-06") for i in unfiltered["items"]),
          f"fc06_found={bool(fc06)} classifier_owner={bc._autonomy_for(fc06).get('owner')}")
    st = (REPO / ".planning/workstreams/flow-compression/STATE.md").read_text(encoding="utf-8").splitlines()
    sl = next((ln for ln in st if "needs Owner authorization (name it)" in ln), "")
    fxs = fixture([sl])
    check("V-S6-BATCH-NEGATIVE-STATE-LINE",
          bool(sl) and bool(bc.ASK_MARKERS.search(sl)) and bool(bc.GUARD_FILTER.search(sl))
          and bc._autonomy_for(sl).get("owner") == "AGENT" and bc.foreseeable_decisions(fxs, WS)["items"] == [],
          f"line_found={bool(sl)} marker={bool(bc.ASK_MARKERS.search(sl))} guard={bool(bc.GUARD_FILTER.search(sl))}")

    # answered: doc marker, live decision, directive, and a superseded decision that must NOT omit
    base = fixture([ASK["push"]])
    iid = bc.foreseeable_decisions(base, WS)["items"][0]["id"]
    doc = bc.foreseeable_decisions(fixture([ASK["push"] + " (DECIDED: no push)"]), WS)
    fresh_missions()
    m1 = uid("a")
    gm.create(base, "/gsd-autonomous", mission_id=m1, now=NOW, workstream=WS)
    live = bc.foreseeable_decisions(base, WS, records=gm._goal_records(base, WS))
    gm.deliver_decision(m1, "no push", decision_id=iid, wake=False, now=NOW)
    live2 = bc.foreseeable_decisions(base, WS, records=gm._goal_records(base, WS))
    gm.deliver_decision(m1, "pushing is fine after all", decision_id="X2", supersedes=iid, wake=False, now=NOW)
    sup = bc.foreseeable_decisions(base, WS, records=gm._goal_records(base, WS))
    fresh_missions()
    m2 = uid("d")
    gm.create(base, "/gsd-autonomous", mission_id=m2, now=NOW, workstream=WS)
    gm.add_directive(m2, f"answers:{iid} do not push")
    dirv = bc.foreseeable_decisions(base, WS, records=gm._goal_records(base, WS))
    check("V-S6-BATCH-ANSWERED",
          len(doc["items"]) == 0 and doc["omitted"] and "marker" in doc["omitted"][0]["reason"]
          and len(live["items"]) == 1 and len(live2["items"]) == 0 and "live decision" in live2["omitted"][0]["reason"]
          and len(sup["items"]) == 1 and sup["omitted"] == []
          and len(dirv["items"]) == 0 and "directive" in dirv["omitted"][0]["reason"],
          f"doc={len(doc['items'])} before={len(live['items'])} live={len(live2['items'])} superseded={len(sup['items'])} dir={len(dirv['items'])}")

    # one record, one queue entry; idempotent; delta only
    q = qdir()
    cwd = fixture(ASK.values())
    arm_once(cwd)
    rows1, pend1 = batched_rows(cwd), oq.pending(q)
    qfile = Path(q) / "OWNER_QUEUE.jsonl"
    check("V-S6-BATCH-ONE-RECORD-ONE-QUEUE",
          len(rows1) == 1 and len(rows1[0]["ids"]) == 4 and len(pend1) == 1 and pend1[0]["id"] == f"q-decisions-{rows1[0]['batch_key']}"
          and pend1[0]["source"] == "arm_decisions" and qfile.is_file() and str(qfile).startswith(TMP)
          and "decisions --batch" in pend1[0]["command"],
          f"rows={len(rows1)} queue={len(pend1)}")
    arm_once(cwd)
    rows2, pend2 = batched_rows(cwd), oq.pending(q)
    new_line = "Owner-only: publish the release notes to the public site"
    spec = Path(cwd) / "vault" / "specs" / f"{WS}.md"
    spec.write_text(spec.read_text(encoding="utf-8") + f"- {new_line}\n", encoding="utf-8")
    arm_once(cwd)
    rows3, pend3 = batched_rows(cwd), oq.pending(q)
    new_id = [i["id"] for i in bc.foreseeable_decisions(cwd, WS)["items"] if i["text"] == new_line]
    check("V-S6-BATCH-IDEMPOTENT",
          len(rows2) == 1 and len(pend2) == 1 and len(rows3) == 2 and len(pend3) == 2 and rows3[1]["ids"] == new_id
          and len(new_id) == 1, f"second={len(rows2)}/{len(pend2)} third={len(rows3)}/{len(pend3)} delta={rows3[-1]['ids'] if rows3 else None}")

    # policy
    cfg = {"workflow": {"use_worktrees": False}}
    pol = bc.foreseeable_decisions(fixture([PREF], config=cfg), WS)
    r0 = (pol["resolved_by_policy"] or [{}])[0]
    rule = r0.get("rule") or {}
    check("V-S6-BATCH-POLICY-RULE-RECORDED",
          pol["items"] == [] and r0.get("resolution") == "RESOLVE_BY_POLICY" and rule.get("key") == "use_worktrees"
          and str(rule.get("source", "")).endswith("config.json") and len(str(rule.get("fingerprint"))) == 16,
          f"rule={rule}")
    nopol = bc.foreseeable_decisions(fixture([PREF]), WS)
    check("V-S6-BATCH-POLICY-REFUSED-WITHOUT-RULE",
          len(nopol["items"]) == 1 and nopol["items"][0]["resolution"] == "OWNER" and nopol["resolved_by_policy"] == [],
          f"items={len(nopol['items'])} resolved={len(nopol['resolved_by_policy'])}")
    wpush = "OWNER DECISION NEEDED: push the branch to origin from a worktree"
    outward = bc.foreseeable_decisions(fixture([wpush], config=cfg), WS)
    import mission_policy as mp
    control = mp.gate_question(wpush, {"use_worktrees": False}).get("result")
    check("V-S6-BATCH-POLICY-NEVER-OUTWARD",
          len(outward["items"]) == 1 and outward["resolved_by_policy"] == [] and outward["items"][0]["kind"] == "git-push",
          f"kind={(outward['items'] or [{}])[0].get('kind')} gate_question={control}")

    # preflight is read-only and never refuses; kill switch removes the check and the write
    cwd = fixture(ASK.values())
    q = qdir()
    before = len(lr.ledger_events())
    pre = gm.arm_preflight(cwd, "/gsd-autonomous", workstream=WS, launch=False,
                           status_reader=lambda c, w: {"outcome": "OK", "reason": "ok"})
    chk = next((c for c in pre["checks"] if c["check"] == "foreseeable_decisions"), {})
    check("V-S6-BATCH-PREFLIGHT-READONLY",
          pre["ok"] is True and chk.get("status") == "warn" and len(lr.ledger_events()) == before
          and oq.pending(q) == [] and not (Path(q) / "OWNER_QUEUE.jsonl").exists(), f"check={chk}")
    os.environ["CPP_BLOCKER_COMPILE"] = "off"
    try:
        q = qdir()
        pre_off = gm.arm_preflight(cwd, "/gsd-autonomous", workstream=WS, launch=False,
                                   status_reader=lambda c, w: {"outcome": "OK", "reason": "ok"})
        cwd_k = fixture(ASK.values())
        arm_once(cwd_k)
        off_ok = (not any(c["check"] == "foreseeable_decisions" for c in pre_off["checks"])
                  and batched_rows(cwd_k) == [] and oq.pending(q) == [])
    finally:
        os.environ.pop("CPP_BLOCKER_COMPILE", None)
    check("V-S6-BATCH-KILL-SWITCH", off_ok, f"off_ok={off_ok}")

    # a raising compiler leaves the arm intact
    real = bc.foreseeable_decisions

    def boom(*a, **k):
        raise RuntimeError("decisions exploded")
    bc.foreseeable_decisions = boom
    try:
        q = qdir()
        cwd_f = fixture(ASK.values())
        rec_f = arm_once(cwd_f)
        pre_f = gm.arm_preflight(cwd_f, "/gsd-autonomous", workstream=WS, launch=False,
                                 status_reader=lambda c, w: {"outcome": "OK", "reason": "ok"})
    finally:
        bc.foreseeable_decisions = real
    failed = [r for r in lr.ledger_events("arm-preflight") if r.get("event") == "owner_decisions_batch_failed"
              and r.get("cwd") == cwd_f]
    chk_f = next((c for c in pre_f["checks"] if c["check"] == "foreseeable_decisions"), {})
    check("V-S6-BATCH-FAIL-OPEN",
          rec_f["state"] == gm.PREPARED and len(failed) == 1 and "RuntimeError" in failed[0]["why"]
          and batched_rows(cwd_f) == [] and oq.pending(q) == [] and pre_f["ok"] is True
          and chk_f.get("status") == "unmeasured", f"state={rec_f['state']} failed={len(failed)} chk={chk_f}")

    # an unreadable source is unmeasured, never zero decisions
    cwd_u = fixture(ASK.values(), roadmap=False)
    fu = bc.foreseeable_decisions(cwd_u, WS)
    pre_u = gm.arm_preflight(cwd_u, "/gsd-autonomous", workstream=WS, launch=False,
                             status_reader=lambda c, w: {"outcome": "OK", "reason": "ok"})
    chk_u = next((c for c in pre_u["checks"] if c["check"] == "foreseeable_decisions"), {})
    check("V-S6-BATCH-UNMEASURED-SOURCE",
          fu["measured"] is False and any(x["status"] == "unmeasured" and x["path"].endswith("ROADMAP.md") for x in fu["sources"])
          and chk_u.get("status") == "unmeasured", f"measured={fu['measured']} chk={chk_u}")


def gates() -> None:
    tracer_gates()
    batch_gates()


def run_once() -> tuple[int, int]:
    RESULTS.clear()
    gates()
    p = sum(1 for _, ok, _ in RESULTS if ok)
    return p, len(RESULTS) - p


def main() -> int:
    t0 = time.time()
    passes, fails = run_once()
    for name, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'} {name} {'' if ok else detail}")
    total = passes + fails
    print(f"S6_PASS={passes}/{total}  ({time.time() - t0:.0f} s)")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
