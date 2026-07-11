# governance/ — Normative rules for every Claude Power Pack project

These files are NORMATIVE, not suggestions. Any project that uses Claude Power Pack obeys
them from its first commit. They are written in imperative voice for Claude Code to read in
a future session, in any project, and know exactly what to do and what not to do. Every
rule cites the real incident that produced it — no generic advice.

## The files (one domain each)
| File | Domain | Read it before… |
|---|---|---|
| `COPY_GOVERNANCE.md` | End-user copy | any deploy that changes user-visible strings |
| `DEPLOY_GOVERNANCE.md` | Production deploys | any deploy to production |
| `REPO_SECURITY_GOVERNANCE.md` | Repository security | the first commit of any project |
| `SESSION_CONTINUITY_GOVERNANCE.md` | Multi-session work | starting any multi-day task |
| `KNOWN_FALSE_POSITIVES.md` | Hook noise | investigating any hook/gate signal |

## How to use in a new project
1. Clone or reference `claude-power-pack`; point the new project's `CLAUDE.md` at this
   folder.
2. Before the first commit: apply `REPO_SECURITY_GOVERNANCE.md`.
3. Before any deploy: apply `DEPLOY_GOVERNANCE.md` (and `COPY_GOVERNANCE.md` if copy changed).
4. On any long build: apply `SESSION_CONTINUITY_GOVERNANCE.md`.
5. On any confusing hook signal: check `KNOWN_FALSE_POSITIVES.md` FIRST.

## Standing obligations (zero knowledge debt)
- A new false positive is added to `KNOWN_FALSE_POSITIVES.md` the same session it appears.
- A new learned pattern is added to `../knowledge/PORTFOLIO_LEARNINGS.md` the same session
  it is discovered. Knowledge is captured where it is learned, never accumulated as debt.
- Governance is the FIRST artifact of any new project, not an afterthought.
