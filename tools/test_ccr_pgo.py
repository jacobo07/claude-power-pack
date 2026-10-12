"""V-CCRPGO-*: Work-Class model, held-out forecast, step anomaly, pre-launch contract (both poles each)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_pgo as pg  # noqa: E402

passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def stream(path: Path, steps: list[int], floor: int = 19000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ctx, lines = floor, []
    for i, s in enumerate(steps + [0]):
        lines.append({"type": "assistant", "message": {"id": f"m{i}", "usage": {"input_tokens": 0, "cache_read_input_tokens": ctx},
                      "content": [{"type": "tool_use", "id": f"t{i}", "input": {}}]}})
        lines.append({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": "x" * (2 * s)}]}})
        ctx += s
    path.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")
    return path


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    normal = [stream(tmp / f"a{i}" / "w.jsonl", [900 + 40 * ((i + j) % 9) for j in range(24)]) for i in range(5)]
    dump = stream(tmp / "dump" / "w.jsonl", [900, 11213] + [950] * 22)
    pgo = pg.build("cls", normal)

    hits = pg.anomaly(pgo, dump)
    if hits and hits[0]["after_call"] == 2 and hits[0]["cost_if_rides"] > 200000:
        _ok("V-CCRPGO-ANOMALY-CATCHES-DUMP", json.dumps(hits[0]))
    else:
        _fail("V-CCRPGO-ANOMALY-CATCHES-DUMP", json.dumps(hits))
    clean = pg.anomaly(pgo, normal[0])
    if len(clean) <= 1:  # a P95 bound lets ~5 % of normal steps through by construction; 24 steps -> at most ~1
        _ok("V-CCRPGO-ANOMALY-QUIET-ON-NORMAL", f"{len(clean)} flagged")
    else:
        _fail("V-CCRPGO-ANOMALY-QUIET-ON-NORMAL", json.dumps(clean))

    ho = pg.heldout("cls", normal[:4], normal[4:])
    if ho["abs_err_known_len_p50"] is not None and ho["abs_err_known_len_p50"] < 0.25:
        _ok("V-CCRPGO-HELDOUT-ERROR-BOUNDED", f"known-len err {ho['abs_err_known_len_p50']}")
    else:
        _fail("V-CCRPGO-HELDOUT-ERROR-BOUNDED", json.dumps(ho["rows"]))

    img = tmp / "image.md"
    img.write_text("obligation text " * 50, encoding="utf-8")
    c0 = pg.contract(None, "do x", img, None)
    if c0["verdict"] == "ADMIT_UNFORECAST" and c0["forecast"] is None:
        _ok("V-CCRPGO-NO-MODEL-IS-UNFORECAST", c0["reasons"][0])
    else:
        _fail("V-CCRPGO-NO-MODEL-IS-UNFORECAST", json.dumps(c0))
    c1 = pg.contract(pgo, "do x", img, None)
    if c1["verdict"] == "ADMIT":
        _ok("V-CCRPGO-CONTRACT-ADMITS-NORMAL", json.dumps(c1["forecast"]))
    else:
        _fail("V-CCRPGO-CONTRACT-ADMITS-NORMAL", json.dumps(c1))
    c2 = pg.contract(pgo, "do x", img, cap=c1["forecast"]["p80"] / 2)
    if c2["verdict"] == "SPLIT":
        _ok("V-CCRPGO-CONTRACT-SPLITS-OVER-CAP", c2["reasons"][-1])
    else:
        _fail("V-CCRPGO-CONTRACT-SPLITS-OVER-CAP", json.dumps(c2))
    big = tmp / "big.md"
    big.write_text("x" * int(pgo["floor"]["p80"] * 3), encoding="utf-8")
    c3 = pg.contract(pgo, "do x", big, None)
    if c3["verdict"] == "DEFLATE":
        _ok("V-CCRPGO-CONTRACT-DEFLATES-FAT-IMAGE", c3["reasons"][0])
    else:
        _fail("V-CCRPGO-CONTRACT-DEFLATES-FAT-IMAGE", json.dumps(c3))

    print(f"CCRPGO_PASS={passes}/{passes + fails}  threshold=7/7")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
