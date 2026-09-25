"""The `check` field of a baseline entry, as a grammar with honest outcomes.

Spec 2026-09-24 §3.2 defines `check` as an optional machine check (file, glob,
regex). Measured 2026-09-25: of the 60 entries in the four B0s, 31 carry a
check and every one of them is prose -- shell fragments with placeholders,
test names, descriptions. A ratchet over prose compares text, and a done-gate
over prose has nothing to run, so "the check passed" could only ever mean that
nobody ran anything.

Grammar (`<kind>:<argument>`, kind is a bare lowercase word):

    file:<relpath>               the file exists under the repo root
    glob:<relpattern>            at least one path matches
    regex:<relpath>::<pattern>   the pattern occurs in the file
    registry:<verifier-id>       a verifier with that id is registered
    test:<relpath>               the test file exists

Two families of answer, deliberately never merged:

  * STATIC kinds (file, glob, regex) are evaluated here, read-only, confined to
    the repo root, and are the ONLY kinds that can return PASS.
  * DELEGATED kinds (registry, test) resolve their target and return
    DELEGATED. Their verdict belongs to the repo's own verifier
    (`verify_change.py`, the test runner); this module never executes code,
    so it never claims a result it did not observe.

Everything else is UNRUNNABLE_PROSE, and an empty field is EMPTY. The
instrument's own failures -- a malformed pattern, an unreadable subject or
registry, a path leaving the root, an entry whose shape crashes the
evaluator -- each have their own outcome, because a verifier that could not
judge and a subject that failed are different evidence.
"""
from __future__ import annotations

import glob as _glob
import json
import os
import re
from dataclasses import dataclass

PASS = "PASS"
FAIL = "FAIL"
DELEGATED = "DELEGATED"
UNRUNNABLE_PROSE = "UNRUNNABLE_PROSE"
EMPTY = "EMPTY"
MALFORMED = "MALFORMED"
UNREADABLE = "UNREADABLE"
REFUSED_PATH = "REFUSED_PATH"
ERROR = "ERROR"

OUTCOMES = (PASS, FAIL, DELEGATED, UNRUNNABLE_PROSE, EMPTY, MALFORMED,
            UNREADABLE, REFUSED_PATH, ERROR)
STATIC_KINDS = ("file", "glob", "regex")
DELEGATED_KINDS = ("registry", "test")
_KIND = re.compile(r"^([a-z]+):(.*)$", re.S)


@dataclass(frozen=True)
class CheckResult:
    entry_id: str
    check: str
    kind: str
    outcome: str
    detail: str

    def as_dict(self) -> dict:
        return {"entry_id": self.entry_id, "check": self.check, "kind": self.kind,
                "outcome": self.outcome, "detail": self.detail}


def parse(check: str) -> tuple:
    """(kind, argument). Unknown or absent kind -> ("prose", check)."""
    text = (check or "").strip()
    if not text:
        return ("empty", "")
    m = _KIND.match(text)
    if not m or m.group(1) not in STATIC_KINDS + DELEGATED_KINDS:
        return ("prose", text)
    return (m.group(1), m.group(2).strip())


def _inside(root: str, rel: str) -> str | None:
    """Absolute path of `rel` under `root`, or None if it escapes or is absolute."""
    if not rel or os.path.isabs(rel) or re.match(r"^[A-Za-z]:", rel) \
            or rel.startswith(("/", "\\")):
        return None
    base = os.path.realpath(root)
    full = os.path.realpath(os.path.join(base, rel))
    if full != base and not full.startswith(base + os.sep):
        return None
    return full


def _registry_ids(registry: str | None) -> set | None:
    if not registry or not os.path.isfile(registry):
        return None
    try:
        with open(registry, "r", encoding="utf-8-sig") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    rows = doc.get("verifiers") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return None
    return {r.get("id") for r in rows if isinstance(r, dict) and r.get("id")}


def _evaluate(kind: str, arg: str, root: str, registry: str | None) -> tuple:
    if kind == "empty":
        return (EMPTY, "no check declared")
    if kind == "prose":
        return (UNRUNNABLE_PROSE, "not in the check grammar; nothing can run it")
    if kind == "registry":
        ids = _registry_ids(registry)
        if ids is None:
            return (UNREADABLE, "no readable verification registry supplied")
        if arg in ids:
            return (DELEGATED, "registered verifier %s; its verdict is the repo's" % arg)
        return (FAIL, "no verifier with id %s is registered" % arg)
    if kind == "regex":
        rel, sep, pattern = arg.partition("::")
        if not sep or not pattern:
            return (MALFORMED, "regex needs <relpath>::<pattern>")
        try:
            rx = re.compile(pattern)
        except re.error as exc:
            return (MALFORMED, "pattern does not compile: %s" % exc)
        full = _inside(root, rel.strip())
        if full is None:
            return (REFUSED_PATH, "path leaves the repo root: %s" % rel)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            return (UNREADABLE, "subject unreadable: %s" % type(exc).__name__)
        return (PASS, "pattern found") if rx.search(text) else (FAIL, "pattern absent")
    if kind == "glob":
        if _inside(root, arg.replace("*", "x").replace("?", "x")) is None:
            return (REFUSED_PATH, "pattern leaves the repo root: %s" % arg)
        base = os.path.realpath(root)
        # The pattern check above cannot see where a match RESOLVES: a symlink or
        # junction inside the root can point outside it. Keep only hits whose
        # real path is still under the root (code review 2026-09-25, LOW).
        hits = [h for h in _glob.glob(os.path.join(base, arg), recursive=True)
                if os.path.realpath(h) == base
                or os.path.realpath(h).startswith(base + os.sep)]
        return (PASS, "%d match(es)" % len(hits)) if hits else (FAIL, "no match")
    # file / test
    full = _inside(root, arg)
    if full is None:
        return (REFUSED_PATH, "path leaves the repo root: %s" % arg)
    exists = os.path.isfile(full)
    if kind == "test":
        return ((DELEGATED, "test exists; run by the repo, not here") if exists
                else (FAIL, "named test does not exist"))
    return (PASS, "exists") if exists else (FAIL, "does not exist")


def evaluate(entry: dict, root: str, registry: str | None = None) -> CheckResult:
    """One entry's check. Never raises: a crash is the outcome ERROR."""
    ident, check, kind = "?", "", "?"
    try:
        ident = str(entry.get("id", "?"))
        check = str(entry.get("check") or "")
        kind, arg = parse(check)
        outcome, detail = _evaluate(kind, arg, root, registry)
        return CheckResult(ident, check, kind, outcome, detail)
    except Exception as exc:  # noqa: BLE001 -- surfaced as ERROR, never swallowed
        return CheckResult(ident, check, kind, ERROR,
                           "evaluator failed: %s: %s" % (type(exc).__name__, exc))


def run_checks(entries: list, root: str, registry: str | None = None) -> list:
    """Every entry judged independently; one hostile entry cannot end the run."""
    return [evaluate(e, root, registry) for e in entries]


def summarize(results: list) -> dict:
    """Counts per outcome. `evaluated` = entries a STATIC kind actually judged."""
    out = {k: 0 for k in OUTCOMES}
    for r in results:
        out[r.outcome] = out.get(r.outcome, 0) + 1
    out["population"] = len(results)
    out["evaluated"] = out[PASS] + out[FAIL]
    return out
