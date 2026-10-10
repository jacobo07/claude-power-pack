---
name: security-research
description: Risk-proportional security engineering using Google Mantis's method (vendored, pinned, prompts only). Use when a change adds or alters a public form, endpoint, server action, webhook, auth/session/permission path, file upload, payment step, outbound email/SMS, AI tool, or dependency; when abuse, spam or a vulnerability is reported; or when asked for a threat model, security review, vulnerability hunt or patch verification. Picks the cheapest level that answers (deterministic check, diff review, threat model, investigation, isolated reproduction) and refuses levels whose isolation does not exist yet. Core rule - a finding is a hypothesis until evidence lifts it, and nothing adversarial runs outside an isolated sandbox.
---

# Security Research (Mantis method, Claude Code carrier)

Source of method: Google Mantis, Apache-2.0, vendored at `vendor/google-mantis/`, pinned to
commit `2b3bbdcb` (2026-10-06). Integrity: `python tools/verify_mantis_vendor.py` must print
`MANTIS_VENDOR_PASS=5/5` before you rely on any file there. Decision record:
`vault/specs/mantis-security-research.md`.

Mantis itself says it is a demonstration, not a production tool, and that every finding needs
human verification. Treat the vendored files as **method**: read the one a stage needs (JIT),
follow its reasoning, and carry the work out with Claude Code tools. The upstream ADK harness
(Gemini/Vertex) is **not** used and **not** vendored.

## Pick the level (cheapest that can answer)

| Level | When | How | Status |
|---|---|---|---|
| L0 deterministic | every change touching the surfaces in the description | existing tests, lint, a grep gate, the project's guard tests | LIVE (per project) |
| L1 diff review | new or changed trust-boundary code | `pp-code-reviewer` + `mantis-review/SKILL.md` checklist on the diff only | LIVE |
| L2 threat model | new public surface, new integration, incident | `mantis-architecture` -> `mantis-threat-model` -> `mantis-advise`; output a surface table with an abuse class and a coverage state per row | LIVE (read-only) |
| L3 investigation | a concrete hypothesis worth hours | `mantis-plan` -> `mantis-researcher` -> `mantis-critic` -> `mantis-dedupe` -> `mantis-calibrate`; read-only on a snapshot, one bounded agent that writes findings to disk as it goes | LIVE (read-only) |
| L4 reproduce / patch / verify | a confirmed finding needing proof | `mantis-reproduce`, `mantis-patch`, `mantis-review` | **ABSENT** until an isolated sandbox exists (no network, no host secrets, disposable). Do not run exploit code on the dev host. |

Escalate only when the lower level leaves a specific, named question open. Budget per run:
state the token cap, the time cap and the stop condition before starting.

## Evidence ladder (never skip a rung in a claim)

observed in logs/production > reproduced in isolation > independently validated > correlated
with the real architecture > reasoned hypothesis > unverified model output. A model's conclusion
alone is a hypothesis. "No findings" means "no findings at the levels run", never "secure".

## Roles

The agent that proposes a patch is never the only one that certifies it: the verifier is a
different agent or a deterministic test that fails on the old code. Severe findings go to the
Owner before any external claim or any change to auth, permissions, privacy or infrastructure.

## Never

- Run Mantis stages against production, third-party systems, real credentials or real personal data.
- Send private code or personal data to an external model service without Owner approval.
- Re-sync `vendor/google-mantis` without review: update the pin, the MANIFEST and the decision record together.
- Block a user by language, country, name or email provider and call it abuse detection.

## Stage map (file to read for each stage)

architecture `mantis-architecture` · history `mantis-history` · threat model `mantis-threat-model` ·
advise `mantis-advise` · plan `mantis-plan` · research `mantis-researcher` · chain `mantis-chain` ·
critic `mantis-critic` · dedupe `mantis-dedupe` · calibrate `mantis-calibrate` · reproduce
`mantis-reproduce` (L4) · patch `mantis-patch` (L4) · review `mantis-review` · reflect
`mantis-reflect` · report `mantis-report` · summarize `mantis-summarize`. The `pipeline-adapter`,
`structural-index` and `meta-agent` files describe the ADK harness and are reference only.
