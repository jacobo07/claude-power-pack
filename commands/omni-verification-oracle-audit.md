---
name: omni-verification-oracle-audit
description: "OVO forensic audit — delta → 5-advisor Council → verdict → atomic vault → gated push. Use before merging or pushing significant changes."
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Omni-Verification Oracle — Audit

Forensic integrity gate. Runs the 5-phase OVO protocol end-to-end, records a signed verdict to `vault/audits/verdicts.jsonl`, and gates subsequent `git push` / deploy via the push-gate hook.

**Note on router priority:** Claude Code discovers slash commands by filename; there is no "priority trigger" mechanism. The substitute for priority is the verdict log — once a fresh A+/A verdict is persisted, the PreToolUse push-gate hook (power-pack-scoped) enforces it for subsequent push attempts in this repo.

## Phase A — Delta Forensics

!`python tools/oracle_delta.py --project . --json`

From the JSON above, capture:
- `delta_id`
- `sha256_pre`
- `changed[]`, `new[]`, `deleted[]`
- `council_block`
- `cold_start`

Then follow Phase A of the protocol below: for each changed file, read its cached `summary`; raw-read only if the summary is insufficient. For each new file, identify the consumer — if none exists, flag **Mistake #38 (Producer-Consumer Gap)** and the verdict cannot exceed **B**.

## OVO Protocol (load canonical source)

@modules/oracle/ovo-protocol.md

## Phase B — Adversarial Reasoning

Per Phase B of the protocol. Cross-check the delta against `./modules/governance-overlay/mistakes-registry.md`. Emit a **≤5-bullet adversarial findings block**, or state **"no adversarial findings"** explicitly.

Each finding: mistake number, file path, specific line-of-concern.

If any finding cannot be addressed in the proposed output this turn, the verdict ceiling is **B**.

## Phase C — Council of 5

!`python tools/council_verdict.py --render --project claude-power-pack`

Reason through all 5 advisors (Contrarian, First Principles, Expansionist, Outsider, Executor) with the delta from Phase A and the adversarial findings from Phase B as explicit context. Fill each `<…>` placeholder in the template with a concrete position — **no hedging**.

## Phase D — Verdict Stamp

Emit the banner per the rubric in `modules/governance-overlay/council.md`:

- **A+** — all 5 approve, zero caveats. Ship.
- **A** — ≤1 minor caveat addressed in this response. Ship.
- **B** — ≥2 caveats or any major concern. **BLOCK.**
- **REJECT** — correctness bug / security hole / scaffold illusion. **BLOCK.**

Then persist the verdict (replace `<VERDICT>` and `<DELTA_ID>`; paste your full Council block as `<BLOCK>`):

```bash
python tools/oracle_delta.py --project . \
  --record-verdict <VERDICT> \
  --delta-id <DELTA_ID> \
  --council-text "<BLOCK>"
```

**On B or REJECT:** stop here. Route to `modules/governance-overlay/post-output.md § Rejection Recovery` (max 3 iterations per task).

## Phase E — Vault & Propose

On **A or A+**, run:

```bash
python tools/oracle_delta.py --project . --vault-post
python tools/oracle_delta.py --project . --report-md vault/audits/ovo_<ISO>_<VERDICT>.md
```

`<ISO>` = current UTC timestamp like `2026-04-20T14-30-00Z` (use `date -u +%Y-%m-%dT%H-%M-%SZ`). `<VERDICT>` = `Aplus` or `A` (filesystem-safe).

**On A+ only**, print the proposed baseline elevation command for Owner review:

```bash
python tools/baseline_ledger.py --elevate claude-power-pack --axis k_qa --baseline <N>
```

where `<N>` is the current axis value plus the verdict delta you agreed with Owner. **Never auto-execute** — ledger writes are global state and require a human keystroke.

## Exit summary

Report back in ≤5 lines:
- Report path (from `--report-md`)
- Verdict stamp
- `sha256_pre[:16]` → `sha256_post[:16]`
- Push-gate status: "active, TTL 10 min" (on A+/A) or "blocked until next PASS" (on B/REJECT)
- Proposed elevation command (A+ only) or `(none)`
