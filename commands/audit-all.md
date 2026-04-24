---
name: audit-all
description: "Unified audit across all subsystems in the current repo — discovers manifests, scores each on edit-thrashing/drift/completion/env-mapping, emits summary + oracle delta."
allowed-tools:
  - Read
  - Bash
argument-hint: "[<N|id>]     — optional: drill into subsystem #N or by id"
---

# Unified Audit — /audit-all

Portable entry point for the Unified Audit Engine. Runs against **the current working directory** via the Power-Pack tooling (resolved by absolute path so it works in any repo Owner opens).

Pipeline (all inline, no sub-agents):
1. `lib/discover.js` — walk the repo for manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `mix.exs`, `plugin.yml`, `.powerpack`, `SKILL.md`, `CLAUDE.md`, ...) up to 3 levels deep.
2. `lib/score.js`    — for each subsystem, compute 0–100 on four benchmarks: edit-thrashing, drift, completion, env-mapping.
3. `tools/oracle_delta.py --json` — OVO Phase A delta overlay (non-fatal if absent).
4. `lib/report.js`   — render the summary table or a drill-down.

## Run

Summary (no argument):

!`node ~/.claude/skills/claude-power-pack/lib/audit_all.js --project .`

Drill-down (with `$ARGUMENTS` equal to a subsystem index like `2` or an id like `root`):

!`node ~/.claude/skills/claude-power-pack/lib/audit_all.js --project . $ARGUMENTS`

## Reading the output

- **STATUS** column thresholds: `GREEN` ≥ 90 · `YELLOW` 75–89 · `ORANGE` 50–74 · `RED` < 50.
- **OVERALL** is weighted: completion counts 2×, the other three 1×. Completion is the Reality-Contract signal — placeholders/stubs cap your grade.
- The `oracle_delta:` footer (summary mode only) names how many files changed/appeared/disappeared since the last OVO verdict. `0 changed / N new` on a dormant repo is expected.

## When to drill down

Pick any subsystem whose row isn't `GREEN`. A drill-down exposes the raw evidence for each benchmark:
- **Edit-Thrashing** — files with ≥ 5 commits in the last 14 days (re-editing the same files repeatedly).
- **Drift** — new runtime files in the last 14 days with **no consumer** inside the repo (producer-consumer gap — Mistake #38).
- **Completion** — Reality-Contract placeholder hits (`TODO:`, `FIXME:`, `HACK:`, `Coming Soon`, `raise NotImplementedError`, `@stub`, etc.).
- **Env Mapping** — for the declared stack, whether the required toolchain binaries resolve on `PATH`.

## Flags (pass via `$ARGUMENTS`)

- `--no-oracle` — skip the Python oracle probe (faster when OVO isn't installed or the cache is cold).
- `--project <path>` — audit a different root.
- `--json` — emit the raw bundle (useful for piping into reviewers or CI).

## Relationship to `/ovo-audit`

- `/audit-all` = **breadth-first** scoring of every subsystem. Goal: find the weakest link in one glance.
- `/ovo-audit` = **forensic depth** on a single delta with 5-advisor Council verdict + push gate.

Run `/audit-all` first to triage. Run `/ovo-audit` on a suspect subsystem once you've identified it.

## Exit summary (Claude: paste the table inline — do NOT let the UI collapse it)

**REQUIRED render contract.** After the script completes, emit these blocks in the response body so the Owner sees the per-subsystem `%` per benchmark at a glance without expanding anything:

1. **Headline line** — `Subsystems: N · GREEN: a · YELLOW: b · ORANGE: c · RED: d · oracle_delta: …`
2. **Full per-subsystem table** (copy verbatim from the script — keep the columns `ID / STACK / THRASH / DRIFT / COMPL / ENV / OVERALL / STATUS`). Fence as a code block so the UI does not fold it behind `+N lines (ctrl+o to expand)`.
3. **Worst subsystem** — one line: `id, overall%, weakest benchmark, top offender`.
4. **Next step** — one line recommending the exact drill-down command, e.g. `/audit-all 1` or `/ira 1` if the same subsystem should be re-scored against the investment axes.

If the script prints `oracle_delta: skipped (…)`, include the reason. If a subsystem is RED/ORANGE, name its two worst axes with %, not just the overall.
