#!/usr/bin/env python
"""Read-only consistency checker across the ledgers, chains, worktrees and resumption files.

    python tools/cpp_fsck.py [--state DIR] [--projects DIR] [--repo DIR] [--lifecycle FILE]
                             [--programmes DIR] [--chain PATH --tick-log PATH] [--now EPOCH]

Zero model cost, never mutates anything, prints repairs as existing commands only. Output is one JSON object
{"findings": [...], "unknown": [...], "info": {...}, "checks": {id: "PASS|FINDING|UNKNOWN"}}.
Exit 0 = every check clean, 1 = a finding exists, 2 = a check could not see its subject.
A missing or unreadable source is UNKNOWN, never PASS: a negative result needs proof the observer could see.

Checks (each from a production incident on 2026-10-23):
  F1 stranded_lease              open reserve > 24 h whose session has no transcript write in 24 h
  F2 parked_chain_polled         parked chain whose tick log shows non-parked actions after the chain file's mtime
  F3 worktree_without_lifecycle  dirty worktree with no lifecycle row (clean ones listed as info)
  F4 stale_resumption            RESUMPTION_FILE anchor sha not an ancestor of HEAD (no anchor = UNKNOWN_FRESHNESS)
  F5 capsule_without_disposition capsule PENDING / CLAIMED_NO_VERDICT older than 24 h
  F6 denominators_unlabelled     goal-status summary lacks scope / lease / programme_executable
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

DAY_S = 24 * 3600
HOME_CLAUDE = Path.home() / ".claude"
PARKED_OK = {"parked", "held"}
SETTLE_FIX = "python tools/mission_spend.py goal-settle --goal {g} --session {s}"
STATUS_KEYS = ("scope", "lease", "programme_executable")


class Result:
    def __init__(self) -> None:
        self.findings: list[dict] = []
        self.unknown: list[dict] = []
        self.info: dict = {}
        self.checks: dict = {}

    def finding(self, check: str, **kw) -> None:
        self.findings.append({"check": check, **kw})

    def unk(self, check: str, **kw) -> None:
        self.unknown.append({"check": check, **kw})

    def close(self, check: str) -> None:
        if any(f["check"] == check for f in self.findings):
            self.checks[check] = "FINDING"
        elif any(u["check"] == check for u in self.unknown):
            self.checks[check] = "UNKNOWN"
        else:
            self.checks[check] = "PASS"

    def exit_code(self) -> int:
        if self.findings:
            return 1
        return 2 if self.unknown else 0

    def as_dict(self) -> dict:
        d = {"findings": self.findings, "unknown": self.unknown, "checks": self.checks}
        if self.info:
            d["info"] = self.info
        return d


def _jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


# git is not on the laptop's non-interactive PATH; a bare "git" raised FileNotFoundError there (2026-10-23).
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, "-C", str(repo), *args], capture_output=True, text=True, timeout=60)


# --- F1 ------------------------------------------------------------------------------------------
def _transcript_mtime(projects: Path, sid: str) -> float | None:
    best = None
    for p in projects.glob(f"**/{sid}.jsonl"):
        m = p.stat().st_mtime
        best = m if best is None else max(best, m)
    return best


def check_stranded_lease(r: Result, state: Path, projects: Path, now: float) -> None:
    c = "stranded_lease"
    base = state / "goal-budget"
    if not base.is_dir():
        r.unk(c, why=f"no goal-budget directory at {base}")
        return
    journals = sorted(base.glob("*/spend.journal.jsonl"))
    if not journals:
        r.unk(c, why=f"no spend.journal.jsonl under {base}")
        return
    projects_ok = projects.is_dir()
    for jp in journals:
        goal = jp.parent.name
        try:
            rows = _jsonl(jp)
        except OSError as e:
            r.unk(c, goal=goal, why=f"unreadable journal: {e}")
            continue
        closed = {rid for x in rows if x.get("op") == "settle" for rid in x.get("closes", [])}
        leaked = {x.get("id") for x in rows if x.get("op") == "leak"}
        for x in rows:
            if x.get("op") != "reserve" or x.get("id") in closed:
                continue
            age = now - float(x.get("ts", now))
            if age <= DAY_S:
                continue
            sid = x.get("sid", "")
            if not projects_ok:
                r.unk(c, goal=goal, session=sid, why=f"transcript root {projects} missing")
                continue
            mt = _transcript_mtime(projects, sid)
            if mt is None:
                r.unk(c, goal=goal, session=sid, why="transcript not found")
            elif now - mt > DAY_S:
                r.finding(c, goal=goal, session=sid, reserve=x.get("id"), amount=x.get("amount"),
                          state="LEAKED" if x.get("id") in leaked else "RESERVED",
                          age_h=round(age / 3600, 1), repair=SETTLE_FIX.format(g=goal, s=sid))


# --- F2 ------------------------------------------------------------------------------------------
def _tick_action(line: str) -> tuple[str, str] | None:
    parts = line.split(None, 1)
    if len(parts) < 2:
        return None
    rest = parts[1]
    first = rest.split()[0]
    if not first.startswith("rc="):
        return parts[0], first
    m = re.search(r'"action"\s*:\s*"([^"]+)"', rest)
    return parts[0], m.group(1) if m else "unknown"


def check_parked_chain(r: Result, chain: Path | None, tick_log: Path | None) -> None:
    c = "parked_chain_polled"
    if chain is None or tick_log is None:
        r.unk(c, why="no --chain / --tick-log given")
        return
    try:
        data = json.loads(chain.read_text(encoding="utf-8"))
        cmt = chain.stat().st_mtime
        lines = tick_log.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, ValueError) as e:
        r.unk(c, why=f"unreadable: {e}")
        return
    if not data.get("parked"):
        return
    bad = []
    for ln in lines:
        t = _tick_action(ln)
        if not t:
            continue
        try:
            ts = dt.datetime.fromisoformat(t[0]).timestamp()
        except ValueError:
            continue
        if ts > cmt and t[1] not in PARKED_OK:
            bad.append({"at": t[0], "action": t[1]})
    if bad:
        r.finding(c, chain=str(chain), polls=bad[:10], count=len(bad),
                  repair="read `parked` before the RAM pre-check in chain_tick.ps1, or unpark: "
                         "python tools/gsdx_chain.py tick --chain <chain> --dry-run")


# --- F3 ------------------------------------------------------------------------------------------
def _norm(p: str) -> str:
    return p.replace("\\", "/").rstrip("/").lower()


def check_worktrees(r: Result, repo: Path, lifecycle: Path) -> None:
    c = "worktree_without_lifecycle"
    try:
        rows = json.loads(lifecycle.read_text(encoding="utf-8")).get("rows", {})
    except (OSError, ValueError) as e:
        r.unk(c, why=f"lifecycle file unreadable: {e}")
        return
    cp = _git(repo, "worktree", "list", "--porcelain")
    if cp.returncode != 0:
        r.unk(c, why=f"git worktree list failed: {cp.stderr.strip()[:200]}")
        return
    known = {_norm(k) for k in rows}
    clean = []
    for ln in cp.stdout.splitlines():
        if not ln.startswith("worktree "):
            continue
        path = ln[len("worktree "):]
        if _norm(path) in known:
            continue
        st = _git(Path(path), "status", "--porcelain")
        if st.returncode != 0:
            r.unk(c, worktree=path, why=f"git status failed: {st.stderr.strip()[:200]}")
        elif st.stdout.strip():
            r.finding(c, worktree=path, dirty_paths=len(st.stdout.splitlines()),
                      repair="classify it in vault/estate/worktree-lifecycle.json (state + reason + salvage)")
        else:
            clean.append(path)
    r.info["unclassified_clean"] = clean


# --- F4 ------------------------------------------------------------------------------------------
def check_resumption(r: Result, repo: Path, programmes: Path) -> None:
    c = "stale_resumption"
    files = sorted(programmes.glob("*/RESUMPTION_FILE.md"))
    if not files:
        r.unk(c, why=f"no RESUMPTION_FILE.md under {programmes}")
        return
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as e:
            r.unk(c, file=str(f), why=str(e))
            continue
        line = next((x for x in text.splitlines() if re.search(r"coherence anchor", x, re.I)), None)
        sha = None
        if line:
            sha = next((t for t in re.findall(r"\b[0-9a-f]{7,40}\b", line) if re.search(r"\d", t)), None)
        if not sha:
            r.unk(c, file=str(f), verdict="UNKNOWN_FRESHNESS", why="no anchor sha")
            continue
        cp = _git(repo, "merge-base", "--is-ancestor", sha, "HEAD")
        if cp.returncode == 1:
            r.finding(c, file=str(f), anchor=sha, verdict="STALE",
                      repair="regenerate the file from the ledger and a HEAD anchor, then re-run cpp_fsck")
        elif cp.returncode != 0:
            r.unk(c, file=str(f), anchor=sha, verdict="UNKNOWN_FRESHNESS",
                  why=f"git could not resolve the anchor: {cp.stderr.strip()[:200]}")


# --- F5 ------------------------------------------------------------------------------------------
def check_capsules(r: Result, state: Path, now: float) -> None:
    c = "capsule_without_disposition"
    # rollover.py writes under state/rollover/ (its STATE_DIR); a flat state/ ledger is the fixture layout.
    path = state / "rollover" / "rollover-ledger.jsonl"
    if not path.exists():
        path = state / "rollover-ledger.jsonl"
    try:
        rows = _jsonl(path)
    except OSError as e:
        r.unk(c, why=f"rollover ledger unreadable: {e}")
        return
    import rollover
    for cap in rollover.dispositions(rows)["capsules"]:
        if cap["disposition"] not in ("PENDING", "CLAIMED_NO_VERDICT"):
            continue
        try:
            sealed = dt.datetime.fromisoformat(cap["sealed_at"]).timestamp()
        except ValueError:
            r.unk(c, session=cap["session_id"], why=f"unparseable sealed_at {cap['sealed_at']}")
            continue
        if now - sealed > DAY_S:
            r.finding(c, session=cap["session_id"], sealed_at=cap["sealed_at"], disposition=cap["disposition"],
                      repair=f"python tools/rollover.py resume --from {cap['session_id']}")


# --- F6 ------------------------------------------------------------------------------------------
def check_denominators(r: Result) -> None:
    c = "denominators_unlabelled"
    from modules.provider_routing.ledger import GoalLedger
    with tempfile.TemporaryDirectory() as td:
        g = GoalLedger(Path(td), "fsck-probe")
        g._append([], {"op": "cap", "value": 1000, "source": "fsck"})
        summary = GoalLedger._summary(g._gfold(g._read()))
    missing = [k for k in STATUS_KEYS if k not in summary]
    if missing:
        r.finding(c, missing=missing, repair="restore GoalLedger._summary labels (commit 2259ca87)")


# --- driver --------------------------------------------------------------------------------------
def run(a: argparse.Namespace) -> Result:
    r = Result()
    now = a.now if a.now is not None else time.time()
    steps = [
        ("stranded_lease", lambda: check_stranded_lease(r, a.state, a.projects, now)),
        ("parked_chain_polled", lambda: check_parked_chain(r, a.chain, a.tick_log)),
        ("worktree_without_lifecycle", lambda: check_worktrees(r, a.repo, a.lifecycle)),
        ("stale_resumption", lambda: check_resumption(r, a.repo, a.programmes)),
        ("capsule_without_disposition", lambda: check_capsules(r, a.state, now)),
        ("denominators_unlabelled", lambda: check_denominators(r)),
    ]
    for cid, fn in steps:
        try:
            fn()
        except Exception as e:  # noqa: BLE001 -- a check that crashed saw nothing: UNKNOWN, never PASS
            r.unk(cid, why=f"{type(e).__name__}: {e}")
        r.close(cid)
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", type=Path, default=HOME_CLAUDE / "state")
    ap.add_argument("--projects", type=Path, default=HOME_CLAUDE / "projects")
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--lifecycle", type=Path, default=ROOT / "vault/estate/worktree-lifecycle.json")
    ap.add_argument("--programmes", type=Path, default=ROOT / "vault/programs")
    ap.add_argument("--chain", type=Path)
    ap.add_argument("--tick-log", type=Path, default=None)
    ap.add_argument("--now", type=float)
    a = ap.parse_args(argv)
    r = run(a)
    print(json.dumps(r.as_dict(), indent=1, ensure_ascii=False))
    return r.exit_code()


if __name__ == "__main__":
    sys.exit(main())
