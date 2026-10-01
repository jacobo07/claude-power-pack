"""Spec readiness -- may this spec AUTHORIZE execution at this tier? (W3, D1/D6)

A spec used to unlock work because it existed and lexically bound. Readiness moves the authority
boundary from "spec present" to "spec execution-ready". Generation and readiness are separate
events: a generated skeleton is `status: draft` with blank criteria and is never ready.

Two grammars, judged differently.

READINESS FORMAT -- any of the keys below in the front matter. Flat items only:
    status: ready
    scope: [modules/billing/]
    open_questions:
      - Q1 | RESOLVED | <answer>            RESOLVED / ASSUMED / NONE keep it ready
      - Q2 | OWNER_DECISION | <question>    OWNER_DECISION / RESEARCH / BLOCKING block it
    acceptance:
      - AC-1 | verify: python tools/test_x.py      every item names a runnable check
    must_still_pass:
      - python tools/test_sdd_os.py                or "none: <reason>"
    checkpoints:                                   required at effective Tier 3
      - CP-1 | <falsifiable checkpoint>
Missing, blank and "none" are three different states: a missing key is NOT_READY, an explicit
`none` (or "none: reason") is an answer. An unfilled authoring marker (TBD, N/A, <...>, "...")
counts as blank, a RESOLVED/ASSUMED question needs its answer written, and `verify:` must name a
command or a V-gate id. Nested YAML is MALFORMED -- reported, never half-read.

LEGACY FORMAT -- none of those keys. Measured 2026-10-01 over the 43 declared specs in this repo:
none used AC-n lines; their proof was V-gate ids and runnable commands, and `status:` was prose
("APPROVED -- Owner ...", "STOP #1 -- BLOCKING", "DELIVERED ..."). Demanding the new keys would
invalidate specs that already carry the information, so a legacy spec is judged semantically:
an approving status AND at least one falsifiable proof (a V-gate id or a runnable command)
-> LEGACY_READY, until LEGACY_WINDOW_ENDS; otherwise NOT_READY with the reason named.

Tier reconciliation (D6): requirements are judged at max(task tier, spec tier). A Tier 1 spec
cannot authorize a Tier 3 task merely by binding to it.

Pure: reads the file, never executes `verify`, never writes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

READY, LEGACY_READY, NOT_READY, MALFORMED, UNJUDGEABLE = (
    "READY", "LEGACY_READY", "NOT_READY", "MALFORMED", "UNJUDGEABLE")
# The approved migration window (plan audit gap 9). After it, a legacy spec must migrate.
LEGACY_WINDOW_ENDS = date(2026, 11, 1)

READINESS_KEYS = ("open_questions", "acceptance", "must_still_pass", "checkpoints", "scope")
_LIST_KEYS = ("open_questions", "acceptance", "must_still_pass", "checkpoints")
_Q_OK = {"RESOLVED", "ASSUMED", "NONE"}
_Q_BLOCK = {"OWNER_DECISION", "RESEARCH", "BLOCKING"}

_FENCE = "---"
# "- id: AC-1" is a nested mapping; "- none: <reason>" is the explicit-none grammar, not a mapping.
_ITEM_KV = re.compile(r"^-\s+(?!none\s*:)[A-Za-z_]\w*\s*:\s", re.I)
_VERIFY = re.compile(r"\|\s*verify\s*:\s*(\S.*)$", re.I)
_NONE_REASON = re.compile(r"^none\s*:\s*\S", re.I)
# "2", "T2", or prose like "SDD-OS T2 (module + persisted config)" -- measured in real specs.
_TIER = re.compile(r"^\s*([0-3])\b|\bT([0-3])\b", re.I)
# Legacy status: the FIRST keyword in the prose decides ("APPROVED ... audit pending" approves;
# "STOP #1 delivered inline; awaiting approval" blocks).
_STATUS_WORD = re.compile(
    r"\b(approved|executing|executed|delivered|shipped|built|implemented|active|landed|verified|"
    r"sealed|done|complete|completed|ready|accepted|stop|blocking|blocked|awaiting|draft|proposed|"
    r"planned|plan|pending|wip|todo|spec)\b", re.I)
_APPROVING = {"approved", "executing", "executed", "delivered", "shipped", "built", "implemented",
              "active", "landed", "verified", "sealed", "done", "complete", "completed", "ready",
              "accepted"}
_V_GATE = re.compile(r"\bV-[A-Z0-9][A-Z0-9-]{2,}")
_COMMAND = re.compile(r"\b(?:python3?|pytest|node|npm|pnpm|mix|cargo|go test)\s+[\w./\\-]+")
_BLANK_AC = re.compile(r"(?m)^\s*-?\s*AC-\d+\s*:\s*$")
# Authoring placeholders. A field holding one of these was never filled in, so it is judged as
# blank -- a heading, a TBD or an angle-bracket prompt is not project-specific evidence.
_PLACEHOLDER = re.compile(
    r"^\s*(?:tbd|tba|todo|fixme|xxx+|n/?a|\?+|\.{3,}|…|<[^>]*>|\[[^\]]*\]|-)?\s*$", re.I)


def _placeholder(text) -> bool:
    return bool(_PLACEHOLDER.match(str(text or "")))


def _runnable(text: str) -> bool:
    """A check someone can execute or look up: a command or a V-gate id."""
    return bool(_COMMAND.search(text) or _V_GATE.search(text))


@dataclass(frozen=True)
class Readiness:
    state: str
    missing: tuple = ()                 # reason codes, e.g. "status:draft", "acceptance:missing"
    effective_tier: int = 0
    spec_tier: int | None = None
    fmt: str = "readiness"              # "readiness" | "legacy"
    notes: tuple = field(default_factory=tuple)

    @property
    def authorizes(self) -> bool:
        return self.state in (READY, LEGACY_READY)


def _front_matter_lines(text: str) -> list[str] | None:
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip().lstrip("﻿"):
        i += 1
    if i >= len(lines) or lines[i].strip().lstrip("﻿") != _FENCE:
        return None
    out = []
    for raw in lines[i + 1:]:
        if raw.strip() == _FENCE:
            return out
        out.append(raw)
    return None                          # unterminated front matter


def _parse(lines: list[str]) -> tuple[dict, list[str]]:
    """Flat key/value + flat list items. Returns (fields, malformed reasons)."""
    fields: dict = {}
    bad: list[str] = []
    key = None
    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if s.startswith("- ") and key:
            if _ITEM_KV.match(s) and key in _LIST_KEYS:
                bad.append(f"{key}:nested-mapping")
            fields.setdefault(key, [])
            if isinstance(fields[key], list):
                fields[key].append(s[2:].strip().strip("'\""))
            continue
        if indent >= 2 and key in _LIST_KEYS:
            bad.append(f"{key}:nested-line")
            continue
        if ":" not in s:
            continue
        k, _, v = s.partition(":")
        key = k.strip().lower()
        v = v.strip()
        if not v:
            fields[key] = []
        elif v.startswith("[") and v.endswith("]"):
            fields[key] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
            key = None
        else:
            fields[key] = v.strip("'\"")
            key = None
    return fields, bad


def _spec_tier(raw) -> int | None:
    m = _TIER.search(str(raw or ""))
    return int(m.group(1) or m.group(2)) if m else None


def _judge_readiness_format(f: dict, eff: int) -> list[str]:
    missing: list[str] = []
    status = str(f.get("status", "")).strip().lower()
    if not status:
        missing.append("status:missing")
    elif status != "ready":
        missing.append(f"status:{status.split()[0]}")

    scope = f.get("scope")
    if scope is None:
        missing.append("scope:missing")
    elif not scope or all(_placeholder(s) for s in (scope if isinstance(scope, list) else [scope])):
        missing.append("scope:blank")

    oq = f.get("open_questions")
    if oq is None:
        missing.append("open_questions:missing")
    elif isinstance(oq, str):
        if oq.strip().lower() != "none":
            missing.append("open_questions:not-a-list")
    elif not oq:
        missing.append("open_questions:blank")
    else:
        for item in oq:
            parts = [p.strip() for p in item.split("|")]
            kind = parts[1].upper() if len(parts) > 1 else ""
            answer = "|".join(parts[2:]).strip()
            if kind in _Q_BLOCK:
                missing.append(f"open_questions:{parts[0]}:{kind}")
            elif kind not in _Q_OK:
                missing.append(f"open_questions:{parts[0]}:unclassified")
            elif kind != "NONE" and _placeholder(answer):
                # "Q1 | RESOLVED |" claims a resolution it does not state.
                missing.append(f"open_questions:{parts[0]}:{kind.lower()}-without-answer")

    ac = f.get("acceptance")
    if ac is None:
        missing.append("acceptance:missing")
    elif not ac or isinstance(ac, str):
        missing.append("acceptance:blank")
    else:
        for item in ac:
            m = _VERIFY.search(item)
            if not m:
                missing.append(f"acceptance:{item.split('|')[0].strip()}:no-verify")
            elif not _runnable(m.group(1)):
                # "verify: TBD" or "verify: it works" names no instrument.
                missing.append(f"acceptance:{item.split('|')[0].strip()}:verify-not-runnable")

    msp = f.get("must_still_pass")
    if msp is None:
        missing.append("must_still_pass:missing")
    elif not msp:
        missing.append("must_still_pass:blank")
    else:
        items = msp if isinstance(msp, list) else [msp]
        if not all(_COMMAND.search(i) or (_NONE_REASON.match(i)
                                          and not _placeholder(i.partition(":")[2]))
                   for i in items):
            missing.append("must_still_pass:not-a-command-or-none-reason")

    if eff >= 3:
        cp = f.get("checkpoints")
        if not cp or isinstance(cp, str) or all(
                _placeholder("|".join(c.split("|")[1:])) for c in cp):
            missing.append("checkpoints:required-at-tier-3")
    return missing


def _judge_legacy(f: dict, body: str, today: date) -> tuple[str, list[str], list[str]]:
    missing: list[str] = []
    notes = ["legacy format: migrate to readiness keys (see modules/sdd_os/readiness.py)"]
    m = _STATUS_WORD.search(str(f.get("status", "")))
    if not m:
        missing.append("status:not-stated")
    elif m.group(1).lower() not in _APPROVING:
        missing.append(f"status:{m.group(1).lower()}")
    if _BLANK_AC.search(body):
        missing.append("acceptance:blank-skeleton")
    if not (_V_GATE.search(body) or _COMMAND.search(body)):
        missing.append("proof:no-v-gate-or-command")
    if missing:
        return NOT_READY, missing, notes
    if today > LEGACY_WINDOW_ENDS:
        return NOT_READY, [f"legacy:window-ended-{LEGACY_WINDOW_ENDS.isoformat()}"], notes
    return LEGACY_READY, [], notes


def assess(spec_path: Path | str, task_tier: int, *, today: date | None = None) -> Readiness:
    today = today or date.today()
    try:
        text = Path(spec_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return Readiness(UNJUDGEABLE, (f"unreadable:{type(exc).__name__}",), effective_tier=task_tier)
    lines = _front_matter_lines(text)
    if lines is None:
        return Readiness(NOT_READY, ("front-matter:missing-or-unterminated",), effective_tier=task_tier)
    fields, bad = _parse(lines)
    spec_tier = _spec_tier(fields.get("tier"))
    eff = max(int(task_tier), spec_tier if spec_tier is not None else int(task_tier))
    notes: tuple = ()
    if spec_tier is not None and spec_tier < int(task_tier):
        notes = (f"spec tier {spec_tier} < task tier {task_tier}: judged at Tier {eff}",)
    if bad:
        return Readiness(MALFORMED, tuple(sorted(set(bad))), eff, spec_tier, "readiness", notes)
    if any(k in fields for k in READINESS_KEYS):
        missing = _judge_readiness_format(fields, eff)
        return Readiness(NOT_READY if missing else READY, tuple(missing), eff, spec_tier,
                         "readiness", notes)
    state, missing, lnotes = _judge_legacy(fields, text, today)
    return Readiness(state, tuple(missing), eff, spec_tier, "legacy", notes + tuple(lnotes))


def audit(root: Path | str, task_tier: int = 2, *, today: date | None = None) -> list[tuple]:
    """Judge every DECLARED spec in a repo: [(relpath, Readiness)]. The legacy-migration report."""
    from modules.sdd_os.spec_binding import iter_candidates, read_covers
    root = Path(root)
    out = []
    for p in sorted(iter_candidates(root), key=lambda q: q.as_posix().lower()):
        if read_covers(p) is not None:
            out.append((p.relative_to(root).as_posix(), assess(p, task_tier, today=today)))
    return out


def _main(argv: list[str]) -> int:
    import argparse
    from collections import Counter
    ap = argparse.ArgumentParser(description="Spec readiness audit (legacy migration report).")
    ap.add_argument("--audit", default=".", help="repo root (default: cwd)")
    ap.add_argument("--tier", type=int, default=2)
    ap.add_argument("--today", help="ISO date, to judge against a fixed legacy window")
    a = ap.parse_args(argv)
    rows = audit(a.audit, a.tier, today=date.fromisoformat(a.today) if a.today else None)
    for rel, r in rows:
        print(f"{r.fmt:9} {r.state:12} {rel}  {' '.join(r.missing)}")
    print(f"declared={len(rows)} " + " ".join(
        f"{k}={v}" for k, v in sorted(Counter(r.state for _, r in rows).items())))
    return 0


__all__ = ["READY", "LEGACY_READY", "NOT_READY", "MALFORMED", "UNJUDGEABLE", "LEGACY_WINDOW_ENDS",
           "READINESS_KEYS", "Readiness", "assess", "audit"]


if __name__ == "__main__":
    import sys
    _root = Path(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    sys.exit(_main(sys.argv[1:]))
