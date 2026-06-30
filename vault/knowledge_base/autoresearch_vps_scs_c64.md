# SCS C64 -- AutoResearch-on-VPS by default (sealed 2026-06-30)

**Doctrine:** Automated research/scraping runs on the KobiiClaw VPS, never
interrupts the Owner's local sessions. Results are PULLED into SessionStart
(detached, TTL-gated, additionalContext -- not a blocking message). Agent-Reach
is the internet-access layer for the channels it covers; for a headless pipeline
that means its credential-free PRIMITIVES (Jina Reader + yt-dlp), not its
agent-facing CLI. Social-automation credentials use dedicated accounts, never the
Owner's, and never live in the repo.

Cross-refs: PR-RESEARCH-OFFLOAD-VPS-001, T-DEDICATED-ACCOUNTS-001,
T-AGENT-REACH-AGENT-FACING-001 (ukdl-universal.md);
vault/plans/autoresearch-vps-migration-2026-06-30.md.

## What shipped (3 blocks)

**Block A -- hung-window audit (EXECUTION).** Root cause was NOT hooks (F0 already
fixed those) but Scheduled Tasks running `LogonType=InteractiveToken` with console/
unhidden launchers. Fixed 7 PP tasks (5 python.exe -> pythonw.exe; 2 PowerShell
+ -WindowStyle Hidden). Extended `tools/audit_spawn_windows.py` with a `--schtasks`
gate (HR-001 honest scoping). Gate: `SPAWN_WINDOW_AUDIT_PASS=42/42 schtask_owned_fails=0`.
4 non-PP tasks (CostaLuz/Kobii/LaptOps) flagged advisory, left for the Owner.
Doc: vault/lessons/schtasks-interactive-token-window-flash.md (T-SPAWN-WINDOW-002).

**Block B -- AutoResearch -> VPS.** Engine (`nightcrawler.py` + rss/youtube/
cross_signal/signal_scorer + config) runs on KobiiClaw `204.168.166.63` in an
isolated venv via cron `0 2,8,14,20 * * *` (self-throttled 6h). Local Stop hook
silenced (no systemMessage). SessionStart hub gained Hook 12: inline cache read ->
additionalContext + detached windowsHide TTL-gated scp. Verified: VPS run 7.7s
33->6+2 signals; hub pull lands cache + surfaces digest.

**Block C -- Agent-Reach enrichment.** Installed Agent-Reach v1.5.0 on the VPS
(dedicated venv; from GitHub zip -- NOT PyPI). Credential-free channels verified:
Jina web reader (live test OK), RSS, yt-dlp (installed). Added an additive,
fail-open, footprint-bounded enrichment stage (`modules/autoresearch/enricher.py`):
top-N accepted signals get Jina full-text (web/RSS) or yt-dlp transcripts (YouTube);
discovery untouched. Live run: 5 signals enriched with real Jina text. Twitter/
Reddit deferred (need dedicated-account cookies -- T-DEDICATED-ACCOUNTS-001).

## Done-gate

`python tools/test_autoresearch_vps.py` -> `AUTORESEARCH_VPS_PASS=5/5` on all 3
hermetic runs (V-VPS-NO-LOCAL-INTERRUPT, V-PULL-MECHANISM, V-AGENT-REACH-ENRICH,
V-CREDENTIALS-NOT-IN-REPO, V-BASELINE-INTACT).

## Operational notes

- VPS disk freed 95%->83% via `docker builder prune` (14.8 GB) + dangling image
  prune. 31 GB of unused Docker volumes left untouched (data-risk; Owner decision).
- Optional later: Twitter/Reddit (dedicated cookies), GitHub (`apt install gh`),
  Exa global search (`npm i -g mcporter`, node v22 already present).
