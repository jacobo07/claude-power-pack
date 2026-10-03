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
import contextlib
import fcntl
import hashlib
import io
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
    except (Exception, SystemExit) as exc:  # noqa: BLE001 -- a gate that crashes must read as red, not as absent
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


def make_scratch_env(tmp: Path, head: str = A7_HEAD, *, hook_registered: bool = True, shared: bool = True) -> Env:
    """Everything under `tmp`: env.sh, sweep.lock, pp.head (no trailing newline, like the measured a7 file),
    credentials built like make_env in test_gex44_env_preflight (future expiresAt, fake canary tokens), a
    settings.json registering one hook whose script does NOT exist (so the preflight measures hooks_broken),
    and the install: a real clone of this repository detached at `head`. `shared=False` builds a standalone
    repository holding only the history up to `head` (fetched by sha), so a deploy must really fetch."""
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
    if shared:
        git(["clone", "--quiet", "--shared", "--no-checkout", str(REPO), str(e.install)], tmp)
        git(["checkout", "-q", "--detach", head], e.install)
    else:
        e.install.mkdir(parents=True)
        git(["init", "-q"], e.install)
        git(["fetch", "--quiet", "--no-tags", str(REPO), head], e.install)
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
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = dep.main(["--env-root", str(e.root), "--source-repo", str(REPO), "--json"])
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


# --------------------------------------------------------------------------- apply path
def stamp_files(e: Env, prefix: str) -> list[str]:
    return sorted(p.name for p in e.root.glob(prefix + "*"))


def ref_target(e: Env, ref: str) -> str | None:
    rc, out, _ = sh([GIT, "rev-parse", "--verify", "--quiet", ref], cwd=e.install)
    return out.strip() if rc == 0 else None


def grp_apply() -> None:
    def apply_ok():
        e = make_scratch_env(scratch(), shared=False)       # standalone history: the deploy must really fetch
        target = repo_head()
        env_sh0, creds0 = e.env_sh.read_bytes(), sha256(e.creds)
        pre_has_target = sh([GIT, "cat-file", "-e", target + "^{commit}"], cwd=e.install)[0] == 0
        res = dep.apply_deploy(e.root, REPO)
        ts = res.get("ts", "?")
        after_reasons = (res.get("after") or {}).get("reasons", [])
        env_sh1 = e.env_sh.read_bytes()
        log_lines = e.root.joinpath("pp-deploy.log").read_text(encoding="utf-8").splitlines() \
            if e.root.joinpath("pp-deploy.log").is_file() else []
        bak_env = e.root / f"env.sh.bak-{ts}"
        bak_head = e.root / f"pp.head.bak-{ts}"
        ok = (res.get("code") == 0 and not pre_has_target and e.head() == target
              and ref_target(e, f"refs/pp-deploy/backup-{ts}") == A7_HEAD
              and e.pp_head.read_bytes() == target.encode() and bak_head.read_bytes() == A7_HEAD.encode()
              and env_sh1 == env_sh0 + (dep.PLANE_LINE + "\n").encode() and bak_env.read_bytes() == env_sh0
              and e.hook.is_file() and "pp_install_stale" not in after_reasons
              and "hooks_broken" not in after_reasons and len(log_lines) == 1
              and json.loads(log_lines[0]).get("target") == target and sha256(e.creds) == creds0
              and (res.get("installer") or {}).get("rc") == 0)
        return ok, (f"code={res.get('code')} target_was_absent={not pre_has_target} head==target={e.head() == target} "
                    f"backup_ref->old={ref_target(e, f'refs/pp-deploy/backup-{ts}') == A7_HEAD} "
                    f"env.sh+1line={env_sh1 == env_sh0 + (dep.PLANE_LINE + chr(10)).encode()} bak_env={bak_env.is_file()} "
                    f"bak_head={bak_head.is_file()} hook_restored={e.hook.is_file()} after_reasons={after_reasons} "
                    f"log_lines={len(log_lines)} installer_rc={(res.get('installer') or {}).get('rc')}")
    guarded("V-DEPLOY-APPLY", apply_ok)

    def idempotent():
        e = make_scratch_env(scratch())
        first = dep.apply_deploy(e.root, REPO)
        head1, baks1, tree1 = e.head(), stamp_files(e, "env.sh.bak-") + stamp_files(e, "pp.head.bak-"), fingerprint(e)
        second = dep.apply_deploy(e.root, REPO)
        baks2, tree2 = stamp_files(e, "env.sh.bak-") + stamp_files(e, "pp.head.bak-"), fingerprint(e)
        changed = [k for k in tree1 if k not in ("tree",) and tree1[k] != tree2[k]]
        ok = (first.get("code") == 0 and second.get("code") == 0 and second.get("already_at_target") is True
              and e.head() == head1 and baks1 == baks2 and not changed)
        return ok, (f"first={first.get('code')} second={second.get('code')} already={second.get('already_at_target')} "
                    f"head_same={e.head() == head1} backups {len(baks1)}->{len(baks2)} changed={changed}")
    guarded("V-DEPLOY-IDEMPOTENT", idempotent)

    def credentials_untouched():
        e = make_scratch_env(scratch())
        before = (sha256(e.creds), e.creds.stat().st_mtime_ns, e.creds.stat().st_mode)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = dep.main(["--env-root", str(e.root), "--source-repo", str(REPO), "--commit", "HEAD", "--apply"])
        res = dep.apply_deploy(e.root, REPO)
        out = buf.getvalue() + json.dumps(res, default=str) + e.root.joinpath("pp-deploy.log").read_text(encoding="utf-8")
        after = (sha256(e.creds), e.creds.stat().st_mtime_ns, e.creds.stat().st_mode)
        leaked = [c for c in (CANARY_ACCESS, CANARY_REFRESH) if c in out]
        return rc == 0 and before == after and not leaked, f"rc={rc} identical={before == after} leaked={leaked}"
    guarded("V-DEPLOY-CREDENTIALS-UNTOUCHED", credentials_untouched)


def grp_refusals() -> None:
    def dirty():
        e = make_scratch_env(scratch())
        victim = e.install / "README.md"
        victim = victim if victim.is_file() else e.install / git(["ls-files"], e.install).splitlines()[0]
        victim.write_bytes(victim.read_bytes() + b"\nhand patch\n")
        before, body = fingerprint(e), victim.read_bytes()
        res = dep.apply_deploy(e.root, REPO)
        after = fingerprint(e)
        ok = (res.get("code") == 4 and victim.read_bytes() == body and e.head() == A7_HEAD
              and not [k for k in before if k != "tree" and before[k] != after[k]]
              and victim.name in (res.get("refusal") or {}).get("why", ""))
        return ok, f"code={res.get('code')} file_intact={victim.read_bytes() == body} head={e.head()[:8]} why={(res.get('refusal') or {}).get('why', '')[:80]}"
    guarded("V-DEPLOY-DIRTY-REFUSED", dirty)

    def not_ancestor():
        e = make_scratch_env(scratch(), head=repo_head())     # env is AHEAD of the older commit asked for
        before = fingerprint(e)
        res = dep.apply_deploy(e.root, REPO, A7_HEAD)
        after = fingerprint(e)
        ok = res.get("code") == 5 and before == after and e.head() == repo_head()
        return ok, f"code={res.get('code')} unchanged={before == after} head={e.head()[:8]} why={(res.get('refusal') or {}).get('why', '')[:90]}"
    guarded("V-DEPLOY-NOT-ANCESTOR-REFUSED", not_ancestor)

    def lock_held():
        e = make_scratch_env(scratch())
        before = fingerprint(e)
        with open(e.lock, "a") as holder:
            fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)         # the cron sweep holds this same file
            res = dep.apply_deploy(e.root, REPO)
            fcntl.flock(holder, fcntl.LOCK_UN)
        after = fingerprint(e)
        ok = res.get("code") == 6 and e.head() == A7_HEAD and before == after
        return ok, f"code={res.get('code')} head={e.head()[:8]} unchanged={before == after}"
    guarded("V-DEPLOY-LOCK-HELD", lock_held)


def grp_replan() -> None:
    def replan():
        e = make_scratch_env(scratch())
        stale = dep.plan_deploy(e.root, REPO)
        mid = git(["rev-list", "--reverse", "--ancestry-path", f"{A7_HEAD}..HEAD"], REPO).splitlines()[0]
        git(["checkout", "-q", "--detach", mid], e.install)     # the install moves AFTER the plan was computed
        res = dep.apply_deploy(e.root, REPO)
        ts = res.get("ts", "?")
        ok = (stale.get("env_head") == A7_HEAD and res.get("code") == 0 and res.get("old_head") == mid
              and ref_target(e, f"refs/pp-deploy/backup-{ts}") == mid and e.head() == repo_head())
        return ok, (f"stale_plan_env_head={str(stale.get('env_head'))[:8]} apply_old_head={str(res.get('old_head'))[:8]} "
                    f"moved_to={mid[:8]} backup_ref->{str(ref_target(e, f'refs/pp-deploy/backup-{ts}'))[:8]} "
                    f"final={e.head()[:8]}")
    guarded("V-DEPLOY-REPLAN-UNDER-LOCK", replan)


def grp_cli() -> None:
    def cli_exit():
        got = {}
        e = make_scratch_env(scratch())                                   # 4: dirty
        victim = e.install / git(["ls-files"], e.install).splitlines()[0]
        victim.write_bytes(victim.read_bytes() + b"\nx\n")
        got["dirty"] = cli(["--env-root", e.root, "--source-repo", REPO, "--apply"])[0]
        e = make_scratch_env(scratch(), head=repo_head())                 # 5: env ahead of the requested commit
        got["ancestry"] = cli(["--env-root", e.root, "--source-repo", REPO, "--commit", A7_HEAD, "--apply"])[0]
        e = make_scratch_env(scratch())                                   # 6: sweep lock held by another holder
        with open(e.lock, "a") as holder:
            fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
            got["lock"] = cli(["--env-root", e.root, "--source-repo", REPO, "--apply"])[0]
            fcntl.flock(holder, fcntl.LOCK_UN)
        return got == {"dirty": 4, "ancestry": 5, "lock": 6}, f"{got}"
    guarded("V-DEPLOY-CLI-EXIT", cli_exit)

    def cli_apply():
        e = make_scratch_env(scratch())
        rc, out, err = cli(["--env-root", e.root, "--source-repo", REPO, "--commit", "HEAD", "--apply"])
        last = out.strip().splitlines()[-1] if out.strip() else ""
        rb = [ln for ln in out.splitlines() if ln.strip().startswith("git -C")]
        return rc == 0 and e.head() == repo_head() and last.startswith("DEPLOY=APPLIED") and bool(rb), \
            f"rc={rc} head_ok={e.head() == repo_head()} last={last[:90]!r} rollback_lines={len(rb)}"
    guarded("V-DEPLOY-CLI-APPLY", cli_apply)

    def source_text():
        src = SCRIPT.read_text(encoding="utf-8")
        bad = [t for t in ("shell=True", "os.system(", "os.popen(", ".credentials.json") if t in src]
        return not bad, f"forbidden={bad}"
    guarded("V-DEPLOY-NO-SHELL-NO-CREDENTIALS-NAME", source_text)


GROUPS = [grp_dryrun, grp_apply, grp_refusals, grp_replan, grp_cli]


REAL_FILES = [Path("/home/kobii/.claude/settings.json"), Path("/home/kobii/a5-env/env.sh"),
              Path("/home/kobii/a7-env/env.sh"), Path("/home/kobii/a5-env/home/.claude/skills/claude-power-pack/.git/HEAD"),
              Path("/home/kobii/a7-env/home/.claude/skills/claude-power-pack/.git/HEAD")]


def real_state() -> dict:
    out = {}
    for p in REAL_FILES:
        try:
            out[str(p)] = (p.stat().st_size, sha256(p))
        except OSError:
            out[str(p)] = None
    return out


REAL_BEFORE = real_state()


def untouched() -> None:
    def source_body():
        after = (repo_head(), repo_status())
        return after == SOURCE_BEFORE, f"head {after[0][:8]} == {SOURCE_BEFORE[0][:8]}, status lines " \
            f"{len(after[1].splitlines())} == {len(SOURCE_BEFORE[1].splitlines())}"
    guarded("V-DEPLOY-SOURCE-UNTOUCHED", source_body)

    def real_body():
        after = real_state()
        present = [k for k, v in after.items() if v is not None]
        changed = [k for k in after if after[k] != REAL_BEFORE[k]]
        return not changed and len(present) >= 1, f"files={len(after)} present={len(present)} changed={changed}"
    guarded("V-DEPLOY-REAL-UNTOUCHED", real_body)


ALL = GROUPS + [untouched]


def run_all() -> int:
    for g in ALL:
        g()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"DEPLOY_PASS={passed}/{total}  threshold={total}/{total}")
    return 0 if passed == total else 1


# --------------------------------------------------------------------------- mutation drill
def _quiet(groups) -> dict[str, bool]:
    """Run groups with printing off; {gate: passed} for what they recorded."""
    start = len(RESULTS)
    QUIET[0] = True
    try:
        for g in groups:
            g()
    finally:
        QUIET[0] = False
    return {n: ok for n, ok, _ in RESULTS[start:]}


def _patch(obj, attr, value):
    saved = getattr(obj, attr)
    setattr(obj, attr, value)
    return lambda: setattr(obj, attr, saved)


def _m_dirty_skipped():
    return _patch(dep, "_modified_paths", lambda git_exe, install, path: [])


def _m_ancestry_skipped():
    return _patch(dep, "_ancestry", lambda git_exe, src, env_head, target: "ancestor")


def _m_dryrun_applies():
    real = dep.plan_deploy

    def mutant(env_root, source_repo, commit=None, now=None):
        plan = real(env_root, source_repo, commit, now)
        if not plan["refusal"]:      # the mutation: the read-only path also moves the install
            dep._run([ep.env_from_root(plan["env_root"])["git"], "checkout", "-q", "--detach", plan["target"]],
                     plan["install"])
        return plan
    return _patch(dep, "plan_deploy", mutant)


def _m_no_backup():
    return _patch(dep, "_backup_file", lambda src, dst: None)


def _m_lock_ignored():
    return _patch(dep, "_take_lock", lambda path: open(os.devnull))


def _m_prelock_plan():
    real, cache = dep.plan_deploy, {}

    def mutant(env_root, source_repo, commit=None, now=None):
        key = (str(env_root), str(source_repo), commit)
        if key not in cache:        # the mutation: whatever was planned first is what is acted on
            cache[key] = real(env_root, source_repo, commit, now)
        return cache[key]
    return _patch(dep, "plan_deploy", mutant)


MUTANTS = [
    ("M1 dirty check skipped", _m_dirty_skipped, [grp_refusals], ["V-DEPLOY-DIRTY-REFUSED"]),
    ("M2 ancestry check skipped", _m_ancestry_skipped, [grp_refusals], ["V-DEPLOY-NOT-ANCESTOR-REFUSED"]),
    ("M3 dry-run path also applies", _m_dryrun_applies, [grp_dryrun], ["V-DEPLOY-DRYRUN-NO-MUTATION"]),
    ("M4 env.sh/pp.head written without backup", _m_no_backup, [grp_apply], ["V-DEPLOY-APPLY"]),
    ("M5 lock failure ignored", _m_lock_ignored, [grp_refusals], ["V-DEPLOY-LOCK-HELD"]),
    ("M6 apply uses the pre-lock plan", _m_prelock_plan, [grp_replan], ["V-DEPLOY-REPLAN-UNDER-LOCK"]),
]


def run_drill() -> int:
    """Each mutant is applied in-process, the gates it must kill are re-run, the mutant is restored. The
    unmutated control runs first and must be green: a drill whose control is red proves nothing."""
    control = _quiet(ALL)
    control_ok = bool(control) and all(control.values())
    print(f"{'PASS' if control_ok else 'FAIL'} DRILL-CONTROL unmutated run: {sum(control.values())}/{len(control)} gates green")
    killed = 0
    for label, apply, groups, targets in MUTANTS:
        restore = apply()
        try:
            seen = _quiet(groups)
        finally:
            restore()
        why = {n: e for n, _, e in RESULTS[-len(seen):]} if seen else {}
        by = [t for t in targets if seen.get(t) is False]
        if len(by) == len(targets):
            killed += 1
            print(f"KILLED {label} by {', '.join(by)} -- {why.get(by[0], '')[:110]}")
        else:
            print(f"SURVIVED {label} (still green or absent: {', '.join(t for t in targets if seen.get(t) is not False)})")
    after = _quiet(ALL)
    clean = bool(after) and all(after.values())
    print(f"{'PASS' if clean else 'FAIL'} DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: {sum(after.values())}/{len(after)} gates green")
    print(f"DRILL killed={killed}/{len(MUTANTS)}")
    return 0 if (killed == len(MUTANTS) and control_ok and clean) else 1


if __name__ == "__main__":
    sys.exit(run_drill() if "--drill" in sys.argv[1:] else run_all())
