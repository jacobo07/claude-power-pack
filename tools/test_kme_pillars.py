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
import re
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


FOLLOW_DEFAULTS = [True]


def run_main(args):
    """In-process main() with stdout/stderr captured, so a drill's monkeypatch reaches it.

    Fixture runs pass a scratch --frozen-file / --frozen-ce-ledger. The instrument (WR-07) only calls a frozen source
    the committed default, so while FOLLOW_DEFAULTS is on this runner points the module's default paths at the
    scratch files the call names (a patch of kp.DENOMS_REL / kp.CE_LEDGER_REL, which `REPO / abs` resolves to the
    scratch path). Gates about the non-default behaviour turn it off or run the CLI as a subprocess."""
    args = list(args)
    saved = (kp.DENOMS_REL, kp.CE_LEDGER_REL)
    if FOLLOW_DEFAULTS[0]:
        if "--frozen-file" in args:
            kp.DENOMS_REL = args[args.index("--frozen-file") + 1]
        if "--frozen-ce-ledger" in args:
            kp.CE_LEDGER_REL = args[args.index("--frozen-ce-ledger") + 1]
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = kp.main(args)
    finally:
        kp.DENOMS_REL, kp.CE_LEDGER_REL = saved
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
          and front.get("population_match") == "exact" and front.get("terminal_evidence") is False
          and "frozen source is not the repo default" in front.get("terminal_evidence_reason", "")
          and front.get("frozen_source", {}).get("all_default") is False
          and "kme_pillars.py" in front.get("command", "") and res["numerator"]["chars"] == 900)
    return ok, f"rc={rc} file={files[0].name} chars={res['numerator']['chars']} match={front.get('population_match')} " \
               f"terminal={front.get('terminal_evidence')} (scratch frozen file is not the committed default)"


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


# =========================================================================== gates (task 2: pillar G poles)
G_CITE_TEXT = ("Listing hiding was already falsified in C6 and K4, so we do not re-test it; the plugin gateway is "
               "the next lever.")


def g_run_pair(first, second, **kw):
    root = g_pair(first, second, **kw)
    rc, res, _o, _e, _d = g_other(root)
    return rc, res


def g_citation_is_reuse():
    rc, res = g_run_pair(C6_TEXT, G_CITE_TEXT)
    rt, _s, det = g_det(res)
    ok = rc == 0 and rt["strict"] == 0 and rt["loose"] == 0 and det["reuse_citations"] == 1 \
        and det["candidates"]["retest"] == 0
    return ok, f"rc={rc} strict={rt['strict']} loose={rt['loose']} reuse={det['reuse_citations']} cands={det['candidates']}"


def g_negated_retest():
    rc, res = g_run_pair(C6_TEXT, "We do not re-test listing hiding.")
    rt, _s, det = g_det(res)
    rc2, res2 = g_run_pair(C6_TEXT, "We will re-test listing hiding.")        # control: the same sentence, not negated
    rt2, _s2, _d2 = g_det(res2)
    neg = [bool(kp.RETEST_RE.search(kp.strip_negated(x))) for x in
           ("do not re-test it", "don't retest it", "we never re-run this", "no need to try again", "re-test it")]
    ok = rc == 0 and rt["strict"] == 0 and det["candidates"]["retest"] == 0 and rt2["strict"] == 1 \
        and neg == [False, False, False, False, True]
    return ok, f"negated strict={rt['strict']} cands={det['candidates']['retest']}; control strict={rt2['strict']}; strip={neg}"


def g_unrelated():
    rc, res = g_run_pair(C6_TEXT, "Re-run the arena drill with the new seed.")
    rt, _s, det = g_det(res)
    ok = rc == 0 and rt["strict"] == 0 and rt["loose"] == 0 and det["candidates"]["retest"] == 1 and det["samples"] == []
    return ok, f"strict={rt['strict']} loose={rt['loose']} cands={det['candidates']}"


def g_order():
    rc, res = g_run_pair(C6_TEXT, K4_TEXT, t_first=-2 * 86400, t_second=-3 * 86400)    # the re-test comes FIRST in time
    rt, _s, det = g_det(res)
    rc2, res2 = g_run_pair(C6_TEXT, K4_TEXT)                                              # control: right order
    rt2, _s2, _d2 = g_det(res2)
    ok = rc == 0 and rt["strict"] == 0 and rt["loose"] == 0 and det["candidates"]["retest"] == 1 and rt2["strict"] == 1
    return ok, f"retest before falsification: strict={rt['strict']} loose={rt['loose']}; control strict={rt2['strict']}"


def g_sealed_relitigated():
    rc, res = g_run_pair("D-03 sealed: commits use pathspec only.", "Reopen D-03: commit with git add -A instead.")
    rt, sealed, det = g_det(res)
    ok = rc == 0 and sealed["records"] == 1 and sealed["strict"] == 1 and rt["records"] == 0 and rt["strict"] == 0 \
        and [m["subject"] for m in det["samples"]] == ["D-03"] and det["samples"][0]["kind"] == "sealed"
    return ok, f"sealed={sealed} falsified={rt} samples={det['samples']}"


def g_sealed_cited():
    rc, res = g_run_pair("D-03 sealed: commits use pathspec only.", "Per sealed D-03 we commit by pathspec.")
    _rt, sealed, det = g_det(res)
    ok = rc == 0 and sealed["strict"] == 0 and sealed["loose"] == 0 and det["reuse_citations"] == 1
    return ok, f"sealed={sealed} reuse={det['reuse_citations']}"


def g_interval():
    root = scratch("gint")
    g_session(root, "sA", -4 * 86400, C6_TEXT)
    g_session(root, "sB", -3 * 86400, "R1 result: cache warming FALSIFIED.")
    g_session(root, "sC", -2 * 86400, K4_TEXT)                                              # strict on listing hiding
    g_session(root, "sD", -1 * 86400, "Try again with warming of cache entries.")           # loose only on cache warming
    rc, res, _o, _e, _d = g_other(root)
    rt, _s, det = g_det(res)
    lo, hi = res["numerator"]["weighted_interval"]
    si = res["share_interval"]
    ok = (rc == 0 and rt["records"] == 2 and rt["strict"] == 1 and rt["loose"] == 2 and rt["strict"] <= rt["loose"]
          and si[0] <= si[1] and lo < hi and len(det["samples"]) == 1)
    return ok, f"falsified={rt} weighted=[{lo}, {hi}] share={si} samples={len(det['samples'])}"


def g_signature_safe():
    root = g_pair("C6 result: listing hiding FALSIFIED " + CANARY + ".",
                  "Re-test listing hiding with the key " + CANARY + " again.")
    rc, res, out, err, out_dir = g_other(root, extra=["--json"])
    written = "".join(p.read_text(encoding="utf-8") for p in out_dir.glob("*.md"))
    subjects = [m["subject"] for m in res["details"]["samples"]]
    import re as _re
    shape = all(_re.fullmatch(r"[a-z]{3,20}( [a-z]{3,20})?|[A-Z]{1,3}-\d{1,3}", x) for x in subjects)
    raw = "".join(p.read_text() for p in pdir(root, GP).glob("*.jsonl"))
    ok = CANARY in raw and written != "" and CANARY not in written + out + err and "sk-ant" not in written \
        and subjects == ["listing hiding"] and shape
    return ok, f"canary in fixture={CANARY in raw} leaked={CANARY in written + out + err} subjects={subjects}"


GATES_G_POLES = [
    ("V-KMEP-G-CITATION-IS-REUSE", g_citation_is_reuse),
    ("V-KMEP-G-NEGATED-RETEST", g_negated_retest),
    ("V-KMEP-G-UNRELATED", g_unrelated),
    ("V-KMEP-G-ORDER", g_order),
    ("V-KMEP-G-SEALED-RELITIGATED", g_sealed_relitigated),
    ("V-KMEP-G-SEALED-CITED", g_sealed_cited),
    ("V-KMEP-G-INTERVAL", g_interval),
    ("V-KMEP-G-SIGNATURE-SAFE", g_signature_safe),
]


# =========================================================================== gates (task 2: pillar H)
def h_run(build, extra=(), project="-home-x-kme-fixture"):
    root = scratch("h")
    fx = Fx(root, project=project)
    fx.human("go", ts(0))
    build(fx)
    rc, res, _o, _e, _d = pil_other("h", root, extra, project=project)
    return rc, res


TEST_CMD = "python3 tools/test_x.py"
W135 = 135.0        # weight of one (10, 0, 1000, 5) call: 10 + 1000 x 0.1 + 5 x 5


def g_h_bash_verify():
    def build(fx):
        call(fx, 0, [("t1", "Bash", {"command": TEST_CMD})])
        fx.tool_result("t1", "T" * 2000, ts(11))
        call(fx, 1)
        call(fx, 2)
    rc, res = h_run(build)
    n, d = res["numerator"], res["details"]
    in_chars = len(json.dumps({"command": TEST_CMD}, ensure_ascii=False))
    exp_lo = in_chars / kp.CPT_HI * 5 + kp.burden(2000, 2, kp.CPT_HI)
    exp_hi = in_chars / kp.CPT_LO * 5 + kp.burden(2000, 2, kp.CPT_LO)
    sigs = [r["signature"] for r in d["cmd_signatures"]]
    ok = (rc == 0 and d["verification_tool_calls"] == 1 and d["result_chars"] == 2000
          and abs(n["weighted_lo"] - exp_lo) < 1e-6 and abs(n["weighted_hi"] - exp_hi) < 1e-6 and sigs == [TEST_CMD]
          and d["weighted_verifier_subagents"] == 0 and d["weighted_tool_calls"] == [n["weighted_lo"], n["weighted_hi"]])
    return ok, f"calls={d['verification_tool_calls']} result_chars={d['result_chars']} lo={n['weighted_lo']:.3f}/{exp_lo:.3f} sigs={sigs}"


def g_h_non_verify():
    def build(fx):
        call(fx, 0, [("a", "Bash", {"command": "ls -la"})])
        fx.tool_result("a", "x" * 500, ts(11))
        call(fx, 1, [("b", "Bash", {"command": "git diff -- tools/test_x.py"})])
        fx.tool_result("b", "y" * 500, ts(13))
        call(fx, 2, [("c", "Bash", {"command": "cd /w && timeout 60 python3 tools/test_y.py --drill --token " + CANARY})])
        fx.tool_result("c", "z" * 500, ts(15))
        # text that only mentions a test run: a heredoc body, inline -c code, an install, a version probe
        call(fx, 3, [("d", "Bash", {"command": "python3 - <<'PY'\nprint('verify the pytest run')\nPY"})])
        fx.tool_result("d", "d" * 400, ts(17))
        call(fx, 4, [("e", "Bash", {"command": 'python3 -c "import pytest; verify = 1"'})])
        fx.tool_result("e", "e" * 400, ts(19))
        call(fx, 5, [("f", "Bash", {"command": "pip install pytest && python3 -m pip show pytest"})])
        fx.tool_result("f", "f" * 400, ts(21))
        call(fx, 6, [("g", "Bash", {"command": "/x/venv/bin/python -m pytest -q tests/test_a.py 2>&1 | tail -5"})])
        fx.tool_result("g", "g" * 300, ts(23))
        # a real run AFTER a heredoc is still a run
        call(fx, 7, [("h", "Bash", {"command": "python3 - <<'PY'\nx = 1\nPY\npython3 tools/test_w.py"})])
        fx.tool_result("h", "h" * 200, ts(25))
        call(fx, 8)
    rc, res = h_run(build)
    d = res["details"]
    sigs = [r["signature"] for r in d["cmd_signatures"]]
    pos = ["pytest -q", "npm test", "npm run test", "node --test", "mix test", "go test ./...", "cargo test",
           "tsc -p . --noEmit", "x --selftest", "x --final", "x --drill", "gsd verify", "python3 tools/test_a.py"]
    neg = ["ls -la", "echo hello", "git status"]
    ok = (rc == 0 and d["verification_tool_calls"] == 3
          and sigs == ["python3 tools/test_y.py", "python -m pytest", "python3 tools/test_w.py"]
          and all(kp.VERIFY_CMD_RE.search(c) for c in pos) and not any(kp.VERIFY_CMD_RE.search(c) for c in neg)
          and kp.cmd_signature("FOO=1 CI=true npm test --silent") == "npm test"
          and kp.cmd_signature("curl -H x") == "curl")
    return ok, f"calls={d['verification_tool_calls']} sigs={sigs}"


def _sub_calls(sub, n_calls=3, with_test=False):
    sub.human("task", ts(5))
    for i in range(n_calls):
        uses = [("st", "Bash", {"command": "python3 tools/test_z.py"})] if with_test and i == 0 else []
        call(sub, i, uses)
        if uses:
            sub.tool_result("st", "R" * 5000, ts(10 + 2 * i + 1))


def g_h_verifier_subagent():
    def build(fx):
        _sub_calls(fx.subagent("a1", "gsd-verifier"))
    rc, res = h_run(build)
    n, d = res["numerator"], res["details"]
    ok = (rc == 0 and n["weighted_lo"] == 3 * W135 and n["weighted_hi"] == 3 * W135
          and d["verifier_agent_types"] == {"gsd-verifier": [1, 3, 3 * W135]} and d["other_agent_types"] == {}
          and d["weighted_verifier_subagents"] == 3 * W135 and d["weighted_tool_calls"] == [0.0, 0.0])

    def build2(fx):
        _sub_calls(fx.subagent("a1", "Explore"))
    rc2, res2 = h_run(build2)
    n2, d2 = res2["numerator"], res2["details"]
    ok2 = rc2 == 0 and n2["weighted_hi"] == 0 and d2["verifier_agent_types"] == {} and d2["other_agent_types"] == {"Explore": 1}
    return ok and ok2, f"verifier: lo={n['weighted_lo']} types={d['verifier_agent_types']}; Explore: hi={n2['weighted_hi']} other={d2['other_agent_types']}"


def g_h_no_double_count():
    def build(fx):
        _sub_calls(fx.subagent("a1", "gsd-verifier"), with_test=True)
    rc, res = h_run(build)
    n, d = res["numerator"], res["details"]
    once = rc == 0 and n["weighted_lo"] == n["weighted_hi"] == 3 * W135 and d["verification_tool_calls"] == 0

    def build2(fx):                                      # control: the same test call in a non-verifier subagent
        _sub_calls(fx.subagent("a1", "Explore"), with_test=True)
    rc2, res2 = h_run(build2)
    d2 = res2["details"]
    ctl = rc2 == 0 and d2["verification_tool_calls"] == 1 and res2["numerator"]["weighted_lo"] > 0
    return once and ctl, f"verifier file lo={n['weighted_lo']} (a)-calls={d['verification_tool_calls']}; control (a)-calls={d2['verification_tool_calls']}"


def g_h_meta_absent():
    def build(fx):
        _sub_calls(fx.subagent("a1"), with_test=True)                    # no meta.json
    rc, res = h_run(build)
    d = res["details"]
    ok = (rc == 0 and d["meta_absent"] == 1 and d["other_agent_types"] == {"unknown": 1} and d["verifier_agent_types"] == {}
          and d["verification_tool_calls"] == 1 and any("meta.json" in c for c in res["caveats"]))
    return ok, f"meta_absent={d['meta_absent']} other={d['other_agent_types']} (a)-calls={d['verification_tool_calls']}"


def g_h_sensitivity_not_verdict():
    def build(fx):
        for i in range(20):
            uses = [("t", "Bash", {"command": TEST_CMD})] if i == 0 else []
            call(fx, i, uses, usage=(10, 0, 300000, 50))
            if uses:
                fx.tool_result("t", "ok" * 25, ts(10 + 2 * i + 1))
    rc, res = h_run(build)
    n, d = res["numerator"], res["details"]
    sens = d["upper_sensitivity"]
    ok = (rc == 0 and res["materiality"] == "< 3 %" and res["share_interval"][1] < 0.03 and sens["share"] >= 0.03
          and "not used for the verdict" in sens["label"] and kp.h_numerator_interval(1.0, 2.0, 99.0) == (1.0, 2.0))
    return ok, f"materiality={res['materiality']} share={res['share_interval']} upper_sensitivity={sens['share']:.4f}"


def g_h_positive():
    def build(fx):
        for i in range(20):
            call(fx, i, [(f"t{i}", "Bash", {"command": TEST_CMD})], usage=(10, 0, 300000, 50))
            fx.tool_result(f"t{i}", "T" * 10000, ts(10 + 2 * i + 1))
    rc, res = h_run(build)

    def build2(fx):                                       # control: same shape, not a verification command
        for i in range(20):
            call(fx, i, [(f"t{i}", "Bash", {"command": "ls -la"})], usage=(10, 0, 300000, 50))
            fx.tool_result(f"t{i}", "T" * 10000, ts(10 + 2 * i + 1))
    rc2, res2 = h_run(build2)
    ok = (rc == 0 and res["materiality"] == ">= 3 %" and res["second_workload_required"] is True
          and rc2 == 0 and res2["materiality"] == "< 3 %" and res2["details"]["verification_tool_calls"] == 0)
    return ok, f"verification-heavy -> {res['materiality']} share={res['share_interval']}; ls control -> {res2['materiality']}"


def _git_exe():
    import shutil
    return os.environ.get("CPP_GIT_EXE") or shutil.which("git")


def g_h_ce_owner_read_real():
    git = _git_exe()
    if not git or not (REPO / kp.CE_LEDGER_REL).exists():
        return "SKIP", "git or the CE ledger is unavailable"
    v = kp.ce_owner_verdicts()
    head = subprocess.run([git, "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    led = json.loads(subprocess.run([git, "-C", str(REPO), "show", f"HEAD:{kp.CE_LEDGER_REL}"], capture_output=True,
                                    text=True).stdout.lstrip("\ufeff"))
    want = {p: ((led.get("state") or {}).get(p) or {}).get("terminal") for p in ("P", "G")}
    ok = v.get("commit") == head and len(v.get("commit", "")) == 40 and v.get("pillars") == want \
        and v.get("ref") == kp.CE_LEDGER_REL
    return ok, f"commit={str(v.get('commit'))[:8]} pillars={v.get('pillars')} independent_read={want}"


def _tmp_repo(ledger_text):
    git = _git_exe()
    d = scratch("gitrepo")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    (d / "ledger.json").write_text(ledger_text)
    for args in (["init", "-q"], ["add", "ledger.json"], ["commit", "-q", "-m", "x"]):
        subprocess.run([git, "-C", str(d)] + args, capture_output=True, env=env, check=True)
    return d


def g_h_ce_owner_unreadable():
    if not _git_exe():
        return "SKIP", "git is unavailable"
    missing = kp.ce_owner_verdicts(ref="vault/programs/none/ledger.json")
    not_repo = kp.ce_owner_verdicts(repo=scratch("norepo"))
    bad = kp.ce_owner_verdicts(repo=_tmp_repo("{not json"), ref="ledger.json")
    nostate = kp.ce_owner_verdicts(repo=_tmp_repo('{"state": {"P": {"terminal": null}}}'), ref="ledger.json")
    good = kp.ce_owner_verdicts(repo=_tmp_repo('{"state": {"P": {"terminal": "SHIPPED"}, "G": {"terminal": null}}}'),
                                ref="ledger.json")
    bad_all = all(v.get("status") == "UNMEASURABLE" and v.get("why") and "pillars" not in v
                  for v in (missing, not_repo, bad, nostate))
    ok = bad_all and good.get("pillars") == {"P": "SHIPPED", "G": None} and len(good.get("commit", "")) == 40
    return ok, f"missing={missing.get('status')} not_repo={not_repo.get('status')} bad_json={bad.get('status')} " \
               f"pillar_absent={nostate.get('status')} readable={good.get('pillars')}"


GATES_H = [
    ("V-KMEP-H-BASH-VERIFY", g_h_bash_verify),
    ("V-KMEP-H-NON-VERIFY", g_h_non_verify),
    ("V-KMEP-H-VERIFIER-SUBAGENT", g_h_verifier_subagent),
    ("V-KMEP-H-NO-DOUBLE-COUNT", g_h_no_double_count),
    ("V-KMEP-H-META-ABSENT", g_h_meta_absent),
    ("V-KMEP-H-SENSITIVITY-NOT-VERDICT", g_h_sensitivity_not_verdict),
    ("V-KMEP-H-POSITIVE", g_h_positive),
    ("V-KMEP-H-CE-OWNER-READ-REAL", g_h_ce_owner_read_real),
    ("V-KMEP-H-CE-OWNER-UNREADABLE", g_h_ce_owner_unreadable),
]


# =========================================================================== gates (plan 03-04, task 1: pillar I tracer)
I_FIX_POP = {"sessions_active": 1, "sessions_dead": 0, "calls": 6, "input": 21, "cache_write": 50000,
             "cache_read": 110000, "output": 260}


def i_tracer_fixture(root, project="-home-x-kme-i"):
    """Main file: 2 calls, first (5, 30000, 0, 100). agent-aa (Explore): 3 calls, first (3, 20000, 5000, 40).
    agent-bb (gsd-planner): 1 call (2, 0, 25000, 10)."""
    fx = Fx(root, project=project)
    fx.human("start", ts(0))
    fx.assistant("m1", "r1", (5, 30000, 0, 100), ts(1))
    fx.assistant("m2", "r2", (5, 0, 30000, 50), ts(2))
    aa = fx.subagent("aa", "Explore")
    aa.human("task", ts(3))
    aa.assistant("a1", "ra1", (3, 20000, 5000, 40), ts(4))
    aa.assistant("a2", "ra2", (3, 0, 25000, 30), ts(5))
    aa.assistant("a3", "ra3", (3, 0, 25000, 30), ts(6))
    bb = fx.subagent("bb", "gsd-planner")
    bb.human("task", ts(3))
    bb.assistant("b1", "rb1", (2, 0, 25000, 10), ts(4))
    return fx


def g_i_e2e():
    root = scratch("itracer")
    i_tracer_fixture(root)
    frozen = write_frozen(root / "frozen.json", **{"KME-L": I_FIX_POP})
    outd = root / "m"
    rc, out, err = run_main(["i", "--denominator", "KME-L", "--frozen-file", frozen, "--root",
                             str(pdir(root, "-home-x-kme-i")), "--out-dir", str(outd)])[0:3]
    files = sorted(outd.glob("I-KME-L-*.md")) if outd.is_dir() else []
    if rc != 0 or len(files) != 1:
        return False, f"rc={rc} files={[f.name for f in files]} err={err[-200:]}"
    front, res = parse_measurement(files[0].read_text(encoding="utf-8"))
    d, n = res["details"], res["numerator"]
    want = 40703 + 25003 * 0.1 * 2 + 2552
    types = d["by_agent_type"]
    ok = (front["pillar"] == "I" and front["population_match"] == "exact" and d["subagent_files"] == 2
          and d["first_ctx"]["n"] == 2 and d["first_ctx"]["min"] == 25002 and d["first_ctx"]["max"] == 25003
          and d["first_ctx"]["total"] == 50005 and d["main_first_ctx"]["n"] == 1
          and d["main_first_ctx"]["min"] == d["main_first_ctx"]["max"] == 30005
          and abs(n["weighted_lo"] - want) < 1e-6 and n["weighted_lo"] == n["weighted_hi"]
          and set(types) == {"Explore", "gsd-planner"}
          and abs(types["Explore"]["weighted"] - (40703 + 5000.6)) < 1e-6 and types["gsd-planner"]["weighted"] == 2552
          and types["Explore"]["first_ctx_total"] == 25003 and d["cold_files"] == 1)
    return ok, f"rc={rc} sub_files={d['subagent_files']} first_ctx={d['first_ctx']} main={d['main_first_ctx']} " \
               f"weighted={n['weighted_lo']}/{want} types={sorted(types)}"


GATES_I_TRACER = [("V-KMEP-I-E2E", g_i_e2e)]


# =========================================================================== gates (plan 03-04, task 2: expansion)
def i_run(build, extra=(), project="-home-x-kme-fixture", label="FX-I"):
    root = scratch("i")
    fx = Fx(root, project=project)
    fx.human("go", ts(0))
    build(fx)
    out_dir = scratch("out")
    rc, res, out, err = run_json(pil_args("i", pdir(root, project), out_dir, label, extra))
    return rc, res


def g_i_synthetic_first():
    def build(fx):
        call(fx, 0, usage=(10, 0, 1000, 5))
        sub = fx.subagent("s1", "Explore")
        sub.human("task", ts(5))
        sub.assistant("syn", "rsyn", (0, 0, 0, 0), ts(6), model="<synthetic>")
        sub.assistant("s2", "rs2", (4, 1000, 0, 5), ts(7))
        sub.assistant("s3", "rs3", (4, 0, 1000, 5), ts(8))
    rc, res = i_run(build)
    d, n = res["details"], res["numerator"]
    want = (4 + 2000 + 25) + 1004 * 0.1 * 1
    ok = (rc in (0, 3) and d["subagent_files"] == 1 and d["first_ctx"]["min"] == d["first_ctx"]["max"] == 1004
          and abs(n["weighted_lo"] - want) < 1e-9)
    return ok, f"first_ctx={d['first_ctx']} weighted={n['weighted_lo']}/{want}"


def g_i_no_subagents():
    def build(fx):
        call(fx, 0)
        call(fx, 1)
    rc, res = i_run(build)
    d, n = res["details"], res["numerator"]
    ok = (rc == 0 and d["subagent_files"] == 0 and n["weighted_lo"] == 0 == n["weighted_hi"]
          and res["observability"] == 1.0 and res["materiality"] == "< 3 %" and d["first_ctx"]["n"] == 0
          and d["main_first_ctx"]["n"] == 1)
    return ok, f"rc={rc} files={d['subagent_files']} numerator={n['weighted_lo']} obs={res['observability']} verdict={res['materiality']}"


def g_i_agent_type():
    def build(fx):
        call(fx, 0)
        for name, typ in (("a1", "Explore"), ("a2", "Explore"), ("a3", "Ex plore<>"), ("a4", None), ("a5", "gsd-planner")):
            sub = fx.subagent(name, typ)
            sub.human("task", ts(5))
            sub.assistant(f"{name}x", f"r{name}", (1, 100, 0, 1), ts(6))
        bad = fx.subagent("a6")
        (bad.path.parent / "agent-a6.meta.json").write_text("{not json")
        bad.human("task", ts(5))
        bad.assistant("a6x", "ra6", (1, 100, 0, 1), ts(6))
    rc, res = i_run(build)
    t = res["details"]["by_agent_type"]
    files = {k: v["files"] for k, v in t.items()}
    ok = files == {"Explore": 3, "gsd-planner": 1, "unknown": 2}
    return ok, f"by_agent_type files={files}"


def g_i_inline_sidechain_unobserved():
    def heavy(inline):
        root = scratch("inl")
        s1 = Fx(root)
        s1.human("go", ts(0))
        for i in range(5):
            s1.assistant(f"m{i}", f"r{i}", (10, 0, 1000000, 50), ts(10 + i))
        if inline:
            s1._w({"type": "assistant", "isSidechain": True, "timestamp": ts(20), "uuid": "u-sc", "requestId": "rsc",
                   "message": {"id": "sc", "model": "claude-opus-5-5", "role": "assistant", "content": [],
                               "usage": {"input_tokens": 1, "cache_creation_input_tokens": 100,
                                         "cache_read_input_tokens": 0, "output_tokens": 1}}})
        sub = s1.subagent("a1", "Explore")
        sub.human("t", ts(30))
        sub.assistant("x1", "rx1", (1, 100, 0, 1), ts(31))
        s2 = Fx(root, session="s2")
        s2.human("go", ts(0))
        for i in range(5):
            s2.assistant(f"n{i}", f"q{i}", (10, 0, 1000000, 50), ts(10 + i))
        out_dir = scratch("out")
        rc, res, _o, _e = run_json(pil_args("i", pdir(root), out_dir))
        return rc, res
    rc1, r1 = heavy(True)
    rc0, r0 = heavy(False)
    ok = (rc1 == 3 and r1["observability"] < 1.0 and r1["materiality"] == "UNMEASURED"
          and r1["details"]["sessions_with_inline_sidechain"] == 1
          and rc0 == 0 and r0["observability"] == 1.0 and r0["materiality"] == "< 3 %")
    # lower bound clearing 3 % is still a verdict although the signal is partial
    def clears():
        root = scratch("inl2")
        s1 = Fx(root)
        s1.human("go", ts(0))
        s1.assistant("m0", "r0", (10, 0, 1000, 5), ts(10))
        s1._w({"type": "assistant", "isSidechain": True, "timestamp": ts(11), "uuid": "u-sc", "requestId": "rsc",
               "message": {"id": "sc", "model": "claude-opus-5-5", "role": "assistant", "content": [],
                           "usage": {"input_tokens": 1, "cache_creation_input_tokens": 100,
                                     "cache_read_input_tokens": 0, "output_tokens": 1}}})
        sub = s1.subagent("a1", "Explore")
        sub.human("t", ts(30))
        sub.assistant("x1", "rx1", (1, 100000, 0, 1), ts(31))
        sub.assistant("x2", "rx2", (1, 0, 100000, 1), ts(32))
        rc, res, _o, _e = run_json(pil_args("i", pdir(root), scratch("out")))
        return rc, res
    rc2, r2 = clears()
    ok2 = rc2 == 0 and r2["observability"] < 1.0 and r2["materiality"] == ">= 3 %"
    return ok and ok2, f"inline: rc={rc1} obs={r1['observability']:.3f} verdict={r1['materiality']}; " \
                       f"clean: obs={r0['observability']} verdict={r0['materiality']}; clears: {r2['materiality']} obs={r2['observability']:.3f}"


def all_args(root, out_dir, project_root=None, extra=()):
    return ["all", "--denominator", "OTHER", "--label", "FX-ALL", "--select", "all", "--until", "none", "--expand",
            "--root", str(project_root or (root / "projects")), "--out-dir", str(out_dir)] + list(extra)


def g_all_one_scan():
    base = scratch("allscan")
    projects = rich_fixture(base / "fx")
    out_all = base / "all"
    before = kp.SCAN_COUNT
    rc, _o, err = run_main(all_args(base, out_all, projects))
    scans_all = kp.SCAN_COUNT - before
    files = {p.name[0]: p for p in out_all.glob("?-FX-ALL-*.md")} if out_all.is_dir() else {}
    got = {}
    for pillar, path in files.items():
        got[pillar] = parse_measurement(path.read_text(encoding="utf-8"))
    singles, before = {}, kp.SCAN_COUNT
    for pillar in "DEFGHI":
        od = base / f"one-{pillar}"
        run_main([pillar.lower(), "--denominator", "OTHER", "--label", "FX-ALL", "--select", "all", "--until", "none",
                  "--expand", "--root", str(projects), "--out-dir", str(od)])
        files1 = list(od.glob("*.md"))
        singles[pillar] = parse_measurement(files1[0].read_text(encoding="utf-8")) if files1 else None
    scans_single = kp.SCAN_COUNT - before
    if sorted(got) != list("DEFGHI") or any(v is None for v in singles.values()):
        return False, f"rc={rc} all files={sorted(got)} single files missing={[k for k, v in singles.items() if v is None]} err={err[-200:]}"
    pop_blocks = {json.dumps(r["population"], sort_keys=True) for _f, r in got.values()}
    cmds = {f["command"] for f, _r in got.values()}
    same = []
    for pillar in "DEFGHI":
        a, b = got[pillar][1], singles[pillar][1]
        same.append(all(a[k] == b[k] for k in ("numerator", "share_interval", "materiality", "observability",
                                                "population", "details", "evidence_role")))
    ok = (scans_all == 1 and scans_single == 6 and len(pop_blocks) == 1 and len(cmds) == 1
          and " all " in next(iter(cmds)) + " " and all(same))
    return ok, f"scans all={scans_all} six singles={scans_single} population blocks={len(pop_blocks)} commands={len(cmds)} equal={same}"


def six_calls(root, project="-home-x-kme-auto", session="s1"):
    fx = Fx(root, project=project, session=session)
    fx.human("go", ts(0))
    for i in range(1, 7):
        fx.assistant(f"m{i}", f"r{i}", (10, 100 * i, 1000 * i, 5), ts(i))
    return fx


def pop_at(k):
    return {"sessions_active": 1, "sessions_dead": 0, "calls": k, "input": 10 * k,
            "cache_write": 100 * k * (k + 1) // 2, "cache_read": 1000 * k * (k + 1) // 2, "output": 5 * k}


def run_pop(args):
    rc, out, err = run_main(["population"] + list(args))
    try:
        return rc, json.loads(out), err
    except ValueError:
        return rc, None, err + out


def auto_pop(root, frozen_pop, extra=(), project="-home-x-kme-auto"):
    frozen = write_frozen(root / f"frozen{len(list(root.glob('frozen*')))}.json", **{"KME-L": frozen_pop})
    return run_pop(["--denominator", "KME-L", "--frozen-file", frozen, "--until", "auto", "--root",
                    str(pdir(root, project))] + list(extra))


def g_until_auto_locate():
    root = scratch("auto")
    six_calls(root)
    rc, res, err = auto_pop(root, pop_at(4))
    ul = (res or {}).get("until_located") or {}
    ok = (rc == 0 and res is not None and res["population_match"] == "exact" and ul.get("method") == "bisect"
          and kp.parse_instant(res["until"]) == kp.parse_instant(ts(4)) and 1 < ul.get("scans", 99) <= kp.LOCATE_MAX_SCANS)
    # the measuring subcommands accept the same flag and measure at the located cutoff
    frozen = write_frozen(root / "f_i.json", **{"KME-L": pop_at(4)})
    out_dir = scratch("out")
    rc2, r2, _o, _e = run_json(["i", "--denominator", "KME-L", "--frozen-file", frozen, "--until", "auto", "--root",
                                str(pdir(root, "-home-x-kme-auto")), "--out-dir", str(out_dir)])
    ok2 = (rc2 == 0 and r2["population_match"] == "exact" and r2["population"]["calls"] == 4
           and r2["until_located"]["method"] == "bisect" and kp.parse_instant(r2["until"]) == kp.parse_instant(ts(4))
           and r2["terminal_evidence"] is True)
    return ok and ok2, f"population: rc={rc} match={(res or {}).get('population_match')} until={(res or {}).get('until')} " \
                       f"located={ul}; measuring: rc={rc2} calls={r2['population']['calls']} until={r2['until']}"


def g_until_auto_at_freeze():
    root = scratch("autof")
    six_calls(root)
    rc, res, err = auto_pop(root, pop_at(6))
    ul = (res or {}).get("until_located") or {}
    ok = (rc == 0 and res is not None and res["population_match"] == "exact" and ul.get("method") == "exact_at_freeze"
          and ul.get("scans") == 1 and res["until"] == kp.FREEZE_INSTANT)
    rc2, res2, err2 = auto_pop(root, pop_at(4), ["--freeze-instant", ts(4.5)])
    ul2 = (res2 or {}).get("until_located") or {}
    ok2 = (rc2 == 0 and res2 is not None and ul2.get("method") == "exact_at_freeze" and ul2.get("scans") == 1
           and kp.parse_instant(res2["until"]) == kp.parse_instant(ts(4.5)))
    return ok and ok2, f"freeze default: rc={rc} method={ul.get('method')} scans={ul.get('scans')}; " \
                       f"--freeze-instant: rc={rc2} method={ul2.get('method')} until={(res2 or {}).get('until')}"


def g_until_auto_unreachable():
    root = scratch("autou")
    six_calls(root)
    off = dict(pop_at(4), cache_read=pop_at(4)["cache_read"] + 1)
    rc, res, err = auto_pop(root, off)
    ul = (res or {}).get("until_located") or {}
    ok_a = (rc == 3 and res is not None and res["population_match"] == "drifted" and ul.get("method") == "not_found")
    above = dict(pop_at(6), calls=9)
    rc2, res2, err2 = auto_pop(root, above)
    ul2 = (res2 or {}).get("until_located") or {}
    ok_b = (rc2 == 3 and res2 is not None and ul2.get("method") == "not_found" and ul2.get("scans") == 1)
    frozen = write_frozen(root / "f_m.json", **{"KME-L": off})
    out_dir = scratch("out")
    rc3, r3, _o, _e = run_json(["i", "--denominator", "KME-L", "--frozen-file", frozen, "--until", "auto", "--root",
                                str(pdir(root, "-home-x-kme-auto")), "--out-dir", str(out_dir)])
    ok_c = (rc3 == 3 and r3["materiality"] == "UNMEASURED" and r3["materiality_reason"] == "cutoff_not_found"
            and r3["terminal_evidence"] is False and r3["share_interval"] is None
            and r3["until_located"]["method"] == "not_found" and len(list(out_dir.glob("I-KME-L-*.md"))) == 1)
    # the locator itself (the CLI also re-verifies the located cutoff after its final scan, which would mask a
    # locator that accepted a calls-only match): drive locate_cutoff with a probe whose calls reach the frozen
    # figure while one field never does
    base = datetime.datetime(2026, 10, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)
    inst = [base + datetime.timedelta(seconds=i) for i in range(10)]
    freeze = inst[-1] + datetime.timedelta(seconds=1)

    def measured(t):
        n = sum(1 for x in inst if x <= t)
        return {"sessions_active": 1, "sessions_dead": 0, "calls": n, "input": n, "cache_write": 0, "cache_read": n,
                "output": 0}
    off4 = dict(measured(inst[3]), cache_read=measured(inst[3])["cache_read"] + 1)
    lo_off = kp.locate_cutoff(lambda t, w: (measured(t), list(inst) if w else None), off4, freeze)
    lo_ok = kp.locate_cutoff(lambda t, w: (measured(t), list(inst) if w else None), measured(inst[3]), freeze)
    ok_d = lo_off["method"] == "not_found" and lo_off["until"] is None and lo_ok["method"] == "bisect" \
        and lo_ok["until"] == inst[3]
    return ok_a and ok_b and ok_c and ok_d, \
        f"calls reachable, one field off: rc={rc} {ul.get('method')}; above corpus: rc={rc2} " \
        f"{ul2.get('method')} scans={ul2.get('scans')}; measuring: rc={rc3} " \
        f"{r3['materiality']}/{r3['materiality_reason']}; locator direct: off-by-one {lo_off['method']}, control {lo_ok['method']}"


def g_until_auto_before_next_call():
    root = scratch("autob")
    fx = Fx(root, project="-home-x-kme-auto")
    fx.human("go", ts(0))
    for i in range(1, 7):
        fx.assistant(f"m{i}", f"r{i}", (10, 100 * i, 1000 * i, 5), ts(i))
        if i == 4:
            Fx(root, project="-home-x-kme-auto", session="s2").human("late prompt", ts(4.5))
    frozen_pop = dict(pop_at(4), sessions_dead=1)
    rc, res, err = auto_pop(root, frozen_pop)
    ul = (res or {}).get("until_located") or {}
    until = kp.parse_instant(res["until"]) if res else None
    ok = (rc == 0 and res is not None and res["population_match"] == "exact" and ul.get("method") == "bisect"
          and until is not None and kp.parse_instant(ts(4.5)) <= until < kp.parse_instant(ts(5)))
    return ok, f"rc={rc} match={(res or {}).get('population_match')} until={(res or {}).get('until')} located={ul}"


def g_until_auto_other_refused():
    root = scratch("autoo")
    six_calls(root)
    pd = pdir(root, "-home-x-kme-auto")
    out_dir = scratch("out")
    rows = {}
    rows["OTHER+auto"] = run_main(["i", "--denominator", "OTHER", "--label", "FX-A", "--select", "all", "--until", "auto",
                                   "--root", str(pd), "--out-dir", str(out_dir)])[0]
    rows["population OTHER+auto"] = run_main(["population", "--denominator", "OTHER", "--label", "FX-A", "--select", "all",
                                              "--until", "auto", "--root", str(pd)])[0]
    rows["D-W7+auto"] = run_main(["d", "--denominator", "CPP-D-W7", "--until", "auto", "--root", str(pd),
                                  "--out-dir", str(out_dir)])[0]
    frozen = write_frozen(root / "f.json", **{"KME-L": pop_at(6)})
    rows["freeze-instant without auto"] = run_main(["i", "--denominator", "KME-L", "--frozen-file", frozen,
                                                    "--freeze-instant", ts(4), "--root", str(pd), "--out-dir", str(out_dir)])[0]
    rows["since with auto"] = run_main(["i", "--denominator", "KME-L", "--frozen-file", frozen, "--until", "auto",
                                        "--since", ts(1), "--root", str(pd), "--out-dir", str(out_dir)])[0]
    rows["control: KME-L auto"] = run_main(["i", "--denominator", "KME-L", "--frozen-file", frozen, "--until", "auto",
                                            "--root", str(pd), "--out-dir", str(out_dir)])[0]
    wrote = len(list(out_dir.glob("*.md")))
    ok = all(v == 2 for k, v in rows.items() if not k.startswith("control")) and rows["control: KME-L auto"] == 0 and wrote == 1
    return ok, f"rcs={rows} files written={wrote}"


def g_until_auto_budget():
    import bisect as _bisect
    base = datetime.datetime(2026, 10, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)
    inst = [base + datetime.timedelta(seconds=7 * i) for i in range(5000)]
    freeze = inst[-1] + datetime.timedelta(seconds=1)
    probes = []

    def measured(t):
        n = _bisect.bisect_right(inst, t)
        return {"sessions_active": 1, "sessions_dead": 0, "calls": n, "input": n, "cache_write": 0, "cache_read": 3 * n,
                "output": 0}

    def probe(t, want):
        probes.append(t)
        return measured(t), (list(inst) if want else None)
    never = dict(measured(freeze), calls=2500, cache_read=7)             # no instant reproduces cache_read 7
    r1 = kp.locate_cutoff(probe, never, freeze, first=(measured(freeze), list(inst)))
    n1 = len(probes) + 1
    probes.clear()
    r2 = kp.locate_cutoff(probe, never, freeze, first=(measured(freeze), list(inst)), max_scans=5)
    n2 = len(probes) + 1
    probes.clear()
    want = measured(inst[3776])
    r3 = kp.locate_cutoff(probe, want, freeze, first=(measured(freeze), list(inst)))
    n3 = len(probes) + 1
    ok = (r1["method"] == "not_found" and n1 <= kp.LOCATE_MAX_SCANS == 24 and r1["scans"] == n1
          and r2["method"] == "not_found" and n2 <= 5 and "budget" in r2["why"]
          and r3["method"] == "bisect" and r3["until"] == inst[3776] and r3["scans"] <= kp.LOCATE_MAX_SCANS)
    return ok, f"never matches: {r1['method']} scans={r1['scans']}; max_scans=5: {r2['method']} scans={r2['scans']} " \
               f"({r2['why'][:40]}); reachable: {r3['method']} scans={r3['scans']}"


def g_window_since():
    root = scratch("since")
    fx = Fx(root)
    fx.human("go", ts(0))
    for i in range(1, 5):
        fx.assistant(f"m{i}", f"r{i}", (10, 0, 100, 5), ts(i))
    Fx(root, session="s2").human("early", ts(1)).assistant("e1", "re1", (1, 1, 1, 1), ts(1.5))
    out_dir = scratch("out")
    rc, res, _o, _e = run_json(pil_args("i", pdir(root), out_dir, extra=["--since", ts(2.5)]))
    p = res["population"]
    lines = scratch("sincekeep") / "f.jsonl"
    f = Fx(root, path=lines)
    f.meta()
    f.human("a", ts(8))
    f.meta()
    rows = [json.loads(x) for x in lines.read_text().splitlines()]
    k_early = kp.make_keep(kp.parse_instant(ts(5)), None)
    k_late = kp.make_keep(kp.parse_instant(ts(9)), None)
    got_early = [k_early(str(lines), o) for o in rows]
    got_late = [k_late(str(lines), o) for o in rows]
    ok = (rc == 0 and p["calls"] == 2 and p["sessions_active"] == 1 and p["sessions_dead"] == 0
          and got_early == [True, True, True] and got_late == [False, False, False]
          and res.get("since") == kp.fmt_instant(kp.parse_instant(ts(2.5))))
    return ok, f"calls={p['calls']} active={p['sessions_active']} dead={p['sessions_dead']} keep early={got_early} late={got_late}"


# ---- D-W7 (referenced denominator from the CE ledger)
def ce_ledger_file(path, calls, window="2026-10-03T09:00:00Z 2026-10-03T12:00:00Z", weighted_delta=0, drop=False, **over):
    fields = {"input": 40, "cache_write": 1000, "cache_read": 400000, "output": 200}
    fields.update(over)
    w = round(kp.weighted(fields)) + weighted_delta
    entry = dict(fields, source=f"python tools/usage_index.py window {window}", calls=calls, subagent_calls=1,
                 weighted_input_equivalent=w)
    denoms = {} if drop else {"D-W7": entry}
    Path(path).write_text(json.dumps({"frozen": {"denominators": denoms}}))
    return str(path)


def ce_ledger_exact(path, project_dir, **over):
    """A CE ledger whose D-W7 entry equals the population measured over `project_dir` in the ledger's own window
    (a reproduced referenced population: coverage exactly 1 and all five usage fields equal)."""
    rc, out, err = run_main(["population", "--denominator", "OTHER", "--label", "PROBE", "--select", "all",
                             "--since", "2026-10-03T09:00:00Z", "--until", "2026-10-03T12:00:00Z",
                             "--root", str(project_dir)])
    m = json.loads(out)["population"]
    fields = {k: m[k] for k in ("input", "cache_write", "cache_read", "output")}
    fields.update(over)
    return ce_ledger_file(path, m["calls"], **fields)


def dw7_args(pillar, root, ledger, out_dir, extra=()):
    return [pillar, "--denominator", "CPP-D-W7", "--frozen-ce-ledger", ledger, "--root", str(pdir(root)),
            "--out-dir", str(out_dir)] + list(extra)


def g_dw7_spec():
    spec = kp.frozen_specs()["CPP-D-W7"]
    f = spec["fields"]
    led = json.loads((REPO / kp.CE_LEDGER_REL).read_text(encoding="utf-8"))["frozen"]["denominators"]["D-W7"]
    ok = (spec["fields"]["calls"] == 75969 == led["calls"] and spec["weighted"] == 3325101725 == round(kp.weighted(f))
          and spec["since"] == "2026-09-26T00:00:00Z" and spec["until"] == "2026-10-03T00:00:00Z"
          and spec["select"] == "all" and spec["denominator_kind"] == "referenced" and spec["host"] == "local"
          and f["cache_read"] == 21968212607)
    root = scratch("dw7spec")
    tracer_fixture(root)
    bad = ce_ledger_file(root / "bad.json", 4, weighted_delta=5)
    miss = ce_ledger_file(root / "miss.json", 4, drop=True)
    out_dir = scratch("out")
    rc_bad = run_main(dw7_args("d", root, bad, out_dir))[0]
    rc_miss = run_main(dw7_args("d", root, miss, out_dir))[0]
    spec_bad = kp.frozen_specs(REPO / kp.DENOMS_REL, bad).get("CPP-D-W7", {})
    okf = (rc_bad == 2 and rc_miss == 2 and "error" in spec_bad and not list(out_dir.glob("*.md")))
    return ok and okf, f"calls={f['calls']} weighted={spec['weighted']} window={spec['since']}..{spec['until']} " \
                       f"refusals: weighted mismatch rc={rc_bad}, absent rc={rc_miss}"


def g_dw7_coverage():
    root = scratch("dw7cov")
    tracer_fixture(root)                                   # 4 calls, 900 hook chars
    out = {}

    def run(name, led):
        rc, res, _o, _e = run_json(dw7_args("d", root, led, scratch("out")))
        out[name] = (rc, res)
        return rc, res
    rc_a, a = run("partial", ce_ledger_file(root / "partial.json", 8))                 # measured 4 of 8 calls
    rc_b, b = run("equal", ce_ledger_exact(root / "equal.json", pdir(root)))           # calls and all five fields equal
    rc_c, c = run("above", ce_ledger_file(root / "above.json", 3))                     # measured 4 of 3 calls: > 1
    rc_e, e = run("same-calls-other-usage", ce_ledger_file(root / "other.json", 4))    # coverage 1, usage fields differ
    rc_d, d = run("partial-clears", ce_ledger_file(root / "pc.json", 8, cache_read=3000, cache_write=100))
    ok = (rc_a == 3 and a["population_match"] == "referenced" and a["coverage"] == 0.5 and a["observability"] == 0.5
          and a["materiality"] == "UNMEASURED" and a["share_interval"][0] < 0.03 and a["terminal_evidence"] is False
          and rc_b == 0 and b["coverage"] == 1.0 and b["observability"] == 1.0 and b["materiality"] != "UNMEASURED"
          and b["terminal_evidence"] is True and not b["population_deltas"]
          and all(abs(x - y) < 1e-6 for x, y in zip(b["share_interval"], b["share_measured_population"]))
          and rc_c == 3 and c["coverage"] > 1 and c["materiality"] == "UNMEASURED" and c["share_interval"] is None
          and c["terminal_evidence"] is False and c["materiality_reason"].startswith("referenced_population_not_reproduced")
          and c["share_measured_population"] is not None
          and rc_e == 3 and e["coverage"] == 1.0 and e["materiality"] == "UNMEASURED" and e["share_interval"] is None
          and e["terminal_evidence"] is False and "cache_read" in e["population_deltas"] and "calls" not in e["population_deltas"]
          and rc_d == 0 and d["observability"] == 0.5 and d["materiality"] == ">= 3 %" and d["terminal_evidence"] is False)
    return ok, f"partial: rc={rc_a} cov={a['coverage']} obs={a['observability']} verdict={a['materiality']} lo={a['share_interval'][0]:.4f}; " \
               f"equal: {b['materiality']} terminal={b['terminal_evidence']}; above: cov={c['coverage']:.2f} {c['materiality']} " \
               f"terminal={c['terminal_evidence']}; same calls other usage: {e['materiality']} terminal={e['terminal_evidence']}; " \
               f"partial but lo clears: {d['materiality']}"


def g_dw7_window_fixed():
    root = scratch("dw7win")
    tracer_fixture(root)
    led = ce_ledger_file(root / "led.json", 2, window="2026-10-03T10:00:03Z 2026-10-03T10:00:08Z")
    out_dir = scratch("out")
    rc, res, _o, _e = run_json(dw7_args("d", root, led, out_dir))
    rcs = {k: run_main(dw7_args("d", root, led, out_dir, [k, ts(1)]))[0] for k in ("--since", "--until")}
    rcs["--freeze-instant"] = run_main(dw7_args("d", root, led, out_dir, ["--freeze-instant", ts(1)]))[0]
    rcs["--select"] = run_main(dw7_args("d", root, led, out_dir, ["--select", "kme"]))[0]
    ok = (rc in (0, 3) and res["population"]["calls"] == 2 and res["until"] == "2026-10-03T10:00:08Z"
          and res["since"] == "2026-10-03T10:00:03Z" and all(v == 2 for v in rcs.values())
          and len(list(out_dir.glob("D-CPP-D-W7-*.md"))) == 1)
    return ok, f"calls={res['population']['calls']} window={res['since']}..{res['until']} refusals={rcs}"


def g_dw7_roles():
    root = scratch("dw7role")
    tracer_fixture(root)
    full = ce_ledger_exact(root / "full.json", pdir(root))
    part = ce_ledger_file(root / "part.json", 8)

    def get(pillar, led, extra=()):
        rc, res, _o, _e = run_json(dw7_args(pillar, root, led, scratch("out"), extra))
        return rc, None if res is None else (res["evidence_role"], res["terminal_evidence"], res["second_workload_valid"])
    rows = [
        ("d full", get("d", full)[1], ("primary", True, None)),
        ("d partial", get("d", part)[1], ("primary", False, None)),
        ("e second_workload full", get("e", full, ["--role", "second_workload"])[1], ("second_workload", False, True)),
        ("e second_workload partial", get("e", part, ["--role", "second_workload"])[1], ("second_workload", False, False)),
        ("e auto", get("e", full)[1], ("smoke", False, None)),
    ]
    rc_d_sw = run_main(dw7_args("d", root, full, scratch("out"), ["--role", "second_workload"]))[0]
    bad = [r[0] for r in rows if r[1] != r[2]]
    return not bad and rc_d_sw == 2, f"{len(rows)} rows wrong={bad} got={[(r[0], r[1]) for r in rows if r[1] != r[2]]} d+second_workload rc={rc_d_sw}"


def multi_project_root():
    root = scratch("mp")
    a = Fx(root, project="-home-x-kme-a", session="sa1")
    a.human("go", ts(0))
    a.assistant("a1", "ra1", (10, 100, 0, 5), ts(1))
    a.assistant("a2", "ra2", (10, 0, 100, 5), ts(2))
    Fx(root, project="-home-x-kme-a", session="sa2").human("only a prompt", ts(3))
    m = Fx(root, project="-home-x-misc", session="sm1")                 # a KME session whose dir name says nothing
    m.human("go", ts(0))
    m.assistant("m1", "rm1", (7, 0, 50, 3), ts(1), tool_uses=[("t1", "Bash", {"command": "ls kme/arena KMEIP"}),
                                                                ("t2", "Bash", {"command": "cat kme/KMEIP.md"})])
    p = Fx(root, project="-home-x-plain", session="sp1")
    p.human("go", ts(0))
    p.assistant("p1", "rp1", (3, 50, 0, 7), ts(1), tool_uses=[("t3", "Bash", {"command": "ls"})])
    return root


MP_POP = {"sessions_active": 2, "sessions_dead": 1, "calls": 3, "input": 27, "cache_write": 100, "cache_read": 150,
          "output": 13}


def g_project_filter():
    root = scratch("pf")
    for proj in ("-home-x-kme-a", "-home-x-misc", "-home-x-plain"):
        Fx(root, project=proj).human("go", ts(0)).assistant("m1", "r1", (1, 1, 1, 1), ts(1))

    def dirs(extra, roots=None):
        rc, res, _o, _e = run_json(["i", "--denominator", "OTHER", "--label", "FX-A", "--select", "all", "--until", "none",
                                    "--root", str(roots or (root / "projects")), "--out-dir", str(scratch("out"))] + list(extra))
        return rc, None if res is None else res["corpus"]["project_dirs"]
    rows = {
        "expand, no filter": dirs(["--expand"])[1],
        "expand, filter kme": dirs(["--expand", "--project-filter", "kme"])[1],
        "expand, filter none-match": dirs(["--expand", "--project-filter", "zzz"])[1],
        "plain root, matching basename": dirs(["--project-filter", "kme-a"], pdir(root, "-home-x-kme-a"))[1],
        "plain root, other basename": dirs(["--project-filter", "kme-a"], pdir(root, "-home-x-plain"))[1],
    }
    rc_bad = run_main(["i", "--denominator", "OTHER", "--label", "FX-A", "--select", "all", "--until", "none", "--root",
                       str(root / "projects"), "--expand", "--project-filter", "(", "--out-dir", str(scratch("out"))])[0]
    want = {"expand, no filter": 3, "expand, filter kme": 1, "expand, filter none-match": 0,
            "plain root, matching basename": 1, "plain root, other basename": 0}
    return rows == want and rc_bad == 2, f"project dirs {rows} invalid regex rc={rc_bad}"


def g_population_subcommand():
    root = multi_project_root()
    frozen = write_frozen(root / "frozen.json", **{"KME-L": MP_POP})
    measure_dir = REPO / kp.MEASUREMENTS_REL
    before = sorted(p.name for p in measure_dir.iterdir()) if measure_dir.is_dir() else []
    rc, res, err = run_pop(["--denominator", "KME-L", "--frozen-file", frozen, "--expand", "--root", str(root / "projects")])
    after = sorted(p.name for p in measure_dir.iterdir()) if measure_dir.is_dir() else []
    rows = [(r["project"], r["sessions_active"], r["sessions_dead"], r["calls"], r["cache_read"])
            for r in (res or {}).get("per_project", [])]
    want_rows = [("-home-x-kme-a", 1, 1, 2, 100), ("-home-x-misc", 1, 0, 1, 50)]
    rc2, res2, _e2 = run_pop(["--denominator", "KME-L", "--frozen-file", frozen, "--expand", "--project-filter", "kme-a",
                              "--root", str(root / "projects")])
    ok = (rc == 0 and res is not None and res["population_match"] == "exact" and rows == want_rows
          and res["denominator"] == "KME-L" and before == after and "frozen" in res and "population" in res
          and rc2 == 3 and res2 is not None and res2["population_match"] == "drifted"
          and [r["project"] for r in res2["per_project"]] == ["-home-x-kme-a"])
    return ok, f"rc={rc} match={(res or {}).get('population_match')} rows={rows} filtered rc={rc2} " \
               f"wrote_nothing={before == after}"


def g_kmeg_auto_real():
    roots = ENV_ROOTS + [MAIN_ROOT]
    if not all(os.path.isdir(r) for r in roots):
        return "SKIP", "corpus roots absent"
    args = ["--denominator", "KME-G", "--until", "auto", "--expand"]
    for r in roots:
        args += ["--root", r]
    before = kp.SCAN_COUNT
    rc, res, err = run_pop(args)
    scans = kp.SCAN_COUNT - before
    ul = (res or {}).get("until_located") or {}
    ok = (rc == 0 and res is not None and res["population_match"] == "exact" and ul.get("method") == "exact_at_freeze"
          and ul.get("scans") == 1 and scans == 1)
    return ok, f"rc={rc} match={(res or {}).get('population_match')} method={ul.get('method')} scans={ul.get('scans')}/{scans}"


GATES_EXPANSION_2 = [
    ("V-KMEP-I-SYNTHETIC-FIRST", g_i_synthetic_first),
    ("V-KMEP-I-NO-SUBAGENTS", g_i_no_subagents),
    ("V-KMEP-I-AGENT-TYPE", g_i_agent_type),
    ("V-KMEP-I-INLINE-SIDECHAIN-UNOBSERVED", g_i_inline_sidechain_unobserved),
    ("V-KMEP-ALL-ONE-SCAN", g_all_one_scan),
    ("V-KMEP-UNTIL-AUTO-LOCATE", g_until_auto_locate),
    ("V-KMEP-UNTIL-AUTO-AT-FREEZE", g_until_auto_at_freeze),
    ("V-KMEP-UNTIL-AUTO-UNREACHABLE", g_until_auto_unreachable),
    ("V-KMEP-UNTIL-AUTO-BEFORE-NEXT-CALL", g_until_auto_before_next_call),
    ("V-KMEP-UNTIL-AUTO-OTHER-REFUSED", g_until_auto_other_refused),
    ("V-KMEP-UNTIL-AUTO-BUDGET", g_until_auto_budget),
    ("V-KMEP-WINDOW-SINCE", g_window_since),
    ("V-KMEP-DW7-SPEC", g_dw7_spec),
    ("V-KMEP-DW7-COVERAGE", g_dw7_coverage),
    ("V-KMEP-DW7-WINDOW-FIXED", g_dw7_window_fixed),
    ("V-KMEP-DW7-ROLES", g_dw7_roles),
    ("V-KMEP-PROJECT-FILTER", g_project_filter),
    ("V-KMEP-POPULATION-SUBCOMMAND", g_population_subcommand),
]
GATES_REAL_2 = [("V-KMEP-KMEG-AUTO-REAL", g_kmeg_auto_real)]


# =========================================================================== plan 03-05: R3 through the done-gate
def _icp():
    """The program-owned done-gate wrapper (imported lazily: it rebinds the CE verifier's module globals)."""
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import test_incremental_cognition_program as icp
    return icp


@contextlib.contextmanager
def icp_sources(icp, **paths):
    """The wrapper's committed-frozen-source table pointed at scratch files for the duration (R3 reads it at call time)."""
    saved = dict(icp.FROZEN_SOURCE_DEFAULTS)
    icp.FROZEN_SOURCE_DEFAULTS.update({k: str(v) for k, v in paths.items()})
    try:
        yield
    finally:
        icp.FROZEN_SOURCE_DEFAULTS.clear()
        icp.FROZEN_SOURCE_DEFAULTS.update(saved)


def r3_led(pillar, *refs):
    return {"state": {pillar: {"evidence": [{"kind": "measurement", "ref": str(r), "sha256": "0" * 64}
                                            for r in refs]}}}


def g_r3_e_pair():
    """The instrument's own pillar-E files (primary KME-L, second workload CPP-D-W7, smoke KME-G) through R3."""
    icp = _icp()
    root = scratch("r3e")
    fx = Fx(root, project="-home-x-kme-e")
    fx.human("start", ts(0))
    rd(fx, 0, "r1", "/w/big.py", E_BODY)
    call(fx, 1)
    rd(fx, 2, "r2", "/w/big.py", E_BODY)
    call(fx, 3)
    call(fx, 4)
    pop = {"sessions_active": 1, "sessions_dead": 0, "calls": 5, "input": 50, "cache_write": 0, "cache_read": 5000,
           "output": 25}
    frozen = write_frozen(root / "frozen.json", **{"KME-L": pop, "KME-G": pop})
    proj = root / "projects" / "-home-x-kme-e"
    outd = root / "m"
    rc1, o1, e1 = run_main(["e", "--denominator", "KME-L", "--frozen-file", frozen, "--root", str(proj),
                            "--out-dir", str(outd)])
    ledger = ce_ledger_exact(root / "ce.json", proj)
    rc2, o2, e2 = run_main(["e", "--denominator", "CPP-D-W7", "--role", "second_workload", "--frozen-ce-ledger",
                            ledger, "--root", str(proj), "--out-dir", str(outd)])
    rc3, o3, e3 = run_main(["e", "--denominator", "KME-G", "--frozen-file", frozen, "--root", str(proj),
                            "--out-dir", str(outd)])
    prim, second, smoke = (next(iter(outd.glob(f"E-{d}-*.md")), None) for d in ("KME-L", "CPP-D-W7", "KME-G"))
    if rc1 != 0 or rc2 != 0 or rc3 != 0 or not (prim and second and smoke):
        return False, f"rc={rc1},{rc2},{rc3} files={sorted(f.name for f in outd.glob('*.md'))} err={(e1 + e2 + e3)[-200:]}"
    fp, fs, fk = (parse_measurement(f.read_text(encoding="utf-8"))[0] for f in (prim, second, smoke))
    shaped = (fp["evidence_role"] == "primary" and fp["terminal_evidence"] is True
              and fs["evidence_role"] == "second_workload" and fs["second_workload_valid"] is True
              and fs["terminal_evidence"] is False and fk["evidence_role"] == "smoke")
    res = icp.ce.Resolver()

    def fails(pillar, *refs):
        with icp_sources(icp, frozen_file=frozen, ce_ledger=ledger):
            return icp.check_measurement_scope(r3_led(pillar, *refs), res, only=[pillar])
    pair, alone, smk, wrong = fails("E", prim, second), fails("E", second), fails("E", smoke), fails("D", prim)
    ok = (shaped and pair == [] and len(alone) == 1 and alone[0].startswith("R3 E:")
          and len(smk) == 1 and smk[0].startswith("R3 E:") and len(wrong) == 1 and wrong[0].startswith("R3 D:"))
    return ok, f"front shaped={shaped} pair={pair} second_alone={alone} smoke={smk} E-file-cited-by-D={wrong}"


GATES_PLAN5_TRACER = [("V-KMEP-R3-E-PAIR", g_r3_e_pair)]


BUNDLE_REL = "vault/programs/incremental-cognition/owner-bundle.md"


def bundle_commands(text):
    """(item tag or None, argv tokens after the script token) for every indented kme_pillars command line."""
    import shlex
    tag, rows = None, []
    for ln in text.split("\n"):
        m = re.match(r"^- \*\*\[([A-Z])\]\*\*", ln)
        if m:
            tag = m.group(1)
        elif re.match(r"^(## |# )", ln):
            tag = None
        if not re.match(r"^ {4,}\S", ln) or "wiki/tools/kme_pillars.py" not in ln:
            continue
        toks = [t.strip("\"'") for t in shlex.split(ln.strip(), posix=False)]
        i = next(k for k, t in enumerate(toks) if t.endswith("wiki/tools/kme_pillars.py"))
        rows.append((tag, ln.strip(), toks[i + 1:]))
    return rows


def g_bundle_argv_parses():
    text = (REPO / BUNDLE_REL).read_text(encoding="utf-8")
    rows = bundle_commands(text)
    ap = kp.build_parser()
    parsed, bad = [], []
    for tag, line, argv in rows:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                parsed.append((tag, ap.parse_args(argv), line))
        except SystemExit:
            bad.append(line[:90])
    blocks = {}
    for m in re.finditer(r"^- \*\*\[([A-Z])\]\*\*.*?(?=^- \*\*\[|\Z)", text, re.M | re.S):
        blocks.setdefault(m.group(1), "")
        blocks[m.group(1)] += m.group(0)
    missing, wrong = [], []
    for P in "DEFGHI":
        blk = blocks.get(P)
        if not blk or f"**[{P}]**" not in blk:
            missing.append(P)
            continue
        own = [a for t, a, _l in parsed if t == P and a.cmd == P.lower() and a.denominator == "KME-L"
               and a.until == "auto"]
        if not own or f"{P}-KME-L-" not in blk:
            wrong.append(P)
    d_w7 = [a for t, a, _l in parsed if t == "D" and a.cmd == "d" and a.denominator == "CPP-D-W7"]
    e_w7 = [a for t, a, _l in parsed if t == "E" and a.cmd == "e" and a.denominator == "CPP-D-W7"
            and a.role == "second_workload"]
    pops = [a for _t, a, _l in parsed if a.cmd == "population"]
    pop_ok = bool(pops) and pops[0].expand is True and pops[0].project_filter is None and pops[0].denominator == "KME-L"
    ok = (len(parsed) >= 7 and not bad and not missing and not wrong and bool(d_w7) and bool(e_w7) and pop_ok)
    return ok, (f"{len(parsed)} commands parsed (>= 7), unparsable={bad} missing_items={missing} "
                f"items_without_own_KME-L_command_or_file_pattern={wrong} D-W7(d)={bool(d_w7)} "
                f"E-second_workload={bool(e_w7)} first_population_unfiltered_expand={pop_ok}")


GATES_PLAN5_BUNDLE = [("V-KMEP-BUNDLE-ARGV-PARSES", g_bundle_argv_parses)]


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


# --------------------------------------------------------------------------- review-fix gates (03-REVIEW WR-01..WR-07, IN-01)
def g_out_dir_inside_root():
    """WR-01: an --out-dir that resolves inside any --root is refused with rc 2 and nothing is written."""
    root = scratch("wr01")
    tracer_fixture(root)
    pd = pdir(root)
    before = tree_state(root / "projects")
    inside = pd / "out"
    rc_in, _o, err_in = run_main(other_args(pd, inside))
    link = scratch("wr01-link") / "lnk"
    try:
        link.symlink_to(pd, target_is_directory=True)
    except OSError as exc:  # Windows without the symlink privilege: a junction resolves the same way
        if os.name != "nt" or getattr(exc, "winerror", None) != 1314:
            raise
        import _winapi
        _winapi.CreateJunction(str(pd), str(link))
    rc_ln, _o2, err_ln = run_main(other_args(pd, link / "viasym"))
    rc_ex, _o3, err_ex = run_main(other_args(root / "projects", root / "projects" / "deeper" / "out") + ["--expand"])
    rc_eq, _o4, _e4 = run_main(other_args(pd, pd))
    after = tree_state(root / "projects")
    out_ok = scratch("wr01-ok")
    rc_ok, _o5, _e5 = run_main(other_args(pd, out_ok))
    wrote = len(list(out_ok.glob("*.md")))
    refused = rc_in == rc_ln == rc_ex == rc_eq == 2
    return refused and before == after and not inside.exists() and "inside --root" in err_in and rc_ok in (0, 3) \
        and wrote == 1, f"inside={rc_in} symlink={rc_ln} expand={rc_ex} equal={rc_eq} tree_unchanged={before == after} " \
                        f"control_rc={rc_ok} control_files={wrote}"


def g_signature_no_url_token():
    """WR-02: a verification command carrying a URL or an opaque token in its arguments never reaches the file."""
    tok = "ghp1234567890abcdefghijklmnopqrstuv"
    cmds = {"url": f"curl https://api.example.com/verify/{tok}",
            "query": f"curl https://api.example.com/verify?access={tok}&x=1",
            "userinfo": f"curl https://user:{tok}@host.example.com/verify",
            "bare-path": f"curl api.example.com/verify/{tok}"}
    root = scratch("wr02")
    fx = Fx(root)
    fx.human("go", ts(0))
    for i, c in enumerate(list(cmds.values()) + [TEST_CMD]):
        call(fx, i, [(f"t{i}", "Bash", {"command": c})])
        fx.tool_result(f"t{i}", "ok" * 50, ts(11 + i))
    call(fx, 9)
    rc, res, out, err, out_dir = pil_other("h", root)
    written = "".join(p.read_text(encoding="utf-8") for p in out_dir.glob("*.md"))
    sigs = sorted(r["signature"] for r in res["details"]["cmd_signatures"])
    unit = {k: kp.cmd_signature(v) for k, v in cmds.items()}
    leaked = tok in written + out + err or "api.example.com" in written + out
    ok = (rc in (0, 3) and not leaked and TEST_CMD in sigs and unit["url"] == "curl <url>"
          and unit["query"] == "curl <url>" and unit["userinfo"] == "curl <url>"
          and unit["bare-path"] == "curl <opaque>" and kp.cmd_signature("python3 tools/test_x.py") == TEST_CMD)
    return ok, f"rc={rc} leaked={leaked} unit={unit} sigs={sigs}"


def g_r3_terminal_requires_primary():
    """WR-04: R3 on a pillar WITH a terminal, driven by the instrument's real output: the primary file is accepted, a
    hand-written KME-G file and a doctored primary are refused, and the wrapper's frozen-rule table equals the instrument's."""
    icp = _icp()
    root = scratch("wr04")
    fx = Fx(root, project="-home-x-kme-e")
    fx.human("start", ts(0))
    rd(fx, 0, "r1", "/w/big.py", E_BODY)
    call(fx, 1)
    call(fx, 2)
    pop = {"sessions_active": 1, "sessions_dead": 0, "calls": 3, "input": 30, "cache_write": 0, "cache_read": 3000,
           "output": 15}
    frozen = write_frozen(root / "frozen.json", **{"KME-L": pop, "KME-G": pop})
    proj, outd = root / "projects" / "-home-x-kme-e", root / "m"
    rc1, _o, e1 = run_main(["e", "--denominator", "KME-L", "--frozen-file", frozen, "--root", str(proj),
                            "--out-dir", str(outd)])
    prim = next(iter(outd.glob("E-KME-L-*.md")), None)
    if rc1 not in (0, 3) or prim is None:
        return False, f"rc={rc1} files={sorted(f.name for f in outd.glob('*.md'))} err={e1[-200:]}"
    hand = outd / "E-HAND-KME-G.md"
    hand.write_text('---\ndenominator: "KME-G"\ncommand: "python3 x"\n---\n\nKME-L KME-G CPP-D-W7 by hand.\n',
                    encoding="utf-8")
    text = prim.read_text(encoding="utf-8")
    fm0 = parse_measurement(text)[0]
    forged = outd / "E-FORGED.md"
    forged.write_text(text.replace('denominator: "KME-L"', 'denominator: "KME-G"', 1), encoding="utf-8")
    res = icp.ce.Resolver()

    def fails(*refs):
        led = {"state": {"E": {"terminal": "RESEARCH_INSUFFICIENT_EVIDENCE", "evidence": [
            {"kind": "measurement", "ref": str(r), "sha256": "0" * 64} for r in refs]}}}
        with icp_sources(icp, frozen_file=frozen):
            return icp.check_measurement_scope(led, res, only=["E"])
    # the instrument's terminal claim is only believed when the file agrees with itself: a verdict-bearing,
    # reproduced primary on the frozen rule. (A UNMEASURED verdict file is terminal_evidence false by construction.)
    good, hand_f, forged_f = fails(prim), fails(hand), fails(forged)
    table_eq = ({k: list(v) for k, v in kp.RULE_DENOMINATORS.items()} == icp.FROZEN_RULE_DENOMINATORS
                and icp.FROZEN_SOURCE_DEFAULTS == {"frozen_file": kp.DENOMS_REL, "ce_ledger": kp.CE_LEDGER_REL})
    ok = (fm0["terminal_evidence"] is True and good == [] and any("cites no kme_pillars primary" in x for x in hand_f)
          and any("claims terminal_evidence true but" in x for x in forged_f) and table_eq)
    return ok, f"primary_terminal={fm0['terminal_evidence']} good={good} hand={hand_f[:1]} forged={forged_f[:1]} table_eq={table_eq}"


def g_second_workload_needs_measured_verdict():
    """WR-05: a second_workload file is valid only when its verdict is measured, and confirms only at '>= 3 %'."""
    def sw(build):
        root = scratch("wr05")
        build(root)
        rc, res, _o, _e = run_json(other_args(pdir(root), scratch("wr05-out"), extra=["--role", "second_workload"]))
        return rc, res
    rc_u, unm = sw(lambda r: (lambda fx: (fx.assistant("m1", "r1", (10, 100, 0, 5), ts(2)),
                                          fx.assistant("m2", "r2", (10, 0, 100, 5), ts(3))))(two_call_session(r)))
    rc_b, below = sw(lambda r: heavy_session(r, 1))
    rc_a, above = sw(lambda r: heavy_session(r, 4000))
    rows = {"unmeasured": (unm["materiality"], unm["second_workload_valid"], unm["second_workload_confirms"]),
            "below": (below["materiality"], below["second_workload_valid"], below["second_workload_confirms"]),
            "above": (above["materiality"], above["second_workload_valid"], above["second_workload_confirms"])}
    want = {"unmeasured": ("UNMEASURED", False, False), "below": ("< 3 %", True, False),
            "above": (">= 3 %", True, True)}
    return rows == want and unm["terminal_evidence"] is False, f"rows={rows} want={want}"


def g_frozen_source_recorded():
    """WR-07: the file records path + sha256 of the frozen source read, and anything but the committed default is not terminal."""
    import hashlib
    root = scratch("wr07")
    tracer_fixture(root)
    frozen = write_frozen(root / "frozen.json", **{"KME-L": TRACER_POP})
    ledger = ce_ledger_exact(root / "ce.json", pdir(root))
    want_sha = hashlib.sha256(Path(frozen).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    args = d_args(root, pdir(root), frozen, scratch("wr07-out"))
    FOLLOW_DEFAULTS[0] = False
    try:
        rc_a, a, _o, _e = run_json(args)                                           # scratch file, committed default untouched
        rc_b, b, _o, _e = run_json(d_args(root, pdir(root), frozen, scratch("wr07-out")) + ["--frozen-ce-ledger", ledger])
        rc_d, d, _o3, _e3 = run_json(dw7_args("d", root, ledger, scratch("wr07-out")))
    finally:
        FOLLOW_DEFAULTS[0] = True
    saved = kp.DENOMS_REL
    kp.DENOMS_REL = frozen                                                          # the frozen file IS the default ...
    try:
        FOLLOW_DEFAULTS[0] = False
        rc_c, c, _o, _e = run_json(args)                                            # ... so this one is terminal
        rc_e, e, _o, _e = run_json(args + ["--frozen-ce-ledger", ledger])           # ... unless the CE ledger flag is off-default
    finally:
        FOLLOW_DEFAULTS[0] = True
        kp.DENOMS_REL = saved
    rc_f, f, _o, _e = run_json(other_args(pdir(root), scratch("wr07-out")))
    fa = (a["frozen_source"] or {}).get("frozen_file", {})
    ok = (rc_a in (0, 3) and a["terminal_evidence"] is False and fa.get("default") is False and fa.get("sha256") == want_sha
          and fa.get("path") == str(frozen) and a["frozen_source"]["all_default"] is False
          and b["terminal_evidence"] is False and b["frozen_source"]["ce_ledger"]["default"] is False
          and d["terminal_evidence"] is False and d["frozen_source"]["ce_ledger"]["sha256"] and not d["frozen_source"]["all_default"]
          and c["terminal_evidence"] is True and c["frozen_source"]["all_default"] is True
          and e["terminal_evidence"] is False and e["frozen_source"]["all_default"] is False
          and f.get("frozen_source") is None)
    return ok, f"scratch file: terminal={a['terminal_evidence']} default={fa.get('default')} sha_ok={fa.get('sha256') == want_sha}; " \
               f"scratch ce flag: {b['terminal_evidence']}; D-W7 scratch ledger: {d['terminal_evidence']}; default file: {c['terminal_evidence']}; " \
               f"default file + off-default ce flag: {e['terminal_evidence']}; OTHER source={f.get('frozen_source')}"


def g_d_needs_hook_attachment():
    """IN-01: D is observed only where a hook_* attachment was seen; file / todo_reminder attachments alone are UNMEASURED."""
    def only_other(root, session, hook):
        fx = two_call_session(root, session=session)
        fx.attachment("file", ts(1), filename="/x/a.py", content="C" * 50)
        fx.attachment("todo_reminder", ts(1), content=["t"])
        if hook:
            fx.attachment("hook_success", ts(1), hookName="SessionStart:startup", stdout="{}", content="")
        fx.assistant(f"m1{session}", f"r1{session}", (10, 100, 0, 5), ts(2))
        fx.assistant(f"m2{session}", f"r2{session}", (10, 0, 100, 5), ts(3))
    r1 = scratch("in01a")
    only_other(r1, "s1", False)
    rc1, res1, _o, _e, _d = d_other(pdir(r1))
    r2 = scratch("in01b")
    only_other(r2, "s1", True)
    rc2, res2, _o, _e, _d = d_other(pdir(r2))
    r3 = scratch("in01c")
    only_other(r3, "s1", True)
    only_other(r3, "s2", False)
    rc3, res3, _o, _e, _d = d_other(pdir(r3))
    ok = (res1["observability"] == 0.0 and res1["materiality"] == "UNMEASURED" and rc1 == 3
          and res2["observability"] == 1.0 and res2["materiality"] == "< 3 %" and rc2 == 0
          and res3["observability"] == 0.5 and res3["materiality"] == "UNMEASURED"
          and res3["details"]["sessions_with_hook_attachments"] == 1
          and res3["details"]["sessions_with_attachment_lines"] == 2)
    return ok, f"non-hook attachments only: obs={res1['observability']} {res1['materiality']} rc={rc1}; plus hook_success: " \
               f"obs={res2['observability']} {res2['materiality']}; mixed: obs={res3['observability']} {res3['materiality']}"


GATES_TRACER = [
    ("V-KMEP-TRACER-D-E2E", g_tracer_e2e),
    ("V-KMEP-AUDIT-BYTE-IDENTICAL", g_audit_byte_identical),
    ("V-KMEP-CLI-USAGE", g_cli_usage),
]
GATES_REVIEW_FIX = [
    ("V-KMEP-OUT-DIR-INSIDE-ROOT", g_out_dir_inside_root),
    ("V-KMEP-SIGNATURE-NO-URL-TOKEN", g_signature_no_url_token),
    ("V-KMEP-R3-TERMINAL-REQUIRES-PRIMARY", g_r3_terminal_requires_primary),
    ("V-KMEP-SECOND-WORKLOAD-NEEDS-VERDICT", g_second_workload_needs_measured_verdict),
    ("V-KMEP-FROZEN-SOURCE-RECORDED", g_frozen_source_recorded),
    ("V-KMEP-D-NEEDS-HOOK-ATTACHMENT", g_d_needs_hook_attachment),
]
GATES = list(GATES_TRACER) + GATES_EXPANSION + GATES_E_TRACER + GATES_PILLAR_EF + GATES_G_TRACER + GATES_G_POLES + GATES_H + GATES_I_TRACER + GATES_EXPANSION_2 + GATES_PLAN5_TRACER + GATES_PLAN5_BUNDLE + GATES_REAL + GATES_REAL_2 + GATES_REVIEW_FIX


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
DRILL_GATES = [n for n, _ in GATES_TRACER + GATES_EXPANSION + GATES_E_TRACER + GATES_PILLAR_EF + GATES_G_TRACER + GATES_G_POLES + GATES_H + GATES_I_TRACER + GATES_EXPANSION_2 + GATES_REVIEW_FIX]    # the -REAL gates are excluded for speed


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


def _m_g_cite_never():
    import re as _re
    return _patch("CITE_RE", _re.compile(r"(?!x)x"))


def _m_g_order_ignored():
    return _patch("is_earlier", lambda rec_key, cand_key: True)


def _m_g_negation_kept():
    return _patch("strip_negated", lambda sentence: sentence)


def _m_h_verifier_never():
    import re as _re
    return _patch("VERIFIER_AGENT_RE", _re.compile(r"(?!x)x"))


def _m_h_verdict_on_sensitivity():
    return _patch("h_numerator_interval", lambda lo, hi, sens: (sens, sens))


def _m_i_main_for_subagents():
    return _patch("is_subagent_path", lambda path: False)


def _m_locate_calls_only():
    return _patch("cutoff_accepts", lambda match, measured, frozen: measured.get("calls") == frozen.get("calls"))


def _m_all_scans_per_pillar():
    real = kp.scan

    def mutant(roots, expand, host, observers, keep, project_filter=None):
        out = None
        for ob in observers:
            out = real(roots, expand, host, [ob], keep, project_filter)
        return out if out is not None else real(roots, expand, host, observers, keep, project_filter)
    return _patch("scan", mutant)


def _m_coverage_ignored():
    return _patch("referenced_coverage", lambda measured_calls, frozen_calls: 1.0)


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
    ("M12 G CITE_RE never matches (a citation becomes a record, reuse reads 0)", _m_g_cite_never,
     ["V-KMEP-G-CITATION-IS-REUSE"]),
    ("M13 G matching ignores timestamp order", _m_g_order_ignored, ["V-KMEP-G-ORDER"]),
    ("M14 G negated phrases are not removed", _m_g_negation_kept, ["V-KMEP-G-NEGATED-RETEST"]),
    ("M15 H VERIFIER_AGENT_RE never matches", _m_h_verifier_never, ["V-KMEP-H-VERIFIER-SUBAGENT"]),
    ("M16 H verdict computed on upper_sensitivity", _m_h_verdict_on_sensitivity,
     ["V-KMEP-H-SENSITIVITY-NOT-VERDICT"]),
    ("M17 I takes the main thread's first call for subagent files (every file read as a main-thread file)",
     _m_i_main_for_subagents, ["V-KMEP-I-E2E"]),
    ("M18 locate_cutoff accepts a calls-only match", _m_locate_calls_only, ["V-KMEP-UNTIL-AUTO-UNREACHABLE"]),
    ("M19 all scans once per pillar", _m_all_scans_per_pillar, ["V-KMEP-ALL-ONE-SCAN"]),
    ("M20 coverage ignored for a referenced denominator", _m_coverage_ignored, ["V-KMEP-DW7-COVERAGE"]),
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
