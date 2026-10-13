#!/usr/bin/env python3
"""gsd_state_projection.py -- GSD STATE.md (+ROADMAP.md, +completion matrix) -> typed JSON -> worker card <= 8 KB (ce-a5 U8). stdlib only.

Usage:
  gsd_state_projection.py --state STATE.md [--roadmap ROADMAP.md] [--matrix M.jsonc] [--repo GIT_DIR --since REV]
                          [--json OUT.json] [--card OUT.md]
Markdown stays the source; the JSON is a projection, the card is a view. Every section the parser does not model
is kept as a pointer (path#Lnn "heading"), never dropped. 'changed since REV' needs --repo/--since: it diffs the
decisions/deferred rows of STATE.md at REV against the working file, and lists changed planning/matrix files.
"""
import argparse, json, os, re, subprocess, sys

CARD_MAX = 8192
KNOWN = {'current position', 'identity (verify before any mutation)', 'decisions', 'deferred verification',
         'session continuity', 'performance metrics'}
RE_UNK = re.compile(r'\b(UNKNOWN|UNMEASURED|UNJUDGED|INCONCLUSIVE|open follow-up|open question|TBD)\b')
RE_BLK = re.compile(r'\b(BLOCKED|blocked)\b')
RE_DEC = re.compile(r'^- \[([^\]]*)\]\s*(.*)$')
RE_DATE = re.compile(r'(\d{4}-\d{2}-\d{2})')
RE_ID = re.compile(r'\b([A-Z]{1,3}\d+[a-z]?|[A-Z]+-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b')


def frontmatter(lines):
    fm = {}
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                break
            m = re.match(r'^(\w+):\s*(.*)$', lines[i])
            if m:
                fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def sections(lines):
    """[(heading, start_line_1based, [body lines])] for '## ' headings."""
    out, cur = [], None
    for i, l in enumerate(lines, 1):
        if l.startswith('## '):
            cur = (l[3:].strip(), i, [])
            out.append(cur)
        elif cur is not None:
            cur[2].append(l)
    return out


def parse_decisions(body, start):
    decs, cur = [], None
    for k, l in enumerate(body):
        m = RE_DEC.match(l)
        if m:
            tag, txt = m.group(1), m.group(2)
            d = RE_DATE.search(tag) or RE_DATE.search(txt[:80])
            i = RE_ID.search(txt[:60]) or RE_ID.search(tag)
            cur = {'id': i.group(1) if i else None, 'tag': tag, 'text': txt, 'date': d.group(1) if d else None,
                   'line': start + k + 1}
            decs.append(cur)
        elif cur is not None and l.startswith(' '):
            cur['text'] += ' ' + l.strip()
        elif l.strip() == '':
            continue
        else:
            cur = None
    return decs


def parse_table(body):
    rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in body if l.startswith('|')]
    if len(rows) < 3:
        return []
    hdr = [h.lower() for h in rows[0]]
    return [dict(zip(hdr, r)) for r in rows[2:]]


def strip_jsonc(t):
    out = []
    for l in t.splitlines():
        if l.lstrip().startswith('//'):
            continue
        out.append(l)
    return json.loads('\n'.join(out))


def roadmap_phases(text):
    ph = []
    for l in text.splitlines():
        m = re.match(r'^- \[( |x)\] \*\*Phase ([\d.]+): ([^*]+)\*\*', l)
        if m:
            ph.append({'phase': m.group(2), 'name': m.group(3).strip(), 'done': m.group(1) == 'x'})
    return ph


def parse_state(text, path='STATE.md', roadmap=None, matrix=None):
    lines = text.splitlines()
    fm = frontmatter(lines)
    secs = sections(lines)
    by = {h.lower(): (h, s, b) for h, s, b in secs}
    cp = by.get('current position')
    pos = {}
    if cp:
        for l in cp[2]:
            m = re.match(r'^\**(Status|Current Phase|Current Plan|Total Plans in Phase)\**:?\**\s*(.*)$', l.strip())
            if m:
                pos[m.group(1).lower().replace(' ', '_')] = m.group(2).strip('* ')
    decs = parse_decisions(by['decisions'][2], by['decisions'][1]) if 'decisions' in by else []
    deferred = parse_table(by['deferred verification'][2]) if 'deferred verification' in by else []
    blockers = [{'phase': r.get('phase'), 'resume': r.get('resume', '')[:200], 'line': by['deferred verification'][1]}
                for r in deferred if 'block' in r.get('state', '').lower()]
    for d in decs:
        if RE_BLK.search(d['text']) and d['id']:
            blockers.append({'decision': d['id'], 'line': d['line'], 'text': d['text'][:160]})
    unknowns = []
    for d in decs:
        m = RE_UNK.search(d['text'])
        if m:
            s = max(0, m.start() - 80)
            unknowns.append({'line': d['line'], 'id': d['id'], 'kw': m.group(1), 'text': d['text'][s:m.end() + 100]})
    sc = by.get('session continuity')
    cont = {}
    if sc:
        for l in sc[2]:
            m = re.match(r'^\*\*([^*]+):\*\*\s*(.*)$', l)
            if m:
                cont[m.group(1).strip().lower()] = m.group(2)
    nxt = []
    if sc:
        nxt = [l.strip() for l in sc[2] if re.match(r'^\s+\d+\.', l)]
    unmodeled = [{'heading': h, 'line': s, 'bytes': sum(len(x) + 1 for x in b)}
                 for h, s, b in secs if h.lower() not in KNOWN]
    # decisions-like bulk after the Performance Metrics table is covered by the section pointer
    out = {'schema': 'gsd-state-projection/1', 'source': path, 'bytes': len(text.encode()), 'lines': len(lines),
           'frontmatter': fm,
           'current': {'phase': fm.get('current_phase') or pos.get('current_phase'),
                       'plan': fm.get('current_plan') or pos.get('current_plan'),
                       'status': fm.get('status') or pos.get('status'), 'stopped_at': fm.get('stopped_at'),
                       'last_activity': fm.get('last_activity_desc')},
           'progress_keys': {k: fm[k] for k in fm if k in ('last_updated', 'workstream')},
           'frontier': {'next': nxt, 'last_session': cont.get('last session'), 'resume_file': cont.get('resume file')},
           'decisions': [{k: d[k] for k in ('id', 'text', 'date', 'line')} for d in decs],
           'blockers': blockers, 'deferred_verifications': deferred, 'open_unknowns': unknowns,
           'sections_unmodeled': unmodeled,
           'section_index': [{'heading': h, 'line': s} for h, s, _ in secs]}
    if roadmap is not None:
        out['roadmap_phases'] = roadmap_phases(roadmap)
    if matrix is not None:
        rows = matrix.get('rows', [])
        out['proof_state'] = {'rows': len(rows), 'by_state': {},
                              'open_required': [{'id': r.get('id'), 'row': r.get('row'), 'state': r.get('state')}
                                                for r in rows if r.get('state') != 'PASS' and r.get('required', True)]}
        for r in rows:
            out['proof_state']['by_state'][r.get('state')] = out['proof_state']['by_state'].get(r.get('state'), 0) + 1
    return out


def git(repo, *a):
    r = subprocess.run(['git', '-C', repo] + list(a), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def changed_since(proj, repo, since, state_rel):
    ch = {'since': since, 'files': [], 'new_decisions': [], 'changed_deferred': [], 'note': ''}
    if not repo or not since:
        ch['note'] = 'not requested'
        return ch
    names = git(repo, 'diff', '--name-only', since, 'HEAD')
    if names is None:
        ch['note'] = 'UNKNOWN: rev not resolvable'
        return ch
    ch['files'] = [n for n in names.split('\n') if n][:40]
    old = git(repo, 'show', f'{since}:{state_rel}')
    if old is None:
        ch['note'] = 'STATE.md absent or untracked at rev (git-excluded?); no decision diff'
        return ch
    o = parse_state(old)
    seen = {(d['id'], d['text']) for d in o['decisions']}
    ch['new_decisions'] = [{'id': d['id'], 'line': d['line'], 'text': d['text'][:140]}
                           for d in proj['decisions'] if (d['id'], d['text']) not in seen]
    od = {json.dumps(r, sort_keys=True) for r in o['deferred_verifications']}
    ch['changed_deferred'] = [r.get('phase') for r in proj['deferred_verifications']
                              if json.dumps(r, sort_keys=True) not in od]
    return ch


def render_card(proj, changed=None, max_bytes=CARD_MAX):
    src = proj['source']
    cur = proj['current']
    L = ['# Worker card (projection; STATE.md is the source)', '',
         f"source: {src} ({proj['bytes']} B, {proj['lines']} lines)", '',
         '## Frontier',
         f"- phase: {cur.get('phase')} | plan: {cur.get('plan')} | status: {cur.get('status')}",
         f"- stopped at: {cur.get('stopped_at')}"]
    for n in proj['frontier']['next'][:6]:
        L.append('- next: ' + n[:300])
    L.append(f"- last session: {(proj['frontier'].get('last_session') or '')[:160]}  -> {src}#session-continuity")
    L.append('')
    L.append('## Changed since ' + str((changed or {}).get('since')))
    if changed and changed.get('since'):
        L.append('- files: ' + (', '.join(changed['files'][:15]) or 'none') + (' ...' if len(changed['files']) > 15 else ''))
        for d in changed['new_decisions'][:8]:
            L.append(f"- new decision {d['id']} ({src}#L{d['line']}): {d['text'][:140]}")
        if changed['changed_deferred']:
            L.append('- deferred rows changed: ' + ', '.join(map(str, changed['changed_deferred'])))
        if changed['note']:
            L.append('- note: ' + changed['note'])
    else:
        L.append('- not requested')
    L.append('')
    L.append('## Blockers')
    for b in proj['blockers'][:8]:
        L.append('- ' + (f"phase {b['phase']}: {b['resume'][:140]}" if 'phase' in b else
                          f"{b['decision']} ({src}#L{b['line']}): {b['text'][:120]}"))
    if not proj['blockers']:
        L.append('- none recorded')
    L.append('')
    L.append('## Open unknowns')
    for u in proj['open_unknowns'][:10]:
        L.append(f"- {u['kw']} ({src}#L{u['line']}): {u['text'][:160]}".replace('\n', ' '))
    if len(proj['open_unknowns']) > 10:
        L.append(f"- +{len(proj['open_unknowns']) - 10} more: grep -n UNKNOWN {src}")
    L.append('')
    L.append('## Proof state')
    ps = proj.get('proof_state')
    if ps:
        L.append(f"- matrix rows {ps['rows']}: {ps['by_state']}")
        for r in ps['open_required'][:12]:
            L.append(f"- row {r['id']} {r['row']}: {r['state']}")
    else:
        L.append('- matrix not given')
    L.append('- deferred verification (phase: state -> resume pointer):')
    for r in proj['deferred_verifications'][:10]:
        L.append(f"  - {r.get('phase')}: {r.get('state')} -> {src}#deferred-verification ({r.get('resume', '')[:90]})")
    L.append('')
    L.append('## Pointers (not inlined)')
    L.append(f"- decisions: {len(proj['decisions'])} in {src}#decisions; ids: " +
             ', '.join(str(d['id']) for d in proj['decisions'][:0]) + 'grep -n "^- \\[" to list')
    for s in proj['sections_unmodeled']:
        L.append(f"- section \"{s['heading']}\" ({s['bytes']} B): {src}#L{s['line']}")
    for s in proj['section_index']:
        if s['heading'].lower() in KNOWN:
            L.append(f"- {s['heading']}: {src}#L{s['line']}")
    pre = proj.get('prefix', '')
    L.append(f"- sibling files: {pre}ROADMAP.md, {pre}MATRIX.md, {pre}MISSION.md, {pre}state.json, {pre}config.json")
    if proj.get('matrix_rel'):
        L.append(f"- completion matrix (source of truth): {proj['matrix_rel']}")
    if proj.get('phase_dirs'):
        L.append(f"- phase dirs under {pre}phases/ (plans <NN>-<MM>-PLAN.md, summaries, VERIFICATION, REVIEW inside): " +
                 ', '.join(d.split('-')[0] for d in proj['phase_dirs']))
        L.append("  dir names: " + ' '.join(proj['phase_dirs']))
    if proj.get('roadmap_phases'):
        op = [p['phase'] for p in proj['roadmap_phases'] if not p['done']]
        L.append(f"- roadmap: {len(proj['roadmap_phases'])} phases, open: {', '.join(op[:40])}")
    card = '\n'.join(L) + '\n'
    # shrink by dropping lowest-value tails, never the pointer block
    while len(card.encode()) > max_bytes and len(L) > 20:
        for i in range(len(L) - 1, -1, -1):
            if L[i].startswith('- note') or L[i].startswith('- new decision') or L[i].startswith('- next') or L[i].startswith('- row ') or L[i].startswith('- ') and 'unknowns' not in L[i] and L[i][2:8] in ('FOLLOW', 'UNKNOW', 'UNMEAS', 'INCONC', 'UNJUDG'):
                del L[i]
                break
        else:
            break
        card = '\n'.join(L) + '\n'
    return card


def build(state, roadmap=None, matrix=None, repo=None, since=None, state_rel=None, prefix='', matrix_rel=None,
          phases_dir=None):
    text = open(state, encoding='utf-8').read()
    rm = open(roadmap, encoding='utf-8').read() if roadmap else None
    mx = strip_jsonc(open(matrix, encoding='utf-8').read()) if matrix else None
    proj = parse_state(text, prefix + os.path.basename(state), rm, mx)
    proj['prefix'] = prefix
    proj['matrix_rel'] = matrix_rel
    proj['phase_dirs'] = sorted(d for d in os.listdir(phases_dir) if os.path.isdir(os.path.join(phases_dir, d))) \
        if phases_dir and os.path.isdir(phases_dir) else []
    proj['changed_since'] = changed_since(proj, repo, since, state_rel or state)
    return proj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', required=True)
    ap.add_argument('--roadmap')
    ap.add_argument('--matrix')
    ap.add_argument('--repo')
    ap.add_argument('--since')
    ap.add_argument('--state-rel', help='STATE.md path relative to repo, for git show')
    ap.add_argument('--prefix', default='', help='repo-relative dir of STATE.md, e.g. .planning/workstreams/dws/')
    ap.add_argument('--matrix-rel', help='repo-relative matrix path for pointers')
    ap.add_argument('--phases-dir')
    ap.add_argument('--json')
    ap.add_argument('--card')
    a = ap.parse_args()
    proj = build(a.state, a.roadmap, a.matrix, a.repo, a.since, a.state_rel, a.prefix, a.matrix_rel, a.phases_dir)
    card = render_card(proj, proj['changed_since'])
    if a.json:
        open(a.json, 'w').write(json.dumps(proj, indent=1, sort_keys=True))
    if a.card:
        open(a.card, 'w').write(card)
    else:
        sys.stdout.write(card)
    return 0 if len(card.encode()) <= CARD_MAX else 2


if __name__ == '__main__':
    sys.exit(main())
