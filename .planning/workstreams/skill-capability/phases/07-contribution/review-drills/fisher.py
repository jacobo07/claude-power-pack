from fractions import Fraction as F
from math import comb, factorial
# independent: probability of table via factorial formula, two-sided = sum over tables with prob <= observed
def tp(a,b,c,d):
    n=a+b+c+d
    return F(factorial(a+b)*factorial(c+d)*factorial(a+c)*factorial(b+d), factorial(n)*factorial(a)*factorial(b)*factorial(c)*factorial(d))
def fisher(x1,n1,x2,n2):
    r1=n1; r2=n2; c1=x1+x2
    obs=tp(x1,n1-x1,x2,n2-x2)
    tot=F(0)
    for a in range(0,n1+1):
        c=c1-a
        if c<0 or c>n2: continue
        p=tp(a,n1-a,c,n2-c)
        if p<=obs: tot+=p
    return tot
pins=[((4,4,0,4),F(1,35)),((5,5,0,5),F(1,126)),((4,5,0,5),F(1,21)),((3,5,0,5),F(1,6)),((2,2,0,2),F(1,3)),((1,2,0,2),F(1)),((3,4,0,5),F(1,21)),((10,10,5,10),F(21,646))]
for t,w in pins: print(t, fisher(*t), w, fisher(*t)==w)
A=F(1,20)
def ms(n1,n2):
    best=None
    for a in range(n1+1):
        for b in range(n2+1):
            if fisher(a,n1,b,n2)<=A:
                e=abs(F(a,n1)-F(b,n2))
                if best is None or e<best: best=e
    return best
allf=[]
for n1 in range(1,11):
    for n2 in range(1,11):
        if n1+n2<=10:
            m=ms(n1,n2)
            if m is not None: allf.append((m,n1,n2))
allf.sort(); print("floor all alloc", allf[:6])
print("equal k", [(k,ms(k,k)) for k in range(1,6)])
print("needed k for 1/2:", [(k,ms(k,k)) for k in range(6,12)])
# pooled designs: existing N0 2 rows, P 2 rows + x,y new
pool=[]
for x in range(0,11):
    for y in range(0,11-x):
        m=ms(2+x,2+y)
        if m is not None: pool.append((m,2+x,2+y))
pool.sort(); print("pooled with 2+2 existing", pool[:6])
# pooled control N0 2 + new, treatment arbitrary existing rows (N0,R,C pooled control 6)
pool2=[]
for x in range(0,11):
    for y in range(0,11-x):
        m=ms(6+x,2+y)
        if m is not None: pool2.append((m,6+x,2+y))
pool2.sort(); print("pooled 6 ctl + 2 P", pool2[:4])
