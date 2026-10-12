"""CDC C4 gates: semantic breaker (hooks/semantic_breaker.js) + calibration (tools/semantic_breaker.py).

Red branches: 30 progress-free calls trip (incident, autopsy, deny budget, next call refused). Controls: commits
reset, edits reset, HEAD move resets, red->green resets, kill switch, unbound session, closeout write admitted.
Mutation drill: each predicate disabled in a throwaway copy of the hook must turn its test RED.
Every hook call is a synchronous node subprocess (nothing detached), so there is nothing to await.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
sys.path.insert(0, str(HERE))
import semantic_breaker as sb  # noqa: E402

HOOK = PP / "hooks" / "semantic_breaker.js"
NODE = os.environ.get("NODE_BIN") or "node"
GIT = os.environ.get("GIT_BIN") or next((p for p in (r"C:\Program Files\Git\cmd\git.exe", "git") if p == "git" or os.path.exists(p)))
passes = fails = 0
T = 8   # test threshold via CPP_SEM_BREAKER_CALLS (the 25 default is exercised once, below)


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


DRIVER = (
    "const m=require(process.argv[1]);const rl=require('readline').createInterface({input:process.stdin});"
    "rl.on('line',async l=>{const q=JSON.parse(l);for(const k of ['CPP_SEM_BREAKER','CPP_SEM_BREAKER_CALLS','CPP_GOAL','CPP_COG_ROUTE'])delete process.env[k];"
    "Object.assign(process.env,q.env);let o=null;try{o=await m.run(q.event);}catch(e){o={_err:String(e)};}"
    "process.stdout.write(JSON.stringify(o||{})+String.fromCharCode(10));});"
)
_drivers = {}


def _driver(hook):
    """One long-lived node per hook file: this host cold-starts node in 3-8 s, so a process per call is not testable.
    Each call writes a request line and blocks on the reply line, so every effect is awaited."""
    k = str(hook)
    if k not in _drivers:
        _drivers[k] = subprocess.Popen([NODE, "-e", DRIVER, str(hook)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       text=True, bufsize=1)
    return _drivers[k]


def close_drivers():
    for d in _drivers.values():
        d.stdin.close()
        d.wait(timeout=30)
    _drivers.clear()


def call(state, sid, tool, tin=None, resp="", pre=False, hook=HOOK, env=None, cwd=None, transcript=None, bound=True):
    e = {"GSD_LONG_RUN_STATE_DIR": str(state), "CPP_SEM_BREAKER_CALLS": str(T)}
    if bound:
        e["CPP_GOAL"] = "g-c4"
    e.update(env or {})
    ev = {"session_id": sid, "hook_event_name": "PreToolUse" if pre else "PostToolUse", "tool_name": tool,
          "tool_input": tin or {}, "cwd": str(cwd or state)}
    if not pre:
        ev["tool_response"] = resp
    if transcript:
        ev["transcript_path"] = str(transcript)
    d = _driver(hook)
    d.stdin.write(json.dumps({"env": e, "event": ev}) + "\n")
    d.stdin.flush()
    out = json.loads(d.stdout.readline() or "{}")
    h = out.get("hookSpecificOutput", {})
    return h.get("permissionDecision") == "deny", h.get("permissionDecisionReason", "")


def incidents(state, sid):
    d = Path(state) / "token-incidents"
    return sorted(d.glob(f"*-{sid}.json")) if d.is_dir() else []


def tripped(state, sid):
    p = Path(state) / "semantic-breaker" / f"{sid}.json"
    return bool(p.exists() and json.loads(p.read_text(encoding="utf-8")).get("tripped"))


def mk_transcript(tmp):
    t = Path(tmp) / "t.jsonl"
    rows = [{"type": "user", "message": {"role": "user", "content": "do it"}},
            {"type": "assistant", "requestId": "r1", "message": {"id": "m1", "model": "x", "role": "assistant",
             "usage": {"input_tokens": 10, "cache_read_input_tokens": 1000, "output_tokens": 5},
             "content": [{"type": "tool_use", "id": "u1", "name": "Read", "input": {"file_path": "a.py"}}]}}]
    t.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return t


def loop(state, sid, n, hook=HOOK, **kw):
    for i in range(n):
        call(state, sid, "Read", {"file_path": f"f{i}.py"}, hook=hook, **kw)


def scenarios(hook, groups=None):
    """Returns {gate: bool}; used live and (one group at a time) against mutants."""
    want = lambda g: groups is None or g in groups
    res = {}
    with tempfile.TemporaryDirectory() as tmp:
        st = Path(tmp) / "state"
        st.mkdir()
        tr = mk_transcript(tmp)
        if want("trip"):
            loop(st, "s-trip", T - 1, hook=hook, transcript=tr, cwd=tmp)
            res["no_trip_below"] = not tripped(st, "s-trip")
            loop(st, "s-trip", 1, hook=hook, transcript=tr, cwd=tmp)
            res["trip_30"] = tripped(st, "s-trip") and len(incidents(st, "s-trip")) == 1
            deny, why = call(st, "s-trip", "Bash", {"command": "ls"}, pre=True, hook=hook, cwd=tmp)
            res["next_call_refused"] = deny and "TOKEN_INCIDENT" in why and "recompile" in why
            deny2, _ = call(st, "s-trip", "Write", {"file_path": str(Path(tmp) / "x-receipt.md")}, pre=True, hook=hook, cwd=tmp)
            res["closeout_write_admitted"] = not deny2
            deny3, _ = call(st, "s-trip", "Write", {"file_path": str(Path(tmp) / "src.py")}, pre=True, hook=hook, cwd=tmp)
            res["other_write_refused"] = deny3
        if want("commit"):
            for i in range(6 * T):
                if i % 3 == 2:
                    call(st, "s-commit", "Bash", {"command": "git commit -F m.txt"}, "[main abc] done", hook=hook, cwd=tmp)
                else:
                    call(st, "s-commit", "Read", {"file_path": f"f{i}.py"}, hook=hook, cwd=tmp)
            res["commits_no_trip"] = not tripped(st, "s-commit") and not incidents(st, "s-commit")
        if want("edit"):
            for i in range(6 * T):
                if i % 5 == 4:
                    call(st, "s-edit", "Edit", {"file_path": "a.py"}, hook=hook, cwd=tmp)
                else:
                    call(st, "s-edit", "Grep", {"pattern": "x"}, hook=hook, cwd=tmp)
            res["edits_no_trip"] = not tripped(st, "s-edit")
        if want("off"):
            loop(st, "s-off", 2 * T, hook=hook, cwd=tmp, env={"CPP_SEM_BREAKER": "off"})
            res["kill_switch"] = not tripped(st, "s-off") and not (st / "semantic-breaker" / "s-off.json").exists()
        if want("unbound"):
            loop(st, "s-unbound", 2 * T, hook=hook, cwd=tmp, bound=False)
            res["unbound_inert"] = not (st / "semantic-breaker" / "s-unbound.json").exists()
        if want("rg"):  # red -> green is progress
            call(st, "s-rg", "Bash", {"command": "python tools/test_x.py"}, "FAIL gate", hook=hook, cwd=tmp)
            for _ in range(T - 2):
                call(st, "s-rg", "Read", {"file_path": "q.py"}, hook=hook, cwd=tmp)
            call(st, "s-rg", "Bash", {"command": "python tools/test_x.py"}, "PASS all", hook=hook, cwd=tmp)
            for _ in range(T - 2):
                call(st, "s-rg", "Read", {"file_path": "q.py"}, hook=hook, cwd=tmp)
            res["red_green_resets"] = not tripped(st, "s-rg")
        if want("head"):  # git HEAD moved outside the tool command is progress
            repo = Path(tmp) / "repo"
            repo.mkdir()
            g = lambda *a: subprocess.run([GIT, "-C", str(repo), "-c", "user.email=a@b", "-c", "user.name=t", *a],
                                          capture_output=True, text=True, check=True)
            g("init", "-q")
            (repo / "a").write_text("1")
            g("add", "a")
            g("commit", "-q", "-m", "one")
            for i in range(T - 2):
                call(st, "s-head", "Read", {"file_path": "q.py"}, hook=hook, cwd=repo)
            (repo / "a").write_text("2")
            g("commit", "-q", "-am", "two")
            for i in range(T - 2):
                call(st, "s-head", "Read", {"file_path": "q.py"}, hook=hook, cwd=repo)
            res["head_moved_resets"] = not tripped(st, "s-head")
        if want("rr"):
            f = Path(tmp) / "same.txt"
            f.write_text("x")
            for _ in range(5):
                call(st, "s-rr", "Read", {"file_path": str(f)}, hook=hook, cwd=tmp)
            s = json.loads((st / "semantic-breaker" / "s-rr.json").read_text(encoding="utf-8"))
            res["rereads_counted"] = s["rereads"] == 4
    return res


def mutant(name, old, new):
    src = HOOK.read_text(encoding="utf-8")
    assert old in src, f"mutation anchor missing: {name}"
    p = PP / "hooks" / f"_mut_{name}_semantic_breaker.js"
    p.write_text(src.replace(old, new, 1), encoding="utf-8")
    return p


def main():
    live = scenarios(HOOK)
    for k, v in live.items():
        check(f"C4-{k}", v, "hook behaves as specified")

    with tempfile.TemporaryDirectory() as tmp:
        st = Path(tmp)
        tr = mk_transcript(tmp)
        loop(st, "s-inc", 25, transcript=tr, cwd=tmp, env={"CPP_SEM_BREAKER_CALLS": ""})
        inc = json.loads(incidents(st, "s-inc")[0].read_text(encoding="utf-8"))
        check("C4-incident-shape", inc["class"] == "TOKEN_INCIDENT" and inc["counters"]["calls_since_progress"] == 25
              and len(inc["last_tools"]) == 12 and inc["threshold"]["calls"] >= 25, f"counters {inc['counters']}")
        check("C4-incident-autopsy", isinstance(inc["autopsy"], dict) and "roles" in inc["autopsy"], f"autopsy keys {list(inc['autopsy'])}")
        b = json.loads((st / "session-budget-s-inc.json").read_text(encoding="utf-8"))
        check("C4-deny-budget", b["stop"] == 1 and b["source"] == "semantic_breaker", "session_budget_guard envelope written")
        # the existing guard really denies on that state (stop=1 vs a transcript with usage)
        guard = PP / "hooks" / "session_budget_guard.js"
        e = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st))
        e.pop("CPP_GOAL", None)
        ev = {"session_id": "s-inc", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"},
              "transcript_path": str(tr), "cwd": str(tmp)}
        p = subprocess.run([NODE, "-e", "require(process.argv[1]).run(JSON.parse(process.argv[2])).then(r=>console.log(JSON.stringify(r)))",
                            str(guard), json.dumps(ev)], capture_output=True, text=True, env=e, timeout=60)
        check("C4-existing-guard-denies", "deny" in p.stdout, p.stdout.strip()[:120])
        # an Owner-declared envelope is never overwritten
        (st / "session-budget-s-own.json").write_text(json.dumps({"target": 9, "warn": 9, "stop": 9}), encoding="utf-8")
        loop(st, "s-own", T, cwd=tmp)
        check("C4-keeps-owner-envelope", json.loads((st / "session-budget-s-own.json").read_text(encoding="utf-8"))["stop"] == 9, "stop stayed 9")

    # fail open on garbage
    p = subprocess.run([NODE, str(HOOK)], input="{not json", capture_output=True, text=True, timeout=30)
    check("C4-fail-open", p.returncode == 0 and p.stdout.strip() == "{}", f"rc={p.returncode} out={p.stdout.strip()}")

    # calibration: synthetic transcripts with known gaps
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for n in range(5):
            rows, i = [], 0
            for gap in (3, 7, 12 + n):
                for _ in range(gap):
                    i += 1
                    rows.append({"type": "assistant", "requestId": f"r{i}", "message": {"id": f"m{i}", "model": "x",
                                 "usage": {"input_tokens": 1}, "content": [{"type": "tool_use", "id": f"u{i}", "name": "Read", "input": {"file_path": "a"}}]}})
                i += 1
                rows.append({"type": "assistant", "requestId": f"r{i}", "message": {"id": f"m{i}", "model": "x",
                             "usage": {"input_tokens": 1}, "content": [{"type": "tool_use", "id": f"u{i}", "name": "Edit", "input": {"file_path": "a"}}]}})
            p = Path(tmp) / f"s{n}.jsonl"
            p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            paths.append(str(p))
        r = sb.calibrate(paths)
        check("C4-calibrate", r["usable"] == 5 and r["gaps"] == 15 and r["calls_p95"] == 16 and r["max"] == 16, f"p95={r['calls_p95']} max={r['max']}")
        r2 = sb.calibrate(paths[:3])
        check("C4-calibrate-needs-5", r2["calls_p95"] is None and r2["default_used"], "fewer than 5 transcripts -> default 25")

    # mutation drill
    G = {"trip_30": "trip", "next_call_refused": "trip", "other_write_refused": "trip", "commits_no_trip": "commit",
         "edits_no_trip": "edit", "kill_switch": "off", "unbound_inert": "unbound", "head_moved_resets": "head",
         "red_green_resets": "rg", "rereads_counted": "rr"}
    muts = {
        "trip_30": ("st.since_progress >= th.calls", "st.since_progress >= 100000"),
        "next_call_refused": ("return denyMsg(st);", "return null;"),
        "commits_no_trip": ("if (COMMIT.test(cmd) && !FAILTXT.test(res.slice(0, 400))) progress = 'commit';", "if (false) progress = 'commit';"),
        "edits_no_trip": ("if (EDITS.has(tool)) progress", "if (false) progress"),
        "kill_switch": ("if (off()) return null;", ""),
        "unbound_inert": ("if (!b) return null;", ""),
        "head_moved_resets": ("head !== st.head", "false"),
        "red_green_resets": ("if (st.red && !bad) progress = 'red_green';", ""),
        "rereads_counted": ("st.rereads += 1;", ""),
        "other_write_refused": ("CLOSEOUT_PATH.test(fp) && (st.closeout", "true && (st.closeout"),
    }
    for name, (old, new) in muts.items():
        mp = mutant(name, old, new)
        try:
            r = scenarios(mp, {G[name]})
        finally:
            mp.unlink()
        check(f"C4-mutant-{name}-RED", r[name] is False, f"gate {name} -> {r[name]} under mutation")
    close_drivers()
    print(f"{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
