"""V-ACR-* gates: the carrier's answer is extracted from BOTH runtime stream shapes.

Measured 2026-10-01: on GEX44 (claude 2.1.285) the Agent tool is synchronous and no sidechain
text is streamed, so a parser written for 2.1.286 (async, answer = last sidechain text)
recorded three benchmark runs as MEASURED with reply=0. Event shapes below mirror the real
2.1.285 capture (/tmp/acr_probe_stream.jsonl on GEX44, events 13/15) and the 2.1.286 runs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent_carrier_run as R  # noqa: E402

passes = fails = 0
TU = "toolu_01Crb94YcL6WTstGLEDzHhue"


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def ev(kind, content, side=None):
    return json.dumps({"type": kind, "parent_tool_use_id": side, "message": {"content": content}})


PARENT_CALL = ev("assistant", [{"type": "tool_use", "name": "Agent", "input": {"subagent_type": "cpp-carrier-verifier", "prompt": "p"}}])
CARRIER_READ = ev("assistant", [{"type": "tool_use", "name": "Read", "input": {"file_path": "/x/image.md"}}], side=TU)
CARRIER_PROMPT = ev("user", [{"type": "text", "text": "Your complete role is in /x/image.md"}], side=TU)


def result(text):
    return ev("user", [{"type": "tool_result", "tool_use_id": TU, "content": [{"type": "text", "text": text}]}])


def main():
    # Arrange/act/assert per shape.
    sync = [PARENT_CALL, CARRIER_PROMPT, CARRIER_READ,
            result("## Audit Result\n1. gap" + "agentId: a4b3371203bfa9b34 (use SendMessage with to: 'a4b33712' to continue)")]
    s = R.parse_stream(sync)
    reply, src = R.carrier_reply(s)
    check("V-ACR-SYNC-2_1_285-TOOL-RESULT", reply == "## Audit Result\n1. gap" and src == "tool_result",
          f"reply={reply!r} src={src} carrier_tools={[c['name'] for c in s['carrier_tools']]}")

    nl = [PARENT_CALL, CARRIER_READ, result("ANSWER\n\nagentId: deadbeef01 (use SendMessage)")]
    reply, src = R.carrier_reply(R.parse_stream(nl))
    check("V-ACR-SYNC-FOOTER-ON-OWN-LINE", reply == "ANSWER" and src == "tool_result", f"reply={reply!r}")

    asyn = [PARENT_CALL, result("Async agent launched successfully. agentId: a1b2c3d4e5"),
            CARRIER_READ, ev("assistant", [{"type": "text", "text": "SIDECHAIN ANSWER"}], side=TU)]
    reply, src = R.carrier_reply(R.parse_stream(asyn))
    check("V-ACR-ASYNC-2_1_286-SIDECHAIN", reply == "SIDECHAIN ANSWER" and src == "sidechain", f"reply={reply!r} src={src}")

    # Controls: nothing usable must stay empty, so run() records UNMEASURED, never an empty MEASURED.
    launch_only = [PARENT_CALL, result("Async agent launched successfully. agentId: a1b2c3d4e5"), CARRIER_READ]
    reply, src = R.carrier_reply(R.parse_stream(launch_only))
    check("V-ACR-LAUNCH-NOTICE-IS-NOT-AN-ANSWER", reply == "" and src == "none", f"reply={reply!r} src={src}")

    reply, src = R.carrier_reply(R.parse_stream([PARENT_CALL, CARRIER_READ]))
    check("V-ACR-NO-RESULT-IS-EMPTY", reply == "" and src == "none", f"reply={reply!r} src={src}")

    # Measured 2026-10-01 (GEX44, first writer-class run): an event whose `message` is a STRING
    # crashed parse_stream with AttributeError, and the run's whole record was lost as a traceback.
    # Odd events are skipped; the usable events around them still parse.
    odd = [PARENT_CALL, json.dumps({"type": "system", "message": "permission denied: Edit"}),
           ev("assistant", ["bare string item", {"type": "text", "text": "SIDE"}], side=TU),
           CARRIER_READ, result("WRITER ANSWER")]
    try:
        s = R.parse_stream(odd)
        reply, src = R.carrier_reply(s)
        ok = reply == "SIDE" and len(s["carrier_tools"]) == 1 and len(s["parent_calls"]) == 1
        detail = f"reply={reply!r} src={src} carrier_tools={len(s['carrier_tools'])}"
    except (AttributeError, TypeError) as e:
        ok, detail = False, f"crashed: {e!r}"
    check("V-ACR-STRING-MESSAGE-DOES-NOT-CRASH", ok, detail)

    # Measured 2026-10-01 (GEX44, writer run 2): the runtime denied the carrier's Edit, the
    # carrier said so, and the record still read MEASURED with no trace of the refusal.
    denial = ev("user", [{"type": "tool_result", "tool_use_id": "t2", "is_error": True,
                          "content": "Permission to use Edit has been denied. IMPORTANT: ..."}], side=TU)
    s = R.parse_stream([PARENT_CALL, CARRIER_READ, denial, result("ANSWER")])
    check("V-ACR-DENIAL-RECORDED", s.get("denied_tools") == ["Edit"], f"denied={s.get('denied_tools')}")
    s = R.parse_stream([PARENT_CALL, CARRIER_READ, result("ANSWER")])
    check("V-ACR-NO-DENIAL-IS-EMPTY", s.get("denied_tools") == [], f"denied={s.get('denied_tools')}")

    # Write grant (Owner go 2026-10-01): the runtime, not the prompt, bounds a writer's surface.
    # Docs: `//` = absolute, Windows paths normalise to //c/...; Edit rules also govern Write,
    # and a Write(path) rule is accepted but never consulted -- so only Edit rules are emitted.
    from modules.capability_runtime import agent_spec as A
    ho = A.load("harness-optimizer")
    syn = A.AgentSpec(json.loads(json.dumps(ho.raw)), ho.dir)      # synthetic writer, unprotected surface
    syn.contract.write_surfaces = ["docs/", "notes.md"]
    g = R.write_grant(syn, "/home/kobii/t/")
    check("V-ACR-GRANT-POSIX", g == ["Edit(//home/kobii/t/docs/**)", "Edit(//home/kobii/t/notes.md)"], f"{g}")
    g = R.write_grant(syn, r"C:\Users\U\target")
    check("V-ACR-GRANT-WINDOWS", g[0] == "Edit(//c/Users/U/target/docs/**)", f"{g}")
    check("V-ACR-GRANT-NONE-WITHOUT-ROOT", R.write_grant(syn, None) == [], "no target root -> no grant")

    def refused(spec, root):
        try:
            R.write_grant(spec, root)
            return False
        except A.AgentSpecError as e:
            return e.code
    # Measured 2026-10-01: .claude/ is a protected path; dontAsk denied the writer's in-surface
    # edit although it was granted. harness-optimizer's whole surface is protected.
    check("V-ACR-GRANT-REFUSES-PROTECTED", refused(ho, "/t") == "SURFACE_PROTECTED",
          f"harness-optimizer surfaces {ho.contract.write_surfaces}")
    check("V-ACR-GRANT-REFUSES-NON-WRITER", refused(A.load("python-reviewer"), "/t") == "GRANT_EXCEEDS_CLASS",
          "a verifier with a target root is refused, never granted Edit")

    # A grant forces a hermetic run; no grant leaves the historical argv untouched.
    hv = R.parent_argv("claude", "P", "haiku", ["Edit(//t/docs/**)"], "writer")
    agents = json.loads(hv[hv.index("--agents") + 1]) if "--agents" in hv else {}
    check("V-ACR-ARGV-HERMETIC-WITH-GRANT",
          hv[hv.index("--permission-mode") + 1] == "dontAsk"
          and hv[hv.index("--setting-sources") + 1] == "project,local"
          and sorted(agents.get("cpp-carrier-writer", {}).get("tools", [])) == sorted(A.CLASS_TOOLS["writer"])
          and agents["cpp-carrier-writer"]["prompt"].strip() and hv[-1] == "Edit(//t/docs/**)",
          f"flags={[x for x in hv if x.startswith('--')]}")
    pv = R.parent_argv("claude", "P", "haiku", [], "verifier")
    check("V-ACR-ARGV-UNCHANGED-WITHOUT-GRANT",
          not {"--permission-mode", "--setting-sources", "--agents"} & set(pv)
          and pv[-4:] == ["Agent", "Read", "Grep", "Glob"], f"{pv[3:]}")

    esc = A.AgentSpec(json.loads(json.dumps(ho.raw)), ho.dir)
    esc.contract.write_surfaces = ["../outside/"]
    check("V-ACR-GRANT-REFUSES-ESCAPE", refused(esc, "/t") == "SURFACE_ESCAPES_ROOT", "'..' surface refused")
    esc.contract.write_surfaces = ["/etc/passwd"]
    check("V-ACR-GRANT-REFUSES-ABSOLUTE", refused(esc, "/t") == "SURFACE_ESCAPES_ROOT", "absolute surface refused")

    # Writes observed against the granted surface (independent of what the runtime allowed).
    w = R.writes_outside("/home/kobii/t", ho.contract.write_surfaces,
                         ["/home/kobii/t/.claude/settings.json", "/home/kobii/t/src/app.py",
                          "/home/kobii/t/.claude/hooks/x.sh"])
    check("V-ACR-WRITES-OUTSIDE", w == ["/home/kobii/t/src/app.py"], f"{w}")

    total = passes + fails
    print(f"ACR_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
