"""V-CFP gate: vendored packet-builder CREDENTIAL filter false positives (backlog D33 item 2).
Runs the builder's own CREDENTIAL regex (extracted from its source) in node. Prints CFP_PASS=n/n."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILDER = ROOT / "vendor/genesis-suite/modules/genesis-source-packets/index.cjs"
COPIES = [ROOT / "vendor/genesis-suite/modules/genesis-task-context/lib/genesis-source-packets.cjs",
          ROOT / "vendor/genesis-suite/modules/genesis-batch-drafts/lib/genesis-source-packets.cjs"]
CONTROLS = ["tools/floor_regression_gate.py", "tools/test_floor_regression_gate.py", "tools/cep_gen2.py"]
FIX = '(?!\\s*["\']?(?:\\$?\\{|\\d+\\s*[,}/]\\d*))'
NODE = ("const fs=require('fs');const src=fs.readFileSync(process.argv[1],'utf8');"
        "const l=src.split('\\n').find(x=>x.startsWith('const CREDENTIAL'));"
        "const CREDENTIAL=eval(l.replace(/^const CREDENTIAL =/,'(').replace(/;\\s*$/,'')+')');"
        "const raw=fs.readFileSync(process.argv[2],'utf8');"
        "process.stdout.write(CREDENTIAL.test(raw)?'BLOCKED':'ADMITTED');")


def verdict(builder: Path, target: Path) -> str:
    # target may be a Path, or an inline text file written by the caller
    r = subprocess.run(["node", "-e", NODE, str(builder), str(target)], capture_output=True, text=True, timeout=60)
    return r.stdout.strip() or ("ERR:" + r.stderr[:80])


results = []


def check(name, ok):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name)


import tempfile
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    # fake key built at runtime so this file carries no key-shaped literal
    fake = d / "fake.txt"
    fake.write_text("tok = '" + "sk" + "-" + "A1b2C3d4E5f6G7h8I9j0" + "'\n" + "pass" + "word" + "=" + "hunter2hunter2xx\n")
    for c in CONTROLS:
        check(f"V-CFP-ADMIT {c}", verdict(BUILDER, ROOT / c) == "ADMITTED")
    for c in COPIES:
        check(f"V-CFP-COPY-SYNC {c.parts[-3]}", FIX in c.read_text(encoding="utf-8") and FIX in BUILDER.read_text(encoding="utf-8"))
    check("V-CFP-FAKE-KEY-STILL-BLOCKED", verdict(BUILDER, fake) == "BLOCKED")
    # mutant: fix reverted in memory -> an admitted control returns to BLOCKED
    mut = d / "mutant.cjs"
    mut.write_text(BUILDER.read_text(encoding="utf-8").replace(FIX, ""), encoding="utf-8")
    back = [c for c in CONTROLS if verdict(mut, ROOT / c) == "BLOCKED"]
    check(f"V-CFP-MUTANT-REVERTED-BLOCKS ({len(back)}/{len(CONTROLS)} back to BLOCKED)", len(back) >= 1)

n = sum(results)
print(f"CFP_PASS={n}/{len(results)}")
sys.exit(0 if n == len(results) else 1)
