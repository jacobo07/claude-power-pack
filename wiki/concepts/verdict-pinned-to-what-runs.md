---
type: concept
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-state-centric-reality-scan]
---

# A verdict is pinned to what runs, not to a proxy for it

A recorded "green" licenses later action only while the thing it judged is unchanged. Pin it to a
proxy that moves for other reasons and the licence expires constantly; pin it to something wider
than the subject and it never means anything.

## Case (2026-10-02)

The goal sweep may act unattended only if its judge and chaos suites were green "on this code".
"This code" was repo HEAD. In a shared tree HEAD moved every 7.6 min (median), so the record was
stale before the next 5-min pass ([[2026-10-02-state-centric-reality-scan]]).

Fix: pin to a digest of the engine's **discovered** import closure
(`modules/gsd_x/goal/engine_identity.py:139` @ `738ed40`): every import incl. function-level
ones, literal-named dynamic imports, `*.py` path literals, line endings normalised. 49 files; 43 of
336 commits in 7 days touch it.

## Rules of thumb

- **Discover the closure, never list it.** The first version missed a namespace package
  (`modules/` has no `__init__.py`) and a `__import__("gsd_long_run")` behind a helper; a
  hand list would have missed both silently.
- **Unknown matches nothing.** A missing seed returns "", which refuses.
- **Tighter pinning is also a safety property.** Dirty engine files change the digest, so the
  scheduler refused during edits and during a mutation drill: it cannot run a mutant.
- Same idea as narrow oracles in a shared tree (`~/.claude/rules/concurrent-writers-shared-tree.md`).

Related: [[goal-spine]], [[goal-spine-connect-not-build]].
