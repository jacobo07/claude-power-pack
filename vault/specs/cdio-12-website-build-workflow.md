---
id: SPEC-CDIO-12
title: CDIO-12 Website Build Workflow (absorption of the "Create a Pro Website" Claude Code method, video fDTwHIKltpc)
tier: T2
status: approved
covers: [cdio-12, website-build-workflow, build-workflow, fDTwHIKltpc, test_cdio_build]
owner_go: "estudiate este video https://www.youtube.com/watch?v=fDTwHIKltpc para ingestar todo este metodo en CDIO y hacerlo todo exactamente igual e incorpora a CDIO todo lo que hay en el backlog de github" (2026-11-12); scope answers - all four CDIO backlogs, generic deploy under DEPLOY_GOVERNANCE (not Hostinger), phased (CDIO-12 first, then backlog item by item)
---

# SPEC — CDIO-12 Website Build Workflow

## Objective

CDIO judges a website (CDIO-00..05), picks its direction (CDIO-06), contracts its behaviour
(CDIO-07) and owes it legal pages (CDIO-10). It has no account of **how a website gets built**
from an Owner request: what to gather first, which skills to load, where the reference comes
from, what the first prompt says, which questions are asked before code, how the first draft is
reviewed and iterated, and how it is published. The video "The EASY way to build a beautiful
website with Claude Code (full workflow)" (Create a Pro Website, 2026-07-02, 26:00) teaches one
such method end to end. This spec absorbs that method step for step into CDIO as dataset
CDIO-12, keeping every step, and records the four points where a literal copy would breach an
existing floor and what replaces it.

## Scope

1. `vault/knowledge_base/cdio/CDIO-12-website-build-workflow.md` — sealed dataset: the nine
   steps of the method (sec. 2), the first-prompt template (sec. 3), the intake questions
   (sec. 4), the criteria in the CDIO-08 grammar (sec. 5), the four floor collisions (sec. 6),
   publishing under DEPLOY_GOVERNANCE (sec. 7), evidence and limits (sec. 8).
2. Wiring: CDIO-00 `governs`, the three CDIO agents (repo + live mirrors), `tools/test_cdio.py`
   dataset count 12 -> 13.
3. `tools/test_cdio_build.py` — V-CDIO-BUILD-* done-gate, including a FIDELITY check that every
   step of the video has its section in the dataset.

## Out of scope

- No new Python module and no scorer change: criteria report under the existing dimensions.
- Hostinger, its affiliate link and its coupon are not adopted (Owner answer 2). The video's
  publish step is kept as "upload the contents of the build folder to a static host", with
  done defined by `governance/DEPLOY_GOVERNANCE.md`.
- The Claude Desktop preview tools (select element, draw on preview) are recorded as what the
  video used; the CLI equivalent is a local server plus screenshots. Neither is automated here.

## Acceptance

- `python tools/test_cdio_build.py` exit 0, with red drills (synthetic malformed criterion,
  removed kernel pointer, mirror drift, removed video step).
- `python tools/test_cdio.py`, `tools/test_cdio_focus.py`, `tools/test_cdio_mobile.py` exit 0.

## Rollback

Delete the dataset, the gate and this spec; restore `EXPECTED_DATASETS = 12` and remove the
CDIO-12 lines from the kernel and the three agents (repo + `~/.claude/agents/`).

## Phase 2 (Owner answer 3: after CDIO-12, item by item)

The four CDIO backlogs, in this order, each as its own spec + gate before any edit:

1. `vault/backlog/2026-10-31_github-issues-design-cdio.md` — TUA-X #4 first (visual 10/10,
   render QA, >=3 distinct PDP presentations; #6, #8, #10 defer to it), then #6, #8, #10, then
   #5, #7, #9 (UX without naming CDIO). Re-read each issue on GitHub before acting (the file
   says GitHub stays the source of truth). claude-power-pack #5 is not a design item: excluded.
2. `vault/backlog/2026-10-02_cdio-modern-saas-styles.md` — three SaaS styles into CDIO-06.
3. `vault/backlog/2026-10-21_cdio-brand-identity-logo-absorption.md` — brand identity & logos.
4. `vault/backlog/2026-10-30_cdio-21-design-resources-universal-absorption.md` — 21 resources,
   36 falsification gates; its D21-A01 reality scan runs first and records overlap with 1-3.

None of the four has been checked against the repo (D41: "Nothing below has been started or
checked against the repo"), so each starts with HR-PREMISE-001 verification.
