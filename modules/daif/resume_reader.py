#!/usr/bin/env python3
"""The far side of the context boundary.

This script is the resumed actor's substrate. It imports nothing from the Power Pack, reads no
transcript, opens no repository, and holds no memory of the session that produced its input. It is
handed ONE file — the resume pack — and it must report what survived.

That isolation is the whole point. DAIF-07 12.6 requires the fidelity claim to be DRILLED rather
than asserted: kill the session, resume with only what is durable, and compare. A verifier that
imports the compiler, or that can fall back on the transcript, is not the far side of a boundary;
it is the near side wearing a costume, and it would certify a pack that a real resumed actor could
not use.

It reports four things, and no opinion:
  what it can list        the constraint and obligation identifiers present in the pack
  what it can CLOSE       DAIF-07 12.5 — an obligation surviving as a name with no closure
                          condition is a haunting, and is reported LOST, loudly
  what it can audit       every critical claim's evidence pointer (11.5 clause 5)
  what has MOVED          each constraint source re-hashed against the pack's record; a source that
                          changed while the session was down is detected here or by nothing
                          (11.5 clause 6)

Exit 0 always — it is an instrument, not a gate. The gate reads its output.

CLI:
  python modules/daif/resume_reader.py <continuity_package.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_SLOTS = [
    "mission_contract", "hard_constraints", "decisions_with_justifications", "current_reality",
    "open_obligations", "evidence_pointers", "expansion_handles", "done_gate",
]


def read_package(package_path: str | Path) -> dict[str, Any]:
    """Everything this process knows comes through here. Fail-open to an empty, honest report."""
    try:
        raw = Path(package_path).read_text(encoding="utf-8-sig", errors="replace")
        package = json.loads(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "readable": False,
            "error": f"{type(exc).__name__}: {exc}",
            "constraint_ids": [],
            "obligation_ids": [],
        }
    if not isinstance(package, dict):
        return {"readable": False, "error": "package is not an object",
                "constraint_ids": [], "obligation_ids": []}

    constraints = package.get("hard_constraints") or []
    obligations = package.get("open_obligations") or []

    constraint_ids = [c.get("identifier") for c in constraints if isinstance(c, dict)]
    obligation_ids = [o.get("identifier") for o in obligations if isinstance(o, dict)]

    # Clause 5 — a constraint whose provenance does not resolve is a claim the resumed actor cannot
    # audit, and it is reported rather than trusted.
    constraints_without_evidence = [
        c.get("identifier") for c in constraints
        if isinstance(c, dict) and not str(c.get("provenance") or "").strip()
    ]

    # DAIF-07 12.5 — closeability, the five resumption elements, checked from the pack alone.
    closeable, hauntings = [], []
    for o in obligations:
        if not isinstance(o, dict):
            continue
        has_what = bool(str(o.get("text") or "").strip())
        has_why = bool(str(o.get("origin") or "").strip())
        has_closure = bool(str(o.get("closure_condition") or "").strip())
        has_evidence = bool(o.get("source") or o.get("evidence"))
        if has_what and has_why and has_closure and has_evidence:
            closeable.append(o.get("identifier"))
        else:
            hauntings.append({
                "identifier": o.get("identifier"),
                "missing": [name for name, ok in (
                    ("what", has_what), ("why", has_why),
                    ("what_closes_it", has_closure), ("evidence", has_evidence)) if not ok],
            })

    # Clause 6 — re-hash each constraint source. This is the only thing the far side reads besides
    # the pack, and it reads it to distrust the pack, never to repair it.
    moved_sources, unreadable_sources = [], []
    for src in (package.get("integrity", {}) or {}).get("constraint_sources", []) or []:
        if not isinstance(src, dict):
            continue
        path, recorded = src.get("path"), src.get("sha256")
        try:
            lines = Path(str(path)).read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            unreadable_sources.append(src.get("source"))
            continue
        now = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
        if now != recorded:
            moved_sources.append({"source": src.get("source"),
                                  "recorded_sha256": recorded, "observed_sha256": now})

    missing_slots = [s for s in REQUIRED_SLOTS if s not in package]

    return {
        "readable": True,
        "schema": package.get("schema", "unknown"),
        "session_id": package.get("session_id", "unknown"),
        "status": package.get("status", "unknown"),
        "cannot_guarantee": package.get("cannot_guarantee", []),
        "constraint_ids": constraint_ids,
        "obligation_ids": obligation_ids,
        "closeable_obligation_ids": closeable,
        "hauntings": hauntings,
        "constraints_without_evidence": constraints_without_evidence,
        "missing_slots": missing_slots,
        "moved_sources": moved_sources,
        "unreadable_sources": unreadable_sources,
        "counts": {
            "constraints": len(constraint_ids),
            "obligations": len(obligation_ids),
            "closeable": len(closeable),
            "hauntings": len(hauntings),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resume from a DAIF continuity package, alone")
    ap.add_argument("package", help="path to continuity_<session_id>.json")
    args = ap.parse_args(argv)
    print(json.dumps(read_package(args.package), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
