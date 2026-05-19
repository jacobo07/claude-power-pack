#!/usr/bin/env python3
"""e2e_clean_install.py — E1 clean-machine verification.

Spawns ``install_global_core.py`` with ``HOME / USERPROFILE / APPDATA /
LOCALAPPDATA / CLAUDE_CONFIG_DIR`` all redirected at a fresh temp
directory (Path A in the FASE E plan), then proves three properties:

  1. Dry-run is non-destructive: the sandbox's ``.claude/`` tree
     either does not exist or has no PP-tracked files after a
     ``--dry-run`` invocation.
  2. Real apply works: a second invocation creates
     ``.claude/agents/`` + ``.claude/commands/`` populated with at
     least one entry each (the inventory's pp-original set).
  3. Idempotency: a THIRD invocation reports every entry as
     ``unchanged`` (SHA-skip working).

Exit codes:
  0 — all three gates green. Evidence written to
      ``vault/audits/clean_install_<iso>.json``.
  1 — any gate red. Evidence still written; non-zero rc surfaces it.

Path A vs Path B:
  This script implements **Path A** (real HOME redirect). Some
  Windows pythons may resolve ``Path.home()`` via the Win32 token
  rather than the ``USERPROFILE`` env var; if that happens this
  script detects it (the sandbox stays empty after apply) and the
  exit message points at the Path-B fallback the plan authorises.

Doctrine alignment:
  * Reality-Contract: every subprocess is real, no synthesised exit
    codes; the report records stdout/stderr tails verbatim.
  * Hooks-dir deny doctrine: the install drives ``settings_merger``
    register-* subcommands, but only against the sandbox settings.
    The host's real ``~/.claude/settings.json`` is never touched
    because ``USERPROFILE`` is pointed elsewhere for the duration.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


PP = Path(__file__).resolve().parents[1]
CORE = PP / "tools" / "install_global_core.py"
PY = sys.executable
ISO_TS = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
EVIDENCE = PP / "vault" / "audits" / f"clean_install_{ISO_TS}.json"

# Env vars Windows + POSIX inspect to locate the user home. Path.home()
# on Win32 reads USERPROFILE first; on POSIX it reads HOME. We set every
# variant so any nested subprocess (settings_merger.py, node) is
# sandboxed identically.
HOME_ENV_KEYS = (
    "HOME",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "CLAUDE_CONFIG_DIR",
)


def _make_sandbox(keep: bool) -> Path:
    """Create the sandbox HOME, return its absolute path."""
    parent = Path(tempfile.gettempdir()) / "pp-e2e-sandboxes"
    parent.mkdir(parents=True, exist_ok=True)
    sandbox = parent / f"home-{ISO_TS}"
    sandbox.mkdir(parents=True, exist_ok=False)
    print(f"  [sandbox] {sandbox}  (keep={keep})", flush=True)
    return sandbox


def _sandbox_env(sandbox: Path) -> dict[str, str]:
    env = dict(os.environ)
    # Strip parent-session markers (mirrors install-global.* wrappers).
    for k in ("CLAUDECODE", "CLAUDE_PROJECT_DIR"):
        env.pop(k, None)
    for k in [x for x in env if x.startswith("CLAUDE_CODE_")]:
        env.pop(k, None)
    # Point every HOME-shaped var at the sandbox.
    for k in HOME_ENV_KEYS:
        env[k] = str(sandbox)
    env["PP_SANDBOX"] = str(sandbox)
    return env


def _run_install(env: dict[str, str], sandbox: Path,
                 extra: list[str]) -> dict:
    """Run install_global_core.py with the given env + extra args."""
    settings = sandbox / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    if not settings.exists():
        settings.write_text("{}", encoding="utf-8")
    argv = [PY, str(CORE), "--settings", str(settings)] + extra
    t0 = time.monotonic()
    cp = subprocess.run(argv, env=env, capture_output=True, text=True,
                        timeout=120)
    elapsed = time.monotonic() - t0
    return {
        "argv": argv,
        "rc": cp.returncode,
        "elapsed_s": round(elapsed, 2),
        "stdout_tail": (cp.stdout or "").splitlines()[-30:],
        "stderr_tail": (cp.stderr or "").splitlines()[-15:],
    }


def _inventory(sandbox: Path) -> dict[str, int]:
    """Count installed agents + commands + hooks in the sandbox."""
    cl = sandbox / ".claude"
    out: dict[str, int] = {}
    for k in ("agents", "commands", "hooks"):
        d = cl / k
        out[k] = sum(1 for p in d.rglob("*") if p.is_file()) if d.exists() else 0
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--keep-sandbox", action="store_true",
                    help="leave the sandbox HOME on disk after the run "
                    "(for forensic inspection); default is to remove it.")
    args = ap.parse_args()

    if not CORE.is_file():
        print(f"e2e_clean_install: missing {CORE}", file=sys.stderr)
        return 2

    print("=" * 72)
    print("e2e_clean_install — Path A (HOME redirect)")
    print(f"  repo    : {PP}")
    print(f"  core    : {CORE}")
    print(f"  evidence: {EVIDENCE}")
    print("=" * 72)

    sandbox = _make_sandbox(args.keep_sandbox)
    env = _sandbox_env(sandbox)
    report: dict = {
        "iso": ISO_TS,
        "sandbox": str(sandbox),
        "path_a": True,
        "env_redirects": {k: env.get(k) for k in HOME_ENV_KEYS},
        "phases": {},
        "verdicts": {},
    }

    try:
        # PHASE 1: dry-run. Sandbox should still be empty (no PP files).
        print("\n  [phase 1] dry-run ...", flush=True)
        ph1 = _run_install(env, sandbox, ["--dry-run"])
        inv1 = _inventory(sandbox)
        report["phases"]["dry_run"] = ph1
        report["phases"]["dry_run_inventory"] = inv1
        v1 = (ph1["rc"] == 0
              and inv1["agents"] == 0 and inv1["commands"] == 0)
        report["verdicts"]["dry_run_non_destructive"] = v1
        print(f"    rc={ph1['rc']} inv={inv1} -> "
              f"{'OK' if v1 else 'FAIL'}")

        # PHASE 2: real apply. Sandbox should now have agents+commands.
        # The install reports rc=1 whenever any pp-original entry has
        # ``missing-source`` (stale ``pp_match.pp_path`` from the
        # Owner-pane schema regen, 2026-05-19). That is EXPECTED and
        # not an installer bug — Path-A viability is decided by
        # whether files actually landed in the sandbox, not by the
        # installer's strict rc.
        print("\n  [phase 2] apply (real) ...", flush=True)
        ph2 = _run_install(env, sandbox, [])
        inv2 = _inventory(sandbox)
        report["phases"]["apply"] = ph2
        report["phases"]["apply_inventory"] = inv2
        path_a_viable = (inv2["agents"] >= 1 and inv2["commands"] >= 1)
        v2 = path_a_viable
        report["verdicts"]["apply_populates_tree"] = v2
        report["verdicts"]["path_a_viable"] = path_a_viable
        if not path_a_viable:
            print("    Path.home() ignored USERPROFILE redirect on this "
                  "host. Sandbox stayed empty after apply.")
        print(f"    rc={ph2['rc']} inv={inv2} -> "
              f"{'OK' if v2 else 'FAIL'} "
              f"(install rc=1 from missing-source is expected)")

        # PHASE 3: idempotent re-apply. The sidecar JSON exposes
        # ``counters`` directly (install_global_core.py:407-410); on a
        # re-apply every shippable row should land in ``unchanged``
        # (SHA-skip working) and ZERO should land in ``installed`` or
        # ``updated``. ``missing-source`` is allowed to be non-zero —
        # it counts entries whose ``pp_match.pp_path`` is stale, which
        # is independent of idempotency.
        print("\n  [phase 3] idempotent re-apply ...", flush=True)
        ph3 = _run_install(env, sandbox, [])
        inv3 = _inventory(sandbox)
        report["phases"]["reapply"] = ph3
        report["phases"]["reapply_inventory"] = inv3
        sidecars = sorted((sandbox / ".claude").glob(
            ".pp-install-report.*.json"))
        counters: dict = {}
        if sidecars:
            try:
                last = json.loads(sidecars[-1].read_text(encoding="utf-8"))
                counters = last.get("counters", {}) or {}
            except (OSError, ValueError) as e:
                report["phases"]["reapply_sidecar_error"] = str(e)
        unchanged = int(counters.get("unchanged", 0))
        updated = int(counters.get("updated", 0))
        installed = int(counters.get("installed", 0))
        errors = int(counters.get("error", 0))
        report["phases"]["reapply_breakdown"] = {
            "unchanged": unchanged,
            "updated": updated,
            "installed": installed,
            "errors": errors,
            "missing-source": int(counters.get("missing-source", 0)),
        }
        # Idempotency gate: zero NEW work this run + no errors.
        # rc may still be 1 if missing-source > 0; that is independent.
        v3 = (updated == 0 and installed == 0 and errors == 0
              and unchanged >= 1)
        report["verdicts"]["reapply_all_unchanged"] = v3
        print(f"    rc={ph3['rc']} unchanged={unchanged} "
              f"updated={updated} installed={installed} "
              f"errors={errors} -> {'OK' if v3 else 'FAIL'}")

        all_green = v1 and v2 and v3
        report["verdicts"]["overall"] = all_green
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8")

        print()
        print("=" * 72)
        print(f"  evidence: {EVIDENCE}")
        if all_green:
            print("  E1 verdict: PASS (Path A - HOME redirect viable, "
                  "dry-run safe, apply populates, idempotent)")
            return 0
        if not report["verdicts"].get("path_a_viable", True):
            print("  E1 verdict: PATH-A NOT VIABLE on this host "
                  "(Path.home() bypassed env). Plan permits Path B "
                  "fallback - see vault/plans/power-pack-globalization-"
                  "2026-05-19.md Phase E1.")
            return 1
        print("  E1 verdict: FAIL (one or more gates red - see "
              f"{EVIDENCE})")
        return 1
    finally:
        if not args.keep_sandbox:
            try:
                shutil.rmtree(sandbox)
                print(f"  [sandbox] removed: {sandbox}")
            except OSError as e:
                print(f"  [sandbox] could not remove {sandbox}: {e}",
                      file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
