"""Measure an OpenAI-compatible streaming endpoint the way serving benchmarks do.

Clean-room reconstruction of the metric DEFINITIONS used by vLLM's and SGLang's
serving benchmarks (UWCP assimilation R6; concepts only, no code, no torch):
  TTFT  time from sending the request to the first content token
  TPOT  (E2E - TTFT) / (output_tokens - 1)       -- per-output-token after the first
  ITL   gaps between successive content chunks
  E2E   request start to the last byte
  goodput  share of requests that were OK AND met every SLO given
Serving stays llama.cpp on GEX44 (vLLM/SGLang reserve a fraction of TOTAL VRAM
against FREE on a shared card); this module measures whatever is serving, so the
routing priors (UWCP S6a) come from a measurement, not a guess.

A request that did not complete OK is counted by outcome and EXCLUDED from every
latency statistic -- never averaged in. With nothing completed, every metric is
None (UNKNOWN), never 0. Output token counts come from the server's `usage` when it
sends one; otherwise from content chunks, and the source is recorded.

Remote runs go through the dispatcher only (broker law); this module never opens a
connection by itself -- the caller passes the URL it is allowed to reach.
"""
from __future__ import annotations

import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

from modules.keos_qwen.outcome import HARNESS_FAILED, OK, TRUNCATED, UNAVAILABLE, from_finish_reason


@dataclass
class RequestResult:
    outcome: str
    reason: str = ""
    ttft_s: float | None = None
    e2e_s: float | None = None
    itl_s: list = field(default_factory=list)
    output_tokens: int | None = None
    tokens_source: str = ""              # "usage" | "chunks" | ""
    finish_reason: str | None = None

    @property
    def tpot_s(self) -> float | None:
        if self.ttft_s is None or self.e2e_s is None or not self.output_tokens \
                or self.output_tokens < 2:
            return None
        return (self.e2e_s - self.ttft_s) / (self.output_tokens - 1)


def run_request(url: str, payload: dict, timeout_s: float, headers: dict | None = None,
                clock=time.perf_counter) -> RequestResult:
    body = json.dumps({**payload, "stream": True,
                       "stream_options": {"include_usage": True}}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    t0 = clock()
    first = last = None
    chunks, usage_tokens, finish = 0, None, None
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            itl = []
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except ValueError:
                    return RequestResult(HARNESS_FAILED, f"unparseable stream chunk {data[:60]!r}")
                if obj.get("usage") and obj["usage"].get("completion_tokens") is not None:
                    usage_tokens = int(obj["usage"]["completion_tokens"])
                for ch in obj.get("choices") or []:
                    if ch.get("finish_reason"):
                        finish = ch["finish_reason"]
                    text = (ch.get("delta") or {}).get("content")
                    if text:
                        now = clock()
                        if first is None:
                            first = now
                        else:
                            itl.append(now - last)
                        last = now
                        chunks += 1
            end = clock()
    except urllib.error.HTTPError as exc:
        return RequestResult(UNAVAILABLE, f"HTTP {exc.code}: the server refused the request")
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as exc:
        return RequestResult(UNAVAILABLE, f"could not complete the request: {exc}")
    if first is None:
        return RequestResult(HARNESS_FAILED, "stream ended with no content token",
                             e2e_s=end - t0, finish_reason=finish)
    outcome, reason = from_finish_reason(finish)
    tokens, source = (usage_tokens, "usage") if usage_tokens is not None else (chunks, "chunks")
    return RequestResult(outcome, reason, first - t0, end - t0, itl, tokens, source, finish)


def _pct(values: list, q: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def summarize(results: list[RequestResult], wall_s: float, slo: dict | None = None) -> dict:
    """Aggregate. `slo` may hold ttft_s / tpot_s / e2e_s ceilings for goodput."""
    ok = [r for r in results if r.outcome == OK]
    by_outcome: dict[str, int] = {}
    for r in results:
        by_outcome[r.outcome] = by_outcome.get(r.outcome, 0) + 1
    ttft = [r.ttft_s for r in ok]
    tpot = [r.tpot_s for r in ok if r.tpot_s is not None]
    itl = [x for r in ok for x in r.itl_s]
    e2e = [r.e2e_s for r in ok]
    out_tokens = sum(r.output_tokens or 0 for r in ok)

    def meets(r):
        for k, ceiling in (slo or {}).items():
            v = r.tpot_s if k == "tpot_s" else getattr(r, k)
            if v is None or v > ceiling:
                return False
        return True
    return {
        "requests": len(results),
        "completed_ok": len(ok),
        "by_outcome": by_outcome,
        "ttft_s": {"p50": _pct(ttft, .5), "p90": _pct(ttft, .9), "p99": _pct(ttft, .99),
                   "mean": statistics.fmean(ttft) if ttft else None},
        "tpot_s": {"p50": _pct(tpot, .5), "mean": statistics.fmean(tpot) if tpot else None},
        "itl_s": {"p50": _pct(itl, .5), "p99": _pct(itl, .99)},
        "e2e_s": {"p50": _pct(e2e, .5), "p99": _pct(e2e, .99)},
        "output_tokens_per_s": (out_tokens / wall_s) if ok and wall_s > 0 else None,
        "requests_per_s": (len(ok) / wall_s) if ok and wall_s > 0 else None,
        "goodput": (sum(meets(r) for r in ok) / len(results)) if results and slo else None,
        "slo": dict(slo or {}),
        "tokens_source": sorted({r.tokens_source for r in ok}),
        "truncated": by_outcome.get(TRUNCATED, 0),
    }


def run(url: str, payloads: list[dict], *, concurrency: int, timeout_s: float,
        headers: dict | None = None, slo: dict | None = None) -> dict:
    if concurrency < 1:
        raise ValueError("concurrency must be >= 1")
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda p: run_request(url, p, timeout_s, headers), payloads))
    report = summarize(results, time.perf_counter() - t0, slo)
    report["concurrency"] = concurrency
    report["results"] = [asdict(r) | {"tpot_s": r.tpot_s} for r in results]
    return report
