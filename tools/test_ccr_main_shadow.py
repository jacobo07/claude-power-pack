"""V-CCRMAINSHADOW-*: only interactive non-unit sessions count, uses after a dropped listing are risk, sidechains are not."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_main_shadow as ms  # noqa: E402

passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def check(gate: str, cond: bool, ev: str) -> None:
    (_ok if cond else _fail)(gate, ev)


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _asst(mid: str, blocks: list[dict], sidechain: bool = False) -> dict:
    return {"t": "assistant", "mid": mid, "sidechain": sidechain, "usage": {"input_tokens": 10, "cache_read_input_tokens": 90},
            "blocks": blocks}


def build(pack: Path) -> None:
    att = [{"ev": "attach", "agent": None, "type": "skill_listing", "bytes": 30000},
           {"ev": "attach", "agent": None, "type": "agent_listing_delta", "bytes": 20000},
           {"ev": "attach", "agent": "Explore", "type": "skill_listing", "bytes": 30000},  # subagent: not main
           {"ev": "attach", "agent": None, "type": "instructions", "bytes": 50000}]
    _write(pack / "receipts/r1/s1.jsonl", [{"ev": "start", "interactive": True, "unit": None}, *att])
    _write(pack / "receipts/r1/s2.jsonl", [{"ev": "start", "interactive": False, "unit": None}, *att])  # headless
    _write(pack / "receipts/r1/s3.jsonl", [{"ev": "start", "interactive": True, "unit": "bounded-code-worker"}, *att])
    _write(pack / "sessions/s1.jsonl", [
        _asst("m0", [{"k": "tool_use", "name": "Skill", "skill": "early"}]),  # before any listing: not counted
        {"t": "attachment", "att": "skill_listing", "sidechain": False},
        _asst("m1", [{"k": "tool_use", "name": "Skill", "skill": "gsd-plan-phase"}, {"k": "tool_use", "name": "Read"}]),
        _asst("m1", [{"k": "tool_use", "name": "Agent", "subagent_type": "gsd-executor"}]),  # same call, second row
        _asst("m2", [{"k": "tool_use", "name": "mcp__ctx__resolve"}]),
        _asst("x1", [{"k": "tool_use", "name": "Skill", "skill": "sub"}], sidechain=True),  # subagent row
    ])


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        build(pack)
        res = ms.shadow(pack)
        t = res["table"]
        check("V-CCRMAINSHADOW-SCOPE", t["sessions"] == 1 and res["sessions"][0]["sid"] == "s1",
              f"sessions={[s['sid'] for s in res['sessions']]} (headless and unit sessions excluded)")
        sk = t["types"]["skill_listing"]
        check("V-CCRMAINSHADOW-MAINONLY", sk["bytes"] == 30000 and sk["events"] == 1, f"skill_listing={sk}")
        cap = res["sessions"][0]["cap"]
        check("V-CCRMAINSHADOW-AFTER", cap["uses"]["skill"] == {"gsd-plan-phase": 1},
              f"skill uses={cap['uses']['skill']} (pre-listing and sidechain uses excluded)")
        check("V-CCRMAINSHADOW-KINDS", cap["uses"]["agent"] == {"gsd-executor": 1} and cap["uses"]["mcp"] == {"mcp__ctx__resolve": 1},
              f"agent={cap['uses']['agent']} mcp={cap['uses']['mcp']}")
        check("V-CCRMAINSHADOW-CALLS", cap["calls"] == 3 and cap["processed"] == 300, f"calls={cap['calls']} processed={cap['processed']}")
        check("V-CCRMAINSHADOW-RISK", t["risk_sessions_any"] == 1 and t["risk_uses"] == {"skill": 1, "agent": 1, "mcp": 1},
              f"risk={t['risk_uses']} any={t['risk_sessions_any']}")
        ins = t["types"]["instructions"]
        check("V-CCRMAINSHADOW-REPLACE", ins["replace_saves_min"] == 50000 - ms.KERNEL_CHARS and ins["lean_saves"] is None,
              f"instructions={ins}")
        exp = round(30000 * (1 - ms.LEAN_RATIO["skill_listing"]) * 3 * ms.TOK_PER_CHAR)
        check("V-CCRMAINSHADOW-LEANTOK", sk["lean_processed_tok"] == exp, f"lean tok={sk['lean_processed_tok']} expected={exp}")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        empty = ms.canary_report(root)
        check("V-CCRMAINSHADOW-PENDING", empty["state"] == "CANARY_PENDING" and empty["canary"] == [], f"state={empty['state']}")
        for i, ctx in enumerate((40000, 42000, 44000)):
            _write(root / f"r/b{i}.jsonl", [{"ev": "start", "interactive": True, "unit": None, "compatible": True},
                                            {"ev": "call", "agent": None, "call": 1, "ctx": ctx}])
        _write(root / "r/c1.jsonl", [
            {"ev": "start", "interactive": True, "unit": None, "compatible": True, "canary": "enforce", "releaseId": "0.1.0-x"},
            {"ev": "attach", "agent": None, "canary": "enforce", "type": "skill_listing", "bytes": 30000, "out": 8000, "lean": 8000, "applied": True},
            {"ev": "attach", "agent": None, "type": "environment", "bytes": 300, "applied": False},  # not a canary row
            {"ev": "fault", "kind": "skills"}, {"ev": "spawn", "agentType": "gsd-executor"},
            {"ev": "call", "agent": None, "call": 1, "ctx": 36000}])
        rep = ms.canary_report(root)
        c = rep["canary"][0] if rep["canary"] else {}
        check("V-CCRMAINSHADOW-CANARY", rep["state"] == "CANARY_RAN" and rep["baseline_n"] == 3 and c.get("withheld") == 22000,
              f"state={rep['state']} base={rep['baseline_n']} withheld={c.get('withheld')}")
        check("V-CCRMAINSHADOW-CANARY-READ", c.get("predicted_first_call_tok") == 5500 and c.get("measured_first_call_tok") == 6000
              and c.get("faults") == {"skills": 1} and c.get("spawns") == {"gsd-executor": 1},
              f"pred={c.get('predicted_first_call_tok')} meas={c.get('measured_first_call_tok')} faults={c.get('faults')}")
    print(f"CCR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
