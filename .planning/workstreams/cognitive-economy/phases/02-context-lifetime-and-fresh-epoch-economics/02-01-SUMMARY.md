---
phase: 02-context-lifetime-and-fresh-epoch-economics
plan: 01
status: complete
commits: [a686390a, 2b8d5cec]
requirements: [CE-D, CE-E]
---

# Plan 02-01 Summary

- `measure/context_lifetime.py` discovers 127 interactive and 52 mission crossings in D-W7 and measures each from
  transcripts (window-bounded calls). It runs reproducibly: sha256 `672ad45d...` on two runs.
- D: economic trigger 3 crossings, net [-0.05 %, +0.19 %] of D-W7; wall route carries 124/127. KSR <= 6.34 % stays
  an upper bound (different denominator, magnitudes ordered only).
- E: mission rotations net [-0.91 %, +2.41 %]; any threshold change <= 2.78 % (lowered) / <= 0.91 % (raised), so
  no proposal under the 3 % rule.
- Controls: positive pair found with a drop; negative session reports 0 crossings.
- Fix commit 2b8d5cec: the word "later" in E's reason tripped the verifier's deferral-prose clause (L7).
