#!/usr/bin/env python3
"""DAIF-08 Part XI — the Session Continuity Cognitive Compiler.

The corpus designates session continuity as its first proving vertical (11.1) and specifies what
a resume pack must CONTAIN (11.3), the gate by which its sufficiency is judged (11.5), and the
visible failure it must produce when it cannot guarantee that sufficiency (11.6). This module is
that compiler. It is not Lazarus and it is not the estate's session recorder — 11.2 names those
as the parents, and this builds neither. It compiles the pack they carry.

The eight required contents of 11.3, and where each comes from:
  mission contract         the session's opening intent + the compiled done-gate
  hard constraints         constraint_extractor (DAIF-01 Strength=hard), admitted WHOLE
  decisions + justification declared unknown -- there is no decision extractor yet, and 11.3 is
                           explicit that a decision carried without its reason is worse than not
                           carried, so it is named as a gap rather than filled with a guess
  current reality          observations and verdicts (git head, branch, dirt), never the plan's
                           assumptions about them
  open obligations         obligation_extractor (DAIF-07), the most frequently lost item
  evidence pointers        every constraint's file:line, every obligation's session#turn
  expansion handles        what was deliberately excluded, with its exclusion reason, so the
                           resumed actor can SEE the boundary rather than invent past it
  done-gate                the six conjunctive clauses, present at the START

The seventh clause (11.6) is the one that makes the other six safe: when fidelity cannot be
guaranteed, the compiler FAILS VISIBLY -- it names what it cannot guarantee and hands the mission
to its authority rather than shipping a plausible pack. status='FAIL_VISIBLE' is that refusal.

No savings figure is asserted here (11.7). The only numbers this module produces are the survival
percentages the reset drill measures.

CLI:
  python modules/daif/session_continuity_compiler.py <session.jsonl> [--project .] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.daif.constraint_extractor import extract_constraints  # noqa: E402
from modules.daif.obligation_extractor import extract_obligations  # noqa: E402
from modules.daif.decision_extractor import extract_decisions  # noqa: E402

# Recognizable file-path tokens in free text -- shared shape with decision_extractor's
# _PATH_TOKEN_RE. Used to confirm existence of every file a constraint or obligation NAMES,
# so the resumed actor does not have to ask "does this file exist" (the c4 re-reading trigger
# the SCS C97 trial measured directly: two-arm trial evidence named this as a driver).
_PATH_TOKEN_RE = re.compile(
    r"\b[\w./\\-]+\.(?:py|js|ts|tsx|jsx|json|md|txt|yml|yaml|toml|cfg|ini|ps1|sh)\b"
)

# A pack too large to sit in a model's context alongside its work is not a pack, it is the
# monolith of DAIF-08 Part XVII level 1 wearing a new name. The budget is declared, not derived:
# roughly a tenth of a 200k context, leaving the resumed mission the other nine tenths to work in.
#
# When the pack exceeds it, the compiler fails VISIBLY and hands the mission to its authority — it
# does NOT trim the constraint set to fit. DAIF-08 11.3 and Part VIII are explicit that hard
# constraints are a FLOOR and not a share, and that a constraint may not be abridged to fit a
# percentage. So an over-budget pack is evidence that the BUDGET is wrong, never that the law is
# too long, and the authority is the only party that may move it.
TOKEN_BUDGET = 20_000
CHARS_PER_TOKEN = 4          # the estate's standing coarse proxy; declared, not hidden

# 11.5 — six conjunctive clauses, no partial credit. Clauses 3 and 4 are BEHAVIORAL: they require
# the two-arm trial of 11.7 (an LLM resumed from the pack vs. one resumed by re-reading) and this
# compiler cannot measure them. They are declared unverified rather than claimed.
GATE_CLAUSES = {
    "c1_constraints_survive": "100% of hard constraints survive the boundary",
    "c2_obligations_survive": "100% of open obligations survive the boundary",
    "c3_state_identified": "the resumed actor knows what is done, in flight, and not started",
    "c4_no_indiscriminate_reread": "the actor continues without re-reading the repository",
    "c5_claims_link_to_evidence": "every critical claim in the pack links to evidence",
    "c6_changed_source_detected": "a source that changed while the session was down is detected",
    "c7_fail_visibly": "when fidelity cannot be guaranteed, the runtime fails visibly",
}
MECHANICALLY_MEASURED = ["c1_constraints_survive", "c2_obligations_survive",
                         "c5_claims_link_to_evidence", "c6_changed_source_detected",
                         "c7_fail_visibly"]
BEHAVIORAL_UNVERIFIED = ["c3_state_identified", "c4_no_indiscriminate_reread"]


def _git(project: Path, *args: str) -> str:
    """Observations, not assumptions (11.3). Fail-open to 'unknown'."""
    for exe in ("git", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            r = subprocess.run([exe, "-C", str(project), *args], capture_output=True,
                               text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0:
            return r.stdout.strip()
    return "unknown"


# Two-arm trial evidence (vault/trials/two_arm_c718d3f5*.json, SCS C97): the resumed actor's
# FIRST source request was "git log / git status ... shows 87 uncommitted paths -- need to see
# what those paths are before continuing." A count is not current reality (11.3) -- it is a
# summary of current reality that forces exactly the re-read the gate exists to prevent. The
# LIST is the observation; a cap exists because the pack has a token budget too (TOKEN_BUDGET).
MAX_LISTED_PATHS = 15


def _current_reality(project: Path) -> dict[str, Any]:
    dirty = _git(project, "status", "--porcelain")
    dirty_lines = [] if dirty in ("", "unknown") else dirty.splitlines()
    uncommitted_files = [line[3:].strip() if len(line) > 3 else line.strip()
                         for line in dirty_lines[:MAX_LISTED_PATHS]]
    # The per-file table is the expensive part and the totals line carries the signal that
    # matters at pack scale (how much moved); the full table is one `git diff --stat HEAD`
    # away and is exactly what expansion_handles names as available on request.
    diff_stat_full = _git(project, "diff", "--stat", "HEAD")
    diff_stat_lines = diff_stat_full.splitlines() if diff_stat_full != "unknown" else []
    diff_summary = diff_stat_lines[-1] if diff_stat_lines else ""
    return {
        "head_commit": _git(project, "log", "-1", "--format=%H"),
        "head_subject": _git(project, "log", "-1", "--format=%s"),
        "branch": _git(project, "rev-parse", "--abbrev-ref", "HEAD"),
        "uncommitted_paths": len(dirty_lines),
        "uncommitted_files": uncommitted_files,
        "uncommitted_files_truncated": len(dirty_lines) > MAX_LISTED_PATHS,
        "diff_summary": diff_summary,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "instrument": "git",
    }


def _referenced_files(project: Path, texts: list[str]) -> list[dict[str, Any]]:
    """Every file a constraint or obligation NAMES, with existence confirmed here rather than
    left for the resumed actor to ask about -- the second gap the SCS C97 trial localized
    ("the pack names files whose existence it never confirms")."""
    tokens: set[str] = set()
    for text in texts:
        tokens.update(_PATH_TOKEN_RE.findall(text))
    out = []
    for tok in sorted(tokens):
        candidate = (project / tok)
        try:
            exists = candidate.exists()
        except OSError:
            exists = False
        out.append({"path": tok, "exists": exists})
    return out


def _mission_contract(session_path: Path, obligations: list[Any]) -> dict[str, Any]:
    """The opening intent, read from the session's first human turn. A continued mission that has
    forgotten its own done-gate is not a continuation but a fresh improvisation (11.3)."""
    intent = "unknown"
    try:
        for line in session_path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(rec, dict) or rec.get("type") != "user":
                continue
            msg = rec.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            text = ""
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "\n".join(b.get("text", "") for b in content
                                 if isinstance(b, dict) and b.get("type") == "text")
            text = text.strip()
            if len(text) > 30:
                intent = text[:1200]
                break
    except OSError:
        pass
    return {
        "intent": intent,
        "authority": "owner",
        "done_gate": "the open obligations below are discharged under their own done-gates",
        "open_obligation_count": len(obligations),
    }


def compile_session(project_path: str | Path, session_path: str | Path) -> dict[str, Any]:
    """Compile the resume pack. Never raises; an unrecoverable input yields status=FAIL_VISIBLE."""
    project = Path(project_path).resolve()
    session = Path(session_path).resolve()

    constraints, c_report = extract_constraints(project)
    obligations, o_report = extract_obligations(session)
    decisions, d_report = extract_decisions(session, project)
    hard = [c for c in constraints if c.strength == "hard"]

    # 11.6 — name what cannot be guaranteed, do not paper over it.
    cannot_guarantee: list[str] = []
    if o_report["turns_scanned"] == 0:
        cannot_guarantee.append(
            f"session {session.name} yielded 0 readable turns — no obligation can be claimed to "
            "have survived a boundary the compiler never saw")
    if not hard:
        cannot_guarantee.append(
            "0 hard constraints extracted — a resume pack with no constraints cannot be trusted "
            "to hold the estate's law across the boundary")
    if c_report["sources_skipped"]:
        cannot_guarantee.append(
            "constraint sources unreadable: " + ", ".join(c_report["sources_skipped"]))
    not_closeable = [o.identifier for o in obligations if not o.is_closeable()]
    if not_closeable:
        # DAIF-07 12.5 — an obligation that survives as a name with no closure condition is a
        # HAUNTING, and counting it as survived is the estate lying to itself with its instrument.
        cannot_guarantee.append(
            f"{len(not_closeable)} obligation(s) survive as names without a closure condition: "
            + ", ".join(not_closeable[:5]))

    package: dict[str, Any] = {
        "schema": "daif-08-part-xi/resume-pack/v1",
        "session_id": session.stem,
        "session_path": str(session),
        "project": str(project),
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "status": "COMPILED",
        "mission_contract": _mission_contract(session, obligations),
        "hard_constraints": [asdict(c) for c in hard],
        "open_obligations": [asdict(o) for o in obligations],
        "decisions_with_justifications": {
            "value": [asdict(d) for d in decisions],
            "intake_report": d_report,
            "reason": (
                f"{d_report['found']} decision(s) with a stated rationale recovered from the "
                f"session by archaeology ({d_report['drk_matched']} cross-matched against the "
                "DRK Decision Registry). This is archaeology, not capture-at-creation (DAIF-08 "
                "11.3): a low-confidence recovered pair is still carried, because a decision "
                "without its reason is worse than not carrying it, but a decision the archaeology "
                "never found is not fabricated to fill the slot."
                if decisions else
                "0 decisions with a stated rationale were found in-session or in the DRK "
                "registry. This is a real, checked absence, not the prior unmeasured default: "
                f"{d_report['turns_scanned']} turns scanned, "
                f"{d_report['drk_registry_records_checked']} DRK records checked."
            ),
        },
        "current_reality": _current_reality(project),
        "referenced_files": _referenced_files(
            project,
            [c.text for c in hard] + [o.text for o in obligations]
            + [d.chosen + " " + d.rationale for d in decisions],
        ),
        "evidence_pointers": {
            "constraints": [c.provenance for c in hard],
            "obligations": [p for o in obligations for p in o.source],
            "decisions": [p for d in decisions for p in d.source],
        },
        "expansion_handles": [
            {
                "handle": "full_session_transcript",
                "target": str(session),
                "exclusion_reason": "excluded by size — the pack carries the compiled obligations, "
                                    "not the turns they were lifted from",
            },
            {
                "handle": "process_rules",
                "target": "the project and global CLAUDE.md soft rules",
                "exclusion_reason": f"excluded by strength — {c_report['process_rules_seen_not_carried']} "
                                    "soft rules are tradeable under record and are not admitted "
                                    "into a pack whose floor is the hard law",
            },
            {
                "handle": "daif_corpus",
                "target": "vault/knowledge_base/d2a_fabric/",
                "exclusion_reason": "excluded by scope — the corpus SPECIFIES this pack, it is not "
                                    "context the resumed mission needs to execute",
            },
            {
                "handle": "full_diff_stat",
                "target": "git diff --stat HEAD",
                "exclusion_reason": "excluded by budget — current_reality.diff_summary carries the "
                                    "totals line; the per-file table costs pack budget the totals "
                                    "line does not, and is one command away if the actor needs it",
            },
            {
                "handle": "uncommitted_files_full_list",
                "target": "git status --porcelain",
                "exclusion_reason": f"excluded by budget — current_reality.uncommitted_files caps at "
                                    f"{MAX_LISTED_PATHS} of the real, uncapped list; a truncated list "
                                    "is disclosed via uncommitted_files_truncated rather than silently "
                                    "presented as complete",
            },
        ],
        "done_gate": {
            "clauses": GATE_CLAUSES,
            "conjunctive": True,
            "partial_credit": False,
            "mechanically_measured": MECHANICALLY_MEASURED,
            "behavioral_unverified": BEHAVIORAL_UNVERIFIED,
            "unverified_reason": "clauses 3 and 4 are behavioral and require the two-arm trial of "
                                 "DAIF-08 11.7 (resume-from-pack vs. resume-by-re-reading, with "
                                 "cost, fidelity and rework recorded on each arm). This compiler "
                                 "does not measure them and does not claim them.",
        },
        "integrity": {
            # The far side re-hashes these. A source that moved while the session was down is
            # DETECTED here or by nothing (11.5 clause 6).
            "constraint_sources": c_report["sources_read"],
        },
        "intake_report": o_report,
        "constraint_report": {k: v for k, v in c_report.items() if k != "sources_read"},
        "savings_claim": None,   # 11.7 — no figure is asserted in advance, and none is stored
    }

    body = json.dumps(package, ensure_ascii=False)
    est_tokens = len(body) // CHARS_PER_TOKEN
    package["size"] = {
        "chars": len(body),
        "estimated_tokens": est_tokens,
        "budget_tokens": TOKEN_BUDGET,
        "fits_budget": est_tokens <= TOKEN_BUDGET,
        "instrument": f"chars // {CHARS_PER_TOKEN} (coarse proxy, declared)",
    }
    if not package["size"]["fits_budget"]:
        cannot_guarantee.append(
            f"pack is {est_tokens} estimated tokens against a {TOKEN_BUDGET} budget — a pack that "
            "cannot be carried is not a pack. The constraints are a floor and may not be abridged "
            "to fit (11.3): the authority must raise the budget or narrow the mission's scope")

    if cannot_guarantee:
        package["status"] = "FAIL_VISIBLE"
        package["cannot_guarantee"] = cannot_guarantee
        package["handed_to"] = "owner"
    return package


def write_package(package: dict[str, Any], project_path: str | Path,
                  out: str | Path | None = None) -> Path:
    if out is not None:
        path = Path(out)
    else:
        path = Path(project_path) / "vault" / "sessions" / \
            f"continuity_{package['session_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DAIF-08 Part XI session continuity compiler")
    ap.add_argument("session", help="path to a Claude Code session .jsonl")
    ap.add_argument("--project", default=".", help="project root")
    ap.add_argument("--out", default=None, help="write the package here")
    args = ap.parse_args(argv)

    package = compile_session(args.project, args.session)
    path = write_package(package, args.project, args.out)

    size = package["size"]
    print(f"status           : {package['status']}")
    print(f"package          : {path}")
    print(f"hard constraints : {len(package['hard_constraints'])}")
    print(f"open obligations : {len(package['open_obligations'])}")
    print(f"size             : {size['estimated_tokens']} est. tokens "
          f"(budget {size['budget_tokens']}, fits={size['fits_budget']})")
    for line in package.get("cannot_guarantee", []):
        print(f"  CANNOT GUARANTEE: {line}")
    return 0 if package["status"] == "COMPILED" else 3


if __name__ == "__main__":
    sys.exit(main())
