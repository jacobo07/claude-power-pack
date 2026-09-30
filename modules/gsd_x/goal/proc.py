#!/usr/bin/env python3
"""Is a process id alive? One answer for every provider.

Two defects this replaces, both found 2026-09-30 while making the goal spine portable:

  POSIX    `os.kill(pid, 0)` raising PermissionError means the process EXISTS and belongs
           to another user. It was caught as an OSError and reported dead, so a lock or a
           gate held by another account read as abandoned.
  Windows  `str(pid) in tasklist_output` is a substring test: pid 12 is "alive" whenever
           any process id, memory figure or session number contains "12". The CSV form is
           parsed and the PID column compared exactly.
"""
from __future__ import annotations

import csv
import io
import os
import subprocess


def _tasklist_has(pid: int) -> bool:
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, timeout=60).stdout
    for row in csv.reader(io.StringIO(out)):
        if len(row) >= 2 and row[1].strip() == str(pid):
            return True
    return False


def pid_alive(pid) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            return _tasklist_has(pid)
        except (OSError, subprocess.SubprocessError):
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True          # it exists; we may not signal it
    except OSError:
        return False
    return True
