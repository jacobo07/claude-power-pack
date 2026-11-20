#!/usr/bin/env python3
"""V-QTAP gates for hooks/statusline_quota_tap.js (BAMR P1). Process boundary: real node, real stdin bytes."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TAP = os.path.join(HERE, "..", "hooks", "statusline_quota_tap.js")
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
passes = fails = 0


def gate(name, cond, ev):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print("%s %s: %s" % ("PASS" if cond else "FAIL", name, ev))


def run(tmp, payload, extra_env=None):
    out = os.path.join(tmp, "qr.json")
    fake = os.path.join(tmp, "fake_statusline.js")
    with open(fake, "w") as f:   # stand-in for gsd-statusline.js: echoes what it received
        f.write("let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>{process.stdout.write('SL:'+s.length)});")
    env = dict(os.environ, CPP_QUOTA_TAP_OUT=out, CPP_QUOTA_TAP_TARGET=fake, **(extra_env or {}))
    p = subprocess.run([NODE, TAP], input=payload.encode("utf-8"), capture_output=True, env=env, timeout=20)
    rec = json.load(open(out)) if os.path.exists(out) else None
    return p, rec


with tempfile.TemporaryDirectory() as tmp:
    rl = {"five_hour": {"used_percentage": 42.5, "resets_at": 1795190000}}
    body = json.dumps({"version": "9.9", "model": {"display_name": "Opus"}, "rate_limits": rl})
    p, rec = run(tmp, body)
    gate("V-QTAP-PRESENT", rec and rec["source"] == "harness_statusline" and rec["rate_limits"] == rl,
         "rate_limits copied verbatim: %s" % (rec and rec["source"]))
    gate("V-QTAP-FORWARD", p.returncode == 0 and p.stdout.decode() == "SL:%d" % len(body),
         "real statusline got the identical stdin: rc=%d out=%r" % (p.returncode, p.stdout.decode()[:40]))

with tempfile.TemporaryDirectory() as tmp:
    p, rec = run(tmp, json.dumps({"version": "9.9", "cwd": "C:\\"}))
    gate("V-QTAP-ABSENT", rec and rec["source"] == "absent" and rec["rate_limits"] is None and rec["top_level_keys"] == ["cwd", "version"],
         "no rate_limits -> source absent, key names only: %s" % (rec and rec["top_level_keys"]))

with tempfile.TemporaryDirectory() as tmp:
    p, rec = run(tmp, "{not json")
    gate("V-QTAP-CORRUPT", p.returncode == 0 and rec is None and p.stdout.decode().startswith("SL:"),
         "unparseable stdin: nothing written, statusline still rendered, rc=%d" % p.returncode)

with tempfile.TemporaryDirectory() as tmp:
    p, rec = run(tmp, json.dumps({"rate_limits": rl}), {"CPP_QUOTA_TAP": "off"})
    gate("V-QTAP-KILLSWITCH", rec is None and p.stdout.decode().startswith("SL:"), "CPP_QUOTA_TAP=off forwards only")

print("QTAP_PASS=%d/%d" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
