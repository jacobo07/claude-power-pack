#!/usr/bin/env python3
"""C1 reader: provider-measured first-call total of a subagent, from raw transcripts. Not a ccr_* tool.

    python3 c1_measure.py SESSION_TRANSCRIPT.jsonl            -> JSON {agents: {id: {first_call_total, model, answer}}}
    python3 c1_measure.py --selftest

first_call_total = input_tokens + cache_creation_input_tokens + cache_read_input_tokens of the FIRST non-synthetic
assistant row of that agent (the definition floor_regression_gate._USAGE_KEYS uses for the main loop).
A subagent's rows are those with an `agentId` or `isSidechain: true` in the session transcript, plus any
<session>/subagents/agent-*.jsonl beside it. An agent with no usable assistant row is UNKNOWN, never 0.
"""
import json
import sys
from pathlib import Path

KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def _rows(path):
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if isinstance(d, dict):
            yield d


def _text(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")


def measure(session_transcript):
    p = Path(session_transcript)
    files = [p] + sorted((p.parent / p.stem / "subagents").glob("agent-*.jsonl"))
    agents = {}
    for f in files:
        for d in _rows(f):
            aid = d.get("agentId") or (f.stem.split("agent-", 1)[1] if f is not p else None)
            if aid is None and not d.get("isSidechain"):
                continue
            aid = aid or "sidechain"
            a = agents.setdefault(aid, {"first_call_total": None, "model": None, "answer": None})
            if d.get("type") != "assistant":
                continue
            m = d.get("message") or {}
            if m.get("model") in (None, "<synthetic>") or not isinstance(m.get("usage"), dict):
                continue
            if a["first_call_total"] is None:
                a["first_call_total"] = sum(int(m["usage"].get(k) or 0) for k in KEYS)
                a["model"] = m.get("model")
            t = _text(m).strip()
            if t:
                a["answer"] = t
    return {"agents": agents}


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        s = Path(td) / "S.jsonl"
        row = lambda **k: json.dumps(k)  # noqa: E731
        u = lambda i, c, r: {"input_tokens": i, "cache_creation_input_tokens": c, "cache_read_input_tokens": r}  # noqa: E731
        s.write_text("\n".join([
            row(type="assistant", message={"model": "m", "usage": u(1, 2, 3), "content": [{"type": "text", "text": "main"}]}),
            row(type="assistant", agentId="A1", isSidechain=True, message={"model": "<synthetic>", "usage": u(0, 0, 0), "content": []}),
            row(type="assistant", agentId="A1", isSidechain=True, message={"model": "m", "usage": u(10, 20, 30), "content": [{"type": "text", "text": "OK"}]}),
            row(type="assistant", agentId="A1", isSidechain=True, message={"model": "m", "usage": u(99, 99, 99), "content": []}),
            row(type="assistant", agentId="A2", isSidechain=True, message={"model": "<synthetic>", "usage": u(0, 0, 0), "content": []}),
        ]) + "\n")
        r = measure(s)["agents"]
        ok = r["A1"]["first_call_total"] == 60 and r["A1"]["answer"] == "OK" and r["A2"]["first_call_total"] is None and "sidechain" not in r
        print("SELFTEST", "PASS" if ok else f"FAIL {r}")
        return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(_selftest())
    print(json.dumps(measure(sys.argv[1]), indent=1))
