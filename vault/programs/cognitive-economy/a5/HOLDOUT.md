# HOLDOUT (ce-a5 U9)

Rule: PROMOTABLE only if gain >= 10% on DWS AND >= 5% on at least one holdout; else DWS_LOCAL. Gain = replay delta from tools/a5_counterfactual.py (assumptions A1-A11 of COUNTERFACTUAL.md; replay, not realized savings).

## Holdouts (read-only, /home/kobii/.claude/projects/)
- CPP/CE mission: -home-kobii-missions-cognitive-economy-e1 — 25 jsonl, ~26 MB, 580 calls, actual 101,141,272 processed tokens.
- Other product: -home-kobii-missions-ql-quickie (quickie project) — 14 jsonl, ~24 MB, 685 calls, actual 147,822,276 processed tokens.
Both present; no DEFER_EXTERNAL_DEPENDENCY. Outputs: A/holdout/<name>/ (TRACE-REPORT.md, COUNTERFACTUAL.md, data/).

## Verdicts
| policy | DWS | cognitive-economy-e1 | ql-quickie | verdict |
|---|---|---|---|---|
| a slim floor 13,507 | 39.7% | 42.4% | 30.5% | PROMOTABLE |
| b1 rotate N=12 | 50.0% | 36.6% | 57.1% | PROMOTABLE |
| b2 rotate N=20 | 46.4% | 29.2% | 54.0% | PROMOTABLE |
| b3 rotate N=40 | 38.6% | 20.5% | 46.3% | PROMOTABLE |
| c read-once | 8.1% | 0.3% | 1.5% | DWS_LOCAL |
| d STATE projection 8KB | 11.6% | 3.0% | 0.0% | DWS_LOCAL |
| e poll->event | 9.3% | 8.7% | 11.0% | DWS_LOCAL |
| f a+b20+c+d+e | 89.6% | 75.7% | 85.8% | PROMOTABLE |

Promotable: a (slim floor), b1/b2/b3 (rotation), f (combined). DWS_LOCAL: c (DWS 8.1%, holdouts <2%), d (DWS 11.6% but holdouts 3.0%/0.0%), e (DWS 9.3% < 10%, though holdouts 8.7%/11.0%).

## Caveats
- Holdouts are small (580/685 calls vs 10,985) and contain subagent/short sessions; session mix differs from DWS. Slim floor gains depend on measured first-call ctx vs 13,507 per session.
- Rotation gain still ignores capsule fidelity/re-derivation (U2 key unknown); f remains LOW confidence.
- Holdout corpora include the live projects dir at run time; sizes may grow.
