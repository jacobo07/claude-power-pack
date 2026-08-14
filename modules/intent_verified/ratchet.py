"""The criterion set as a NAMED ratchet.

The denominator is discovered from the specs, which closes one hole and opens
another: delete a criterion and the denominator shrinks silently. This module
is the answer, and it is the same one `vault/governance/mutation_ratchet.json`
already uses -- standing debt is a named set, never a count, because a
threshold is satisfied by deleting a subject and a name is not.

Two regressions are refused:

  WITHDRAWN     a criterion the baseline recorded is gone from every spec
  UNJOINED_BACK a criterion that was reachable from the standing gate no
                longer is

Debt falling is always allowed. Debt growing must be named to be accepted.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .join import CriterionResult, Reach

SCHEMA_VERSION = 1
DEFAULT_BASELINE = Path("vault") / "governance" / "intent_ratchet.json"


@dataclass
class RatchetReport:
    withdrawn: list[str] = field(default_factory=list)
    unjoined_back: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    repaired: list[str] = field(default_factory=list)

    @property
    def regressed(self) -> bool:
        return bool(self.withdrawn or self.unjoined_back)

    def as_dict(self) -> dict:
        return {"withdrawn": self.withdrawn,
                "unjoined_back": self.unjoined_back,
                "added": self.added, "repaired": self.repaired}


def snapshot(results: list[CriterionResult]) -> dict:
    """Current state, keyed by spec, values sorted for a stable diff."""
    specs: dict[str, dict[str, list[str]]] = {}
    for r in results:
        entry = specs.setdefault(r.criterion.spec,
                                 {"criteria": [], "unjoined": []})
        entry["criteria"].append(r.criterion.id)
        if r.reach is not Reach.REACHABLE:
            entry["unjoined"].append(r.criterion.id)
    for entry in specs.values():
        entry["criteria"] = sorted(set(entry["criteria"]))
        entry["unjoined"] = sorted(set(entry["unjoined"]))
    return {"version": SCHEMA_VERSION,
            "updated": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "specs": dict(sorted(specs.items()))}


def _ids(state: dict, key: str) -> set[str]:
    out: set[str] = set()
    for entry in (state.get("specs") or {}).values():
        out.update(entry.get(key) or ())
    return out


def load(path: Path) -> dict | None:
    """The baseline, or None when none has been recorded yet."""
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path: Path, state: dict) -> Path:
    """Atomic write -- a half-written baseline would fail every later run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return path


def compare(baseline: dict | None, current: dict) -> RatchetReport:
    """Diff two snapshots by NAME. A first run has nothing to regress from."""
    if not baseline:
        return RatchetReport(added=sorted(_ids(current, "criteria")))
    base_all, cur_all = _ids(baseline, "criteria"), _ids(current, "criteria")
    base_unjoined = _ids(baseline, "unjoined")
    cur_unjoined = _ids(current, "unjoined")
    return RatchetReport(
        withdrawn=sorted(base_all - cur_all),
        # Reachable before, not reachable now -- and still declared, so this
        # is a real loss of coverage rather than a criterion that was removed.
        unjoined_back=sorted((cur_unjoined - base_unjoined) & base_all),
        added=sorted(cur_all - base_all),
        repaired=sorted(base_unjoined - cur_unjoined))


def check(results: list[CriterionResult],
          baseline_path: Path) -> tuple[RatchetReport, dict]:
    """Compare the current criterion set against the recorded baseline."""
    current = snapshot(results)
    return compare(load(baseline_path), current), current


__all__ = ["SCHEMA_VERSION", "DEFAULT_BASELINE", "RatchetReport", "snapshot",
           "load", "save", "compare", "check"]
