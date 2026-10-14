"""WU-A6: per-session call facts for one project's history (laptop projections, content-free).
Processed = input + cache_read + cache_creation + output per distinct mid (largest streamed output kept);
weighted = input 1, cache_read 0.1, cache_creation 1.25, output 5 (A3 corpus definitions).
Usage: python3 madzia_history.py <pack> <sid-prefix>..."""
import glob, json, sys
from pathlib import Path

K = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")
W = dict(zip(K, (1, 0.1, 1.25, 5)))


def facts(path: Path) -> dict:
    calls, order = {}, []
    for line in open(path, errors="replace"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        u = o.get("usage")
        if o.get("role") != "assistant" or not isinstance(u, dict) or o.get("sidechain") or not o.get("mid"):
            continue
        u = {k: int(u.get(k) or 0) for k in K}
        if o["mid"] not in calls:
            order.append(o["mid"])
            calls[o["mid"]] = (u, o.get("ts"), o.get("model"))
        elif u["output_tokens"] > calls[o["mid"]][0]["output_tokens"]:
            calls[o["mid"]] = (u, calls[o["mid"]][1], calls[o["mid"]][2])
    us = [calls[m][0] for m in order]
    ctx = [u["input_tokens"] + u["cache_read_input_tokens"] + u["cache_creation_input_tokens"] for u in us]
    return {"calls": len(us), "floor": ctx[0] if ctx else None, "last_ctx": ctx[-1] if ctx else None,
            "processed": sum(sum(u.values()) for u in us),
            "weighted": round(sum(u[k] * W[k] for u in us for k in K), 1),
            "first_ts": calls[order[0]][1] if order else None, "model": calls[order[0]][2] if order else None}


def main(pack: str, prefixes: list[str]) -> int:
    out = {}
    for p in prefixes:
        f = next(iter(glob.glob(str(Path(pack) / "sessions" / f"{p}*.jsonl"))), None)
        out[p] = facts(Path(f)) if f else None
    json.dump(out, sys.stdout, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
