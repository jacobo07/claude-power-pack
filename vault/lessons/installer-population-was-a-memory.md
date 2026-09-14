# The installer's population was a memory, and it had been empty for four months

**2026-09-14.** Strengthens `PR-COVERAGE-BY-CONSTRUCTION-001`. Does not add a
rule: the principle already covered this exactly, and that is the finding.

## What happened

`tools/install_global_core.py` installed **zero agents and zero commands onto a
clean machine and returned 0 with a clean report.**

The shipping loop read `inv[kind]["items"]`. No inventory file in
`tools/_inventory/` has ever had an `items` key — they carry `pp_original`,
`plugins`, `user_personal`. The loop body never executed once. Every counter
therefore read zero, **including the `skipped-not-pp` branch that existed to
make rejections visible**, so nothing in the output distinguished "considered
everything and shipped nothing" from "never looked".

Underneath it, a second and independent defect: the source resolver was
`repo/<kind>/<name>` — one directory for a domain fed by three. Of the eight
agents the inventory names, seven do not resolve there. Repairing only the
schema would have shipped one agent and reported success.

## Why nothing caught it

`tools/e2e_clean_install.py` asserts `agents >= 1` after a real apply. It was
red. It had been red since the inventory was generated on 2026-05-19, and it
said:

> `Path.home() ignored USERPROFILE redirect on this host. Sandbox stayed empty
> after apply.` → *PATH-A NOT VIABLE, plan permits Path B fallback.*

Both clauses were false. Run with `--keep-sandbox`, the sandbox held
`settings.json`, `SESSION_SAFETY_CONTRACT.md` and two install sidecars. The
redirect worked perfectly and the tree was never empty.

**The gate had one question and a hardcoded answer for "no".** An empty agent
count is produced by two different worlds — a redirect that failed and an
installer that ships nothing — and it pre-assigned the blame to the host, which
is the one of the two that nobody in this repo can fix. Four months of a red
gate reading as an environment limitation.

Its own phase 3 contradicted it three lines below the accusation:
`unchanged=1`. A host that ignored the redirect cannot produce an *unchanged*
on re-apply into that sandbox. **When a verdict contradicts the evidence
printed beside it, the parser is wrong, not the world.**

And phase 1 passed on `agents == 0 and commands == 0`. A dry run that wrote
nothing and an installer that ships nothing are the same zero: **that check was
satisfied by the defect it existed to exclude.**

## The class, third occurrence

| # | Consumer | Population declared by |
|---|---|---|
| 1 | Liveness Ledger | eight hand-declared components |
| 2 | `modules/mirror_discovery` | a hand-declared domain **root** (`ed9546f`) |
| 3 | `install_global_core` | a hand-curated inventory, generated once |

The rule was written after (1). It reads: *an audit whose subjects are enrolled
by hand measures memory, not reality.* It covers (2) and (3) word for word.

It did not prevent them because **its enforcement was pinned to the incident
that birthed it.** `modules/liveness/reachability.py` gates the liveness
ledger and nothing asked the same question of any other consumer. A rule
enforced at one site is prose everywhere else, and prose does not travel to the
moment someone types a population.

The generalisation worth keeping is about the *shape of the universe*, not the
list: **a dynamic enumeration inside a statically-bounded universe is still a
static enumeration.** Fixing the file level left the root level; fixing the
root level left the manifest. Each repair looked complete because the layer it
fixed became honest.

## What was done

Population is now **discovered** via `modules.mirror_discovery`, which already
owns "which repo directories feed this live domain". The inventory keeps the
job it is genuinely the authority for — `user_personal` and `plugins.*` are
*declarations of ownership*, which cannot be discovered by scanning a
directory. Coverage completeness without absorbing a foreign estate.

Measured on a sandboxed clean machine: **0 → 27 agents, 0 → 75 commands.**

## Traps worth carrying

- **A counter shared between two producers cannot attribute either.** The first
  enumeration signal summed `installed/updated/unchanged/missing-source/error/
  skipped-not-pp` and returned 1 against a loop that ran zero times, because
  the session-safety deploy increments the same counters. Replaced by
  `shippable-considered`, written by the shipping loop and nowhere else. **Have
  the producer report its own aperture; do not infer it from shared totals.**
- **"Could not ask" must not be spelled like "nothing exists".** An unreachable
  discovery now returns `None`, never `{}`. An empty population installs
  nothing and exits clean — the original outage wearing a different cause.
- **A guard whose subjects are all out of reach reports the same green as one
  that works.** Every name PP excludes for sovereignty (the operator's
  specialist, the `gsd-` family) is live-only, so discovery never offers one and
  the exclusion has never fired in production. Its drill is therefore
  **synthetic**, and keeps working on the day that stops being true.
- **Fix the misattributing gate BEFORE the defect it misattributes.** Repair the
  installer first and the false message never prints again — there would be
  nothing left to show the gate had been lying. Landed as two commits in that
  order deliberately.

## Evidence

`f95e118` (gate attribution + before/after evidence pair), `b88448f` (population
+ `tools/test_install_population.py`, 7/7 with every red branch driven),
`ebaa0b1` (five advisor lenses captured; PP live-only 14 → 9), `d2d2a34`
(duplicate authority retired, 1 → 0).

Before/after verdicts preserved verbatim in
`vault/audits/clean_install_2026-09-14T14-59-17Z.json` and
`...T15-13-45Z.json`.

## Still open

`V-MIRROR-BUDGET` is a wall-clock threshold on a tree with a live concurrent
writer; measured in `ed9546f` as ambient-dominated, observed both red (28.08s)
and green in this session's runs. Not tuned. The structural repair is to
bracket the run on tree state and report INCONCLUSIVE when the tree moved.

Ten commands are still named `pp_original` with no source in any root. They are
reported as `claimed-without-source` by every install; capturing them is the
same work the five advisor lenses just received.
