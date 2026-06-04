#!/usr/bin/env python3
"""
MCP Health Check -- PP BL-MCP-STABILITY-001.

Unified health probe for every MCP server Claude Code knows about on this
host, across BOTH mechanisms (UKDL T-PW-001):

  1. ``mcpServers``   in ~/.claude.json  -- stdio, CLIENT owns the pipe.
  2. ``enabledPlugins`` in settings.json -- plugin loader owns the lifecycle.

CRITICAL ARCHITECTURAL TRUTH (FASE -1 forensics, 2026-06-04):
  A stdio mcpServer is a child of claude.exe communicating over claude's
  own stdin/stdout pipe. When it dies you get JSON-RPC -32000. An EXTERNAL
  relauncher (Task Scheduler, this script, anything) CANNOT reconnect it --
  a separately-spawned process has its own stdio and is an ORPHAN, not a
  reconnection. Only a Claude-side restart (/mcp reconnect, or relaunch)
  resurrects a stdio server. Therefore for stdio servers this tool does
  DETECTION + ADVISORY only. It never relaunches them.

  Plugin servers (e.g. playwright) ARE externally recoverable: kill the
  stale node procs and the plugin loader respawns clean transport on next
  use. That recovery is delegated to playwright_watchdog.ps1 (T-PW-001).

Status vocabulary per server:
  HEALTHY        process alive (stdio) / plugin enabled + watchdog (plugin)
  DEAD           configured stdio server, no process -> -32000 territory
  STALE          plugin procs alive but no watchdog -> transport may stale
  NEEDS_WATCHDOG plugin enabled, procs alive, watchdog not installed
  NOT_ENABLED    plugin not enabled
  UNKNOWN        could not determine

ASCII-only output (survives Windows cp1252 console). Exit 0 unless --strict.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PP_PATH = Path(__file__).resolve().parent.parent
TOOLS = PP_PATH / "tools"
CLAUDE_JSON = Path.home() / ".claude.json"
SETTINGS = Path.home() / ".claude" / "settings.json"
TELEMETRY_DIR = PP_PATH / "vault" / "telemetry" / "mcp_health"
TELEMETRY_LOG = TELEMETRY_DIR / "mcp_state.jsonl"

# Reuse the sealed Playwright probe instead of duplicating it (T-PW-001).
sys.path.insert(0, str(TOOLS))
try:
    import check_playwright_mcp as pw  # type: ignore
except Exception:  # pragma: no cover - defensive; never block a health read
    pw = None


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_stdio_servers() -> dict[str, dict]:
    """Return {name: cfg} for every stdio mcpServer in ~/.claude.json
    (top-level + per-project)."""
    if not CLAUDE_JSON.exists():
        return {}
    try:
        d = json.loads(CLAUDE_JSON.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    out: dict[str, dict] = {}
    for name, cfg in (d.get("mcpServers") or {}).items():
        out[name] = cfg
    for _path, pcfg in (d.get("projects") or {}).items():
        for name, cfg in (pcfg.get("mcpServers") or {}).items():
            out.setdefault(name, cfg)
    return out


def server_signature(cfg: dict) -> str | None:
    """Most specific token identifying this server's process command line.

    For npx/bunx/uvx servers the package spec (e.g. '@21st-dev/magic',
    '@notionhq/notion-mcp-server', 'coplay-mcp-server') is the strongest
    match against a live process command line.
    """
    args = cfg.get("args") or []
    # Prefer an arg that looks like a package: has a slash, or '@scope', or
    # ends in a known mcp suffix. Skip flags and key=value pairs.
    best = None
    for a in args:
        if not isinstance(a, str):
            continue
        s = a.strip()
        if s.startswith("-") or s.upper().startswith("API_KEY"):
            continue
        if "/" in s or s.startswith("@") or "mcp" in s.lower():
            # strip a trailing @version for a looser substring match
            tok = s.split("@latest")[0] if s.endswith("@latest") else s
            best = tok
            break
    if best is None:
        # fall back to the command itself (e.g. a bare binary name)
        cmd = cfg.get("command")
        if isinstance(cmd, str) and cmd and cmd not in ("npx", "bunx", "uvx", "bun", "uv", "node"):
            best = cmd
    return best


def get_running_cmdlines() -> list[tuple[int, int, str]]:
    """Return [(pid, age_minutes, cmdline)] for candidate MCP host processes.

    One PowerShell round-trip for all of node/bun/python/uv -- never N spawns.
    """
    if platform.system() != "Windows":
        return []
    ps_cmd = (
        "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Name -in @('node.exe','bun.exe','python.exe',"
        "'pythonw.exe','uv.exe','uvx.exe','deno.exe') -and $_.CommandLine } | "
        "ForEach-Object { "
        "$age = if ($_.CreationDate) { "
        "[int][Math]::Round((New-TimeSpan -Start $_.CreationDate -End (Get-Date)).TotalMinutes) "
        "} else { 0 }; "
        "Write-Output ('PID=' + $_.ProcessId + ' AGE=' + $age + ' CMD=' + $_.CommandLine) }"
    )
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=20,
        )
    except Exception:
        return []
    rows: list[tuple[int, int, str]] = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("PID="):
            continue
        try:
            head, cmd = line.split(" CMD=", 1)
            parts = dict(p.split("=", 1) for p in head.split() if "=" in p)
            rows.append((int(parts["PID"]), int(parts.get("AGE", 0)), cmd))
        except Exception:
            continue
    return rows


def probe_stdio(servers: dict[str, dict], procs: list[tuple[int, int, str]]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for name, cfg in servers.items():
        sig = server_signature(cfg)
        entry = {
            "mechanism": "stdio (mcpServers, client-owned pipe)",
            "command": cfg.get("command", ""),
            "signature": sig,
            "status": "UNKNOWN",
            "pid": None,
            "age_minutes": None,
        }
        if sig:
            sig_l = sig.lower()
            match = next(((pid, age) for pid, age, cmd in procs if sig_l in cmd.lower()), None)
            if match:
                entry["status"] = "HEALTHY"
                entry["pid"], entry["age_minutes"] = match
            else:
                entry["status"] = "DEAD"
        result[name] = entry
    return result


def probe_playwright() -> dict:
    """Delegate to the sealed T-PW-001 probe; classify into our vocabulary."""
    entry = {
        "mechanism": "plugin (enabledPlugins, loader-owned, externally recoverable)",
        "status": "UNKNOWN",
        "procs": 0,
        "watchdog_installed": False,
        "watchdog_state": "unknown",
    }
    if pw is None:
        return entry
    try:
        _cfg, enabled = pw.find_plugin_config()
        procs = pw.get_playwright_processes()
        wd_installed, wd_state = pw.check_watchdog()
    except Exception:
        return entry
    entry["procs"] = len(procs)
    entry["watchdog_installed"] = bool(wd_installed)
    entry["watchdog_state"] = wd_state
    if not enabled:
        entry["status"] = "NOT_ENABLED"
    elif wd_installed:
        entry["status"] = "HEALTHY"
    elif procs:
        # procs alive but no watchdog -> transport can go stale unattended
        entry["status"] = "NEEDS_WATCHDOG"
    else:
        entry["status"] = "NEEDS_WATCHDOG"
    return entry


def append_telemetry(source: str, servers: dict[str, dict]) -> None:
    """M3: classify magic's (and every server's) death-mode over time.

    Append-only JSONL: one row per run. Over N sessions the rows let us
    say whether a stdio server dies at startup vs after idle vs randomly.
    """
    try:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": _utcnow(),
            "source": source,
            "servers": {
                n: {"status": e.get("status"), "age_minutes": e.get("age_minutes")}
                for n, e in servers.items()
            },
        }
        with TELEMETRY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    except OSError as e:
        # Fail-open: telemetry must never block a health read. But not
        # silent -- leave a breadcrumb on stderr so a broken log surface
        # is observable (Error-Never-Silent).
        print(f"[mcp_health_check] telemetry append skipped: {e}", file=sys.stderr)


def print_report(stdio: dict[str, dict], playwright: dict) -> None:
    print("=" * 60)
    print("MCP HEALTH CHECK -- all servers, both mechanisms")
    print("=" * 60)

    print("\n[stdio mcpServers -- ~/.claude.json -- DETECTION+ADVISORY only]")
    if not stdio:
        print("  (none configured)")
    for name, e in stdio.items():
        tag = {
            "HEALTHY": "OK   ",
            "DEAD": "DEAD ",
            "UNKNOWN": "WARN ",
        }.get(e["status"], "     ")
        extra = f"pid={e['pid']} age={e['age_minutes']}min" if e.get("pid") else ""
        print(f"  {tag} {name:14s} {e['status']:8s} {extra}")

    print("\n[plugin servers -- settings.json enabledPlugins -- externally recoverable]")
    tag = {"HEALTHY": "OK   ", "NEEDS_WATCHDOG": "WARN ",
           "NOT_ENABLED": "FAIL "}.get(playwright["status"], "     ")
    print(f"  {tag} playwright     {playwright['status']:8s} "
          f"procs={playwright['procs']} watchdog={playwright['watchdog_state']}")

    # Advisories
    dead = [n for n, e in stdio.items() if e["status"] == "DEAD"]
    if dead:
        print("\n--- ADVISORY: stdio server(s) DEAD ---")
        for n in dead:
            print(f"  {n}: -32000 / disconnected. RECOVER IN CLAUDE CODE:")
            print(f"     1) Run /mcp  ->  reconnect '{n}'")
            print(f"     2) If that fails: restart Claude Code (the client respawns it).")
        print("  DO NOT launch the server externally -- a separately-spawned")
        print("  process is an ORPHAN, not a reconnection (T-MCP-RECONNECT-001).")
    if playwright["status"] == "NEEDS_WATCHDOG":
        print("\n--- ADVISORY: Playwright watchdog not installed ---")
        print("  Install (one-time, true auto-recovery):")
        print("     powershell -File tools\\playwright_watchdog.ps1 -Action start")
        print("  Disconnected right now:")
        print("     powershell -File tools\\playwright_stale_killer.ps1")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Unified MCP health check.")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON")
    ap.add_argument("--source", default="manual",
                    help="telemetry source tag (e.g. session_start, manual)")
    ap.add_argument("--no-log", action="store_true", help="skip telemetry append")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any server DEAD or playwright NEEDS_WATCHDOG")
    args = ap.parse_args(argv)

    servers = load_stdio_servers()
    procs = get_running_cmdlines()
    stdio = probe_stdio(servers, procs)
    playwright = probe_playwright()

    if not args.no_log:
        merged = dict(stdio)
        merged["playwright"] = playwright
        append_telemetry(args.source, merged)

    if args.json:
        print(json.dumps({"stdio": stdio, "playwright": playwright}, indent=2))
    else:
        print_report(stdio, playwright)

    if args.strict:
        any_dead = any(e["status"] == "DEAD" for e in stdio.values())
        pw_bad = playwright["status"] in ("NEEDS_WATCHDOG", "NOT_ENABLED")
        return 1 if (any_dead or pw_bad) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
