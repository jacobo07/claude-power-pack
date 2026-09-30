# Upstream report draft — `@opengsd/gsd-core` 1.14.0

**Status: FILED 2026-09-30 on the Owner's go.** Re-verified first against the `v1.15.0`
tag sources (released 2026-09-26, so the "1.14.0 is latest" premise below had expired):
all three defects unchanged. Split by the project's own SECURITY.md:
D1+D2 -> public issue https://github.com/open-gsd/gsd-core/issues/5133 ;
D4 (re-consent bypass, in SECURITY.md scope) -> private advisory GHSA-27c7-mm4w-qwgp
(state `triage`). The body below is the original draft, kept as written.

**Subject version.** `~/.claude/gsd-core/VERSION` = `1.14.0`. N6 read the npm registry
directly (not through `npm`, which is broken on this host — `npm view` dies with
`Class extends value undefined is not a constructor or null`) and found `latest` =
`1.14.0`. The installed tree is current, so these three defects are live in the newest
published version. This is not a stale install.

**Scope.** Three defects, one root theme: **evidence that distinguishes an instrument
failure from a domain verdict is produced, then discarded before the decider sees it.**
D1 and D2 are two halves of one path. D4 is the same category error applied to trust
disclosure. Nothing in our estate patches the vendor tree; every line below is a report,
not a change we made.

---

## D1 — `runBoundedShell` drops the spawn error its own producer preserved

**Where.** `bin/lib/check-command-router.cjs:1099-1108`

```js
runBoundedShell(opts) {
    const r = execTool('sh', ['-c', opts.command], { cwd: opts.cwd, timeout: opts.timeoutMs });
    return {
        exitCode: r.exitCode,
        stdout: r.stdout,
        stderr: r.stderr,
        signal: r.signal,
        timedOut: r.timedOut,
    };
},
```

**The evidence exists one layer down.** `bin/lib/shell-command-projection.cjs:588-593`:

```js
function _spawnResult(result, program) {
    if (result.error && result.error.code === 'ENOENT') {
        return { exitCode: 127, stdout: '', stderr: `${program}: not found`, signal: null, error: result.error, timedOut: false };
    }
    const signal = result.signal ?? null;
    const error = result.error ?? null;
```

`_spawnResult` deliberately carries `error` — including the ENOENT case it special-cases.
`runBoundedShell` forwards five fields and `error` is not among them, so the field is
dropped at the boundary between the producer that computed it and the consumer that needs it.

**Failure mode.** On any host where `sh` is not resolvable on `PATH`, every
`command-exit-zero` predicate returns exit 127 with no surviving indication that the
shell was never found. The caller cannot distinguish "your command ran and refused" from
"there was no shell to run it in".

**Minimal fix.** Forward `error` (and, if a narrower change is preferred, a derived
`spawnFailed: Boolean(r.error)`), leaving the existing five fields untouched.

---

## D2 — `evaluateCommandExitZero` has three outcomes and needs a fourth

**Where.** `bin/lib/gate-predicate-evaluator.cjs:78-102`

The function branches exactly three ways: `res.timedOut` → block; `res.exitCode === 0` →
pass; everything else → block. The comment at line 94 states the collapse plainly:

```js
// Non-zero (incl. null exit from a signal kill) => block. Surface code + stderr/stdout tail.
```

**Failure mode.** A gate that could not run and a gate that ran and refused return an
identical verdict object (`block: true`, `details.kind: 'command-exit-zero'`). There is no
route to `onError`. Consequences, in order of severity:

1. **A misconfigured or unavailable toolchain reads as a domain refusal.** An operator is
   sent to fix their code when the actual fault is a missing interpreter.
2. **A red-pole drill cannot be trusted.** A test asserting "the gate blocks when the
   condition is violated" passes identically on a host where the gate never executed. The
   failing branch and the never-ran branch are indistinguishable to the assertion, so the
   drill reports green coverage it does not have.
3. The blocking direction is fail-closed, which is correct and is why this is a
   correctness-of-diagnosis defect rather than a safety hole.

**Minimal fix.** With D1 applied, add a branch before the non-zero fallthrough: when the
result carries a spawn error, return a distinct outcome routed through the existing
`onError` path rather than as `block`. The three current branches keep their behaviour
exactly; only the previously-unreachable fourth world gains a name.

**Note on ordering.** D2 cannot be fixed without D1. The evidence D2 needs is precisely
the field D1 drops.

---

## D3 (context, not a request) — a third-party predicate kind is not registrable

`KIND_TABLE` (`gate-predicate-evaluator.cjs:148`) is module-private with no registration
API, and `EVALUATOR_KINDS` is exported frozen. We verified this while looking for a way to
work around D2 in our own capability rather than reporting it. There is no such way, which
is why this is a report. We are not asking for a plugin API; we record the check so a
maintainer knows the workaround space was searched before filing.

---

## D4 — `hasExecutable` omits gates, so a shell-reaching capability is disclosed as declarative

**Where.** `bin/lib/capability-trust.cjs:628-636`

```js
const hooks = safeCollect(() => collectHookSurfaces(manifest, stagedDir, missingArtifacts), []);
const commandModules = safeCollect(() => collectCommandSurfaces(manifest, stagedDir, missingArtifacts), []);
const mcpServers = safeCollect(() => collectMcpSurfaces(manifest), []);
const reviewerLanes = safeCollect(() => collectReviewerLaneSurfaces(manifest, resolveHost), []);
const instructionSurfaces = safeCollect(() => collectInstructionSurfaces(manifest), []);
// ADR-2363 D3: instruction surfaces are deliberately ABSENT from this expression. Adding them
// would silently change `executableSetChanged` and the auto-update re-consent trigger.
const hasExecutable = hooks.length > 0 || commandModules.length > 0 || mcpServers.length > 0 || reviewerLanes.length > 0;
```

`gates` is not a collected class. The file contains no occurrence of `gates` or
`command-exit-zero`.

**Failure mode, measured.** A manifest whose only surface is a `gates[].check.predicate` of
kind `command-exit-zero` — which `gate-predicate-evaluator.cjs` executes via
`execTool('sh', ['-c', ...])` — reaches `capability-trust.cjs:1176` with
`hasExecutable === false` and, with no instruction surfaces, prints at line 1181:

> `This capability ships no executable surfaces (declarative only).`

Our own `cpp-gsd-x-mission` manifest printed exactly that on `capability update`
(2026-09-22). It runs a shell command.

**Why this is more than wording.** The comment at lines 633-634 states that the same
`hasExecutable` drives `executableSetChanged` and the auto-update re-consent trigger.
Because a gate is not counted, **the command string a gate executes can be changed by an
update without re-consent being requested.** A user consented to a capability described to
them as declarative; the thing that changed underneath them is a shell command line.

**On the ADR-2363 objection.** The comment records a deliberate decision to keep
*instruction* surfaces out of this expression, precisely to avoid perturbing
`executableSetChanged`. That reasoning does not transfer to gates, and the distinction is
the point of the ADR rather than an exception to it:

- An instruction surface changes what the agent is *told*. ADR-2363 D3 judged that it
  should be disclosed (line 1186 does disclose it) without forcing re-consent.
- A gate predicate changes what the machine *executes*. Re-triggering consent when it
  changes is the behaviour a user would expect, and it is the same treatment `hooks`,
  `commandModules`, `mcpServers` and `reviewerLanes` already receive.

So we are not proposing to weaken ADR-2363 D3. We are proposing that gates belong on the
executable side of the line the ADR drew, and that the current omission places them on the
instruction side without anyone having decided that.

**Minimal fix.** Add a `collectGateSurfaces(manifest)` alongside the existing collectors,
include it in `hasExecutable`, and surface it in the disclosure list. Line 1177's
conditional for "declarative only" then becomes correct without further change.

**Compatibility note a maintainer will want.** This will flip `executableSetChanged` to
true on the next update for every already-installed capability that declares a gate, so
those users will be asked to re-consent once. That is the correct outcome — they were never
asked the first time — but it is a visible one-time behaviour change and should ship with a
release note rather than silently.

---

## How each claim above was established

| claim | instrument | result |
|---|---|---|
| installed version | `~/.claude/gsd-core/VERSION` | `1.14.0` |
| `latest` = installed | direct HTTPS registry read (N6); `npm` is broken on this host | `1.14.0` |
| D1 field drop | read both sites, `check-command-router.cjs:1099-1108` vs `shell-command-projection.cjs:588-593` | confirmed |
| D2 three branches | read `gate-predicate-evaluator.cjs:78-102` | confirmed, incl. line 94's own comment |
| D4 omission | read `capability-trust.cjs:628-636`; grep for `gates` / `command-exit-zero` in that file | zero occurrences |
| D4 live effect | `tools/test_gsd_x_consent_integrity.js`, with a positive control proving the function can return `true` | `hasExecutable=false` on our real manifest |
| D3 no registration API | read `KIND_TABLE` at `gate-predicate-evaluator.cjs:148`; `EVALUATOR_KINDS` exported frozen | refuted as a workaround |

**Not established.** We have not run the proposed fixes against the upstream test suite, and
we have not measured how many published capabilities declare a gate — so the size of the
one-time re-consent wave in D4 is unknown to us. Both belong to a maintainer.

**Local posture.** Zero vendor `.cjs` has been modified in this estate. D4 is pinned locally
by `tools/test_gsd_x_consent_integrity.js` as a *characterization* — it asserts today's
defective behaviour on purpose, with a positive control, and goes red with an explanatory
message if upstream fixes it. It is to be inverted deliberately at that point, not deleted.
