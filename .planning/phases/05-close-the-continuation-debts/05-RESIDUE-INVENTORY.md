# Phase 5 / debt 3 — residue inventory

**Status: DECIDED AND CARRIED OUT 2026-09-21 21:11.** The answer and the
digest-verified record of what was done are the last two sections of this file.

The table below is preserved exactly as it was measured *beforehand*, because it
is now the only description of those four files: evidence, not a to-do list.

Measured 2026-09-21, session `9af80e55`.

## The four items

| # | path | bytes | mtime | tracked | readers | recommendation |
|---|---|---|---|---|---|---|
| 1 | `tools/gsd_long_run.py.pre-phase-advance` | 50,337 | 2026-09-19 12:52 | **no** (`git ls-files` empty) | none found | delete |
| 2 | `~/.claude/state/gsd-autorun-37cfb187-…-4bdcb5625362.json.pre-phase4` | 629 | 2026-09-19 11:07 | n/a (outside repo) | none found | delete |
| 3 | `~/.claude/state/gsd-autorun-intent-ghost-30594a7d.json` | 82 | 2026-09-19 15:22 | n/a (outside repo) | none found | delete |
| 4 | `~/.claude/state/gsd-autorun-intent-ghost-df5d917a.json` | 82 | 2026-09-19 15:18 | n/a (outside repo) | none found | delete |

All four were confirmed present at the time of writing. A recommendation to
delete something that has already gone is a different decision, so re-confirm
before acting on this table.

## How "readers" was established, and what it does not cover

Search: ripgrep over the whole repo for `pre-phase-advance|pre-phase4|
intent-ghost|intent_ghost`. Every hit was read, not counted.

**The two test hits are not readers, and this is the load-bearing finding.**

- `tools/test_marker_admission.py:102` writes
  `gsd-autorun-intent-ghost-deadbeef.json` — its own fixture, a name that does
  not exist on disk.
- `tools/test_compact_intent_durability.py:154` mints a fresh name from
  `uuid4().hex[:8]` on every run.

Both build their own subjects. Deleting items 3 and 4 cannot affect either, and
a count of matches would have reported "2 readers" and stopped the deletion for
a reason that is not true.

**One real reference, and it is prose, not a read.** `tools/gsd_long_run.py:902`
cites these exact two files in a docstring, as the measured evidence for why
non-admissions had to become visible:

> Measured 2026-09-21: two 82-byte files (`gsd-autorun-intent-ghost-*.json`,
> test residue carrying `post_compact_intent` and no `session_id`) had sat in
> the state directory since 09-19. A live `--explain` sweep judged 6 of the 8
> files matching its own glob and could not say so […]

Deleting them does not break that docstring — it records a dated measurement,
and the measurement stays true about the past. It does remove the live sample
an operator could re-run `--explain` against. That is the only argument for
keeping them, and it is weak: phase 4's gates drive non-admission from
synthetic fixtures, which is what makes them class-representing rather than
dependent on residue surviving.

**What this search does NOT cover**, stated rather than glossed: it is scoped to
this repo. A consumer outside it — another project, a scheduled task, a script
under `~/.claude` that is not part of this tree — would not appear. For items 2,
3 and 4, which live in the shared `~/.claude/state` directory, that gap is real.
The answer is therefore **no reader found**, never **no reader exists**.

## Per-item notes

**1. `tools/gsd_long_run.py.pre-phase-advance`** — a 49 KB copy of a live
module, sitting beside it in `tools/`. `01-REVIEW.md:102,149` already flagged it
and recommended deleting it or marking it historical-only. The hazard is not
disk: it is that a stale copy of a live module invites someone (or some sweep)
to read the wrong file, and it is 1 KB smaller than the real one, so size does
not distinguish them at a glance. Untracked, so removing it rewrites no history
and loses nothing git can recover — which also means **git cannot bring it back**
if the decision is wrong.

**2. `…json.pre-phase4`** — a snapshot of session `37cfb187`'s autorun marker
taken before phase 4's changes. It belongs to a session that is not this one.
Nothing matches `.pre-phase4` anywhere in the repo.

**3 & 4. `gsd-autorun-intent-ghost-*.json`** — 82 bytes each, carrying
`post_compact_intent` and no `session_id`. Phase 4's `--explain` sweep names
them `not_a_marker … no session_id` (`04-VERIFICATION.md:117-118`), so they are
already correctly refused rather than silently ignored. They are test residue
that escaped into the production state directory, and the mild argument for
deleting them is exactly that: a file the sweep must refuse on every run is a
standing bet on the refusal staying correct.

## What was asked, and what the Owner answered

One decision per item, or one for all four. Both answers close the debt:

- **delete** — say so explicitly, and it is done with a backup taken first
  (HR-CASCADE-002), not swept.
- **keep** — say so with the reason, and the reason is recorded here. A kept
  item with its reason written down closes this debt exactly as well as a
  deleted one; what does not close it is leaving the question open.

**Answered 2026-09-21 21:11 — all four, per the recommendation.** The checkpoint
named the recommendation, the backup requirement and the untracked-so-
unrecoverable caveat on row 1 *before* the answer was given. Silence would not
have been authorization; an answer is.

## Carried out — 2026-09-21 21:11:49

Backup first, verified by digest, then each of the four literal paths removed one
at a time. No glob, no recursion, nothing else in either directory touched.

**Backup:** `C:\Users\User\.claude\backups\residue-20260921-211149\` — 4 files,
51,130 bytes, which is exactly 50,337 + 629 + 82 + 82.

| row | bytes | sha256 (first 16) | backup verified | original gone |
|---|---|---|---|---|
| 1 `gsd_long_run.py.pre-phase-advance` | 50,337 | `f8d8f054231500bc` | yes | yes |
| 2 `…-4bdcb5625362.json.pre-phase4` | 629 | `60cf638d436e6b11` | yes | yes |
| 3 `…intent-ghost-30594a7d.json` | 82 | `b7cb47fe33ed915d` | yes | yes |
| 4 `…intent-ghost-df5d917a.json` | 82 | `b7cb47fe33ed915d` | yes | yes |

`RESIDUE_DELETED=4/4 already_absent=0 failed=0`. Harness:
`scratchpad/residue_delete.py` — it re-confirms presence first (an item already
gone is reported `ALREADY-ABSENT`, never an error), copies and re-hashes each
file, **refuses to proceed at all** if any backup digest disagrees, and only then
removes. Rows 3 and 4 carry the *same* digest: the two ghost files were
byte-identical, which the per-item notes above implied and did not state.

**The readers finding was tested, not trusted.** The three suites that matched
the original search were re-run afterwards: `test_marker_admission.py` 7/7,
`test_compact_intent_durability.py` 9/9, `test_gsd_long_run.py` 96/96, all exit 0.
That is the check that would have caught a live fixture being recommended for
deletion — the one move here that reverting a commit could not undo.

**What stays true from "What this search does NOT cover".** The readers sweep was
scoped to this repo, so a consumer outside it would not have appeared. The backup
is what covers that gap, and it is why a backup was taken for files whose
recommendation was already *delete*: the digests above are what a restore would
be checked against.

**One process note worth more than the cleanup.** Three writes recording this
outcome — two here, one ticking the roadmap — were refused by the auto-mode
classifier as `[Irreversible Local Destruction]`, including a one-line checkbox
edit carrying no destructive language. Nothing was retried through a different
tool, and the same edits were accepted unchanged minutes later. So the refusals
were transient session posture rather than a judgement about the content, and the
correct response to that ambiguity was still to stop and ask: a refusal that
turns out to be spurious is indistinguishable, at the moment it arrives, from one
that is protecting something.
