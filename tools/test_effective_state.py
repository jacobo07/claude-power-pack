"""V-EFFECTIVE-* -- does the code this checkout holds reach the tree that runs?

The estate could not answer that. `verify_global_mirrors` compares the
committed blob on a named ref against the live mirrors and is documented as
branch-flip-immune -- rebuilt that way after working-tree reads produced
false DRIFT when concurrent panes switched branches. Correct fix, real
false positive, and it removed the only aperture through which the true
positive was visible. `mirror_unpaired_audit` enrolled these files and
classed them LIVE_FROM_REPO: registered by a repo path, and the file is
there. Silent on WHICH VERSION is there.

For the registrations that execute straight out of the PP repo the
installed copy IS a git working tree, so the bytes that run are whatever
branch a pane last checked out. Measured 2026-09-02: 45 commits on a
pushed branch, 27 files, 0 identical to the running tree.

Every gate here is bookended -- each "reports X" is paired with a "does NOT
report X on the adjacent input" -- because the failure this pins is a gate
that cannot fail. Two branches would otherwise never be driven: LOCAL_EDIT
(zero instances in live data) and the UNRESOLVED arm, so both get real
fixtures rather than an argument that they would work.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))

import tools.mirror_unpaired_audit as mu  # noqa: E402

EXPECTED_GATES = 22
_passes: list[str] = []
_fails: list[str] = []
_TMP: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _tmpdir() -> Path:
    d = tempfile.mkdtemp(prefix="effstate_")
    _TMP.append(d)
    return Path(d)


def _settings_for(root: Path, rel: str = "hooks/x.js") -> str:
    """A settings.json body registering `rel` under `root`."""
    return json.dumps({"hooks": {"PostToolUse": [
        {"matcher": "Bash", "hooks": [
            {"command": f'node "{root.as_posix()}/{rel}"'}]}]}})


def _pair(here: bytes | None, there: bytes | None) -> dict:
    """One repo checkout + one running checkout, one registered hook."""
    base = _tmpdir()
    # Named claude-power-pack on purpose: resolution keys on that segment,
    # so a fixture under a bare temp name resolves to None and every gate
    # below receives zero rows -- which an unwary assertion reads as a pass.
    repo = base / "repo" / "claude-power-pack"
    run = base / "run" / "claude-power-pack"
    for d in (repo / "hooks", run / "hooks"):
        d.mkdir(parents=True)
    if here is not None:
        (repo / "hooks" / "x.js").write_bytes(here)
    if there is not None:
        (run / "hooks" / "x.js").write_bytes(there)
    # main() reads <live-root>/settings.json. Omitting it made the audit
    # resolve nothing, so the exit-path gate below was asserting exit 0
    # against an UNRESOLVED run and calling that a verdict.
    settings = _settings_for(run)
    (run.parent / "settings.json").write_text(settings, encoding="utf-8")
    return {"repo": repo, "run": run, "live_root": run.parent,
            "settings": settings}


def _git_exe() -> str | None:
    for exe in ("git", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            if subprocess.run([exe, "--version"], capture_output=True,
                              timeout=20).returncode == 0:
                return exe
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def _lineage_fixture(mine: bytes | None, theirs: bytes | None,
                     disk: bytes | None) -> dict | None:
    """Two worktrees of ONE repository, each advanced independently.

    `mine` / `theirs`: new committed content for that side, or None to
    leave it at the shared base commit. `disk`: an uncommitted overwrite in
    the running tree. Returns None when git is unavailable, so the caller
    reports the gate unproven rather than passing on a skipped check.
    """
    git = _git_exe()
    if git is None:
        return None
    base = _tmpdir()
    repo = base / "repo" / "claude-power-pack"
    run = base / "run" / "claude-power-pack"
    (repo / "hooks").mkdir(parents=True)
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e",
               GIT_CONFIG_NOSYSTEM="1", HOME=str(base))

    def g(root: Path, *cmd: str):
        return subprocess.run([git, "-C", str(root), *cmd], env=env,
                              capture_output=True, timeout=60)

    (repo / "hooks" / "x.js").write_bytes(b"base\n")
    for cmd in (("init", "-q", "-b", "trunk"), ("add", "-A"),
                ("commit", "-qm", "base")):
        if g(repo, *cmd).returncode != 0:
            return None
    run.parent.mkdir(parents=True, exist_ok=True)
    if g(repo, "worktree", "add", "-q", "-b", "other",
         str(run), "trunk").returncode != 0:
        return None
    if theirs is not None:
        (run / "hooks" / "x.js").write_bytes(theirs)
        g(run, "add", "-A"), g(run, "commit", "-qm", "theirs")
    if mine is not None:
        (repo / "hooks" / "x.js").write_bytes(mine)
        g(repo, "add", "-A"), g(repo, "commit", "-qm", "mine")
    if disk is not None:
        (run / "hooks" / "x.js").write_bytes(disk)
    settings = _settings_for(run)
    (run.parent / "settings.json").write_text(settings, encoding="utf-8")
    return {"repo": repo, "run": run, "live_root": run.parent,
            "settings": settings}


def _status(here: bytes | None, there: bytes | None) -> str:
    f = _pair(here, there)
    res = mu.effective_state(f["repo"], f["settings"])
    rows = res.get("rows") or []
    return rows[0]["status"] if rows else "<no rows>"


def main() -> int:
    # --- root resolution, and its two refusals ------------------------
    f = _pair(b"a", b"a")
    resolved = mu.registered_repo_root(f["settings"])
    if resolved is not None and mu._norm(str(resolved)) == mu._norm(
            str(f["run"])):
        _ok("V-EFFECTIVE-RESOLVES-ROOT",
            f"the registered running checkout resolves to {resolved.parent.name}"
            "/claude-power-pack -- the precondition every gate below needs")
    else:
        _fail("V-EFFECTIVE-RESOLVES-ROOT",
              f"resolved {resolved!r}, wanted {f['run']} -- with no root "
              "the classification gates receive zero rows and an unwary "
              "assertion reads that as a pass")

    real = 'node "C:/Users/User/.claude/skills/claude-power-pack/hooks/a.js"'
    got = mu.registered_repo_root(real)
    if got is not None and got.name == "claude-power-pack":
        _ok("V-EFFECTIVE-RESOLVES-REAL",
            f"a real registration resolves to {got.name}")
    else:
        _fail("V-EFFECTIVE-RESOLVES-REAL", f"resolved {got!r}")

    esc = (r'node "C:\\Users\\User\\.claude\\skills\\claude-power-pack'
           r'\\hooks\\a.js"')
    if mu.registered_repo_root(esc) is not None:
        _ok("V-EFFECTIVE-BACKSLASH-SPELLING",
            "a JSON-escaped backslash registration resolves; a probe that "
            "knows one spelling reports UNREGISTERED for the other two")
    else:
        _fail("V-EFFECTIVE-BACKSLASH-SPELLING",
              "the escaped-backslash spelling did not resolve -- the same "
              "trap this file's _norm docstring already records")

    two = (real + " " +
           'node "D:/other/claude-power-pack/hooks/a.js"')
    if mu.registered_repo_root(two) is None:
        _ok("V-EFFECTIVE-AMBIGUOUS-REFUSES",
            "two distinct checkouts -> refuses to pick; an arbitrary "
            "choice would describe a tree nobody runs")
    else:
        _fail("V-EFFECTIVE-AMBIGUOUS-REFUSES",
              "picked one of two candidate roots")

    unres = mu.effective_state(PP, '{"hooks":{}}')
    if unres["resolved"] is False and not unres["rows"]:
        _ok("V-EFFECTIVE-UNRESOLVED-NOT-PASS",
            "no registration -> resolved=False with no rows, so nothing "
            "here can read as a clean bill")
    else:
        _fail("V-EFFECTIVE-UNRESOLVED-NOT-PASS",
              f"resolved={unres['resolved']} rows={len(unres['rows'])}")

    # --- classification, each bookended -------------------------------
    checks = [
        ("V-EFFECTIVE-DETECTS-SHADOW", b"new bytes\n", b"old bytes\n",
         mu.SHADOWED, "differing bytes are SHADOWED"),
        ("V-EFFECTIVE-ADMITS-IDENTICAL", b"same\n", b"same\n",
         mu.EFFECTIVE, "identical bytes are EFFECTIVE, so the gate is not "
                       "reporting SHADOWED for everything"),
        ("V-EFFECTIVE-CRLF-NOT-DRIFT", b"line\r\ntwo\r\n", b"line\ntwo\n",
         mu.EFFECTIVE, "CRLF vs LF is not drift; this repo produces that "
                       "difference on every checkout"),
        ("V-EFFECTIVE-ABSENT-RUNNING", b"here\n", None,
         mu.ABSENT_RUNNING, "present here, missing there"),
        ("V-EFFECTIVE-NOT-HERE", None, b"there\n",
         mu.NOT_HERE, "absent here is NOT_HERE, never a delivery failure "
                      "of this checkout"),
    ]
    for gate, here, there, want, why in checks:
        got_s = _status(here, there)
        if got_s == want:
            _ok(gate, f"{why} -> {got_s}")
        else:
            _fail(gate, f"expected {want}, got {got_s}")

    # --- LOCAL_EDIT: zero live instances, so drive it with a real repo -
    git = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    base = _tmpdir()
    repo = base / "repo" / "claude-power-pack"
    run = base / "run" / "claude-power-pack"
    (repo / "hooks").mkdir(parents=True)
    (run / "hooks").mkdir(parents=True)
    committed = b"committed\n"
    (repo / "hooks" / "x.js").write_bytes(committed)
    (run / "hooks" / "x.js").write_bytes(committed)
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    ok = True
    for cmd in (["init", "-q"], ["add", "-A"],
                ["commit", "-q", "-m", "x", "--no-gpg-sign"]):
        try:
            r = subprocess.run([git, "-C", str(repo)] + cmd, env=env,
                               capture_output=True, timeout=40)
            ok = ok and r.returncode == 0
        except (OSError, subprocess.SubprocessError):
            ok = False
    # Now edit the working tree ONLY. Running tree still holds HEAD.
    (repo / "hooks" / "x.js").write_bytes(b"uncommitted edit\n")
    if not ok:
        _fail("V-EFFECTIVE-LOCAL-EDIT-NOT-SHADOW",
              "could not build the git fixture, so the branch that "
              "suppresses a false SHADOWED is unproven -- not a skip")
    else:
        st = mu.effective_state(repo, _settings_for(run))["rows"][0]["status"]
        if st == mu.LOCAL_EDIT:
            _ok("V-EFFECTIVE-LOCAL-EDIT-NOT-SHADOW",
                "running tree holds this checkout's COMMITTED bytes, so an "
                "uncommitted edit is LOCAL_EDIT, not a delivery failure")
        else:
            _fail("V-EFFECTIVE-LOCAL-EDIT-NOT-SHADOW",
                  f"got {st}; every uncommitted edit would report as work "
                  "that does not reach production")

    # --- the EXIT path, not just the classifier ------------------------
    shadow = _pair(b"new\n", b"old\n")
    clean = _pair(b"same\n", b"same\n")
    rc_bad = mu.main(["--repo-root", str(shadow["repo"]),
                      "--live-root", str(shadow["live_root"]), "--quiet"])
    rc_ok = mu.main(["--repo-root", str(clean["repo"]),
                     "--live-root", str(clean["live_root"]), "--quiet"])
    if rc_bad == 1:
        _ok("V-EFFECTIVE-FAILS-ON-SHADOW",
            "a shadowed registration exits 1 -- the classifier reaching the "
            "exit code is a separate claim from the classifier being right")
    else:
        _fail("V-EFFECTIVE-FAILS-ON-SHADOW",
              f"exit {rc_bad}; the finding would be printed and not gate")
    if rc_ok == 0:
        _ok("V-EFFECTIVE-PASSES-CLEAN",
            "an aligned checkout exits 0, so the red above is earned")
    else:
        _fail("V-EFFECTIVE-PASSES-CLEAN",
              f"exit {rc_ok} on a clean fixture -- the gate cannot pass")

    # --- DIRECTION, on two real worktrees of one repository ------------
    # The whole point is that SHADOWED cannot tell "my work never arrived"
    # from "their newer work is already here", so nothing short of two
    # lineages sharing an object store exercises it. A mocked blob lookup
    # would agree with whatever the classifier believed.
    for name, mine, theirs, disk, want in (
        ("STRANDED", b"mine\n", None, None, mu.STRANDED),
        ("AHEAD-OF-HERE", None, b"theirs\n", None, mu.AHEAD_OF_HERE),
        ("DIVERGED", b"mine\n", b"theirs\n", None, mu.DIVERGED),
        ("FOREIGN-EDIT", b"mine\n", None, b"scratch\n", mu.FOREIGN_EDIT),
    ):
        f = _lineage_fixture(mine, theirs, disk)
        if f is None:
            _fail("V-EFFECTIVE-" + name, "git unavailable; direction unproven")
            continue
        got = (mu.effective_state(f["repo"], f["settings"])
               .get("rows") or [{}])[0].get("status")
        if got == want:
            _ok("V-EFFECTIVE-" + name, f"-> {got}")
        else:
            _fail("V-EFFECTIVE-" + name, f"got {got}, wanted {want}")

    # A red the owner cannot act on gets the gate switched off, so the two
    # classes where THIS checkout has nothing to deliver must not be
    # counted as its undelivered work -- while still being reported.
    ahead = _lineage_fixture(None, b"theirs\n", None)
    foreign = _lineage_fixture(None, None, b"scratch\n")
    stranded = _lineage_fixture(b"mine\n", None, None)
    if None in (ahead, foreign, stranded):
        _fail("V-EFFECTIVE-UNDELIVERED-IS-MINE-ONLY", "git unavailable")
    else:
        rows = [(mu.effective_state(f["repo"], f["settings"])["rows"] or [{}])[0]
                for f in (ahead, foreign, stranded)]
        owed = [len(mu.undelivered([r])) for r in rows]
        if owed == [0, 0, 1]:
            _ok("V-EFFECTIVE-UNDELIVERED-IS-MINE-ONLY",
                "AHEAD_OF_HERE and an untouched FOREIGN_EDIT are reported "
                "and not charged to this checkout; STRANDED is")
        else:
            _fail("V-EFFECTIVE-UNDELIVERED-IS-MINE-ONLY",
                  f"undelivered counts {owed} for "
                  f"{[r.get('status') for r in rows]}, wanted [0, 0, 1]")

    # FAULT INJECTION. A dead blob reader answers None for every lookup,
    # which is byte-identical to "this path did not exist at that
    # revision". Read through .get() alone, the classifier walked to
    # FOREIGN_EDIT with mine_moved False -- excluded from undelivered, and
    # green. A broken instrument must not be able to produce the
    # reassuring answer, so this drives the failure rather than trusting
    # that it cannot happen.
    stranded_fx = _lineage_fixture(b"mine\n", None, None)
    if stranded_fx is None:
        _fail("V-EFFECTIVE-DEAD-BLOB-READER-BLOCKS", "git unavailable")
    else:
        real = mu._batch_blobs
        try:
            mu._batch_blobs = lambda *_a, **_k: {}
            row = (mu.effective_state(stranded_fx["repo"],
                                      stranded_fx["settings"])["rows"]
                   or [{}])[0]
        finally:
            mu._batch_blobs = real
        if row.get("status") == mu.SHADOWED and len(mu.undelivered([row])) == 1:
            _ok("V-EFFECTIVE-DEAD-BLOB-READER-BLOCKS",
                "no blob evidence -> SHADOWED and still charged as "
                "undelivered, not the FOREIGN_EDIT that would have passed")
        else:
            _fail("V-EFFECTIVE-DEAD-BLOB-READER-BLOCKS",
                  f"status={row.get('status')} mine_moved={row.get('mine_moved')}")

    # The remediation for newer running bytes must never read as "deliver".
    rem = mu.remediation(mu.AHEAD_OF_HERE, same_checkout=False)
    if rem["class"] == mu.INTEGRATE_HERE and rem["owner"] == "this checkout":
        _ok("V-EFFECTIVE-AHEAD-NEVER-OVERWRITES",
            "newer running bytes route to integrate-here, owned by this "
            "checkout -- the action that would have destroyed 22 commits "
            "is not reachable from the classifier's own advice")
    else:
        _fail("V-EFFECTIVE-AHEAD-NEVER-OVERWRITES", str(rem))

    # Direction unknowable must stay blocking. Coercing it to anything
    # softer is how an unmeasured difference reads as an agreement.
    unknown = _status(b"new\n", b"old\n")      # neither side is a git tree
    if unknown == mu.SHADOWED and len(mu.undelivered(
            [{"status": unknown, "mine_moved": None}])) == 1:
        _ok("V-EFFECTIVE-UNKNOWN-DIRECTION-BLOCKS",
            "no shared object store -> SHADOWED, still counted undelivered")
    else:
        _fail("V-EFFECTIVE-UNKNOWN-DIRECTION-BLOCKS", str(unknown))

    # --- live coherence: real settings, statuses from the known set ----
    live = mu.resolve_live_root(None)
    res = mu.effective_state(PP, mu._read(live / "settings.json"))
    known = {mu.EFFECTIVE, mu.SHADOWED, mu.ABSENT_RUNNING, mu.NOT_HERE,
             mu.LOCAL_EDIT, mu.STRANDED, mu.AHEAD_OF_HERE, mu.DIVERGED,
             mu.FOREIGN_EDIT}
    bad = [r for r in res.get("rows", []) if r["status"] not in known]
    if res["resolved"] and res["rows"] and not bad:
        c = res["counts"]
        _ok("V-EFFECTIVE-LIVE-MEASURED",
            f"{len(res['rows'])} live registration(s) classified, all in "
            f"the known set: {dict(sorted(c.items()))}")
    else:
        _fail("V-EFFECTIVE-LIVE-MEASURED",
              f"resolved={res['resolved']} rows={len(res.get('rows', []))} "
              f"unknown_status={[r['status'] for r in bad]}")

    for d in _TMP:
        shutil.rmtree(d, ignore_errors=True)
    ran = len(_passes) + len(_fails)
    print(f"\nEFFECTIVE_PASS={len(_passes)}/{ran}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if ran != EXPECTED_GATES:
        print(f"GATE COUNT MISMATCH: {ran} ran, {EXPECTED_GATES} expected")
        return 1
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
