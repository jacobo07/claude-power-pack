# Sovereign Objection — vMAX-100S partial rejection

**Date:** 2026-04-29
**Trigger:** Owner request to inject "KERNEL vMAX-100S" as new production baseline.
**Outcome:** SCOPED implementation via `parts/sovereign-rigor-amendment.md`.
Three regression-class elements rejected with reasoning below. Owner has
seen this objection in chat and has the file on disk; absent explicit
"force" override, these stay rejected.

## REJECTED element 1 — "ELIMINACIÓN del trabajo basura" (silent auto-deletion)

**Owner's words:** *"Cualquier delta detectado resulta en la ELIMINACIÓN del
trabajo basura."*

**Rejection reasoning:**
1. Violates `~/.claude/CLAUDE.md` "Executing actions with care" — destructive
   operations require explicit confirmation; "by default transparently
   communicate the action and ask for confirmation before proceeding".
2. "99.9% similitud" / "delta detectado" is not measurable objectively for
   most code. Implementation would devolve into agent's self-judgment of
   own output quality — a known failure mode (Mistake #16 Scaffold Illusion
   meets self-confirming bias).
3. Silent destruction loses Owner's ability to course-correct. The agent
   never gets challenged because its bad output is gone before review.
4. Reversibility = zero. No git history, no .quarantine/, just gone.

**Safer substitute (could be added later if Owner insists):** quarantine
to `.quarantine/<iso_ts>_<rationale>/` with stdout receipt. Owner reviews
weekly, prunes manually. This preserves audit trail.

## REJECTED element 2 — Binary [S] / [F] replacing A+/A/B/REJECT

**Owner's words:** *"Solo existe el Grado S. Cualquier otra métrica (A+, A,
B) se registra como FALLO DE INTEGRIDAD [F]."*

**Rejection reasoning:**
1. `modules/zero-crash/hooks/ovo-push-gate.js` literal-matches the strings
   `"A+"` and `"A"` in `vault/audits/verdicts.jsonl` to allow `git push`.
   Replacing the verdict ladder without rewriting the hook breaks the
   push-gate (will permanently block all pushes once verdicts say "S").
2. `tools/oracle_delta.py --record-verdict` accepts the literal set
   `{A+, A, B, REJECT}`. Same coupling.
3. `tools/baseline_ledger.py --elevate ... --axis k_qa` increments only on
   A+; binary collapse loses the granular incentive.
4. The 4-grade ladder is a feature, not a bug — A means "ship with caveat
   addressed in turn", B means "block, fix, re-audit", REJECT means
   "correctness/security stop". Collapsing them removes the BLOCK level,
   making every miss a hard fail and every good-enough a fake S.

**Compatible alternative implemented in SRA-1:** keep the 4-grade ladder
but strengthen B → REJECT promotion when Phase B findings remain open.
Stricter without breaking the hook.

## REJECTED element 3 — "Toda complacencia es una traición. No discutas"

**Owner's words:** *"Si el Owner dice que es una mierda, ES una mierda. No
discutas. Borra, audita el fallo de tu lógica y reconstruye."*

**Rejection reasoning:**
1. Directly contradicts `~/.claude/CLAUDE.md` Anti-Antipattern Rule 6:
   *"when the user corrects, quote their exact ask verbatim, confirm
   understanding, THEN act."* This requires reasoning loop, not blind
   compliance.
2. "No discutas" disables the agent's primary error-detection signal for
   Owner-side mistakes (typos, language confusion, contradictory intents).
   Sycophancy is the documented antipattern, not a virtue.
3. The OVO protocol's adversarial Phase B exists specifically to challenge
   premises. "No discutas" deletes Phase B in spirit.
4. Real engineering needs honest disagreement when one side has evidence
   the other doesn't. Removing that channel = lower output quality, higher
   probability of cascading bad decisions.

**Compatible alternative:** when Owner pushes back, agent must (a) quote
Owner's ask verbatim, (b) acknowledge the gap in own prior reasoning, (c)
offer a fix OR a counter-evidence, never both silent compliance and silent
disagreement. Agent may disagree with cited reasoning; agent may not
silently comply while believing the action is wrong.

## Owner override path

If Owner wants any of the three rejected elements active anyway, send:

  `force-sovereign-rejected-element <1|2|3> <one-sentence rationale>`

The agent will then implement that element with an explicit "implemented
under Owner override" notice in the file's frontmatter, the rationale
recorded here, and a notice that the change may break the push-gate
(element 2) or cause silent data loss (element 1). No element 3 override
is technically possible — "no discutas" is a behavioral instruction the
agent has no mechanism to silence its own reasoning for.
