#!/usr/bin/env python3
"""a5_u8_fault_check.py -- for DWS sessions that read STATE.md, take the next 5 calls' targets and check the card
names/points to each (ce-a5 U8). Usage: a5_u8_fault_check.py CALLS.jsonl.gz CARD.md [--sessions id,id] [--all]
Targets: Read/Edit paths. Shell/Grep/Glob/Agent calls carry no state-derivable path -> TASK (not state-derived).
Planning/matrix/vault-spec paths are STATE targets: COVERED if the card names the path, its dir, or its basename; else FAULT.
Non-planning repo files (src/, config/scripts, tests) are TASK targets: derived from the task prompt, not from STATE."""
import collections, gzip, json, re, sys

def norm(p):
    p = (p or '').replace('\\', '/')
    return re.sub(r'^.*orca-dws-wt/', '', p)

def classify(kind, p, card):
    if kind == 'T':
        return 'TASK', p
    q = norm(p)
    if re.search(r'(^|/)\.planning/|completion-matrix|(^|/)(STATE|ROADMAP|MATRIX|MISSION)\.md$|RESUMPTION|\.planning', q):
        base = q.split('/')[-1]
        parts = q.split('/')
        ok = (q in card) or (base in card)
        if not ok and 'phases' in parts:
            d = parts[parts.index('phases') + 1] if len(parts) > parts.index('phases') + 1 else ''
            ok = bool(d) and d in card and '.planning/workstreams/dws/phases/' in card
        return ('COVERED' if ok else 'FAULT'), q
    return 'TASK', q

def targets(c):
    t = [('R', p) for p in c['reads']] + [('E', p) for p in c['edits']]
    if c['sh'] or c['tools'] and not t:
        t.append(('T', (c['sh'] or ','.join(c['tools']))[:60]))
    return t

def main():
    calls_p, card_p = sys.argv[1], sys.argv[2]
    card = open(card_p).read()
    by = collections.defaultdict(list)
    for l in gzip.open(calls_p, 'rt'):
        c = json.loads(l); by[c['session']].append(c)
    for s in by: by[s].sort(key=lambda c: c['seq'])
    want = None
    if '--sessions' in sys.argv:
        want = sys.argv[sys.argv.index('--sessions') + 1].split(',')
    tot = collections.Counter(); faults = []; replaced = 0; reads = 0
    for s, cs in sorted(by.items()):
        if want and s not in want: continue
        for i, c in enumerate(cs):
            if not any(re.search(r'workstreams/dws/STATE\.md$', norm(p)) for p in c['reads']): continue
            reads += 1; bad = 0
            for n in cs[i + 1:i + 6]:
                for k, p in targets(n):
                    v, q = classify(k, p, card); tot[v] += 1
                    if v == 'FAULT': bad += 1; faults.append((s[:12], i, q))
                    if want: print(f'  {s[:12]}@{i} {v:7} {k} {q}')
            replaced += (bad == 0)
    print(f'state_reads={reads} replaced_no_fault={replaced} targets={dict(tot)}')
    for f in faults[:40]: print('FAULT', *f)
    return 0

if __name__ == '__main__':
    sys.exit(main())
