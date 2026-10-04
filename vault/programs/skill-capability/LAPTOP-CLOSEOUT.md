# Skill / Capability Program -- laptop closeout (D-02)

Every step below runs on the laptop unless it is marked **gex44**. The laptop shared checkout is
`C:\Users\User\.claude\skills\claude-power-pack`.

What gex44 already did: every pillar except N is terminal, and `--pillar A` .. `--pillar M` pass on committed blobs.
The gex44 pre-final record is `vault/programs/skill-capability/evidence/pre-final-gex44.md`
(`PF_TERMINAL=A..M`, `PF_OPEN=N (expected ...)`, `PF_VERDICT=PASS`). Pillar N is open by design: `--final` and its R1
check read the settings file of the host they run on, so N closes only here.

What the gex44 run did not do: it pushed nothing, spent no session, never wrote state.N, never ran `--final`, and never
edited `~/.claude`. All of that is yours, in the order below.

Two notes about the gate that checks this file (`python tools/test_skill_capability_prefinal.py --closeout`):
- In closeout mode, V-PF-CLOSEOUT-DECISIONS reads STATE.md as of the commit that last touched this file. If you add a
  STATE decision line (`OWNER DECISION` or `(decision)`) and then edit this file again, the new line needs its own
  `### Q` section here, or `--closeout` goes red.
- The N row of `reviews/cbr.md` records the gex44 run status, `open`. It is not updated when you close N here.

Order of the whole closeout:
1. Bring the run branch to the laptop and check Owner boundary 4.
2. Run every Owner bundle item, in order.
3. Answer the Owner decisions (each has a recorded pick, except pillar E).
4. Close pillar N: write state.N, commit it, run `--closeout`, run `--final`, write CLOSE.md, push under boundary 4.

`--final` cannot pass before state.N exists (L3 N), so state.N is written and committed before `--final`, not after.

## 1. Bring the run branch to the laptop

The run's commits are on branch `mission/skill-capability-run` in the gex44 worktree
`/home/kobii/missions/skill-capability/.claude/worktrees/sc-run`. The run's own push to the gex44 bare repo
(`/home/kobii/repos/claude-power-pack.git`, branch `mission/skill-capability`) was refused by the ovo-push-gate hook
and not retried. The recorded pick is (a): you run the push.

**gex44** (fast-forward of `mission/skill-capability`, which is an ancestor of the run HEAD):

```
git -C /home/kobii/missions/skill-capability/.claude/worktrees/sc-run push origin mission/skill-capability-run:mission/skill-capability
```

The alternative is to fetch `mission/skill-capability-run` straight from the gex44 clone instead of from the bare repo.

**laptop**, in `C:\Users\User\.claude\skills\claude-power-pack`:

```
git remote -v
git fetch <the remote that points at the gex44 bare repo> mission/skill-capability
```

The remote name for the gex44 bare repo cannot be observed from gex44, so `git remote -v` finds it.

### Owner boundary 4 and pillar N's push rule

Before you bring the run into the shared checkout, and before any push:

```
git log --oneline FETCH_HEAD..HEAD
git log --oneline HEAD..FETCH_HEAD
```

The first command lists commits on the checkout that the run does not have. These are foreign commits that would
interleave. The second lists the run's commits. A push happens only once no foreign commits interleave. Whether you
merge or check out the run is your choice.

## Owner bundle, in order

These are the `[X]` lines of `vault/programs/skill-capability/owner-bundle.md`, copied verbatim and in order from the
committed file. Run each item in this order. Each item names its own host and commands.

1. [A] (host: laptop) The laptop's live commit card is the shared checkout's `hooks/doctrine_cards.js` (loaded by the laptop dispatcher via `../skills/claude-power-pack/hooks/doctrine_cards.js`), so the window rule (`mtime-in-own-shell-window`), the `git_error` ledger field and the empty-tree fallback reach live sessions only when you bring branch `mission/skill-capability` into that checkout. After that, the first natural commit after an own shell write on the laptop should log `unknown_reasons` = `mtime-in-own-shell-window` in `~/.claude/state/doctrine-cards/ledger.jsonl` (host: laptop). Also at your discretion: delete or ignore the 3 `abcd1234` test rows already in the live ledger (this run does not touch the laptop ledger). This is the deferred live-hook sync routed per CONTEXT, not built here, and pillar A's terminal does not depend on it.
2. [A] (host: laptop) Plan 01-02 changed `hooks/capsule_mutation_guard.js` (commit eadc0fd5): `path.basename` became `path.win32.basename` in `unwrapCall`. Behaviour is identical on Windows and it fixes POSIX (the capsule suite was 17/18 on gex44 before it). It is a live laptop hook outside pillar A's frozen owners: accept it or revert eadc0fd5 when you sync hooks to the laptop.
3. [B] (host: laptop) Pillar B's two listing-hiding attempts are falsified on D-LISTING (C6 +11 chars; K4 startup tokens 87739 -> 89844, +2105 above the +-1500 noise, n=1 per arm). The one recorded next listing hypothesis (vault/plans/skill-virtualization-k-slice-2026-10-03.md, NEXT hypothesis) is a gateway that also pages plugin skills, sized so full latent listing demand stays under the 30000-char cap. It needs your approval and fresh laptop sessions from the listing family (8 of 12 left, D-SESSIONS); GEX44 is a different install and cannot measure it. Bound: an upper bound of ~9000 startup tokens per session minus ~4000 per gateway read; it is never a realized saving until a champion / challenger pair of fresh sessions run with `wiki/tools/listing_floor_probe.py` shows challenger startup_tokens below champion by more than the +-1500 noise. Precondition: before entries / described counts are used as evidence, split listing lines at ': ' in `analyse` of `wiki/tools/listing_floor_probe.py`; the first-':' split merges every plugin:skill line (the TRAP in vault/lessons/2026-10-03-capped-listing-and-card-aperture.md, shown by V-LF-ENTRIES-APERTURE). The probe appends to listing_floor_probe.results.jsonl, so use new labels; reusing champion-startup / challenger-startup makes V-LF-SOURCES refuse. Pillar B's terminal (FALSIFIED_OR_REJECTED_BY_EVIDENCE) does not depend on this line.
4. [C] (host: laptop) Population recall and precision for `concurrent-writers-shared-tree` are UNMEASURED on gex44: the pinned pack is a selection of 20 of 140 ledger rows with no `opportunity` rows, and gex44 has no card ledger. After bringing branch `mission/skill-capability` into the laptop checkout, run `python tools/test_skill_delivery.py --measure-live --window laptop --root ~/.claude/projects --days 7 --end <ISO> --out vault/programs/skill-capability/evidence/C-window-laptop.json`. It reads the live card ledger (`~/.claude/state/doctrine-cards/ledger.jsonl`) and the laptop transcripts and prints the population figures with n; the code path is proven on the fixture by V-SD-LIVE-PATH. The 3 `abcd1234` test rows in that ledger count as judgement_unknown, never as opportunities. The output is counts and skill names only; ship it back as a commit on the branch. Pillar C's terminal does not depend on this run.
5. [D] (host: laptop) The D gate (`tools/test_skill_coverage.py`) classifies every recorded live plane separately and gex44 is the only one recorded (161 skills, i.e. directories holding SKILL.md; 9 high criticality with coverage none there). To add the laptop plane, after bringing branch `mission/skill-capability` into the laptop checkout: run `python tools/skill_coverage.py --measure-live --host laptop`, commit `vault/programs/skill-capability/evidence/D-live-laptop.json`, re-render with `python tools/test_skill_coverage.py --write-evidence`, then move the state.D prg sha256 (a new plane changes the rendered `D-coverage.md`) and add `D-live-laptop.json` as a new file evidence with its LF sha256. Coverage figures on the laptop are real only once the pillar A live-hook sync is in place (the laptop dispatcher must be this checkout's). Pillar D's terminal does not depend on this run.
6. [H] (host: laptop) Run `python tools/skill_mirror_drift.py --live` on the laptop (exit 1 names drifted live copies), record it with `python tools/skill_mirror_drift.py --measure-live --host laptop`, re-render with `python tools/test_skill_drift.py --write-evidence`, and move the state.H pins (prg sha256, plus the new recording as file evidence). Fetch precondition: the H gate re-derives the gex44 recording's repo side from the blobs at its `repo_commit` 97ded664c314857fb32f88576a41529380d060e7 (from `H-live-gex44.json`), so the laptop clone must have fetched branch `mission/skill-capability` before `--pillar H` or `--final`; otherwise V-SKD-RECORD-REPRODUCES prints INCONCLUSIVE "commit not readable" and H fails. gex44 finding (not repaired, gex44's `~/.claude` is not edited by this run): DRIFT 1 = `android-reverse-engineering` (live copy lacks `scripts/check-deps.ps1`, `scripts/decompile.ps1`, `scripts/find-api-calls.ps1`, `scripts/install-dep.ps1`), ABSENT_LIVE 10 of 24 repo skills. You decide whether gex44's live skills are synced.
7. [H] (host: laptop) Behaviour you inherit: `tools/router_freshness_gate.py` now has three new ways to go red, each printed on its `V-ROUTER-SKILL-DRIFT` line with a reason: (1) a live skill copy drifted from its committed mirror, (2) git cannot be found or the blob read fails, (3) the `skill_mirror_drift` import or a live-tree read raises. Any of them turns the router row of `tools/verify_spp.py` red. Measured cost on gex44: `skill_drift_check` max 0.054 s over 3 runs (bound 3.0 s); the router test file went 0.03-0.04 s -> 0.10-0.11 s. After any edit to a card hook (`hooks/doctrine_cards.js`, `hooks/destructive_doctrine_card.js`) or its source skill, commit it, re-derive the card and run `python tools/skill_mirror_drift.py --record-cards`, or `--final` fails on H (pillar G adds lineage on top of this record).
8. [F] (host: laptop) After bringing branch `mission/skill-capability` into the laptop checkout, run `python tools/skill_dedup_sweep.py --measure-live --host laptop --out vault/programs/skill-capability/evidence/F-sweep-laptop.json` and commit it; the gate (`python tools/test_skill_representation.py`) then checks it with every V-FD clause. `--compare` against a live tree is timing-sensitive: the live `claude-power-pack` directory holds files its own hooks append to (`vault/ceps/fires.jsonl`, `vault/test-results/.auto-spawned.log`), so a few minutes after a measure it can print `MOVED <plane>/claude-power-pack ['dir_digest']` with groups unchanged (05-01 deviation 2); the default gate never reads the live tree. To apply any operation: two fresh laptop sessions from the listing family (8 of 12 left, D-SESSIONS) with `wiki/tools/listing_floor_probe.py` under new labels (before, after), two delivery windows from `python tools/test_skill_delivery.py --measure-live` for the operated skill, then one entry in `f-operations.json`; the gate refuses it unless after startup tokens + the 1500 noise < before and recall does not drop. Host string precondition (05-02 deviation 7): V-FO-RECALL accepts only windows whose recorded host is `laptop` (`LISTING_HOSTS` in `tools/test_skill_representation.py`), but `--measure-live` records `socket.gethostname()` and has no `--host` flag (the committed C-window-G.json records `kobicraft-gex44`), so the laptop's windows are refused until you edit `LISTING_HOSTS` on purpose in a commit of its own; never edit a window's host field by hand. The only skill whose recall is measurable today is `concurrent-writers-shared-tree` (`opportunity_detectors` in C-window-G.json: commit card ledger); any other skill's recall is UNMEASURED and its operation is refused. Upper bound per dedup group: distinct names - 1 listing entries; the 30000-char cap binds and refills (C6, K4), so the realized listing saving may be 0. Pillar F's terminal does not depend on this line. Since 76d5cac5 an operation entry must also name `applied_commit`: commit the operation itself between the before and after recall windows (before.end <= its committer time <= after.start) and record that commit's hash in the entry; an entry without it is refused by V-FO-RECALL. A listing-chars figure counts only when the probe row carries `watch_shape` proof (one line, one key, exact length); the frozen probe writes none, so its rows read UNMEASURED (8a8ffb8d).
9. [F] (host: gex44) OWNER decision, no operation applied: the gex44 install holds the recorded dedup group `managing-sleepy-skills` + `sleepy-skills` (identical SKILL.md body, sha 01e535170bf2; both declare the frontmatter name `managing-sleepy-skills`; `managing-sleepy-skills` is a file subset of `sleepy-skills`, which holds extra files), recorded in `evidence/F-sweep-gex44.json` at repo_commit 01f4182a (161 skills of 186 entries). Upper bound 1 listing entry on gex44, not a D-LISTING figure; the saving is UNMEASURED (neither member is in the K4 watch set) and may be 0. Removing or merging one is your call on gex44; this run never edits `~/.claude`. `python tools/skill_dedup_sweep.py --compare vault/programs/skill-capability/evidence/F-sweep-gex44.json` on gex44 can report `claude-power-pack` dir_digest moved from its own hook logs; that is not a group change. Pillar F's terminal does not depend on this line.
10. [G] (host: laptop) Live cards: the laptop dispatcher loads the shared checkout's own `hooks/doctrine_cards.js` and `hooks/destructive_doctrine_card.js` (see [A]), so after you bring branch `mission/skill-capability` into that checkout both carry the lineage trailer (`// LINEAGE ...` plus `// COMPILED-FROM: skill=... source=... sha256=... commit=...`, comment-only, behaviour unchanged). If copies of either card also live in the laptop's `~/.claude/hooks/`, the mirror-parity row pairs `hooks/*.js` there (`modules/mirror_discovery/discovery.py`) and shows them drifted until you re-sync them from the checkout; gex44's `~/.claude/hooks/` holds neither file (checked 2026-10-03, never edited by this run). The trailer source commits 31e1e25c (concurrent-writers-shared-tree) and 7f985799 (destructive-state-authorization) are on `origin/feature/knowledge-acquisition` and `origin/mission/skill-capability`, so a laptop clone that fetched either branch can judge them. Pillar G's terminal does not depend on this line.
11. [G] (host: laptop) Gate runtime: `python tools/test_card_lineage.py` builds a fixture of temp git repos and copies it for each of its 32 drills (40 gate lines after the phase 6 review fixes); on gex44 the whole gate took at most 5.79 s (3.36 s, 4.17 s, 3.36 s in 06-02 at 30 lines; 4.4 s wall in 06-03; about 5.0 s in the review fix; 5.79 s at the phase 6 close). The laptop runtime is not measured; CE allows 1800 s per gate, and `--pillar G` / `--final` run it there.
12. [G] (host: laptop) Behaviour you inherit: after any edit to `skills/concurrent-writers-shared-tree/SKILL.md` or `skills/destructive-state-authorization/SKILL.md`, commit it, re-read the skill, then update the card text and its trailer together (`python tools/card_lineage.py --trailer-for <skill>` prints the trailer line, with the commit that last touched the committed SKILL.md) and commit the card. Then run `python tools/skill_mirror_drift.py --record-cards`, re-render H (`python tools/test_skill_drift.py --write-evidence`) and G (`python tools/test_card_lineage.py --write-evidence`), commit them, and move the pins: state.H (H-drift.md, card_source_digests.json) and state.G (G-lineage.md, card_source_digests.json, which both pillars pin). Otherwise `--final` fails on G (SOURCE-CURRENT), and on H too when the record is not re-recorded. Re-recording H alone does not clear G.
13. [E] (host: laptop) Contribution is not claimed on the committed rows. The committed CWST paired benchmark gives an effect of 0 points between arms under the reflog-aware grades (50 points under the stored grades), n=2 per arm. Within the D-SESSIONS cap of 10 new sessions the smallest effect any allocation can separate is 75 points (80 at 5 vs 5). A separating benchmark for the stored-grade effect needs a smallest total of 15 sessions (6 vs 9; 20 at 10 per arm with equal allocation), a necessary condition and not a power calculation, above the cap. The C-fixed card's "2/2 PASS" in frozen D-CARD.arm_c (and the C8 audit) has no committed row; judged by the gate's own verdict rule against N0 0/2 it is an effect of 100 points, which the budget CAN separate (SEPARABLE: 4 per arm, 8 sessions; smallest total 7; inside the cap of 10). Its p=1/3 at n=2 only says those few rows are not significant on their own, which is not the question. Question (Owner-reserved; this run spends no session): (a) run about 8 fresh laptop sessions, C-fixed vs N0 at 4 per arm, inside the cap; (b) raise the D-SESSIONS cap to at least 15 for a benchmark that could separate the stored-grade effect; or (c) keep E at RESEARCH_INSUFFICIENT_EVIDENCE. Separately: if the C-fixed rows exist on the laptop, commit them to results-delivery.jsonl.
14. [L] (host: laptop) Point the cognitive-economy mission at `vault/programs/skill-capability/handoffs/L.md`: the Context Compiler is ABSENT by name in this repository (committed blobs at 1e32ae7a, gex44: 0 of 4294 tracked paths match `(?i)context[_-]?compiler`; `git grep -nIE 'class ContextCompiler|def compile_context|context_compiler' -- '*.py' '*.js'` 0 lines), and this program defers it to that mission and builds none. Adjudicate the contradicting claim at `vault/audits/usirc/CAPABILITY_MATRIX_G_TO_M.md:63`, which reads `| J4 | Memory Runtime and Context Compiler | **EXISTS_AND_COMPLETE** | `memory-engine` + **DAIF-08 Context Assembly and Mission Runtime** (20 Parts) + `cognitive_os` residency CO-13/14 | HIGH |`, against that measured absence. The aperture is by name only, so an implementation under another name (the line cites memory-engine, DAIF-08 and CO-13/14) is not excluded: either name the component that implements it to the CE mission, or correct the audit line. Two more lines mention a context compiler, quoted in the handoff (`vault/audits/frontier28/VERDICTS.md:253`, `vendor/genesis-suite/modules/genesis-batch-drafts/lib/genesis-batch-drafts.cjs:3`). Pillar L's terminal (DEFERRED_STRONGER_OWNER) does not depend on your answer.
15. [I] (host: laptop) Point the cognitive-economy mission's pillar T ("institutional GC / simplification", predicted AUTHORIZATION_BOUND) at `vault/programs/skill-capability/handoffs/I.md`. It lists 83 module candidates (not reachable and undeclared, from `modules/liveness/reachability.py` run on a committed export of 1e32ae7a with an empty HOME; 75 gate offenders there, 64 on the gex44 live plane, the difference being live ~/.claude seeds), the 13 verdicts of `modules/capability_runtime/retirement.py --json` (UNEVALUABLE 5, ACTIVE 4, EXTERNAL 2, NEVER 2), and 155 skill candidates (coverage none on plane gex44 and not invoked in window G, 2026-09-26T18:05Z..2026-10-03T18:05Z). A candidate is not a deletion verdict, the lists are per plane and per window, and this program deleted nothing; any removal is yours (CE pillar T's rule: settings.json and skill removal need Owner). Pillar I's terminal does not depend on your answer.
16. [J] (host: laptop) The frozen owner `~/.claude/skills/skill-creator/SKILL.md` was not edited by this program. Have skill-creator emit, in every new SKILL.md frontmatter, the declaration the J gate requires: a `metadata:` block holding `opportunity_detector: <repo-relative path>`, or `opportunity_detector: none` plus `opportunity_detector_reason: <text>`. The keys are under `metadata:` because of a measured validator finding: the official plugin `quick_validate.py` (line 42) and the synced copies (line 84) whitelist top-level keys (`ALLOWED_PROPERTIES = {name, description, license, allowed-tools, metadata, compatibility}`), so a top-level `opportunity_detector:` would be refused; with the keys nested, 0 of 72 (variant, skill) validator outcomes changed on gex44. `python tools/skill_creation_gate.py --suggest` prints the lines for each repo skill, and `python tools/skill_creation_gate.py` refuses an undeclared `skills/<name>/`. Emit the `metadata:` block BEFORE the `description:` line, never after a block-scalar description (`description: >` or `|`): the router's own reader (`modules/skill_router/skill_index.py` `_read_frontmatter`) ends a block-scalar description only at a `key: value` line, so a bare `metadata:` after it, and both declaration lines, are read into the skill's description and its domain keywords (review WR-06; `insert_declaration` in the gate places it that way, and V-SCG-ROUTER-DESCRIPTION pins it). Pillar J's terminal does not depend on this edit.
17. [J] (host: laptop and gex44) Sync the live skill copies from the repo. Since 007f1d86 all 24 repo `skills/*/SKILL.md` carry the declaration, so every live copy drifts until synced (Owner decision (a): accepted as the expected red). Measured on gex44 in 08-02: `python3 tools/test_cdio_mobile.py` went `CDIO_MOBILE_PASS=6/6` -> `5/6` (`[FAIL] V-CDIO-MOBILE-MIRRORS: drift=['SKILL.md']`, repo vs `~/.claude/skills/mobile-app-ui-design/SKILL.md`); `python3 tools/skill_mirror_drift.py --live` went IDENTICAL 13 / DRIFT 1 / ABSENT_LIVE 10 -> IDENTICAL 0 / DRIFT 14 / ABSENT_LIVE 10 (rc 1 both times; the DRIFT 1 before was android-reverse-engineering, 4 `.ps1` files missing live). On the laptop, once branch `mission/skill-capability` is in the shared checkout, `tools/router_freshness_gate.py` V-ROUTER-SKILL-DRIFT reports the 14-skill drift and turns the router row of `tools/verify_spp.py` red (on gex44 it still reports IDENTICAL 13, DRIFT 1, because it judges the parent checkout's HEAD). Copy each repo `skills/<name>/` over its live copy on each host (14 live copies on gex44; the 10 ABSENT_LIVE are your call), then expect `python tools/skill_mirror_drift.py --live` to report no DRIFT for the synced skills and `python tools/test_cdio_mobile.py` to print 6/6. Do not weaken V-CDIO-MOBILE-MIRRORS to clear it.
18. [K] (host: laptop) Run `python tools/skill_opportunity_signals.py report` (read-only; never `sync` unless you mean to write) and record the CO-12 `capability_opportunity` row count; ACV (`modules/capability_runtime/agent_spec.py`) consumes those rows, see `vault/programs/skill-capability/handoffs/K.md`. gex44 value as measured at 73770627: `{"rows": 0, "by_decision": {}, "opportunities": 0, "delivered_by_card": 0, "unknown": 0}`; a `signals.jsonl` exists on gex44 but gex44 has no card ledger, so the count there is UNMEASURED, not zero opportunities. The laptop has the card ledger (`~/.claude/state/doctrine-cards/ledger.jsonl`). Pillar K's terminal does not depend on the count.
19. [M] (host: laptop) Read `vault/programs/skill-capability/handoffs/M.md`: it lists every turn and token figure this program reported, each with its named denominator (A 5 turns upper_bound on D-CARD; B 9000 tokens upper_bound on D-LISTING; B-listing-floor.md lines 21, 45, 46 on D-LISTING; E-contribution.md line 45 on D-SESSIONS, a pass-rate difference). A cost figure for any of them comes only from a `tools/usage_index.py` window you choose; this program converted none to money. Two cost-marker hits in this program's own files were adjudicated not a cost model and are pinned by exact line in `M_ADJUDICATED` of `tools/skill_handoffs.py`: `tools/skill_dedup_sweep.py:324` `def _line_cost(` (pillar F listing char count) and `tools/test_card_precision.py:330` `def write_unborn_pricing(` (pillar A drill fixture); disagree with a reason if you read them otherwise. Pillar M's terminal does not depend on your answer.

## Owner decisions

Each question quotes the STATE.md decision line it comes from. Every recorded pick except pillar E's was made during
the run as the reversible option. Pillar E has no pick, because spending sessions is reserved to you.

### Q1: Push the run branch to the gex44 bare repo?
Source (STATE.md): "[Run, epoch 2]: push of HEAD to origin mission/skill-capability (fast-forward, 0"
Question: the run's push of `mission/skill-capability-run` to `origin mission/skill-capability` (fast-forward) was
refused by the ovo-push-gate hook. Who pushes it?
Options: (a) you run `git -C /home/kobii/missions/skill-capability/.claude/worktrees/sc-run push origin mission/skill-capability-run:mission/skill-capability` on gex44 (section 1); (b) leave the run local on gex44 and fetch `mission/skill-capability-run` straight from the gex44 clone.
Recorded pick: (a). Nothing is lost either way, because every commit is on the local run branch.

### Q2: Spend D-SESSIONS on pillar E's contribution benchmark?
Source (STATE.md): "[Phase 7, epoch 3]: OWNER DECISION NEEDED (CORRECTED after 07-REVIEW CR-01) -- p"
Source (STATE.md): "[Phase 7, epoch 4]: 07-REVIEW all 9 findings fixed (5f6cedd3..7acd2feb, 07-REVIE"
Question: pillar E closed RESEARCH_INSUFFICIENT_EVIDENCE on the committed rows (authoritative effect 0, n=2 per arm).
Do you spend fresh laptop sessions to measure it? The figures are the corrected epoch 4 ones, the same as the [E]
bundle line (item 13); the epoch 3 figures are superseded.
Options: (a) about 8 fresh laptop sessions, C-fixed vs N0 at 4 per arm: the frozen D-CARD.arm_c 2/2 vs 0/2 is an effect of 100 points, which is SEPARABLE inside the D-SESSIONS cap of 10 (smallest total 7); (b) raise the D-SESSIONS cap to at least 15 for a benchmark that could separate the stored-grade effect of 50 points (smallest total 15 at 6 vs 9; 20 at 10 per arm with equal allocation); (c) keep E at RESEARCH_INSUFFICIENT_EVIDENCE.
Recorded pick: none. Spending sessions is reserved to you, so E stays RESEARCH_INSUFFICIENT_EVIDENCE on the committed rows. If E's terminal changes, the E row of `reviews/cbr.md` and the E entries of ledger `deltas` must change with it.

### Q3: Accept the live-mirror red until you sync the live skill copies?
Source (STATE.md): "[Phase 8, epoch 3]: plans 08-01..08-04 written (not yet plan-checked). OWNER DEC"
Question: since 007f1d86 all 24 repo `skills/*/SKILL.md` declare `metadata: opportunity_detector`, and the live
`~/.claude` copies were never edited by this run. `tools/test_cdio_mobile.py` V-CDIO-MOBILE-MIRRORS fails on gex44, and
the laptop `tools/router_freshness_gate.py` V-ROUTER-SKILL-DRIFT goes red, until the live copies are synced.
Options: (a) accept the expected red until you sync (the [J] bundle line, item 17); (b) declare only skills without a live mirror test; (c) you sync the live copies right after 08-02.
Recorded pick: (a). It is reversible, the red is honest drift named in advance, and no test is weakened. The sync itself is yours (live `~/.claude`).

### Q4: Rewrite the 7 SKILL.md frontmatters that were invalid YAML before phase 8 (IN-04)?
Source (STATE.md): "[Phase 8, epoch 4]: 08-REVIEW 0 CR / 6 WR / 4 IN (46f2b5ca); 9 fixed (fa8e85f8.."
Question: 7 of the 24 repo SKILL.md frontmatters were already invalid YAML before phase 8. Phase 8 did not rewrite
them. Should they be rewritten?
Options: (a) keep them as they are, as recorded in the IN-04 delta (ledger `deltas.intelligence`, pillar J); (b) rewrite them in a separate change, and then widen the live-mirror sync of Q3 to cover them.
Recorded pick: (a), not fixed. It is reversible and the defect predates phase 8.

## Close pillar N (laptop)

Run these in the laptop checkout, after section 1 and the bundle. Each step gives its expected output.

1. Check that the closeout inputs are clean (Windows CRLF or stat noise here would make `--closeout` and `--final`
   INCONCLUSIVE). Expected: no output.

   ```
   git status --porcelain -- tools vault/programs/skill-capability
   ```

   If it prints anything, only inspect it (`git diff --stat -- tools vault/programs/skill-capability` and
   `git diff --ignore-cr-at-eol --stat -- tools vault/programs/skill-capability`). Do not reset, clean or renormalize
   to clear it. Deciding what to do with a real change is yours.

2. `python tools/test_skill_capability_program.py --selftest`. Expected: `SCP_SELFTEST=PASS`.

3. `python tools/test_skill_capability_program.py --status`. Expected: open `["N"]` and violations `[]`.

4. `python tools/test_skill_capability_prefinal.py --closeout`, before state.N exists. Expected: `PF_VERDICT=FAIL`,
   with `PF_FAILED=V-PF-L8` only, and the V-PF-L8 reason naming only `L3 N: no terminal disposition`, the same as the
   gex44 run.

5. Compute the LF sha256 of the four files that state.N pins:

   ```
   python -c "import sys;sys.path.insert(0,'tools');from pathlib import Path;import test_cognitive_economy_program as ce;[print(p, ce.lf_sha256(Path(p))) for p in sys.argv[1:]]" vault/programs/skill-capability/evidence/pre-final-gex44.md vault/programs/skill-capability/reviews/ukdl.md vault/programs/skill-capability/reviews/cbr.md vault/programs/skill-capability/LAPTOP-CLOSEOUT.md
   ```

6. Write state.N. Replace only the `"N"` line of `vault/programs/skill-capability/ledger.json` under `"state"`
   (today `  "N": {"terminal": null, "evidence": [], "savings": []}`) with one line of this shape, putting the four
   hashes from step 5 where the `<sha256 ...>` slots are:

   ```
   "N": {"terminal": "IMPLEMENTED_AND_VERIFIED", "reason": "The closeout reviews are written (reviews/ukdl.md with 12 UKDL candidates, reviews/cbr.md with a 14-row case-based review) and ledger deltas are filled (product 14, intelligence 15). The gex44 pre-final check passed with A..M terminal (evidence/pre-final-gex44.md). On host laptop the --closeout gate passes on committed blobs and --final checks R1 against the P0-declared retained settings. The run branch is pushed only under Owner boundary 4, once no foreign commits interleave.", "evidence": [{"kind": "gate", "argv": ["python", "tools/test_skill_capability_prefinal.py", "--closeout"]}, {"kind": "prg", "ref": "vault/programs/skill-capability/evidence/pre-final-gex44.md", "sha256": "<sha256 of pre-final-gex44.md>"}, {"kind": "file", "ref": "vault/programs/skill-capability/reviews/ukdl.md", "sha256": "<sha256 of ukdl.md>"}, {"kind": "file", "ref": "vault/programs/skill-capability/reviews/cbr.md", "sha256": "<sha256 of cbr.md>"}, {"kind": "file", "ref": "vault/programs/skill-capability/LAPTOP-CLOSEOUT.md", "sha256": "<sha256 of LAPTOP-CLOSEOUT.md>"}], "savings": []}
   ```

   Keep the line's leading indentation and its comma exactly as the old line had them. Change nothing else in the
   ledger: the gate checks every other key against the frozen copy. The reason must not use deferral words (CE
   `DEFERRAL_PROSE`).

7. Commit the ledger by pathspec, because the gate reads committed blobs:

   ```
   git commit -m "docs(skill-capability): close pillar N on the laptop (state.N)" -- vault/programs/skill-capability/ledger.json
   git log -1 --format=%s
   ```

8. `python tools/test_skill_capability_prefinal.py --closeout`. Expected: `PF_VERDICT=PASS`. This is the gate argv
   that state.N declares, `["python", "tools/test_skill_capability_prefinal.py", "--closeout"]`, and `--final` runs it.

9. Run step 1 again (expected: no output), then:

   ```
   python tools/test_skill_capability_program.py --final
   ```

   Expected: `SCP_VERDICT=PASS`. If R1 fails, the live laptop `~/.claude/settings.json` differs from the
   P0-declared `retained.settings` (`/skillOverrides` sha256 `ffbedf71cbcc8e4d3c178ed1c4a31b48acd6a6049dfb548191685dac67843e5f`,
   `/env/CLAUDE_DOCTRINE_CARDS` = `deny`). Restoring the settings or re-declaring them is your decision.

10. Write `vault/programs/skill-capability/CLOSE.md` with these lines, then the `--final` output pasted verbatim:

    ```
    host: laptop
    commit: <the 40-hex commit that --final ran on, from git rev-parse HEAD>
    date: <UTC date and time of the --final run>
    command: python tools/test_skill_capability_program.py --final
    ```

11. Commit CLOSE.md by pathspec, then push under boundary 4 (section 1: no foreign commits interleave):

    ```
    git commit -m "docs(skill-capability): CLOSE.md with the laptop --final output" -- vault/programs/skill-capability/CLOSE.md
    git log -1 --format=%s
    ```
