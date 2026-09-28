"""Python caller for the vendored Node packages (vendor/genesis-suite, vendor/context-budget).

The only way CPP code reaches an assimilated cold-path capability. One call = one short-lived
``node lib/adapters/genesis-suite.js`` process; nothing is kept warm, so a caller on a hot path
must not use this (hot-path capabilities are native: modules/context_budget, modules/autonomy_gate,
the provider breaker in tools/gsd_mission.py).

Outcomes are distinct on purpose (instrument-before-claim: a verifier that could not judge is
not a verifier that rejected):
    OK               the upstream function returned; ``value`` holds its JSON result
    SUBJECT_INVALID  the upstream function ran and refused the input
    BRIDGE_FAILED    the call could not be made: node missing or outside the vendored engine
                     range, unknown export, timeout, vendored tree absent
    UNREADABLE       node ran but did not answer with the adapter's JSON
A caller may fall back to its pre-assimilation behaviour on BRIDGE_FAILED / UNREADABLE, and
must say so; it may never treat either as OK.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "lib" / "adapters" / "genesis-suite.js"
DEFAULT_TIMEOUT_S = 30.0

OK = "OK"
SUBJECT_INVALID = "SUBJECT_INVALID"
BRIDGE_FAILED = "BRIDGE_FAILED"
UNREADABLE = "UNREADABLE"


@dataclass
class BridgeResult:
    outcome: str
    value: object = None
    error: str = ""
    detail: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.outcome == OK


def node_exe() -> str | None:
    explicit = os.environ.get("CPP_NODE_EXE")
    if explicit:
        return explicit if Path(explicit).is_file() else None
    return shutil.which("node")


def call(module: str, fn: str | None = None, args: list | None = None, *, package: str = "genesis-suite",
         factory: dict | None = None, method: str | None = None,
         timeout: float = DEFAULT_TIMEOUT_S) -> BridgeResult:
    exe = node_exe()
    if exe is None:
        return BridgeResult(BRIDGE_FAILED, error="node executable not found (set CPP_NODE_EXE)")
    if not ADAPTER.is_file():
        return BridgeResult(BRIDGE_FAILED, error=f"adapter missing: {ADAPTER}")
    if not (ROOT / "vendor" / package / "package.json").is_file():
        return BridgeResult(BRIDGE_FAILED, error=f"vendored package absent: {package}")
    req = {"package": package, "module": module, "fn": fn, "args": args or []}
    if factory is not None:
        req["factory"] = factory
        req["method"] = method
    try:
        proc = subprocess.run([exe, str(ADAPTER)], input=json.dumps(req).encode("utf-8"),
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return BridgeResult(BRIDGE_FAILED, error=f"timeout after {timeout}s", detail={"request": req})
    except OSError as exc:
        return BridgeResult(BRIDGE_FAILED, error=f"could not start node: {exc!r}")
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    try:
        reply = json.loads(out)
    except ValueError:
        return BridgeResult(UNREADABLE, error="adapter reply was not JSON",
                            detail={"exit": proc.returncode, "stdout": out[:500],
                                    "stderr": proc.stderr.decode("utf-8", errors="replace")[:500]})
    outcome = reply.get("outcome")
    if outcome not in (OK, SUBJECT_INVALID, BRIDGE_FAILED):
        return BridgeResult(UNREADABLE, error=f"unknown adapter outcome {outcome!r}", detail=reply)
    return BridgeResult(outcome, value=reply.get("value"), error=reply.get("error", ""),
                        detail={k: v for k, v in reply.items() if k not in ("outcome", "value", "error")})
