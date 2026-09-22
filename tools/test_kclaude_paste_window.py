"""V-PASTE-* -- the paste window of a new pane (T-KCLAUDE-PASTE-WINDOW-001).

Symptom (Owner, 2026-09-22): a prompt pasted into a NEW pane did not arrive.
Root cause: every synchronous step kclaude.ps1 runs before `& claude` is time
in which the pane is not yet Claude -- no prompt box, no bracketed-paste mode --
so a paste in that window has no reader. Measured before the fix: ~2.2 s of
synchronous Python (prelaunch --mode fast ~1.1 s + hook-registry check ~1.1 s).

The property this gate holds: on a BARE pane with an unchanged hook registry,
NOTHING synchronous runs before `launch`. It drives the real launcher, not a
re-implementation, with a stub `claude` first on PATH, and reads the step trace
the launcher writes when KCLAUDE_TRACE_FILE is set. It COUNTS steps rather than
timing them: on this host python's own startup measured 458-1422 ms across
consecutive runs, so a timing budget would fail on load and pass on luck.

Isolation: TEMP and CLAUDE_STATE_DIR point at a private directory, so the
probe cannot consume another pane's restart flag (the launcher's legacy-glob
fallback would) or write the Owner's receipts; trace mode itself suppresses
the detached spawns and the settings repair. The live settings.json is only
READ, by the hook-registry checker.

  python tools/test_kclaude_paste_window.py           # judge the live launcher
  KCLAUDE_PS1=<copy> python tools/...                  # judge a copy (mutation drill)

Exit 0 = all pass, 1 = a gate failed, 2 = HARNESS-FAILED (a precondition the
probe needs did not hold; that is not a finding about the launcher).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
PS1 = Path(os.environ.get("KCLAUDE_PS1") or HOME / ".claude" / "bin" / "kclaude.ps1")
POWERSHELL = r"C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe"
REPO = Path(__file__).resolve().parents[1]
FAKE_SID = "00000000-0000-4000-8000-000000000000"

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def harness_failed(why: str) -> None:
    print(f"HARNESS-FAILED: {why}")
    raise SystemExit(2)


class Probe:
    """One private world: stub claude on PATH, private TEMP and state dir."""

    def __init__(self, root: Path):
        self.root = root
        self.bin = root / "bin"
        self.temp = root / "temp"
        self.state = root / "state"
        for d in (self.bin, self.temp, self.state):
            d.mkdir(parents=True, exist_ok=True)
        self.calls = root / "stub-claude-calls.txt"
        # The stub records every invocation, so `launch` in the trace can be
        # tied to a launch that actually happened (control V-PASTE-STUB-RAN).
        (self.bin / "claude.cmd").write_text(
            f'@echo %*>>"{self.calls}"\r\n@exit /b 0\r\n', encoding="ascii")

    def run(self, name: str, args: list[str], cwd: Path) -> list[str]:
        trace = self.root / f"trace-{name}.txt"
        env = dict(os.environ)
        env.update({
            "KCLAUDE_TRACE_FILE": str(trace),
            "CLAUDE_STATE_DIR": str(self.state),
            "TEMP": str(self.temp),
            "TMP": str(self.temp),
            "PATH": str(self.bin) + os.pathsep + env.get("PATH", ""),
        })
        env.pop("PP_PANE_SCOPE", None)
        p = subprocess.run(
            [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1), *args],
            cwd=str(cwd), env=env, capture_output=True, text=True,
            errors="replace", timeout=120)
        if not trace.exists():
            harness_failed(f"case {name}: launcher wrote no trace (rc={p.returncode}; "
                           f"stderr={p.stderr.strip()[:300]!r})")
        return [ln.strip() for ln in trace.read_text(encoding="ascii").splitlines() if ln.strip()]

    def receipts(self) -> list[dict]:
        f = self.state / "session-config-generations.jsonl"
        if not f.exists():
            return []
        return [json.loads(ln) for ln in f.read_text(encoding="ascii").splitlines() if ln.strip()]

    def stub_calls(self) -> int:
        # Bytes are in the console code page: a bare `echo` in a Spanish-locale
        # cmd writes "ECHO est\xe1 desactivado.", so only the line COUNT is read.
        if not self.calls.exists():
            return 0
        return len(self.calls.read_bytes().splitlines())

    @property
    def cache(self) -> Path:
        return self.state / "hook-registry-verdict-cache.json"


def sync_steps(trace: list[str]) -> list[str]:
    """Synchronous steps that ran BEFORE the launch line."""
    if "launch" not in trace:
        return ["<no launch line>"]
    return [s for s in trace[: trace.index("launch")] if s.startswith("sync:")]


def main() -> int:
    if not PS1.is_file():
        harness_failed(f"launcher not found: {PS1}")
    if not Path(POWERSHELL).is_file():
        harness_failed(f"powershell not found: {POWERSHELL}")
    print(f"subject: {PS1}")

    root = Path(tempfile.mkdtemp(prefix="kclaude-paste-"))
    try:
        pr = Probe(root)
        bare_cwd = root / "bare-cwd"
        bare_cwd.mkdir()

        # --- A: cold cache -- the checker must run, and seed the cache ----------
        a = pr.run("A-cold", [], bare_cwd)
        if sync_steps(a) == ["sync:hook-registry"]:
            _ok("V-PASTE-COLD-JUDGES-LIVE", f"cold cache runs the checker once: {a}")
        else:
            _fail("V-PASTE-COLD-JUDGES-LIVE", f"expected exactly [sync:hook-registry], got {a}")
        rc = pr.receipts()
        if rc and rc[-1].get("verdict") == "VALID" and rc[-1].get("cached") is False:
            _ok("V-PASTE-COLD-RECEIPT", "receipt VALID, cached=false")
        else:
            harness_failed(f"cold run did not judge the live registry VALID: {rc[-1:] or 'no receipt'} "
                           "-- the warm-cache case below would be meaningless")

        # --- B: warm cache, bare pane -- THE PROPERTY -----------------------------
        b = pr.run("B-warm", [], bare_cwd)
        if sync_steps(b) == []:
            _ok("V-PASTE-BARE-NOTHING-BLOCKS", f"bare pane reaches launch with zero synchronous steps: {b}")
        else:
            _fail("V-PASTE-BARE-NOTHING-BLOCKS",
                  f"synchronous steps before launch on a bare pane: {sync_steps(b)} -- each one is "
                  "time in which a pasted prompt has no reader (T-KCLAUDE-PASTE-WINDOW-001)")
        rc = pr.receipts()
        if rc and rc[-1].get("cached") is True and rc[-1].get("verdict") == "VALID":
            _ok("V-PASTE-WARM-RECEIPT-HONEST", "receipt still written, marked cached=true")
        else:
            _fail("V-PASTE-WARM-RECEIPT-HONEST", f"warm run receipt wrong: {rc[-1:]}")

        # --- C: a changed input must re-judge ------------------------------------
        c_body = json.loads(pr.cache.read_text(encoding="utf-8"))
        c_body["key"] = c_body["key"] + "|tampered"
        pr.cache.write_text(json.dumps(c_body), encoding="utf-8")
        c = pr.run("C-stale-key", [], bare_cwd)
        if sync_steps(c) == ["sync:hook-registry"]:
            _ok("V-PASTE-STALE-KEY-REJUDGES", "a cache whose key no longer matches is not trusted")
        else:
            _fail("V-PASTE-STALE-KEY-REJUDGES", f"stale key was trusted: {c}")

        # --- D: only VALID is ever reused ----------------------------------------
        d_body = json.loads(pr.cache.read_text(encoding="utf-8"))   # re-seeded by C
        d_body["verdict"] = "INVALID"
        pr.cache.write_text(json.dumps(d_body), encoding="utf-8")
        d = pr.run("D-invalid-cached", [], bare_cwd)
        if sync_steps(d) == ["sync:hook-registry"]:
            _ok("V-PASTE-INVALID-NEVER-CACHED", "a stored non-VALID verdict forces a live re-judge")
        else:
            _fail("V-PASTE-INVALID-NEVER-CACHED", f"non-VALID verdict silenced the checker: {d}")

        # --- E: positive control -- the tracer DOES see a synchronous python step --
        e = pr.run("E-resume", ["--resume", FAKE_SID], bare_cwd)
        if "sync:prelaunch-fast" in sync_steps(e):
            _ok("V-PASTE-RESUME-KEEPS-DECISION",
                "resume pane still runs the fast decision (load-bearing there), and the tracer sees it")
        else:
            _fail("V-PASTE-RESUME-KEEPS-DECISION",
                  f"no sync:prelaunch-fast on a resume pane: {e} -- either the decision was dropped "
                  "where it matters, or the tracer went blind (then B's green means nothing)")

        # --- F: the namer's pre-launch list, read from disk -----------------------
        proj = HOME / ".claude" / "projects" / re.sub(r"[^a-zA-Z0-9]", "-", str(REPO))
        want = min(400, len(list(proj.glob("*.jsonl")))) if proj.is_dir() else 0
        f = pr.run("F-known", [], REPO)
        got = next((int(s.split(":", 1)[1]) for s in f if s.startswith("known:")), None)
        if want == 0:
            harness_failed(f"no transcripts under {proj}; the known-list case needs a populated cwd")
        if got == want:
            _ok("V-PASTE-KNOWN-FROM-DISK", f"namer would receive {got} pre-existing sids, matching disk")
        else:
            _fail("V-PASTE-KNOWN-FROM-DISK", f"launcher computed known:{got}, disk holds {want}")
        if sync_steps(f) == []:
            _ok("V-PASTE-KNOWN-IS-NOT-A-STEP", "computing the list added no synchronous step")
        else:
            _fail("V-PASTE-KNOWN-IS-NOT-A-STEP", f"{sync_steps(f)}")

        # --- G: every `launch` line was a real launch ------------------------------
        n = pr.stub_calls()
        if n == 6:
            _ok("V-PASTE-STUB-RAN", "stub claude invoked once per case (6/6)")
        else:
            _fail("V-PASTE-STUB-RAN", f"stub claude invoked {n} times for 6 cases")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"PASTE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
