#!/usr/bin/env python3
"""drx_compare.py -- version-agnostic comparison of deep_research runs (DRX U6).

The ledger can only judge runs that HAVE a ledger, so it cannot be the yardstick
between an engine with one and an engine without. This instrument applies one
rule to every run, whatever version produced it:

  For each persisted learning, take its informative numbers (evidence_ledger.
  numbers_in: commas stripped, integers < 10 ignored). Re-fetch every URL the
  report cites (through the same guarded fetch + markdown cascade). The learning
  is NUMBER-SUPPORTED if it carries >= 1 number and every one of them occurs in
  at least one cited page; NUMBER-UNSUPPORTED if any is absent from all of them;
  NO-NUMBER otherwise.

It is a narrow proxy for citation faithfulness (a number can occur in a page
for an unrelated reason, and a correct qualitative claim scores NO-NUMBER), so
it is reported next to its denominators, never as "accuracy". Pages are fetched
at comparison time for every run alike; a page that fails to load is counted.

    python tools/drx_compare.py <run_dir> [<run_dir> ...] [--json out.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP / "modules" / "deep-research"))

import deep_research as dr  # noqa: E402
import evidence_ledger as el  # noqa: E402

_URL_RE = re.compile(r"^- <(https?://[^>]+)>", re.M)
_cache: dict[str, str | None] = {}


def _page_text(url: str) -> str | None:
    if url not in _cache:
        try:
            page = dr.fetch_page(url)
            md, _layer = dr.html_to_markdown(page["html"], max_chars=10**7,
                                             base_url=page.get("final_url", url))
            _cache[url] = md or ""
        except dr.LayerError:
            _cache[url] = None
    return _cache[url]


def _learning_text(labelled: str) -> str:
    """The claim itself: drop the [LEVEL][QUALITY] prefix and trailing labels."""
    body = re.sub(r"^(\[[A-Z_]+\])+\s*", "", labelled)
    return body.split(" — ")[0]


def _runs(run_dir: Path) -> list[dict]:
    out = []
    for report in sorted(run_dir.glob("*.md")):
        if report.name.startswith("RESUMPTION"):
            continue
        text = report.read_text(encoding="utf-8")
        slug = report.stem.split("_", 2)[-1]
        raw = run_dir / f"{slug}.raw.jsonl"
        learnings: list[str] = []
        if raw.exists():
            rows = [json.loads(ln) for ln in raw.read_text(encoding="utf-8").splitlines() if ln.strip()]
            last_header = max((i for i, r in enumerate(rows) if r.get("type") == "run-header"), default=-1)
            learnings = [r["learning"] for r in rows[last_header + 1:] if r.get("type") == "learning"]
        ledger_file = report.with_name(report.stem + ".ledger.json")
        out.append({
            "report": report.name,
            "urls": _URL_RE.findall(text.split("## Run metadata")[0]),
            "learnings": learnings,
            "queries_used": int((re.search(r"\*\*Queries used:\*\* (\d+)", text) or [0, 0])[1]),
            "duration_s": float((re.search(r"\*\*Duration:\*\* ([\d.]+)", text) or [0, 0])[1]),
            "insufficient": "INSUFFICIENT DATA" in text.splitlines()[0] if text else True,
            "ledger": (json.loads(ledger_file.read_text(encoding="utf-8"))["summary"]
                       if ledger_file.exists() else None),
        })
    return out


def score_run(run: dict) -> dict:
    pages = {u: _page_text(u) for u in run["urls"]}
    readable = [t for t in pages.values() if t]
    nums_in_pages = set().union(*(el.numbers_in(t) for t in readable)) if readable else set()
    sup = unsup = nonum = 0
    for ln in run["learnings"]:
        nums = el.numbers_in(_learning_text(ln))
        if not nums:
            nonum += 1
        elif nums <= nums_in_pages:
            sup += 1
        else:
            unsup += 1
    with_num = sup + unsup
    return {
        "report": run["report"], "queries_used": run["queries_used"],
        "duration_s": run["duration_s"], "insufficient": run["insufficient"],
        "learnings": len(run["learnings"]), "cited_urls": len(run["urls"]),
        "urls_unreadable_now": sum(1 for t in pages.values() if not t),
        "number_supported": sup, "number_unsupported": unsup, "no_number": nonum,
        "number_support_rate": round(sup / with_num, 3) if with_num else None,
        "ledger": run["ledger"],
    }


def main(argv: list[str]) -> int:
    out_json = None
    if "--json" in argv:
        i = argv.index("--json")
        out_json = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if not argv:
        print(__doc__)
        return 2
    result = {}
    for d in argv:
        rows = [score_run(r) for r in _runs(Path(d))]
        tot = {k: sum(r[k] for r in rows) for k in (
            "learnings", "cited_urls", "urls_unreadable_now", "number_supported",
            "number_unsupported", "no_number", "queries_used")}
        wn = tot["number_supported"] + tot["number_unsupported"]
        tot["number_support_rate"] = round(tot["number_supported"] / wn, 3) if wn else None
        tot["runs"] = len(rows)
        tot["insufficient_runs"] = sum(1 for r in rows if r["insufficient"])
        tot["duration_s"] = round(sum(r["duration_s"] for r in rows), 1)
        result[d] = {"runs": rows, "total": tot}
        print(f"\n== {d}")
        for r in rows:
            led = r["ledger"] or {}
            print(f"  {r['report'][:60]:60}  learn={r['learnings']:2} urls={r['cited_urls']:2} "
                  f"num_sup={r['number_supported']}/{r['number_supported'] + r['number_unsupported']} "
                  f"nonum={r['no_number']} q={r['queries_used']} t={r['duration_s']}s"
                  + (f" ledger_span_rate={led.get('persisted_verified_span_rate')}" if led else ""))
        print(f"  TOTAL {json.dumps(tot)}")
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
