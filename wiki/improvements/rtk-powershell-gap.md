---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-internal-inventory]
status: IDEA
effort: M
graduated_to:
---

# RTK does not compress PowerShell

## Problem

RTK (LIVE) rewrites Bash commands to compress their output; it passes every other tool through
(`modules/rtk-core/rtk-rewrite.js:106-110` @ `3b07419`), because a POSIX rewrite is a PowerShell
parse error. On this host the global CLAUDE.md mandates PowerShell for git, python, node and npm,
and PowerShell output is 25-26 % of context growth
([[2026-10-02-token-economy-internal-inventory]]). The only RTK measurement is 80 % on one Bash
command (`git log --stat -50`).

Doc drift: the global CLAUDE.md says "RTK proxy must be active"; that is true and covers only the
minority shell.

## Bound

Unknown. CMV dropped a PowerShell tee as ≤ 4.5 % of tool rent; growth share and rent share of one
technique are different measures ([[token-economy-levers]], Disagreements).

## Proposed steps

1. Sample 7 d of PowerShell tool results: which commands produce the largest outputs (git log,
   pytest, python scripts).
2. If a few commands dominate, wrap them PowerShell-natively (e.g. invoke `rtk.exe` with
   PowerShell call syntax) rather than porting the Bash rewriter.
3. Measure on real calls before claiming a ratio.

Related: [[tool-output-at-source]].
