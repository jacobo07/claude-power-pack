# Runbook — video-analyzer MCP server

**Last verified:** 2026-05-24

## What it is

Local Python MCP server (`server.py`, FastMCP HTTP transport) exposing 3 video-analysis tools (`analyze_video`, `transcribe_audio`, `extract_frames`) to claude.ai web via an ngrok static-domain tunnel with mandatory bearer-token auth and a filesystem allow-list.

## Topology

```
claude.ai web
    |  HTTPS POST /mcp + Authorization: Bearer <token>
    v
https://paging-pushpin-sandworm.ngrok-free.dev   <-- STABLE ngrok static domain
    |  forward
    v
http://localhost:8765  (ngrok agent)
    |
    v
python server.py  (FastMCP HTTP server, allow-list = ~/Videos)
```

## Files in `C:\Users\User\Apps\mcp-video-analyzer\`

| File | Purpose |
|---|---|
| `server.py` | the MCP server (FastMCP) |
| `boot_server.ps1` | Task Scheduler wrapper: sets env, launches python |
| `boot_tunnel.ps1` | Task Scheduler wrapper: launches ngrok with static domain |
| `ngrok.exe` | local ngrok binary (3.39.4, downloaded from Equinox CDN) |
| `cloudflared.exe` | legacy — kept for fallback only; tunnel is now ngrok |
| `.bearer` | 64-hex MCP bearer token |
| `.ngrok_config.json` | authtoken + domain + port (informational; boot scripts hardcode the same values) |
| `.boot_server.log` / `.boot_tunnel.log` | latest task-wrapper output |
| `.server.log` / `.ngrok.log` | latest server / ngrok process output |
| `cloudflare_login_simple.py`, `cloudflare_login_via_playwright.py`, `ngrok_setup.py` | one-shot setup helpers (kept for replay / reference) |

## Persistence — how it survives reboot

Two Scheduled Tasks (`mcp-video-server`, `mcp-video-tunnel`), trigger = AtLogon (current user), principal = current user / Limited, restart 3x at 1-min intervals. Both wrap PowerShell -File pointing to the boot scripts above. URL is stable across reboots because ngrok routes a CLAIMED static domain (`paging-pushpin-sandworm.ngrok-free.dev`) to whatever ngrok agent is currently authenticated.

Verify state:
```powershell
Get-ScheduledTask -TaskName 'mcp-video-*' | Select-Object TaskName, State
```

## Manual ops

**Restart from scratch:**
```powershell
Get-Process ngrok | Stop-Process -Force
(Get-NetTCPConnection -LocalPort 8765 -State Listen).OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
schtasks /run /tn "mcp-video-server"
Start-Sleep 6
schtasks /run /tn "mcp-video-tunnel"
```

**Smoke test:**
```powershell
$token = (Get-Content C:\Users\User\Apps\mcp-video-analyzer\.bearer -Raw).Trim()
$body = '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"smoke\",\"version\":\"1.0\"}}}'
curl.exe -s -i -X POST https://paging-pushpin-sandworm.ngrok-free.dev/mcp `
  -H "Authorization: Bearer $token" `
  -H "Accept: application/json, text/event-stream" `
  -H "Content-Type: application/json" --data $body
```
Expect: `HTTP/1.1 200 OK` + an SSE event with `serverInfo.name = video-analyzer`.

**Rotate the bearer:**
1. Generate a new 64-hex string, overwrite `.bearer`.
2. Restart `mcp-video-server` task (the env var is read on launch).
3. Update the Authorization header in claude.ai connector.

**Rotate the ngrok domain** (only needed if Owner re-claims a different free domain):
1. Edit `$domain = '...'` in `boot_tunnel.ps1`.
2. `schtasks /run /tn "mcp-video-tunnel"` (or wait for next reboot).
3. Update the URL in claude.ai connector.

**Disable the whole thing temporarily:**
```powershell
Disable-ScheduledTask -TaskName 'mcp-video-server'
Disable-ScheduledTask -TaskName 'mcp-video-tunnel'
Get-Process ngrok | Stop-Process -Force
```

## Updating the claude.ai connector

claude.ai web -> Settings -> Connectors / Custom Integrations -> video-analyzer ->
- URL: `https://paging-pushpin-sandworm.ngrok-free.dev/mcp`
- Auth header: `Authorization: Bearer <contents of .bearer>`
- Save -> Connect.

## Known caveats

- ngrok free static domains are 1 per account, region-bound. If ngrok ever yanks the free static domain offering, fall back to plain `ngrok http 8765` (random URL per restart) plus the Playwright auto-register flow (see `register_via_playwright.py`).
- The MCP server `analyze_video(path)` reads files from disk. The path allow-list (`MCP_ALLOWED_PATHS` env var, default `~/Videos`) is the only barrier against arbitrary-file-read through the tunnel. Bearer is the auth; allow-list is the blast-radius cap. Keep both.
- Boot scripts MUST stay 7-bit ASCII (no em-dashes, accents). PowerShell 5.1 invoked by Task Scheduler reads .ps1 using the system ANSI codepage, not UTF-8 — non-ASCII bytes mis-parse and break unrelated braces. See `vault/lessons/powershell-5-1-script-encoding.md`.
