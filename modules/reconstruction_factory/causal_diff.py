"""Causal diff: aligns target and candidate instruction rows and classifies every hunk by its COMPILER cause, then attributes a change in the
diff to the source edit that made it. Classes (closed set): REG_ALLOC (same op, registers differ), CONST (immediates differ), RELOC (call/data
target differs), OPCODE (different instruction), ORDER (same instructions, different order), MISSING / EXTRA (length), FRAME (stack frame)."""
import difflib
import re
from collections import Counter

from .certify import text_rows

CLASSES = ("REG_ALLOC", "CONST", "RELOC", "OPCODE", "ORDER", "MISSING", "EXTRA", "FRAME")
_REGS = re.compile(r"\b(?:r|f|cr)\d+\b")
_SP = re.compile(r"\br1\b")
_NUM = re.compile(r"(?<![\w])-?(?:0x[0-9a-f]+|\d+)(?![\w])")


def _regless(args):
    return _REGS.sub("R", args)


def _numless(args):
    return _NUM.sub("N", _regless(args))


def classify_pair(t, c):
    if t == c:
        return None
    if t[0] != c[0]:
        return "OPCODE"
    if t[2:] != c[2:]:
        return "RELOC"
    if t[0] in ("stwu", "addi") and _SP.search(t[1]) and _SP.search(c[1]) and t[1] != c[1]:
        return "FRAME"
    if _regless(t[1]) == _regless(c[1]):
        return "REG_ALLOC"
    if _numless(t[1]) == _numless(c[1]):
        return "CONST"
    return "OPCODE"


def diff_rows(trows, crows):
    """-> list of hunks {cls, t:[rows], c:[rows], at}. ORDER when a replace hunk holds the same rows in both sides as a multiset."""
    hunks = []
    sm = difflib.SequenceMatcher(None, trows, crows, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        t, c = trows[i1:i2], crows[j1:j2]
        if tag == "delete":
            cls = "MISSING"
        elif tag == "insert":
            cls = "EXTRA"
        elif Counter(t) == Counter(c):
            cls = "ORDER"
        elif len(t) == len(c):
            cs = [classify_pair(a, b) for a, b in zip(t, c)]
            cls = Counter(cs).most_common(1)[0][0] if cs else "OPCODE"
        else:
            cls = "OPCODE"
        hunks.append({"cls": cls, "at": i1, "t": t, "c": c})
    return hunks


def causal_diff(adapter, target, cand, symbols):
    out = {"symbols": {}, "classes": Counter(), "hunks": 0}
    ta, ca = text_rows(adapter, target, symbols), text_rows(adapter, cand, symbols)
    for s in symbols:
        if ta[s] is None or ca[s] is None:
            out["symbols"][s] = {"absent": True}
            out["classes"]["MISSING"] += 1
            continue
        h = diff_rows(ta[s], ca[s])
        out["symbols"][s] = {"hunks": h, "n_target": len(ta[s]), "n_cand": len(ca[s])}
        for x in h:
            out["classes"][x["cls"]] += 1
        out["hunks"] += len(h)
    out["classes"] = dict(out["classes"])
    out["primary"] = max(out["classes"], key=out["classes"].get) if out["classes"] else None
    return out


def attribute(before, after):
    """Causal attribution of one source edit: per-class delta of the diff (negative = the edit removed that cause). `verdict` is IMPROVED /
    REGRESSED / NEUTRAL by total hunk count, ties broken by nothing (NEUTRAL)."""
    keys = set(before["classes"]) | set(after["classes"])
    delta = {k: after["classes"].get(k, 0) - before["classes"].get(k, 0) for k in sorted(keys)}
    d = after["hunks"] - before["hunks"]
    return {"delta": delta, "hunks_delta": d, "verdict": "IMPROVED" if d < 0 else ("REGRESSED" if d > 0 else "NEUTRAL")}
