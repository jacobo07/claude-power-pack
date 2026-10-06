#!/usr/bin/env python
"""test_e1_mechanical_cleanup.py -- a paid measurement survives a temp-dir cleanup failure (post-E1 D5).

6124eecf: on Windows a process the CLI left behind held e1_mechanical's temp cwd, cleanup raised, and a
measurement already paid for was lost. The fix is TemporaryDirectory(ignore_cleanup_errors=True). This test
drives `one_call` with a fake CLI (no model) that prints a valid usage report and leaves a detached child
holding the cwd and an open file in it:

  V-E1M-HOLD-REAL    positive control: the unpatched-flag mutant raises, so the hold really breaks cleanup
                     (without it, GREEN below would prove nothing)
  V-E1M-SURVIVES     the real module returns MEASURED with the fake's context under the same hold
  V-E1M-CORRUPT-*    corrupt-usage controls: zeros and absent fields are UNMEASURED, never MEASURED

    python vault/programs/cognitive-economy/measure/test_e1_mechanical_cleanup.py
Exit 0 = all pass; 1 = a failure; 2 = INCONCLUSIVE (the hold did not break cleanup on this host).
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "e1_mechanical.py"
FLAG = "ignore_cleanup_errors=True"

FAKE = r'''
import json, os, subprocess, sys
mode = os.environ["E1M_FAKE_MODE"]
if mode == "hold":
    child = ("import os,time; f=open('held.txt','w'); f.write('x'); f.flush(); "
             "open(os.environ['E1M_PIDFILE'],'w').write(str(os.getpid())); time.sleep(30)")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen([sys.executable, "-c", child], cwd=os.getcwd(), stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, creationflags=flags)
    import time
    for _ in range(100):
        if os.path.exists(os.environ["E1M_PIDFILE"]) and os.path.getsize(os.environ["E1M_PIDFILE"]):
            break
        time.sleep(0.05)
    usage = {"input_tokens": 2, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 900, "output_tokens": 1}
elif mode == "zeros":
    usage = {"input_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0, "output_tokens": 0}
else:
    usage = {"input_tokens": 2, "output_tokens": 1}
print(json.dumps({"type": "result", "is_error": False, "session_id": "fake", "num_turns": 1, "usage": usage}))
'''


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Shim:
    """Stands in for the module's `subprocess`: runs the fake instead of a real CLI."""
    TimeoutExpired = subprocess.TimeoutExpired

    def __init__(self, fake: Path):
        self.fake = fake

    def run(self, cmd, **kw):
        return subprocess.run([sys.executable, str(self.fake)] + list(cmd[1:]), **kw)


def kill(pidfile: Path) -> None:
    try:
        pid = int(pidfile.read_text().strip())
    except (OSError, ValueError):
        return
    subprocess.run(["taskkill", "/F", "/PID", str(pid)] if os.name == "nt" else ["kill", "-9", str(pid)],
                   capture_output=True)
    time.sleep(0.3)


def call(mod, fake: Path, mode: str, pidfile: Path):
    os.environ["E1M_FAKE_MODE"] = mode
    os.environ["E1M_PIDFILE"] = str(pidfile)
    pidfile.write_text("")
    mod.subprocess = Shim(fake)
    try:
        return mod.one_call("claude", "m", None), None
    except OSError as exc:
        return None, exc
    finally:
        kill(pidfile)


def main() -> int:
    results = []
    with tempfile.TemporaryDirectory(prefix="e1m-test-", ignore_cleanup_errors=True) as tmp:
        t = Path(tmp)
        fake, pidfile = t / "fake_claude.py", t / "child.pid"
        fake.write_text(FAKE, encoding="utf-8")
        text = SRC.read_text(encoding="utf-8")
        if FLAG not in text:
            print(f"FAIL V-E1M-FLAG the fix ({FLAG}) is not in {SRC.name}")
            return 1
        mutant_path = t / "e1_mechanical_mutant.py"
        mutant_path.write_text(text.replace(FLAG, "ignore_cleanup_errors=False"), encoding="utf-8")
        mutant, real = load(mutant_path, "e1m_mutant"), load(SRC, "e1m_real")

        res, exc = call(mutant, fake, "hold", pidfile)
        if exc is None:
            print(f"INCONCLUSIVE V-E1M-HOLD-REAL the hold did not break cleanup here (mutant returned {res})")
            return 2
        results.append(("V-E1M-HOLD-REAL", True, f"mutant lost the measurement: {type(exc).__name__}"))

        res, exc = call(real, fake, "hold", pidfile)
        ok = exc is None and res and res.get("state") == "MEASURED" and res.get("context") == 1002
        results.append(("V-E1M-SURVIVES", bool(ok), f"result={res} exc={exc!r}"))

        for mode in ("zeros", "absent"):
            res, exc = call(real, fake, mode, pidfile)
            ok = exc is None and res and res.get("state") == "UNMEASURED"
            results.append((f"V-E1M-CORRUPT-{mode}", bool(ok), f"result={json.dumps(res)[:160]}"))

    for gid, ok, ev in results:
        print(f"  {'ok' if ok else 'FAIL'}   {gid} {ev}")
    passed = sum(ok for _, ok, _ in results)
    print(f"E1M_CLEANUP={'PASS' if passed == len(results) else 'FAIL'} {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
