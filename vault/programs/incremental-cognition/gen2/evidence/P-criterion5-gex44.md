---
pillar: P
programme: IC-gen2 autonomous-optimization
plane: gex44
denominator: KME-L
head: 40597853eba2117a6fe9607612ec5ab8f7942fc4
measured_at: 2026-10-07T00:06:04Z
verdict: WIN
---

# [P] (IC-gen2) KME-L challenger, criterion 5 decided by measurement

ROADMAP Phase 2 criterion 5 (plan 02-06). The verdict below is computed from the machine-readable `## Data` block of
`P-table-gex44.md` (plan 02-05, plane `gex44`, host `kobiicraft-gex44`) by the command in `## Verdict`; it is not
narrated. This file holds numbers, paths and verdicts only, no transcript text (HR-SECRET-002).

## Rule

Pre-registered rule (written at planning time, before any Phase 2 number exists):
- WIN iff `challenger.warm.wall_median_s < scoped.warm.wall_median_s` AND `challenger.raw_bytes < scoped.raw_bytes`.
- Reported beside, never deciding: cold medians, post-delta, index bytes, raw + index bytes, the seven-run and Run 6
  population rows, ratios scoped / challenger.

Anything other than WIN is a LOSS of increment 1. The comparison is against the cheaper scoped baseline (`all` + `rank`,
orchestrator decision 3), not against champion Run 5.

## Verdict

command: `python3 -I -c 'import json,re,pathlib;t=pathlib.Path("vault/programs/incremental-cognition/gen2/evidence/P-table-gex44.md").read_text();d=json.loads(re.search(r"^## Data\s*\n+```json\n(.*?)\n```",t,re.S|re.M).group(1));cw=d["challenger"]["warm"]["wall_median_s"];sw=d["scoped"]["warm"]["wall_median_s"];cb=d["challenger"]["raw_bytes"];sb=d["scoped"]["raw_bytes"];v="WIN" if cw<sw and cb<sb else "LOSS";print("P-JUDGEMENT verdict=%s wall_warm_s=%s/%s raw_bytes=%d/%d wall_ratio=%.3f bytes_ratio=%.3f"%(v,cw,sw,cb,sb,sw/cw,sb/cb))'`

P-JUDGEMENT verdict=WIN wall_warm_s=29.580848/56.975624 raw_bytes=3298099868/6120339068 wall_ratio=1.926 bytes_ratio=1.856

Reading it: the challenger warm median wall is 29.580848 s against 56.975624 s for the scoped path (1.926x), and its
traced raw bytes are 3,298,099,868 against 6,120,339,068 (1.856x). Both inequalities hold, so the rule returns WIN.

Reported beside, not deciding:

| What | scoped (all+rank) | challenger (all+rank) | scoped / challenger |
|---|---|---|---|
| warm median wall, s (n=5) | 56.975624 | 29.580848 | 1.926 |
| evicted-best-effort median wall, s (n=5, residency not measured) | 58.523155 | 37.529019 | 1.559 |
| raw bytes (traced, two processes) | 6,120,339,068 | 3,298,099,868 | 1.856 |
| index bytes (traced, two processes) | 0 | 1,805,435,496 | n/a |
| raw + index bytes | 6,120,339,068 | 5,103,535,364 | 1.199 |
| post-delta warm median wall on the scratch copy, s | n/a | 28.758788 | n/a (six-directory index, not comparable on index bytes) |

Plain statement of the cost the rule does not count: the challenger additionally reads 1.81 GB of SQLite index
(two reads of the whole-corpus index, one per process), so its total read volume is 5.10 GB against
6.12 GB for the scoped path. It is still lower, by 1,016,803,704 bytes, but the saving on bytes is 16.6% when
the index is counted and 46.1% on the raw-bytes column the rule decides on. The index is not a transcript read: it holds metadata rows
and no transcript text. The "evicted" rows are best-effort `posix_fadvise(DONTNEED)` and residency was not measured, so they are
not a cold-cache claim.

## Table

The P-table rows copied from `P-table-gex44.md` `## Table` (sources are in the last column; the cited Run 5 and Run 6 rows
are the frozen champion runs, with Run 6 bytes UNMEASURED and Run 5 bytes derived).

| row | plan | cache | n | wall (median s) | raw bytes | unique bytes | raw files opened | cross-project bytes | CostaLuz bytes | index bytes | source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| champion Run 5 (unscoped, cited) | champion | n/a | 1 | 869 (cited) | 109,088,283,520 (derived) | 9,934,971,549 (derived) | 4,015 distinct (derived) | 78,486,588,180 (derived) | 998,161,080 (derived) | 0 (no index) | ledger frozen.champion.run5; bytes: 10 x 02-04 unscoped scan |
| Run 6 population (scoped, cited) | scoped | page cache as found | 1 | 24 (cited, rchar 2.83 GB) | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0 (no index) | ledger frozen.champion.run6 |
| Run 6 seven separate runs D..I, L (scoped, cited) | scoped | page cache as found | 7 | 177 (cited sum, rchar 19.47 GB) | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0 (no index) | ledger frozen.champion.run6 |
| scoped all+rank, evicted | scoped | evicted best-effort, residency not measured | 5 | 58.523 | 6,120,339,068 | 3,055,976,146 | 995 | 0 | 0 | 0 | bench JSON scoped-cold-a/b, scoped-traced |
| scoped all+rank, warm | scoped | warm | 5 | 56.976 | 6,120,339,068 | 3,055,976,146 | 995 | 0 | 0 | 0 | bench JSON scoped-warm, scoped-traced |
| challenger all+rank, evicted | challenger | evicted best-effort, residency not measured | 5 | 37.529 | 3,298,099,868 | 1,648,220,948 | 369 | 0 | 0 | 1,805,435,496 | bench JSON challenger-cold-a/b, challenger-traced |
| challenger all+rank, warm | challenger | warm | 5 | 29.581 | 3,298,099,868 | 1,648,220,948 | 369 | 0 | 0 | 1,805,435,496 | bench JSON challenger-warm, challenger-traced |
| challenger post-delta (scratch copy) | challenger | warm | 5 | 28.759 | 3,301,460,730 | 1,649,876,803 | 372 | 0 | 0 | 519,078,504 | bench JSON challenger-post-delta-warm/-traced; index = delta.sqlite (six-directory index) |

Caption: Cross-project bytes count transcript bytes outside the KME-L scope; index bytes are reads of the SQLite index, a whole-corpus file that holds metadata rows of every project (CostaLuz included) and no transcript text.

## Narrowed claim

The challenger is the KME-L zero-rescan path of pillar [P] (IC-gen2), narrowed to what was measured:
- The certified Phase 1 index selects the sessions; only the selected sessions' transcripts are read, through the existing
  observers (`wiki/tools/kme_pillars.py`, `wiki/tools/kme_replay.py`), raw and every time.
- The certificate is keyed on the selection-parser digest, the attribution version, the pattern set and the population
  definition; any edit to a selection source invalidates it, and the guard chain deopts to the scoped champion path.
- Per-session watermark closure: a transcript that grew after certification is read as stale, not trusted from the index
  (post-delta canary: five appended sessions read as stale, output equal to the scoped run and to the committed files, SAME 7/7).
- KME frozen denominators only, with `select kme` only; the global raw scan runs only on `--cross-project`.
- Measured on the GEX44 corpus copy for the seven-file KME-L query: 1.926x on warm median wall and 1.856x on
  raw bytes against the scoped `all` + `rank` path, with the index bytes reported beside.

## Not claimed

- Zero raw bytes: the selected sessions are still read raw (3,298,099,868 bytes, 369 files in the traced set).
- Any saving on index bytes: the challenger reads 1,805,435,496 index bytes and the scoped path none; they are reported beside, and
  raw + index is 83.4% of the scoped raw bytes.
- Pillar G caching: G reads its selected files raw every time, with no persisted text-derived cache (orchestrator decision 6).
- A cold-cache result: the evicted rows are residency-not-measured.
- The laptop plane (`plane: laptop`): nothing was measured there.
- Savings over real usage: no count of real KME-L queries exists on this plane; the figures are per query.
- Promotion and the closure of pillar P: frozen rule clause 6 (ratchet promotion, fresh worker, bypass gate) belongs to Phase 6.

## Facts sidecar

Not built: increment 1 beat the scoped path on both deciding comparisons, orchestrator decision 1 (a facts sidecar is built
only if increment 1 loses criterion 5). The increment-2 design (per-file facts keyed on content id, parser digest and per-pillar
metric digest, pillar G deopt-only) stays unbuilt.
