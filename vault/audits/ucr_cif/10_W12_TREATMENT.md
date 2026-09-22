# W12 — the frozen treatment, and the gate that was never the one being modelled

**Wave range:** `f2f359d..HEAD` on `ucr-cif/construction`. A range, never a count.

**Terminal state: `BLOCKED — RESOURCE / EXTERNAL`.**
The treatment remains **UNMEASURED**. It is not failed, not passed, not harmful, not
beneficial. `STRUCTURAL_RANKING_ENABLED = False`, `UCR_CIF_PROSE_RANK` unset,
`MAX_OWNERS` 5, `DISTINCTIVE_MAX_HOLDERS` 3, `MAX_DISTINCTIVE_REQUIRED` 3,
`create_spec`, the corpus, the 503 ABSTAIN and the 218 UNRESOLVED all untouched.
Production behaviour is byte-identical to what it was at `f2f359d`.

---

## 1. What the wave was sent to do, and what it did instead

W11 built the representation-neutral declaration channel and could not measure whether
using it repairs the routing harm W10 found. Its paired run was killed for host memory
pressure. The frontier's instruction was: *"Budget the host first; losing the run twice
is scheduling, not evidence."*

That instruction rests on a premise nobody had measured — that the run is expensive.
**It is not, and measuring it is the finding that outlives this wave.**

## 2. The mutation debt W11 owed is closed

W11 sealed on a plan last driven before its own projection and arm commits landed. That
is a claim about a tree that no longer exists. Driven at `f2f359d`:

| plan | W4 | W5 | W7 | W8 | W9 | W10 | W11 | total |
|---|---|---|---|---|---|---|---|---|
| mutations | 14 | 23 | 10 | 6 | 7 | 12 | 8 | **80** |
| verdict | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **ALL_CAUGHT** |

Every restore verified at source and at runtime; the tree returned to the three foreign
items after every plan.

**One anchor had rotted, for the ordinary reason.** W11 replaced the `if treatment:`
block W10's `W64` matched with the `_ARMS` identity table, so the probe reported
HARNESS-FAILED — correctly, and that report is the only reason the rot was visible.

The repair is the part worth carrying. The obvious literal translation — flipping
`os.environ.pop(k, None)` in the new `else` branch — reads as a faithful port and is
wrong: at twelve spaces of indentation that string is **also a substring of the
sixteen-space restore line in the `finally` block**, so the anchor matches twice and the
probe mutates the restore path rather than the selection path. A mutant editing code no
arm depends on, behind a diff that looks perfectly correct — which is exactly how W9's
`W36` survived. The anchor was instead placed where W11 moved the semantics: the `_ARMS`
table, with `ARM_CONTROL: ()` becoming the full treatment environment. Strictly stronger
than the original, because it now contaminates the control with the prose environment as
well as the rank one.

## 3. The footprint, and the diagnosis it falsifies

`tools/ucr_cif_footprint.py` sweeps session counts with **one child per point** — peak
RSS is monotonic inside a process, so an in-process sweep reports the largest point for
every point after it — and measures the child's own peak, which is a property of the
workload and immune to what the rest of the machine is doing.

| sessions | cases | peak | elapsed |
|---|---|---|---|
| 30 | 95 | 44 MB | 87.7 s |
| 60 | 143 | 47 MB | 183.3 s |
| 120 | 398 | 62 MB | 437.3 s |

`peak_mb = 36.5 + 0.2071 × sessions`, max |residual| **1.9 MB** over three points.
**Predicted peak at 573 sessions: 155 MB.** Confirmed live: the two arms sat at 127 MB
and 121 MB mid-sweep.

`environment_qualifier.capacity_probe` — the canonical owner, asked rather than
second-guessed — returned **ADMITTED**: 155 MB × 1 in flight + 1024 MB reserve = 1,179 MB
required against 4,267 MB available, clear of the ×1.5 margin.

So the W11 run was refused on a host-level free-memory percentage while its own
requirement was a seventh of a gigabyte. **The gauge that killed it is not a fact about
the subject.**

What *is* real is time: the 120-session point took 437 s, so 573 sessions is roughly half
an hour per arm rather than the ~12 min the handoff carried. The footprint sweep itself
overran a 600 s foreground budget, which is how that came to light.

## 4. Why the run died anyway, and why that is not §XLIII's experiment defect

Both arms were killed again. The harness stated the mechanism in its own notification:

> stopped because the system is running low on memory … **while the session was idle,
> which says nothing about the command or its own memory use.**

Measured at the moment of the kill:

| | |
|---|---|
| host free | **3,947 MB of 32,061 = 12.3 %** (W11 died at 12.8 %) |
| `claude` | 23 processes, 8,268 MB |
| `Cursor` | **55 processes, 8,342 MB** |
| mission-owned reapable residue | **none** — 3 python processes, 118 MB, all Power Pack hooks with live parents |
| partial artifacts | none, from either arm |

> **There are two admission authorities with different criteria, and the binding one is
> not the one this mission models.**

`capacity_probe` reasons about the **workload** and was correct — the run needed 155 MB
against 4 GB and would have completed. The harness reaper reasons about **host total
while the session is idle**, and reaps a 155 MB job at 4 GB free regardless of what it
costs. A run can be ADMITTED by the first and reaped by the second forever.

This matters because it retires an entire class of proposed remedy. Shrinking the
experiment cannot reach that gate: at the moment of the kill the job was already one
twenty-sixth of the free memory. Neither can retrying — the trigger is a host total that
this mission does not control and that the reaper samples *while idle*, which is
precisely when a long derivation is idle.

The §XLIII test is therefore answered, and answered in the direction that forbids calling
this a subject defect: the experiment does **not** reproducibly exhaust memory. Its
footprint is measured, bounded, linear and tiny. `BLOCKED — RESOURCE / EXTERNAL` is the
honest family, and the one thing the wave must not do is weaken the gate or evade it.
Detaching the run so the reaper cannot see it was available and was refused: that is the
resource-gate bypass the Contract of Reality names, and the harness explicitly instructed
that the work not be restarted unasked.

## 5. What was built, and why it is worth more than a retry

**The pre-registration is committed ahead of the numbers**
(`w12_preregistration.md`). The eight are pinned **by value** from the committed store —
`pre_cap` and `post_cap` `.by_owner["modules/governance-overlay"] = {"worsened": 8}`,
zero improved, zero unchanged, zero evicted — beside the population fingerprint, the
safety strata, and an operational reading of "recover" in which **an eviction
disqualifies**. A treatment whose `worsened` falls from 8 to 2 while evicting the owner
three times has not repaired anything; it has removed the harmed owner from the agent's
view, which is the substitution W10 already measured at constant slot count.

**The comparator refuses before it reports** (`tools/ucr_cif_w12_verdict.py`). Movement
is unreachable until comparability (`COMPARABLE`, licensed by `paired_verdict_allowed`,
`UNREADABLE` kept as its own class), execution (both arms diverge from their own control)
and baseline identity (the fresh W9 arm reproduces `worsened 8`) have all passed. On
refusal it prints no movement at all, so a reader cannot learn the answer and then decide
whether the run counted.

`tools/test_w12_verdict.py` **12/12** drives both poles — four refusals asserting on the
**absence** of the movement header, five recovery corners, and a licensing control so a
comparator that refused everything cannot pass the refusal assertions.
`ucr_cif_w12.json` **5/5 ALL_CAUGHT**. Family now **85**.

**`W69` earned its place by failing before it judged real data.** The mutation keys the
headline to the pre-cap half — where a ranking change is free, since W10 proved pre-cap
`evicted = admitted = 0` and every set-level effect is the cap's. It had nothing to fail
against: the gate asserted `"NOT_RECOVERED" in out`, which the post-cap line satisfies no
matter which half the headline names. The gate now parses the value off the headline
line. Writing the mutation beside the instrument found a hole in the instrument's own
gate; writing it after the result would have found a hole in nothing.

## 6. The projection was stale at the W11 seal

`--verify` reported `source_fresh False`. That is load-bearing here in a way the module's
docstring says it is not: staleness is safe *while ranking is off*, and the arms switch
ranking on.

The reasoning that followed was right in form and wrong in fact. The projection was built
at `09:41:35Z`, before W11's own final commits `390c3e6` and `f281762`; I concluded it was
the output of a superseded extractor, killed the running reference arm, and rebuilt. The
rebuild changed **four lines** — `build_ms`, `built_at`, `repo_fingerprint`, `files_seen`
1373→1376 — and **no evidence at all**: all 674 symbol-held and all 236 declaration-held
terms byte-identical. W11's late commits changed the extractor's code and not its output
on this estate. Correct precaution, no semantic gain, ~15 minutes of a reference arm.
Recorded that way rather than as a catch.

## 7. Two defects in the same family, found and deliberately NOT fixed

Both are hand-maintained enumerations inside the treatment, which is the shape this
mission exists to catch — a guard whose population is enumerated rather than discovered.

1. **`prose_authority.SELF_MEASUREMENT_PREFIXES`** lists `tools/test_w9_`, `_w10_`,
   `_w11_` by hand. This wave's own `tools/test_w12_verdict.py` falls outside it and is
   classified as an ordinary runtime consumer. Every future wave inherits the same gap.
2. **`prose_authority.RUNTIME_DIRS` and `CONTRACT_DIRS` both list `"skills"`**, but
   referrers are enumerated from `ownership_evidence.SCAN_DIRS`, which has no `skills`.
   Those branches cannot fire.

**Neither is fixed here.** Both live inside the treatment, and changing treatment
semantics before the first valid measurement is the one thing this wave may not do. They
are the first commit of the wave that measures.

Their effect today is **measured, not assumed**. Computed live at this HEAD with all
three new `tools/` files present: declared terms **814**, owners earning declarations
**26**, `governance-overlay` **256**, SELF_MEASUREMENT edges **9** — every figure
identical to W11's record. My instruments contributed zero edges, because none of them
resolves a path to a prose artifact. The defects are live and inert, and both halves of
that are worth stating.

Verified independently rather than inherited: `SCAN_DIRS = (modules, tools, hooks,
commands, agents, governance, rules)` — `vault/` is genuinely absent, so W11's "benchmark
exclusion is a property of scope" holds.

## 8. A destructive default, caught before it fired

`ucr_cif_oracle.main`'s `--store` **defaults to the canonical
`vault/ucr_cif/oracle_cases.json`**. A treatment run with default flags therefore
overwrites the control record the comparison is against, in place, with no confirmation.
The W12 arms were given explicit store paths for this reason. This is recorded as a
standing hazard rather than repaired, for the same freeze reason as §7.

## 9. Production Reality, per gate

| gate | status |
|---|---|
| PR-W12-1 worktree identity | **MET** — git-dir `…/.git/worktrees/pp-ucr-cif`, common-dir the PP repo, toplevel `C:/Users/User/Apps/pp-ucr-cif` |
| PR-W12-2 current HEAD | **MET** — W11 seal `f2f359d` confirmed, range `8c39376..f2f359d` |
| PR-W12-3 mutation re-drive | **MET** — 80 ALL_CAUGHT at final HEAD |
| PR-W12-4 restore | **MET** — source and runtime restores verified every plan |
| PR-W12-5 resource admission | **MET, and superseded** — `capacity_probe` ADMITTED; the binding gate is a different authority (§4) |
| PR-W12-6 oracle health | **MET** — canonical store re-derives; fingerprint reproduced |
| PR-W12-7 projection health | **MET** — rebuilt, `source_fresh True`, evidence unchanged |
| PR-W12-8 treatment frozen | **MET** — no semantic change to any treatment module this wave |
| PR-W12-9 production control | **MET** — flags and constants unchanged; no hidden enable |
| PR-W12-10…23 (paired run) | **NOT REACHED** — no arm completed |
| PR-W12-P1…P8 (promotion) | **DO NOT APPLY** — there is no promotion |
| PR-W10-10 label lineage | **OPEN — NOT EXERCISED.** No real label defect surfaced; none was manufactured |

## 10. Verdict

| question | answer |
|---|---|
| Is the prose relation real, typed, independent? | **YES** (W11, re-proved at this HEAD) |
| Does the treatment repair the routing harm? | **UNMEASURED** — no valid run was obtainable |
| Is the experiment too expensive to run? | **NO — falsified.** 155 MB, measured |
| Is this an experiment/runtime memory defect? | **NO** — §XLIII's test answered on evidence |
| Can a valid run be obtained without unsafe interference? | **NOT on this host as configured** |

**Promotion family unchanged: KEEP COMPUTED / REPORT-ONLY.** The signal keeps its W11
status because nothing this wave measured bears on it. The *experiment* is
`BLOCKED — RESOURCE / EXTERNAL`.

**The one Owner-side action that unblocks it**, named because it is the only lever this
mission does not hold: the reaper is disabled by starting Claude Code with
`CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` **in its environment at launch** — the
harness states that setting it from a shell command has no effect. The alternative is
fewer concurrent live sessions: 23 `claude` and 55 `Cursor` processes hold 16.6 GB of the
32 GB between them. Either one makes the run a thirty-minute job that completes.

Everything the run needs is committed, green, frozen and re-runnable. What is missing is
half an hour in which nothing reaps it.
