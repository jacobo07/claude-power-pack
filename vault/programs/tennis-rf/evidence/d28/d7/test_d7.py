#!/usr/bin/env python3
"""V-D7-* gate. Reads <out>/{replay,controls}.json produced by d7.py; reruns the closure twice for determinism. Exit 0 iff all pass."""
import json, subprocess, sys, os
sys.path.insert(0, "/home/kobii/missions/tennis-w11/out/d28/tools"); sys.path.insert(0, "/home/kobii/missions/tennis-w11/out/d28/d5/tools")
import dirty, d5
out = sys.argv[1]
rp = json.load(open(out + "/replay.json")); ct = json.load(open(out + "/controls.json"))
C = dirty.load(); asm = d5.load()["text"]
ok = []
def chk(n, c, extra=""):
    ok.append(bool(c)); print(("PASS " if c else "FAIL ") + n, extra)
chk("V-D7-REPRO clean-set diff empty (5 variants)", all(not v["clean_diff"] for v in rp.values()))
chk("V-D7-REPRO-SHA output sha equals whole-corpus", all(v["sha_equal"] for v in rp.values()))
chk("V-D7-SOUND no full-run change outside closure", all(not v["full_changed_outside_closure"] for v in rp.values()))
chk("V-D7-CTRL-UNUSED empty closure", ct["unused_fact"]["size"] == 0)
chk("V-D7-CTRL-WIDE wide-struct closure covers every changed fn and equals full", not ct["wide_struct"]["full_changed_outside_closure"] and ct["wide_struct"]["clean_equal"] and ct["wide_struct"]["sha_equal"] and ct["wide_struct"]["closure_size"] > ct["unused_fact"]["size"], "size=%d" % ct["wide_struct"]["closure_size"])
chk("V-D7-CTRL-D6 closure contains every fn D6 saw change", not ct["d6_changed_in_closure"]["missing"] and len(ct["d6_changed_in_closure"]["d6_saw_change"]) == 3)
v = rp["D5_void_void"]
old = C["hctx"]; new = old.rstrip("\n") + "\nvoid fn_801D022C(void);\n"
a = dirty.closure(C, old, new, asm); b = dirty.closure(C, old, new, asm)
chk("V-D7-DET closure identical across runs", a == b and a[0] == dirty.closure(C, old, new, asm)[0])
chk("V-D7-SMALLER closure < 1797 for D6 deltas", all(v["closure_size"] < 1797 for v in rp.values()), str({k: x["closure_size"] for k, x in rp.items()}))
sys.exit(0 if all(ok) else 1)