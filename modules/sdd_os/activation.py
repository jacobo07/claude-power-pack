#!/usr/bin/env python3
"""SDD-OS automatic activation -- closes RC-1 and RC-3 (BL-SDD-ACT-001).

RC-1 was that the agent's standing instructions never mention SDD-OS, so
classification depended on the agent remembering a system nobody told it
about. RC-3 was that the one live surface sat at slot 10 of 13 behind a
three-advisory cap and produced nothing.

This module is the instruction surface. It runs on the UserPromptSubmit
chokepoint that already reaches every repo, and it is deliberately NOT
part of the capped advisory queue -- a governance directive that loses a
coin-flip against a cost tip is not a governance directive.

This module NEVER writes to disk. Generation is an explicit act
(`/cpp-sdd-os spec "<task>"`, or `pre_exec_gate.enforce()` called directly).

That was learned the hard way, same day it shipped. The first version tied
auto-generation to "has this repo been scaffolded", treating adoption as
consent. Within hours it had written
`vault/specs/t3-preflight-git-fetch-origin-git-log-oneline-5-cat.md` -- a
spec skeleton named after a PREFLIGHT SHELL BLOCK in the prompt. Worse,
`jit_skill_loader._active_spec()` selects the most-recently-modified spec,
so that empty skeleton immediately became the injected "ACTIVE PROJECT
SPEC", displacing the real one on every subsequent turn.

Three lessons, all now enforced by the single rule "the hook does not
write": (1) a prompt is not a task statement -- it carries preflight
blocks, pasted logs and command output, and a slug derived from it is
noise; (2) a generated artifact that immediately becomes an authoritative
input is a feedback loop, and an EMPTY one is a false source of truth
(T-SDD-OS-SPEC-DRIFT-001); (3) scaffolding a repo is consent to be
GOVERNED, never consent to be WRITTEN TO on every prompt.
Sealed T-SDD-OS-HOOK-GENERATED-ITS-OWN-INPUT-001.

Fail-open absolute: any error yields silence, never a blocked prompt.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

# Below this length a prompt is a follow-up ("continue", "yes", "now fix
# the test"), not a task statement. Classifying those produces noise that
# trains the human to ignore the directive.
MIN_PROMPT_CHARS = 40
COOLDOWN_MINUTES = 20

_HEADER = "=== SDD-OS — Spec First. Execution Second. Validation Always. ==="
_FOOTER = "=== end SDD-OS ==="


def _task_key(prompt: str, cwd: str) -> str:
    """Throttle key that changes when the TASK changes.

    Keying on the project alone would mute the directive for 20 minutes
    across unrelated tasks; keying on the prompt hash lets a genuinely
    new task re-fire immediately while a rephrased retry stays quiet.
    """
    digest = hashlib.sha256(
        f"{Path(cwd).name.lower()}|{prompt.strip().lower()}".encode()
    ).hexdigest()[:12]
    return f"sdd-os-{digest}"


def _is_meta_prompt(prompt: str) -> bool:
    """True for prompts ABOUT the spec system rather than tasks needing one.

    Without this, asking "why doesn't SDD-OS activate?" trips the gate and
    demands a spec for the question itself.
    """
    low = prompt.lower()
    meta = ("sdd-os", "sdd os", "spec gate", "spec-driven development os")
    verbs = ("what", "why", "how", "explain", "show", "list", "status",
             "qué", "que ", "por qué", "porque", "cómo", "como ",
             "explica", "muestra")
    return any(m in low for m in meta) and any(v in low for v in verbs)


def build_directive(prompt: str,
                    cwd: str | Path | None = None) -> str | None:
    """Compose the SDD-OS directive for this prompt, or None for silence.

    READ-ONLY. Calls `evaluate()`, never `enforce()`: this runs on every
    prompt in every repo, and a per-prompt writer is how the module
    generated its own injected input (see module docstring).

    Silence conditions (each deliberate):
      - prompt too short to be a task statement
      - the prompt is a question about SDD-OS itself
      - a spec already declares coverage of this task
      - Tier 0 with nothing worth saying
      - throttled: the same task already got the directive
    """
    try:
        if not prompt or len(prompt.strip()) < MIN_PROMPT_CHARS:
            return None
        if _is_meta_prompt(prompt):
            return None

        root = Path(cwd) if cwd else Path.cwd()

        from modules.pp_agents.proactive_core import is_throttled, mark_fired
        from modules.sdd_os.pre_exec_gate import evaluate

        key = _task_key(prompt, str(root))
        if is_throttled(key, "sdd-os", COOLDOWN_MINUTES):
            return None

        decision = evaluate(prompt, root)

        # A bound spec is the success case: say so once, briefly, so the
        # agent reads it -- then stop talking.
        if decision.action == "proceed":
            body = decision.directive
        elif decision.action == "inline_mini_spec":
            # Tier 0 with no spec is normal and needs no ceremony.
            if decision.tier == 0:
                return None
            body = decision.directive
        else:
            body = decision.directive

        lines = [
            _HEADER,
            body,
            "",
            "This is a standing rule, not a suggestion: at Tier 2+ the "
            "spec precedes the first code edit (PARTE I sec. 4). Tier 0-1 "
            "needs only the inline mini-spec above.",
            _FOOTER,
        ]
        out = "\n".join(lines)
        mark_fired(key, "sdd-os", body[:200])
        return out
    except Exception:
        return None  # fail-open: never block a prompt


__all__ = [
    "MIN_PROMPT_CHARS",
    "COOLDOWN_MINUTES",
    "build_directive",
]
