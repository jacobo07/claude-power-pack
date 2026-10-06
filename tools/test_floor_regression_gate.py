#!/usr/bin/env python3
"""V-FLOOR-* gates: the floor regression gate (incremental-cognition phase 4, pillar K).

Hermetic: every fixture is a synthetic transcript tree built here under a scratch directory; nothing reads or
writes the real ~/.claude and no session is ever spawned. A SKIP or an INCONCLUSIVE is printed and counted apart;
it is never a PASS and never part of the n/m denominator.

    python3 tools/test_floor_regression_gate.py                       run every gate
    python3 tools/test_floor_regression_gate.py --drill               mutation drill (each mutant must be killed)
    python3 tools/test_floor_regression_gate.py --gate-path <file>    run the gates against another copy of the gate
    python3 tools/test_floor_regression_gate.py --real-session SID    seed a real session's transcript (laptop plane)
"""
from __future__ import annotations

import argparse
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
# The test fence: with these set the gate refuses any --probe executable outside the scratch root, so no test in this
# process (in-process or subprocess) can start a real `claude` session.
os.environ["CPP_FLOOR_GATE_TEST"] = "1"
os.environ["CPP_FLOOR_GATE_TEST_ROOT"] = str(TMP_ROOT)
# Hermetic dispatcher log (window health): an EXISTING empty log reads "settled", so the real host log -- whose
# pre-2026-10-05 lines name no session -- can never make a synthetic window "unknown". g_window_degraded overrides it.
(TMP_ROOT / "dispatcher-errors.log").write_text("", encoding="utf-8")
os.environ["CPP_DISPATCHER_ERROR_LOG"] = str(TMP_ROOT / "dispatcher-errors.log")
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
                      prompt="Reply with the single word OK.", extra=(), hookrows=None, skill_entries=None,
                      agents=None, sysmsg=None, hook_event="SessionStart", hook_name="SessionStart:startup")


def write_settings(base, regs, name="settings.json"):
    """Write <base>/.claude/<name> registering {event: [command, ...]}; a str `regs` is written verbatim (malformed fixtures)."""
    path = Path(base) / ".claude" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(regs, str):
        path.write_text(regs, encoding="utf-8")
    else:
        doc = {"hooks": {ev: [{"matcher": "", "hooks": [{"type": "command", "command": c} for c in cmds]}]
                         for ev, cmds in regs.items()}}
        path.write_text(json.dumps(doc), encoding="utf-8")
    return path


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
    tx.skill_listing(s["skill_entries"] if s["skill_entries"] is not None else listing_entries(s["skills"]))
    if s["agents"]:
        tx.agent_listing(s["agents"])
    ev, nm = s["hook_event"], s["hook_name"]
    if s["hookrows"] is not None:
        for command, text in s["hookrows"]:
            tx.hook_success(ev, nm, command, additional_context=text)
        tx.hook_context(ev, nm, [text for _, text in s["hookrows"]])
    else:
        tx.hook_context(ev, nm, ["H" * s["hook"]])
    for command, text in s["sysmsg"] or ():
        tx.hook_success(ev, nm, command, system_message=text)
        tx.hook_system_message(ev, nm, text)
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
def under_root(path) -> bool:
    try:
        p, r = Path(path).resolve(), TMP_ROOT.resolve()
    except (OSError, RuntimeError):
        return False
    return r in p.parents


def cli_env(env_extra=None) -> dict:
    """The environment of a gate subprocess: scratch HOME, repo on PYTHONPATH, the test fence ALWAYS on."""
    env = dict(os.environ)
    SCRATCH_HOME.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(SCRATCH_HOME)
    env["USERPROFILE"] = str(SCRATCH_HOME)
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env.update(env_extra or {})
    env["CPP_FLOOR_GATE_TEST"] = "1"
    env["CPP_FLOOR_GATE_TEST_ROOT"] = str(TMP_ROOT)
    return env


def refuse_real_probe(args, env) -> None:
    """V-FLOOR-NO-REAL-SESSION's guard: a --probe run from a test must name a stub executable under the scratch root."""
    if "--probe" in [str(a) for a in args]:
        exe = env.get("CPP_CLAUDE_EXE")
        if not exe or not under_root(exe):
            raise AssertionError("--probe from a test needs CPP_CLAUDE_EXE = a stub executable under the scratch root")


def run_cli(args, env_extra=None):
    """The real CLI as a subprocess: [sys.executable, <gate file>, *args], cwd = repo root, HOME = scratch home."""
    env = cli_env(env_extra)
    refuse_real_probe(args, env)
    p = subprocess.run([sys.executable, str(GATE_FILE), *[str(a) for a in args]], cwd=str(REPO), env=env,
                       capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout, p.stderr


def run_main(args):
    """In-process GATE.main with stdout and stderr captured, so a drill's monkeypatch reaches it."""
    if "--probe" in [str(a) for a in args] and (os.environ.get("CPP_FLOOR_GATE_TEST") != "1"
                                                or os.environ.get("CPP_FLOOR_GATE_TEST_ROOT") != str(TMP_ROOT)):
        raise AssertionError("--probe in-process needs the test fence on")
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
    appended_path = tx.write(tx.path.with_name("appended.jsonl"))   # same project dir: same install_home and cwd
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


# --------------------------------------------------------------------------- gates: attribution (plan 04-02)
def attr_check(ref_sizes, now_sizes, user_regs=None, project_regs=None, cli=False, root=None):
    """Floor pair under one home / cwd with the given settings registrations written first; (rc, out, root)."""
    root = root or scratch("attr")
    home, repo = root / "home", root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    if user_regs is not None:
        write_settings(home, user_regs)
    if project_regs is not None:
        write_settings(repo, project_regs)
    ref_tx, now_tx = floor_pair(root, ref_sizes, now_sizes)
    ref_json = root / "ref.json"
    if cli:
        rc, out, err = run_cli(["--write-reference", ref_json, "--transcript", ref_tx])
    else:
        with with_home(home):
            rc, out, err = run_main(["--write-reference", ref_json, "--transcript", ref_tx])
    if rc != 0:
        raise AssertionError(f"reference write rc={rc} {out[-200:]!r} {err[-200:]!r}")
    if cli:
        rc, out, err = run_cli(["--check", "--reference", ref_json, "--transcript", now_tx])
    else:
        with with_home(home):
            rc, out, err = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
    return rc, out, root


def hook_cmds(root):
    root = Path(root)
    return f'node "{root}/home/.claude/hooks/u.js"', f'node "{root}/repo/hooks/p.js"'


def g_hook_correlated():
    """A hook element is attributed to the command that produced it and the settings file that registers that command.

    Each case runs twice: through the real CLI (a subprocess) and in-process (where a drill mutant can reach it)."""
    why = []
    u_text, p_text = "u" * 2000, "p" * 2000
    for cli in (True, False):
        for label, now_u, now_p, want_rc, want_scope in (
                ("project hook +1024", u_text, p_text + "q" * 1024, 0, "project"),
                ("universal hook +1024", u_text + "q" * 1024, p_text, 1, "universal")):
            tag = f"{'cli' if cli else 'in-process'} {label}"
            root = scratch("hookc")
            U, P = hook_cmds(root)
            sizes = lambda a, b: {"hookrows": [(U, a), (P, b)], "hook_name": "SessionStart"}
            rc, out, _ = attr_check(sizes(u_text, p_text), sizes(now_u, now_p), user_regs={"SessionStart": [U]},
                                    project_regs={"SessionStart": [P]}, cli=cli, root=root)
            lay = find_lines(out, "LAYER hook_context:SessionStart:SessionStart ")
            scope = find_lines(out, "SCOPE ")
            risk = find_lines(out, "RISE hook_context:SessionStart:SessionStart ")
            if rc != want_rc or len(lay) != 1 or f"scope={want_scope} " not in lay[0] or not lay[0].endswith("delta=+1024"):
                why.append(f"{tag}: rc={rc} layer={lay} last={last_line(out)!r}")
                continue
            want_line = ("SCOPE universal=+0 project=+1024 harness=+0 unattributed=+0" if want_scope == "project"
                         else "SCOPE universal=+1024 project=+0 harness=+0 unattributed=+0")
            if scope != [want_line]:
                why.append(f"{tag}: scope={scope}")
            if want_rc == 1 and (len(risk) != 1 or "scope=universal" not in risk[0] or "universal_1k" not in risk[0]):
                why.append(f"{tag}: rise={risk}")
            if want_rc == 0 and risk:
                why.append(f"{tag}: unexpected rise {risk}")
    return (not why), "; ".join(why) or "+1024 in the project-registered hook: exit 0, scope project; in the user-registered hook: exit 1, scope universal (universal_1k); CLI and in-process"


def touch(path, text="x"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def measure_floor(root, sizes, session="m"):
    """Measure a freshly built floor (HOME pointed at the scratch home) -> the gate's measurement dict."""
    path = build_floor(root, session, sizes).write()
    with with_home(Path(root) / "home"):
        return GATE.measure(str(path))


def hook_src(cmd):
    """The component source a hook command is filed under: the contract key, with the first script file name of the command."""
    found = re.search(r"([A-Za-z0-9._-]+\.(?:js|py|cmd|sh))(?![A-Za-z0-9._-])", cmd)
    key = "hook:" + hashlib.sha256(cmd.encode("utf-8")).hexdigest()[:16]
    return key + (":" + found.group(1) if found else "")


def comp(m, layer, source):
    """(scope, scope_basis) of one component, or None."""
    for c in m["components"]:
        if c["layer"] == layer and c["source"] == source:
            return c["scope"], c.get("scope_basis")
    return None


def skill_sizes(named, filler=6000):
    """Floor sizes whose skill listing holds the named entries [(name, description length)] then `filler` chars of generic ones."""
    return {"skill_entries": [(n, "d" * k) for n, k in named] + listing_entries(filler, 50)}


def g_hook_system_message():
    why = []
    u_text, p_text = "u" * 2000, "p" * 2000
    for label, now_u, now_p, want_rc, want_scope in (
            ("project hook message +1024", u_text, p_text + "q" * 1024, 0, "project"),
            ("universal hook message +1024", u_text + "q" * 1024, p_text, 1, "universal")):
        root = scratch("sysm")
        U, P = hook_cmds(root)
        sizes = lambda a, b: {"sysmsg": [(U, a), (P, b)], "hook_name": "SessionStart"}
        rc, out, _ = attr_check(sizes(u_text, p_text), sizes(now_u, now_p), user_regs={"SessionStart": [U]},
                                project_regs={"SessionStart": [P]}, root=root)
        lay = find_lines(out, "LAYER hook_system_message:SessionStart:SessionStart ")
        if rc != want_rc or len(lay) != 1 or f"scope={want_scope} " not in lay[0] or not lay[0].endswith("delta=+1024"):
            why.append(f"{label}: rc={rc} layer={lay} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "systemMessage attributed through the producing command: project +1024 green, universal +1024 red"


def g_hook_plugin():
    root = scratch("plug")
    cmd = "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd session-start"
    sizes = lambda n: {"hookrows": [(cmd, "x" * n)], "hook_name": "SessionStart"}
    m = measure_floor(root, sizes(2000))
    got = comp(m, "hook_context:SessionStart:SessionStart", hook_src(cmd))
    rc, out, _ = attr_check(sizes(2000), sizes(3024))
    risk = find_lines(out, "RISE hook_context:SessionStart:SessionStart scope=universal")
    ok = got == ("universal", "plugin") and rc == 1 and len(risk) == 1
    return ok, f"component={got} +1024: rc={rc} rise={risk}"


def g_hook_event_fallback():
    """No producing row: the event's registrations never decide the scope (WR-02 supersedes the event fallback)."""
    why = []
    layer, src = "hook_context:UserPromptSubmit:UserPromptSubmit", "event:UserPromptSubmit"
    U, P = "node user.js", "node project.js"
    want = ("unattributed", "event_uncorrelated")
    for label, user, proj in (("user only", {"UserPromptSubmit": [U]}, None),
                              ("project only", None, {"UserPromptSubmit": [P]}),
                              ("both", {"UserPromptSubmit": [U]}, {"UserPromptSubmit": [P]}),
                              ("user registers another event", {"SessionStart": [U]}, {"SessionStart": [P]})):
        root = scratch("evfb")
        if user is not None:
            write_settings(root / "home", user)
        if proj is not None:
            write_settings(root / "repo", proj)
        m = measure_floor(root, {"hook_event": "UserPromptSubmit", "hook_name": "UserPromptSubmit"})
        got = comp(m, layer, src)
        if got != want:
            why.append(f"{label}: {got} want {want}")
    sizes = lambda n: {"hook_event": "UserPromptSubmit", "hook_name": "UserPromptSubmit", "hook": n}
    rc, out, _ = attr_check(sizes(2000), sizes(3024), project_regs={"UserPromptSubmit": [P]})
    if rc != 1 or not find_lines(out, f"LAYER {layer} scope=unattributed") or find_lines(out, f"LAYER {layer} scope=project"):
        why.append(f"project-only +1024: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "no producing row: unattributed whatever the registrations (user / project / both / other event); project-only +1024 red"


def g_hook_ambiguous():
    why = []
    layer = "hook_context:SessionStart:SessionStart"
    root = scratch("amb")
    C = f'node "{root}/shared.js"'
    sizes = lambda n: {"hookrows": [(C, "c" * n)], "hook_name": "SessionStart"}
    rc, out, _ = attr_check(sizes(2000), sizes(3024), user_regs={"SessionStart": [C]}, project_regs={"SessionStart": [C]},
                            root=root)
    risk = find_lines(out, f"RISE {layer} scope=unattributed")
    if rc != 1 or len(risk) != 1:
        why.append(f"one command in both settings +1024: rc={rc} rise={risk}")
    root = scratch("amb")
    X1, X2 = f'node "{root}/x1.js"', f'node "{root}/x2.js"'
    sizes = lambda n: {"hookrows": [(X1, "t" * n), (X2, "t" * n)], "hook_name": "SessionStart"}
    write_settings(root / "home", {"SessionStart": [X1, X2]})
    m = measure_floor(root, sizes(1000))
    got = comp(m, layer, "ambiguous:SessionStart")
    if got != ("unattributed", "ambiguous"):
        why.append(f"two commands, equal text: {got}")
    return (not why), "; ".join(why) or "a command registered in both settings, and two commands producing equal text, are unattributed"


def g_settings_unreadable():
    why = []
    layer = "hook_context:SessionStart:SessionStart"
    for label, bad_where, bad_text in (("project settings not JSON", "project", "{not json"),
                                       ("project settings a JSON list", "project", "[]"),
                                       ("user settings not JSON", "user", "{nope")):
        root = scratch("unr")
        U, P = hook_cmds(root)
        sizes = lambda a, b: {"hookrows": [(U, a), (P, b)], "hook_name": "SessionStart"}
        user = {"SessionStart": [U]} if bad_where != "user" else bad_text
        proj = {"SessionStart": [P]} if bad_where != "project" else bad_text
        rc, out, _ = attr_check(sizes("u" * 2000, "p" * 2000), sizes("u" * 2000, "p" * 3024), user_regs=user,
                                project_regs=proj, root=root)
        m = measure_floor(root, sizes("u" * 2000, "p" * 2000))
        got = comp(m, layer, hook_src(P))
        risk = find_lines(out, f"RISE {layer} scope=unattributed")
        if rc != 1 or len(risk) != 1 or got != ("unattributed", "unknown_settings"):
            why.append(f"{label}: rc={rc} rise={risk} component={got}")
    root = scratch("unr")
    U, P = hook_cmds(root)
    sizes = lambda b: {"hookrows": [(U, "u" * 2000), (P, b)], "hook_name": "SessionStart"}
    rc, out, _ = attr_check(sizes("p" * 2000), sizes("p" * 3024), user_regs={"SessionStart": [U]},
                            project_regs={"SessionStart": [P]}, root=root)
    if rc != 0:
        why.append(f"control (readable settings, project hook +1024): rc={rc}")
    return (not why), "; ".join(why) or "malformed or non-object settings -> unknown_settings, +1024 red; readable control green"


def g_exec_form_registration():
    """A hook registered in exec form (`command` + `args`) is recorded by the harness as the space-joined command line;
    the registration must match that line, or every exec-form CPP hook reads `no_registration` (measured 2026-10-05:
    59 of 65 laptop hooks, the SessionStart dispatcher among them)."""
    why = []
    root = Path(scratch("exe"))
    home, cwd = root / "home", root / "proj"
    cwd.mkdir(parents=True, exist_ok=True)
    node, script = "C:/Program Files/nodejs/node.exe", "C:/x/.claude/hooks/hook-dispatcher.js"
    joined = f"{node} {script} --event=SessionStart-chain"
    entries = [{"type": "command", "command": node, "args": [script, "--event=SessionStart-chain"]},
               {"type": "command", "command": "node legacy.js"}]
    write_settings(home, json.dumps({"hooks": {"SessionStart": [{"matcher": "", "hooks": entries}]}}))
    regs = GATE.registrations(home / ".claude" / "settings.json") or {}
    if joined not in regs.get("SessionStart", set()):
        why.append(f"exec form not registered as its joined line: {sorted(regs.get('SessionStart', set()))}")
    if "node legacy.js" not in regs.get("SessionStart", set()):
        why.append("control: string-form command lost")
    got = GATE.command_scope(joined, GATE.AttributionContext(cwd, home))
    if got != ("universal", "user_settings"):
        why.append(f"joined exec-form command scope={got}")
    bad = [{"type": "command", "command": node, "args": "not-a-list"}]
    write_settings(home, json.dumps({"hooks": {"SessionStart": [{"matcher": "", "hooks": bad}]}}))
    if GATE.registrations(home / ".claude" / "settings.json") is not None:
        why.append("args that are not a list of strings must read unknown (None), never a partial registration")
    return (not why), "; ".join(why) or "exec form matched by its joined line -> universal/user_settings; string form kept; malformed args -> unknown"


def g_cwd_absent_unattributed():
    """A transcript whose cwd is not a directory on this host (a laptop transcript read elsewhere) is never filed as project."""
    why = []
    layer = "hook_context:SessionStart:SessionStart"
    sizes = lambda: {"hookrows": [(U, "u" * 2000), (P, "p" * 2000)], "hook_name": "SessionStart",
                     "skill_entries": [("ps", "d" * 100), ("us", "d" * 100)] + listing_entries(6000, 50),
                     "agents": [("pa", "agent"), ("ua", "agent")]}
    for present in (True, False):
        root = scratch("cwdabs")
        U, P = hook_cmds(root)
        write_settings(root / "home", {"SessionStart": [U], "UserPromptSubmit": [U]})
        write_settings(root / "repo", {"SessionStart": [P]})
        touch(root / "repo" / ".claude" / "skills" / "ps" / "SKILL.md")
        touch(root / "home" / ".claude" / "skills" / "us" / "SKILL.md")
        touch(root / "repo" / ".claude" / "agents" / "pa.md")
        touch(root / "home" / ".claude" / "agents" / "ua.md")
        path = build_floor(root, "m", {**sizes(), "hook_event": "SessionStart"}).write()
        up = build_floor(root, "up", {"hook_event": "UserPromptSubmit", "hook_name": "UserPromptSubmit"}).write()
        if not present:
            shutil.rmtree(root / "repo")
        with with_home(root / "home"):
            m, mu = GATE.measure(str(path)), GATE.measure(str(up))
        want = {
            "hook P": (comp(m, layer, hook_src(P)), ("project", "project_settings") if present else ("unattributed", "not_on_this_host")),
            "hook U": (comp(m, layer, hook_src(U)), ("universal", "user_settings") if present else ("unattributed", "not_on_this_host")),
            "event uncorrelated": (comp(mu, "hook_context:UserPromptSubmit:UserPromptSubmit", "event:UserPromptSubmit"),
                                   ("unattributed", "event_uncorrelated")),
            "skill ps": (comp(m, "skill_listing", "ps"), ("project", "project_file") if present else ("unattributed", "not_on_this_host")),
            "skill us": (comp(m, "skill_listing", "us"), ("universal", "install_file") if present else ("unattributed", "not_on_this_host")),
            "agent pa": (comp(m, "other:agent_listing_delta", "pa"), ("project", "project_file") if present else ("unattributed", "not_on_this_host")),
            "agent ua": (comp(m, "other:agent_listing_delta", "ua"), ("universal", "install_file") if present else ("unattributed", "not_on_this_host")),
        }
        for k, (got, w) in want.items():
            if got != w:
                why.append(f"cwd {'present' if present else 'absent'} {k}: {got} want {w}")
    # the verdict: a +1,024 skill rise that is green as project with the cwd present is red without it
    for present in (True, False):
        root = scratch("cwdabs")
        touch(root / "repo" / ".claude" / "skills" / "ps" / "SKILL.md")
        ref, now = floor_pair(root, skill_sizes([("ps", 100)]), skill_sizes([("ps", 1124)]))
        if not present:
            shutil.rmtree(root / "repo")
        ref_json = root / "ref.json"
        with with_home(root / "home"):
            rc0, out0, _ = run_main(["--write-reference", ref_json, "--transcript", ref])
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now])
        if rc0 != 0 or rc != (0 if present else 1):
            why.append(f"verdict cwd {'present' if present else 'absent'}: write={rc0} check={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "cwd present: hooks/skills/agents attributed; cwd absent: all unattributed (not_on_this_host), +1024 red"


def g_skill_project():
    root = scratch("skp")
    touch(root / "repo" / ".claude" / "skills" / "ps" / "SKILL.md")
    touch(root / "repo" / ".claude" / "commands" / "ns" / "rest.md")
    named = lambda n: [("ps", n), ("ns:rest", 100)]
    rc, out, _ = attr_check(skill_sizes(named(100)), skill_sizes(named(1124)), root=root)
    lay = find_lines(out, "LAYER skill_listing ")
    why = []
    if rc != 0 or len(lay) != 1 or "scope=project" not in lay[0] or not lay[0].endswith("delta=+1024") or find_lines(out, "RISE"):
        why.append(f"project skill +1024: rc={rc} layer={lay} last={last_line(out)!r}")
    m = measure_floor(root, skill_sizes(named(100)))
    got = comp(m, "skill_listing", "ns:rest")
    if got != ("project", "project_file"):
        why.append(f"ns:rest via commands/ns/rest.md: {got}")
    return (not why), "; ".join(why) or "a skill under <cwd>/.claude/skills and a ns:rest command under <cwd>/.claude/commands/ns are project; +1024 green"


def g_skill_universal():
    root = scratch("sku")
    touch(root / "home" / ".claude" / "skills" / "us" / "SKILL.md")
    rc, out, _ = attr_check(skill_sizes([("us", 100)]), skill_sizes([("us", 1124)]), root=root)
    risk = find_lines(out, "RISE skill_listing scope=universal delta=+1024")
    ok = rc == 1 and len(risk) == 1 and "universal_1k" in risk[0]
    return ok, f"rc={rc} rise={risk}"


def g_skill_namespace():
    why = []
    root = scratch("skn")
    touch(root / "home" / ".claude" / "commands" / "bmad" / "architecture.md")
    touch(root / "home" / ".claude" / "commands" / "carl" / "tasks" / "add-rule.md")
    touch(root / "repo" / ".claude" / "commands" / "both" / "x.md")
    touch(root / "home" / ".claude" / "commands" / "both" / "x.md")
    named = [("bmad:architecture", 50), ("carl:tasks:add-rule", 50), ("superpowers:brainstorming", 50),
             ("both:x", 50), ("anthropic-skills:pdf", 50)]
    m = measure_floor(root, skill_sizes(named))
    for name, want in (("bmad:architecture", ("universal", "install_file")),
                       ("carl:tasks:add-rule", ("universal", "install_file")),
                       ("superpowers:brainstorming", ("universal", "plugin_namespace")),
                       ("anthropic-skills:pdf", ("universal", "plugin_namespace")),
                       ("both:x", ("unattributed", "ambiguous"))):
        got = comp(m, "skill_listing", name)
        if got != want:
            why.append(f"{name}: {got} want {want}")
    return (not why), "; ".join(why) or "ns:rest -> commands/ns/rest.md under the install is universal, an unfound plugin namespace is universal, both homes unattributed"


def g_skill_builtin_unattributed():
    why = []
    root = scratch("skb")
    touch(root / "repo" / ".claude" / "commands" / "osa.md")
    touch(root / "home" / ".claude" / "commands" / "osa.md")
    touch(root / "repo" / ".claude" / "escape" / "SKILL.md")      # <cwd>/.claude/skills/../escape/SKILL.md must NOT be reached
    named = [("init", 50), ("osa", 50), ("../escape", 50)]
    m = measure_floor(root, skill_sizes(named))
    for name, want in (("init", ("unattributed", "no_file")), ("osa", ("unattributed", "ambiguous")),
                       ("../escape", ("unattributed", "bad_name"))):
        got = comp(m, "skill_listing", name)
        if got != want:
            why.append(f"{name}: {got} want {want}")
    rc, out, _ = attr_check(skill_sizes([("init", 100)]), skill_sizes([("init", 1124)]))
    if rc != 1 or not find_lines(out, "RISE skill_listing scope=unattributed delta=+1024"):
        why.append(f"built-in +1024: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "a built-in, a name in both homes and a path-traversal name are unattributed; +1024 red"


def g_listing_split_exact():
    root = scratch("split")
    touch(root / "repo" / ".claude" / "skills" / "ps" / "SKILL.md")
    touch(root / "home" / ".claude" / "skills" / "us" / "SKILL.md")
    tx = Tx(root, None, "split")
    tx.user("x")
    listing = "header text\n- ps: first\n  more\n- us: second\n- init: third\n- bmad:thing: fourth\n"
    tx.attachment("skill_listing", content=listing, names=["ps", "us", "init", "bmad:thing"], skillCount=4, isInitial=True)
    tx.assistant()
    with with_home(root / "home"):
        m = GATE.measure(str(tx.write()))
    comps = [c for c in m["components"] if c["layer"] == "skill_listing"]
    by = {c["source"]: (c["scope"], c["chars"]) for c in comps}
    want = {"listing:header": ("unattributed", len("header text\n")),
            "ps": ("project", len("- ps: first\n") + len("  more\n")), "us": ("universal", len("- us: second\n")),
            "init": ("unattributed", len("- init: third\n")), "bmad:thing": ("universal", len("- bmad:thing: fourth\n"))}
    why = []
    if by != want:
        why.append(f"entries {by} want {want}")
    if sum(c["chars"] for c in comps) != len(listing):
        why.append("entries do not sum to len(content)")
    layers = {(r["layer"], r["scope"]): r["chars"] for r in m["layers"] if r["layer"] == "skill_listing"}
    if sum(layers.values()) != len(listing) or set(k[1] for k in layers) != {"project", "universal", "unattributed"}:
        why.append(f"layer rows {layers}")
    return (not why), "; ".join(why) or "per-entry scopes mix project / universal / unattributed and still sum to the listing's chars"


def g_agent_scope():
    why = []
    root = scratch("agt")
    touch(root / "repo" / ".claude" / "agents" / "pa.md")
    touch(root / "home" / ".claude" / "agents" / "sub" / "ua.md")
    entries = lambda n: [("pa", "p" * n), ("ua", "u" * 100), ("general-purpose", "g" * 100), ("plug:thing", "t" * 100)]
    m = measure_floor(root, {"agents": entries(100)})
    for name, want in (("pa", ("project", "project_file")), ("ua", ("universal", "install_file")),
                       ("general-purpose", ("unattributed", "no_file")), ("plug:thing", ("universal", "plugin_namespace"))):
        got = comp(m, "other:agent_listing_delta", name)
        if got != want:
            why.append(f"{name}: {got} want {want}")
    rc, out, _ = attr_check({"agents": entries(100)}, {"agents": entries(1124)}, root=root)
    if rc != 0 or not find_lines(out, "LAYER other:agent_listing_delta scope=project"):
        why.append(f"project agent +1024: rc={rc} last={last_line(out)!r}")
    ent2 = lambda n: [("pa", "p" * 100), ("ua", "u" * n)]
    root = scratch("agt")
    touch(root / "repo" / ".claude" / "agents" / "pa.md")
    touch(root / "home" / ".claude" / "agents" / "sub" / "ua.md")
    rc, out, _ = attr_check({"agents": ent2(100)}, {"agents": ent2(1124)}, root=root)
    if rc != 1 or not find_lines(out, "RISE other:agent_listing_delta scope=universal delta=+1024"):
        why.append(f"universal agent +1024: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "agents resolve under <cwd>/.claude/agents and <home>/.claude/agents (nested); a built-in is unattributed"


def g_relabel_no_rise():
    root = scratch("rel")
    U, P = hook_cmds(root)
    sizes = {"hookrows": [(P, "p" * 2000)], "hook_name": "SessionStart",
             "skill_entries": [("ps", "d" * 100)] + listing_entries(6000, 50)}
    ref_tx, now_tx = floor_pair(root, sizes, sizes)
    ref_json = root / "ref.json"
    with with_home(root / "home"):
        rc0, out0, _ = run_main(["--write-reference", ref_json, "--transcript", ref_tx])
    # after the reference: a project settings file registers P and a project skill file appears -> the same chars relabel
    write_settings(root / "repo", {"SessionStart": [P]})
    touch(root / "repo" / ".claude" / "skills" / "ps" / "SKILL.md")
    with with_home(root / "home"):
        rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
        now_m = GATE.measure(str(now_tx))
    ref = json.loads(ref_json.read_text(encoding="utf-8"))
    ref_scope = {(c["layer"], c["source"]): c["scope"] for c in ref["components"]}
    now_scope = {(c["layer"], c["source"]): c["scope"] for c in now_m["components"]}
    layer = "hook_context:SessionStart:SessionStart"
    relabeled = (ref_scope.get((layer, hook_src(P))), now_scope.get((layer, hook_src(P))), ref_scope.get(("skill_listing", "ps")),
                 now_scope.get(("skill_listing", "ps")))
    ok = (rc0 == 0 and rc == 0 and relabeled == ("unattributed", "project", "unattributed", "project")
          and not find_lines(out, "RISE") and not find_lines(out, "LAYER "))
    return ok, f"write={rc0} check={rc} relabeled(hook ref,now; skill ref,now)={relabeled} layers={find_lines(out, 'LAYER ')}"


# --------------------------------------------------------------------------- gates: rules (Task 2)
def pair_check(ref_sizes, now_sizes, ref_edit=None, extra_args=()):
    """Build a floor pair, write the reference in-process, optionally edit it, check the second transcript."""
    root = scratch("c")
    ref_tx, now_tx = floor_pair(root, ref_sizes, now_sizes)
    ref_json = root / "ref.json"
    rc, out, err = run_main(["--write-reference", ref_json, "--transcript", ref_tx])
    if rc != 0:
        raise AssertionError(f"reference write rc={rc} {out[-200:]!r} {err[-200:]!r}")
    if ref_edit is not None:
        doc = json.loads(ref_json.read_text(encoding="utf-8"))
        ref_edit(doc)
        ref_json.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    rc, out, err = run_main(["--check", "--reference", ref_json, "--transcript", now_tx, *extra_args])
    return rc, out, err


def find_lines(out, prefix):
    return [ln for ln in out.splitlines() if ln.startswith(prefix)]


def explain(layer, scope=None, unit="chars", bound=1100, reason="seeded", commit="abcdef1", drop=(), **over):
    """An evidenced budget entry. Since 2026-10-05 an explanation is not prose: it names its producer, the consumer
    that needs the bytes resident, an evidence file that exists in the repo, and when it is reviewed (pillar K)."""
    e = {"layer": layer, "unit": unit, "delta_bound": bound, "reason": reason, "commit": commit,
         "producer": "seeded-producer", "consumer": "seeded-consumer",
         "evidence": "tools/floor_regression_gate.py", "review_when": "seeded review condition"}
    if scope is not None:
        e["scope"] = scope
    e.update(over)
    for k in drop:
        e.pop(k, None)
    return e


def set_explanations(items):
    def edit(doc):
        doc["explanations"] = items
    return edit


def g_layer_table():
    root = scratch("table")
    tx = Tx(root, None, "table")
    home, wd = tx.home, tx.cwd
    tx.meta("last-prompt")
    tx.user("a prompt")
    tx.user("a slash expansion", meta=True)
    tx.file(wd / "src" / "a.py", "x" * 777)
    tx.hook_success("SessionStart", "SessionStart:startup", "node hook.js", additional_context="secret-ish stdout " * 20)
    tx.instructions([
        (home / ".claude" / "CLAUDE.md", "User", "u" * 101),
        (wd / "CLAUDE.md", "Project", "p" * 202),
        (home / ".claude" / "rules" / "a.md", "User", "a" * 303),
        (wd / ".claude" / "rules" / "b.md", "Project", "b" * 404),
        (wd / "notes" / "x.md", "Project", "x" * 505),
        ("/etc/claude/managed.md", "Managed", "m" * 606),
    ])
    listing = "header line\n- alpha: first\n  continued here\n- beta: second\n- gamma\n"
    tx.attachment("skill_listing", content=listing, names=["alpha", "beta", "gamma"], skillCount=3, isInitial=True)
    tx.agent_listing([("Explore", "reads"), ("Plan", "plans a lot")])
    tx.hook_context("SessionStart", "SessionStart:startup", ["e" * 11, "f" * 22])
    tx.hook_system_message("SessionStart", "SessionStart:startup", "m" * 33)
    tx.prompt_snapshot(["one " * 10, "two " * 20])
    harness_payloads = {
        "environment": {"snapshot": {"platform": "linux", "workingDirectory": str(wd)}},
        "model": {"identity": "claude-opus-5-5", "text": "model text"},
        "date": {"date": "2026-10-04"},
        "auto_mode": {"bypass": False},
        "command_permissions": {"allowedTools": ["Bash"]},
        "credential_org": {"organizationUuid": "o-1"},
        "remote_session_change": {"url": None, "commit": None},
        "session_context": {"context": {"userEmail": "a@b.c", "gitStatus": "clean"}},
    }
    for at, payload in harness_payloads.items():
        tx.attachment(at, **payload)
    tx.attachment("deferred_tools_delta", addedNames=["t"], addedLines=["- t"])
    tx.attachment("brand_new", payload="p" * 50)
    tx.assistant()
    m = GATE.measure(str(tx.write()))

    def jl(payload):
        return len(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    want = {
        ("memory_global", "universal"): 101, ("memory_project", "project"): 202, ("rules", "universal"): 303,
        ("rules", "project"): 404, ("other:instructions", "project"): 505, ("other:instructions", "unattributed"): 606,
        ("skill_listing", "unattributed"): len(listing),
        ("other:agent_listing_delta", "unattributed"): len("- Explore: reads") + len("- Plan: plans a lot"),
        ("hook_context:SessionStart:SessionStart:startup", "unattributed"): 33,    # no producing row: never attributed from the event (WR-02)
        ("hook_system_message:SessionStart:SessionStart:startup", "unattributed"): 33,
        ("system_prompt", "unattributed"): len("one " * 10) + len("two " * 20),
        ("other:deferred_tools_delta", "unattributed"): jl({"addedNames": ["t"], "addedLines": ["- t"]}),
        ("other:brand_new", "unattributed"): jl({"payload": "p" * 50}),
    }
    for at, payload in harness_payloads.items():
        want[(f"other:{at}", "harness")] = jl(payload)
    got = {(r["layer"], r["scope"]): r["chars"] for r in m["layers"]}
    why = []
    for k in sorted(set(want) | set(got)):
        if want.get(k) != got.get(k):
            why.append(f"{k}: want {want.get(k)} got {got.get(k)}")
    if m["total_chars"] != sum(want.values()):
        why.append(f"total_chars {m['total_chars']} != {sum(want.values())}")
    sk = [c for c in m["components"] if c["layer"] == "skill_listing"]
    if sum(c["chars"] for c in sk) != len(listing):
        why.append("skill entries do not sum to len(content)")
    srcs = {c["source"]: c["chars"] for c in sk}
    if srcs != {"listing:header": len("header line\n"), "alpha": len("- alpha: first\n") + len("  continued here\n"),
                "beta": len("- beta: second\n"), "gamma": len("- gamma\n")}:
        why.append(f"skill sources {srcs}")
    parts = [c for c in m["components"] if c["layer"] == "system_prompt"]
    if len(parts) != 2 or not all(re.fullmatch(r"part:[0-9a-f]{12}", c["source"]) and c["scope"] == "unattributed" for c in parts):
        why.append(f"system prompt parts {parts}")
    ex = m["excluded"]
    if not (ex["prompt_chars"] > 0 and ex["file_chars"] > 0 and ex["hook_success_rows"] == 1):
        why.append(f"excluded {ex}")
    if m["skill_listing"]["entries"] != 3 or m["skill_listing"]["skill_count"] != 3:
        why.append(f"skill_listing {m['skill_listing']}")
    return (not why), ("; ".join(why) or f"{len(want)} (layer, scope) rows exact; total {m['total_chars']}")


def g_positive_universal():
    rc, out, _ = pair_check({}, {"g": 11024})
    share = 1024 / 50000
    risk = find_lines(out, "RISE memory_global scope=universal delta=+1024")
    ok = share < 0.03 and rc == 1 and len(risk) == 1 and "universal_1k" in risk[0] and "layer_3pct" not in risk[0]
    return ok, f"share={share:.4f} rc={rc} rise={risk}"


def g_project_local():
    rc, out, _ = pair_check({}, {"p": 11024})
    scope = find_lines(out, "SCOPE ")
    layer = find_lines(out, "LAYER memory_project scope=project")
    ok = (rc == 0 and scope == ["SCOPE universal=+0 project=+1024 harness=+0 unattributed=+0"]
          and len(layer) == 1 and layer[0].endswith("delta=+1024") and not find_lines(out, "RISE"))
    return ok, f"rc={rc} scope={scope} layer={layer}"


def g_scope_report():
    why = []
    for name, now, want in (("project", {"p": 11024}, {"universal": 0, "project": 1024, "harness": 0, "unattributed": 0}),
                            ("universal", {"g": 11024}, {"universal": 1024, "project": 0, "harness": 0, "unattributed": 0})):
        rc, out, _ = pair_check({}, now, extra_args=["--json"])
        doc = json.loads(out)
        if doc.get("scope_deltas") != want:
            why.append(f"{name}: scope_deltas={doc.get('scope_deltas')}")
    return (not why), "; ".join(why) or "JSON scope_deltas split universal/project for both pairs"


def g_project_3pct():
    rc, out, _ = pair_check({}, {"p": 11600})
    risk = find_lines(out, "RISE memory_project scope=project")
    ok = rc == 1 and len(risk) == 1 and "rules=layer_3pct" in risk[0]
    return ok, f"rc={rc} rise={risk}"


def g_boundary():
    rc_lo, out_lo, _ = pair_check({}, {"g": 10999})
    rc_hi, out_hi, _ = pair_check({}, {"g": 11000})
    ok = rc_lo == 0 and rc_hi == 1 and bool(find_lines(out_hi, "RISE memory_global scope=universal delta=+1000"))
    return ok, f"+999 rc={rc_lo}; +1000 rc={rc_hi}"


def g_total_3pct():
    rc, out, _ = pair_check({}, {"r": 8500, "g": 10500, "p": 10600})
    rises = find_lines(out, "RISE ")
    ok = rc == 1 and len(rises) == 1 and rises[0].startswith("RISE total scope=unattributed delta=+1600") and "rules=total_3pct" in rises[0]
    return ok, f"rc={rc} rises={rises}"


def g_system_prompt_new_part():
    why = []
    rc, out, _ = pair_check({}, {"sp": ["S" * 8000, "N" * 1024]})
    risk = find_lines(out, "RISE system_prompt scope=unattributed delta=+1024")
    if rc != 1 or len(risk) != 1 or "universal_1k" not in risk[0]:
        why.append(f"new part: rc={rc} rise={risk}")
    rc, out, _ = pair_check({"sp": ["A" * 4000, "B" * 4000]}, {"sp": ["B" * 4000, "A" * 4000]})
    if rc != 0 or find_lines(out, "LAYER system_prompt"):
        why.append(f"swapped order: rc={rc} {find_lines(out, 'LAYER system_prompt')}")
    rc, out, _ = pair_check({}, {"sp": ["S" * 8000 + "E" * 200]})
    lay = find_lines(out, "LAYER system_prompt scope=unattributed")
    if rc != 0 or len(lay) != 1 or not lay[0].endswith("delta=+200"):
        why.append(f"edited part: rc={rc} {lay}")
    return (not why), "; ".join(why) or "new 1,024 part red (unattributed, universal_1k); swapped order green; edited part nets +200"


def g_harness_not_1k():
    sc = lambda n: ("session_context", {"context": {"userEmail": "a@b.c", "gitStatus": "g" * n}})
    rc, out, _ = pair_check({"extra": [sc(100)]}, {"extra": [sc(1300)]})
    scope = find_lines(out, "SCOPE ")
    ok = rc == 0 and scope == ["SCOPE universal=+0 project=+0 harness=+1200 unattributed=+0"] and not find_lines(out, "RISE")
    return ok, f"rc={rc} scope={scope}"


def g_unattributed_1k():
    rc, out, _ = pair_check({}, {"extra": [("brand_new", {"payload": "Z" * 1100})]})
    risk = find_lines(out, "RISE other:brand_new scope=unattributed")
    ok = rc == 1 and len(risk) == 1 and "rules=universal_1k" in risk[0]
    return ok, f"rc={rc} rise={risk}"


def g_fall_ratchet_hint():
    rc, out, _ = pair_check({}, {"g": 8000}, extra_args=["--json"])
    big = json.loads(out)
    rc2, out2, _ = pair_check({}, {"g": 9500}, extra_args=["--json"])
    small = json.loads(out2)
    ok = rc == 0 and rc2 == 0 and big.get("ratchet_hint") is True and small.get("ratchet_hint") is False
    return ok, f"-4%: rc={rc} hint={big.get('ratchet_hint')}; -1%: rc={rc2} hint={small.get('ratchet_hint')}"


def g_explained_green():
    why = []
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([explain("memory_global", "universal")]))
    if rc != 0 or not find_lines(out, "EXPLAINED memory_global scope=universal delta=+1024 by=abcdef1"):
        why.append(f"universal explained: rc={rc} last={last_line(out)!r}")
    rc, out, _ = pair_check({}, {"sp": ["S" * 8000, "N" * 1024]},
                            ref_edit=set_explanations([explain("system_prompt", "unattributed")]))
    if rc != 0 or not find_lines(out, "EXPLAINED system_prompt scope=unattributed delta=+1024"):
        why.append(f"system prompt explained: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "an explanation within its bound turns the red green and is printed"


def g_explanation_bound():
    why = []
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([explain("memory_global", "universal", bound=1024)]))
    if rc != 0:
        why.append(f"control: bound 1024 == delta 1024 must cover: rc={rc}")
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([explain("memory_global", "universal", bound=1000)]))
    if rc != 1:
        why.append(f"bound 1000 < delta 1024: rc={rc}")
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([explain("memory_global", "universal", unit="tokens")]))
    if rc != 1:
        why.append(f"unit tokens against a chars rise: rc={rc}")
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([explain("memory_global", "project")]))
    if rc != 1:
        why.append(f"explanation scope project against a universal rise: rc={rc}")
    return (not why), "; ".join(why) or "bound, unit and scope each limit what an explanation covers"


def g_explanation_empty_reason():
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([explain("memory_global", "universal", reason="   ")]))
    ok = rc == 2 and last_line(out).startswith("FLOOR verdict=UNMEASURABLE exit=2 reason=explanation_refused")
    return ok, f"rc={rc} last={last_line(out)!r}"


def g_explanation_fields():
    why = []
    cases = {"commit xyz": explain("memory_global", "universal", commit="xyz"),
             "delta_bound 0": explain("memory_global", "universal", bound=0),
             "unit bytes": explain("memory_global", "universal", unit="bytes"),
             "scope unknown": explain("memory_global", "everyone"),
             "layer empty": explain("", "universal"),
             "producer missing": explain("memory_global", "universal", drop=("producer",)),
             "consumer blank": explain("memory_global", "universal", consumer="  "),
             "review_when missing": explain("memory_global", "universal", drop=("review_when",)),
             "evidence not a repo file": explain("memory_global", "universal", evidence="vault/no/such/evidence.md"),
             "evidence escapes the repo": explain("memory_global", "universal", evidence="../outside.md")}
    for label, item in cases.items():
        rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([item]))
        if rc != 2 or "reason=explanation_refused" not in last_line(out):
            why.append(f"{label}: rc={rc} last={last_line(out)!r}")
    # one bad entry refuses the whole reference even when another entry would cover the rise
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations(
        [explain("memory_global", "universal"), explain("rules", "universal", reason="")]))
    if rc != 2:
        why.append(f"one bad entry among good: rc={rc}")
    return (not why), "; ".join(why) or "ten malformed entries and a mixed list each refuse the reference (exit 2)"


def g_explanation_is_debt():
    """An accepted rise stays visible: the EXPLAINED line names producer and evidence, and a DEBT line sums it."""
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([explain("memory_global", "universal")]))
    exp = find_lines(out, "EXPLAINED memory_global scope=universal delta=+1024 by=abcdef1")
    debt = find_lines(out, "DEBT ")
    ok = (rc == 0 and len(exp) == 1 and "producer=seeded-producer" in exp[0]
          and "evidence=tools/floor_regression_gate.py" in exp[0]
          and debt == ["DEBT accepted_rises=1 chars=+1024 tokens=+0"])
    # control: with nothing explained there is no debt line claiming zero debt from a rise that went red
    rc2, out2, _ = pair_check({}, {"g": 11024})
    ok = ok and rc2 == 1 and not find_lines(out2, "DEBT ")
    return ok, f"rc={rc} explained={exp} debt={debt} | unexplained rc={rc2}"


def g_window_degraded():
    """A window whose SessionStart chain the dispatcher abandoned (its log names the session) is never measured as a
    floor: a failed hub reads exactly like a smaller one. Checked windows refuse, references refuse, another session's
    abandonment does not count, and a missing log is reported as unknown, never as settled."""
    why = []
    root = scratch("deg")
    ref_tx, now_tx = floor_pair(root, {}, {})
    log = root / "dispatcher-errors.log"

    def line(sid):
        return ("2026-10-05T21:37:48.854Z [SessionStart-chain] CHAIN-DEADLINE-ABANDONED after 4000ms Error: still "
                f"running: ../skills/claude-power-pack/hooks/session_start_hub.js; session={sid}; host free=1MB\n")

    with env_set(CPP_DISPATCHER_ERROR_LOG=log):
        log.write_text("", encoding="utf-8")
        ref_json = root / "ref.json"
        rc, out, _ = run_main(["--write-reference", ref_json, "--transcript", ref_tx])
        if rc != 0:
            return False, f"clean reference write rc={rc} {last_line(out)!r}"
        rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
        if rc != 0 or not find_lines(out, "WINDOW_HEALTH settled"):
            why.append(f"settled control: rc={rc} health={find_lines(out, 'WINDOW_HEALTH')}")
        log.write_text(line("other-session-0001"), encoding="utf-8")
        rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
        if rc != 0:
            why.append(f"another session's abandonment degraded this one: rc={rc}")
        log.write_text(line(Path(now_tx).stem), encoding="utf-8")
        rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
        if rc != 2 or "reason=window_degraded" not in last_line(out):
            why.append(f"degraded checked window: rc={rc} last={last_line(out)!r}")
        log.write_text(line(Path(ref_tx).stem), encoding="utf-8")
        ref2 = root / "ref2.json"
        rc, out, _ = run_main(["--write-reference", ref2, "--transcript", ref_tx])
        if rc != 2 or "reason=window_degraded" not in last_line(out) or ref2.exists():
            why.append(f"degraded reference written: rc={rc} exists={ref2.exists()} last={last_line(out)!r}")
        # A line written before the dispatcher named sessions cannot be attributed: near this session's first call it
        # makes the window UNKNOWN, never settled (measured: probe 6eba7a1f read "settled" from exactly such a line).
        first = next(json.loads(ln)["timestamp"] for ln in Path(now_tx).read_text(encoding="utf-8").splitlines()
                     if ln.strip() and json.loads(ln).get("type") == "assistant")
        t0 = datetime.datetime.strptime(first, "%Y-%m-%dT%H:%M:%S.%fZ")
        # ... and an unknown window is never green (exit 2 window_unverified), while a far-off line leaves it settled.
        for offset, want, want_rc in ((10, "unknown", 2), (3600, "settled", 0)):
            stamp = (t0 - datetime.timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            log.write_text(f"{stamp} [SessionStart-chain] CHAIN-DEADLINE-ABANDONED after 4000ms Error: still running: "
                           "../skills/claude-power-pack/hooks/session_start_hub.js; host free=1MB\n", encoding="utf-8")
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
            if rc != want_rc or not find_lines(out, f"WINDOW_HEALTH {want}"):
                why.append(f"unnamed line {offset}s before first call: rc={rc} health={find_lines(out, 'WINDOW_HEALTH')} want {want}")
            if want_rc == 2 and "reason=window_unverified" not in last_line(out):
                why.append(f"unknown window not refused as window_unverified: {last_line(out)!r}")
        # an unknown window cannot become a champion either
        ref3 = root / "ref3.json"
        rc, out, _ = run_main(["--write-reference", ref3, "--transcript", ref_tx])
        if rc != 0:   # the ref window's first call is the same second as now's here; the unnamed line is 3600 s away
            why.append(f"settled reference refused: rc={rc} {last_line(out)!r}")
    with env_set(CPP_DISPATCHER_ERROR_LOG=root / "absent.log"):
        rc, out, _ = run_main(["--check", "--reference", root / "ref.json", "--transcript", now_tx])
        if rc != 2 or not find_lines(out, "WINDOW_HEALTH unknown") or "reason=window_unverified" not in last_line(out):
            why.append(f"absent log: rc={rc} health={find_lines(out, 'WINDOW_HEALTH')} last={last_line(out)!r}")
        rc, out, _ = run_main(["--write-reference", root / "ref4.json", "--transcript", ref_tx])
        if rc != 2 or "reason=window_unverified" not in last_line(out) or (root / "ref4.json").exists():
            why.append(f"reference from an unverifiable window: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or ("abandoned window exit 2 (check and reference), other session ignored, unnamed "
                                         "line near start -> unknown exit 2, far -> settled, absent log -> unknown, "
                                         "never green, never a champion")


def g_tokens_rule():
    why = []
    rc, out, _ = pair_check({}, {"usage": (2, 30998, 0, 10)})
    risk = find_lines(out, "RISE tokens scope=unattributed")
    if rc != 1 or len(risk) != 1 or "unit=tokens" not in risk[0] or "rules=tokens_3pct" not in risk[0]:
        why.append(f"+3.3% tokens: rc={rc} rise={risk}")
    for extra, want_rc in ((("--chars-only",), 0), ((), 2)):   # WR-03: not comparable is exit 2 unless --chars-only
        rc, out, _ = pair_check({}, {"usage": (2, 30998, 0, 10), "prompt": "A different prompt entirely."}, extra_args=extra)
        tl = find_lines(out, "TOKENS ")
        if rc != want_rc or len(tl) != 1 or "status=not_comparable" not in tl[0]:
            why.append(f"different prompt {extra}: rc={rc} tokens={tl}")
    rc, out, _ = pair_check({}, {"usage": (2, 30998, 0, 10)},
                            ref_edit=set_explanations([explain("tokens", unit="tokens", bound=1000)]))
    if rc != 0 or not find_lines(out, "EXPLAINED tokens scope=unattributed delta=+998"):
        why.append(f"explained tokens: rc={rc} last={last_line(out)!r}")
    rc, out, _ = pair_check({}, {"usage": (2, 30500, 0, 10)})
    if rc != 0:
        why.append(f"+1.6% tokens must stay green: rc={rc}")
    return (not why), "; ".join(why) or "tokens: +3.3% red, different prompt not_comparable, explained green, +1.6% green"


# --------------------------------------------------------------------------- gates: safety (Task 3)
REFERENCE_KEYS = {"schema", "provenance", "components", "layers", "total_chars", "tokens", "skill_listing",
                  "excluded", "explanations", "caveats"}
JSON_KEYS = {"verdict", "exit", "reason", "rows", "findings", "explained", "scope_deltas", "tokens_axis",
             "ratchet_hint", "reference", "provenance", "caveats", "detail", "probe_error", "cwd_admitted"}


@contextlib.contextmanager
def with_home(home):
    saved = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
    os.environ["HOME"] = os.environ["USERPROFILE"] = str(home)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def edit_json(path, fn):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    fn(doc)
    Path(path).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def unmeasurable(rc, out, reason):
    return rc == 2 and last_line(out).startswith(f"FLOOR verdict=UNMEASURABLE exit=2 reason={reason}")


def good_ref(prefix="u"):
    root = scratch(prefix)
    ref_tx, now_tx = floor_pair(root, {}, {})
    ref_json = root / "ref.json"
    rc, out, err = run_main(["--write-reference", ref_json, "--transcript", ref_tx])
    if rc != 0:
        raise AssertionError(f"reference write rc={rc} {out[-200:]!r}")
    return root, ref_tx, now_tx, ref_json


def g_unmeasurable_table():
    root, ref_tx, now_tx, ref_json = good_ref("unm")
    why = []

    def case(label, args, reason):
        rc, out, _ = run_main(args)
        if not unmeasurable(rc, out, reason):
            why.append(f"{label}: rc={rc} last={last_line(out)!r} want reason={reason}")

    check = ["--check", "--reference", ref_json, "--transcript"]
    rc, out, _ = run_main([*check, now_tx])
    if rc != 0:
        why.append(f"control: valid pair rc={rc}")
    case("missing transcript", [*check, root / "absent.jsonl"], "no_transcript")
    (root / "empty.jsonl").write_bytes(b"")
    case("empty file", [*check, root / "empty.jsonl"], "unreadable")
    (root / "junk.jsonl").write_text("not json\nstill not json\n", encoding="utf-8")
    case("non-JSON lines", [*check, root / "junk.jsonl"], "unreadable")
    nl = Tx(root, None, "nolisting")
    nl.user("x")
    nl.instructions([(nl.home / ".claude" / "CLAUDE.md", "User", "g" * 10)])
    nl.assistant()
    case("no skill_listing", [*check, nl.write()], "no_skill_listing")
    nl2 = Tx(root, None, "noninitial")
    nl2.skill_listing([("a", "b")], initial=False)
    nl2.assistant()
    case("only a non-initial skill_listing", [*check, nl2.write()], "no_skill_listing")
    case("missing reference", ["--check", "--reference", root / "nope.json", "--transcript", now_tx], "reference_missing")
    (root / "notjson.json").write_text("{nope", encoding="utf-8")
    case("reference not JSON", ["--check", "--reference", root / "notjson.json", "--transcript", now_tx], "reference_invalid")
    for label, edit in (("schema != floor-reference/1", lambda d: d.update(schema="floor-reference/0")),
                        ("components missing", lambda d: d.pop("components")),
                        ("total_chars not matching the components", lambda d: d.update(total_chars=1))):
        bad = root / "bad.json"
        bad.write_text(ref_json.read_text(encoding="utf-8"), encoding="utf-8")
        edit_json(bad, edit)
        case(label, ["--check", "--reference", bad, "--transcript", now_tx], "reference_invalid")
    other = root / "other.json"
    other.write_text(ref_json.read_text(encoding="utf-8"), encoding="utf-8")
    edit_json(other, lambda d: d["provenance"].update(plane="elsewhere"))
    case("plane edited", ["--check", "--reference", other, "--transcript", now_tx], "not_comparable")
    saved = GATE.DEFAULT_REFERENCE_REL
    GATE.DEFAULT_REFERENCE_REL = str(root / "absent-default.json")
    try:
        case("default reference absent", ["--check", "--transcript", now_tx], "reference_missing")
    finally:
        GATE.DEFAULT_REFERENCE_REL = saved
    return (not why), "; ".join(why) or "12 refusals each exit 2 with a named reason; the valid pair is exit 0"


def g_not_comparable():
    root, ref_tx, now_tx, ref_json = good_ref("nc")
    why = []
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
    if rc != 0:
        why.append(f"control: unedited reference rc={rc}")
    for fields in (("plane",), ("cwd",), ("platform",), ("install_home",), ("plane", "cwd")):
        bad = root / ("bad-" + "-".join(fields) + ".json")
        bad.write_text(ref_json.read_text(encoding="utf-8"), encoding="utf-8")

        def edit(d, fields=fields):
            for f in fields:
                d["provenance"][f] = "elsewhere"
        edit_json(bad, edit)
        rc, out, _ = run_main(["--check", "--reference", bad, "--transcript", now_tx])
        detail = "\n".join(find_lines(out, "UNMEASURABLE"))
        if not unmeasurable(rc, out, "not_comparable") or not all(f in detail for f in fields):
            why.append(f"{fields}: rc={rc} detail={detail!r} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "plane / cwd / platform / install_home each refuse and are named"


def g_admit_cwd():
    root, ref_tx, now_tx, ref_json = good_ref("ac")
    why = []
    bad = root / "bad-cwd.json"
    bad.write_text(ref_json.read_text(encoding="utf-8"), encoding="utf-8")
    edit_json(bad, lambda d: d["provenance"].update(cwd="elsewhere"))
    rc, out, _ = run_main(["--check", "--reference", bad, "--transcript", now_tx])
    if not unmeasurable(rc, out, "not_comparable"):
        why.append(f"without the flag: rc={rc} last={last_line(out)!r}")
    rc, out, _ = run_main(["--check", "--reference", bad, "--transcript", now_tx, "--admit-cwd"])
    if rc != 0 or not find_lines(out, "CWD_ADMITTED"):
        why.append(f"with --admit-cwd: rc={rc} last={last_line(out)!r}")
    bad2 = root / "bad-plane-cwd.json"
    bad2.write_text(ref_json.read_text(encoding="utf-8"), encoding="utf-8")
    edit_json(bad2, lambda d: d["provenance"].update(cwd="elsewhere", plane="elsewhere"))
    rc, out, _ = run_main(["--check", "--reference", bad2, "--transcript", now_tx, "--admit-cwd"])
    if not unmeasurable(rc, out, "not_comparable"):
        why.append(f"plane+cwd with the flag must still refuse: rc={rc} last={last_line(out)!r}")
    rc, out, _ = run_main(["--write-reference", root / "w-ac.json", "--transcript", now_tx, "--admit-cwd"])
    if not unmeasurable(rc, out, "admit_cwd_without_check"):
        why.append(f"--admit-cwd with --write-reference: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "cwd differs: exit 2 without the flag, exit 0 + CWD_ADMITTED with it; plane+cwd still exit 2; flag refused outside --check"


def g_write_safety():
    root, ref_tx, now_tx, ref_json = good_ref("ws")
    why = []
    home = root / "home"
    with with_home(home):
        before = ref_json.read_bytes()
        rc, out, _ = run_main(["--write-reference", ref_json, "--transcript", now_tx])
        if not unmeasurable(rc, out, "reference_exists") or ref_json.read_bytes() != before:
            why.append(f"existing target: rc={rc} last={last_line(out)!r} unchanged={ref_json.read_bytes() == before}")
        rc, out, _ = run_main(["--write-reference", ref_json, "--transcript", now_tx, "--replace"])
        doc = json.loads(ref_json.read_text(encoding="utf-8"))
        if rc != 0 or ref_json.read_bytes() == before or doc["provenance"]["session_id"] != "now":
            why.append(f"--replace: rc={rc} session={doc['provenance'].get('session_id')}")
        leftovers = [f.name for f in root.iterdir() if f.name.startswith("ref.json") and f.name != "ref.json"]
        if leftovers:
            why.append(f"--replace left temp files {leftovers}")
        if doc.get("explanations") != []:
            why.append(f"explanations={doc.get('explanations')}")
        target = home / ".claude" / "floor-ref.json"
        rc, out, _ = run_main(["--write-reference", target, "--transcript", ref_tx])
        if not unmeasurable(rc, out, "refused_path") or target.exists():
            why.append(f"target under ~/.claude: rc={rc} exists={target.exists()} last={last_line(out)!r}")
        # the checkout itself may live under ~/.claude (the laptop): ROOT stays writable, a sibling does not
        saved_root = GATE.ROOT
        GATE.ROOT = home / ".claude" / "skills" / "claude-power-pack"
        try:
            inside = GATE.ROOT / "vault" / "floor" / "reference.json"
            rc, out, _ = run_main(["--write-reference", inside, "--transcript", ref_tx])
            if rc != 0 or not inside.is_file():
                why.append(f"target under ROOT inside ~/.claude: rc={rc} last={last_line(out)!r}")
            rc, out, _ = run_main(["--write-reference", home / ".claude" / "projects" / "x.json", "--transcript", ref_tx])
            if not unmeasurable(rc, out, "refused_path"):
                why.append(f"sibling of ROOT under ~/.claude: rc={rc} last={last_line(out)!r}")
        finally:
            GATE.ROOT = saved_root
    return (not why), "; ".join(why) or "exists refused and bytes unchanged; --replace atomic; ~/.claude refused except under ROOT"


def g_no_model_call():
    root = scratch("nmc")
    ref_tx, now_tx = floor_pair(root, {}, {})
    ref_json = root / "ref.json"
    rc, out, _ = run_main(["--write-reference", ref_json, "--transcript", ref_tx])
    why = [] if rc == 0 else [f"setup rc={rc}"]
    syn = build_floor(root, "synthetic", {"usage": (0, 0, 0, 0)})
    syn.rows[-1]["message"]["model"] = "<synthetic>"
    syn_path = syn.write()
    target = root / "syn-ref.json"
    rc, out, _ = run_main(["--write-reference", target, "--transcript", syn_path])
    if not unmeasurable(rc, out, "no_model_call") or target.exists():
        why.append(f"write: rc={rc} last={last_line(out)!r} exists={target.exists()}")
    for extra, want_rc in (((), 2), (("--chars-only",), 0)):   # WR-03: no model call is exit 2 unless --chars-only
        rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", syn_path, *extra])
        tl = find_lines(out, "TOKENS ")
        if rc != want_rc or len(tl) != 1 or "status=no_model_call" not in tl[0]:
            why.append(f"check {extra}: rc={rc} tokens={tl}")
    noasst = build_floor(root, "noassistant", {})
    noasst.rows.pop()
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", noasst.write(), "--chars-only"])
    tl = find_lines(out, "TOKENS ")
    if rc != 0 or len(tl) != 1 or "status=no_model_call" not in tl[0]:
        why.append(f"no assistant row: rc={rc} tokens={tl}")
    return (not why), "; ".join(why) or "synthetic first call: write refused, check reports TOKENS no_model_call (exit 2; --chars-only exit 0)"


def g_no_secret():
    canary = "sk-ant-" + "A" * 50
    root = scratch("sec")

    def build(session):
        tx = Tx(root, None, session)
        home, wd = tx.home, tx.cwd
        tx.meta("last-prompt")
        tx.user("prompt carrying " + canary)
        tx.hook_success("SessionStart", "SessionStart:startup", "node hook.js --token " + canary, additional_context=canary)
        tx.instructions([
            (home / ".claude" / "CLAUDE.md", "User", "G" * 500 + canary),
            (wd / "CLAUDE.md", "Project", "P" * 500),
            (home / ".claude" / "rules" / (canary + ".md"), "User", "R" * 400),
        ])
        tx.skill_listing(listing_entries(1200, 10))
        tx.hook_context("SessionStart", "SessionStart:startup", ["H" * 100 + canary])
        tx.prompt_snapshot(["S" * 300 + canary])
        tx.attachment("session_context", context={"userEmail": "a@b.c", "gitStatus": "g" * 40 + canary})
        tx.assistant()
        return tx.write()

    ref_t, now_t = build("ref"), build("now")
    ref_json = root / "ref.json"
    why = []
    outputs = []
    rc, out, err = run_main(["--write-reference", ref_json, "--transcript", ref_t])
    outputs += [out, err]
    if rc != 0:
        return False, f"write rc={rc} {out[-200:]!r}"
    for extra in ([], ["--json"]):
        rc, out, err = run_main(["--check", "--reference", ref_json, "--transcript", now_t, *extra])
        outputs += [out, err]
        if rc != 0:
            why.append(f"check {extra} rc={rc} {out[-200:]!r}")
    ref_text = ref_json.read_text(encoding="utf-8")
    for label, text in (("stdout/stderr", "\n".join(outputs)), ("reference", ref_text)):
        if canary in text or "A" * 50 in text:
            why.append(f"canary found in {label}")
    keys = set(json.loads(ref_text).keys())
    if keys != REFERENCE_KEYS:
        why.append(f"reference keys {sorted(keys ^ REFERENCE_KEYS)}")
    if "[REDACTED" not in ref_text:
        why.append("control: the rules file name carrying the canary was not redacted in the reference")
    return (not why), "; ".join(why) or "canary in 7 places never leaves the process; reference keys exact; the rules path is [REDACTED]"


def g_read_only():
    if os.name == "nt":
        return "SKIP", "chmod a-w does not make a tree read-only on nt"
    root, ref_tx, now_tx, ref_json = good_ref("ro")

    def snapshot():
        snap = {}
        for dp, _, fns in os.walk(root):
            for fn in fns:
                f = Path(dp) / fn
                st = f.stat()
                snap[str(f.relative_to(root))] = (st.st_size, st.st_mtime_ns, sha256_file(f))
        return snap
    for dp, dns, fns in os.walk(root):
        for n in dns + fns:
            os.chmod(os.path.join(dp, n), 0o555 if os.path.isdir(os.path.join(dp, n)) else 0o444)
    before = snapshot()
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx])
    after = snapshot()
    return (rc == 0 and before == after and len(before) >= 3), f"rc={rc} files={len(before)} unchanged={before == after}"


def g_json():
    root, ref_tx, now_tx, ref_json = good_ref("js")
    why = []
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", now_tx, "--json"])
    doc = json.loads(out)
    if set(doc) != JSON_KEYS:
        why.append(f"keys differ: {sorted(set(doc) ^ JSON_KEYS)}")
    if doc.get("verdict") != "WITHIN_BOUND" or doc.get("exit") != 0 or rc != 0:
        why.append(f"verdict={doc.get('verdict')} exit={doc.get('exit')} rc={rc}")
    for k in ("rows", "findings", "explained", "caveats"):
        if not isinstance(doc.get(k), list):
            why.append(f"{k} is not a list")
    if not (doc.get("caveats") or []):
        why.append("caveats empty")
    if "window_sha256" not in (doc.get("provenance") or {}):
        why.append("provenance carries no window_sha256")
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", root / "absent.jsonl", "--json"])
    doc = json.loads(out)
    if set(doc) != JSON_KEYS or doc.get("verdict") != "UNMEASURABLE" or doc.get("exit") != 2 or doc.get("reason") != "no_transcript":
        why.append(f"unmeasurable doc: keys={sorted(doc)} verdict={doc.get('verdict')} reason={doc.get('reason')}")
    return (not why), "; ".join(why) or "one JSON document with the 15 keys (detail and probe_error since IN-02, cwd_admitted since WU1), for a verdict and for UNMEASURABLE"


def g_cli_usage():
    root, ref_tx, now_tx, ref_json = good_ref("cu")
    why = []
    for label, args in (("no source", ["--check", "--reference", ref_json]),
                        ("both modes", ["--check", "--write-reference", root / "x.json", "--transcript", now_tx]),
                        ("no mode", ["--transcript", now_tx]),
                        ("write without source", ["--write-reference", root / "y.json"])):
        rc, out, err = run_main(args)
        if rc != 2:
            why.append(f"{label}: rc={rc}")
    return (not why), "; ".join(why) or "usage errors exit 2"


# --------------------------------------------------------------------------- gates: sources (plan 04-03)
def home_env(root):
    """HOME / USERPROFILE at <root>/home for a subprocess (the owner's lookup globs ~/.claude/projects)."""
    return {"HOME": str(Path(root) / "home"), "USERPROFILE": str(Path(root) / "home")}


def g_sources_e2e():
    root = scratch("src")
    ref_tx, now_tx = floor_pair(root, {}, {"g": 11024})
    ref_json = root / "ref.json"
    env = home_env(root)
    rc, out, err = run_cli(["--write-reference", ref_json, "--transcript", ref_tx], env)
    if rc != 0:
        return False, f"setup write rc={rc} {out[-200:]!r}"
    os.utime(ref_tx, (1_000_000_000, 1_000_000_000))
    os.utime(now_tx, (1_000_000_100, 1_000_000_100))
    why = []
    rc, out, _ = run_cli(["--check", "--reference", ref_json, "--project-dir", ref_tx.parent], env)
    if rc != 1 or "SOURCE project_dir selected=now.jsonl candidates=2" not in out.splitlines():
        why.append(f"(a) rc={rc} source={find_lines(out, 'SOURCE ')}")
    elif not out.startswith("SOURCE ") or out.index("SOURCE ") > out.index("FLOOR "):
        why.append("(a) SOURCE is not printed before the FLOOR lines")
    os.utime(ref_tx, (1_000_000_200, 1_000_000_200))
    rc, out, _ = run_cli(["--check", "--reference", ref_json, "--project-dir", ref_tx.parent], env)
    if rc != 0 or "SOURCE project_dir selected=ref.jsonl candidates=2" not in out.splitlines():
        why.append(f"(b) rc={rc} source={find_lines(out, 'SOURCE ')}")
    rc, out, _ = run_cli(["--check", "--reference", ref_json, "--session", "ref"], env)
    if rc != 0 or "SOURCE session id=ref" not in out.splitlines():
        why.append(f"(c) rc={rc} source={find_lines(out, 'SOURCE ')}")
    rc, out, _ = run_cli(["--check", "--reference", ref_json, "--session", "now"], env)
    if rc != 1 or "SOURCE session id=now" not in out.splitlines():
        why.append(f"(c2) rc={rc} source={find_lines(out, 'SOURCE ')}")
    rc, out, _ = run_cli(["--check", "--reference", ref_json, "--json", "--session", "ref"], env)
    doc = json.loads(out)
    if (doc.get("provenance") or {}).get("source") != "session":
        why.append(f"(d) provenance.source={(doc.get('provenance') or {}).get('source')!r}")
    rc, out, _ = run_cli(["--check", "--reference", ref_json, "--transcript", ref_tx, "--project-dir", ref_tx.parent], env)
    if rc != 2:
        why.append(f"(e) two sources must be a usage error: rc={rc}")
    return (not why), "; ".join(why) or "project-dir picks the newest (now.jsonl red, then ref.jsonl green), --session ref green, now red"


def g_project_dir_newest():
    root = scratch("pdir")
    d = root / "proj"
    d.mkdir()
    files = {}
    for name, mt in (("a.jsonl", 1_000), ("b.jsonl", 3_000), ("c.jsonl", 2_000)):
        (d / name).write_text("{}\n", encoding="utf-8")
        os.utime(d / name, (mt, mt))
        files[name] = d / name
    (d / "nested").mkdir()
    (d / "nested" / "z.jsonl").write_text("{}\n", encoding="utf-8")
    os.utime(d / "nested" / "z.jsonl", (9_000, 9_000))
    (d / "newest.txt").write_text("x", encoding="utf-8")
    os.utime(d / "newest.txt", (9_500, 9_500))
    why = []
    picked, n = GATE.newest_transcript(d)
    if Path(picked).name != "b.jsonl" or n != 3:
        why.append(f"newest by mtime: {Path(picked).name} candidates={n} (want b.jsonl 3; nested and non-jsonl never count)")
    for name in files:
        os.utime(d / name, (5_000, 5_000))
    picked, n = GATE.newest_transcript(d)
    if Path(picked).name != "c.jsonl":
        why.append(f"tie broken by name: {Path(picked).name} (want c.jsonl)")
    empty = root / "empty"
    empty.mkdir()
    ref_root, ref_tx, now_tx, ref_json = good_ref("pdirref")
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--project-dir", empty])
    if not unmeasurable(rc, out, "no_transcript"):
        why.append(f"empty dir: rc={rc} last={last_line(out)!r}")
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--project-dir", root / "absent-dir"])
    if not unmeasurable(rc, out, "no_transcript"):
        why.append(f"absent dir: rc={rc} last={last_line(out)!r}")
    # through main: the newest of the pair is what gets measured
    os.utime(ref_tx, (1_000_000_000, 1_000_000_000))
    os.utime(now_tx, (1_000_000_500, 1_000_000_500))
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--project-dir", ref_tx.parent])
    if "SOURCE project_dir selected=now.jsonl candidates=2" not in out.splitlines():
        why.append(f"main picked {find_lines(out, 'SOURCE ')}")
    return (not why), "; ".join(why) or "newest by mtime, ties by name, nested / non-jsonl ignored, empty and absent dir -> no_transcript"


def g_session_unknown():
    root, ref_tx, now_tx, ref_json = good_ref("sunk")
    home = root / "home"
    import listing_floor_probe as lfp
    saved = lfp.time.sleep
    lfp.time.sleep = lambda *_a, **_k: None
    try:
        with with_home(home):
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--session", "no-such-session-0000"])
    finally:
        lfp.time.sleep = saved
    ok = unmeasurable(rc, out, "no_transcript") and lfp.time.sleep is saved
    return ok, f"rc={rc} last={last_line(out)!r}" if not ok else "an unknown session id -> exit 2 no_transcript (sleep patched, restored)"


def g_session_id_refused():
    root, ref_tx, now_tx, ref_json = good_ref("sref")
    import listing_floor_probe as lfp
    calls = []
    saved = lfp.transcript
    lfp.transcript = lambda sid: calls.append(sid) or None
    why = []
    try:
        for bad in ("../x", "a/b", "ab", "x" * 65, "a b", "*", "a" + "\x00" + "b", ""):
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--session", bad])
            if not unmeasurable(rc, out, "invalid_session_id"):
                why.append(f"{bad!r}: rc={rc} last={last_line(out)!r}")
    finally:
        lfp.transcript = saved
    if calls:
        why.append(f"the owner's lookup was reached for {calls}")
    return (not why), "; ".join(why) or "8 malformed ids -> exit 2 invalid_session_id before any glob"


# --------------------------------------------------------------------------- gates: --probe (stubs only)
STUB_BODY = """#!{python}
import json, os, re, sys, time, uuid
marker = os.environ.get("STUB_MARKER")
if marker:
    with open(marker, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(sys.argv) + "\\n")
cwd = os.getcwd()
sid = str(uuid.uuid4())
home = os.path.expanduser("~")
d = os.path.join(home, ".claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", cwd))
os.makedirs(d, exist_ok=True)
def row(n, **kw):
    kw["timestamp"] = "2026-10-04T10:00:%02d.000Z" % n
    kw["sessionId"] = sid
    return kw
def att(n, atype, **f):
    return row(n, type="attachment", cwd=cwd, attachment=dict(type=atype, **f))
rows = [
    row(1, type="user", cwd=cwd, isMeta=False, message={{"role": "user", "content": "Reply with the single word OK."}}),
    att(2, "instructions", files=[
        {{"path": os.path.join(home, ".claude", "CLAUDE.md"), "type": "User", "content": "G" * 10000}},
        {{"path": os.path.join(cwd, "CLAUDE.md"), "type": "Project", "content": "P" * 10000}}]),
    att(3, "skill_listing", content="- alpha: first skill\\n- beta: second skill\\n", names=["alpha", "beta"],
        skillCount=2, isInitial=True),
    att(4, "prompt_snapshot", systemPrompt=["S" * 800]),
    row(5, type="assistant", cwd=cwd, message={{"role": "assistant", "model": "claude-opus-5-5",
        "content": [{{"type": "text", "text": "OK"}}],
        "usage": {{"input_tokens": 2, "cache_creation_input_tokens": 30000, "cache_read_input_tokens": 0,
                  "output_tokens": 10}}}}),
]
with open(os.path.join(d, sid + ".jsonl"), "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\\n")
{tail}
"""
STUB_TAIL_OK = 'print(json.dumps({"session_id": sid, "total_cost_usd": 0.0, "num_turns": 1, "result": "OK"}))'
STUB_TAIL_NOSID = 'print(json.dumps({"total_cost_usd": 0.0, "num_turns": 1, "result": "OK"}))'


def write_stubs(root):
    """Stub executables under <root>/bin: good, bad-exit, no-session-id, and a non-executable copy of the good one."""
    root = Path(root)
    b = root / "bin"
    b.mkdir(parents=True, exist_ok=True)
    good = b / "claude-stub"
    good.write_text(STUB_BODY.format(python=sys.executable, tail=STUB_TAIL_OK), encoding="utf-8")
    good.chmod(0o755)
    bad = b / "claude-bad"
    bad.write_text(f"#!{sys.executable}\nimport sys\nsys.exit(3)\n", encoding="utf-8")
    bad.chmod(0o755)
    nosid = b / "claude-nosid"
    nosid.write_text(STUB_BODY.format(python=sys.executable, tail=STUB_TAIL_NOSID), encoding="utf-8")
    nosid.chmod(0o755)
    noexec = b / "claude-noexec"
    noexec.write_text(good.read_text(encoding="utf-8"), encoding="utf-8")
    noexec.chmod(0o644)
    return {"good": good, "bad": bad, "nosid": nosid, "noexec": noexec}


def probe_env(root, exe, extra=None):
    root = Path(root)
    env = {"CPP_CLAUDE_EXE": str(exe), "CPP_FLOOR_PROBE_RESULTS": str(root / "probe-results.jsonl"),
           "STUB_MARKER": str(root / "marker.jsonl"), **home_env(root)}
    env.update(extra or {})
    return env


@contextlib.contextmanager
def env_set(**kv):
    """os.environ keys set (or unset with None) for the block and restored after it."""
    saved = {k: os.environ.get(k) for k in kv}
    for k, v in kv.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def patched(obj, attr, value):
    saved = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, saved)


def probe_root(prefix):
    root = scratch(prefix)
    (root / "repo").mkdir()
    (root / "home").mkdir()
    return root, write_stubs(root)


TRACKED_RESULTS = REPO / "wiki" / "tools" / "listing_floor_probe.results.jsonl"


def tracked_results_sha() -> str:
    return sha256_file(TRACKED_RESULTS) if TRACKED_RESULTS.exists() else "absent"


def g_probe_stub():
    if os.name == "nt":
        return "SKIP", "a script cannot be the owner's argv[0] on nt"
    root, stubs = probe_root("pstub")
    env = probe_env(root, stubs["good"])
    before = tracked_results_sha()
    ref_json = root / "ref.json"
    rc, out, err = run_cli(["--write-reference", ref_json, "--probe", "--cwd", root / "repo"], env)
    why = []
    if rc != 0 or not ref_json.is_file():
        return False, f"write rc={rc} out={out[-300:]!r} err={err[-300:]!r}"
    marker = (root / "marker.jsonl").read_text(encoding="utf-8").splitlines()
    if len(marker) != 1:
        why.append(f"marker holds {len(marker)} argv lines after the write")
    else:
        argv = json.loads(marker[0])
        for want in ("-p", "Reply with the single word OK.", "--model"):
            if want not in argv:
                why.append(f"argv lacks {want!r}: {argv}")
    rows = [json.loads(ln) for ln in (root / "probe-results.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(rows) != 1 or not str(rows[0].get("label", "")).startswith("floor-gate-"):
        why.append(f"probe-results.jsonl rows={[r.get('label') for r in rows]}")
    if tracked_results_sha() != before:
        why.append("the tracked listing_floor_probe.results.jsonl changed")
    if not any(ln.startswith("SOURCE probe ") for ln in out.splitlines()) or not any(ln.startswith("PROBE exe=") for ln in out.splitlines()):
        why.append(f"no SOURCE probe / PROBE line: {out[:300]!r}")
    ref = json.loads(ref_json.read_text(encoding="utf-8"))
    prov = ref.get("provenance", {})
    if prov.get("source") != "probe" or not str((prov.get("probe") or {}).get("label", "")).startswith("floor-gate-"):
        why.append(f"reference provenance source={prov.get('source')!r} probe={prov.get('probe')!r}")
    if ref.get("total_chars") is None or (ref.get("tokens") or {}).get("first_call_total") != 30002:
        why.append(f"reference tokens={ref.get('tokens')}")
    rc, out, err = run_cli(["--check", "--reference", ref_json, "--probe", "--cwd", root / "repo"], env)
    if rc != 0 or not last_line(out).startswith("FLOOR verdict=WITHIN_BOUND"):
        why.append(f"check rc={rc} last={last_line(out)!r} err={err[-200:]!r}")
    marker = (root / "marker.jsonl").read_text(encoding="utf-8").splitlines()
    if len(marker) != 2:
        why.append(f"marker holds {len(marker)} lines after the check (want 2)")
    if tracked_results_sha() != before:
        why.append("the tracked results file changed after the check")
    return (not why), "; ".join(why) or "stub ran twice (marker 2), write+check green, results rebound to scratch, tracked results sha unchanged"


def g_probe_bad_exit():
    if os.name == "nt":
        return "SKIP", "a script cannot be the owner's argv[0] on nt"
    root, stubs = probe_root("pbad")
    target = root / "x.json"
    rc, out, err = run_cli(["--write-reference", target, "--probe", "--cwd", root / "repo"], probe_env(root, stubs["bad"]))
    ok = unmeasurable(rc, out, "probe_failed") and not target.exists() and "Traceback" not in err
    return ok, f"rc={rc} last={last_line(out)!r} exists={target.exists()} err={err[-200:]!r}" if not ok else "stub exit 3 with no output -> exit 2 probe_failed, nothing written"


def g_probe_not_executable():
    if os.name == "nt":
        return "SKIP", "file modes do not decide executability on nt"
    root, stubs = probe_root("pnx")
    target = root / "x.json"
    rc, out, err = run_cli(["--write-reference", target, "--probe", "--cwd", root / "repo"], probe_env(root, stubs["noexec"]))
    ok = unmeasurable(rc, out, "probe_failed") and not target.exists() and "Traceback" not in err and "PermissionError" in out
    return ok, f"rc={rc} out={out[-300:]!r} err={err[-200:]!r}" if not ok else "mode 0o644 stub -> exit 2 probe_failed (PermissionError named, no message)"


def g_probe_timeout():
    import listing_floor_probe as lfp
    root, stubs = probe_root("ptmo")
    ref_json = good_ref("ptref")[3]
    why = []
    args = ["--check", "--reference", ref_json, "--probe", "--cwd", root / "repo"]

    def raiser(*a, **k):
        raise subprocess.TimeoutExpired(a[0] if a else "claude", 900)

    def run_pole(label, patch_obj, patch_attr, patch_value):
        before = (lfp.CLAUDE, lfp.OUT, list(sys.argv))
        with env_set(CPP_CLAUDE_EXE=stubs["good"], CPP_FLOOR_PROBE_RESULTS=root / "r.jsonl", **home_env(root)):
            with patched(patch_obj, patch_attr, patch_value):
                rc, out, err = run_main(args)
        after = (lfp.CLAUDE, lfp.OUT, list(sys.argv))
        if not unmeasurable(rc, out, "probe_failed"):
            why.append(f"{label}: rc={rc} last={last_line(out)!r}")
        if "Traceback" in err or "Traceback" in out:
            why.append(f"{label}: traceback printed")
        if before != after:
            why.append(f"{label}: owner globals not restored {before} -> {after}")
        return out
    out = run_pole("timeout", lfp.subprocess, "run", raiser)
    if "TimeoutExpired" not in out:
        why.append(f"timeout: probe_error class not named: {out[-200:]!r}")

    def exits(*a, **k):
        raise SystemExit(2)
    run_pole("systemexit", lfp, "main", exits)

    def oserr(*a, **k):
        raise FileNotFoundError(2, "gone")
    run_pole("oserror", lfp.subprocess, "run", oserr)
    return (not why), "; ".join(why) or "TimeoutExpired / SystemExit / OSError -> exit 2 probe_failed, no traceback, lfp.CLAUDE / OUT / sys.argv restored"


def g_probe_no_exe():
    import listing_floor_probe as lfp
    root, stubs = probe_root("pnoexe")
    ref_json = good_ref("pnoref")[3]
    calls = []
    why = []
    with env_set(CPP_CLAUDE_EXE=None, **home_env(root)):
        with patched(lfp, "CLAUDE", str(root / "no-such-claude")), patched(shutil, "which", lambda *_a, **_k: None), \
                patched(lfp.subprocess, "run", lambda *a, **k: calls.append(a) or None):
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--probe", "--cwd", root / "repo"])
    if not unmeasurable(rc, out, "claude_exe_not_found"):
        why.append(f"unset exe: rc={rc} last={last_line(out)!r}")
    # an env path to a file that does not exist is the same refusal
    with env_set(CPP_CLAUDE_EXE=root / "bin" / "absent", **home_env(root)):
        with patched(lfp.subprocess, "run", lambda *a, **k: calls.append(a) or None):
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--probe", "--cwd", root / "repo"])
    if not unmeasurable(rc, out, "claude_exe_not_found"):
        why.append(f"absent env exe: rc={rc} last={last_line(out)!r}")
    if calls:
        why.append(f"subprocess.run reached {len(calls)} time(s)")
    return (not why), "; ".join(why) or "no executable (env unset / env path absent) -> exit 2 claude_exe_not_found, zero subprocess calls"


def g_probe_fence():
    import listing_floor_probe as lfp
    root, stubs = probe_root("pfence")
    ref_json = good_ref("pfref")[3]
    calls = []
    why = []
    with env_set(CPP_CLAUDE_EXE=sys.executable, **home_env(root)):
        with patched(lfp.subprocess, "run", lambda *a, **k: calls.append(a) or None):
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--probe", "--cwd", root / "repo"])
    if not unmeasurable(rc, out, "probe_fenced") or calls:
        why.append(f"outside the root: rc={rc} last={last_line(out)!r} calls={len(calls)}")
    with env_set(CPP_FLOOR_GATE_TEST_ROOT=None, CPP_CLAUDE_EXE=stubs["good"]):
        try:
            GATE.resolve_probe_exe(lfp)
            why.append("fence on with no root did not refuse")
        except GATE.Unmeasurable as exc:
            if exc.reason != "probe_fenced":
                why.append(f"fence without root: {exc.reason}")
    with env_set(CPP_CLAUDE_EXE=stubs["good"]):
        try:
            if str(GATE.resolve_probe_exe(lfp)) != str(stubs["good"]):
                why.append("the stub inside the root was not returned")
        except GATE.Unmeasurable as exc:
            why.append(f"stub inside the root refused: {exc.reason}")
    # the fence only restricts: unset, an executable outside the root is accepted (the production path)
    with env_set(CPP_FLOOR_GATE_TEST=None, CPP_CLAUDE_EXE=sys.executable):
        try:
            GATE.resolve_probe_exe(lfp)
        except GATE.Unmeasurable as exc:
            why.append(f"fence off still refused: {exc.reason}")
    return (not why), "; ".join(why) or "fence on: outside root and rootless refused before spawn, stub inside accepted; fence off changes nothing"


def g_probe_refusals():
    import listing_floor_probe as lfp
    root, stubs = probe_root("pref")
    ref_json = good_ref("prref")[3]
    calls = []
    why = []
    with env_set(CPP_CLAUDE_EXE=stubs["good"], **home_env(root)):
        with patched(lfp.subprocess, "run", lambda *a, **k: calls.append(a) or None):
            rc, out, _ = run_main(["--check", "--reference", ref_json, "--probe", "--cwd", root / "no-such-dir"])
    if not unmeasurable(rc, out, "probe_cwd_missing") or calls:
        why.append(f"missing cwd: rc={rc} last={last_line(out)!r} calls={len(calls)}")
    ref_tx = good_ref("prref2")[1]
    for flag, val in (("--transcript", ref_tx), ("--project-dir", Path(ref_tx).parent), ("--session", "abc-123")):
        rc, out, _ = run_main(["--check", "--reference", ref_json, flag, val, "--cwd", root / "repo"])
        if not unmeasurable(rc, out, "cwd_without_probe"):
            why.append(f"--cwd with {flag}: rc={rc} last={last_line(out)!r}")
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--probe", "--transcript", ref_tx])
    if rc != 2:
        why.append(f"--probe with --transcript must be a usage error: rc={rc}")
    if os.name != "nt":
        saved = lfp.time.sleep
        lfp.time.sleep = lambda *_a, **_k: None
        try:
            with env_set(CPP_CLAUDE_EXE=stubs["nosid"], CPP_FLOOR_PROBE_RESULTS=root / "r.jsonl", **home_env(root)):
                rc, out, _ = run_main(["--check", "--reference", ref_json, "--probe", "--cwd", root / "repo"])
        finally:
            lfp.time.sleep = saved
        if not unmeasurable(rc, out, "probe_failed"):
            why.append(f"no session_id: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "missing cwd, --cwd without --probe, --probe with another source, output without session_id -> refused"


def g_probe_view():
    why = []
    root = scratch("pview")
    path = build_floor(root, "real", {}).write()
    import listing_floor_probe as lfp
    owner = lfp.analyse(str(path), [])
    m = GATE.measure(str(path))
    if m["probe_view"] != {"startup_tokens": owner["startup_tokens"], "listing": owner["listing"]}:
        why.append(f"probe_view {m['probe_view']} != owner {owner}")
    if m["tokens"]["first_call_total"] != m["probe_view"]["startup_tokens"] or m["tokens"]["first_call_total"] != 30002:
        why.append(f"tokens {m['tokens']['first_call_total']} vs probe_view {m['probe_view']['startup_tokens']}")
    ref_json = root / "ref.json"
    rc, out, _ = run_main(["--write-reference", ref_json, "--transcript", path])
    rc, out, _ = run_main(["--check", "--reference", ref_json, "--transcript", path, "--json"])
    doc = json.loads(out)
    if (doc.get("provenance") or {}).get("probe_view") != m["probe_view"]:
        why.append(f"--json provenance.probe_view={(doc.get('provenance') or {}).get('probe_view')}")
    syn = build_floor(root, "synthetic", {"usage": (0, 0, 0, 0)})
    syn.rows[-1]["message"]["model"] = "<synthetic>"
    sm = GATE.measure(str(syn.write()))
    if sm["probe_view"]["startup_tokens"] != 0 or sm["tokens"]["status"] != "no_model_call":
        why.append(f"synthetic: probe_view={sm['probe_view']['startup_tokens']} tokens={sm['tokens']['status']}")
    return (not why), "; ".join(why) or "probe_view == the owner's analyse (real call 30002); synthetic: probe_view 0 while tokens no_model_call"


def g_no_real_session():
    root, stubs = probe_root("pnrs")
    why = []
    ref_json = good_ref("pnrref")[3]
    for label, extra in (("no exe env", {}), ("exe outside the root", {"CPP_CLAUDE_EXE": sys.executable})):
        try:
            run_cli(["--check", "--reference", ref_json, "--probe"], extra)
            why.append(f"run_cli accepted --probe with {label}")
        except AssertionError:
            pass
    try:
        rc, out, _ = run_cli(["--check", "--reference", ref_json, "--probe", "--cwd", root / "repo"],
                             {"CPP_CLAUDE_EXE": str(stubs["bad"]), **home_env(root)})
        if rc != 2:
            why.append(f"stub env: rc={rc}")
    except AssertionError as exc:
        why.append(f"run_cli refused a stub under the root: {exc}")
    env = cli_env({"CPP_FLOOR_GATE_TEST": "0", "CPP_FLOOR_GATE_TEST_ROOT": "/"})
    if env.get("CPP_FLOOR_GATE_TEST") != "1" or env.get("CPP_FLOOR_GATE_TEST_ROOT") != str(TMP_ROOT):
        why.append("cli_env lets a caller switch the fence off")
    if os.environ.get("CPP_FLOOR_GATE_TEST") != "1":
        why.append("the process-wide fence is off")
    try:
        with env_set(CPP_FLOOR_GATE_TEST=None):
            run_main(["--check", "--reference", ref_json, "--probe"])
        why.append("run_main accepted --probe with the fence off")
    except AssertionError:
        pass
    return (not why), "; ".join(why) or "run_cli / run_main refuse --probe without a stub under the scratch root; the fence cannot be switched off by a caller"


# --------------------------------------------------------------------------- gates: the real GEX44 floor (plan 04-03)
# Real transcripts are READ ONLY; every seeded variant is a scratch copy. Absolute paths: SKIP when absent.
REAL_A = Path("/home/kobii/.claude/projects/-home-kobii-missions-incremental-cognition--claude-worktrees-ic-run/"
              "607795c4-aa30-4fb8-886c-5b1e24a7a991.jsonl")      # interactive session, finished
REAL_B = Path("/home/kobii/.claude/projects/-home-kobii-missions-incremental-cognition/"
              "34f03871-4d33-4b7d-a52e-ec674b20a223.jsonl")      # mission worker: REAL_A's prompt plus one appended part
REAL_A7 = Path("/home/kobii/a7-env/home/.claude/projects/-home-kobii-kobii-a7/"
               "71e107ea-3171-4da7-b4bb-aedbc33d3f78.jsonl")     # first assistant row is <synthetic> "Login expired"
REF_GEX44 = REPO / "vault" / "programs" / "incremental-cognition" / "floor" / "reference-gex44.json"
REAL_B_SESSION = "34f03871-4d33-4b7d-a52e-ec674b20a223"
REAL_SESSION_ARG = [None]
if "--real-session" in sys.argv:
    REAL_SESSION_ARG[0] = sys.argv[sys.argv.index("--real-session") + 1]


def absent(*paths):
    gone = [str(p) for p in paths if not Path(p).is_file()]
    return f"UNMEASURABLE: not on this host: {', '.join(gone)}" if gone else None


def on_gex44() -> bool:
    return GATE.host_plane() == "gex44"


def layer_sum(m, layer):
    return sum(c["chars"] for c in m["components"] if c["layer"] == layer)


def layer_sources(m, layer):
    return [c for c in m["components"] if c["layer"] == layer]


def g_real_gex44():
    gone = absent(REAL_A)
    if gone:
        return "SKIP", gone
    m = GATE.measure(str(REAL_A))
    why = []

    def want(label, got, expected):
        if got != expected:
            why.append(f"{label}={got} want {expected}")
    want("memory_global", layer_sum(m, "memory_global"), 25037)
    want("memory_global scopes", {c["scope"] for c in layer_sources(m, "memory_global")}, {"universal"})
    want("memory_project", layer_sum(m, "memory_project"), 34478)
    want("memory_project scopes", {c["scope"] for c in layer_sources(m, "memory_project")}, {"project"})
    want("rules", layer_sum(m, "rules"), 63625)
    want("rules sources", len(layer_sources(m, "rules")), 23)
    want("rules scopes", {c["scope"] for c in layer_sources(m, "rules")}, {"universal"})
    want("skill_listing chars", m["skill_listing"]["chars"], 30000)
    want("skill_listing components", layer_sum(m, "skill_listing"), 30000)
    ss = "hook_context:SessionStart:SessionStart"
    want("SessionStart hook_context", layer_sum(m, ss), 7798)
    want("SessionStart sources", len(layer_sources(m, ss)), 2)
    if any(c["scope"] == "project" for c in layer_sources(m, ss)):
        why.append("SessionStart hook_context holds a project source")
    ups = "hook_context:UserPromptSubmit:UserPromptSubmit"
    want("UserPromptSubmit hook_context", layer_sum(m, ups), 2299)
    if any(c["scope"] == "project" for c in layer_sources(m, ups)):
        why.append("UserPromptSubmit hook_context holds a project source")
    sp = layer_sources(m, "system_prompt")
    want("system_prompt", sum(c["chars"] for c in sp), 9447)
    want("system_prompt parts", len(sp), 14)
    if not all(c["source"].startswith("part:") and c["scope"] == "unattributed" for c in sp):
        why.append("a system prompt part is not a digest-identified unattributed part")
    want("agent listing", layer_sum(m, "other:agent_listing_delta"), 27062)
    want("first call tokens", m["tokens"]["first_call_total"], 107351)
    want("tokens status", m["tokens"]["status"], "measured")
    want("probe_view startup_tokens", (m["probe_view"] or {}).get("startup_tokens"), 107351)
    prov = m["provenance"]
    want("install_home", prov["install_home"], "/home/kobii")
    want("cwd", prov["cwd"], "/home/kobii/missions/incremental-cognition")
    if on_gex44():
        want("plane", prov["plane"], "gex44")
    return (not why), "; ".join(why) or f"real GEX44 floor reproduced exactly: total={m['total_chars']} tokens=107351 window_rows={prov['window_rows']}"


def g_real_a7_no_call():
    gone = absent(REAL_A7)
    if gone:
        return "SKIP", gone
    m = GATE.measure(str(REAL_A7))
    why = []
    if m["tokens"]["status"] != "no_model_call":
        why.append(f"tokens.status={m['tokens']['status']}")
    if (m["probe_view"] or {}).get("startup_tokens") != 0:
        why.append(f"probe_view.startup_tokens={(m['probe_view'] or {}).get('startup_tokens')} (the owner reads a synthetic row as 0)")
    if m["skill_listing"]["chars"] != 30003:
        why.append(f"skill_listing chars={m['skill_listing']['chars']}")
    hs = [c for c in m["components"] if c["layer"].startswith("hook_system_message:SessionStart")]
    if sum(c["chars"] for c in hs) != 8332:
        why.append(f"hook_system_message chars={sum(c['chars'] for c in hs)}")
    if m["provenance"]["install_home"] != "/home/kobii/a7-env/home":
        why.append(f"install_home={m['provenance']['install_home']}")
    root = scratch("a7")
    target = root / "a7.json"
    rc, out, _ = run_cli(["--write-reference", target, "--transcript", REAL_A7])
    if not unmeasurable(rc, out, "no_model_call") or target.exists():
        why.append(f"write: rc={rc} last={last_line(out)!r} exists={target.exists()}")
    return (not why), "; ".join(why) or "login-expired session: tokens no_model_call, owner startup_tokens 0, no reference written (exit 2)"


def g_real_appended_prompt():
    if not on_gex44():
        return "SKIP", f"plane is {GATE.host_plane()!r}, not gex44"
    gone = absent(REAL_A, REAL_B)
    if gone:
        return "SKIP", gone
    root = scratch("appended")
    ref = root / "ref-a.json"
    rc, out, err = run_cli(["--write-reference", ref, "--transcript", REAL_A])
    if rc != 0:
        return False, f"write rc={rc} {out[-300:]!r}"
    rc, out, _ = run_cli(["--check", "--reference", ref, "--transcript", REAL_B])
    why = []
    rise = [ln for ln in out.splitlines() if ln.startswith("RISE system_prompt scope=unattributed delta=+4383")]
    if rc != 1 or len(rise) != 1 or "universal_1k" not in rise[0]:
        why.append(f"rc={rc} rise={rise} out={out[-500:]!r}")
    rc, out, _ = run_cli(["--check", "--reference", ref, "--transcript", REAL_B, "--json"])
    sd = json.loads(out).get("scope_deltas") or {}
    if sd.get("universal") != 0 or sd.get("project") != 0:
        why.append(f"scope_deltas={sd} (universal and project must be +0: the worker differs by the appended prompt only)")
    return (not why), "; ".join(why) or f"reference from the interactive session, check of the mission worker: {rise[0]}"


def copy_window(src, dest):
    """Rows of `src` through its first assistant row, parsed (a scratch copy; the source is only read)."""
    rows = []
    with open(src, "rb") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line.decode("utf-8", errors="replace"))
            rows.append(row)
            if isinstance(row, dict) and row.get("type") == "assistant":
                break
    return rows


def append_z(rows, kind, basename=None):
    """+1,024 'Z' on the instructions file of `kind` (and, for User, basename CLAUDE.md); a new Project entry when none."""
    for row in rows:
        a = row.get("attachment") if isinstance(row, dict) else None
        if not isinstance(a, dict) or a.get("type") != "instructions":
            continue
        for f in a.get("files") or []:
            if f.get("type") == kind and (basename is None or str(f.get("path", "")).replace("\\", "/").endswith("/" + basename)):
                f["content"] = (f.get("content") or "") + "Z" * 1024
                return True
    if kind == "Project":
        for row in rows:
            a = row.get("attachment") if isinstance(row, dict) else None
            if isinstance(a, dict) and a.get("type") == "instructions":
                cwd = row.get("cwd") or "/"
                a.setdefault("files", []).append({"path": str(cwd).rstrip("/") + "/CLAUDE.md", "type": "Project", "content": "Z" * 1024})
                return True
    return False


def g_seeded_real():
    src = REAL_A
    if REAL_SESSION_ARG[0]:
        import listing_floor_probe as lfp
        found = lfp.transcript(REAL_SESSION_ARG[0])
        if not found:
            return "SKIP", f"UNMEASURABLE: no transcript for --real-session {REAL_SESSION_ARG[0]}"
        src = Path(found)
    gone = absent(src)
    if gone:
        return "SKIP", gone
    root = scratch("seeded")
    pdir = root / "home" / ".claude" / "projects" / src.parent.name
    pdir.mkdir(parents=True)
    variants = {}
    for name, edit in (("a", None), ("b", ("User", "CLAUDE.md")), ("c", ("Project", None))):
        rows = copy_window(src, None)
        if edit and not append_z(rows, *edit):
            return False, f"variant {name}: no instructions entry of type {edit[0]} to extend"
        out = pdir / f"{name}00.jsonl"
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        variants[name] = out
    env = home_env(root)
    ref = root / "ref.json"
    rc, out, err = run_cli(["--write-reference", ref, "--transcript", variants["a"]], env)
    if rc != 0:
        return False, f"write rc={rc} {out[-300:]!r}"
    why = []
    rc, out, _ = run_cli(["--check", "--reference", ref, "--transcript", variants["a"]], env)
    if rc != 0:
        why.append(f"control (unchanged copy): rc={rc} last={last_line(out)!r}")
    rc, out, _ = run_cli(["--check", "--reference", ref, "--transcript", variants["b"]], env)
    rise = [ln for ln in out.splitlines() if ln.startswith("RISE memory_global scope=universal delta=+1024")]
    if rc != 1 or not rise:
        why.append(f"+1,024 in ~/.claude/CLAUDE.md: rc={rc} rise={rise} out={out[-400:]!r}")
    rc, out, _ = run_cli(["--check", "--reference", ref, "--transcript", variants["c"]], env)
    scope = [ln for ln in out.splitlines() if ln.startswith("SCOPE ")]
    if rc != 0 or not scope or "project=+1024" not in scope[0] or "universal=+0" not in scope[0]:
        why.append(f"+1,024 in the project CLAUDE.md: rc={rc} scope={scope}")
    return (not why), "; ".join(why) or f"real transcript {src.name[:8]}: +1,024 user CLAUDE.md RED (memory_global universal), same bytes in the project CLAUDE.md green (project +1024)"


def g_ref_gex44_green():
    if not on_gex44():
        return "SKIP", f"plane is {GATE.host_plane()!r}, not gex44"
    gone = absent(REAL_A)
    if gone:
        return "SKIP", gone
    if not REF_GEX44.is_file():
        return False, f"the committed reference is missing: {REF_GEX44}"
    # the interactive session's first prompt differs from the mission worker's, so the tokens axis is not comparable:
    # without --chars-only that is exit 2 (WR-03), with it WITHIN_BOUND_CHARS_ONLY
    rc, out, err = run_cli(["--check", "--reference", REF_GEX44, "--transcript", REAL_A])
    why = []
    if not unmeasurable(rc, out, "tokens_unmeasured") or find_lines(out, "RISE "):
        why.append(f"default: rc={rc} last={last_line(out)!r} rise={find_lines(out, 'RISE ')}")
    rc, out, err = run_cli(["--check", "--reference", REF_GEX44, "--transcript", REAL_A, "--chars-only"])
    if rc != 0 or not last_line(out).startswith("FLOOR verdict=WITHIN_BOUND_CHARS_ONLY exit=0") or len(find_lines(out, "CHARS_ONLY ")) != 1:
        why.append(f"--chars-only: rc={rc} last={last_line(out)!r} rise={find_lines(out, 'RISE ')}")
    rc, out, _ = run_cli(["--check", "--reference", REF_GEX44, "--transcript", REAL_A, "--chars-only", "--json"])
    doc = json.loads(out)
    sd = doc.get("scope_deltas") or {}
    if sd.get("universal") != 0 or sd.get("project") != 0 or doc.get("verdict") != "WITHIN_BOUND_CHARS_ONLY":
        why.append(f"scope_deltas={sd} verdict={doc.get('verdict')}")
    return (not why), "; ".join(why) or "today's interactive floor (607795c4) vs the plane-gex44 reference: tokens not comparable -> exit 2 tokens_unmeasured; --chars-only -> WITHIN_BOUND_CHARS_ONLY, universal +0, project +0"


def g_real_reference_pinned():
    """R2-W1 item 3: the committed reference's window pin is re-derived from the real transcript it was written from."""
    gone = absent(REAL_B)
    if gone:
        return "SKIP", gone
    if not REF_GEX44.is_file():
        return False, f"the committed reference is missing: {REF_GEX44}"
    ref = json.loads(REF_GEX44.read_text(encoding="utf-8"))
    prov = ref.get("provenance") or {}
    why = []
    if prov.get("plane") != "gex44" or prov.get("session_id") != REAL_B_SESSION or ref.get("explanations") != []:
        why.append(f"identity plane={prov.get('plane')!r} session={prov.get('session_id')!r} explanations={ref.get('explanations')!r}")
    if not (isinstance(prov.get("window_sha256"), str) and len(prov["window_sha256"]) == 64 and isinstance(prov.get("window_rows"), int)):
        return False, f"the reference provenance carries no window_sha256 / window_rows: {sorted(prov)}"
    _rows, _assistant, raw = GATE.read_window(str(REAL_B))
    sha, nrows = GATE.window_digest(raw)
    if sha != prov["window_sha256"]:
        why.append(f"window_sha256 re-read {sha[:12]} != committed {prov['window_sha256'][:12]}")
    if nrows != prov["window_rows"]:
        why.append(f"window_rows re-read {nrows} != committed {prov['window_rows']}")
    # positive control: another real window must NOT match, so this comparison can fail
    if Path(REAL_A).is_file():
        _r, _a, raw_a = GATE.read_window(str(REAL_A))
        if GATE.window_digest(raw_a)[0] == prov["window_sha256"]:
            why.append("control: a different real window produced the same digest")
    # the file ends with no later row's influence: the digest equals what a fresh measure() records
    if GATE.measure(str(REAL_B))["provenance"]["window_sha256"] != sha:
        why.append("measure() and window_digest disagree on the same transcript")
    return (not why), "; ".join(why) or f"committed reference window pinned to {REAL_B_SESSION[:8]}: sha256 {sha[:12]} rows={nrows} re-derived from disk"


# --------------------------------------------------------------------------- the [K] owner-bundle item
BUNDLE = REPO / "vault" / "programs" / "incremental-cognition" / "owner-bundle.md"
BUNDLE_GATE_PREFIX = "python tools/floor_regression_gate.py "
BUNDLE_TEST_PREFIX = "python tools/test_floor_regression_gate.py"


def build_test_parser():
    """The argument set of THIS test file. The module reads sys.argv directly at import (--gate-path, --real-session,
    --drill); this parser is the declared grammar the owner-bundle command lines are checked against."""
    ap = argparse.ArgumentParser(prog="test_floor_regression_gate.py", add_help=False)
    ap.add_argument("--drill", action="store_true")
    ap.add_argument("--gate-path", metavar="FILE")
    ap.add_argument("--real-session", metavar="SID")
    return ap


def _parse_quiet(parser, argv):
    """None if argv parses, else argparse's complaint (SystemExit is a failure, never an abort)."""
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            parser.parse_args(argv)
    except SystemExit:
        return err.getvalue().strip().splitlines()[-1] if err.getvalue().strip() else "argparse exited"
    return None


def bundle_section(text, header_prefix="## Phase 4"):
    """The lines of the section whose header starts with header_prefix, up to the next `## ` header; None if absent."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith(header_prefix):
            out = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("## "):
                    break
                out.append(nxt)
            return out
    return None


def bundle_argv_report(text):
    """(gate_lines, test_lines, problems): every command line of the Phase 4 section parsed by the owner's own parser."""
    section = bundle_section(text)
    if section is None:
        return 0, 0, ["no `## Phase 4` section"]
    problems, n_gate, n_test = [], 0, 0
    for raw in section:
        ln = raw.strip()
        if ln.startswith(BUNDLE_GATE_PREFIX):
            n_gate += 1
            if "<" in ln or ">" in ln:
                problems.append(f"placeholder / redirection token in: {ln}")
            why = _parse_quiet(GATE.build_parser(), ln[len(BUNDLE_GATE_PREFIX):].split())
            if why:
                problems.append(f"gate line does not parse ({why}): {ln}")
        elif ln == BUNDLE_TEST_PREFIX or ln.startswith(BUNDLE_TEST_PREFIX + " "):
            n_test += 1
            if "<" in ln or ">" in ln:
                problems.append(f"placeholder / redirection token in: {ln}")
            why = _parse_quiet(build_test_parser(), ln[len(BUNDLE_TEST_PREFIX):].split())
            if why:
                problems.append(f"test line does not parse ({why}): {ln}")
    return n_gate, n_test, problems


def g_bundle_argv_parses():
    """The [K] item's command lines are proven only to parse: each one goes through the tool's own argparse."""
    if not BUNDLE.is_file():
        return False, f"owner bundle missing: {BUNDLE}"
    n_gate, n_test, problems = bundle_argv_report(BUNDLE.read_text(encoding="utf-8"))
    # controls: the checker must be able to fail, and to pass
    bad = ("## Phase 4 -- x\n    python tools/floor_regression_gate.py --check --no-such-flag --transcript t.jsonl\n"
           "    python tools/test_floor_regression_gate.py --bogus\n"
           "    python tools/floor_regression_gate.py --check --transcript <t>\n")
    _g, _t, bad_problems = bundle_argv_report(bad)
    if len(bad_problems) != 3:
        problems.append(f"control: a bundle with an unknown gate flag, an unknown test flag and a placeholder raised {len(bad_problems)} problems, expected 3")
    good = ("## Phase 4 -- x\n    python tools/floor_regression_gate.py --check --session abc\n"
            "    python tools/test_floor_regression_gate.py --real-session abc\n")
    g2, t2, good_problems = bundle_argv_report(good)
    if good_problems or (g2, t2) != (1, 1):
        problems.append(f"control: a valid bundle read as gate={g2} test={t2} problems={good_problems}")
    if n_gate < 6 or n_test < 2:
        problems.append(f"the Phase 4 section holds {n_gate} gate lines and {n_test} test lines; needs at least 6 and 2")
    if len(re.findall(r"^- \*\*\[K\]\*\*", BUNDLE.read_text(encoding="utf-8"), flags=re.M)) != 1:
        problems.append("exactly one `- **[K]**` item is required")
    return (not problems), "; ".join(problems) or f"{n_gate} gate lines and {n_test} test lines of the Phase 4 [K] item parse with their own argparse (controls: bad bundle raises 3 problems, good bundle none)"


# --------------------------------------------------------------------------- gates: review fixes (phase 4 code review)
def cut_line(path, atype, keep=50):
    """Truncate to `keep` bytes the first transcript line whose attachment.type == atype (a copy cut mid-write)."""
    lines = Path(path).read_bytes().split(b"\n")
    for i, raw in enumerate(lines):
        if raw.strip() and (json.loads(raw).get("attachment") or {}).get("type") == atype:
            lines[i] = raw[:keep]
            break
    else:
        raise AssertionError(f"no {atype} line to cut")
    Path(path).write_bytes(b"\n".join(lines))
    return path


def legacy_read_window(path):
    """read_window before CR-01: a line that does not parse is kept in the digest and dropped from the rows."""
    rows, raw_lines, assistant, parsed = [], [], None, 0
    for line in open(path, "rb"):
        raw = line[:-1] if line.endswith(b"\n") else line
        if not raw.strip():
            continue
        try:
            row = json.loads(raw.decode("utf-8", errors="replace"))
        except ValueError:
            row = None
        if isinstance(row, dict):
            parsed += 1
            if row.get("type") == "assistant":
                assistant = row
                break
            rows.append(row)
        raw_lines.append(raw)
    if parsed == 0:
        raise GATE.Unmeasurable("unreadable", "no parseable JSON line")
    return rows, assistant, raw_lines


def g_window_line_unparseable():
    """CR-01: an unparseable line inside the startup window is UNMEASURABLE (exit 2), never a silently shorter floor."""
    why = []
    for cli in (True, False):
        tag = "cli" if cli else "in-process"
        run = run_cli if cli else run_main
        root = scratch("cr01")
        ref_tx, now_tx = floor_pair(root, {}, {})
        ref_json = root / "ref.json"
        rc, out, err = run(["--write-reference", ref_json, "--transcript", ref_tx])
        if rc != 0:
            return False, f"{tag} setup rc={rc} {out[-200:]!r}"
        # positive control: the intact check transcript is green
        rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", now_tx])
        if rc != 0 or "reason=within_bound" not in last_line(out):
            why.append(f"{tag} control: rc={rc} last={last_line(out)!r}")
        # the check transcript with its `instructions` line cut to 50 bytes
        cut = cut_line(build_floor(root, "cut", {}).write(), "instructions")
        rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", cut])
        if not unmeasurable(rc, out, "window_line_unparseable") or "1 " not in out:
            why.append(f"{tag} cut instructions: rc={rc} last={last_line(out)!r}")
        # a valid JSON line that is not an object is as unreadable as a truncated one
        scalar = build_floor(root, "scalar", {}).write()
        lines = scalar.read_bytes().split(b"\n")
        lines.insert(2, b"[1, 2, 3]")
        scalar.write_bytes(b"\n".join(lines))
        rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", scalar])
        if not unmeasurable(rc, out, "window_line_unparseable"):
            why.append(f"{tag} non-object line: rc={rc} last={last_line(out)!r}")
        # a reference is never written from a window with an unreadable line
        target = root / "cut-ref.json"
        rc, out, _ = run(["--write-reference", target, "--transcript", cut])
        if not unmeasurable(rc, out, "window_line_unparseable") or target.exists():
            why.append(f"{tag} write: rc={rc} last={last_line(out)!r} exists={target.exists()}")
        # control: damage AFTER the first assistant row is outside the window and does not matter
        late = build_floor(root, "late", {}).write()
        with open(late, "ab") as fh:
            fh.write(b'{"type": "attachment", "attachment": {"type": "ins\n')
        rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", late])
        if rc != 0 or "reason=within_bound" not in last_line(out):
            why.append(f"{tag} damage after the window: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "cut / non-object line in the window -> exit 2 window_line_unparseable (check and write, CLI and in-process); intact and after-window damage stay green"


def expect_hook_key(cmd, base=None):
    """The component source a hook command must be filed under (CR-02): hook:<sha256(command)[:16]> and, at most, the
    script basename. Computed here from the contract, never from the gate's own helper."""
    key = "hook:" + hashlib.sha256(cmd.encode("utf-8")).hexdigest()[:16]
    return key + (":" + base if base else "")


HOOK_KEY_RE = re.compile(r"^hook:[0-9a-f]{16}(:[A-Za-z0-9._-]{1,64})?$")


def hook_source_case(run, tag):
    """CR-02 through one runner (the real CLI or in-process); -> list of problems."""
    why = []
    root = scratch("cr02")
    secret_a, secret_b = "Sup3rS3cretValue12", "hunter2hunter2xx"
    cmd_u = f'DB_PASS={secret_b} node "{root}/home/.claude/hooks/u.js" --password={secret_a} --event=SessionStart'
    cmd_p = f'python3 {root}/repo/hooks/p.py --token \'{secret_a}Zq\''
    text = lambda ch, n: ch * n   # distinct filler per hook: identical text would be two producers of one element
    sizes = lambda a, b: {"hookrows": [(cmd_u, text("u", a)), (cmd_p, text("p", b))], "hook_name": "SessionStart"}
    write_settings(root / "home", {"SessionStart": [cmd_u]})
    write_settings(root / "repo", {"SessionStart": [cmd_p]})
    ref_tx, now_same = floor_pair(root, sizes(2000, 2000), sizes(2000, 2000))
    now_up = build_floor(root, "up", sizes(3024, 2000)).write()
    ref_json = root / "ref.json"
    rc, out, err = run(["--write-reference", ref_json, "--transcript", ref_tx])
    if rc != 0:
        return [f"{tag} write rc={rc} {out[-200:]!r}"]
    raw = ref_json.read_text(encoding="utf-8")
    for needle in (secret_a, secret_b, "--password", "DB_PASS", "--token", "--event=SessionStart", cmd_u, cmd_p):
        if needle in raw:
            why.append(f"{tag}: reference holds hook command text {needle[:24]!r}")
    doc = json.loads(raw)
    layer = "hook_context:SessionStart:SessionStart"
    srcs = sorted(c["source"] for c in doc["components"] if c["layer"] == layer)
    want = sorted([expect_hook_key(cmd_u, "u.js"), expect_hook_key(cmd_p, "p.py")])
    if srcs != want:
        why.append(f"{tag}: hook sources {srcs} want {want}")
    if not all(HOOK_KEY_RE.match(x) for x in srcs):
        why.append(f"{tag}: hook source outside the key grammar: {srcs}")
    # matching survives the key: the same floor is green, +1024 in the user-registered hook is red, universal
    rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", now_same])
    if rc != 0 or "reason=within_bound" not in last_line(out):
        why.append(f"{tag}: same floor: rc={rc} last={last_line(out)!r}")
    rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", now_up])
    risk = find_lines(out, f"RISE {layer} scope=universal")
    if rc != 1 or len(risk) != 1:
        why.append(f"{tag}: +1024 user hook: rc={rc} rise={risk} last={last_line(out)!r}")
    rc, jout, _ = run(["--check", "--reference", ref_json, "--transcript", now_up, "--json"])
    for needle in (secret_a, secret_b, "--password", cmd_u):
        if needle in jout or needle in out:
            why.append(f"{tag}: check output holds hook command text {needle[:24]!r}")
    # control: a command whose hash differs is another source (matching is on the key, so this can go red)
    other = build_floor(root, "other", {"hookrows": [(cmd_u + " --x", text("u", 2000)), (cmd_p, text("p", 2000))],
                                        "hook_name": "SessionStart"}).write()
    rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", other])
    if rc != 1 or not find_lines(out, f"RISE {layer} "):
        why.append(f"{tag}: control, command changed: rc={rc} last={last_line(out)!r}")
    return why


def g_hook_source_no_command_text():
    """CR-02: the component source of a hook is a stable key; no hook command text reaches a written reference."""
    why = hook_source_case(run_cli, "cli") + hook_source_case(run_main, "in-process")
    return (not why), "; ".join(why) or "reference + check output carry hook:<sha256[:16]>[:basename] only (no argument, no env assignment, no secret); same floor green, +1024 user hook red (universal); CLI and in-process"


def drop_instruction_row(path):
    """Remove the whole `instructions` attachment row from a transcript (a resumed or wrong session)."""
    out = []
    for raw in Path(path).read_bytes().split(b"\n"):
        if raw.strip() and (json.loads(raw).get("attachment") or {}).get("type") == "instructions":
            continue
        out.append(raw)
    Path(path).write_bytes(b"\n".join(out))
    return path


def g_layer_absent():
    """WR-01: a reference layer of >= 1,000 chars that is wholly absent from the check is UNMEASURABLE, not a fall."""
    why = []
    for cli in (True, False):
        tag = "cli" if cli else "in-process"
        run = run_cli if cli else run_main

        def case(label, ref_sizes, edit, want):
            root = scratch("wr01")
            ref_tx, now_tx = floor_pair(root, ref_sizes, {})
            ref_json = root / "ref.json"
            rc, out, _ = run(["--write-reference", ref_json, "--transcript", ref_tx])
            if rc != 0:
                why.append(f"{tag} {label}: setup rc={rc}")
                return
            edit(now_tx)
            rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", now_tx])
            if want is None:
                if rc != 0 or "reason=within_bound" not in last_line(out):
                    why.append(f"{tag} {label}: want within_bound, rc={rc} last={last_line(out)!r}")
            elif not unmeasurable(rc, out, f"layer_absent:{want}"):
                why.append(f"{tag} {label}: rc={rc} last={last_line(out)!r} want reason=layer_absent:{want}")
            return out

        # the reviewer's repro: the instructions attachment is gone altogether (a resumed / wrong session)
        out = case("instructions row gone", {"g": 100000}, drop_instruction_row, "memory_global")
        if out is not None and "memory_project" not in out:
            why.append(f"{tag} instructions row gone: detail does not name every absent layer: {out[-300:]!r}")
        case("user CLAUDE.md gone", {}, _drop_user_claude, "memory_global")
        # controls: the layer is still there (shrunk to nothing much) -> a fall, green
        case("layer shrunk, still present", {"g": 100000},
             lambda p: _set_user_claude(p, "G"), None)
        # boundary: 1,000 chars absent -> refused; 999 -> green; a small layer vanishing is not a reason to refuse
        case("rules 1000 chars gone", {"r": 1000}, lambda p: _drop_rules(p), "rules")
        case("rules 999 chars gone", {"r": 999}, lambda p: _drop_rules(p), None)
    return (not why), "; ".join(why) or "a >= 1,000-char reference layer wholly absent -> exit 2 layer_absent:<layer> (names every absent layer); shrunk layer, 999-char layer absent -> green; CLI and in-process"


def _edit_files(path, fn):
    out = []
    for raw in Path(path).read_bytes().split(b"\n"):
        if raw.strip():
            row = json.loads(raw)
            att = row.get("attachment") or {}
            if att.get("type") == "instructions":
                att["files"] = fn(att["files"])
                raw = json.dumps(row, ensure_ascii=False).encode("utf-8")
        out.append(raw)
    Path(path).write_bytes(b"\n".join(out))


def _is_user_claude(f) -> bool:
    # separators normalised like _drop_rules: on Windows the fixture path ends "\.claude\CLAUDE.md"
    return f["type"] == "User" and f["path"].replace("\\", "/").endswith("/CLAUDE.md")


def _drop_user_claude(path):
    _edit_files(path, lambda fs: [f for f in fs if not _is_user_claude(f)])


def _set_user_claude(path, text):
    def edit(fs):
        for f in fs:
            if _is_user_claude(f):
                f["content"] = text
        return fs
    _edit_files(path, edit)


def _drop_rules(path):
    _edit_files(path, lambda fs: [f for f in fs if "/.claude/rules/" not in f["path"].replace("\\", "/")])


def legacy_uncorrelated_scope(event, ctx):
    """The pre-WR-02 fallback: an element no hook_success row produced was filed by who registers its event."""
    if not ctx.available:
        return "unattributed", "not_on_this_host"
    proj, user = ctx.project_regs(), ctx.user_regs()
    if proj is None or user is None:
        return "unattributed", "unknown_settings"
    in_proj, in_user = bool(proj.get(event)), bool(user.get(event))
    if in_proj and in_user:
        return "unattributed", "ambiguous"
    return ("project", "event_fallback") if in_proj else ("universal", "event_fallback")


def g_hook_uncorrelated_unattributed():
    """WR-02: a hook element with no producing row is `unattributed` (never project on the event alone); plain-text stdout correlates."""
    why = []
    layer = "hook_context:SessionStart:SessionStart"
    src = "event:SessionStart"
    P, U = "node project.js", "node user.js"
    for cli in (True, False):
        tag = "cli" if cli else "in-process"
        # the reviewer's repro: project settings register the event, user settings nothing, 1,200 chars, no producer row
        rc, out, _ = attr_check({"hook": 1, "hook_name": "SessionStart"}, {"hook": 1200, "hook_name": "SessionStart"}, project_regs={"SessionStart": [P]}, cli=cli)
        risk = find_lines(out, f"RISE {layer} scope=unattributed")
        if rc != 1 or len(risk) != 1 or "universal_1k" not in risk[0] or find_lines(out, f"LAYER {layer} scope=project"):
            why.append(f"{tag} project-only +1199: rc={rc} rise={risk} last={last_line(out)!r}")
    # every registration shape files an uncorrelated element as unattributed
    for label, user, proj in (("user only", {"SessionStart": [U]}, None), ("project only", None, {"SessionStart": [P]}),
                              ("both", {"SessionStart": [U]}, {"SessionStart": [P]}), ("neither", None, None)):
        root = scratch("wr02")
        if user is not None:
            write_settings(root / "home", user)
        if proj is not None:
            write_settings(root / "repo", proj)
        got = comp(measure_floor(root, {"hook_name": "SessionStart"}), layer, src)
        if got != ("unattributed", "event_uncorrelated"):
            why.append(f"{label}: {got} want ('unattributed', 'event_uncorrelated')")
    # a hook that prints plain text is correlated by its stdout (so it is attributed, not left uncorrelated)
    root = scratch("wr02")
    write_settings(root / "home", {"SessionStart": [U]})
    write_settings(root / "repo", {"SessionStart": [P]})
    tx = build_floor(root, "plain", {"hook": 1200, "hook_name": "SessionStart"})
    asst = tx.rows.pop()
    tx.attachment("hook_success", hookEvent="SessionStart", hookName="SessionStart", command=P, stdout="H" * 1200 + "\n",
                  content="ok", toolUseID="tu1", exitCode=0)
    tx.rows.append(asst)
    got = comp(GATE_MEASURE_HOME(root, tx.write()), layer, hook_src(P))
    if got != ("project", "project_settings"):
        why.append(f"plain-text stdout: {got} want ('project', 'project_settings')")
    return (not why), "; ".join(why) or "uncorrelated element: unattributed for user-only / project-only / both / neither, project-only +1199 red (universal_1k); plain-text stdout correlates"


def GATE_MEASURE_HOME(root, path):
    with with_home(Path(root) / "home"):
        return GATE.measure(str(path))


def g_tokens_unmeasured():
    """WR-03: an unmeasured / non-comparable tokens axis is never plain WITHIN_BOUND: exit 2 unless --chars-only says so."""
    why = []
    for cli in (True, False):
        tag = "cli" if cli else "in-process"
        run = run_cli if cli else run_main
        root = scratch("wr03")
        ref_tx, _ = floor_pair(root, {}, {})
        ref_json = root / "ref.json"
        rc, out, _ = run(["--write-reference", ref_json, "--transcript", ref_tx])
        if rc != 0:
            return False, f"{tag} setup rc={rc}"
        syn = build_floor(root, "synthetic", {"usage": (0, 0, 0, 0)})
        syn.rows[-1]["message"]["model"] = "<synthetic>"
        variants = {
            "not_comparable": build_floor(root, "other-prompt", {"prompt": "A different prompt entirely."}).write(),
            "no_model_call": syn.write(),
        }
        for status, path in variants.items():
            rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", path])
            if not unmeasurable(rc, out, "tokens_unmeasured") or status not in out:
                why.append(f"{tag} {status} default: rc={rc} last={last_line(out)!r}")
            if "FLOOR verdict=WITHIN_BOUND " in out:
                why.append(f"{tag} {status} default still prints a plain WITHIN_BOUND")
            rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", path, "--chars-only"])
            note = find_lines(out, "CHARS_ONLY ")
            if (rc != 0 or not last_line(out).startswith("FLOOR verdict=WITHIN_BOUND_CHARS_ONLY exit=0 reason=within_bound_chars_only")
                    or len(note) != 1 or "not compared" not in note[0] or status not in note[0]):
                why.append(f"{tag} {status} --chars-only: rc={rc} note={note} last={last_line(out)!r}")
            rc, jout, _ = run(["--check", "--reference", ref_json, "--transcript", path, "--chars-only", "--json"])
            try:
                doc = json.loads(jout)
            except ValueError:
                why.append(f"{tag} {status} --json: not JSON (rc={rc}) {jout[-120:]!r}")
                continue
            if doc["verdict"] != "WITHIN_BOUND_CHARS_ONLY" or doc["exit"] != 0 or doc["tokens_axis"]["status"] != status:
                why.append(f"{tag} {status} --json: {doc['verdict']} {doc['exit']} {doc['tokens_axis']['status']}")
        # a material chars rise is still red with tokens unmeasured, with or without the flag
        bad = build_floor(root, "rise", {"prompt": "A different prompt entirely.", "g": 11500}).write()
        for extra in ((), ("--chars-only",)):
            rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", bad, *extra])
            if rc != 1 or not find_lines(out, "RISE memory_global scope=universal"):
                why.append(f"{tag} rise with tokens unmeasured {extra}: rc={rc} last={last_line(out)!r}")
        # controls: a measured, comparable tokens axis is plain WITHIN_BOUND, and --chars-only does not loosen it
        same = build_floor(root, "same", {}).write()
        for extra in ((), ("--chars-only",)):
            rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", same, *extra])
            if rc != 0 or not last_line(out).startswith("FLOOR verdict=WITHIN_BOUND exit=0") or find_lines(out, "CHARS_ONLY "):
                why.append(f"{tag} control measured {extra}: rc={rc} last={last_line(out)!r}")
        up = build_floor(root, "tok-up", {"usage": (2, 30998, 0, 10)}).write()
        rc, out, _ = run(["--check", "--reference", ref_json, "--transcript", up, "--chars-only"])
        if rc != 1 or not find_lines(out, "RISE tokens scope=unattributed"):
            why.append(f"{tag} measured tokens +3.3% with --chars-only: rc={rc} last={last_line(out)!r}")
        # --chars-only belongs to --check only
        rc, out, _ = run(["--write-reference", root / "w.json", "--transcript", ref_tx, "--chars-only"])
        if not unmeasurable(rc, out, "chars_only_without_check") or (root / "w.json").exists():
            why.append(f"{tag} --write-reference --chars-only: rc={rc} last={last_line(out)!r}")
    return (not why), "; ".join(why) or "tokens not_comparable / no_model_call: exit 2 tokens_unmeasured; --chars-only -> WITHIN_BOUND_CHARS_ONLY exit 0 with a CHARS_ONLY note; rises and a measured tokens axis stay enforced; CLI and in-process"


def g_replace_failure_no_stray_tmp():
    """IN-01: a failed --replace write leaves no `<target>.tmp<pid>` behind (the reference directory is committed)."""
    why = []
    for cli in (True, False):
        tag = "cli" if cli else "in-process"
        run = run_cli if cli else run_main
        root = scratch("in01")
        ref_tx, _ = floor_pair(root, {}, {})
        # os.replace(tmp, <a directory>) fails for real: the failure comes after the temp file was written
        target = root / "out" / "ref.json"
        target.mkdir(parents=True)
        rc, out, _ = run(["--write-reference", target, "--transcript", ref_tx, "--replace"])
        stray = sorted(p.name for p in target.parent.iterdir() if p.name != "ref.json")
        if not unmeasurable(rc, out, "write_failed") or stray:
            why.append(f"{tag} failed replace: rc={rc} last={last_line(out)!r} stray={stray}")
        if not target.is_dir():
            why.append(f"{tag} the target directory is gone")
        # control: a successful --replace leaves exactly the target
        good = root / "good" / "ref.json"
        rc, out, _ = run(["--write-reference", good, "--transcript", ref_tx])
        rc2, out2, _ = run(["--write-reference", good, "--transcript", ref_tx, "--replace"])
        left = sorted(p.name for p in good.parent.iterdir())
        if rc != 0 or rc2 != 0 or left != ["ref.json"]:
            why.append(f"{tag} control: rc={rc}/{rc2} left={left}")
    return (not why), "; ".join(why) or "failed --replace: exit 2 write_failed and no temp file left; successful --replace leaves only the target; CLI and in-process"


def g_json_detail_and_probe_note():
    """IN-02: --json carries `detail` / `probe_error` on exit 2, and the probe's tracked results file is named in the docs."""
    why = []
    root = scratch("in02")
    ref_tx, _ = floor_pair(root, {}, {})
    rc, out, _ = run_cli(["--check", "--reference", root / "absent.json", "--transcript", ref_tx, "--json"])
    doc = json.loads(out)
    if rc != 2 or doc.get("reason") != "reference_missing" or doc.get("detail") != "no such reference file" or "probe_error" not in doc:
        why.append(f"reference_missing --json: rc={rc} reason={doc.get('reason')!r} detail={doc.get('detail')!r} keys={sorted(doc)}")
    text_rc, text_out, _ = run_cli(["--check", "--reference", root / "absent.json", "--transcript", ref_tx])
    if "no such reference file" not in text_out or str(doc.get("detail")) not in text_out:
        why.append(f"text mode no longer names the detail: {text_out[-200:]!r}")
    if os.name != "nt":
        proot, stubs = probe_root("in02")
        rc, out, _ = run_cli(["--write-reference", proot / "x.json", "--probe", "--cwd", proot / "repo", "--json"],
                             probe_env(proot, stubs["noexec"]))
        doc = json.loads(out)
        if rc != 2 or doc.get("reason") != "probe_failed" or doc.get("probe_error") != "PermissionError" or not doc.get("detail"):
            why.append(f"probe_failed --json: rc={rc} reason={doc.get('reason')!r} probe_error={doc.get('probe_error')!r} detail={doc.get('detail')!r}")
    # success paths carry the two keys too, empty (the schema does not depend on the verdict)
    rc, out, _ = run_cli(["--write-reference", root / "w.json", "--transcript", ref_tx, "--json"])
    doc = json.loads(out)
    if rc != 0 or "detail" not in doc or doc.get("probe_error") is not None:
        why.append(f"written --json: rc={rc} detail={'detail' in doc} probe_error={doc.get('probe_error')!r}")
    # the documentation names the tracked file a --probe appends to
    rc, helptext, _ = run_cli(["--help"])
    flat = " ".join(helptext.split())
    if "listing_floor_probe.results.jsonl" not in flat or "CPP_FLOOR_PROBE_RESULTS" not in flat:
        why.append("--help does not name the tracked results file / CPP_FLOOR_PROBE_RESULTS")
    if "listing_floor_probe.results.jsonl" not in (GATE.__doc__ or ""):
        why.append("the module docstring does not name the tracked results file")
    return (not why), "; ".join(why) or "--json carries detail / probe_error on exit 2 (and null/empty on success); --help and the docstring name wiki/tools/listing_floor_probe.results.jsonl"


GATES_REVIEWFIX = [
    ("V-FLOOR-JSON-DETAIL-AND-PROBE-NOTE", g_json_detail_and_probe_note),
    ("V-FLOOR-REPLACE-FAILURE-NO-STRAY-TMP", g_replace_failure_no_stray_tmp),
    ("V-FLOOR-TOKENS-UNMEASURED", g_tokens_unmeasured),
    ("V-FLOOR-HOOK-UNCORRELATED-UNATTRIBUTED", g_hook_uncorrelated_unattributed),
    ("V-FLOOR-LAYER-ABSENT", g_layer_absent),
    ("V-FLOOR-HOOK-SOURCE-NO-COMMAND-TEXT", g_hook_source_no_command_text),
    ("V-FLOOR-WINDOW-LINE-UNPARSEABLE", g_window_line_unparseable),
]


# --------------------------------------------------------------------------- run
GATES_TRACER = [
    ("V-FLOOR-TRACER-E2E", g_tracer_e2e),
    ("V-FLOOR-WINDOW-APPEND-STABLE", g_window_append_stable),
    ("V-FLOOR-HOOK-CORRELATED", g_hook_correlated),
    ("V-FLOOR-EXPLANATION-IS-DEBT", g_explanation_is_debt),
    ("V-FLOOR-WINDOW-DEGRADED", g_window_degraded),
]
GATES_RULES = [
    ("V-FLOOR-LAYER-TABLE", g_layer_table),
    ("V-FLOOR-POSITIVE-UNIVERSAL", g_positive_universal),
    ("V-FLOOR-PROJECT-LOCAL", g_project_local),
    ("V-FLOOR-SCOPE-REPORT", g_scope_report),
    ("V-FLOOR-PROJECT-3PCT", g_project_3pct),
    ("V-FLOOR-BOUNDARY", g_boundary),
    ("V-FLOOR-TOTAL-3PCT", g_total_3pct),
    ("V-FLOOR-SYSTEM-PROMPT-NEW-PART", g_system_prompt_new_part),
    ("V-FLOOR-HARNESS-NOT-1K", g_harness_not_1k),
    ("V-FLOOR-UNATTRIBUTED-1K", g_unattributed_1k),
    ("V-FLOOR-FALL-RATCHET-HINT", g_fall_ratchet_hint),
    ("V-FLOOR-EXPLAINED-GREEN", g_explained_green),
    ("V-FLOOR-EXPLANATION-BOUND", g_explanation_bound),
    ("V-FLOOR-EXPLANATION-EMPTY-REASON", g_explanation_empty_reason),
    ("V-FLOOR-EXPLANATION-FIELDS", g_explanation_fields),
    ("V-FLOOR-TOKENS-RULE", g_tokens_rule),
]
GATES_ATTRIBUTION = [
    ("V-FLOOR-HOOK-SYSTEM-MESSAGE", g_hook_system_message),
    ("V-FLOOR-HOOK-PLUGIN", g_hook_plugin),
    ("V-FLOOR-HOOK-EVENT-FALLBACK", g_hook_event_fallback),
    ("V-FLOOR-HOOK-AMBIGUOUS", g_hook_ambiguous),
    ("V-FLOOR-SETTINGS-UNREADABLE", g_settings_unreadable),
    ("V-FLOOR-EXEC-FORM-REGISTRATION", g_exec_form_registration),
    ("V-FLOOR-CWD-ABSENT-UNATTRIBUTED", g_cwd_absent_unattributed),
    ("V-FLOOR-SKILL-PROJECT", g_skill_project),
    ("V-FLOOR-SKILL-UNIVERSAL", g_skill_universal),
    ("V-FLOOR-SKILL-NAMESPACE", g_skill_namespace),
    ("V-FLOOR-SKILL-BUILTIN-UNATTRIBUTED", g_skill_builtin_unattributed),
    ("V-FLOOR-LISTING-SPLIT-EXACT", g_listing_split_exact),
    ("V-FLOOR-AGENT-SCOPE", g_agent_scope),
    ("V-FLOOR-RELABEL-NO-RISE", g_relabel_no_rise),
]
GATES_SAFETY = [
    ("V-FLOOR-UNMEASURABLE-TABLE", g_unmeasurable_table),
    ("V-FLOOR-NOT-COMPARABLE", g_not_comparable),
    ("V-FLOOR-ADMIT-CWD", g_admit_cwd),
    ("V-FLOOR-WRITE-SAFETY", g_write_safety),
    ("V-FLOOR-NO-MODEL-CALL", g_no_model_call),
    ("V-FLOOR-NO-SECRET", g_no_secret),
    ("V-FLOOR-READ-ONLY", g_read_only),
    ("V-FLOOR-JSON", g_json),
    ("V-FLOOR-CLI-USAGE", g_cli_usage),
]
GATES_SOURCES = [
    ("V-FLOOR-SOURCES-E2E", g_sources_e2e),
    ("V-FLOOR-PROJECT-DIR-NEWEST", g_project_dir_newest),
    ("V-FLOOR-SESSION-UNKNOWN", g_session_unknown),
    ("V-FLOOR-SESSION-ID-REFUSED", g_session_id_refused),
    ("V-FLOOR-PROBE-STUB", g_probe_stub),
    ("V-FLOOR-PROBE-BAD-EXIT", g_probe_bad_exit),
    ("V-FLOOR-PROBE-NOT-EXECUTABLE", g_probe_not_executable),
    ("V-FLOOR-PROBE-TIMEOUT", g_probe_timeout),
    ("V-FLOOR-PROBE-NO-EXE", g_probe_no_exe),
    ("V-FLOOR-PROBE-FENCE", g_probe_fence),
    ("V-FLOOR-PROBE-REFUSALS", g_probe_refusals),
    ("V-FLOOR-PROBE-VIEW", g_probe_view),
    ("V-FLOOR-NO-REAL-SESSION", g_no_real_session),
    ("V-FLOOR-REAL-GEX44", g_real_gex44),
    ("V-FLOOR-REAL-A7-NO-CALL", g_real_a7_no_call),
    ("V-FLOOR-REAL-APPENDED-PROMPT", g_real_appended_prompt),
    ("V-FLOOR-SEEDED-REAL", g_seeded_real),
    ("V-FLOOR-REF-GEX44-GREEN", g_ref_gex44_green),
    ("V-FLOOR-REAL-REFERENCE-PINNED", g_real_reference_pinned),
    ("V-FLOOR-BUNDLE-ARGV-PARSES", g_bundle_argv_parses),
]
GATES = GATES_TRACER + GATES_RULES + GATES_ATTRIBUTION + GATES_SAFETY + GATES_SOURCES + GATES_REVIEWFIX


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


# --------------------------------------------------------------------------- mutation drill
GATE_FN = dict(GATES)
SUBPROCESS_ONLY = ("V-FLOOR-TRACER-E2E", "V-FLOOR-SOURCES-E2E", "V-FLOOR-PROBE-STUB", "V-FLOOR-PROBE-BAD-EXIT",
                   "V-FLOOR-PROBE-NOT-EXECUTABLE", "V-FLOOR-NO-REAL-SESSION", "V-FLOOR-REAL-A7-NO-CALL",
                   "V-FLOOR-REAL-APPENDED-PROMPT", "V-FLOOR-SEEDED-REAL", "V-FLOOR-REF-GEX44-GREEN")   # real subprocesses: a monkeypatch cannot reach them
DRILL_GATES = [n for n, _ in GATES if n not in SUBPROCESS_ONLY]


QUIET_SKIPPED: list = []


def _quiet(names) -> dict:
    """Run the named gates with printing off; {gate: passed} for the ones that ran to PASS/FAIL (QUIET_SKIPPED holds
    the ones that SKIPped: a host without the real transcripts)."""
    start = len(RESULTS)
    QUIET[0] = True
    try:
        for n in names:
            run_gate(n, GATE_FN[n])
    finally:
        QUIET[0] = False
    QUIET_SKIPPED[:] = [g for st, g, _ in RESULTS[start:] if st in ("SKIP", "INCONCLUSIVE")]
    return {g: st == "PASS" for st, g, _ in RESULTS[start:] if st in ("PASS", "FAIL")}


def _patch(attr, replacement):
    """Replace GATE.<attr>; returns the restore callable."""
    original = getattr(GATE, attr)
    setattr(GATE, attr, replacement)
    return lambda: setattr(GATE, attr, original)


def _m_scope_universal():
    return _patch("scope_key", lambda component: "universal")


def _m_scope_project():
    return _patch("scope_key", lambda component: "project")


def _m_universal_threshold_off():
    return _patch("UNIVERSAL_MIN_CHARS", 10 ** 9)


def _m_validate_always_ok():
    return _patch("validate_explanations", lambda items: None)


def _m_covering_ignores_bound_and_unit():
    return _patch("covering_explanation",
                  lambda finding, items: next((e for e in items if e.get("layer") == finding["layer"]), None))


def _m_no_layer_3pct():
    real = GATE.is_material
    return _patch("is_material", lambda row, ref_total: [r for r in real(row, ref_total) if r != "layer_3pct"])


def _m_exit_unmeasurable_zero():
    real = GATE.exit_code
    return _patch("exit_code", lambda verdict: 0 if verdict == "UNMEASURABLE" else real(verdict))


def _m_system_prompt_harness():
    return _patch("scope_for_system_prompt_part", lambda part_text: "harness")


def _m_correlate_empty():
    return _patch("correlate_hook", lambda element, event, field, window_rows: set())


def _m_skill_never_project():
    real = GATE.scope_for_name

    def fake(kind, name, ctx):
        scope, basis = real(kind, name, ctx)
        return ("unattributed" if scope == "project" else scope), basis
    return _patch("scope_for_name", fake)


def _m_host_has_always():
    return _patch("host_has", lambda path: True)


def _m_newest_oldest():
    def oldest(directory):
        d = Path(directory)
        cands = sorted((p for p in d.glob("*.jsonl") if p.is_file()), key=lambda p: (p.stat().st_mtime_ns, p.name))
        if not cands:
            raise GATE.Unmeasurable("no_transcript", "no *.jsonl directly in the directory")
        return cands[0], len(cands)
    return _patch("newest_transcript", oldest)


def _m_window_drop_unparseable():
    return _patch("read_window", legacy_read_window)


def _m_hook_source_raw_command():
    return _patch("hook_source_key", lambda cmd: cmd)


def _m_absent_layers_none():
    return _patch("absent_layers", lambda ref, now: [])


def _m_event_fallback_project():
    return _patch("uncorrelated_scope", legacy_uncorrelated_scope)


def _m_tokens_gap_green():
    return _patch("unmeasured_tokens_verdict", lambda axis, chars_only: ("WITHIN_BOUND", "within_bound", ""))


def _m_synthetic_measured():
    real = GATE.first_call_tokens
    return _patch("first_call_tokens", lambda assistant: real(assistant) if real(assistant) is not None
                  else (0 if assistant is not None else None))


MUTANTS = [
    ("M1 scope_key returns universal (the scope split is dropped)", _m_scope_universal,
     ["V-FLOOR-PROJECT-LOCAL", "V-FLOOR-SCOPE-REPORT"]),
    ("M2 scope_key returns project", _m_scope_project, ["V-FLOOR-POSITIVE-UNIVERSAL"]),
    ("M3 UNIVERSAL_MIN_CHARS = 10**9 (the 1,000-char rule is off)", _m_universal_threshold_off,
     ["V-FLOOR-POSITIVE-UNIVERSAL", "V-FLOOR-BOUNDARY"]),
    ("M4 validate_explanations accepts everything", _m_validate_always_ok, ["V-FLOOR-EXPLANATION-EMPTY-REASON"]),
    ("M5 covering_explanation ignores delta_bound and unit", _m_covering_ignores_bound_and_unit,
     ["V-FLOOR-EXPLANATION-BOUND"]),
    ("M6 exit_code maps UNMEASURABLE to 0 (a comparison that could not be made reads green)", _m_exit_unmeasurable_zero,
     ["V-FLOOR-UNMEASURABLE-TABLE"]),
    ("M7 is_material never returns layer_3pct", _m_no_layer_3pct, ["V-FLOOR-PROJECT-3PCT"]),
    ("M8 scope_for_system_prompt_part returns harness (type-based harness for system prompt parts)",
     _m_system_prompt_harness, ["V-FLOOR-SYSTEM-PROMPT-NEW-PART"]),
    ("M9 correlate_hook returns no producing command (every hook element falls back to its event)", _m_correlate_empty,
     ["V-FLOOR-HOOK-CORRELATED"]),
    ("M10 scope_for_name never returns project (a project skill or agent reads as unattributed)", _m_skill_never_project,
     ["V-FLOOR-SKILL-PROJECT"]),
    ("M11 host_has treats an absent cwd as available (a foreign transcript is attributed from this host)",
     _m_host_has_always, ["V-FLOOR-CWD-ABSENT-UNATTRIBUTED"]),
    ("M12 newest_transcript returns the OLDEST session (the project dir source measures a stale floor)",
     _m_newest_oldest, ["V-FLOOR-PROJECT-DIR-NEWEST"]),
    ("M13 first_call_tokens accepts a <synthetic> first call as measured (a login-expired session writes a reference)",
     _m_synthetic_measured, ["V-FLOOR-NO-MODEL-CALL"]),
    ("M14 read_window drops an unparseable window line silently (CR-01: a truncated floor reads WITHIN_BOUND)",
     _m_window_drop_unparseable, ["V-FLOOR-WINDOW-LINE-UNPARSEABLE"]),
    ("M15 hook_source_key stores the raw hook command as the component source (CR-02: argument text reaches the reference)",
     _m_hook_source_raw_command, ["V-FLOOR-HOOK-SOURCE-NO-COMMAND-TEXT"]),
    ("M16 absent_layers finds nothing (WR-01: a floor that lost a whole layer reads as a fall, WITHIN_BOUND)",
     _m_absent_layers_none, ["V-FLOOR-LAYER-ABSENT"]),
    ("M17 uncorrelated hook element filed by its event's registrations (WR-02: a plugin hook reads as project)",
     _m_event_fallback_project, ["V-FLOOR-HOOK-UNCORRELATED-UNATTRIBUTED", "V-FLOOR-HOOK-EVENT-FALLBACK"]),
    ("M18 unmeasured_tokens_verdict returns plain WITHIN_BOUND (WR-03: a tokens axis nobody compared reads green)",
     _m_tokens_gap_green, ["V-FLOOR-TOKENS-UNMEASURED", "V-FLOOR-NO-MODEL-CALL", "V-FLOOR-TOKENS-RULE"]),
]


def run_drill() -> int:
    """Control first (all in-process gates green), each mutant applied and restored, then an unmutated rerun."""
    if GATE is None:
        print(f"FAIL DRILL-CONTROL gate does not load: {GATE_LOAD_ERROR}")
        return 1
    before = sha256_file(GATE_FILE)
    control = _quiet(DRILL_GATES)
    control_skipped = len(QUIET_SKIPPED)
    control_ok = len(control) + control_skipped == len(DRILL_GATES) and all(control.values()) and len(control) > 0
    print(f"{'PASS' if control_ok else 'FAIL'} DRILL-CONTROL unmutated run: {sum(control.values())}/{len(control)} gates green"
          f" (skipped {control_skipped})")
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
    clean = len(after) + len(QUIET_SKIPPED) == len(DRILL_GATES) and all(after.values()) and len(after) > 0
    print(f"{'PASS' if clean else 'FAIL'} DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: {sum(after.values())}/{len(after)} gates green"
          f" (skipped {len(QUIET_SKIPPED)})")
    restored = sha256_file(GATE_FILE) == before
    print(f"{'PASS' if restored else 'FAIL'} DRILL-RESTORE gate file sha256 {before[:16]} before == after")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean and restored) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
