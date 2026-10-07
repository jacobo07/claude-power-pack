"""A1-2 gate: `turns.py --attribute`, the program meter (gaps G3-G5 of amendment A1).

Hermetic: a temp sqlite with the index's `calls` columns and temp transcripts; never the live index.
Every bucket is driven from both sides, and three mutants must turn the checks red:
  MUT-lineage-off      the lineage rule removed (no read signal, no program roots) -- G4
  MUT-exclusion-off    ledger-metered sessions summed into tier A -- G5 double count
  MUT-shell-any-write  every shell command naming a program path booked as a write -- G5 (the
                       canary's first finding: a pane LISTING the program dir landed in tier A)
Prints CE_A1_ATTR_PASS=n/m; exit 0 only if all pass.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "turns", REPO / "vault/programs/cognitive-economy/measure/turns.py")
turns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(turns)

PP = "C:/Users/User/.claude/skills/claude-power-pack"
GEN2 = "C:/Users/User/Apps/pp-ce-gen2"
KC = "C:/Users/User/Desktop/Cursor Projects/KobiiCraft"
S1, S2, S3, S4, S5, S6, S7 = (f"{c * 8}-0000-4000-8000-000000000000" for c in "1234567")
N = 1111          # processed per call: inp 1 + cw 10 + cr 100 + out 1000
SINCE, UNTIL = 1000.0, 2000.0
passes = fails = 0


def _ok(tag: str, ev: str = "") -> None:
    global passes
    passes += 1
    print(f"  ok   {tag} {ev}")


def _fail(tag: str, diag: str = "") -> None:
    global fails
    fails += 1
    print(f"  FAIL {tag} {diag}")


def line(mid: str, cwd: str, tools=()) -> dict:
    return {"type": "assistant", "requestId": f"r{mid}", "timestamp": "2026-10-05T00:00:00Z", "cwd": cwd,
            "message": {"id": mid, "usage": {"input_tokens": 1},
                        "content": [{"type": "tool_use", "name": n, "input": i} for n, i in tools]}}


def build(root: Path) -> Path:
    """Fixture: 16 index rows, 15 inside the window. Expected buckets in EXPECT."""
    proj = root / "projects"
    ce = f"{PP}/vault/programs/cognitive-economy"
    files = {
        S1: [("m1", 1001, line("m1", PP, [("Read", {"file_path": f"{PP}/README.md"})])),
             ("m2", 1002, line("m2", PP, [("Edit", {"file_path": f"{ce}/gen2/ledger.json"})])),
             ("m3", 1003, line("m3", PP)),
             ("m4", 1004, line("m4", PP, [("PowerShell", {"command": "python tools\\cep_gen2.py --final"})])),
             ("m5", 1005, line("m5", PP, [("Read", {"file_path": f"{PP}/hooks/x.js"})]))],
        S2: [("n1", 1010, line("n1", GEN2, [("Bash", {"command": "ls"})])),
             ("n2", 1011, line("n2", GEN2, [("Bash", {"command": "ls"})]))],
        S3: [("o1", 1020, line("o1", KC, [("Edit", {"file_path": f"{KC}/src/Main.java"})]))],
        S4: [("p1", 1030, line("p1", PP))],
        S5: [("q1", 1040, line("q1", PP, [("Write", {"file_path": f"{PP}/tools/test_ce_x.py"})]))],
        S6: [("s1", 1050, line("s1", PP, [("Write", {"file_path": f"{PP}/vault/programs/cognitive-economy-e9/x.md"})])),
             ("s0", 1000, line("s0", PP, [("Write", {"file_path": f"{ce}/y.md"})]))],
        S7: [("u1", 1060, line("u1", KC, [("PowerShell", {"command": f"Get-ChildItem '{ce}' | Format-Table"})])),
             ("u2", 1061, line("u2", KC, [("Read", {"file_path": f"{ce}/CLOSE.md"})]))],
    }
    db = root / "index.sqlite"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE calls(k TEXT PRIMARY KEY, file TEXT, ts REAL, session TEXT, inp INTEGER, "
                "cw INTEGER, cr INTEGER, out INTEGER)")
    for sid, calls in files.items():
        fp = proj / "p" / f"{sid}.jsonl"
        fp.parent.mkdir(parents=True, exist_ok=True)
        with open(fp, "w", encoding="utf-8") as fh:
            for mid, ts, o in calls:
                fh.write(json.dumps(o) + "\n")
                if mid == "m2":   # the same message streamed over a second line: one call, not two
                    fh.write(json.dumps(o) + "\n")
                con.execute("INSERT INTO calls VALUES(?,?,?,?,1,10,100,1000)", (f"{mid}|r{mid}", str(fp), ts, sid))
    sub = proj / "p" / S1 / "subagents" / "agent-a.jsonl"     # subagent of S1: rolls up to S1
    sub.parent.mkdir(parents=True)
    sub.write_text(json.dumps(line("t1", PP, [("Read", {"file_path": f"{ce}/COMPLETION-PLAN.md"})])) + "\n",
                   encoding="utf-8")
    con.execute("INSERT INTO calls VALUES(?,?,?,?,1,10,100,1000)", ("t1|rt1", str(sub), 1006, S1))
    con.execute("INSERT INTO calls VALUES(?,?,?,?,1,10,100,1000)", ("gone|rg", str(proj / "p" / f"{S4}.jsonl"), 1031, S4))
    con.commit()
    con.close()
    return db


# 15 calls in (SINCE, UNTIL]; s0 sits exactly at SINCE and is outside the window. S4 holds one
# text-only call and one featureless one: not a single tool_use observed -> unknown_no_tools.
EXPECT = {"A": 3, "B": 6, "excluded_A": 1, "excluded_B": 0, "outside_span": 1, "not_program": 2,
          "unknown_no_tools": 1, "unknown_featureless": 1}


def checks(res: dict, ctl: dict, ctl_missing: dict) -> list:
    got = res["calls_by_bucket"]
    by = {r["session"][:8]: r for r in res["sessions"]}
    return [
        ("V-A1-ATTR-population", res["calls"] == 15 and res["population_ok"], f"calls={res['calls']}"),
        ("V-A1-ATTR-window-open-start", "s0" not in json.dumps(res) and got["not_program"] == 2, "ts==since excluded"),
        ("V-A1-ATTR-buckets", got == EXPECT, json.dumps(got)),
        ("V-A1-ATTR-tierA-write-span", by.get(S1[:8], {}).get("A") == 3 * N, f"S1 A={by.get(S1[:8], {}).get('A')}"),
        ("V-A1-ATTR-stream-dedup", res["population_processed"] == 15 * N, "m2 streamed twice, counted once"),
        ("V-A1-ATTR-subagent-rollup", by.get(S1[:8], {}).get("B") == 2 * N, "t1 (subagent read) widens S1's span"),
        ("V-A1-ATTR-lineage-cwd", by.get(S2[:8], {}).get("B") == 2 * N, "cwd in pp-ce-gen2, no write"),
        ("V-A1-ATTR-shell-read-is-lineage", by.get(S7[:8], {}).get("B") == 2 * N and "A" not in by.get(S7[:8], {}),
         json.dumps(by.get(S7[:8]))),
        ("V-A1-ATTR-excluded", by.get(S5[:8], {}).get("excluded_A") == N and "A" not in by.get(S5[:8], {}), ""),
        ("V-A1-ATTR-sibling-name", S6[:8] not in by, "cognitive-economy-e9 is not the program"),
        ("V-A1-ATTR-not-program", S3[:8] not in by, "KobiiCraft edit"),
        ("V-A1-ATTR-controls-pass", ctl["ok"], json.dumps(ctl)),
        ("V-A1-ATTR-control-unobserved-fails", not ctl_missing["ok"], json.dumps(ctl_missing["neg"])),
    ]


def run(db: Path, exclude=frozenset({S5[:8]}), roots=turns.PROGRAM_ROOTS) -> list:
    con = sqlite3.connect(db)
    try:
        res = turns.attribute(SINCE, UNTIL, turns.PROGRAM_PATHS, roots, exclude, con=con)
    finally:
        con.close()
    ctl = turns.attribution_controls(res, pos=(S1[:8], S2[:8], S5[:8]), neg=(S3[:8],))
    ctl_missing = turns.attribution_controls(res, pos=(S1[:8],), neg=("deadbeef",))
    return checks(res, ctl, ctl_missing)


def shell_cases() -> None:
    """SHELL_WRITE from both poles on the command shapes the estate actually issues."""
    w = ["Set-Content -Path x -Value 1", "[System.IO.File]::WriteAllText($p, $b)", "echo x > out.json",
         "python3 tools/x.py", "& 'C:\\P\\python.exe' x.py", "cp a b", "sed -i s/a/b/ f"]
    r = ["Get-ChildItem $d -File", "cat ledger.json", "Select-String -Path f -Pattern x", "ls 2>&1",
         "Get-Content f | Select-Object -First 3", "grep -n x f"]
    bad = [c for c in w if not turns.SHELL_WRITE.search(c)] + [c for c in r if turns.SHELL_WRITE.search(c)]
    (_ok if not bad else _fail)("V-A1-ATTR-shell-write-poles", f"{len(w)} write / {len(r)} read" if not bad else str(bad))


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db = build(root)
        for tag, ok, ev in run(db):
            (_ok if ok else _fail)(tag, ev)
        shell_cases()

        led = root / "ledger.json"
        led.write_text(json.dumps({"budget_tokens": {"spent_measured": {"sources": [
            {"what": "pane 87601e81 after anchor", "processed": 12819555}]}}}), encoding="utf-8")
        got = turns.ledger_session_prefixes(led)   # 12819555 is 8 hex digits: an int, never a session
        (_ok if got == {"87601e81"} else _fail)("V-A1-ATTR-ledger-prefixes", str(got))

        def mutant(tag, **kw):
            red = [t for t, ok, _ in run(db, **kw) if not ok]
            (_ok if red else _fail)(tag, f"killed by {red}" if red else "SURVIVED")

        # MUT-lineage-off: no read signal, no program roots -> S2, S7 and the subagent read vanish.
        real = turns.program_probe
        turns.program_probe = lambda rx: (lambda n, i, c: None if n in turns.READ_TOOLS else real(rx)(n, i, c))
        try:
            mutant("V-A1-ATTR-MUT-lineage-off", roots=())
        finally:
            turns.program_probe = real
        # MUT-exclusion-off: the ledger-metered session S5 is summed into tier A.
        mutant("V-A1-ATTR-MUT-exclusion-off", exclude=frozenset())
        # MUT-shell-any-write: a read-only listing of the program dir becomes a write.
        real_rx = turns.SHELL_WRITE
        turns.SHELL_WRITE = re.compile(r"")
        try:
            mutant("V-A1-ATTR-MUT-shell-any-write")
        finally:
            turns.SHELL_WRITE = real_rx
    print(f"CE_A1_ATTR_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
