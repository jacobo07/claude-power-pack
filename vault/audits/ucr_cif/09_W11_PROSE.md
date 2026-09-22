# W11 — a representation-neutral declaration channel

**Wave range:** `8c39376..HEAD` on `ucr-cif/construction`. Pinned as a range
deliberately: W10 wrote "the EIGHT commits" into an artifact whose own commit made
the count nine, and the true figure was ten. An artifact cannot carry a final
cardinality that its own commit changes.

**Status of the treatment flag throughout signal construction:**
`STRUCTURAL_RANKING_ENABLED = False`, untouched. `MAX_OWNERS`,
`DISTINCTIVE_MAX_HOLDERS`, `MAX_DISTINCTIVE_REQUIRED`, `create_spec` and the
corpus are frozen. The 503 ABSTAIN and 218 UNRESOLVED stay open.

---

## 1. The mechanism, and why it is narrower than "prose is under-represented"

`ownership_evidence.build_structural_index` returns four channels. Two can promote
a candidate, and a prose owner can reach **neither**:

| channel | code owner | prose owner |
|---|---|---|
| `defined` — term-specific, promotes | `.py` AST symbols; `.js`/`.ts` via `_DECL_RX` | nothing: `_DECL_RX` holds `.js` and `.ts` only |
| `inbound` — owner-level, corroborates | Python `import` edges | nothing: a document cannot be imported |
| `named` | path words | path words |
| `registry` | JSON keys | JSON keys, if it ships any |

`.md` *is* scanned — `ALL_EXT` includes it — so a prose artifact contributes a bag
of words and a filename and then stops. `governance-overlay` holding 13.7 % of its
term-pairs structurally against a 21.0 % corpus average is a property of the
extractor, not of the owner. W9 measured the number; W11 names the cause.

## 2. Two of the frontier's three candidates are dead — measured before building

The W10 frontier proposed reading governance rule ids, document headings or
front-matter `covers:` keys as declarations. Supply was measured against the one
owner with a named mechanism-level defect behind it, before any policy was chosen:

| candidate | supply in `modules/governance-overlay` (10 files) | estate-wide |
|---|---|---|
| `covers:` front-matter | **0** | 40 files carry it, all elsewhere |
| headed rule ids | **1** (`MC-OVO-21`) | 28 files; `ukdl-universal.md` alone has 260 |
| document headings | **148** across 8 markdown files | 1,061 markdown files scanned |

Two of three have effectively no supply in the owner they were proposed to repair.
The third has abundant supply and is exactly what the mission forbids. This is
recorded as a falsification of the frontier's own action-1 shape, not as a
discovery made after the extractor was built.

## 3. What replaced them

Neither half is authority alone:

> A prose artifact becomes **declaration-capable** when a consumer outside it
> resolves a path to **that specific artifact** and acts on it. Its declarations
> are then read from its structured surface — headings, rule ids, `covers:` keys —
> never from its prose body.

An imported module defines symbols; a consumed contract declares headings. The
predicate never asks what the extension is.

**The discriminator lands inside the positive case.** Of nine artifacts under
`modules/governance-overlay`, four declare (`core.md`, `council.md`,
`mistakes-registry.md`, `post-output.md`) and four stay silent (`during-task.md`,
`pre-task.md`, `pre-output.md`, `zero-issue-baseline.md`) — same owner, same
directory, same extension. `pre-task.md` carries **81** declaration terms and earns
nothing, because nothing loads it. A family keyed on directory, on extension or on
vocabulary could not produce that split, and it is a stronger negative control than
any external README.

## 4. Provenance: the family this is NOT

Ranked by raw mentions, the top referrers of `governance-overlay` are the benchmark
and the adjudication the signal must stay independent of:

| referrer | mentions | class |
|---|---|---|
| `vault/ucr_cif/oracle_cases.json` | 4,734 | BENCHMARK — the W10 answer key |
| `vault/ucr_cif/disposition_ledger.json` | 452 | W3's own output |
| `vault/ucr_cif/structural_projection.json` | 37 | this signal's own projection |
| `ownership_evidence.py`, `disposition_consumer.py`, `owner_truth.py` | 2–3 | comments recording W9/W10's measurement of this owner |

A backlink count would have scored this owner overwhelmingly **from its own answer
key**, and the result would have looked like a triumph. Exactly one provenance class
promotes.

**Benchmark exclusion is a property of SCOPE, not of a check.** `vault` is not in
`SCAN_DIRS`, so the oracle is never walked. That is stronger than a guard — but it
also means the `BENCHMARK` provenance clause cannot fire on today's estate, and a
gate nobody has seen work is indistinguishable from one that passes. So the
classifier is driven directly, the scope invariant is pinned by its own gate, and a
directed mutation puts `vault` into scope to prove the invariant is load-bearing.

## 5. Admission neutrality

`ownership_evidence` does not import this module. `adjudicate` is untouched, so no
disposition moves and the ledger and corpus stay frozen. The channel reaches ranking
only through `structural_projection`, which is behind a flag that is `False`.
Evidence is not promotion, and the signal cannot mint authority.

## 6. What the mutations found

A surviving mutant is a question about reachability, not an automatic coverage gap —
so `W11-owner-disambiguation-removed` was measured rather than patched around.
Dropping the clause on the real estate:

| | with the clause | without |
|---|---|---|
| declared terms | 814 | **1,087** |
| owners earning declarations | 26 | **51** |
| spurious CONSUMER edges admitted | — | **418** |

The cause is a real population: `coding-style.md`, `hooks.md`, `patterns.md`,
`security.md` and `testing.md` are each shared by **20** prose artifacts, so every
`rules/*` language pack would be credited by any file that mentions one of those
names. Reachable, not equivalent, not defensive-only — so it earned a gate, with a
synthetic two-owner collision case that represents the class and a floor assertion
proving the collision population is real.

## 7. PR-W10-11, closed

W10 computed a population fingerprint and printed it; nothing ever compared two, so
the guard that makes a paired verdict mean anything had never run. `compare_fingerprints`
now returns three outcomes — UNREADABLE is neither DRIFTED nor COMPARABLE, because a
fingerprint that could not be read says nothing about drift — names the keys that
moved, and is gated by a **positive** licence test so a status added later cannot
widen it. Driven on the real 1,471-case store and through the shipped `--compare`
CLI, both poles.

One instrument defect was found and fixed before it could hide anything: the
every-key test looped over the module's own `_FP_KEYS`, so a mutation *narrowing*
that tuple would have shrunk the test with it and passed.

## 8. Cost

`build_edges` is the expensive half at roughly 13 s over 319 prose artifacts and is
offline by construction, compiled at the existing `structural_projection` build
boundary. Deriving declarations from compiled edges costs **~1.8 ms**. Nothing on a
selection path parses a document, walks git, or traverses the vault.

## 9. PR-W10-10

Still **OPEN — NOT EXERCISED**. No real label defect surfaced during this wave, and
a gold label will not be mutated to make the correction lineage look driven. A
production claim requires a production event.
