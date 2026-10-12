"""CCR v4 B4/B6: Work-Class cost model (Cognitive PGO), boundary forecast, step anomalies, pre-launch contract.

    build    --cls C --out pgo.json  <stream.jsonl ...>   learn the class distribution from real worker transcripts
    forecast --pgo pgo.json [--calls N]                    P50/P80 processed for one boundary of the class
    heldout  --cls C --train <...> --test <...>            forecast error on transcripts the model did not see
    anomaly  --pgo pgo.json <stream.jsonl>                 per-call steps above the class P95 step, with the row that caused it
    contract --pgo pgo.json --obligation TEXT --image F [--cap N]   Semantic Cost Contract + admission verdict, before launch

A step is the provider ctx growth between two calls (exact). The forecast of a boundary is floor x calls + the carry
that the class's per-call growth implies: processed(n) = n*floor + g*n*(n-1)/2. Nothing here is a constant someone
picked: every number comes from the transcripts given to `build`. With no model for the class the verdict is
ADMIT_UNFORECAST, never ADMIT, so an unknown cost is not reported as a known one.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ccr_carry_fit import steps_of  # noqa: E402

PROSE_TOK_PER_CHAR = 0.3  # ContextImage text; the B3 fit measured 0.45-0.59 on tool text, prose runs lower


def _q(xs, q):
    return float(np.percentile(np.asarray(xs, dtype=float), q)) if len(xs) else None


def boundary_facts(path: Path) -> dict:
    calls, steps = steps_of(path)
    n = len(calls)
    growth = [(d, row) for d, row in steps]
    return {"name": f"{path.parent.name}/{path.name}", "calls": n, "floor": calls[0] if calls else 0,
            "processed": sum(calls), "last": calls[-1] if calls else 0, "steps": [d for d, _ in growth],
            "slope": (calls[-1] - calls[0]) / (n - 1) if n > 1 else 0.0}


def build(cls: str, paths: list[Path]) -> dict:
    facts = [boundary_facts(p) for p in paths]
    facts = [f for f in facts if f["calls"] > 1]
    steps = [s for f in facts for s in f["steps"]]
    return {"cls": cls, "n": len(facts), "sources": [f["name"] for f in facts],
            "floor": {"p50": _q([f["floor"] for f in facts], 50), "p80": _q([f["floor"] for f in facts], 80)},
            "calls": {"p50": _q([f["calls"] for f in facts], 50), "p80": _q([f["calls"] for f in facts], 80)},
            "slope": {"p50": _q([f["slope"] for f in facts], 50), "p80": _q([f["slope"] for f in facts], 80)},
            "processed": {"p50": _q([f["processed"] for f in facts], 50), "p80": _q([f["processed"] for f in facts], 80)},
            "step": {"p50": _q(steps, 50), "p95": _q(steps, 95), "n": len(steps)}}


def forecast(pgo: dict, calls: float | None = None, floor: float | None = None) -> dict:
    n = calls if calls is not None else pgo["calls"]["p50"]
    f = floor if floor is not None else pgo["floor"]["p50"]
    def proc(g, n_):
        return n_ * f + g * n_ * (n_ - 1) / 2
    return {"calls": n, "floor": f, "p50": proc(pgo["slope"]["p50"], n),
            "p80": proc(pgo["slope"]["p80"], max(n, pgo["calls"]["p80"] if calls is None else n))}


def heldout(cls: str, train: list[Path], test: list[Path]) -> dict:
    pgo = build(cls, train)
    rows = []
    for p in test:
        f = boundary_facts(p)
        fc = forecast(pgo)                                   # before launch: class only
        fk = forecast(pgo, calls=f["calls"], floor=f["floor"])  # after the floor and length are known
        rows.append({"name": f["name"], "actual": f["processed"], "class_p50": round(fc["p50"]), "class_p80": round(fc["p80"]),
                     "err_class_p50": round((fc["p50"] - f["processed"]) / f["processed"], 3),
                     "within_class_p80": f["processed"] <= fc["p80"],
                     "known_len_p50": round(fk["p50"]), "err_known_len": round((fk["p50"] - f["processed"]) / f["processed"], 3)})
    errs = [abs(r["err_class_p50"]) for r in rows]
    return {"pgo": pgo, "rows": rows, "abs_err_class_p50": _q(errs, 50),
            "abs_err_known_len_p50": _q([abs(r["err_known_len"]) for r in rows], 50)}


def anomaly(pgo: dict, path: Path) -> list[dict]:
    """Steps above the class P95 step: what entered the context and how many calls it then rode."""
    calls, steps = steps_of(path)
    bound = pgo["step"]["p95"]
    out = []
    for i, (d, row) in enumerate(steps):
        if bound is not None and d > bound:
            big = max(row, key=row.get)
            out.append({"after_call": i + 1, "step": d, "class_p95": round(bound), "rides": len(calls) - 1 - i,
                        "cost_if_rides": d * (len(calls) - 1 - i), "dominant_kind": big, "chars": row[big]})
    return out


def contract(pgo: dict | None, obligation: str, image: Path, cap: float | None) -> dict:
    text = image.read_text(encoding="utf-8", errors="replace")
    image_tok = round(len(text) * PROSE_TOK_PER_CHAR)
    c = {"obligation": obligation, "image": str(image), "image_chars": len(text), "image_tok_est": image_tok,
         "work_class": pgo["cls"] if pgo else None, "necessity": "NOVEL", "reasons": []}
    if not pgo or not pgo.get("n"):
        c.update(verdict="ADMIT_UNFORECAST", forecast=None)
        c["reasons"].append("no Work-Class model: cost is UNKNOWN, not zero")
        return c
    fc = forecast(pgo)
    c["forecast"] = {k: round(v) for k, v in fc.items()}
    floor_room = (pgo["floor"]["p80"] or 0)
    if floor_room and image_tok > 0.5 * floor_room:
        c["reasons"].append(f"ContextImage ~{image_tok} tok is over half the class floor P80 {round(floor_room)}: DEFLATE it")
    if cap is not None and fc["p80"] > cap:
        c["reasons"].append(f"forecast P80 {round(fc['p80'])} exceeds the cap {round(cap)}: SPLIT the unit")
        c["verdict"] = "SPLIT"
    elif c["reasons"]:
        c["verdict"] = "DEFLATE"
    else:
        c["verdict"] = "ADMIT"
    return c


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--cls", required=True); b.add_argument("--out", required=True); b.add_argument("streams", nargs="+")
    f = sub.add_parser("forecast"); f.add_argument("--pgo", required=True); f.add_argument("--calls", type=float)
    h = sub.add_parser("heldout"); h.add_argument("--cls", required=True)
    h.add_argument("--train", nargs="+", required=True); h.add_argument("--test", nargs="+", required=True)
    a = sub.add_parser("anomaly"); a.add_argument("--pgo", required=True); a.add_argument("stream")
    c = sub.add_parser("contract"); c.add_argument("--pgo"); c.add_argument("--obligation", required=True)
    c.add_argument("--image", required=True); c.add_argument("--cap", type=float)
    x = ap.parse_args(argv)
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))  # noqa: E731
    if x.cmd == "build":
        r = build(x.cls, [Path(p) for p in x.streams])
        Path(x.out).parent.mkdir(parents=True, exist_ok=True)
        Path(x.out).write_text(json.dumps(r, indent=1), encoding="utf-8")
    elif x.cmd == "forecast":
        r = forecast(load(x.pgo), calls=x.calls)
    elif x.cmd == "heldout":
        r = heldout(x.cls, [Path(p) for p in x.train], [Path(p) for p in x.test])
    elif x.cmd == "anomaly":
        r = anomaly(load(x.pgo), Path(x.stream))
    else:
        pgo = load(x.pgo) if x.pgo and Path(x.pgo).exists() else None
        r = contract(pgo, x.obligation, Path(x.image), x.cap)
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
