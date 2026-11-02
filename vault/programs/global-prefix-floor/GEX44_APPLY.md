# GPF diet applied LIVE on GEX44 (2026-11-02 ~18:40 UTC, Owner "y")

Host kobicraft-gex44 (user kobii). Source: W1 diet a46ae9a3 (`vault/programs/ctx-rent-x/diet/`, branch gex44/gpf-run).

## Pre-checks
- Live `~/.claude/CLAUDE.md` and the 5 rules byte-equal the snapshot W1 measured (sha256 ef98fa5e..., d7dd9669..., 96545477...,
  81b53168..., 2ae141c9..., befb119e...). The apply script re-checked this with `cmp` and would abort on drift.
- Measured stubs pointed at `vault/programs/ctx-rent-x/diet/rules-archive/` "in the PP repo", but GEX44's PP checkout
  (feature/knowledge-acquisition 24d117e2) does not have it. The live stubs point instead at
  `~/.claude/knowledge_vault/claude-doctrine/rules-archive/<name>.md` (installed, never auto-loaded). The diet's own pointer
  `claude-doctrine/global-claudemd-archive.md` is installed as the full original. Bundle hashes: `gex44-apply/SHA256SUMS`.

## Applied
`~/.claude/CLAUDE.md` 25,206 -> 6,938 B; 5 rules -> 2-line stubs. Each file written as a temp file + mv, then `cmp`-verified.
Backup + SHA256SUMS: `/home/kobii/.claude/backups/gpf-apply-20261102T183952/`.
Revert (on GEX44): `B=~/.claude/backups/gpf-apply-20261102T183952; cp $B/CLAUDE.md ~/.claude/; for r in durable-exit-transaction effect-authority-across-transports generated-content-needs-an-evidence-gate python/testing common/code-review; do cp $B/rules/$r.md ~/.claude/rules/$r.md; done`

## Smoke (HR-2) and measurement -- driver gpf_floor_decomp.py @a46ae9a3, arm `full` rebuilt from live, haiku "reply OK"
| arm | call-1 | receipt |
|---|---|---|
| pre-apply (live original) | 113,785 / 113,776 | pre-1/2.json |
| post-apply (live diet) | 86,209 / 86,207, both replied `OK` | post-1/2.json |
| attribution: post-apply snapshot with the original 6 files restored IN THE ARM only | 99,991 / 99,997 | attr-orig*.json |

**Smoke: GREEN.** Sessions start on the live diet and answer.
**Diet-attributable saving: -13,786 tokens per call-1 (-13.8%), n=2/arm, spread <0.01%. MEASURED.**
The raw pre->post drop of -27,572 is NOT all the diet. About -13.8K came from some other change in live `~/.claude` between the
pre and post builds (~20 min apart, 26 claude processes on the host). It is unattributed, and the system+tools block was unchanged
(cc 36,367 vs 36,370). The pre-apply estimate of ~-21K (W1 -29.4K minus the repo CLAUDE.md) was wrong; -13.8K is the number.
Quality: not re-run live. W1 measured 6/6 on this exact diet (w1-quality-results.json).
Open: pre-existing dangling pointers on GEX44 that the diet did not introduce: `knowledge_vault/core/HARD-RULES-DIGEST.md`,
`core/anti-antipatterns.md`, `claude-doctrine/*-detail.md`.
