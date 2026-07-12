#!/usr/bin/env python3
"""liveness_ledger.py -- D1: the post-ship liveness monitor (SCS strategic-gaps).

The ecosystem verifies at CONSTRUCTION time (V-gates, hermetic x3, done-gates) and
is blind POST-SHIP. A V-gate proves code works WHEN INVOKED; nothing proves anything
invokes it. `built != wired` is therefore a recurring CLASS (dispatcher drift, the
PM-03 producer-without-consumer bus, orphan modules/fields, the FD then FIOS
Copy-Item last-miles) -- each rediscovered ad-hoc, sessions later, as a fresh lesson.

The Liveness Ledger closes the loop *ship -> is it alive?*. Every wired component
declares a liveness contract (its surface + a deterministic evidence probe); the
auditor runs the probes daily and emits one verdict per component:

  LIVE               -- the probe found RECENT evidence the system ran end-to-end.
  WIRED-BUT-SILENT   -- wired/registered but produced no recent evidence (idle, or a
                        broken producer, or a producer with no consumer -- the PM-03
                        bus is the canonical instance: written every session, read by
                        nobody).
  DRIFTED            -- canonical (repo) and the live surface (~/.claude/hooks)
                        disagree by hash (the classic dispatcher drift).
  ORPHANED           -- an artifact exists on the live surface with NO source in the
                        repo (dead code in ~/.claude/hooks).

Every probe is pure filesystem + hash + CO-12-signal-recency -- no model, no network.
Fail-open ABSOLUTE: any probe error yields a verdict of UNKNOWN with the error noted,
never an exception (a monitor that breaks the session it monitors is worse than none).

D1 is the base the companion systems ride: D4 (OWNER_QUEUE) auto-clears a queue row
when its component's verdict flips to LIVE; D5's scheduled-task health becomes a row
so a silent task failure can never re-normalize.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Verdict vocabulary (single source of truth).
LIVE = "LIVE"
SILENT = "WIRED-BUT-SILENT"
DRIFTED = "DRIFTED"
ORPHANED = "ORPHANED"
UNKNOWN = "UNKNOWN"
_NON_LIVE = (SILENT, DRIFTED, ORPHANED, UNKNOWN)

# Default freshness window for signal/mtime probes, in hours. Env-tunable.
DEFAULT_MAX_AGE_H = float(os.environ.get("PP_LIVENESS_MAX_AGE_H", "36"))


def _repo_root() -> Path:
    return _PP_ROOT


def _live_hooks_dir() -> Path:
    return Path.home() / ".claude" / "hooks"


def _sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _age_hours(ts_iso: str, now: datetime) -> float | None:
    """Hours between an ISO timestamp and now. Fail-open -> None."""
    try:
        t = datetime.fromisoformat(ts_iso)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return (now - t).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# The registry: every wired component's liveness contract. Seed rows cover the
# five surfaces the strategic audit named; new wired components add a row here
# (the done-gate amendment: ship + registry row, same class as "new hook needs a
# Copy-Item doc").
# --------------------------------------------------------------------------- #
def default_registry() -> list[dict]:
    return [
        {
            "id": "hook-dispatcher",
            "surface": "hooks-dir",
            "desc": "canonical hook-dispatcher.js vs the live ~/.claude/hooks copy",
            "probe": {"type": "hash-drift", "name": "hook-dispatcher.js",
                      "repo_rel": "hooks/hook-dispatcher.js"},
        },
        {
            "id": "pm-03-bus",
            "surface": "pm-bus",
            "desc": "PM-03 findings bus -- written every session, consumer wiring pending",
            "probe": {"type": "pm-bus",
                      "producer_glob": "findings_bus_*.jsonl",
                      "consume_signal": "pm03_consume"},
        },
        {
            "id": "fios-token-irr",
            "surface": "stop-chain",
            "desc": "FIOS token_irr Stop-chain -- emits FIOS IRR + feeds CO-12",
            "probe": {"type": "co12-signal", "kind": "fios_token_irr"},
        },
        {
            "id": "fd-07-flywheel",
            "surface": "stop-chain",
            "desc": "FD-07 flywheel Stop hook -- distils frontier deltas each turn",
            "probe": {"type": "co12-signal", "kind": "fd_flywheel_turn"},
        },
        {
            "id": "kclaude-preflight",
            "surface": "kclaude",
            "desc": "FIOS session_compiler preflight -- writes SESSION_ZERO on a frontier launch",
            "probe": {"type": "file-mtime",
                      "glob": "vault/sessions/SESSION_ZERO_*.md",
                      "root": "repo"},
        },
        {
            "id": "drk-kernel",
            "surface": "decision-registry",
            "desc": "DRK review kernel -- every reviewed decision appends a record",
            "probe": {"type": "file-mtime",
                      "glob": "vault/decision_registry/records.jsonl",
                      "root": "repo"},
        },
        {
            "id": "drk-proactive",
            "surface": "audits",
            "desc": "DRK proactive scanner -- daily sweep proposing decisions nobody asked about",
            "probe": {"type": "file-mtime",
                      "glob": "vault/audits/drk_proactive_*.md",
                      "root": "repo"},
        },
        {
            "id": "dfp-necessity-ledger",
            "surface": "decision-registry",
            "desc": ("DFP necessity ledger -- every knowledge-first decision appends a "
                     "record carrying a PREDICTION. No records => the protocol is "
                     "UNMEASURED, and DFP-05 has nothing to grade (INV-3)."),
            "probe": {"type": "file-mtime",
                      "glob": "vault/dataset_first/necessity_ledger.jsonl",
                      "root": "repo"},
        },
    ]


# --------------------------------------------------------------------------- #
# Probes. Each returns (verdict, evidence_str). Fail-open -> (UNKNOWN, "...").
# --------------------------------------------------------------------------- #
def _probe_hash_drift(spec: dict, *, repo_root: Path, hooks_live_dir: Path) -> tuple[str, str]:
    name = spec.get("name", "")
    repo_file = repo_root / spec.get("repo_rel", "")
    live_file = hooks_live_dir / name
    repo_exists, live_exists = repo_file.is_file(), live_file.is_file()
    if not repo_exists and not live_exists:
        return UNKNOWN, f"neither repo nor live {name} exists"
    if repo_exists and not live_exists:
        return DRIFTED, f"canonical present, live ~/.claude/hooks/{name} MISSING (not deployed)"
    if live_exists and not repo_exists:
        return ORPHANED, f"live {name} present, NO repo source ({spec.get('repo_rel')})"
    rh, lh = _sha256(repo_file), _sha256(live_file)
    if rh is None or lh is None:
        return UNKNOWN, "hash read failed"
    if rh == lh:
        return LIVE, f"in sync (sha256 {rh[:12]})"
    return DRIFTED, f"HASH MISMATCH repo {rh[:12]} != live {lh[:12]} -- Copy-Item pending"


def _probe_co12_signal(spec: dict, *, signals: list, now: datetime,
                       max_age_h: float) -> tuple[str, str]:
    kind = spec.get("kind", "")
    matches = [s for s in signals if s.get("kind") == kind]
    if not matches:
        return SILENT, f"no '{kind}' signal ever recorded (wired, never fired)"
    ages = [a for a in (_age_hours(s.get("ts", ""), now) for s in matches) if a is not None]
    if not ages:
        return SILENT, f"{len(matches)} '{kind}' signals but no parseable ts"
    freshest = min(ages)
    if freshest <= max_age_h:
        return LIVE, f"{len(matches)} signals, freshest {freshest:.1f}h ago (<= {max_age_h:.0f}h)"
    return SILENT, f"{len(matches)} signals but freshest {freshest:.1f}h ago (> {max_age_h:.0f}h -- gone quiet)"


def _probe_pm_bus(spec: dict, *, mesh_dir: Path, signals: list, now: datetime,
                  max_age_h: float) -> tuple[str, str]:
    """The producer-without-consumer probe. LIVE only if a consume signal is
    recent; producer-present-but-no-consumer is the WIRED-BUT-SILENT demonstration."""
    consume_kind = spec.get("consume_signal", "pm03_consume")
    consumes = [s for s in signals if s.get("kind") == consume_kind]
    fresh_consume = any((a is not None and a <= max_age_h)
                        for a in (_age_hours(s.get("ts", ""), now) for s in consumes))
    try:
        producers = list(mesh_dir.glob(spec.get("producer_glob", "*.jsonl"))) if mesh_dir.is_dir() else []
    except OSError:
        producers = []
    if fresh_consume:
        return LIVE, f"{len(producers)} producer file(s), consume signal '{consume_kind}' recent"
    if producers:
        return SILENT, (f"{len(producers)} producer file(s); consumer is the SessionStart "
                        f"hub read but emits no '{consume_kind}' signal -- consumption unmeasured")
    return ORPHANED, "no producer files and no consumer -- bus inert"


def _probe_file_mtime(spec: dict, *, repo_root: Path, now: datetime,
                      max_age_h: float) -> tuple[str, str]:
    base = repo_root if spec.get("root") == "repo" else Path.home()
    try:
        hits = sorted(base.glob(spec.get("glob", "")), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        hits = []
    if not hits:
        return SILENT, f"no file matching {spec.get('glob')} (surface produced nothing)"
    newest = hits[0]
    try:
        mt = datetime.fromtimestamp(newest.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return UNKNOWN, "mtime read failed"
    age = (now - mt).total_seconds() / 3600.0
    if age <= max_age_h:
        return LIVE, f"{newest.name} {age:.1f}h ago (<= {max_age_h:.0f}h)"
    return SILENT, f"newest {newest.name} {age:.1f}h ago (> {max_age_h:.0f}h -- quiet)"


# --------------------------------------------------------------------------- #
# Auditor.
# --------------------------------------------------------------------------- #
def audit(registry=None, *, repo_root=None, hooks_live_dir=None, mesh_dir=None,
          state_dir=None, now=None, max_age_h: float = DEFAULT_MAX_AGE_H) -> list[dict]:
    """Run every registry probe, return one verdict row per component. Fail-open
    per-row: a probe that raises yields UNKNOWN, never aborts the audit."""
    reg = registry if registry is not None else default_registry()
    repo_root = Path(repo_root) if repo_root else _repo_root()
    hooks_live_dir = Path(hooks_live_dir) if hooks_live_dir else _live_hooks_dir()
    mesh_dir = Path(mesh_dir) if mesh_dir else (Path.home() / ".claude" / "state" / "parallel_mesh")
    now = now or datetime.now(timezone.utc)
    try:
        from modules.cognitive_os.co_12_telemetry import load_signals
        signals = load_signals(state_dir=state_dir)
    except Exception:  # noqa: BLE001 -- fail-open
        signals = []
    rows = []
    for entry in reg:
        pid = entry.get("id", "?")
        spec = entry.get("probe", {}) or {}
        ptype = spec.get("type", "")
        try:
            if ptype == "hash-drift":
                verdict, ev = _probe_hash_drift(spec, repo_root=repo_root, hooks_live_dir=hooks_live_dir)
            elif ptype == "co12-signal":
                verdict, ev = _probe_co12_signal(spec, signals=signals, now=now, max_age_h=max_age_h)
            elif ptype == "pm-bus":
                verdict, ev = _probe_pm_bus(spec, mesh_dir=mesh_dir, signals=signals, now=now, max_age_h=max_age_h)
            elif ptype == "file-mtime":
                verdict, ev = _probe_file_mtime(spec, repo_root=repo_root, now=now, max_age_h=max_age_h)
            else:
                verdict, ev = UNKNOWN, f"unknown probe type '{ptype}'"
        except Exception as e:  # noqa: BLE001 -- fail-open per row
            verdict, ev = UNKNOWN, f"probe error (fail-open): {e}"
        rows.append({"id": pid, "surface": entry.get("surface", ""),
                     "desc": entry.get("desc", ""), "verdict": verdict, "evidence": ev})
    return rows


def _report_md(rows: list[dict], *, now: datetime) -> str:
    counts = {v: sum(1 for r in rows if r["verdict"] == v)
              for v in (LIVE, SILENT, DRIFTED, ORPHANED, UNKNOWN)}
    non_live = sum(counts[v] for v in _NON_LIVE)
    lines = [
        "# Liveness Ledger -- post-ship verdict (D1)",
        "",
        f"Generated {now.isoformat()} | {len(rows)} components | "
        f"{counts[LIVE]} LIVE, {non_live} non-LIVE "
        f"({counts[SILENT]} silent, {counts[DRIFTED]} drifted, "
        f"{counts[ORPHANED]} orphaned, {counts[UNKNOWN]} unknown).",
        "",
        "Verdict class: LIVE = recent end-to-end evidence; WIRED-BUT-SILENT = wired "
        "but no recent evidence (idle / broken producer / producer-without-consumer); "
        "DRIFTED = repo vs ~/.claude/hooks hash mismatch; ORPHANED = live artifact "
        "with no repo source.",
        "",
        "| Component | Surface | Verdict | Evidence |",
        "|---|---|---|---|",
    ]
    order = {LIVE: 3, SILENT: 1, DRIFTED: 0, ORPHANED: 0, UNKNOWN: 2}
    for r in sorted(rows, key=lambda r: (order.get(r["verdict"], 5), r["id"])):
        ev = r["evidence"].replace("|", "\\|")
        lines.append(f"| `{r['id']}` | {r['surface']} | **{r['verdict']}** | {ev} |")
    lines += ["",
              "Non-LIVE rows are the ship->silence gap made visible. A row here is the "
              "authoritative liveness fact -- not a lesson rediscovered sessions later.",
              ""]
    return "\n".join(lines)


def write_report(rows=None, *, out_path=None, now=None, **audit_kw) -> Path:
    """Audit (unless rows supplied) and write the markdown report. Returns the
    path written. Fail-open: a write error still returns the intended path."""
    now = now or datetime.now(timezone.utc)
    if rows is None:
        rows = audit(now=now, **audit_kw)
    # D1 -> D4 composition: a component now LIVE auto-clears its OWNER_QUEUE
    # residual, so the Owner never bookkeeps completion. Fail-open: a queue
    # error never disturbs report generation.
    try:
        from modules.owner_queue.owner_queue import autoclear
        autoclear([r["id"] for r in rows if r.get("verdict") == LIVE], now=now)
    except Exception:  # noqa: BLE001 -- fail-open
        pass
    out = Path(out_path) if out_path else (_repo_root() / "vault" / "audits" / "liveness_report.md")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_report_md(rows, now=now), encoding="utf-8")
    except OSError:
        pass
    return out


def summary_line(rows=None, **audit_kw) -> str:
    """One-line SessionStart advisory. Fail-open -> a benign line."""
    try:
        rows = rows if rows is not None else audit(**audit_kw)
        non_live = [r for r in rows if r["verdict"] in _NON_LIVE]
        if not non_live:
            return f"Liveness: {len(rows)}/{len(rows)} LIVE."
        worst = ", ".join(f"{r['id']}={r['verdict']}" for r in non_live[:4])
        return f"Liveness: {len(rows) - len(non_live)}/{len(rows)} LIVE | attention: {worst}"
    except Exception:  # noqa: BLE001
        return "Liveness: probe unavailable (fail-open)."


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="D1 Liveness Ledger")
    ap.add_argument("--report", action="store_true", help="write vault/audits/liveness_report.md")
    ap.add_argument("--json", action="store_true", help="print verdict rows as JSON")
    ap.add_argument("--summary", action="store_true", help="print the SessionStart one-liner")
    ap.add_argument("--max-age-h", type=float, default=DEFAULT_MAX_AGE_H)
    args = ap.parse_args(argv)
    rows = audit(max_age_h=args.max_age_h)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if args.summary:
        print(summary_line(rows))
        return 0
    if args.report:
        p = write_report(rows=rows)
        print(f"wrote {p}")
    for r in rows:
        print(f"  [{r['verdict']:16s}] {r['id']:20s} {r['evidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
