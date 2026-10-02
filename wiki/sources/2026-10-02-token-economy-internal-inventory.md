---
type: source
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-internal-inventory]
raw: raw/2026-10-02-token-economy-internal-inventory.md
kind: note
origin: read-only research subagent output, 2026-10-02 (committed @ 3b07419)
---

# Source — Token / context economy: internal inventory (2026-10-02)

Read-only inventory of every PP mechanism that measures, saves or spends tokens, with status
(LIVE / SHADOW / PLANNED / ABSENT / RETIRED), every measured number found, owners, and 15
contradictions between docs and code. Two rows were spot-checked at `3b07419`: RTK passes
non-Bash tools through (`modules/rtk-core/rtk-rewrite.js:106-110`), and the price table is
internally consistent (see [[token-economy-levers]]).

## Key takeaways

1. **Growth is tool output.** Tool results are 78.4 % of context growth: Read 56.5 %, PowerShell
   26.0 %, Grep 9.3 %, Agent 0.9 % (raw, "Where the tokens go").
2. **The floor is measured and partly movable.** Neutral cwd 91.9k: CLAUDE.md + rules 44.7k,
   skills 6.5k, hooks 4.8k, MCP 2.0k, plugins 1.4k; harness + tool schemas 34.5k not movable.
   Floor figures from other populations range 126k-192k and are not reconciled (raw,
   Contradiction 4).
3. **Much of the saving machinery is SHADOW or advisory.** Spawn admission SHADOW, model routing
   advisory, CO-08 cap advisory with 29-34 hot sessions, the daily cost advisory cannot fire at
   real output levels (raw, Mechanisms; Contradiction 10).
4. **RTK compresses only Bash**, while PowerShell is the mandated shell on this host (raw,
   Contradiction 3).
5. **Two stale docs:** the TCO gate's "70 % of 200k" vs the live 45 % of a 1M window; the
   token-shield SessionStart hook spawns a repo-relative path that fails outside PP (raw,
   Contradictions 2, 13).
6. **Ten levers with no owner program** (raw, "Owned vs open").

## Pages touched

[[token-economy-levers]], [[tool-output-at-source]], [[rtk-powershell-gap]],
[[sdk-probe-floor]], [[always-loaded-prefix-audit]].
