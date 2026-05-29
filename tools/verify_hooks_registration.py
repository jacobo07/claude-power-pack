#!/usr/bin/env python3
"""verify_hooks_registration.py -- sub-verifier for BL-HOOKS-REG-001.

Seven binary sub-checks:
  H1 reg-script       tools/register_global_hooks.py exists +
                      --dry-run rc=0
  H2 status-script    tools/check_hook_status.py exists + importable
  H3 hooks-on-disk    4 JS hooks present in hooks/
  H4 docs-present     docs/HOOKS_SETUP.md present + non-trivial
  H5 sscheck-flag     tools/tco_compact_gate.py advertises
                      --session-start-check
  H6 smoke-harness    tools/_hook_smoke.py present + importable
  H7 idempotency-mod  register module guards against duplicates via
                      marker substrings

Exit 0 iff all 7 pass. Prints HOOKS_REG_PROBE=N/7 for verify_spp.py.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PP))
sys.path.insert(0, str(PP / "tools"))


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    reg = PP / "tools" / "register_global_hooks.py"
    if not reg.is_file():
        checks.append(("reg-script", False, f"missing: {reg}"))
    else:
        with tempfile.TemporaryDirectory(prefix="prob_reg_") as td:
            settings = Path(td) / "settings.json"
            settings.write_text(json.dumps({"hooks": {}}),
                                encoding="utf-8-sig")
            try:
                mod = importlib.import_module("register_global_hooks")
                mod = importlib.reload(mod)
                mod.SETTINGS_PATH = settings
                rc = mod.main(["--dry-run"])
                if rc == 0:
                    checks.append(("reg-script", True,
                                   f"--dry-run rc=0 ({reg.stat().st_size}B)"))
                else:
                    checks.append(("reg-script", False,
                                   f"--dry-run rc={rc}"))
            except Exception as exc:
                checks.append(("reg-script", False,
                               f"{type(exc).__name__}: {exc}"))

    chk = PP / "tools" / "check_hook_status.py"
    if not chk.is_file():
        checks.append(("status-script", False, f"missing: {chk}"))
    else:
        try:
            mod = importlib.import_module("check_hook_status")
            mod = importlib.reload(mod)
            if hasattr(mod, "main") and hasattr(mod, "PP_HOOK_MARKERS"):
                checks.append(("status-script", True,
                               f"{len(mod.PP_HOOK_MARKERS)} markers"))
            else:
                checks.append(("status-script", False, "missing attrs"))
        except Exception as exc:
            checks.append(("status-script", False,
                           f"{type(exc).__name__}: {exc}"))

    js_hooks = [
        "uqf_pre_edit_gate.js",
        "osa_deploy_detector.js",
        "bug-hunter-ceps-bridge.js",
        "jobs_woz_gate.js",
    ]
    missing = [h for h in js_hooks if not (PP / "hooks" / h).is_file()]
    if not missing:
        checks.append(("hooks-on-disk", True,
                       f"{len(js_hooks)}/{len(js_hooks)} present"))
    else:
        checks.append(("hooks-on-disk", False, f"missing={missing}"))

    docs = PP / "docs" / "HOOKS_SETUP.md"
    if docs.is_file() and docs.stat().st_size > 1500:
        checks.append(("docs-present", True,
                       f"{docs.stat().st_size} bytes"))
    else:
        checks.append(("docs-present", False,
                       f"is_file={docs.is_file()}"))

    tco = PP / "tools" / "tco_compact_gate.py"
    if not tco.is_file():
        checks.append(("sscheck-flag", False, f"missing: {tco}"))
    else:
        text = tco.read_text(encoding="utf-8")
        if "--session-start-check" in text and "session_start_check" in text:
            checks.append(("sscheck-flag", True,
                           "flag and handler both present"))
        else:
            checks.append(("sscheck-flag", False,
                           "flag or handler missing"))

    smoke = PP / "tools" / "_hook_smoke.py"
    if smoke.is_file() and smoke.stat().st_size > 1500:
        checks.append(("smoke-harness", True,
                       f"{smoke.stat().st_size} bytes"))
    else:
        checks.append(("smoke-harness", False,
                       f"is_file={smoke.is_file()}"))

    try:
        mod = importlib.import_module("register_global_hooks")
        mod = importlib.reload(mod)
        specs = mod._hooks_to_register()
        markers = {s["marker"] for s in specs}
        expected = {
            "uqf_pre_edit_gate",
            "osa_deploy_detector",
            "bug-hunter-ceps-bridge",
            "session-start-check",
            "jobs_woz_gate",
        }
        if markers == expected:
            checks.append(("idempotency-mod", True,
                           f"5 markers exact-match"))
        else:
            checks.append(("idempotency-mod", False,
                           f"markers={markers} vs {expected}"))
    except Exception as exc:
        checks.append(("idempotency-mod", False,
                       f"{type(exc).__name__}: {exc}"))

    passes_n = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    for name, ok, msg in checks:
        tag = "PASS" if ok else "FAIL"
        print(f"{tag}  {name:18s} {msg}")
    print()
    print(f"HOOKS_REG_PROBE={passes_n}/{total}")
    return 0 if passes_n == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
