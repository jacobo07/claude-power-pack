# Pillar F -- representation operations (skill-capability)

Frozen pillar F rule (ledger, quoted):

> each representation operation applied to a skill carries a before/after listing measurement against D-LISTING and a recall check; dedup decisions come from a content-hash sweep

Rendered by `tools/test_skill_representation.py --write-evidence` from committed inputs only: the sweep recordings `vault/programs/skill-capability/evidence/F-sweep-*.json`, `vault/programs/skill-capability/f-operations.json`, the D-LISTING probe rows of `wiki/tools/listing_floor_probe.results.jsonl` (the two K4 rows pinned by session id), the noise line of `vault/lessons/2026-10-03-capped-listing-and-card-aperture.md` and the drill outcomes. No host is read and no timestamp is written, so a re-run on another host renders the same bytes.

## Planes

- host: gex44 -- sweep recording `F-sweep-gex44.json`, node `kobicraft-gex44`, repo_commit `01f4182a1afd5060fcb009c6cdf79b740cd6a2ff`, live root `~/.claude/skills`
- host: laptop -- D-LISTING probe row `champion-startup`, session `8f983bc6-d760-4440-938d-aeed86a548ae`, ts 2026-10-03T15:35:11 (derived: cwd or settings_file under the laptop profile, the derivation of B-listing-floor.md)
- host: laptop -- D-LISTING probe row `challenger-startup`, session `b568fafb-782d-48ab-9014-d9ae2b13c882`, ts 2026-10-03T15:35:50 (derived: cwd or settings_file under the laptop profile, the derivation of B-listing-floor.md)

The two planes are kept apart: the sweep describes the gex44 install, the D-LISTING rows describe the laptop listing.

## Commands

command: python3 tools/skill_dedup_sweep.py --measure-live --host gex44 --out vault/programs/skill-capability/evidence/F-sweep-gex44.json
command: python3 tools/skill_dedup_sweep.py --compare vault/programs/skill-capability/evidence/F-sweep-gex44.json
note: on node `kobicraft-gex44` this --compare exits 1 (`MOVED <plane>/<skill> ['dir_digest', 'files'] (groups and drift_excluded unchanged)`) once a live skill's own hooks append to its directory; groups and drift_excluded unchanged is the expected reading. On any other node it is INCONCLUSIVE (host-bound).
command: python3 tools/test_skill_representation.py
command: python3 tools/test_skill_representation.py --write-evidence

## Population (per plane, per recording, never summed)

| recording | plane | entries | skills | no_skill_md | non_dir |
|---|---|---|---|---|---|
| F-sweep-gex44.json | gex44 | 186 | 161 | 24 | 1 (predicting-market-opportunities) |
| F-sweep-gex44.json | repo | 24 | 24 | 0 | 0 (-) |

## Dedup candidate groups

### `F-sweep-gex44.json` group 01e535170bf2

- body_sha `01e535170bf2`, body_bytes 155
- members: gex44/managing-sleepy-skills (fm_name managing-sleepy-skills, files 2); gex44/sleepy-skills (fm_name managing-sleepy-skills, files 12)
- subset pairs: gex44/managing-sleepy-skills is a subset of gex44/sleepy-skills
- fm_name_collision: True
- laptop listing status of `managing-sleepy-skills` per K4 row: champion UNMEASURED (not in watch set), challenger UNMEASURED (not in watch set)
- laptop listing status of `sleepy-skills` per K4 row: champion UNMEASURED (not in watch set), challenger UNMEASURED (not in watch set)
- entries_upper_bound 1; listing_chars_upper_bound UNMEASURED
- cap note: upper bound only: the 30,000-char listing cap binds and refills (C6, K4: B FALSIFIED), so a realized listing saving may be 0
- This is an upper bound, never a realized saving.

## Operations applied

- operations applied: 0 (`vault/programs/skill-capability/f-operations.json`; host: gex44, per its note)
- note, quoted: "Host gex44 applied no representation operation (decision D-01): a before/after D-LISTING measurement needs fresh laptop sessions, and listing hiding was falsified twice (C6, K4)."
- Why none were applied (D-01): a before/after measurement against D-LISTING needs fresh laptop sessions. D-SESSIONS: listing family 8 of 12 left; this phase consumed 0 fresh sessions. Listing hiding was falsified twice against D-LISTING (C6, K4: pillar B).
- Frozen D-LISTING at K4: startup_tokens 87739 -> 89844, listing chars cap 30000, after 29795; noise 1500 tokens (vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 12).
- Laptop applications go to the owner bundle as `[F]` lines with upper bounds, never as savings.

## Entry schema

- `op`: one of disclosure, fission, fusion, inline, dedup; `skill`: the skill name; `applied_commit`: the commit (7-40 hex, an ancestor of HEAD) that applied the operation.
- `before` / `after`: {`denominator`: "D-LISTING", `probe_label`, `session_id`, `command`}: a reference to ONE row of the D-LISTING probe results, resolved by label AND session id. No figure is typed: startup_tokens and listing chars are read from that row.
- `recall`: {`before`: {`window`, `command`}, `after`: {`window`, `command`}}: committed skill-delivery windows (`skill-delivery-window/1`) under the evidence directory; num and n are read from them, and their `start` / `end` order them: the before window ends by the committer time of `applied_commit` (git `%cI`), and the after window starts no earlier than it.
- dedup only: `sweep` (a committed `F-sweep-*.json` recording) and `group` (the 64-hex body_sha of a group re-derived from it).

## What each clause refuses

- V-FO-FILE: refuses an absent, malformed or other-schema operations file, or one whose rule is not the frozen F rule verbatim (absent is never zero operations).
- V-FO-ENTRIES: refuses any entry with a clause that is not ok or n/a (INCONCLUSIVE when every such clause is INCONCLUSIVE).
- V-FO-OP: refuses an op outside {disclosure, fission, fusion, inline, dedup}, or no skill.
- V-FO-BEFORE: refuses a before side that is missing, not D-LISTING or without its command, or that resolves to zero or several probe rows by label AND session id, or to a row with rc != 0, result != OK, a row not derived to the laptop plane (cwd or settings_file under the laptop profile), or a zero / non-int figure (UNMEASURED).
- V-FO-AFTER: refuses an after side with any defect V-FO-BEFORE refuses.
- V-FO-PAIR: refuses before and after resolving to one row, or the after row preceding the before row in the append-only rows.
- V-FO-RECALL: refuses a missing recall check; a window outside the evidence directory, absent, of another schema or capability (one present but uncommitted is INCONCLUSIVE, never judged); a null recall, n = 0, num outside [0, n]; a window without timezone-bearing start < end, or a before window that does not end by the after window's start (one window twice, or reversed); windows from two hosts, or from a host that is not the D-LISTING plane (laptop); an applied_commit that is absent, not 7-40 hex, not a commit or not an ancestor of HEAD (UNMEASURED; git unable to answer is INCONCLUSIVE), or whose committer time is before the before window's end or after the after window's start (both windows on one side of the operation).
- V-FO-HELPED: refuses after startup_tokens + sourced noise >= before startup_tokens (not measured to help); unsourced noise is INCONCLUSIVE.
- V-FO-RECALL-HELD: refuses after recall below before recall (integer cross-multiplication).
- V-FO-DEDUP-SWEEP: refuses a dedup whose sweep is not a committed recording that passed every V-FD clause, whose group is not re-derived from it, or whose skill is not a member.
- V-FO-PLANE: refuses a dedup of a member on a plane D-LISTING does not measure (only repo and laptop are).
- V-FO-NOISE-SOURCED: refuses the K4 noise figure absent from the committed lessons file.
- V-FO-DRILLS: refuses a drill whose red set is not exactly its expected clause, or a positive control that is not green.
- V-FO-SUBPROCESS-POLES: refuses the --operations entrance not exiting 1 on a fabricated entry without a recall check, or not exiting 0 on the committed file, across a real process.
- V-FR-EVIDENCE-CURRENT: refuses this file differing from a fresh render of committed inputs, or not committed.

## Operation drills (fabricated unless named REAL)

| drill | expected | observed |
|---|---|---|
| POSITIVE-CONTROL | (none) | passes all clauses |
| POSITIVE-CONTROL-DEDUP | (none) | passes all clauses |
| OP-OUTSIDE | V-FO-OP (FAIL) | killed by V-FO-OP (FAIL) |
| MISSING-AFTER | V-FO-AFTER (FAIL) | killed by V-FO-AFTER (FAIL) |
| WRONG-DENOM | V-FO-BEFORE (FAIL) | killed by V-FO-BEFORE (FAIL) |
| ZERO-TOKENS | V-FO-BEFORE (FAIL) | killed by V-FO-BEFORE (FAIL) |
| SESSION-MISMATCH | V-FO-AFTER (FAIL) | killed by V-FO-AFTER (FAIL) |
| AMBIGUOUS-LABEL | V-FO-BEFORE (FAIL) | killed by V-FO-BEFORE (FAIL) |
| ROW-PLANE | V-FO-AFTER (FAIL) | killed by V-FO-AFTER (FAIL) |
| ORDER | V-FO-PAIR (FAIL) | killed by V-FO-PAIR (FAIL) |
| MISSING-RECALL | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-NULL | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-N0 | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-WRONG-CAP | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-WRONG-HOST | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-DUPLICATE | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-ORDER | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-UNTIMED | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-BOTH-PRE-OP | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| RECALL-BOTH-POST-OP | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| MISSING-APPLIED-COMMIT | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| APPLIED-COMMIT-REAL | (none) | passes all clauses |
| APPLIED-COMMIT-UNRESOLVED | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| APPLIED-COMMIT-NOT-ANCESTOR | V-FO-RECALL (FAIL) | killed by V-FO-RECALL (FAIL) |
| APPLIED-COMMIT-GIT-FAILURE | V-FO-RECALL (INCONCLUSIVE) | killed by V-FO-RECALL (INCONCLUSIVE) |
| NOT-HELPED | V-FO-HELPED (FAIL) | killed by V-FO-HELPED (FAIL) |
| NOISE-ABSENT | V-FO-HELPED (INCONCLUSIVE) | killed by V-FO-HELPED (INCONCLUSIVE) |
| RECALL-DROP | V-FO-RECALL-HELD (FAIL) | killed by V-FO-RECALL-HELD (FAIL) |
| DEDUP-NOT-IN-SWEEP | V-FO-DEDUP-SWEEP (FAIL) | killed by V-FO-DEDUP-SWEEP (FAIL) |
| DEDUP-NOT-MEMBER | V-FO-DEDUP-SWEEP (FAIL) | killed by V-FO-DEDUP-SWEEP (FAIL) |
| DEDUP-GEX44-REAL | V-FO-PLANE (FAIL) | killed by V-FO-PLANE (FAIL) |
| K4-REAL | V-FO-HELPED (FAIL) | killed by V-FO-HELPED (FAIL) |

## V-FD tamper drills (`F-sweep-gex44.json`)

| drill | tampered | expected | observed |
|---|---|---|---|
| REPO-BODY | agent-architecture-audit | V-FD-REPO-REPRODUCES | killed by V-FD-REPO-REPRODUCES |
| GEX44-BODY | adversarial-longevity | V-FD-GROUPS-REPRODUCE | killed by V-FD-GROUPS-REPRODUCE |
| GROUPS-EMPTIED | groups | V-FD-GROUPS-REPRODUCE | killed by V-FD-GROUPS-REPRODUCE |
| POP-ZERO | gex44 | V-FD-POP-FLOOR | killed by V-FD-POP-FLOOR |
| SAME-NAME-INJECT | android-reverse-engineering | V-FD-GROUPS-REPRODUCE, V-FD-PLANES-APART | killed by V-FD-GROUPS-REPRODUCE, V-FD-PLANES-APART |
| MEMBER-SHA | gex44/managing-sleepy-skills:instructions.md | V-FD-MEMBER-FILES | killed by V-FD-MEMBER-FILES |
| DISTINCT-NAMES | group managing-sleepy-skills+sleepy-skills distinct_names | V-FD-GROUPS-REPRODUCE, V-FD-PLANES-APART | killed by V-FD-GROUPS-REPRODUCE, V-FD-PLANES-APART |

## Decision D-01: IMPLEMENTED_AND_VERIFIED (not AUTHORIZATION_BOUND)

1. Both halves of the frozen rule are implemented and checkable now. Dedup can only cite a group re-derived from a committed content-hash sweep that is measured on real planes and holds a real group (05-01). An applied operation can only be recorded with D-LISTING rows and recall windows, and the gate derives every figure from those committed instrument outputs.
2. The ROADMAP goal is "apply ... only where measured to help". On gex44 nothing can be measured against D-LISTING, and the one listing lever with evidence was falsified twice (C6, K4). Applying zero operations is the goal's own answer on this plane. The frozen rule does not require that any operation be applied.
3. The gate is not one that cannot fire. Every clause has a fabricated red drill, every green pole is a fully formed entry, three drills use real committed data (the K4 rows, the gex44 group, a real ancestor commit as the applied_commit anchor), and the entrance is driven red across a real process boundary.
4. AUTHORIZATION_BOUND is rejected. It would state that the pillar waits on the Owner, but the pillar's rule is satisfied without an Owner act. The L6 `falsification` file it needs (a pre-registered IMPLEMENT ending otherwise) would assert a falsification that never happened: nothing pre-registered for F was falsified.
