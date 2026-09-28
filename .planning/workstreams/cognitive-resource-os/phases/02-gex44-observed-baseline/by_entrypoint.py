#!/usr/bin/env python3
"""by_entrypoint.py -- read-only evidence reproducer for Phase 2 (GEX44 observed baseline).

Read-only. Composes tools/tis_observed, tools/budget_monitor, tools/pricing_source and
tools/tis_report; adds grouping only, with no parsing of usage, no dedupe and no pricing of
its own. Prints aggregates only (no paths, no session ids, no transcript text). An evidence
reproducer, not a tool.

Usage:
  python3 by_entrypoint.py             # measure this host's real transcripts, print JSON
  python3 by_entrypoint.py --selftest  # synthetic fixture, no real transcript is read
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# .../02-gex44-observed-baseline/by_entrypoint.py -> parents[5] is the repo/worktree root:
# 0 phases/02-.../ (self.parent), 1 phases/, 2 cognitive-resource-os/, 3 workstreams/,
# 4 .planning/, 5 repo root.
ROOT = Path(__file__).resolve().parents[5]

# Populated by _ensure_tools_importable(), never at module-import time (WR-04): a bare
# `import by_entrypoint` (e.g. Phase 4 reusing measure()) must not print or sys.exit.
T = bm = pricing_source = tis_report = None

passes = fails = 0


def _ensure_tools_importable() -> None:
    """Idempotent. Verifies the repo layout, adds tools/ to sys.path, and imports the
    composed tools into this module's globals. Called from main()/selftest() only --
    never at module-import time -- so importing this module for its measure() function
    is import-safe (WR-04): no stdout write, no sys.exit as a side effect of `import
    by_entrypoint`."""
    global T, bm, pricing_source, tis_report
    if T is not None:
        return
    if not (ROOT / "tools" / "tis_observed.py").is_file():
        print(json.dumps({"state": "UNMEASURED", "reason": "repo root not found"}))
        sys.exit(2)
    sys.path.insert(0, str(ROOT / "tools"))
    import tis_observed as _T
    import budget_monitor as _bm
    import pricing_source as _pricing_source
    import tis_report as _tis_report
    T, bm, pricing_source, tis_report = _T, _bm, _pricing_source, _tis_report

# A zero-valued but truthy price table. Used solely to pull the `ttl_assumed` boolean out
# of T.cost_usd's own composition (cache_creation breakdown present or not) without
# re-deriving that check here, and without needing a real price for the call's model.
_ZERO_PRICES = {"input": 0.0, "output": 0.0, "cache_write_5m": 0.0,
                "cache_write_1h": 0.0, "cache_read": 0.0}


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"  [PASS] {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"  [FAIL] {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def _iso(d: dt.datetime) -> str:
    return d.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_relative(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def _median(values):
    return statistics.median(values) if values else None


def _reconcile_val(a, b, tol: float = 0.0) -> str:
    ok = (abs(a - b) < tol) if tol else (a == b)
    return "MATCH" if ok else f"MISMATCH a={a} b={b}"


def _reconcile_pair(a1, b1, a2, b2) -> str:
    if a1 == b1 and a2 == b2:
        return "MATCH"
    return f"MISMATCH a=({a1},{a2}) b=({b1},{b2})"


def _entrypoints_in_file(path: Path) -> set:
    """The one raw-line read in this file: distinct `entrypoint` values seen across every
    line of one transcript. tis_observed only keeps the FIRST value; this exists purely to
    check the one-entrypoint-per-file contract (Defect case c), never to attribute calls."""
    eps: set = set()
    try:
        with open(path, encoding="utf-8-sig") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict) and obj.get("entrypoint"):
                    eps.add(obj["entrypoint"])
    except OSError:
        pass
    return eps


def _all_files(dirs) -> list:
    files = []
    for d in dirs:
        d = Path(d)
        for p in sorted(d.glob("*.jsonl")):
            files.append(p)
            sub = p.parent / p.stem / "subagents"
            if sub.is_dir():
                files.extend(sorted(sub.glob("*.jsonl")))
    return files


def _cache_write_split(usage: dict):
    cc = T._int(usage.get("cache_creation_input_tokens"))
    br = usage.get("cache_creation")
    w1 = T._int(br.get("ephemeral_1h_input_tokens")) if isinstance(br, dict) else 0
    return cc, w1


def _is_ttl_assumed(usage: dict) -> bool:
    _, assumed = T.cost_usd(usage, _ZERO_PRICES)
    return assumed


def _usd_1h_only(usage: dict, prices) -> float:
    _, w1 = _cache_write_split(usage)
    if w1 <= 0 or not prices:
        return 0.0
    synth = {"cache_creation_input_tokens": w1,
             "cache_creation": {"ephemeral_5m_input_tokens": 0,
                                "ephemeral_1h_input_tokens": w1}}
    usd, _ = T.cost_usd(synth, prices)
    return usd if usd is not None else 0.0


def _by_entrypoint_all_time(sessions: list) -> dict:
    groups: dict = {}
    for s in sessions:
        key = (s.entrypoint or "unknown") if s.state == "MEASURED" else f"({s.state})"
        groups.setdefault(key, []).append(s)
    out = {}
    for key, group in groups.items():
        g = T.summarize(group)
        measured_calls = [s.calls for s in group if s.state == "MEASURED"]
        out[key] = {
            "sessions": g["sessions"],
            "by_state": g["by_state"],
            "calls": g["calls"],
            "subagent_calls": g["subagent_calls"],
            "first_call_context_median": g["startup_context_median"],
            "startup_shared_share_median": g["startup_shared_share_median"].get(key),
            "calls_per_session_median": _median(measured_calls),
        }
    return out


def _by_entrypoint_trailing_7d(dirs, cutoff_ts, models, pricing_ok, entrypoint_keys) -> dict:
    calls_by_group: dict = {}
    for c in T.iter_calls(dirs, modified_since=cutoff_ts):
        ts = bm._parse_iso(c.get("ts") or "")
        if ts is None or ts.timestamp() < cutoff_ts:
            continue
        key = c.get("entrypoint") or "unknown"
        calls_by_group.setdefault(key, []).append(c)

    out = {}
    for key in sorted(set(entrypoint_keys) | set(calls_by_group.keys())):
        calls = calls_by_group.get(key, [])
        if not calls:
            out[key] = {
                "state_7d": "MEASURED_ZERO", "sessions": 0, "calls": 0,
                "calls_per_session_median": None, "sessions_le2_calls": 0,
                "usd": (0.0 if pricing_ok else None),
                "usd_1h_write": (0.0 if pricing_ok else None),
                "share_1h_write_usd": None,
                "cache_write_tokens": 0, "cache_write_1h_tokens": 0,
                "share_1h_write_tokens": None,
                "ttl_assumed_calls": 0, "unpriced_calls": 0, "unpriced_models": [],
                "usd_by_model": {},
            }
            continue

        per_session: dict = {}
        usd_total = 0.0
        usd_1h_total = 0.0
        cache_write_tokens = 0
        cache_write_1h_tokens = 0
        ttl_assumed = 0
        unpriced_calls = 0
        unpriced_models: list = []
        usd_by_model: dict = {}
        for c in calls:
            usage = c["usage"]
            model = c["model"]
            sid = c["session_id"]
            per_session[sid] = per_session.get(sid, 0) + 1
            cc, w1 = _cache_write_split(usage)
            cache_write_tokens += cc
            cache_write_1h_tokens += w1
            if _is_ttl_assumed(usage):
                ttl_assumed += 1
            prices = models.get(model)
            if pricing_ok and prices:
                usd, _assumed = T.cost_usd(usage, prices)
                # T.cost_usd (tools/tis_observed.py) returns None only when `not prices`,
                # which the `pricing_ok and prices` guard above already excludes -- usd
                # cannot be None here. Assert loudly instead of a silently-unreachable
                # `if usd is None` arm, so a future contract change (e.g. a malformed
                # price row) surfaces immediately rather than mis-summing (WR-03).
                assert usd is not None, (
                    f"cost_usd returned None for model={model!r} despite truthy prices "
                    "-- cost_usd's None-contract changed, update this guard")
                usd_total += usd
                usd_by_model[model] = usd_by_model.get(model, 0.0) + usd
                usd_1h_total += _usd_1h_only(usage, prices)
            else:
                unpriced_calls += 1
                if model not in unpriced_models:
                    unpriced_models.append(model)

        sessions_le2 = sum(1 for n in per_session.values() if n <= 2)
        out[key] = {
            "state_7d": "MEASURED",
            "sessions": len(per_session),
            "calls": len(calls),
            "calls_per_session_median": _median(list(per_session.values())),
            "sessions_le2_calls": sessions_le2,
            "usd": (round(usd_total, 6) if pricing_ok else None),
            "usd_1h_write": (round(usd_1h_total, 6) if pricing_ok else None),
            "share_1h_write_usd": (round(usd_1h_total / usd_total, 6)
                                    if pricing_ok and usd_total else None),
            "cache_write_tokens": cache_write_tokens,
            "cache_write_1h_tokens": cache_write_1h_tokens,
            "share_1h_write_tokens": (round(cache_write_1h_tokens / cache_write_tokens, 6)
                                       if cache_write_tokens else None),
            "ttl_assumed_calls": ttl_assumed,
            "unpriced_calls": unpriced_calls,
            "unpriced_models": unpriced_models,
            "usd_by_model": {m: round(v, 6) for m, v in usd_by_model.items()},
        }
    return out


_NATIVE_KEYS = ("sessions", "by_state", "calls", "subagent_calls",
                "startup_context_median", "startup_context_min", "startup_context_max",
                "startup_prefix_share_estimate", "startup_shared_share_median",
                "duplicate_usage_lines_collapsed", "synthetic_skipped", "bad_lines")


def _build_scope(scope_dirs, cutoff_ts, models, pricing_ok) -> dict:
    sessions = T.scan(scope_dirs)
    at = _by_entrypoint_all_time(sessions)
    native = T.summarize(sessions)
    native_restricted = {k: native[k] for k in _NATIVE_KEYS}
    real_keys = [k for k in at if not (k.startswith("(") and k.endswith(")"))]
    t7 = _by_entrypoint_trailing_7d(scope_dirs, cutoff_ts, models, pricing_ok, real_keys)
    return {"all_time": {"native_summary": native_restricted, "by_entrypoint": at},
            "trailing_7d": {"by_entrypoint": t7}}


def measure(dirs, own_dir, now_ts, pricing, pricing_meta) -> dict:
    """Pure function of its inputs. Composes tis_observed/budget_monitor/tis_report; adds
    grouping only. Field names are exact -- Task 2's verify reads them."""
    dirs = [Path(d) for d in dirs]
    cutoff_ts = now_ts - bm.BURN_WINDOW_DAYS * 86400
    models = (pricing or {}).get("models") or {}
    pricing_ok = pricing is not None

    now_dt_ = dt.datetime.fromtimestamp(now_ts, dt.timezone.utc)
    cutoff_dt = dt.datetime.fromtimestamp(cutoff_ts, dt.timezone.utc)

    result: dict = {
        "source": "observed",
        "measured_at_utc": _iso(now_dt_),
        "cutoff_utc": _iso(cutoff_dt),
        "window_days": bm.BURN_WINDOW_DAYS,
        "pricing": {
            "file": pricing_meta.get("file"),
            "status": pricing_meta.get("status"),
            "fetched_iso": pricing_meta.get("fetched_iso"),
        },
    }

    # -- corpus (no mtime prune: every call from T.iter_calls(dirs)) --
    all_calls = list(T.iter_calls(dirs))
    call_ts = []
    for c in all_calls:
        ts = bm._parse_iso(c.get("ts") or "")
        if ts is not None:
            call_ts.append(ts)
    session_files = sum(1 for d in dirs for _ in Path(d).glob("*.jsonl"))
    subagent_files = 0
    for d in dirs:
        for p in Path(d).glob("*.jsonl"):
            sub = p.parent / p.stem / "subagents"
            if sub.is_dir():
                subagent_files += len(list(sub.glob("*.jsonl")))
    earliest = min(call_ts) if call_ts else None
    latest = max(call_ts) if call_ts else None
    result["corpus"] = {
        "project_dirs": len(dirs),
        "session_files": session_files,
        "subagent_files": subagent_files,
        "earliest_call_utc": _iso(earliest) if earliest else None,
        "latest_call_utc": _iso(latest) if latest else None,
        "span_days": (latest - earliest).days if earliest and latest else None,
    }

    # -- assumption_checks (global, over `dirs`) --
    files = _all_files(dirs)
    multi_entrypoint_files = sum(1 for f in files if len(_entrypoints_in_file(f)) > 1)
    calls_without_ttl_split = sum(1 for c in all_calls if _is_ttl_assumed(c["usage"]))
    win_calls = []
    for c in all_calls:
        ts = bm._parse_iso(c.get("ts") or "")
        if ts is not None and ts.timestamp() >= cutoff_ts:
            win_calls.append(c)
    sess_eps: dict = {}
    for c in win_calls:
        sess_eps.setdefault(c["session_id"], set()).add(c.get("entrypoint") or "unknown")
    sessions_under_multiple_entrypoints_7d = sum(1 for eps in sess_eps.values() if len(eps) > 1)
    unpriced_models_7d = {c["model"] for c in win_calls if not models.get(c["model"])}
    result["assumption_checks"] = {
        "multi_entrypoint_files": multi_entrypoint_files,
        "calls_without_ttl_split": calls_without_ttl_split,
        "sessions_under_multiple_entrypoints_7d": sessions_under_multiple_entrypoints_7d,
        "unpriced_models_7d": len(unpriced_models_7d),
    }

    # -- scopes --
    own_dir_present = bool(own_dir) and Path(own_dir).is_dir()
    if own_dir:
        own_resolved = str(Path(own_dir).resolve())
        excl_dirs = [d for d in dirs if str(Path(d).resolve()) != own_resolved]
    else:
        excl_dirs = list(dirs)

    scope_all = _build_scope(dirs, cutoff_ts, models, pricing_ok)
    scope_excl = _build_scope(excl_dirs, cutoff_ts, models, pricing_ok)
    scope_excl["own_dir_present"] = own_dir_present

    result["scopes"] = {"all_projects": scope_all,
                        "excluding_this_repo_project_dir": scope_excl}

    # -- reconcile (all_projects only) --
    reconcile: dict = {}
    native = scope_all["all_time"]["native_summary"]
    at = scope_all["all_time"]["by_entrypoint"]
    sum_sessions = sum(g["sessions"] for g in at.values())
    sum_calls = sum(g["calls"] for g in at.values())
    reconcile["R1"] = _reconcile_val(sum_sessions, native["sessions"])
    reconcile["R2"] = _reconcile_val(sum_calls, native["calls"])

    r3_bad = []
    for key, g in at.items():
        if key.startswith("(") and key.endswith(")"):
            continue
        native_val = native["startup_shared_share_median"].get(key)
        if g["startup_shared_share_median"] != native_val:
            r3_bad.append(f"{key}: a={g['startup_shared_share_median']} b={native_val}")
    reconcile["R3"] = "MATCH" if not r3_bad else "MISMATCH " + "; ".join(r3_bad)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        tis_report.main(["--observed", "--all-projects"])
    try:
        r4_json = json.loads(buf.getvalue())
        r4_sessions = r4_json["summary"]["sessions"]
        r4_calls = r4_json["summary"]["calls"]
        reconcile["R4"] = _reconcile_pair(r4_sessions, native["sessions"],
                                          r4_calls, native["calls"])
    except Exception as exc:
        reconcile["R4"] = f"MISMATCH error={type(exc).__name__}: {exc}"

    bm_agg = bm._aggregate_observed(bm.BURN_WINDOW_DAYS, pricing, project_dirs=dirs)
    t7_all = scope_all["trailing_7d"]["by_entrypoint"]
    sdkcli_calls = t7_all.get("sdk-cli", {}).get("calls", 0)
    reconcile["R5"] = _reconcile_val(sdkcli_calls, bm_agg.get("calls", 0))
    if not pricing_ok:
        reconcile["R6"] = f"SKIPPED pricing {pricing_meta.get('status')}"
    else:
        sdkcli_usd = t7_all.get("sdk-cli", {}).get("usd") or 0.0
        reconcile["R6"] = _reconcile_val(sdkcli_usd, bm_agg.get("usd", 0.0), tol=1e-6)

    overall = "MATCH"
    for k, v in reconcile.items():
        if v.startswith("SKIPPED"):
            continue
        if v != "MATCH":
            overall = "MISMATCH"
            break
    reconcile["overall"] = overall
    result["reconcile"] = reconcile

    return result


def _write_session(path: Path, entrypoint: str, calls: list):
    """calls: list of {mid, rid, ts, model (default claude-test), usage}."""
    lines = [json.dumps({"type": "user", "entrypoint": entrypoint, "message": {"content": "x"}})]
    for c in calls:
        msg = {"model": c.get("model", "claude-test"), "usage": c["usage"]}
        if c.get("mid") is not None:
            msg["id"] = c["mid"]
        obj = {"type": "assistant", "message": msg}
        if c.get("ts") is not None:
            obj["timestamp"] = c["ts"]
        if c.get("rid") is not None:
            obj["requestId"] = c["rid"]
        lines.append(json.dumps(obj))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def selftest() -> int:
    _ensure_tools_importable()

    # S0 (WR-04): a bare `import by_entrypoint` in a fresh subprocess must not print or
    # sys.exit -- that side effect used to run unconditionally at module-import time.
    # Checked in a subprocess (not this process) since this process already imported the
    # module and mutated sys.path; a subprocess re-imports cold.
    proc = subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path.insert(0, {str(HERE)!r}); "
                                "import by_entrypoint"],
        capture_output=True, text=True, timeout=30)
    s0 = proc.returncode == 0 and proc.stdout == "" and proc.stderr == ""
    check("S0", s0,
          f"rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proj1 = root / "proj1"
        proj2 = root / "proj2"
        proj1.mkdir()
        proj2.mkdir()

        now_ts = time.time()
        now_dt_ = dt.datetime.fromtimestamp(now_ts, dt.timezone.utc)

        def iso(delta_days=0):
            return _iso(now_dt_ - dt.timedelta(days=delta_days))

        # S1 fixture: proj1 cli session (2 calls, first has cc=900/cr=100 -> ctx 1000, share 0.1).
        _write_session(proj1 / "sessA.jsonl", "cli", [
            {"mid": "a1", "rid": "ra1", "ts": iso(1),
             "usage": {"input_tokens": 0, "cache_creation_input_tokens": 900,
                       "cache_read_input_tokens": 100, "output_tokens": 10}},
            {"mid": "a2", "rid": "ra2", "ts": iso(1),
             "usage": {"input_tokens": 100, "cache_creation_input_tokens": 0,
                       "cache_read_input_tokens": 0, "output_tokens": 50}},
        ])
        # proj2 sdk-cli session: one call 30d old, one call 1d old that is a pure 1h write.
        _write_session(proj2 / "sessB.jsonl", "sdk-cli", [
            {"mid": "b1", "rid": "rb1", "ts": iso(30),
             "usage": {"input_tokens": 10, "output_tokens": 5}},
            {"mid": "b2", "rid": "rb2", "ts": iso(1),
             "usage": {"input_tokens": 0, "output_tokens": 0,
                       "cache_creation_input_tokens": 1000000,
                       "cache_creation": {"ephemeral_5m_input_tokens": 0,
                                          "ephemeral_1h_input_tokens": 1000000}}},
        ])
        # proj2 transcript with no real call (MEASURED_ZERO).
        (proj2 / "sessC.jsonl").write_text(
            json.dumps({"type": "user", "message": {"content": "x"}}) + "\n", encoding="utf-8")

        prices = {"claude-test": {"input": 2.0, "output": 10.0, "cache_write_5m": 2.5,
                                   "cache_write_1h": 20.0, "cache_read": 0.2}}
        pricing = {"models": prices}
        pricing_meta = {"file": "vault/pricing/test.json", "status": "ok", "fetched_iso": iso(0)}

        old_pd = T.PROJECTS_DIR
        T.PROJECTS_DIR = root
        try:
            dirs = [proj1, proj2]
            res = measure(dirs, proj1, now_ts, pricing, pricing_meta)

            at = res["scopes"]["all_projects"]["all_time"]["by_entrypoint"]
            rec = res["reconcile"]
            s1 = (at.get("cli", {}).get("sessions") == 1 and at["cli"]["calls"] == 2
                  and at.get("sdk-cli", {}).get("sessions") == 1 and at["sdk-cli"]["calls"] == 2
                  and at.get("(MEASURED_ZERO)", {}).get("sessions") == 1
                  and rec["R1"] == "MATCH" and rec["R2"] == "MATCH")
            check("S1", s1,
                  f"cli={at.get('cli')} sdk-cli={at.get('sdk-cli')} "
                  f"mz={at.get('(MEASURED_ZERO)')} R1={rec['R1']} R2={rec['R2']}")

            s2 = (at["cli"]["startup_shared_share_median"] == 0.1 and rec["R3"] == "MATCH")
            check("S2", s2,
                  f"cli_share={at['cli']['startup_shared_share_median']} R3={rec['R3']}")

            t7 = res["scopes"]["all_projects"]["trailing_7d"]["by_entrypoint"]
            sdk7 = t7.get("sdk-cli", {})
            s3 = (sdk7.get("calls") == 1 and sdk7.get("usd") == 20.0
                  and sdk7.get("usd_1h_write") == 20.0
                  and sdk7.get("share_1h_write_usd") == 1.0
                  and sdk7.get("share_1h_write_tokens") == 1.0)
            check("S3", s3, f"{sdk7}")

            s4 = (rec["R5"] == "MATCH" and rec["R6"] == "MATCH")
            check("S4", s4, f"R5={rec['R5']} R6={rec['R6']}")

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc5 = tis_report.main(["--observed", "--all-projects"])
            s5 = (rec["R4"] == "MATCH" and rc5 == 0)
            check("S5", s5, f"R4={rec['R4']} rc5={rc5}")

            mism = _reconcile_val(5, 6)
            s6 = mism.startswith("MISMATCH")
            check("S6", s6, mism)

            excl = res["scopes"]["excluding_this_repo_project_dir"]
            s7 = ("cli" not in excl["all_time"]["by_entrypoint"]
                  and excl["own_dir_present"] is True)
            check("S7", s7,
                  f"keys={list(excl['all_time']['by_entrypoint'].keys())} "
                  f"own_dir_present={excl['own_dir_present']}")

            proj3 = root / "proj3"
            proj3.mkdir()
            _write_session(proj3 / "sessD.jsonl", "sdk-cli", [
                {"mid": "d1", "rid": "rd1", "ts": iso(1), "model": "claude-unknown",
                 "usage": {"input_tokens": 100, "output_tokens": 10}},
            ])
            res8 = measure([proj1, proj2, proj3], proj1, now_ts, pricing, pricing_meta)
            t7_8 = res8["scopes"]["all_projects"]["trailing_7d"]["by_entrypoint"]["sdk-cli"]
            s8 = (t7_8["unpriced_calls"] == 1 and t7_8["usd"] == 20.0)
            check("S8", s8, f"unpriced_calls={t7_8['unpriced_calls']} usd={t7_8['usd']}")

            dumped = json.dumps(res)
            s9 = (str(root) not in dumped and "sessA" not in dumped
                  and "sessB" not in dumped and "sessC" not in dumped)
            check("S9", s9, "no fixture path or session id in json.dumps(result)")
        finally:
            T.PROJECTS_DIR = old_pd

    print(f"BYEP_SELFTEST_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    _ensure_tools_importable()
    now_ts = bm._utc_now().timestamp()
    if not T.PROJECTS_DIR.is_dir():
        print(json.dumps({"state": "UNMEASURED", "reason": "no transcripts dir"}))
        return 2
    dirs = sorted(p for p in T.PROJECTS_DIR.iterdir() if p.is_dir())
    if not dirs:
        print(json.dumps({"state": "UNMEASURED", "reason": "no project dirs"}))
        return 2

    pricing, pricing_status = bm._load_pricing()
    try:
        pricing_file = _repo_relative(pricing_source.current_pricing_path())
    except FileNotFoundError:
        pricing_file = None
    fetched_iso = pricing.get("fetched_iso") if pricing else None
    pricing_meta = {"file": pricing_file, "status": pricing_status, "fetched_iso": fetched_iso}

    own_dir = T.PROJECTS_DIR / T.project_key(str(ROOT))
    result = measure(dirs, own_dir, now_ts, pricing, pricing_meta)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
