# Phase 0 Evidence: Spec, gen2 freeze, novelty gate

Commit A (pre-registration): `afcdceea302c8662b6b8c87c30d6eb8ed8dcba18`. Commit B (FROZEN_AT only): `8752562a42c9e82aefe18bd1fe9c211fc262f229`. Branch `mission/autonomous-optimization-gen2`. Plane: gex44. Spec of record: `vault/specs/autonomous-optimization.md`. Every output below is from a fresh process run at HEAD `8752562a` (after commit B), except where a row names another commit.

## Criterion results

| ROADMAP Phase 0 criterion | artifact | proof command | observed line |
|---|---|---|---|
| 1. T3 spec with `covers:`, PRD, arch, acceptance, rollback, kill switches | `vault/specs/autonomous-optimization.md` | `python3 tools/test_ao_p0.py` | `PASS V-AOP0-SPEC-READY  state=READY missing=[]`; `AOP0_PASS=22/22  threshold=22/22` |
| 2. gen2 ledger + FROZEN_AT, pillars M O P Q R, gen1 `frozen` untouched, wrapper judges gen2, a mutant per rule | `vault/programs/incremental-cognition/gen2/ledger.json`, `gen2/FROZEN_AT` | `python3 tools/test_incremental_cognition_program.py --generation 2 --status`, `--generation 2 --selftest` | `{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}`; `ICP_GEN2_SELFTEST=PASS` (66 `killed by` lines in that run) |
| 3. novelty check recorded, EXTEND_EXISTING_OWNER with file:line evidence from a discovered sweep | `vault/audits/autonomous-optimization-novelty-2026-10-05.md` | `python3 tools/test_ao_p0.py` | `PASS V-AOP0-NOVELTY-13  13 rows in order against NOVELTY_PROOF_QUESTIONS; problems=[]`; `PASS V-AOP0-NOVELTY-CITES-RESOLVE  33 citations resolved; problems=[]`; `PASS V-AOP0-NOVELTY-VERDICT  problems=[]` |
| 4. champion numbers frozen with their commands (Run 5, Run 6) | `gen2/ledger.json` `frozen.champion`, `gen2/evidence/champion/` | `python3 tools/test_incremental_cognition_program.py --generation 2 --status` (G2-CHAMP re-derives every number from the pinned copies; a violation would be listed) | `{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}` |
| 5. instrument fix found while arming, recorded as an opportunity row | `tools/gex44_env_preflight.py`, `gen2/evidence/OPP-001-pp-install-hash-floor.md`, `opportunities[OPP-001]` | `python3 tools/test_gex44_env_preflight.py --drill`; `python3 tools/gex44_env_preflight.py --current --checks pp_install` | `DRILL killed=10/10`; `READY        pp_install    head 8752562a contains the floor 5962571c via cherry_pick_trailer` |

## Verifier output (fresh processes, after 8752562a)

`python3 tools/test_ao_p0.py` (exit 0)
```
AOP0_PASS=22/22  threshold=22/22
```

`python3 tools/test_gex44_env_preflight.py --drill` (exit 0)
```
DRILL killed=10/10
```

`python3 tools/test_gex44_env_preflight.py` (exit 0)
```
ENVPF_PASS=64/64  threshold=64/64
```

`python3 tools/gex44_env_preflight.py --current --checks pp_install` (exit 0)
```
READY        pp_install    head 8752562a contains the floor 5962571c via cherry_pick_trailer
PREFLIGHT=READY reasons=-
```

`python3 tools/test_persistent_failure_park.py` (exit 0)
```
PFP_PASS=28/28  threshold=28/28
```

`python3 tools/test_mission_launch_gate.py` (exit 0)
```
LG_PASS=20/20  threshold=20/20
```

`python3 tools/test_incremental_cognition_program.py --selftest` (exit 0)
```
CEP_SELFTEST=PASS
ICP_GEN2_SELFTEST=PASS
ICP_SELFTEST=PASS
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` (exit 0)
```
ICP_GEN2_SELFTEST=PASS
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --status` (exit 0)
```
{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --audit` (exit 0)
```
A7 ok recorded frozen_sha256 equals the live one
ICP_GEN2_AUDIT=PASS frozen_sha256=a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --final` (exit 1, expected: nine open-programme lines, no L2)
```
  FAIL L3 M: no terminal disposition
  FAIL L3 O: no terminal disposition
  FAIL L3 P: no terminal disposition
  FAIL L3 Q: no terminal disposition
  FAIL L3 R: no terminal disposition
  FAIL L8 review ukdl: missing or its file does not exist
  FAIL L8 review cbr: missing or its file does not exist
  FAIL L8 delta product: empty
  FAIL L8 delta intelligence: empty
ICP_GEN2_VERDICT=FAIL failures=9
```
This is a red verdict, reported as red. The nine lines are the open pillars (their terminal dispositions belong to Phases 1-6) and the closeout reviews and deltas (Phase 7).

## Inherited gen1 state (D-OQ3)

`python3 tools/test_incremental_cognition_program.py --final` (exit 1), run at HEAD `8752562a`. The first twelve lines belong to the CE program judged by the wrapper (`CEP_VERDICT`), then the IC gen1 line, then the gen2 block (the same nine lines as above):
```
  FAIL L3 A: no terminal disposition
  FAIL L3 B: no terminal disposition
  FAIL L3 C: no terminal disposition
  FAIL L3 I: no terminal disposition
  FAIL L3 J: no terminal disposition
  FAIL L3 K: no terminal disposition
  FAIL L3 M: no terminal disposition
  FAIL L3 N: no terminal disposition
  FAIL L8 review ukdl: missing or its file does not exist
  FAIL L8 review cbr: missing or its file does not exist
  FAIL L8 delta product: empty
  FAIL L8 delta intelligence: empty
CEP_VERDICT=FAIL failures=12
  FAIL CE clauses failed (rc 1)
ICP_VERDICT=FAIL failures=1
```
These are inherited gen1 state: they are not claimed green, and no gen1 file was edited (`git diff --quiet 3f48f2e3 HEAD` over gen1 `ledger.json`, gen1 `FROZEN_AT`, both CE/SC ledgers, both CE/SC verifiers, root `.planning/STATE.md` and `tools/gsd_mission.py` exits 0). The programme done-gate is `--generation 2 --final` PASS plus the Phase 6 Production Reality probe, not the wrapper's combined exit code.

## Freeze

- SHA_A (pre-registration commit) `afcdceea302c8662b6b8c87c30d6eb8ed8dcba18`; it adds only `gen2/evidence/freeze-audit.md` (108 insertions, `git show --stat`). The `frozen` object of `gen2/ledger.json` at SHA_A hashes to the recorded value (`ic_gen2.frozen_sha256` over `git show afcdceea:vault/programs/incremental-cognition/gen2/ledger.json`) and the ledger file is byte-identical to the working copy.
- SHA_B (FROZEN_AT) `8752562a42c9e82aefe18bd1fe9c211fc262f229`; `git show --stat --format= HEAD` lists only `vault/programs/incremental-cognition/gen2/FROZEN_AT`, one insertion; its content equals `git rev-parse HEAD~1`.
- Frozen sha256: `a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e` (the `--generation 2 --audit` line above; A7 compares it with the record in `gen2/evidence/freeze-audit.md`).
- L2 live drill (command: `python3 -c 'import sys, copy; sys.path.insert(0, "tools"); import ic_gen2, test_cognitive_economy_program as ce; led = ic_gen2.load_ledger(); bad = copy.deepcopy(led); bad["frozen"]["pillars"][1]["rule"] += " (edited)"; good = [x for x in ic_gen2.problems(led, None, False) if x.startswith("L2")]; red = [x for x in ic_gen2.problems(bad, None, False) if x.startswith("L2")]; print(good, red); raise SystemExit(0 if not good and red else 1)'`, exit 0; the plan signature `problems(led, None, False)` worked unchanged) printed: `[] ['L2 frozen pre-registration differs from its copy at FROZEN_AT']`. The unedited ledger has no L2 problem; the edited in-memory copy is refused.
- Pre-freeze fix round 1 of 2: the audit went red once the record existed (see Intelligence Delta); the fix is commit `75517767`, `frozen` was not touched.
- The 24 ROADMAP criteria of Phases 1-6 map to verbatim clauses of the frozen pillar rules: 29 rows in `gen2/evidence/freeze-audit.md`, checked by the Task 1 verify one-liner (`29 [] []`, exit 0).

## Opportunity OPP-001

Row `opportunities[OPP-001]` in `gen2/ledger.json` (outside `frozen`): status `priced`, `realized_dividend` null (read with `python3 -c` over the ledger). Predicted dividend: 1 owner waiver avoided per default-env re-arm (basis: predicted from the measured false positive, not yet observed on the live install). Next transition: "canary: the live GEX44 install's own preflight reads READY after its normal fast-forward sync". Evidence file `gen2/evidence/OPP-001-pp-install-hash-floor.md`; fix commits `ea8c51f6`, `62152c0b`, `21bafb5d`. Its realized effect on the live install is UNMEASURED.

## Ownership (AO-01)

Extended, by path (not created): `tools/gex44_env_preflight.py` and `tools/test_gex44_env_preflight.py` (pp_install accept paths, drill M7-M10), `tools/test_incremental_cognition_program.py` (the IC wrapper: `--generation 2`, `--audit`), the IC program ledger convention under `vault/programs/incremental-cognition/` (the gen2 ledger), `vault/specs/autonomous-optimization.md` and the HR-NOVELTY-001 record under `vault/audits/`. The only new code files of the phase are `tools/ic_gen2.py` and `tools/test_ao_p0.py`. No new modules package, runtime, database or ratchet was added: `git diff --name-only --diff-filter=A 3f48f2e3 HEAD -- modules` prints nothing.

## Product Delta

- The default GEX44 environment no longer reads `pp_install_stale` on a picked install: `python3 tools/gex44_env_preflight.py --current --checks pp_install` prints `PREFLIGHT=READY reasons=-` (via `cherry_pick_trailer`), and `python3 tools/test_gex44_env_preflight.py` is `ENVPF_PASS=64/64` where plan 00-02 measured 55/57 at its start (`two inherited reds`). The live install itself changes only through its fast-forward sync.
- `python3 tools/test_incremental_cognition_program.py --generation 2 --status|--selftest|--audit|--final` now judges the programme; the wrapper `--selftest` folds it in (`ICP_GEN2_SELFTEST=PASS`).
- The champion numbers (Run 5 869 s / 101.53 GB, Run 6 24 s / 2.83 GB; ratios 36.2 and 35.9 from `frozen.champion.ratios_derived`) are re-derivable from pinned evidence copies on every `--generation 2 --status` run (violations `[]`).
- Pillars M, O, P, Q, R are frozen with their predicted terminal and rule; a later phase cannot weaken one without `L2 frozen pre-registration differs from its copy at FROZEN_AT` (drill above).

## Intelligence Delta

- The `PP_COMMIT_FLOOR` object `5962571c` is absent on GEX44 (`floor_present: false` in the `--json` output of the preflight, plan 00-02), so only the cherry-pick trailer path can accept there; the patch-id path needs the object (hence the `[P0]` owner-bundle line).
- The drill counted an already-red gate as a kill; M3 was retargeted to `V-ENVPF-PP-STALE-NOT-ANCESTOR` (plan 00-02; drill `DRILL killed=10/10`).
- `covers:` ties between a spec and a plan block T2+ tasks (plan 00-01 `V-AOP0-MUT-covers-tie`, `PASS` in the `test_ao_p0.py` run above; a plan tied with the spec is AMBIGUOUS, so task text names the spec literally).
- CE globals can judge a second ledger only through a restoring context manager (`ic_gen2.bound()`, `V-IC2-BINDING-RESTORED`).
- The IC done-gate cannot reach exit 0 from this programme alone because gen1 stays red (`ICP_VERDICT=FAIL failures=1` above), hence D-OQ3.
- A selftest whose mutant reads the real repo fails the moment the audit record is written: `V-IC2-MUT-A7-frozen-without-record SURVIVED` made A2 (selftest passes) red, `ICP_GEN2_AUDIT=FAIL ... failures=1`. The fixture resolver now hides a path when `files[path]` is None (commit `75517767`); the same gate then passed both pre-freeze and in a simulated post-freeze state. The audit gate's own A2 rule is what caught it before the one-way step.
- Plan 00-04 found that argv equality (not substring) is the right comparison for the Run 6 command, and that A7 must refuse FROZEN_AT without an audit record (00-04 SUMMARY key-decisions).
- A first audit of the real ledger found no A-rule failure, so the 24-criterion read changed no `frozen` text; every criterion had a carrying clause (29 rows).

## Limits and open items

- The `[P0]` patch-id owner-bundle line (`gen2/owner-bundle.md`) is requested, not granted: on GEX44 the patch-id path cannot accept because the floor object is absent.
- The live GEX44 install `4856b50d` receives the pp_install fix only through its fast-forward sync, so OPP-001's realized effect is UNMEASURED.
- Gen1 red pillars A, B, C, I, J, K, M, N and the four gen1 L8 lines stay red (`CEP_VERDICT=FAIL failures=12`, `ICP_VERDICT=FAIL failures=1`).
- The IC wrapper's R4 owner-decision check recognises only the gen1 bundle path; to revisit before any gen2 AUTHORIZATION_BOUND terminal.
- `python3 tools/test_mission_launch_gate.py` passes with this host's own preflight reasons `['auth_expired', 'hooks_broken']` (from its `V-LG-REAL-PREFLIGHT-E2E` line); those are environment facts of this run, not claims about the programme.
- `PP_PATCH_ID_SCAN = 300`: a pick older than 300 non-merge commits is not found by the patch-id path (trailer path unbounded).
- Gen2 `deltas` stay empty in Phase 0 by design; `--generation 2 --final` reports `L8 delta product: empty` and `L8 delta intelligence: empty` until programme closeout.
