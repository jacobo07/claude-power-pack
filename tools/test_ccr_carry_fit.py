"""V-CCRFIT-*: the carry fit recovers known rates and reports what it cannot explain as residual."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_carry_fit as cf  # noqa: E402

passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def stream(path: Path, steps: list[tuple[int, int, int]], floor: int = 20000) -> None:
    """steps: (tool_result chars, thinking signature chars, hidden tokens no row shows)."""
    ctx, lines = floor, []
    for i, (tr, sig, hidden) in enumerate(steps + [(0, 0, 0)]):
        inp = {"command": "y" * (60 + 53 * (i % 5))}
        lines.append({"type": "assistant", "message": {"id": f"m{i}", "usage": {"input_tokens": 0, "cache_read_input_tokens": ctx},
                      "content": [{"type": "thinking", "thinking": "", "signature": "s" * sig},
                                  {"type": "tool_use", "id": f"t{i}", "input": inp}]}})
        lines.append({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": "x" * tr}]}})
        ctx += round(0.5 * tr + 0.3 * sig + 0.445 * len(json.dumps(inp))) + hidden
    path.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    # thinking mass as real workers show it: as large as the tool text and uncorrelated with it (a3: 40.8 % vs 33.4 %)
    rows = [(1000 + 37 * i, (i * 733) % 3000, 0) for i in range(30)]
    clean = tmp / "clean" / "w.jsonl"
    clean.parent.mkdir()
    stream(clean, rows)
    r = cf.fit({"clean": cf.steps_of(clean)})
    rates = r["rates"]
    if abs(rates["tool_result"] - 0.5) < 0.02 and abs(rates["thinking_sig"] - 0.3) < 0.02:
        _ok("V-CCRFIT-RECOVERS-RATES", f"tool_result {rates['tool_result']} thinking_sig {rates['thinking_sig']}")
    else:
        _fail("V-CCRFIT-RECOVERS-RATES", str(rates))
    a = r["attempts"]["clean"]
    if abs(a["residual"]) < 0.02 * a["carry"]:
        _ok("V-CCRFIT-CLEAN-RESIDUAL-SMALL", f"residual {a['residual']} of carry {a['carry']}")
    else:
        _fail("V-CCRFIT-CLEAN-RESIDUAL-SMALL", json.dumps(a))

    # the other pole: tokens no row shows (e.g. an unknown kind) must surface as residual, not hide in a kind
    hid = tmp / "hidden" / "w.jsonl"
    hid.parent.mkdir()
    stream(hid, [(tr, sig, 3000 if i % 2 else 0) for i, (tr, sig, _) in enumerate(rows)])
    r2 = cf.fit({"hidden": cf.steps_of(hid)})
    a2 = r2["attempts"]["hidden"]
    # constant-per-step hidden mass is unidentifiable by the fit; it must be caught as an implausible rate or residual
    if r2["verdict"] == "IMPLAUSIBLE" or a2["residual"] > 0.1 * a2["carry"]:
        _ok("V-CCRFIT-HIDDEN-IS-NOT-SILENT", f"verdict {r2['verdict']} {r2['implausible']} residual {a2['residual']}")
    else:
        _fail("V-CCRFIT-HIDDEN-IS-NOT-SILENT", json.dumps(r2))
    if r["verdict"] == "PLAUSIBLE":
        _ok("V-CCRFIT-CLEAN-IS-PLAUSIBLE", str(r["rates"]))
    else:
        _fail("V-CCRFIT-CLEAN-IS-PLAUSIBLE", json.dumps(r))

    # ablation: drop a kind that carries real mass and its mass must reappear as residual
    r4 = cf.fit({"clean": cf.steps_of(clean)}, drop=("thinking_sig",))
    a4 = r4["attempts"]["clean"]
    if a4["residual"] > 0.05 * a4["carry"] or r4["verdict"] == "IMPLAUSIBLE":
        _ok("V-CCRFIT-ABLATION-MOVES-MASS", f"residual {a4['residual']} verdict {r4['verdict']}")
    else:
        _fail("V-CCRFIT-ABLATION-MOVES-MASS", json.dumps(r4))

    one = tmp / "one" / "w.jsonl"
    one.parent.mkdir()
    one.write_text(json.dumps({"type": "assistant", "message": {"id": "m0", "usage": {"input_tokens": 5}, "content": []}}), encoding="utf-8")
    r3 = cf.fit({"one": cf.steps_of(one)})
    if "error" in r3:
        _ok("V-CCRFIT-NO-STEPS-IS-AN-ERROR", r3["error"])
    else:
        _fail("V-CCRFIT-NO-STEPS-IS-AN-ERROR", json.dumps(r3))

    print(f"CCRFIT_PASS={passes}/{passes + fails}  threshold=6/6")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
