#!/usr/bin/env python3
"""TCO Compact Gate -- A1 threshold (70%) + Model Router CLI.

Read-only intelligence layer over `tools/tis.py` event log. No
mutation, no daemon, no scheduler. Stdlib pure. Fail-open on any
ingest error (a cost-visibility tool must never block real work).

CLI:
    python tools/tco_compact_gate.py
        -> current session context-pct estimate + recommendation

    python tools/tco_compact_gate.py --route subagent_explore
        -> recommended model id for the task_type

    python tools/tco_compact_gate.py --route-skill Explore
        -> recommended model id for the SKILL name (uses skill_to_task_type)

    python tools/tco_compact_gate.py --json
        -> machine-readable state (for hooks / verify_spp).

Decisions encoded:
    A1 -- single 70% warn threshold (aligned with global CLAUDE.md
          Context Pressure Response). No hard-stop tier; one source
          of truth.
    B3 -- routing JSON consumed here; per-skill recommendation
          surfaced via --route-skill.
    C2 -- governor warning emitted when session-duration or
          tokens-this-session crosses derived threshold.

This module imports tis lazily so it is callable even when the TIS
log is empty (cold-start safe).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROUTING_PATH = ROOT / "vault" / "config" / "model-routing.json"

WARN_PCT = 70
MAX_CONTEXT_TOKENS = 200_000

SESSION_TOKEN_WARN = 100_000
SESSION_DURATION_WARN_S = 2 * 60 * 60


def _load_routing() -> dict:
    if not ROUTING_PATH.is_file():
        return {
            "default_model": "claude-opus-4-7",
            "rules": [],
            "skill_to_task_type": {},
        }
    try:
        return json.loads(ROUTING_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {
            "default_model": "claude-opus-4-7",
            "rules": [],
            "skill_to_task_type": {},
        }


def load_routing(task_type: str) -> str:
    """Return recommended model id for a task_type. Default = opus."""
    cfg = _load_routing()
    default = cfg.get("default_model", "claude-opus-4-7")
    for r in cfg.get("rules", []):
        if r.get("task_type") == task_type:
            return r.get("recommended_model", default)
    return default


def route_skill(skill_name: str) -> tuple[str, str]:
    """Return (recommended_model, task_type) for a skill name.

    Unknown skill -> (default_model, "unmapped").
    """
    cfg = _load_routing()
    smap = cfg.get("skill_to_task_type", {})
    task_type = smap.get(skill_name)
    if task_type is None:
        return cfg.get("default_model", "claude-opus-4-7"), "unmapped"
    return load_routing(task_type), task_type


def route_prompt(prompt: str) -> dict | None:
    """Wire modules.cost_collapse.router into the TCO surface.

    Returns a cheap-first routing recommendation for a raw prompt, or
    None when the Cost Collapse module is unavailable (fail-open -- a
    cost-visibility tool must never block real work). MICRO (the
    default route) returns None too: no advice needed for the common
    case, only NANO (route down to Haiku) and MACRO/ULTRA (route up to
    Opus) are worth surfacing.
    """
    if not prompt:
        return None
    try:
        from modules.cost_collapse.router import route, RouteClass
    except (ImportError, ModuleNotFoundError):
        return None
    try:
        r = route(prompt)
    except Exception:
        return None
    if r.route_class == RouteClass.NANO:
        return {
            "route_class": "NANO",
            "model": r.model,
            "max_budget": r.max_budget,
            "advice": (
                f"Cost route: {r.model} -- trivial task, Haiku suggested "
                f"(<= ${r.max_budget:g})."
            ),
        }
    if r.route_class in (RouteClass.MACRO, RouteClass.ULTRA):
        return {
            "route_class": r.route_class.name,
            "model": r.model,
            "max_budget": r.max_budget,
            "advice": (
                f"Cost route: {r.model} -- complex task, high reasoning "
                f"tier (budget <= ${r.max_budget:g})."
            ),
        }
    return None  # MICRO -> default, no advice


def _read_session_entries(session_id: str | None = None) -> list[dict]:
    """Best-effort read of TIS log for the active session. Empty list
    on any failure -- callers handle the cold-start case."""
    try:
        from tools import tis  # type: ignore
    except (ImportError, ModuleNotFoundError):
        try:
            import tis  # type: ignore
        except (ImportError, ModuleNotFoundError):
            return []
    try:
        sid = session_id or tis.get_session_id()
        return [e for e in tis.read_log() if e.get("session_id") == sid]
    except Exception:
        return []


def _transcript_calls(session_id: str | None) -> list[dict]:
    """MEASURED per-call usage from the session's own transcript, deduplicated by message id.

    Measured 2026-09-27: the TIS log holds no model usage at all -- only the JIT hook's
    chars/4 estimate of the prompt it saw -- and its session id is a sidecar never rotated,
    so the TIS path reported 30 M "session" tokens over 124 days while this session's real
    context was 552 k. The transcript carries the API's own usage for every call."""
    import os
    sid = session_id or os.environ.get("CLAUDE_CODE_SESSION_ID") or ""
    if len(sid) < 32:          # a TIS sidecar id (8 chars) names no transcript
        return []
    hits = list((Path.home() / ".claude" / "projects").glob(f"*/{sid}.jsonl"))
    if not hits:
        return []
    seen, calls = set(), []
    try:
        with open(hits[0], encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                msg = rec.get("message") or {}
                u = msg.get("usage")
                if rec.get("type") != "assistant" or not u or msg.get("id") in seen:
                    continue
                seen.add(msg.get("id"))
                cr = int(u.get("cache_read_input_tokens") or 0)
                cw = int(u.get("cache_creation_input_tokens") or 0)
                inp = int(u.get("input_tokens") or 0)
                calls.append({"ctx": cr + cw + inp, "cache_read": cr, "cache_write": cw,
                              "input": inp, "output": int(u.get("output_tokens") or 0),
                              "ts": rec.get("timestamp") or ""})
    except OSError:
        return []
    return calls


def _context_window(calls: list[dict]) -> int:
    """The window the session runs in, from evidence: an explicit override, the configured
    [1m] model, or an observed call larger than 200 k (which only a 1 M window admits)."""
    import os
    override = os.environ.get("CPP_CONTEXT_WINDOW", "")
    if override.isdigit():
        return int(override)
    try:
        model = json.loads((Path.home() / ".claude" / "settings.json").read_text(
            encoding="utf-8-sig")).get("model", "")
    except (OSError, ValueError):
        model = ""
    if "[1m]" in str(model) or any(c["ctx"] > MAX_CONTEXT_TOKENS for c in calls):
        return 1_000_000
    return MAX_CONTEXT_TOKENS


def _measured_state(calls: list[dict]) -> dict:
    window = _context_window(calls)
    last = calls[-1]["ctx"]
    pct = max(0, min(100, int(last * 100 / window)))
    ts = []
    for c in calls:
        try:
            ts.append(datetime.fromisoformat(str(c["ts"]).replace("Z", "+00:00")))
        except ValueError:
            continue
    duration_s = int((max(ts) - min(ts)).total_seconds()) if len(ts) >= 2 else 0
    totals = {k: sum(c[k] for c in calls) for k in ("cache_read", "cache_write", "input", "output")}
    warns = []
    if duration_s > SESSION_DURATION_WARN_S:
        warns.append(f"session-duration {duration_s}s > {SESSION_DURATION_WARN_S}s "
                     f"(loop hygiene -- /compact every 2h)")
    if pct >= WARN_PCT:
        rec, should = (f"WARN: contexto medido {pct}% >= {WARN_PCT}% -- ejecuta /compact antes "
                       f"de spawnar subagents o continuar loops"), True
    else:
        rec, should = f"OK contexto medido {pct}% < {WARN_PCT}% -- continuar", False
    return {
        "source": "transcript-usage (measured)",
        "session_pct_estimate": pct,
        "context_window": window,
        "context_last_call": last,
        "context_first_call": calls[0]["ctx"],
        "session_calls": len(calls),
        "session_tokens_total": sum(totals.values()),
        "token_mix": totals,
        "session_duration_s": duration_s,
        "recommendation": rec,
        "should_compact": should,
        "governor_warnings": warns,
        "warn_threshold_pct": WARN_PCT,
        "session_duration_warn_s": SESSION_DURATION_WARN_S,
    }


def _compute_context_proxy(entries: list[dict]) -> int:
    """Proxy for *current* context window size, not cumulative session
    history. Uses the maximum input_tokens of the last 3 calls, falling
    back to half the global max if recent calls are anomalously small
    (e.g. trailing tool-result entries). Sealed 2026-05-28 after the
    cumulative-sum bug reported 100% when reality was ~10%.

    Rationale: the context size for any single turn is the input_tokens
    the model received that turn. Summing across the entire session
    inflates with every turn and is not a context-window measurement.
    """
    if not entries:
        return 0
    inputs = [int(e.get("input_tokens", 0) or 0) for e in entries]
    recent = inputs[-3:] if len(inputs) >= 3 else inputs
    max_recent = max(recent) if recent else 0
    max_global = max(inputs) if inputs else 0
    return max(max_recent, max_global // 2)


def estimate_context_pct(session_id: str | None = None) -> int:
    """Estimate % of max-context window consumed by the *current* turn.

    Uses MAX of last 3 input_tokens (with half-global fallback) as the
    proxy for current context size. NOT a cumulative sum across the
    session -- that confused historical tokens with live context and
    reported 100% on healthy sessions.
    """
    entries = _read_session_entries(session_id)
    if MAX_CONTEXT_TOKENS <= 0:
        return 0
    proxy = _compute_context_proxy(entries)
    pct = int(proxy * 100 / MAX_CONTEXT_TOKENS)
    return max(0, min(100, pct))


def _session_token_total(session_id: str | None = None) -> int:
    entries = _read_session_entries(session_id)
    return sum(int(e.get("input_tokens", 0) or 0) +
               int(e.get("output_tokens", 0) or 0) for e in entries)


def _session_duration_s(session_id: str | None = None) -> int:
    """Span between earliest and latest event timestamp for the
    active session. 0 if fewer than 2 events."""
    entries = _read_session_entries(session_id)
    if len(entries) < 2:
        return 0
    ts = []
    for e in entries:
        raw = e.get("timestamp_iso", "")
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            ts.append(dt)
        except ValueError:
            continue
    if len(ts) < 2:
        return 0
    return int((max(ts) - min(ts)).total_seconds())


def check_compact_gate(session_id: str | None = None) -> dict:
    """Return state dict: pct, recommendation, should_compact,
    governor warnings, raw token total, duration seconds. One log
    read shared across all three derived metrics."""
    calls = _transcript_calls(session_id)
    if calls:
        return _measured_state(calls)
    entries = _read_session_entries(session_id)
    # total: cumulative session tokens (governor metric, NOT context)
    total = sum(int(e.get("input_tokens", 0) or 0) +
                int(e.get("output_tokens", 0) or 0) for e in entries)
    # pct: live context proxy via MAX of last 3 input_tokens (sealed 2026-05-28)
    proxy = _compute_context_proxy(entries)
    pct = (max(0, min(100, int(proxy * 100 / MAX_CONTEXT_TOKENS)))
           if MAX_CONTEXT_TOKENS > 0 else 0)
    ts = []
    for e in entries:
        raw = e.get("timestamp_iso", "")
        if not raw:
            continue
        try:
            ts.append(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except ValueError:
            continue
    duration_s = (int((max(ts) - min(ts)).total_seconds())
                  if len(ts) >= 2 else 0)
    governor_warns: list[str] = []
    if total > SESSION_TOKEN_WARN:
        governor_warns.append(
            f"session-tokens {total} > {SESSION_TOKEN_WARN} (consider /compact)")
    if duration_s > SESSION_DURATION_WARN_S:
        governor_warns.append(
            f"session-duration {duration_s}s > {SESSION_DURATION_WARN_S}s "
            f"(loop hygiene -- /compact every 2h)")

    if pct >= WARN_PCT:
        rec = (f"WARN: contexto estimado {pct}% >= {WARN_PCT}% -- "
               f"ejecuta /compact antes de spawnar subagents o continuar loops")
        should_compact = True
    else:
        rec = f"OK contexto {pct}% < {WARN_PCT}% -- continuar"
        should_compact = False
    inputs_only = [int(e.get("input_tokens", 0) or 0) for e in entries]
    max_single_input = max(inputs_only) if inputs_only else 0
    return {
        "source": "tis-proxy (JIT prompt-size estimate; NOT model context)",
        "session_pct_estimate": pct,
        "session_tokens_total": total,
        "session_calls": len(entries),
        "context_max_single_input": max_single_input,
        "context_proxy_used": proxy,
        "session_duration_s": duration_s,
        "recommendation": rec,
        "should_compact": should_compact,
        "governor_warnings": governor_warns,
        "warn_threshold_pct": WARN_PCT,
        "session_token_warn": SESSION_TOKEN_WARN,
        "session_duration_warn_s": SESSION_DURATION_WARN_S,
    }


def _print_human(state: dict) -> None:
    print(f"source:                 {state.get('source', 'unknown')}")
    print(f"context-pct:            {state['session_pct_estimate']}%  "
          f"[warn>=70%]")
    if "context_window" in state:
        mix = state["token_mix"]
        print(f"context:                last={state['context_last_call']:,} "
              f"first={state['context_first_call']:,} window={state['context_window']:,}")
        print(f"token mix:              cache_read={mix['cache_read']:,} "
              f"cache_write={mix['cache_write']:,} input={mix['input']:,} output={mix['output']:,}")
    print(f"session-tokens:         {state['session_tokens_total']:,}")
    print(f"session-duration:       {state['session_duration_s']}s")
    print(f"recommendation:         {state['recommendation']}")
    # Debug line: surfaces the MAX vs SUM divergence visibly (sealed 2026-05-28)
    print(
        f"  [TCO debug] calls={state.get('session_calls', 0)}  "
        f"max_single_input={state.get('context_max_single_input', 0):,}  "
        f"proxy_used={state.get('context_proxy_used', 0):,}  "
        f"pct={state['session_pct_estimate']}%"
    )
    if state["governor_warnings"]:
        print("governor:")
        for w in state["governor_warnings"]:
            print(f"  - {w}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="TCO Compact Gate + Model Router CLI")
    p.add_argument("--route", metavar="TASK_TYPE",
                   help="Print recommended model id for a task_type")
    p.add_argument("--route-skill", metavar="SKILL_NAME",
                   help="Print recommended model id for a skill name")
    p.add_argument("--route-prompt", metavar="PROMPT",
                   help="Cheap-first route recommendation for a raw prompt "
                        "(wires modules.cost_collapse.router)")
    p.add_argument("--json", action="store_true",
                   help="Emit machine-readable JSON state")
    p.add_argument("--session", metavar="SID", default=None,
                   help="Override session id (default = active TIS session)")
    p.add_argument("--session-start-check", action="store_true",
                   help="SessionStart hook entry: emit advisory only "
                        "when context_pct >= WARN_PCT, silent otherwise. "
                        "Always exit 0 (fail-open).")
    args = p.parse_args(argv)

    if args.session_start_check:
        try:
            state = check_compact_gate(args.session)
            pct = int(state.get("session_pct_estimate", 0) or 0)
        except Exception:
            return 0
        if pct < WARN_PCT:
            return 0
        msg = (
            f"[Jobs] [pp-tco-advisor] Session-start context proxy at "
            f"{pct}% (warn threshold {WARN_PCT}%).\n"
            f"Carry-over from prior turn -- consider /compact before the "
            f"first heavy task.\n"
            f"-> python tools/tco_compact_gate.py for the full breakdown."
        )
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": msg,
            }
        }
        print(json.dumps(payload))
        return 0

    if args.route:
        model = load_routing(args.route)
        if args.json:
            print(json.dumps({"task_type": args.route, "model": model}))
        else:
            print(model)
        return 0

    if args.route_skill:
        model, task_type = route_skill(args.route_skill)
        if args.json:
            print(json.dumps({"skill": args.route_skill,
                              "task_type": task_type,
                              "model": model}))
        else:
            print(f"{model}  (task_type={task_type})")
        return 0

    if args.route_prompt:
        rec = route_prompt(args.route_prompt)
        if args.json:
            print(json.dumps(rec if rec else {"route_class": "MICRO",
                                              "advice": None}))
        else:
            print(rec["advice"] if rec else
                  "MICRO (default route) -- Sonnet, no cost advice needed")
        return 0

    state = check_compact_gate(args.session)
    if args.json:
        state["captured_iso"] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(state, indent=2))
    else:
        _print_human(state)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
