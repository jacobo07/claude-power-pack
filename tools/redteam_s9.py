#!/usr/bin/env python3
"""S9 red team (flow-compression Phase 8, plan 08-02): the 15 Owner claims, each attacked on the real subject.

Every claim ends in exactly one verdict of the closed set HELD / BREACH / UNMEASURED. There is no PASS. HELD means the
attack failed on the real code or evidence AND a guard-removed positive control showed the same attack succeeding; the
judge demotes a HELD whose control did not fire to UNMEASURED(control_did_not_fire). The host is read-only: ledger rows
come only through flow_replay.read_prefix over the 07 pin, and an open-mode probe turns any write to the ledger, the
Owner queue, the settings or the mission records into exit 3. Mutating attacks run on temp copies; patches of real module
behaviour are attribute scopes restored in a finally.

    python3 tools/redteam_s9.py run --pin <07-PIN.json> --claims all|1,2,.. --json <out.json> --md <out.md>
"""
from __future__ import annotations

import argparse
import ast
import builtins
import contextlib
import datetime
import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT))

SCHEMA = "redteam-s9/1"
HELD, BREACH, UNMEASURED = "HELD", "BREACH", "UNMEASURED"
VERDICTS = (HELD, BREACH, UNMEASURED)
PLANES = ("GEX44-host-readonly", "GEX44-temp-copy", "seeded", "repo-artefact", "LAPTOP-ONLY-not-observed")
MISSION_BASE = "7edba723"
LANDED = "043bb2b4"          # the commit at which phases 1-7 landed; the diff range below is fixed so the report reproduces
PHASE7 = ".planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger"
C15_REASON = "claim text absent; OWNER DECISION NEEDED"

CLAIMS = {
    1: "The context hypothesis was correlation, not cause.",
    2: "Rotation increases rehydration cost more than compaction.",
    3: "Preflight merely moves waits earlier without reducing span.",
    4: "Auto-normalized ROADMAP changes semantics.",
    5: "Immutable packets become stale too quickly.",
    6: "Admission reservation causes deadlocks or resource hoarding.",
    7: "Auto-renew allows runaway cost.",
    8: "The semantic progress signal can be gamed by noisy commits or tests.",
    9: "Night readiness asks too many Owner questions.",
    10: "The terminal reconciler creates false DONE.",
    11: "Blocked work stealing violates dependency or workspace ownership.",
    12: "Historical replay is biased by missing telemetry.",
    13: "The efficiency compiler optimizes aggregate mission-hours rather than the actual critical path.",
    14: "GSD X policy leaked into GSD Core.",
    15: "(claim text absent from the repo)",
}
# sub-attacks are declared before any of them run; essential ones decide whether a claim can be HELD at all
SUBATTACKS = {
    1: ["causal-wording", "causal-effect"],
    2: ["rehydration-cost"],
    3: ["span-effect"],
    4: ["writer-sweep", "packet-normaliser"],
    5: ["packet-staleness"],
    6: ["primitive-sweep", "hoarding", "deadlock"],
    7: ["renew-loop"],
    8: ["noise-cases"],
    9: ["decisions-sweep", "production-frequency"],
    10: ["crafted-receipts", "host-evidence"],
    11: ["no-stealing-code", "predicate"],
    12: ["missing-telemetry"],
    13: ["subject", "objective-sweep", "seeded-serialization"],
    14: ["branch-diff", "host-core"],
    15: ["claim-text-search"],
}
NON_ESSENTIAL = {"host-evidence", "production-frequency"}      # declared before the run; they never decide a verdict alone


# --------------------------------------------------------------------------------------------------- judging
def result(name, verdict, plane, evidence=None, *, control_fired=None, negative_quiet=None, reason=None, command=""):
    return {"name": name, "verdict": verdict, "plane": plane, "evidence": evidence or {}, "control_fired": control_fired,
            "negative_control_quiet": negative_quiet, "reason": reason, "command": command}


def judge(subs: list[dict]) -> dict:
    """The claim verdict: HELD needs a fired control (else UNMEASURED); worst of the sub-verdicts; closed set only."""
    out, final = [], HELD
    rank = {HELD: 0, UNMEASURED: 1, BREACH: 2}
    if not subs:
        return {"verdict": UNMEASURED, "reason": "no_sub_attacks", "subs": []}
    for s in subs:
        v = s.get("verdict")
        if v not in VERDICTS:
            raise ValueError(f"verdict {v!r} is outside the closed set {VERDICTS}")
        if s.get("plane") not in PLANES:
            raise ValueError(f"plane {s.get('plane')!r} is not one of {PLANES}")
        s = dict(s)
        if v == HELD and s.get("control_fired") is not True:
            s["verdict"], s["reason"] = UNMEASURED, "control_did_not_fire"
        if s["verdict"] == UNMEASURED and not s.get("reason"):
            s["reason"] = "unspecified"
        out.append(s)
    # a non-essential sub-attack that is UNMEASURED does not drag the claim; a BREACH from any sub-attack always counts
    decisive = [s for s in out if s["name"] not in NON_ESSENTIAL or s["verdict"] == BREACH]
    for s in decisive or out:
        if rank[s["verdict"]] > rank[final]:
            final = s["verdict"]
    reasons = sorted({f"{s['name']}:{s['reason']}" for s in decisive if s["verdict"] == UNMEASURED and s.get("reason")})
    return {"verdict": final, "reason": "; ".join(reasons) if final == UNMEASURED else None, "subs": out}


# --------------------------------------------------------------------------------------------------- read-only probe
class WriteProbe:
    """Records every open / mutate call whose target sits under `roots` with a write, append or create intent."""

    def __init__(self, roots):
        self.roots = [os.path.realpath(str(r)) for r in roots]
        self.writes: list[str] = []
        self.opens = 0

    def _under(self, p) -> bool:
        try:
            rp = os.path.realpath(os.fspath(p))
        except (TypeError, ValueError):
            return False
        return any(rp == r or rp.startswith(r + os.sep) for r in self.roots)

    def __enter__(self):
        self._saved = {}
        probe = self

        def wrap_open(real):
            def inner(file, mode="r", *a, **k):
                probe.opens += 1
                if isinstance(file, (str, bytes, os.PathLike)) and probe._under(file) and \
                        any(c in str(mode) for c in "wax+"):
                    probe.writes.append(f"open({os.path.basename(os.fspath(file))!r},{mode!r})")
                return real(file, mode, *a, **k)
            return inner

        def wrap_osopen(real):
            def inner(path, flags, *a, **k):
                probe.opens += 1
                if probe._under(path) and flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC):
                    probe.writes.append(f"os.open({os.path.basename(os.fspath(path))!r})")
                return real(path, flags, *a, **k)
            return inner

        def wrap_path(name, real):
            def inner(*args, **k):
                if args and isinstance(args[0], (str, bytes, os.PathLike)) and probe._under(args[0]):
                    probe.writes.append(f"os.{name}({os.path.basename(os.fspath(args[0]))!r})")
                return real(*args, **k)
            return inner

        for obj, name, maker in ((builtins, "open", wrap_open), (io, "open", wrap_open), (os, "open", wrap_osopen)):
            self._saved[(obj, name)] = getattr(obj, name)
            setattr(obj, name, maker(getattr(obj, name)))
        for name in ("remove", "unlink", "rename", "replace", "mkdir", "makedirs", "rmdir", "truncate", "utime"):
            if hasattr(os, name):
                self._saved[(os, name)] = getattr(os, name)
                setattr(os, name, wrap_path(name, getattr(os, name)))
        return self

    def __exit__(self, *exc):
        for (obj, name), real in self._saved.items():
            setattr(obj, name, real)


def host_roots(pn: dict) -> list[str]:
    home = Path.home() / ".claude"
    return [pn["ledger"], pn["missions_dir"], str(home / "settings.json"), str(home / "settings.local.json")]


# --------------------------------------------------------------------------------------------------- helpers
def sha256(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*args, cwd=ROOT) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:160]}")
    return r.stdout


@contextlib.contextmanager
def attr_patch(module, name, value):
    """Install `value` as module.name for the block and put the original object back in a finally."""
    original = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, original)


@contextlib.contextmanager
def temp_root(prefix="s9rt-"):
    d = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def scrub(obj, tmp_roots=()):
    """Temp paths -> basenames, recursively (STATE incident class 8: a temp path in a stored result is nondeterminism)."""
    if isinstance(obj, dict):
        return {k: scrub(v, tmp_roots) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [scrub(v, tmp_roots) for v in obj]
    if isinstance(obj, str):
        return re.sub(r"(/tmp|/var/tmp)/[^\s'\",)]*", lambda m: os.path.basename(m.group(0).rstrip("/")) or "tmp",
                      obj)
    return obj


class Ctx:
    """What an attack may read: the verified pin, its rows and records (host read-only), and the repo root."""

    def __init__(self, pin_path):
        import flow_replay as fr
        self.fr = fr
        self.pin_path = Path(pin_path)
        self.pin = fr.load_pin(self.pin_path)
        self.rows, self.torn = fr.read_prefix(self.pin)          # Inconclusive when the pin does not verify
        self.records, self.drift = fr.read_records(self.pin)
        self.root = ROOT
        self._cache: dict = {}

    def cached(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]


def _tools_py() -> list[Path]:
    """Mission code a sweep reads: tools/*.py and modules/**/*.py, never tests and never this harness."""
    out = [p for p in sorted((ROOT / "tools").glob("*.py")) if not p.name.startswith("test_") and p.name != "redteam_s9.py"]
    out += [p for p in sorted((ROOT / "modules").rglob("*.py")) if "test" not in p.name]
    return out


# --------------------------------------------------------------------------------------------------- claim 14
_CORE_SWITCHES_EXTRA = ("arm_preflight", "blocker_compiler", "mission_reconcile", "foreseeable_decisions",
                        "progress_fingerprint")
MUTATE_VERBS = ("config-set", "config.set", "config-new-project", "phase.add", "phase.remove", "phase.complete",
                "phase.insert", "phase add", "phase remove", "phase complete", "roadmap.update", "roadmap update",
                "roadmap.set", "state.set", "state.update", "state update", "workstream.create", "workstream.set",
                "workstream create", "milestone.complete", "milestone complete")
_SPAWN = {"run", "Popen", "check_output", "check_call", "call", "_run", "run_cmd"}


def diff_gsd_core(base: str, head: str, cwd=ROOT) -> list[str]:
    """Paths changed between two commits that sit under a gsd-core directory."""
    names = git("diff", "--name-only", f"{base}..{head}", cwd=cwd).splitlines()
    return sorted(n for n in names if re.search(r"(^|/)gsd-core(/|$)", n))


def classify_gsd_tools_calls(text: str) -> list[dict]:
    """Per function that names gsd-tools AND reaches a process-spawning call: read or mutate by its string constants."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        consts = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        names = [n.id for n in ast.walk(fn) if isinstance(n, ast.Name)]
        if not (any("gsd-tools" in c for c in consts) or any(n == "GSD_TOOLS" for n in names)):
            continue
        spawns = any(isinstance(n, ast.Call) and (getattr(n.func, "attr", None) in _SPAWN
                                                  or getattr(n.func, "id", None) in _SPAWN) for n in ast.walk(fn))
        if not spawns:
            continue
        joined = " ".join(consts)
        mutate = sorted(v for v in MUTATE_VERBS if v in joined)
        out.append({"function": fn.name, "class": "mutate" if mutate else "read", "verbs": mutate})
    return out


def sweep_core_text(files: dict[str, str], needles: list[str]) -> list[str]:
    return sorted(p for p, t in files.items() if any(n in t for n in needles))


def _core_needles() -> list[str]:
    import flow_replay as fr
    return sorted(set(fr.SWITCHES) | set(fr.HELD) | set(_CORE_SWITCHES_EXTRA))


def attack_14(ctx) -> list[dict]:
    subs = []
    # --- branch-diff
    cmd = f"git diff --name-only {MISSION_BASE}..{LANDED} ; git diff --name-only {LANDED}..HEAD"
    landed = git("diff", "--name-only", f"{MISSION_BASE}..{LANDED}").splitlines()
    core_paths = diff_gsd_core(MISSION_BASE, LANDED) + diff_gsd_core(LANDED, "HEAD")
    sites = []
    for n in landed:
        if n.startswith(".planning") or n.startswith("docs/") or "/test_" in n or n.startswith("tools/test_"):
            continue
        p = ROOT / n
        if p.is_file() and p.suffix == ".py":
            for c in classify_gsd_tools_calls(p.read_text(encoding="utf-8", errors="replace")):
                sites.append({"file": n, **c})
    mutating = [s for s in sites if s["class"] == "mutate"]
    with temp_root() as td:                                        # positive controls, each driven through the same functions
        git_ok = ["git", "-c", "user.email=a@b", "-c", "user.name=a"]
        subprocess.run([*git_ok, "init", "-q", str(td)], check=True, capture_output=True)
        (td / "a.txt").write_text("a", encoding="utf-8")
        subprocess.run([*git_ok, "-C", str(td), "add", "."], check=True, capture_output=True)
        subprocess.run([*git_ok, "-C", str(td), "commit", "-qm", "base"], check=True, capture_output=True)
        base = git("rev-parse", "HEAD", cwd=td).strip()
        (td / "gsd-core" / "bin").mkdir(parents=True)
        (td / "gsd-core" / "bin" / "x.cjs").write_text("x", encoding="utf-8")
        subprocess.run([*git_ok, "-C", str(td), "add", "."], check=True, capture_output=True)
        subprocess.run([*git_ok, "-C", str(td), "commit", "-qm", "core"], check=True, capture_output=True)
        flagged_diff = diff_gsd_core(base, "HEAD", cwd=td)
        clean_diff = diff_gsd_core(base, base, cwd=td)
    ctrl_mut = classify_gsd_tools_calls(
        "import subprocess\nGSD_TOOLS='x'\ndef f():\n    subprocess.run(['node', GSD_TOOLS, 'config-set', 'k', 'v'])\n")
    ctrl_read = classify_gsd_tools_calls(
        "import subprocess\nGSD_TOOLS='x'\ndef f():\n    subprocess.run(['node', GSD_TOOLS, 'query', 'init.manager'])\n")
    fired = bool(flagged_diff) and any(c["class"] == "mutate" for c in ctrl_mut)
    quiet = not clean_diff and all(c["class"] == "read" for c in ctrl_read)
    ev = {"changed_files_in_range": len(landed), "gsd_core_paths_changed": core_paths,
          "gsd_tools_call_functions": len(sites), "mutating_call_functions": mutating,
          "control_diff_flagged": flagged_diff, "control_mutate_classified": len(ctrl_mut)}
    if core_paths or mutating:
        subs.append(result("branch-diff", BREACH, "repo-artefact", ev, control_fired=fired, negative_quiet=quiet,
                           reason="gsd-core path or mutating gsd-tools call in the branch", command=cmd))
    elif not landed:
        subs.append(result("branch-diff", UNMEASURED, "repo-artefact", ev, reason="empty_diff_range", command=cmd))
    else:
        subs.append(result("branch-diff", HELD, "repo-artefact", ev, control_fired=fired, negative_quiet=quiet, command=cmd))
    # --- host-core
    core = Path.home() / ".claude" / "gsd-core"
    cmd = "grep -rlE <switch names> ~/.claude/gsd-core (text files)"
    needles = _core_needles()
    files = {}
    if core.is_dir():
        for p in sorted(core.rglob("*")):
            if p.is_file() and p.stat().st_size < 2_000_000 and p.suffix in {".cjs", ".js", ".md", ".json", ".sh", ".py", ".mjs", ".ts", ""}:
                try:
                    files[str(p.relative_to(core))] = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
    hits = sweep_core_text(files, needles)
    ctrl_files = dict(list(files.items())[:3]) or {"a.md": "x"}
    ctrl_files["injected.cjs"] = "const s = process.env.CPP_ROTATION_INVARIANT; " + needles[0]
    ctrl_hits = sweep_core_text(ctrl_files, needles)
    base_ts = int(git("log", "-1", "--format=%ct", MISSION_BASE).strip())
    newer = sum(1 for p in core.rglob("*") if p.is_file() and p.stat().st_mtime > base_ts) if core.is_dir() else None
    ev = {"core_files_read": len(files), "needles": len(needles), "files_naming_a_switch": hits,
          "control_injected_found": "injected.cjs" in ctrl_hits, "files_newer_than_base_supplementary": newer,
          "laptop_core": "LAPTOP-ONLY-not-observed"}
    if not files:
        subs.append(result("host-core", UNMEASURED, "GEX44-host-readonly", ev, reason="gsd_core_absent_on_this_host", command=cmd))
    elif hits:
        subs.append(result("host-core", BREACH, "GEX44-host-readonly", ev, control_fired=True, command=cmd,
                           reason="a core file names a GSD X switch or function"))
    else:
        subs.append(result("host-core", HELD, "GEX44-host-readonly", ev, control_fired="injected.cjs" in ctrl_hits,
                           negative_quiet=not hits, command=cmd))
    return subs


# --------------------------------------------------------------------------------------------------- claim 10
def _c10_world(td: Path, case: str, count: list):
    """(rec, truth_done, note) for one crafted case; receipts are written beside a packet in a temp tree."""
    import gsd_mission as gm
    import receipt_judge as rj
    d = td / case
    d.mkdir()
    pkt = d / "unit.md"
    pkt.write_text("# packet\n", encoding="utf-8")
    rp = gm.stem_receipt(pkt)
    rec = {"mission_id": "m-" + case.replace("_", "")[:10], "state": "HALTED", "cwd": str(d), "created_at": 1.0,
           "wu_packet": {"path": str(pkt)}}
    body = "# Receipt\nStatus: DONE\nClaims: tests=5\n"
    note = None
    if case == "measured_key":
        rp.write_text(body, encoding="utf-8")
        rj.certificate_path(rp).write_text(json.dumps({"measured": {"tests": 9}}), encoding="utf-8")
        note = "certificate under key 'measured' (not 'values') is ignored by receipt_judge"
    elif case == "divergent_values":
        rp.write_text(body, encoding="utf-8")
        rj.certificate_path(rp).write_text(json.dumps({"values": {"tests": 9}}), encoding="utf-8")
    elif case == "other_mission_receipt":
        other = d / "other-unit.md"
        other.write_text("# other\n", encoding="utf-8")
        gm.stem_receipt(other).write_text(body, encoding="utf-8")
    elif case == "epoch_mismatch":
        rp.write_text(body, encoding="utf-8")
        rec["created_at"] = time.time() + 86400
    elif case == "not_done":
        rp.write_text("# Receipt\nStatus: IN PROGRESS\n", encoding="utf-8")
    elif case == "missing":
        pass
    elif case == "real_values":
        rp.write_text(body, encoding="utf-8")
        rj.certificate_path(rp).write_text(json.dumps({"values": {"tests": 5}}), encoding="utf-8")
    else:
        raise ValueError(case)
    return rec, rp, note


C10_CASES = ("measured_key", "divergent_values", "other_mission_receipt", "epoch_mismatch", "not_done", "missing")


def drive_c10(td: Path, cases, calls: list) -> dict:
    """Run the real reconcile on each crafted case; {case: {outcome, is_done}}. `calls` counts real reconcile calls."""
    import mission_reconcile as mrc
    import receipt_judge as rj
    out = {}
    real = mrc.reconcile

    def counted(*a, **k):
        calls.append(1)
        return real(*a, **k)

    with attr_patch(mrc, "reconcile", counted):
        for case in cases:
            rec, rp, note = _c10_world(td, case, calls)
            r = mrc.reconcile(rec, events=[], now=time.time(), programs_dir=td / case, missions=[rec])
            out[case] = {"outcome": r["outcome"], "is_done": bool(rj.is_done(rp)), "note": note}
    return out


def drive_forced(td: Path, calls: list) -> dict:
    """The is_done guard alone: the resolver is made to claim DONE for a receipt whose Status is not DONE (a worker success
    or closed non-DONE status reaching the reconciler), so only receipt_judge.is_done stands between it and RECOVERED_DONE."""
    import gsd_mission as gm
    import mission_reconcile as mrc
    import receipt_judge as rj
    real_res, real_rec = gm.resolve_receipt, mrc.reconcile

    def forced(*a, **k):
        r = dict(real_res(*a, **k))
        r["status"] = "DONE"
        return r

    def counted(*a, **k):
        calls.append(1)
        return real_rec(*a, **k)

    rec, rp, _ = _c10_world(td, "not_done", calls)
    with attr_patch(gm, "resolve_receipt", forced), attr_patch(mrc, "reconcile", counted):
        r = mrc.reconcile(rec, events=[], now=time.time(), programs_dir=td / "not_done", missions=[rec])
    return {"outcome": r["outcome"], "is_done": bool(rj.is_done(rp))}


def attack_10(ctx) -> list[dict]:
    import flow_replay as fr
    subs = []
    calls: list = []
    with temp_root() as td:
        base = drive_c10(td, C10_CASES, calls)
    with temp_root() as td, fr.mutant_scope("terminal-without-proof"):
        mut = drive_c10(td, C10_CASES, calls)
    with temp_root() as td:
        neg = drive_c10(td, ("real_values",), calls)
    with temp_root() as td:
        forced_base = drive_forced(td, calls)
    with temp_root() as td, fr.mutant_scope("terminal-without-proof"):
        forced_mut = drive_forced(td, calls)
    false_done = sorted(c for c, v in base.items() if v["outcome"] == "RECOVERED_DONE" and not v["is_done"])
    mut_done = sorted(c for c, v in mut.items() if v["outcome"] == "RECOVERED_DONE" and base[c]["outcome"] != "RECOVERED_DONE")
    if forced_mut["outcome"] == "RECOVERED_DONE" and forced_base["outcome"] != "RECOVERED_DONE":
        mut_done.append("forced_status_not_done")
    notes = {c: v["note"] for c, v in base.items() if v["note"]}
    unverified = sorted(c for c, v in base.items() if v["outcome"] == "RECOVERED_DONE" and v["note"])
    ev = {"cases": {c: base[c]["outcome"] for c in C10_CASES}, "reconcile_calls": len(calls),
          "false_done_cases": false_done, "mutant_recovered_done_cases": mut_done,
          "negative_control_real_values": neg["real_values"]["outcome"],
          "forced_status_guard_alone": {"unmutated": forced_base["outcome"], "mutant": forced_mut["outcome"],
                                        "is_done": forced_base["is_done"]},
          "noted_not_breach": {c: notes[c] for c in unverified}}
    cmd = "mission_reconcile.reconcile over 6 crafted cases + forced-status guard control; flow_replay.mutant_scope('terminal-without-proof')"
    fired = bool(mut_done)
    quiet = neg["real_values"]["outcome"] == "RECOVERED_DONE"
    if false_done:
        subs.append(result("crafted-receipts", BREACH, "GEX44-temp-copy", ev, control_fired=fired, negative_quiet=quiet,
                           reason="RECOVERED_DONE where receipt_judge.is_done is false", command=cmd))
    else:
        subs.append(result("crafted-receipts", HELD, "GEX44-temp-copy", ev, control_fired=fired and quiet,
                           negative_quiet=quiet, command=cmd))
    # host evidence comes from the hash-checked replay report; the Verifier found no host receipts to judge
    rep = load_replay(ctx)
    done_na = rep["fc06_done_proof"]
    subs.append(result("host-evidence", UNMEASURED, "GEX44-host-readonly",
                       {"s5_slice": rep["s5"], "done_proof": done_na}, reason="no host receipts (done_proof not_applicable)",
                       command="07-REPLAY.json (sha256 checked against the committed blob)"))
    return subs


# --------------------------------------------------------------------------------------------------- reused evidence
def load_replay(ctx) -> dict:
    """07-REPLAY.json, used only after its sha256 equals the committed blob and its pin sha256 equals 07-PIN.json."""
    import flow_replay as fr

    def load():
        p = ROOT / PHASE7 / "07-REPLAY.json"
        blob = subprocess.run(["git", "show", f"HEAD:{PHASE7}/07-REPLAY.json"], cwd=str(ROOT), capture_output=True,
                              timeout=60)
        if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != sha256(p):
            raise fr.Inconclusive("07-REPLAY.json does not equal the committed blob")
        rep = json.loads(p.read_bytes())
        if ((rep.get("pin") or {}).get("data") or {}).get("sha256") != ctx.pin["sha256"]:
            raise fr.Inconclusive("07-REPLAY.json was built from a different pin")
        return rep
    rep = ctx.cached("replay", load)
    s5 = (rep.get("s5") or {}).get("data") or {}
    dp = ((rep.get("fc06") or {}).get("data") or {}).get("done_proof")
    s5 = {"keys": sorted(s5)[:12]} if isinstance(s5, dict) else {}
    return {"s5": s5, "fc06_done_proof": dp, "raw": rep}


# --------------------------------------------------------------------------------------------------- claim 7
C7_AUTH, C7_CALLS = 10_000_000_000, 100


def c7_loop(ms, *, lapse_at=None):
    """Drive mission_spend.judge in a pure loop on a dict record, mirroring _renew_lease's bookkeeping on the dict.
    The fingerprint changes on every call and the spend grows 1.3x per call, so every call outruns the estimate."""
    rec = {"mission_id": "m-redteam", "authority_tokens": C7_AUTH, "token_estimate": 1000, "token_trip_ratio": 2.0,
           "lease_renewals": 0, "cost_mark": {"fp": "fp-0", "tokens": 0}}
    cap = C7_AUTH - ms.closeout_reserve(rec)
    spent, renewals, trips, over_cap_no_trip, renew_after_lapse, tripped_at = 1000, 0, 0, 0, 0, None
    for i in range(1, C7_CALLS + 1):
        spent = int(spent * 1.3) + 1
        if lapse_at is not None and i == lapse_at:
            rec["authority_tokens"] = None
        d = ms.judge(rec, spent, f"fp-{i}")
        rc = d.get("recompile")
        if d.get("trip"):
            trips += 1
            tripped_at = i
            break
        if rc and rc.get("lease"):
            if rec.get("authority_tokens") is None:
                renew_after_lapse += 1
            c = int(rc["authority"]) - ms.closeout_reserve(rec)
            headroom = min(int(rc["estimate"]), max(1, c - int(rc["spent"])))
            est = max(1, min(math.ceil((int(rc["spent"]) + headroom) / float(rc["ratio"])), int(c // float(rc["ratio"]))))
            rec["token_estimate"] = est
            rec["lease_renewals"] = int(rec["lease_renewals"]) + 1
            rec["cost_mark"] = {"fp": rc["fp"], "tokens": rc["spent"]}
            renewals += 1
        elif d.get("mark"):
            rec["cost_mark"] = d["mark"]
        if rec.get("authority_tokens") and spent >= cap:
            over_cap_no_trip += 1
    return {"renewals": renewals, "trips": trips, "tripped_at": tripped_at, "over_cap_no_trip": over_cap_no_trip,
            "renew_after_lapse": renew_after_lapse, "final_spent": spent, "cap": cap}


def c7_topup(tu):
    """The top-up judge asked 30 times about one authority-trip hold; count how many asks it answers `grant`."""
    gm = tu.gm
    rec = {"mission_id": "m-redteam", "state": "HELD", "owner_hold": {"kind": "cost", "set_at": 111.0,
           "reason": tu.AUTHORITY_TRIP + " ..."}}
    prog = {"measured": True, "progress": True, "commits": 2, "paths": 3}
    pol = {"grants": [], "max_topups": 2, "last_head": "abc"}
    grants = 0
    for _ in range(30):
        d = tu.judge(rec, pol, prog)
        if d["action"] == "grant":
            grants += 1
            pol["grants"].append({"hold_set_at": 111.0})
    rec2 = dict(rec, owner_hold=dict(rec["owner_hold"], set_at=222.0))
    pol["grants"].append({"hold_set_at": 150.0})
    refused = tu.judge(rec2, pol, prog)["action"] == "refuse"
    return {"grants_for_one_hold": grants, "second_hold_at_max_refused": refused, "terminal_is_none": gm is not None}


def attack_7(ctx) -> list[dict]:
    import flow_replay as fr
    import mission_spend as ms
    import mission_topup as tu
    base = c7_loop(ms)
    lapsed = c7_loop(ms, lapse_at=10)
    top = c7_topup(tu)
    with fr.mutant_scope("expand-authority"):
        mut_auth = c7_loop(ms)
    with attr_patch(ms, "LEASE_MAX_RENEWALS", 10 ** 9):
        mut_cap = c7_loop(ms)

    def judge_ignoring_seq(rec, pol, prog):
        return tu.judge(rec, dict(pol, grants=[]), prog)
    grants_ignoring = 0
    rec = {"mission_id": "m-redteam", "state": "HELD", "owner_hold": {"kind": "cost", "set_at": 111.0,
           "reason": tu.AUTHORITY_TRIP + " ..."}}
    for _ in range(30):
        if judge_ignoring_seq(rec, {"grants": [{"hold_set_at": 111.0}], "max_topups": 2}, {"measured": True, "progress": True,
                                                                                         "commits": 1, "paths": 1})["action"] == "grant":
            grants_ignoring += 1
    violations = []
    if base["over_cap_no_trip"]:
        violations.append("spend past authority less closeout without a trip")
    if base["renewals"] > ms.LEASE_MAX_RENEWALS:
        violations.append("renewals above LEASE_MAX_RENEWALS")
    if top["grants_for_one_hold"] > 1 or not top["second_hold_at_max_refused"]:
        violations.append("top-up granted more than once for one hold")
    if lapsed["renew_after_lapse"] or not lapsed["trips"]:
        violations.append("renewal granted after authority lapsed, or no trip")
    fired = (mut_auth["over_cap_no_trip"] > 0 and mut_cap["renewals"] > 20 and grants_ignoring > 1)
    ev = {"base": base, "authority_lapsed_at_call_10": lapsed, "topup": top, "lease_max_renewals": ms.LEASE_MAX_RENEWALS,
          "control_expand_authority_over_cap_calls": mut_auth["over_cap_no_trip"],
          "control_lease_cap_removed_renewals": mut_cap["renewals"], "control_seq_ignored_grants": grants_ignoring}
    cmd = "mission_spend.judge in a 100-call pure loop (fingerprint moves every call); mission_topup.judge x30; mutant expand-authority; LEASE_MAX_RENEWALS patched"
    if violations:
        return [result("renew-loop", BREACH, "GEX44-temp-copy", ev, control_fired=fired, negative_quiet=True,
                       reason="; ".join(violations), command=cmd)]
    return [result("renew-loop", HELD, "GEX44-temp-copy", ev, control_fired=fired, negative_quiet=True, command=cmd)]


# --------------------------------------------------------------------------------------------------- claim 8
C8_CASES = ("empty_commit", "amend_identical_tree", "state_md_only", "resumption_file_md_only", "resumption_md_only",
            "tracked_junk_file", "untracked_test_log", "gitignored_dir_file", "mtime_only")


def _g(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="rt", GIT_AUTHOR_EMAIL="rt@x", GIT_COMMITTER_NAME="rt", GIT_COMMITTER_EMAIL="rt@x")
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:120]}")
    return r.stdout


def _c8_repo(td: Path) -> Path:
    repo = td / "repo"
    (repo / ".planning" / "workstreams" / "x").mkdir(parents=True)
    _g(repo, "init", "-q")
    (repo / ".gitignore").write_text("ignored_dir/\n", encoding="utf-8")
    (repo / "app.py").write_text("print('v1')\n", encoding="utf-8")
    (repo / ".planning" / "workstreams" / "x" / "PLAN.md").write_text("# plan\n", encoding="utf-8")
    (repo / ".planning" / "workstreams" / "x" / "STATE.md").write_text("s0\n", encoding="utf-8")
    (repo / "ignored_dir").mkdir()
    _g(repo, "add", "-A")
    _g(repo, "commit", "-q", "-m", "base")
    return repo


def _c8_apply(repo: Path, case: str) -> None:
    ws = repo / ".planning" / "workstreams" / "x"
    if case == "empty_commit":
        _g(repo, "commit", "-q", "--allow-empty", "-m", "noise")
    elif case == "amend_identical_tree":
        _g(repo, "commit", "-q", "--amend", "--allow-empty", "-m", "base again")
    elif case == "state_md_only":
        (ws / "STATE.md").write_text("s1 no unit\n", encoding="utf-8")
        _g(repo, "add", "-A"), _g(repo, "commit", "-q", "-m", "state")
    elif case == "resumption_file_md_only":
        (repo / "RESUMPTION_FILE.md").write_text("next: nothing\n", encoding="utf-8")
        _g(repo, "add", "-A"), _g(repo, "commit", "-q", "-m", "resumption file")
    elif case == "resumption_md_only":
        (ws / "RESUMPTION.md").write_text("resume\n", encoding="utf-8")
        _g(repo, "add", "-A"), _g(repo, "commit", "-q", "-m", "resumption")
    elif case == "tracked_junk_file":
        (repo / "junk.txt").write_text(os.urandom(16).hex(), encoding="utf-8")
        _g(repo, "add", "-A"), _g(repo, "commit", "-q", "-m", "junk")
    elif case == "untracked_test_log":
        (repo / "pytest.log").write_text("3 passed\n", encoding="utf-8")
    elif case == "gitignored_dir_file":
        (repo / "ignored_dir" / "cache.bin").write_text("x", encoding="utf-8")
    elif case == "mtime_only":
        os.utime(repo / "app.py", (1, 1))
    elif case == "real_code_change":
        (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
        _g(repo, "add", "-A"), _g(repo, "commit", "-q", "-m", "feat")
    else:
        raise ValueError(case)


def c8_cases(gm, ms, cases, *, bookkeeping_count=False) -> dict:
    out = {}
    env = os.environ.get("CPP_PROGRESS_BOOKKEEPING")
    if bookkeeping_count:
        os.environ["CPP_PROGRESS_BOOKKEEPING"] = "count"
    else:
        os.environ.pop("CPP_PROGRESS_BOOKKEEPING", None)
    try:
        for case in cases:
            with temp_root() as td:
                repo = _c8_repo(td)
                before = gm.progress_fingerprint(str(repo))
                _c8_apply(repo, case)
                after = gm.progress_fingerprint(str(repo))
            moved = before is not None and after is not None and before != after
            granted = False
            if moved:
                rec = {"authority_tokens": 10_000_000_000, "token_estimate": 1000, "token_trip_ratio": 2.0,
                       "lease_renewals": 0, "cost_mark": {"fp": before, "tokens": 1000}}
                d = ms.judge(rec, 5000, after)
                granted = bool((d.get("recompile") or {}).get("lease"))
            out[case] = {"measured": before is not None and after is not None, "moved": moved, "renewal_granted": granted}
    finally:
        if env is None:
            os.environ.pop("CPP_PROGRESS_BOOKKEEPING", None)
        else:
            os.environ["CPP_PROGRESS_BOOKKEEPING"] = env
    return out


def attack_8(ctx) -> list[dict]:
    import gsd_mission as gm
    import mission_spend as ms
    base = c8_cases(gm, ms, C8_CASES)
    real = c8_cases(gm, ms, ("real_code_change",))["real_code_change"]
    ctl = c8_cases(gm, ms, ("state_md_only",), bookkeeping_count=True)["state_md_only"]
    gamed = sorted(c for c, v in base.items() if v["moved"] and v["renewal_granted"])
    ev = {"cases": base, "gamed_cases": gamed, "real_code_change": real,
          "control_count_mode_state_md_only_moved": ctl["moved"],
          "bound_on_damage": {"lease_max_renewals": ms.LEASE_MAX_RENEWALS, "ceiling": "authority less closeout reserve (claim 7)"},
          "unmeasured_cases": sorted(c for c, v in base.items() if not v["measured"])}
    fired = bool(ctl["moved"])
    quiet = bool(real["moved"] and real["renewal_granted"]) and not base["state_md_only"]["moved"]
    cmd = "gsd_mission.progress_fingerprint before/after 9 noise cases in temp git repos + mission_spend.judge; CPP_PROGRESS_BOOKKEEPING=count control"
    if gamed:
        return [result("noise-cases", BREACH, "GEX44-temp-copy", ev, control_fired=fired, negative_quiet=quiet,
                       reason=f"content-free change moves the fingerprint and is granted a lease renewal: {', '.join(gamed)}",
                       command=cmd)]
    return [result("noise-cases", HELD, "GEX44-temp-copy", ev, control_fired=fired, negative_quiet=quiet, command=cmd)]


# --------------------------------------------------------------------------------------------------- claim 4
_C4_ENTRIES = ("arm_preflight", "arm_chain", "arm", "arm_mission", "plan_next", "supervise", "supervisor_pass")
_C4_WRITE_ATTRS = {"write_text", "write_bytes", "rename", "copy", "copyfile", "copy2", "move", "unlink", "truncate", "writelines"}
_C4_ROADMAP_VERBS = ("roadmap update", "roadmap.update", "roadmap.set", "roadmap set", "update-plan-progress")


def sweep_roadmap_writers(files: dict[str, str], entries=_C4_ENTRIES) -> dict:
    """Functions that name ROADMAP and write (or call a gsd-tools roadmap mutation), and whether a name-based call walk from
    the arm / supervisor entry points reaches them. A function name shared by two files is treated as one node (over-approximates)."""
    calls: dict[str, set] = {}
    sites, examined = [], 0
    for name, text in sorted(files.items()):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            examined += 1
            callees = set()
            writes, opens = set(), 0
            for n in ast.walk(fn):
                if isinstance(n, ast.Call):
                    f = n.func
                    if isinstance(f, ast.Name):
                        callees.add(f.id)
                        if f.id == "open" and len(n.args) > 1 and isinstance(n.args[1], ast.Constant) \
                                and any(c in str(n.args[1].value) for c in "wa+x"):
                            opens += 1
                    elif isinstance(f, ast.Attribute):
                        callees.add(f.attr)
                        if f.attr in _C4_WRITE_ATTRS:
                            writes.add(f.attr)
            calls.setdefault(fn.name, set()).update(callees)
            seg = ast.get_source_segment(text, fn) or ""
            verb = [v for v in _C4_ROADMAP_VERBS if v in seg]
            if "ROADMAP" in seg and (writes or opens or verb):
                sites.append({"file": name, "function": fn.name, "writes": sorted(writes), "opens_w": opens, "gsd_verbs": verb})
    reach, frontier = set(entries), list(entries)
    while frontier:
        for c in calls.get(frontier.pop(), ()):
            if c not in reach:
                reach.add(c)
                frontier.append(c)
    for s in sites:
        s["reachable_from_arm_or_supervisor"] = s["function"] in reach
    return {"sites": sites, "functions_examined": examined, "reachable": [s for s in sites if s["reachable_from_arm_or_supervisor"]]}


_C4_ALPHA = (b"a", b"b", b" ", b"\t", b"\n", b"\r", b"\r\n", b"\xef\xbb\xbf", "é".encode(), "é".encode())


def _c4_canon(x: bytes) -> bytes:
    """An independent statement of the allowed equivalence: one leading BOM and CRLF versus LF, nothing else."""
    if x[:3] == b"\xef\xbb\xbf":
        x = x[3:]
    return re.sub(rb"\r\n", b"\n", x)


def c4_property(gm, seed=11, n=300) -> dict:
    import random
    rng = random.Random(seed)
    dig = lambda b: hashlib.sha256(gm._normalise_packet(b)).hexdigest()   # noqa: E731
    pool = [b"".join(rng.choice(_C4_ALPHA) for _ in range(rng.randint(0, 7))) for _ in range(n)]
    pool += [b"", b"\r", b"a\rb", b"a\r\nb", b"a\nb", b"\xef\xbb\xbfx", b"x\xef\xbb\xbfy", b"x ", b"x", b"x\n", b"e\xcc\x81", "é".encode()]
    seen: dict[str, bytes] = {}
    collisions = []
    for b in pool:
        d = dig(b)
        if d in seen and _c4_canon(seen[d]) != _c4_canon(b):
            collisions.append([seen[d].hex(), b.hex()])
        seen.setdefault(d, b)
    changes = {"trailing_space": (b"abc", b"abc "), "trailing_newline": (b"abc", b"abc\n"), "cr_only_vs_lf": (b"a\nb", b"a\rb"),
               "mid_bom": (b"ab", b"a\xef\xbb\xbfb"), "nfc_vs_nfd": ("é".encode(), "é".encode()), "empty_vs_nl": (b"", b"\n")}
    allowed = {"leading_bom": (b"abc", b"\xef\xbb\xbfabc"), "crlf_vs_lf": (b"a\nb\n", b"a\r\nb\r\n")}
    merged_semantic = sorted(k for k, (x, y) in changes.items() if dig(x) == dig(y))
    split_allowed = sorted(k for k, (x, y) in allowed.items() if dig(x) != dig(y))
    return {"inputs": len(pool), "random_collisions": collisions[:5], "random_collision_count": len(collisions),
            "semantic_changes_merged": merged_semantic, "allowed_equivalences_split": split_allowed}


def attack_4(ctx) -> list[dict]:
    import gsd_mission as gm
    files = {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8", errors="replace") for p in _tools_py()}
    sw = sweep_roadmap_writers(files)
    inj = dict(files)
    inj["modules/zz_injected.py"] = ("from pathlib import Path\ndef arm_preflight(d):\n    sneaky(d)\n"
                                     "def sneaky(d):\n    (Path(d) / 'ROADMAP.md').write_text('x')\n")
    ctl_sw = sweep_roadmap_writers(inj)
    ctl_found = any(s["file"] == "modules/zz_injected.py" and s["reachable_from_arm_or_supervisor"] for s in ctl_sw["sites"])
    prop = c4_property(gm)

    def stripping(data: bytes) -> bytes:
        return data.strip()
    with attr_patch(gm, "_normalise_packet", stripping):
        ctl_prop = c4_property(gm)
    ctl_prop_fired = bool(ctl_prop["semantic_changes_merged"] or ctl_prop["random_collision_count"])
    quiet_prop = not prop["allowed_equivalences_split"]
    subs = []
    ev_sw = {"functions_examined_gt_1000": sw["functions_examined"] > 1000, "files_swept_gt_100": len(files) > 100,   # counts move with every tools edit
             "roadmap_write_sites": [{k: v for k, v in s.items()} for s in sw["sites"]], "reachable_count": len(sw["reachable"]),
             "control_injected_found_and_reachable": ctl_found}
    cmd_sw = "ast sweep of tools/*.py and modules/**/*.py for ROADMAP-naming writers + name-based call walk from arm/supervisor entry points"
    if sw["reachable"]:
        subs.append(result("writer-sweep", BREACH, "repo-artefact", ev_sw, control_fired=ctl_found, negative_quiet=True,
                           reason="an automatic path reaches a ROADMAP writer", command=cmd_sw))
    else:
        subs.append(result("writer-sweep", HELD, "repo-artefact", ev_sw, control_fired=ctl_found, negative_quiet=True, command=cmd_sw))
    ev_p = dict(prop, control_whitespace_stripping=ctl_prop)
    cmd_p = "gsd_mission._normalise_packet over 312 inputs and 8 named pairs; attr_patch to a whitespace-stripping normaliser as control"
    if prop["random_collision_count"] or prop["semantic_changes_merged"]:
        subs.append(result("packet-normaliser", BREACH, "GEX44-temp-copy", ev_p, control_fired=ctl_prop_fired,
                           negative_quiet=quiet_prop, reason="normaliser merges inputs that differ beyond BOM or CRLF", command=cmd_p))
    else:
        subs.append(result("packet-normaliser", HELD, "GEX44-temp-copy", ev_p, control_fired=ctl_prop_fired and quiet_prop,
                           negative_quiet=quiet_prop, command=cmd_p))
    return subs


# --------------------------------------------------------------------------------------------------- claim 9
def c9_sweep(bc, gate, cwd, use_filters=True) -> dict:
    """foreseeable_decisions over every workstream of this clone; each emitted item re-classified independently."""
    root = Path(cwd) / ".planning" / "workstreams"
    per, spurious, dup, owner, total, srcs_ok = {}, [], [], 0, 0, 0
    for ws in sorted(p.name for p in root.iterdir() if p.is_dir()):
        r = bc.foreseeable_decisions(str(cwd), ws, use_filters=use_filters)
        srcs_ok += sum(1 for s in r["sources"] if s["status"] == "ok")
        texts: dict[str, int] = {}
        n_sp = 0
        for it in r["items"]:
            total += 1
            v = gate.classify(it["text"], authorized=())
            if v.get("owner") == "OWNER" or bc.PROTECTED.search(it["text"]):
                owner += 1
            else:
                n_sp += 1
                spurious.append({"workstream": ws, "line": it["line"], "text": it["text"][:70]})
            key = re.sub(r"\W+", " ", it["text"]).strip().lower()
            texts[key] = texts.get(key, 0) + 1
        d = sum(c - 1 for c in texts.values() if c > 1)
        if d:
            dup.append({"workstream": ws, "duplicates": d})
        per[ws] = {"items": len(r["items"]), "spurious": n_sp}
    return {"workstreams": len(per), "sources_read": srcs_ok, "items": total, "owner_class": owner,
            "spurious": len(spurious), "spurious_examples": spurious[:3], "duplicate_workstreams": dup,
            "duplicates": sum(d["duplicates"] for d in dup), "per_workstream": per}


def attack_9(ctx) -> list[dict]:
    import blocker_compiler as bc
    from modules.autonomy_gate import gate
    real = c9_sweep(bc, gate, ctx.root)
    ctl = c9_sweep(bc, gate, ctx.root, use_filters=False)
    fired = ctl["spurious"] > 0
    with temp_root() as td:
        ws = td / ".planning" / "workstreams" / "seed"
        ws.mkdir(parents=True)
        (ws / "STATE.md").write_text("OWNER DECISION NEEDED: whether to publish the package to the public PyPI index\n"
                                     "- Verified the retry loop passes 40/40 tests\n", encoding="utf-8")
        seeded = c9_sweep(bc, gate, td)
    seeded_quiet = seeded["items"] >= 1 and seeded["spurious"] == 0
    cmd = ("blocker_compiler.foreseeable_decisions over every .planning/workstreams entry of this clone; each item re-classified by "
           "modules.autonomy_gate.gate.classify(authorized=()); control: use_filters=False")
    ev = {"definition": "too many = at least one emitted item that is not Owner-class, or that duplicates another item",
          "real": {**{k: v for k, v in real.items() if k not in ("per_workstream", "items", "owner_class", "sources_read")}, "sources_read_ge_5": real["sources_read"] >= 5}, "control_filters_off": {"spurious_positive": ctl["spurious"] > 0, "items_positive": ctl["items"] > 0, "workstreams": ctl["workstreams"]},  # item counts move with every STATE.md edit, so only their sign is evidence
          "seeded_ask": {k: v for k, v in seeded.items() if k not in ("per_workstream", "spurious_examples")}}
    subs = []
    if real["spurious"] or real["duplicates"]:
        subs.append(result("decisions-sweep", BREACH, "GEX44-host-readonly", ev, control_fired=fired, negative_quiet=seeded_quiet,
                           reason=f"{real['spurious']} non-Owner-class and {real['duplicates']} duplicate item(s) emitted", command=cmd))
    else:
        subs.append(result("decisions-sweep", HELD, "GEX44-host-readonly", ev, control_fired=fired and seeded_quiet,
                           negative_quiet=seeded_quiet, command=cmd))
    n = sum(1 for r in ctx.rows if r.get("event") == "owner_decisions_batch")
    subs.append(result("production-frequency", UNMEASURED if n == 0 else HELD, "GEX44-host-readonly",
                       {"owner_decisions_batch_rows_in_pin": n}, control_fired=True if n else None,
                       reason="no owner_decisions_batch row in the pinned prefix: live frequency unmeasured" if n == 0 else None,
                       command="count of owner_decisions_batch rows in the pinned ledger prefix"))
    return subs


# --------------------------------------------------------------------------------------------------- claim 11
_C11_ACTION_VERBS = ("launch", "claim", "assign", "spawn", "steal", "reassign", "dispatch", "start_worker", "admit")
_C11_ACTION_EVENTS = ("unit_complete", "unit_completed", "unit_settled", "recovery_committed", "recovery_unit_advanced")
_C11_ALLOWED_READERS = ("tools/blocker_compiler.py", "tools/flow_replay.py", "tools/s9_kv_check.py")


def sweep_stealing_consumers(files: dict[str, str]) -> dict:
    """Functions that read `independent_work` and also call something that launches, claims, assigns or dispatches work.
    The producer and the evaluator-side readers are listed apart; a consumer anywhere else is work stealing code."""
    readers, consumers = [], []
    for name, text in sorted(files.items()):
        if "independent_work" not in text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            seg = ast.get_source_segment(text, fn) or ""
            if "independent_work" not in seg:
                continue
            readers.append({"file": name, "function": fn.name})
            if name in _C11_ALLOWED_READERS:
                continue
            acts: set = set()

            def name_of(n):
                return n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else ""
            for n in ast.walk(fn):
                # an action is a consumer of independent_work only when it is gated by it or is handed it
                if isinstance(n, (ast.If, ast.IfExp, ast.While)) and "independent_work" in (ast.get_source_segment(text, n.test) or ""):
                    body = n.body if isinstance(n.body, list) else [n.body]
                    for stmt in body:
                        acts |= {name_of(c) for c in ast.walk(stmt) if isinstance(c, ast.Call) and any(v in name_of(c).lower() for v in _C11_ACTION_VERBS)}
                elif isinstance(n, ast.Call) and any(v in name_of(n).lower() for v in _C11_ACTION_VERBS) \
                        and "independent_work" in "".join(ast.get_source_segment(text, x) or "" for x in [*n.args, *[k.value for k in n.keywords]]):
                    acts.add(name_of(n))
            if acts:
                consumers.append({"file": name, "function": fn.name, "action_calls": sorted(acts)})
    return {"readers": readers, "consumers": consumers}


def s8_predicate(rows: list[dict]) -> dict:
    """D-09: >= 1 incident where an independent safe action existed while the critical path was blocked AND the blocker row
    recorded independent_work=true. Independent action = a unit-completion or recovery commit row of the same mission after the
    blocked row and before its next mission_unblocked row."""
    incidents, true_rows = [], 0
    by_mission: dict = {}
    for i, r in enumerate(rows):
        by_mission.setdefault(r.get("mission_id") or r.get("session_id"), []).append(r)
    for mid, rs in by_mission.items():
        for j, r in enumerate(rs):
            if r.get("event") != "mission_blocked" or r.get("independent_work") is not True:
                continue
            true_rows += 1
            for later in rs[j + 1:]:
                if later.get("event") == "mission_unblocked":
                    break
                if later.get("event") in _C11_ACTION_EVENTS:
                    incidents.append({"mission_id": mid, "blocked_ts": r.get("ts"), "action": later.get("event")})
                    break
    return {"value": bool(incidents), "incidents": len(incidents), "blocked_rows": sum(1 for r in rows if r.get("event") == "mission_blocked"),
            "blocked_with_independent_work_true": true_rows}


def attack_11(ctx) -> list[dict]:
    files = {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8", errors="replace") for p in _tools_py()}
    sw = sweep_stealing_consumers(files)
    inj = dict(files)
    inj["modules/zz_inject.py"] = ("def pick(rows):\n    for r in rows:\n        if r.get('independent_work'):\n"
                                   "            launch_mission(r)\n")
    ctl = sweep_stealing_consumers(inj)
    found = any(c["file"] == "modules/zz_inject.py" for c in ctl["consumers"])
    subs = []
    ev = {"readers_of_independent_work": sw["readers"], "consumers": sw["consumers"], "files_swept": len(files),
          "control_injected_consumer_found": found}
    cmd = "ast sweep: functions reading independent_work that also call launch/claim/assign/dispatch (S8 is dormant by decision D-09)"
    if sw["consumers"]:
        subs.append(result("no-stealing-code", BREACH, "repo-artefact", ev, control_fired=found, negative_quiet=True,
                           reason="work stealing code exists although S8 is dormant", command=cmd))
    else:
        subs.append(result("no-stealing-code", HELD, "repo-artefact", ev, control_fired=found, negative_quiet=True, command=cmd))
    real = s8_predicate(ctx.rows)
    t0 = {"mission_id": "m-seed", "ts": "t"}
    seeded_true = s8_predicate([dict(t0, event="mission_blocked", independent_work=True), dict(t0, event="unit_completed"),
                                dict(t0, event="mission_unblocked")])
    no_action = s8_predicate([dict(t0, event="mission_blocked", independent_work=True), dict(t0, event="worker_acked"),
                              dict(t0, event="mission_unblocked"),
                              dict(t0, event="unit_completed")])
    not_recorded = s8_predicate([dict(t0, event="mission_blocked", independent_work=False), dict(t0, event="unit_completed")])
    fired = seeded_true["value"] is True
    quiet = no_action["value"] is False and not_recorded["value"] is False
    evp = {"pin_rows": len(ctx.rows), "pinned_prefix": real, "seeded_qualifying": seeded_true["value"],
           "independent_work_true_without_action": no_action["value"], "action_without_independent_work_true": not_recorded["value"]}
    cmdp = "s8_predicate(rows) from D-09 over the pinned prefix, a seeded qualifying ledger and two negative seeds"
    if real["value"]:
        subs.append(result("predicate", BREACH, "GEX44-host-readonly", evp, control_fired=fired, negative_quiet=quiet,
                           reason="the S8 activation predicate is true at the pin but S8 is still dormant", command=cmdp))
    else:
        subs.append(result("predicate", HELD, "GEX44-host-readonly", evp, control_fired=fired and quiet, negative_quiet=quiet,
                           command=cmdp))
    return subs


def sweep_hours_deciders(files: dict[str, str]) -> dict:
    """Functions that read the summed-mission-hours number and let it steer a branch or a pick. Reporting-only readers
    (the accounting itself, the renderer) are listed apart; a decider anywhere is an efficiency compiler on the wrong number."""
    import ast
    readers, deciders = [], []
    for rel, src in sorted(files.items()):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            body = ast.Module(body=fn.body, type_ignores=[])
            reads = any((isinstance(n, ast.Constant) and n.value == "summed_mission_hours") or
                        (isinstance(n, ast.Name) and n.id == "summed_mission_hours") or
                        (isinstance(n, ast.Attribute) and n.attr == "summed_mission_hours") for n in ast.walk(body))
            if not reads:
                continue
            entry = {"file": rel, "function": fn.name}
            readers.append(entry)
            steers = False
            for n in ast.walk(body):
                tests = [n.test] if isinstance(n, (ast.If, ast.IfExp, ast.While)) else [n] if isinstance(n, ast.Compare) else []
                for t in tests:
                    if any((isinstance(m, ast.Constant) and m.value == "summed_mission_hours") or
                           (isinstance(m, ast.Attribute) and m.attr == "summed_mission_hours") or
                           (isinstance(m, ast.Name) and m.id == "summed_mission_hours") for m in ast.walk(t)):
                        steers = True
            if steers or re.search(r"(choose|select|optimi|decide|rank|compile|prefer)", fn.name):
                deciders.append(entry)
    return {"readers": readers, "deciders": deciders}


def _c13_rows(parallel: bool) -> list[dict]:
    def row(m, t, ev, **kw):
        return dict({"mission_id": m, "ts": f"2026-10-01T{t}:00:00+00:00", "event": ev}, **kw)
    if parallel:
        return [row("m-aaaa", "00", "launch_claimed"), row("m-bbbb", "00", "launch_claimed"),
                row("m-aaaa", "03", "mission_completed"), row("m-bbbb", "03", "mission_completed")]
    return [row("m-aaaa", "00", "launch_claimed"), row("m-aaaa", "02", "mission_renewed", successor="m-bbbb"),
            row("m-aaaa", "02", "mission_completed"), row("m-bbbb", "02", "launch_claimed"),
            row("m-bbbb", "04", "mission_completed")]


def attack_13(ctx) -> list[dict]:
    files = {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8", errors="replace") for p in _tools_py()}
    named = sorted(rel for rel, src in files.items()
                   if re.search(r"efficiency[_ ]?compil", rel + "\n" + src, re.I) and not rel.endswith(("redteam_s9.py", "test_s9_redteam.py")))
    subs = [result("subject", HELD, "repo-artefact",
                   {"files_swept": len(files), "files_naming_an_efficiency_compiler": named,
                    "subject_used": "flow_replay.time_accounting + verdict + render_md (the only code that reads summed hours)"},
                   control_fired=bool(re.search(r"efficiency[_ ]?compil", "def efficiency_compiler(): pass", re.I)),
                   negative_quiet=not named, reason=None, command="grep every tools/*.py path and body for an efficiency compiler")]
    sw = sweep_hours_deciders(files)
    inj = dict(files)
    inj["modules/zz_inject.py"] = ("def choose_plan(acc):\n    if acc['summed_mission_hours']['hours'] < 10:\n"
                                   "        return 'gain'\n    return 'loss'\n")
    found = any(d["file"] == "modules/zz_inject.py" for d in sweep_hours_deciders(inj)["deciders"])
    ev = {"readers": sw["readers"], "deciders": sw["deciders"], "control_injected_decider_found": found}
    cmd = "ast sweep: functions reading summed_mission_hours that branch on it or are named choose/select/optimise/decide/rank"
    subs.append(result("objective-sweep", BREACH if sw["deciders"] else HELD, "repo-artefact", ev, control_fired=found,
                       negative_quiet=True, reason="a decision reads summed mission-hours" if sw["deciders"] else None, command=cmd))
    fr = ctx.fr
    par, ser = fr.time_accounting(_c13_rows(True), {}), fr.time_accounting(_c13_rows(False), {})
    h = lambda a, k: a[k]["hours"]
    summed_drop = h(ser, "summed_mission_hours") < h(par, "summed_mission_hours")
    crit_rise = h(ser, "critical_path_wall_clock_hours") > h(par, "critical_path_wall_clock_hours")
    wall_rise = h(ser, "wall_clock_hours") > h(par, "wall_clock_hours")
    naive_gain = h(ser, "summed_mission_hours") < h(par, "summed_mission_hours")      # the aggregate-hours objective
    real_gain = h(ser, "critical_path_wall_clock_hours") < h(par, "critical_path_wall_clock_hours")
    mutant_labels = naive_gain and not real_gain
    quiet = all(k in par and k in ser for k in ("summed_mission_hours", "wall_clock_hours", "critical_path_wall_clock_hours"))
    evs = {"parallel": {k: h(par, k) for k in ("summed_mission_hours", "wall_clock_hours", "critical_path_wall_clock_hours")},
           "serialized": {k: h(ser, k) for k in ("summed_mission_hours", "wall_clock_hours", "critical_path_wall_clock_hours")},
           "summed_drops_when_serialized": summed_drop, "critical_path_rises": crit_rise, "wall_rises": wall_rise,
           "summed_keyed_label_calls_serialized_a_gain": naive_gain, "critical_path_keyed_label_calls_it_a_gain": real_gain}
    ok = summed_drop and crit_rise and wall_rise and quiet and not sw["deciders"]
    subs.append(result("seeded-serialization", HELD if ok else BREACH, "seeded", evs, control_fired=mutant_labels,
                       negative_quiet=quiet, reason=None if ok else "serialized arm reads as a gain by summed hours",
                       command="time_accounting over 2 parallel vs 2 serialized seeded missions; a summed-hours labeller is the control"))
    return subs


_C6_ADMISSION_FILES = ("tools/resource_admission.py", "tools/mission_launch_gate.py", "tools/mission_resources.py",
                       "tools/mission_sleep.py", "tools/route_admission.py", "tools/cognitive_admission.py")
_C6_LOCKS = {"flock", "lockf", "locking", "Lock", "RLock", "Semaphore", "BoundedSemaphore"}
_C6_REFUSALS = ("launch_held", "launch_held_cwd", "provider_held", "quota_held", "relay_held", "launch_refused_resources",
                "launch_refused_admission", "launch_preflight_refused", "goal_arm_refused")
_C6_DEADLINE_S = 300 + 600       # gsd_mission.START_DEADLINE_S plus the ten minutes the plan allows


def sweep_admission_primitives(files: dict[str, str]) -> dict:
    """Every wake predicate handed to a sleep, every lock-like primitive in the admission modules, and whether the
    resource refusal runs before the launch claim. A wake that names another mission is a wait-for edge."""
    wakes, locks = [], []
    for rel, src in sorted(files.items()):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                nm = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id if isinstance(n.func, ast.Name) else ""
                if nm in ("_sleep", "sleep_on_change", "entry") and any(isinstance(a, ast.Dict) for a in n.args):
                    for a in n.args:
                        if isinstance(a, ast.Dict):
                            keys = [k.value for k in a.keys if isinstance(k, ast.Constant)]
                            kind = next((v.value for k, v in zip(a.keys, a.values)
                                         if isinstance(k, ast.Constant) and k.value == "kind" and isinstance(v, ast.Constant)), None)
                            if kind is not None:
                                wakes.append({"file": rel, "kind": kind, "keys": sorted(map(str, keys))})
                if rel in _C6_ADMISSION_FILES or rel.endswith("zz_inject.py"):
                    if nm in _C6_LOCKS:
                        locks.append({"file": rel, "primitive": nm, "line": n.lineno})
    return {"wakes": wakes, "locks": locks}


def _c6_wait_for_cycle(graph: dict) -> list | None:
    """A cycle in {mission: [missions it waits on]}, or None."""
    state: dict = {}

    def visit(m, path):
        state[m] = 1
        for w in graph.get(m, []):
            if state.get(w) == 1:
                return path + [m, w]
            if state.get(w) is None:
                c = visit(w, path + [m])
                if c:
                    return c
        state[m] = 2
        return None
    for m in sorted(graph):
        if state.get(m) is None:
            c = visit(m, [])
            if c:
                return c
    return None


def _c6_graph(wakes_of: dict) -> dict:
    """{mission: [ids its wake predicate names]}; only a wake that carries a mission reference adds an edge."""
    return {m: [str(v) for k, v in w.items() if k in ("mission", "missions", "waits_on", "after", "inherited_from")
                for v in (v if isinstance(v, list) else [v])] for m, w in wakes_of.items()}


def attack_6(ctx) -> list[dict]:
    import resource_admission as rsa
    import mission_launch_gate as mlg
    import mission_sleep as msl
    import gsd_mission as gm
    files = {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8", errors="replace") for p in _tools_py()}
    sw = sweep_admission_primitives(files)
    inj = dict(files)
    inj["modules/zz_inject.py"] = ("import fcntl\ndef f(rec):\n    fcntl.flock(1, 2)\n    return _sleep(rec, 'x', {'kind': 'mission', "
                                   "'waits_on': 'm-other'}, 'launch_held')\n")
    csw = sweep_admission_primitives(inj)
    found = any(w["kind"] == "mission" for w in csw["wakes"]) and any(l["primitive"] == "flock" for l in csw["locks"])
    kinds = sorted({w["kind"] for w in sw["wakes"]})
    stray = [w for w in sw["wakes"] if w["kind"] not in msl.WAKE_KINDS
             or any(re.search(r"mission|pred|other|waits", k) for k in w["keys"])]
    lw = next(n for n in ast.walk(ast.parse(files["tools/gsd_mission.py"])) if isinstance(n, ast.FunctionDef) and n.name == "launch_worker")
    seg = ast.get_source_segment(files["tools/gsd_mission.py"], lw) or ""
    order = {"resource_refusal_at": seg.find("rsa.refusal("), "route_admission_at": seg.find("admission_refusal(rec)"),
             "claim_at": seg.find('event="launch_claimed"')}
    ra_tree = ast.parse(files["tools/resource_admission.py"])
    ra_calls = sorted({n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(ra_tree)
                       if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name))})
    reads_missions = [c for c in ra_calls if c in ("load", "list_missions", "ledger_events", "all_missions", "sessions")]
    before = 0 <= order["resource_refusal_at"] < order["claim_at"] and 0 <= order["route_admission_at"] < order["claim_at"]
    deadline_defined = gm.START_DEADLINE_S == 300 and "pending.get(\"deadline\")" in files["tools/gsd_mission.py"]
    ev = {"wake_kinds_on_the_path": kinds, "wake_sites": len(sw["wakes"]), "stray_wakes": stray,
          "lock_like_primitives_in_admission_modules": sw["locks"], "admission_runs_before_the_claim": before, **order,
          "resource_admission_reads_other_missions": reads_missions, "claim_deadline_s": gm.START_DEADLINE_S,
          "launching_branch_reads_deadline": deadline_defined, "control_injected_wait_and_lock_found": found}
    ok = not stray and not sw["locks"] and before and not reads_missions and deadline_defined and len(sw["wakes"]) >= 1
    subs = [result("primitive-sweep", HELD if ok else BREACH, "repo-artefact", ev, control_fired=found, negative_quiet=ok,
                   reason=None if ok else "an admission primitive is held across missions, has no deadline, or waits on another mission",
                   command="ast sweep of wake predicates, lock primitives and the claim order in launch_worker")]
    # hoarding: the pinned prefix, claim by claim
    rows, fr = ctx.rows, ctx.fr
    end = fr._epoch(rows[-1].get("ts")) if rows else None
    by: dict = {}
    for r in rows:
        if fr._mid(r):
            by.setdefault(fr._mid(r), []).append(r)
    claims, late, stuck, outstanding = 0, [], [], []
    for m, rs in by.items():
        for k, r in enumerate(rs):
            if r.get("event") != "launch_claimed":
                continue
            claims += 1
            t0 = fr._epoch(r.get("ts"))
            nxt = rs[k + 1] if k + 1 < len(rs) else None
            t1 = fr._epoch(nxt.get("ts")) if nxt else None
            if t1 is None:
                if t0 is not None and end is not None and end - t0 > _C6_DEADLINE_S:
                    stuck.append(m)
                outstanding.append((t0, end, m))
            else:
                if t0 is not None and t1 - t0 > _C6_DEADLINE_S:
                    late.append(m)
                outstanding.append((t0, t1, m))
    overlap = 0
    for r in rows:
        if r.get("event") in _C6_REFUSALS:
            t = fr._epoch(r.get("ts"))
            if t is not None and any(a is not None and b is not None and a <= t < b and m != fr._mid(r) for a, b, m in outstanding):
                overlap += 1
    refusals = sum(1 for r in rows if r.get("event") in _C6_REFUSALS)
    # control: a refusal rule that treats any other mission's claim as occupied capacity is caused by it
    mutant_blocked = 0
    for r in rows:
        if r.get("event") in _C6_REFUSALS:
            t = fr._epoch(r.get("ts"))
            if t is not None and any(a is not None and b is not None and a <= t < b and m != fr._mid(r) for a, b, m in outstanding):
                mutant_blocked += 1
    # an outstanding claim is counted by the mutant as a hold whenever a claim sits open: a seeded open claim shows it
    seeded_open = [(0.0, 10_000.0, "m-a")]
    seeded_ref = [(5.0, "m-b")]
    mutant_seeded = sum(1 for t, m in seeded_ref if any(a <= t < b and m != x for a, b, x in seeded_open))
    ev = {"pin_rows": len(rows), "claims": claims, "deadline_plus_ten_min_s": _C6_DEADLINE_S, "claims_followed_up_late": len(late),
          "claims_never_followed_up": len(stuck), "refusal_rows": refusals, "refusal_rows_inside_another_missions_open_claim": overlap,
          "refusal_code_reads_other_missions": reads_missions, "seeded_open_claim_blocks_other_under_mutant": mutant_seeded}
    caused = bool(overlap) and bool(reads_missions)
    bad = bool(stuck) or caused
    subs.append(result("hoarding", BREACH if bad else HELD, "GEX44-host-readonly", ev, control_fired=mutant_seeded == 1 and claims > 0,
                       negative_quiet=not stuck, reason="a claim is outstanding with no follow-up, or a refusal is caused by another claim" if bad else None,
                       command="pair launch_claimed with the next row of the same mission over the pinned prefix; read the refusal code for any other-mission input"))
    # deadlock: three seeded missions held by the real refusals, released by the real resource delta
    recs = {f"m-{c}{c}{c}{c}": {"mission_id": f"m-{c}{c}{c}{c}", "epoch": 1, "state": "PREPARED"} for c in "abc"}
    state = {"v": "NOT_READY"}
    wakes_of, held_now, held_after = {}, 0, 0
    with attr_patch(mlg, "preflight", lambda now: {"verdict": state["v"], "reasons": ["mem low"], "unmeasured": []}), \
            attr_patch(mlg, "enabled", lambda: True), attr_patch(mlg, "preflight_enabled", lambda: True):
        for m, rec in recs.items():
            ref = mlg.refusal(rec, "launch", 100.0)
            if ref and ref.get("refuse"):
                held_now += 1
                wakes_of[m] = ref["sleep"]["wake"]
        state["v"] = "READY"
        for m in reversed(list(recs)):
            ref = mlg.refusal(recs[m], "launch", 200.0)
            if ref and ref.get("refuse"):
                held_after += 1
    saved_env = os.environ.pop("CPP_RESOURCE_ADMISSION", None)       # the switch is off for the harness; the delta is judged with it on
    try:
        low = rsa.refusal("top-level-worker", reader=lambda: {"available_mb": 10})
        high = rsa.refusal("top-level-worker", reader=lambda: {"available_mb": 10 ** 6})
    finally:
        if saved_env is not None:
            os.environ["CPP_RESOURCE_ADMISSION"] = saved_env
    graph = _c6_graph(wakes_of)
    cycle = _c6_wait_for_cycle(graph)
    cyc_a = {"m-aaaa": {"inherited_from": "m-bbbb"}, "m-bbbb": {"inherited_from": "m-cccc"}, "m-cccc": {"inherited_from": "m-aaaa"}}
    mutant_cycle = _c6_wait_for_cycle(_c6_graph(cyc_a))
    import provider_breaker as pb
    loop = {"m-aaaa": {"mission_id": "m-aaaa", "renewed_from": "m-bbbb"}, "m-bbbb": {"mission_id": "m-bbbb", "renewed_from": "m-aaaa"}}
    with attr_patch(pb, "enabled", lambda: True):
        lineage_loop = pb.lineage_hold(loop["m-aaaa"], 100.0, load=lambda i: loop[i])
    ev = {"held_under_preflight_not_ready": held_now, "held_after_ready_in_reverse_order": held_after, "wake_kinds_seen": sorted({w.get("kind") for w in wakes_of.values()}),
          "wait_for_edges": sum(len(v) for v in graph.values()), "wait_for_cycle": cycle, "resource_refusal_low_memory": (low or {}).get("verdict"),
          "resource_refusal_after_delta": high, "renewed_from_loop_ends_without_hold": lineage_loop is None,
          "mutant_wait_for_cycle_found": mutant_cycle is not None}
    ok = held_now == 3 and held_after == 0 and cycle is None and low is not None and high is None and lineage_loop is None
    subs.append(result("deadlock", HELD if ok else BREACH, "seeded", ev, control_fired=mutant_cycle is not None, negative_quiet=cycle is None,
                       reason=None if ok else "a hold does not clear on the resource delta, or the wait-for graph has a cycle",
                       command="3 seeded missions refused by mission_launch_gate, released by flipping the preflight verdict; wait-for graph from the real wake predicates"))
    return subs


# --------------------------------------------------------------------------------------------------- claim 15
_C15_FILES = (".planning/workstreams/flow-compression/STATE.md", ".planning/workstreams/flow-compression/RESUMPTION_FILE.md",
              "RESUMPTION_FILE.md", PHASE7.rsplit("/", 1)[0] + "/08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate/08-CONTEXT.md",
              "vault/specs/flow-compression.md")


def c15_lists(files: dict[str, str], minimum=15) -> list[dict]:
    """Numbered lists that count at least `minimum` consecutive items from 1; the only place a fifteenth claim could live."""
    out = []
    for rel, text in sorted(files.items()):
        run, best = 0, 0
        for line in text.splitlines():
            m = re.match(r"\s*(\d+)[.)]\s+\S", line)
            if m and int(m.group(1)) == run + 1:
                run += 1
            elif m and int(m.group(1)) == 1:
                run = 1
            else:
                run = 0 if line.strip() else run
            best = max(best, run)
        if best >= minimum:
            out.append({"file": rel, "items": best})
    return out


def attack_15(ctx) -> list[dict]:
    files = {rel: (ROOT / rel).read_text(encoding="utf-8", errors="replace") for rel in _C15_FILES if (ROOT / rel).is_file()}
    found = c15_lists(files)
    planted = dict(files)
    planted["planted.md"] = "\n".join(f"{i}. hypothesis number {i}" for i in range(1, 16))
    ctl = any(f["file"] == "planted.md" for f in c15_lists(planted))
    return [result("claim-text-search", UNMEASURED, "repo-artefact",
                   {"files_searched": sorted(files), "files_missing": sorted(set(_C15_FILES) - set(files)),
                    "lists_of_15_or_more": found, "claim_text_found": bool(found)},
                   control_fired=ctl, negative_quiet=True,
                   reason=C15_REASON if not found else f"{C15_REASON}; a list of 15+ exists but no sentence is attributable to the Owner",
                   command="regex a numbered list of 15+ consecutive items in STATE, RESUMPTION (workstream+root), 08-CONTEXT, the spec; a planted 15-item list is the control")]


# --------------------------------------------------------------------------------------------------- claim 12
def _c12_ts(x):
    try:
        return datetime.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def c12_bias(rows: list[dict], pin_end: float) -> dict:
    """Independent of flow_replay: headline ends open missions at the pin end, bounded ends them at their last row."""
    by: dict = {}
    for r in rows:
        k, t = r.get("mission_id") or r.get("session_id"), _c12_ts(r.get("ts"))
        if not k or t is None:
            continue
        m = by.setdefault(k, {"first": t, "last": t, "terminal": False})
        m["first"], m["last"] = min(m["first"], t), max(m["last"], t)
        if r.get("event") in ("mission_halted", "mission_completed") or r.get("state") in ("COMPLETED", "HALTED", "ORPHANED"):
            m["terminal"] = True
    head = sum((m["last"] if m["terminal"] else pin_end) - m["first"] for m in by.values()) / 3600
    bounded = sum(m["last"] - m["first"] for m in by.values()) / 3600
    opn = [m for m in by.values() if not m["terminal"]]
    return {"missions": len(by), "open": len(opn), "headline_h": round(head, 3), "bounded_h": round(bounded, 3),
            "bias_h": round(head - bounded, 3), "bias_ratio": round((head - bounded) / bounded, 3) if bounded else None}


def _c12_seed(with_terminals: bool) -> tuple[list[dict], float]:
    t0 = datetime.datetime(2026, 10, 1, tzinfo=datetime.timezone.utc).timestamp()
    def row(m, h, ev):
        return {"mission_id": m, "ts": datetime.datetime.fromtimestamp(t0 + h * 3600, datetime.timezone.utc).isoformat(), "event": ev}
    rows = [row("m-a", 0, "launch_claimed"), row("m-a", 1, "cost_mark"), row("m-z", 0, "launch_claimed"),
            row("m-z", 10, "mission_completed")]
    if with_terminals:
        rows.insert(2, row("m-a", 2, "mission_completed"))
    return rows, t0 + 10 * 3600


def attack_12(ctx) -> list[dict]:
    pin_end = max(t for t in (_c12_ts(r.get("ts")) for r in ctx.rows) if t is not None)
    real = c12_bias(ctx.rows, pin_end)
    acct = ctx.fr.time_accounting(ctx.rows, {})["summed_mission_hours"]
    seeded_full, seeded_cut = c12_bias(*_c12_seed(True)), c12_bias(*_c12_seed(False))
    rep = load_replay(ctx)["raw"]
    vt = (rep.get("verdict_totals") or {}).get("data") or {}
    measured, apart = sum((vt.get("measured") or {}).values()), vt.get("unmeasured_apart")
    cov = (rep.get("coverage") or {}).get("data") or {}
    tol = ctx.fr.FAITHFUL_TOL
    agrees = abs(real["headline_h"] - acct["hours"]) <= 0.01 * acct["hours"]
    breach = real["bias_ratio"] is not None and real["bias_ratio"] > tol
    ev = {"independent": real, "flow_replay_summed_h": acct["hours"], "independent_matches_flow_replay": agrees,
          "tolerance": tol, "bias_exceeds_tolerance": breach,
          "unmeasured_kept_apart": {"measured_total": measured, "unmeasured_apart": apart,
                                    "rows_mapped_of_total": [cov.get("mapped_to_slice"), cov.get("failure_rows_total")]},
          "seeded_complete": seeded_full, "seeded_terminals_removed": seeded_cut}
    fired = seeded_full["bias_h"] == 0 and seeded_cut["bias_h"] == 9.0
    return [result("missing-telemetry", BREACH if breach else HELD, "seeded", ev, control_fired=fired,
                   negative_quiet=seeded_full["bias_h"] == 0 and agrees,
                   reason=(f"summed mission-hours are {real['bias_h']} h over the bounded figure ({real['bias_ratio']:.0%}): "
                           f"{real['open']} open missions are ended at the pin, not at their last row") if breach else None,
                   command="recompute mission spans with my own terminal predicate; seeded complete ledger bias 0, terminals removed bias 9 h")]


# --------------------------------------------------------------------------------------------------- claim 3
def c3_span(stop_champion: float, stop_challenger: float, resolution: dict) -> dict:
    """Mission span under each arm: a fixed-time resolution ends both at the same moment; a notify-delay resolution
    ends each arm `delay` seconds after its own stop, so only that kind can turn an earlier stop into a shorter span."""
    end = lambda stop: resolution["t"] if resolution["kind"] == "fixed_time" else stop + resolution["delay"]
    return {"champion_end": end(stop_champion), "challenger_end": end(stop_challenger),
            "span_delta_s": end(stop_challenger) - end(stop_champion)}


def attack_3(ctx) -> list[dict]:
    rep = load_replay(ctx)["raw"]
    s2 = [i for i in (rep.get("incidents") or {}).get("data", []) if i.get("slice") == "S2"]
    av = ((rep.get("avoidable_idle") or {}).get("data")) or {}
    seeded_fixed = c3_span(1000.0, 100.0, {"kind": "fixed_time", "t": 5000.0})
    seeded_notify = c3_span(1000.0, 100.0, {"kind": "notify", "delay": 60.0})
    fired = seeded_fixed["span_delta_s"] == 0 and seeded_notify["span_delta_s"] == -900.0
    if len(s2) != 1:
        return [result("span-effect", UNMEASURED, "repo-artefact", {"s2_incidents": len(s2)}, control_fired=fired,
                       reason=f"{len(s2)} S2 incidents; the span effect needs exactly the one recorded", command="07-REPLAY.json incidents slice S2")]
    inc = s2[0]
    mine = [r for r in ctx.rows if r.get("mission_id") == inc["mission_id"]]
    last = mine[-1]
    released = [r for r in mine if r.get("event") == "mission_completed"]
    exo = last.get("event") == "mission_halted" and bool(re.search(r"owner dead|older than|budget", str(last.get("reason"))))
    ev = {"incident": {k: inc.get(k) for k in ("id", "mission_id", "kind", "seam", "verdict", "delta_s", "hold_window_s", "rows")},
          "challenger_stops_earlier_by_s": inc["delta_s"], "mission_end": {"event": last.get("event"), "ts": last.get("ts"), "reason": last.get("reason")},
          "unblock_before_end": bool(released), "resolution_exogenous": exo,
          "avoidable_idle_h_before_after": [av.get("avoidable_h_before"), av.get("avoidable_h_after")],
          "seeded_fixed_time_resolution": seeded_fixed, "seeded_notify_resolution": seeded_notify,
          "reading": "the earlier stop is a worker interval not spent; the mission ended by timeout, so its span is the same in both arms"}
    return [result("span-effect", UNMEASURED, "repo-artefact", ev, control_fired=fired, negative_quiet=seeded_fixed["span_delta_s"] == 0,
                   reason="one S2 incident and its resolution is exogenous: the span effect of an earlier stop is not observable"
                   if exo else "one S2 incident and no recorded resolution",
                   command="07-REPLAY.json S2 incident + the mission's own ledger rows; seeded fixed-time vs notify-delay resolutions are the control")]


# --------------------------------------------------------------------------------------------------- claim 5
C5_WINDOW_H, C5_SHARE = 24.0, 0.25      # my own definition of "stale too quickly" (recorded as a decision); sensitivity is printed
C5_MIN_N = 10


def c5_rate(items: list[dict], window_h=C5_WINDOW_H) -> dict:
    """items: {set_at, superseded_at|None}. An item with no set_at cannot be timed: it is UNMEASURED, not a zero."""
    timed = [i for i in items if i.get("set_at") is not None]
    fast = [i for i in timed if i.get("superseded_at") is not None and 0 <= (i["superseded_at"] - i["set_at"]) / 3600 <= window_h]
    return {"admitted": len(items), "timed": len(timed), "untimed": len(items) - len(timed), "superseded_fast": len(fast),
            "share": round(len(fast) / len(timed), 4) if timed else None}


def attack_5(ctx) -> list[dict]:
    sup = {r["mission_id"]: _c12_ts(r.get("ts")) for r in ctx.rows if r.get("event") == "mission_superseded"}
    items = [{"mission_id": m, "set_at": (r["wu_packet"] or {}).get("set_at"), "superseded_at": sup.get(m)}
             for m, r in sorted(ctx.records.items()) if isinstance(r, dict) and r.get("wu_packet")]
    real = c5_rate(items)
    refusals = sum(1 for r in ctx.rows if "packet" in str(r.get("event")) and "refus" in str(r.get("event")))
    sens = {str(w): c5_rate(items, w)["share"] for w in (1.0, 6.0, 24.0, 72.0, 168.0)}
    fast = c5_rate([{"set_at": 0.0, "superseded_at": 1800.0}] * 12)
    slow = c5_rate([{"set_at": 0.0, "superseded_at": 90 * 3600.0}] * 12)
    untimed = c5_rate([{"set_at": None, "superseded_at": 5.0}] * 3)
    fired = fast["share"] >= C5_SHARE > slow["share"] and untimed["share"] is None
    ev = {"rule": f"stale-fast = superseded within {C5_WINDOW_H} h of packet admission; claim proven at a share >= {C5_SHARE}",
          "real": real, "supersessions_in_pin": len(sup), "packet_refusal_rows": refusals, "share_by_window_h": sens,
          "seeded_fast": fast, "seeded_slow": slow, "seeded_untimed": untimed,
          "live_evidence_not_used": "Owner: AMR packets r2/r4 re-targeted closed phases 03 and 07 (host recovery dirs mutate; not reproducible, so not a verdict input)"}
    if real["timed"] < C5_MIN_N:
        return [result("packet-staleness", UNMEASURED, "seeded", ev, control_fired=fired, reason=f"only {real['timed']} timed packets (< {C5_MIN_N})",
                       command="wu_packet records in the pin x mission_superseded rows")]
    breach = real["share"] >= C5_SHARE
    if breach:
        return [result("packet-staleness", BREACH, "seeded", ev, control_fired=fired, negative_quiet=slow["share"] == 0.0,
                       reason=f"{real['superseded_fast']} of {real['timed']} packets superseded within {C5_WINDOW_H} h",
                       command="share of admitted wu_packets superseded within 24 h; seeded fast/slow/untimed sets are the controls")]
    # supersession is one staleness mode; the Owner's live evidence (a packet re-targeting a closed phase) is another that the
    # pin cannot observe, so a low supersession share cannot hold the claim
    return [result("packet-staleness", UNMEASURED, "seeded", ev, control_fired=fired, negative_quiet=slow["share"] == 0.0,
                   reason=f"supersession share {real['share']} is under {C5_SHARE} but closed-phase re-targeting (Owner live evidence) is not observable in the pin",
                   command="share of admitted wu_packets superseded within 24 h; seeded fast/slow/untimed sets are the controls")]


# --------------------------------------------------------------------------------------------------- claim 1
_C1_FILES = tuple(f"{PHASE7.rsplit('/', 1)[0]}/{p}" for p in (
    "01/01-EVIDENCE.md", "01/01-01-SUMMARY.md", "01/01-VERIFICATION.md",
    "07-s7-historical-replay-champion-challenger/07-REPLAY.md",
    "08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate/08-CONTEXT.md")) + ("vault/specs/flow-compression.md",)
_C1_CAUSAL = re.compile(r"\b(caus(?:e|es|ed|al|ality)|because|due to|leads? to|led to|results? in|reduc(?:e|es|ed)|improv(?:e|es|ed)|"
                        r"prov(?:e|es|en)|wins?|loses?|better|worse)\b", re.I)
_C1_QUALIFIER = re.compile(r"confound|correlat|observational|not proven|unproven|does not prove|not a cause|no causal", re.I)


def c1_scan(files: dict[str, str]) -> list[dict]:
    """A comparative-effect paragraph names rotation and compaction, carries two or more medians and a causal verb.
    It is qualified when it or a neighbouring paragraph says confounded / correlation / not proven."""
    hits = []
    for rel, text in sorted(files.items()):
        paras = re.split(r"\n\s*\n", text)
        for i, p in enumerate(paras):
            if (re.search(r"rotat", p, re.I) and re.search(r"compact", p, re.I) and len(re.findall(r"median\s+[\d.]+", p, re.I)) >= 2
                    and _C1_CAUSAL.search(p)):
                window = " ".join(paras[max(0, i - 1):i + 2])
                hits.append({"file": rel, "paragraph": i, "causal_verbs": sorted({m.lower() for m in _C1_CAUSAL.findall(p)}),
                             "qualified": bool(_C1_QUALIFIER.search(window))})
    return hits


def _med(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def c1_naive_vs_stratified(samples: list[tuple]) -> dict:
    """samples: (arm, stratum, minutes). A comparison across arms is causal only if it survives holding the stratum fixed."""
    arm = lambda a, s=None: [m for (x, st, m) in samples if x == a and (s is None or st == s)]
    naive = _med(arm("rotation")) - _med(arm("compaction"))
    diffs = [_med(arm("rotation", s)) - _med(arm("compaction", s)) for s in sorted({st for (_, st, _) in samples})
             if arm("rotation", s) and arm("compaction", s)]
    return {"naive_diff_min": naive, "stratified_diff_min": sum(diffs) / len(diffs) if diffs else None, "strata": len(diffs)}


def attack_1(ctx) -> list[dict]:
    files = {rel: (ROOT / rel).read_text(encoding="utf-8", errors="replace") for rel in _C1_FILES if (ROOT / rel).is_file()}
    hits = c1_scan(files)
    stripped = {rel: _C1_QUALIFIER.sub("", t) for rel, t in files.items()}
    ctl_hits = c1_scan(stripped)
    fired = bool(hits) and all(h["qualified"] for h in hits) and any(not h["qualified"] for h in ctl_hits)
    unq = [h for h in hits if not h["qualified"]]
    subs = [result("causal-wording", BREACH if unq else (HELD if hits else UNMEASURED), "repo-artefact",
                   {"files_scanned": sorted(files), "comparative_effect_paragraphs": hits, "unqualified": unq,
                    "control_qualifiers_removed_unqualified": [h for h in ctl_hits if not h["qualified"]]},
                   control_fired=fired, negative_quiet=not unq,
                   reason=("an effect comparison is stated without a confound qualifier" if unq else
                           None if hits else "no comparative effect sentence exists to judge"),
                   command="paragraphs naming rotation+compaction with two medians and a causal verb; the same files with the qualifiers deleted are the control")]
    s1 = (((load_replay(ctx)["raw"].get("by_slice") or {}).get("data") or {}).get("S1")) or {}
    naive_conf = c1_naive_vs_stratified([("rotation", "easy", 1.0)] * 9 + [("rotation", "hard", 9.0)] * 1 + [("compaction", "easy", 1.0)] * 1
                                        + [("compaction", "hard", 9.0)] * 9)
    simpson = naive_conf["naive_diff_min"] < -3 and abs(naive_conf["stratified_diff_min"]) < 1e-9
    subs.append(result("causal-effect", UNMEASURED, "seeded",
                       {"s1_replay_verdicts": s1, "phase1_comparison": "rotation n=35 median 3.2 min vs compaction n=52 median 4.8 min, stated confounded in 01-EVIDENCE.md",
                        "strata_recorded": False, "seeded_confounded_arms": naive_conf},
                       control_fired=simpson, negative_quiet=True,
                       reason="rotation and compaction were not randomised and no stratum is recorded, so no causal effect is estimable; S1 replay holds only UNMEASURED",
                       command="07-REPLAY.json S1 + a seeded confounded sample where the naive gap vanishes once stratified"))
    return subs


# --------------------------------------------------------------------------------------------------- claim 2
C2_MISSION = "m-3d5f0a27e41d"
C2_PROJECTS = Path.home() / ".claude" / "projects" / "-home-kobii-missions-flow-compression"


def c2_verdict(rot: list, lo: list, hi: list, min_n=3) -> dict:
    if len(rot) < min_n or len(lo) < min_n:
        return {"verdict": UNMEASURED, "reason": f"n too small (rotation {len(rot)}, compaction {len(lo)}; need {min_n})"}
    r, l, h = _med(rot), _med(lo), _med(hi)
    if r <= l:
        return {"verdict": HELD, "reason": None, "medians": [r, l, h]}
    if r > h:
        return {"verdict": BREACH, "reason": "rotation first-call context exceeds even the pre-compaction context", "medians": [r, l, h]}
    return {"verdict": UNMEASURED, "reason": "rotation lies between the compaction lower bound and ceiling", "medians": [r, l, h]}


def _c2_calls(path: Path, until: float | None):
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        u = (r.get("message") or {}).get("usage") if r.get("type") == "assistant" and isinstance(r.get("message"), dict) else None
        t = _c12_ts(r.get("timestamp"))
        if u and t is not None and (until is None or t <= until) and (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)) > 0:
            out.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
    return out


def c2_extract(ctx) -> dict:
    import gsd_epoch as ge
    eps = [e for e in ge.epochs(C2_MISSION, ctx.rows) if e.get("end")]
    rot, lo, hi, per = [], [], [], []
    for e in eps:
        f = C2_PROJECTS / f"{e['session']}.jsonl"
        if not f.is_file():
            per.append({"epoch": e["epoch"], "transcript": "absent"})
            continue
        calls = _c2_calls(f, _c12_ts(e["end"]))
        drops = [i for i in range(1, len(calls)) if calls[i - 1] >= 100_000 and calls[i] <= 0.7 * calls[i - 1]]
        if e.get("start_cause") == "CONTEXT_ROTATION" and calls:
            rot.append(calls[0])
        for i in drops:
            lo.append(calls[i]); hi.append(calls[i - 1])
        per.append({"epoch": e["epoch"], "cause": e.get("start_cause"), "calls": len(calls), "first_call_ctx": calls[0] if calls else None,
                    "compaction_drops": len(drops), "ledger_compactions": e.get("compactions")})
    return {"rotation": rot, "comp_lo": lo, "comp_hi": hi, "epochs": per}


def attack_2(ctx) -> list[dict]:
    ctl_breach = c2_verdict([300_000] * 3, [50_000] * 3, [100_000] * 3)
    ctl_held = c2_verdict([40_000] * 3, [50_000] * 3, [100_000] * 3)
    ctl_mid = c2_verdict([70_000] * 3, [50_000] * 3, [100_000] * 3)
    fired = (ctl_breach["verdict"], ctl_held["verdict"], ctl_mid["verdict"]) == (BREACH, HELD, UNMEASURED)
    if not C2_PROJECTS.is_dir():
        return [result("rehydration-cost", UNMEASURED, "GEX44-host-readonly", {"transcripts": str(C2_PROJECTS)}, control_fired=fired,
                       reason="transcript directory absent", command="per-epoch first-call context from the host transcripts")]
    x = c2_extract(ctx)
    v = c2_verdict(x["rotation"], x["comp_lo"], x["comp_hi"])
    ev = {"mission": C2_MISSION, "rotation_first_call_ctx": x["rotation"], "compaction_post_ctx_lower_bound": x["comp_lo"],
          "compaction_pre_ctx_ceiling": x["comp_hi"], "medians_rot_lo_hi": v.get("medians"), "per_epoch": x["epochs"],
          "seeded": {"rotation_dearer": ctl_breach, "rotation_cheaper": ctl_held, "between": ctl_mid},
          "ledger_compactions_in_closed_epochs": sum(e.get("ledger_compactions") or 0 for e in x["epochs"]),
          "instrument": "compactions are inferred from a >=30% fall in per-call context (transcripts hold no compaction marker); costs are tokens in context, not dollars"}
    return [result("rehydration-cost", v["verdict"], "GEX44-host-readonly", ev, control_fired=fired, negative_quiet=ctl_held["verdict"] == HELD,
                   reason=v["reason"], command="first-call context of each rotation epoch vs post/pre-drop context of inferred compactions, epochs closed at the pin")]


ATTACKS = {1: attack_1, 2: attack_2, 5: attack_5, 3: attack_3, 15: attack_15, 12: attack_12, 6: attack_6, 13: attack_13, 11: attack_11, 9: attack_9, 4: attack_4, 7: attack_7, 8: attack_8, 10: attack_10, 14: attack_14}


# --------------------------------------------------------------------------------------------------- run + report
def command_tag(claims, pin_path, json_path, md_path) -> str:
    c = ",".join(str(i) for i in claims)
    return (f"python3 tools/redteam_s9.py run --pin {pin_path} --claims {c if len(claims) < 15 else 'all'}"
            f" --json {json_path} --md {md_path}")


def run_claims(ctx, claims, *, probe=True) -> dict:
    out = {}
    roots = host_roots(ctx.pin)
    with (WriteProbe(roots) if probe else contextlib.nullcontext()) as wp:
        for cid in claims:
            fn = ATTACKS.get(cid)
            if fn is None:
                subs = [result(n, UNMEASURED, "repo-artefact", {}, reason="no_attack_implemented") for n in SUBATTACKS[cid]]
            else:
                subs = fn(ctx)
            declared = SUBATTACKS[cid]
            got = [s["name"] for s in subs]
            if got != declared:
                raise AssertionError(f"claim {cid}: ran sub-attacks {got}, declared {declared}")
            j = judge(subs)
            out[cid] = {"id": cid, "claim": CLAIMS[cid], "verdict": j["verdict"], "reason": j["reason"],
                        "planes": sorted({s["plane"] for s in j["subs"]}), "subs": j["subs"]}
    writes = list(getattr(wp, "writes", []))
    return {"claims": out, "host_writes": writes, "host_opens_observed": getattr(wp, "opens", 0)}


def build_report(ctx, ran: dict, command: str, generated_at=None) -> dict:
    rep = {"schema": SCHEMA, "command": command, "pin_sha256": ctx.pin["sha256"], "pin_rows": len(ctx.rows),
           "verdicts_closed_set": list(VERDICTS), "claims": [ran["claims"][i] for i in sorted(ran["claims"])],
           "host_writes_observed": ran["host_writes"]}
    rep = scrub(rep)
    rep["generated_at"] = generated_at
    return rep


def render_md(rep: dict) -> str:
    L = [f"# S9 red team: the 15 Owner claims", "",
         f"Command: `{rep['command']}`  ", f"Pin sha256: `{rep['pin_sha256']}` ({rep['pin_rows']} rows)  ",
         f"Host write opens observed: {len(rep['host_writes_observed'])}", "",
         "Verdicts are HELD / BREACH / UNMEASURED. HELD means the attack failed on the real subject and a guard-removed "
         "control showed it could succeed. There is no PASS.", "",
         "| # | Claim | Verdict | Planes | Sub-verdicts |", "|---|---|---|---|---|"]
    for c in rep["claims"]:
        sv = "; ".join(f"{s['name']}={s['verdict']}" for s in c["subs"])
        L.append(f"| {c['id']} | {c['claim']} | **{c['verdict']}** | {', '.join(c['planes'])} | {sv} |")
    L.append("")
    for c in rep["claims"]:
        L += [f"## Claim {c['id']}: {c['claim']}", f"Verdict: **{c['verdict']}**" + (f" ({c['reason']})" if c["reason"] else ""), ""]
        for s in c["subs"]:
            L.append(f"- `{s['name']}` {s['verdict']} [{s['plane']}] control_fired={s['control_fired']} "
                     f"negative_quiet={s['negative_control_quiet']}" + (f" reason: {s['reason']}" if s["reason"] else ""))
            L.append(f"  - command: `{s['command']}`")
            L.append(f"  - evidence: `{json.dumps(s['evidence'], sort_keys=True, default=str)[:700]}`")
        if c["verdict"] == BREACH:
            br = [s for s in c["subs"] if s["verdict"] == BREACH]
            L += ["", f"### FC-12 incident draft (claim {c['id']})",
                  f"- symptom: {br[0]['reason']}", "- root cause: see the evidence above",
                  "- earliest discoverable point: the red-team attack named above, runnable at any commit",
                  "- repair: none in this plan; a gap-closure plan owns repairs",
                  f"- test: the V-S9RT-C{c['id']:02d} gates", "- pattern: a guard asserted by prose and never attacked"]
        L.append("")
    L += ["## Claim 15", f"UNMEASURED: {C15_REASON}. No text is invented for it.", ""]
    L += ["## LAPTOP-ONLY (not observed on this plane)", "- the laptop gsd-core install", "- live hooks and laptop ledger facts", ""]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="redteam_s9")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--pin", required=True)
    r.add_argument("--claims", default="all")
    r.add_argument("--json", required=True)
    r.add_argument("--md", required=True)
    a = ap.parse_args(argv)
    import flow_replay as fr
    claims = sorted(CLAIMS) if a.claims == "all" else sorted({int(x) for x in a.claims.split(",")})
    if any(c not in CLAIMS for c in claims):
        print(f"unknown claim in {a.claims}", file=sys.stderr)
        return 2
    try:
        ctx = Ctx(a.pin)
        ran = run_claims(ctx, claims)
    except fr.Inconclusive as exc:
        print(f"S9RT_INCONCLUSIVE {exc}", file=sys.stderr)
        return 2
    if ran["host_writes"]:
        print(f"S9RT_HOST_WRITE {ran['host_writes']}", file=sys.stderr)
        return 3
    rep = build_report(ctx, ran, command_tag(claims, a.pin, a.json, a.md),
                       datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    Path(a.json).write_text(json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    Path(a.md).write_text(render_md(rep), encoding="utf-8")
    print("S9RT_VERDICTS " + " ".join(f"{c['id']}={c['verdict']}" for c in rep["claims"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
