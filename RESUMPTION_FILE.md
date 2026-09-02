# RESUMPTION — delivery, and which side is behind

**Repo** `~/.claude/skills/claude-power-pack` · **branch** `frontier28/session-2026-08-26`
· **worktree** isolated under the session scratchpad. Three worktrees share this repository:
the install at `~/.claude/skills/claude-power-pack` on `feature/knowledge-acquisition`
(another pane, ~244 dirty files), this session's, and a detached checkout of `main` at
`C:\Users\User\Apps\pp-main`. Do not switch, reset, merge into, or check out over the install.

**Thesis.** The install location is a git working tree, so the bytes that run are whichever
branch a pane last checked out. Committed, pushed, and merged to `main` is not delivered.

## What the last session got wrong, and this one corrected

`SHADOWED 5` was reported as five pieces of stranded work, and the forwarded next action was
"put the installed tree on `main`, SHADOWED falls to 0". **That was harmful.** The branches
have DIVERGED — `main..FKA` 22, `FKA..main` 33 — and against the merge base the five are:

| file | truth |
|---|---|
| `bug-hunter-ceps-bridge.js` | STRANDED — mine moved, theirs did not |
| `session_start_hub.js` | STRANDED |
| `graph_first_gate.js` | **AHEAD_OF_HERE** — the running bytes are newer |
| `zero-command-bootstrap.js` | **AHEAD_OF_HERE** |
| `output_contract_stop.js` | FOREIGN_EDIT — that pane's uncommitted work |

Checking the install out onto `main` would have destroyed 22 commits to "deliver" two files
that needed no delivery. **Never act on a drift verdict that cannot say which side is behind.**

## State

The detector now decides direction from the merge base of the two worktrees' HEADs and
returns STRANDED / AHEAD_OF_HERE / DIVERGED / FOREIGN_EDIT, falling back to SHADOWED when the
running root is not a worktree of this repository — undetermined direction keeps blocking.
`remediation()` names the class and its owner; `undelivered()` charges the gate only for what
this checkout can resolve. The done-gate consumes it: all four still veto a runtime claim, an
unmapped status now blocks instead of falling off the end of a list, and LOCAL_EDIT became
UNVERIFIED because what executes is the last commit.

**No actuator was built, and that is the finding, not a gap.** Of five targets, two are
another pane's newer commits (writing would be a regression), one is their uncommitted work,
two would dirty a tree this session does not own. A mutation engine whose every real case is
refuse is complexity, not closure.

Coherence anchors:
`tools/test_effective_state.py` → 22/22 · `tools/test_effective_precondition.py` → 23/23 ·
`tools/mirror_unpaired_audit.py --quiet` → 2 STRANDED / 2 AHEAD_OF_HERE / 1 FOREIGN_EDIT ·
`tools/test_correctness_traps.py` → 9/11, the two reds naming the matcher.

## The Owner action — DONE 2026-09-02, do not forward it again

`migrate_capture_surface.py --apply` ran. Backup at
`~/.claude/settings.json.bak-capture-surface-20260902T214621Z`. Verified independently, not
from the tool's own success line: matchers `Bash|PowerShell` 2 → 4 and `Bash` 5 → 3;
`capture_liveness.py` NARROW → **COVERED, exit 0**; `test_correctness_traps.py` 9/11 → 10/11
with `V-TRAP-CHAIN-MATCHER-COVERS-POWERSHELL` green. A second run prints "nothing NARROW and
addable" — idempotent.

**Routing is delivered; it is not yet exercised.** Hooks load at session start, so the
process running now still holds the pre-change registration set. The first PowerShell record
from `cascade_check_bash` will appear in a session started after this one. Until one does,
the honest claim is DELIVERED, PENDING ACTIVATION — not "prevention proven".

Three shell-facing registrations remain blind, and **the migration is the wrong tool for
them**: `bug-hunter-learning.js`, `osa_deploy_detector.js` and `tty-restore.js` reject the
surface in their own source, so widening their matchers would assert a coverage the code
refuses. That is a code change, and nobody has asked for it.

`C:\Users\User\Apps\pp-main` is a detached checkout of `main`, created because the command
above was absent from the installed tree. Remove with
`git -C ~/.claude/skills/claude-power-pack worktree remove C:/Users/User/Apps/pp-main`.

Do **not** copy `hook-dispatcher.js` to `~/.claude/hooks/` — measured obsolete, and it would
delete `closer-guard.js` from production.

## Next three actions

1. Re-measure before anything: `python tools/mirror_unpaired_audit.py --quiet`. The class
   names, not the count, decide what is safe.
2. The two STRANDED files reach production when the install's branch takes `main` — that is
   the other pane's merge to make, not a file to write. Nothing here is owed a mutation.
3. Watch the capture corpus broaden past `bash:*` — 103 of 118 were Bash-tagged while Bash is
   27.6% of command traffic. A PowerShell-tagged record is the first evidence the widened
   route is EXERCISED rather than merely configured, and it cannot appear before a session
   starts after 2026-09-02T21:46Z.

## Start instruction

Run the anchors above; their output is the current truth, and the branch topology under them
changes without notice. Re-measure any forwarded Owner action, including its path, before
executing it — three of the last four were wrong, one of them harmful. State a completion
claim's SCOPE: `certify()` will tell you when you have overclaimed, and for tools and library
code the honest scope is `repository`, which does not owe delivery proof.
