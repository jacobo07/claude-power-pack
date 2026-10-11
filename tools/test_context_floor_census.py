#!/usr/bin/env python3
"""V-CENSUS gates for tools/context_floor_census.py (what the call-1 floor and each call's growth are made of).

Synthetic fixture built here; one read-only positive control on the real ctx-rent-a2 baseline
transcript reports SKIP (never PASS) when that file is absent.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
passes = fails = skips = 0


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def att(atype, rendered_chars=None, side=False, **extra):
    row = {"type": "attachment", "isSidechain": side, "attachment": {"type": atype, **extra}}
    if rendered_chars is not None:
        row["rendered"] = [{"content": "r" * rendered_chars}]
    return row


def user(content, meta=False, side=False):
    return {"type": "user", "isSidechain": side, "isMeta": meta,
            "message": {"role": "user", "content": content}}


def asst(mid, blocks, cc, cr, out, inp=0, side=False):
    usage = {"input_tokens": inp, "cache_creation_input_tokens": cc,
             "cache_read_input_tokens": cr, "output_tokens": out}
    return {"type": "assistant", "isSidechain": side,
            "message": {"id": mid, "role": "assistant", "content": blocks, "usage": usage}}


def tool_result(tid, chars):
    return user([{"type": "tool_result", "tool_use_id": tid, "content": "x" * chars}])


FILE_A = "C:\\Users\\U\\.claude\\CLAUDE.md"
FILE_B = "C:\\Users\\U\\.claude\\rules\\b.md"

FIXTURE = [
    {"type": "mode", "mode": "normal"},
    att("hook_cancelled", hookName="SessionStart:clear", hookEvent="SessionStart", timedOut=True, timeoutMs=15000),
    att("hook_additional_context", 400, hookName="SessionStart", hookEvent="SessionStart", content=["c"]),
    user("p" * 300),
    att("skill_listing", 1000),
    att("agent_listing_delta", 600),
    att("credential_org", None, organizationUuid="u"),          # not rendered: never sent, never counted
    {"type": "attachment", "isSidechain": False, "rendered": [{"content": "w" * 3100}],
     "attachment": {"type": "instructions", "files": [
         {"path": FILE_A, "type": "User", "content": "a" * 2000},
         {"path": FILE_B, "type": "User", "content": "b" * 1000}]}},
    att("prompt_snapshot", None, systemPrompt=["s" * 500, "s" * 200]),
    att("skill_listing", 9999, side=True),                       # a subagent's context, not this one's
    # call 1 spans two lines (thinking + tool_use); total 3,000
    asst("m1", [{"type": "thinking", "thinking": ""}], 2000, 1000, 50),
    asst("m1", [{"type": "tool_use", "id": "t1", "name": "Read", "input": {}}], 2000, 1000, 50),
    tool_result("t1", 3500),
    # call 2: 3,000 + 50 output + 1,000 Read result = 4,050
    asst("m2", [{"type": "tool_use", "id": "t2", "name": "Bash", "input": {}}], 1050, 3000, 20),
    tool_result("t2", 1400),
    tool_result("t2", 1400),                                     # duplicate row: counted once
    att("prompt_snapshot", None, systemPrompt=["s" * 5000]),    # re-record, not growth: never charged
    att("total_tokens_reminder", 100),
    # call 3: 4,050 + 20 output + 400 new = 4,470
    asst("m3", [{"type": "text", "text": "ok"}], 420, 4050, 10),
    # call 4 after a compaction: the total FALLS; never charged to anyone
    asst("m4", [{"type": "text", "text": "ok"}], 100, 900, 5),
]


def write(td, name, rows):
    p = Path(td) / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def main() -> int:
    global skips
    cfc = _load("context_floor_census")
    with tempfile.TemporaryDirectory() as td:
        r = cfc.census(write(td, "s.jsonl", FIXTURE), chars_per_token=4.0)
        fl, hi = r["floor"], r["history"]
        src = {s["source"]: s for s in fl["sources"]}

        check("V-CENSUS-CALLS-DEDUP", r["calls"] == 4, f"calls={r['calls']}")
        check("V-CENSUS-FLOOR-MEASURED", fl["measured_tokens"] == 3000, f"measured={fl['measured_tokens']}")
        check("V-CENSUS-FLOOR-FILES",
              src.get(f"instructions:{FILE_A}", {}).get("chars") == 2000
              and src.get(f"instructions:{FILE_B}", {}).get("chars") == 1000
              and src.get("instructions:(wrapper)", {}).get("chars") == 100,
              "per-file chars + wrapper remainder")
        check("V-CENSUS-FLOOR-HOST-ITEMS",
              src.get("attachment:skill_listing", {}).get("chars") == 1000
              and src.get("attachment:agent_listing_delta", {}).get("chars") == 600
              and src.get("hook:SessionStart:SessionStart", {}).get("chars") == 400
              and src.get("user_prompt", {}).get("chars") == 300
              and src.get("system_prompt(host)", {}).get("chars") == 700,
              "listings, hook injection, prompt, system prompt")
        check("V-CENSUS-SIDECHAIN-SKIP", src["attachment:skill_listing"]["chars"] == 1000,
              "the 9,999-char sidechain listing was not added")
        check("V-CENSUS-UNRENDERED-SKIP", not any("credential_org" in k for k in src),
              "an attachment with no rendered text is never charged")
        chars = [s["chars"] for s in fl["sources"]]
        check("V-CENSUS-RANKED", chars == sorted(chars, reverse=True), f"order={chars}")
        total_chars = 2000 + 1000 + 100 + 1000 + 600 + 400 + 300 + 700
        check("V-CENSUS-RESIDUAL",
              fl["attributed_chars"] == total_chars
              and fl["estimated_tokens"] == round(total_chars / 4.0)
              and fl["unattributed_tokens"] == 3000 - round(total_chars / 4.0),
              f"attributed={fl['attributed_chars']} est={fl['estimated_tokens']} rest={fl['unattributed_tokens']}")
        # call 1: cache_read 1,000 = host prefix; 2,000 session-specific; system prompt excluded from it
        check("V-CENSUS-PREFIX-SPLIT",
              fl["host_prefix_tokens"] == 1000 and fl["session_tokens"] == 2000
              and fl["session_estimated_tokens"] == round((total_chars - 700) / 4.0)
              and fl["session_unattributed_tokens"] == 2000 - round((total_chars - 700) / 4.0),
              f"prefix={fl['host_prefix_tokens']} session={fl['session_tokens']} "
              f"est={fl['session_estimated_tokens']} rest={fl['session_unattributed_tokens']}")
        check("V-CENSUS-HOOK-TIMEOUTS",
              fl["hooks_timed_out"] == [{"hook": "SessionStart:clear", "event": "SessionStart", "timeout_ms": 15000}],
              f"{fl['hooks_timed_out']}")

        prod = hi["by_producer"]
        check("V-CENSUS-HISTORY-SINGLE", prod.get("tool_result:Read") == 1000,
              f"Read charged {prod.get('tool_result:Read')} (delta 1,050 minus 50 output)")
        check("V-CENSUS-HISTORY-SPLIT",
              prod.get("tool_result:Bash") == round(400 * 1400 / 1500)
              and prod.get("attachment:total_tokens_reminder") == round(400 * 100 / 1500)
              and "system_prompt(host)" not in prod,
              f"Bash={prod.get('tool_result:Bash')} reminder={prod.get('attachment:total_tokens_reminder')}")
        check("V-CENSUS-HISTORY-OUTPUT", hi["assistant_output_tokens"] == 50 + 20 + 10,
              f"output carried={hi['assistant_output_tokens']}")
        check("V-CENSUS-HISTORY-RESET",
              hi["resets"] == [{"call": 4, "delta": 1000 - 4470}] and "m4" not in json.dumps(prod),
              f"resets={hi['resets']}")
        check("V-CENSUS-CALIBRATION",
              # step 1: Read alone 3,500/1,000; step 2: Bash is 93 % of 1,500 chars -> 1,500/400
              r["calibration"]["samples"] == 2
              and abs(r["calibration"]["median_chars_per_token"] - (3.5 + 3.75) / 2) < 0.01
              and r["chars_per_token"]["value"] == 4.0 and r["chars_per_token"]["source"] == "explicit",
              f"{r['calibration']} used={r['chars_per_token']}")

        check("V-CENSUS-DENSE-BOUND-ABSENT", fl["session_unattributed_at_calibrated"] is None,
              "2 calibration samples < minimum: no dense bound is invented")
        # Default ratio: the history-calibrated median never sizes floor items.
        r2 = cfc.census(write(td, "s2.jsonl", FIXTURE))
        check("V-CENSUS-RATIO-DEFAULT",
              r2["chars_per_token"] == {"value": cfc.DEFAULT_CHARS_PER_TOKEN, "source": "default"},
              f"{r2['chars_per_token']}")

        # Absent is not zero: a transcript with no model call has no measured floor.
        r3 = cfc.census(write(td, "none.jsonl", FIXTURE[:9]))
        check("V-CENSUS-NO-CALL", r3["floor"]["measured_tokens"] is None and r3["verdict"] == "NO_CALL"
              and r3["floor"]["unattributed_tokens"] is None,
              f"verdict={r3['verdict']} measured={r3['floor']['measured_tokens']}")

        md = cfc.render_markdown([r], top=5)
        check("V-CENSUS-MARKDOWN", "| source |" in md and "unattributed" in md and md.count("\n| ") >= 5,
              "ranked table rendered")

    # Positive control on the real baseline (read-only).
    real = Path.home() / ".claude/projects/C--Users-User--claude-skills-claude-power-pack" \
        / "47f3da08-ebdf-43f0-b825-cb990a69ae5c.jsonl"
    if real.is_file():
        rr = cfc.census(real)
        rsrc = {s["source"] for s in rr["floor"]["sources"]}
        check("V-CENSUS-REAL-FLOOR", rr["floor"]["measured_tokens"] == 122_093,
              f"measured={rr['floor']['measured_tokens']} (plan section 1: 122,093)")
        check("V-CENSUS-REAL-SOURCES",
              "attachment:skill_listing" in rsrc and "attachment:agent_listing_delta" in rsrc
              and sum(1 for s in rsrc if s.startswith("instructions:")) >= 29,
              f"{len(rsrc)} sources")
        hi = rr["history"]
        growth = hi["last_call_tokens"] - rr["floor"]["measured_tokens"]
        charged = sum(hi["by_producer"].values()) + hi["assistant_output_tokens"]
        check("V-CENSUS-REAL-CONSERVATION",
              not hi["resets"] and abs(growth - charged) <= len(hi["by_producer"]),
              f"growth={growth:,} charged+output={charged:,} (no reset; rounding only)")
        check("V-CENSUS-REAL-DENSE-BOUND",
              rr["calibration"]["samples"] >= 3 and rr["floor"]["session_unattributed_at_calibrated"] is not None
              and rr["chars_per_token"]["source"] == "default",
              f"samples={rr['calibration']['samples']} bound={rr['floor']['session_unattributed_at_calibrated']}")
    else:
        skips += 1
        print("  [SKIP] V-CENSUS-REAL-*: baseline transcript absent")

    print(f"CENSUS_PASS={passes}/{passes + fails}  skips={skips}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
