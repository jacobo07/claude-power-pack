#!/usr/bin/env python3
"""Workspace Capsule: the exact relevant state of a working tree, portable (UWCP S2).

A Workstream that moves between hosts needs the WORK, not just the branch:
HEAD, the index, unstaged edits and the untracked files that matter. Forcing a
commit to move them would rewrite what the engineer meant; copying the whole
directory would carry secrets, other people's edits and build debris. So a
capsule is a canonical manifest plus content-addressed parts, captured by rule
and verified on arrival.

    capture(root, out_dir, scope_paths=[...])        -> manifest (dict), parts on disk
    hydrate(capsule_dir, target_dir, capsule_id=...)  -> reproduces the state
    verify(target_dir, manifest)                      -> EQUIVALENT | COMPATIBLE_WITH_DECLARED_DRIFT
                                                         | NON_EQUIVALENT | UNKNOWN
    retain(store, referenced, min_age_s=...)          -> two-pass retention, RETIRED tombstones

The object model (spec amendment A6, uwcp.AMENDMENTS.md):

  * **Identity is two git trees**, never a diff. `index_tree` is the staged
    state and `worktree_tree` the staged+unstaged state, both written from a
    synthetic index SEEDED from the base tree. Seeding keeps what NTFS cannot
    express (100755, 120000 symlinks, gitlinks); an empty-index build drops them.
    Git's own clean form makes the identity eol-invariant.
  * **Restore is by objects.** The bundle carries the trees (as two wrapper
    commits); the node fetches them and renders them with its OWN smudge/eol
    through `read-tree -u`. A patch is bound to the byte representation of the
    host that made it (`git apply` under autocrlf, F-GIT-1) and is never shipped.
  * **Content verification is layered.** Every part and the manifest are named
    by {sha256, size}; size is checked first; digests before git is asked. Then
    `fetch` with transfer.fsckObjects -- `git bundle verify` is structural only:
    measured 2026-09-25, a byte-flipped pack passes it with exit 0.
  * **The conversion environment is recorded** (autocrlf, eol, safecrlf, filter
    drivers in scope, git and LFS versions). Trees differing only in line endings
    under a differing environment are COMPATIBLE_WITH_DECLARED_DRIFT, never
    corruption; under an equal environment they are NON_EQUIVALENT.
  * **Foreign work is never carried.** A dirty path outside the scope, or one
    that was already dirty when the goal began and that no epoch touched, is
    excluded AND reported by name, and travels at its base version.
  * **Secrets refuse the whole capture.** Structural names and content hits in
    ADDED lines refuse; the report names path and pattern, never the value. Two
    instruments: the Secret Firewall's patterns and an independent entropy check.
  * **Refusals, not guesses:** an unmerged index, a required filter that is not
    installed, a dirty gitlink, case-colliding paths onto a case-insensitive host,
    a missing bundle prerequisite (the caller re-captures a full bundle), a dirty
    target. UNKNOWN is never EQUIVALENT, and RETIRED is not NON_EQUIVALENT.
"""
from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import math
import os
import re
import secrets as _secrets
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

EQUIVALENT = "EQUIVALENT"
COMPATIBLE = "COMPATIBLE_WITH_DECLARED_DRIFT"
NON_EQUIVALENT = "NON_EQUIVALENT"
UNKNOWN = "UNKNOWN"
VERDICTS = (EQUIVALENT, COMPATIBLE, NON_EQUIVALENT, UNKNOWN)
RETIRED, PRESENT, ABSENT = "RETIRED", "PRESENT", "ABSENT"

MANIFEST = "manifest.json"
BUNDLE = "base.bundle"
UNTRACKED_TAR = "untracked.tar"
SCHEMA = "uwcp.workspace_capsule/2"
DEFAULT_PART_CAP = 100 * 1024 * 1024          # per part; the node disk is a shared resource
STRUCTURAL_SECRET_GLOBS = (".env", ".env.*", "*.pem", "*.key", "id_rsa*", "id_ed25519*",
                           "id_ecdsa*", "*.p12", "*.pfx", "credentials*.json", "*.keystore")
SECRET_DIRS = frozenset({".ssh", "secrets", "_secrets", ".aws", ".gnupg"})
LOCKFILES = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock",
             "Cargo.lock", "go.sum", "mix.lock", "Gemfile.lock", "composer.lock")
ENTROPY_MIN_LEN = 32
ENTROPY_THRESHOLD = 4.5                      # bits/char; hex digests top out at 4.0
_TOKEN_RE = re.compile(r"[A-Za-z0-9+/=_\-]{%d,}" % ENTROPY_MIN_LEN)
GIT_CANDIDATES = (r"C:\Program Files\Git\cmd\git.exe", "git")
# Wrapper commits are transport, not identity: fixed author and date make them
# reproducible from the trees they carry.
_WRAP_ENV = {"GIT_AUTHOR_NAME": "uwcp", "GIT_AUTHOR_EMAIL": "uwcp@localhost",
             "GIT_COMMITTER_NAME": "uwcp", "GIT_COMMITTER_EMAIL": "uwcp@localhost",
             # git rejects epoch 0 as a date; any fixed instant will do.
             "GIT_AUTHOR_DATE": "1000000000 +0000", "GIT_COMMITTER_DATE": "1000000000 +0000"}
_ZERO = re.compile(r"^0+$")
RETENTION_STATE = ".retention.json"


class CaptureRefused(Exception):
    """The capture would carry a secret, or cannot establish what it carries."""


class HydrateError(Exception):
    """The capsule cannot be reproduced here without loss or damage."""

    def __init__(self, message: str, code: str = "refused"):
        super().__init__(message)
        self.code = code


class MissingPrerequisite(HydrateError):
    """The node lacks the bundle's base commit: re-capture a FULL bundle, never apply partially."""

    def __init__(self, message: str):
        super().__init__(message, "missing_prerequisite")


# --- plumbing -----------------------------------------------------------------

def _git(root: Path, *args: str, stdin: bytes | None = None,
         env: dict | None = None) -> tuple[int, bytes, str]:
    for exe in GIT_CANDIDATES:
        try:
            p = subprocess.run([exe, "-C", str(root), *args], capture_output=True,
                               input=stdin, timeout=600, env=env,
                               stdin=None if stdin is not None else subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            continue
        return p.returncode, p.stdout or b"", (p.stderr or b"").decode("utf-8", "replace")
    return 127, b"", "git not found"


def _git_ok(root: Path, *args: str, stdin: bytes | None = None, env: dict | None = None,
            exc=CaptureRefused) -> bytes:
    rc, out, err = _git(root, *args, stdin=stdin, env=env)
    if rc != 0:
        raise exc(f"git {' '.join(args[:3])} failed: {err.strip()[:200]}")
    return out


def _cfg(root: Path, key: str) -> str:
    return _git(root, "config", "--get", key)[1].decode("utf-8", "replace").strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _no_floats(obj, where: str = "manifest") -> None:
    if isinstance(obj, float):
        raise CaptureRefused(f"{where} carries a float; the canonical form admits none")
    if isinstance(obj, dict):
        for k, v in obj.items():
            _no_floats(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for v in obj:
            _no_floats(v, where)


def _canonical(obj) -> bytes:
    """UTF-8, sorted keys, no whitespace, no floats: the bytes the capsule id names."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def _pkey(p: str) -> bytes:
    return p.encode("utf-8", "surrogateescape")


def _in_scope(path: str, scope: list[str]) -> bool:
    for s in scope:
        s = s.strip("/")
        if s in ("", "."):
            return True
        if path == s or path.startswith(s + "/"):
            return True
    return False


def _structural_secret(path: str) -> bool:
    parts = path.split("/")
    if SECRET_DIRS.intersection(parts[:-1]):
        return True
    return any(fnmatch.fnmatch(parts[-1], g) for g in STRUCTURAL_SECRET_GLOBS)


def _entropy(token: str) -> float:
    counts: dict[str, int] = {}
    for ch in token:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(token)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def _is_binary(data: bytes) -> bool:
    return b"\0" in data[:8000]


def content_hits(label: str, data: bytes) -> list[str]:
    """Secret findings for one blob of content, as 'label: pattern' -- never the value."""
    if _is_binary(data):
        return []
    from modules.secret_firewall.detector import scan_text  # noqa: PLC0415
    text = data.decode("utf-8", "replace")
    hits = [f"{label}: {h.pattern_name}" for h in scan_text(text)]
    for m in _TOKEN_RE.finditer(text):
        if _entropy(m.group(0)) > ENTROPY_THRESHOLD:
            hits.append(f"{label}: high_entropy_token")
            break
    return hits


def _added_lines(patch: bytes) -> bytes:
    """Only what the capture ADDS: context and removed lines are already in the base."""
    keep = [ln[1:] for ln in patch.split(b"\n")
            if ln.startswith(b"+") and not ln.startswith(b"+++")]
    return b"\n".join(keep)


def _status(root: Path) -> tuple[set, set, set]:
    """(staged, unstaged, untracked) repo-relative posix paths."""
    raw = _git_ok(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    staged, unstaged, untracked = set(), set(), set()
    entries = raw.split(b"\0")
    i = 0
    while i < len(entries):
        e = entries[i].decode("utf-8", "surrogateescape")
        i += 1
        if len(e) < 4:
            continue
        x, y, path = e[0], e[1], e[3:]
        if x in "RC":            # rename/copy: the next entry is the source path
            i += 1
        if x == "?" and y == "?":
            untracked.add(path)
            continue
        if x not in " ?":
            staged.add(path)
        if y not in " ?":
            unstaged.add(path)
    return staged, unstaged, untracked


def _ls_tree(root: Path, tree: str, scope: list[str] | None = None) -> list[tuple[str, str, str]]:
    """(mode, oid, path) for every entry of `tree`, recursively."""
    args = ["ls-tree", "-r", "-z", "--full-tree", tree]
    raw = _git_ok(root, *args)
    out = []
    for ent in raw.split(b"\0"):
        if not ent:
            continue
        meta, _, path = ent.decode("utf-8", "surrogateescape").partition("\t")
        mode, _typ, oid = meta.split()
        if scope is None or _in_scope(path, scope):
            out.append((mode, oid, path))
    return out


def _object_format(root: Path) -> str:
    rc, out, _ = _git(root, "rev-parse", "--show-object-format")
    return out.decode().strip() if rc == 0 and out.strip() else "sha1"


def case_collisions(paths) -> list[list[str]]:
    """Groups of paths that differ only by case -- one of each is lost on NTFS/APFS."""
    groups: dict[str, list[str]] = {}
    for p in paths:
        groups.setdefault(p.casefold(), []).append(p)
    return sorted(sorted(g) for g in groups.values() if len(g) > 1)


def _case_insensitive(root: Path) -> bool:
    ic = _cfg(root, "core.ignorecase").lower()
    if ic in ("true", "false"):
        return ic == "true"
    return os.name == "nt" or sys.platform == "darwin"


def conversion_env(root: Path, drivers=()) -> dict:
    """The host settings that decide a file's clean form (a correctness baseline field)."""
    lfs = _git(root, "lfs", "version")
    return {"autocrlf": _cfg(root, "core.autocrlf"), "eol": _cfg(root, "core.eol"),
            "safecrlf": _cfg(root, "core.safecrlf"),
            "git_version": _git(root, "version")[1].decode().strip(),
            "lfs_version": lfs[1].decode().strip() if lfs[0] == 0 else "",
            "filters_in_scope": {d: bool(_cfg(root, f"filter.{d}.clean")
                                         or _cfg(root, f"filter.{d}.process"))
                                 for d in sorted(drivers)}}


def _filters_in_scope(root: Path, paths: list[str]) -> list[str]:
    if not paths:
        return []
    stdin = b"\0".join(_pkey(p) for p in paths) + b"\0"
    raw = _git_ok(root, "check-attr", "-z", "--stdin", "filter", stdin=stdin)
    f = raw.split(b"\0")
    drivers = set()
    for i in range(0, len(f) - 2, 3):
        v = f[i + 2].decode("utf-8", "replace")
        if v not in ("unspecified", "unset", "set", ""):
            drivers.add(v)
    return sorted(drivers)


# --- capture ------------------------------------------------------------------

def capture(root, out_dir, *, scope_paths, foreign_baseline=(), owned=(),
            include_untracked=(), base_known: str | None = None, declared_drift=(),
            part_cap: int = DEFAULT_PART_CAP, provenance: dict | None = None) -> dict:
    """Write a capsule for `root` into `out_dir` and return its manifest.

    `base_known` is the node's answer to "have" asked AT DISPATCH, never a
    remembered head: a commit the node holds lets the bundle be incremental.
    The manifest is written last, so a directory without one is in flight.
    """
    from modules.repo_identity.identity import PortableIdUnknown, portable_repo_id  # noqa
    root, out = Path(root), Path(out_dir)
    scope = [str(s).replace("\\", "/") for s in (scope_paths or [])]
    if not scope:
        raise CaptureRefused("a capsule needs declared scope paths ('.' for the whole repo)")
    try:
        repo_id = portable_repo_id(root)
    except PortableIdUnknown as exc:
        raise CaptureRefused(f"no portable repository identity: {exc}") from exc
    if _git_ok(root, "ls-files", "-u", "-z").strip(b"\0"):
        raise CaptureRefused("the index is unmerged (a merge or rebase is in progress); "
                             "a mid-merge state is not a capsule")
    fmt = _object_format(root)
    head = _git_ok(root, "rev-parse", "HEAD").decode().strip()
    base_tree = _git_ok(root, "rev-parse", "HEAD^{tree}").decode().strip()
    rc, br, _ = _git(root, "symbolic-ref", "--short", "-q", "HEAD")
    branch = br.decode().strip() if rc == 0 else ""
    rc, org, _ = _git(root, "remote", "get-url", "origin")
    origin = org.decode().strip() if rc == 0 else ""

    staged, unstaged, untracked = _status(root)
    owned_set, baseline = set(owned or ()), set(foreign_baseline or ())
    dirty = staged | unstaged | untracked
    foreign = sorted((p for p in dirty
                      if not _in_scope(p, scope) or (p in baseline and p not in owned_set)),
                     key=_pkey)
    fset = set(foreign)
    excluded = [{"path": p, "reason": "foreign: outside scope or pre-existing and untouched"}
                for p in foreign]
    carry_untracked = []
    for p in sorted(untracked - fset, key=_pkey):
        if any(fnmatch.fnmatch(p, g) for g in include_untracked):
            carry_untracked.append(p)
        else:
            excluded.append({"path": p, "reason": "untracked and not allowlisted"})
    excluded.sort(key=lambda e: _pkey(e["path"]))
    carry_staged = sorted(staged - fset, key=_pkey)
    carry_unstaged = sorted(unstaged - fset, key=_pkey)

    secret_paths = [p for p in carry_staged + carry_unstaged + carry_untracked
                    if _structural_secret(p)]
    if secret_paths:
        raise CaptureRefused(f"structural secret path(s) would be carried: {secret_paths}")

    real_modes = {}
    if carry_staged or carry_unstaged:
        for ln in _git_ok(root, "ls-files", "-s", "-z", "--",
                          *(carry_staged + carry_unstaged)).split(b"\0"):
            meta, _, p = ln.decode("utf-8", "surrogateescape").partition("\t")
            if p:
                real_modes[p] = meta.split()
    dirty_links = [p for p in carry_staged + carry_unstaged
                   if real_modes.get(p, [""])[0] == "160000"]
    if dirty_links:
        raise CaptureRefused(f"dirty submodule(s) {dirty_links}: a gitlink's own work is not "
                             "in the parent capsule; commit it there or declare it foreign")

    # Secret scan over what the capture ADDS (instrument only; diffs are never shipped).
    hits: list[str] = []
    if carry_staged:
        hits += content_hits("staged", _added_lines(_git_ok(
            root, "diff", "--cached", "-U0", "--no-color", "--no-ext-diff", "--",
            *carry_staged)))
    if carry_unstaged:
        hits += content_hits("unstaged", _added_lines(_git_ok(
            root, "diff", "-U0", "--no-color", "--no-ext-diff", "--", *carry_unstaged)))
    untracked_data: dict[str, bytes] = {}
    for p in carry_untracked:
        try:
            untracked_data[p] = (root / p).read_bytes()
        except OSError as exc:
            raise CaptureRefused(f"untracked {p} unreadable: {exc}") from exc
        hits += content_hits(p, untracked_data[p])
    if hits:
        raise CaptureRefused(f"secret-like content would be carried: {sorted(set(hits))}")

    # Filters decide clean form. A required driver this host lacks makes the
    # identity unknowable here: refuse rather than record a host-shaped tree.
    in_scope_tracked = [p.decode("utf-8", "surrogateescape")
                        for p in _git_ok(root, "ls-files", "-z", "--", *scope).split(b"\0") if p]
    drivers = _filters_in_scope(root, in_scope_tracked + carry_untracked)
    for d in drivers:
        installed = bool(_cfg(root, f"filter.{d}.clean") or _cfg(root, f"filter.{d}.process"))
        if not installed and _cfg(root, f"filter.{d}.required").lower() == "true":
            raise CaptureRefused(f"filter driver {d!r} is required by .gitattributes in scope "
                                 "and not installed on this host")
    env_conv = conversion_env(root, drivers)

    # The two trees, from a synthetic index seeded from the base tree.
    with tempfile.TemporaryDirectory(prefix="uwcp-idx-") as td:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(td) / "index")}
        _git_ok(root, "read-tree", base_tree, env=env)
        info, removed = [], []
        for p in carry_staged:
            if p in real_modes:
                mode, oid, _stage = real_modes[p]
                info.append(_pkey(f"{mode} {oid}\t{p}"))
            else:
                removed.append(p)
        if info:
            _git_ok(root, "update-index", "-z", "--index-info",
                    stdin=b"\0".join(info) + b"\0", env=env)
        if removed:
            _git_ok(root, "update-index", "--force-remove", "--", *removed, env=env)
        index_tree = _git_ok(root, "write-tree", env=env).decode().strip()
        present = [p for p in carry_unstaged if (root / p).exists() or (root / p).is_symlink()]
        gone = [p for p in carry_unstaged if p not in present]
        if present:
            _git_ok(root, "update-index", "--add", "--", *present, env=env)
        if gone:
            _git_ok(root, "update-index", "--force-remove", "--", *gone, env=env)
        worktree_tree = _git_ok(root, "write-tree", env=env).decode().strip()

    out.mkdir(parents=True, exist_ok=True)
    parts: list[dict] = []

    def put(name: str, role: str, data: bytes) -> None:
        if len(data) > part_cap:
            raise CaptureRefused(f"part {name} is {len(data)} bytes, cap {part_cap}")
        (out / name).write_bytes(data)
        parts.append({"name": name, "role": role, "size": len(data),
                      "sha256": hashlib.sha256(data).hexdigest()})

    # Transport: two wrapper commits (parent = head) under temporary refs, bundled.
    prereq = ""
    if base_known:
        if base_known == head:
            prereq = head
        else:
            rc, _, _ = _git(root, "merge-base", "--is-ancestor", base_known, head)
            prereq = base_known if rc == 0 else ""
    nonce = _secrets.token_hex(6)
    refs = {"index": f"refs/uwcp/{nonce}/index", "worktree": f"refs/uwcp/{nonce}/worktree"}
    wrap_env = {**os.environ, **_WRAP_ENV}
    commits = {}
    try:
        for role, tree in (("index", index_tree), ("worktree", worktree_tree)):
            commits[role] = _git_ok(root, "commit-tree", tree, "-p", head, "-m",
                                    f"uwcp capsule {role} tree", env=wrap_env).decode().strip()
            _git_ok(root, "update-ref", refs[role], commits[role])
        bpath = out / BUNDLE
        revs = ([f"^{prereq}"] if prereq else []) + [refs["index"], refs["worktree"]]
        _git_ok(root, "bundle", "create", "-q", str(bpath), *revs)
        # Structural check only (header, prerequisites); content is proven at fetch.
        _git_ok(root, "bundle", "verify", "-q", str(bpath))
    finally:
        for r in refs.values():
            _git(root, "update-ref", "-d", r)
    size = bpath.stat().st_size
    if size > part_cap:
        raise CaptureRefused(f"bundle is {size} bytes, cap {part_cap}")
    parts.append({"name": BUNDLE, "role": "bundle", "size": size, "sha256": _sha256(bpath),
                  "prerequisites": [prereq] if prereq else [], "refs": refs,
                  "commits": commits})

    untracked_ids = []
    if carry_untracked:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for p in carry_untracked:
                data = untracked_data[p]
                exe = os.name != "nt" and os.access(root / p, os.X_OK)
                info = tarfile.TarInfo(p)
                info.size, info.mtime, info.mode = len(data), 0, 0o755 if exe else 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                tar.addfile(info, io.BytesIO(data))
                untracked_ids.append({"path": p, "size": len(data),
                                      "sha256": hashlib.sha256(data).hexdigest(),
                                      "mode": "100755" if exe else "100644"})
        put(UNTRACKED_TAR, "untracked_tar", buf.getvalue())
    parts.sort(key=lambda d: _pkey(d["name"]))

    entries = _ls_tree(root, worktree_tree, scope)
    body = {
        "schema": SCHEMA, "digest_function": "sha256", "git_object_format": fmt,
        "repo_id": repo_id, "origin": origin, "branch": branch,
        "base": {"commit": head, "tree": base_tree},
        "trees": {"index_tree": index_tree, "worktree_tree": worktree_tree},
        "scope": scope,
        "untracked": untracked_ids,
        "gitlinks": [{"path": p, "commit": o} for m, o, p in entries if m == "160000"],
        "lockfiles": [{"path": p, "blob": o} for m, o, p in entries
                      if p.rsplit("/", 1)[-1] in LOCKFILES],
        "conversion_env": env_conv,
        "carried": {"staged": carry_staged, "unstaged": carry_unstaged,
                    "untracked": carry_untracked},
        "excluded": excluded, "foreign": foreign,
        "declared_drift": sorted(declared_drift or (), key=_pkey),
        "parts": parts,
        "provenance": {"captured_at": datetime.now(timezone.utc).isoformat(),
                       "host": socket.gethostname(), **(provenance or {})},
    }
    _no_floats(body)
    raw = _canonical(body)
    (out / MANIFEST).write_bytes(raw)          # last: its presence marks a complete capsule
    return {**body, "capsule_id": hashlib.sha256(raw).hexdigest(), "manifest_size": len(raw)}


# --- hydrate ------------------------------------------------------------------

def load_manifest(capsule_dir, expected_id: str | None = None) -> dict:
    """Parse and authenticate a manifest. The id is the sha256 of its exact bytes."""
    raw = (Path(capsule_dir) / MANIFEST).read_bytes()
    try:
        m = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HydrateError(f"manifest unreadable: {exc}", "corrupt_manifest") from exc
    if not isinstance(m, dict) or m.get("schema") != SCHEMA or _canonical(m) != raw:
        raise HydrateError("manifest is not in canonical form (tampered or truncated)",
                           "corrupt_manifest")
    cid = hashlib.sha256(raw).hexdigest()
    if expected_id is not None and cid != expected_id:
        raise HydrateError(f"manifest is capsule {cid[:12]}, not the authorized "
                           f"{expected_id[:12]}", "wrong_capsule")
    return {**m, "capsule_id": cid, "manifest_size": len(raw)}


def _tombstone(capsule_dir: Path, capsule_id: str) -> Path | None:
    for t in (capsule_dir.parent / f"{capsule_id}.retired",
              capsule_dir.parent / f"{capsule_dir.name}.retired"):
        if t.is_file():
            return t
    return None


def hydrate(capsule_dir, target_dir, *, capsule_id: str) -> dict:
    """Reproduce capsule `capsule_id` in `target_dir`. Refuses rather than damages."""
    cap, target = Path(capsule_dir), Path(target_dir)
    if not (cap / MANIFEST).is_file():
        tomb = _tombstone(cap, capsule_id)
        if tomb:
            raise HydrateError(f"capsule {capsule_id[:12]} was retired by retention "
                               f"({tomb.read_text(encoding='utf-8')[:160]})", RETIRED)
        raise HydrateError(f"capsule {capsule_id[:12]} has no manifest here", ABSENT)
    m = load_manifest(cap, capsule_id)
    # Size first, then digest -- all before git is asked anything.
    for part in m["parts"]:
        p = cap / part["name"]
        if not p.is_file():
            raise HydrateError(f"capsule part {part['name']} is missing", "corrupt_part")
        if p.stat().st_size != part["size"]:
            raise HydrateError(f"capsule part {part['name']} is {p.stat().st_size} bytes, "
                               f"manifest says {part['size']}", "corrupt_part")
        if _sha256(p) != part["sha256"]:
            raise HydrateError(f"capsule part {part['name']} does not match its digest",
                               "corrupt_part")
    bundle = next(p for p in m["parts"] if p["role"] == "bundle")

    if not (target / ".git").exists():
        target.mkdir(parents=True, exist_ok=True)
        _git_ok(target, "init", "-q", f"--object-format={m['git_object_format']}",
                exc=HydrateError)
    else:
        if _object_format(target) != m["git_object_format"]:
            raise HydrateError(f"target repository is {_object_format(target)}, capsule is "
                               f"{m['git_object_format']}", "object_format")
        try:
            staged, unstaged, _ = _status(target)
        except CaptureRefused as exc:
            raise HydrateError(f"target status unreadable: {exc}", UNKNOWN) from exc
        if staged or unstaged:
            raise HydrateError("target repository has uncommitted changes; refusing to "
                               "overwrite work nobody authorized destroying", "dirty_target")
    for c in bundle.get("prerequisites") or ():
        if _git(target, "cat-file", "-e", f"{c}^{{commit}}")[0] != 0:
            raise MissingPrerequisite(f"target lacks base commit {c[:12]}; re-capture a full "
                                      "bundle (base_known=None) and dispatch that")
    specs = [f"+{r}:{r}" for r in bundle["refs"].values()]
    rc, _, err = _git(target, "-c", "transfer.fsckObjects=true", "-c", "fetch.fsckObjects=true",
                      "fetch", "-q", str((cap / BUNDLE).resolve()), *specs)
    if rc != 0:
        raise HydrateError(f"bundle objects failed to fetch/verify: {err.strip()[:200]}",
                           "fetch_failed")
    trees = m["trees"]
    if _case_insensitive(target):
        names = [p for _m, _o, p in _ls_tree(target, trees["worktree_tree"])]
        twins = case_collisions(names)
        if twins:
            raise HydrateError(f"case-colliding paths {twins[:3]} cannot coexist on this "
                               "case-insensitive host", "case_collision")
    for args in (("checkout", "-q", "--detach", m["base"]["commit"]),
                 ("read-tree", "-m", "-u", "HEAD", trees["worktree_tree"]),
                 ("read-tree", trees["index_tree"])):
        rc, _, err = _git(target, *args)
        if rc != 0:
            raise HydrateError(f"git {args[0]} failed: {err.strip()[:200]}", "restore_failed")
    if any(p["role"] == "untracked_tar" for p in m["parts"]):
        with tarfile.open(cap / UNTRACKED_TAR) as tar:
            for mem in tar.getmembers():
                n = mem.name.replace("\\", "/")
                if n.startswith("/") or ".." in n.split("/") or not mem.isfile():
                    raise HydrateError(f"refusing unsafe capsule member {mem.name!r}",
                                       "unsafe_member")
                data = tar.extractfile(mem).read()
                dest = target / n
                if dest.exists() and dest.read_bytes() != data:
                    raise HydrateError(f"untracked {n} already exists here with other bytes",
                                       "dirty_target")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
    return {"head": m["base"]["commit"], "capsule_id": m["capsule_id"]}


# --- verify -------------------------------------------------------------------

def _diff_tree(root: Path, a: str, b: str) -> list[tuple[str, str, str]]:
    """(old_oid, new_oid, path) for entries that differ between trees a and b."""
    raw = _git_ok(root, "diff-tree", "-r", "-z", "--no-renames", a, b)
    f = raw.split(b"\0")
    out = []
    for i in range(0, len(f) - 1, 2):
        meta = f[i].decode()
        if not meta.startswith(":"):
            continue
        _om, _nm, oo, no, _st = meta[1:].split()
        out.append((oo, no, f[i + 1].decode("utf-8", "surrogateescape")))
    return out


def _blob_bytes(root: Path, oid: str) -> bytes | None:
    if _ZERO.match(oid):
        return None
    rc, out, _ = _git(root, "cat-file", "blob", oid)
    return out if rc == 0 else None


def verify(target_dir, manifest: dict) -> tuple[str, list[str]]:
    """Is `target_dir` the captured state? One of VERDICTS, plus reasons."""
    target = Path(target_dir)
    try:
        rc, out, err = _git(target, "rev-parse", "HEAD")
        if rc != 0:
            return UNKNOWN, [f"cannot read HEAD: {err.strip()[:120]}"]
        reasons, drift = [], []
        head = out.decode().strip()
        if head != manifest["base"]["commit"]:
            reasons.append(f"HEAD {head[:12]} != {manifest['base']['commit'][:12]}")
        cap_env = manifest["conversion_env"]
        node_env = conversion_env(target, cap_env.get("filters_in_scope", {}))
        absent = sorted(d for d, ok in cap_env.get("filters_in_scope", {}).items()
                        if not ok or not node_env["filters_in_scope"].get(d))
        if absent:
            return UNKNOWN, [f"filter driver(s) {absent} not installed on both hosts; the "
                             "clean form cannot be compared"]
        if _git_ok(target, "ls-files", "-u", "-z").strip(b"\0"):
            return UNKNOWN, ["target index is unmerged"]
        env_differs = any(cap_env.get(k) != node_env.get(k) for k in ("autocrlf", "eol"))
        got_index = _git_ok(target, "write-tree").decode().strip()
        idx_path = Path(_git_ok(target, "rev-parse", "--git-path", "index").decode().strip())
        if not idx_path.is_absolute():
            idx_path = target / idx_path
        with tempfile.TemporaryDirectory(prefix="uwcp-vfy-") as td:
            env = {**os.environ, "GIT_INDEX_FILE": str(Path(td) / "index")}
            shutil.copyfile(idx_path, Path(td) / "index")
            _git_ok(target, "add", "-u", "--", ".", env=env)
            got_work = _git_ok(target, "write-tree", env=env).decode().strip()
        declared = set(manifest.get("declared_drift") or ())
        seen = set()
        for label, want, got in (("index", manifest["trees"]["index_tree"], got_index),
                                 ("worktree", manifest["trees"]["worktree_tree"], got_work)):
            if want == got:
                continue
            if _git(target, "cat-file", "-e", f"{want}^{{tree}}")[0] != 0:
                reasons.append(f"{label} tree {want[:12]} absent here: the capsule's objects "
                               "never arrived")
                continue
            for oo, no, p in _diff_tree(target, want, got):
                if p in seen:
                    continue
                seen.add(p)
                if p in declared:
                    drift.append(f"{p}: declared drift")
                    continue
                a, b = _blob_bytes(target, oo), _blob_bytes(target, no)
                if (env_differs and a is not None and b is not None and not _is_binary(a)
                        and not _is_binary(b)
                        and a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")):
                    drift.append(f"{p}: line endings differ under a differing conversion_env")
                else:
                    reasons.append(f"{label} {p} differs")
        for g in manifest.get("gitlinks") or ():
            sub = target / g["path"]
            rc, so, _ = _git(sub, "rev-parse", "HEAD") if (sub / ".git").exists() else (1, b"", "")
            if rc != 0 or so.decode().strip() != g["commit"]:
                reasons.append(f"submodule {g['path']} objects absent or at another commit")
        for u in manifest.get("untracked") or ():
            fp = target / u["path"]
            ok = fp.is_file() and fp.stat().st_size == u["size"] and _sha256(fp) == u["sha256"]
            if not ok:
                (drift if u["path"] in declared else reasons).append(
                    f"untracked {u['path']} missing or differs")
    except (OSError, KeyError, ValueError, CaptureRefused, subprocess.SubprocessError) as exc:
        return UNKNOWN, [f"could not judge: {exc}"]
    if reasons:
        return NON_EQUIVALENT, reasons
    if drift:
        return COMPATIBLE, drift
    return EQUIVALENT, []


# --- retention ----------------------------------------------------------------

def capsule_status(store, capsule_id: str) -> str:
    """PRESENT | RETIRED | ABSENT for a capsule stored as <store>/<capsule_id>/."""
    store = Path(store)
    d = store / capsule_id
    if (d / MANIFEST).is_file():
        try:
            load_manifest(d, capsule_id)
            return PRESENT
        except HydrateError:
            return ABSENT
    return RETIRED if (store / f"{capsule_id}.retired").is_file() else ABSENT


def retain(store, referenced, *, min_age_s: float, now: float | None = None) -> dict:
    """One retention pass over <store>/<capsule_id>/ directories.

    `referenced` = capsule ids in the last N receipts UNION queued/running
    manifests -- the caller's authority, re-asked every pass. A capsule is
    retired only when it is older than `min_age_s` (>= max epoch budget +
    transfer margin) AND was unreferenced on the previous pass too. A directory
    with no valid manifest is in flight (the manifest is written last) and is
    never deleted. Retirement leaves a tombstone so hydrate can say RETIRED.
    """
    store = Path(store)
    now = time.time() if now is None else now
    referenced = set(referenced)
    state_p = store / RETENTION_STATE
    try:
        marked = json.loads(state_p.read_text(encoding="utf-8")).get("unreferenced", {})
    except (OSError, ValueError):
        marked = {}
    report = {"retired": [], "marked": [], "referenced": [], "young": [], "in_flight": []}
    next_marked = {}
    for d in sorted(p for p in store.iterdir() if p.is_dir()) if store.is_dir() else ():
        mp = d / MANIFEST
        if not mp.is_file():
            report["in_flight"].append(d.name)
            continue
        try:
            cid = load_manifest(d)["capsule_id"]
        except (HydrateError, OSError):
            report["in_flight"].append(d.name)
            continue
        if cid in referenced:
            report["referenced"].append(cid)
            continue
        if now - mp.stat().st_mtime <= min_age_s:
            report["young"].append(cid)
            continue
        if cid in marked:
            # Re-judge immediately before the destruction: the same bytes, still unreferenced.
            if load_manifest(d)["capsule_id"] != cid or cid in referenced:
                continue
            (store / f"{cid}.retired").write_text(json.dumps(
                {"retired_at": datetime.now(timezone.utc).isoformat(),
                 "reason": "unreferenced on two retention passes and older than the margin",
                 "first_unreferenced": marked[cid]}), encoding="utf-8")
            shutil.rmtree(d)
            report["retired"].append(cid)
        else:
            next_marked[cid] = now
            report["marked"].append(cid)
    store.mkdir(parents=True, exist_ok=True)
    state_p.write_text(json.dumps({"unreferenced": next_marked}), encoding="utf-8")
    return report
