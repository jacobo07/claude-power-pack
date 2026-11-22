#!/usr/bin/env python3
"""UserPromptSubmit: route a visual prompt to the design tools its surface needs (spec design-surface-router.md).

Silent for a prompt that names no visual surface. Otherwise ONE block: the kinds, the skills to load now, the
recommended ones, and what the Stop gate (tools/design_donegate_stop.py) will check. The kinds are kept per session
so the Stop gate judges later turns ("sigue") by the surface the work started as.
Fail-open: any error prints nothing. Kill switch: CPP_DESIGN_ROUTE=off.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))


def block(pol: dict) -> str:
    rec = ", ".join(pol["recommended"]) or "none"
    req = ", ".join(pol["required"]) or "none for this kind"
    py = sys.executable or "python"
    lines = [
        "Design route (Power Pack, automatic): this prompt is visual work of kind %s." % "+".join(pol["kinds"]),
        "- Load NOW with the Skill tool, before the first visual file: %s." % req,
        "- Also apply where they fit: %s." % rec,
    ]
    lines += ["- %s" % a for a in pol["advice"]]
    checks = ["the skills above were loaded in this session"]
    if pol["taste"]:
        checks.insert(0, "every HTML page passes the Taste lint with no critical (`%s -m modules.cdio.taste <page>` "
                         "from %s)" % (py, _PP_ROOT))
    if pol["review"]:
        checks.append("cdio-reviewer APPROVED the CURRENT bytes of every visual file, recorded with "
                      "`%s %s render <files>` then `... record --verdicts <v.json> --files <files>`"
                      % (py, _PP_ROOT / "tools" / "design_review_record.py"))
    lines.append("- Before calling it done, the Stop gate checks every visual file written here: " + "; ".join(checks) + ".")
    lines.append("- A check that genuinely does not apply: write `NO APLICA: design-taste|design-skills|design-review: "
                 "<reason>` in the final message.")
    return "\n".join(lines)


# Text that reaches UserPromptSubmit without the Owner typing it. Measured 2026-11-22 over the live prompts.jsonl
# (106 routes): ~54 fired on these, including all 44 `motion` routes -- a subagent hand-back that mentions a "trailer"
# re-routed the session to motion, demanded motion-promo, and (latest prompt decides) switched off the review of app
# source. The Owner's own words, typed or pasted, are never filtered (V-DRO-*).
# One definition, shared with the family-baseline injector (modules/gsd_x/cli.py), which fired on the same machine
# text and armed a turn-end gate (2026-11-22). Re-exported under the old name for callers and V-DRO.
from modules.gsd_x.prompt_origin import MACHINE_PREFIXES as _MACHINE_PREFIXES, owner_text  # noqa: E402,F401


def run(payload: dict) -> dict | None:
    from modules.cdio import design_route as dr
    prompt = owner_text(str(payload.get("prompt") or payload.get("user_prompt") or ""))
    if not prompt:
        return None
    routes = dr.load_routes()
    kinds = dr.classify(prompt, routes)
    if not kinds:
        return None
    sid = str(payload.get("session_id") or payload.get("sessionId") or "")
    if sid:
        st = dr.load_session(sid)
        # The LATEST visual prompt decides, never the union of the session: one stray match early on must not decide
        # the gate for every later page (review of a9db1d43, F1).
        st["kinds"] = kinds
        dr.save_session(sid, st)
    dr.append_row("prompts.jsonl", {"sid": sid, "kinds": kinds})
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                   "additionalContext": block(dr.policy(kinds, routes))}}


def main() -> int:
    if os.environ.get("CPP_DESIGN_ROUTE", "").strip().lower() in ("off", "0", "false"):
        return 0
    try:
        raw = sys.stdin.read().lstrip("﻿")
        payload = json.loads(raw) if raw.strip() else {}
        out = run(payload if isinstance(payload, dict) else {})
        if out:
            sys.stdout.write(json.dumps(out, ensure_ascii=True))  # cp1252 stdout: see design_donegate_stop.main
    except Exception as exc:  # noqa: BLE001 -- fail-open, never silently
        try:
            from modules.cdio import design_route as dr
            dr.append_row("errors.jsonl", {"hook": "prompt", "error": "%s: %s" % (type(exc).__name__, exc)})
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
