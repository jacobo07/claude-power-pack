"""WU-P1P2 shared asm parsing over the DTK split of the whole DOL (all 560 files, 18,820 `.fn` blocks).

Pure functions over text: parse_program(asm_dir) -> Program. No model, no compiler. Linear (control-flow-insensitive)
register tracking is used where noted; every consumer labels its output as structural, never semantic.
"""
import collections
import hashlib
import os
import re

FN = re.compile(r'^\.fn\s+"?([^",\s]+)"?')
ENDFN = re.compile(r'^\.endfn\s')
OBJ = re.compile(r'^\.obj\s+"?([^",\s]+)"?')
ENDOBJ = re.compile(r'^\.endobj\s')
INSN = re.compile(r'^/\*\s+([0-9A-Fa-f]{8})\s+[0-9A-Fa-f]{8}\s+(?:[0-9A-Fa-f]{2}\s+){4}\*/\s*(.*)$')
LABEL = re.compile(r'^(\.L_[0-9A-Fa-f]+):')
WORD = re.compile(r'^\.4byte\s+"?([A-Za-z_.$][\w.$@]*)"?(\+0x[0-9A-Fa-f]+)?')
FLOATDEF = re.compile(r'^\.(float|double)\s+(\S+)')
SYMREF = re.compile(r'"?([A-Za-z_$][\w$]*)"?@(?:ha|h|l|sda21|sda2)\b')
MEM = re.compile(r'^(-?(?:0x[0-9A-Fa-f]+|\d+))\((r\d+)\)$')
SDAMEM = re.compile(r'^"?([A-Za-z_$][\w$]*)"?@(sda21|l)\((r\d+)\)$')
NUM = re.compile(r'^-?(?:0x[0-9A-Fa-f]+|\d+)$')
GPR = re.compile(r'^r(\d+)$')
FPR = re.compile(r'^f(\d+)$')

CALLS = {"bl", "bctrl", "blrl"}
COND = re.compile(r'^b(eq|ne|lt|gt|le|ge|ns|so|dnz|dz|nl|ng|un|nu|c|dnzt|dnzf|dzt|dzf|t|f)[+-]?$')
CONDRET = re.compile(r'^b(eq|ne|lt|gt|le|ge|ns|so|dnz|dz|nl|ng|un|nu)lr[+-]?$')
CONDCTR = re.compile(r'^b(eq|ne|lt|gt|le|ge|ns|so|nl|ng|un|nu)ctr[+-]?$')
WIDTH = {"lbz": 1, "lhz": 2, "lha": 2, "lwz": 4, "lfs": 4, "lfd": 8, "stb": 1, "sth": 2, "stw": 4, "stfs": 4, "stfd": 8}
NOWRITE = ("st", "cmp", "fcmp", "tw", "mt", "dcb", "icb", "sync", "isync", "eieio", "b", "crxor", "creqv", "cror",
           "crclr", "crset", "crnot", "mcrf", "nop", "sc", "rfi", "psq_st")
VOLATILE_G = {"r0"} | {"r%d" % i for i in range(3, 13)}
VOLATILE_F = {"f%d" % i for i in range(0, 14)}


def parse_num(s):
    v = int(s, 16) if s.lstrip("-").startswith("0x") else int(s)
    return -int(s[1:], 16) if s.startswith("-0x") else v


class Insn:
    __slots__ = ("addr", "m", "ops", "text")

    def __init__(self, addr, text):
        self.addr, self.text = addr, text
        p = text.split(None, 1)
        self.m = p[0] if p else ""
        self.ops = [o.strip() for o in p[1].split(",")] if len(p) > 1 else []


def mem_op(i):
    """(kind 'l'|'st', width, offset or None, base reg, base symbol or None) for a D-form memory op, else None."""
    m = i.m
    base_m = m.rstrip(".")
    if base_m.endswith("x") or base_m in ("lmw", "stmw"):
        if base_m in ("lmw", "stmw"):
            mm = MEM.match(i.ops[1]) if len(i.ops) > 1 else None
            if mm:
                n = int(GPR.match(i.ops[0]).group(1))
                return ("l" if m == "lmw" else "st", 4 * (32 - n), parse_num(mm.group(1)), mm.group(2), None)
        return None
    if base_m.startswith("psq_"):
        mm = MEM.match(i.ops[1]) if len(i.ops) > 1 else None
        if mm:
            return ("l" if base_m.startswith("psq_l") else "st", 8 if i.ops[2] == "0" else 4, parse_num(mm.group(1)), mm.group(2), None)
        return None
    core = base_m[:-1] if base_m.endswith("u") and base_m[:-1] in WIDTH else base_m
    if core not in WIDTH or len(i.ops) < 2:
        return None
    kind = "st" if core.startswith("st") else "l"
    mm = MEM.match(i.ops[1])
    if mm:
        return (kind, WIDTH[core], parse_num(mm.group(1)), mm.group(2), None)
    sm = SDAMEM.match(i.ops[1])
    if sm:
        return (kind, WIDTH[core], None, sm.group(3), sm.group(1))
    return None


def writes(i):
    """Registers written by i (GPR/FPR names), linear model."""
    m = i.m
    if m in CALLS:
        return set(VOLATILE_G) | set(VOLATILE_F)
    out = set()
    mo = mem_op(i)
    if mo:
        kind, w, off, base, sym = mo
        if kind == "l":
            if m == "lmw":
                out |= {"r%d" % k for k in range(int(i.ops[0][1:]), 32)}
            else:
                out.add(i.ops[0])
        if i.m.rstrip(".").endswith("u") or i.m.rstrip(".").endswith("ux"):
            out.add(base)
        return out
    if m.startswith(NOWRITE):
        return out
    if m in ("mflr", "mfctr", "mfcr", "mfspr", "mftb", "mffs", "mfmsr"):
        return {i.ops[0]} if i.ops else set()
    if i.ops and (GPR.match(i.ops[0]) or FPR.match(i.ops[0])):
        out.add(i.ops[0])
    return out


def reads(i):
    """Register names i reads (operands after the destination, plus memory bases; stores read all operands)."""
    regs = set()
    mo = mem_op(i)
    ops = i.ops
    if mo:
        regs.add(mo[3])
        if mo[0] == "st":
            regs.add(ops[0])
        return regs
    src = ops if (i.m.startswith(NOWRITE) or i.m in ("mtctr", "mtlr")) else ops[1:]
    for o in src:
        mm = MEM.match(o)
        o = mm.group(2) if mm else o
        if GPR.match(o) or FPR.match(o):
            regs.add(o)
    return regs


def is_branch(i):
    m = i.m
    return m == "b" or m in ("blr", "bctr") or bool(COND.match(m) or CONDRET.match(m) or CONDCTR.match(m))


Program = collections.namedtuple("Program", "fns order file_of labels data_refs code_refs floats tables")


def parse_program(asm_dir):
    fns, order, file_of, labels = {}, [], {}, {}
    data_refs = collections.Counter()   # symbol -> count of .4byte words naming it (outside jumptable objects)
    code_refs = collections.Counter()   # symbol -> count of @ha/@l/@sda21 operand references from code
    floats, tables = {}, {}
    for fname in sorted(os.listdir(asm_dir)):
        if not fname.endswith(".s"):
            continue
        cur = obj = None
        objwords = []
        for line in open(os.path.join(asm_dir, fname), encoding="utf-8", errors="replace"):
            s = line.strip()
            m = FN.match(s)
            if m:
                cur = m.group(1)
                fns[cur], labels[cur] = [], {}
                order.append(cur)
                file_of[cur] = fname
                pend = []
                continue
            if cur is not None:
                if ENDFN.match(s):
                    cur = None
                    continue
                lm = LABEL.match(s)
                if lm:
                    pend.append(lm.group(1))
                    continue
                im = INSN.match(s)
                if im:
                    ins = Insn(int(im.group(1), 16), re.sub(r'/\*.*?\*/', '', im.group(2)).strip())
                    for lb in pend:
                        labels[cur][lb] = len(fns[cur])
                    pend = []
                    fns[cur].append(ins)
                    for sym in SYMREF.findall(ins.text):
                        code_refs[sym] += 1
                continue
            om = OBJ.match(s)
            if om:
                obj, objwords = om.group(1), []
                continue
            if obj is not None:
                if ENDOBJ.match(s):
                    if obj.startswith("jumptable_"):
                        tables[obj] = objwords
                    else:
                        for sym, off in objwords:
                            data_refs[sym] += 1
                    obj = None
                    continue
                wm = WORD.match(s)
                if wm:
                    objwords.append((wm.group(1), int(wm.group(2)[3:], 16) if wm.group(2) else 0))
                fm = FLOATDEF.match(s)
                if fm and obj not in floats:
                    try:
                        floats[obj] = float(fm.group(2))
                    except ValueError:
                        pass
    return Program(fns, order, file_of, labels, data_refs, code_refs, floats, tables)


def target(i):
    return i.ops[-1].strip('"') if i.ops else None


def cfg(name, ins, labels, tables):
    """Basic blocks over one function. Returns (blocks [(start,end)], edges [(src_block, dst_block)], back_edges)."""
    n = len(ins)
    if n == 0:
        return [], [], 0
    lead = {0}
    for k, i in enumerate(ins):
        if is_branch(i):
            if k + 1 < n:
                lead.add(k + 1)
            t = target(i)
            if t in labels:
                lead.add(labels[t])
    jt_targets = []
    start = ins[0].addr
    refs = {t for i in ins for t in re.findall(r'\b(jumptable_[0-9A-Fa-f_]+)', i.text)}
    addr_idx = {i.addr: k for k, i in enumerate(ins)}
    for t in refs:
        for sym, off in tables.get(t, []):
            if sym == name and (start + off) in addr_idx:
                jt_targets.append(addr_idx[start + off])
                lead.add(addr_idx[start + off])
    starts = sorted(lead)
    blocks = [(s, (starts[j + 1] if j + 1 < len(starts) else n)) for j, s in enumerate(starts)]
    bidx = {s: j for j, s in enumerate(starts)}
    edges = []
    for j, (s, e) in enumerate(blocks):
        last = ins[e - 1]
        m = last.m
        t = target(last)
        nxt = j + 1 if j + 1 < len(blocks) else None
        if m == "b":
            if t in labels:
                edges.append((j, bidx[labels[t]]))
        elif m == "blr":
            pass
        elif m == "bctr":
            for k in sorted(set(jt_targets)):
                edges.append((j, bidx[k]))
        elif COND.match(m):
            if t in labels:
                edges.append((j, bidx[labels[t]]))
            if nxt is not None:
                edges.append((j, nxt))
        else:  # conditional return / conditional ctr / plain fall-through
            if nxt is not None:
                edges.append((j, nxt))
    back = sum(1 for a, b in edges if b <= a)
    return blocks, sorted(set(edges)), back


def normalise_window(win):
    """Normalised text of a window: registers renumbered by first appearance, numbers -> N, symbols -> S."""
    regmap = {}

    def reg(m):
        r = m.group(0)
        if r not in regmap:
            regmap[r] = "%s%d" % (r[0].upper(), len(regmap))
        return regmap[r]
    out = []
    for i in win:
        t = re.sub(r'"[^"]*"|\b(?:lbl|fn|jumptable|gap)_[\w]+|\.L_[0-9A-Fa-f]+|\b__\w+', "S", i.text)
        t = re.sub(r'-?\b0x[0-9A-Fa-f]+\b|-?\b\d+\b(?![(\w])', "N", t)
        t = re.sub(r'\b[rf]\d+\b', reg, t)
        out.append(t)
    return "|".join(out)


def sha(s, n=16):
    return hashlib.sha1(s.encode()).hexdigest()[:n]
