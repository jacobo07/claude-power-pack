---
name: ovo-audit
description: "Alias for /omni-verification-oracle-audit. OVO forensic audit — delta → Council → verdict → vault → gated push."
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Omni-Verification Oracle — Audit (alias)

Short-form invocation of `/omni-verification-oracle-audit`. Same phases, same artifacts, same verdict log consumed by the push-gate hook when the `.powerpack` sentinel is present.

## Phase A — Delta Forensics

!`python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py --project . --json`

Capture `delta_id`, `sha256_pre`, `changed[]`, `new[]`, `deleted[]`, `council_block`, `cold_start`. For each new file, identify the consumer (Mistake #38 gate — no consumer = verdict cap at B).

## OVO Protocol (load canonical source)

**Read** the protocol file now (use the Read tool): `~/.claude/skills/claude-power-pack/modules/oracle/ovo-protocol.md`. Internalize its 5 phases before continuing.

## Phase B — Adversarial Reasoning

Cross-check the delta against `~/.claude/skills/claude-power-pack/modules/governance-overlay/mistakes-registry.md` (Read it if needed). Emit ≤5-bullet adversarial findings block, or "no adversarial findings". Findings not addressed this turn cap the verdict at **B**.

## Phase C — Council of 5

!`python ~/.claude/skills/claude-power-pack/tools/council_verdict.py --render`

Reason through Contrarian / First Principles / Expansionist / Outsider / Executor with the Phase A delta and Phase B findings as context. No hedging.

## Phase D — Verdict Stamp

Emit `[COUNCIL_VERDICT: A+|A|B|REJECT]` per the rubric in `~/.claude/skills/claude-power-pack/modules/governance-overlay/council.md`, then persist:

```bash
python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py \
  --project . \
  --record-verdict <VERDICT> \
  --delta-id <DELTA_ID> \
  --council-text "<BLOCK>"
```

**On B or REJECT:** stop. Route to `~/.claude/skills/claude-power-pack/modules/governance-overlay/post-output.md § Rejection Recovery`.

## Phase E — Vault & Propose

On A/A+:

```bash
python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py --project . --vault-post
python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py --project . --report-md vault/audits/ovo_<ISO>_<VERDICT>.md
```

On A+ only: print (do not execute) the baseline elevation command, substituting the current project name for `<PROJECT>`:

```bash
python ~/.claude/skills/claude-power-pack/tools/baseline_ledger.py --elevate <PROJECT> --axis k_qa --baseline <N>
```

## Exit summary

Report path + verdict + `sha256_pre[:16] → sha256_post[:16]` + push-gate status (`active` if `.powerpack` sentinel present; otherwise `local-log only`) + elevation proposal (A+ only).
