#!/usr/bin/env python3
"""V-BENCH-* gates for modules/inference_bench (UWCP assimilation R6).

A real HTTP server on loopback streams SSE with KNOWN timings: the first token
after 300 ms, then one every 50 ms. Tolerances are sized below the distance
between the right answer and the plausible wrong ones (TTFT 0.30 vs ITL 0.05;
a TPOT computed over all tokens instead of tokens-1 is ~17 % off at 6 tokens).
This is LOCAL_REALITY for the instrument; measuring GEX44 is owed (S6a) and runs
only through the dispatcher.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.inference_bench import run, run_request, summarize  # noqa: E402
from modules.keos_qwen.outcome import HARNESS_FAILED, OK, TRUNCATED, UNAVAILABLE  # noqa: E402

FIRST_S, GAP_S, TOKENS = 0.30, 0.05, 6
passes = fails = 0


def check(gate, cond, good, bad):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {good}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {bad}")


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _chunk(self, obj):
        self.wfile.write(b"data: " + json.dumps(obj).encode() + b"\n\n")
        self.wfile.flush()

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/500":
            self.send_response(500)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        if self.path == "/empty":
            self._chunk({"choices": [{"delta": {}, "finish_reason": "stop"}]})
            self.wfile.write(b"data: [DONE]\n\n")
            return
        time.sleep(FIRST_S)
        for i in range(TOKENS):
            if i:
                time.sleep(GAP_S)
            last = i == TOKENS - 1
            fr = ("length" if self.path == "/length" else "stop") if last else None
            self._chunk({"choices": [{"delta": {"content": f"t{i}"}, "finish_reason": fr}]})
        if self.path != "/nousage":
            self._chunk({"choices": [], "usage": {"completion_tokens": TOKENS}})
        self.wfile.write(b"data: [DONE]\n\n")


def main() -> int:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    p = {"model": "fake", "messages": [{"role": "user", "content": "hi"}]}

    r = run_request(base + "/ok", p, 10)
    # Timing checks are self-consistent, not wall-clock windows: a loaded host moved one
    # run's numbers outside fixed windows (2026-09-25), which made the gate flaky. The
    # server's sleeps are FLOORS; each check is placed between the right answer and the
    # nearest wrong one.
    tail = 0.5 * (TOKENS - 1) * GAP_S
    check("V-BENCH-TTFT", r.outcome == OK and r.ttft_s >= FIRST_S and r.ttft_s < r.e2e_s - tail,
          f"TTFT {r.ttft_s:.3f}s >= {FIRST_S}s and well before the last token (E2E {r.e2e_s:.3f}s)",
          f"{r}")
    check("V-BENCH-ITL", len(r.itl_s) == TOKENS - 1 and all(x >= 0.8 * GAP_S for x in r.itl_s),
          f"{len(r.itl_s)} inter-token gaps, each >= the server's {GAP_S}s sleep", f"{r.itl_s}")
    mean_itl = sum(r.itl_s) / len(r.itl_s) if r.itl_s else 0
    # (E2E-TTFT)/(tokens-1) equals the mean gap; dividing by tokens instead is 17 % low.
    check("V-BENCH-TPOT", r.tpot_s is not None and mean_itl and abs(r.tpot_s / mean_itl - 1) < 0.08,
          f"TPOT {r.tpot_s:.4f}s within 8 % of mean ITL {mean_itl:.4f}s", f"tpot={r.tpot_s} itl={mean_itl}")
    check("V-BENCH-USAGE-SOURCE", r.output_tokens == TOKENS and r.tokens_source == "usage",
          "token count taken from the server's usage chunk", f"{r.output_tokens} {r.tokens_source}")
    n = run_request(base + "/nousage", p, 10)
    check("V-BENCH-CHUNK-SOURCE", n.output_tokens == TOKENS and n.tokens_source == "chunks",
          "without usage, tokens are counted from chunks AND labelled so", f"{n}")
    t = run_request(base + "/length", p, 10)
    check("V-BENCH-TRUNCATED", t.outcome == TRUNCATED, "finish_reason length -> TRUNCATED", f"{t}")
    e = run_request(base + "/500", p, 10)
    check("V-BENCH-HTTP-ERROR", e.outcome == UNAVAILABLE, "HTTP 500 -> UNAVAILABLE", f"{e}")
    z = run_request(base + "/empty", p, 10)
    check("V-BENCH-NO-CONTENT", z.outcome == HARNESS_FAILED, "a stream with no content is not OK", f"{z}")
    port_dead = run_request("http://127.0.0.1:9/x", p, 2)
    check("V-BENCH-REFUSED", port_dead.outcome == UNAVAILABLE, "connection refused -> UNAVAILABLE",
          f"{port_dead}")

    # The SLO is derived from the measured request: this gate tests the goodput FORMULA,
    # and a fixed 1.0 s ceiling made it a measurement of host load (flaked 2026-09-25).
    s = summarize([r, t, e], 1.0, slo={"ttft_s": r.ttft_s + 1e-6})
    check("V-BENCH-FAILED-EXCLUDED", s["completed_ok"] == 1 and s["by_outcome"] == {OK: 1, TRUNCATED: 1, UNAVAILABLE: 1}
          and abs(s["ttft_s"]["p50"] - r.ttft_s) < 1e-9,
          "non-OK requests are counted by outcome and excluded from latency", f"{s}")
    check("V-BENCH-GOODPUT", s["goodput"] is not None and abs(s["goodput"] - 1 / 3) < 1e-9,
          "goodput = OK and within SLO, over ALL requests (1/3)", f"{s['goodput']}")
    empty = summarize([e, z], 1.0, slo={"ttft_s": 1.0})
    check("V-BENCH-NOTHING-IS-UNKNOWN", empty["ttft_s"]["p50"] is None
          and empty["output_tokens_per_s"] is None and empty["completed_ok"] == 0,
          "nothing completed -> metrics are None, never 0", f"{empty}")

    rep = run(base + "/ok", [p] * 4, concurrency=4, timeout_s=30, slo={"ttft_s": 30.0})
    check("V-BENCH-CONCURRENT", rep["completed_ok"] == 4 and rep["concurrency"] == 4
          and rep["goodput"] == 1.0, "four concurrent requests all measured", f"{rep['by_outcome']}")
    srv.shutdown()
    print(f"BENCH_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
