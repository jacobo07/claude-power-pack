#!/usr/bin/env python3
"""verify_osa.py — sub-verifier for the OSA axis (sealed 2026-05-28).

Five binary sub-checks:
  O1 osa-imports         modules.osa.{throttle,never_again,gpu_eyes,
                          dispatcher,osa_command} import without error
  O2 osa-config          vault/osa/config.json is valid JSON with the
                          required sections (throttle, triggers, gpu_eyes)
  O3 osa-throttle-check  throttle.check() returns a valid string
                          (GO|CACHE_HIT:N|COOLDOWN:N|BUDGET_EXHAUSTED)
  O4 osa-dispatcher      dispatcher.should_activate() returns a 3-tuple
                          without crashing; payload contains 'project'
  O5 osa-agent-file      ~/.claude/agents/omni-singularity.md exists
                          and frontmatter does not contain the forbidden
                          triggers:/throttle: YAML keys

Exit 0 iff all 5 pass. Prints OSA_PROBE=N/5 line for verify_spp.py.
Used by verify_spp.py row "osa-active".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    # O1 imports
    try:
        from modules.osa import throttle as _t  # noqa: F401
        from modules.osa import never_again as _n  # noqa: F401
        from modules.osa import gpu_eyes as _g  # noqa: F401
        from modules.osa import dispatcher as _d  # noqa: F401
        from modules.osa import osa_command as _c  # noqa: F401
        checks.append(("osa-imports", True, "5 modules imported"))
    except Exception as exc:
        checks.append(("osa-imports", False, f"{exc!r}"))

    # O2 config.json present + sections
    cfg_path = PP / "vault" / "osa" / "config.json"
    if not cfg_path.is_file():
        checks.append(("osa-config", False, f"missing: {cfg_path}"))
    else:
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            missing = [s for s in ("throttle", "triggers", "gpu_eyes")
                       if s not in data]
            if missing:
                checks.append(
                    ("osa-config", False, f"missing sections: {missing}"))
            elif not isinstance(
                data["throttle"].get("max_daily_calls"), int
            ) or data["throttle"]["max_daily_calls"] <= 0:
                checks.append(
                    ("osa-config", False,
                     f"invalid max_daily_calls: {data['throttle'].get('max_daily_calls')}"))
            else:
                checks.append(
                    ("osa-config", True,
                     f"max_daily={data['throttle']['max_daily_calls']}"))
        except Exception as exc:
            checks.append(("osa-config", False, f"parse: {exc!r}"))

    # O3 throttle.check returns valid token
    try:
        from modules.osa import throttle as _t
        token = _t.check("verify-osa-probe")
        valid = (
            token == "GO" or token == "BUDGET_EXHAUSTED"
            or token.startswith("CACHE_HIT:")
            or token.startswith("COOLDOWN:")
        )
        if valid:
            checks.append(("osa-throttle-check", True, f"-> {token}"))
        else:
            checks.append(("osa-throttle-check", False, f"-> {token!r}"))
    except Exception as exc:
        checks.append(("osa-throttle-check", False, f"{exc!r}"))

    # O4 dispatcher.should_activate returns 3-tuple, payload has project
    try:
        from modules.osa import dispatcher as _d
        result = _d.should_activate("verify-osa-probe")
        if (isinstance(result, tuple) and len(result) == 3
                and isinstance(result[2], dict)
                and "project" in result[2]):
            checks.append(
                ("osa-dispatcher", True,
                 f"active={result[0]} reason={result[1]}"))
        else:
            checks.append(
                ("osa-dispatcher", False, f"unexpected: {result!r}"))
    except Exception as exc:
        checks.append(
            ("osa-dispatcher", False, f"{exc!r}"))

    # O5 agent file exists + no forbidden frontmatter keys
    agent_path = Path.home() / ".claude" / "agents" / "omni-singularity.md"
    if not agent_path.is_file():
        checks.append(("osa-agent-file", False, f"missing: {agent_path}"))
    else:
        try:
            content = agent_path.read_text(encoding="utf-8")
            if not content.startswith("---"):
                checks.append(
                    ("osa-agent-file", False, "missing frontmatter"))
            else:
                fm_end = content.find("\n---", 3)
                fm = content[3:fm_end] if fm_end > 0 else content
                bad = [k for k in ("triggers:", "throttle:") if k in fm]
                if bad:
                    checks.append(
                        ("osa-agent-file", False,
                         f"forbidden keys: {bad}"))
                else:
                    checks.append(
                        ("osa-agent-file", True,
                         "valid frontmatter, no triggers:/throttle: keys"))
        except Exception as exc:
            checks.append(("osa-agent-file", False, f"{exc!r}"))

    passes = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    for name, ok, msg in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"{tag}  {name:24s} {msg}")
    print()
    print(f"OSA_PROBE={passes}/{total}")
    return 0 if passes == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
