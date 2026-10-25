#!/usr/bin/env python3
"""S9 Knowledge Vault checker (flow-compression Phase 8, FC-12, D-06).

Makes every citation in a flow-compression incident file executable, so a vault entry is evidence and not a claim:

  python3 tools/s9_kv_check.py incidents --glob 'vault/incidents/2026-10-2*-flow-compression-*.md' \
          --evidence /tmp/s9-evidence [--expect N]
  python3 tools/s9_kv_check.py --selftest

Incident format: a title, a `**Class:**` line, and `##` sections Symptom, Timeline, Root cause, Earliest discoverable
point, Repair, Test, Pattern (non-empty). Only the `## Test` section is parsed for citations, one per line:

  gate: <V-ID> in tools/test_<name>.py     the id appears literally in that file AND `PASS <V-ID>` is in
                                            <evidence>/test_<name>.out (a suite run made in this phase)
  commit: <hex7..40>                        `git cat-file -e <hash>^{commit}` resolves in the repo
  check: init-progress                      gsd-tools `query init.progress --ws flow-compression --raw` is run now:
                                            completed_count >= 7 and phases 01-07 phase_complete

Every incident needs at least one commit line and at least one gate or check line.

Exit codes: 0 no findings; 1 findings; 2 INCONCLUSIVE (evidence missing/unreadable, instrument unavailable). A check
that could not run is never a pass. Read-only on every input; standard library plus the in-repo flow_replay import.
"""
from __future__ import annotations

import argparse
import glob as _glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

REQUIRED_SECTIONS = ("Symptom", "Timeline", "Root cause", "Earliest discoverable point", "Repair", "Test", "Pattern")
GATE_RE = re.compile(r"^\s*(?:[-*]\s+)?gate:\s*(V-[A-Z0-9][A-Z0-9-]*)\s+in\s+(tools/test_[A-Za-z0-9_]+\.py)\b")
COMMIT_RE = re.compile(r"^\s*(?:[-*]\s+)?commit:\s*([0-9a-f]{7,40})\b")
CHECK_RE = re.compile(r"^\s*(?:[-*]\s+)?check:\s*([a-z][a-z0-9-]*)\b")
MIN_COMPLETED = 7          # phases 01-07 were complete when this checker was written; a later seal only raises it
GSD_WS = "flow-compression"

_INIT_CACHE: dict = {}


def finding(path, code: str, detail: str) -> dict:
    return {"file": str(path), "code": code, "detail": detail}


def exit_code(findings: list[dict]) -> int:
    """2 when anything is INCONCLUSIVE (could not be judged), else 1 when anything failed, else 0."""
    if any(f["code"].startswith("INCONCLUSIVE") for f in findings):
        return 2
    return 1 if findings else 0


# ------------------------------------------------------------------------------------------------ incident parsing
def _sections(text: str) -> dict[str, str]:
    out: dict[str, list[str]] = {}
    cur = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m and not line.startswith("###"):
            cur = m.group(1).strip().lower()
            out.setdefault(cur, [])
            continue
        if cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def parse_citations(test_section: str) -> dict:
    gates, commits, checks = [], [], []
    for line in test_section.splitlines():
        m = GATE_RE.match(line)
        if m:
            gates.append((m.group(1), m.group(2)))
            continue
        m = COMMIT_RE.match(line)
        if m:
            commits.append(m.group(1))
            continue
        m = CHECK_RE.match(line)
        if m:
            checks.append(m.group(1))
    return {"gates": gates, "commits": commits, "checks": checks}


# ------------------------------------------------------------------------------------------------ instruments
def _git_resolves(repo: Path, h: str) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{h}^{{commit}}"],
                           capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def _gate_in_text(gate: str, text: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9-])" + re.escape(gate) + r"(?![A-Za-z0-9-])", text) is not None


def _evidence_lines(evidence_dir: Path, stem: str) -> list[str] | None:
    p = evidence_dir / f"{stem}.out"
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None


def _gsd_tools_path(gsd_tools: str | None) -> str:
    return gsd_tools or os.environ.get("GSD_TOOLS") or str(Path.home() / ".claude/gsd-core/bin/gsd-tools.cjs")


def init_progress(repo: Path, gsd_tools: str | None = None) -> dict:
    """Run the GSD completion instrument. Returns {'ok': bool, 'inconclusive': bool, 'detail': str, 'completed': n}."""
    tool = _gsd_tools_path(gsd_tools)
    key = (str(repo), tool)
    if key in _INIT_CACHE:
        return _INIT_CACHE[key]
    res = _init_progress_uncached(repo, tool)
    _INIT_CACHE[key] = res
    return res


def _init_progress_uncached(repo: Path, tool: str) -> dict:
    if not Path(tool).is_file() or shutil.which("node") is None:
        return {"ok": False, "inconclusive": True, "detail": f"gsd-tools or node unavailable ({tool})", "completed": None}
    try:
        r = subprocess.run(["node", tool, "query", "init.progress", "--ws", GSD_WS, "--raw"], cwd=str(repo),
                           capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "inconclusive": True, "detail": f"init.progress did not run: {type(exc).__name__}", "completed": None}
    out = r.stdout.strip()
    if out.startswith("@file:"):
        try:
            out = Path(out[len("@file:"):]).read_text(encoding="utf-8")
        except OSError:
            return {"ok": False, "inconclusive": True, "detail": "init.progress @file output unreadable", "completed": None}
    try:
        doc = json.loads(out)
    except ValueError:
        return {"ok": False, "inconclusive": True, "detail": f"init.progress output is not JSON (exit {r.returncode})", "completed": None}
    completed = doc.get("completed_count")
    phases = {str(p.get("number")): bool(p.get("phase_complete")) for p in doc.get("phases") or []}
    missing = [n for n in (f"{i:02d}" for i in range(1, MIN_COMPLETED + 1)) if not phases.get(n)]
    ok = isinstance(completed, int) and completed >= MIN_COMPLETED and not missing
    detail = f"completed_count={completed}; phases 01-0{MIN_COMPLETED} not complete: {missing or 'none'}"
    return {"ok": ok, "inconclusive": False, "detail": detail, "completed": completed}


# ------------------------------------------------------------------------------------------------ the checker
def check_incidents(paths, evidence_dir, repo, gsd_tools: str | None = None) -> list[dict]:
    """Findings (possibly empty) for each incident file. `evidence_dir` holds <suite stem>.out files from a suite run
    made in this phase. Nothing is written."""
    repo = Path(repo)
    evidence_dir = Path(evidence_dir) if evidence_dir is not None else None
    findings: list[dict] = []
    for path in paths:
        path = Path(path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(finding(path, "INCONCLUSIVE_UNREADABLE", type(exc).__name__))
            continue
        if not re.search(r"^#\s+\S", text, re.M):
            findings.append(finding(path, "MISSING_TITLE", "no '# ' title line"))
        if not re.search(r"^\*\*Class:\*\*\s*\S", text, re.M):
            findings.append(finding(path, "MISSING_SECTION", "Class: no '**Class:**' line with content"))
        secs = _sections(text)
        for name in REQUIRED_SECTIONS:
            key = name.lower()
            hit = next((k for k in secs if k == key or k.startswith(key + " ")), None)
            if hit is None:
                findings.append(finding(path, "MISSING_SECTION", name))
            elif not secs[hit].strip():
                findings.append(finding(path, "EMPTY_SECTION", name))
        test_key = next((k for k in secs if k == "test" or k.startswith("test ")), None)
        cites = parse_citations(secs.get(test_key, "")) if test_key else {"gates": [], "commits": [], "checks": []}
        if not cites["commits"]:
            findings.append(finding(path, "NO_COMMIT_CITATION", "the Test section cites no 'commit:' line"))
        if not cites["gates"] and not cites["checks"]:
            findings.append(finding(path, "NO_TEST_CITATION", "the Test section cites no 'gate:' or 'check:' line"))
        for h in cites["commits"]:
            if not _git_resolves(repo, h):
                findings.append(finding(path, "COMMIT_UNRESOLVED", h))
        for chk in cites["checks"]:
            if chk != "init-progress":
                findings.append(finding(path, "UNKNOWN_CHECK", chk))
                continue
            ip = init_progress(repo, gsd_tools)
            if ip["inconclusive"]:
                findings.append(finding(path, "INCONCLUSIVE_INIT_PROGRESS", ip["detail"]))
            elif not ip["ok"]:
                findings.append(finding(path, "INIT_PROGRESS_FAILED", ip["detail"]))
        if cites["gates"]:
            have_ev = evidence_dir is not None and evidence_dir.is_dir() and any(evidence_dir.glob("*.out"))
            if not have_ev:
                findings.append(finding(path, "INCONCLUSIVE_NO_EVIDENCE",
                                        f"gate citations present but evidence directory {evidence_dir} is missing or empty"))
                continue
        for gate, tfile in cites["gates"]:
            tpath = repo / tfile
            try:
                ttext = tpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                findings.append(finding(path, "GATE_TESTFILE_MISSING", f"{gate} in {tfile}"))
                continue
            if not _gate_in_text(gate, ttext):
                findings.append(finding(path, "GATE_NOT_IN_TESTFILE", f"{gate} not literal in {tfile}"))
                continue
            lines = _evidence_lines(evidence_dir, Path(tfile).stem)
            if lines is None:
                findings.append(finding(path, "GATE_NO_PASS_LINE", f"{gate}: no {Path(tfile).stem}.out in evidence"))
                continue
            esc = re.escape(gate)
            if any(re.match(rf"^\s*FAIL\s+{esc}(\s|$)", ln) for ln in lines):
                findings.append(finding(path, "GATE_FAILED_IN_EVIDENCE", gate))
            elif not any(re.match(rf"^\s*PASS\s+{esc}(\s|$)", ln) for ln in lines):
                findings.append(finding(path, "GATE_NO_PASS_LINE", f"{gate}: no PASS line in {Path(tfile).stem}.out"))
    return findings


# ------------------------------------------------------------------------------------------------ selftest
def _expect(findings: list[dict], code: str) -> bool:
    return any(f["code"] == code for f in findings)


def selftest(repo: Path = REPO, base: str | None = None) -> int:
    """Each negative case is a mutated temp copy of a REAL incident file run through the REAL checker; it must produce
    its named finding. The unmodified copy (and the copy with a valid gate) must produce none."""
    base_path = Path(base) if base else repo / "vault/incidents/2026-10-24-flow-compression-phase-seal-without-frontmatter.md"
    original = base_path.read_text(encoding="utf-8")
    passes = fails = 0

    def record(name: str, ok: bool, why: str = "") -> None:
        nonlocal passes, fails
        if ok:
            passes += 1
            print(f"PASS {name} {why}".rstrip())
        else:
            fails += 1
            print(f"FAIL {name} {why}".rstrip())

    with tempfile.TemporaryDirectory(prefix="s9kv-selftest-") as td:
        td = Path(td)
        ev = td / "evidence"
        ev.mkdir()
        gate = "V-S6-HOLD-PARKS-TYPED"
        (ev / "test_s6_blockers.out").write_text(f"PASS V-S6-TRACER-FAIL-OPEN \nPASS {gate} ok\n", encoding="utf-8")
        gate_line = f"- gate: {gate} in tools/test_s6_blockers.py\n"

        def run(name_text: str, text: str, evidence=ev, gsd_tools=None) -> list[dict]:
            p = td / f"{name_text}.md"
            p.write_text(text, encoding="utf-8")
            return check_incidents([p], evidence, repo, gsd_tools=gsd_tools)

        def add_gate(text: str, line: str) -> str:
            return text.replace("## Pattern", line + "\n## Pattern", 1)

        # controls: the real file, and the real file with one valid gate, both clean
        f = run("control_clean", original)
        record("S9KV-CONTROL-CLEAN", f == [], f"findings={[x['code'] for x in f]}")
        f = run("control_gate", add_gate(original, gate_line))
        record("S9KV-CONTROL-GATE-CLEAN", f == [], f"findings={[x['code'] for x in f]}")

        # section removed (one case per required heading shape: heading line deleted)
        f = run("no_symptom", original.replace("## Symptom", "## Elsewhere", 1))
        record("S9KV-NEG-SECTION-REMOVED", _expect(f, "MISSING_SECTION"), f"findings={[x['code'] for x in f]}")
        body = re.sub(r"(## Pattern\n).*?(\n## Open debt)", r"\1\2", original, flags=re.S)
        f = run("empty_pattern", body)
        record("S9KV-NEG-SECTION-EMPTY", _expect(f, "EMPTY_SECTION"), f"findings={[x['code'] for x in f]}")
        f = run("no_class", original.replace("**Class:**", "Class:", 1))
        record("S9KV-NEG-CLASS-LINE-REMOVED", _expect(f, "MISSING_SECTION"), f"findings={[x['code'] for x in f]}")
        # commit replaced by an unresolvable hash
        f = run("bad_commit", re.sub(r"commit: [0-9a-f]{8}", "commit: deadbeef", original, count=1))
        record("S9KV-NEG-COMMIT-UNRESOLVABLE", _expect(f, "COMMIT_UNRESOLVED"), f"findings={[x['code'] for x in f]}")
        # all commit lines removed
        f = run("no_commit", re.sub(r"- commit: [0-9a-f]+\n", "", original))
        record("S9KV-NEG-NO-COMMIT-CITATION", _expect(f, "NO_COMMIT_CITATION"), f"findings={[x['code'] for x in f]}")
        # gate id absent from the test file
        f = run("gate_absent", add_gate(original, "- gate: V-S6-NO-SUCH-GATE-XYZ in tools/test_s6_blockers.py\n"))
        record("S9KV-NEG-GATE-ABSENT-FROM-TESTFILE", _expect(f, "GATE_NOT_IN_TESTFILE"), f"findings={[x['code'] for x in f]}")
        # gate present in the file but FAIL in the evidence
        ev_fail = td / "evidence_fail"
        ev_fail.mkdir()
        (ev_fail / "test_s6_blockers.out").write_text(f"FAIL {gate} broke\n", encoding="utf-8")
        f = run("gate_fail", add_gate(original, gate_line), evidence=ev_fail)
        record("S9KV-NEG-GATE-FAIL-IN-EVIDENCE", _expect(f, "GATE_FAILED_IN_EVIDENCE"), f"findings={[x['code'] for x in f]}")
        # gate present in the file, no PASS line at all
        ev_none = td / "evidence_nopass"
        ev_none.mkdir()
        (ev_none / "test_s6_blockers.out").write_text("PASS V-S6-TRACER-FAIL-OPEN \n", encoding="utf-8")
        f = run("gate_nopass", add_gate(original, gate_line), evidence=ev_none)
        record("S9KV-NEG-GATE-NO-PASS-LINE", _expect(f, "GATE_NO_PASS_LINE"), f"findings={[x['code'] for x in f]}")
        # evidence directory missing -> INCONCLUSIVE and exit 2, not a pass
        f = run("ev_missing", add_gate(original, gate_line), evidence=td / "no_such_dir")
        record("S9KV-NEG-EVIDENCE-MISSING-EXIT2", _expect(f, "INCONCLUSIVE_NO_EVIDENCE") and exit_code(f) == 2,
               f"findings={[x['code'] for x in f]} exit={exit_code(f)}")
        # check line removed and no gate -> no test citation remains
        f = run("no_check", re.sub(r"- check: init-progress\n", "", original))
        record("S9KV-NEG-NO-TEST-CITATION", _expect(f, "NO_TEST_CITATION"), f"findings={[x['code'] for x in f]}")
        # init-progress instrument says the count regressed -> finding (a fake gsd-tools stands in for the instrument)
        fake = td / "fake-gsd-tools.cjs"
        fake.write_text("console.log(JSON.stringify({completed_count: 3, phases: []}))\n", encoding="utf-8")
        f = run("ip_regress", original, gsd_tools=str(fake))
        record("S9KV-NEG-INIT-PROGRESS-REGRESSED", _expect(f, "INIT_PROGRESS_FAILED"), f"findings={[x['code'] for x in f]}")
        # init-progress instrument missing -> INCONCLUSIVE exit 2
        f = run("ip_missing", original, gsd_tools=str(td / "absent.cjs"))
        record("S9KV-NEG-INIT-PROGRESS-UNAVAILABLE-EXIT2", exit_code(f) == 2, f"findings={[x['code'] for x in f]}")
        # exit_code ordering: a failure alongside an INCONCLUSIVE stays 2; failure alone is 1; empty is 0
        record("S9KV-EXIT-CODES", exit_code([]) == 0 and exit_code([finding("x", "EMPTY_SECTION", "")]) == 1
               and exit_code([finding("x", "INCONCLUSIVE_NO_EVIDENCE", ""), finding("x", "EMPTY_SECTION", "")]) == 2)
    total = passes + fails
    print(f"SELFTEST_PASS={passes}/{total}")
    return 0 if fails == 0 else 1


# ------------------------------------------------------------------------------------------------ CLI
def _cmd_incidents(args) -> int:
    pattern = args.glob if os.path.isabs(args.glob) else str(REPO / args.glob)
    paths = sorted(_glob.glob(pattern))
    if args.expect is not None and len(paths) != args.expect:
        print(f"FINDING glob matched {len(paths)} files, expected {args.expect}")
        return 1
    if not paths:
        print("FINDING glob matched no files")
        return 1
    findings = check_incidents(paths, args.evidence, REPO)
    for f in findings:
        print(f"FINDING {Path(f['file']).name} {f['code']} {f['detail']}")
    code = exit_code(findings)
    print(f"INCIDENTS files={len(paths)} findings={len(findings)} exit={code}")
    return code


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("incidents")
    p.add_argument("--glob", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--expect", type=int)
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.cmd == "incidents":
        return _cmd_incidents(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
