# PORTFOLIO_LEARNINGS.md — Confirmed patterns from the Jacobo portfolio + Hermes sessions

> Each entry: what happened · what was learned · rule derived · where it applies.
> These are specific and actionable. A learned pattern is added here the same session it
> is discovered — zero knowledge debt. Governance files in `../governance/` enforce the
> rules; this ledger records their origin.

---

## LRN-01 — Humanized copy is a production gate
- What happened: the portfolio's copy exposed terms like "stack", "Next.js", "framework",
  "LLM" to non-technical end users (a restaurant owner, an investor).
- What was learned: for a non-technical audience, technical vocabulary in visible copy is a
  defect, not a style preference.
- Rule: before any deploy that changes copy, grep the SERVED HTML for the banned-term list;
  BLOCK on any visible hit. Formalized as gate V-COPY-01.
- Applies to: any project with an end-user interface — portfolios, landing pages, products
  for non-technical users. See `../governance/COPY_GOVERNANCE.md`.

## LRN-02 — RESUMPTION_FILE for multi-session work
- What happened (Hermes): `/compact` was announced as text but never executed; context
  filled without emptying.
- What was learned: a slash command printed as assistant text is inert. Continuity across
  sessions must be state written to disk.
- Rule: any task longer than one session keeps a `RESUMPTION_FILE.md` at the root — a
  self-contained execution prompt, under 400 words, imperative, updated after every sealed
  unit (not at the end), written proactively at ~65% context.
- Applies to: any multi-day project or compendium of >10 units. See
  `../governance/SESSION_CONTINUITY_GOVERNANCE.md`.

## LRN-03 — FIOS / IRR / FD-07 cross-contamination
- What happened: the Stop hook emitted CommonWealth Ops / Power Pack vocabulary (FIOS, IRR,
  FD-07, FD flywheel, PP_SESSION_OBJECTIVE) in Hermes and the portfolio, where those
  concepts do not exist.
- What was learned: these are REAL Power Pack modules; their vocabulary bleeds through the
  shared Stop hook into unrelated projects, where it is noise.
- Rule: in a non-CW-Ops / non-Power-Pack project, treat these terms as a false positive —
  ignore, do not build any related ledger or asset, spend ≤2 minutes, document in the
  project's `CLAUDE.md`.
- Applies to: every project that is not CW Ops. See `../governance/KNOWN_FALSE_POSITIVES.md`.

## LRN-04 — Next.js allowBuilds must be set before a Vercel deploy
- What happened: Regina and the portfolio both shipped a `pnpm-workspace.yaml` whose
  `allowBuilds` entries held instructional non-boolean text; the build passed locally but
  failed on Vercel.
- What was learned: pnpm 11 blocks native-dependency builds unless `allowBuilds` holds real
  booleans; the local install can hang without a TTY when it wants to rebuild them.
- Rule: before deploying a Next.js project, set each native dep (sharp, unrs-resolver,
  @swc/core, @parcel/watcher) to `true`, reinstall with `CI=true`, confirm the local build
  exits 0, then deploy.
- Applies to: any Next.js project deployed to Vercel. See `../governance/DEPLOY_GOVERNANCE.md`.

## LRN-05 — Reality before deploy
- What happened: Deng Chaowei's store needed a real database plus payment and email keys to
  function, and blocked iframe embedding by design. A bare deploy would have shipped a
  broken store; instead the store runs in a safe test-payment mode with no real charges.
- What was learned: honoring a "deploy it" instruction blindly can ship something worse than
  not deploying. The Reality Contract outranks checking the deploy box.
- Rule: before deploying a client project, verify it works without unconfigured external
  dependencies — or keep an honest static preview that promises nothing it cannot do.
  Surface the trade-off to the Owner rather than shipping a broken surface.
- Applies to: any project with non-trivial external dependencies (payments, email, database).
  See `../governance/DEPLOY_GOVERNANCE.md`.

## LRN-06 — Repositories are private by default
- What happened: a security audit found 23 of the Owner's proprietary repositories public.
- What was learned: leaving proprietary code public is a standing risk; public must be a
  deliberate act.
- Rule: any repository with proprietary code, business logic, datasets, or internal
  governance is private from its first commit. Public is reserved for open-source libraries
  and community tools, decided actively.
- Applies to: every project. See `../governance/REPO_SECURITY_GOVERNANCE.md`.

## LRN-07 — PII in planning documents
- What happened: the portfolio's first commit staged a third party's (VeloxGear) phone
  number inside a planning document.
- What was learned: PII leaks through planning/registry docs, not just the UI — the staging
  area is the real perimeter.
- Rule: before the first commit of any project that processed third-party data, grep the
  staging area for PII patterns (phone, email, national-ID). Sanitize before committing.
- Applies to: any project handling client or third-party data, planning docs included. See
  `../governance/REPO_SECURITY_GOVERNANCE.md`.

## LRN-08 — Co-Authored-By on investor-facing repos
- What happened: portfolio commits carried an AI-tool "Co-Authored-By" trailer on a repo
  meant to impress investors.
- What was learned: on an externally-visible history, an AI-tool trailer can read as "did
  not build this alone" — a positioning risk, not just a formality.
- Rule: before connecting a repo to hosting or making its history visible to investors or
  clients, review the commit history and decide with the Owner whether to keep or clean the
  trailers.
- Applies to: portfolios, investor decks, any repo with externally-visible history. See
  `../governance/REPO_SECURITY_GOVERNANCE.md`.

## LRN-09 — Credential discovery before a headless deploy
- What happened: an expired `VERCEL_TOKEN` in the environment masked the valid CLI session
  during a headless deploy.
- What was learned: a stale env token silently overrides a working CLI login; the first
  `whoami` is the cheap tell.
- Rule: for a headless deploy, prefer the CLI's native session (`vercel whoami`) over reading
  credential files. If the first `whoami` fails, clear env vars that could mask the native
  session before hunting for tokens.
- Applies to: any project with a headless deploy to Vercel or similar. See
  `../governance/DEPLOY_GOVERNANCE.md`.

## LRN-10 — gh CLI needs git on PATH (Windows)
- What happened: `gh` operations failed with "not a git repository" on a valid repo on this
  Windows host.
- What was learned: `gh` shells out to the native `git`, not a bundled one; if git is not on
  PATH, `gh` misreports the repo as invalid.
- Rule: on Windows, prepend Git's `cmd` directory to PATH before using `gh`. A "not a git
  repository" error on a valid repo is a PATH problem, not a repo problem.
- Applies to: any Windows project using `gh` CLI.
