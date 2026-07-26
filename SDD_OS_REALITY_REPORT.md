# SDD-OS Reality Report — why it never activates

**Date:** 2026-07-26
**Phase:** -1 (blocking reality scan, pre-approval)
**Primary source:** `Dataset SDD-OS 1.txt` (46,474 B, 3,774 lines) — located at
`C:\Users\User\Downloads\Dataset SDD-OS 1.txt` and mirrored at
`Downloads\Datasets Claude Power Pack\Datasets Sistemas Claude Power Pack\`.
Read via its sealed ingestion: `vault/knowledge_base/sdd_os/` (sha256 `a6c8f6bcd83a8230`,
5 PARTE files + MASTER, 48,210 B). PARTE I read in full — it is the governance layer
that defines activation.

---

## 0. Verdict up front

**SDD-OS is not missing. It is built, sealed, and unreachable.**

The dataset is ingested. The tier classifier works. Per-tier PRD templates exist.
Per-tier quality floors exist. A signal agent exists and sits in a live hook chain.

And across **91 scanned project directories**, the number that carry any SDD-OS
instruction, spec scaffold, or tier classification is **zero**.

The gap is not "no activation mechanism exists". The gap is that the one mechanism
that does exist is (a) invisible to the agent's instruction surface, (b) satisfied by
artifacts that prove nothing about the current task, and (c) advisory in a slot that
is frequently crowded out before it speaks.

---

## A. Where SDD-OS lives today

| Artifact | Path | Status | Evidence |
|---|---|---|---|
| Dataset (sealed) | `vault/knowledge_base/sdd_os/` — 5 PARTE files + `sdd_os_MASTER.md` | **SEALED** | 48,210 B, sha256 `a6c8f6bcd83a8230`, ingested by `tools/sdd_os_ingest.py` |
| Ingest tool | `tools/sdd_os_ingest.py` | EXISTS | one-shot; already run |
| Seal record | `vault/knowledge_base/sdd-os.md` | SEALED | SCS C39 / BL-SDD-OS-001, 2026-06-07 |
| Tier classifier | `modules/spec_gate/gate.py::classify_tier()` | **WORKS** | free text → Tier 0-3 + size + `requires_prd`; keyword tables mirror PARTE I §3-4 |
| Spec presence check | `modules/spec_gate/gate.py::check_spec_gate()` | **WORKS, WRONG PREDICATE** | see RC-2 |
| Signal agent | `modules/pp_agents/signals/sdd_tier.py` | WIRED, near-mute | see RC-3 |
| Per-tier PRD templates | `commands/prd-tier{0,1,2,3}.md`, `commands/prd-generate.md` | **ORPHAN** | not mirrored to `~/.claude/commands/` → not invocable |
| PRD generator module | `modules/sdd_os/prd_generator.py` | **ORPHAN** | zero callers; absent from the reachability registry entirely |
| Per-tier quality floors | `modules/output_contracts` `TIER_OQS_FLOOR` | EXISTS | 60/70/80/90 by tier |
| Test suite | `tools/test_sdd_os.py` | PASSES | 10/10 ×3 hermetic per the seal |

**Status summary:** sealed dataset, working classifier, two orphan surfaces, one
near-mute signal. Nothing writes a spec. Nothing blocks execution without one.

---

## B. Activation mechanisms — what actually fires

The live chain **does** exist, and it is shorter than expected:

```
settings.json  UserPromptSubmit
  └─ hooks/hook-dispatcher.js  --event=UserPromptSubmit-chain     [LIVE]
       └─ tools/jit_skill_loader.py                (PY_EXE child) [LIVE]
            └─ modules/pp_agents/proactive_dispatcher.py
                 └─ signals/sdd_tier.evaluate(prompt, cwd, project)
                      └─ spec_gate.classify_tier() + check_spec_gate()
```

Verified at `hooks/hook-dispatcher.js:251-260` (chain registration) and
`tools/jit_skill_loader.py:1230-1241` (dispatcher call).

So the honest finding is **not** "there is no activation path". There is one. But:

- `~/.claude/CLAUDE.md` contains **zero** occurrences of `SDD`, `Tier`,
  `classify_tier`, or `spec-driven` (case-insensitive grep, no matches). The agent's
  own standing instructions never mention the system.
- `vault/liveness/reachability_registry.json:326` classes
  `pp_agents/signals/sdd_tier` as **`PLANNED`** — "signal module built; no
  corresponding `agents/pp-*.md` currently imports it". That entry is *stale in its
  reasoning* (the dispatcher does import it) but *correct in its conclusion*: nothing
  durable reaches it.
- `modules/sdd_os/*` is **absent from the registry altogether** — not scored UNKNOWN,
  simply not in the denominator. This is `PR-COVERAGE-BY-CONSTRUCTION-001` firing on
  SDD-OS itself.
- Every throttle record under `vault/pp_agents/throttle/pp-sdd-tier_*` carries a
  pytest-tmpdir or v-gate name (`tmp*`, `sleepy_vgate_*`, `vg-dept-spec-*`). **There is
  no production firing record.** The signal has only ever run under test.

---

## C. State in the Owner's repos — measured, not assumed

Scanned every directory under `Desktop\Cursor Projects` (56 top-level) plus the
nested KobiiCraft / KobiiSports / Computer Personal Ops / Vibe Coding trees
(35 more) = **91 directories**, matching against the exact `SPEC_GLOBS` tuple the
gate itself uses.

| Measure | Result |
|---|---|
| Directories scanned | 91 |
| Carrying any SDD-OS reference in `CLAUDE.md` | **0** |
| Carrying a `.specify/` or `docs/specs/` scaffold | **0** |
| Where the gate is auto-satisfied by `vault/plans/*.md` | **27** |
| Carrying a real `PRD.md` | 3 (`CPGS`, `costaluz-rrss-pipeline-v2-prd-bootstrap`, `Jacobo`) |
| With no spec artifact of any kind | 61 |

Named repos from the brief:

| Repo | `CLAUDE.md` | SDD-OS ref | Spec artifact | Gate outcome |
|---|---|---|---|---|
| TUA-X | yes | **no** | `vault/plans/*.md` × 50 | silent (auto-satisfied) |
| TUA-X worktrees (×20) | yes | **no** | `vault/plans/*.md` × 27-41 | silent (auto-satisfied) |
| KobiiCraft Core Files | yes | **no** | `vault/plans/*.md` × 131 | silent (auto-satisfied) |
| InfinityOps (+2 worktrees) | yes | **no** | `vault/plans/*.md` × 15-16 | silent (auto-satisfied) |
| KobiiSports Resort | yes | **no** | none | would fire (advisory only) |
| AKOS | no | **no** | none | would fire (advisory only) |
| GEO-audit | yes | **no** | none | would fire (advisory only) |
| CostaLuz Lawyers | no | **no** | none | would fire (advisory only) |
| CommonWealth Ops | — | — | not found under `Cursor Projects` | unmeasured |

**The gap is real in production, and it is worse in the busiest repos.** The four
repos the Owner works in most (TUA-X, KobiiCraft, InfinityOps and their worktrees)
are precisely the ones where the gate is permanently silent — because they have
accumulated the most plan files.

---

## D. Gap analysis — Dataset requirement vs. reality

| PARTE I requirement | Exists? | Evidence |
|---|---|---|
| §3 Classify every task into Tier 0-3 **before executing** | **partial** | `classify_tier()` works, but is only consulted inside a signal that is silent for Tier 0-1 and silent whenever any spec-shaped file exists. No standing instruction makes the agent classify. |
| §4 Auto-trigger a PRD on 14 listed conditions; "ejecutar sin PRD queda prohibido" | **no** | Only ~2 of the 14 conditions are expressible as keywords. There is no enforcement surface — nothing refuses execution. |
| §5 Produce a PRD (problem/objective/non-goals/actors/FR/NFR/AC) | **template only** | `commands/prd-tier{0..3}.md` exist but are not invocable; `prd_generator.py` has zero callers. |
| §6 Architecture Spec before Tier 2/3 execution | **no** | No generator, no gate, no artifact in any repo. |
| §6.5 Kill switches | **no** | Eight stop conditions defined; none implemented for SDD-OS. |
| §7 Ambitious roadmap (5 phases) when warranted | **no** | No mechanism. |
| §8 Completion Gate (Spec/Arch/Execution/Validation/Standardization) | **partial** | Per-tier OQS floors exist in `output_contracts`; the five named sub-gates do not. |
| §11 Future Standardization Loop | **adjacent** | UKDL + compound-learnings cover the spirit; not bound to spec state. |
| §12 No standard regression / inheritance | **no** | No mechanism. |
| §13 Deliver classification + PRD + arch + roadmap + AC **inline, approvable** before Tier 2/3 | **no** | No mechanism. |
| §2 Universality — works in any repo, no prior docs required | **partial** | The primitives are cwd-aware and stdlib-only (genuinely portable), but nothing bootstraps a repo that has never seen SDD-OS. |
| Spec update loop (spec follows code) | **no** | Nothing detects or repairs spec drift. |

---

## E. Root cause chain

Four links. Each is independently sufficient to produce the observed silence.

**RC-1 — The instruction surface never mentions the system.**
`~/.claude/CLAUDE.md` is the only document loaded into every session in every repo.
It contains zero SDD-OS content. The agent is therefore never instructed to classify a
tier or demand a spec. The sole carrier is a level-2 hook advisory that the agent is
explicitly told is non-binding. *A governance system whose only voice is an advisory
the agent may ignore is a suggestion.*

**RC-2 — The gate's predicate does not test what the gate claims to test.**
`_find_spec()` returns the newest file matching `SPEC_GLOBS`, which includes
`vault/plans/*.md`. A repo with 131 historical plan files (KobiiCraft) passes the spec
gate forever, for every future task, regardless of whether any of those files describes
the task at hand. The gate answers *"does this repo contain a spec-shaped file?"* when
the question is *"does THIS TASK have a spec?"* There is no task↔spec binding.
This is the same defect class already sealed in memory as
`feedback_zero_cannot_fall` and `feedback_never_gate_on_a_ratio`: **a gate whose
predicate is satisfiable by something other than the thing it must prove.**

**RC-3 — The one live surface is advisory, late, and generates nothing.**
`sdd_tier` sits at position **10 of 13** in the dispatch plan under a
`MAX_ADVISORIES_PER_TURN = 3` cap — on a turn where three earlier signals fire, it is
cut before speaking. When it does speak it emits one sentence of prose and produces no
artifact. Zero production throttle records confirm it has never fired outside tests.

**RC-4 — Nothing bootstraps a repo, and nothing keeps a spec true.**
No scaffold on first contact with a repo (0/91 have one), so RC-2's "no spec" branch
never gets repaired — it just nags. And no drift detection, so even a correct spec
decays into a false source of truth the moment code moves past it.

**Causal summary:** RC-1 removes the instruction, RC-2 removes the trigger in the busy
repos, RC-3 removes the force where the trigger survives, RC-4 removes the recovery.
The system is complete on paper and inert in practice.

---

## F. Mode classification — PLAN MODE, not ULTRA-PLAN

Per `PR-MODE-SELECTION-001`: execution mode by default; ULTRA-PLAN only for a genuine
architectural decision or a new-from-scratch system.

- **Not from scratch.** The dataset, classifier, templates, floors, and dispatcher slot
  all exist and are correct. D2A+ applies: extend, do not rebuild. Roughly 70% of the
  build is done.
- **Mostly wiring.** RC-1, RC-3, RC-4 are registration, enforcement, and scaffold work
  against existing primitives.
- **One genuine design decision.** RC-2 — how a spec binds to a *task* rather than to a
  *repo* — is architectural and is carried into STOP #1 as an open decision rather than
  silently resolved.

Blast radius is transversal (every repo) but every change is reversible: additive
CLAUDE.md sections, additive scaffold files, and a gate whose predicate is narrowed
behind a fail-open path. ULTRA-PLAN's 3-5× output cost is not justified for wiring
work whose single architectural question can be surfaced in one decision.

**Classification: PLAN MODE with one escalated open decision.**

---

## G. Constraint noted for the plan — HR-001

`~/.claude/CLAUDE.md` is agent-owned global config. Under HR-001 the classifier blocks
agent writes to it in auto-mode. The plan must therefore ship the PP-internal half
(module, gate, scaffold, tests, and the exact text block) and surface the global
registration as an explicit Owner-side step — documented honestly, not advisory-tagged
as done.

---

## H. What this report does not establish

- `CommonWealth Ops` was not found under `Desktop\Cursor Projects`; its state is
  unmeasured. Path needed.
- PARTEs II-V (Contracts/Proof, Spec-Compiler, Requirements-Truth, Decision-OS) were
  not read in full for this scan — PARTE I governs activation, which is the question
  Phase -1 asks. They are required reading before implementing the spec *content*
  generators, and are called out as such in the plan.
- The scan measured spec *presence*, not spec *quality*. A repo counted as
  "auto-satisfied" may still hold a genuinely relevant spec; the point is that the gate
  cannot tell the difference.
