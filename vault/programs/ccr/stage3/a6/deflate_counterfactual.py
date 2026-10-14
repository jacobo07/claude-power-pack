"""WU-A6 DEFLATE counterfactual on one real undeclared launch (laptop projection, content-free).
Every call of the undeclared session carried D = its first-call context minus the median first-call context of
the same project's declared unit workers. DEFLATE would remove D from every call: processed saving = calls x D.
Weighted saving: on call 1 D is priced at that call's own input/cache mix; on later calls at cache_read (0.1),
which is what a stable prefix costs once cached. Output tokens are left unchanged (no claim on them).
Usage: python3 deflate_counterfactual.py <pack> <undeclared sid prefix> <declared sid prefix>..."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from madzia_history import K, W, facts  # noqa: E402


def first_call(path: Path) -> dict:
    for line in open(path, errors="replace"):
        o = json.loads(line)
        if o.get("role") == "assistant" and isinstance(o.get("usage"), dict) and not o.get("sidechain") and o.get("mid"):
            return {k: int(o["usage"].get(k) or 0) for k in K}
    raise SystemExit(f"no call in {path}")


def main(pack: str, und: str, decl: list[str]) -> int:
    f = lambda p: next((Path(pack) / "sessions").glob(f"{p}*.jsonl"))
    u, ds = facts(f(und)), [facts(f(p)) for p in decl]
    floor_d = statistics.median(d["floor"] for d in ds)
    d_tok = u["floor"] - floor_d
    c1 = first_call(f(und))
    ctx1 = sum(c1[k] for k in K[:3])
    w1 = sum(c1[k] * W[k] for k in K[:3]) / ctx1          # price per context token on call 1
    saved_p = u["calls"] * d_tok
    saved_w = d_tok * w1 + (u["calls"] - 1) * d_tok * W["cache_read_input_tokens"]
    print(json.dumps({"undeclared": und, "calls": u["calls"], "floor_undeclared": u["floor"],
                      "declared_floors": [d["floor"] for d in ds], "floor_declared_median": floor_d,
                      "D_per_call": d_tok, "call1_mix": c1, "call1_price_per_ctx_tok": round(w1, 4),
                      "processed_before": u["processed"], "processed_after": u["processed"] - saved_p,
                      "processed_saved": saved_p, "processed_saved_pct": round(100 * saved_p / u["processed"], 1),
                      "weighted_before": u["weighted"], "weighted_after": round(u["weighted"] - saved_w, 1),
                      "weighted_saved": round(saved_w, 1),
                      "weighted_saved_pct": round(100 * saved_w / u["weighted"], 1)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3:]))
