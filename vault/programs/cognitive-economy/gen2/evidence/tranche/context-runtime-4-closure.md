# context-runtime-4 closure (E0)

VERDICT: FAIL on spend (Owner: close as FAIL, no re-baseline).
- R1 PASS 592,688; R2 PASS 1,442,476 (workers 2,035,164)
- coordinator e6e0eca7: baseline 26189610 -> frozen final 30760307 = 4570697
- total 6605861 vs cap 3,500,000
- violations: UNDECIDED (no owned_units declared); E1 adds explicit NOT_APPLICABLE for future tranches, not retroactively here.
- Earlier reported 'spend PASS 3,461,950' was a live reading that kept growing (defect D1); superseded by this frozen value.
