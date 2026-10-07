"""CE-T0a: self_spend.py meters the requested session (main + its own subagents) and nothing else.

Hermetic: USERPROFILE/HOME point at a tmp dir, so the module's default project dir is a fixture that
holds the hardcoded sid's transcript -- the foreign file the pre-fix meter counted for any --session.
"""
import json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "vault", "programs", "cognitive-economy", "gen2", "evidence", "stage0", "self_spend.py")
OWN = "11111111-0000-4000-8000-000000000001"
MISSING = "33333333-0000-4000-8000-000000000003"
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  " + detail))


def rec(mid, i, cw, cr, o, sid):
    return json.dumps({"sessionId": sid, "type": "assistant", "message": {"id": mid, "usage": {
        "input_tokens": i, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr, "output_tokens": o}}})


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build(home, foreign_sid):
    d = os.path.join(home, ".claude", "projects", "C--Users-User--claude-skills-claude-power-pack")
    # (a) own main transcript: m1 + m2, m1 repeated (streaming dup) -> 1115 + 2227
    write(os.path.join(d, OWN + ".jsonl"), [rec("m1", 10, 100, 1000, 5, OWN), rec("m2", 20, 200, 2000, 7, OWN),
                                           rec("m1", 10, 100, 1000, 5, OWN)])
    # (b) own subagent -> 10
    write(os.path.join(d, OWN, "subagents", "agent-a1.jsonl"), [rec("s1", 1, 2, 3, 4, OWN)])
    # (c) foreign: the hardcoded sid's main transcript + subagent, 7M each
    write(os.path.join(d, foreign_sid + ".jsonl"), [rec("f1", 7000000, 0, 0, 0, foreign_sid)])
    write(os.path.join(d, foreign_sid, "subagents", "agent-f.jsonl"), [rec("f2", 7000000, 0, 0, 0, foreign_sid)])
    return d


def run(module, home, *args):
    env = dict(os.environ, USERPROFILE=home, HOME=home, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, module, *args], capture_output=True, text=True, env=env, timeout=60)
    return p.stdout + p.stderr


def main():
    src = open(MOD, encoding="utf-8").read()
    foreign = re.search(r'(?m)^sid="([^"]+)"', src).group(1)
    tmp = tempfile.mkdtemp(prefix="ce_t0a_")
    try:
        d = build(tmp, foreign)
        out = run(MOD, tmp, "--session", OWN)
        check("own main + own subagent counted exactly", "calls 3 processed 3,352 (ctx 3,336 out 16)" in out, out)
        check("own subagent attributed", "subagent calls 1 subagent ctx 6" in out, out)
        check("foreign transcript excluded", "7,0" not in out and "files 2 " in out, out)
        miss = run(MOD, tmp, "--session", MISSING)
        check("no transcript -> None, never 0", "processed None" in miss and "processed 0" not in miss, miss)
        # driver shape: exec with only sid=/d= rewritten, under a foreign argv that itself carries --session
        drv = re.sub(r'(?m)^d=.*$', lambda _: "d=" + repr(d), re.sub(r'(?m)^sid=.*$', lambda _: 'sid="%s"' % OWN, src))
        env_argv, sys.argv = sys.argv, ["tranche_driver.py", "--session", MISSING]
        import io, contextlib
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(drv, "self_spend_rewritten", "exec"), {"__name__": "__main__"})
        finally:
            sys.argv = env_argv
        check("driver exec (sid=/d= rewritten) ignores host argv", "calls 3 processed 3,352" in buf.getvalue(), buf.getvalue())
        # mutation: revert the fix (flags ignored again) -> must go red
        mut = os.path.join(tmp, "mut", "self_spend.py")
        os.makedirs(os.path.dirname(mut))
        reverted = re.sub(r'(?m)^if "--(session|dir)" in a:.*$', "pass", src)
        assert reverted != src, "mutation did not apply"
        open(mut, "w", encoding="utf-8").write(reverted)
        mout = run(mut, tmp, "--session", OWN)
        check("mutant (flags ignored) is red: meters the foreign sid", "calls 3 processed 3,352" not in mout
              and "14,000,000" in mout, mout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = sum(results)
    print("SELF_SPEND_ATTRIBUTION_PASS=%d/%d" % (n, len(results)))
    return 0 if n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
