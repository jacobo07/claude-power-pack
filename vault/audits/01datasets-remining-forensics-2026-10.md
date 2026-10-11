# 01_Datasets re-mining forensics (cognitive-reuse W0, 2026-10-11)

Question: which TUA-X session(s) mined `01_Datasets` again, how much was redundant, and why
could nothing stop it. Method: read-only sweep of Claude transcripts; no estimates.

## Command (reproducible)

`python -I vault/audits/01datasets-remining-forensics-2026-10.sweep.py` (150 s deadline, read-only).
Search space: `~/.claude/projects/*` dirs matching `TUA-X|wt-creative|wt-cw|Apps--wt` (15 dirs),
all `*.jsonl` recursively **including `subagents/`**. A hit = an assistant `tool_use` whose input
contains `01_Datasets`. First pass without `subagents/` MISSED the ads agent: top-level transcripts
alone show it as one `Agent` call.

`tokens` = sum of `usage` input + output + cache_creation over the transcript. It counts cache
creation every turn, so it is an upper-bound activity gauge, NOT billing. Compare rows, do not price them.

## Result: 11 transcripts (7 sessions + 4 subagents) touched the corpus

| transcript | window (UTC) | calls | distinct paths | on `extracted\Ads` | paths already seen earlier | note |
|---|---|---|---|---|---|---|
| 4ce76b21 | 2026-08-05 | 1 | 0 | 0 | 0 | CEIS mission; only a memory write cites the corpus |
| e39065d6 | 08-16..17 | 25 | 12 | 0 | 0 | located/merged 4 copies, YouTube harvest |
| 2b8a8bfc | 09-30 | 8 | 3 | 0 | 0 | llm-wiki build, coverage measure |
| 61c014d6 | 09-30..10-01 | 19 | 13 | 0 | 1 | failure-evidence intake |
| 61c014d6/sub d71c1b7a | 10-01 | 18 | 10 | 0 | 0 | reads 9 failure transcripts in full |
| 61c014d6/sub 3e45cbc9 | 10-01 | 18 | 10 | 0 | 1 | same, batch B |
| 681ad0fb | 10-02 | 10 | 6 | 0 | 0 | YouTube topic-evidence FTS5 index |
| dbbceb56 | 10-09 | 13 | 2 | 0 | 0 | reachability audit |
| dbbceb56/sub 9cf38a0f | 10-09 | 10 | 4 | 0 | 0 | read-only knowledge audit |
| 5a1df852 | 10-11 | 4 | 1 | 0 | 0 | parent of the ads agent |
| **5a1df852/sub a46882db** | **10-11 13:30..13:58** | **52** | **41** | **18** | **2** | **the ads agent** |

## The "ads" agent

**Session `5a1df852-0f26-4ec9-9d10-53a667cd5f81`, subagent `a46882db`**, spawned by the parent as
`Agent "Mine 01_Datasets for ads/ecom"` (general-purpose, sonnet), 2026-10-11 13:30-13:58 UTC.
Brief: Ad Lab for Brand #001 "Carla Miravet"; bound "~60 file reads, 35 minutes"; read-only; output
`scratchpad/datasets-ads-ecom.md`. It read 41 distinct paths, 18 under `extracted\Ads`, and 59 tool calls in total.

## Legitimate vs redundant (per re-read)

- **Exact-file overlap is small: 2 of 41 paths** had been read by an earlier session. By file, this was
  mostly NEW reading, not a literal re-read. The Owner's premise "it mined the same thing again" is
  true at the **corpus** level and mostly false at the **file** level.
- **Legitimate**: a new question (ad creative/BFCM rules for a 300 EUR Spanish fashion test) over files
  no earlier session had opened; the ads folder had never been read by any prior session in these
  transcripts (0 `extracted\Ads` hits before this agent).
- **Redundant / unreachable prior work**: session 681ad0fb built `vault/youtube_evidence/` (chunked FTS5 index
  over the YouTube harvest) 9 days earlier. The ads agent opened YouTube channel transcripts directly
  (AlexFedotofff, AustinRabin, aries1, AcHampton, ...) with Read/Grep and its 59 calls include no
  access to that index. That sub-portion is the real missed reuse. Evidence for "did not consult" is
  absence in its tool calls, not a statement by the agent.
- **Why nothing stopped it**: no coverage record existed. PART_44 recorded "YA asimilado -> DO_NOT_REBUILD"
  while reading 4 of 361 files; DBOIS Phase 0 listed 408 files without per-file depth; CO-05 registry
  `vault/cognitive_os/asset_registry.jsonl` does not exist; FD-00 has no live caller. The agent had no way to
  ask "what is already covered, at what depth?".

## Not measured here (do not cite as findings)

- Token cost of the redundant fraction (transcript `usage` is not attributable per file).
- Whether the agent's deliverable duplicated content in `vault/youtube_evidence/` (not diffed).
- Sessions outside the 15 scanned dirs (`C--Users-kobig-*`, `_wt-cw-converge-deploy-release` had 0 transcripts).

## Consequence for W1+

Receipt must record **depth per file** and **artifact pointers** (so `vault/youtube_evidence/INDEX` is
discoverable as prior coverage), and delivery must reach **subagent** spawns, not only the parent prompt.
