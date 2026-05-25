#!/usr/bin/env python3
"""Cascade Error Prevention System (CEPS) -- single-file core module.

Covers FASE 2 micro-commits M8 (3 triggers), M9 (root-cause extractor),
M10 (forward propagation), and M11 (distributor). Deviation from the
plan's per-component file split is deliberate: each component is 50-150
LOC, splitting adds boilerplate without benefit and increases the
maintenance surface.

Schema authority: vault/ceps/schema.json (M7).
Pattern index:   vault/ceps/patterns.db (FTS5 sidecar, own rowid space,
                 never touches turns_fts -- BL-0068 apex doctrine).
Event log:       vault/ceps/events.jsonl (append-only, atomic write).
Distribution:    vault/knowledge_base/{session_lessons,ukdl-universal}.md
                 (atomic write -- never `cat >>` after 2026-05-23
                 apex-corruption empirical lesson).

Fail-open semantics (Ley 24): any internal error is logged to
~/.claude/logs/ceps.log and the call returns None / [] / empty dict.
CEPS is never allowed to disrupt the user's prompt path.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"
SCHEMA_PATH = PP_ROOT / "vault" / "ceps" / "schema.json"
EVENTS_PATH = PP_ROOT / "vault" / "ceps" / "events.jsonl"
DRAFTS_DIR = PP_ROOT / "vault" / "ceps" / "drafts"
DB_PATH = PP_ROOT / "vault" / "ceps" / "patterns.db"
LESSONS_PATH = PP_ROOT / "vault" / "knowledge_base" / "session_lessons.md"
UKDL_PATH = PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"
LOG = HOME / ".claude" / "logs" / "ceps.log"

VALID_CATEGORIES = (
    "regression", "security", "drift", "scaffold", "incomplete-shell",
    "integration", "spec-violation", "tooling", "env",
)
AUTO_TEST_CATEGORIES = {"regression", "security", "drift"}
VALID_CONFIDENCE = ("low", "high")

# Prevention-rule templates by category (M9). Each takes {root_cause,
# subsystem} substitution.
RULE_TEMPLATES = {
    "regression": (
        "Before touching {subsystem}, verify the regression scenario "
        "({root_cause_short}) is still covered by a passing test."
    ),
    "security": (
        "When editing {subsystem}, verify the security invariant "
        "({root_cause_short}) is preserved and never bypassed."
    ),
    "drift": (
        "Watch for drift in {subsystem}: {root_cause_short}. Sync the "
        "canonical source before editing the mirror."
    ),
    "scaffold": (
        "Do not emit incomplete shells in {subsystem}: {root_cause_short}. "
        "Build it end-to-end or state the gap and stop."
    ),
    "incomplete-shell": (
        "{subsystem} shipped without wiring: {root_cause_short}. Verify "
        "every emitted artifact is reachable from a real call path."
    ),
    "integration": (
        "Cross-module call in {subsystem} broke: {root_cause_short}. "
        "Run an integration smoke test that exercises the boundary."
    ),
    "spec-violation": (
        "{subsystem} drifted from spec: {root_cause_short}. Re-read the "
        "spec section before editing the implementation."
    ),
    "tooling": (
        "Tool failure in {subsystem}: {root_cause_short}. Confirm the "
        "tool actually ran and returned the expected output before "
        "trusting its absence-of-error."
    ),
    "env": (
        "Environment mismatch on {subsystem}: {root_cause_short}. Probe "
        "the env (uname/whoami/version) before assuming the runtime."
    ),
}


# ---------------------------------------------------------------------------
# Logging / atomic write primitives
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _atomic_write(path: Path, text: str) -> None:
    """tempfile + os.replace, same parent dir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _atomic_append(path: Path, text: str) -> None:
    """Read-modify-write atomic append. Prevents the 2026-05-23 apex
    `cat >>` corruption pattern (heredoc-via-shell lost the Testing
    Gate Axis from the loose mirror)."""
    if path.is_file():
        body = path.read_text(encoding="utf-8")
        if not body.endswith("\n"):
            body += "\n"
    else:
        body = ""
    _atomic_write(path, body + text)


# ---------------------------------------------------------------------------
# Pattern signature (M9 root-cause normalization)
# ---------------------------------------------------------------------------

_WS_RX = re.compile(r"\s+")
_NONWORD_RX = re.compile(r"[^\w\s]+", re.UNICODE)


def _normalize_root_cause(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace. Stable across
    minor wording variations so the same underlying mechanism yields
    the same signature."""
    t = text.lower()
    t = _NONWORD_RX.sub(" ", t)
    t = _WS_RX.sub(" ", t).strip()
    return t


def pattern_signature(root_cause: str) -> str:
    norm = _normalize_root_cause(root_cause)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def event_id(root_cause: str) -> str:
    return f"ceps_{pattern_signature(root_cause)}"


def _short(text: str, n: int = 80) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "..."


# ---------------------------------------------------------------------------
# FTS5 pattern DB (M10 substrate)
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS ceps_patterns_fts USING fts5(
    id UNINDEXED,
    ts UNINDEXED,
    category,
    subsystem,
    root_cause,
    prevention_rule,
    affected_modules,
    confidence UNINDEXED,
    tokenize='porter unicode61'
);
"""


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(_SCHEMA_SQL)
    return conn


def _db_insert(conn: sqlite3.Connection, event: dict) -> None:
    conn.execute(
        "INSERT INTO ceps_patterns_fts(id, ts, category, subsystem, "
        "root_cause, prevention_rule, affected_modules, confidence) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event["id"], event["ts"], event["category"], event["subsystem"],
            event["root_cause"], event["prevention_rule"],
            " ".join(event.get("affected_modules") or []),
            event.get("confidence", "high"),
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# M9: record_error (extractor + classifier + distributor entry point)
# ---------------------------------------------------------------------------

def record_error(
    category: str,
    subsystem: str,
    root_cause: str,
    affected_modules: Optional[list] = None,
    evidence_path: Optional[str] = None,
    confidence: str = "high",
) -> Optional[dict]:
    """Validate, classify, compute signature, persist, and distribute.

    Returns the event dict on success, None on validation failure or any
    internal exception (fail-open per Ley 24).
    """
    try:
        if category not in VALID_CATEGORIES:
            _log(f"record_error: invalid category={category}")
            return None
        if confidence not in VALID_CONFIDENCE:
            _log(f"record_error: invalid confidence={confidence}")
            return None
        if not root_cause or len(root_cause) > 600:
            _log("record_error: root_cause empty or too long")
            return None
        sig = pattern_signature(root_cause)
        rule = RULE_TEMPLATES[category].format(
            subsystem=subsystem or "unknown",
            root_cause_short=_short(root_cause, 60),
        )
        event = {
            "id": f"ceps_{sig}",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "category": category,
            "subsystem": subsystem or "unknown",
            "root_cause": root_cause.strip(),
            "pattern_signature": sig,
            "prevention_rule": rule,
            "affected_modules": affected_modules or [],
            "evidence_path": evidence_path,
            "confidence": confidence,
            "auto_test_eligible": category in AUTO_TEST_CATEGORIES,
        }

        # Append to events.jsonl (atomic line append)
        EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_PATH, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Insert into FTS5
        conn = _db()
        try:
            _db_insert(conn, event)
        finally:
            conn.close()

        # M11: distribute
        distribute(event)
        return event
    except Exception as exc:
        _log(f"record_error ERROR {type(exc).__name__}: {exc}")
        return None


# ---------------------------------------------------------------------------
# M11: distribute
# ---------------------------------------------------------------------------

def distribute(event: dict) -> dict:
    """Atomic-append the event to the 3 destinations.

    Returns {"session_lessons": bool, "ukdl": bool, "patterns_db": bool}.
    Each flag = "this destination is now updated with the event".
    """
    result = {"session_lessons": False, "ukdl": False, "patterns_db": True}
    try:
        sl_entry = (
            f"\n### CEPS event {event['id']} -- {event['category']} "
            f"({event['ts']})\n\n"
            f"- subsystem: `{event['subsystem']}`\n"
            f"- root cause: {event['root_cause']}\n"
            f"- prevention rule: {event['prevention_rule']}\n"
            f"- pattern signature: `{event['pattern_signature']}`\n"
            f"- confidence: {event['confidence']}\n"
            f"- auto-test eligible: {event['auto_test_eligible']}\n"
        )
        _atomic_append(LESSONS_PATH, sl_entry)
        result["session_lessons"] = True
    except Exception as exc:
        _log(f"distribute session_lessons ERROR {type(exc).__name__}: {exc}")

    try:
        ukdl_entry = (
            f"\n- [{event['category']}/{event['subsystem']}] "
            f"`{event['id']}` -- {event['prevention_rule']}\n"
        )
        _atomic_append(UKDL_PATH, ukdl_entry)
        result["ukdl"] = True
    except Exception as exc:
        _log(f"distribute ukdl ERROR {type(exc).__name__}: {exc}")

    return result


# ---------------------------------------------------------------------------
# M10: forward propagation (FTS5 query)
# ---------------------------------------------------------------------------

_FTS_PUNCT_RX = re.compile(r"[^\w\s]+", re.UNICODE)


def _fts_query_from_prompt(prompt: str, subsystem_hints=None) -> str:
    """Build a safe FTS5 MATCH expression from the prompt + hints.

    FTS5 MATCH has its own syntax. We extract the top content words
    (>=4 chars, alphanumeric) from the prompt, OR them together, and
    optionally OR in subsystem hints. Empty -> return None upstream.
    """
    base = _FTS_PUNCT_RX.sub(" ", prompt.lower()).split()
    words = [w for w in base if len(w) >= 4][:12]
    if subsystem_hints:
        words = list(subsystem_hints) + words
    if not words:
        return ""
    # Quote each word to avoid FTS5 reserved tokens like AND/OR/NOT.
    quoted = [f'"{w}"' for w in words]
    return " OR ".join(quoted)


def propagate(prompt: str, subsystem_hints=None, top_k: int = 3) -> list:
    """Return up to top_k `[ceps-pattern] ...` lines for the prompt.

    Fail-open: any internal error -> empty list.
    """
    try:
        if not DB_PATH.exists():
            return []
        q = _fts_query_from_prompt(prompt, subsystem_hints)
        if not q:
            return []
        conn = _db()
        try:
            rows = conn.execute(
                "SELECT category, subsystem, prevention_rule, "
                "pattern_signature_short FROM ("
                "  SELECT category, subsystem, prevention_rule, "
                "  substr(id, 6, 8) AS pattern_signature_short, "
                "  rank FROM ceps_patterns_fts "
                "  WHERE ceps_patterns_fts MATCH ? "
                "  ORDER BY rank LIMIT ?"
                ")",
                (q, top_k),
            ).fetchall()
        finally:
            conn.close()
        lines = []
        for cat, sub, rule, sig in rows:
            lines.append(
                f"[ceps-pattern] {rule} (cat={cat}, sub={sub}, sig={sig})"
            )
        return lines
    except Exception as exc:
        _log(f"propagate ERROR {type(exc).__name__}: {exc}")
        return []


# ---------------------------------------------------------------------------
# M8: triggers
# ---------------------------------------------------------------------------

def from_slash_command(argv: list) -> Optional[dict]:
    """Slash command entry point. Usage:
    /ceps-record-error <category> <subsystem> <root_cause...>
    """
    if len(argv) < 3:
        _log("from_slash_command: too few args")
        return None
    category, subsystem = argv[0], argv[1]
    root_cause = " ".join(argv[2:])
    return record_error(category, subsystem, root_cause,
                        confidence="high")


_VERIFY_FAIL_RX = re.compile(
    r"\[FAIL\]\s+(\S+)\s+rc=\d+\s+[\d.]+s\s+(.+?)(?:\n|$)")


def from_verify_fail(verify_stdout: str) -> list:
    """Parse `tools/verify_spp.py` STRICT-FAIL rows -> high-confidence
    records. Returns the list of created events."""
    out = []
    for m in _VERIFY_FAIL_RX.finditer(verify_stdout):
        row, detail = m.group(1).strip(), m.group(2).strip()
        # Best-guess category by row name. Conservative: default to
        # `tooling` so the record exists even for unrecognized rows.
        category = "tooling"
        if "drift" in row or "mirror" in row:
            category = "drift"
        elif "spec" in row or "schema" in row:
            category = "spec-violation"
        ev = record_error(
            category=category,
            subsystem=f"verify-spp/{row}",
            root_cause=f"verify_spp row `{row}` FAIL: {detail}",
            evidence_path="tools/verify_spp.py",
            confidence="high",
        )
        if ev:
            out.append(ev)
    return out


_CORRECTION_RX = re.compile(
    r"\b(?:no,?\s+actually|that'?s\s+wrong|wait,?\s+(?:no|stop)|"
    r"revert|undo|nope|incorrect|bad\s+take|que\s+no|"
    r"no\s+es\s+(?:asi|así)|stop\s+(?:doing|that))\b", re.I)


def from_stop_hook(last_turns: list) -> list:
    """Scan the last few user turns for correction signals. Emits
    LOW-confidence drafts to vault/ceps/drafts/ instead of persisting.
    Drafts are promoted to events via `/ceps-confirm <draft-id>`.
    """
    drafts = []
    try:
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        for turn in last_turns[-5:]:
            text = turn if isinstance(turn, str) else turn.get("text", "")
            if _CORRECTION_RX.search(text):
                draft_id = hashlib.sha1(
                    (text + str(time.time())).encode("utf-8")
                ).hexdigest()[:12]
                draft = {
                    "draft_id": draft_id,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "snippet": _short(text, 200),
                    "confidence": "low",
                    "needs_confirmation": True,
                }
                path = DRAFTS_DIR / f"{draft_id}.json"
                _atomic_write(path, json.dumps(draft, indent=2,
                                               ensure_ascii=False) + "\n")
                drafts.append(draft)
    except Exception as exc:
        _log(f"from_stop_hook ERROR {type(exc).__name__}: {exc}")
    return drafts


# ---------------------------------------------------------------------------
# CLI entry point (for slash-command + ad-hoc invocation)
# ---------------------------------------------------------------------------

def _main(argv: list) -> int:
    if not argv:
        print("usage: ceps.py record <category> <subsystem> <root_cause...>",
              file=sys.stderr)
        print("       ceps.py propagate <prompt>", file=sys.stderr)
        print("       ceps.py from-verify <path-to-verify-stdout>",
              file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "record":
        ev = from_slash_command(rest)
        if ev:
            print(json.dumps(ev, indent=2, ensure_ascii=False))
            return 0
        print("record failed (see ~/.claude/logs/ceps.log)",
              file=sys.stderr)
        return 1
    if cmd == "propagate":
        lines = propagate(" ".join(rest))
        for l in lines:
            print(l)
        return 0
    if cmd == "from-verify":
        if not rest:
            print("from-verify requires a file path", file=sys.stderr)
            return 2
        stdout = Path(rest[0]).read_text(encoding="utf-8")
        evs = from_verify_fail(stdout)
        print(f"recorded {len(evs)} events from verify_spp stdout")
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
