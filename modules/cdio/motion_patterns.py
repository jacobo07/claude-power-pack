"""Contract-aware motion pattern resolver (CDIO-07 x visual-patterns).

The motion knowledge in `vault/knowledge_base/visual-patterns/` was reachable only
by keyword search after an opt-in refresh (`tools/design_index.py --search`), and
that search is blind to the project's declared experience contract. So the same
query returned an ambient grain texture to a payments console and to a landing
hero. A pattern corpus that cannot tell those apart is advice, not intelligence.

This module is the decision-time consumer. Given the CDIO-07 `experience:`
contract (already parsed by `tools/design_gate.py`) and the path of the surface
being written, it answers one question: which motion patterns may this surface
use, and why -- or why none.

Four answers, kept apart on purpose (CDIO-07 sec.3):

  unassessed      no contract declared. Nothing is proposed. Absence of a contract
                  is not permission, and it is not `none` either.
  abstain         the contract declares `expressiveness: none` or
                  `motion_budget: none`. A complete, correct answer: no motion.
  unknown_surface a contract exists but the path names no surface kind this
                  resolver knows. Withheld rather than guessed.
  applicable      one or more patterns clear every condition. Each carries the
                  pattern's own purpose and evidence level, so a hypothesis is
                  never presented with the weight of a proven pattern.

The corpus is DISCOVERED (every `*.md` with a `motion:` block), never enrolled by
hand, and an entry that is malformed is reported in `corpus_errors` rather than
dropped -- a silently skipped pattern is indistinguishable from one that does not
apply. The resolver never raises the contract and never proposes more motion than
the contract permits: every condition only narrows.
"""
from __future__ import annotations

import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
CORPUS_DIR = os.path.join(_PP_ROOT, "vault", "knowledge_base", "visual-patterns")

# Mirrors tools/design_gate.py. Pinned against it by V-MGRAM-RANK-DRIFT so the two
# vocabularies cannot diverge without a red gate.
EXPRESSIVENESS_RANK = {"none": 0, "restrained": 1, "moderate": 2, "high": 3}
MOTION_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}

# Ordered weakest -> strongest. `hypothesis` < `research` (verified externally,
# never built here) < `local` (observed and built once) < ... < `baseline`.
EVIDENCE_LEVELS = ("hypothesis", "research", "local", "repeated", "proven",
                   "baseline-candidate", "baseline")

# Surface vocabulary. A kind is inferred from any path segment or filename token.
# Several kinds may match one path; the exclusion test then wins, so
# `onboarding/payment/page.tsx` is judged as checkout as well as onboarding.
SURFACE_TOKENS = {
    "landing": {"landing", "home", "homepage", "marketing"},
    "hero": {"hero"},
    "onboarding": {"onboarding", "welcome", "getting-started", "getstarted"},
    "product-tour": {"tour", "demo", "showcase", "features", "product-tour"},
    "pricing": {"pricing", "plans"},
    "checkout": {"checkout", "payment", "payments", "billing", "cart", "refund"},
    "auth": {"login", "signin", "sign-in", "signup", "sign-up", "register", "auth",
             "password"},
    "admin": {"admin", "backoffice", "console", "ops"},
    "settings": {"settings", "preferences", "account"},
    "form": {"form", "forms"},
    "dashboard": {"dashboard", "analytics", "reports", "metrics"},
    "list-detail": {"detail", "details", "list", "inbox", "feed"},
    "destructive": {"delete", "danger", "destroy", "remove"},
    "docs": {"docs", "documentation", "guide", "guides"},
}

REQUIRED_FIELDS = ("applies_to", "excluded_from", "min_expressiveness",
                   "min_motion_budget", "requires_reduced_motion", "evidence_level",
                   "provenance", "purpose")

_BLOCK_RE = re.compile(r"^motion:[ \t]*\r?\n((?:[ \t]+\S.*\r?\n?)*)", re.MULTILINE)
_FIELD_RE = re.compile(r"^[ \t]+([a-z_]+):[ \t]*(.+?)[ \t]*$", re.MULTILINE)
_ID_RE = re.compile(r"^id:[ \t]*(\S+)", re.MULTILINE)
_NAME_RE = re.compile(r"^name:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
# HR-VP-01: an entry without a "when NOT to use" section is advertising.
_NOT_USE_RE = re.compile(r"^##[ \t]+Cuando NO usar[ \t]*\r?\n(.*?)(?=^##[ \t]|\Z)",
                         re.MULTILINE | re.DOTALL)


def surface_kinds(surface_path: str) -> list:
    """Return the sorted surface kinds named by a path, or [] if none."""
    if not surface_path:
        return []
    norm = surface_path.replace("\\", "/").lower()
    parts = [p for p in norm.split("/") if p]
    tokens = set()
    for part in parts:
        stem = os.path.splitext(part)[0]
        tokens.add(stem)
        tokens.update(t for t in re.split(r"[^a-z0-9-]+", stem) if t)
        tokens.update(t for t in re.split(r"[^a-z0-9]+", stem) if t)
    return sorted(k for k, words in SURFACE_TOKENS.items() if tokens & words)


def _parse_value(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [v.strip().strip("\"'") for v in raw[1:-1].split(",") if v.strip()]
    return raw.strip("\"'")


def parse_entry(path: str):
    """Return (entry_dict, errors) for one pattern file, or (None, []) if the file
    carries no `motion:` block (it is simply not a motion pattern)."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        return None, [f"{os.path.basename(path)}: unreadable ({exc})"]
    parts = text.lstrip().split("---", 2)
    fm = parts[1] if text.lstrip().startswith("---") and len(parts) >= 3 else ""
    block = _BLOCK_RE.search(fm)
    if not block:
        return None, []
    name = os.path.basename(path)
    fields = {k: _parse_value(v) for k, v in _FIELD_RE.findall(block.group(1))}
    errors = [f"{name}: missing motion.{f}" for f in REQUIRED_FIELDS if f not in fields]
    for key, vocab in (("min_expressiveness", EXPRESSIVENESS_RANK),
                       ("min_motion_budget", MOTION_RANK)):
        if key in fields and fields[key] not in vocab:
            errors.append(f"{name}: motion.{key}={fields[key]!r} not in {sorted(vocab)}")
    if "evidence_level" in fields and fields["evidence_level"] not in EVIDENCE_LEVELS:
        errors.append(f"{name}: motion.evidence_level={fields['evidence_level']!r} "
                      f"not in {list(EVIDENCE_LEVELS)}")
    for key in ("applies_to", "excluded_from"):
        vals = fields.get(key)
        if key in fields and not isinstance(vals, list):
            errors.append(f"{name}: motion.{key} must be a [list]")
        elif isinstance(vals, list):
            unknown = sorted(set(vals) - set(SURFACE_TOKENS))
            if unknown:
                errors.append(f"{name}: motion.{key} names unknown surface kinds {unknown}")
    if fields.get("requires_reduced_motion") not in (None, "equivalent"):
        errors.append(f"{name}: motion.requires_reduced_motion must be 'equivalent' "
                      "(CDIO-07 sec.5: accessibility floors are not arbitrable)")
    not_use = _NOT_USE_RE.search(text)
    if not not_use or len(not_use.group(1).strip()) < 40:
        errors.append(f"{name}: 'Cuando NO usar' missing or empty (HR-VP-01)")
    idm, nm = _ID_RE.search(fm), _NAME_RE.search(fm)
    if not idm:
        errors.append(f"{name}: missing id")
    entry = dict(fields, id=idm.group(1) if idm else name, name=nm.group(1) if nm else name,
                 file=os.path.relpath(path, _PP_ROOT).replace("\\", "/"))
    return (None if errors else entry), errors


def load_corpus(corpus_dir: str = CORPUS_DIR):
    """Discover every motion pattern. Returns (entries, corpus_errors)."""
    entries, errors = [], []
    try:
        names = sorted(os.listdir(corpus_dir))
    except OSError as exc:
        return [], [f"corpus unreadable: {exc}"]
    for n in names:
        if n.endswith(".md") and n != "README.md":
            entry, errs = parse_entry(os.path.join(corpus_dir, n))
            errors.extend(errs)
            if entry:
                entries.append(entry)
    return entries, errors


def _judge(entry: dict, kinds: list, expr: str, motion: str, reduced: str):
    """Return None if the entry applies, else the first reason it does not."""
    excluded = sorted(set(kinds) & set(entry["excluded_from"]))
    if excluded:
        return f"surface is {excluded} which the pattern excludes"
    if not set(kinds) & set(entry["applies_to"]):
        return f"pattern applies to {entry['applies_to']}, surface is {kinds}"
    if EXPRESSIVENESS_RANK[expr] < EXPRESSIVENESS_RANK[entry["min_expressiveness"]]:
        return (f"needs expressiveness>={entry['min_expressiveness']}, "
                f"contract declares {expr}")
    if MOTION_RANK[motion] < MOTION_RANK[entry["min_motion_budget"]]:
        return (f"needs motion_budget>={entry['min_motion_budget']}, "
                f"contract declares {motion}")
    if entry["requires_reduced_motion"] == "equivalent" and reduced != "equivalent":
        return ("needs reduced_motion: equivalent; contract declares "
                f"{reduced or 'nothing'} -- the pattern cannot be honoured without "
                "breaching the reduced-motion floor")
    return None


def resolve(experience, surface_path: str, corpus_dir: str = CORPUS_DIR) -> dict:
    """Decide which motion patterns a surface may use under its declared contract."""
    entries, corpus_errors = load_corpus(corpus_dir)
    kinds = surface_kinds(surface_path)
    base = {"surface": surface_path, "surface_kinds": kinds, "patterns": [],
            "withheld": [], "corpus_size": len(entries), "corpus_errors": corpus_errors}

    if not experience:
        return dict(base, state="unassessed",
                    reason="no CDIO-07 experience contract declared; motion patterns "
                           "are not proposed to an undeclared surface")
    expr = experience.get("expressiveness")
    motion = experience.get("motion_budget")
    reduced = experience.get("reduced_motion")
    if expr == "none" or motion == "none":
        return dict(base, state="abstain",
                    reason=f"contract declares expressiveness={expr}, "
                           f"motion_budget={motion}: no motion is the correct answer "
                           "(CDIO-07 sec.3)")
    if expr not in EXPRESSIVENESS_RANK or motion not in MOTION_RANK:
        return dict(base, state="unassessed",
                    reason=f"contract does not declare usable expressiveness/"
                           f"motion_budget (got {expr!r}/{motion!r}); nothing proposed")
    if not kinds:
        return dict(base, state="unknown_surface",
                    reason="the surface path names no known surface kind "
                           f"({sorted(SURFACE_TOKENS)}); withheld rather than guessed")

    patterns, withheld = [], []
    for e in entries:
        why_not = _judge(e, kinds, expr, motion, reduced)
        if why_not:
            withheld.append({"id": e["id"], "reason": why_not})
        else:
            patterns.append({"id": e["id"], "name": e["name"], "file": e["file"],
                             "evidence_level": e["evidence_level"],
                             "purpose": e["purpose"], "provenance": e["provenance"]})
    state = "applicable" if patterns else "none_applicable"
    reason = (f"{len(patterns)} of {len(entries)} motion patterns clear surface "
              f"{kinds} under expressiveness={expr}, motion_budget={motion}")
    return dict(base, state=state, reason=reason, patterns=patterns, withheld=withheld)


def advisory_line(guidance: dict) -> str:
    """One line for the PreToolUse hook. Empty when there is nothing actionable:
    the injection stays proportional to the decision, never a corpus dump."""
    state = (guidance or {}).get("state")
    if state == "applicable":
        items = "; ".join(f"{p['id']} {p['name']} [{p['evidence_level']}] -> {p['file']}"
                          for p in guidance["patterns"])
        return (f"CDIO motion ({', '.join(guidance['surface_kinds'])}): patterns that "
                f"clear this surface's CDIO-07 contract: {items}. Read an entry before "
                "animating; each defines its purpose, 'Cuando NO usar' and the "
                "reduced-motion equivalent. Motion without one of these purposes is "
                "decoration and is not required.")
    if state == "abstain":
        return (f"CDIO motion: abstain -- {guidance['reason']}. Do not add animation "
                "to this surface.")
    return ""
