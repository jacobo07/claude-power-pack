# /cpp-osr — Observed System Reconstruction

Compare a build against an observed external system, and locate where two
executions first parted. Entry point: `tools/osr_audit.py`, which reaches
`modules/osr/` (model · compare · align · ordering).

## When this fires

- A build is claimed to reproduce an external reference and the claim needs an
  instrument rather than an opinion.
- A regression is visible on screen and the first *visible* difference is not
  trusted to be the first difference that happened.
- A system reaches a correct-looking terminal state and the prerequisite
  contracts that should have produced it have not been witnessed.

## What it will not do

`modules/osr/` acquires no evidence (**crawl_os** owns acquisition, provenance,
custody and authorization), stands up no graph (**graphify** owns the semantic
IR), publishes no fidelity number (**DAIF-03 §1.7** holds the metric authority
by Owner ruling — OSR emits observations its dimensions consume), investigates
no cause (**CRAIF** owns candidates, evidence and closure), promotes no finding
to a rule (**FD-03** routes, **rule_compiler** places) and assigns no epistemic
status (**ACIS** owns the ladder; OSR enforces only No-Autopromotion locally).

Full boundary: `vault/audits/usirc/BOUNDARY_CONTRACT.md`.

## Subcommands

```
python tools/osr_audit.py --types
python tools/osr_audit.py --model vault/osr/models/<target>.json
python tools/osr_audit.py --compare-raster REF.png BUILD.png
python tools/osr_audit.py --compare-geometry REF.json BUILD.json
python tools/osr_audit.py --compare-timeline REF.json BUILD.json
python tools/osr_audit.py --align REF.jsonl BUILD.jsonl --mission NAME
python tools/osr_audit.py --verify-order REQUIRED.json OBSERVED.json --terminal STATE
```

Add `--json` to any of them for machine-readable output.

## Reading the verdicts

Every instrument is three-valued: `MATCH`, `DIFF`, `UNMEASURED`. **`UNMEASURED`
exits non-zero.** An unmeasured dimension is a failed dimension — a gate that
passes because nothing could be measured is the quiet pass this estate has
sealed as a defect four separate times, and it is why `osa/gpu_eyes.py` reports
`visual_qa_passed=None` rather than `True`.

Aggregation is a **conjunction, never an average**. Any `DIFF` makes the report
`DIFF`; any `UNMEASURED` without a `DIFF` makes it `UNMEASURED`. Averaging is
the mechanism by which a fatal loss disappears into a good-looking number, and
DAIF-03 §1.2 prohibits it by name.

For `--align`, read `t1_internal` before `t2_observable`. A non-zero
`causal_distance` means the visible failure is downstream of where the
executions actually parted, and an investigation that starts at the symptom
starts in the wrong place.

## Done-gate

`python tools/test_osr.py` — 30 V-OSR-* gates, hermetic. Exit 0 required.

## Origin

`vault/audits/usirc/` — a 9-artifact ownership audit of a ~160-dataset proposal.
89 mechanisms were classified against a discovered denominator of 1,350 files;
77 already had an owner. These three did not, and one law was general enough to
keep. Everything else the proposal asked for already exists under another name.
