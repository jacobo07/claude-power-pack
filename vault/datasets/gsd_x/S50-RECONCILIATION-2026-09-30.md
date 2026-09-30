# §50 — the 18 GSD X rule candidates against the existing rule stores

`Dataset GSD X 1.txt` §50 (line 2416): integrate verified GSD X learnings with the existing
stores, **create no GSD-specific duplicate memory**, and distinguish incident fact /
GSD lesson / autonomous-engineering lesson / universal rule. The 18 candidates are the
two tables in `vault/lessons/derived-obligation-first-vertical.md` (13) and
`vault/lessons/knowledge-stale-by-omission.md` (5), recorded as GSDX-M08.

**Method.** A keyword probe over UKDL, CLAE, HARD-RULES, `~/.claude/rules`, PP skills and
lessons found leads for 6 of 18. Paraphrase defeats keywords, so both CLAE registries
were then read in full (127 traps, 174 process rules) and every candidate judged by
mechanism, not wording. The probe's "none" was wrong for 7 candidates.

## Verdicts

| # | candidate (short) | verdict | existing owner |
|---|---|---|---|
| 01 | a derived requirement keeps provenance | COVERED | `PR-CLAE-LEDGER-EVERY-MATERIAL-CLAIM` |
| 02 | a model-generated requirement is a candidate | COVERED | `T-CLAE-SELF-CERTIFICATION`, `T-CLAE-SYNTHESIZED-REFERENCE` |
| 03 | backlog done does not authorise mission done | COVERED | `T-CLAE-INHERITED-CLOSURE`, `PR-CLAE-COMPUTE-AT-EACH-SCALE` |
| 04 | an obligation goes stale when its parent stops holding, even from SATISFIED | PARTIAL | `T-CLAE-STANDING-DEVIATION` has the shape (persisting for a reason that no longer exists); the inverse direction — releasing an obligation — is not stated |
| 05 | worker narrative is not transition authority | COVERED | `PR-CLAE-EXECUTOR-REQUESTS-NEVER-GRANTS`, `T-CLAE-SELF-GRANTED-CLOSURE` |
| 06 | test a derivation on a domain it was not written for | COVERED | `evaluation-corpus-governance` ("don't present a revealed case as unseen again") |
| 07 | a detector's red branch must reach a gate | COVERED | `PR-CLAE-EVIDENCE-HAS-A-CONSUMER`, `T-CLAE-EVIDENCE-VOLUME` |
| 08 | pin a standing property to its surface, a dated measurement to its commit | **NEW** | `PR-CLAE-ALWAYS-PINNED` says pin; not WHICH pin. Already structural in `gsd_x_claim_reconcile.py` (`commit:` vs `path:`) |
| 09 | a closed vocabulary over natural language is fitted by construction | PARTIAL | neighbour of 06; the vocabulary-chasing mechanism is not named anywhere |
| 10 | a crashing mutant is not a survivor | COVERED | `PR-CLAE-THREE-VALUED-OUTPUT`; implemented as UNJUDGED in `tools/mutation_drill.py` |
| 11 | two of three inputs identical, so "unchanged" | **NEW** | nearest is `T-CLAE-UNENUMERATED-ROUTE-SPACE`, a different mechanism |
| 12 | splitting prose on a conjunction to make a requirement list | **NEW** | none |
| 13 | a seal whose hash depends on line endings | COVERED | `HR-CANON-BYTES-VCS-001` (UKDL:8322), broader and older |
| 14 | new evidence no claim covers is a freshness failure | COVERED | `PR-CLAE-LEDGER-EVERY-MATERIAL-CLAIM`, `T-CLAE-VACUOUS-NEGATIVE-PROOF`; enforced by V-GSDX-DATASET-COVERAGE |
| 15 | a current claim needs current evidence dependencies, not a recent timestamp | **NEW** | complements `PR-CLAE-UNVERIFIED-DISPOSITION`, which is interval-based; this says time is not the staleness signal |
| 16 | name overlap does not prove contract equivalence | COVERED | `PR-CLAE-PREFLIGHT-SEVEN-SURFACES`, `PR-CLAE-SEARCH-BY-PROPERTY-NOT-NAME` |
| 17 | a pre-registered prediction tests the layer it was written at | PARTIAL | `T-CLAE-WRONG-INSTRUMENT-KIND` (answers a different question under the same name) |
| 18 | scoping a coverage sweep to claimed surfaces rebuilds staleness | COVERED | `PR-CLAE-DISCOVER-DONT-DECLARE`, `T-CLAE-SUMMARY-ANCHORED-REVIEW`, PP PR-COVERAGE-BY-CONSTRUCTION-001 |

**11 covered · 3 partial · 4 new.** §50 forbids duplicating the 11. What is owed is the 4
new ones and a decision on the 3 partials (extend the existing entry, or promote).

## Level, per §50's four classes

- 08 — **universal engineering rule** (any ledger with pins), already enforced by mechanism.
- 11, 12 — **autonomous-engineering lessons** (traps an agent falls into when judging change and deriving work).
- 15 — **universal engineering rule**.
- 04, 09, 17 — autonomous-engineering; each is best as an extension line on its CLAE neighbour.

## Why nothing was written to the UKDL in this unit

GSDX-M09: the UKDL has a continuous writer (the CEPS auto-appender, 892 uncommitted lines at
12:41). Promotion therefore means hunk-scoped staging of only these rows beside the
appender's. That is a write into the canonical corpus, and GSDX-M08 assigns it to that
file's owner — so it waits for the Owner's go.
