#!/usr/bin/env python3
"""CCN Phase 4: account-level weekly governor shared by laptop and GEX44.

One account, one weekly quota, several hosts. Each host measures the API-equivalent spend recorded in its own
transcripts since the weekly reset and writes a per-host JSON; `status` merges whatever hosts reported.

  account_governor.py measure [--host NAME]          write this host's measured spend
  account_governor.py status  [--json]               pct estimate, lower bound, per-host split, coverage
  account_governor.py check --action arm|topup       exit 0 ALLOW, exit 3 REFUSE (lower bound >= 85%)

Honesty rules: the lower bound counts only measured spend of hosts that reported, so a host with no report
can never push a decision up. Unreadable telemetry never refuses and never allows silently: ALLOW + UNKNOWN.
The calibration (API-eq dollars per 100% of the weekly quota) is an ESTIMATE and is labelled as such.
State lives in --state-dir (default ~/.claude/state): account-governor.json (config), account-governor-override.json,
account-governor-ledger.jsonl, account-governor-hosts/<host>.json.
"""
import argparse
import json
import os
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ccn_bench  # noqa: E402  (price / transcript_cost)
import ccn_census  # noqa: E402  (parse_ts / main_transcripts / records)

REFUSE_PCT = 85.0          # Owner Q2 (2026-10-24): enforce at 85%
OVERRIDE_MAX_S = 24 * 3600
RESET_GAP_S = 2 * 3600     # inferred reset: a >= 2 h gap with no calls anywhere
EXPECTED_HOSTS = ("laptop", "gex44")
WEEK_S = 7 * 24 * 3600
DEFAULT_STATE = os.path.expanduser("~/.claude/state")


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def parse_when(v):
    """epoch seconds from a number or an ISO string; None when unreadable."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    if isinstance(v, str):
        return ccn_census.parse_ts(v)
    return None


def assistant_events(roots, since):
    """(timestamp, message id, usage) for every assistant record at or after `since`, from every transcript."""
    seen = {}
    for _sid, path in ccn_census.main_transcripts(roots, since - 3600):
        for rec in ccn_census.records(path):
            msg = rec.get("message") if isinstance(rec, dict) else None
            if not isinstance(msg, dict) or msg.get("role") != "assistant" or not isinstance(msg.get("usage"), dict):
                continue
            t = ccn_census.parse_ts(rec.get("timestamp"))
            if t is None or t < since:
                continue
            seen[(path, msg.get("id") or rec.get("uuid"))] = (t, msg["usage"])
    return seen


def infer_reset(roots, now, lookback_s=WEEK_S + 86400):
    """Start of the activity burst after the latest >= 2 h zero-call gap; None when there is no such gap."""
    times = sorted(t for t, _ in assistant_events(roots, now - lookback_s).values())
    reset = None
    for a, b in zip(times, times[1:]):
        if b - a >= RESET_GAP_S:
            reset = b
    return reset


def current_window(reset, now):
    """Roll a configured reset forward by whole weeks to the latest one not after `now`.

    The config holds ONE observed reset; without this, the window would keep growing after the
    next weekly reset and the lower bound would sum two weeks into a false REFUSE.
    """
    if reset is None or now is None or reset > now:
        return reset
    return reset + ((now - reset) // WEEK_S) * WEEK_S


def measure_spend(roots, reset_at, now):
    """API-equivalent dollars since `reset_at`, one usage per (transcript, message id)."""
    ev = assistant_events(roots, reset_at)
    return {"api_eq_usd": round(sum(ccn_bench.price(u) for _, u in ev.values()), 4), "calls": len(ev), "measured_at": now}


def config(state_dir):
    cfg = load_json(os.path.join(state_dir, "account-governor.json")) or {}
    return cfg


def host_files(state_dir):
    d = os.path.join(state_dir, "account-governor-hosts")
    out = {}
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.endswith(".json"):
                j = load_json(os.path.join(d, name))
                if isinstance(j, dict):
                    out[name[:-5]] = j
    return out


def status(state_dir, now=None, roots=None):
    """Merged weekly picture. Never raises on missing telemetry: it reports what it could not know."""
    now = time.time() if now is None else now
    cfg = config(state_dir)
    calib = cfg.get("calibration_api_eq_per_100pct")
    if not isinstance(calib, (int, float)) or isinstance(calib, bool) or calib <= 0:
        calib = None
    reset, reset_src = current_window(parse_when(cfg.get("reset_at")), now), "config"
    if reset is None:
        reset, reset_src = infer_reset(roots or ccn_census.default_roots(), now), "inferred (>=2h zero-call gap)"
    hosts_expected = tuple(cfg.get("hosts") or EXPECTED_HOSTS)
    per_host, stale = {}, []
    for h, j in host_files(state_dir).items():
        v, since = j.get("api_eq_usd"), parse_when(j.get("reset_at"))
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        if reset is not None and since is not None and abs(since - reset) > 3600:
            stale.append(h)   # measured against a different window: not summable
            continue
        per_host[h] = round(float(v), 4)
    missing = [h for h in hosts_expected if h not in per_host]
    lower_usd = round(sum(per_host.values()), 4)
    res = {"reset_at": reset, "reset_source": reset_src if reset is not None else "UNKNOWN",
           "calibration_api_eq_per_100pct": calib, "calibration_label": "ESTIMATE" if calib else "MISSING",
           "per_host_api_eq_usd": per_host, "missing_hosts": missing, "stale_hosts": stale,
           "coverage": "FULL" if not missing else ("NONE" if not per_host else "PARTIAL"),
           "lower_bound_usd": lower_usd, "pct_lower_bound": None, "pct_estimate": None, "confidence": "UNKNOWN"}
    if calib and reset is not None and per_host:
        lo = lower_usd / calib * 100.0
        res["pct_lower_bound"] = round(lo, 2)
        rep = cfg.get("reported_pct")      # optional Owner/usage-screen reading for this window
        rep_at = parse_when(cfg.get("reported_at"))
        usable = isinstance(rep, (int, float)) and not isinstance(rep, bool) and rep_at is not None and rep_at >= reset
        res["pct_estimate"] = round(max(lo, float(rep)), 2) if usable else round(lo, 2)
        res["estimate_source"] = "reported_pct" if usable and rep > lo else "measured lower bound"
        res["confidence"] = "HIGH" if res["coverage"] == "FULL" else "LOWER BOUND ONLY (hosts missing: %s)" % ",".join(missing)
    return res


def read_override(state_dir, now):
    """(active, reason). Valid only with a non-empty reason and an `until` in the future within 24 h."""
    j = load_json(os.path.join(state_dir, "account-governor-override.json"))
    if not isinstance(j, dict):
        return False, "none"
    until = parse_when(j.get("until"))
    if until is None:
        return False, "override unreadable (no usable `until`)"
    if until <= now:
        return False, "override expired"
    if until > now + OVERRIDE_MAX_S:
        return False, "override rejected: `until` is more than 24 h away"
    if not str(j.get("reason") or "").strip():
        return False, "override rejected: no reason"
    return True, str(j["reason"]).strip()


def decide(st, override, action):
    """(exit code, verdict, why). 0 ALLOW, 3 REFUSE."""
    lo, est = st["pct_lower_bound"], st["pct_estimate"]
    if lo is None:
        return 0, "ALLOW+UNKNOWN", "telemetry unreadable (%s): neither refused nor cleared" % (
            "no calibration" if st["calibration_api_eq_per_100pct"] is None else "no spend or reset")
    if lo >= REFUSE_PCT:
        if override[0]:
            return 0, "ALLOW+OVERRIDE", "lower bound %.1f%% >= %.0f%% but Owner override active: %s" % (lo, REFUSE_PCT, override[1])
        return 3, "REFUSE", "%s refused: weekly lower bound %.1f%% >= %.0f%% (Owner Q2); override file absent or invalid (%s)" % (
            action, lo, REFUSE_PCT, override[1])
    if est is not None and est >= REFUSE_PCT:
        return 0, "ALLOW+WARN", "estimate %.1f%% >= %.0f%% but the measured lower bound is %.1f%%" % (est, REFUSE_PCT, lo)
    return 0, "ALLOW", "lower bound %.1f%%, estimate %.1f%%" % (lo, est)


def append_ledger(state_dir, row):
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, "account-governor-ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def check(state_dir, action, now=None, roots=None):
    now = time.time() if now is None else now
    st = status(state_dir, now, roots)
    code, verdict, why = decide(st, read_override(state_dir, now), action)
    append_ledger(state_dir, {"ts": now, "action": action, "verdict": verdict, "exit": code, "why": why,
                              "pct_lower_bound": st["pct_lower_bound"], "pct_estimate": st["pct_estimate"],
                              "coverage": st["coverage"]})
    return code, verdict, why, st


def cmd_measure(a):
    now = time.time()
    cfg = config(a.state_dir)
    roots = a.root or ccn_census.default_roots()
    reset = current_window(parse_when(cfg.get("reset_at")), now) or infer_reset(roots, now)
    if reset is None:
        print("measure: no reset_at in config and none inferable; nothing written", file=sys.stderr)
        return 2
    row = dict(measure_spend(roots, reset, now), host=a.host, reset_at=reset)
    d = os.path.join(a.state_dir, "account-governor-hosts")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, a.host + ".json")
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(row, f)
    os.replace(tmp, path)
    print(json.dumps(row))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state-dir", default=DEFAULT_STATE)
    ap.add_argument("--root", action="append", help="projects directory for reset inference / measure")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--host", default=socket.gethostname())
    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--action", choices=("arm", "topup"), required=True)
    a = ap.parse_args(argv)
    if a.cmd == "measure":
        return cmd_measure(a)
    if a.cmd == "status":
        st = status(a.state_dir, roots=a.root)
        print(json.dumps(st, indent=1) if a.json else "\n".join("%s: %s" % kv for kv in st.items()))
        return 0
    code, verdict, why, _ = check(a.state_dir, a.action, roots=a.root)
    print("%s: %s" % (verdict, why))
    return code


if __name__ == "__main__":
    sys.exit(main())
