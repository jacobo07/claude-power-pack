---
name: validation-planes-do-not-transfer
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use before declaring a user-visible capability complete (page, screen, dialog, game view, generated UI), or when a structural, functional, truth or local-render gate is offered as proof of what users see. Name the reality level observed (CODE_VERIFIED, LOCAL_RENDER, PLATFORM_PREVIEW, LIVE), identify the build behind any screenshot, and test full, partial, minimal and absent content plus interaction states at several viewports. Core rule - a gate proves something only about the plane it observes."
---

# Validation Planes Do Not Transfer

A gate proves something about the plane it observes, and nothing about the planes it
does not. Structure, runtime, rendered surface, truth, readiness and production are
different claims. Passing one never passes another, however green the dashboard.

> **A user-visible capability is not complete until its rendered, interactive surface has
> been observed at the highest reality level reasonably available — and the claim names
> that level.**

Proportional by construction: this binds only what a person SEES or TOUCHES. A backend
subsystem owes no screenshot; a page, screen, dialog, game view or generated UI does.

## The planes, and what each cannot see

| plane | proves | blind to |
|---|---|---|
| structural | the artifact is well-formed and composable | anything rendered |
| functional | an interaction does what it is wired to do | how it looks, whether it competes |
| truth | every visible claim has a source | layout, interaction |
| rendered | a real engine laid it out at real viewports | the platform's own chrome, production data |
| readiness | the content and media were chosen, not defaulted | whether production honours it |
| production | what a real user sees | nothing — it is the reference |

Name the level in every claim: CODE_VERIFIED, LOCAL_RENDER, PLATFORM_PREVIEW, LIVE. A local
render is never reported as a platform verification.

## Rules

- **Before adjudicating a screenshot, identify the build.** A deployed artifact must say
  which code produced it (a manifest inside the artifact, a content digest of its source).
  "Which code is this?" answered by archaeology is its own defect.
- **Absence collapses.** When evidence removes content, the layout recomposes around what
  remains. A gated-out component that keeps its shell is a visible defect every structural
  gate passes.
- **A compound claim is only as true as each material subclaim.** Judge each part; report
  every unbacked part, not the first.
- **Merchant/operator-editable text is a claim surface too.** Generation-time gates never see
  what a person typed into an editor; only a gate over the artifact's own settings does.
- **Default is not approval.** "The platform has an image" is not "a person chose it".
  Readiness distinguishes previewable from launch-ready; it never blocks a preview.
- **Test the rendered states that matter:** full, partial, minimal and absent content; the
  interaction states (a sticky element entering, exiting, returning; unavailable items); at
  several viewports; with hidden elements proven unfocusable.
- **A real user's screenshot outranks green lower layers** for the plane it shows — it is
  direct evidence of the rendered surface. It is a symptom, never a root cause: reproduce,
  then fix the primitive, never the one store.

## DON'T

- **Don't call a rendering harness faithful until it resolves defaults the way the platform
  does.** An unset value that the harness treats differently (Undefined vs nil) invents
  elements the real platform never draws.
- **Don't assert absence on rendered text without checking what CSS did to it.** Transformed
  text makes a case-sensitive "not in" a permanent pass.
- **Don't let a control count only the items that carry your attribute.** A hardcoded item
  arrives without it.
- **Don't run a browser inside a test process that already owns an event loop**, and don't
  run one on a starved host; both read as a failing page. Probe in a subprocess, gate on
  headroom, and report INCONCLUSIVE.

## Source

Evidence and the full incident: `~/.claude/knowledge_vault/rules-evidence/validation-planes-do-not-transfer.md`.
