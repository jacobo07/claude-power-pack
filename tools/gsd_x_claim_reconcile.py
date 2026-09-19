#!/usr/bin/env python3
"""Reconcile the GSD X claims ledger against authoritative projections.

The ledger (`vault/datasets/gsd_x/claims.jsonl`) had a gate that returned 6/6
exit 0 while the corpus was 27 commits stale. Every clause was honest: fields
present, vocabulary closed, companions bound, cross-references resolved, and
the honesty clause satisfied. Nothing was contradicted, because the missing
knowledge was never asserted falsely -- it was never asserted at all.

So this reconciler answers two questions the gate could not:

  1. STALE_DEPENDENCY -- did a surface a claim was observed against move since
     the claim recorded it?  Answered from git blob SHAs, never from dates.
  2. UNCOVERED_EVIDENCE -- did material evidence land that no claim speaks
     about?  This is the class that let the corpus go stale while green.

Measured 2026-09-19 and the reason (2) exists: of the 12 distinct surfaces the
21 path-naming claims were observed against, ZERO moved across the 27
unreconciled commits. A dependency detector reports CURRENT for all of them
and is right to. The corpus was stale anyway, because every unreconciled
commit touched a surface no claim names. Coverage is therefore scoped to the
COMPLEMENT of the claimed surfaces, not to them.

It never writes the ledger. Deterministic facts are produced deterministically;
deciding which uncovered event deserves a claim is a semantic judgement and is
left to a human or a model reading `--propose` output.

Exit codes -- three outcomes, never two:
    0  ran, nothing to reconcile
    1  ran, findings to reconcile
    2  INSTRUMENT_FAILED -- could not judge. Never conflated with 0 or 1.

Usage:
    python tools/gsd_x_claim_reconcile.py                  # report
    python tools/gsd_x_claim_reconcile.py --propose out.md # + candidate rows
    python tools/gsd_x_claim_reconcile.py --since <sha>    # override boundary
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATASET = Path(os.environ.get("GSDX_DATASET") or REPO / "vault" / "datasets" / "gsd_x" / "claims.jsonl")

# The commit at which the ledger was last reconciled. Overridable, because a
# future reconciliation moves it and nothing should have to edit this file.
def _boundary() -> str:
    """The commit through which the ledger has been reconciled.

    GSDX-D09 decided this advances with each reconciliation. Holding it as a
    constant in the reader made that decision documented but not executable --
    the ledger could be reconciled and the reconciler would keep measuring from
    a boundary four waves old. It is a fact about the corpus, so it lives beside
    the corpus.
    """
    if os.environ.get("GSDX_SINCE"):
        return os.environ["GSDX_SINCE"]
    marker = DATASET.parent / "RECONCILED-THROUGH"
    if marker.is_file():
        val = marker.read_text(encoding="utf-8-sig").strip()
        if val:
            return val
    return "fd87e39"


DEFAULT_SINCE = _boundary()

# --- materiality -----------------------------------------------------------
#
# A commit is a MATERIAL EVIDENCE EVENT when it touches at least one file and
# not every file it touches merely restates state.
#
# NARRATION restates; it never establishes. These three patterns are this
# estate's own naming conventions, each with a measured instance in
# fd87e39..HEAD:
#   RESUMPTION_FILE.md                       -> 265c12c
#   *.RESUMPTION.md                          -> 396477d, 8138d50, 1fdd3cc
#   .planning/**/*-CONTEXT.md                -> 72fc059
NARRATION = (
    re.compile(r"^RESUMPTION_FILE\.md$"),
    re.compile(r"(^|/)[^/]*\.RESUMPTION\.md$"),
    re.compile(r"^\.planning/.*-CONTEXT\.md$", re.IGNORECASE),
)

# GENERATED trees are machine-authored; a change there is an artifact of a
# producer run, not evidence about the system.
GENERATED = (
    re.compile(r"^docs/(arch|changelog|constitution|prd)/"),
    re.compile(r"^_knowledge_graph/"),
    re.compile(r"^_audit_cache/"),
)

# --- instrument controls ---------------------------------------------------
#
# A sweep that silently stops matching must not read as a clean bill. Ported
# from tools/gsd_x_ups_sweep.py:63-67, which encodes the same rule.
# A sweep that silently stops matching must not read as a clean bill. The first
# version of this control was a MINIMUM COMMIT COUNT, which worked exactly once:
# after a reconciliation the range is legitimately short, so the floor turned a
# freshly-reconciled ledger into a permanent INSTRUMENT_FAILED. An empty range is
# the CORRECT answer to "what landed since we last reconciled", not a defect.
#
# What actually needs asserting is that the BOUNDARY is real and behind us --
# a boundary that does not resolve, or that is not an ancestor of HEAD, means the
# sweep is measuring from nowhere and its emptiness means nothing.
POSITIVE_CONTROL = "9c30713"     # the first confirmed resume. While it is inside
                                 # the range the predicate must reach it; once the
                                 # boundary passes it, it must be an ANCESTOR of
                                 # the boundary -- which proves the boundary did
                                 # not jump past reality rather than skipping the
                                 # check.

SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")


class InstrumentFailure(RuntimeError):
    """The reconciler could not judge. Never a statement about the ledger."""


def _git_exe() -> str:
    """git is not on PowerShell's non-interactive PATH on this host."""
    found = shutil.which("git")
    if found:
        return found
    for candidate in (r"C:\Program Files\Git\cmd\git.exe", "/usr/bin/git"):
        if Path(candidate).exists():
            return candidate
    raise InstrumentFailure("git not found on PATH or at any known location")


def git(*args: str) -> str:
    try:
        out = subprocess.run(
            [_git_exe(), "-C", str(REPO), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=False,
        )
    except OSError as exc:
        raise InstrumentFailure(f"git {' '.join(args)}: {exc}") from exc
    if out.returncode != 0:
        raise InstrumentFailure(
            f"git {' '.join(args)} exited {out.returncode}: {out.stderr.strip()[:200]}"
        )
    return out.stdout


def load_claims() -> list[dict]:
    if not DATASET.is_file():
        raise InstrumentFailure(f"no dataset at {DATASET}")
    rows = []
    for n, line in enumerate(DATASET.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise InstrumentFailure(f"{DATASET.name}:{n} is not JSON: {exc}") from exc
    return rows


def is_narration_or_generated(path: str) -> bool:
    path = path.replace("\\", "/")
    return any(p.search(path) for p in NARRATION) or any(p.search(path) for p in GENERATED)


def commit_files(sha: str) -> list[str]:
    raw = git("show", "--name-only", "--format=", sha)
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def material_events(since: str) -> tuple[list[dict], list[dict]]:
    """Split the range into material evidence events and everything else."""
    try:
        git("rev-parse", "--verify", f"{since}^{{commit}}")
    except InstrumentFailure:
        raise InstrumentFailure(
            f"boundary {since!r} does not resolve to a commit"
        ) from None
    try:
        git("merge-base", "--is-ancestor", since, "HEAD")
    except InstrumentFailure:
        raise InstrumentFailure(
            f"boundary {since} is not an ancestor of HEAD -- the sweep would "
            "measure from a commit this branch never passed through"
        ) from None
    log = git("log", "--reverse", "--format=%H%x1f%s", f"{since}..HEAD")
    entries = [ln for ln in log.splitlines() if ln.strip()]

    material, skipped = [], []
    for entry in entries:
        sha, _, subject = entry.partition("\x1f")
        files = commit_files(sha)
        if not files:
            skipped.append({"sha": sha, "subject": subject, "why": "touches zero files"})
            continue
        # A commit touching ONLY the ledger is the act of reconciling, not
        # evidence to reconcile. Without this the reconciler can never reach
        # zero: every reconciliation it prompts becomes a new finding.
        if all(f.replace("\\", "/").startswith("vault/datasets/gsd_x/") for f in files):
            skipped.append({"sha": sha, "subject": subject, "why": "ledger bookkeeping"})
            continue
        substantive = [f for f in files if not is_narration_or_generated(f)]
        if not substantive:
            skipped.append({"sha": sha, "subject": subject, "why": "narration or generated only"})
            continue
        material.append({"sha": sha, "subject": subject, "files": substantive})

    reachable = {e["sha"][:7] for e in material} | {e["sha"][:7] for e in skipped}
    if POSITIVE_CONTROL not in reachable:
        # Out of range is legitimate once the boundary has advanced past it --
        # but only if it is genuinely BEHIND the boundary. Anything else means
        # the boundary points somewhere the control never was.
        try:
            git("merge-base", "--is-ancestor", POSITIVE_CONTROL, since)
        except InstrumentFailure:
            raise InstrumentFailure(
                f"positive control {POSITIVE_CONTROL} is neither inside "
                f"{since}..HEAD nor an ancestor of {since}. The boundary does "
                "not describe this history, and a clean result would mean "
                "nothing."
            ) from None
    return material, skipped


def referenced_shas(claims: list[dict]) -> set[str]:
    """Every short-sha-shaped token any claim mentions, in any prose field."""
    out: set[str] = set()
    for c in claims:
        blob = " ".join(
            str(c.get(k, "")) for k in ("evidence", "instrument", "note", "rationale", "claim")
        )
        out.update(m.group(0)[:7] for m in SHA_RE.finditer(blob))
    return out


# A claim set where nothing carries depends_on yields "0 stale" -- which is
# indistinguishable from a healthy corpus and is the SAME vacuous-pass defect
# this reconciler exists to close, one layer in. Below the floor the dependency
# half reports that it could not judge, never that it found nothing.
MIN_PINNED_CLAIMS = 10


# Two kinds, both implemented. `path:<repo-relative>@<blob-sha7>` pins a STANDING
# property to the surface it was observed against; `commit:<sha>` pins a dated
# measurement to the immutable event that produced it. Adding a kind here without
# a branch below is what the unknown-kind refusal exists to prevent.
KNOWN_DEPENDENCY_KINDS = frozenset({"path", "commit"})


def dependency_verdicts(claims: list[dict]) -> list[dict]:
    """A claim is STALE_DEPENDENCY when a surface it was pinned to has moved."""
    pinned = [c for c in claims if c.get("depends_on")]
    if len(pinned) < MIN_PINNED_CLAIMS:
        raise InstrumentFailure(
            f"{len(pinned)} claims carry depends_on, floor is {MIN_PINNED_CLAIMS}. "
            "A dependency sweep over an unpinned corpus reports zero stale "
            "claims because it examined none -- that is not a clean bill."
        )
    verdicts = []
    for c in claims:
        for dep in c.get("depends_on") or []:
            # An unrecognised kind used to be skipped silently, which made a
            # typo (`paht:`) and a declared-but-unbuilt kind read exactly like an
            # enforced pin. A pin that looks enforced and is not is the failure
            # class this whole reconciler exists to close, so an unknown kind is
            # now an instrument failure rather than a quiet pass.
            kind = dep.split(":", 1)[0] if ":" in dep else dep
            if kind not in KNOWN_DEPENDENCY_KINDS:
                raise InstrumentFailure(
                    f"{c.get('id')}: depends_on kind {kind!r} is not implemented. "
                    f"Known kinds: {sorted(KNOWN_DEPENDENCY_KINDS)}. Declaring a "
                    "pin the sweep cannot evaluate is worse than carrying none."
                )
            if kind == "commit":
                # A dated measurement does not depend on a living surface: what
                # was observed on a given day stays observed however the code
                # moves afterwards. Pinning such a claim to a mutable blob makes
                # it permanently, falsely stale -- and a gate nobody can green is
                # a gate that gets switched off. A commit sha is immutable, so
                # this pin can only fail when the sha is wrong, which is the only
                # way a historical claim's dependency CAN be wrong.
                sha = dep[len("commit:"):].strip()
                if not sha:
                    raise InstrumentFailure(
                        f"{c.get('id')}: depends_on entry {dep!r} names no commit")
                try:
                    git("rev-parse", "--verify", f"{sha}^{{commit}}")
                except InstrumentFailure:
                    verdicts.append({"id": c["id"], "verdict": "STALE_DEPENDENCY",
                                     "detail": f"commit {sha} does not resolve"})
                continue
            surface, _, pinned = dep[len("path:"):].rpartition("@")
            if not surface or not pinned:
                raise InstrumentFailure(
                    f"{c.get('id')}: depends_on entry {dep!r} carries no @<sha> pin"
                )
            try:
                now = git("rev-parse", f"HEAD:{surface}").strip()
            except InstrumentFailure:
                verdicts.append({"id": c["id"], "verdict": "STALE_DEPENDENCY",
                                 "detail": f"{surface} no longer exists at HEAD"})
                continue
            if not now.startswith(pinned):
                verdicts.append({"id": c["id"], "verdict": "STALE_DEPENDENCY",
                                 "detail": f"{surface} {pinned} -> {now[:7]}"})
    return verdicts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=DEFAULT_SINCE)
    ap.add_argument("--propose", metavar="PATH")
    args = ap.parse_args()

    try:
        claims = load_claims()
        material, skipped = material_events(args.since)
        seen = referenced_shas(claims)
        uncovered = [e for e in material if e["sha"][:7] not in seen]
        stale = dependency_verdicts(claims)
    except InstrumentFailure as exc:
        print(f"INSTRUMENT_FAILED: {exc}")
        return 2

    print(f"# GSD X claim reconciliation  ({len(claims)} claims, {args.since}..HEAD)\n")
    print(f"  material evidence events : {len(material)}")
    print(f"  skipped (not evidence)   : {len(skipped)}")
    print(f"  covered by a claim       : {len(material) - len(uncovered)}")
    print(f"  UNCOVERED_EVIDENCE       : {len(uncovered)}")
    print(f"  STALE_DEPENDENCY         : {len(stale)}\n")

    for e in skipped:
        print(f"  skip  {e['sha'][:7]}  {e['why']:<28}  {e['subject'][:52]}")
    print()
    for e in uncovered:
        print(f"  UNCOVERED  {e['sha'][:7]}  {e['subject'][:64]}")
    for v in stale:
        print(f"  STALE      {v['id']:<10} {v['detail']}")

    if args.propose:
        lines = [
            "# Candidate claims — proposed, not asserted",
            "",
            "Each row below is a material evidence event with no claim covering it.",
            "Whether it deserves a claim, and what that claim says, is a semantic",
            "judgement this tool does not make.",
            "",
        ]
        lines += [f"- `{e['sha'][:7]}` — {e['subject']}" for e in uncovered]
        Path(args.propose).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n  proposed {len(uncovered)} candidate rows -> {args.propose}")

    total = len(uncovered) + len(stale)
    print(f"\nGSDX_RECONCILE: {total} finding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
