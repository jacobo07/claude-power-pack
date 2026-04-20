---
name: omni-verification-oracle-audit
description: "OVO forensic audit — delta → 5-advisor Council → verdict → atomic vault → gated push. Runs in the current repo; tooling is resolved to the Power-Pack install."
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Omni-Verification Oracle — Audit

Portable entry point for the Omni-Verification Oracle. Runs on **the current working directory** (`--project .`) but invokes the Power-Pack tooling via absolute paths so it works in any repo Owner opens.

**Push-gate scope:** the hook at `~/.claude/skills/claude-power-pack/modules/zero-crash/hooks/ovo-push-gate.js` only enforces in repos containing a `.powerpack` sentinel file at the repo root. Every other repo sees a no-op pass — verdicts are still logged locally (`vault/audits/verdicts.jsonl` in the current repo), they just don't gate `git push` yet.

## Phase A — Delta Forensics

!`python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py --project . --json`

From the JSON above, capture: `delta_id`, `sha256_pre`, `changed[]`, `new[]`, `deleted[]`, `council_block`, `cold_start`.

For each entry in `changed[]`, read its 1-line cached `summary` first — raw-read only if the summary is insufficient to judge blast radius. For each entry in `new[]`, identify the consumer: grep for imports or references. **If no consumer exists, flag Mistake #38 (Producer-Consumer Gap) immediately and cap the verdict at B.**

## OVO Protocol (load canonical source)

**Read** the protocol file now (use the Read tool): `~/.claude/skills/claude-power-pack/modules/oracle/ovo-protocol.md`. Internalize its 5 phases before continuing — every step below assumes you have it in context.

## Phase B — Adversarial Reasoning

Per Phase B of the protocol you just read. Cross-check the delta against the Mistakes Registry at `~/.claude/skills/claude-power-pack/modules/governance-overlay/mistakes-registry.md` (Read it if needed). Emit a **≤5-bullet adversarial findings block**, or state **"no adversarial findings"** explicitly.

Each finding: mistake number, file path, specific line-of-concern. Findings not addressed in the proposed output this turn cap the verdict at **B**.

## Phase C — Council of 5

!`python ~/.claude/skills/claude-power-pack/tools/council_verdict.py --render`

Reason through all 5 advisors (Contrarian, First Principles, Expansionist, Outsider, Executor) with the delta from Phase A and the adversarial findings from Phase B as explicit context. Fill each `<…>` placeholder with a concrete position — **no hedging**.

## Phase D — Verdict Stamp

Emit the banner per the rubric in `~/.claude/skills/claude-power-pack/modules/governance-overlay/council.md`:

- **A+** — all 5 approve, zero caveats.
- **A** — ≤1 minor caveat addressed in this response.
- **B** — ≥2 caveats or any major concern. **BLOCK.**
- **REJECT** — correctness bug / security hole / scaffold illusion. **BLOCK.**

Then persist the verdict (replace `<VERDICT>`, `<DELTA_ID>`; paste your Council block as `<BLOCK>`):

```bash
python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py \
  --project . \
  --record-verdict <VERDICT> \
  --delta-id <DELTA_ID> \
  --council-text "<BLOCK>"
```

**On B or REJECT:** stop here. Route to `~/.claude/skills/claude-power-pack/modules/governance-overlay/post-output.md § Rejection Recovery` (max 3 iterations per task).

## Phase E — Vault & Propose

On **A or A+**, run:

```bash
python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py --project . --vault-post
python ~/.claude/skills/claude-power-pack/tools/oracle_delta.py --project . --report-md vault/audits/ovo_<ISO>_<VERDICT>.md
```

`<ISO>` = current UTC timestamp (e.g. `date -u +%Y-%m-%dT%H-%M-%SZ`). `<VERDICT>` = `Aplus` or `A` (filesystem-safe).

**On A+ only,** surface the proposed baseline elevation for Owner review (detect the project name from `pwd`; substitute `<PROJECT>`):

```bash
python ~/.claude/skills/claude-power-pack/tools/baseline_ledger.py --elevate <PROJECT> --axis k_qa --baseline <N>
```

**Never auto-execute** — ledger writes are global state and require a human keystroke.

## Exit summary

Report back in ≤5 lines:
- Report path (from `--report-md`)
- Verdict stamp
- `sha256_pre[:16]` → `sha256_post[:16]`
- Push-gate status: `active, TTL 10 min` if `.powerpack` sentinel present; `local-log only (gate not scoped to this repo)` otherwise
- Proposed elevation command (A+ only) or `(none)`
