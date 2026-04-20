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

Short-form invocation of `/omni-verification-oracle-audit`. Same behavior, same files produced, same verdict log consumed by the push-gate hook.

## Phase A — Delta Forensics

!`python tools/oracle_delta.py --project . --json`

Capture `delta_id`, `sha256_pre`, `changed[]`, `new[]`, `deleted[]`, `council_block`, `cold_start` from the JSON above. For each new file, identify the consumer (Mistake #38 gate).

## OVO Protocol (load canonical source)

@modules/oracle/ovo-protocol.md

## Phase B — Adversarial Reasoning

Cross-check delta against `./modules/governance-overlay/mistakes-registry.md`. Emit ≤5-bullet adversarial findings block, or "no adversarial findings". Findings not addressed this turn cap the verdict at **B**.

## Phase C — Council of 5

!`python tools/council_verdict.py --render --project claude-power-pack`

Reason through Contrarian / First Principles / Expansionist / Outsider / Executor with the Phase A delta and Phase B findings as context. No hedging.

## Phase D — Verdict Stamp

Emit `[COUNCIL_VERDICT: A+|A|B|REJECT]` per the rubric in `modules/governance-overlay/council.md`, then persist:

```bash
python tools/oracle_delta.py --project . \
  --record-verdict <VERDICT> \
  --delta-id <DELTA_ID> \
  --council-text "<BLOCK>"
```

**On B or REJECT:** stop. Route to `modules/governance-overlay/post-output.md § Rejection Recovery`.

## Phase E — Vault & Propose

On A/A+:

```bash
python tools/oracle_delta.py --project . --vault-post
python tools/oracle_delta.py --project . --report-md vault/audits/ovo_<ISO>_<VERDICT>.md
```

On A+ only: print (do not execute) the baseline elevation command:

```bash
python tools/baseline_ledger.py --elevate claude-power-pack --axis k_qa --baseline <N>
```

## Exit summary

Report path + verdict + `sha256_pre[:16] → sha256_post[:16]` + push-gate status + elevation proposal (A+ only).
