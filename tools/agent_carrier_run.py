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
from modules.capability_runtime import agent_telemetry as T  # noqa: E402


DENIED_RE = re.compile(r"Permission to use (\w+) has been denied")


def _posix_root(root: str) -> str:
    """Absolute path in the permission engine's form: POSIX, Windows drive as /c/..."""
    p = str(root).replace("\\", "/").rstrip("/")
    m = re.match(r"^([A-Za-z]):(/.*)?$", p)
    return f"/{m.group(1).lower()}{m.group(2) or ''}" if m else p


# Paths the permission system never auto-approves outside bypassPermissions, whatever the
# allow rules say (docs: permission-modes "Protected paths", sandboxing "Protected paths").
# Headless dontAsk turns that into a denial, so a grant over one is a grant that cannot work.
PROTECTED_DIRS = {".claude", ".git", ".vscode", ".idea"}
PROTECTED_FILES = {".mcp.json", ".bashrc", ".zshrc", ".profile", ".bash_profile", ".gitconfig"}


def _surfaces(spec: A.AgentSpec) -> list[str]:
    out = []
    for s in spec.contract.write_surfaces:
        s = str(s).replace("\\", "/")
        parts = [p for p in s.split("/") if p not in ("", ".")]
        if s.startswith("/") or re.match(r"^[A-Za-z]:", s) or ".." in parts:
            raise A.AgentSpecError("SURFACE_ESCAPES_ROOT", f"{spec.id}: {s!r} is not relative to the target root")
        if parts and (parts[0] in PROTECTED_DIRS or parts[-1] in PROTECTED_FILES):
            raise A.AgentSpecError("SURFACE_PROTECTED",
                                   f"{spec.id}: {s!r} is a protected path; a headless run can never write it")
        out.append(s)
    return out


def write_grant(spec: A.AgentSpec, target_root: str | None) -> list[str]:
    """Runtime allow rules bounding a writer carrier to its declared write_surfaces under one
    explicit target root (Owner go 2026-10-01). Headless `claude -p` grants a carrier nothing
    the parent was not granted; measured 2026-10-01, the writer's Edit was denied outright.

    Only `Edit(...)` rules: per the permission docs an Edit rule governs every built-in file
    editor including Write, while a `Write(path)` rule is accepted and never consulted -- a
    grant written that way would look scoped and do nothing. `//` marks an absolute path; a
    single `/` would anchor at the working directory. A directory surface (trailing /) grants
    its subtree, a file surface grants that file only."""
    if not target_root:
        return []
    if spec.permission_class != "writer":
        raise A.AgentSpecError("GRANT_EXCEEDS_CLASS",
                               f"{spec.id} is {spec.permission_class}; only a writer may receive a write grant")
    root = _posix_root(target_root)
    return [f"Edit(/{root}/{s.rstrip('/')}/**)" if s.endswith("/") else f"Edit(/{root}/{s})"
            for s in _surfaces(spec)]


def writes_outside(target_root: str, surfaces: list[str], written: list[str]) -> list[str]:
    """Paths the carrier edited that no declared surface covers. Judged from the record,
    independently of what the runtime allowed, so a grant wider than intended shows up."""
    root = _posix_root(target_root)
    allowed = [(root + "/" + s.replace("\\", "/"), s.endswith("/")) for s in surfaces]
    out = []
    for w in written:
        p = _posix_root(w)
        if not any(p.startswith(a) if is_dir else p == a for a, is_dir in allowed):
            out.append(w)
    return out


def carrier_agents_json(permission_class: str) -> str:
    """The carrier definition, from the repo file, for `--agents`. A hermetic run excludes
    user settings, and measured 2026-10-01 that also hides ~/.claude/agents ("Agent type
    'cpp-carrier-writer' not found"), so the carrier has to travel with the run."""
    name = A.carrier_name(permission_class)
    text = (A.CARRIERS_DIR / f"{name}.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise A.AgentSpecError("CARRIER_UNREADABLE", name)
    fm, body = m.groups()
    field = lambda k: ((re.search(rf"(?m)^{k}:\s*(.+)$", fm) or [None, ""])[1]).strip()
    tools = re.findall(r"[A-Za-z]+", field("tools"))
    if sorted(tools) != sorted(A.CLASS_TOOLS[permission_class]):
        raise A.AgentSpecError("CARRIER_TOOLS_DRIFT", f"{name}: {tools} != {A.CLASS_TOOLS[permission_class]}")
    return json.dumps({name: {"description": field("description"), "prompt": body, "tools": tools}})


def parent_argv(exe: str, prompt: str, parent_model: str, grant: list[str], permission_class: str) -> list[str]:
    """Without a grant: the historical argv (S2/S3 runs were measured with it). With a grant
    the run is HERMETIC, or the grant is a lie: measured 2026-10-01 on GEX44, whose user
    settings allow Edit everywhere, a scoped grant narrowed nothing and an out-of-surface edit
    landed. dontAsk denies whatever is not granted; project/local sources keep the host's
    user-level allows out; the carrier then has to be passed inline."""
    argv = [exe, "-p", prompt, "--model", parent_model, "--output-format", "stream-json", "--verbose"]
    if grant:
        argv += ["--setting-sources", "project,local", "--permission-mode", "dontAsk",
                 "--agents", carrier_agents_json(permission_class)]
    return argv + ["--allowedTools", "Agent", "Read", "Grep", "Glob", *grant]


def parse_stream(lines: list[str]) -> dict:
    """The Agent tool is ASYNC in this runtime (measured 2026-09-30): its tool_result is
    a 'launched' notice and the carrier's answer arrives later. So the carrier's reply is
    its own LAST sidechain text block, not the parent's tool_result."""
    carrier_tools, parent_agent_calls, agent_results, final, usage = [], [], [], "", {}
    carrier_text, denied = "", []
    # Run accounting (ACV C6): every result event (real streams carry two), the first session id
    # seen (the init event has it even when a timeout cuts the result off), and the models each
    # side ACTUALLY ran on, from message.model.
    results, init_session, models = [], None, {"parent": set(), "carrier": set()}
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
        if init_session is None and isinstance(ev.get("session_id"), str):
            init_session = ev["session_id"]
        if ev.get("type") == "assistant":
            if isinstance(msg.get("model"), str):
                models["carrier" if side else "parent"].add(msg["model"])
            for c in content:
                if c.get("type") == "tool_use":
                    rec = {"name": c.get("name"), "input": c.get("input") or {}}
                    (carrier_tools if side else parent_agent_calls).append(rec)
                elif c.get("type") == "text" and side and c.get("text", "").strip():
                    carrier_text = c["text"]
        elif ev.get("type") == "user":
            for c in content:
                if c.get("type") != "tool_result":
                    continue
                body = c.get("content")
                text = body if isinstance(body, str) else "".join(
                    b.get("text", "") for b in (body or []) if isinstance(b, dict))
                # A tool_use in the record says only that the call was attempted. Measured
                # 2026-10-01: a writer carrier's Edit was refused by the runtime and the run
                # still read MEASURED. The refusal is a fact of the run; record it.
                if c.get("is_error") and (d := DENIED_RE.match(text)):
                    denied.append(d.group(1))
                if not side:
                    agent_results.append(text)
        elif ev.get("type") == "result":
            final, usage = ev.get("result") or "", ev.get("usage") or {}
            results.append(ev)
    return {"carrier_tools": carrier_tools, "parent_calls": parent_agent_calls,
            "agent_results": agent_results, "final": final, "usage": usage,
            "carrier_text": carrier_text, "denied_tools": denied,
            "results": results, "init_session": init_session, "models": models}


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


def _run_body(spec_id: str, mission: str, mode: str, model: str | None, parent_model: str, timeout: int,
              state_version: str | None, stream_out: Path | None, target_root: str | None,
              specs_dir: Path | None, box: dict) -> dict:
    """One dispatch and its judged record. `box` carries what run() needs to account for the run
    whatever happens here: whether the process started, its stdout, the spec and the clock."""
    spec = A.load(spec_id, specs_dir)
    grant = write_grant(spec, target_root)        # typed refusal before anything is dispatched
    d = spec.dispatch(mission, mode, state_version=state_version)
    carrier_model = model or d.get("model") or "sonnet"
    box.update(spec=spec, carrier=d["subagent_type"], carrier_model=carrier_model)
    exe = shutil.which("claude")
    if not exe:
        return {"status": "UNMEASURED", "reason": "claude CLI not on PATH"}
    parent_prompt = (
        f"Call the Agent tool exactly once with subagent_type `{d['subagent_type']}`, "
        f"model `{carrier_model}`, description `run {spec_id}`, and this prompt, verbatim, between the markers:\n"
        f"<<<PROMPT\n{d['prompt']}\nPROMPT>>>\n"
        "When it returns, output only the agent's reply, verbatim, with nothing added.")
    t0 = box["t0"] = time.time()
    # ignore_cleanup_errors: measured 2026-10-01, a process the `claude -p` child left behind
    # still held this cwd, rmtree raised PermissionError on exit and the finished run's whole
    # record was lost. A leftover temp dir is litter; a lost measurement is not recoverable.
    with tempfile.TemporaryDirectory(prefix="acr-", ignore_cleanup_errors=True) as cwd:
        try:
            # stdin closed: `claude -p` reads stdin, and inherited it swallowed the rest of a
            # `bash -s` script on GEX44 (measured 2026-10-01).
            box["started"] = True                 # from here on the run spends tokens (C6 gap 3)
            p = subprocess.run(parent_argv(exe, parent_prompt, parent_model, grant, spec.permission_class),
                               cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
            box["stdout"] = p.stdout or ""
        except subprocess.TimeoutExpired as e:
            # The partial output is bytes even with text=True; its init event still names the
            # session (C6 gap 5).
            box["timed_out"], box["stdout"] = True, _text(e.stdout)
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
        "denied_tools": s["denied_tools"],
        "write_grant": grant, "hermetic": bool(grant),
    }
    written = [str(c["input"].get("file_path", "")) for c in s["carrier_tools"]
               if c["name"] in ("Edit", "Write", "MultiEdit", "NotebookEdit")]
    if target_root:
        # Attempted writes, not proven ones: a denied attempt is listed here AND in denied_tools.
        rec["write_attempts"] = written
        rec["writes_outside_surface"] = writes_outside(target_root, _surfaces(spec), written)
    if spec.output_contract == "proof-bundle-v1":
        res = B.validate(reply, spec, state_version or A.current_state_version(ROOT))
        rec["bundle"] = {"verdict": res["verdict"], "reasons": res["reasons"]}
    return rec


def _text(out) -> str:
    if out is None:
        return ""
    return out.decode("utf-8", errors="replace") if isinstance(out, bytes) else str(out)


def run(spec_id: str, mission: str, mode: str = "virtual", model: str | None = None,
        parent_model: str = "haiku", timeout: int = 900, state_version: str | None = None,
        stream_out: Path | None = None, target_root: str | None = None,
        specs_dir: Path | None = None, *, purpose: str = "manual", resolution_id: str | None = None,
        sink=None) -> dict:
    """Dispatch one spec and account for it (ACV C6). Every run whose `claude -p` process STARTED
    emits exactly one terminal CO-12 `agent_run` signal -- on success, on an early exit, on a
    timeout, and on an exception raised after the start (re-raised unchanged). A run that never
    started (CLI missing, typed spec error before dispatch) emits nothing: no tokens were spent.
    `resolution_id` comes only from the resolver (resolve_and_run); a direct spec_id run is
    unlinked (None). Residual blind spots: a hard kill of this harness, and a post-timeout hang
    on Windows when a grandchild still holds the pipe -- neither reaches the finally."""
    box: dict = {}
    rec = None
    try:
        rec = _run_body(spec_id, mission, mode, model, parent_model, timeout, state_version, stream_out,
                        target_root, specs_dir, box)
        return rec
    finally:
        if box.get("started"):
            _account(box, rec, purpose=purpose, resolution_id=resolution_id, sink=sink)


def _account(box: dict, rec: dict | None, *, purpose: str, resolution_id: str | None, sink) -> None:
    run_id, recorded = None, False
    try:
        s = parse_stream(box.get("stdout", "").splitlines())
        last = s["results"][-1] if s["results"] else None
        run_id = (last or {}).get("session_id") or s["init_session"]
        source = "result" if (last or {}).get("session_id") else ("init" if s["init_session"] else "none")
        spec = box["spec"]
        payload = T.run_payload(
            resolution_id=resolution_id, run_id=run_id, run_id_source=source, spec=spec.id,
            spec_hash=spec.spec_hash(), permission_class=spec.permission_class, carrier=box.get("carrier"),
            purpose=purpose,
            executor_status=(last or {}).get("subtype") or ("TIMEOUT" if box.get("timed_out") else "NO_RESULT"),
            executor_error=last.get("is_error") if last else None,
            harness_status=(rec or {}).get("status") or "HARNESS_ERROR", results=s["results"],
            models_observed=s["models"], carrier_model_configured=box.get("carrier_model"),
            seconds=round(time.time() - box.get("t0", time.time()), 1))
        recorded = T.record_run(payload, sink=sink)
    except Exception:  # noqa: BLE001 -- accounting never changes or breaks the run it describes
        recorded = False
    if rec is not None:
        rec["run_id"], rec["run_recorded"] = run_id, recorded


def resolve_and_run(task: str, mission: str, max_class: str = "verifier", k: int = 3,
                    specs_dir: Path | None = None, use_cache: bool = True, cache_path: Path | None = None,
                    *, sink=None, **run_kw) -> dict:
    """Request -> resolution -> run. One resolve (C5 telemetry: one agent_resolution signal); if it
    certified a specialist, the top candidate runs with that resolution_id, so its agent_run joins
    the resolution. No candidate -> no run, and the resolution stays visible with zero runs."""
    rr = T.resolve_and_record(task, max_class, k, specs_dir=specs_dir, use_cache=use_cache,
                              cache_path=cache_path, sink=sink)
    res = rr.result
    out = {"resolution_id": rr.resolution_id, "resolution_recorded": rr.recorded,
           "resolver_status": res["status"], "miss": res["miss"]}
    if not res["candidates"]:
        return {**out, "status": "NO_RUN", "reason": f"no certified specialist ({res['miss']})"}
    spec_id = res["candidates"][0]["id"]
    rec = run(spec_id, mission, specs_dir=specs_dir, purpose="resolved", resolution_id=rr.resolution_id,
              sink=sink, **run_kw)
    rec.update(out, resolved_spec=spec_id)
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_id", nargs="?", help="run this spec directly (unlinked); or use --resolve")
    ap.add_argument("--resolve", metavar="TASK", help="resolve TASK first; run the certified top candidate")
    ap.add_argument("--max-class", default="verifier", choices=A.CLASS_ORDER, help="grant for --resolve")
    ap.add_argument("--mission-file", required=True)
    ap.add_argument("--mode", default="virtual", choices=A.MODES)
    ap.add_argument("--model"); ap.add_argument("--parent-model", default="haiku")
    ap.add_argument("--out"); ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--target-root", help="writer only: grant Edit on the spec's write_surfaces under this dir")
    ap.add_argument("--specs-dir", help="alternate spec catalog (synthetic probes); default = the repo's")
    a = ap.parse_args(argv)
    if bool(a.spec_id) == bool(a.resolve):
        print("AGENTSPEC_ERROR USAGE give exactly one of <spec_id> or --resolve TASK", file=sys.stderr)
        return 2
    if a.target_root and not Path(a.target_root).is_dir():
        print(f"AGENTSPEC_ERROR NO_TARGET_ROOT {a.target_root} is not a directory", file=sys.stderr)
        return 2
    kw = dict(mode=a.mode, model=a.model, parent_model=a.parent_model, timeout=a.timeout,
              state_version=A.current_state_version(ROOT),
              stream_out=Path(a.out).with_suffix(".stream.jsonl") if a.out else None,
              target_root=a.target_root, specs_dir=Path(a.specs_dir) if a.specs_dir else None)
    mission = Path(a.mission_file).read_text(encoding="utf-8")
    try:
        if a.resolve:
            specs_dir = kw.pop("specs_dir")
            rec = resolve_and_run(a.resolve, mission, a.max_class, specs_dir=specs_dir, **kw)
        else:
            rec = run(a.spec_id, mission, **kw)
    except A.AgentSpecError as e:
        print(f"AGENTSPEC_ERROR {e.code} {e}", file=sys.stderr)
        return 2
    if rec.get("run_recorded") is False:
        print(f"RUN_NOT_RECORDED run_id={rec.get('run_id')} (CO-12 write failed; the record below is unaffected)",
              file=sys.stderr)
    text = json.dumps(rec, indent=1)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    brief = {k: v for k, v in rec.items() if k not in ("reply", "carrier_tools")}
    print(json.dumps(brief, indent=1))
    return 0 if rec.get("status") == "MEASURED" else 1


if __name__ == "__main__":
    sys.exit(main())
