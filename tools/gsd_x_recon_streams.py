"""Build one OBSERVED claim per stream from the recon inventory. Refuses on any unmapped event.

Usage: python tools/gsd_x_recon_inventory.py recon.json
       python tools/gsd_x_recon_streams.py recon.json out.jsonl
Exit 2 names every event whose scope no stream owns; add it to STREAMS, never to a catch-all.
Rows are written to out.jsonl for review; appending them to claims.jsonl is a separate step."""
import collections, json, sys
from pathlib import Path

PP = Path(r"C:\Users\User\.claude\skills\claude-power-pack")
sys.path.insert(0, str(PP / "tools"))
import gsd_x_claim_reconcile as rc  # noqa: E402

STREAMS = {
    "S01": ("GSD X mission itself (goal spine, mission gate, structured facts, reconstruction)",
            {"gsd-x", "gsd-x-mutation", "goal", "goal-log", "goal-epoch", "goal-sweep",
             "goal-long-run", "repo-identity"}),
    "S02": ("UWCP continuity plane and its assimilated primitives (lease, trace context, provider routing, history check, inference bench, done-gate evidence class)",
            {"uwcp", "uwcp-assimilation", "uwcp-tla", "uwcp-corpus", "lease", "history-check",
             "trace-context", "provider-routing", "inference-bench", "done-gate", "liveness"}),
    "S03": ("Unattended long runs (/cpp-gsd-long, gsd_mission, epochs, walls, sweep, night worker, delivery ledger)",
            {"gsd-mission", "gsd-long", "cpp-gsd-long", "gsd-long-run", "mission", "mission-wall",
             "mission-watchdog", "test-gsd-mission", "gsd-epoch", "epoch", "gsd-sweep", "sweep",
             "breaker", "night", "ledger", "marker", "cert", "certification", "mission-continuity",
             "spec", "auto-compact", "fix", "drill", "review", "inbox", "docs", "backlog"}),
    "S04": ("Milestone v1 GSD planning workstream (two-pane exactness, phases 1-5, acceptance gate)",
            set()),
    "S05": ("CRO GEX44 workstream and the rule-relocation ablation (P1-P5, P3 moves, context rent)",
            {"cro", "cro-p3", "cro-01", "phase-2", "phase-3", "phase-4", "phase-5", "skills",
             "context-rent", "01-01", "01-02", "02-01", "03-01", "04-01", "05-01", "02", "03", "05"}),
    "S06": ("Torre Universal / UCR-CIF and the capability runtime (surface architecture, family scan, inheritance)",
            {"tower", "ucr-cif", "torre-universal", "tools", "inheritance", "surface_architecture",
             "surface", "capability", "capability_runtime", "done_gate"}),
    "S07": ("Assimilation programme (Genesis Suite, Context Budget, cognitive-resource OS, UACF)",
            {"assim", "assimilation", "cognitive-resource-os", "uacf"}),
    "S08": ("Interactive context rollover and pane lifecycle (/kclear-/kresume capsule, 45 % watchdog, kclaude, statusline)",
            {"rollover", "watchdog", "kclaude", "statusline"}),
    "S09": ("Hook chain and dispatcher hygiene (zero-issue gate, graph-first, skill advisor, deep research, agent packs, test isolation)",
            {"hooks", "dispatcher", "zero-issue-gate", "graph_first_gate", "skill-advisor",
             "deep-research", "agent-packs", "playwright", "iso", "tests"}),
    "S10": ("Product demo module", {"product-demo"}),
    "S11": ("KEOS-Qwen", {"keos-qwen"}),
    "S12": ("Token economics (TIS observed usage, telemetry, pricing, budget runway, TCO, routing)",
            {"tis", "token-telemetry", "pricing", "budget", "tco", "token-optimizer", "routing"}),
    "S13": ("Doctrine and knowledge (UKDL rows, vault lessons, new skills)",
            {"ukdl", "ukdl-candidates", "vault", "knowledge"}),
    "S14": ("CDIO motion grammar (visual patterns, motion resolver, CDIO hook, V-MGRAM gate)",
            {"visual-patterns", "cdio", "cdio-hook", "motion-grammar"}),
    "S15": ("Power Pack standing self-evaluation (pp-eval)", {"pp-eval"}),
}
# .planning phase scopes are split by date: the v1 milestone ran 09-20..09-22, CRO from 09-28.
PLANNING = {"01", "02", "03", "04", "05", "02,03", "phase 5", "gate", "roadmap", "state"}
CRO_START = "2026-09-27"


def stream_of(e):
    s = e["scope"]
    if s == "unscoped":
        subj = e["subject"].lower()
        if subj.startswith("gsd-x"):
            return "S01"
        if subj.startswith(("phase", "milestone")):
            return "S04"
        if subj.startswith(("cro", "skills+hooks")):
            return "S05"
        if "mobile-game-wii-port" in subj:
            return "S13"
        if e["sha"] in {"b75994e", "15bcdbe", "033f957"}:
            return "S03"
        return None
    if s in PLANNING:
        return "S05" if e["date"] >= CRO_START else "S04"
    for sid, (_, scopes) in STREAMS.items():
        if s in scopes:
            return sid
    return None


def main():
    groups = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    claims = rc.load_claims()
    pins = collections.defaultdict(set)
    for c in claims:
        for d in c.get("depends_on") or []:
            if d.startswith("path:"):
                pins[d[5:].rpartition("@")[0]].add(c["id"])
    head = rc.git("rev-parse", "--short=7", "HEAD").strip()
    by = collections.defaultdict(list)
    unmapped = []
    for es in groups.values():
        for e in es:
            sid = stream_of(e)
            (by[sid].append(e) if sid else unmapped.append(e))
    if unmapped:
        for e in unmapped:
            print("UNMAPPED", e["sha"], e["scope"], e["subject"][:80])
        return 2
    total = sum(len(v) for v in by.values())
    order = {sha[:7]: i for i, sha in enumerate(
        rc.git("rev-list", "--reverse", f"{rc.DEFAULT_SINCE}..HEAD").split())}
    rows = []
    for sid in sorted(by):
        es = sorted(by[sid], key=lambda e: order[e["sha"]])
        d0, d1 = min(e["date"] for e in es), max(e["date"] for e in es)
        span = f"on {d0}" if d0 == d1 else f"between {d0} and {d1}"
        title = STREAMS[sid][0]
        hits = collections.defaultdict(set)
        for e in es:
            for f in e["files"]:
                if f in pins:
                    hits[f].add(e["sha"])
        if hits:
            hit_txt = "; ".join(f"{f} by {', '.join(sorted(s))} (pins {', '.join(sorted(pins[f]))})"
                                for f, s in sorted(hits.items()))
            pin_sentence = (f"{sum(1 for e in es if any(f in pins for f in e['files']))} of them "
                            f"touched a surface a GSD X claim is path-pinned to: {hit_txt}.")
        else:
            pin_sentence = "None of them touched a surface any GSD X claim is path-pinned to."
        rows.append({
            "id": f"GSDX-{sid}",
            "state": "OBSERVED",
            "date": "2026-09-30",
            "claim": (f"Stream '{title}' landed {len(es)} material commits {span} "
                      f"that no GSD X claim spoke about. {pin_sentence}"),
            "evidence": ("tools/gsd_x_recon_inventory.py over a30f39f.." + head + ", grouped by commit "
                         "scope into streams; commits: " + " ".join(e["sha"] for e in es)),
            "instrument": ("the reconciler's own materiality predicate (imported by the inventory) plus a "
                           "stream map that refuses any unmapped event; pin intersection is exact path "
                           "equality against every path: depends_on entry"),
            "depends_on": [f"commit:{es[-1]['sha']}"],
            "note": ("Per-stream coarsening of the per-event precedent in 977223e. This row records that "
                     "the stream exists and what it touched; it asserts nothing about the correctness of "
                     "the work, which is owned by that stream's own specs and gates."),
        })
    Path(sys.argv[2]).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                                 encoding="utf-8")
    for sid in sorted(by):
        print(f"{sid} {len(by[sid]):4d}  {STREAMS[sid][0][:70]}")
    print(f"streams={len(by)} events={total} head={head}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
