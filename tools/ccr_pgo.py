"""CCR v4 B4/B6: Work-Class cost model (Cognitive PGO), boundary forecast, step anomalies, pre-launch contract.

    build    --cls C --out pgo.json  <stream.jsonl ...>   learn the class distribution from real worker transcripts
    build    --by-class --missions M --pack DIR --root CLONE [--v1 S ...] --out pgo-classes.json [--corpus C.json]
             WU-A3: classify every Work Unit session, time-split per class, fit on train, judge on held-out
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


# --- WU-A3: Work-Class PGO by class, fitted on usage projections and judged on a later held-out slice ---
# A class is read from packet / route / obligation TEXT by fixed rules, first match wins; no model is called.
# The rules were written from packet titles before any class cost was computed, and are never tuned on held-out.
CLASS_RULES = [
    ("multimodal", "text", r"screenshot|\.png\b|\bvision\b|visual (?:qa|check|diff)|playwright|in-browser"),
    ("lookup", "title", r"\blook ?up\b|\bpredecessor\b|\bcanary:"),
    ("long-textual", "title", r"knowledge|hand-?off|hand off|decisions|dossier|census|autopsy|certif|\bjudge\b"
                              r"|evidence|\breport\b|frontier"),
    ("bounded-code", "text", r"\btests?\b|test_|\.py\b|\.js\b|\bdrill|fixture|implement|\bbuild\b|\bwire"),
]
GENERIC = "generic"
TRAIN_FRAC = 0.7
MIN_TRAIN = 3            # fewer train sessions than this and the class forecasts with the generic cold start
GATE = {"p50_ape": 0.25, "p80_cov": 0.70, "n_heldout": 8}
WEIGHTS = {"input": 1.0, "cache_read": 0.1, "cache_creation": 1.25, "output": 5.0}


def classify(text: str) -> tuple[str, str | None]:
    """(class, rule that fired). The title is the first non-empty line; 'text' rules see everything."""
    import re
    low = (text or "").lower()
    title = next((ln for ln in low.splitlines() if ln.strip()), "")
    for cls, scope, pat in CLASS_RULES:
        if re.search(pat, title if scope == "title" else low):
            return cls, f"{cls}:{scope}"
    return GENERIC, None


def projection_facts(path: Path) -> dict:
    """Per-session cost from a usage projection (t/mid/usage/blocks per line). A message id streamed over
    several lines counts once; its output is the largest seen (stream-json reports output as it grows)."""
    per: dict[str, dict] = {}
    order: list[str] = []
    model, imgs, results, ts0 = None, 0, 0, None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except ValueError:
                continue  # a torn line carries no usage
            ts0 = ts0 or ev.get("ts")
            for b in ev.get("blocks") or []:
                if b.get("k") == "tool_result" or b.get("images"):
                    results += 1
                    imgs += 1 if b.get("images") or b.get("k") == "image" else 0
            u, mid = ev.get("usage"), ev.get("mid")
            if ev.get("t") != "assistant" or not u or not mid:
                continue
            model = ev.get("model") or model
            row = {"input": u.get("input_tokens", 0) or 0, "cache_read": u.get("cache_read_input_tokens", 0) or 0,
                   "cache_creation": u.get("cache_creation_input_tokens", 0) or 0, "output": u.get("output_tokens", 0) or 0}
            if mid not in per:
                order.append(mid)
                per[mid] = row
            else:
                per[mid] = {k: max(per[mid][k], row[k]) for k in row}
    ctx = [per[m]["input"] + per[m]["cache_read"] + per[m]["cache_creation"] for m in order]
    tot = {k: sum(per[m][k] for m in order) for k in WEIGHTS}
    n = len(ctx)
    return {"calls": n, "floor": ctx[0] if n else 0, "slope": (ctx[-1] - ctx[0]) / (n - 1) if n > 1 else 0.0,
            "processed": sum(tot.values()), "weighted": round(sum(WEIGHTS[k] * tot[k] for k in WEIGHTS), 1),
            "image_share": round(imgs / results, 4) if results else 0.0, "model": model, "ts": ts0, **tot}


def _iso(ts: str | None) -> float | None:
    from datetime import datetime
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() if ts else None
    except ValueError:
        return None


def corpus(missions: Path, pack: Path, root: Path, v1: list[Path] = (), v1_obligation: str = "") -> list[dict]:
    """Every Work Unit mission whose packet is in this clone under vault/programs/ and whose owner session is
    projected, plus the V1 canary streams. One row per owner session."""
    import re
    rows = []
    for m in json.loads(missions.read_text(encoding="utf-8")):
        hit = re.search(r"vault[\\/]+programs[\\/]+(.+)$", m.get("packet") or "")
        if not hit:
            continue
        rel = "vault/programs/" + hit.group(1).replace("\\", "/")
        pkt = root / rel
        if not pkt.is_file():
            continue
        text = pkt.read_text(encoding="utf-8", errors="replace")
        if m.get("route"):
            rp = root / re.sub(r"^.*?(vault[\\/])", r"\1", str(m["route"])).replace("\\", "/")
            text += "\n" + (rp.read_text(encoding="utf-8", errors="replace") if rp.is_file() else "")
        cls, rule = classify(text)
        for sid in m.get("owners") or []:
            sp = pack / "sessions" / f"{sid}.jsonl"
            if not sp.is_file():
                continue
            f = projection_facts(sp)
            if f["calls"] < 1:
                continue
            rows.append({"src": "mission", "id": m["id"], "sid": sid, "packet": rel, "state": m.get("state"),
                         "t": m.get("created") or _iso(f["ts"]), "cls": cls, "rule": rule, **f})
    v1_cls, v1_rule = classify(v1_obligation)
    for p in v1:
        f = projection_facts(p)
        if f["calls"] >= 1:
            rows.append({"src": "v1", "id": p.stem, "sid": None, "packet": v1_obligation, "state": "COMPLETED",
                         "t": _iso(f["ts"]), "cls": v1_cls, "rule": v1_rule, **f})
    return sorted(rows, key=lambda r: (r["t"] or 0, r["id"]))


def fit_class(cls: str, rows: list[dict]) -> dict:
    """Empirical quantiles of whole-session cost: P50 and P80 come straight from the train sessions."""
    q = lambda k, p: _q([r[k] for r in rows], p)  # noqa: E731
    return {"cls": cls, "n": len(rows), "sources": [r["sid"] or r["id"] for r in rows],
            "processed": {"p50": q("processed", 50), "p80": q("processed", 80)},
            "weighted": {"p50": q("weighted", 50), "p80": q("weighted", 80)},
            "calls": {"p50": q("calls", 50), "p80": q("calls", 80)},
            "floor": {"p50": q("floor", 50), "p80": q("floor", 80)},
            "slope": {"p50": q("slope", 50), "p80": q("slope", 80)},
            "image_share": {"p50": q("image_share", 50)}}


def judge(model: dict, rows: list[dict]) -> dict:
    """P50 absolute % error, signed bias (median of (P50 - actual) / actual) and P80 coverage on rows."""
    if not rows or not model.get("n"):
        return {"n": len(rows), "p50_ape": None, "bias": None, "p80_cov": None}
    p50, p80 = model["processed"]["p50"], model["processed"]["p80"]
    rel = [(p50 - r["processed"]) / r["processed"] for r in rows]
    return {"n": len(rows), "p50_ape": round(_q([abs(x) for x in rel], 50), 4), "bias": round(_q(rel, 50), 4),
            "p80_cov": round(sum(r["processed"] <= p80 for r in rows) / len(rows), 4)}


def time_split(rows: list[dict], frac: float = TRAIN_FRAC) -> tuple[list[dict], list[dict]]:
    rows = sorted(rows, key=lambda r: (r["t"] or 0, r["id"]))
    k = round(frac * len(rows))
    k = min(max(k, 1), len(rows) - 1) if len(rows) > 1 else len(rows)
    return rows[:k], rows[k:]


def loo(cls: str, rows: list[dict]) -> dict:
    """Leave-one-out: each session forecast by a model fit on all the others (includes later sessions)."""
    errs, cov = [], []
    for i, r in enumerate(rows):
        m = fit_class(cls, rows[:i] + rows[i + 1:])
        if m["n"]:
            errs.append((m["processed"]["p50"] - r["processed"]) / r["processed"])
            cov.append(r["processed"] <= m["processed"]["p80"])
    if not errs:
        return {"n": len(rows), "p50_ape": None, "bias": None, "p80_cov": None}
    return {"n": len(errs), "p50_ape": round(_q([abs(e) for e in errs], 50), 4), "bias": round(_q(errs, 50), 4),
            "p80_cov": round(sum(cov) / len(cov), 4)}


def confidence(ho: dict) -> str:
    """LOW when the held-out slice is under the gate's n or its P80 coverage is under 70 %."""
    if (ho.get("n") or 0) < GATE["n_heldout"] or ho.get("p80_cov") is None or ho["p80_cov"] < GATE["p80_cov"]:
        return "LOW"
    return "HIGH" if ho["p50_ape"] is not None and ho["p50_ape"] < GATE["p50_ape"] else "MEDIUM"


def build_by_class(rows: list[dict]) -> dict:
    """Per class: time split (earliest ~70 % train, latest ~30 % held-out), fit on train only, judge on
    held-out. The shipped model IS the train fit that was judged. Classes with < MIN_TRAIN train sessions
    forecast with the generic cold start (fit on every class's train rows) and are judged as such."""
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["cls"], []).append(r)
    splits = {c: time_split(rs) for c, rs in by.items()}
    gen_train = [r for tr, _ in splits.values() for r in tr]
    gen_test = [r for _, te in splits.values() for r in te]
    generic = fit_class(GENERIC, gen_train)
    out = {"rules": CLASS_RULES, "train_frac": TRAIN_FRAC, "min_train": MIN_TRAIN, "gate": GATE, "classes": {}}
    for c in sorted(by):
        tr, te = splits[c]
        model = fit_class(c, tr) if len(tr) >= MIN_TRAIN else {**generic, "cold_start_for": c}
        ho = judge(model, te)
        ent = {"model": model, "n_total": len(by[c]), "n_train": len(tr), "heldout": ho,
               "heldout_ids": [r["sid"] or r["id"] for r in te], "confidence": confidence(ho),
               "train_until": tr[-1]["t"] if tr else None}
        if len(by[c]) < 12:
            ent["loo"] = loo(c, by[c])   # tiny class: leave-one-out reported beside, never instead of, the split
        ent["gate_pass"] = bool(ho["n"] >= GATE["n_heldout"] and ho["p50_ape"] is not None
                                and ho["p50_ape"] < GATE["p50_ape"] and ho["p80_cov"] >= GATE["p80_cov"])
        out["classes"][c] = ent
    gho = judge(generic, gen_test)
    out["classes"].setdefault(GENERIC, {"model": generic, "n_total": 0, "n_train": len(gen_train)})
    out["generic"] = {"model": generic, "n_train": len(gen_train), "heldout": gho, "confidence": confidence(gho)}
    return out


def pick_class(classes: dict, text: str) -> tuple[str, dict, str]:
    """(class, model, confidence) for an obligation / packet text; an unknown or empty class is the generic
    cold start at LOW confidence."""
    cls, _ = classify(text)
    ent = classes["classes"].get(cls)
    if ent and ent.get("model", {}).get("n") and "heldout" in ent:
        return cls, ent["model"], ent["confidence"]
    return GENERIC, classes["generic"]["model"], "LOW"


def contract(pgo: dict | None, obligation: str, image: Path, cap: float | None) -> dict:
    text = image.read_text(encoding="utf-8", errors="replace")
    image_tok = round(len(text) * PROSE_TOK_PER_CHAR)
    conf = None
    if pgo and "classes" in pgo:                      # WU-A3 class models: pick one, carry its confidence
        cls, pgo, conf = pick_class(pgo, obligation + "\n" + text)
        pgo = {**pgo, "cls": cls}
    c = {"obligation": obligation, "image": str(image), "image_chars": len(text), "image_tok_est": image_tok,
         "work_class": pgo["cls"] if pgo else None, "necessity": "NOVEL", "reasons": []}
    if conf:
        c["confidence"] = conf
    if not pgo or not pgo.get("n"):
        c.update(verdict="ADMIT_UNFORECAST", forecast=None)
        c["reasons"].append("no Work-Class model: cost is UNKNOWN, not zero")
        return c
    if conf:
        fc = {"p50": pgo["processed"]["p50"], "p80": pgo["processed"]["p80"], "calls": pgo["calls"]["p50"],
              "floor": pgo["floor"]["p50"]}
    else:
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
    if conf == "LOW" and c["verdict"] in ("SPLIT", "DEFLATE"):
        c["advisory"] = c["verdict"]                  # a LOW-confidence forecast advises; it never hard-rejects
        c["verdict"] = "ADMIT_LOW_CONFIDENCE"
    return c


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--cls"); b.add_argument("--out", required=True); b.add_argument("streams", nargs="*")
    b.add_argument("--by-class", action="store_true"); b.add_argument("--missions"); b.add_argument("--pack"); b.add_argument("--root")
    b.add_argument("--v1", nargs="*", default=[]); b.add_argument("--v1-obligation", default="v1 canary: predecessor lookup")
    b.add_argument("--corpus")
    f = sub.add_parser("forecast"); f.add_argument("--pgo", required=True); f.add_argument("--calls", type=float)
    h = sub.add_parser("heldout"); h.add_argument("--cls", required=True)
    h.add_argument("--train", nargs="+", required=True); h.add_argument("--test", nargs="+", required=True)
    a = sub.add_parser("anomaly"); a.add_argument("--pgo", required=True); a.add_argument("stream")
    c = sub.add_parser("contract"); c.add_argument("--pgo"); c.add_argument("--obligation", required=True)
    c.add_argument("--image", required=True); c.add_argument("--cap", type=float)
    x = ap.parse_args(argv)
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))  # noqa: E731
    if x.cmd == "build" and x.by_class:
        if not (x.missions and x.pack and x.root):
            ap.error("build --by-class needs --missions, --pack and --root")
        rows = corpus(Path(x.missions), Path(x.pack), Path(x.root), [Path(p) for p in x.v1], x.v1_obligation)
        r = build_by_class(rows)
        Path(x.out).parent.mkdir(parents=True, exist_ok=True)
        Path(x.out).write_text(json.dumps(r, indent=1), encoding="utf-8")
        if x.corpus:
            Path(x.corpus).write_text(json.dumps(rows, indent=1), encoding="utf-8")
        r = {c: {k: e.get(k) for k in ("n_total", "n_train", "heldout", "confidence", "gate_pass")}
             for c, e in r["classes"].items()} | {"_generic": r["generic"]["heldout"]}
    elif x.cmd == "build":
        if not (x.cls and x.streams):
            ap.error("build needs --cls and streams (or --by-class)")
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
