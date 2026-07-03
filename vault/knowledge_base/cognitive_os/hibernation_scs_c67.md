# SCS C67 — Transparent-Process-Hibernation (FASE A)

**Sealed:** 2026-07-03. **Mode:** ULTRA-PLAN scope + EXECUTION build (Owner-approved
at STOP #1). **Parent economy:** Cognitive OS (CO-07 hibernation / CO-08 cap / CO-10
guarantee-ledger). **Next free SCS:** C68.
**Commits:** `18f4a6d` governor, `8088b3e` executor+no-sid, `ed2443b` kclaude park +
G4 verify, `cdeb6cd` scanner + idle-granularity fix, `881ff58` orchestrator,
`<this>` docs + seal.

## What was sealed

Idle `claude.exe` panes are killed to reclaim RAM and **transparently rehydrated on
the next keystroke** by the `kclaude` wrapper. Extends CO-07 (context store) + CO-08
(hot detection) to the OS-process layer — never reimplements them.

**Empirical driver (measured, not estimated):** 56 live `claude.exe` = **12.2 GB
working set** (~217 MB WS / ~1 GB commit each) — 93% wrapper-launched. Only 2–3 are
ever in use.

| Component | Module | Behavior | CO-10 level |
|---|---|---|---|
| Governor | `process_governor.py` | `decide`/`plan`/`enrich_panes` — idle>15min + not-hot + anchored + wakeable + sid-known | WRAPPER (fail-safe keep) |
| Executor | `hibernate_runner.py` | CO-07 store+verify → arm wake flag → kill; rollback flag on kill-fail | WRAPPER |
| Rehydrate verify | `rehydration.py` | G4 identity gate: restored sid == resumed sid, else FAILED | pure (over CO-07 restore) |
| Wake mechanism | `kclaude.ps1` | sid beacon + `ReadKey` park on `claude-hibernate-<pid>.flag` → `--resume` | WRAPPER (the only act-tier) |
| Scanner | `scan_panes.ps1` | live `claude.exe` → raw records; read-only, never kills | — |
| Orchestrator | `run_hibernation.py` | scan→enrich→plan→hibernate; **DRY by default** | — |

## Never-hibernate invariants (fail-SAFE)
foreground · `/loop` · hot (turn <15min) · idle unknown · no anchor · no sid · not
wakeable. Worst case = a missed economy (idle pane stays alive), **never** a killed
pane that cannot rehydrate, **never** a lost session, **never** the wrong session
resumed (G4 identity gate). Fail-open absolute.

## Done-gate — empirical, honest
- `tools/test_hibernation.py` = **21/21 PASS, hermetic (2× re-runnable, exit 0)**.
- **Live smoke test:** 57 real panes scanned → **0 hibernate / 57 keep** (no beacons
  under un-patched wrappers) → fails safe end-to-end, exactly as designed.
- Baseline imports (scheduler/hibernation/acceptance) intact — sealed CO-family not
  regressed.
- **Bug caught + fixed during build (TDD value):** `enrich_panes` initially folded
  the CO-08 120-min hot set as a force-keep — wrong granularity, would keep every
  pane active in 2h. Dropped; `idle_min<15` in `decide()` is the correct guard.
  Guarded by `V-ENRICH-RESOLVES`.

## FASE B (host-limited, NOT built — honest boundary)
Wake-keystroke-as-message (ConPTY `CONIN$` limit), raw non-wrapped panes (reap
deferred), exact live-frame continuity (scrollback DOES persist; only the TUI frame
swaps). Full spec + Owner install steps: `vault/plans/process-hibernation-fase-a.md`.

## Install (ship-patches-Owner-installs, per STOP #1)
15 pwsh panes activate on `bin\kclaude.ps1` mirror-sync; 37 `kclaude.bat` panes via
repoint/converge to `bin\kclaude.cmd`; daemon = Scheduled Task (scan → run
`--live`). Start DRY, then `--live`. Steps in the plan doc §3.
