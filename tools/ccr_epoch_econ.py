"""CCR v4 E1: epoch (rotation) economics with cache-write cost, plus the thinking-carry lever.

Arms simulated on the SAME recorded call sequence:
  A as recorded; B/C/D rotate every k=10/20/40 calls; E rotates when sim ctx >= 2x floor;
  F break-even: rotate when m * expected_remaining * 0.1 * growth > 1.25 * (floor + capsule).
A rotation resets ctx to floor (ctx of the first call) + CAPSULE, pays one cache write of that prefix, drops all
growth carried since the previous rotation. Offline, stdlib only (the thinking lever imports ccr_carry_fit).

    python tools/ccr_epoch_econ.py madzia <stream.jsonl>... --train N --json
    python tools/ccr_epoch_econ.py lobby <dir> --cutoff 2026-10-01
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

W_READ, W_WRITE, W_INPUT, W_OUT = 0.1, 1.25, 1.0, 5.0  # weighted cost per token
CAPSULE = 8000
MIN_CALLS = 5
SAVING_BAR = 15.0  # percent, held-out
KS = {"B": 10, "C": 20, "D": 40}
F_MULTS = (0.25, 0.5, 1.0, 2.0, 4.0)
ARMS = ["A", "B", "C", "D", "E", "F"]


def load_session(path):
    """-> (calls, unknown, first_ts). call = dict(inp, cr, cw, out). unknown = a call lacked cache_creation."""
    calls, seen, unknown, ts0 = [], set(), False, None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") != "assistant":
                continue
            msg = ev.get("message") or {}
            mid = msg.get("id")
            if not mid or mid in seen:
                continue
            seen.add(mid)
            u = msg.get("usage") or {}
            if "cache_creation_input_tokens" not in u or "cache_read_input_tokens" not in u:
                unknown = True
            ts0 = ts0 or ev.get("timestamp")
            calls.append({"inp": u.get("input_tokens") or 0, "cr": u.get("cache_read_input_tokens") or 0,
                          "cw": u.get("cache_creation_input_tokens") or 0, "out": u.get("output_tokens") or 0})
    return calls, unknown, ts0


def ctx_of(c):
    return c["inp"] + c["cr"] + c["cw"]


def cost_of(c):
    return W_READ * c["cr"] + W_WRITE * c["cw"] + W_INPUT * c["inp"] + W_OUT * c["out"]


def simulate(calls, arm, k=None, m=1.0, exp_len=0):
    """-> dict(cost, processed, rotations, rot=list of call indexes that rotate)."""
    if arm == "A":
        return {"cost": sum(cost_of(c) for c in calls), "processed": sum(ctx_of(c) for c in calls),
                "rotations": 0, "rot": []}
    floor = ctx_of(calls[0])
    prefix = floor + CAPSULE
    base_orig = ctx_of(calls[0])  # original ctx at the last rotation
    sim_prev = base_orig  # sim ctx of the previous call
    orig_prev = base_orig
    cost = processed = 0.0
    rot = []
    for i, c in enumerate(calls):
        o = ctx_of(c)
        sim = max(sim_prev + (o - orig_prev), prefix) if i else o  # growth carries on; a recorded compaction cannot go below the rotated prefix
        growth = sim - prefix
        do = False
        if i:
            if arm in KS_ARMS:
                do = i % KS_ARMS[arm] == 0
            elif arm == "E":
                do = sim >= 2 * floor
            elif arm == "F":
                rem = max(exp_len - i, 0)
                do = m * rem * W_READ * growth > W_WRITE * prefix and growth > 0
        if do:
            rot.append(i)
            sim = prefix
            cost += W_WRITE * prefix + W_INPUT * c["inp"] + W_OUT * c["out"]
        else:
            cw = min(c["cw"], sim)
            cost += W_WRITE * cw + W_READ * max(sim - cw - c["inp"], 0) + W_INPUT * c["inp"] + W_OUT * c["out"]
        processed += sim
        sim_prev, orig_prev = sim, o
    return {"cost": cost, "processed": int(processed), "rotations": len(rot), "rot": rot}


KS_ARMS = KS


def run_arm(sessions, arm, **kw):
    cost = proc = rots = 0
    for calls in sessions:
        r = simulate(calls, arm, **kw)
        cost += r["cost"]
        proc += r["processed"]
        rots += r["rotations"]
    return {"cost": cost, "processed": proc, "rotations": rots}


def evaluate(train, held):
    """Fit the best rule on TRAIN, evaluate all arms on HELD-OUT. Returns the table and the verdict."""
    exp_len = int(sum(len(s) for s in train) / max(len(train), 1))
    cfgs = {a: {} for a in ARMS if a != "F"}
    best_m = min(F_MULTS, key=lambda m: run_arm(train, "F", m=m, exp_len=exp_len)["cost"])
    cfgs["F"] = {"m": best_m, "exp_len": exp_len}
    out = {"exp_len": exp_len, "best_m": best_m, "arms": {}}
    a_tr, a_he = run_arm(train, "A")["cost"], run_arm(held, "A")["cost"]
    for a in ARMS:
        tr, he = run_arm(train, a, **cfgs[a]), run_arm(held, a, **cfgs[a])
        out["arms"][a] = {"train_cost": tr["cost"], "held_cost": he["cost"], "held_processed": he["processed"],
                          "held_rotations": he["rotations"],
                          "train_saving_pct": 100 * (a_tr - tr["cost"]) / a_tr if a_tr else 0.0,
                          "held_saving_pct": 100 * (a_he - he["cost"]) / a_he if a_he else 0.0}
    cand = [a for a in ARMS if a != "A"]
    chosen = max(cand, key=lambda a: out["arms"][a]["train_saving_pct"])  # fit on TRAIN only
    out["chosen"] = chosen
    s = out["arms"][chosen]["held_saving_pct"]
    out["held_saving_pct"] = s
    out["verdict"] = "BEATS_A" if s >= SAVING_BAR else f"ABSTAIN:{s:.1f}%"
    return out, cfgs


def thinking_share(per_stream_sessions, thinking_per_step):
    """per attempt: thinking-carry token-calls under A and each arm (rotation drops the carried rows)."""
    res = {a: 0.0 for a in ARMS}
    for calls, think, kw_by_arm in per_stream_sessions:
        n = len(calls)
        for a in ARMS:
            rot = simulate(calls, a, **kw_by_arm[a])["rot"] if a != "A" else []
            for i, t in enumerate(think):  # row appended before call i+1
                nxt = next((r for r in rot if r > i), n)
                res[a] += t * max(nxt - 1 - i, 0) if a != "A" else t * (n - 1 - i)
    return res


def load_dir_sessions(d, cutoff):
    train, held, unknown, short = [], [], 0, 0
    for p in sorted(Path(d).glob("*.jsonl")):
        calls, unk, ts = load_session(p)
        if unk:
            unknown += 1
            continue
        if len(calls) < MIN_CALLS:
            short += 1
            continue
        (held if (ts or "")[:10] >= cutoff else train).append(calls)
    return train, held, unknown, short


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["madzia", "lobby"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--train", type=int, default=6, help="madzia: first N streams are train")
    ap.add_argument("--cutoff", default="2026-10-01")
    a = ap.parse_args(argv)
    res = {}
    if a.mode == "lobby":
        train, held, unknown, short = load_dir_sessions(a.paths[0], a.cutoff)
        res["sessions"] = {"train": len(train), "held": len(held), "unknown": unknown, "short": short}
        res["eval"], _ = evaluate(train, held)
    else:
        sess = []
        for p in a.paths:
            calls, unk, _ = load_session(p)
            sess.append((p, calls, unk))
        usable = [(p, c) for p, c, u in sess if not u and len(c) >= MIN_CALLS]
        train = [c for _, c in usable[:a.train]]
        held = [c for _, c in usable[a.train:]]
        res["sessions"] = {"train": len(train), "held": len(held), "unknown": sum(1 for s in sess if s[2])}
        res["eval"], cfgs = evaluate(train, held)
        sys.path.insert(0, str(Path(__file__).parent))
        import ccr_carry_fit as cf
        per = {p: cf.steps_of(Path(p)) for p, _ in usable}
        fit = cf.fit(per)
        rate = fit["rates"]["thinking_sig"]
        items, tot = [], {"all": []}
        for p, calls in usable:
            think = [rate * row["thinking_sig"] for _, row in per[p][1]]
            items.append((calls, think, cfgs))
        res["thinking"] = {"rate_tok_per_char": rate, "fit_verdict": fit["verdict"]}
        tc = thinking_share(items, None)
        carry_total = sum(sum(c[i]["cw"] * 0 + ctx_of(c[i]) - ctx_of(c[0]) for i in range(len(c))) for c, _, _ in items)
        res["thinking"]["token_calls"] = tc
        res["thinking"]["share_of_A_carry_pct"] = {k: 100 * v / carry_total if carry_total else 0 for k, v in tc.items()}
        res["thinking"]["removed_vs_A_pct"] = {k: 100 * (tc["A"] - v) / tc["A"] if tc["A"] else 0 for k, v in tc.items()}
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
