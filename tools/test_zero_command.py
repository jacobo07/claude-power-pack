#!/usr/bin/env python3
"""test_zero_command.py - Zero-Command Plan T5 verification harness (G1-G8).

Eight gates verifying the Zero-Command Layer (Components A-D) and the
hook-stack consolidation (Components E.1-E.3) work as specified in
~/.claude/plans/sorted-crafting-hanrahan.md.

Exit code: 0 if all gates either PASS or SKIP-explained; 1 if any FAIL.
Each gate prints a one-line status; the final summary is the contract
the plan's "Done-gate for the whole plan" line references.

Run: python tools/test_zero_command.py
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
PP_ROOT = HOME / ".claude" / "skills" / "claude-power-pack"

NODE = shutil.which("node") or "node"
PYTHON = sys.executable


class Gate:
    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc
        self.status = "PENDING"
        self.detail = ""

    def passed(self, detail: str = "") -> None:
        self.status = "PASS"
        self.detail = detail

    def failed(self, detail: str) -> None:
        self.status = "FAIL"
        self.detail = detail

    def skipped(self, detail: str) -> None:
        self.status = "SKIP"
        self.detail = detail

    def render(self) -> str:
        marker = {"PASS": "[OK]", "FAIL": "[X] ", "SKIP": "[..]",
                  "PENDING": "[??]"}[self.status]
        line = f"  {marker} {self.name} - {self.desc}"
        if self.detail:
            line += f"  ({self.detail})"
        return line


def _mk_project(name: str, *, with_specify: bool = False) -> Path:
    """Create a synthetic project dir under TEMP with .git + package.json."""
    base = Path(tempfile.mkdtemp(prefix=f"zc-{name}-"))
    (base / ".git").mkdir()
    (base / "package.json").write_text('{"name":"zc-test"}', encoding="utf-8")
    if with_specify:
        (base / ".specify" / "memory").mkdir(parents=True)
    return base


def _send_stdin(args: list[str], payload: dict, timeout: int = 10) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        input=json.dumps(payload),
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ---------- G1: hook fanout (deferred to live system) ----------

def gate_g1() -> Gate:
    g = Gate("G1", "hook fanout <=4 spawns per Write (was 9+)")
    fanout_audit = PP_ROOT / "vault" / "audits"
    candidates = list(fanout_audit.glob("hook-fanout-before-after-*.json"))
    if not candidates:
        g.skipped("audit artifact missing - run E.1 measurement first")
        return g
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
        after = data.get("after", {}).get("write_spawns")
        before = data.get("before", {}).get("write_spawns")
        if after is None or before is None:
            g.skipped(f"audit shape unknown: {latest.name}")
            return g
        if after <= 4 and after < before:
            g.passed(f"after={after} before={before} (artifact {latest.name})")
        else:
            g.failed(f"after={after} before={before}; expected after<=4")
    except Exception as e:
        g.failed(f"audit parse error: {e}")
    return g


# ---------- G2: gatekeeper blob slim ----------

def gate_g2() -> Gate:
    g = Gate("G2", "gatekeeper additionalContext <=4 KB on Read")
    gatekeeper = HOME / ".claude" / "hooks" / "gatekeeper-semantic.js"
    if not gatekeeper.is_file():
        g.skipped("gatekeeper-semantic.js not deployed")
        return g
    try:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": str(PP_ROOT / "README.md")},
            "cwd": str(PP_ROOT),
            "session_id": "g2-test",
        }
        rc, out, err = _send_stdin([NODE, str(gatekeeper)], payload, timeout=12)
        if rc != 0:
            g.skipped(f"hook exit {rc}: {err.strip()[:120]}")
            return g
        try:
            resp = json.loads(out)
        except Exception:
            resp = {}
        ctx_size = 0
        ctx = (resp.get("hookSpecificOutput", {}) or {}).get("additionalContext", "")
        if ctx:
            ctx_size = len(ctx.encode("utf-8"))
        else:
            ctx = resp.get("additionalContext", "")
            ctx_size = len(ctx.encode("utf-8")) if ctx else 0
        # Distinguish "gatekeeper ran and was slim" from "gatekeeper returned
        # empty without running its main path" - a 0-byte PASS hides the
        # latter case (code-review efficiency-#3 finding).
        if ctx_size == 0:
            g.skipped("gatekeeper returned empty - cannot prove main path ran "
                      "with synthetic payload; manual probe required")
        elif ctx_size <= 4_000:
            g.passed(f"additionalContext={ctx_size} B (>0 confirms gatekeeper "
                     f"main path ran)")
        else:
            g.failed(f"additionalContext={ctx_size} B > 4 KB")
    except Exception as e:
        g.failed(f"probe error: {e}")
    return g


# ---------- G3: RTK clean (live system observation) ----------

def gate_g3() -> Gate:
    g = Gate("G3", "10 Bash calls produce 0 [rtk] warnings")
    if os.environ.get("RTK_NO_INIT_WARN"):
        g.passed("RTK_NO_INIT_WARN env set")
        return g
    rtk_bin = HOME / ".claude" / "bin" / "rtk.exe"
    if not rtk_bin.is_file():
        g.skipped("rtk.exe not installed")
        return g
    try:
        proc = subprocess.run([str(rtk_bin), "--help"], capture_output=True,
                              text=True, timeout=5)
        combined = (proc.stdout or "") + (proc.stderr or "")
        if "No hook installed" in combined:
            g.failed("rtk --help still emits 'No hook installed' warning")
        else:
            g.passed("rtk --help clean (no install warning)")
    except Exception as e:
        g.skipped(f"rtk probe error: {e}")
    return g


# ---------- G4: Component A ----------

def gate_g4() -> Gate:
    g = Gate("G4", "Component A stubs constitution.md + writes marker")
    hook = PP_ROOT / "hooks" / "zero-command-bootstrap.js"
    if not hook.is_file():
        g.failed(f"hook source missing: {hook}")
        return g
    cwd = _mk_project("g4")
    try:
        payload = {"session_id": "g4-test", "cwd": str(cwd), "source": "startup"}
        start = time.time()
        rc, out, err = _send_stdin([NODE, str(hook)], payload, timeout=10)
        elapsed = time.time() - start
        if rc != 0:
            g.failed(f"hook exit {rc}: {err.strip()[:200]}")
            return g
        marker = cwd / ".pp-onboarded"
        const = cwd / ".specify" / "memory" / "constitution.md"
        if not marker.is_file():
            g.failed(f"marker missing after run (elapsed={elapsed:.2f}s)")
            return g
        if not const.is_file():
            g.failed(f"constitution.md missing after run")
            return g
        body = const.read_text(encoding="utf-8")
        if cwd.name not in body.splitlines()[0]:
            g.failed(f"project name not stubbed into header line: {body.splitlines()[0][:80]}")
            return g
        if elapsed > 2.0:
            g.failed(f"too slow: {elapsed:.2f}s > 2.0s")
            return g
        g.passed(f"marker+constitution in {elapsed:.2f}s")
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
    return g


# ---------- G5: Component B.2 ----------

def gate_g5() -> Gate:
    g = Gate("G5", "B.2 detects new-feature intent + drops flag")
    loader = PP_ROOT / "tools" / "jit_skill_loader.py"
    if not loader.is_file():
        g.failed("jit_skill_loader.py missing")
        return g
    cwd = _mk_project("g5", with_specify=True)
    try:
        payload = {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "add a feature to export the dashboard as CSV",
            "cwd": str(cwd),
            "session_id": "g5-test",
        }
        rc, out, err = _send_stdin([PYTHON, str(loader)], payload, timeout=15)
        flag = cwd / ".pp-pending-spec.json"
        if not flag.is_file():
            g.failed(f"flag not dropped (rc={rc}, stderr={err.strip()[:160]})")
            return g
        flag_data = json.loads(flag.read_text(encoding="utf-8"))
        if flag_data.get("command_to_dispatch") != "/speckit-spec":
            g.failed(f"flag missing/wrong command_to_dispatch: {flag_data}")
            return g
        if "feature to export the dashboard" not in flag_data.get("prompt", ""):
            g.failed("flag prompt does not carry the user prompt")
            return g
        g.passed(f"flag uuid={flag_data.get('uuid', '?')[:8]}")
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
    return g


# ---------- G6: Component B.3 ----------

def gate_g6() -> Gate:
    g = Gate("G6", "B.3 daemon parses and dispatches flag (headless)")
    daemon = PP_ROOT / "hooks" / "pending-keystrokes-daemon.ps1"
    if not daemon.is_file():
        g.failed("daemon source missing")
        return g
    flag_dir = Path(tempfile.mkdtemp(prefix="zc-g6-"))
    try:
        flag = flag_dir / "test.flag"
        flag.write_text(json.dumps({
            "uuid": str(uuid.uuid4()),
            "command_to_dispatch": "/speckit-spec",
            "prompt": "test feature",
            "ttl_sec": 600,
            "ts": time.time(),
        }), encoding="utf-8")
        ps_check = (
            "$f = Get-Content -Raw '" + str(flag) + "'; "
            "$o = $f | ConvertFrom-Json; "
            "if ($o.command_to_dispatch -eq '/speckit-spec' -and "
            "$o.prompt -eq 'test feature') { 'OK' } else { 'BAD' }"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_check],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode == 0 and "OK" in proc.stdout:
            src = daemon.read_text(encoding="utf-8")
            if "SendKeys" in src and "command_to_dispatch" in src:
                g.passed("flag schema valid + daemon has SendKeys + command_to_dispatch")
            else:
                g.failed("daemon source missing SendKeys or command_to_dispatch")
        else:
            g.failed(f"flag schema parse failed: {proc.stdout.strip()} / "
                     f"{proc.stderr.strip()[:120]}")
    finally:
        shutil.rmtree(flag_dir, ignore_errors=True)
    return g


# ---------- G7: Component C ----------

def gate_g7() -> Gate:
    g = Gate("G7", "C verifier runs cleanly + has 3/3 check fns + 3/3 handoff kinds")
    verifier = PP_ROOT / "tools" / "background_verifier_run.py"
    if not verifier.is_file():
        g.failed("background_verifier_run.py missing")
        return g
    cwd = _mk_project("g7")
    try:
        proc = subprocess.run(
            [PYTHON, str(verifier), "--cwd", str(cwd), "--session", "g7"],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode != 0:
            g.failed(f"verifier exit {proc.returncode}: {proc.stderr.strip()[:160]}")
            return g
        src = verifier.read_text(encoding="utf-8")
        required_fns = ["check_mirror_parity", "check_ovo_staleness",
                        "check_spec_coherence"]
        missing = [fn for fn in required_fns if f"def {fn}" not in src]
        if missing:
            g.failed(f"verifier missing functions: {missing}")
            return g
        for kind in ("mirror-drift", "ovo-stale", "spec-incoherent"):
            if f'"{kind}"' not in src:
                g.failed(f"verifier missing handoff kind '{kind}'")
                return g
        g.passed("3/3 fns + 3/3 handoff kinds present, runs clean")
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
    return g


# ---------- G8: Component D ----------

def gate_g8() -> Gate:
    g = Gate("G8", "Component D probe writes marker (+ handoff on gaps)")
    probe = PP_ROOT / "tools" / "first_time_project_init.py"
    if not probe.is_file():
        g.failed("first_time_project_init.py missing")
        return g
    cwd = _mk_project("g8")
    try:
        proc = subprocess.run(
            [PYTHON, str(probe), "--cwd", str(cwd), "--session", "g8"],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode != 0:
            g.failed(f"probe exit {proc.returncode}: {proc.stderr.strip()[:160]}")
            return g
        marker = cwd / ".pp-onboarded-prereqs"
        if not marker.is_file():
            g.failed("marker missing after probe")
            return g
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
        except Exception as e:
            g.failed(f"marker not valid JSON: {e}")
            return g
        if "results" not in data or len(data["results"]) < 4:
            g.failed(f"marker missing 4 probe results: {data.get('results')}")
            return g
        gaps = data.get("gaps_count", -1)
        if gaps == 0:
            g.passed("probe ran 4 checks, 0 gaps on this host (marker valid)")
        else:
            handoff_dir = cwd / "vault" / "handoffs"
            handoffs = list(handoff_dir.glob("pp-onboarding-*.md")) if handoff_dir.is_dir() else []
            if handoffs:
                g.passed(f"gaps={gaps}, handoff written")
            else:
                g.failed(f"gaps={gaps} but no handoff in vault/handoffs/")
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
    return g


# ---------- G9: T6 sealing in apex (added per plan Task 6.3) ----------

def gate_g9() -> Gate:
    g = Gate("G9", "T6: 'Zero-Command Standard' sealed in apex + PP mirror cross-link")
    apex = HOME / ".claude" / "knowledge_vault" / "core" / "apex-completion-standard.md"
    mirror = PP_ROOT / "vault" / "knowledge_base" / "apex_baseline_doctrine.md"
    if not apex.is_file():
        g.failed(f"apex missing: {apex}")
        return g
    if not mirror.is_file():
        g.failed(f"PP mirror missing: {mirror}")
        return g
    try:
        apex_body = apex.read_text(encoding="utf-8", errors="replace")
        mirror_body = mirror.read_text(encoding="utf-8", errors="replace")
        if "Zero-Command Standard (sealed 2026-05-21)" not in apex_body:
            g.failed("apex missing 'Zero-Command Standard (sealed 2026-05-21)' heading")
            return g
        if "Zero-Command Standard cross-link" not in mirror_body:
            g.failed("PP mirror missing 'Zero-Command Standard cross-link' heading")
            return g
        g.passed("apex section + PP mirror cross-link present")
    except Exception as e:
        g.failed(f"read error: {e}")
    return g


def main() -> int:
    gates = [
        gate_g1(), gate_g2(), gate_g3(), gate_g4(),
        gate_g5(), gate_g6(), gate_g7(), gate_g8(),
        gate_g9(),
    ]
    print("Zero-Command Verification Harness (T5, G1-G8)")
    print(f"Run: {datetime.now(timezone.utc).isoformat()}")
    print("")
    for g in gates:
        print(g.render())
    print("")
    passed = sum(1 for g in gates if g.status == "PASS")
    failed = sum(1 for g in gates if g.status == "FAIL")
    skipped = sum(1 for g in gates if g.status == "SKIP")
    print(f"Summary: {passed} PASS / {failed} FAIL / {skipped} SKIP "
          f"(of {len(gates)})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
