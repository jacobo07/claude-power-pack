---
phase: 05-representation-operations
plan: 01
subsystem: skill-capability / pillar F
status: complete
tags: [dedup, content-hash, sweep, pillar-F, gate]
requires: [tools/skill_mirror_drift.py (phase 4, incl. review fixes f51fef33..3b9ae2f0), modules/skill_router/skill_index._FM_RE]
provides: [tools/skill_dedup_sweep.py, tools/test_skill_representation.py (sweep half), evidence/F-sweep-gex44.json]
affects: [05-02 (extends the gate with the operation ledger), 05-03 (ledger closure, L5 argv)]
tech-stack:
  added: []
  patterns: [discovered population, committed-blob reads, clause table with tamper drills, positive control on real data]
key-files:
  created:
    - tools/skill_dedup_sweep.py
    - tools/test_skill_representation.py
    - vault/programs/skill-capability/evidence/F-sweep-gex44.json
  modified: []
decisions:
  - "The gate reads recordings as committed blobs at HEAD (phase 4 posture): an uncommitted recording is INCONCLUSIVE, never judged"
  - "Group `subset` is checked by V-FD-MEMBER-FILES only; V-FD-GROUPS-REPRODUCE compares groups without it, and checks that re-derived group members carry member_files lists"
  - "One commit for the three files (the plan's Task 2 instruction), not a separate tracer commit"
metrics:
  duration: ~8 min
  completed: 2026-10-03
estimate:
  tokens: 75000
  tasks: 2
actuals:
  tokens: 33000
  tasks: 2
  commits: 3
plan_head_before: dc65b432910bb17ef581543073f0d5a0010874b5
---

# Phase 5 Plan 01: dedup content-hash sweep, gex44 recording, sweep gate Summary

The repo and gex44 skill planes are discovered, never listed. Each skill is hashed two ways: its SKILL.md body (frontmatter stripped by the owner's `_FM_RE`) and its whole directory (phase 4's `dir_digest`). One dedup candidate group comes out of it on gex44: `managing-sleepy-skills` + `sleepy-skills`. The gate re-derives that recording from committed files and blobs, and each tampered field turns it red through its own clause.

## Recorded counts (evidence/F-sweep-gex44.json, repo_commit 01f4182a)

| plane | entries | skills | no_skill_md | non_dir | symlinked |
|---|---|---|---|---|---|
| repo (blobs at 01f4182a) | 24 | 24 | 0 | 0 | 0 |
| gex44 `~/.claude/skills` | 186 | 161 | 24 | 1 (`predicting-market-opportunities`, dangling symlink) | 0 |

These match the plan-time reading (24 / 186 = 161 + 24 + 1).

Groups (1):
- `gex44/managing-sleepy-skills` + `gex44/sleepy-skills`: `fm_name_collision` true (both declare `managing-sleepy-skills`), `skill_md_identical` true, subset `[managing-sleepy-skills ⊆ sleepy-skills]` (sleepy-skills holds extra files).
- Listing effect (`--json`): both members `UNMEASURED (not in watch set)` in the two K4 rows. `entries_upper_bound` 1, `listing_chars_upper_bound` UNMEASURED. The cap note applies: a realized saving may be 0.
- `drift_excluded`: 14 names, the repo skills that are mirrored identically on gex44. These go to pillar H and are not dedup.
- Zero repo-plane groups and zero cross-plane different-name groups.

## Tasks

| # | Task | Commit |
|---|---|---|
| 1 | Tracer: sweep -> gex44 recording -> gate re-derives the group | ec706ab8 (committed together with Task 2, per the plan) |
| 2 | Full V-FD clauses, hash poles, tamper drills, `--recording` entrance | ec706ab8 |
| - | `--compare` names the moved record fields (deviation 2) | cfe4c377 |

The tracer gate was run end-to-end before expanding: `--compare` exit 0, gate `SR_PASS=2/2`.

## Gate output (default mode, after commit)

```
  ok   V-FD-RECORDINGS F-sweep-gex44.json host=gex44 repo_commit=01f4182a
  ok   V-FD-POP-FLOOR ... gex44=161/186 (no_skill_md=24 non_dir=1) repo=24/24 ... repo_floor=24
  ok   V-FD-REPO-REPRODUCES ... repo plane re-derived from blobs at 01f4182a: 24 records equal
  ok   V-FD-GROUPS-REPRODUCE ... groups=1 [managing-sleepy-skills+sleepy-skills fm_name_collision=True] drift_excluded=14
  ok   V-FD-MEMBER-FILES ... 2 member file lists re-digest; subset pairs [['gex44/managing-sleepy-skills', 'gex44/sleepy-skills']]
  ok   V-FD-PLANES-APART ... 1 groups each >= 2 distinct names; drift_excluded=14 kept apart
  ok   V-FD-REAL-GROUP ... gex44 re-derives 1 group(s): managing-sleepy-skills+sleepy-skills
  ok   V-FD-HASH-POLES 7 poles + 1 mutant (SAME-BODY, CRLF, ONE-BYTE, NO-FRONTMATTER, SAME-NAME-CROSS-PLANE,
       CROSS-PLANE-RENAMED, DISCOVERY all ok; V-FD-MUTANT-WHOLE-FILE-HASHER killed by SAME-BODY)
  ok   V-FD-TAMPER-DRILLS 6 drills + clean control
      ok   V-FD-DRILL-REPO-BODY (agent-architecture-audit) killed by V-FD-REPO-REPRODUCES
      ok   V-FD-DRILL-GEX44-BODY (adversarial-longevity) killed by V-FD-GROUPS-REPRODUCE
      ok   V-FD-DRILL-GROUPS-EMPTIED (groups) killed by V-FD-GROUPS-REPRODUCE
      ok   V-FD-DRILL-POP-ZERO (gex44) killed by V-FD-POP-FLOOR
      ok   V-FD-DRILL-SAME-NAME-INJECT (android-reverse-engineering) killed by V-FD-GROUPS-REPRODUCE, V-FD-PLANES-APART
      ok   V-FD-DRILL-MEMBER-SHA (gex44/managing-sleepy-skills:instructions.md) killed by V-FD-MEMBER-FILES
SR_PASS=9/9
```

Before the commit, the default mode printed `INCONCLUSIVE V-FD-RECORDINGS ... uncommitted` with all other recording clauses INCONCLUSIVE and exit 1. That is the intended refusal.

## Tampered-run check

`/tmp/F-sweep-tampered.json` is a copy of the recording in which gex44 `adversarial-longevity` (a non-member) takes the group's body_sha.

```
$ python3 tools/test_skill_representation.py --recording /tmp/F-sweep-tampered.json   # exit 1
  ok   V-FD-RECORDINGS F-sweep-tampered.json host=gex44 repo_commit=01f4182a (filename suffix rule not applied: outside vault/programs/skill-capability/evidence/)
  ...
  FAIL V-FD-GROUPS-REPRODUCE F-sweep-tampered.json: group 0 ['adversarial-longevity', 'managing-sleepy-skills', 'sleepy-skills'] differs from the recorded one in ['body_bytes', 'distinct_names', 'members', 'names', 'skill_md_identical']
  ...
SR_PASS=6/7
```

## Program gates (foreground, timeout 1900)

```
A rc=0 CEP_PILLAR_A=PASS
B rc=0 CEP_PILLAR_B=PASS
C rc=0 CEP_PILLAR_C=PASS
D rc=0 CEP_PILLAR_D=PASS
H rc=0 CEP_PILLAR_H=PASS
```

## Acceptance evidence

- Live tree read-only: `ls -la --time-style=full-iso ~/.claude/skills | sha256sum` gave `7474633e…59b14e` before the measure run, after it, and again after the gate runs.
- `grep -c '"description"' F-sweep-gex44.json` = 0.
- `grep -n 'expanduser\|Path.home' tools/test_skill_representation.py` returns nothing.
- `git show --stat ec706ab8` lists exactly the three plan files. The subject matches.

## Deviations from Plan

1. **[Rule 3 - Blocking] The tamper drills needed a precise tamper shape.** The plan says to change a non-member's body_sha. Setting it to a random value derives nothing different, so no clause could catch it: off-host, a live hash is a recorded fact, and only `--compare` on the measuring host can see that change. The GEX44-BODY drill and the manual tamper therefore give the non-member the group's body_sha (a hidden duplicate). This keeps V-FD-REAL-GROUP ok, as the plan-check WARNING 2 asked.
2. **[Rule 1 - Bug, found after commit] `--compare` against the live tree is time-sensitive.** At measure time it reproduced (exit 0). A few minutes later it printed `MOVED gex44/claude-power-pack ['dir_digest'] (groups and drift_excluded unchanged)`. The live `claude-power-pack` directory holds runtime files its own hooks append to (`vault/ceps/fires.jsonl`, `vault/test-results/.auto-spawned.log`). Its body hash and every group stay unchanged. `--compare` still exits 1 on any move, which is the safe option. The fix in cfe4c377 makes it name the moved fields so this reads as what it is. As a result, the plan's Task 1 `<verify>` (`--compare && gate`) passes only right after a measure, while the default gate stays green (it never reads the live tree). The recording was not re-measured to chase a passing `--compare`.
3. **Gate reads committed blobs (orchestrator note, phase 4 posture).** Discovery is HEAD-tracked plus the working-tree glob. Each recording is read through `smd.committed_bytes`, and an untracked one is `INCONCLUSIVE uncommitted`.
4. **Group `subset` is owned by V-FD-MEMBER-FILES.** `groups()` adds `subset` only when member files are given. V-FD-GROUPS-REPRODUCE compares groups with `subset` stripped and checks that re-derived members have member_files lists. Without this split, the MEMBER-SHA and SAME-NAME-INJECT drills could not each fail exactly their named set.
5. **`--recording` outside the evidence dir skips the filename-suffix rule** and says so on the V-FD-RECORDINGS line. Without this, the `/tmp` tampered copy would fail V-FD-RECORDINGS and mask V-FD-GROUPS-REPRODUCE.
6. **Concurrent commit on the branch.** Another agent committed `01f4182a docs(06): …` after this plan's ledger base (dc65b432). The recording's `repo_commit` is 01f4182a (HEAD at measure time). `commits: 3` is `git rev-list --count dc65b432..HEAD` and includes that foreign commit. This plan's own commits are 2: ec706ab8 and cfe4c377.
7. **Single commit for Task 1 + Task 2**, as the plan's Task 2 instruction and acceptance (`git show --stat HEAD` = 3 files) require, instead of a per-task tracer commit.
8. **Live plane extras:** `symlinked` list and a repo-plane `non_dir` list were added so `entries == skills + no_skill_md + non_dir` holds on both planes. Both are empty on the repo plane today.

## Known Stubs

None. `listing_chars_upper_bound` = `UNMEASURED` is a measured absence: neither sleepy member is in the K4 watch set. It is not a stub.

## Threat Flags

None. The sweep only reads the live tree and writes only `--out`.

## Self-Check: PASSED

- FOUND tools/skill_dedup_sweep.py, tools/test_skill_representation.py, vault/programs/skill-capability/evidence/F-sweep-gex44.json
- FOUND commits ec706ab8, cfe4c377
