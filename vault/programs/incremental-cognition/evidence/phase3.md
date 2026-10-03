# Phase 3 evidence -- pillars [D] [E] [F] [G] [H] [I]: the KME measuring instrument, built and smoke-run on GEX44

Plane: **gex44**. Instrument: `wiki/tools/kme_pillars.py` (subcommands `d e f g h i all population`), gate
`tools/test_kme_pillars.py`, done-gate guard R3 in `tools/test_incremental_cognition_program.py`. Requirements
IC-D..IC-I are **addressed, not satisfied**: each is satisfied only by its ledger terminal, which needs the laptop
KME-L measurement file (owner bundle `[D]`..`[I]`). Nothing here is a pillar terminal.

## Plane and denominator

- Every measurement file committed from GEX44 is about the **instrument**, not the pillar: KME-G (the GEX44 corpus,
  frozen population 13 active / 151 dead / 1,322 calls at 2026-10-03T16:13:37Z) or the named workload GEX44-B001.
  Each carries `plane: "gex44"`, `evidence_role: "smoke"`, `terminal_evidence: false`. KME-L is laptop-plane and is
  not on this host; no KME-G figure below is a KME-L figure, and none is generalised to it.
- The three evidence roles the instrument writes, and how R3 (below) treats each:

  | evidence_role | written when | `terminal_evidence` | R3 |
  |---|---|---|---|
  | `primary` | the denominator is in the pillar's frozen rule (D: KME-L, CPP-D-W7; E..I: KME-L) | true only if the population reproduced the frozen one (or a referenced one is fully covered) and the verdict is measured | accepted only with `terminal_evidence: true` |
  | `second_workload` | `--role second_workload` on a workload outside the pillar's own rule | false (never terminal itself) | accepted only if `second_workload_valid` is true AND the same pillar also cites a primary file with `terminal_evidence: true` |
  | `smoke` | the denominator is outside the pillar's frozen rule (every file committed here) | false | refused always |

- **Frozen rule E, "confirmed on a second workload", in the done-gate.** E's closing shape is a primary KME-L file
  plus a second-workload file. The bundle asks for CPP-D-W7 (the frozen, referenced workload; valid only at
  coverage >= 1). The instrument also lets `--role second_workload` run on KME-G (valid when its population is exact)
  or on a named OTHER workload (valid by construction, since a non-frozen population has nothing to reproduce), and R3
  accepts any such file beside a terminal primary. **Decision:** the program accepts all three, because the frozen
  rule says "a second workload" without naming one and the claim itself stays in the KME-L primary file; the
  independence argument is made at close time. A KME-G second workload is a real, separate KME corpus but of the same
  kind of work as KME-L, so it is the weaker confirmation; an OTHER workload has no reproduction check at all. Whoever
  closes E must say in `evidence/E.md` which was used and why it is independent (named debt below). KME-G can never
  stand in for KME-L: with no terminal KME-L primary, R3 refuses the second workload.
- R3 exit contract: `--pillar <P>` prints the CE lines, then `  FAIL R3 ...` lines, then `ICP_PILLAR_<P>=PASS|FAIL`;
  `--final` adds R3 to `ICP_VERDICT`. Today every pillar D..I still prints `FAIL L3 <P>: no terminal disposition`
  (state is empty), which is the expected, honest result.

## D-W7 parser difference (visible, not only a debt line)

CPP-D-W7 is a **referenced** denominator: its window (2026-09-26 .. 2026-10-03, 75,969 calls, weighted
3,325,101,725) is read from the CE ledger (`vault/programs/cognitive-economy/ledger.json`), produced by
`tools/usage_index.py`, which **dedupes calls across files and keeps the last copy**. `kme_pillars` counts **per file
with max-merge**. So coverage >= 1 (measured calls / ledger calls) does not prove the two instruments saw the same
call set, and coverage < 1 makes the upper bound unknown (UNMEASURED unless the lower bound alone clears 3 %). Every
CPP-D-W7 file carries this caveat in its `caveats`. On GEX44 no CPP-D-W7 file exists (the window is laptop data); the
instrument's coverage and role behaviour is proven on synthetic ledgers (`V-KMEP-DW7-SPEC/-COVERAGE/-WINDOW-FIXED/-ROLES`).

## Frozen rules (verbatim from `vault/programs/incremental-cognition/ledger.json` frozen.pillars)

- **D** (predicted FALSIFIED_OR_REJECTED_BY_EVIDENCE): "measure hook_additional_context chars per tool call on KME-L
  and CPP-D-W7 sessions; a slice only at >= 3 % weighted; broken hook delivery is fixed under B regardless"
- **E** (predicted RESEARCH_INSUFFICIENT_EVIDENCE): "replay rereads of identical file versions on KME-L (same path,
  unchanged content between reads); build a query path in an existing owner only at >= 3 % weighted on KME-L AND
  confirmed on a second workload; never split source for size alone"
- **F** (predicted MERGED_INTO_EXISTING_OWNER): "measure GSD workflow-doc residency (char x turns) on KME-L; if
  gsd-tools init already returns the compact state, hand the residency finding to the GSD owner; never fork GSD"
- **G** (predicted RESEARCH_INSUFFICIENT_EVIDENCE): "count re-tested falsified hypotheses and re-litigated sealed
  decisions in the corpus (positive control: listing hiding C6 -> K4); one falsifiable slice on the existing owner
  only if the count clears materiality or a correctness exception"
- **H** (predicted FALSIFIED_OR_REJECTED_BY_EVIDENCE): "consume CE P and G verdicts; one KME-specific check that
  verification share is below materiality"
- **I** (predicted MERGED_INTO_EXISTING_OWNER): "add the measured subagent first-call context on KME-L to CE B / SC
  A-C; no move of a rule or skill here"
- Materiality (frozen): "a dedicated slice needs >= 3 % of a named weighted denominator (default KME-L weighted;
  CPP-D-W7 for CPP-corpus claims)"; weighted = input 1 + cache_read 0.1 + cache_write 2 + output 5; KME-G weighted =
  54,899,559.

## Commands and observed outputs (GEX44 smoke, read-only on the a5 / a7 / b001 trees)

Each command is the `command:` field of the committed file; the frozen cutoff is `--until 2026-10-03T16:13:37Z` (the
I file used `--until auto`, which located it as `exact_at_freeze`, one scan). Roots: `/home/kobii/a5-env/home/.claude/projects`,
`/home/kobii/a7-env/home/.claude/projects`, `/home/kobii/b001-env/home/.claude/projects`, `/home/kobii/.claude/projects`
(four `--root` flags, `--expand`). Named workload: `--denominator OTHER --label GEX44-B001 --select all --host gex44
--expand --root /home/kobii/b001-env/home/.claude/projects`.

| pillar | file | LF sha256 | population_match | until | share_interval | materiality | second_workload_required | second-workload file |
|---|---|---|---|---|---|---|---|---|
| D | `measurements/D-KME-G-2026-10-03.md` | `e8d7c24d005217d69dc4073232f47c3017333af2114f6baa255409443cf88fc3` | exact | 2026-10-03T16:13:37Z | [2.6388 %, 3.9582 %] | STRADDLES | true | `D-GEX44-B001-2026-10-03.md` (smoke sample, not_frozen, [0.0015 %, 0.0022 %], **UNMEASURED** since the review-fix regeneration: observability 0.855, only 7 of its 10 sessions carry a `hook_*` attachment, so the earlier `< 3 %` was an unobserved-as-zero reading (03-REVIEW IN-01); sha `22527425a4f53ae90a4f3e690f0ae3d063d6142eb070073a345d62df8dec4e56`) |
| E | `measurements/E-KME-G-2026-10-03.md` | `c984c288aab49733f5d3f2e6227bf0b002f0b5e7dcc684638d4485bb9086af0c` | exact | 2026-10-03T16:13:37Z | [0.0, 0.0] | < 3 % | false | not required |
| F | `measurements/F-KME-G-2026-10-03.md` | `9977d194cf7ac952d69095580813f4341e1d9b08041ce846279be85f02c5cf60` | exact | 2026-10-03T16:13:37Z | [0.6880 %, 1.0320 %] | < 3 % | false | not required |
| G | `measurements/G-KME-G-2026-10-03.md` | `ae95ba7459167e593a8b46ea124e2861b976671e1411df8bfcd886fe9fcccb9a` | exact | 2026-10-03T16:13:37Z | [0.0, 0.0] | < 3 % | false | not required |
| H | `measurements/H-KME-G-2026-10-03.md` | `f330f734da25555bda758860f923fbdd841aae40b0a1e0455ff1672f46adf76b` | exact | 2026-10-03T16:13:37Z | [7.2976 %, 7.3973 %] | >= 3 % | true | `H-GEX44-B001-2026-10-03.md` (smoke, not_frozen, [8.7317 %, 9.1489 %], `>= 3 %`; sha `9319c45a7a8b1997ef584c61b08a1936ab3265d526d92b1f5be5ed1dfb4abdb3`) |
| I | `measurements/I-KME-G-2026-10-03.md` | `c29c7978962fe8aeb64b49a2a7be7fef4879289b70db4b99aa1386b8efe6a234` | exact (`exact_at_freeze`, 1 scan) | 2026-10-03T16:13:37Z | [8.2611 %, 8.2611 %] | >= 3 % | true | `I-GEX44-B001-2026-10-03.md` (smoke, not_frozen, 17.2544 %, `>= 3 %`; sha `6ab4337dc405e01bc71110952a8a1ebc5e576e4fa16e3b768f9b9fc60a2d126a`) |

One-scan equality (03-04): `all --denominator KME-G --until auto --expand ...` over the same roots wrote six files whose
`share_interval` and numerators equal the per-pillar files above for D, E, F, G, H, I, all `population=exact`,
`cutoff=exact_at_freeze`, one scan.

`--pillar` outputs as observed at the end of this plan (state D..I is empty, so L3 fails by design; R3 adds nothing
because no measurement is cited):

```
$ for P in D E F G H I; do python3 tools/test_incremental_cognition_program.py --pillar $P; done
  FAIL L3 D: no terminal disposition
CEP_PILLAR_D=FAIL
ICP_PILLAR_D=FAIL
  (the same two lines, with the letter, for E, F, G, H and I)
```

## Instrument proofs

- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=83/83  threshold=83/83  skipped=0  inconclusive=0` (81 at the
  start of this plan, +`V-KMEP-R3-E-PAIR`, +`V-KMEP-BUNDLE-ARGV-PARSES`). Real-corpus gates, observed now:
  `V-KMEP-KMEG-FROZEN-REAL` (measured 13 / 151 / 1,322 / input 2,644 / cache_write 6,272,100 / cache_read 381,540,448 /
  output 839,734 = the frozen KME-G entry, `frozen_equal=True`), `V-KMEP-AUDIT-BYTE-IDENTICAL-REAL` (`sessions=177 files=6
  differing=[]`), `V-KMEP-KMEG-AUTO-REAL` (`match=exact method=exact_at_freeze scans=1/1`).
- `python3 tools/test_kme_pillars.py --drill` -> `PASS DRILL-CONTROL unmutated run: 78/78 gates green`, twenty `KILLED`
  lines, `PASS DRILL-CLEAN-AFTER-MUTANTS 78/78`, `DRILL killed=20/20`.
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`, with the R3
  poles `ok   V-ICP-R3-CLEAN`, `-REAL` (a committed KME-G smoke file refused), `-SMOKE-REFUSED`, `-E-PAIR-ACCEPTED`,
  `-SECOND-ALONE-REFUSED`, `-SECOND-INVALID-REFUSED`, `-SECOND-WITH-FALSE-PRIMARY-REFUSED`, `-WRONG-PILLAR-REFUSED`,
  `-NON-KMEP`, `-QUOTED-NOT-FIELD` and `V-ICP-MUT-terminal-evidence-false killed by R3`. Driving the guard with a smoke
  verdict removed made `-SMOKE-REFUSED` and `-REAL` go red; removing the orphan-second-workload rule made
  `-SECOND-ALONE-REFUSED` and `-SECOND-WITH-FALSE-PRIMARY-REFUSED` go red. End to end on the instrument's own pillar-E
  files (`V-KMEP-R3-E-PAIR`): primary KME-L + second workload CPP-D-W7 accepted; the second workload alone refused; the
  KME-G smoke file refused; the E primary cited by pillar D refused ("measures pillar E").
- `python3 tools/test_persistent_failure_park.py` -> `PFP_PASS=28/28`; `python3 tools/test_provider_breaker.py` ->
  `BREAKER_PASS=18/18` (phase-2 suites unchanged).
- `V-ICP-REAL-OWNER-READ` still prints `INCONCLUSIVE` in this clone (commits fa9ae2ed / 21671d6c are not present); that
  line predates this plan and does not fail the selftest.
- Owner-bundle parse proof: `V-KMEP-BUNDLE-ARGV-PARSES` -> 11 commands parsed through `build_parser()`, none rejected;
  driven red by a misspelt flag, a `--expand`-less or filtered first `population` command, a missing `[F]` item, a
  missing `--role second_workload` and an empty bundle. The fourteen-commit cherry-pick list was replayed in a scratch
  clone from the P0 freeze commit plus the FROZEN_AT pointer commit: the pick applied cleanly and the suite read
  `KMEP_PASS=82/82` with `ICP_SELFTEST=PASS` (the scratch lacked this bundle-text commit and its gate). Those bundle
  commands themselves are **NOT RUNNABLE HERE** (laptop paths) and are proven only to parse.
- G hand precision check on KME-G: 0 samples (no strict match), so precision is unmeasured; the 20-sample audit list is
  empty on this corpus. G's output stays an interval.

## Artifacts (LF sha256 of each committed file the evidence relies on)

```
f2d40f9b261331048a6f35ef151f3555ef97b07bf5fedcfb9d172f8ad33c36c7  wiki/tools/kme_pillars.py
e7a74a9423724a406be8f52407975248ce030f467e237218b4fe7f177e6f9682  wiki/tools/kme_token_audit.py
4e65cf6382b110a0411c56bbfeb2c4f08b9ebce290944b286133541110b387ef  tools/test_kme_pillars.py
78aacabdaf57f3100c2b091f59762071ab3ef22b6f2acd05b2fd7419cde928d8  tools/test_incremental_cognition_program.py
a242f05a575b1add67250775f7138f5e3001df8879489e1eecc8e07d42bec39c  vault/programs/incremental-cognition/owner-bundle.md
e8d7c24d005217d69dc4073232f47c3017333af2114f6baa255409443cf88fc3  vault/programs/incremental-cognition/measurements/D-KME-G-2026-10-03.md
22527425a4f53ae90a4f3e690f0ae3d063d6142eb070073a345d62df8dec4e56  vault/programs/incremental-cognition/measurements/D-GEX44-B001-2026-10-03.md
c984c288aab49733f5d3f2e6227bf0b002f0b5e7dcc684638d4485bb9086af0c  vault/programs/incremental-cognition/measurements/E-KME-G-2026-10-03.md
9977d194cf7ac952d69095580813f4341e1d9b08041ce846279be85f02c5cf60  vault/programs/incremental-cognition/measurements/F-KME-G-2026-10-03.md
ae95ba7459167e593a8b46ea124e2861b976671e1411df8bfcd886fe9fcccb9a  vault/programs/incremental-cognition/measurements/G-KME-G-2026-10-03.md
f330f734da25555bda758860f923fbdd841aae40b0a1e0455ff1672f46adf76b  vault/programs/incremental-cognition/measurements/H-KME-G-2026-10-03.md
9319c45a7a8b1997ef584c61b08a1936ab3265d526d92b1f5be5ed1dfb4abdb3  vault/programs/incremental-cognition/measurements/H-GEX44-B001-2026-10-03.md
c29c7978962fe8aeb64b49a2a7be7fef4879289b70db4b99aa1386b8efe6a234  vault/programs/incremental-cognition/measurements/I-KME-G-2026-10-03.md
6ab4337dc405e01bc71110952a8a1ebc5e576e4fa16e3b768f9b9fc60a2d126a  vault/programs/incremental-cognition/measurements/I-GEX44-B001-2026-10-03.md
```

## Product Delta

What a user of the program can now do:

- Measure pillars D..I on any named denominator in **one scan** (`all`), with a population proof first: the recomputed
  population must equal the frozen entry field by field (`population` prints it and exits 0 or 3), a growing corpus is
  brought back to the freeze instant by `--until auto`, and a drifted or unobserved population is UNMEASURED, never
  "below materiality".
- Read the same files as evidence about **who may close what**: the done-gate (`--pillar`, `--final`) now refuses a
  terminal that cites a KME-G smoke file, a non-reproduced primary, a second workload without its terminal primary, or
  a file measuring another pillar. "Never substitute KME-G for KME-L" is enforced, not asserted.
- Run six tagged laptop items (`[D]`..`[I]` in `owner-bundle.md`) whose commands are known to be valid invocations of the
  shipped instrument, starting from an unfiltered population proof.

## Intelligence Delta

What the system now knows, each figure about the **KME-G / GEX44 corpus** and its caveats, never about KME-L:

- **D (hook rent).** `hook_additional_context` is 740,326 chars over 1,105 attachments on KME-G: weighted share
  [2.64 %, 3.96 %], so the 3 % bar sits **inside** the interval (STRADDLES) and KME-G cannot decide D. On the
  GEX44-B001 workload the same chars are about 0.002 % of its weighted denominator, but that run is **UNMEASURED**
  (observability 0.855: 3 of its 10 sessions carry no hook attachment, so their silence says nothing; an earlier
  version of this file read it as `< 3 %`, corrected by IN-01 and regenerated), so no comparison between the two
  workloads is drawn. The CPP-D-W7 leg (the other half of D's rule) cannot run on this host. Caveat: the D-W7 parser difference above.
- **E (rereads).** 142 Read results, 140 first reads, 2 unhashable (images), **0 identical rereads of any class**:
  nothing to virtualize in this corpus, consistent with E's predicted RESEARCH_INSUFFICIENT_EVIDENCE. Whether the
  harness already deduplicates rereads cannot be told from this: the stub count is also 0, so there is no stubbed reread
  to see either way (the two Reads of one workflow doc sit in different transcript files, i.e. different contexts).
  KME-L decides.
- **F (GSD doc residency).** 24 GSD doc deliveries, 175,494 chars, share [0.69 %, 1.03 %]. `gsd-tools init` is present
  (2 calls, 1,261 chars) and in the one paired turn the doc delivered beside it was 6.29x larger (7,933 vs 1,261): the
  compact state exists, as F's MERGED_INTO_EXISTING_OWNER direction expects, but this rests on **one paired turn** and
  is a sample, not a finding.
- **G (re-tested falsifications).** Strict 0, loose 0 on both counts; 29 re-test markers and 0 re-litigation markers
  were candidates, none a record. KME-G holds too few falsification statements to say anything (3 sentences in 11,103
  matched a marker, all conditional or template wording): the zero means "nothing to re-test here", not "re-testing
  does not occur". The positive control (C6 -> K4) exists only as a fixture, because that case lives in plan
  documents, not in these transcripts.
- **H (verification share).** [7.30 %, 7.40 %] on KME-G and [8.73 %, 9.15 %] on GEX44-B001, both `>= 3 %`, **driven by
  verifier subagents** (7 files on KME-G: `kme-g1-ownership-arbiter` x6, `pp-code-reviewer` x1; 3.90 M weighted);
  the CE pillar-P part (test and gate tool calls plus output carriage) is only about 0.2 - 1.25 %. H's predicted
  direction ("below materiality") is not supported on these two corpora; the KME-L run keeps the split visible. CE P and
  G terminals are both open at this history (`consumed_owner_verdicts` null), so R2 for H is not satisfiable yet.
- **I (subagent bootstrap).** 11 subagent files on KME-G boot at a median 125,746 tokens of first-call context
  (min 124,905, max 128,739; total 1,393,005) against a main-thread first call of median 184,030 (about 68 %); all 11
  first calls are cold (cache_write > cache_read). Numerator 4,535,326 weighted = **8.26 %**; 17.25 % on GEX44-B001.
  Both clear 3 %, which is evidence for the CE B / SC A-C handoff the frozen rule asks for; no rule or skill moves here.
- **Instrument facts.** A stat-pinned copy of the a5 / a7 / b001 trees reproduces the frozen audit byte for byte; the
  frozen KME-G population reproduces exactly at the freeze instant; the 24-hour cutoff locator is bounded at 24 scans
  total and refuses a calls-only match.

## Named debts

- **Six KME-L runs pending** (owner bundle `[D]`..`[I]`, laptop plane, NOT RUNNABLE HERE): until each `<P>-KME-L-*.md`
  lands with an exact population, no terminal exists. D additionally needs `D-CPP-D-W7`; E needs its CPP-D-W7 (or other
  valid) second workload if the primary says `second_workload_required: true`.
- **The P0 KME-L project-dir list was never recorded.** The population proof therefore starts unfiltered over the whole
  projects root; if it reads not-exact, the Owner must settle the roots from its `per_project` rows (bundle text).
- **D-W7 parser difference** (above): coverage >= 1 does not prove the same call set; every D-W7 file says so.
- **G precision** is measured only by a hand sample, and on KME-G that sample is empty; the KME-L file's 20-sample audit
  must be checked by hand and its precision recorded before any slice.
- **H's R2** waits on CE P and G terminals on this history (both open here); I's R2 waits on CE B and SC B terminals.
- **Second-workload independence for E is argued at close time**: R3 accepts a valid KME-G or named-workload second
  workload beside a terminal KME-L primary and cannot judge independence; `evidence/E.md` must.
- The chars-per-token interval (3.0..4.5) and the single-write residency model are estimates, stated in every file's
  `estimate_model`; the G classifier is heuristic (interval output); the F doc classes are path-based.

## Status: OPEN

Ledger `state.D` .. `state.I` are NOT written, IC-D .. IC-I are not ticked, and no pillar is closed. Each terminal waits
for its laptop KME-L file (`owner-bundle.md`, items `[D]`..`[I]`); until then `--pillar D` .. `--pillar I` print
`ICP_PILLAR_<P>=FAIL` ("no terminal disposition"), as expected.
