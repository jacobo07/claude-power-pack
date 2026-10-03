#!/usr/bin/env python3
"""agent_bench -- S3 quality benchmark for agent capability virtualization.

Spec: vault/specs/agent-capability-virtualization.md, slice S3. Frozen fixtures x three
arms (monolithic / virtual / crippled) x n=1, same carrier model (sonnet), each a REAL
dispatch through tools/agent_carrier_run.py.

  python tools/agent_bench.py run   [--set v1|v2] [--out-dir DIR] [--model sonnet]   # resumable
  python tools/agent_bench.py score [--set v1|v2] [--out-dir DIR]                     # verdict

Sets. v1 (vault/benchmarks/agent_virtualization) was VOID on 2026-10-01: its defects were
generic knowledge the inline core already reached. v2 (.../agent_virtualization_v2) seeds
only defects whose doctrine lives in a deep page. Each set carries its own fixtures,
answer_key.json and MANIFEST.json; the fixture list is the answer key's.

PRE-REGISTERED SCORING (committed before the first v1 run, 7ea0a9e, and unchanged since;
the spec fixed the verdict rule but not these two definitions):

  finding block  one numbered item (`N.` or `N)` at line start, <=3 spaces indent) inside the
                 reply's `### Gaps` section, running to the next item or `#` heading. The
                 "Audit clean items" section never counts. No `### Gaps` heading -> the whole
                 reply (minus clean items) is scanned, so a format slip costs nothing in recall.
  HIT            a seeded defect is hit when ONE block matches its anchor AND its concept
                 regex (answer_key.json, case-insensitive). One block may hit several.
  false positive a block that hits no seeded defect. Genuine extra gaps count too; the rule is
                 comparative (virtual FP <= monolithic FP + 1), so they cost every arm alike.

  per fixture    arm X non-inferior to monolithic iff hits_X >= hits_mono - 1 AND
                 fp_X <= fp_mono + 1 (spec S3).
  verdict        virtual non-inferior on every fixture AND crippled regressing on >= 1
                 -> NON_INFERIOR. Virtual failing any fixture -> REGRESSION. Crippled never
                 regressing -> VOID (the instrument cannot see a loss). Any run not MEASURED
                 or any MANIFEST hash mismatch -> INCONCLUSIVE. INCONCLUSIVE and VOID block S4.
  cost           seconds per run are reported beside the verdict and never enter it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETS = {"v1": ROOT / "vault" / "benchmarks" / "agent_virtualization",
        "v2": ROOT / "vault" / "benchmarks" / "agent_virtualization_v2"}
BENCH = SETS["v1"]
ARMS = ("monolithic", "virtual", "crippled")
SPEC_ID = "oneshot-architect-auditor"
MISSION_HEAD = "Audit this plan. Output the ULTRA gap list."
ITEM_RE = re.compile(r"(?m)^ {0,3}\d{1,2}[.)]\s")
GAPS_RE = re.compile(r"(?mi)^#{2,4}\s*gaps\b.*$")
HEADING_RE = re.compile(r"(?m)^#{1,6}\s")
CLEAN_RE = re.compile(r"(?mi)^#{1,6}\s.*\bclean items?\b.*$")


def answer_key(bench: Path = BENCH) -> dict:
    return json.loads((bench / "answer_key.json").read_text(encoding="utf-8"))["fixtures"]


def fixtures_of(bench: Path = BENCH) -> tuple:
    return tuple(sorted(answer_key(bench)))


FIXTURES = fixtures_of(BENCH)


def content_sha256(p: Path) -> str:
    """sha256 of the file with CRLF folded to LF. A freeze is about CONTENT: measured 2026-10-01,
    the v2 manifest hashed the laptop's autocrlf bytes of spec.json, and the Linux checkout of the
    SAME git blob (1411d55) failed the check on GEX44. Line endings are the host's, not the content's."""
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def manifest_mismatches(root: Path = ROOT, bench: Path = BENCH) -> list[str]:
    """Every frozen file whose content hash differs from the set's MANIFEST.json. Empty = scoring allowed."""
    man = json.loads((bench / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = []
    for rel, want in man["files"].items():
        p = root / rel
        got = content_sha256(p) if p.is_file() else "MISSING"
        if got != want:
            bad.append(f"{rel}: {got[:12]} != {want[:12]}")
    return bad


def finding_blocks(reply: str) -> list[str]:
    text = reply or ""
    clean = CLEAN_RE.search(text)
    if clean:   # "Audit clean items" are what the auditor VERIFIED, never findings
        rest = text[clean.end():]
        nxt = HEADING_RE.search(rest)
        text = text[:clean.start()] + (rest[nxt.start():] if nxt else "")
    m = GAPS_RE.search(text)
    if m:
        text = text[m.end():]
        nxt = HEADING_RE.search(text)
        text = text[:nxt.start()] if nxt else text
    starts = [x.start() for x in ITEM_RE.finditer(text)]
    return [text[s: starts[i + 1] if i + 1 < len(starts) else len(text)].strip()
            for i, s in enumerate(starts)]


def score_reply(reply: str, defects: list[dict]) -> dict:
    blocks = finding_blocks(reply)
    hits, block_hit = set(), [False] * len(blocks)
    for d in defects:
        a, c = re.compile(d["anchor"], re.I), re.compile(d["concept"], re.I)
        for i, b in enumerate(blocks):
            if a.search(b) and c.search(b):
                hits.add(d["id"])
                block_hit[i] = True
    return {"blocks": len(blocks), "hits": sorted(hits), "n_hits": len(hits), "n_defects": len(defects),
            "fp": sum(1 for h in block_hit if not h),
            "missed": sorted(d["id"] for d in defects if d["id"] not in hits)}


def non_inferior(arm: dict, mono: dict) -> bool:
    return arm["n_hits"] >= mono["n_hits"] - 1 and arm["fp"] <= mono["fp"] + 1


def verdict(scores: dict, manifest_bad: list[str], fixtures: tuple = FIXTURES) -> dict:
    """scores[fixture][arm] = score_reply(...) or {"status": <not MEASURED>}."""
    if manifest_bad:
        return {"verdict": "INCONCLUSIVE", "why": ["manifest mismatch"] + manifest_bad}
    missing = [f"{f}/{a}" for f in fixtures for a in ARMS
               if "n_hits" not in (scores.get(f) or {}).get(a, {})]
    if missing:
        return {"verdict": "INCONCLUSIVE", "why": [f"not measured: {m}" for m in missing]}
    per = {f: {a: non_inferior(scores[f][a], scores[f]["monolithic"]) for a in ("virtual", "crippled")}
           for f in fixtures}
    crippled_regressed = any(not per[f]["crippled"] for f in fixtures)
    virtual_ok = all(per[f]["virtual"] for f in fixtures)
    if not crippled_regressed:
        v = "VOID"
    else:
        v = "NON_INFERIOR" if virtual_ok else "REGRESSION"
    return {"verdict": v, "per_fixture": per, "crippled_regressed": crippled_regressed}


def mission_for(fixture: str, bench: Path = BENCH) -> str:
    return MISSION_HEAD + "\n\n" + (bench / "fixtures" / fixture).read_text(encoding="utf-8")


def run_name(fixture: str, arm: str) -> str:
    return f"{fixture[:2]}-{arm}.json"


def cmd_run(bench: Path, out_dir: Path, model: str) -> int:
    bad = manifest_mismatches(bench=bench)
    if bad:
        print("REFUSED: frozen benchmark files changed:\n  " + "\n  ".join(bad))
        return 2
    sys.path.insert(0, str(ROOT / "tools"))
    import agent_carrier_run as R  # noqa: E402
    from modules.capability_runtime import agent_spec as A  # noqa: E402
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in fixtures_of(bench):
        for arm in ARMS:   # arms interleaved per fixture, so drift over the session hits all alike
            dest = out_dir / run_name(f, arm)
            if dest.is_file() and json.loads(dest.read_text(encoding="utf-8")).get("status") == "MEASURED":
                print(f"skip {dest.name} (already MEASURED)", flush=True)
                continue
            t0 = time.time()
            rec = R.run(SPEC_ID, mission_for(f, bench), arm, model, "haiku", 900, A.current_state_version(ROOT),
                        purpose="benchmark")      # ACV C6: real runs, real tokens, tagged as an experiment
            rec.update({"fixture": f, "arm": arm, "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            dest.write_text(json.dumps(rec, indent=1), encoding="utf-8")   # durable as it goes
            print(f"{dest.name}: {rec.get('status')} {round(time.time() - t0)}s "
                  f"reply={rec.get('returned_chars')} pages={rec.get('pages_read')}", flush=True)
    return 0


def cmd_score(bench: Path, out_dir: Path) -> int:
    key = answer_key(bench)
    fixtures = fixtures_of(bench)
    scores: dict = {}
    for f in fixtures:
        for arm in ARMS:
            p = out_dir / run_name(f, arm)
            rec = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"status": "ABSENT"}
            s = (score_reply(rec.get("reply", ""), key[f])
                 if rec.get("status") == "MEASURED" and rec.get("reply")
                 else {"status": rec.get("status", "ABSENT")})
            s.update({"seconds": rec.get("seconds"), "pages_read": rec.get("pages_read")})
            scores.setdefault(f, {})[arm] = s
    v = verdict(scores, manifest_mismatches(bench=bench), fixtures)
    report = {"set": bench.name, "verdict": v, "scores": scores}
    (out_dir / "score.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for f in fixtures:
        for arm in ARMS:
            s = scores[f][arm]
            print(f"{f[:2]} {arm:<10} " + (f"hits={s['n_hits']}/{s['n_defects']} fp={s['fp']} blocks={s['blocks']} "
                                           f"{s['seconds']}s pages={len(s['pages_read'] or [])} missed={s['missed']}"
                                           if "n_hits" in s else f"status={s['status']}"))
    print(f"VERDICT {v['verdict']}  {json.dumps({k: v[k] for k in v if k != 'verdict'})}")
    return 0 if v["verdict"] == "NON_INFERIOR" else 1


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("run", "score"))
    ap.add_argument("--set", default="v1", choices=sorted(SETS))
    ap.add_argument("--out-dir")
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT))
    bench = SETS[a.set]
    out = Path(a.out_dir) if a.out_dir else bench / "runs" / ("s3" if a.set == "v1" else "s3b")
    return cmd_run(bench, out, a.model) if a.cmd == "run" else cmd_score(bench, out)


if __name__ == "__main__":
    sys.exit(main())
