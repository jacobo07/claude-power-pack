import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w4_benchmark as w

PRICES = {"m1": {"input": 1.0, "cache_read": 0.1, "cache_write_5m": 2.0, "cache_write_1h": 4.0, "output": 10.0},
          w.REF_MODEL: {"input": 4.0, "cache_read": 0.2, "cache_write_5m": 5.0, "cache_write_1h": 8.0, "output": 20.0}}


def row(mid, model, i, r, w5, w1, o):
    return json.dumps({"type": "assistant", "message": {"id": mid, "model": model, "content": [], "usage": {
        "input_tokens": i, "cache_read_input_tokens": r, "cache_creation_input_tokens": w5 + w1,
        "output_tokens": o, "cache_creation": {"ephemeral_5m_input_tokens": w5, "ephemeral_1h_input_tokens": w1}}}})


def make(model):
    d = tempfile.mkdtemp()
    p = Path(d) / "t.jsonl"
    p.write_text("\n".join([row("a", model, 10, 0, 100, 1000, 50), row("b", model, 5, 1000, 0, 200, 20),
                            row("b", model, 5, 1000, 0, 200, 20)]) + "\n", encoding="utf-8")
    return p


def checks():
    bad = []
    r = w.analyze(make("m1"), PRICES)
    # call1 = 10+0+1100; call2 = 5+1000+200; processed = 2315
    if r.get("call1_processed") != 1110: bad.append("call1")
    if r.get("processed") != 2315: bad.append("processed")
    if r.get("calls") != 2: bad.append("calls dedupe")
    if abs(r.get("cache_hit_ratio", 0) - 1000 / 2315) > 1e-12: bad.append("ratio")
    # input15*1 + read1000*.1 + cw5 100*2 + cw1h 1200*4 + out70*10 = 15+100+200+4800+700 = 5815 /1e6
    if abs((r.get("cost_usd") or 0) - 0.005815) > 1e-12: bad.append("price")
    # opus: 15*4+1000*.2+100*5+1200*8+70*20 = 60+200+500+9600+1400 = 11760
    if abs((r.get("cost_usd_at_opus_5_5") or 0) - 0.01176) > 1e-12: bad.append("opus price")
    return bad


def main():
    n = ok = 0

    def t(name, cond):
        nonlocal n, ok
        n += 1
        ok += bool(cond)
        print(("PASS " if cond else "FAIL ") + name)

    bad = checks()
    t("V-1 exact processed/ratio/price on known tokens", not bad)
    r = w.analyze(make("mystery-model"), PRICES)
    t("V-2 unknown model is UNPRICED, not 0", r["cost_usd"] is None and r["cost_status"].startswith("UNPRICED"))
    t("V-3 unknown model still gives opus-5.5 reprice", r["cost_usd_at_opus_5_5"] is not None)
    r = w.analyze(Path(tempfile.gettempdir()) / "nope-w4.jsonl", PRICES)
    t("V-4 missing transcript gives error, not zeros", "error" in r and "processed" not in r)
    orig = w._processed
    w._processed = lambda u: int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0)
    try:
        try:
            mutant_bad = checks()
        except Exception:
            mutant_bad = ["raised"]
    finally:
        w._processed = orig
    t("V-5 mutant dropping cache_write from processed is caught", len(mutant_bad) > 0)
    v = w.judge({"X": {"error": "e"}})
    t("V-6 judge surfaces error", v and v[0][2] == "ERROR")
    print("W4_PASS=%d/%d" % (ok, n))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
