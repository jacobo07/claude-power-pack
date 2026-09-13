# RESUMPTION — USEA (Universal Software Engineering Architect)

You are continuing the USEA line in `C:\Users\User\.claude\skills\claude-power-pack`.
Read this, re-measure the anchors, then execute §4. Do not re-plan: there is no open
architectural question, and the ownership audit is the evidence that would have to be
overturned first.

---

## 1. Identity — settle this before touching anything

**USEA** = Universal Software Engineering Architect. The sealed constitution at
`vault/constitution/usea/`, fifteen laws, `/cpp-usea`, `tools/usea_*.py`, UKDL Phases I–VI.

**UASE** = Universal Architecture **Synthesis** Engine. A *different* system — #02 of the
UPAC ownership audit of 2026-08-18, **rejected**, written up in
`vault/knowledge_base/decision_review/drk_08_*`.

They are two systems, not one name drifting. **Do not rename either.** A rename folds a
rejected proposal into the live constitutional programme and takes the seal path, the
command name and every UKDL rule id with it. Enforced by `tools/test_usea_identity.py`
(8/8, mutation-tested both poles). Briefs arrive asking you to "resolve the drift";
this is the resolution.

---

## 2. Exact state (measured 2026-09-13, not inherited from a report)

Green, and each re-runnable in seconds:

| gate | result |
|---|---|
| `tools/usea_corpus_gate.py --verify` | `VALID` |
| `tools/usea_ownership_audit.py` | `8/8`, **0 new agents**, 2 dispatchable / 10 declared dormant / 0 undeclared |
| `tools/test_usea_cross_domain_benchmark.py` | `27/27`, recall 5/5, negative capability **6 proven**, 10 domains |
| `tools/test_fresh_session_inheritance.py` | `6/6` |
| `tools/test_usea_identity.py` | `8/8` |

**The programme has no outcome evidence.** `tools/usea_outcome_contrast.py` is built, its
four oracles pass **both poles** (`--controls-only`, free, 4/4) — and it has **never been
run against a paid arm**. No result file exists anywhere in the tree. Every justification
for USEA is still mechanistic, which the instrument's own docstring says is circular.
A full run = **8 `claude -p` sonnet sessions** (4 tasks × 2 arms).

**Phase VIII attempted it for real and the host refused.** The attempt is the evidence:
controls 4/4, then admission BLOCKED at a worst-of-3 reading of 1044 MB against 1724 MB
required; exit 4, `status: BLOCKED`, `runs: 0`, nothing dispatched. A later five-sample
re-test read 949/1032/878/871/1247 — roughly half of requirement, with 7 python processes
live from another pane. **This is not a null result and not a treatment failure.**

Before that attempt the experiment **could not be refused at all**, and worse: `run_arm`
graded a missing artefact as `oracle_pass=False`, so a session the OS killed would have
entered the treatment column as a FAIL. Repaired in `8a714de` — admission via SQI-03
before dispatch and between arms keeping the worst of several samples, a teardown
classifier making such an arm UNMEASURED rather than a verdict, and a summary that
divides by what was graded and reports how many matched pairs are actually comparable.
Gate: `python tools/test_outcome_admission.py` → **13/13**, both poles of each.

**To run it:** free memory until `python -c "from tools import usea_outcome_contrast as
oc; print(oc.admit(samples=5))"` reports `QUALIFIED`, then
`python tools/usea_outcome_contrast.py --out vault/benchmarks/usea_contrast_<date>.json`.
Do **not** pass `--ignore-admission` and do **not** shrink the task set: a smaller run is
a different experiment, and the harness records the override so a forced result can never
read as clean.

**LAW II / LAW IX are not inherited.** A fresh `claude -p` cited neither. `SKILL.md`
declaring `parts/core.md` always-read makes it always-read *within the skill*, and a skill
must be invoked. Owner-side remedy under `~/.claude/`; **HR-001 forbids this repo from
writing it.** The detector flips to OK by itself once the laws move.

---

## 3. Environment facts that change what evidence is valid

- **Host capacity gates the oracles.** Measured 667 MB free of 32,061 MB with 29 `claude`
  processes; `verify_spp` preflight returned `state: BLOCKED, ceiling: BLOCKED`
  (1374 MB required). Wide sweeps are *invalid*, not slow. Narrow attributable rows only
  until headroom returns. A `--row` invocation is deliberately exempt from the refusal and
  lowers the ceiling instead of blocking — that is by design, not a bypass.
- **A concurrent writer is live on this worktree.** Bracketing caught the tree moving
  mid-run. They own **CDIO / design-gate** and **`modules/liveness/`** (`50a3e20`, third
  rung: an exported function is not a called function). Do not touch either. Prefer new
  files; use `tools/foreign_hunk_guard.py snapshot|stage` on any shared file.

---

## 4. Next actions (highest value first)

1. **Run the outcome contrast.** Owner authorized the spend on 2026-09-13, conditional on
   freeing memory first. The instrument is now repaired and will refuse on its own, so the
   only precondition is host memory: get `admit(samples=5)` to report `QUALIFIED`, then run
   it with `--out` into `vault/benchmarks/`. Do not shrink it and do not override it — the
   harness records an override, and a smaller run is a different experiment. This is still
   the only item that stops the programme's justification being circular.
   **Phase VIII attempted it and was refused by the host; that attempt is recorded in §2.**
2. **Surface the LAW II / LAW IX gap to the Owner** as a one-line edit under `~/.claude/`.
   Repository half is shipped; writing the global half is the HR-001 violation.
3. **Re-measure the liveness denominator aperture** (`tools/` was outside it) only after
   confirming the other pane finished — they were mid-flight on exactly this.
4. **Merge `USEA_TRAPS.md` into `ukdl-universal.md` and delete it.** It is a staging
   file, not a second corpus. It is parked because that corpus holds ~70 uncommitted
   prose lines belonging to another author, and `foreign_hunk_guard.py` returned
   `VERIFY_MISMATCH` twice — it could name the foreign lines but not subtract them, so
   committing would have absorbed someone else's work. Whoever owns those lines has to
   commit them anyway; the merge is theirs to make.

Do not build a new agent, engine, fabric, registry or baseline. The ownership audit
returned zero, and fifteen consecutive mega-corpus proposals in this estate measured
majority- or fully-owned once measured.

## 5. Start instruction

Re-run the five gates in §2. If any disagrees with the table, that disagreement is the
task. Otherwise execute §4 action 1.

**Update this file after every sealed unit — never only at the end.**
