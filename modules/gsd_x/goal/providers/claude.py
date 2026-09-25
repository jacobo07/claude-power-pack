#!/usr/bin/env python3
"""Two Claude providers: one the Factory starts, one a human drives.

HEADLESS (`claude -p`) is a NEW session in an isolated worktree, authorised by
the Owner on 2026-09-22 at 4 per day with no production writes. It is a new
session on purpose: resuming an existing one would put two writers on one
transcript, which is why /cpp-gsd-long refuses headless resume. A fresh session
has no such conflict -- it reads the brief and nothing else.

INTERACTIVE is the honest name for "a human in a pane does this". It starts
nothing. It writes the brief where the operator will find it and then waits for
a RECEIPT FILE; until that exists the epoch is running, and past its TTL it ends
`expired` -- a named ending distinct from `lost`, because nobody died, the
window simply closed. Without a TTL an interactive epoch whose human never
returns would block closure forever.

Neither produces a verdict. What an agent says it achieved is an account of
itself; a gate epoch is what proves the work.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ..epoch import (COMPLETED, EXPIRED, FAILED, OBS_ENDED, OBS_LOST, OBS_RUNNING,
                     EpochError, Observation, Receipt, echo)
from ..git_state import commits_between, head, tree_id

BIN_ENV = "CLAUDE_BIN"
ARGS_ENV = "CLAUDE_ARGS_TEMPLATE"        # space-separated; {prompt} substituted
LEDGER_ENV = "GSDX_CLAUDE_EPOCH_LEDGER"
DEFAULT_LEDGER = "~/.claude/state/gsd-x/claude_epochs.jsonl"
DISABLE_FLAG_ENV = "GSDX_CLAUDE_DISABLE_FLAG"
DEFAULT_DISABLE_FLAG = "~/.claude/state/gsd-x/claude_epochs.disabled"

DEFAULT_MAX_PER_DAY = 4                  # Owner decision 2026-09-22 (Q1)
DEFAULT_WALL_BOUND_S = 3600.0
DEFAULT_INTERACTIVE_TTL_S = 8 * 3600.0


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p))


def _truthy(v) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "yes", "on")


class HeadlessClaudeProvider:
    """A fresh `claude -p` session in a worktree the goal owns."""

    name = "claude-headless"

    def __init__(self, run_dir: Path, wall_bound_s: float = DEFAULT_WALL_BOUND_S,
                 max_per_day: int = DEFAULT_MAX_PER_DAY, argv_prefix: list | None = None):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.wall_bound_s = float(wall_bound_s)
        self.max_per_day = int(max_per_day)
        self.argv_prefix = list(argv_prefix or [os.environ.get(BIN_ENV) or "claude"])
        self._procs: dict[int, subprocess.Popen] = {}

    def _ledger(self) -> Path:
        return _expand(os.environ.get(LEDGER_ENV) or DEFAULT_LEDGER)

    def _flag(self) -> Path:
        return _expand(os.environ.get(DISABLE_FLAG_ENV) or DEFAULT_DISABLE_FLAG)

    def _marker(self, token: str) -> Path:
        return self.run_dir / f"claude-{token}.json"

    def audit(self, outcome: str, detail: str, epoch_id: str) -> None:
        p = self._ledger()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                                     "outcome": outcome, "epoch_id": epoch_id,
                                     "detail": detail[:300]}) + "\n")
        except OSError as exc:
            print(f"claude-provider: audit not written ({exc})")

    def used_today(self) -> int:
        p = self._ledger()
        if not p.is_file():
            return 0
        today = datetime.now(timezone.utc).date().isoformat()
        n = 0
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("outcome") == "dispatched" and str(row.get("ts", "")).startswith(today):
                n += 1
        return n

    def dispatch(self, spec: dict) -> dict:
        brief = (spec.get("brief") or "").strip()
        if not brief:
            raise EpochError("a headless claude epoch needs a brief")
        root = Path(spec["root"])
        if not root.is_dir():
            raise EpochError(f"headless claude epoch worktree does not exist: {root}")
        # The isolation is the safety property, so it is checked rather than
        # assumed: an epoch pointed at a live checkout is refused.
        if spec.get("must_be_worktree", True) and not (root / ".git").exists():
            raise EpochError(f"{root} is not a git worktree; a headless epoch runs in an "
                             "isolated worktree the goal owns")
        if self._flag().is_file():
            raise EpochError(f"headless claude epochs are disabled: {self._flag()} exists")
        used = self.used_today()
        if used >= self.max_per_day:
            raise EpochError(f"the headless claude budget is spent: {used}/{self.max_per_day} "
                             "today (Owner cap)")
        token = spec["identity"]["run_token"]
        log = self.run_dir / f"claude-{token}.log"
        marker = self._marker(token)
        marker.write_text(json.dumps({"token": token, "epoch_id": spec["epoch_id"],
                                      "log": str(log), "pid": None, "root": str(root)}),
                          encoding="utf-8")
        tmpl = (os.environ.get(ARGS_ENV) or "-p {prompt}").split()
        argv = [*self.argv_prefix, *[brief if a == "{prompt}" else a for a in tmpl]]
        with open(log, "wb") as out:
            proc = subprocess.Popen(argv, cwd=str(root), stdout=out,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                    env={**os.environ, "PYTHONIOENCODING": "utf-8",
                                         "GSDX_GOAL_EPOCH": spec["epoch_id"]})
        marker.write_text(json.dumps({**json.loads(marker.read_text(encoding="utf-8")),
                                      "pid": proc.pid}), encoding="utf-8")
        self._procs[proc.pid] = proc
        self.audit("dispatched", f"pid {proc.pid} in {root}", spec["epoch_id"])
        return {"pid": proc.pid, "token": token, "log": str(log), "marker": str(marker),
                "epoch_id": spec["epoch_id"], "root": str(root), "started_at": time.time(),
                "head_before": head(root), "tree_before": tree_id(root, spec.get("scope_paths"))}

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

    def harvest(self, handle: dict, spec: dict) -> Receipt:
        root = Path(handle["root"])
        proc = self._procs.get(handle.get("pid"))
        rc = proc.poll() if proc is not None else None
        log = Path(handle.get("log", ""))
        text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        failures = []
        if rc is None:
            failures.append({"summary": "the headless session produced no exit status",
                             "signature": "claude-no-exit"})
        elif rc != 0:
            failures.append({"summary": f"the headless session exited {rc}: {text.strip()[-200:]}",
                             "signature": f"claude-exit:{rc}"})
        before, after = handle.get("head_before", ""), head(root)
        commits = commits_between(root, before, after)
        self.audit("harvested", f"rc={rc} commits={len(commits)}", spec.get("epoch_id", ""))
        return Receipt(spec["epoch_id"], self.name, spec["revision"], **echo(spec),
                       head_before=before,
                       head_after=after, tree_before=handle.get("tree_before", ""),
                       tree_after=tree_id(root, spec.get("scope_paths")), commits=commits,
                       failures=failures,
                       cost={"seconds": round(time.time() - handle.get("started_at", 0), 1)},
                       narrative=text.strip()[-2000:])

    def cancel(self, handle: dict) -> None:
        pid = handle.get("pid")
        if pid:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               capture_output=True, timeout=60)
            else:
                proc = self._procs.get(pid)
                if proc is not None:
                    proc.kill()
        self.audit("cancelled", f"pid {pid}", handle.get("epoch_id", ""))

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


class InteractiveClaudeProvider:
    """Hands a brief to a human pane and waits for a receipt file."""

    name = "claude-interactive"

    def __init__(self, run_dir: Path, wall_bound_s: float = DEFAULT_INTERACTIVE_TTL_S):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.wall_bound_s = float(wall_bound_s)

    def _paths(self, token: str) -> tuple[Path, Path]:
        return (self.run_dir / f"brief-{token}.md", self.run_dir / f"receipt-{token}.json")

    def _meta(self, token: str) -> Path:
        """Where the epoch's own facts live, so a handle recovered after a crash
        harvests against the real worktree instead of whatever the process's
        current directory happens to be."""
        return self.run_dir / f"meta-{token}.json"

    def dispatch(self, spec: dict) -> dict:
        brief = (spec.get("brief") or "").strip()
        if not brief:
            raise EpochError("an interactive epoch needs a brief for the operator")
        token = spec["identity"]["run_token"]
        brief_path, receipt_path = self._paths(token)
        brief_path.write_text(brief, encoding="utf-8")
        root = Path(spec["root"])
        self._meta(token).write_text(
            json.dumps({"root": str(root), "epoch_id": spec["epoch_id"],
                        "started_at": time.time(), "head_before": head(root)}),
            encoding="utf-8")
        return {"token": token, "brief": str(brief_path), "receipt": str(receipt_path),
                "epoch_id": spec["epoch_id"], "root": str(root), "started_at": time.time(),
                "head_before": head(root), "tree_before": tree_id(root, spec.get("scope_paths"))}

    def observe(self, handle: dict) -> Observation:
        receipt = Path(handle["receipt"])
        if receipt.is_file():
            return Observation(OBS_ENDED, COMPLETED, "the operator returned a receipt")
        if time.time() - handle.get("started_at", 0) > self.wall_bound_s:
            # EXPIRED, not LOST: nobody died, the window closed. An interactive
            # epoch with no TTL would block closure forever on a human who never
            # came back.
            return Observation(OBS_ENDED, EXPIRED, "no receipt before the TTL")
        return Observation(OBS_RUNNING, "", f"waiting for {receipt.name}")

    def harvest(self, handle: dict, spec: dict) -> Receipt:
        root = Path(handle["root"])
        receipt = Path(handle["receipt"])
        data, failures = {}, []
        if receipt.is_file():
            try:
                data = json.loads(receipt.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                failures.append({"summary": f"the operator's receipt is unreadable: {exc}",
                                 "signature": "interactive-receipt-unreadable"})
        else:
            failures.append({"summary": "the epoch expired with no operator receipt",
                             "signature": "interactive-expired"})
        before, after = handle.get("head_before", ""), head(root)
        commits = commits_between(root, before, after)
        return Receipt(spec["epoch_id"], self.name, spec["revision"], **echo(spec),
                       head_before=before,
                       head_after=after, tree_before=handle.get("tree_before", ""),
                       tree_after=tree_id(root, spec.get("scope_paths")), commits=commits,
                       failures=failures, cost={"seconds": round(
                           time.time() - handle.get("started_at", 0), 1)},
                       narrative=str(data.get("narrative", ""))[:2000])

    def cancel(self, handle: dict) -> None:
        """Withdraw the brief. There is no process to kill: the operator simply
        finds the request gone, which is the honest effect of cancelling work
        that a human owns."""
        brief = Path(handle.get("brief", ""))
        if brief.is_file():
            try:
                brief.unlink()
            except OSError as exc:
                print(f"claude-interactive: brief not withdrawn ({exc})")

    def probe(self, identity: dict) -> dict | None:
        token = identity.get("run_token", "")
        brief_path, receipt_path = self._paths(token)
        meta_path = self._meta(token)
        if not meta_path.is_file():
            return None                 # the brief was never handed over
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return {"token": token, "brief": str(brief_path), "receipt": str(receipt_path),
                "epoch_id": meta.get("epoch_id", ""), "root": meta.get("root", ""),
                "started_at": meta.get("started_at", 0),
                "head_before": meta.get("head_before", ""), "tree_before": ""}
