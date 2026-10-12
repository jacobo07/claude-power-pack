"""CCR v4 B3: attribute a worker's context carry to row kinds, fitted against the provider's exact deltas.

Between call k and call k+1 the provider context grows by exactly the tokens of the rows appended in between
(assistant message k: text, tool_use inputs, thinking blocks; then the user rows: tool results, images). This
fits tokens = sum(rate_kind * size_kind) over every step of the given claude stream-json transcripts (least
squares, no intercept, rates clipped at 0), then charges each step's rows for the calls they ride.

Sizes only: thinking is measured by its block sizes (text and signature), never by reading its content.
A kind the fit does not know shows up as residual, so the residual is reported, never folded into a kind.

    python tools/ccr_carry_fit.py <worker.stream.jsonl> [...] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

KINDS = ["tool_result", "assistant_text", "tool_input", "thinking_text", "thinking_sig", "images"]
MAX_TOK_PER_CHAR = 1.0  # physical ceiling for any text kind; images are per image and uncapped
# Mass that rides every step alike cannot be told apart from a kind present on every step (no intercept, positive
# rows): it inflates that kind's rate instead of the residual. So the readable kinds carry a tokenization band, and
# a rate outside it marks the fit IMPLAUSIBLE. Band anchor: the B5 canary measured 0.585 tok/char on a path listing.
PLAUSIBLE = {"tool_result": (0.2, 0.75), "assistant_text": (0.2, 0.75), "tool_input": (0.2, 0.75)}


def _blank() -> dict[str, int]:
    return {k: 0 for k in KINDS}


def steps_of(path: Path) -> tuple[list[int], list[tuple[int, dict[str, int]]]]:
    """Per-call provider context (deduped by message id) and, per step, (ctx delta, row sizes appended)."""
    calls: list[int] = []
    steps: list[tuple[int, dict[str, int]]] = []
    seen: set[str] = set()
    cur = _blank()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except ValueError:
                continue  # a torn or non-JSON line of the stream carries no row
            kind, msg = ev.get("type"), ev.get("message") or {}
            if kind == "assistant":
                mid = msg.get("id")
                if mid and mid not in seen:
                    seen.add(mid)
                    u = msg.get("usage") or {}
                    ctx = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                    if calls:
                        steps.append((ctx - calls[-1], cur))
                    calls.append(ctx)
                    cur = _blank()
                for b in msg.get("content") or []:
                    bt = b.get("type")
                    if bt == "text":
                        cur["assistant_text"] += len(b.get("text", ""))
                    elif bt == "tool_use":
                        cur["tool_input"] += len(json.dumps(b.get("input") or {}))
                    elif bt == "thinking":
                        cur["thinking_text"] += len(b.get("thinking", ""))
                        cur["thinking_sig"] += len(b.get("signature", ""))
                    elif bt == "redacted_thinking":
                        cur["thinking_sig"] += len(b.get("data", ""))
            elif kind == "user":
                for b in msg.get("content") or []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_result":
                        c = b.get("content")
                        if isinstance(c, str):
                            cur["tool_result"] += len(c)
                            continue
                        for x in c or []:
                            if x.get("type") == "text":
                                cur["tool_result"] += len(x.get("text", ""))
                            elif x.get("type") == "image":
                                cur["images"] += 1
                    elif b.get("type") == "text":
                        cur["assistant_text"] += len(b.get("text", ""))
    return calls, steps


def fit(per: dict[str, tuple[list[int], list]], drop: tuple[str, ...] = ()) -> dict:
    """drop: kinds left out of the model (an ablation: their mass must then appear as residual)."""
    all_steps = [s for _, steps in per.values() for s in steps]
    if not all_steps:
        return {"error": "no steps: every transcript has fewer than two calls"}
    X = np.array([[0 if k in drop else s[1][k] for k in KINDS] for s in all_steps], dtype=float)
    y = np.array([s[0] for s in all_steps], dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    coef = np.clip(coef, 0, None)
    # A kind present once per step (a tool_use input) acts as an intercept and can absorb mass no row shows.
    # No text costs more than one token per char, so a char rate above that is capped and the remaining kinds
    # refit; what is still unexplained stays in the residual (V-CCRFIT-HIDDEN-SURFACES-AS-RESIDUAL).
    capped = [j for j, k in enumerate(KINDS) if k != "images" and coef[j] > MAX_TOK_PER_CHAR]
    if capped:
        coef[capped] = MAX_TOK_PER_CHAR
        free = [j for j in range(len(KINDS)) if j not in capped]
        sub, *_ = np.linalg.lstsq(X[:, free], y - X[:, capped] @ coef[capped], rcond=None)
        coef[free] = np.clip(sub, 0, None)
    pred = X @ coef
    present = X.sum(axis=0) > 0
    implausible = [k for j, k in enumerate(KINDS) if k in PLAUSIBLE and present[j]
                   and not PLAUSIBLE[k][0] <= coef[j] <= PLAUSIBLE[k][1]]
    out = {"rates": {k: round(float(c), 4) for k, c in zip(KINDS, coef)}, "capped": [KINDS[j] for j in capped],
           "implausible": implausible, "verdict": "IMPLAUSIBLE" if implausible else "PLAUSIBLE", "dropped": list(drop), "steps": len(y),
           "delta": int(y.sum()), "abs_residual_pct": round(100 * float(np.abs(y - pred).sum()) / max(float(y.sum()), 1), 1),
           "attempts": {}}
    for name, (calls, steps) in per.items():
        n = len(calls)
        floor = calls[0] if calls else 0
        carry = sum(calls) - floor * n
        shares = {k: 0.0 for k in KINDS}
        resid = 0.0
        for i, (d, row) in enumerate(steps):
            rides = n - 1 - i  # rows appended before call i+1 ride calls i+1 .. n-1
            est = {k: float(coef[j]) * row[k] for j, k in enumerate(KINDS)}
            for k in KINDS:
                shares[k] += est[k] * rides
            resid += (d - sum(est.values())) * rides
        out["attempts"][name] = {"calls": n, "processed": sum(calls), "floor": floor, "floor_rent": floor * n, "carry": carry,
                                 "by_kind": {k: int(v) for k, v in shares.items()}, "residual": int(resid)}
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("streams", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--drop", default="", help="comma-separated kinds to leave out (ablation)")
    a = ap.parse_args(argv)
    per = {}
    for p in a.streams:
        path = Path(p)
        per[f"{path.parent.name}/{path.name}"] = steps_of(path)
    r = fit(per, tuple(k for k in a.drop.split(",") if k))
    if a.json or "error" in r:
        print(json.dumps(r, indent=1))
        return 0 if "error" not in r else 1
    print(f"{r['verdict']} {r['implausible'] or ''} rates (tok/char; tok/image) {r['rates']}  dropped={r['dropped']}  "
          f"steps={r['steps']}  abs residual {r['abs_residual_pct']}%")
    for name, v in r["attempts"].items():
        c = max(v["carry"], 1)
        parts = "  ".join(f"{k}={100 * x / c:.1f}%" for k, x in v["by_kind"].items())
        print(f"{name}: calls={v['calls']} processed={v['processed']:,} floor_rent={v['floor_rent']:,} carry={v['carry']:,}  {parts}  residual={100 * v['residual'] / c:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
