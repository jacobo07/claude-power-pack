# WU-D3 receipt
Status: DONE
Done-check: `python -I tools/test_d3.py <d3>` on GEX44 -> TEST_D3 OK, exit 0 (11 checks V-D3-*; output `evidence/d28/d3/test_d3.txt`).
Evidence: PP `evidence/d28/d3/` (residuals.jsonl 1,797 rows, census.json, autonomy.json, tools/residual.py, tools/test_d3.py). GEX44 M/out/d28/d3/.

## Results
1. Residual compiler v0 (`tools/residual.py`): per fn unresolved_vars (untyped field offsets, helper/field/self-sig/qtype/m2c keys from D1d blockers),
   certified (header, VALID idioms, motif cover, proof family), conflicts, obligations, expected_unlock (sole-blocker key, UNVERIFIED structural
   prediction). Residual size is `null` (UNKNOWN) for 215 functions (m2c emitted no code, or not clean with nothing named): never counted as 0.
2. Census: size quantiles over the 1,582 known sizes: min 0, p25 1, median 5, p75 12, p90 21, max 188. Empty-residual-not-clean contradictions: 0.
   31 functions are not clean with lint codes but no blocker key (= D1d `unexplained_not_clean`; named in census.json, distance 5, UNKNOWN).
   One other contradiction, explained: fn_80252F34 lint-clean but compile FAILED (lint checks types only; D2 admission_gap, NULL undeclared) -> distance 2.
3. Distance histogram (rule in residual.py `distance()`): 0:12, 1:263, 2:1307, 3:92, 4:92, 5:31 (sum 1,797). The 22 W12 sent functions agree:
   12 MATCH=0, 9 PARTIAL=1, FAIL=2; the 2 EXCLUDED are 2 and 5.
4. Effective remaining work, MEASURED rates only: class 0 = 12 done. Class 1 (263): W12 12/22 (Wilson95 0.347-0.731) -> 91-192 expected MATCH with
   0 model calls, 120 (point) need follow-up; follow-up cost UNKNOWN (only near-match compression 5 classes/9 PARTIAL is measured). Classes 2-5
   (1,522 fns): rate UNKNOWN, token range [0, UNKNOWN]. W12 aggregate 3,453,372 tokens/22 fns = 156,971 is a ceiling, NOT a rate
   (whole session incl. prep); priced lower bound 0, upper bound UNKNOWN. 275 functions priced, 1,522 unpriced.
5. Red control: permuting fn->blocker sets across functions gives clean fns a foreign blocker set (min 215, mean 230.3 of 20 perms) vs real 0: PROVEN.

## Plan delta
MDG 9/17/18 (residual census, distance-to-autonomy, effective remaining work): 1,797 rows; histogram 12/263/1307/92/92/31; 1,522 of 1,797
functions have no measured cost rate, so effective remaining work in tokens is UNKNOWN above class 1. Largest class (1,307) is pure fact-gap
(prototype/field facts), consistent with D2: the lever is the header fact table.

## Commands
GEX44 M/out/d28: `python -I tools/residual.py /home/kobii/missions/tennis-w11/out /home/kobii/missions/tennis-w11/out/d28/d3` then `python -I tools/test_d3.py .../d3`.
Inputs: d28/d1d/{facts.jsonl,blockers.json,factor.json,hypotheses.json,idioms_status.json}, W12 evidence/w12/measure/records.jsonl. No model calls on functions.
