"""CCR v4 A5: E1 arm D (rotate every 40 calls) on held-out Lobby transcripts, with the capsule MEASURED by
tools/ccr_continuation.py at every rotation point (A4 method), replacing E1's assumed 8,000 tokens (stdlib).

Split = A4's (earliest 70 % by first ts is train; held-out only is replayed). At every K40 rotation point i of
a held-out session the transcript is copied up to call i into --work and the capsule is built there with
--repo (a git-init copy of the Lobby repo). The source transcripts are only read.

Three cost models on the same recorded call sequence:
  E1-D-8k       E1's simulate, capsule 8,000 (the original assumption)
  E1-D-measured E1's simulate, prefix = floor + capsule_i (measured at that rotation)
  A4-D-measured A4's rotation cost (capsule write + measured rehydration + first-call overhead, train-fit),
                prefix = floor + capsule_i + R

    python tools/ccr_lobby_a5.py --transcripts <dir> --repo <git-init copy> --work <dir> --out a5-offline.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_breakeven as be  # noqa: E402
import ccr_continuation as cc  # noqa: E402
from ccr_epoch_econ import W_INPUT, W_OUT, W_READ, W_WRITE, cost_of, ctx_of  # noqa: E402

K = 40


def cut_copy(src: Path, k: int, dst: Path) -> None:
    """Write src's lines up to (not including) the line that opens assistant message k+1 (0-based call k)."""
    seen, out = set(), []
    with open(src, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            m = re.search(r'"id":"(msg_[^"]+)"', ln) if '"assistant"' in ln else None
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                if len(seen) > k:
                    break
            out.append(ln)
    dst.write_text("".join(out), encoding="utf-8")


def measure_caps(s: dict, src: Path, repo: Path, work: Path) -> dict[int, dict]:
    obligation = be._first_user_text(src)
    caps = {}
    for i in range(K, s["params"]["n"], K):
        cp = work / f"{s['sid']}.at{i}.jsonl"
        cut_copy(src, i, cp)
        cap = cc.build(repo, obligation, [], cp)
        caps[i] = {"note": "inline" if "PREDECESSOR NOTE" in cap else "ref", **cc.rent(cap)}
    return caps


def sim(calls: list[dict], caps: dict[int, int], model: str, m: dict | None = None) -> dict:
    """caps: rotation call -> capsule tokens. model in E1 | A4."""
    if model == "A":
        return {"cost": sum(cost_of(c) for c in calls), "processed": sum(ctx_of(c) for c in calls), "rotations": 0}
    floor = ctx_of(calls[0])
    R = m["R"] if model == "A4" else 0
    prefix = None
    sim_prev = orig_prev = floor
    cost = processed = 0.0
    rots = 0
    for i, c in enumerate(calls):
        o = ctx_of(c)
        s = o if i == 0 else max(sim_prev + (o - orig_prev), prefix if prefix is not None else floor)
        if i and i in caps:
            rots += 1
            cap = caps[i]
            prefix = floor + cap + R
            s = prefix
            if model == "E1":
                cost += W_WRITE * (floor + cap) + W_INPUT * c["inp"] + W_OUT * c["out"]
                processed += s
                sim_prev, orig_prev = s, o
                continue
            cost += be.rotate_once({**m, "capsule": cap}, floor)
        cw = min(c["cw"], s)
        cost += W_WRITE * cw + W_READ * max(s - cw - c["inp"], 0) + W_INPUT * c["inp"] + W_OUT * c["out"]
        processed += s
        sim_prev, orig_prev = s, o
    return {"cost": cost, "processed": int(processed), "rotations": rots}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ccr_lobby_a5")
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    tdir, work = Path(a.transcripts), Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    rows = be.load_lobby(tdir)
    train, held = be.split(rows)
    caps_tr = [c["est_tokens"] for c in json.loads(
        (Path(__file__).resolve().parent.parent / "vault/programs/ccr/stage3/a4/capsules-lobby.json").read_text())]
    m = be.fit("lobby", train, be._med(caps_tr))
    per, tot = [], {k: {"cost": 0.0, "processed": 0, "rotations": 0} for k in
                    ("A", "E1-D-8k", "E1-D-measured", "A4-D-measured")}
    all_caps = []
    for s in held:
        mc = measure_caps(s, tdir / f"{s['sid']}.jsonl", Path(a.repo), work)
        all_caps += [v["est_tokens"] for v in mc.values()]
        measured = {i: v["est_tokens"] for i, v in mc.items()}
        r = {"A": sim(s["calls"], {}, "A"),
             "E1-D-8k": sim(s["calls"], {i: 8000 for i in measured}, "E1"),
             "E1-D-measured": sim(s["calls"], measured, "E1"),
             "A4-D-measured": sim(s["calls"], measured, "A4", m)}
        a_cost = r["A"]["cost"] or 1
        per.append({"sid": s["sid"], "t": s["t"], "calls": s["params"]["n"], "floor": s["params"]["floor"],
                    "capsules": mc, **{k: {**v, "saving_pct": round(100 * (a_cost - v["cost"]) / a_cost, 2)}
                                      for k, v in r.items()}})
        for k, v in r.items():
            for f in ("cost", "processed", "rotations"):
                tot[k][f] += v[f]
    a_cost = tot["A"]["cost"] or 1
    for k in tot:
        tot[k]["cost"] = round(tot[k]["cost"])
        tot[k]["saving_pct"] = round(100 * (a_cost - tot[k]["cost"]) / a_cost, 2)
    med = {k: be._med([p[k]["saving_pct"] for p in per if p[k]["rotations"]] or [0.0]) for k in tot if k != "A"}
    out = {"k": K, "n_train": len(train), "n_held": len(held), "train_model": m,
           "capsules": {"n": len(all_caps), "p50": be._med(all_caps), "p80": be._q(all_caps, 0.8),
                        "max": max(all_caps) if all_caps else 0, "min": min(all_caps) if all_caps else 0},
           "totals": tot, "median_session_saving_pct_rotating_only": med, "sessions": per}
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({"n_held": len(held), "capsules": out["capsules"], "totals": tot, "median": med}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
