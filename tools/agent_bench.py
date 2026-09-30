#!/usr/bin/env python3
"""agent_bench -- S3 quality benchmark for agent capability virtualization.

Spec: vault/specs/agent-capability-virtualization.md, slice S3. Three frozen fixtures x
three arms (monolithic / virtual / crippled) x n=1, same carrier model (sonnet), each a
REAL dispatch through tools/agent_carrier_run.py.

  python tools/agent_bench.py run   [--out-dir DIR] [--model sonnet]   # resumable, one JSON per run
  python tools/agent_bench.py score [--out-dir DIR]                     # verdict + per-run table

PRE-REGISTERED SCORING (committed before the first run; the spec fixed the verdict rule but
not these two definitions, so they are fixed here, in code, ahead of any result):

  finding block  one numbered item (`N.` or `N)` at line start, <=3 spaces indent) inside the
                 reply's `### Gaps` section, running to the next item or `#` heading. The
                 "Audit clean items" section never counts. No `### Gaps` heading -> the whole
                 reply is scanned, so a format slip costs nothing in recall.
  HIT            a seeded defect is hit when ONE block matches its anchor AND its concept
                 regex (answer_key.json, case-insensitive). One block may hit several.
  false positive a block that hits no seeded defect. Genuine extra gaps count too; the rule is
                 comparative (virtual FP <= monolithic FP + 1), so they cost every arm alike.

  per fixture    arm X non-inferior to monolithic iff hits_X >= hits_mono - 1 AND
                 fp_X <= fp_mono + 1 (spec S3).
  verdict        virtual NON_INFERIOR on all 3 fixtures AND crippled REGRESSION on >= 1
                 -> NON_INFERIOR. Virtual failing any fixture -> REGRESSION. Crippled never
                 regressing -> VOID (the instrument cannot see a loss). Any run not MEASURED
                 or any MANIFEST hash mismatch -> INCONCLUSIVE. INCONCLUSIVE and VOID block S4.
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
BENCH = ROOT / "vault" / "benchmarks" / "agent_virtualization"
FIXTURES = ("F1-payments-ledger.md", "F2-recovery-daemon.md", "F3-admin-export.md")
ARMS = ("monolithic", "virtual", "crippled")
SPEC_ID = "oneshot-architect-auditor"
MISSION_HEAD = "Audit this plan. Output the ULTRA gap list."
ITEM_RE = re.compile(r"(?m)^ {0,3}\d{1,2}[.)]\s")
GAPS_RE = re.compile(r"(?mi)^#{2,4}\s*gaps\b.*$")
HEADING_RE = re.compile(r"(?m)^#{1,6}\s")
CLEAN_RE = re.compile(r"(?mi)^#{1,6}\s.*\bclean items?\b.*$")


def manifest_mismatches(root: Path = ROOT) -> list[str]:
    """Every frozen file whose sha256 differs from MANIFEST.json. Empty = scoring allowed."""
    man = json.loads((BENCH / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = []
    for rel, want in man["files"].items():
        p = root / rel
        got = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "MISSING"
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
    return {"blocks": len(blocks), "hits": sorted(hits), "n_hits": len(hits),
            "fp": sum(1 for h in block_hit if not h),
            "missed": sorted(d["id"] for d in defects if d["id"] not in hits)}


def non_inferior(arm: dict, mono: dict) -> bool:
    return arm["n_hits"] >= mono["n_hits"] - 1 and arm["fp"] <= mono["fp"] + 1


def verdict(scores: dict, manifest_bad: list[str]) -> dict:
    """scores[fixture][arm] = score_reply(...) or {"status": <not MEASURED>}."""
    if manifest_bad:
        return {"verdict": "INCONCLUSIVE", "why": ["manifest mismatch"] + manifest_bad}
    missing = [f"{f}/{a}" for f in FIXTURES for a in ARMS
               if "n_hits" not in (scores.get(f) or {}).get(a, {})]
    if missing:
        return {"verdict": "INCONCLUSIVE", "why": [f"not measured: {m}" for m in missing]}
    per = {f: {a: non_inferior(scores[f][a], scores[f]["monolithic"]) for a in ("virtual", "crippled")}
           for f in FIXTURES}
    crippled_regressed = any(not per[f]["crippled"] for f in FIXTURES)
    virtual_ok = all(per[f]["virtual"] for f in FIXTURES)
    if not crippled_regressed:
        v = "VOID"
    else:
        v = "NON_INFERIOR" if virtual_ok else "REGRESSION"
    return {"verdict": v, "per_fixture": per, "crippled_regressed": crippled_regressed}


def mission_for(fixture: str) -> str:
    return MISSION_HEAD + "\n\n" + (BENCH / "fixtures" / fixture).read_text(encoding="utf-8")


def cmd_run(out_dir: Path, model: str) -> int:
    bad = manifest_mismatches()
    if bad:
        print("REFUSED: frozen benchmark files changed:\n  " + "\n  ".join(bad))
        return 2
    sys.path.insert(0, str(ROOT / "tools"))
    import agent_carrier_run as R  # noqa: E402
    from modules.capability_runtime import agent_spec as A  # noqa: E402
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in FIXTURES:
        for arm in ARMS:   # arms interleaved per fixture, so drift over the session hits all alike
            dest = out_dir / f"{f[:2]}-{arm}.json"
            if dest.is_file() and json.loads(dest.read_text(encoding="utf-8")).get("status") == "MEASURED":
                print(f"skip {dest.name} (already MEASURED)", flush=True)
                continue
            t0 = time.time()
            rec = R.run(SPEC_ID, mission_for(f), arm, model, "haiku", 900, A.current_state_version(ROOT))
            rec.update({"fixture": f, "arm": arm, "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            dest.write_text(json.dumps(rec, indent=1), encoding="utf-8")   # durable as it goes
            print(f"{dest.name}: {rec.get('status')} {round(time.time() - t0)}s "
                  f"reply={rec.get('returned_chars')} pages={rec.get('pages_read')}", flush=True)
    return 0


def cmd_score(out_dir: Path) -> int:
    key = json.loads((BENCH / "answer_key.json").read_text(encoding="utf-8"))["fixtures"]
    scores: dict = {}
    for f in FIXTURES:
        for arm in ARMS:
            p = out_dir / f"{f[:2]}-{arm}.json"
            rec = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"status": "ABSENT"}
            scores.setdefault(f, {})[arm] = (score_reply(rec.get("reply", ""), key[f])
                                             if rec.get("status") == "MEASURED" and rec.get("reply")
                                             else {"status": rec.get("status", "ABSENT")})
    v = verdict(scores, manifest_mismatches())
    report = {"verdict": v, "scores": scores}
    (out_dir / "score.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for f in FIXTURES:
        for arm in ARMS:
            s = scores[f][arm]
            print(f"{f[:2]} {arm:<10} " + (f"hits={s['n_hits']}/8 fp={s['fp']} blocks={s['blocks']} missed={s['missed']}"
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
    ap.add_argument("--out-dir", default=str(BENCH / "runs" / "s3"))
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT))
    return cmd_run(Path(a.out_dir), a.model) if a.cmd == "run" else cmd_score(Path(a.out_dir))


if __name__ == "__main__":
    sys.exit(main())
