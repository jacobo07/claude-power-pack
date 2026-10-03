---
name: concurrent-writers-shared-tree
description: Doctrine for two or more agent sessions writing in ONE working tree. Use before committing in a shared checkout (pathspec commits are file-granular: two writers in the same file means one commit takes the other's hunks), before publishing a commit built from a private index seeded from HEAD (re-read HEAD, refuse on a move, compare-and-swap), and before trusting a repo-wide test, lint or type-check run while other sessions edit (bracket the run with the SET of dirty paths; if it moved, the verdict is INCONCLUSIVE unless the moved paths are outside the oracle's domain). Also when a commit has already swallowed another session's work. Core rule - prefer new files, commit early, and make the oracle's scope equal the change's scope.
---

# Concurrent Writers in One Working Tree

Two agent sessions editing the same checkout is normal on a single-developer machine, and it
is not, by itself, a problem: measured over two days on one repo, the shared tree produced
*composition* — one session committed a mechanism and the other built the adjacent piece four
minutes later, having read it. Isolating them into worktrees would have prevented that.

What breaks is narrower, and both halves are cheap to defend.

## 1. Commit isolation is FILE-granular

Pathspec-scoped commits (`commit -F msg -- path/a path/b`) are the standard defence, and they
work — until two writers are inside **the same file**. Then the pathspec names a file
containing both authors' hunks, and whoever commits first takes the other's work under a
message that does not describe it.

This is not a mistake by either side. Both can follow the doctrine exactly and it still
happens, because the doctrine's unit of protection is coarser than the collision.

**So:**

- **Prefer creating a NEW file over extending a shared one** while another writer is live. A
  new gate, a new module, a new script cannot be swallowed. The work that survived cleanly in
  the source incident was in files only one session touched.
- **Commit early.** The exposure window is exactly the time your hunks sit uncommitted in a
  file someone else is also editing. Minutes, not hours.
- **Before committing, read the file's diff hunk headers** and check whether any hunk is
  outside the region you edited. Two `@@` ranges you do not recognise is the signal.
- **When it has already happened, do not rewrite the other session's commit.** A live session
  is building on it; rewriting history under a running writer is strictly worse than a
  mis-titled commit. Record in your own commit message where the missing part landed and why,
  so the change stays findable even though it is no longer bisectable.
- Hunk-level staging is the correct repair when you catch it *before* the other side commits.
  Interactive `add -p` is unavailable to agents; the non-interactive route is to filter the
  unified diff to your own hunks and apply it to the index, then verify the staged diff
  contains only what you expect.
- **A private index seeded from HEAD is a snapshot, and git's ref lock does not cover it.**
  `git commit` parents on HEAD-at-start; its lock guards only the window after it starts. A
  commit landing between your seed and that start is silently reverted by your tree. Measured
  2026-09-23 (KobiiCraft): four of another pane's files deleted this way. Re-read HEAD
  immediately before committing and refuse on a move. If a commit landed and a post-check then
  failed, still sync the shared index to HEAD, or it holds a staged revert. Repair your own
  damaging commit additively (a restore built from the exact blobs, published by
  compare-and-swap on the ref), never by rewriting under a live pane.

## 2. An oracle's verdict is about its subject only if its observation domain equals its subject

A repo-wide type-check, test suite or lint has an observation domain far wider than the change
it is judging. In a shared tree that width is pure liability: it can go red for someone else's
half-written file, and it can go green in a window that says nothing about either writer.

**Bracket every wide oracle with a reading of the tree state, before and after.** If the set of
dirty paths changed across the run, the verdict is **INCONCLUSIVE** — neither a rejection of
your change nor a licence to claim it passes. It costs two cheap commands and it is the only
thing that distinguishes "your code is wrong" from "someone saved a file".

**Bracket on the SET of dirty paths, not a count or a hash of them.** Measured
2026-09-10: a run opened and closed on 254 dirty paths and the tree had still
moved — one path had left the set while another entered it. A count cannot see
that, and a hash of the whole listing sees it but cannot say what moved, which
leaves you with an INCONCLUSIVE you cannot act on. Capture the sorted path list
before and after and diff them; naming the four paths that moved took one command
and turned an unusable verdict into a precise one.

Because with the names in hand, a movement is often demonstrably harmless, and
the distinction is worth making rather than defaulting to INCONCLUSIVE:

- **A path that moved outside the oracle's observation domain cannot have
  affected it.** Three of those four were under test trees the run never
  collected and an engine module its import closure never reaches. That is not a
  hopeful assumption — it is the same aperture question you ask of any
  instrument, applied to the contamination instead of the subject.
- **`untracked → committed` changes a file's git status without changing its
  bytes.** The fourth path was inside the collected tree and had merely been
  committed by the other writer mid-run. The test runner read identical content
  before and after. Porcelain movement is a proxy for content movement and it is
  not a perfect one.

So the ladder is: wide oracle plus bracket gives you a verdict you may have to
discard; narrow oracle plus bracket gives you one you can defend even when the
tree moves, because you can name what moved and show it was out of scope. In the
same session a fifteen-second run over ten named test files still caught the
other writer touching a file — the movement never stops, and scoping the oracle
is what makes it stop mattering.

**Narrow oracles are concurrency-proof for free.** A gate whose domain is the modules it
tests, driven by its own fixture, cannot be contaminated by an unrelated writer — no
coordination, no locking, no worktree. In the source incident the narrow gate was correct on
every run while the wide one was wrong twice. When you have a choice, make the oracle's scope
equal the change's scope; that is a better investment than isolating the writers.

## DON'T

- **Don't infer writer ownership from process count.** N agent processes tells you nothing
  about who holds which file. Use file mtimes against the clock, and commit trailers.
- **Don't conclude "the tree is clean" from a status read taken before a long command.** That
  reading expired the moment the command started.
- **Don't build a lock manager for this.** Measured harm across two days of genuine
  concurrency: one mis-titled commit and two contaminated wide-oracle runs, all recoverable,
  against continuous compounding between the two writers. Sizing the defence to the damage
  means doctrine and bracketing, not infrastructure.
- **Don't retry a wide oracle expecting a different answer.** Read what moved first; a green
  on the second run may just be the other writer having finished, which is a timing result,
  not a fix.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/concurrent-writers-shared-tree.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
