#!/usr/bin/env python3
"""V-FLOOR-* gates for the S1 floor attribution in wiki/tools/listing_floor_probe.py.

Drives both poles on synthetic transcripts read through the real window reader and classifier: an ON window with
hook context against an OFF window without it attributes the difference to CPP; a missing, zero, contaminated or
unread OFF reading is UNDECIDED with cpp_added None, never 0. No claude session is started.

    python tools/test_listing_floor_probe.py
"""
import contextlib, io, json, os, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "wiki", "tools"))
import listing_floor_probe as lfp  # noqa: E402

passes = fails = 0


def _ok(gate, evidence):
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate, diagnostic):
    global fails
    fails += 1
    print(f"FAIL {gate}: {diagnostic}")


def check(gate, cond, evidence):
    (_ok if cond else _fail)(gate, evidence)


def write_transcript(directory, name, hook_text, usage_total):
    rows = [
        {"type": "attachment", "attachment": {"type": "skill_listing", "isInitial": True,
                                              "content": "- a: alpha\n- b: beta\n"}},
        {"type": "attachment", "attachment": {"type": "instructions", "files": [
            {"path": "/h/.claude/CLAUDE.md", "type": "User", "content": "x" * 500}]}},
    ]
    if hook_text:
        rows.append({"type": "attachment", "attachment": {"type": "hook_additional_context", "hookEvent": "SessionStart",
                                                          "hookName": "SessionStart:startup", "content": [hook_text]}})
    rows.append({"type": "user", "message": {"content": "Reply with the single word OK."}})
    rows.append({"type": "assistant", "message": {"model": "claude-opus-5-5", "content": [], "usage": {
        "input_tokens": usage_total, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}})
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def row(path):
    r = lfp.analyse(path, [])
    r["layers"] = lfp.decompose(path)
    return r


def main():
    with tempfile.TemporaryDirectory() as d:
        on_p = write_transcript(d, "on.jsonl", "h" * 300, 1200)
        off_p = write_transcript(d, "off.jsonl", None, 1000)
        on, off = row(on_p), row(off_p)

        # Arrange/Act done above; Assert per gate.
        check("V-FLOOR-DECOMPOSE-ON", on["layers"] == {"hooks": 300, "memory_global": 500, "skill_listing": 21},
              f"layers={on['layers']}")
        check("V-FLOOR-DECOMPOSE-OFF", "hooks" not in off["layers"] and off["layers"].get("memory_global") == 500,
              f"layers={off['layers']}")
        missing = lfp.decompose(os.path.join(d, "absent.jsonl"))
        check("V-FLOOR-DECOMPOSE-MISSING", missing == {"unmeasured": "no_transcript"}, f"decompose(absent)={missing}")

        a = lfp.attribute(on, off)
        check("V-FLOOR-ATTR-CPP", a["verdict"] == "MEASURED" and a["host_forced"] == 1000 and a["cpp_added"] == 200,
              f"attribution={a}")

        u = lfp.attribute(on, dict(off, startup_tokens=None))
        check("V-FLOOR-OFF-MISSING", u["verdict"] == "UNDECIDED" and u["cpp_added"] is None
              and u["reason"] == "off_unmeasured", f"attribution={u}")
        z = lfp.attribute(on, dict(off, startup_tokens=0))
        check("V-FLOOR-OFF-ZERO", z["verdict"] == "UNDECIDED" and z["cpp_added"] is None, f"attribution={z}")
        n = lfp.attribute(on, None)
        check("V-FLOOR-OFF-ABSENT-ROW", n["verdict"] == "UNDECIDED" and n["cpp_added"] is None, f"attribution={n}")
        w = lfp.attribute(on, dict(off, layers={"unmeasured": "no_transcript"}))
        check("V-FLOOR-OFF-WINDOW-UNMEASURED", w["verdict"] == "UNDECIDED" and w["reason"] == "off_window_unmeasured",
              f"attribution={w}")
        k = lfp.attribute(on, dict(off, layers=on["layers"]))
        check("V-FLOOR-KILL-INEFFECTIVE", k["verdict"] == "UNDECIDED" and k["reason"] == "kill_switch_ineffective",
              f"attribution={k}")
        e = lfp.attribute(dict(on, startup_tokens=900), off)
        check("V-FLOOR-OFF-EXCEEDS", e["verdict"] == "UNDECIDED" and e["reason"] == "off_exceeds_on", f"attribution={e}")

        r = lfp.rank(on["layers"], off["layers"])
        check("V-FLOOR-RANK", [x["class"] for x in r] == ["memory_global", "hooks", "skill_listing"]
              and r[1]["off_chars"] == 0, f"rank={r}")
        r2 = lfp.rank(on["layers"], {"unmeasured": "x"})
        check("V-FLOOR-RANK-OFF-UNKNOWN", all(x["off_chars"] is None for x in r2), f"rank={r2}")

        # --pair without anything switched off is refused before any session is spawned.
        saved = (lfp.CLAUDE, list(sys.argv))
        try:
            lfp.CLAUDE = os.path.join(d, "no-such-claude.exe")
            sys.argv = ["listing_floor_probe.py", "--label", "t", "--prompt", "p", "--pair", "--out",
                        os.path.join(d, "out.jsonl")]
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = lfp.main()
        finally:
            lfp.CLAUDE, sys.argv = saved
        check("V-FLOOR-PAIR-NEEDS-OFF", rc == 2 and not os.path.exists(os.path.join(d, "out.jsonl")),
              f"rc={rc} out={buf.getvalue().strip()[:80]}")

    print(f"FLOOR_PROBE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
