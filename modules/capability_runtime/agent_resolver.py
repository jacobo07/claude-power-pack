#!/usr/bin/env python3
"""agent_resolver.py -- capability request -> certified specialist, outside the model.

Spec: vault/specs/agent-capability-virtualization.md (S2; typed misses: C4,
vault/plans/acv-c4-typed-misses-2026-10-03.md).

The parent does not read a list of specialists. It states a need; this resolver
answers with at most k candidates, or with a typed miss. It never forces a match.

Two stages, both deterministic:
  1. retrieval  BM25 over each spec's own contract text (name, sovereign
                question, scope, triggers, description, page topics). Cheap at
                catalog scale; only a shortlist reaches stage 2.
  2. gate       `applicability.evaluate` -- the estate's existing capability
                gate (anti-trigger veto, owner, required evidence, duplicate
                scope, runtime). A spec is CERTIFIED for the task only when the
                gate returns an activating verdict. Lexical similarity alone is
                a near miss, reported but never dispatched.

Authority only narrows: the request carries `max_class` (the permission the
caller holds). A spec whose class exceeds it is excluded with CLASS_EXCEEDS_GRANT;
the resolver never raises a class and never lowers a spec's class to make it fit.

Typed misses (`miss`, None when RESOLVED). Each says what may be concluded:
  CATALOG_UNREADABLE  the search did not cover the estate (no catalog, or a spec failed
                      to load). Says nothing about whether a capability exists.
  CLASS_EXCLUDED      a spec ABOVE the grant would pass the same gate. Not a gap.
  BELOW_GATE          an in-grant spec hit a trigger and a capability gate BLOCKED it
                      (applicability.BLOCKING). The capability exists. Not a gap.
  NO_MATCH            the catalog is complete and no shortlisted spec reached its gate.
                      An anti-trigger veto after a trigger hit counts here (`vetoed_by`):
                      the spec disclaimed the request. Scope: BM25 top-SHORTLIST only.
Precedence, when several facts hold: CATALOG_UNREADABLE > CLASS_EXCLUDED > BELOW_GATE >
NO_MATCH (MISS_ORDER). Facts are collected over the whole shortlist, before the top-k cut.
A task with no searchable terms raises EMPTY_TASK: it never reached a search.

Cache: keyed by the normalised request, the grant, k, a fingerprint of every spec.json and
the code's own hash. Only a COMPLETE catalog's answer is stored; `miss` travels in the value.

  python -m modules.capability_runtime.agent_resolver resolve "<task>" [--max-class verifier] [--k 3] [--json]
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime import agent_spec as A  # noqa: E402
from modules.capability_runtime.applicability import (  # noqa: E402
    BLOCKING, MissionContext, Verdict, _hits, canonical_text, evaluate,
)

CACHE = Path.home() / ".claude" / "state" / "agent_resolver_cache.json"
CACHE_MAX = 500
ACTIVATING = {Verdict.MANDATORY, Verdict.RECOMMENDED, Verdict.AVAILABLE_ON_TRIGGER}
SHORTLIST = 20
MISS_ORDER = ("CATALOG_UNREADABLE", "CLASS_EXCLUDED", "BELOW_GATE")   # NO_MATCH when none holds
_TOK = re.compile(r"[a-z0-9]+")
_STOP = frozenset("a an the and or of to in on for with is are be this that it as at by from".split())


def _tokens(text: str) -> list[str]:
    # canonical_text first: [a-z0-9]+ alone turned "C++" into "c" and then dropped it (S5a D1).
    return [t for t in _TOK.findall(canonical_text(text).lower()) if t not in _STOP and len(t) > 1]


def _stem(t: str) -> str:
    """Crude plural fold: 'gaps' -> 'gap', 'errors' -> 'error'. Enough for trigger
    matching; not a linguistic stemmer and not pretending to be one."""
    return t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t


def spec_text(s: "A.AgentSpec") -> str:
    c = s.contract
    topics = " ".join(t for p in s.pages for t in p.get("topics", []))
    return " ".join([c.name, c.sovereign_question, " ".join(c.scope), " ".join(c.triggers),
                     s.description, topics])


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.4, b: float = 0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.avg = (sum(len(d) for d in docs) / len(docs)) if docs else 0.0
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in docs]

    def score(self, q: list[str], i: int) -> float:
        tf, dl, s = self.tf[i], len(self.docs[i]), 0.0
        for t in q:
            f = tf.get(t, 0)
            if f:
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / (self.avg or 1)))
        return s


def fingerprint(specs_dir: Path | None = None) -> str | None:
    """Cache key for the catalog: (name, size, mtime) of every spec.json. None when the
    catalog cannot be stat'ed (a spec deleted between glob and stat): the caller then skips
    the cache for that call rather than crashing before the catalog is even read (C4).

    Measured 2026-09-30: hashing CONTENT opened every file before a cache lookup and
    was 3.8 of 4.3 s on a 1,000-spec catalog. Metadata is enough here -- this key
    only invalidates a cache. Its worst miss is a stale candidate id, and compile()
    re-verifies every page hash before anything is dispatched."""
    root = specs_dir or A.SPECS_DIR
    h = hashlib.sha256()
    try:
        if root.is_dir():
            for f in sorted(root.glob("*/spec.json")):
                st = f.stat()
                h.update(f"{f.parent.name}|{st.st_size}|{st.st_mtime_ns};".encode())
    except OSError:
        return None
    return h.hexdigest()[:16]


_POLICY: str | None = None
# Modules in this package that never change an answer. agent_telemetry only serialises a result
# and agent_resolver_cli only parses arguments and prints one; hashing either would make an edit
# there read as a resolver version change and flush every cache entry (ACV C5 audit gap 1, R2).
NOT_POLICY = frozenset({"agent_telemetry.py", "agent_resolver_cli.py"})


def policy_hash(root: Path | None = None) -> str:
    """Version of the code that produces an answer: sha256 over every capability_runtime module
    except NOT_POLICY.

    The cache key used to carry only the query, the grant and the catalog, so a miss cached
    before a matcher fix kept being served after it (measured 2026-10-03, S5a D2). The class
    order (agent_spec), contract defaults and scales (contract) and the gates (applicability)
    all change answers, so the whole package is hashed, once per process. `root` hashes another
    directory, uncached, so a gate can edit a copy of the package instead of the live one."""
    global _POLICY
    if root is not None:
        return _hash_package(Path(root))
    if _POLICY is None:
        _POLICY = _hash_package(Path(__file__).resolve().parent)
    return _POLICY


def _hash_package(root: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(root.glob("*.py")):
        if f.name in NOT_POLICY:
            continue
        h.update(f.name.encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:16]


def _mission(task: str, s: "A.AgentSpec", qstems: set) -> MissionContext:
    """The mission text the gate judges a spec on: one builder for in-grant AND excluded specs.

    Routing miss found by the S2 probe (2026-09-30): "audit this migration plan" never reached a
    spec whose trigger is "audit plan", because the shared gate matches triggers as contiguous
    phrases. Order-free trigger hits are appended to the mission text, so the SAME gate still
    applies every other rule (anti-trigger veto, owner, evidence, scope, runtime) -- only
    relevance is widened, here only."""
    hits = [t for t in s.contract.triggers
            if (ts := {_stem(x) for x in _tokens(t)}) and ts <= qstems]
    return MissionContext(description=task + (" || " + " ; ".join(hits) if hits else ""))


def pick_miss(facts: dict) -> str:
    """The single reason a resolution produced no candidate: the first fact in MISS_ORDER that
    holds, else NO_MATCH. A fixed table, never iteration order over specs."""
    return next((m for m in MISS_ORDER if facts.get(m)), "NO_MATCH")


def resolve(task: str, max_class: str = "verifier", k: int = 3,
            specs_dir: Path | None = None, use_cache: bool = True, cache_path: Path | None = None) -> dict:
    t0 = time.perf_counter()
    A.class_rank(max_class)                                   # typed error on a bad grant
    if not (task or "").strip():
        raise A.AgentSpecError("EMPTY_TASK", "a capability request needs a task")
    q = _tokens(task)
    if not q:
        # "!!! ???" is not a search: BM25 scores every spec 0, so any miss label would be false
        # evidence about the estate. Same typed error as a blank task (C4 decision 3).
        raise A.AgentSpecError("EMPTY_TASK", f"no searchable terms in {task.strip()[:40]!r}")
    # Request identity (ACV C5): the normalised token sequence this resolver actually searched, so
    # "Review C++ code" and "review cpp code" are one request. The normalisation lives in this
    # package, which policy_hash covers, so (query_fp, policy) stays unambiguous across changes.
    qfp = hashlib.sha256(" ".join(q).encode("utf-8")).hexdigest()[:16]
    fp = fingerprint(specs_dir)
    pol = policy_hash()
    use_cache = use_cache and fp is not None
    key = hashlib.sha256(f"{' '.join(q)}|{max_class}|{k}|{fp}|{pol}".encode()).hexdigest()[:24]
    cpath = cache_path or CACHE
    cache = {}
    if use_cache and cpath.is_file():
        try:
            cache = json.loads(cpath.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cache = {}
        if key in cache:
            hit = dict(cache[key])
            hit.update(cache="HIT", ms=round((time.perf_counter() - t0) * 1000, 2))
            return hit

    specs, broken = A.catalog(specs_dir)
    if not specs:
        # NO_CATALOG / every spec broken -> the search never happened. An existing, empty
        # catalog is a complete search over nothing.
        miss = "CATALOG_UNREADABLE" if broken else "NO_MATCH"
        # miss_ids name specs that failed to load; a missing catalog is not a spec, and its path
        # is not a capability identity (ACV C5), so NO_CATALOG contributes no id.
        return {"status": "CATALOG_UNREADABLE" if broken else "NO_CERTIFIED_SPECIALIST",
                "miss": miss, "miss_ids": sorted(b["spec"] for b in broken if b["code"] != "NO_CATALOG"),
                "vetoed_by": [], "candidates": [], "near_misses": [], "excluded": [], "broken": broken,
                "catalog_size": 0, "fingerprint": fp, "policy": pol, "query_fp": qfp, "cache": "MISS",
                "ms": round((time.perf_counter() - t0) * 1000, 2)}
    index = BM25([_tokens(spec_text(s)) for s in specs])
    ranked = sorted(((index.score(q, i), s) for i, s in enumerate(specs)), key=lambda x: -x[0])
    shortlist = [(sc, s) for sc, s in ranked[:SHORTLIST] if sc > 0]

    qstems = {_stem(t) for t in q}
    candidates, near, excluded = [], [], []
    facts = {"CATALOG_UNREADABLE": [b["spec"] for b in broken], "CLASS_EXCLUDED": [], "BELOW_GATE": []}
    vetoed = []
    for sc, s in shortlist:
        ctx = _mission(task, s, qstems)
        ap = evaluate(s.contract, ctx)
        if A.class_rank(s.permission_class) > A.class_rank(max_class):
            # Judged by the same gate so that only a spec that WOULD be selected counts as an
            # exclusion. Measured 2026-10-03: 7 reviewers were shortlisted above an investigator
            # grant for "review this code for bugs" on lexical overlap alone.
            would = ap.verdict in ACTIVATING
            excluded.append({"id": s.id, "code": "CLASS_EXCEEDS_GRANT", "would_activate": would,
                             "detail": f"needs {s.permission_class}, grant is {max_class}"})
            if would:
                facts["CLASS_EXCLUDED"].append(s.id)
            continue
        row = {"id": s.id, "class": s.permission_class, "carrier": A.carrier_name(s.permission_class),
               "bm25": round(sc, 3), "verdict": ap.verdict.value, "gate_score": ap.score, "reason": ap.reason}
        if ap.verdict in ACTIVATING:
            candidates.append(row)
            continue
        near.append(row)
        # "Reached its gate" is evaluate()'s own gate-1.5 predicate on the same text it judged.
        if _hits(ctx.description, s.contract.triggers):
            if ap.verdict in BLOCKING:
                facts["BELOW_GATE"].append(s.id)
            else:
                vetoed.append(s.id)                    # anti-trigger veto: the spec disclaimed it
    order = {Verdict.MANDATORY.value: 0, Verdict.RECOMMENDED.value: 1, Verdict.AVAILABLE_ON_TRIGGER.value: 2}
    candidates.sort(key=lambda r: (order[r["verdict"]], -r["gate_score"], -r["bm25"]))
    if candidates:
        status, miss, miss_ids = "RESOLVED", None, []
    else:
        miss = pick_miss(facts)
        miss_ids = sorted(facts.get(miss, []))
        status = "CATALOG_UNREADABLE" if miss == "CATALOG_UNREADABLE" else "NO_CERTIFIED_SPECIALIST"
    out = {"status": status, "miss": miss, "miss_ids": miss_ids,
           "vetoed_by": sorted(vetoed) if miss == "NO_MATCH" else [],
           "candidates": candidates[:k], "near_misses": near[:k], "excluded": excluded,
           "broken": broken, "catalog_size": len(specs), "fingerprint": fp, "policy": pol,
           "query_fp": qfp, "cache": "MISS",
           "ms": round((time.perf_counter() - t0) * 1000, 2)}
    # Only a complete catalog's answer is reusable: a spec that failed to load may be the one
    # that matches, and restoring it need not change any spec.json the fingerprint sees.
    if use_cache and not broken:
        try:
            cache[key] = {k2: v for k2, v in out.items() if k2 not in ("cache", "ms")}
            while len(cache) > CACHE_MAX:
                cache.pop(next(iter(cache)))
            cpath.parent.mkdir(parents=True, exist_ok=True)
            cpath.write_text(json.dumps(cache), encoding="utf-8")
        except OSError:
            pass                                           # a cache write failure never changes the answer
    return out


def main(argv=None) -> int:
    """The CLI lives in agent_resolver_cli (outside policy_hash, ACV C5 R2); this stub keeps the
    documented `python -m modules.capability_runtime.agent_resolver resolve ...` working."""
    from modules.capability_runtime.agent_resolver_cli import main as cli_main
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
