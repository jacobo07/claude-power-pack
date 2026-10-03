#!/usr/bin/env python3
"""agent_resolver.py -- capability request -> certified specialist, outside the model.

Spec: vault/specs/agent-capability-virtualization.md (S2).

The parent does not read a list of specialists. It states a need; this resolver
answers with at most k candidates, or with the typed answer
NO_CERTIFIED_SPECIALIST. It never forces a match.

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

Cache: keyed by the normalised request plus a fingerprint of every spec.json, so
any catalog change invalidates every entry.

  python -m modules.capability_runtime.agent_resolver resolve "<task>" [--max-class verifier] [--k 3] [--json]
"""
from __future__ import annotations

import argparse
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
    MissionContext, Verdict, canonical_text, evaluate,
)

CACHE = Path.home() / ".claude" / "state" / "agent_resolver_cache.json"
CACHE_MAX = 500
ACTIVATING = {Verdict.MANDATORY, Verdict.RECOMMENDED, Verdict.AVAILABLE_ON_TRIGGER}
SHORTLIST = 20
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


def fingerprint(specs_dir: Path | None = None) -> str:
    """Cache key for the catalog: (name, size, mtime) of every spec.json.

    Measured 2026-09-30: hashing CONTENT opened every file before a cache lookup and
    was 3.8 of 4.3 s on a 1,000-spec catalog. Metadata is enough here -- this key
    only invalidates a cache. Its worst miss is a stale candidate id, and compile()
    re-verifies every page hash before anything is dispatched."""
    root = specs_dir or A.SPECS_DIR
    h = hashlib.sha256()
    if root.is_dir():
        for f in sorted(root.glob("*/spec.json")):
            st = f.stat()
            h.update(f"{f.parent.name}|{st.st_size}|{st.st_mtime_ns};".encode())
    return h.hexdigest()[:16]


def resolve(task: str, max_class: str = "verifier", k: int = 3,
            specs_dir: Path | None = None, use_cache: bool = True, cache_path: Path | None = None) -> dict:
    t0 = time.perf_counter()
    A.class_rank(max_class)                                   # typed error on a bad grant
    if not (task or "").strip():
        raise A.AgentSpecError("EMPTY_TASK", "a capability request needs a task")
    fp = fingerprint(specs_dir)
    key = hashlib.sha256(f"{' '.join(_tokens(task))}|{max_class}|{k}|{fp}".encode()).hexdigest()[:24]
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
        return {"status": "CATALOG_UNREADABLE" if broken else "NO_CERTIFIED_SPECIALIST",
                "candidates": [], "near_misses": [], "excluded": [], "broken": broken,
                "catalog_size": 0, "fingerprint": fp, "cache": "MISS",
                "ms": round((time.perf_counter() - t0) * 1000, 2)}
    q = _tokens(task)
    index = BM25([_tokens(spec_text(s)) for s in specs])
    ranked = sorted(((index.score(q, i), s) for i, s in enumerate(specs)), key=lambda x: -x[0])
    shortlist = [(sc, s) for sc, s in ranked[:SHORTLIST] if sc > 0]

    qstems = {_stem(t) for t in q}
    candidates, near, excluded = [], [], []
    for sc, s in shortlist:
        if A.class_rank(s.permission_class) > A.class_rank(max_class):
            excluded.append({"id": s.id, "code": "CLASS_EXCEEDS_GRANT",
                             "detail": f"needs {s.permission_class}, grant is {max_class}"})
            continue
        # Routing miss found by the S2 probe (2026-09-30): "audit this migration plan"
        # never reached a spec whose trigger is "audit plan", because the shared gate
        # matches triggers as contiguous phrases. Order-free trigger hits are appended to
        # the mission text, so the SAME gate still applies every other rule (anti-trigger
        # veto, owner, evidence, scope, runtime) -- only relevance is widened, here only.
        hits = [t for t in s.contract.triggers
                if (ts := {_stem(x) for x in _tokens(t)}) and ts <= qstems]
        ctx = MissionContext(description=task + (" || " + " ; ".join(hits) if hits else ""))
        ap = evaluate(s.contract, ctx)
        row = {"id": s.id, "class": s.permission_class, "carrier": A.carrier_name(s.permission_class),
               "bm25": round(sc, 3), "verdict": ap.verdict.value, "gate_score": ap.score, "reason": ap.reason}
        (candidates if ap.verdict in ACTIVATING else near).append(row)
    order = {Verdict.MANDATORY.value: 0, Verdict.RECOMMENDED.value: 1, Verdict.AVAILABLE_ON_TRIGGER.value: 2}
    candidates.sort(key=lambda r: (order[r["verdict"]], -r["gate_score"], -r["bm25"]))
    out = {"status": "RESOLVED" if candidates else "NO_CERTIFIED_SPECIALIST",
           "candidates": candidates[:k], "near_misses": near[:k], "excluded": excluded,
           "broken": broken, "catalog_size": len(specs), "fingerprint": fp, "cache": "MISS",
           "ms": round((time.perf_counter() - t0) * 1000, 2)}
    if use_cache:
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
    ap = argparse.ArgumentParser(prog="agent_resolver")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve"); r.add_argument("task")
    r.add_argument("--max-class", default="verifier", choices=A.CLASS_ORDER)
    r.add_argument("--k", type=int, default=3); r.add_argument("--json", action="store_true")
    r.add_argument("--no-cache", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = resolve(a.task, a.max_class, a.k, use_cache=not a.no_cache)
    except A.AgentSpecError as e:
        print(f"AGENTSPEC_ERROR {e.code} {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        print(f"{res['status']} catalog={res['catalog_size']} cache={res['cache']} {res['ms']}ms")
        for c in res["candidates"]:
            print(f"  {c['id']}  class={c['class']} verdict={c['verdict']} gate={c['gate_score']} bm25={c['bm25']}")
            print(f"    compile: python -m modules.capability_runtime.agent_spec compile {c['id']} "
                  f"--mission-file <file> --json   (dispatch to {c['carrier']})")
        for n in res["near_misses"]:
            print(f"  near-miss {n['id']}: {n['reason']}")
        for e in res["excluded"]:
            print(f"  excluded {e['id']}: {e['code']} {e['detail']}")
    return 0 if res["status"] == "RESOLVED" else 1


if __name__ == "__main__":
    sys.exit(main())
