#!/usr/bin/env python3
"""cost_gate.py -- W5: pre-launch CONTEXT cost gate (Claude Max => not money).

The Owner is on Claude Max (flat rate): marginal $/token = 0. So this gate is
about CONTEXT efficiency, not spend. Three advisories, each independently
fail-open to silence:

  1. DAILY BURN -- real output_tokens generated today, read ONLY from the
     transcripts via token_ground_truth (the single valid source; SCS C53 +
     UKDL T-TCO-TRACKING-GAP-001). budget_monitor (programmatic credits) and
     TIS (JIT-injection size) are WRONG for this and are never consulted.
     Over the threshold (default 100M out/day) -> suggest /compact.
  2. COMPRESSION -- if context_monitor flags pressure for the cwd's latest
     transcript, estimate the live context size (the latest turn's real
     input+cache_read tokens) that /compact would reclaim.
  3. MODEL HINT -- opt-in: only when a task `description` is supplied (there is
     none at pre-launch), classify_tier(description) Tier 0-1 -> suggest Haiku.
     classify_tier is description-based, NOT cwd-based, so cwd alone stays silent.

Returns a list of advisory lines (empty == silent). NEVER raises, NEVER mocks,
NEVER fabricates a number: a missing measurement yields silence, not a fake 0.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# 100M output tokens/day -- well above the measured ~49.5M real daily output
# (vault/audits/token_usage_2026-06-23.md), so it only fires on a genuinely
# heavy day. Configurable.
DEFAULT_OUTPUT_THRESHOLD = 100_000_000

# Weekly-burn dashboard (D1, Weekly-Burn-RCA 2026-06-30). Output tokens are the
# dominant Claude-Max cost driver; these are the empirical anchors from the
# forensic (vault/plans/weekly-limit-burn-rca-2026-06-30.md):
#   - June measured average output/day = 13.5M (per-turn ts, 29 active days).
#   - The 48h burn was 49.2M output == "74% of the weekly limit" per the Owner,
#     so the weekly output-equivalent limit ~= 49.2M / 0.74 ~= 66M. This is an
#     OWNER-DERIVED ESTIMATE (Anthropic's exact weekly weighting is not exposed
#     in transcripts), configurable, used only for an advisory projection.
HIST_DAILY_OUTPUT_AVG = 13_500_000
WEEKLY_OUTPUT_LIMIT_EST = 66_000_000
ELEVATED_FACTOR = 1.5      # 24h rate above this * the June avg -> "elevated"


@dataclass
class CostGate:
    lines: list = field(default_factory=list)   # advisory strings (empty=silent)
    burn_output_today: int | None = None
    source: str = "silent"                       # advisory | silent | error


@dataclass
class WeeklyBurn:
    burn_24h: int | None = None
    burn_7d: int | None = None
    rate_factor: float | None = None   # 24h burn / June daily avg
    days_left: float | None = None     # at the 24h rate, days to exhaust limit
    elevated: bool = False
    line: str | None = None            # advisory string, or None (silent)


def weekly_burn(proj_base=None, now=None, *,
                hist_daily_avg: int = HIST_DAILY_OUTPUT_AVG,
                weekly_limit: int = WEEKLY_OUTPUT_LIMIT_EST,
                elevated_factor: float = ELEVATED_FACTOR,
                w24_fn=None, w7_fn=None) -> WeeklyBurn:
    """Real weekly burn + projection from per-turn transcript output (D1).

    Fires the advisory when the last-24h output rate exceeds
    `elevated_factor` * the June daily average. The projection ("limite agotado
    en ~N dias") uses the 24h rate against the remaining weekly allowance.
    Fail-open: any missing measurement -> silent (line=None), never a fake 0.
    """
    try:
        if w24_fn is None or w7_fn is None:
            from tools.token_ground_truth import window_output  # type: ignore
        b24 = (w24_fn or (lambda: window_output(24, proj_base, now)))()
        b7 = (w7_fn or (lambda: window_output(24 * 7, proj_base, now)))()
        if not isinstance(b24, int) or hist_daily_avg <= 0:
            return WeeklyBurn(burn_24h=b24, burn_7d=b7)
        factor = b24 / hist_daily_avg
        # Projection: at the current 24h rate, how many days does ONE weekly
        # allowance last? = weekly_limit / burn_24h. Reset-anchor-free and fully
        # real (a trailing-7d sum would span weekly resets and falsely read
        # "exhausted"). days_left < 7 => the current pace cannot last a week.
        days_left = (weekly_limit / b24) if b24 > 0 else None
        elevated = factor >= elevated_factor
        line = None
        if elevated:
            proj = (f" A este ritmo una asignacion semanal dura ~{days_left:.1f} "
                    f"dias{' (insostenible, <7)' if days_left < 7 else ''}."
                    if days_left is not None else "")
            line = (f"PP: burn semanal elevado -- {factor:.1f}x el ritmo normal "
                    f"(~{b24 / 1_000_000:.0f}M out/24h vs "
                    f"~{hist_daily_avg / 1_000_000:.0f}M media).{proj} "
                    f"Considera prompts mas pequenos o pausar build no urgente.")
        return WeeklyBurn(burn_24h=b24, burn_7d=b7, rate_factor=factor,
                          days_left=days_left, elevated=elevated, line=line)
    except Exception:  # noqa: BLE001 -- fail-open
        return WeeklyBurn()


def _latest_context_tokens(cwd: str, proj_base=None):
    """Live context size = the most-recent transcript's LAST turn
    (input_tokens + cache_read_input_tokens). Real number; what /compact would
    shrink. None if unreadable. Imports lazily to keep fail-open tight."""
    try:
        from tools.token_ground_truth import iter_transcripts  # type: ignore
        files = iter_transcripts(proj_base or (Path.home() / ".claude" / "projects"))
        cwd_enc = None
        import re
        cwd_enc = re.sub(r"[^a-zA-Z0-9]", "-", cwd or "")
        cands = [f for f in files if f.parent.name == cwd_enc]
        if not cands:
            return None
        latest = max(cands, key=lambda f: f.stat().st_mtime)
        last_usage = None
        for line in latest.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = e.get("message")
            if isinstance(msg, dict) and isinstance(msg.get("usage"), dict):
                last_usage = msg["usage"]
        if not last_usage:
            return None
        return (last_usage.get("input_tokens", 0)
                + last_usage.get("cache_read_input_tokens", 0))
    except Exception:  # noqa: BLE001
        return None


def cost_gate(cwd: str, *, description: str | None = None,
              output_threshold: int = DEFAULT_OUTPUT_THRESHOLD,
              now: datetime | None = None, proj_base=None,
              burn_fn=None, assess_fn=None, context_fn=None,
              classify_fn=None) -> CostGate:
    """Compose the three advisories. Every block is independently fail-open."""
    lines: list[str] = []
    burn = None

    # 1. daily burn -- transcripts only (token_ground_truth)
    try:
        if burn_fn is None:
            from tools.token_ground_truth import today_output_tokens as burn_fn  # type: ignore
        burn = burn_fn(proj_base=proj_base, now=now)
        if isinstance(burn, int) and burn > output_threshold:
            lines.append(
                f"PP: has generado ~{burn / 1_000_000:.0f}M tokens de salida "
                f"hoy. Considera /compact en sesiones largas.")
    except Exception:  # noqa: BLE001
        pass

    # 2. compression -- only if context_monitor flags pressure for this cwd
    try:
        if assess_fn is None:
            from modules.cpc_os.context_monitor import assess as assess_fn  # type: ignore
        decision = assess_fn(cwd, None)
        state = decision.get("state", "HEALTHY") if isinstance(decision, dict) else "HEALTHY"
        if state != "HEALTHY":
            ctx = (context_fn or _latest_context_tokens)(cwd, proj_base)
            if isinstance(ctx, int) and ctx > 0:
                lines.append(
                    f"PP: /compact reclamaria ~{ctx / 1000:.0f}k tokens de "
                    f"contexto en esta sesion ({state}).")
    except Exception:  # noqa: BLE001
        pass

    # 3b. weekly burn -- real per-turn output, projection to limit (D1).
    #     Independent fail-open; only a line when the 24h rate is elevated.
    try:
        wb = weekly_burn(proj_base=proj_base, now=now)
        if wb.line:
            lines.append(wb.line)
    except Exception:  # noqa: BLE001
        pass

    # 3. model hint -- opt-in (needs a task description; cwd alone stays silent)
    if description:
        try:
            if classify_fn is None:
                from modules.spec_gate.gate import classify_tier as classify_fn  # type: ignore
            tr = classify_fn(description)
            if tr.tier <= 1:
                lines.append(
                    f"PP: tarea Tier {tr.tier} ({tr.reason}) -- Haiku basta, "
                    f"reserva Opus para Tier 2+.")
        except Exception:  # noqa: BLE001
            pass

    return CostGate(lines=lines, burn_output_today=burn,
                    source="advisory" if lines else "silent")


def main(argv=None) -> int:
    import argparse
    import os
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--description", default=None)
    ap.add_argument("--threshold", type=int, default=DEFAULT_OUTPUT_THRESHOLD)
    args = ap.parse_args(argv)
    g = cost_gate(args.cwd or os.getcwd(), description=args.description,
                  output_threshold=args.threshold)
    for ln in g.lines:
        print(ln)
    if not g.lines:
        print(f"# silent (burn_today={g.burn_output_today})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
