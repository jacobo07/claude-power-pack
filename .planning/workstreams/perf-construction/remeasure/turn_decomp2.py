"""Interval-union decomposition of laptop turn wall time (read-only).

Per main-thread turn (rows between system/turn_duration markers), build intervals:
  API    [api-request ts (querySource repl_main_thread), last assistant ts with that requestRef]
  HOOK   [ts - durationMs, ts] per hook attachment / stop_hook_summary hookInfo (event kept)
  AGENT  [tool_use ts, tool_result ts] for Agent/Task tools (subagent time)
  TOOL   same for every other tool (includes the Pre/Post hooks that ran around it)
Each category is reported as union coverage / turn wall (each <= 100%). Exclusive attribution uses priority
HOOK > API > AGENT > TOOL > idle, so the exclusive shares sum to 100%.
Usage: turn_decomp2.py <projects_root> <days> <max_files>
"""
import json, os, sys, glob, time, statistics as st
from datetime import datetime

def ts(s):
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()
    except Exception:
        return None

def union(iv):
    iv = sorted((a, b) for a, b in iv if b > a)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out

def length(u):
    return sum(b - a for a, b in u)

def subtract(u, v):
    """u minus v, both unions."""
    res = []
    for a, b in u:
        cur = a
        for c, d in v:
            if d <= cur or c >= b:
                continue
            if c > cur:
                res.append([cur, c])
            cur = max(cur, d)
        if cur < b:
            res.append([cur, b])
    return res

def clip(u, lo, hi):
    return [[max(a, lo), min(b, hi)] for a, b in u if min(b, hi) > max(a, lo)]

def turns_of(path):
    out, cur = [], []
    with open(path, encoding='utf-8', errors='replace') as f:
        for l in f:
            try:
                d = json.loads(l)
            except Exception:
                continue
            if d.get('isSidechain'):
                continue
            cur.append(d)
            if d.get('type') == 'system' and d.get('subtype') == 'turn_duration':
                out.append(cur); cur = []
    return out

def decomp(turn):
    end = turn[-1]
    total_ms = end.get('durationMs'); t_end = ts(end.get('timestamp') or '')
    if not isinstance(total_ms, (int, float)) or total_ms <= 0 or not t_end:
        return None
    t0 = t_end - total_ms / 1000
    req_t, req_last, hooks, uses, agent, tool = {}, {}, {}, {}, [], []
    for d in turn:
        t = ts(d.get('timestamp') or '')
        if not t:
            continue
        typ = d.get('type')
        if typ == 'api-request' and d.get('querySource', 'repl_main_thread') == 'repl_main_thread':
            req_t[d.get('id')] = t
        elif typ == 'assistant':
            r = d.get('requestRef')
            if r:
                req_last[r] = max(req_last.get(r, 0), t)
            c = (d.get('message') or {}).get('content')
            for b in c if isinstance(c, list) else []:
                if isinstance(b, dict) and b.get('type') == 'tool_use':
                    uses[b.get('id')] = (t, b.get('name'))
        elif typ == 'user':
            c = (d.get('message') or {}).get('content')
            for b in c if isinstance(c, list) else []:
                if isinstance(b, dict) and b.get('type') == 'tool_result' and b.get('tool_use_id') in uses:
                    st_, name = uses.pop(b.get('tool_use_id'))
                    (agent if name in ('Agent', 'Task') else tool).append((st_, t))
        elif typ == 'attachment':
            a = d.get('attachment') or {}
            if str(a.get('type', '')).startswith('hook_') and isinstance(a.get('durationMs'), (int, float)):
                hooks.setdefault(a.get('hookEvent') or '?', []).append((t - a['durationMs'] / 1000, t))
        elif typ == 'system' and d.get('subtype') == 'stop_hook_summary':
            for i in d.get('hookInfos') or []:
                if isinstance(i.get('durationMs'), (int, float)):
                    hooks.setdefault('Stop', []).append((t - i['durationMs'] / 1000, t))
    api = [(req_t[r], req_last[r]) for r in req_t if r in req_last]
    if not api:
        return None
    U = {k: clip(union(v), t0, t_end) for k, v in
         {'api': api, 'agent': agent, 'tool': tool,
          'hook': [x for v in hooks.values() for x in v]}.items()}
    ev = {e: length(clip(union(v), t0, t_end)) for e, v in hooks.items()}
    total = t_end - t0
    excl = {}
    taken = []
    for k in ('hook', 'api', 'agent', 'tool'):
        part = subtract(U[k], union(taken))
        excl[k] = length(part)
        taken += [tuple(x) for x in part]
    excl['idle'] = max(0.0, total - sum(excl.values()))
    return {'total': total, 'cov': {k: length(v) for k, v in U.items()}, 'excl': excl, 'ev': ev, 't_end': t_end}

def main():
    root, days, cap = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
    cutoff = time.time() - days * 86400
    files = sorted((p for p in glob.glob(os.path.join(root, '*', '*.jsonl')) if os.path.getmtime(p) >= cutoff),
                   key=os.path.getmtime, reverse=True)[:cap]
    res = []
    for p in files:
        try:
            res += [r for r in (decomp(t) for t in turns_of(p)) if r]
        except Exception:
            pass
    # optional 4th/5th args: ISO window [since, until) on each turn's END time, so a long session's old turns
    # never count in a later window (file mtime alone admitted them)
    if len(sys.argv) > 5:
        lo = datetime.fromisoformat(sys.argv[4].replace('Z', '+00:00')).timestamp()
        hi = datetime.fromisoformat(sys.argv[5].replace('Z', '+00:00')).timestamp()
        res = [r for r in res if lo <= r['t_end'] < hi]
        print('window', sys.argv[4], '->', sys.argv[5])
    print(f'files={len(files)} turns={len(res)} (last {days} d, newest {cap} files, main thread)')
    def report(rows, label):
        T = sum(r['total'] for r in rows)
        ex = {k: sum(r['excl'][k] for r in rows) / T * 100 for k in ('hook', 'api', 'agent', 'tool', 'idle')}
        cv = {k: sum(r['cov'][k] for r in rows) / T * 100 for k in ('hook', 'api', 'agent', 'tool')}
        evs = {}
        for r in rows:
            for e, s in r['ev'].items():
                evs[e] = evs.get(e, 0) + s
        print(f'{label}: n={len(rows)} wall={T/3600:.1f} h')
        print('  EXCLUSIVE share: ' + '  '.join(f'{k}={v:.1f}%' for k, v in ex.items()))
        print('  coverage       : ' + '  '.join(f'{k}={v:.1f}%' for k, v in cv.items()))
        print('  hook events    : ' + '  '.join(f'{e}={s/T*100:.1f}%' for e, s in sorted(evs.items(), key=lambda x: -x[1])[:6]))
    report(res, 'ALL TURNS')
    res.sort(key=lambda r: r['total'])
    report(res[: len(res) // 2], 'FASTER HALF')
    report(res[-max(1, len(res) // 10):], 'SLOWEST 10%')
    no_agent = [r for r in res if r['cov']['agent'] == 0]
    report(no_agent, 'TURNS WITHOUT SUBAGENTS')
    print('per-turn median s: total=%.1f hook_excl=%.1f api_excl=%.1f tool_excl=%.1f idle=%.1f' % (
        st.median(r['total'] for r in res), st.median(r['excl']['hook'] for r in res), st.median(r['excl']['api'] for r in res),
        st.median(r['excl']['tool'] for r in res), st.median(r['excl']['idle'] for r in res)))

main()
