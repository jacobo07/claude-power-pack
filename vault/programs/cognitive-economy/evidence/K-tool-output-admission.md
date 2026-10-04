# [K] Tool output admission -- KSR instrument replicated on the CPP corpus

Frozen rule: one replication on the CPP corpus with the same instrument; a firewall needs ONE class with >= 3 %
NOT_OBSERVED/IMMEDIATE (dead) carriage.

## Instrument

Campaign copy `vault/programs/cognitive-economy/measure/ksr_cpp/` of `vault/audits/ksr_archaeology/scripts/`
(`ctx_admission.py` + `ctx_dead.py`). It differs in exactly two places, both marked `CAMPAIGN COPY`: `CORPUS` points
at the CPP transcripts (`~/.claude/projects/C--Users-User--claude-skills-claude-power-pack`), and the manifest
admits only top-level session files written in or after D-W7 (mtime >= 2026-09-26T00:00:00Z). The original is
untouched (sha256 of `ctx_dead.py` before the copy: D7802967...; the copy was byte-identical before its edit).
Classes, pricing, probes, the dead-carriage definition and the decision rule are the original pre-registration.

Manifest committed BEFORE measuring (instrument rule S3): commit 36db0ff8, manifest sha256
`d729f28d1ebaf2da091033be4e1dafe812f04344c185e06b318ad3e5dc719469`, 99 files, population 79.

command: `cd vault/programs/cognitive-economy/measure/ksr_cpp && python ctx_dead.py --measure`
(result sha256 `5fd854d82ea1ea903a0451e6b06656d5279f7c4629f835fd54f07b7843f82c7a`; stdout
`ksr_cpp/ctx_dead_stdout.txt`; full output `ksr_cpp/ctx_dead_out.json`).

## Result (denominator: the corpus's own weighted total, 554.3 M; the KSR original used the same construction)

- Tool output carried: 10.28 % of weighted spend. Dead after last observable use: <= **6.93 %** (UPPER bound).
  Unmeasured: 2.44 %. Replaceable candidates: 0.53 %. Identical repeats: 0.00 %.
- Largest single class: `read:~/.claude skills/PP`, dead <= **2.67 %**. Next: `tool:Grep` 0.97 %,
  `ps:file content via shell` 0.43 %. **No class reaches 3 %.**
- Against D-W7 (weighted 3,325,101,725): the corpus is the CPP project's share of D-W7, 554.3 M ~ 16.7 %. All
  tool-output dead carriage <= 6.93 % x 554.3 M ~ 38.4 M ~ 1.16 % of D-W7 (upper bound).

## Controls (all valid)

- Planted used item detected: true. Planted unused item not observed: true.
- Self-vs-cross-session probe ratio per family: ps 249.6, tool 121.5, read 74.2 (all >= 2, valid).
- Token calibration (estimated resident tool tokens / actual context): 0.1288.

## Decision

FALSIFIED_OR_REJECTED_BY_EVIDENCE, as pre-registered. The CPP corpus has slightly more dead carriage than KSR
(6.93 % vs 6.34 %), but it is spread across classes like KSR's, and the largest class is 2.67 % < 3 %.

Caveat on class granularity: on CPP, reads of the repo itself fall in `read:~/.claude skills/PP`, because the repo
lives under `~/.claude/skills`. So that class is a union of many path families. Splitting it can only produce
smaller classes, so no subclass can exceed 2.67 % and the decision stands.

Displacement: not applicable (no lever built). Saving: none claimed.
