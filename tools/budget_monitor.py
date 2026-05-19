#!/usr/bin/env python3
"""budget_monitor.py - Programmatic-credit runway tracker.

From 2026-06-15 Anthropic moves programmatic Claude usage (Agent SDK,
`claude -p`, GitHub Actions, third-party orchestrators) off the
subscription bucket and onto a separate metered credit ($20 Pro / $100
Max 5x / $200 Max 20x) priced at full API rates. This monitor reads:

  * Owner-seeded ~/.claude/budget.json
      {tier, monthly_usd, refill_iso, model_default}
  * Externalized pricing vault/pricing/anthropic_2026-05.json
      (fetched_iso older than 30d -> refuse compute, emit 'stale-pricing')
  * Real telemetry JSONL files in vault/telemetry/
      jit_usage_*.jsonl  (token counts per JIT injection)
      rtk_*.jsonl        (raw vs rtk-wrapped Bash-output tokens)

...and computes the real runway in days at the trailing 7d burn rate.

Precedence: env ANTHROPIC_PROGRAMMATIC_BUDGET_USD > file monthly_usd >
'unconfigured' (no fabricated number). The winning source is logged into
every JSONL row so the result is reproducible.

Honest failure modes (sentinels, never silent zero or infinity):
  * config missing            -> status='unconfigured'
  * pricing stale (>30 days)  -> status='stale-pricing'
  * telemetry n<3 rows        -> status='INSUFFICIENT_TELEMETRY'
  * empty/zero burn           -> runway_days=null with reason

Writes vault/telemetry/budget-<ISO>.jsonl. NOT self-registered (auto-mode
classifier denies agent hook self-registration); Owner registers as a
SessionStart hook via tools/settings_merger.py or manual settings.json.

Usage:
  python tools/budget_monitor.py             # writes JSONL + prints summary
  python tools/budget_monitor.py --quiet     # JSONL only, no stdout
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import math
import os
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = Path(__file__).resolve().parents[1]
BUDGET_FILE = HOME / ".claude" / "budget.json"
PRICING_FILE = PP_ROOT / "vault" / "pricing" / "anthropic_2026-05.json"
TELEMETRY_DIR = PP_ROOT / "vault" / "telemetry"

STALE_PRICING_DAYS = 30
MIN_TELEMETRY_ROWS = 3
BURN_WINDOW_DAYS = 7
ENV_BUDGET_OVERRIDE = "ANTHROPIC_PROGRAMMATIC_BUDGET_USD"


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso_now() -> str:
    return _utc_now().replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")


def _parse_iso(s: str) -> dt.datetime | None:
    if not isinstance(s, str) or not s:
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d
    except Exception:
        return None


def _load_budget_config() -> tuple[dict | None, str]:
    """Returns (config_dict_or_None, winning_source).

    Precedence: ENV ANTHROPIC_PROGRAMMATIC_BUDGET_USD > file > unconfigured.
    """
    env_val = os.environ.get(ENV_BUDGET_OVERRIDE)
    if env_val:
        try:
            usd = float(env_val)
            return ({"tier": "env-override", "monthly_usd": usd,
                     "refill_iso": "", "model_default": "claude-opus-4-7"},
                    f"env:{ENV_BUDGET_OVERRIDE}")
        except (TypeError, ValueError):
            return (None, "env-malformed")
    if not BUDGET_FILE.is_file():
        return (None, "file-absent")
    try:
        cfg = json.loads(BUDGET_FILE.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return (None, f"file-malformed:{type(exc).__name__}")
    required = ("tier", "monthly_usd")
    for k in required:
        if k not in cfg:
            return (None, f"file-missing-key:{k}")
    if not isinstance(cfg.get("monthly_usd"), (int, float)) \
            or cfg["monthly_usd"] <= 0:
        return (None, "file-invalid:monthly_usd")
    if cfg.get("tier") not in ("pro", "max5x", "max20x", "env-override"):
        return (None, f"file-invalid:tier={cfg.get('tier')!r}")
    cfg.setdefault("model_default", "claude-opus-4-7")
    cfg.setdefault("refill_iso", "")
    return (cfg, "file:~/.claude/budget.json")


def _load_pricing() -> tuple[dict | None, str]:
    if not PRICING_FILE.is_file():
        return (None, "pricing-absent")
    try:
        p = json.loads(PRICING_FILE.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return (None, f"pricing-malformed:{type(exc).__name__}")
    fetched = _parse_iso(p.get("fetched_iso", ""))
    if fetched is None:
        return (None, "pricing-no-fetched-iso")
    age = (_utc_now() - fetched).days
    if age > STALE_PRICING_DAYS:
        return (None, f"stale-pricing:{age}d-old")
    return (p, "ok")


def _iter_jsonl(pattern: str):
    """Yield (path, parsed_row) for matching JSONL files."""
    if not TELEMETRY_DIR.is_dir():
        return
    for fp in TELEMETRY_DIR.glob(pattern):
        try:
            for ln in fp.read_text(encoding="utf-8-sig").splitlines():
                if not ln.strip():
                    continue
                try:
                    row = json.loads(ln)
                except Exception:
                    continue
                yield fp, row
        except Exception:
            continue


def _row_tokens(row: dict) -> int:
    """Extract approx token count from a JIT usage row.

    The loader writes `bytes` per injection (not tokens). Convert via
    cl100k ratio approx (~4 chars/token). Honest fallback: if row has
    explicit `tokens` or `size_tok`, prefer those.
    """
    if isinstance(row.get("tokens"), (int, float)):
        return int(row["tokens"])
    if isinstance(row.get("size_tok"), (int, float)):
        return int(row["size_tok"])
    b = row.get("bytes")
    if isinstance(b, (int, float)) and b > 0:
        return math.ceil(b / 4)
    return 0


def _aggregate_burn(window_days: int) -> dict:
    """Sum injected JIT tokens + RTK Bash-output tokens over window."""
    cutoff = _utc_now().timestamp() - (window_days * 86400)
    jit_input = 0
    jit_output = 0
    rtk_raw = 0
    rtk_compressed = 0
    n_rows = 0
    for _, row in _iter_jsonl("jit_usage_*.jsonl"):
        ts = row.get("ts")
        if not isinstance(ts, (int, float)) or ts < cutoff:
            continue
        n_rows += 1
        jit_input += _row_tokens(row)
    for _, row in _iter_jsonl("rtk_*.jsonl"):
        ts = row.get("ts")
        if not isinstance(ts, (int, float)) or ts < cutoff:
            continue
        n_rows += 1
        rtk_raw += int(row.get("raw_tok") or 0)
        rtk_compressed += int(row.get("rtk_tok") or 0)
    return {
        "n_rows": n_rows,
        "jit_input_tok": jit_input,
        "jit_output_tok": jit_output,
        "rtk_raw_tok": rtk_raw,
        "rtk_compressed_tok": rtk_compressed,
    }


def _compute_runway(cfg: dict, pricing: dict, burn: dict) -> dict:
    model = cfg.get("model_default", "claude-opus-4-7")
    prices = (pricing.get("models") or {}).get(model)
    if not prices:
        return {"status": f"unknown-model:{model}", "runway_days": None}
    if burn["n_rows"] < MIN_TELEMETRY_ROWS:
        return {"status": "INSUFFICIENT_TELEMETRY",
                "runway_days": None,
                "reason": f"n={burn['n_rows']}<{MIN_TELEMETRY_ROWS}"}
    in_price_per_tok = prices["input"] / 1_000_000.0
    out_price_per_tok = prices["output"] / 1_000_000.0
    daily_burn_usd = (
        (burn["jit_input_tok"] * in_price_per_tok
         + burn["jit_output_tok"] * out_price_per_tok)
        / max(1, BURN_WINDOW_DAYS)
    )
    if daily_burn_usd <= 0:
        return {"status": "zero-burn-in-window",
                "runway_days": None,
                "daily_burn_usd": 0.0}
    runway = cfg["monthly_usd"] / daily_burn_usd
    return {"status": "ok",
            "runway_days": round(runway, 2),
            "daily_burn_usd": round(daily_burn_usd, 4),
            "monthly_usd": cfg["monthly_usd"],
            "model": model}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true",
                    help="suppress stdout summary (JSONL still written)")
    args = ap.parse_args()

    cfg, cfg_source = _load_budget_config()
    pricing, pricing_status = _load_pricing()
    burn = _aggregate_burn(BURN_WINDOW_DAYS)

    if cfg is None:
        runway = {"status": f"unconfigured:{cfg_source}",
                  "runway_days": None}
    elif pricing is None:
        runway = {"status": pricing_status, "runway_days": None}
    else:
        runway = _compute_runway(cfg, pricing, burn)

    row = {
        "ts": _utc_now().timestamp(),
        "iso": _iso_now(),
        "config_source": cfg_source,
        "pricing_status": pricing_status,
        "burn_window_days": BURN_WINDOW_DAYS,
        "burn": burn,
        "result": runway,
    }
    try:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        out = TELEMETRY_DIR / ("budget-" + row["iso"].replace(":", "")
                                + ".jsonl")
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        if not args.quiet:
            print(f"[budget_monitor] telemetry write failed: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)

    if args.quiet:
        return 0
    status = runway.get("status", "?")
    days = runway.get("runway_days")
    print(f"=== Programmatic Budget Monitor ({row['iso']}) ===")
    print(f"  config: {cfg_source}")
    print(f"  pricing: {pricing_status}")
    print(f"  trailing-{BURN_WINDOW_DAYS}d telemetry rows: {burn['n_rows']}")
    if status == "ok":
        print(f"  daily burn: ${runway['daily_burn_usd']:.4f} "
              f"on model={runway['model']}")
        print(f"  monthly budget: ${runway['monthly_usd']:.2f}")
        print(f"  RUNWAY: {days} days at current rate")
    else:
        print(f"  RUNWAY: unmeasured ({status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
