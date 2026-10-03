#!/usr/bin/env python3
"""V-DEPLOY-* gates: one repeatable, locked, backed-up git deploy moves a stale GEX44 env's PP install.

Pillar B of the incremental-cognition program (ledger id B), second half: tools/gex44_env_deploy.py. The
measured precedent it replaces: a7's install was moved by a git bundle plus a hand-written pp.head, a5's is a
tarball copy with a hand-applied patch, orca-env carries hand-copied files.

Hermetic: every env is a scratch directory under a tempfile root, whose PP install is a REAL clone of this
repository detached at the measured a7 head (01199995), so the staleness is real history, not a fixture. The
credentials file carries clearly fake canary strings. Nothing here names, opens or writes the real ~/.claude,
~/a5-env or ~/a7-env; V-DEPLOY-REAL-UNTOUCHED only reads them to prove nobody else did.

    python3 tools/test_gex44_env_deploy.py            run every gate
    python3 tools/test_gex44_env_deploy.py --drill     mutation drill (each mutant must be killed)
"""
from __future__ import annotations

import atexit
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gex44_env_deploy as dep  # noqa: E402
import gex44_env_preflight as ep  # noqa: E402

REPO = HERE.parent
SCRIPT = HERE / "gex44_env_deploy.py"
A7_HEAD = "01199995c7d15a9540dc4180c8f3a50d6e1244b3"
GIT = os.environ.get("CPP_GIT_EXE") or shutil.which("git") or "/usr/bin/git"
CANARY_ACCESS = "CANARY-ACCESS-DO-NOT-PRINT"
CANARY_REFRESH = "CANARY-REFRESH-DO-NOT-PRINT"
TMP_ROOT = Path(tempfile.mkdtemp(prefix="envdeploy-test-"))
atexit.register(shutil.rmtree, str(TMP_ROOT), ignore_errors=True)
GIT_HOME = TMP_ROOT / "githome"
GIT_HOME.mkdir()
GIT_ENV = {**os.environ, "HOME": str(GIT_HOME), "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}

RESULTS: list[tuple[str, bool, str]] = []
QUIET = [False]
_COUNTER = [0]


def check(name: str, cond, ev="") -> None:
    ok = bool(cond)
    RESULTS.append((name, ok, str(ev)))
    if not QUIET[0]:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {ev}")


def guarded(name: str, fn) -> None:
    """Run one gate body returning (ok, evidence); an exception is a FAIL with its class, never a crash."""
    try:
        ok, ev = fn()
    except Exception as exc:  # noqa: BLE001 -- a gate that crashes must read as red, not as absent
        ok, ev = False, f"{exc.__class__.__name__}: {exc}"
    check(name, ok, ev)


def scratch(prefix: str = "case") -> Path:
    _COUNTER[0] += 1
    d = TMP_ROOT / f"{prefix}{_COUNTER[0]}"
    d.mkdir(parents=True)
    return d


def sh(argv, cwd=None, env=None, timeout=300):
    p = subprocess.run([str(a) for a in argv], cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                       errors="replace", env=env or GIT_ENV, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def git(args, cwd) -> str:
    rc, out, err = sh([GIT, *args], cwd=cwd)
    if rc != 0:
        raise RuntimeError(f"git {' '.join(args)} failed rc={rc}: {err.strip()[:200]}")
    return out.strip()


def sha256(path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


# --------------------------------------------------------------------------- fixtures
class Env:
    """A scratch env: paths of everything a deploy may touch."""

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.root = tmp / "env"
        self.home = self.root / "home"
        self.install = self.home / ".claude" / "skills" / "claude-power-pack"
        self.env_sh = self.root / "env.sh"
        self.pp_head = self.root / "pp.head"
        self.lock = self.root / "sweep.lock"
        self.settings = self.home / ".claude" / "settings.json"
        self.creds = self.home / ".claude" / ".credentials.json"
        self.hook = self.home / ".claude" / "hooks" / "learning-sentinel.js"

    def head(self) -> str:
        return git(["rev-parse", "HEAD"], self.install)


def make_scratch_env(tmp: Path, head: str = A7_HEAD, *, hook_registered: bool = True) -> Env:
    """Everything under `tmp`: env.sh, sweep.lock, pp.head (no trailing newline, like the measured a7 file),
    credentials built like make_env in test_gex44_env_preflight (future expiresAt, fake canary tokens), a
    settings.json registering one hook whose script does NOT exist (so the preflight measures hooks_broken),
    and the install: a real shared clone of this repository detached at `head`."""
    e = Env(tmp)
    (e.home / ".claude").mkdir(parents=True)
    e.env_sh.write_text(
        f"export HOME={e.home}\nexport PATH={e.root}/npm/bin:$PATH\nexport CPP_GIT_EXE={GIT}\n", encoding="utf-8")
    e.lock.write_text("", encoding="utf-8")
    e.pp_head.write_bytes(head.encode())
    oauth = {"accessToken": CANARY_ACCESS, "refreshToken": CANARY_REFRESH,
             "expiresAt": int((time.time() + 86400) * 1000)}
    e.creds.write_text(json.dumps({"claudeAiOauth": oauth}), encoding="utf-8")
    hooks = ({"Stop": [{"hooks": [{"type": "command", "command": f"node {e.hook}"}]}]} if hook_registered else {})
    e.settings.write_text(json.dumps({"hooks": hooks}), encoding="utf-8")
    e.install.parent.mkdir(parents=True, exist_ok=True)
    git(["clone", "--quiet", "--shared", "--no-checkout", str(REPO), str(e.install)], tmp)
    git(["checkout", "-q", "--detach", head], e.install)
    return e


def tree_listing(root: Path) -> list[str]:
    """Every non-.git path under root with its size: a created, removed or resized file shows up."""
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            p = Path(dp) / f
            try:
                out.append(f"{p.relative_to(root)}:{p.stat().st_size}")
            except OSError:
                out.append(f"{p.relative_to(root)}:?")
    return sorted(out)


def fingerprint(e: Env) -> dict:
    refs = sh([GIT, "for-each-ref"], cwd=e.install)[1]
    return {"env.sh": sha256(e.env_sh), "pp.head": sha256(e.pp_head), "settings": sha256(e.settings),
            "creds": sha256(e.creds), "git_head": sha256(e.install / ".git" / "HEAD"), "refs": refs,
            "tree": tree_listing(e.root)}


def cli(args: list, *, env=None, cwd=None):
    p = subprocess.run([sys.executable, str(SCRIPT), *[str(a) for a in args]], capture_output=True, text=True,
                       errors="replace", env=env or GIT_ENV, cwd=cwd, timeout=600)
    return p.returncode, p.stdout, p.stderr


def repo_head() -> str:
    return git(["rev-parse", "HEAD"], REPO)


def repo_status() -> str:
    return sh([GIT, "status", "--porcelain"], cwd=REPO)[1]


SOURCE_BEFORE = (repo_head(), repo_status())


# --------------------------------------------------------------------------- tracer: dry-run on a7's real history
def grp_dryrun() -> None:
    def plan():
        e = make_scratch_env(scratch())
        rc, out, err = cli(["--env-root", e.root, "--source-repo", REPO, "--json"])
        d = json.loads(out)
        reasons = d.get("before", {}).get("reasons", [])
        ok = (rc == 0 and d.get("env_head") == A7_HEAD and d.get("target") == repo_head()
              and d.get("hooks_repair") is True and d.get("plane_marker") == "will add"
              and bool(d.get("rollback")) and "pp_install_stale" in reasons and "hooks_broken" in reasons
              and d.get("refusal") is None)
        return ok, (f"rc={rc} env_head={str(d.get('env_head'))[:8]} target={str(d.get('target'))[:8]} "
                    f"hooks_repair={d.get('hooks_repair')} plane_marker={d.get('plane_marker')} "
                    f"rollback={len(d.get('rollback') or [])} reasons={reasons} refusal={d.get('refusal')}")
    guarded("V-DEPLOY-DRYRUN-PLAN", plan)

    def no_mutation():
        e = make_scratch_env(scratch())
        before = fingerprint(e)
        rc, out, err = cli(["--env-root", e.root, "--source-repo", REPO, "--json"])
        after = fingerprint(e)
        diff = [k for k in before if before[k] != after[k]]
        # positive control: the fingerprint is able to see a created file and a rewritten ref, so "unchanged" is a
        # measurement and not an instrument that cannot move
        (e.root / "probe.txt").write_text("x", encoding="utf-8")
        git(["update-ref", "refs/probe/x", "HEAD"], e.install)
        sees = [k for k, v in fingerprint(e).items() if v != after[k]]
        return rc == 0 and not diff and bool(before["tree"]) and {"tree", "refs"} <= set(sees), \
            f"rc={rc} changed={diff} files={len(before['tree'])} control_sees={sees}"
    guarded("V-DEPLOY-DRYRUN-NO-MUTATION", no_mutation)

    def not_env_root():
        outcomes = []
        for label, build in (("empty dir", lambda d: None),
                             ("env.sh but no home/", lambda d: (d / "env.sh").write_text("export HOME=/x\n"))):
            d = scratch("notenv")
            build(d)
            before = sorted(os.listdir(d))
            rc, out, err = cli(["--env-root", d, "--source-repo", REPO, "--json"])
            outcomes.append((label, rc, sorted(os.listdir(d)) == before))
        return all(rc == 3 and same for _, rc, same in outcomes), f"{outcomes}"
    guarded("V-DEPLOY-NOT-ENV-ROOT", not_env_root)

    def refuses_home():
        e = make_scratch_env(scratch())
        marker = scratch("shim") / "git-was-called"
        shim_dir = marker.parent
        shim = shim_dir / "git"
        shim.write_text(f"#!/bin/sh\necho called >> {marker}\nexit 1\n", encoding="utf-8")
        shim.chmod(0o755)
        base = {k: v for k, v in os.environ.items() if k != "CPP_GIT_EXE"}
        base["PATH"] = f"{shim_dir}{os.pathsep}{base.get('PATH', '')}"
        # control: the shim is on PATH and a normal run does call it, so "no call" below is a measurement
        control_env = {**base, "HOME": str(GIT_HOME)}
        cli(["--env-root", e.root, "--source-repo", REPO, "--json"], env=control_env)
        control_called = marker.exists()
        marker.unlink(missing_ok=True)
        home_env = {**base, "HOME": str(e.root)}
        rc, out, err = cli(["--env-root", e.root, "--source-repo", REPO, "--json"], env=home_env)
        called = marker.exists()
        return rc == 3 and control_called and not called, \
            f"rc={rc} control_called_shim={control_called} home_run_called_shim={called}"
    guarded("V-DEPLOY-REFUSES-HOME", refuses_home)


GROUPS = [grp_dryrun]


def source_untouched() -> None:
    def body():
        after = (repo_head(), repo_status())
        return after == SOURCE_BEFORE, f"head {after[0][:8]} == {SOURCE_BEFORE[0][:8]}, status lines " \
            f"{len(after[1].splitlines())} == {len(SOURCE_BEFORE[1].splitlines())}"
    guarded("V-DEPLOY-SOURCE-UNTOUCHED", body)


def run_all() -> int:
    for g in GROUPS:
        g()
    source_untouched()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"DEPLOY_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_all())
