---
title: Frontier-28 — failure and trap record
date: 2026-08-25
status: OPEN — appended in the session each failure occurs (zero knowledge debt)
mandate: brief §46 (first failure already exists) · §47 (all session failures become capital) · §49 (UKDL three levels)
cutoff: bc81ca76cd8ef9ea78982c99016a03e979a91570
---

# Frontier-28 mission traps

Each entry was observed in this session with the evidence that produced it. None is
hypothetical, none is auto-promoted to UKDL — §49 requires an owner and a precedent check
before a rule is added, and this estate already carries three rule corpora.

---

## T-CONTAMINATION-INSTITUTIONALISED-001 — the audit's output became a permanent parent, not a transient hit

**Observed.** `d2a_engine.py::_discover_families()` promotes every directory under
`vault/knowledge_base/` to a family that later proposals are scored against. It reads the
working tree and derives keywords from **filenames**. The previous mission wrote
`vault/knowledge_base/ucr_cif/` and committed it; by the next session the engine was
scoring a new brief against `KB-UCR-CIF`, reporting coverage "capped by the plausibility
floor" against it. The advisory naming that parent was emitted by a hook, unprompted, at
the top of this very session.

**Why this is a different failure from its predecessor.**
`T-SELF-CONTAMINATED-DENOMINATOR-001` (2026-08-25, prior mission) described a *sweep
script* reading its own committed JSON. That contamination died when the script ended.
This one was written into the engine's **family table**, where it prices every future
proposal, for as long as the directory exists. Same root, radically different half-life.

**The distinction worth keeping.** A contaminated *measurement* is an event. A contaminated
*authority* is a state. The first is caught by re-running clean; the second survives every
re-run, because the corruption is now part of what "clean" means. When an audit writes into
a tree that any instrument treats as a source of authority, ask not "did this pollute my
result" but **"did this become something that will judge my successors."**

**Mechanism.** A filesystem-derived family carries no birth record. Nothing in the engine
could distinguish sealed institutional capital from an audit directory created on Monday,
because directory existence was the entire admission test.

**Fix applied.** `modules/duplicate_to_advantage/provenance.py`, wired into
`_discover_families()`. Two boundaries; the weaker is pinned by a gate precisely because
it is insufficient — see the next entry. Replay: cutoff `a3a66a8^` drops KB-UCR-CIF
(27→26 families); cutoff `bc81ca7` retains it, because `ucr_cif` genuinely predates this
audit. A *relative* frontier, not a blanket ban.

**Disposition.** UKDL trap candidate, high applicability. Sibling of
`PR-COVERAGE-BY-CONSTRUCTION-001` (a denominator must be discovered) and of
`T-SELF-CONTAMINATED-DENOMINATOR-001` (it must also be bounded). This adds the third face:
**it must also be dated**, because an unbounded denominator that is also undated does not
merely mislead one measurement, it appoints an authority.

---

## T-HALF-FIX-PASSES-ITS-OWN-CASE-001 — the obvious boundary would have admitted the very case it was written for

**Observed.** The first boundary implemented was tracked-ness: a directory with no
git-tracked files is in-flight output, not a sealed parent. It is the natural fix, it is
cheap, and it is correct as far as it goes.

It does not go far enough. The mission that created `ucr_cif` **committed** it the same
day. Under tracked-ness alone, `family_provenance()` returns `sealed: True, tracked: 3` —
the boundary written specifically to stop KB-UCR-CIF admits KB-UCR-CIF.

**Why it nearly shipped.** The fix was reasoned from the failure's *description* ("an audit
wrote into the tree it audits") rather than from the failure's *evidence* (`git log` says
that write was committed at 14:45:54, hours before it did any damage). The description
suggests uncommitted work; the evidence says otherwise. Nothing about the mechanism felt
wrong, and the test suite would have been green — because the test would have asserted the
mechanism's behaviour, not the original case's outcome.

**Fix applied.** A **declared** cutoff (`PP_AUDIT_CUTOFF`) closes it, and
`V-D2A-PROV-TRACKED-IS-NOT-ENOUGH` asserts the weaker signal's insufficiency *as a gate*,
so that a later reader removing the cutoff cannot mistake the half for the whole.

**Generalizes to.** Any fix reasoned from a failure's narrative instead of its artefacts.
**Re-run the original case against the proposed fix before believing it** — not a
reconstruction of the case, the case. A fix that cannot be shown failing the old input is
a hypothesis wearing a patch's clothes. Corollary worth keeping: **when a half-measure is
retained for defence-in-depth, pin its inadequacy in a named test**, or the next
maintainer will read its presence as sufficiency.

**Disposition.** UKDL process-rule candidate. Distinct from Regla 12 (two failures force a
mechanism pivot): here the *first* attempt was already insufficient and no failure would
ever have surfaced it, because the half-fix produces no error — only a silent pass.

---

## T-TEST-SKIPPED-ITSELF-GREEN-001 — a new gate reported 0/0 PASS at exit 0 while asserting nothing

**Observed.** `tools/test_d2a_provenance.py` probed availability with a bare `git`
subprocess. A bare `git` is **not** on this host's non-interactive PowerShell PATH (a
documented estate lesson). Every gate skipped, and the suite printed
`D2A_PROVENANCE_PASS=0/0  threshold=0/0` and exited **0** — a passing run that asserted
nothing, produced by the very file written to catch false negatives.

**Mechanism.** The harness and the code under test disagreed about how to find git.
`provenance.py` resolves it correctly (`shutil.which` plus a Windows fallback path); the
test re-implemented the lookup and got it wrong. A skip path that reports success is
indistinguishable from a pass in any output a human or a CI gate reads.

**Fix applied.** The test now asks the code under test how it finds git
(`prov._git()`), so the harness cannot disagree with its subject. Re-run: 6/6, three
consecutive runs.

**Generalizes to.** **A skip must never be spelled the same as a pass**, and a test harness
must not re-implement a capability lookup its subject already owns — the duplicate
inevitably drifts, and it drifts toward silence. Note `0/0` satisfies `threshold=0/0`:
a ratio gate is satisfied by an empty denominator, which is the estate's sealed
`feedback_never_gate_on_a_ratio` reappearing inside a brand-new file.

**Disposition.** Not a new rule — an **enforcement gap on two already-sealed ones**
(`never gate on a ratio`, `PowerShell git PATH gap`). The right output is a convention for
V-gate suites: a suite that executes zero gates exits non-zero.

---

## Standing obligation

Appended in-session, evaluated for UKDL promotion at Phase 6, never auto-promoted and
never silently dropped.
