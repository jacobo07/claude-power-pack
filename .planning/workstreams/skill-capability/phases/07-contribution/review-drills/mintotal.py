import sys
sys.path.insert(0, "/home/kobii/missions/skill-capability/.claude/worktrees/sc-run/tools")
import test_contribution_verdict as T
from fractions import Fraction as F
best=None
for tot in range(2, 21):
    hits=[(n1,tot-n1,T.min_separable(n1,tot-n1)[0]) for n1 in range(1,tot) if T.min_separable(n1,tot-n1) and T.min_separable(n1,tot-n1)[0] <= F(1,2)]
    if hits: print(tot, hits); break
# also: tables with effect exactly 1/2 separating
for tot in range(2, 21):
    hits=[]
    for n1 in range(1,tot):
        n2=tot-n1
        for a in range(n1+1):
            for b in range(n2+1):
                if abs(F(a,n1)-F(b,n2))==F(1,2) and T.fisher_two_sided(a,n1,b,n2)<=T.ALPHA: hits.append((a,n1,b,n2))
    if hits: print("exact 1/2 effect separable at total", tot, hits[:4]); break
