# CCR v4 stage 3 -- A3 evidence: Work-Class PGO and held-out calibration

Every number is measured on the **Linux plane GEX44, host 2.1.296**, from the projected pack (`/home/kobii/missions/ccr-s3-data/pack`), and is reproducible with:

    D=/home/kobii/missions/ccr-s3-data/pack
    python3 tools/ccr_pgo.py build --by-class --missions $D/missions.json --pack $D --root . \
      --v1 $D/v1/attempt1-stream-r1-OFF.jsonl $D/v1/stream-r*.jsonl \
      --out vault/programs/ccr/stage3/a3/pgo-classes.json --corpus vault/programs/ccr/stage3/a3/corpus.json

The projections hold usage only, with no text, so nothing below is derived from transcript text. Classes come from packet text in this clone. `route` is null on all 433 mission records, so no route text was available.

## Verdict

**Gate NOT MET for any class.** The gate is P50 APE < 25 % and P80 coverage >= 70 % on n >= 8 held-out.
- `bounded-code` is the only class with enough held-out sessions (n = 24). Coverage passes (70.8 %), but P50 APE is 46.4 %, which fails.
- `long-textual` meets both accuracy bars (APE 21.7 %, coverage 85.7 %), but it has only **n = 7** held-out sessions, one short of the 8 required. It fails on n alone, and it ships at LOW confidence.
- `lookup` and `generic` are LOW (n held-out 3).
- `multimodal` has **n = 0** in the Work Unit corpus. It is not a class yet, and any multimodal packet falls to the generic cold start at LOW confidence.

No class, rule, quantile or split was adjusted after the held-out results were seen. The classifier rules were written from packet titles before any per-class cost was computed.

## 1. Corpus

- **Work Unit sessions: 119.** These are mission records whose packet resolves under `vault/programs/` in this clone and whose owner session is projected. 433 records in total: 219 have no packet path, 81 have a packet path missing from this clone, and 14 have no projected owner session. Every usable mission had exactly one owner.
- **V1 canary streams: 6.** These are `attempt1-stream-r1-OFF` and `stream-r1..r5`, all with the obligation "v1 canary: predecessor lookup".
- **Total: 125 sessions, 165,297,659 processed tokens.** Models: claude-sonnet-5-5 119, claude-haiku-5-5 6 (the V1 runs).

Per-session facts are in `vault/programs/ccr/stage3/a3/corpus.json`:
- calls: distinct `mid` with usage
- floor: the first call's context
- slope: (last ctx - first ctx) / (calls - 1)
- processed: input + cache_read + cache_creation + output, deduped by `mid`, taking the largest streamed output
- weighted: input 1, cache_read 0.1, cache_creation 1.25, output 5
- image share: tool results that carry images
- model

Image share is 0.0 for all 125 sessions. The parser does count images: a test confirms it, and a non-corpus session `0bdd6fe2` measures 0.303. The 52 projected sessions that carry images are receipt sessions, or missions whose packet is not in this clone.

## 2. Taxonomy (deterministic, `ccr_pgo.CLASS_RULES`, first match wins)

| class | scope | rule (regex, lower-cased) | n in corpus |
|---|---|---|---:|
| multimodal | whole text | screenshot, .png, vision, visual qa/check/diff, playwright, in-browser | 0 |
| lookup | title | look up / lookup, predecessor, `canary:` | 9 (3 apr-canary + 6 V1) |
| long-textual | title | knowledge, handoff, decisions, dossier, census, autopsy, certif, judge, evidence, report, frontier | 25 |
| bounded-code | whole text | test(s), test_, .py, .js, drill, fixture, implement, build, wire | 80 |
| generic (cold start) | -- | nothing matched | 11 |

The data supports three fitted classes plus the generic cold start. `multimodal` stays as a declared rule with no model.

## 3. Per-class fit and held-out calibration

Method:
- Each class is sorted by mission `created` (V1: the first stream `ts`).
- The earliest round(0.7 n) sessions are train and the rest are held-out.
- The model is the empirical P50/P80 of train `processed`.
- **The shipped model is exactly the train fit that was judged.**
- APE is |P50 - actual| / actual, reported as its median.
- Bias is the median of (P50 - actual) / actual. Negative means the forecast is under the actual cost.
- Coverage is the share of held-out sessions with actual <= P80.

| class | n total | n train | n held-out | P50 forecast | P80 forecast | **P50 APE** | **bias** | **P80 coverage** | confidence | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| bounded-code | 80 | 56 | 24 | 1,034,453 | 2,066,060 | 46.4 % | -21.3 % | 70.8 % | MEDIUM | FAIL (APE) |
| long-textual | 25 | 18 | 7 | 872,628 | 1,662,484 | 21.7 % | -18.3 % | 85.7 % | LOW | FAIL (n 7 < 8) |
| lookup | 9 | 6 | 3 | 126,075 | 312,365 | 73.1 % | -73.1 % | 33.3 % | LOW | FAIL (n, APE, cov) |
| generic (unmatched packets) | 11 | 8 | 3 | 318,475 | 1,198,061 | 78.5 % | -78.5 % | 33.3 % | LOW | FAIL |
| multimodal | 0 | 0 | 0 | -- | -- | -- | -- | -- | LOW (cold start) | n = 0 |
| generic cold start (all classes' train, judged on all held-out) | 125 | 88 | 37 | 885,954 | 1,770,387 | 41.8 % | -27.6 % | 73.0 % | -- | -- |

**Leave-one-out**, reported beside the time split for classes under 12 sessions. It is never used for confidence or the gate, and it does use later sessions to forecast earlier ones:

| class | n | P50 APE | bias | P80 coverage |
|---|---:|---:|---:|---:|
| lookup | 9 | 73.2 % | +28.0 % | 66.7 % |
| generic | 11 | 64.8 % | -22.1 % | 72.7 % |

Every class's held-out bias is negative: later sessions cost more than earlier ones of the same class. This is drift over time (the latest cohort is cdc C5b..C12, tennis-rf D1..D4 and APR7), and a time-stable class quantile cannot absorb it.

## 4. V1 task re-forecast ("v1 canary: predecessor lookup", 4-6 calls)

The original contract (`stage2/v1/contract-r2-CCR.json`) priced this task as `bounded-code-worker` with a Madzia prior: calls P50 28, P50 1,179,457, P80 2,164,496. A3's classifier now places it in **lookup**.

| run | arm | calls | actual processed | old P50 (x actual) | **pre-V1 lookup P50** (apr canaries only, n 3) | in pre-V1 P80 132,581 | shipped lookup P50 126,075 | in shipped P80 312,365 |
|---|---|---:|---:|---:|---:|---|---:|---|
| attempt1-r1 | OFF | 6 | 457,404 | 2.6x | 93,545 (-79.5 %) | no | -72.4 % (train) | no |
| r1 | OFF | 4 | 312,365 | 3.8x | -70.1 % | no | -59.6 % (train) | yes |
| r2 | CCR | 4 | 89,475 | **13.2x** | **+4.5 %** | yes | +40.9 % (train) | yes |
| r3 | OFF | 6 | 468,726 | 2.5x | -80.0 % | no | -73.1 % | no |
| r4 | CCR | 4 | 81,674 | **14.4x** | **+14.5 %** | yes | +54.4 % | yes |
| r5 | OFF | 6 | 470,607 | 2.5x | -80.1 % | no | -73.2 % | no |

Reading:
- The **pre-V1 lookup model** is fit only on what existed before the canary, so it is fully out of sample. It removes the 13.2-14.4x over-forecast on the CCR arm: P50 APE 9.5 % on the 2 CCR runs, with both inside P80.
- The OFF arm of the same task costs 3.5-5.7x more than the CCR arm (312-471k vs 82-89k). One lookup quantile cannot cover both arms: OFF coverage is 0/4. Arm (or whether CCR is on) is a cost driver that the class does not encode.
- Across all 6 runs, the pre-V1 model scores P50 APE 74.8 %, bias -74.8 %, coverage 33.3 %.
- Adding an arm feature is a candidate for a later unit. It was not done here, because the only evidence for it is these held-out runs.

## 5. Tool (`tools/ccr_pgo.py`) and tests

- `build --by-class --missions --pack --root [--v1 ...] --out pgo-classes.json [--corpus]` writes the per-class models, the held-out metrics, LOO for tiny classes, confidence, `gate_pass` and the rules.
- `contract --pgo pgo-classes.json --obligation T --image F [--cap N]` works as follows:
  - It classifies obligation plus image text and picks that class model.
  - If a class is unknown or has no model, it uses the generic cold start at LOW.
  - It emits `confidence`.
  - Confidence is LOW when n held-out < 8 or P80 coverage < 70 %. It is HIGH only when the full gate is met, and MEDIUM otherwise.
  - **A LOW contract never hard-rejects.** A SPLIT/DEFLATE outcome becomes `ADMIT_LOW_CONFIDENCE` with `advisory` set to the would-be verdict. `gsd_mission` enforce mode refuses only SPLIT/DEFLATE, so LOW admits.
  - A single-class `pgo.json` behaves exactly as before.
- `python3 tools/test_ccr_pgo.py`: **CCRPGO_PASS=16/16**. That is 7 existing tests plus 9 new A3 tests:
  - projection dedup by mid
  - deterministic classifier
  - time split with no leak
  - LOW on poor coverage
  - LOW on thin held-out
  - HIGH when the gate is met
  - LOW never hard-rejects
  - unknown -> generic LOW
  - lookup not priced as code
- `python3 tools/test_gsd_mission_ccr_contract.py`: 5 passed, 0 failed.
- Not wired: `gsd_mission._ccr_contract` still loads `<pgo dir>/<ccr_class>.json`. Pointing it at `pgo-classes.json` is a follow-up and is not part of this unit.
