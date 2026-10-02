#!/usr/bin/env python3
"""V-SHAPE-* gates: execution shape per root (plan s12 commit 5, audit G5/G6).

One human root P1 whose subagent A spawns a NESTED subagent C. A's transcript has
its own promptId line, so a one-level ancestry (the spawn row's prompt) charges
C to A's prompt instead of P1: the transitive resolver must not. Shape per root:
area (calls), surface (input + cache write + cache read), depth (longest
sequential call chain, children by max), spawn-tree height, width (peak
concurrent subagent transcripts, an approximation from call timestamps), wall
and active duration. Per-root sums must equal the window. Hermetic; no model call."""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fanout_ledger as fl  # noqa: E402
import usage_index as ux  # noqa: E402

PASS = FAIL = 0
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()


def ok(gate, cond, ev):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"  {'PASS' if cond else 'FAIL'} {gate}: {ev}")


def iso(h):
    return datetime.fromtimestamp(T0 + h * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def call(mid, h, sess, spawns=(), cr=100):
    content = [{"type": "tool_use", "id": s, "name": "Agent",
                "input": {"subagent_type": "Explore", "prompt": "x"}} for s in spawns]
    return json.dumps({"type": "assistant", "timestamp": iso(h), "sessionId": sess,
                       "requestId": "r" + mid,
                       "message": {"id": mid, "model": "claude-opus-5-5", "content": content,
                                   "usage": {"input_tokens": 1, "cache_read_input_tokens": cr,
                                             "cache_creation_input_tokens": 10,
                                             "output_tokens": 5}}}) + "\n"


def prompt(pid, h, sess, kind="human"):
    return json.dumps({"type": "user", "promptId": pid, "timestamp": iso(h), "sessionId": sess,
                       "origin": {"kind": kind}}) + "\n"


def sub(d: Path, name: str, tuid: str, depth: int, body: str) -> None:
    (d / f"agent-{name}.jsonl").write_text(body, encoding="utf-8")
    (d / f"agent-{name}.meta.json").write_text(
        json.dumps({"agentType": "Explore", "toolUseId": tuid, "spawnDepth": depth}),
        encoding="utf-8")


def build(proj: Path) -> None:
    p = proj / "C--p"
    subs = p / "S1" / "subagents"
    subs.mkdir(parents=True)
    (p / "S1.jsonl").write_text(
        prompt("P1", 0.99, "S1") + call("m1", 1.0, "S1", spawns=("tuA", "tuB"))
        + call("m2", 1.1, "S1") + call("m3", 1.4, "S1"), encoding="utf-8")   # 1.15 -> 1.4: idle
    sub(subs, "a", "tuA", 1,
        prompt("PA", 1.04, "S1", kind="task") + call("a1", 1.05, "S1")
        + call("a2", 1.08, "S1", spawns=("tuC",)) + call("a3", 1.12, "S1") + call("a4", 1.15, "S1"))
    sub(subs, "b", "tuB", 1, call("b1", 1.07, "S1"))
    sub(subs, "c", "tuC", 2, call("c1", 1.12, "S1") + call("c2", 1.13, "S1"))
    # A session with no promptId at all: its call has no root and must still be counted.
    (p / "S2.jsonl").write_text(call("u1", 1.5, "S2"), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        proj = Path(td) / "projects"
        build(proj)
        con = ux.connect(Path(td) / "ix.sqlite")
        try:
            r = ux.refresh(con, proj, deadline_s=30)
            ok("V-SHAPE-REFRESH", r["status"] == "OK", json.dumps(r))
            rows = fl.load_calls(con, T0, T0 + 10 * 3600)
            c_root = {x["prompt"] for x in rows if x["file"].endswith("agent-c.jsonl")}
            ok("V-SHAPE-TRANSITIVE-ROOT", c_root == {"P1"},
               f"nested subagent C charged to {c_root} (want P1, not A's own prompt PA)")
            ok("V-SHAPE-ROOT-CLASS", {x["root"] for x in rows if x["prompt"] == "P1"} == {"HUMAN"},
               "every call under P1, nested included, classes as HUMAN")

            res = fl.shape(con, T0, T0 + 10 * 3600)
            by = {s["prompt"]: s for s in res["roots"]}
            p1 = by.get("P1", {})
            ok("V-SHAPE-AREA", p1.get("area") == 10 and p1.get("parent_calls") == 3,
               f"area={p1.get('area')} parent={p1.get('parent_calls')} (3 parent + 4 A + 1 B + 2 C)")
            ok("V-SHAPE-SURFACE", p1.get("surface") == 10 * 111, f"surface={p1.get('surface')}")
            ok("V-SHAPE-DEPTH", p1.get("depth_calls") == 9,
               f"depth={p1.get('depth_calls')} (3 parent + max(A 4 + C 2, B 1))")
            ok("V-SHAPE-HEIGHT", p1.get("spawn_height") == 2, f"height={p1.get('spawn_height')}")
            ok("V-SHAPE-WIDTH", p1.get("width_approx") == 2,
               f"width={p1.get('width_approx')} (A overlaps B, then A overlaps C)")
            ok("V-SHAPE-SPAWNS", p1.get("spawns") == 3, f"spawns={p1.get('spawns')} (nested C counted)")
            ok("V-SHAPE-WALL", p1.get("wall_s") == round(0.4 * 3600), f"wall_s={p1.get('wall_s')}")
            ok("V-SHAPE-ACTIVE", p1.get("active_s") == round(0.4 * 3600) - round(0.25 * 3600),
               f"active_s={p1.get('active_s')} (wall minus the one 900 s gap over "
               f"{fl.ACTIVE_GAP_S}s; every other gap <= 180 s)")
            ok("V-SHAPE-UNROOTED", res["unrooted"]["calls"] == 1, f"unrooted={res['unrooted']}")
            w = ux.window(con, T0, T0 + 10 * 3600)
            ok("V-SHAPE-SUMS", res["check"]["calls"] == w["calls"] == 11
               and res["check"]["consistent"],
               f"roots+unrooted={res['check']['calls']} window={w['calls']} {res['check']}")
            tree = fl.prompt_tree(con, "P1")
            ok("V-SHAPE-TREE", tree.get("shape", {}).get("depth_calls") == 9,
               "the prompt tree carries its shape")
        finally:
            con.close()

    total = PASS + FAIL
    print(f"EXECUTION_SHAPE_PASS={PASS}/{total}  threshold={total}/{total}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
