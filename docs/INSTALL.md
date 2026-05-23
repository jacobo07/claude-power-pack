# Programmatic Budget Layer — Install & Activation

> **First time on this host?** This doc covers the **second** layer —
> the RTK + JIT compression activation that minimises programmatic
> credit burn. Start with the **5-minute global install** at
> [`INSTALL-GLOBAL.md`](./INSTALL-GLOBAL.md), then come back here
> to opt into the budget layer.

Effective **2026-06-15**, Anthropic moves programmatic Claude usage
(Agent SDK, `claude -p`, GitHub Actions, third-party orchestrators)
off the subscription bucket and onto a separate metered credit at full
API rates:

| Tier   | Monthly programmatic credit |
|--------|-----------------------------|
| Pro    | $20                          |
| Max 5x | $100                         |
| Max 20x| $200                         |

These credits **do not roll over**. The Claude Power Pack ships four
components that compress what counts toward the credit. None of them
fabricates a number; every percentage you see in `verify_full_install`
is measured live on your host.

## Architecture (what compresses what)

| Component | What it compresses | Where the savings apply |
|-----------|--------------------|--------------------------|
| **RTK** (`~/.claude/bin/rtk.exe`) | Bash command **output** before it reaches the model context | Inside Claude Code's hook chain only (PreToolUse:Bash). Raw Agent SDK without CC: no RTK. |
| **JIT skeletal tier** (`tools/jit_skill_loader.py`) | Apollo skill **input** at injection time. In programmatic mode (`CLAUDE_PROGRAMMATIC=1` or non-TTY) every profiled module renders as pointer-only. | UserPromptSubmit hook — fires under `claude -p` and CC-wrapped SDK. Raw API: no JIT. |
| **Cache hints** (`vault/cache_hints/`) | Marks the **stable injected context** for the Anthropic API's prompt-cache feature. JIT emits hint sidecars; downstream Agent-SDK code reads them and sets `cache_control: ephemeral` on the corresponding blocks. | Wherever downstream code calls the API directly. |
| **Budget monitor** (`tools/budget_monitor.py`) | Nothing — it observes. Reads `~/.claude/budget.json` + telemetry, computes runway. | Anywhere. |

**Critical: these channels do NOT compose linearly.** RTK operates on
Bash output; JIT operates on prompt input; cache hints reduce per-call
input cost only on cache hits. `tools/verify_full_install.py` prints
the two probe numbers **side by side**, never multiplied, because their
byte streams are different and the product is not the per-session
savings.

## Activation order (5 steps)

### 1. Externalized pricing (already present)

`vault/pricing/anthropic_2026-05.json` ships with the repo. The budget
monitor refuses to compute a runway if `fetched_iso` is more than 30
days old (status: `stale-pricing`). When that happens, re-fetch from
`source_url` in the JSON header and update both `fetched_iso` and the
prices.

### 2. Seed your budget config

```powershell
copy docs\budget.example.json $env:USERPROFILE\.claude\budget.json
notepad $env:USERPROFILE\.claude\budget.json   # set tier + monthly_usd
```

Or, for a one-shot override, set `ANTHROPIC_PROGRAMMATIC_BUDGET_USD`
(env wins over file; the winning source is logged in every JSONL row).

### 3. Activate RTK output compression (Owner action)

The auto-mode classifier denies the agent self-persisting hooks. Run
once from a shell that has direct file access:

```powershell
copy modules\rtk-core\rtk-rewrite.js $env:USERPROFILE\.claude\hooks\
python tools\settings_merger.py register-pretool --node-script `
    $env:USERPROFILE\.claude\hooks\rtk-rewrite.js --matcher Bash --timeout 10
```

Then `/restart` your Claude Code session. Verify via:

```bash
python tools/verify_full_install.py
```

Section 2 should show `[OK] RTK hook: PreToolUse:Bash registered + script present`.

### 4. Activate JIT skeletal compression (Owner action)

```powershell
python tools\settings_merger.py register-userprompt `
    --py-interp <abs path to python.exe>
```

Then `/restart`. Verify Section 3 shows `[OK] JIT hook: ... + script
present`.

### 5. Confirm the impact on YOUR host

```bash
python tools/verify_full_install.py
python tools/measure_compression.py --programmatic --coordinated
python tools/budget_monitor.py
```

These are the only numbers that should drive your expectations. The
two compression percentages from `verify_full_install` apply to
different byte streams; the runway from `budget_monitor` applies only
once you have at least 3 telemetry rows in the trailing 7-day window
(sentinel `INSUFFICIENT_TELEMETRY` otherwise — never a fabricated runway).

## Honest reality contract

- If RTK has nothing to rewrite for a given command, savings = 0.
- If JIT injects a module with a `summary` profile that has no
  verbose anchors to drop, savings approach the structural floor of
  the skeletal renderer (e.g., apollo-kotlin at 53.5%; documented
  per-module floor in `tools/measure_compression.py`).
- Cache hits depend on the Anthropic API cache-control feature being
  respected by the calling code; without a downstream consumer, hint
  files are validated and ignored.
- The budget monitor never reports a runway it cannot compute. It
  prints `unconfigured`, `stale-pricing`, `INSUFFICIENT_TELEMETRY`, or
  `zero-burn-in-window` as honest sentinels.

## Sealed standard

The four requirements above (RTK active, JIT programmatic profiles,
prompt-cache hints, budget monitor) are codified in
`vault/standards/programmatic-budget-standard.md`. As of 2026-06-15
the standard becomes a mandatory gate for any Power-Pack-based system
that issues programmatic API calls.
