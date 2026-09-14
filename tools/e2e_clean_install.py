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


def _tree(sandbox: Path) -> set[str]:
    """Every file under the sandbox's .claude, relative and sorted-comparable.

    This is the discriminant the agent/command counts cannot supply. An
    installer that shipped nothing and a HOME redirect the interpreter
    ignored BOTH leave ``agents == 0``; only one of them also leaves the
    tree empty of everything else the install writes (settings.json, the
    session-safety contract, its own sidecar report).
    """
    cl = sandbox / ".claude"
    if not cl.exists():
        return set()
    return {p.relative_to(cl).as_posix() for p in cl.rglob("*") if p.is_file()}


def _sidecar_counters(sandbox: Path) -> dict:
    """The counters the install wrote for its own run, newest sidecar."""
    sidecars = sorted((sandbox / ".claude").glob(".pp-install-report.*.json"))
    if not sidecars:
        return {}
    try:
        last = json.loads(sidecars[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return last.get("counters", {}) or {}


def _enumerated(counters: dict) -> int:
    """How many rows the SHIPPING LOOP considered, per the installer itself.

    Not derived from installed/updated/unchanged: those are also
    incremented by the session-safety deploy that runs in the same pass,
    so summing them measures "the install did some file work" and reads
    above zero even when no agent was ever enumerated. Measured 2026-09-14:
    that sum returned 1 against a shipping loop that ran zero times.

    ``shippable-considered`` is written by the shipping loop and by
    nothing else. An installer too old to report it returns -1, which is
    "could not tell" and must not be read as either answer.
    """
    if "shippable-considered" not in counters:
        return -1
    return int(counters.get("shippable-considered", 0))


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
        # PHASE 1: dry-run changes nothing. Measured as a set difference
        # over the whole tree, not as ``agents == 0``: a dry run that
        # wrote nothing and an installer that ships nothing produce the
        # same zero, so the old form was satisfied by the defect it was
        # meant to exclude.
        print("\n  [phase 1] dry-run ...", flush=True)
        tree0 = _tree(sandbox)
        ph1 = _run_install(env, sandbox, ["--dry-run"])
        inv1 = _inventory(sandbox)
        tree1 = _tree(sandbox)
        # Two artifacts are this HARNESS's, not the install's effect, and
        # both appear on a first dry run: the sidecar is the report OF the
        # run, and settings.json is seeded by _run_install above (lines
        # 96-99) as a precondition before the install is even spawned.
        # Excluding them by name keeps the check a real set difference
        # rather than widening it back to "nothing landed".
        _HARNESS_ARTIFACTS = ("settings.json",)
        added = {p for p in tree1 - tree0
                 if not p.startswith(".pp-install-report.")
                 and p not in _HARNESS_ARTIFACTS}
        report["phases"]["dry_run"] = ph1
        report["phases"]["dry_run_inventory"] = inv1
        report["phases"]["dry_run_tree_added"] = sorted(added)
        v1 = (ph1["rc"] == 0 and not added)
        report["verdicts"]["dry_run_non_destructive"] = v1
        print(f"    rc={ph1['rc']} inv={inv1} added={sorted(added)} -> "
              f"{'OK' if v1 else 'FAIL'}")

        # PHASE 2: real apply. Three INDEPENDENT questions, because the
        # single ``agents >= 1`` check could not tell them apart and
        # answered all three with one hardcoded accusation against the
        # host:
        #   redirect_honored  -- did Path.home() follow USERPROFILE?
        #   installer_enumerated -- did the shipping loop run at all?
        #   apply_populates_tree -- did agents + commands actually land?
        # Measured 2026-09-14: redirect honored, tree populated with
        # settings.json + the session-safety contract, and every shipping
        # counter at zero. The gate had reported that as "Path.home()
        # ignored USERPROFILE redirect ... sandbox stayed empty", which
        # was false in both clauses and sent the reader to a Path-B
        # fallback instead of to the installer.
        print("\n  [phase 2] apply (real) ...", flush=True)
        ph2 = _run_install(env, sandbox, [])
        inv2 = _inventory(sandbox)
        tree2 = _tree(sandbox)
        counters2 = _sidecar_counters(sandbox)
        enumerated2 = _enumerated(counters2)
        redirect_honored = bool(tree2)
        # Tri-state, never collapsed to a boolean: -1 is "the installer is
        # too old to report its own aperture", which is different evidence
        # from "it enumerated nothing" and must not be reported as either.
        installer_enumerated = (None if enumerated2 < 0
                                else enumerated2 > 0)
        path_a_viable = redirect_honored
        v2 = (inv2["agents"] >= 1 and inv2["commands"] >= 1)
        report["phases"]["apply"] = ph2
        report["phases"]["apply_inventory"] = inv2
        report["phases"]["apply_tree"] = sorted(tree2)
        report["phases"]["apply_counters"] = counters2
        report["verdicts"]["apply_populates_tree"] = v2
        report["verdicts"]["path_a_viable"] = path_a_viable
        report["verdicts"]["redirect_honored"] = redirect_honored
        report["verdicts"]["installer_enumerated"] = installer_enumerated
        if not redirect_honored:
            print("    Path.home() ignored the USERPROFILE redirect on "
                  "this host: NOTHING landed in the sandbox, not even "
                  "settings.json. Path A is not viable here.")
        elif installer_enumerated is None:
            print("    Redirect honored, but this install does not report "
                  "'shippable-considered'. Cannot tell 'shipped nothing' "
                  "from 'shipped elsewhere' — INCONCLUSIVE, not a verdict "
                  "about the installer.")
        elif installer_enumerated is False:
            rows = int(counters2.get("inventory-rows-seen", 0))
            print(f"    Redirect HONORED — {len(tree2)} file(s) landed in "
                  f"the sandbox. The install then shipped nothing: the "
                  f"shipping loop considered 0 rows out of "
                  f"{rows} it could read from the inventory, so the loop "
                  f"body never executed. This is the installer, not the "
                  f"host — its reader and tools/_inventory/*.json do not "
                  f"agree on schema.")
        elif not v2:
            print(f"    Redirect honored and the shipping loop ran "
                  f"({enumerated2} row(s) considered), but agents and/or "
                  f"commands did not land: {inv2}. Look at per-row "
                  f"verdicts in {EVIDENCE.name}.")
        print(f"    rc={ph2['rc']} inv={inv2} enumerated={enumerated2} -> "
              f"{'OK' if v2 else 'FAIL'}")

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
        # Attribution order matters. The host is blamed ONLY when the
        # sandbox is genuinely empty; an empty agent count on a populated
        # sandbox is the installer's, and saying otherwise sends the
        # reader to change the wrong thing.
        if report["verdicts"].get("redirect_honored") is False:
            print("  E1 verdict: PATH-A NOT VIABLE on this host "
                  "(Path.home() bypassed env; sandbox empty). Plan "
                  "permits Path B fallback - see vault/plans/power-pack-"
                  "globalization-2026-05-19.md Phase E1.")
            return 1
        # ``is False`` and not ``not ...``: the verdict is tri-state, and
        # None means the installer could not be asked. An unanswerable
        # question must not be reported as an accusation.
        if report["verdicts"].get("installer_enumerated") is False:
            print("  E1 verdict: INSTALLER SHIPS NOTHING. The HOME "
                  "redirect worked; install_global_core.py's shipping "
                  "loop considered zero rows. Its reader and "
                  "tools/_inventory/*.json disagree on schema. This is "
                  "NOT a host limitation and NOT a Path-B case.")
            return 1
        if report["verdicts"].get("installer_enumerated") is None:
            print("  E1 verdict: INCONCLUSIVE. The redirect worked, but "
                  "this install does not report 'shippable-considered', "
                  "so the gate cannot attribute the empty tree. Not a "
                  "pass and not a finding about the installer.")
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
