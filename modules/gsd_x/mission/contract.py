#!/usr/bin/env python3
"""Mission Contract v1 -- a PROJECTION over owners that already exist.

The contract is not a record. Almost every field it exposes is owned somewhere
else and is read on demand, because a copy of someone else's truth is a second
truth that drifts, and the drift is silent. Each field therefore carries the
owner it came from and how it was obtained:

    PROJECTED  read from an existing owner at call time (GSD's .planning, git,
               the baseline chain). Never cached, never persisted.
    COMPUTED   derived from other fields by a pure function here.
    STORED     genuinely mission-specific, owned by nobody else, durable.

Exactly two things are STORED, and both had to be argued for rather than
assumed:

  * the verbatim human intent -- nothing else in the estate retains the sparse
    sentence a mission started from, and the whole point of the wave is to keep
    it distinguishable from what was derived afterwards (a closure receipt that
    cannot say which requirements the human asked for cannot report honestly);
  * the derived obligations themselves, which are new semantics.

Everything else is a read.

WHAT THIS IS NOT. It is not a lifecycle. GSD owns phase, plan, task, execution,
verification and transition, and this module neither writes nor contradicts any
of them: a mission with no GSD location reports `absent`, it does not invent
one. It is not a mission database -- there is no store here, and the obligation
store it points at is scoped to one mission's own directory.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Sources: STORED is the only one that owns anything.
PROJECTED = "PROJECTED"
COMPUTED = "COMPUTED"
STORED = "STORED"
ABSENT = "ABSENT"


@dataclass(frozen=True)
class Field:
    """One contract field, and an answer to 'who says so?'."""
    name: str
    value: object
    kind: str
    owner: str

    @property
    def present(self) -> bool:
        return self.value not in (None, "", [], {})


def _git(root: Path, *args: str) -> str | None:
    """git, or None. A repo question has three answers and one of them is
    'this is not a repo', which is not an error and must not read as one."""
    for exe in (r"C:\Program Files\Git\cmd\git.exe", "git"):
        try:
            p = subprocess.run([exe, "-C", str(root), *args],
                               capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        return p.stdout.strip() if p.returncode == 0 else None
    return None


def _planning_dir(root: Path) -> Path | None:
    d = root / ".planning"
    return d if d.is_dir() else None


def _state_field(planning: Path, key: str) -> str | None:
    """Read a `key: value` line from GSD's STATE.md without parsing the rest.

    Deliberately narrow: this module reads GSD's state, it does not model it.
    A parser that understood the whole file would be a second implementation of
    something GSD owns, and would go wrong the first time GSD changed it.
    """
    f = planning / "STATE.md"
    if not f.is_file():
        return None
    try:
        text = f.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _baseline_chain(root: Path) -> list[str]:
    """Which baseline documents actually apply here, nearest first.

    Projected, never copied. The contract reports WHICH baseline governs the
    mission; it does not restate its contents, because restating them is how a
    mission ends up with a stale private fork of the estate's doctrine.
    """
    found = []
    for p in (root / "CLAUDE.md", root.parent / "CLAUDE.md",
              Path.home() / ".claude" / "CLAUDE.md"):
        try:
            if p.is_file():
                found.append(str(p))
        except OSError:
            continue
    # de-duplicate while keeping order: root and root.parent can coincide
    return list(dict.fromkeys(found))


@dataclass
class MissionContract:
    mission_id: str
    root: Path
    fields: list[Field] = field(default_factory=list)

    def get(self, name: str) -> Field | None:
        return next((f for f in self.fields if f.name == name), None)

    def value(self, name: str, default=None):
        f = self.get(name)
        return f.value if f is not None else default

    def by_kind(self, kind: str) -> list[Field]:
        return [f for f in self.fields if f.kind == kind]

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "root": str(self.root),
            "fields": [
                {"name": f.name, "kind": f.kind, "owner": f.owner, "value": f.value}
                for f in self.fields
            ],
        }


def project(root: Path, intent: str | None = None,
            obligations: list | None = None) -> MissionContract:
    """Build the contract by reading its owners. Writes nothing, anywhere."""
    root = Path(root).resolve()
    planning = _planning_dir(root)
    fields: list[Field] = []

    def add(name, value, kind, owner):
        fields.append(Field(name, value, kind if value not in (None, "", []) else ABSENT,
                            owner))

    # --- identity -----------------------------------------------------------
    milestone = _state_field(planning, "milestone_name") if planning else None
    add("milestone", milestone, PROJECTED, ".planning/STATE.md (GSD)")
    add("repo", root.name, PROJECTED, "filesystem")
    add("branch", _git(root, "rev-parse", "--abbrev-ref", "HEAD"), PROJECTED, "git")
    add("head", (_git(root, "rev-parse", "--short", "HEAD") or None), PROJECTED, "git")

    # --- the human's own words ---------------------------------------------
    # STORED, and kept verbatim. A contract that paraphrases the intent has
    # already begun deciding what the mission is about.
    if intent is None:
        f = root / "INTENT.txt"
        intent = f.read_text(encoding="utf-8-sig").strip() if f.is_file() else None
    add("human_intent", intent, STORED, "the human")

    # --- where GSD thinks this mission is -----------------------------------
    # `absent` is a real answer: a mission that has not entered GSD has no
    # phase, and inventing one would be the duplicate lifecycle this module
    # exists to avoid.
    if planning:
        phases = sorted(p.name for p in (planning / "phases").glob("*")) \
            if (planning / "phases").is_dir() else []
        plans = sorted(p.name for p in planning.glob("*PLAN*.md"))
        cfg = planning / "config.json"
        try:
            config = json.loads(cfg.read_text(encoding="utf-8-sig")) if cfg.is_file() else None
        except (OSError, json.JSONDecodeError):
            config = None
        add("gsd_location", {"phases": phases, "plans": plans}, PROJECTED,
            ".planning/ (GSD)")
        add("gsd_config", config, PROJECTED, ".planning/config.json (GSD)")
    else:
        add("gsd_location", None, PROJECTED, ".planning/ (GSD) -- not present")
        add("gsd_config", None, PROJECTED, ".planning/config.json (GSD) -- not present")

    # --- baseline -----------------------------------------------------------
    add("baseline", _baseline_chain(root), PROJECTED, "CLAUDE.md chain")

    # --- inspectable project reality ---------------------------------------
    try:
        reality = sorted(p.name for p in root.iterdir() if p.is_file())[:50]
    except OSError:
        reality = []
    add("project_reality", reality, PROJECTED, "filesystem")

    # --- the genuinely new part --------------------------------------------
    obs = list(obligations or [])
    add("derived_obligations", [o.to_dict() for o in obs], STORED,
        "gsd_x mission obligation store")

    # A proof requirement is not a field somebody sets; it is what each accepted
    # obligation already carries. Computing it keeps one owner.
    add("proof_requirements",
        [{"obligation": o.id, "proof": o.proof} for o in obs
         if o.is_accepted and o.proof],
        COMPUTED, "derived from accepted obligations")

    mission_id = milestone or f"{root.name}"
    return MissionContract(mission_id=mission_id, root=root, fields=fields)
