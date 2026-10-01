#!/usr/bin/env python3
"""agent_patch_apply -- the parent's half of the patch-proposal-v1 contract.

A specialist whose surface it may not write (harness-optimizer: everything under .claude/
is a protected path) returns ONE unified diff instead of editing. This tool is how the
parent applies it, so "the parent applies the patch" is a command, not a sentence.

  python tools/agent_patch_apply.py <reply.md|run.json> --root <repo> [--apply]

Default is a dry run (`git apply --check`). `--apply` changes the working tree.

Why `--recount`: measured 2026-10-01 on GEX44, the first real proposal had a correct body
under a miscounted hunk header (`@@ -2,7 +2,6 @@` over 6 old / 5 new lines). Plain
`git apply` called it a corrupt patch; `--recount` recomputes the counts from the body and
still requires every context and removed line to match the file, so it forgives the
header and nothing else.

Refusals are typed and change nothing: NO_DIFF / MULTIPLE_DIFFS (the contract says exactly
one), PATH_ESCAPES_ROOT (absolute or '..' path in a header), NOT_A_REPO, CHECK_FAILED.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DIFF_RE = re.compile(r"```diff[ \t]*\r?\n(.*?)```", re.S)
HEADER_RE = re.compile(r"(?m)^(?:---|\+\+\+) (?:[ab]/)?(\S+)")


class PatchRefused(ValueError):
    def __init__(self, code: str, msg: str):
        super().__init__(f"{code}: {msg}")
        self.code = code


def extract_patch(reply: str) -> str:
    blocks = DIFF_RE.findall(reply or "")
    if not blocks:
        raise PatchRefused("NO_DIFF", "the reply carries no ```diff block")
    if len(blocks) > 1:
        raise PatchRefused("MULTIPLE_DIFFS", f"{len(blocks)} diff blocks; the contract allows one")
    patch = blocks[0].replace("\r\n", "\n")
    for p in HEADER_RE.findall(patch):
        if p == "/dev/null":
            continue
        if p.startswith("/") or re.match(r"^[A-Za-z]:", p) or ".." in p.split("/"):
            raise PatchRefused("PATH_ESCAPES_ROOT", p)
    return patch if patch.endswith("\n") else patch + "\n"


def _git() -> str:
    g = shutil.which("git") or next((p for p in (r"C:\Program Files\Git\cmd\git.exe",) if Path(p).is_file()), None)
    if not g:
        raise PatchRefused("NO_GIT", "git not found")
    return g


def apply_patch(patch: str, root: Path, apply: bool = False) -> dict:
    root = Path(root)
    if not (root / ".git").exists():
        raise PatchRefused("NOT_A_REPO", str(root))
    git = _git()
    base = [git, "-C", str(root), "apply", "--recount"]
    # Bytes, not text: measured 2026-10-01, text-mode stdin on Windows turned every \n of the
    # patch into \r\n and no line matched the LF file ("patch does not apply").
    data = patch.encode("utf-8")
    chk = subprocess.run(base + ["--check", "-"], input=data, capture_output=True)
    if chk.returncode != 0:
        raise PatchRefused("CHECK_FAILED", chk.stderr.decode("utf-8", "replace").strip()[:400])
    out = {"checked": True, "applied": False,
           "files": sorted({p for p in HEADER_RE.findall(patch) if p != "/dev/null"})}
    if apply:
        r = subprocess.run(base + ["-"], input=data, capture_output=True)
        if r.returncode != 0:
            raise PatchRefused("APPLY_FAILED", r.stderr.decode("utf-8", "replace").strip()[:400])
        out["applied"] = True
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="agent_patch_apply")
    ap.add_argument("source", help="the carrier's reply (.md) or an agent_carrier_run record (.json)")
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    text = Path(a.source).read_text(encoding="utf-8")
    if a.source.endswith(".json"):
        text = json.loads(text).get("reply", "")
    try:
        res = apply_patch(extract_patch(text), Path(a.root), a.apply)
    except PatchRefused as e:
        print(f"PATCH_REFUSED {e.code} {e}", file=sys.stderr)
        return 2
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
