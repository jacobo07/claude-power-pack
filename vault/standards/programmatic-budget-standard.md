# Programmatic Budget Standard

**Status:** advisory until 2026-06-14T23:59:59Z · **mandatory from 2026-06-15T00:00:00Z**
**Sealed:** 2026-05-19 · **Repo:** claude-power-pack · **Cutover trigger:** Anthropic moves programmatic Claude usage (Agent SDK, `claude -p`, GitHub Actions, third-party orchestrators) off subscription buckets onto a separate metered credit at full API rates ($20 Pro / $100 Max 5x / $200 Max 20x, no rollover).

## Scope

This standard governs any system **built on top of the Claude Power Pack** that issues programmatic Claude API calls — whether through `claude -p`, the Agent SDK, GitHub Actions runners, or third-party orchestrators that drive Claude headlessly.

It does **not** govern interactive Claude Code sessions; those continue under the subscription bucket and the existing Apollo retrofit (S+ Criteria, sealed 2026-05-18) remains the gate.

## The four requirements

A system in scope is **non-conformant** if any of the following is missing or unmeasured.

### 1. RTK Bash-output compression active

`~/.claude/bin/rtk.exe` present + sha-pinned per `vendor/rtk/UPSTREAM_REF.md`, registered as a `PreToolUse:Bash` hook so every Bash call this system issues through Claude Code's hook chain has its output compressed before reaching the model context. Verified per-host by `tools/verify_full_install.py` Section 2 returning `[OK]` and the side-by-side probe returning a real percentage on the canonical benchmark (`git log --stat -50`).

**Out-of-scope channel honesty:** RTK does not affect raw Agent SDK calls that bypass Claude Code's hook chain. Systems that drive the API directly must measure their own Bash-output compression separately or accept that RTK contributes zero on that channel.

### 2. JIT programmatic skeletal-tier active

`tools/jit_skill_loader.py` detects programmatic mode (`CLAUDE_PROGRAMMATIC=1` env or non-TTY stdin) and promotes every profiled module to the skeletal (pointer-only) renderer, regardless of `SKELETAL_MODULES` set membership. Verified by `tools/measure_compression.py --programmatic` exit 0 with the gate `≥60%` for modules with `full_tok ≥ 600` and per-module documented floors otherwise (e.g., `apollo-kotlin` at 50%, measured 53.5% from a 493-token SKILL.md hitting the frontmatter+pointer structural floor).

### 3. Prompt-cache hints emitted with a real consumer

When the JIT loader runs in programmatic mode, it writes sibling `vault/cache_hints/<module>_<tier>.json` files carrying `content_sha256` + Anthropic API `cache_control: ephemeral` directive. The in-repo consumer `tools/cache_hint_apply.py` validates each hint by re-rendering the source SKILL.md at the recorded tier and comparing hashes — stale hashes are flagged `[FAIL] stale-hash`, never silent. Downstream Agent-SDK code reads validated hints to set block-level cache control on API calls.

**Honesty constraint:** inside Claude Code's hook chain, prompt caching is Anthropic-controlled and the hint file does not influence it. The hint is for callers that own the API call directly.

### 4. Budget monitor running with externalized pricing

`tools/budget_monitor.py` reads:
- Owner-seeded `~/.claude/budget.json` (schema in `docs/budget.example.json`)
- Externalized pricing `vault/pricing/anthropic_2026-05.json` (refuses compute if `fetched_iso > 30d` old → `stale-pricing` sentinel)
- Real telemetry JSONL in `vault/telemetry/`

Precedence: env `ANTHROPIC_PROGRAMMATIC_BUDGET_USD` > file > `unconfigured` sentinel. Winning source is logged into every output row. Never fabricates a runway: `INSUFFICIENT_TELEMETRY` (n<3 rows), `zero-burn-in-window`, `unconfigured:*`, `stale-pricing:*d-old` are the documented sentinels.

## Measurement honesty

The standard explicitly **forbids composite multiplier marketing**. The two probes from `verify_full_install.py`:

- **Bash-output RTK compression** (measured on `git log --stat -50`)
- **Skill-injection JIT compression** (arithmetic mean across the live trigger-matrix modules in programmatic mode)

operate on **different byte streams** (Bash output vs API prompt input). Multiplying them does not yield combined per-session savings. Any system that prints a composite "X× multiplier" without an end-to-end session-token delta probe to back it is non-conformant.

Whatever the **real measured numbers** are on a given host, those are the numbers. On the 2026-05-19 reference host: RTK 68.3% (raw 13077 t → rtk 4147 t), JIT 79.7% average across 10 Apollo trigger modules. These are reproducible by re-running `tools/verify_full_install.py`. They are not aspirational targets; they are the floor expected from a correctly-wired host.

## Gate

`tools/verify_full_install.py` exits 0 when the three OS-side fundamentals (RTK binary + pricing freshness + telemetry directory) all pass. Advisories (missing budget config, unregistered hooks) never fail the gate — they instruct the Owner with the exact command to run.

Post-2026-06-15, any pull request adding a new programmatic call path must include a `tools/verify_full_install.py` exit-0 transcript in the PR description and may not pass review without it.

## Reference implementation

- `tools/budget_monitor.py` — runway tracker
- `tools/measure_compression.py --programmatic` — compression gate
- `tools/jit_skill_loader.py` — JIT loader with programmatic detection
- `tools/cache_hint_apply.py` — cache-hint consumer
- `tools/verify_full_install.py` — host audit + side-by-side probes
- `modules/rtk-core/rtk-rewrite.js` — RTK rewriter with adoption telemetry
- `vault/pricing/anthropic_2026-05.json` — externalized pricing with provenance
- `docs/budget.example.json` — budget.json schema reference
- `docs/INSTALL.md` — owner-facing activation guide
