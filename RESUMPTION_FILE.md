# RESUMPTION — SQI / UQIOS Dataset Family Build

You are continuing the **Sovereign Quality Intelligence (SQI)** corpus build in
`C:\Users\User\.claude\skills\claude-power-pack`. This file is self-contained. Read it, then
the index, then execute Block 4. Do not ask. Do not re-plan. Do not re-derive the architecture.

---

## 1. What this is

SQI is the **Verification axis** of Claude Power Pack: a dataset corpus governing whether the
executable reality is actually verified, and what evidence licenses that claim. It is the
ex-post counterpart to DRK (decisions, ex-ante) and ACIS (epistemic status of claims).

Source spec: `C:\Users\User\Downloads\Dataset Claude Power Pack Universal Quality & Iteration Intelligence 1.txt`
Architecture (approved at STOP #1): `vault/plans/sqi-uqios-architecture-2026-07-12.md`
**Binding ontology — read before authoring any Part:** `vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md`

---

## 2. Exact state

**SEALED (do not touch, do not rewrite):**

- `vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md` — 9 canonical objects, 12-state verdict
  ontology, Q0–Q5 / L1–L7 / R0–R4 ladders, 8 Quality Laws, the no-parallel-system boundary.
- `vault/knowledge_base/sqi/sqi_00_constitution_v1.txt` — **20/20 Parts, 25,782 words, COMPLETE.**
- `vault/knowledge_base/sqi/sqi_01_repository_reality_v1.txt` — **20/20 Parts, 26,989 words, COMPLETE.**
- `tools/test_sqi.py` — the family done-gate. **12/12, ×3 hermetic, exit 0, datasets=2.**
- `vault/knowledge_base/sqi/SQI_INDEX.md` — live status.
- UKDL: `T-SQI-PARALLEL-SYSTEM-001`, `PR-SQI-COMPOUND-INTELLIGENCE-001`,
  `T-SQI-SELF-EVOLUTION-UNCONTROLLED-001` sealed in `vault/knowledge_base/ukdl-universal.md`.

**Coherence anchor — these must all agree or something has drifted:**
`tools/test_sqi.py` reports `datasets=N` and `SQI_PASS=6N/6N` · `SQI_INDEX.md` lists exactly N as
`COMPLETE` · `vault/knowledge_base/sqi/sqi_*_v1.txt` is exactly N files. Today **N = 2**.

**PENDING (the active scope):**

- `sqi_02_test_reach_v1.txt` ★ — `IN_PROGRESS` — an agent was authoring this. **Verify before
  trusting:** run the gate. If the file is absent or fails, author it yourself per Block 4.
- `sqi_03_environment_qualification_v1.txt` — 0/20 — `NOT_STARTED`

**DEFERRED (backlog, Owner-approved, not abandoned):** SQI-04…SQI-13. Verdicts already fixed
in `SQI_INDEX.md`. Do not build them in this scope. Do not re-litigate their verdicts.

---

## 3. Active decisions (binding — do not revisit)

1. **Scope = spearhead.** SQI-00…03 only. The other 10 datasets are backlog.
2. **14 datasets, not 17.** Overlaps are replaced by cross-references to the system that
   already owns the capability (`T-SQI-PARALLEL-SYSTEM-001`). **Never fork:** the evidence
   ladder (ACIS), the knowledge graph (graphify), the insight router (**FD-03 — DO NOT
   BUILD**), decision verdicts/blast radius (DRK), bug→invariant (`modules/hard_rules`),
   the premise verifier (`modules/error_prevention`), done-gate scoring (`output_contracts`).
3. **Fabrication contract.** One `.txt` per dataset. `PART I`…`PART XX`, each closed by
   `PART N FINAL LAW`. Dense prose, numbered subsections, arrow flows. **No** markdown
   headings, bullets, tables, or code fences. **≥1,200 words per Part** (incl. FINAL LAW).
4. **Vocabulary.** Use *transmutation* / *institutionalization*. Never the commerce-adjacent
   synonym the gate quarantines — see `tools/test_sqi.py` `_BANNED` (fragment-assembled;
   never spell those literals out in vault prose, it trips PP's own content gate).
5. **Never move a criterion to fit a draft.** If a Part lands under the floor, raise the Part
   with substantive content — never lower the floor. That is scope laundering (SQI-00 Part XVI).
6. **Evidence discipline.** Every Part's claims about real repos must trace to the sealed
   SCS C81 audit (`vault/knowledge_base/testing/`). **Invent no findings.**

---

## 4. Next three actions (imperative)

1. **Author `sqi_01_repository_reality_v1.txt`** — 20 Parts. Subject: reality scanning the
   disk before trusting any description; domain classification (16 domains) and why it
   determines which tests are meaningful vs artificial; the executable-surface map; unknown-
   state preservation. Ground it in the real C81 finding that a repo was misclassified from
   its name and the disk disproved it, preventing a fabricated finding. Write in chunks of
   ~5 Parts to the scratchpad, concatenate with PowerShell + `WriteAllText` (UTF-8 no-BOM,
   LF), then run the gate.
2. **Run `python tools/test_sqi.py`** — it must reach `SQI_PASS=12/12`, ×3 hermetic, exit 0.
   Fix every FAIL by raising the dataset. Then update `SQI_INDEX.md` (status + word count +
   gate evidence) and **rewrite this file's Block 2** before committing.
3. **Micro-commit, pathspec-scoped:**
   `& $g -C <repo> commit -F <msgfile> -- vault/knowledge_base/sqi/sqi_01_repository_reality_v1.txt vault/knowledge_base/sqi/SQI_INDEX.md RESUMPTION_FILE.md`
   Then repeat 1–3 for **SQI-02** (★ highest ROI — authored-vs-executed reconciliation, canonical
   invocation discovery, baselines, the five green-signal verdicts) and **SQI-03**
   (environment qualification, dependency reproducibility, toolchain resolution, clean checkout).

After SQI-03 seals: FASE 6/7 — `SQI_CONTAMINATION_AUDIT.md`, `SQI_COVERAGE_AUDIT.md`,
`SQI_COMPLETION_REPORT.md` (honest gaps), seal `PR-SQI-COMPOUND-INTELLIGENCE-001`,
`T-SQI-SELF-EVOLUTION-UNCONTROLLED-001`, `T-SQI-PARALLEL-SYSTEM-001` into UKDL, then
`git push` until `REMOTE_DELTA = 0 0`.

---

## 5. Start instruction

Read this file, then `vault/knowledge_base/sqi/SQI_INDEX.md`, then
`vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md`, then execute Block 4 from action 1.
Do not ask for approval. Do not explain the plan. Build.

**Update this file after every sealed dataset — never only at the end.** A mid-run crash must
always leave a valid resume point.
