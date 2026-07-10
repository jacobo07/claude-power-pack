"""Universal Meta-Systems Runtime -- CLI.

Subcommands:
  list                     the seven + the loop (no corpus dataset read)
  show   MS-N              summarize one meta-system (corpus doctrine)
  apply  MS-N              interpret one meta-system for THIS repo's noun-map
  loop                    interpret all seven (loop order) for this repo
  audit                   gap audit == apply MS-6 (Absence Engine) to this repo
  propose                 PROPOSE candidate nouns from the repo's CLAUDE.md

The runtime interprets the read-only corpus; it never reimplements a meta-system
and never writes to the corpus. Findings can be published to the PM-03 bus
(fail-open: bus absent -> a visible note, never a crash).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import LOOP_ORDER, CORPUS_PINNED_SHA
from . import corpus_parser as cp
from .executor import build_plan, plan_to_dict, render_plan
from .loop import run_loop
from .noun_map import NounMap, load_noun_map, propose_candidates

# Navigational one-liners (documentation, NOT the meta-system's operational
# logic -- the ops/gates/pipelines are always read from the corpus, never here).
ONE_LINERS = {
    "MS-0": "Provenance Substrate -- reproducibility-and-lineage by construction (floor).",
    "MS-1": "Composition Fabric -- assemble systems from published contracts.",
    "MS-2": "Intent Compiler -- intent -> concern planes -> contracts -> assembled system.",
    "MS-3": "Compounding Substrate -- shared frontier; each build cheaper than the last.",
    "MS-4": "Capital Ledger -- book non-code capital as first-class assets.",
    "MS-5": "Evolution & Integrity Fabric -- evolve forever, safely, without drift.",
    "MS-6": "Absence Engine -- model what's missing/dormant; route it to be filled.",
}

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_NO_CORPUS = 2


def _resolve_corpus(arg: str | None, repo: Path) -> Path | None:
    if arg:
        p = Path(arg)
        return p if (p / "MASTER_INDEX.md").is_file() else None
    return cp.find_corpus_root(repo)


def _publish(repo: Path, plans, sid: str):
    """Publish one finding per plan to PM-03. Returns published count, or None
    if the bus is unavailable. Never raises."""
    try:
        pp_root = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(pp_root / "modules" / "parallel_mesh"))
        import pm_03_bus  # type: ignore
    except Exception:  # noqa: BLE001 -- bus optional, fail-open
        return None
    findings = [{
        "topic": f"meta-system:{p.ms_id}",
        "claim": (f"{p.ms_id} interpreted for this repo: {len(p.ops)} actions, "
                  f"{len(p.gates)} invariants (noun-map={p.noun_map_source})"),
        "evidence": p.source_path,
    } for p in plans]
    try:
        return pm_03_bus.publish_session_findings(str(repo), findings, sid=sid)
    except Exception:  # noqa: BLE001
        return None


def _emit(plans, as_json: bool) -> None:
    if as_json:
        payload = [plan_to_dict(p) for p in plans]
        print(json.dumps(payload if len(payload) != 1 else payload[0],
                         ensure_ascii=False, indent=2))
    else:
        print(("\n\n" + "=" * 70 + "\n\n").join(render_plan(p) for p in plans))


def _add_common(sp) -> None:
    sp.add_argument("--repo", default=".", help="repo root (default: cwd)")
    sp.add_argument("--corpus", default=None, help="corpus root (default: discover)")
    sp.add_argument("--json", action="store_true", help="emit JSON")
    sp.add_argument("--publish", action="store_true", help="publish findings to PM-03")
    sp.add_argument("--sid", default="", help="publishing pane/session id")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cpp-meta-systems",
                                 description="Universal Meta-Systems Runtime")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="the seven + the loop")

    p_show = sub.add_parser("show", help="summarize one meta-system")
    p_show.add_argument("ms", help="MS-0 .. MS-6")
    _add_common(p_show)

    p_apply = sub.add_parser("apply", help="interpret one meta-system for this repo")
    p_apply.add_argument("ms", help="MS-0 .. MS-6")
    _add_common(p_apply)

    p_loop = sub.add_parser("loop", help="interpret all seven for this repo")
    p_loop.add_argument("--stop-after", type=int, default=None)
    _add_common(p_loop)

    p_audit = sub.add_parser("audit", help="gap audit (== apply MS-6)")
    _add_common(p_audit)

    p_prop = sub.add_parser("propose", help="propose candidate nouns from CLAUDE.md")
    p_prop.add_argument("--repo", default=".")
    p_prop.add_argument("--top", type=int, default=None)

    args = ap.parse_args(argv)

    if args.cmd == "list":
        print("Universal Meta-Systems (corpus pinned @ " + CORPUS_PINNED_SHA + ")\n")
        for ms in ("MS-0", "MS-1", "MS-2", "MS-3", "MS-4", "MS-5", "MS-6"):
            print(f"  {ms}  {ONE_LINERS[ms]}")
        print("\nClosed loop: " + " -> ".join(LOOP_ORDER))
        return EXIT_OK

    if args.cmd == "propose":
        repo = Path(args.repo).resolve()
        cands = (propose_candidates(repo, args.top) if args.top
                 else propose_candidates(repo))
        if not cands:
            print(f"[propose] no CLAUDE.md found under {repo}; "
                  f"declare .pp_meta_systems.json manually.")
            return EXIT_OK
        print(f"[propose] candidate local nouns from {repo}\\CLAUDE.md "
              f"(map a universal noun onto one of these; this is a proposal, "
              f"not a mapping):")
        for c in cands:
            print(f"  - {c}")
        return EXIT_OK

    repo = Path(args.repo).resolve()
    corpus = _resolve_corpus(args.corpus, repo)
    if corpus is None:
        print("[error] meta-systems corpus not found (env "
              "UNIVERSAL_META_SYSTEMS_CORPUS / sibling dir / Owner default). "
              "The seven are usable conceptually from the module docs, but the "
              "runtime needs the corpus datasets.", file=sys.stderr)
        return EXIT_NO_CORPUS

    if args.cmd == "show":
        plan = build_plan(args.ms, NounMap(source="generic"), corpus)
        _emit([plan], args.json)
        return EXIT_OK

    if args.cmd == "apply":
        nm = load_noun_map(repo)
        plan = build_plan(args.ms, nm, corpus)
        _emit([plan], args.json)
        if args.publish:
            n = _publish(repo, [plan], args.sid)
            print(f"\n[PM-03] {'unavailable' if n is None else str(n) + ' published'}")
        return EXIT_OK

    if args.cmd == "loop":
        nm = load_noun_map(repo)
        plans = run_loop(nm, corpus, stop_after=args.stop_after)
        _emit(plans, args.json)
        if args.publish:
            n = _publish(repo, plans, args.sid)
            print(f"\n[PM-03] {'unavailable' if n is None else str(n) + ' published'}")
        return EXIT_OK

    if args.cmd == "audit":
        nm = load_noun_map(repo)
        plan = build_plan("MS-6", nm, corpus)
        print(f"# GAP AUDIT for {repo}\n# (the Absence Engine MS-6 applied to this "
              f"repo -- each ACTION is a gap-detection duty, each INVARIANT a "
              f"gate the audit must honor)\n")
        _emit([plan], args.json)
        if args.publish:
            n = _publish(repo, [plan], args.sid)
            print(f"\n[PM-03] {'unavailable' if n is None else str(n) + ' published'}")
        return EXIT_OK

    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
