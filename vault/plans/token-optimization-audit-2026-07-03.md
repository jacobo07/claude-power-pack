# Token Optimization -- Corpus Structural Audit

**Generated:** 2026-07-03 14:26  
**Sessions analyzed:** 633  
**Source:** `~/.claude/projects/*/*.jsonl` per-turn `message.usage` + `message.content` (measured, no estimates)  
**Corpus totals:** in=80,536,173 out=524,017,714 cache_rd=62,744,272,022 cache_cr=2,331,111,148 cacheR=96.3%  
**Plan:** Claude Max (flat rate) -- real levers are OUTPUT VOLUME + CACHE RATIO + CONTEXT EFFICIENCY, not $.

## A2 -- Output distribution (the dominant cost)

- Usage turns: **229,440**, total output **524,017,714**
- Output/turn: median **1,321.0**, mean **2,283**, p95 **7,192**, max **64,000**
- **40.9%** of all output is produced by the fattest 10% of turns

| Output | Date | Project | sid | Turns | Cache% |
|---|---|---|---|---|---|
| 13,406,341 | 2026-06-04 | C--Users-User--claude-skills-c | 3f8d60d4 | 7086 | 96.1% |
| 13,406,341 | 2026-06-04 | C--Users-User-Apps-mcp-video-a | 3f8d60d4 | 7086 | 96.1% |
| 11,633,588 | 2026-06-03 | C--Users-User-Desktop-Cursor-P | 43773144 | 5131 | 96.7% |
| 11,061,441 | 2026-06-06 | C--Users-User-Desktop-Cursor-P | b5293708 | 2838 | 93.3% |
| 10,885,758 | 2026-07-03 | C--Users-User-Desktop-Cursor-P | 8cce8060 | 5195 | 97.7% |
| 10,765,469 | 2026-07-03 | C--Users-User-Desktop-Cursor-P | 74c7668b | 1156 | 94.6% |
| 10,381,119 | 2026-06-06 | C--Users-User-Desktop-Cursor-P | 56b87206 | 6311 | 97.9% |
| 10,223,650 | 2026-06-30 | C--Users-User-Desktop-Cursor-P | 561659a1 | 1638 | 95.7% |

## A3 -- Cache ratio per repo (outlier hunt)

| Project | Sessions | Output | Cache% | Mean 1st-load |
|---|---|---|---|---|
| C--Users-User-Desktop-Cursor-Projects-TU | 121 | 170,903,638 | 96.8% | 57,476 |
| C--Users-User-Desktop-Cursor-Projects-Mi | 145 | 141,866,761 | 95.9% | 64,024 |
| C--Users-User-Desktop-Cursor-Projects-In | 48 | 59,793,626 | 96.5% | 61,406 |
| C--Users-User-Desktop-Cursor-Projects-GE | 122 | 33,945,253 | 95.0% | 50,039 |
| C--Users-User-Apps-mcp-video-analyzer | 35 | 33,542,035 | 95.6% | 65,840 |
| C--Users-User--claude-skills-claude-powe | 35 | 33,541,533 | 95.6% | 65,840 |
| C--Users-User-Desktop-Cursor-Projects-Vi | 9 | 16,136,057 | 97.2% | 48,474 |
| C--Users-User-Desktop-Cursor-Projects-Wi | 56 | 12,852,617 | 96.5% | 51,240 |
| C--Users-User-Desktop-Cursor-Projects-Co | 3 | 10,897,427 | 97.9% | 44,461 |
| C--Users-User-Desktop-Cursor-Projects-Co | 5 | 3,781,397 | 96.9% | 50,409 |
| C--Users-User-Desktop-Cursor-Projects-Vi | 3 | 1,412,183 | 96.1% | 62,533 |
| C--Users-User-Desktop-Cursor-Projects-In | 2 | 1,170,694 | 94.0% | 62,397 |
| C--Users-User-Desktop-Cursor-Projects-Cl | 1 | 937,187 | 94.9% | 46,283 |
| C--Users-kobig-Desktop-Cursor-Projects-T | 1 | 768,190 | 97.3% | 50,755 |
| C--Users-User-Desktop-Cursor-Projects-TU | 1 | 768,190 | 97.3% | 50,755 |

**No low-cache outliers.** Every repo with >500k output holds >=90% cache ratio. Cache is not the lever.

## A1 -- Initial context load + session shape

- First-turn load (system prompt + skills + CLAUDE.md, mostly cache-creation): mean **57,054**, median **59,008**, max **103,405**
- Turns/session: mean **362.5**, median **2**, **282** sessions over 40 turns

## A4 -- Inefficiency patterns

- Sessions re-reading a file >=3x: **188** (5,540 redundant re-reads total; note: re-read tool_results are cache-side, low $ but live-window churn)
- Sessions with >=3 FASE-1/Reality-Scan/PREFLIGHT markers (possible in-session duplication): **160**

| Project | sid | Markers | Turns |
|---|---|---|---|
| C--Users-User--claude-skills-c | 3f8d60d4 | 134 | 7086 |
| C--Users-User-Apps-mcp-video-a | 3f8d60d4 | 134 | 7086 |
| C--Users-User-Desktop-Cursor-P | 9afe4b9d | 123 | 548 |
| C--Users-User-Desktop-Cursor-P | cd4822bc | 85 | 3147 |
| C--Users-User-Desktop-Cursor-P | 17bb5353 | 65 | 2626 |
| C--Users-User-Desktop-Cursor-P | d1a01b2c | 65 | 1625 |
| C--Users-User-Desktop-Cursor-P | 34c75182 | 50 | 1912 |
| C--Users-User-Desktop-Cursor-P | b5293708 | 38 | 2838 |

## A5 -- Hour-of-day burn + parallel-session hypothesis

- Distinct (date,hour) buckets: **444**
- Of the top-20 output hours, **100%** had >=2 sessions active concurrently

| Hour (UTC) | Output | Concurrent sessions |
|---|---|---|
| 2026-05-31 21:00 | 6,602,350 | 4 |
| 2026-07-02 21:00 | 5,729,925 | 25 |
| 2026-06-23 11:00 | 5,280,500 | 23 |
| 2026-06-25 21:00 | 4,769,120 | 22 |
| 2026-06-26 14:00 | 4,739,439 | 23 |
| 2026-06-30 10:00 | 4,491,608 | 23 |
| 2026-06-29 10:00 | 4,387,396 | 17 |
| 2026-06-25 14:00 | 4,277,617 | 22 |
| 2026-06-24 15:00 | 4,245,635 | 17 |
| 2026-07-01 17:00 | 4,097,409 | 26 |

## A6 -- Context size vs output (is a big window buying value?)

| Fed context | Turns | Mean output | Median output |
|---|---|---|---|
| <60k (low) | 681 | 889 | 0 |
| 60-120k (mid) | 21,286 | 1,849 | 1,050.5 |
| >120k (high) | 207,473 | 2,333 | 1,361 |

## A2b -- Fat-tail classification (DECISIVE, `--sample-fat 40`)

The 40 fattest output turns classified on disk (repetition ratio + primary tool):

| Category | Turns | Output | Reducibility verdict |
|---|---|---|---|
| reasoning/report | 29 | 1,825,331 | **NOT** -- uniq_ratio 1.0, top_repeat 0-1 (dense, unique) |
| code/file-write | 9 | 562,140 | **NOT** -- real `Write` deliverables (uniq 0.89-0.98) |
| mixed/tool-call | 2 | 128,000 | **NOT** -- PowerShell/Read tool calls |
| repetitive/dataset | 0 | 0 | (none found -- no boilerplate in the tail) |

Many turns sit at exactly 64,000 output (the max-tokens ceiling), concentrated
in a few Cursor-Projects sids. Every one is non-repetitive. **The output fat
tail is genuine content, not strippable boilerplate.**

## CONCLUSION -- no quality-safe high-ROI token fix exists

Evidence-backed negative result (the correct answer per the reality contract:
"si un patron no tiene ROI medible -> ignorar"):

1. **Input side is saturated.** 96.3% cache, zero low-cache repos, first-load
   already under the 40k-char CLAUDE.md firewall. Cache (CATEGORIA C) is a
   **dead lever**.
2. **Output side is the dominant cost (6.5x input) but not reducible.** The fat
   tail (40.9% of output) is dense/unique reasoning + real file writes. Cutting
   it sacrifices output quality -- explicitly forbidden.
3. **The real burn driver is behavioral, not code.** A5: peak hours run 17-26
   concurrent panes. Already targeted by PM-04 Budget Auction (shipped). The
   lever is session discipline, not a token-format fix.
4. **Only surviving quality-safe lever (modest):** A1 first-load ~57k, driven by
   the global CLAUDE.md + per-prompt JIT skill injection (13,396 B). Input-side,
   cached, low marginal cost. Owner-owned decision (which CLAUDE.md sections are
   redundant); HR-001 forbids auto-editing global config.

**Recommendation:** do NOT implement speculative output/cache "optimizations."
The system is already near-optimal on the levers that don't cost quality. The
audit's value is proving that with numbers.

---
*Generated by tools/token_corpus_audit.py -- FASE -1 corpus audit.*
