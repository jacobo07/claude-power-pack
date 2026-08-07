# CDICF — NEXT ACTIONS

Ordered. Each is one sitting. Do not reorder without recording why in
`CDICF_DECISION_LOG.md`.

## Immediate — CLOSED 2026-08-06

| # | Action | State |
|---|---|---|
| 1 | Resolve Tailark's copyright holder | **DONE** — MIT © 2025 **Irung**, read from `LICENCE.md`. Confidence OBSERVED → VERIFIED |
| 2 | Resolve `nilbuild/driver.js` canonicality | **DONE** — rename redirect, not a fork. Both API paths return one identical object (`fork: false`, no parent, 2018-03-11, 26,544 stars). Canonical: `nilbuild/driver.js` |
| 3 | Pin all 5 upstream commits + fingerprints | **PARTIAL** — all 5 commits pinned from the API. Fingerprints deliberately `PENDING_CLONE` (decision D-008): fetched license text can be whitespace-reflowed, so a hash of it would not match repository bytes and would false-positive on `--expect` |

Remaining legal debt: **fingerprints only**, and only at clone time. Holders and
canonicality are settled; attribution rows can now be written.

## A2 — Component Manifest — SEALED 2026-08-06

Shipped in `modules/cdicf/` (schema, dependency-free validator + CLI, two examples,
README) with 21 tests. Six invariants enforced; INV-02 refuses to record a
redistribution-prohibited component as a fork — the structural form of the React Bits
decision.

| # | Remaining | Done when |
|---|---|---|
| 5 | Emit Upstream Mirror Ledger rows from `license_gate.js --json` rather than by hand | A ledger row is produced by the tool, not typed |

**Trap (confirmed in practice):** new files under `lib/` are **gitignored**.
`lib/license_gate.js` commits only because it was already tracked; `git add lib/...`
prints "The following paths are ignored". A2 therefore lives in `modules/cdicf/`.

**Trap (confirmed in practice):** three of five upstreams do not name their license file
`LICENSE` — `LICENSE.md`, `LICENCE.md` (British), and lowercase `license`. Fixed in
`findLicenseFiles`; assume nothing about the filename or the default branch (`driver.js`
is on `master`).

**Gap (D-009):** `modules/liveness/reachability.py` enumerates Python packages only, so
`modules/cdicf/` is absent from its 343 modules rather than passing. Its reachability is
asserted by its tests and nothing else until the scanner discovers JS subjects.

## A3 — Registry producer — SEALED 2026-08-06 (partial: rollback outstanding)

`modules/cdicf/registry_emitter.js`, 16 tests.

| # | Action | State |
|---|---|---|
| 6 | shadcn-format registry entry + install manifest per component | **DONE** — `registry-item.json` + `install-manifest.json`, checksummed, artifacts sorted so the digest is filesystem-independent |
| 7 | Commit-pinned deterministic install **+ rollback + interrupted-install recovery** | **DONE** — pinning and determinism at A3; rollback and interrupted-install recovery delivered by A3b (`modules/cdicf/installer.js`, 24 tests). Action 7 is closed |
| 8 | **Redistribution guard** — refuse any prohibited component | **DONE** — refused at exit 5 with zero bytes written (`V-EMIT-01`, `V-EMIT-02`). Posture is *derived* from `license_tier` via the gate, never read from the manifest field, so a hand-edited manifest cannot walk past it (`V-EMIT-03`) |

Action 8 was the load-bearing one: INV-02 is no longer a schema opinion, it is a system
boundary. The registry is the distribution channel, so refusing here is refusing to
redistribute.

**RATIFIED (D-011), 2026-08-06:** `--reference-only` stands. Owner's ruling —
redistribution is the movement of code, and a URL is not code. The Motion Gateway
namespace is in scope with the pointer path as its emission mode.

## A3b — Installer, rollback, recovery — SEALED 2026-08-06

`modules/cdicf/installer.js`, 24 tests. Action 7 closed.

| # | Action | State |
|---|---|---|
| 9 | Transactional installer consuming `install-manifest.json` | **DONE** — journalled; `V-INST-03`/`V-INST-04` kill a real process (`exit 137`) inside the rename sweep and recover the exact pre-state |
| 10 | Checksum verification on install | **DONE** — content is hashed against the install manifest before any write (`V-INST-15`), the roll-up is recomputed rather than trusted, and postconditions are read back from disk (`V-INST-19`) |

Beyond the brief, because each was a gap the work exposed rather than a feature added:
`verify` (post-install drift, `V-INST-20`) · path-traversal containment (`V-INST-16`) ·
the journal as mutex, refusing a live transaction (`V-INST-21`) · recovery that **declines**
to delete a file edited after the interruption (`V-INST-07`).

**Not claimed:** filesystem-level multi-file atomicity, which no portable filesystem
offers. What is guaranteed is stated precisely in `modules/cdicf/README.md` — nothing
committed partially, every partial state detectable and reversible, the window bounded to
the rename sweep. Between an abrupt kill and the next invocation a partial tree does exist
on disk. That is recovery, not prevention, and it is named as such.

## A4 — Selection + Abstention — SEALED 2026-08-06

`modules/cdicf/selector.js`, 25 tests.

| # | Action | State |
|---|---|---|
| 9 | Hard filters → soft scoring → explanation → abstention | **DONE** — six abstention codes, each with a reason and a remedy. `V-SEL-17` returns "build it" on a field of poor fits; `V-SEL-09` refuses a tour over unresolved UX findings as the wrong remedy entirely |
| 10 | Prior-adoption enters as a **tiebreak only**, never a scored term | **DONE** — `V-SEL-16`: an already-used component loses to a better fit, and no contribution row names it |

Both inherited constraints were honoured structurally rather than by intention:

- *A score whose factors are per-item constants ranks nothing.* Relevance is a **hard
  filter first** and a weighted term second (D-014, `V-SEL-12`) — zero relevance removes a
  candidate rather than costing it points it can win back on maturity.
- *A composite score mapped onto a hard verdict kills whole classes.* Hard filters are
  independent predicates evaluated **before any score exists**; the composite only ever
  decides ranking and the absolute `MIN_SCORE` floor. No conjunct is derived from a score.
- Thresholds are absolute, never ratios or percentiles (`V-SEL-17`) — a percentile always
  crowns someone no matter how bad the field is.
- The matching vocabulary is **discovered from the candidate set**, so an unrecognised
  intent returns `NO_RECOGNISED_INTENT_TERMS` rather than looking like "nothing fits"
  (`V-SEL-11`). Zero cannot fall, so the two must not share an output.

**Found by real-input verification, after 23/23 synthetic tests passed first run** (D-015):
a self-matching relevance signal, and a "dominant cause" reported over a tie. Sealed as
`T-SELF-MATCHING-RELEVANCE-SIGNAL-001` and `T-DOMINANT-OF-A-TIE-001`.

The engine **never installs**. `V-SEL-22` asserts it both behaviourally (no filesystem
writes) and structurally (no import path to the installer).

## A5 — Adversarial evaluation corpus — SEALED 2026-08-06

`tests/a5_adversarial.test.js`, 41 scenarios across LEGAL · SELECTION · INSTALL · REGISTRY ·
BOUNDARY · TRAP, plus a meta-scenario asserting the corpus's own size and category spread.

| # | Action | State |
|---|---|---|
| 11 | ~40 adversarial scenarios as executable cases | **DONE** — 41 scenarios, each carrying `what_it_tests` (the property) and `why_it_could_fail` (the mechanism), both printed on failure. **Six failed on first run**, exposing four distinct defects, all fixed in the same commit (D-016) |

Each scenario is declarative and executed by a loop, so it passes or fails binarily with
its own metadata as the evidence. Most run through the **CLI** rather than the exported
functions: argv parsing, exit codes and wiring are part of the contract, and a suite that
only calls exports can pass while the real entry point is broken.

**What the corpus actually bought.** 117 tests written alongside the engines were green.
41 scenarios derived from the *brief's stated requirements* rather than from the code found
four defects those 117 could not see — a prose-only remedy, an omitted scoring dimension,
an unresolved-dependency install that passed every gate, and a `minLength` constraint that
admitted whitespace. That is the argument for A5, measured rather than asserted.

**The honest limit:** these scenarios were still written by the engines' author. Deriving
them from the specification narrows that bias; it does not eliminate it. A genuinely
independent instrument is a different agent or a real consuming project, and neither has
run yet.

Hermetic: 42/42 identical across three consecutive runs.

## Extensions — 6 of 6 done

| # | Extension | State |
|---|---|---|
| **E1** | `DESIGN.md.template` +9 decisions | **SEALED** `e9d5170` — a Component Provenance section whose nine decisions **are** the selector's `--context` object, so a decision recorded there changes what the engine refuses. Verified against the real gate, not assumed: `V-DESIGN-TEMPLATE-CLEAN` still APPROVE score=100 family=F3 |
| **E6** | `DESIGN_GOVERNANCE.md` +3 clauses | **SEALED** `63ccfff` — Section 8: reuse-first, provenance-mandatory, tour-as-last-resort, each backed by an exit code rather than a habit |
| **E2** | `design_index.py` + component FTS5 sidecar | **SEALED** `a8d9947` — own **database file**, own tables and triggers; 15 gates in `tools/test_cdicf_index.py`, hermetic 3× |
| **E3** | graphify integration | **SEALED** — **not** as proposed. One `_GOV_ID` token, ontology untouched, 8 gates in `tools/test_cdicf_graph.py` |
| **E4** | installer kill switch (HR-APA-009) | **SEALED** `7c9ec1d` — sentinel + signal, journal **preserved**, `ABORTED_BY_KILL_SWITCH` recorded; 10 gates in `tests/killswitch.test.js` |
| **E5** | `modules/cdio` dependency-scope hard filter | **SEALED** `ddd6334` — CRITICAL **before** the score, `score_review` untouched, §5 gate measured unchanged; 10 gates in `tools/test_cdicf_scope.py` |

### E3 — the proposal was wrong twice, and the record said so

Two premises failed verification before a line was written:

- **The named owner does not own it.** `modules/graphify/indexer.py` is CLI plus repo
  discovery. `NODE_TYPES` is defined in `tools/graphify_knowledge.py:57`.
- **The extension itself was already decided against.** In July an identical proposal
  for CDIO was reality-scanned and the Owner approved **riding the existing types**,
  because editing the ontology re-indexes 722 coordinates for every repo
  (`vault/plans/cdio-build-2026-07-05.md` decision 1; `scs_c78_cdio_active.md`).

CDICF follows that precedent instead of re-litigating it. The entire change is one token
— `CDICF[-_]` added to `_GOV_ID` in `global_store.py`, mirroring `CDIO-\d` exactly.

Two things are asserted that a naive suite would not have:

- **Blast radius is measured.** 106 files mention the word; the token requires the
  *identifier* form, so prose does not promote (`V-CDICF-GRAPH-04`). A signal gate that
  says yes to everything is not a gate.
- **The ontology is pinned frozen** (`V-CDICF-GRAPH-07`). A later session that adds a
  `component` node type fails this gate. Without it, someone could pass every CDICF test
  while quietly taking the blast radius the Owner declined. The frozen count is measured
  from source, not assumed — the first draft guessed 12 against a real 10 and failed
  correctly.

CDICF's A5 traps were **already** promotable under the pre-existing `T-[A-Z]` token, and
`V-CDICF-GRAPH-03` says so, so this change is not credited with coverage that predates it.

### E4 — the kill switch, unblocked by an Owner decision

The premise was still false — `modules/capability_runtime/` has no activation-mode
concept, and "4 activation modes" appears only in CDICF's own plan. What was buildable
was the thing that phrase was standing in for: **the kill switch HR-APA-009 demands of any
write surface**, plus the contract that declares it
(`vault/capability_runtime/contracts/cdicf-installer.json`).

**The mechanism was chosen from the estate, then corrected by a fact about the host.**
PP's convention for a long-running process is a SIGTERM/SIGINT handler with graceful
shutdown. That alone would have been *inert here*: Node never **emits** SIGTERM on
Windows, so a signal-only switch is a switch that cannot fire — the disarmed-kill-switch
shape already on this estate's record. The portable arm is therefore a sentinel file
(`<target>/.cdicf/KILL_SWITCH`), cross-process and inspectable, with signals honoured
where the platform delivers them and listeners removed on every exit path.

Semantics, per the Owner's ruling:

- Armed **before** start → refuse at exit 12 **without creating a journal**; refusing
  after the lock would leave a dirty-state marker for a transaction that touched nothing.
  Checked in `install()` as well as `applyPlan`, so an idempotent no-op and a dry run
  cannot report success into a project someone has explicitly fenced off.
- Mid-transaction → stop at the next seam. There is now a seam per **write**
  (`staging-file`, `backup-file`), because "stop before the next write" is only true if a
  checkpoint exists before each one.
- In the rename sweep → the in-flight `renameSync` completes (one atomic syscall) and the
  sweep stops before the next. `V-KILL-05` asserts exactly one rename landed.
- **The journal is preserved**, which is why the abort is handled *before* the generic
  catch: `recover` deletes the journal, and the journal is the post-mortem. An abort
  stops; `recover` repairs — and now archives to `.cdicf/aborted/<txid>.json`, so the
  evidence outlives the repair (`V-KILL-06`).
- `ABORTED_BY_KILL_SWITCH` lands in `installed.json` as an `aborted` audit row, never in
  `components`. The component was not installed, and a record claiming otherwise is worse
  than none (`V-KILL-04`).
- Earlier committed installs are untouched (`V-KILL-07`). It stops what is in flight; it
  is not a retro-active uninstall.
- It does **not** auto-disarm, and every refusal names the disarm command (`V-KILL-02`) —
  a switch that resets after one trip is a pause button, and one nobody can turn off is an
  outage.

HR-APA-009 was **observed refusing** an empty `kill_switch` and an empty `rollback`, not
assumed to pass.

### E5 — the dependency-scope filter, and why it is not a Verdict

The blast-radius concern was real, and the Owner's ruling resolved it: a missing dependency
is CRITICAL because it is observable in production on first render; a low score is a
judgment and is not.

That forced the design. A `critical` **Verdict** subtracts 25 inside `score_review`, so
emitting one would have changed score *composition* — the exact 82→78 drift this row was
deferred over. So the check is **not a Verdict**. It is a hard filter evaluated before any
score exists (`review_gate`), and `score_review` is untouched. CRITICAL does not lower the
number; it means the review never reaches one, and `GateResult.score` is `None` rather
than a deduction (`V-CDICF-SCOPE-06`).

**Measured, not asserted.** A snapshot of every real `DESIGN.md` plus an 11-case verdict
matrix spanning the boundaries was captured *before the first edit* and re-measured after:
byte-identical. `APPROVE_MIN` is still 80, and `review_gate` with no target equals
`score_review` exactly.

What it buys beyond the installer: the installer resolves dependencies at **install** time
(exit 11) and structurally cannot see a dependency removed a week later. `V-CDICF-SCOPE-05`
exercises exactly that against a real emitter+installer install. Two guards, two moments,
not redundant. Three states, never two — a record predating dependency tracking is
`unassessed`: reported, not blocking, because blocking would inert the gate on day one and
passing silently would launder an unknown into a yes.

Historical note, kept because it was the deferral's own reasoning: `modules/cdio/` is 4
Python files, not the 12 the ledger claimed, and `scorer.py` is 376 lines.

Constraint that still stands for whoever adds the next check: **do not add a check without
re-measuring existing
scored surfaces.** A criterion that silently re-scores history is indistinguishable from
a regression.

E1 and E6 were taken first because they are the two that make the spine *reachable*: until
a project's governance tells someone to run the selector, four working executables are a
capability nobody's process invokes.

### E2 — the isolation decision, and why it went further than the brief

The pre-existing `design_tools` index lives **inside** the shared
`SOVEREIGN-HISTORY-VAULT.db` alongside `turns` / `turns_fts`, isolated only by table
naming. Shared substrate, so the sidecar takes its own file: `CDICF-COMPONENT-INDEX.db`,
resolved by `--db` > `CDICF_INDEX_DB` > a sibling of the vault DB.

Naming alone would have satisfied the constraint and left it a convention. Instead
`_assert_isolated` reads `sqlite_master` and **refuses to build** into any database
holding `turns*` or `design_tools*` (`V-CDICF-IDX-04`, exit 3). Pointing `--db` at the
shared vault is now an exit code rather than a mistake review has to catch.

Two design decisions carry more weight than the search itself:

- **Provenance is absent from the schema, not merely unindexed.** There is no
  licence, fingerprint or holder column to leak into a text match — searching a real
  `copyright_holder` returns `NO_MATCH` (`V-CDICF-IDX-03`). Licence posture is a hard
  filter decided by the gate; it must never be a rankable term.
- **An empty result has three exit codes, never one.** `NO_INDEX` (30), `INDEX_EMPTY`
  (31) and `NO_MATCH` (32) are distinct, and freshness is reported separately
  (`--strict-fresh` → 33). A stale index answering "nothing" is answering *cannot say*,
  and collapsing that into "no component fits" is how a component that exists reads as
  a genuine gap.

**Wiring, because an unreachable index is an orphan module.** `selector.js` gained
`--candidates-from <file.json>`, consuming the sidecar's `candidates` array. The decision
now carries `candidate_source`: a narrowed set is labelled `mode: "search"` with the
caveat that a component absent from the index could not be considered — an abstention
over a narrowed set is partly a statement about the query. An **empty** narrowed list is
refused at exit 3 rather than forwarded (`V-CDICF-IDX-14`): passing it through would let
a search miss become a verdict about the catalogue and produce "build it".

Install state is read from the installer's `installed.json`, never inferred from files on
disk, and clears again on retirement (`V-CDICF-IDX-08`/`09`) — a one-way flag would read
as installed forever after the first install. The indexed set itself is **discovered** by
walking the manifest directory, so it cannot drift the way an incrementally-maintained
record does.

The directory path is unchanged and still labelled `mode: "directory"`
(`V-CDICF-IDX-15`), so `DESIGN_GOVERNANCE.md` §8.1 remains accurate as written.

## Standing gates

- `python modules/liveness/reachability.py` — every new module wired, declared or deleted.
- Gate on absolute counts, never ratios.
- No dataset prose describing an engine that does not run.
