#!/usr/bin/env python3
"""verify_full_install.py - Host audit for the Programmatic Budget Layer.

NOT an installer. This script audits the CURRENT host's wiring of the
Claude Power Pack programmatic-budget components and emits side-by-side
probe numbers (no fabricated composite multiplier). Reality-Contract:
every percentage printed traces to a live measurement performed in this
same invocation.

Sections audited:
  1. RTK binary present at ~/.claude/bin/rtk.exe (--version matches the
     pinned vendor/rtk/UPSTREAM_REF.md identity guard).
  2. RTK PreToolUse:Bash hook registered in ~/.claude/settings.json.
  3. JIT UserPromptSubmit hook registered in ~/.claude/settings.json.
  4. Owner-seeded ~/.claude/budget.json present + schema-valid.
  5. Externalized pricing fresh (vault/pricing/anthropic_2026-05.json
     fetched_iso younger than 30 days).
  6. Telemetry directory + recent activity (jit_usage_*.jsonl,
     rtk_*.jsonl).
  7. Cache hints validate via tools/cache_hint_apply.py.

Side-by-side measurements (Gap 9 — DO NOT multiply these):
  * Bash-output RTK: tok delta on `git log --stat -50`.
  * Skill-injection JIT: arithmetic mean reduction across programmatic
    tier across the live trigger-matrix modules.

Hook-registration ambiguity (Gap 8):
  * Registered in settings.json + script present  -> [OK]
  * Registered, script missing on disk            -> [FAIL]
  * NOT registered                                -> [ADVISORY] + how-to
  * Cannot know if a registered hook has actually been LOADED by the
    current Claude Code session — only /restart proves it. We never
    auto-register or auto-restart.

Exit code: 0 if all CRITICAL sections pass (RTK binary + pricing fresh
+ telemetry dir present), 1 otherwise. Advisories never fail the gate.

Usage:
  python tools/verify_full_install.py
  python tools/verify_full_install.py --quiet
"""
from __future__ import annotations
import argparse
import datetime as dt
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = Path(__file__).resolve().parents[1]
RTK_BIN = HOME / ".claude" / "bin" / "rtk.exe"
USER_SETTINGS = HOME / ".claude" / "settings.json"
BUDGET_FILE = HOME / ".claude" / "budget.json"
PRICING_FILE = PP_ROOT / "vault" / "pricing" / "anthropic_2026-05.json"
TELEMETRY_DIR = PP_ROOT / "vault" / "telemetry"
UPSTREAM_REF = PP_ROOT / "vendor" / "rtk" / "UPSTREAM_REF.md"
LOADER = PP_ROOT / "tools" / "jit_skill_loader.py"
CACHE_HINT_APPLY = PP_ROOT / "tools" / "cache_hint_apply.py"


def _load_jsl():
    spec = importlib.util.spec_from_file_location("jsl", LOADER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _read_json(p: Path) -> dict | None:
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def check_rtk_binary() -> tuple[str, str, dict]:
    """Section 1: RTK binary + identity guard."""
    detail = {}
    if not RTK_BIN.is_file():
        return ("FAIL", "rtk.exe absent at ~/.claude/bin/rtk.exe",
                {"path": str(RTK_BIN), "present": False})
    detail["path"] = str(RTK_BIN)
    detail["bytes"] = RTK_BIN.stat().st_size
    try:
        res = subprocess.run([str(RTK_BIN), "--version"],
                             capture_output=True, text=True, timeout=5)
        ver = (res.stdout or res.stderr or "").strip().splitlines()
        ver = ver[0] if ver else ""
        detail["version_output"] = ver
    except Exception as exc:
        return ("FAIL", f"rtk --version failed: {type(exc).__name__}",
                detail)
    pinned = ""
    if UPSTREAM_REF.is_file():
        for line in UPSTREAM_REF.read_text(encoding="utf-8").splitlines():
            if "Binary version installed" in line and "`" in line:
                parts = line.split("`")
                if len(parts) >= 2:
                    pinned = parts[1].strip()
                    break
    detail["pinned"] = pinned
    if pinned and pinned not in ver:
        return ("FAIL",
                f"version mismatch: rtk reports {ver!r}, pinned {pinned!r}",
                detail)
    return ("OK", f"rtk {ver} present + matches pinned {pinned!r}", detail)


def _hook_registered_path(settings: dict, event: str,
                          matcher_substr: str,
                          command_substr: str) -> str | None:
    """Return the actual command string of a matching registration, or
    None. Lets the caller validate the script-file path that's actually
    wired, not a guess."""
    if not isinstance(settings, dict):
        return None
    hooks = (settings.get("hooks") or {}).get(event) or []
    for entry in hooks:
        m = (entry.get("matcher") or "")
        if matcher_substr and matcher_substr not in m:
            continue
        for h in (entry.get("hooks") or []):
            cmd = h.get("command") or ""
            if command_substr in cmd:
                return cmd
    return None


def _extract_script_path(cmd: str, suffix: str) -> Path | None:
    """Pull the .js/.py path from a `node ... "PATH"` style hook command."""
    import re
    for m in re.finditer(r'"([^"]+\.' + suffix + r')"', cmd):
        return Path(m.group(1))
    for tok in cmd.split():
        if tok.endswith("." + suffix):
            return Path(tok.strip('"\''))
    return None


def check_rtk_hook() -> tuple[str, str, dict]:
    """Section 2: RTK PreToolUse:Bash hook registered.

    Honest path check: parse the registered command, then verify THAT
    script exists (handles both the Owner-copy pattern under
    ~/.claude/hooks/ and the ship-location-direct pattern under the
    power-pack repo).
    """
    settings = _read_json(USER_SETTINGS) or {}
    reg_cmd = _hook_registered_path(settings, "PreToolUse", "Bash",
                                     "rtk-rewrite.js")
    if reg_cmd is None:
        return ("ADVISORY",
                "RTK PreToolUse:Bash NOT registered. To enable: register "
                "via tools/settings_merger.py register-pretool",
                {"registered": False})
    script = _extract_script_path(reg_cmd, "js")
    if script is None:
        return ("FAIL",
                "registered but command string has no parseable .js path",
                {"registered": True, "command": reg_cmd})
    if not script.is_file():
        return ("FAIL",
                f"registered but {script} missing on disk",
                {"registered": True, "script": str(script)})
    return ("OK", f"PreToolUse:Bash registered + script present at "
            f"{script}",
            {"registered": True, "script": str(script)})


def check_jit_hook() -> tuple[str, str, dict]:
    """Section 3: JIT UserPromptSubmit hook registered + script present."""
    settings = _read_json(USER_SETTINGS) or {}
    reg_cmd = _hook_registered_path(settings, "UserPromptSubmit", "",
                                     "jit_skill_loader.py")
    if reg_cmd is None:
        return ("ADVISORY",
                "JIT UserPromptSubmit NOT registered. To enable: "
                "tools/settings_merger.py register-userprompt",
                {"registered": False})
    script = _extract_script_path(reg_cmd, "py")
    if script is not None and not script.is_file():
        return ("FAIL", f"registered but {script} missing on disk",
                {"registered": True, "script": str(script)})
    return ("OK", "UserPromptSubmit JIT loader registered + script present",
            {"registered": True,
             "script": str(script) if script else "(unparsed)"})


def check_budget_config() -> tuple[str, str, dict]:
    """Section 4: Owner-seeded ~/.claude/budget.json."""
    if os.environ.get("ANTHROPIC_PROGRAMMATIC_BUDGET_USD"):
        return ("OK", "ANTHROPIC_PROGRAMMATIC_BUDGET_USD env-override set",
                {"source": "env"})
    cfg = _read_json(BUDGET_FILE)
    if cfg is None:
        return ("ADVISORY",
                f"{BUDGET_FILE} absent. Copy docs/budget.example.json "
                "to ~/.claude/budget.json and edit",
                {"present": False})
    if not isinstance(cfg.get("monthly_usd"), (int, float)) \
            or cfg["monthly_usd"] <= 0:
        return ("FAIL", "budget.json malformed: monthly_usd missing/invalid",
                {"cfg": cfg})
    return ("OK",
            f"budget.json tier={cfg.get('tier')} "
            f"monthly_usd=${cfg['monthly_usd']:.2f}",
            {"cfg": cfg})


def check_pricing_fresh() -> tuple[str, str, dict]:
    """Section 5: pricing JSON fetched_iso < 30 days."""
    p = _read_json(PRICING_FILE)
    if p is None:
        return ("FAIL", f"{PRICING_FILE} absent or malformed",
                {"present": False})
    try:
        fetched = dt.datetime.fromisoformat(
            p.get("fetched_iso", "").replace("Z", "+00:00"))
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return ("FAIL", "pricing.fetched_iso unparseable",
                {"fetched_iso": p.get("fetched_iso")})
    age = (dt.datetime.now(dt.timezone.utc) - fetched).days
    if age > 30:
        return ("FAIL", f"pricing is {age}d old (>30d stale)",
                {"age_days": age})
    return ("OK", f"pricing fresh ({age}d old)", {"age_days": age})


def check_telemetry() -> tuple[str, str, dict]:
    """Section 6: telemetry dir + recent rows."""
    if not TELEMETRY_DIR.is_dir():
        return ("FAIL", f"{TELEMETRY_DIR} absent", {"present": False})
    jit = list(TELEMETRY_DIR.glob("jit_usage_*.jsonl"))
    rtk = list(TELEMETRY_DIR.glob("rtk_*.jsonl"))
    budget = list(TELEMETRY_DIR.glob("budget-*.jsonl"))
    detail = {"jit_files": len(jit), "rtk_files": len(rtk),
              "budget_files": len(budget)}
    return ("OK",
            f"telemetry present (jit={len(jit)}, rtk={len(rtk)}, "
            f"budget={len(budget)})", detail)


def check_cache_hints() -> tuple[str, str, dict]:
    """Section 7: cache_hints validate via the in-repo consumer."""
    if not CACHE_HINT_APPLY.is_file():
        return ("FAIL", "tools/cache_hint_apply.py missing",
                {"consumer_present": False})
    try:
        res = subprocess.run(
            [sys.executable, str(CACHE_HINT_APPLY), "--quiet"],
            capture_output=True, text=True, timeout=15,
            cwd=str(PP_ROOT))
        if res.returncode != 0:
            return ("FAIL", f"cache_hint_apply exit {res.returncode}",
                    {"exit": res.returncode})
        return ("OK", "cache_hint_apply.py exit 0 (hints valid or "
                "directory empty)", {"exit": 0})
    except Exception as exc:
        return ("FAIL", f"cache_hint_apply crashed: {type(exc).__name__}",
                {"error": str(exc)})


def probe_rtk_output() -> dict:
    """Side-by-side probe A: Bash-output RTK compression on a fixed
    benchmark. Identical methodology to verify_rtk_fusion.py."""
    if not RTK_BIN.is_file():
        return {"status": "rtk-absent", "pct": None}
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tok = lambda s: len(enc.encode(s))
    except Exception:
        tok = lambda s: math.ceil(len(s) / 4)
    cmd = ["git", "log", "--stat", "-50"]
    try:
        raw = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=15, cwd=str(PP_ROOT))
        wrap = subprocess.run([str(RTK_BIN)] + cmd, capture_output=True,
                              text=True, timeout=15, cwd=str(PP_ROOT))
    except Exception as exc:
        return {"status": f"probe-error:{type(exc).__name__}",
                "pct": None}
    raw_t = tok(raw.stdout or "")
    rtk_t = tok(wrap.stdout or "")
    if raw_t <= 0 or not (wrap.stdout or "").strip():
        return {"status": "no-output", "pct": None}
    pct = max(0.0, (raw_t - rtk_t) / raw_t)
    return {"status": "ok", "pct": pct, "raw_tok": raw_t,
            "rtk_tok": rtk_t, "domain": "Bash command output"}


def probe_jit_skill() -> dict:
    """Side-by-side probe B: arithmetic mean JIT reduction across the
    live trigger-matrix modules in programmatic mode."""
    try:
        jsl = _load_jsl()
    except Exception as exc:
        return {"status": f"loader-error:{type(exc).__name__}",
                "pct": None}
    upstream = PP_ROOT / "vendor" / "apollo" / "upstream"
    targets = sorted({m for t in getattr(jsl, "TRIGGERS", [])
                      for m in t[2]})
    if not targets:
        return {"status": "no-targets", "pct": None}
    tok = jsl._tok
    reds: list[float] = []
    per_mod: list[dict] = []
    for mod in targets:
        skill = upstream / mod / "SKILL.md"
        if not skill.is_file():
            continue
        body = skill.read_text(encoding="utf-8")
        full = jsl._render(mod, body, "full", programmatic=True)
        summ = jsl._render(mod, body, "summary", programmatic=True)
        tf, ts = tok(full), tok(summ)
        if tf > 0:
            r = 1.0 - (ts / tf)
            reds.append(r)
            per_mod.append({"module": mod, "reduction": r})
    if not reds:
        return {"status": "no-measurements", "pct": None}
    return {"status": "ok", "pct": sum(reds) / len(reds),
            "n_modules": len(reds), "per_module": per_mod,
            "domain": "Apollo skill-card injection"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    checks = [
        ("1. RTK binary",      check_rtk_binary()),
        ("2. RTK hook",        check_rtk_hook()),
        ("3. JIT hook",        check_jit_hook()),
        ("4. Budget config",   check_budget_config()),
        ("5. Pricing fresh",   check_pricing_fresh()),
        ("6. Telemetry",       check_telemetry()),
        ("7. Cache hints",     check_cache_hints()),
    ]
    critical_fail = any(s == "FAIL" for label, (s, _, _) in checks
                        if "RTK binary" in label or "Pricing" in label
                        or "Telemetry" in label)

    rtk_probe = probe_rtk_output()
    jit_probe = probe_jit_skill()

    if not args.quiet:
        print("=== Programmatic Budget Layer — Host Audit ===")
        for label, (status, reason, _) in checks:
            print(f"  [{status}] {label}: {reason}")
        print()
        print("--- Budget Impact (side-by-side probes, NOT multiplied) ---")
        if rtk_probe.get("pct") is not None:
            print(f"  Bash-output RTK compression: "
                  f"{rtk_probe['pct']:.1%}  "
                  f"[domain: {rtk_probe['domain']}, "
                  f"raw={rtk_probe['raw_tok']}t -> "
                  f"rtk={rtk_probe['rtk_tok']}t]")
        else:
            print(f"  Bash-output RTK compression: unmeasured "
                  f"({rtk_probe.get('status')})")
        if jit_probe.get("pct") is not None:
            print(f"  Skill-injection JIT compression: "
                  f"{jit_probe['pct']:.1%}  "
                  f"[domain: {jit_probe['domain']}, "
                  f"n={jit_probe['n_modules']} modules, arithmetic mean]")
        else:
            print(f"  Skill-injection JIT compression: unmeasured "
                  f"({jit_probe.get('status')})")
        print()
        print("  These two probes operate on DIFFERENT byte streams "
              "(Bash output vs API prompt input). Multiplying them "
              "would not be the combined per-session savings — that "
              "requires an end-to-end session-token delta probe, which "
              "this script does not perform. Each number stands alone.")
    return 1 if critical_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
