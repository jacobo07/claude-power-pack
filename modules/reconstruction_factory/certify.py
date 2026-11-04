"""Exact certification. A certificate is issued only when TWO instruments that share no code agree and the controls bracket holds:

  INDEPENDENT evidence (both required, disagreement = DISAGREEMENT, never a pass):
    ELF   judge.judge   -- section bytes with relocation fields masked, relocation rows, local data
    TEXT  objdump text  -- (opcode, operands, reloc) rows of each symbol's extent, address-normalised
  CORROBORATING evidence (necessary, not sufficient): deterministic rebuild (two clean compiles give the same object digest),
    positive control (target vs itself is EXACT, before and after), negative control (candidate with one code byte flipped is refused).
  TOOLCHAIN: exactness is evaluated under the pinned recipe and every manifest variant of it. Exact only under a non-pinned
    variant = UNDERDETERMINED_TOOLCHAIN (no certificate). Held-out functions are refused until released.

Verdicts: CERTIFIED_EXACT, NOT_EXACT, UNDERDETERMINED_TOOLCHAIN, DISAGREEMENT, CONTROL_FAILED, REBUILD_UNSTABLE, COMPILE_FAILED, HELDOUT_NOT_RELEASED.
"""
import hashlib
import os
import tempfile

from . import judge as J
from .elf import Elf

CERT_VERDICTS = ("CERTIFIED_EXACT", "NOT_EXACT", "UNDERDETERMINED_TOOLCHAIN", "DISAGREEMENT", "CONTROL_FAILED", "REBUILD_UNSTABLE",
                 "COMPILE_FAILED", "HELDOUT_NOT_RELEASED")


def text_rows(adapter, obj, symbols):
    """Per-symbol list of (op, args, reloc type, reloc sym) from the disassembler, offsets rebased to the symbol start. None if a symbol is absent."""
    with open(obj, "rb") as fh:
        e = Elf(fh.read())
    out = {}
    cache = {}
    for s in symbols:
        x = e.extent(s)
        if x is None:
            out[s] = None
            continue
        sec, off, size = x
        if sec["name"] not in cache:
            cache[sec["name"]] = adapter.disasm(obj, sec["name"])
        out[s] = [(r["op"], r["args"], (r["reloc"] or {}).get("type"), (r["reloc"] or {}).get("sym"))
                  for r in cache[sec["name"]] if off <= r["off"] < off + size]
    return out


def text_equal(adapter, target, cand, symbols):
    a, b = text_rows(adapter, target, symbols), text_rows(adapter, cand, symbols)
    return all(a[s] is not None and a[s] == b[s] and len(a[s]) > 0 for s in symbols)


def flip_byte(src, dst, symbols):
    """Negative control object: copy src, flip one bit of the first code byte of the first symbol. Always differs from src in a judged extent."""
    with open(src, "rb") as fh:
        data = bytearray(fh.read())
    e = Elf(bytes(data))
    sec, off, size = e.extent(symbols[0])
    if size < 1:
        raise ValueError("empty symbol")
    data[sec["off"] + off + size - 1] ^= 0x01
    with open(dst, "wb") as fh:
        fh.write(bytes(data))
    return dst


def sha_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def certify(factory, fn, text, released=False):
    P = factory.project
    f = P.functions[fn]
    cert = {"function": fn, "verdict": None, "evidence": {"independent": {}, "corroborating": {}}, "toolchain": {"pinned": f["recipe"], "exact_under": []},
            "adapter": factory.adapter.id, "adapter_version": factory.adapter.version()}
    if f.get("heldout") and not released:
        cert["verdict"] = "HELDOUT_NOT_RELEASED"
        return cert
    symbols = f["symbols"]
    res, comp = factory.judge_text(fn, text)
    cert["pct"] = res.get("pct")
    if not comp.ok:
        cert["verdict"] = "COMPILE_FAILED"
        return cert
    target = factory.target(fn)
    ev = cert["evidence"]
    ev["independent"]["elf"] = bool(res["exact"])
    ev["independent"]["text"] = bool(text_equal(factory.adapter, target, comp.obj, symbols))
    if ev["independent"]["elf"] != ev["independent"]["text"]:
        cert["verdict"] = "DISAGREEMENT"
        return cert
    if not ev["independent"]["elf"]:
        cert["verdict"] = "NOT_EXACT"
        cert["reasons"] = res["reasons"]
        # toolchain discrimination: is it exact under another recipe variant of the pinned base?
        for vid, v in P.doc["toolchain"].get("variant", {}).items():
            if v["base"] != f["recipe"]:
                continue
            r2, c2 = factory.judge_text(fn, text, variant=vid)
            if c2.ok and r2["exact"] and text_equal(factory.adapter, target, c2.obj, symbols):
                cert["toolchain"]["exact_under"].append(vid)
        if cert["toolchain"]["exact_under"]:
            cert["verdict"] = "UNDERDETERMINED_TOOLCHAIN"
        return cert
    # corroboration
    with tempfile.TemporaryDirectory(prefix="rf-neg-") as d:
        again = factory.compile_text(fn, text)
        ev["corroborating"]["rebuild_stable"] = bool(again.ok and again.obj_sha256 == comp.obj_sha256)
        ev["corroborating"]["positive_control"] = bool(J.judge(target, target, symbols)["exact"])
        neg = flip_byte(comp.obj, os.path.join(d, "neg.o"), symbols)
        ev["corroborating"]["negative_control_refused"] = J.judge(target, neg, symbols)["exact"] is False
        ev["corroborating"]["positive_control_after"] = bool(J.judge(target, comp.obj, symbols)["exact"])
    c = ev["corroborating"]
    if not c["rebuild_stable"]:
        cert["verdict"] = "REBUILD_UNSTABLE"
    elif not (c["positive_control"] and c["negative_control_refused"] and c["positive_control_after"]):
        cert["verdict"] = "CONTROL_FAILED"
    else:
        cert["verdict"] = "CERTIFIED_EXACT"
        cert["toolchain"]["exact_under"] = [f["recipe"]]
        cert["candidate_sha256"] = comp.obj_sha256
        cert["source_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    return cert
