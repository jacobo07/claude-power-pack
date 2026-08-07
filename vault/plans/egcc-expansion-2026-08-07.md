---
title: EGCC Expansion — 25 spaces swept for a genuinely new governance family
date: 2026-08-07
status: STOP #1 — BLOCKING, presented inline, no dataset and no module written
verdict: 0 datasets derivable; 3 EXTENDs survive, 1 pre-existing gap confirmed and resized
covers: [egcc, expansion, gap_discovery, stop1, rule_compiler, denominator, novelty_gate]
denominator: EGCC_EXPANSION_DENOMINATOR.md
head: 290edc2
---

# EGCC Expansion — Sprint 1

The brief asked for 25 genuinely new datasets that would take the governance
compiler and constitutional runtime several levels further. This is the measured
answer against a denominator discovered from disk.

## 0. Inherited state honoured, not re-audited

EGCC Phase 0 (2026-08-06) measured 0 of 25 and built two residues, Rc1
(`enforcement` field) and Rc2 (`drift_registry`). Both are on `main`. That
verdict is carried forward, not re-litigated.

Two preflight actions the prior session had deliberately left for the Owner were
executed this session, both explicitly requested in the brief:

| Action | Result |
|---|---|
| `modules.owner_queue.stop_ledger --write` | 23 STOP-bearing plans — **OPEN 8 · CONTRADICTED 11 · RESOLVED 4** (was 18 plans / 8-6-4) |
| `tools/hardrule_compile.py --compile` | 162 rules, digest 2,970 B of 4,096, global digest regenerated with the binding banner |

**EFAIF Sprint 1 (2026-08-06, another pane) already swept ten of these spaces.**
Its verdicts are carried forward rather than re-measured, per the brief's "no
re-auditar lo ya medido". Where a space here duplicates an EFAIF candidate that
is *still awaiting the Owner at its own STOP #2*, it is marked DUPLICATE and not
re-proposed — proposing it twice would let one gap consume two approval slots.

## 1. The 25 spaces

Legend — **GAP** survives to the novelty gate · **OWNED** an incumbent was opened
and found to hold it · **REFUTED** the space's premise is false on this estate ·
**STARVED** the input the space needs does not exist · **DUPLICATE** already
proposed and pending · **CARRY** a prior pass measured it.

| # | Space | Verdict | Evidence |
|---|---|---|---|
| 1 | Rule retirement evidence | **GAP** → C3 | Key inspection of a compiled rule: no retirement, expiry or sunset field. `capability_runtime/retirement.py` retires *capabilities*, a different subject |
| 2 | Constitutional amendment log | DUPLICATE | EFAIF S3 → candidate C1, pending at EFAIF's STOP #2 |
| 3 | Governance jurisprudence | **REFUTED** | `modules/hard_rules/residual.py`: the corpus is prohibitions-only, 0 mandates. Prohibitions cannot contradict, so there is no precedent to record |
| 4 | Rule half-life | **STARVED** | Depends on #1. Nothing can measure how long a rule stays valid before a validity condition exists to expire |
| 5 | Evidence demand contract | DUPLICATE | EFAIF S6 → candidate C2, pending |
| 6 | Evidence chain integrity | CARRY / OWNED | EFAIF S13: 206 hits on `stale\|freshness\|verified_at\|expiry`. Owned densely |
| 7 | Governance supply chain | **GAP (half)** → C1 | Measured: exactly two source files, 147 + 15. The foreign-estate half is owned by `effect_harness.py:166`; the converse half is not |
| 8 | Constitutional provenance graph | OWNED | graphify holds 1,238 coordinates; `_GOV_ID` already promotes `HR-`/`PR-`/`T-` identifiers (CDICF E3) |
| 9 | Binding-point prioritizer | **STARVED** | Ranking needs trigger-frequency telemetry that does not exist, over a field at 0 of 162 adoption. A score whose factors are constants ranks nothing |
| 10 | Enforcement effectiveness | OWNED | `modules/rule_compiler/effect_harness.py` |
| 11 | Constitutional shadow mode | OWNED by construction | Rc1's `ADVISORY` rung *is* the shadow primitive: a rule declared ADVISORY is carried and does not block |
| 12 | Governance counterfactual | OWNED | `modules/rule_compiler/counterfactual.py` — binds rule + recorded incident + runnable detector. This was EGCC's headline mechanism, already shipped |
| 13 | Rule quality score | **FALSE POSITIVE** | 25 valid rules carry neither trigger nor stop — **all 25 are `IMPERATIVE`**, one-line prose whose text is the rule. Restricted to the 124 valid `FIELDED` rules, the count missing either field is **0** |
| 14 | Benchmark corpus | OWNED / adjacent | `counterfactual.py` is the golden-case binding; CDICF A5's 41 adversarial scenarios are the precedent for the form |
| 15 | Rule conflict detector | **REFUTED** | Same mechanism as #3 |
| 16 | Governance red team | **OWNED as of today** | `modules/sqi/redteam_protocol.py` + `tools/test_redteam_protocol.py`, built this session by another pane |
| 17 | Drift family severity | DEFER | Rc2 is one day old. Classifying 56 discovered families by institutional severity has no evidence of need yet |
| 18 | Semantic drift early warning | OWNED by construction | Rc2's `--singletons`: the 100 one-file terms *are* terms not yet a family |
| 19 | Constitutional entropy | **REJECT** | Genuinely absent, and fails novelty Q6: no decision anywhere would change on the number. A metric with no consumer is a rhetorical layer |
| 20 | Governance economics | OWNED | `frontier_intelligence/corpus_roi.py` · `recall_roi` · `token_irr` |
| 21 | Unknown governance space | **STARVED** | Requires a corpus of real decisions. `vault/decision_registry/records.jsonl` holds **1 row**. A coverage measure over a 1-row denominator produces a number that cannot fall |
| 22 | Constitutional self-critique | OWNED | SQI (`run_sqi.py`, 45/45 ×3) + the ACIS E0–E7 ladder |
| 23 | Governance adoption | **STARVED** | Same 1-row ledger as #21 |
| 24 | Rule interaction graph | **REFUTED** | #3's mechanism, plus graphify already carries the identifiers |
| 25 | *(free slot)* | **GAP** → C1, C2 | Two defects found by the sweep itself, neither on the brief's list |

## 2. Candidates that reached the novelty gate

### C1 — the enforced corpus and the compiled corpus are near-disjoint

**Measured.** 418 distinct `HR-` ids are named across 3,066 files. **16** are in
the compiled corpus. 402 are not; **68 of those are named in ≥2 distinct files**,
the same measured recurrence gate `rule_compiler` uses for boilerplate and
`drift_registry` uses to earn a family name — so they are rules the estate refers
to, not typos.

The recurrent uncompiled ids are the estate's *live safety rules*:
`HR-PREMISE-001` (44 files), `HR-COST-001` (23), `HR-SECRET-001` (19),
`HR-OUTPUT-001` (16), `HR-CASCADE-002` (14). Each is enforced by a live hook —
`hooks/secret_firewall_gate.js`, `hooks/cascade_check_bash.js`,
`hooks/hook-dispatcher.js` — and **absent from the corpus the compiler reads**.
Verified directly, not inferred: `vault/hard_rules/HARD_RULES.md` contains zero
occurrences of any of those five ids. `parser.load_corpus()` reads exactly two
files and neither is `CLAUDE.md`, where their canonical text lives.

**Why nothing caught it.** `tools/verify_hard_rules.py` check H7 is stated in its
own docstring as *"archive-or-claude — CLAUDE.md **OR**
vault/hard_rules/HARD_RULES.md has the sentinel block"*. A disjunction cannot
witness a divergence between its operands: a rule present only in the mirror
passes H7 forever while never compiling. The gate is satisfied by exactly the
state that produces the defect.

**Why extending is not obviously insufficient.** `effect_harness.py:166` already
owns the converse measurement and states it plainly — 140 of 149 compiled rules
govern other estates. It begins from the compiled set, so a rule absent from that
set is absent from its denominator; this is the same shape as the finding it
exists to prevent, pointing the other way. That makes C1 an **EXTEND on
`rule_compiler`**, not a new family.

Novelty gate: fails **Q4** and **Q5**. No new primitive — a set difference over
two discovered sets. Verdict **EXTEND_EXISTING_OWNER**.

### C2 — `severity` carries no usable value in the entire corpus

147 of 162 rules leave it empty. All 15 populated ones read
`'CRITICAL | RECURRENCE: 1x'` or `'HIGH | RECURRENCE: 6x'` — the field capture
runs to end of line and swallows the ` | RECURRENCE: Nx` suffix. Three distinct
values exist corpus-wide and none is a severity.

This is the **same defect class** fixed in Rc1, where `_FIELD_RE` joined aliases
in dictionary order and `ENFORCEMENT` would have shadowed `ENFORCEMENT_LEVEL`.
That fix was applied to alias ordering; the trailing-suffix capture was not
examined. Verdict **EXTEND** on `parser.py`. Small and certain.

### C3 — a rule cannot state the condition that would retire it

`HR-NOVELTY-001` question 12 requires a retirement condition of any new system,
and the brief's own done-gate requires that "each rule has evidence, scope,
enforcement path, **retirement condition**, falsification test". A compiled rule
has no field for it — confirmed by key inspection, not grep.

This is Rc1's shape exactly: a governance property the estate already demands in
prose, with nowhere to record it, so it cannot be checked. Verdict **EXTEND** on
`schema.py`. Fails Q5 — no new primitive.

### C4 — the reachability scanner is blind to four packages, not one

CDICF recorded gap **D-009** as `modules/cdicf` being absent from the liveness
scan because the scanner enumerates Python packages. Measured, the blind set is
**four**: `cdicf`, `governance-overlay`, `harness`, `rtk-core`. Six further
`modules/` directories contain neither `.py` nor `.js`.

This is a **confirmation and resizing of an already-named gap**, not a discovery.
It belongs to whoever owns D-009. Reported, not claimed.

## 3. Verdict

**0 of 25 spaces yield a genuinely new dataset family.** Distribution:
7 OWNED · 4 REFUTED-or-false-positive · 4 STARVED · 2 DUPLICATE · 2 OWNED-by-construction ·
1 CARRY · 1 REJECT · 1 DEFER · **3 GAP** (C1–C3) · 1 confirm-and-resize (C4).

This is the **fifteenth consecutive** mega-corpus proposal measured
majority-or-fully owned against a discovered denominator. Prior fourteen:
AISHF · RE Baseline · KSF · UKR Compendium · IIG · CRPF · IGEF · E-passes ·
CCFL-PDPF · USIRC · APIR · SEIP · UCEIMR · EFAIF · EGCC.

Against an estate of 80 module directories, 26 knowledge families, 68 commands,
1,525 executable gates and 161 compiled rules, an expansion pass finds adjacency,
not territory. That is the estate reporting density, not the sweep failing.

## 4. Anti-inflation

No candidate was padded to approach 25 (`no-silent-caps`). Every GAP was re-tested
against its nearest incumbent by **opening** that incumbent, never by a phrase
failing to grep (`T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001`) — which is how #12 was
found already shipped and #13 was killed as a false positive after the raw count
looked like a defect.

The three survivors total on the order of a hundred lines across three files that
already exist.

## 5. Blocking condition

C1–C3 are not built. No dataset, module or schema change is written until the
Owner selects inline.
