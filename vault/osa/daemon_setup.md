# OSA Background Daemon Setup

> Sealed 2026-05-29 (BL-GLOB-001). Owner-side deployment. The OSA
> dispatcher does NOT spawn `claude -p` autonomously — it logs the
> trigger decision and queues the audit. Running this daemon is what
> makes the OSA *proactive* in long-running environments where the
> Owner is not at the keyboard.

## Linux / VPS — crontab

```cron
# Every 30 minutes: run OSA audit, respect throttle gate.
# Append output to a rotating log; never block the cron slot.
*/30 * * * * cd $HOME/.claude/skills/claude-power-pack && \
  python -m modules.osa.osa_command --audit \
  >> /var/log/osa-daemon.log 2>&1
```

Install with `crontab -e`. Verify with `crontab -l | grep osa`.

Log rotation (Linux):

```bash
sudo tee /etc/logrotate.d/osa-daemon <<EOF
/var/log/osa-daemon.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

## Windows — Task Scheduler

1. Open Task Scheduler → Action → Create Task.
2. **General** tab: name `osa-daemon`, run whether user logged in or not, "Do not store password" off.
3. **Triggers** tab: New → Daily, recur every 1 day, repeat task every 30 minutes for a duration of 1 day.
4. **Actions** tab: New → Start a program:
   - Program/script: `python`
   - Add arguments: `-m modules.osa.osa_command --audit`
   - Start in: `%USERPROFILE%\.claude\skills\claude-power-pack`
5. **Conditions** tab: uncheck "Start the task only if computer is on AC power" if on a laptop.
6. **Settings** tab: check "If the task fails, restart every 1 minute, attempt to restart up to 3 times."

Verify with PowerShell:

```powershell
Get-ScheduledTask -TaskName osa-daemon | Get-ScheduledTaskInfo
```

## Manual test

Before installing the scheduler, run once interactively:

```bash
cd $HOME/.claude/skills/claude-power-pack
python -m modules.osa.osa_command --audit
```

Expected exit conditions:

- `BUDGET_EXHAUSTED` → exit 0 (skip the cycle cleanly). The next
  scheduled run will retry once the daily budget rolls over.
- `CACHE_HIT:<min>` → exit 0 with the cached summary.
- `GO` + no trigger fired → exit 0 with `status=sleepy`.
- `GO` + trigger fired → exit 0 with `status=would_invoke`. The V1
  contract is that the dispatcher does NOT autonomously spawn
  `claude -p`; it logs the decision. Owner invokes the agent
  manually via `/osa --force` if they want a real audit run.

## Verify daemon is alive

```bash
# Linux
sudo systemctl status cron        # or `crond`
ls -la /var/log/osa-daemon.log

# Windows
Get-ScheduledTask osa-daemon
Get-EventLog Application -Source 'Task Scheduler' -Newest 5
```

## Disable

```bash
# Linux: edit crontab and delete the line
crontab -e

# Windows
Unregister-ScheduledTask -TaskName osa-daemon -Confirm:$false
```

## Cost note

Each run executes `python -m modules.osa.osa_command --audit` which
reads TIS / dispatcher state and emits JSON. It does NOT call
`claude -p` (V1 contract). Daemon cost ~= zero tokens. The throttle
gate's `max_daily_calls` only matters if/when V2 wires the dispatcher
to spawn audits autonomously.
