#!/usr/bin/env python3
"""The ISOLATED stage: a work epoch runs in its own git worktree, and what it
wrote is judged against the goal's declared write set BEFORE anything of it is
ingested. Contract: vault/specs/gdd-resident-driver.md, "ISOLATED stage".

    validate the write set + a clean base      (before anything is spent)
    git worktree add -b resident/<mission> <state>/worktrees/<mission> <base>
    provider runs with cwd = that worktree, and nothing else
    harvest: changed paths (committed AND uncommitted) vs the write set,
             ancestry of the worktree HEAD, and whether main moved because of it
    cleanup: `git worktree remove` without --force, only on a clean tree;
             the branch is always kept -- it IS the deliverable

THE RESIDENT NEVER MERGES, PUSHES OR REWRITES THE GOAL'S BRANCH. The work
reaches the goal tree only when a person merges it. After green gates in the
worktree the resident FAST-FORWARDS one dedicated ref, `factory/integration`
(`integrate`), by compare-and-swap, and touches no other ref.

Everything here reads git through one helper that keeps stderr, because a
refusal must carry git's own words, not a guess about them.
"""
from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

from .. import git_state as gs

BRANCH_PREFIX = "resident/"

# Pre-spend refusals (no epoch, no mission, nothing dispatched).
EMPTY_WRITE_SET = "EMPTY_WRITE_SET"
WRITE_SET_ESCAPES_REPO = "WRITE_SET_ESCAPES_REPO"
NO_CLEAN_BASE = "NO_CLEAN_BASE"
WORK_AWAITING_MERGE = "WORK_AWAITING_MERGE"
# Isolation refusals (epoch begun, ended CANCELLED; mission REFUSED).
WORKTREE_PATH_EXISTS = "WORKTREE_PATH_EXISTS"
WORKTREE_INSIDE_REPO = "WORKTREE_INSIDE_REPO"
WORKTREE_ADD_FAILED = "WORKTREE_ADD_FAILED"
# Harvest refusal.
WRITE_SET_VIOLATION = "WRITE_SET_VIOLATION"
OUT_OF_SCOPE = "OUT_OF_SCOPE"
HISTORY_REWRITTEN = "HISTORY_REWRITTEN"
LEFT_BRANCH = "LEFT_BRANCH"
MAIN_BRANCH_MOVED = "MAIN_BRANCH_MOVED"
UNREADABLE = "UNREADABLE"

# Integration (Owner decision "option 1"): fast-forward ONE dedicated branch.
INTEGRATION_BRANCH = "factory/integration"
INTEGRATION_REF = f"refs/heads/{INTEGRATION_BRANCH}"
INTEGRATED, ALREADY_INTEGRATED, INTEGRATION_REFUSED = (
    "INTEGRATED", "ALREADY_INTEGRATED", "INTEGRATION_REFUSED")
NOTHING_TO_INTEGRATE = "NOTHING_TO_INTEGRATE"
INTEGRATION_WORKTREE_DIRTY = "INTEGRATION_WORKTREE_DIRTY"
NO_GATES = "NO_GATES"
GATES_RED = "GATES_RED"
INTEGRATION_HEAD_MOVED = "INTEGRATION_HEAD_MOVED"
INTEGRATION_CHECKED_OUT = "INTEGRATION_CHECKED_OUT"
INTEGRATION_NOT_FAST_FORWARD = "INTEGRATION_NOT_FAST_FORWARD"
INTEGRATION_RACE_LOST = "INTEGRATION_RACE_LOST"

# Worktree inspection verdicts (census).
ABSENT, PRISTINE, DIRTY, ADVANCED = "ABSENT", "PRISTINE", "DIRTY", "ADVANCED"


class IsolationRefused(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


def git(root: Path, *args: str, timeout: float = 120.0) -> tuple[int, str, str]:
    """(rc, stdout, stderr). rc 127 when no git executable could be started."""
    for exe in gs.GIT_CANDIDATES:
        try:
            p = subprocess.run([exe, "-C", str(root), *args], capture_output=True, text=True,
                               timeout=timeout, stdin=subprocess.DEVNULL,
                               encoding="utf-8", errors="replace")
        except (OSError, subprocess.SubprocessError):
            continue
        return p.returncode, (p.stdout or ""), (p.stderr or "").strip()
    return 127, "", "no git executable could be started"


# --- the write set ---------------------------------------------------------------------

def _norm(p: str) -> str:
    s = str(p).replace("\\", "/").strip()
    while s.startswith("./"):
        s = s[2:]
    s = s.rstrip("/")
    return s or "."


def validate_write_set(root: Path, paths) -> tuple[str, str]:
    """('', '') when admissible, else (reason, detail). The write set is the
    goal's declared scope.paths AS DECLARED -- never the gate path's '.' default."""
    if not isinstance(paths, (list, tuple)) or not [p for p in paths if str(p).strip()]:
        return EMPTY_WRITE_SET, "the goal declares no scope.paths; a work epoch needs a write set"
    base = Path(root).resolve()
    bad = []
    for raw in paths:
        s = str(raw).strip()
        n = _norm(s)
        parts = PurePosixPath(n).parts
        if (not s or Path(s).is_absolute() or s.startswith(("/", "\\")) or ":" in s
                or ".." in parts or ".git" in parts):
            bad.append(s)
            continue
        try:
            (base / n).resolve().relative_to(base)
        except ValueError:
            bad.append(s)
    if bad:
        return WRITE_SET_ESCAPES_REPO, f"not inside the repo: {bad}"
    return "", ""


def in_write_set(path: str, write_set) -> bool:
    p = _norm(path)
    for d in write_set or []:
        dn = _norm(d)
        if dn == "." or p == dn or p.startswith(dn + "/"):
            return True
    return False


def clean_base(root: Path, paths) -> tuple[str, str, str]:
    """(base_commit, '', '') or ('', NO_CLEAN_BASE, detail)."""
    head = gs.head(root)
    if not head:
        return "", NO_CLEAN_BASE, f"{root} has no HEAD commit"
    tid = gs.tree_id(root, list(paths))
    if not tid.startswith("git:"):
        return "", NO_CLEAN_BASE, (f"the goal scope is not committed ({tid}); the state the "
                                   "engine judged is not a commit a worktree can start from")
    return head, "", ""


def root_ref(root: Path) -> str:
    rc, out, _ = git(root, "symbolic-ref", "-q", "HEAD")
    return out.strip() if rc == 0 else ""


def is_ancestor(root: Path, a: str, b: str) -> bool:
    if not a or not b:
        return False
    rc, _, _ = git(root, "merge-base", "--is-ancestor", a, b)
    return rc == 0


# --- isolation ---------------------------------------------------------------------------

def branch_for(mission_id: str) -> str:
    return f"{BRANCH_PREFIX}{mission_id}"


def create(root: Path, path: Path, branch: str, base: str) -> Path:
    """Create the worktree. Raises IsolationRefused; never reuses a path."""
    root, path = Path(root), Path(path)
    try:
        path.resolve().relative_to(root.resolve())
        raise IsolationRefused(WORKTREE_INSIDE_REPO,
                               f"{path} lies inside the goal repo {root}; move the resident "
                               "state dir out of it")
    except ValueError:
        pass
    if path.exists():
        raise IsolationRefused(WORKTREE_PATH_EXISTS, f"{path} already exists; never reused")
    path.parent.mkdir(parents=True, exist_ok=True)
    rc, out, err = git(root, "worktree", "add", "-b", branch, str(path), base)
    if rc != 0:
        raise IsolationRefused(WORKTREE_ADD_FAILED, f"git worktree add rc={rc}: {err or out}"[:400])
    if gs.head(path) != base:
        raise IsolationRefused(WORKTREE_ADD_FAILED,
                               f"{path} was created but its HEAD is {gs.head(path)!r}, not {base}")
    return path


# --- what a worktree changed ----------------------------------------------------------

def _split_z(out: str) -> list:
    return [x for x in out.split("\0") if x]


def committed_paths(wt: Path, base: str) -> list:
    rc, out, err = git(wt, "diff", "--name-only", "-z", "--no-renames", base, "HEAD")
    if rc != 0:
        raise OSError(f"git diff {base}..HEAD failed: {err}")
    return sorted(set(_split_z(out)))


def uncommitted_paths(wt: Path) -> list:
    rc, out, err = git(wt, "status", "--porcelain=v1", "-z", "--no-renames",
                       "--untracked-files=all")
    if rc != 0:
        raise OSError(f"git status failed: {err}")
    return sorted({e[3:] for e in _split_z(out) if len(e) > 3})


def inspect(wt: Path, base: str) -> tuple[str, str]:
    """ABSENT | PRISTINE | DIRTY | ADVANCED, with the evidence."""
    wt = Path(wt)
    if not wt.exists():
        return ABSENT, f"{wt} does not exist"
    head = gs.head(wt)
    if not head:
        return DIRTY, f"{wt} exists and is not a readable git worktree"
    try:
        dirty = uncommitted_paths(wt)
    except OSError as exc:
        return DIRTY, f"status unreadable: {exc}"
    if dirty:
        return DIRTY, f"uncommitted: {dirty[:10]}"
    if head != base:
        return ADVANCED, f"HEAD {head[:12]} != base {base[:12]}"
    return PRISTINE, "HEAD == base and nothing uncommitted"


def check_harvest(mission: dict) -> dict:
    """The write-set verdict for a returned work mission. Never raises: a git
    failure is itself a refusal (UNREADABLE), because an unjudged harvest must
    not be ingested."""
    wt = Path(mission["worktree"])
    base = mission["base_commit"]
    ws = mission.get("write_set") or []
    root = Path(mission["root"])
    ev = {"worktree": str(wt), "base": base, "write_set": list(ws)}
    reasons: list = []
    offending: list = []
    try:
        head = gs.head(wt)
        ev["head"] = head
        if not head:
            raise OSError(f"{wt} has no readable HEAD")
        if not is_ancestor(wt, base, head):
            reasons.append(f"{HISTORY_REWRITTEN}: HEAD {head[:12]} does not descend from base "
                           f"{base[:12]}")
        cur_ref = root_ref(wt)
        if cur_ref != f"refs/heads/{mission['branch']}":
            reasons.append(f"{LEFT_BRANCH}: worktree HEAD is {cur_ref or 'detached'}, not "
                           f"refs/heads/{mission['branch']}")
        committed = committed_paths(wt, base) if not reasons else []
        uncommitted = uncommitted_paths(wt)
        ev["committed"], ev["uncommitted"] = committed, uncommitted
        for p in sorted(set(committed) | set(uncommitted)):
            if not in_write_set(p, ws):
                offending.append(p)
        if offending:
            reasons.append(f"{OUT_OF_SCOPE}: {offending}")
        # Main moved BECAUSE of this epoch? Worktrees share refs with the root.
        before = mission.get("root_head_at_isolation", "")
        now_root = gs.head(root)
        ev["root_head_before"], ev["root_head_after"] = before, now_root
        if before and now_root != before:
            if not is_ancestor(root, before, now_root):
                reasons.append(f"{MAIN_BRANCH_MOVED}: goal root HEAD moved non-fast-forward "
                               f"{before[:12]} -> {now_root[:12]}")
            else:
                rc, out, _ = git(wt, "log", "--format=%H", f"{base}..{head}")
                ours = [c for c in out.split() if c] if rc == 0 else []
                leaked = [c for c in ours if is_ancestor(root, c, now_root)]
                if leaked:
                    reasons.append(f"{MAIN_BRANCH_MOVED}: goal root HEAD now reaches this "
                                   f"epoch's commits {[c[:12] for c in leaked]}")
    except OSError as exc:
        reasons.append(f"{UNREADABLE}: {exc}")
    ev["offending"] = offending
    ev["reasons"] = reasons
    return {"ok": not reasons, "reason": "" if not reasons else WRITE_SET_VIOLATION,
            "evidence": ev}


def worktree_list_has_branch(root: Path, ref: str) -> tuple[bool, str]:
    """(checked_out, error). `git worktree list --porcelain` names the branch
    each worktree -- the main one included -- has checked out."""
    rc, out, err = git(root, "worktree", "list", "--porcelain")
    if rc != 0:
        return False, f"git worktree list rc={rc}: {err}"
    return any(line.strip() == f"branch {ref}" for line in out.splitlines()), ""


def read_ref(root: Path, ref: str) -> tuple[str, str]:
    """(commit, error). ('', '') when the ref does not exist."""
    rc, out, err = git(root, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}")
    if rc == 0:
        return out.strip(), ""
    rc2, out2, _ = git(root, "show-ref", "--verify", "-q", ref)
    if rc2 != 0:
        return "", ""                    # absent
    return "", f"{ref} exists but does not resolve to a commit: {err}"


def integrate(root: Path, job_commit: str, base: str) -> dict:
    """Fast-forward refs/heads/factory/integration to `job_commit`. Touches that
    one ref and nothing else; never merges, rebases, forces or pushes.

    Returns {ok, state, reason, detail, ref_before, ref_after, created}."""
    out = {"ok": False, "state": INTEGRATION_REFUSED, "reason": "", "detail": "",
           "ref": INTEGRATION_REF, "ref_before": "", "ref_after": "", "created": False}

    def refuse(reason: str, detail: str) -> dict:
        out.update(reason=reason, detail=detail[:400])
        out["ref_after"] = read_ref(root, INTEGRATION_REF)[0]
        return out

    if not job_commit or not base:
        return refuse(UNREADABLE, f"job commit {job_commit!r} / base {base!r} missing")
    busy, err = worktree_list_has_branch(root, INTEGRATION_REF)
    if err:
        return refuse(UNREADABLE, err)
    if busy:
        return refuse(INTEGRATION_CHECKED_OUT,
                      f"{INTEGRATION_BRANCH} is checked out in a worktree; updating it there "
                      "would desynchronise that worktree -- a person switches it away first")
    cur, err = read_ref(root, INTEGRATION_REF)
    if err:
        return refuse(UNREADABLE, err)
    out["ref_before"] = cur
    if not cur:
        rc, o, e = git(root, "update-ref", "-m", f"resident: create at base {base[:12]}",
                       INTEGRATION_REF, base, "")
        if rc != 0:
            return refuse(INTEGRATION_RACE_LOST,
                          f"creating {INTEGRATION_REF} at {base[:12]} refused: {e or o}")
        out["created"] = True
        cur = base
    if cur == job_commit:
        out.update(ok=True, state=ALREADY_INTEGRATED, ref_after=cur,
                   detail=f"{INTEGRATION_BRANCH} already at {cur[:12]}")
        return out
    if not is_ancestor(root, cur, job_commit):
        return refuse(INTEGRATION_NOT_FAST_FORWARD,
                      f"{INTEGRATION_BRANCH} tip {cur[:12]} is not an ancestor of the job commit "
                      f"{job_commit[:12]}; never merged, rebased or forced -- a person decides")
    rc, o, e = git(root, "update-ref", "-m", f"resident: fast-forward to {job_commit[:12]}",
                   INTEGRATION_REF, job_commit, cur)
    if rc != 0:
        return refuse(INTEGRATION_RACE_LOST,
                      f"{INTEGRATION_REF} moved since it was read at {cur[:12]}: {e or o}")
    after = read_ref(root, INTEGRATION_REF)[0]
    if after != job_commit:
        return refuse(INTEGRATION_RACE_LOST,
                      f"{INTEGRATION_REF} reads {after[:12]} after the update, not {job_commit[:12]}")
    out.update(ok=True, state=INTEGRATED, ref_after=after,
               detail=f"{INTEGRATION_BRANCH} {cur[:12]} -> {after[:12]} (fast-forward)")
    return out


def integration_carries(root: Path, commit: str) -> bool:
    """Does factory/integration currently contain `commit`?"""
    tip = read_ref(root, INTEGRATION_REF)[0]
    return bool(tip) and is_ancestor(root, commit, tip)


def awaiting_merge(root: Path, delivered_head: str, base: str) -> bool:
    """A delivered branch that carries commits not yet in the goal root's HEAD."""
    if not delivered_head or delivered_head == base:
        return False
    return not is_ancestor(root, delivered_head, gs.head(root))


# --- cleanup ----------------------------------------------------------------------------

def remove_if_clean(root: Path, wt: Path, branch: str) -> dict:
    """Remove a worktree only when it is OURS (checked out on its mission
    branch) and holds nothing uncommitted. Never --force: git re-checks
    cleanliness itself at the moment of removal. The branch is kept."""
    wt = Path(wt)
    if not wt.exists():
        rc, _, err = git(root, "worktree", "prune")
        return {"removed": False, "kept": False, "detail": f"already absent (prune rc={rc})"}
    ref = root_ref(wt)
    if not branch or ref != f"refs/heads/{branch}":
        return {"removed": False, "kept": True,
                "detail": f"not provably ours: HEAD is {ref or 'unreadable/detached'}, "
                          f"expected refs/heads/{branch}"}
    try:
        dirty = uncommitted_paths(wt)
    except OSError as exc:
        return {"removed": False, "kept": True, "detail": f"status unreadable: {exc}"}
    if dirty:
        return {"removed": False, "kept": True,
                "detail": f"uncommitted work kept for a person: {dirty[:20]}"}
    rc, out, err = git(root, "worktree", "remove", str(wt))
    if rc != 0:
        return {"removed": False, "kept": True, "detail": f"git refused: {err or out}"[:300]}
    return {"removed": True, "kept": False, "detail": "clean; branch kept"}
