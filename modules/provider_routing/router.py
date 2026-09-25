"""Choose the provider for one epoch, and write down why, before anything runs.

Clean-room reconstruction of the parts of LiteLLM's router UWCP needs (UWCP
assimilation R4, vault/specs/uwcp-assimilation.md §14; concepts only, no code):
  - a bounded fallback chain that never revisits a target in one decision;
  - retries decided by error CLASS, defaulting to zero;
  - a separate fallback for context-window errors (here: skip every rung that
    shares the window that just truncated);
  - classification by a POSITIVE semantic list, because a provider can fail with
    a success transport (LiteLLM #38535: quota exhaustion arriving as HTTP 200;
    here: a CLI harness printing a limit message and exiting 0);
  - numeric config read so that 0 means zero, never "unset" (LiteLLM #32425);
  - routing state never derived from telemetry (LiteLLM #32574).
Not reconstructed: per-minute cooldowns (meaningless at 4-6 epochs a day; the
equivalent here is the per-(obligation, provider) failure signature rule).

The outcome vocabulary is keos_qwen's (OK, UNAVAILABLE, TRUNCATED, HARNESS_FAILED)
plus two routing-level outcomes it does not carry: FAILED (the subject was asked,
answered, and its answer failed the gate) and AUTH_FAILED (non-retryable, alerts).

`decide()` is a pure function of its input; the record it returns carries every
input, so a decision can be replayed and argued with.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from modules.keos_qwen.outcome import HARNESS_FAILED, OK, TRUNCATED, UNAVAILABLE, from_finish_reason

FAILED = "FAILED"
AUTH_FAILED = "AUTH_FAILED"
OUTCOMES = (OK, UNAVAILABLE, TRUNCATED, HARNESS_FAILED, FAILED, AUTH_FAILED)

AVAILABLE, NOT_AVAILABLE, UNKNOWN = "AVAILABLE", "UNAVAILABLE", "UNKNOWN"

# refusal predicates -- each names a different fix
STALE_AVAILABILITY = "stale_availability"
PROVIDER_UNAVAILABLE = "provider_unavailable"
UNKNOWN_CONTEXT_WINDOW = "unknown_context_window"
OVER_CONTEXT = "over_context"
WINDOW_TRUNCATED = "window_truncated_this_epoch"
BUDGET_UNKNOWN = "budget_unknown"
BUDGET_SPENT = "budget_spent"
SAME_SIGNATURE_TWICE = "same_signature_twice"
VISITED = "visited_this_epoch"
AUTH = "auth_failed"

SELECTION_RULE = "first_feasible_in_chain"

# Retries by outcome class. Everything is 0 on purpose: a retry of the same provider
# with the same input is a blind retry; the chain and the failure-signature rule are
# where a second attempt comes from.
RETRIES = {OK: 0, UNAVAILABLE: 0, TRUNCATED: 0, HARNESS_FAILED: 0, FAILED: 0, AUTH_FAILED: 0}


class ConfigError(ValueError):
    pass


def read_count(raw, name: str) -> int:
    """A non-negative integer setting where 0 is a real value. Missing is an error,
    never a default: `raw or DEFAULT` is how a cap of 0 became unlimited."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise ConfigError(f"{name} is not set")
    try:
        v = int(str(raw).strip())
    except ValueError as exc:
        raise ConfigError(f"{name}={raw!r} is not an integer") from exc
    if v < 0:
        raise ConfigError(f"{name}={v} is negative")
    return v


@dataclass(frozen=True)
class Budget:
    ledger: str
    used: int
    cap: int


@dataclass(frozen=True)
class Candidate:
    provider: str
    window_group: str                  # rungs sharing one ctx window (e.g. "qwen-local-32k")
    ctx_window: int | None = None      # read LIVE from the server; None = not measured
    availability: str = UNKNOWN
    availability_measured_at: float | None = None
    budget: Budget | None = None       # None = no ledger answer, which is not "free"
    budgeted: bool = True              # False only for providers with no quota at all
    prior: float | None = None
    recent_signatures: tuple = ()      # last failure signatures for THIS obligation, newest last


@dataclass(frozen=True)
class RouteInput:
    obligation_class: str
    prompt_tokens: int
    chain: tuple                       # Candidates in preference order
    now: float
    max_availability_age_s: float
    visited: tuple = ()                # providers already tried in this epoch
    truncated_groups: tuple = ()       # window groups that returned TRUNCATED this epoch


def refusal(c: Candidate, inp: RouteInput) -> str:
    """Why this candidate may not run, or "" if it may. Order = cheapest to check."""
    if c.provider in inp.visited:
        return VISITED
    if c.availability_measured_at is None or \
            inp.now - c.availability_measured_at > inp.max_availability_age_s:
        return STALE_AVAILABILITY
    if c.availability != AVAILABLE:
        return AUTH if c.availability == AUTH_FAILED else PROVIDER_UNAVAILABLE
    if c.window_group in inp.truncated_groups:
        return WINDOW_TRUNCATED
    if c.ctx_window is None:
        return UNKNOWN_CONTEXT_WINDOW
    if inp.prompt_tokens > c.ctx_window:
        return OVER_CONTEXT
    if c.budgeted:
        if c.budget is None:
            return BUDGET_UNKNOWN
        if c.budget.used >= c.budget.cap:
            return BUDGET_SPENT
    sig = tuple(s for s in c.recent_signatures if s)
    if len(sig) >= 2 and sig[-1] == sig[-2]:
        return SAME_SIGNATURE_TWICE
    return ""


def decide(inp: RouteInput) -> dict:
    """The decision record. `selected` None means BLOCKED -- never a silent default."""
    seen, rows = set(), []
    selected = None
    for depth, c in enumerate(inp.chain):
        if c.provider in seen:
            raise ConfigError(f"provider {c.provider!r} appears twice in one chain")
        seen.add(c.provider)
        why = refusal(c, inp)
        rows.append({**asdict(c), "feasible": not why, "refusal_reason": why})
        if not why and selected is None:
            selected = (c.provider, depth)
    return {
        "obligation_class": inp.obligation_class,
        "prompt_tokens": inp.prompt_tokens,
        "decided_at": inp.now,
        "max_availability_age_s": inp.max_availability_age_s,
        "visited": list(inp.visited),
        "truncated_groups": list(inp.truncated_groups),
        "candidates": rows,
        "selected": selected[0] if selected else None,
        "fallback_depth": selected[1] if selected else None,
        "selection_rule": SELECTION_RULE,
        "blocked": selected is None,
    }


# --- outcome classification -------------------------------------------------------

# Positive lists of what a limit or an auth failure LOOKS like in a harness's output.
# Seeded from documented wording; the real binaries' exit codes on these messages are
# NOT yet measured (owed by UWCP S6). A miss falls through to the transport verdict,
# and that fall-through is logged by the caller.
QUOTA_PATTERNS = (r"usage limit", r"rate.?limit", r"\bquota\b", r"limit (?:reached|exceeded)",
                  r"credit balance is too low", r"too many requests", r"\b429\b")
AUTH_PATTERNS = (r"\b401\b", r"invalid (?:api )?key", r"unauthori[sz]ed", r"please run /login",
                 r"authentication (?:failed|error|required)", r"not logged in")
_QUOTA = re.compile("|".join(QUOTA_PATTERNS), re.I)
_AUTH = re.compile("|".join(AUTH_PATTERNS), re.I)


@dataclass(frozen=True)
class Classified:
    outcome: str
    reason: str
    retries: int = 0
    matched: str = ""


def classify_cli(exit_code: int | None, output_tail: str, *, gate_passed: bool | None = None) -> Classified:
    """A CLI harness run -> routing outcome. Semantics before transport: an exit 0
    carrying a limit or auth message is not OK."""
    text = output_tail or ""
    m = _AUTH.search(text)
    if m:
        return Classified(AUTH_FAILED, f"auth failure text ({m.group(0)!r}), exit {exit_code}",
                          RETRIES[AUTH_FAILED], m.group(0))
    m = _QUOTA.search(text)
    if m:
        return Classified(UNAVAILABLE, f"limit text ({m.group(0)!r}), exit {exit_code}",
                          RETRIES[UNAVAILABLE], m.group(0))
    if exit_code is None:
        return Classified(HARNESS_FAILED, "no exit status: the run could not be observed")
    if exit_code != 0:
        return Classified(FAILED, f"exit {exit_code}")
    if gate_passed is False:
        return Classified(FAILED, "exit 0, but the gate refused the result")
    return Classified(OK, "exit 0, no limit or auth text")


def classify_server(finish_reason, *, gate_passed: bool | None = None) -> Classified:
    """An OpenAI-compatible server response -> routing outcome (keos_qwen's mapping)."""
    outcome, reason = from_finish_reason(finish_reason)
    if outcome == OK and gate_passed is False:
        return Classified(FAILED, reason + "; the gate refused the result")
    return Classified(outcome, reason, RETRIES[outcome])
