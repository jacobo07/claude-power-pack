#!/usr/bin/env python
"""Mutation drills for hooks/doctrine_cards.js on an ISOLATED copy (same protocol as
tools/mutation_drill.py, which runs only python suites): a clean-copy control must pass 15/15, then
each mutant must turn its named gate to FAIL, and the live card's SHA-256 must be unchanged at the end.

    python hooks/tests/drill-doctrine-cards.py
"""
import hashlib, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
LIVE = HOOKS / "doctrine_cards.js"
TEST = HOOKS / "tests" / "test-doctrine-cards.js"
MUTANTS = [  # (gate that must FAIL, anchor, replacement) -- one invariant each
    ("V-DC-SAME-FILE-FOREIGN", "!own.added.has(l.trim())", "false"),                       # G'1 ownership
    ("V-DC-COMMIT-AM", "if (a.includes('a')) all = true;", ""),                             # G'2 -am cluster
    ("V-DC-AMEND-UNKNOWN", "if (a === '--amend' || ", "if ("),                              # G'2 amend
    ("V-DC-NONCOMMIT-NO-IO", "if (!COMMIT_RE.test(elideLiteralBodies(command)))",
     "ledger({ decision: 'seen' }); if (!COMMIT_RE.test(elideLiteralBodies(command)))"),     # G'11
    ("V-DC-DENY-ONCE", "if (fs.existsSync(flag))", "if (false)"),                            # once per foreign set
    ("V-DC-SHELL-WRITE-UNKNOWN", "own.shell.some((c) => c.toLowerCase().includes(base))", "false"),
    ("V-DC-SUBAGENT-OWN", "if (f.endsWith('.jsonl')) files.push(path.join(sub, f));", "void f;"),  # G'9
    ("V-DC-LEDGER-NEVER-DENIES", "if (MODE !== 'deny')", "if (MODE === 'never')"),           # G'3
]


def run(copy: Path) -> str:
    r = subprocess.run(["node", str(copy / "tests" / "test-doctrine-cards.js")], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300)
    return r.stdout + r.stderr


def fresh(src: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="dc-drill-")) / "hooks"
    (d / "tests").mkdir(parents=True)
    (d / "doctrine_cards.js").write_text(src, encoding="utf-8")
    shutil.copyfile(TEST, d / "tests" / "test-doctrine-cards.js")
    return d


live_sha = hashlib.sha256(LIVE.read_bytes()).hexdigest()
src = LIVE.read_text(encoding="utf-8")
ctrl = run(fresh(src))
m = re.search(r"DOCTRINE_CARDS_PASS=(\d+)/(\d+)", ctrl)
if not m or m.group(1) != m.group(2):
    print("CONTROL_INVALID:", ctrl[-400:]); sys.exit(4)
print(f"control: DOCTRINE_CARDS_PASS={m.group(1)}/{m.group(2)}")
killed = 0
for gate, old, new in MUTANTS:
    if src.count(old) != 1:
        print(f"HARNESS {gate}: anchor matches {src.count(old)}x"); sys.exit(3)
    out = run(fresh(src.replace(old, new)))
    if re.search(rf"^FAIL {re.escape(gate)}:", out, re.M):
        verdict = "KILLED"; killed += 1
    elif "DOCTRINE_CARDS_PASS=" not in out:
        verdict = "UNJUDGED"
    else:
        verdict = "SURVIVED"
    print(f"MUTANT {verdict} gate={gate}")
if hashlib.sha256(LIVE.read_bytes()).hexdigest() != live_sha:
    print("HARNESS: live card changed during the drill"); sys.exit(3)
print(f"DRILL_PASS={killed}/{len(MUTANTS)}  live sha unchanged")
sys.exit(0 if killed == len(MUTANTS) else 1)
