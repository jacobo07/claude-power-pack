#!/usr/bin/env python3
"""CCN Phase 4: account-level weekly governor shared by laptop and GEX44.

One account, one weekly quota, several hosts. Each host measures the API-equivalent spend recorded in its own
transcripts since the weekly reset and writes a per-host JSON; `status` merges whatever hosts reported.

  account_governor.py measure [--host NAME]          write this host's measured spend
  account_governor.py status  [--json]               pct estimate, lower bound, per-host split, coverage
  account_governor.py check --action arm|topup|resume|relaunch|deterministic
                                                     exit 0 ALLOW, exit 3 REFUSE

Source precedence (BAMR, 2026-11-20):
  1. OFFICIAL -- the harness's own `rate_limits` (seven_day, five_hour), copied by hooks/statusline_quota_tap.js
     into quota-reading.json. Used when captured within `official_fresh_s` and its window has not reset since.
     Weekly refuses at >= 85% (15% Owner reserve); five_hour at >= 100 - five_hour_reserve_pct (default 20).
     No five_hour key in a fresh reading = the provider reports no 5-hour window for this account (claude-swap
     upstream semantics), judged on the weekly window alone.
  2. ESTIMATE -- API-eq spend of the configured hosts over the calibration. Measured 2026-11-20: the estimate read
     83.58% while the official weekly reading was 18%, so it is a fallback, never a peer of (1).
  3. UNKNOWN -- neither usable (no/stale/absent official reading AND estimate without calibration, without a
     reset, or with any configured host missing/stale/older than `host_fresh_s`). Owner decision 2026-11-20:
     unknown blocks autonomous model spend: REFUSE+UNKNOWN (exit 3). It was ALLOW+UNKNOWN until then.
Action `deterministic` (work that spends no model quota) is always allowed. A valid Owner override (reason,
`until` within 24 h) lifts any refusal. Only configured hosts are summed: a stray file under another name
(measured 2026-11-20: `measure` without --host wrote DESKTOP-PMT5BS8.json beside laptop.json -> 126%) is
reported in `unexpected_hosts`, never summed, and `measure` refuses an unconfigured host name.
State lives in --state-dir (default ~/.claude/state): account-governor.json (config), account-governor-override.json,
account-governor-ledger.jsonl, account-governor-hosts/<host>.json, quota-reading.json (official, written by the tap).
Kill switch for the fail-closed change only: CPP_GOVERNOR_UNKNOWN=allow restores ALLOW+UNKNOWN.
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
OFFICIAL_FILE = "quota-reading.json"      # written by hooks/statusline_quota_tap.js on every statusline render
OFFICIAL_FRESH_S = 900                    # a reading older than this is STALE (config: official_fresh_s)
HOST_FRESH_S = 3 * 3600                   # a host measurement older than this makes coverage PARTIAL (config: host_fresh_s)
FIVE_HOUR_RESERVE_PCT = 20.0              # Owner decision 3 (2026-11-20); config: five_hour_reserve_pct
# Owner 2026-11-21 ("todo lo que promueva la autonomia responsable y que no se bloqueen ni queden paradas las
# misiones"): a mission CLOSEOUT -- one bounded worker that only writes the handoff a held mission needs to move
# again -- may spend the Owner reserve band, never the last 3 %. Unknown quota still refuses it.
CLOSEOUT_REFUSE_PCT = 97.0
SPEND_ACTIONS = ("arm", "topup", "resume", "relaunch", "closeout")
ACTIONS = SPEND_ACTIONS + ("deterministic",)


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


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def cfg_num(cfg, key, default):
    v = _num(cfg.get(key))
    return default if v is None or v < 0 else v


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


def official_reading(state_dir, now, fresh_s=OFFICIAL_FRESH_S):
    """The harness's own quota picture, or why it is not usable. Never fitted, never inferred."""
    j = load_json(os.path.join(state_dir, OFFICIAL_FILE))
    if not isinstance(j, dict):
        return {"state": "UNKNOWN", "why": "no official reading (%s absent or unreadable)" % OFFICIAL_FILE}
    if j.get("source") != "harness_statusline" or not isinstance(j.get("rate_limits"), dict):
        return {"state": "UNKNOWN", "why": "harness sent no rate_limits (source=%s)" % j.get("source")}
    at = _num(j.get("captured_at"))
    if at is None:
        return {"state": "UNKNOWN", "why": "official reading has no captured_at"}
    age = now - at
    if age > fresh_s:
        return {"state": "STALE", "why": "official reading is %.0f s old (> %.0f s)" % (age, fresh_s), "age_s": round(age)}
    windows, rolled = {}, []
    for name in ("seven_day", "five_hour"):
        w = j["rate_limits"].get(name)
        pct = _num(w.get("used_percentage")) if isinstance(w, dict) else None
        if pct is None:
            continue
        resets = _num(w.get("resets_at"))
        if resets is not None and resets <= now:
            rolled.append(name)   # the window reset after the reading: it says nothing about the new one
            continue
        windows[name] = {"pct": pct, "resets_at": resets}
    if "seven_day" not in windows:
        why = "weekly window rolled since the reading" if "seven_day" in rolled else "reading carries no seven_day window"
        return {"state": "UNKNOWN", "why": why, "age_s": round(age)}
    return {"state": "FRESH", "age_s": round(age), "windows": windows, "rolled": rolled}


def status(state_dir, now=None, roots=None, infer=True):
    """Merged weekly picture. Never raises on missing telemetry: it reports what it could not know.

    `infer=False` (every admission `check`) never scans transcripts: without a configured reset the estimate is
    UNKNOWN. Measured 2026-11-20: inference walks every transcript under ~/.claude/projects, >180 s per call,
    and the mission sweep would have paid that on every launch decision."""
    now = time.time() if now is None else now
    cfg = config(state_dir)
    calib = cfg.get("calibration_api_eq_per_100pct")
    if not isinstance(calib, (int, float)) or isinstance(calib, bool) or calib <= 0:
        calib = None
    reset, reset_src = current_window(parse_when(cfg.get("reset_at")), now), "config"
    if reset is None and infer:
        reset, reset_src = infer_reset(roots or ccn_census.default_roots(), now), "inferred (>=2h zero-call gap)"
    hosts_expected = tuple(cfg.get("hosts") or EXPECTED_HOSTS)
    host_fresh_s = cfg_num(cfg, "host_fresh_s", HOST_FRESH_S)
    per_host, stale, old, unexpected = {}, [], [], []
    for h, j in host_files(state_dir).items():
        if h not in hosts_expected:
            unexpected.append(h)   # never summed: one host under two names double-counts its spend
            continue
        v, since = j.get("api_eq_usd"), parse_when(j.get("reset_at"))
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        if reset is not None and since is not None and abs(since - reset) > 3600:
            stale.append(h)   # measured against a different window: not summable
            continue
        at = _num(j.get("measured_at"))
        if at is not None and now - at > host_fresh_s:
            old.append(h)     # a valid lower bound, but its growth since is unknown
        per_host[h] = round(float(v), 4)
    missing = [h for h in hosts_expected if h not in per_host]
    lower_usd = round(sum(per_host.values()), 4)
    full = not missing and not old
    res = {"reset_at": reset, "reset_source": reset_src if reset is not None else "UNKNOWN",
           "calibration_api_eq_per_100pct": calib, "calibration_label": "ESTIMATE" if calib else "MISSING",
           "per_host_api_eq_usd": per_host, "missing_hosts": missing, "stale_hosts": stale, "old_hosts": old,
           "unexpected_hosts": unexpected,
           "coverage": "FULL" if full else ("NONE" if not per_host else "PARTIAL"),
           "lower_bound_usd": lower_usd, "pct_lower_bound": None, "pct_estimate": None, "confidence": "UNKNOWN"}
    off = official_reading(state_dir, now, cfg_num(cfg, "official_fresh_s", OFFICIAL_FRESH_S))
    res["official"] = off
    if off["state"] == "FRESH" and full and off["windows"]["seven_day"]["pct"] > 0:
        # what the calibration would be if the official weekly reading is true; reported, never written to config
        res["implied_calibration_api_eq_per_100pct"] = round(lower_usd / (off["windows"]["seven_day"]["pct"] / 100.0), 2)
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


def decide(st, override, action, five_hour_refuse_pct=100.0 - FIVE_HOUR_RESERVE_PCT):
    """(exit code, verdict, why). 0 ALLOW, 3 REFUSE. Official reading first, estimate second, unknown refuses."""
    if action == "deterministic":
        return 0, "ALLOW+DETERMINISTIC", "deterministic work spends no model quota"
    off = st.get("official") or {"state": "UNKNOWN", "why": "no official reading"}
    weekly_refuse = CLOSEOUT_REFUSE_PCT if action == "closeout" else REFUSE_PCT
    if action == "closeout":
        five_hour_refuse_pct = max(five_hour_refuse_pct, CLOSEOUT_REFUSE_PCT)
    if off["state"] == "FRESH":
        w7, w5 = off["windows"]["seven_day"], off["windows"].get("five_hour")
        breaches = []
        if w7["pct"] >= weekly_refuse:
            breaches.append("official weekly %.1f%% >= %.0f%%" % (w7["pct"], weekly_refuse))
        if w5 is not None and w5["pct"] >= five_hour_refuse_pct:
            breaches.append("official 5h %.1f%% >= %.0f%% (Owner 5h reserve)" % (w5["pct"], five_hour_refuse_pct))
        if breaches:
            if override[0]:
                return 0, "ALLOW+OVERRIDE", "%s but Owner override active: %s" % ("; ".join(breaches), override[1])
            return 3, "REFUSE", "%s refused: %s; override absent or invalid (%s)" % (action, "; ".join(breaches), override[1])
        return 0, "ALLOW+OFFICIAL", "official weekly %.1f%%, %s (reading %ss old)" % (
            w7["pct"], "5h %.1f%%" % w5["pct"] if w5 else "no 5h window reported", off.get("age_s"))
    lo, est = st["pct_lower_bound"], st["pct_estimate"]
    if lo is None or st["coverage"] != "FULL":
        why = "official %s (%s); estimate %s" % (off["state"], off.get("why"), "unreadable (%s)" % (
            "no calibration" if st["calibration_api_eq_per_100pct"] is None else "no spend or reset")
            if lo is None else "coverage %s (missing %s, old %s)" % (st["coverage"], st["missing_hosts"], st.get("old_hosts")))
        if override[0]:
            return 0, "ALLOW+OVERRIDE", "quota unknown -- %s -- Owner override active: %s" % (why, override[1])
        if os.environ.get("CPP_GOVERNOR_UNKNOWN", "").lower() == "allow":
            return 0, "ALLOW+UNKNOWN", "quota unknown -- %s -- kill switch CPP_GOVERNOR_UNKNOWN=allow" % why
        return 3, "REFUSE+UNKNOWN", "%s refused: quota unknown -- %s (Owner decision 2026-11-20: unknown is never zero)" % (action, why)
    if lo >= weekly_refuse:
        if override[0]:
            return 0, "ALLOW+OVERRIDE", "lower bound %.1f%% >= %.0f%% but Owner override active: %s" % (lo, weekly_refuse, override[1])
        return 3, "REFUSE", "%s refused: weekly lower bound %.1f%% >= %.0f%% (Owner Q2); override file absent or invalid (%s)" % (
            action, lo, weekly_refuse, override[1])
    if est is not None and est >= weekly_refuse:
        return 0, "ALLOW+WARN", "estimate %.1f%% >= %.0f%% but the measured lower bound is %.1f%%" % (est, weekly_refuse, lo)
    return 0, "ALLOW", "lower bound %.1f%%, estimate %.1f%%" % (lo, est)


def append_ledger(state_dir, row):
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, "account-governor-ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def check(state_dir, action, now=None, roots=None):
    now = time.time() if now is None else now
    st = status(state_dir, now, roots, infer=bool(roots))   # admission never scans the real transcript store
    five_refuse = 100.0 - cfg_num(config(state_dir), "five_hour_reserve_pct", FIVE_HOUR_RESERVE_PCT)
    code, verdict, why = decide(st, read_override(state_dir, now), action, five_refuse)
    off = st.get("official") or {}
    append_ledger(state_dir, {"ts": now, "action": action, "verdict": verdict, "exit": code, "why": why,
                              "pct_lower_bound": st["pct_lower_bound"], "pct_estimate": st["pct_estimate"],
                              "coverage": st["coverage"], "official_state": off.get("state"),
                              "official_windows": off.get("windows")})
    return code, verdict, why, st


def cmd_measure(a):
    now = time.time()
    cfg = config(a.state_dir)
    hosts = tuple(cfg.get("hosts") or EXPECTED_HOSTS)
    host = a.host or socket.gethostname()
    if host not in hosts:
        print("measure: host %r is not one of the configured hosts %s; pass --host <one of them>. "
              "Nothing written (a second name for one host double-counts its spend)." % (host, list(hosts)), file=sys.stderr)
        return 2
    a.host = host
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
    m.add_argument("--host", default=None, help="one of the configured hosts (default: this machine's name, refused if unconfigured)")
    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--action", choices=ACTIONS, required=True)
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
