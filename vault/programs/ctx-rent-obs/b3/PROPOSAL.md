# ctx-rent-obs t3 W10: top-level boot floor reduction proposal

**Nothing here is applied.** Each row is for the Owner to accept or reject; a later tranche executes.
Weekly value = saving per call x 35,586 top-level calls (ESTATE week 10-18..10-25, laptop). It is **processed tokens,
not billed**: cache reads bill lower, so billed payback is not derived. Per-call savings are on the **call-1 floor**;
later calls carry the same prefix, which is why the per-call figure is multiplied by all calls.

Evidence classes: **measured** = fresh headless probe pairs (`b3/contracts/C3a.verdict.json`); **ESTIMATE** = census
chars/3.6 (`B3.md`, `b3/toplevel-boot-aggregate.json`). C3a shows the chars/3.6 estimate overstated the skill listing
by ~2.35K (8.36K est. vs 6.01K measured, x0.72). Treat every ESTIMATE row below as an upper bound, and read the
x0.72 column as the haircut if the same overstatement holds (unverified for the other sources).

| # | source | saving / call | weekly processed | evidence | behaviour risk | exact edit | revert |
|---|---|---:|---:|---|---|---|---|
| 1 | agent listing (`attachment:agent_listing_delta`) | 10.6K est. (7.7K at x0.72) | 378M (272M) | ESTIMATE; no CLI flag removes it | the agent types removed can no longer be dispatched by name; which ones a session needs is not measured here | move the agent `.md` files not used in the last 30 days out of `~/.claude/agents/` and the PP agent mirrors into a `agents-parked/` folder (keep the ones a hook dispatches by name) | move the folder back; agents load cold per session |
| 2 | always-loaded rules (`~/.claude/rules/*.md`, 8 files) | 7.3K est. (5.3K) | 261M (188M) | ESTIMATE | a rule stops being in prefix; it fires only when its skill loads | move `generated-content-needs-an-evidence-gate`, `effect-authority-across-transports`, `durable-exit-transaction` (4.2K est.) into skills with the same name and extend `skill-rule-index.md`, the way 18 rules already moved | copy the files back from `~/.claude/backups/` taken before the move |
| 3 | per-project MEMORY.md index | 5.4K est. mean (3.9K) | 191M (138M) | ESTIMATE; the PP pane alone carries 6.3K | the index loses hooks to older memories; the files stay | cut `MEMORY.md` to the 200-line limit already set in `~/.claude/CLAUDE.md`, moving cold lines to `MEMORY_COLD.md` (already used for this) | restore the file from git or the `.bak` |
| 4 | skill listing (`attachment:skill_listing`) | **6.0K measured** | **214M** | **measured** (2 pairs, 5,838 and 6,180) | `--disable-slash-commands` also removes all slash commands: `/kclear`, `/kresume`, `/lazarus`, `/ultra` unusable, and the Skill tool lists nothing | do **not** apply as a blanket flag. Safer variant, ESTIMATE only: shorten descriptions of the ~230 listed skills; the listing is capped at 30K chars and already shows descriptions for only 71 of 232 entries | remove the flag from the launcher / restore descriptions from git |
| 5 | hook additionalContext (SessionStart 1.5K + UserPromptSubmit 0.85K) | 2.3K est. (1.7K) | 83M (60M) | ESTIMATE; also 4 of 7 valid sessions had a hook time out before call 1 | the injected reminders (Findings Bus, OWNER_QUEUE, compound-learning auto-invoke) stop appearing | cap each hook's context at 1K chars in the hook, not in settings | revert the hook commit |
| 6 | project CLAUDE.md files | 0.6K to 2.5K per repo; PP repo 6.35K | not derived (repo-specific) | ESTIMATE | doctrine text no longer inline | move the sealed Activation Criteria sections of the PP `CLAUDE.md` to a skill index, as for rules | git revert |

Rows 1 to 3 are the largest ESTIMATE rows and are not yet measured. **Recommended next step** (not done here): measure
rows 1 and 2 with the same matched-pair method before accepting. Row 1 needs a way to hide the agent files from one probe
(a scratch `--setting-sources` or `--plugin-dir` experiment, or a temporary agents folder move), which is exactly the
config change this tranche forbade, so it needs your go.

## What C3a changes about the ranking
- The only measured row is #4, and it is the one with the worst side effect (no commands). It is a proof that the method
  works and a calibration of the estimator, not a recommendation.
- The estimator's x0.72 overstatement means the 54.8K "unattributed" half of the floor is **smaller** than stated: named
  sources are over-counted, so the unattributed remainder is under-counted. No W8 or W9 figure bounds it.
- Headless probe floors (70K-86K) sit below organic floors (110K): the delta transfers to organic sessions, the absolute
  number does not.

## Payback
One accepted 10K cut is worth ~356M processed per week (10K x 35,586 calls), so the tranche's ~7M budget is returned
in roughly 3 hours of estate traffic (7M / 356M x 168 h), on a processed basis.
Row 4 alone, if it were safe to apply, is worth 214M processed per week. Billed payback is not derived.
