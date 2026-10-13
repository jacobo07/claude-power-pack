# F. Windows vs Linux claude.exe footprint: attribution (2026-10-13)

Planes: **windows-laptop** (32,061 MB RAM, 42 claude.exe, live Owner panes; Available under 4 GB, so read-only
instruments only) and **GEX44 Linux** (64 GB, live claude processes). Workloads are NOT matched between planes;
every cross-plane statement below is labelled with that limit.

## Instruments
- Windows: `python -m modules.prr.regions --json` (VirtualQueryEx region walk + GetProcessMemoryInfo EX2), joined
  with process creation time from Win32_Process. Read-only; nothing is trimmed, suspended or signalled.
- Linux: `/proc/<pid>/smaps_rollup` (Rss, Anonymous, Swap) and `/proc/<pid>/status` (VmHWM, VmData).

## Windows, 39 claude.exe (median per process)
| Quantity | MB | Meaning |
|---|---|---|
| Private bytes (commit charge, what the census called "private") | 896.6 | committed private memory; backed by RAM **or pagefile** |
| Private working set | 252.9 | private pages resident in RAM now |
| Private committed, not resident | 608.0 | paged out, or committed and never touched |
| Image committed | 273.4 | the claude.exe executable, file-backed, physically shared across all 39 |
| Mapped committed | 9.8 | file mappings |
| Private reserved (address space only) | 9,913.2 | JSC/allocator virtual reservations; zero RAM, zero commit |

Sums over 39: commit 33,074 MB, private resident 9,621 MB, private non-resident 23,453 MB.
Age does not drive the split: processes 2.4-5.6 h old already commit 673-1,129 MB with 179-439 MB resident;
a 164 h process commits 1,082 / 385 resident. Peak working sets (468-1,206 MB) far above current working sets
show the memory manager trimming resident pages under RAM starvation. For several young processes commit exceeds
peak working set by 400-600 MB (e.g. pid 41032: commit 996, peak WS 468): that part was never resident at once,
the signature of allocator commit-ahead.

## Linux (GEX44), live claude
| pid | age h | RSS | Anonymous | File-backed | Swap | VmHWM |
|---|---|---|---|---|---|---|
| 1810054 | 90.2 | 154.8 | 64.1 | 90.7 | 8.9 | 165.2 |
| 3878307 | 0.04 | 356.1 | 227.4 | 128.7 | 0 | 384.1 |
Linux has overcommit: untouched anonymous memory is neither RSS nor charged, so Linux has no analogue of the
608 MB "committed, not resident" bucket.

## Verdict on the "~887 MB vs 107-160 MB" gap
The two numbers measure different things. 887 MB is Windows **commit charge**; 107-160 MB was Linux **anonymous
RSS** on a fresh stub-API bench. The like-for-like Windows number is private working set: median 253 MB (179-439 MB),
against Linux anonymous 64-227 MB under unmatched workloads. The residual gap is therefore at most ~1-2x, not 5-8x,
and is not yet attributed between workload and platform.

| Component (per process) | MB | Class |
|---|---|---|
| Commit-ahead / trimmed private (commit minus private WS) | ~608 | ALLOCATOR + WINDOWS_SPECIFIC (no overcommit). Costs commit limit and pagefile, **not RAM** |
| claude.exe image | ~273 committed, ~30 resident private-equivalent | HOST_IMMUTABLE, shared across processes |
| Address-space reservations | ~9,900 | HOST_IMMUTABLE, zero physical cost |
| Private resident | ~253 | WORKLOAD_CONTROLLED + UNKNOWN until a matched run |

## What this changes
1. The laptop's RAM problem is count x resident, not a per-process 887 MB: 42 claude (11.5 GB working set) plus
   54 Cursor processes (5.6 GB WS, 12.6 GB commit). Commit charge 79.0 of 101.3 GB is a second, separate limit:
   commit-ahead consumes the pagefile, and hitting the limit fails allocations even with RAM free.
2. The census's "private" column must not be read as RAM. Report private WS beside it (priority 5 floor work).
3. Fewer concurrent claude processes is the dominant lever on this plane (WORKLOAD_CONTROLLED, priority 10).

## Open (not yet measured)
- Matched-workload comparison: the B stub bench on Windows (needs >= 4 GB Available locally) or a Windows host.
- Never-touched vs paged-out split of the 608 MB (needs QueryWorkingSetEx sampling over time, or ETW).
- Census "available 388 MB" vs OS "free 2.5-3.5 GB" minutes apart: reconcile which counter census reads.
