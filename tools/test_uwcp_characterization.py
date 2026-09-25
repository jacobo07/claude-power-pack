#!/usr/bin/env python3
"""UWCP S0-2: characterization of TODAY's behaviour that UWCP must change.

Every V-UWCP-CHAR-* case asserts the CURRENT (defective) behaviour and is green
on the commit that introduces this file. Each names the slice commit that will
invert it; that commit flips the assertion in place, so the diff between the two
versions of the same test is the evidence (vault/specs/uwcp.md §17-18, S0).

Each defect case sits beside a positive control proving the mechanism it pins
can observe anything at all -- a characterization that passes because the
instrument is blind would invert into a vacuous green later.

    python tools/test_uwcp_characterization.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import brief as gb        # noqa: E402
from modules.gsd_x.goal import contract as gc     # noqa: E402
from modules.gsd_x.goal import epoch as ep        # noqa: E402
from modules.gsd_x.goal import git_state as gs    # noqa: E402
from modules.gsd_x.goal import log as gl          # noqa: E402

REPO = "d" * 40
GIT = next((g for g in gs.GIT_CANDIDATES if shutil.which(g) or Path(g).is_file()), None)


def _git(cwd: Path, *args: str) -> str:
    p = subprocess.run([GIT, "-C", str(cwd), *args], capture_output=True, text=True,
                       timeout=60, stdin=subprocess.DEVNULL)
    if p.returncode != 0:
        raise RuntimeError(f"git {args}: {p.stderr.strip()}")
    return p.stdout.strip()


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    base = Path(tempfile.mkdtemp(prefix="uwcp_char_"))

    # --- C1 late receipt after the epoch ended (inverted by S1-8, fence) -------
    lg = gl.GoalLog(REPO, "g-char", base=base / "goals")
    s = gc.declare(lg, "characterize", ["it runs"], [], {"paths": ["src"]})
    key = ep.info_key(s.revision, [], "fake", "initial", "scope0")
    e1 = ep.begin(lg, gc.project(lg), "fake", {}, key, "initial", "t")
    ep.mark_running(lg, gc.project(lg), e1.epoch_id, {"h": 1}, "t")
    rid_ok = ep.ingest_receipt(lg, gc.project(lg),
                               ep.Receipt(e1.epoch_id, "fake", s.revision, narrative="a"), "t")
    check("V-UWCP-CHAR-RECEIPT-CONTROL", bool(rid_ok),
          "control: a receipt for a running epoch is ingested", "control receipt refused")
    ep.end(lg, gc.project(lg), e1.epoch_id, ep.LOST, "stall abort", "t")
    try:
        ep.ingest_receipt(lg, gc.project(lg),
                          ep.Receipt(e1.epoch_id, "fake", s.revision, narrative="late"), "t")
        late_ingested = True
    except ep.EpochError:
        late_ingested = False
    check("V-UWCP-CHAR-LATE-RECEIPT-INGESTED", late_ingested,
          "TODAY: a receipt arriving after the epoch ended LOST is still ingested "
          "(no fence) -- S1-8 inverts this", "already refused: invert this case in S1-8")

    # --- C2 pins hash working-tree bytes: CRLF vs LF disagree (S1-9) ----------
    lf = base / "lf"
    crlf = base / "crlf"
    for d, nl in ((lf, b"\n"), (crlf, b"\r\n")):
        (d / "gate").mkdir(parents=True)
        (d / "gate" / "t.py").write_bytes(b"print(1)" + nl + b"print(2)" + nl)
    pin_lf = gs.file_pin(lf, ["gate/t.py"])
    pin_crlf = gs.file_pin(crlf, ["gate/t.py"])
    check("V-UWCP-CHAR-PIN-CONTROL", gs.file_pin(lf, ["gate/t.py"]) == pin_lf,
          "control: identical bytes pin identically", "pin not deterministic")
    check("V-UWCP-CHAR-PIN-EOL-SPLIT", pin_lf != pin_crlf,
          "TODAY: one committed file pins differently on a CRLF (Windows) and an LF "
          "(GEX44) checkout -- S1-9 inverts this", "already eol-invariant: invert in S1-9")
    check("V-UWCP-CHAR-SCOPE-EOL-SPLIT",
          ep.scope_hash(lf, ["gate"]) != ep.scope_hash(crlf, ["gate"]),
          "TODAY: scope_hash (the retry key) differs across line endings, so a failed "
          "attempt re-run on the other host passes as new information -- S1-9",
          "already eol-invariant: invert in S1-9")

    # --- C3 scope_hash moves on untracked build debris (S1-9) -----------------
    before = ep.scope_hash(lf, ["gate"])
    (lf / "gate" / "__pycache__").mkdir()
    (lf / "gate" / "__pycache__" / "t.cpython-312.pyc").write_bytes(b"\x00junk")
    check("V-UWCP-CHAR-SCOPE-DEBRIS", ep.scope_hash(lf, ["gate"]) != before,
          "TODAY: running a gate (which writes __pycache__) moves the retry key -- S1-9",
          "already ignores untracked debris: invert in S1-9")

    # --- C4 brief has no total bound (S1-6) -----------------------------------
    big = "x" * 200_000
    lg2 = gl.GoalLog(REPO, "g-brief", base=base / "goals")
    s2 = gc.declare(lg2, big, ["ok"], [], {"paths": ["src"]})
    try:
        text = gb.compile_brief(s2, [], "/w", "task")
    except gb.BriefTooLarge as exc:
        text = ""
        big_refused = str(exc)
    else:
        big_refused = ""
    small = gb.compile_brief(gc.declare(gl.GoalLog(REPO, "g-small", base=base / "goals"),
                                        "small", ["ok"], [], {"paths": ["src"]}), [], "/w", "t")
    check("V-UWCP-CHAR-BRIEF-CONTROL", 0 < len(small) < 4000,
          f"control: an ordinary brief compiles ({len(small)} chars)", "ordinary brief broke")
    # INVERTED by S1-6: was V-UWCP-CHAR-BRIEF-UNBOUNDED (a 200 KB brief compiled).
    check("V-UWCP-BRIEF-BOUNDED", bool(big_refused) and not text,
          f"a 200 KB intent is refused, not cut to fit ({big_refused[:70]}...)",
          f"compiled a {len(text)}-char brief")
    try:
        gb.compile_brief(gc.project(gl.GoalLog(REPO, "g-small", base=base / "goals")),
                         [], "/w", "t", max_tokens=50)
        tok_refused = False
    except gb.BriefTooLarge:
        tok_refused = True
    check("V-UWCP-BRIEF-TOKEN-BOUND", tok_refused,
          "an executor whose window cannot hold the brief is refused before dispatch",
          "a brief over the executor's token bound compiled")

    # --- C5 autonomy passes off-git (UNKNOWN head -> PASS) (S1-10) ------------
    from modules.gsd_x.goal import sweep as sw  # noqa: PLC0415
    old = os.environ.get("GSDX_GOALS_ROOT")
    os.environ["GSDX_GOALS_ROOT"] = str(base / "auto" / "goals")
    try:
        rec = sw.record_path()
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(json.dumps({"head": "a" * 40, "green": True, "suites": {}}),
                       encoding="utf-8")
        nongit = base / "nongit_runtime"
        nongit.mkdir()
        allowed, why = sw.autonomy_verdict(nongit)
        check("V-UWCP-CHAR-AUTONOMY-NONGIT-PASSES", allowed,
              "TODAY: a green record from ANY code licenses autonomy when the runtime is not "
              f"a git tree ({why}) -- S1-10 inverts this", f"already refused: {why}")
        if GIT:
            gitrt = base / "gitrt"
            gitrt.mkdir()
            _git(gitrt, "init", "-q")
            _git(gitrt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                 "--allow-empty", "-m", "r")
            allowed2, why2 = sw.autonomy_verdict(gitrt)
            check("V-UWCP-CHAR-AUTONOMY-CONTROL", not allowed2,
                  "control: on a git runtime a record for another head is refused",
                  f"control failed: {why2}")
    finally:
        if old is None:
            os.environ.pop("GSDX_GOALS_ROOT", None)
        else:
            os.environ["GSDX_GOALS_ROOT"] = old

    # --- C6 the long-run provider cannot start a run (S1-11) ------------------
    from modules.gsd_x.goal.providers.long_run import LongRunProvider  # noqa: PLC0415
    try:
        LongRunProvider(base / "lr").dispatch({"identity": {"run_token": "t"}})
        cannot = False
        why6 = "dispatch returned"
    except ep.EpochError as exc:
        cannot = "cannot start" in str(exc)
        why6 = str(exc)[:90]
    check("V-UWCP-CHAR-LONGRUN-CANNOT-START", cannot,
          "TODAY: the goal spine cannot start a /cpp-gsd-long run although v3 `arm` "
          "exists -- S1-11 inverts this", f"behaviour changed: {why6}")

    # --- C7 repo identity: path key is host-local, no portable id (S1-3) ------
    from modules.repo_identity import identity as ri  # noqa: PLC0415
    if GIT:
        a = base / "clone_a"
        a.mkdir()
        _git(a, "init", "-q")
        (a / "f.txt").write_text("x\n", encoding="utf-8")
        _git(a, "add", "f.txt")
        _git(a, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "root")
        b = base / "elsewhere" / "clone_b"
        b.parent.mkdir()
        subprocess.run([GIT, "clone", "-q", str(a), str(b)], capture_output=True, timeout=60)
        check("V-UWCP-CHAR-REPOID-ROOT-CONTROL", gl.repo_id(a) == gl.repo_id(b),
              "control: the goal log's root-commit id is equal across two clones",
              "root-commit ids differ")
        # INVERTED by S1-3: was V-UWCP-CHAR-REPOKEY-HOSTLOCAL ("no portable id").
        check("V-UWCP-REPOID-PORTABLE",
              ri.repo_key(str(a)) != ri.repo_key(str(b))
              and ri.portable_repo_id(a) == ri.portable_repo_id(b) == gl.repo_id(a),
              "the path key stays host-local by design, and portable_repo_id gives both "
              "clones one id, the same one the goal log uses",
              "portable id missing or disagrees with the goal log")
        sh = base / "shallow"
        (a / "g.txt").write_text("y\n", encoding="utf-8")
        _git(a, "add", "g.txt")
        _git(a, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "two")
        subprocess.run([GIT, "clone", "-q", "--depth", "1", "file://" + a.as_posix(), str(sh)],
                       capture_output=True, timeout=60)
        try:
            ri.portable_repo_id(sh)
            shallow_refused = False
        except ri.PortableIdUnknown:
            shallow_refused = True
        check("V-UWCP-REPOID-SHALLOW-REFUSED", shallow_refused and (sh / ".git").exists(),
              "a shallow clone is refused: its boundary commit is not the root",
              "shallow clone accepted, or the fixture clone did not happen")
        try:
            gl.repo_id(sh)
            wrapper_refuses = False
        except gl.RepoIdUnknown:
            wrapper_refuses = True
        check("V-UWCP-REPOID-WRAPPER-CONTRACT", wrapper_refuses,
              "the goal log keeps raising its own RepoIdUnknown", "wrapper contract changed")
    else:
        fails.append("V-UWCP-CHAR-GIT")
        print("  FAIL V-UWCP-CHAR-GIT: git not found; C5 control and C7 could not run "
              "(HARNESS, not a finding)")

    total = len(passes) + len(fails)
    print(f"UWCP_CHAR_PASS={len(passes)}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
