#!/usr/bin/env python3
"""a5_trace.py -- DWS trace corpus -> typed call table, provenance labels, flamegraph report (ce-a5 U1). stdlib only.

Usage: a5_trace.py --corpus DIR --repo DWS_REPO --out A_DIR      (writes A/data/calls.jsonl.gz, A/data/sessions.json, A/TRACE-REPORT.md)

Unit of "session": one transcript file (a main session or one subagent file); `parent` is the top-level session id.
Call: one assistant API call = unique (message.id, requestId) over the whole corpus (first file in sorted path order wins).
Streamed lines of one call share that key; their tool_use blocks are joined (by tool_use id, in line order).
ctx = input + cache_read + cache_write taken from the first streamed line; out = max output_tokens over its lines.
err = any tool_use of the call got a tool_result with is_error.

PROVENANCE LABELS -- a PROXY: each label is a deterministic rule outcome, not ground truth about intent.
First matching rule wins, in this priority:
  1 DELEGATION  tool in {Agent, Task, SendMessage}
  2 MUTATION    tool in {Edit, Write, MultiEdit, NotebookEdit} or shell command containing `git commit`
  3 RECOVERY    one of the previous 2 calls of the same session has err (and 1-2 did not match)
  4 STATE_READ  a Read target matches .planning/, STATE.md, ROADMAP.md or completion-matrix
  5 REDISCOVERY a Read target was already read earlier in the same session and that path has had no Edit/Write since
  6 CONTROL_LOOP shell command has sleep / Start-Sleep / until / while / poll / watch / a `status` word (not `git status`),
                or tool Monitor
  7 PROOF       shell command has test / tests / vitest / pytest / jest / e2e / playwright / tsc / typecheck / lint / check / verify
  8 NOVELTY     everything else
poll flag = the CONTROL_LOOP shell/Monitor rule; read-once state is per session and counted over calls in table order.
"""
import argparse, collections, gzip, io, json, os, re, subprocess, sys

DELEG = {'Agent', 'Task', 'SendMessage'}
MUT = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}
SHELL = {'Bash', 'PowerShell'}
LABELS = ['STATE_READ', 'REDISCOVERY', 'CONTROL_LOOP', 'PROOF', 'MUTATION', 'RECOVERY', 'DELEGATION', 'NOVELTY']
RE_STATE = re.compile(r'(\.planning/|(^|/)STATE\.md$|(^|/)ROADMAP\.md$|completion-matrix)')
RE_POLL = re.compile(r'(^|[\s;|&(])(sleep|Start-Sleep|until|while|watch)\b|\bpoll|(?<!git )\bstatus\b', re.I)
RE_PROOF = re.compile(r'\b(tests?|vitest|pytest|jest|e2e|playwright|tsc|typecheck|lint|check|verify)\b', re.I)
RE_COMMIT = re.compile(r'\bgit\s+commit\b')


def dedupe_key(m, o):
    return (m.get('id'), o.get('requestId'))


def norm_path(p):
    p = (p or '').replace('\\', '/')
    return re.sub(r'^.*orca-dws-wt/', '', p)


def shell_head(c):
    c = re.sub(r"^\$\w+\s*=\s*'[^']*';?\s*", '', c.strip())
    return ' '.join(re.findall(r"[\w./:-]+", c)[:3])[:60]


def iter_files(root):
    out = []
    for d, ds, fs in os.walk(root):
        ds.sort()
        for f in sorted(fs):
            if f.endswith('.jsonl'):
                out.append(os.path.join(d, f))
    return sorted(out)


def read_meta(path):
    mp = path[:-6] + '.meta.json'
    try:
        with open(mp, encoding='utf-8') as fh:
            return json.load(fh).get('agentType') or 'unknown'
    except Exception:
        return 'unknown'


def extract(corpus):
    """-> list of call rows (unlabelled), deterministic order."""
    seen = set()
    rows = []
    for f in iter_files(corpus):
        rel = os.path.relpath(f, corpus).replace(os.sep, '/')
        sub = '/subagents/' in '/' + rel
        sid = os.path.basename(f)[:-6]
        parent = rel.split('/')[0] if sub else sid
        agent = read_meta(f) if sub else 'main'
        calls = collections.OrderedDict()
        errs = {}
        with open(f, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                t = o.get('type')
                m = o.get('message')
                if not isinstance(m, dict):
                    continue
                if t == 'user':
                    c = m.get('content')
                    if isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get('type') == 'tool_result':
                                errs[b.get('tool_use_id')] = bool(b.get('is_error'))
                    continue
                if t != 'assistant':
                    continue
                key = dedupe_key(m, o)
                if key in seen and key not in calls:
                    continue
                u = m.get('usage') or {}
                if key not in calls:
                    calls[key] = {'model': m.get('model'), 'ts': o.get('timestamp'),
                                  'in': u.get('input_tokens') or 0, 'cr': u.get('cache_read_input_tokens') or 0,
                                  'cw': u.get('cache_creation_input_tokens') or 0, 'out': 0, 'tu': collections.OrderedDict()}
                e = calls[key]
                e['out'] = max(e['out'], u.get('output_tokens') or 0)
                for b in (m.get('content') or []):
                    if isinstance(b, dict) and b.get('type') == 'tool_use':
                        e['tu'].setdefault(b.get('id') or ('anon%d' % len(e['tu'])), b)
        for seq, (key, e) in enumerate(calls.items()):
            seen.add(key)
            tools, reads, edits, cmds, err = [], [], [], [], False
            for tid, b in e['tu'].items():
                n = b.get('name')
                tools.append(n)
                inp = b.get('input') or {}
                if n == 'Read':
                    reads.append(norm_path(inp.get('file_path')))
                elif n in MUT:
                    edits.append(norm_path(inp.get('file_path') or inp.get('notebook_path')))
                elif n in SHELL:
                    cmds.append(inp.get('command') or '')
                if errs.get(tid):
                    err = True
            cmd = '\n'.join(cmds)
            rows.append({
                'session': sid, 'parent': parent, 'side': 'subagent' if sub else 'main', 'agent': agent, 'seq': seq,
                'model': e['model'], 'ts': e['ts'], 'ctx': e['in'] + e['cr'] + e['cw'], 'in': e['in'], 'cr': e['cr'],
                'cw': e['cw'], 'out': e['out'], 'tools': tools, 'reads': reads, 'edits': edits,
                'sh': shell_head(cmds[0]) if cmds else '', 'cmd': cmd[:160].replace('\n', ' ; '),
                'poll': bool(RE_POLL.search(cmd)) or 'Monitor' in tools,
                'proof': bool(RE_PROOF.search(cmd)), 'commit': bool(RE_COMMIT.search(cmd)),
                'sleep1': bool(re.search(r'\bsleep\s+1\b', cmd)), 'err': err})
    return rows


def label_rows(rows):
    """Adds 'label' in place (rows grouped by session, in seq order)."""
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r['session'], []).append(r)
    for sid, rs in by.items():
        read_dirty = {}  # path -> True if read and not edited since
        for i, r in enumerate(rs):
            tools = set(r['tools'])
            rediscov = any(read_dirty.get(p) for p in r['reads'])
            if tools & DELEG:
                lab = 'DELEGATION'
            elif tools & MUT or r['commit']:
                lab = 'MUTATION'
            elif any(x['err'] for x in rs[max(0, i - 2):i]):
                lab = 'RECOVERY'
            elif any(RE_STATE.search(p) for p in r['reads']):
                lab = 'STATE_READ'
            elif rediscov:
                lab = 'REDISCOVERY'
            elif r['poll']:
                lab = 'CONTROL_LOOP'
            elif r['proof']:
                lab = 'PROOF'
            else:
                lab = 'NOVELTY'
            r['label'] = lab
            for p in r['edits']:
                read_dirty[p] = False
            for p in r['reads']:
                read_dirty[p] = True
    return rows


def session_table(rows):
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r['session'], []).append(r)
    out = {}
    for sid in sorted(by):
        rs = by[sid]
        lc = collections.Counter(r['label'] for r in rs)
        out[sid] = {'parent': rs[0]['parent'], 'side': rs[0]['side'], 'agent': rs[0]['agent'], 'calls': len(rs),
                    'first_ctx': rs[0]['ctx'], 'last_ctx': rs[-1]['ctx'], 'ctx_sum': sum(r['ctx'] for r in rs),
                    'out_sum': sum(r['out'] for r in rs), 'models': sorted({r['model'] for r in rs if r['model']}),
                    't0': rs[0]['ts'], 't1': rs[-1]['ts'], 'errors': sum(r['err'] for r in rs),
                    'labels': dict(sorted(lc.items()))}
    return out


def write_data(rows, sessions, data_dir):
    os.makedirs(data_dir, exist_ok=True)
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0, filename='') as gz:
        for r in rows:
            gz.write((json.dumps(r, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8'))
    with open(os.path.join(data_dir, 'calls.jsonl.gz'), 'wb') as fh:
        fh.write(buf.getvalue())
    with open(os.path.join(data_dir, 'sessions.json'), 'w', encoding='utf-8') as fh:
        json.dump(sessions, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write('\n')


# ---------------- matrix history ----------------
def strip_jsonc(s):
    out, i, n, instr = [], 0, len(s), False
    while i < n:
        c = s[i]
        if instr:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(s[i + 1]); i += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True; out.append(c)
        elif c == '/' and s[i:i + 2] == '//':
            while i < n and s[i] != '\n':
                i += 1
            continue
        elif c == '/' and s[i:i + 2] == '/*':
            j = s.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        else:
            out.append(c)
        i += 1
    return re.sub(r',(\s*[}\]])', r'\1', ''.join(out))


def matrix_states(text):
    states = {}

    def walk(x):
        if isinstance(x, dict):
            if 'id' in x and 'state' in x:
                states[str(x['id'])] = x['state']
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(json.loads(strip_jsonc(text)))
    return states


def matrix_history(repo, path='config/dws-completion-matrix.jsonc'):
    log = subprocess.run(['git', '-C', repo, 'log', '--reverse', '--format=%H %cI', '--', path],
                         capture_output=True, text=True, check=True).stdout.split('\n')
    hist, prev = [], {}
    for ln in log:
        if not ln.strip():
            continue
        h, d = ln.split()
        txt = subprocess.run(['git', '-C', repo, 'show', '%s:%s' % (h, path)], capture_output=True, text=True,
                             check=True).stdout
        cur = matrix_states(txt)
        ch = sum(1 for k, v in cur.items() if prev.get(k) != v) if prev else 0
        hist.append({'commit': h[:9], 'date': d, 'rows': len(cur), 'changes': ch})
        prev = cur
    return hist


def utc_key(iso):
    """ISO-8601 with offset or Z -> sortable UTC string."""
    from datetime import datetime, timezone
    d = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return d.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')


# ---------------- report ----------------
def pct(sorted_list, q):
    return sorted_list[min(len(sorted_list) - 1, int(len(sorted_list) * q))] if sorted_list else None


def fmt(n):
    return '{:,}'.format(int(n))


def table(head, body):
    return '\n'.join(['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)] + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in body])


def headline(rows, sessions):
    ctxs = sorted(r['ctx'] for r in rows)
    tot = sum(ctxs)
    sub = [r for r in rows if r['side'] == 'subagent']
    sl = sorted(sessions.values(), key=lambda s: -s['ctx_sum'])
    floor = sum(s['first_ctx'] * s['calls'] for s in sl)
    firsts = sorted(s['first_ctx'] for s in sl)
    rd = collections.Counter(p for r in rows for p in r['reads'])
    h = {'sessions_files': len(sl), 'calls': len(rows), 'ctx_total': tot, 'ctx_p50': pct(ctxs, .5), 'ctx_p90': pct(ctxs, .9),
         'sub_call_share': round(len(sub) / len(rows), 4) if rows else None,
         'sub_ctx_share': round(sum(r['ctx'] for r in sub) / tot, 4) if tot else None,
         'sessions_gt60': sum(1 for s in sl if s['calls'] > 60),
         'tokshare_gt60': round(sum(s['ctx_sum'] for s in sl if s['calls'] > 60) / tot, 4) if tot else None,
         'sessions_gt150': sum(1 for s in sl if s['calls'] > 150),
         'tokshare_gt150': round(sum(s['ctx_sum'] for s in sl if s['calls'] > 150) / tot, 4) if tot else None,
         'first_call_p50': pct(firsts, .5), 'floor_tokens_sum_first_x_calls': floor, 'floor_share_sum_first_x_calls': round(floor / tot, 4) if tot else None,
         'reads': sum(rd.values()), 'distinct_read_paths': len(rd),
         'STATE.md reads': sum(v for p, v in rd.items() if p.endswith('STATE.md')),
         'matrix reads': rd.get('config/dws-completion-matrix.jsonc', 0),
         'ROADMAP reads': sum(v for p, v in rd.items() if p.endswith('ROADMAP.md')),
         'sleep 1 (shell head)': sum(1 for r in rows if r['sh'] == 'sleep 1'),
         'poll loops (until)': sum(1 for r in rows if re.search(r'\buntil\b', r['cmd'])),
         'poll-flag calls (all rules)': sum(1 for r in rows if r['poll']),
         'Monitor tool calls': sum(1 for r in rows if 'Monitor' in r['tools']),
         'floor_tokens_p50xcalls': (pct(firsts, .5) or 0) * len(rows),
         'floor_share_p50xcalls': round((pct(firsts, .5) or 0) * len(rows) / tot, 4) if tot else None,
         'calls_without_tool_use (joined)': sum(1 for r in rows if not r['tools']),
         'tools_per_call': round(sum(len(r['tools']) for r in rows) / len(rows), 3) if rows else None}
    return h


def ngram_rows(rows, n, top=30):
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r['session'], []).append(r)
    cnt, ctxsum = collections.Counter(), collections.Counter()
    for rs in by.values():
        toks = [r['tools'][0] if r['tools'] else '(none)' for r in rs]
        for i in range(len(rs) - n + 1):
            g = tuple(toks[i:i + n])
            cnt[g] += 1
            ctxsum[g] += sum(x['ctx'] for x in rs[i:i + n]) / n
    items = [(g, c, ctxsum[g] / c) for g, c in cnt.items()]
    items.sort(key=lambda x: (-x[1] * x[2], x[0]))
    return [(' > '.join(g), c, fmt(m), fmt(c * m)) for g, c, m in items[:top]]


def context_rent(rows, top=30):
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r['session'], []).append(r)
    rent, cnt = collections.Counter(), collections.Counter()
    for rs in by.values():
        n = len(rs)
        for i, r in enumerate(rs[:-1]):
            if not r['reads']:
                continue
            growth = max(0, rs[i + 1]['ctx'] - r['ctx']) / len(r['reads'])
            for p in r['reads']:
                rent[p] += growth * (n - i - 1)
                cnt[p] += 1
    items = sorted(rent.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return [(p, cnt[p], fmt(v)) for p, v in items], sum(rent.values())


def report(rows, sessions, hist, corpus_name):
    tot = sum(r['ctx'] for r in rows)
    L = ['# TRACE-REPORT (ce-a5 U1)', '',
         'Generated by tools/a5_trace.py from %s. Labels are a PROXY: a rule outcome (see tool header), not ground truth.' % corpus_name,
         'Tokens = processed ctx (input + cache read + cache write) summed over calls.', '', '## 0. Headline', '']
    h = headline(rows, sessions)
    L.append(table(['metric', 'value'], [(k, fmt(v) if isinstance(v, int) else v) for k, v in h.items()]))
    L += ['', '## 1. Tokens by provenance label', '']
    lc = collections.OrderedDict((l, [0, 0, 0]) for l in LABELS)
    for r in rows:
        x = lc[r['label']]; x[0] += 1; x[1] += r['ctx']; x[2] += r['out']
    L.append(table(['label', 'calls', 'ctx tokens', 'share', 'output tokens'],
                   [(l, fmt(v[0]), fmt(v[1]), '%.1f%%' % (100.0 * v[1] / tot), fmt(v[2])) for l, v in lc.items()]))
    L += ['', '## 2. Tokens by session-length bucket (calls per transcript file)', '']
    bk = collections.OrderedDict((b, [0, 0, 0]) for b in ['<=20', '21-60', '61-150', '>150'])
    for s in sessions.values():
        n = s['calls']
        b = '<=20' if n <= 20 else '21-60' if n <= 60 else '61-150' if n <= 150 else '>150'
        bk[b][0] += 1; bk[b][1] += n; bk[b][2] += s['ctx_sum']
    L.append(table(['bucket', 'sessions', 'calls', 'ctx tokens', 'share'],
                   [(b, v[0], fmt(v[1]), fmt(v[2]), '%.1f%%' % (100.0 * v[2] / tot)) for b, v in bk.items()]))
    L += ['', '## 3. First-call floor distribution (ctx of the first call of each file)', '']
    body = []
    groups = [('all', list(sessions.values())), ('main', [s for s in sessions.values() if s['side'] == 'main']),
              ('subagent', [s for s in sessions.values() if s['side'] == 'subagent'])]
    for a in sorted({s['agent'] for s in sessions.values() if s['side'] == 'subagent'}):
        groups.append(('agent:' + a, [s for s in sessions.values() if s['agent'] == a]))
    for name, ss in groups:
        f = sorted(s['first_ctx'] for s in ss)
        if f:
            body.append((name, len(f), fmt(pct(f, 0)), fmt(pct(f, .1)), fmt(pct(f, .5)), fmt(pct(f, .9)), fmt(f[-1]),
                         fmt(sum(s['first_ctx'] * s['calls'] for s in ss))))
    L.append(table(['group', 'files', 'min', 'p10', 'p50', 'p90', 'max', 'floor tokens (first x calls)'], body))
    rb, rtot = context_rent(rows)
    L += ['', '## 4. Context rent by object (top 30 read paths)', '',
          'Approximation: object size = ctx growth on the call after the read (split over reads of that call, clamped >= 0); '
          'rent = size x calls remaining in the session (resident until session end; compaction ignored). Total rent over all paths: %s.' % fmt(rtot), '']
    L.append(table(['path', 'reads', 'rent tokens'], rb))
    for n in (3, 5):
        L += ['', '## 5.%d Top 30 tool-sequence %d-grams (first tool of each call) by count x mean ctx' % (n // 2, n), '']
        L.append(table(['gram', 'count', 'mean ctx', 'count x mean ctx'], ngram_rows(rows, n)))
    L += ['', '## 6. Calls per matrix step (matrix git history, D/orca-dws)', '',
          'changes = rows whose `state` differs from the previous commit of config/dws-completion-matrix.jsonc (first commit = baseline, 0). '
          'Window = calls with ts (UTC) in (previous commit time, this commit time]; calls before the first commit join the first window; '
          'calls after the last commit are listed separately.', '']
    wins, keys = [], [utc_key(x['date']) for x in hist]
    body, prev = [], ''
    for i, x in enumerate(hist):
        lo = prev if i else ''
        sel = [r for r in rows if r['ts'] and lo < utc_key(r['ts']) <= keys[i]]
        prev = keys[i]
        body.append((x['commit'], x['date'], x['rows'], x['changes'], fmt(len(sel)), fmt(sum(r['ctx'] for r in sel)),
                     ('%.1f' % (len(sel) / x['changes'])) if x['changes'] else 'n/a'))
    after = [r for r in rows if r['ts'] and hist and utc_key(r['ts']) > keys[-1]]
    L.append(table(['commit', 'date', 'rows', 'state changes', 'calls in window', 'ctx tokens', 'calls per change'], body))
    ch = sum(x['changes'] for x in hist)
    inw = sum(int(b[4].replace(',', '')) for b in body)
    L += ['', 'Total state changes %d; calls in windows %s; calls after last commit %s. Calls per state change overall: %s.'
          % (ch, fmt(inw), fmt(len(after)), ('%.1f' % (inw / ch)) if ch else 'n/a')]
    return '\n'.join(L) + '\n', h


def build(corpus, repo, out):
    rows = label_rows(extract(corpus))
    sessions = session_table(rows)
    write_data(rows, sessions, os.path.join(out, 'data'))
    hist = matrix_history(repo) if repo else []
    text, h = report(rows, sessions, hist, 'corpus ' + os.path.basename(corpus.rstrip('/')))
    with open(os.path.join(out, 'TRACE-REPORT.md'), 'w', encoding='utf-8') as fh:
        fh.write(text)
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--repo', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    h = build(a.corpus, a.repo, a.out)
    print(json.dumps(h, indent=1))


if __name__ == '__main__':
    main()
