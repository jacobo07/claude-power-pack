---
title: Heavy I/O on Windows hosts MUST be resource-governed
date: 2026-05-22
incident: VIDEO_TDR_FAILURE BSOD (bugcheck 0x00000116) on the originating host
scope: any PP-shipped script that does large-volume disk I/O or compression
status: SEALED — apex-doctrine candidate
---

## Trigger

3 hard reboots (Kernel-Power Event 41) in 24 h on the originating host, each
correlated with my heavy I/O operations:

| Timestamp           | Activity in flight                                  |
|---------------------|----------------------------------------------------|
| 2026-05-21 18:02:36 | Big rename-batch operation (4 `.jsonl.live` files) |
| 2026-05-21 21:14:42 | `.jsonl.live` cleanup work continuing              |
| 2026-05-22 17:42:22 | Two back-to-back 380 MB zip writes (snapshot)      |

The final crash bugcheck was `0x00000116` = `VIDEO_TDR_FAILURE` (GPU driver
timeout). The driver bug is not mine to fix. But each instance of "system
already fragile + I deliver heavy I/O burst" pushed it over the edge.

## The rule

Any PP-shipped script that does **>100 MB of writes** OR **>30 s of sustained
CPU + disk activity** MUST carry the full resource-governance stack below.
A single layer is not enough. The five layers in concert make heavy I/O
invisible to interactive workloads.

### Layer 1 — Single-instance lock

File-based mutex with stale-reclaim. Refuses to start if another copy of the
same script is already running, regardless of how it was launched (manual,
scheduled task, agent retry). Prevents two heavy runs from piling up.

```python
LOCK_PATH = BACKUP_ROOT / ".session-snapshot.lock"
LOCK_STALE_SECONDS = 30 * 60   # >30 min → presumed crashed → reclaim
```

Exit code 4 on "held by live instance" — caller (Scheduled Task,
install-global retry, manual re-run) sees an explicit refusal.

### Layer 2 — Idle CPU priority

Drop the current process to `IDLE_PRIORITY_CLASS` (Win32) or `SCHED_IDLE`
(POSIX) before any heavy work. A 60-second compression operation at idle
priority is invisible to the interactive Cursor + Claude.exe + Chrome
foreground; at normal priority it competes for the same scheduler slots.

```python
import ctypes
from ctypes import wintypes
IDLE_PRIORITY_CLASS = 0x40
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.GetCurrentProcess.restype = wintypes.HANDLE
k.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
k.SetPriorityClass.restype = wintypes.BOOL
k.SetPriorityClass(k.GetCurrentProcess(), IDLE_PRIORITY_CLASS)
```

**Sub-trap (sealed same date)**: WITHOUT the explicit `argtypes`/`restype`
declarations, ctypes treats `HANDLE` as `int` (32-bit). On x64 Windows the
HANDLE is 64-bit; the truncated pseudo-handle makes `SetPriorityClass`
return FALSE silently. The priority drop appears to succeed in code but
the process keeps running at NORMAL — defeating the entire hardening.
Empirically caught: standalone test showed `before: 0x20` (NORMAL) →
`after: 0x40` (IDLE) only after adding the type declarations. Always
declare ctypes signatures explicitly for Win32 calls on 64-bit hosts.

### Layer 3 — Fast compression (level 1, not 6)

`zlib` compresslevel default is 6 (balanced). For Layer-3 "last resort"
snapshots the priority is "snapshot exists", not "snapshot is tiny".
Level 1 is ~3x faster at the cost of ~10-15% larger output. On a 1.4 GiB
source: level 6 = ~57 s / 380 MiB; level 1 = ~20 s / 430 MiB. The 3x
runtime reduction is itself a hardening — fewer seconds of disk pressure.

```python
zipfile.ZipFile(..., compresslevel=1)
```

Reserve level 6+ for foreground compression where the user is actively
waiting and the size matters.

### Layer 4 — Disk-space precheck

Refuse to start if free space on the target volume is less than 1.5x
the uncompressed source. A partial zip that exhausts the last MB is
worse than no snapshot — it can starve other writes and corrupt files
mid-flight. Fail-fast with exit code 6.

```python
usage = shutil.disk_usage(str(BACKUP_ROOT))
needed = int(source_bytes * 1.5)
if usage.free < needed: return 6
```

### Layer 5 — Idle-only + battery-aware scheduling

For any Scheduled Task that runs PP heavy I/O:

```powershell
$task = Get-ScheduledTask -TaskName 'ClaudePP-...'
$task.Settings.DisallowStartIfOnBatteries = $true
$task.Settings.StopIfGoingOnBatteries     = $true
$task.Settings.RunOnlyIfIdle              = $true
$task.Settings.IdleSettings.IdleDuration  = 'PT5M'
$task.Settings.IdleSettings.WaitTimeout   = 'PT1H'
Set-ScheduledTask -InputObject $task
```

Means: the task ONLY runs after the host has been idle 5+ minutes AND is
on AC power AND will stop if power switches to battery. Worst case: skips
a day if the user is heavily using the host the whole day; in practice
fires within an hour of overnight idle.

## Cross-references

- Canonical implementation: `tools/session-snapshot.py` (BL-SESSION-SAFETY-001
  Layer 3)
- Installer wiring: `tools/install_global_core.py:_register_snapshot_task`
- Contract: `vault/contracts/SESSION_SAFETY_CONTRACT.md` §2 Layer 3
- Apex candidate: this lesson is a candidate for promotion into
  `apex-completion-standard.md` as the "Heavy I/O Governance Axis" of any
  PP feature that ships a long-running scheduled job.

## Vaccine

Any future PP script doing >100 MB of writes or >30 s of sustained CPU+disk
must demonstrate (in the same emission as the diff) which of the 5 layers
it implements. Missing layers without an explicit justification are
REJECTED.
