#!/usr/bin/env python3
"""owner_queue.py -- D4: the OWNER_QUEUE activation layer. HR-001 residuals, surfaced.

HR-001 makes some actions structurally the Owner's (writing ~/.claude/hooks, a
scheduled-task registration, a settings.json hook entry): the agent SHIPS the
PP-internal half and DOCUMENTS the Owner step. Those documented steps were scattered
-- buried in a vault/plans doc, a memory file, a session-end emission -- tracked
nowhere as a SET, so built->live latency was unbounded and invisible (the PM-03
consumer wiring sat pending 6+ days).

TWO LAYERS, ONE HUMAN SURFACE (reconciled with the parallel-pane vault/OWNER_QUEUE.md):
  * vault/OWNER_QUEUE.md   -- THE durable, git-tracked, human-curated register. Rich
                              runbooks, "why", "verify". Agents append items HERE
                              (versioned, PR-reviewable, cross-machine). NOT rewritten
                              by this engine -- it is the source, not a derived file.
  * THIS engine            -- the DYNAMIC ACTIVATION layer over that doc. `ingest_vault_queue`
                              parses the doc's `[PENDING]` sections into an append-only
                              event log + a materialized pending view the SessionStart
                              hub reads in pure JS; the hub surfaces stale residuals so
                              none can hide, and a resolved section (its [PENDING] tag
                              removed by the Owner) auto-flips its row done on re-ingest.
                              `append()` also serves rare purely-programmatic residuals.

State (machine-local, under ~/.claude/state -- residuals are host-specific):
  OWNER_QUEUE.jsonl        -- append-only add/done EVENTS (multi-pane safe; source of truth).
  OWNER_QUEUE.pending.json -- materialized pending rows (the hub's pure-JS read view;
                              a python shell-out at SessionStart is forbidden, SCS C23).

Fail-open ABSOLUTE: any error -> a benign no-op / empty result, never an exception
that could disturb a caller (a residual tracker must never break the work it tracks).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]

_GRACE_HOURS_DEFAULT = float(os.environ.get("PP_OWNER_QUEUE_GRACE_H", "24"))
_ID_HASH_LEN = 10        # chars of the (action, command) sha256 that form a row id
_HOURS_PER_DAY = 24.0    # age-string day/hour crossover

_PENDING_RE = re.compile(r"\[PENDING", re.I)
_SYSTEM_RE = re.compile(r"\*\*Systems?:\*\*\s*(.+)", re.I)
_HEADER_RE = re.compile(r"^##\s+(.+)$")
_TRAIL_TAG_RE = re.compile(r"\s*\[[^\]]*\]\s*$")   # trailing "[PENDING ...]"
_LEAD_NUM_RE = re.compile(r"^\d+\.\s*")            # leading "3. "


def _state_dir(state_dir=None) -> Path:
    return Path(state_dir) if state_dir else (Path.home() / ".claude" / "state")


def _jsonl(state_dir=None) -> Path:
    return _state_dir(state_dir) / "OWNER_QUEUE.jsonl"


def _pending_json(state_dir=None) -> Path:
    return _state_dir(state_dir) / "OWNER_QUEUE.pending.json"


def _vault_md_path(repo_root=None) -> Path:
    return (Path(repo_root) if repo_root else _PP_ROOT) / "vault" / "OWNER_QUEUE.md"


def _now(now=None) -> datetime:
    return now or datetime.now(timezone.utc)


def _mk_id(action: str, command: str) -> str:
    """Deterministic id from (action, command) so a re-run backfill is idempotent."""
    h = hashlib.sha256(f"{action}\x00{command}".encode("utf-8")).hexdigest()[:_ID_HASH_LEN]
    return f"q-{h}"


def _vault_id(title: str) -> str:
    """Stable id for a vault-sourced section (by title), so re-ingest is idempotent."""
    h = hashlib.sha256(("vault\x00" + title).encode("utf-8")).hexdigest()[:_ID_HASH_LEN]
    return f"qv-{h}"


def _read_events(state_dir=None) -> list:
    p = _jsonl(state_dir)
    if not p.is_file():
        return []
    out = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
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


def _fold(events: list) -> list:
    """Fold the add/done event log into current rows (last op wins per id)."""
    rows: dict[str, dict] = {}
    order: list[str] = []
    for ev in events:
        op = ev.get("op")
        rid = ev.get("id")
        if not rid:
            continue
        if op == "add":
            if rid not in rows:
                order.append(rid)
                rows[rid] = {
                    "id": rid, "created": ev.get("created", ""),
                    "action": ev.get("action", ""), "command": ev.get("command", ""),
                    "unblocks": ev.get("unblocks", ""), "component": ev.get("component"),
                    "source": ev.get("source"),
                    "status": "pending", "completed": None, "by": None,
                }
            else:
                r = rows[rid]
                r["action"] = ev.get("action", r["action"])
                r["command"] = ev.get("command", r["command"])
        elif op == "done":
            if rid in rows:
                rows[rid]["status"] = "done"
                rows[rid]["completed"] = ev.get("completed", "")
                rows[rid]["by"] = ev.get("by", "manual")
    return [rows[r] for r in order]


def load(state_dir=None) -> list:
    """Current queue rows (folded). Fail-open -> []."""
    try:
        return _fold(_read_events(state_dir))
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def _append_event(ev: dict, state_dir=None) -> bool:
    try:
        d = _state_dir(state_dir)
        d.mkdir(parents=True, exist_ok=True)
        with _jsonl(state_dir).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def _materialize(state_dir=None) -> None:
    """Rewrite the pending.json view the SessionStart hub reads. Fail-open."""
    try:
        pending_rows = [r for r in load(state_dir) if r["status"] == "pending"]
        _pending_json(state_dir).write_text(
            json.dumps(pending_rows, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def append(action: str, command: str, *, unblocks: str = "", component=None,
           source=None, state_dir=None, now=None, row_id: str | None = None) -> str:
    """Add a pending residual (idempotent by id). Returns the row id. Fail-open."""
    try:
        rid = row_id or _mk_id(action, command)
        if rid in {r["id"] for r in load(state_dir)}:
            return rid  # idempotent -- a backfill re-run does not duplicate
        _append_event({"op": "add", "id": rid, "created": _now(now).isoformat(),
                       "action": action, "command": command, "unblocks": unblocks,
                       "component": component, "source": source}, state_dir)
        _materialize(state_dir)
        return rid
    except Exception:  # noqa: BLE001 -- fail-open
        return row_id or _mk_id(action, command)


def complete(row_id: str, *, by: str = "manual", state_dir=None, now=None) -> bool:
    """Mark a row done (idempotent). Returns True if a pending row was closed."""
    try:
        r = {x["id"]: x for x in load(state_dir)}.get(row_id)
        if not r or r["status"] == "done":
            return False
        _append_event({"op": "done", "id": row_id, "completed": _now(now).isoformat(),
                       "by": by}, state_dir)
        _materialize(state_dir)
        return True
    except Exception:  # noqa: BLE001 -- fail-open
        return False


def autoclear(live_component_ids, *, state_dir=None, now=None) -> list:
    """Close every pending row whose `component` is now LIVE. Called by the D1
    auditor -- the composition that lets the Owner never bookkeep completion.
    Returns the list of closed ids. Fail-open -> []."""
    try:
        live = set(live_component_ids or [])
        closed = []
        for r in load(state_dir):
            if r["status"] == "pending" and r.get("component") and r["component"] in live:
                if complete(r["id"], by="auto", state_dir=state_dir, now=now):
                    closed.append(r["id"])
        return closed
    except Exception:  # noqa: BLE001 -- fail-open
        return []


# --------------------------------------------------------------------------- #
# vault/OWNER_QUEUE.md ingestion -- the bridge to the durable human register.
# --------------------------------------------------------------------------- #
def _parse_vault_sections(text: str) -> list:
    """Split the durable doc into `## ` sections; classify each as pending (has a
    [PENDING] tag) and pull its **System(s):** path. Fail-open -> []."""
    sections, cur = [], None
    for ln in text.split("\n"):
        m = _HEADER_RE.match(ln)
        if m:
            if cur:
                sections.append(cur)
            cur = {"header": m.group(1).strip(), "body": []}
        elif cur is not None:
            cur["body"].append(ln)
    if cur:
        sections.append(cur)
    out = []
    for s in sections:
        header = s["header"]
        body = "\n".join(s["body"])
        sysm = _SYSTEM_RE.search(body)
        system = sysm.group(1).strip().strip("`").strip() if sysm else None
        title = _LEAD_NUM_RE.sub("", _TRAIL_TAG_RE.sub("", header)).strip()
        out.append({"title": title, "pending": bool(_PENDING_RE.search(header)),
                    "system": system})
    return out


def ingest_vault_queue(repo_root=None, *, state_dir=None, now=None) -> dict:
    """Sync the durable vault/OWNER_QUEUE.md [PENDING] sections into the dynamic
    layer: new pending sections become rows; a section that lost its [PENDING] tag
    flips its row done (by='vault-resolved'). Idempotent, fail-open -> zero counts."""
    try:
        md = _vault_md_path(repo_root)
        if not md.is_file():
            return {"ingested": 0, "resolved": 0, "pending_vault": 0}
        text = md.read_text(encoding="utf-8-sig", errors="replace")
        sections = _parse_vault_sections(text)
        pending_ids = {_vault_id(s["title"]) for s in sections if s["pending"]}
        cur = {r["id"]: r for r in load(state_dir)}
        ingested = 0
        for s in sections:
            if not s["pending"]:
                continue
            rid = _vault_id(s["title"])
            if rid not in cur:
                _append_event({"op": "add", "id": rid, "created": _now(now).isoformat(),
                               "action": s["title"], "command": "runbook: vault/OWNER_QUEUE.md",
                               "unblocks": s["system"] or "", "component": s["system"],
                               "source": "vault"}, state_dir)
                ingested += 1
        resolved = 0
        for rid, r in cur.items():
            if (r.get("source") == "vault" and r["status"] == "pending"
                    and rid not in pending_ids):
                if complete(rid, by="vault-resolved", state_dir=state_dir, now=now):
                    resolved += 1
        _materialize(state_dir)
        return {"ingested": ingested, "resolved": resolved, "pending_vault": len(pending_ids)}
    except Exception:  # noqa: BLE001 -- fail-open
        return {"ingested": 0, "resolved": 0, "pending_vault": 0}


def pending(state_dir=None, *, min_age_h: float = 0.0, now=None) -> list:
    """Pending rows, optionally only those older than min_age_h. Fail-open -> []."""
    try:
        nz = _now(now)
        out = []
        for r in load(state_dir):
            if r["status"] != "pending":
                continue
            if min_age_h > 0:
                try:
                    t = datetime.fromisoformat(r["created"])
                    if t.tzinfo is None:
                        t = t.replace(tzinfo=timezone.utc)
                    if (nz - t).total_seconds() / 3600.0 < min_age_h:
                        continue
                except (ValueError, TypeError):
                    pass
            out.append(r)
        return out
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def _age_str(created: str, now: datetime) -> str:
    try:
        t = datetime.fromisoformat(created)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        h = (now - t).total_seconds() / 3600.0
        return (f"{h/_HOURS_PER_DAY:.1f}d" if h >= _HOURS_PER_DAY else f"{h:.1f}h")
    except (ValueError, TypeError):
        return "?"


def sessionstart_digest(state_dir=None, *, min_age_h: float = _GRACE_HOURS_DEFAULT,
                        now=None) -> str | None:
    """The SessionStart line for pending rows past the grace window. Mirrors the JS
    hub hook's logic so the CLI/tests and the hook agree. Fail-open -> None."""
    stale = pending(state_dir, min_age_h=min_age_h, now=now)
    if not stale:
        return None
    nz = _now(now)
    lines = [f"[OWNER_QUEUE] {len(stale)} residual(s) pending > "
             f"{min_age_h:.0f}h (durable list: vault/OWNER_QUEUE.md):"]
    for r in stale:
        lines.append(f"- {r['action']} (age {_age_str(r['created'], nz)}): {r.get('command','')}")
    return "\n".join(lines)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="D4 OWNER_QUEUE activation layer")
    ap.add_argument("--ingest", action="store_true", help="sync vault/OWNER_QUEUE.md -> dynamic layer")
    ap.add_argument("--add", nargs="?", const="", help="action text (with --command)")
    ap.add_argument("--command", default="")
    ap.add_argument("--unblocks", default="")
    ap.add_argument("--component", default=None)
    ap.add_argument("--done", help="complete a row by id")
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--min-age-h", type=float, default=_GRACE_HOURS_DEFAULT)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.ingest:
        print("ingest:", ingest_vault_queue())
    if args.add:
        print("added", append(args.add, args.command, unblocks=args.unblocks, component=args.component))
    if args.done:
        print("closed" if complete(args.done) else "no-op")
    if args.digest:
        print(sessionstart_digest(min_age_h=args.min_age_h) or "(no stale residuals)")
    rows = load()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            mark = "DONE" if r["status"] == "done" else "PEND"
            print(f"  [{mark}] {r['id']} ({r.get('source') or 'prog'}) {r['action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
