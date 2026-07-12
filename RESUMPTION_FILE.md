# RESUMPTION — SQI / UQIOS

You are continuing work on the **Sovereign Quality Intelligence (SQI)** axis in
`C:\Users\User\.claude\skills\claude-power-pack`. Read this file, then the index, then execute
Block 4. Do not re-plan. The architecture is approved and sealed.

---

## 1. What this is

SQI is the **Verification axis** of Claude Power Pack: it governs whether the executable reality
is actually verified, and what evidence licenses that claim. It is the ex-post counterpart to DRK
(decisions, ex-ante) and ACIS (epistemic status of claims).

It is now **two layers**: a corpus (doctrine) and engines (enforcement).

- Corpus: `vault/knowledge_base/sqi/` — 4 datasets, 80 Parts, 108,598 words.
- Engines: `modules/sqi/` — scanner, qualifier, reconciler. `tools/run_sqi.py` runs all three.
- Architecture: `vault/plans/sqi-uqios-architecture-2026-07-12.md`
- Engine contract: `vault/plans/sqi-reconciliation-engine-2026-07-12.md`
- **Binding ontology — read before authoring any Part:** `vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md`
- Honest gaps: `vault/knowledge_base/sqi/SQI_COMPLETION_REPORT.md`
- Latest seal: `vault/knowledge_base/sqi/sqi_scs_c91.md`

---

## 2. Exact state

**SPEARHEAD CORPUS (SCS C90) AND EXECUTABLE LAYER (SCS C91) ARE BOTH COMPLETE AND PUSHED.**
Do not rewrite either.

- `sqi_00_constitution_v1.txt` · `sqi_01_repository_reality_v1.txt` ·
  `sqi_02_test_reach_v1.txt` ★ · `sqi_03_environment_qualification_v1.txt` — 20/20 Parts each.
- `modules/sqi/repo_reality_scanner.py` · `environment_qualifier.py` · `reconcile.py` ·
  `discovery_rules.json` (**governed artifact** — widening its exclusions is the census trap).
- `tools/run_sqi.py` → `vault/audits/sqi_report_<date>.md` + JSON sidecar.
- `tests/test_sqi_engine.py` — 24 tests, **inside** `tests/` so the engine is reached by the
  canonical invocation. It is there because the engine reported SELF-REACH ZERO about itself.
- `sqi-runner` in the D1 Liveness Ledger. CO-12 signal kind `sqi_reconcile`.
- UKDL: `T-SQI-PARALLEL-SYSTEM-001`, `PR-SQI-COMPOUND-INTELLIGENCE-001`,
  `T-SQI-SELF-EVOLUTION-UNCONTROLLED-001`, `PR-SQI-EXECUTABLE-GOVERNANCE-001`,
  `T-SQI-FINDING-FABRICATION-001`, `T-SQI-DIRECTORY-NOT-MANIFEST-001`.

**Coherence anchor — these must agree or something has drifted:**
`python tools/test_sqi.py` reports `SQI_PASS=36/36` and `datasets=4` · `SQI_INDEX.md` marks 4
datasets `COMPLETE` · `vault/knowledge_base/sqi/sqi_*_v1.txt` is exactly 4 files ·
`modules/sqi/*.py` is exactly 4 files (3 engines + `__init__`).

**What the engine measures about this repository right now** (do not re-derive; re-run it):
Test File Reach **3.0%** (3 of 100) · Orphaned **97** · Executed Protection Ratio **1.6%** ·
authoritative invocation **BROKEN** (`pytest` exits 3, collects nothing) · reach under it
**UNKNOWN, not zero** · verdict `PARTIAL_GREEN`.

**NOT BUILT (backlog, verdicts already fixed in `SQI_INDEX.md` — do not re-litigate):**
SQI-04…SQI-13. Ten datasets.

---

## 3. Active decisions (binding — do not revisit)

1. **14 datasets, not 17.** Every overlapping capability is a cross-reference to the system that
   already owns it (`T-SQI-PARALLEL-SYSTEM-001`). **Never fork:** the evidence ladder (ACIS), the
   knowledge graph (graphify), the insight router (**FD-03 — DO NOT BUILD; it already *is* the
   "Failure-to-Data Compiler"**), decision verdicts/blast radius (DRK), bug→invariant
   (`modules/hard_rules`), the premise verifier (`modules/error_prevention`), done-gate scoring
   (`output_contracts`), telemetry (CO-12 `record_signal` — extend the kind, never fork the bus),
   liveness (D1 `default_registry` — add an entry, never a second ledger).
2. **Fabrication contract.** One `.txt` per dataset. `PART I`…`PART XX`, each closed by
   `PART N FINAL LAW`. Dense prose, numbered subsections, arrow flows. **No** markdown headings,
   bullets, tables, or code fences. **≥1,200 words per Part.**
3. **Vocabulary.** Use *transmutation* / *institutionalization*. The quarantined literals live
   fragment-assembled in `tools/test_sqi.py` `_BANNED` and are **never spelled out in any vault
   prose — including prose that is describing the rule.** A document about forbidden words cannot
   contain the forbidden words.
4. **Never move a criterion to fit a draft.** If a Part lands under the floor, raise the Part.
   The only gate ever loosened here was loosened because the *detector* was broken, never because
   a real finding was inconvenient — that is Part XIII's Gate Mutation Firewall.
5. **The producer never certifies its own claim.** Delegated work is verified by running the gate
   yourself, not by trusting the agent's self-report.
6. **Never adjust the engine so the number confirms the hypothesis** (`T-SQI-FINDING-FABRICATION-001`).
   Every number the engine produced disagreed with the plan's prediction, and every disagreement
   was a real fact about the repository. Report what the instrument says.
7. **The engine surfaces; the Owner remediates.** Widening the canonical invocation is a
   governance event (SQI-02 §9.10). Do not silently fix `testpaths` or the `_logs/` crash.

---

## 4. Next actions (imperative — highest value first)

1. **Build the SQI-02 Part XII baseline guardian.** This is now the largest gap: the engine
   *measures* and does not *gate*. Per-root, keyed by the environment hash, carrying node
   identities (a delta of three is an alarm; three names are an action). An increase is free; a
   silent **decrease** fails the build. The party whose change caused the decrease may not, in
   the same task, author the baseline update that permits it. Wire it into a done-gate. This
   moves SQI from `invoked` to `enforced` on Part XVII's own five-state ladder — and a signal
   that is emitted and never read is functionally identical to one never computed (§8.4).
2. **Point `run_sqi.py` at the rest of the estate.** It takes a path argument and has never been
   run outside PP. TUA-X's 390 orphaned tests are one `testpaths` line; CostaLuz's scanner is
   declared and never invoked; the two Elixir repos cannot compile. The engine detects all three
   classes already. Nothing has pointed it at them.
3. **Surface the three PP findings to the Owner** (they are governance decisions, not agent
   work): the broken zero-argument default, the absent root pytest config, and the 63 unprotected
   module packages including `secret_firewall`.
4. **Only then** consider SQI-04…13 from the backlog. Ten more datasets of doctrine on top of an
   engine that cannot yet refuse anything would deepen the gap, not close it.

---

## 5. Start instruction

Read this file, then `SQI_INDEX.md`, then `SQI_COMPLETION_REPORT.md` §4 (honest gaps), then
execute Block 4 action 1. Do not ask for approval. Do not explain the plan. Build.

**Update this file after every sealed unit of work — never only at the end.**
