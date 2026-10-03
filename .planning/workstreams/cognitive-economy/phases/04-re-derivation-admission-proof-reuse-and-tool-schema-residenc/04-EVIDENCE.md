# Phase 4 Evidence: Re-derivation, admission, proof reuse and tool-schema residency

Full measurements: `vault/programs/cognitive-economy/evidence/K-tool-output-admission.md`,
`vault/programs/cognitive-economy/evidence/F-G-P-C-carriage.md`.

| Pillar | Terminal | Key number |
|---|---|---|
| K | FALSIFIED_OR_REJECTED_BY_EVIDENCE | largest dead class 2.67 % (CPP corpus, KSR construction) < 3 % |
| F | FALSIFIED_OR_REJECTED_BY_EVIDENCE | sibling identical re-reads 1.8793 % of D-W7 weighted < 3 % |
| G | FALSIFIED_OR_REJECTED_BY_EVIDENCE | decided from F's identity boundary; no recurrence >= 3 % |
| P | FALSIFIED_OR_REJECTED_BY_EVIDENCE | verification carriage 0.5007 % < 3 % |
| C (tools) | measured here, terminal in phase 7 | ToolSearch schema carriage 0.0020 % < 3 % |

Verifier (epoch 4 re-run): `CEP_PILLAR_F/G/K/P/C=PASS`.

## Product Delta

- `measure/carriage.py`: a zero-model-call carriage instrument over transcripts that prices any tool-output class on
  D-W7 weighted; reusable for any later "is X worth a slice" question.

## Intelligence Delta

- Four pre-registered levers (firewall, sibling memoization, CSE, proof reuse) fail the 3 % rule on measurement.
  The carriage that matters is generic Read output (21.02 % of D-W7), not any single reusable class.
