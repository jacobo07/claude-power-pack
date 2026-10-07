"""V-DRIVER-* gates for tools/tranche_driver.py. Each red branch is driven, each against a green control."""
import subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tranche_driver as td  # noqa: E402

passes = fails = 0


def gate(name, ok, ev=""):
    global passes, fails
    passes += bool(ok); fails += not ok
    print(f"  {'ok' if ok else 'FAIL'}   {name} {ev}")


head = subprocess.run([td.GIT, "-C", str(td.REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    (t / "ok.py").write_text("raise SystemExit(0)\n"); (t / "bad.py").write_text("raise SystemExit(1)\n")
    good = t / "good.md"; good.write_text(f"verdict PASS\nCOMMITS: {head[:10]}\n")
    unreach = t / "unreach.md"; unreach.write_text("COMMITS: deadbeefdeadbeef\n")
    nocommit = t / "nocommit.md"; nocommit.write_text("verdict PASS\n")
    okt, badt = f'"{t / "ok.py"}"', f'"{t / "bad.py"}"'
    P = lambda rc, tests=(okt,): {"step": "SX", "cap": 1000, "receipt": str(rc), "tests": list(tests), "prompt": ""}
    sp = lambda v: (lambda sid: v)

    c, _ = td.check(P(good), "x", sp(500)); gate("V-DRIVER-GREEN-CONTROL", all(c.values()), c)
    c, _ = td.check(P(t / "missing.md"), "x", sp(500)); gate("V-DRIVER-MISSING-RECEIPT", not c["receipt"], c)
    c, _ = td.check(P(unreach), "x", sp(500)); gate("V-DRIVER-UNREACHABLE-COMMIT", not c["commits"], c)
    c, _ = td.check(P(nocommit), "x", sp(500)); gate("V-DRIVER-NO-COMMIT-LINE", not c["commits"], c)
    c, _ = td.check(P(good, (okt, badt)), "x", sp(500)); gate("V-DRIVER-FAILING-TEST", not c["tests"], c)
    c, _ = td.check(P(good), "x", sp(1001)); gate("V-DRIVER-OVER-CAP-SPEND", not c["spend"], c)
    c, _ = td.check(P(good), "x", sp(None)); gate("V-DRIVER-UNKNOWN-SPEND-NOT-GREEN", not c["spend"], c)

    launched = []
    fake_launch = lambda argv, prompt: launched.append(argv) or 0
    declared_cwd = []
    decl = lambda code: (lambda argv, timeout=None, cwd=None: (declared_cwd.append(cwd) or code)
                         if "session-declare" in argv else td.run(argv, timeout))
    pk = dict(P(good)); pk["prompt"] = str(t / "ok.py")
    q = dict(log=lambda m: None, calls_fn=lambda sid, stop: 5)
    r = td.drive([pk], {"steps": {}}, "c", 4_500_000, 0, 1_200_000, sp(4_499_500), decl(0), fake_launch, **q)
    gate("V-DRIVER-REFUSE-TRANCHE-OVER-CAP", r["steps"]["SX"]["verdict"] == "REFUSED_OVER_CAP" and not launched, r)
    big = dict(pk, cap=2_000_000)
    r = td.drive([big], {"steps": {}}, "c", 4_500_000, 0, 1_200_000, sp(0), decl(0), fake_launch, **q)
    gate("V-DRIVER-REFUSE-STEP-MAX", r["steps"]["SX"]["verdict"] == "REFUSED_OVER_CAP" and not launched, r)
    r = td.drive([pk], {"steps": {}}, "c", 4_500_000, 0, 1_200_000, sp(500), decl(3), fake_launch, **q)
    gate("V-DRIVER-ADMISSION-REFUSED", r["steps"]["SX"]["verdict"] == "ADMISSION_REFUSED" and not launched, r)
    r = td.drive([pk], {"steps": {}}, "c", 4_500_000, 0, 1_200_000, sp(500), decl(0), fake_launch,
                 log=lambda m: None, calls_fn=lambda sid, stop: 0)
    gate("V-DRIVER-REFUSE-INFEASIBLE", r["steps"]["SX"]["verdict"] == "REFUSED_INFEASIBLE" and not launched, r)
    # calls_for prices calls at the guard's measured floor: 124,166/call, 2 reserve, 2,100 growth.
    fz = lambda spent, pc: (lambda sid, stop, n: {"spent": spent, "per_call": pc})
    n9 = td.calls_for("x", 900_000, fz(0, 124_166))
    # n=4 -> 6 calls with reserve: 6*124,166 + 2,100*6*7/2 = 789,096 <= 900k; n=5 -> 927,962 > 900k.
    gate("V-DRIVER-CALLS-AT-MEASURED-FLOOR", n9 == 4, f"n={n9} (fixed 110k rule gave 8, which the guard refused)")
    gate("V-DRIVER-CALLS-NONE-FIT", td.calls_for("x", 200_000, fz(0, 124_166)) == 0)
    gate("V-DRIVER-CALLS-UNKNOWN-COST", td.calls_for("x", 900_000, fz(0, None)) is None)
    import mission_spend as ms  # noqa: E402 -- the real guard, in-process: no session is declared
    fsid = "00000000-feas-probe-0000-000000000000"
    nr = td.calls_for(fsid, 2_800_000)
    adm, rej = ms.feasibility(fsid, 2_800_000, nr), ms.feasibility(fsid, 2_800_000, (nr or 0) + 1)
    gate("V-DRIVER-REAL-GUARD-ADMITS-N-REFUSES-N+1", bool(nr) and adm["feasible"] and not rej["feasible"],
         f"n={nr} per_call={adm['per_call']}")
    # tranche cap 1800: SX fits (coord 500 + cap 1000); SY must be refused because SX's measured 500 now counts.
    r = td.drive([pk, dict(pk, step="SY")], {"steps": {}}, "c", 1800, 0, 1_200_000, sp(500), decl(0), fake_launch, **q)
    gate("V-DRIVER-PASS-PATH+WORKER-SPEND-COUNTS", r["steps"]["SX"]["verdict"] == "PASS" and len(launched) == 1 and
         "--session-id" in launched[0] and r["steps"]["SY"]["verdict"] == "REFUSED_OVER_CAP", r["steps"])
    gate("V-DRIVER-REAL-METER", isinstance(td.spend("e6e0eca7-6de8-4e89-9194-4cb611644727"), int))
    # a worker run from a worktree is filed under ANOTHER project dir; the meter must find it, and no file is unknown.
    proj = t / "projects"; (proj / "C--elsewhere-wt").mkdir(parents=True)
    (proj / "C--elsewhere-wt" / "w1.jsonl").write_text(
        '{"message": {"id": "m1", "usage": {"input_tokens": 100, "output_tokens": 5}}}\n', encoding="utf-8")
    gate("V-DRIVER-SPEND-OTHER-PROJECT-DIR", td.spend("w1", proj) == 105, td.spend("w1", proj))
    gate("V-DRIVER-SPEND-NO-TRANSCRIPT-IS-UNKNOWN", td.spend("absent", proj) is None)
    # receipts are judged in the worktree (ROOT), not in the coordinator's tree.
    (t / "rel-receipt.md").write_text("verdict PASS\n")
    rel = {"step": "SR", "cap": 1000, "receipt": "rel-receipt.md", "tests": [], "prompt": ""}
    c_main, _ = td.check(rel, "x", sp(1))
    td.ROOT = t
    try:
        c_wt, _ = td.check(rel, "x", sp(1))
    finally:
        td.ROOT = td.REPO
    gate("V-DRIVER-RECEIPT-JUDGED-IN-ROOT", c_wt["receipt"] and not c_main["receipt"], (c_main, c_wt))
    # a worktree has no session history, so admission run there prices nothing and refuses: it must run in REPO.
    gate("V-DRIVER-ADMISSION-PRICED-IN-REPO", bool(declared_cwd) and all(c == td.REPO for c in declared_cwd),
         set(map(str, declared_cwd)))
    # E2: with a manifest the coordinator is declared (stop = baseline + allowance) before any launch.
    ev = []

    def cdecl(code):
        def f(argv, timeout=None, cwd=None):
            if "session-declare" in argv:
                ev.append(("declare", argv[argv.index("--session") + 1], argv[argv.index("--stop") + 1]))
                return code if "COORD" in argv else 0
            return td.run(argv, timeout)
        return f
    ev_launch = lambda argv, prompt: ev.append(("launch",)) or 0
    man = {"coordinator": {"sid": "COORD", "allowance": 1000}}
    q2 = dict(log=lambda m: None, calls_fn=lambda sid, stop: 5, calls_count_fn=lambda sid: 7)
    r = td.drive([pk], {"steps": {}}, "c", 4_500_000, 0, 1_200_000, sp(500), cdecl(0), ev_launch, manifest=man, **q2)
    gate("V-DRIVER-COORDINATOR-DECLARED-FIRST", ev[:1] == [("declare", "COORD", "1500")] and ("launch",) in ev, ev)
    s = r["steps"]["SX"]
    gate("V-DRIVER-STEP-CALLS-AND-BOUNDARIES", s.get("calls") == 7 and s.get("boundaries") == 1, s)
    ev.clear()
    r = td.drive([pk], {"steps": {}}, "c", 4_500_000, 0, 1_200_000, sp(500), cdecl(3), ev_launch, manifest=man, **q2)
    gate("V-DRIVER-COORDINATOR-REFUSED-NOTHING-LAUNCHED", ("launch",) not in ev and not r["steps"] and
         r.get("coordinator_admission", {}).get("verdict") == "REFUSED", (ev, r))
    ev.clear()
    r = td.drive([pk], {"steps": {}}, "c", 4_500_000, 0, 1_200_000, sp(500), cdecl(3), ev_launch, **q2)
    gate("V-DRIVER-NO-MANIFEST-UNCHANGED", ("launch",) in ev and all(e[1] != "COORD" for e in ev if e[0] == "declare")
         and "coordinator_admission" not in r, ev)
    # calls come from the guard's own counter on the worker transcript; no transcript is unknown, never 0.
    w2 = proj / "C--elsewhere-wt" / "w2.jsonl"
    w2.write_text("".join(
        '{"type": "assistant", "message": {"id": "m%d", "role": "assistant", "content": [{"type": "tool_use", '
        '"id": "t%d", "name": "Read", "input": {}}], "usage": {"input_tokens": 100, "output_tokens": 5}}}\n' % (i, i)
        for i in (1, 2)), encoding="utf-8")
    ref = ms.session_tokens(w2)["calls"]
    gate("V-DRIVER-CALLS-FROM-TRANSCRIPT", td.calls_of("w2", proj) == ref == 2 and td.calls_of("absent", proj) is None,
         (td.calls_of("w2", proj), ref))
    gate("V-DRIVER-BOUNDARIES-LISTED", td.boundaries("x\nBOUNDARIES: a; b; c\n") == 3 and td.boundaries("") == 1
         and td.boundaries("BOUNDARIES: 4") == 4)

print(f"DRIVER_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
