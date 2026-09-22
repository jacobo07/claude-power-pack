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
9. **`sh` does not resolve in GSD's dispatch surface, and that makes the gate
   fire ALWAYS. MEASURED, not open.** Answered later in N5 through the surface
   that actually dispatches the gate — `shell-command-projection.execTool`, the
   function `check-command-router.cjs:1100` calls — rather than through a
   PowerShell proxy:

       resolveExecutableBinary('sh')   -> null
       execTool('sh', ['-c', 'echo'])  -> exit 127, "sh: not found"

   `sh.exe` exists twice (Git for Windows `bin\sh.exe`, `usr\bin\sh.exe`), so
   this is a **resolution contract**, never "Windows-incompatible".

   **The consequence is the severe part.** Our only surface is a
   `command-exit-zero` gate, and `gate-predicate-evaluator.cjs:94-102` maps any
   non-zero exit to `block: true`. With `blocking: true` and `onError: halt`,
   `ship.md` step 2 halts. Driven end to end, real manifest through the real
   evaluator:

       {"block":true,"message":"command exited 127: sh: not found",
        "details":{"kind":"command-exit-zero","exitCode":127}}

   **So `gsd_x_mission.enabled` must NOT be switched on for any GSD project on
   this host.** It would halt every ship, unconditionally, for a reason with
   nothing to do with obligations. Pinned by `tools/test_gsd_x_sh_dispatch.js`
   (4/4), whose `V-GSDXSH-DEFECT` is written to go RED when upstream resolves
   `sh` — invert it then and record the fixing version.

   **And the methodological lesson, which is the transferable one:** a gate that
   fires ALWAYS is indistinguishable from a gate that works. W1's planned red
   pole — "an open obligation blocks the ship" — would have passed here for
   entirely the wrong reason. Only the negative control (no obligation, must NOT
   block) separates them. That is why the negative control is required rather
   than nice.
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
| **`sh` in real dispatch env** | **MEASURED — and it is a DEFECT** | `test_gsd_x_sh_dispatch.js` 4/4 with both controls: bare `sh` is unresolvable (exit 127), so the gate returns `block:true` on every run. **Do not enable the capability on this host.** The live ship drill is now blocked *behind* this, not merely unattempted |
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

**Not the live ship drill.** That was the next action when this file was first
written; the `sh` measurement recorded in rule 9 landed afterwards and moved the
blocker underneath it. A drill run today would halt at the gate for exit 127 and
prove nothing about obligations — and, worse, would LOOK like the red pole
passing.

Take the resolution contract first. In rough order of leverage:

1. **Decide the owner's fix for `sh`.** The bare-`sh` assumption is upstream
   (`check-command-router.cjs:1100`), so the options are: get upstream to resolve
   a shell the way it already resolves other binaries; or express our gate in a
   kind that needs no shell (`artifact-frontmatter-equals` is the only other
   built-in, and it cannot run our python, so this likely means asking upstream
   for a shell-free executable kind). **No environment magic** — prepending Git's
   `bin` to PATH in a wrapper would make our gate pass while leaving every other
   capability's `command-exit-zero` gate broken on every Windows host, and would
   hide the defect rather than fix it.
2. **Declare the runtime requirement in the manifest**, which is ours today and
   is honest regardless of how (1) resolves, alongside the E11 absolute paths in
   the predicate.
3. **Then** the live ship drill, in a disposable scratch project, with the
   negative control that rule 9 explains is load-bearing.

Standing operational note: if the host is under `host-memory-floor.js`'s CRITICAL
floor (1024 MB), expect protected writes to be denied for liveness rather than
for content — rule 7, not a new problem. Run the reaper first and re-read its
log: `GHOST_CLEAN` means the population is empty at that instant, but it
regenerates from our own timed-out hook spawns, so a denial a few minutes later
usually has something to take.
