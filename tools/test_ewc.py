"""V-EWC gate: Stop hooks vs closure fixtures (target behaviour; RED until E2+)."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tools" / "fixtures" / "ewc"
HOOKS = ["hooks/closer-guard.js", "hooks/gsd_stop_continuation.js"]


def run_stop(case):
    """Run both real Stop hooks in a temp HOME; return (blocked, receipts)."""
    with tempfile.TemporaryDirectory() as home:
        env = dict(os.environ, HOME=home, USERPROFILE=home)
        for k in ("CPP_GSD_CONT_FORCE", "CPP_GSD_STOP_CONTINUATION"):
            env.pop(k, None)
        (Path(home) / ".claude" / "state").mkdir(parents=True)
        (Path(home) / ".claude" / "logs").mkdir(parents=True)
        payload = {"session_id": "ewc-" + case, "hook_event_name": "Stop",
                   "transcript_path": str(FIX / (case + ".jsonl")), "cwd": str(ROOT)}
        blocked = False
        for h in HOOKS:
            r = subprocess.run(["node", str(ROOT / h)], input=json.dumps(payload),
                               capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=300)
            try:
                out = json.loads(r.stdout or "{}")
            except ValueError:
                out = {}
            if out.get("decision") == "block":
                blocked = True
        rp = Path(home) / ".claude" / "state" / "autonomy-decisions.jsonl"
        rec = rp.read_text(encoding="utf8") if rp.exists() else ""
        return blocked, rec


results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("[PASS] " if ok else "[FAIL] ") + name + (("  :: " + detail) if detail and not ok else ""))


b, rec = run_stop("incident")
check("V-EWC-1 incident: blocked or CONTINUE_* receipt", b or "CONTINUE_" in rec)
b, rec = run_stop("complete")
check("V-EWC-2a complete: not blocked", not b)
check("V-EWC-2b complete: STOP_COMPLETE receipt", "STOP_COMPLETE" in rec)
b, rec = run_stop("human_only")
check("V-EWC-3a human-only: not blocked", not b)
check("V-EWC-3b human-only: STOP_HUMAN_GATE receipt", "STOP_HUMAN_GATE" in rec)
# ---- Stop-level gate scenarios (E3): drive gsd_stop_continuation.js alone in a temp HOME ----
sys.path.insert(0, str(ROOT))
GSD = str(ROOT / "hooks" / "gsd_stop_continuation.js")
REPO = "abcdef0123456"
_hr = Path(tempfile.mkdtemp()) / "highram.js"
_hr.write_text("require('os').freemem = () => 64 * 1024 * 1048576;\n", encoding="utf8")
HIGH_RAM = str(_hr).replace("\\", "/")


class Home:
    def __init__(self):
        self._t = tempfile.TemporaryDirectory()
        self.home = Path(self._t.name)
        (self.home / ".claude" / "state").mkdir(parents=True)
        (self.home / ".claude" / "logs").mkdir(parents=True)
        self.goals = self.home / "goals"
        self.state = self.home / ".claude" / "state"

    def env(self, **kw):
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home),
                 GSDX_GOALS_ROOT=str(self.goals))
        for k in ("CPP_GSD_CONT_FORCE", "CPP_GSD_STOP_CONTINUATION", "CPP_EWC_GATE",
                  "GSD_LONG_RUN_STATE_DIR", "NODE_OPTIONS"):
            e.pop(k, None)
        e["NODE_OPTIONS"] = "--require " + HIGH_RAM          # hermetic: host RAM must not decide a verdict
        e.update({k: v for k, v in kw.items() if v is not None})
        return e

    def stop(self, case="complete", sid="t1", tp=None, **env):
        payload = {"session_id": sid, "hook_event_name": "Stop", "cwd": str(ROOT),
                   "transcript_path": tp or str(FIX / (case + ".jsonl"))}
        r = subprocess.run(["node", GSD], input=json.dumps(payload), capture_output=True, text=True,
                           env=self.env(**env), cwd=str(ROOT), timeout=300)
        out = json.loads(r.stdout or "{}")
        return out, self.receipts()

    def receipts(self):
        p = self.state / "autonomy-decisions.jsonl"
        return [json.loads(l) for l in p.read_text(encoding="utf8").splitlines() if l.strip()] if p.exists() else []

    def marker(self, sid="t1", **kw):
        m = {"phase": 1, "cycles": 0, "continuation": "stop-block", "cwd": str(self.home),
             "armed_at": __import__("datetime").datetime.now().isoformat()}
        m.update(kw)
        (self.state / f"gsd-autorun-{sid}.json").write_text(json.dumps(m), encoding="utf8")

    def log(self, goal_id):
        from modules.gsd_x.goal.log import GoalLog
        return GoalLog(REPO, goal_id, base=self.goals)

    def say(self, text, name="turn"):
        """Write a one-turn transcript whose last assistant message is `text`; return its path."""
        p = self.home / (name + ".jsonl")
        u = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "go"}]}}
        a = {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}
        p.write_text(json.dumps(u) + "\n" + json.dumps(a) + "\n", encoding="utf8")
        return str(p)

    def add(self, text, sid="t1", sev="RED", owner="AGENT", act="NOW", source="test"):
        from modules.gsd_x.goal import session_scope as ss
        os.environ["GSDX_GOALS_ROOT"] = str(self.goals)
        return ss.add(REPO, sid, text=text, source=source, severity=sev, actionability=act,
                      owner_class=owner, next_action="Do the work: " + text)

    def close(self, oid, sid="t1"):
        from modules.gsd_x.goal import session_scope as ss
        os.environ["GSDX_GOALS_ROOT"] = str(self.goals)
        ss.close(REPO, sid, oid, "pytest tools/x: exit 0")


def last(recs):
    return recs[-1] if recs else {}


# modes (both poles)
h = Home()
out, rec = h.stop("incident", CPP_EWC_GATE="enforce")
check("V-EWC-4a enforce incident: blocked, CONTINUE_*, mode=enforce, would_block", out.get("decision") == "block"
      and last(rec).get("category").startswith("CONTINUE_") and last(rec).get("mode") == "enforce" and last(rec).get("would_block") is True)
check("V-EWC-4b enforce block names ONE obligation by id + action", "Next: s-" in out.get("reason", "") and "Action:" in out.get("reason", ""))
h = Home()
out, rec = h.stop("incident", CPP_EWC_GATE="shadow")
check("V-EWC-5a shadow incident: never blocks, would_block=true",
      out.get("decision") != "block" and last(rec).get("would_block") is True and last(rec).get("mode") == "shadow")
h = Home()
out, rec = h.stop("incident")
check("V-EWC-5b default interactive (no marker) is shadow", out.get("decision") != "block" and last(rec).get("mode") == "shadow")
h = Home(); h.marker()
out, rec = h.stop("incident")
check("V-EWC-5c armed mission default is enforce: blocked", out.get("decision") == "block" and last(rec).get("mode") == "enforce")
h = Home()
out, rec = h.stop("incident", CPP_EWC_GATE="off")
check("V-EWC-5d off: no gate receipt, no block", out.get("decision") != "block" and not rec)
for c, cat in (("complete", "STOP_COMPLETE"), ("human_only", "STOP_HUMAN_GATE")):
    h = Home()
    out, rec = h.stop(c, CPP_EWC_GATE="enforce")
    check(f"V-EWC-6 enforce {c}: not blocked, {cat}", out.get("decision") != "block" and last(rec).get("category") == cat)
h = Home()
out, rec = h.stop("human_only", CPP_EWC_GATE="enforce")
check("V-EWC-6c human gate carries a <= 6 line decision package", 0 < len(last(rec).get("decision_package", [])) <= 6)

# ledger-driven (session ledger, no transcript findings)
h = Home(); oid = h.add("Re-run the gate for module X")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-7a ledger AGENT/NOW open + clean transcript: CONTINUE", out.get("decision") == "block" and oid in out["reason"])
h.close(oid)
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-7b ledger obligation closed: STOP_COMPLETE", out.get("decision") != "block" and last(rec).get("category") == "STOP_COMPLETE")
h = Home(); h.add("Owner picks the palette", owner="OWNER", act="HUMAN_PREF", sev="INFO")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-7c only an Owner obligation open: HUMAN_GATE", out.get("decision") != "block" and last(rec).get("category") == "STOP_HUMAN_GATE")

# unreadable state
h = Home()
d = h.goals / REPO / "session-t1"
d.mkdir(parents=True); (d / "000001.json").write_text("{broken", encoding="utf8")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-8a unreadable ledger: STOP_UNKNOWN, allowed", out.get("decision") != "block" and last(rec).get("category") == "STOP_UNKNOWN")
check("V-EWC-8b unreadable ledger is never STOP_COMPLETE", not any(r["category"] == "STOP_COMPLETE" for r in rec))

# livelock: same digest twice -> one block only
h = Home()
o1, _ = h.stop("incident", CPP_EWC_GATE="enforce")
o2, rec = h.stop("incident", CPP_EWC_GATE="enforce")
check("V-EWC-9a same open-set digest twice: second not blocked", o1.get("decision") == "block"
      and o2.get("decision") != "block" and last(rec).get("category") == "NO_DELTA")
# 3 continuations without progress -> STALLED + diagnosis obligation
h = Home()
verdicts = []
for i in range(5):
    h.add(f"Fix distinct failure number {i} in module {chr(97 + i)}")
    o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
    verdicts.append((o.get("decision"), last(rec).get("category")))
check("V-EWC-9b 3 no-progress continuations then STALLED allow",
      [v[0] for v in verdicts[:3]] == ["block"] * 3 and verdicts[3][1] == "STALLED" and verdicts[3][0] is None, str(verdicts))
sd = h.goals / REPO / "session-t1"
evs = [json.loads(p.read_text(encoding="utf8")) for p in sorted(sd.glob("0*.json"))]
diag = [e for e in evs if e["data"].get("source") == "stalled_diagnosis"]
chain_ok = True
try:
    from modules.gsd_x.goal.log import GoalLog
    GoalLog(REPO, "session-t1", base=h.goals).read()          # Python verifies the hash chain Node extended
except Exception as exc:                                    # noqa: BLE001
    chain_ok = False
check("V-EWC-9c STALLED records AGENT/NOW 'change strategy' obligation, chain intact",
      len(diag) == 1 and diag[0]["data"]["owner_class"] == "AGENT" and diag[0]["data"]["actionability"] == "NOW"
      and "Change strategy" in diag[0]["data"]["next_action"] and chain_ok)
# progress resets the counter (positive pole of livelock)
h = Home(); a = h.add("Fix failure alpha in module a"); b = h.add("Fix failure beta in module b")
h.add("Fix failure gamma in module c")
o, _ = h.stop("complete", CPP_EWC_GATE="enforce")
h.close(a); o2, _ = h.stop("complete", CPP_EWC_GATE="enforce")
h.close(b); o3, rec = h.stop("complete", CPP_EWC_GATE="enforce")
_sp = h.home / ".claude" / "logs" / "gsd-continuation-state.json"
st = json.loads(_sp.read_text(encoding="utf8")).get("t1", {}) if _sp.exists() else {}
check("V-EWC-9d fewer NOW obligations = progress: keeps blocking, no STALLED",
      all(x.get("decision") == "block" for x in (o, o2, o3)) and st["noProgress"] == 0, str([x.get("decision") for x in (o, o2, o3)]) + str(st))

# budget / RAM / ping-pong / streak (allow-conditions), each with its positive control
h = Home(); h.marker(cycles=99, max_cycles=40); h.add("Fix failure in module q")
out, rec = h.stop("complete")
check("V-EWC-10a budget exhausted: allowed, BUDGET", out.get("decision") != "block" and last(rec).get("category") == "BUDGET")
h = Home(); h.marker(cycles=1, max_cycles=40); h.add("Fix failure in module q")
out, rec = h.stop("complete")
check("V-EWC-10b budget available (control): blocked", out.get("decision") == "block", str(rec))
stub = Path(tempfile.mkdtemp()) / "lowram.js"
stub.write_text("require('os').freemem = () => 100 * 1048576;\n", encoding="utf8")
h = Home(); h.add("Fix failure in module q")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce", NODE_OPTIONS="--require " + str(stub).replace("\\", "/"))
check("V-EWC-10c RAM floor: allowed, STOP_RESOURCE_BLOCKED", out.get("decision") != "block"
      and last(rec).get("category") == "STOP_RESOURCE_BLOCKED")
h = Home(); h.add("Fix failure in module q")
(h.home / ".claude" / "logs" / "closer-guard-state.json").write_text(json.dumps({"t1": {"blocked": True}}), encoding="utf8")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-10d closer-guard blocked this session: no ping-pong", out.get("decision") != "block"
      and last(rec).get("category") == "DEFER_CLOSER", str(rec))
h = Home(); h.add("Fix failure in module q")
sf = h.home / ".claude" / "logs" / "gsd-continuation-state.json"
sf.write_text(json.dumps({"t1": {"blocked": True, "streak": 6, "obDigest": "zzz", "mfp": "", "nowCount": 9, "maxSev": 3}}), encoding="utf8")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-10e streak ceiling kept: allowed", out.get("decision") != "block" and last(rec).get("category") == "STREAK_CEILING", str(rec))

# goal-bound session reads the GOAL log (observe-only binding)
h = Home()
from modules.gsd_x.goal.log import GoalLog
glog = GoalLog(REPO, "ewc-g1", base=h.goals)
glog.append(1, "obligation.accepted", {"id": "ob-1", "plane": "OUTCOME", "text": "Ship the thing", "done_gate": "",
            "gate_pin": [], "revision": "r1", "gate_class": "unit"}, "t")
bd = h.state / "goal-binding"; bd.mkdir()
(bd / "t1.json").write_text(json.dumps({"goal": "ewc-g1"}), encoding="utf8")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-11a goal-bound: open goal obligation drives CONTINUE", out.get("decision") == "block" and "ob-1" in out["reason"], str(out) + str(rec))
check("V-EWC-11b goal-bound hook never writes a binding", sorted(p.name for p in bd.iterdir()) == ["t1.json"])
h2 = Home()
out, rec = h2.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-11c no binding, no ledger (control): COMPLETE", out.get("decision") != "block" and last(rec).get("category") == "STOP_COMPLETE")

# ---- E4 (M8): unread child output is an obligation; ledger obligations reach the successor card + capsule ----
h = Home()
tmpd = h.home / "tmp"
(tmpd / "claude" / "ewc" / "t1" / "tasks").mkdir(parents=True)
(tmpd / "claude" / "ewc" / "t1" / "tasks" / "bx1.output").write_text("result: 3 failures", encoding="utf8")
out, rec = h.stop("complete", CPP_EWC_GATE="enforce", TEMP=str(tmpd), TMP=str(tmpd), TMPDIR=str(tmpd))
check("V-EWC-12a unread task output (interactive, no marker, empty ledger) drives CONTINUE",
      out.get("decision") == "block" and "UNCONSUMED_CHILD" in out.get("reason", ""), str(out) + str(rec))
h = Home()
(h.home / "tmp").mkdir()
out, rec = h.stop("complete", CPP_EWC_GATE="enforce", TEMP=str(h.home / "tmp"), TMP=str(h.home / "tmp"))
check("V-EWC-12b no task output (control): COMPLETE", out.get("decision") != "block"
      and last(rec).get("category") == "STOP_COMPLETE", str(rec))

from modules.gsd_x.goal import session_scope as _ss
from modules.gsd_x.goal.log import repo_id as _rid
h = Home()
os.environ["GSDX_GOALS_ROOT"] = str(h.goals)
_rep = _rid(ROOT)
for i in range(12):
    _ss.add(_rep, "t1", text=f"Fix failure number {i}", source="test", severity="RED", actionability="NOW",
            owner_class="AGENT", next_action=f"Do the work {i}")
_lines = _ss.open_lines(str(ROOT), "t1")
check("V-EWC-13a open_lines: <= 10 lines, id + severity + next_action", 0 < len(_lines) <= 10
      and "RED" in _lines[0] and "Do the work" in _lines[0], str(_lines))
check("V-EWC-13b open_lines: other session / no repo => no lines (control)",
      _ss.open_lines(str(ROOT), "other") == [] and _ss.open_lines(str(h.home), "t1") == [])
sys.path.insert(0, str(ROOT / "tools"))
import gsd_mission as _gm, rollover as _ro
_card = _gm.render_card({"epoch": 2, "mission_id": "m-x", "cwd": str(ROOT), "owner": {"session_id": "t1"},
                         "resume_command": "x", "directives": []})
check("V-EWC-13c successor card carries the open obligations", "OPEN OBLIGATIONS" in _card and "Do the work" in _card, _card[:400])
_boot = _ro.bootstrap({"session_id": "t1", "cwd": str(ROOT), "repo": {}, "obligations": [], "handoff": {}})
check("V-EWC-13d /kclear capsule bootstrap carries the open obligations", "Do the work" in _boot, _boot[:400])
_card0 = _gm.render_card({"epoch": 2, "mission_id": "m-x", "cwd": str(ROOT), "owner": {"session_id": "none"},
                          "resume_command": "x", "directives": []})
check("V-EWC-13e no ledger (control): no OPEN OBLIGATIONS block", "OPEN OBLIGATIONS" not in _card0)
# fresh epoch: new context, next action exists only in the ledger => CONTINUE at Stop
out, rec = h.stop("complete", CPP_EWC_GATE="enforce")
check("V-EWC-13f fresh-epoch fixture: ledger-only obligation still yields CONTINUE",
      out.get("decision") == "block" and "CONTINUE_" in json.dumps(rec), str(out) + str(rec))

# ---- E5 (M9): fault matrix. One V-EWC-FM-* gate per row; the expected verdict is in the gate name. ----
def blocked(o):
    return o.get("decision") == "block"


def cat(rec):
    return last(rec).get("category")


def fm(name, verdict, ok, detail=""):
    check(f"V-EWC-FM-{name} -> {verdict}", ok, detail)


def table(*rows):
    return "\n".join(["| Check | Result |", "|---|---|"] + list(rows))


def say_stop(text, **env):
    h = Home()
    o, rec = h.stop(tp=h.say(text), CPP_EWC_GATE="enforce", **env)
    return h, o, rec


def no_complete(rec):
    return not any(r["category"] == "STOP_COMPLETE" for r in rec)


h, o, rec = say_stop(table("| Contrast ratio | FAIL (RED) |"))
fm("01-red-internal-fix", "CONTINUE_FAILED_GATE (block)", blocked(o) and cat(rec) == "CONTINUE_FAILED_GATE", str(rec))
h, o, rec = say_stop(table("| Spacing scale | WARN: 3 off-grid values, fixable |"))
fm("02-amber-actionable", "CONTINUE_ACTIONABLE_WARNING (block)", blocked(o) and cat(rec) == "CONTINUE_ACTIONABLE_WARNING", str(rec))
h = Home(); h.add("Optional polish of the changelog wording", sev="INFO", act="INFO")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("03-info-warning-no-obligation", "STOP_COMPLETE", not blocked(o) and cat(rec) == "STOP_COMPLETE", str(rec))
h, o, rec = say_stop("Everything is green. Final visual approval is the Owner's call.")
fm("04-subjective-only", "STOP_HUMAN_GATE", not blocked(o) and cat(rec) == "STOP_HUMAN_GATE", str(rec))
h, o, rec = say_stop("The evidence file was not written for this run.")
fm("05-missing-evidence", "CONTINUE_MISSING_EVIDENCE (block)", blocked(o) and cat(rec) == "CONTINUE_MISSING_EVIDENCE", str(rec))
h, o, rec = say_stop("The changes are not committed yet and sit in the working tree.")
fm("06-missing-commit", "CONTINUE_* (block)", blocked(o) and str(cat(rec)).startswith("CONTINUE_"), str(rec))
h, o, rec = say_stop("Next iteration: tighten the spacing scale and fix contrast -- I recommend doing it next.")
fm("07-explicit-next-action", "CONTINUE_KNOWN_NEXT_ACTION (block)", blocked(o) and cat(rec) == "CONTINUE_KNOWN_NEXT_ACTION", str(rec))
h = Home(); oid = h.add("Reviewer finding: null deref in parser.py line 40", source="review")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("08-review-finding", "CONTINUE_OPEN_OBLIGATION (block, names the id)",
   blocked(o) and oid in o.get("reason", "") and cat(rec) == "CONTINUE_OPEN_OBLIGATION", str(rec))
h, o, rec = say_stop(table("| pytest tools/test_x.py | 2 FAILED |"))
fm("09-failed-test", "CONTINUE_FAILED_GATE (block)", blocked(o) and cat(rec) == "CONTINUE_FAILED_GATE", str(rec))
h, o, rec = say_stop("The Production Reality evidence was not produced for this change.")
fm("10-production-reality-missing", "CONTINUE_MISSING_EVIDENCE (block)", blocked(o) and cat(rec) == "CONTINUE_MISSING_EVIDENCE", str(rec))
h = Home(); h.add("Owner picks the logo colour", owner="OWNER", act="HUMAN_PREF", sev="INFO")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("11-human-preference", "STOP_HUMAN_GATE", not blocked(o) and cat(rec) == "STOP_HUMAN_GATE", str(rec))
h = Home(); h.add("Irreversible: drop the production table", owner="OWNER", act="APPROVAL", sev="AMBER")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("12-irreversible", "STOP_HUMAN_GATE", not blocked(o) and cat(rec) == "STOP_HUMAN_GATE", str(rec))
h = Home(); h.add("Outward-facing: publish the release to the public registry", owner="OWNER", act="APPROVAL", sev="AMBER")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("13-outward-without-authorization", "STOP_HUMAN_GATE", not blocked(o) and cat(rec) == "STOP_HUMAN_GATE", str(rec))
h = Home(); h.add("Provider quota exhausted; needs a funded API key", owner="OWNER", act="RESOURCE", sev="AMBER")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("14-provider-resource-block", "STOP_RESOURCE_BLOCKED", not blocked(o) and cat(rec) == "STOP_RESOURCE_BLOCKED", str(rec))
print("[GAP] V-EWC-FM-15-token-budget-exhausted: the Stop gate has no token-budget input (ewcGate bounds max_cycles/max_hours only; "
      "tokens are bounded by the cost breaker outside Stop). Not counted as a pass.")
h = Home(); h.marker(cycles=40, max_cycles=40); h.add("Fix failure in module q")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("16-iteration-budget-exhausted", "BUDGET (allowed, receipt names the suppressed CONTINUE)", not blocked(o) and cat(rec) == "BUDGET"
   and str(last(rec).get("suppressed_verdict")).startswith("CONTINUE_"), str(rec))


def growing(h, n):
    o, rec = {}, []
    for i in range(n):
        o, rec = h.stop(tp=h.say(table(*[f"| Gate {chr(97 + k)}{i} | FAIL |" for k in range(i + 1)])), CPP_EWC_GATE="enforce")
    return o, rec


h = Home()
o, rec = growing(h, 4)
fm("17-same-repair-fails-3x", "STALLED (allowed on the 4th stop)", not blocked(o) and cat(rec) == "STALLED", str(rec))
h = Home()
gd = h.goals / REPO / "ewc-g2"; gd.mkdir(parents=True); (gd / "000001.json").write_text("{broken", encoding="utf8")
bd = h.state / "goal-binding"; bd.mkdir(); (bd / "t1.json").write_text(json.dumps({"goal": "ewc-g2"}), encoding="utf8")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("19-goal-spine-unreadable", "STOP_UNKNOWN (allowed, never COMPLETE)", not blocked(o) and cat(rec) == "STOP_UNKNOWN" and no_complete(rec), str(rec))
h = Home()
h.goals.mkdir(parents=True); (h.goals / "e0c0e0c0e0c0").write_text("not a directory", encoding="utf8")
o, rec = growing(h, 4)
fm("20-obligation-write-fails", "STALLED (allowed; hook survives the failed diagnosis write)",
   not blocked(o) and cat(rec) == "STALLED" and (h.goals / "e0c0e0c0e0c0").is_file(), str(rec))
_th = Path(tempfile.mkdtemp()) / "throw.js"
_th.write_text("const M=require('module');const o=M.prototype.require;M.prototype.require=function(id){const r=o.apply(this,arguments);"
               "if(/ewc_gate(\\.js)?$/.test(id)&&r&&r.evaluate){r.evaluate=function(){throw new Error('boom');};}return r;};\n"
               "require('os').freemem = () => 64 * 1024 * 1048576;\n", encoding="utf8")
h = Home(); h.add("Fix failure in module q")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce", NODE_OPTIONS="--require " + str(_th).replace("\\", "/"))
fm("21-evaluator-throws", "continue (fail-open, no crash, no STOP_COMPLETE receipt)", not blocked(o) and no_complete(rec), str(o) + str(rec))
h = Home()
o, rec = h.stop(tp=str(h.home / "no-such-transcript.jsonl"), CPP_EWC_GATE="enforce")
fm("22-completion-unknown", "STOP_UNKNOWN (allowed, never COMPLETE)", not blocked(o) and cat(rec) == "STOP_UNKNOWN", str(rec))
h = Home(); h.add("Optional: reword the changelog entry", sev="AMBER", act="INFO")
o1, rec = h.stop("complete", CPP_EWC_GATE="enforce"); o2, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("23-one-optional-warning-left", "STOP_COMPLETE twice, never blocks", not blocked(o1) and not blocked(o2)
   and [r["category"] for r in rec] == ["STOP_COMPLETE", "STOP_COMPLETE"], str(rec))
h, o, rec = say_stop("A future project could add dark mode to the dashboard, but that is outside this task.")
fm("24-out-of-scope-opportunity", "STOP_COMPLETE (no obligation)", not blocked(o) and cat(rec) == "STOP_COMPLETE" and last(rec).get("open") == 0, str(rec))
h = Home(); a = h.add("Fix failure alpha in module a"); b = h.add("Fix failure beta in module b")
o1, _ = h.stop("complete", CPP_EWC_GATE="enforce")
h.close(a); o2, _ = h.stop("complete", CPP_EWC_GATE="enforce")
h.close(b); o3, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("25-two-independent-obligations", "block, block (names the other), STOP_COMPLETE", blocked(o1) and blocked(o2)
   and b in o2.get("reason", "") and not blocked(o3) and cat(rec) == "STOP_COMPLETE", str(o2) + str(rec))
h = Home(); h.add("Run the integration suite once the deploy lands", act="AFTER_DEP")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("26a-after-dep-is-not-now", "STOP_SCHEDULED_WAIT (allowed)", not blocked(o) and cat(rec) == "STOP_SCHEDULED_WAIT", str(rec))
now_id = h.add("Land the deploy of module z")
o, rec = h.stop("complete", CPP_EWC_GATE="enforce")
fm("26b-now-blocker-named-not-dependent", "block naming the NOW obligation", blocked(o) and now_id in o.get("reason", ""), str(o))
h = Home(); tmpd = h.home / "tmp"; tdir = tmpd / "claude" / "ewc" / "t1" / "tasks"; tdir.mkdir(parents=True)
tenv = dict(TEMP=str(tmpd), TMP=str(tmpd), TMPDIR=str(tmpd))
o1, rec1 = h.stop("complete", CPP_EWC_GATE="enforce", **tenv)
(tdir / "bx2.output").write_text("result: 1 failure", encoding="utf8")
o2, rec2 = h.stop("complete", CPP_EWC_GATE="enforce", **tenv)
fm("27-child-result-arrives-during-evaluation", "STOP_COMPLETE then block UNCONSUMED_CHILD (no loss)", not blocked(o1)
   and cat(rec1) == "STOP_COMPLETE" and blocked(o2) and "UNCONSUMED_CHILD" in o2.get("reason", ""), str(o2) + str(rec2))

print("EWC_PASS=%d/%d" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
