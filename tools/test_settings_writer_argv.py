"""Producer-boundary drills for CPP's own settings.json writer (fix_conhost_hook_leak.py).

Incident 2026-09-16: an ad-hoc rewrite kept each hook's script path and dropped every
argument after it, including the six dispatcher --event= routing identities; every Power
Pack hook went dark for ~42 h. The consumer-side gate (test_hook_registration_integrity.py)
catches the result. These drills hold the PRODUCER to the round-trip contract:
read -> transform -> write -> read must preserve every hook's argv except the intended unwrap,
and a write must not clobber a concurrent writer (Orca X rewrites the file at launch).
Fixtures are built from the REAL settings schema (a deep copy of the live file), never
the live file itself.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fix_conhost_hook_leak as fx  # noqa: E402

passes = fails = 0


def _ok(g: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {g}: {ev}")


def _fail(g: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {g}: {ev}")


def fixture() -> dict:
    live = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
    d = copy.deepcopy(live)
    # Inject one Orca-shaped conhost wrapper so the writer has real work to do.
    d["hooks"].setdefault("TeammateIdle", []).append({"hooks": [{
        "type": "command", "command": r"C:\WINDOWS\System32\conhost.exe",
        "args": ["--headless", r"C:\WINDOWS\System32\cmd.exe", "/d", "/c", r"%USERPROFILE%\.orca\agent-hooks\claude-hook.cmd"],
        "timeout": 10}]})
    return d


def dispatcher_events(d: dict) -> list[str]:
    return sorted(a for groups in d["hooks"].values() for g in groups for h in g["hooks"]
                  for a in (h.get("args") or []) if a.startswith("--event="))


def main() -> int:
    base = fixture()
    ev_before = dispatcher_events(base)
    if len(ev_before) < 6:
        print(f"HARNESS-FAILED: live settings carry {len(ev_before)} --event= args; expected >= 6")
        return 2

    # GREEN: the real unwrap preserves every other argv and all routing identities.
    d = copy.deepcopy(base)
    targets = {(e, m, h) for e, m, h, _ in fx.scan(d)}
    before = copy.deepcopy(d)
    fx.repair(d)
    v = fx.argv_violations(before, d, targets)
    (_ok if not v and dispatcher_events(d) == ev_before and len(targets) >= 1 else _fail)(
        "V-WRITER-UNWRAP-PRESERVES-ARGV", f"targets={len(targets)} violations={v[:2]} events_kept={dispatcher_events(d) == ev_before}")

    # RED: the incident's lossy transform (keep only the .js path) must be refused.
    d = copy.deepcopy(base)
    before = copy.deepcopy(d)
    for groups in d["hooks"].values():
        for g in groups:
            for h in g["hooks"]:
                a = h.get("args") or []
                js = next((x for x in a if str(x).endswith(".js")), None)
                if js:
                    h["args"] = [js]
    v = fx.argv_violations(before, d, set())
    hit = [x for x in v if "--event=" in x]
    (_ok if len(hit) >= 6 else _fail)("V-WRITER-INCIDENT-TRANSFORM-REFUSED", f"{len(hit)} routing identities flagged")

    # RED: an unwrap that drops the wrapped tail must be refused.
    d = copy.deepcopy(base)
    targets = {(e, m, h) for e, m, h, _ in fx.scan(d)}
    before = copy.deepcopy(d)
    orig = fx._unwrap
    fx._unwrap = lambda e: {**{k: v for k, v in e.items() if k != "args"}, "command": e["args"][1]}
    try:
        fx.repair(d)
    finally:
        fx._unwrap = orig
    v = fx.argv_violations(before, d, targets)
    (_ok if v else _fail)("V-WRITER-LOSSY-UNWRAP-REFUSED", v[0] if v else "no violation reported")

    # CAS: a concurrent writer between read and write -> not written, other writer's bytes kept.
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "settings.json"
        p.write_text(json.dumps(base, indent=2), encoding="utf-8")
        concurrent = json.dumps({"hooks": {}, "written_by": "concurrent-writer"})
        orig_repair = fx.repair

        def racing_repair(s: dict) -> int:
            n = orig_repair(s)
            p.write_text(concurrent, encoding="utf-8")
            return n
        fx.repair = racing_repair
        try:
            rc = fx.main(["--settings", str(p), "--apply"])
        finally:
            fx.repair = orig_repair
        kept = p.read_text(encoding="utf-8") == concurrent
        leftovers = [x.name for x in Path(td).iterdir() if ".tmp-conhost-" in x.name]
        (_ok if rc == 4 and kept and not leftovers else _fail)(
            "V-WRITER-CAS-CONCURRENT", f"rc={rc} concurrent_bytes_kept={kept} tmp_leftovers={leftovers}")

    # CONTROL: the same apply with no race writes and keeps every routing identity.
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "settings.json"
        p.write_text(json.dumps(base, indent=2), encoding="utf-8")
        rc = fx.main(["--settings", str(p), "--apply"])
        after = json.loads(p.read_text(encoding="utf-8"))
        (_ok if rc == 0 and not fx.scan(after) and dispatcher_events(after) == ev_before else _fail)(
            "V-WRITER-APPLY-CONTROL", f"rc={rc} wrappers_left={len(fx.scan(after))} events_kept={dispatcher_events(after) == ev_before}")

    print(f"WRITER_ARGV_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
