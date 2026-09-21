---
id: UACF-UKDL-SEED
name: UKDL seeds from the surface-architecture build
type: ukdl-seed
domain: uacf
status: awaiting-promotion
date: 2026-09-21
---

# UKDL seeds — surface architecture build, 2026-09-21

**Why these are here and not in `ukdl-universal.md`.** That file is ~9,000 lines and
shared. During this session the tree carried 426→437 dirty paths, four worktrees and at
least three other live sessions, two of which committed between my own commits.
`~/.claude/rules/concurrent-writers-shared-tree.md`: *prefer creating a NEW file over
extending a shared one while another writer is live* — pathspec isolation is
file-granular and cannot protect two writers inside one file. The iteration protocol's
FASE 4 permits the active project's vault as a destination. **Promote these into
`ukdl-universal.md` in a quiet tree.**

Every entry below came from a failure that actually happened in this session, with the
commit or command that produced it.

---

### T-D2A-FALSE-FOLD-ON-VOCABULARY-001 — trap

**Trap:** a 95 %-confidence FOLD verdict can be a word match.
D2A folded the proposed signup fabric into `MOD-ARCHITECTURE-HORIZON` at 95 %.
`architecture_horizon/horizon.py` is an import-graph blast-radius ranker whose own
docstring says it does not simulate and selects nothing. The only thing shared was the
word "architecture".
**Fix:** before acting on a high-confidence FOLD, read the named parent's **mechanism**,
not its name. `PR-OWNERSHIP-EVIDENCE-BEATS-SCORE-001` already says evidence beats score;
this is the case where the score was *highest*.
**Corollary:** in the same run, 17 of 20 systems returned DEFER at **exactly 45 %** — one
instrument giving one answer to seventeen questions carries no information. And the real
parent (`universal-meta-systems/runtime/specialization.py`) was never named by the
engine at all; it was found by reading.
**Evidence:** `d2a_engine.py --family-file`, 2026-09-21.

### T-SUBSTRING-DETECTOR-FLAGS-ITS-OWN-RULE-001 — trap

**Trap:** a prohibition that names its forbidden examples trips its own substring
detector. `V-SA-KERNEL-DOMAIN-BLIND` failed on the package docstring that said *"every
domain word — signup, onboarding, account, trial — lives in verticals/"*. A substring
matcher cannot tell a prohibition from a violation.
**Fix:** state the rule without citing the tokens, and **do not add an exemption list** —
an exemption written by the rule's author is an exemption for everything. Related:
`contaminates_kernel` matches by substring with no `\b` anchor
(`specialization.py:173-178`), unlike `applicability._hits` (`:104`), so `"sign"` hits
`"design"` and `"form"` hits `"information"`. Domain vocabulary must be multi-token.
**Evidence:** commit `c190bd5`.

### T-DISQUALIFIER-INFLATION-001 — trap

**Trap:** counting a rule's *exclusions* as evidence for it. A scoring function summed
`requires + disqualifiers`, so the archetype declaring the most ways it could lose won.
**Fix:** a condition that did not fire is the absence of evidence against, never evidence
for. Count only what had to hold.
**Evidence:** commit `e17eb4f`, caught by a contrasting-fixture set, invisible to unit tests.

### T-RESIDUAL-MAKES-AN-OUTCOME-UNREACHABLE-001 — trap

**Trap:** adding a zero-requirement fallback to a registry makes "nothing matched"
impossible, silently retiring an outcome. `STRUCTURED_CONFIGURATOR` is always justified,
so the justified set is never empty and `ABSTAIN` became unreachable while still being
declared, tested and documented.
**Fix:** after adding any always-true member to a decision set, re-ask which branches are
still reachable, and either give the outcome a reachable meaning or delete it. Sibling of
the estate's existing rule that a predicate's two branches must both be reachable.
**Evidence:** commit `e17eb4f`.

### PR-INHERIT-VERBATIM-NEVER-PARAPHRASE-001 — process rule

**Rule:** when a child inherits a boundary from a parent, copy the strings; do not improve
the wording. `HR-APA-017` compares by value, so *"which component renders a step"* in
place of *"which component realises a semantic"* reads as a **dropped** boundary, and
`derive()` refused the first real seed.
**Fix:** declare ADDITIONS only and union the parent's list at build time, so a new parent
boundary is picked up automatically instead of being silently lost. Paraphrase is how a
constraint quietly disappears.
**Evidence:** commit `b6dc52a`.

### PR-FIXTURES-FALSIFY-THEY-DO-NOT-CONFIRM-001 — process rule

**Rule:** write the expected outcome of every fixture **before** running it, and when
reality disagrees, decide explicitly whether the expectation or the code was wrong — then
say which, in the fixture.
In this build the contrasting set produced three genuine defects **and** two wrong
expectations of mine. Had the expectations been written after the first run, all five
would have been recorded as passes.
**Fix:** a scenario set exists to falsify. Assert outcome AND result together; a set that
only checks the outcome passes while the wrong answer is produced.
**Evidence:** commit `e17eb4f`; the regulated fixture carries its own correction inline.

### T-DATACLASS-NEEDS-SYS-MODULES-REGISTRATION-001 — trap

**Trap:** a module loaded via `importlib.util.spec_from_file_location` is not in
`sys.modules`, and `@dataclass` resolves `sys.modules.get(cls.__module__).__dict__`
(`dataclasses.py:749`). Every dataclass in it raises
`AttributeError: 'NoneType' object has no attribute '__dict__'` — a message that points
nowhere near the cause.
**Fix:** register the module **before** `exec_module`, and pop it on failure so a
half-executed module is never left behind. Needed here because a package directory name
contains a hyphen, which `import` cannot spell.
**Evidence:** commit `b6dc52a`.

### T-A-GATE-THAT-GRADED-ITSELF-WITH-A-STRING-001 — trap

**Trap:** an estate can hold an honest grader and never call it.
`done_gate/strength_ladder.assess` — thirteen rungs, three-valued evidence, refuses a
claim stronger than its evidence — had **no caller**. `callable_inventory.json:571-573`
records it `PROSE_ONLY`; its only invoker was a sentence in a command file. Meanwhile the
*reachable* production-reality surface, `gsd_x/mission/closure.py:116`, is a self-declared
string defaulting to `"UNPROVEN"`.
**Fix:** `tools/prg_assess.py`. Its probe measures what it can and leaves the rest
**absent**, and `--fast` demonstrates this by dropping the ladder from
ADVERSARIALLY-VERIFIED to WIRED when it skips the one instrument that could measure
reachability. A probe that filled in unmeasured rungs would be the laundering the gate
exists to refuse.
**Evidence:** commit `d1ee4ed`.

---

## Candidates deliberately NOT promoted

The three patterns extracted from the reference clip — invariant promise beside varying
evidence, an outcome-named primary action, a returning-party path at the value boundary —
have **one** source: a single 5.72 s recording of a preview deployment. LAW 10,
applicability before universalization. They are recorded in `UACF-01` §5 with their
confidence and what would move them, and they are not baseline obligations.
