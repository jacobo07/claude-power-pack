# GSD X — resumption contract after wave N5

**Written 2026-09-22.** Self-contained: a fresh worker continues from this file
with no prior conversation. Read `gsd-x-n4.RESUMPTION.md` for N4's closed items
and `gsd-x-n3.RESUMPTION.md` for N3's; nothing in either is superseded here.

## Identity

- Repo `C:\Users\User\.claude\skills\claude-power-pack`
- Canonical **development**: `feature/knowledge-acquisition`
- Canonical **release**: `main`
- **HEAD at writing: `8bd2c04`**, and `origin/feature/knowledge-acquisition`
  is the same commit — **0 ahead, 0 behind**.

### Correct the handoff before trusting it

The N4-to-N5 handoff reported HEAD `572cd5a` and "8 commits ahead, unpushed".
Both were false when measured at the start of N5:

| reported | measured |
|---|---|
| HEAD `572cd5a` | `8bd2c04` — `26cf3f8` and `8bd2c04` (kclaude paste-window, NGEN) landed after, from another pane |
| 8 commits ahead, unpushed | 0 ahead / 0 behind; already pushed |
| working tree clean (session snapshot) | **441 dirty paths** — 41 modified, 400 untracked |

A handoff is a hypothesis. The Reality Scan is the authority, and the session's
own git snapshot is not a Reality Scan.

## What must NOT be re-litigated without new evidence

Carried forward from N4, unchanged and still binding:

1. **Derivation does not generalise from prose (GSDX-M04).** The operators are
   general over FACTS; the prose extractor is a closed vocabulary, fitted by
   construction. Three domains cost three pattern corrections. **N5 note: this
   is now CLOSED by `572cd5a`** — facts can be declared, so the operators no
   longer wait on a vocabulary. Do not re-run the three-domain experiment.
2. **The gate is proven at the CONTRACT, not at the EVENT (GSDX-M05).**
   **N5 note: superseded in part.** Registration, activation and reachability
   are now proven (below). The EVENT — a real live ship — is still open.
3. **Derived obligations enter GSD at PLANNING, never as verifier findings
   (GSDX-D13).** `verifier-evidence-gate.md` silently demotes an obligation
   routed there to advisory.
4. **DAIF does not own derived obligations (GSDX-M06).** It requires a
   commitment frame and refuses wishes; its intake would discard this whole
   population. Field names were reused; ownership was not.
5. **GSDX-U08 was an EQUIVALENT mutant (GSDX-M07).** `_silence_dormant` is a
   live backstop. Do not delete it; do not re-add a mutant to it.
6. **A dated measurement takes `commit:`, a standing property takes `path:`
   (GSDX-D12).** Pinning a dated fact to a live blob manufactures a permanent
   false stale.

New in N5, and equally binding:

7. **The liveness blocker is HOST RAM STARVATION, and it is not a hypothesis.**
   It is written into `~/.claude/hooks/hook-dispatcher.js:408-415`, with its
   own measurement: the HR-SECRET-001 gates are *not slow* — secret-scanner's
   isolated median is **228 ms against a 5000 ms budget** — they die because
   the host is starved, and under starvation a 228 ms spawn exceeds any budget
   you can write. Measured 844 MB free of 32 GB then; **651 MB during N5**.
   Both gates are `critical: true`, so a timeout **fails closed**: the write is
   denied with *"HR-SECRET-001 could not be enforced ... detector timed out"*.
   **A denial with that wording is not a secret finding.** Do not investigate
   the content; do not weaken the gate; do not route around it. N5 reproduced
   this denial first-hand on its first attempt to write this very file.
8. **The orphan reaper is safe, and on this host it had nothing to do.**
   Measured in N5, not assumed: self-tests `HUSK_SELFTEST=5/5` and
   `GHOST_SELFTEST=15/15`, every refusal branch driven plus the disjointness
   control. A live run then logged **`GHOST_CLEAN scanned=57`** — zero ghost
   and zero abandoned-hook orphans — and reaped exactly **1** dev-server
   orphan. Free memory moved +160 MB across the run while `node.exe` rose
   27 to 40 from other sessions, so **that delta is not attributable to the
   reaper**. It cannot touch `claude.exe`: it enumerates only `node.exe` and
   `python*.exe`, so the Owner's sessions are out of scope by construction,
   and every rule additionally requires the parent to be dead.
   Do not reach for it as the memory lever without first re-reading its log:
   if it says `GHOST_CLEAN`, the population is empty and the lever is absent.
9. **`sh` exists on this host and is not on PATH.** `C:\Program Files\Git\bin\sh.exe`
   and `...\Git\usr\bin\sh.exe` both exist; `Get-Command sh` fails. So the open
   question is a **resolution contract**, never "Windows-incompatible". A
   PowerShell-spawned probe is a proxy for the GSD dispatch environment and is
   not evidence about it.
10. **`host-memory-floor.js` already owns host-memory visibility.** SessionStart,
    `critical`, zero spawns, fail-open, 420 readings logged to
    `~/.claude/logs/host-memory-floor.json` (OK 291 / WARN 85 / CRITICAL 44).
    It *reports*; it does not repair. Do not build a second one.
11. **The host drifts fast enough to confound any before/after reading.**
    Measured within minutes in N5: 797 -> 3005 -> 651 -> 1728 -> 1888 MB. Any
    memory claim must be bracketed on both sides and attributed by process
    identity, never by a single delta. A monotonic-looking curve here is a
    property of the host, not of the change.

## State

**W1 (GSDX-M05) and W2 (GSDX-M04) both advanced materially.** Commits, oldest
first:

    5524f09  seam measurement: execute:wave:post cannot dispatch the gate
    297024e  gate moved to ship:pre; activation key made reachable
    e6d20a2  reachability gate, 9/9, 7/7 mutations
    c7b4f61  upstream consent defect characterized, 3/3 + red branch
    572cd5a  FACTS.json — facts can be declared, 15/15, 7/7 mutations

### The capability, as registered

`capabilities/cpp-gsd-x-mission/capability.json`

    point          ship:pre          (bound to gsd-core ship.md:168)
    when           gsd_x_mission.enabled
    blocking       true
    onError        halt
    predicate      command-exit-zero -> execTool('sh', ['-c', ...])
    activationKey  gsd_x_mission.enabled, default FALSE

Global install does **not** activate it: the key is absent from this repo's
`.planning/config.json`, and every other GSD project on the host is unaffected
until it sets the key itself. That asymmetry is deliberate and measured.

### Proof grades — claim strength never exceeds the boundary crossed

| layer | grade | instrument |
|---|---|---|
| registry | PROVEN | manifest present, gate at `ship:pre` |
| activation | PROVEN | key reachable, default false, project-scoped |
| reachability | PROVEN | `test_gsd_x_manifest_reachability.py` 9/9, 7/7 mutations, binding derived from gsd-core's own workflow files |
| structured facts | PROVEN | `test_gsd_x_structured_facts.py` 15/15, 7/7 mutations, G2-PARITY mechanically derived from sealed blobs |
| consent defect | CHARACTERIZED | `test_gsd_x_consent_integrity.js` 3/3 + driven red branch |
| **live ship dispatch** | **UNPROVEN** | never dispatched |
| **`sh` in real dispatch env** | **UNPROVEN** | only a PowerShell proxy exists, and it does not count |
| **FACTS.json producer** | **ABSENT** | no instance of `FACTS.json` exists anywhere on disk |

Production Reality: **FIRST_VERTICAL_SLICE**, `UNIVERSAL_CAPABILITY_UNPROVEN`.

Regression at N5: mission 17/17 · mission mutations 6/6 · gsd-x 15/15 ·
parity 7/7 · reachability 9/9 · consent 3/3.

## Open, with exact next action

| item | state | next |
|---|---|---|
| **W1 live ship drill** | never dispatched | drive `gsd-ship` in a **disposable scratch GSD project**, never this repo (its `.planning/` is shared and already dirty). Three poles: RED (obligation open, halt, names DO-1) · GREEN (gate verdict satisfies; narrative must not) · NEGATIVE CONTROL (capability deactivated, the protection demonstrably stops) |
| **`sh` portability contract** | binary exists, not on PATH | measure *inside* the dispatch, then fix at the owning layer: declared requirement plus resolution. Not environment magic |
| **Manifest hardcoded paths** | E11 violation, shipped | the predicate embeds absolute `C:/Users/User/...` for both python and the tool. Portable resolution owed |
| **FACTS.json producer** | hidden human job | derive a small number of facts from authoritative sources, with provenance (observed/derived/declared/assumed), staleness detection, `UNKNOWN` distinct from false, no second source of truth |
| **Drift decision layer** | detector exists in GSD Core | add decision semantics on top; **do not build a second detector**. It must distinguish irrelevant HEAD movement from semantic-owner change — with 441 dirty paths and foreign commits here, that relevance test is not academic |
| **Trust disclosure** (`capability-trust.cjs:635`) | upstream-owned, characterized | re-scan whether upstream moved; keep provenance; no vendor mutation; the pre-migration backup at `~/.claude/gsd-local-patches` is **not** a source of truth |
| **`-GhostSelfTest` is not side-effect-free** | found in N5 | the live Electron-husk scan runs before the flag is checked, so a "self-test" can reap. `-HuskSelfTest` exits earlier and is clean. Move the flag check above the husk block |
| `EXTERNAL_GITHUB_ENFORCEMENT_PENDING` | `.github/` still absent | needs repo-admin authority; unchanged since N3 |
| UKDL promotion | `PROMOTION_PENDING_CONCURRENT_WRITER` | the canonical file had a live writer at every prior attempt |
| 56 claims unpinned | frozen, shrink-only | ratchet fails on new debt, stale entries and stale pins |
| One-level derivation only | by decision | Consequence Closure comes after the fact producer, not before |

## Next highest-leverage capability

**Produce facts from authoritative sources.** `572cd5a` moved the vocabulary
burden from a regex to whoever writes `FACTS.json`; it did not remove it, and
the commit body says so in its own words. No `FACTS.json` exists on this host,
so the surface is consumable and unfed. Everything above it is proven at N=1.

Do this before Consequence Closure, before the Unknown Queue, before the
Assumption Graph — for the same reason N4 gave: recursing a derivation whose
base case is hand-authored multiplies the authoring problem rather than
escaping it.

## Owners that must NOT be duplicated

GSD Core (lifecycle, plan, phase, transition, verifier evidence gate, **plan
drift detection**) · Capability Runtime (applicability, dormancy-before-evidence
ordering) · DAIF (stated obligations) · Graphify (typed edges) · Done Gate plus
strength ladder plus Production Reality · `claims.jsonl` (PROGRAM knowledge,
never mission state) · `host-memory-floor.js` (host memory visibility) ·
`hook-dispatcher.js` (chain scheduling, critical lane, deadlines) ·
`orphan-dev-server-reaper.ps1` (orphan process reclamation).

## Next exact valid action

Drive the W1 live ship drill in a scratch project, measuring `sh` inside the
dispatch environment as it runs. If the host is under `host-memory-floor.js`'s
CRITICAL floor (1024 MB), expect protected writes to be denied for liveness
rather than for content — that is rule 7 above, not a new problem, and the
reaper is only the answer if its log says there are orphans to take.
