# AutoResearch -> KobiiClaw VPS migration (Block B, 2026-06-30)

STOP #1 decisions: VPS schedule + silence hook + SessionStart pull. Target =
KobiiClaw `204.168.166.63`, user `kobicraft`, key `~/.ssh/kobicraft_vps`.

## Reality corrections that shaped this (from the FASE -1 scan)

- The on-screen "Stop says [KobiiClaw AutoResearch v2] ..." was the **Stop hook**
  `~/.claude/hooks/kobiiclaw-autoresearch.js` systemMessage, fired every session
  exit / every project (throttled 6h). NOT a window, NOT a real scheduler.
- The engine `modules/autoresearch/nightcrawler.py` was built to run "2x/day via
  scheduler" but **no scheduled task ever existed** -> it effectively never ran
  (orphan / write-without-read). The VPS cron is the first real schedule.
- The engine uses only **public RSS + YouTube-RSS over httpx** -> zero credentials
  (Telegram + video-analysis both disabled). Trivially VPS-portable.

## VPS layout (`/home/kobicraft/autoresearch/`)

- `.venv/` — isolated venv (httpx 0.28.1, feedparser 6.0.12).
- Engine files (scp'd from `modules/autoresearch/`): `nightcrawler.py`,
  `rss_sniffer.py`, `youtube_firehose.py`, `cross_signal_bus.py`,
  `signal_scorer.py`, `config.json`. (video_analyzer/vision/whisper skipped —
  import-guarded behind the disabled video flag.)
- `run.sh` (755) — sources `.env`, runs nightcrawler via the venv.
- `.env` (600) — VPS-only secrets, empty now; populated in Block C
  (dedicated Twitter/Reddit accounts).
- `logs/nightcrawler.log` — cron stdout/stderr.
- State (digests, signals, lockfile): `/home/kobicraft/.claude/autoresearch-triggers/`.

## V1-V5 (done-gates observed)

- **V1** Manual run OK: 7.7s, 3/3 steps OK, 33 signals -> 6 accepted + 2 cross,
  real `latest_digest.md` produced.
- **V2** `.env` perms 600, VPS-only, not in any repo.
- **V3** cron `0 2,8,14,20 * * *` (every 6h) -> `run.sh`. Engine self-throttles via
  its 6h lockfile, so the cadence is idempotent. Wrapper test: `Throttled... exit 0`.
- **V4** Local Stop hook silenced (`~/.claude/hooks/kobiiclaw-autoresearch.js`:
  return `{continue:true}`, no systemMessage — verified HAS_SYSMSG=false). New
  SessionStart pull added to `hooks/session_start_hub.js` (Hook 12): inline cache
  read -> additionalContext; detached TTL-gated (6h) windowsHide scp refresh.
  E2E verified: first run pulls (cache 1540 B), second run surfaces the digest.
- **V5** No local scheduled task to disable (none ever existed). Local footprint
  is now the silenced hook + the SessionStart pull only.

## Revert

- VPS: `crontab -e` remove the autoresearch line; `rm -rf ~/autoresearch`.
- Local Stop hook: restore the prior `systemMessage` return in
  `~/.claude/hooks/kobiiclaw-autoresearch.js` (git-untracked; live-only file).
- Hub: revert Hook 12 in `hooks/session_start_hub.js` (this commit).

## Open (Block C, after STOP #2)

Expand sources via Agent-Reach (dedicated Twitter/Reddit accounts) -> populate
`.env`, extend the engine. Disk on the VPS is at 94% (9.3 GB free) — keep the
Agent-Reach footprint tight (use `--safe`, avoid heavy browser/yt-dlp caches).
