#!/usr/bin/env python3
"""first_time_project_init.py - quick PP prereq probe (Zero-Command Component D).

Spawned detached by ~/.claude/hooks/first-time-project.js on the first
SessionStart in a real project dir (.git + manifest, no
.pp-onboarded-prereqs marker).

Runs 4 quick checks (each <500 ms) and writes:
  - <cwd>/.pp-onboarded-prereqs           (audit trail, always)
  - <cwd>/vault/handoffs/pp-onboarding-<ts>.md  (only when gaps exist)

Quick checks (the slow surface area of verify_full_install.py is
intentionally excluded - this is a first-impression probe, not the full
gate):
  1. PP install layout sanity (hooks/, tools/, vault/templates/ present)
  2. Spec Kit templates available
  3. Hook dispatcher present
  4. ~/.claude/settings.json parseable

Fail-open: any exception logs and returns code 0 (the marker still
written with the partial result so the next SessionStart doesn't
re-probe).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
LOG_FILE = HOME / ".claude" / "logs" / "first-time-project.log"


def log(msg: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()} [probe] {msg}\n")
    except Exception as e:
        sys.stderr.write(f"first-time-project log fail: {e}\n")


def check_pp_layout() -> dict:
    required = [
        PP_ROOT / "hooks",
        PP_ROOT / "tools",
        PP_ROOT / "vault" / "templates",
        PP_ROOT / "vault" / "knowledge_base",
    ]
    missing = [str(p) for p in required if not p.is_dir()]
    return {"name": "pp-layout", "ok": not missing, "missing": missing}


def check_speckit_templates() -> dict:
    speckit = PP_ROOT / "vault" / "templates" / "speckit"
    expected = ["constitution.md.template"]
    if not speckit.is_dir():
        return {"name": "speckit-templates", "ok": False,
                "missing": ["vault/templates/speckit/ directory"]}
    missing = [t for t in expected if not (speckit / t).is_file()]
    return {"name": "speckit-templates", "ok": not missing, "missing": missing}


def check_hook_dispatcher() -> dict:
    dispatcher = HOME / ".claude" / "hooks" / "hook-dispatcher.js"
    pp_dispatcher = PP_ROOT / "hooks" / "hook-dispatcher.js"
    deployed = dispatcher.is_file()
    sourced = pp_dispatcher.is_file()
    return {
        "name": "hook-dispatcher",
        "ok": sourced,  # source presence is the prereq; deploy is Owner's call
        "deployed": deployed,
        "sourced": sourced,
    }


def check_settings_json() -> dict:
    settings = HOME / ".claude" / "settings.json"
    if not settings.is_file():
        return {"name": "settings-json", "ok": False,
                "reason": "~/.claude/settings.json missing"}
    try:
        json.loads(settings.read_text(encoding="utf-8"))
        return {"name": "settings-json", "ok": True}
    except Exception as e:
        return {"name": "settings-json", "ok": False,
                "reason": f"parse error: {e}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--session", default="unknown")
    args = ap.parse_args()

    cwd = Path(args.cwd)
    if not cwd.is_dir():
        log(f"cwd not a directory: {cwd}")
        return 0

    marker = cwd / ".pp-onboarded-prereqs"
    if marker.exists():
        return 0  # belt + suspenders, hook already guards this

    started = time.time()
    results = []
    for probe in (check_pp_layout, check_speckit_templates,
                  check_hook_dispatcher, check_settings_json):
        try:
            results.append(probe())
        except Exception as e:
            results.append({"name": probe.__name__, "ok": False, "error": str(e)})

    gaps = [r for r in results if not r.get("ok")]
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session": args.session,
        "cwd": str(cwd),
        "duration_sec": round(time.time() - started, 3),
        "results": results,
        "gaps_count": len(gaps),
    }

    try:
        marker.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    except Exception as e:
        log(f"marker write failed: {e}")

    if gaps:
        try:
            handoff_dir = cwd / "vault" / "handoffs"
            handoff_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
            handoff_path = handoff_dir / f"pp-onboarding-{ts}.md"
            lines = [
                "# Power Pack Onboarding Gaps Detected",
                "",
                f"- **Project**: `{cwd}`",
                f"- **Session**: `{args.session}`",
                f"- **Gaps**: {len(gaps)} of {len(results)} checks failed",
                "",
                "## What failed",
                "",
            ]
            for g in gaps:
                lines.append(f"### {g.get('name', '?')}")
                if g.get("missing"):
                    lines.append(f"- Missing: {', '.join(g['missing'])}")
                if g.get("reason"):
                    lines.append(f"- Reason: {g['reason']}")
                if g.get("error"):
                    lines.append(f"- Error: {g['error']}")
                lines.append("")
            lines.extend([
                "## Suggested install path",
                "",
                "```bash",
                "cd ~/.claude/skills/claude-power-pack && git pull",
                "python tools/verify_full_install.py",
                "```",
                "",
                "*Generated by first-time-project probe (Zero-Command Component D). "
                "Marker `.pp-onboarded-prereqs` records the full check result.*",
            ])
            handoff_path.write_text("\n".join(lines), encoding="utf-8")
            log(f"handoff written {handoff_path} gaps={len(gaps)}")
        except Exception as e:
            log(f"handoff write failed: {e}")

    log(f"probe complete cwd={cwd} duration={summary['duration_sec']}s gaps={len(gaps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
