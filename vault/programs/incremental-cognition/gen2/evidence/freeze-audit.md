---
programme: IC-gen2 autonomous-optimization
plane: gex44
head: 755177676b81ef6d430cd35c634193c77cdce893
audited_at: 2026-10-06T14:31:00Z
---

# IC-gen2 pre-freeze audit record

Spec of record: `vault/specs/autonomous-optimization.md` (covers entry `ic-gen2-freeze`). This record is written before
commit A (the pre-registration commit) and is part of it. Every command below was run in a fresh process on plane
gex44 against the uncommitted pre-registration at HEAD 75517767, in the order listed.

Fix round 1 of 2: the first run (HEAD f616bc4f, record already on disk) was red on `--generation 2 --audit`: the
selftest mutant `V-IC2-MUT-A7-frozen-without-record` SURVIVED because the real repo now held the record, so A2 failed
(`ICP_GEN2_AUDIT=FAIL ... failures=1`). The defect was in `tools/ic_gen2.py` (the fixture resolver could not hide a real
path), not in `frozen`; it was fixed in commit 75517767 and the whole sequence below was re-run from the start. No
`frozen` text changed, so the sha256 below is the one plan 00-04 recorded.

## Suite

| command | exit code | summary line |
|---|---|---|
| `python3 tools/test_ao_p0.py` | 0 | AOP0_PASS=22/22  threshold=22/22 |
| `python3 tools/test_gex44_env_preflight.py --drill` | 0 | DRILL killed=10/10 |
| `python3 tools/test_gex44_env_preflight.py` | 0 | ENVPF_PASS=64/64  threshold=64/64 |
| `python3 tools/test_persistent_failure_park.py` | 0 | PFP_PASS=28/28  threshold=28/28 |
| `python3 tools/test_mission_launch_gate.py` | 0 | LG_PASS=20/20  threshold=20/20 |
| `python3 tools/test_incremental_cognition_program.py --selftest` | 0 | ICP_SELFTEST=PASS |
| `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` | 0 | ICP_GEN2_SELFTEST=PASS |
| `python3 tools/test_incremental_cognition_program.py --generation 2 --status` | 0 | {"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []} |
| `python3 tools/test_incremental_cognition_program.py --generation 2 --audit` | 0 | A7 ok (not frozen yet); verdict line in the Audit section below |
| `python3 tools/test_incremental_cognition_program.py --generation 2 --final` | 1 | ICP_GEN2_VERDICT=FAIL failures=10 |
| `python3 tools/gex44_env_preflight.py --current --checks pp_install` | 0 | PREFLIGHT=READY reasons=- |

The `--final` row is the expected pre-freeze red (exit 1, exactly 10 lines: L2 not frozen, L3 for M O P Q R, four L8
lines), reported below verbatim and never counted as a pass.

## Audit

Output of `python3 tools/test_incremental_cognition_program.py --generation 2 --audit` (exit 0):

```
A1 ok status problems empty (CE L1-L9/X under the gen2 binding + G2 rules)
A2 ok gen2 selftest passes
A3 ok final-mode failure set equals the expected open-programme set (10 lines, pre-freeze)
A4 ok roadmap_phases equal the ROADMAP checklist: M[4, 6], O[1], P[2, 6], Q[3], R[5, 6]
A5 ok 10 frozen owner paths tracked
A6 ok 79 gen2-authored frozen strings carry no deferral word and no placeholder
A7 ok (not frozen yet)
ICP_GEN2_AUDIT=PASS frozen_sha256=a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e
```

## Expected red

Output of `python3 tools/test_incremental_cognition_program.py --generation 2 --final` (exit 1):

```
  FAIL L2 not frozen: FROZEN_AT missing, the pre-registration was never committed
  FAIL L3 M: no terminal disposition
  FAIL L3 O: no terminal disposition
  FAIL L3 P: no terminal disposition
  FAIL L3 Q: no terminal disposition
  FAIL L3 R: no terminal disposition
  FAIL L8 review ukdl: missing or its file does not exist
  FAIL L8 review cbr: missing or its file does not exist
  FAIL L8 delta product: empty
  FAIL L8 delta intelligence: empty
ICP_GEN2_VERDICT=FAIL failures=10
```

## Criteria to rules

Independent read of `frozen` (D-OQ4): each success criterion of ROADMAP Phases 1-6 (24 in total: 4, 5, 3, 4, 3, 5,
re-counted from `ROADMAP.md` "Phase Details") against the clause of the pillar rule that carries it. Each quoted clause
is a verbatim substring of that pillar's `rule` in `gen2/ledger.json`; a criterion may have more than one carrying row.

| pillar | criterion | clause |
|---|---|---|
| O | 1.1 | "(1) tools/usage_index.py schema v5 adds tool events (tool, input hash, path, result bytes), cwd, project/workstream attribution (mixed allowed) and realpath + content identity via tools/tis_observed.py store_identity" |
| O | 1.1 | "(2) the v4 -> v5 migration re-reads zero already-ingested files, measured" |
| O | 1.2 | "(3) six negative controls go red when they should: a mixed-project session attributed to both projects, two distinct histories not merged, a junction alias counted once, _archived handled by a declared rule, a parser failure surfaced and never a silent zero, an empty population refusing a verdict" |
| O | 1.3 | "(4) population parity with the frozen KME-L denominator (102 sessions / 34,871 calls / cache_read 11,549,646,300) on the GEX44 corpus copy /home/kobii/kme-corpus/projects, dedup reconciled to the unit, labelled plane gex44" |
| O | 1.4 | "(5) refresh cost (wall, bytes) measured for a cold build and for a delta" |
| P | 2.1 | "(1) the kme_pillars access plan is certified index -> project-scoped raw -> global raw only on an explicit cross-project question, a guard failure deopts with a logged reason, and invalidation is keyed on source watermark, parser version, attribution version and metric definition" |
| P | 2.2 | "(2) the 7 KME-L measurement files (D, E, F, G, H, I, L) reproduce identically from the challenger" |
| P | 2.3 | "(3) a champion vs scoped vs challenger table (wall, raw bytes, unique bytes, raw files opened, cross-project bytes exposed) is measured against frozen champion run5 and run6" |
| P | 2.3 | "(4) a KME-only query opens zero CostaLuz bytes and a negative control proves that check can fail" |
| P | 2.4 | "(5) changing a source or the parser version invalidates exactly the affected closure" |
| P | 2.5 | "Allowed loss (D-OQ4): if the challenger does not beat the scoped path on repeated queries, P closes FALSIFIED_OR_REJECTED_BY_EVIDENCE with a falsification artifact naming [P] (IC-gen2) that carries the table" |
| P | 2.5 | "A narrowed challenger closes IMPLEMENTED_AND_VERIFIED only for the narrowed scope named in its reason and evidence" |
| Q | 3.1 | "(1) detectors extend CO-12 (modules/cognitive_os/co_12_telemetry.py record_signal) with no new top-level component and cover read amplification (same path + content read N times), scan amplification (bytes read / evidence consumed), a repeated identical command with unchanged inputs, a retry without causal delta, and a model call answering a deterministic question" |
| Q | 3.1 | "(2) counters are cheap and always on, with detail only on anomaly" |
| Q | 3.2 | "(3) the discovery eval finds the KME-L hotspot without any KME-specific signature, finds one seeded hotspot, does not flag one known no-optimization case, rejects one low-ROI case, and reports detected / missed / false positive counts" |
| Q | 3.3 | "(4) detector overhead is measured" |
| M | 4.1 | "(1) opportunity rows live in the existing ledger convention, no new database, and carry evidence, scope, workload class, frequency, current cost, hypothesis, owner search result, predicted dividend, build + proof + carrying cost, risk, reversibility, champion, challenger, status, retirement condition and realized dividend" |
| M | 4.2 | "(2) lifecycle states observed, priced, shadow, canary, certified, promoted plus rejected, narrowed, superseded, retired, with a test that refuses a direct jump to promoted" |
| M | 4.3 | "(3) the autonomy envelope (derived, index, cache and reversible tooling autonomous; architecture, authority, global settings and irreversible actions to the owner bundle) is driven from both sides by tests" |
| M | 4.4 | "(4) every opportunity has a budget and a branch whose predicted payback deteriorates is re-evaluated or stopped and recorded" |
| R | 5.1 | "(1) the loop itself raises, prices and accepts the next candidate from detector output without the Founder naming it (expected tools/sovereign_miner.py, the only automatic full-corpus parse; the detectors' first-ranked candidate wins if reality offers better, with the ranking recorded)" |
| R | 5.2 | "(2) shadow agreement is measured, a canary runs on the GEX44 corpus copy, and certification carries a realized dividend measured on a named denominator" |
| R | 5.3 | "(3) the laptop scheduled-task deploy is an owner-bundle [R] (IC-gen2) line" |
| P | 6.1 | "(6) the certified path is promoted through modules/tower/ratchet.promote at project scope" |
| R | 6.1 | "(4) family-scope promotion of the anti-rescan principle through modules/tower/ratchet.promote happens only if this transfer evidence supports it" |
| P | 6.2 | "a fresh worker asked a KME question without naming the index takes the index path (the path log shows the hit)" |
| P | 6.3 | "bypassing the index turns a gate red" |
| M | 6.4 | "(5) a predicted dividend is never labelled realized, and the measured overhead of index refresh plus detectors stays below the realized savings, both with commands" |
| M | 6.5 | "(6) the Production Reality probe shows real CLI -> real substrate -> measured effect" |
