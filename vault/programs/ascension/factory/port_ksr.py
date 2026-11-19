#!/usr/bin/env python3
"""Lane merge KSR -> WSR (Owner 2026-11-19 "go ahead to both", pane 81dcf473): KSR (t1-campaign) and WSR (wsr-decomp)
reconstruct the same main.dol (sha1 7752caae). Port every KSR CERTIFIED function that WSR's report does not yet hold at
100% into WSR as a per-function unit, re-verified against WSR's OWN dtk target object before anything is written.

Source per receipt component: cert1-llm -> its src_path (as is, else with the typedef prelude); every other component ->
the KSR m2c lift (decomp_work m2c_main/c/main_<ADDR>.c) through the lane transform (repair.transform_v5 +
toolchain_sd.retype) plus the prelude, exactly as ksr_lane certified it. Compiler = KSR's (Wii/1.7, sha f54d5644), flags
= the receipt's own. A function is carved only if (a) it compiles, (b) objdiff gives 100% against the WSR target object
that defines its symbol, (c) its address lies outside every existing split unit. Unit:
Object(NonMatching, "factory/<sym>.c", cflags=[receipt flags], mw_version="Wii/1.7") in the Factory lib.

usage: port_ksr.py --repo WSR_SCRATCH [--limit N]   (prints a JSON summary; writes <repo>/factory_port_ksr.jsonl)
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile

T1 = "/home/kobii/missions/t1-campaign"
sys.path.insert(0, T1)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.recon_fabric import cv1  # noqa: E402
import factory as F  # noqa: E402

M2C_C = "/home/kobii/decomp_work/b8d1db7edd42/m2c_main/c"
GAME = "RZTP01"
MW_VERSION = "Wii/1.7"


def flag_items(flags):
    out = []
    for t in flags.split():
        if t.startswith("-") or not out:
            out.append(t)
        else:
            out[-1] += " " + t
    return out


def compile_pct(tc, src, flags, sym, targets):
    work = tempfile.mkdtemp(prefix="port-")
    try:
        open(os.path.join(work, "fn.c"), "w", encoding="utf-8", newline="\n").write(src)
        try:
            rc = subprocess.run([tc["wibo"], tc["mw"]] + flags.split() + ["-c", "fn.c", "-o", "fn.o"], cwd=work,
                                capture_output=True, timeout=90).returncode
        except subprocess.TimeoutExpired:
            return "TIMEOUT", None
        o = os.path.join(work, "fn.o")
        if rc != 0 or not os.path.exists(o) or sym not in cv1.elf_funcs(o):
            return "NO_COMPILE", None
        for t in targets:
            if cv1.objdiff_pct(tc, t, o, sym, work) == 100.0:
                return "MATCH", t
        return "NO_MATCH", None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    ws, rng = {}, []
    for l in open(os.path.join(a.repo, "config", GAME, "symbols.txt")):
        m = re.match(r"\s*(\S+)\s*=\s*\.text:0x([0-9A-Fa-f]+);.*type:function.*size:0x([0-9A-Fa-f]+)", l)
        if m:
            ws[int(m.group(2), 16)] = (m.group(1), int(m.group(3), 16))
    splits_p = os.path.join(a.repo, "config", GAME, "splits.txt")
    for m in re.finditer(r"\.text\s+start:0x([0-9A-Fa-f]+)\s+end:0x([0-9A-Fa-f]+)", open(splits_p).read()):
        rng.append((int(m.group(1), 16), int(m.group(2), 16)))
    r = json.load(open(os.path.join(a.repo, "build", GAME, "report.json")))
    done = {f.get("name") for u in r["units"] for f in u.get("functions") or [] if f.get("fuzzy_match_percent") == 100}
    idx = F.target_index(a.repo, GAME)
    tc = dict(cv1.toolchain())  # KSR's own toolchain: mw = Wii/1.7
    pre = F.prelude()
    todo = []
    for p in sorted(glob.glob(os.path.join(T1, "evidence/cert1*/receipts.jsonl"))):
        comp = p.split("/")[-2]
        for l in open(p):
            x = json.loads(l)
            if x.get("verdict") != "CERTIFIED":
                continue
            m = re.search(r"([0-9A-Fa-f]{8})$", x.get("id") or x.get("key") or x.get("fn") or x.get("sym") or "")
            if not m:
                continue
            addr = int(m.group(1), 16)
            if addr in ws and ws[addr][0] not in done:
                todo.append((addr, comp, x))
    seen, out = set(), []
    todo.sort(key=lambda t: t[0])
    if a.limit:
        todo = todo[:a.limit]
    for addr, comp, x in todo:
        if addr in seen:
            continue
        sym, size = ws[addr]
        row = {"addr": "%08X" % addr, "sym": sym, "comp": comp, "size": size}
        if any(s <= addr < e for s, e in rng):
            row["state"] = "IN_EXISTING_SPLIT"; out.append(row); continue
        targets = idx.get(sym) or []
        if not targets:
            row["state"] = "NO_TARGET"; out.append(row); continue
        if comp == "cert1-llm":
            raw = open(os.path.join(T1, x["src_path"]), encoding="utf-8", errors="replace").read()
            cands = [raw, pre + raw]
        else:
            lift = os.path.join(M2C_C, "main_%08X.c" % addr)
            if not os.path.exists(lift):
                row["state"] = "NO_LIFT"; out.append(row); continue
            try:
                cands = [pre + F.transform(open(lift, encoding="utf-8", errors="replace").read())]
            except Exception as e:  # recorded, never silent
                row["state"] = "XF_ERROR:" + type(e).__name__; out.append(row); continue
        st = None
        for src in cands:
            st, tgt = compile_pct(tc, src, x["flags"], sym, targets)
            if st == "MATCH":
                break
        row["state"] = st
        if st == "MATCH":
            unit = "factory/%s.c" % sym
            dst = os.path.join(a.repo, "src", unit)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "w", encoding="utf-8", newline="\n").write(
                "/* KSR certificate %s (%s), ported to WSR: objdiff 100%% vs WSR target, %s */\n%s" % (comp, x.get("batch") or x.get("run"), MW_VERSION, src))
            row["unit"], row["flags"] = unit, x["flags"]
            rng.append((addr, addr + size))
            seen.add(addr)
        out.append(row)
    new = [r for r in out if r.get("state") == "MATCH"]
    if new:
        open(splits_p, "a", encoding="utf-8", newline="\n").write("\n" + "\n".join(
            "%s:\n\t.text       start:0x%s end:0x%08X\n" % (r["unit"], r["addr"], int(r["addr"], 16) + r["size"]) for r in new))
        cfg_p = os.path.join(a.repo, "configure.py")
        cfg = open(cfg_p, encoding="utf-8").read()
        i = cfg.index('"lib": "Factory",')
        j = cfg.index('"objects": [', i) + len('"objects": [')
        body = "\n".join('            Object(NonMatching, "%s", cflags=[%s], mw_version="%s"),' % (
            r["unit"], ", ".join(json.dumps(f) for f in flag_items(r["flags"])), MW_VERSION) for r in new)
        open(cfg_p, "w", encoding="utf-8", newline="\n").write(cfg[:j] + "\n" + body + cfg[j:])
    with open(os.path.join(a.repo, "factory_port_ksr.jsonl"), "w", newline="\n") as w:
        for r in out:
            w.write(json.dumps(r) + "\n")
    states = {}
    for r in out:
        states[r["state"]] = states.get(r["state"], 0) + 1
    print(json.dumps({"candidates": len(todo), "states": states, "carved": len(new), "bytes": sum(r["size"] for r in new)}))


if __name__ == "__main__":
    main()
