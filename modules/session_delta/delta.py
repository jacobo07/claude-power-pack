#!/usr/bin/env python3
"""delta.py -- the producer the compound-learnings gather path never had.

`hooks/learning-sentinel.js::gatherLearningFiles()` reads
`<cwd>/.claude/cache/learnings/*.md` first and `memory/sessions/session_*.md`
second. Measured 2026-08-03: the first path has no writer anywhere in the
estate and the second holds zero files in this repo, so the sentinel returns []
on every Stop and exits at `if (files.length === 0) return;`. LEARNINGS_PENDING.md
is therefore never written, /cpp-compound is never auto-invoked, and the L3
proposal extractor never spawns -- a fully live three-stage consumer chain,
starved of input since it shipped.

This module writes that input. It is a PRODUCER, not a system:
`governance/KNOWLEDGE_CAPTURE_GOVERNANCE.md` rules that no fourth capture system
may exist, and names this exact hole under "Known gap, not fixed here".

Boundary vs fable_distillation (which owns per-repo session-delta capture):
FD-07 reads the PM-03 bus on a FRONTIER session's Stop and writes a deposits
ledger. This reads the working tree on EVERY session's Stop and writes one
markdown file in the schema compound-learnings already parses. Different input,
different cadence, different artifact, different consumer.

Answers five questions, each from a producer that already exists:
  capabilities touched     -- git status (same source tools/ads_sync.py reads)
  rules measured or not    -- rule_compiler.effect_harness.coverage()
  outputs without consumer -- liveness.reachability.scan() on the touched set
  gaps left open           -- owner_queue.pending()
  institutional proposal   -- the synthesis, escalated via owner_queue.append()

There is no rule-FIRING log in this estate (checked: trace-flusher.js ships
traces to a VPS, not rule fires), so the rules line reports UNMEASURED coverage
and names the absence. A named absence beats an invented signal.

    python -m modules.session_delta.delta --repo . --sid abc123
    python -m modules.session_delta.delta --repo . --sid abc123 --dry-run --json

Fail-open ABSOLUTE: any error yields an empty delta and a silent no-op;
main() ALWAYS exits 0. A reporting gate must never break the session it reports on.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Stop fires once per TURN, not once per session. The target path is derived
# from the sid, so every turn overwrites the same file and the count semantics
# learning-sentinel depends on (files, not writes) stay correct. This throttle
# only caps how often that rewrite costs a git+scan.
MIN_INTERVAL_S = float(os.environ.get("PP_SESSION_DELTA_MIN_INTERVAL_S", "300"))
# A truncated collection is reported in the artifact, never dropped silently.
MAX_PATHS = int(os.environ.get("PP_SESSION_DELTA_MAX_PATHS", "200"))
GIT_TIMEOUT_S = 10.0

# Rendering caps -- how many items a section names before it summarises the rest.
MAX_LISTED_CREATED = 20
MAX_LISTED_GAPS = 10
MAX_NAMED_ORPHANS = 3
SID_TAG_LEN = 8

LEARNINGS_REL = Path(".claude") / "cache" / "learnings"

_SURFACE_KINDS = (
    ("hooks/", "hook"),
    ("modules/", "module"),
    ("tools/", "tool"),
    ("commands/", "command"),
    ("agents/", "agent"),
    ("governance/", "governance"),
    ("vault/", "vault"),
    ("docs/", "docs"),
)


@dataclass
class SessionDelta:
    repo: str = ""
    sid: str = ""
    ts: str = ""
    created: list = field(default_factory=list)     # paths new this session
    modified: list = field(default_factory=list)    # paths changed this session
    truncated: int = 0                              # paths dropped by MAX_PATHS
    orphans: list = field(default_factory=list)     # touched modules, ORPHAN + undeclared
    rules_claimed: int = 0
    rules_unmeasured: int = 0
    open_gaps: list = field(default_factory=list)   # pending OWNER_QUEUE rows
    scanned_modules: bool = False                   # whether the reachability branch ran

    @property
    def touched(self) -> list:
        return self.created + self.modified

    def is_empty(self) -> bool:
        """No touched paths and no open gaps -> nothing to say. Silence is the
        correct output; a file written every session destroys the sentinel's
        `count > threshold` semantics."""
        return not self.touched and not self.open_gaps


# --------------------------------------------------------------------------- #
# producers
# --------------------------------------------------------------------------- #
def _git_exe() -> str | None:
    found = shutil.which("git")
    if found:
        return found
    for candidate in (r"C:\Program Files\Git\cmd\git.exe",
                      r"C:\Program Files (x86)\Git\cmd\git.exe"):
        if Path(candidate).is_file():
            return candidate
    return None


def git_status(repo: Path) -> tuple[list, list, int]:
    """(created, modified, truncated) from `git status --porcelain`.

    The working tree against HEAD is the honest session window: a Stop hook has
    no session-start ref, and the tree is cumulative, so the last write of a
    session is also its most complete one.

    `-uall` is load-bearing, not a preference: plain --porcelain collapses an
    untracked directory to a single `modules/pkg/` row, so a brand-new module
    package -- the exact case the orphan check exists for -- would never reach
    `_touched_module_units`."""
    exe = _git_exe()
    if not exe:
        return [], [], 0
    try:
        proc = subprocess.run(
            [exe, "-C", str(repo), "status", "--porcelain", "-uall"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_S,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return [], [], 0
    if proc.returncode != 0:
        return [], [], 0

    created, modified = [], []
    for line in (proc.stdout or "").splitlines():
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:].strip().strip('"')
        if " -> " in path:                      # rename: keep the destination
            path = path.split(" -> ", 1)[1].strip().strip('"')
        if not path:
            continue
        (created if ("A" in code or "?" in code) else modified).append(path)

    total = len(created) + len(modified)
    truncated = max(0, total - MAX_PATHS)
    if truncated:
        keep_created = created[:MAX_PATHS]
        keep_modified = modified[:max(0, MAX_PATHS - len(keep_created))]
        created, modified = keep_created, keep_modified
    return created, modified, truncated


def _touched_module_units(paths) -> set:
    """`modules/<pkg>/<name>.py` -> the `<pkg>/<name>` unit reachability scores."""
    units = set()
    for p in paths:
        norm = p.replace("\\", "/")
        if not norm.startswith("modules/") or not norm.endswith(".py"):
            continue
        unit = norm[len("modules/"):-len(".py")]
        if unit:
            units.add(unit)
    return units


def orphan_units(repo: Path, units) -> list:
    """Touched modules that are unreachable AND undeclared -- the Liveness
    Standard's own gate condition, applied to this session's own output."""
    if not units:
        return []
    try:
        from modules.liveness import reachability as rx
    except ImportError:
        return []
    try:
        registry = rx.load_registry(repo)
        declared = set(registry.get("modules", {}) or {})
        rows = rx.scan(repo, registry)
    except Exception:  # noqa: BLE001 -- fail-open
        return []
    out = []
    for row in rows:
        unit = row.get("unit", "")
        if unit in units and row.get("status") == rx.ORPHAN and unit not in declared:
            out.append(unit)
    return sorted(out)


def rule_coverage() -> tuple[int, int]:
    """(claimed, unmeasured) from the effect harness. No probes are executed."""
    try:
        from modules.rule_compiler.effect_harness import coverage
        cov = coverage()
    except Exception:  # noqa: BLE001 -- fail-open
        return 0, 0
    unmeasured = cov.get("unmeasured")
    return len(cov.get("claimed") or []), (len(unmeasured) if unmeasured else 0)


def open_gaps(state_dir=None) -> list:
    """Pending OWNER_QUEUE rows -- gaps recorded and not yet closed."""
    try:
        from modules.owner_queue import owner_queue as oq
        return [r.get("action", "") for r in oq.pending(state_dir) if r.get("action")]
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# collect / render / escalate
# --------------------------------------------------------------------------- #
def collect(repo, sid: str = "", *, state_dir=None, now=None) -> SessionDelta:
    """Build the delta from the producers above. Fail-open -> an empty delta."""
    d = SessionDelta(sid=sid or "")
    try:
        repo_path = Path(repo).resolve()
        d.repo = str(repo_path)
        d.ts = (now or datetime.now(timezone.utc)).isoformat()
        d.created, d.modified, d.truncated = git_status(repo_path)
        units = _touched_module_units(d.touched)
        if units:
            d.scanned_modules = True
            d.orphans = orphan_units(repo_path, units)
            d.rules_claimed, d.rules_unmeasured = rule_coverage()
        d.open_gaps = open_gaps(state_dir)
    except Exception:  # noqa: BLE001 -- fail-open
        return d
    return d


def _by_kind(paths) -> dict:
    counts: dict = {}
    for p in paths:
        norm = p.replace("\\", "/")
        kind = next((k for prefix, k in _SURFACE_KINDS if norm.startswith(prefix)), "other")
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def _kind_line(counts: dict) -> str:
    def _plural(kind: str, n: int) -> str:
        return kind if (n == 1 or kind.endswith("s")) else kind + "s"
    return ", ".join(f"{n} {_plural(k, n)}"
                     for k, n in sorted(counts.items(), key=lambda kv: -kv[1])) or "none"


def _by_signal(paths) -> list:
    """Paths a human acts on first. `docs/` is machine-generated by ads_sync and
    `vault/` is mostly append-only record, so both sink below the surfaces a
    reader must actually decide about -- the artifact has to be actionable, and
    twenty auto-generated doc stubs at the top is narration."""
    rank = {"hook": 0, "module": 1, "tool": 2, "command": 3, "agent": 4,
            "governance": 5, "other": 6, "vault": 7, "docs": 8}
    kind_of = {}
    for p in paths:
        norm = p.replace("\\", "/")
        kind_of[p] = next((k for prefix, k in _SURFACE_KINDS if norm.startswith(prefix)), "other")
    return sorted(paths, key=lambda p: (rank.get(kind_of[p], 6), p))


def render(d: SessionDelta) -> str:
    """Markdown in the schema learning-sentinel's HEADER_PROBE_RE matches, so the
    artifact is recognised on the primary path AND the header-filtered fallback."""
    repo_name = Path(d.repo).name if d.repo else "?"
    lines = [
        f"# Session Delta -- {repo_name} -- {d.ts}",
        "",
        f"**Session:** `{d.sid or 'unknown'}`  ",
        f"**Repo:** `{d.repo}`  ",
        f"**Window:** working tree vs HEAD -- "
        f"{len(d.created)} new, {len(d.modified)} changed"
        + (f" ({d.truncated} more not listed, cap {MAX_PATHS})" if d.truncated else ""),
        "",
        "## Patterns",
        "",
        f"- Surfaces touched: {_kind_line(_by_kind(d.touched))}.",
    ]

    if d.scanned_modules:
        lines.append(
            f"- Rule effects: {d.rules_claimed} rule(s) carry a runnable effect claim, "
            f"{d.rules_unmeasured} carry none. This estate has no rule-FIRING log, so "
            f"which rules were *exercised* this session is not observable -- only which "
            f"are measurable at all."
        )
    else:
        lines.append(
            "- No module changed this session, so the reachability and rule-coverage "
            "checks did not run."
        )

    lines += ["", "## What Worked", ""]
    if d.created:
        ranked = _by_signal(d.created)
        lines += [f"- Landed `{p}`" for p in ranked[:MAX_LISTED_CREATED]]
        rest = len(ranked) - MAX_LISTED_CREATED
        if rest > 0:
            lines.append(f"- ...and {rest} more new path(s), lower-signal first-dropped: "
                         f"{_kind_line(_by_kind(ranked[MAX_LISTED_CREATED:]))}.")
    if d.modified:
        lines.append(f"- Changed {len(d.modified)} existing path(s).")
    if not d.touched:
        lines.append("- No file changed; this delta exists for its open gaps.")

    lines += ["", "## What Failed", ""]
    failed = False
    if d.orphans:
        failed = True
        for unit in d.orphans:
            lines.append(
                f"- `modules/{unit}` landed unreachable from any live surface and is "
                f"absent from `vault/liveness/reachability_registry.json` -- it fails "
                f"the Liveness Standard gate. Verdict owed: WIRE, DECLARE, or DELETE."
            )
    if d.open_gaps:
        failed = True
        lines.append(f"- {len(d.open_gaps)} OWNER_QUEUE residual(s) still pending:")
        lines += [f"  - {g}" for g in d.open_gaps[:MAX_LISTED_GAPS]]
        if len(d.open_gaps) > MAX_LISTED_GAPS:
            lines.append(f"  - ...and {len(d.open_gaps) - MAX_LISTED_GAPS} more.")
    if d.truncated:
        failed = True
        lines.append(
            f"- {d.truncated} changed path(s) exceeded the {MAX_PATHS}-path cap and are "
            f"not represented above."
        )
    if not failed:
        lines.append("- Nothing measured as failing: no orphaned output, no open residual.")

    lines += ["", takeaway(d), ""]
    return "\n".join(lines)


def takeaway(d: SessionDelta) -> str:
    """The single institutional change this session argues for."""
    if d.orphans:
        named = ", ".join(d.orphans[:MAX_NAMED_ORPHANS])
        more = ", ..." if len(d.orphans) > MAX_NAMED_ORPHANS else ""
        return (f"**Takeaway:** {len(d.orphans)} module(s) shipped this session with no "
                f"live consumer ({named}{more}). Shipping is not wiring -- give each a "
                f"WIRE / DECLARE / DELETE verdict before the next ship.")
    if d.open_gaps and not d.touched:
        return (f"**Takeaway:** this session changed nothing and left {len(d.open_gaps)} "
                f"residual(s) open. The queue is the backlog; drain it or re-scope it.")
    if d.open_gaps:
        return (f"**Takeaway:** work shipped while {len(d.open_gaps)} residual(s) stayed "
                f"open. New surface arriving faster than old surface is activated is the "
                f"debt shape to watch.")
    return ("**Takeaway:** the session's output is fully reachable and no residual is "
            "open. The measurable institutional delta is zero.")


def escalate(d: SessionDelta, *, state_dir=None) -> list:
    """Route the one actionable finding to a human decision surface. An orphaned
    output is the only condition here that fails an existing gate; everything else
    is reporting and stays in the artifact."""
    ids = []
    if not d.orphans:
        return ids
    try:
        from modules.owner_queue import owner_queue as oq
    except ImportError:
        return ids
    for unit in d.orphans:
        try:
            ids.append(oq.append(
                f"Liveness verdict owed for modules/{unit} (shipped unreachable, undeclared)",
                f"python modules/liveness/reachability.py  # then WIRE, DECLARE in "
                f"vault/liveness/reachability_registry.json, or DELETE",
                unblocks=f"modules/{unit}",
                component=unit,
                source="session_delta",
                state_dir=state_dir,
            ))
        except Exception:  # noqa: BLE001 -- fail-open
            continue
    return ids


def target_path(repo, sid: str, *, now=None) -> Path:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    tag = (sid or "nosid").replace("/", "-")[:SID_TAG_LEN] or "nosid"
    return Path(repo) / LEARNINGS_REL / f"{stamp}_{tag}.md"


def _throttled(path: Path, *, now=None, min_interval_s: float = MIN_INTERVAL_S) -> bool:
    """True when this file was rewritten too recently to be worth recomputing."""
    if min_interval_s <= 0:
        return False
    try:
        age = (now or datetime.now(timezone.utc)).timestamp() - path.stat().st_mtime
    except OSError:
        return False
    return age < min_interval_s


def run(repo, sid: str = "", *, dry_run: bool = False, state_dir=None, now=None,
        min_interval_s: float = MIN_INTERVAL_S) -> dict:
    """Collect, write when non-empty, escalate. Never raises."""
    result = {"written": None, "escalated": [], "skipped": None, "delta": None}
    try:
        path = target_path(repo, sid, now=now)
        if not dry_run and _throttled(path, now=now, min_interval_s=min_interval_s):
            result["skipped"] = "throttled"
            return result
        d = collect(repo, sid, state_dir=state_dir, now=now)
        result["delta"] = asdict(d)
        if d.is_empty():
            result["skipped"] = "empty-delta"
            return result
        body = render(d)
        if dry_run:
            result["skipped"] = "dry-run"
            result["body"] = body
            return result
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        result["written"] = str(path)
        result["escalated"] = escalate(d, state_dir=state_dir)
    except Exception:  # noqa: BLE001 -- fail-open
        return result
    return result


def main(argv: list | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Session Delta Gate -- post-session producer")
    ap.add_argument("--repo", default=".", help="repo root (the Stop payload's cwd)")
    ap.add_argument("--sid", default="", help="session id")
    ap.add_argument("--dry-run", action="store_true", help="render, write nothing")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-interval-s", type=float, default=MIN_INTERVAL_S)
    ap.add_argument("--state-dir", default=None,
                    help="OWNER_QUEUE state dir (default ~/.claude/state); set it to "
                         "keep a test run off the real queue")
    args = ap.parse_args(argv)
    try:
        res = run(args.repo, args.sid, dry_run=args.dry_run,
                  state_dir=args.state_dir, min_interval_s=args.min_interval_s)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
        elif res.get("written"):
            print(f"[session-delta] wrote {res['written']}"
                  + (f" (+{len(res['escalated'])} OWNER_QUEUE row(s))"
                     if res["escalated"] else ""))
        elif res.get("body"):
            print(res["body"])
        else:
            print(f"[session-delta] no-op ({res.get('skipped') or 'nothing to report'})")
    except Exception:  # noqa: BLE001 -- fail-open
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
