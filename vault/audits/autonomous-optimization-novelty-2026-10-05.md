---
title: IC-gen2 autonomous-optimization -- HR-NOVELTY-001 run against a discovered sweep
date: 2026-10-05
status: MEASURED - 13/13 answered against a discovered sweep
subject: IC-gen2 autonomous-optimization (vault/plans/autonomous-optimization-2026-10-05.md, vault/specs/autonomous-optimization.md)
verdict: EXTEND_EXISTING_OWNER
plane: gex44
sweep_commit: a83d1d7128cb9ada7bbbed1a243127de2ac08e6c
---

# HR-NOVELTY-001 -- 13 of 13, against the programme as proposed

## 0. Subject

The proposal is the IC-gen2 programme: observe execution, detect recurring avoidable cost, price it, build the smallest
challenger, promote it through the existing ratchet. It could be read as a new institutional mega-system (an optimizer,
an opportunity lifecycle, a capital allocator). HR-NOVELTY-001 therefore requires the thirteen questions answered from a
discovered sweep of this repo, never from the proposal's own list of what it assumes does not exist.

Every citation in section 3 is `path:LINE "fragment"` and is resolved mechanically by `tools/test_ao_p0.py`: the path is a
git-tracked file inside the repo, and the fragment occurs verbatim on that line of the file as committed at
`sweep_commit` (the commit the sweep ran at). Pinning to a commit keeps the record checkable after later phases edit the
swept files; the current working tree is not the evidence, the snapshot is.

## 1. What the keyword gate did

`check_novelty_gate` is advisory and keyword-triggered. Live output on this plane:

```
plan text: applies=False matched=None
ROADMAP text: applies=False matched=None
control "new autonomous optimization operating system": applies=True matched='operating system'
control "new optimization governance layer": applies=True matched='governance layer'
```

The gate is silent on both the plan of record and the ROADMAP. Per `modules/spec_gate/gate.py` lines 355-364 a keyword list
is bounded by its own vocabulary, so that silence is a vocabulary limit, not evidence of non-novelty. The two positive
controls prove the instrument can fire. The thirteen questions are therefore answered anyway, from the sweep below.

## 2. Sweep

Run from the repo root at `sweep_commit`. A hit count is a count of lines for `grep -rn` and of files for `grep -rln`.

- `grep -rn "SCHEMA_VERSION" tools/usage_index.py` -> hits=5 (schema 4, no v5 yet)
- `grep -rln "challenger" modules tools wiki/tools` -> hits=10 files (9 pre-existing owners of the vocabulary, plus `tools/test_ao_p0.py`, a self-hit of this programme)
- `grep -rn "def promote\|def revert\|def verify_chain" modules/tower/ratchet.py` -> hits=3
- `grep -rn "def record_signal" modules/cognitive_os/co_12_telemetry.py` -> hits=1
- `grep -rln "opportunity lifecycle\|technical capital\|realized dividend\|predicted dividend" modules tools wiki/tools vault/specs vault/plans` -> hits=3 files (the plan of record, this programme's own spec, and `vault/plans/cognitive-microkernel-brief-2026-10-04.md`); zero files under modules, tools or wiki/tools, so no executable owner
- `grep -rln "def store_identity" tools` -> hits=1
- `grep -rln "ratchet" modules tools` -> hits=41 files, including two family-specific ratchets (`modules/sqi/ratchet.py`, `modules/intent_verified/ratchet.py`) and the generic one, `modules/tower/ratchet.py`
- `grep -rln "opportunities" vault/programs` -> hits=1 (a prose owner brief under skill-capability/gen2; no durable opportunity ledger exists)
- `grep -c "cwd" tools/usage_index.py` -> hits=0; positive control `grep -c "session" tools/usage_index.py` -> hits=12 (the grep can find a column name that is present)
- `grep -c "usage_index" wiki/tools/kme_pillars.py wiki/tools/kme_token_audit.py` -> hits=1 and hits=0 (the one hit is a message string, not an import); positive control `grep -n "import usage_index" tools/estate_shadow.py` -> hits=1

## 3. The thirteen

| # | question | measured answer |
|---|---|---|
| 1 | What concrete problem has no owner today? | The optimization lifecycle (detect, price, challenge, promote) has no executable owner: the plan itself records it as documented-only, vault/plans/autonomous-optimization-2026-10-05.md:33 "Documented-only (no executable owner)". And the substrate the champion needs is not there: the only tool events usage_index records are agent spawns, tools/usage_index.py:362 "Agent/Task tool_use becomes a spawn row", and its calls table has no cwd, project or content-identity column, tools/usage_index.py:70 "CREATE TABLE IF NOT EXISTS calls(k TEXT PRIMARY KEY" (sweep: cwd hits=0, session control hits=12). |
| 2 | What new outcome would this produce? | Measurement runs that take seconds instead of minutes, and a miner that parses a delta instead of the whole corpus: vault/plans/autonomous-optimization-2026-10-05.md:63 "Expected dividend: measurement runs minutes -> seconds". The measured gap is real: vault/plans/autonomous-optimization-2026-10-05.md:22 "scoped 24 s / 2.83 GB" against 869 s / 101.53 GB unscoped, vault/specs/autonomous-optimization.md:61 "STEP r4-population exit=3 killed=no wall_s=869". |
| 3 | What real consumer needs it? | The KME measurement path that rescans every run, wiki/tools/kme_pillars.py:1629 "def scan(roots, expand, host, observers, keep, project_filter=None):", the replay ranker, wiki/tools/kme_replay.py:5 "live champion/challenger sessions spend quota and need an Owner decision", and the daily miner that streams the whole corpus, tools/sovereign_miner.py:4 "Streams every Claude Code transcript". |
| 4 | Why is extending an existing owner insufficient? | It is not insufficient, which is why the verdict is extend. Ingest is already incremental, tools/usage_index.py:424 "Index the bytes appended since the last pass"; promotion and revert already exist with a reason and an authority, modules/tower/ratchet.py:164 "def promote(family: str, new_entries: list, reason: str, authority: str,"; the done-gate already judges a second ledger by rebinding, tools/test_incremental_cognition_program.py:86 "ce.FROZEN_AT_REL = PROGRAM_DIR +". Each pillar maps to an existing owner, see section 4. |
| 5 | What new primitive does it require? | None beyond a row schema inside an existing ledger. Signals already have a locked fail-open writer, modules/cognitive_os/co_12_telemetry.py:84 "def record_signal(kind: str, payload: dict, *, state_dir=None,", and an existing producer kind, tools/skill_opportunity_signals.py:28 "KIND = ". An opportunity row is an object in a list of the gen2 ledger, outside the frozen object; there is no new store, daemon or database. |
| 6 | What decisions would it make that nobody makes today? | Whether a recurring cost is worth a challenger at all, and whether to stop a branch below break-even. Today the one reopened pillar is a disposition only: vault/programs/incremental-cognition/ledger.json:59 "dispositions only: CE Q/N/O/M and the pre-registration pattern of this verifier already own them". Gen2 reopens M as executable and keeps authority with the Owner: promotion still requires an authority, modules/tower/ratchet.py:164 "def promote(family: str, new_entries: list, reason: str, authority: str,". |
| 7 | What evidence would it produce? | A tamper-evident chain of generations and per-opportunity rows with measured, not predicted, dividends. The chain verifier exists, modules/tower/ratchet.py:120 "def verify_chain(family: str, root", and the pre-registration is pinned by commit, spec section 8.3: vault/specs/autonomous-optimization.md:133 "Only `frozen` is pinned by `FROZEN_AT`". |
| 8 | What failure class does it prevent? | Full-corpus rescans that nobody priced: the champion json-parses every line of every transcript on every run, wiki/tools/kme_token_audit.py:216 "for root, _dirs, files in os.walk(pdir):", and the diagnosis records that it never reads the index, vault/plans/zero-rescan-reality-scan-2026-10-05.md:108 "it never reads usage_index" (sweep: usage_index hits=0 in kme_token_audit, hits=1 string only in kme_pillars, control import hits=1 in estate_shadow). |
| 9 | What interfaces would it have with existing owners? | Existing ones only: the store identity producer, tools/tis_observed.py:349 "def store_identity(base=None)"; the ratchet consumer, tools/family_baseline.py:115 "from modules.tower import ratchet as rt"; the telemetry writer, modules/cognitive_os/co_12_telemetry.py:84 "def record_signal(kind: str, payload: dict, *, state_dir=None,"; and the champion scan, wiki/tools/kme_pillars.py:1629 "def scan(roots, expand, host, observers, keep, project_filter=None):". |
| 10 | How would its value be measured? | By the frozen champion numbers and a parity denominator, against commands recorded in the spec: vault/specs/autonomous-optimization.md:61 "STEP r4-population exit=3 killed=no wall_s=869" is the unscoped baseline and vault/plans/autonomous-optimization-2026-10-05.md:22 "scoped 24 s / 2.83 GB" is the bar a challenger must beat on repeated queries; a challenger that does not is narrowed or rejected. Realized dividend stays separate from predicted. |
| 11 | What complexity would it introduce? | The real risk is a second ratchet or a parallel store. The sweep found two family-specific ratchets already, modules/sqi/ratchet.py:1 "SQI Baseline Ratchet" and modules/intent_verified/ratchet.py:1 "The criterion set as a NAMED ratchet", beside the generic one. The programme adds no ratchet: it promotes through modules/tower/ratchet.py, and the spec states it as a non-goal, vault/specs/autonomous-optimization.md:85 "No new operating system, runtime, database, scheduler or ratchet". The one new file class is a judge, tools/ic_gen2.py. |
| 12 | What condition would justify retiring it? | A challenger that loses to plain scoping is rejected with a falsification artifact; gen2 judging is removable by reverting one dispatch commit, vault/specs/autonomous-optimization.md:177 "- KS-2 LIVE: gen2 judging is reached only through"; a promoted entry is undone by the existing revert, modules/tower/ratchet.py:146 "def revert(family: str, entry_id: str, reason: str, authority: str,". |
| 13 | Why is this not a rhetorical layer over systems that already exist? | Because it is falsifiable at each step: the champion, the scoped path and the challenger are timed on the same corpus, a challenger may lose and is then rejected, and the plan commits to building no new layer, vault/plans/autonomous-optimization-2026-10-05.md:37 "No new OS / runtime / DB / scheduler". The keyword gate cannot decide this, modules/spec_gate/gate.py:355 "A keyword list is bounded by its own vocabulary", so this record and its resolvable citations are the evidence, and a mutant per rule proves the judge can fail. |

## 4. Verdict

`EXTEND_EXISTING_OWNER`. The sweep supports no new module, view, policy pack or scanner. Each pillar extends an owner that
the sweep found:

- `tools/usage_index.py` is the substrate owner (pillar O): incremental ingest exists, schema 4 lacks tool events, cwd, project attribution and content identity.
- `wiki/tools/kme_pillars.py` is the challenger owner (pillar P), with `wiki/tools/kme_token_audit.py` and `wiki/tools/kme_replay.py`.
- `modules/cognitive_os/co_12_telemetry.py` is the detector owner (pillar Q), with `tools/skill_opportunity_signals.py`.
- `modules/tower/ratchet.py` is the promotion owner (pillars M and R); no second ratchet is created.
- The cognitive-economy verifier, reused by rebinding and never edited, is the judge of the gen2 ledger.

The single new file class is `tools/ic_gen2.py`, a judge of an existing ledger convention (the gen1 incremental-cognition
ledger shape). It adds no store and no runtime. If a later phase finds that this verdict no longer holds, the slice stops
and the classification is re-run, not patched.
