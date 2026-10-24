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
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cc")
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
          c["populations"].get("mission_blocked") == 6 and c["populations"].get("owner_hold_set") == 1
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


# ------------------------------------------------------------------------------------------------ Task 3: full set
import ast  # noqa: E402
import contextlib  # noqa: E402
import inspect  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import textwrap  # noqa: E402

THIS = sys.modules[__name__]
PHASE_DIR = REPO / ".planning/workstreams/flow-compression/phases/06-s6-blocker-compiler-owner-boundary"
CENSUS_PATH = PHASE_DIR / "06-CENSUS.md"
REAL_CWD = str(REPO)
REAL_WS = "flow-compression"

# Reason strings below are copied from the host ledger census (06-CENSUS.md) or, for the zero-row classes, built from
# the named hold kinds the writers produce. Every pair was run through the REAL compiler before it was kept: the
# positive must compile to its class and the negative must compile to the NAMED neighbour, so a negative that lands
# anywhere else is a changed control, not a pass.
H = "host lists session blocked (no waitingFor); host needs: "
CMD = H + "run /clear"
DEC = H + 'Reply "approve all 8", name the subset, or say "keep all"'
HOSTGATE = "host: waiting for permission prompt"
PUSH = (H + "From the laptop: push feat/wsctx-m2 to GitHub, open the PR using PR_BODY.md, wait for CI, then merge and "
        "deploy Phoenix and infinity_ui together.")
CAP = H + "approve ~3M more budget to finish (judge P39 frames)"
COSTR = ("cost breaker: 1,958,619 processed since the work tree last changed (stall budget 1,500,000); "
         "semantic progress is not kept")
COSTH = {"kind": "cost", "reason": COSTR}
GSDR = ("gsd NO_PHASES on 2 consecutive passes (300 s): GSD parses 0 phases from ROADMAP.md -- "
        "no relay until GSD answers OK")
SEAL = "capsule-v2 seal impossible for mission-m-c474d0bfc3e6-e3: recovery REFUSED: obligations: no open item found"
CERT = "resume_not_certified: successor not certified"
PARK = "E1 ALL_DECIDED at 9787a946 work complete, no rerun"
UNK = H + "open this session to continue setup"

CONTROLS = {
    "HOST_GATE": ({"reason": HOSTGATE}, {"reason": CMD}, "COMMAND_REQUEST"),
    "COMMAND_REQUEST": ({"reason": CMD}, {"reason": HOSTGATE}, "HOST_GATE"),
    "DECISION_REQUEST": ({"reason": DEC}, {"reason": CMD}, "COMMAND_REQUEST"),
    "RESOURCE_REQUEST": ({"reason": H + "Supply target images (kitten reshape, Jacobo hair) or a new offline source"},
                         {"reason": DEC}, "DECISION_REQUEST"),
    "PUBLISH_BOUNDARY": ({"reason": PUSH}, {"reason": CMD}, "COMMAND_REQUEST"),
    "CAPITAL_EXHAUSTED": ({"reason": CAP}, {"reason": COSTR, "hold": COSTH, "is_hold": True}, "COST_HOLD_RECOVERING"),
    "COST_HOLD_RECOVERING": ({"reason": COSTR, "hold": COSTH, "is_hold": True}, {"reason": CAP}, "CAPITAL_EXHAUSTED"),
    "PROVIDER_LIMIT": ({"reason": "GEX44 account weekly limit until 2026-10-21 19:00 Europe/Berlin (worker a3937ee7 "
                                  "got the limit message on turn 1)"}, {"reason": HOSTGATE}, "HOST_GATE"),
    "WAIT_RESOURCE": ({"reason": "disk pressure hold", "hold": {"kind": "resource", "reason": "disk pressure hold"},
                       "is_hold": True},
                      {"reason": "disk pressure hold", "hold": {"kind": "owner_stop", "reason": "disk pressure hold"},
                       "is_hold": True}, "OWNER_PARK"),
    "GSD_HOLD": ({"reason": GSDR, "hold": {"outcome": "NO_PHASES", "reason": "x", "unblock": "GSD parses the roadmap"}},
                 {"reason": "totally unrecognised reason text"}, "UNKNOWN"),
    "CAPSULE_NOT_CERTIFIED": ({"reason": CERT, "hold": {"kind": "resume_not_certified"}},
                              {"reason": SEAL, "hold": {"kind": "seal_refused"}}, "CAPSULE_SEAL_REFUSED"),
    "CAPSULE_SEAL_REFUSED": ({"reason": SEAL, "hold": {"kind": "seal_refused"}},
                             {"reason": CERT, "hold": {"kind": "resume_not_certified"}}, "CAPSULE_NOT_CERTIFIED"),
    "SETUP_HOLD": ({"reason": "canary: envelope before first launch", "is_hold": True}, {"reason": HOSTGATE},
                   "HOST_GATE"),
    "OWNER_PARK": ({"reason": PARK, "is_hold": True}, {"reason": PARK}, "UNKNOWN"),
    "UNKNOWN": ({"reason": UNK}, {"reason": CMD}, "COMMAND_REQUEST"),
}


def cb(**kw):
    kw.setdefault("evidence", {"measured": False})
    return bc.compile_blocker(**kw)


def class_gates() -> None:
    missing = [k for k in bc.CLASSES if k not in CONTROLS]
    extra = [k for k in CONTROLS if k not in bc.CLASSES]
    pos_bad, neg_bad = [], []
    for k in bc.CLASSES:
        if k not in CONTROLS:
            continue
        p, n, nb = CONTROLS[k]
        got = cb(**p)
        if got["class"] != k or not (got.get("unblock_condition") or {}).get("kind"):
            pos_bad.append(f"{k}->{got['class']}")
        neg = cb(**n)["class"]
        if neg == k or neg != nb:
            neg_bad.append(f"{k}->{neg}")
    check("V-S6-CLASS-POSITIVE", not missing and not extra and not pos_bad,
          f"missing={missing} extra={extra} bad={pos_bad}")
    check("V-S6-CLASS-NEGATIVE", not missing and not extra and not neg_bad, f"missing={missing} bad={neg_bad}")


# ------------------------------------------------------------------------------------------------ independent_work
def rm_fx(boxes: dict, deps: dict | None = None, current=2, state: bool = True, roadmap: bool = True,
          ws: str = "rw") -> tuple[str, str]:
    _n[0] += 1
    cwd = ROOT / f"rm-{_n[0]}"
    base = cwd / ".planning" / "workstreams" / ws
    base.mkdir(parents=True)
    if roadmap:
        lines = ["# roadmap", ""]
        for n, done in boxes.items():
            lines.append(f"- [{'x' if done else ' '}] **Phase {n}: unit {n}**")
        lines.append("")
        for n in boxes:
            d = (deps or {}).get(n)
            lines += [f"### Phase {n}: unit {n}", "**Depends on**: " + (", ".join(f"Phase {x}" for x in d) if d else "Nothing"), ""]
        (base / "ROADMAP.md").write_text("\n".join(lines), encoding="utf-8")
    if state:
        body = f"current_phase: {current}\n" if current is not None else "status: ok\n"
        (base / "STATE.md").write_text(f"---\n{body}---\n", encoding="utf-8")
    return str(cwd), ws


def indep(cwd, ws, reason=HOSTGATE, **kw):
    return cb(reason=reason, cwd=cwd, workstream=ws, evidence=None, **kw)


def indep_gates() -> None:
    cwd, ws = rm_fx({1: True, 2: False, 3: False, 4: False}, {3: [1], 4: [2]})
    pos = indep(cwd, ws)
    check("V-S6-INDEPENDENT-POSITIVE",
          pos["class"] == "HOST_GATE" and pos["independent_work"] is True and "unit(s) 3 " in pos["independent_reason"] + " "
          and "4" not in pos["independent_reason"].split("unit(s)")[1].split("runnable")[0],
          f"{pos['independent_work']} {pos['independent_reason']}")
    unk = indep(cwd, ws, reason=UNK)
    check("V-S6-UNKNOWN-NEVER-INDEPENDENT",
          unk["class"] == "UNKNOWN" and unk["independent_work"] is False and unk["independent_reason"] == "unclassified"
          and pos["independent_work"] is True, f"{unk['class']} {unk['independent_work']} {unk['independent_reason']}")
    cwd2, ws2 = rm_fx({1: True, 2: False, 3: False, 4: False}, {3: [2], 4: [3]})
    lin = indep(cwd2, ws2)
    ev2 = bc.plan_evidence(cwd2, ws2)
    check("V-S6-INDEPENDENT-NO-OTHER-UNIT",
          ev2["measured"] is True and lin["independent_work"] is False and lin["independent_reason"] == "no_other_unit",
          f"{lin['independent_work']} {lin['independent_reason']}")
    cases = {"no ROADMAP": rm_fx({1: True, 2: False}, roadmap=False),
             "no STATE": rm_fx({1: True, 2: False, 3: False}, {3: [1]}, state=False),
             "no current_phase": rm_fx({1: True, 2: False, 3: False}, {3: [1]}, current=None),
             "no parsed units": rm_fx({})}
    bad = []
    for label, (c_, w_) in cases.items():
        r = indep(c_, w_)
        if r["independent_work"] is not False or r["independent_reason"] != "unmeasured":
            bad.append(f"{label}: {r['independent_work']}/{r['independent_reason']}")
    nocwd = cb(reason=HOSTGATE, evidence=None)
    if nocwd["independent_work"] is not False or nocwd["independent_reason"] != "unmeasured":
        bad.append(f"no cwd: {nocwd['independent_work']}/{nocwd['independent_reason']}")
    check("V-S6-INDEPENDENT-UNMEASURED", not bad, "; ".join(bad))
    cs, ws_s = rm_fx({1: False, 2: False}, {})
    stale = indep(cs, ws_s)
    cs2, ws_s2 = rm_fx({1: False, 2: False, 3: False}, {3: []})
    ahead = indep(cs2, ws_s2)
    check("V-S6-INDEPENDENT-STALE-BOX",
          stale["independent_work"] is False and stale["independent_reason"] == "no_other_unit"
          and ahead["independent_work"] is True and "unit(s) 3 " in ahead["independent_reason"] + " "
          and "unit(s) 1" not in ahead["independent_reason"],
          f"stale={stale['independent_reason']} ahead={ahead['independent_reason']}")
    rec_cost = {"mission_id": "m-x", "owner_hold": COSTH}
    held = indep(cwd, ws, rec=rec_cost)
    held_arg = indep(cwd, ws, hold=COSTH)
    check("V-S6-INDEPENDENT-AUTHORITY-HOLD",
          held["independent_work"] is False and held["independent_reason"] == "authority_exhausted"
          and held_arg["independent_work"] is False and pos["independent_work"] is True,
          f"{held['independent_reason']} {held_arg['independent_reason']}")
    real_ev = bc.plan_evidence(REAL_CWD, REAL_WS)
    roadmap_txt = (Path(REAL_CWD) / ".planning/workstreams" / REAL_WS / "ROADMAP.md").read_text(encoding="utf-8")
    n_real = len(re.findall(r"^- \[[ xX]\] \*\*Phase \d", roadmap_txt, re.M))
    real = indep(REAL_CWD, REAL_WS)
    check("V-S6-INDEPENDENT-REAL-ROADMAP",
          Path(REAL_CWD).resolve() == REPO.resolve() and real_ev["measured"] is True and len(real_ev["units"]) == n_real
          and n_real >= 6 and real["independent_work"] is False and real["independent_reason"] == "no_other_unit",
          f"cwd={REAL_CWD} units={len(real_ev.get('units', []))}/{n_real} cur={real_ev.get('current')} "
          f"{real['independent_work']}/{real['independent_reason']}")
    a = [json.dumps(cb(**CONTROLS[k][0]), sort_keys=True) for k in bc.CLASSES if k in CONTROLS]
    b = [json.dumps(cb(**CONTROLS[k][0]), sort_keys=True) for k in bc.CLASSES if k in CONTROLS]
    c = json.dumps(indep(cwd, ws), sort_keys=True), json.dumps(indep(cwd, ws), sort_keys=True)
    check("V-S6-DETERMINISTIC", a == b and len(a) == len(bc.CLASSES) and c[0] == c[1], f"controls={len(a)} equal={a == b}")

    # the autonomy gate decides who must act; the compiler only agrees with it (FC-06)
    from modules.autonomy_gate import gate as ag
    force = "git push --force origin main"
    plain = "git push origin feat/x"
    deploy = "deploy the build to production"
    inspect_only = "read the log file and summarize the failing test"
    rubric = (ag.classify(force)["owner"] == "OWNER" and ag.classify(plain)["owner"] == "OWNER"
              and ag.classify(plain, authorized=("git-push",))["owner"] == "AGENT"
              and ag.classify(deploy)["owner"] == "OWNER" and ag.classify(inspect_only)["owner"] == "AGENT")
    seen = {}
    for label, text in (("force", force), ("plain", plain), ("deploy", deploy)):
        r = cb(reason=H + text)
        seen[label] = (r["class"], r["owner_required"])
    agrees = all(v == ("PUBLISH_BOUNDARY", True) for v in seen.values())
    ctrl = cb(reason=H + inspect_only)
    check("V-S6-AUTONOMY-AGREEMENT", rubric and agrees and ctrl["class"] != "PUBLISH_BOUNDARY",
          f"rubric={rubric} seen={seen} control={ctrl['class']}")


# ------------------------------------------------------------------------------------------------ structure (AST)
SRC_HOOK: list = [None]
WRITER_CALLEES = {"transition", "ledger_append"}
LAUNCH_NAMES = {"launch_worker", "transition", "create", "arm", "arm_chain", "wake", "wake_mission", "system",
                "Popen", "run", "check_call", "check_output", "call", "spawn"}
ALLOWED_S6_EVENTS = {"mission_blocked", "owner_decisions_batched", "owner_decisions_batch_failed"}
STATES_LITERAL = {"PREPARED", "LAUNCHING", "RUNNING", "HANDOFF_REQUESTED", "BLOCKED", "COMPLETED", "HALTED", "ORPHANED"}
ACTIONS_LITERAL = {"adopt", "await", "halt", "launch", "none", "recover", "relay", "replace", "settle", "slim_finished",
                   "surface_blocked", "surface_unknown", "unblock"}


def tool_sources() -> dict:
    if SRC_HOOK[0]:
        return SRC_HOOK[0]()
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(TOOLS.glob("*.py")) if not p.name.startswith("test_")}


def _nm(n):
    return n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else None


class _Walk(ast.NodeVisitor):
    def __init__(self, out):
        self.out, self.stack = out, []

    def visit_FunctionDef(self, n):
        self.stack.append(n.name)
        self.generic_visit(n)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, c):
        fn = self.stack[-1] if self.stack else "<module>"
        callee = _nm(c.func)
        consts = [a.value for a in c.args if isinstance(a, ast.Constant)] + \
                 [k.value.value for k in c.keywords if isinstance(k.value, ast.Constant)]
        if callee in WRITER_CALLEES:
            if "mission_blocked" in consts or any(k.arg == "state" and _nm(k.value) == "BLOCKED" for k in c.keywords):
                self.out["blocked"].add(fn)
            for ev in ("owner_hold_set", "recovery_boundary"):
                if ev in consts:
                    self.out["hold_writers"].add(fn)
        if callee == "annotate_hold":
            self.out["annotating"].add(fn)
        if callee == "block_mission":
            self.out["block_calls"] += 1
        self.generic_visit(c)


def discover(sources: dict) -> dict:
    out = {"blocked": set(), "hold_writers": set(), "annotating": set(), "block_calls": 0, "parse_errors": []}
    for fname, src in sources.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            out["parse_errors"].append(fname)
            continue
        _Walk(out).visit(tree)
    return out


def launch_violations(src: str) -> list:
    v = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in ("subprocess", "gsd_mission") for a in n.names):
            v.append("import " + ",".join(a.name for a in n.names))
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in ("subprocess", "gsd_mission"):
            v.append("from " + str(n.module))
        if isinstance(n, ast.Call) and _nm(n.func) in LAUNCH_NAMES:
            v.append("call " + str(_nm(n.func)))
    return v


def _fn(src: str, name: str):
    return next((n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == name), None)


def _calls(fn, names) -> list:
    return [c for c in ast.walk(fn) if isinstance(c, ast.Call) and _nm(c.func) in names]


def struct_gates() -> None:
    srcs = tool_sources()
    d = discover(srcs)
    planted = discover({"p.py": "def sneaky(m):\n    transition(m, expect_epoch=0, expect_state=1, event='mission_blocked', "
                                "state=BLOCKED)\n"})
    docstr = discover({"p.py": 'def quiet():\n    """mission_blocked is written by transition(state=BLOCKED)."""\n    return 1\n'})
    unann = discover({"p.py": "def h(m):\n    transition(m, event='owner_hold_set')\n"})
    ann = discover({"p.py": "def h(m):\n    annotate_hold(m, {})\n    transition(m, event='owner_hold_set')\n"})
    controls = (planted["blocked"] == {"sneaky"} and docstr["blocked"] == set() and unann["hold_writers"] == {"h"}
                and "h" not in unann["annotating"] and "h" in ann["annotating"])
    unannotated = sorted(d["hold_writers"] - d["annotating"])
    check("V-S6-WRITER-DISCOVERY",
          controls and d["blocked"] == {"block_mission"} and not unannotated
          and {"set_owner_hold", "_amr_boundary"} <= d["hold_writers"] and d["block_calls"] >= 5
          and not d["parse_errors"] and len(srcs) >= 20,
          f"blocked={sorted(d['blocked'])} unannotated={unannotated} hold_writers={sorted(d['hold_writers'])} "
          f"block_calls={d['block_calls']} controls={controls}")

    comp = srcs.get("blocker_compiler.py", "")
    gm_src = srcs.get("gsd_mission.py", "")
    planted_launch = launch_violations("def x():\n    launch_worker()\n")
    clean_ctrl = launch_violations("def y():\n    return 1\n")
    viol = launch_violations(comp)
    read_only = ["annotate_hold", "_compile_blocker", "_blocker_ledger", "current_blocker", "batch_foreseeable_decisions"]
    gm_viol = []
    for name in read_only:
        f = _fn(gm_src, name)
        if f is None:
            gm_viol.append(f"{name} missing")
            continue
        gm_viol += [f"{name}: {_nm(c.func)}" for c in _calls(f, LAUNCH_NAMES)]
    bm = _fn(gm_src, "block_mission")
    bm_calls = [_nm(c.func) for c in _calls(bm, LAUNCH_NAMES)] if bm else ["missing"]
    check("V-S6-NO-NEW-LAUNCH-PATH",
          planted_launch and not clean_ctrl and bool(comp) and not viol and not gm_viol and bm_calls == ["transition"],
          f"compiler={viol} gm={gm_viol} block_mission={bm_calls} control={planted_launch}")

    events = set()
    for name in ("block_mission", "annotate_hold", "batch_foreseeable_decisions", "_compile_blocker", "_blocker_ledger"):
        f = _fn(gm_src, name)
        for c in (_calls(f, WRITER_CALLEES) if f else []):
            for k in c.keywords:
                if k.arg == "event" and isinstance(k.value, ast.Constant):
                    events.add(k.value.value)
            if _nm(c.func) == "ledger_append" and len(c.args) > 1 and isinstance(c.args[1], ast.Constant):
                events.add(c.args[1].value)
    pn = _fn(gm_src, "plan_next")
    actions = set()
    for n in ast.walk(pn) if pn else []:
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "action" and isinstance(v, ast.Constant):
                    actions.add(v.value)
    check("V-S6-FC10-NO-NEW-STATE",
          set(gm.STATES) == STATES_LITERAL and actions == ACTIONS_LITERAL and bool(events) and events <= ALLOWED_S6_EVENTS,
          f"states={sorted(set(gm.STATES) ^ STATES_LITERAL)} actions={sorted(actions ^ ACTIONS_LITERAL)} "
          f"events={sorted(events - ALLOWED_S6_EVENTS)}")


# ------------------------------------------------------------------------------------------------ consumers, holds
def consumers_gates() -> None:
    mid, rec = supervised_block("Choose 1 or run /compact")
    plan = lambda r: gm.plan_next(r, NOW + 5, [], pid_alive=lambda p: True)  # noqa: E731
    bare = {k: v for k, v in rec.items() if k != "blocker"}
    flipped = {**rec, "blocker": {**rec["blocker"], "independent_work": True, "owner_required": False, "zzz": 1}}
    a, b, c = plan(rec), plan(bare), plan(flipped)
    hid = held_mission("c")
    gm.set_owner_hold(hid, "Owner reviewing the plan", now=NOW)
    hrec = gm.load(hid)
    nohb = {**hrec, "owner_hold": {k: v for k, v in hrec["owner_hold"].items() if k != "blocker"}}
    ha, hb = plan(hrec), plan(nohb)
    check("V-S6-CONSUMERS-TOLERATE",
          a == b == c and ha == hb and "blocker" in rec and "blocker" in hrec["owner_hold"]
          and gm.current_blocker(bare) is None and gm.current_blocker(nohb) is None
          and gm.current_blocker(rec) is not None and gm.current_blocker(hrec) is not None,
          f"blocked_same={a == b == c} hold_same={ha == hb} plan={a.get('action')}/{ha.get('action')}")


BREAKER = "cost breaker: processed 156,097,796 >= authority 155,000,000 minus 1,000,000 closeout reserve"


def hold_gates() -> None:
    hid = held_mission("p")
    gm.set_owner_hold(hid, "Owner reviewing the plan", now=NOW)
    hold = gm.load(hid)["owner_hold"]
    hb = hold.get("blocker") or {}
    hrow = ledger_rows(hid, "owner_hold_set")
    wd = ROOT / f"amr-{uid('w')}"
    wd.mkdir()
    subprocess.run([gm.resolve_exe("git"), "-C", str(wd), "init", "-q"], check=True)
    mid = uid("q")
    gm.create(str(wd), "/gsd-autonomous --ws obd", mission_id=mid, workstream="obd", now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING, epoch=2,
                  max_hours=100.0)
    gm.set_owner_hold(mid, BREAKER, now=NOW, kind="cost")
    rec = gm.load(mid)
    gm._amr_boundary(rec, {"boundary": "no materially different strategy known for UNCLASSIFIED", "unit": None,
                           "failure": None}, NOW + 5, rec.get("owner_hold"))
    after = gm.load(mid)
    ab = (after.get("owner_hold") or {}).get("blocker") or {}
    wait = (after.get("owner_hold") or {}).get("wait") or {}
    arow = ledger_rows(mid, "recovery_boundary")
    cond = ab.get("unblock_condition") or {}
    check("V-S6-HOLD-PARKS-TYPED",
          hb.get("class") == "OWNER_PARK" and hb.get("owner_required") is True and bool(hb.get("unblock_condition"))
          and len(hrow) == 1 and hrow[0].get("blocker_class") == "OWNER_PARK"
          and ab.get("class") == "CAPITAL_EXHAUSTED" and cond.get("kind") == "owner_act" and bool(wait.get("resume"))
          and cond.get("command") == wait.get("resume") and (arow and arow[-1].get("blocker_class") == "CAPITAL_EXHAUSTED"),
          f"park={hb.get('class')} amr={ab.get('class')} cmd_ok={cond.get('command') == wait.get('resume')} "
          f"rows={len(hrow)}/{len(arow)}")


def isolation_gates() -> None:
    lp = Path(lr.ledger_path()).resolve()
    qd = Path(os.environ.get("PP_OWNER_QUEUE_STATE_DIR", "")).resolve()
    home_state = (Path.home() / ".claude" / "state").resolve()
    inside = lambda p: str(p).startswith(str(ROOT))  # noqa: E731
    check("V-S6-ISOLATION",
          inside(lp) and inside(qd) and not str(lp).startswith(str(home_state)) and not str(qd).startswith(str(home_state))
          and os.environ.get("CPP_CLAUDE_EXE") == "__no_such_claude_in_tests__",
          f"ledger={lp} queue={qd}")


def census_gates() -> None:
    try:
        text = CENSUS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        check("V-S6-CENSUS-ARTIFACT", False, f"unreadable {type(exc).__name__}")
        return
    led = re.search(r"^Ledger: `(.+)`", text, re.M)
    rows = re.search(r"^Rows read: (\d+)", text, re.M)
    pops = {e: int(n) for e, n in re.findall(r"^\| (mission_blocked|blocked_intent|owner_hold_set|recovery_owner_boundary) \| (\d+) \|",
                                              text, re.M)}
    table = {k: int(n) for k, n in re.findall(r"^\| ([A-Z_]+) \| (\d+) \|", text, re.M) if k in bc.CLASSES}
    total = re.search(r"Compiled rows: (\d+); UNKNOWN residual: (\d+)", text)
    resid = sum(int(n) for n in re.findall(r"^- x(\d+): ", text, re.M))
    ok = (bool(led) and bool(rows) and int(rows.group(1)) > 0 and set(pops) == set(bc.CENSUS_EVENTS) and sum(pops.values()) > 0
          and set(table) == set(bc.CLASSES) and bool(total) and sum(table.values()) == int(total.group(1))
          and table.get("UNKNOWN") == int(total.group(2)) == resid)
    check("V-S6-CENSUS-ARTIFACT", ok,
          f"ledger={bool(led)} rows={rows.group(1) if rows else None} pops={pops} classes={len(table)} "
          f"sum={sum(table.values())} stated={total.groups() if total else None} resid={resid}")


GROUPS = {"tracer": tracer_gates, "batch": batch_gates, "class": class_gates, "indep": indep_gates,
          "struct": struct_gates, "consumers": consumers_gates, "hold": hold_gates, "isolation": isolation_gates,
          "census": census_gates}


def gates() -> None:
    for fn in GROUPS.values():
        fn()


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
