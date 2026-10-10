#!/usr/bin/env python3
"""ce-a5 U9: promotion rule over DWS + holdout counterfactual results.
PROMOTABLE iff gain >= 10% on DWS AND >= 5% on at least one holdout; else DWS_LOCAL.
A holdout whose gain is None (missing / DEFER_EXTERNAL_DEPENDENCY) never satisfies the threshold.
Usage: a5_holdout.py --dws A/data/counterfactual.json --holdout name=path ... --out A/HOLDOUT.md"""
import argparse, json, os, sys
DWS_MIN, HOLD_MIN = 0.10, 0.05

def gains(path):
    rows = json.load(open(path))['rows']
    return {r[0]: -r[3] for r in rows if r[0] != 'actual'}

def classify(dws, holds):
    """dws: gain or None; holds: list of gain or None."""
    if dws is None or dws < DWS_MIN - 1e-12:
        return 'DWS_LOCAL'
    if any(h is not None and h >= HOLD_MIN - 1e-12 for h in holds):
        return 'PROMOTABLE'
    return 'DWS_LOCAL'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dws', required=True)
    ap.add_argument('--holdout', action='append', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    d = gains(a.dws)
    hs = []
    for h in a.holdout:
        n, p = h.split('=', 1)
        hs.append((n, gains(p) if os.path.exists(p) else None))
    L = ['| policy | DWS | ' + ' | '.join(n for n, _ in hs) + ' | verdict |', '|---|---|' + '---|' * len(hs) + '---|']
    for k, g in d.items():
        hv = [(x[1] or {}).get(k) for x in hs]
        L.append('| %s | %.1f%% | %s | %s |' % (k, 100 * g, ' | '.join('%.1f%%' % (100 * v) if v is not None else 'DEFER_EXTERNAL_DEPENDENCY' for v in hv), classify(g, hv)))
    open(a.out, 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))

if __name__ == '__main__':
    main()
