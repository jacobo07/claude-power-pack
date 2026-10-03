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

    def tool_result(self, tool_use_id, text, t):
        return self._w({"type": "user", "timestamp": t, "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}]}})

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


GATES_TRACER = [
    ("V-KMEP-TRACER-D-E2E", g_tracer_e2e),
    ("V-KMEP-AUDIT-BYTE-IDENTICAL", g_audit_byte_identical),
    ("V-KMEP-CLI-USAGE", g_cli_usage),
]
GATES = list(GATES_TRACER)


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


if __name__ == "__main__":
    sys.exit(run_all())
