#!/usr/bin/env python3
"""KME token audit: scan Claude Code transcripts, attribute token usage.

Usage: kme_token_audit.py --host NAME --out out.json ROOT_DIR [ROOT_DIR ...]
Each ROOT_DIR is a ~/.claude/projects/<project> directory (or a projects root,
with --expand, in which case every child dir is scanned).
"""
import argparse, collections, json, os, re, sys

KME_RE = re.compile(r'KobiMapEngine|KobiiMapEngine|\bKME\b|\bkme[-_/\\]|mapengine|map_engine|KMEIP', re.I)
PATH_KME_RE = re.compile(r'kme|mapengine', re.I)


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for c in content:
            if isinstance(c, dict):
                if c.get('type') == 'text':
                    out.append(c.get('text', ''))
                elif c.get('type') == 'tool_result':
                    out.append(text_of(c.get('content')))
                elif c.get('type') == 'image':
                    out.append('[image]')
            elif isinstance(c, str):
                out.append(c)
        return '\n'.join(out)
    return ''


def user_text(sess, tx):
    sess['user_prompts'] += 1
    sess['user_chars'] += len(tx)
    h = len(KME_RE.findall(tx))
    sess['kme_hits'] += 3 * h
    # a human-typed prompt, not an expanded skill/command body or a pasted log
    if '<command-name>' not in tx[:400] and 'Base directory for this skill' not in tx[:200] and len(tx) < 20000:
        sess['user_kme_hits'] += h
    if not sess['first_prompt']:
        sess['first_prompt'] = tx[:200]


def tool_key(name, inp):
    if not isinstance(inp, dict):
        return name
    if name in ('Bash', 'PowerShell'):
        cmd = (inp.get('command') or '').strip().split('\n')[0]
        return f"{name}: {cmd[:110]}"
    if name in ('Read', 'Write', 'Edit', 'NotebookEdit'):
        return f"{name}: {inp.get('file_path', '')}"
    if name in ('Grep', 'Glob'):
        return f"{name}: {inp.get('pattern', '')[:80]} @ {inp.get('path', '')}"
    if name in ('Agent', 'Task'):
        return f"{name}: {inp.get('subagent_type', 'general')} / {inp.get('description', '')[:60]}"
    if name == 'Skill':
        return f"Skill: {inp.get('skill', '')}"
    return name


def scan_file(path, sess, observer=None, keep=None):
    """Accumulate one jsonl file into session dict `sess`."""
    # observer / keep are the additive hooks of kme_pillars (default None = the P0 behaviour, pinned byte-identical
    # by V-KMEP-AUDIT-BYTE-IDENTICAL): keep(path, o) -> False drops the line before anything reads it;
    # observer.on_line(path, o, call_index, sess) sees each kept line with the call index the residency loop uses;
    # observer.on_file_end(path, sess, order, calls, compact_points) runs once the file is fully accumulated.
    # scan_project(select=...) is a further additive hook of kme_pillars (default None = the P0 behaviour): a file the
    # select callable refuses is never opened, its session is still registered.
    calls = {}          # dedupe key -> record
    order = []          # dedupe keys in order (main thread residency)
    tools = {}          # tool_use_id -> (name, key)
    pending_results = []  # (key, name, chars, call_index_at_insert)
    is_sub = '/subagents/' in path.replace('\\', '/')
    compact_points = []
    with open(path, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:
                sess['bad_lines'] += 1
                continue
            if keep is not None and not keep(path, o):
                continue
            if observer is not None:
                observer.on_line(path, o, len(order), sess)
            t = o.get('type')
            ts = o.get('timestamp')
            if ts:
                sess['first'] = min(sess['first'] or ts, ts)
                sess['last'] = max(sess['last'] or ts, ts)
            if o.get('cwd') and not sess['cwd']:
                sess['cwd'] = o['cwd']
            if t == 'system' and (o.get('subtype') == 'compact_boundary'):
                sess['compactions'] += 1
                compact_points.append(len(order))
            if o.get('isCompactSummary'):
                sess['compact_summaries'] += 1
            if t == 'attachment':
                a = o.get('attachment') or {}
                k = a.get('type', '?')
                if a.get('hookName'):
                    k += ':' + str(a.get('hookName'))[:60]
                elif a.get('hookEvent'):
                    k += ':' + str(a.get('hookEvent'))
                n = len(json.dumps(a, ensure_ascii=False))
                sess['attach'][k][0] += 1
                sess['attach'][k][1] += n
                continue
            msg = o.get('message') or {}
            if t == 'assistant' and isinstance(msg, dict):
                u = msg.get('usage')
                content = msg.get('content') or []
                for c in content if isinstance(content, list) else []:
                    if not isinstance(c, dict):
                        continue
                    if c.get('type') == 'tool_use':
                        nm = c.get('name', '?')
                        tk = tool_key(nm, c.get('input'))
                        tools[c.get('id')] = (nm, tk)
                        sess['tool_calls'][nm] += 1
                        inp = json.dumps(c.get('input'), ensure_ascii=False)
                        sess['tool_input_chars'][nm] += len(inp)
                        h = len(KME_RE.findall(inp))
                        sess['kme_hits'] += h
                        sess['tool_uses'] += 1
                        if h:
                            sess['tool_uses_kme'] += 1
                        if nm in ('Agent', 'Task') and isinstance(c.get('input'), dict):
                            sess['agent_models'][c['input'].get('model') or 'inherit'] += 1
                        if nm == 'Read' and isinstance(c.get('input'), dict):
                            sess['reads'][c['input'].get('file_path', '')] += 1
                    elif c.get('type') == 'text':
                        sess['kme_hits'] += len(KME_RE.findall(c.get('text', '')))
                        sess['assistant_text_chars'] += len(c.get('text', ''))
                    elif c.get('type') == 'thinking':
                        sess['thinking_chars'] += len(c.get('thinking', ''))
                if isinstance(u, dict):
                    key = (msg.get('id') or o.get('uuid'), o.get('requestId'))
                    rec = calls.get(key)
                    cc = u.get('cache_creation') or {}
                    vals = dict(
                        inp=u.get('input_tokens') or 0,
                        cw=u.get('cache_creation_input_tokens') or 0,
                        cw1h=cc.get('ephemeral_1h_input_tokens') or 0,
                        cw5m=cc.get('ephemeral_5m_input_tokens') or 0,
                        cr=u.get('cache_read_input_tokens') or 0,
                        out=u.get('output_tokens') or 0,
                    )
                    if rec is None:
                        calls[key] = dict(vals, model=msg.get('model', '?'), ts=ts)
                        order.append(key)
                    else:
                        for k2, v in vals.items():
                            rec[k2] = max(rec[k2], v)
            elif t == 'user' and isinstance(msg, dict):
                content = msg.get('content')
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get('type') == 'tool_result':
                            nm, tk = tools.get(c.get('tool_use_id'), ('?', '?'))
                            n = len(text_of(c.get('content')))
                            sess['tool_result_chars'][nm] += n
                            pending_results.append((tk, nm, n, len(order)))
                        elif isinstance(c, dict) and c.get('type') == 'text' and not o.get('isMeta'):
                            user_text(sess, c.get('text', ''))
                elif isinstance(content, str) and not o.get('isMeta'):
                    user_text(sess, content)
    # residency: a tool result stays in context for every later call until the next compaction
    for tk, nm, n, idx in pending_results:
        nxt = [p for p in compact_points if p > idx]
        end = nxt[0] if nxt else len(order)
        resid = max(0, end - idx)
        sess['residency'].append((tk, nm, n, resid, n * resid))
    for key in order:
        r = calls[key]
        bucket = 'sub' if is_sub else 'main'
        m = r['model']
        if m == '<synthetic>':
            continue
        tot = sess['by_model'].setdefault(m, collections.Counter())
        for k2 in ('inp', 'cw', 'cw1h', 'cw5m', 'cr', 'out'):
            tot[k2] += r[k2]
            sess[bucket][k2] += r[k2]
        tot['calls'] += 1
        sess[bucket]['calls'] += 1
        ctx = r['inp'] + r['cw'] + r['cr']
        sess['max_ctx'] = max(sess['max_ctx'], ctx)
        if not is_sub and 'first_ctx' not in sess:
            sess['first_ctx'] = ctx  # context before any work: the per-session fixed overhead
        day = (r['ts'] or '')[:10]
        dd = sess['by_day'].setdefault(day, collections.Counter())
        for k2 in ('inp', 'cw', 'cr', 'out', 'calls'):
            dd[k2] += r[k2] if k2 != 'calls' else 1
        if ctx >= 150000:
            sess['calls_over_150k'] += 1
    if is_sub:
        sess['subagent_files'] += 1
    if observer is not None:
        observer.on_file_end(path, sess, order, calls, compact_points)


def new_sess(proj, sid):
    return dict(project=proj, session=sid, cwd=None, first=None, last=None, first_prompt='',
                main=collections.Counter(), sub=collections.Counter(), by_model={}, by_day={},
                tool_calls=collections.Counter(), tool_result_chars=collections.Counter(),
                tool_input_chars=collections.Counter(), agent_models=collections.Counter(),
                reads=collections.Counter(), attach=collections.defaultdict(lambda: [0, 0]),
                residency=[], kme_hits=0, user_prompts=0, user_chars=0, assistant_text_chars=0,
                thinking_chars=0, compactions=0, compact_summaries=0, max_ctx=0, calls_over_150k=0,
                subagent_files=0, bad_lines=0, tool_uses=0, tool_uses_kme=0, user_kme_hits=0)


def scan_project(pdir, observer=None, keep=None, select=None):
    """Scan one project dir; observer / keep are passed to scan_file (default None = P0 behaviour).
    select(proj, sid, full_path) -> bool, when given, decides per file whether it is read: a refused file is never
    opened, but its session is still registered (the session count of a run does not depend on the selection)."""
    proj = os.path.basename(pdir.rstrip('/\\'))
    sessions = {}
    for root, _dirs, files in os.walk(pdir):
        for f in files:
            if not f.endswith('.jsonl'):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, pdir).replace('\\', '/')
            sid = rel.split('/')[0].replace('.jsonl', '')
            s = sessions.get(sid) or new_sess(proj, sid)
            sessions[sid] = s
            if select is not None and not select(proj, sid, full):
                continue
            try:
                scan_file(full, s, observer=observer, keep=keep)
            except Exception as e:
                s['bad_lines'] += 1
                print(f"WARN {full}: {e}", file=sys.stderr)
    return list(sessions.values())


def classify(s):
    """Return (class, share). share = fraction of the session's tool calls whose input touches KME."""
    share = s['tool_uses_kme'] / s['tool_uses'] if s['tool_uses'] else 0.0
    if PATH_KME_RE.search(s['project']) or (s['cwd'] and PATH_KME_RE.search(s['cwd'])):
        return 'KME_PATH', 1.0
    if share >= 0.30 or (s['user_kme_hits'] >= 2 and share >= 0.10):
        return 'KME_STRONG', share
    if share >= 0.05 or s['user_kme_hits'] >= 1:
        return 'KME_WEAK', share
    return 'NONE', share


def finish_session(s, host):
    """Per-session finishing of main(), verbatim: class/share, host, residency top-40, reads >= 2, attach dict."""
    s['class'], s['kme_share'] = classify(s)
    s['host'] = host
    s['residency'] = sorted(s['residency'], key=lambda x: -x[4])[:40]
    s['reads'] = {k: v for k, v in s['reads'].items() if v >= 2}
    s['attach'] = {k: v for k, v in s['attach'].items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--expand', action='store_true')
    ap.add_argument('roots', nargs='+')
    a = ap.parse_args()
    dirs = []
    for r in a.roots:
        if a.expand:
            dirs += [os.path.join(r, d) for d in sorted(os.listdir(r)) if os.path.isdir(os.path.join(r, d))]
        else:
            dirs.append(r)
    out = []
    for d in dirs:
        for s in scan_project(d):
            finish_session(s, a.host)
            out.append(s)
    with open(a.out, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, default=lambda x: dict(x) if isinstance(x, collections.Counter) else str(x))
    print(f"OK host={a.host} dirs={len(dirs)} sessions={len(out)} "
          f"kme={sum(1 for s in out if s['class'] in ('KME_PATH','KME_STRONG'))}")


if __name__ == '__main__':
    main()
