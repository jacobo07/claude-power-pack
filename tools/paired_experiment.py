"""Paired Experiments (T8 item 31, genesis-paired-experiments -> WRAP).

A comparison between two CPP alternatives is decided only by a PREREGISTERED experiment: the
spec (cases, holdout split, prompt/source/rubric hashes, requested worker, targets) is hashed
and frozen BEFORE any run, every run must start after that moment and carry that hash, and
every grade must be independent, blinded and bound to the exact output bytes it scored. The
vendored module enforces all of it through the one bridge; this wrapper adds the durable,
append-only experiment directory:

    vault/experiments/<id>/registration.json   frozen; a second, different registration is refused
    vault/experiments/<id>/runs.json           one record per (case, variant)
    vault/experiments/<id>/grades.json
    vault/experiments/<id>/analysis.json       the vendored analysis, verbatim

Failed runs are kept. Totals stay null when history is incomplete. monetarySavings is always null.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.external_assimilation import node_bridge as nb  # noqa: E402

EXPERIMENTS = ROOT / "vault" / "experiments"


class ExperimentError(Exception):
    pass


def js_now() -> str:
    d = datetime.now(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"


def exp_dir(exp_id: str, base: Path | None = None) -> Path:
    return (base or EXPERIMENTS) / exp_id


def preregister(spec: dict, base: Path | None = None) -> dict:
    """Freeze the spec. Re-registering the identical spec is a no-op; a different one refuses."""
    r = nb.call("pairedExperiments", "preregisterExperiment", [spec], timeout=60)
    if not r.ok:
        raise ExperimentError(f"registration refused: {r.outcome} {r.error}")
    reg = r.value
    d = exp_dir(spec["id"], base)
    path = d / "registration.json"
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("sha256") != reg["sha256"]:
            raise ExperimentError(f"{spec['id']} is already registered as {old.get('sha256', '')[:12]}; "
                                  f"a changed spec is a NEW experiment, never an edit")
        return old
    d.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, indent=1), encoding="utf-8")
    return reg


def load(exp_id: str, name: str, base: Path | None = None, default=None):
    p = exp_dir(exp_id, base) / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save(exp_id: str, name: str, value, base: Path | None = None) -> Path:
    p = exp_dir(exp_id, base) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=1), encoding="utf-8")
    return p


def analyze(exp_id: str, base: Path | None = None, overhead_tokens: dict | None = None) -> dict:
    reg = load(exp_id, "registration.json", base)
    if reg is None:
        raise ExperimentError(f"{exp_id}: not registered")
    payload = {"registration": reg, "runs": load(exp_id, "runs.json", base, []),
               "grades": load(exp_id, "grades.json", base, [])}
    if overhead_tokens is not None:
        payload["overheadTokens"] = overhead_tokens
    r = nb.call("pairedExperiments", "analyzeExperiment", [payload], timeout=60)
    if not r.ok:
        raise ExperimentError(f"analysis refused: {r.outcome} {r.error}")
    save(exp_id, "analysis.json", r.value, base)
    return r.value
