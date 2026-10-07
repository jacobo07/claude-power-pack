#!/usr/bin/env python
"""Meter truth gate (Owner order 2026-10-07, "hacer infalible el medidor"): the program meter must be impossible to get
silently wrong. Two independent counters (measure/attribute.py, stage0/self_spend.py) are driven over synthetic
transcripts for every failure seen on 2026-10-07 (F1 wrong dir, F2 text-only calls dropped, F3 receipt below meter), plus
duplicate ids, torn lines, missing transcripts, several dirs, another host, and the two golden sessions.

    python tools/test_ce_meter_truth.py        -> CE_METER_PASS=n/m
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MEASURE = REPO / "vault" / "programs" / "cognitive-economy" / "measure"
SELF_SPEND = REPO / "vault" / "programs" / "cognitive-economy" / "gen2" / "evidence" / "stage0" / "self_spend.py"
sys.path.insert(0, str(MEASURE))
sys.path.insert(0, str(REPO / "tools"))
import attribute as at  # noqa: E402
import cep_gen2 as cep  # noqa: E402

ROOT = "C:\\prog\\wt"
res: list = []


def gate(name: str, ok: bool, why: str = "") -> None:
    res.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'} {name}{(': ' + why) if why and not ok else ''}")


def rec(i: int, sid: str, toks: int, out: int = 0, mid=None, req=None, hour: int = 10, tool=None, inp=None, cwd="C:\\elsewhere") -> dict:
    content = [{"type": "tool_use", "name": tool, "input": inp}] if tool else [{"type": "text", "text": "x"}]
    m = {"content": content, "usage": {"input_tokens": toks, "cache_creation_input_tokens": 0,
                                        "cache_read_input_tokens": 0, "output_tokens": out}}
    if mid is not False:
        m["id"] = mid if mid is not None else f"{sid}-m{i}"
    o = {"type": "assistant", "sessionId": sid, "cwd": cwd, "timestamp": f"2026-10-07T{hour:02d}:00:{i:02d}Z", "message": m}
    if req is not False:
        o["requestId"] = req if req is not None else f"{sid}-r{i}"
    return o


def put(path: Path, rows: list, raw_tail: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows) + raw_tail, encoding="utf-8")


def spend_cli(sid: str, d, *extra) -> tuple:
    p = subprocess.run([sys.executable, "-I", str(SELF_SPEND), "--session", sid, "--dir", str(d), *extra],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


def num(out: str, word: str):
    import re
    m = re.search(rf"{word} ([\d,]+)", out)
    return int(m.group(1).replace(",", "")) if m else None


def meter_cli(d, *args) -> tuple:
    p = subprocess.run([sys.executable, "-I", str(MEASURE / "attribute.py"), "--projects-dir", str(d), *args],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout


def main() -> int:
    wr = {"file_path": ROOT + "\\a.py"}
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)

        # F1: a session filed under a project dir nobody named is still found, subagents included, by BOTH counters
        sid = "aaaa1111"
        put(t / "dirA" / "other.jsonl", [rec(0, "other", 9)])
        put(t / "dirB" / f"{sid}.jsonl", [rec(0, sid, 100, 10), rec(1, sid, 200, 20)])
        put(t / "dirB" / sid / "subagents" / "agent-1.jsonl", [rec(2, sid, 300, 30, mid="sub-m")])
        want_calls, want_proc = 3, 100 + 10 + 200 + 20 + 300 + 30
        gate("V-METER-F1-FIND-ANY-DIR", len(at.find_session_files(sid, t)) == 2, str(at.find_session_files(sid, t)))
        gate("V-METER-F1-SINGLE-DIR-CANNOT-SEE", at.find_session_files(sid, t / "dirA") == [], "control: dirA must not hold it")
        v = at.meter_session(sid, t)
        gate("V-METER-F1-AGREE-ANY-DIR", v["verdict"] == "AGREE" and v.get("calls") == want_calls and v.get("processed") == want_proc, json.dumps(v))
        rc, out = spend_cli(sid, t)
        gate("V-METER-F1-SELFSPEND-ANY-DIR", rc == 0 and num(out, "processed") == want_proc and num(out, "calls") == want_calls, out)

        # missing transcript: UNKNOWN, non-zero, never a zero (both counters, and the CLI)
        v = at.meter_session("nosuch", t)
        gate("V-METER-MISSING-IS-UNKNOWN", v["verdict"] == "UNKNOWN" and "processed" not in v and "calls" not in v, json.dumps(v))
        rc, out = spend_cli("nosuch", t)
        gate("V-METER-MISSING-SELFSPEND-UNKNOWN", rc != 0 and "UNKNOWN" in out and num(out, "processed") is None, f"rc={rc} {out}")
        rc, _ = meter_cli(t, "--session", "nosuch")
        gate("V-METER-MISSING-CLI-NONZERO", rc == 2, f"rc={rc}")

        # M5: another host's session is UNKNOWN naming the host; a local transcript wins over the declaration
        v = at.meter_session("gex-only", t, host="GEX44")
        gate("V-METER-OTHER-HOST-UNKNOWN-NAMED", v["verdict"] == "UNKNOWN" and "GEX44" in v["why"] and v["host"] == "GEX44", json.dumps(v))
        v = at.meter_session(sid, t, host="GEX44")
        gate("V-METER-LOCAL-TRANSCRIPT-BEATS-HOST-CLAIM", v["verdict"] == "AGREE" and v["processed"] == want_proc, json.dumps(v))

        # F2: text-only calls outside every basis are in the session total, in their own row, never in program_processed
        s2 = "bbbb2222"
        rows = [rec(i, s2, 1000) for i in range(5)] + [rec(5, s2, 7, tool="Write", inp=wr)] + [rec(i, s2, 1000) for i in range(6, 12)]
        put(t / "dirC" / f"{s2}.jsonl", rows)
        r = at.attribute([t / "dirC" / f"{s2}.jsonl"], [ROOT])
        tot = r["session_totals"][s2]
        gate("V-METER-F2-TOTAL-INCLUDES-UNATTRIBUTED", tot["calls"] == 12 and tot["processed"] == 11 * 1000 + 7, json.dumps(tot))
        gate("V-METER-F2-UNATTRIBUTED-OWN-ROW", tot["unattributed_calls"] == 11 and tot["unattributed_processed"] == 11000
             and r["program_processed"] == 7, json.dumps(tot))
        r0 = at.attribute([t / "dirC" / f"{s2}.jsonl"], [])
        gate("V-METER-ATTRIBUTION-NEVER-REDUCES-TOTAL", r0["total_processed"] == r["total_processed"] == 11007, f"{r0['total_processed']} vs {r['total_processed']}")
        v = at.meter_session(s2, t)
        gate("V-METER-F2-SESSION-VERDICT-FULL-TOTAL", v["verdict"] == "AGREE" and v["processed"] == 11007 and v["calls"] == 12, json.dumps(v))

        # duplicates: same id twice, id absent + same requestId, neither id nor requestId (each is its own call)
        s3 = "cccc3333"
        put(t / "dirD" / f"{s3}.jsonl", [rec(0, s3, 10, mid="dup"), rec(1, s3, 10, mid="dup"), rec(2, s3, 20, mid=False, req="rq"),
                                          rec(3, s3, 20, mid=False, req="rq"), rec(4, s3, 5, mid=False, req=False), rec(5, s3, 5, mid=False, req=False)])
        v = at.meter_session(s3, t)
        gate("V-METER-DUP-IDS-COUNT-ONCE", v["verdict"] == "AGREE" and v["calls"] == 4 and v["processed"] == 10 + 20 + 5 + 5, json.dumps(v))

        # several dirs hold the same session: union, deduplicated
        s4 = "dddd4444"
        put(t / "dirE" / f"{s4}.jsonl", [rec(0, s4, 11), rec(1, s4, 22)])
        put(t / "dirF" / f"{s4}.jsonl", [rec(1, s4, 22), rec(2, s4, 33)])
        v = at.meter_session(s4, t)
        gate("V-METER-MULTIDIR-UNION-DEDUP", v["verdict"] == "AGREE" and v["calls"] == 3 and v["processed"] == 66 and v["files"] == 2, json.dumps(v))

        # M4: torn lines are counted by both counters and the verdict is never a clean AGREE
        s5 = "eeee5555"
        put(t / "dirG" / f"{s5}.jsonl", [rec(0, s5, 40), rec(1, s5, 60)], raw_tail='{"type": "assistant", "message": {"id": "cut\nnot json at all\n')
        v = at.meter_session(s5, t)
        gate("V-METER-TORN-LINES-REPORTED", v["verdict"] == "INCOMPLETE" and v["lower_bound"]["torn_lines"] == 2
             and v["lower_bound"]["processed"] == 100, json.dumps(v))
        rc, out = spend_cli(s5, t)
        gate("V-METER-TORN-SELFSPEND-COUNTS", num(out, "torn") == 2 and num(out, "processed") == 100, out)
        rc, _ = meter_cli(t, "--session", s5)
        gate("V-METER-TORN-CLI-EXIT-3", rc == 3, f"rc={rc}")
        r = at.attribute([t / "dirG" / f"{s5}.jsonl"], [])
        gate("V-METER-TORN-NAMED-UNKNOWN", r["torn_lines"] == 2 and any("torn" in u for u in r["unknown"]), str(r["unknown"]))

        # M3: counters that differ never produce a number; a control with the real second counter still agrees
        v = at.meter_session(sid, t, second=lambda s, d, u: {"calls": want_calls, "processed": want_proc + 1, "torn_lines": 0})
        gate("V-METER-DISAGREE-NO-NUMBER", v["verdict"] == "DISAGREE" and "processed" not in v and "calls" not in v, json.dumps(v))
        v = at.meter_session(sid, t, second=lambda s, d, u: None)
        gate("V-METER-NO-SECOND-READING-UNKNOWN", v["verdict"] == "UNKNOWN" and "processed" not in v, json.dumps(v))
        rc, _ = meter_cli(t, "--session", sid)
        gate("V-METER-CONTROL-CLI-AGREE-EXIT-0", rc == 0, f"rc={rc}")
        gate("V-METER-COUNTERS-INDEPENDENT", "import attribute" not in SELF_SPEND.read_text(encoding="utf-8")
             and "self_spend" not in (MEASURE / "attribute.py").read_text(encoding="utf-8").split("SELF_SPEND =")[0].split('"""', 2)[2]
             and "import self_spend" not in (MEASURE / "attribute.py").read_text(encoding="utf-8"))

        # time cut-off pins a golden value: calls after --until are outside both counters
        s6 = "ffff6666"
        put(t / "dirH" / f"{s6}.jsonl", [rec(0, s6, 100, hour=10), rec(1, s6, 200, hour=17), rec(2, s6, 400, hour=19)])
        v = at.meter_session(s6, t, until="2026-10-07T18:00:00Z")
        gate("V-METER-UNTIL-CUTOFF-BOTH-COUNTERS", v["verdict"] == "AGREE" and v["processed"] == 300 and v["calls"] == 2, json.dumps(v))
        v = at.meter_session(s6, t)
        gate("V-METER-NO-CUTOFF-COUNTS-ALL", v.get("processed") == 700, json.dumps(v))

        # F3: a receipt self-reporting below what the meter counted fails; at the metered count it passes
        s7 = "gggg7777"
        put(t / "dirI" / f"{s7}.jsonl", [rec(i, s7, 10) for i in range(16)])
        metered = at.meter_session(s7, t).get("calls", -1)

        def receipt(**kw):
            with tempfile.TemporaryDirectory() as rt:
                root = Path(rt)
                (root / "ev.md").write_text("e\n", encoding="utf-8")
                cep._write_receipt(root, lambda r: cep._as_measurement(r, **kw))
                return cep.check_receipt("C", "receipt.json", root)

        gate("V-METER-F3-RECEIPT-3-VS-METER-16-FAILS", metered == 16 and any("metered wins" in x for x in receipt(boundary_calls=3, metered_calls=metered)))
        gate("V-METER-F3-RECEIPT-AT-METER-PASSES", receipt(boundary_calls=metered, metered_calls=metered) == [])
        gate("V-METER-F3-RECEIPT-WITHOUT-METER-FAILS", any("no metered_calls" in x for x in receipt(boundary_calls=3)))

    # M7 golden values on the real transcripts, pinned with a cut-off so later calls cannot move them
    proj = Path.home() / ".claude" / "projects"
    cut = "2026-10-07T18:00:00Z"

    def golden(prefix: str):
        sids = sorted({p.stem for p in proj.glob(f"*/{prefix}*.jsonl")})
        return at.meter_session(sids[0], proj, until=cut) if len(sids) == 1 else {"verdict": "UNKNOWN", "why": f"{len(sids)} transcripts match {prefix}"}

    g = golden("489481fa")
    gate("V-METER-GOLDEN-489481FA", g["verdict"] in ("AGREE", "INCOMPLETE") and (g.get("processed") or g.get("lower_bound", {}).get("processed")) == 10_695_300
         and (g.get("calls") or g.get("lower_bound", {}).get("calls")) == 61, json.dumps(g)[:300])
    g = golden("886d7bb9")
    gate("V-METER-GOLDEN-886D7BB9", g["verdict"] in ("AGREE", "INCOMPLETE") and (g.get("processed") or g.get("lower_bound", {}).get("processed") or 0) >= 16_916_777
         and (g.get("calls") or g.get("lower_bound", {}).get("calls") or 0) >= 71, json.dumps(g)[:300])

    print(f"CE_METER_PASS={sum(res)}/{len(res)}")
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
