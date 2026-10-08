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
    won, mute, used = _race(100)
    check("V-GOAL-RACE-LAST", won == 1 and mute == 0 and used == 100,
          f"5 processes race a 100 cap with 100 leases: {won} admitted, {mute} unanswered, used {used}")
    won, mute, used = _race(500)
    check("V-GOAL-RACE-CONTROL", won == 5 and mute == 0 and used == 500, f"same race at cap 500: {won} admitted")


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
        declare("acct", 300, lease_calls=1)
        a = ms.goal_renew("acct", "account-A-sid", 250, 50, HOST)
        b = ms.goal_renew("acct", "account-B-sid", 0, 50, HOST)
        check("V-GOAL-CROSS-ACCOUNT", a["ok"] and not b["ok"],
              f"A settles 250 + lease 50 = cap; B (other account, same goal) -> {b.get('reason')}")
        declare("acct2", 300, lease_calls=1)
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
        ms.goal_renew("sp", "p", 900, 50, HOST)        # used 950, remaining 50
        r = ms.goal_spawn("sp", "p", 100, 0, HOST)
        check("V-GOAL-SPAWN-OVER-REMAINING", not r["ok"], f"Agent estimate 100 vs remaining 50: {r['reason']}")
        r = ms.goal_spawn("sp", "p", 40, 0, HOST)
        check("V-GOAL-SPAWN-CONTROL", r["ok"], "estimate 40 fits and is reserved")
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
        declare("gg", 1000, roots=[str(work)], lease_calls=1)
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


# --- R1 (goal ce-a3b-r): canonical goal-state authorization + scoped Owner grants -------------------

def _short83(p: Path):
    """The 8.3 alias of an existing path, or None when the volume has none."""
    if sys.platform != "win32":
        return None
    import ctypes
    buf = ctypes.create_unicode_buffer(1024)
    n = ctypes.windll.kernel32.GetShortPathNameW(str(p), buf, 1024)
    s = buf.value if 0 < n < 1024 else None
    return s if s and s.lower() != str(p).lower() else None


def _junction(link: Path, target: Path) -> bool:
    if sys.platform != "win32":
        try:
            os.symlink(target, link, target_is_directory=True)
            return True
        except OSError:
            return False
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, text=True)
    return r.returncode == 0 and link.exists()


def g_canon():
    e = Env()
    try:
        work = e.root / "work"
        (work / "specs").mkdir(parents=True)
        declare("gc", 10_000_000, roots=[str(work)], lease_calls=1)
        tx = e.root / "t.jsonl"
        tx.write_text(row("m1", 100), encoding="utf-8")
        spec = work / "specs" / "goal-budget-admission.md"
        spec.write_text("# a read-only spec that merely carries the words in its name\n", encoding="utf-8")
        dec, why = run_guard(e, "cn-1", tx, work, tool_input={"file_path": str(spec)})
        check("V-GOAL-CANON-SPEC-READABLE", dec is None,
              f"a spec NAMED goal-budget-*.md outside the state dir is admitted: {dec} {why[:80]}")
        dec, why = run_guard(e, "cn-1", tx, work, tool="Grep", tool_input={"pattern": "x", "path": str(spec.parent)})
        check("V-GOAL-CANON-SPEC-GREPPABLE", dec is None, f"grep over the spec dir is admitted: {dec} {why[:80]}")

        led = e.state / "goal-budget" / "gc" / "spend.journal.jsonl"
        check("V-GOAL-CANON-LEDGER-EXISTS", led.exists(), f"the control target exists: {led.name}")
        aliases = {
            "absolute": (work, str(led)),
            "relative": (e.state, "goal-budget/gc/spend.journal.jsonl"),
            "dotdot": (work, str(e.state / "goal-budget" / "gc" / ".." / "gc" / "spend.journal.jsonl")),
            "dotdot-out": (work, str(work / ".." / "state" / "goal-budget" / "gc" / "spend.journal.jsonl")),
            "mixed-case": (work, str(led).replace("goal-budget", "GoAl-BuDgEt")),
            "forward-slash": (work, str(led).replace("\\", "/")),
            "trailing-sep": (work, str(led.parent) + os.sep),
            "dir-itself": (work, str(e.state / "goal-budget")),
        }
        short = _short83(e.state / "goal-budget")
        if short:
            aliases["8.3-short"] = (work, str(Path(short) / "gc" / "spend.journal.jsonl"))
        jn = e.root / "innocent"
        if _junction(jn, e.state / "goal-budget"):
            aliases["junction"] = (work, str(jn / "gc" / "spend.journal.jsonl"))
        bad = []
        for name, (cwd, fp) in aliases.items():
            dec, why = run_guard(e, "cn-2", tx, cwd, tool_input={"file_path": fp})
            if dec != "deny":
                bad.append(name)
        check("V-GOAL-CANON-STATE-DENIED", not bad,
              f"the ledger and {len(aliases) - 1} aliases ({', '.join(aliases)}) all denied; admitted: {bad or 'none'}")
        sess = e.state / "session-budget-cn-3.json"
        sess.write_text("{}", encoding="utf-8")
        dec, _ = run_guard(e, "cn-3", tx, work, tool="Edit", tool_input={"file_path": str(sess), "old_string": "a", "new_string": "b"})
        dec2, _ = run_guard(e, "cn-3", tx, work, tool="Write", tool_input={"file_path": str(e.state / "goal-budget" / "gc" / "x"), "content": "y"})
        check("V-GOAL-CANON-WRITES-DENIED", dec == "deny" and dec2 == "deny", f"Edit {dec}, Write {dec2} on protected state")
        dec, _ = run_guard(e, "cn-3", tx, work, tool="Bash", tool_input={"command": f"cat '{str(led).replace(chr(92), '/')}'"})
        check("V-GOAL-CANON-SHELL-PATH-DENIED", dec == "deny", "a shell command naming the ledger by a path token is denied")
        dec, _ = run_guard(e, "cn-3", tx, work, tool="Bash", tool_input={"command": "python tools/mission_spend.py goal-grant --goal gc --session cn-3 --op read --path x"})
        dec2, _ = run_guard(e, "cn-3", tx, work, tool="Bash", tool_input={"command": "python tools/mission_spend.py goal-revoke --id g"})
        check("V-GOAL-CANON-SHELL-VERBS-DENIED", dec == "deny" and dec2 == "deny", f"goal-grant {dec}, goal-revoke {dec2} from a bound shell")
        dec, _ = run_guard(e, "cn-3", tx, work, tool="Bash", tool_input={"command": "echo hello"})
        check("V-GOAL-CANON-SHELL-CONTROL", dec is None, "an unrelated shell command is admitted")
    finally:
        e.close()


def _grant(*a, **k):
    try:
        return ms.goal_grant(*a, **k)
    except AttributeError:
        return {"ok": False, "reason": "goal_grant is not implemented"}


def _journal_ops(e, goal, op):
    p = e.state / "goal-budget" / goal / "spend.journal.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip() and json.loads(x).get("op") == op]


def g_grant():
    import time
    e = Env()
    try:
        work = e.root / "work"
        work.mkdir()
        declare("gt", 10_000_000, roots=[str(work)], lease_calls=1)
        tx = e.root / "t.jsonl"
        tx.write_text(row("m1", 100), encoding="utf-8")
        prot = e.state / "goal-budget" / "notes.txt"
        prot.write_text("owner-approved read", encoding="utf-8")
        rd = {"file_path": str(prot)}

        dec, _ = run_guard(e, "gr-0", tx, work, tool_input=rd)
        check("V-GOAL-GRANT-CONTROL", dec == "deny", "no grant: the protected read is denied")
        r = _grant("gt", "gr-1", "read", str(prot), owner=False)
        check("V-GOAL-GRANT-NEEDS-OWNER", not r.get("ok"), f"a grant without --owner is refused: {str(r.get('reason'))[:60]}")

        r = _grant("gt", "gr-1", "read", str(prot), count=1, ttl_min=60, owner=True)
        check("V-GOAL-GRANT-ISSUED", bool(r.get("ok")) and len(_journal_ops(e, "gt", "grant")) == 1 if r.get("ok") else False,
              f"Owner grant recorded in the journal: {r.get('ok')} {str(r.get('reason', ''))[:50]}")
        dec1, w1 = run_guard(e, "gr-1", tx, work, tool_input=rd)
        dec2, w2 = run_guard(e, "gr-1", tx, work, tool_input=rd)
        check("V-GOAL-GRANT-EXACT", dec1 is None and dec2 == "deny" and len(_journal_ops(e, "gt", "grant_use")) == 1,
              f"first read {dec1}, second read {dec2} (count 1); grant_use rows {len(_journal_ops(e, 'gt', 'grant_use')) if (e.state / 'goal-budget' / 'gt').exists() else 0}")

        _grant("gt", "gr-2", "read", str(prot), count=1, ttl_min=60, owner=True, now=time.time() - 7200)
        dec, _ = run_guard(e, "gr-2", tx, work, tool_input=rd)
        check("V-GOAL-GRANT-EXPIRED", dec == "deny", f"an expired grant is denied: {dec}")

        _grant("gt", "gr-3", "read", str(prot), count=1, ttl_min=60, owner=True)
        dec, _ = run_guard(e, "gr-4", tx, work, tool_input=rd)
        check("V-GOAL-GRANT-OTHER-SID", dec == "deny", f"another session cannot use it: {dec}")

        other = e.state / "goal-budget" / "other.txt"
        other.write_text("a", encoding="utf-8")
        _grant("gt", "gr-5", "read", str(other), count=1, ttl_min=60, owner=True)
        other.write_text("changed after the grant", encoding="utf-8")
        dec, _ = run_guard(e, "gr-5", tx, work, tool_input={"file_path": str(other)})
        check("V-GOAL-GRANT-SHA-CHANGED", dec == "deny", f"a changed sha256 voids the grant: {dec}")

        _grant("gt", "gr-6", "read", str(prot), count=5, ttl_min=60, owner=True)
        dec, _ = run_guard(e, "gr-6", tx, work, tool="Edit", tool_input={"file_path": str(prot), "old_string": "a", "new_string": "b"})
        dec2, _ = run_guard(e, "gr-6", tx, work, tool="Write", tool_input={"file_path": str(prot), "content": "z"})
        check("V-GOAL-GRANT-NEVER-WRITES", dec == "deny" and dec2 == "deny", f"read grant: Edit {dec}, Write {dec2}")
        dec3, _ = run_guard(e, "gr-6", tx, work, tool_input=rd)
        check("V-GOAL-GRANT-SAME-CONTROL", dec3 is None, f"the same grant still admits its Read: {dec3}")

        _grant("gt", "gr-7", "read", str(prot), count=5, ttl_min=60, owner=True)
        dec, _ = run_guard(e, "gr-7", tx, work, tool_input=rd, CPP_GOAL_GRANTS="0")
        check("V-GOAL-GRANT-SWITCH-OFF", dec == "deny", f"CPP_GOAL_GRANTS=0 ignores grants: {dec}")

        gid = (_journal_ops(e, "gt", "grant") or [{}])[-1].get("id")
        rv = ms.goal_revoke("gt", gid) if hasattr(ms, "goal_revoke") and gid else {"ok": False}
        _grant("gt", "gr-8", "read", str(prot), count=5, ttl_min=60, owner=True)
        g8 = [g for g in _journal_ops(e, "gt", "grant") if g.get("sid") == "gr-8"]
        rv = ms.goal_revoke("gt", g8[0]["id"]) if hasattr(ms, "goal_revoke") and g8 else {"ok": False}
        dec, _ = run_guard(e, "gr-8", tx, work, tool_input=rd)
        check("V-GOAL-GRANT-REVOKED", bool(rv.get("ok")) and dec == "deny", f"a revoked grant is denied: revoke {rv.get('ok')}, read {dec}")
    finally:
        e.close()


def g_refusal_no_closeout_read():
    e = Env()
    try:
        work = e.root / "work2"
        work.mkdir()
        declare("gx", 1000, roots=[str(work)], lease_calls=1)
        tx = e.root / "t.jsonl"
        tx.write_text(row("m1", 100), encoding="utf-8")
        run_guard(e, "rf-1", tx, work)
        with open(tx, "a", encoding="utf-8") as fh:
            fh.write(row("m2", 2000))
        decs = [run_guard(e, "rf-1", tx, work)[0] for _ in range(5)]
        check("V-GOAL-REFUSAL-NO-CLOSEOUT-READ", all(d == "deny" for d in decs),
              f"pins 19240f98: five Reads after a goal refusal -> {decs}")
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
              g_raise, g_host_and_roots, g_review_fixes, g_guard, g_canon, g_grant,
              g_refusal_no_closeout_read, g_dispatch_wiring):
        try:
            g()
        except Exception as ex:   # a crashed gate is a FAIL with its reason, never a skipped one
            check(f"V-GOAL-{g.__name__}", False, f"crashed: {type(ex).__name__}: {ex}")
    print(f"GOAL_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
