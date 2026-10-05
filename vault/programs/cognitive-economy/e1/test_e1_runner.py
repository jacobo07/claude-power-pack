"""V-E1-* gates for the E1 runner: one counted run end to end with a fake CLI process, then every validity, spend,
argv, env, session-parsing and transcript-lookup branch driven red and green.

    python3 vault/programs/cognitive-economy/e1/test_e1_runner.py [GATE-NAME ...]

Stdlib only, no pytest, no model call: a guard installed before any other import blocks every exec of a claude
binary (V-E1-NO-MODEL proves it fires; V-E1-NO-MODEL-END proves only that control attempted a session). With gate
names, only those gates run, plus the two no-model gates; an unknown name exits 1. Ends
`E1_PASS=<passes>/<total>`; exit 0 only when every selected gate passed.
"""
import sys

sys.dont_write_bytecode = True

import os  # noqa: E402
import subprocess  # noqa: E402

BLOCKED = []
_RealPopen = subprocess.Popen


class ModelCallBlocked(Exception):
    """Deliberately not an OSError: a blocked session must not read as an ordinary exec error."""


def _argv0(args):
    if isinstance(args, (list, tuple)):
        return str(args[0]) if args else ""
    return str(args).split()[0] if str(args).split() else ""


class GuardedPopen(_RealPopen):
    def __init__(self, args, *a, **kw):
        a0 = _argv0(args)
        if "claude" in os.path.basename(a0) or "/claude/" in os.path.realpath(a0):
            BLOCKED.append(list(args) if isinstance(args, (list, tuple)) else [str(args)])
            raise ModelCallBlocked(f"blocked exec of {a0}")
        super().__init__(args, *a, **kw)


subprocess.Popen = GuardedPopen  # installed before e1_runner or any bank module is imported

import importlib.util  # noqa: E402
import json  # noqa: E402
import tempfile  # noqa: E402
import traceback  # noqa: E402
import types  # noqa: E402
import uuid  # noqa: E402
from pathlib import Path  # noqa: E402

E1 = Path(__file__).resolve().parent
sys.path.insert(0, str(E1))
import e1_contract as K  # noqa: E402
import e1_runner as R  # noqa: E402

BANK_PATH = E1 / "bank"
try:
    BANK = R.load_bank(BANK_PATH)
    BANK_ERR = None
except SystemExit as e:  # a refusal, never a skip: every bank gate FAILs naming it
    BANK, BANK_ERR = None, f"bank not loadable: {e}"

GCEG = "J-gceg_product_page"


def need_bank():
    if BANK is None:
        raise RuntimeError(BANK_ERR)
    return BANK


# ---- fake CLI process --------------------------------------------------------------------------------

def fake_transcript_lines(sid, extra_repeat=False):
    u1 = {"input_tokens": 3, "cache_creation_input_tokens": 5000, "cache_read_input_tokens": 20000,
          "output_tokens": 40}
    u2 = {"input_tokens": 5, "cache_creation_input_tokens": 300, "cache_read_input_tokens": 25000,
          "output_tokens": 60}
    lines = [{"type": "user", "entrypoint": "sdk-cli", "sessionId": sid,
              "message": {"role": "user", "content": "x"}},
             {"type": "assistant", "requestId": "req_1", "sessionId": sid,
              "message": {"id": "msg_1", "role": "assistant", "model": K.MODEL, "usage": u1}},
             {"type": "assistant", "requestId": "req_2", "sessionId": sid,
              "message": {"id": "msg_2", "role": "assistant", "model": K.MODEL, "usage": u2}}]
    if extra_repeat:
        lines.append(lines[-1])
    return "".join(json.dumps(x) + "\n" for x in lines)


class FakeCli:
    """exec_fn stand-in for `claude -p`: writes the task's REF or NAIVE source and a two-call transcript."""

    def __init__(self, pole, projects, t):
        self.pole, self.projects, self.t, self.argv = pole, Path(projects), t, None

    def __call__(self, argv, **kw):
        self.argv = list(argv)
        assert argv[0] == R.CLAUDE, argv[0]
        prompt = argv[argv.index("-p") + 1]
        assert self.t["module"] in prompt, prompt
        spec = importlib.util.spec_from_file_location("e1test_task_" + uuid.uuid4().hex[:8], self.t["file"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cwd = Path(kw["cwd"])
        (cwd / mod.MODULE).write_text(getattr(mod, self.pole), encoding="utf-8")
        sid = str(uuid.uuid4())
        d = self.projects / R._norm(cwd)
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{sid}.jsonl").write_text(fake_transcript_lines(sid), encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(
            {"session_id": sid, "num_turns": 2, "is_error": False}) + "\n", stderr="")


# ---- helpers -----------------------------------------------------------------------------------------

def good_run(**over):
    """The all-good run record (every field of the e1_contract docstring); overrides use dotted keys for metrics."""
    rec = {"kind": "run", "run_id": "J-x-A-a1", "task": "J-x", "rule": "rules/x.md", "arm": "A", "attempt": 1,
           "base": "0" * 40, "bank_dir": "vault/programs/cognitive-economy/e1/bank", "task_file_sha256": "0" * 64,
           "cli": R.CLAUDE, "cli_version": "2.1.289 (test)", "model": K.MODEL, "excluded": [],
           "started": "2026-10-05T00:00:00+00:00", "started_epoch": 0.0, "tree_files": 100, "bank_in_tree": [],
           "pin_copies_removed": [], "precondition_rc": 1,
           "precondition_summary": "E1J_PASS=0/8 control=0/4 judgement=0/4", "session_launched": True,
           "claude_rc": 0, "wall_s": 1.0, "num_turns": 2, "is_error": False, "session_id": "s",
           "session_changed_paths": [], "grade_rc": 0, "grade_summary": "E1J_PASS=8/8 control=4/4 judgement=4/4",
           "grade_passed": 8, "grade_total": 8, "grade_fails": [],
           "metrics": {"state": "MEASURED", "reason": "by session id", "transcript": "t.jsonl",
                       "entrypoint": "sdk-cli", "calls": 2, "first_call_context": 25003,
                       "total_context": 50308, "output_tokens": 100, "models": [K.MODEL]},
           "ended": "2026-10-05T00:00:01+00:00", "worktree_removed": True}
    for k, v in over.items():
        if k.startswith("metrics."):
            rec["metrics"][k[len("metrics."):]] = v
        else:
            rec[k] = v
    return rec


def _raiser(name):
    def f(*a, **k):
        raise AssertionError(f"{name} must not be called")
    return f


def _tracer(pole, arm, rid, excl=None):
    bank = need_bank()
    saved = bank.RUNS
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        bank.RUNS = d / "runs"
        try:
            t = bank.tasks(only=[GCEG])[0]
            base = bank.jbase()
            results = d / "results.jsonl"
            fake = FakeCli(pole, d / "projects", t)
            rec = R.one_run(bank, t, arm, 1, base, excl=R.excludes() if excl is None else excl,
                            cli_version="2.1.289 (test)",
                            append=lambda r: R.append_record(results, r), run_id=rid, exec_fn=fake,
                            projects=d / "projects")
            R.append_record(results, rec)
            lines = [json.loads(x) for x in results.read_text(encoding="utf-8").splitlines()]
            tree_gone = not os.path.lexists(bank.RUNS / rid)
        finally:
            bank.RUNS = saved
    return t, rec, fake, lines, tree_gone


# ---- Task 1 gates ------------------------------------------------------------------------------------

def g_no_model():
    try:
        subprocess.run([R.CLAUDE, "--version"])  # cannot spend even if the guard is broken
        return False, "a claude exec was NOT blocked"
    except ModelCallBlocked as e:
        return True, f"blocked: {e}"


def g_tracer_ref():
    t, rec, fake, lines, gone = _tracer("REF", "B", "e1test-gceg-B-a1")
    m = rec.get("metrics", {})
    settings = json.loads(fake.argv[fake.argv.index("--settings") + 1]) if fake.argv and "--settings" in fake.argv \
        else {}
    checks = {
        "valid": rec.get("valid") is True and rec.get("invalid_reasons") == [],
        "task_pass": rec.get("task_pass") is True,
        "pre_red": rec.get("precondition_rc") not in (0, None),
        "metrics": (m.get("state"), m.get("first_call_context"), m.get("total_context"), m.get("output_tokens"),
                    m.get("entrypoint")) == ("MEASURED", 25003, 50308, 100, "sdk-cli"),
        "spend": rec.get("spend") == 50308,
        "no_leak": rec.get("bank_in_tree") == [] and rec.get("tree_files", 0) > 0,
        "scrub": rec.get("pin_copies_removed") == ["rules/common/code-review.md", "rules/python/testing.md"],
        "changed": "M e1j/product_page.py" in rec.get("session_changed_paths", []),
        "removed": rec.get("worktree_removed") is True and gone,
        "settings": settings.get("claudeMdExcludes") == R.excludes(),
        "records": [x["kind"] for x in lines] == ["run_start", "run"]
                   and all(x["run_id"] == "e1test-gceg-B-a1" for x in lines),
    }
    bad = [k for k, v in checks.items() if not v]
    return not bad, (f"bad={bad} valid={rec.get('valid')} reasons={rec.get('invalid_reasons')} "
                     f"task_pass={rec.get('task_pass')} first={m.get('first_call_context')} "
                     f"total={m.get('total_context')} out={m.get('output_tokens')} spend={rec.get('spend')} "
                     f"pre={rec.get('precondition_summary')} grade={rec.get('grade_summary')} "
                     f"scrub={rec.get('pin_copies_removed')} tree_files={rec.get('tree_files')} "
                     f"err={rec.get('error')}")


def g_tracer_naive():
    t, rec, fake, lines, gone = _tracer("NAIVE", "A", "e1test-gceg-A-a1", excl=[])
    judgement = {n for n, k in t["checks"] if k == "judgement"}
    failing = [f.split()[1] for f in rec.get("grade_fails", []) if len(f.split()) > 1]
    checks = {
        "valid": rec.get("valid") is True,
        "fails": rec.get("task_pass") is False and bool(rec.get("grade_fails")),
        "judgement_only": bool(failing) and len(failing) == len(rec.get("grade_fails", []))
                          and all(n in judgement for n in failing),
        "no_settings": fake.argv is not None and "--settings" not in fake.argv,
        "removed": rec.get("worktree_removed") is True and gone,
        "records": [x["kind"] for x in lines] == ["run_start", "run"],
    }
    bad = [k for k, v in checks.items() if not v]
    return not bad, (f"bad={bad} valid={rec.get('valid')} reasons={rec.get('invalid_reasons')} "
                     f"grade={rec.get('grade_summary')} failing={failing} err={rec.get('error')}")


def g_no_model_end():
    p_argvs = [a for a in BLOCKED if "-p" in a]
    probes = [a for a in BLOCKED if a == [R.CLAUDE, "--version"]]
    other = [a for a in BLOCKED if a not in probes]
    return (not p_argvs and len(probes) == 1 and not other,
            f"blocked={len(BLOCKED)} with -p={len(p_argvs)} version-probes={len(probes)} other={[a[:3] for a in other]}")


# ---- Task 2 gates ------------------------------------------------------------------------------------

FAULTS = [
    ({"bank_in_tree": ["x"]}, "bank file in run tree"),
    ({"tree_files": 0}, "run tree listing empty"),
    ({"precondition_rc": 0}, "precondition not red"),
    ({"precondition_summary": "no E1J line"}, "precondition not red"),
    ({"metrics.state": "UNMEASURED"}, "session transcript UNMEASURED"),
    ({"metrics.entrypoint": "cli"}, "entrypoint cli"),
    ({"metrics.models": ["claude-haiku-4-5"]}, "model claude-opus-5-5 absent from transcript"),
    ({"grade_summary": "no E1J line"}, "grade did not run"),
]


def _valid_checks(fn):
    good = fn(good_run())
    res = [(fn(good_run(**over)), want) for over, want in FAULTS]
    pre_only = {k: v for k, v in good_run().items()
                if k in ("kind", "run_id", "task", "rule", "arm", "attempt", "base", "bank_dir", "task_file_sha256",
                         "cli", "cli_version", "model", "excluded", "started", "started_epoch",
                         "session_launched")}
    pre_only["session_launched"] = False
    early = fn(pre_only)
    ok = good == (True, []) and all(r == (False, [w]) for r, w in res) and early[0] is False
    return ok, good, res, early


def g_valid():
    ok, good, res, early = _valid_checks(K.run_valid)
    # red drill: a run_valid that ignores the model clause must fail the same predicate
    mutant_ok = _valid_checks(lambda r: K.run_valid(r) if _model_present(r) else (True, []))[0]
    return ok and not mutant_ok, (f"good={good} faults={[r[1] for r, _ in res]} pre_session={early} "
                                  f"mutant_rejected={not mutant_ok}")


def _model_present(r):
    return K.MODEL in (r.get("metrics", {}).get("models") or [])


def g_task_pass():
    cases = [(good_run(grade_rc=0, grade_passed=8, grade_total=8), True),
             (good_run(grade_rc=1, grade_passed=7, grade_total=8), False),
             (good_run(grade_rc=0, grade_passed=0, grade_total=0), False),
             (good_run(grade_rc="timeout", grade_passed=0, grade_total=0), False)]
    got = [K.task_pass(r) for r, _ in cases]
    return got == [w for _, w in cases], f"got={got}"


def _spend_checks(fn):
    a = fn(good_run(**{"metrics.total_context": 700000}))
    b = fn(good_run(metrics={"state": "NO_CALLS", "total_context": 0}))
    c = fn(good_run(session_launched=False, metrics={"state": "UNMEASURED", "reason": "x"}))
    d = fn(good_run(session_launched=True, metrics={"state": "UNMEASURED", "reason": "x"}))
    return (a == 700000 and b == 0 and c == 0 and d is None), (a, b, c, d)


def g_spend():
    ok, got = _spend_checks(K.run_spend)
    mutant_ok, mgot = _spend_checks(lambda r: K.run_spend(r) or 0)  # folds unknown into 0
    return ok and not mutant_ok, f"got={got} mutant(unknown->0)={mgot} rejected={not mutant_ok}"


def g_run_id():
    ok = K.run_id("J-x", "B", 2) == "J-x-B-a2"
    refused = []
    for a, n in (("C", 1), ("A", 3), ("A", 0)):
        try:
            K.run_id("J-x", a, n)
        except K.ContractError:
            refused.append((a, n))
    return ok and len(refused) == 3, f"J-x-B-a2={ok} refused={refused}"


def g_argv():
    ex = R.excludes()
    common = [R.CLAUDE, "-p", "P", "--model", "claude-opus-5-5", "--output-format", "json", "--max-turns", "40",
              "--permission-mode", "acceptEdits", "--allowedTools", "Read,Edit,Write,Grep,Glob,Bash"]
    a = R.session_cmd("P", "A", ex)
    b = R.session_cmd("P", "B", ex)
    b_ok = b[:-2] == common and b[-2] == "--settings" and json.loads(b[-1]) == {"claudeMdExcludes": ex}
    try:
        R.session_cmd("P", "C", ex)
        c_refused = False
    except ValueError:
        c_refused = True
    ok = a == common and b_ok and c_refused and R.CLAUDE == "/home/kobii/.local/bin/claude"
    return ok, f"A_exact={a == common} B_exact={b_ok} C_refused={c_refused} argv0={a[0]}"


def _write_packet(d, cands):
    p = Path(d) / "packet.json"
    p.write_text(json.dumps({"experiments": [{"candidates": cands}]}), encoding="utf-8")
    return p


def g_excludes():
    ex = R.excludes()
    real_ok = (len(ex) == 13 and all(p.startswith("/home/kobii/.claude/rules/") for p in ex)
               and "/home/kobii/.claude/rules/technical-failure-to-product-state.md" in ex
               and "/home/kobii/.claude/rules/scoped-side-effect-authority.md" in ex)
    cands = json.loads(R.PACKET.read_text(encoding="utf-8"))["experiments"][0]["candidates"]
    refused = {}
    with tempfile.TemporaryDirectory() as d:
        for name, cs in (("twelve", cands[:12]),
                         ("hooks", cands[:12] + [{"rule": "~/.claude/hooks/x.md", "bytes": 1, "sha256_lf": "0"}])):
            try:
                R.excludes(_write_packet(d, cs))
                refused[name] = False
            except ValueError:
                refused[name] = True
    return real_ok and all(refused.values()), f"real13={real_ok} refused={refused} first={ex[0] if ex else None}"


def g_env():
    keys = {"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SSE_PORT": "1234"}
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ.update(keys)
        env = R.child_env()
        stripped = not any(k in env for k in keys)
        kept = env.get("PATH") == os.environ.get("PATH") and env.get("HOME") == os.environ.get("HOME") \
            and "PATH" in env and "HOME" in env
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return stripped and kept, f"stripped={stripped} kept_PATH_HOME={kept}"


def g_session_parse():
    out = {}
    with tempfile.TemporaryDirectory() as d:
        def ok_exec(argv, **kw):
            return subprocess.CompletedProcess(argv, 0, stdout='progress line\n{"session_id": "sid-1", '
                                               '"num_turns": 3, "is_error": false}\n', stderr="")

        def garbage(argv, **kw):
            return subprocess.CompletedProcess(argv, 0, stdout="garbage", stderr="")

        def timeout(argv, **kw):
            raise subprocess.TimeoutExpired(argv, 1)

        def missing(argv, **kw):
            raise FileNotFoundError(argv[0])

        for name, fn in (("ok", ok_exec), ("garbage", garbage), ("timeout", timeout), ("missing", missing)):
            rec = {}
            sid = R.session(d, "P", "A", rec, [], exec_fn=fn)
            out[name] = (sid, rec)
    ok = (out["ok"][0] == "sid-1" and out["ok"][1]["claude_rc"] == 0 and out["ok"][1]["num_turns"] == 3
          and out["garbage"][0] == "" and out["garbage"][1].get("stdout_tail") == "garbage"
          and out["timeout"][1]["claude_rc"] == "timeout" and out["timeout"][1]["session_launched"] is True
          and out["missing"][1]["claude_rc"] == "exec-error" and out["missing"][1]["session_launched"] is False)
    return ok, {k: (v[0], v[1].get("claude_rc"), v[1].get("session_launched")) for k, v in out.items()}


def g_transcript():
    res = {}
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "projects"
        wt = "/r/runs/J-cwst1_oracle_bracket-B-a1"
        tdir = proj / "-r-runs-J-cwst1-oracle-bracket-B-a1"  # the measured encoding, written literally
        tdir.mkdir(parents=True)
        other = proj / "-somewhere-else"
        other.mkdir()
        (other / "sid-42.jsonl").write_text("{}\n")
        import time
        t0 = time.time()
        res["by_sid"] = R.find_transcript("sid-42", wt, t0, proj)
        f1 = tdir / "a.jsonl"
        f1.write_text("{}\n")
        res["by_tree"] = R.find_transcript("", wt, t0, proj)
        f2 = tdir / "b.jsonl"
        f2.write_text("{}\n")
        res["two"] = R.find_transcript("", wt, t0, proj)
        f2.unlink()
        os.utime(f1, (t0 - 100, t0 - 100))
        res["old"] = R.find_transcript("", wt, t0, proj)
        res["no_dir"] = R.find_transcript("", "/r/runs/other-run", t0, proj)
    ok = (res["by_sid"][0] is not None and res["by_sid"][0].name == "sid-42.jsonl"
          and res["by_tree"][0] is not None and res["by_tree"][0].name == "a.jsonl"
          and res["two"][0] is None and res["two"][1].startswith("ambiguous")
          and res["old"][0] is None
          and res["no_dir"] == (None, "no transcript for run tree"))
    return ok, {k: (v[0].name if v[0] else None, v[1]) for k, v in res.items()}


def g_metrics():
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "projects"
        (proj / "p").mkdir(parents=True)
        syn = {"type": "assistant", "requestId": "r", "message": {"id": "m", "model": "<synthetic>",
                                                                   "usage": {"input_tokens": 9}}}
        (proj / "p" / "syn.jsonl").write_text(json.dumps(syn) + "\n")
        a = R.metrics("syn", "/nowhere", 0, proj)
        (proj / "p" / "two.jsonl").write_text(fake_transcript_lines("two", extra_repeat=True))
        b = R.metrics("two", "/nowhere", 0, proj)
        c = R.metrics("missing", "/nowhere", 0, proj)
    ok = (a["state"] == "NO_CALLS" and a["total_context"] == 0
          and b["state"] == "MEASURED" and b["calls"] == 2
          and (b["first_call_context"], b["total_context"], b["output_tokens"]) == (25003, 50308, 100)
          and c["state"] == "UNMEASURED")
    return ok, f"synthetic={a['state']}/{a['total_context']} two={b.get('state')} calls={b.get('calls')} " \
               f"{b.get('first_call_context')}/{b.get('total_context')}/{b.get('output_tokens')} missing={c['state']}"


def g_grade_timeout():
    # the frozen bank's own timeout result (validate_bank.jgrade): the grade ran and failed -> valid, task fails
    def bank_timeout(wt, t):
        return {"rc": 124, "passed": 0, "total": 0, "control": (0, 0), "judgement": (0, 0),
                "fails": ["grade timed out after 300 s"], "summary": "grade timeout"}

    def raising(wt, t):
        raise subprocess.TimeoutExpired(["py"], 300)
    out = {}
    for name, fn in (("bank", bank_timeout), ("raised", raising)):
        g = R.grade(types.SimpleNamespace(jgrade=fn), "/x", {})
        rec = good_run(grade_rc=g["rc"], grade_summary=g["summary"], grade_passed=g["passed"],
                       grade_total=g["total"])
        out[name] = (g["rc"], K.run_valid(rec), K.task_pass(rec))
    ok = (out["bank"] == (124, (True, []), False)
          and out["raised"] == ("timeout", (False, ["grade did not run"]), False))
    return ok, f"{out}"


def _fake_run(leak, jgrade=None, arm="A", excl=()):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        tf = d / "task_fake.py"
        tf.write_text("# fake\n")
        calls, appended = [], []

        def exec_fn(argv, **kw):
            calls.append(argv)
            raise AssertionError("exec must not be called")
        bank = types.SimpleNamespace(fresh_tree=lambda rid, base: d / "wt", leak_scan=lambda wt: leak,
                                     drop_tree=lambda wt: True,
                                     jprepare=(lambda wt, t: []) if jgrade else _raiser("jprepare"),
                                     jgrade=jgrade or _raiser("jgrade"), git=_raiser("git"),
                                     JPROMPT="{module}")
        t = {"id": "J-fake", "rule": "rules/x.md", "file": tf, "module": "e1j/fake.py"}
        rec = R.one_run(bank, t, arm, 1, "0" * 40, excl=list(excl), cli_version="test", append=appended.append,
                        exec_fn=exec_fn, projects=d / "projects")
    return rec, calls, appended


def g_leak_abort():
    r1, c1, a1 = _fake_run((5, ["vault/programs/cognitive-economy/e1/bank/x.py"]))
    r2, c2, a2 = _fake_run((0, []))
    ok = (not c1 and not a1 and r1["session_launched"] is False and r1["valid"] is False
          and "bank file in run tree" in r1["invalid_reasons"] and r1["spend"] == 0 and "error" not in r1
          and not c2 and not a2 and r2["valid"] is False and "run tree listing empty" in r2["invalid_reasons"]
          and r2["spend"] == 0 and "error" not in r2)
    return ok, (f"leak: reasons={r1['invalid_reasons'][:2]} spend={r1['spend']} exec={len(c1)} start={len(a1)} | "
                f"empty: reasons={r2['invalid_reasons'][:2]} exec={len(c2)} start={len(a2)} "
                f"err={r1.get('error')}/{r2.get('error')}")


def g_precondition_green():
    def jgrade(wt, t, cleanup=True):
        return {"rc": 0, "summary": "E1J_PASS=8/8 control=4/4 judgement=4/4", "passed": 8, "total": 8,
                "fails": []}
    r, c, a = _fake_run((10, []), jgrade=jgrade)
    ok = not c and not a and r["valid"] is False and "precondition not red" in r["invalid_reasons"] \
        and "error" not in r and r["spend"] == 0
    return ok, f"reasons={r['invalid_reasons']} exec={len(c)} start={len(a)} err={r.get('error')}"


# ---- 02-02 Task 1 gates: contract primitives --------------------------------------------------------

E1_TASKS = [  # (id, rule, rule_bytes) in contract order: the real packet bytes (bank/index.json)
    ("J-gceg_product_page", "rules/generated-content-needs-an-evidence-gate.md", 6284),
    ("J-eaat_session_launch", "rules/effect-authority-across-transports.md", 6106),
    ("J-hfee_outbox", "rules/human-facing-external-effects.md", 5520),
    ("J-dcme_doc_status", "rules/documented-capability-must-be-executable.md", 5045),
    ("J-vpdt_verified_level", "rules/validation-planes-do-not-transfer.md", 3656),
    ("J-cpc_compact_row", "rules/capability-preserving-compaction.md", 3335),
    ("J-slai_pane_sleep", "rules/state-lifetime-and-incarnation.md", 3137),
    ("J-pert_freed_memory", "rules/post-effect-resource-truth.md", 3126),
    ("J-det_exit_all", "rules/durable-exit-transaction.md", 2830),
    ("J-pyt_test_gate", "rules/python/testing.md", 2516),
    ("J-cr_review_verdict", "rules/common/code-review.md", 1772),
]
E1_RULES = [r for _, r, _ in E1_TASKS]
R2_RULES = ["rules/technical-failure-to-product-state.md", "rules/scoped-side-effect-authority.md"]
ORDER_IDS = [i for i, _, _ in E1_TASKS]


def mk_order():
    """The 11 synthetic tasks, already in contract order."""
    return [{"id": i, "rule": r, "rule_bytes": b} for i, r, b in E1_TASKS]


def _refuses(fn, *a):
    try:
        fn(*a)
        return None
    except K.ContractError as e:
        return str(e)


def g_order():
    import random
    shuffled = mk_order()
    random.Random(7).shuffle(shuffled)
    got = [t["id"] for t in K.contract_order(shuffled, E1_RULES)]
    base = mk_order()
    bad = {
        "twelve": base + [{"id": "J-x", "rule": "rules/x.md", "rule_bytes": 1}],
        "r2_rule": base[:10] + [{"id": "J-tf", "rule": R2_RULES[0], "rule_bytes": 6932}],
        "same_rule": base[:10] + [dict(base[0], id="J-dup")],
        "same_bytes": base[:10] + [dict(base[10], rule_bytes=base[9]["rule_bytes"])],
        "not_allowed": base[:10] + [dict(base[10], rule="rules/other.md")],
    }
    allowed = {"twelve": E1_RULES + ["rules/x.md"]}
    refused = {k: _refuses(K.contract_order, v, allowed.get(k, E1_RULES)) for k, v in bad.items()}
    why = {"twelve": "MAX_TASKS", "r2_rule": "not an E1 rule", "same_rule": "two tasks",
           "same_bytes": "not total", "not_allowed": "not an E1 rule"}
    named = {k: bool(refused[k]) and why[k] in refused[k] for k in bad}
    ok = got == ORDER_IDS and shuffled[0]["id"] != ORDER_IDS[0] and all(named.values())
    return ok, f"order_ok={got == ORDER_IDS} first={got[0]} refused_with_reason={named}"


def g_alternation():
    got = [K.arm_order(i) for i in range(11)]
    want = [("A", "B") if i % 2 == 0 else ("B", "A") for i in range(11)]
    return got == want, f"0={got[0]} 1={got[1]} 10={got[10]}"


def g_decide():
    got = {(a, b): K.decide(a, b) for a in (True, False) for b in (True, False)}
    want = {(True, True): (K.RELOCATION_CANDIDATE, False), (True, False): (K.STAYS, False),
            (False, False): (K.NO_INFORMATION, False), (False, True): (K.NO_INFORMATION, True)}
    return got == want, f"{got}"


def g_posctl_fn():
    cases = [((100000, 85000), True), ((100000, 85001), False), ((100000, 120000), False),
             ((None, 85000), False), ((100000, None), False)]
    got = [K.positive_control_ok(*a) for a, _ in cases]
    return got == [w for _, w in cases], f"85000={got[0]} 85001={got[1]} 120000={got[2]} None={got[3:]}"


def g_harm_fn():
    S, R_, N = K.STAYS, K.RELOCATION_CANDIDATE, K.NO_INFORMATION
    cases = [([S] * 4, True), ([S] * 3 + [R_] * 5, False), ([S] * 3 + [R_] * 5 + [S], False), ([N] * 8, False)]
    got = [K.harm_fired(c) for c, _ in cases]
    return got == [w for _, w in cases], f"4losses={got[0]} 3in8={got[1]} 4th_in_9th={got[2]} noinfo8={got[3]}"


def g_spend_fn():
    due = [K.spend_stop_due(16_000_000, 1_000_000), K.spend_stop_due(16_000_001, 1_000_000),
           K.spend_stop_due(16_999_999, None), K.spend_stop_due(17_000_000, None)]
    reached = [K.spend_reached(16_999_999), K.spend_reached(17_000_000)]
    ok = due == [False, True, False, True] and reached == [False, True]
    return ok, (f"due(16.0M,1M)={due[0]} due(16.000001M,1M)={due[1]} due(16.999999M,None)={due[2]} "
                f"due(17M,None)={due[3]} reached(16.999999M)={reached[0]} reached(17M)={reached[1]}")


# ---- 02-02 Task 2 gates: replayable state machine ---------------------------------------------------

RULE_OF = {i: r for i, r, _ in E1_TASKS}
T0, T1, T2 = ORDER_IDS[:3]


def mk_run(task, arm, attempt, valid=True, passed=True, first=None, total=700_000):
    """A run record for the contract gates. first None -> 100,000 for A and 81,000 for B (gate 1's measured
    ~19,000 delta), so a script passes the positive control unless it sets first. An invalid run keeps a MEASURED
    transcript (its spend is measured) but its grade printed no E1J line."""
    if first is None:
        first = 100_000 if arm == "A" else 81_000
    over = {"run_id": K.run_id(task, arm, attempt), "task": task, "rule": RULE_OF.get(task, "rules/x.md"),
            "arm": arm, "attempt": attempt, "metrics.first_call_context": first, "metrics.total_context": total}
    if not passed:
        over.update(grade_rc=1, grade_passed=7, grade_summary="E1J_PASS=7/8 control=4/4 judgement=3/4")
    if not valid:
        over["grade_summary"] = "no E1J line"
    return good_run(**over)


def pair(i, a=True, b=True, a_first=None, b_first=None, total=700_000):
    """Both arms of the task at contract position i, valid, in that position's arm order."""
    spec = {"A": (a, a_first), "B": (b, b_first)}
    return [mk_run(ORDER_IDS[i], arm, 1, passed=spec[arm][0], first=spec[arm][1], total=total)
            for arm in K.arm_order(i)]


def noinfo(i):
    """The first arm of position i invalid twice."""
    arm = K.arm_order(i)[0]
    return [mk_run(ORDER_IDS[i], arm, 1, valid=False), mk_run(ORDER_IDS[i], arm, 2, valid=False)]


def pairs(spec):
    """spec: list of (i, kwargs) or (i, None) for a no-information task -> concatenated records."""
    out = []
    for i, kw in spec:
        out += noinfo(i) if kw is None else pair(i, **kw)
    return out


def nxt(records):
    return K.next_action(K.replay(mk_order(), records))


def simulate(order, script, limit=60):
    """Pure twin of plan 02-04's drive(): replay, append pair records for newly terminal tasks, next_action, run
    the scripted outcome for (task, arm, attempt), stop on STOP/HALTED. Reaching `limit` is itself a failure."""
    records = []
    for _ in range(limit):
        st = K.replay(order, records)
        for t in st["tasks"]:
            if t["status"] != "PENDING" and t["id"] not in st["pairs_recorded"]:
                records.append(K.pair_record(st, t["id"]))
        act = K.next_action(st)
        if act[0] != "RUN":
            if act[0] == "STOP":
                records.append(K.stop_record(st, act[1], R2_RULES))
            return records, act
        records.append(script(*act[1:]))
    raise RuntimeError(f"simulate: no stop within {limit} iterations")


def g_next_empty():
    got = nxt([])
    return got == ("RUN", "J-gceg_product_page", "A", 1), f"{got}"


def g_alternation_sm():
    r = [mk_run(T0, "A", 1)]
    s1 = nxt(r)
    r.append(mk_run(T0, "B", 1))
    s2 = nxt(r)
    r.append(mk_run(T1, "B", 1))
    s3 = nxt(r)
    ok = s1 == ("RUN", T0, "B", 1) and s2 == ("RUN", T1, "B", 1) and s3 == ("RUN", T1, "A", 1)
    return ok, f"{s1} {s2} {s3}"


def g_rerun_once():
    a1 = [mk_run(T0, "A", 1, valid=False)]
    s1 = nxt(a1)
    a2 = a1 + [mk_run(T0, "A", 2, valid=False)]
    st2 = K.replay(mk_order(), a2)
    s2 = K.next_action(st2)
    b_refused = _refuses(K.replay, mk_order(), a2 + [mk_run(T0, "B", 1)])
    b2 = [mk_run(T0, "A", 1), mk_run(T0, "B", 1, valid=False), mk_run(T0, "B", 2, valid=False)]
    st3 = K.replay(mk_order(), b2)
    ctl = nxt([mk_run(T0, "A", 1, valid=False), mk_run(T0, "A", 2)])
    t2, t3 = st2["tasks"][0], st3["tasks"][0]
    ok = (s1 == ("RUN", T0, "A", 2)
          and t2["status"] == K.NO_INFORMATION and "arm A" in t2["no_info_reason"]
          and s2 == ("RUN", T1, "B", 1) and b_refused is not None
          and t3["status"] == K.NO_INFORMATION and "arm B" in t3["no_info_reason"]
          and K.next_action(st3) == ("RUN", T1, "B", 1)
          and ctl == ("RUN", T0, "B", 1))
    return ok, (f"A-invalid1={s1} | A-invalid2: {t2['status']} '{t2['no_info_reason']}' next={s2} "
                f"B-after-refused={bool(b_refused)} | B-invalid2: {t3['status']} '{t3['no_info_reason']}' | "
                f"control A-invalid-then-valid={ctl}")


def g_one_pair():
    cases = {
        "attempt3": ([dict(mk_run(T0, "A", 1), attempt=3, run_id=f"{T0}-A-a3")], "attempt"),
        "duplicate": ([mk_run(T0, "A", 1, valid=False), mk_run(T0, "A", 1, valid=False)], "duplicate"),
        "after_decided": (pair(0) + [mk_run(T0, "A", 2)], "already terminal"),
        "later_task": ([mk_run(T1, "B", 1)], "still PENDING"),
        "second_arm_first": ([mk_run(T0, "B", 1)], "first arm"),
        "unknown_task": ([mk_run("J-nope", "A", 1)], "unknown task"),
        "bad_run_id": ([dict(mk_run(T0, "A", 1), run_id="x")], "run_id"),
        "non_object": ([["not", "a", "record"]], "not a JSON object"),
        "run_after_stop": (pair(0) + [{"kind": "stop", "condition": "SPEND_STOP"}] + pair(1),
                           "after the stop record"),
    }
    got = {k: _refuses(K.replay, mk_order(), recs) for k, (recs, _) in cases.items()}
    named = {k: bool(got[k]) and want in got[k] for k, (_, want) in cases.items()}
    control = _refuses(K.replay, mk_order(), pair(0) + pair(1) + noinfo(2) + pair(3))
    control_stop_last = _refuses(K.replay, mk_order(), pair(0) + [{"kind": "stop", "condition": "SPEND_STOP"}])
    ok = all(named.values()) and control is None and control_stop_last is None
    return ok, f"refused_with_reason={named} legal_set_refused={control}"


def g_posctl_sm():
    exact = nxt(pair(0, a_first=100_000, b_first=85_000))
    short = nxt(pair(0, a_first=100_000, b_first=85_001))
    later = nxt(pair(0) + pair(1, a_first=100_000, b_first=100_000))
    first_valid = nxt(noinfo(0) + pair(1, a_first=100_000, b_first=85_001))
    ok = (exact == ("RUN", T1, "B", 1) and short == ("STOP", K.POSITIVE_CONTROL_STOP)
          and later == ("RUN", T2, "A", 1) and first_valid == ("STOP", K.POSITIVE_CONTROL_STOP))
    return ok, f"delta15000={exact} delta14999={short} 2nd_pair_delta0={later} noinfo_then_14999={first_valid}"


def g_harm_sm():
    L = {"a": True, "b": False}
    three = pairs([(i, L) for i in range(3)])
    s3 = nxt(three)
    s4 = nxt(three + pair(3, **L))
    ninth = nxt(pairs([(i, L) for i in range(3)] + [(i, {}) for i in range(3, 8)] + [(8, L)]))
    st_ni = K.replay(mk_order(), pairs([(i, L) for i in range(3)] + [(3, None)] + [(i, {}) for i in range(4, 9)]
                                       + [(9, L)]))
    s_ni = K.next_action(st_ni)
    ok = (s3 == ("RUN", ORDER_IDS[3], "B", 1) and s4 == ("STOP", K.HARM_STOP)
          and ninth == ("RUN", "J-pyt_test_gate", "B", 1)
          and s_ni == ("RUN", "J-cr_review_verdict", "A", 1) and st_ni["losses_in_window"] == 3)
    return ok, (f"3losses={s3} 4losses={s4} loss_in_9th={ninth} noinfo_between: next={s_ni} "
                f"losses_in_window={st_ni['losses_in_window']} valid_pairs={len(st_ni['valid_pairs'])}")


def g_spend_sm():
    order = mk_order()
    base16 = pairs([(i, {"total": 1_000_000}) for i in range(8)])
    st = K.replay(order, base16)
    a = K.next_action(st)
    st_b = K.replay(order, base16 + [mk_run(ORDER_IDS[8], "A", 1, valid=False, total=1)])
    b = K.next_action(st_b)
    c = K.next_action(dict(st, spent=16_999_999, max_seen=None))
    c_ctl = K.next_action(dict(st, spent=16_999_999, max_seen=1_000_000))
    st_d = K.replay(order, base16 + [mk_run(ORDER_IDS[8], "A", 1, valid=False, total=1_500_000)])
    d = K.next_action(st_d)
    unk = good_run(run_id=K.run_id(T0, "A", 1), task=T0, rule=RULE_OF[T0], arm="A", attempt=1,
                   session_launched=True, metrics={"state": "UNMEASURED", "reason": "x"})
    e = nxt([unk])
    e_ctl = nxt([dict(unk, session_launched=False)])
    st_f = K.replay(order, pairs([(i, {"total": 800_000}) for i in range(11)]))
    f = K.next_action(st_f)
    ok = (a == ("RUN", ORDER_IDS[8], "A", 1) and st["spent"] == 16_000_000 and st["max_seen"] == 1_000_000
          and b == ("STOP", K.SPEND_STOP) and st_b["spent"] == 16_000_001 and st_b["max_seen"] == 1_000_000
          and c == ("RUN", ORDER_IDS[8], "A", 1) and c_ctl == ("STOP", K.SPEND_STOP)
          and d == ("STOP", K.SPEND_STOP) and st_d["spent"] == 17_500_000
          and e == ("STOP", K.SPEND_UNMEASURED) and e_ctl == ("RUN", T0, "A", 2)
          and f == ("STOP", K.ALL_DECIDED) and st_f["spent"] >= K.CAP)
    return ok, (f"16.0M/1M={a[0]} 16.000001M/1M={b} 16.999999M/None={c[0]} 16.999999M/1M={c_ctl[1]} "
                f"invalid-crossing={d[1]}@{st_d['spent']} unknown={e} unlaunched={e_ctl} "
                f"all-terminal@{st_f['spent']}={f[1]}")


MIXED = [(True, True), (True, False), (False, True), (False, False), (True, True), (True, False), (True, True),
         (True, True), (True, False), (True, True), (True, True)]


CLAUSE4 = {(True, True): ("RELOCATION_CANDIDATE", False), (True, False): ("STAYS", False),
           (False, True): ("NO_INFORMATION", True), (False, False): ("NO_INFORMATION", False)}


def g_all_decided_sm():
    recs = pairs([(i, {"a": a, "b": b}) for i, (a, b) in enumerate(MIXED)])
    st = K.replay(mk_order(), recs)
    act = K.next_action(st)
    fd = K.final_decisions(st, K.ALL_DECIDED, R2_RULES)
    bad = []
    for i, (a, b) in enumerate(MIXED):
        tid, rule = ORDER_IDS[i], E1_RULES[i]
        dec, flag = CLAUSE4[(a, b)]  # the literal table, not K.decide: an expectation must not be the subject
        e = fd.get(rule, {})
        if (e.get("decision"), e.get("b_pass_where_a_fails"), e.get("a_run"), e.get("b_run"), e.get("task")) != \
                (dec, flag, K.run_id(tid, "A", 1), K.run_id(tid, "B", 1), tid):
            bad.append(rule)
    r2 = [fd.get(r, {}).get("decision") for r in R2_RULES]
    ok = act == ("STOP", K.ALL_DECIDED) and not bad and r2 == [K.R2_CARRIED] * 2 and len(fd) == 13
    counts = {}
    for v in fd.values():
        counts[v["decision"]] = counts.get(v["decision"], 0) + 1
    return ok, f"next={act} mismatched={bad} r2={r2} n={len(fd)} counts={counts}"


def g_final():
    order = mk_order()
    L = {"a": True, "b": False}
    harm = K.final_decisions(K.replay(order, pairs([(i, L) for i in range(4)])), K.HARM_STOP, R2_RULES)
    pc = K.final_decisions(K.replay(order, pair(0, b_first=100_000)), K.POSITIVE_CONTROL_STOP, R2_RULES)
    sp = K.final_decisions(K.replay(order, pair(0) + pair(1, **L)), K.SPEND_STOP, R2_RULES)
    nf = K.final_decisions(K.replay(order, pair(0, a=False, b=True)), K.SPEND_STOP, R2_RULES)
    unknown = _refuses(K.final_decisions, K.replay(order, []), "NOT_A_CONDITION", R2_RULES)
    ok = (len(harm) == 13 and all(v["decision"] == K.STAYS for v in harm.values())
          and all(pc[r]["decision"] == K.STAYS and pc[r]["basis"] == "arms did not differ" for r in E1_RULES)
          and all(pc[r]["decision"] == K.R2_CARRIED for r in R2_RULES)
          and sp[E1_RULES[0]]["decision"] == K.RELOCATION_CANDIDATE and sp[E1_RULES[1]]["decision"] == K.STAYS
          and all(sp[r]["decision"] == K.UNDECIDED_STAYS for r in E1_RULES[2:])
          and nf[E1_RULES[0]]["decision"] == K.NO_INFORMATION and nf[E1_RULES[0]]["b_pass_where_a_fails"] is True
          and unknown is not None)
    return ok, (f"harm={sorted({v['decision'] for v in harm.values()})}/{len(harm)} "
                f"posctl={pc[E1_RULES[0]]['decision']}:{pc[E1_RULES[0]]['basis']!r} r2={pc[R2_RULES[0]]['decision']} "
                f"spend={[sp[r]['decision'] for r in E1_RULES[:3]]}.. "
                f"afail_bpass={nf[E1_RULES[0]]['decision']}/{nf[E1_RULES[0]]['b_pass_where_a_fails']} "
                f"unknown_condition_refused={bool(unknown)}")


def g_tokens_no_tiebreak():
    order = mk_order()
    s1 = pairs([(i, {"a": a, "b": b}) for i, (a, b) in enumerate(MIXED)])
    s2 = pairs([(i, {"a": a, "b": b, "a_first": 200_000, "b_first": 150_000, "total": 300_000})
                for i, (a, b) in enumerate(MIXED)])
    for r in s2:
        r["metrics"]["output_tokens"] = 99_999
    st1, st2 = K.replay(order, s1), K.replay(order, s2)
    d1 = [t.get("decision") for t in st1["tasks"]]
    d2 = [t.get("decision") for t in st2["tasks"]]
    f1 = {k: v["decision"] for k, v in K.final_decisions(st1, K.ALL_DECIDED, R2_RULES).items()}
    f2 = {k: v["decision"] for k, v in K.final_decisions(st2, K.ALL_DECIDED, R2_RULES).items()}
    differ = st1["spent"] != st2["spent"] and st1["first_pair"]["delta"] != st2["first_pair"]["delta"]
    ok = d1 == d2 and f1 == f2 and differ and st1["spent"] < K.CAP and st2["spent"] < K.CAP
    return ok, f"same_decisions={d1 == d2 and f1 == f2} tokens_differ={differ} spent={st1['spent']}/{st2['spent']}"


def g_halted_sm():
    recs = pair(0)
    ctl = nxt(recs)
    got = nxt(recs + [{"kind": "stop", "condition": K.SPEND_STOP}])
    ok = got == ("HALTED", K.SPEND_STOP) and ctl == ("RUN", T1, "B", 1)
    return ok, f"with_stop={got} without={ctl}"


def g_reconcile_sm():
    rid = K.run_id(T0, "A", 1)
    start = {"kind": "run_start", "run_id": rid, "task": T0, "rule": RULE_OF[T0], "arm": "A", "attempt": 1}
    a = nxt([start])
    b = nxt([start, mk_run(T0, "A", 1)])
    start2 = dict(start, run_id=K.run_id(T1, "B", 1), task=T1, arm="B")
    c = nxt(pair(0, b_first=100_000) + [start2])  # a pending start outranks the positive-control stop
    ok = a == ("RECONCILE", rid) and b == ("RUN", T0, "B", 1) and c == ("RECONCILE", start2["run_id"])
    return ok, f"start_only={a} start+run={b} before_posctl={c}"


def g_campaign():
    order = mk_order()
    calls = {"n": 0}

    def control(t, a, n):
        calls["n"] += 1
        return mk_run(t, a, n, total=1_000_000 if calls["n"] <= 16 else 999_999)

    scripts = {
        "all_pass": lambda t, a, n: mk_run(t, a, n),
        "all_loss": lambda t, a, n: mk_run(t, a, n, passed=(a == "A")),
        "no_delta": lambda t, a, n: mk_run(t, a, n, first=100_000),
        "million": lambda t, a, n: mk_run(t, a, n, total=1_000_000),
        "million_then_999999": control,
        "task2_A_invalid": lambda t, a, n: mk_run(t, a, n, valid=not (t == T2 and a == "A")),
    }
    out = {}
    for name, fn in scripts.items():
        recs, act = simulate(order, fn)
        stop = recs[-1] if recs and recs[-1].get("kind") == "stop" else {}
        prs = [r for r in recs if r["kind"] == "pair"]
        out[name] = {"act": act, "runs": sum(r["kind"] == "run" for r in recs), "pairs": len(prs),
                     "spent": stop.get("spent"), "over": stop.get("over_cap_by"),
                     "t2": next((p["status"] for p in prs if p["task"] == T2), None)}
    # red drill: the reactive gate (spend_reached alone) lets the 18th run start and carries the total past the cap
    saved = K.spend_stop_due
    calls["n"] = 0
    try:
        K.spend_stop_due = lambda spent, max_seen: K.spend_reached(spent)
        recs, _ = simulate(order, control)
        mutant = (sum(r["kind"] == "run" for r in recs), recs[-1].get("over_cap_by"))
    finally:
        K.spend_stop_due = saved
    o = out
    ok = (o["all_pass"]["act"] == ("STOP", K.ALL_DECIDED) and o["all_pass"]["runs"] == 22
          and o["all_pass"]["pairs"] == 11
          and o["all_loss"]["act"] == ("STOP", K.HARM_STOP) and o["all_loss"]["runs"] == 8
          and o["all_loss"]["pairs"] == 4
          and o["no_delta"]["act"] == ("STOP", K.POSITIVE_CONTROL_STOP) and o["no_delta"]["runs"] == 2
          and o["million"]["act"] == ("STOP", K.SPEND_STOP) and o["million"]["runs"] == 17
          and o["million"]["spent"] == 17_000_000 and o["million"]["over"] == 0
          and o["million_then_999999"]["act"] == ("STOP", K.SPEND_STOP)
          and o["million_then_999999"]["runs"] == 17 and o["million_then_999999"]["spent"] == 16_999_999
          and o["million_then_999999"]["over"] == 0
          and o["task2_A_invalid"]["act"] == ("STOP", K.ALL_DECIDED) and o["task2_A_invalid"]["t2"] == K.NO_INFORMATION
          and mutant == (18, 999_998))  # 16 x 1,000,000 + 2 x 999,999 = 17,999,998
    return ok, " ".join(f"{k}={v['act'][1]}/{v['runs']}r/{v['pairs']}p"
                        + (f"/spent={v['spent']}/over={v['over']}" if k.startswith("million") else "")
                        + (f"/t2={v['t2']}" if k == "task2_A_invalid" else "")
                        for k, v in o.items()) + f" reactive-gate-mutant={mutant[0]}r/over={mutant[1]}"


# ---- 02-01 review fixes ------------------------------------------------------------------------------

def g_cli_error():
    out = {}
    for name, over in (("exec_err", {"is_error": True, "subtype": "error_during_execution"}),
                       ("max_turns_red", {"is_error": True, "subtype": "error_max_turns", "grade_rc": 1,
                                          "grade_passed": 5, "grade_summary": "E1J_PASS=5/8 control=4/4 judgement=1/4"}),
                       ("ok", {"is_error": False, "subtype": "success"})):
        r = good_run(**over)
        out[name] = (K.run_valid(r), K.task_pass(r))
    # the session parser records subtype and the result head
    rec = {}
    long = "x" * 500

    def ex(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, stdout=json.dumps(
            {"session_id": "s1", "num_turns": 4, "is_error": True, "subtype": "error_during_execution",
             "result": long}) + "\n", stderr="")
    R.session("/tmp", "P", "A", rec, [], exec_fn=ex)
    parsed = (rec.get("subtype"), len(rec.get("result_head") or ""))
    ok = (out["exec_err"] == ((False, ["session ended in CLI error error_during_execution"]), True)
          and out["max_turns_red"] == ((True, []), False)
          and out["ok"] == ((True, []), True)
          and parsed == ("error_during_execution", 200))
    return ok, f"{out} parsed={parsed}"


def _transcript_with(path, tool_inputs, tool_results):
    lines = []
    for i, inp in enumerate(tool_inputs):
        lines.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": f"tu{i}", "name": "Bash", "input": inp}]}})
    for i, res in enumerate(tool_results):
        lines.append({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": f"tu{i}", "content": res}]}})
    Path(path).write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")


def g_bank_access():
    markers = R.bank_markers(BANK_PATH)
    frozen = (E1 / "BANK_FROZEN_AT").read_text(encoding="utf-8").strip()
    with tempfile.TemporaryDirectory() as d:
        dirty, clean = Path(d) / "dirty.jsonl", Path(d) / "clean.jsonl"
        _transcript_with(dirty, [{"command": "git show d68871742a:vault/programs/cognitive-economy/e1/x.py"}],
                         [[{"type": "text", "text": "CHECKS = ... E1J_PASS=8/8"}]])
        _transcript_with(clean, [{"command": "python3 -m pytest e1j/"}, {"file_path": "e1j/product_page.py"}],
                         ["2 passed", [{"type": "text", "text": "def render(): ..."}]])
        hits = R.bank_access(dirty, markers)
        none = R.bank_access(clean, markers)
    got = sorted({m for m, _ in hits})
    # 4 bank names + 11 task stems + the freeze prefix + BANK_FROZEN_AT
    ok = (frozen.startswith(R.BANK_COMMIT_PREFIX) and "task_gceg_product_page" in markers and len(markers) == 17
          and got == ["E1J_PASS", R.BANK_COMMIT_PREFIX] and none == []
          and any("git show d68871742a" in ex for _, ex in hits))
    return ok, f"markers={len(markers)} dirty={got} clean={none} excerpt={hits[0][1][:60] if hits else None}"


def g_bank_access_recorded():
    """The tracer path records bank_access ([] for the fake CLI's clean transcript) and validity is unchanged."""
    t, rec, fake, lines, gone = _tracer("REF", "B", "e1test-gceg-B-a1-ba")
    return rec.get("bank_access") == [] and rec.get("valid") is True, \
        f"bank_access={rec.get('bank_access')} valid={rec.get('valid')} err={rec.get('bank_access_error')}"


def g_arm_excludes():
    ex = R.excludes()
    refused = {}
    for name, arm, excl in (("A13", "A", ex), ("B0", "B", []), ("B12", "B", ex[:12]), ("A1", "A", ex[:1])):
        r, c, a = None, None, None
        try:
            r, c, a = _fake_run((10, []), arm=arm, excl=excl)
            refused[name] = False
        except ValueError:
            refused[name] = True
    legal = {}
    for name, arm, excl in (("A0", "A", []), ("B13", "B", ex)):
        try:
            legal[name] = R.check_arm_excludes(arm, excl) == list(excl)
        except ValueError:
            legal[name] = False
    # refusal precedes the worktree: fresh_tree must never be reached
    reached = []
    bank = types.SimpleNamespace(fresh_tree=lambda rid, base: reached.append(rid))
    try:
        R.one_run(bank, {"id": "J-f", "rule": "r", "file": __file__, "module": "m"}, "B", 1, "0" * 40, excl=[],
                  cli_version="t", append=_raiser("append"), exec_fn=_raiser("exec"))
        before_tree = False
    except ValueError:
        before_tree = not reached
    ok = all(refused.values()) and all(legal.values()) and before_tree
    return ok, f"refused={refused} legal={legal} refused_before_tree={before_tree}"


GATES = [
    ("V-E1-NO-MODEL", g_no_model),
    ("V-E1-TRACER-REF", g_tracer_ref),
    ("V-E1-TRACER-NAIVE", g_tracer_naive),
    ("V-E1-VALID", g_valid), ("V-E1-TASK-PASS", g_task_pass), ("V-E1-SPEND", g_spend),
    ("V-E1-RUN-ID", g_run_id), ("V-E1-ARGV", g_argv), ("V-E1-EXCLUDES", g_excludes), ("V-E1-ENV", g_env),
    ("V-E1-SESSION-PARSE", g_session_parse), ("V-E1-TRANSCRIPT", g_transcript), ("V-E1-METRICS", g_metrics),
    ("V-E1-GRADE-TIMEOUT", g_grade_timeout), ("V-E1-LEAK-ABORT", g_leak_abort),
    ("V-E1-PRECONDITION-GREEN", g_precondition_green),
    ("V-E1-ORDER", g_order), ("V-E1-ALTERNATION", g_alternation), ("V-E1-DECIDE", g_decide),
    ("V-E1-POSCTL-FN", g_posctl_fn), ("V-E1-HARM-FN", g_harm_fn), ("V-E1-SPEND-FN", g_spend_fn),
    ("V-E1-NEXT-EMPTY", g_next_empty), ("V-E1-ALTERNATION-SM", g_alternation_sm),
    ("V-E1-RERUN-ONCE", g_rerun_once), ("V-E1-ONE-PAIR", g_one_pair), ("V-E1-POSCTL-SM", g_posctl_sm),
    ("V-E1-HARM-SM", g_harm_sm), ("V-E1-SPEND-SM", g_spend_sm), ("V-E1-ALL-DECIDED-SM", g_all_decided_sm),
    ("V-E1-FINAL", g_final), ("V-E1-TOKENS-NO-TIEBREAK", g_tokens_no_tiebreak), ("V-E1-HALTED-SM", g_halted_sm),
    ("V-E1-RECONCILE-SM", g_reconcile_sm), ("V-E1-CAMPAIGN", g_campaign),
    ("V-E1-CLI-ERROR", g_cli_error), ("V-E1-BANK-ACCESS", g_bank_access),
    ("V-E1-BANK-ACCESS-RECORDED", g_bank_access_recorded), ("V-E1-ARM-EXCLUDES", g_arm_excludes),
    ("V-E1-NO-MODEL-END", g_no_model_end),  # keep last in every later plan
]
ALWAYS = ("V-E1-NO-MODEL", "V-E1-NO-MODEL-END")


def main(argv):
    names = [n for n, _ in GATES]
    unknown = [a for a in argv if a not in names]
    if unknown:
        print(f"unknown gate(s): {unknown}")
        return 1
    sel = set(argv) | set(ALWAYS) if argv else set(names)
    chosen = [(n, f) for n, f in GATES if n in sel]
    passes = 0
    for name, fn in chosen:
        try:
            ok, ev = fn()
        except Exception as e:  # a crashing gate is a FAIL, never a silent skip
            ok, ev = False, f"crashed: {type(e).__name__}: {e} | {traceback.format_exc().splitlines()[-3:]}"
        passes += bool(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name} {str(ev)[:300]}")
    print(f"E1_PASS={passes}/{len(chosen)}  threshold={len(chosen)}/{len(chosen)}")
    return 0 if passes == len(chosen) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
