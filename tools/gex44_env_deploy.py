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
    rc, st, _ = _run([igit, "--no-optional-locks", "status", "--porcelain", "--untracked-files=no"], install,
                     path=env.get("path"))
    if rc != 0:
        return _refuse(plan, EXIT_GUARD, "git could not read the install's status")
    plan["modified"] = [r[3:] for r in st.splitlines()]
    ref = commit or "HEAD"
    src = Path(source_repo)
    if ref.startswith("-") or not src.is_dir():
        return _refuse(plan, EXIT_GUARD, f"bad source repo or revision: {source_repo} {ref}")
    rc, tgt, _ = _run([sgit, "rev-parse", "--verify", f"{ref}^{{commit}}"], src)
    if rc != 0 or not re.fullmatch(r"[0-9a-f]{40}", tgt.strip()):
        return _refuse(plan, EXIT_GUARD, f"the source repo {src} does not resolve {ref!r} to a commit")
    plan["target"] = tgt.strip()
    rc, _, _ = _run([sgit, "merge-base", "--is-ancestor", plan["env_head"], plan["target"]], src)
    plan["ancestry"] = ("ancestor" if rc == 0 else "env ahead or diverged" if rc == 1
                        else "env head unknown to the source")
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--env-root", required=True, help="an env root holding env.sh and home/ (e.g. ~/a7-env)")
    ap.add_argument("--source-repo", default=str(REPO_ROOT), help="the PP repository to deploy from (a local path)")
    ap.add_argument("--commit", help="any revision the source repo resolves (default: its HEAD); the resolved "
                    "sha is what the plan and the deploy log record")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    plan = plan_deploy(args.env_root, args.source_repo, args.commit)
    print(json.dumps(plan, indent=2) if args.json else _render(plan))
    return plan["refusal"]["code"] if plan["refusal"] else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
