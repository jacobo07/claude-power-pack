# Pillar N -- closeout (UKDL three levels, CBR, deltas): evidence

Plane: GEX44 `kobicraft-gex44` (Linux 6.8, user `kobii`), `python3` 3.12.3, branch `mission/incremental-cognition-run`,
HEAD `1a1ad30e0439c10b92bb7cb1af403deec6a894c9` at measurement, worktree
`/home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run`. Measured 2026-10-04, foreground, from the worktree
root. Nothing here was run on the laptop. Nothing was promoted into the UKDL or a CBR family.

## Frozen rule (verbatim from ledger.json, frozen.pillars id N)

> candidates go to vault/programs/incremental-cognition/ukdl-candidates.md; promotion into ukdl-universal.md and CBR is reviewed, never silent

Predicted terminal: `MERGED_INTO_EXISTING_OWNER`. Owners of the rule: `vault/knowledge_base/ukdl-universal.md` and `tools/baseline_ledger.py`. The rule has two
halves: the candidates are in the program's own file, and promotion is reviewed, never silent. The mission can do the
first half and make the second unable to be silent; the promotion itself, and institutional garbage collection (CE pillar
T), are not the mission's to do. So pillar N is addressed here and is not closed.

## What was reviewed

- `vault/programs/incremental-cognition/ukdl-candidates.md`: 16 candidate learnings of this run at three levels: 6 universal, 6 domain, 4 project, each with
  evidence refs that resolve at HEAD (67 refs, checked by V-ICN-EVIDENCE-RESOLVES).
- `vault/programs/incremental-cognition/reviews/ukdl.md`, verdicts per candidate: 4 PROMOTE-PROPOSED (IC-U-01, IC-U-04, IC-U-06, IC-D-01), 11 HOLD, 1 REJECT
  (IC-U-02, a duplicate of `T-COMMIT-IS-NOT-INSTALL-WHEN-THE-INSTALL-IS-A-WORKING-TREE-001`).
- `vault/programs/incremental-cognition/reviews/cbr.md`, verdicts per candidate: 2 HOLD (the two performance candidates, held by the frozen transfer rule)
  and 14 REJECT, every row filed against the family `none`; no candidate is promotable to a CBR family.
- Duplicate sweep: 16 lines in `reviews/ukdl.md` (`- <id>: <command> -> <n> hits`), one per candidate.
- `## Promotions recorded`: none in either review. `vault/knowledge_base` and `vault/tower` are byte-identical to the
  phase base (`git diff --quiet` over both exits 0).
- Transfer rule, quoted byte for byte in `reviews/cbr.md` and checked against `frozen.materiality.transfer` by
  V-ICN-CBR-TRANSFER-RULE: a performance guarantee promoted to CBR needs a second, materially independent workload.

## Ledger reviews and deltas

Only the `reviews` and `deltas` members of `vault/programs/incremental-cognition/ledger.json` changed over plan 06-04 (`frozen` and every `state.<P>` are
untouched; `state.N` is `{}`). Over the plan, `git diff <plan base> HEAD -- vault/programs/incremental-cognition/ledger.json` removes exactly these two
lines and no others:

```
- "reviews": {"ukdl": null, "cbr": null},
- "deltas": {"product": [], "intelligence": []}
```

Reviews, pinned as `{file, sha256}` (LF sha256, checked by V-ICN-LEDGER-REVIEWS-PINNED):

```
reviews.ukdl  596bc6edde3e74695c8ac190d43d0e91018b1d79479b880cfd2f29e51dc23acd  vault/programs/incremental-cognition/reviews/ukdl.md
reviews.cbr   7de41a07004b4f1ae3a316fa2324892dcf75e1e0cb8c37788f9bc96e456c24bd  vault/programs/incremental-cognition/reviews/cbr.md
```

Deltas: 8 product and 9 intelligence entries, phases 1 to 6, each with
reachable program commits and evidence `{ref, sha256}` (checked by V-ICN-LEDGER-DELTAS and
V-ICN-LEDGER-DELTAS-COVER-PHASES):

| id | phase | pillars | plane |
|----|-------|---------|-------|
| product-1-A-relay-follows-a-proven-worktree | 1 | A | gex44 |
| product-2-C-park-and-resume | 2 | C | gex44 |
| product-2-B-preflight-deploy-launch-gate | 2 | B | gex44 |
| product-3-DI-kme-instrument | 3 | D,E,F,G,H,I | gex44 |
| product-4-K-floor-regression-gate | 4 | K | gex44 |
| product-5-L-replay-ranker-and-bundle | 5 | L | gex44 |
| product-6-JM-r2-evidence-printer | 6 | J,M | gex44 |
| product-6-N-candidate-reviews | 6 | N | repo |
| intelligence-1-A-gex44-gate-counts | 1 | A,B | gex44 |
| intelligence-2-C-classification-and-inheritance | 2 | C | gex44 |
| intelligence-2-B-measured-env-facts | 2 | B | gex44 |
| intelligence-3-DEF-kme-g-smoke | 3 | D,E,F | gex44 |
| intelligence-3-GHI-kme-g-smoke | 3 | G,H,I | gex44 |
| intelligence-4-K-floor-facts | 4 | K | gex44 |
| intelligence-5-L-kme-g-smoke-ranking | 5 | L | gex44 |
| intelligence-6-JM-owner-blocked | 6 | J,M | gex44 |
| intelligence-6-N-review-facts | 6 | N | repo |

Every KME-G figure in the deltas is labelled smoke; every ranking figure is an upper bound; the phase 1 to 5 entries are
taken from the committed evidence files they cite, the phase 6 entries from `evidence/JM-blocked.md`, `06-01-SUMMARY.md`
and `06-03-SUMMARY.md`. No delta names a terminal and none claims that a pillar closed.

## Done-gate run

`python3 tools/test_incremental_cognition_program.py --status` (exit 0):

```
{
 "open": [
  "A",
  "B",
  "C",
  "D",
  "E",
  "F",
  "G",
  "H",
  "I",
  "J",
  "K",
  "L",
  "M",
  "N"
 ],
 "closed": [],
 "violations": []
}
```

`python3 tools/test_incremental_cognition_program.py --final` (exit 1, as expected), verbatim:

```
  INCONCLUSIVE V-ICP-REAL-OWNER-READ: fa9ae2ed / 21671d6c not in this clone
  FAIL L3 A: no terminal disposition
  FAIL L3 B: no terminal disposition
  FAIL L3 C: no terminal disposition
  FAIL L3 D: no terminal disposition
  FAIL L3 E: no terminal disposition
  FAIL L3 F: no terminal disposition
  FAIL L3 G: no terminal disposition
  FAIL L3 H: no terminal disposition
  FAIL L3 I: no terminal disposition
  FAIL L3 J: no terminal disposition
  FAIL L3 K: no terminal disposition
  FAIL L3 L: no terminal disposition
  FAIL L3 M: no terminal disposition
  FAIL L3 N: no terminal disposition
CEP_VERDICT=FAIL failures=14
  FAIL CE clauses failed (rc 1)
ICP_VERDICT=FAIL failures=1
```

`python3 tools/test_incremental_cognition_program.py --pillar N` (exit 1), verbatim:

```
  FAIL L3 N: no terminal disposition
CEP_PILLAR_N=FAIL
ICP_PILLAR_N=FAIL
```

Reading, in plain words. `--final` fails, as expected, on the fourteen open pillars and on nothing else: fourteen
`FAIL L3 <P>: no terminal disposition` lines (A to N). Before plan 06-04 it printed four more lines (`FAIL L8 review ukdl`,
`review cbr`, `delta product`, `delta intelligence`) and `CEP_VERDICT=FAIL failures=18`; those four are gone, so the review
and delta clause (CE clause L8) is now satisfied, and the count is 14. The first line is an INCONCLUSIVE, not a pass:
the CE phase-1 commits `fa9ae2ed` / `21671d6c` are not in this clone, so the real owner read is not made here. No pillar is
closed on this host and none is claimed; `--status` lists all fourteen as open with `"violations": []`.

Other gates, run fresh in this plan, last line of each:

| command | exit | last line |
|---------|------|-----------|
| `python3 tools/test_incremental_cognition_program.py --selftest` | 0 | `ICP_SELFTEST=PASS` |
| `python3 tools/test_ic_closeout.py` | 0 | `ICN_PASS=11/11  threshold=11/11  skipped=0  inconclusive=0` |
| `python3 tools/test_ic_closeout.py --drill` | 0 | `DRILL killed=12/12` |
| `python3 tools/test_ic_r2_evidence.py` | 0 | `ICR2_PASS=14/14  threshold=14/14  skipped=0  inconclusive=0` |
| `python3 tools/test_ic_r2_evidence.py --drill` | 0 | `DRILL killed=6/6` |
| `python3 tools/test_kme_replay.py` | 0 | `KMER_PASS=45/45  threshold=45/45  skipped=0  inconclusive=0` |
| `timeout 300 python3 tools/test_kme_pillars.py` | 0 | `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0` |
| `timeout 300 python3 tools/test_floor_regression_gate.py` | 0 | `FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0` |

## Baseline, vault, institutional GC

- Baseline: the owner of the baseline axes is `tools/baseline_ledger.py` (axes `k_qa`, `k_router`, `engineering_baseline`,
  `highest_dna`; its ledger is `~/.claude/vault/global_baseline_ledger.json`). This program moved none of them: the file is
  byte-identical to the phase base, was not run, and no command of this plan targets `~/.claude`.
- Vault: the program's vault artifacts are `vault/programs/incremental-cognition/ukdl-candidates.md`, `vault/programs/incremental-cognition/reviews/`, `vault/programs/incremental-cognition/evidence/`,
  `vault/programs/incremental-cognition/measurements/`, `vault/programs/incremental-cognition/owner-bundle.md` and `vault/programs/incremental-cognition/ledger.json`. The UKDL (`vault/knowledge_base/ukdl-universal.md`) and
  `vault/tower` were not touched by any commit of plan 06-04 (checked below).
- Institutional garbage collection is CE pillar T (`modules/liveness/reachability.py`, predicted `AUTHORIZATION_BOUND`,
  external to this program). Its state in `vault/programs/cognitive-economy/ledger.json` at HEAD reads
  `{'terminal': None, 'evidence': [], 'savings': []}`: open. This program does not do it.

## Liveness

Aperture, quoted from `python3 modules/liveness/reachability.py`: "APERTURE: packages under `modules/` only. `tools/` is
NOT scanned, so nothing below is evidence about the verification runner, the benchmarks, the commit wrapper or the hunk
guard." The tools of this phase live under `tools/`, so the sweep says nothing about them. Measured on GEX44,
`timeout 120 python3 modules/liveness/reachability.py --json`: exit 1, 490 modules, 64 offenders (pre-existing; this
program added no module). The phase-own proof: `git diff --name-only 23979ec2 HEAD -- modules hooks commands agents
SKILL.md CLAUDE.md vault/liveness` prints nothing, and none of this phase's own commits (15 at measurement, subject scope
`incremental-cognition`, `06` or `06-0N`, since `23979ec2`) touches those paths (`phase-own 15 touching liveness paths []`).
How the new tools are reached: by their own tests (`tools/test_ic_r2_evidence.py`, `tools/test_ic_closeout.py`, each with a
mutation drill), by the owner-bundle `[J]`, `[M]` and `[N]` lines, and by the done-gate's `--pillar` R2 wiring. No hook or
CI job runs `tools/test_ic_closeout.py`.

## Artifacts (LF sha256)

```
bd44d268b10635304a57d46c072dc4c2c6082b65b71789a7dd826b692b5d6607  vault/programs/incremental-cognition/ukdl-candidates.md
596bc6edde3e74695c8ac190d43d0e91018b1d79479b880cfd2f29e51dc23acd  vault/programs/incremental-cognition/reviews/ukdl.md
7de41a07004b4f1ae3a316fa2324892dcf75e1e0cb8c37788f9bc96e456c24bd  vault/programs/incremental-cognition/reviews/cbr.md
973218db57169604208209ef6f2d9fa3a5048b78bd082ef3ed8fc5d16cc38377  vault/programs/incremental-cognition/ledger.json
25204924c93c1ca12e0bcfdd0dd22cf503840b86146eaa675c7705dd79537d6e  tools/test_ic_closeout.py
4a71977780290054015c5b69854c4a5c7300e061e94c0b7a3149234e4b73dc84  tools/ic_r2_evidence.py
6af6b02e2188ef65804bb8580f8f61225d65347021f1580f4cd997b5f26fed4d  tools/test_ic_r2_evidence.py
0b601dce5c8af643ac7c111c7f434fc8fe32ab98c3753a29653200506afcdfb2  vault/programs/incremental-cognition/evidence/JM-blocked.md
```

(`hashlib.sha256` over the file bytes with CRLF folded to LF, the CE verifier's `lf_sha256`.)

## Product Delta

What the Owner can now do: print the exact R2 rows the day the cognitive-economy and skill-capability pillars land a
terminal (`python3 tools/ic_r2_evidence.py --pillar <J|M> --commit HEAD`) and trust `--pillar` to check them; read this
run's learnings reviewed at three levels, with one promotion action in the owner bundle (`[N]`), and see a promotion that
was not recorded turn the closeout gate red; see every shipped phase in the ledger deltas, each tied to committed evidence
and reachable program commits, with a gate that turns red the day a phase ships without one.

## Intelligence Delta

Measured facts, each with its source:

- The owner ledgers (cognitive-economy and skill-capability) carry no terminal for any pillar on this history, so R2 for
  pillars J and M cannot be satisfied here (`evidence/JM-blocked.md`).
- The per-pillar done-gate did not run R2 before plan 06-01: a J terminal with a misquoted owner terminal printed
  `ICP_PILLAR_J=PASS`. It runs R2 now, and `V-ICP-R2-PILLAR-MODE` holds it (`06-01-SUMMARY.md`).
- 16 candidates, 4 PROMOTE-PROPOSED / 11 HOLD / 1 REJECT for the UKDL and 2 HOLD / 14 REJECT for CBR (`reviews/ukdl.md`,
  `reviews/cbr.md`, counted above).
- What `--final` says now: failures 14 (fourteen open pillars), the four review and delta lines gone, the first line
  INCONCLUSIVE because two CE commits are not in this clone.

## Named debts

- Promotion into the UKDL and CBR is the Owner's `[N]` item; this run promoted nothing.
- Pillars J and M wait on the cognitive-economy and skill-capability terminals; the R2 rows can be printed only after them.
- Institutional garbage collection is CE pillar T (external, open at HEAD).
- `tools/` is outside the liveness scanner's aperture.
- No hook or CI job runs `tools/test_ic_closeout.py`; it runs when someone runs it.
- Every pillar (A to N) is open on this host (`--status`: `"closed": []`); what each one waits for is the Owner item or
  the owner program named for it in `owner-bundle.md`.

## Status: OPEN

Ledger `state.N` is not written by this mission run and IC-N is not ticked; `requirements.mark-complete` was not called.
