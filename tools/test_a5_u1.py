#!/usr/bin/env python3
"""Tests for a5_trace.py on a 3-session synthetic fixture (not the corpus). Prints A5_U1_PASS=n/m."""
import gzip, json, os, shutil, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a5_trace as T

_n = [0]


def asst(mid, req, content, ts, inp=10, cr=100, cw=0, out=5):
    return {'type': 'assistant', 'requestId': req, 'timestamp': ts,
            'message': {'id': mid, 'model': 'm1', 'content': content,
                        'usage': {'input_tokens': inp, 'cache_read_input_tokens': cr, 'cache_creation_input_tokens': cw, 'output_tokens': out}}}


def tu(name, **inp):
    _n[0] += 1
    return {'type': 'tool_use', 'id': 'tu%d' % _n[0], 'name': name, 'input': inp}


def res(tid, err=False):
    return {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': tid, 'is_error': err, 'content': 'x'}]}}


def write(path, objs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        for o in objs:
            fh.write(json.dumps(o) + '\n')


def fixture(root):
    _n[0] = 0
    # S1 main: streamed call (2 lines, same key), labels each rule
    a = tu('Read', file_path='C:\\x\\orca-dws-wt\\.planning\\STATE.md')       # STATE_READ
    b = tu('Read', file_path='src/a.ts')                                       # NOVELTY
    c = tu('Read', file_path='src/a.ts')                                       # REDISCOVERY (re-read, no edit)
    d = tu('Edit', file_path='src/a.ts')                                       # MUTATION
    e = tu('Read', file_path='src/a.ts')                                       # NOVELTY control (edit in between)
    f = tu('Bash', command='sleep 1')                                          # CONTROL_LOOP
    g = tu('Bash', command='pnpm test -- foo')                                 # PROOF (errors)
    h = tu('Bash', command='ls src')                                           # RECOVERY (within 2 of error)
    i = tu('Bash', command='ls docs')                                          # RECOVERY
    j = tu('Bash', command='ls lib')                                           # NOVELTY control (3 after error)
    k = tu('Bash', command='git commit -m x')                                  # MUTATION
    objs = [asst('m1', 'r1', [{'type': 'text', 'text': 'hi'}], '2026-10-01T00:00:01Z'),   # streamed line 1 (text only)
            asst('m1', 'r1', [a], '2026-10-01T00:00:02Z', out=40),                          # streamed line 2 (tool)
            res(a['id'])]
    for n, t in enumerate([b, c, d, e, f, g, h, i, j, k]):
        objs.append(asst('m%d' % (n + 2), 'r%d' % (n + 2), [t], '2026-10-01T00:01:%02dZ' % n, cr=100 + n))
        objs.append(res(t['id'], err=(t is g)))
    write(os.path.join(root, 'S1.jsonl'), objs)
    # S2 subagent of S1: Agent delegation + control shell without poll + `git status` control
    l = tu('Agent', prompt='p')
    m = tu('Bash', command='git status')
    n_ = tu('Read', file_path='src/a.ts')       # not a re-read: different session
    write(os.path.join(root, 'S1', 'subagents', 'agent-a1.jsonl'),
          [asst('s2m1', 'r1', [l], '2026-10-01T01:00:00Z'), asst('s2m2', 'r2', [m], '2026-10-01T01:00:01Z'),
           asst('s2m3', 'r3', [n_], '2026-10-01T01:00:02Z')])
    with open(os.path.join(root, 'S1', 'subagents', 'agent-a1.meta.json'), 'w') as fh:
        json.dump({'agentType': 'gsd-executor'}, fh)
    # S3 main: duplicate of S1 call m2/r2 (dedupe across files) + a no-tool call + `until` loop
    o_ = tu('Bash', command='until grep -q done f; do sleep 2; done')
    write(os.path.join(root, 'S3.jsonl'),
          [asst('m2', 'r2', [tu('Read', file_path='dup.ts')], '2026-10-01T02:00:00Z'),
           asst('s3m1', 'r1', [{'type': 'text', 'text': 'no tool'}], '2026-10-01T02:00:01Z'),
           asst('s3m2', 'r2', [o_], '2026-10-01T02:00:02Z')])


def run(root):
    return T.label_rows(T.extract(root))


def by_session(rows):
    d = {}
    for r in rows:
        d.setdefault(r['session'], []).append(r)
    return d


def t_dedupe(root):
    rows = run(root)
    s = by_session(rows)
    # 11 distinct calls in S1 (streamed m1 counted once), 3 in S2, S3 dup dropped -> 2
    ok = len(s['S1']) == 11 and len(s['S3']) == 2 and len(rows) == 16
    ok = ok and not any('dup.ts' in r['reads'] for r in rows)
    return ok


def t_stream_join(root):
    r = by_session(run(root))['S1'][0]
    return r['tools'] == ['Read'] and r['out'] == 40 and r['ctx'] == 110 and r['reads'] == ['.planning/STATE.md']


def labels(root):
    s = by_session(run(root))
    return [r['label'] for r in s['S1']], [r['label'] for r in s['agent-a1']], [r['label'] for r in s['S3']]


def t_state_read(root):
    return labels(root)[0][0] == 'STATE_READ'


def t_rediscovery_pos_ctl(root):
    l = labels(root)[0]
    return l[2] == 'REDISCOVERY' and l[1] == 'NOVELTY' and l[4] == 'NOVELTY'  # first read, and read after an edit


def t_rediscovery_cross_session(root):
    return labels(root)[1][2] == 'NOVELTY'


def t_control_loop(root):
    l = labels(root)
    return l[0][5] == 'CONTROL_LOOP' and l[2][1] == 'CONTROL_LOOP' and l[1][1] == 'NOVELTY'  # git status is not a poll


def t_proof(root):
    return labels(root)[0][6] == 'PROOF'


def t_mutation(root):
    l = labels(root)[0]
    return l[3] == 'MUTATION' and l[10] == 'MUTATION'


def t_recovery(root):
    l = labels(root)[0]
    return l[7] == 'RECOVERY' and l[8] == 'RECOVERY' and l[9] == 'NOVELTY'


def t_delegation(root):
    return labels(root)[1][0] == 'DELEGATION'


def t_novelty_default(root):
    return labels(root)[2][0] == 'NOVELTY'  # no-tool call


def t_agent_type(root):
    r = by_session(run(root))
    return r['agent-a1'][0]['agent'] == 'gsd-executor' and r['agent-a1'][0]['side'] == 'subagent' and r['S1'][0]['side'] == 'main' \
        and r['agent-a1'][0]['parent'] == 'S1'


def t_regen_identical(root):
    outs = []
    for k in range(2):
        o = tempfile.mkdtemp(prefix='a5u1out')
        try:
            T.build(root, '', o)
            outs.append({n: open(os.path.join(o, p, n) if p else os.path.join(o, n), 'rb').read()
                         for p, n in [('data', 'calls.jsonl.gz'), ('data', 'sessions.json'), ('', 'TRACE-REPORT.md')]})
        finally:
            shutil.rmtree(o)
    rows = [json.loads(x) for x in gzip.decompress(outs[0]['calls.jsonl.gz']).decode().splitlines()]
    return outs[0] == outs[1] and len(rows) == 16 and all('label' in r for r in rows)


def t_jsonc(root):
    s = T.matrix_states('{"rows": [ // c\n {"id": 1, "state": "A", "u": "http://x//y",}, /* b */ {"id": 2, "state": "B"},\n]}')
    return s == {'1': 'A', '2': 'B'}


def t_mutant_dedupe(root):
    orig = T.dedupe_key
    T.dedupe_key = lambda m, o: (m.get('id'), o.get('timestamp'))  # broken key: streamed lines / duplicates no longer collapse
    try:
        return t_dedupe(root) is False  # the real check must go red under the mutant
    finally:
        T.dedupe_key = orig


TESTS = [t_dedupe, t_stream_join, t_state_read, t_rediscovery_pos_ctl, t_rediscovery_cross_session, t_control_loop, t_proof,
         t_mutation, t_recovery, t_delegation, t_novelty_default, t_agent_type, t_regen_identical, t_jsonc, t_mutant_dedupe]


def main():
    root = tempfile.mkdtemp(prefix='a5u1fx')
    passed = 0
    try:
        fixture(root)
        for t in TESTS:
            try:
                ok = bool(t(root))
            except Exception as ex:
                ok = False
                print('ERR', t.__name__, repr(ex))
            print(('PASS ' if ok else 'FAIL ') + t.__name__)
            passed += ok
    finally:
        shutil.rmtree(root)
    print('A5_U1_PASS=%d/%d' % (passed, len(TESTS)))
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == '__main__':
    main()
