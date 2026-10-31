"""V-CTXR-* gates for tools/ctx_rent.py. Fixtures use the real transcript line shapes (assistant lines carry one content
block each and share a message.id with usage; tool results arrive as user lines; attachments are their own lines)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctx_rent as cx  # noqa: E402

PASS = FAIL = 0


def check(gate: str, cond: bool, ev: str) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {gate}: {ev}")
    else:
        FAIL += 1
        print(f"FAIL {gate}: {ev}")


def usage(total: int, out: int = 10) -> dict:
    return {"input_tokens": 3, "cache_read_input_tokens": total - 3, "cache_creation_input_tokens": 0, "output_tokens": out}


def a_line(mid: str, ts: str, total: int, block: dict) -> str:
    return json.dumps({"type": "assistant", "timestamp": ts, "message": {"id": mid, "usage": usage(total), "content": [block]}})


def u_result(tid: str, text: str) -> str:
    return json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": text}]}})


def tool_use(tid: str, path: str) -> dict:
    return {"type": "tool_use", "id": tid, "name": "Read", "input": {"file_path": path}}


BIG1 = "x" * 3975 + " /repo/src/beta_helper.py"        # 4000 chars = 1000 tokens, names beta_helper
BIG2 = "y" * 1974 + " /repo/src/gamma_unused.py"       # 2000 chars = 500 tokens, nothing ever uses it
TS = "2026-10-28T10:00:0%dZ"


def session(late_ref: bool = False, compact: bool = False, dup_line: bool = False) -> str:
    L = [
        a_line("m0", TS % 0, 1000, tool_use("t1", "/repo/src/alpha_module.py")),
        u_result("t1", BIG1),
        a_line("m1", TS % 1, 2100 if not compact else 52100, tool_use("t1b", "/repo/src/beta_helper.py")),       # uses t1 (names beta_helper)
        u_result("t1b", "short"),
        a_line("m2", TS % 2, 2200 if not compact else 52200, tool_use("t2", "/repo/src/gamma_file.py")),
        u_result("t2", BIG2),
        a_line("m3", TS % 3, 2800 if not compact else 9000, {"type": "thinking", "thinking": "t" * 400}),
        a_line("m4", TS % 4, 2900, {"type": "text", "text": "I reread /repo/src/gamma_unused.py" if late_ref else "done"}),
    ]
    if dup_line:
        L.insert(2, a_line("m0", TS % 0, 1000, {"type": "text", "text": "same id, second block"}))
    return "\n".join(L) + "\n"


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        f = base / "s.jsonl"
        f.write_text(session(), encoding="utf-8")

        # --- carriage: floor is measured, the rest is the labelled estimate
        c = cx.carriage(f)
        check("V-CTXR-CALLS", c["calls"] == 5 and c["floor_measured"] == 1000, f"5 calls, floor {c['floor_measured']}")
        check("V-CTXR-CARRIAGE-CLASS", c["mean_est_by_class_APPROX"]["tool_result"] > 0 and c["mean_est_by_class_APPROX"]["thinking"] > 0,
              f"tool_result and thinking attributed: {c['mean_est_by_class_APPROX']}")
        check("V-CTXR-CALIBRATION-PRESENT", c["calibration_est_over_actual"] is not None and "mean_est_total_APPROX" in c,
              "estimate carries its own calibration against the measured input")

        # --- dead rent: exact on a hand-computed fixture. t1 1000 tok enters call1, last used by call1's output -> dead on calls 2,3,4
        d = cx.dead_rent(f)
        t1_carried, t1_dead = 1000 * 4, 1000 * 3
        t2_carried, t2_dead = 500 * 2, 500 * 2           # t2 enters call3, never referenced
        t1b = 1.25 * 3                                    # 'short' = 5 chars, enters call2, never referenced
        check("V-CTXR-DEAD-EXACT", abs(d["result_rent_tokens_APPROX"] - (t1_carried + t2_carried + t1b)) <= 2
              and abs(d["dead_rent_tokens_UPPER_BOUND"] - (t1_dead + t2_dead + t1b)) <= 2, f"hand-computed carried {t1_carried + t2_carried + t1b}, dead {t1_dead + t2_dead + t1b}; got {d}")
        check("V-CTXR-DEAD-NEVER", abs(d["never_referenced_rent_tokens"] - (t2_dead + t1b)) <= 2, f"never-referenced rent {d['never_referenced_rent_tokens']}")

        # --- positive control: the detector can return the other answer
        f2 = base / "late.jsonl"
        f2.write_text(session(late_ref=True), encoding="utf-8")
        d2 = cx.dead_rent(f2)
        check("V-CTXR-DEAD-CONTROL", d2["dead_rent_tokens_UPPER_BOUND"] < d["dead_rent_tokens_UPPER_BOUND"],
              f"a late reference to t2 lowers dead rent {d['dead_rent_tokens_UPPER_BOUND']} -> {d2['dead_rent_tokens_UPPER_BOUND']}")

        # --- compaction boundary ends the carriage
        f3 = base / "comp.jsonl"
        f3.write_text(session(compact=True), encoding="utf-8")
        d3 = cx.dead_rent(f3)
        check("V-CTXR-COMPACTION", d3["result_rent_tokens_APPROX"] < d["result_rent_tokens_APPROX"],
              f"input 52200 -> 9000 is a boundary: carried {d['result_rent_tokens_APPROX']} -> {d3['result_rent_tokens_APPROX']}")
        check("V-CTXR-COMPACTION-DETECTED", d3["compaction_boundaries"] == 1, f"boundaries {d3['compaction_boundaries']}")

        # --- mutation drills: break each mechanism, the gate above must go red
        orig_re, orig_drop = cx.TOKEN_RE, cx.COMPACT_DROP
        try:
            cx.TOKEN_RE = __import__("re").compile(r"(?!x)x")        # reference detection off
            dm = cx.dead_rent(f)
            check("V-CTXR-DRILL-REFERENCE", dm["dead_rent_tokens_UPPER_BOUND"] > d["dead_rent_tokens_UPPER_BOUND"] and
                  dm["dead_share_of_result_rent"] == 1.0, "no reference detection => everything dead (the gate sees it)")
            cx.COMPACT_DROP = 5.0                                    # compaction detection off
            dm2 = cx.dead_rent(f3)
            check("V-CTXR-DRILL-COMPACTION", dm2["compaction_boundaries"] == 0 and dm2["result_rent_tokens_APPROX"] > d3["result_rent_tokens_APPROX"],
                  "no compaction detection => carriage runs past the boundary (the gate sees it)")
        finally:
            cx.TOKEN_RE, cx.COMPACT_DROP = orig_re, orig_drop

        # --- call dedup: a second line with the same message.id is not a second call
        f4 = base / "dup.jsonl"
        f4.write_text(session(dup_line=True), encoding="utf-8")
        check("V-CTXR-DEDUP", cx.carriage(f4)["calls"] == 5, "same message.id counted once")

        # --- estate: class, window, generation join (CURRENT / STALE / UNKNOWN is never 'current')
        proj = base / "projects" / "-repo"
        (proj / "SID-A" / "subagents").mkdir(parents=True)
        for sid in ("SID-A", "SID-B", "SID-C", "SID-W"):
            (proj / f"{sid}.jsonl").write_text(session(), encoding="utf-8")
        (proj / "SID-A" / "subagents" / "agent-1.jsonl").write_text(session(), encoding="utf-8")
        rec = base / "receipts"
        for sid, rel in (("SID-A", "rel-X"), ("SID-B", "rel-Y")):
            (rec / "1").mkdir(parents=True, exist_ok=True)
            (rec / "1" / f"{sid}.jsonl").write_text(json.dumps({"ev": "start", "ts": 1, "releaseId": rel}) + "\n", encoding="utf-8")
        doc = cx.estate(base / "projects", "2026-10-28T00:00:00Z", "2026-10-29T00:00:00Z", [rec], "rel-X", {"SID-W": "background"}, "TESTPLANE")
        gens = doc["classes"]["top-level"]
        check("V-CTXR-GEN-CURRENT", "CURRENT:rel-X" in gens and gens["CURRENT:rel-X"]["sessions"] == 1, f"gens {sorted(gens)}")
        check("V-CTXR-GEN-STALE", "STALE:rel-Y" in gens, "a session on another release is STALE")
        check("V-CTXR-GEN-UNKNOWN", "UNKNOWN" in gens and gens["UNKNOWN"]["sessions"] == 1, "no receipt => UNKNOWN, not current")
        check("V-CTXR-CLASSES", "subagent" in doc["classes"] and "worker:background" in doc["classes"], f"classes {sorted(doc['classes'])}")
        check("V-CTXR-PLANE-LABEL", doc["plane"] == "TESTPLANE", "every estate carries its plane")
        doc_out = cx.estate(base / "projects", "2026-11-05T00:00:00Z", "2026-11-06T00:00:00Z", [rec], "rel-X", {}, "TESTPLANE")
        check("V-CTXR-WINDOW", doc_out["total"]["calls"] == 0 and doc["total"]["calls"] == 25, f"in-window 25 calls, out-of-window {doc_out['total']['calls']}")
        check("V-CTXR-FLOOR-RENT", gens["CURRENT:rel-X"]["floor_rent"] == 5 * 1000 and gens["CURRENT:rel-X"]["mean_floor"] == 1000, "floor rent = calls x call-1 floor")

        # --- diff refuses a cross-plane delta, and keeps one-sided cells
        other = dict(doc, plane="LAPTOP")
        try:
            cx.diff(doc, other)
            refused = False
        except SystemExit:
            refused = True
        check("V-CTXR-DIFF-CROSS-PLANE", refused, "a delta between two planes is refused")
        rows = cx.diff(doc, doc_out)
        check("V-CTXR-DIFF-ONE-SIDED", any(r["to"] is None and r["from"] for r in rows), "cells that vanished are kept, not dropped")

    print(f"CTXR_PASS={PASS}/{PASS + FAIL}  threshold={PASS + FAIL}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
