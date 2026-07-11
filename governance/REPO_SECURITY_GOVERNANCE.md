# REPO_SECURITY_GOVERNANCE.md — Private by default

> Normative. Domain: all projects. Origin: Jacobo portfolio security audit, 2026-07-11
> (23 proprietary repositories were found public).

## The rule
A repository holding proprietary code, business logic, datasets, or internal governance is
PRIVATE from its first commit. Public is an ACTIVE decision, never the default.

## What may be public
Only: open-source libraries, community tools, and projects explicitly intended for the
community. Everything else is private. Forks of third-party open-source projects are the
Owner's call — surface them, do not assume.

## Pre-commit security checklist (mandatory)
- [ ] Grep the staging area for PII (phone, email, national-ID patterns). Hits →
      sanitize before commit. (Origin: the portfolio's first commit staged a third
      party's phone number in a planning document.)
- [ ] Grep the staging area for secrets and tokens (keys, connection strings). Hits →
      remove and rotate.
- [ ] Confirm `.gitignore` covers `.env*`, `node_modules/`, `.next/`, `.vercel/`,
      `_logs/`, and OS/editor files.
- [ ] Decide the Co-Authored-By trailer BEFORE the first public or investor-facing commit.
      On an investor-facing repository, a visible AI-tool co-author trailer can read as
      "did not build this alone" — decide with the Owner whether to keep or clean it.
      (Origin: portfolio commit history.)

## Commit hygiene on a shared or multi-pane worktree
- Never `git add -A`. Stage explicit paths. Scope every commit with a trailing
  `-- <pathspec>` so another pane's staged files are never packaged under your message.
- `git fetch && git status` before starting; if behind, `git pull --rebase`.

## Applies to
Every project, every first commit.
