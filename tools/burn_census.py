#!/usr/bin/env python3
"""BAMR P5: deterministic burn census over mission records -- where did tokens go without progress?

Reads ~/.claude/state/gsd-mission-*.json (read-only, zero model cost) and groups missions by how they ended
(state + normalised `reason`). For each class: missions, measured tokens (`cost_mark.tokens`), tokens of
missions whose work tree never changed (`progress.fp` == `progress_origin`) -- the "spend without progress"
signal -- and how many records could not be judged. A missing measurement is counted as UNKNOWN, never as 0.

  burn_census.py [--state-dir DIR] [--top N] [--json]

This is the evidence an optimisation obligation (BURN_OPTIMIZATION_REQUIRED) must cite; it does not decide
an optimisation by itself. Tree change is a proxy for progress (a commit or edit), not proof of correct work.
"""
import argparse
import glob
import json
import os
import re
import sys

DEFAULT_STATE = os.path.expanduser("~/.claude/state")
_NUM = re.compile(r"\d+(?:\.\d+)?")
_ID = re.compile(r"\b(?:m-[0-9a-f]{6,}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}|[0-9a-f]{7,40})\b")


def reason_class(state, reason):
    """Stable class for a free-text reason: ids and numbers masked, first 70 chars."""
    r = _NUM.sub("N", _ID.sub("<id>", str(reason or "").strip().lower()))
    return "%s | %s" % (state or "?", (r[:70] or "<no reason>"))


def judge(rec):
    """Per-record facts. tokens/changed are None when the record cannot say."""
    cm = rec.get("cost_mark") if isinstance(rec.get("cost_mark"), dict) else {}
    tok = cm.get("tokens")
    tok = int(tok) if isinstance(tok, (int, float)) and not isinstance(tok, bool) and tok >= 0 else None
    prog = rec.get("progress") if isinstance(rec.get("progress"), dict) else {}
    origin, fp = rec.get("progress_origin"), prog.get("fp")
    changed = (fp != origin) if (origin and fp and prog.get("measured")) else None
    return {"state": rec.get("state"), "class": reason_class(rec.get("state"), rec.get("reason")), "tokens": tok,
            "changed": changed, "epochs": rec.get("epoch") or 0, "continuations": rec.get("continuations") or 0,
            "failed_launches": rec.get("failed_launches") or 0}


def census(records):
    classes = {}
    tot = {"missions": 0, "tokens_measured": 0, "tokens_unknown": 0, "no_change_tokens": 0, "change_unknown": 0}
    for rec in records:
        j = judge(rec)
        c = classes.setdefault(j["class"], {"missions": 0, "tokens_measured": 0, "tokens_unknown": 0,
                                            "no_change_missions": 0, "no_change_tokens": 0, "change_unknown": 0,
                                            "epochs": 0, "continuations": 0, "failed_launches": 0})
        c["missions"] += 1
        tot["missions"] += 1
        for k in ("epochs", "continuations", "failed_launches"):
            c[k] += int(j[k]) if isinstance(j[k], (int, float)) else 0
        if j["tokens"] is None:
            c["tokens_unknown"] += 1
            tot["tokens_unknown"] += 1
        else:
            c["tokens_measured"] += j["tokens"]
            tot["tokens_measured"] += j["tokens"]
        if j["changed"] is None:
            c["change_unknown"] += 1
            tot["change_unknown"] += 1
        elif not j["changed"]:
            c["no_change_missions"] += 1
            if j["tokens"] is not None:
                c["no_change_tokens"] += j["tokens"]
                tot["no_change_tokens"] += j["tokens"]
    ranked = sorted(classes.items(), key=lambda kv: (-kv[1]["no_change_tokens"], -kv[1]["tokens_measured"]))
    return {"totals": tot, "classes": [dict(cls=k, **v) for k, v in ranked]}


def load_records(state_dir):
    out, bad = [], 0
    for p in glob.glob(os.path.join(state_dir, "gsd-mission-*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                j = json.load(f)
            if isinstance(j, dict) and j.get("mission_id"):
                out.append(j)
        except (OSError, ValueError):
            bad += 1
    return out, bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state-dir", default=DEFAULT_STATE)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    recs, bad = load_records(a.state_dir)
    res = census(recs)
    res["unreadable_records"] = bad
    res["classes"] = res["classes"][: max(1, a.top)]
    if a.json:
        print(json.dumps(res, indent=1))
        return 0
    t = res["totals"]
    print("missions=%d unreadable=%d tokens_measured=%.1fM (unknown on %d) no_change_tokens=%.1fM (change unknown on %d)"
          % (t["missions"], bad, t["tokens_measured"] / 1e6, t["tokens_unknown"], t["no_change_tokens"] / 1e6, t["change_unknown"]))
    for c in res["classes"]:
        print("%6.1fM no-change %6.1fM total  n=%-4d nochg=%-4d epochs=%-5d cont=%-4d fail=%-3d  %s"
              % (c["no_change_tokens"] / 1e6, c["tokens_measured"] / 1e6, c["missions"], c["no_change_missions"],
                 c["epochs"], c["continuations"], c["failed_launches"], c["cls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
