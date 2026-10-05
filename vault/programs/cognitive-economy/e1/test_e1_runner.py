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
import shutil  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
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
    v = K.CLI_VERSION
    lines = [{"type": "user", "entrypoint": "sdk-cli", "sessionId": sid, "version": v,
              "message": {"role": "user", "content": "x"}},
             {"type": "assistant", "requestId": "req_1", "sessionId": sid, "version": v,
              "message": {"id": "msg_1", "role": "assistant", "model": K.MODEL, "usage": u1}},
             {"type": "assistant", "requestId": "req_2", "sessionId": sid, "version": v,
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
           "cli_versions_observed": [K.CLI_VERSION], "bank_drift_after": [],
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


def real_drift():
    """The production post-grade re-check over the real worktree bank (read-only git)."""
    return R.check_frozen_pin() + R.bank_drift(R.REPO, R._bank_rel(R.BANK_DIR, R.REPO), R.FROZEN)


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
                            projects=d / "projects", drift_fn=real_drift)
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
    ({"cli_versions_observed": ["2.1.290"]}, "cli version drift: transcript reports ['2.1.290'], want ['2.1.289']"),
    ({"cli_versions_observed": ["2.1.289", "2.1.290"]},
     "cli version drift: transcript reports ['2.1.289', '2.1.290'], want ['2.1.289']"),
    ({"cli_versions_observed": None}, "cli version drift: transcript reports None, want ['2.1.289']"),
    ({"bank_drift_after": ["edited since freeze: bank/x.py"]}, "bank drift during run"),
    ({"bank_drift_after": None}, "bank not re-checked after grade"),
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
    keys = {"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SSE_PORT": "1234",
            "DISABLE_AUTOUPDATER": "0"}
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ.update(keys)
        env = R.child_env()
        stripped = not any(k in env for k in keys if k != "DISABLE_AUTOUPDATER")
        no_update = env.get("DISABLE_AUTOUPDATER") == "1"
        kept = env.get("PATH") == os.environ.get("PATH") and env.get("HOME") == os.environ.get("HOME") \
            and "PATH" in env and "HOME" in env
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return stripped and kept and no_update, f"stripped={stripped} kept_PATH_HOME={kept} autoupdater_off={no_update}"


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


# ---- plan 02-03: pins, CLI, bank drift, records, preflight ------------------------------------------

import contextlib  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import re  # noqa: E402

REAL_CANDS = json.loads(R.PACKET.read_text(encoding="utf-8"))["experiments"][0]["candidates"]
OK_VERSION = "2.1.289 (Claude Code)"


def _rel(c):
    return c["rule"][len("~/.claude/"):] if c["rule"].startswith("~/.claude/") else c["rule"]


def _sha_lf(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def pin_world(d):
    """Temp home/.claude holding the 13 packet rule paths (synthetic bytes) and a packet pinning those bytes."""
    d = Path(d)
    home = d / "home"
    cands = []
    for c in REAL_CANDS:
        rel = _rel(c)
        f = home / ".claude" / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        data = f"# {rel}\nline two\nline three\n".encode()
        f.write_bytes(data)
        cands.append({"rule": c["rule"], "bytes": c["bytes"], "sha256_lf": _sha_lf(data)})
    return _write_packet(d, cands), home


def g_pins():
    with tempfile.TemporaryDirectory() as d:
        packet, home = pin_world(d)
        clean = R.check_pins(packet, home)
        rel = "rules/python/testing.md"
        f = home / ".claude" / rel
        orig = f.read_bytes()
        f.write_bytes(orig[:-2] + b"X\n")
        edited = R.check_pins(packet, home)
        f.unlink()
        deleted = R.check_pins(packet, home)
        f.write_bytes(orig.replace(b"\n", b"\r\n"))
        crlf = R.check_pins(packet, home)
    ok = (clean == (13, []) and edited[0] == 12 and len(edited[1]) == 1 and edited[1][0].startswith(rel + ": sha256")
          and deleted[0] == 12 and deleted[1] == [f"{rel}: unreadable (FileNotFoundError)"] and crlf == (13, []))
    return ok, f"clean={clean[0]}/{clean[1]} edited={edited} deleted={deleted} crlf={crlf}"


def g_cli():
    good = R.check_cli(R.CLAUDE, lambda: OK_VERSION)
    local = R.check_cli("/usr/local/bin/claude", _raiser("version_fn"))
    bare = R.check_cli("claude", _raiser("version_fn"))
    old = R.check_cli(R.CLAUDE, lambda: "2.1.113 (Claude Code)")

    def boom():
        raise OSError("no exec")
    unread = R.check_cli(R.CLAUDE, boom)
    ok = (good == ([], OK_VERSION) and len(local[0]) == 1 and "/usr/local/bin/claude" in local[0][0]
          and len(bare[0]) == 1 and "claude" in bare[0][0] and len(old[0]) == 1 and "2.1.113" in old[0][0]
          and unread[0] == ["version unreadable: OSError"])
    return ok, f"good={good} local={local} bare={bare} old={old} unread={unread}"


def _g(repo, *args):
    subprocess.run(["git", "-c", "user.name=e1", "-c", "user.email=e1@example.invalid", "-c", "core.hooksPath=/dev/null",
                    "-c", "commit.gpgsign=false", *args], cwd=str(repo), check=True, capture_output=True)


def drift_repo(d, bankless_freeze=False):
    """Temp git repo: bank/{task_a.py,_e1_common.py} committed; BANK_FROZEN_AT holding that commit (or, with
    bankless_freeze, an earlier commit with no bank/)."""
    repo = Path(d)
    _g(repo, "init", "-q")
    (repo / "README").write_text("r\n", encoding="utf-8")
    _g(repo, "add", "README")
    _g(repo, "commit", "-q", "-m", "first")
    first = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
    (repo / "bank").mkdir()
    (repo / "bank" / "task_a.py").write_text("A = 1\n", encoding="utf-8")
    (repo / "bank" / "_e1_common.py").write_text("C = 1\n", encoding="utf-8")
    _g(repo, "add", "bank")
    _g(repo, "commit", "-q", "-m", "freeze")
    h = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
    frozen = repo / "BANK_FROZEN_AT"
    frozen.write_text((first if bankless_freeze else h) + "\n", encoding="utf-8")
    return repo, frozen


def g_bank_drift():
    res = {}

    def case(name, mutate=None, bankless=False):
        with tempfile.TemporaryDirectory() as d:
            repo, frozen = drift_repo(d, bankless)
            if mutate:
                mutate(repo, frozen)
            res[name] = R.bank_drift(repo, "bank", frozen)

    def edit(repo, _f):
        (repo / "bank" / "task_a.py").write_text("A = 2\n", encoding="utf-8")

    def edit_commit(repo, f):
        edit(repo, f)
        _g(repo, "commit", "-q", "-am", "edit")

    case("clean")
    case("edited", edit)
    case("edited_committed", edit_commit)
    case("added", lambda r, f: (r / "bank" / "task_zz.py").write_text("Z = 1\n", encoding="utf-8"))

    def pyc(r, _f):
        (r / "bank" / "__pycache__").mkdir()
        (r / "bank" / "__pycache__" / "x.pyc").write_bytes(b"\0")
    case("pycache_only", pyc)
    case("deleted", lambda r, f: (r / "bank" / "_e1_common.py").unlink())
    case("frozen_absent", lambda r, f: f.unlink())
    case("not_a_hash", lambda r, f: f.write_text("not-a-hash\n", encoding="utf-8"))
    case("zeros", lambda r, f: f.write_text("0" * 40 + "\n", encoding="utf-8"))
    case("bankless", bankless=True)
    want = {"clean": None, "pycache_only": None,
            "edited": "edited since freeze: bank/task_a.py", "edited_committed": "edited since freeze: bank/task_a.py",
            "added": "added since freeze: bank/task_zz.py", "deleted": "missing since freeze: bank/_e1_common.py",
            "frozen_absent": "BANK_FROZEN_AT missing", "not_a_hash": "BANK_FROZEN_AT malformed",
            "zeros": "not in this repository", "bankless": "holds no bank"}
    ok = all((res[k] == []) if w is None else (len(res[k]) == 1 and w in res[k][0]) for k, w in want.items())
    return ok, " ".join(f"{k}={res[k]}" for k in want)


def g_records_read():
    with tempfile.TemporaryDirectory() as d:
        absent = R.read_records(Path(d) / "results.jsonl")
        f = Path(d) / "r.jsonl"
        f.write_text('{"kind": "run"}\n\n   \n{"kind": "stop"}\n', encoding="utf-8")
        blanks = R.read_records(f)
        g = Path(d) / "bad.jsonl"
        g.write_text('{"kind": "run"}\n[1, 2]\n', encoding="utf-8")
        try:
            R.read_records(g)
            bad = "no error"
        except K.ContractError as e:
            bad = str(e)
    ok = absent == [] and blanks == [{"kind": "run"}, {"kind": "stop"}] and bad == "results line 2 malformed"
    return ok, f"absent={absent} blanks={blanks} bad={bad!r}"


FAKE_BASE = "78ba9e7414" + "c" * 30
FAKE_FROZEN = "ab" * 20


def fake_world(tmp, **faults):
    """-> preflight kwargs for an all-good world built under tmp; each fault flips exactly one input."""
    tmp = Path(tmp)
    packet, home = pin_world(tmp)
    pk = json.loads(packet.read_text(encoding="utf-8"))["experiments"][0]["candidates"]
    e1 = sorted((c for c in pk if _rel(c) not in R.EXCLUDED_BY_R2), key=lambda c: -c["bytes"])
    tasks = [{"id": f"J-t{i:02d}", "rule": _rel(c), "module": f"m{i}.py", "file": tmp / f"task_t{i:02d}.py"}
             for i, c in enumerate(e1)]
    bank_dir = tmp / "bank"
    bank_dir.mkdir()
    items = [{"order": i + 1, "id": t["id"], "rule": t["rule"], "rule_bytes": c["bytes"], "sha256_lf": c["sha256_lf"]}
             for i, (t, c) in enumerate(zip(tasks, e1))]
    if faults.get("index_swap"):
        items[3], items[4] = items[4], items[3]
    if faults.get("index_ten"):
        items = items[:10]
    idx = {"bank": "x", "base": FAKE_BASE, "missing": ["rules/x.md"] if faults.get("index_missing") else [],
           "tasks": items}
    if not faults.get("index_absent"):
        (bank_dir / "index.json").write_text(json.dumps(idx), encoding="utf-8")

    def jbase():
        if faults.get("base_raise"):
            raise SystemExit(f"BASE {FAKE_BASE} contains the bank or its plans: ['bank/x']")
        return FAKE_BASE
    bank = types.SimpleNamespace(HERE=bank_dir, tasks=lambda: [dict(t) for t in tasks], jbase=jbase)
    if not faults.get("no_freeze"):
        bank.freeze_check = (lambda *a: ["x"]) if faults.get("freeze_bad") else (lambda *a: [])
    frozen = tmp / "BANK_FROZEN_AT"
    frozen.write_text(FAKE_FROZEN + "\n", encoding="utf-8")
    if faults.get("pin_edit"):
        f = home / ".claude" / "rules/common/code-review.md"
        f.write_bytes(f.read_bytes() + b"x")
    results = tmp / "results.jsonl"
    if faults.get("results_malformed"):
        results.write_text('{"kind": "run_start", "run_id": "r"}\nnot json\n', encoding="utf-8")
    if faults.get("results_attempt3"):
        t0 = tasks[0]["id"]
        results.write_text(json.dumps({"kind": "run", "run_id": f"{t0}-A-a3", "task": t0, "arm": "A",
                                       "attempt": 3}) + "\n", encoding="utf-8")
    version = "2.1.113 (Claude Code)" if faults.get("version_old") else OK_VERSION
    drift = ["edited since freeze: bank/task_a.py"] if faults.get("drift") else []
    return dict(bank_dir=bank_dir, bank=bank, repo=R.REPO, frozen=frozen, results=results, packet=packet, home=home,
                cli_path=R.CLAUDE, version_fn=lambda: version, drift_fn=lambda *a, **k: list(drift),
                packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(), frozen_hash=FAKE_FROZEN)


CHECK_NAMES = ["cli", "packet", "pins", "excludes", "bank", "bank_drift", "freeze_check", "base", "index", "results"]

PREFLIGHT_FAULTS = [
    ("freeze_bad", "freeze_check"), ("no_freeze", "freeze_check"), ("base_raise", "base"),
    ("index_absent", "index"), ("index_swap", "index"), ("index_missing", "index"), ("index_ten", "index"),
    ("pin_edit", "pins"), ("version_old", "cli"), ("results_malformed", "results"),
    ("results_attempt3", "results"), ("drift", "bank_drift"),
]


def g_preflight_ok():
    with tempfile.TemporaryDirectory() as d:
        checks = R.preflight(**fake_world(d))
    ok = [c[0] for c in checks] == CHECK_NAMES and all(c[1] for c in checks)
    return ok, " ".join(f"{n}:{'OK' if o else 'REFUSED'}:{det[:40]}" for n, o, det in checks)


def g_preflight_refusals():
    got = {}
    for fault, want in PREFLIGHT_FAULTS:
        with tempfile.TemporaryDirectory() as d:
            checks = R.preflight(**fake_world(d, **{fault: True}))
        refused = [n for n, o, _ in checks if not o]
        names = [c[0] for c in checks]
        got[fault] = (refused, names == CHECK_NAMES, next((det for n, o, det in checks if n == want), "")[:60])
    ok = all(got[f][0] == [w] and got[f][1] for f, w in PREFLIGHT_FAULTS)
    return ok, " ".join(f"{f}>{','.join(got[f][0])}" for f, _ in PREFLIGHT_FAULTS)


def g_preflight_nobank():
    with tempfile.TemporaryDirectory() as d:
        w = fake_world(d)
        empty = Path(d) / "empty"
        empty.mkdir()
        w.update(bank_dir=empty, bank=None)
        try:
            checks = R.preflight(**w)
            esc = None
        except BaseException as e:  # the gate's subject: nothing may escape
            checks, esc = [], f"{type(e).__name__}: {e}"
    st = {n: (o, det) for n, o, det in checks}
    ok = (esc is None and [c[0] for c in checks] == CHECK_NAMES and st["bank"][0] is False
          and "no validate_bank.py" in st["bank"][1]
          and all(st[n] == (False, "bank not loaded") for n in ("freeze_check", "base", "index", "results"))
          and all(st[n][0] for n in ("cli", "pins", "excludes", "bank_drift")))
    return ok, f"escaped={esc} " + " ".join(f"{n}:{'OK' if st[n][0] else 'REFUSED'}:{st[n][1][:40]}" for n in st)


def g_per_run_checks():
    out = {}
    for fault in (None, "pin_edit", "drift", "version_old"):
        with tempfile.TemporaryDirectory() as d:
            w = fake_world(d, **({fault: True} if fault else {}))
            out[fault or "good"] = R.per_run_checks(bank_rel="bank", frozen=w["frozen"], packet=w["packet"],
                                                    home=w["home"], version_fn=w["version_fn"],
                                                    drift_fn=w["drift_fn"], packet_sha256=w["packet_sha256"],
                                                    frozen_hash=w["frozen_hash"])
    ok = (out["good"] == {"problems": [], "cli_version": OK_VERSION}
          and all(len(out[f]["problems"]) == 1 for f in ("pin_edit", "drift", "version_old")))
    return ok, " ".join(f"{k}={v['problems']}" for k, v in out.items())


def g_cli_preflight():
    with tempfile.TemporaryDirectory() as d:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = R.cmd_preflight(["--bank", d], version_fn=lambda: OK_VERSION)
        lines = buf.getvalue().splitlines()
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        rc2 = R.cmd_preflight(["--bogus"])
    ok = (rc == 1 and any(ln.startswith("CHECK bank REFUSED") for ln in lines) and bool(lines)
          and lines[-1].startswith("PREFLIGHT REFUSED") and rc2 == 2)
    return ok, f"rc={rc} last={lines[-1] if lines else None!r} bank={[ln[:60] for ln in lines if ' bank ' in ln]} bogus_rc={rc2}"


# ---- 02-04 Task 1 gates: the durable campaign loop ------------------------------------------------------

def _no_reconcile(start):
    raise AssertionError(f"reconcile_fn called for {start.get('run_id')}")


class Loop:
    """One drive() call with recorders: run_fn calls, check_fn calls, the event order and commit subjects."""

    def __init__(self, results, script, *, problems_at=None, commit_raises_at=None, reconcile_fn=_no_reconcile,
                 spent_log=False):
        self.results, self.script = Path(results), script
        self.calls, self.events, self.subjects, self.lines, self.spent_before = [], [], [], [], []
        self.problems_at, self.commit_raises_at, self.reconcile_fn, self.spent_log = (
            problems_at, commit_raises_at, reconcile_fn, spent_log)
        self.checks = 0

    def run_fn(self, task, arm, attempt, ctx):
        self.events.append("run")
        if self.spent_log:
            st = K.replay(mk_order(), R.read_records(self.results))
            self.spent_before.append((st["spent"], st["max_seen"]))
        self.calls.append((task, arm, attempt))
        return self.script(task, arm, attempt)

    def check_fn(self):
        self.checks += 1
        self.events.append("check")
        if self.problems_at is not None and self.checks == self.problems_at:
            return {"problems": ["pins: rules/python/testing.md sha256 changed"], "cli_version": OK_VERSION}
        return {"problems": [], "cli_version": OK_VERSION}

    def commit_fn(self, subject):
        if self.commit_raises_at is not None and len(self.subjects) + 1 == self.commit_raises_at:
            raise RuntimeError("git commit failed: simulated")
        self.subjects.append(subject)

    def drive(self, max_pairs=None):
        return R.drive(mk_order(), results=self.results, run_fn=self.run_fn, check_fn=self.check_fn,
                       reconcile_fn=self.reconcile_fn, commit_fn=self.commit_fn, max_pairs=max_pairs,
                       r2_rules=R2_RULES, out=self.lines.append)

    def records(self):
        return R.read_records(self.results)


def _kinds(recs):
    return {k: sum(r.get("kind") == k for r in recs) for k in ("run", "pair", "stop", "refusal", "run_start")}


def _expected_calls(n_tasks):
    return [(ORDER_IDS[i], arm, 1) for i in range(n_tasks) for arm in K.arm_order(i)]


def g_loop_all_decided():
    with tempfile.TemporaryDirectory() as d:
        lp = Loop(Path(d) / "results.jsonl", lambda t, a, n: mk_run(t, a, n))
        rc = lp.drive()
        recs = lp.records()
    last = recs[-1] if recs else {}
    fd = last.get("final_decisions", {})
    ok = (rc == (0, K.ALL_DECIDED) and _kinds(recs) == {"run": 22, "pair": 11, "stop": 1, "refusal": 0,
                                                         "run_start": 0}
          and last.get("kind") == "stop" and last.get("condition") == K.ALL_DECIDED
          and sum(v["decision"] == K.RELOCATION_CANDIDATE for v in fd.values()) == 11
          and [fd.get(r, {}).get("decision") for r in R2_RULES] == [K.R2_CARRIED] * 2
          and len(lp.subjects) == 12 and lp.calls == _expected_calls(11)
          and lp.events == ["check", "run"] * 22 and lp.checks == 22)
    return ok, (f"rc={rc} kinds={_kinds(recs)} last={last.get('kind')}/{last.get('condition')} "
                f"reloc={sum(v['decision'] == K.RELOCATION_CANDIDATE for v in fd.values())} "
                f"r2={[fd.get(r, {}).get('decision') for r in R2_RULES]} commits={len(lp.subjects)} "
                f"checks={lp.checks} check_before_every_run={lp.events == ['check', 'run'] * 22} "
                f"first_calls={lp.calls[:4]}")


def g_loop_harm():
    with tempfile.TemporaryDirectory() as d:
        lp = Loop(Path(d) / "r.jsonl", lambda t, a, n: mk_run(t, a, n, passed=(a == "A")))
        rc = lp.drive()
        recs = lp.records()
    with tempfile.TemporaryDirectory() as d:
        three = set(ORDER_IDS[:3])
        ctl = Loop(Path(d) / "r.jsonl", lambda t, a, n: mk_run(t, a, n, passed=(a == "A" or t not in three)))
        rc_ctl = ctl.drive()
        crecs = ctl.records()
    stop = recs[-1] if recs else {}
    decs = [v["decision"] for v in stop.get("final_decisions", {}).values()]
    ok = (rc == (3, K.HARM_STOP) and len(lp.calls) == 8 and _kinds(recs)["pair"] == 4
          and stop.get("condition") == K.HARM_STOP and decs == [K.STAYS] * 13
          and rc_ctl == (0, K.ALL_DECIDED) and len(ctl.calls) == 22
          and crecs[-1].get("losses_in_window") == 3)
    return ok, (f"all_loss={rc}/{len(lp.calls)}r/{_kinds(recs)['pair']}p stays={decs.count(K.STAYS)}/{len(decs)} "
                f"control_3_losses={rc_ctl}/{len(ctl.calls)}r losses_in_window={crecs[-1].get('losses_in_window')}")


def g_loop_spend():
    out = {}
    for name, totals in (("million", None), ("million_then_999999", "ctl")):
        with tempfile.TemporaryDirectory() as d:
            cnt = {"n": 0}

            def script(t, a, n, totals=totals, cnt=cnt):
                cnt["n"] += 1
                return mk_run(t, a, n, total=999_999 if totals == "ctl" and cnt["n"] > 16 else 1_000_000)
            lp = Loop(Path(d) / "r.jsonl", script, spent_log=True)
            rc = lp.drive()
            stop = lp.records()[-1]
        out[name] = (rc, len(lp.calls), lp.spent_before[16] if len(lp.spent_before) > 16 else None,
                     stop.get("spent"), stop.get("over_cap_by"), stop.get("max_seen"))
    # red drill: with the reactive gate (spend_reached alone) the control script starts an 18th run
    saved = K.spend_stop_due
    try:
        K.spend_stop_due = lambda spent, max_seen: K.spend_reached(spent)
        with tempfile.TemporaryDirectory() as d:
            cnt = {"n": 0}

            def script2(t, a, n):
                cnt["n"] += 1
                return mk_run(t, a, n, total=999_999 if cnt["n"] > 16 else 1_000_000)
            mut = Loop(Path(d) / "r.jsonl", script2)
            mut.drive()
            mutant = (len(mut.calls), mut.records()[-1].get("over_cap_by"))
    finally:
        K.spend_stop_due = saved
    m, c = out["million"], out["million_then_999999"]
    ok = (m[0] == (3, K.SPEND_STOP) and m[1] == 17 and m[2] == (16_000_000, 1_000_000) and m[3] == 17_000_000
          and m[4] == 0
          and c[0] == (3, K.SPEND_STOP) and c[1] == 17 and c[3] == 16_999_999 and c[4] == 0 and c[5] == 1_000_000
          and c[3] + c[5] > K.CAP and mutant == (18, 999_998))
    return ok, (f"million={m[0][1]}/{m[1]}r 17th_starts_at={m[2]} spent={m[3]} over={m[4]} | "
                f"16x1M+999999={c[0][1]}/{c[1]}r spent={c[3]} over={c[4]} max_seen={c[5]} "
                f"18th_withheld={c[3]}+{c[5]}>{K.CAP} | reactive-gate-mutant={mutant[0]}r/over={mutant[1]}")


def g_loop_posctl():
    out = {}
    for name, b0 in (("delta14999", 100_000 - 14_999), ("delta15000", 100_000 - 15_000)):
        with tempfile.TemporaryDirectory() as d:
            lp = Loop(Path(d) / "r.jsonl",
                      lambda t, a, n, b0=b0: mk_run(t, a, n, first=b0 if (t, a) == (T0, "B") else None))
            rc = lp.drive()
            recs = lp.records()
        pr = next((r for r in recs if r.get("kind") == "pair"), {})
        out[name] = (rc, len(lp.calls), pr.get("used"), (pr.get("positive_control") or {}).get("ok"))
    s, c = out["delta14999"], out["delta15000"]
    ok = (s[0] == (3, K.POSITIVE_CONTROL_STOP) and s[1] == 2 and s[2] is False and s[3] is False
          and c[1] >= 3 and c[0] == (0, K.ALL_DECIDED) and c[2] is True and c[3] is True)
    return ok, (f"delta14999={s[0][1]}/{s[1]}r used={s[2]} pc_ok={s[3]} | "
                f"delta15000={c[0][1]}/{c[1]}r used={c[2]} pc_ok={c[3]}")


def g_loop_noinfo():
    with tempfile.TemporaryDirectory() as d:
        lp = Loop(Path(d) / "r.jsonl", lambda t, a, n: mk_run(t, a, n, valid=not (t == T0 and a == "A")))
        rc = lp.drive()
        recs = lp.records()
    pr = next((r for r in recs if r.get("kind") == "pair" and r.get("task") == T0), {})
    ok = (pr.get("decision") == K.NO_INFORMATION and "arm A" in str(pr.get("no_info_reason"))
          and (T0, "B", 1) not in lp.calls and lp.calls[:3] == [(T0, "A", 1), (T0, "A", 2), (T1, "B", 1)]
          and rc == (0, K.ALL_DECIDED))
    return ok, (f"pair0={pr.get('decision')} reason={pr.get('no_info_reason')!r} "
                f"t0_B_called={(T0, 'B', 1) in lp.calls} calls={lp.calls[:3]} end={rc}")


def g_loop_resume():
    with tempfile.TemporaryDirectory() as d:
        res = Path(d) / "r.jsonl"
        one = Loop(res, lambda t, a, n: mk_run(t, a, n))
        rc1 = one.drive(max_pairs=1)
        b1 = res.read_bytes()
        k1 = _kinds(R.read_records(res))
        two = Loop(res, lambda t, a, n: mk_run(t, a, n))
        rc2 = two.drive()
        b2 = res.read_bytes()
        k2 = _kinds(R.read_records(res))
    ok = (rc1 == (4, "PAUSED") and k1["pair"] == 1 and k1["stop"] == 0 and one.calls == _expected_calls(1)
          and two.calls[:1] == [(T1, "B", 1)] and not any(c[0] == T0 for c in two.calls)
          and rc2 == (0, K.ALL_DECIDED) and b2.startswith(b1) and len(b2) > len(b1)
          and k2["pair"] == 11 and k2["run"] == 22)
    return ok, (f"first={rc1} kinds={k1} | resume first_call={two.calls[:1]} t0_rerun={any(c[0] == T0 for c in two.calls)} "
                f"end={rc2} prefix={b2.startswith(b1)} kinds={k2}")


def g_loop_halted():
    with tempfile.TemporaryDirectory() as d:
        res = Path(d) / "r.jsonl"
        recs, act = simulate(mk_order(), lambda t, a, n: mk_run(t, a, n, passed=(a == "A")))
        for r in recs:
            R.append_record(res, r)
        before = res.read_bytes()

        def boom(*a, **k):
            raise AssertionError("called after a stop record")
        lines = []
        rc = R.drive(mk_order(), results=res, run_fn=boom, check_fn=boom, reconcile_fn=boom, commit_fn=boom,
                     r2_rules=R2_RULES, out=lines.append)
        after = res.read_bytes()
    ok = act == ("STOP", K.HARM_STOP) and rc == (3, K.HARM_STOP) and before == after and lines == [
        f"E1-RUN HALTED {K.HARM_STOP}"]
    return ok, f"rc={rc} unchanged={before == after} out={lines}"


def g_loop_refusal():
    with tempfile.TemporaryDirectory() as d:
        res = Path(d) / "r.jsonl"
        lp = Loop(res, lambda t, a, n: mk_run(t, a, n), problems_at=3)
        rc = lp.drive()
        recs = lp.records()
        ref = [r for r in recs if r.get("kind") == "refusal"]
        again = Loop(res, lambda t, a, n: mk_run(t, a, n))
        rc2 = again.drive()
    ok = (rc == (1, "REFUSED") and len(lp.calls) == 2 and len(ref) == 1
          and ref[0].get("before") == K.run_id(T1, "B", 1) and "testing.md" in str(ref[0].get("problems"))
          and recs[-1].get("kind") == "refusal" and lp.subjects[-1] == f"data(e1): refusal before {K.run_id(T1, 'B', 1)}"
          and again.calls[:1] == [(T1, "B", 1)] and rc2 == (0, K.ALL_DECIDED))
    return ok, (f"rc={rc} runs={len(lp.calls)} refusal={ref[0] if ref else None} commits={lp.subjects} | "
                f"resume first={again.calls[:1]} end={rc2}")


def _reconcile_case(d, with_transcript, start_extra=None):
    d = Path(d)
    rid = K.run_id(T0, "A", 1)
    wt = d / "runs" / rid
    projects = d / "projects"
    projects.mkdir()
    drops = []
    if with_transcript:
        wt.mkdir(parents=True)
        pd = projects / R._norm(wt)
        pd.mkdir()
        (pd / "s.jsonl").write_text(fake_transcript_lines("s"), encoding="utf-8")
    bank = types.SimpleNamespace(HERE=BANK_PATH, drop_tree=lambda p: drops.append(str(p)) or True)
    res = d / "r.jsonl"
    R.append_record(res, {"kind": "run_start", "run_id": rid, "task": T0, "rule": RULE_OF[T0], "arm": "A",
                          "attempt": 1, "base": "0" * 40, "wt": str(wt), "started": "2026-10-05T00:00:00+00:00",
                          "started_epoch": 0.0, "cli_version": OK_VERSION, "excluded": [], **(start_extra or {})})
    lp = Loop(res, lambda t, a, n: mk_run(t, a, n),
              reconcile_fn=lambda start: R.reconcile(bank, start, projects=projects))
    rc = lp.drive()
    recs = lp.records()
    rec = next((r for r in recs if r.get("kind") == "run" and r.get("run_id") == rid), {})
    return rc, rec, lp, drops, str(wt)


def g_loop_reconcile():
    with tempfile.TemporaryDirectory() as d:
        rc, rec, lp, drops, wt = _reconcile_case(d, True)
    with tempfile.TemporaryDirectory() as d:
        rc2, rec2, lp2, drops2, _ = _reconcile_case(d, False)
    ok = (rec.get("error") == R.INTERRUPTED and rec.get("valid") is False
          and "grade did not run" in rec.get("invalid_reasons", []) and rec.get("spend") == 50308
          and rec.get("worktree_removed") is True and drops == [wt]
          and lp.calls[:1] == [(T0, "A", 2)] and rc == (0, K.ALL_DECIDED)
          and rec2.get("spend") is None and rec2.get("worktree_removed") is True and drops2 == []
          and rc2 == (3, K.SPEND_UNMEASURED) and lp2.calls == [])
    return ok, (f"with_transcript: valid={rec.get('valid')} spend={rec.get('spend')} err={rec.get('error')!r} "
                f"dropped={len(drops)} next={lp.calls[:1]} end={rc} | no_transcript: spend={rec2.get('spend')} "
                f"metrics={(rec2.get('metrics') or {}).get('state')} end={rc2} runs={len(lp2.calls)}")


def g_loop_commit_fail():
    with tempfile.TemporaryDirectory() as d:
        res = Path(d) / "r.jsonl"
        lp = Loop(res, lambda t, a, n: mk_run(t, a, n), commit_raises_at=1)
        rc = lp.drive()
        recs = lp.records()
        again = Loop(res, lambda t, a, n: mk_run(t, a, n))
        rc2 = again.drive()
        recs2 = again.records()
    p0 = [r for r in recs2 if r.get("kind") == "pair" and r.get("task") == T0]
    ok = (rc == (1, "COMMIT_FAILED") and recs[-1].get("kind") == "pair" and recs[-1].get("task") == T0
          and any(x.startswith("E1-RUN COMMIT_FAILED") for x in lp.lines)
          and len(p0) == 1 and rc2 == (0, K.ALL_DECIDED) and again.calls[:1] == [(T1, "B", 1)]
          and again.subjects[:1] == [f"data(e1): pair 2 {T1} {K.RELOCATION_CANDIDATE}"])
    return ok, (f"rc={rc} last={recs[-1].get('kind')}/{recs[-1].get('task')} | resume end={rc2} "
                f"t0_pair_records={len(p0)} first_commit={again.subjects[:1]}")


# ---- 02-04 Task 2 gates: commit per pair, `plan` and `run` -------------------------------------------------

def _commit_repo(d, hook_rewrites=False):
    repo = Path(d) / "repo"
    repo.mkdir()
    _g(repo, "init", "-q")
    for k, v in (("user.name", "e1"), ("user.email", "e1@example.invalid"), ("commit.gpgsign", "false"),
                 ("core.hooksPath", "/dev/null")):
        _g(repo, "config", k, v)
    (repo / "results.jsonl").write_text('{"kind": "run_start"}\n', encoding="utf-8")
    (repo / "other.txt").write_text("o\n", encoding="utf-8")
    _g(repo, "add", "results.jsonl")
    _g(repo, "commit", "-q", "-m", "first")
    if hook_rewrites:
        hooks = Path(d) / "hooks"
        hooks.mkdir()
        h = hooks / "commit-msg"
        h.write_text("#!/bin/sh\nsed -i '1s/.*/data(e1): rewritten/' \"$1\"\n", encoding="utf-8")
        h.chmod(0o755)
        _g(repo, "config", "core.hooksPath", str(hooks))
    with open(repo / "results.jsonl", "a", encoding="utf-8") as fh:
        fh.write('{"kind": "pair"}\n')
    _g(repo, "add", "other.txt")
    return repo


def _git_out(repo, *args):
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True).stdout


def g_commit():
    subject = "data(e1): pair 1 J-x STAYS"
    with tempfile.TemporaryDirectory() as d:
        repo = _commit_repo(d)
        head = R.commit_results(repo, [repo / "results.jsonl"], subject)
        names = _git_out(repo, "show", "--name-only", "--format=", "HEAD").split()
        staged = _git_out(repo, "diff", "--cached", "--name-only").split()
        subj = _git_out(repo, "log", "-1", "--format=%s").strip()
        body_last = _git_out(repo, "log", "-1", "--format=%B").rstrip("\n").splitlines()[-1]
        head_now = _git_out(repo, "rev-parse", "HEAD").strip()
    with tempfile.TemporaryDirectory() as d:  # the subject check's red branch: a hook rewrites the subject
        repo = _commit_repo(d, hook_rewrites=True)
        before = _git_out(repo, "rev-parse", "HEAD").strip()
        try:
            R.commit_results(repo, [repo / "results.jsonl"], subject)
            mismatch = None
        except RuntimeError as e:
            mismatch = str(e)
        after = _git_out(repo, "rev-parse", "HEAD").strip()
        left = _git_out(repo, "log", "-1", "--format=%s").strip()
    ok = (head == head_now and names == ["results.jsonl"] and staged == ["other.txt"] and subj == subject
          and body_last == R.COAUTHOR and mismatch is not None and "rewritten" in mismatch and subject in mismatch
          and after != before and left == "data(e1): rewritten")
    return ok, (f"files={names} still_staged={staged} subject_ok={subj == subject} coauthor_ok={body_last == R.COAUTHOR} "
                f"| hook-rewrite: raised={mismatch is not None} left_as_is={left!r}")


FORBIDDEN = re.compile(r"\b(done|ready|ship|final)\b", re.IGNORECASE)


def g_commit_subjects():
    got = {}
    for name, script, problems_at, want in (
            ("all_pass", lambda t, a, n: mk_run(t, a, n), None, 12),
            ("all_loss", lambda t, a, n: mk_run(t, a, n, passed=(a == "A")), None, 5),
            ("refusal", lambda t, a, n: mk_run(t, a, n), 3, 2)):
        with tempfile.TemporaryDirectory() as d:
            lp = Loop(Path(d) / "r.jsonl", script, problems_at=problems_at)
            lp.drive()
        got[name] = (lp.subjects, want)
    subjects = [s for v in got.values() for s in v[0]]
    ok = (all(len(v[0]) == v[1] for v in got.values()) and len(subjects) == 19
          and all(s.startswith("data(e1): ") for s in subjects) and not any(FORBIDDEN.search(s) for s in subjects))
    return ok, (" ".join(f"{k}={len(v[0])}/{v[1]}" for k, v in got.items())
                + f" forbidden={[s for s in subjects if FORBIDDEN.search(s)]} last={got['all_loss'][0][-1]!r}")


def _capture(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue().splitlines()


def g_cli_plan():
    with tempfile.TemporaryDirectory() as d:
        absent = Path(d) / "absent.jsonl"
        rc, lines = _capture(R.cmd_plan, ["--bank", str(BANK_PATH), "--results", str(absent)])
        empty = Path(d) / "empty"
        empty.mkdir()
        rc_e, lines_e = _capture(R.cmd_plan, ["--bank", str(empty)])
        one = Path(d) / "one.jsonl"
        for r in pair(0):
            R.append_record(one, r)
        rc_1, lines_1 = _capture(R.cmd_plan, ["--bank", str(BANK_PATH), "--results", str(one)])
        written = sorted(p.name for p in Path(d).iterdir())
    tasks = [ln.split() for ln in lines if ln.startswith("TASK ")]
    want = [t["id"] for t in R.ordered_tasks(need_bank())]
    ok = (rc == 0 and [t[2] for t in tasks] == want and len(tasks) == 11 and want[0] == GCEG
          and "arms=A,B" in tasks[0] and tasks[1][2] == "J-eaat_session_launch" and "arms=B,A" in tasks[1]
          and tasks[-1][2] == "J-cr_review_verdict" and lines[-1] == f"NEXT RUN {GCEG} A 1"
          and rc_e == 1 and any(x.startswith("PLAN REFUSED") for x in lines_e)
          and rc_1 == 0 and lines_1[-1] == "NEXT RUN J-eaat_session_launch B 1"
          and written == ["empty", "one.jsonl"])
    return ok, (f"rc={rc} tasks={len(tasks)} first={tasks[0][2:3] + tasks[0][5:6] if tasks else None} "
                f"last={tasks[-1][2] if tasks else None} next={lines[-1] if lines else None!r} | empty_bank={rc_e} "
                f"{lines_e[-1][:50] if lines_e else None!r} | one_pair next={lines_1[-1] if lines_1 else None!r} "
                f"files_after={written}")


def g_cli_run_refuses():
    before = list(BLOCKED)
    saved = R.drive
    R.drive = _never_drive  # belt and braces: the refusal must come before the loop
    try:
        with tempfile.TemporaryDirectory() as d:
            res = Path(d) / "results.jsonl"
            rc, lines = _capture(R.cmd_run, ["--no-commit"], frozen=Path(d) / "absent_BANK_FROZEN_AT", results=res,
                                 version_fn=lambda: OK_VERSION)
            exists = res.exists()
    finally:
        R.drive = saved
    new = BLOCKED[len(before):]
    ok = (rc == 1 and bool(lines) and lines[-1].startswith("E1-RUN REFUSED") and not exists
          and not any("-p" in a for a in new) and new == [])
    return ok, f"rc={rc} last={lines[-1] if lines else None!r} results_exists={exists} new_blocked={new} " + \
        f"refused={[ln[:40] for ln in lines if 'REFUSED' in ln and ln.startswith('CHECK')]}"


def _never_drive(*a, **k):
    raise AssertionError("drive reached from a gate that must refuse first")


def g_cli_usage():
    got = {}
    saved = R.preflight, R.drive
    reached = []
    R.preflight = lambda **k: reached.append("preflight") or [("cli", False, "usage gate")]
    R.drive = _never_drive  # a usage error must never reach the checks, let alone the loop
    try:
        for argv in ([], ["bogus"], ["run", "--max-pairs", "x"], ["plan", "--bogus"], ["run", "--max-pairs", "0"]):
            rc, lines = _capture(R.main, argv)
            got[" ".join(argv) or "(none)"] = (rc, lines)
    finally:
        R.preflight, R.drive = saved
    usage = got["(none)"][1]
    text = "\n".join(usage)
    names_all = all(f"e1_runner.py {c}" in text for c in ("plan", "preflight", "run"))
    ok = all(v[0] == 2 for v in got.values()) and names_all and reached == []
    return ok, " ".join(f"{k!r}={v[0]}" for k, v in got.items()) + f" usage_names_all={names_all} checks_reached={reached}"


# ---- 02-03 review fixes (F1-F5): pinned identities, post-run re-checks, refusal on a raising check -----------

def _packet_world(d, edit):
    """fake_world with its packet rewritten by edit(cands) -> (world, cands); the world's packet_sha256 follows the
    edit, so only the property under test can refuse."""
    w = fake_world(d)
    cands = json.loads(w["packet"].read_text(encoding="utf-8"))["experiments"][0]["candidates"]
    cands = edit(cands)
    _write_packet(d, cands)
    w["packet_sha256"] = hashlib.sha256(w["packet"].read_bytes()).hexdigest()
    return w, cands


def _per_run(w, **over):
    kw = dict(bank_rel="bank", frozen=w["frozen"], packet=w["packet"], home=w["home"], version_fn=w["version_fn"],
              drift_fn=w["drift_fn"], packet_sha256=w["packet_sha256"], frozen_hash=w["frozen_hash"])
    kw.update(over)
    return R.per_run_checks(**kw)["problems"]


def _refused(checks):
    return [n for n, o, _ in checks if not o]


def g_packet_pin():
    """F1: the packet's own bytes are pinned in the runner; preflight and per_run_checks refuse any other packet."""
    head = subprocess.run(["git", "show", "HEAD:vault/programs/cognitive-economy/post-reset-packet.json"],
                          cwd=str(R.REPO), capture_output=True, check=True).stdout
    real = (R.PACKET_SHA256 == hashlib.sha256(head).hexdigest() == hashlib.sha256(R.PACKET.read_bytes()).hexdigest()
            and R.check_packet() == [])
    with tempfile.TemporaryDirectory() as d:
        w = fake_world(d)
        clean = _per_run(w, packet_sha256=R.PACKET_SHA256)  # the temp packet is not the pinned one
        pf = _refused(R.preflight(**dict(w, packet_sha256=R.PACKET_SHA256)))
        good = _per_run(w)
        missing = _per_run(dict(w, packet=Path(d) / "absent.json"))
    with tempfile.TemporaryDirectory() as d:
        # rule bytes edited AND the packet's sha256_lf rewritten to match (review d1): pins pass, the packet pin not
        pinned = fake_world(d)["packet_sha256"]
        shutil.rmtree(d)
        Path(d).mkdir()
        w2, _ = _packet_world(d, lambda cs: [dict(c, sha256_lf=_sha_lf(b"# edited rule\n"))
                                             if _rel(c) == "rules/python/testing.md" else c for c in cs])
        (w2["home"] / ".claude" / "rules/python/testing.md").write_bytes(b"# edited rule\n")
        rewritten = _per_run(w2, packet_sha256=pinned)
        pins_pass = R.check_pins(w2["packet"], w2["home"]) == (13, [])
    ok = (real and len(clean) == 1 and clean[0].startswith("packet sha256") and pf == ["packet"] and good == []
          and pins_pass and len(rewritten) == 1 and rewritten[0].startswith("packet sha256")
          and any(p.startswith("packet unreadable: FileNotFoundError") for p in missing))
    return ok, (f"real_pin={real} other_packet={clean} preflight_refused={pf} control={good} "
                f"rewritten_pin={rewritten} missing={missing[:2]}")


def g_packet_set():
    """F1+F2: a packet that is not 13 distinct rules is refused by check_pins, excludes, preflight and per-run."""
    out = {}
    for name, edit in (("dup", lambda cs: [cs[0] if _rel(c) == "rules/scoped-side-effect-authority.md" else c
                                           for c in cs]),
                       ("twelve", lambda cs: [c for c in cs  # review d2: an R2 rule dropped from arm B
                                              if _rel(c) != "rules/scoped-side-effect-authority.md"])):
        with tempfile.TemporaryDirectory() as d:
            w, cands = _packet_world(d, edit)
            n, bad = R.check_pins(w["packet"], w["home"])
            try:
                R.excludes(w["packet"], w["home"])
                ex = "accepted"
            except ValueError as e:
                ex = str(e)
            pf = _refused(R.preflight(**w))
            pr = _per_run(w)
            out[name] = (n, bad, ex, pf, pr)
    dup, twelve = out["dup"], out["twelve"]
    ok = (dup[0] == 13 and any("more than once" in b for b in dup[1]) and "more than once" in dup[2]
          and dup[3] == ["pins", "excludes"] and len(dup[4]) == 1 and dup[4][0].startswith("pins 13/13:")
          and twelve[0] == 12 and any("12 candidates" in b for b in twelve[1]) and "12 candidates" in twelve[2]
          and twelve[3] == ["pins", "excludes"] and len(twelve[4]) == 1 and twelve[4][0].startswith("pins 12/13"))
    return ok, f"dup={dup} | twelve={twelve}"


def g_frozen_pin():
    """F3: BANK_FROZEN_AT must hold the pinned freeze hash; a re-freeze passes bank_drift but is refused."""
    real = R.BANK_FROZEN_HASH == R.FROZEN.read_text(encoding="utf-8").strip() and R.check_frozen_pin() == [] \
        and R.BANK_COMMIT_PREFIX == R.BANK_FROZEN_HASH[:10]
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "w").mkdir()
        (Path(d) / "repo").mkdir()
        w = fake_world(Path(d) / "w")
        repo, frozen = drift_repo(Path(d) / "repo")
        h = frozen.read_text(encoding="utf-8").strip()
        kw = dict(repo=repo, frozen=frozen, frozen_hash=h, drift_fn=R.bank_drift)
        control = _per_run(w, **kw)
        (repo / "bank" / "task_a.py").write_text("A = 2\n", encoding="utf-8")
        _g(repo, "commit", "-q", "-am", "edit")
        h2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
        frozen.write_text(h2 + "\n", encoding="utf-8")
        drift_alone = R.bank_drift(repo, "bank", frozen)
        refrozen = _per_run(w, **kw)
        pf = R.preflight(**dict(w, frozen=w["frozen"], frozen_hash=h))
    st = {n: (o, det) for n, o, det in pf}
    ok = (real and control == [] and drift_alone == [] and len(refrozen) == 1
          and refrozen[0].startswith("BANK_FROZEN_AT") and _refused(pf) == ["bank_drift"]
          and "!= pinned freeze" in st["bank_drift"][1])
    return ok, (f"real_pin={real} control={control} refrozen_bank_drift={drift_alone} per_run={refrozen} "
                f"preflight={_refused(pf)}:{st['bank_drift'][1][:60]}")


def _session_run(version="2.1.289", drift_fn=None, has_drift_fn=True):
    """one_run through the session over a fake bank (red precondition, green grade) and a fake CLI whose transcript
    stamps `version` -> the run record."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        tf = d / "task_fake.py"
        tf.write_text("# fake\n")
        wt = d / "wt"
        wt.mkdir()
        projects = d / "projects"
        grades = iter([{"rc": 1, "summary": "E1J_PASS=0/8 control=0/4 judgement=0/4", "passed": 0, "total": 8,
                        "fails": ["x"]},
                       {"rc": 0, "summary": "E1J_PASS=8/8 control=4/4 judgement=4/4", "passed": 8, "total": 8,
                        "fails": []}])

        def exec_fn(argv, **kw):
            sid = str(uuid.uuid4())
            p = projects / R._norm(kw["cwd"])
            p.mkdir(parents=True, exist_ok=True)
            text = fake_transcript_lines(sid).replace(f'"version": "{K.CLI_VERSION}"', f'"version": "{version}"')
            (p / f"{sid}.jsonl").write_text(text, encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(
                {"session_id": sid, "num_turns": 2, "is_error": False}) + "\n", stderr="")
        bank = types.SimpleNamespace(fresh_tree=lambda rid, base: wt, leak_scan=lambda w: (10, []),
                                     drop_tree=lambda w: True, jprepare=lambda w, t: [],
                                     jgrade=lambda w, t: next(grades), JPROMPT="{module}")
        t = {"id": "J-fake", "rule": "rules/x.md", "file": tf, "module": "e1j/fake.py"}
        kw = {"drift_fn": drift_fn} if has_drift_fn else {}
        return R.one_run(bank, t, "A", 1, "0" * 40, excl=[], cli_version=OK_VERSION, append=lambda r: None,
                         exec_fn=exec_fn, projects=projects, **kw)


def g_cli_drift():
    """F4: the transcript's own CLI version is recorded and must equal CLI_VERSION; the bank is re-checked after
    the grade (drift, a raising check or no check -> invalid)."""
    def boom():
        raise OSError("bank gone")
    good = _session_run(drift_fn=lambda: [])
    newer = _session_run(version="2.1.290", drift_fn=lambda: [])
    drifted = _session_run(drift_fn=lambda: ["edited since freeze: bank/task_a.py"])
    raised = _session_run(drift_fn=boom)
    unchecked = _session_run(has_drift_fn=False)
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "t.jsonl"
        f.write_text(fake_transcript_lines("s") + json.dumps({"type": "x", "version": "2.1.290"}) + "\nnot json\n",
                     encoding="utf-8")
        mixed = R.transcript_versions(f)
    ok = (good["valid"] is True and good["cli_versions_observed"] == ["2.1.289"] and good["bank_drift_after"] == []
          and newer["valid"] is False and newer["cli_versions_observed"] == ["2.1.290"]
          and newer["invalid_reasons"] == ["cli version drift: transcript reports ['2.1.290'], want ['2.1.289']"]
          and drifted["valid"] is False and drifted["invalid_reasons"] == ["bank drift during run"]
          and raised["valid"] is False and raised["invalid_reasons"] == ["bank drift during run"]
          and "bank drift unreadable: OSError" in str(raised["bank_drift_after"])
          and unchecked["valid"] is False and unchecked["invalid_reasons"] == ["bank not re-checked after grade"]
          and mixed == ["2.1.289", "2.1.290"])
    return ok, (f"good={good['valid']}/{good['cli_versions_observed']} newer={newer['invalid_reasons']} "
                f"drifted={drifted['invalid_reasons']} raised={raised['bank_drift_after']} "
                f"unchecked={unchecked['invalid_reasons']} mixed={mixed}")


def g_loop_drift_halt():
    """F4: a run whose post-grade re-check found bank drift halts the campaign with a refusal record."""
    calls = []

    def script(t, a, n):
        calls.append((t, a, n))
        r = mk_run(t, a, n)
        if len(calls) == 3:
            r["bank_drift_after"] = ["edited since freeze: bank/task_a.py"]
            r["valid"], r["invalid_reasons"] = K.run_valid(r)
        return r
    with tempfile.TemporaryDirectory() as d:
        lp = Loop(Path(d) / "r.jsonl", script)
        rc = lp.drive()
        recs = lp.records()
    rid = K.run_id(*calls[2]) if len(calls) > 2 else None
    ref = recs[-1] if recs else {}
    ok = (rc == (1, "REFUSED") and len(lp.calls) == 3 and ref.get("kind") == "refusal" and ref.get("after") == rid
          and ref.get("problems", [""])[0] == "bank drift during run" and lp.subjects[-1] == f"data(e1): refusal after {rid}"
          and recs[-2].get("valid") is False)
    return ok, f"rc={rc} runs={len(lp.calls)} last={ref} commits={lp.subjects[-1:]}"


def g_loop_check_every_run():
    """drive() runs check_fn before EVERY run, attempt 2 included; a check_fn that raises is a refusal."""
    def script(t, a, n):
        return mk_run(t, a, n, valid=not (t == T0 and a == "A" and n == 1))
    with tempfile.TemporaryDirectory() as d:
        lp = Loop(Path(d) / "r.jsonl", script)
        rc = lp.drive()
    retried = (T0, "A", 2) in lp.calls
    alternates = lp.events == ["check", "run"] * len(lp.calls)

    class Raising(Loop):
        def check_fn(self):
            self.checks += 1
            self.events.append("check")
            if self.checks == 2:
                raise OSError("packet unreadable")
            return {"problems": [], "cli_version": OK_VERSION}
    with tempfile.TemporaryDirectory() as d:
        lr = Raising(Path(d) / "r.jsonl", script)
        try:
            rc2 = lr.drive()
            esc = None
        except BaseException as e:  # the subject: nothing may escape
            rc2, esc = None, f"{type(e).__name__}: {e}"
        recs = lr.records()
    ref = recs[-1] if recs else {}
    ok = (rc == (0, K.ALL_DECIDED) and retried and alternates and len(lp.calls) == 23
          and esc is None and rc2 == (1, "REFUSED") and len(lr.calls) == 1 and ref.get("kind") == "refusal"
          and ref.get("before") == K.run_id(T0, "A", 2) and "per-run check raised: OSError" in str(ref.get("problems")))
    return ok, (f"rc={rc} runs={len(lp.calls)} attempt2={retried} check_before_every_run={alternates} | "
                f"raising: rc={rc2} escaped={esc} runs={len(lr.calls)} refusal={ref.get('problems')}")


def g_drift_unreadable():
    """F5: a bank directory the walk cannot list is "bank unreadable", never "nothing added"."""
    if os.geteuid() == 0:
        return False, "running as root: mode 000 does not deny reads, the drill cannot observe the branch"
    res = {}
    for name, mode in (("listable", 0o755), ("unlistable", 0o000)):
        with tempfile.TemporaryDirectory() as d:
            repo, frozen = drift_repo(d)
            sub = repo / "bank" / "sub"
            sub.mkdir()
            (sub / "task_z.py").write_text("Z = 1\n", encoding="utf-8")
            sub.chmod(mode)
            try:
                res[name] = R.bank_drift(repo, "bank", frozen)
            finally:
                sub.chmod(0o755)
    ok = (res["listable"] == ["added since freeze: bank/sub/task_z.py"]
          and len(res["unlistable"]) == 1 and res["unlistable"][0].startswith("bank unreadable:")
          and "bank/sub" in res["unlistable"][0])
    return ok, f"{res}"


# ---- 02-04 review fixes: the session dies with the runner (F1), lost commits (F2), torn tail (F3) ----------------

def _wait_for(cond, limit):
    """Bounded poll: True as soon as cond() holds, False after `limit` seconds (never an open-ended wait)."""
    end = time.time() + limit
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return bool(cond())


def _fake_script(d, name, body):
    """An executable fake CLI (never named claude, so the no-model guard stays armed for the real binary)."""
    f = Path(d) / name
    f.write_text(f"#!{sys.executable}\n" + body, encoding="utf-8")
    f.chmod(0o755)
    return str(f)


def _reap(*pids):
    for pid in pids:
        try:
            os.kill(int(pid), 9)
        except (OSError, ValueError, TypeError):
            pass


_PARENT = """import sys
sys.path.insert(0, {e1!r})
import test_e1_runner as TT  # the no-model guard is armed in this process too
R = TT.R
R.CLAUDE = sys.argv[1]
res = sys.argv[2]
R.session(sys.argv[3], "P", "A", {{}}, [], on_spawn=lambda pid, st: R.append_record(
    res, {{"kind": "run_start", "run_id": "r", "session_pid": pid, "session_pid_start": st}}))
"""


def g_session_pdeathsig():
    """A runner SIGKILLed mid-session takes its session with it, and run_start held the child's pid + start time
    while the child was still running (recorded before the wait)."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        pidf, res, wt = d / "child.pid", d / "r.jsonl", d / "wt"
        wt.mkdir()
        cli = _fake_script(d, "fakecli", "import os, time\n"
                           f"open({str(pidf)!r}, 'w').write(str(os.getpid()))\ntime.sleep(30)\n")
        parent_py = d / "parent.py"
        parent_py.write_text(_PARENT.format(e1=str(E1)), encoding="utf-8")
        par = subprocess.Popen([sys.executable, str(parent_py), cli, str(res), str(wt)])
        pid = start = None
        try:
            if not _wait_for(lambda: pidf.exists() and pidf.read_text().strip() and res.exists(), 60):
                return False, "fake session never started"
            pid = int(pidf.read_text())
            recs = R.read_records(res)
            st = R.proc_start(pid)
            start = st[0] if st else None
            recorded = (len(recs) == 1 and recs[0].get("session_pid") == pid
                        and recs[0].get("session_pid_start") == start and start is not None)
            alive_before = R.session_alive(pid, start)
            par.kill()
            par.wait(timeout=10)
            died = _wait_for(lambda: not R.session_alive(pid, start), 5)
        finally:
            _reap(par.pid, pid)
    return recorded and alive_before and died, (f"recorded_before_wait={recorded} child_alive_then={alive_before} "
                                                f"child_dead_after_runner_kill={died} pid={pid}")


def g_session_timeout_group():
    """On the session timeout the whole process group dies (a grandchild too), and the run reads "timeout"."""
    saved = (R.CLAUDE, R.SESSION_TIMEOUT)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        pidf = d / "pids"
        R.CLAUDE = _fake_script(d, "fakecli", "import os, subprocess, sys, time\n"
                                "g = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
                                f"open({str(pidf)!r}, 'w').write(f'{{os.getpid()}} {{g.pid}}')\ntime.sleep(30)\n")
        R.SESSION_TIMEOUT = 2
        pids = []
        try:
            rec = {}
            R.session(d, "P", "A", rec, [])
            pids = [int(x) for x in pidf.read_text().split()] if pidf.exists() else []
            starts = [R.proc_start(x) for x in pids]
            dead = len(pids) == 2 and _wait_for(lambda: all(st is None or st[1] == "Z" or R.proc_start(x) != st
                                                                for x, st in zip(pids, starts)), 5)
        finally:
            R.CLAUDE, R.SESSION_TIMEOUT = saved
            _reap(*pids)
    ok = (rec.get("claude_rc") == "timeout" and rec.get("session_launched") is True and dead
          and rec.get("session_pid") == (pids[0] if pids else -1) and rec.get("wall_s", 99) < 20)
    return ok, (f"rc={rec.get('claude_rc')} wall={rec.get('wall_s')} pids={pids} group_dead={dead} "
                f"recorded_pid={rec.get('session_pid')}")


def g_runstart_pid():
    """The production one_run path (no exec_fn): the child itself finds its own pid in run_start."""
    bank = need_bank()
    saved_runs, saved_cli = bank.RUNS, R.CLAUDE
    saved_env = {k: os.environ.get(k) for k in ("E1FAKE_RESULTS", "E1FAKE_SEEN")}
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        results, seen = d / "results.jsonl", d / "seen"
        bank.RUNS = d / "runs"
        os.environ["E1FAKE_RESULTS"], os.environ["E1FAKE_SEEN"] = str(results), str(seen)
        R.CLAUDE = _fake_script(d, "fakecli", "import json, os\n"
                                "recs = [json.loads(x) for x in open(os.environ['E1FAKE_RESULTS']) if x.strip()]\n"
                                "ok = [r for r in recs if r.get('kind') == 'run_start' "
                                "and r.get('session_pid') == os.getpid()]\n"
                                "open(os.environ['E1FAKE_SEEN'], 'w').write('seen' if len(ok) == 1 else 'missing')\n"
                                "print(json.dumps({'session_id': '', 'num_turns': 0, 'is_error': False}))\n")
        try:
            t = bank.tasks(only=[GCEG])[0]
            rec = R.one_run(bank, t, "A", 1, bank.jbase(), excl=[], cli_version="2.1.289 (test)",
                            append=lambda r: R.append_record(results, r), run_id="e1test-pid-A-a1",
                            projects=d / "projects")
            R.append_record(results, rec)
            lines = R.read_records(results)
            saw = seen.read_text() if seen.exists() else None
        finally:
            bank.RUNS, R.CLAUDE = saved_runs, saved_cli
            for k, v in saved_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    rs = lines[0] if lines else {}
    ok = ([x.get("kind") for x in lines] == ["run_start", "run"] and saw == "seen"
          and isinstance(rs.get("session_pid"), int) and isinstance(rs.get("session_pid_start"), int)
          and rec.get("session_pid") == rs.get("session_pid") and rec.get("claude_rc") == 0
          and rec.get("session_launched") is True)
    return ok, (f"kinds={[x.get('kind') for x in lines]} child_saw_its_pid={saw} run_start_pid="
                f"{rs.get('session_pid')}/{rs.get('session_pid_start')} rc={rec.get('claude_rc')} "
                f"err={rec.get('error')}")


def g_reconcile_alive():
    """reconcile refuses (no record, no drop, no run) while the recorded session pid with that start time lives;
    a reused pid (other start time) and a dead pid reconcile as before."""
    live = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        st = _wait_for(lambda: R.proc_start(live.pid) is not None, 5) and R.proc_start(live.pid)[0]
        out = {}
        for name, extra in (("alive", {"session_pid": live.pid, "session_pid_start": st}),
                            ("unknown_start", {"session_pid": live.pid, "session_pid_start": None}),
                            ("reused_pid", {"session_pid": live.pid, "session_pid_start": st + 1})):
            with tempfile.TemporaryDirectory() as d:
                rc, rec, lp, drops, _ = _reconcile_case(d, True, extra)
                out[name] = (rc, rec.get("spend"), len(drops), lp.calls[:1], lp.lines[-1] if lp.lines else "")
        live.kill()
        live.wait(timeout=10)
        with tempfile.TemporaryDirectory() as d:
            rc, rec, lp, drops, _ = _reconcile_case(d, True, {"session_pid": live.pid, "session_pid_start": st})
            out["dead"] = (rc, rec.get("spend"), len(drops), lp.calls[:1], lp.lines[-1] if lp.lines else "")
    finally:
        _reap(live.pid)
    refused = [f"session still alive pid {live.pid}" in out[k][4] and out[k][0] == (1, "REFUSED")
               and out[k][1] is None and out[k][2] == 0 and out[k][3] == [] for k in ("alive", "unknown_start")]
    measured = [out[k][0] == (0, K.ALL_DECIDED) and out[k][1] == 50308 and out[k][2] == 1
                and out[k][3] == [(T0, "A", 2)] for k in ("reused_pid", "dead")]
    return all(refused) and all(measured), {k: (v[0], v[1], v[2], v[4][:60]) for k, v in out.items()}


class _Kill(BaseException):
    """Stands in for SIGKILL: drive has no finally, so nothing after the raise point runs."""


def _git_repo(d):
    repo = Path(d) / "repo"
    repo.mkdir()
    _g(repo, "init", "-q")
    for k, v in (("user.name", "e1"), ("user.email", "e1@example.invalid"), ("commit.gpgsign", "false"),
                 ("core.hooksPath", "/dev/null")):
        _g(repo, "config", k, v)
    (repo / "seed.txt").write_text("s\n", encoding="utf-8")
    _g(repo, "add", "seed.txt")
    _g(repo, "commit", "-q", "-m", "seed")
    return repo


def _real_drive(repo, res, *, commit_fn=None, dirty_fn=None):
    return R.drive(mk_order(), results=res, run_fn=lambda t, a, n, ctx: mk_run(t, a, n),
                   check_fn=lambda: {"problems": [], "cli_version": OK_VERSION}, reconcile_fn=_no_reconcile,
                   commit_fn=commit_fn or (lambda s: R.commit_results(repo, [res], s)),
                   dirty_fn=dirty_fn or (lambda: R.results_dirty(repo, res)), r2_rules=R2_RULES, out=lambda x: None)


def g_loop_stop_recommit():
    """A stop record whose commit was lost (crash after the append, or the stop commit failing) is committed by the
    next drive before it reports HALTED; a dirty file that cannot be committed (or an unreadable status) is
    COMMIT_FAILED, never a clean exit; a clean halted file makes no commit."""
    res_of = {}
    real_append = R.append_record
    for case in ("crash_after_stop_append", "stop_commit_fails"):
        with tempfile.TemporaryDirectory() as d:
            repo = _git_repo(d)
            res = repo / "results.jsonl"
            calls = {"n": 0}

            def app(path, rec):
                real_append(path, rec)
                if case == "crash_after_stop_append" and rec.get("kind") == "stop":
                    raise _Kill("after stop append")

            def flaky_commit(subj):
                if case == "stop_commit_fails" and subj.startswith("data(e1): stop"):
                    raise RuntimeError("index.lock held by another session (simulated)")
                R.commit_results(repo, [res], subj)
            R.append_record = app
            try:
                first = _real_drive(repo, res, commit_fn=flaky_commit)
            except _Kill as e:
                first = f"KILLED {e}"
            finally:
                R.append_record = real_append
            before = _git_out(repo, "log", "-1", "--format=%s").strip()
            second = _real_drive(repo, res)
            head = _git_out(repo, "rev-parse", "HEAD").strip()
            third = _real_drive(repo, res)  # clean: no further commit
            res_of[case] = (first, before, second, _git_out(repo, "log", "-1", "--format=%s").strip(),
                            '"kind": "stop"' in _git_out(repo, "show", "HEAD:results.jsonl"),
                            _git_out(repo, "status", "--porcelain", "--", "results.jsonl").strip(),
                            third, _git_out(repo, "rev-parse", "HEAD").strip() == head)
            calls["n"] += 1
    halted_subjects = []
    with tempfile.TemporaryDirectory() as d:  # the HALTED branch on its own: clean at start, dirty at HALTED
        res = Path(d) / "r.jsonl"
        lp = Loop(res, lambda t, a, n: mk_run(t, a, n))
        lp.drive()
        flags = iter([False, True])
        rc_h = R.drive(mk_order(), results=res, run_fn=None, check_fn=None, reconcile_fn=None,
                       commit_fn=halted_subjects.append, dirty_fn=lambda: next(flags), r2_rules=R2_RULES,
                       out=lambda x: None)
        rc_fail = R.drive(mk_order(), results=res, run_fn=None, check_fn=None, reconcile_fn=None,
                          commit_fn=lambda s: (_ for _ in ()).throw(RuntimeError("commit refused")),
                          dirty_fn=lambda: True, r2_rules=R2_RULES, out=lambda x: None)
        rc_unread = R.drive(mk_order(), results=res, run_fn=None, check_fn=None, reconcile_fn=None,
                            commit_fn=halted_subjects.append,
                            dirty_fn=lambda: (_ for _ in ()).throw(RuntimeError("git status failed")),
                            r2_rules=R2_RULES, out=lambda x: None)
    ok = all(v[1].startswith("data(e1): pair 11") and v[2] == (0, K.ALL_DECIDED) and v[4] and v[5] == ""
             and v[6] == (0, K.ALL_DECIDED) and v[7] for v in res_of.values())
    ok = ok and (res_of["stop_commit_fails"][0] == (1, "COMMIT_FAILED")
                 and str(res_of["crash_after_stop_append"][0]).startswith("KILLED")
                 and rc_h == (0, K.ALL_DECIDED) and halted_subjects == [f"data(e1): stop {K.ALL_DECIDED} (recommit)"]
                 and rc_fail == (1, "COMMIT_FAILED") and rc_unread == (1, "COMMIT_FAILED"))
    return ok, ({k: (v[0], v[1][:24], v[2], v[3][:40], v[4], v[5], v[7]) for k, v in res_of.items()},
                f"halted_branch={rc_h} {halted_subjects} commit_fails={rc_fail} status_unreadable={rc_unread}")


def g_torn_tail():
    """append_record refuses onto a non-empty file whose last byte is not a newline (bytes unchanged), and drive
    refuses before any run; absent, empty and newline-terminated files append as before."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        res = d / "r.jsonl"
        for a in ("A", "B"):
            R.append_record(res, mk_run(T0, a, 1))
        res.write_bytes(res.read_bytes()[:-1])
        before = res.read_bytes()
        try:
            R.append_record(res, {"kind": "pair"})
            refused = None
        except K.ContractError as e:
            refused = str(e)
        unchanged = res.read_bytes() == before
        lp = Loop(res, lambda t, a, n: mk_run(t, a, n))
        rc = lp.drive()
        empty, absent, fine = d / "e.jsonl", d / "a.jsonl", d / "f.jsonl"
        empty.write_bytes(b"")
        fine.write_bytes(b'{"kind": "x"}\n')
        for f in (empty, absent, fine):
            R.append_record(f, {"kind": "y"})
        controls = [len(R.read_records(f)) for f in (empty, absent, fine)]
    ok = (refused is not None and "torn tail" in refused and unchanged and rc == (1, "REFUSED")
          and lp.calls == [] and any("torn tail" in x for x in lp.lines) and controls == [1, 1, 2])
    return ok, f"refused={refused!r:.60} unchanged={unchanged} drive={rc} runs={lp.calls} controls={controls}"


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
    ("V-E1-PINS", g_pins), ("V-E1-CLI", g_cli), ("V-E1-BANK-DRIFT", g_bank_drift),
    ("V-E1-RECORDS-READ", g_records_read),
    ("V-E1-PREFLIGHT-OK", g_preflight_ok), ("V-E1-PREFLIGHT-REFUSALS", g_preflight_refusals),
    ("V-E1-PREFLIGHT-NOBANK", g_preflight_nobank), ("V-E1-PER-RUN-CHECKS", g_per_run_checks),
    ("V-E1-CLI-PREFLIGHT", g_cli_preflight),
    ("V-E1-LOOP-ALL-DECIDED", g_loop_all_decided), ("V-E1-LOOP-HARM", g_loop_harm),
    ("V-E1-LOOP-SPEND", g_loop_spend), ("V-E1-LOOP-POSCTL", g_loop_posctl), ("V-E1-LOOP-NOINFO", g_loop_noinfo),
    ("V-E1-LOOP-RESUME", g_loop_resume), ("V-E1-LOOP-HALTED", g_loop_halted),
    ("V-E1-LOOP-REFUSAL", g_loop_refusal), ("V-E1-LOOP-RECONCILE", g_loop_reconcile),
    ("V-E1-LOOP-COMMIT-FAIL", g_loop_commit_fail),
    ("V-E1-COMMIT", g_commit), ("V-E1-COMMIT-SUBJECTS", g_commit_subjects), ("V-E1-CLI-PLAN", g_cli_plan),
    ("V-E1-CLI-RUN-REFUSES", g_cli_run_refuses), ("V-E1-CLI-USAGE", g_cli_usage),
    ("V-E1-PACKET-PIN", g_packet_pin), ("V-E1-PACKET-SET", g_packet_set), ("V-E1-FROZEN-PIN", g_frozen_pin),
    ("V-E1-CLI-DRIFT", g_cli_drift), ("V-E1-LOOP-DRIFT-HALT", g_loop_drift_halt),
    ("V-E1-LOOP-CHECK-EVERY-RUN", g_loop_check_every_run), ("V-E1-DRIFT-UNREADABLE", g_drift_unreadable),
    ("V-E1-SESSION-PDEATHSIG", g_session_pdeathsig), ("V-E1-SESSION-TIMEOUT-GROUP", g_session_timeout_group),
    ("V-E1-RUNSTART-PID", g_runstart_pid), ("V-E1-RECONCILE-ALIVE", g_reconcile_alive),
    ("V-E1-LOOP-STOP-RECOMMIT", g_loop_stop_recommit), ("V-E1-TORN-TAIL", g_torn_tail),
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
