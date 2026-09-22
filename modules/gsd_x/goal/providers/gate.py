#!/usr/bin/env python3
"""The deterministic provider: run a named done gate and report what it observed.

This is the provider that produces EVIDENCE. It runs one command -- a test file,
a verifier, an in-game check -- and returns a verdict tied to the tree it ran
against, the revision it was asked about, the class of gate it is, and the pin
of the gate's own files.

It does not decide anything. Whether that verdict may satisfy an obligation is
`convergence.evaluate`'s question, and the answer depends on facts this provider
only reports: a unit test cannot prove a REALITY obligation however green.

The gate CLASS is declared by whoever registered the gate, never inferred here.
Guessing "this looks like an in-game check" from a filename is exactly the
inference that would let a local test satisfy a runtime claim.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from ..epoch import (COMPLETED, FAILED, LOST, OBS_ENDED, OBS_LOST, OBS_RUNNING,
                     EpochError, Observation, Receipt)
from ..git_state import file_pin, head, tree_id

GATE_CLASSES = ("unit", "integration", "in_game", "live")
DEFAULT_TIMEOUT_S = 900.0


class GateProvider:
    """Runs one gate per epoch, in its own process, with a bound."""

    name = "gate"

    def __init__(self, run_dir: Path, wall_bound_s: float = DEFAULT_TIMEOUT_S):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.wall_bound_s = float(wall_bound_s)
        # Per INSTANCE. A class-level dict would share child handles between
        # providers and let one epoch read another's exit status.
        self._procs: dict[int, subprocess.Popen] = {}

    # --- helpers -------------------------------------------------------------
    def _marker(self, run_token: str) -> Path:
        """Where this run records itself. Derived from the identity minted
        BEFORE dispatch, so `probe` can find a run whose handle was never
        written because the coordinator died in between."""
        return self.run_dir / f"gate-{run_token}.json"

    @staticmethod
    def _spec_gate(spec: dict) -> dict:
        g = spec.get("gate") or {}
        if not g.get("command"):
            raise EpochError("a gate epoch needs a command to run")
        if g.get("class") not in GATE_CLASSES:
            raise EpochError(f"gate class {g.get('class')!r} must be one of {GATE_CLASSES}")
        if not g.get("files"):
            raise EpochError("a gate epoch must name the gate's own files, so they can be pinned")
        return g

    # --- provider contract ---------------------------------------------------
    def dispatch(self, spec: dict) -> dict:
        g = self._spec_gate(spec)
        root = Path(spec["root"])
        token = spec["identity"]["run_token"]
        log = self.run_dir / f"gate-{token}.log"
        marker = self._marker(token)
        # The marker is written BEFORE the process starts: a probe that finds no
        # marker can say "nothing was started", and one that finds a marker with
        # no pid can say "it started and we lost the handle". Those need
        # different answers and must stay distinguishable.
        marker.write_text(json.dumps({"token": token, "epoch_id": spec["epoch_id"],
                                      "log": str(log), "started_at": time.time(),
                                      "pid": None}), encoding="utf-8")
        with open(log, "wb") as out:        # the child keeps its own duplicate
            proc = subprocess.Popen(g["command"], cwd=str(root), stdout=out,
                                    stderr=subprocess.STDOUT,
                                    env={**os.environ, "PYTHONIOENCODING": "utf-8",
                                         "GSDX_GOAL_EPOCH": spec["epoch_id"]})
        handle = {"pid": proc.pid, "token": token, "log": str(log),
                  "marker": str(marker), "started_at": time.time(),
                  "tree_before": tree_id(root, spec.get("scope_paths")),
                  "head_before": head(root)}
        marker.write_text(json.dumps({**json.loads(marker.read_text(encoding="utf-8")),
                                      "pid": proc.pid}), encoding="utf-8")
        self._procs[proc.pid] = proc
        return handle

    def observe(self, handle: dict) -> Observation:
        proc = self._procs.get(handle.get("pid"))
        if proc is None:
            # Another process owns it (or we restarted). The marker says it was
            # started; without the child handle we cannot read its exit status,
            # and guessing is what turns a finished gate into a false failure.
            return Observation(OBS_LOST, LOST, "no child handle in this process")
        rc = proc.poll()
        if rc is None:
            if time.time() - handle.get("started_at", 0) > self.wall_bound_s:
                return Observation(OBS_RUNNING, "", "over its wall bound; cancel it")
            return Observation(OBS_RUNNING)
        return Observation(OBS_ENDED, COMPLETED if rc == 0 else FAILED, f"exit {rc}")

    def harvest(self, handle: dict, spec: dict) -> Receipt:
        g = self._spec_gate(spec)
        root = Path(spec["root"])
        proc = self._procs.get(handle.get("pid"))
        rc = proc.poll() if proc is not None else None
        # A CANCELLED gate did not judge anything. Its exit status belongs to
        # whoever killed it (measured: taskkill leaves 1), and reporting that as
        # "the gate ran and failed" is a fabricated verdict about work that never
        # finished. Cancellation is recorded by cancel() and read back here.
        if self._was_cancelled(handle):
            rc = None
        log = Path(handle["log"])
        observed = ""
        if log.is_file():
            tail = log.read_text(encoding="utf-8", errors="replace").strip().splitlines()
            observed = tail[-1][:200] if tail else ""
        tree = tree_id(root, spec.get("scope_paths"))
        verdicts = []
        failures = []
        if rc is None:
            # Not finished, cancelled, or not ours to read. A receipt that
            # invented an exit status here would be the fake-done this design
            # refuses -- and "cancelled" needs different words from "still
            # running", because only one of them is going to produce a verdict.
            cancelled = self._was_cancelled(handle)
            failures.append({"summary": f"gate {g['id']} produced no exit status"
                                        + (" (cancelled before it could judge)"
                                           if cancelled else ""),
                             "signature": (f"gate-cancelled:{g['id']}" if cancelled
                                           else f"gate-no-exit:{g['id']}")})
        else:
            verdicts.append({"gate": g["id"], "exit_status": rc, "observed": observed,
                             "tree_hash": tree, "revision": spec["revision"],
                             "gate_class": g["class"],
                             "gate_pin": [list(p) for p in file_pin(root, g["files"])]})
            if rc != 0:
                failures.append({"summary": f"gate {g['id']} exited {rc}: {observed}",
                                 "signature": f"gate-exit:{g['id']}:{rc}"})
        return Receipt(spec["epoch_id"], self.name, spec["revision"],
                       head_before=handle.get("head_before", ""), head_after=head(root),
                       tree_before=handle.get("tree_before", ""), tree_after=tree,
                       verdicts=verdicts, failures=failures,
                       cost={"seconds": round(time.time() - handle.get("started_at", 0), 1)},
                       narrative=observed)

    def _was_cancelled(self, handle: dict) -> bool:
        """Read the cancellation from the marker, not from memory: the process
        that cancels an epoch is often not the one that harvests it."""
        marker = handle.get("marker")
        if not marker or not Path(marker).is_file():
            return False
        try:
            return bool(json.loads(Path(marker).read_text(encoding="utf-8")).get("cancelled"))
        except (OSError, json.JSONDecodeError):
            return False

    def cancel(self, handle: dict) -> None:
        pid = handle.get("pid")
        proc = self._procs.get(pid)
        marker = Path(handle["marker"]) if handle.get("marker") else None
        if marker is not None and marker.is_file():
            try:
                data = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            marker.write_text(json.dumps({**data, "cancelled": True,
                                          "cancelled_at": time.time()}), encoding="utf-8")
        if pid is None:
            return
        # Kill the TREE, not the parent. A gate that spawns a test runner leaves
        # grandchildren writing into the worktree the next epoch will read.
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=60)
        elif proc is not None:
            proc.kill()
        if proc is not None:
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass

    def probe(self, identity: dict) -> dict | None:
        """Find a run started before a crash, by the identity minted before it."""
        marker = self._marker(identity.get("run_token", ""))
        if not marker.is_file():
            return None                      # nothing was ever started
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if data.get("pid") is None:
            return None                      # started to write, never spawned
        return {"pid": data["pid"], "token": data["token"], "log": data["log"],
                "marker": str(marker), "started_at": data.get("started_at", 0),
                "tree_before": "", "head_before": ""}
