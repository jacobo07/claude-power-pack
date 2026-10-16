"""V-STR-*: mission_spend.session_tree_report -- the cost tree of a session, deduped by message id.
Measured 2026-10-16: summing `usage` per transcript LINE read 65.4M for a 29.9M tree, because Claude repeats a
message's usage on every content-block line. The report must equal session_tree_tokens, never the line sum."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mission_spend as ms  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes, fails = passes + bool(cond), fails + (not cond)
    print(("PASS " if cond else "FAIL ") + gate + ("" if cond else f" :: {ev}"))


def line(mid, inp, cache, out):
    return json.dumps({"type": "assistant", "message": {"id": mid, "model": "claude-sonnet-5-5", "usage": {
        "input_tokens": inp, "cache_read_input_tokens": cache, "cache_creation_input_tokens": 0, "output_tokens": out}}})


def main():
    # Arrange: main session with one message written as TWO block lines (same id, same usage) + one subagent.
    d = Path(tempfile.mkdtemp())
    main_t = d / "sid.jsonl"
    main_t.write_text("\n".join([line("m1", 10, 1000, 5), line("m1", 10, 1000, 5), line("m2", 20, 2000, 7)]) + "\n")
    sub = d / "sid" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-a1.jsonl").write_text("\n".join([line("s1", 1, 500, 3), line("s1", 1, 500, 3)]) + "\n")
    (sub / "agent-a1.meta.json").write_text(json.dumps({"agentType": "gsd-planner", "description": "Plan phase 5"}))

    # Act
    rep = ms.session_tree_report(main_t)
    tot = ms.session_tree_tokens(main_t)
    raw = sum(sum(json.loads(x)["message"]["usage"].values()) for f in (main_t, sub / "agent-a1.jsonl")
              for x in f.read_text().splitlines())

    # Assert
    check("V-STR-DEDUP-TOTAL", rep["tokens"] == 1015 + 2027 + 504 == tot["tokens"], f"{rep['tokens']} vs {tot}")
    check("V-STR-CONTROL-LINE-SUM-IS-WRONG", raw == 2 * 1015 + 2027 + 2 * 504 and raw != rep["tokens"], str(raw))
    nodes = {n["file"]: n for n in rep["nodes"]}
    sa = nodes.get("agent-a1.jsonl", {})
    check("V-STR-NODES-TYPED", nodes["sid.jsonl"]["kind"] == "main" and nodes["sid.jsonl"]["turns"] == 2
          and sa.get("agent_type") == "gsd-planner" and sa.get("turns") == 1, str(rep["nodes"]))
    check("V-STR-CTX-PER-TURN", nodes["sid.jsonl"]["peak_ctx"] == 2020 and nodes["sid.jsonl"]["avg_ctx"] == 1515,
          str(nodes["sid.jsonl"]))
    print(f"STR_PASS={passes}/{passes + fails}  threshold=4/4")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
