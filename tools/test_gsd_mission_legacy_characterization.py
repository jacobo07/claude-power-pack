#!/usr/bin/env python
"""V-G23-* gates: characterization of the LEGACY mission path of tools/gsd_mission.py.

Spec vault/specs/mission-capsule-rollover.md section 8, G23: before T6 wires capsule-v2 into
gsd_mission, the behaviour of a record WITHOUT `rollover_protocol` is captured on the
pre-change code -- worker argv, card bytes, ledger event order per supervise branch, and the
record's key set -- so every later edit must leave the legacy path byte-identical. Live
missions (P3) have no protocol field; every gsd_mission edit reaches them on the next sweep.

The golden lives in tools/fixtures/gsd_mission_legacy_golden.json. It was captured once with
`--capture` (refused when the golden already exists); its `meta` names the source sha and HEAD
it was taken on. A legitimate legacy change is a re-capture with `--capture --force`, made on
purpose and reviewed as a diff of the golden, never a side effect of a green run.

Hermetic: state is redirected to a temp dir BEFORE import; host sessions, pid probe, runners,
git/GSD/transcript facts and the provider breaker are injected. Nothing here reads or writes
the live estate, and no fake pid can reach a real process (pid_alive answers "gone").

Mutants (always run): four in-process mutants route a legacy record toward v2 behaviour. Each
must turn the comparison red, and the clean run after them must be green again, so a
comparator that sees nothing -- or a mutant that leaks -- cannot pass.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-mission-g23-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
for _k in ("CPP_CLAUDE_EXE", "CPP_MISSION_CONTINUATION", "CPP_SOURCE_PACKET_CARD"):
    os.environ.pop(_k, None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_epoch as ge  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402

GOLDEN = HERE / "fixtures" / "gsd_mission_legacy_golden.json"
NOW = 1_800_000_000.0
TMP_FORMS = sorted({TMP, str(Path(TMP).resolve())}, key=len, reverse=True)

passes = fails = 0


def _ok(gate, ev=""):
    global passes
    passes += 1
    print(f"PASS {gate} {ev}")


def _fail(gate, ev=""):
    global fails
    fails += 1
    print(f"FAIL {gate} {ev}")


def check(gate, cond, ev=""):
    (_ok if cond else _fail)(gate, ev)


# ------------------------------------------------------------------------------- the world
class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


class World:
    """Every non-deterministic input of the legacy path, as a knob."""

    def __init__(self):
        self.tokens = 1000            # context size the transcript would report
        self.children = "NONE"        # gsd_epoch.child_work verdict
        self.stop_reason = "end_turn"
        self.hold = None              # provider_breaker answer
        self.fp = None                # progress fingerprint
        self.launches: list[list[str]] = []
        self.stops: list[list[str]] = []

    def launch_run(self, argv, cwd):
        self.launches.append(list(argv))
        if "--resume" in argv:
            sid = argv[argv.index("--resume") + 1]
            return R(f"resumed · {sid[:8]}")
        return R(f"backgrounded · 9e9e9e9e · {argv[argv.index('-n') + 1]}")

    def stop_run(self, argv):
        self.stops.append(list(argv))
        return R("stopped")


W = World()
_ORIG_DECIDE = ge.decide_turn_end
_ORIG_TURN_DONE = ge.turn_ended_as_done


def _children(sid, now):
    if W.children == "HOLD":
        return {"verdict": "HOLD", "pending": [{"tool_use_id": "toolu_x"}], "unconsumed": []}
    return {"verdict": W.children}


def install_world():
    gm._git_facts = lambda wd: {"head": "abc1234", "dirty": 0, "recent": ["abc1234 seed commit"]}
    gm._plan_facts = lambda wd, ws=None: "Phase 1 of 2: pending"
    gm._autonomy_rubric = lambda: ("RUBRIC (fixed for characterization)", "")
    gm.effective_workdir = lambda *a, **k: None
    gm.handoff_note_from_transcript = lambda sid: "note from the transcript"
    gm.provider_hold = lambda rec, now: W.hold
    gm.progress_fingerprint = lambda wd: W.fp
    ge.decide_turn_end = lambda rec, now=None, *, events=None, **_: _ORIG_DECIDE(
        rec, now, events=events, tokens=lambda sid: W.tokens, children=_children,
        last_turn_at=lambda sid: None)
    ge.turn_ended_as_done = lambda rec, sessions, **_: _ORIG_TURN_DONE(
        rec, sessions, stop_reason=lambda sid: W.stop_reason)


def reset():
    global W
    W = World()
    for p in Path(TMP).iterdir():
        if p.is_file():
            p.unlink()


# ------------------------------------------------------------------------------- helpers
def seed_running(mid, *, iterations=1, **fields):
    """A RUNNING legacy mission at epoch 1 owned by a background worker, and its host row."""
    sid = f"{mid[2:10]}-owner-session"
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="seed", now=NOW,
                  state=gm.RUNNING, epoch=1, iterations=iterations,
                  owner={"session_id": sid, "pid": 5151, "kind": "background",
                         "heartbeat_at": NOW, "epoch": 1}, **fields)
    return [{"sessionId": sid, "status": "idle", "state": "working", "kind": "background",
             "id": sid[:8], "pid": 999}]


def sup(sessions, gsd="OK", now=NOW):
    return gm.supervise(now=now, sessions=sessions,
                        gsd_status=lambda c, workstream=None: {"outcome": gsd, "reason": gsd.lower()},
                        runner=W.launch_run, stop_runner=W.stop_run, pid_alive=lambda pid: False)


CARDS: dict[str, str] = {}


def _tmpless(s: str) -> str:
    for form in TMP_FORMS:
        s = s.replace(form, "<TMP>")
    return s


def norm(obj):
    """JSON-shaped, temp dir masked, every card replaced by a reference into CARDS."""
    if isinstance(obj, dict):
        return {str(k): norm(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [norm(v) for v in obj]
    if isinstance(obj, str):
        s = _tmpless(obj)
        if s.startswith("MISSION CONTINUITY"):
            raw = s.encode("utf-8")
            key = hashlib.sha256(raw).hexdigest()[:16]
            CARDS[key] = s
            return f"<CARD {key} {len(raw)}B>"
        return s
    if isinstance(obj, float) and obj.is_integer():
        return int(obj)
    return obj


def record_shape(mid):
    rec = gm.load(mid)
    if rec is None:
        return None
    return {"keys": sorted(rec), "state": rec["state"], "epoch": rec["epoch"],
            "pending_kind": (rec.get("pending") or {}).get("kind"),
            "has_rollover_protocol": "rollover_protocol" in rec}


def observe(mids, rows):
    renewed = [r["renewed_as"] for r in rows or [] if r.get("renewed_as")]
    out = {"rows": norm(rows or []),
           "events": {m: [e["event"] for e in lr.ledger_events(m)] for m in mids},
           "launch_argv": norm(W.launches), "stop_argv": norm(W.stops),
           "records": {m: record_shape(m) for m in mids}}
    for i, m in enumerate(renewed):
        out["events"][f"renewed[{i}]"] = [e["event"] for e in lr.ledger_events(m)]
        out["records"][f"renewed[{i}]"] = record_shape(m)
    for row in out["rows"]:
        if isinstance(row, dict) and row.get("renewed_as"):
            row["renewed_as"] = "<RENEWED-ID>"
    return out


# ------------------------------------------------------------------------------- scenarios
def s_launch_ack_heartbeat():
    gm.create(TMP, "/gsd-autonomous", mission_id="m-launch", now=NOW)
    rows = sup([])
    gm.ack_session("9e9e9e9e-worker-session", pid=4242, now=NOW + 10)
    gm.ack_session("9e9e9e9e-worker-session", pid=4242, now=NOW + 20)
    return observe(["m-launch"], rows)


def s_adopt():
    gm.create(TMP, "/gsd-autonomous", mission_id="m-adopt", now=NOW)
    sup([])
    rows = sup([{"sessionId": "9e9e9e9e-adopted", "state": "working", "status": "busy",
                 "kind": "background", "id": "9e9e9e9e"}], now=NOW + 30)
    return observe(["m-adopt"], rows)


def s_replace_overdue_launch():
    gm.create(TMP, "/gsd-autonomous", mission_id="m-overdue", now=NOW)
    sup([])
    rows = sup([], now=NOW + gm.START_DEADLINE_S + 1)
    return observe(["m-overdue"], rows)


def s_halt_unacknowledged():
    gm.create(TMP, "/gsd-autonomous", mission_id="m-unack", now=NOW)
    gm.transition("m-unack", expect_epoch=0, expect_state=gm.PREPARED, event="seed", now=NOW,
                  state=gm.LAUNCHING, epoch=1, failed_launches=gm.MAX_REPLACEMENTS - 1,
                  pending={"kind": "worker_start", "epoch": 1, "deadline": NOW - 1})
    return observe(["m-unack"], sup([]))


def s_relay_continue():
    W.tokens = 1000
    return observe(["m-cont"], sup(seed_running("m-cont")))


def s_relay_rotate_unmeasured():
    W.tokens = None
    return observe(["m-unmeas"], sup(seed_running("m-unmeas")))


def s_relay_rotate_ceiling():
    W.tokens = ge.CONTINUE_MAX_TOKENS + 1
    return observe(["m-ceil"], sup(seed_running("m-ceil")))


def s_replace_turn_done():
    hs = seed_running("m-tdone")
    hs[0]["state"] = "done"
    hs[0].pop("status")
    return observe(["m-tdone"], sup(hs))


def s_replace_owner_dead():
    hs = seed_running("m-dead")
    hs[0]["state"] = "stopped"
    hs[0].pop("status")
    return observe(["m-dead"], sup(hs))


def s_gsd_complete():
    return observe(["m-gdone"], sup(seed_running("m-gdone"), gsd="ALL_COMPLETE"))


def s_gsd_hold_block_unblock():
    hs = seed_running("m-hold")
    rows = sup(hs, gsd="NO_PHASES") + sup(hs, gsd="NO_PHASES", now=NOW + 300)
    rows += sup(hs, gsd="OK", now=NOW + 600)
    return observe(["m-hold"], rows)


def s_gsd_unavailable_held():
    return observe(["m-unav"], sup(seed_running("m-unav"), gsd="UNAVAILABLE"))


def s_provider_quota_hold():
    W.hold = {"class": "quota", "until": NOW + 600, "reason": "usage limit reached"}
    return observe(["m-quota"], sup(seed_running("m-quota")))


def s_provider_auth_hold():
    W.hold = {"class": "auth", "until": NOW + 900, "reason": "401", "streak": 2, "quarantine": False}
    return observe(["m-auth"], sup(seed_running("m-auth")))


def s_child_hold():
    W.children = "HOLD"
    return observe(["m-child"], sup(seed_running("m-child")))


def s_handoff_relay():
    hs = seed_running("m-hand")
    gm.request_handoff(hs[0]["sessionId"], "explicit hand-off note", now=NOW)
    return observe(["m-hand"], sup(hs, now=NOW + 5))


def s_wall_enforced():
    hs = seed_running("m-wall")
    hs[0]["status"] = "busy"
    flag = Path(TMP) / f"mission-wall-{hs[0]['sessionId']}-e1.flag"
    flag.write_text(json.dumps({"asked_at": (NOW - ge.WALL_GRACE_S - 100) * 1000, "n": 2}),
                    encoding="utf-8")
    return observe(["m-wall"], sup(hs))


def s_budget_halt_renew():
    return observe(["m-budget"], sup(seed_running("m-budget", max_cycles=1)))


def s_budget_halt_complete():
    return observe(["m-bdone"], sup(seed_running("m-bdone", max_cycles=1), gsd="ALL_COMPLETE"))


def s_no_progress_halt():
    W.fp = "same-tree"
    hs = seed_running("m-stall", progress={"fp": "same-tree", "stalls": gm.NO_PROGRESS_EPOCHS - 1,
                                           "measured": True})
    return observe(["m-stall"], sup(hs))


def s_waiting_human_then_unblock():
    hs = seed_running("m-human")
    hs[0]["waitingFor"] = "permission prompt"
    rows = sup(hs)
    hs[0].pop("waitingFor")
    hs[0]["status"] = "busy"
    rows += sup(hs, now=NOW + 60)
    return observe(["m-human"], rows)


def s_records_and_argv():
    """create/arm record shape and worker_argv for every option the launch carries."""
    gm.create(TMP, "/gsd-autonomous --ws alpha", mission_id="m-rec", now=NOW)
    armed = gm.arm(TMP, "/gsd-autonomous", launch=False, mission_id="m-arm", now=NOW)["mission"]
    rec = {**armed, "epoch": 3, "allowed_tools": ["Bash(git:*)"], "add_dirs": ["D:/extra"],
           "permission_mode": "auto", "card": gm.render_card({**armed, "epoch": 3}),
           "autocompact": "500k"}
    plain = gm.worker_argv(rec, "/gsd-autonomous")
    (Path(TMP) / "worker-mcp-probe.json").write_text(
        json.dumps({"verdict": "APPLY", "measured_at": __import__("time").time()}), encoding="utf-8")
    stripped = gm.worker_argv(rec, "/gsd-autonomous")
    out = observe(["m-rec", "m-arm"], [])
    out["argv_plain"] = norm(plain)
    out["argv_mcp_apply"] = norm(stripped)
    return out


def s_cards():
    """Card bytes for the shapes T6 will add a block beside: workstream, directives, work tree,
    packet-free note, and the hard cap."""
    base = {"mission_id": "m-card", "epoch": 4, "cwd": TMP, "resume_command": "/gsd-autonomous",
            "workstream": "alpha", "directives": ["do X first"], "work_dir": TMP + "-wt",
            "note": "predecessor says phase 2 is half done"}
    facts = {"head": "abc1234", "dirty": 3, "recent": ["abc1234 one", "def5678 two"]}
    full = gm.render_card(base, facts, "GSD facts line")
    bare = gm.render_card({**base, "workstream": None, "directives": [], "work_dir": None, "note": ""})
    capped = gm.render_card({**base, "note": "x" * 20000}, facts, "g" * 4000)
    return {"full": norm(full), "bare": norm(bare), "capped": norm(capped),
            "capped_bytes": len(capped.encode("utf-8"))}


SCENARIOS = [s_launch_ack_heartbeat, s_adopt, s_replace_overdue_launch, s_halt_unacknowledged,
             s_relay_continue, s_relay_rotate_unmeasured, s_relay_rotate_ceiling,
             s_replace_turn_done, s_replace_owner_dead, s_gsd_complete, s_gsd_hold_block_unblock,
             s_gsd_unavailable_held, s_provider_quota_hold, s_provider_auth_hold, s_child_hold,
             s_handoff_relay, s_wall_enforced, s_budget_halt_renew, s_budget_halt_complete,
             s_no_progress_halt, s_waiting_human_then_unblock, s_records_and_argv, s_cards]


def snapshot() -> dict:
    CARDS.clear()
    install_world()
    out = {}
    for fn in SCENARIOS:
        reset()
        out[fn.__name__] = fn()
    return {"scenarios": out, "cards": dict(sorted(CARDS.items()))}


def diff(a, b, path="") -> list[str]:
    if type(a) is not type(b):
        return [f"{path}: type {type(a).__name__} != {type(b).__name__}"]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: {'missing now' if k not in b else 'new now'}")
            else:
                out += diff(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"] + [
                d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f"{path}[{i}]")][:3]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {str(a)[:80]!r} != {str(b)[:80]!r}"]


# ------------------------------------------------------------------------------- mutants
def _mut_route_v2():
    orig = gm.create
    gm.create = lambda *a, **k: _stamp(orig(*a, **k))
    return lambda: setattr(gm, "create", orig)


def _stamp(rec):
    gm.transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=rec["state"],
                  event="protocol_stamped", now=NOW, rollover_protocol="capsule-v2")
    return gm.load(rec["mission_id"])


def _mut_card_block():
    orig = gm.render_card
    gm.render_card = lambda rec, *a, **k: "MISSION CONTINUITY " + "CAPSULE-V2 block\n" + orig(rec, *a, **k)
    return lambda: setattr(gm, "render_card", orig)


def _mut_stop_authorization():
    orig = gm.stop_owner

    def stop(owner, sessions, **kw):
        lr.ledger_append("m-unmeas", "outgoing_stop_authorized", capsule_sha="x")
        return orig(owner, sessions, **kw)
    gm.stop_owner = stop
    return lambda: setattr(gm, "stop_owner", orig)


def _mut_argv_mcp():
    orig = gm.worker_argv
    gm.worker_argv = lambda rec, prompt: (lambda a: a[:4] + ["--strict-mcp-config"] + a[4:])(orig(rec, prompt))
    return lambda: setattr(gm, "worker_argv", orig)


MUTANTS = [("ROUTE-LEGACY-TO-V2", _mut_route_v2, "has_rollover_protocol"),
           ("CARD-V2-BLOCK", _mut_card_block, "/cards"),
           ("STOP-AUTH-ON-LEGACY", _mut_stop_authorization, "/events/"),
           ("ARGV-MCP-ON-LEGACY", _mut_argv_mcp, "argv")]


# ------------------------------------------------------------------------------- main
def _git_head() -> str:
    g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    try:
        return subprocess.run([g if Path(g).exists() else "git", "-C", str(HERE.parent), "rev-parse",
                               "--short=8", "HEAD"], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as exc:  # noqa: BLE001 -- meta only; the comparison never reads it
        return f"unreadable ({type(exc).__name__})"


def main(argv: list[str]) -> int:
    src = (HERE / "gsd_mission.py").read_bytes()
    snap = snapshot()
    if "--capture" in argv:
        if GOLDEN.exists() and "--force" not in argv:
            print(f"REFUSED: {GOLDEN.name} exists; a re-capture needs --force and a reviewed diff")
            return 2
        meta = {"captured_on_head": _git_head(),
                "gsd_mission_sha256": hashlib.sha256(src).hexdigest(),
                "gsd_mission_has_rollover_protocol": b"rollover_protocol" in src,
                "scenarios": len(SCENARIOS)}
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps({"meta": meta, **snap}, indent=1, ensure_ascii=False) + "\n",
                          encoding="utf-8", newline="\n")
        print(f"CAPTURED {GOLDEN} {meta}")
        return 0

    try:
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail("V-G23-GOLDEN-READABLE", f"{type(exc).__name__}: {exc}")
        print(f"G23_PASS={passes}/{passes + fails}")
        return 1
    meta = golden.get("meta") or {}
    check("V-G23-GOLDEN-PRE-CHANGE", meta.get("gsd_mission_has_rollover_protocol") is False,
          f"captured on {meta.get('captured_on_head')} without rollover_protocol in the source")
    want = {"scenarios": golden.get("scenarios"), "cards": golden.get("cards")}
    check("V-G23-POPULATION", len(want["scenarios"] or {}) == len(SCENARIOS) >= 20,
          f"{len(want['scenarios'] or {})} scenarios in the golden, {len(SCENARIOS)} here")

    for name, got in snap["scenarios"].items():
        d = diff(want["scenarios"].get(name), got, f"/{name}")
        check(f"V-G23-LEGACY {name}", not d, "; ".join(d[:4]))
    d = diff(want["cards"], snap["cards"], "/cards")
    check("V-G23-CARD-BYTES", not d, "; ".join(d[:4]) or f"{len(snap['cards'])} distinct cards")
    no_proto = [m for s in snap["scenarios"].values() for m, r in (s.get("records") or {}).items()
                if r and r["has_rollover_protocol"]]
    check("V-G23-NO-PROTOCOL-ON-LEGACY", not no_proto, str(no_proto))

    for name, apply, marker in MUTANTS:
        undo = apply()
        try:
            m = snapshot()
        finally:
            undo()
        d = diff(want, {"scenarios": m["scenarios"], "cards": m["cards"]})
        hit = [x for x in d if marker in x]
        check(f"V-G23-MUTANT-{name}", bool(hit), f"{len(d)} diffs, {len(hit)} at {marker!r}: {hit[:1]}")

    again = snapshot()
    d = diff(want, {"scenarios": again["scenarios"], "cards": again["cards"]})
    check("V-G23-CLEAN-AFTER-MUTANTS", not d, "; ".join(d[:3]))
    print(f"G23_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
