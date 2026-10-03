#!/usr/bin/env python3
"""V-FLOOR-* gates: the floor regression gate (incremental-cognition phase 4, pillar K).

Hermetic: every fixture is a synthetic transcript tree built here under a scratch directory; nothing reads or
writes the real ~/.claude and no session is ever spawned. A SKIP or an INCONCLUSIVE is printed and counted apart;
it is never a PASS and never part of the n/m denominator.

    python3 tools/test_floor_regression_gate.py                       run every gate
    python3 tools/test_floor_regression_gate.py --drill               mutation drill (each mutant must be killed)
    python3 tools/test_floor_regression_gate.py --gate-path <file>    run the gates against another copy of the gate
"""
from __future__ import annotations

import atexit
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "wiki" / "tools"))
sys.path.insert(0, str(REPO))

DEFAULT_GATE = REPO / "tools" / "floor_regression_gate.py"
GATE_FILE = DEFAULT_GATE
if "--gate-path" in sys.argv:
    GATE_FILE = Path(sys.argv[sys.argv.index("--gate-path") + 1]).resolve()

TMP_ROOT = Path(tempfile.mkdtemp(prefix="floor-test-"))
SCRATCH_HOME = TMP_ROOT / "home0"
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


def load_gate(path: Path):
    spec = importlib.util.spec_from_file_location("floor_regression_gate", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["floor_regression_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


GATE = None
GATE_LOAD_ERROR = None
try:
    GATE = load_gate(GATE_FILE)
except Exception as _exc:  # noqa: BLE001 -- RED state: the gate file does not exist yet
    GATE_LOAD_ERROR = f"{_exc.__class__.__name__}: {_exc}"


# --------------------------------------------------------------------------- fixture builder
def ts(n: float) -> str:
    """ISO Z timestamp, 3 fractional digits, n seconds after 2026-10-04T10:00:00Z."""
    base = datetime.datetime(2026, 10, 4, 10, 0, 0, tzinfo=datetime.timezone.utc)
    t = base + datetime.timedelta(seconds=n)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


class Tx:
    """Builds one transcript at <root>/home/.claude/projects/<cwd, non-alphanumerics as "-">/<session>.jsonl."""

    def __init__(self, root, cwd=None, session="s1"):
        self.root = Path(root)
        self.home = self.root / "home"
        self.cwd = Path(cwd) if cwd else self.root / "repo"
        self.cwd.mkdir(parents=True, exist_ok=True)
        self.session = session
        self.rows: list[dict] = []
        self.n = 0
        d = self.home / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(self.cwd))
        d.mkdir(parents=True, exist_ok=True)
        self.path = d / f"{session}.jsonl"

    def add(self, **row):
        self.n += 1
        row.setdefault("sessionId", self.session)
        row["timestamp"] = ts(self.n)
        self.rows.append(row)
        return self

    def meta(self, kind="last-prompt"):
        return self.add(type=kind)

    def user(self, text, meta=False):
        return self.add(type="user", cwd=str(self.cwd), isMeta=meta, message={"role": "user", "content": text})

    def attachment(self, atype, **fields):
        return self.add(type="attachment", cwd=str(self.cwd), attachment={"type": atype, **fields})

    def file(self, path, text):
        return self.attachment("file", filename=str(path), displayPath=str(path), content={"type": "text", "file": {"content": text}})

    def hook_success(self, event, name, command, additional_context=None, system_message=None):
        out = {"hookSpecificOutput": {"hookEventName": event}}
        if additional_context is not None:
            out["hookSpecificOutput"]["additionalContext"] = additional_context
        if system_message is not None:
            out["systemMessage"] = system_message
        return self.attachment("hook_success", hookEvent=event, hookName=name, command=command,
                               stdout=json.dumps(out), content="ok", toolUseID="tu1", exitCode=0)

    def hook_context(self, event, name, elements):
        return self.attachment("hook_additional_context", hookEvent=event, hookName=name, content=list(elements), toolUseID="tu2")

    def hook_system_message(self, event, name, text):
        return self.attachment("hook_system_message", hookEvent=event, hookName=name, content=text)

    def instructions(self, files):
        return self.attachment("instructions", files=[{"path": str(p), "type": t, "content": c} for p, t, c in files])

    def skill_listing(self, entries, initial=True):
        content = "".join(f"- {n}: {d}\n" for n, d in entries)
        return self.attachment("skill_listing", content=content, names=[n for n, _ in entries],
                               skillCount=len(entries), isInitial=initial)

    def agent_listing(self, entries):
        return self.attachment("agent_listing_delta", addedTypes=[t for t, _ in entries],
                               addedLines=[f"- {t}: {d}" for t, d in entries], isInitial=True)

    def prompt_snapshot(self, parts):
        return self.attachment("prompt_snapshot", systemPrompt=list(parts))

    def assistant(self, usage=(2, 30000, 0, 10), model="claude-opus-5-5"):
        i, cc, cr, out = usage
        return self.add(type="assistant", cwd=str(self.cwd), message={
            "role": "assistant", "model": model, "content": [{"type": "text", "text": "OK"}],
            "usage": {"input_tokens": i, "cache_creation_input_tokens": cc, "cache_read_input_tokens": cr,
                      "output_tokens": out}})

    def write(self, path=None) -> Path:
        out = Path(path) if path else self.path
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            for r in self.rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        return out


FLOOR_DEFAULTS = dict(g=10000, p=10000, r=8000, skills=12000, hook=2000, sp=None, usage=(2, 30000, 0, 10),
                      prompt="Reply with the single word OK.", extra=())


def listing_entries(total, n=100):
    """n skill entries whose listing content is exactly `total` chars."""
    base = total // n
    out = []
    for i in range(n):
        name = f"s{i:03d}"
        line_len = base + (total - base * n if i == n - 1 else 0)
        out.append((name, "d" * (line_len - len(f"- {name}: ") - 1)))
    return out


def build_floor(root, session, sizes, cwd=None) -> Tx:
    s = dict(FLOOR_DEFAULTS)
    s.update(sizes)
    sp = s["sp"] if s["sp"] is not None else ["S" * 8000]
    tx = Tx(root, cwd, session)
    home, wd = tx.home, tx.cwd
    tx.meta("last-prompt")
    tx.user(s["prompt"])
    tx.instructions([
        (home / ".claude" / "CLAUDE.md", "User", "G" * s["g"]),
        (wd / "CLAUDE.md", "Project", "P" * s["p"]),
        (home / ".claude" / "rules" / "r1.md", "User", "R" * s["r"]),
    ])
    tx.skill_listing(listing_entries(s["skills"]))
    tx.hook_context("SessionStart", "SessionStart:startup", ["H" * s["hook"]])
    tx.prompt_snapshot(sp)
    for atype, fields in s["extra"]:
        tx.attachment(atype, **fields)
    tx.assistant(usage=s["usage"])
    return tx


def floor_pair(root, ref_sizes, now_sizes):
    """Two transcripts ref.jsonl / now.jsonl under the SAME home and cwd; default floor 50,000 chars, 30,002 tokens."""
    root = Path(root)
    ref = build_floor(root, "ref", ref_sizes or {})
    now = build_floor(root, "now", now_sizes or {})
    return ref.write(), now.write()


# --------------------------------------------------------------------------- runners
def run_cli(args, env_extra=None):
    """The real CLI as a subprocess: [sys.executable, <gate file>, *args], cwd = repo root, HOME = scratch home."""
    env = dict(os.environ)
    SCRATCH_HOME.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(SCRATCH_HOME)
    env["USERPROFILE"] = str(SCRATCH_HOME)
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, str(GATE_FILE), *[str(a) for a in args]], cwd=str(REPO), env=env,
                       capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout, p.stderr


def run_main(args):
    """In-process GATE.main with stdout and stderr captured, so a drill's monkeypatch reaches it."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = GATE.main([str(a) for a in args])
    return rc, out.getvalue(), err.getvalue()


def last_line(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- gates: tracer
def g_tracer_e2e():
    root = scratch("tracer")
    ref_tx, now_tx = floor_pair(root, {}, {"g": 11024})
    ref_json = root / "ref.json"
    why = []
    # (a) write the reference
    rc, out, err = run_cli(["--write-reference", ref_json, "--transcript", ref_tx])
    if rc != 0 or not ref_json.is_file():
        return False, f"(a) write rc={rc} out={out[-200:]!r} err={err[-200:]!r}"
    ref = json.loads(ref_json.read_text(encoding="utf-8"))
    rows = {(r["layer"], r["scope"]): r["chars"] for r in ref.get("layers", [])}
    if ref.get("schema") != "floor-reference/1":
        why.append(f"schema={ref.get('schema')!r}")
    if ref.get("total_chars") != 50000:
        why.append(f"total_chars={ref.get('total_chars')}")
    if (ref.get("tokens") or {}).get("first_call_total") != 30002:
        why.append(f"first_call_total={(ref.get('tokens') or {}).get('first_call_total')}")
    for key, want in (("memory_global", 10000), ("memory_project", 10000), ("rules", 8000)):
        scope = "project" if key == "memory_project" else "universal"
        if rows.get((key, scope)) != want:
            why.append(f"{key}/{scope}={rows.get((key, scope))} want {want}")
    if why:
        return False, "(a) " + "; ".join(why)
    # (b) the same floor is within bound
    rc, out, err = run_cli(["--check", "--reference", ref_json, "--transcript", ref_tx])
    if rc != 0 or not last_line(out).startswith("FLOOR verdict=WITHIN_BOUND exit=0"):
        return False, f"(b) rc={rc} last={last_line(out)!r}"
    # (c) +1,024 universal chars is red, naming layer and scope
    rc, out, err = run_cli(["--check", "--reference", ref_json, "--transcript", now_tx])
    lines = out.splitlines()
    risk = [ln for ln in lines if ln.startswith("RISE memory_global scope=universal delta=+1024")]
    scope_ok = "SCOPE universal=+1024 project=+0 harness=+0 unattributed=+0" in lines
    if rc != 1 or not risk or "universal_1k" not in risk[0] or not scope_ok:
        return False, f"(c) rc={rc} rise={risk} scope_line={scope_ok} out={out[-300:]!r}"
    # (d) a missing transcript is UNMEASURABLE, never 0
    rc, out, err = run_cli(["--check", "--reference", ref_json, "--transcript", root / "absent.jsonl"])
    if rc != 2 or not last_line(out).startswith("FLOOR verdict=UNMEASURABLE exit=2 reason=no_transcript"):
        return False, f"(d) rc={rc} last={last_line(out)!r}"
    return True, "write=0 check-same=0 seeded+1024=1(RISE memory_global universal universal_1k) absent=2(no_transcript)"


def g_window_append_stable():
    """R2-W1: rows appended AFTER the first assistant row never move the measurement or the window digest."""
    root = scratch("window")
    tx = build_floor(root, "base", {})
    base_path = tx.write()
    # the same transcript with extra rows appended after the first assistant row
    tx.user("a later prompt that must not count")
    tx.hook_context("Stop", "Stop:late", ["L" * 3000])
    tx.attachment("brand_new_late", payload="Z" * 5000)
    tx.assistant(usage=(5, 99999, 0, 7))
    appended_path = tx.write(root / "appended.jsonl")
    a, b = GATE.measure(str(base_path)), GATE.measure(str(appended_path))
    why = []
    if a["components"] != b["components"]:
        why.append("components moved")
    if a["layers"] != b["layers"] or a["total_chars"] != b["total_chars"]:
        why.append("layers/total moved")
    if a["tokens"] != b["tokens"]:
        why.append("tokens moved")
    pa, pb = a["provenance"], b["provenance"]
    if pa["window_sha256"] != pb["window_sha256"] or pa["window_rows"] != pb["window_rows"]:
        why.append(f"window moved {pa['window_sha256'][:12]}/{pa['window_rows']} vs {pb['window_sha256'][:12]}/{pb['window_rows']}")
    if why:
        return False, "; ".join(why)
    # verdict through the CLI: a reference from the base, checked against the appended transcript, is within bound
    ref_json = root / "ref.json"
    rc, out, _ = run_main(["--write-reference", ref_json, "--transcript", base_path])
    if rc != 0:
        return False, f"write rc={rc} {out[-200:]!r}"
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", appended_path])
    if rc != 0 or not last_line(out).startswith("FLOOR verdict=WITHIN_BOUND"):
        return False, f"check of appended rc={rc} last={last_line(out)!r}"
    ref = json.loads(ref_json.read_text(encoding="utf-8"))
    if ref["provenance"].get("window_sha256") != pa["window_sha256"] or ref["provenance"].get("window_rows") != pa["window_rows"]:
        return False, "reference provenance does not carry window_sha256 / window_rows"
    if not re.search(r"^WINDOW .*same=yes", out, re.M):
        return False, f"check output carries no WINDOW same=yes line: {out[-300:]!r}"
    # control: a row changed BEFORE the first assistant row changes the digest (the gate can go red)
    tx2 = build_floor(root, "edited", {"prompt": "Reply with the single word OK!"})
    c = GATE.measure(str(tx2.write()))
    if c["provenance"]["window_sha256"] == pa["window_sha256"]:
        return False, "control: editing a pre-assistant row did not change window_sha256"
    if c["provenance"]["window_rows"] != pa["window_rows"]:
        return False, "control: editing a row changed window_rows"
    return True, f"window_sha256={pa['window_sha256'][:12]} rows={pa['window_rows']} stable under 4 appended rows; pre-assistant edit -> {c['provenance']['window_sha256'][:12]}"


# --------------------------------------------------------------------------- run
GATES_TRACER = [
    ("V-FLOOR-TRACER-E2E", g_tracer_e2e),
    ("V-FLOOR-WINDOW-APPEND-STABLE", g_window_append_stable),
]
GATES = list(GATES_TRACER)


def run_all() -> int:
    if GATE is None:
        record("FAIL", "V-FLOOR-GATE-LOADS", f"{GATE_FILE}: {GATE_LOAD_ERROR}")
        print("FLOOR_PASS=0/1  threshold=1/1  skipped=0  inconclusive=0")
        return 1
    for name, fn in GATES:
        run_gate(name, fn)
    graded = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    passes = sum(1 for r in graded if r[0] == "PASS")
    skipped = sum(1 for r in RESULTS if r[0] == "SKIP")
    inconclusive = sum(1 for r in RESULTS if r[0] == "INCONCLUSIVE")
    m = len(graded)
    print(f"FLOOR_PASS={passes}/{m}  threshold={m}/{m}  skipped={skipped}  inconclusive={inconclusive}")
    return 0 if passes == m and m > 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
