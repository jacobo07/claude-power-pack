# <module>/tests/e2e_continuity.py - simulates 3 slots, crash, restore; asserts invariants.
import json, os, subprocess, sys, tempfile, pathlib, datetime

MOD = pathlib.Path(__file__).resolve().parents[1]
NODE = r"C:/Program Files/nodejs/node.exe"

def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="lze2e-"))
    reg_root = tmp / "lazarus"; reg_root.mkdir()
    proj = tmp / "proj"; proj.mkdir()
    for i, sid in enumerate(["AAA", "BBB", "CCC"], 1):
        (proj / f"{sid}.jsonl").write_text(
            json.dumps({"type": "summary", "summary": f"chat {sid}"}) + "\n", encoding="utf8")
        subprocess.run([NODE, str(MOD / "recorder.js")],
            input=json.dumps({"session_id": sid, "cwd": str(proj)}),
            env={**os.environ, "LAZARUS_REG_ROOT": str(reg_root), "LAZARUS_TERMINAL_KEY": f"slot{i}"},
            text=True, check=True)
    rows = json.loads((reg_root / "terminal_registry.json").read_text())["rows"]
    assert len(rows) == 3, f"expected 3 slots, got {len(rows)}"
    by_slot = {r["slot"]: r["session_id"] for r in rows}
    assert by_slot == {"slot1": "AAA", "slot2": "BBB", "slot3": "CCC"}, by_slot

    for i, sid in enumerate(["AAA", "BBB", "CCC"], 1):
        out = subprocess.check_output(["powershell", "-ExecutionPolicy", "Bypass", "-File",
            str(MOD / "restore.ps1"), "-RegRoot", str(reg_root), "-Slot", f"slot{i}", "-DryRun"],
            text=True)
        assert f"claude --resume {sid}" in out, f"slot{i} restore wrong: {out}"

    before = sorted(p.name for p in proj.glob("*"))
    subprocess.run([NODE, "-e",
        f"require(String.raw`{MOD/'mark.js'}`).mark(String.raw`{proj}`,['AAA','BBB','CCC'],new Date())"],
        check=True)
    after = sorted(p.name for p in proj.glob("*"))
    assert before == after, f"files changed names! {before} -> {after}"
    assert not list(proj.glob("*.jsonl.live")), "shadow file created - INVARIANT VIOLATION"
    # encoding="utf8" is required: the marker is a non-Latin-1 emoji and
    # Python's default read_text() uses cp1252 on Windows, mis-decoding the
    # bytes so the (correct) yellow-mark assertion would falsely fail.
    s = json.loads((proj / "AAA.jsonl").read_text(encoding="utf8").splitlines()[0])
    assert s["summary"].startswith("🟡 [PRE-REBOOT"), s["summary"]

    print("e2e_continuity OK")
    v = {"ts": datetime.datetime.utcnow().isoformat()+"Z", "audit": "lazarus-v4-e2e",
         "grade": "A", "invariants": ["3 slots exact", "restore exact sid", "0 jsonl renamed", "yellow mark"]}
    with (MOD / "tests" / "verdicts.jsonl").open("a", encoding="utf8") as fh:
        fh.write(json.dumps(v) + "\n")

if __name__ == "__main__":
    sys.exit(main())
