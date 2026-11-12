"""Coordinator (c84eb8e1) independent check of S34KC receipts (adapted from the ddf4990e indep_v2 method).
Per receipt: the source is the evidence .c file whose sha256 equals src_sha256 (content hash, not name); flags are
ksr_lane.arms()[arm]; the compiled function bytes are compared with the ORIGINAL DOL at the receipt address, masking
only words the compiled object's own relocations touch; size must equal the stage capsule target symbol's size.
Negative control on EVERY receipt: the same code vs DOL at address+4 must show unexplained differences.
Usage (from the t1 root): python3 -I indep_s34kc.py <receipts.jsonl> [...]"""
import glob, hashlib, importlib.util, json, os, sys, tempfile
sys.path = [p for p in sys.path if p not in ("/tmp", "")]  # /tmp holds stray modules (dis.py) that shadow the stdlib
_spec = importlib.util.spec_from_file_location("indep_check", "/home/kobii/agora/indep-c84/indep_check.py")
ic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ic)  # chdir to t1 + sys.path; DOL path; dol_reader; elf_fn
from modules.recon_fabric import ksr_lane, cv1  # noqa: E402

CAP = "/home/kobii/ksr_stage/ksrmb-s25-20261111-140212/capsule"
srcs = {}
for f in glob.glob("evidence/ascension/s3[045]k*/**/*.c", recursive=True):
    srcs.setdefault(hashlib.sha256(open(f, "rb").read()).hexdigest(), f)
read, dsha = ic.dol_reader(ic.DOL)
print("DOL", dsha[:16], "sources indexed", len(srcs))
tc, arms = cv1.toolchain(), ksr_lane.arms()
n = good = neg = 0
for fn in sys.argv[1:]:
    for line in open(fn):
        r = json.loads(line)
        n += 1
        addr = int(r["id"].split(":")[1], 16)
        sf = srcs.get(r["src_sha256"])
        if not sf:
            print(r["id"], "SOURCE_NOT_FOUND"); continue
        src = open(sf, encoding="utf-8", errors="replace").read()
        rc, o = 1, None
        for text in (src, ksr_lane.prelude() + src):
            rc, o = ksr_lane.compile_fn(tc, text, arms[r["arm"]], tempfile.mkdtemp())
            if rc == 0:
                break
        if rc != 0:
            print(r["id"], "COMPILE_FAIL", sf); continue
        code, masked = ic.elf_fn(o, r["sym"])
        # receipts name the object relative to capsule/split ("obj/..."); cohorts relative to capsule ("split/obj/...")
        tp = next((p for p in (os.path.join(CAP, r["obj"]), os.path.join(CAP, "split", r["obj"])) if os.path.exists(p)), None)
        if not tp:
            print(r["id"], "TARGET_OBJECT_NOT_FOUND", r["obj"]); continue
        tcode, _ = ic.elf_fn(tp, r["sym"])
        un = [i for i in range(0, len(code), 4) if code[i:i + 4] != read(addr, len(code))[i:i + 4] and i not in masked]
        sh = read(addr + 4, len(code))
        u2 = [i for i in range(0, len(code), 4) if code[i:i + 4] != sh[i:i + 4] and i not in masked]
        ok = len(code) == len(tcode) and not un
        good += ok
        neg += bool(u2)
        print(r["id"], r["arm"], "size", len(code), "target", len(tcode), "masked", len(masked), "unexplained", len(un),
              "OK" if ok else "FAIL", "neg+4", "detected" if u2 else "BLIND")
print(f"checked {n} ok {good} neg_detected {neg}")
print("INDEP_S34KC_PASS" if n > 0 and good == n and neg == n else "INDEP_S34KC_FAIL")
