# RE_BASELINE_RESUMPTION

Read this file, then `vault/knowledge_base/COMPENDIUM_CHARTER.md`, then execute block 4.
Do not ask. Do not explain. Do not replan.

## 1. Identity

RE Baseline Compendium build. Repo: `C:\Users\User\.claude\skills\claude-power-pack`.
Corpus: 9 reverse-engineering rounds, SHA256 `CFBDAB0C…21C4`, extracted read-only under
the session scratchpad; the ZIP is authoritative (two pillars exist nowhere else).
Thesis: convert the corpus into institutional infrastructure **organized by verified gap,
never by source pillar**, because Phase 0 measured ~55–60 % of its proposals as already
owned by this stack.

## 2. Exact state

- Phases −2, −1, 0: **SEALED**. Commit `281c67e`. Audit at
  `vault/plans/re-baseline-compendium-2026-07-26.md`.
- STOP #1: **resolved**. Owner approved 3 NEW families + 5 EXTEND passes over the literal
  A–J ten-family specification.
- Charter: **SEALED** at `vault/knowledge_base/COMPENDIUM_CHARTER.md`.
- Parts sealed: CLAE I-XXVI — FAMILY COMPLETE (26/26). Closure verdict: complete with residual, accounting-only, acceptance line empty (Part XXVI section 5).
  Authoritative count is the coherence anchor below, never this line.
- CRPF: **CLOSED — struck as a family by Owner ruling (A then B'), 2026-07-27.** No CRPF
  Part exists and none will. Option A (repair wiring) and Option B' (CO-13 + CO-14) are
  both COMPLETE. Evidence: `vault/plans/crpf-option-a-wiring-2026-07-27.md`; datasets at
  `vault/knowledge_base/cognitive_os/cognitive_os_{13,14}_*.md`. Commits `a91328c`
  (scheduled-task discovery, 171→180 REACHABLE), `5f88210` (13-module disposition),
  `7bff31c` (JIT trigger, 85→22 firings), `3c41824` (CO-13 + CO-14).
- **IGEF: CLOSED — struck as a family by Owner ruling (A then B), 2026-07-29.** No IGEF
  Part exists and none will. PASO −1 (`vault/plans/igef-2026-07-29.md`, commit `124c25b`)
  swept a discovered denominator of 1,364 files / 152 families: 0 of 4 mechanisms justify
  a family, and two founding premises were refuted (the `Rule` dataclass has no retirement
  field, so G9's complaint was vacuous; M4's live predicate is already risk-weighted).
  Owner chose repair-with-evidence over construction. All three shipped:
  - **A** `0087c1c` — alert escalation on unresolved repeat. Also fixed the defect the
    audit did not see: `MIRROR_PAIRS` compared two *different documents*, so all 333
    handoffs were a permanent false positive and escalation alone would have promoted
    garbage to URGENT. 13/13 ×3; replay says 333 files become 11.
  - **B** `a8e7662` — discovery producer replaces the literal pair list; 9 → 28 pairs,
    2 → 7 real drifts visible. `mirror-parity-law.md` §1/§5/§6 amended, since the law
    itself made hand-enrollment the official procedure. 11/11 ×3.
  - **M1b** `9df175b` — rule effect harness: a rule bound to a runnable probe and a
    baseline. `--coverage` reports 147 compiled rules, 147 with no effect claim. 6/6 ×3.
  - `ef0533a` — `mirror_discovery` declared LIBRARY; gate offenders 4 → 2.
  **Open, Owner-side:** 7 drifted mirror pairs remain unresolved (Option C). §2 sync
  direction is repo ← global, so the repo side may be updated; nothing was synced here.
- Superseded audit text (kept so it cannot drift back): STOP #1 recorded three residency
  authorities as uncoordinated, and recorded that no surface writes CO-06's heat fields.
  Both were wrong. DAIF-08 and PM-05 both declare CO-04 their owner (CO-14 §I.1), and the
  observations are written continuously by `jit_skill_loader` under other names (CO-13 §I.1).

- CRPF (historical): **STOP #1** — audit at
  `vault/plans/crpf-2026-07-27.md` (commit `feb05c2`). PASO -1 found the "3 NEW + 5 EXTEND"
  criterion was never written down, and that CLAE was admitted by a measured zero-hit sweep
  while CRPF's G6 was admitted by asserted absence over a hand-recalled three-entry owner list.
  A discovered denominator finds all seven chartered CRPF mechanisms owned by `cognitive_os`
  (CO-00..CO-12, 12 datasets + 11 modules), DAIF-08 Context Runtime (20 Parts) and Parallel
  Mesh PM-04/05 — none of which Phase 0 enumerated. The real G6 is wiring: 13 residency
  modules are WIRED-BUT-SILENT / declared PLANNED. Three options are on the table
  (A repair-wiring · B a 4-6 Part reconciliation residue family · C build as chartered).
- IGEF (historical): admitted by the same asserted-absence standard as CRPF's G6. Audited
  2026-07-29; the answer was that its gaps did not survive a discovered denominator.
  Superseded text kept so it cannot drift back: the audit characterised the mirror-drift
  delta as a real drift that had grown to 2,083 lines. It had grown, but it was the size
  gap between two unrelated documents tracking the global file's growth — not a mirror
  falling behind. The finding (333 alerts, 67 days, no escalation) stands and is stronger;
  the characterisation of the delta was wrong.
- Superseded text on record: Part II §6 corrects Part I and `CLAE_CHARTER.md`, which both
  described the design-review scorer as a distance instrument. It is a stage-two graded
  criterion instrument. Do not restore the earlier phrasing anywhere in this family.

**Coherence anchor.** `CLAE_INDEX.md` must list exactly as many Part rows marked SEALED as
there are `PART_*.md` files in `vault/knowledge_base/clae/`. If those two counts disagree,
the index is lying — reconcile from the filesystem, never from the index.

## 3. Active decisions

- Construction order is dependency-derived and fixed: CLAE → CRPF → IGEF → E1…E5 →
  integration → review → seal. CLAE is first because it supplies the external-bar
  discipline everything else is scored against.
- `rule_compiler` owns rule placement. IGEF must not contain a placement compiler.
- `graphify` owns the semantic IR. E3 extends it; it never stands up a second graph.
- `fable_distillation` owns succession. E1 adds execution trials; it never forks FD.
- Zero executable code in dataset artifacts. Zero CommonWealth Ops vocabulary.
- Push is withheld: `main` is ahead of origin with unrelated work from concurrent panes.
  Commit with `-- <pathspec>` scoping every time; never `git add -A`.

## 4. Next three actions

1. Write the next unsealed CLAE Part named in `CLAE_INDEX.md`, at the depth floor defined
   in the charter, one Part per file.
2. Commit it alone, pathspec-scoped, then verify `git log -1 --format=%s` matches the
   message file's first line.
3. Update this file's block 2 and the `CLAE_INDEX.md` status row for that Part before
   starting the next one.

## 5. Start instruction

Read this file, then the charter, then `vault/knowledge_base/clae/CLAE_INDEX.md`.
Execute block 4 against the first Part whose status is not SEALED.
