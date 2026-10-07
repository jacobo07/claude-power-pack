"""V-GOAL-* gates: pre-call goal budget admission (vault/specs/goal-budget-admission.md).

Origin: A1 (vault/programs/cognitive-economy/gen2/AMENDMENT-A1-2026-10-07.md, INCIDENT 2026-10-07)
spent 42,307,381 against a 20M cap that was only read after the spend. These gates pin the Owner's
mutation list -- concurrent last reserve, Agent spawn over remaining, resume reset, cross-account,
crash with a live lease, UNKNOWN cost -- plus the audit gaps (idempotent settle, cap as journal state,
leaked-lease settlement, agent-side raise, roots overlap, exemption narrowing, subagent spend, fail
closed). Every refusal is paired with a control in which the same input fits and is admitted: a gate
that refuses everything would pass every refusal assertion.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PP))
import mission_spend as ms  # noqa: E402
from modules.provider_routing.ledger import GoalLedger, LedgerError  # noqa: E402

GUARD = PP / "hooks" / "session_budget_guard.js"
DISPATCHER = PP / "hooks" / "hook-dispatcher.js"
NODE = shutil.which("node") or "node"
HOST = ms.socket.gethostname() if hasattr(ms, "socket") else __import__("socket").gethostname()

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


class Env:
    """An isolated state dir; CLAUDECODE removed unless a gate asks for it."""
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="goal_"))
        self.state = self.root / "state"
        self.state.mkdir()
        self.saved = {k: os.environ.get(k) for k in ("GSD_LONG_RUN_STATE_DIR", "CLAUDECODE", "CPP_GOAL")}
        os.environ["GSD_LONG_RUN_STATE_DIR"] = str(self.state)
        os.environ.pop("CLAUDECODE", None)
        os.environ.pop("CPP_GOAL", None)

    def close(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.root, ignore_errors=True)


def declare(goal, cap, owner=True, **kw):
    """owner=True stands for the Owner's interactive confirmation; gates that test its absence pass False."""
    return ms.goal_declare(goal, cap, "test", kw.get("roots"), kw.get("hosts"), kw.get("lease_calls"), owner=owner)


# --- review 31f1e714 gates (H1 authority, M1 agent hold, L1 ids) --------------------------------------

def g_review_fixes():
    e = Env()
    try:
        try:
            ms._goal_ledger("..")
            check("V-GOAL-ID-DOTS", False, "goal id '..' accepted: its ledger would sit in state/ itself")
        except ValueError:
            check("V-GOAL-ID-DOTS", "a.b" == ms._goal_ledger("a.b").goal, "'..' refused, 'a.b' admitted")

        declare("o", 1000, lease_calls=1)
        r = declare("o", 2000, owner=False)
        ok = declare("o", 900, owner=False)
        check("V-GOAL-RAISE-NEEDS-OWNER", not r["ok"] and ok["ok"] and ok["cap"] == 900,
              f"no CLAUDECODE, no Owner confirmation: raise -> {r.get('reason', '')[:50]}; lowering admitted")
        p = subprocess.run([sys.executable, str(HERE / "mission_spend.py"), "goal-declare", "--goal", "o",
                            "--cap", "5000", "--source", "t", "--owner"],
                           input="o\n", capture_output=True, text=True, env=dict(os.environ))
        out = json.loads(p.stdout.strip().splitlines()[-1])
        check("V-GOAL-OWNER-NEEDS-TTY", p.returncode == 3 and "TTY" in out["reason"],
              f"--owner with piped stdin (an agent shell) -> exit {p.returncode}: {out['reason']}")

        declare("ah", 10_000, lease_calls=1)
        led = GoalLedger(ms.goal_root() / "ah", "ah")
        led.renew("p", 0, 100)
        rid = led.spawn("p", 1000, base=0)["reservation"]
        led.renew("p", 300, 100)                  # the child's first 300 land; the parent renews
        st, res = led.status(), led._gfold(led._read())["res"][rid]
        check("V-GOAL-AGENT-HOLD-SURVIVES-RENEW", res["state"] == "RESERVED" and st["used"] == 300 + 700 + 100,
              f"after a renew the hold is still open and shrunk: state {res['state']}, used {st['used']} (want 1100)")
        led.renew("p", 1300, 100)
        res = led._gfold(led._read())["res"][rid]
        check("V-GOAL-AGENT-HOLD-RELEASED", res["state"] == "SETTLED" and led.status()["used"] == 1400,
              f"once the child's spend reached the estimate the hold closes: {res['state']}, used {led.status()['used']}")
    finally:
        e.close()


# --- ledger / CLI gates -----------------------------------------------------------------------------

def g_cap_journal():
    e = Env()
    try:
        declare("g1", 1000, lease_calls=1)
        led = GoalLedger(ms.goal_root() / "g1", "g1")
        check("V-GOAL-CAP-JOURNAL", led.status()["cap"] == 1000 and led.caps == {},
              f"cap folded from the journal = {led.status()['cap']}, constructor caps {led.caps}")
        try:
            led.reserve("x", "g1", 1)
            check("V-GOAL-NO-RAW-RESERVE", False, "reserve() admitted on a goal ledger")
        except LedgerError:
            check("V-GOAL-NO-RAW-RESERVE", True, "reserve() refused: renew()/spawn() are the only paths")
    finally:
        e.close()


def _race(cap, n=5):
    e = Env()
    try:
        declare("race", cap, lease_calls=1)
        env = dict(os.environ)
        procs = [subprocess.Popen([sys.executable, str(HERE / "mission_spend.py"), "goal-renew", "--goal", "race",
                                   "--session", f"s{i}", "--measured", "0", "--per-call", "100"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
                 for i in range(n)]
        outs = []
        for p in procs:
            lines = p.communicate(timeout=60)[0].strip().splitlines()
            try:
                outs.append(json.loads(lines[-1]))
            except (IndexError, ValueError):
                outs.append(None)              # a racer that crashed (e.g. a torn journal) never answered
        try:
            used = GoalLedger(ms.goal_root() / "race", "race").status()["used"]
        except LedgerError as ex:
            used = f"unreadable ({ex})"
        return sum(1 for o in outs if o and o["ok"]), sum(1 for o in outs if o is None), used
    finally:
        e.close()


def g_race():
    # Every racer must ANSWER: an unanswered racer is the lost-lock failure, not a refusal.
    # With headroom an admitted racer costs its lease (100) plus its final reply (100): cap 200 fits one.
    # The 4 losers each book their own final reply (they still answer the deny): used 100 + 4 x 100.
    won, mute, used = _race(200)
    check("V-GOAL-RACE-LAST", won == 1 and mute == 0 and used == 500,
          f"5 processes race a 200 cap with 100 leases + 100 replies: {won} admitted, {mute} unanswered, used {used}")
    won, mute, used = _race(1000)
    check("V-GOAL-RACE-CONTROL", won == 5 and mute == 0 and used == 500, f"same race at cap 1000: {won} admitted")


def g_settle_and_resume():
    e = Env()
    try:
        declare("s", 10_000, lease_calls=1)
        led = GoalLedger(ms.goal_root() / "s", "s")
        led.renew("a", 1000, 100)
        led.renew("a", 1000, 100)                     # replayed settle at the same cumulative total
        st = led.status()
        check("V-GOAL-SETTLE-IDEMPOTENT", st["settled"] == 1000 and st["open"] == 100,
              f"two settles at 1000: settled {st['settled']} open {st['open']} (one lease, not two)")
        GoalLedger(ms.goal_root() / "s", "s").renew("a", 0, 100)   # resume: a fresh process, counter at 0
        st = led.status()
        check("V-GOAL-RESUME-NO-RESET", st["settled"] == 1000,
              f"a resume reporting measured 0 keeps the watermark: settled {st['settled']}")
        led.renew("a", 1500, 100)
        check("V-GOAL-SETTLE-DELTA", led.status()["settled"] == 1500, f"growth books the delta: {led.status()['settled']}")
    finally:
        e.close()


def g_cross_account():
    e = Env()
    try:
        declare("acct", 400, lease_calls=1)
        a = ms.goal_renew("acct", "account-A-sid", 250, 50, HOST)
        b = ms.goal_renew("acct", "account-B-sid", 0, 50, HOST)
        check("V-GOAL-CROSS-ACCOUNT", a["ok"] and not b["ok"],
              f"A settles 250 + lease 50 + its reply 50; B (other account, same goal) -> {b.get('reason')}")
        declare("acct2", 400, lease_calls=1)
        c = ms.goal_renew("acct2", "account-B-sid", 0, 50, HOST)
        check("V-GOAL-CROSS-ACCOUNT-CONTROL", c["ok"], "B on its own goal is admitted")
    finally:
        e.close()


def g_crash_and_leak():
    e = Env()
    try:
        declare("c", 1000, lease_calls=1)
        now = [1_000_000.0]
        led = GoalLedger(ms.goal_root() / "c", "c", clock=lambda: now[0], leak_after_s=60)
        led.renew("w", 0, 400)                        # the worker crashes holding this lease
        now[0] += 3600
        st = led.status()
        journal = (ms.goal_root() / "c" / "spend.journal.jsonl").read_text(encoding="utf-8")
        leaked = [r for r in map(json.loads, filter(str.strip, journal.splitlines())) if r["op"] == "leak"]
        check("V-GOAL-CRASH-LEASE-COUNTS", st["used"] == 400 and len(leaked) == 1,
              f"lease abandoned an hour: used {st['used']}, leak records {len(leaked)}")
        led.renew("w", 650, 100)                      # it resumes: the leaked lease settles to MEASURED
        st = led.status()
        check("V-GOAL-SETTLE-AFTER-LEAK", st["settled"] == 650 and st["open"] == 100,
              f"settle after leak books measured 650 (not the 400 reserved): {st['settled']}/{st['open']}")
    finally:
        e.close()


def g_spawn():
    e = Env()
    try:
        declare("sp", 1000, lease_calls=1)
        ms.goal_renew("sp", "p", 850, 50, HOST)        # used 900; remaining 50 net of p's own reply (50)
        r = ms.goal_spawn("sp", "p", 100, 0, HOST)
        check("V-GOAL-SPAWN-OVER-REMAINING", not r["ok"], f"Agent estimate 100 vs remaining 50: {r['reason']}")
        r = ms.goal_spawn("sp", "p", 40, 0, HOST)
        check("V-GOAL-SPAWN-CONTROL", r["ok"], "estimate 40 fits and is reserved")
    finally:
        e.close()


def _two_panes(goal, per_call):
    """Two panes each spend exactly their lease until refused, then make one final reply of
    `per_call` (the request a deny cannot stop). Returns the total actually spent."""
    led = GoalLedger(ms.goal_root() / goal, goal)
    spent, live = {"a": 0, "b": 0}, ["a", "b"]
    for _ in range(100):
        for sid in list(live):
            r = led.renew(sid, spent[sid], 200, per_call=per_call)
            if r["ok"]:
                spent[sid] += r["lease"]["amount"]
            else:
                live.remove(sid)
                spent[sid] += 100
        if not live:
            break
    return sum(spent.values())


def g_headroom():
    # Canary #2 (CANARY.md, cc2a2a73): with the closeout gone, 195,084 of the 207,358 overshoot was one
    # final reply per pane after its deny. Headroom holds that reply back from every other pane.
    e = Env()
    try:
        declare("hr", 2000)
        declare("hr0", 2000)
        on, off = _two_panes("hr", 100), _two_panes("hr0", 0)
        check("V-GOAL-HEADROOM-CAP-HOLDS", on <= 2000 and off > 2000,
              f"spent incl. final replies: with headroom {on} <= 2000; control without it {off} > 2000")
        g = GoalLedger(ms.goal_root() / "hr", "hr")._gfold(GoalLedger(ms.goal_root() / "hr", "hr")._read())
        finals = [r for r in g["res"].values() if r.get("kind") == "final"]
        check("V-GOAL-HEADROOM-FINAL-HOLD", len(finals) == 2 and all(r["amount"] == 100 for r in finals),
              f"each refused pane books its final reply: {[(r['sid'], r['amount']) for r in finals]}")

        declare("hs", 1000)
        led = GoalLedger(ms.goal_root() / "hs", "hs")
        led.renew("p", 0, 200, per_call=100)                     # used 200, one live pane owes 100
        r = led.spawn("p", 750, base=0)
        check("V-GOAL-HEADROOM-SPAWN", not r["ok"] and "final reply" in r["reason"],
              f"raw remaining 800 but 700 net of the pane's reply: {r['reason'][:70]}")
        check("V-GOAL-HEADROOM-SPAWN-CONTROL", led.spawn("p", 700, base=0)["ok"], "700 fits net of headroom")
    finally:
        e.close()


def g_raise():
    e = Env()
    try:
        declare("r", 1000, lease_calls=1)
        ok = declare("r", 1500)
        check("V-GOAL-RAISE-CONTROL", ok["ok"] and ok["cap"] == 1500, "an Owner raise before crossing is admitted")
        os.environ["CLAUDECODE"] = "1"
        r = declare("r", 2000)
        low = declare("r", 1200)
        os.environ.pop("CLAUDECODE")
        check("V-GOAL-RAISE-FROM-AGENT", not r["ok"] and low["ok"] and low["cap"] == 1200,
              f"inside an agent: raise -> {r.get('reason')}; lowering admitted")
        ms.goal_renew("r", "x", 1300, 50, HOST)        # spent past the 1200 cap
        before = (ms.goal_root() / "r" / "spend.journal.jsonl").read_bytes()
        r = declare("r", 5000)
        after = (ms.goal_root() / "r" / "spend.journal.jsonl").read_bytes()
        check("V-GOAL-RAISE-CONTAINED", not r["ok"] and "CONTAINED" in r["reason"] and before == after,
              f"Owner raise after crossing -> {r['reason'][:60]}...; journal unchanged {before == after}")
    finally:
        e.close()


def g_host_and_roots():
    e = Env()
    try:
        root = e.root / "work"
        root.mkdir()
        declare("h", 1000, hosts=["SOME-OTHER-HOST"], roots=[str(root)])
        r = ms.goal_renew("h", "x", 0, 50, HOST)
        check("V-GOAL-UNKNOWN-HOST", not r["ok"] and r["reason"].startswith("UNKNOWN"), r["reason"])
        declare("h2", 1000, hosts=[HOST])
        check("V-GOAL-HOST-CONTROL", ms.goal_renew("h2", "x", 0, 50, HOST)["ok"], "listed host admitted")
        r = declare("h3", 1000, roots=[str(root / "sub")])
        check("V-GOAL-ROOTS-OVERLAP", not r["ok"] and "overlap" in r["reason"], r.get("reason"))
        r = declare("h4", 1000, roots=[str(e.root / "elsewhere")])
        check("V-GOAL-ROOTS-CONTROL", r["ok"], "a disjoint root is admitted")
        os.environ["CLAUDECODE"] = "1"
        r = declare("h", 1000, roots=[str(e.root / "elsewhere2")])
        os.environ.pop("CLAUDECODE")
        check("V-GOAL-NO-AGENT-REBIND", not r["ok"], f"an agent moving a goal's roots -> {r.get('reason')}")
    finally:
        e.close()


# --- guard gates ------------------------------------------------------------------------------------

RUNNER = r"""
const g = require(process.argv[1]);
let raw = ''; process.stdin.on('data', d => raw += d).on('end', () => {
  process.stdout.write(JSON.stringify({ out: g.decide(JSON.parse(raw)) }));
});
"""


def row(mid, n, ts="2099-01-01T00:00:00.000Z"):    # after any goal's `since`, so every row counts
    u = {"input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
    return json.dumps({"type": "assistant", "timestamp": ts, "uuid": "u-" + mid,
                       "message": {"id": mid, "model": "claude-opus-5-5", "usage": u,
                                   "content": [{"type": "text", "text": "x"}]}}) + "\n"


def run_guard(e, sid, tx, cwd, tool="Read", tool_input=None, **env_extra):
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(e.state))
    env.pop("CPP_SESSION_BUDGET", None)
    env.pop("CPP_GOAL", None)
    env.update(env_extra)
    ev = {"session_id": sid, "transcript_path": str(tx), "cwd": str(cwd), "tool_name": tool,
          "tool_input": tool_input or {"file_path": str(cwd / "f.txt")}}
    p = subprocess.run([NODE, "-e", RUNNER, str(GUARD)], input=json.dumps(ev), capture_output=True,
                       text=True, env=env, timeout=60)
    out = json.loads(p.stdout)["out"]
    d = (out or {}).get("hookSpecificOutput") or {}
    return d.get("permissionDecision"), d.get("permissionDecisionReason") or d.get("additionalContext") or ""


def g_guard():
    e = Env()
    try:
        work, other = e.root / "work", e.root / "other"
        work.mkdir()
        other.mkdir()
        # 1200: leases 100 then 150 admitted (each net of the pane's own reply), an Agent of one lease
        # (150) refused at 50 left net of headroom, and the next renew at 1050 + reply 200 refused.
        declare("gg", 1200, roots=[str(work)], lease_calls=1)
        tx = e.root / "t.jsonl"
        tx.write_text(row("m1", 100), encoding="utf-8")

        dec, why = run_guard(e, "unbound-1", tx, other)
        check("V-GOAL-GUARD-UNBOUND-INERT", dec is None and not (e.state / "session-budget-unbound-1.goal.json").exists(),
              "a session outside every root is untouched (no state, no verdict)")
        dec, why = run_guard(e, "bound-1", tx, work)
        gs = json.loads((e.state / "session-budget-bound-1.goal.json").read_text())
        check("V-GOAL-GUARD-BIND-CWD", dec is None and gs["lease"] and gs["lease"]["amount"] == 100,
              f"cwd under the goal root binds and leases: {gs['lease']}")

        with open(tx, "a", encoding="utf-8") as fh:
            fh.write(row("m2", 150))
        sub = e.root / "t" / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent-x.jsonl").write_text(row("a1", 600), encoding="utf-8")
        dec, why = run_guard(e, "bound-1", tx, work)
        gs = json.loads((e.state / "session-budget-bound-1.goal.json").read_text())
        check("V-GOAL-GUARD-SUBAGENT-SPEND", dec is None and gs["tokens"] == 850,
              f"main 250 + subagent 600 measured = {gs['tokens']}")

        dec, why = run_guard(e, "bound-1", tx, work, tool="Agent", tool_input={"prompt": "x"})
        check("V-GOAL-GUARD-AGENT-REFUSED", dec == "deny" and "child refused" in why,
              f"Agent with remaining < one lease: {why[:90]}")

        with open(tx, "a", encoding="utf-8") as fh:
            fh.write(row("m3", 200))
        dec, why = run_guard(e, "bound-1", tx, work, tool="Bash", tool_input={"command": "python big_job.py"})
        check("V-GOAL-GUARD-EXHAUSTED", dec == "deny" and "GOAL BUDGET (gg)" in why, why[:100])
        # Canary 2026-10-07 (CANARY.md, 51e46273): a free Read closeout after a goal refusal admitted
        # 793K of a 1.17M overshoot. A goal refusal admits ONE handoff write per pane and no reads.
        for n in range(5):
            dec, why = run_guard(e, "bound-1", tx, work)
            if dec != "deny":
                break
        check("V-GOAL-GUARD-NO-READ-CLOSEOUT", dec == "deny" and "GOAL BUDGET (gg)" in why,
              f"an exhausted goal pane gets no Read closeout (5 tries): {dec} {why[:70]}")
        hand = str(work / "memory" / "handoffs" / "h.md")
        dec, why = run_guard(e, "bound-1", tx, work, tool="Write", tool_input={"file_path": hand, "content": "x"})
        check("V-GOAL-GUARD-CLOSEOUT", dec is None and "closeout call 1/1" in why,
              f"an exhausted goal pane may write its handoff once: {why[:70]}")
        dec, why = run_guard(e, "bound-1", tx, work, tool="Write", tool_input={"file_path": hand, "content": "y"})
        check("V-GOAL-GUARD-CLOSEOUT-ONCE", dec == "deny", f"a second handoff write is denied: {why[:70]}")

        dec, _ = run_guard(e, "bound-1", tx, work, tool="Bash",
                           tool_input={"command": "python tools/mission_spend.py goal-status --goal gg"})
        check("V-GOAL-GUARD-STATUS-EXEMPT", dec is None, "a bare goal-status stays reachable when exhausted")
        dec, _ = run_guard(e, "bound-1", tx, work, tool="PowerShell", tool_input={
            "command": "& 'C:\\Py\\python.exe' 'tools\\mission_spend.py' goal-status --goal gg"})
        check("V-GOAL-GUARD-STATUS-EXEMPT-PS", dec is None, "the PowerShell call-operator form is exempt too")
        dec, _ = run_guard(e, "bound-1", tx, work, tool="Bash",
                           tool_input={"command": "python tools/heavy_job.py --tag mission_spend.py goal-status --goal gg"})
        check("V-GOAL-GUARD-EXEMPT-DECOY", dec == "deny", "another program carrying the status words is judged (H2)")

        # H1a: a forged local lease (same goal + since, an enormous amount) is not the authority.
        since = ms.read_index()["gg"]["since"]
        forged = {"goal": "gg", "since": since, "files": {}, "ids": [], "tokens": 0, "context": 0, "closeout": 0,
                  "lease": {"id": "gg:bound-7:1", "amount": 10 ** 15, "base": 0}}
        (e.state / "session-budget-bound-7.goal.json").write_text(json.dumps(forged), encoding="utf-8")
        dec, why = run_guard(e, "bound-7", tx, work, tool="Bash", tool_input={"command": "python big_job.py"})
        check("V-GOAL-GUARD-FORGED-LEASE", dec == "deny" and "budget_spent" in why,
              f"a lease the journal never issued forces a renew, which refuses: {why[:80]}")
        dec, why = run_guard(e, "bound-8", tx, work, tool="Write",
                             tool_input={"file_path": str(e.state / "session-budget-bound-8.goal.json"), "content": "{}"})
        dec2, _ = run_guard(e, "bound-8", tx, work, tool="Bash", tool_input={
            "command": "python tools/mission_spend.py goal-declare --goal gg --cap 999999999 --source x"})
        check("V-GOAL-GUARD-SELF-STATE-PROTECTED", dec == "deny" and dec2 == "deny",
              "writing its own guard state, or goal-declare from a bound session, is judged as goal state")
        dec, _ = run_guard(e, "bound-1", tx, work, tool="Bash",
                           tool_input={"command": "echo mission_spend.py goal-status; python big_job.py"})
        check("V-GOAL-GUARD-EXEMPT-NARROW", dec == "deny", "a command that only MENTIONS it is still judged")
        dec, why = run_guard(e, "bound-2", tx, work, tool="Bash",
                             tool_input={"command": f"Remove-Item {e.state}\\goal-budget\\index.json"})
        check("V-GOAL-GUARD-STATE-PROTECTED", dec == "deny" and "goal-budget" in why, why[:90])

        declare("gg2", 100_000, lease_calls=1)
        dec, _ = run_guard(e, "bound-3", tx, other, tool="Agent", tool_input={"prompt": "x"}, CPP_GOAL="gg2")
        check("V-GOAL-GUARD-AGENT-CONTROL", dec is None, "CPP_GOAL binding with room: the Agent is admitted")

        dec, why = run_guard(e, "bound-4", tx, other, CPP_GOAL="never-declared")
        check("V-GOAL-GUARD-UNKNOWN-GOAL", dec == "deny" and "UNKNOWN" in why, why[:90])
        dec, why = run_guard(e, "bound-5", tx, other, CPP_GOAL="gg2", PYTHON_BIN=str(e.root / "no-python.exe"))
        check("V-GOAL-GUARD-RENEW-FAILS-CLOSED", dec == "deny" and "UNKNOWN" in why, why[:90])
        dec, _ = run_guard(e, "unbound-2", tx, other, PYTHON_BIN=str(e.root / "no-python.exe"))
        check("V-GOAL-GUARD-FAIL-CLOSED-CONTROL", dec is None, "an unbound session never calls python")
        dec, _ = run_guard(e, "bound-6", tx, work, CPP_SESSION_BUDGET="off")
        check("V-GOAL-GUARD-KILL-SWITCH", dec is None, "CPP_SESSION_BUDGET=off disables goal mode too")
    finally:
        e.close()


def g_dispatch_wiring():
    text = DISPATCHER.read_text(encoding="utf-8")
    check("V-GOAL-AGENT-LANE",
          "'PreToolUse-Agent-default': ['../skills/claude-power-pack/hooks/session_budget_guard.js']" in text
          and "tools: ['Agent', 'Task'], chain: 'PreToolUse-Agent-default'" in text,
          "dispatcher carries the Agent lane and its no-event route")


def main():
    for g in (g_cap_journal, g_race, g_settle_and_resume, g_cross_account, g_crash_and_leak, g_spawn,
              g_headroom, g_raise, g_host_and_roots, g_review_fixes, g_guard, g_dispatch_wiring):
        try:
            g()
        except Exception as ex:   # a crashed gate is a FAIL with its reason, never a skipped one
            check(f"V-GOAL-{g.__name__}", False, f"crashed: {type(ex).__name__}: {ex}")
    print(f"GOAL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
