#!/usr/bin/env python3
"""V-AOP0-* gates for Phase 0 of the IC-gen2 autonomous-optimization programme.

Judges two artifacts and proves every rule on them can fail:

  * the T3 spec        vault/specs/autonomous-optimization.md   (readiness, sections, covers, binding)
  * the novelty record vault/audits/autonomous-optimization-novelty-2026-10-05.md  (HR-NOVELTY-001)

Each rule is driven from both poles: the real artifact runs first as the clean control, then a mutant
(an altered in-memory or temp-repo copy) must be reported. A mutant passes only when the judge reports
the defect AND the matching clean control was clean, so a judge that refuses everything cannot pass.

Isolation: SDD_OS_STATE_DIR points at a fresh temp dir before modules.sdd_os is imported, so no test
writes under the real ~/.claude. Stdlib only. Run from the repo root:

    python3 tools/test_ao_p0.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_STATE_DIR = Path(tempfile.mkdtemp(prefix="aop0-state-"))
os.environ["SDD_OS_STATE_DIR"] = str(_STATE_DIR)
sys.path.insert(0, str(ROOT))

from modules.sdd_os.readiness import assess  # noqa: E402
from modules.sdd_os.spec_binding import find_bound_spec, parse_front_matter, read_covers  # noqa: E402

SPEC_REL = "vault/specs/autonomous-optimization.md"
PLAN_REL = "vault/plans/autonomous-optimization-2026-10-05.md"
STATE_REL = ".planning/workstreams/autonomous-optimization/STATE.md"

REQUIRED_HEADINGS = (
    "## Measured baseline (2026-10-05, plane gex44)",
    "## 1. Problem",
    "## 2. Objective",
    "## 3. Non-goals",
    "## 4. Actors",
    "## 5. Functional requirements",
    "## 6. Non-functional requirements",
    "## 7. Acceptance criteria",
    "## 8. Architecture spec",
    "### 8.1 Components affected",
    "### 8.2 System flow",
    "### 8.3 Contracts",
    "### 8.4 Failure modes",
    "### 8.5 Rollback plan",
    "## 9. Test plan",
    "## 10. Validation",
    "## Governance spec (Tier 3)",
    "## Cross-repo applicability (Tier 3)",
    "## Compatibility matrix and migration strategy (Tier 3)",
    "## Kill switches (Tier 3)",
    "## Standardization rule (Tier 3)",
    "## 11. Completion gate",
)
KILL_SWITCH_STATUS = {"KS-1": "LIVE", "KS-2": "LIVE", "KS-3": "LIVE", "KS-4": "PLANNED", "KS-5": "PLANNED"}
PLAN_PROBE = "autonomous optimization zero-rescan kme-l challenger"

results: list[tuple[str, bool, str]] = []


def gate(name: str, cond: bool, evidence: str = "") -> None:
    results.append((name, bool(cond), evidence))
    print(f"{'PASS' if cond else 'FAIL'} {name}  {evidence}")


def guarded(name: str, fn) -> None:
    """Run a gate body; an exception is a FAIL, never a crash that hides later gates."""
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - the exception IS the evidence
        gate(name, False, f"exception {type(exc).__name__}: {exc}")


# --- pure judges (mutants reuse them) --------------------------------------------------------

def _body(text: str) -> str:
    parts = text.split("\n---\n", 1)
    return parts[1] if text.startswith("---") and len(parts) == 2 else text


def spec_problems(path: Path | str, root: Path | str = ROOT) -> list[str]:
    """Every defect of the spec at `path`, each prefixed with the rule that found it."""
    path, root = Path(path), Path(root)
    probs: list[str] = []
    text = path.read_text(encoding="utf-8")

    r = assess(path, 3)
    if r.state != "READY":
        probs.append(f"READY: state={r.state} missing={list(r.missing)}")

    lines = {ln.rstrip() for ln in text.splitlines()}
    for h in REQUIRED_HEADINGS:
        if h not in lines:
            probs.append(f"SECTIONS: heading missing: {h}")
    for ks, want in KILL_SWITCH_STATUS.items():
        m = re.search(rf"^- {ks}\s+(LIVE|PLANNED)\b", text, re.M)
        if not m:
            probs.append(f"SECTIONS: {ks} has no LIVE/PLANNED status word")
        elif m.group(1) != want:
            probs.append(f"SECTIONS: {ks} is {m.group(1)}, expected {want}")

    fm = parse_front_matter(text)
    covers = read_covers(path) or ()
    plan_rel = str(fm.get("plan", PLAN_REL))
    plan_covers = read_covers(root / plan_rel)
    if plan_covers is None:
        probs.append(f"COVERS: plan of record {plan_rel} unreadable or declares no covers")
        plan_covers = ()
    if len(covers) < 4:
        probs.append(f"COVERS: only {len(covers)} entries, need at least 4")
    for e in covers:
        if "-" not in e:
            probs.append(f"COVERS: entry {e!r} is not multi-token")
        if e.lower() in {c.lower() for c in plan_covers}:
            probs.append(f"COVERS: entry {e!r} repeats the plan of record")

    oq = fm.get("open_questions") or []
    for n in range(1, 6):
        item = next((i for i in oq if i.startswith(f"Q{n} ")), None)
        if item is None:
            probs.append(f"DECISIONS: Q{n} missing")
            continue
        parts = [p.strip() for p in item.split("|")]
        if len(parts) < 3 or parts[1].upper() != "RESOLVED" or not parts[2]:
            probs.append(f"DECISIONS: Q{n} is not RESOLVED with an answer")
        if f"D-OQ{n}" not in item:
            probs.append(f"DECISIONS: Q{n} does not carry D-OQ{n}")
    body = _body(text)
    for needle in ("ICP_GEN2_VERDICT", "inherited", "never claimed green"):
        if needle not in body:
            probs.append(f"DECISIONS: body lacks {needle!r}")
    return probs


def binding_problems(root: Path | str) -> list[str]:
    """Binding of the spec against the repo at `root`: REFERENCED, STRONG, no tie, plan stays STRONG."""
    root = Path(root)
    spec = root / SPEC_REL
    probs: list[str] = []

    def at(b, rel: str) -> bool:
        return b.spec_path is not None and b.spec_path.resolve() == (root / rel).resolve()

    def note(label: str, b) -> str:
        return f"{label}: strength={b.strength} spec={b.spec_path} alternatives={[p.name for p in b.alternatives]}"

    b = find_bound_spec(f"{SPEC_REL} gen2 ledger freeze", root)
    if b.strength != "REFERENCED" or not at(b, SPEC_REL):
        probs.append("BIND(a) " + note("path probe must be REFERENCED to the spec", b))
    for entry in read_covers(spec) or ():
        probe = " ".join(entry.split("-"))
        b = find_bound_spec(probe, root)
        if b.strength == "AMBIGUOUS":
            probs.append("BIND(b) AMBIGUOUS " + note(f"entry {entry!r}", b))
        elif b.strength not in ("STRONG", "REFERENCED") or not at(b, SPEC_REL):
            probs.append("BIND(b) " + note(f"entry {entry!r} must bind to the spec", b))
    b = find_bound_spec(PLAN_PROBE, root)
    if b.strength == "AMBIGUOUS":
        probs.append("BIND(c) AMBIGUOUS " + note("plan probe", b))
    elif b.strength != "STRONG" or not at(b, PLAN_REL):
        probs.append("BIND(c) " + note("plan probe must stay STRONG to the plan of record", b))
    return probs


def make_temp_repo(spec_text: str) -> Path:
    """A repo with only vault/specs and vault/plans: the real plan of record plus the given spec text."""
    repo = Path(tempfile.mkdtemp(prefix="aop0-repo-"))
    (repo / "vault" / "specs").mkdir(parents=True)
    (repo / "vault" / "plans").mkdir(parents=True)
    shutil.copy2(ROOT / PLAN_REL, repo / PLAN_REL)
    (repo / SPEC_REL).write_text(spec_text, encoding="utf-8")
    return repo


def _has(problems: list[str], prefix: str) -> bool:
    return any(p.startswith(prefix) for p in problems)


# --- spec gates ------------------------------------------------------------------------------

def spec_gates() -> None:
    spec = ROOT / SPEC_REL
    r = assess(spec, 3)
    gate("V-AOP0-SPEC-READY", r.state == "READY" and not r.missing,
         f"state={r.state} missing={list(r.missing)}")

    probs = spec_problems(spec)
    sec = [p for p in probs if p.startswith("SECTIONS")]
    gate("V-AOP0-SPEC-SECTIONS", not sec,
         f"{len(REQUIRED_HEADINGS)} headings + {len(KILL_SWITCH_STATUS)} kill-switch status words; problems={sec}")
    cov = [p for p in probs if p.startswith("COVERS")]
    covers = read_covers(spec) or ()
    gate("V-AOP0-SPEC-COVERS-DISJOINT", not cov, f"covers={list(covers)} problems={cov}")
    bind = binding_problems(ROOT)
    gate("V-AOP0-SPEC-BINDS", not bind, f"{len(covers) + 2} probes against the real repo; problems={bind}")
    dec = [p for p in probs if p.startswith("DECISIONS")]
    gate("V-AOP0-SPEC-DECISIONS", not dec, f"problems={dec}")

    state_txt = (ROOT / STATE_REL).read_text(encoding="utf-8")
    gate("V-AOP0-STATE-D-OQ3", "[Orchestrator D-OQ3 2026-10-05]" in state_txt
         and "never claimed green" in state_txt, "STATE.md carries the D-OQ3 decision bullet")


def spec_mutants() -> None:
    real = (ROOT / SPEC_REL).read_text(encoding="utf-8")

    # clean control inside the temp-repo harness: it must be clean, or no mutant below proves anything
    ctrl = make_temp_repo(real)
    ctrl_spec = spec_problems(ctrl / SPEC_REL, root=ctrl)
    ctrl_bind = binding_problems(ctrl)
    gate("V-AOP0-MUT-control", not ctrl_spec and not ctrl_bind,
         f"temp-repo harness clean on the real spec: spec={ctrl_spec} bind={ctrl_bind}")
    harness_ok = not ctrl_spec and not ctrl_bind

    draft = make_temp_repo(real.replace("status: ready", "status: draft", 1))
    p = spec_problems(draft / SPEC_REL, root=draft)
    gate("V-AOP0-MUT-spec-draft", harness_ok and _has(p, "READY"),
         f"status draft -> {[x for x in p if x.startswith('READY')]}")

    tie_text = real.replace("covers: [", "covers: [autonomous-optimization, ", 1)
    tie = make_temp_repo(tie_text)
    b = binding_problems(tie)
    s = spec_problems(tie / SPEC_REL, root=tie)
    gate("V-AOP0-MUT-covers-tie", harness_ok and any("AMBIGUOUS" in x for x in b) and _has(s, "COVERS"),
         f"covers gains a plan entry -> bind={[x[:60] for x in b if 'AMBIGUOUS' in x]} covers={_has(s, 'COVERS')}")

    nks = make_temp_repo(real.replace("## Kill switches (Tier 3)\n", "", 1))
    p = spec_problems(nks / SPEC_REL, root=nks)
    gate("V-AOP0-MUT-no-killswitch", harness_ok and any("Kill switches" in x for x in p),
         f"heading removed -> {[x for x in p if 'Kill switches' in x]}")


# --- novelty record judge --------------------------------------------------------------------

from modules.spec_gate.gate import NOVELTY_PROOF_QUESTIONS, check_novelty_gate  # noqa: E402

NOVELTY_REL = "vault/audits/autonomous-optimization-novelty-2026-10-05.md"
ROADMAP_REL = ".planning/workstreams/autonomous-optimization/ROADMAP.md"
GATE_CONTROLS = ("new autonomous optimization operating system", "new optimization governance layer")
REQUIRED_SWEEP = ("SCHEMA_VERSION", "challenger", "def promote", "def record_signal",
                  "opportunity lifecycle", "def store_identity", "ratchet", "opportunities")
# path.ext:LINE "fragment" -- the fragment is straight-quoted and holds no double quote
_CITE = re.compile(r'([A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(\d+) "([^"\n]+)"')
_ROW = re.compile(r"^\|\s*\*{0,2}(\d+)\*{0,2}\s*\|")
_GATE_LINE = re.compile(r"^(plan text|ROADMAP text|control \"[^\"]+\"): applies=(True|False) matched=(None|'[^']*')\s*$", re.M)
_GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_TERMINAL_PROMPT": "0"}


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull, *args], cwd=root, env=_GIT_ENV,
                          capture_output=True, text=True, timeout=30)


def _section(text: str, heading: str) -> str:
    m = re.search(rf"^{re.escape(heading)}.*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def cite_problems(cites: list[tuple[str, str, str]], root: Path | str, snapshot: str) -> list[str]:
    """Resolve each (path, line, fragment): inside the repo, tracked by git, present in the snapshot
    commit with the fragment verbatim on that line. Argv lists only, never a shell."""
    root = Path(root)
    probs: list[str] = []
    real_root = root.resolve()
    for rel, line, frag in cites:
        tag = f'{rel}:{line} "{frag[:40]}"'
        norm = os.path.normpath(rel)
        resolved = (root / rel).resolve()
        if os.path.isabs(rel) or norm.startswith("..") or (
                resolved != real_root and real_root not in resolved.parents):
            probs.append(f"CITE: {tag} is outside the repo")
            continue
        if _git(root, "ls-files", "--error-unmatch", "--", norm).returncode != 0:
            probs.append(f"CITE: {tag} is not a git-tracked file")
            continue
        blob = _git(root, "show", f"{snapshot}:{norm}")
        if blob.returncode != 0:
            probs.append(f"CITE: {tag} is not present in snapshot {snapshot[:8]}")
            continue
        lines = blob.stdout.splitlines()
        n = int(line)
        if not 1 <= n <= len(lines):
            probs.append(f"CITE: {tag} line {n} is past the end ({len(lines)} lines)")
        elif frag not in lines[n - 1]:
            probs.append(f"CITE: {tag} fragment does not occur on that line")
    return probs


def _gate_repr(text: str) -> str:
    r = check_novelty_gate(text)
    return f"applies={r.applies} matched={r.matched!r}"


def live_gate_lines(root: Path | str = ROOT) -> dict[str, str]:
    root = Path(root)
    out = {"plan text": _gate_repr((root / PLAN_REL).read_text(encoding="utf-8")),
           "ROADMAP text": _gate_repr((root / ROADMAP_REL).read_text(encoding="utf-8"))}
    for c in GATE_CONTROLS:
        out[f'control "{c}"'] = _gate_repr(c)
    return out


def novelty_problems(text: str, root: Path | str = ROOT) -> list[str]:
    """Every defect of a novelty record text, each prefixed with the rule that found it."""
    root = Path(root)
    probs: list[str] = []
    fm = parse_front_matter(text)
    snapshot = str(fm.get("sweep_commit", "")).strip()

    rows = [ln for ln in _section(text, "## 3. The thirteen").splitlines() if _ROW.match(ln)]
    if len(rows) != 13:
        probs.append(f"ROWS: {len(rows)} table rows, need exactly 13")
    all_cites: list[tuple[str, str, str]] = []
    for ln in rows:
        cells = [c.strip() for c in ln.strip().strip("|").split("|", 2)]
        n = int(_ROW.match(ln).group(1))
        if len(cells) != 3:
            probs.append(f"ROWS: row {n} is not # | question | answer")
            continue
        if not 1 <= n <= 13 or cells[1] != NOVELTY_PROOF_QUESTIONS[n - 1]:
            probs.append(f"ROWS: row {n} question does not equal NOVELTY_PROOF_QUESTIONS[{n - 1}]")
        found = _CITE.findall(cells[2])
        if not found:
            probs.append(f"CITE: row {n} carries no path:LINE \"fragment\" citation")
        all_cites.extend(found)

    if not re.fullmatch(r"[0-9a-f]{7,40}", snapshot):
        probs.append(f"CITE: front matter sweep_commit {snapshot!r} is not a commit sha")
    elif _git(root, "merge-base", "--is-ancestor", snapshot, "HEAD").returncode != 0:
        probs.append(f"CITE: sweep_commit {snapshot} is not an ancestor of HEAD")
    else:
        probs.extend(cite_problems(all_cites, root, snapshot))

    verdict = str(fm.get("verdict", "")).strip()
    if verdict != "EXTEND_EXISTING_OWNER":
        probs.append(f"VERDICT: front matter verdict is {verdict!r}, the slice stops unless EXTEND_EXISTING_OWNER")
    if "EXTEND_EXISTING_OWNER" not in _section(text, "## 4. Verdict"):
        probs.append("VERDICT: section 4 does not state EXTEND_EXISTING_OWNER")

    recorded = {m.group(1): f"applies={m.group(2)} matched={m.group(3)}" for m in _GATE_LINE.finditer(text)}
    for key, live in live_gate_lines(root).items():
        if key not in recorded:
            probs.append(f"GATE: record has no line for {key!r}")
        elif recorded[key] != live:
            probs.append(f"GATE: {key!r} recorded {recorded[key]} but the gate returns {live}")

    sweep = _section(text, "## 2. Sweep")
    for needle in REQUIRED_SWEEP:
        if needle not in sweep:
            probs.append(f"SWEEP: section 2 has no command for {needle!r}")
    if len(re.findall(r"hits=\d+", sweep)) < len(REQUIRED_SWEEP):
        probs.append("SWEEP: fewer hit counts than required commands")
    return probs


def _first_cite(text: str) -> re.Match:
    sec = _section(text, "## 3. The thirteen")
    m = _CITE.search(sec)
    if m is None:
        raise AssertionError("record has no citation to mutate")
    return m


def novelty_gates() -> None:
    path = ROOT / NOVELTY_REL
    text = path.read_text(encoding="utf-8")
    probs = novelty_problems(text)

    rows = [p for p in probs if p.startswith("ROWS")]
    gate("V-AOP0-NOVELTY-13", not rows, f"13 rows in order against NOVELTY_PROOF_QUESTIONS; problems={rows}")

    cite = [p for p in probs if p.startswith("CITE")]
    n_cites = len(_CITE.findall(_section(text, "## 3. The thirteen")))
    gate("V-AOP0-NOVELTY-CITES-RESOLVE", not cite, f"{n_cites} citations resolved; problems={cite}")

    ctrl = check_novelty_gate(GATE_CONTROLS[0])
    gp = [p for p in probs if p.startswith("GATE")]
    gate("V-AOP0-NOVELTY-GATE-CONTROL", ctrl.applies is True and ctrl.matched == "operating system" and not gp,
         f"positive control applies={ctrl.applies} matched={ctrl.matched!r}; problems={gp}")

    vp = [p for p in probs if p.startswith("VERDICT")]
    gate("V-AOP0-NOVELTY-VERDICT", not vp, f"problems={vp}")

    sp = [p for p in probs if p.startswith("SWEEP")]
    gate("V-AOP0-NOVELTY-SWEEP-RECORDED", not sp, f"problems={sp}")


def novelty_mutants() -> None:
    text = (ROOT / NOVELTY_REL).read_text(encoding="utf-8")
    base = novelty_problems(text)
    gate("V-AOP0-MUT-novelty-control", not base, f"real record is clean before any mutant: {base}")
    clean = not base

    lines = text.splitlines(keepends=True)
    idx13 = next(i for i, ln in enumerate(lines) if _ROW.match(ln) and _ROW.match(ln).group(1) == "13")
    p = novelty_problems("".join(lines[:idx13] + lines[idx13 + 1:]))
    gate("V-AOP0-MUT-novelty-rows12", clean and _has(p, "ROWS"), f"12 rows -> {[x for x in p if x.startswith('ROWS')]}")

    m = _first_cite(text)
    frag_mut = text.replace(f'"{m.group(3)}"', f'"{m.group(3)}Z"', 1)
    p = novelty_problems(frag_mut)
    gate("V-AOP0-MUT-novelty-fragment", clean and any("fragment does not occur" in x for x in p),
         f"fragment +1 char -> {[x[:90] for x in p if x.startswith('CITE')]}")

    eof_mut = text.replace(f'{m.group(1)}:{m.group(2)} "', f'{m.group(1)}:999999 "', 1)
    p = novelty_problems(eof_mut)
    gate("V-AOP0-MUT-novelty-line-eof", clean and any("past the end" in x for x in p),
         f"line 999999 -> {[x[:90] for x in p if x.startswith('CITE')]}")

    out_mut = text.replace(f'{m.group(1)}:{m.group(2)} "', f'../outside.md:{m.group(2)} "', 1)
    po = novelty_problems(out_mut)
    tmp = Path(tempfile.mkdtemp(prefix="aop0-novrepo-"))
    for args in (("init", "-q"), ("config", "user.email", "t@example.invalid"), ("config", "user.name", "t")):
        _git(tmp, *args)
    (tmp / "a.txt").write_text("hello world\n", encoding="utf-8")
    (tmp / "b.txt").write_text("hello world\n", encoding="utf-8")        # present on disk, never added
    _git(tmp, "add", "a.txt")
    _git(tmp, "commit", "-q", "-m", "fixture")
    snap = _git(tmp, "rev-parse", "HEAD").stdout.strip()
    ctrl_c = cite_problems([("a.txt", "1", "hello")], tmp, snap)
    pu = cite_problems([("b.txt", "1", "hello")], tmp, snap)
    gate("V-AOP0-MUT-novelty-path",
         clean and not ctrl_c and any("outside the repo" in x for x in po) and any("not a git-tracked" in x for x in pu),
         f"control(tracked)={ctrl_c} outside={[x[:60] for x in po if 'outside' in x]} untracked={pu}")

    p = novelty_problems(text.replace("verdict: EXTEND_EXISTING_OWNER", "verdict: NEW_MODULE", 1))
    gate("V-AOP0-MUT-novelty-verdict", clean and _has(p, "VERDICT"), f"NEW_MODULE -> {[x for x in p if x.startswith('VERDICT')]}")

    stale = text.replace("plan text: applies=False", "plan text: applies=True", 1)
    p = novelty_problems(stale)
    gate("V-AOP0-MUT-novelty-stale-gate", clean and _has(p, "GATE"),
         f"recorded applies flipped -> {[x[:80] for x in p if x.startswith('GATE')]}")


def main() -> int:
    guarded("V-AOP0-SPEC", spec_gates)
    guarded("V-AOP0-SPEC-MUT", spec_mutants)
    guarded("V-AOP0-NOVELTY", novelty_gates)
    guarded("V-AOP0-NOVELTY-MUT", novelty_mutants)
    passes = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"AOP0_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if passes == total and total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
