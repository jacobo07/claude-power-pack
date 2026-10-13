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

    by_class(tmp)
    print(f"CCRPGO_PASS={passes}/{passes + fails}  threshold=16/16")
    return 0 if fails == 0 else 1


def proj(path: Path, ctxs: list[int], out: int = 10, repeat: int = 2, images: int = 0) -> Path:
    """A usage projection: each message id streamed over `repeat` lines, output growing to `out`."""
    lines = [{"t": "user", "ts": "2026-10-01T00:00:00Z", "blocks": [{"k": "tool_result", "bytes": 9, "images": 1}]}
             for _ in range(images)]
    for i, c in enumerate(ctxs):
        for j in range(repeat):
            lines.append({"t": "assistant", "ts": "2026-10-01T00:00:01Z", "model": "claude-sonnet-5-5", "mid": f"m{i}",
                          "usage": {"input_tokens": 0, "cache_read_input_tokens": c, "cache_creation_input_tokens": 0,
                                    "output_tokens": out if j == repeat - 1 else 1}, "blocks": [{"k": "tool_use"}]})
        lines.append({"t": "user", "blocks": [{"k": "tool_result", "bytes": 9}]})
    path.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")
    return path


def row(i: int, cls: str, processed: float) -> dict:
    return {"src": "mission", "id": f"m{i:03d}", "sid": f"s{i:03d}", "t": float(i), "cls": cls, "processed": processed,
            "weighted": processed / 5, "calls": 10, "floor": 20000, "slope": 1000.0, "image_share": 0.0}


def by_class(tmp: Path) -> None:
    f = pg.projection_facts(proj(tmp / "p.jsonl", [1000, 3000, 6000], out=10, repeat=3, images=1))
    if f["calls"] == 3 and f["processed"] == 10000 + 30 and f["floor"] == 1000 and f["slope"] == 2500 and f["image_share"] > 0:
        _ok("V-CCRPGO-A3-PROJECTION-DEDUP-BY-MID", json.dumps({k: f[k] for k in ("calls", "processed", "weighted", "image_share")}))
    else:
        _fail("V-CCRPGO-A3-PROJECTION-DEDUP-BY-MID", json.dumps(f))

    cases = {"# WU-V1 canary: predecessor lookup": "lookup", "# X -- Knowledge promotion and handoff": "long-textual",
             "# Y -- add a gate\nwrite tests in test_y.py": "bounded-code", "# Z -- take screenshot.png of the page": "multimodal",
             "# W -- Autonomy Convergence unit S8": "generic"}
    got = {t: pg.classify(t)[0] for t in cases}
    if got == cases and pg.classify(list(cases)[0]) == pg.classify(list(cases)[0]):
        _ok("V-CCRPGO-A3-CLASSIFIER-DETERMINISTIC", json.dumps(list(got.values())))
    else:
        _fail("V-CCRPGO-A3-CLASSIFIER-DETERMINISTIC", json.dumps(got))

    # 30 bounded-code sessions: early cheap, late dear -> the shipped model must not see the late ones
    rows = [row(i, "bounded-code", 100000 + 1000 * i) for i in range(21)] + [row(i, "bounded-code", 900000) for i in range(21, 30)]
    rows += [row(100 + i, "lookup", 50000 + 1000 * i) for i in range(5)]
    built = pg.build_by_class(rows)
    bc = built["classes"]["bounded-code"]
    if bc["n_train"] == 21 and bc["model"]["processed"]["p80"] < 900000 and bc["heldout"]["n"] == 9 \
            and set(bc["heldout_ids"]) == {f"s{i:03d}" for i in range(21, 30)}:
        _ok("V-CCRPGO-A3-TIME-SPLIT-NO-LEAK", f"train {bc['n_train']} held-out {bc['heldout']['n']} p80 {bc['model']['processed']['p80']}")
    else:
        _fail("V-CCRPGO-A3-TIME-SPLIT-NO-LEAK", json.dumps({k: bc[k] for k in ("n_train", "heldout", "heldout_ids")}))
    if bc["heldout"]["p80_cov"] == 0.0 and bc["confidence"] == "LOW" and not bc["gate_pass"]:
        _ok("V-CCRPGO-A3-LOW-ON-POOR-COVERAGE", json.dumps(bc["heldout"]))
    else:
        _fail("V-CCRPGO-A3-LOW-ON-POOR-COVERAGE", json.dumps(bc["heldout"]))
    lk = built["classes"]["lookup"]
    if lk["confidence"] == "LOW" and lk["heldout"]["n"] < 8 and "loo" in lk:
        _ok("V-CCRPGO-A3-LOW-ON-THIN-HELDOUT", f"n held-out {lk['heldout']['n']}, loo n {lk['loo']['n']}")
    else:
        _fail("V-CCRPGO-A3-LOW-ON-THIN-HELDOUT", json.dumps(lk))

    stable = [row(i, "bounded-code", 100000 + 100 * (i % 7)) for i in range(30)]
    good = pg.build_by_class(stable)
    gb = good["classes"]["bounded-code"]
    if gb["confidence"] == "HIGH" and gb["gate_pass"]:
        _ok("V-CCRPGO-A3-HIGH-WHEN-GATE-MET", json.dumps(gb["heldout"]))
    else:
        _fail("V-CCRPGO-A3-HIGH-WHEN-GATE-MET", json.dumps(gb["heldout"]))

    img = tmp / "pkt.md"
    img.write_text("# Y -- add a gate\nwrite tests in test_y.py\n", encoding="utf-8")
    hi = pg.contract(good, "# Y -- add a gate", img, cap=1000)
    lo = pg.contract(built, "# Y -- add a gate", img, cap=1000)
    if hi["verdict"] == "SPLIT" and hi["confidence"] == "HIGH" and lo["verdict"] == "ADMIT_LOW_CONFIDENCE" \
            and lo["advisory"] == "SPLIT" and lo["work_class"] == "bounded-code":
        _ok("V-CCRPGO-A3-LOW-NEVER-HARD-REJECTS", f"HIGH->{hi['verdict']} LOW->{lo['verdict']} ({lo['advisory']})")
    else:
        _fail("V-CCRPGO-A3-LOW-NEVER-HARD-REJECTS", json.dumps([hi, lo]))

    unk = tmp / "unk.md"
    unk.write_text("# W -- Autonomy Convergence unit S8\n", encoding="utf-8")
    cu = pg.contract(built, "# W -- Autonomy Convergence unit S8", unk, cap=None)
    if cu["work_class"] == "generic" and cu["confidence"] == "LOW" and cu["forecast"]:
        _ok("V-CCRPGO-A3-UNKNOWN-IS-GENERIC-LOW", json.dumps(cu["forecast"]))
    else:
        _fail("V-CCRPGO-A3-UNKNOWN-IS-GENERIC-LOW", json.dumps(cu))

    look = tmp / "look.md"
    look.write_text("# v1 canary: predecessor lookup\n", encoding="utf-8")
    cl = pg.contract(built, "v1 canary: predecessor lookup", look, cap=None)
    if cl["work_class"] == "lookup" and cl["forecast"]["p50"] < bc["model"]["processed"]["p50"]:
        _ok("V-CCRPGO-A3-LOOKUP-NOT-PRICED-AS-CODE", f"lookup P50 {cl['forecast']['p50']} vs code P50 {round(bc['model']['processed']['p50'])}")
    else:
        _fail("V-CCRPGO-A3-LOOKUP-NOT-PRICED-AS-CODE", json.dumps(cl))


if __name__ == "__main__":
    sys.exit(main())
