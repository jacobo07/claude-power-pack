import re, struct, sys
S = "/home/kobii/agora/factory/tn-f2"
orig = [l.split()[-1] for l in open(S + "/config/TENNIS/config.yml") if l.startswith("object:")][0]
A = open(S + "/" + orig, "rb").read(); B = open(S + "/build/TENNIS/main.dol", "rb").read()
def secs(d):
    off = struct.unpack(">18I", d[0:72]); addr = struct.unpack(">18I", d[72:144]); size = struct.unpack(">18I", d[144:216])
    return [(i, off[i], addr[i], size[i]) for i in range(18) if size[i]]
sym = {}
for l in open(S + "/config/TENNIS/symbols.txt"):
    m = re.match(r"\s*(\S+)\s*=\s*\.\S+:0x([0-9A-Fa-f]+);", l)
    if m: sym[int(m.group(2), 16)] = m.group(1)
def nm(v): return sym.get(v, hex(v))
print("sizes equal:", len(A) == len(B))
for (i, oa, aa, sa), (_, ob, ab, sb) in zip(secs(A), secs(B)):
    if aa != ab or sa != sb:
        print("sec", i, "header differs", hex(aa), hex(ab), sa, sb); continue
    a, b = A[oa:oa + sa], B[ob:ob + sb]
    diffs = [k for k in range(0, sa, 4) if a[k:k + 4] != b[k:k + 4]]
    if not diffs: continue
    print(f"sec {i} addr {hex(aa)} size {sa}: {len(diffs)} words differ")
    for k in diffs[:12]:
        wa, wb = struct.unpack(">I", a[k:k + 4])[0], struct.unpack(">I", b[k:k + 4])[0]
        print(f"  {hex(aa + k)} [{nm(aa + k)}] orig {nm(wa) if i >= 7 else hex(wa)}  built {nm(wb) if i >= 7 else hex(wb)}")
# full .ctors table order, as names
for (i, oa, aa, sa), (_, ob, ab, sb) in zip(secs(A), secs(B)):
    if i >= 7 and sa <= 512 and A[oa:oa + sa] != B[ob:ob + sb]:
        wa = struct.unpack(f">{sa // 4}I", A[oa:oa + sa]); wb = struct.unpack(f">{sa // 4}I", B[ob:ob + sb])
        print("orig order :", [nm(x) for x in wa])
        print("built order:", [nm(x) for x in wb])
        print("same multiset:", sorted(wa) == sorted(wb))
