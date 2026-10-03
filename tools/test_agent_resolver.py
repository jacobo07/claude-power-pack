#!/usr/bin/env python3
"""V-RES-* gates: the resolver as a discovery benchmark (virtualization S2).

The two real specs are placed inside a catalog of 1,000 SYNTHETIC specs (clearly
named synthetic-agent-NNNN, written to a temp dir, never installed). Labeled
queries cover the obvious, paraphrased, cross-domain, over-grant and no-match
cases. A resolver that always matched would fail the no-match gate; one that
never matched fails the rest; one that raised a class to fit fails the grant gate.

V-RES-MISS-* (ACV C4) drive every typed miss through the real resolve() path: the real
catalog for NO_MATCH / CLASS_EXCLUDED / the anti-trigger veto, temp catalogs built from real
specs for BELOW_GATE, precedence and the unreadable-catalog cases.
"""
from __future__ import annotations

import json
import pathlib
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
SFH, AUDITOR = "silent-failure-hunter", "oneshot-architect-auditor"
SFH_TASK = "check this service for swallowed errors"
AUDIT_TASK = "audit this migration plan for gaps before implementation"
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


def code_of(fn):
    try:
        fn()
        return "NO_ERROR"
    except A.AgentSpecError as e:
        return e.code


def real_spec(cat: Path, sid: str, as_dir: str | None = None, evidence: list | None = None) -> None:
    """Copy a REAL spec into a temp catalog; `evidence` adds required_evidence the resolver
    never supplies, so gate 3 blocks it on the real path (C4: no real spec declares any)."""
    d = cat / (as_dir or sid)
    shutil.copytree(A.SPECS_DIR / sid, d)
    if evidence:
        raw = json.loads((d / "spec.json").read_text(encoding="utf-8"))
        raw["contract"]["required_evidence"] = evidence
        (d / "spec.json").write_text(json.dumps(raw), encoding="utf-8")


def rows(path: Path) -> int:
    return len(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else 0


def typed_misses(t: Path) -> None:
    print("\n[resolver] typed misses (ACV C4)")
    # BELOW_GATE: an in-grant spec hits its trigger and a capability gate blocks it. k=0 proves
    # the fact is read from the whole shortlist, not from the truncated near_misses list.
    cat = t / "below"
    real_spec(cat, SFH, evidence=["runtime-trace"])
    r = R.resolve(SFH_TASK, max_class="investigator", specs_dir=cat, use_cache=False)
    r0 = R.resolve(SFH_TASK, max_class="investigator", k=0, specs_dir=cat, use_cache=False)
    check("V-RES-MISS-BELOW-GATE", (r["status"], r["miss"], r["miss_ids"]) == (
        "NO_CERTIFIED_SPECIALIST", "BELOW_GATE", [SFH]) and (r0["miss"], r0["miss_ids"]) == ("BELOW_GATE", [SFH]),
          f"{r['miss']} {r['miss_ids']} | k=0: {r0['miss']}")

    # Precedence: both facts hold (SFH blocked in grant, the auditor would activate above it).
    # Two catalogs with the directory names swapped: the catalog sorts by directory name, so a
    # result that followed iteration order would differ between them.
    task = SFH_TASK + " and " + AUDIT_TASK
    got = []
    for name, (a, b) in {"order-a": ("a-sfh", "z-aud"), "order-b": ("z-sfh", "a-aud")}.items():
        cat = t / name
        real_spec(cat, SFH, a, evidence=["runtime-trace"])
        real_spec(cat, AUDITOR, b)
        r = R.resolve(task, max_class="investigator", specs_dir=cat, use_cache=False)
        blocked = any(n["id"] == SFH and n["verdict"] == "BLOCKED_BY_MISSING_EVIDENCE" for n in r["near_misses"])
        got.append((r["miss"], r["miss_ids"], blocked))
    table = R.pick_miss({"BELOW_GATE": ["x"], "CLASS_EXCLUDED": ["y"], "CATALOG_UNREADABLE": []})
    check("V-RES-MISS-PRECEDENCE", got == [("CLASS_EXCLUDED", [AUDITOR], True)] * 2 and table == "CLASS_EXCLUDED"
          and R.pick_miss({"BELOW_GATE": ["x"], "CATALOG_UNREADABLE": ["z"]}) == "CATALOG_UNREADABLE"
          and R.pick_miss({}) == "NO_MATCH", f"{got} table={table}")

    # CATALOG_UNREADABLE, partial: one real spec loads, one spec.json is not JSON. Before C4 this
    # answered NO_CERTIFIED_SPECIALIST and was CACHED, though the broken spec may be the match.
    cat = t / "partial"
    real_spec(cat, SFH)
    (cat / "zz-broken").mkdir()
    (cat / "zz-broken" / "spec.json").write_text("{not json", encoding="utf-8")
    pc = t / "partial-cache.json"
    r1 = R.resolve("write a haiku about the ocean", specs_dir=cat, cache_path=pc)
    r2 = R.resolve("write a haiku about the ocean", specs_dir=cat, cache_path=pc)
    check("V-RES-MISS-CATALOG-PARTIAL", (r1["status"], r1["miss"], r1["miss_ids"]) == (
        "CATALOG_UNREADABLE", "CATALOG_UNREADABLE", ["zz-broken"]) and r1["catalog_size"] == 1,
          f"{r1['status']} {r1['miss']} {r1['miss_ids']}")
    rr = R.resolve(SFH_TASK, max_class="investigator", specs_dir=cat, cache_path=pc)
    rr2 = R.resolve(SFH_TASK, max_class="investigator", specs_dir=cat, cache_path=pc)
    check("V-RES-MISS-UNREADABLE-NOT-CACHED", r2["cache"] == "MISS" and rows(pc) == 0
          and top(rr) == [SFH] and rr2["cache"] == "MISS",
          f"miss twice: {r1['cache']}/{r2['cache']}, partial RESOLVED twice: {rr['cache']}/{rr2['cache']}, rows={rows(pc)}")

    r = R.resolve("anything at all", specs_dir=t / "no-such-catalog", use_cache=False)
    check("V-RES-MISS-NO-CATALOG", (r["status"], r["miss"]) == ("CATALOG_UNREADABLE", "CATALOG_UNREADABLE"),
          f"{r['status']} {r['miss']} {r['broken']}")

    # fingerprint() is read before the catalog: a stat failure there disables the cache for the
    # call instead of crashing (C4 audit gap 5). Boundary stub: the filesystem's stat.
    real_stat = pathlib.Path.stat
    pathlib.Path.stat = lambda self, *a, **kw: (_ for _ in ()).throw(OSError("simulated stat failure")) \
        if self.name == "spec.json" else real_stat(self, *a, **kw)
    try:
        fp = R.fingerprint(t / "below")
    finally:
        pathlib.Path.stat = real_stat
    check("V-RES-FINGERPRINT-OSERROR", fp is None, f"fingerprint={fp}")


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

        # S5a D2: a cached answer must not survive a change to the code that produced it.
        # Measured 2026-10-03: the key was tokens|class|k|catalog metadata, so a miss cached
        # before a matcher fix kept being served after it. The policy is a hash of every
        # capability_runtime module; changing it here stands in for editing one of them.
        pcache = Path(t) / "policy-cache.json"
        fresh = R.resolve("compose a jingle for a pizza advert", specs_dir=cat, cache_path=pcache)
        warm = R.resolve("compose a jingle for a pizza advert", specs_dir=cat, cache_path=pcache)
        real_policy = R.policy_hash()
        R._POLICY = "edited-" + real_policy
        try:
            after = R.resolve("compose a jingle for a pizza advert", specs_dir=cat, cache_path=pcache)
        finally:
            R._POLICY = real_policy
        check("V-RES-CACHE-POLICY", warm["cache"] == "HIT" and after["cache"] == "MISS"
              and warm.get("policy") == real_policy,
              f"same code -> {warm['cache']}, edited code -> {after['cache']}")
        # C4: the typed reason is part of the cached value, so a HIT reproduces it.
        check("V-RES-MISS-CACHE-ROUNDTRIP", (fresh["cache"], fresh["miss"]) == ("MISS", "NO_MATCH")
              and (warm["cache"], warm["miss"], warm["miss_ids"]) == ("HIT", "NO_MATCH", []),
              f"fresh {fresh['cache']}/{fresh['miss']} -> cached {warm['cache']}/{warm['miss']}")
        # C4 decision 3 (supersedes C3's V-RES-CACHE-NO-EMPTY-KEY): a task with no searchable
        # terms is not a search, so it is the typed EMPTY_TASK error and never touches the cache.
        n_before = rows(pcache)
        codes = [code_of(lambda: R.resolve("!!! ???", specs_dir=cat, cache_path=pcache)) for _ in range(2)]
        check("V-RES-EMPTY-QUERY-TYPED", codes == ["EMPTY_TASK"] * 2 and rows(pcache) == n_before,
              f"codes={codes}, cache rows {n_before}->{rows(pcache)}")

        empty = Path(t) / "empty"
        empty.mkdir()
        r = R.resolve("anything", specs_dir=empty, use_cache=False)
        check("V-RES-EMPTY-CATALOG", (r["status"], r["miss"], r["catalog_size"]) == (
            "NO_CERTIFIED_SPECIALIST", "NO_MATCH", 0), f"{r['status']} {r['miss']}")
        check("V-RES-BAD-GRANT-TYPED", code_of(lambda: R.resolve("x", max_class="root", specs_dir=cat,
                                                                 use_cache=False)) == "UNKNOWN_CLASS",
              "a bad grant is judged before the task's tokens")

        typed_misses(Path(t))

    # Symbol-bearing names (S5a D1), on the REAL catalog: measured 2026-10-03, "C++" tokenised
    # to nothing and this request resolved to no specialist while "cpp" reached cpp-reviewer.
    toks = [R._tokens(x) for x in ("C++", "C#", "F#", "review this C++ code")]
    check("V-RES-SYMBOL-TOKENS", toks == [["cpp"], ["csharp"], ["fsharp"], ["review", "cpp", "code"]], toks)
    r = R.resolve("review this C++ code for memory bugs", use_cache=False)
    check("V-RES-SYMBOL-ROUTES", top(r)[:1] == ["cpp-reviewer"], f"{r['status']} {top(r)}")

    # Typed misses on the REAL catalog (C4). Measured 2026-10-03 before C4: the haiku request
    # carried a lexical near-miss and "review this code for bugs" excluded 7 reviewers that no
    # gate had judged -- read as causes, either would have made NO_MATCH unreachable.
    r = R.resolve("write a haiku about the ocean", use_cache=False)
    check("V-RES-MISS-NO-MATCH-REAL", (r["status"], r["miss"], r["miss_ids"]) == (
        "NO_CERTIFIED_SPECIALIST", "NO_MATCH", []) and not r["broken"], f"{r['miss']} broken={r['broken']}")
    r = R.resolve("review this code for bugs", max_class="investigator", use_cache=False)
    check("V-RES-MISS-EXCLUSION-NOT-NOISE", r["miss"] == "NO_MATCH" and len(r["excluded"]) >= 1
          and not any(e["would_activate"] for e in r["excluded"]),
          f"{r['miss']}, {len(r['excluded'])} lexical exclusions, none would activate")
    r = R.resolve(AUDIT_TASK, max_class="investigator", use_cache=False)
    check("V-RES-MISS-CLASS-EXCLUDED-REAL", (r["miss"], r["miss_ids"]) == ("CLASS_EXCLUDED", [AUDITOR]),
          f"{r['miss']} {r['miss_ids']}")
    # C4 audit gap 1: an anti-trigger veto after a trigger hit is the spec disclaiming the request
    # (every real anti-trigger is "write the fix"), not proof a capability exists -> NO_MATCH.
    r = R.resolve("review this go code and write the fix", use_cache=False)
    check("V-RES-MISS-VETO-IS-NO-MATCH", (r["miss"], r["vetoed_by"]) == ("NO_MATCH", ["go-reviewer"]),
          f"{r['miss']} vetoed_by={r['vetoed_by']}")

    print(f"AGENT_RESOLVER_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
