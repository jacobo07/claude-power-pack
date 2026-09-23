# GSD X — resumption contract, wave N6 (in flight)

**Opened 2026-09-23.** Self-contained: a fresh worker continues from this file with
no prior conversation. `gsd-x-n5.RESUMPTION.md` is **not superseded** — everything
in its "must NOT be re-litigated" list still binds. This file records what N6
measured on top of it.

## Identity

- Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch
  `feature/knowledge-acquisition`, worktree = **repo root**.
- **Do not move to `.claude/worktrees/gsd-x`.** That worktree is branch `gsd-x` at
  `a3411c9` and does **not** contain the N5 commits. Moving there abandons the
  mission's history.
- N6 opened at HEAD `7bc075b`; first N6 commit is `cb9b2c8`, whose parent was
  `c8a5d03` — HEAD moved **twice** under N6 from another pane mid-slice.

## Correct the handoff before trusting it (again)

The N5→N6 handoff reported HEAD `66f4088` and the session snapshot reported a
clean tree. Measured at N6 start:

| reported | measured |
|---|---|
| HEAD `66f4088` | `7bc075b` — **32 commits later** |
| working tree clean (session snapshot) | **490 dirty paths** (42 modified, 448 untracked) |
| — | all 32 commits foreign: another pane's UCR-CIF / Torre Universal mission |

N5 recorded this exact trap and it recurred verbatim one wave later. **Prose in a
handoff does not stop the next reader trusting the snapshot.** The instrument that
would have: re-read HEAD immediately before every commit and refuse on a move —
which N6 did, and which caught `7bc075b → c8a5d03`.

## What N6 has SEALED

### `cb9b2c8` — the shell prerequisite became a check

- `capability.json` now carries structured `runtimeRequirements[]` (posix-shell,
  python-interpreter, mission-tool) with `onUnmet: refuse-activation`.
- `tools/gsd_x_runtime_preflight.js` probes each through the **same surface
  gsd-core dispatches the gate on**, not a PowerShell proxy.
- Live verdict on this host: **UNMET, naming `posix-shell`, exit 1.**
- Proof: `tools/test_gsd_x_runtime_preflight.js` **7/7**, both poles plus a
  positive control; two mutations driven, each landing on its own assertion;
  restore SHA-256 `099680E2…` verified.
- Regression unchanged: reachability 9/9 · gsd-x 15/15 · mission 17/17 ·
  facts 15/15 · consent 3/3 · sh dispatch 4/4.

### `dc5ff59` — the Fact Producer exists, and absence stopped meaning one thing

- `tools/gsd_x_fact_producer.py` produces facts from sources this estate already
  owns: `bounded_local_capacity` **OBSERVED** from `host-memory-floor.js`'s own
  readings, `unattended_operation` **DERIVED** from the long-run markers in
  `~/.claude/state`, scoped to the mission root.
- Live: capacity HOLDS (1312 MB free of 32061, WARN), unattended NOT-HELD. Both
  poles came from the world, not from a fixture.
- Document has **three** buckets — `facts[]`, `not_held[]`, `unknown[]` — because
  the consumer reads presence as "holds", so a single absence silently carried
  measured-false, could-not-measure and never-asked. **UNKNOWN is not false.**
- Freshness is dependency-driven, no clock: each fact records sha256+mtime+size of
  its sources. Unrelated file changes → FRESH. A source changing → STALE, named.
  A source that **vanished → UNKNOWN, not STALE**.
- Proof: **15/15**; three mutations driven (UNKNOWN→false reds all four UNKNOWN
  gates at 11/15; dropping mission scoping reds the cross-mission gate; reporting
  an unreadable source as STALE reds its own), restore SHA-256 `2C0EA317…`.

**Open, deliberately:** the document is `gsdx-facts/2` and `load()` accepts only
`gsdx-facts/1`, so it **refuses** the document today. That is fail-closed and
correct; an additive field the loader silently ignored would be fail-open. **No
FACTS.json is emitted into the repo until the loader learns v2** — writing one
into `vault/benchmarks/mission_spine` would flip `source_of()` from prose to
structured underneath the parity proof.

## What N6 MEASURED that changes the architecture

**The root cause is not `sh`.** Read the source, not the symptom:

1. `shell-command-projection.cjs:588-591` — `_spawnResult` **preserves** the spawn
   error (`error: result.error`, ENOENT → exit 127). The evidence exists.
2. `check-command-router.cjs:1099-1108` — `runBoundedShell` forwards only
   `{exitCode, stdout, stderr, signal, timedOut}` and **drops `error`**.
3. `gate-predicate-evaluator.cjs:80-102` — the decider therefore has **three**
   outcomes: timed out → block · exit 0 → pass · **everything else → block:true**.

> **A gate that could not run and a gate that judged and refused return the
> identical verdict.** The distinguishing evidence is produced one layer below the
> decider and discarded one layer above it. That is the universal defect, and it
> is not Windows-specific: it fires on any host where a declared command is
> unavailable.

**`resolveExecutableBinary` is NOT broken.** It appends PATHEXT correctly and
would find `sh.exe`. It returns null because no PATH segment holds a POSIX shell.
`sh.exe` exists twice and neither directory is on PATH. Presence ≠ resolution ≠
PATH membership.

**Trust disclosure (D4), confirmed still live.** `capability-trust.cjs:635`
computes `hasExecutable` from `hooks | commandModules | mcpServers | reviewerLanes`
— **gates are not a class**. So our command-spawning gate is disclosed at line 1181
as *"ships no executable surfaces (declarative only)"*. Not a wording bug: the
source of truth is missing a class.

## Upstream, decided in N6 — do not re-derive

- Package is **`@opengsd/gsd-core`**, installed `VERSION` **1.14.0**,
  `.gsd-runtime` = `claude`, **not a git repo**, no root `package.json`.
- **npm registry reports `latest` = 1.14.0 — identical to what is installed.** The
  tree is current, so **upstream has NOT fixed D1/D2/D4**; they are live in the
  newest published version. This is not a stale install.
- `backup-meta.json` says `from_version: 1.22.4`, which is **higher** than latest.
  It is **not a downgrade**: those paths say `get-shit-done/`, so it records a
  **package rename with a version-line reset** on 2026-09-14. Version numbers
  across that boundary are not comparable. (N6 nearly recorded "rollback" as a
  finding; it was wrong.)
- **`npm` itself is broken on this host** — `npm view` dies with *"Class extends
  value undefined is not a constructor or null"*. `check-latest-version.cjs` is
  built on `execNpm`, so **GSD's own `/gsd-update` version check cannot run here**.
  The registry answer above came from a direct HTTPS read, not from npm.
- **A third-party predicate kind is impossible.** `KIND_TABLE`
  (gate-predicate-evaluator.cjs:148) is module-private with no registration API;
  `EVALUATOR_KINDS` is exported frozen and read-only. That candidate is **refuted**,
  not deferred.
- **Estate precedent: zero vendor `.cjs` has ever been locally modified.** Every
  file in `gsd-local-patches` is markdown. A `.cjs` overlay would be silently
  replaced on update (backed up, not merged), and the installed tree carries **no
  pristine-hash manifest** to detect drift at rest.

**Conclusion carried forward:** do not mutate the vendor tree. Ship the half we
own (done in `cb9b2c8`), and route D1/D2/D4 upstream as a report. **Submitting
upstream is outward-facing and needs the Owner** — it is the one open decision.

## Next exact valid action

0. **Teach `structured_facts.load()` schema v2** — accept v1 unchanged (the parity
   proof builds v1 fixtures through `dump()`), require `state` + `depends_on` on a
   v2 document, and surface a non-empty `unknown[]` in the mission verdict so a
   closure receipt can never silently claim completeness. Only then emit a real
   FACTS.json. Until this lands the producer's output is correctly refused.
1. **Draft the upstream report** for D1/D2/D4 (do not send). One issue, three
   defects, each with file:line, the measured verdict, and the minimal fix:
   `runBoundedShell` forwards the spawn error; `evaluateCommandExitZero` gains a
   fourth outcome routed through `onError` rather than returned as `block`;
   `hasExecutable` derives from the complete surface including gates.
2. **W1 live ship** remains blocked behind D1/D2 and must stay blocked. A drill
   today halts at exit 127 and **looks like the red pole passing**. The
   runtime-failure control is what separates them and is now buildable: the
   preflight gives a verdict that is provably distinct from a domain block.
3. Then: trust disclosure (C), reachability baseline (D), Fact Producer (E),
   drift decision layer (F), frontier recompile.

## What must NOT be re-litigated without new evidence

All six items from N5, plus:

7. **The evaluator's missing fourth outcome is the root cause; `sh` is the
   symptom.** Fixing `sh` alone leaves every other capability's gate conflating
   instrument failure with domain failure.
8. **Do not prepend anything to PATH, hardcode a shell path, or wrap the gate.**
   Each makes our gate green and leaves the defect intact for every other
   capability on every Windows host.
9. **Upstream is current at 1.14.0.** Do not spend a wave looking for a newer
   version that fixes this; there isn't one. Re-check only via direct registry
   read — npm is broken here.
10. **`resolved === null` while the probe succeeds is unreachable on win32.** The
    resolver and `execTool` run the same PATH+PATHEXT search there; the divergence
    is a POSIX behaviour. Drive that rule through the injected surface, never by
    hunting a host fixture. (Two N6 test failures, both honest, cost this.)
