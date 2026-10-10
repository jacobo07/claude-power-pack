#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a5_holdout as H
R = []
def t(name, got, want):
    R.append(got == want)
    print(('ok  ' if got == want else 'FAIL'), name, got)
c = H.classify
t('both thresholds met', c(0.10, [0.05, 0.0]), 'PROMOTABLE')            # control admits
t('DWS just below 10%', c(0.099, [0.5]), 'DWS_LOCAL')
t('holdouts just below 5%', c(0.5, [0.049, 0.0]), 'DWS_LOCAL')
t('second holdout carries', c(0.2, [0.0, 0.06]), 'PROMOTABLE')
t('missing holdout, other ok', c(0.2, [None, 0.05]), 'PROMOTABLE')
t('all holdouts missing', c(0.9, [None, None]), 'DWS_LOCAL')
t('holdout big, DWS small', c(0.09, [0.9, 0.9]), 'DWS_LOCAL')
t('DWS unknown', c(None, [0.9]), 'DWS_LOCAL')
t('negative gain', c(-0.2, [-0.1]), 'DWS_LOCAL')
with tempfile.TemporaryDirectory() as d:  # end-to-end on fixtures
    def w(n, rows):
        p = os.path.join(d, n); json.dump({'rows': rows}, open(p, 'w')); return p
    dws = w('d.json', [['actual', 100, 1, 0], ['p', 80, 1, -0.2], ['q', 95, 1, -0.05]])
    h1 = w('h1.json', [['actual', 100, 1, 0], ['p', 90, 1, -0.1], ['q', 90, 1, -0.1]])
    out = os.path.join(d, 'o.md')
    r = subprocess.run([sys.executable, '-I', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'a5_holdout.py'),
                        '--dws', dws, '--holdout', 'h1=' + h1, '--holdout', 'h2=' + os.path.join(d, 'none.json'), '--out', out], capture_output=True, text=True)
    s = open(out).read()
    t('cli exit 0', r.returncode, 0)
    t('cli p promotable', '| p | 20.0% | 10.0% | DEFER_EXTERNAL_DEPENDENCY | PROMOTABLE |' in s, True)
    t('cli q DWS_LOCAL', 'DWS_LOCAL' in s.split('| q |')[1], True)
print('A5_U9_PASS=%d/%d' % (sum(R), len(R)))
sys.exit(0 if all(R) else 1)
