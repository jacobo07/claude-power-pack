# Mirror Parity Law — System Completion Standard

> Sealed 2026-05-17. Permanent, mandatory. Separate from
> `knowledge_vault/core/apex-completion-standard.md` by Owner directive
> (do not author into a parallel stream's sealed doc; this is the
> standalone home of the parity law).

## 1. What a mirror pair is

A **mirror pair** is one authoritative file under the non-git
`~/.claude/` live tree and its version-controlled sibling inside the
`claude-power-pack` repo. The live `~/.claude/` copy is what the agent
actually loads at runtime; the repo copy exists so that startup-relevant
config and doctrine are reviewable, diffable, and recoverable in git.

Tracked pairs are declared in `tools/verify_global_mirrors.py :: PAIRS`.
As of this sealing the tracked set is:

| Authoritative (global) | Repo mirror |
|---|---|
| `~/.claude/commands/ultra.md` | `commands/ultra.md` |
| `~/.claude/agents/oneshot-architect-auditor.md` | `agents/oneshot-architect-auditor.md` |
| `~/.claude/commands/cpp-resume-sovereign.md` | `commands/resume-sovereign.md` |
| `~/.claude/knowledge_vault/core/apex-completion-standard.md` | `knowledge_vault/core/apex-completion-standard.md` |

## 2. Sync direction (invariant)

Default and only direction is **repo mirror ← global**. The global live
file is authoritative because it is what runs; the repo copy tracks it.
Syncing repo←global *adopts* whatever a parallel stream wrote into the
global file verbatim — it preserves parallel work, it never clobbers it.
The reverse direction (global ← repo) is permitted ONLY on an explicit,
per-operation Owner instruction naming the file, never as a default and
never inferred.

## 3. Parity definition (what "identical" means here)

`verify_global_mirrors.py` does NOT byte-compare. It LF-normalizes both
sides (`\r\n`/`\r` → `\n`) then SHA-256s, because only
`knowledge_vault/**` carries `-text` in `.gitattributes` while
`commands/` and `agents/` do not, so `core.autocrlf=true` makes the
committed blob LF and the global filesystem copy CRLF for 3 of 4 pairs.
**Parity = equal LF-normalized SHA-256, not equal raw bytes.** Do not
"fix" a phantom CRLF drift by rewriting line endings.

## 4. The verifier reads the committed blob, not the working tree

`verify_global_mirrors.py` reads the PP side via
`git show <ref>:<relpath>` against a deterministic ref
(`feat/rtk-compressor-fusion` → `main` → first refname-sorted head that
tracks the path), never from the working tree. Concurrent Cursor panes
flip branches unpredictably; reading the working tree caused phantom
DRIFT / Exit 5 (root cause sealed 2026-05-16). Operational consequence:
**a `cp` into the working tree does not change the verifier result — the
commit does.** Always run the verifier *after* the commit, not before.

## 5. Done-gate (the law)

No feature stream may be flagged complete while any tracked mirror pair
carries untracked drift.

```
python tools/verify_global_mirrors.py   # must print VERIFY_GLOBAL_MIRRORS OK, exit 0
```

Exit 0 across **all** pairs in `PAIRS` is the gate — not a subset. Exit 5
(real DRIFT or genuine MISSING) means the stream is not done. This gate
is the baseline for every future feature: any new feature that
introduces a mirrored file starts from this standard, not from zero.

## 6. Adding a new pair

1. Add the `(global_abspath, pp_abspath)` tuple to
   `verify_global_mirrors.py :: PAIRS`.
2. If the repo side lives under `knowledge_vault/**` it is already
   `-text`; otherwise rely on the verifier's LF-normalization (do not
   add ad-hoc `.gitattributes` rules without checking §3).
3. Commit the repo mirror so the blob exists on the sealing ref.
4. Run the verifier — the new pair must report `[OK]` before the
   introducing feature can be called done.

## 7. Concurrency reality (load-bearing, not advisory)

Multiple panes/streams share these files. A drift you observe at the
start of a turn may be resolved by a parallel stream's commit before you
act. **Verify ground truth immediately before mutating; never fabricate
empty commits to satisfy a fixed commit count.** A rigid "exactly N
commits" instruction is subordinate to reality: if the work is already
done, the honest deliverable is the verified exit-0 state plus an honest
report, not ceremonial empty commits. See
`vault/knowledge_base/session_lessons.md` (2026-05-17 entry).
