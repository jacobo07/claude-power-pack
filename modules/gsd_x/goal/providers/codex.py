#!/usr/bin/env python3
"""Codex as a goal epoch: headless, bounded, and careful with a shared account.

Codex gives the goal spine what nothing else does -- a FRESH CONTEXT executor
that needs no pane and no human. That is why it is in v1 at all.

THE ACCOUNT IS SHARED. This is not a metered API key; it is the Owner's single
ChatGPT/Codex session, already used by Hermes' chat tier and the Studio image
tier. Those enforce their limits in ONE process with an asyncio lock and an
in-memory cooldown, neither of which a separate process can see. So this
provider treats the account as shared state:

  * the kill switch is honoured before every dispatch -- the CODEX_DISABLED
    environment variable AND the flag file, because a flag file kills a running
    estate without a restart;
  * usage is appended to the SAME ledger the other tiers write, tagged
    `goal-epoch`, so one account has one audit trail rather than two;
  * a rate limit writes a SHARED cooldown file, so the next dispatch here waits
    instead of hammering the account;
  * a cross-process lock file makes two local epochs mutually exclusive.

HONEST LIMIT, MEASURED RATHER THAN CLAIMED AWAY: Hermes and Studio run on the
VPS. A lock file on this host cannot exclude a process on another one, so this
provider bounds CONCURRENCY LOCALLY and cannot prevent the VPS spending the
same quota at the same time. Closing that needs a shared authority both hosts
ask, which v1 does not have. Named here rather than implied.

WHAT IT DOES NOT DO: produce a verdict. Codex writing code is work; whether the
work is correct is what a gate epoch answers. A receipt here carries the diff
and the commits, never proof.

`workspace-write` is a wider trust class than the chat tier's read-only
sandbox, and it is confined to the isolated worktree the spec names.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ..epoch import COMPLETED, FAILED, OBS_ENDED, OBS_LOST, OBS_RUNNING, EpochError, \
    Observation, Receipt
from ..git_state import commits_between, head, tree_id

# The other tiers' own names, reused so one account keeps one switch and one
# ledger. Re-spelling them here would create the second control surface this
# provider exists to avoid.
DISABLED_ENV = "CODEX_DISABLED"
DISABLE_FLAG_ENV = "CODEX_DISABLE_FLAG"
DEFAULT_DISABLE_FLAG = "~/.hermes/codex.disabled"
AUDIT_LOG_ENV = "CODEX_AUDIT_LOG"
DEFAULT_AUDIT_LOG = "~/.hermes/codex_usage.jsonl"
COOLDOWN_ENV = "CODEX_COOLDOWN_FILE"
DEFAULT_COOLDOWN = "~/.hermes/codex_cooldown.json"
BIN_ENV = "CODEX_BIN"
HOME_ENV = "CODEX_HOME"

RATE_LIMIT_MARKERS = ("rate limit", "429", "too many requests", "quota", "usage limit")
DEFAULT_COOLDOWN_S = 300.0

ENDPOINT = "goal-epoch"
DEFAULT_MAX_PER_DAY = 10          # Owner decision 2026-09-22 (Q2)
DEFAULT_WALL_BOUND_S = 1200.0     # 20 minutes (Q2)
LOCK_NAME = "gsdx-goal-epoch.lock"


def _truthy(v) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "yes", "on")


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p))


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


class CodexProvider:
    name = "codex"

    def __init__(self, run_dir: Path, wall_bound_s: float = DEFAULT_WALL_BOUND_S,
                 max_per_day: int = DEFAULT_MAX_PER_DAY, argv_prefix: list | None = None,
                 codex_home: Path | None = None):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.wall_bound_s = float(wall_bound_s)
        self.max_per_day = int(max_per_day)
        self.argv_prefix = list(argv_prefix or [os.environ.get(BIN_ENV) or "codex"])
        # Pinned, never inherited: a provider started from Task Scheduler
        # inherits no CODEX_HOME, resolves ~/.codex, and would not find the
        # account the Owner authorised.
        self.codex_home = Path(codex_home) if codex_home else _expand(
            os.environ.get(HOME_ENV) or "~/.codex")
        self._procs: dict[int, subprocess.Popen] = {}

    # --- shared-account controls ------------------------------------------------
    def _flag_path(self) -> Path:
        return _expand(os.environ.get(DISABLE_FLAG_ENV) or DEFAULT_DISABLE_FLAG)

    def _audit_path(self) -> Path:
        return _expand(os.environ.get(AUDIT_LOG_ENV) or DEFAULT_AUDIT_LOG)

    def _cooldown_path(self) -> Path:
        return _expand(os.environ.get(COOLDOWN_ENV) or DEFAULT_COOLDOWN)

    def disabled_reason(self) -> str:
        if _truthy(os.environ.get(DISABLED_ENV)):
            return f"{DISABLED_ENV} is set"
        flag = self._flag_path()
        if flag.is_file():
            return f"the kill switch file {flag} exists"
        return ""

    def cooling_until(self) -> float:
        p = self._cooldown_path()
        if not p.is_file():
            return 0.0
        try:
            return float(json.loads(p.read_text(encoding="utf-8")).get("until", 0))
        except (OSError, ValueError, json.JSONDecodeError):
            return 0.0

    def trip_cooldown(self, seconds: float = DEFAULT_COOLDOWN_S) -> None:
        p = self._cooldown_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"until": time.time() + seconds, "by": ENDPOINT}),
                     encoding="utf-8")

    def audit(self, outcome: str, detail: str, epoch_id: str = "") -> None:
        """One account, one ledger. Appended, never rotated by us."""
        p = self._audit_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                                     "endpoint": ENDPOINT, "outcome": outcome,
                                     "epoch_id": epoch_id, "detail": detail[:300]}) + "\n")
        except OSError as exc:            # never break the epoch over its own audit
            print(f"codex-provider: audit not written ({exc})")

    def used_today(self) -> int:
        p = self._audit_path()
        if not p.is_file():
            return 0
        today = datetime.now(timezone.utc).date().isoformat()
        n = 0
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("endpoint") == ENDPOINT and str(row.get("ts", "")).startswith(today) \
                    and row.get("outcome") == "dispatched":
                n += 1
        return n

    # --- cross-process lock -------------------------------------------------------
    def _lock_path(self) -> Path:
        return self.codex_home / LOCK_NAME

    def acquire_lock(self, epoch_id: str) -> None:
        lock = self._lock_path()
        lock.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"pid": os.getpid(), "epoch_id": epoch_id, "at": time.time()})
        try:
            with open(lock, "x", encoding="utf-8") as fh:
                fh.write(payload)
            return
        except FileExistsError:
            pass
        # Someone holds it. A holder whose process is gone, or which has outlived
        # the wall bound, is stale: keeping the account locked forever because a
        # worker died is worse than the race the lock prevents.
        try:
            held = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            held = {}
        pid, at = int(held.get("pid") or 0), float(held.get("at") or 0)
        stale = (not _pid_alive(pid)) or (time.time() - at > self.wall_bound_s * 2)
        if not stale:
            raise EpochError(f"another local codex epoch holds the account "
                             f"(pid {pid}, epoch {held.get('epoch_id')})")
        lock.write_text(payload, encoding="utf-8")

    def release_lock(self, epoch_id: str) -> None:
        """Release only OUR lock. Deleting a lock we do not hold would free the
        account while another epoch is still spending it."""
        lock = self._lock_path()
        if not lock.is_file():
            return
        try:
            held = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if held.get("epoch_id") == epoch_id:
            try:
                lock.unlink()
            except OSError as exc:
                print(f"codex-provider: lock not released ({exc})")

    # --- provider contract ----------------------------------------------------------
    def _marker(self, token: str) -> Path:
        return self.run_dir / f"codex-{token}.json"

    def dispatch(self, spec: dict) -> dict:
        prompt = (spec.get("prompt") or "").strip()
        if not prompt:
            raise EpochError("a codex epoch needs a prompt")
        worktree = Path(spec["root"])
        if not worktree.is_dir():
            raise EpochError(f"codex epoch worktree does not exist: {worktree}")
        why = self.disabled_reason()
        if why:
            raise EpochError(f"codex is disabled: {why}")
        cooling = self.cooling_until()
        if cooling > time.time():
            raise EpochError(f"the codex account is rate-limited for another "
                             f"{int(cooling - time.time())}s (shared cooldown)")
        used = self.used_today()
        if used >= self.max_per_day:
            raise EpochError(f"the codex goal-epoch budget is spent: {used}/{self.max_per_day} "
                             "today")
        token = spec["identity"]["run_token"]
        self.acquire_lock(spec["epoch_id"])
        log = self.run_dir / f"codex-{token}.log"
        marker = self._marker(token)
        marker.write_text(json.dumps({"token": token, "epoch_id": spec["epoch_id"],
                                      "log": str(log), "pid": None,
                                      "root": str(worktree)}), encoding="utf-8")
        argv = [*self.argv_prefix, "exec", "--skip-git-repo-check",
                "--sandbox", "workspace-write", prompt]
        env = {**os.environ, HOME_ENV: str(self.codex_home), "PYTHONIOENCODING": "utf-8"}
        with open(log, "wb") as out:
            proc = subprocess.Popen(argv, cwd=str(worktree), stdout=out,
                                    stderr=subprocess.STDOUT, env=env)
        marker.write_text(json.dumps({**json.loads(marker.read_text(encoding="utf-8")),
                                      "pid": proc.pid}), encoding="utf-8")
        self._procs[proc.pid] = proc
        self.audit("dispatched", f"pid {proc.pid} in {worktree}", spec["epoch_id"])
        return {"pid": proc.pid, "token": token, "log": str(log), "marker": str(marker),
                "epoch_id": spec["epoch_id"], "root": str(worktree),
                "started_at": time.time(), "head_before": head(worktree),
                "tree_before": tree_id(worktree, spec.get("scope_paths"))}

    def observe(self, handle: dict) -> Observation:
        proc = self._procs.get(handle.get("pid"))
        if proc is None:
            return Observation(OBS_LOST, "", "no child handle in this process")
        rc = proc.poll()
        if rc is None:
            if time.time() - handle.get("started_at", 0) > self.wall_bound_s:
                return Observation(OBS_RUNNING, "", "over its wall bound; cancel it")
            return Observation(OBS_RUNNING)
        return Observation(OBS_ENDED, COMPLETED if rc == 0 else FAILED, f"exit {rc}")

    def _log_text(self, handle: dict) -> str:
        log = Path(handle.get("log", ""))
        return log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""

    def harvest(self, handle: dict, spec: dict) -> Receipt:
        root = Path(handle["root"])
        proc = self._procs.get(handle.get("pid"))
        rc = proc.poll() if proc is not None else None
        text = self._log_text(handle)
        low = text.lower()
        failures = []
        if any(m in low for m in RATE_LIMIT_MARKERS):
            # Shared state: the next dispatch on this host waits rather than
            # spending the Owner's account into a harder limit.
            self.trip_cooldown()
            failures.append({"summary": "codex reported a rate limit; shared cooldown set",
                             "signature": "codex-rate-limited"})
        if rc is None:
            failures.append({"summary": "codex produced no exit status "
                                        "(cancelled, or not ours to read)",
                             "signature": "codex-no-exit"})
        elif rc != 0:
            failures.append({"summary": f"codex exited {rc}: {text.strip()[-200:]}",
                             "signature": f"codex-exit:{rc}"})
        after = head(root)
        before = handle.get("head_before", "")
        commits = commits_between(root, before, after)
        self.audit("harvested", f"rc={rc} commits={len(commits)}", spec.get("epoch_id", ""))
        self.release_lock(handle.get("epoch_id", ""))
        # NO verdicts: Codex writing code is work, and a gate epoch is what says
        # whether the work is right.
        return Receipt(spec["epoch_id"], self.name, spec["revision"],
                       head_before=before, head_after=after,
                       tree_before=handle.get("tree_before", ""),
                       tree_after=tree_id(root, spec.get("scope_paths")),
                       commits=commits, failures=failures,
                       cost={"seconds": round(time.time() - handle.get("started_at", 0), 1),
                             "endpoint": ENDPOINT},
                       narrative=text.strip()[-2000:])

    def cancel(self, handle: dict) -> None:
        pid = handle.get("pid")
        marker = Path(handle["marker"]) if handle.get("marker") else None
        if marker is not None and marker.is_file():
            try:
                data = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            marker.write_text(json.dumps({**data, "cancelled": True}), encoding="utf-8")
        if pid:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               capture_output=True, timeout=60)
            else:
                proc = self._procs.get(pid)
                if proc is not None:
                    proc.kill()
        self.audit("cancelled", f"pid {pid}", handle.get("epoch_id", ""))
        self.release_lock(handle.get("epoch_id", ""))

    def probe(self, identity: dict) -> dict | None:
        marker = self._marker(identity.get("run_token", ""))
        if not marker.is_file():
            return None
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if data.get("pid") is None:
            return None
        return {"pid": data["pid"], "token": data["token"], "log": data["log"],
                "marker": str(marker), "epoch_id": data.get("epoch_id", ""),
                "root": data.get("root", ""), "started_at": 0,
                "head_before": "", "tree_before": ""}
