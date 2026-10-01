---
type: synthesis
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-sdd-external-research, 2026-10-01-sdd-internal-inventory]
---

# SDD-OS gap analysis: does it instruct an AI the way an engineer would?

**Question (Owner, 2026-10-01):** every technical gap SDD-OS has in instructing AI models the way a
software engineer would.

**Method.**
- External benchmark: a 33-item checklist with evidence tiers ([[2026-10-01-sdd-external-research]]).
  I verified two tier-A papers against their abstracts.
- Internal inventory of SDD-OS with file:line evidence ([[2026-10-01-sdd-internal-inventory]]).
- My own checks: I re-read the binder and the gate code, and ran `wiki/tools/sdd_probe.py`, which calls
  the real `classify_tier` and `evaluate` against a temp repo, with a no-spec control.
- Code references are @ `e0f541f` unless noted. Component page: [[sdd-os]].

## Answer in one paragraph

SDD-OS gets the shape right (tiered ceremony, spec before code, a standing instruction, a live
per-prompt check), and the shape is what practitioners recommend. But it checks that a spec *exists
and names the task*, never what the spec *says*. Everything is advisory text, so nothing enforces it.
The ingredients with measured evidence are each missing or optional: naming which tests to run and
what must not regress, resolving open questions before coding, giving signatures and files, keeping
work to few files. Nothing measures whether SDD-OS changes outcomes. In engineering terms it is a
ticket template plus a reminder, not a spec process: no definition of ready, no review against the
spec, no traceability that runs.

## Verified defects (reproduced 2026-10-01 with `tools/sdd_probe.py`)

| # | defect | evidence |
|---|---|---|
| D1 | **An empty draft spec unlocks a T2 task.** Front matter `covers: [billing]`, `status: draft`, blank `AC-001`. The decision flips from `write_spec` (no-spec control) to `proceed`. | probe; `modules/sdd_os/pre_exec_gate.py:330-338` returns `proceed` on any binding; `spec_binding.py:259-270` reads only `covers` |
| D2 | **An unrelated task binds through one shared word.** "fix billing typo in the README footer" binds to the billing spec, gets `proceed`, and is classed T2 because "billing" is a T2 keyword | probe; `spec_binding.py:195-205` (subset match); `spec_gate/gate.py` `_TIER2` |
| D3 | **Tiers come from vocabulary, not risk.** "refactor the APIs and modules" → T1 (plural misses `\b` match). "drop the old table" → T1 (destructive data change). "rename … across the public SDK" → T0 (breaking API change). | probe; `spec_gate/gate.py:196-219`, default T1 when nothing matches |
| D4 | **Prohibitive wording, advisory mechanism.** "execution without a spec is not permitted" is injected text; the hook fails open and nothing refuses an edit | `pre_exec_gate.py:377-381`; `activation.py:140` |
| D5 | **The template never reaches the agent.** For T2/T3 the agent gets a filename only; the skeleton is written only by the CLI | inventory §1, `activation.py:14,26-33` |
| D6 | **Spec tier is ignored.** `read_tier` exists but the binder never calls it, and real specs write `tier: T2`, which it cannot parse | inventory §3; `spec_binding.py:181` |

## Scored against the engineer-grade checklist (33 items)

✗ = missing, ◐ = partial (exists but optional, unwired or unchecked), ✓ = met. Tier = strength of the
outside evidence for the item.

| # | checklist item (abridged) | tier | SDD-OS | why |
|---|---|---|---|---|
| 1 | Spec sized to the task | B | ◐ | Tiers exist; assignment is keyword-based (D3) |
| 2 | WHAT/WHY, not steps | B | ◐ | Template has Problem/Objective; unchecked |
| 3 | Singular requirements | B | ✗ | No check |
| 4 | Unambiguous requirements | A/B | ✗ | "Ambiguity Scanner" is doctrine only (PARTE IV), 0 code |
| 5 | No contradictions (incl. with CLAUDE.md rules) | **A** | ✗ | No check |
| 6 | Omissions filled (errors, edges, data) | A/B | ◐ | Template §8.4 "failure modes", a blank prompt |
| 7 | AC executable / mapped 1:1 to tests | A/B | ◐ | `intent_verified` joins V-gate ids, CLI-only, no hook; template AC-ids have no consumer; 9 of 64 criteria satisfied (`vault/audits/DONE_GATE_AUDIT.md:84-92`) |
| 8 | Structured AC (EARS / Given-When-Then) | B | ✗ | Free text `AC-001:` |
| 9 | Declarative examples with concrete data | B | ✗ | — |
| 10 | Names files, interfaces, signatures | A? | ◐ | Template §8.1/§8.3 blank prompts; not injected (D5) |
| 11 | Points to an in-repo pattern to imitate | B | ✗ | No section |
| 12 | Explicit non-goals | B | ◐ | Template §3; 9 of 33 real specs have one |
| 13 | Alternatives + decision record | B | ✗ | No section in SDD-OS |
| 14 | Open questions resolved before coding | **A** | ✗ | No section, no step; only a "knowledge gap" verdict about missing doctrine, not task ambiguity |
| 15 | When to stop and ask (always/ask/never) | A/B | ◐ | "Ambiguity = Stop" is prose in CLAUDE.md |
| 16 | Regression guard (tests that must still pass) | **A** | ◐ | T1 "Regression risk" heading; 0 of 33 real specs have it |
| 17 | Exact test commands, not "do TDD" | **A** | ◐ | Template "Test plan"; the best real specs do it by hand; not required |
| 18 | Bugs start from a failing repro test | B | ✗ | A bug fix is T1 → three inline questions |
| 19 | Static gates in done | A? | ◐ | `TIER_OQS_FLOOR` called only from tests |
| 20 | Small, independently verifiable checkpoints | **A** | ✗ | No tasks section; decomposition lives in GSD / `/ultra`, not linked |
| 21 | Task dependencies / parallel waves | B | ✗ | — |
| 22 | Independent fresh-context review against the spec | B | ◐ | PP has reviewers; none is given the spec |
| 23 | Self-contained for a fresh session | B | ◐ | Specs are files; nothing checks they stand alone |
| 24 | Minimal instruction files | **A** | ✗ | SDD-OS adds a section to a 39,810-char global CLAUDE.md plus a per-prompt injection (4,097 so far) |
| 25 | Critical rules enforced by deterministic gates | **A** | ✗ | D4 |
| 26 | Traceability requirement → task → test → commit | B | ◐ | CLI-only join on V-gate ids |
| 27 | Measurable NFR thresholds | B | ◐ | Template §6, blank |
| 28 | Spec in repo, versioned, change as deltas | B | ◐ | In git; no delta / change control |
| 29 | Spec updated when code diverges | B/C | ◐ | `scaffold.check_drift`: repo-wide mtime compare, CLI-only |
| 30 | Done names the evidence to show | B | ◐ | Template §11 "Completion gate"; PP culture; unchecked |
| 31 | Artifacts short enough to be read | B | ✗ | T2 template has 11 sections, T3 adds 5; no length budget |
| 32 | Ceremony declared, explicit escalation criteria | B | ◐ | Tiers declared; criteria = keywords |
| 33 | Effectiveness measured on own tasks | **A** | ✗ | No eval or ablation; only injection counts |

**Totals: 0 met, 18 partial, 15 missing.** Of the 8 items backed only by tier-A evidence (bold),
**6 are missing and 2 partial** (#16, #17). Every partial item has the same flaw: the template allows
it, but nothing requires it.

## Gaps outside the checklist

- **Doctrine without code.** PARTE II–VI (spec compiler, requirement drift detector, ambiguity
  scanner, kill switches, regression inheritance) are markdown only (inventory §5, §10).
- **Two gates disagree.** The old `spec_gate.check_spec_gate` (any spec-shaped file passes) still
  serves `sdd_tier`, `one_shot/compiler.py` and `dataset_first/classifier.py` (inventory §3).
- **Docs contradict code.** `governance/SDD_OS_GOVERNANCE.md:93-99` says the directive writes
  after scaffolding; `activation.py:26-33` says the hook never writes. Code wins (test
  V-SDDOS-HOOK-READONLY). Same pattern as [[portfolio-learnings]].
- **Not installed.** `/cpp-sdd-os` and `/prd-tier0..3` are absent from `~/.claude/commands`.
  `.specify/` holds an unfilled Spec Kit constitution template, so Spec Kit is not in use.
- **Real specs beat the template.** The best specs (`vault/specs/post-edit-diagnostics.md`,
  `gsd-long-run-v2.md`) have a measured problem, a behaviour contract, "not done, deliberately",
  and exact test commands. They were written by hand; the template produces none of that.
- **Tests prove the machinery, not the outcome.** 14/14 and 9/9 pass, as they should. None checks the
  content of a bound spec, which is why D1 passes the suite.

## What to change, ranked

Rank = strength of evidence × how directly it changes what the agent does × cost. None of this is
approved; each needs an improvement page and an Owner decision.

1. **Measure before adding ceremony** (#33, tier A). No study shows full spec workflows beat a
   plain prompt plus tests, and context files can cost more than 20% extra for no gain. Replay ~20
   past T2 tasks with SDD-OS on and off and score them.
   Folds into [[measure-knowledge-store-consultation]]'s method. Cost: M.
2. **Bind only to a spec that is ready** (D1, D2, D6). Refuse `proceed` when the spec is
   `status: draft`, when its tier is below the task's, or when it lacks at least one AC with a runnable
   check and a "must still pass" line. Fixes the probe's false "proceed" decisions. Cost: S; the
   probe becomes its test.
3. **Inject the tier-A ingredients, not the whole template** (#14, #16, #17, #20, #10). For T2+, ask
   for exactly five things:
   - open questions, answered or explicitly assumed;
   - files and signatures to touch;
   - the test command that proves done;
   - tests that must keep passing;
   - checkpoints of a few files each.

   Drop the rest unless the task needs it (#31). Cost: S.
4. **Tier by blast radius, not vocabulary** (D3, #1, #32). Add signals: files likely touched,
   destructive data verbs (drop, delete, truncate, migrate), public-API words (SDK, public, breaking),
   and plural/stem matching. Cost: S-M.
5. **Run traceability in the done-gate** (#7, #26). Make `intent_verified` join on AC ids and run
   it from the Stop / done path, not only the CLI. Cost: M.
6. **One deterministic gate, where it pays** (#25, tier A). Ask-mode PreToolUse on Edit/Write for
   T3, or for T2 data or public-API tasks with no ready spec. Everything else stays advisory to avoid
   friction. Cost: M; needs a kill switch.
7. **Clean-up.** Retire the old `check_spec_gate` callers, install or delete the
   orphan commands and `.specify`, fix the governance consent text, and replace the mtime drift
   heuristic with a per-spec check of the files the spec names (#29). Cost: S each.

## Open questions

- Does SDD-OS improve outcomes at all, after adjusting for its token cost? Unmeasured (item 1).
- Should the template converge on the Owner's best hand-written specs rather than the generic
  PRD skeleton?
- arXiv 2604.24712 reports under-specification sometimes helps code correctness. Where is the floor
  below which more spec hurts?
