# [G] compile-out + lineage -- evidence

Frozen pillar G rule (ledger, quoted):

> a compiled-out card names the skill and commit it was compiled from, and a gate fails when the source skill changes without the card being re-derived

This file is rendered by `tools/test_card_lineage.py --write-evidence` from the gate's own results, and V-CLG-EVIDENCE-CURRENT compares the committed copy with a fresh render.

## Method

- Trailer grammar: the last lines of each card are one comment line per skill the card names, `// COMPILED-FROM: skill=<name> source=skills/<name>/SKILL.md sha256=<64 hex> commit=<40 hex>`. A card naming two skills carries two lines, so a change to either skill's SKILL.md fails SOURCE-CURRENT until that line is re-derived (drill MULTI-SKILL-RERECORDED). sha256 is the LF-normalized digest of the committed SKILL.md; commit is the commit that last changed it when the card was derived.
- Population, discovered: every `hooks/**/*.js` tracked at the judged commit outside `hooks/tests/` and `hooks/_tests/`, whose LF text holds a CARD_TOKEN match (`<name>` skill) or a line starting with `// COMPILED-FROM:`. Discovery does not depend on how (or whether) the dispatcher registers the file. Nothing is listed by hand. Floor 2.
- Committed-blob rule: every byte compared comes from git blobs at the judged commit or at the trailer commit, CRLF->LF. No working-tree file is read, so an uncommitted edit never stands in for a source.
- Reuse: git access, blob reads, failure classification and the H record comparison are the skill_mirror_drift functions (git_run, resolve_commit, tracked_paths, committed_card_pairs, card_source_state, card_drift, card_verdict, is_git_failure); the card token and dispatcher reading are skill_coverage's (CARD_TOKEN, registered_hooks, discover_cards). One implementation each.
- Outcomes are PASS, FAIL or UNMEASURED; the verdict is PASS only when all 10 clauses are PASS for every card. A git failure before or during discovery (git missing, unresolvable ref, nothing tracked, a member blob unreadable) is INCONCLUSIVE, never PASS and never a traceback. After discovery a clause whose git call did not answer (failure, timeout, a trailer commit beyond a shallow clone's history) is a git-tagged UNMEASURED, and the verdict is INCONCLUSIVE when every non-PASS clause is one; any measured FAIL, or an UNMEASURED that is not git (no trailer, missing source), makes it FAIL.

Clauses:

- TRAILER (per card): at least one `// COMPILED-FROM:` line in the card, every one parses, and no skill has two; absent, a duplicate skill or an unparseable line is UNMEASURED and the other six per-card clauses are then UNMEASURED ("no trailer").
- SKILL (per card): the set of trailer skills EQUALS the set of skills the card text names in CARD_TOKEN form (`<name>` skill): a named skill without a trailer, or a trailer for an unnamed skill, is FAIL. The five clauses below are judged per trailer and folded (any FAIL is FAIL, else any UNMEASURED is UNMEASURED).
- SOURCE-PATH (per card): the trailer's source is `skills/<trailer skill>/SKILL.md`.
- SOURCE-CURRENT (per card): the committed source at the judged commit has the trailer's LF sha256; an absent source is UNMEASURED. This is the clause a re-record of H alone cannot clear.
- COMMIT-ANCESTOR (per card): the trailer commit resolves and is an ancestor of the judged commit (unresolvable: UNMEASURED, and so are the next two).
- COMMIT-TOUCHES (per card): the trailer commit changed the source path, by the definition `--trailer-for` prints: the last commit up to it that changed the source (path-limited `git log -1`) is itself, so a merge that resolved the source counts.
- COMMIT-DIGEST (per card): the source blob at the trailer commit has the trailer's digest.
- FLOOR (gate): population size >= 2 (0 is UNMEASURED, 1 is FAIL).
- DISPATCHER-COVERED (gate): every card the dispatcher registers, in either CHAIN_MAP shape (`../skills/claude-power-pack/<rel>` and `./<rel>`, skill_mirror_drift.committed_card_pairs with dotslash), is a population member, so a registered card outside the sweep (a test directory) cannot escape it.
- H-RECORD-CURRENT (gate): pillar H's committed record agrees with the committed cards and sources (skill_mirror_drift.card_source_state + card_drift + card_verdict).

## Population (live checkout, HEAD)

verdict PASS, population 2

| card | skill | source | sha256 | commit | TRAILER | SKILL | SOURCE-PATH | SOURCE-CURRENT | COMMIT-ANCESTOR | COMMIT-TOUCHES | COMMIT-DIGEST |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hooks/destructive_doctrine_card.js | destructive-state-authorization | skills/destructive-state-authorization/SKILL.md | 2985bd97002abf0589a95080a7d29b447b7a703df9ccd319494dba45701cd0de | 7f985799916ce6e12cbdc6e2495c47065366c14b | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| hooks/doctrine_cards.js | concurrent-writers-shared-tree | skills/concurrent-writers-shared-tree/SKILL.md | f1f52de4c3115d0aafc39d69c67a2e1ae7936ae63b26ecc9263d89f1150e57c0 | 31e1e25ca20bdf1266aa48c832312ef983d5d1eb | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

Gate clauses: FLOOR PASS, DISPATCHER-COVERED PASS, H-RECORD-CURRENT PASS
H record `vault/programs/skill-capability/card_source_digests.json` recorded_at_commit `ee645e0901571354af8e023eb5c641b19aa4ce08`

## Drills

Each drill starts from a copy of a clean temporary git repo seeded from the HEAD blobs of the dispatcher, the two cards and their SKILL.md sources (commits R, A, B, C). CW is hooks/doctrine_cards.js, DS is hooks/destructive_doctrine_card.js; a per-card clause is `<card>:<CLAUSE>`. A drill is ok only when the observed verdict and fail set EQUAL the declared ones (and the clauses expected UNMEASURED are UNMEASURED).

| id | mutation | declared | observed | result |
|---|---|---|---|---|
| CLEAN | none | PASS {} | PASS {} | ok |
| SOURCE-CHANGED-RERECORDED | first byte of CW's SKILL.md changed and committed; trailer untouched; H re-recorded | FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT} | FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT} | ok |
| SOURCE-CHANGED-RAW | the same source change, H not re-recorded | FAIL {H-RECORD-CURRENT, hooks/doctrine_cards.js:SOURCE-CURRENT} | FAIL {H-RECORD-CURRENT, hooks/doctrine_cards.js:SOURCE-CURRENT} | ok |
| REDERIVED | SOURCE-CHANGED-RAW, then CW's trailer re-derived with trailer_for and H re-recorded | PASS {} | PASS {} | ok |
| MERGE-REDERIVED | CW's SKILL.md edited on two branches, the conflict resolved inside the merge commit; trailer re-derived with trailer_for (it names the merge) and H re-recorded | PASS {} | PASS {} | ok |
| MULTI-SKILL-LINEAGED | CW also names `third-skill` (a see-also line) and carries a second trailer for it; H re-recorded with 3 pairs | PASS {} | PASS {} | ok |
| MULTI-SKILL-RERECORDED | MULTI-SKILL-LINEAGED (judged PASS first), then third-skill's SKILL.md changed and committed, card untouched, H re-recorded | FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT} | FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT} | ok |
| MULTI-SKILL-UNLINEAGED | CW also names `third-skill` with no trailer for it; H re-recorded with 3 pairs | FAIL {hooks/doctrine_cards.js:SKILL} | FAIL {hooks/doctrine_cards.js:SKILL} | ok |
| TRAILER-SHA-DIGIT | one hex digit of CW's trailer sha256 changed | FAIL {hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:SOURCE-CURRENT} | FAIL {hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:SOURCE-CURRENT} | ok |
| TRAILER-ABSENT | DS trailer line deleted (its two LINEAGE comment lines kept) | FAIL {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/destructive_doctrine_card.js:SKILL, hooks/destructive_doctrine_card.js:SOURCE-CURRENT, hooks/destructive_doctrine_card.js:SOURCE-PATH, hooks/destructive_doctrine_card.js:TRAILER} | FAIL {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/destructive_doctrine_card.js:SKILL, hooks/destructive_doctrine_card.js:SOURCE-CURRENT, hooks/destructive_doctrine_card.js:SOURCE-PATH, hooks/destructive_doctrine_card.js:TRAILER} | ok |
| TRAILER-DUPLICATE | DS trailer line duplicated | FAIL {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/destructive_doctrine_card.js:SKILL, hooks/destructive_doctrine_card.js:SOURCE-CURRENT, hooks/destructive_doctrine_card.js:SOURCE-PATH, hooks/destructive_doctrine_card.js:TRAILER} | FAIL {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/destructive_doctrine_card.js:SKILL, hooks/destructive_doctrine_card.js:SOURCE-CURRENT, hooks/destructive_doctrine_card.js:SOURCE-PATH, hooks/destructive_doctrine_card.js:TRAILER} | ok |
| TRAILER-UNPARSEABLE | DS trailer sha256 cut to 63 hex | FAIL {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/destructive_doctrine_card.js:SKILL, hooks/destructive_doctrine_card.js:SOURCE-CURRENT, hooks/destructive_doctrine_card.js:SOURCE-PATH, hooks/destructive_doctrine_card.js:TRAILER} | FAIL {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/destructive_doctrine_card.js:SKILL, hooks/destructive_doctrine_card.js:SOURCE-CURRENT, hooks/destructive_doctrine_card.js:SOURCE-PATH, hooks/destructive_doctrine_card.js:TRAILER} | ok |
| SKILL-MISMATCH | CW trailer replaced by the trailer for DS's skill | FAIL {hooks/doctrine_cards.js:SKILL} | FAIL {hooks/doctrine_cards.js:SKILL} | ok |
| SOURCE-PATH | CW trailer keeps its skill but points at DS's source, digest and commit A | FAIL {hooks/doctrine_cards.js:SOURCE-PATH} | FAIL {hooks/doctrine_cards.js:SOURCE-PATH} | ok |
| GHOST-SKILL | CW's CARD_TOKEN and trailer renamed to ghost-skill (sha256 and commit kept); re-record refused | FAIL {H-RECORD-CURRENT, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES, hooks/doctrine_cards.js:SOURCE-CURRENT} | FAIL {H-RECORD-CURRENT, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES, hooks/doctrine_cards.js:SOURCE-CURRENT} | ok |
| COMMIT-UNKNOWN | CW trailer commit = deadbeef x 5 (absent from a complete history: COMMIT-ANCESTOR is a measured FAIL) | FAIL {hooks/doctrine_cards.js:COMMIT-ANCESTOR, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES} | FAIL {hooks/doctrine_cards.js:COMMIT-ANCESTOR, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES} | ok |
| SHALLOW-CLONE | the clean fixture judged through a depth-1 clone that lacks the trailer commits (real ancestors) | INCONCLUSIVE {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/doctrine_cards.js:COMMIT-ANCESTOR, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES} | INCONCLUSIVE {hooks/destructive_doctrine_card.js:COMMIT-ANCESTOR, hooks/destructive_doctrine_card.js:COMMIT-DIGEST, hooks/destructive_doctrine_card.js:COMMIT-TOUCHES, hooks/doctrine_cards.js:COMMIT-ANCESTOR, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES} | ok |
| COMMIT-NOT-ANCESTOR | CW trailer commit = a side-branch commit adding identical source bytes | FAIL {hooks/doctrine_cards.js:COMMIT-ANCESTOR} | FAIL {hooks/doctrine_cards.js:COMMIT-ANCESTOR} | ok |
| COMMIT-NOT-TOUCHING | CW trailer commit = the H record commit (did not change the source) | FAIL {hooks/doctrine_cards.js:COMMIT-TOUCHES} | FAIL {hooks/doctrine_cards.js:COMMIT-TOUCHES} | ok |
| COMMIT-WRONG-DIGEST | CW source changed; trailer carries the new digest but commit A | FAIL {hooks/doctrine_cards.js:COMMIT-DIGEST} | FAIL {hooks/doctrine_cards.js:COMMIT-DIGEST} | ok |
| FLOOR-ONE | DS hook file removed (registration kept); H re-recorded with one pair | FAIL {FLOOR} | FAIL {FLOOR} | ok |
| FLOOR-ZERO | both card files removed; re-record refused | FAIL {DISPATCHER-COVERED, FLOOR, H-RECORD-CURRENT} | FAIL {DISPATCHER-COVERED, FLOOR, H-RECORD-CURRENT} | ok |
| UNLINEAGED-CARD | new top-level hooks/new_card.js naming CW's skill, no trailer, not registered | FAIL {hooks/new_card.js:COMMIT-ANCESTOR, hooks/new_card.js:COMMIT-DIGEST, hooks/new_card.js:COMMIT-TOUCHES, hooks/new_card.js:SKILL, hooks/new_card.js:SOURCE-CURRENT, hooks/new_card.js:SOURCE-PATH, hooks/new_card.js:TRAILER} | FAIL {hooks/new_card.js:COMMIT-ANCESTOR, hooks/new_card.js:COMMIT-DIGEST, hooks/new_card.js:COMMIT-TOUCHES, hooks/new_card.js:SKILL, hooks/new_card.js:SOURCE-CURRENT, hooks/new_card.js:SOURCE-PATH, hooks/new_card.js:TRAILER} | ok |
| DISPATCHER-UNCOVERED | hooks/tests/deep_card.js (test directories are outside the sweep) = copy of CW, registered next to CW; H re-recorded with 3 pairs | FAIL {DISPATCHER-COVERED} | FAIL {DISPATCHER-COVERED} | ok |
| DISPATCHER-UNCOVERED-DOTSLASH | hooks/tests/fixtures/dot_card.js = copy of CW, registered next to CW with the `./tests/fixtures/dot_card.js` shape (H's parser does not read it, no re-record) | FAIL {DISPATCHER-COVERED} | FAIL {DISPATCHER-COVERED} | ok |
| SUBDIR-CARD-DOTSLASH | hooks/_shared/sub_card.js = copy of CW with its marker defused, registered with the `./_shared/sub_card.js` shape (no re-record) | FAIL {hooks/_shared/sub_card.js:COMMIT-ANCESTOR, hooks/_shared/sub_card.js:COMMIT-DIGEST, hooks/_shared/sub_card.js:COMMIT-TOUCHES, hooks/_shared/sub_card.js:SKILL, hooks/_shared/sub_card.js:SOURCE-CURRENT, hooks/_shared/sub_card.js:SOURCE-PATH, hooks/_shared/sub_card.js:TRAILER} | FAIL {hooks/_shared/sub_card.js:COMMIT-ANCESTOR, hooks/_shared/sub_card.js:COMMIT-DIGEST, hooks/_shared/sub_card.js:COMMIT-TOUCHES, hooks/_shared/sub_card.js:SKILL, hooks/_shared/sub_card.js:SOURCE-CURRENT, hooks/_shared/sub_card.js:SOURCE-PATH, hooks/_shared/sub_card.js:TRAILER} | ok |
| CARD-EDIT-UNRECORDED | one comment line appended to CW after its trailer, H not re-recorded | FAIL {H-RECORD-CURRENT} | FAIL {H-RECORD-CURRENT} | ok |
| RECORD-UNPARSEABLE | H record replaced by a lone `{` | FAIL {H-RECORD-CURRENT} | FAIL {H-RECORD-CURRENT} | ok |
| CRLF | CW's SKILL.md, both cards, the dispatcher and the record committed with CRLF line ends | PASS {} | PASS {} | ok |
| WORKTREE-ONLY | CW source byte changed and DS trailer deleted in the working tree only, not committed | PASS {} | PASS {} | ok |

## Load-bearing

Each clause was forced PASS (its CLAUSES entry replaced) and its singleton drill re-judged; TRAILER has no singleton (its failure leaves the other six unmeasurable), so the population was narrowed to members carrying the marker. Each patch was restored and the drill re-judged.

| clause | drill | patched verdict | restored verdict |
|---|---|---|---|
| SOURCE-CURRENT | SOURCE-CHANGED-RERECORDED | PASS | FAIL |
| SKILL | SKILL-MISMATCH | PASS | FAIL |
| SOURCE-PATH | SOURCE-PATH | PASS | FAIL |
| COMMIT-ANCESTOR | COMMIT-NOT-ANCESTOR | PASS | FAIL |
| COMMIT-TOUCHES | COMMIT-NOT-TOUCHING | PASS | FAIL |
| COMMIT-DIGEST | COMMIT-WRONG-DIGEST | PASS | FAIL |
| FLOOR | FLOOR-ONE | PASS | FAIL |
| DISPATCHER-COVERED | DISPATCHER-UNCOVERED | PASS | FAIL |
| H-RECORD-CURRENT | CARD-EDIT-UNRECORDED | PASS | FAIL |
| TRAILER | UNLINEAGED-CARD | PASS | FAIL |

Git unavailable (`vgm._git_exe` raising): live INCONCLUSIVE, fixture INCONCLUSIVE, after restoration PASS.

Git failing inside a clause on the clean fixture (one subcommand stubbed): merge-base: INCONCLUSIVE 2 clause(s); log: INCONCLUSIVE 2 clause(s); cat-file: INCONCLUSIVE 2 clause(s).

## Re-derivation

When a source skill changes: re-read the skill, update the card text and its trailer together (the line comes from `python3 tools/card_lineage.py --trailer-for <skill>`, which prints and never writes), commit, then re-record H with `python3 tools/skill_mirror_drift.py --record-cards` and commit the record. H's re-record alone does not clear SOURCE-CURRENT (drill SOURCE-CHANGED-RERECORDED).

## Commands

command: python3 tools/test_card_lineage.py
command: python3 tools/test_card_lineage.py --write-evidence
command: python3 tools/card_lineage.py
command: python3 tools/card_lineage.py --trailer-for <skill>
command: python3 tools/skill_mirror_drift.py --record-cards
