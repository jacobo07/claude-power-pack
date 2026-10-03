# [H] [J] Turn advancement and non-convergence on D-W7

Frozen rules. H: "deliver a reproducible turn taxonomy (advancing / coordination / bookkeeping / recovery / proof /
repeat / non-convergent) over usage_index joined to git; any optimization it suggests faces the 3 % rule".
J: "decided from H: non-advancing turns of interactive roots >= 3 % of D-W7 earns a detector proposal; also record
(audit G5) that Ralph no_progress fingerprints the whole work dir, so in a shared checkout peer churn reads as
progress".

## Instrument

`vault/programs/cognitive-economy/measure/turns.py` (zero model calls). Population: every D-W7 call in the usage
index (read-only sqlite), found in its transcript by `<message.id>|<requestId>`. Each call's tool uses become
categories; classes are assigned by first match, the rule for each written in the script's docstring:
recovery (an errored tool_result just before) > repeat (every tool identical to an earlier one, no edit or
compaction between) > proof (a test or gate command) > bookkeeping (record-file edit, git, task tools) > advancing
(edit of a file a commit of its repo touched within [-300 s, +24 h], any branch) > non_convergent (edit in a repo,
no such commit) > coordination (orchestration tools or text only) > unsettled (everything else; its value is not
observable, so it is kept apart from waste). Edits whose repo log could not be read would be `edit_unknown`
(UNSETTLED); in this run no repo log failed.

J's decision input was pre-registered in the script's docstring at commit 8f7b6caf, before any figure existed:
the weighted share of repeat + recovery + non_convergent turns in HUMAN-rooted trees. The broader share (every class
except advancing) is reported and is not the decision input.

command: `cd vault/programs/cognitive-economy/measure && python turns.py --measure --json turns_out.json --freeze turns_frozen_sample.json`
(result sha256 `fb0cffc14ac5f1658bd32002604d07319ab98837e54c5c2670681e72bd46b1fc`; full output
`measure/turns_out.json`).

Performance fix that made the run possible (it never completed before, > 600 s): repo tops found in-process
(nearest `.git`), one `git log` per object store (orca's 9,841 refs are shared by its worktrees), and
`tools/root_progress.py` handed the same caches by in-process monkeypatch, its file untouched. Extraction now takes
~3.5 min for 1,541 transcripts / 3.13 GB.

## Population control

75,969 calls classified = D-W7's 75,969 calls; 0 featureless; 1,541 transcripts; 95 repos; 0 repo logs failed.
Weighted total 3,325,101,725 = D-W7 weighted (100.0 %).

## Result (denominator D-W7 weighted)

| class | all calls | % D-W7 | HUMAN-rooted calls | % D-W7 |
|---|---|---|---|---|
| advancing | 9,709 | 12.53 | 5,274 | 7.20 |
| bookkeeping | 8,642 | 12.93 | 3,455 | 5.33 |
| coordination | 5,048 | 9.38 | 2,515 | 3.81 |
| proof | 4,776 | 6.13 | 2,511 | 3.22 |
| recovery | 5,170 | 5.80 | 2,743 | 3.10 |
| repeat | 617 | 0.78 | 70 | 0.10 |
| non_convergent | 356 | 0.48 | 218 | 0.31 |
| unsettled | 41,651 | 51.97 | 21,572 | 27.08 |

- J decision input (HUMAN-rooted recovery + repeat + non_convergent): **3.51 %** of D-W7. Broader non-advancing
  share (not the decision input): 42.95 %.
- Per root (`tools/root_progress.py`, the 40 costliest roots = 16.23 % of D-W7, all ADVANCED): median 27.6 turns per
  commit in span, median 45.7 turns per green test. The costliest root (a mission, 634 turns, 0.80 %) made 19 commits
  and recorded 1 green test.

## Classifier controls

- Blind hand labels: `turns.py --sample 40 --seed 20261003 --sheet turns_label_sheet.json`. The sheet shows what each
  call did (tool names + truncated inputs, whether an error preceded), never its class. Labelled by concept, then
  scored: `turns.py --score turns_label_sheet.json` ->
  `{"labelled": 40, "agreement": 0.875, "shuffled_agreement": 0.45, "disagreements": {"proof->unsettled": 1, "bookkeeping->proof": 1, "unsettled->bookkeeping": 3}}`
  (label->classifier). Negative control: the same labels against shuffled classifier output agree 45 %.
- Every disagreement is outside J's classes: 3 read-only git commands (`git show`, status probes) the GIT rule calls
  bookkeeping; 1 lint run the test regex misses; 1 commit command carrying a gate token. All 3 recovery labels
  agree. J's input does not move under these errors.
- Limitation, stated: one labeller, of the same agent family as the classifier's author, and only 3 recovery
  items in the sample. The agreement figure bounds the classifier's gross error, not recovery's precision.

## H gate (PRG)

command: `python vault/programs/cognitive-economy/gates/gate_turns.py` (fresh process)

```
  ok   labels_sha256 expected f83bf3fe5bcbb56408b661a5fcd60302447c7494278ac49e57fa4f6b354605a5 observed f83bf3fe5bcbb56408b661a5fcd60302447c7494278ac49e57fa4f6b354605a5
  distribution {'advancing': 379, 'bookkeeping': 355, 'coordination': 173, 'non_convergent': 14, 'proof': 203, 'recovery': 225, 'repeat': 22, 'unsettled': 1629}
GATE_TURNS=PASS failures=0 rows=3000
```

Red drill: `--perturb-order` (swap recovery/repeat precedence) -> labels_sha256 `b379877e...`, `GATE_TURNS=FAIL`,
exit 1. The frozen sample `measure/turns_frozen_sample.json` (3,000 feature rows, no paths or text) is pinned by
sha256 in H's ledger evidence.

## Decisions

- **H: IMPLEMENTED_AND_VERIFIED.** The taxonomy is reproducible (gate above). Optimizations it suggests, by the 3 %
  rule: none clears it as a lever of its own. Bookkeeping is 12.93 % of D-W7 but is the record work the doctrine
  requires (handoffs, STATE, commits); there is no measured removable share, so no proposal. Recovery is 5.80 % and
  is handed to J. UNSETTLED (51.97 %) is not waste and is not proposed against.
- **J: the frozen rule fires.** HUMAN-rooted recovery + repeat + non_convergent = 3.51 % >= 3 %, so a detector
  proposal is earned. It is a handoff to the frozen owner `tools/gsd_mission.py`
  (`vault/programs/cognitive-economy/handoffs/J.md`), not an edit. Two facts the owner needs: (1) the share that
  fires the rule is HUMAN-rooted, which `gsd_mission` does not supervise; non-HUMAN roots carry another
  ~3.55 % (all roots 7.06 % minus HUMAN 3.51 %); (2) 88 % of the input is recovery (3.10 of 3.51 points), so a
  repeat-only or churn-only detector would address 0.41 points.
- **Audit G5, verified in source:** `tools/gsd_mission.py:1649-1671` `progress_fingerprint` hashes `rev-parse HEAD`,
  the whole-tree `status --porcelain` and `diff HEAD --shortstat` of the work dir. In a shared checkout, any peer's
  commit or dirty file changes the hash, so a stalled mission reads as progressing and the no_progress halt
  (`gsd_mission.py:1553-1563`) cannot fire.

Displacement: not applicable (no lever built here). Saving: none claimed.
