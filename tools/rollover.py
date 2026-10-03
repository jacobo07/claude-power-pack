#!/usr/bin/env python3
"""Interactive context rollover (P3) -- capsule, safe-to-forget, resume.

Spec: vault/specs/interactive-context-rollover.md. The mission/worker half of
context rotation belongs to tools/gsd_epoch.py; this module owns the ORDINARY
interactive session, where today the Owner types /kclear, /clear, and pastes a
plan path. Preservation and destruction are separate calls here: `seal`
writes and reads back a capsule, `safe_to_forget` judges it, and nothing in
this module ever resets a context. In SHADOW mode (the only mode wired today)
each decision is only recorded.

Every fact is typed: a value, or UNKNOWN with a reason. UNKNOWN never counts
as present -- a capsule missing its HEAD is not "probably fine".

Subcommands:
  shadow   observe one session: decide, compile, seal, judge; destroys nothing
  seal     compile + seal a capsule now (what /kclear calls)
  resume   successor side: claim the newest capsule for this cwd, refresh
           reality, print the bootstrap and the resume exam (/kresume)
  certify  successor answers the exam; certified capsules are retired
  status   recent ledger rows
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

SCHEMA = "rollover-capsule-v1"
# capsule-v2 (spec vault/specs/mission-capsule-rollover.md): a mission worker's handoff. Same seal,
# gate, claim, refresh, exam and certify as v1 -- only the identity and the sources differ. Keyed
# `mission-<mission_id>-e<epoch>` and stored in its OWN directory: the interactive hub card and the
# autotype enumerate `capsules/` with no schema filter, so a worker's capsule there would tell an
# ordinary pane in the same repo to /kresume it.
SCHEMA_V2 = "rollover-capsule-v2"
MISSION_PREFIX = "mission-"
MISSION_SEAL_ORIGINS = ("worker_handoff", "supervisor_fallback", "recovery")
CLAIM_LEASE_S = 30 * 60          # a claim nobody certified within this is recoverable (spec I3)
STATE_DIR =Path(os.environ.get("CPP_ROLLOVER_STATE_DIR") or (Path.home() / ".claude" / "state" / "rollover"))
UNKNOWN = "UNKNOWN"

MIN_GROWTH_TOKENS = 150_000      # resident above floor+bootstrap worth discarding
HORIZON_CALLS = 30               # ESTIMATE of calls left when nobody knows; recorded as such
HANDOFF_MAX_AGE_S = 30 * 60      # a handoff older than this does not describe the current state
CAPSULE_MAX_AGE_S = 24 * 3600    # a successor never adopts a capsule older than this
BOOTSTRAP_MAX_CHARS = 4000
GOAL_RE = re.compile(r"(RESUMPTION[^/\\]*\.md$|[/\\]vault[/\\](plans|specs)[/\\][^/\\]+\.md$|[/\\]\.planning[/\\])", re.I)
NEXT_HEAD_RE = re.compile(r"^#{1,4}\s*.*\b(next|pending|open obligations?|remaining)\b", re.I)
ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.*\S)")
HANDOFF_SID_RE = re.compile(r"(?:Session ID\*{0,2}:\s*`?|session_id:\s*)([0-9a-fA-F-]{8,})")
GIT_CANDIDATES = [r"C:\Program Files\Git\cmd\git.exe", "git"]


RESET_MAX_AGE_S = 30 * 60        # a capsule older than this no longer describes the session


def shadow_enabled() -> bool:
    return (os.environ.get("CPP_ROLLOVER_SHADOW") or "").lower() != "off"


def active_enabled() -> bool:
    """Active rollover is ON by default (Owner, 2026-09-28, typed in the owning pane).

    Kill switch `CPP_ROLLOVER_ACTIVE=0`. The switch only ever DISABLES: unset is ON, so a
    host that never heard of the variable still behaves the way the Owner asked for on
    every host. A deny is a value you send, not a value you hope is absent -- but here the
    dangerous direction is enabling by accident, and an unset variable cannot type `/clear`
    on its own: every reset still has to pass `gate()` first.
    """
    return (os.environ.get("CPP_ROLLOVER_ACTIVE") or "").strip().lower() not in ("0", "off", "false")


def _now() -> float:
    return time.time()


def _iso(ts: Optional[float] = None) -> str:
    return _dt.datetime.fromtimestamp(ts if ts is not None else _now(), _dt.timezone.utc).isoformat(timespec="seconds")


def _unknown(reason: str) -> dict:
    return {"state": UNKNOWN, "reason": reason}


# ----------------------------------------------------------------------------- repo
def _git_exe() -> str:
    for c in GIT_CANDIDATES:
        if c == "git" or Path(c).is_file():
            return c
    return "git"


def _git(root: Path, *args: str, timeout: float = 15.0) -> tuple[bool, str]:
    # 5 s timed out `rev-parse` on 2026-09-28 at 473 MB free of 32 GB. A starved host must read
    # as UNKNOWN (refusal), never hang the caller: every call site is detached or interactive.
    try:
        cp = subprocess.run([_git_exe(), "-C", str(root), *args], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, exc.__class__.__name__
    return cp.returncode == 0, (cp.stdout if cp.returncode == 0 else cp.stderr).strip()


def repo_facts(cwd: str) -> dict:
    """Root, branch, HEAD, sorted dirty-path SET. Any failed read is UNKNOWN for that field."""
    ok, root = _git(Path(cwd), "rev-parse", "--show-toplevel")
    if not ok:
        return {"state": UNKNOWN, "reason": f"not a git work tree ({root[:80]})"}
    root_p = Path(root)
    out: dict = {"state": "OK", "root": str(root_p)}
    ok, head = _git(root_p, "rev-parse", "HEAD")
    out["head"] = head if ok else _unknown(head[:80])
    ok, branch = _git(root_p, "rev-parse", "--abbrev-ref", "HEAD")
    out["branch"] = branch if ok else _unknown(branch[:80])
    ok, status = _git(root_p, "status", "--porcelain", "--untracked-files=no", timeout=30.0)
    out["dirty"] = sorted({ln[3:].strip() for ln in status.splitlines() if len(ln) > 3}) if ok else _unknown(status[:80])
    return out


def foreign_custody(writes: list[str], capsule_root: Optional[str]) -> dict:
    """This session's OWN written paths that are uncommitted in a repo other than the capsule's.

    Measured 2026-10-03 (plan ccp-s16 F7): session a4849588 resumed in an Orca-X worktree, fixed
    tools/rollover.py in the Power Pack repo, sealed SAFE_TO_FORGET and was cleared; the edit sat
    uncommitted for 3 days with no obligation naming it. The capsule kept the last 15 writes and
    read dirty state only for its own repo. Status is scoped to the session's own paths, so peers'
    dirt in a shared tree is never judged. Only Write/Edit/NotebookEdit paths are seen: files
    written through a shell are invisible here."""
    by_root: dict[str, list[str]] = {}
    unchecked = 0
    roots: dict[str, Optional[str]] = {}
    own = os.path.normcase(os.path.abspath(capsule_root)) if capsule_root else None
    for w in writes:
        parent = str(Path(w).parent)
        if parent not in roots:
            ok, top = _git(Path(parent), "rev-parse", "--show-toplevel") if Path(parent).is_dir() else (False, "")
            roots[parent] = top if ok else None
        top = roots[parent]
        if not top:
            unchecked += 1
            continue
        if own and os.path.normcase(os.path.abspath(top)) == own:
            continue
        by_root.setdefault(top, []).append(w)
    repos = []
    for top, paths in sorted(by_root.items()):
        ok, status = _git(Path(top), "status", "--porcelain", "--untracked-files=all", "--", *paths, timeout=30.0)
        if not ok:
            return _unknown(f"git status failed in {top}: {status[:80]}")
        dirty = sorted({ln[3:].strip() for ln in status.splitlines() if len(ln) > 3})
        if dirty:
            repos.append({"root": top, "dirty": dirty})
    return {"state": "OK", "repos": repos, "unchecked_non_repo": unchecked}


# ----------------------------------------------------------------------- transcript
def _rows(path: Optional[Path]):
    if not path or not Path(path).is_file():
        return
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                yield row


def session_writes(transcript: Optional[Path]) -> list[str]:
    """Paths this session wrote, oldest first (Write/Edit/NotebookEdit tool inputs)."""
    seen: dict[str, int] = {}
    for i, row in enumerate(_rows(transcript)):
        msg = row.get("message")
        content = msg.get("content") if isinstance(msg, dict) else None
        for b in content if isinstance(content, list) else []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit", "NotebookEdit"):
                p = (b.get("input") or {}).get("file_path") or (b.get("input") or {}).get("notebook_path")
                if p:
                    seen[str(p)] = i
    return [p for p, _ in sorted(seen.items(), key=lambda kv: kv[1])]


def usage_facts(transcript: Optional[Path]) -> dict:
    """Floor (call #1) and current resident, one API call counted once (tis_observed)."""
    if not transcript or not Path(transcript).is_file():
        return _unknown("no transcript")
    try:
        import tis_observed as tis
        calls, *_ = tis._calls_in(Path(transcript))
    except Exception as exc:  # noqa: BLE001 -- a reader failure is UNKNOWN, not zero
        return _unknown(f"reader failed: {exc.__class__.__name__}")
    if not calls:
        return _unknown("no model calls yet")
    resident = [tis._context_of(c["usage"]) for c in calls]
    return {"state": "OK", "calls": len(resident), "floor": resident[0], "resident": resident[-1],
            "model": calls[-1].get("model") or ""}


def price_ratio(model: str) -> dict:
    """1h cache write and cache read price for `model` from the newest dated book."""
    try:
        import session_autopsy as sa
        books = sa._price_books()
        row = sa._model_row(books[-1][1], model) if books else None
    except Exception as exc:  # noqa: BLE001
        return _unknown(f"price book unreadable: {exc.__class__.__name__}")
    if not row or row.get("cache_write_1h") is None or row.get("cache_read") is None:
        return _unknown(f"no price row for {model or 'unknown model'}")
    return {"state": "OK", "write": float(row["cache_write_1h"]), "read": float(row["cache_read"]),
            "source": books[-1][2]}


def child_state(session_id: str) -> dict:
    """Pending background work, from gsd_epoch's reader (CONNECT, not a copy)."""
    try:
        import gsd_epoch
        return gsd_epoch.child_work(session_id)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": UNKNOWN, "reason": f"child reader unavailable: {exc.__class__.__name__}"}


def _find_transcript(session_id: str) -> Optional[Path]:
    """The session's own transcript, by exact id (gsd_epoch's lookup), never 'the newest file'."""
    try:
        import gsd_epoch
        return gsd_epoch._transcript(session_id)
    except Exception:  # noqa: BLE001 -- absent is UNKNOWN downstream
        return None


def current_session() -> str:
    """The host names its own session in CLAUDE_CODE_SESSION_ID (verified 2026-09-28)."""
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or ""


def session_cwd(session_id: str) -> Optional[str]:
    """The directory the host SESSION runs in, from its registry record, or None.

    Not the shell cwd: measured 2026-09-29, session 357823a8 ran in InfinityOps and sealed
    after a `cd` into io-chatgpt-plugin, so the capsule named only that repo and the successor,
    which opens where the session runs, never saw it (no card, no autotype). The registry
    record (~/.claude/sessions/<pid>.json, the one the daemon routes by) carries the session's
    own cwd; it is trusted only when its sessionId is this session. CLAUDE_PID is tried first,
    then every record, since a caller may not run under the host's environment."""
    if not session_id:
        return None
    d = Path(os.environ.get("CPP_CLAUDE_SESSIONS_DIR") or (Path.home() / ".claude" / "sessions"))
    pid = os.environ.get("CLAUDE_PID") or ""
    first = [d / f"{pid}.json"] if pid.isdigit() else []
    try:
        rest = sorted(d.glob("*.json")) if d.is_dir() else []
    except OSError:
        rest = []
    for p in first + rest:
        try:
            rec = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if isinstance(rec, dict) and rec.get("sessionId") == session_id and rec.get("cwd"):
            return str(rec["cwd"])
    return None


def host_identity() -> Optional[dict]:
    """The claude process this code runs under, as {pid, proc_start}, or None.

    `/clear` starts a new session INSIDE the same claude process, so the process is the one
    thing a predecessor and its successor share; the successor's transcript names only itself.
    Measured 2026-09-30 (614697c1): a sibling pane in the same repo sealed 9e694f9a eleven
    minutes after this pane's predecessor sealed f3099e7b, and newest-for-this-directory handed
    the successor the sibling's capsule -- locking the sibling's real successor out (exit 5).
    proc_start comes from the host registry (~/.claude/sessions/<pid>.json) so a recycled pid
    cannot impersonate the sealer. None when either half is missing: unknown never matches."""
    pid = os.environ.get("CLAUDE_PID") or ""
    if not pid.isdigit():
        return None
    d = Path(os.environ.get("CPP_CLAUDE_SESSIONS_DIR") or (Path.home() / ".claude" / "sessions"))
    try:
        rec = json.loads((d / f"{pid}.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    start = rec.get("procStart") if isinstance(rec, dict) else None
    if not start or str(rec.get("pid")) != pid:
        return None
    return {"pid": int(pid), "proc_start": str(start)}


# ------------------------------------------------------------------ goal + handoff
def goal_pointer(cwd: str, writes: list[str], explicit: Optional[str] = None) -> dict:
    if explicit:
        p = Path(explicit) if Path(explicit).is_absolute() else Path(cwd) / explicit
        return {"state": "OK", "path": str(p), "basis": "explicit"} if p.is_file() else _unknown(f"named goal {explicit} does not exist")
    for w in reversed(writes):
        if GOAL_RE.search(w) and Path(w).is_file():
            return {"state": "OK", "path": w, "basis": "written by this session"}
    return _unknown("this session wrote no plan/spec/RESUMPTION file and none was named")


def obligations_from(path: Optional[str]) -> list[str]:
    """Items under a heading naming next/pending/open work. Empty list = none found."""
    if not path or not Path(path).is_file():
        return []
    items, inside = [], False
    for line in Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if line.lstrip().startswith("#"):
            inside = bool(NEXT_HEAD_RE.match(line.strip()))
            continue
        m = ITEM_RE.match(line) if inside else None
        if m:
            items.append(m.group(1)[:200])
    return items[:10]


def handoff_facts(cwd: str, session_id: str = "") -> dict:
    """This session's own handoff (memory/handoffs/<sid>.md) first; the shared project file,
    which any pane's /kclear overwrites, only as a fallback -- and then its Session ID decides."""
    try:
        import session_checkpoint as sc
        mem = sc.get_memory_dir(sc.find_project_root(Path(cwd)))
        own = mem / getattr(sc, "HANDOFFS_DIR", "handoffs") / f"{session_id}.md"
        path = own if session_id and own.is_file() else mem / sc.HANDOFF_NAME
    except (Exception, SystemExit) as exc:  # noqa: BLE001 -- find_project_root raises SystemExit
        return _unknown(f"handoff location unresolved: {exc.__class__.__name__}")
    if not path.is_file():
        return _unknown(f"no handoff at {path}")
    data = path.read_bytes()
    # The handoff file is per PROJECT, not per session: a sibling pane's /kclear overwrites it.
    # Its own Session ID line (session_checkpoint.render_handoff / the watchdog's tier-2 twin) is
    # the only thing that says whose state it describes.
    m = HANDOFF_SID_RE.search(data.decode("utf-8", errors="replace"))
    return {"state": "OK", "path": str(path), "age_s": round(_now() - path.stat().st_mtime),
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "session": m.group(1) if m else UNKNOWN}


# ------------------------------------------------------------------------- capsule
def compile_capsule(session_id: str, cwd: str, transcript: Optional[str], *, goal: Optional[str] = None,
                    next_items: Optional[list[str]] = None, summary: str = "") -> dict:
    tp = Path(transcript) if transcript else _find_transcript(session_id)
    writes = session_writes(tp)
    gp = goal_pointer(cwd, writes, goal)
    handoff = handoff_facts(cwd, session_id)
    own_handoff = handoff.get("state") == "OK" and handoff.get("session") == session_id
    items, source = list(next_items or []), "explicit"
    if not items:
        items, source = obligations_from(gp.get("path")), "goal file"
    if not items and own_handoff:
        items, source = obligations_from(handoff.get("path")), "own handoff"
    repo = repo_facts(cwd)
    return {
        "schema": SCHEMA, "session_id": session_id, "cwd": str(cwd), "created": _iso(),
        "session_cwd": session_cwd(session_id),
        "host": host_identity(),
        "transcript": str(tp) if tp else None,
        "repo": repo, "goal": gp,
        "foreign": foreign_custody(writes, repo.get("root") if repo.get("state") == "OK" else None),
        "obligations": items or [], "obligations_source": source if items else None,
        "handoff": handoff, "children": child_state(session_id),
        "usage": usage_facts(tp),
        "writes": writes[-15:],
        "summary": (summary or "")[:600],
    }


def completeness(capsule: dict, now: Optional[float] = None) -> dict:
    """Which load-bearing categories are present. UNKNOWN is absent; a HOLD is a refusal."""
    missing, warnings = [], []
    repo = capsule.get("repo") or {}
    if repo.get("state") != "OK":
        missing.append(f"repo: {repo.get('reason', 'absent')}")
    else:
        for k in ("head", "branch", "dirty"):
            if isinstance(repo.get(k), dict):
                missing.append(f"repo.{k}: {repo[k].get('reason')}")
        if isinstance(repo.get("dirty"), list) and repo["dirty"]:
            warnings.append(f"{len(repo['dirty'])} dirty tracked paths survive on disk, not in context")
    # Custody (ccp-s16 S1): the session's own uncommitted writes in ANOTHER repo leave nobody holding
    # them once this context is gone. Capsules sealed before this key existed are not judged on it.
    fo = capsule.get("foreign")
    if isinstance(fo, dict) and fo.get("state") != "OK":
        missing.append(f"custody: {fo.get('reason', 'unreadable')}")
    elif isinstance(fo, dict):
        for r in fo.get("repos") or []:
            missing.append(f"custody: {len(r['dirty'])} uncommitted path(s) this session wrote in {r['root']}: "
                           + ", ".join(r["dirty"][:4]) + " -- commit them there before /clear")
        if fo.get("unchecked_non_repo"):
            warnings.append(f"custody: {fo['unchecked_non_repo']} written path(s) outside any git repo, not checked")
    if (capsule.get("goal") or {}).get("state") != "OK":
        missing.append(f"goal: {(capsule.get('goal') or {}).get('reason', 'absent')}")
    if not capsule.get("obligations"):
        missing.append("obligations: no open item found in the goal file or handoff")
    h = capsule.get("handoff") or {}
    if capsule.get("kind") == "mission":
        # A worker has no /kclear handoff file: its continuity sources are the mission record, GSD
        # and its own note. What must be present instead is who it is and how it was sealed.
        run = capsule.get("run") if isinstance(capsule.get("run"), dict) else {}
        for k in ("mission_id", "epoch", "successor_epoch"):
            if run.get(k) in (None, ""):
                missing.append(f"run.{k}: absent")
        origin = capsule.get("seal_origin")
        if origin not in MISSION_SEAL_ORIGINS:
            missing.append(f"seal_origin: {origin!r} is not one of {', '.join(MISSION_SEAL_ORIGINS)}")
        elif origin == "worker_handoff" and not (capsule.get("note") or "").strip():
            missing.append("note: the worker sealed no HANDOFF NOTE -- it is not a worker hand-off")
        if origin in ("supervisor_fallback", "recovery") and not capsule.get("degraded"):
            missing.append(f"degraded: a {origin} seal must be marked degraded")
    elif h.get("state") != "OK":
        missing.append(f"handoff: {h.get('reason', 'absent')}")
    elif h.get("session") != capsule.get("session_id"):
        missing.append(f"handoff: written by session {str(h.get('session'))[:8]}, not this one -- run /kclear")
    elif h.get("age_s", 0) > HANDOFF_MAX_AGE_S:
        missing.append(f"handoff: {h['age_s']}s old, older than {HANDOFF_MAX_AGE_S}s -- run /kclear")
    ch = (capsule.get("children") or {}).get("verdict")
    if ch == "HOLD":
        missing.append(f"children: {len(capsule['children'].get('pending') or [])} background task(s) pending")
    elif ch == "EXPIRED":
        warnings.append("children: pending background work older than the wait bound, named as lost")
    elif ch != "CLEAR":
        missing.append(f"children: {(capsule.get('children') or {}).get('reason', 'unknown')}")
    return {"complete": not missing, "missing": missing, "warnings": warnings}


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def capsule_path(session_id: str, state_dir: Optional[Path] = None) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    sub = "mission-capsules" if safe.startswith(MISSION_PREFIX) else "capsules"
    return (state_dir or STATE_DIR) / sub / f"{safe}.json"


def mission_key(mission_id: str, epoch) -> str:
    """The capsule key of the worker that ran `epoch` of `mission_id`. Session ids are uuids and
    never start with MISSION_PREFIX, so the two key spaces cannot collide."""
    return f"{MISSION_PREFIX}{mission_id}-e{int(epoch)}"


def seal(capsule: dict, state_dir: Optional[Path] = None) -> dict:
    """Write, then read back from DISK and compare the hash. Only a read-back is a seal."""
    path = capsule_path(capsule.get("session_id", ""), state_dir)
    data = json.dumps(capsule, indent=1, sort_keys=True, ensure_ascii=False).encode("utf-8")
    want = hashlib.sha256(data).hexdigest()
    try:
        _atomic_write(path, data)
        got = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        return {"sealed": False, "reason": f"write failed: {exc.__class__.__name__}", "path": str(path)}
    if got != want:
        return {"sealed": False, "reason": "read-back hash differs", "path": str(path)}
    return {"sealed": True, "path": str(path), "sha256": want, "bytes": len(data)}


def safe_to_forget(receipt: dict, comp: dict) -> dict:
    """PASS only for a sealed capsule that is still the bytes it was sealed as, and complete."""
    reasons = []
    if not receipt.get("sealed"):
        reasons.append(f"not sealed: {receipt.get('reason')}")
    else:
        try:
            if hashlib.sha256(Path(receipt["path"]).read_bytes()).hexdigest() != receipt["sha256"]:
                reasons.append("capsule on disk changed since it was sealed")
        except OSError as exc:
            reasons.append(f"capsule unreadable: {exc.__class__.__name__}")
    reasons += comp.get("missing") or []
    return {"verdict": "SAFE_TO_FORGET" if not reasons else "REFUSED", "reasons": reasons}


def sealed_receipt(session_id: str, state_dir: Optional[Path] = None) -> Optional[dict]:
    """The receipt this session's capsule was ACTUALLY sealed with, read from the ledger.

    A capsule cannot witness its own integrity: hashing the file and comparing the digest
    to itself is a predicate with one reachable branch, so it would answer "unchanged" for
    a capsule someone had rewritten between the seal and the reset. The `capsule_sealed`
    row is the only independent record of the bytes that were observed.
    """
    path = (state_dir or STATE_DIR) / "rollover-ledger.jsonl"
    found = None
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("event") == "capsule_sealed" and row.get("session_id") == session_id:
                    found = row          # last one wins: the most recent seal
    except OSError:
        return None
    return found


def gate(session_id: str, state_dir: Optional[Path] = None, max_age_s: float = RESET_MAX_AGE_S,
         now: Optional[float] = None) -> dict:
    """May `/clear` be typed for this session RIGHT NOW? The one authority for the reset.

    Judges the capsule that was sealed and shown, never a freshly compiled one: re-sealing
    at the moment of destruction would authorise destroying whatever arrived since the
    seal, which is exactly the race the receipt exists to close.

    Three verdicts, deliberately not interchangeable. SAFE_TO_FORGET may reset; REFUSED
    means the capsule moved, aged out, or was never good; NO_CAPSULE means nothing was
    ever sealed here. Only the middle one is a statement about this session's contents,
    and only it is fixed by sealing again.
    """
    now = _now() if now is None else now
    p = capsule_path(session_id, state_dir)
    row = sealed_receipt(session_id, state_dir)
    if row is None:
        return {"verdict": "NO_CAPSULE", "capsule": str(p), "sha256": None, "age_s": None,
                "reasons": ["no capsule_sealed receipt for this session"]}
    reasons: list[str] = []
    if row.get("safe_to_forget") != "SAFE_TO_FORGET":
        reasons += [f"the seal itself refused: {r}" for r in (row.get("refusals") or ["unstated"])]
    receipt = row.get("capsule") or {}
    want = receipt.get("sha256")
    if not receipt.get("sealed") or not want:
        reasons.append("the recorded receipt carries no sealed hash")
    else:
        try:
            if hashlib.sha256(p.read_bytes()).hexdigest() != want:
                reasons.append("capsule on disk is not the bytes that were sealed")
        except OSError as exc:
            reasons.append(f"capsule unreadable: {exc.__class__.__name__}")
    # Freshness. The receipt authorises destroying the state it was taken over; work that
    # landed afterwards was never captured, so an old capsule is not a licence for it.
    try:
        age = now - p.stat().st_mtime
    except OSError:
        age = None
    if age is None:
        reasons.append("capsule age unknown")
    elif age > max_age_s:
        reasons.append(f"capsule sealed {int(age)}s ago (limit {int(max_age_s)}s): seal again before clearing")
    if p.with_suffix(".certified").exists():
        reasons.append("capsule already certified and retired")
    return {"verdict": "SAFE_TO_FORGET" if not reasons else "REFUSED", "capsule": str(p),
            "sha256": want, "age_s": None if age is None else int(age), "reasons": reasons}


def bootstrap(capsule: dict) -> str:
    """The successor's first context: pointers and facts, never the transcript.

    Branch and HEAD are deliberately NOT printed (spec mission-capsule-rollover D3): the exam asks
    for them, and they are judged against the tree NOW, so the successor must read them from git.
    Printing the sealed values made the exam a copy test, and after a RECOMPILE a wrong one."""
    repo = capsule.get("repo") or {}
    run = capsule.get("run") if isinstance(capsule.get("run"), dict) else {}
    origin = (f"mission {run.get('mission_id')} epoch {run.get('epoch')} -> {run.get('successor_epoch')}"
              if capsule.get("kind") == "mission" else f"session {capsule.get('session_id', '?')[:8]}")
    lines = [f"[rollover] Continuing from {origin} (sealed {capsule.get('created')}).",
             f"Goal file: {(capsule.get('goal') or {}).get('path', UNKNOWN)} -- read it before acting.",
             f"Repo: {repo.get('root', UNKNOWN)} -- read its branch and HEAD from git yourself (the exam asks)."]
    if capsule.get("degraded"):
        lines.append(f"DEGRADED capsule ({capsule.get('seal_origin')}): the predecessor never handed off. "
                     "RECOVERY first: read the tree, its uncommitted changes and the goal file before trusting anything here.")
    if capsule.get("note"):
        lines.append("Predecessor's note (a claim to verify, not a fact): " + str(capsule["note"])[:1200])
    if capsule.get("summary"):
        lines.append(f"Summary: {capsule['summary']}")
    obl = capsule.get("obligations") or []
    if obl:
        lines.append("Open obligations (first is next):")
        lines += [f"  {i}. {o}" for i, o in enumerate(obl, 1)]
    dirty = repo.get("dirty") if isinstance(repo.get("dirty"), list) else []
    if dirty:
        lines.append(f"Dirty at seal ({len(dirty)}; some may be other panes'): " + ", ".join(dirty[:8]))
    lines.append(f"Handoff: {(capsule.get('handoff') or {}).get('path', UNKNOWN)}")
    text = "\n".join(lines)
    return text if len(text) <= BOOTSTRAP_MAX_CHARS else text[:BOOTSTRAP_MAX_CHARS - 20] + "\n[...truncated]"


# -------------------------------------------------------------------------- policy
SHARE_WOULD, SHARE_CONTINUE = 0.75, 0.25   # declared policy parameters (plan ccp-s16 Q5), not quantities


def _share(values: list, x: float) -> float:
    """Share of observed remaining-work values that still pay back a fresh epoch at break-even x."""
    import bisect
    return (len(values) - bisect.bisect_left(values, x)) / len(values)


def _economics(n_star: float, growth: int, ev: dict, reh: Optional[dict]) -> dict:
    """Interval judgement (plan ccp-s16 §16.1 D1). Robust only when the WHOLE plausible range agrees:
    ROLLOVER needs the share >= SHARE_WOULD even at the pessimistic break-even n* + C/G (C = measured
    rehydration, an upper bound); CONTINUE needs the share <= SHARE_CONTINUE even at the optimistic n*.
    Anything between is UNDETERMINED, and an unknown horizon is UNKNOWN -- never the old 30."""
    vals = ev.get("values") if ev.get("basis") == "MEASURED_PRIOR" else None
    if not vals:
        return {"economics": UNKNOWN, "reason": f"horizon unknown ({ev.get('reason') or ev.get('basis')})"}
    c = reh.get("tokens") if isinstance(reh, dict) and str(reh.get("basis", "")).startswith("UPPER_BOUND") else None
    n_hi = round(n_star + c / growth, 1) if isinstance(c, (int, float)) else None
    s_lo = round(_share(vals, n_star), 3)
    s_hi = round(_share(vals, n_hi), 3) if n_hi is not None else None
    out = {"horizon_n": len(vals), "share_at_breakeven": s_lo, "breakeven_calls_hi": n_hi,
           "share_at_breakeven_hi": s_hi, "rehydration_basis": (reh or {}).get("basis", UNKNOWN),
           "rehydration_tokens": c}
    if s_hi is not None and s_hi >= SHARE_WOULD:
        return {**out, "economics": "ROBUST_ROLLOVER",
                "reason": f"robust: {s_hi:.0%} of the prior pays back even at {n_hi} calls (rehydration incl.)"}
    if s_lo <= SHARE_CONTINUE:
        return {**out, "economics": "ROBUST_CONTINUE",
                "reason": f"continue: only {s_lo:.0%} of the prior reaches break-even {n_star} calls"}
    why = "rehydration unknown" if n_hi is None else f"{s_hi:.0%} at {n_hi} .. {s_lo:.0%} at {n_star} calls"
    return {**out, "economics": "UNDETERMINED", "reason": f"economics undetermined: {why}"}


def decide(usage: dict, capsule_bytes: int, boundary: bool, used_pct: Optional[float],
           ratio: dict, pressure_pct: float = 70.0, horizon=HORIZON_CALLS,
           rehydration: Optional[dict] = None) -> dict:
    """Deterministic, explainable. Tokens only; N* in future calls, UNKNOWN when unpriced.

    `horizon` is either an int (the ESTIMATE constant, or one value of a replay sweep) or an
    evidence dict from rollover_replay.build_prior; with evidence, only ROBUST_ROLLOVER rolls
    (plan ccp-s16 §16.1 Q2: undetermined or unknown economics never ask). Pure: callers load."""
    if usage.get("state") != "OK":
        return {"would_rollover": False, "reason": f"usage {usage.get('reason')}", "breakeven_calls": None}
    ev = horizon if isinstance(horizon, dict) else None
    boot = max(1, capsule_bytes // 4)          # ESTIMATE: ~4 chars per token
    fresh = usage["floor"] + boot
    growth = usage["resident"] - fresh
    n_star = None
    if ratio.get("state") == "OK" and growth > 0:
        n_star = round(fresh * (ratio["write"] - ratio["read"]) / (growth * ratio["read"]), 1)
    out = {"resident": usage["resident"], "floor": usage["floor"], "bootstrap_est": boot,
           "growth_above_fresh": growth, "breakeven_calls": n_star,
           "horizon_calls": None if ev else horizon,
           "horizon_basis": ev.get("basis", UNKNOWN) if ev else "ESTIMATE", "boundary": boundary,
           "used_pct": used_pct, "saving_per_call_tokens": max(0, growth)}
    if ev:
        out["horizon_computed_at"] = ev.get("computed_at")
    if used_pct is not None and used_pct >= pressure_pct:
        return {**out, "would_rollover": True, "reason": f"pressure: {used_pct}% >= {pressure_pct}%"}
    if growth < MIN_GROWTH_TOKENS:
        return {**out, "would_rollover": False, "reason": f"growth {growth:,} < {MIN_GROWTH_TOKENS:,}"}
    if n_star is None:
        return {**out, "would_rollover": False, "reason": f"break-even unknown ({ratio.get('reason')})"}
    if ev:
        econ = _economics(n_star, growth, ev, rehydration)
        out.update(econ)
        if econ["economics"] != "ROBUST_ROLLOVER":
            return {**out, "would_rollover": False}
        if not boundary:
            return {**out, "would_rollover": False, "reason": "robust, but not at a work boundary"}
        return {**out, "would_rollover": True, "reason": econ["reason"] + " at a boundary"}
    if n_star > horizon:
        return {**out, "would_rollover": False, "reason": f"break-even {n_star} calls > horizon {horizon}"}
    if not boundary:
        return {**out, "would_rollover": False, "reason": "worth it, but not at a work boundary"}
    return {**out, "would_rollover": True, "reason": f"break-even {n_star} calls <= {horizon} at a boundary"}


def at_boundary(repo: dict, start_head: Optional[str]) -> bool:
    """A commit landed this session, or the tracked tree is clean."""
    if repo.get("state") != "OK":
        return False
    if isinstance(repo.get("dirty"), list) and not repo["dirty"]:
        return True
    return bool(start_head and isinstance(repo.get("head"), str) and repo["head"] != start_head)


# ------------------------------------------------------------------------ successor
CLAIM_LOCK_TIMEOUT_S = 2.0
CLAIM_TORN_S = 60                # an unreadable claim this old is a crash between create and write


class _ClaimLock:
    """Exclusive sidecar lock around every claim REWRITE (renew, takeover, refresh note). The first
    claim is an O_EXCL create and needs none. Same idiom as ledger(): never deleted, released by the
    OS if the holder dies. `ok` is False when it could not be taken in time -- callers refuse."""

    def __init__(self, marker: Path):
        self.path, self.fd, self.ok = marker.with_suffix(".claimlock"), None, False

    def __enter__(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.fd = os.open(str(self.path), os.O_RDWR | os.O_CREAT)
            deadline = time.time() + CLAIM_LOCK_TIMEOUT_S
            while not _lock_try(self.fd):
                if time.time() > deadline:
                    return self
                time.sleep(0.005)
            self.ok = True
        except OSError:
            self.ok = False
        return self

    def __exit__(self, *exc):
        if self.fd is not None:
            try:
                if self.ok and sys.platform == "win32":
                    import msvcrt
                    os.lseek(self.fd, 0, os.SEEK_SET)
                    msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            os.close(self.fd)
        return False


def read_claim(session_id: str, state_dir: Optional[Path] = None) -> Optional[dict]:
    """The claim record, or None when absent or unreadable. A pre-lease claim ({claimant, ts}) is
    returned as written: its missing generation and lease are judged by _claim_stale."""
    try:
        rec = json.loads(capsule_path(session_id, state_dir).with_suffix(".claim").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None


def _holder_dead(host: Optional[dict], alive=None) -> Optional[bool]:
    """True when the claimant's claude process is provably gone (pid dead, or the pid now belongs to
    a process with another start time); None when that cannot be told. Never a false dead from an
    unanswered question: None keeps the claim, only the lease then frees it."""
    if not isinstance(host, dict) or not str(host.get("pid") or "").isdigit():
        return None
    pid = int(host["pid"])
    if alive is None:
        try:
            import gsd_long_run as lr
            alive = lr._pid_alive
        except Exception:  # noqa: BLE001 -- no liveness reader: unknown, not dead
            return None
    state = alive(pid)
    if state is False:
        return True
    if state is True and host.get("proc_start"):
        d = Path(os.environ.get("CPP_CLAUDE_SESSIONS_DIR") or (Path.home() / ".claude" / "sessions"))
        try:
            rec = json.loads((d / f"{pid}.json").read_text(encoding="utf-8-sig"))
            now_start = rec.get("procStart") if isinstance(rec, dict) else None
        except (OSError, ValueError):
            return None
        if now_start and str(now_start) != str(host["proc_start"]):
            return True          # the pid was recycled: the holder is gone
        return False
    return None


def _claim_stale(cur: Optional[dict], marker: Path, now: float, alive=None) -> tuple[bool, str]:
    try:
        age = now - marker.stat().st_mtime
    except OSError:
        age = None
    if cur is None:
        return (age is not None and age > CLAIM_TORN_S), "claim record unreadable (torn create)"
    lease = cur.get("lease_until")
    if isinstance(lease, (int, float)):
        if now > lease:
            return True, f"lease expired {int(now - lease)}s ago"
    elif age is not None and age > CLAIM_LEASE_S:
        return True, f"pre-lease claim {int(age)}s old"
    if _holder_dead(cur.get("host"), alive):
        return True, "holder process is gone"
    return False, ""


def claim(session_id: str, claimant: str, state_dir: Optional[Path] = None, *,
          host: Optional[dict] = None, now: Optional[float] = None, lease_s: float = CLAIM_LEASE_S,
          alive=None) -> dict:
    """One successor per capsule (spec I3). First claim: O_EXCL create. The holder renews its
    lease by claiming again. Another claimant is refused, naming the holder -- unless the claim is
    stale (lease expired, or its process provably dead), in which case it is TAKEN OVER under the
    claim lock with generation + 1. The old holder is then fenced: certify checks the holder, so
    a successor that died after claiming no longer bricks the transition (D5, 2026-10-03)."""
    marker = capsule_path(session_id, state_dir).with_suffix(".claim")
    now = _now() if now is None else now
    fresh = {"claimant": claimant, "ts": _iso(now), "at": now, "generation": 1,
             "lease_until": now + lease_s, "host": host}
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        fd = None
    if fd is not None:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(fresh, fh)
        return {"claimed": True, "holder": claimant, "generation": 1}
    with _ClaimLock(marker) as lk:
        if not lk.ok:
            return {"claimed": False, "holder": UNKNOWN, "why": "claim lock busy"}
        cur = read_claim(session_id, state_dir)
        holder = (cur or {}).get("claimant", UNKNOWN)
        gen = int((cur or {}).get("generation") or 1)
        if holder == claimant:
            _atomic_write(marker, json.dumps({**cur, "lease_until": now + lease_s}).encode("utf-8"))
            return {"claimed": True, "holder": claimant, "generation": gen}
        if marker.with_suffix(".certified").exists():
            return {"claimed": False, "holder": holder, "generation": gen, "why": "already certified"}
        stale, why = _claim_stale(cur, marker, now, alive)
        if not stale:
            return {"claimed": False, "holder": holder, "generation": gen}
        _atomic_write(marker, json.dumps({**fresh, "generation": gen + 1, "took_over_from": holder,
                                          "takeover_reason": why}).encode("utf-8"))
        return {"claimed": True, "holder": claimant, "generation": gen + 1,
                "took_over_from": holder, "takeover_reason": why}


def note_refresh(session_id: str, claimant: str, verdict: str, state_dir: Optional[Path] = None,
                 now: Optional[float] = None, snapshot: Optional[dict] = None) -> bool:
    """Record on the claim that THIS generation's holder refreshed reality, and WHAT it saw. certify
    requires it (spec I4) and judges the answers against that snapshot (audit G17): judging against
    HEAD at certify time made a sibling pane's commit between the two steps fail a correct answer."""
    marker = capsule_path(session_id, state_dir).with_suffix(".claim")
    with _ClaimLock(marker) as lk:
        if not lk.ok:
            return False
        cur = read_claim(session_id, state_dir)
        if not cur or cur.get("claimant") != claimant:
            return False
        cur.update(refresh=verdict, refreshed_at=_now() if now is None else now,
                   refreshed_generation=int(cur.get("generation") or 1), snapshot=snapshot)
        _atomic_write(marker, json.dumps(cur).encode("utf-8"))
        return True


# ------------------------------------------------------------- pre-certification markers
# One authority for "certified" (audit G25): this module creates the marker the mutation guard
# (hooks/capsule_mutation_guard.js) reads, and flips it in certify_flow. One file per MISSION,
# naming the worker the supervisor launched, so the guard can match a session whose bg id is not
# bound yet by the host registry's `name` (audit G7).
def precert_path(mission_id: str, state_dir: Optional[Path] = None) -> Path:
    return (state_dir or STATE_DIR) / "precert" / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', mission_id)}.json"


def precert_write(mission_id: str, fields: dict, state_dir: Optional[Path] = None) -> dict:
    """Create or update this mission's marker (atomic: the guard never reads a torn one)."""
    p = precert_path(mission_id, state_dir)
    try:
        cur = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cur = {}
    rec = {**(cur if isinstance(cur, dict) else {}), **fields, "mission_id": mission_id, "updated_at": _now()}
    _atomic_write(p, json.dumps(rec, sort_keys=True).encode("utf-8"))
    return rec


def precert_read(mission_id: str, state_dir: Optional[Path] = None) -> Optional[dict]:
    try:
        rec = json.loads(precert_path(mission_id, state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) else None


def refresh(capsule: dict, cwd: str) -> dict:
    """Reality before authority: the successor compares the capsule with the tree NOW.

    The tree is the capsule's recorded repo root, not the successor's cwd: a session that opened
    in one checkout and `cd`-ed into a worktree is matched by session_cwd, and reading the cwd then
    compared the worktree's capsule against the other checkout (f3b5ff1d, 2026-09-30: a false
    RECOMPILE on root/branch/head/dirty while the worktree was exactly as sealed)."""
    then = capsule.get("repo") or {}
    sealed_root = then.get("root") if isinstance(then.get("root"), str) else ""
    if sealed_root and not Path(sealed_root).is_dir():
        return {"verdict": "RECOMPILE", "divergences": [f"root gone: {sealed_root}"], "now": {}}
    now = repo_facts(sealed_root or cwd)
    if sealed_root and _pathkey(cwd) != _pathkey(sealed_root):
        now["elsewhere"] = sealed_root
    if now.get("state") != "OK" or then.get("state") != "OK":
        return {"verdict": UNKNOWN, "divergences": ["repo unreadable now or at seal"], "now": now}
    div = []
    for k in ("root", "branch", "head"):
        if now.get(k) != then.get(k):
            div.append(f"{k}: sealed {str(then.get(k))[:40]} -> now {str(now.get(k))[:40]}")
    if isinstance(now.get("dirty"), list) and isinstance(then.get("dirty"), list):
        moved = sorted(set(now["dirty"]) ^ set(then["dirty"]))
        if moved:
            div.append(f"dirty set moved by {len(moved)}: " + ", ".join(moved[:6]))
    gp = (capsule.get("goal") or {}).get("path")
    if gp and not Path(gp).is_file():
        div.append(f"goal file gone: {gp}")
    return {"verdict": "CONTINUE" if not div else "RECOMPILE", "divergences": div, "now": now}


def obligations_now(capsule: dict) -> list[str]:
    """The open obligations as the durable sources say NOW (spec I4). An interactive capsule whose
    obligations came from its goal file re-reads that file; one whose obligations were stated
    explicitly or taken from its own handoff has no live source and keeps them. A mission capsule's
    obligations come from GSD and are passed in by the adapter (`reality["obligations"]`)."""
    if capsule.get("obligations_source") == "goal file":
        return obligations_from((capsule.get("goal") or {}).get("path"))
    return list(capsule.get("obligations") or [])


def reality_now(capsule: dict, cwd: str = "") -> dict:
    """What the exam is judged against: the capsule's own tree as it is now, and its obligations."""
    root = (capsule.get("repo") or {}).get("root")
    repo = repo_facts(root if isinstance(root, str) and Path(root).is_dir() else (cwd or "."))
    return {"repo": repo, "obligations": obligations_now(capsule)}


def exam(capsule: dict, reality: Optional[dict] = None) -> list[dict]:
    """The questions, with the answer each is judged against. With `reality` (certify) the branch,
    HEAD and next obligation are those of the tree NOW; without it (resumable) the sealed values.

    Judging against the seal was D2: after a RECOMPILE, quoting the stale HEAD certified."""
    repo = (reality or {}).get("repo") if reality is not None else (capsule.get("repo") or {})
    repo = repo if isinstance(repo, dict) and (reality is None or repo.get("state") == "OK") else {}
    obl = (reality or {}).get("obligations") if reality is not None else capsule.get("obligations")
    head = repo.get("head") if isinstance(repo.get("head"), str) else ""
    branch = repo.get("branch") if isinstance(repo.get("branch"), str) else ""
    items = [{"key": "goal", "q": "Which file is the goal?", "a": Path((capsule.get("goal") or {}).get("path") or "").name},
             {"key": "branch", "q": "Which branch is checked out in the capsule's repo NOW?", "a": branch},
             {"key": "head", "q": "What is that repo's HEAD NOW (first 7)?", "a": head[:7]},
             {"key": "next", "q": "What is the next open obligation, from the goal file?", "a": (obl or [""])[0]}]
    if capsule.get("degraded"):
        dirty = repo.get("dirty") if isinstance(repo.get("dirty"), list) else None
        items.append({"key": "dirty", "q": "How many tracked paths are uncommitted in that repo NOW? (RECOVERY)",
                      "a": "" if dirty is None and reality is not None else str(len(dirty or []))})
    return items


def _norm(s) -> str:
    """Compare what was meant, not how a shell delivered it (audit G16): obligations carry markdown
    and backticks, and inside PowerShell double quotes a backtick is the escape character, so the
    same text arrives altered. Backticks, asterisks and quotes are dropped; whitespace collapses."""
    s = re.sub(r"[`*\"']", "", str(s or ""))
    return re.sub(r"\s+", " ", s).strip().lower()


NEXT_MIN_CHARS = 12


def _matches(key: str, want: str, got: str) -> bool:
    if not want or not got:
        return False
    if key == "head":
        return len(got) >= 7 and got[:len(want)] == want
    if key != "next":
        return got == want
    # D4: "any substring" passed on the answer "a". Containing the whole obligation is fine; a
    # fragment of it must be a real fragment, not a letter.
    return got == want or want in got or (got in want and len(got) >= max(NEXT_MIN_CHARS, len(want) // 3))


def certify(capsule: dict, answers: dict, reality: Optional[dict] = None) -> dict:
    """RESUME_CERTIFIED only when every answer matches reality NOW. `reality` defaults to a fresh
    read of the capsule's tree; an unreadable tree fails the questions that need it."""
    reality = reality_now(capsule) if reality is None else reality
    wrong = []
    for item in exam(capsule, reality):
        want, got = _norm(item["a"]), _norm(answers.get(item["key"]))
        if not _matches(item["key"], want, got):
            wrong.append({"key": item["key"], "expected": item["a"] or "UNREADABLE NOW", "given": answers.get(item["key"])})
    return {"verdict": "RESUME_CERTIFIED" if not wrong else "RESUME_FAILED", "wrong": wrong}


# -------------------------------------------------------------------------- ledger
LEDGER_LOCK_TIMEOUT_S = 2.0     # bounded well inside the 20 s foreground gate: a stuck holder costs a row


def _lock_try(fd: int) -> bool:
    try:
        if sys.platform == "win32":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _ledger_failed(base: Path, event: str, why: str) -> None:
    """A dropped row leaves its own uniquely named file: no shared append, so no race to lose it."""
    try:
        d = base / "ledger-failures"
        d.mkdir(parents=True, exist_ok=True)
        name = f"{time.time_ns()}-{os.getpid()}.json"
        (d / name).write_text(json.dumps({"ts": _iso(), "event": event, "why": why}), encoding="utf-8")
    except OSError:
        pass
    print(f"rollover ledger: row {event!r} NOT written ({why})", file=sys.stderr)


def ledger(event: str, state_dir: Optional[Path] = None, **fields) -> bool:
    """Append one row under an exclusive lock. Measured 2026-10-03 (plan ccp-s16 F6): Windows
    append is seek-to-end + write, so concurrent sessions OVERWROTE each other's rows (6 tails
    left in the live ledger; the old shape loses 114-271 of 900 rows in test_rollover_ledger_race;
    O_APPEND + one os.write lost as many in a scratch run). The lock is a sidecar file, never
    deleted, released by the OS if the holder dies (idiom of gsd_mission._Lock); the ledger itself
    is not locked, because Windows locks are mandatory and would block `sealed_receipt` readers.
    On timeout or OSError the row is dropped and REPORTED (returns False, ledger-failures/ file);
    it is never written torn and this function never raises -- callers that need the row (the
    capsule_sealed writers) check the return."""
    base = state_dir or STATE_DIR
    path = base / "rollover-ledger.jsonl"
    data = (json.dumps({"ts": _iso(), "event": event, **fields}, ensure_ascii=False) + "\n").encode("utf-8")
    fd, locked = None, False
    try:
        base.mkdir(parents=True, exist_ok=True)
        fd = os.open(base / "rollover-ledger.lock", os.O_RDWR | os.O_CREAT)
        deadline = time.time() + LEDGER_LOCK_TIMEOUT_S
        while not _lock_try(fd):
            if time.time() > deadline:
                _ledger_failed(base, event, f"lock busy > {LEDGER_LOCK_TIMEOUT_S}s")
                return False
            time.sleep(0.005)
        locked = True
        with open(path, "ab") as fh:
            fh.write(data)
        return True
    except OSError as exc:
        _ledger_failed(base, event, f"{exc.__class__.__name__}: {exc}")
        return False
    finally:
        if fd is not None:
            try:
                if locked and sys.platform == "win32":
                    import msvcrt
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)   # explicit: close-release can lag
            except OSError:
                pass
            os.close(fd)      # closing releases the lock on every platform


def resumable(capsule: dict) -> list[str]:
    """Why no successor could ever certify this capsule; empty means it can be resumed.

    certify() refuses an exam item whose expected answer is empty, so a capsule sealed with no
    goal or no obligation is uncertifiable by construction. The shadow seals such capsules into
    the same directory as /kclear. Offering one would make the successor claim it, which locks
    out every other successor, and then fail the exam with no way to pass. Measured 2026-09-28:
    capsule gsdlr-92a0350ee055, leaked by a test run, was claimed that way."""
    return [f"{item['key']} was never recorded" for item in exam(capsule) if not _norm(item["a"])]


def _pathkey(p) -> str:
    s = str(p or "").strip()
    return os.path.normcase(os.path.normpath(s)) if s else ""


def capsule_is_here(cap: dict, cwd: str) -> bool:
    """True when this session's cwd is the capsule's cwd OR the repo root it recorded.

    The seal records the SHELL cwd, which drifts: measured 2026-09-29, capsule ea5c9025 was
    sealed from GEO-audit\\scripts after a `cd`, the successor opened at GEO-audit, and an exact
    cwd compare hid a capsule sealed 38 s earlier -- no card, no autotype, and /kresume exit 4.
    The repo root is the stable identity. Not "any ancestor": a capsule from a nested repo must
    not surface in its parent.

    Neither covers a `cd` into ANOTHER repo (357823a8, 2026-09-29): the capsule's session_cwd,
    the session's own directory from session_cwd(), is where its successor opens, so it
    matches too. Capsules sealed before that field existed keep the two-key rule."""
    here = _pathkey(cwd)
    if not here:
        return False
    repo = cap.get("repo") if isinstance(cap.get("repo"), dict) else {}
    keys = (_pathkey(cap.get("session_cwd")), _pathkey(cap.get("cwd")), _pathkey(repo.get("root")))
    return here in {k for k in keys if k}


def same_host(cap: dict, host: Optional[dict]) -> bool:
    """True when the capsule was sealed by the claude process `host` names (pid AND start)."""
    h = cap.get("host") if isinstance(cap.get("host"), dict) else None
    return bool(host and h and h.get("pid") == host.get("pid") and h.get("proc_start")
                and str(h.get("proc_start")) == str(host.get("proc_start")))


def newest_capsule(cwd: str, state_dir: Optional[Path] = None, exclude: str = "",
                   skipped: Optional[list] = None, host: Optional[dict] = None) -> Optional[dict]:
    """The capsule a successor here adopts: the newest one sealed by ITS OWN claude process
    (its predecessor, see host_identity) when one exists, else the newest here. The fallback
    keeps a restart in a new process, and capsules sealed before `host` was recorded,
    resumable exactly as before."""
    d = (state_dir or STATE_DIR) / "capsules"
    best = None
    for p in sorted(d.glob("*.json"), key=lambda q: q.stat().st_mtime, reverse=True) if d.is_dir() else []:
        if p.with_suffix(".certified").exists() or _now() - p.stat().st_mtime > CAPSULE_MAX_AGE_S:
            continue
        try:
            cap = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if cap.get("schema") != SCHEMA or cap.get("session_id") == exclude:
            continue
        if not capsule_is_here(cap, cwd):
            continue
        if resumable(cap):
            if skipped is not None:
                skipped.append(cap.get("session_id"))
            continue
        if same_host(cap, host):
            return cap
        if best is None:
            best = cap
        if host is None:
            break
    return best


# ----------------------------------------------------------------------------- CLI
def observe(session_id: str, cwd: str, transcript: Optional[str], used_pct: Optional[float],
            tier: str = "", start_head: Optional[str] = None, state_dir: Optional[Path] = None) -> dict:
    """SHADOW: every step of a rollover except the destruction, recorded."""
    cap = compile_capsule(session_id, cwd, transcript)
    receipt = seal(cap, state_dir)
    comp = completeness(cap)
    stf = safe_to_forget(receipt, comp)
    usage = cap["usage"]
    ev, reh = horizon_evidence(state_dir)
    dec = decide(usage, len(bootstrap(cap)), at_boundary(cap["repo"], start_head), used_pct,
                 price_ratio(usage.get("model", "")) if usage.get("state") == "OK" else _unknown("no usage"),
                 horizon=ev, rehydration=reh)
    row = {"session_id": session_id, "cwd": cwd, "tier": tier, "mode": "shadow",
           "decision": dec, "capsule": receipt, "completeness": comp, "safe_to_forget": stf["verdict"],
           "refusals": stf["reasons"], "obligations": len(cap.get("obligations") or []),
           "bootstrap_chars": len(bootstrap(cap))}
    ledger("shadow_candidate", state_dir, **row)
    return row


PRIOR_FILE = "horizon-prior.json"           # written by tools/rollover_replay.py prior --write
PRIOR_SCHEMA = "rollover-horizon-prior-v1"


def horizon_evidence(state_dir: Optional[Path] = None, now: Optional[float] = None) -> tuple[dict, Optional[dict]]:
    """(horizon evidence, rehydration evidence) for decide(). Missing, unreadable, foreign-schema or
    expired priors are UNKNOWN with the reason -- decide then never asks (plan ccp-s16 §16.1 D1b);
    the old constant is never substituted. The artifact is refreshed by rollover_econ.py."""
    p = (state_dir or STATE_DIR) / PRIOR_FILE
    try:
        ev = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"basis": UNKNOWN, "reason": "no prior artifact"}, None
    except (OSError, ValueError) as exc:
        return {"basis": UNKNOWN, "reason": f"prior unreadable: {exc.__class__.__name__}"}, None
    if not isinstance(ev, dict) or ev.get("schema") != PRIOR_SCHEMA:
        return {"basis": UNKNOWN, "reason": "prior has a foreign schema"}, None
    exp = ev.get("expires_at")
    if not isinstance(exp, (int, float)) or exp < (_now() if now is None else now):
        return {"basis": UNKNOWN, "reason": "prior expired", "stale": True}, None
    return ev, ev.get("rehydration")


def _answers(a) -> Optional[dict]:
    """One flag per answer is the shell-safe form: PowerShell 5.1 strips the double quotes out of
    a JSON argument to a native exe (measured 2026-09-28: every field arrived as None). --answers
    JSON stays accepted; if it does not parse, that is None -- "could not read your answers" --
    never an empty dict that reads as "you answered nothing"."""
    got = {k: getattr(a, k) for k in ("goal", "branch", "head", "next") if getattr(a, k, None)}
    if a.answers:
        try:
            parsed = json.loads(a.answers)
        except ValueError:
            return None
        if not isinstance(parsed, dict):
            return None
        got = {**parsed, **got}
    return got


def claim_holder(session_id: str, state_dir: Optional[Path] = None) -> Optional[str]:
    marker = capsule_path(session_id, state_dir).with_suffix(".claim")
    try:
        return json.loads(marker.read_text(encoding="utf-8")).get("claimant")
    except (OSError, ValueError):
        return None


def _key(cap: dict) -> str:
    return cap.get("capsule_key") or cap.get("session_id") or ""


def resume_flow(cap: dict, claimant: str, cwd: str, state_dir: Optional[Path] = None,
                certify_cmd: Optional[str] = None, obligations: Optional[list] = None) -> int:
    """Successor side, shared by /kresume and the mission adapter: refuse an uncertifiable capsule
    BEFORE claiming it (I5), claim it (I3), refresh reality and record that refresh on the claim
    (I4), then print the bootstrap and the questions -- never their answers (D3).
    Exit 0 claimed, 4 not resumable, 5 claimed by another / lost the claim."""
    key = _key(cap)
    why = resumable(cap)
    if why:
        # Refused BEFORE the claim: a claim on an uncertifiable capsule only locks others out.
        print(f"NOT RESUMABLE: capsule {key} cannot be certified -- {'; '.join(why)}.")
        ledger("resume_not_resumable", state_dir, session_id=key, claimant=claimant, reasons=why)
        return 4
    cl = claim(key, claimant, state_dir, host=host_identity())
    if not cl["claimed"]:
        print(f"REFUSED: capsule {key[:40]} is already claimed by {cl['holder']}"
              + (f" ({cl['why']})" if cl.get("why") else "") + ".")
        ledger("claim_refused", state_dir, session_id=key, claimant=claimant, holder=cl["holder"],
               why=cl.get("why"))
        return 5
    if cl.get("took_over_from"):
        ledger("claim_taken_over", state_dir, session_id=key, claimant=claimant,
               previous=cl["took_over_from"], reason=cl.get("takeover_reason"), generation=cl["generation"])
    rf = refresh(cap, cwd)
    now = rf.get("now") or {}
    snapshot = {"state": now.get("state", UNKNOWN), "root": now.get("root"),
                "branch": now.get("branch") if isinstance(now.get("branch"), str) else None,
                "head": now.get("head") if isinstance(now.get("head"), str) else None,
                "dirty": now.get("dirty") if isinstance(now.get("dirty"), list) else None,
                "obligations": list(obligations) if obligations is not None else obligations_now(cap)}
    if not note_refresh(key, claimant, rf["verdict"], state_dir, snapshot=snapshot):
        print(f"REFUSED: the claim on {key[:40]} changed hands while refreshing (or its lock is busy). "
              "Run resume again; do not mutate.")
        ledger("claim_lost_during_refresh", state_dir, session_id=key, claimant=claimant)
        return 5
    ledger("successor_claimed", state_dir, session_id=key, claimant=claimant, generation=cl["generation"],
           refresh=rf["verdict"], divergences=rf["divergences"])
    print(bootstrap(cap))
    print(f"\nReality refresh: {rf['verdict']}")
    if rf["now"].get("elsewhere"):
        print(f"  (checked the capsule's repo, not this cwd -- work there: {rf['now']['elsewhere']})")
    for d in rf["divergences"]:
        # Name WHAT moved, not its value: "head: sealed X -> now Y" printed the exam's answer
        # (caught by V-CAP2-BOOTSTRAP-NO-HEAD). The values stay in the ledger row above.
        k = d.split(":", 1)[0]
        print(f"  - {k} moved since the seal" if k in ("root", "branch", "head") else f"  - {d}")
    if rf["verdict"] != "CONTINUE":
        print("RECOMPILE: the tree moved since the seal. Do not continue from the capsule as written: "
              "re-derive the next step from the goal file and the tree; the exam is judged against them NOW.")
    print("\nResume exam -- answer from the tree and the goal file, before any mutation, then run:")
    print("  " + (certify_cmd or f"python {Path(__file__).as_posix()} certify --from {key} --claimant {claimant} "
                  "--goal <file> --branch <b> --head <7> --next \"<first obligation>\""))
    for item in exam(cap):
        print(f"  [{item['key']}] {item['q']}")
    return 0


def _snapshot_reality(snap: dict) -> dict:
    repo = {"state": "OK" if snap.get("head") else UNKNOWN, "root": snap.get("root"),
            "branch": snap.get("branch"), "head": snap.get("head"), "dirty": snap.get("dirty")}
    return {"repo": repo, "obligations": snap.get("obligations") or []}


def _flip_precert(cap: dict, key: str, claimant: str, state_dir: Optional[Path]) -> Optional[str]:
    """Lift the mutation guard for a mission successor -- only the marker naming THIS capsule.
    Returns why it was not lifted, or None."""
    if cap.get("kind") != "mission":
        return None
    mid = ((cap.get("run") or {}).get("mission_id")) or ""
    mk = precert_read(mid, state_dir)
    if not mk:
        return None      # nothing was locked, so there is nothing to lift (the guard reads only markers)
    if mk.get("capsule_key") != key:
        return f"the marker names capsule {mk.get('capsule_key')}, not {key}"
    precert_write(mid, {"certified_at": _now(), "certified_by": claimant}, state_dir)
    return None


def certify_flow(key: str, claimant: str, answers: Optional[dict], state_dir: Optional[Path] = None) -> tuple[int, dict]:
    """Only the CURRENT generation's holder, after a refresh recorded in that generation, may
    certify (I3, I4); all of it under the claim lock, so a takeover cannot interleave (G18).
    Answers are judged against the refresh SNAPSHOT; if the tree moved since, exit 8 = refresh
    again (G17). A failure names the wrong keys, never the expected values (G15). On success the
    capsule is retired and, for a mission, the guard's marker is lifted (G25) -- idempotently, so
    a crash between the two is healed by certifying again.
    Exit 0 certified, 4 no capsule, 5 fenced / no refresh / lock busy, 6 RESUME_FAILED,
    7 answers unreadable, 8 tree moved since the refresh."""
    path = capsule_path(key, state_dir)
    if not path.is_file():
        print(f"No capsule {path}.")
        return 4, {"verdict": "NO_CAPSULE"}
    marker = path.with_suffix(".claim")
    with _ClaimLock(marker) as lk:
        if not lk.ok:
            print("REFUSED: the claim lock is busy; certify again.")
            return 5, {"verdict": "LOCK_BUSY"}
        cur = read_claim(key, state_dir) or {}
        gen = int(cur.get("generation") or 1)
        if cur.get("claimant") != claimant:
            # Fencing: only the successor that holds the claim NOW may take mutation authority.
            print(f"REFUSED: capsule is claimed by {cur.get('claimant') or 'nobody'}, not {claimant}; run resume first.")
            ledger("certify_refused", state_dir, session_id=key, claimant=claimant, holder=cur.get("claimant"))
            return 5, {"verdict": "FENCED"}
        cap = json.loads(path.read_text(encoding="utf-8"))
        if cur.get("certified_generation") == gen and path.with_suffix(".certified").exists():
            why = _flip_precert(cap, key, claimant, state_dir)     # heal a crash after the retire
            print("RESUME_CERTIFIED (already) -- " + (why or "authority restored") + ".")
            return (0 if why is None else 5), {"verdict": "RESUME_CERTIFIED", "wrong": [], "marker": why}
        snap = cur.get("snapshot")
        if not cur.get("refreshed_at") or cur.get("refreshed_generation") != gen or not isinstance(snap, dict):
            print("REFUSED: no reality refresh is recorded for this claim; run resume first.")
            ledger("certify_refused", state_dir, session_id=key, claimant=claimant, holder=claimant,
                   why="no refresh in this claim generation")
            return 5, {"verdict": "NO_REFRESH"}
        if answers is None:
            print("UNREADABLE: --answers is not a JSON object (PowerShell strips its quotes); "
                  "pass --goal/--branch/--head/--next instead. Nothing judged.")
            return 7, {"verdict": "UNREADABLE"}
        # The tree is compared with the refresh BEFORE anything is judged (review MEDIUM, 2026-10-03):
        # judged first, a successor that read the NEW head got exit 6 "re-read and retry" for ever,
        # and a match on the old head wrote a resume_certified row that rollover_replay counts.
        now = repo_facts(snap.get("root") or ".") if snap.get("root") else {}
        if now.get("head") != snap.get("head") or now.get("branch") != snap.get("branch"):
            print("REFRESH AGAIN: the tree moved since your resume (another commit or checkout). "
                  "Run resume again and re-answer; nothing was judged or certified.")
            ledger("certify_stale_refresh", state_dir, session_id=key, claimant=claimant, generation=gen)
            return 8, {"verdict": "STALE_REFRESH"}
        res = certify(cap, answers, _snapshot_reality(snap))
        ledger(res["verdict"].lower(), state_dir, session_id=key, claimant=claimant, generation=gen,
               wrong=[w["key"] for w in res["wrong"]])
        if res["verdict"] != "RESUME_CERTIFIED":
            print("RESUME_FAILED -- re-read the goal file and the tree; do not mutate yet. Wrong: "
                  + ", ".join(w["key"] for w in res["wrong"]))
            return 6, res
        _atomic_write(marker, json.dumps({**cur, "certified_generation": gen}).encode("utf-8"))
        _atomic_write(path.with_suffix(".certified"), _iso().encode("utf-8"))
        why = _flip_precert(cap, key, claimant, state_dir)
    if why:
        ledger("precert_not_lifted", state_dir, session_id=key, claimant=claimant, why=why)
        print(f"RESUME_CERTIFIED, but mutation authority was NOT restored: {why}.")
        return 5, {**res, "marker": why}
    print("RESUME_CERTIFIED -- the capsule is retired; continue with the first obligation.")
    return 0, res


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sh = sub.add_parser("shadow")
    sh.add_argument("--session", required=True)
    sh.add_argument("--cwd", default=os.getcwd())
    sh.add_argument("--transcript")
    sh.add_argument("--used-pct", type=float)
    sh.add_argument("--tier", default="")
    se = sub.add_parser("seal")
    se.add_argument("--session", default=current_session())
    se.add_argument("--cwd", default=os.getcwd())
    se.add_argument("--transcript")
    se.add_argument("--goal")
    se.add_argument("--next", action="append", default=[])
    se.add_argument("--summary", default="")
    rs = sub.add_parser("resume")
    rs.add_argument("--cwd", default=os.getcwd())
    rs.add_argument("--claimant", default=current_session() or f"pid{os.getppid()}")
    rs.add_argument("--from", dest="from_session")
    ce = sub.add_parser("certify")
    ce.add_argument("--from", dest="from_session", required=True)
    ce.add_argument("--claimant", default=current_session() or f"pid{os.getppid()}")
    for k in ("goal", "branch", "head", "next"):
        ce.add_argument(f"--{k}")
    ce.add_argument("--answers", help='JSON {"goal","branch","head","next"} (fragile under PowerShell 5.1)')
    ga = sub.add_parser("gate")
    ga.add_argument("--session", default=current_session())
    ga.add_argument("--max-age-s", type=float, default=RESET_MAX_AGE_S)
    st = sub.add_parser("status")
    st.add_argument("--n", type=int, default=10)
    a = ap.parse_args(argv)

    if a.cmd == "shadow":
        if not shadow_enabled():
            return 0
        row = observe(a.session, a.cwd, a.transcript, a.used_pct, a.tier)
        print(json.dumps({k: row[k] for k in ("safe_to_forget", "refusals", "decision")}, indent=1))
        return 0
    if a.cmd == "gate":
        if not a.session:
            print("REFUSED: no session id (CLAUDE_CODE_SESSION_ID unset); pass --session.")
            return 2
        g = gate(a.session, max_age_s=a.max_age_s)
        print(f"capsule   {g['capsule']}")
        print(f"verdict   {g['verdict']}")
        for r in g["reasons"]:
            print(f"  refuse   {r}")
        ledger("reset_gate", session_id=a.session, verdict=g["verdict"], reasons=g["reasons"],
               age_s=g.get("age_s"))
        # Distinct codes on purpose: 3 says this session's capsule is not good enough to
        # forget, 4 says nothing was ever sealed here. A caller that collapsed them would
        # tell the Owner their work had moved when in fact nobody had captured it.
        return {"SAFE_TO_FORGET": 0, "NO_CAPSULE": 4}.get(g["verdict"], 3)
    if a.cmd == "seal":
        if not a.session:
            print("REFUSED: no session id (CLAUDE_CODE_SESSION_ID unset); pass --session.")
            return 2
        cap = compile_capsule(a.session, a.cwd, a.transcript, goal=a.goal, next_items=a.next, summary=a.summary)
        receipt, comp = seal(cap), completeness(cap)
        stf = safe_to_forget(receipt, comp)
        recorded = ledger("capsule_sealed", session_id=a.session, cwd=a.cwd, capsule=receipt,
                          safe_to_forget=stf["verdict"], refusals=stf["reasons"])
        print(f"capsule   {receipt.get('path')}  sealed={receipt.get('sealed')}  sha={str(receipt.get('sha256'))[:12]}")
        if not recorded:    # the gate reads this row: without it /clear would meet NO_CAPSULE (ccp-s16 W1)
            print(f"verdict   {UNKNOWN} -- the seal record was not written (ledger busy); seal again before /clear")
            return 3
        print(f"verdict   {stf['verdict']}")
        for r in stf["reasons"]:
            print(f"  missing  {r}")
        for w in comp["warnings"]:
            print(f"  note     {w}")
        return 0 if stf["verdict"] == "SAFE_TO_FORGET" else 3
    if a.cmd == "resume":
        skipped: list = []
        cap = (json.loads(capsule_path(a.from_session).read_text(encoding="utf-8"))
               if a.from_session and capsule_path(a.from_session).is_file()
               else newest_capsule(a.cwd, exclude=a.claimant, skipped=skipped, host=host_identity()))
        if not cap:
            print("No sealed, unretired capsule for this directory in the last 24 h. Nothing to resume.")
            if skipped:
                print(f"  ({len(skipped)} capsule(s) here were skipped as not resumable: no goal or no "
                      f"obligation was recorded, e.g. {skipped[0]})")
            return 4
        return resume_flow(cap, a.claimant, a.cwd)
    if a.cmd == "certify":
        return certify_flow(a.from_session, a.claimant, _answers(a))[0]
    if a.cmd == "status":
        path = STATE_DIR / "rollover-ledger.jsonl"
        rows = path.read_text(encoding="utf-8").splitlines()[-a.n:] if path.is_file() else []
        for r in rows:
            try:
                e = json.loads(r)
            except ValueError:
                continue
            d = e.get("decision") or {}
            print(f"{e.get('ts')} {e.get('event'):20} {str(e.get('session_id'))[:8]} "
                  f"{e.get('safe_to_forget', e.get('refresh', ''))} {d.get('reason', '')}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
