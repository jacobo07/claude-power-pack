# Liveness Ledger -- post-ship verdict (D1)

Generated 2026-07-10T17:26:21.585094+00:00 | 5 components | 4 LIVE, 1 non-LIVE (1 silent, 0 drifted, 0 orphaned, 0 unknown).

Verdict class: LIVE = recent end-to-end evidence; WIRED-BUT-SILENT = wired but no recent evidence (idle / broken producer / producer-without-consumer); DRIFTED = repo vs ~/.claude/hooks hash mismatch; ORPHANED = live artifact with no repo source.

| Component | Surface | Verdict | Evidence |
|---|---|---|---|
| `pm-03-bus` | pm-bus | **WIRED-BUT-SILENT** | 3 producer file(s); consumer is the SessionStart hub read but emits no 'pm03_consume' signal -- consumption unmeasured |
| `fd-07-flywheel` | stop-chain | **LIVE** | 109 signals, freshest 0.0h ago (<= 36h) |
| `fios-token-irr` | stop-chain | **LIVE** | 65 signals, freshest 0.0h ago (<= 36h) |
| `hook-dispatcher` | hooks-dir | **LIVE** | in sync (sha256 7afbbb78659e) |
| `kclaude-preflight` | kclaude | **LIVE** | SESSION_ZERO_2026-07-10T162015Z.md 1.1h ago (<= 36h) |

Non-LIVE rows are the ship->silence gap made visible. A row here is the authoritative liveness fact -- not a lesson rediscovered sessions later.
