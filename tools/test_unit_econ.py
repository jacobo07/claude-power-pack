"""V-UECON-* -- unit_econ counts like mission_spend and reports amplification from a forecast."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import unit_econ as ue  # noqa: E402

passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, why: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {why}")


def row(mid, i, w, r, o, ts, tool=False):
    content = [{"type": "tool_use", "id": f"t{mid}", "name": "Read", "input": {}}] if tool else [{"type": "text", "text": "x"}]
    return {"type": "assistant", "timestamp": ts, "uuid": f"u-{mid}-{ts}",
            "message": {"id": mid, "model": "m", "content": content,
                        "usage": {"input_tokens": i, "cache_creation_input_tokens": w,
                                  "cache_read_input_tokens": r, "output_tokens": o}}}


def main() -> int:
    rows = [row("m1", 10, 1000, 0, 50, "2026-10-25T10:00:00Z", True),     # 1060
            row("m1", 10, 1000, 0, 50, "2026-10-25T10:00:01Z"),            # duplicate id: streamed block
            row("m2", 5, 0, 1060, 100, "2026-10-25T10:01:00Z", True),      # 1165
            row("m3", 5, 0, 1160, 300, "2026-10-25T10:02:00Z", True),      # 1465
            row("m4", 5, 0, 1460, 40, "2026-10-25T10:03:00Z"),             # 1505
            row("m5", 5, 0, 1500, 60, "2026-10-25T10:04:00Z")]             # 1565
    rows.append({"type": "assistant", "timestamp": "2026-10-25T10:05:00Z",
                 "message": {"id": "syn", "model": "<synthetic>", "content": [],
                             "usage": {"input_tokens": 999999, "output_tokens": 0}}})
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "t.jsonl"
        t.write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n", encoding="utf-8")
        vj = Path(d) / "v.json"
        vj.write_text(json.dumps({"commits": 2}), encoding="utf-8")
        rec = ue.build(t, None, "g", "implementation", "U1", 3000, {"commits": 2})
        want = 1060 + 1165 + 1465 + 1505 + 1565

        if rec["calls"] == 5 and rec["processed_tokens"] == want:
            _ok("V-UECON-DEDUPE", f"duplicate message id and synthetic row not counted: {rec['processed_tokens']}")
        else:
            _fail("V-UECON-DEDUPE", f"calls={rec['calls']} tokens={rec['processed_tokens']} want={want}")

        if rec["count_agrees_with_mission_spend"]:
            _ok("V-UECON-REFERENCE", "per-call sum equals mission_spend.session_tokens")
        else:
            _fail("V-UECON-REFERENCE", f"{rec['processed_tokens']} vs {rec['mission_spend_tokens']}")

        if rec["first_call_cws"] == 1000 and rec["first_call_cache_read"] == 0:
            _ok("V-UECON-FIRST-CALL", "first call cache write 1000, cache read 0")
        else:
            _fail("V-UECON-FIRST-CALL", f"cws={rec['first_call_cws']} read={rec['first_call_cache_read']}")

        if (rec["p50_per_call"], rec["p80_per_call"], rec["peak_per_call"], rec["avg_per_call"]) == (1465, 1505, 1565, want // 5):
            _ok("V-UECON-DISTRIBUTION", "p50/p80/peak/avg per call match hand-computed values")
        else:
            _fail("V-UECON-DISTRIBUTION", f"{rec['p50_per_call']}/{rec['p80_per_call']}/{rec['peak_per_call']}/{rec['avg_per_call']}")

        if rec["amplification"] == round(want / 3000, 3) and rec["value_deposit"] == {"commits": 2}:
            _ok("V-UECON-AMPLIFICATION", f"actual/forecast = {rec['amplification']}, value passed through")
        else:
            _fail("V-UECON-AMPLIFICATION", f"{rec['amplification']} {rec['value_deposit']}")

        none = ue.build(t, None, "g", "c", "u", None, None)
        if none["amplification"] is None and none["measurement_tax_s"] >= 0:
            _ok("V-UECON-NO-FORECAST", "no forecast -> amplification null (absent, not zero); tax reported")
        else:
            _fail("V-UECON-NO-FORECAST", str(none["amplification"]))

        late = ue.build(t, "2026-10-25T10:02:30Z", "g", "c", "u", None, None)
        if late["calls"] == 2 and late["processed_tokens"] == 1505 + 1565:
            _ok("V-UECON-SINCE", "--since drops earlier calls")
        else:
            _fail("V-UECON-SINCE", f"calls={late['calls']} tokens={late['processed_tokens']}")

        out = Path(d) / "r.json"
        r = subprocess.run([sys.executable, str(HERE / "unit_econ.py"), "--transcript", str(t), "--goal", "g",
                            "--work-class", "c", "--unit", "u", "--forecast", "3000", "--value-json", str(vj),
                            "--write", str(out)], capture_output=True, text=True, encoding="utf-8")
        got = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
        if r.returncode == 0 and got.get("processed_tokens") == want and got.get("value_deposit") == {"commits": 2}:
            _ok("V-UECON-CLI-WRITE", "CLI prints and writes the receipt")
        else:
            _fail("V-UECON-CLI-WRITE", f"rc={r.returncode} {r.stderr[:160]}")
    print(f"UECON_PASS={passes}/{passes + fails}  threshold=8/8")
    return 0 if fails == 0 and passes == 8 else 1


if __name__ == "__main__":
    sys.exit(main())
