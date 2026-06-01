# Sprint 1 -- Owner Registration Steps (BL-TOOL-AUTO-001)

Sealed 2026-06-01. The Power Pack auto-mode classifier **hard-denies** writes to
`~/.claude/settings.json` and `~/.claude/agents/` (HR-001). The PP-internal
artifacts below are built, tested, and committed; these are the **one-time
Owner-side registration steps** that activate them. Each is copy-paste ready.

`<PP>` = `C:/Users/User/.claude/skills/claude-power-pack`

---

## 1. Stop hooks (fire-and-forget, end-of-turn)

Both scripts exist and were tested (`exit 0`, dispatch logged to
`%TEMP%/pp-stop-hooks.log`). They run a slow tool detached so the Stop event
never blocks:

| Script | Tool fired | PASO 0 timing |
|--------|-----------|---------------|
| `hooks/jit_correlate_stop.js` | `jit_ref_correlate.py` | 3.2 s -> detached |
| `hooks/session_snapshot_stop.js` | `session-snapshot.py` | >12 s -> detached |

Add to `~/.claude/settings.json` under `hooks.Stop` (create the array if
absent). **Back up settings.json first.**

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command",
            "command": "node \"C:/Users/User/.claude/skills/claude-power-pack/hooks/jit_correlate_stop.js\"" },
          { "type": "command",
            "command": "node \"C:/Users/User/.claude/skills/claude-power-pack/hooks/session_snapshot_stop.js\"" }
        ]
      }
    ]
  }
}
```

Activation requires `/restart` (hooks load once at session start).

---

## 2. Agent: pp-token-auditor

Spec lives at `vault/agents_specs/pp-token-auditor.md`. Agents cold-load, so a
new agent file does not dispatch until `/restart`.

```powershell
Copy-Item `
  "C:\Users\User\.claude\skills\claude-power-pack\vault\agents_specs\pp-token-auditor.md" `
  "C:\Users\User\.claude\agents\pp-token-auditor.md"
# then /restart
```

---

## 3. Mechanism-F daemons -- ALREADY INSTALLED

`tools/install_sprint1_daemons.py` was run this session; 4 tasks are `Ready`:

| Task | Schedule | Tool |
|------|----------|------|
| `PP-Vault-Summarize` | daily 02:00 | `vault_summarize.py --check` |
| `PP-Sovereign-Miner` | daily 03:00 | `sovereign_miner.py` |
| `PP-Miner-V2` | daily 03:30 | `miner_v2.py` |
| `PP-Normalize-Paths` | daily 04:00 | `normalize_paths.py --check` |

Verify / manage:
```powershell
Get-ScheduledTask -TaskName 'PP-*' | Select TaskName, State
# remove all:
python tools\install_sprint1_daemons.py --uninstall
```

---

## 4. SessionStart health checks -- ALREADY LIVE (no registration)

`compound_audit` + `drift_report` were wired into `hooks/session_start_hub.js`
(Mechanism A, in-hub per SCS C23 -- no new settings.json entry). They run
detached on every SessionStart and write evidence to:

- `vault/health/compound_audit.last.txt`
- `vault/health/drift_report.last.txt`

Active immediately; no Owner step required.
