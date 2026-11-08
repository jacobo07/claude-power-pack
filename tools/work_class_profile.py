"""Work-class profile: a settled work unit updates its class profile BEFORE the next unit is forecast.

    settle   --class C --unit U --processed N --calls N --avg-ctx N --max-ctx N --attempts N --attempts-failed N
             [--forecast N] --cause TEXT       append one sample + receipt (idempotent per unit)
    forecast --class C [--calls N]             p50/p80/p95 + confidence from the settled samples
    calibrate --class C                        mean abs pct error and surprise rate over settled receipts

Sibling of ccr_pgo.py: that module learns a class from raw transcripts (build/heldout); this one records the ACTUAL
of every completed unit so the next forecast moves. With fewer than 3 samples no quantile is invented: p50 is the
median, p80/p95 are None and `basis` says so. Cost of an unseen class is UNKNOWN (confidence NONE), never zero.
`lease_forecast` is the number to hand to phase_lease.make_lease.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}")
P95_MIN_N = 10


class ProfileError(ValueError):
    pass


def store_dir() -> Path:
    d = os.environ.get("CPP_WORK_CLASS_PROFILE_DIR")
    return Path(d) if d else Path.home() / ".claude" / "state" / "work-class-profile"


def _name(kind: str, v) -> str:
    v = str(v or "").strip()
    if not _NAME.fullmatch(v) or ".." in v:
        raise ProfileError(f"{kind} must be a plain name, not {v!r}")
    return v


def _count(name: str, v, positive=False) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or v < 0 or (positive and v == 0):
        raise ProfileError(f"{name} must be a {'positive' if positive else 'non-negative'} integer, not {v!r}")
    return v


def _path(cls: str) -> Path:
    return store_dir() / f"{cls}.json"


def _load(cls: str) -> dict:
    p = _path(cls)
    if not p.is_file():
        return {"cls": cls, "samples": []}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d.get("samples"), list):
            return d
    except (OSError, ValueError) as exc:
        # an unreadable profile must not read as an empty one: the next settle would overwrite the history
        raise ProfileError(f"profile {p} is unreadable ({type(exc).__name__}); refusing to treat it as empty")
    raise ProfileError(f"profile {p} has no samples list; refusing to treat it as empty")


def _save(cls: str, doc: dict) -> None:
    p = _path(cls)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{cls}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    k = (len(s) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo))  # token counts are integers


def _floor() -> int:
    try:
        d = json.loads((HERE.parent / "vault" / "config" / "route-floors.json").read_text(encoding="utf-8"))
        return int(d["profiles"]["top-level-worker"]["floor"])
    except (OSError, ValueError, KeyError, TypeError):
        return 110835  # measured 2026-10-06 (m-8bbdf725cd52 first call); only used if the config is unreadable


def _stats(samples: list[dict]) -> dict:
    xs = [s["processed"] for s in samples]
    n = len(xs)
    out = {"n": n, "p50": None, "p80": None, "p95": None, "confidence": "NONE", "basis": "no settled samples"}
    if n == 0:
        return out
    out["p50"] = _quantile(xs, 0.5)
    if n < 3:
        out.update(confidence="LOW", basis=f"fewer than 3 settled samples (n={n}): p50 is the median, "
                                           "p80/p95 not estimated")
        return out
    out["p80"] = _quantile(xs, 0.8)
    if n >= P95_MIN_N:
        out["p95"] = _quantile(xs, 0.95)
    out["confidence"] = "HIGH" if n >= 10 else "MEDIUM"
    out["basis"] = f"empirical quantiles over n={n} settled samples" + ("" if n >= P95_MIN_N else
                                                                       f"; p95 needs n>={P95_MIN_N}")
    return out


def forecast(work_class: str, calls: int | None = None) -> dict:
    cls = _name("work_class", work_class)
    samples = _load(cls)["samples"]
    out = _stats(samples)
    out["work_class"] = cls
    out["structural"] = None
    if calls is not None:
        calls = _count("calls", calls, positive=True)
        growth = [s["avg_ctx"] - _floor() for s in samples if isinstance(s.get("avg_ctx"), int)]
        g = max(0.0, _quantile(growth, 0.5)) if growth else 0.0
        out["structural"] = round(calls * (_floor() + g))
        out["structural_basis"] = f"calls x (floor {_floor()} + median growth {round(g)})"
    return out


def settle_unit(work_class: str, unit_id: str, actual: dict, forecast: int | None = None, cause: str = "") -> dict:
    """Append one sample (idempotent per unit_id) and return its receipt. The profile is durable on return, so the
    next forecast() already includes this unit."""
    cls, uid = _name("work_class", work_class), _name("unit_id", unit_id)
    a = {k: _count(k, actual.get(k), positive=(k == "processed")) for k in ("processed", "calls")}
    for k in ("avg_ctx", "max_ctx", "attempts", "attempts_failed"):
        a[k] = _count(k, actual.get(k, 0))
    if forecast is not None:
        forecast = _count("forecast", forecast, positive=True)
    doc = _load(cls)
    for s in doc["samples"]:
        if s["unit_id"] == uid:
            return dict(s["receipt"], idempotent=True)
    p80 = _stats(doc["samples"])["p80"]
    ratio = a["processed"] / forecast if forecast else None
    receipt = {"work_class": cls, "unit_id": uid, "forecast": forecast, "actual": a["processed"],
               "variance_ratio": ratio, "abs_pct_error": abs(a["processed"] - forecast) / forecast if forecast else None,
               "p80_at_settle": p80, "cause": str(cause or "")[:500], "settled_at": time.time(), "idempotent": False}
    doc["samples"].append(dict(a, unit_id=uid, receipt=receipt))
    _save(cls, doc)
    return receipt


def calibration(work_class: str) -> dict:
    cls = _name("work_class", work_class)
    rs = [s["receipt"] for s in _load(cls)["samples"]]
    errs = [r["abs_pct_error"] for r in rs if r.get("abs_pct_error") is not None]
    p80s = [r for r in rs if r.get("p80_at_settle") is not None]
    return {"work_class": cls, "units": len(rs), "units_with_forecast": len(errs),
            "mean_abs_pct_error": sum(errs) / len(errs) if errs else None,
            "units_with_p80": len(p80s),
            "surprise_rate": sum(1 for r in p80s if r["actual"] > r["p80_at_settle"]) / len(p80s) if p80s else None}


def lease_forecast(work_class: str, calls: int | None = None) -> dict:
    """The integer for phase_lease.make_lease: p80 when estimated, else the largest settled sample (a forecast
    below something already observed would be a pre-spent lease). Unknown class -> ProfileError, no number."""
    f = forecast(work_class, calls)
    if f["n"] == 0:
        raise ProfileError(f"no settled samples for {f['work_class']}: no forecast to lease against")
    if f["p80"] is not None:
        return {"forecast": round(f["p80"]), "basis": f"p80 over n={f['n']} ({f['confidence']})"}
    mx = max(s["processed"] for s in _load(f["work_class"])["samples"])
    return {"forecast": int(mx), "basis": f"max of n={f['n']} settled samples ({f['confidence']}; no p80)"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("settle")
    s.add_argument("--class", dest="cls", required=True)
    s.add_argument("--unit", required=True)
    for k in ("processed", "calls", "avg-ctx", "max-ctx", "attempts", "attempts-failed"):
        s.add_argument(f"--{k}", type=int, required=True)
    s.add_argument("--forecast", type=int)
    s.add_argument("--cause", required=True)
    f = sub.add_parser("forecast")
    f.add_argument("--class", dest="cls", required=True)
    f.add_argument("--calls", type=int)
    c = sub.add_parser("calibrate")
    c.add_argument("--class", dest="cls", required=True)
    x = ap.parse_args(argv)
    try:
        if x.cmd == "settle":
            r = settle_unit(x.cls, x.unit, {"processed": x.processed, "calls": x.calls, "avg_ctx": x.avg_ctx,
                                            "max_ctx": x.max_ctx, "attempts": x.attempts,
                                            "attempts_failed": x.attempts_failed}, forecast=x.forecast, cause=x.cause)
        elif x.cmd == "forecast":
            r = forecast(x.cls, x.calls)
        else:
            r = calibration(x.cls)
    except ProfileError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
