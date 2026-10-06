"""V-WAKE gates: both poles of the zero-model wake check, driven through the scheduled command itself."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
fails = 0


def check(name, ok, ev=""):
    global fails
    print(("PASS " if ok else "FAIL ") + name + " " + str(ev))
    fails += 0 if ok else 1


def run_task(gate_exit, tmp):
    gate = tmp / f"gate{gate_exit}.py"
    gate.write_text(f"import sys; sys.exit({gate_exit})", encoding="utf-8")
    flag = tmp / f"flag{gate_exit}.json"
    env = dict(os.environ, PP_WAKE_GATE_CMD=json.dumps([sys.executable, str(gate)]), PP_WAKE_FLAG=str(flag))
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "vault_summarize.py"), "--check"],
                       capture_output=True, text=True, env=env, cwd=str(tmp))
    line = next((l for l in p.stdout.splitlines() if l.startswith("WAKE_CHECK ")), None)
    return p.returncode, (json.loads(line[11:]) if line else None), flag, p.stdout


with tempfile.TemporaryDirectory() as t:
    tmp = Path(t)
    rc, rep, flag, out = run_task(0, tmp)
    check("V-WAKE-DORMANT", rep and rep["wake"] is False and rep["model_calls"] == 0 and not flag.exists(), rep)
    rc1, rep1, flag1, out1 = run_task(1, tmp)
    check("V-WAKE-FLIP", rep1 and rep1["wake"] is True and rep1["model_calls"] == 0 and flag1.exists(), rep1)
    rc2, rep2, flag2, _ = run_task(2, tmp)
    check("V-WAKE-UNKNOWN-NOT-GREEN", rep2 and rep2["wake"] is True and rep2["reason"].startswith("UNKNOWN"), rep2)
    check("V-WAKE-EXIT-UNCHANGED", rc == rc1 == rc2, (rc, rc1, rc2))
import wake_check
c = {"model_calls": 0}
try:
    wake_check.run_gate([sys.executable, "x.py", "--probe"], c)
    check("V-WAKE-MODEL-REFUSED", False, "no raise")
except RuntimeError:
    check("V-WAKE-MODEL-REFUSED", c["model_calls"] == 1, c)
sys.exit(1 if fails else 0)
