"""PP Proactive Dispatcher -- Jobs/Woz Standard.

Single entry point called from tools/jit_skill_loader.py on every
UserPromptSubmit. Evaluates the signal modules in priority order,
respects per-agent throttle, and returns at most three advisories per
turn (no-spam invariant).
"""
from __future__ import annotations

from pathlib import Path
import sys

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.pp_agents.proactive_core import (
    AgentConfig,
    evaluate_and_fire,
)
from modules.pp_agents.signals import (
    backlog,
    cascade,
    code_quality,
    cost,
    error_recurrence,
    errors,
    health,
    lessons,
    premise_risk,
    quality,
    sdd_tier,
    setup_scan,
    spec_compliance,
)

MAX_ADVISORIES_PER_TURN = 3

AGENT_CONFIGS: dict[str, AgentConfig] = {
    "pp-code-reviewer": AgentConfig(
        "pp-code-reviewer",
        cooldown_minutes=15,
        min_signal_strength=0.5,
        domains=["code"],
    ),
    "pp-tco-advisor": AgentConfig(
        "pp-tco-advisor",
        cooldown_minutes=20,
        min_signal_strength=0.6,
    ),
    "pp-ceps-analyst": AgentConfig(
        "pp-ceps-analyst",
        cooldown_minutes=10,
        min_signal_strength=0.4,
    ),
    "pp-monitor": AgentConfig(
        "pp-monitor",
        cooldown_minutes=5,
        min_signal_strength=0.9,
    ),
    "pp-uqf-auditor": AgentConfig(
        "pp-uqf-auditor",
        cooldown_minutes=30,
        min_signal_strength=0.3,
    ),
    "pp-never-again": AgentConfig(
        "pp-never-again",
        cooldown_minutes=60,
        min_signal_strength=0.7,
    ),
    "pp-cascade-guard": AgentConfig(
        "pp-cascade-guard",
        cooldown_minutes=5,
        min_signal_strength=0.7,
    ),
    "pp-backlog-autopilot": AgentConfig(
        "pp-backlog-autopilot",
        cooldown_minutes=120,
        min_signal_strength=0.7,
    ),
    # Spec-Driven Department (BL-SPEC-DEPT-001) -- asymmetric cooldowns:
    # a fresh task = fresh context (15m), premise risk slightly longer
    # (20m), recurrence is a slow signal (60m).
    "pp-spec-guardian": AgentConfig(
        "pp-spec-guardian",
        cooldown_minutes=15,
        min_signal_strength=0.5,
        domains=["spec"],
    ),
    # Governance Propagation (BL-GOV-PROP-001) -- cross-repo governance signals.
    # pp-sdd-tier TAKES the spec slot (tier-aware; supersedes the binary
    # spec_compliance gate in the dispatch plan). pp-setup-scan nudges an
    # un-profiled repo once per day.
    "pp-sdd-tier": AgentConfig(
        "pp-sdd-tier",
        cooldown_minutes=5,
        min_signal_strength=0.5,
        domains=["spec"],
    ),
    "pp-setup-scan": AgentConfig(
        "pp-setup-scan",
        cooldown_minutes=1440,   # once per repo per day
        min_signal_strength=0.5,
    ),
    "pp-premise-guardian": AgentConfig(
        "pp-premise-guardian",
        cooldown_minutes=20,
        min_signal_strength=0.5,
    ),
    "pp-error-analyst": AgentConfig(
        "pp-error-analyst",
        cooldown_minutes=60,
        min_signal_strength=0.6,
    ),
}


def dispatch(context: dict) -> list[str]:
    """Evaluate all signals and return at most MAX_ADVISORIES_PER_TURN.

    context keys (all optional, defaults safe):
      project              -- str cwd basename, used for throttle scope
      prompt               -- str current user prompt (spec/tier signals)
      cwd                  -- str active repo path (spec/tier/setup signals)
      last_written_code    -- str newly-written code body
      last_written_file    -- str path of the last touched file
      current_error        -- str current error message text
      session_had_errors   -- bool whether this session saw errors
      errors_fixed         -- int count of errors fixed this session
    """
    project = context.get("project", "global") or "global"
    advisories: list[str] = []

    plan = [
        ("pp-tco-advisor", lambda: cost.evaluate(project)),
        ("pp-monitor", lambda: health.evaluate(project)),
        ("pp-ceps-analyst",
         lambda: errors.evaluate(context.get("current_error", ""), project)),
        ("pp-code-reviewer",
         lambda: code_quality.evaluate(
             context.get("last_written_code", ""), project)),
        ("pp-uqf-auditor",
         lambda: quality.evaluate(
             context.get("last_written_file", ""), project)),
        ("pp-never-again",
         lambda: lessons.evaluate(
             bool(context.get("session_had_errors", False)),
             int(context.get("errors_fixed", 0)), project)),
        ("pp-cascade-guard",
         lambda: cascade.evaluate(
             context.get("current_error", ""), project)),
        ("pp-backlog-autopilot", lambda: backlog.evaluate(project)),
        # Governance Propagation (BL-GOV-PROP-001): sdd_tier takes the spec slot
        # (tier-aware; supersedes the binary spec_compliance gate); setup_scan
        # nudges an un-profiled repo. Both run cross-repo (any cwd). The legacy
        # spec_compliance module is retained (its unit tests still cover it) but
        # is no longer in the dispatch plan -- sdd_tier subsumes its concern.
        ("pp-sdd-tier",
         lambda: sdd_tier.evaluate(
             context.get("prompt", ""), context.get("cwd", ""), project)),
        ("pp-setup-scan",
         lambda: setup_scan.evaluate(context.get("cwd", ""), project)),
        ("pp-premise-guardian",
         lambda: premise_risk.evaluate(
             context.get("current_error", ""),
             bool(context.get("session_had_errors", False)), project)),
        ("pp-error-analyst",
         lambda: error_recurrence.evaluate(
             bool(context.get("session_had_errors", False)), project)),
    ]

    for agent_name, signal_fn in plan:
        if len(advisories) >= MAX_ADVISORIES_PER_TURN:
            break
        config = AGENT_CONFIGS.get(agent_name, AgentConfig(agent_name))
        advisory = evaluate_and_fire(
            agent_name, project, signal_fn, config)
        if advisory:
            advisories.append(advisory)

    return advisories


def dispatch_to_additional_context(context: dict) -> str | None:
    """Format advisories for jit_skill_loader additionalContext injection.

    Returns None when no advisories fire (silence = approval).
    """
    advisories = dispatch(context)
    if not advisories:
        return None
    header = "--- PP Agents (Jobs/Woz Standard) ---"
    body = "\n".join(advisories)
    footer = "--- end PP Agents ---"
    return f"\n{header}\n{body}\n{footer}\n"


__all__ = [
    "dispatch",
    "dispatch_to_additional_context",
    "AGENT_CONFIGS",
    "MAX_ADVISORIES_PER_TURN",
]
