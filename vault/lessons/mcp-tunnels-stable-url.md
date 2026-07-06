# MCP tunnels — quick is ephemeral, named/static is the only durable answer

**Sealed:** 2026-05-24 (video-analyzer MCP after 50-min URL-stability detour)
**Applies to:** any MCP server intended to be reachable from `claude.ai` web through a tunnel.

## The trap

`cloudflared tunnel --url http://localhost:PORT --no-autoupdate` (the "quick tunnel" pattern) prints a `https://<random>.trycloudflare.com` URL and routes it to your local server. It feels permanent because it survives the SSH-y interactive session. It is not: the URL is bound to that specific cloudflared process. When the process dies (host reboot, Ctrl+C, OOM, anything) the URL goes 404 forever and the next start gets a new random URL. Same shape for `ngrok http PORT` (no `--url` flag) and for `localtunnel` / `serveo` / any "give me a free random subdomain" service.

Symptom on the claude.ai side: "Couldn't reach the MCP server" on a connector that "was working yesterday".

## The fix

You need a URL whose lifetime is decoupled from the tunnel-agent process:

1. **Cloudflare named tunnel + DNS-routed hostname** (`cloudflared tunnel create` + `cloudflared tunnel route dns`). Requires (a) a Cloudflare account and (b) a domain managed by Cloudflare DNS. Login is interactive: `cloudflared tunnel login` opens the OS default browser to a `dash.cloudflare.com/argotunnel?...` URL; the user authorizes and picks a zone, cert.pem is written to `~/.cloudflared/`. Trap: the callback can fail with `Failed to fetch resource` if the user takes >9 min OR if Turnstile rejects a Playwright-driven browser (it does — Cloudflare detects Playwright CDP fingerprint regardless of who solves the captcha). For automated installs, having the user open the URL in their real Brave/Chrome (with their normal cookies) is the safest path.

2. **ngrok with reserved static subdomain** (`ngrok http --url=https://<your>.ngrok-free.dev PORT`). Free tier as of 2026-05 gives 1 reserved subdomain per account (host TLD is `ngrok-free.dev`, NOT `.app`). Requires (a) ngrok account, (b) authtoken (`ngrok config add-authtoken <token>`), (c) one claimed domain via dashboard.ngrok.com/domains. NO domain-of-your-own needed -> simpler than Cloudflare named tunnel for a single-user dev box.

3. **Tailscale Funnel** (not tried in this session) — exposes a Tailscale-private service on a stable `*.ts.net` hostname. Worth evaluating if (1) and (2) ever break.

## Persistence layer (orthogonal to choice of tunnel)

Two Windows Scheduled Tasks at AtLogon (current user, no admin needed):
- Task A: launches the MCP server (`python server.py` wrapped in a `boot_server.ps1`).
- Task B: launches the tunnel agent pointing at the same port (`ngrok http --url=https://STATIC PORT` wrapped in a `boot_tunnel.ps1`).

Both wrappers are 7-bit ASCII (see [[powershell-5-1-script-encoding]]). Task B includes a wait-for-port loop because Task Scheduler triggers both at the same instant.

## Decision tree for the next time

```
need claude.ai web access?
|-- no  -> use stdio mode (Claude Desktop only); skip the tunnel entirely
|-- yes -> need URL stable across reboots?
    |-- no  -> quick tunnel + accept paste-URL-after-reboot ritual
    |-- yes -> have a Cloudflare-managed domain?
        |-- yes -> Cloudflare named tunnel (route dns to <sub>.yourdomain.tld)
        |-- no  -> ngrok free reserved subdomain
```

## What burned 50 minutes (so the next session doesn't)

- 9 min: Playwright drives Cloudflare login -> Turnstile rejects the headed Brave (CDP fingerprint detected).
- 9 min: Manual Cloudflare login in user's real Brave -> cert.pem callback fails (`Failed to fetch resource`, no user-side error shown until cloudflared times out).
- 4 min: ngrok login Playwright v1 -> `wait_for_dashboard` substring-matched the HOSTNAME `dashboard.ngrok.com` as a "logged-in" signal. False positive interrupted the user mid-Google-OAuth.
- 10 min: ngrok login Playwright v2 -> Cookiebot privacy modal blocked the login page; user opened ngrok signup in their REAL Brave + pasted authtoken + claimed domain in 5 min.
- ASCII-encoding trap on the boot wrappers (see lessons/powershell-5-1-script-encoding.md) added another 15.

## Cross-ref

- vault/runbooks/video-analyzer-mcp.md
- vault/lessons/powershell-5-1-script-encoding.md
- C:\Users\User\Apps\mcp-video-analyzer\boot_server.ps1, boot_tunnel.ps1
- Memory: feedback_mcp_tunnel_stability.md
