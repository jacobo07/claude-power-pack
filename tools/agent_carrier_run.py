#!/usr/bin/env python3
"""agent_carrier_run -- dispatch one compiled AgentSpec through a REAL carrier.

Spec: vault/specs/agent-capability-virtualization.md (S2 real-boundary gate, S3
benchmark). Nothing here simulates the runtime: a `claude -p` parent makes one
real Agent tool call to the carrier, and the stream-json event log is the
evidence. Recorded per run:

  carrier_tools   every tool call the carrier made (from sidechain events)
  pages_read      which deep role pages it actually Read (paging, observed)
  image_read      whether it Read its context image (pointer delivery)
  returned_chars  size of what came back across the agent boundary
  reply           the carrier's final text (what the parent received)
  bundle          validator verdict, when the spec's contract is a proof bundle

  python tools/agent_carrier_run.py <spec_id> --mission-file m.md [--mode virtual]
        [--model sonnet] [--parent-model haiku] [--out run.json]

A run whose stream cannot be read is recorded as status=UNMEASURED with the
reason, never as an empty success.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.capability_runtime import agent_bundle as B  # noqa: E402
from modules.capability_runtime import agent_spec as A  # noqa: E402


def parse_stream(lines: list[str]) -> dict:
    """The Agent tool is ASYNC in this runtime (measured 2026-09-30): its tool_result is
    a 'launched' notice and the carrier's answer arrives later. So the carrier's reply is
    its own LAST sidechain text block, not the parent's tool_result."""
    carrier_tools, parent_agent_calls, agent_results, final, usage = [], [], [], "", {}
    carrier_text = ""
    for ln in lines:
        ln = ln.strip()
        if not ln.startswith("{"):
            continue
        try:
            ev = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict):
            continue
        side = ev.get("parent_tool_use_id")
        # Measured 2026-10-01 (GEX44, first writer run): some events carry `message` as a
        # string; reading it as a dict crashed the parser and lost the whole run record.
        msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
        content = [c for c in msg.get("content") or [] if isinstance(c, dict)] \
            if isinstance(msg.get("content"), list) else []
        if ev.get("type") == "assistant":
            for c in content:
                if c.get("type") == "tool_use":
                    rec = {"name": c.get("name"), "input": c.get("input") or {}}
                    (carrier_tools if side else parent_agent_calls).append(rec)
                elif c.get("type") == "text" and side and c.get("text", "").strip():
                    carrier_text = c["text"]
        elif ev.get("type") == "user" and not side:
            for c in content:
                if c.get("type") == "tool_result":
                    body = c.get("content")
                    text = body if isinstance(body, str) else "".join(
                        b.get("text", "") for b in (body or []) if isinstance(b, dict))
                    agent_results.append(text)
        elif ev.get("type") == "result":
            final, usage = ev.get("result") or "", ev.get("usage") or {}
    return {"carrier_tools": carrier_tools, "parent_calls": parent_agent_calls,
            "agent_results": agent_results, "final": final, "usage": usage,
            "carrier_text": carrier_text}


LAUNCH_RE = re.compile(r"(?i)\b(launched|running in the background|started in the background|async agent)\b")
AGENT_FOOTER_RE = re.compile(r"agentId:\s*[0-9a-f]{8,}[\s\S]*$")


def carrier_reply(s: dict) -> tuple[str, str]:
    """The carrier's answer and where it came from. Two runtime shapes, both measured:
      2.1.286 (2026-09-30): Agent is ASYNC -- the tool_result is a launch notice and the answer
               is the carrier's last SIDECHAIN text block.
      2.1.285 (2026-10-01, GEX44): Agent is SYNC -- no sidechain text is streamed at all; the
               answer is the parent's Agent tool_result, followed by an `agentId: ...` footer.
    Reading only the first shape recorded three GEX44 runs as MEASURED with reply=0."""
    if s.get("carrier_text", "").strip():
        return s["carrier_text"], "sidechain"
    tool_result = s["agent_results"][-1] if s.get("agent_results") else ""
    if tool_result and not LAUNCH_RE.search(tool_result[:300]):
        return AGENT_FOOTER_RE.sub("", tool_result).strip(), "tool_result"
    return "", "none"


def run(spec_id: str, mission: str, mode: str = "virtual", model: str | None = None,
        parent_model: str = "haiku", timeout: int = 900, state_version: str | None = None,
        stream_out: Path | None = None) -> dict:
    spec = A.load(spec_id)
    d = spec.dispatch(mission, mode, state_version=state_version)
    carrier_model = model or d.get("model") or "sonnet"
    exe = shutil.which("claude")
    if not exe:
        return {"status": "UNMEASURED", "reason": "claude CLI not on PATH"}
    parent_prompt = (
        f"Call the Agent tool exactly once with subagent_type `{d['subagent_type']}`, "
        f"model `{carrier_model}`, description `run {spec_id}`, and this prompt, verbatim, between the markers:\n"
        f"<<<PROMPT\n{d['prompt']}\nPROMPT>>>\n"
        "When it returns, output only the agent's reply, verbatim, with nothing added.")
    t0 = time.time()
    # ignore_cleanup_errors: measured 2026-10-01, a process the `claude -p` child left behind
    # still held this cwd, rmtree raised PermissionError on exit and the finished run's whole
    # record was lost. A leftover temp dir is litter; a lost measurement is not recoverable.
    with tempfile.TemporaryDirectory(prefix="acr-", ignore_cleanup_errors=True) as cwd:
        try:
            p = subprocess.run([exe, "-p", parent_prompt, "--model", parent_model,
                                "--output-format", "stream-json", "--verbose",
                                "--allowedTools", "Agent", "Read", "Grep", "Glob"],
                               cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"status": "UNMEASURED", "reason": f"timeout {timeout}s", "spec": spec_id, "mode": mode}
    if stream_out:
        # The raw event log is the evidence a record is derived from. A tool_use in the
        # record does not say whether the runtime let it run; the stream's results do.
        stream_out.parent.mkdir(parents=True, exist_ok=True)
        stream_out.write_text(p.stdout, encoding="utf-8")
    s = parse_stream(p.stdout.splitlines())
    if not s["parent_calls"]:
        return {"status": "UNMEASURED", "reason": f"parent made no tool call (exit {p.returncode})",
                "stderr": p.stderr[-400:], "spec": spec_id, "mode": mode}
    agent_call = next((c for c in s["parent_calls"] if c["name"] in ("Agent", "Task")), None)
    tool_result = s["agent_results"][-1] if s["agent_results"] else ""
    if not s["carrier_tools"] and "hook error" in tool_result[:200]:
        # Measured 2026-09-30: a PreToolUse gate refused the dispatch and its text came back
        # as the "reply". The carrier never ran; that is not a result of any kind.
        return {"status": "DISPATCH_BLOCKED", "reason": tool_result[:300], "spec": spec_id, "mode": mode}
    reply, reply_source = carrier_reply(s)
    if not reply.strip():
        # An empty answer is not a measurement (2026-10-01: three GEX44 runs were MEASURED, reply=0).
        return {"status": "UNMEASURED", "reason": "carrier reply empty in every known stream shape",
                "carrier_tools": [c["name"] for c in s["carrier_tools"]], "spec": spec_id, "mode": mode}
    reads = [str(c["input"].get("file_path", "")).replace("\\", "/") for c in s["carrier_tools"] if c["name"] == "Read"]
    deep = [(spec.page_path(pg)).as_posix() for pg in spec.pages if pg["load"] == "on_demand"]
    rec = {
        "status": "MEASURED", "spec": spec_id, "mode": mode, "carrier": d["subagent_type"],
        "carrier_model": carrier_model, "spec_hash": spec.spec_hash(), "seconds": round(time.time() - t0, 1),
        "dispatched_to": (agent_call or {}).get("input", {}).get("subagent_type"),
        "dispatch_prompt_chars": len(((agent_call or {}).get("input") or {}).get("prompt", "")),
        "image_read": any(r.endswith(Path(d["image"]).name) for r in reads),
        "carrier_tools": [{"name": c["name"], "path": c["input"].get("file_path") or c["input"].get("pattern")
                           or c["input"].get("command")} for c in s["carrier_tools"]],
        "pages_read": sorted({"/".join(r.split("/")[-2:]) for r in reads
                              if any(r.lower().endswith("/".join(x.split("/")[-2:]).lower()) for x in deep)}),
        "returned_chars": len(reply), "reply": reply, "reply_source": reply_source, "parent_usage": s["usage"],
    }
    if spec.output_contract == "proof-bundle-v1":
        res = B.validate(reply, spec, state_version or A.current_state_version(ROOT))
        rec["bundle"] = {"verdict": res["verdict"], "reasons": res["reasons"]}
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_id"); ap.add_argument("--mission-file", required=True)
    ap.add_argument("--mode", default="virtual", choices=A.MODES)
    ap.add_argument("--model"); ap.add_argument("--parent-model", default="haiku")
    ap.add_argument("--out"); ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args(argv)
    rec = run(a.spec_id, Path(a.mission_file).read_text(encoding="utf-8"), a.mode, a.model,
              a.parent_model, a.timeout, A.current_state_version(ROOT),
              Path(a.out).with_suffix(".stream.jsonl") if a.out else None)
    text = json.dumps(rec, indent=1)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    brief = {k: v for k, v in rec.items() if k not in ("reply", "carrier_tools")}
    print(json.dumps(brief, indent=1))
    return 0 if rec.get("status") == "MEASURED" else 1


if __name__ == "__main__":
    sys.exit(main())
