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


def explain(layer, scope=None, unit="chars", bound=1100, reason="seeded", commit="abcdef1"):
    e = {"layer": layer, "unit": unit, "delta_bound": bound, "reason": reason, "commit": commit}
    if scope is not None:
        e["scope"] = scope
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
        ("hook_context:SessionStart:SessionStart:startup", "unattributed"): 33,
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
             "layer empty": explain("", "universal")}
    for label, item in cases.items():
        rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations([item]))
        if rc != 2 or "reason=explanation_refused" not in last_line(out):
            why.append(f"{label}: rc={rc} last={last_line(out)!r}")
    # one bad entry refuses the whole reference even when another entry would cover the rise
    rc, out, _ = pair_check({}, {"g": 11024}, ref_edit=set_explanations(
        [explain("memory_global", "universal"), explain("rules", "universal", reason="")]))
    if rc != 2:
        why.append(f"one bad entry among good: rc={rc}")
    return (not why), "; ".join(why) or "five malformed entries and a mixed list each refuse the reference (exit 2)"


def g_tokens_rule():
    why = []
    rc, out, _ = pair_check({}, {"usage": (2, 30998, 0, 10)})
    risk = find_lines(out, "RISE tokens scope=unattributed")
    if rc != 1 or len(risk) != 1 or "unit=tokens" not in risk[0] or "rules=tokens_3pct" not in risk[0]:
        why.append(f"+3.3% tokens: rc={rc} rise={risk}")
    rc, out, _ = pair_check({}, {"usage": (2, 30998, 0, 10), "prompt": "A different prompt entirely."})
    tl = find_lines(out, "TOKENS ")
    if rc != 0 or len(tl) != 1 or "status=not_comparable" not in tl[0]:
        why.append(f"different prompt: rc={rc} tokens={tl}")
    rc, out, _ = pair_check({}, {"usage": (2, 30998, 0, 10)},
                            ref_edit=set_explanations([explain("tokens", unit="tokens", bound=1000)]))
    if rc != 0 or not find_lines(out, "EXPLAINED tokens scope=unattributed delta=+998"):
        why.append(f"explained tokens: rc={rc} last={last_line(out)!r}")
    rc, out, _ = pair_check({}, {"usage": (2, 30500, 0, 10)})
    if rc != 0:
        why.append(f"+1.6% tokens must stay green: rc={rc}")
    return (not why), "; ".join(why) or "tokens: +3.3% red, different prompt not_comparable, explained green, +1.6% green"


# --------------------------------------------------------------------------- run
GATES_TRACER = [
    ("V-FLOOR-TRACER-E2E", g_tracer_e2e),
    ("V-FLOOR-WINDOW-APPEND-STABLE", g_window_append_stable),
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
GATES = GATES_TRACER + GATES_RULES


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
DRILL_GATES = [n for n, _ in GATES if n != "V-FLOOR-TRACER-E2E"]    # the tracer is a real subprocess: a monkeypatch cannot reach it


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


def _m_system_prompt_harness():
    return _patch("scope_for_system_prompt_part", lambda part_text: "harness")


MUTANTS = [
    ("M1 scope_key returns universal (the scope split is dropped)", _m_scope_universal,
     ["V-FLOOR-PROJECT-LOCAL", "V-FLOOR-SCOPE-REPORT"]),
    ("M2 scope_key returns project", _m_scope_project, ["V-FLOOR-POSITIVE-UNIVERSAL"]),
    ("M3 UNIVERSAL_MIN_CHARS = 10**9 (the 1,000-char rule is off)", _m_universal_threshold_off,
     ["V-FLOOR-POSITIVE-UNIVERSAL", "V-FLOOR-BOUNDARY"]),
    ("M4 validate_explanations accepts everything", _m_validate_always_ok, ["V-FLOOR-EXPLANATION-EMPTY-REASON"]),
    ("M5 covering_explanation ignores delta_bound and unit", _m_covering_ignores_bound_and_unit,
     ["V-FLOOR-EXPLANATION-BOUND"]),
    ("M7 is_material never returns layer_3pct", _m_no_layer_3pct, ["V-FLOOR-PROJECT-3PCT"]),
    ("M8 scope_for_system_prompt_part returns harness (type-based harness for system prompt parts)",
     _m_system_prompt_harness, ["V-FLOOR-SYSTEM-PROMPT-NEW-PART"]),
]


def run_drill() -> int:
    """Control first (all in-process gates green), each mutant applied and restored, then an unmutated rerun."""
    if GATE is None:
        print(f"FAIL DRILL-CONTROL gate does not load: {GATE_LOAD_ERROR}")
        return 1
    before = sha256_file(GATE_FILE)
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
    restored = sha256_file(GATE_FILE) == before
    print(f"{'PASS' if restored else 'FAIL'} DRILL-RESTORE gate file sha256 {before[:16]} before == after")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean and restored) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
