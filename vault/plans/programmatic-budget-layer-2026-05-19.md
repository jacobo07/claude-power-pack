# Programmatic Budget Layer — Execution Record

**Trigger:** Anthropic moves programmatic Claude usage off subscription bucket onto a separate metered credit at API rates from 2026-06-15.

**Scope:** any system built on the Claude Power Pack that issues programmatic Claude API calls (Agent SDK, claude -p, GitHub Actions, third-party orchestrators).

**Status:** sealed 2026-05-19. Five micro-commits landed atomically.

## PASOs executed

### P1 — Budget runway tracker
- `tools/budget_monitor.py` reads Owner-seeded `~/.claude/budget.json` + externalized `vault/pricing/anthropic_2026-05.json` (30-day staleness gate) + telemetry.
- Honest sentinels: `unconfigured`, `stale-pricing`, `INSUFFICIENT_TELEMETRY`, `zero-burn-in-window`. Never fabricates a runway.
- Env `ANTHROPIC_PROGRAMMATIC_BUDGET_USD` > file > unconfigured; winning source logged into each output row.
- Verified live: env-override probe produced runway 2187 days on 44 trailing-7d telemetry rows; unconfigured probe correctly emitted sentinel.

### P2 — Programmatic mode in JIT + measure gate
- `jit_skill_loader.py` `_is_programmatic()` detects `CLAUDE_PROGRAMMATIC=1` env or non-TTY stdin; promotes every profiled module to skeletal renderer in programmatic mode.
- `measure_compression.py --programmatic` gate at >=60%; documented per-module floor for small files (apollo-kotlin 50% floor, real measured 53.5% — 493-token SKILL.md hits frontmatter+pointer structural floor).
- 9 modules >=73-88% reduction, 1 at 53.5% explicitly tagged `[OK-smallfile]`. Interactive gate unchanged (no regression).

### P3 + P3b — Cache hints + RTK adoption telemetry
- JIT in programmatic mode writes `vault/cache_hints/<module>_<tier>.json` with content sha256 + Anthropic `cache_control: ephemeral`.
- In-repo consumer `tools/cache_hint_apply.py` validates each hint by re-rendering source at recorded tier and comparing hashes. Stale hashes flagged with reason. Closed Mistake #38 (no write-only ghost output).
- `modules/rtk-core/rtk-rewrite.js` appends adoption rows to `vault/telemetry/rtk_<sid>.jsonl` per Bash call. Honest adoption-only schema; no fabricated per-call savings (unmeasurable at PreToolUse time).

### P4 — Host audit + side-by-side probes
- `tools/verify_full_install.py` audits 7 sections, exit 0 if 3 critical fundamentals pass.
- Two probe percentages printed side-by-side, NEVER multiplied (Gap 9). Reference host: 68.3% RTK Bash-output / 79.7% JIT skill-injection mean (n=10 modules).
- Explicit non-composition warning in stdout.
- `docs/INSTALL.md` is the owner-facing 5-step activation guide.

### P5 — Sealed standard + lesson
- `vault/standards/programmatic-budget-standard.md` codifies the four requirements; advisory until 2026-06-14T23:59:59Z, mandatory thereafter.
- Global apex standard updated; global<->pp mirror byte-identical post-commit.
- Addendum 11 in `vault/knowledge_base/session_lessons.md` records the forensic decisions (multiplier honesty, structural floor, consumer-closure, adoption-only telemetry, sibling concurrent edits, anti-thrash recovery).

## DONE-GATE evidence

- `python tools/budget_monitor.py` exit 0 (sentinel or real number, never fabricated)
- `python tools/measure_compression.py --programmatic` exit 0 (9 [OK] + 1 [OK-smallfile])
- `python tools/measure_compression.py` exit 0 (interactive baseline — no regression)
- `python tools/cache_hint_apply.py` exit 0 (3 valid hints loaded; staleness gate verified by hash drift probe)
- `python tools/verify_full_install.py` exit 0 (6 [OK] + 1 [ADVISORY] — Owner-seeded budget.json absent)
- `git rev-list origin/feat/rtk-compressor-fusion..HEAD` drops to 0 after the P5 push

## Reality contract

Every number in the standard and in `verify_full_install.py` output is measured live on the host at run time. No constant marketing multiplier. No declared-not-measured percentage. Sentinels replace fabricated values everywhere it would otherwise be tempting to inflate.
