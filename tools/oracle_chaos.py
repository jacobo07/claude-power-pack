#!/usr/bin/env python3
"""
oracle_chaos.py — Fault-Injection Validation harness (MC-OVO-92).

Spawns a target command under controlled chaos (CPU spin, memory
pressure, disk pressure, timeout budget) and verifies it either
completes within SLA or recovers from the perturbation. Emits a
structured verdict that OVO Phase D can consume before stamping A+ on
any infrastructure-tagged delta.

Scope limits (no stubs, just honest bounds):
  - Local-process chaos only. Does not cross OS boundaries, does not
    kill Docker containers, does not break Kubernetes pods. That's
    explicitly out of scope for MVP.
  - CPU stress is a Python-native busy loop on N worker threads.
  - Memory pressure allocates a bytearray of configurable MB for the
    duration of the run.
  - Disk pressure writes a file of configurable MB to the OS temp dir
    and removes it on exit.
  - "SLA recovery" means the target process exits with code 0 within
    ``--deadline`` seconds AND within ``--deadline * 1.5`` including
    tail cleanup.

Usage (one chaos mode per run):
  python tools/oracle_chaos.py --cmd "python -c 'import time; time.sleep(3); print(\"ok\")'" --cpu 4 --deadline 10
  python tools/oracle_chaos.py --cmd "mvn -q verify" --mem-mb 512 --deadline 180
  python tools/oracle_chaos.py --cmd "npm test" --disk-mb 250 --deadline 120
  python tools/oracle_chaos.py --cmd "./run.sh" --cpu 2 --mem-mb 256 --disk-mb 100 --deadline 60

Exit codes: 0 PASS (target survived + within SLA),
            1 FAIL (target failed or exceeded SLA),
            2 argv error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_OUT = "vault/audits/chaos_runs.jsonl"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OVO Fault-Injection Harness")
    p.add_argument("--project", default=".", help="project root (vault path lives here)")
    p.add_argument("--out", default=DEFAULT_OUT, help="output JSONL path relative to --project")
    p.add_argument("--cmd", required=True, help="target command to run under chaos (quoted)")
    p.add_argument("--deadline", type=int, default=60,
                   help="SLA deadline in seconds. Exit code 0 within deadline = PASS (default 60)")
    p.add_argument("--cpu", type=int, default=0,
                   help="N CPU spinner threads (chaos mode). Default 0 = off.")
    p.add_argument("--mem-mb", type=int, default=0,
                   help="Memory to hold during target run, in MB. Default 0 = off.")
    p.add_argument("--disk-mb", type=int, default=0,
                   help="Disk bytes to write to OS temp dir, in MB. Default 0 = off.")
    p.add_argument("--cwd", default=None, help="working directory for the target command")
    p.add_argument("--env", action="append", default=[],
                   help="extra env var in KEY=VALUE form (repeatable)")
    p.add_argument("--label", help="human-readable run label")
    p.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    p.add_argument("--no-log", action="store_true", help="do not append a record to the JSONL")
    return p.parse_args()


# ────────────────────── chaos drivers ──────────────────────


class CPUStressor:
    def __init__(self, workers: int):
        self.workers = workers
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def _spin(self):
        # Pure Python busy loop — measurable CPU load without sub-deps.
        while not self._stop.is_set():
            x = 0
            for _ in range(100_000):
                x = (x * 1103515245 + 12345) & 0x7FFFFFFF

    def start(self):
        for _ in range(self.workers):
            t = threading.Thread(target=self._spin, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        self._stop.set()
        for t in self._threads:
            t.join(timeout=1.0)


class MemoryHolder:
    def __init__(self, mb: int):
        self.mb = mb
        self._buf: bytearray | None = None

    def start(self):
        # One contiguous allocation; touched page-by-page so the OS actually
        # commits it.
        size = self.mb * 1024 * 1024
        self._buf = bytearray(size)
        for i in range(0, size, 4096):
            self._buf[i] = 1

    def stop(self):
        self._buf = None


class DiskFiller:
    def __init__(self, mb: int):
        self.mb = mb
        self._path: Path | None = None

    def start(self):
        fd, raw = tempfile.mkstemp(prefix="ovo-chaos-", suffix=".bin")
        os.close(fd)
        self._path = Path(raw)
        chunk = b"\0" * (1024 * 1024)
        with self._path.open("wb") as fh:
            for _ in range(self.mb):
                fh.write(chunk)

    def stop(self):
        if self._path and self._path.exists():
            try:
                self._path.unlink()
            except OSError:
                pass
        self._path = None


def build_env(pairs: list[str]) -> dict:
    env = dict(os.environ)
    for p in pairs:
        if "=" not in p:
            print(f"oracle_chaos: bad --env entry (expected KEY=VALUE): {p}", file=sys.stderr)
            sys.exit(2)
        k, v = p.split("=", 1)
        env[k] = v
    return env


def run_target(cmd: str, deadline: int, cwd: str | None, env: dict) -> dict:
    start_ts = time.monotonic()
    timed_out = False
    try:
        # shell=True is deliberate — target cmds are expected to be shell-quoted
        # by the caller. The tool is invoked under explicit Owner control.
        proc = subprocess.Popen(
            cmd if sys.platform == "win32" else shlex.split(cmd),
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=(sys.platform == "win32"),
        )
    except OSError as e:
        return {
            "launched": False,
            "error": str(e),
            "elapsed_seconds": 0.0,
        }
    try:
        stdout, stderr = proc.communicate(timeout=deadline * 1.5)
        elapsed = time.monotonic() - start_ts
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            stdout, stderr = b"", b""
        elapsed = time.monotonic() - start_ts
    return {
        "launched": True,
        "timed_out": timed_out,
        "exit_code": proc.returncode if not timed_out else None,
        "elapsed_seconds": round(elapsed, 3),
        "stdout_tail": _tail(stdout),
        "stderr_tail": _tail(stderr),
    }


def _tail(b: bytes, max_chars: int = 1000) -> str:
    try:
        s = b.decode("utf-8", errors="replace")
    except Exception:
        s = str(b)
    return s[-max_chars:]


def classify(run: dict, deadline: int) -> dict:
    if not run.get("launched"):
        return {"verdict": "FAIL", "reason": f"target did not launch: {run.get('error')}"}
    if run.get("timed_out"):
        return {"verdict": "FAIL", "reason": f"target timed out past {int(deadline * 1.5)}s"}
    if run.get("exit_code") != 0:
        return {"verdict": "FAIL", "reason": f"target exit code {run.get('exit_code')}"}
    if run.get("elapsed_seconds", 0) > deadline:
        return {"verdict": "FAIL", "reason": f"target exceeded SLA deadline {deadline}s"}
    return {"verdict": "PASS", "reason": f"target completed in {run['elapsed_seconds']}s within deadline {deadline}s"}


def sign(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    out_path = (project / args.out).resolve()
    env = build_env(args.env)

    chaos_modes: list[str] = []
    cpu = CPUStressor(args.cpu) if args.cpu > 0 else None
    mem = MemoryHolder(args.mem_mb) if args.mem_mb > 0 else None
    disk = DiskFiller(args.disk_mb) if args.disk_mb > 0 else None

    try:
        if cpu:
            cpu.start()
            chaos_modes.append(f"cpu:{args.cpu}")
        if mem:
            mem.start()
            chaos_modes.append(f"mem:{args.mem_mb}MB")
        if disk:
            disk.start()
            chaos_modes.append(f"disk:{args.disk_mb}MB")
        run = run_target(args.cmd, args.deadline, args.cwd, env)
    finally:
        if cpu:
            cpu.stop()
        if mem:
            mem.stop()
        if disk:
            disk.stop()

    verdict = classify(run, args.deadline)
    record = {
        "schema": "ovo-chaos-v1",
        "timestamp": iso_now(),
        "label": args.label,
        "cmd": args.cmd,
        "deadline_seconds": args.deadline,
        "chaos_modes": chaos_modes or ["none"],
        "run": run,
        "verdict": verdict,
    }
    record["sha256"] = sign(record)

    if not args.no_log:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    sys.stdout.write(
        json.dumps(record, indent=2 if args.pretty else None) + "\n"
    )
    return 0 if verdict["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
