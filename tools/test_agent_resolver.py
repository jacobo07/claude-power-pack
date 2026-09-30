#!/usr/bin/env python3
"""V-RES-* gates: the resolver as a discovery benchmark (virtualization S2).

The two real specs are placed inside a catalog of 1,000 SYNTHETIC specs (clearly
named synthetic-agent-NNNN, written to a temp dir, never installed). Labeled
queries cover the obvious, paraphrased, cross-domain, over-grant and no-match
cases. A resolver that always matched would fail the no-match gate; one that
never matched fails the rest; one that raised a class to fit fails the grant gate.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.capability_runtime import agent_spec as A  # noqa: E402
from modules.capability_runtime import agent_resolver as R  # noqa: E402

N_SYNTH = 1000
DOMAINS = ["kubernetes rollout", "css grid layout", "postgres vacuum", "android gradle build",
           "terraform drift", "react hydration", "kafka consumer lag", "ios push certificates",
           "webpack bundle size", "redis eviction", "elixir supervision", "unity shader",
           "stripe payout", "dns propagation", "s3 lifecycle", "graphql schema"]
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def synth(root: Path, i: int):
    d = root / f"synthetic-agent-{i:04d}"
    (d / "pages").mkdir(parents=True)
    dom = DOMAINS[i % len(DOMAINS)]
    body = f"SYNTHETIC load-test role {i} for {dom}. Never dispatched.\n"
    (d / "pages" / "01-role.md").write_bytes(body.encode())
    raw = {"contract": {"id": d.name, "name": f"synthetic {dom} specialist {i}", "owner": "synthetic",
                        "triggers": [f"synthetic domain {i:04d} topic", f"{dom} issue"],
                        "consumers": ["load test"], "scope": [dom], "maturity": "experimental"},
           "agent": {"permission_class": A.CLASS_ORDER[i % 3], "description": f"synthetic {dom}",
                     "pages": [{"path": "pages/01-role.md", "load": "inline", "topics": [dom],
                                "sha256": A._sha(body.encode())}]}}
    (d / "spec.json").write_text(json.dumps(raw), encoding="utf-8")


def top(res):
    return [c["id"] for c in res["candidates"]]


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        cat = Path(t) / "catalog"
        cat.mkdir()
        for real in ("oneshot-architect-auditor", "silent-failure-hunter"):
            shutil.copytree(A.SPECS_DIR / real, cat / real)
        for i in range(N_SYNTH):
            synth(cat, i)
        cache = Path(t) / "cache.json"

        def q(task, **kw):
            return R.resolve(task, specs_dir=cat, cache_path=cache, use_cache=False, **kw)

        # First touch of 1,000 JUST-WRITTEN files pays a per-file open cost on this host
        # (measured ~3.6 ms each, 2026-09-30) that a catalog living on disk does not.
        # Reported, not gated; the gate is the steady-state uncached resolve.
        t0 = time.perf_counter()
        r = q("check this service for swallowed errors")
        first_ms = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        r = q("check this service for swallowed errors")
        warm_ms = (time.perf_counter() - t0) * 1000
        check("V-RES-OBVIOUS", top(r)[:1] == ["silent-failure-hunter"], top(r))
        check("V-RES-SCALE-CATALOG", r["catalog_size"] == N_SYNTH + 2 and not r["broken"],
              f"catalog={r['catalog_size']} broken={len(r['broken'])}")
        check("V-RES-LATENCY", warm_ms < 2000,
              f"uncached resolve over {r['catalog_size']} specs: {warm_ms:.0f} ms "
              f"(first touch of fresh files: {first_ms:.0f} ms, info)")
        r = q("does this code fail silently anywhere")
        check("V-RES-PARAPHRASE", "silent-failure-hunter" in top(r), top(r))
        r = q("audit this migration plan for gaps before implementation", max_class="verifier")
        check("V-RES-ORDER-FREE-TRIGGER", top(r)[:1] == ["oneshot-architect-auditor"], top(r))
        r = q("audit this migration plan for gaps before implementation", max_class="investigator")
        check("V-RES-GRANT-DOWNGRADE-ONLY", "oneshot-architect-auditor" not in top(r) and any(
            e["id"] == "oneshot-architect-auditor" and e["code"] == "CLASS_EXCEEDS_GRANT" for e in r["excluded"]),
            f"excluded={[(e['id'], e['code']) for e in r['excluded']][:2]}")
        r = q("review the payment plan for ownership gaps and error handling", max_class="verifier")
        check("V-RES-CROSS-DOMAIN", r["status"] == "RESOLVED" and set(top(r)) & {
            "oneshot-architect-auditor", "silent-failure-hunter"}, top(r))
        r = q("compose a jingle for a pizza advert")
        check("V-RES-NO-MATCH-IS-TYPED", r["status"] == "NO_CERTIFIED_SPECIALIST" and not r["candidates"], r["status"])
        r = q("synthetic domain 0777 topic", max_class="writer")
        check("V-RES-NEEDLE", top(r)[:1] == ["synthetic-agent-0777"], top(r)[:3])
        r = q("check the redis eviction issue", max_class="writer")
        check("V-RES-TOPK-BOUNDED", len(r["candidates"]) <= 3 and r["status"] == "RESOLVED",
              f"{len(r['candidates'])} of many redis specs returned")

        # cache: second identical call hits; a catalog change invalidates it
        R.resolve("check this service for swallowed errors", specs_dir=cat, cache_path=cache)
        hit = R.resolve("check this service for swallowed errors", specs_dir=cat, cache_path=cache)
        check("V-RES-CACHE-HIT", hit["cache"] == "HIT", f"{hit['cache']} {hit['ms']} ms")
        synth(cat, N_SYNTH)
        miss = R.resolve("check this service for swallowed errors", specs_dir=cat, cache_path=cache)
        check("V-RES-CACHE-INVALIDATES", miss["cache"] == "MISS", "catalog change -> MISS")

        empty = Path(t) / "empty"
        empty.mkdir()
        r = R.resolve("anything", specs_dir=empty, use_cache=False)
        check("V-RES-EMPTY-CATALOG", r["status"] == "NO_CERTIFIED_SPECIALIST" and r["catalog_size"] == 0, r["status"])
        try:
            R.resolve("x", max_class="root", specs_dir=cat, use_cache=False)
            code = "NO_ERROR"
        except A.AgentSpecError as e:
            code = e.code
        check("V-RES-BAD-GRANT-TYPED", code == "UNKNOWN_CLASS", code)

    print(f"AGENT_RESOLVER_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
