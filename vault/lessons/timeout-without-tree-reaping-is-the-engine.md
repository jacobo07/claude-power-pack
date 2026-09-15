# A Timeout That Kills One Process Is Not Containment

**Sealed 2026-09-15** (Claude Power Pack, hook runtime). Origin: an investigation
into "Claude Code sits on *running PreToolUse hooks, 3 of 4 complete* for minutes".

## The finding, and why it inverts the obvious diagnosis

The brief assumed an **unbounded wait**. The measurement found the opposite: the
bound fires constantly, and firing is what causes the damage.

```
node/python processes alive                65
  orphaned (parent gone)                   49      holding 271 MB
  oldest orphan                            4 days
host free memory                           518 MB of 32,061 MB   (1.6 %)
hook-dispatcher timeout events (live log)  15,574  (28,508 lines)
```

`spawnSync`'s `timeout` kills the **direct child only**. Every one of those
15,574 timeouts was an opportunity to strand a descendant, and strandings
accumulate into RAM starvation, which makes the *next* hook breach its budget,
which strands another descendant.

> **Unreaped, a per-step timeout is not the protection. It is the engine.**

This is a positive-feedback loop that presents as "everything got slow", so it
is diagnosed as load, latency, or a hung hook — never as the timeout itself.

## Post-hoc tree-kill is not available, and this is worth knowing before designing

The natural fix — "on timeout, kill the process tree" — does not work from the
parent's side once `spawnSync` has returned:

```
taskkill /T /F /PID <childPid>   ->  ERROR: process "41224" not found
```

By the time the call returns, the child is already dead, so there is no live PID
to walk a tree from. Containment must therefore be established **at spawn time**
(a Job Object, which pure Node cannot create) or achieved **afterwards by
reaping**. There is no third option, and reaching for `taskkill` after the fact
wastes a cycle discovering this.

What makes reaping viable: **Windows does not reparent orphans.** A dead parent's
PID stays in the child's `ParentProcessId`, so `parent is gone` remains a
decidable property indefinitely. That is the whole basis of the repair.

## The reason it survived: the detector was blind by construction

An orphan reaper already existed and had run for months. Its load-bearing clause:

```powershell
if ($CpuTicks -ne 0) { return $false }   # "never resumed" => nothing to lose
```

and its own self-test enshrined the refusal — *"healthy long task: has burned
CPU → want = $false"*. Correct for its original subject. **Structurally incapable
of seeing this class**, because a hook that ran, breached its timeout and was
orphaned has burned CPU by definition. It is precisely the population the rule
promises to spare.

Two further blind instruments in the same estate, both of which read green while
the failure was happening:

- the hook-budget gate folded `host_starved` into its **pass total**, so the one
  instrument that could see starvation reported success exactly when starved;
- the security gate's suite asserted `fail-open was lost — doctrine requires it`
  and **passed**, so the suite was pinning the defect it was written to guard.

> **A predicate can be correct and still be the wrong question. Before debugging
> a detector that missed something, ask what its clauses make it unable to see.**

This was the **third** time this one file lost a class to its own enumerator
(after an Electron husk and a never-resumed child). The recurrence is the signal:
when a file has lost a class twice, the enumerator is the defect, not the
predicate — and the fix is to enumerate the real population once, structurally,
rather than to add another clause.

## Adding a rule beats loosening one

The repair did **not** relax `CpuTicks -eq 0`. It added a second rule with its
own, different safety argument:

| rule | why it is safe to kill |
|---|---|
| never-resumed | burned no CPU, so it holds no state and has nothing to lose |
| **abandoned-hook** | **a hook's whole output contract is stdout read by its parent; with the parent gone it is not working, it is writing to a closed pipe** |

The second argument is *stronger*, because it does not care whether the process
did work — the work is undeliverable either way.

Relaxing the first rule would have made it eat healthy long-running tasks, which
is worse than the leak. So: **when a guard cannot see a class, add a rule with an
independent justification; do not widen the clause that is protecting something
else.** Then assert they stay **disjoint**, so a later change that makes the old
rule claim the new class fails in the suite rather than in an incident.

## Derive bounds from declared contracts, never from feel

The age floor is 300 s because the longest declared `timeoutMs` is 70 s and the
longest harness budget is 120 s — so a process past 300 s has outlived every
bound it could have been running under. Written down that way, the floor moves
automatically when a budget does. A number chosen for feel cannot.

And exclude deliberate survivors (daemons, watchers, pane restorers) **by name**,
not by heuristic. A heuristic that spares them also spares the thing you are
hunting.

## Honesty clauses that this repair needed

- **Count the kill, not the decision.** A `Stop-Process` that threw is a process
  still running; a count built from intent reports it as reaped.
- **Count per rule, never a total.** A total cannot distinguish *the new rule
  works* from *the old rule does all of it and the new one is dead*.
- **Do not claim the memory.** Free RAM moved 518 → 1186 → 434 MB during the work
  under a live concurrent pane. The attributable metric was the orphan count
  (49 → 11); host memory was dominated by other activity and claiming it would
  have been a fabricated win.
- **State the residual.** The oldest orphan survived: its command line is
  relative (`tools/audit_cache.py`), so nothing can attribute it to `.claude` at
  all. Identifying it needs cwd, which `Win32_Process` does not offer cheaply.

## Fail-closed couples to this repair

The same starvation made a security gate fail open **256 times**, and twice
during the session that fixed it. Its own header recorded the decisive pair:
same payload, 8218 ms at 844 MB free → **allowed**; 929 ms uncontended →
**denied**. Host load was deciding whether a credential could land.

Turning it fail-closed immediately produced a **false denial of a clean write**
on the first suite run. The fuller measurement matters, because the first number
was wrong in a way worth recording:

| observation | result | host |
|---|---|---|
| first run after the change | R2 denied (false) | starved |
| three reruns | 3/3 clean | 301 MB free |
| during heavy concurrent load | **1/3** — R1 and R2 both failed | acute spike |
| six consecutive runs | 6/6/6 clean | 239 MB free |

`ea18929` recorded this as "roughly one run in four". **That framing is not
supported** — a rate implies a steady process. What the data shows is a **bursty
failure correlated with contention spikes**, clean otherwise, and *lower* free
memory (239 MB) produced a clean sweep while a busier moment at higher free
memory did not. So free RAM is the wrong predictor; instantaneous CPU/IO
contention is the real one, and a mean would hide exactly the behaviour that
matters.

> **A failure that arrives in bursts must not be reported as a rate.** The
> average is calm precisely when the user is not.

That is the accepted cost and it is why the two changes are coupled:
**fail-closed is only comfortable once orphan accumulation is bounded.** Ship
them together or the refusals look random. If the bursts prove disruptive, one
bounded re-run in a fresh child closes most of them at no cost to the security
property, because the detector is read-only and idempotent — deliberately not
done here, since the Owner chose plain deny over retry.

## DON'T

- **Don't read a bounded lane as a safe lane.** Bounded means the *parent* is
  bounded. Ask what the bound does to descendants.
- **Don't add a timeout as the repair for a stall** until you know whether an
  existing timeout is causing it. Raising a bound moves the cliff.
- **Don't trust a synthetic process-tree rig.** Three were built here and all
  three failed — an absent heartbeat indistinguishable from a child that never
  started, a control whose child raced its own spawn, and a third where neither
  arm produced its proof line. The live process table answered in one query with
  better fidelity, because it is the actual population. Pivot to production
  reality rather than debugging the rig a third time.
- **Don't leave a runtime authority unversioned.** The reaper, the dispatcher and
  the security suite all lived only in `~/.claude`, which is not a git repo — so
  the estate's orphan-reaping authority had no rollback path and no mirror pair.
  A live-loaded script also has no parse gate: a `$var:` scope-qualifier typo
  left the reaper broken for several minutes and only a follow-up run caught it.

## Related

- `vault/lessons/hook-fanout-systemic-cost.md` — the scheduling half
- `~/.claude/rules/guard-event-reachability.md` — a guard that cannot be reached
- `~/.claude/rules/instrument-before-claim.md` — could this instrument return the
  other answer?
