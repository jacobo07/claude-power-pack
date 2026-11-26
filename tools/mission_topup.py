#!/usr/bin/env python
"""Mission auto top-up (spec vault/specs/mission-auto-topup.md).

A mission armed overnight should not wait seven hours on a budget stop while it is producing commits, and should
not spend without limit either. The Owner declares, at arm time, an authority plus N top-ups of a fixed step. The
5-minute sweep grants one step when the mission is parked on its mission-authority trip AND the execution root has
non-bookkeeping commits since the last grant. Anything else stays held, recorded, and is surfaced once.

    mission_topup.py budget  --mission M --authority 120M --topups 3 --step 40M [--reason TEXT]
    mission_topup.py suggest --cwd REPO
    mission_topup.py sweep   [--dry-run]
    mission_topup.py status  --mission M

Kill switch: CPP_MISSION_AUTO_TOPUP=off (sweep does nothing).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402
import mission_binding as mb  # noqa: E402

SCHEMA = "mission-topup/1"
AUTHORITY_TRIP = "cost breaker (mission authority)"
DEFAULT_PHASE_TOKENS = 40_000_000   # measured: 154M / 4 phases, one project, 2026-10-15
BOOKKEEPING_PREFIX = ".planning/"
DEFAULT_CEILING_X = 3.0             # Owner 2026-11-21 "x3" (was 2x, 2026-11-16): grow to 3x authority, commits-gated


def enabled() -> bool:
    return (os.environ.get("CPP_MISSION_AUTO_TOPUP") or "").strip().lower() != "off"


def default_enabled() -> bool:
    return (os.environ.get("CPP_MISSION_TOPUP_DEFAULT") or "").strip().lower() != "off"


def ceiling_x() -> float:
    try:
        x = float(os.environ.get("CPP_MISSION_TOPUP_CEILING_X") or DEFAULT_CEILING_X)
    except ValueError:
        x = DEFAULT_CEILING_X
    return max(1.0, x)


def default_terms(authority: int, step: int | None = None) -> dict:
    """{ceiling, step, max_topups} for the 2x default: the steps that fit between authority and ceiling."""
    ceiling = int(authority * ceiling_x())
    room = max(0, ceiling - authority)
    stp = min(step or DEFAULT_PHASE_TOKENS, room) if room else (step or DEFAULT_PHASE_TOKENS)
    return {"ceiling": ceiling, "step": stp, "max_topups": (-(-room // stp)) if room else 0}


def policy_path(mission_id: str) -> Path:
    return Path(gm.lr.state_dir()) / f"mission-topup-{mission_id}.json"


def load_policy(mission_id: str) -> dict | None:
    p = policy_path(mission_id)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_policy(pol: dict) -> None:
    p = policy_path(pol["mission_id"])
    tmp = p.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(pol, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def parse_tokens(text) -> int:
    """'40M' / '1.5M' / '800K' / '40000000' -> int. Refuses anything else."""
    s = str(text).strip().upper().replace("_", "").replace(",", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KMG]?)", s)
    if not m:
        raise ValueError(f"not a token count: {text!r}")
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "G": 1_000_000_000}[m.group(2)]
    n = int(float(m.group(1)) * mult)
    if n <= 0:
        raise ValueError(f"token count must be positive: {text!r}")
    return n


def _git(wd: str, *args: str) -> str | None:
    g = gm.resolve_exe("git") or "git"
    try:
        r = subprocess.run([g, "-C", wd, *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30)
    except Exception:  # noqa: BLE001 -- unmeasured is its own answer
        return None
    return r.stdout if r.returncode == 0 else None


def head_of(wd: str) -> str | None:
    out = _git(wd, "rev-parse", "HEAD")
    return out.strip() if out else None


def branch_tips(wd: str) -> list[str] | None:
    """Tips of every local branch of the repository `wd` belongs to (worktree branches share refs/heads)."""
    out = _git(wd, "for-each-ref", "--format=%(objectname)", "refs/heads")
    return None if out is None else sorted({t for t in out.split() if t})


def progress_since(wd: str, base: str | None, exclude_tips=None, since: float | None = None) -> dict:
    """{measured, progress, commits, paths, head, tips}. Progress = new commits touching a path outside `.planning/`.
    An unknown base or an unreadable root is unmeasured, never 'no progress'.

    New = reachable from HEAD or ANY local branch, and from neither `base` nor a tip recorded at the last grant.
    Measured 2026-11-22 (m-76e04d86896d): the work of plan 02-03 sat on an executor's worktree branch, unmerged,
    so HEAD-only counting read 30 minutes of real commits as "0 commits" and the mission stayed parked 3 h. A
    policy written before tips were recorded has no `exclude_tips`; it counts branch commits made after `since`
    (its last grant or budget time), so an old unrelated branch in the clone is never mistaken for new work."""
    head = head_of(wd)
    if not head or not base:
        return {"measured": False, "progress": False, "head": head, "why": "root or base unreadable"}
    if _git(wd, "cat-file", "-e", f"{base}^{{commit}}") is None:
        return {"measured": False, "progress": False, "head": head, "why": f"base {base[:8]} not in history"}
    tips = branch_tips(wd)
    excl = [f"^{base}", *[f"^{t}" for t in (exclude_tips or [])]]
    if exclude_tips is not None:
        scans = [["HEAD", "--branches", *excl]]
    else:   # legacy policy: HEAD as before, plus branch commits made inside the window
        scans = [["HEAD", *excl]] + ([["--branches", *excl, f"--since={int(since)}"]] if since is not None else [])
    commits: set[str] = set()
    paths: set[str] = set()
    for scan in scans:
        log = _git(wd, "rev-list", *scan)
        names = _git(wd, "log", "--format=", "--name-only", *scan)
        if log is None or names is None:
            return {"measured": False, "progress": False, "head": head, "why": f"history unreadable from {base[:8]}"}
        commits |= {c for c in log.split() if c}
        paths |= {p for p in names.splitlines() if p.strip() and not p.startswith(BOOKKEEPING_PREFIX)}
    return {"measured": True, "progress": bool(commits) and bool(paths), "head": head, "tips": tips,
            "commits": len(commits), "paths": len(paths)}


# ----------------------------------------------------------------------------- W2: progress receipts
# Spec vault/specs/mission-capital-state.md (W2). progress_since() above reads ONE checkout plus EVERY local branch, so
# a new unrelated branch in a shared clone bought a grant. progress_receipts() reads what is the mission's own:
# (a) its ledger receipts and (b) a commit delta over its LINEAGE roots, derived from mission and session ids, never
# from a branch name. Kill switch CPP_PROGRESS_RECEIPTS=off -> progress_since (the any-branch reading of 8c059095).
MAX_LINEAGE_FILES = 64          # transcripts (worker + subagents) read per judgement, newest first


def receipts_enabled() -> bool:
    return (os.environ.get("CPP_PROGRESS_RECEIPTS") or "").strip().lower() not in ("off", "0", "false")


_LEDGER_CACHE: dict = {"key": None, "by_mission": None}


def _mission_rows(mid: str) -> list[dict] | None:
    """This mission's ledger rows (keyed by `mission_id`, else the row's session_id). One parse per ledger version,
    because one sweep visits every policy. A missing ledger is [] (nothing written yet); an unreadable one is None."""
    p = gm.lr.ledger_path()
    try:
        st = p.stat()
    except FileNotFoundError:
        return []
    except OSError:
        return None
    key = (str(p), st.st_mtime_ns, st.st_size)
    if _LEDGER_CACHE["key"] != key:
        by: dict = {}
        try:
            with open(p, encoding="utf-8-sig", errors="replace") as fh:
                for line in fh:
                    if '"mission_id"' not in line and '"session_id": "m-' not in line:
                        continue
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(row, dict):
                        by.setdefault(row.get("mission_id") or row.get("session_id"), []).append(row)
        except OSError:
            return None
        _LEDGER_CACHE.update(key=key, by_mission=by)
    return list(_LEDGER_CACHE["by_mission"].get(mid) or [])


def ledger_receipts(rows: list[dict] | None, since: float | None) -> list[dict] | None:
    """Source (a): measured progress receipts written after `since`. Only the breaker's GOOD_PROGRESS receipt counts:
    it is a MEASUREMENT (the allow-listed content fingerprint of the bound tree moved; bookkeeping such as STATE.md
    never moves it). A cost_mark transition is always preceded by one, so it adds nothing. An obligation closed by
    hand (obligation_set) or a checkpoint is the worker's own statement, not a measurement, and never buys capital.
    None = ledger unreadable (unmeasured, never 'no receipts')."""
    if rows is None:
        return None
    out = []
    for r in rows:
        if r.get("event") != "breaker_receipt" or r.get("classification") != mb.GOOD:
            continue
        t = gm.lr._parse_iso(r.get("ts"))
        if t is None or (since is not None and t <= float(since)):
            continue
        out.append({"at": t, "action": r.get("action"), "gen": r.get("gen"), "root": r.get("root")})
    return out


def lineage_sessions(rec: dict, rows: list[dict] | None) -> list[str]:
    """The mission's own worker sessions: every `worker_acked` worker in its ledger, plus the current owner."""
    sids: list[str] = []
    for r in rows or []:
        if r.get("event") == "worker_acked" and r.get("worker"):
            sids.append(str(r["worker"]))
    own = (rec.get("owner") or {}).get("session_id")
    if own:
        sids.append(str(own))
    return list(dict.fromkeys(sids))


def _session_evidence(sid: str, since: float | None) -> tuple[list[str], list[str]]:
    """(written paths, subagent cwds) a session and its subagents recorded after `since`. Main-thread cwd is NOT
    returned: a background worker's transcript cwd is the arm checkout, shared with every other pane."""
    tr = gm.lr.find_transcript(sid)
    if not tr:
        return [], []
    files = [(Path(tr), False)]
    sub = Path(tr).parent / Path(tr).stem / "subagents"
    try:
        files += [(f, True) for f in sorted(sub.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)]
    except OSError:
        pass
    wrote, cwds = [], []
    for f, sidechain in files[:MAX_LINEAGE_FILES]:
        try:
            if since is not None and f.stat().st_mtime < float(since):
                continue   # untouched since the last grant: nothing new can be in it
        except OSError:
            continue
        uses = mb.tool_uses_since(f, float(since or 0)) or []
        wrote += mb.written_paths(uses)
        if sidechain:
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        if '"cwd"' not in line:
                            continue
                        try:
                            row = json.loads(line)
                        except ValueError:
                            continue
                        if not isinstance(row, dict):
                            continue
                        t = gm.lr._parse_iso(row.get("timestamp"))
                        if row.get("cwd") and (since is None or t is None or t >= float(since)):
                            cwds.append(str(row["cwd"]))
            except OSError:
                continue
    return wrote, cwds


def lineage_roots(rec: dict, rows: list[dict] | None, since: float | None) -> dict:
    """Source (b) roots: {roots, sessions, named}. Every binding generation (the bound root, its `previous`, every
    root a `workspace_rebound` row or rebind receipt of THIS mission names), plus each worktree of the repository in
    which one of the mission's own sessions wrote a file or ran a subagent after `since`. The arm checkout (cwd) is
    a root only while it is the execution root or a session wrote in it: other panes commit there too."""
    roots: list[str] = [mb.execution_root(rec)]
    b = mb.binding(rec) or {}
    if b.get("previous"):
        roots.append(str(b["previous"]))
    for r in rows or []:
        if r.get("root") and (r.get("event") == "workspace_rebound"
                              or (r.get("event") == "breaker_receipt" and r.get("action") == "rebind")):
            roots.append(str(r["root"]))
    sessions = lineage_sessions(rec, rows)
    named: list[str] = []
    paths: list[str] = []
    for sid in sessions:
        w, c = _session_evidence(sid, since)
        paths += w + c
    wts = mb.worktrees(rec["cwd"]) if paths else []
    for p in paths:
        hit = None
        np_ = mb._norm(p)
        for w in wts or []:
            r_ = mb._norm(w["root"])
            if (np_ == r_ or np_.startswith(r_ + os.sep)) and (hit is None or len(r_) > len(mb._norm(hit))):
                hit = w["root"]
        if hit:
            named.append(hit)
    roots += named
    seen, out = set(), []
    for r in roots:
        k = mb._norm(r)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return {"roots": out, "sessions": sessions, "named": list(dict.fromkeys(named))}


def progress_receipts(rec: dict, pol: dict) -> dict:
    """{measured, progress, commits, paths, receipts, head, tips, roots, why}: the mission's progress since its last
    grant (pol last_head / last_tips / last_at), the union of (a) ledger receipts and (b) the non-bookkeeping commit
    delta over the lineage roots' HEADs (c: commits touching only .planning/ and branches outside the lineage do not
    count). Progress is measured when either source answered; neither answering is unmeasured, never 'none'."""
    mid = rec["mission_id"]
    base, tips = pol.get("last_head"), pol.get("last_tips")
    since = pol.get("last_at") or pol.get("set_at")
    rows = _mission_rows(mid)
    rc = ledger_receipts(rows, since)
    lin = lineage_roots(rec, rows, since)
    root = mb.execution_root(rec)
    head = head_of(root)
    heads = {r: (head if r == root else head_of(r)) for r in lin["roots"]}
    live = [h for h in heads.values() if h]
    out = {"head": head, "tips": branch_tips(root) if head else None, "roots": lin["roots"],
           "named": lin["named"], "unread": [r for r, h in heads.items() if not h],
           "receipts": len(rc) if rc is not None else 0, "receipts_measured": rc is not None}
    commits: set[str] = set()
    paths: set[str] = set()
    why = None
    wd = next((r for r, h in heads.items() if h), None)
    if not base or not live or wd is None:
        why = "root or base unreadable"
    elif _git(wd, "cat-file", "-e", f"{base}^{{commit}}") is None:
        why = f"base {base[:8]} not in history"
    else:
        excl = [f"^{base}", *[f"^{t}" for t in (tips or [])]]
        if tips is not None:
            scans = [[*live, *excl]]
        else:   # legacy policy (no tips): the execution root as before; other lineage heads inside the window only
            others = [h for r, h in heads.items() if h and r != root]
            scans = ([[head, *excl]] if head else []) + (
                [[*others, *excl, f"--since={int(since)}"]] if others and since is not None else [])
        for scan in scans:
            log = _git(wd, "rev-list", *scan)
            names = _git(wd, "log", "--format=", "--name-only", *scan)
            if log is None or names is None:
                why = f"history unreadable from {base[:8]}"
                break
            commits |= {c for c in log.split() if c}
            paths |= {p for p in names.splitlines() if p.strip() and not p.startswith(BOOKKEEPING_PREFIX)}
    commit_measured = why is None
    if not commit_measured:
        commits, paths = set(), set()
    by_commit = bool(commits) and bool(paths)
    measured = commit_measured or (rc is not None and len(rc) > 0)
    out.update(measured=measured, progress=by_commit or out["receipts"] > 0, commits=len(commits), paths=len(paths))
    if not measured:
        out["why"] = why if rc is not None else f"{why}; ledger unreadable"
    return out


def is_authority_trip(rec: dict) -> bool:
    hold = rec.get("owner_hold") or {}
    return hold.get("kind") == "cost" and AUTHORITY_TRIP in (hold.get("reason") or "")


CAPITAL_EXHAUSTED = "CAPITAL_EXHAUSTED"
AUTHORITY_ASK = "OWNER_BOUNDARY (AUTHORITY)"
CAPITAL_STATES = ("HEALTHY", "PRESSURE", "RENEW_ELIGIBLE", "RESUME_ONLY", "EXHAUSTED_OWNER", "WAITING_PROVIDER",
                  "TERMINAL", "UNKNOWN")


def capital_state_enabled() -> bool:
    return (os.environ.get("CPP_CAPITAL_STATE") or "").strip().lower() not in ("off", "0", "false")


def provider_enabled() -> bool:
    """W5 kill switch: CPP_TOPUP_PROVIDER=off -> a provider hold no longer separates from capital (pre-W5)."""
    return (os.environ.get("CPP_TOPUP_PROVIDER") or "").strip().lower() not in ("off", "0", "false")


def provider_of(rec: dict | None, now: float) -> dict | None:
    """W5: the provider hold the mission's next successor would meet (gsd_mission.provider_hold: the provider
    breaker's quota / auth / transient classes, with its own degraded fallback), or None. Read only at a capital
    boundary or under PRESSURE: a capital grant then would only buy a successor the provider refuses. An unreadable
    provider is None here (the breaker already ledgers its own unavailability), so it never blocks a grant alone."""
    if not rec or not provider_enabled():
        return None
    try:
        h = gm.provider_hold(rec, now)
    except Exception as exc:  # noqa: BLE001 -- named, never a hold
        gm.lr.ledger_append(rec.get("mission_id"), "capital_provider_unreadable", mission_id=rec.get("mission_id"),
                            error=f"{type(exc).__name__}: {exc}"[:200])
        return None
    if not h:
        return None
    until = h.get("until")
    if until is not None and float(until) <= now:
        return None
    return {"class": h.get("class", "quota"), "until": until, "reason": str(h.get("reason") or "")[:200],
            "quarantine": bool(h.get("quarantine"))}


def capital_label(rec: dict | None) -> str | None:
    """Which capital boundary the record is parked on, or None. `authority_hold`: the cost breaker's (or the
    dead-worker guard's) mission-authority hold. `blocked_capital` (H1): state BLOCKED, no Owner hold, and the
    worker's own question 'raise authority' -- the CURRENT blocker (gm.current_blocker: compiled in this epoch) is
    CAPITAL_EXHAUSTED, or the asking text `OWNER_BOUNDARY (AUTHORITY)` heads the record reason or the blocker's
    (block_mission keeps it on the blocker: later transitions overwrite rec.reason while the mission stays BLOCKED;
    parallel line 8c059095, m-76e04d86896d). Record fields only, never ledger text."""
    if not rec:
        return None
    if is_authority_trip(rec):
        return "authority_hold"
    if rec.get("state") == gm.BLOCKED and not rec.get("owner_hold"):
        b = gm.current_blocker(rec) or {}
        texts = (str(rec.get("reason") or ""), str(b.get("reason") or ""))
        if b.get("class") == CAPITAL_EXHAUSTED or any(t.startswith(AUTHORITY_ASK) for t in texts):
            return "blocked_capital"
    return None


def occurrence_key(rec: dict, label: str | None):
    """The per-occurrence key a grant/resume is written against (exactly-once). A hold: its set_at. A BLOCKED park:
    'blocked:e<epoch>:<blocker at | updated_at>' -- the exact form the parallel line (8c059095, live on GEX44 as
    b2af3eb0) writes, so a grant it already wrote is recognised here after the merge instead of granted twice, and
    _complete keys the BLOCKED -> RUNNING unblock on the 'blocked:' prefix. Every relaunch bumps the epoch, so a later
    block differs and two passes over one block agree."""
    if label == "authority_hold":
        return (rec.get("owner_hold") or {}).get("set_at")
    if label == "blocked_capital":
        b = gm.current_blocker(rec) or {}
        return f"blocked:e{rec.get('epoch')}:{b.get('at') or rec.get('updated_at')}"
    return None


def _raised_since(rec: dict, at) -> bool:
    """An authority receipt raised the ceiling at or after `at` (the block): the worker's question was answered."""
    if at is None:
        return False
    return any(float(r.get("at") or 0) >= float(at) and int(r.get("new") or 0) > int(r.get("prev") or 0)
               for r in rec.get("authority_receipts") or [] if isinstance(r, dict))


def _min_lease() -> int:
    """The room a minimum successor lease needs, computed as _dead_worker_authority_guard does."""
    import mission_recovery as mr
    return -(-mr.MIN_LEASE_TOKENS * 1000 // int(1000 * (1 - mr.RESERVE_FRACTION)))


# ------------------------------------------------------------------ W3: predictive renewal, events, exactly-once
# Spec vault/specs/mission-capital-state.md "W3". One per-mission lock serialises every top-up pass (poller, in-process
# event, manual CLI), the record seq is re-read before a grant/resume entry is written, and a thread-local depth stops
# a pass's own effects (set_authority, release, decide) from re-entering it as events.
import threading  # noqa: E402

_EV = threading.local()
EVENT_LOCK_S = 15.0    # an event waits this long for a pass in flight, then leaves it to the reconciler
POLL_LOCK_S = 30.0
PREDICTIVE_PREFIX = "pressure:"
PREDICTIVE_CAUSES = ("forecast_invalidated", "cost_mark", "pre_launch")


def predictive_enabled() -> bool:
    return (os.environ.get("CPP_TOPUP_PREDICTIVE") or "").strip().lower() not in ("off", "0", "false")


def event_enabled() -> bool:
    return (os.environ.get("CPP_TOPUP_EVENT") or "").strip().lower() not in ("off", "0", "false")


class _Quiet:
    """Inside a top-up pass (or budget()): capital events raised by its own writes are not re-dispatched."""

    def __enter__(self):
        _EV.depth = getattr(_EV, "depth", 0) + 1
        return self

    def __exit__(self, *exc):
        _EV.depth -= 1


def in_capital_pass() -> bool:
    return getattr(_EV, "depth", 0) > 0


def lock_path(mission_id: str) -> Path:
    return policy_path(mission_id).with_suffix(".lock")


def _topup_lock(mission_id: str, timeout_s: float):
    """The per-mission top-up lock: gsd_mission's kernel byte-range lock (released by the OS when a holder dies,
    never reclaimed by age). One seam, so the race suite can remove it and show what the seq check holds alone."""
    return gm._Lock(lock_path(mission_id), timeout_s=timeout_s)


def next_lease(rec: dict, pol: dict | None) -> tuple[int, str]:
    """The next lease's size, for PRESSURE: the work class's settled p80 (work_class_profile.lease_forecast, the
    integer phase leases use), else the policy step -- one grant's worth -- named as such, never a guess."""
    cls = rec.get("work_class") or (rec.get("baseline") or {}).get("work_class") or "GSD_RESUME"
    try:
        import work_class_profile as wcp
        f = wcp.lease_forecast(cls)
        return int(f["forecast"]), f"{cls} {f['basis']}"
    except Exception:  # noqa: BLE001 -- no settled samples (or no profile): the step is the named fallback
        return int((pol or {}).get("step") or 0), f"policy step ({cls}: no settled lease forecast)"


def _predictive_this_epoch(pol: dict | None, rec: dict) -> dict | None:
    """The last unvoided predictive grant made during the record's CURRENT epoch (one worker's life), or None. Its key
    carries the epoch (`pressure:e<epoch>:...`), so a grant from an earlier worker -- one a relaunch card told its
    successor about -- does not count."""
    tag = f"{PREDICTIVE_PREFIX}e{rec.get('epoch')}:"
    hits = [g for g in (pol or {}).get("grants") or []
            if str(g.get("hold_set_at") or "").startswith(tag) and not g.get("voided")]
    return hits[-1] if hits else None


def _unapplied_predictive(grants: list, authority: int) -> dict | None:
    """The current epoch's last grant when it is a predictive one whose raise never landed (authority below its
    `to`, not voided): a pass died between writing it and its effect. Matched on the authority still EQUAL to the
    grant's `from`: any other figure means someone set the authority since, and that act is not undone here."""
    last = grants[-1] if grants else None
    if (last and str(last.get("hold_set_at") or "").startswith(PREDICTIVE_PREFIX) and not last.get("voided")
            and int(authority or 0) == int(last.get("from") or -1) < int(last.get("to") or 0)):
        return last
    return None


def _owner_exhausted(pol: dict, auth: int) -> bool:
    """The authority dimension is the Owner's: ceiling reached, or (no ceiling) every top-up spent. Same rule as the
    EXHAUSTED_OWNER branches of capital_state."""
    if pol.get("ceiling"):
        return auth >= int(pol["ceiling"])
    return bool(pol) and len(pol.get("grants") or []) >= int(pol.get("max_topups") or 0)


def _waiting_provider(out: dict, provider: dict) -> dict:
    """W5: the WAITING_PROVIDER state. The wake is the provider's own reset (the first poll at or after it), not
    the Owner: a quota resets by itself; a quarantine (until None) needs a re-login, which is not a capital act."""
    until = provider.get("until")
    out["dims"].update(wake_at=until, provider_class=provider.get("class"))
    when = (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(until))) if until is not None
            else "a re-login (quarantined)")
    return {**out, "state": "WAITING_PROVIDER",
            "why": f"provider {provider.get('class')} until {when}: {provider.get('reason')}"[:300]}


def capital_state(rec: dict | None, pol: dict | None, spent: int | None, now: float,
                  lease: tuple[int, str] | None = None, provider: dict | None = None) -> dict:
    """Pure: the ONE capital state of a mission (spec vault/specs/mission-capital-state.md, W1).
    {state, label, why, dims}. dims = authority/spent/reserve/headroom/min_lease, hours deadline, cycles used/max,
    and the occurrence key. Unmeasured spend is UNKNOWN, never zero. Cycles are recorded only: the runtime renews
    a cycle-capped halt itself (mission_renewed, measured 5 min). `lease` (W3) = next_lease(): PRESSURE is headroom
    below max(minimum lease, next lease); absent, the policy step stands for the next lease (W1 behaviour).
    `provider` (W5) = provider_of(): at a boundary or under PRESSURE, a live provider hold is WAITING_PROVIDER, which
    grants, resumes and releases nothing and pings nobody; dims.wake_at is its reset (None = quarantined, a re-login).
    Hours exhausted still wins: that is the Owner's either way."""
    import mission_spend as ms
    pol = pol or {}
    if rec is None or rec.get("state") in gm.TERMINAL:
        return {"state": "TERMINAL", "label": None, "why": "mission gone or terminal", "dims": {}}
    label = capital_label(rec)
    auth = int(rec.get("authority_tokens") or 0)
    reserve = ms.closeout_reserve(rec) if auth else 0
    need = _min_lease()
    headroom = None if spent is None else auth - reserve - int(spent)
    mh = float(rec.get("max_hours") or gm.lr.DEFAULT_MAX_HOURS)
    # S9 A1: time already parked on a durable wait is not execution time (budget_exhausted excludes it too)
    deadline = float(rec.get("created_at") or now) + int(rec.get("waited_s") or 0) + 3600 * mh
    dims = {"authority": auth, "spent": spent, "reserve": reserve, "headroom": headroom, "min_lease": need,
            "hours_deadline": deadline, "max_hours": mh,
            "cycles_used": int(rec.get("iterations") or 0),
            "cycles_max": int(rec.get("max_cycles") or gm.lr.DEFAULT_MAX_CYCLES),
            "key": occurrence_key(rec, label)}
    dims["cycles_exhausted"] = dims["cycles_used"] >= dims["cycles_max"]
    out = {"label": label, "dims": dims}
    if label is None:
        if headroom is None:
            return {**out, "state": "UNKNOWN", "why": "spent unmeasured"}
        nxt, basis = lease if lease is not None else (int(pol.get("step") or 0), "policy step")
        dims.update(pressure_at=max(need, nxt), lease_basis=basis)
        st = "PRESSURE" if headroom < dims["pressure_at"] else "HEALTHY"
        if st == "PRESSURE" and provider:
            return _waiting_provider(out, provider)
        return {**out, "state": st, "why": f"headroom {headroom:,} vs next lease {dims['pressure_at']:,} ({basis})"}
    if now >= deadline:
        return {**out, "state": "EXHAUSTED_OWNER", "why": f"hours exhausted ({mh:g} h)", "dim": "hours"}
    # review L1: an Owner boundary on authority (ceiling reached / top-ups exhausted) at the renew zone is reported as
    # EXHAUSTED_OWNER even under a provider wait -- like hours, it is the Owner's either way, and a quarantine
    # (no reset time) would otherwise hide it until after a re-login.
    renew_zone = headroom is not None and (headroom <= need if label == "authority_hold"
                                           else headroom < max(need, int(pol.get("step") or 0)))
    if provider and not (renew_zone and _owner_exhausted(pol, auth)):
        return _waiting_provider(out, provider)
    if spent is None:
        return {**out, "state": "UNKNOWN", "why": "spent unmeasured: no grant on an unknown spend"}
    if label == "blocked_capital":
        # The worker asked itself. Under one step of headroom the ask is a real capital stop (renew below). With a step
        # or more it is answered by a resume only when the Owner raised authority after the block (a stale ask); else
        # it is not a budget stop -- no grant, the Owner is told (parallel line 8c059095, AUTHORITY-BLOCK-ROOM-LEFT).
        if headroom >= max(need, int(pol.get("step") or 0)):
            if _raised_since(rec, (gm.current_blocker(rec) or {}).get("at")):
                return {**out, "state": "RESUME_ONLY",
                        "why": f"stale authority ask: raised to {auth:,} after the block, headroom {headroom:,}"}
            pg = _predictive_this_epoch(pol, rec)
            if pg:
                # W3 (measured on GEX44, V-W3-RACE-WORKER-BLOCK-VS-POLLER): a predictive grant raises authority and,
                # by design, tells the worker nothing. A worker still reading the old figure then asks for authority
                # it already has. Its ask predates what it was never told: answer it with a resume, not an Owner ping.
                return {**out, "state": "RESUME_ONLY",
                        "why": (f"stale authority ask: predictive top-up {pg.get('n')} raised to {auth:,} in this "
                                f"worker's epoch {rec.get('epoch')}, headroom {headroom:,}")}
            return {**out, "state": "HEALTHY", "dim": "ask",
                    "why": f"authority block with {headroom:,} still unspent (>= one step)"}
    elif headroom > need:
        return {**out, "state": "RESUME_ONLY",
                "why": f"stale capital park: headroom {headroom:,} > minimum lease {need:,} under authority {auth:,}"}
    if pol.get("ceiling"):
        if auth >= int(pol["ceiling"]):
            return {**out, "state": "EXHAUSTED_OWNER", "dim": "authority",
                    "why": f"ceiling reached ({int(pol['ceiling']):,}); beyond it is the Owner's"}
    elif pol and len(pol.get("grants") or []) >= int(pol.get("max_topups") or 0):
        return {**out, "state": "EXHAUSTED_OWNER", "dim": "authority",
                "why": f"top-ups exhausted ({len(pol.get('grants') or [])}/{pol.get('max_topups')})"}
    return {**out, "state": "RENEW_ELIGIBLE", "why": f"{label}: headroom {headroom:,} <= minimum lease {need:,}"}


_NO_SPENT = object()


def judge(rec: dict | None, pol: dict, prog: dict, spent=_NO_SPENT, now: float | None = None,
          predictive: bool = False, lease: tuple[int, str] | None = None, provider: dict | None = None) -> dict:
    """{action: none|grant|resume|release|refuse, why[, key, capital]}. Consumes capital_state only.
    `resume` completes a grant already written for this occurrence; `release` (RESUME_ONLY) wakes a stale park
    without adding capital. CPP_CAPITAL_STATE=off -> the judge exactly as at 8c452fac.
    `predictive` (W3): a mission at no boundary but under PRESSURE is judged for a grant BEFORE it parks.
    `provider` (W5): WAITING_PROVIDER is `none` with wake_at -- even a grant already written waits (its key does not
    change, so it is resumed, exactly once, after the reset)."""
    if not capital_state_enabled():
        return _judge_8c452fac(rec, pol, prog)
    now = time.time() if now is None else now
    if spent is _NO_SPENT:
        spent = _spent(rec) if rec else None
    if predictive and rec and lease is None:
        lease = next_lease(rec, pol)
    cs = capital_state(rec, pol, spent, now, lease=lease, provider=provider)
    if cs["state"] == "TERMINAL":
        return {"action": "none", "why": cs["why"], "capital": cs}
    if cs["state"] == "WAITING_PROVIDER":
        return {"action": "none", "why": cs["why"], "waiting_provider": True, "wake_at": cs["dims"].get("wake_at"),
                "key": cs["dims"].get("key"), "capital": cs}
    if cs["label"] is None:
        if predictive and predictive_enabled() and cs["state"] == "PRESSURE":
            return _judge_predictive(rec, pol, prog, cs, now)
        return {"action": "none", "why": "no mission capital boundary (authority hold or BLOCKED/CAPITAL_EXHAUSTED)",
                "capital": cs}
    key = cs["dims"]["key"]
    base = {"key": key, "capital": cs}
    grants = pol.get("grants") or []   # the CURRENT policy epoch only; earlier epochs live in prior_grants
    if grants and grants[-1].get("hold_set_at") == key and not grants[-1].get("voided"):
        return {"action": "resume", "why": "grant already written for this hold", **base}
    if _unapplied_predictive(grants, cs["dims"]["authority"]):
        # W3 review LOW-3: a predictive grant whose raise died before landing is completed first (raise only); the
        # park it left is then a stale hold with headroom (RESUME_ONLY) next pass. Granting n+1 from the un-raised
        # authority instead would spend a top-up slot for nothing.
        return {"action": "resume", "why": "an unapplied predictive grant is completed first", **base}
    resumes = pol.get("resumes") or []
    if resumes and resumes[-1].get("key") == key:
        return {"action": "release", "why": "resume already written for this hold", "resume": True, **base}
    if cs["state"] in ("EXHAUSTED_OWNER", "UNKNOWN", "HEALTHY"):   # HEALTHY here = an ask with a step unspent
        return {"action": "refuse", "why": cs["why"], **base}
    if cs["state"] == "RESUME_ONLY":
        return {"action": "release", "why": cs["why"], **base}
    if not prog.get("measured"):
        return {"action": "refuse", "why": f"progress unmeasured: {prog.get('why')}", **base}
    if not prog.get("progress"):
        return {"action": "refuse", "why": (f"no progress since {str(pol.get('last_head'))[:8]}: "
                                            f"{prog.get('commits', 0)} commit(s), {prog.get('paths', 0)} "
                                            "non-bookkeeping path(s)"
                                            + (", 0 progress receipt(s)" if "receipts" in prog else "")), **base}
    rcpt = f" + {prog['receipts']} progress receipt(s)" if prog.get("receipts") else ""
    return {"action": "grant", "why": f"{prog['commits']} commit(s) touching {prog['paths']} path(s){rcpt}", **base}


def _judge_predictive(rec: dict, pol: dict, prog: dict, cs: dict, now: float) -> dict:
    """W3 (H4): a running mission whose headroom is below its next lease, judged BEFORE it parks. Same envelope and
    progress gates as a boundary grant; anything short of a grant is `none`, never a refusal: the mission is running,
    and if it does reach the boundary that pass asks the Owner. Key 'pressure:e<epoch>:a<authority>': a completed
    grant moves the authority, so the next judgement is a new occurrence and needs new progress since this grant."""
    d = cs["dims"]
    key = f"{PREDICTIVE_PREFIX}e{rec.get('epoch')}:a{d['authority']}"
    base = {"key": key, "capital": cs, "predictive": True}
    grants = pol.get("grants") or []
    if ((grants and grants[-1].get("hold_set_at") == key and not grants[-1].get("voided"))
            or _unapplied_predictive(grants, d["authority"])):
        return {"action": "resume", "why": "predictive grant already written at this authority", **base}
    last = grants[-1] if grants else None
    if last and not last.get("voided") and str(last.get("hold_set_at") or "").startswith(PREDICTIVE_PREFIX):
        # W3 review MEDIUM-2: at most ONE unspent predictive step outstanding. With a next lease larger than headroom
        # plus a step, every cost_mark (a commit = new progress) would grant again and could drain the top-ups with
        # little spend, parking the mission EXHAUSTED_OWNER later. The next one waits until that step is spent.
        step_given = int(last.get("to") or 0) - int(last.get("from") or 0)
        spent_since = None if last.get("spent") is None or d["spent"] is None else d["spent"] - int(last["spent"])
        if spent_since is None or spent_since < step_given:
            return {"action": "none", **base,
                    "why": (f"predictive: one step ahead already (grant {last.get('n')}: "
                            f"{spent_since if spent_since is not None else 'unmeasured'} of {step_given:,} spent since)")}
    if rec.get("owner_hold") or rec.get("state") == gm.BLOCKED:
        return {"action": "none", "why": "predictive: parked on another hold or block, not capital", **base}
    if now >= d["hours_deadline"]:
        return {"action": "none", "why": f"predictive: hours exhausted ({d['max_hours']:g} h)", **base}
    if pol.get("ceiling"):
        if d["authority"] >= int(pol["ceiling"]):
            return {"action": "none", "why": f"predictive: ceiling reached ({int(pol['ceiling']):,})", **base}
    elif len(grants) >= int(pol.get("max_topups") or 0):
        return {"action": "none", "why": f"predictive: top-ups exhausted ({len(grants)}/{pol.get('max_topups')})",
                **base}
    if not prog.get("measured"):
        return {"action": "none", "why": f"predictive: progress unmeasured: {prog.get('why')}", **base}
    if not prog.get("progress"):
        return {"action": "none", "why": "predictive: no progress since the last grant", **base}
    rcpt = f" + {prog['receipts']} progress receipt(s)" if prog.get("receipts") else ""
    return {"action": "grant", **base,
            "why": (f"predictive: headroom {d['headroom']:,} < next lease {d['pressure_at']:,} ({d['lease_basis']}); "
                    f"{prog['commits']} commit(s) touching {prog['paths']} path(s){rcpt}")}


def _judge_8c452fac(rec: dict | None, pol: dict, prog: dict) -> dict:
    """The kill-switch path: judge() verbatim as at 8c452fac (mission-capital W0)."""
    if rec is None or rec.get("state") in gm.TERMINAL:
        return {"action": "none", "why": "mission gone or terminal"}
    if not is_authority_trip(rec):
        return {"action": "none", "why": "no mission-authority cost hold"}
    hold_at = (rec.get("owner_hold") or {}).get("set_at")
    grants = pol.get("grants") or []   # the CURRENT policy epoch only; earlier epochs live in prior_grants
    if grants and grants[-1].get("hold_set_at") == hold_at:
        return {"action": "resume", "why": "grant already written for this hold"}
    # H6 (mission-capital W0): with a ceiling the envelope is bounded by the ceiling, not by a grant count; a
    # count is honoured only when no ceiling was set (pre-ceiling policies keep their behaviour).
    if pol.get("ceiling"):
        if int(rec.get("authority_tokens") or 0) >= int(pol["ceiling"]):
            return {"action": "refuse", "why": f"ceiling reached ({int(pol['ceiling']):,}); beyond it is the Owner's"}
    elif len(grants) >= int(pol["max_topups"]):
        return {"action": "refuse", "why": f"top-ups exhausted ({len(grants)}/{pol['max_topups']})"}
    if not prog.get("measured"):
        return {"action": "refuse", "why": f"progress unmeasured: {prog.get('why')}"}
    if not prog.get("progress"):
        return {"action": "refuse", "why": (f"no progress since {str(pol.get('last_head'))[:8]}: "
                                            f"{prog.get('commits', 0)} commit(s), {prog.get('paths', 0)} "
                                            "non-bookkeeping path(s)")}
    return {"action": "grant", "why": f"{prog['commits']} commit(s) touching {prog['paths']} path(s)"}


def _spent(rec: dict) -> int | None:
    try:
        import mission_spend as ms
        return ms.processed_tokens(rec)
    except Exception:  # noqa: BLE001 -- unmeasured spend is recorded as None, not 0
        return None


def toast_enabled() -> bool:
    """On by default on Windows. A redirected state dir (GSD_LONG_RUN_STATE_DIR: every suite, never the live sweep)
    is a test run, which must not toast the Owner's desktop unless it asks with CPP_MISSION_NOTIFY_TOAST=on."""
    v = (os.environ.get("CPP_MISSION_NOTIFY_TOAST") or "").strip().lower()
    if os.name != "nt" or v in ("off", "0", "false"):
        return False
    return v == "on" or not os.environ.get("GSD_LONG_RUN_STATE_DIR")


_TOAST_PS = (
    "$ErrorActionPreference='Stop';"
    "[void][Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime];"
    "[void][Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom.XmlDocument,ContentType=WindowsRuntime];"
    "$t=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:CPP_TOAST_TEXT));"
    "$x=New-Object Windows.Data.Xml.Dom.XmlDocument;"
    "$x.LoadXml('<toast duration=\"long\"><visual><binding template=\"ToastGeneric\"><text>Misiones PP</text>"
    "<text></text></binding></visual></toast>');"
    "$x.GetElementsByTagName('text').Item(1).InnerText=$t;"
    "$n=[Windows.UI.Notifications.ToastNotification]::new($x);"
    "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
    "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($n)")


def toast(text: str) -> str:
    """Windows toast (spec mission-unattended-continuity B): stays in the Action Center while the Owner is away.
    CREATE_NO_WINDOW: a sweep must never flash a console (console-popup rule). The text travels in an env var as
    base64, never inside the command line. Returns 'toast shown' or a failure string; never raises."""
    import base64
    try:
        env = {**os.environ, "CPP_TOAST_TEXT": base64.b64encode(text[:600].encode("utf-8")).decode("ascii")}
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _TOAST_PS],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as exc:  # noqa: BLE001 -- recorded by the caller as not delivered
        return f"toast failed: {type(exc).__name__}"
    return "toast shown" if r.returncode == 0 else f"toast failed: rc {r.returncode} {(r.stderr or '').strip()[:80]}"


def notify(text: str, sender=None, toaster=None) -> str:
    """Telegram when configured, else a Windows toast; returns what happened, never raises."""
    if sender is not None:
        return sender(text)
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        if toaster is not None:
            return toaster(text)
        return toast(text) if toast_enabled() else "no channel configured"
    try:
        import urllib.parse
        import urllib.request
        data = urllib.parse.urlencode({"chat_id": chat, "text": text[:3900]}).encode()
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=15) as r:
            return f"telegram {r.status}"
    except Exception as exc:  # noqa: BLE001 -- recorded by the caller
        return f"telegram failed: {type(exc).__name__}"


def _complete(mid: str, grant: dict, decide_fn, now: float) -> str:
    """Raise authority to the grant (idempotent), release the hold, wake the worker with a decision.
    A predictive grant (W3, key 'pressure:') raises only: the mission is running, so there is no hold to release, no
    block to answer and no worker to wake (a decision there would stop a working worker to tell it nothing)."""
    rec = gm.load(mid)
    # W3 review LOW-2: the raise is a CAS on the seq just read. An Owner raise landing in between is not overwritten
    # upward: the CasConflict leaves the grant written, and the next pass resumes it against the Owner's figure.
    seq = rec.get("seq")
    cur = int(rec.get("authority_tokens") or 0)
    if cur < int(grant["to"]) and cur != int(grant["from"]):
        # Someone set the authority between this grant's write and its effect (an Owner raise to a figure below `to`,
        # or a cut). That act is the newer authority statement: the grant is VOIDED, like a re-budget's (W1), never
        # completed over it. The next pass judges the mission afresh at the Owner's figure.
        why = (f"authority set to {cur:,} after grant {grant['n']} was written (from {int(grant['from']):,}, "
               f"to {int(grant['to']):,}); superseded")
        pol = load_policy(mid) or {}
        for g in pol.get("grants") or []:
            if g.get("n") == grant["n"] and not g.get("voided"):
                g["voided"] = {"at": now, "why": why}
                save_policy(pol)
                gm.lr.ledger_append(mid, "authority_topup_voided", mission_id=mid, n=grant["n"], to=grant["to"],
                                    authority=cur, reason=why)
        return f"voided: {why}"
    if str(grant.get("hold_set_at") or "").startswith(PREDICTIVE_PREFIX):
        if int(rec.get("authority_tokens") or 0) < grant["to"]:
            gm.set_authority(mid, tokens=grant["to"], now=now, expected_seq=seq, provenance="topup_policy",
                             reason=f"predictive top-up {grant['n']} under Owner policy (mission-capital W3)")
        return "predictive: authority raised; no hold, no wake"
    if int(rec.get("authority_tokens") or 0) < grant["to"]:
        gm.set_authority(mid, tokens=grant["to"], now=now, expected_seq=seq, provenance="topup_policy",
                         reason=f"auto top-up {grant['n']} under Owner policy (spec mission-auto-topup)")
    if gm.load(mid).get("owner_hold"):
        gm.release_owner_hold(mid, now=now)
    text = (f"Auto top-up {grant['n']} granted under the Owner's pre-authorised policy: authority "
            f"{grant['from']:,} -> {grant['to']:,} processed tokens, because {grant['why']}. Continue the "
            "milestone where you stopped; every other constraint is unchanged.")
    out = decide_fn(mid, text, decision_id=f"TOPUP{grant['n']}")
    _unblock(mid, grant.get("hold_set_at"), now, f"auto top-up {grant['n']} answered the authority block")
    return f"woke={out.get('woke') if isinstance(out, dict) else out}"


def _unblock(mid: str, key, now: float, reason: str) -> None:
    """A BLOCKED park (key 'blocked:...') whose question is answered (authority raised or headroom confirmed, decision
    on the record) goes back to RUNNING: a worker the decision could not wake is replaced by the supervisor once the
    mission runs again; left BLOCKED, nothing would relaunch it (parallel line 8c059095)."""
    cur = gm.load(mid)
    if str(key).startswith("blocked:") and cur and cur.get("state") == gm.BLOCKED:
        gm.transition(mid, expect_epoch=cur["epoch"], expect_state=gm.BLOCKED, event="mission_unblocked", now=now,
                      state=gm.RUNNING, reason=reason)


def _complete_resume(mid: str, entry: dict, decide_fn, now: float) -> str:
    """RESUME_ONLY: release the stale hold (if any) and wake with a RESUME<k> decision. The text is built from the
    stored entry only, so a replay re-sends the same id with the same text: a no-op, never a second wake."""
    if gm.load(mid).get("owner_hold"):
        gm.release_owner_hold(mid, now=now)
    text = (f"Capital resume {entry['k']}: authority {int(entry['authority']):,} already leaves "
            f"{int(entry['headroom']):,} processed tokens of headroom; no top-up was needed. Continue the milestone "
            "where you stopped; every other constraint is unchanged.")
    out = decide_fn(mid, text, decision_id=f"RESUME{entry['k']}")
    _unblock(mid, entry.get("key"), now, f"capital resume {entry['k']} answered the authority block")
    return f"woke={out.get('woke') if isinstance(out, dict) else out}"


def sweep_one(mid: str, *, now: float | None = None, decide_fn=None, sender=None, dry_run: bool = False,
              predictive: bool | None = None, lock_timeout: float = POLL_LOCK_S, cause: str = "poll",
              predictive_only: bool = False) -> dict:
    """One top-up pass over one mission, serialised by the per-mission lock (W3 exactly-once): the poller, an
    in-process capital event, a manual CLI pass and recovery all converge here, so two of them never judge the same
    occurrence at once. A pass that cannot take the lock in `lock_timeout` acts on nothing and says so.
    `predictive` None = CPP_TOPUP_PREDICTIVE (on): the poller reconciles PRESSURE too, in case an event was missed."""
    predictive = predictive_enabled() if predictive is None else (predictive and predictive_enabled())
    if load_policy(mid) is None:
        return {"mission": mid, "action": "none", "why": "no policy"}
    with _Quiet():
        try:
            lock = _topup_lock(mid, lock_timeout)
            lock.__enter__()
        except gm.MissionError as exc:
            return {"mission": mid, "action": "none", "busy": True, "cause": cause,
                    "why": f"another top-up pass holds the lock ({exc}); it judges this occurrence"}
        try:
            return _sweep_one_locked(mid, now=now, decide_fn=decide_fn, sender=sender, dry_run=dry_run,
                                     predictive=predictive, cause=cause, predictive_only=predictive_only)
        finally:
            lock.__exit__(None, None, None)


def _sweep_one_locked(mid: str, *, now, decide_fn, sender, dry_run: bool, predictive: bool, cause: str,
                      predictive_only: bool = False) -> dict:
    now = time.time() if now is None else now
    decide_fn = decide_fn or gm.deliver_decision
    pol = load_policy(mid)   # re-read under the lock: the pass before ours may have written a grant
    if pol is None:
        return {"mission": mid, "action": "none", "why": "no policy"}
    rec = gm.load(mid)
    at_boundary = bool(rec) and (capital_label(rec) is not None or is_authority_trip(rec))
    if predictive_only and at_boundary:
        # review note: pre_launch is authority-only. A launch running the boundary judge on its own record could
        # unblock it under the launch's feet (its claim then CAS-fails); the boundary has its own event and the poller.
        return {"mission": mid, "action": "none", "cause": cause,
                "why": "predictive only: a capital boundary is judged by its own event and the poller"}
    spent = _spent(rec) if rec else None
    lease = next_lease(rec, pol) if (rec and predictive) else None
    pressured = (bool(rec) and predictive and not at_boundary
                 and capital_state(rec, pol, spent, now, lease=lease)["state"] == "PRESSURE")
    # W2: progress = the mission's ledger receipts + its lineage roots' commits (progress_receipts). Read only at a
    # capital boundary or under predictive PRESSURE (W3): nothing else consumes it, and the sweep visits every policy.
    # CPP_PROGRESS_RECEIPTS=off -> HEAD plus every local branch (8c059095), where a NEW unrelated branch still counts.
    if not rec:
        prog = {"measured": False, "why": "no mission record"}
    elif not at_boundary and not pressured:
        prog = {"measured": False, "why": "not at a capital boundary (not read)"}
    elif receipts_enabled():
        prog = progress_receipts(rec, pol)
    else:
        prog = progress_since(mb.execution_root(rec), pol.get("last_head"), pol.get("last_tips"),
                              since=pol.get("last_at") or pol.get("set_at"))
    provider = provider_of(rec, now) if (at_boundary or pressured) else None
    verdict = judge(rec, pol, prog, spent=spent, now=now, predictive=predictive, lease=lease, provider=provider)
    if not dry_run:
        _track_provider_wait(mid, pol, verdict, now)
    if verdict["action"] == "grant" and not dry_run:
        try:   # CCN-3 weekly account ceiling (Owner Q2 = enforce 85%), checked before the grant is written
            import account_governor as _ag
            _code, _verdict, _why, _ = _ag.check(_ag.DEFAULT_STATE, "topup")
        except Exception as exc:  # noqa: BLE001 -- the governor fails open
            _code = 0
            gm.lr.ledger_append(mid, "account_governor_error", mission_id=mid, why=f"{type(exc).__name__}: {exc}"[:300])
        if _code == 3 and verdict.get("predictive"):
            # a running mission is not parked: the governor's no is recorded, the Owner is not told it is parked
            verdict = {**verdict, "action": "none", "why": f"predictive: {_why}"}
        elif _code == 3:
            verdict = {**{k: v for k, v in verdict.items() if k in ("key",)}, "action": "refuse", "why": _why}
    out = {"mission": mid, "cause": cause, **{k: v for k, v in verdict.items() if k != "capital"}}
    if "capital" in verdict:
        out["capital_state"] = verdict["capital"]["state"]
    if dry_run or verdict["action"] == "none":
        return out
    if verdict["action"] in ("grant", "release") and not verdict.get("resume"):
        # W3 CAS: a NEW entry is written only against the record we judged. Progress reading takes seconds; a hold
        # released, an Owner raise or a relaunch in between makes this judgement stale, and the next pass re-judges.
        cur = gm.load(mid)
        if not cur or cur.get("seq") != rec.get("seq"):
            moved = cur.get("seq") if cur else None
            gm.lr.ledger_append(mid, "authority_topup_cas_moved", mission_id=mid, action=verdict["action"],
                                seq_judged=rec.get("seq"), seq_now=moved, cause=cause)
            return {**out, "action": "none", "cas_moved": True,
                    "why": f"record moved since judged (seq {rec.get('seq')} -> {moved}); the next pass re-judges"}
    # the per-occurrence key: a hold's set_at, or a BLOCKED authority park's 'blocked:e<epoch>:<at>' (W1 + 8c059095),
    # or a predictive 'pressure:e<epoch>:a<authority>' (W3)
    hold_at = verdict["key"] if "key" in verdict else rec["owner_hold"].get("set_at")
    if verdict["action"] == "refuse":
        if pol.get("notified_hold_set_at") != hold_at:
            if (verdict.get("capital") or {}).get("dim") == "hours":
                fix = (f"Extend it with: gsd_mission.py authority --mission {mid} --extend-hours H "
                       f"--owner-turn <session>:<timestamp>, then release.")
            else:
                fix = (f"Raise it with: gsd_mission.py authority --mission {mid} --tokens N "
                       f"--owner-turn <session>:<timestamp>, then release.")
            msg = (f"Mission {mid} is parked on its budget and was NOT topped up: {verdict['why']}. "
                   f"Authority {int(rec.get('authority_tokens') or 0):,}. " + fix)
            pol["notified_hold_set_at"] = hold_at
            pol["last_refusal"] = {"at": now, "why": verdict["why"], "notify": notify(msg, sender)}
            save_policy(pol)
            gm.lr.ledger_append(mid, "authority_auto_topup_refused", mission_id=mid, why=verdict["why"],
                                notify=pol["last_refusal"]["notify"])
        out["notify"] = (pol.get("last_refusal") or {}).get("notify")
        return out
    if verdict["action"] == "release":   # RESUME_ONLY: headroom exists; no grant, no capital added
        if not verdict.get("resume"):
            cs = verdict["capital"]["dims"]
            k = len(pol.get("resumes") or []) + 1
            entry = {"k": k, "key": hold_at, "at": now, "authority": cs["authority"], "spent": cs["spent"],
                     "headroom": cs["headroom"], "why": verdict["why"]}
            # Written BEFORE the effect (exactly-once): a pass that dies after this line is completed next pass.
            pol.setdefault("resumes", []).append(entry)
            save_policy(pol)
            gm.lr.ledger_append(mid, "authority_hold_resumed", mission_id=mid,
                                **{x: entry[x] for x in ("k", "authority", "spent", "headroom")})
        out["result"] = _complete_resume(mid, pol["resumes"][-1], decide_fn, now)
        return out
    if verdict["action"] == "grant":
        cur = int(rec.get("authority_tokens") or 0)
        to = cur + int(pol["step"])
        if pol.get("ceiling"):
            to = min(to, int(pol["ceiling"]))   # the last step is clipped: never above the ceiling
        # n is unique per mission across every policy epoch: it names the TOPUP<n> decision, and a reused
        # decision id is a replay no-op that never wakes the worker.
        n = len(pol.get("prior_grants") or []) + len(pol.get("grants") or []) + 1
        grant = {"n": n, "epoch": int(pol.get("policy_epoch") or 0), "at": now, "hold_set_at": hold_at,
                 "from": cur, "to": to, "head": prog["head"], "spent": spent, "why": verdict["why"]}
        # Written BEFORE the effect: a pass that dies after this line is completed (never re-granted) next pass.
        pol.setdefault("grants", []).append(grant)
        # A grant bought by receipts alone on an unreadable root keeps the previous commit base (else None forever).
        pol["last_head"] = prog["head"] or pol.get("last_head")
        pol["last_tips"] = prog.get("tips") if prog["head"] else pol.get("last_tips")
        pol["last_at"] = now
        save_policy(pol)
        gm.lr.ledger_append(mid, "authority_auto_topup", mission_id=mid, cause=cause,
                            predictive=bool(verdict.get("predictive")),
                            **{k: grant[k] for k in ("n", "from", "to", "head", "spent")})
    out["result"] = _complete(mid, pol["grants"][-1], decide_fn, now)
    return out


def _track_provider_wait(mid: str, pol: dict, verdict: dict, now: float) -> None:
    """W5: one ledger row when a capital boundary starts waiting on the provider (or its reset moves), one when the
    wait ends -- written on CHANGE, never every pass. pol["waiting_provider"] carries the open wait (metrics read
    the rows). Runs under the top-up lock (sweep_one), so the policy write cannot race another pass."""
    open_wait = pol.get("waiting_provider")
    if verdict.get("waiting_provider"):
        cs = (verdict.get("capital") or {}).get("dims") or {}
        cur = {"since": (open_wait or {}).get("since", now), "wake_at": verdict.get("wake_at"),
               "class": cs.get("provider_class"), "key": verdict.get("key")}
        if not open_wait or open_wait.get("wake_at") != cur["wake_at"] or open_wait.get("class") != cur["class"]:
            pol["waiting_provider"] = cur
            save_policy(pol)
            gm.lr.ledger_append(mid, "capital_waiting_provider", mission_id=mid, wake_at=cur["wake_at"],
                                provider_class=cur["class"], key=cur["key"], why=str(verdict.get("why"))[:300])
    elif open_wait:
        pol.pop("waiting_provider", None)
        save_policy(pol)
        gm.lr.ledger_append(mid, "capital_provider_cleared", mission_id=mid, waited_s=round(now - open_wait["since"]),
                            wake_at=open_wait.get("wake_at"), late_s=(round(now - open_wait["wake_at"])
                                                                       if open_wait.get("wake_at") else None))


def _decide_deferred(mid: str, text: str, decision_id: str | None = None) -> dict:
    """The event path's decide: the decision is recorded (durable, on every later launch card) but no host call is
    made in-process -- an event fires inside the supervisor's per-mission breaker thread, where `claude stop` +
    continue was measured at over 60 s. The wake becomes the existing `pending_wake` obligation, which the next
    supervise pass delivers to an idle owner or clears for a dead one (the card carries it)."""
    out = gm.deliver_decision(mid, text, decision_id=decision_id, wake=False)
    if out.get("recorded"):
        cur = gm.load(mid)
        if cur and cur.get("state") not in gm.TERMINAL:
            gm.transition(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], event="decision_wake_pending",
                          touch=False, pending_wake={"decision_id": decision_id, "at": time.time(),
                                                     "why": "capital event: wake deferred to the sweep"})
    return {**out, "woke": "deferred to the sweep (pending_wake)"}


def on_capital_event(mid: str, cause: str, *, now: float | None = None, decide_fn=None, sender=None) -> dict | None:
    """W3 (H5): the in-process event path. gsd_mission calls it right after a cost hold, a block, an authority set,
    a cost mark, a forecast recompile and before a relaunch. It runs the same sweep_one as the poller, under the
    same lock, so the poller stays the reconciler and never a second granter. None = not dispatched (switch off,
    no policy, or raised by a top-up pass's own write). A pass in flight -> `busy`, recorded as deferred."""
    if not (enabled() and event_enabled()) or in_capital_pass():
        return None
    try:
        if not policy_path(mid).exists():
            return None
        out = sweep_one(mid, now=now, decide_fn=decide_fn or _decide_deferred, sender=sender,
                        predictive=cause in PREDICTIVE_CAUSES, lock_timeout=EVENT_LOCK_S, cause=cause,
                        predictive_only=cause == "pre_launch")
    except Exception as exc:  # noqa: BLE001 -- an event never breaks the write that raised it; the poller reconciles
        gm.lr.ledger_append(mid, "capital_event_error", mission_id=mid, cause=cause,
                            error=f"{type(exc).__name__}: {exc}"[:300])
        return {"mission": mid, "action": "error", "cause": cause, "why": f"{type(exc).__name__}: {exc}"[:300]}
    if out.get("busy"):
        gm.lr.ledger_append(mid, "capital_event_deferred", mission_id=mid, cause=cause, why=out["why"][:300])
    elif out.get("action") not in (None, "none"):
        gm.lr.ledger_append(mid, "capital_event", mission_id=mid, cause=cause, action=out["action"],
                            why=str(out.get("why"))[:300])
    return out


def adopt_defaults(now: float | None = None) -> list[str]:
    """Give the 2x default policy to every live mission parked on its authority trip that has no policy (addendum
    2026-11-16). Base = the head its binding recorded at arm, so only work done since arm counts as progress."""
    if not default_enabled():
        return []
    now = time.time() if now is None else now
    adopted = []
    for rec in gm.all_missions():
        mid = rec.get("mission_id")
        auth = int(rec.get("authority_tokens") or 0)
        parked = capital_label(rec) if capital_state_enabled() else is_authority_trip(rec)
        if (not mid or rec.get("state") in gm.TERMINAL or not parked or auth <= 0
                or policy_path(mid).exists()):
            continue
        terms = default_terms(auth)
        base = (rec.get("binding") or {}).get("head")
        if not base and rec.get("created_at"):   # never bound: the root's last commit at arm time
            out = _git(mb.execution_root(rec), "rev-list", "-1", f"--before=@{int(rec['created_at'])}", "HEAD")
            base = out.strip() if out else None
        pol = {"schema": SCHEMA, "mission_id": mid, "grants": [], "authority": auth, "set_at": now,
               "reason": f"default policy (Owner 2026-11-16): ceiling {ceiling_x():g}x authority, commits-gated",
               "last_head": base, "last_at": rec.get("created_at"), "default": True, **terms}
        save_policy(pol)
        gm.lr.ledger_append(mid, "authority_topup_policy", mission_id=mid, authority=auth, default=True, **terms)
        adopted.append(mid)
    return adopted


def sweep(*, now: float | None = None, decide_fn=None, sender=None, dry_run: bool = False) -> list[dict]:
    if not enabled():
        return [{"action": "none", "why": "CPP_MISSION_AUTO_TOPUP=off"}]
    res = []
    if not dry_run:
        try:
            adopt_defaults(now)
        except Exception as exc:  # noqa: BLE001 -- adoption failure must not stop the explicit policies
            res.append({"action": "error", "why": f"adopt_defaults: {type(exc).__name__}: {exc}"[:300]})
    for p in sorted(Path(gm.lr.state_dir()).glob("mission-topup-m-*.json")):
        mid = p.stem[len("mission-topup-"):]
        try:
            res.append(sweep_one(mid, now=now, decide_fn=decide_fn, sender=sender, dry_run=dry_run))
        except Exception as exc:  # noqa: BLE001 -- one mission's failure must not stop the others
            gm.lr.ledger_append(mid, "authority_auto_topup_error", mission_id=mid,
                                error=f"{type(exc).__name__}: {exc}"[:300])
            res.append({"mission": mid, "action": "error", "why": f"{type(exc).__name__}: {exc}"[:300]})
    return res


def budget(mid: str, authority, topups: int | None, step, reason: str = "", now: float | None = None,
           ceiling=None, owner_turn: str | None = None, receipt=None) -> dict:
    """topups=None derives them from the ceiling (default 2x authority); an explicit topups keeps the old
    behaviour, bounded only by an explicit ceiling. W3: its set_authority raises no capital event (the policy it
    is about to write would be judged half-written), and it holds the top-up lock so no pass judges mid-re-budget.
    W4: `owner_turn` (verified here) or `receipt` (an Owner turn verified on another host, HMAC-signed) gives the
    policy its provenance. A receipt's signed authority/ceiling/step ARE the policy: a figure given here must equal
    them, and the same receipt applied again is a no-op (a replay would otherwise open a fresh policy epoch and
    restore top-ups the Owner already granted once)."""
    with _Quiet(), _topup_lock(mid, POLL_LOCK_S):
        if receipt is not None:
            import authority_receipt as ar
            rec = gm.load(mid)
            if rec is None:
                raise gm.MissionError(f"no mission {mid}")
            try:
                signed = ar.verify(receipt, rec, "authority", now=now)
            except ar.ReceiptError as exc:
                raise gm.MissionError(f"receipt refused: {exc}") from None
            t = signed["terms"]
            if t.get("tokens") is None or t.get("ceiling") is None or t.get("step") is None:
                raise gm.MissionError("receipt refused: a budget needs a receipt that signs tokens, ceiling and step")
            for name, given, want in (("authority", authority, t["tokens"]), ("ceiling", ceiling, t["ceiling"]),
                                      ("step", step, t["step"])):
                if given is not None and parse_tokens(given) != want:
                    raise gm.MissionError(f"receipt refused: {name} {given!r} is not the signed {want:,}")
            if topups is not None:
                raise gm.MissionError("receipt refused: a receipt budget derives its top-ups from the signed ceiling")
            prior = load_policy(mid) or {}
            if signed["nonce"] in [c.get("nonce") for c in prior.get("receipts") or []]:
                gm.lr.ledger_append(mid, "authority_receipt_replay_noop", mission_id=mid, nonce=signed["nonce"],
                                    key_id=signed["key_id"])
                return prior
            authority, ceiling, step = t["tokens"], t["ceiling"], t["step"]
            reason = reason or f"Owner budget by portable receipt from {signed['source']['host']}"
        else:
            signed = None
            if owner_turn:   # the same replay rule for a local Owner turn
                turn = gm.verify_owner_turn(owner_turn)
                prior = load_policy(mid) or {}
                # review M2: every Owner turn a budget ever consumed, across epochs -- not only the latest policy's
                spent_turns = set(prior.get("owner_turns") or []) | {prior.get("owner_turn")}
                if turn.get("uuid") and turn.get("uuid") in spent_turns:
                    gm.lr.ledger_append(mid, "authority_receipt_replay_noop", mission_id=mid, owner_turn=turn["uuid"])
                    return prior
        pol = _budget(mid, authority, topups, step, reason=reason, now=now, ceiling=ceiling,
                      owner_turn=owner_turn, receipt=receipt, signed=signed)
    on_capital_event(mid, "budget")   # judged once the new policy is whole, outside budget's own lock
    return pol


def _budget(mid: str, authority, topups: int | None, step, reason: str = "", now: float | None = None,
            ceiling=None, owner_turn: str | None = None, receipt=None, signed: dict | None = None) -> dict:
    now = time.time() if now is None else now
    rec = gm.load(mid)
    if rec is None:
        raise gm.MissionError(f"no mission {mid}")
    if topups is not None and topups < 0:
        raise ValueError("--topups must be >= 0")
    auth, stp = parse_tokens(authority), parse_tokens(step)
    ceil_tokens = parse_tokens(ceiling) if ceiling is not None else None
    if ceil_tokens is not None and ceil_tokens < auth:
        raise ValueError("--ceiling must be >= --authority")
    if topups is None:
        terms = default_terms(auth, stp)
        if ceil_tokens is not None:
            room = ceil_tokens - auth
            terms = {"ceiling": ceil_tokens, "step": min(stp, room) if room else stp,
                     "max_topups": (-(-room // min(stp, room))) if room else 0}
    else:
        terms = {"ceiling": ceil_tokens, "step": stp, "max_topups": int(topups)}
    pol = load_policy(mid)
    # W1 item 7, half-applied grant: the last current-epoch grant was written (before its effect) but its raise never
    # landed. It is VOIDED, explicitly, not completed: the Owner's re-budget is the newer authority statement, and
    # completing would apply (and wake under) a raise the Owner is replacing in this same call -- set_authority
    # below would overwrite it at once. Read BEFORE set_authority, which moves the authority it is compared with.
    cur_auth = int(rec.get("authority_tokens") or 0)
    last = ((pol or {}).get("grants") or [None])[-1]
    if last and not last.get("voided") and int(last.get("to") or 0) > cur_auth:
        why_void = (f"re-budget to {auth:,} before grant {last.get('n')} applied (to {int(last['to']):,} > "
                    f"authority {cur_auth:,}); superseded by the Owner budget")
        last["voided"] = {"at": now, "why": why_void}
        gm.lr.ledger_append(mid, "authority_topup_voided", mission_id=mid, n=last.get("n"), to=last.get("to"),
                            authority=cur_auth, reason=why_void)
    out = gm.set_authority(mid, tokens=auth, now=now, reason=reason or "Owner budget at arm (mission-auto-topup)",
                           owner_turn=owner_turn, receipt=receipt)
    last_receipt = (out.get("authority_receipts") or [{}])[-1] if out else {}
    if (owner_turn or receipt) and out and out.get("seq") == rec.get("seq"):
        # review M2: set_authority answered a replay of an Owner act already applied (authority_replay_noop, record
        # untouched). A new policy epoch here would restore top-ups that act's policy already granted.
        gm.lr.ledger_append(mid, "authority_receipt_replay_noop", mission_id=mid, via="set_authority",
                            owner_turn=(last_receipt.get("owner_turn") or {}).get("uuid"))
        return pol or load_policy(mid) or {}
    if pol is None:
        pol = {"schema": SCHEMA, "mission_id": mid, "grants": [], "prior_grants": [], "policy_epoch": 0}
    else:   # H6: a re-set policy opens a new epoch; the old grants are kept but no longer count against it
        pol["prior_grants"] = list(pol.get("prior_grants") or []) + list(pol.get("grants") or [])
        pol["grants"] = []
        pol["policy_epoch"] = int(pol.get("policy_epoch") or 0) + 1
    topups, stp = terms["max_topups"], terms["step"]
    # W4: the policy names its own provenance, so a top-up granted under it inherits a named Owner act (or is seen
    # to inherit none).
    prov = "portable_receipt" if signed else ("owner_turn" if owner_turn else "none")
    pol.update({"authority": auth, "max_topups": int(topups), "step": stp, "ceiling": terms["ceiling"],
                "set_at": now, "reason": reason, "last_head": head_of(mb.execution_root(rec)),
                "last_tips": branch_tips(mb.execution_root(rec)), "last_at": now, "provenance": prov,
                "owner_turn": (last_receipt.get("owner_turn") or {}).get("uuid") if prov != "none" else None})
    if pol["owner_turn"]:   # review M2: consumed turns survive later epochs (the replay check reads all of them)
        pol["owner_turns"] = (list(pol.get("owner_turns") or []) + [pol["owner_turn"]])[-50:]
    if signed:
        pol["receipts"] = (list(pol.get("receipts") or []) + [
            {"nonce": signed["nonce"], "key_id": signed["key_id"], "host": signed["source"]["host"],
             "turn": signed["source"]["uuid"], "at": now, "policy_epoch": pol["policy_epoch"]}])[-20:]
    save_policy(pol)
    gm.lr.ledger_append(mid, "authority_topup_policy", mission_id=mid, authority=auth, max_topups=topups, step=stp,
                        policy_epoch=pol["policy_epoch"], provenance=prov)
    return pol


# W5 metrics. A refusal whose why names an Owner rule is a legitimate interrupt. Any other refusal is listed for
# review: it is not called avoidable, because the ledger alone cannot prove that.
LEGIT_REFUSAL = ("ceiling reached", "hours exhausted", "top-ups exhausted", "no progress", "weekly")
_PARK_END = ("owner_hold_released", "mission_unblocked", "mission_closed")
_TOPUP_REASON = re.compile(r"\b(?:auto|predictive) top-up \d+ under Owner policy")


def _pct(xs: list, q: float):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * (len(s) - 1) + 0.5))]


def capital_metrics(mid: str, now: float | None = None, events: list | None = None) -> dict:
    """W5, from the ledger only (spec "W5"). A capital park starts at an authority hold (owner_hold_set naming the
    mission authority) or at a worker's authority ask (mission_blocked with OWNER_BOUNDARY (AUTHORITY) /
    CAPITAL_EXHAUSTED). It ends at release, unblock, close or a terminal state; at the end of the ledger it is still open.
    - authorized_capital_stall_s: the time spent in parks that ended without a new Owner act (an auto top-up under the
      Owner's policy, or a resume over authority that already existed). The capital had been authorized and the
      runtime was the one waiting. This is the plan's H4/H5 cost.
    - owner_boundary_s: the time spent in parks that ended on an Owner raise (owner_turn, portable_receipt, or none
      for a hand raise).
    - open_s: the time spent in parks that are still open, from their start to now.
    - renewal_latency_s: park start to the auto grant or resume.
    - owner_interrupts: the refusal notices. "legitimate" means the why names an Owner rule; anything else is listed
      under "review".
    - predictive_rate: predictive grants divided by all grants. provider_waits are read from the W5 rows."""
    now = time.time() if now is None else now
    ev = events if events is not None else gm.lr.ledger_events(mid)
    parks, cur = [], None
    refusals, grants, waits = [], [], []
    for e in ev:
        name, reason = e.get("event"), str(e.get("reason") or "")
        t = gm.lr._parse_iso(e.get("ts")) or e.get("at")
        if t is None:
            continue
        if cur is not None:
            if name == "capital_provider_cleared":   # review L2: the provider's share of this park, booked apart
                cur["provider_s"] = cur.get("provider_s", 0) + int(e.get("waited_s") or 0)
            if name in ("authority_auto_topup", "authority_hold_resumed") and cur["by"] is None:
                cur["by"], cur["renewed_at"] = "auto", t
            elif name == "authority_set" and cur["by"] is None:
                # auto only by provenance, or (rows before W4) by the top-up's OWN reason format. Measured on GEX44
                # m-76e04d86896d: the Owner's 08:50 hand raise read "Owner-approved top-up 1 of 2", so a bare
                # "top-up" match counted an Owner act as the runtime's.
                prov = (e.get("receipt") or {}).get("provenance")
                if prov != "topup_policy" and not (prov is None and _TOPUP_REASON.search(reason)):
                    cur["by"] = "owner"
            # A hold park ends at its release. A BLOCKED park ends at the first row that is no longer BLOCKED: there,
            # D2 continued the turn (turn_continued, LAUNCHING) with no mission_unblocked row at all.
            st = e.get("state")
            if (name in _PARK_END or st in gm.TERMINAL
                    or (cur["kind"] == "blocked" and st is not None and st != gm.BLOCKED)):
                cur["end"] = t
                parks.append(cur)
                cur = None
        if cur is None:   # the row that ended one park can open the next (a hold set on the relaunched worker)
            if name == "owner_hold_set" and "(mission authority)" in reason:
                cur = {"start": t, "end": None, "by": None, "kind": "hold"}
            elif name == "mission_blocked" and (AUTHORITY_ASK in reason or CAPITAL_EXHAUSTED in reason):
                cur = {"start": t, "end": None, "by": None, "kind": "blocked"}
    for e in ev:
        if e.get("event") == "authority_auto_topup_refused":
            why = str(e.get("why") or "")
            refusals.append({"why": why[:160], "legitimate": any(k in why for k in LEGIT_REFUSAL)})
        elif e.get("event") == "authority_auto_topup":
            grants.append(bool(e.get("predictive")))
        elif e.get("event") == "capital_provider_cleared":
            waits.append(int(e.get("waited_s") or 0))
    if cur is not None:
        parks.append(cur)
    by = {"auto": 0.0, "owner": 0.0, "other": 0.0}
    open_s, lat, prov_s = 0.0, [], 0.0
    for p in parks:
        dur = (now if p["end"] is None else p["end"]) - p["start"]
        pw = min(dur, float(p.get("provider_s") or 0))   # review L2: provider time is not the runtime's stall
        prov_s += pw
        if p["end"] is None:
            open_s += dur - pw
            continue
        by[p["by"] or "other"] += dur - pw
        if p["by"] == "auto":
            lat.append(p["renewed_at"] - p["start"])
    rec = gm.load(mid)

    def _iso(t):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t)) if t else None
    return {"mission": mid, "parks": len(parks), "open_parks": sum(1 for p in parks if p["end"] is None),
            "provider_wait_in_parks_s": round(prov_s),
            "last_parks": [{"start": _iso(p["start"]), "end": _iso(p["end"]), "by": p["by"] or ("open" if p["end"]
                            is None else "other"), "s": round((p["end"] or now) - p["start"])} for p in parks[-5:]],
            "authorized_capital_stall_s": round(by["auto"]), "owner_boundary_s": round(by["owner"]),
            "other_park_s": round(by["other"]), "open_s": round(open_s),
            "renewal_latency_s": {"n": len(lat), "p50": _pct(lat, 0.5) and round(_pct(lat, 0.5)),
                                  "max": round(max(lat)) if lat else None},
            "owner_interrupts": {"legitimate": sum(1 for r in refusals if r["legitimate"]),
                                 "review": [r["why"] for r in refusals if not r["legitimate"]][-5:]},
            "grants": len(grants), "predictive_grants": sum(grants),
            "predictive_rate": round(sum(grants) / len(grants), 3) if grants else None,
            "provider_waits": {"n": len(waits), "waited_s": sum(waits)},
            # from the record's typed receipts (authority_lineage's count), without its full-ledger read: the census
            # calls this once per mission (measured 121 s over 534 missions on GEX44 when it re-read the ledger)
            "receipt_less_raises": (sum(1 for r in rec.get("authority_receipts") or []
                                        if isinstance(r, dict) and r.get("provenance") == "none") if rec else None)}


def open_phases(repo: str) -> int | None:
    """Unchecked phase lines in .planning/ROADMAP.md (`- [ ] **Phase N`); None when there is no roadmap."""
    p = Path(repo) / ".planning" / "ROADMAP.md"
    if not p.is_file():
        return None
    return len(re.findall(r"^\s*-\s*\[ \]\s*\**\s*Phase\b", p.read_text(encoding="utf-8", errors="replace"),
                          flags=re.M | re.I))


def suggest(repo: str, phases: int | None = None) -> dict:
    rate = parse_tokens(os.environ.get("CPP_MISSION_PHASE_TOKENS") or DEFAULT_PHASE_TOKENS)
    n = phases if phases is not None else open_phases(repo)
    basis = "ROADMAP.md open phases" if phases is None and n is not None else "given"
    if n is None:
        n, basis = 3, "no ROADMAP.md: assumed 3 phases"
    auth = max(1, n) * rate
    return {"phases": n, "basis": basis, "rate": rate, "authority": auth, "topups": 3, "step": rate}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("budget")
    b.add_argument("--mission", required=True)
    b.add_argument("--authority", default=None, help="REQUIRED unless --receipt (which signs it)")
    b.add_argument("--topups", type=int, default=None,
                   help="explicit count; omitted = derived from the ceiling (default 2x authority)")
    b.add_argument("--ceiling", default=None, help="hard authority ceiling for auto top-ups, e.g. 240M")
    b.add_argument("--step", default=None, help="top-up step (default 40M; a --receipt signs its own)")
    b.add_argument("--reason", default="")
    b.add_argument("--owner-turn", default=None, help="W4: <session>:<timestamp> of the Owner's message setting this "
                                                      "budget (verified here); without it the raise is flagged")
    b.add_argument("--receipt", default=None, help="W4: a signed authority receipt (file or ar1. token) issued "
                                                   "where the Owner typed it; it signs authority, ceiling and step")
    s = sub.add_parser("suggest")
    s.add_argument("--cwd", default=".")
    s.add_argument("--phases", type=int)
    w = sub.add_parser("sweep")
    w.add_argument("--dry-run", action="store_true")
    t = sub.add_parser("status")
    t.add_argument("--mission", required=True)
    c = sub.add_parser("census", help="W5 historical capital-stall census over the whole ledger")
    c.add_argument("--days", type=float, default=None, help="only ledger rows from the last N days")
    a = ap.parse_args(argv)
    if a.cmd == "budget":
        if a.receipt is None and a.authority is None:
            ap.error("budget needs --authority (or --receipt)")
        step = a.step if (a.step is not None or a.receipt is not None) else "40M"
        try:
            pol = budget(a.mission, a.authority, a.topups, step, a.reason, ceiling=a.ceiling,
                         owner_turn=a.owner_turn, receipt=a.receipt)
        except gm.MissionError as exc:
            print(f"BUDGET REFUSED: {exc}", file=sys.stderr)
            return 3
        ceil = f"{pol['ceiling']:,}" if pol.get("ceiling") else "none"
        print(f"BUDGET SET mission={a.mission} authority={pol['authority']:,} topups={pol['max_topups']} "
              f"step={pol['step']:,} ceiling={ceil} base_head={str(pol['last_head'])[:8]}")
    elif a.cmd == "suggest":
        r = suggest(a.cwd, a.phases)
        print(f"SUGGEST phases={r['phases']} ({r['basis']}) x {r['rate']:,} = authority {r['authority']:,}; "
              f"run: mission_topup.py budget --mission <id> --authority {r['authority'] // 1_000_000}M "
              f"--step {r['step'] // 1_000_000}M  (top-ups derived: ceiling {ceiling_x():g}x)")
    elif a.cmd == "sweep":
        for r in sweep(dry_run=a.dry_run):
            if r.get("action") not in ("none",):
                print(f"TOPUP {r.get('mission')} {r['action']}: {r['why']} {r.get('result') or r.get('notify') or ''}")
    elif a.cmd == "status":
        # W5: the policy, the capital state now, and the ledger metrics (spec "W5"), in one read for the Owner packet
        rec, pol, now = gm.load(a.mission), load_policy(a.mission), time.time()
        cs = None
        if rec:
            spent = _spent(rec)
            at_b = capital_label(rec) is not None
            cs = capital_state(rec, pol, spent, now, lease=next_lease(rec, pol),
                               provider=provider_of(rec, now) if at_b else None)
        print(json.dumps({"policy": pol, "capital": cs, "metrics": capital_metrics(a.mission, now)}, indent=1,
                         default=str))
    elif a.cmd == "census":
        print(json.dumps(census(since_days=a.days), indent=1, default=str))
    return 0


def census(since_days: float | None = None, now: float | None = None) -> dict:
    """W5 historical stall census: capital_metrics for every mission in the ledger, read once and grouped. Totals
    are sums of named figures. A mission with no capital park is counted but not listed."""
    now = time.time() if now is None else now
    by_mid: dict = {}
    cutoff = now - since_days * 86400 if since_days else None
    with open(gm.lr.ledger_path(), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            mid = e.get("mission_id") or e.get("session_id")
            if not str(mid or "").startswith("m-"):
                continue
            if cutoff is not None and (gm.lr._parse_iso(e.get("ts")) or now) < cutoff:
                continue
            by_mid.setdefault(mid, []).append(e)
    rows = [capital_metrics(mid, now, events=ev) for mid, ev in sorted(by_mid.items())]
    parked = [r for r in rows if r["parks"]]
    keys = ("authorized_capital_stall_s", "owner_boundary_s", "other_park_s", "open_s", "provider_wait_in_parks_s",
            "grants", "predictive_grants")
    tot = {k: sum(int(r[k] or 0) for r in parked) for k in keys}
    tot["owner_interrupts_legitimate"] = sum(r["owner_interrupts"]["legitimate"] for r in parked)
    tot["owner_interrupts_review"] = sum(len(r["owner_interrupts"]["review"]) for r in parked)
    lat = [r["renewal_latency_s"]["p50"] for r in parked if r["renewal_latency_s"]["p50"] is not None]
    return {"missions": len(rows), "with_capital_parks": len(parked), "since_days": since_days, "totals": tot,
            "renewal_latency_p50_of_p50s_s": _pct(lat, 0.5),
            "top_stalls": sorted(({"mission": r["mission"], "authorized_capital_stall_s": r["authorized_capital_stall_s"],
                                   "open_s": r["open_s"], "parks": r["parks"]} for r in parked),
                                 key=lambda x: -(x["authorized_capital_stall_s"] + x["open_s"]))[:10]}


if __name__ == "__main__":
    # W3 review MEDIUM-1: run as a script (the `sweep` poller, the `budget` CLI), this module is `__main__`, and
    # gsd_mission's `import mission_topup` would load a SECOND copy whose reentrancy depth is 0: a grant's own
    # set_authority event then waited on the lock its own pass held (21.4 s, a false capital_event_deferred row).
    sys.modules["mission_topup"] = sys.modules[__name__]
    sys.exit(main())
