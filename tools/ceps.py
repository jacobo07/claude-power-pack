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
# D1: durable rejection ledger. A fail-open path that leaves no trace is a
# silent outage -- 60 `invalid scope=session` rejections sat in LOG for 80
# days because no gate read it. capture_liveness.py reads this file.
REJECTIONS_PATH = PP_ROOT / "vault" / "ceps" / "rejections.jsonl"

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


def _record_rejection(reason: str, **fields) -> None:
    """Append a rejected record_error() call to the rejection ledger.

    Fail-open must not mean fail-silent. Every call that reaches
    record_error() and does not produce an event lands here, so
    capture_liveness.py can prove the divergence between what the
    producers fired and what the corpus stored.

    `origin` separates a production capture loss from a test suite
    deliberately feeding invalid input. Without it the liveness gate
    counts test_ceps_edge_cases' intentional rejections as real loss and
    fails on a healthy repo -- a gate that cries wolf stops being read.
    """
    _log(f"record_error: {reason}")
    try:
        REJECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "reason": reason,
            "origin": os.environ.get("CEPS_ORIGIN", "direct"),
        }
        entry.update({k: v for k, v in fields.items() if v is not None})
        with open(REJECTIONS_PATH, "a", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # The ledger is a diagnostic; it must never break the user path.
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

# D3: variable tokens masked BEFORE punctuation is stripped. Two sightings
# of one mechanism differ only in path, line number, pid or timestamp; if
# those survive into the hash every occurrence gets a unique signature,
# `occurrences` never exceeds 1, and recurrence-gated promotion (>=2
# projects) and the cascade map (>=2 co-occurrences) can never fire.
_MASKS = (
    (re.compile(r"\d{4}-\d{2}-\d{2}[t ]\d{2}:\d{2}:\d{2}\S*"), " TS "),
    (re.compile(r"[a-z]:[\\/][^\s'\"]+", re.IGNORECASE), " PATH "),
    (re.compile(r"(?<![\w.])/(?:[\w.\-]+/)+[\w.\-]+"), " PATH "),
    (re.compile(r"\bline\s+\d+", re.IGNORECASE), " line N "),
    (re.compile(r"0x[0-9a-f]+", re.IGNORECASE), " HEX "),
    (re.compile(r"\b(?:pid|port|exit code)\s*[:=]?\s*\d+", re.IGNORECASE),
     " NUM "),
    (re.compile(r"\b\d{3,}\b"), " NUM "),
)


def _normalize_root_cause(text: str) -> str:
    """Mask variable tokens, lowercase, strip punctuation, collapse
    whitespace. Stable across minor wording variations AND across the
    paths / line numbers / ids that differ between two sightings of the
    same underlying mechanism, so both yield one signature."""
    t = text.lower()
    for rx, repl in _MASKS:
        t = rx.sub(repl, t)
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

def compute_confidence(
    occurrences: int,
    resolution_success: bool = False,
) -> float:
    """ECC instinct-model confidence score on the 0.3-0.9 scale.

    Source: ECC continuous-learning-v2 / Affaan Mustafa MIT,
    adapted from JS/shell to Python. Reflects how much weight a
    pattern carries: low (0.3) = first sighting, medium (0.5-0.7)
    = recurring, high (0.8-0.9) = recurring + resolution proven.

    Args:
        occurrences: count of times this error pattern has been
            observed. >=1.
        resolution_success: whether the fix has been verified to
            prevent recurrence.
    """
    score = 0.3
    if occurrences >= 2:
        score += 0.2
    if occurrences >= 5:
        score += 0.2
    if resolution_success:
        score += 0.2
    return round(min(0.9, max(0.3, score)), 2)


def promote_to_global(
    error_pattern: str,
    project_ids: list[str],
) -> bool:
    """Returns True iff this error pattern has been seen across
    >=2 distinct projects, qualifying it for global scope.

    Source: ECC continuous-learning-v2 / Affaan Mustafa MIT,
    adapted from JS to Python.
    """
    return len(set(project_ids)) >= 2


def _project_id_hash(project_root: Optional[str] = None) -> str:
    """Stable short hash of the project root path. Empty if no
    project root can be determined.
    """
    if project_root is None:
        project_root = os.getcwd()
    if not project_root:
        return ""
    return hashlib.sha256(
        project_root.encode("utf-8", errors="replace")
    ).hexdigest()[:12]


# Generation of the semantic admission rules. Bump when a rule changes so
# the history audit can tell "judged by the current rules" from "judged by
# an older generation and due for re-judgement".
ADMISSION_REV = 1

_VACUOUS_CLAIM = re.compile(
    r"""^\W*(?:
          (?<!\d)0+\s*(?:failed|failures?|errors?|warnings?)
        | no\s+(?:failed|failures?|errors?|warnings?)
        | (?:failures?|errors?)\s*[:=]\s*0+
        )\W*$""",
    re.IGNORECASE | re.VERBOSE,
)


def is_vacuous_failure_claim(root_cause: str) -> bool:
    """True when the WHOLE root_cause asserts that nothing failed.

    Shape validation cannot tell a failure from a success: `record_error`
    checked that `category` was spelled correctly and that `root_cause`
    was non-empty, so a producer that matched `\\d+ failed` against a
    pytest summary filed "0 failed" as a regression, and a consumer that
    keyed on category never noticed (2026-08-25).

    Deliberately anchored to the entire string. "reported 0 failed but
    exit code was 1" is a real finding that happens to contain a zero, and
    a gate that swallowed it would trade one silent corruption for
    another. Only a claim carrying no evidence beyond the zero is refused.
    """
    return bool(_VACUOUS_CLAIM.match((root_cause or "").strip()))


def record_error(
    category: str,
    subsystem: str,
    root_cause: str,
    affected_modules: Optional[list] = None,
    evidence_path: Optional[str] = None,
    confidence: str = "high",
    confidence_score: Optional[float] = None,
    scope: str = "project",
    project_id: Optional[str] = None,
) -> Optional[dict]:
    """Validate, classify, compute signature, persist, and distribute.

    Returns the event dict on success, None on validation failure or any
    internal exception (fail-open per Ley 24).

    ECC absorption (2026-05-27): added `confidence_score` (0.3-0.9
    numeric, ECC instinct-model adapted from continuous-learning-v2),
    `scope` ("project" | "global"), and `project_id` (hash of project
    root). Existing string `confidence` ("low" | "high") remains
    backward-compatible.
    """
    try:
        ctx = {"category": category, "subsystem": subsystem}
        if category not in VALID_CATEGORIES:
            _record_rejection(f"invalid category={category}", **ctx)
            return None
        if confidence not in VALID_CONFIDENCE:
            _record_rejection(f"invalid confidence={confidence}", **ctx)
            return None
        if scope not in ("project", "global"):
            _record_rejection(f"invalid scope={scope}", **ctx)
            return None
        if confidence_score is not None and not (
            0.0 <= confidence_score <= 1.0
        ):
            _record_rejection("confidence_score out of range", **ctx)
            return None
        if not root_cause or len(root_cause) > 600:
            _record_rejection("root_cause empty or too long", **ctx)
            return None
        if is_vacuous_failure_claim(root_cause):
            _record_rejection(
                f"vacuous failure claim: {_short(root_cause, 60)}", **ctx)
            return None
        sig = pattern_signature(root_cause)
        rule = RULE_TEMPLATES[category].format(
            subsystem=subsystem or "unknown",
            root_cause_short=_short(root_cause, 60),
        )
        # M1/NIT1: schema declares max_chars=300 on prevention_rule;
        # enforce on the rendered output (templates may stretch with
        # long subsystem identifiers).
        if len(rule) > 300:
            rule = rule[:297] + "..."
        event = {
            "id": f"ceps_{sig}",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "category": category,
            "subsystem": subsystem or "unknown",
            "root_cause": root_cause.strip(),
            "pattern_signature": sig,
            "prevention_rule": rule,
            # Judged at admission, so no event is ever born unjudged and the
            # history audit has only legacy rows to catch up on. The backfill
            # re-judges from original fields and overrules this if a later
            # rule generation disagrees.
            "admission_status": "valid",
            "admission_note": "",
            "admission_rev": ADMISSION_REV,
            "affected_modules": affected_modules or [],
            "evidence_path": evidence_path,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "scope": scope,
            "project_id": project_id if project_id is not None
                          else _project_id_hash(),
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
        _record_rejection(
            f"internal {type(exc).__name__}: {exc}",
            category=category, subsystem=subsystem,
        )
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
            # M2/NIT2: flattened to a single SELECT; substr alias is
            # bound inline so no outer wrapper is needed.
            rows = conn.execute(
                "SELECT category, subsystem, prevention_rule, "
                "substr(id, 6, 8) AS sig "
                "FROM ceps_patterns_fts "
                "WHERE ceps_patterns_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
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


def _existing_sigs() -> set:
    """M3/NIT3: scan events.jsonl for already-recorded signatures so
    `from_verify_fail` can skip duplicates on re-invocation. Fail-open:
    any read error -> empty set (re-record, never block)."""
    if not EVENTS_PATH.is_file():
        return set()
    sigs = set()
    try:
        for line in EVENTS_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                sigs.add(json.loads(line).get("pattern_signature", ""))
            except json.JSONDecodeError:
                continue
    except Exception as exc:
        _log(f"_existing_sigs ERROR {type(exc).__name__}: {exc}")
    return sigs


def from_verify_fail(verify_stdout: str) -> list:
    """Parse `tools/verify_spp.py` STRICT-FAIL rows -> high-confidence
    records. M3/NIT3: idempotent under re-invocation -- signatures
    already present in events.jsonl are skipped so the same stdout
    parsed twice produces zero duplicate rows."""
    existing = _existing_sigs()
    out = []
    for m in _VERIFY_FAIL_RX.finditer(verify_stdout):
        row, detail = m.group(1).strip(), m.group(2).strip()
        root_cause = f"verify_spp row `{row}` FAIL: {detail}"
        sig = pattern_signature(root_cause)
        if sig in existing:
            continue
        existing.add(sig)
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
            root_cause=root_cause,
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

# --- Cross-project baseline (spec vault/specs/cross-project-baseline.md) ----
#
# promote_to_global() above has been a pure predicate since it landed: it
# returns a bool and its only caller in the tree is tools/test_uqf.py. So no
# pattern has EVER been promoted, and nothing in any other project could
# surface what one project learned. What follows is the missing WRITER.
#
# It is deliberately stricter than the bare >=2-projects predicate. Measured on
# the live corpus 2026-08-31: 8 signatures clear >=2 projects, but only 4 are
# real. `FAILED` (a bare word scraped from output), `Error ? err.message :
# String(err` (JavaScript source) and `Error exacto: [mensaje completo` (a
# Spanish doc template) all clear it -- and two of those carry
# admission_status="valid", so the admission layer alone does not stop them.
# Promoting those would inject boilerplate about `bash:cd` into every project
# forever, which is worse than the silence it replaces.
PROMOTED_PATH = PP_ROOT / "vault" / "ceps" / "promoted.jsonl"

# POSITIVE CONTROL, not a growing blacklist (PR-POSITIVE-CONTROL-BEATS-A-
# GROWING-BLACKLIST-001): a root_cause is portable only if it IS a recognisable
# error identity. The Error|Exception branch requires a COMPOUND identifier --
# `AssertionError` matches, the bare prose word `Error` does not, which is the
# single change that stopped the doc-template and source-code fragments.
_PORTABLE_IDENTITY = re.compile(r"""(
      \b[A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)\b
    | Traceback\ \(most\ recent\ call\ last\)
    | \bPermission\ denied\b
    | \bNo\ such\ file\ or\ directory\b
    | \bcommand\ not\ found\b
    | \[Tool\ result\ missing\ due\ to\ internal\ error\]
    | \b(?:ENOENT|EACCES|EPERM|ECONNREFUSED|ETIMEDOUT|EADDRINUSE)\b
    | \bsegmentation\ fault\b
    | \bexit\ (?:code|status)\ \d+
    | \bHTTP\ [45]\d\d\b
    | \btimed?\ ?out\b
)""", re.IGNORECASE | re.VERBOSE)


def is_portable_identity(root_cause: str) -> bool:
    """True when a root_cause names an error, rather than quoting something."""
    text = str(root_cause or "")
    if is_vacuous_failure_claim(text):
        return False
    return bool(_PORTABLE_IDENTITY.search(text))


def _admitted_events(events: list) -> list:
    """Events fit to argue portability: semantically admitted AND naming an
    error. Both are required -- 51 of 101 live events are identity_suspect
    (the subsystem is a navigation prefix like `bash:cd`, not the failing
    tool), and separately, some `valid` events quote source code."""
    return [e for e in events
            if e.get("admission_status") == "valid"
            and is_portable_identity(e.get("root_cause"))]


def compute_promotions(events: list) -> list:
    """Group by pattern_signature and return the promotable records.

    Portability is counted over ADMITTED events only. A pattern that reaches
    seven projects on suspect evidence has not been shown to travel -- it has
    been shown to be logged a lot (recurrence is not portability).
    """
    groups: dict = {}
    for e in events:
        sig = e.get("pattern_signature")
        if sig:
            groups.setdefault(sig, []).append(e)

    out = []
    for sig, evs in sorted(groups.items()):
        admitted = _admitted_events(evs)
        project_ids = [e.get("project_id", "") for e in admitted
                       if e.get("project_id")]
        if not promote_to_global(sig, project_ids):
            continue
        newest = max(admitted, key=lambda e: str(e.get("ts", "")))
        out.append({
            "pattern_signature": sig,
            "root_cause": newest.get("root_cause"),
            "prevention_rule": newest.get("prevention_rule"),
            "category": newest.get("category"),
            "subsystems": sorted({e.get("subsystem") for e in admitted
                                  if e.get("subsystem")}),
            "project_ids": sorted(set(project_ids)),
            "project_count": len(set(project_ids)),
            "admitted": len(admitted),
            "observed": len(evs),
            "promoted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    return out


def promote_patterns(events_path: Optional[Path] = None,
                     out_path: Optional[Path] = None) -> dict:
    """Write the promotable set to the global baseline. Idempotent by
    signature: a re-run refreshes a record in place rather than appending a
    duplicate, so the file stays a SET and the injector cannot show the same
    rule twice."""
    src = Path(events_path) if events_path else EVENTS_PATH
    dst = Path(out_path) if out_path else PROMOTED_PATH

    events = []
    try:
        for line in src.read_text(encoding="utf-8",
                                  errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue  # one bad line must not blind the whole pass
    except OSError as exc:
        return {"ok": False, "error": f"unreadable events: {exc}",
                "promoted": 0}

    records = compute_promotions(events)
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(json.dumps(r, ensure_ascii=False) + "\n"
                       for r in records)
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, dst)
    except OSError as exc:
        return {"ok": False, "error": f"unwritable baseline: {exc}",
                "promoted": 0}

    return {"ok": True, "promoted": len(records), "path": str(dst),
            "signatures": [r["pattern_signature"] for r in records]}


# Resolved-draft directories are derived from DRAFTS_DIR at CALL time, never
# bound at import. The suites here redirect ceps.DRAFTS_DIR into a tmpdir to
# stay hermetic; a module-level constant would keep pointing at the real vault
# and a "hermetic" test would quietly write into it.
def _confirmed_dir() -> Path:
    return DRAFTS_DIR / "confirmed"


def _dismissed_dir() -> Path:
    return DRAFTS_DIR / "dismissed"


def list_drafts() -> list:
    """Correction drafts awaiting an Owner verdict.

    from_stop_hook() writes LOW-confidence drafts rather than events, because
    an Owner saying "no, that's wrong" is a signal about the agent, not yet a
    diagnosed defect. The draft is deliberately not an event until a human
    says what it was. This is the read side of that pair; without it the
    drafts were unreachable and the producer had nothing to write to.
    """
    try:
        if not DRAFTS_DIR.is_dir():
            return []
    except OSError:
        return []
    out = []
    for path in sorted(DRAFTS_DIR.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ValueError):
            continue  # a corrupt draft must not blind the reader to the rest
    return out


def _move_draft(draft_id: str, dest_dir: Path, **stamp) -> Optional[dict]:
    """Move one draft out of the pending set, stamping how it was resolved."""
    src = DRAFTS_DIR / f"{draft_id}.json"
    if not src.exists():
        return None
    try:
        draft = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    draft.update(stamp)
    draft["needs_confirmation"] = False
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(dest_dir / f"{draft_id}.json",
                      json.dumps(draft, indent=2, ensure_ascii=False) + "\n")
        src.unlink()
    except OSError as exc:
        _log(f"_move_draft ERROR {type(exc).__name__}: {exc}")
        return None
    return draft


def confirm_draft(draft_id: str, category: str = "spec-violation",
                  subsystem: str = "owner-correction") -> Optional[dict]:
    """Promote a correction draft into a real CEPS event.

    The Owner supplies the category, because only they know what the
    correction was ABOUT; the draft only knows that one happened.
    """
    src = DRAFTS_DIR / f"{draft_id}.json"
    if not src.exists():
        return None
    try:
        draft = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    event = record_error(
        category=category,
        subsystem=subsystem,
        root_cause=str(draft.get("snippet", ""))[:600],
        confidence="high",           # a human confirmed it; that IS the evidence
        evidence_path=str(src),
    )
    if not event:
        return None                  # rejection already went to the ledger
    # The event's identity field is `id` (see record_error's return). Reading a
    # plausible-but-absent `event_id` stamps None and silently loses the link
    # from the draft to the event it became -- caught by the gate below only
    # because the gate asserted on the identity, not on truthiness.
    _move_draft(draft_id, _confirmed_dir(), confirmed_event_id=event.get("id"))
    return event


def dismiss_draft(draft_id: str, reason: str = "") -> Optional[dict]:
    """Retire a draft the Owner judges to be noise.

    A pending set with no terminal transition is the trap this estate already
    sealed once: a status field nobody can move is decoration, and the queue
    grows forever while reading as healthy. Dismissal is that transition.
    """
    return _move_draft(draft_id, _dismissed_dir(), dismissed_reason=str(reason))


def _main(argv: list) -> int:
    if not argv:
        print("usage: ceps.py record <category> <subsystem> <root_cause...>",
              file=sys.stderr)
        print("       ceps.py propagate <prompt>", file=sys.stderr)
        print("       ceps.py from-verify <path-to-verify-stdout>",
              file=sys.stderr)
        print("       ceps.py promote", file=sys.stderr)
        print("       ceps.py drafts", file=sys.stderr)
        print("       ceps.py confirm <draft-id> [category] [subsystem]",
              file=sys.stderr)
        print("       ceps.py dismiss <draft-id> [reason...]", file=sys.stderr)
        return 2
    if argv[0] == "drafts":
        pending = list_drafts()
        print(json.dumps({"pending": pending, "count": len(pending)},
                         indent=2, ensure_ascii=False))
        return 0
    if argv[0] == "confirm":
        if len(argv) < 2:
            print("confirm requires a draft-id", file=sys.stderr)
            return 2
        ev = confirm_draft(*argv[1:4])
        if not ev:
            print(f"confirm failed for {argv[1]} "
                  f"(unknown draft, or rejected -- see vault/ceps/rejections.jsonl)",
                  file=sys.stderr)
            return 1
        print(json.dumps(ev, indent=2, ensure_ascii=False))
        return 0
    if argv[0] == "dismiss":
        if len(argv) < 2:
            print("dismiss requires a draft-id", file=sys.stderr)
            return 2
        got = dismiss_draft(argv[1], " ".join(argv[2:]))
        if not got:
            print(f"dismiss failed for {argv[1]} (unknown draft)",
                  file=sys.stderr)
            return 1
        print(json.dumps(got, indent=2, ensure_ascii=False))
        return 0
    if argv[0] == "promote":
        res = promote_patterns()
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res.get("ok") else 1
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
