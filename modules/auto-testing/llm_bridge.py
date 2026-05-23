"""LLM bridge for the Auto-Testing Skill — claude.exe -p via STDIN.

Spec ref: vault/specs/auto-testing-gate.md §6

Vaccines applied:
- WinError 206 (Windows argv 8 KB cap) — user message via STDIN, never
  as a positional argument. See
  vault/lessons/windows-argv-limit-stdin-fix.md (sealed 2026-05-23 mid
  deep-research Paso 1.8).
- Stop-hook subprocess recursion — sentinel env-var
  CLAUDEPP_AUTOTEST_RUNNING=1 set in the spawned claude.exe's env so
  hooks/auto-test-gate.js silently exits when re-fired from inside the
  child's Stop chain. Sister lesson:
  vault/lessons/stop-hook-subprocess-recursion.md.

The LLM call is the slow part of the fast gate (~17-30s on this host
empirically). Hard timeout default = 25s; on timeout the runner returns
LLMTimeout, which the upstream gate translates to CEILING(LLM_timeout)
and ALLOWS the commit (fail-OPEN by design — a degraded LLM must not
block real commits).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


SENTINEL_ENV = "CLAUDEPP_AUTOTEST_RUNNING"


@dataclass
class LLMResult:
    ok: bool
    text: str
    duration_sec: float
    error: str = ""


class LLMTimeout(Exception):
    pass


class LLMNotAvailable(Exception):
    pass


def _resolve_claude_cli() -> Path:
    """Pinpoint claude.exe.

    Order: HOME/.local/bin/claude.exe (Owner install), then PATH lookup.
    Sister logic to deep_research._llm_claude_cli.
    """
    home = Path(os.path.expanduser("~"))
    candidate = home / ".local" / "bin" / "claude.exe"
    if candidate.exists():
        return candidate
    resolved = shutil.which("claude.exe") or shutil.which("claude")
    if not resolved:
        raise LLMNotAvailable("claude.exe not found in ~/.local/bin or on PATH")
    return Path(resolved)


def call_llm(system: str, user: str, timeout: int = 25) -> LLMResult:
    """Synchronous claude.exe -p call.

    Args:
        system: short system prompt (rides in --append-system-prompt;
                size-bounded by argv but the typical prompt is <2 KB).
        user:   user message (any size; passed via STDIN).
        timeout: wall-clock cap in seconds. Default 25 to fit the gate's
                 30s budget with margin for spawn + parse.

    Returns:
        LLMResult. On any failure (binary missing, timeout, non-zero
        exit, empty stdout), ok=False and `error` carries the reason.
        Callers decide whether to ceiling-allow or escalate.
    """
    import time

    t0 = time.monotonic()
    try:
        cli = _resolve_claude_cli()
    except LLMNotAvailable as e:
        return LLMResult(ok=False, text="", duration_sec=0.0, error=str(e))

    args: list[str] = [
        str(cli),
        "-p",
        "--disable-slash-commands",
        "--disallowed-tools", "*",
        "--append-system-prompt", system,
    ]

    sub_env = os.environ.copy()
    sub_env[SENTINEL_ENV] = "1"

    try:
        r = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            input=user,
            env=sub_env,
        )
    except subprocess.TimeoutExpired:
        return LLMResult(
            ok=False, text="", duration_sec=time.monotonic() - t0,
            error="LLM timeout after " + str(timeout) + "s",
        )
    except OSError as e:
        return LLMResult(
            ok=False, text="", duration_sec=time.monotonic() - t0,
            error="subprocess error: " + str(e),
        )

    duration = time.monotonic() - t0

    if r.returncode != 0:
        snippet = (r.stderr or r.stdout or "")[:200]
        return LLMResult(
            ok=False, text="", duration_sec=duration,
            error="exit " + str(r.returncode) + ": " + repr(snippet),
        )

    output = (r.stdout or "").strip()
    if not output:
        return LLMResult(
            ok=False, text="", duration_sec=duration,
            error="empty stdout",
        )

    return LLMResult(ok=True, text=output, duration_sec=duration)


def main(argv: list[str]) -> int:
    """CLI smoke runner.

    Usage:
      python llm_bridge.py "<system>" "<user>"

    Empirically verified 2026-05-23 with system="You are terse." and
    user="Say HELLO and nothing else."
    """
    if len(argv) != 2:
        print("usage: llm_bridge.py <system> <user>", flush=True)
        return 2
    system, user = argv
    res = call_llm(system, user, timeout=25)
    if res.ok:
        print("OK (" + str(round(res.duration_sec, 1)) + "s): " + res.text)
        return 0
    print("FAIL (" + str(round(res.duration_sec, 1)) + "s): " + res.error)
    return 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
