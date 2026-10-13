"""CCR v4 A4: weighted rotation break-even per Work Class, with MEASURED capsules (stdlib).

At a call whose context is `ctx`, the two futures differ only in what every later call reads:
  continuing   every call reads ctx (+ its own growth, the same in both futures) at W_READ
  rotating     pays once: W_WRITE * (floor + capsule)        capsule + floor cache write
                        + rehydration calls (measured: calls 1..r of a fresh class session, plus r reads of the capsule)
                        + first-call overhead (measured: the first call's output and uncached input)
               then every call reads floor + capsule + R, R = the context the rehydration calls add.
  k*(ctx) = rotate_once / (W_READ * (ctx - floor - capsule - R)): calls a rotation needs to pay itself back.
A greedy "rotate iff E[remaining] > k*" over-rotates (A4 replay: Lobby -22 %): each rotation's saving only lasts
until the next one. With carry growing g tokens per call, a renewal cycle of T calls costs rotate_once +
W_READ*g*T^2/2, minimal per call at carry X* = g*T* = sqrt(2 * rotate_once * g / W_READ). Decision rule:
  rotate iff carry = ctx - floor - capsule - R >= X*  AND  E[remaining calls | i] > k*(ctx).
Growth after the decision is paid identically in both futures and cancels. Cache is assumed warm on the
continuing side (a cold resume would also pay W_WRITE * ctx, which only favours rotating).

    python tools/ccr_breakeven.py capsules-pp --corpus <a3 corpus.json> --root . --out caps-pp.json
    python tools/ccr_breakeven.py capsules-lobby --transcripts <dir> --repo <git-init copy> --work <dir> --out caps-lobby.json
    python tools/ccr_breakeven.py export --be be.json --cls bounded-code --as bounded-code-worker --out <pgo>/bounded-code-worker.breakeven.json
    python tools/ccr_breakeven.py fit --corpus <corpus.json> --pack <pack> --lobby <dir> --caps-pp .. --caps-lobby .. --out be.json
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_continuation as cc  # noqa: E402
from ccr_epoch_econ import W_INPUT, W_OUT, W_READ, W_WRITE, cost_of, ctx_of, load_session  # noqa: E402

REHYD_CALLS = 3            # calls after the first that re-establish the working set
MIN_CALLS = 5              # as E1: shorter sessions have nothing to rotate
CEILING = 300_000          # the gsd_epoch continuation ceiling the shadow is compared with
TRAIN_FRAC = 0.7           # as A3: the earliest 70 % of a class (by first ts) is train
LOBBY_EVERY = 40           # Lobby capsule sample points: E1's winning arm D rotated every 40 calls
LOBBY_MAX_POINTS = 3       # per session
NOTE_SLOT = cc.est_tokens(cc.NOTE_ITEM_CHARS + 40)  # a predecessor note inlined at its largest (PP has no text)


# ------------------------------------------------------------------------ per-call data
def calls_of(path) -> tuple[list[dict], str | None]:
    """Per-call usage from a usage projection (t/mid) or a full transcript (type/message). A message id
    streamed over several lines counts once, with the largest value seen."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        head = fh.readline()
    if '"t":' not in head and '"t" :' not in head:
        calls, _, ts = load_session(path)
        return calls, ts
    per, order, ts0 = {}, [], None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            ts0 = ts0 or ev.get("ts")
            u, mid = ev.get("usage"), ev.get("mid")
            if ev.get("t") != "assistant" or not u or not mid:
                continue
            row = {"inp": u.get("input_tokens") or 0, "cr": u.get("cache_read_input_tokens") or 0,
                   "cw": u.get("cache_creation_input_tokens") or 0, "out": u.get("output_tokens") or 0}
            if mid not in per:
                order.append(mid)
                per[mid] = row
            else:
                per[mid] = {k: max(per[mid][k], row[k]) for k in row}
    return [per[m] for m in order], ts0


def session_params(calls: list[dict]) -> dict:
    ctx = [ctx_of(c) for c in calls]
    r = min(REHYD_CALLS, len(calls) - 1)
    return {"n": len(calls), "floor": ctx[0], "g": max((ctx[-1] - ctx[0]) / (len(ctx) - 1), 0.0) if len(ctx) > 1 else 0.0, "R": max(ctx[r] - ctx[0], 0) if r > 0 else 0,
            "rehyd_cost": sum(cost_of(c) for c in calls[1:r + 1]), "r": r,
            "first_overhead": W_INPUT * calls[0]["inp"] + W_OUT * calls[0]["out"]}


def _med(xs):
    return statistics.median(xs) if xs else 0.0


def _q(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(math.ceil(q * len(s))) - 1)] if s else 0.0


# ------------------------------------------------------------------------ the model
def rotate_once(m: dict, floor: float | None = None) -> float:
    f = m["floor"] if floor is None else floor
    return W_WRITE * (f + m["capsule"]) + m["rehyd_cost"] + m["r"] * W_READ * m["capsule"] + m["first_overhead"]


def k_star(ctx: float, m: dict, floor: float | None = None) -> float:
    f = m["floor"] if floor is None else floor
    saving = W_READ * (ctx - f - m["capsule"] - m["R"])
    return rotate_once(m, f) / saving if saving > 0 else math.inf


def x_star(m: dict, floor: float | None = None) -> float:
    """Renewal-optimal carry at which to rotate (infinite horizon, linear growth g per call)."""
    return math.sqrt(2 * rotate_once(m, floor) * m["g"] / W_READ) if m["g"] > 0 else math.inf


def expected_remaining(i: int, lengths: list[int]) -> float:
    """Median calls still to come for a session already at call i (survivors of the train lengths)."""
    rest = [n - i for n in lengths if n > i]
    return _med(rest) if rest else 0.0


def decide(ctx: float, i: int, m: dict, floor: float | None = None) -> dict:
    f = m["floor"] if floor is None else floor
    k, xs = k_star(ctx, m, f), x_star(m, f)
    carry = ctx - f - m["capsule"] - m["R"]
    rem = expected_remaining(i, m["lengths"])
    return {"rotate": carry >= xs and rem > k, "k_star": None if math.isinf(k) else round(k, 1), "remaining": rem,
            "carry": int(carry), "x_star": None if math.isinf(xs) else round(xs), "ctx": int(ctx),
            "rule": "rotate iff carry >= X* and E[remaining calls] > k*"}


def fit(cls: str, sessions: list[dict], capsule: float) -> dict:
    ps = [s["params"] for s in sessions]
    return {"cls": cls, "n": len(ps), "capsule": round(capsule, 1), "r": REHYD_CALLS,
            "floor": _med([p["floor"] for p in ps]), "R": _med([p["R"] for p in ps]),
            "g": round(_med([p["g"] for p in ps]), 1),
            "rehyd_cost": round(_med([p["rehyd_cost"] for p in ps]), 1),
            "first_overhead": round(_med([p["first_overhead"] for p in ps]), 1),
            "lengths": sorted(p["n"] for p in ps)}


# ------------------------------------------------------------------------ replay
def simulate(calls: list[dict], m: dict, arm: str, trace_at: int | None = None) -> dict:
    """A = as recorded; C300 = rotate when sim ctx >= 300k (the continuation ceiling, at call grain);
    BE = break-even decide() at every call. A rotation pays rotate_once (session's own floor) and resets
    sim ctx to floor + capsule + R; recorded growth then carries on (E1's clamp: never below that prefix)."""
    floor = ctx_of(calls[0])
    prefix = floor + m["capsule"] + m["R"]
    cost = processed = 0.0
    sim_prev = orig_prev = floor
    rot, at = [], None
    for i, c in enumerate(calls):
        o = ctx_of(c)
        sim = o if (i == 0 or arm == "A") else max(sim_prev + (o - orig_prev), prefix if rot else floor)
        do = False
        if i and arm == "C300":
            do = sim >= CEILING
        elif i and arm == "K40":
            do = i % 40 == 0
        elif i and arm == "BE":
            do = decide(sim, i, m, floor)["rotate"]
        if do:
            rot.append(i)
            cost += rotate_once(m, floor)
            sim = prefix
        cw = min(c["cw"], sim)
        cost += W_WRITE * cw + W_READ * max(sim - cw - c["inp"], 0) + W_INPUT * c["inp"] + W_OUT * c["out"]
        processed += sim
        if trace_at is not None and i == trace_at:
            at = sim
        sim_prev, orig_prev = sim, o
    return {"cost": cost, "processed": int(processed), "rotations": len(rot), "ctx_at": at}


def replay(held: list[dict], m: dict) -> dict:
    out = {}
    for arm in ("A", "C300", "K40", "BE"):
        rs = [simulate(s["calls"], m, arm) for s in held]
        out[arm] = {"cost": round(sum(r["cost"] for r in rs)), "processed": sum(r["processed"] for r in rs),
                    "rotations": sum(r["rotations"] for r in rs)}
    a = out["A"]["cost"] or 1
    for arm in out:
        out[arm]["saving_pct"] = round(100 * (a - out[arm]["cost"]) / a, 2)
    return out


def history_elasticity(sessions: list[dict], m: dict, step: int) -> dict:
    """Model-facing ctx at a fixed later call under carry (recorded) vs capsule (break-even rotations)."""
    rows = []
    for s in sessions:
        if s["params"]["n"] <= step:
            continue
        carry = ctx_of(s["calls"][step])
        cap = simulate(s["calls"], m, "BE", trace_at=step)["ctx_at"]
        rows.append({"sid": s["sid"], "carry": carry, "capsule": cap})
    if not rows:
        return {"step": step, "n": 0}
    floor = _med([s["params"]["floor"] for s in sessions if s["params"]["n"] > step])
    mc, mp = _med([r["carry"] for r in rows]), _med([r["capsule"] for r in rows])
    return {"step": step, "n": len(rows), "median_floor": floor, "carry_ctx_p50": mc, "capsule_ctx_p50": mp,
            "carry_slope_per_call": round((mc - floor) / step, 1), "capsule_slope_per_call": round((mp - floor) / step, 1),
            "ratio_capsule_over_carry": round(mp / mc, 3) if mc else None, "rows": rows}


# ------------------------------------------------------------------------ capsules (measured)
def packet_title(p: Path) -> str:
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            return ln.lstrip("# ").strip()[:300]
    return p.stem


def capsules_pp(corpus: list[dict], root: Path) -> list[dict]:
    """One capsule per mission row, built on this clone: obligation = packet title, receipt = <packet>-receipt.md
    when it exists. Projections carry no text, so no predecessor note; NOTE_SLOT is added when fitting."""
    out = []
    for row in corpus:
        if row.get("src") != "mission" or not row.get("packet"):
            continue
        pk = root / row["packet"]
        if not pk.exists():
            continue
        rc = pk.with_name(pk.stem + "-receipt.md")
        recs = [rc] if rc.exists() else []
        cap = cc.build(root, packet_title(pk), recs)
        out.append({"id": row["id"], "cls": row["cls"], "receipt": bool(recs), **cc.rent(cap)})
    return out


def _first_user_text(path: Path) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            if '"user"' not in ln:
                continue
            try:
                o = json.loads(ln)
            except ValueError:
                continue
            if o.get("type") == "user" and not o.get("isMeta"):
                c = (o.get("message") or {}).get("content")
                t = c if isinstance(c, str) else "\n".join(
                    b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")
                t = next((x.strip() for x in t.splitlines() if x.strip()), "")
                if t:
                    return t[:300]
    return "continue the Ralph epoch"


def capsules_lobby(tdir: Path, repo: Path, work: Path) -> list[dict]:
    """At each sample rotation point (every LOBBY_EVERY calls, up to LOBBY_MAX_POINTS per session) copy the
    transcript up to that call into `work` and build the capsule with --repo (git-init copy) and --transcript (copy).
    The source transcripts are only read."""
    work.mkdir(parents=True, exist_ok=True)
    out = []
    for p in sorted(tdir.glob("*.jsonl")):
        calls, _ = calls_of(p)
        if len(calls) < LOBBY_EVERY + 1:
            continue
        points = [k for k in range(LOBBY_EVERY, len(calls), LOBBY_EVERY)][:LOBBY_MAX_POINTS]
        obligation = _first_user_text(p)
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        for k in points:
            seen, cut = set(), len(lines)
            for j, ln in enumerate(lines):
                m = re.search(r'"id":"(msg_[^"]+)"', ln) if '"assistant"' in ln else None
                if m and m.group(1) not in seen:
                    seen.add(m.group(1))
                    if len(seen) > k:
                        cut = j
                        break
            cp = work / f"{p.stem}.at{k}.jsonl"
            cp.write_text("".join(lines[:cut]), encoding="utf-8")
            cap = cc.build(repo, obligation, [], cp)
            out.append({"sid": p.stem, "at_call": k, "cls": "lobby",
                        "note": "inline" if "PREDECESSOR NOTE" in cap else "ref", **cc.rent(cap)})
    return out


# ------------------------------------------------------------------------ assembling the classes
def load_pp(corpus: list[dict], pack: Path) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for row in corpus:
        p = pack / "sessions" / f"{row['sid']}.jsonl"
        if row.get("src") == "v1":
            continue  # V1 streams live under v1/ with their own names; the 3 apr canaries keep lookup alive
        if not p.exists():
            continue
        calls, _ = calls_of(p)
        if len(calls) < MIN_CALLS:
            continue
        by.setdefault(row["cls"], []).append({"sid": row["sid"], "t": row.get("t") or 0, "calls": calls,
                                              "params": session_params(calls)})
    return by


def load_lobby(tdir: Path) -> list[dict]:
    out = []
    for p in sorted(tdir.glob("*.jsonl")):
        calls, ts = calls_of(p)
        if len(calls) < MIN_CALLS:
            continue
        out.append({"sid": p.stem, "t": ts or "", "calls": calls, "params": session_params(calls)})
    return out


def split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    s = sorted(rows, key=lambda r: r["t"])
    k = round(TRAIN_FRAC * len(s))
    return s[:k], s[k:]


def class_report(cls: str, rows: list[dict], capsule: float, history_step: int | None = None) -> dict:
    train, held = split(rows)
    m = fit(cls, train, capsule)
    rep = {"model": m, "n_train": len(train), "n_held": len(held)}
    rep["k_star"] = {}
    for label, ctx in (("ctx_100k", 100_000), ("ctx_200k", 200_000), ("ctx_300k", CEILING)):
        k = k_star(ctx, m)
        rep["k_star"][label] = None if math.isinf(k) else round(k, 1)
    rep["rotate_once"] = round(rotate_once(m), 1)
    xs = x_star(m)
    rep["x_star"] = None if math.isinf(xs) else round(xs)
    rep["ctx_star"] = None if math.isinf(xs) else round(m["floor"] + m["capsule"] + m["R"] + xs)
    rep["k_star_at_ctx_star"] = None if math.isinf(xs) else round(rotate_once(m) / (W_READ * xs), 1)
    # the smallest ctx at which rotating pays back within the remaining calls of a session at the class P50 midpoint
    mid = int(_med(m["lengths"]) // 2)
    rem = expected_remaining(mid, m["lengths"])
    rep["breakeven_ctx_at_mid"] = {"call": mid, "remaining": rem,
                                   "ctx": round(m["floor"] + m["capsule"] + m["R"] + rotate_once(m) / (W_READ * rem))
                                   if rem > 0 else None}
    rep["held_replay"] = replay(held, m) if held else None
    # Sensitivity: the same replay under E1's assumptions (capsule 8,000, rotation = floor + capsule write only)
    e1 = {**m, "capsule": 8000, "R": 0, "rehyd_cost": 0.0, "first_overhead": 0.0, "r": 0}
    rep["held_replay_e1_assumptions"] = replay(held, e1) if held else None
    if history_step:
        rep["history"] = history_elasticity(held + train, m, history_step)
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ccr_breakeven")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("capsules-pp")
    a.add_argument("--corpus", required=True)
    a.add_argument("--root", required=True)
    a.add_argument("--out", required=True)
    b = sp.add_parser("capsules-lobby")
    b.add_argument("--transcripts", required=True)
    b.add_argument("--repo", required=True)
    b.add_argument("--work", required=True)
    b.add_argument("--out", required=True)
    x = sp.add_parser("export", help="one class model as the mod reads it: <stateDir>/pgo/<unit class>.breakeven.json")
    x.add_argument("--be", required=True)
    x.add_argument("--cls", required=True)
    x.add_argument("--as", dest="as_cls", required=True)
    x.add_argument("--out", required=True)
    f = sp.add_parser("fit")
    f.add_argument("--corpus", required=True)
    f.add_argument("--pack", required=True)
    f.add_argument("--lobby", required=True)
    f.add_argument("--caps-pp", required=True)
    f.add_argument("--caps-lobby", required=True)
    f.add_argument("--history-step", type=int, default=120)
    f.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "capsules-pp":
        rows = capsules_pp(json.loads(Path(args.corpus).read_text()), Path(args.root))
        Path(args.out).write_text(json.dumps(rows, indent=1))
        print(json.dumps({"n": len(rows)}))
        return 0
    if args.cmd == "capsules-lobby":
        rows = capsules_lobby(Path(args.transcripts), Path(args.repo), Path(args.work))
        Path(args.out).write_text(json.dumps(rows, indent=1))
        print(json.dumps({"n": len(rows)}))
        return 0
    if args.cmd == "export":
        m = dict(json.loads(Path(args.be).read_text())["classes"][args.cls]["model"])
        m["fit_cls"], m["cls"] = m["cls"], args.as_cls
        Path(args.out).write_text(json.dumps(m))
        print(json.dumps({k: m[k] for k in ("cls", "fit_cls", "capsule", "R", "g")}))
        return 0
    caps_pp = json.loads(Path(args.caps_pp).read_text())
    caps_lb = json.loads(Path(args.caps_lobby).read_text())
    corpus = json.loads(Path(args.corpus).read_text())
    out = {"weights": {"read": W_READ, "write": W_WRITE, "input": W_INPUT, "output": W_OUT},
           "rehyd_calls": REHYD_CALLS, "ceiling": CEILING, "note_slot_tokens": NOTE_SLOT, "classes": {}, "capsules": {}}
    for cls, rows in sorted(load_pp(corpus, Path(args.pack)).items()):
        ts = [c["est_tokens"] for c in caps_pp if c["cls"] == cls]
        cap = _med(ts) + NOTE_SLOT
        out["capsules"][cls] = {"n": len(ts), "p50": _med(ts), "p80": _q(ts, 0.8), "max": max(ts) if ts else 0,
                                "used": cap, "used_is": "p50 + note slot (PP projections carry no note text)"}
        out["classes"][cls] = class_report(cls, rows, cap)
    ts = [c["est_tokens"] for c in caps_lb]
    out["capsules"]["lobby"] = {"n": len(ts), "p50": _med(ts), "p80": _q(ts, 0.8), "max": max(ts) if ts else 0,
                                "used": _med(ts), "used_is": "p50 (note measured at each point)",
                                "note_inline": sum(1 for c in caps_lb if c["note"] == "inline")}
    out["classes"]["lobby"] = class_report("lobby", load_lobby(Path(args.lobby)), _med(ts), args.history_step)
    Path(args.out).write_text(json.dumps(out, indent=1))
    for cls, r in out["classes"].items():
        print(cls, json.dumps({"ctx_star": r["ctx_star"], "x_star": r["x_star"], "k_at_ctx_star": r["k_star_at_ctx_star"],
                               "k_star": r["k_star"], "rotate_once": r["rotate_once"], "be_mid": r["breakeven_ctx_at_mid"],
                               "replay": r["held_replay"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
