[L] -> modules/cognitive_os/co_12_telemetry.py

Handoff of skill-capability pillar [L] (CO-12 + Context Compiler), predicted DEFERRED_STRONGER_OWNER.

Frozen rule (ledger `frozen.pillars`):

> the Context Compiler is ABSENT; it is deferred to the cognitive-economy program with a handoff; CO-12 is written only through record_signal

Frozen owners: `modules/cognitive_os/co_12_telemetry.py`, `vault/programs/cognitive-economy/ledger.json`.

- measured_at_commit: 1e32ae7a3a6404070cb8e5ff6fa9c983ace8c5d6
- freeze: 217d72b5944a664fbc0baa1060c04617ff10f481
- host: kobicraft-gex44
- plane: committed blobs at measured_at_commit (git grep / cat-file / diff / archive), never the working tree
- produced by: python3 tools/skill_handoffs.py --write L
- claim: PASS absence=PASS control=PASS writer=PASS

## Commands and observed output

| command | observed |
|---|---|
| `git ls-tree -r --name-only 1e32ae7a \| grep -icE 'context[_-]?compiler'` | 0 of 4294 tracked paths |
| `git grep -nIE 'class ContextCompiler\|def compile_context\|context_compiler' 1e32ae7a -- '*.py' '*.js'` | 0 lines (rc 1) |
| `git grep -nIi -F 'context compiler' 1e32ae7a -- vault/audits/usirc/CAPABILITY_MATRIX_G_TO_M.md vault/audits/frontier28/VERDICTS.md vendor/genesis-suite/modules/genesis-batch-drafts/lib/genesis-batch-drafts.cjs` | 3 lines |
| `git grep -nI -F 'signals.jsonl' 1e32ae7a -- '*.py' '*.js'  (then the writer marker per line)` | 15 lines, 3 writer lines |
| `git diff -U0 217d72b5 1e32ae7a -- '*.py' '*.js'  (added lines, writer marker)` | 14257 added lines, 0 writer lines |

## Claim parts

| part | outcome | reason |
|---|---|---|
| absence | PASS | 0 tracked paths, 0 code lines |
| control | PASS | name control vault/audits/usirc/CAPABILITY_MATRIX_G_TO_M.md:63; 3 writer controls hit |
| writer | PASS | 0 of 14257 added lines write signals.jsonl |

## Aperture

- Context Compiler: by name only (tracked paths matching `(?i)context[_-]?compiler`, and the identifiers `class ContextCompiler|def compile_context|context_compiler` in *.py / *.js). An implementation under another name is not excluded.
- CO-12 writers: lines naming `signals.jsonl` in *.py / *.js that also open it in a write, append or create mode, or call write_text / write_bytes / an fs write on it, on the same line. A writer that builds the path on one line and opens it on another is outside this marker; the three positive controls show the marker reaches the known writers.
- Added lines: every `+` line of the diff from the freeze 217d72b5 to the measured commit, in all *.py / *.js files. The range includes commits of other programs (a superset of this one's).

## Evidence

### Contradicting claims (quoted for the Owner)

- `vault/audits/frontier28/VERDICTS.md:253`: | **CSO** | **NOT ENTERED** | Same gate. The open question remains whether it is a new system or an evaluation head of the existing context compiler. |
- `vault/audits/usirc/CAPABILITY_MATRIX_G_TO_M.md:63`: | J4 | Memory Runtime and Context Compiler | **EXISTS_AND_COMPLETE** | `memory-engine` + **DAIF-08 Context Assembly and Mission Runtime** (20 Parts) + `cognitive_os` residency CO-13/14 | HIGH |
- `vendor/genesis-suite/modules/genesis-batch-drafts/lib/genesis-batch-drafts.cjs:3`: // to the task-context compiler; this module never dispatches, persists or accepts.

### CO-12 writers at 1e32ae7a

| file:line | line |
|---|---|
| modules/cognitive_os/co_12_telemetry.py:111 | `with (d / "signals.jsonl").open("ab") as fh:` |
| tools/test_agent_telemetry.py:271 | `with (state / "signals.jsonl").open("ab") as fh:` |
| tools/test_co12_signal_race.py:47 | `with (Path(state) / "signals.jsonl").open("a", encoding="utf-8") as fh:` |

Writer controls: modules/cognitive_os/co_12_telemetry.py, tools/test_agent_telemetry.py, tools/test_co12_signal_race.py. The first is the owner's `record_signal`; the other two are tests that write a fixture file in a temporary state directory.

### Writer lines added since the freeze: 0

## What the owner should do

- Cognitive-economy (owner of the Context Compiler question, CE ledger): treat the Context Compiler as ABSENT by name in this repository, as measured above, and decide whether to build it. This program defers it and builds none.
- The Owner adjudicates the contradicting audit line quoted above (it calls the capability EXISTS_AND_COMPLETE and names other components); plan 08-04 writes that as an `[L]` owner-bundle item.
- `modules/cognitive_os/co_12_telemetry.py`: `record_signal` stays the single writer of the CO-12 file. This program writes CO-12 rows only through it (`tools/skill_opportunity_signals.py`).

## What this program did not do

- Did not build, stub or name a Context Compiler.
- Did not add a second writer of the CO-12 file, and did not run any CO-12 writer for this handoff.
- Did not edit `vault/programs/cognitive-economy/**` or the audit files it quotes.
