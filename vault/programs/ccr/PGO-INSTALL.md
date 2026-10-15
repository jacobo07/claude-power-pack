# PGO install runbook (CCR X2 step 5)

Put the Stage 3 PGO model files where the runtime reads them, prove the readers read them, and know how to hold DEFLATE.
Owner of the code: `tools/ccr_pgo.py` (`install`, `verify`). Gate: `python -I tools/test_ccr_pgo_install.py` prints `PGOINST_PASS=14/14`.

## What is installed

Destination: `~/.claude/ccr/state/pgo/` (`C:\Users\User\.claude\ccr\state\pgo\`), or the directory in `CPP_CCR_PGO_DIR` when set.

| File | Committed source | Reader |
|---|---|---|
| `pgo-classes.json` | `vault/programs/ccr/stage3/a3/pgo-classes.json` | `tools/gsd_mission.py` `_ccr_contract` classifies the Work Unit packet from it (work class + confidence); `deflate_unit` then declares the unit |
| `bounded-code-worker.breakeven.json` | `vault/programs/ccr/stage3/a4/pgo/bounded-code-worker.breakeven.json` | `mods/cpp-cognitive-runtime/hooks/register.ts` reads `<state>/pgo/<unit class>.breakeven.json` for a declared unit; `policy.ts` `parseBreakevenModel` accepts it |
| `read-only-reviewer.breakeven.json` | `vault/programs/ccr/stage3/a4/pgo/read-only-reviewer.breakeven.json` | same reader, unit class `read-only-reviewer` |

## Install and verify

Run from the repository root.

```powershell
python tools/ccr_pgo.py verify      # BEFORE: exit 1, verdict UNFORECAST while the directory is absent
python tools/ccr_pgo.py install     # validates every source, writes atomically, reads each file back, prints sha256 per file
python tools/ccr_pgo.py verify      # AFTER: exit 0
```

`install` validates every source first with the rule the mod uses (`validate_classes`, `validate_breakeven`, mirrored from
`policy.ts` `parseBreakevenModel`). One invalid source aborts the whole install with nothing written. A destination file that
already exists with different bytes is refused (exit 1, bytes untouched) unless `--force`; `--force` records the previous
sha256 in the output. Identical bytes are an idempotent success. `--receipt FILE` also writes the printed JSON to FILE.

`verify` drives the REAL readers (`gsd_mission._ccr_contract`, then `deflate_unit` with DEFLATE on and with the off hold)
against the directory, with all mission-state variables pointed at a temp directory, so it writes no real state. It exits 0
only when the packet is classified from the installed file, the off hold declares nothing, and no break-even file is invalid.
`breakeven_ok: null` means no break-even file is present (unknown, not a pass).

## What the files change

- A bounded-code Work Unit slim launch is classified at confidence MEDIUM or better, so `deflate_unit` declares the unit
  `bounded-code-worker` (a declaration file in the mission store, its path in `CCR_WORK_UNIT`). DEFLATE is on by default once `pgo-classes.json` exists.
- A LOW-confidence class (lookup, long-textual, generic) only records `would_deflate`; nothing is declared.
- The break-even files wire the observe-only rotate advice. Nothing rotates a session.

## Holds (two forms, both tested)

1. Per process: set `CPP_CCR_DEFLATE` to `off` (also accepted: `0`, `false`) before a launch.
   ```powershell
   $env:CPP_CCR_DEFLATE = 'off'
   ```
   With it set, `deflate_unit` declares nothing and records nothing (V-PGOINST-HOLD-OFF). A variable set in an interactive
   session does NOT reach processes started by the Task Scheduler (the sweep). Making it persistent per user is an Owner
   decision and is not applied here.
2. Shared by every launcher: remove `pgo-classes.json` from the state directory. The contract becomes UNFORECAST, no class is
   known, and `deflate_unit` returns `no_unit_class` with or without the environment variable (V-PGOINST-HOLD-BY-REMOVAL).

## Rollback

Delete exactly the three files by name, after comparing their sha256 with the install receipt
(`vault/programs/ccr/stage3/pgo-install-receipt.json`). Touch nothing else in the directory.

```powershell
$d = "$HOME\.claude\ccr\state\pgo"
Get-FileHash "$d\pgo-classes.json","$d\bounded-code-worker.breakeven.json","$d\read-only-reviewer.breakeven.json"   # compare with the receipt
Remove-Item "$d\pgo-classes.json","$d\bounded-code-worker.breakeven.json","$d\read-only-reviewer.breakeven.json"
```

## Owner step when the live write is refused (HR-001)

A write under `~/.claude/` can be refused by the classifier at tool level. Then the agent must not work around it. Run
these lines yourself from the repository root, then run `python tools/ccr_pgo.py verify` (expect exit 0).

```powershell
$repo = 'C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr-v5'   # or the main checkout once merged
$d = "$HOME\.claude\ccr\state\pgo"
New-Item -ItemType Directory -Force -Path $d | Out-Null
Copy-Item "$repo\vault\programs\ccr\stage3\a3\pgo-classes.json" "$d\pgo-classes.json"
Copy-Item "$repo\vault\programs\ccr\stage3\a4\pgo\bounded-code-worker.breakeven.json" "$d\bounded-code-worker.breakeven.json"
Copy-Item "$repo\vault\programs\ccr\stage3\a4\pgo\read-only-reviewer.breakeven.json" "$d\read-only-reviewer.breakeven.json"
Get-FileHash "$d\*.json"   # equals the sha256 of the three sources
```
