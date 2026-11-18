---
covers: [cdio-10-publish-gate, legal-deploy-gate, legal_deploy_gate, legal-demote-single-page]
tier: T2
owner_decision: "Owner 2026-11-18 'y' to: add CDIO-10 to the deploy gate first, then demote the legal floor to major in the design review of a single page"
---
# CDIO-10 at publish time + legal floor demoted for a single page

## Problem (measured 2026-11-18)
- CDIO-10 (`modules/cdio/legal_surface.py`) blocks website done by Owner decision (spec cdio-10-legal-surface.md,
  2026-10-08: "blocks done"). Its only live caller is `cdio-reviewer`, i.e. the DESIGN review. Nothing checks it when a
  site is published (grep: legal_surface is called by cdio-reviewer, backlog_autopilot/webslice, asc_baseline_evidence).
- GEX44 SaaS rerun (data f75143b1): a single landing page built to a brief that named no site was recorded BLOCK 0 by
  three `legal-page-present` criticals (privacy, terms, DPA). The agent rightly refused to invent legal text, so the
  design done-gate could never pass, and its re-blocks were spent on something outside the brief.
The legal floor belongs where a site becomes public. It may leave the design review of a single page only once it
is enforced there.

## Build
1. `tools/legal_deploy_gate.py` (logic + CLI, stdin payload): for a web-publish command, resolve the site root
   (`--cwd <dir>` arg, else a leading `cd <dir> &&|;`, else the payload cwd), find `.cpp-legal.json` walking up from it:
   - absent -> DENY: "declare the jurisdiction" with the exact file to write;
   - `{"exempt": "<reason, >= 15 chars>"}` -> allow, ledgered (the escape is a written, committed reason);
   - `{"jurisdiction": "us|eu|es", "saas": bool, "b2b": bool}` -> `legal_surface.check`; any critical fail -> DENY
     listing them with the template to build from; else allow.
   Ledger `~/.claude/state/legal_deploy/ledger.jsonl` (override `CPP_LEGAL_DEPLOY_STATE_DIR`); fail-open with the
   error ledgered; kill switch `CPP_LEGAL_DEPLOY_GATE=off`.
2. `hooks/legal_deploy_gate.js` (PreToolUse-Bash-chain, which also receives PowerShell): pure-node prefilter; spawns
   python only when the command, with heredoc / here-string bodies elided, starts a production web publish:
   `vercel ... --prod`, `netlify deploy ... --prod`, `firebase deploy` (not `--only` without hosting),
   `wrangler pages deploy`, `gh-pages -d`, `surge`; each at a command position (line start, after ; & |, or after
   npx / pnpm [dlx] / yarn / bunx), so the words inside a commit message do not match. Deny shape =
   `permissionDecision:'deny'` (never `continue:false`, see cascade_check_bash.js defect 1).
3. `tools/design_review_record.py`: when every recorded file sits in one directory tree that holds exactly ONE html
   page and no package.json (a single page, not a site), reviewer verdicts `legal-page-present`,
   `legal-fields-filled`, `legal-page-linked` that fail as critical are recorded as major, named in the row
   (`legal_demoted`). A real site (2+ pages or an app) keeps the critical floor in the design review too.
4. `vault/agents/cdio-reviewer.md` (+ live copy): says so.

## Acceptance (V-LDG-*, tools/test_legal_deploy_gate.py; V-DSR additions)
- SILENT-NON-DEPLOY: `git commit -m "vercel --prod later"`, `npm test`, `vercel dev` -> nothing, python not spawned.
- DENY-UNDECLARED / DENY-MISSING-PAGES (es, names privacidad / aviso-legal) / ALLOW-COMPLETE (filled + linked site)
  / ALLOW-EXEMPT / REFUSE-SHORT-EXEMPT / POWERSHELL (tool_name PowerShell) / CWD-ARG (`--cwd site`) / KILL /
  FIREBASE-FUNCTIONS-SILENT / HEREDOC-SILENT / WIRED (repo dispatcher Bash chain).
- V-DSR-RECORD-LEGAL-DEMOTED-SINGLE-PAGE (a single page with the three legal criticals can be APPROVE) and
  V-DSR-RECORD-LEGAL-KEPT-FOR-SITE (two pages: still BLOCK).

## Honest limits
- A deploy that does not pass through a shell command this session runs (git-integration auto-deploys on push, CI,
  a dashboard button) is not seen. Preview deploys are not gated.
- The check is static (CDIO-10's own limits); it proves pages exist, are filled and linked, not that they are lawful.

## Rollback
`CPP_LEGAL_DEPLOY_GATE=off`, or delete the dispatcher line; revert the recorder hunk to restore the critical floor in
the design review.
