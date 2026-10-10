"""Per-session shape of dws spend: calls per session, first/last context, share of tokens in long sessions."""
import json, glob, os, sys

root = os.path.expanduser('~/.claude/projects/C--Users-User-Apps-orca-dws-wt')
rows = []
for f in glob.glob(os.path.join(root, '**', '*.jsonl'), recursive=True):
    seen = set(); ctxs = []; models = set()
    for line in open(f, encoding='utf-8', errors='replace'):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get('type') != 'assistant':
            continue
        m = o.get('message') or {}
        k = (m.get('id'), o.get('requestId'))
        if k in seen:
            continue
        seen.add(k)
        u = m.get('usage') or {}
        ctxs.append((u.get('input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0))
        models.add(m.get('model'))
    if ctxs:
        rows.append({'f': os.path.basename(f), 'sub': 'subagents' in f, 'n': len(ctxs), 'first': ctxs[0],
                     'last': ctxs[-1], 'sum': sum(ctxs), 'models': sorted(x for x in models if x)})
rows.sort(key=lambda r: -r['sum'])
tot = sum(r['sum'] for r in rows)
buckets = {'<=20': 0, '21-60': 0, '61-150': 0, '>150': 0}
btok = dict.fromkeys(buckets, 0)
for r in rows:
    b = '<=20' if r['n'] <= 20 else '21-60' if r['n'] <= 60 else '61-150' if r['n'] <= 150 else '>150'
    buckets[b] += 1; btok[b] += r['sum']
first_floor = sorted(r['first'] for r in rows)
out = {'sessions': len(rows), 'tokens': tot,
       'sessions_by_len': buckets, 'token_share_by_len': {k: round(v / tot, 3) for k, v in btok.items()},
       'first_call_ctx_p50': first_floor[len(first_floor) // 2],
       'top10': rows[:10]}
with open(sys.argv[1], 'w', encoding='utf-8') as fh:
    json.dump(out, fh, indent=1)
