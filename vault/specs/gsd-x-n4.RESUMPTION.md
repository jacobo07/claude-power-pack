# GSD X — resumption contract after wave N4

**Written 2026-09-20.** Self-contained: a fresh worker continues from this file
with no prior conversation. Supersedes nothing in `gsd-x-n3.RESUMPTION.md`;
read that one for N3's closed items.

## Identity

- Repo `C:\Users\User\.claude\skills\claude-power-pack`
- Canonical **development**: `feature/knowledge-acquisition`
- Canonical **release**: `main`
- Reconciled through **`5d09fad`** (`vault/datasets/gsd_x/RECONCILED-THROUGH`)

## What must NOT be re-litigated without new evidence

1. **Derivation does not generalise (GSDX-M04).** The operators are general over
   FACTS; the prose fact-extractor is a closed vocabulary and is fitted by
   construction. Measured across three domains: domain 2 cost two pattern
   corrections, domain 3 cost one more verb. Do not re-run this experiment to
   confirm it — replace the reality adapter with structured input and re-test.
2. **The gate is proven at the CONTRACT, not at the EVENT (GSDX-M05).**
   `gsd_x_mission.py check` emits exactly `{block, message}`, and GSD's
   dispatcher halts wave completion on `blocking:true` + `block:true`. No
   capability manifest was registered because none was found on this host. Do
   not report this as an integration.
3. **Derived obligations enter GSD at PLANNING, never as verifier findings
   (GSDX-D13).** GSD's `verifier-evidence-gate.md` requires deterministic
   evidence for a new-scope finding to BLOCK and downgrades one without it to
   advisory. An obligation routed there is silently demoted. Measured from GSD
   Core's own reference, before any integration code existed.
4. **DAIF does not own derived obligations (GSDX-M06).** Contract audit: it
   requires a commitment frame and refuses wishes, so it extracts obligations
   someone STATED. Its intake would discard this entire population. The field
   names were reused; the ownership was not.
5. **GSDX-U08 was an EQUIVALENT mutant (GSDX-M07).** `_silence_dormant`
   compensates for an ordering defect the Capability Runtime fixed at source, so
   with upstream correct no producer constructs the state it discriminates. The
   filter is KEPT — driven with gate 1 disabled it removes the blocked verdict,
   so it is a live backstop. Do not delete it and do not re-add a mutant to it.
6. **A dated measurement takes `commit:`, a standing property takes `path:`
   (GSDX-D12).** Pinning a dated fact to a live blob manufactures a permanent
   false stale.

## State

**N4 is CLOSED.** Ledger 87 → 108 claims, 52 pinned, 56 frozen.

    dataset gate     11/11 exit 0      drill            10/10 both poles
    GSDX suite       15/15 exit 0      GSDX mutations     2/2 semantic
    mission suite    17/17 exit 0      mission mutations  6/6 semantic
    reconciler       0 uncovered, 0 stale, exit 0

Production Reality: **FIRST_VERTICAL_SLICE**, `UNIVERSAL_CAPABILITY_UNPROVEN`.

`continuation-proven-live` v1 is **untouched**. `.planning/STATE.md` was read and
never written. Another pane committed 12 times during this wave and was working
`ukdl-universal.md` 2m44s before the knowledge writeback; nothing of theirs was
committed, formatted, stashed, reset or absorbed.

## The vertical, as built

    INTENT.txt + README.md
      -> extract_facts()            7 named facts, each with the span it matched
      -> 3 operators                IRREVERSIBILITY / ABSENT_SIGNAL / FAILURE
      -> judge()                    CANDIDATE -> ACCEPTED | REJECTED | N/A
      -> store.save()               one JSON file under the mission root
      -> project()                  Mission Contract: 2 STORED, rest PROJECTED
      -> evaluate_transition()      only a gate verdict satisfies; narrative never
      -> project_closure()          DENIES while an accepted obligation is open

    modules/gsd_x/mission/{contract,obligation,store,closure}.py
    tools/gsd_x_mission.py            derive | contract | closure | check
    tools/test_gsd_x_mission.py       17 gates
    tools/test_gsd_x_mission_mutation.py  6 semantic mutations
    vault/benchmarks/mission_spine/   sealed fixture + HOLDOUT-SEALED.md + run/

## Open, with exact next action

| item | state | next |
|---|---|---|
| **Prose reality adapter** (GSDX-M04) | closed vocabulary, fitted | replace with structured project facts; re-test against a domain nobody wrote a pattern for. **Highest leverage item in this file.** |
| **GSD manifest registration** (GSDX-M05) | envelope proven, event not | locate a GSD capability manifest schema, register a hook at a lifecycle point, drive a real wave and observe the halt |
| `EXTERNAL_GITHUB_ENFORCEMENT_PENDING` | `.github/` still absent | needs repo-admin authority; unchanged from N3 |
| UKDL promotion | still `PROMOTION_PENDING_CONCURRENT_WRITER` | N3's 5 candidates in `vault/lessons/knowledge-stale-by-omission.md`, N4's 13 in `vault/lessons/derived-obligation-first-vertical.md`. The canonical file had a live writer at both attempts |
| 56 claims unpinned | frozen inventory, shrink-only | backfill further subsets; the ratchet fails on new debt, stale entries and now stale pins |
| `depends_on` kind `report:` | never implemented, and now REFUSED loudly | `gate:`/`report:` were retired in favour of an instrument failure on any unknown kind. Implement only when evidence demands one |
| One-level derivation only | by decision (§55) | Consequence Closure — obligation from obligation to a fixpoint — is the wave after the adapter |

## Next highest-leverage capability

**Replace the reality adapter.** Everything above it is proven at N=1 and the
adapter is the measured ceiling: three domains, three corrections, and the fourth
will cost a fourth. Structured project facts — from the codebase, the
infrastructure description, the runbook — is what turns "survives three wordings"
into a claim about derivation rather than about regular expressions.

Do this before Consequence Closure, before the Unknown Queue and before the
Assumption Graph. Recursing a derivation whose base case is a closed vocabulary
multiplies the vocabulary problem; it does not escape it.

Owners that must **not** be duplicated: GSD Core (lifecycle, plan, phase,
transition, verifier evidence gate) · Capability Runtime (applicability, and it
owns the dormancy-before-evidence ordering) · DAIF (stated obligations) ·
Graphify (typed edges) · Done Gate + strength ladder + Production Reality ·
`claims.jsonl` (PROGRAM knowledge, never mission state).
