#!/usr/bin/env python3
"""gex44_env_deploy -- move a stale GEX44 env's PP install to a target commit by git, never by copying files.

Pillar B of the incremental-cognition program, second half. The measured precedent this replaces: a7's install
was moved by a git bundle plus a hand-written pp.head, a5's install is a tarball copy with a hand-applied patch,
and orca-env carries hand-copied gsd_mission.py files. One command, repeatable:

    python3 tools/gex44_env_deploy.py --env-root ~/a7-env --source-repo <PP repo> --commit <rev>           dry-run
    python3 tools/gex44_env_deploy.py --env-root ~/a7-env --source-repo <PP repo> --commit <rev> --apply   deploy

Dry-run is the default and mutates nothing. A plan refuses (exit code in brackets) instead of destroying
something it was not authorized to destroy:

    [3] not an env root / the user's own HOME / install is not a git checkout / revision does not resolve
    [4] the install has modified tracked files (hand patches are the Owner's to decide about, never overwritten)
    [5] the env HEAD is not an ancestor of the target (the deploy never moves an install backwards or sideways)

The deploy never reads, copies or writes a credentials file and never runs the claude binary: auth is judged
only through the read-only preflight (tools/gex44_env_preflight.py). Re-login stays an Owner action.
"""
from __future__ import annotations

import argparse
import atexit
import datetime as _dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gex44_env_preflight as ep  # noqa: E402 -- the one authority on "is this env ready", called not forked

EXIT_OK, EXIT_GUARD, EXIT_DIRTY, EXIT_ANCESTRY, EXIT_LOCK, EXIT_STILL_STALE, EXIT_GIT = 0, 3, 4, 5, 6, 7, 8
PLANE = "gex44"
PLANE_LINE = f"export CPP_MISSION_PLANE={PLANE}"
GIT_TIMEOUT = 120
REPO_ROOT = Path(__file__).resolve().parent.parent

_TMP_HOMES: list[str] = []


def _git_home() -> str:
    """One throwaway HOME for every spawned git: it never reads or writes the caller's git config."""
    if not _TMP_HOMES:
        d = tempfile.mkdtemp(prefix="envdeploy-git-")
        _TMP_HOMES.append(d)
        atexit.register(shutil.rmtree, d, ignore_errors=True)
    return _TMP_HOMES[0]


def _run(argv, cwd, timeout=GIT_TIMEOUT, home=None, path=None):
    """(returncode | None when the program could not start or timed out, stdout, stderr). Argv list, no shell."""
    env = {**os.environ, "HOME": home or _git_home(), "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}
    if path is not None:
        env["PATH"] = path
    try:
        p = subprocess.run([str(a) for a in argv], cwd=str(cwd), capture_output=True, text=True, errors="replace",
                           env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "", f"timeout after {timeout}s"
    except OSError as exc:
        return None, "", exc.__class__.__name__
    return p.returncode, p.stdout, p.stderr


def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _source_git() -> str | None:
    return os.environ.get("CPP_GIT_EXE") or shutil.which("git")


def _refuse(plan: dict, code: int, why: str) -> dict:
    plan["refusal"] = {"code": code, "why": why}
    return plan


def _guard(env_root) -> tuple[Path | None, str | None]:
    """Is this a directory the deploy may treat as an env root? Judged from the path alone, before any git call:
    it must hold env.sh and a home/ directory and must be neither "/", the user's own HOME, nor an ancestor of it."""
    root = Path(env_root).expanduser()
    if not root.is_dir():
        return None, f"not a directory: {root}"
    resolved = root.resolve()
    if resolved == Path(resolved.anchor):
        return None, "refusing the filesystem root"
    try:
        home = Path.home().resolve()
    except (RuntimeError, OSError):
        home = None
    if home is not None and (resolved == home or resolved in home.parents):
        return None, f"refusing {resolved}: it is the user's own HOME or an ancestor of it"
    if not (resolved / "env.sh").is_file() or not (resolved / "home").is_dir():
        return None, f"not an env root (needs env.sh and home/): {resolved}"
    return resolved, None


def _modified_paths(git_exe, install, path) -> list[str] | None:
    """Tracked files the install has modified (the paths), [] when clean, None when git could not say."""
    rc, st, _ = _run([git_exe, "--no-optional-locks", "status", "--porcelain", "--untracked-files=no"], install,
                     path=path)
    return [r[3:] for r in st.splitlines()] if rc == 0 else None


def _ancestry(git_exe, src, env_head, target) -> str:
    """Judged in the SOURCE repo: is the env HEAD an ancestor of (or equal to) the target."""
    rc, _, _ = _run([git_exe, "merge-base", "--is-ancestor", env_head, target], src)
    return "ancestor" if rc == 0 else "env ahead or diverged" if rc == 1 else "env head unknown to the source"


def plan_deploy(env_root, source_repo, commit=None, now=None) -> dict:
    """READ-ONLY. What a deploy of `commit` (default: the source repo's HEAD) to this env would do, or why it
    refuses. A refusal is a field of the plan, never an exception. `now` is only the instant the preflight judges
    credential expiry against (a test seam); backup names always carry the real UTC time of the run."""
    ts = _utc_stamp()
    plan: dict = {"mode": "dry-run", "env_root": str(env_root), "source_repo": str(source_repo),
                  "target_ref": commit or "HEAD", "ts": ts, "refusal": None, "env_head": None, "target": None,
                  "ancestry": None, "already_at_target": None, "modified": [], "hooks_repair": None,
                  "plane_marker": None, "before": None, "rollback": [], "backups": {}}
    root, why = _guard(env_root)
    if why:
        return _refuse(plan, EXIT_GUARD, why)
    plan["env_root"] = str(root)
    try:
        env = ep.env_from_root(root)
    except ValueError as exc:
        return _refuse(plan, EXIT_GUARD, str(exc))
    install = env["install"]
    plan["install"] = install
    igit, sgit = env.get("git") or _source_git(), _source_git()
    if not igit or not os.path.isfile(igit) or not sgit:
        return _refuse(plan, EXIT_GUARD, "no git executable to ask")
    if not os.path.isdir(install):
        return _refuse(plan, EXIT_GUARD, f"no PP install at {install}")
    rc, top, _ = _run([igit, "rev-parse", "--show-toplevel"], install, path=env.get("path"))
    if rc != 0 or os.path.realpath(top.strip()) != os.path.realpath(install):
        return _refuse(plan, EXIT_GUARD, f"the install is not the root of a git checkout: {install}")
    rc, head, _ = _run([igit, "rev-parse", "HEAD"], install, path=env.get("path"))
    if rc != 0:
        return _refuse(plan, EXIT_GUARD, "git could not resolve the install HEAD")
    plan["env_head"] = head.strip()
    modified = _modified_paths(igit, install, env.get("path"))
    if modified is None:
        return _refuse(plan, EXIT_GUARD, "git could not read the install's status")
    plan["modified"] = modified
    ref = commit or "HEAD"
    src = Path(source_repo)
    if ref.startswith("-") or not src.is_dir():
        return _refuse(plan, EXIT_GUARD, f"bad source repo or revision: {source_repo} {ref}")
    rc, tgt, _ = _run([sgit, "rev-parse", "--verify", f"{ref}^{{commit}}"], src)
    if rc != 0 or not re.fullmatch(r"[0-9a-f]{40}", tgt.strip()):
        return _refuse(plan, EXIT_GUARD, f"the source repo {src} does not resolve {ref!r} to a commit")
    plan["target"] = tgt.strip()
    plan["ancestry"] = _ancestry(sgit, src, plan["env_head"], plan["target"])
    plan["already_at_target"] = plan["env_head"] == plan["target"]
    before = ep.run(env, now)
    plan["before"] = {"verdict": before["verdict"], "reasons": before["reasons"],
                      "unmeasured": before["unmeasured"], "findings": before["findings"],
                      "checks": [{"check": c["check"], "state": c["state"], "why": c["why"]}
                                 for c in before["checks"]]}
    plan["hooks_repair"] = "hooks_broken" in before["reasons"]
    plan["plane_marker"] = "present" if "CPP_MISSION_PLANE" in env["env_var_names"] else "will add"
    env_sh, pp_head = root / "env.sh", root / "pp.head"
    plan["backups"] = {"ref": f"refs/pp-deploy/backup-{ts}",
                       "env_sh": f"{env_sh}.bak-{ts}" if plan["plane_marker"] == "will add" else None,
                       "pp_head": f"{pp_head}.bak-{ts}" if pp_head.is_file() else None}
    plan["rollback"] = [f"git -C {install} checkout --detach {plan['env_head']}"]
    if plan["backups"]["env_sh"]:
        plan["rollback"].append(f"cp {plan['backups']['env_sh']} {env_sh}")
    if plan["backups"]["pp_head"]:
        plan["rollback"].append(f"cp {plan['backups']['pp_head']} {pp_head}")
    if plan["modified"]:
        shown = ", ".join(plan["modified"][:20])
        return _refuse(plan, EXIT_DIRTY, f"the install has {len(plan['modified'])} modified tracked file(s): {shown}")
    if plan["ancestry"] != "ancestor":
        return _refuse(plan, EXIT_ANCESTRY, f"the env HEAD {plan['env_head'][:8]} is not an ancestor of the "
                       f"target {plan['target'][:8]}: {plan['ancestry']}")
    return plan


# --------------------------------------------------------------------------- apply
OWNER_ACTIONS = {
    "auth_expired": "the login is expired: re-login in this env (interactive, never copied between envs): "
                    "bash -c '. {env_sh}; exec claude' then /login",
    "auth_missing": "no login in this env: log in interactively: bash -c '. {env_sh}; exec claude' then /login",
    "interpreter_unsupported": "the env's node/python is outside the vendored engine range: upgrade the interpreter "
                               "(Owner action, never bypassed by this deploy)",
}
_SCRIPT_SUFFIXES = (".js", ".cjs", ".mjs", ".py", ".sh")


def _take_lock(path: Path):
    """The env's own sweep lock (the one the 5-minute cron holds with `flock -n`), non-blocking and exclusive.
    The open file object when taken, None when another holder has it."""
    import fcntl
    f = open(path, "a")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def _backup_file(src: Path, dst: Path) -> None:
    """Copy src to dst keeping its mode and mtime; never overwrite an existing backup."""
    if dst.exists():
        raise FileExistsError(f"backup already exists: {dst}")
    shutil.copy2(src, dst)


def _write_atomic(path: Path, data: bytes) -> None:
    """Temp file in the same directory, then os.replace; the original mode is kept."""
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        if path.exists():
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _missing_hook_scripts(env: dict) -> list[Path]:
    """Absolute hook scripts the env's settings.json registers under <home>/.claude/hooks that do not exist."""
    hooks_dir = Path(env["home"]) / ".claude" / "hooks"
    try:
        settings = json.loads((Path(env["home"]) / ".claude" / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    found: list[Path] = []
    for _, hk in ep._hook_entries(settings):
        cmd = hk.get("command")
        try:
            tokens = shlex.split(cmd) if isinstance(cmd, str) else []
        except ValueError:
            continue
        for t in [ep._expand(t, env["home"]) for t in tokens + [str(a) for a in hk.get("args") or []]]:
            p = Path(t)
            if t.endswith(_SCRIPT_SUFFIXES) and p.is_absolute() and p.parent == hooks_dir and not p.exists() \
                    and p not in found:
                found.append(p)
    return found


def _restore_hook_scripts(env: dict, install: str) -> list[dict]:
    """tools/install_global_core.py (the existing installer) syncs agents, commands and the session-safety
    contract but does NOT copy hook scripts: it prints `cp` lines for the Owner. A registered hook whose script is
    missing is the measured hooks_broken, so this restores exactly those scripts from the install's own tracked
    hooks/ directory -- only into THIS env's <home>/.claude/hooks, only when absent (never an overwrite), and never
    into another env's tree (a7's hooks resolve into a5's, which this deploy leaves alone)."""
    out = []
    for target in _missing_hook_scripts(env):
        source = Path(install) / "hooks" / target.name
        if not source.is_file():
            out.append({"script": str(target), "restored": False, "why": "not in the install's hooks/ directory"})
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        except OSError as exc:
            out.append({"script": str(target), "restored": False, "why": exc.__class__.__name__})
            continue
        out.append({"script": str(target), "restored": True, "from": str(source)})
    return out


def apply_deploy(env_root, source_repo, commit=None, now=None) -> dict:
    """Deploy. Takes the env's sweep lock first (held -> code 6, nothing changed), then re-plans UNDER the lock and
    acts only on that fresh plan: the authorized state is re-read immediately before the effect, so an install that
    moved since any earlier look is judged as it is now. Any refusal is returned unchanged."""
    root, why = _guard(env_root)
    if why:
        return {**plan_deploy(env_root, source_repo, commit, now), "mode": "apply", "code": EXIT_GUARD, "steps": []}
    lock = _take_lock(root / "sweep.lock")
    if lock is None:
        return {"mode": "apply", "env_root": str(root), "source_repo": str(source_repo), "code": EXIT_LOCK,
                "refusal": {"code": EXIT_LOCK, "why": f"{root / 'sweep.lock'} is held by another process "
                            "(a sweep is running); nothing was changed"}, "steps": [], "rollback": [],
                "target": None, "old_head": None}
    try:
        return _apply_locked(root, source_repo, commit, now)
    finally:
        lock.close()


def _apply_locked(root: Path, source_repo, commit, now) -> dict:
    plan = plan_deploy(root, source_repo, commit, now)            # fresh, under the lock
    res = {**plan, "mode": "apply", "steps": [], "code": EXIT_OK, "old_head": plan.get("env_head")}
    if plan["refusal"]:
        res["code"] = plan["refusal"]["code"]
        return res
    env = ep.env_from_root(root)
    install, ts, old, target = env["install"], plan["ts"], plan["env_head"], plan["target"]
    igit, path = env.get("git") or _source_git(), env.get("path")
    env_sh, pp_head, src = root / "env.sh", root / "pp.head", Path(source_repo)
    res["rollback"] = list(plan["rollback"])

    def step(name: str, ok: bool, detail: str = "", fatal: bool = True) -> bool:
        """Record a step. A failed fatal step (git, env files) is code 8; a failed repair step is not fatal by
        itself -- the post-deploy preflight is the judge of whether the repair held (code 7)."""
        res["steps"].append({"step": name, "ok": ok, "detail": detail})
        if not ok and fatal:
            res["code"] = EXIT_GIT
        return ok

    def git_step(name, argv) -> bool:
        rc, out, err = _run(argv, install, path=path)
        return step(name, rc == 0, (err or out).strip()[:300])

    if not plan["already_at_target"]:
        if not git_step("fetch", [igit, "fetch", "--no-tags", str(src), target]):
            return _finish(root, res, env, now)
        if not git_step("backup-ref", [igit, "update-ref", plan["backups"]["ref"], old]):
            return _finish(root, res, env, now)
        if not git_step("checkout", [igit, "checkout", "-q", "--detach", target]):
            return _finish(root, res, env, now)
    else:
        step("fetch/checkout", True, "already at target")
    try:
        if pp_head.is_file() and pp_head.read_bytes() != target.encode():
            _backup_file(pp_head, root / f"pp.head.bak-{ts}")
            _write_atomic(pp_head, target.encode())
            step("pp.head", True, f"{old[:8]} -> {target[:8]}")
        if plan["plane_marker"] == "will add":
            original = env_sh.read_bytes()
            _backup_file(env_sh, root / f"env.sh.bak-{ts}")
            lead = b"" if original.endswith(b"\n") or not original else b"\n"
            _write_atomic(env_sh, original + lead + (PLANE_LINE + "\n").encode())
            step("env.sh", True, f"appended {PLANE_LINE}")
    except OSError as exc:
        step("env files", False, f"{exc.__class__.__name__}: {exc}")
        return _finish(root, res, env, now)
    env = ep.env_from_root(root)
    mid = ep.run(env, now, ["hooks"])
    if plan["hooks_repair"] or "hooks_broken" in mid["reasons"]:
        py = env.get("python") or sys.executable
        rc, out, err = _run([py, str(Path(install) / "tools" / "install_global_core.py"), "--settings",
                             str(Path(env["home"]) / ".claude" / "settings.json"), "--repo", install], install,
                            timeout=300, home=env["home"], path=path)
        tail = (out + err).strip().splitlines()[-20:]
        res["installer"] = {"rc": rc, "tail": tail}
        step("installer", rc == 0, f"install_global_core.py rc={rc}", fatal=False)
        restored = _restore_hook_scripts(env, install)
        res["hooks_restored"] = restored
        res["rollback"] += [f"rm {r['script']}" for r in restored if r["restored"]]
        res["rollback"].append(f"installer backups of anything it overwrote: {env['home']}/.claude/.pp-backups/")
        step("hook-scripts", all(r["restored"] for r in restored),
             f"{sum(r['restored'] for r in restored)}/{len(restored)} missing registered script(s) restored",
             fatal=False)
    return _finish(root, res, env, now)


def _finish(root: Path, res: dict, env: dict, now) -> dict:
    """Final preflight, the log line, the exit code. A git failure keeps code 8; otherwise 0 only when the
    post-deploy preflight no longer reports pp_install_stale or hooks_broken (else 7)."""
    env = ep.env_from_root(root)
    after = ep.run(env, now)
    res["after"] = {"verdict": after["verdict"], "reasons": after["reasons"], "unmeasured": after["unmeasured"],
                    "findings": after["findings"],
                    "checks": [{"check": c["check"], "state": c["state"], "why": c["why"]} for c in after["checks"]]}
    res["backup_ref"] = res["backups"].get("ref")
    still = [r for r in ("pp_install_stale", "hooks_broken") if r in after["reasons"]]
    if res["code"] == EXIT_OK and still:
        res["code"] = EXIT_STILL_STALE
    res["owner_actions"] = [OWNER_ACTIONS[r].format(env_sh=root / "env.sh") for r in after["reasons"]
                            if r in OWNER_ACTIONS]
    line = {"ts": res["ts"], "env_root": str(root), "old_head": res["old_head"], "target": res["target"],
            "backup_ref": res["backup_ref"], "code": res["code"],
            "before": {"verdict": res["before"]["verdict"], "reasons": res["before"]["reasons"]},
            "after": {"verdict": after["verdict"], "reasons": after["reasons"]},
            "steps": [{"step": s["step"], "ok": s["ok"]} for s in res["steps"]]}
    try:
        with open(root / "pp-deploy.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line) + "\n")
    except OSError as exc:
        res["steps"].append({"step": "log", "ok": False, "detail": exc.__class__.__name__})
    return res


def _render(plan: dict) -> str:
    lines = [f"env_root   {plan['env_root']}",
             f"install    head {str(plan.get('env_head'))[:8]} -> target {str(plan.get('target'))[:8]} "
             f"({plan['target_ref']}); ancestry: {plan.get('ancestry')}; modified tracked files: "
             f"{len(plan.get('modified') or [])}"]
    if plan.get("before"):
        b = plan["before"]
        lines.append(f"before     {b['verdict']} reasons={','.join(b['reasons']) or '-'}")
        lines += [f"           {c['state']:<12} {c['check']:<13} {c['why']}" for c in b["checks"]]
        lines.append(f"will do    hooks repair: {plan['hooks_repair']}; mission plane marker: {plan['plane_marker']}; "
                     f"already at target: {plan['already_at_target']}")
    if plan.get("rollback"):
        lines.append("rollback (Owner commands, if the deploy must be undone):")
        lines += [f"  {r}" for r in plan["rollback"]]
    ref = plan["refusal"]
    if ref:
        lines.append(f"REFUSED [{ref['code']}]: {ref['why']}")
    lines.append(f"DEPLOY=DRY-RUN target={plan.get('target') or '-'} refusal={ref['code'] if ref else 'none'}")
    return "\n".join(lines)


def _render_apply(res: dict) -> str:
    lines = [f"env_root   {res['env_root']}",
             f"install    {str(res.get('old_head'))[:8]} -> {str(res.get('target'))[:8]} ({res.get('target_ref')})"]
    lines += [f"step       {'ok  ' if s['ok'] else 'FAIL'} {s['step']}: {s['detail']}" for s in res.get("steps", [])]
    ref = res.get("refusal")
    if ref:
        lines.append(f"REFUSED [{ref['code']}]: {ref['why']}")
    if res.get("after"):
        a = res["after"]
        lines.append(f"after      {a['verdict']} reasons={','.join(a['reasons']) or '-'}")
    for act in res.get("owner_actions", []):
        lines.append(f"OWNER ACTION: {act}")
    if res.get("rollback"):
        lines.append("rollback (Owner commands, if the deploy must be undone):")
        lines += [f"  {r}" for r in res["rollback"]]
    state = "REFUSED" if ref else "APPLIED" if res["code"] == EXIT_OK else "INCOMPLETE"
    lines.append(f"DEPLOY={state} target={res.get('target') or '-'} code={res['code']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--env-root", required=True, help="an env root holding env.sh and home/ (e.g. ~/a7-env)")
    ap.add_argument("--source-repo", default=str(REPO_ROOT), help="the PP repository to deploy from (a local path)")
    ap.add_argument("--commit", help="any revision the source repo resolves (default: its HEAD); the resolved "
                    "sha is what the plan and the deploy log record")
    ap.add_argument("--apply", action="store_true", help="deploy (default: dry-run, which mutates nothing)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.apply:
        res = apply_deploy(args.env_root, args.source_repo, args.commit)
        print(json.dumps(res, indent=2, default=str) if args.json else _render_apply(res))
        return res["code"]
    plan = plan_deploy(args.env_root, args.source_repo, args.commit)
    print(json.dumps(plan, indent=2) if args.json else _render(plan))
    return plan["refusal"]["code"] if plan["refusal"] else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
