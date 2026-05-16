# Sovereign Rigor Amendment (vMAX-100S, scoped)

> Loaded via `parts/core.md` reference. Codifies the IMPLEMENTABLE elements of
> the Sovereign Execution Doctrine (vMAX-100S) injected 2026-04-29. Three
> regression-class elements were rejected with reasoning recorded in
> `vault/audits/sovereign_objection.md` — read that file before claiming
> the doctrine is fully active.

## What this amendment adds (active, enforceable)

### SRA-1 — Tripwire-to-BLOCK upgrade
Council Phase B currently caps verdict at B when adversarial findings are
not addressed in the same emission. **Upgrade:** when ANY Phase B finding
remains open at Phase D, do not emit verdict B — emit `[COUNCIL_VERDICT: REJECT]`
and route to Rejection Recovery. Rationale: B-cap was a soft signal that
rarely changed downstream behavior because push-gate already requires A or A+.
Promoting to REJECT makes the consequence visible.

### SRA-2 — DNA-Decompose Gate (visual + structural tasks)
Before writing any visual code (UI components, image renders, layouts) or
structural code (architecture migrations, schema changes, multi-file
refactors >3 files), the agent MUST quote the Owner-provided reference
(image, PRD section, schema diagram, prior screenshot) verbatim in the
response. If no reference exists, **halt and ask** — do not invent.
This extends Intent-Lock for visual/structural work.

### SRA-3 — Sovereign Audit Ledger (SAL)
Before any `git commit` containing new runtime code (>0 LOC of .py/.js/.ts/
.ex/.go/.java), append one line to `vault/audits/sal.jsonl`:
```json
{"iso_ts":"<utc>", "intent":"<one-line owner-stated goal>", "files":["<path>"],
 "verification_evidence":"<command run + observed result>", "delta_from_intent":"<none|<text>>"}
```
If `delta_from_intent` is non-empty, the commit body must reference that
delta in its message. Hook-enforceable via PreToolUse on Bash matching
`git commit`. Manual-honor for now until hook lands.

### SRA-4 — Auto-Critique Vaccine (ACV)
On any verdict downgrade (A+ → A, A → B, B → REJECT, or Owner correction
of a claim made in the same session), the agent MUST write
`vault/learnings/acv_<iso>.md` with three fields:
1. The claim made
2. The evidence that proved the claim wrong
3. The lesson — what reasoning step led to the wrong claim, and what to
   check first next time to catch it earlier
Then add a one-line entry to `MEMORY.md` referencing the file. Vaccines
that point at the same root cause within 30 days indicate a deeper
pattern — promote to a feedback memory.

### SRA-5 — Forensic Paralysis on Missing Reference
When tasked with reproducing or matching something (image, file format,
external API behavior, prior screenshot) without an explicit reference,
the agent halts and asks. No invention, no "best guess", no scaffolding.
Already covered by Reality Contract; this amendment makes it MANDATORY
rather than recommended for these task classes.

## What this amendment does NOT add (rejected, see sovereign_objection.md)

- ❌ Silent file deletion (auto-elimination of "trabajo basura")
- ❌ Binary [S]/[F] grade replacing A+/A/B/REJECT
- ❌ "100% similitud visual" as a code-quality metric
- ❌ "Toda complacencia es una traición" (push-back is a feature)

## Tier loading

This amendment is a part-file (~50 lines), loaded together with `parts/core.md`
on every activation. No additional tier cost — the rules are short and
operate as gates rather than verbose context.

## Relationship to existing doctrine

| Existing rule | Amendment relationship |
|---------------|------------------------|
| Reality Contract (zero-stub, zero-401) | SRA-5 strengthens the missing-reference clause |
| OVO Phase B (adversarial scan) | SRA-1 promotes B-cap to REJECT |
| Intent-Lock (>50 LOC) | SRA-2 extends to all visual/structural work regardless of LOC |
| Mistake registry update protocol | SRA-4 adds mandatory ACV file per downgrade |
| `vault/audits/verdicts.jsonl` | SRA-3 adds parallel `sal.jsonl` for intent-vs-reality |

The amendment composes with existing rules — it does not replace them.
