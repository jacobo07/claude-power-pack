#!/usr/bin/env python3
"""V-KMEP-* gates: the kme_pillars measuring instrument (incremental-cognition phase 3, pillar D first).

Hermetic: every fixture is a synthetic transcript tree built here under a scratch directory. The two -REAL
gates read (never write) the GEX44 KME-G corpora and are SKIPped when those roots are absent. A SKIP or an
INCONCLUSIVE is printed and counted apart; it is never a PASS and never part of the n/m denominator.

    python3 tools/test_kme_pillars.py            run every gate
    python3 tools/test_kme_pillars.py --drill     mutation drill (each mutant must be killed)
"""
from __future__ import annotations

import atexit
import contextlib
import datetime
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "wiki" / "tools"))
sys.path.insert(0, str(REPO))
import kme_pillars as kp  # noqa: E402

SCRIPT = REPO / "wiki" / "tools" / "kme_pillars.py"
FROZEN_SHA = "18e928af8c489f9d29dd1e76e0c7aa3c6a6975eb"
TMP_ROOT = Path(tempfile.mkdtemp(prefix="kmep-test-"))
_COUNTER = [0]
RESULTS: list[tuple[str, str, str]] = []   # (status, gate, evidence)
QUIET = [False]


def _cleanup() -> None:
    for dp, dns, fns in os.walk(TMP_ROOT):
        for n in dns + fns:
            with contextlib.suppress(OSError):
                os.chmod(os.path.join(dp, n), 0o700)
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


atexit.register(_cleanup)


def scratch(prefix: str = "t") -> Path:
    _COUNTER[0] += 1
    d = TMP_ROOT / f"{prefix}{_COUNTER[0]}"
    d.mkdir(parents=True)
    return d


# --------------------------------------------------------------------------- gate plumbing
def record(status: str, gate: str, ev: str = "") -> None:
    RESULTS.append((status, gate, str(ev)))
    if not QUIET[0]:
        print(f"{status} {gate} {ev}".rstrip())


def run_gate(gate: str, fn) -> None:
    """fn returns (True|False|'SKIP'|'INCONCLUSIVE', evidence); an exception is a FAIL naming its class."""
    try:
        res, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a gate that crashes must read red, never absent
        res, ev = False, f"{exc.__class__.__name__}: {exc}"
    if res in ("SKIP", "INCONCLUSIVE"):
        record(res, gate, ev)
    else:
        record("PASS" if res else "FAIL", gate, ev)


# --------------------------------------------------------------------------- fixture builder
def ts(n: float) -> str:
    """ISO Z timestamp, 3 fractional digits, n seconds after 2026-10-03T10:00:00Z."""
    base = datetime.datetime(2026, 10, 3, 10, 0, 0, tzinfo=datetime.timezone.utc)
    t = base + datetime.timedelta(seconds=n)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


class Fx:
    """Writes jsonl transcripts under <root>/projects/<project>/ ; one Fx = one transcript file."""

    def __init__(self, root, project="-home-x-kme-fixture", session="s1", path=None):
        self.root = Path(root)
        self.project = project
        self.session = session
        self.pdir = self.root / "projects" / project
        self.path = Path(path) if path else self.pdir / f"{session}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def touch(self):
        self.path.touch()
        return self

    def _w(self, obj):
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj) + "\n")
        return self

    def human(self, text, t):
        return self._w({"type": "user", "timestamp": t, "cwd": "/home/x/work",
                        "message": {"role": "user", "content": text}})

    def assistant(self, msg_id, req_id, usage, t, tool_uses=(), text=None, model="claude-opus-5-5"):
        """usage = (input, cache_creation, cache_read, output); tool_uses = [(id, name, input_dict)]."""
        content = []
        if text is not None:
            content.append({"type": "text", "text": text})
        for tid, name, inp in tool_uses:
            content.append({"type": "tool_use", "id": tid, "name": name, "input": inp})
        i, cw, cr, o = usage
        return self._w({"type": "assistant", "timestamp": t, "uuid": f"u-{msg_id}", "requestId": req_id,
                        "message": {"id": msg_id, "model": model, "role": "assistant", "content": content,
                                    "usage": {"input_tokens": i, "cache_creation_input_tokens": cw,
                                              "cache_read_input_tokens": cr, "output_tokens": o}}})

    def tool_result(self, tool_use_id, text, t, is_error=False):
        block = {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}
        if is_error:
            block["is_error"] = True
        return self._w({"type": "user", "timestamp": t, "message": {"role": "user", "content": [block]}})

    def meta_text(self, text, t):
        """A harness-injected user line (isMeta) whose content is a list of text blocks, as skill bodies are."""
        return self._w({"type": "user", "timestamp": t, "isMeta": True, "message": {"role": "user", "content": [
            {"type": "text", "text": text}]}})

    def attachment(self, atype, t, **fields):
        return self._w({"type": "attachment", "timestamp": t, "attachment": dict({"type": atype}, **fields)})

    def compact(self, t):
        return self._w({"type": "system", "subtype": "compact_boundary", "timestamp": t})

    def meta(self, kind="last-prompt"):
        """A metadata line: real transcripts carry NO timestamp on these."""
        return self._w({"type": kind, "lastPrompt": "x"})

    def subagent(self, agent_id, agent_type=None):
        p = self.pdir / self.session / "subagents" / f"agent-{agent_id}.jsonl"
        if agent_type:
            p.parent.mkdir(parents=True, exist_ok=True)
            (p.parent / f"agent-{agent_id}.meta.json").write_text(json.dumps({"agentType": agent_type}))
        return Fx(self.root, self.project, self.session, path=p)


def hook_ctx(fx, t, n_chars, hook="PreToolUse:Bash", ch="A"):
    return fx.attachment("hook_additional_context", t, content=[ch * n_chars], hookName=hook,
                         hookEvent=hook.split(":")[0])


def tracer_fixture(root):
    """The plan's tracer fixture: A idx0 resident 2, B idx1 resident 1, C idx3 resident 1; weighted 3340."""
    fx = Fx(root)
    fx.human("start", ts(0))
    hook_ctx(fx, ts(1), 300, ch="A")
    fx.assistant("m1", "r1", (10, 1000, 0, 50), ts(2), tool_uses=[("tu1", "Bash", {"command": "echo ok"})])
    fx.tool_result("tu1", "ok", ts(3))
    hook_ctx(fx, ts(4), 300, ch="B")
    fx.assistant("m2", "r2", (10, 0, 1000, 50), ts(5))
    fx.compact(ts(6))
    fx.assistant("m3", "r3", (10, 0, 1000, 50), ts(7))
    hook_ctx(fx, ts(8), 300, ch="C")
    fx.assistant("m4", "r4", (10, 0, 1000, 50), ts(9))
    return fx


TRACER_POP = {"sessions_active": 1, "sessions_dead": 0, "calls": 4, "input": 40, "cache_write": 1000,
              "cache_read": 3000, "output": 200}


def write_frozen(path, **entries):
    Path(path).write_text(json.dumps(entries, indent=1))
    return str(path)


# --------------------------------------------------------------------------- runners
def run_cli(args, cwd=REPO):
    p = subprocess.run([sys.executable, str(SCRIPT)] + list(args), cwd=str(cwd), capture_output=True, text=True,
                       timeout=300)
    return p.returncode, p.stdout, p.stderr


def run_main(args):
    """In-process main() with stdout/stderr captured, so a drill's monkeypatch reaches it."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = kp.main(list(args))
    return rc, out.getvalue(), err.getvalue()


def run_json(args):
    """In-process run with --json; returns (rc, result dict or None, stdout, stderr)."""
    rc, out, err = run_main(list(args) + ["--json"])
    res = None
    for line in out.splitlines():
        if line.startswith("{"):
            res = json.loads(line)
    return rc, res, out, err


def parse_measurement(text):
    lines = text.split("\n")
    assert lines[0] == "---", "front matter missing"
    end = lines.index("---", 1)
    front = {}
    for ln in lines[1:end]:
        k, _, v = ln.partition(": ")
        front[k] = json.loads(v)
    a = text.index("<!-- kmep-json -->") + len("<!-- kmep-json -->")
    b = text.index("<!-- /kmep-json -->")
    return front, json.loads(text[a:b])


def utc_date():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def d_args(root, project_dir, frozen, out_dir, denominator="KME-L", extra=()):
    return ["d", "--denominator", denominator, "--frozen-file", str(frozen), "--root", str(project_dir),
            "--out-dir", str(out_dir)] + list(extra)


# --------------------------------------------------------------------------- byte-identity machinery
def rich_fixture(root):
    """A KME project with two sessions (compaction, attachments, repeated reads, a subagent) + one non-KME."""
    fx = Fx(root, session="sA")
    fx.human("map the KMEIP arena", ts(0))
    hook_ctx(fx, ts(1), 120)
    fx.attachment("hook_success", ts(1), hookName="SessionStart:startup", stdout="{}", content="")
    fx.assistant("a1", "ra1", (5, 800, 0, 30), ts(2), text="reading",
                 tool_uses=[("t1", "Read", {"file_path": "/x/kme/a.py"}), ("t2", "Bash", {"command": "ls kme"})])
    fx.tool_result("t1", "R" * 500, ts(3))
    fx.tool_result("t2", "files", ts(3))
    fx.assistant("a2", "ra2", (5, 100, 800, 40), ts(4),
                 tool_uses=[("t3", "Read", {"file_path": "/x/kme/a.py"})])
    fx.tool_result("t3", "R" * 500, ts(5))
    fx.compact(ts(6))
    fx.meta()
    fx.assistant("a3", "ra3", (5, 0, 900, 20), ts(7), model="claude-sonnet-5")
    fx.assistant("a3", "ra3", (5, 0, 900, 25), ts(7))   # streamed duplicate line: max-merged
    sub = fx.subagent("ag1", "Explore")
    sub.human("sub task", ts(3))
    sub.assistant("s1", "rs1", (2, 300, 0, 10), ts(3.5), tool_uses=[("st1", "Grep", {"pattern": "KME", "path": "/x"})])
    sub.tool_result("st1", "hits", ts(3.6))
    sub.assistant("s2", "rs2", (2, 0, 300, 10), ts(3.7))
    Fx(root, session="sB").human("kme again", ts(10)).assistant("b1", "rb1", (1, 10, 0, 5), ts(11))
    Fx(root, session="sDead").human("only a prompt", ts(12))
    other = Fx(root, project="-home-x-plain", session="sC")
    other.human("unrelated", ts(0))
    other.assistant("c1", "rc1", (3, 50, 0, 7), ts(1), tool_uses=[("c1t", "Bash", {"command": "ls"})])
    return root / "projects"


def git_show(path):
    p = subprocess.run(["git", "show", f"{FROZEN_SHA}:{path}"], cwd=str(REPO), capture_output=True, check=True)
    return p.stdout


def run_pipeline(tooldir, workdir, audit_args, report_name="report.json", denom_name="denom.json"):
    """audit -> kme_report -> kme_denominators with the tools from `tooldir`; returns {name: bytes} + stdouts."""
    workdir.mkdir(parents=True, exist_ok=True)
    audit_out = workdir / "audit.json"
    outs = {}
    for label, cmd in (
        ("audit", [sys.executable, str(tooldir / "kme_token_audit.py"), "--out", str(audit_out)] + audit_args),
        ("report", [sys.executable, str(tooldir / "kme_report.py"), str(workdir / report_name), str(audit_out)]),
        ("denom", [sys.executable, str(tooldir / "kme_denominators.py"), str(workdir / report_name),
                   str(workdir / denom_name)]),
    ):
        p = subprocess.run(cmd, cwd=str(workdir), capture_output=True, text=True, timeout=600)
        if p.returncode != 0:
            raise RuntimeError(f"{label} rc={p.returncode}: {p.stderr[-300:]}")
        outs[label + ".stdout"] = p.stdout.encode()
    for n in ("audit.json", report_name, denom_name):
        outs[n] = (workdir / n).read_bytes()
    return outs


def old_tooldir(base):
    d = base / "old"
    d.mkdir(parents=True, exist_ok=True)
    for name in ("kme_token_audit.py", "kme_report.py", "kme_denominators.py"):
        (d / name).write_bytes(git_show(f"wiki/tools/{name}"))
    return d


# =========================================================================== gates (task 1: tracer)
def g_tracer_e2e():
    root = scratch("tracer")
    tracer_fixture(root)
    frozen = write_frozen(root / "frozen.json", **{"KME-L": TRACER_POP})
    outd = root / "m"
    rc, out, err = run_cli(d_args(root, root / "projects" / "-home-x-kme-fixture", frozen, outd))
    files = sorted(outd.glob("D-KME-L-*.md")) if outd.is_dir() else []
    if rc != 0 or len(files) != 1 or not files[0].name.startswith(f"D-KME-L-{utc_date()}"):
        return False, f"rc={rc} files={[f.name for f in files]} err={err[-200:]}"
    front, res = parse_measurement(files[0].read_text(encoding="utf-8"))
    ok = (front.get("pillar") == "D" and front.get("denominator") == "KME-L"
          and front.get("population_match") == "exact" and front.get("terminal_evidence") is True
          and "kme_pillars.py" in front.get("command", "") and res["numerator"]["chars"] == 900)
    return ok, f"rc={rc} file={files[0].name} chars={res['numerator']['chars']} match={front.get('population_match')}"


def g_audit_byte_identical():
    base = scratch("bytes")
    projects = rich_fixture(base / "fx")
    old = old_tooldir(base)
    new_tools = REPO / "wiki" / "tools"
    args = ["--host", "local", "--expand", str(projects)]
    a = run_pipeline(old, base / "o", args)
    b = run_pipeline(new_tools, base / "n", args)
    diff = [k for k in sorted(a) if a[k] != b.get(k)]
    # the audit JSON must really contain the compaction, subagent and attachment data (not an empty equality)
    audit = json.loads(a["audit.json"])
    rich = (any(s["compactions"] for s in audit) and any(s["subagent_files"] for s in audit)
            and any(s["attach"] for s in audit))
    return (not diff and rich and len(audit) == 4), \
        f"files={len(a)} differing={diff} sessions={len(audit)} rich={rich} bytes={len(a['audit.json'])}"


def g_cli_usage():
    rc, out, err = run_main(["d"])
    return rc == 2, f"main(['d']) rc={rc}"


# =========================================================================== gates (task 2: expansion)
def other_args(project_dir, out_dir, label="FX-A", extra=()):
    return ["d", "--denominator", "OTHER", "--label", label, "--select", "all", "--until", "none",
            "--root", str(project_dir), "--out-dir", str(out_dir)] + list(extra)


def d_other(project_dir, extra=(), label="FX-A"):
    out_dir = scratch("out")
    rc, res, out, err = run_json(other_args(project_dir, out_dir, label, extra))
    return rc, res, out, err, out_dir


def pdir(root, project="-home-x-kme-fixture"):
    return Path(root) / "projects" / project


def g_population_drift():
    root = scratch("drift")
    tracer_fixture(root)
    drifted = dict(TRACER_POP, calls=TRACER_POP["calls"] + 1)
    frozen = write_frozen(root / "frozen.json", **{"KME-L": drifted})
    out_dir = root / "m"
    rc, res, _o, _e = run_json(d_args(root, pdir(root), frozen, out_dir))
    ok = (rc == 3 and res["population_match"] == "drifted" and "calls" in res["population_deltas"]
          and res["materiality"] == "UNMEASURED" and res["terminal_evidence"] is False
          and res["share_interval"] is None and res["share_measured_population"] is not None
          and len(list(out_dir.glob("D-KME-L-*.md"))) == 1)
    return ok, f"rc={rc} match={res['population_match']} deltas={res['population_deltas']} " \
               f"verdict={res['materiality']} share_measured={res['share_measured_population']}"


TABLE = [
    (([0.01, 0.02], "exact", 1.0), "< 3 %"),
    (([0.03, 0.05], "exact", 1.0), ">= 3 %"),
    (([0.02, 0.04], "exact", 1.0), "STRADDLES"),
    ((None, "exact", 1.0), "UNMEASURED"),
    (([0.01, 0.02], "drifted", 1.0), "UNMEASURED"),
    (([0.01, 0.02], "exact", 0.5), "UNMEASURED"),
    (([0.04, 0.06], "exact", 0.5), ">= 3 %"),
]


def g_verdict_table():
    bad = []
    for args, want in TABLE:
        got = kp.materiality(*args)[0]
        if got != want or got not in kp.VERDICTS:
            bad.append((args, want, got))
    return not bad, f"{len(TABLE)} rows, mismatches={bad}"


def g_unmeasured_not_below():
    inputs = [(None, "exact", 1.0), ([], "not_frozen", 1.0), ([0.01, 0.02], "drifted", 1.0),
              ([0.0, 0.0], "drifted", 1.0), ([0.01, 0.02], "exact", 0.5), ([0.0, 0.0], "exact", 0.0),
              ([0.01, 0.02], "not_frozen", None), ([0.0, 0.0], "exact", 0.999)]
    got = [kp.materiality(*a)[0] for a in inputs]
    bad = [(a, g) for a, g in zip(inputs, got) if g != "UNMEASURED"]
    return not bad, f"{len(inputs)} UNMEASURED-producing inputs, not UNMEASURED: {bad}"


def g_burden_model():
    a, b = kp.burden(400, 5, 4.0), kp.burden(400, 0, 4.0)
    return a == 240.0 and b == 0.0, f"burden(400,5,4.0)={a} burden(400,0,4.0)={b}"


def g_weighted_ledger():
    ledger = json.loads((REPO / kp.LEDGER_REL).read_text(encoding="utf-8"))
    want = ledger["frozen"]["denominators"]["KME-L"]["weighted_input_equivalent"]
    specs = kp.frozen_specs(REPO / kp.DENOMS_REL)
    got = round(kp.weighted(specs["KME-L"]["fields"]))
    return got == want == 1764247687, f"weighted={got} ledger={want}"


def g_population_equals_pipeline():
    base = scratch("pipe")
    projects = rich_fixture(base / "fx")
    out = run_pipeline(REPO / "wiki" / "tools", base / "w", ["--host", "local", "--expand", str(projects)])
    entry = json.loads(out["denom.json"])["KME-L"]
    sessions, fan, _d = kp.scan([str(projects)], True, "local", [], None)
    pop = kp.population(sessions, {"select": "kme"}, fan.kept, False)
    mine = {f: pop[f] for f in kp.POP_FIELDS}
    match, deltas = kp.compare_population(mine, {f: entry[f] for f in kp.POP_FIELDS})
    return match == "exact" and mine["sessions_dead"] == 1 and mine["sessions_active"] == 2, \
        f"match={match} deltas={deltas} mine={mine}"


def g_d_residency():
    root = scratch("resid")
    tracer_fixture(root)
    rc, res, _o, _e, _d = d_other(pdir(root))
    n = res["numerator"]
    want_lo = sum(300 / kp.CPT_HI * (2 + 0.1 * (r - 1)) for r in (2, 1, 1))
    want_hi = sum(300 / kp.CPT_LO * (2 + 0.1 * (r - 1)) for r in (2, 1, 1))
    lo, hi = n["weighted_interval"]
    ok = (abs(lo - want_lo) < 1e-9 and abs(hi - want_hi) < 1e-9 and n["chars_per_tool_use"] == 900 / 1
          and n["chars_per_call"] == 900 / 4)
    return ok, f"lo={lo:.6f}/{want_lo:.6f} hi={hi:.6f}/{want_hi:.6f} per_tool_use={n['chars_per_tool_use']} " \
               f"per_call={n['chars_per_call']}"


def two_call_session(root, project="-home-x-kme-fixture", session="s1"):
    fx = Fx(root, project=project, session=session)
    fx.human("go", ts(0))
    return fx


def g_d_only_additional_context():
    root = scratch("only")
    fx = two_call_session(root)
    hook_ctx(fx, ts(1), 300)
    fx.attachment("hook_success", ts(1), hookName="SessionStart:startup", stdout="X" * 5000, content="")
    fx.attachment("hook_system_message", ts(1), hookName="SessionStart:startup", content="Y" * 700)
    fx.attachment("hook_non_blocking_error", ts(1), hookName="Stop", stderr="boom")
    fx.assistant("m1", "r1", (10, 100, 0, 5), ts(2))
    fx.assistant("m2", "r2", (10, 0, 100, 5), ts(3))
    rc, res, _o, _e, _d = d_other(pdir(root))
    det = res["details"]
    oth = det["other_hook_attachments"]
    ok = (res["numerator"]["chars"] == 300 and oth.get("hook_success", [0, 0])[1] >= 5000
          and oth.get("hook_system_message", [0, 0])[0] == 1 and det["hook_errors"] == {"Stop": 1})
    return ok, f"chars={res['numerator']['chars']} other={oth} errors={det['hook_errors']}"


def g_d_unobserved():
    root = scratch("unobs")
    fx = two_call_session(root)
    fx.assistant("m1", "r1", (10, 100, 0, 5), ts(2))
    fx.assistant("m2", "r2", (10, 0, 100, 5), ts(3))
    rc, res, _o, _e, _d = d_other(pdir(root))
    return res["observability"] == 0.0 and res["materiality"] == "UNMEASURED" and rc == 3, \
        f"rc={rc} observability={res['observability']} verdict={res['materiality']}"


def g_d_silent():
    root = scratch("silent")
    fx = two_call_session(root)
    fx.attachment("hook_success", ts(1), hookName="SessionStart:startup", stdout="Z" * 4000, content="")
    fx.assistant("m1", "r1", (10, 100, 0, 5), ts(2))
    fx.assistant("m2", "r2", (10, 0, 100, 5), ts(3))
    rc, res, _o, _e, _d = d_other(pdir(root))
    return (res["numerator"]["chars"] == 0 and res["observability"] == 1.0 and res["materiality"] == "< 3 %"
            and rc == 0), f"rc={rc} chars={res['numerator']['chars']} obs={res['observability']} " \
                          f"verdict={res['materiality']}"


def g_d_subagent_scope():
    root = scratch("subscope")
    fx = two_call_session(root)
    hook_ctx(fx, ts(1), 300, ch="M")
    for i in range(1, 5):
        fx.assistant(f"m{i}", f"r{i}", (10, 0, 100, 5), ts(1 + i))
    sub = fx.subagent("ag1", "Explore")
    sub.human("sub", ts(1.5))
    hook_ctx(sub, ts(1.6), 300, ch="S")
    sub.assistant("s1", "rs1", (10, 0, 100, 5), ts(1.7))
    sub.assistant("s2", "rs2", (10, 0, 100, 5), ts(1.8))
    rc, res, _o, _e, _d = d_other(pdir(root))
    want_lo = 300 / kp.CPT_HI * (2 + 0.1 * 3) + 300 / kp.CPT_HI * (2 + 0.1 * 1)   # main: 4 calls, sub: 2 calls
    lo = res["numerator"]["weighted_interval"][0]
    return abs(lo - want_lo) < 1e-9, f"lo={lo:.6f} want={want_lo:.6f} (session-wide residency would be " \
                                     f"{300 / kp.CPT_HI * 2.5 * 2:.6f})"


def heavy_session(root, per_call_chars, n=10):
    fx = two_call_session(root)
    for i in range(n):
        hook_ctx(fx, ts(1 + 2 * i), per_call_chars)
        fx.assistant(f"m{i}", f"r{i}", (10, 0, 100000, 50), ts(2 + 2 * i))
    return fx


def g_d_positive():
    root = scratch("pos")
    heavy_session(root, 4000)
    rc, res, _o, _e, _d = d_other(pdir(root))
    ctl = scratch("posctl")
    heavy_session(ctl, 1)
    rc2, res2, _o2, _e2, _d2 = d_other(pdir(ctl))
    ok = (res["materiality"] == ">= 3 %" and res["second_workload_required"] is True
          and res2["materiality"] == "< 3 %" and res2["second_workload_required"] is False)
    return ok, f"4000 chars/call -> {res['materiality']} share={res['share_interval']} second={res['second_workload_required']}; " \
               f"1 char/call -> {res2['materiality']}"


def g_until_cutoff():
    root = scratch("cut")
    s1 = Fx(root)
    s1.human("go", ts(0))
    s1.assistant("m1", "r1", (10, 100, 0, 5), ts(2))
    s1.assistant("m2", "r2", (10, 0, 100, 5), ts(5))
    s1.meta()
    s1.assistant("m3", "r3", (10, 0, 100, 5), ts(9))
    s1.meta()
    Fx(root, session="s2").human("late", ts(12))
    cut = ts(6)
    rc, res, _o, _e, _d = d_other(pdir(root), ["--until", cut])
    rc0, res0, _o0, _e0, _d0 = d_other(pdir(root), ["--until", "none"])
    p, p0 = res["population"], res0["population"]
    # keep() unit rows: trailing meta lines inherit the previous timestamp; leading ones take the file's first
    lines = scratch("keepunit") / "f.jsonl"
    f = Fx(root, path=lines)
    f.meta()
    f.human("a", ts(8))
    f.meta()
    f.human("b", ts(20))
    f.meta()
    rows = [json.loads(x) for x in lines.read_text().splitlines()]
    k_cut = kp.make_keep(None, kp.parse_instant(ts(10)))
    got = [k_cut(str(lines), o) for o in rows]
    k_no_ts = kp.make_keep(None, kp.parse_instant(ts(10)))
    nots = scratch("nots") / "g.jsonl"
    Fx(root, path=nots).meta().meta()
    got_no_ts = [k_no_ts(str(nots), json.loads(x)) for x in nots.read_text().splitlines()]
    ok = (p["calls"] == 2 and p["sessions_active"] == 1 and p["sessions_dead"] == 0
          and p0["calls"] == 3 and p0["sessions_dead"] == 1
          and got == [True, True, True, False, False] and got_no_ts == [False, False])
    return ok, f"until: calls={p['calls']} dead={p['sessions_dead']}; none: calls={p0['calls']} " \
               f"dead={p0['sessions_dead']}; keep rows={got} no-ts file={got_no_ts}"


def g_no_overwrite():
    root = scratch("noov")
    tracer_fixture(root)
    out_dir = scratch("noov-out")
    args = other_args(pdir(root), out_dir)
    rc1, _o1, _e1 = run_main(args)
    first = sorted(out_dir.glob("D-FX-A-*.md"))
    h1 = first[0].read_bytes() if first else b""
    rc2, _o2, _e2 = run_main(args)
    rc3, _o3, _e3 = run_main(args)
    names = sorted(x.name for x in out_dir.glob("D-FX-A-*.md"))
    ok = (rc1 == rc2 == rc3 == 0 and len(names) == 3 and first[0].read_bytes() == h1
          and any(n.endswith("-2.md") for n in names) and any(n.endswith("-3.md") for n in names))
    return ok, f"files={names}"


def g_other_label():
    root = scratch("lab")
    tracer_fixture(root)
    out_dir = scratch("lab-out")
    bad = {}
    for lab in ("KME-L", "KME-G", "CPP-D-W7", "lower-case", "X"):
        rc, _o, _e = run_main(other_args(pdir(root), out_dir, lab))
        bad[lab] = rc
    rc_nolabel, _o, _e = run_main(["d", "--denominator", "OTHER", "--select", "all", "--until", "none", "--root",
                                   str(pdir(root)), "--out-dir", str(out_dir)])
    wrote_on_refusal = list(out_dir.glob("*.md"))
    rc_ok, res, _o2, _e2 = run_json(other_args(pdir(root), out_dir, "GEX44-B001"))
    files = sorted(x.name for x in out_dir.glob("*.md"))
    ok = (all(v == 2 for v in bad.values()) and rc_nolabel == 2 and not wrote_on_refusal and rc_ok == 0
          and res["denominator_kind"] == "named_workload" and res["denominator"] == "GEX44-B001"
          and files == [f"D-GEX44-B001-{utc_date()}.md"])
    return ok, f"refusals={bad} nolabel={rc_nolabel} files={files} kind={res['denominator_kind']}"


def g_role_table():
    root = scratch("roles")
    tracer_fixture(root)
    exact = write_frozen(root / "f_exact.json", **{"KME-L": TRACER_POP, "KME-G": TRACER_POP})
    drift = write_frozen(root / "f_drift.json", **{"KME-L": dict(TRACER_POP, calls=5),
                                                   "KME-G": dict(TRACER_POP, calls=5)})
    pd = pdir(root)
    rows = []

    def run(extra, frozen, den):
        return run_json(d_args(root, pd, frozen, scratch("rt-out"), denominator=den, extra=extra))

    def row(name, rc, res, want):
        got = None if res is None else (res["evidence_role"], res["terminal_evidence"], res["second_workload_valid"])
        rows.append((name, rc, got, want, got == want))

    rc, res, _o, _e = run([], exact, "KME-L")
    row("KME-L exact", rc, res, ("primary", True, None))
    rc, res, _o, _e = run([], drift, "KME-L")
    row("KME-L drifted", rc, res, ("primary", False, None))
    rc, res, _o, _e = run([], exact, "KME-G")
    row("KME-G", rc, res, ("smoke", False, None))
    rc, res, _o, _e = run_json(other_args(pd, scratch("rt-out")))
    row("OTHER", rc, res, ("smoke", False, None))
    rc, res, _o, _e = run_json(other_args(pd, scratch("rt-out"), extra=["--role", "second_workload"]))
    row("OTHER second_workload", rc, res, ("second_workload", False, True))
    rc, _o, _e = run_main(d_args(root, pd, exact, scratch("rt-out"), extra=["--role", "second_workload"]))
    rows.append(("KME-L second_workload", rc, rc, 2, rc == 2))
    rc, res, _o, _e = run(["--role", "second_workload"], drift, "KME-G")
    row("KME-G second_workload drifted", rc, res, ("second_workload", False, False))
    bad = [r[0] for r in rows if not r[4]]
    return not bad, f"{len(rows)} rows, wrong={bad} got={[(r[0], r[2]) for r in rows if not r[4]]}"


CANARY = "sk-ant-" + "A" * 50


def g_no_secret():
    root = scratch("sec")
    fx = two_call_session(root)
    fx.attachment("hook_additional_context", ts(1), content=["ctx " + CANARY], hookName="PreToolUse:" + CANARY,
                  hookEvent="PreToolUse")
    fx.assistant("m1", "r1", (10, 100, 0, 5), ts(2), text="said " + CANARY,
                 tool_uses=[("tu1", "Bash", {"command": "echo " + CANARY})])
    fx.tool_result("tu1", "out " + CANARY, ts(3))
    fx.assistant("m2", "r2", (10, 0, 100, 5), ts(4))
    raw = fx.path.read_text()
    out_dir = scratch("sec-out")
    rc, out, err = run_main(other_args(pdir(root), out_dir, extra=["--json"]))
    written = "".join(p.read_text(encoding="utf-8") for p in out_dir.glob("*.md"))
    present = [n for n, t in (("file", written), ("stdout", out), ("stderr", err)) if CANARY in t]
    return CANARY in raw and written != "" and not present and rc in (0, 3), \
        f"fixture holds canary={CANARY in raw}; leaked into {present}; rc={rc}"


def tree_state(root):
    import hashlib
    st = {}
    for dp, dns, fns in os.walk(root):
        for n in dns + fns:
            full = os.path.join(dp, n)
            sx = os.lstat(full)
            h = hashlib.sha256(open(full, "rb").read()).hexdigest() if stat.S_ISREG(sx.st_mode) else ""
            st[os.path.relpath(full, root)] = (sx.st_size, sx.st_mtime_ns, h)
    return st


def g_read_only():
    root = scratch("ro")
    tracer_fixture(root)
    tree = root / "projects"
    for dp, dns, fns in os.walk(tree):
        for n in fns:
            os.chmod(os.path.join(dp, n), 0o444)
    for dp, dns, fns in os.walk(tree, topdown=False):
        os.chmod(dp, 0o555)
    before = tree_state(tree)
    rc, _o, _e = run_main(other_args(pdir(root), scratch("ro-out")))
    after = tree_state(tree)
    return rc == 0 and before == after and len(before) >= 2, f"rc={rc} entries={len(before)} unchanged={before == after}"


def g_freeze_instant():
    try:
        p = subprocess.run(["git", "show", "-s", "--format=%cI", FROZEN_SHA], cwd=str(REPO), capture_output=True,
                           text=True, timeout=30)
    except OSError:
        return "SKIP", "git unavailable"
    if p.returncode != 0:
        return "SKIP", f"git show failed rc={p.returncode}"
    t = datetime.datetime.fromisoformat(p.stdout.strip()).astimezone(datetime.timezone.utc)
    got = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    pinned = (REPO / "vault/programs/incremental-cognition/FROZEN_AT").read_text().strip()
    return got == kp.FREEZE_INSTANT and pinned == FROZEN_SHA, f"git={got} FREEZE_INSTANT={kp.FREEZE_INSTANT}"


# --------------------------------------------------------------------------- real-corpus gates (read-only)
ENV_ROOTS = ["/home/kobii/a5-env/home/.claude/projects", "/home/kobii/a7-env/home/.claude/projects",
             "/home/kobii/b001-env/home/.claude/projects"]
MAIN_ROOT = "/home/kobii/.claude/projects"


def stat_snapshot(roots):
    snap = {}
    for r in roots:
        for dp, _dns, fns in os.walk(r):
            for n in fns:
                full = os.path.join(dp, n)
                try:
                    sx = os.stat(full)
                except OSError:
                    continue
                snap[full] = (sx.st_size, sx.st_mtime_ns)
    return snap


def copy_pinned(roots, dest):
    """Real copies (never hardlinks) pinned by a (relpath, size, mtime_ns) snapshot of the originals before and
    after copying. Returns (copied roots, 'ok' | 'moved')."""
    for attempt in range(2):
        before = stat_snapshot(roots)
        out = []
        for i, r in enumerate(roots):
            target = dest / f"try{attempt}" / f"r{i}"
            shutil.copytree(r, target)
            out.append(str(target))
        if stat_snapshot(roots) == before:
            return out, "ok"
    return [], "moved"


def g_audit_byte_identical_real():
    if not all(os.path.isdir(r) for r in ENV_ROOTS):
        return "SKIP", "env roots absent"
    need = max(300 * 1024 * 1024, 1)
    tmp = tempfile.gettempdir()
    free = shutil.disk_usage(tmp).free
    if free < need:
        return "SKIP", f"free disk {free // 2**20} MB in {tmp} < 300 MB"
    with tempfile.TemporaryDirectory(prefix="kmep-real-", dir=tmp) as td:
        td = Path(td)
        copies, state = copy_pinned(ENV_ROOTS, td)
        if state != "ok":
            return "INCONCLUSIVE", "originals moved during both copies"
        old = old_tooldir(td)
        args = ["--host", "gex44", "--expand"] + copies
        a = run_pipeline(old, td / "o", args)
        b = run_pipeline(REPO / "wiki" / "tools", td / "n", args)
        diff = [k for k in sorted(a) if a[k] != b.get(k)]
        n_sess = len(json.loads(a["audit.json"]))
        return not diff and n_sess > 100, f"sessions={n_sess} files={len(a)} differing={diff} audit_bytes={len(a['audit.json'])}"


def g_kmeg_frozen_real():
    roots = ENV_ROOTS + [MAIN_ROOT]
    if not all(os.path.isdir(r) for r in roots):
        return "SKIP", "corpus roots absent"
    out_dir = scratch("kmeg-out")
    args = ["d", "--denominator", "KME-G", "--until", kp.FREEZE_INSTANT, "--expand", "--out-dir", str(out_dir)]
    for r in roots:
        args += ["--root", r]
    rc, res, _o, _e = run_json(args)
    frozen = kp.frozen_specs(REPO / kp.DENOMS_REL)["KME-G"]["fields"]
    mine = {f: res["population"][f] for f in kp.POP_FIELDS}
    return mine == frozen and res["population_match"] == "exact", f"rc={rc} measured={mine} frozen_equal={mine == frozen}"


# =========================================================================== pillar E / F fixtures
def pil_args(pillar, project_dir, out_dir, label="FX-A", extra=()):
    return [pillar, "--denominator", "OTHER", "--label", label, "--select", "all", "--until", "none",
            "--root", str(project_dir), "--out-dir", str(out_dir)] + list(extra)


def pil_other(pillar, root, extra=(), label="FX-A", project="-home-x-kme-fixture"):
    out_dir = scratch("out")
    rc, res, out, err = run_json(pil_args(pillar, pdir(root, project), out_dir, label, extra))
    return rc, res, out, err, out_dir


def call(fx, n, tool_uses=(), usage=(10, 0, 1000, 5)):
    """One assistant call c<n>; timestamps are monotone in n."""
    return fx.assistant(f"m{n}", f"r{n}", usage, ts(10 + 2 * n), tool_uses=list(tool_uses))


def rd(fx, n, tid, path, text, **rng):
    """Assistant call n carrying a Read of `path`, followed by its tool_result."""
    inp = dict({"file_path": path}, **rng)
    call(fx, n, [(tid, "Read", inp)])
    fx.tool_result(tid, text, ts(10 + 2 * n + 1))
    return fx


def klass(res, name):
    return res["details"]["classes"].get(name, {"count": 0, "chars": 0, "char_x_calls": 0})


E_BODY = "def f():\n" + "x = 1\n" * 500          # a stable 3,000-char file body
E_BODY = (E_BODY + "#" * 3000)[:3000]


def g_e_tracer_e2e():
    root = scratch("etracer")
    fx = Fx(root, project="-home-x-kme-e")
    fx.human("start", ts(0))
    marker = "UNIQUE-CONTENT-MARKER-E"
    body = (marker + "\n" + E_BODY)[:3000]
    rd(fx, 0, "r1", "/w/big.py", body)
    call(fx, 1)
    rd(fx, 2, "r2", "/w/big.py", body)
    call(fx, 3)
    call(fx, 4)
    frozen = write_frozen(root / "frozen.json", **{"KME-L": {
        "sessions_active": 1, "sessions_dead": 0, "calls": 5, "input": 50, "cache_write": 0, "cache_read": 5000,
        "output": 25}})
    outd = root / "m"
    rc, out, err = run_main(["e", "--denominator", "KME-L", "--frozen-file", frozen, "--root",
                             str(root / "projects" / "-home-x-kme-e"), "--out-dir", str(outd)])
    files = sorted(outd.glob("E-KME-L-*.md")) if outd.is_dir() else []
    if rc != 0 or len(files) != 1:
        return False, f"rc={rc} files={[f.name for f in files]} err={err[-200:]}"
    text = files[0].read_text(encoding="utf-8")
    front, res = parse_measurement(text)
    c = klass(res, "identical_same_segment")
    resident = c["char_x_calls"] // c["chars"] if c["chars"] else None
    ok = (front["pillar"] == "E" and c["count"] == 1 and c["chars"] == 3000 and resident == 2
          and marker not in text and front["population_match"] == "exact")
    return ok, f"rc={rc} file={files[0].name} same_segment={c} resident={resident} marker_absent={marker not in text}"


GATES_E_TRACER = [("V-KMEP-E-E2E", g_e_tracer_e2e)]


# =========================================================================== gates (task 2: pillar E expansion)
def e_run(build, extra=(), project="-home-x-kme-fixture"):
    """build(fx) writes one main-thread transcript; returns (rc, result)."""
    root = scratch("e")
    fx = Fx(root, project=project)
    fx.human("go", ts(0))
    build(fx)
    rc, res, _o, _e, _d = pil_other("e", root, extra, project=project)
    return rc, res


def g_e_after_compaction():
    def build(fx):
        rd(fx, 0, "a", "/w/f.py", E_BODY)
        call(fx, 1)
        fx.compact(ts(10 + 2 * 1 + 1))
        rd(fx, 2, "b", "/w/f.py", E_BODY)
        call(fx, 3)
    rc, res = e_run(build)
    n = res["numerator"]
    c = klass(res, "identical_after_compaction")
    ok = (c["count"] == 1 and klass(res, "identical_same_segment")["count"] == 0 and n["weighted_lo"] == 0
          and n["weighted_hi"] > 0 and n["chars"] == 3000)
    return ok, f"after_compaction={c} lo={n['weighted_lo']} hi={n['weighted_hi']}"


def g_e_intervening_edit():
    def build(fx):
        rd(fx, 0, "a", "/w/f.py", E_BODY)
        call(fx, 1, [("ed", "Edit", {"file_path": "/w/f.py", "old_string": "x", "new_string": "y"})])
        fx.tool_result("ed", "edited", ts(10 + 2 + 1))
        rd(fx, 2, "b", "/w/f.py", E_BODY)
        call(fx, 3)
        # control: an Edit of ANOTHER path does not excuse the reread
        rd(fx, 4, "c", "/w/g.py", E_BODY)
        call(fx, 5, [("ed2", "Write", {"file_path": "/w/other.py", "content": "z"})])
        rd(fx, 6, "d", "/w/g.py", E_BODY)
        call(fx, 7)
    rc, res = e_run(build)
    n = res["numerator"]
    rw, same = klass(res, "rewritten_identical"), klass(res, "identical_same_segment")
    ok = rw["count"] == 1 and same["count"] == 1 and n["chars"] == 3000 and n["weighted_lo"] > 0
    return ok, f"rewritten_identical={rw} same_segment={same} numerator_chars={n['chars']}"


def g_e_changed_content():
    def build(fx):
        rd(fx, 0, "a", "/w/f.py", E_BODY)
        rd(fx, 1, "b", "/w/f.py", E_BODY + "!")                     # changed outside any tool write
        call(fx, 2, [("ed", "MultiEdit", {"file_path": "/w/f.py", "edits": []})])
        fx.tool_result("ed", "ok", ts(10 + 4 + 1))
        rd(fx, 3, "c", "/w/f.py", E_BODY + "!!")                    # changed after a write
        call(fx, 4)
    rc, res = e_run(build)
    ok = (klass(res, "changed_outside_tools")["count"] == 1 and klass(res, "changed_after_write")["count"] == 1
          and res["numerator"]["chars"] == 0)
    return ok, f"outside={klass(res, 'changed_outside_tools')['count']} after_write={klass(res, 'changed_after_write')['count']} " \
               f"numerator_chars={res['numerator']['chars']}"


def g_e_stub():
    stub = "File unchanged since last read. The content from the earlier Read tool_result is still current."
    def build(fx):
        rd(fx, 0, "a", "/w/f.py", E_BODY)
        rd(fx, 1, "b", "/w/f.py", stub)
        call(fx, 2)
    rc, res = e_run(build)
    st = klass(res, "stub")
    ok = (st["count"] == 1 and st["chars"] == len(stub) and klass(res, "identical_same_segment")["count"] == 0
          and res["numerator"]["chars"] == 0 and res["numerator"]["weighted_hi"] == 0)
    return ok, f"stub={st} identical={klass(res, 'identical_same_segment')['count']} numerator={res['numerator']['chars']}"


def g_e_range():
    def build(fx):
        rd(fx, 0, "a", "/w/f.py", E_BODY, offset=0, limit=100)
        rd(fx, 1, "b", "/w/f.py", E_BODY, offset=200, limit=100)    # other range: not a reread
        rd(fx, 2, "c", "/w/f.py", E_BODY, offset=0, limit=100)      # same range: a reread
        call(fx, 3)
    rc, res = e_run(build)
    ok = (klass(res, "first")["count"] == 2 and klass(res, "identical_same_segment")["count"] == 1)
    return ok, f"first={klass(res, 'first')['count']} identical={klass(res, 'identical_same_segment')['count']}"


def g_e_thread_scope():
    root = scratch("ethr")
    fx = Fx(root)
    fx.human("go", ts(0))
    rd(fx, 0, "a", "/w/f.py", E_BODY)
    call(fx, 1)
    sub = fx.subagent("ag1", "Explore")
    sub.human("sub", ts(5))
    rd(sub, 2, "sa", "/w/f.py", E_BODY)
    call(sub, 3)
    rc, res, _o, _e, _d = pil_other("e", root)
    ok = (klass(res, "first")["count"] == 2 and klass(res, "identical_same_segment")["count"] == 0
          and res["numerator"]["chars"] == 0)
    return ok, f"first={klass(res, 'first')['count']} identical={klass(res, 'identical_same_segment')['count']}"


def g_e_error_ignored():
    def build(fx):
        rd(fx, 0, "a", "/w/f.py", E_BODY)
        call(fx, 1, [("bad", "Read", {"file_path": "/w/f.py"})])
        fx.tool_result("bad", E_BODY, ts(10 + 2 + 1), is_error=True)
        rd(fx, 2, "c", "/w/f.py", E_BODY)
        call(fx, 3)
    rc, res = e_run(build)
    total = sum(c["count"] for c in res["details"]["classes"].values())
    ok = total == 2 and klass(res, "identical_same_segment")["count"] == 1
    return ok, f"events={total} identical={klass(res, 'identical_same_segment')['count']}"


BIG = "".join(f"line {i:05d} of a large source file\n" for i in range(700))[:20000]


def g_e_positive():
    root = scratch("epos")
    fx = Fx(root)
    fx.human("go", ts(0))
    for i in range(12):
        call(fx, i, [(f"t{i}", "Read", {"file_path": "/w/big.py"})], usage=(10, 0, 300000, 50))
        fx.tool_result(f"t{i}", BIG, ts(10 + 2 * i + 1))
    rc, res, _o, _e, _d = pil_other("e", root)
    ctl = scratch("eposctl")
    fx2 = Fx(ctl)
    fx2.human("go", ts(0))
    for i in range(12):          # same reads, but the file differs every time: no identical version
        call(fx2, i, [(f"t{i}", "Read", {"file_path": "/w/big.py"})], usage=(10, 0, 300000, 50))
        fx2.tool_result(f"t{i}", BIG[:-10] + f"{i:010d}", ts(10 + 2 * i + 1))
    rc2, res2, _o2, _e2, _d2 = pil_other("e", ctl)
    ok = (res["materiality"] == ">= 3 %" and res["second_workload_required"] is True
          and klass(res, "identical_same_segment")["count"] == 11
          and res2["materiality"] == "< 3 %" and res2["numerator"]["chars"] == 0)
    return ok, f"identical rereads -> {res['materiality']} share={res['share_interval']}; changing file -> {res2['materiality']}"


def g_e_absent():
    root = scratch("eabs")
    fx = Fx(root)
    fx.human("go", ts(0))
    call(fx, 0, [("b", "Bash", {"command": "ls"})])
    fx.tool_result("b", "x", ts(11))
    call(fx, 1)
    rc, res, _o, _e, _d = pil_other("e", root)
    n = res["numerator"]
    ok = (rc == 0 and n["chars"] == 0 and n["weighted_hi"] == 0 and res["materiality"] == "< 3 %"
          and res["observability"] == 1.0 and res["details"]["reads_total"] == 0)
    return ok, f"rc={rc} chars={n['chars']} verdict={res['materiality']} reads={res['details']['reads_total']}"


# =========================================================================== gates (task 2: pillar F)
DOC12K = "D" * 12000
H_CLAUDE = "/h/.claude"


def f_run(build, extra=()):
    root = scratch("f")
    fx = Fx(root)
    fx.human("go", ts(0))
    build(fx)
    rc, res, _o, _e, _d = pil_other("f", root, extra)
    return rc, res


def kind(res, k):
    return res["details"]["by_kind"].get(k, {"count": 0, "chars": 0})


def g_f_read_workflow():
    def build(fx):
        rd(fx, 0, "a", f"{H_CLAUDE}/gsd-core/workflows/execute-phase.md", DOC12K)
        call(fx, 1)
    rc, res = f_run(build)
    kinds = {kp.gsd_doc_kind(p): p for p in (f"{H_CLAUDE}/gsd-core/workflows/x.md", f"{H_CLAUDE}/get-shit-done/templates/y.md",
                                            f"{H_CLAUDE}\\gsd-core\\references\\z.md", f"{H_CLAUDE}/skills/gsd-autonomous/SKILL.md",
                                            f"{H_CLAUDE}/commands/gsd/plan-phase.md")}
    unit_ok = set(kinds) == {"workflow", "template", "reference", "skill", "command"}
    ok = unit_ok and kind(res, "workflow")["count"] == 1 and kind(res, "workflow")["chars"] == 12000
    return ok, f"kinds={sorted(k for k in kinds if k)} workflow={kind(res, 'workflow')}"


def g_f_file_attachment():
    def build(fx):
        fx.attachment("file", ts(5), filename=f"{H_CLAUDE}/gsd-core/references/ui-brand.md",
                      content={"type": "text", "file": {"filePath": f"{H_CLAUDE}/gsd-core/references/ui-brand.md",
                                                        "content": "R" * 5000, "numLines": 10}})
        fx.attachment("file", ts(5.5), filename=f"{H_CLAUDE}/gsd-core/templates/t.md", content="T" * 700)
        call(fx, 0)
    rc, res = f_run(build)
    ok = kind(res, "reference")["chars"] == 5000 and kind(res, "template")["chars"] == len("T" * 700)
    return ok, f"reference={kind(res, 'reference')} template={kind(res, 'template')}"


def g_f_skill_body():
    body = f"Base directory for this skill: {H_CLAUDE}/skills/gsd-autonomous\n\n" + "S" * 2400
    def build(fx):
        fx.meta_text(body, ts(5))
        call(fx, 0)
    rc, res = f_run(build)
    ok = kind(res, "skill_body")["count"] == 1 and kind(res, "skill_body")["chars"] == len(body)
    return ok, f"skill_body={kind(res, 'skill_body')} want chars={len(body)}"


def g_f_invoked_skills():
    def build(fx):
        fx.attachment("invoked_skills", ts(5), skills=[
            {"name": "gsd-plan-phase", "path": "userSettings:gsd-plan-phase", "content": "P" * 2000},
            {"name": "humanizer", "path": "userSettings:humanizer", "content": "H" * 900}])
        call(fx, 0)
    rc, res = f_run(build)
    ok = kind(res, "invoked_skill")["count"] == 1 and kind(res, "invoked_skill")["chars"] == 2000
    return ok, f"invoked_skill={kind(res, 'invoked_skill')}"


def g_f_command_body():
    body = "<command-name>/gsd:plan-phase</command-name>\n<objective>Create the plan</objective>\n" + "C" * 1500
    def build(fx):
        fx.human(body, ts(5))
        call(fx, 0)
    rc, res = f_run(build)
    ok = kind(res, "command_body")["count"] == 1 and kind(res, "command_body")["chars"] == len(body)
    return ok, f"command_body={kind(res, 'command_body')}"


def g_f_non_gsd():
    def build(fx):
        rd(fx, 0, "a", "/h/README.md", "R" * 4000)
        fx.meta_text("Base directory for this skill: /h/.claude/skills/humanizer\n\n" + "H" * 3000, ts(5))
        fx.attachment("file", ts(6), filename="/h/proj/README.md", content="Q" * 2000)
        fx.human("<command-name>/other</command-name>\n<objective>not gsd</objective>", ts(7))
        rd(fx, 1, "b", "/h/.claude/skills/humanizer/SKILL.md", "Z" * 900)
        call(fx, 2)
    rc, res = f_run(build)
    n = res["numerator"]
    ok = n["chars"] == 0 and res["details"]["by_kind"] == {} and n["weighted_hi"] == 0 and rc == 0
    return ok, f"chars={n['chars']} by_kind={res['details']['by_kind']}"


INIT_CMD = "node /h/.claude/gsd-core/bin/gsd-tools.cjs query init.plan-phase 3"


def g_f_init_paired():
    def build(fx):
        rd(fx, 0, "a", f"{H_CLAUDE}/gsd-core/workflows/plan-phase.md", DOC12K)
        call(fx, 1, [("i1", "Bash", {"command": INIT_CMD})])
        fx.tool_result("i1", "J" * 900, ts(10 + 2 + 1))
        call(fx, 2)
        fx.human("next turn", ts(40))                       # a later turn: doc only, no init
        rd(fx, 3, "b", f"{H_CLAUDE}/gsd-core/workflows/execute-phase.md", "E" * 5000)
        call(fx, 4)
    rc, res = f_run(build)
    d = res["details"]
    pt = d["paired_turns"]
    inits = [INIT_CMD, 'gsd_run query init.execute-phase "${PHASE}"', 'node "/x/gsd-tools" init plan-phase',
             "node gsd-tools.cjs init-something", "node gsd-tools.cjs query state.load", "ls gsd-tools"]
    matches = [bool(kp.INIT_RE.search(c)) for c in inits]
    ok = (pt["count"] == 1 and pt["doc_chars"] == 12000 and pt["init_chars"] == 900 and pt["ratio"] == 13.33
          and d["init_json_present"] is True and d["init"]["count"] == 1
          and matches == [True, True, True, False, False, False])
    return ok, f"paired={pt} init_json_present={d['init_json_present']} init={d['init']['count']} regex={matches}"


def g_f_init_absent():
    def build(fx):
        rd(fx, 0, "a", f"{H_CLAUDE}/gsd-core/workflows/plan-phase.md", DOC12K)
        call(fx, 1, [("s", "Bash", {"command": "node gsd-tools.cjs query state.load"})])
        fx.tool_result("s", "J" * 900, ts(10 + 3))
        call(fx, 2)
    rc, res = f_run(build)
    d = res["details"]
    pt = d["paired_turns"]
    # control: an init call exists but its turn carries no workflow doc -> still no ratio, never 0
    def build2(fx):
        call(fx, 0, [("i1", "Bash", {"command": INIT_CMD})])
        fx.tool_result("i1", "J" * 900, ts(11))
        call(fx, 1)
    rc2, res2 = f_run(build2)
    d2 = res2["details"]
    ok = (d["init_json_present"] is False and pt["ratio"] is None and pt["count"] == 0
          and res["numerator"]["chars"] == 12000
          and d2["init_json_present"] is True and d2["paired_turns"]["ratio"] is None)
    return ok, f"no init: present={d['init_json_present']} ratio={pt['ratio']}; init without doc: " \
               f"present={d2['init_json_present']} ratio={d2['paired_turns']['ratio']}"


def g_f_positive():
    root = scratch("fpos")
    fx = Fx(root)
    fx.human("go", ts(0))
    for i in range(12):
        call(fx, i, [(f"t{i}", "Read", {"file_path": f"{H_CLAUDE}/gsd-core/workflows/execute-phase.md"})],
             usage=(10, 0, 300000, 50))
        fx.tool_result(f"t{i}", "G" * 20000, ts(10 + 2 * i + 1))
    rc, res, _o, _e, _d = pil_other("f", root)
    ctl = scratch("fposctl")
    fx2 = Fx(ctl)
    fx2.human("go", ts(0))
    for i in range(12):
        call(fx2, i, [(f"t{i}", "Read", {"file_path": f"/h/proj/notes{i}.md"})], usage=(10, 0, 300000, 50))
        fx2.tool_result(f"t{i}", "G" * 20000, ts(10 + 2 * i + 1))
    rc2, res2, _o2, _e2, _d2 = pil_other("f", ctl)
    ok = (res["materiality"] == ">= 3 %" and res["second_workload_required"] is True
          and res2["materiality"] == "< 3 %" and res2["numerator"]["chars"] == 0)
    return ok, f"gsd doc every turn -> {res['materiality']} share={res['share_interval']}; non-gsd reads -> {res2['materiality']}"


GATES_PILLAR_EF = [
    ("V-KMEP-E-AFTER-COMPACTION", g_e_after_compaction),
    ("V-KMEP-E-INTERVENING-EDIT", g_e_intervening_edit),
    ("V-KMEP-E-CHANGED-CONTENT", g_e_changed_content),
    ("V-KMEP-E-STUB", g_e_stub),
    ("V-KMEP-E-RANGE", g_e_range),
    ("V-KMEP-E-THREAD-SCOPE", g_e_thread_scope),
    ("V-KMEP-E-ERROR-IGNORED", g_e_error_ignored),
    ("V-KMEP-E-POSITIVE", g_e_positive),
    ("V-KMEP-E-ABSENT", g_e_absent),
    ("V-KMEP-F-READ-WORKFLOW", g_f_read_workflow),
    ("V-KMEP-F-FILE-ATTACHMENT", g_f_file_attachment),
    ("V-KMEP-F-SKILL-BODY", g_f_skill_body),
    ("V-KMEP-F-INVOKED-SKILLS", g_f_invoked_skills),
    ("V-KMEP-F-COMMAND-BODY", g_f_command_body),
    ("V-KMEP-F-NON-GSD", g_f_non_gsd),
    ("V-KMEP-F-INIT-PAIRED", g_f_init_paired),
    ("V-KMEP-F-INIT-ABSENT", g_f_init_absent),
    ("V-KMEP-F-POSITIVE", g_f_positive),
]


# =========================================================================== pillar G / H fixtures
GP = "-home-x-kme-g"
C6_TEXT = ("C6 result: listing hiding FALSIFIED. 134 name-only overrides moved the skill listing from 29,991 to "
           "30,002 chars; startup tokens did not fall.")
K4_TEXT = ("K4 plan: re-test listing hiding behind a gateway. Move 133 pageable skills to user-invocable-only and "
           "measure startup tokens again.")


def g_session(root, session, t, text, project=GP, usage=(10, 0, 1000, 5), n=0):
    """One session of one human prompt and one assistant call carrying `text`."""
    fx = Fx(root, project=project, session=session)
    fx.human("go", ts(t - 1))
    fx.assistant(f"{session}-m{n}", f"{session}-r{n}", usage, ts(t), text=text)
    return fx


def g_pair(first_text, second_text, t_first=-3 * 86400, t_second=-2 * 86400):
    root = scratch("g")
    g_session(root, "sA", t_first, first_text)
    g_session(root, "sB", t_second, second_text)
    return root


def g_other(root, extra=(), label="FX-A"):
    out_dir = scratch("out")
    rc, res, out, err = run_json(["g", "--denominator", "OTHER", "--label", label, "--select", "all",
                                  "--until", "none", "--root", str(pdir(root, GP)), "--out-dir", str(out_dir)]
                                 + list(extra))
    return rc, res, out, err, out_dir


def g_det(res):
    d = res["details"]
    return d["retested_falsifications"], d["relitigated_sealed"], d


def g_c6_k4_positive():
    root = g_pair(C6_TEXT, K4_TEXT)
    frozen = write_frozen(root / "frozen.json", **{"KME-L": {
        "sessions_active": 2, "sessions_dead": 0, "calls": 2, "input": 20, "cache_write": 0, "cache_read": 2000,
        "output": 10}})
    outd = root / "m"
    rc, out, err = run_main(["g", "--denominator", "KME-L", "--frozen-file", frozen, "--root",
                             str(pdir(root, GP)), "--out-dir", str(outd)])
    files = sorted(outd.glob("G-KME-L-*.md")) if outd.is_dir() else []
    if rc != 0 or len(files) != 1:
        return False, f"rc={rc} files={[f.name for f in files]} err={err[-200:]}"
    text = files[0].read_text(encoding="utf-8")
    front, res = parse_measurement(text)
    rt, _sealed, det = g_det(res)
    si = res["share_interval"]
    subjects = [m["subject"] for m in det["samples"]]
    ok = (front["pillar"] == "G" and front["population_match"] == "exact" and rt["strict"] == 1
          and rt["loose"] >= 1 and subjects == ["listing hiding"] and si is not None and si[0] <= si[1]
          and "startup tokens did not fall" not in text)
    return ok, f"rc={rc} strict={rt['strict']} loose={rt['loose']} subjects={subjects} share={si}"


GATES_G_TRACER = [("V-KMEP-G-C6-K4-POSITIVE", g_c6_k4_positive)]


GATES_EXPANSION = [
    ("V-KMEP-POPULATION-DRIFT", g_population_drift),
    ("V-KMEP-VERDICT-TABLE", g_verdict_table),
    ("V-KMEP-UNMEASURED-NOT-BELOW", g_unmeasured_not_below),
    ("V-KMEP-BURDEN-MODEL", g_burden_model),
    ("V-KMEP-WEIGHTED-LEDGER", g_weighted_ledger),
    ("V-KMEP-POPULATION-EQUALS-PIPELINE", g_population_equals_pipeline),
    ("V-KMEP-D-RESIDENCY", g_d_residency),
    ("V-KMEP-D-ONLY-ADDITIONAL-CONTEXT", g_d_only_additional_context),
    ("V-KMEP-D-UNOBSERVED", g_d_unobserved),
    ("V-KMEP-D-SILENT", g_d_silent),
    ("V-KMEP-D-SUBAGENT-SCOPE", g_d_subagent_scope),
    ("V-KMEP-D-POSITIVE", g_d_positive),
    ("V-KMEP-UNTIL-CUTOFF", g_until_cutoff),
    ("V-KMEP-NO-OVERWRITE", g_no_overwrite),
    ("V-KMEP-OTHER-LABEL", g_other_label),
    ("V-KMEP-ROLE-TABLE", g_role_table),
    ("V-KMEP-NO-SECRET", g_no_secret),
    ("V-KMEP-READ-ONLY", g_read_only),
    ("V-KMEP-FREEZE-INSTANT", g_freeze_instant),
]
GATES_REAL = [
    ("V-KMEP-AUDIT-BYTE-IDENTICAL-REAL", g_audit_byte_identical_real),
    ("V-KMEP-KMEG-FROZEN-REAL", g_kmeg_frozen_real),
]


GATES_TRACER = [
    ("V-KMEP-TRACER-D-E2E", g_tracer_e2e),
    ("V-KMEP-AUDIT-BYTE-IDENTICAL", g_audit_byte_identical),
    ("V-KMEP-CLI-USAGE", g_cli_usage),
]
GATES = list(GATES_TRACER) + GATES_EXPANSION + GATES_E_TRACER + GATES_PILLAR_EF + GATES_G_TRACER + GATES_REAL


def summary_line() -> str:
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    n = sum(1 for r in counted if r[0] == "PASS")
    m = len(counted)
    sk = sum(1 for r in RESULTS if r[0] == "SKIP")
    inc = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    return f"KMEP_PASS={n}/{m}  threshold={m}/{m}  skipped={sk}  inconclusive={inc}"


def run_all() -> int:
    for name, fn in GATES:
        run_gate(name, fn)
    print(summary_line())
    counted = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    return 0 if counted and all(r[0] == "PASS" for r in counted) else 1


# --------------------------------------------------------------------------- mutation drill
GATE_FN = dict(GATES)
DRILL_GATES = [n for n, _ in GATES_TRACER + GATES_EXPANSION + GATES_E_TRACER + GATES_PILLAR_EF + GATES_G_TRACER]    # the -REAL gates are excluded for speed


def _quiet(names) -> dict:
    """Run the named gates with printing off; {gate: passed} for the ones that ran to PASS/FAIL."""
    start = len(RESULTS)
    QUIET[0] = True
    try:
        for n in names:
            run_gate(n, GATE_FN[n])
    finally:
        QUIET[0] = False
    return {g: st == "PASS" for st, g, _ in RESULTS[start:] if st in ("PASS", "FAIL")}


def _patch(attr, value):
    saved = getattr(kp, attr)
    setattr(kp, attr, value)
    return lambda: setattr(kp, attr, saved)


def _m_unmeasured_to_below():
    real = kp.materiality

    def mutant(*a, **k):
        v, r = real(*a, **k)
        return ("< 3 %", r) if v == "UNMEASURED" else (v, r)
    return _patch("materiality", mutant)


def _m_always_exact():
    return _patch("compare_population", lambda measured, frozen: ("exact", {}))


def _m_resident_one():
    return _patch("resident_calls", lambda idx, compact_points, n_order: 1)


def _m_every_hook_type():
    return _patch("counts_for_d", lambda atype: True)


def _m_until_ignored():
    return _patch("make_keep", lambda since, until: (lambda path, o: True))


def _m_truncating_writer():
    def mutant(out_dir, stem, text):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{stem}.md"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return path
    return _patch("write_measurement", mutant)


def _m_e_ignores_compaction():
    real = kp.classify_read
    return _patch("classify_read", lambda prev, h, wcount, seg: real(prev, h, wcount, prev[2] if prev else seg))


def _m_e_stub_never():
    return _patch("is_stub_text", lambda text: False)


def _m_e_writes_ignored():
    real = kp.classify_read
    return _patch("classify_read", lambda prev, h, wcount, seg: real(prev, h, prev[1] if prev else wcount, seg))


def _m_f_kind_none():
    return _patch("gsd_doc_kind", lambda path: None)


def _m_f_ratio_zero():
    real = kp.pair_ratio
    return _patch("pair_ratio", lambda doc, init, n: 0.0 if n < 1 else real(doc, init, n))


MUTANTS = [
    ("M1 materiality maps UNMEASURED to '< 3 %'", _m_unmeasured_to_below, ["V-KMEP-UNMEASURED-NOT-BELOW"]),
    ("M2 compare_population always exact", _m_always_exact, ["V-KMEP-POPULATION-DRIFT"]),
    ("M3 D resident calls forced to 1", _m_resident_one, ["V-KMEP-D-RESIDENCY"]),
    ("M4 D counts every hook attachment type", _m_every_hook_type, ["V-KMEP-D-ONLY-ADDITIONAL-CONTEXT"]),
    ("M5 make_keep ignores until", _m_until_ignored, ["V-KMEP-UNTIL-CUTOFF"]),
    ("M6 writer truncates instead of suffixing", _m_truncating_writer, ["V-KMEP-NO-OVERWRITE"]),
    ("M7 E ignores compaction boundaries (every identical reread is same-segment)", _m_e_ignores_compaction,
     ["V-KMEP-E-AFTER-COMPACTION"]),
    ("M8 E stub test never matches", _m_e_stub_never, ["V-KMEP-E-STUB"]),
    ("M9 E writes never mark a path", _m_e_writes_ignored, ["V-KMEP-E-INTERVENING-EDIT"]),
    ("M10 F gsd_doc_kind always None", _m_f_kind_none, ["V-KMEP-F-READ-WORKFLOW", "V-KMEP-F-POSITIVE"]),
    ("M11 F paired ratio reads 0 when no init was seen", _m_f_ratio_zero, ["V-KMEP-F-INIT-ABSENT"]),
]


def run_drill() -> int:
    """Control first (all in-process gates green), each mutant applied and restored, then an unmutated rerun."""
    control = _quiet(DRILL_GATES)
    control_ok = len(control) == len(DRILL_GATES) and all(control.values())
    print(f"{'PASS' if control_ok else 'FAIL'} DRILL-CONTROL unmutated run: {sum(control.values())}/{len(control)} gates green")
    killed = 0
    for label, apply, targets in MUTANTS:
        restore = apply()
        try:
            seen = _quiet(targets)
        finally:
            restore()
        by = [t for t in targets if seen.get(t) is False]
        if len(by) == len(targets):
            killed += 1
            print(f"KILLED {label} by {', '.join(by)}")
        else:
            print(f"SURVIVED {label} (still green or absent: {', '.join(t for t in targets if seen.get(t) is not False)})")
    after = _quiet(DRILL_GATES)
    clean = len(after) == len(DRILL_GATES) and all(after.values())
    print(f"{'PASS' if clean else 'FAIL'} DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: {sum(after.values())}/{len(after)} gates green")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
