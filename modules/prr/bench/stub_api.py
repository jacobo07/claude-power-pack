"""stub_api.py -- deterministic local stand-in for the Anthropic Messages API (PRR memory benchmark).

Lets a REAL claude process run hundreds of turns with zero provider tokens, so the host's
allocation behaviour (transcript, tool results, compaction, resume) is measured faithfully
while only the model's replies are scripted.

Script per request:
  - last user content holds a tool_result  -> text "ok", stop end_turn
  - a fresh user turn and PRR_TOOL_BYTES>0 -> one Bash tool_use printing PRR_TOOL_BYTES chars
  - anything else (titles, summaries, side calls) -> text "ok"
Every request's body size is appended to PRR_STUB_LOG (JSON lines), which measures the
context the host re-sends each call.

stdlib only; Python 3.8+. Usage: python3 stub_api.py --port 8765 --tool-bytes 20000 --log req.jsonl
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ids = itertools.count(1)
CFG = {"tool_bytes": 0, "log": None, "summary_bytes": 400, "script": "bash", "image": None}


def _has_tool_result(msg: dict) -> bool:
    content = msg.get("content")
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def _is_summary_request(body: dict) -> bool:
    msgs = body.get("messages") or []
    last = msgs[-1] if msgs else {}
    content = last.get("content")
    text = content if isinstance(content, str) else " ".join(
        b.get("text", "") for b in (content or []) if isinstance(b, dict))
    return "summary" in text.lower() and "conversation" in text.lower()


def plan_reply(body: dict) -> dict:
    msgs = body.get("messages") or []
    last = msgs[-1] if msgs else {}
    if _is_summary_request(body):
        return {"kind": "text", "text": "<summary>" + ("s" * CFG["summary_bytes"]) + "</summary>"}
    if last.get("role") == "user" and _has_tool_result(last):
        return {"kind": "text", "text": "ok"}
    tools = {t.get("name") for t in (body.get("tools") or []) if isinstance(t, dict)}
    fresh = last.get("role") == "user"
    if fresh and CFG["script"] == "agent":
        agent_tool = "Agent" if "Agent" in tools else ("Task" if "Task" in tools else None)
        if agent_tool:
            return {"kind": "tool", "name": agent_tool,
                    "input": {"description": "prr fixture agent", "prompt": "prr subagent turn",
                              "subagent_type": "general-purpose"}}
    if fresh and CFG["script"] == "image" and CFG["image"] and "Read" in tools:
        return {"kind": "tool", "name": "Read", "input": {"file_path": CFG["image"]}}
    if CFG["tool_bytes"] > 0 and "Bash" in tools and fresh:
        n = int(CFG["tool_bytes"])
        return {"kind": "tool", "name": "Bash",
                "input": {"command": f"python3 -c \"print('x'*{n})\"", "description": "prr fixture output"}}
    return {"kind": "text", "text": "ok"}


def _message(model: str, reply: dict, mid: str) -> dict:
    if reply["kind"] == "tool":
        content = [{"type": "tool_use", "id": f"toolu_prr{mid}", "name": reply["name"], "input": reply["input"]}]
        stop = "tool_use"
    else:
        content = [{"type": "text", "text": reply["text"]}]
        stop = "end_turn"
    return {"id": f"msg_prr{mid}", "type": "message", "role": "assistant", "model": model,
            "content": content, "stop_reason": stop, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5,
                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}


def _sse(model: str, reply: dict, mid: str):
    msg = _message(model, reply, mid)
    start = dict(msg, content=[], stop_reason=None)
    yield "message_start", {"type": "message_start", "message": start}
    block = msg["content"][0]
    if block["type"] == "text":
        yield "content_block_start", {"type": "content_block_start", "index": 0,
                                      "content_block": {"type": "text", "text": ""}}
        yield "content_block_delta", {"type": "content_block_delta", "index": 0,
                                      "delta": {"type": "text_delta", "text": block["text"]}}
    else:
        yield "content_block_start", {"type": "content_block_start", "index": 0,
                                      "content_block": {"type": "tool_use", "id": block["id"],
                                                        "name": block["name"], "input": {}}}
        yield "content_block_delta", {"type": "content_block_delta", "index": 0,
                                      "delta": {"type": "input_json_delta",
                                                "partial_json": json.dumps(block["input"])}}
    yield "content_block_stop", {"type": "content_block_stop", "index": 0}
    yield "message_delta", {"type": "message_delta",
                            "delta": {"stop_reason": msg["stop_reason"], "stop_sequence": None},
                            "usage": {"output_tokens": 5}}
    yield "message_stop", {"type": "message_stop"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quiet: the JSONL log is the record
        return

    def _send_json(self, code: int, obj: dict):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send_json(200, {"data": [], "has_more": False})

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("content-length", "0")
        self.end_headers()

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        try:
            body = json.loads(raw or b"{}")
        except ValueError:
            self._send_json(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "bad json"}})
            return
        path = self.path.split("?")[0]
        if path.endswith("/count_tokens"):
            self._send_json(200, {"input_tokens": max(1, len(raw) // 4)})
            return
        mid = str(next(_ids))
        reply = plan_reply(body)
        if CFG["log"]:
            with open(CFG["log"], "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"t": time.time(), "id": mid, "path": path, "bytes": len(raw),
                                     "n_messages": len(body.get("messages") or []),
                                     "reply": reply["kind"]}) + "\n")
        model = body.get("model") or "claude-haiku-4-5"
        if not body.get("stream"):
            self._send_json(200, _message(model, reply, mid))
            return
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.send_header("connection", "close")
        self.end_headers()
        for event, data in _sse(model, reply, mid):
            self.wfile.write(f"event: {event}\ndata: {json.dumps(data)}\n\n".encode())
        self.wfile.flush()
        self.close_connection = True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--tool-bytes", type=int, default=0)
    ap.add_argument("--log", default=None)
    ap.add_argument("--script", choices=["bash", "agent", "image"], default="bash")
    ap.add_argument("--image", default=None, help="image file the image script Reads each turn")
    args = ap.parse_args(argv)
    CFG.update(tool_bytes=args.tool_bytes, log=args.log, script=args.script, image=args.image)
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"stub_api listening 127.0.0.1:{args.port} tool_bytes={args.tool_bytes}", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
