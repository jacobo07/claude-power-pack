"""V-PUSHAUTH-* -- mission push authority (Resource Residency W0, 2026-11-21).

Historical regression: 2026-11-20 23:53:24 a mission worker pushed to the PUBLIC origin with `& $g push -u origin
worktree-resource-residency` (PowerShell tool), past ovo-push-gate's literal-only regex. Both layers are driven for
real: the PreToolUse gate as a node process with a real payload, the pre-push hook through a real `git push` into a
temporary bare remote. A mutant gate with the old detection must let the incident through (drill goes red).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(HERE, "push_authority.py")
GATE = os.path.join(REPO, "modules", "zero-crash", "hooks", "ovo-push-gate.js")
HOOK = os.path.join(HERE, "git-hooks", "pre-push")
GIT = r"C:\Program Files\Git\cmd\git.exe" if os.path.exists(r"C:\Program Files\Git\cmd\git.exe") else "git"
NODE = shutil.which("node") or "node"
WORKER = "e5ca940c-89d9-4ed5-9410-5bdcde03e068"      # the real worker of the incident
OTHER = "11111111-2222-3333-4444-555555555555"
INCIDENT = "& $g push -u origin worktree-resource-residency 2>&1 | Select -Last 3"
fails = []


def gate(name: str, ok: bool, why: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" -- {why}"))
    if not ok:
        fails.append(name)


def env_for(state: str, sid: str | None = None) -> dict:
    e = dict(os.environ)
    e["GSD_LONG_RUN_STATE_DIR"] = state
    e.pop("CLAUDE_CODE_SESSION_ID", None)
    e.pop("OVO_BYPASS", None)
    if sid:
        e["CLAUDE_CODE_SESSION_ID"] = sid
    return e


def tool(state: str, *args: str, sid: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True, env=env_for(state, sid))


def run_gate(script: str, state: str, cmd: str, sid: str, cwd: str) -> int:
    payload = json.dumps({"tool_name": "PowerShell", "tool_input": {"command": cmd}, "session_id": sid, "cwd": cwd})
    r = subprocess.run([NODE, script], input=payload, capture_output=True, text=True, env=env_for(state))
    return r.returncode


with tempfile.TemporaryDirectory() as d:
    state = os.path.join(d, "state"); os.makedirs(state)
    with open(os.path.join(state, "gsd-mission-m-e78bdb938339.json"), "w") as f:
        json.dump({"mission_id": "m-e78bdb938339", "previous_owner": {"session_id": WORKER}}, f)
    plain = os.path.join(d, "plain"); os.makedirs(plain)          # no .powerpack: only the authority check applies

    # -- decider
    r = tool(state, "check", "--session", WORKER)
    gate("V-PUSHAUTH-WORKER-DENIED", r.returncode == 3 and "m-e78bdb938339" in r.stdout, r.stdout)
    gate("V-PUSHAUTH-NON-WORKER-ALLOWED", tool(state, "check", "--session", OTHER).returncode == 0)
    gate("V-PUSHAUTH-NO-SESSION-ALLOWED", tool(state, "check", "--session", "").returncode == 0)
    r = tool(state, "grant", "--mission", "m-e78bdb938339", "--reason", "self", sid=WORKER)
    gate("V-PUSHAUTH-WORKER-CANNOT-GRANT", r.returncode == 3 and tool(state, "check", "--session", WORKER).returncode == 3)

    # -- PreToolUse gate (real node process, real payload shape)
    gate("V-PUSHAUTH-GATE-INCIDENT-BLOCKED", run_gate(GATE, state, INCIDENT, WORKER, plain) == 2)
    for label, cmd in [("GIT-C", 'git -C "C:\\x y" push origin b'),
                       ("GIT-FULLPATH", "& 'C:\\Program Files\\Git\\cmd\\git.exe' push origin b"),
                       ("GIT-EXE", "git.exe push"), ("AFTER-SEP", "git add -A; git commit -m x; git push")]:
        gate(f"V-PUSHAUTH-GATE-{label}-BLOCKED", run_gate(GATE, state, cmd, WORKER, plain) == 2, cmd)
    for label, cmd in [("HERESTRING-QUOTE", "$add = @'\n  (`git push` evades)\n'@\n[IO.File]::AppendAllText($f,$add)"),
                       ("ECHO-QUOTE", "echo 'git push'"), ("ARRAY-PUSH", "$list.push(1)"),
                       ("NO-PUSH", "git status; git log -1")]:
        gate(f"V-PUSHAUTH-GATE-{label}-PASSES", run_gate(GATE, state, cmd, WORKER, plain) == 0, cmd)
    gate("V-PUSHAUTH-GATE-NON-WORKER-PASSES", run_gate(GATE, state, INCIDENT, OTHER, plain) == 0)

    # -- mutation drill: the old literal-only detection must let the incident through
    src = open(GATE, encoding="utf-8").read()
    mutant_src = src.replace("if (!isPushShaped(cmd)) return emit(0);", "if (!BLOCK_REGEX.test(cmd)) return emit(0);")
    mutant = GATE.replace(".js", f".mutant-{os.getpid()}.js")
    try:
        open(mutant, "w", encoding="utf-8").write(mutant_src)
        gate("V-PUSHAUTH-MUTANT-GOES-RED", mutant_src != src and run_gate(mutant, state, INCIDENT, WORKER, plain) == 0,
             "mutant still blocks: the regression test would not catch a revert")
    finally:
        if os.path.exists(mutant):
            os.remove(mutant)

    # -- pre-push hook through a real git push
    bare = os.path.join(d, "remote.git"); work = os.path.join(d, "work")
    git = lambda *a, cwd=work, sid=None: subprocess.run([GIT, *a], cwd=cwd, capture_output=True, text=True,
                                                        env=env_for(state, sid))
    git("init", "--bare", bare, cwd=d); git("init", work, cwd=d)
    os.makedirs(os.path.join(work, "tools")); shutil.copy(TOOL, os.path.join(work, "tools", "push_authority.py"))
    shutil.copy(HOOK, os.path.join(work, ".git", "hooks", "pre-push"))
    git("config", "user.email", "t@t"); git("config", "user.name", "t")
    git("add", "-A"); git("commit", "-m", "c"); git("remote", "add", "origin", bare)
    r = git("push", "origin", "HEAD:refs/heads/b1", sid=WORKER)
    gate("V-PUSHAUTH-HOOK-WORKER-REFUSED", r.returncode != 0 and "push authority" in r.stderr, r.stderr[-300:])
    r = git("push", "origin", "HEAD:refs/heads/b2", sid=OTHER)
    gate("V-PUSHAUTH-HOOK-NON-WORKER-PUSHES", r.returncode == 0, r.stderr[-300:])
    r = git("push", "origin", "HEAD:refs/heads/b3")
    gate("V-PUSHAUTH-HOOK-NO-SESSION-PUSHES", r.returncode == 0, r.stderr[-300:])
    tool(state, "grant", "--mission", "m-e78bdb938339", "--reason", "Owner test")
    r = git("push", "origin", "HEAD:refs/heads/b4", sid=WORKER)
    gate("V-PUSHAUTH-HOOK-GRANTED-PUSHES", r.returncode == 0, r.stderr[-300:])
    gate("V-PUSHAUTH-GATE-GRANTED-PASSES", run_gate(GATE, state, INCIDENT, WORKER, plain) == 0)
    tool(state, "revoke", "--mission", "m-e78bdb938339")
    r = git("push", "origin", "HEAD:refs/heads/b5", sid=WORKER)
    gate("V-PUSHAUTH-HOOK-REVOKED-REFUSED", r.returncode != 0)
    heads = git("ls-remote", bare).stdout
    gate("V-PUSHAUTH-REMOTE-HAS-ONLY-ALLOWED", all(b in heads for b in ("b2", "b3", "b4"))
         and not any(b in heads for b in ("b1", "b5")), heads)

print("ALL PASS" if not fails else "FAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)
