# Canonicalization receipt — GSD X source of truth

**Sealed 2026-09-19.** Produced by measurement, not by policy assertion.

## The premise that was false

The brief described three potentially competing GSD X realities — `gsd-x`,
`integrate/gsd-x-landing` and `main` — and asked for them to be canonicalized or
explicitly superseded. Measured, there was never a conflict to resolve:

| branch | tip | commits unique to it vs `main` |
|---|---|---|
| `gsd-x` | `a3411c9` | **0** |
| `integrate/gsd-x-landing` | `42dd006` | **0** |

Both were already ancestors of the development branch. There was nothing to merge, nothing
to rescue and nothing to lose. A wave spent "merging the old GSD X branches" would have
produced no change to any file.

## Canonical assignment

| role | ref | tip |
|---|---|---|
| canonical **development** | `feature/knowledge-acquisition` | `1d1700d` |
| canonical **release** | `main` (= `origin/main`) | `ada05e2` |
| historical, superseded, **not deleted** | `gsd-x`, `integrate/gsd-x-landing` | `a3411c9`, `42dd006` |

Neither historical branch is deleted: they cost nothing, they carry authored history, and
deleting them would destroy the only record that they were once separate.

## How `main` was advanced

`main` was 23 commits behind and **0 ahead**, and was checked out in no worktree — verified
against `git worktree list --porcelain`, with the primary tree on the development branch and
the three others on `gsd-x`, `ucr-cif/construction` and a detached commit. So the ref could be
moved without any working tree being involved, and **none of the 416 foreign dirty paths in
the main checkout could be absorbed**.

The move used the **compare-and-swap** form, which asserts the old value:

    git update-ref refs/heads/main <new> <old>

The single-argument form is unconditional. It would move `main` to a non-descendant just as
happily, leaving the local branch disagreeing with a remote that then rejects the push. The
three-argument form cannot: if anything had moved `main` between the check and the write, the
write fails. Ancestry was verified separately with `merge-base --is-ancestor` before the swap.

No force. No history rewritten. No branch deleted.

Verified after: `origin/main` = `ada05e2`, and `merge-base --is-ancestor HEAD origin/main`
returns 0.

## Required gates at the moment of release

    dataset gate   10/10  exit 0
    drill          10/10  exit 0   (both poles)
    GSDX suite     14/14  exit 0
    reconciler      0 findings, exit 0

## CI enforcement — `EXTERNAL_GITHUB_ENFORCEMENT_PENDING`

`.github/` **does not exist** in this repository. There are zero workflows and no branch
protection, so nothing enforces the gates above at merge time; today they are enforced by the
release step running them, which is operator discipline rather than structure.

This is **not** fabricated as protection, and no workflow was invented to look like coverage.
The exact gap:

- **Required checks that should gate `main`:** `tools/test_gsd_x_dataset.py` (both `main()`
  and `--drill`), `tools/test_gsd_x.py`, `tools/gsd_x_claim_reconcile.py`.
- **What is needed:** a workflow invoking those four, plus branch protection on `main`
  requiring them.
- **Why it was not done here:** creating branch protection is a repository-administration
  change on an external service, outward-facing and not covered by the authority granted for
  this session. It is recorded rather than performed.

The repository's delivery model is deliberately local-first, so the minimum mechanism that
prevents constitutional regression is the in-repo executable check — which now exists and is
red on real defects, as the dependency ratchet demonstrated by refusing this wave's own
unpinned claim.
