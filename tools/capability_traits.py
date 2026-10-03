"""CLI over modules.capability_runtime.trait_scan. Produces the structural trait cache.

The out-of-band entry point of the trait producer (UCEP Phase 2, audit G4). The producer
walks a repository, which costs 0.3 to 48 seconds on this estate, so it never runs inside a
hook chain with a latency deadline: 815 measured abandonments of the prompt chain showed
there is no safe hook lane (the same decision `tools/tower_capsule.py` records). The prompt
path only READS the cache this file writes (`archetypes.read_traits`). Run it from a command,
a scheduled task, or by hand. Hosting it on a schedule is Owner step O-1
(`.planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-OWNER-QUEUE.md`);
this file never schedules or registers anything.

    python tools/capability_traits.py <root> [--force]    produce one repository's cache
    python tools/capability_traits.py --all [--force]     one cache per estate project
    python tools/capability_traits.py --show <root>       print what the reader sees

`<root>` must be an absolute path to an existing directory: the current directory is never
consulted. Unless `--force`, a repository that is unchanged within a day is SKIPPED (the stored
document is left as it was).

  exit 0  produced, skipped or shown
  exit 1  a production FAILED (one root, or at least one repository under --all)
  exit 2  root unresolvable (nothing written), or an argument not understood (usage printed)

Every production run appends one row to `<state dir>/traits_production.jsonl`, success
included. A scheduled run has no console (pythonw): without that row, "the task ran and
produced 42 caches" and "the task never ran" look the same, because every cache simply goes
STALE.
"""
from __future__ import annotations

import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.capability_runtime import archetypes, trait_scan  # noqa: E402

LEDGER_NAME = "traits_production.jsonl"

USAGE = """usage: capability_traits.py <root> [--force]
       capability_traits.py --all [--force]
       capability_traits.py --show <root>
  <root> is an absolute path to an existing directory"""


def _ledger(row):
    """Append one JSON line to the production ledger. A ledger failure is reported on
    stderr and never fails the run."""
    path = os.path.join(archetypes.default_state_dir(), LEDGER_NAME)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    except OSError as exc:
        print("traits ledger not written: %s" % exc, file=sys.stderr)


def _cut(doc):
    """1 when the document's walk was cut by the file cap or the time budget, else 0."""
    walk = (doc or {}).get("walk") or {}
    return 1 if walk.get("truncated") or walk.get("budget_hit") else 0


def _walk_line(doc):
    walk = (doc or {}).get("walk") or {}
    return "files=%s truncated=%s budget_hit=%s ecosystems=%s" % (
        walk.get("files"), walk.get("truncated"), walk.get("budget_hit"),
        ",".join(walk.get("ecosystems") or ()) or "none")


def _trait_lines(traits):
    for name in archetypes.TRAITS:
        r = traits[name]
        detail = ", ".join(r.get("evidence") or ()) or r.get("reason") or ""
        print("  %-16s %-9s %-9s %s" % (name, r["state"], r["fact_state"], detail))


def produce_one(root, force=False):
    """Produce one repository's cache and print the outcome. Exit code: 0 produced or
    skipped, 1 FAILED, 2 root unresolvable (nothing written, no ledger row)."""
    res = trait_scan.produce(root, force=force)
    outcome = res.get("outcome")
    if outcome == trait_scan.UNRESOLVABLE:
        print("TRAITS UNRESOLVABLE  %s -- %s (an absolute path to an existing directory is required)"
              % (root, res.get("reason")))
        return 2
    doc = res.get("doc") or {}
    print("TRAITS %s" % outcome)
    if outcome == trait_scan.FAILED:
        print("  reason      %s" % res.get("reason"))
    else:
        print("  repo        %s" % doc.get("repo"))
        print("  repo_key    %s" % doc.get("repo_key"))
        print("  cache       %s" % res.get("path"))
        print("  walk        %s" % _walk_line(doc))
        _trait_lines(doc.get("traits") or {})
    _ledger({"ts": time.time(), "mode": "one", "projects": 1, "outcomes": {outcome: 1},
             "truncated": _cut(doc)})
    return 1 if outcome == trait_scan.FAILED else 0


def produce_all(repos=None, force=False):
    """One cache per project. With `repos=None` the estate is enumerated through
    `family_scan.find_repos`, collapsed through `main_repo_of`: produced on the MAIN repo,
    never on the worktree `family_scan` happens to keep as the population's representative,
    because a cache keyed to a worktree is one the main checkout's prompt path never reads.
    An explicit list is produced as given and never triggers the enumeration. Returns 1
    when any production FAILED, else 0."""
    if repos is None:
        if _HERE not in sys.path:
            sys.path.insert(0, _HERE)
        from family_scan import find_repos, main_repo_of      # sibling import, as tower_capsule does
        repos = sorted({main_repo_of(r) for r in find_repos()})
    else:
        repos = list(repos)
    counts, cut = {}, 0
    for repo in repos:
        res = trait_scan.produce(repo, force=force)
        outcome = res.get("outcome", "?")
        counts[outcome] = counts.get(outcome, 0) + 1
        doc = res.get("doc") or {}
        cut += _cut(doc)
        extra = "  %s" % _walk_line(doc) if doc else "  %s" % (res.get("reason") or "")
        print("  %-12s %s%s" % (outcome, repo, extra))
    print()
    print("TRAITS %d  %s" % (len(repos), counts))
    _ledger({"ts": time.time(), "mode": "all", "projects": len(repos), "outcomes": counts,
             "truncated": cut})
    return 1 if trait_scan.FAILED in counts else 0


def show(root):
    """Print what the prompt-path reader sees for `root`. Reads only; writes nothing."""
    if archetypes.subject_root(root) is None:
        print("TRAITS UNRESOLVABLE  %s -- an absolute path to an existing directory is required" % root)
        return 2
    res = archetypes.read_traits(root)
    cache = res["cache"]
    print("TRAITS %s" % cache["state"])
    print("  cache       %s" % cache.get("path"))
    print("  reason      %s" % (cache.get("reason") or "-"))
    if cache.get("produced_at") is not None:
        print("  age         %.1f hours" % ((time.time() - cache["produced_at"]) / 3600.0))
    if cache.get("walk"):
        print("  walk        %s" % _walk_line({"walk": cache["walk"]}))
    _trait_lines(res["traits"])
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    unknown = [a for a in args if a.startswith("--") and a not in ("--all", "--show")]
    if unknown:
        print("unknown argument: %s" % unknown[0])
        print(USAGE)
        return 2
    if args == ["--all"]:
        return produce_all(None, force=force)
    if len(args) == 2 and args[0] == "--show" and not force:
        return show(args[1])
    if len(args) == 1 and not args[0].startswith("--"):
        return produce_one(args[0], force=force)
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main())
