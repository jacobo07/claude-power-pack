"""Report the W11 prose declaration channel. Computed and reported, never active.

    python tools/ucr_cif_prose.py                 estate summary + the harmed stratum
    python tools/ucr_cif_prose.py --owner X       every artifact of one owner
    python tools/ucr_cif_prose.py --artifact P    every edge of one artifact, typed

The channel is not consulted by `adjudicate`, so no disposition moves, and it
reaches ranking only through `structural_projection`, which is behind
`STRUCTURAL_RANKING_ENABLED` and is False. This prints evidence; it promotes
nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from modules.ucr_cif import prose_authority as PA  # noqa: E402

HARMED = "modules/governance-overlay"


def _fmt_classes(edges: dict) -> str:
    return " ".join(f"{k}={len(v)}" for k, v in sorted(edges.items())) or "-"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--owner", default="")
    ap.add_argument("--artifact", default="")
    ap.add_argument("--json", default="")
    args = ap.parse_args(argv)

    t0 = time.perf_counter()
    edges = PA.build_edges(_ROOT)
    build_ms = 1000.0 * (time.perf_counter() - t0)
    t1 = time.perf_counter()
    decls = PA.prose_declarations(_ROOT, edges)
    decl_ms = 1000.0 * (time.perf_counter() - t1)
    cov = PA.coverage(_ROOT, edges)

    print("== PROSE DECLARATION CHANNEL (W11, reported only) ==")
    print(f"  build_edges                {build_ms:8.0f} ms over "
          f"{cov['artifacts']} prose artifacts")
    print(f"  prose_declarations         {decl_ms:8.1f} ms")
    print(f"  artifacts with CONSUMER    {cov['artifacts_with_consumer_edge']}")
    print(f"  artifacts declaring        {cov['artifacts_declaring']}")
    print(f"  blocked by lifecycle       {cov['artifacts_blocked_by_lifecycle']}")
    print(f"  declared terms             {len(decls)}")
    print("  edges by provenance class")
    for k, n in sorted(cov["edges_by_class"].items(), key=lambda x: -x[1]):
        mark = "  <- promotes" if k in PA.PROMOTING else ""
        print(f"      {k:<18} {n:6d}{mark}")

    owners = defaultdict(set)
    for term, os_ in decls.items():
        for o in os_:
            owners[o].add(term)
    print(f"\n== OWNERS EARNING DECLARATIONS ({len(owners)}) ==")
    for o, terms in sorted(owners.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {len(terms):5d}  {o}")

    if args.artifact:
        meta = edges.get(args.artifact)
        if meta is None:
            print(f"\nno such prose artifact: {args.artifact}")
            return 1
        print(f"\n== {args.artifact} ==")
        print(f"  owner                {meta['owner']}")
        print(f"  declaration_capable  {meta['declaration_capable']}")
        print(f"  declares             {len(meta['declares'])} terms")
        for cls in sorted(meta["edges"]):
            for ref in meta["edges"][cls]:
                print(f"  {cls:<18} <- {ref}")
        return 0

    target = args.owner or HARMED
    print(f"\n== {target} ==")
    any_seen = False
    for rel, meta in sorted(edges.items()):
        if meta["owner"] != target:
            continue
        any_seen = True
        cons = len(meta["edges"].get(PA.CONSUMER, []))
        verdict = ("DECLARES" if cons and meta["declaration_capable"]
                   and meta["declares"] else "silent")
        print(f"  {rel.split('/')[-1]:<26} {verdict:<9} "
              f"declares={len(meta['declares']):<4} {_fmt_classes(meta['edges'])}")
    if not any_seen:
        print(f"  no prose artifacts under {target}")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(
            {"coverage": cov, "declarations": decls,
             "build_ms": round(build_ms, 1)}, indent=1), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
