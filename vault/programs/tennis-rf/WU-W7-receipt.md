# W7 receipt
Status: DONE

Commits: PP only (evidence/w7/prep_corpus.py, evidence/w7/families.py, measure/families.json, measure/features.json, KNOWLEDGE.md, this receipt). Zero model calls on functions, zero GEX44 jobs, zero compiles, no code in wt_tennis_rf.
Commands: `python -I evidence/w7/prep_corpus.py`; factory-venv `m2c_producer.py` over all 1,797 (M2C_DONE rows=1797, no compile); `python -I evidence/w7/families.py measure` (deterministic: second clustering identical).

Method (families.json `summary.method`): edge iff shape view S (loose hash equal, or >=12 insns, size ratio >=0.85, mnemonic cosine >=0.95) AND (call-context C: callee-set Jaccard >=0.5, or data-context D: lbl object Jaccard >=0.5, or X: full-body identical incl. numbers, <=16 insns). Families = connected components; singleton = family of one.

- PROVEN: 1,797 functions -> 1,255 families (1,114 singletons, 87 of size 2, 38 of 3-5, 11 of 6-20, 5 of >20; largest 136, 36, 35, 23, 22). Recurrence (functions in families >=3) = 509 (28.3 %). Novelty density = 1,255 / 1,797 = 0.698.
- PROVEN red control: permuting call/data/full-body features across functions -> 1,732 families, 60 fns in >=3 (edges 11,594 -> 148); permuting shape -> 1,742 families, 40 fns in >=3 (edges 162). Structure collapses to ~singletons, so the clusters are not an artefact of size/unit.
- m2c over all 1,797: 1,613 L1, 92 M2C_ERROR, 92 M2C_FAILED; 172 are L1 with zero `?` and zero unk fields.
- Deterministic-eligible = exact Resort shape AND SRC PROVEN donor = 167 (9.3 %). Via "m2c-clean + family with a W5-verified member" = 0 (W5a/W5b verified 0). Model-needed = 1,630 (90.7 %). Ceiling if every m2c-clean were verified later: 194 (10.8 %). Correction to W3 receipt: its "179" is 167 exact + 12 loose-only donors; only the 167 are counted here.
- W5 cross-check (18 drawn fns): 4 sit in families >=2 (sizes 5, 36, 35, 23); in all 4 the drawn fn's unresolved-type count lies inside its mates' range (0..0, 1..1, 3..3, 3..5) -> consistent with the clustering (VALIDATES, weakly: m2c text property only, no verdicts exist). 14 of 18 are singletons, so W5's sampling covered novelty-heavy functions; no W5 result contradicts a family. NOT_PROVEN that family-mates share a source fix (needs a verdict oracle).
- Scope A closure: 50 getter callers (step3) span 48 families. One level of argument propagation (controller-tainted r3-r10 at a direct bl, same linear tracker; synthetic positive found, synthetic negative not) finds 0 extra callees, so closure = 50 functions / 48 families; none is donor-proven eligible, none m2c-clean. Upper bound (all 160 Tennis-candidate direct callees incl. the 50) = 160 fns / 145 families. Limits: linear tracker, virtual calls (bctrl) and non-direct flows invisible (floors, as step3).
- UNKNOWN: cost per family; whether clusters transfer fixes (no verified member anywhere).
- Next unit must know: Tennis is ~70 % novel by this clustering and only ~9 % deterministic; price Scope A as ~48-145 families, mostly singletons. Calls ~25.
