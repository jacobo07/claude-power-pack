#!/usr/bin/env python3
"""verify_global_mirrors.py - BL-0064 enforcement (dynamic, branch-flip-immune).

SHA-256 compares the version-controlled PP mirrors against the global
~/.claude/{commands,agents,knowledge_vault}/ canonical files.

Phantom-drift root cause (sealed 2026-05-16): the prior implementation read
the PP side from the *working tree*, which concurrent Cursor panes flip
between branches unpredictably -> false DRIFT, Exit 5. This rewrite NEVER
reads the working tree for the PP side. It reads the committed blob via
`git -C <repo> show <ref>:<relpath>` against a deterministic named ref, so
the result is invariant to whatever branch a concurrent pane checked out.

Resolution chains
-----------------
Repo path (Q4a):  --repo-path  ->  $POWERPACK_REPO  ->
  `git rev-parse --show-toplevel` from this script's dir  ->
  hardcoded host fallback (C:/Users/User/.claude/skills/claude-power-pack).

Canonical ref (Q1a intent honored, false literal corrected):
  --ref  ->  $POWERPACK_MIRROR_REF  ->  the sealing branch
  (feat/rtk-compressor-fusion)  ->  main  ->  the first refname-sorted
  local head that actually tracks the path. The chosen ref is reported
  per-pair. kdos/v1.2-sync is an ancestor that tracks none of these files,
  so it is intentionally NOT a default (audit gap #1).

Autocrlf parity (Q3a): only `knowledge_vault/**` carries `-text` in
.gitattributes; the commands/ and agents/ pairs do NOT. Under
core.autocrlf=true the committed blob is LF while the global filesystem
copy is CRLF. Both sides are therefore LF-normalized before hashing -
load-bearing for 3 of 4 pairs, not mere defense-in-depth.

Exit codes: 0 = all pairs OK (or legitimately SKIPped). 5 = real DRIFT or
a genuine MISSING (global file absent, or PP path tracked on no ref).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import PurePosixPath

HARDCODED_REPO = r"C:\Users\User\.claude\skills\claude-power-pack"

# Sealing branch: the lineage that actually owns these files (audit-verified
# 2026-05-16). Used only as a fallback after --ref / env. Overridable so a
# future rename does not strand the tool.
SEALING_REF = "main"  # post-merge 2026-05-23: feat/rtk-compressor-fusion
                       # was merged into main; main is now the production
                       # branch per the Production Branch Standard.

PAIRS = [
    (r"C:\Users\User\.claude\commands\ultra.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\commands\ultra.md"),
    (r"C:\Users\User\.claude\agents\oneshot-architect-auditor.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\agents"
     r"\oneshot-architect-auditor.md"),
    (r"C:\Users\User\.claude\commands\cpp-resume-sovereign.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\commands"
     r"\resume-sovereign.md"),
    (r"C:\Users\User\.claude\knowledge_vault\core\apex-completion-standard.md",
     r"C:\Users\User\.claude\skills\claude-power-pack\knowledge_vault"
     r"\core\apex-completion-standard.md"),
    # Globalization 2026-05-19: runtime hooks the installer ships to a new
    # user's ~/.claude/hooks/. PP repo IS the canonical; the verifier asserts
    # the live host has not drifted from the shipped canonical (or vice versa).
    (r"C:\Users\User\.claude\hooks\learning-sentinel.js",
     r"C:\Users\User\.claude\skills\claude-power-pack\hooks"
     r"\learning-sentinel.js"),
    (r"C:\Users\User\.claude\hooks\hook-dispatcher.js",
     r"C:\Users\User\.claude\skills\claude-power-pack\hooks"
     r"\hook-dispatcher.js"),
    (r"C:\Users\User\.claude\hooks\lazarus-livesnap.js",
     r"C:\Users\User\.claude\skills\claude-power-pack\hooks"
     r"\lazarus-livesnap.js"),
    # NOTE 2026-05-23: resume-hide-live.js (BL-0013 .jsonl-rename
    # cloaking) was decommissioned by mark-live-session.js. Removed
    # from PAIRS so this verifier stops asking for a file that no
    # longer exists on either side.
    (r"C:\Users\User\.claude\hooks\zero-issue-gate.js",
     r"C:\Users\User\.claude\skills\claude-power-pack\hooks"
     r"\zero-issue-gate.js"),
    (r"C:\Users\User\.claude\hooks\jobs-woz-gatekeeper.js",
     r"C:\Users\User\.claude\skills\claude-power-pack\hooks"
     r"\jobs-woz-gatekeeper.js"),
]


def _norm_sha(data: bytes) -> str:
    """LF-normalize then SHA-256. Neutralizes core.autocrlf=true drift."""
    lf = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(lf).hexdigest()


def _git_exe() -> str:
    """Resolve git executable. M8 fix: on Windows under PowerShell
    -NonInteractive PATH may omit Git's cmd dir; bare ['git', ...] in
    subprocess raises FileNotFoundError which this script catches as
    OSError and silently returns 'untracked' -- a false-positive that
    masks real mirror state. Falls back to known install paths per
    Windows Bash Bridge Reliability doctrine."""
    import shutil
    p = shutil.which("git")
    if p:
        return p
    if os.name == "nt":
        for candidate in (
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
        ):
            if os.path.isfile(candidate):
                return candidate
    raise FileNotFoundError(
        "git executable not found on PATH or known Windows locations")


def resolve_repo(cli_repo: str | None) -> str:
    if cli_repo and os.path.isdir(cli_repo):
        return os.path.abspath(cli_repo)
    env_repo = os.environ.get("POWERPACK_REPO")
    if env_repo and os.path.isdir(env_repo):
        return os.path.abspath(env_repo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        top = subprocess.run(
            [_git_exe(), "-C", script_dir, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=15,
        )
        if top.returncode == 0:
            cand = top.stdout.strip()
            if cand and os.path.isdir(cand):
                return os.path.abspath(cand)
    except (OSError, subprocess.SubprocessError):
        pass
    return HARDCODED_REPO


def repo_rel_posix(pp_abspath: str, repo_root: str) -> str:
    """Absolute Windows PP path -> repo-root-relative POSIX git pathspec."""
    rel = os.path.relpath(pp_abspath, repo_root)
    return PurePosixPath(*rel.replace("\\", "/").split("/")).as_posix()


def _ref_tracks(repo: str, ref: str, rel_posix: str) -> bool:
    try:
        r = subprocess.run(
            [_git_exe(), "-C", repo, "cat-file", "-e", f"{ref}:{rel_posix}"],
            capture_output=True, timeout=15,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _sorted_heads(repo: str) -> list[str]:
    try:
        r = subprocess.run(
            [_git_exe(), "-C", repo, "for-each-ref", "--sort=refname",
             "--format=%(refname:short)", "refs/heads"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0:
            return [x for x in r.stdout.splitlines() if x.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    return []


def resolve_ref(repo: str, rel_posix: str, cli_ref: str | None) -> str | None:
    """Deterministic, working-tree-independent. None => tracked on no ref."""
    candidates: list[str] = []
    if cli_ref:
        candidates.append(cli_ref)
    env_ref = os.environ.get("POWERPACK_MIRROR_REF")
    if env_ref:
        candidates.append(env_ref)
    candidates.append(SEALING_REF)
    candidates.append("main")
    candidates.extend(_sorted_heads(repo))
    seen: set[str] = set()
    for ref in candidates:
        if ref in seen:
            continue
        seen.add(ref)
        if _ref_tracks(repo, ref, rel_posix):
            return ref
    return None


def git_show_blob(repo: str, ref: str, rel_posix: str):
    """Return (bytes, None) or (None, reason). returncode-checked (gap #2)."""
    try:
        r = subprocess.run(
            [_git_exe(), "-C", repo, "show", f"{ref}:{rel_posix}"],
            capture_output=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"git-show-error:{e}"
    if r.returncode != 0:
        return None, f"git-show-rc{r.returncode}"
    if not r.stdout:
        return None, "git-show-empty"
    return r.stdout, None


def _read_global(path: str):
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def check_pairs(repo: str, cli_ref: str | None) -> int:
    fails: list[str] = []
    for global_path, pp_abspath in PAIRS:
        base = os.path.basename(global_path)
        rel_posix = repo_rel_posix(pp_abspath, repo)

        g_bytes = _read_global(global_path)
        if g_bytes is None:
            print(f"  [MISSING] {base}: global file absent ({global_path})")
            fails.append(f"global-absent:{base}")
            continue

        ref = resolve_ref(repo, rel_posix, cli_ref)
        if ref is None:
            print(f"  [MISSING] {base}: PP path tracked on no ref "
                  f"({rel_posix})")
            fails.append(f"pp-untracked:{base}")
            continue

        blob, reason = git_show_blob(repo, ref, rel_posix)
        if blob is None:
            print(f"  [MISSING] {base}: {reason} @ {ref}:{rel_posix}")
            fails.append(f"{reason}:{base}")
            continue

        gh, ph = _norm_sha(g_bytes), _norm_sha(blob)
        if gh == ph:
            print(f"  [OK] {base}: global={gh[:12]} "
                  f"pp={ph[:12]} (ref={ref})")
        else:
            print(f"  [DRIFT] {base}: global={gh[:12]} "
                  f"pp={ph[:12]} (ref={ref})")
            fails.append(f"drift:{base}")

    if fails:
        print("VERIFY_GLOBAL_MIRRORS FAIL:", " | ".join(fails))
        return 5
    print("VERIFY_GLOBAL_MIRRORS OK")
    return 0


def self_test(repo: str, cli_ref: str | None) -> int:
    """Cryptographic invariance across refs. Absent-on-a-ref = SKIP (gap #9),
    never a pass and never a drift. Fails only if two PRESENT refs disagree.
    """
    print("--- self-test: cross-ref normalized-SHA invariance ---")
    primary = []
    if cli_ref:
        primary.append(cli_ref)
    primary += [SEALING_REF, "main", "HEAD"]
    seen: set[str] = set()
    refs = []
    for r in primary:
        if r not in seen:
            seen.add(r)
            refs.append(r)

    failures: list[str] = []
    for _global_path, pp_abspath in PAIRS:
        base = os.path.basename(pp_abspath)
        rel_posix = repo_rel_posix(pp_abspath, repo)
        digests: dict[str, str] = {}
        for ref in refs:
            if not _ref_tracks(repo, ref, rel_posix):
                print(f"  [SKIP] {base} @ {ref}: not tracked on this ref")
                continue
            blob, reason = git_show_blob(repo, ref, rel_posix)
            if blob is None:
                print(f"  [SKIP] {base} @ {ref}: {reason}")
                continue
            digests[ref] = _norm_sha(blob)
        present = set(digests.values())
        if len(present) <= 1:
            shown = next(iter(present))[:12] if present else "n/a"
            print(f"  [INVARIANT] {base}: {len(digests)} present ref(s) "
                  f"agree sha={shown}")
        else:
            print(f"  [VIOLATION] {base}: present refs disagree {digests}")
            failures.append(base)

    if failures:
        print("SELF_TEST FAIL:", " | ".join(failures))
        return 5
    print("SELF_TEST OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="BL-0064 dynamic mirror verifier")
    ap.add_argument("--repo-path", default=None,
                    help="explicit PP repo root (highest precedence)")
    ap.add_argument("--ref", default=None,
                    help="explicit canonical ref (highest precedence)")
    ap.add_argument("--self-test", action="store_true",
                    help="assert cross-ref normalized-SHA invariance")
    a = ap.parse_args()
    repo = resolve_repo(a.repo_path)
    if not os.path.isdir(os.path.join(repo, ".git")) and not os.path.isfile(
            os.path.join(repo, ".git")):
        # Resolved path is not a git repo; still emit a deterministic failure
        # rather than a stack trace.
        print(f"VERIFY_GLOBAL_MIRRORS FAIL: not a git repo: {repo}")
        return 5
    print(f"repo={repo}")
    if a.self_test:
        return self_test(repo, a.ref)
    return check_pairs(repo, a.ref)


if __name__ == "__main__":
    raise SystemExit(main())
