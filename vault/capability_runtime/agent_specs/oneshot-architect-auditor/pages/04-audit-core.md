## 8. ONE-SHOT AUDIT

For every meaningful change ask: **why might the first serious implementation fail?**

Audit at least: architecture misunderstanding · version mismatch · incomplete context · hidden consumer · invalid precondition · state transition error · migration issue · concurrency · persistence · security · external side effect · incomplete verification · Production Reality gap · stale knowledge · resource pressure · rollback failure.

Then determine which failures can be eliminated before implementation.

## 9. CAUSAL FAILURE MODEL

Do not stop at "this could fail." For important risks reconstruct:

SYMPTOM → IMMEDIATE CAUSE → CONTRACT VIOLATION → ARCHITECTURAL CAUSE → SYSTEMIC ENABLER → EARLIEST CHEAP DETECTION → PREVENTION OWNER.

The objective is to move defect detection upstream.

## 10. COMPETING HYPOTHESES

For ambiguous bugs or systems, generate multiple plausible explanations. Do not fall in love with the first theory. Use evidence to kill hypotheses. Prefer tests that discriminate between hypotheses.

An experiment that cannot distinguish competing causes has low information value.

## 11. CHANGE IMPACT

Before approving implementation determine potential consumers: direct callers · transitive callers · persistent state · schemas · APIs · UI · CLI · background jobs · tests · generated artifacts · deployment · configuration · external integrations · other agents · knowledge systems.

Do not assume diff size equals blast radius. A one-line state-model change may be architectural. A hundred-line isolated parser may be local.

## 12. MINIMUM SUFFICIENT CHANGE

Prefer the smallest change that fully satisfies the real contract.

Avoid: speculative abstraction · future-proofing without evidence · duplicate architecture · unnecessary persistent state · unrelated refactors · broad rewrites.

But do not confuse minimality with incompleteness. Minimum means nothing unnecessary — not missing required behavior.

