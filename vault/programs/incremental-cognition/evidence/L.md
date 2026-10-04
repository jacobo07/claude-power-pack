# Pillar L -- offline replay ranking of the live experiments: evidence

Plane: GEX44 `kobicraft-gex44` (Linux 6.8, user `kobii`), `python3` 3.12.3, branch `mission/incremental-cognition-run`,
worktree `/home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run`. Measured 2026-10-04, foreground, from
the worktree root. Nothing here was run on the laptop: the KME-L ranking and the quota decision are the two `[L]` items
of `vault/programs/incremental-cognition/owner-bundle.md` (section `## Phase 5 -- offline replay ranking and the
live-experiment decision (laptop plane)`). No `claude` session was started.

## Frozen rule (verbatim from ledger.json, frozen.pillars id L)

> offline replay of KME-L (late rollover, identical rereads, unchanged-precondition retries) ranks live experiments; live champion/challenger sessions spend quota and need an Owner decision

Predicted terminal: `RESEARCH_INSUFFICIENT_EVIDENCE`. Owner of the rule: `vault/programs/cognitive-economy/ledger.json`
(the CE ledger; cited here, never edited). The rule names the denominator KME-L, which is laptop-plane; the corpus is not
on GEX44. So the instrument is built and smoke-run on GEX44 and the pillar is not closed.

## What the ranker measures

`wiki/tools/kme_replay.py rank` scans the transcripts once through `kme_pillars`' own run context (frozen-source record,
flag refusals, the `--until auto` locator, the population match: imported, never forked) and writes one
`L-<label>-<UTC date>.md` that ranks three candidate experiments on ONE weighted denominator (the run's selected
population, named in the file). The unit is the ledger's weighted input-equivalent (input 1, cache_read 0.1,
cache_write 2, output 5). Every figure is an UPPER BOUND on what the experiment could save, never a realized saving: the
displacement rule is frozen (tokens a change removes may be paid again elsewhere), so each ranked entry carries
`saving_status: upper_bound` and `displacement: unknown`.

| candidate | model (upper bound) |
|---|---|
| `late_rollover` | policy P(G) replayed per transcript file (one thread = one context): roll over whenever the simulated context's growth above the thread floor F (its first non-synthetic call's input + cache_write + cache_read) reaches G tokens (default 100,000); on each later call avoided tokens = min(cut - F, ctx_k - F); upper weighted = min(avoided, cache_read_k) x 0.1 + the rest x 2; an actual compaction restarts the policy. G = 50,000 / 100,000 / 200,000 are reported beside as sensitivity and never decide the rank |
| `identical_rereads` | the Phase 3 pillar E numerator: `kme_pillars.EObserver` itself (imported); the upper bound is its `weighted_interval[1]` (rereads of an identical file version in one thread, residency-weighted), equal to `round(weighted_interval[1], 6)` |
| `unchanged_precondition_retries` | the same tool with the same key repeated in one transcript file with no intervening Edit / Write / MultiEdit / NotebookEdit (loose = the upper bound) or no intervening call outside the read-only tools (strict, beside); upper weighted per retry = result burden (chars, residency, 3.0 chars per token) + the issuing message's output share x 5 |

Why growth and not an absolute context. The threshold is growth above the thread's own floor because, on GEX44, the
main-thread first-call floor is 172,753 .. 194,591 tokens (03-04 I smoke), above P0's 150,000 large-context mark: an
absolute threshold would "cross" on every first call and measure the floor, not lateness. The smoke below shows the same
fact (floor median 173,427.5).

Why the retry key is the command text and not the input JSON. The planning probe of the a5 / a7 / b001 trees (unwindowed,
not a measurement, recorded in 05-01-PLAN so fixtures match reality): keyed by the full input JSON only 1 identical
repeat exists (a Bash input carries `description`); keyed by the Bash command text there are 75 repeats, 19 with no
intervening write tool (loose) and 5 with only read-only tools between (strict).

Exclusions and bounds: `Read` (pillar E's) and the write tools are not retry candidates; `Agent` / `Task` re-dispatches
are counted beside only (their cost lives in subagent files the replay cannot link to the parent call).

UNMEASURED is never zero. A candidate whose signal is not observed for the whole selected population (rollover: a session
with inline sidechain lines in its main file; retries: a retry whose tool_result never appears; any drift of the
population or an unlocated cutoff: all three) is listed under `unranked` with a named reason and NO number; a candidate
observed with no events is a measured zero and is ranked. Only MEASURED candidates rank, highest upper bound first, ties in
the fixed candidate order. Every ranked entry is read against 3 % on its bound (`>= 3 %`: a live experiment could clear
materiality and needs the Owner's quota decision; `< 3 %`: cannot clear materiality even if fully realized).

Exit codes: 0 every candidate measured, 3 any UNMEASURED (the file is still written), 2 usage or refusal (nothing written).

terminal_evidence rule (`terminal_ok`): true only for a primary file (denominator in the rule's `KME-L`), population
exactly reproduced, the committed (default) frozen source and nothing unranked. A smoke file (any other denominator)
carries `terminal_evidence: false` and `evidence_role: smoke`. The program done-gate (R3-L, 05-03) believes a
`terminal_evidence` claim only when the file's own fields agree with it, and refuses a smoke, a forged primary and the
owner bundle quoted as an `owner_decision` (R4).

## Commands and observed outputs

All from the worktree root on GEX44, foreground, bounded.

```
$ python3 tools/test_kme_replay.py                                  (exit 0)
KMER_PASS=45/45  threshold=45/45  skipped=0  inconclusive=0
PASS V-KMER-BUNDLE-SUMMARY-ITEMS 19 item key(s) incl. sync (>= 19), 24 row(s), problems=[], controls report: {'removed row': True, 'stale row': True, 'unknown command': True, 'removed header': True}
PASS V-KMER-BUNDLE-SUMMARY-UAT 11 pending UAT key(s) (>= 11) and 1 VER key(s) (>= 1) each have a row, problems=[], 7 controls report

$ python3 tools/test_kme_replay.py --drill                          (exit 0)
PASS DRILL-CONTROL unmutated run: 42/42 gates green
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 42/42 gates green
DRILL killed=19/19

$ timeout 300 python3 tools/test_kme_pillars.py                     (exit 0)
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
$ timeout 600 python3 tools/test_kme_pillars.py --drill             (exit 0)
DRILL killed=20/20
$ timeout 300 python3 tools/test_floor_regression_gate.py           (exit 0)
FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0
$ python3 tools/test_incremental_cognition_program.py --selftest    (exit 0)
CEP_SELFTEST=PASS
ICP_SELFTEST=PASS
$ python3 tools/test_incremental_cognition_program.py --pillar L    (exit 1)
  FAIL L3 L: no terminal disposition
CEP_PILLAR_L=FAIL
ICP_PILLAR_L=FAIL
```

KME-G smoke (plane gex44; produced by 05-02, committed as
`vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md`; labelled smoke, plane gex44, never terminal,
`evidence_role: smoke`, `terminal_evidence: false`). Command (exit 0, 3.7 s): `python3 wiki/tools/kme_replay.py rank
--denominator KME-G --until auto --expand --root /home/kobii/a5-env/home/.claude/projects --root
/home/kobii/a7-env/home/.claude/projects --root /home/kobii/b001-env/home/.claude/projects --root
/home/kobii/.claude/projects`. Population match exact (13 active / 151 dead sessions, 1,322 calls, weighted
54,899,558.8, frozen source the committed `kme_audit_2026-10-03.json` sha256 38493644...c1da, `until_located`
exact_at_freeze). Reading, quoted from that file:

| rank | candidate | upper bound (weighted) | share of KME-G weighted | vs 3 % on the bound |
|---|---|---|---|---|
| 1 | late_rollover (G = 100,000) | 8,773,728.0 | 0.1598 | >= 3 % |
| 2 | unchanged_precondition_retries | 2,520.633333 | 0.000046 | < 3 % |
| 3 | identical_rereads | 0.0 (measured zero) | 0.0 | < 3 % |

Rollover sensitivity (upper / rollovers): G 50,000 -> 11,643,331.2 / 41; 100,000 -> 8,773,728.0 / 16; 200,000 ->
3,024,745.1 / 5; 24 threads, 9 cross G = 100,000, floor min 124,905, median 173,427.5, max 194,591. Retries: 3 loose, 0
strict (Bash 2, ExitWorktree 1; 1 after an error; 0 Agent re-dispatches). Rereads: 142 reads, 140 first, 2 unhashable, 0
identical. On this corpus only late rollover could clear 3 %, and only as an optimistic ceiling. It says nothing about
KME-L; KME-L decides.

Owner-bundle replays of 05-03 (scratch clones at the P0 freeze `18e928af`, literal lines, only the fetch URL replaced by
the local worktree path; both clones removed):

- Old Phase 3 path (`FROZEN_AT` pick `d4d35059`, then the fourteen picks, all applied): `grep -c frozen_source
  wiki/tools/kme_pillars.py` -> 0. The fourteen picks predate the eight phase-3 review fixes `d241bb5e` .. `326da74c`
  (`frozen_source` was added by `a4d09a24`, WR-07); no KME-L file made along that list could close D..I.
- Old `[K]` path (eight picks, then the `ef336ec7` tree-state checkout): the owner bundle is absent in that clone and
  `python3 tools/test_floor_regression_gate.py` exits 1 with `FAIL V-FLOOR-BUNDLE-ARGV-PARSES owner bundle missing`
  (`FLOOR_PASS=66/67`).
- New path, the `## Laptop code sync` lines at tip `f3cdc79b`/`26f039f1`: fetch, ancestor check (exit 0), empty status,
  checkout and commit exit 0; four suites exit 0.

Final replay (this plan), clone at `18e928af`, the `## Laptop code sync` lines read from the committed bundle at branch
tip `4c3044b888394ef45af1126535f7348880580228`: `git fetch` exit 0; `git rev-parse FETCH_HEAD` ->
`4c3044b888394ef45af1126535f7348880580228` (equal to the branch tip); `git merge-base --is-ancestor f3cdc79b... FETCH_HEAD`
exit 0; `git status --short -- <paths>` printed nothing (0 bytes); checkout and pathspec commit exit 0; then, each exit 0:

```
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
SKIP V-KMER-BUNDLE-SUMMARY-UAT phase(s) ['01', '02', '03', '04'] cited by a row have no UAT or VERIFICATION file on this checkout
KMER_PASS=40/40  threshold=40/40  skipped=1  inconclusive=0
FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0
ICP_SELFTEST=PASS
```

The UAT gate SKIPs there because the workstream holds no phases directory at the freeze (a SKIP is never a PASS and is
outside the n/m count); the bundle's expected-output block predates the table, so a paragraph under it (commit
`4c3044b8`) states 40/40 with skipped=1 at the freeze and 41/41 on GEX44.

## Owners consumed

- `wiki/tools/kme_pillars.py` (Phase 3): the run path (`_measure` / `_resolve`: frozen-source record, `--until auto`
  locator, population match) and `EObserver` are imported. The only edit to that file is an additive keyword
  (`observer_factories`) on `_measure` / `_resolve` and its three measuring call sites, six lines in all (05-01); its
  89/89 suite and 20/20 drill are unchanged.
- The CE ledger (`vault/programs/cognitive-economy/ledger.json`) is the frozen owner of rule L and the owner of
  `tools/test_cognitive_economy_program.py`; both are cited and not edited (`git diff --stat --
  tools/test_cognitive_economy_program.py` prints nothing). The program wrapper `tools/test_incremental_cognition_program.py`
  gained R3-L and R4 (05-03) and its selftest is green.
- `modules.secret_firewall.redact`: every emitted text passes it; commands appear only as `kp.cmd_signature` output
  (`V-KMER-NO-SECRET`, a canary in five places).

## Owner bundle consolidation

- The bundle opens with `## Summary (every Owner item, phases 1-5)`: 24 rows (the code sync, every `[A]`..`[L]` item,
  the judgement checks that exist only as pending UAT tests), each with source, action, exact command and what closes
  when it lands. Coverage is discovered: `V-KMER-BUNDLE-SUMMARY-ITEMS` enumerates the file's own `- **[X]**` items and
  the sync step (19 keys) and requires a row for each, refuses a row citing an item that does not exist and a command
  that is not an indented line of the body; `V-KMER-BUNDLE-SUMMARY-UAT` enumerates the pending tests of the phase UAT
  files (11) and the human_verification entry of the UAT-less phase 1 VERIFICATION (1). Both carry in-gate controls that
  must report a removed row, a stale row and an unknown command.
- `## Laptop code sync`: one guarded step (fetch, tip recorded, ancestor check, empty status, checkout of the program
  tool files, pathspec commit, four suites) replaces the Phase 3 cherry-pick list and the `[K]` cherry-pick /
  tree-state steps; replay-proven on GEX44 only.
- The two corrections (Phase 3: no `frozen_source` on the old path; Phase 4: the old path lacks the bundle its own
  parse gate reads) are worded only as the replays observed them; R3-L / R4 are in the program done-gate.

## Liveness

The scanner's own aperture, quoted from `python3 modules/liveness/reachability.py`:

```
APERTURE: packages under `modules/` only. `tools/` is NOT scanned, so nothing below is evidence about the verification runner, the benchmarks, the commit wrapper or the hunk guard. Silence here about a tool is absence from the denominator, never health.
```

`wiki/tools/` is outside it as well. With BASE = `bfe4ee4ada6a8e2fa3ae22a3cce211bb4edeebc1` (the parent of the oldest
commit touching `wiki/tools/kme_replay.py`), `git diff --name-only BASE..HEAD -- modules hooks commands agents SKILL.md
CLAUDE.md vault/liveness` prints nothing (0 lines), so none of the scanner's inputs changed in this phase. Today's run,
plane gex44: `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 | gate offenders: 64`, exit 1, the same 64
pre-existing offenders K.md recorded at phase 4, none introduced here. No registry entry was written: registry keys are
`modules/` units.

How the ranker is reached today: its test (`tools/test_kme_replay.py`), the `[L]` owner-bundle item (its command is
parse-proven by `V-KMER-BUNDLE-ARGV-PARSES`), and, once L closes, the ledger evidence that `--final` reads (R3-L checks
the KME-L file's own fields). No hook, CI job or `--final` run executes the ranker itself.

## Artifacts (LF sha256)

```
a4ecf18c12129812433e265c137e1b07b428405a98b7d250794954e29e46a33a  wiki/tools/kme_replay.py
481a80a32d2c5fe90f8a013c072b0c8cc18ce701dc87be0a530df62e09e0712f  tools/test_kme_replay.py
575781ed5f8722f268cb13f86f22cd3d549f3df3c5be64b08430c4aee67f1e92  vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md
29d8685f302be575221210ae47fcd643e961781368e3eb01566316e440f2b10f  vault/programs/incremental-cognition/owner-bundle.md
0d439f2b6fc24bfe19dd55dd40d7702c56908d425b19116e49d99763ef3c30d4  tools/test_incremental_cognition_program.py
3a005629aa093e044c2d3760d3180a4a138ea228edf8a6736af70fb8d00e8270  wiki/tools/kme_pillars.py
```

(`hashlib.sha256` over the file bytes with CRLF folded to LF, the CE verifier's `lf_sha256`.)

## Product Delta

The Owner can now see, from one command run on the laptop, the three live experiments (late rollover, identical rereads,
unchanged-precondition retries) ranked by upper bound on one named weighted denominator, each with a reading against
3 % and an UNMEASURED candidate listed with its reason and never shown as 0. They open one bundle whose first section
lists every action the program needs from them, with the exact command and what each closes, and a gate turns red the day
an item or a pending UAT check has no row. The laptop code arrives through one guarded sync instead of two stale
per-item cherry-pick lists. The live-session quota decision stays a plain `[L]` item the Owner answers in their own
words.

## Intelligence Delta

Measured facts, each with its source:

- KME-G smoke ranking: late rollover 8,773,728.0 (15.98 % of the weighted denominator 54,899,558.8, `>= 3 %`), retries
  2,520.6 (0.0046 %), rereads 0.0 (measured zero); rollover is 11,643,331.2 at G = 50,000 and 3,024,745.1 at G = 200,000,
  still above 3 % at 200,000 (`L-KME-G-2026-10-04.md`).
- The floor sits above the rollover threshold: first-call context floors on GEX44 run 124,905 .. 194,591 (median
  173,427.5) over 24 threads, so growth above the floor, not an absolute context, is what a rollover candidate can
  measure (`L-KME-G-2026-10-04.md`; 03-04 I smoke).
- The retry key is the command text: by full input JSON 1 identical repeat, by Bash command text 75 repeats (05-01-PLAN
  planning probe, unwindowed). On the smoke population 3 loose and 0 strict retries.
- The Phase 3 cherry-pick list was stale: replayed at `18e928af` it leaves `kme_pillars.py` with `frozen_source` 0 times,
  so R3 (WR-07) would refuse every KME-L file made along it; the `[K]` old path leaves the fixture suite at 66/67 because
  its own parse gate reads a bundle that path never brings (05-03 replays above). The `[K]` and KME-L bundle items
  therefore depend on the code sync, not on their old lists.
- What the KME-G smoke can say about KME-L: that the instrument runs end to end on a real corpus, reproduces its
  population exactly and ranks. What it cannot: any KME-L figure, any realized saving, or whether a live experiment is
  worth its quota. The corpora differ (GEX44 mission workers against the laptop's sessions).

## Code-review fixes (05-REVIEW-FIX.md, 2026-10-04)

The figures above are unchanged by the review fixes (the smoke was regenerated with the command recorded in it; the a5, a7
and b001 trees are byte- and mtime-identical before and after). What changed: the ranked entries carry the upper bound
only (no `weighted_lo` / `weighted_interval`), values rounded to 6 decimals; equal figures share a rank; retries and
rereads are keyed per thread; a terminal ranking must be at rollover growth 100000 and be internally consistent
(ids, json block, frozen source); `top_paths` are digests; R4 judges the identity of an `owner_decision` ref (the bundle
under any spelling, a byte copy, any mission-written file) instead of its spelling. Counts now: `test_kme_replay.py`
45/45, drill 19/19; `test_kme_pillars.py` 89/89; `test_floor_regression_gate.py` 67/67; program selftest PASS;
`--pillar L` still exits 1 (no terminal).

## Named debts

- The KME-L run is the Owner's `[L]` item; no KME-L ranking exists. The live-session decision is the Owner's, in their
  own words, as `evidence/L-owner-decision.md` (not written, not paraphrased).
- The upper bounds are gross: a rollover's own re-read cost and any summary are not subtracted; the loose retry class
  includes state changed through Bash or the outside world; Agent re-dispatches sit outside the candidate. The bounds of
  different candidates overlap and are not additive.
- The sync is proven only in GEX44 scratch clones at the freeze, never on the laptop; the UAT coverage gate SKIPs on the
  laptop and in those clones (the phase files are not there).
- `wiki/tools/` and `tools/` are outside the liveness scanner and no hook, CI job or `--final` run executes the ranker.
- The 64 pre-existing liveness offenders on GEX44 are not this phase's.

## Status: OPEN

Ledger `state.L` is not written (`{}`), IC-L is not ticked, and `python3 tools/test_incremental_cognition_program.py
--pillar L` still reports `FAIL L3 L: no terminal disposition`. The pillar closes only through the `[L]` items: the
Owner's KME-L ranking file `L-KME-L-<date>.md` and/or the Owner's decision file, after which L takes the terminal its
frozen rule gives.
