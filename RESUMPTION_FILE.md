# RESUMPTION — SQI / UQIOS Dataset Family

You are continuing work on the **Sovereign Quality Intelligence (SQI)** corpus in
`C:\Users\User\.claude\skills\claude-power-pack`. Read this file, then the index, then execute
Block 4. Do not re-plan. Do not re-derive the architecture — it is approved and sealed.

---

## 1. What this is

SQI is the **Verification axis** of Claude Power Pack: a corpus governing whether the executable
reality is actually verified, and what evidence licenses that claim. It is the ex-post
counterpart to DRK (decisions, ex-ante) and ACIS (epistemic status of claims).

Architecture (approved STOP #1): `vault/plans/sqi-uqios-architecture-2026-07-12.md`
**Binding ontology — read before authoring any Part:** `vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md`
Honest gaps: `vault/knowledge_base/sqi/SQI_COMPLETION_REPORT.md`

---

## 2. Exact state

**THE APPROVED SPEARHEAD SCOPE IS COMPLETE AND PUSHED.** Do not rewrite any of it.

- `CANONICAL_ONTOLOGY.md` — 10 canonical objects, 12-state verdict ontology, Q0–Q5 / L1–L7 /
  R0–R4 ladders, 8 Quality Laws, the no-parallel-system boundary.
- `sqi_00_constitution_v1.txt` — 20/20 Parts, 25,811 words.
- `sqi_01_repository_reality_v1.txt` — 20/20 Parts, 26,989 words.
- `sqi_02_test_reach_v1.txt` ★ — 20/20 Parts, 28,596 words.
- `sqi_03_environment_qualification_v1.txt` — 20/20 Parts, 27,202 words.
- `SQI_INDEX.md` · `SQI_CONTAMINATION_AUDIT.md` (CLEAN) · `SQI_COMPLETION_REPORT.md`
- `tools/test_sqi.py` — the family done-gate. **`SQI_PASS=27/27`, ×3 hermetic, exit 0.**
- UKDL sealed: `T-SQI-PARALLEL-SYSTEM-001`, `PR-SQI-COMPOUND-INTELLIGENCE-001`,
  `T-SQI-SELF-EVOLUTION-UNCONTROLLED-001`.

**Coherence anchor — these must agree or something has drifted:**
`python tools/test_sqi.py` reports `datasets=4` and `SQI_PASS=27/27` · `SQI_INDEX.md` marks 4
datasets `COMPLETE` · `vault/knowledge_base/sqi/sqi_*_v1.txt` is exactly 4 files.

**NOT BUILT (backlog, verdicts already fixed in `SQI_INDEX.md` — do not re-litigate):**
SQI-04…SQI-13. Ten datasets.

---

## 3. Active decisions (binding — do not revisit)

1. **14 datasets, not 17.** Every overlapping capability is a cross-reference to the system that
   already owns it (`T-SQI-PARALLEL-SYSTEM-001`). **Never fork:** the evidence ladder (ACIS), the
   knowledge graph (graphify), the insight router (**FD-03 — DO NOT BUILD; it already *is* the
   "Failure-to-Data Compiler"**), decision verdicts/blast radius (DRK), bug→invariant
   (`modules/hard_rules`), the premise verifier (`modules/error_prevention`), done-gate scoring
   (`output_contracts`).
2. **Fabrication contract.** One `.txt` per dataset. `PART I`…`PART XX`, each closed by
   `PART N FINAL LAW`. Dense prose, numbered subsections, arrow flows. **No** markdown headings,
   bullets, tables, or code fences. **≥1,200 words per Part.**
3. **Vocabulary.** Use *transmutation* / *institutionalization*. The quarantined literals live
   fragment-assembled in `tools/test_sqi.py` `_BANNED` and are **never spelled out in any vault
   prose — including prose that is describing the rule.** That recursion bit this build four
   times. A document about forbidden words cannot contain the forbidden words.
4. **Never move a criterion to fit a draft.** If a Part lands under the floor, raise the Part.
   Lowering the floor is scope laundering (SQI-00 Part XVI). The one gate ever loosened here was
   loosened because the *detector* was broken (too-narrow vocabulary), never because a real
   finding was inconvenient — that distinction is Part XIII's Gate Mutation Firewall.
5. **The producer never certifies its own claim.** Delegated datasets are verified by running the
   gate yourself, not by trusting the agent's self-report.
6. **Evidence discipline.** All repo claims trace to the sealed SCS C81 audit
   (`vault/knowledge_base/testing/`). **Invent no findings and no numbers.**

---

## 4. Next actions (imperative — highest value first)

1. **Implement the SQI-02 reconciliation engine and run it against Claude Power Pack itself.**
   This is the largest open gap: the corpus is doctrine, and by its own Executable Governance Law
   a policy without enforcement is documentation. PP still has **70 of 76 test files outside its
   canonical invocation** — the finding that founded this corpus. Build
   `modules/sqi/reconcile.py`: walk authored test artifacts, walk what the canonical invocation
   actually collects, emit Test File Reach + Orphaned Test Count, and fail on a silent decrease.
   Wire it into a done-gate. Reproduce the 70/76 number automatically.
2. **Then the other founding findings**, in ROI order: TUA-X's 390 orphaned tests (one config
   line), CostaLuz's inert scanner, the two Elixir repos that cannot compile.
3. **Only then** consider SQI-04…13 from the backlog. Ten more datasets of doctrine on top of
   zero engines would deepen the gap the completion report names.

---

## 5. Start instruction

Read this file, then `SQI_INDEX.md`, then `SQI_COMPLETION_REPORT.md` §4 (honest gaps), then
execute Block 4 action 1. Do not ask for approval. Do not explain the plan. Build.

**Update this file after every sealed unit of work — never only at the end.**
