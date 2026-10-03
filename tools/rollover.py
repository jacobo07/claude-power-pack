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
STATE_DIR = Path(os.environ.get("CPP_ROLLOVER_STATE_DIR") or (Path.home() / ".claude" / "state" / "rollover"))
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
    return {
        "schema": SCHEMA, "session_id": session_id, "cwd": str(cwd), "created": _iso(),
        "session_cwd": session_cwd(session_id),
        "host": host_identity(),
        "transcript": str(tp) if tp else None,
        "repo": repo_facts(cwd), "goal": gp,
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
    if (capsule.get("goal") or {}).get("state") != "OK":
        missing.append(f"goal: {(capsule.get('goal') or {}).get('reason', 'absent')}")
    if not capsule.get("obligations"):
        missing.append("obligations: no open item found in the goal file or handoff")
    h = capsule.get("handoff") or {}
    if h.get("state") != "OK":
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
    return (state_dir or STATE_DIR) / "capsules" / f"{safe}.json"


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
    """The successor's first context: pointers and facts, never the transcript."""
    repo = capsule.get("repo") or {}
    head = repo.get("head") if isinstance(repo.get("head"), str) else UNKNOWN
    lines = [f"[rollover] Continuing from session {capsule.get('session_id', '?')[:8]} "
             f"(sealed {capsule.get('created')}).",
             f"Goal file: {(capsule.get('goal') or {}).get('path', UNKNOWN)} -- read it before acting.",
             f"Repo: {repo.get('root', UNKNOWN)} branch {repo.get('branch') if isinstance(repo.get('branch'), str) else UNKNOWN} "
             f"HEAD {head[:12]}."]
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
def decide(usage: dict, capsule_bytes: int, boundary: bool, used_pct: Optional[float],
           ratio: dict, pressure_pct: float = 70.0, horizon: int = HORIZON_CALLS) -> dict:
    """Deterministic, explainable. Tokens only; N* in future calls, UNKNOWN when unpriced."""
    if usage.get("state") != "OK":
        return {"would_rollover": False, "reason": f"usage {usage.get('reason')}", "breakeven_calls": None}
    boot = max(1, capsule_bytes // 4)          # ESTIMATE: ~4 chars per token
    fresh = usage["floor"] + boot
    growth = usage["resident"] - fresh
    n_star = None
    if ratio.get("state") == "OK" and growth > 0:
        n_star = round(fresh * (ratio["write"] - ratio["read"]) / (growth * ratio["read"]), 1)
    out = {"resident": usage["resident"], "floor": usage["floor"], "bootstrap_est": boot,
           "growth_above_fresh": growth, "breakeven_calls": n_star, "horizon_calls": horizon,
           "horizon_basis": "ESTIMATE", "boundary": boundary, "used_pct": used_pct,
           "saving_per_call_tokens": max(0, growth)}
    if used_pct is not None and used_pct >= pressure_pct:
        return {**out, "would_rollover": True, "reason": f"pressure: {used_pct}% >= {pressure_pct}%"}
    if growth < MIN_GROWTH_TOKENS:
        return {**out, "would_rollover": False, "reason": f"growth {growth:,} < {MIN_GROWTH_TOKENS:,}"}
    if n_star is None:
        return {**out, "would_rollover": False, "reason": f"break-even unknown ({ratio.get('reason')})"}
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
def claim(session_id: str, claimant: str, state_dir: Optional[Path] = None) -> dict:
    """One successor per capsule: O_EXCL create. A second claim names the holder."""
    marker = capsule_path(session_id, state_dir).with_suffix(".claim")
    try:
        fd = os.open(str(marker), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            holder = json.loads(marker.read_text(encoding="utf-8")).get("claimant")
        except (OSError, ValueError):
            holder = UNKNOWN
        return {"claimed": holder == claimant, "holder": holder}
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"claimant": claimant, "ts": _iso()}, fh)
    return {"claimed": True, "holder": claimant}


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


def exam(capsule: dict) -> list[dict]:
    repo = capsule.get("repo") or {}
    return [{"key": "goal", "q": "Which file is the goal?", "a": Path((capsule.get("goal") or {}).get("path") or "").name},
            {"key": "branch", "q": "Which branch is authoritative?", "a": repo.get("branch")},
            {"key": "head", "q": "Which HEAD was sealed (first 7)?", "a": str(repo.get("head") or "")[:7]},
            {"key": "next", "q": "What is the next open obligation?", "a": (capsule.get("obligations") or [""])[0]}]


def _norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def certify(capsule: dict, answers: dict) -> dict:
    wrong = []
    for item in exam(capsule):
        want, got = _norm(item["a"]), _norm(answers.get(item["key"]))
        ok = bool(want) and (got == want if item["key"] != "next" else (got and (got in want or want in got)))
        if not ok:
            wrong.append({"key": item["key"], "expected": item["a"], "given": answers.get(item["key"])})
    return {"verdict": "RESUME_CERTIFIED" if not wrong else "RESUME_FAILED", "wrong": wrong}


# -------------------------------------------------------------------------- ledger
def ledger(event: str, state_dir: Optional[Path] = None, **fields) -> None:
    path = (state_dir or STATE_DIR) / "rollover-ledger.jsonl"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _iso(), "event": event, **fields}, ensure_ascii=False) + "\n")
    except OSError:
        pass  # telemetry: a lost row never blocks a session


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
    dec = decide(usage, len(bootstrap(cap)), at_boundary(cap["repo"], start_head), used_pct,
                 price_ratio(usage.get("model", "")) if usage.get("state") == "OK" else _unknown("no usage"))
    row = {"session_id": session_id, "cwd": cwd, "tier": tier, "mode": "shadow",
           "decision": dec, "capsule": receipt, "completeness": comp, "safe_to_forget": stf["verdict"],
           "refusals": stf["reasons"], "bootstrap_chars": len(bootstrap(cap))}
    ledger("shadow_candidate", state_dir, **row)
    return row


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
        ledger("capsule_sealed", session_id=a.session, cwd=a.cwd, capsule=receipt,
               safe_to_forget=stf["verdict"], refusals=stf["reasons"])
        print(f"capsule   {receipt.get('path')}  sealed={receipt.get('sealed')}  sha={str(receipt.get('sha256'))[:12]}")
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
        why = resumable(cap)
        if why:
            # Refused BEFORE the claim: a claim on an uncertifiable capsule only locks others out.
            print(f"NOT RESUMABLE: capsule {cap['session_id']} cannot be certified -- {'; '.join(why)}.")
            ledger("resume_not_resumable", session_id=cap["session_id"], claimant=a.claimant, reasons=why)
            return 4
        cl = claim(cap["session_id"], a.claimant)
        if not cl["claimed"]:
            print(f"REFUSED: capsule {cap['session_id'][:8]} is already claimed by {cl['holder']}.")
            ledger("claim_refused", session_id=cap["session_id"], claimant=a.claimant, holder=cl["holder"])
            return 5
        rf = refresh(cap, a.cwd)
        ledger("successor_claimed", session_id=cap["session_id"], claimant=a.claimant,
               refresh=rf["verdict"], divergences=rf["divergences"])
        print(bootstrap(cap))
        print(f"\nReality refresh: {rf['verdict']}")
        if rf["now"].get("elsewhere"):
            print(f"  (checked the capsule's repo, not this cwd -- work there: {rf['now']['elsewhere']})")
        for d in rf["divergences"]:
            print(f"  - {d}")
        if rf["verdict"] != "CONTINUE":
            print("Do not continue from the capsule as written: re-read the goal file and the tree first.")
        print("\nResume exam -- answer before any mutation, then run:")
        print(f"  python {Path(__file__).as_posix()} certify --from {cap['session_id']} "
              f"--claimant {a.claimant} --goal <file> --branch <b> --head <7> --next \"<first obligation>\"")
        for item in exam(cap):
            print(f"  [{item['key']}] {item['q']}")
        return 0
    if a.cmd == "certify":
        path = capsule_path(a.from_session)
        if not path.is_file():
            print(f"No capsule {path}.")
            return 4
        holder = claim_holder(a.from_session)
        if holder != a.claimant:
            # Fencing: only the successor that won the claim may take mutation authority.
            print(f"REFUSED: capsule is claimed by {holder or 'nobody'}, not {a.claimant}; run resume first.")
            ledger("certify_refused", session_id=a.from_session, claimant=a.claimant, holder=holder)
            return 5
        answers = _answers(a)
        if answers is None:
            print("UNREADABLE: --answers is not a JSON object (PowerShell strips its quotes); "
                  "pass --goal/--branch/--head/--next instead. Nothing judged.")
            return 7
        cap = json.loads(path.read_text(encoding="utf-8"))
        res = certify(cap, answers)
        ledger(res["verdict"].lower(), session_id=a.from_session, wrong=res["wrong"])
        if res["verdict"] == "RESUME_CERTIFIED":
            _atomic_write(path.with_suffix(".certified"), _iso().encode("utf-8"))
            print("RESUME_CERTIFIED -- the capsule is retired; continue with the first obligation.")
            return 0
        print("RESUME_FAILED -- re-read the goal file; do not mutate yet.")
        for w in res["wrong"]:
            print(f"  {w['key']}: expected {w['expected']!r}, given {w['given']!r}")
        return 6
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
