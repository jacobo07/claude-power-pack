STATUS: DONE
COMMITS: 700b5c21
Packet sha256 245e1f1dee6c verified.
Gate: python3 -I tools/test_a5_u9.py -> A5_U9_PASS=12/12 (refusals paired with admitting controls).
Holdouts: cognitive-economy-e1 (CE mission; 25 jsonl, ~26MB, 580 calls); ql-quickie (other product; 14 jsonl, ~24MB, 685 calls). Both present.
Best combined f: DWS -89.6%, e1 -75.7%, quickie -85.8% (A/holdout/*/COUNTERFACTUAL.md, A/data/counterfactual.json).
PROMOTABLE: a slim floor, b1/b2/b3 rotation, f combined. DWS_LOCAL: c read-once, d STATE projection (holdouts 3.0/0.0%), e poll->event (DWS 9.3% < 10%).
Caveats: holdouts small; rotation capsule fidelity not modelled; labels are proxies. See A/HOLDOUT.md.
Tool added: tools/a5_holdout.py (promotion rule + table). Deviations: none. Model calls: none from code.
Note: working tree had unrelated pre-existing dirty files; committed by pathspec only.
HANDOFF NOTE: rotation and slim floor generalise across hosts' corpora; read-once/STATE/poll stay DWS-local.
