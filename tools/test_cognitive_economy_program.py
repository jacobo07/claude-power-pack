#!/usr/bin/env python
"""test_cognitive_economy_program.py -- the done-gate of PLAN-COGNITIVE-ECONOMY-PROGRAM.

One command decides whether the cognitive-economy campaign may be called DONE:

    python tools/test_cognitive_economy_program.py --final

Authority: `vault/programs/cognitive-economy/ledger.json` (committed in git). Every pillar
A-T must be in a terminal state, each terminal backed by the evidence ITS KIND needs,
every evidence pointer must resolve, the pre-registration (`frozen`) must be identical
to its copy at the freeze commit, savings must say realized / upper bound / unknown with
a displacement status, and every IMPLEMENTED pillar's declared gate commands are RE-RUN
here, at one instant, and must exit 0.

Why gates are re-run here and not through the Goal spine (phase-4 audit G1-G4,
vault/audits/cognitive-economy-phase4-audit.md): the spine pins every verdict to the
whole repo's HEAD^{tree} when the scope is clean, so in a shared checkout any peer commit
invalidates every banked verdict; a bound mission is an open epoch that blocks closure;
`status --json` carries no obligation list. Re-running the gates in one pass needs no
tree pin: the verdict is about the tree the final run sees.

Why the ledger layer exists at all: "deferred to an owner" would otherwise close any
pillar. Here a deferral must name an owner that exists and a handoff that landed; a
demotion from a pre-registered IMPLEMENT needs a falsification artifact; prose
deferrals ("later", "TODO") are refused.

Modes:
  --final        the done-gate (exit 0 only when everything holds)
  --status       progress report; exit 1 if a recorded terminal is malformed
  --pillar X     one pillar's clauses + its gates (exit 0 when that pillar is proven)
  --selftest     drives every clause's red branch (each mutant must die by ITS clause,
                 the clean fixture GREEN) plus a real-subprocess control of the gate
                 runner; --final runs it too

Gate commands are argv lists, never shell strings: `["python", "tools/x.py", ...]` or
`["python", "vault/.../y.py", ...]`, a script inside this repo, never this verifier.

File hashes are of LF-normalized content (the git blob form): a CRLF checkout of the
same file must not read as a different file.

Exit codes: 0 pass, 1 fail, 2 could not run.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SELF_REL = "tools/test_cognitive_economy_program.py"
LEDGER_REL = "vault/programs/cognitive-economy/ledger.json"
FROZEN_AT_REL = "vault/programs/cognitive-economy/FROZEN_AT"
PILLARS = [chr(c) for c in range(ord("A"), ord("T") + 1)]
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
GATE_TIMEOUT_S = 1800

TERMINALS = {
    "IMPLEMENTED_AND_VERIFIED", "MERGED_INTO_EXISTING_OWNER",
    "FALSIFIED_OR_REJECTED_BY_EVIDENCE", "DEFERRED_STRONGER_OWNER",
    "AUTHORIZATION_BOUND", "EXTERNAL_BLOCKED", "RESEARCH_INSUFFICIENT_EVIDENCE",
}
# Evidence kinds each terminal needs (all of one inner tuple, any one tuple).
REQUIRED_KINDS = {
    "IMPLEMENTED_AND_VERIFIED": [("gate", "prg")],
    # A merge or deferral is a HANDOFF that landed: a per-pillar handoff file naming the
    # owner, committed AFTER the freeze (audit G7: "owner path + any ancestor commit" was
    # satisfiable by HEAD and a path that existed before the campaign began).
    "MERGED_INTO_EXISTING_OWNER": [("owner", "handoff")],
    "FALSIFIED_OR_REJECTED_BY_EVIDENCE": [("measurement",)],
    "DEFERRED_STRONGER_OWNER": [("owner", "handoff")],
    "AUTHORIZATION_BOUND": [("owner_decision",)],
    "EXTERNAL_BLOCKED": [("blocker",)],
    "RESEARCH_INSUFFICIENT_EVIDENCE": [("measurement",)],
}
FILE_KINDS = ("file", "measurement", "falsification", "prg", "owner_decision", "handoff")
HANDOFF_DIR = "vault/programs/cognitive-economy/handoffs/"
SAVING_STATUS = {"realized", "upper_bound", "unknown"}
DISPLACEMENT = {"settled", "unknown", "not_applicable"}
DEFERRAL_PROSE = re.compile(r"(?i)\b(later|todo|tbd|future work|eventually|someday)\b")
SAFE_ARG = re.compile(r"^[A-Za-z0-9_./:=,@+-]*$")


def lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, "-C", str(REPO), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def gate_argv_problem(argv) -> str | None:
    """Why a declared gate may not run, or None. Static: no process is started."""
    if not isinstance(argv, list) or len(argv) < 2 or argv[0] != "python":
        return "gate must be an argv list starting with 'python' and a script"
    script = str(argv[1]).replace("\\", "/")
    if not (script.startswith("tools/") or script.startswith("vault/")) or ".." in script:
        return f"gate script {script!r} must live under tools/ or vault/ in this repo"
    if script == SELF_REL:
        return "a gate may not invoke the done-gate itself (recursion)"
    if not (REPO / script).is_file():
        return f"gate script {script} does not exist"
    bad = [a for a in argv[2:] if not SAFE_ARG.match(str(a))]
    if bad:
        return f"gate arguments carry unsafe characters: {bad[:2]}"
    return None


class Resolver:
    """Answers 'does this pointer exist / does this gate pass'. Faked in the selftest."""

    def commit_reachable(self, ref: str) -> bool:
        if not re.fullmatch(r"[0-9a-f]{7,40}", ref or ""):
            return False
        if _git("cat-file", "-e", f"{ref}^{{commit}}").returncode != 0:
            return False
        return _git("merge-base", "--is-ancestor", ref, "HEAD").returncode == 0

    @staticmethod
    def _path(rel: str) -> Path:
        """Repo-relative, or absolute / ~-prefixed for owners outside the repo
        (e.g. ~/.claude/commands/cpp-compound.md, audit G8)."""
        p = Path(rel).expanduser()
        return p if p.is_absolute() else REPO / rel

    def file_sha(self, rel: str):
        p = self._path(rel)
        return lf_sha256(p) if p.is_file() else None

    def path_exists(self, rel: str) -> bool:
        return bool(rel) and self._path(rel).exists()

    def file_text(self, rel: str) -> str:
        p = self._path(rel)
        return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""

    def frozen_sha(self):
        fa = REPO / FROZEN_AT_REL
        return fa.read_text(encoding="utf-8").strip() if fa.is_file() else None

    def handoff_landed(self, rel: str) -> bool:
        """A commit reachable from HEAD that touches `rel` and is NOT an ancestor of the
        freeze commit: the handoff was written by the campaign, after pre-registration."""
        frozen = self.frozen_sha()
        if not frozen:
            return False
        r = _git("log", "--format=%H", "HEAD", "--", rel)
        for sha in r.stdout.split():
            if _git("merge-base", "--is-ancestor", sha, frozen).returncode != 0:
                return True
        return False

    def run_gate(self, argv: list) -> tuple:
        """(returncode, tail of output). A real subprocess, cwd = repo, no shell."""
        try:
            r = subprocess.run([sys.executable] + [str(a) for a in argv[1:]], cwd=str(REPO),
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=GATE_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return 124, f"timeout after {GATE_TIMEOUT_S}s"
        return r.returncode, (r.stdout + r.stderr)[-400:]

    def frozen_at_commit(self):
        """The `frozen` object as committed at FROZEN_AT, or None if not frozen yet."""
        fa = REPO / FROZEN_AT_REL
        if not fa.is_file():
            return None
        sha = fa.read_text(encoding="utf-8").strip()
        r = _git("show", f"{sha}:{LEDGER_REL}")
        if r.returncode != 0:
            raise RuntimeError(f"FROZEN_AT names {sha!r} but git cannot show the ledger there")
        return json.loads(r.stdout)["frozen"]


def check_ledger(led: dict, res: Resolver, final: bool, only=None, run_gates=True) -> list:
    """Every failure is a string naming the clause and pillar. Empty = pass."""
    f = []
    fr = led.get("frozen") or {}
    ids = [p.get("id") for p in fr.get("pillars", [])]
    if ids != PILLARS:
        return [f"L1 frozen pillars must be exactly A-T in order, got {ids}"]
    state = led.get("state") or {}
    if sorted(state) != PILLARS:
        return [f"L1 state must hold A-T, got {sorted(state)}"]
    predicted = {p["id"]: p.get("predicted") for p in fr["pillars"]}
    owners = {p["id"]: list(p.get("owner") or []) for p in fr["pillars"]}
    denoms = sorted((fr.get("denominators") or {}).keys())
    for pid, pred in predicted.items():
        if pred not in TERMINALS:
            f.append(f"L1 {pid}: predicted {pred!r} is not a terminal state")
        for o in owners[pid]:
            if not res.path_exists(o):
                f.append(f"L1 {pid}: frozen owner {o} does not exist")

    ref = res.frozen_at_commit()
    if ref is None:
        if final:
            f.append("L2 not frozen: FROZEN_AT missing, the pre-registration was never committed")
    elif json.dumps(ref, sort_keys=True) != json.dumps(fr, sort_keys=True):
        f.append("L2 frozen pre-registration differs from its copy at FROZEN_AT")

    for pid in (only or PILLARS):
        st = state[pid] or {}
        term = st.get("terminal")
        ev = st.get("evidence") or []
        if term is None:
            if final:
                f.append(f"L3 {pid}: no terminal disposition")
            continue
        if term not in TERMINALS:
            f.append(f"L3 {pid}: {term!r} is not a terminal state")
            continue
        kinds = {e.get("kind") for e in ev}
        if not any(set(need) <= kinds for need in REQUIRED_KINDS[term]):
            f.append(f"L4 {pid}: {term} needs evidence kinds {REQUIRED_KINDS[term]}, "
                     f"has {sorted(k for k in kinds if k)}")
        for e in ev:
            f.extend(_check_evidence(pid, e, res, owners[pid], denoms))
        if term == "IMPLEMENTED_AND_VERIFIED" and run_gates:
            for e in ev:
                if e.get("kind") != "gate":
                    continue
                why = gate_argv_problem(e.get("argv"))
                if why:
                    f.append(f"L5 {pid}: {why}")
                    continue
                rc, tail = res.run_gate(e["argv"])
                if rc != 0:
                    f.append(f"L5 {pid}: gate {' '.join(map(str, e['argv']))} rc {rc}: {tail[-160:]}")
        if predicted[pid] == "IMPLEMENTED_AND_VERIFIED" and term != "IMPLEMENTED_AND_VERIFIED":
            fal = [e for e in ev if e.get("kind") == "falsification"]
            if not fal:
                f.append(f"L6 {pid}: pre-registered IMPLEMENT ended {term} without a falsification artifact")
            elif not all(f"[{pid}]" in res.file_text(e.get("ref") or "") for e in fal):
                f.append(f"L6 {pid}: falsification artifact does not name pillar [{pid}]")
        reason = st.get("reason") or ""
        if not reason.strip():
            f.append(f"L7 {pid}: terminal without a reason")
        elif DEFERRAL_PROSE.search(reason):
            f.append(f"L7 {pid}: reason defers in prose: {DEFERRAL_PROSE.search(reason).group(0)!r}")
        for s in st.get("savings") or []:
            f.extend(_check_saving(pid, s))

    if final and not only:
        for key in ("ukdl", "cbr"):
            rv = (led.get("reviews") or {}).get(key)
            if not rv or not rv.get("file") or not res.path_exists(rv["file"]):
                f.append(f"L8 review {key}: missing or its file does not exist")
        for key in ("product", "intelligence"):
            if not (led.get("deltas") or {}).get(key):
                f.append(f"L8 delta {key}: empty")
    return f


def _check_evidence(pid: str, e: dict, res: Resolver, owners: list, denoms: list) -> list:
    kind, ref = e.get("kind"), e.get("ref") or ""
    if kind == "gate":
        return [] if e.get("argv") else [f"L4 {pid}: gate evidence without argv"]
    if kind == "blocker":
        return [] if (e.get("text") or "").strip() else [f"L4 {pid}: blocker without text"]
    if not ref:
        return [f"L4 {pid}: {kind} evidence without ref"]
    if kind == "commit" and not res.commit_reachable(ref):
        return [f"L4 {pid}: commit {ref} not reachable from HEAD"]
    if kind == "owner":
        if ref not in owners:
            return [f"L4 {pid}: owner {ref} is not one of the pillar's frozen owners {owners}"]
        if not res.path_exists(ref):
            return [f"L4 {pid}: owner {ref} does not exist"]
    if kind in FILE_KINDS:
        sha = res.file_sha(ref)
        if sha is None:
            return [f"L4 {pid}: {kind} file {ref} does not exist"]
        # Mandatory (audit G7): an unpinned citation can be rewritten after it is cited.
        if not e.get("sha256"):
            return [f"L4 {pid}: {kind} file {ref} cited without sha256"]
        if e["sha256"] != sha:
            return [f"L4 {pid}: {kind} file {ref} sha256 changed since it was cited"]
        text = res.file_text(ref)
        if kind in ("owner_decision", "handoff", "falsification") and f"[{pid}]" not in text:
            return [f"L4 {pid}: {kind} file {ref} does not name pillar [{pid}]"]
        if kind == "handoff":
            if not ref.startswith(HANDOFF_DIR):
                return [f"L4 {pid}: handoff {ref} must live under {HANDOFF_DIR}"]
            if not any(o in text for o in owners):
                return [f"L4 {pid}: handoff {ref} names none of the pillar's owners"]
            if not res.handoff_landed(ref):
                return [f"L4 {pid}: handoff {ref} has no commit after the freeze"]
        if kind == "measurement":
            if not any(d in text for d in denoms):
                return [f"L4 {pid}: measurement {ref} names no frozen denominator {denoms}"]
            if "command:" not in text:
                return [f"L4 {pid}: measurement {ref} does not record the command that produced it"]
    return []


def _check_saving(pid: str, s: dict) -> list:
    out = []
    st, disp = s.get("status"), s.get("displacement")
    if st not in SAVING_STATUS:
        out.append(f"L9 {pid}: saving status {st!r} not in {sorted(SAVING_STATUS)}")
    if disp not in DISPLACEMENT:
        out.append(f"L9 {pid}: saving displacement {disp!r} not in {sorted(DISPLACEMENT)}")
    if st == "realized" and disp != "settled":
        out.append(f"L9 {pid}: realized saving with displacement {disp!r} (must be settled)")
    if st == "realized" and not s.get("measurement"):
        out.append(f"L9 {pid}: realized saving without a measurement reference")
    if not s.get("denominator"):
        out.append(f"L9 {pid}: saving without a named denominator")
    return out


# ---------------------------------------------------------------- selftest

SHA = "f" * 64
OWNER = "ok/owner.md"


class FakeResolver(Resolver):
    """Files exist under ok/ and the handoff dir. Their text names every pillar, the
    D-W7 denominator, a command and the owner -- except files whose name says otherwise
    (nodenom / noowner / other), so each mutant removes exactly one property."""

    def __init__(self, frozen, gate_rc=0):
        self.frozen, self.gate_rc, self.gate_calls = frozen, gate_rc, 0

    def commit_reachable(self, ref):
        return ref == "abc1234"

    def _exists(self, rel):
        return rel.startswith("ok/") or rel.startswith(HANDOFF_DIR)

    def file_sha(self, rel):
        return SHA if self._exists(rel) else None

    def path_exists(self, rel):
        return self._exists(rel)

    def file_text(self, rel):
        if not self._exists(rel):
            return ""
        base = "decision " + " ".join(f"[{p}]" for p in PILLARS) + f" D-W7 command: python x {OWNER}"
        if "nodenom" in rel:
            return base.replace("D-W7", "")
        if "noowner" in rel:
            return base.replace(OWNER, "")
        if "other" in rel:
            return "a falsification about something else"
        return base

    def handoff_landed(self, rel):
        return "stale" not in rel

    def run_gate(self, argv):
        self.gate_calls += 1
        return self.gate_rc, "fake"

    def frozen_at_commit(self):
        return copy.deepcopy(self.frozen)


REAL_GATE = ["python", "tools/gsd_mission_freshness.py", "--help"]


def _merged(pid, handoff=None, **ev):
    return {"terminal": "MERGED_INTO_EXISTING_OWNER", "reason": "owner holds it", "savings": [],
            "evidence": [{"kind": "owner", "ref": OWNER},
                         {"kind": "handoff", "ref": handoff or f"{HANDOFF_DIR}{pid}.md", "sha256": SHA, **ev}]}


def _clean_fixture():
    led = json.loads((REPO / LEDGER_REL).read_text(encoding="utf-8"))
    for p in led["frozen"]["pillars"]:
        p["predicted"] = "MERGED_INTO_EXISTING_OWNER"
        p["owner"] = [OWNER]
    led["frozen"]["pillars"][0]["predicted"] = "IMPLEMENTED_AND_VERIFIED"
    for pid in PILLARS:
        led["state"][pid] = _merged(pid)
    led["state"]["A"] = {"terminal": "IMPLEMENTED_AND_VERIFIED", "reason": "before-snapshot frozen",
                         "evidence": [{"kind": "gate", "argv": REAL_GATE},
                                      {"kind": "prg", "ref": "ok/prg.md", "sha256": SHA}],
                         "savings": [{"status": "upper_bound", "displacement": "unknown",
                                      "denominator": "D-W7"}]}
    led["reviews"] = {"ukdl": {"file": "ok/ukdl.md"}, "cbr": {"file": "ok/cbr.md"}}
    led["deltas"] = {"product": ["x"], "intelligence": ["y"]}
    return led


def selftest(verbose=True) -> bool:
    clean = _clean_fixture()
    ok = True

    def say(good, label):
        nonlocal ok
        if not good:
            ok = False
            print(f"  FAIL {label}")
        elif verbose:
            print(f"  ok   {label}")

    def run(led, res=None):
        return check_ledger(led, res or FakeResolver(clean["frozen"]), final=True)

    def m(fn):
        led = copy.deepcopy(clean)
        fn(led)
        return led

    def all_deferred(led):
        for pid in PILLARS:
            led["state"][pid] = {"terminal": "DEFERRED_STRONGER_OWNER", "reason": "someone else",
                                 "evidence": [], "savings": []}

    def set_a(**kw):
        def fn(led):
            led["state"]["A"].update(kw)
        return fn

    clean_res = FakeResolver(clean["frozen"])
    say(not run(clean, clean_res) and clean_res.gate_calls == 1,
        "V-CEP-SELFTEST-CLEAN (green, and the IMPLEMENTED gate was actually run once)")

    prg = {"kind": "prg", "ref": "ok/prg.md", "sha256": SHA}

    def put(pid, value):
        return lambda l: l["state"].__setitem__(pid, value)

    def predict_e_implement(led):
        led["frozen"]["pillars"][4]["predicted"] = "IMPLEMENTED_AND_VERIFIED"
        led["state"]["E"] = {"terminal": "FALSIFIED_OR_REJECTED_BY_EVIDENCE", "reason": "r",
                             "evidence": [{"kind": "measurement", "ref": "ok/m", "sha256": SHA},
                                          {"kind": "falsification", "ref": "ok/other-f", "sha256": SHA}]}

    mutants = {
        "all-deferred-no-evidence": (m(all_deferred), "L4"),
        # audit G7: an owner path plus HEAD used to satisfy a deferral
        "deferred-citing-head": (m(put("B", {"terminal": "DEFERRED_STRONGER_OWNER", "reason": "r", "evidence": [{"kind": "owner", "ref": OWNER}, {"kind": "commit", "ref": "abc1234"}]})), "L4"),
        "handoff-before-freeze": (m(put("C", _merged("C", handoff=f"{HANDOFF_DIR}stale-C.md"))), "L4"),
        "handoff-names-no-owner": (m(put("C", _merged("C", handoff=f"{HANDOFF_DIR}noowner-C.md"))), "L4"),
        "handoff-outside-dir": (m(put("C", _merged("C", handoff="ok/C.md"))), "L4"),
        "evidence-without-sha": (m(lambda l: l["state"]["D"]["evidence"][1].pop("sha256")), "L4"),
        "evidence-sha-changed": (m(lambda l: l["state"]["D"]["evidence"][1].__setitem__("sha256", "0" * 64)), "L4"),
        "measurement-without-denominator": (m(put("F", {"terminal": "RESEARCH_INSUFFICIENT_EVIDENCE", "reason": "r", "evidence": [{"kind": "measurement", "ref": "ok/nodenom-F.md", "sha256": SHA}]})), "L4"),
        "owner-not-frozen": (m(lambda l: l["state"]["G"]["evidence"].__setitem__(0, {"kind": "owner", "ref": "ok/other-owner.md"})), "L4"),
        "frozen-owner-missing": (m(lambda l: l["frozen"]["pillars"][7].__setitem__("owner", ["gone/owner.md"])), "L1"),
        "dangling-commit": (m(lambda l: l["state"]["B"]["evidence"].append({"kind": "commit", "ref": "deadbee"})), "L4"),
        "authorization-without-decision-file": (m(put("B", {"terminal": "AUTHORIZATION_BOUND", "reason": "owner y per move", "evidence": [{"kind": "owner_decision", "ref": "gone/bundle.md", "sha256": SHA}]})), "L4"),
        "implemented-without-gate": (m(set_a(evidence=[prg])), "L4"),
        "unbacked-demotion": (m(put("A", _merged("A"))), "L6"),
        "falsification-of-other-pillar": (m(predict_e_implement), "L6"),
        "recursive-gate": (m(set_a(evidence=[{"kind": "gate", "argv": ["python", SELF_REL, "--final"]}, prg])), "L5"),
        "shell-gate": (m(set_a(evidence=[{"kind": "gate", "argv": "python tools/x.py && rm -rf ."}, prg])), "L5"),
        "unsafe-arg-gate": (m(set_a(evidence=[{"kind": "gate", "argv": REAL_GATE[:2] + ["a;b"]}, prg])), "L5"),
        "realized-without-displacement": (m(set_a(savings=[{"status": "realized", "displacement": "unknown", "denominator": "D-W7", "measurement": "ok/m"}])), "L9"),
        "saving-without-denominator": (m(set_a(savings=[{"status": "unknown", "displacement": "unknown"}])), "L9"),
        "deferral-prose": (m(lambda l: l["state"]["D"].__setitem__("reason", "we will do this later")), "L7"),
        "open-pillar": (m(lambda l: l["state"]["E"].__setitem__("terminal", None)), "L3"),
        "frozen-edited": (m(lambda l: l["frozen"]["pillars"][3].__setitem__("rule", "moved goalposts")), "L2"),
        "no-ukdl-review": (m(lambda l: l["reviews"].__setitem__("ukdl", None)), "L8"),
        "empty-intelligence-delta": (m(lambda l: l["deltas"].__setitem__("intelligence", [])), "L8"),
    }
    for name, (led, clause) in mutants.items():
        res = FakeResolver(led["frozen"] if name != "frozen-edited" else clean["frozen"])
        got = run(led, res)
        say(any(x.startswith(clause) for x in got), f"V-CEP-MUT-{name} killed by {clause}")

    failing_gate = FakeResolver(clean["frozen"], gate_rc=1)
    say(any(x.startswith("L5") for x in run(clean, failing_gate)), "V-CEP-MUT-gate-red killed by L5")
    unfrozen = type("R", (FakeResolver,), {"frozen_at_commit": lambda self: None})(clean["frozen"])
    say(any(x.startswith("L2") for x in run(clean, unfrozen)), "V-CEP-MUT-unfrozen killed by L2")

    # The gate runner on a REAL subprocess, both poles: the fakes above never start one.
    real = Resolver()
    rc_ok, _ = real.run_gate(REAL_GATE)
    with tempfile.TemporaryDirectory(dir=str(REPO / "tools")) as td:
        bad = Path(td) / "exit3.py"
        bad.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        rel = bad.relative_to(REPO).as_posix()
        rc_bad, _ = real.run_gate(["python", rel])
    say(rc_ok == 0 and rc_bad == 3, f"V-CEP-REAL-RUNNER (green rc {rc_ok}, red rc {rc_bad})")
    say(gate_argv_problem(REAL_GATE) is None and gate_argv_problem(["python", SELF_REL]) is not None,
        "V-CEP-REAL-ALLOWLIST (real script admitted, the verifier itself refused)")

    # handoff_landed on REAL git, both poles, with the poles DERIVED from the plan file's
    # own history (C0 1cabd117 first; later commits such as the P0 freeze and the execution
    # log touched it too, which is what turned a hardcoded "only commit is C0" pole red):
    # frozen AT its newest commit -> every touching commit is an ancestor -> not landed;
    # frozen at the parent of its oldest commit -> landed after. Skipped (INCONCLUSIVE,
    # not PASS) where that history is absent, e.g. a shallow clone.
    plan = "vault/plans/cognitive-economy-program-2026-10-03.md"
    if _git("cat-file", "-e", "1cabd117^{commit}").returncode == 0:
        def at(sha):
            return type("R", (Resolver,), {"frozen_sha": lambda self: sha})()
        touching = _git("log", "--format=%H", "HEAD", "--", plan).stdout.split()
        newest, oldest = touching[0], touching[-1]
        before = at(newest).handoff_landed(plan)
        after = at(oldest + "^").handoff_landed(plan)
        say(oldest.startswith("1cabd117") and before is False and after is True,
            f"V-CEP-REAL-HANDOFF (frozen at newest {newest[:8]} -> {before}, "
            f"frozen before C0 -> {after}, oldest {oldest[:8]})")
    else:
        print("  INCONCLUSIVE V-CEP-REAL-HANDOFF: commit 1cabd117 not in this clone")
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--final", action="store_true")
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--selftest", action="store_true")
    mode.add_argument("--pillar", choices=PILLARS)
    a = ap.parse_args(argv)

    if a.selftest:
        ok = selftest()
        print(f"CEP_SELFTEST={'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    try:
        led = json.loads((REPO / LEDGER_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"CEP_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
        return 2
    res = Resolver()
    if a.status:
        fails = check_ledger(led, res, final=False, run_gates=False)
        open_ = [p for p in PILLARS if not (led["state"][p] or {}).get("terminal")]
        print(json.dumps({"open": open_, "closed": [p for p in PILLARS if p not in open_],
                          "violations": fails}, indent=1))
        return 1 if fails else 0
    if a.pillar:
        fails = check_ledger(led, res, final=True, only=[a.pillar])
        for x in fails:
            print("  FAIL", x)
        print(f"CEP_PILLAR_{a.pillar}={'PASS' if not fails else 'FAIL'}")
        return 0 if not fails else 1
    fails = []
    if not selftest(verbose=False):
        fails.append("S0 selftest failed: the verifier cannot be trusted")
    fails += check_ledger(led, res, final=True)
    for x in fails:
        print("  FAIL", x)
    print(f"CEP_VERDICT={'PASS' if not fails else 'FAIL'} failures={len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
