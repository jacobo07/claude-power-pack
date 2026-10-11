# RESUMPTION_FILE: ccr (CPP Cognitive Runtime as a Claude Code mod)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(shared tree, 1000+ foreign dirty files: pathspec-scoped commits only). Goal `ccr`, cap 36,880,000 (Owner approved
p95 = 66.2M at 22:02 on 2026-10-11; the cap raise was never applied — apply only when the remaining runs short).
Canonical plan: `vault/plans/ccr-v2-enforcement-2026-10-11.md` + addendum `ccr-v2-addendum-2026-10-11.md`.
**Owner: session 8f164910** (took over from 93bd1001 on 2026-10-12 by Owner choice; do not run both).

**State (coherence anchor: HEAD contains 51bbfc3b "feat(ccr S4)").**
- SEALED: S1 369593ab (subagent linker), S2 1a0a62da (release tooling), S3 781c4809 (Work Unit tier: `CCR_WORK_UNIT`
  → class closure enforced on a main session), S4 51bbfc3b (system-prompt materialization receipt, observe only).
- Installed release is still 0.1.0-feaae8b0 (S3/S4 are dev-only; ablation arm U loads the dev copy via --plugin-dir).
- First call, KSR harness `CursorProjects/tools/kobiimii/ctx_ablation.py`, Opus: default 73,400 · lean E 10,407 ·
  U (stock flags + unit) 16,290 / 17,233 / 15,973 / 16,606 (MCP connect count drives a ~1.3K spread).
- U−E decomposed (receipts): kernel+index +4,817 chars (mandatory; E is underlinked) · deferred_tools_delta 4,307 ·
  advisory hook ctx +1,328 · engine rows +1,022 · ~3K tok = deferral cost (host has no tool removal). System
  prompt is only ~4.3K chars on Opus lean; compose-time tool narrowing measured useless and withdrawn.

**Active decisions.** First-call work is near its floor; the money is intra-epoch carry (~69 % of a Madzia epoch:
tool results, repeated hook context). Do not polish deferred_tools_delta (~800 tok, cache-read priced) before carry.

**Next 3 actions.**
1. P5 probe: does `session.append` rewrite a tool-result row before it is stored AND sent (incl. images)? Read the
   d.ts contract, then one bounded headless probe.
2. If P5 holds: ingestion projection for large tool results (raw to a sha page store, projection + handle in the
   row), unit sessions first, with a page-fault path and a multi-call benchmark (8–15 calls) before/after.
3. Madzia R4 only at a driver boundary (worker pid 17144 was live at 22:19); KSR files only when clean.

**Start.** `python tools/mission_spend.py goal-status --goal ccr`, `python tools/ccr_release.py status`, then action 1.
