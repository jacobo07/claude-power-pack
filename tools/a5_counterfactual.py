#!/usr/bin/env python3
"""a5_counterfactual.py -- counterfactual replay of DWS call sequences under candidate policies (ce-a5 U2). stdlib only.

Usage: a5_counterfactual.py --calls A/data/calls.jsonl.gz --out A_DIR   (writes A/COUNTERFACTUAL.md, A/data/counterfactual.json,
                                                                         and negative results into --neg JSON if given)
ASSUMPTIONS (also printed in COUNTERFACTUAL.md header):
 A1 tokens = sum over calls of ctx (input+cache_read+cache_write), the U1 currency; output tokens are excluded everywhere.
 A2 growth caused by call j = ctx[j+1]-ctx[j] (what its result/output added to the next call's context); last call of a session = 0.
    Negative growth (compaction/reset, 12 cases) is kept as measured.
 A3 simulated ctx of a kept call = F + sum of caused growth of kept calls before it in the current segment; F = floor of the segment.
    Growth does not depend on the policy (a removed call removes its own growth only; other calls keep their measured growth).
 A4 floor F = measured first-call ctx of the session; 30 sessions have first ctx 0 (measurement artifact) and keep F=0 in 'actual'.
 A5 (a) slim: F := 13,507 for every session (also those with measured floor 0 or below 13,507: the policy sets, it does not min()).
 A6 (b) rotation at N: after every N kept calls a fresh segment starts at F + CAPSULE(2,500 tokens); growth continues from there.
    The capsule's authoring cost (output tokens) and loss of information (re-derivation) are NOT modelled.
 A7 (c) read-once: REDISCOVERY-labelled calls removed with their growth. Label is a proxy (U1).
 A8 (d) STATE projection: caused growth of each STATE_READ call := min(measured growth, 2,500) (8 KB ~ 2.5K tokens); call kept.
 A9 (e) poll->event: CONTROL_LOOP-labelled calls removed with their growth (an event wakes the session instead; wake cost not modelled).
 A10 Calls removed by (c)/(e) are dropped before rotation counting; rotation counts kept calls. Combination f = a + b20 + c + d + e.
 A11 No cache-discount modelling: processed tokens, not dollars.
"""
import argparse, collections, gzip, json, os, sys

SLIM = 13507
CAPSULE = 2500
STATE_CAP = 2500


def load(path):
    by = collections.OrderedDict()
    with gzip.open(path, 'rt') as f:
        for l in f:
            r = json.loads(l)
            by.setdefault(r['session'], []).append(r)
    for v in by.values():
        v.sort(key=lambda r: r['seq'])
    return by


def caused(calls):
    return [(calls[i + 1]['ctx'] - calls[i]['ctx']) if i + 1 < len(calls) else 0 for i in range(len(calls))]


def replay(calls, slim=False, rot=None, no_reread=False, state=False, noloop=False, capsule=CAPSULE):
    """returns (tokens, kept_calls) for one session"""
    if not calls:
        return 0, 0
    g = caused(calls)
    F = SLIM if slim else calls[0]['ctx']
    tot = n = 0
    cur = F
    seg = 0
    for c, gr in zip(calls, g):
        if (no_reread and c['label'] == 'REDISCOVERY') or (noloop and c['label'] == 'CONTROL_LOOP'):
            continue
        if rot and seg >= rot:
            cur = F + capsule
            seg = 0
        if state and c['label'] == 'STATE_READ':
            gr = min(gr, STATE_CAP)
        tot += cur
        n += 1
        seg += 1
        cur += gr
    return tot, n


POLICIES = [
    ('actual', {}),
    ('a slim floor 13,507', dict(slim=True)),
    ('b1 rotate N=12', dict(rot=12)),
    ('b2 rotate N=20', dict(rot=20)),
    ('b3 rotate N=40', dict(rot=40)),
    ('c read-once', dict(no_reread=True)),
    ('d STATE projection 8KB', dict(state=True)),
    ('e poll->event', dict(noloop=True)),
    ('f a+b20+c+d+e', dict(slim=True, rot=20, no_reread=True, state=True, noloop=True)),
]


def run(by, capsule=CAPSULE):
    out = {}
    for name, kw in POLICIES:
        t = n = 0
        for calls in by.values():
            a, b = replay(calls, capsule=capsule, **kw)
            t += a
            n += b
        out[name] = (t, n)
    return out


def duplicates(by, k=3):
    """CSE candidates: (read target, next-k first-tool sequence) seen in >=2 distinct sessions."""
    occ = collections.defaultdict(set)
    cnt = collections.Counter()
    for s, calls in by.items():
        for i, c in enumerate(calls):
            seq = tuple((x['tools'][0] if x['tools'] else '-') for x in calls[i + 1:i + 1 + k])
            for p in set(c['reads']):
                key = (p, seq)
                occ[key].add(s)
                cnt[key] += 1
    groups = [k_ for k_, v in occ.items() if len(v) >= 2]
    redundant = sum(cnt[g] - 1 for g in groups)
    return len(groups), redundant, sum(cnt.values())


def confidence(name):
    return {'actual': 'measured',
            'a slim floor 13,507': 'MEDIUM: floor measured on slim-t2 probe; growth assumed independent of floor',
            'b1 rotate N=12': 'LOW-MED: capsule fidelity and re-derivation after rotation not modelled',
            'b2 rotate N=20': 'LOW-MED: same as b1',
            'b3 rotate N=40': 'LOW-MED: same as b1',
            'c read-once': 'LOW: REDISCOVERY label is a proxy; some re-reads follow edits/compaction',
            'd STATE projection 8KB': 'LOW-MED: needs a projection that preserves what STATE_READ consumers use',
            'e poll->event': 'LOW: CONTROL_LOOP label is a proxy; event delivery must exist (U-other)',
            'f a+b20+c+d+e': 'LOW: product of LOW assumptions; interaction via A3 growth independence'}.get(name, 'LOW')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--calls', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--neg')
    a = ap.parse_args()
    by = load(a.calls)
    res = run(by)
    base_t, base_n = res['actual']
    dups = duplicates(by)
    rows = []
    neg = []
    for name, _ in POLICIES:
        t, n = res[name]
        d = (t - base_t) / base_t
        rows.append((name, t, n, d))
        if name != 'actual' and -d < 0.03:
            neg.append({'question': 'Does policy "%s" cut DWS processed tokens by >= 3%%?' % name,
                        'envelope': 'U2 counterfactual replay over 10,985 DWS calls; assumptions A1-A11 in COUNTERFACTUAL.md',
                        'number': '%.2f%% delta (%d tokens)' % (100 * d, t - base_t),
                        'reopen_condition': 'new trace with a different session mix, or a change to the policy parameters that moves the replay delta past 3%'})
    best = min(rows[1:], key=lambda r: r[1])
    L = ['# COUNTERFACTUAL (ce-a5 U2)', '', 'Generated by tools/a5_counterfactual.py from A/data/calls.jsonl.gz. NOT realized savings: a replay under stated assumptions.', '',
         '## Assumptions', '']
    L += [l[1:] for l in __doc__.split('\n') if l.startswith(' A')]
    L += ['', '## Results', '', '| policy | processed tokens | calls | delta vs actual | confidence |', '|---|---|---|---|---|']
    for name, t, n, d in rows:
        L.append('| %s | %s | %s | %+.1f%% | %s |' % (name, format(t, ','), format(n, ','), 100 * d, confidence(name)))
    L += ['', 'Best single/combined policy: **%s** (%+.1f%%).' % (best[0], 100 * best[3]), '',
          '## Reopened questions', '',
          '1. Duplicate derivations (read target + same next-3 first-tool sequence in >= 2 distinct sessions): %s CSE-candidate groups; %s redundant occurrences beyond the first, of %s read occurrences. Crude: identical sequence != identical derivation.' % (format(dups[0], ','), format(dups[1], ','), format(dups[2], ',')),
          '2. Tool-schema share of the first-call floor: **UNKNOWN**. Transcripts carry only the total usage (input+cache) per call and name-level `deferred_tools_delta` / `skill_listing` attachments; no per-component token counts, so schema tokens cannot be separated from system prompt, CLAUDE.md and skills. Policy (a) therefore tests the floor as a whole.', '']
    open(os.path.join(a.out, 'COUNTERFACTUAL.md'), 'w').write('\n'.join(L))
    json.dump({'rows': rows, 'dups': dups}, open(os.path.join(a.out, 'data', 'counterfactual.json'), 'w'), indent=1)
    if a.neg:
        json.dump({'schema': 'a5-negative-investments/1', 'entries': neg}, open(a.neg, 'w'), indent=1)
    for r in rows:
        print('%-24s %15s %7s %+.1f%%' % (r[0], format(r[1], ','), format(r[2], ','), 100 * r[3]))
    print('dups', dups)


if __name__ == '__main__':
    main()
