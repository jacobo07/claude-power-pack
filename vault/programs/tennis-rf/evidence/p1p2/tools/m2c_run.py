"""WU-P1P2: m2c over the 1,797 Tennis functions in a process pool, one arm per call, plus source_lint per output.

    KSR_DECOMP_TOOLS=/opt/ksr-decomp /opt/ksr-decomp/venv/bin/python m2c_run.py <arm noctx|ctx> <out_dir> <facts.jsonl>
        [--context <header copy>] [--jobs 20]
Per-function isolation, adaptation and admission are m2c_producer.py's own (imported unchanged). Each function gets a
120 s alarm (status TIMEOUT). Lint (gex44/source_lint.py, unchanged), family "C" / flags "-lang c":
  ctx arm  : clean = L1 and lint(compose(raw)) == []  (the compiled unit; lint(raw) is recorded but the current lint
             flags MISSING_PRELUDE on any bare text using s32 etc. by design: the prelude lives in the header)
  noctx arm: clean = L1 and lint(M2C_TYPES + raw) == []  (prelude only, no struct knowledge)
Writes <out_dir>/records.jsonl and <out_dir>/c/<fn>.c.
"""
import argparse
import contextlib
import hashlib
import io
import json
import multiprocessing as mp
import os
import re
import signal
import sys
import tempfile

M = "/home/kobii/missions/tennis-w11"
DECOMP = os.path.join(M, "wt/tools/wros/binary/decomp")
ASM = os.path.join(M, "wst_tennis/step0/split_sports/out/asm")
sys.path.insert(0, DECOMP)
sys.path.insert(0, os.path.join(DECOMP, "gex44"))
import m2c_producer as P  # noqa: E402
import source_lint  # noqa: E402
import tennis_context  # noqa: E402

QTYPE = re.compile(r'(?<![\w])\?(?![\w])')
UNK = re.compile(r'(?:->|\.)\s*unk[0-9A-Fa-f]+\b')
G = {}


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def init(flags, context, arm):
    sys.path.insert(0, P.M2C)
    from m2c.main import parse_flags, run
    G.update(parse_flags=parse_flags, run=run, flags=flags, context=context, arm=arm)
    G["ctx_text"] = open(context, encoding="utf-8").read() if context else None
    sys.setrecursionlimit(min(2 ** 31 - 1, 10 * sys.getrecursionlimit()))
    signal.signal(signal.SIGALRM, _alarm)


def one(job):
    fn, start, block, extra = job
    status, err, c = "OK", "", ""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "fn.s")
        open(src, "w", encoding="utf-8").write(block + "".join("\n" + t for t in extra))
        out, eb = io.StringIO(), io.StringIO()
        signal.alarm(120)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(eb):
                rc = G["run"](G["parse_flags"](G["flags"] + [src]))
            c = out.getvalue()
            if rc != 0:
                why = eb.getvalue() or c
                why = why[why.find("Decompilation failure"):] if "Decompilation failure" in why else why
                status, err = "M2C_FAILED", " ".join(why.replace("/*", "").replace("*/", "").split())[:300]
        except Timeout:
            status, err = "TIMEOUT", "120 s alarm"
        except Exception as e:  # one function's failure is recorded, never propagated
            status, err = "EXCEPTION", "%s: %s" % (type(e).__name__, str(e)[:300])
        finally:
            signal.alarm(0)
    adm = P.admit(status, c)
    rec = dict(fn=fn, id="main:" + start, status=adm, error=err, c_sha256=hashlib.sha256(c.encode()).hexdigest() if c else "",
               n_unresolved_types=len(QTYPE.findall(source_lint.strip_noise(c))) if c else None,
               n_unk_fields=len(UNK.findall(source_lint.strip_noise(c))) if c else None)
    if G["arm"] == "ctx":
        raw = source_lint.lint_unit(c, "C", "-lang c") if c else ["NO_OUTPUT"]
        comp = source_lint.lint_unit(tennis_context.compose(c, G["ctx_text"]), "C", "-lang c") if c else ["NO_OUTPUT"]
        rec.update(lint_raw=raw, lint_composed=comp, clean=adm == "L1" and not comp)
    else:
        pre = source_lint.lint_unit(tennis_context.M2C_TYPES + c, "C", "-lang c") if c else ["NO_OUTPUT"]
        raw = source_lint.lint_unit(c, "C", "-lang c") if c else ["NO_OUTPUT"]
        rec.update(lint_prelude=pre, lint_raw=raw, clean=adm == "L1" and not pre)
    rec["lint_codes"] = sorted({x.split(":")[0] for x in rec.get("lint_composed", rec.get("lint_prelude", []))})
    return rec, c


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("arm", choices=["noctx", "ctx"])
    ap.add_argument("out")
    ap.add_argument("facts")
    ap.add_argument("--context")
    ap.add_argument("--jobs", type=int, default=20)
    a = ap.parse_args(argv)
    if not P.venv_ok(sys.executable, P.TOOLS):
        print("M2C_REFUSED: factory venv python required")
        return 2
    if (a.arm == "ctx") != bool(a.context):
        print("ARM_CONTEXT_MISMATCH")
        return 2
    flags = P.build_flags(False, a.context)
    rows = [json.loads(l) for l in open(a.facts)]
    text, tables = P.blocks(ASM)
    jobs = []
    for r in rows:
        block = text[r["fn"]]
        extra = []
        for t in sorted(set(P.TABLE_REF.findall(block))):
            if t in tables:
                block, tab = P.adapt_table(block, tables[t], r["fn"], int(r["addr"], 16))
                extra.append(tab)
        jobs.append((r["fn"], r["addr"], block, extra))
    if a.context:  # warm m2c's context cache once, before forking, so workers only read it
        init(flags, a.context, a.arm)
        one(jobs[0])
    os.makedirs(os.path.join(a.out, "c"), exist_ok=True)
    n = 0
    with mp.get_context("fork").Pool(a.jobs, initializer=init, initargs=(flags, a.context, a.arm)) as pool, \
            open(os.path.join(a.out, "records.jsonl"), "w") as w:
        for rec, c in pool.imap_unordered(one, jobs, chunksize=4):
            if c:
                open(os.path.join(a.out, "c", rec["fn"] + ".c"), "w", encoding="utf-8").write(c)
            w.write(json.dumps(rec, sort_keys=True) + "\n")
            w.flush()
            n += 1
    print("M2C_RUN_DONE arm=%s rows=%d" % (a.arm, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
