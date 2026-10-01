---
type: source
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-sdd-external-research]
raw: raw/2026-10-01-sdd-external-research.md
kind: note
origin: research subagent (web), 2026-10-01; ~50 tool calls
---

# External benchmark: how engineers instruct AI coding agents

A research subagent's survey of how engineers and current tools instruct AI coding agents, plus the
evidence behind each practice. Tiers: **A** measured study, **B** vendor/practitioner claim with
detail, **C** opinion. Ends in a 33-item "engineer-grade spec checklist" used by
[[sdd-os-gap-analysis]].

## Coverage

- Tools: Spec Kit, Kiro (EARS), OpenSpec, Tessl / BMAD / Agent OS (search summaries only), Claude
  Code best practices, Codex AGENTS.md, Cursor, Devin, Aider, GitHub's analysis of 2,500 agents.md files.
- Classic engineering practice: ISO 29148 requirement qualities, EARS, Gherkin, Google design docs, ADRs. DoR/DoD,
  RFCs, OpenAPI and traceability matrices are from general knowledge, not fetched.
- Evidence: context files, tests as spec, clarification, decomposition, requirement quality, spec drift.

## Strongest findings

- **Context files don't reliably help.** "Providing context files does not generally improve task
  success rates, while increasing inference cost by over 20% on average"; repo overviews don't help.
  Gloaguen et al., arXiv 2602.11988, **verified against the abstract 2026-10-01**. [A]
- **Point the agent at the right tests; don't tell it to do TDD.** Showing which tests to check cut
  regressions from 6.08% to 1.82%; generic TDD instructions raised them to 9.94%, worse than no
  instruction. TDAD, arXiv 2603.17973, **verified against the abstract**. (Open-weight models only.) [A]
- **Clarifying before coding nearly closes the underspecification gap.** 69.4% vs 70.8% with a full
  spec; models default to not asking. arXiv 2603.26233, 2502.13069. Not verified by me. [A]
- **Compliance decays within a session.** ~5.6% lower odds per extra generated function; file
  size and position had no detectable effect. arXiv 2605.10039. Not verified by me. [A]
- **Success falls as more files are touched.** ~18% (1-2 files) to ~2% (7+). arXiv 2602.09540. Not verified. [A]
- **Structured specs and signatures help.** arXiv 2605.02455 **exists, but is a pilot study** (FSE
  Companion '26); its abstract has no numbers. The "+7.8% from signatures" and ">70% of failures
  statically detectable" figures come from the subagent and are unverified.
- **No controlled study shows full Spec Kit/Kiro workflows beat plain prompts plus tests.** The
  evidence covers components (signatures, tests, clarification), not the ceremony.
- **Practitioners criticise heavy spec process.** Kiro turned a small bug into 4 stories and 16
  acceptance criteria; reviewers "rather review code than markdown" (Böckeler, martinfowler.com). [B]
- **Spec drift**: conceptual proposals only; no measured drift rates.

## Disagreements

- arXiv 2604.24712 (exploratory) reports under-specification sometimes *helps*, so more spec is not
  always better. This sits against checklist items 4-6.
