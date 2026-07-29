#!/usr/bin/env python3
"""verify_global_mirrors.py - BL-0064 enforcement (dynamic, branch-flip-immune).

SHA-256 compares the version-controlled PP mirrors against the global
~/.claude/{hooks,commands,agents,knowledge_vault}/ canonical files.

Pair source (rewritten 2026-07-29)
----------------------------------
Pairs are DISCOVERED by `modules.mirror_discovery`, not listed here. The
previous implementation carried nine literal tuples and the Mirror Parity Law
told the next author to append a tenth by hand; measured consequence on this
host: 5 of 10 name-matched hooks tracked, 2 of 13 commands, and
`knowledge_vault/core/skill-completion-standard.md` never enrolled at all.
A hand-enrolled denominator cannot fail you if it never enrolled the file
(`PR-COVERAGE-BY-CONSTRUCTION-001`). Only two things remain declared, because
neither is observable: name aliases, and prefixes other tools install into the
shared live tree.

Files present on one side only are reported as INVENTORY, never as drift --
the repo deliberately ships commands that are not installed and the live tree
carries knowledge the repo does not mirror. `--strict` promotes them to
failures for a caller that wants full symmetry.

Phantom-drift root cause (sealed 2026-05-16): the prior implementation read
the PP side from the *working tree*, which concurrent Cursor panes flip
between branches unpredictably -> false DRIFT, Exit 5. This NEVER reads the
working tree for the PP side. It reads the committed blob against a
deterministic named ref, so the result is invariant to whatever branch a
concurrent pane checked out.

Blobs are fetched with a single `git cat-file --batch` per ref rather than one
`git show` per pair: discovery raised the pair count from 9 to 27 and the
mirror-parity row in `tools/verify_spp.py` runs under a 15 s budget.

Resolution chains
-----------------
Repo path (Q4a):  --repo-path  ->  $POWERPACK_REPO  ->
  `git rev-parse --show-toplevel` from this script's dir  ->
  hardcoded host fallback (C:/Users/User/.claude/skills/claude-power-pack).

Canonical ref (Q1a intent honored, false literal corrected):
  --ref  ->  $POWERPACK_MIRROR_REF  ->  the sealing branch  ->  main  ->
  the first refname-sorted local head that actually tracks the path.

Autocrlf parity (Q3a): only `knowledge_vault/**` carries `-text` in
.gitattributes; the commands/ and agents/ pairs do NOT. Under
core.autocrlf=true the committed blob is LF while the global filesystem
copy is CRLF. Both sides are therefore LF-normalized before hashing -
load-bearing for most pairs, not mere defense-in-depth.

Exit codes: 0 = all pairs OK (or legitimately SKIPped). 5 = real DRIFT or
a genuine MISSING (global file absent, or PP path tracked on no ref).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

HARDCODED_REPO = r"C:\Users\User\.claude\skills\claude-power-pack"

# Sealing branch: the lineage that actually owns these files (audit-verified
# 2026-05-16). Used only as a fallback after --ref / env. Overridable so a
# future rename does not strand the tool.
SEALING_REF = "main"  # post-merge 2026-05-23: feat/rtk-compressor-fusion
                       # was merged into main; main is now the production
                       # branch per the Production Branch Standard.

GIT_TIMEOUT = 15
BATCH_TIMEOUT = 60

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

from modules.mirror_discovery import discover  # noqa: E402


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
            capture_output=True, text=True, timeout=GIT_TIMEOUT,
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


def _sorted_heads(repo: str) -> list[str]:
    try:
        r = subprocess.run(
            [_git_exe(), "-C", repo, "for-each-ref", "--sort=refname",
             "--format=%(refname:short)", "refs/heads"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT,
        )
        if r.returncode == 0:
            return [x for x in r.stdout.splitlines() if x.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    return []


def ref_candidates(repo: str, cli_ref: str | None) -> list[str]:
    out: list[str] = []
    for ref in ([cli_ref] if cli_ref else []) + \
            ([os.environ.get("POWERPACK_MIRROR_REF")]
             if os.environ.get("POWERPACK_MIRROR_REF") else []) + \
            [SEALING_REF, "main"] + _sorted_heads(repo):
        if ref and ref not in out:
            out.append(ref)
    return out


def tracked_at(repo: str, ref: str) -> set:
    """Every path tracked at `ref`, in one subprocess. Replaces a per-path
    `cat-file -e`, which cost one process per pair per candidate ref."""
    try:
        r = subprocess.run(
            [_git_exe(), "-C", repo, "ls-tree", "-r", "--name-only", ref],
            capture_output=True, text=True, timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if r.returncode != 0:
        return set()
    return {line.strip() for line in r.stdout.splitlines() if line.strip()}


def batch_blobs(repo: str, ref: str, rels: list) -> dict:
    """{rel: (bytes|None, reason|None)} for all rels at `ref`, one process."""
    if not rels:
        return {}
    payload = "".join(f"{ref}:{r}\n" for r in rels).encode("utf-8")
    try:
        proc = subprocess.run(
            [_git_exe(), "-C", repo, "cat-file", "--batch"],
            input=payload, capture_output=True, timeout=BATCH_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return {r: (None, f"git-batch-error:{e}") for r in rels}
    if proc.returncode != 0:
        return {r: (None, f"git-batch-rc{proc.returncode}") for r in rels}

    out, pos, result = proc.stdout, 0, {}
    for rel in rels:
        nl = out.find(b"\n", pos)
        if nl == -1:
            result[rel] = (None, "git-batch-truncated")
            continue
        header = out[pos:nl].split()
        pos = nl + 1
        if header and header[-1] in (b"missing", b"ambiguous"):
            result[rel] = (None, f"git-batch-{header[-1].decode()}")
            continue
        try:
            size = int(header[2])
        except (IndexError, ValueError):
            result[rel] = (None, "git-batch-badheader")
            continue
        blob = out[pos:pos + size]
        pos += size + 1  # object payload is followed by a newline
        result[rel] = (blob, None) if blob else (None, "git-batch-empty")
    return result


def _read_global(path: str):
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def _plan(repo: str, cli_ref: str | None, pairs: list):
    """Assign each pair a ref that tracks it. Returns (by_ref, untracked)."""
    candidates = ref_candidates(repo, cli_ref)
    rels = {str(p.repo): repo_rel_posix(str(p.repo), repo) for p in pairs}
    remaining = list(pairs)
    by_ref: dict = {}
    for ref in candidates:
        if not remaining:
            break
        tracked = tracked_at(repo, ref)
        if not tracked:
            continue
        hit = [p for p in remaining if rels[str(p.repo)] in tracked]
        if hit:
            by_ref.setdefault(ref, []).extend(hit)
            remaining = [p for p in remaining if p not in hit]
    return by_ref, remaining, rels


def check_pairs(repo: str, cli_ref: str | None, strict: bool = False,
                inventory: bool = False) -> int:
    d = discover(Path(repo))
    counts = d.domain_counts()
    print(f"discovered {len(d.pairs)} mirror pair(s) across "
          f"{len(counts)} domain(s); {d.unpaired_total} file(s) present on one "
          f"side only; {len(d.excluded)} foreign file(s) excluded")
    for dom, c in counts.items():
        print(f"  - {dom}: paired={c['PAIRED']} live-only={c['LIVE_ONLY']} "
              f"repo-only={c['REPO_ONLY']}")

    fails: list = []
    by_ref, untracked, rels = _plan(repo, cli_ref, d.pairs)

    for pair in untracked:
        print(f"  [MISSING] {pair.label}: PP path tracked on no ref "
              f"({rels[str(pair.repo)]})")
        fails.append(f"pp-untracked:{pair.live.name}")

    for ref, group in by_ref.items():
        blobs = batch_blobs(repo, ref, [rels[str(p.repo)] for p in group])
        for pair in group:
            rel = rels[str(pair.repo)]
            g_bytes = _read_global(str(pair.live))
            if g_bytes is None:
                print(f"  [MISSING] {pair.label}: global file absent "
                      f"({pair.live})")
                fails.append(f"global-absent:{pair.live.name}")
                continue
            blob, reason = blobs.get(rel, (None, "git-batch-absent"))
            if blob is None:
                print(f"  [MISSING] {pair.label}: {reason} @ {ref}:{rel}")
                fails.append(f"{reason}:{pair.live.name}")
                continue
            gh, ph = _norm_sha(g_bytes), _norm_sha(blob)
            if gh == ph:
                print(f"  [OK] {pair.label}: global={gh[:12]} "
                      f"pp={ph[:12]} (ref={ref})")
            else:
                print(f"  [DRIFT] {pair.label}: global={gh[:12]} "
                      f"pp={ph[:12]} (ref={ref})")
                fails.append(f"drift:{pair.live.name}")

    if inventory or strict:
        print("\n--- inventory: present on one side only ---")
        for domain, rel in d.live_only:
            print(f"  [LIVE-ONLY] {domain}/{rel}")
        for domain, rel in d.repo_only:
            print(f"  [REPO-ONLY] {domain}/{rel}")
    if strict:
        fails += [f"live-only:{domain}/{rel}" for domain, rel in d.live_only]
        fails += [f"repo-only:{domain}/{rel}" for domain, rel in d.repo_only]

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
    d = discover(Path(repo))
    refs: list[str] = []
    for r in ([cli_ref] if cli_ref else []) + [SEALING_REF, "main", "HEAD"]:
        if r and r not in refs:
            refs.append(r)

    rels = {str(p.repo): repo_rel_posix(str(p.repo), repo) for p in d.pairs}
    per_ref = {ref: batch_blobs(repo, ref, list(rels.values())) for ref in refs}

    failures: list = []
    for pair in d.pairs:
        rel = rels[str(pair.repo)]
        digests: dict = {}
        for ref in refs:
            blob, reason = per_ref[ref].get(rel, (None, "absent"))
            if blob is None:
                print(f"  [SKIP] {pair.repo.name} @ {ref}: {reason}")
                continue
            digests[ref] = _norm_sha(blob)
        present = set(digests.values())
        if len(present) <= 1:
            shown = next(iter(present))[:12] if present else "n/a"
            print(f"  [INVARIANT] {pair.repo.name}: {len(digests)} present "
                  f"ref(s) agree sha={shown}")
        else:
            print(f"  [VIOLATION] {pair.repo.name}: present refs disagree "
                  f"{digests}")
            failures.append(pair.repo.name)

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
    ap.add_argument("--inventory", action="store_true",
                    help="list files present on one side only")
    ap.add_argument("--strict", action="store_true",
                    help="treat one-sided files as failures, not inventory")
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
    return check_pairs(repo, a.ref, strict=a.strict, inventory=a.inventory)


if __name__ == "__main__":
    raise SystemExit(main())
