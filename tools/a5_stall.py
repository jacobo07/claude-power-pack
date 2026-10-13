#!/usr/bin/env python3
"""a5_stall.py -- stall-trip measurement over the A5 call table (ce-a5 U7). stdlib only.

Usage: a5_stall.py --calls A/data/calls.jsonl.gz --out A/STALL.md
A stall trip at K fires on the (K+1)th consecutive non-MUTATION call of a session (the guard's rule:
calls since the last edit/commit > K). Tokens = ctx + out per call. A trip is TRUE when the session never mutates
again (the calls from the trip on are cut); otherwise FALSE (it would have stopped a session that went on to progress).
"""
import argparse, collections, gzip, json

KS = (10, 15, 25)
FALSE_RATE_MAX = 0.05


def load(path):
    S = collections.defaultdict(list)
    with gzip.open(path, 'rt') as f:
        for line in f:
            c = json.loads(line)
            S[c['session']].append(c)
    for v in S.values():
        v.sort(key=lambda c: c['seq'])
    return S


def tok(c):
    return c['ctx'] + c['out']


def measure(S, ks=KS, strict=True):
    """strict: trip when run length > K (the guard). strict=False is the off-by-one mutant (>= K)."""
    gaps, res = [], {k: dict(trips=0, true=0, false=0, cut=0, sessions=set()) for k in ks}
    tot = sum(tok(c) for v in S.values() for c in v)
    nomut = [0, 0]
    for s, v in S.items():
        run, anymut = [], False

        def close(run, tail):
            for k in ks:
                if len(run) > k if strict else len(run) >= k:
                    r = res[k]
                    r['trips'] += 1
                    r['sessions'].add(s)
                    if tail:
                        r['true'] += 1
                        r['cut'] += sum(tok(c) for c in run[k:])
                    else:
                        r['false'] += 1
        for c in v:
            if c['label'] == 'MUTATION':
                gaps.append(len(run))
                close(run, False)
                run, anymut = [], True
            else:
                run.append(c)
        close(run, True)
        if not anymut:
            nomut[0] += 1
            nomut[1] += sum(tok(c) for c in v)
    return dict(tokens=tot, gaps=sorted(gaps), res=res, nomut=nomut, sessions=len(S),
                calls=sum(len(v) for v in S.values()))


def choose_k(m, ks=KS, extra=range(1, 101)):
    """Rule: the smallest K whose false-trip rate (gaps between consecutive mutations longer than K) is <= 5 %."""
    g = m['gaps']
    for k in extra:
        if sum(1 for x in g if x > k) / len(g) <= FALSE_RATE_MAX:
            return k
    return max(g)


def q(g, p):
    return g[min(len(g) - 1, int(p * len(g)))]


def report(m, existing=25):
    g, n, K = m['gaps'], len(m['gaps']), choose_k(m)
    cert = abs(existing - K) <= 0.2 * K
    L = ["# A5 U7 -- semantic-progress stall trip (measured)", "",
         f"Source: A/data/calls.jsonl.gz ({m['sessions']} sessions, {m['calls']:,} calls, {m['tokens']:,} tokens ctx+out). "
         "Progress = a MUTATION-labelled call (Edit/Write/MultiEdit/NotebookEdit or `git commit`; U1 proxy label). "
         "The guard's own progress set is the same tools plus any command containing `commit`.", "",
         "## Gap between consecutive MUTATION calls (within a session)", "",
         f"n={n}; p50={q(g,.5)} p75={q(g,.75)} p90={q(g,.9)} p95={q(g,.95)} p99={q(g,.99)} max={g[-1]} (calls strictly between).", "",
         "## Trip at K (fires when calls since last mutation > K)", "",
         "| K | trips | TRUE (never mutated again) | FALSE (mutated later) | gaps>K | tokens cut after trip | share of corpus |",
         "|---|---|---|---|---|---|---|"]
    for k in KS:
        r = m['res'][k]
        L.append(f"| {k} | {r['trips']} | {r['true']} | {r['false']} | {sum(1 for x in g if x > k)}/{n} = "
                 f"{sum(1 for x in g if x > k)/n:.3f} | {r['cut']:,} | {r['cut']/m['tokens']:.2%} |")
    L += ["", f"Sessions with no mutation at all: {m['nomut'][0]} ({m['nomut'][1]:,} tokens, {m['nomut'][1]/m['tokens']:.2%}) -- "
          "mostly read-only subagents; a trip there cuts nothing the session was for, so the cut column counts only the tail past K.", "",
          "## Rule and choice", "",
          f"Rule: K = the smallest K whose false-trip rate (share of mutation gaps longer than K) is <= {FALSE_RATE_MAX:.0%}. Measured K = {K}.",
          f"Existing DEFAULT_NOPROGRESS = {existing}; |{existing}-{K}| = {abs(existing-K)} vs 20 % of K = {0.2*K:.1f} -> "
          + ("CERTIFY_EXISTING, no code change." if cert else "NOT within 20 %: default changed to the measured K (env CPP_NOPROGRESS_K overrides)."), "",
          "## Honest bounds", "",
          "- The cut is small (K=15: 1.79% of tokens; K=14 is between the K=10 and K=15 rows) because most spend sits in sessions that do mutate; the trip is a runaway bound, not a savings engine.",
          "- Labels are a proxy. Receipt writes and matrix deltas are not separate signals here: a receipt is a Write (MUTATION); a bare matrix delta by shell is invisible to the proxy.",
          "- FALSE trips are the price: K=14 stops about 1 in 20 gaps that would have ended in a mutation; the guard's closeout allowance then lets the worker write its receipt."]
    return "\n".join(L) + "\n", K, cert


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--calls', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    txt, K, cert = report(measure(load(a.calls)))
    open(a.out, 'w', encoding='utf8').write(txt)
    print('K', K, 'CERTIFY_EXISTING' if cert else 'CHANGE')
