#!/usr/bin/env python3
"""
oracle_heartbeat.py — Runtime Handshake Probe (MC-OVO-90).

Captures a live snapshot of the system OVO is auditing and writes a
signed JSONL record to ``vault/audits/heartbeats.jsonl``. OVO's Phase D
verdict flow consumes the most recent record and caps the verdict at B
unless a heartbeat younger than ``--max-age`` seconds is attached.

This tool does NOT stub — every path is real:
  - Default mode probes local CPU, memory, load, uptime via psutil.
  - ``--pid`` / ``--process-name`` narrows to a specific target
    (e.g. Paper's ``java.exe`` or a Node worker).
  - ``--log-tail <path> --log-pattern <regex>`` scrapes numeric metrics
    from a running log file (Paper prints ``Running ... TPS`` via
    ``/mspt`` plugins; Spark exposes MSPT to stdout).
  - ``--check`` reads the latest record and validates its age, exit
    non-zero if stale. Use this in OVO's verdict flow.

Signing: SHA256(host + timestamp + canonical_metrics_json). Not
cryptographic — it's a tamper-evident integrity seal so a stale file
can't be edited to fake freshness.

Usage:
  python tools/oracle_heartbeat.py                       # local probe
  python tools/oracle_heartbeat.py --pid 1234            # PID-targeted
  python tools/oracle_heartbeat.py --process-name java.exe
  python tools/oracle_heartbeat.py --log-tail server.log \\
        --log-pattern "TPS:\\s*(\\d+\\.\\d+)" --metric-name tps
  python tools/oracle_heartbeat.py --check --max-age 60  # gate check

Exit codes: 0 ok, 1 heartbeat missing/stale (``--check`` only),
            2 argv error, 3 io error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import psutil
except ImportError:
    print(
        "oracle_heartbeat: psutil is required. "
        "Install with: pip install psutil",
        file=sys.stderr,
    )
    sys.exit(3)


DEFAULT_OUT = "vault/audits/heartbeats.jsonl"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OVO Runtime Handshake Probe")
    p.add_argument("--project", default=".", help="project root (where vault/audits lives)")
    p.add_argument("--out", default=DEFAULT_OUT, help="output JSONL path, relative to --project")
    p.add_argument("--pid", type=int, help="narrow metrics to a specific PID")
    p.add_argument("--process-name", help="narrow metrics to first process matching this exe name (case-insensitive substring match)")
    p.add_argument("--log-tail", help="path to a log file to scrape for numeric metrics")
    p.add_argument("--log-pattern", help="regex with exactly one capture group extracting a numeric value from the log tail")
    p.add_argument("--log-tail-lines", type=int, default=500, help="how many trailing lines of --log-tail to read (default 500)")
    p.add_argument("--metric-name", default="log_value", help="name under which --log-pattern's capture is stored")
    p.add_argument("--label", help="human-readable label for this probe (e.g. 'kobicraft-prod')")
    p.add_argument("--pretty", action="store_true", help="pretty-print the JSON to stdout")
    p.add_argument("--check", action="store_true", help="read the most recent heartbeat and validate its age; non-zero exit on stale/missing")
    p.add_argument("--max-age", type=int, default=60, help="seconds tolerance for --check mode (default 60)")
    return p.parse_args()


def find_process(pid: int | None, name: str | None) -> psutil.Process | None:
    if pid is not None:
        try:
            return psutil.Process(pid)
        except psutil.NoSuchProcess:
            return None
    if name:
        needle = name.lower()
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                exe = (proc.info.get("name") or "").lower()
                if needle in exe:
                    return proc
                exe_path = (proc.info.get("exe") or "").lower()
                if needle in exe_path:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    return None


def system_metrics() -> dict:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    load = None
    if hasattr(os, "getloadavg"):
        try:
            load = list(os.getloadavg())
        except OSError:
            load = None
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cpu_percent_1s": psutil.cpu_percent(interval=1.0),
        "cpu_count": psutil.cpu_count(logical=True),
        "mem_total_mb": round(vm.total / (1024 * 1024), 1),
        "mem_available_mb": round(vm.available / (1024 * 1024), 1),
        "mem_percent": vm.percent,
        "swap_percent": swap.percent,
        "load_avg_1_5_15": load,
        "boot_time": datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }


def process_metrics(proc: psutil.Process) -> dict:
    # proc.cpu_percent() requires a prior call with interval; warm up then sample.
    try:
        proc.cpu_percent(interval=None)
        time.sleep(0.5)
        cpu = proc.cpu_percent(interval=None)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        cpu = None
    try:
        mem = proc.memory_info()
        rss_mb = round(mem.rss / (1024 * 1024), 1)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        rss_mb = None
    try:
        threads = proc.num_threads()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        threads = None
    try:
        status = proc.status()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        status = "unknown"
    try:
        create_ts = proc.create_time()
        uptime_s = int(time.time() - create_ts)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        uptime_s = None
    try:
        name = proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        name = "<unknown>"
    return {
        "pid": proc.pid,
        "name": name,
        "status": status,
        "cpu_percent": cpu,
        "rss_mb": rss_mb,
        "num_threads": threads,
        "uptime_seconds": uptime_s,
    }


def scrape_log(path: Path, pattern: str, tail_lines: int) -> list[float]:
    if not path.exists():
        raise FileNotFoundError(f"log-tail path not found: {path}")
    compiled = re.compile(pattern)
    # Read last ~tail_lines lines efficiently.
    with path.open("rb") as fh:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        # Rough heuristic: 200 bytes per line average.
        block = max(8192, tail_lines * 200)
        fh.seek(max(0, size - block))
        data = fh.read().decode("utf-8", errors="replace")
    lines = data.splitlines()[-tail_lines:]
    values: list[float] = []
    for line in lines:
        m = compiled.search(line)
        if m and m.groups():
            try:
                values.append(float(m.group(1)))
            except ValueError:
                continue
    return values


def canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sign(record: dict) -> str:
    payload = canonical_json(record)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_record(args: argparse.Namespace) -> dict:
    record: dict = {
        "schema": "ovo-heartbeat-v1",
        "timestamp": iso_now(),
        "label": args.label,
        "system": system_metrics(),
    }
    if args.pid is not None or args.process_name:
        proc = find_process(args.pid, args.process_name)
        if proc is None:
            record["process"] = {"error": "process-not-found"}
        else:
            record["process"] = process_metrics(proc)
    if args.log_tail:
        if not args.log_pattern:
            record["log_scrape"] = {"error": "--log-pattern required with --log-tail"}
        else:
            try:
                values = scrape_log(Path(args.log_tail), args.log_pattern, args.log_tail_lines)
            except FileNotFoundError as e:
                record["log_scrape"] = {"error": str(e)}
                values = []
            if values:
                record["log_scrape"] = {
                    "metric": args.metric_name,
                    "sample_count": len(values),
                    "min": round(min(values), 3),
                    "max": round(max(values), 3),
                    "mean": round(sum(values) / len(values), 3),
                    "last": values[-1],
                }
            elif "log_scrape" not in record:
                record["log_scrape"] = {"error": "no-matches"}
    return record


def do_probe(args: argparse.Namespace, out_path: Path) -> int:
    record = build_record(args)
    record["sha256"] = sign(record)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(canonical_json(record) + "\n")
    if args.pretty:
        json.dump(record, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(canonical_json(record) + "\n")
    return 0


def do_check(out_path: Path, max_age: int) -> int:
    if not out_path.exists():
        print(f"[/heartbeat --check] no heartbeat file at {out_path}", file=sys.stderr)
        return 1
    last = None
    with out_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                last = line
    if last is None:
        print(f"[/heartbeat --check] {out_path} empty", file=sys.stderr)
        return 1
    try:
        rec = json.loads(last)
    except json.JSONDecodeError as e:
        print(f"[/heartbeat --check] corrupt last record: {e}", file=sys.stderr)
        return 1
    stored_sha = rec.pop("sha256", None)
    actual_sha = sign(rec)
    if stored_sha != actual_sha:
        print("[/heartbeat --check] integrity seal mismatch — record tampered", file=sys.stderr)
        return 1
    ts_raw = rec.get("timestamp")
    if not ts_raw:
        print("[/heartbeat --check] record has no timestamp", file=sys.stderr)
        return 1
    try:
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    except ValueError:
        print(f"[/heartbeat --check] unparseable timestamp: {ts_raw}", file=sys.stderr)
        return 1
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    print(
        f"[/heartbeat --check] last={ts_raw} age={int(age)}s max={max_age}s "
        f"label={rec.get('label')}"
    )
    if age > max_age:
        print(
            f"[/heartbeat --check] STALE — age {int(age)}s exceeds {max_age}s",
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    out_path = (project / args.out).resolve()
    if args.check:
        return do_check(out_path, args.max_age)
    return do_probe(args, out_path)


if __name__ == "__main__":
    sys.exit(main())
