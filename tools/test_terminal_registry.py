"""V-gates for the live terminal registry (vault/specs/live-terminal-registry.md).

Hermetic by construction: build_pane_map.ps1 takes -StateDir and -ProjBase, and
reads beacons from $env:TEMP, so the whole pipeline runs against a throwaway tree
and never touches ~/.claude/state. Tests go through the REAL entry point -- a unit
test of the transform alone would have passed while production dropped the panes
(T-COLLECTION-GATE-DROPS-LIVE-PANE-001).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD = REPO / "tools" / "build_pane_map.ps1"
GUARD = REPO / "tools" / "lib" / "beacon_identity.ps1"
REGISTRY_JS = REPO / "extension" / "src" / "terminal_registry.js"
NODE = r"C:\Program Files\nodejs\node.exe"

passes = 0
fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"  [OK]   {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global fails
    fails += 1
    print(f"  [FAIL] {gate}: {diag}")


def _sanitize(path: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in path)


def _live_pids() -> set[int]:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process | ForEach-Object { $_.Id }"],
        capture_output=True, text=True, check=False,
    ).stdout
    return {int(x) for x in out.split() if x.strip().isdigit()}


def _dead_pid(live: set[int]) -> int:
    for candidate in range(999999, 990000, -2):
        if candidate not in live:
            return candidate
    raise RuntimeError("no free pid found")


def _write_transcript(proj_base: Path, cwd: str, sid: str, minutes_old: int) -> None:
    """A transcript shaped like the ones build_pane_map.ps1 actually parses."""
    d = proj_base / _sanitize(cwd)
    d.mkdir(parents=True, exist_ok=True)
    ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_old)).isoformat()
    lines = [
        {"type": "user", "cwd": cwd, "timestamp": ts,
         "message": {"role": "user", "content": "terminal registry gate fixture"}},
        {"type": "assistant", "cwd": cwd, "timestamp": ts,
         "message": {"role": "assistant", "content": "ack"}},
    ]
    (d / f"{sid}.jsonl").write_text(
        "\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8"
    )


def _write_registry(state: Path, cwd: str, host_pid: int, names: list[str]) -> None:
    d = state / "terminals"
    d.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "vscode.window.terminals",
        "cwd": cwd,
        "repo": Path(cwd).name,
        "hostPid": host_pid,
        "terminals": [
            {"name": n, "sidPrefix": _sid8(n), "processId": None, "index": i}
            for i, n in enumerate(names)
        ],
    }
    (d / (_sanitize(cwd) + ".json")).write_text(json.dumps(payload), encoding="utf-8")


def _sid8(name: str) -> str:
    import re
    m = re.findall(r"[0-9a-f]{8}", name, re.I)
    return m[-1].lower() if m else ""


def _run_build(state: Path, proj_base: Path, temp: Path) -> dict:
    env = dict(os.environ)
    env["TEMP"] = str(temp)
    env["TMP"] = str(temp)
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(BUILD),
         "-StateDir", str(state), "-ProjBase", str(proj_base)],
        capture_output=True, text=True, check=False, env=env,
    )
    out = state / "pane_map.json"
    if not out.exists():
        return {}
    return json.loads(out.read_text(encoding="utf-8-sig"))


def main() -> int:
    print("=" * 62)
    print("LIVE TERMINAL REGISTRY GATES")
    print("=" * 62)

    # --- pure transform (node selftest) --------------------------------------
    r = subprocess.run([NODE, str(REGISTRY_JS), "--selftest"],
                       capture_output=True, text=True, check=False)
    if r.returncode == 0 and "TERMINAL_REGISTRY_SELFTEST=PASS" in r.stdout:
        _ok("V-TERMREG-WRITTEN", r.stdout.strip().splitlines()[-1])
    else:
        _fail("V-TERMREG-WRITTEN", (r.stdout + r.stderr).strip()[:200])

    # --- pid-identity guard (powershell selftest) ----------------------------
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-File", str(GUARD), "--selftest"],
                       capture_output=True, text=True, check=False)
    guard_ok = r.returncode == 0 and "BEACON_IDENTITY_SELFTEST=PASS" in r.stdout
    if guard_ok and "V-BEACON-PID-IDENTITY-REJECTS-FOREIGN" in r.stdout:
        _ok("V-BEACON-PID-IDENTITY", "foreign process rejected for a live pid")
    else:
        _fail("V-BEACON-PID-IDENTITY", (r.stdout + r.stderr).strip()[:200])
    if guard_ok and "V-BEACON-PID-CTIME-REJECTS-NEWER" in r.stdout:
        _ok("V-BEACON-PID-CTIME", "process newer than its beacon rejected (pid reuse)")
    else:
        _fail("V-BEACON-PID-CTIME", (r.stdout + r.stderr).strip()[:200])

    # --- end-to-end through build_pane_map.ps1 -------------------------------
    root = Path(tempfile.mkdtemp(prefix="pp-termreg-"))
    try:
        state = root / "state"
        proj = root / "projects"
        temp = root / "temp"
        for d in (state, proj, temp):
            d.mkdir(parents=True, exist_ok=True)

        repo_a = root / "RepoAlpha"
        repo_b = root / "RepoBeta"
        repo_c = root / "RepoGamma"
        for d in (repo_a, repo_b, repo_c):
            d.mkdir(parents=True, exist_ok=True)

        sid_a = "aaaaaaa1-1111-4111-8111-111111111111"
        sid_b = "bbbbbbb2-2222-4222-8222-222222222222"
        sid_c = "ccccccc3-3333-4333-8333-333333333333"
        # Idle well past ACTIVE (2h) so ONLY a live signal can hold them OPEN-NOW.
        for cwd, sid in ((repo_a, sid_a), (repo_b, sid_b), (repo_c, sid_c)):
            _write_transcript(proj, str(cwd), sid, minutes_old=600)

        live = _live_pids()
        host_pid = os.getpid()
        dead = _dead_pid(live)

        # A: two terminals, one carrying the session id. Live host.
        _write_registry(state, str(repo_a), host_pid,
                        [f"RepoAlpha - fixture {sid_a[:8]}", "Last session"])
        # B: three terminals but the writing window is DEAD -> must not count.
        _write_registry(state, str(repo_b), dead,
                        [f"RepoBeta - fixture {sid_b[:8]}", "x", "y"])
        # A corrupt registry file must not take the run down.
        (state / "terminals" / "corrupt.json").write_text("{ not json", encoding="utf-8")
        # C: no registry at all, but a beacon whose pid is this live python process.
        (temp / f"kclaude-pane-{host_pid}.sid").write_text(
            json.dumps({"sid": sid_c, "cwd": str(repo_c), "pid": host_pid,
                        "ts": datetime.now(timezone.utc).isoformat()}),
            encoding="utf-8")

        data = _run_build(state, proj, temp)
        if not data:
            _fail("V-TERMINALS-OPEN-REPORTED", "pane_map.json not produced")
            _fail("V-TERMREG-PER-WINDOW", "no output")
            _fail("V-TERMREG-DEAD-HOST-IGNORED", "no output")
            _fail("V-TERMREG-FAIL-OPEN", "no output")
            _fail("V-TERMREG-ADDS-ONLY", "no output")
        else:
            topen = data.get("terminalsOpen") or {}
            tiers = {p["repo"]: p["tier"] for p in data.get("panes", [])}

            if "terminalsOpen" in data:
                _ok("V-TERMINALS-OPEN-REPORTED", f"terminalsOpen={topen}")
            else:
                _fail("V-TERMINALS-OPEN-REPORTED", "key absent from pane_map.json")

            if topen.get("RepoAlpha") == 2:
                _ok("V-TERMREG-PER-WINDOW", "RepoAlpha counted 2 from its own file")
            else:
                _fail("V-TERMREG-PER-WINDOW", f"RepoAlpha={topen.get('RepoAlpha')} want 2")

            if "RepoBeta" not in topen:
                _ok("V-TERMREG-DEAD-HOST-IGNORED", f"dead hostPid {dead} contributed nothing")
            else:
                _fail("V-TERMREG-DEAD-HOST-IGNORED", f"RepoBeta={topen.get('RepoBeta')}")

            # Fail-open: the corrupt file neither raised nor suppressed a good one.
            if topen.get("RepoAlpha") == 2:
                _ok("V-TERMREG-FAIL-OPEN", "corrupt registry skipped, good one still read")
            else:
                _fail("V-TERMREG-FAIL-OPEN", "corrupt file affected a healthy repo")

            # RepoGamma has no registry entry; only the beacon proves it live.
            if tiers.get("RepoGamma") == "OPEN-NOW":
                _ok("V-TERMREG-ADDS-ONLY", "beacon-only pane stayed OPEN-NOW at 600 min idle")
            else:
                _fail("V-TERMREG-ADDS-ONLY", f"RepoGamma tier={tiers.get('RepoGamma')}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("=" * 62)
    print(f"TERMINAL_REGISTRY_PASS={passes}/{passes + fails}  threshold=8/8")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
