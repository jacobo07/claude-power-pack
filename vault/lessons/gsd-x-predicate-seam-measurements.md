# The predicate seam, measured — W1 (GSDX-M05)

**2026-09-22**, branch `feature/knowledge-acquisition`, HEAD `7dfc5c3`.
A new file rather than an edit to a canonical one: `ukdl-universal.md` has had a
live concurrent writer at both previous promotion attempts
(`vault/specs/gsd-x-n4.RESUMPTION.md:84`), and this tree carries ~440 dirty
paths from another pane. The merge is deferred; this is the pointer.

## What was already believed, and what the measurement changed

`572629f` moved the gate from GSD's prose `kind:"gate"` envelope to
`check.predicate` + `command-exit-zero`, on the reading that the predicate form
is "the enforced, blocking, machine-checked path". That reading is correct about
the **evaluator** and incomplete about the **dispatch**.

## M1 — `execute:wave:post` is the one hook point that cannot dispatch a predicate

Every other documented point exhibits the predicate form:

| hook point | predicate form | supplies `--phase-dir` |
|---|---|---|
| `plan:pre` — `workflows/plan-phase.md:1428` | yes | yes |
| `execute:post` — `workflows/execute-phase.md:1161` | yes | **no — `--phase-number` only** |
| `verify:pre` — `workflows/verify-work.md:91` | yes | yes |
| `ship:pre` — `workflows/ship.md:168` | yes | yes (+ phase-number) |
| **`execute:wave:post`** — `workflows/execute-phase/steps/wave-post-gate-hooks.md:11` | **no** | no |

`wave-post-gate-hooks.md:11` is the only dispatch line and it reads
`hook.check.query`. Line 7 of the same file states that a predicate gate "uses
the check CLI's `predicate` form with the predicate JSON and phase number
(**shown in the block below**)" — and the block below contains no predicate
form. The capability is documented as dispatchable at a point whose only
exhibited dispatch cannot dispatch it.

This matters because `check.query` is **not available to a third party**: the
query subcommands are a fixed built-in list (`bin/lib/check-command-router.cjs:1669`),
and `bin/lib/gate-predicate-evaluator.cjs:8-10` records that before #2008
"nothing EVALUATED a declared predicate for non-built-in capabilities —
`check.query` was the only enforced shape". Predicate is the third-party
mechanism, and `execute:wave:post` never received #2008's treatment.

Upstream-owned (`@opengsd/gsd-core`). Not a power-pack defect.

## M2 — `sh` does not resolve in a plainly-spawned child

Driving the real CLI with the argv shape `ship.md:168` documents, with no
`--phase-dir`:

    EXIT=0
    {"block": true,
     "message": "command exited 127: sh: not found",
     "details": {"kind": "command-exit-zero", "exitCode": 127, "signal": null}}

`gate-predicate-evaluator.cjs` runs the command through `execTool('sh', ...)`,
which resolves `sh` on PATH rather than through a shell. `sh.exe` exists at
`C:\Program Files\Git\bin\sh.exe` and `C:\Program Files\Git\usr\bin\sh.exe`;
neither directory is on the PATH of the process measured here.

**Scope of this claim, stated exactly.** The subject was a node process spawned
from PowerShell. GSD's real dispatch executes its preamble *in* `sh` (the bash
block at `wave-post-gate-hooks.md:10`), so a child spawned from there would
likely inherit a PATH containing Git's bin. This measurement therefore proves
the failure mode is **reachable and names its exact observable**; it is not yet
evidence about the environment of a real GSD wave. Measuring PATH in the wrong
process is not evidence about the right one — the same limit `572629f` recorded.

## M3 — a phase dir outside the project root is refused, at the wrong altitude

    --phase-dir <abs path outside any project>
    EXIT=1   Error: path escapes its allowed directory: <path>

This is an **instrument error**, not a gate verdict: exit 1 with empty stdout,
no `{block, message}`. Per `wave-post-gate-hooks.md:17-19` a non-zero exit with
unparseable output is a *command failure*, which under our manifest's
`onError: "halt"` halts the wave — correct behaviour, but the message an
operator sees would describe a containment violation rather than an obligation.

A scratch project for a drill must therefore live inside a real project root,
with the phase dir beneath it. Nothing in the plan or the audit named this.

## M4 — an absent `--phase-dir` is not containment-checked at all

Case M2 above supplied no `--phase-dir`. There was no containment refusal: the
command executed with `"${PHASE_DIR}"` interpolated to the empty string, exactly
as `gate-predicate-evaluator.cjs:43-53` (`ctx.phaseDir ?? ''`) specifies. The
containment check guards a supplied path; it says nothing about an absent one.

On a host where `sh` resolves, this path reaches our own tool as
`check "" --exit-code`, which fails closed at exit 2 by the fix in `572629f` —
so the gate would block **every** wave, for a reason unrelated to obligations.

## Consequence for the four-pole drill

Pole A (open obligation → halt) would have "passed" for the wrong reason: the
wave halts either way, and the halt names a command error rather than DO-1/DO-2.
Pole B (satisfied → wave passes) is the pole that exposes it, because the
command error is obligation-independent. Attribution must therefore be taken at
the registration layer — `gsd_run loop render-hooks execute:wave:post --raw`
across the enable/disable transition — with the wave outcome kept only as a
corroborant.

Baseline captured this session, with the capability installed at global scope
and `enabled` false: three active hooks (`drift` ×2, `ui`), ours **absent**.

## Registry state, measured by the registry's own reader

`gsd-tools capability list --raw` → **47 total**: 46 `first-party`, 1 `global`
= `cpp-gsd-x-mission` `1.0.0`, `status: active`, `surfaced: true`, sourced from
the power-pack path. `7dfc5c3`'s "46 → 47" is corroborated.

Two path probes (`~/.claude/.gsd-capabilities.json`, `~/.claude/.gsd/capabilities`)
reported absence and were simply the wrong instrument; the ledger is not at
either path. A registry is authoritative about its own contents — ask it.

## Correction to the plan this produced

`~/.claude/gsd-local-patches/` is **not** an overlay or patch seam. It is a
dated pre-migration backup (13/05/2026, `backup-meta.json`, the old
`get-shit-done/` tree). Landing an upstream fix there would land it nowhere.
The mechanism was inferred from a directory name by two independent readers.

## M5 — the activation key was validator-clean and could never be true

`activationKey: "enabled"` with `config: { "enabled": {...} }` passes
`capability-validator.cjs:717`, which only checks that `config` carries an own
property of that name. But `capability-validator.cjs:700` documents the field as
"the **dotted** config key that gates this capability", and
`capability-activation.cjs:71-107` resolves it through a four-level walk —
loaded config, workstream `config.json`, root `config.json`, registry schema
default — returning `false` when none is found.

A bare `enabled` is found at none of them. Measured: `capability set` reported
`"capability is surfaced but every hook is gated off"`, and the hook stayed
`configured:false active:false` whichever way the capability-level flag was
turned, because that flag is a different thing from the config key the hook's
`when` names.

Every first-party capability is namespaced — `intel.enabled` with a config key
literally named `"intel.enabled"` (`capability-registry.cjs:2028-2035`), and
likewise `graphify.enabled`, `refactor.trigger_enabled`, `workflow.live_dom_uat`.
Ours was also un-namespaced in a host-global config space, so any project with a
top-level `enabled` would have flipped it.

Now `gsd_x_mission.enabled` in all three places (config key, activationKey,
gate `when`). This is the fourth member of one family in this capability's short
life: **installed, surfaced, validator-clean, and unable to fire.** Validation
proves shape; only activation proves reach.

## M6 — activation is project-scoped, which contains the blast radius

The install is global (`scope: global`, `runtimeConfigDir: C:\Users\User\.claude`),
and the audit's first gap was that enabling a `blocking:true` / `onError:halt`
gate there exposes the four other GSD projects on this host. Measured, that is
not what happens: `when` resolves from the **project's** config, so the same
installed capability renders differently per project.

    ship:pre, scratch project (gsd_x_mission.enabled true)
      activeHooks = [cpp-gsd-x-mission, security]   ours present, blocking, onError halt
    ship:pre, claude-power-pack (not set)
      activeHooks = [security]                      ours absent

Global install, per-project activation, default false. The exposure the gap
described requires someone to set the key in that project's own config.

This pair is also the attribution instrument the audit asked for. A wave or ship
that completes is returned identically by "gate passed", "gate disabled", "never
registered" and "manifest rejected"; `loop render-hooks <point>` across the
transition distinguishes them, and the outcome is kept only as a corroborant.

## What is still not proven

No `/gsd:ship` run has dispatched this gate. The ship workflow is driven by an
agent reading workflow markdown, so it cannot be invoked from a tool call —
everything above is the real capability registry, the real activation resolver
and the real `check predicate` CLI, which is one seam short of the real
lifecycle. The `sh` question is likewise answered for a PowerShell-spawned child
and not for GSD's own dispatch, which runs its preamble in `sh`.
