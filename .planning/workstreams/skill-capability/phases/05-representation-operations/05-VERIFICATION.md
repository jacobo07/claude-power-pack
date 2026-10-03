---
phase: 05-representation-operations
verified: 2026-10-03T22:55:00Z
status: gaps_found
score: 17/18 must-have truths verified (roadmap criterion + 17 plan truths). One partial - 05-01 truth 5, the listing-chars "upper bound" (WR-05). 3/3 plans have a must-have I drove red independently
covered_files:
  - .planning/workstreams/skill-capability/REQUIREMENTS.md
  - .planning/workstreams/skill-capability/phases/05-representation-operations/05-01-PLAN.md
  - .planning/workstreams/skill-capability/phases/05-representation-operations/05-01-SUMMARY.md
  - .planning/workstreams/skill-capability/phases/05-representation-operations/05-02-PLAN.md
  - .planning/workstreams/skill-capability/phases/05-representation-operations/05-02-SUMMARY.md
  - .planning/workstreams/skill-capability/phases/05-representation-operations/05-03-PLAN.md
  - .planning/workstreams/skill-capability/phases/05-representation-operations/05-03-SUMMARY.md
  - tools/skill_dedup_sweep.py
  - tools/test_skill_representation.py
  - vault/programs/skill-capability/evidence/F-representation.md
  - vault/programs/skill-capability/evidence/F-sweep-gex44.json
  - vault/programs/skill-capability/f-operations.json
  - vault/programs/skill-capability/ledger.json
  - vault/programs/skill-capability/owner-bundle.md
covered_digest: "v1:sha256:66fa1f3b871ad7b42c2b45b5fca91fce11f8117a89834b57e4c2c12dbbfbaf33"
behavior_unverified: 0
overrides_applied: 0
verifier: gsd-verifier subagent, host gex44, worktree sc-run, HEAD 78ca9cac
gaps:
  - truth: "05-01 truth 5: the predicted effect is an UPPER BOUND (listing chars UNMEASURED unless every removable member is watched as described)"
    status: partial
    reason: >-
      skill_dedup_sweep.listing_effect counts each member as len(name) + LINE_OVERHEAD (5) + N, where N is the
      probe's `described (N)`. The probe (wiki/tools/listing_floor_probe.py analyse) takes N from the FIRST line of
      an entry only, and splits the name at the first ':'. In a real skill_listing attachment on gex44 (transcript
      88cfe52b, 294 entries, 30000 chars), 36 entries free more characters than this formula. Examples:
      agent-reach 221 vs 845 freed and claude-api 165 vs 1083 (multi-line descriptions); code-review 27 vs 375
      (the `code-review:code-review` plugin line overwrites the probe's dict key). The quantity is labelled an
      upper bound but is not one for these shapes. The defect is latent: today's only group renders UNMEASURED
      because neither member is watched, so no published figure is wrong, and pillar F's terminal does not depend on it.
    artifacts:
      - path: "tools/skill_dedup_sweep.py"
        issue: "listing_effect line cost assumes a single-line `- <name>: <desc>` entry; CHARS_BASIS text says '+ 4' while LINE_OVERHEAD = 5"
      - path: "wiki/tools/listing_floor_probe.py"
        issue: "watch status records only the first line of a description and keys entries by text before the first ':' (frozen owner; read-only for this program)"
    missing:
      - "Return listing_chars_upper_bound UNMEASURED unless the probe row proves each counted member is a single-line entry (or have a new probe row record the entry's full block length), and add a pole that builds a multi-line entry and a namespaced collision and requires bound >= chars freed"
      - "Make CHARS_BASIS state the overhead the code adds (5: '- ', ': ', newline), not 4"
human_verification: []
---

# Phase 5: Representation operations - Verification

**Goal:** Apply disclosure / fission / fusion / inline / dedup only where measured to help.
**Requirements:** SC-F. **Host:** gex44 (python3 3.12.3). **HEAD:** 78ca9cac. **Re-verification:** No.

## Roadmap success criterion

| Criterion | Observed | Verdict |
|-----------|----------|---------|
| Each applied operation carries before/after D-LISTING and a recall check; `--pillar F` PASS | `f-operations.json` holds 0 operations, and the gate says so (`V-FO-ENTRIES 0 operations applied`). A fabricated applied entry that I committed in a clone is refused by the gate (drill 05-02). `--pillar F` prints `CEP_PILLAR_F=PASS`. No operation was applied without measurement; no operation was applied at all, with the reasons D-01 gives | VERIFIED |

## Gates run (foreground, bounded)

| Gate | Result |
|------|--------|
| `timeout 600 python3 tools/test_skill_representation.py` | rc=0, `SR_PASS=15/15`. V-FD: 13 hash poles and 2 mutants, then 7 tamper drills plus a clean control. V-FO: 25 drills (2 positive controls, 3 status expectations, 20 kills each by its own clause), the subprocess poles, and V-FR-EVIDENCE-CURRENT ok |
| `timeout 1900 python3 tools/test_skill_capability_program.py --pillar F` | `CEP_PILLAR_F=PASS`, rc=0. CE re-runs the gate argv as a real subprocess (`ce.run_gate`). The gate takes about 0.3 s on gex44 |
| `--pillar A`, `B`, `C`, `D`, `H` | all `PASS` |
| `--status` | closed `A B C D F H`; open `E G I J K L M N`; `violations: []`; rc=0 |

## Ledger state.F (independent check)

- terminal `IMPLEMENTED_AND_VERIFIED`. Evidence: gate argv `["python","tools/test_skill_representation.py"]`, the prg `F-representation.md`, two files (`F-sweep-gex44.json`, `f-operations.json`), both frozen owners, and the commits `ec706ab8` and `e4947f62`. `savings: []`.
- **Pins:** I computed my own LF-normalized sha256 for each file, from the HEAD blob and from the working tree. All three equal their pins: F-representation.md `a2c0fc2b…`, F-sweep-gex44.json `8b17edc5…`, f-operations.json `a19b06cf…`. Both commits are ancestors of HEAD.
- **`frozen`:** `frozen` at HEAD equals `frozen` at FROZEN_AT `217d72b5`. Result: True.
- **Edit scope:** the ledger diff from `ec706ab8^` to HEAD is exactly the one `"F":` line.
- **Reason text:** it says "25 drills (23 refusals, 2 positive controls) each go red by their own clause". Two of those 23 are INCONCLUSIVE expectations, not reds. Info only.

## Per-plan must-haves driven to the other answer (temp clone /tmp/v5clone at 78ca9cac)

| Plan | Must-have | Drill | Result |
|------|-----------|-------|--------|
| 05-01 | A tampered recording is refused, and groups are re-derived from records | set `planes.gex44.records.sleepy-skills.body_sha` to 64 zeros, then commit | rc=1, `SR_PASS=10/15`: `FAIL V-FD-GROUPS-REPRODUCE re-derived 0 groups, recorded 1` and `FAIL V-FD-REAL-GROUP`; the tamper drills went INCONCLUSIVE because the clean control broke. `--pillar F` = FAIL. Reverted: 15/15 |
| 05-02 | An applied entry missing a real recall pair or not measured to help is refused | committed one entry: a disclosure of concurrent-writers-shared-tree over the real K4 rows, with both recall windows = `C-window-G.json` | rc=1, `FAIL V-FO-ENTRIES 1 of 1 entries refused`, the reasons being `V-FO-RECALL FAIL: ... same window` and `V-FO-HELPED FAIL: 89844 + 1500 >= 87739`. The subprocess green pole also turned red (rc=1). `--pillar F` = FAIL. Reverted: 15/15 |
| 05-02 (WR-02) | The ordering drills bite | code mutant: the ordering condition replaced by `if False and ...` | `FAIL V-FO-DRILL-RECALL-DUPLICATE` and `FAIL V-FO-DRILL-RECALL-ORDER` (red clauses []), `SR_PASS=13/15`. RECALL-UNTIMED stayed killed, which is correct because it is a different branch. Restored |
| 05-03 | The prg is pinned by LF sha256, and the evidence must equal its render | (i) prg sha256 set to zeros in ledger.json; (ii) one byte appended to F-representation.md | (i) `FAIL L4 F: prg ... sha256 changed since it was cited`, CEP FAIL. (ii) L4 FAIL plus `L5 F: gate ... rc 1: V-FR-EVIDENCE-CURRENT differs from a fresh render`, and the gate gave 14/15. Reverted: PASS |

After the drills, `git diff 78ca9cac HEAD` in the clone is empty and the clone's tree is clean. In the real worktree, `git diff HEAD -- tools/ vault/programs/skill-capability/ wiki/tools/ modules/skill_router/` is empty.

## Independent checks requested by the fixer

### (a) WR-02, recall ordering (commit e5a41192): correct, but not sufficient

- **Correct as far as it goes.** It requires each window to have tz-bearing start < end, and before.end <= after.start. That is a necessary condition for "before = pre-op, after = post-op". It refuses the two shapes the review reproduced: one measurement under two filenames, and a reversed pair. My mutant shows those drills fail without the clause.
- **No false refusal found.** The real producer (`test_skill_delivery.py` `_utc`) writes `%Y-%m-%dT%H:%M:%SZ`, and `C-window-G.json` carries `start`/`end` in that form. In-process on `base_fixture` (python 3.12), all of these passed: touching windows (before.end == after.start), +02:00 offsets, and fractional seconds. There is a separate refusal of legitimate pairs, but it is not caused by WR-02: the host must be the literal `laptop` while the producer records `socket.gethostname()`, and only `concurrent-writers-shared-tree` has a recall detector. Both are disclosed in owner-bundle line 11 (05-02 deviation 7, review WR-07).
- **It accepts an illegitimate pair.** Nothing binds the windows to the operation. The entry carries no applied-at time or commit, and the windows are never compared with the before/after probe rows. Two consecutive pre-op windows pass every clause: I tried 2020-01-01..08 and 2020-01-08..15 in-process, and the result was `ALL ok/n-a`. Two post-op windows would pass the same way. So "recall held across the operation" is not established. What is established is only "two disjoint, ordered windows".
- **The fixer's reason for skipping the anchor is true but avoidable.** The probe row `ts` has no timezone (`2026-10-03T15:35:11`). But an entry could name its applied commit, and git `%cI` is tz-bearing. Then the gate could require before.end <= commit time <= after.start.
- **Severity: WARNING.** It is latent at 0 operations, it is not a 05-02 must-have, and it bites the first real entry.

### (b) WR-05, listing upper bound (commit 32be6105): not a true upper bound

- **What the code adds.** It computes `len(name) + LINE_OVERHEAD + N` with `LINE_OVERHEAD = len("- ") + len(": ") + len("\n") = 5`. The commit message and the rendered `chars_basis` say "+ 4", and the code adds 5. The pole works only because the code uses 5: `- aa: <100>` frees 107 = 2+5+100.
- **The format comes from the probe.** `listing_floor_probe.analyse` parses the `skill_listing` attachment line by line: `ln.startswith("- ")`, then `ln[2:].partition(":")`, then `desc.strip()`. N is the length of the stripped text after the first ':' on the entry's first line.
- **Where it is exact.** For a single-line entry `- <name>: <desc>` whose name has no ':' and whose desc has no edge whitespace, the formula equals the characters freed. That makes it a tight upper bound there.
- **Where it fails.** A real listing on this host (transcript 88cfe52b, 30000 chars, 294 entries) has 36 entries where the formula is below the characters freed:
  - multi-line descriptions: the probe sees only the first line, and continuation lines are uncounted. Examples: agent-reach 221 vs 845, claude-api 165 vs 1083.
  - plugin-namespaced lines: `- code-review:code-review` parses to the name `code-review` and overwrites the real `code-review` entry in the probe dict. The bound is 27 against 375 freed.
  - stripped edge whitespace, which `chars_basis` already discloses.
- **Verdict.** It is not a true upper bound in general. It is latent today, because the recorded group renders UNMEASURED. Recorded as the one gap above.

## Requirements coverage

| Req | Status | Evidence |
|-----|--------|----------|
| SC-F | SATISFIED for the terminal (sweep + operation gate, 0 operations applied, `--pillar F` PASS); one partial truth on the bound | drills above |

## Anti-patterns

- `grep -nE "TBD|FIXME|XXX"` over `tools/skill_dedup_sweep.py` and `tools/test_skill_representation.py` finds nothing.
- `CHARS_BASIS` text says "+ 4" while the code adds 5. Info, and part of the gap.

## Laptop plane (owner bundle, not gaps)

Two items belong to the Owner bundle: the `[F]` laptop sweep and operation procedure, including the host-string precondition and the recall reachability limit, and the gex44 sleepy-skills candidate.

## Gaps summary

There is one partial gap. The listing-chars "upper bound" is not an upper bound for multi-line or namespace-colliding listing entries. The probe that feeds it is the frozen owner, so the fix belongs in `listing_effect`: return UNMEASURED unless single-line entries are proven, and add a pole. It is latent, and pillar F's terminal does not depend on it. WR-02 is a warning: the ordering rule is right but does not anchor the windows to the operation.

---
_Verified: 2026-10-03T22:55:00Z, gsd-verifier, host gex44_
