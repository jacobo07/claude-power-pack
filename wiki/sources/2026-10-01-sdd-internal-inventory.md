---
type: source
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-sdd-internal-inventory]
raw: raw/2026-10-01-sdd-internal-inventory.md
kind: note
origin: read-only audit subagent, 2026-10-01, ~69 tool calls; repo @ e0f541f
---

# SDD-OS internal inventory (audit, 2026-10-01)

A subagent's read-only audit of SDD-OS in this repo, with file:line evidence, and a re-check of each
root cause in `SDD_OS_REALITY_REPORT.md` (2026-07-26). Feeds [[sdd-os-gap-analysis]] and [[sdd-os]].

## What I re-verified myself

- `spec_binding.find_bound_spec` reads only `covers`, and `pre_exec_gate.evaluate` returns
  `proceed` on any binding: read the code, then reproduced with `wiki/tools/sdd_probe.py`.
- Tier classification is a keyword match with T1 as the default: reproduced with the probe.
- "Not permitted" is injected text (`pre_exec_gate.py:377-381`), and `activation.py:140` swallows
  exceptions: read.

## Taken from the audit without re-checking

- Test results: `test_sdd_os.py` 14/14 and `test_sdd_os_activation.py` 9/9 pass.
- 4,097 throttle records (2026-07-26 to 2026-10-01). Of these, 47% were the T1 inline mini-spec,
  25% told the agent a T2/T3 task had no spec, and 28% reported a bound spec. These count
  injections, not compliance.
- Real specs: 33 in `vault/specs`; 25 declare `covers`, none use AC-NNN ids, none have a
  regression-risk heading.
- `intent_verified` has no hook. `TIER_OQS_FLOOR` and `check_drift` have no production caller.
- The slash commands are missing from `~/.claude/commands`, and `.specify/` was never filled in.

## Reality Report root causes, as of 2026-10-01

| root cause | status |
|---|---|
| RC-1 the agent's instructions never mention SDD-OS | fixed |
| RC-2 any spec-shaped file satisfies the gate | fixed on the SDD-OS path; still true for the old `check_spec_gate` |
| RC-3 advisory, capped, generates nothing | partly fixed (fires reliably; still advisory, writes nothing) |
| RC-4 no repo bootstrap, no spec upkeep | partly fixed (scaffold via the CLI; drift check is an mtime heuristic, CLI-only) |
