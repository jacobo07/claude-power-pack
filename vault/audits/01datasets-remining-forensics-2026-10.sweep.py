"""W0 sweep: which sessions touched 01_Datasets. Bounded, read-only."""
import json, os, re, sys, time, glob
from collections import defaultdict

ROOT = r'C:\Users\User\.claude\projects'
DEADLINE = time.time() + 150
dirs = [d for d in os.listdir(ROOT)
        if re.search(r'TUA-X|wt-creative|wt-cw|Apps--wt', d, re.I)]
pat = re.compile(r'01_Datasets[^"\\]*(?:\\\\[^"\\]*)*', re.I)
rows = []
for d in dirs:
    for f in glob.glob(os.path.join(ROOT, d, '**', '*.jsonl'), recursive=True):
        if time.time() > DEADLINE:
            print('DEADLINE HIT', file=sys.stderr); break
        files = set(); first = last = None; tok = 0; calls = 0; ads = 0
        try:
            with open(f, encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    ts = o.get('timestamp')
                    m = o.get('message') or {}
                    u = m.get('usage') if isinstance(m, dict) else None
                    if u:
                        tok += (u.get('input_tokens') or 0) + (u.get('output_tokens') or 0) \
                            + (u.get('cache_creation_input_tokens') or 0)
                    c = m.get('content') if isinstance(m, dict) else None
                    if o.get('type') == 'assistant' and isinstance(c, list):
                        for it in c:
                            if it.get('type') == 'tool_use':
                                s = json.dumps(it.get('input', {}))
                                if '01_Datasets' in s:
                                    calls += 1
                                    first = first or ts; last = ts
                                    inp = it['input']
                                    p = inp.get('file_path') or inp.get('path')
                                    if p and '01_Datasets' in p:
                                        files.add(p.replace('\\\\', '\\'))
                                    else:
                                        for mm in re.findall(r'[A-Za-z]:\\\\[^"]*?01_Datasets[^"]*', s):
                                            files.add(mm.replace('\\\\', '\\'))
                                    if re.search(r'extracted\\\\?Ads', s, re.I):
                                        ads += 1
        except OSError as e:
            print('ERR', f, e, file=sys.stderr); continue
        if calls:
            rows.append((os.path.relpath(f, os.path.join(ROOT, d))[:8] + ('/sub:' + os.path.basename(f)[-14:-6] if 'subagents' in f else ''), d[-40:], first, last, calls, len(files), ads, tok, files))

rows.sort(key=lambda r: r[2] or '')
seen = set()
sys.stdout.reconfigure(encoding='utf-8')
print('session|dir|first|last|calls|distinct_paths|ads_calls|tokens|paths_seen_earlier')
for r in rows:
    prior = len(r[8] & seen)
    seen |= r[8]
    print('|'.join(map(str, (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], prior))))
print('dirs scanned:', len(dirs), 'sessions with hits:', len(rows))
