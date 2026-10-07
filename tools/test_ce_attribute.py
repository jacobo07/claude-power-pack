#!/usr/bin/env python
"""A2-1 gate: per-call program attribution (turns.py --attribute -> measure/attribute.py) and the metered-receipt rule.
Hermetic: synthetic transcripts in a temp dir, no usage index, no live state. Both poles for every guard.

    python tools/test_ce_attribute.py        -> CE_ATTRIBUTE_PASS=n/n
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MEASURE = REPO / "vault" / "programs" / "cognitive-economy" / "measure"
sys.path.insert(0, str(MEASURE))
sys.path.insert(0, str(REPO / "tools"))
import attribute as at  # noqa: E402
import cep_gen2 as cep  # noqa: E402

ROOT = "C:\\prog\\wt"
OUT = "C:\\elsewhere"
res: list = []


def gate(name: str, ok: bool, why: str = "") -> None:
    res.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'} {name}{(': ' + why) if why and not ok else ''}")


def call(i: int, sid: str, toks: int, cwd: str = OUT, tool=None, inp=None, dup_of=None) -> dict:
    content = [{"type": "tool_use", "name": tool, "input": inp}] if tool else [{"type": "text", "text": "x"}]
    return {"type": "assistant", "sessionId": sid, "cwd": cwd, "timestamp": f"2026-10-07T10:00:{i:02d}Z",
            "requestId": f"{sid}-req{dup_of if dup_of is not None else i}",
            "message": {"id": f"{sid}-msg{dup_of if dup_of is not None else i}", "content": content,
                        "usage": {"input_tokens": toks, "cache_creation_input_tokens": 0,
                                  "cache_read_input_tokens": 0, "output_tokens": 0}}}


def write(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def main() -> int:
    wr = {"file_path": ROOT + "\\a.py"}
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        # S1: before(100) | write(200) | mid(300) | write(400) | after(500)  -> span = 200+300+400
        write(t / "S1.jsonl", [call(0, "S1", 100), call(1, "S1", 200, tool="Write", inp=wr), call(2, "S1", 300),
                               call(3, "S1", 400, tool="Edit", inp=wr), call(4, "S1", 500)])
        r = at.attribute([t / "S1.jsonl"], [ROOT])
        gate("V-ATTR-WRITE-SPAN-EXACT", r["program_processed"] == 900 and r["by_basis"]["write_span"] == 900,
             json.dumps(r["by_basis"]))
        gate("V-ATTR-OUTSIDE-SPAN-TEXT-IS-UNKNOWN", any("2 text-only" in u for u in r["unknown"]), str(r["unknown"]))

        # negative control: a session that never touches the program contributes nothing
        write(t / "N.jsonl", [call(0, "N", 7000, tool="Read", inp={"file_path": OUT + "\\z.py"})])
        gate("V-ATTR-NEGATIVE-CONTROL-ZERO", at.attribute([t / "N.jsonl"], [ROOT])["program_processed"] == 0)

        # coordinator pane: never writes, only reads a card / runs inside the worktree (G4)
        write(t / "C.jsonl", [call(0, "C", 50, tool="Read", inp={"file_path": ROOT + "\\card.md"}),
                              call(1, "C", 60, cwd=ROOT, tool="Agent", inp={}), call(2, "C", 70)])
        r = at.attribute([t / "C.jsonl"], [ROOT], cards=[ROOT + "\\card.md"])
        gate("V-ATTR-COORDINATOR-COUNTED", r["by_basis"]["lineage_card"] == 50 and r["by_basis"]["lineage_cwd"] == 60
             and r["program_processed"] == 110, json.dumps(r["by_basis"]))
        r2 = at.attribute([t / "C.jsonl"], [ROOT])
        gate("V-ATTR-CARD-NEEDS-DECLARATION", r2["by_basis"]["lineage_card"] == 0, "undeclared card was counted")

        # G5 double count: the same message id in two transcripts counts once; the dedup branch is driven both ways
        write(t / "D1.jsonl", [call(0, "D", 111, tool="Write", inp=wr)])
        write(t / "D2.jsonl", [call(9, "D", 111, tool="Write", inp=wr, dup_of=0)])
        a = at.attribute([t / "D1.jsonl", t / "D2.jsonl"], [ROOT])
        b = at.attribute([t / "D1.jsonl", t / "D2.jsonl"], [ROOT], dedup=False)
        gate("V-ATTR-DEDUP-MESSAGE-ID", a["program_processed"] == 111 and a["duplicates_dropped"] == 1, str(a["program_processed"]))
        gate("V-ATTR-DEDUP-OFF-DOUBLE-COUNTS", b["program_processed"] == 222, "control: without dedup it must double")

        # G5 exclusion: a session already in a ledger source is skipped and listed
        e = at.attribute([t / "S1.jsonl", t / "D1.jsonl"], [ROOT], exclude_sids=["S1"])
        gate("V-ATTR-EXCLUDE-SID", e["program_processed"] == 111 and e["excluded_sessions"] == ["S1"], str(e["excluded_sessions"]))

        # subagent transcripts roll up into the parent session
        write(t / "P" / "sub" / "P.jsonl", [call(0, "P", 5, tool="Write", inp=wr)])
        write(t / "P" / "subagents" / "agent-1.jsonl", [call(1, "ignored", 8, tool="Write", inp=wr)])
        r = at.attribute([t / "P" / "sub" / "P.jsonl", t / "P" / "subagents" / "agent-1.jsonl"], [ROOT])
        gate("V-ATTR-SUBAGENT-ROLLS-UP", r["program_processed"] == 13 and "P" in r["sessions"], str(list(r["sessions"])))

        # a call with no usage is never counted as zero spend
        row = call(0, "U", 0, tool="Write", inp=wr)
        row["message"].pop("usage")
        write(t / "U.jsonl", [row])
        r = at.attribute([t / "U.jsonl"], [ROOT])
        gate("V-ATTR-NO-USAGE-IS-UNKNOWN", r["program_processed"] == 0 and any("no usage" in u for u in r["unknown"]), str(r["unknown"]))

        # the CLI through turns.py really delegates and prints the same total
        p = subprocess.run([sys.executable, "-I", str(MEASURE / "turns.py"), "--attribute", "--root", ROOT,
                            "--projects-dir", str(t)], capture_output=True, text=True, encoding="utf-8")
        ok = p.returncode == 0
        try:
            total = json.loads(p.stdout)["program_processed"]
        except (ValueError, KeyError):
            total = None
        want = at.attribute([str(x) for x in t.rglob("*.jsonl")], [ROOT])["program_processed"]
        gate("V-ATTR-CLI-VIA-TURNS", ok and want == 1084 and total == want,
             f"rc={p.returncode} total={total} want={want} err={p.stderr[-200:]}")

    # receipt: a self-reported boundary count below the metered one fails (EDD WU-1: 3 vs 16)
    def receipt(**kw):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ev.md").write_text("e\n", encoding="utf-8")
            cep._write_receipt(root, lambda r: cep._as_measurement(r, **kw))
            return cep.check_receipt("C", "receipt.json", root)

    gate("V-ATTR-RECEIPT-3-VS-16-FAILS", any("metered wins" in x for x in receipt(boundary_calls=3, metered_calls=16)))
    gate("V-ATTR-RECEIPT-EQUAL-PASSES", receipt(boundary_calls=16, metered_calls=16) == [])
    gate("V-ATTR-RECEIPT-NO-METER-FAILS", any("no metered_calls" in x for x in receipt(boundary_calls=16)))
    gate("V-ATTR-RECEIPT-ABSENT-FIELDS-UNCHANGED", receipt() == [])
    print(f"CE_ATTRIBUTE_PASS={sum(res)}/{len(res)}")
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
