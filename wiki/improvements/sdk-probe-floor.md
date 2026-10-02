---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-internal-inventory]
status: IDEA
effort: S
graduated_to:
---

# Cheaper floor for one-shot `claude -p` calls

## Problem

516 of 981 main transcripts in 7 days made exactly one call; 508 of them came from the `sdk-cli`
entrypoint. Together ~$409, 4.9 % of estimated spend, ~$0.80 each
(`wiki/tools/token_economy_cuts2.2026-10-02.out` [B] @ `fd27800`). Each pays a cold first call
(first-call context p50 114k) to return a short answer ([[token-economy-levers]]).

## Who launches them

- Confirmed: deep-research runs each LLM step as `claude -p --disable-slash-commands
  --disallowed-tools "*"` with a pinned model; tools are off but the project prefix (CLAUDE.md,
  rules, skills listing, hooks) still loads (`modules/deep-research/deep_research.py:795-805` @
  `3b07419`). Sample titles match its prompt ("Decompose the research topic below ...", `:113`).
- Unattributed: "Reply with exactly: PROBE-OK" and "A fact is ..." probes. A grep for `PROBE-OK`
  over `~/.claude` `*.py/js/ps1` found nothing; the launcher may live in another repo.

## Evidence for a cheaper floor

A one-call probe measured 91.3k in an empty directory vs 111.6k in this repo
([[2026-10-02-state-centric-reality-scan]]): running from a neutral cwd removes ~20k per call
without any flag. `--bare` cannot run on the subscription login (same source).

## Proposed steps

1. Run deep-research's `claude -p` child from a neutral temp cwd; re-measure first-call tokens.
2. Attribute the remaining probe titles to their launchers.
3. Check whether the probes need Claude Code at all; the API layer has no Claude Code floor but
   bills an API key, not the subscription.
