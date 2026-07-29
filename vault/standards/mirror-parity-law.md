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

**Amended 2026-07-29 — tracked pairs are DISCOVERED, not declared.**
`modules/mirror_discovery` scans `~/.claude/{hooks,commands,agents,knowledge_vault}`
and their repo siblings and pairs by identity of the domain-relative path.

The original sealing declared four tuples in `tools/verify_global_mirrors.py ::
PAIRS`, and §6 told the next author to append a fifth by hand. Five more were
appended over the following months and then nobody appended again. Measured
2026-07-29: the list held 9 pairs while the two trees contained **28** — 5 of
10 name-matched hooks, 2 of 13 commands, 1 of 2 agents, and
`knowledge_vault/core/skill-completion-standard.md` was never enrolled at all.
Of the 7 pairs actually drifted at that moment the declared list could see
only 2. A denominator enrolled by hand cannot fail you if it never enrolled
the file (`PR-COVERAGE-BY-CONSTRUCTION-001`).

Two things stay declared, because neither is observable from either tree:

| Declared | Where | Why it cannot be derived |
|---|---|---|
| Name aliases | `mirror_discovery.ALIASES` | Nothing records that `~/.claude/commands/cpp-resume-sovereign.md` and `commands/resume-sovereign.md` are one document. |
| Foreign prefixes | `mirror_discovery.FOREIGN_PREFIXES` | Files another tool installs into the shared live tree are present, unpaired, and not this repo's to mirror. |

The set at the original sealing, kept as history:

| Authoritative (global) | Repo mirror |
|---|---|
| `~/.claude/commands/ultra.md` | `commands/ultra.md` |
| `~/.claude/agents/oneshot-architect-auditor.md` | `agents/oneshot-architect-auditor.md` |
| `~/.claude/commands/cpp-resume-sovereign.md` | `commands/resume-sovereign.md` |
| `~/.claude/knowledge_vault/core/apex-completion-standard.md` | `knowledge_vault/core/apex-completion-standard.md` |

All four are still tracked; `tools/test_mirror_discovery.py ::
V-MIRROR-COVERS-LEGACY` asserts the producer rediscovers every pair the
deleted list declared, so the change cannot have traded one blind spot for
another.

## 1b. A file present on one side only is inventory, not drift

The repo deliberately ships commands that are not installed, and the live tree
carries knowledge the repo does not mirror; on this host that is 302 files.
They are reported by `--inventory` and counted in the run header, and they do
**not** affect the exit code. `--strict` promotes them to failures for a
caller that wants full symmetry. Treating them as failures by default would
rebuild the very noise `modules/alert_escalation` exists to remove.

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

Exit 0 across **all discovered** pairs is the gate — not a subset, and no
longer whatever a list remembered. Exit 5 (real DRIFT or genuine MISSING)
means the stream is not done. This gate is the baseline for every future
feature: any new feature that introduces a mirrored file starts from this
standard, not from zero.

## 6. Adding a new pair

Nothing to add. Put the repo mirror at the same domain-relative path as the
global file and commit it; the producer tracks it on the next run. Then:

1. If the repo side lives under `knowledge_vault/**` it is already
   `-text`; otherwise rely on the verifier's LF-normalization (do not
   add ad-hoc `.gitattributes` rules without checking §3).
2. Commit the repo mirror so the blob exists on the sealing ref — §4 still
   holds, the verifier reads the committed blob and not the working tree.
3. Run the verifier — the new pair must report `[OK]` before the
   introducing feature can be called done.

Only two cases still require an edit, and both are decisions rather than
observations: a pair whose two sides carry **different names** goes in
`mirror_discovery.ALIASES`, and a file installed by **another tool** goes in
`mirror_discovery.FOREIGN_PREFIXES`. If you find yourself wanting to add a
tuple for any other reason, the paths disagree and the fix is to align them.

## 7. Concurrency reality (load-bearing, not advisory)

Multiple panes/streams share these files. A drift you observe at the
start of a turn may be resolved by a parallel stream's commit before you
act. **Verify ground truth immediately before mutating; never fabricate
empty commits to satisfy a fixed commit count.** A rigid "exactly N
commits" instruction is subordinate to reality: if the work is already
done, the honest deliverable is the verified exit-0 state plus an honest
report, not ceremonial empty commits. See
`vault/knowledge_base/session_lessons.md` (2026-05-17 entry).
