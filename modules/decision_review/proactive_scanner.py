"""proactive_scanner.py -- DRK in proactive mode: propose without being asked.

The reactive kernel answers when a decision is brought to it. Most of a stack's
decision debt is never brought to anything: a gate that stopped firing, a dataset
nobody recalls, a residual that aged out, a module built without a recorded
decision. This scanner finds those and proposes.

DISCIPLINE (T-DRK-PROACTIVE-NOISE-001). A scanner that emits too much becomes
noise and is ignored -- at which point it is worse than absent, because the stack
believes it is covered. Three rules hold that line:
  1. Every suggestion carries `evidence` naming a REAL path or ledger row. A
     detector that cannot cite one emits nothing. No generic heuristics.
  2. `high` urgency requires a VERIFIABLE high blast radius -- a kernel-computed
     magnitude, or a drifted gate the stack believes is enforcing and which
     provably is not deployed. Nothing else earns high.
  3. Volume detectors are capped and the cap is REPORTED, never silent.

Every detector composes a system that already exists -- liveness (D1), recall_roi
(D3), owner_queue (D4), the DRK kernel itself. It invents no new signal.

Fail-open per detector: one that raises is skipped and the scan continues. The
scanner never blocks a workflow; it writes a report and, for high-urgency findings
only, appends to the existing OWNER_QUEUE.

Stdlib only. No hardcoded absolute paths.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from .decision_record import DecisionObject, Registry  # noqa: E402
from .decision_kernel import (  # noqa: E402
    classify_reversibility,
    compute_blast_radius,
    Reversibility,
)

HIGH, MEDIUM, LOW = "high", "medium", "low"

# A suggestion's urgency is `high` only above this kernel-computed blast magnitude
# (of the nine DRK-02 surfaces). Rule 2 above.
HIGH_BLAST_MAGNITUDE = 5
MEDIUM_BLAST_MAGNITUDE = 3

# Owner residuals: aged past this many hours they are debt, not queue.
RESIDUAL_DEBT_H = 24 * 7
RESIDUAL_ABANDONED_H = 24 * 30

# Volume cap for the unrecorded-decision detector (reported, never silent).
MAX_UNRECORDED = 5

_MODULE_SKIP = {"__pycache__", "decision_review"}


@dataclass
class ProactiveSuggestion:
    """One finding. `evidence` is the contract: a real path or ledger row that a
    reader can open. A suggestion without it is not published."""

    type: str          # decision_needed | debt | orphan | opportunity
    description: str
    repo: str
    path: str          # where in the repo it was detected
    verdict_hint: str  # a verdict from the closed DRK-00 ontology
    urgency: str       # high | medium | low
    evidence: str      # WHERE the finding came from -- never prose, never invented
    detector: str = ""
    blast: dict = field(default_factory=dict)

    def is_publishable(self) -> bool:
        """Rule 1: no evidence, no path -> not published. Enforced at the egress,
        so a sloppy detector cannot leak an ungrounded suggestion."""
        return bool((self.evidence or "").strip()) and bool((self.path or "").strip())

    def to_dict(self) -> dict:
        return asdict(self)


_URGENCY_ORDER = {HIGH: 0, MEDIUM: 1, LOW: 2}


def _urgency_from_blast(magnitude: int) -> str:
    if magnitude >= HIGH_BLAST_MAGNITUDE:
        return HIGH
    if magnitude >= MEDIUM_BLAST_MAGNITUDE:
        return MEDIUM
    return LOW


# --------------------------------------------------------------------------- #
# Detector 1 -- orphans / silent systems (composes D1 Liveness Ledger).
# --------------------------------------------------------------------------- #
def detect_orphans(*, repo_root: Path, now=None, state_dir=None) -> list:
    """Non-LIVE components from the D1 audit. Each row already carries its own
    evidence string -- the ledger's, not ours."""
    try:
        from modules.liveness.liveness_ledger import audit, LIVE, DRIFTED, SILENT, ORPHANED
        rows = audit(repo_root=repo_root, state_dir=state_dir, now=now)
    except Exception:  # noqa: BLE001 -- fail-open: detector skipped, scan continues
        return []
    hint = {DRIFTED: "APPROVE-WITH-CONDITIONS", SILENT: "REQUEST-EVIDENCE",
            ORPHANED: "REMOVE"}
    out = []
    for r in rows:
        v = r.get("verdict")
        if v == LIVE:
            continue
        # A DRIFTED gate is the one non-blast case that earns `high`: the stack
        # believes it is enforcing and it provably is not deployed, so EVERY
        # operation the gate covers is currently unguarded. That is verifiable,
        # not a heuristic.
        urgency = HIGH if v == DRIFTED else MEDIUM if v in (SILENT, ORPHANED) else LOW
        out.append(ProactiveSuggestion(
            type="orphan",
            description=f"{r.get('id')} is {v}: {r.get('desc', '')}",
            repo=repo_root.name,
            path=f"liveness:{r.get('surface', '')}/{r.get('id')}",
            verdict_hint=hint.get(v, "DEFER"),
            urgency=urgency,
            evidence=f"D1 liveness audit -> {v}: {r.get('evidence', '')}",
            detector="liveness"))
    return out


# --------------------------------------------------------------------------- #
# Detector 2 -- dead knowledge (composes D3 Recall-ROI).
# --------------------------------------------------------------------------- #
def detect_dead_knowledge(*, repo_root: Path, now=None, td=None) -> list:
    """KB items never recalled inside the window. Only FIRM candidates are
    emitted; PROVISIONAL means the corpus is too young to prove disuse, and
    publishing an unproven retirement is exactly the noise rule 1 forbids."""
    try:
        from modules.recall_roi.recall_roi import retirement_candidates
        r = retirement_candidates(td=td, now=now)
    except Exception:  # noqa: BLE001 -- fail-open
        return []
    meta = r.get("meta", {}) or {}
    if meta.get("error"):
        return []
    window = meta.get("window_days", "?")
    span = meta.get("corpus_span_days", "?")
    out = []
    for item in r.get("firm", []):
        out.append(ProactiveSuggestion(
            type="opportunity",
            description=f"KB item '{item}' has not been recalled once in {window}d",
            repo=repo_root.name,
            path=f"vault/specs/{item}",
            verdict_hint="REMOVE",
            urgency=LOW,
            evidence=(f"D3 recall-ROI: 0 injections in the {window}d window "
                      f"(corpus span {span}d -- sufficient history)"),
            detector="recall_roi"))
    return out


# --------------------------------------------------------------------------- #
# Detector 3 -- aged Owner residuals (composes D4 OWNER_QUEUE).
# --------------------------------------------------------------------------- #
def detect_owner_residuals(*, repo_root: Path, now=None, state_dir=None) -> list:
    """A residual that has aged past a week stopped being a queue item and became
    debt: either it still matters (execute it) or it does not (drop it). Silence
    is the one answer that is always wrong."""
    try:
        from modules.owner_queue.owner_queue import pending
        rows = pending(state_dir, min_age_h=RESIDUAL_DEBT_H, now=now)
    except Exception:  # noqa: BLE001 -- fail-open
        return []
    nz = now or datetime.now(timezone.utc)
    out = []
    for r in rows:
        age_h = _age_hours(r.get("created", ""), nz)
        if age_h is None:
            continue  # unparseable ts -> no evidence -> no suggestion (rule 1)
        abandoned = age_h >= RESIDUAL_ABANDONED_H
        out.append(ProactiveSuggestion(
            type="debt",
            description=(f"Owner residual pending {age_h / 24:.0f}d: "
                         f"{r.get('action', '')}"),
            repo=repo_root.name,
            path=f"owner_queue:{r.get('id', '')}",
            verdict_hint="REMOVE" if abandoned else "APPROVE-WITH-CONDITIONS",
            urgency=MEDIUM if abandoned else LOW,
            evidence=(f"D4 OWNER_QUEUE row {r.get('id', '')} created "
                      f"{r.get('created', '')} -- still pending "
                      f"({age_h / 24:.0f}d), command: {r.get('command', '')}"),
            detector="owner_queue"))
    return out


def _age_hours(ts_iso: str, now: datetime) -> float | None:
    try:
        t = datetime.fromisoformat(ts_iso)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return (now - t).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Detector 4 -- architecture decisions implicit in the code with no Decision
# Record (composes the DRK registry + the kernel's own blast-radius compute).
# --------------------------------------------------------------------------- #
_DOC_RE = re.compile(r'^\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', re.DOTALL)


def _module_docstring(init_py: Path) -> str:
    try:
        head = init_py.read_text(encoding="utf-8-sig", errors="replace")[:2000]
    except OSError:
        return ""
    m = _DOC_RE.search(head)
    return (m.group(1).strip() if m else "")[:600]


def detect_unrecorded_decisions(*, repo_root: Path, registry: Registry | None = None,
                                cap: int = MAX_UNRECORDED) -> list:
    """A module is a decision that was made. If no Decision Record cites it, the
    reasoning behind it exists nowhere -- which is the institutional-memory gap
    DRK-05 is about.

    Grounding: the module's own docstring is the evidence (a module with none is
    skipped -- nothing to cite). The kernel computes the blast radius from that
    docstring, so urgency is derived, never guessed. Only Tipo-B/C modules
    qualify: a trivially-reversible module did not need a recorded decision.
    Capped at `cap`, and the cap is reported by the caller.
    """
    modules_dir = repo_root / "modules"
    if not modules_dir.is_dir():
        return []
    reg = registry if registry is not None else Registry()
    try:
        records = reg.load()
    except Exception:  # noqa: BLE001 -- fail-open
        records = []
    blob = json.dumps(records).lower() if records else ""

    scored = []
    try:
        pkgs = sorted(p for p in modules_dir.iterdir() if p.is_dir())
    except OSError:
        return []
    for pkg in pkgs:
        if pkg.name in _MODULE_SKIP or pkg.name.startswith("."):
            continue
        init_py = pkg / "__init__.py"
        if not init_py.is_file():
            continue
        doc = _module_docstring(init_py)
        if not doc:
            continue  # no docstring -> no evidence -> no suggestion (rule 1)
        if pkg.name.lower() in blob:
            continue  # already cited by a Decision Record
        probe = DecisionObject(
            id=f"probe-{pkg.name}", statement=doc, problem="", options=[],
            chosen="", rationale="")
        rev = classify_reversibility(probe)
        if rev == Reversibility.A:
            continue  # trivially reversible -> no recorded decision was owed
        blast = compute_blast_radius(probe)
        scored.append((blast.get("magnitude", 0), pkg, doc, rev, blast))

    scored.sort(key=lambda t: (-t[0], t[1].name))
    out = []
    for magnitude, pkg, doc, rev, blast in scored[:cap]:
        rel = f"modules/{pkg.name}/"
        out.append(ProactiveSuggestion(
            type="decision_needed",
            description=(f"{rel} is a Tipo-{rev.value} module with no Decision "
                         f"Record -- the reasoning behind it is unrecorded"),
            repo=repo_root.name,
            path=rel,
            verdict_hint="REQUEST-EVIDENCE",
            urgency=_urgency_from_blast(magnitude),
            evidence=(f"{rel}__init__.py exists and its docstring touches "
                      f"{magnitude} blast surface(s) "
                      f"({', '.join(blast.get('surfaces', [])) or 'none'}); "
                      f"0 records in the decision registry name it "
                      f"({len(records)} records scanned)"),
            detector="unrecorded_decision",
            blast=blast))
    return out, len(scored)


# --------------------------------------------------------------------------- #
# The scan.
# --------------------------------------------------------------------------- #
def scan_repo(repo_root=None, *, now=None, state_dir=None, td=None,
              registry: Registry | None = None,
              cap: int = MAX_UNRECORDED) -> list:
    """Every detector, each independently fail-open. Returns suggestions sorted by
    urgency. An empty list is a valid result (nothing found is not an error) and
    an empty or non-existent repo yields [] rather than a raise."""
    root = Path(repo_root).resolve() if repo_root else PP_ROOT
    if not root.is_dir():
        return []
    suggestions: list = []
    truncated = 0

    # SCOPE. The D1 liveness registry and the D3 recall-ROI corpus describe THIS
    # pack's components and knowledge base -- they are PP-global ledgers, not
    # per-repo ones. Run against a foreign repo they would report PP's own silent
    # systems as findings ABOUT that repo: evidence that does not belong to the
    # thing being scanned. That is fabrication, not detection, so they run only
    # when the target IS the pack. A foreign repo gets the detector whose evidence
    # actually lives there (unrecorded decisions) plus the Owner-global residuals.
    detectors = [
        lambda: detect_owner_residuals(repo_root=root, now=now, state_dir=state_dir),
    ]
    if root == PP_ROOT:
        detectors[:0] = [
            lambda: detect_orphans(repo_root=root, now=now, state_dir=state_dir),
            lambda: detect_dead_knowledge(repo_root=root, now=now, td=td),
        ]

    for detector in detectors:
        try:
            suggestions.extend(detector() or [])
        except Exception:  # noqa: BLE001 -- fail-open per detector
            continue

    try:
        found, total = detect_unrecorded_decisions(
            repo_root=root, registry=registry, cap=cap)
        suggestions.extend(found)
        truncated = max(0, total - len(found))
    except Exception:  # noqa: BLE001 -- fail-open
        pass

    # Rule 1 enforced at the egress: an ungrounded suggestion never leaves here.
    suggestions = [s for s in suggestions if s.is_publishable()]
    suggestions.sort(key=lambda s: (_URGENCY_ORDER.get(s.urgency, 3), s.type, s.path))
    if truncated:
        # Rule 3: a cap is stated, never silent.
        suggestions.append(ProactiveSuggestion(
            type="opportunity",
            description=(f"{truncated} further unrecorded-decision candidate(s) "
                         f"were not listed (cap={cap})"),
            repo=root.name, path="modules/",
            verdict_hint="DEFER", urgency=LOW,
            evidence=f"scan cap reached: {truncated} candidate(s) beyond the top {cap}",
            detector="cap-notice"))
    return suggestions


# --------------------------------------------------------------------------- #
# Egress -- the report + the OWNER_QUEUE (existing channels only).
# --------------------------------------------------------------------------- #
def render_report(suggestions: list, *, now=None, repo: str = "") -> str:
    nz = now or datetime.now(timezone.utc)
    counts = {u: sum(1 for s in suggestions if s.urgency == u)
              for u in (HIGH, MEDIUM, LOW)}
    lines = [
        "# DRK Proactive Scan -- decisions the stack did not ask about",
        "",
        f"Generated {nz.isoformat()} | repo `{repo}` | {len(suggestions)} suggestion(s): "
        f"{counts[HIGH]} high, {counts[MEDIUM]} medium, {counts[LOW]} low.",
        "",
        "Every row cites a real path or ledger row. A finding without evidence is "
        "not published (T-DRK-PROACTIVE-NOISE-001). `high` requires a verifiable "
        "blast radius, not a heuristic.",
        "",
        "| Urgency | Type | Where | Hint | Finding | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for s in suggestions:
        desc = s.description.replace("|", "/")
        ev = s.evidence.replace("|", "/")
        lines.append(f"| {s.urgency.upper()} | {s.type} | `{s.path}` | "
                     f"{s.verdict_hint} | {desc} | {ev} |")
    if not suggestions:
        lines.append("| -- | -- | -- | -- | nothing found | clean scan |")
    lines += ["", "Zero findings is a valid scan."]
    return "\n".join(lines) + "\n"


def write_report(suggestions: list, *, repo_root=None, now=None,
                 out_path=None) -> Path | None:
    root = Path(repo_root).resolve() if repo_root else PP_ROOT
    nz = now or datetime.now(timezone.utc)
    path = Path(out_path) if out_path else (
        root / "vault" / "audits" / f"drk_proactive_{nz.strftime('%Y-%m-%d')}.md")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_report(suggestions, now=nz, repo=root.name),
                        encoding="utf-8")
        return path
    except OSError:  # fail-open: a scan that cannot write is still not an error
        return None


def publish(suggestions: list, *, state_dir=None, now=None) -> list:
    """High-urgency findings -> the EXISTING OWNER_QUEUE (D4). No new channel.
    owner_queue.append is idempotent by id, so a daily re-scan of an unfixed
    finding does not duplicate the row. Returns the appended ids."""
    high = [s for s in suggestions if s.urgency == HIGH and s.is_publishable()]
    if not high:
        return []
    try:
        from modules.owner_queue.owner_queue import append
    except Exception:  # noqa: BLE001 -- fail-open
        return []
    ids = []
    for s in high:
        try:
            rid = append(
                f"[DRK] {s.description}",
                f"python -m modules.decision_review.proactive_scanner --repo .",
                unblocks=s.verdict_hint,
                component=s.path,
                source="drk-proactive",
                state_dir=state_dir, now=now)
            if rid:
                ids.append(rid)
        except Exception:  # noqa: BLE001 -- fail-open per row
            continue
    return ids


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DRK proactive scanner")
    ap.add_argument("--repo", default=str(PP_ROOT))
    ap.add_argument("--write", action="store_true", help="write the audit report")
    ap.add_argument("--publish", action="store_true",
                    help="append high-urgency findings to the OWNER_QUEUE")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    suggestions = scan_repo(args.repo)
    if args.json:
        print(json.dumps([s.to_dict() for s in suggestions], ensure_ascii=False,
                         indent=1))
    else:
        print(render_report(suggestions, repo=Path(args.repo).resolve().name))
    if args.write:
        p = write_report(suggestions, repo_root=args.repo)
        if p:
            print(f"report -> {p}")
    if args.publish:
        ids = publish(suggestions)
        print(f"OWNER_QUEUE rows: {len(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
