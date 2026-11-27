"""Per-hook-command cost over laptop transcripts (read-only). Usage: hook_cost.py <root> <days> <max_files>"""
import json, os, sys, glob, time, re, statistics as st
from datetime import datetime
root, days, cap = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
# optional 4th/5th args: ISO window [since, until) on each hook row's own timestamp
WIN = None
if len(sys.argv) > 5:
    WIN = (datetime.fromisoformat(sys.argv[4].replace('Z', '+00:00')).timestamp(),
           datetime.fromisoformat(sys.argv[5].replace('Z', '+00:00')).timestamp())
    print('window', sys.argv[4], '->', sys.argv[5])
cutoff = time.time() - days * 86400
files = sorted((p for p in glob.glob(os.path.join(root, '*', '*.jsonl')) if os.path.getmtime(p) >= cutoff),
               key=os.path.getmtime, reverse=True)[:cap]
agg = {}
def short(cmd):
    m = re.findall(r'[\w\-.]+\.(?:js|py|ps1|cmd|sh|mjs)', cmd or '')
    return (m[-1] if m else (cmd or '?')[:40])
for p in files:
    try:
        for l in open(p, encoding='utf-8', errors='replace'):
            if '"durationMs"' not in l or ('hook_' not in l and 'stop_hook_summary' not in l):
                continue
            try:
                d = json.loads(l)
            except Exception:
                continue
            if WIN:
                try:
                    tt = datetime.fromisoformat(str(d.get('timestamp')).replace('Z', '+00:00')).timestamp()
                except Exception:
                    continue
                if not (WIN[0] <= tt < WIN[1]):
                    continue
            a = d.get('attachment') or {}
            items = []
            if str(a.get('type', '')).startswith('hook_') and isinstance(a.get('durationMs'), (int, float)):
                items.append((a.get('hookEvent'), a.get('command'), a['durationMs'], bool(a.get('timedOut'))))
            if d.get('subtype') == 'stop_hook_summary':
                for i in d.get('hookInfos') or []:
                    if isinstance(i.get('durationMs'), (int, float)):
                        items.append(('Stop', i.get('command'), i['durationMs'], False))
            for ev, cmd, ms, to in items:
                k = (ev, short(cmd))
                e = agg.setdefault(k, {'n': 0, 'ms': [], 'to': 0})
                e['n'] += 1; e['ms'].append(ms); e['to'] += to
    except Exception:
        pass
tot = sum(sum(e['ms']) for e in agg.values())
print(f'files={len(files)} hook runs={sum(e["n"] for e in agg.values())} total hook-seconds={tot/1000:.0f} (sum, not wall)')
print(f'{"event":17} {"hook":38} {"runs":>6} {"median_ms":>9} {"p90_ms":>7} {"share":>6} {"timeouts":>8}')
for (ev, h), e in sorted(agg.items(), key=lambda x: -sum(x[1]['ms']))[:22]:
    v = sorted(e['ms'])
    print(f'{str(ev):17} {h[:38]:38} {e["n"]:6} {st.median(v):9.0f} {v[int(len(v)*0.9)]:7.0f} {sum(v)/tot*100:5.1f}% {e["to"]:8}')
