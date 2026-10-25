# ctx-rent-obs tranche 1 on GEX44 (Linux plane)

Run `vault/programs/ctx-rent-obs/WORKER.md` with the changes below. This is a clone at `~/missions/ctx-rent-obs` on
branch `mission/ctx-rent-obs`. Commit there; the laptop fetches the branch back. The laptop record m-68387e14220e is
on hold, so you are the only writer of this work.

## Changes to WORKER.md
- git is `git` on PATH. You are alone in this clone: still commit only the paths you touched, one unit per commit.
- **Skip "First, before any edit" step 1** (goal binding) **and W1 step 7** (the ledger moves). The goal ledgers live
  on the laptop; the laptop coordinator books them after fetching your branch.
  - Write in CLOSURE.md: "ledger moves pending, done on the laptop plane".
  - Leave a `LEDGER_TODO` section with the two exact actions.
- **`python tools/cpp_fsck.py` reads this host's `~/.claude/state`.** Its live findings describe GEX44, not the laptop.
  Use it only for your own tests, and say so in STATUS.md.
- **W2: label every probe and B1 field "plane: GEX44"** (Claude Code version, model, listings, hooks of THIS install).
  It is a GEX44 baseline, not the laptop's.
  - Do not touch `~/.claude` settings.
  - The census JSON of slice B is not available here. Mark it "laptop-plane, pending".
- **W3: the M1 transcripts are on the laptop.**
  - Commit the C1 contract first.
  - Then measure only if a fresh matched pair can run here with a CLI flag (for example `--plugin-dir` with the
    clone's `mods/`) and no settings or install change. Otherwise the verdict is UNMEASURABLE (plane: GEX44, raw data
    on laptop), with the reason.
- **Budget:** stop at 45 turns. Before stopping, write `vault/programs/ctx-rent-obs/STATUS.md` with every unit's state
  and done-gate output, and commit it.
