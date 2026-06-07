#!/usr/bin/env python3
"""Secure Installer -- CPP Setup OS Pillar 3 (Sprint 3 / M13).

Turns a ranked recommendation list into a DRY-RUN install plan with a
rollback recipe, and runs a Secret Firewall scan FIRST. Never applies
autonomously; owner-side (global config) steps are surfaced separately
(source: Dataset CPP Setup 1.txt sec. 13 DRY-RUN FIRST DOCTRINE, sec. 31
PHASE 1 -- Secret Firewall before installer, sec. 54 ROLLBACK SYSTEM).

Doctrine encoded as hard gates:
  * secret scan runs before any plan is deemed safe; CRITICAL hits ->
    blocked (HR-SECRET / Phase-1: firewall before install);
  * every step ships a rollback action (no step without an undo);
  * owner-side steps (global ~/.claude config) are never auto-applied
    (HR-001 / Owner-side action doctrine).

stdlib-only; the secret scan reuses the M1 firewall (fail-open if absent).
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from pathlib import Path

from .roi_analyzer import Recommendation, analyze
from .scanner import scan


@dataclass
class InstallStep:
    rec_id: str
    action: str
    target: str
    install_mode: str       # local | owner-side | dry-run-only
    rollback_action: str    # the explicit undo for this step


@dataclass
class InstallPlan:
    steps: list[InstallStep] = dc_field(default_factory=list)
    owner_side_actions: list[str] = dc_field(default_factory=list)
    rollback_recipe: list[str] = dc_field(default_factory=list)
    secret_critical_hits: int = 0
    secret_scan_ran: bool = False
    blocked_reason: str | None = None
    safe_to_apply: bool = False

    @property
    def dry_run(self) -> bool:
        return True  # this engine NEVER applies; it only plans.


def _secret_scan_critical(root: Path) -> tuple[bool, int]:
    """Return (scan_ran, critical_hit_count). Fail-open: if the firewall
    module is unavailable, report not-ran rather than crashing."""
    try:
        import sys
        pp_root = Path(__file__).resolve().parents[2]
        if str(pp_root) not in sys.path:
            sys.path.insert(0, str(pp_root))
        from tools.secret_scan_repo import scan_repo
        hits = scan_repo(root, "CRITICAL", honor_allowlist=True)
        return True, len(hits)
    except Exception:
        return False, 0


def _rollback_for(rec: Recommendation) -> str:
    if rec.install_mode == "owner-side":
        return ("revert the ~/.claude config entry added for "
                f"{rec.id!r} (settings_merger supports unregister).")
    if rec.category in ("docs", "command", "skill"):
        return f"delete the file(s) created for {rec.id!r} (git clean)."
    if rec.category == "hook":
        return f"remove the {rec.id!r} hook registration; restore settings.json backup."
    return f"git restore / remove the changes introduced by {rec.id!r}."


def dry_run(recommendations: list[Recommendation],
            root: str | Path | None = None) -> InstallPlan:
    """Build a dry-run install plan with rollback, after a secret scan.

    The plan is advisory: local steps are proposed (never auto-applied),
    owner-side steps are listed for the Owner. A CRITICAL secret hit
    blocks the plan (firewall-before-install).
    """
    r = Path(root).resolve() if root else Path.cwd()
    plan = InstallPlan()

    ran, crit = _secret_scan_critical(r)
    plan.secret_scan_ran = ran
    plan.secret_critical_hits = crit

    for rec in recommendations:
        step = InstallStep(
            rec_id=rec.id,
            action=f"[DRY-RUN] would {('apply locally' if rec.install_mode == 'local' else 'propose (' + rec.install_mode + ')')}: {rec.title}",
            target=str(r),
            install_mode=rec.install_mode,
            rollback_action=_rollback_for(rec))
        plan.steps.append(step)
        plan.rollback_recipe.append(f"{rec.id}: {step.rollback_action}")
        if rec.install_mode == "owner-side":
            plan.owner_side_actions.append(
                f"{rec.title} -- requires Owner approval (global config; "
                "HR-001 Owner-side action).")

    if crit > 0:
        plan.blocked_reason = (
            f"{crit} CRITICAL secret(s) detected -- Phase 1 doctrine: "
            "rotate/scrub via the Secret Firewall BEFORE any install. "
            "No raw values surfaced (HR-SECRET-002).")
        plan.safe_to_apply = False
    elif not plan.steps:
        plan.blocked_reason = "no recommendations to install."
        plan.safe_to_apply = False
    else:
        plan.safe_to_apply = True

    return plan


def dry_run_path(root: str | None = None) -> InstallPlan:
    """Convenience: scan -> analyze -> dry-run plan."""
    profile = scan(root)
    return dry_run(analyze(profile), root)


def render(plan: InstallPlan) -> str:
    lines = ["=== Secure Installer -- DRY RUN (nothing applied) ==="]
    lines.append(f"secret scan ran: {plan.secret_scan_ran}; "
                 f"CRITICAL hits: {plan.secret_critical_hits}")
    lines.append(f"safe to apply: {plan.safe_to_apply}"
                 + (f"  BLOCKED: {plan.blocked_reason}"
                    if plan.blocked_reason else ""))
    lines.append(f"\nSteps ({len(plan.steps)}):")
    for s in plan.steps:
        lines.append(f"  - {s.action}\n    rollback: {s.rollback_action}")
    if plan.owner_side_actions:
        lines.append("\nOwner-side actions (not auto-applied):")
        for a in plan.owner_side_actions:
            lines.append(f"  - {a}")
    lines.append(f"\nRollback recipe: {len(plan.rollback_recipe)} step(s) "
                 "(one per change).")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Secure Installer (dry-run)")
    ap.add_argument("--path", default=".")
    ap.add_argument("--apply", action="store_true",
                    help="reserved; this engine is dry-run-only by design")
    args = ap.parse_args(argv)
    if args.apply:
        print("Refusing: secure_installer is dry-run-only. Owner applies "
              "after review (HR-001 / dry-run-first doctrine).")
    print(render(dry_run_path(args.path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
