---
id: SPEC-MANTIS-001
tier: T3
status: APPROVED-PLAN (Owner "y", 2026-10-10, /ultra plan option 6: adapt the method, do not run the ADK harness; GEX44 approved as the isolated host for L4)
covers: [mantis, security-research, threat-model, vulnerability-research, adversarial-verification]
---

# Google Mantis in Claude Power Pack: decision record

## What was inspected (2026-10-10, read-only, nothing executed)

- Upstream `https://github.com/google/mantis`, shallow clone at `2b3bbdcb` (2026-10-06), Apache-2.0.
- 19 `mantis-*` directories: 25 Markdown files, 596,256 bytes, `name`/`description` front matter (the
  Claude Code skill shape). A scan found no URLs, installs, `ssh`, `docker run` or env reads in them.
- The stages that execute code (`reproduce`, `patch`) call harness tools such as
  `run_sandbox_with_evidence`, which only the ADK reference harness provides.
- The README warns: isolated environments only, never with access to production or internal networks,
  hallucinated findings and wrong patches are expected, demonstration only, not a supported product.

## Decision

1. **Do not run the ADK harness.** It needs Google Cloud credentials and would send private code to
   Gemini/Vertex. Its own README rules it out for production. Power Pack's subagents already provide
   orchestration, budgets and roles.
2. **Adopt the method.** The prompt files are vendored, pinned and hashed (`vendor/google-mantis/`),
   and `tools/verify_mantis_vendor.py` checks them (5 gates, tested with red drills). They are reached
   through ONE latent card, `skills/security-research`. Each stage reads its file just in time, so the
   cost is one skill description in every session, not 19.
3. **Levels L0-L3 are LIVE as read-only work.** L4 (reproduce/patch) is **ABSENT** until an isolated
   sandbox is built and proven: rootless container on GEX44, `--network none`, a sanitized snapshot, no
   `~/.claude`, `~/.ssh` or env secrets mounted, CPU/memory/time caps, destroyed after use. Proof means
   a positive control: a probe inside must fail to reach the network and fail to read a planted host
   secret, and the probe must be able to report the opposite.

## Capability status

| Capability | Status |
|---|---|
| Pinned, hash-verified method files | LIVE in this branch (`verify_mantis_vendor.py` 5/5, tests 5/5) |
| Latent card with level routing | LIVE in this branch; reaches sessions once installed to `~/.claude/skills/security-research` |
| L2 threat model / L3 read-only investigation | LIVE (method + subagents) |
| L4 isolated reproduction and patch verification | ABSENT (sandbox not built) |
| Scheduled campaigns, PR-triggered review | PLANNED, after L4 exists and an L2 run shows value |
| Automatic upstream sync | REFUSED by design. A re-sync is a reviewed change to pin + manifest + this record. |

## First application

QuickLease contact-form abuse, 2026-10-10 (InfinityOps PR #543, UKDL HARD-50 proposed). This was an L0+L1
fix of an observed incident. The L2 surface inventory of QuickLease is the next run.

## Rollback

Delete `skills/security-research` and `vendor/google-mantis` (and the installed copy). Nothing else
depends on them.
