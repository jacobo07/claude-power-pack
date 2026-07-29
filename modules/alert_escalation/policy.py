"""Escalation policy for repeat alerts that nobody resolves.

A detector that raises the identical alert every session is not providing
detection: it trains its reader to ignore it. Measured origin -- 333
`mirror-drift` handoffs over 67 days, all naming one pair, none escalated,
none suppressed (`vault/plans/igef-2026-07-29.md`).

The policy answers one question per finding: given how many times this exact
finding has been reported since it was last seen resolved, does the detector
write another routine notice, promote it to URGENT, or stay quiet because an
URGENT promotion is already standing?

Routes
    ROUTINE   below threshold -- write the ordinary handoff.
    ESCALATE  threshold reached -- promote to URGENT, refresh ESCALATED.md.
    SUPPRESS  already escalated and not yet stale -- write nothing. This is
              what stops the 333-file pile: once promoted, the finding is
              represented by one standing row, not another file per session.

Resolution is a real transition, not an assumption. `note_resolved` is called
by the detector when the condition no longer holds; it stamps an epoch, and
occurrences are only ever counted after that epoch. Without that producer the
counter could never fall and every finding would escalate eventually.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

LEDGER_NAME = "escalations.json"
STANDING_NAME = "ESCALATED.md"

DEFAULT_ESCALATE_AFTER = 3
DEFAULT_RE_ESCALATE_DAYS = 7
MIN_ESCALATE_AFTER = 2  # a threshold of 1 is "escalate everything" -- not a policy

CONFIG_REL = ("vault", "config", "alert_escalation.json")
ENV_THRESHOLD = "PP_ALERT_ESCALATION_THRESHOLD"
ENV_RE_ESCALATE_DAYS = "PP_ALERT_RE_ESCALATE_DAYS"

KEY_MARKER = "**Finding key**:"
SECONDS_PER_DAY = 86400

ROUTINE = "ROUTINE"
ESCALATE = "ESCALATE"
SUPPRESS = "SUPPRESS"

# handoff files are named <kind>-2026-07-29T11-34-39Z.md
_TS_RX = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})Z")


@dataclass(frozen=True)
class Policy:
    escalate_after: int = DEFAULT_ESCALATE_AFTER
    re_escalate_after_days: int = DEFAULT_RE_ESCALATE_DAYS
    source: str = "default"


@dataclass
class Decision:
    route: str
    occurrences: int
    threshold: int
    reason: str
    key: str = ""
    escalated_at: float = 0.0

    @property
    def should_write_routine(self) -> bool:
        return self.route == ROUTINE

    @property
    def should_escalate(self) -> bool:
        return self.route == ESCALATE


@dataclass
class Entry:
    kind: str = ""
    occurrences: int = 0
    first_seen: float = 0.0
    last_seen: float = 0.0
    resolved_at: float = 0.0
    escalated_at: float = 0.0
    bootstrapped: bool = False
    detail: str = ""
    history: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "occurrences": self.occurrences,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "resolved_at": self.resolved_at,
            "escalated_at": self.escalated_at,
            "bootstrapped": self.bootstrapped,
            "detail": self.detail,
            "history": self.history[-_HISTORY_CAP:],
        }


_HISTORY_CAP = 10


def _coerce_int(raw, fallback: int, floor: int) -> int:
    try:
        val = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    return val if val >= floor else floor


def load_policy(repo_root: Path) -> Policy:
    """Config file first, environment second. Never hardcoded at the call site."""
    escalate_after = DEFAULT_ESCALATE_AFTER
    re_days = DEFAULT_RE_ESCALATE_DAYS
    source = "default"

    cfg_path = Path(repo_root).joinpath(*CONFIG_REL)
    try:
        if cfg_path.is_file():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
            if isinstance(cfg, dict):
                escalate_after = _coerce_int(
                    cfg.get("escalate_after", escalate_after),
                    escalate_after, MIN_ESCALATE_AFTER)
                re_days = _coerce_int(
                    cfg.get("re_escalate_after_days", re_days), re_days, 1)
                source = str(cfg_path)
    except (OSError, ValueError):
        pass  # a broken config must not disable detection; defaults stand

    env_threshold = os.environ.get(ENV_THRESHOLD)
    if env_threshold:
        escalate_after = _coerce_int(
            env_threshold, escalate_after, MIN_ESCALATE_AFTER)
        source = f"env:{ENV_THRESHOLD}"
    env_days = os.environ.get(ENV_RE_ESCALATE_DAYS)
    if env_days:
        re_days = _coerce_int(env_days, re_days, 1)

    return Policy(escalate_after=escalate_after,
                  re_escalate_after_days=re_days, source=source)


def finding_key(kind: str, *identity: str) -> str:
    """Stable identity for one finding. Two different pairs are two findings."""
    parts = [re.sub(r"\s+", " ", str(p).strip()) for p in identity if str(p).strip()]
    return f"{kind}::" + "|".join(parts) if parts else kind


def handoff_timestamp(path: Path) -> float:
    m = _TS_RX.search(path.name)
    if m:
        y, mo, d, h, mi, s = (int(x) for x in m.groups())
        try:
            return time.mktime((y, mo, d, h, mi, s, 0, 0, -1))
        except (OverflowError, ValueError):
            pass
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def count_prior_occurrences(handoff_dir: Path, kind: str, key: str,
                            legacy_match: str = "", since: float = 0.0) -> int:
    """Occurrences already on disk, after `since`.

    Counted from the handoff files themselves because those files are the
    authoritative record -- a ledger introduced today cannot witness a
    two-month-old repeat, and the pre-existing corpus is precisely the case
    this policy exists to catch.
    """
    handoff_dir = Path(handoff_dir)
    if not handoff_dir.is_dir():
        return 0
    marker = f"{KEY_MARKER} `{key}`"
    count = 0
    for path in handoff_dir.glob(f"{kind}-*.md"):
        if handoff_timestamp(path) <= since:
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if marker in body or (legacy_match and legacy_match in body):
            count += 1
    return count


def load_ledger(handoff_dir: Path) -> dict:
    path = Path(handoff_dir) / LEDGER_NAME
    try:
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(raw, dict):
                return {k: Entry(**{f: v for f, v in val.items()
                                    if f in Entry.__dataclass_fields__})
                        for k, val in raw.items() if isinstance(val, dict)}
    except (OSError, ValueError, TypeError):
        pass
    return {}


def save_ledger(handoff_dir: Path, ledger: dict) -> None:
    path = Path(handoff_dir)
    path.mkdir(parents=True, exist_ok=True)
    payload = {k: e.as_dict() for k, e in ledger.items()}
    (path / LEDGER_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def observe(handoff_dir: Path, policy: Policy, kind: str, key: str,
            detail: str = "", legacy_match: str = "",
            now: float = 0.0) -> Decision:
    """Record one detection of `key` and decide what the detector may write."""
    now = now or time.time()
    ledger = load_ledger(handoff_dir)
    entry = ledger.get(key) or Entry(kind=kind)
    entry.kind = kind or entry.kind

    if not entry.bootstrapped:
        # First run under this policy: adopt the history already on disk so a
        # long-standing repeat escalates immediately instead of restarting at 1.
        entry.occurrences = count_prior_occurrences(
            handoff_dir, kind, key, legacy_match, entry.resolved_at)
        entry.bootstrapped = True

    entry.occurrences += 1
    entry.first_seen = entry.first_seen or now
    entry.last_seen = now
    entry.detail = detail or entry.detail
    entry.history = (entry.history + [round(now, 3)])[-_HISTORY_CAP:]

    decision = _route(entry, policy, now)
    if decision.route == ESCALATE:
        entry.escalated_at = now

    ledger[key] = entry
    save_ledger(handoff_dir, ledger)
    if decision.route == ESCALATE:
        write_standing_report(handoff_dir, ledger, policy)

    decision.key = key
    decision.escalated_at = entry.escalated_at
    return decision


def _route(entry: Entry, policy: Policy, now: float) -> Decision:
    threshold = policy.escalate_after
    if entry.occurrences < threshold:
        return Decision(ROUTINE, entry.occurrences, threshold,
                        f"{entry.occurrences} of {threshold} before escalation")
    if not entry.escalated_at:
        return Decision(ESCALATE, entry.occurrences, threshold,
                        f"{entry.occurrences} unresolved occurrences "
                        f"reached the threshold of {threshold}")
    stale_after = policy.re_escalate_after_days * SECONDS_PER_DAY
    if now - entry.escalated_at >= stale_after:
        return Decision(ESCALATE, entry.occurrences, threshold,
                        f"still unresolved {int((now - entry.escalated_at) / SECONDS_PER_DAY)} "
                        f"days after the last promotion")
    return Decision(SUPPRESS, entry.occurrences, threshold,
                    "an URGENT promotion for this finding is already standing")


def note_resolved(handoff_dir: Path, key: str, now: float = 0.0) -> bool:
    """The condition no longer holds. Clears the count and the promotion.

    This is the producer that makes the counter fall. Its absence would make
    every long-lived finding escalate regardless of whether anyone fixed it.
    """
    now = now or time.time()
    ledger = load_ledger(handoff_dir)
    entry = ledger.get(key)
    if entry is None or (entry.occurrences == 0 and not entry.escalated_at):
        return False
    policy_reset = Entry(kind=entry.kind, resolved_at=now, bootstrapped=True,
                         first_seen=entry.first_seen, last_seen=entry.last_seen,
                         detail=entry.detail)
    ledger[key] = policy_reset
    save_ledger(handoff_dir, ledger)
    write_standing_report(handoff_dir, ledger, None)
    return True


def open_escalations(ledger: dict) -> list:
    return sorted(
        ((k, e) for k, e in ledger.items()
         if e.escalated_at and e.escalated_at > e.resolved_at),
        key=lambda kv: kv[1].escalated_at)


def write_standing_report(handoff_dir: Path, ledger: dict,
                          policy: Policy | None) -> Path:
    """One file naming every finding currently promoted to URGENT.

    Rewritten in place, never appended. A report that grows by one file per
    session is the defect this module exists to remove.
    """
    handoff_dir = Path(handoff_dir)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    path = handoff_dir / STANDING_NAME
    path.write_text(render_standing_report(ledger, policy), encoding="utf-8")
    return path


def render_standing_report(ledger: dict, policy: Policy | None) -> str:
    rows = open_escalations(ledger)
    lines = ["# Escalated findings -- URGENT", ""]
    if policy is not None:
        lines.append(f"Policy: escalate after {policy.escalate_after} unresolved "
                     f"occurrences; re-state every {policy.re_escalate_after_days} "
                     f"days. Source: `{policy.source}`.")
        lines.append("")
    if not rows:
        lines += ["No finding is currently escalated.", "",
                  "*Rewritten in place by modules/alert_escalation.*", ""]
        return "\n".join(lines)
    lines += [
        f"{len(rows)} finding(s) repeated past the escalation threshold without "
        "being resolved. Routine notices for these are suppressed -- this file "
        "is their single standing record.",
        "",
        "| Finding | Kind | Occurrences | First seen | Escalated |",
        "|---|---|---|---|---|",
    ]
    for key, e in rows:
        lines.append(
            f"| `{key}` | {e.kind} | {e.occurrences} | {_stamp(e.first_seen)} "
            f"| {_stamp(e.escalated_at)} |")
    lines += ["", "## Detail", ""]
    for key, e in rows:
        lines.append(f"### `{key}`")
        lines.append("")
        lines.append(e.detail or "(no detail recorded)")
        lines.append("")
    lines.append("*Rewritten in place by modules/alert_escalation; a row leaves "
                 "when the detector observes the condition resolved.*")
    lines.append("")
    return "\n".join(lines)


def _stamp(ts: float) -> str:
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
