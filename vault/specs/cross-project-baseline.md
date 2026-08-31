---
title: Cross-project baseline — promote and inject what one project learns
date: 2026-08-31
tier: T2
status: PROPOSED — awaiting Owner decision on §5
covers: [cross_project_baseline, ceps_promotion, promote_to_global, compound_learnings,
         learning_sentinel, global_rules, graph_first_gate, baseline_injection,
         portfolio_learnings, flywheel_read_side]
origin: Owner 2026-08-31 — "siento que globalmente mis proyectos no estan usando y
        documentando todos los cambios y mejoras que hago, para que sean baseline para
        otros proyectos... y eso deberia pasar globalmente aunque no les de esa orden
        en el prompt, SIEMPRE"
---

# Spec — cross-project baseline

## 1. The measurement

The machinery is not missing. **Its first stage is the only one that runs.**
Measured 2026-08-31 by direct read, not recalled:

| Stage | Owner | Wired? | Measured state |
|---|---|---|---|
| CAPTURE an error/learning | `hooks/bug-hunter-ceps-bridge.js` (PostToolUse-Bash, fires in every project) | ✅ | **101 events across 17 project roots.** Fired twice during this session |
| DETECT recurrence | `pattern_signature` in `tools/ceps.py` | ✅ | **8 of 56 distinct patterns already span ≥2 projects**; one spans **7** |
| PROMOTE to global scope | `tools/ceps.py::promote_to_global` | ❌ | **A pure predicate.** Returns a bool, writes nothing. Its only caller in the tree is `tools/test_uqf.py` |
| MATERIALISE to `~/.claude/rules/` | `hooks/learning-sentinel.js` + `/cpp-compound` | ❌ | `state/compound-learnings.json` → **`"last_run_global": null`** — the global pass has never run. Per-project `last_run_iso` frozen at **2026-05-15** (108 days). `~/.claude/rules/` holds **2 files, both dated 2026-05-29**, both ECC absorptions — zero derived from any project |
| INJECT into a different project | `hooks/graph_first_gate.js` | ❌ | Reads the promoted store but emits only `globalCount` — **a number**. `hooks/cascade_check_bash.js`, the other wired Bash consumer, contains **zero** references to the event log |

`vault/ceps/fires.jsonl` holds 89 records. Every one carries
`producer: "bug-hunter-ceps-bridge"` and `signal: "unknown"`, with **no
`project_id`**. Those are the *capture* bridge logging itself — not a past
pattern being surfaced to prevent a repeat. **The read side has zero records,
ever.**

So the Owner's report is exact, and the break is locatable to three joints:
the estate writes diligently, promotes nothing, and reads back a count.

This is `feedback_producer_fires_sink_empty` at estate scale, with
`feedback_dead_consumer_hides_bad_producer` as the reason it stayed invisible:
nothing consumed the log, so nobody noticed the log was never being promoted.

### 1.1 The eight patterns that already qualify

`promote_to_global` returns `True` at ≥2 distinct projects. These would all
return `True` today and none has ever been promoted:

| signature | projects |
|---|---|
| `5d28a90f4498a814` | **7** — GEO-audit, KobiiCraft, KobiiSports, power-pack + 3 unresolved |
| `d47d40fe40071e32` | 4 — KobiiCraft, KobiiSports + 2 |
| `5ee413c0d90a1085` | 3 — GEO-audit, KobiiCraft + 1 |
| `42168ff94099d7df` | 3 — GEO-audit, power-pack + 1 |
| `d284f9fa8e8a94c8` | 3 — KobiiCraft + 2 |
| `b77f13ea8d89b1be` | 2 — KobiiCraft, power-pack |
| `8a8f7e7df7ae6c02` | 2 — power-pack + 1 |
| `c773f25b4c2973b3` | 2 — Jacobo + 1 |

The Orca X case the Owner names is the same shape: 8 events captured, zero
promoted, and nothing in any other project would ever surface them.

## 2. What is NOT the problem

- **Not capture.** It works, globally, without being asked. Do not rebuild it.
- **Not storage.** `vault/ceps/events.jsonl` is a single file in the Power Pack
  repo, shared by every project. Cross-project storage already exists.
- **Not the vocabulary.** Three rule corpora, `PORTFOLIO_LEARNINGS.md`, the
  graph's `PROMOTABLE` set (`hard_rule`/`trap`/`decision`/`contract`/`dataset`/
  `scs_seal`) already define what is worth carrying between projects.
- **Not a new dataset family.** Per `HR-NOVELTY-001`, this classifies as
  **EXTEND_EXISTING_OWNER** on three named owners. A new institutional layer
  here would be the sixteenth majority-owned proposal in this estate.

## 3. Design — three joints, no new system

### 3.1 Promotion producer (closes the `promote_to_global` orphan)

A pass over `events.jsonl` that groups by `pattern_signature`, applies the
EXISTING predicate, and writes qualifying patterns to a global baseline file
with their project set and evidence. The predicate stays exactly as it is; what
is added is a **writer**, so the boolean finally has a consequence.

Absolutes, not ratios: the output is a NAMED SET of promoted signatures, and
the gate fails while a qualifying pattern is unpromoted — never a coverage
percentage (`feedback_never_gate_on_a_ratio`).

### 3.2 Injection consumer (closes the count-only read)

`graph_first_gate.js` already reads the promoted store on every Bash and Read,
cheaply, in every project. It gains the ability to emit **matching content**
rather than a count — bounded to the top N by relevance to the current command
or file.

The relevance term must be **necessary, not weighted**
(`feedback_constant_factors_rank_nothing`: five of six scoring factors were
per-item constants, so relevance 0.0 still cleared MANDATORY and 8 of 9 items
activated). A promoted pattern that does not match the current context emits
nothing. Silence is the default; an unconditional dump of eight rules into
every prompt in every project is the failure mode this must avoid, not the goal.

### 3.3 Materialisation (the never-run global pass)

`"last_run_global": null` is the single most actionable number here. The
compounding pass that turns recurring signals into durable `~/.claude/rules/`
entries has never executed. Whether it should now run automatically is **not a
call this spec makes** — see §5.

## 4. Files (on approval)

| File | Change |
|---|---|
| `tools/ceps.py` | `promote_patterns()` — the writer behind the existing predicate |
| `vault/ceps/promoted.jsonl` | new — the global baseline set, append-only |
| `hooks/graph_first_gate.js` | relevance-gated content emission, replacing count-only |
| `tools/test_cross_project_baseline.py` | V-gates below |

## 5. The decision that is the Owner's, not mine

**The Owner's "SIEMPRE" contradicts a standing design choice in this repo.**
Stating it rather than silently resolving it:

`compound-learnings` is declared **"Sleepy: gated by `/cpp-compound`, never
autoruns"**, and the Sovereign Standard says *"future skills MUST be latent-card
+ JIT-full-depth, never always-on."* Sleepiness is deliberate token austerity,
not an oversight. "Always, without being asked" is the opposite instruction.

Three ways to resolve, and they are genuinely different products:

- **(A) Cheap-always, expensive-sleepy** *(recommendation)* — promotion (§3.1)
  and relevance-gated injection (§3.2) run automatically in every project,
  because both are file reads of a ~100 KB store that `graph_first_gate`
  already performs. The expensive synthesis (`/cpp-compound`) stays gated.
  Satisfies "SIEMPRE" for the part the Owner actually feels missing — *the
  learning reaching the next project* — without breaking austerity.
- **(B) Fully automatic** — the global compounding pass runs on a schedule too.
  Maximum propagation; retires the sleepy doctrine for this skill and costs
  tokens in every session. Needs an explicit retirement of that doctrine, not
  a quiet exception.
- **(C) Promotion only** — write the baseline, keep injection manual behind a
  command. Cheapest, and leaves the Owner's actual complaint open, since a
  baseline nobody reads is the exact state measured in §1.

## 6. Acceptance criteria (done-gate)

| Gate | Assertion |
|---|---|
| `V-XPB-PROMOTES` | every signature with ≥2 distinct `project_id`s appears in `promoted.jsonl`; the 8 named in §1.1 are present |
| `V-XPB-NO-SELF-PROMOTION` | a signature seen many times in ONE project does **not** promote — recurrence is not portability (`feedback_truth_proof_is_not_transfer_proof`) |
| `V-XPB-INJECTS-CONTENT` | a context matching a promoted pattern receives the pattern's **text**; the count-only path is gone |
| `V-XPB-SILENT-ON-NO-MATCH` | an unrelated context receives **nothing** — proves relevance is necessary, not weighted |
| `V-XPB-FAIL-OPEN` | a corrupt or absent `promoted.jsonl` degrades to silence, never an exception in a hook |

## 7. Out of scope

- **No new corpus, family, or institutional layer** (§2, `HR-NOVELTY-001`).
- **No change to capture.** It works; touching it risks the one stage that does.
- **No retroactive rewrite** of the 101 existing events. Promotion reads them;
  it does not edit them.
- **No auto-materialisation** unless the Owner picks (B) in §5.
