#!/usr/bin/env python3
"""test_a5_u2.py -- hermetic arithmetic tests for a5_counterfactual (ce-a5 U2)."""
import os, sys, tempfile, gzip, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a5_counterfactual as cf

def call(s, i, ctx, label='NOVELTY', reads=(), tools=('Read',)):
    return dict(session=s, seq=i, ctx=ctx, label=label, reads=list(reads), tools=list(tools))

# S1: ctx 100,130,160,200,230 labels N,R,N,C,S ; growth caused: 30,30,40,30,0
S1 = [call('s1', 0, 100), call('s1', 1, 130, 'REDISCOVERY'), call('s1', 2, 160), call('s1', 3, 200, 'CONTROL_LOOP'), call('s1', 4, 230, 'STATE_READ')]
# S2: ctx 50,5000,5010 labels N,STATE_READ,N ; growth 4950,10,0
S2 = [call('s2', 0, 50), call('s2', 1, 5000, 'STATE_READ'), call('s2', 2, 5010)]
BY = {'s1': S1, 's2': S2}

def total(**kw):
    t = n = 0
    for c in BY.values():
        a, b = cf.replay(c, **kw)
        t += a; n += b
    return t, n

def main():
    tests = []
    # actual: s1 100+130+160+200+230=820 ; s2 50+5000+5010=10060
    tests.append(('actual', total() == (10880, 8)))
    # slim: s1 F=13507: 13507,+30,+30,+40,+30 -> 13507+13537+13567+13607+13637=67855; s2: 13507, +4950=18457, +10=18467 -> 50431
    tests.append(('slim', total(slim=True) == (118286, 8)))
    # rot2 s1: 100,130 ; reset 2600 ; 2600+g2(40)=2640 ; reset 2600 -> 8070
    #  s2: 50,5000 ; reset 50+2500=2550 -> 7600 ; total 15660
    tests.append(('rotate2', total(rot=2) == (15670, 8)))
    # read-once: s1 drops call1 (growth 30 lost): kept 100,(100+g0=130 -> call0 growth=30) ... calls 0,2,3,4: 100,130,160... compute:
    #  call0 cur=100 ->cur=130 ; call2 130 ->cur=160(g=40->170?) g2=40 -> 170 ; call3 170 -> +30=200 ; call4 200 => 100+130+170+200=600... check: kept 0,2,3,4 => 100,130,170,200 =600 ; wait 4 calls
    tests.append(('read-once', total(no_reread=True) == (600 + 10060, 7)))
    # state: s1 call4 growth 0 stays; s2 call1 growth min(10,2500)=10 unchanged ; s2 call0 not state. => unchanged
    #  use S3 to prove cap
    S3 = [call('s3', 0, 50), call('s3', 1, 5000, 'STATE_READ'), call('s3', 2, 5010)]
    # state cap applies to growth caused by STATE_READ call (call1: 5010-5000=10) -> use bigger
    S4 = [call('s4', 0, 100), call('s4', 1, 110, 'STATE_READ'), call('s4', 2, 9110)]
    # caused growth of call1 = 9000 -> capped 2500: 100,110,2610 = 2820 ; actual 100+110+9110=9320
    tests.append(('state', cf.replay(S4, state=True) == (2820, 3) and cf.replay(S4) == (9320, 3)))
    # poll->event: s1 drops call3 (growth 30 lost): calls 0,1,2,4 : 100,130,160,200+... g2=40 -> 200 ; call4 cur=200 => 100+130+160+200=590 ; s2 unchanged
    tests.append(('noloop', total(noloop=True) == (590 + 10060, 7)))
    # combo slim+rot2+reread+state+loop on S1: kept calls 0,2,4 (calls1,3 dropped). g: c0=30,c2=40,c4=0. F=13507
    #  call0 13507 ->13537 ; call2 13537 -> 13577 ; seg=2 -> reset 13507+2500=16007 ; call4 16007 => 13507+13537+16007=43051
    tests.append(('combo', cf.replay(S1, slim=True, rot=2, no_reread=True, state=True, noloop=True) == (43051, 3)))
    # control for mutant: capsule cost matters (rot2 with capsule=0 differs)
    tests.append(('capsule-control', cf.replay(S1, rot=2, capsule=0)[0] != cf.replay(S1, rot=2)[0]))
    # mutant: rotation ignores capsule -> must disagree with hand value (red)
    mut = cf.replay(S1, rot=2, capsule=0)[0]
    tests.append(('mutant-red', mut != 8070))
    # duplicates: same read+next tools in two sessions -> 1 group, 1 redundant
    D = {'x': [call('x', 0, 1, reads=['p']), call('x', 1, 1, tools=['Edit'])], 'y': [call('y', 0, 1, reads=['p']), call('y', 1, 1, tools=['Edit'])]}
    tests.append(('dups', cf.duplicates(D)[:2] == (1, 1)))
    # dups control: different follow-up -> no group
    D['y'][1]['tools'] = ['Bash']
    tests.append(('dups-control', cf.duplicates(D)[:2] == (0, 0)))
    # end to end CLI on a fixture
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(os.path.join(t, 'data'))
        p = os.path.join(t, 'calls.jsonl.gz')
        with gzip.open(p, 'wt') as f:
            for c in S1 + S2:
                f.write(json.dumps(c) + '\n')
        neg = os.path.join(t, 'neg.json')
        r = subprocess.run([sys.executable, '-I', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a5_counterfactual.py'), '--calls', p, '--out', t, '--neg', neg], capture_output=True, text=True)
        ok = r.returncode == 0 and os.path.exists(os.path.join(t, 'COUNTERFACTUAL.md')) and 'UNKNOWN' in open(os.path.join(t, 'COUNTERFACTUAL.md')).read()
        tests.append(('cli', ok))
    ok = 0
    for n, v in tests:
        print(('PASS ' if v else 'FAIL ') + n)
        ok += bool(v)
    print('A5_U2_PASS=%d/%d' % (ok, len(tests)))
    sys.exit(0 if ok == len(tests) else 1)

main()
