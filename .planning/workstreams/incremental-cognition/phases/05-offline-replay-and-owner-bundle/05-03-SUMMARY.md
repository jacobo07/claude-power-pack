---
phase: 05-offline-replay-and-owner-bundle
plan: 03
subsystem: owner-bundle-and-done-gate
tags: [kme, pillar-L, owner-bundle, done-gate, R3, R4, laptop-code-sync, scratch-replay]

requires:
  - phase: 05-offline-replay-and-owner-bundle
    provides: kme_replay rank core, ranking contract, KME-G smoke file (05-01, 05-02)
provides:
  - "owner bundle: ## Phase 5 with two [L] items (KME-L replay ranking line parse-proven; live-session quota decision asked, never answered)"
  - "owner bundle: ## Laptop code sync (one guarded fetch + tree-state checkout, replay-proven at the P0 freeze) and one Phase 5 correction paragraph under each of the Phase 3 and Phase 4 headers"
  - "wrapper done-gate: R3 covers pillar L kme_replay ranking files; R4 refuses the owner bundle as an owner_decision for every pillar"
  - "tools/test_kme_replay.py: V-KMER-BUNDLE-ARGV-PARSES, V-KMER-R3-PAIR, V-KMER-R3-TABLE-PINNED"
affects: [05-04 bundle summary]

actuals:
  tokens: 6870
  tasks: 3
  commits: 3
plan_head_before: 9824ab024c7b8595dadc9ddc802ddc07f0e22cd2
commits: 3

tech-stack:
  added: []
  patterns:
    - "an owner-bundle command is proven by the instrument's own parser, with controls inside the gate (a bad flag and a placeholder are refused)"
    - "a done-gate believes a terminal_evidence claim only when the file's own fields agree with it"
    - "a laptop procedure is proven by replaying its literal lines (only the fetch URL replaced) in a scratch clone at the laptop's floor"

key-files:
  created: []
  modified:
    - vault/programs/incremental-cognition/owner-bundle.md
    - tools/test_incremental_cognition_program.py
    - tools/test_kme_replay.py

key-decisions:
  - "R3-L requires a kme_replay primary ranking file only for a measurement-kind L terminal; an AUTHORIZATION_BOUND L needs the Owner's decision file instead and R3 stays silent on it"
  - "R4 matches the bundle by normalised path (backslashes, leading ./, inner ./, the absolute path of this checkout), not by string equality"
  - "the sync pins the T2 commit f3cdc79b (the commit that adds R3-L / R4) as its phase-5 ancestor"

requirements-completed: []   # IC-L addressed, NOT satisfied: L stays OPEN (no KME-L ranking, no Owner decision); ledger state.L is {}

coverage:
  - id: D1
    description: "the bundle asks the Owner for the KME-L ranking run (one parse-proven line) and for the live-session quota decision (no command, no answer, no decision file)"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "V-KMER-BUNDLE-ARGV-PARSES (1 rank line tagged L, 2 [L] items, Phase 5 NOT RUNNABLE HERE, controls)"
        status: pass
    human_judgment: false
  - id: D2
    description: "the done-gate refuses a smoke ranking, a forged primary and the bundle quoted as an owner_decision for pillar L; accepts the instrument's own KME-L primary"
    requirement: IC-L
    verification:
      - kind: unit
        ref: "V-ICP-R3-L-* (PRIMARY-ACCEPTED, SMOKE-REFUSED, 11 MUT, NO-PRIMARY-REFUSED, AUTH-ONLY-SILENT, KMER-NO-ROLE-REFUSED, REAL), V-ICP-R4-*, V-KMER-R3-PAIR, V-KMER-R3-TABLE-PINNED"
        status: pass
    human_judgment: false
  - id: D3
    description: "the laptop receives the program's tool files in one guarded step, proven on GEX44 only by a literal replay at 18e928af; the two stale laptop procedures carry a correction worded only as their replay observed"
    requirement: IC-L
    verification:
      - kind: integration
        ref: "scratch-clone replay of the sync lines read from the bundle (fetch tip == branch tip, ancestor exit 0, empty status, checkout and commit exit 0, four suites exit 0); old-path replays recorded below"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-10-04
status: complete
---

# Phase 5 Plan 03: Owner bundle [L] items, done-gate R3-L / R4, laptop code sync Summary

**The bundle now asks the Owner for the KME-L replay ranking (one parse-proven line) and for the live-session quota decision (asked, never answered), the done-gate refuses a smoke ranking, a forged primary and the bundle quoted as a decision for pillar L, and the laptop gets one guarded code-sync step that was proven by replaying its literal lines in a scratch clone at the P0 freeze, with the two stale laptop procedures corrected only as their replay observed.**

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | 8dcf1ced | docs(incremental-cognition): L -- [L] owner-bundle items (KME-L replay ranking, live-session quota decision), parse-proven |
| 2 | f3cdc79b1b961075e5a7bbd451be6569faf6c405 | feat(incremental-cognition): done-gate R3 covers pillar L ranking files; R4 refuses the owner bundle as an owner_decision |
| 3 | 26f039f1 | docs(incremental-cognition): owner bundle -- one laptop code sync for [D]..[I], [K], [L]; Phase 3 / Phase 4 corrections from replaying their old paths |

Task 2's full sha `f3cdc79b1b961075e5a7bbd451be6569faf6c405` is the PIN of the sync's ancestor check (it resolves: `git cat-file -t` prints `commit`).

## Gate output (final, observed after Task 3, in the worktree)

```
KMER_PASS=39/39  threshold=39/39  skipped=0  inconclusive=0          (python3 tools/test_kme_replay.py)
DRILL killed=13/13 ; PASS DRILL-CLEAN-AFTER-MUTANTS 37/37             (python3 tools/test_kme_replay.py --drill)
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0          (python3 tools/test_kme_pillars.py)
FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0         (python3 tools/test_floor_regression_gate.py)
ICP_SELFTEST=PASS                                                    (python3 tools/test_incremental_cognition_program.py --selftest)
```

Selftest: V-ICP-R3-L-PRIMARY-ACCEPTED, -SMOKE-REFUSED, -NO-PRIMARY-REFUSED, -AUTH-ONLY-SILENT, -KMER-NO-ROLE-REFUSED, -REAL, V-ICP-R4-BUNDLE-REFUSED, V-ICP-R4-OTHER-DECISION-SILENT and 11 `V-ICP-R3-L-MUT-*` lines, each `ok`. The one INCONCLUSIVE V-ICP-REAL-OWNER-READ (fa9ae2ed / 21671d6c not in this clone) is pre-existing and does not fail the selftest.

`python3 tools/test_incremental_cognition_program.py --pillar L`: exit 1, `FAIL L3 L: no terminal disposition` (count 1), no R3 / R4 line (state.L is empty). `git diff --stat -- tools/test_cognitive_economy_program.py` prints nothing. `--final` still fails on the CE clauses only (`failures=1`, the open pillars), unchanged by this plan.

## RED / first-run record

- **Task 1 RED:** `FAIL V-KMER-BUNDLE-ARGV-PARSES 0 replay line(s) parsed, ... [L] items=0 (>= 2), Phase 5 NOT RUNNABLE HERE=False, controls(bad=2/2, good=0/0)=True` -> `KMER_PASS=36/37`. The controls were already green (they test the gate's own parser on synthetic text). GREEN after the Phase 5 section: `KMER_PASS=37/37`, drill 13/13.
- **Task 2 RED:** `python3 tools/test_incremental_cognition_program.py --selftest` died with `NameError: name 'KMER_INSTRUMENT' is not defined` at the first new pole; `python3 tools/test_kme_replay.py` -> `FAIL V-KMER-R3-PAIR ... smoke=[...] no-primary=[]` (an L terminal citing no ranking was not refused: the gap) and `FAIL V-KMER-R3-TABLE-PINNED AttributeError: ... no attribute 'REPLAY_RULE_DENOMINATORS'` -> `KMER_PASS=37/39`. After the build one pole of mine was wrong (`smoke-role-claims-terminal` expected the "claims terminal_evidence true but" message, but a file that calls itself smoke is refused earlier by the smoke line); it was moved out of the loop with the right assertion, and `V-ICP-R3-L-REAL` was tightened to require the line `is a smoke measurement` (the looser `smoke` substring also matched the no-primary message).

## Scratch replays (GEX44; nothing run on the laptop)

Old Phase 3 path, clone at the P0 freeze `18e928af`, `FROZEN_AT` pick `d4d35059` then the fourteen picks exactly as the bundle has them (all applied, exit 0):

- `grep -c frozen_source wiki/tools/kme_pillars.py` -> **0**.

Old `[K]` path, same clone: the eight `[K]` picks exit 0; `git checkout ef336ec7... -- <three paths>` and its commit exit 0; then:

- `ls .../owner-bundle.md` -> absent (exit 2).
- `timeout 300 python3 /tmp/ic-p5-03-old/tools/test_floor_regression_gate.py` -> **exit 1**, `FAIL V-FLOOR-BUNDLE-ARGV-PARSES owner bundle missing: /tmp/ic-p5-03-old/vault/programs/incremental-cognition/owner-bundle.md`, `FLOOR_PASS=66/67`.

New path, clone at `18e928af`, the sync lines (first replay at tip `f3cdc79b` with the Task 1 bundle, then re-replayed at the final tip by extracting the indented `git` lines from the committed bundle section and running them with `git -C`, only the fetch URL replaced by the worktree path):

- `git fetch` exit 0; `git rev-parse FETCH_HEAD` -> `26f039f15ac9a298af7da90bfcd32a8ff59cffd9`, equal to the worktree `git rev-parse HEAD` at that time (first replay: `f3cdc79b...`, equal likewise).
- `git merge-base --is-ancestor f3cdc79b... FETCH_HEAD` -> exit 0.
- `git status --short -- <PATHS>` -> empty output, exit 0.
- `git checkout FETCH_HEAD -- <PATHS>` exit 0; `git commit -F ... -- <PATHS>` exit 0 (21 files, no live-loaded file in PATHS).
- The four suites, each exit 0: `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0`, `KMER_PASS=39/39  threshold=39/39  skipped=0  inconclusive=0`, `FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0`, `ICP_SELFTEST=PASS`.
- No suite needed an extra path: PATHS as the plan listed them sufficed on the first try (no fresh-clone retry).

Both scratch clones were removed (`test -d /tmp/ic-p5-03-old` and `test -d /tmp/ic-p5-03-sync` both exit 1).

## Insert-only and ledger checks

- `git diff T1^ T1 -- owner-bundle.md | grep -c '^-[^-]'` -> 0 (Task 1, +34 lines); same for Task 3 (T3, +54 lines) -> 0.
- `grep -c '^- \*\*\[L\]\*\*'` -> 2; `grep -c 'NOT RUNNABLE HERE'` -> 3; `grep -c '^## Laptop code sync'` -> 1; two `**Phase 5 correction` paragraphs.
- `ledger.json` `state.L` -> `{}`; IC-L unticked; `test -e vault/programs/incremental-cognition/evidence/L-owner-decision.md` exits 1 (no decision file written, none paraphrased).
- Task 3 `git show --stat HEAD` lists only the bundle.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The Task 3 `<verify>` script's `bad` check is broader than its stated intent**
- **Found during:** Task 3 verify.
- **Issue:** the script flags any indented sync-section line containing the substring `kme_pillars.py`, but the plan itself requires the indented suite line `python tools/test_kme_pillars.py`, which contains it. The stated intent (and the real gate, `V-KMEP-BUNDLE-ARGV-PARSES`, via `bundle_commands`) is the literal path `wiki/tools/kme_pillars.py`. As written the verify can never exit 0 with the required four suite lines.
- **Fix:** kept the four suite lines as the plan requires and ran the script with the check narrowed to `wiki/tools/kme_pillars.py`: `KMER_SYNC sections=1 indented=13 missing=[] bad=[] corrections=2`, exit 0. The plan's literal script prints `bad=['python tools/test_kme_pillars.py']` and exits 1, for that one line only. The real gates (`V-KMEP-BUNDLE-ARGV-PARSES`, 89/89) stay green.
- **Files modified:** none (verification only).

### Judgement calls (no rule trigger)

1. **Commit trailer.** The attribution reminder in force for this run (`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`) was used, as in 05-01 and 05-02, not the Opus line in the execution prompt.
2. **R4 matches by normalised path**, not string equality (plan: backslashes and a leading `./`): also an inner `./` and the absolute path of this checkout, since a forged ref could use either. Five spellings are driven in `V-ICP-R4-BUNDLE-REFUSED`, for pillars L and B.
3. **`frozen_source_problems`** is the helper the plan asked to factor out; its message text is unchanged for D..I, so every existing R3 line and pole is unchanged.
4. **Wording of the Phase 3 correction.** The plan says the done-gate's R3 (WR-07) refuses a terminal claim without `frozen_source`. The old laptop path itself would not run that guard (its wrapper predates WR-07); the refusal is at the branch tip, where the ledger is checked, so the paragraph says "the program done-gate's R3 (WR-07) refuses ..." and cites the selftest pole, not the old path's own behaviour. The old path was only observed to leave `frozen_source` out of the instrument (grep count 0).
5. **The unreported `--final` CE failure** (`CEP_VERDICT=FAIL failures=18`) is the open pillars and is unchanged; this plan does not touch the CE file.

No Rule 1, 2 or 4 deviations. No auth gates, no package installs. No checkpoint reached (the tracer's gate passed in every mode: `<verify>` is automated-only and was re-run).

## Known Stubs

None.

## Threat Flags

None. No new endpoint or write path; the sync lines read from the local repo path only in the replay and never write under `~/.claude/**`; no `claude` session was started and no remote was fetched from or pushed to.

## Notes for the next plan

- 05-04's bundle summary can quote: the two `[L]` items, the `## Laptop code sync` section (pin `f3cdc79b`), and the fact that the sync replaces the Phase 3 / `[K]` cherry-pick procedures.
- Pillar L stays OPEN: it needs the Owner's KME-L run (`L-KME-L-<date>.md`) or an Owner decision file in the Owner's own words.

## Self-Check: PASSED

- FOUND: vault/programs/incremental-cognition/owner-bundle.md, tools/test_incremental_cognition_program.py, tools/test_kme_replay.py
- FOUND commits: 8dcf1ced, f3cdc79b, 26f039f1 (`git rev-list --count 9824ab02..HEAD` = 3 before this SUMMARY commit)
- Gates re-run after the last task commit: KMER_PASS=39/39, DRILL killed=13/13, KMEP_PASS=89/89, FLOOR_PASS=67/67, ICP_SELFTEST=PASS
