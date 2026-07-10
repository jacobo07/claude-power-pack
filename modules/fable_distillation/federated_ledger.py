#!/usr/bin/env python3
"""federated_ledger.py -- D2: make the FD flywheel compound across ALL repos.

PREMISE CORRECTION (the strategic audit said "the FD-07 ledger exists only in PP" --
that is imprecise). The deposit ledger is ALREADY per-repo: fd_07_flywheel writes
`deposits_<repo-slug>.jsonl`, and token_irr reads per-repo. KobiiCraft / TUA-X show
FDI 0 not because the ledger is PP-only, but because their per-repo ledger is EMPTY
-- their frontier sessions deposit nothing (a real declared session has never mined
findings there). So D2 does NOT re-create per-repo ledgers (they exist); it delivers
the three things that are genuinely missing:

  1. aggregate()          -- the cross-repo ROLLUP over every deposits_<slug>.jsonl
                             (per-repo asset/FDI + a global total). The per-repo view
                             exists; the global one did not.
  2. propagate_critical() -- mirror the source repo's transversal PR-/HR- doctrine
                             into each subscriber repo's own UKDL_PROPAGATED.md
                             (append-only, hash-idempotent, never touches their
                             curated files). A CRITICAL rule sealed in PP now reaches
                             the repos where the same bug would otherwise recur.
  3. fdi_advisory()       -- at a NON-PP frontier Stop with 0 deposits, nudge the
                             Owner to declare PP_SESSION_OBJECTIVE so that session
                             actually mines a portable asset (wired into token_irr).

Fail-open ABSOLUTE everywhere. Propagation is one-way (source -> subscribers),
append-only, and writes only a dedicated file it owns -- it can never corrupt a
subscriber's hand-curated knowledge base.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# The FD-07 flywheel's per-repo deposit ledgers live here (reused, not forked).
def _fd_state_dir(state_dir=None) -> Path:
    return Path(state_dir) if state_dir else (
        Path.home() / ".claude" / "state" / "fable_distillation")


def _slug(repo: str) -> str:
    """Same encoding fd_07_flywheel._deposits_path uses (repo path -> filename slug)."""
    return re.sub(r"[^a-zA-Z0-9]", "-", repo or "")


def _is_pp_repo(repo: str) -> bool:
    return "claude-power-pack" in (repo or "")


# --------------------------------------------------------------------------- #
# 1. Cross-repo aggregate over the existing per-repo deposit ledgers.
# --------------------------------------------------------------------------- #
def _read_deposits(path: Path) -> list:
    out = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
    except OSError:
        return []
    return out


def aggregate(state_dir=None) -> dict:
    """Roll up every deposits_<slug>.jsonl into a per-repo + global view. Fail-open."""
    try:
        d = _fd_state_dir(state_dir)
        rows = []
        total_assets = total_frontier_only = 0
        for fp in sorted(glob.glob(str(d / "deposits_*.jsonl"))):
            slug = Path(fp).stem[len("deposits_"):]
            deps = _read_deposits(Path(fp))
            assets = len(deps)
            frontier_only = sum(1 for x in deps
                                if x.get("portability_target") == "frontier-only")
            rows.append({
                "slug": slug, "assets": assets, "frontier_only": frontier_only,
                "fdi": round(frontier_only / assets, 3) if assets else 0.0,
                "net_portable": assets - frontier_only,
            })
            total_assets += assets
            total_frontier_only += frontier_only
        return {
            "repos": len(rows), "per_repo": rows,
            "global": {
                "total_assets": total_assets,
                "total_frontier_only": total_frontier_only,
                "global_fdi": (round(total_frontier_only / total_assets, 3)
                               if total_assets else 0.0),
                "net_portable": total_assets - total_frontier_only,
            },
        }
    except Exception:  # noqa: BLE001 -- fail-open
        return {"repos": 0, "per_repo": [], "global": {"total_assets": 0}}


# --------------------------------------------------------------------------- #
# 2. CRITICAL/transversal lesson propagation (source -> subscribers).
# --------------------------------------------------------------------------- #
# A propagatable block: a `### ...PR-<id>` process rule or `### ...HR-<id>` hard
# rule header and its body (transversal by definition). Repo-specific traps (T-*)
# are intentionally NOT propagated -- they are local, not universal.
_PROP_HEADER_RE = re.compile(r"^###\s+.*\b((?:PR|HR)-[A-Z0-9][A-Z0-9-]*)\b", re.M)
_MARK_RE = re.compile(r"<!--\s*fd-prop:([^:]+):([0-9a-f]{12})\s*-->")


def _ukdl_path(repo_root) -> Path:
    return Path(repo_root) / "vault" / "knowledge_base" / "ukdl-universal.md"


def _propagated_path(repo_root) -> Path:
    return Path(repo_root) / "vault" / "knowledge_base" / "UKDL_PROPAGATED.md"


def extract_transversal_blocks(text: str) -> list:
    """Return [{id, hash, body}] for each PR-/HR- section in a UKDL doc. Each block
    is bounded by the NEXT `### ` header of ANY kind, so an intervening non-PROP
    section (e.g. a repo-local T- trap) is never swept into a PROP block's body."""
    blocks = []
    heads = list(re.finditer(r"^###\s+(.+)$", text, re.M))
    for i, m in enumerate(heads):
        pm = re.search(r"\b((?:PR|HR)-[A-Z0-9][A-Z0-9-]*)\b", m.group(1))
        if not pm:
            continue
        start = m.start()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[start:end].rstrip()
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
        blocks.append({"id": pm.group(1), "hash": h, "body": body})
    return blocks


def _existing_ids(propagated_text: str) -> set:
    return {m.group(1) for m in _MARK_RE.finditer(propagated_text)}


def propagate_critical(source_repo_root, target_repo_roots, *, now=None) -> dict:
    """Mirror the source repo's PR-/HR- blocks into each target's UKDL_PROPAGATED.md
    (append-only, idempotent by id). Never touches a target's curated files.
    Returns {target_slug: {"added": n, "skipped": n}}. Fail-open per target."""
    result = {}
    try:
        src = _ukdl_path(source_repo_root)
        if not src.is_file():
            return {"error": "source ukdl missing"}
        blocks = extract_transversal_blocks(src.read_text(encoding="utf-8-sig",
                                                           errors="replace"))
        stamp = (now or datetime.now(timezone.utc)).isoformat()
        for troot in target_repo_roots:
            slug = _slug(str(troot))
            try:
                pp = _propagated_path(troot)
                if not pp.parent.is_dir():
                    result[slug] = {"added": 0, "skipped": 0, "note": "no vault/knowledge_base"}
                    continue
                prior = pp.read_text(encoding="utf-8-sig", errors="replace") if pp.is_file() else ""
                have = _existing_ids(prior)
                new_chunks, added, skipped = [], 0, 0
                for b in blocks:
                    if b["id"] in have:
                        skipped += 1
                        continue
                    new_chunks.append(
                        f"<!-- fd-prop:{b['id']}:{b['hash']} -->\n{b['body']}\n")
                    added += 1
                if added:
                    header = ("# UKDL_PROPAGATED -- imported transversal doctrine (D2)\n\n"
                              "One-way mirror of the source repo's PR-/HR- rules. Append-only, "
                              "machine-managed -- do NOT hand-edit; edit the source UKDL.\n"
                              if not prior else "")
                    with pp.open("a", encoding="utf-8") as fh:
                        if header:
                            fh.write(header)
                        fh.write(f"\n<!-- propagated {stamp} from {_slug(str(source_repo_root))} -->\n")
                        fh.write("\n".join(new_chunks))
                result[slug] = {"added": added, "skipped": skipped}
            except OSError as e:
                result[slug] = {"added": 0, "skipped": 0, "note": f"io error: {e}"}
        return result
    except Exception as e:  # noqa: BLE001 -- fail-open
        return {"error": f"propagate failed (fail-open): {e}"}


# --------------------------------------------------------------------------- #
# 3. FDI-0 advisory (wired into token_irr.stop_entry).
# --------------------------------------------------------------------------- #
def fdi_advisory(repo: str, *, state_dir=None) -> str | None:
    """At a NON-PP frontier Stop with 0 deposits, nudge the Owner to declare an
    objective so the session actually mines a portable asset. None otherwise."""
    try:
        if _is_pp_repo(repo):
            return None
        dep_path = _fd_state_dir(state_dir) / f"deposits_{_slug(repo)}.jsonl"
        n = len(_read_deposits(dep_path)) if dep_path.is_file() else 0
        if n > 0:
            return None
        name = Path(repo).name or repo
        return (f"FD flywheel: 0 portable deposits in {name} (FDI 0). This frontier "
                f"spend left no reusable asset -- declare PP_SESSION_OBJECTIVE (or a "
                f".pp_frontier.json) so the session mines a delta worth keeping.")
    except Exception:  # noqa: BLE001 -- fail-open
        return None


def load_subscribers(config_path=None) -> list:
    """Read the subscriber registry [{slug, root}] the Owner maintains. Fail-open."""
    try:
        p = (Path(config_path) if config_path else
             Path(__file__).resolve().parents[2] / "vault" / "config" / "fd_subscribers.json")
        if not p.is_file():
            return []
        data = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
        return data if isinstance(data, list) else data.get("subscribers", [])
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="D2 Federated FD Ledger")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--propagate", action="store_true",
                    help="mirror source PR-/HR- into subscriber repos (from fd_subscribers.json)")
    ap.add_argument("--advisory", metavar="REPO", help="print the FDI-0 advisory for REPO")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.aggregate:
        agg = aggregate()
        print(json.dumps(agg, indent=2) if args.json else
              f"repos={agg['repos']} global_assets={agg['global'].get('total_assets')} "
              f"global_fdi={agg['global'].get('global_fdi')}")
        for r in agg.get("per_repo", []):
            print(f"  {r['slug']}: {r['assets']} assets, FDI {r['fdi']}")
    if args.propagate:
        src = str(Path(__file__).resolve().parents[2])
        targets = [os.path.expanduser(s["root"]) for s in load_subscribers() if s.get("root")]
        print("propagate:", json.dumps(propagate_critical(src, targets), indent=2))
    if args.advisory:
        print(fdi_advisory(args.advisory) or "(no advisory)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
