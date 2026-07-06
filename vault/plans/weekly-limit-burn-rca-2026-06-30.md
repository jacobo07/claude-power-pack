# Weekly-Limit Burn — Forensic RCA (2026-06-30)

> Status: **DIAGNOSIS — STOP #1 (awaiting Owner confirmation of root cause)**
> Source: per-turn `message.usage` from `~/.claude/projects/*/*.jsonl`, bucketed
> by ACTUAL turn timestamp (not session last-ts). 639 transcripts, 16,476 turns
> in the 48h window (2026-06-28 11:01Z → 2026-06-30 11:01Z). Zero estimates.

## BURN RATE FORENSIC REPORT

| Metric | Value |
|---|---|
| Output tokens, last 48h | **49,185,850** |
| Output/day, last 48h | **24,592,925** |
| Output/day, June average (29 active days) | 13,572,180 |
| **Overconsumption factor** | **1.81× the June average** |
| Cache ratio, 48h | 95.8% |
| Cache ratio, June / lifetime | 96.4% / 96.4% |
| ULTRA-PLAN prompts in THIS PP session (48h) | ~0 (PP = 0.5M out = **~1%** of burn) |

### By day (per-turn)
- 2026-06-28: out **21.76M** (cacheR 95.3%)
- 2026-06-29: out **22.69M** (cacheR 96.6%)
- 2026-06-30: out 4.74M partial (cacheR 93.9%)

→ Burn was **front-loaded and sustained**, not a single spike. Two back-to-back
full days at ~22M output each. Peak hours sustained 2.5–2.9M output/hour
(06-28 18:00–23:00), and several single hours hit 4.0–4.4M — a rate no single
session can produce → **multiple parallel panes**.

### By repo (48h, output)
| Output | Share | Repo |
|---|---|---|
| 23.67M | **48%** | TUA-X |
| 12.70M | **26%** | InfinityOps |
| 7.64M | 16% | Vibe-Coding-Projects-Sovereign |
| 3.18M | 6% | KobiiCraft |
| 0.90M | 2% | GEO-audit |
| 0.53M | **1%** | claude-power-pack (THIS session family) |

**TUA-X + InfinityOps = 74% of the entire 48h burn.**

### Top sessions (48h, output / turns / out-per-turn)
- 74c7668b (TUA-X): 6.97M / 699 turns / **9,974 out/turn** — 35 `EXECUTION MODE` prompts
- 9afe4b9d (TUA-X): 4.57M / 548 turns / 8,332 out/turn — 51 `FASE/MODE` prompts
- f1acb1ec (InfinityOps): 2.72M / 1,202 turns — 12 prompts, 3 `ULTRA-PLAN` + 10 `EXECUTION MODE`, all with `git push`
- 8cce8060 (TUA-X): 2.69M / 970 turns — 32 `EXECUTION MODE` + `DONE-GATE`
- 561659a1 (TUA-X): 1.48M / 217 turns / 6,449 out/turn — 7 `EXECUTION MODE`

## ROOT-CAUSE HYPOTHESIS (with evidence)

**The driver is high-volume large structured prompts — `EXECUTION MODE` /
`ULTRA-PLAN` / `FASE` / `DONE-GATE`, each 8k–18k chars — fired consecutively at
~40-minute cadence, each spawning a full agentic sprint (multi-FASE +
implementation + tests×3 + git push).**

- Measured cost per structured prompt: 74c7668b = 6.97M ÷ 36 prompts ≈ **194k
  output tokens per EXECUTION MODE cycle**; f1acb1ec ≈ 227k; 8cce8060 ≈ 81k.
  Each big prompt ≈ **80k–230k output**, because each one runs a whole sprint.
- 242 turns >8k output in 74c7668b alone; 211 in 9afe4b9d. The output is in the
  agentic loop (read→edit→test→push), ~19 assistant turns per human prompt.
- **Compounded by parallel panes**: overlapping session timestamps in peak hours
  (TUA-X 74c7668b + 8cce8060 + InfinityOps f1acb1ec all live 06-28 15:00–21:00)
  push the hourly rate above single-session ceilings.

### What the data RULES OUT
- **NOT a cache break.** 48h cache ratio 95.8% ≈ lifetime 96.4%. Context reuse is
  healthy; the burn is raw OUTPUT volume, not regenerated context. → Plan R4 is
  not the cause.
- **NOT this PP / ULTRA-PLAN session.** The prompt's framing ("this session's
  ULTRA-PLAN prompts caused the burn") is **disproven**: PP = ~1% of the 48h
  output. The *mechanism* (heavy structured prompts → ~200k output each) is real
  and confirmed — but it lives in **TUA-X (48%) and InfinityOps (26%)**, where
  `EXECUTION MODE` prompts were fired in long consecutive runs across multiple
  panes. The single biggest lever is those two repos, not this one.

### Honest scope of the "74% weekly limit" number
I have per-turn output tokens (the dominant cost driver), not Anthropic's exact
Max weekly-limit weighting. The defensible statement: **49.2M output in 48h at
1.81× the June daily rate, front-loaded into two consecutive days** — enough to
consume the bulk of a weekly allowance in 2 days even before input/weighting.
