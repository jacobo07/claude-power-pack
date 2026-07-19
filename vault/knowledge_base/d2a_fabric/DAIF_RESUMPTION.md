# RESUMPTION — DAIF (Duplicate-to-Advantage Institutional Fabric)

You are continuing the **DAIF** corpus build in `C:\Users\User\.claude\skills\claude-power-pack`.
Read this file, then `DAIF_INDEX.md`, then `DAIF_CANONICAL_MAP.md`, then execute Block 4. Do not
re-plan and do not re-run Phase 2 — the architecture is Owner-approved (re-spec 2026-07-12).

---

## 1. What this is

DAIF is the **compilation-substrate axis**: typed cognitive representations (CIRs), a cognitive type
system, a fidelity/loss contract, a formal obligation lifecycle, an institutional contract fabric, a
context/mission runtime, and reality synchronization — plus D2A+ elevated from one engine to a
constitutional default. It is the substrate that lets the PP's existing sealed families (SQI, DRK, FD,
ACIS, CO, GK, PM, D2A-engine) **compound**, not a re-build of any of them.

## 2. Exact state (coherence anchor — these must agree)

- Phase 2 CLOSED: `DAIF_CANONICAL_MAP.md` = 22 candidates → **8 build · 6 do-not-build · 8 folded**.
- 8 sovereign datasets in `DAIF_INDEX.md` manifest: DAIF-00,01,02,03,04,07,08,21.
- ## ✅ CORPUS COMPLETE — 8/8 SEALED · 160/160 Parts · **292,276 words** · `DAIF_PASS=48/48` exit 0
  DAIF-00 30,417w · DAIF-01 33,509w · DAIF-02 34,826w · DAIF-03 38,694w · DAIF-04 39,939w ·
  DAIF-07 38,435w · DAIF-08 40,125w · DAIF-21 36,331w. Mean **1,827 w/Part** (reference standard: 1,357).
  Phase 7 + Phase 8 CLOSED: `DAIF_COMPOUNDING_MAP.md` (9 compounding couplings · coverage matrix ·
  **11/11 final-audit gates PASS** · zero classified FAILs · honest residuals · 4 UKDL rules).
- Done-gate: `python tools/test_daif.py` (V-DAIF-PARTS/FINALLAW/DENSITY≥1200/FABRICATION/CONTAMINATION/NONDUP).
  Observed to refuse then pass — a real gate. Agents over-report word counts by ~5-8%; the orchestrator's independent
  count governs. Only the 1,200 floor is binding — there is NO upper ceiling; never cut mechanism to hit a word target.
- **THE CORPUS IS STILL A SPECIFICATION — but it now has ONE running vertical (SCS C96, 2026-07-13).**
  The rest of the corpus remains unproven, and DAIF-21 Part XIX's self-audit (4 unproven claims, 3 honest risks)
  still stands for everything outside this vertical. Presenting a specification as a running system is the exact
  failure the corpus exists to prevent, and it is now a *narrower* claim, not a retired one.
- **FIRST PROVING VERTICAL — BUILT AND MEASURED (DAIF-08 Part XI).** `modules/daif/`:
  `obligation_extractor.py` (DAIF-07 object, taxonomy, intake gate, de-dup) ·
  `constraint_extractor.py` (DAIF-01 typed constraints; hard = `Strength=hard`) ·
  `session_continuity_compiler.py` (the 8 contents of 11.3; `status=FAIL_VISIBLE` is clause 7) ·
  `resume_reader.py` (the far side: stdlib only, package as its ONLY input).
  Package lands at `vault/sessions/continuity_<session_id>.json`.
  Done-gate: `python tools/test_daif_session_compiler.py` → `DAIF_COMPILER_PASS=9/9`, hermetic ×3.
  **MEASURED (real 6.4 MB session, fresh-process reset): hard constraints 100% (74/74) ·
  open obligations 100% (10/10), all closeable per DAIF-07 12.5 · 0 invented claims.**
- **TWO-ARM TRIAL RUN — clauses 3 and 4 MEASURED (SCS C97, 2026-07-13).** `modules/daif/two_arm_trial.py`;
  gate `python tools/test_daif_two_arm_trial.py` → `DAIF_TRIAL_PASS=8/8` (records in `vault/trials/`,
  gitignored — re-run `--sample` to regenerate; it costs real API money and the gate REFUSES rather
  than passing on absent evidence). 3 sealed missions, `claude-sonnet-5`, zero tools in both arms.
  **token delta saved (B−A): +76,336 / +41,973 / +40,466 — the pack is cheaper 3/3.**
  **clause 3: FAIL / PASS / PASS. clause 4: FAIL / FAIL / FAIL.**
- **THE PART XI DONE-GATE REMAINS OPEN.** Clause 4 fails on every mission: the resumed actor asks for
  the source anyway. The pack is cheaper and it is NOT yet sufficient. Do not describe the compiler as
  passing its gate. Artifact-level fidelity verdict: **DEGRADE** (sample post-dates the artifact,
  DAIF-03 10.2; representative stratum only; n=3, 10.6).
- **THE THREE LOCALIZED GAPS ARE FIXED (2026-07-19); RE-RUN IN PROGRESS.** `_current_reality` now
  emits `uncommitted_files` (a real, capped LIST, `MAX_LISTED_PATHS=15`, truncation disclosed) plus
  `diff_summary` (the totals line — the full per-file table is an `expansion_handle`, not silently
  dropped), not just a count. `_referenced_files` scans every hard-constraint/obligation/decision
  text for file-path tokens and confirms each one's existence against disk before the actor has to
  ask. `modules/daif/decision_extractor.py` (new) recovers `decisions_with_justifications` by the
  same archaeology pattern as `obligation_extractor.py` — chosen+rationale pairs, cross-matched
  against the DRK Decision Registry (composed, not forked) — and replaces the permanent `"unknown"`
  with either real recovered pairs or a checked, honest "0 found, N turns scanned" absence.
  `tools/test_daif_session_compiler.py` gained 3 gates for these (`V-DECISION-EXTRACTOR-REAL`,
  `V-CURRENT-REALITY-LISTS-PATHS`, `V-REFERENCED-FILES-CHECKED`) — **`DAIF_COMPILER_PASS=12/12`**
  (was 9/9), no regression, `DAIF_PASS=48/48` corpus gate still holds.
  **Budget note:** the fix pushed mission `c718d3f5...`'s pack to `FAIL_VISIBLE` (est. tokens over
  `TOKEN_BUDGET=20,000` even after trimming `MAX_LISTED_PATHS` 60→15 and the diff to a one-line
  summary) — the hard-constraint set alone has grown 74→75 since the original trial (CLAUDE.md
  grows independent of this fix), and the compiler's own doctrine reserves raising `TOKEN_BUDGET`
  for the authority, not the agent; not moved unilaterally.
- **RE-RUN COMPLETE (2026-07-19) — CLAUSE 4 DID NOT MOVE. Do not describe the fix as having closed
  the gate.** `python modules/daif/two_arm_trial.py --sample`, same 3 sealed missions, records in
  `vault/trials/two_arm_*.json` (overwritten in place — the originals are in this file's history and
  in commit `bb55634` if a byte-for-byte diff is ever needed).
  **clause 4 (no re-reading): FAIL / FAIL / FAIL — unchanged from the original trial.** All three
  arms still asked for source access. Mission 1's requests were now about the pack's OWN disclosed
  limits (wants the un-truncated `git status`/`git diff`, notes `RESUMPTION_FILE.md` and
  `vault/progress.md` show as uncommitted) rather than blind guesses — the fixed fields are being
  read and reasoned about, they just were not sufficient to stop the ask. **Six Arm-A runs across
  the original trial and this rerun; clause 4 has passed zero of them.**
  **clause 3 / invention — mixed, not a clean improvement:** mission 1 went FAIL→PASS on both
  (92 citations, all grounded — the fix's added content is directly why). Missions 2 and 3 went
  PASS→FAIL on both, driven largely by citations like `"HR-BACKLOG-001 through HR-BACKLOG-003"` and
  `"HR-CASCADE-001 through HR-CASCADE-005"` — the arm summarizing several really-present pack
  constraints as one range, which the adjudicator's per-citation matcher (built for single-unit
  paraphrases, DAIF-03 10.4) does not recognize and scores as invented. This is flagged, not
  resolved: it may be a real regression, or it may be the adjudicator failing to parse a valid
  compression, and the two explanations are not yet distinguished.
  **token delta saved (B−A), this rerun: +67,107 / +43,286 / +42,829 — pack still cheaper 3/3**,
  smaller than the original because the pack itself is larger now (more real content).
  **NEW, HIGHER-PRIORITY FINDING: `session_overhead_tokens` measured at 74,063** for a trivial
  "reply with exactly: OK" call with the SAME `claude -p --disallowed-tools ...` invocation the
  trial arms use. `--disallowed-tools` blocks ACTIONS (Read/Bash/etc.) but there is no flag in
  `_call_model()` suppressing the CLI's own automatic project-context loading (CLAUDE.md, skills,
  hooks) — meaning Arm A may not be resuming from ONLY the compiled pack the trial constructs; it
  may ALSO be sitting inside this repo's live CLAUDE.md via the CLI's normal onboarding, which
  would explain both the volume of the overhead and would call into question what clause 3/4/
  invention have actually been measuring, in THIS rerun and in the original SCS C97 trial alike.
  **CONFIRMED, not just hypothesized: `claude --help`'s own text states the default system prompt
  includes "CLAUDE.md auto-discovery," and `_call_model()` passes neither `--system-prompt` nor
  `--exclude-dynamic-system-prompt-sections` nor any other isolation flag — both arms run with this
  repo's live CLAUDE.md/skills/hooks loaded on top of whatever packet is fed via stdin.** This most
  plausibly explains the mission-2/3 citation pattern above: an arm citing real CLAUDE.md content
  the extractor classified SOFT (excluded from the pack by design) is not inventing, it is reporting
  what its own onboarding handed it — the adjudicator has no way to tell that apart from a genuine
  invention because it only checks citations against `pack_texts`. Clause 4's verdict is more
  likely trustworthy despite the leak (CLAUDE.md content carries no session-specific obligations or
  current-reality facts, so it cannot be what lets an arm avoid asking for the session); clause 3 and
  invention are the ones the leak most directly compromises, in this rerun AND in the original SCS
  C97 trial alike. **Fix path, not yet applied:** re-run with `--system-prompt-file <packet-only>`
  or `--append-system-prompt` replacing the bare packet-as-stdin approach, so Arm A's ONLY system
  content is the compiled pack — or run the CLI from a directory with no CLAUDE.md at all. Either
  requires changing `_call_model()` and re-spending real API money; not done unilaterally here.
- **STANDING STATE: the Part XI done-gate remains OPEN.** Clause 4 has never passed. Do not build
  further derived systems on top of an unclosed proving vertical. The immediate next action is the
  overhead/isolation question above, not another content fix to the pack — six failed Arm-A runs on
  the same clause is the anti-antipattern-protocol's 2-consecutive-failures law, applied: change the
  approach, don't retry the same shape a third time.
- Batching pattern that works: 3 batches/dataset (I–VII, VIII–XIV, XV–XX) via Agent SOLO; verify+merge+gate+commit each;
  seal on full-20 gate pass; push after seal.
- Directory: `vault/knowledge_base/d2a_fabric/`. Fabrication contract = SQI's (`sqi/CANONICAL_ONTOLOGY.md` §9):
  `.txt`, PART I…XX, FINAL LAW per Part, dense prose, no headings/bullets/tables/fences, 1,200–1,500 w/Part.

## 3. Active decisions (binding — do not revisit)

1. **8 datasets, not 22.** Every folded/referenced candidate's verdict is in `DAIF_CANONICAL_MAP.md` §1/§3.
   Never fork: capability graph (GK), evidence/lineage/provenance (GK-04 + ACIS), dataset evolution
   (FD-07 + evolution_engine), benchmarks (SQI + CDIO), event transport (PM-03 + CEPS).
2. **DAIF-00 composes the sealed D2A engine (SCS C85), never re-implements it.** The engine is the
   executable; DAIF-00 is the constitution + duplicate ontology the engine lacked as a dataset.
3. **Domain Contamination Gate on every Part.** Quarantined literals (0 hits): ecommerce/store/shop/
   merchant/SKU/catalog/revenue/operator/brand/Shopify/WooCommerce/Stripe/CommonWealth/CW-Ops. Re-express
   the source's contaminated examples on PP-internal scopes (universal/power-pack/repo/project/feature/session/model).
4. **Epistemic marking on every claim:** EXISTS/PARTIALLY_EXISTS/SPECIFIED/PROPOSED/HYPOTHETICAL/REQUIRES_VALIDATION.
   No unmeasured savings/ROI figure (CO-12 Telemetry-Before-Claims).
5. **Producer never certifies its own claim.** Delegated Parts are verified by running the depth/contamination
   gate yourself, not by trusting a subagent self-report.
6. **First vertical = Session Continuity Cognitive Compiler** (re-spec §26) — proven against
   `session_compiler.py`, Lazarus, `/kclear`, CO-07. No savings number fixed in advance.

## 4. Next actions (imperative — highest value first)

1. **Author DAIF-00** (`daif_00_d2a_constitution_v1.txt`), 20 Parts. Spine: duplicate ontology (nominal/
   semantic/conceptual/functional/mechanism/data/evaluation/authority/lifecycle/temporal) · legitimate-
   redundancy taxonomy (defense-in-depth/fallback/specialization/compatibility/historical) · the D2A+
   pipeline · Sovereignty Test · reinforce/extend/compose/extract/create/reject verdicts · proactive
   scanner across all artifact types · advantage-conversion economics · D2A decision records · metrics ·
   maturity · adversarial cases · false-positive/false-negative control. Compose the engine (SCS C85).
2. Then DAIF-01 (type system) → DAIF-02 (CIRs) → DAIF-03 (fidelity/loss) → DAIF-07 (obligations) →
   DAIF-04 (contracts) → DAIF-08 (context/mission runtime) → DAIF-21 (reality sync).
3. Per dataset at CONTENT_COMPLETE: run Depth + Contamination + Non-Duplication + Mechanism + No-Code
   gates; micro-commit pathspec-scoped; update `DAIF_INDEX.md` manifest + this file.
4. Phase 7 (Compounding Map) + Phase 8 (hardening audits) + seal SCS C95 + UKDL (MAP §7) + push (REMOTE_DELTA 0 0).

## 5. Start instruction

Read this file, then `DAIF_INDEX.md`, then `DAIF_CANONICAL_MAP.md`, then author DAIF-00 Part I onward.
Delegation allowed via Agent SOLO (Windows cap-2), each Part self-verified against the depth gate before
acceptance. Do not ask for approval (Owner re-spec §25). Build.

**Update this file after every sealed Part-batch — never only at the end.**
