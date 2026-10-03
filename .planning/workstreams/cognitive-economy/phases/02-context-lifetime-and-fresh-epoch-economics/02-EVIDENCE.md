# Phase 2 Evidence: Context lifetime and fresh-epoch economics

Commits `a686390a`, `2b8d5cec`. Full measurement: `vault/programs/cognitive-economy/evidence/D-E-context-lifetime.md`.

| Pillar | Terminal | Key number (D-W7) |
|---|---|---|
| D | MERGED_INTO_EXISTING_OWNER | economic trigger net [-0.05 %, +0.19 %] over 3 crossings |
| E | MERGED_INTO_EXISTING_OWNER | rotations net [-0.91 %, +2.41 %]; threshold-change ceiling <= 2.78 % < 3 % |

Verifier: `CEP_PILLAR_D=PASS`, `CEP_PILLAR_E=PASS` (fresh processes after 2b8d5cec).

Controls: positive b56ffff2 -> 4bb2abf7 found with ctx drop; negative 00343cb8 -> 0 crossings. Script exit is 1
unless both hold.

## Product Delta

- A re-runnable, zero-model-call instrument for context-boundary economics (`measure/context_lifetime.py`), with
  route-level breakdown, intervals instead of point savings, and controls built in.
- The owners of the economic trigger and the epoch rotation now hold numbers instead of "savings UNMEASURED".

## Intelligence Delta

- The economic trigger is barely live yet: 39 `would_rollover` verdicts became only 5 asks and 3 crossings in its
  first window. Almost all context-boundary traffic is still the 45 % wall.
- A crossing's realized saving is unknowable without its counterfactual (compaction or session end). The honest
  output is an interval [-rehydration, carry_saved - rehydration], which is wide for interactive crossings:
  [-2.13 %, +17.16 %].
- Rehydration is not small: median rotation ~0.6 M weighted, cheapest 0.28 M. That prices out more frequent
  rotation. The average mission session pays ~1.2 M of rent above its floor, but most of that sits in a few long
  sessions.
- Measurement trap found and fixed before it shipped: counting whole transcripts instead of in-window calls inflated
  the numerator against a fixed denominator (UB 19.81 % -> 19.29 %) and would have drifted as live sessions grew.
