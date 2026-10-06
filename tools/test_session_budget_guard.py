"""V-SBG-* gates: the SESSION cost breaker (hooks/session_budget_guard.js).

Origin: the skyparty-spawn closeout (transcript b9dbdfe2, 2026-10-05) ran 131 calls to 35.45M
processed tokens in an ordinary interactive session; tools/mission_spend.py only judged missions.
The guard enforces a declared session envelope on PreToolUse with mission_spend's unit, reading the
transcript incrementally. These gates pin: parity with the Python reference, incremental equality,
every breaker red AND green, the one-grace rule, the rotation exemption, the kill switch, a
positive control on a REAL transcript, latency, and the wiring in both dispatchers (canonical and
live) with one end-to-end deny through the live dispatcher.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
import mission_spend as ms  # noqa: E402

GUARD = Path(os.environ.get("SBG_DRILL_GUARD") or PP / "hooks" / "session_budget_guard.js")   # drill: a mutated copy
LIVE_DISPATCHER = Path.home() / ".claude" / "hooks" / "hook-dispatcher.js"
DISPATCHERS = [PP / "hooks" / "hook-dispatcher.js", LIVE_DISPATCHER]
NODE = shutil.which("node") or "node"
SID = "sbg-test-0001"

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


RUNNER = r"""
const g = require(process.argv[1]);
let raw = ''; process.stdin.on('data', d => raw += d).on('end', () => {
  const ev = JSON.parse(raw); const t0 = process.hrtime.bigint();
  const out = g.decide(ev); const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  process.stdout.write(JSON.stringify({ out, ms }));
});
"""


def row(mid, usage=None, tools=(), ts="2026-10-05T10:00:00.000Z", model="claude-opus-5-5", typ="assistant"):
    content = [{"type": "tool_use", "name": n, "input": inp} for n, inp in tools] or [{"type": "text", "text": "x"}]
    m = {"id": mid, "model": model, "content": content}
    if usage is not None:
        m["usage"] = usage
    return json.dumps({"type": typ, "timestamp": ts, "uuid": "u-" + mid, "message": m}) + "\n"


def U(i, cw=0, cr=0, o=0):
    return {"input_tokens": i, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr, "output_tokens": o}


class Box:
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="sbg_"))
        self.state = self.root / "state"
        self.state.mkdir()
        self.tx = self.root / "t.jsonl"
        self.tx.write_text("", encoding="utf-8")

    def env(self, **extra):
        e = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(self.state))
        e.pop("CPP_SESSION_BUDGET", None)
        e.update(extra)
        return e

    def declare(self, **kw):
        old = os.environ.get("GSD_LONG_RUN_STATE_DIR")
        os.environ["GSD_LONG_RUN_STATE_DIR"] = str(self.state)
        try:
            args = dict(target=1000, warn=2000, stop=3000)
            args.update(kw)
            return ms.declare(SID, **args)
        finally:
            if old is None:
                os.environ.pop("GSD_LONG_RUN_STATE_DIR")
            else:
                os.environ["GSD_LONG_RUN_STATE_DIR"] = old

    def append(self, text):
        with open(self.tx, "a", encoding="utf-8") as fh:
            fh.write(text)

    def call(self, cmd="echo hi", tx=True, tool="Bash", inp=None, **env):
        ev = {"session_id": SID, "tool_name": tool, "tool_input": inp if inp is not None else {"command": cmd}}
        if tx:
            ev["transcript_path"] = str(self.tx)
        p = subprocess.run([NODE, "-e", RUNNER, str(GUARD)], input=json.dumps(ev), capture_output=True,
                           text=True, env=self.env(**env), timeout=60)
        if p.returncode != 0:
            return {"out": "CRASH:" + p.stderr[-300:], "ms": -1}
        return json.loads(p.stdout)

    def st(self):
        return json.loads((self.state / f"session-budget-{SID}.state.json").read_text(encoding="utf-8"))


def kind(out):
    if out is None:
        return "allow"
    if isinstance(out, str):
        return out
    h = out.get("hookSpecificOutput") or {}
    if h.get("permissionDecision") == "deny":
        return "deny"
    return "advise" if h.get("additionalContext") else "other"


def main():
    # V-SBG-INERT: no budget file -> null, and cheap
    b = Box()
    r = b.call()
    check("V-SBG-INERT", kind(r["out"]) == "allow" and not any(b.state.iterdir()), f"no envelope -> allow, {r['ms']:.2f} ms, no state written")

    # V-SBG-PARITY: dup ids, synthetic row, since filter, tool_use, user rows
    b = Box()
    b.append(row("old", U(999), ts="2026-10-05T08:00:00.000Z", tools=[("Bash", {"command": "x"})]))
    b.append(row("m1", U(10, 20, 30, 5), tools=[("Read", {"file_path": "a"})]))
    b.append(row("m1", U(10, 20, 30, 5), tools=[("Bash", {"command": "ls"})]))   # same message, second block
    b.append(row("syn", U(777), model="<synthetic>"))
    b.append(row("m2", U(1, 2, 300, 7), tools=[("Edit", {"file_path": "a"})]))
    b.append(json.dumps({"type": "user", "timestamp": "2026-10-05T10:00:01Z", "message": {"role": "user", "content": "hi"}}) + "\n")
    since = "2026-10-05T09:00:00"
    b.declare(since_iso=since)
    py = ms.session_tokens(b.tx, since)
    ref = ms._file_tokens(b.tx, since)
    r = b.call()
    s = b.st()
    check("V-SBG-PARITY", (s["tokens"], s["calls"], s["context"]) == (py["tokens"], py["calls"], py["context"]) and py["tokens"] == ref == 375,
          f"js={s['tokens']}/{s['calls']}/{s['context']} py={py} _file_tokens={ref} (expected 375 tokens, 3 calls, ctx 303)")

    # V-SBG-INCREMENTAL: a partial trailing line is not consumed; totals equal a full read
    b = Box()
    b.declare()
    full = row("a", U(100)) + row("b", U(200), tools=[("Write", {})]) + row("c", U(300))
    cut = len(full) - 40
    b.append(full[:cut])
    b.call()
    mid = b.st()["tokens"]
    b.append(full[cut:])
    b.call()
    check("V-SBG-INCREMENTAL", mid == 300 and b.st()["tokens"] == 600 == ms.session_tokens(b.tx)["tokens"],
          f"after partial write {mid}, after completion {b.st()['tokens']}, offset {b.st()['offset']}")

    # V-SBG-TOKENS red / warn / green
    b = Box(); b.declare(); b.append(row("a", U(500, o=1)))
    g = kind(b.call()["out"])
    b.append(row("b", U(1600)))
    w = kind(b.call()["out"])
    b.append(row("c", U(1000)))
    d = b.call()["out"]
    check("V-SBG-TOKENS", (g, w, kind(d)) == ("allow", "advise", "deny") and "stop 3,000" in d["hookSpecificOutput"]["permissionDecisionReason"],
          f"501 -> {g}, 2101 -> {w}, 3101 -> {kind(d)}")

    # V-SBG-DIVERGENCE: 4 calls vs estimate 2 x 1.5 = 3
    b = Box(); b.declare(calls_estimate=2)
    b.append(row("a", U(1), tools=[("Edit", {})] * 3))
    g = kind(b.call()["out"])
    b.append(row("b", U(1), tools=[("Edit", {})]))
    d = kind(b.call()["out"])
    check("V-SBG-DIVERGENCE", (g, d) == ("allow", "deny"), f"3 calls -> {g}, 4 calls -> {d}")

    # V-SBG-CONTEXT
    b = Box(); b.declare(target=10**9, warn=10**9, stop=10**9, context_ceiling=50000)
    b.append(row("a", U(10, 0, 40000)))
    g = kind(b.call()["out"])
    b.append(row("b", U(10, 0, 60000)))
    d = kind(b.call()["out"])
    check("V-SBG-CONTEXT", (g, d) == ("allow", "deny"), f"ctx 40010 -> {g}, 60010 -> {d}")

    # V-SBG-NOPROGRESS: K=3; reads only trip, an Edit or a commit resets
    b = Box(); b.declare(noprogress_calls=3)
    b.append(row("a", U(1), tools=[("Read", {})] * 3))
    g = kind(b.call()["out"])
    b.append(row("b", U(1), tools=[("Grep", {})]))
    d = kind(b.call()["out"])
    b.append(row("c", U(1), tools=[("PowerShell", {"command": "git commit -F m -- x"})]))
    reset = kind(b.call()["out"])
    check("V-SBG-NOPROGRESS", (g, d, reset) == ("allow", "deny", "allow"), f"3 reads -> {g}, 4 -> {d}, after commit -> {reset}")

    # V-SBG-GRACE: no transcript_path -> one advisory, then deny; readable again -> allow
    b = Box(); b.declare()
    first, second = kind(b.call(tx=False)["out"]), kind(b.call(tx=False)["out"])
    back = kind(b.call()["out"])
    check("V-SBG-GRACE", (first, second, back) == ("advise", "deny", "allow"), f"{first} -> {second} -> recovered {back}")

    # V-SBG-CORRUPT-BUDGET: same rule for an unreadable envelope
    b = Box(); b.declare()
    (b.state / f"session-budget-{SID}.json").write_text("{not json", encoding="utf-8")
    seq = (kind(b.call()["out"]), kind(b.call()["out"]))
    check("V-SBG-CORRUPT-BUDGET", seq == ("advise", "deny"), f"{seq}")

    # V-SBG-EXEMPT + V-SBG-KILL: tripped session can still rotate / be switched off
    b = Box(); b.declare(); b.append(row("a", U(5000)))
    tripped = kind(b.call()["out"])
    ex = kind(b.call(cmd="python rollover.py seal")["out"])
    kill = kind(b.call(CPP_SESSION_BUDGET="off")["out"])
    check("V-SBG-EXEMPT", (tripped, ex) == ("deny", "allow"), f"over stop -> {tripped}; rollover.py -> {ex}")
    check("V-SBG-KILL", kill == "allow", f"CPP_SESSION_BUDGET=off -> {kill}")

    # V-SBG-CHECKPOINT-*: envelope = 20 calls x 1.5 = 30; reserve 6 (capped at a quarter = 7)
    def reads(n):
        return row(f"r{time.monotonic_ns()}", U(1), tools=[("Read", {})] * n)

    def reason(o):
        return ((o or {}).get("hookSpecificOutput") or {}).get("permissionDecisionReason") or ""

    COMMIT = 'git commit -m "wip <noreply@example.com>" -- a.txt'
    PS_GIT = "& 'C:\\Program Files\\Git\\cmd\\git.exe' -C C:\\repo status"
    # post-ceiling (31 calls > 30)
    b = Box(); b.declare(calls_estimate=20); b.append(reads(31))
    c1 = b.call(COMMIT)
    c1b = b.call(tool="PowerShell", cmd=PS_GIT)
    c1c = b.call("git add -A && git commit -F m.txt; git status")
    check("V-SBG-CHECKPOINT-POST-CEILING-COMMIT", all(kind(c["out"]) == "advise" and "CHECKPOINT MODE" in ((c["out"].get("hookSpecificOutput") or {}).get("additionalContext") or "") for c in (c1, c1b, c1c)),
          f"git commit / PS git status / chain -> {kind(c1['out'])},{kind(c1b['out'])},{kind(c1c['out'])}")
    c2 = b.call(tool="Edit", inp={"file_path": "C:/repo/src/app.js"})
    check("V-SBG-CHECKPOINT-POST-CEILING-SOURCE-DENIED", kind(c2["out"]) == "deny" and "CHECKPOINT MODE" in reason(c2["out"]) and "RESUMPTION" in reason(c2["out"]) and "git commit" in reason(c2["out"]),
          f"Edit src/app.js -> {kind(c2['out'])}; text lists the allowed set")
    c3 = [b.call(tool=t, inp={"file_path": p}) for t, p in (("Edit", "C:\\repo\\RESUMPTION.md"), ("Write", "/r/RESUMPTION_M2.md"), ("Write", "/r/TOKENS.md"))]
    check("V-SBG-CHECKPOINT-POST-CEILING-RESUMPTION", all(kind(c["out"]) == "advise" for c in c3), f"{[kind(c['out']) for c in c3]}")
    check("V-SBG-CHECKPOINT-READ-AND-OTHER-BASH-DENIED", all(kind(c["out"]) == "deny" for c in (
        b.call(tool="Read", inp={"file_path": "a"}), b.call("npm test"), b.call("git status | cat"), b.call("git status; rm -rf x"),
        b.call("git commit -m x > out.txt"), b.call('git commit -m "$(rm x)"'), b.call("git push"), b.call("git reset --hard"))),
          "Read, npm, piped/chained/redirected/substituted git, push and reset are all denied in the window")
    # declared checkpoint_paths admit their file and only theirs
    b = Box(); b.declare(calls_estimate=20); b.append(reads(31))
    bp = b.state / f"session-budget-{SID}.json"
    j = json.loads(bp.read_text(encoding="utf-8")); j["checkpoint_paths"] = ["vault/handoffs/h.md"]; bp.write_text(json.dumps(j), encoding="utf-8")
    p_ok, p_no = b.call(tool="Write", inp={"file_path": "C:/r/vault/handoffs/h.md"}), b.call(tool="Write", inp={"file_path": "C:/r/vault/handoffs/other.md"})
    check("V-SBG-CHECKPOINT-DECLARED-PATH", kind(p_ok["out"]) == "advise" and kind(p_no["out"]) == "deny", f"declared -> {kind(p_ok['out'])}, other -> {kind(p_no['out'])}")
    # approaching the ceiling: 25 calls (5 remain) is already checkpoint; 10 calls is ordinary
    b = Box(); b.declare(calls_estimate=20); b.append(reads(25))
    pre_src, pre_git = b.call(tool="Edit", inp={"file_path": "C:/r/src/a.js"}), b.call(COMMIT)
    b = Box(); b.declare(calls_estimate=20); b.append(reads(10))
    early = b.call(tool="Edit", inp={"file_path": "C:/r/src/a.js"})
    check("V-SBG-CHECKPOINT-PRE-CEILING", (kind(pre_src["out"]), kind(pre_git["out"]), kind(early["out"])) == ("deny", "advise", "allow"),
          f"5 remain: src {kind(pre_src['out'])}, commit {kind(pre_git['out'])}; 20 remain: src {kind(early['out'])}")
    # beyond the reserve (ceiling passed by >= 6 calls): everything denied, with the ordinary breaker text
    b = Box(); b.declare(calls_estimate=20); b.append(reads(31))
    b.call(COMMIT)                      # first over-ceiling look pins over_at = 31
    b.append(reads(6))
    far = [b.call(COMMIT), b.call(tool="Edit", inp={"file_path": "C:/r/RESUMPTION.md"}), b.call(tool="Edit", inp={"file_path": "C:/r/src/a.js"})]
    check("V-SBG-CHECKPOINT-BEYOND-RESERVE-ALL-DENIED", all(kind(c["out"]) == "deny" and "CHECKPOINT MODE" not in reason(c["out"]) and "SESSION BUDGET BREAKER" in reason(c["out"]) for c in far),
          f"{[kind(c['out']) for c in far]}")
    # reserve 0 in the budget file turns the mode off: the ordinary deny for a commit
    b = Box(); b.declare(calls_estimate=20); b.append(reads(31))
    j = json.loads((b.state / f"session-budget-{SID}.json").read_text(encoding="utf-8")); j["checkpoint_reserve"] = 0
    (b.state / f"session-budget-{SID}.json").write_text(json.dumps(j), encoding="utf-8")
    off = b.call(COMMIT)
    check("V-SBG-CHECKPOINT-RESERVE-ZERO-OFF", kind(off["out"]) == "deny" and "CHECKPOINT MODE" not in reason(off["out"]), f"{kind(off['out'])}")

    # V-SBG-REAL-PARITY (positive control): the largest real transcript on this host
    proj = ms.projects_root()
    real = max((p for p in proj.glob("*/*.jsonl")), key=lambda p: p.stat().st_size, default=None) if proj.is_dir() else None
    if real is None:
        check("V-SBG-REAL-PARITY", False, "no real transcript found: the control could not run")
    else:
        b = Box(); b.declare(target=10**12, warn=10**12, stop=10**12, noprogress_calls=10**9)
        snap = b.root / "real.jsonl"
        shutil.copyfile(real, snap)
        b.tx = snap
        r = b.call()
        s = b.st()
        py = ms.session_tokens(snap)
        check("V-SBG-REAL-PARITY", s["tokens"] == py["tokens"] == ms._file_tokens(snap, None) and s["calls"] == py["calls"] and py["tokens"] > 0,
              f"{snap.stat().st_size/1e6:.1f} MB: js {s['tokens']:,}/{s['calls']} py {py['tokens']:,}/{py['calls']}; first full read {r['ms']:.0f} ms")
        b.append(row("zz-new", U(1)))
        r2 = b.call()
        check("V-SBG-LATENCY", 0 <= r2["ms"] < 50, f"incremental call after one appended line: {r2['ms']:.2f} ms (< 50)")

    # V-SBG-WIRED: canonical and live dispatchers list the guard on all three PreToolUse lanes
    for d in DISPATCHERS:
        txt = d.read_text(encoding="utf-8") if d.exists() else ""
        n = sum(1 for lane in ("Bash", "Edit", "Read")
                if f"'PreToolUse-{lane}-default': [" in txt and "session_budget_guard.js" in txt.split(f"'PreToolUse-{lane}-default': [", 1)[1].split("\n", 1)[0])
        check("V-SBG-WIRED", n == 3, f"{d}: {n}/3 lanes")

    # V-SBG-E2E: through the LIVE dispatcher, a tripped envelope denies a real Bash-chain event
    b = Box(); b.declare(); b.append(row("a", U(5000)))
    ev = {"session_id": SID, "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "echo hi"},
          "transcript_path": str(b.tx), "cwd": str(b.root)}
    p = subprocess.run([NODE, str(LIVE_DISPATCHER), "--event=PreToolUse-Bash-chain"], input=json.dumps(ev),
                       capture_output=True, text=True, env=b.env(), timeout=120)
    try:
        hso = json.loads(p.stdout or "{}").get("hookSpecificOutput") or {}
    except ValueError:
        hso = {}
    check("V-SBG-E2E", hso.get("permissionDecision") == "deny" and "SESSION BUDGET BREAKER" in (hso.get("permissionDecisionReason") or ""),
          f"live dispatcher -> {hso.get('permissionDecision')!r}")

    print(f"SBG_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
