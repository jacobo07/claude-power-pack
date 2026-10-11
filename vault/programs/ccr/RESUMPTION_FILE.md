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

**Carry, measured (2026-10-12, `evidence/carry_decompose.py` on worker d6343597, 26 calls, 1,192,066 tok).**
Model-facing carry: Read **images 55 %** (13 images; ~3K tok each makes the total reconcile with 1.19M, inferred) ·
assistant tool_use 18 % · Read text 8 % · hook_additional_context 6 % · PowerShell 5 %. `prompt_snapshot`,
`hook_success`, `hook_cancelled` rows are transcript-only (absent from the CCR attachment receipt) — exclude them.
`session.append` contract (d.ts L4366, L10564-10701): a rewrite of `content` is what is stored AND sent; the
structured tool record stays raw in the transcript (Law 15 holds by host); `hook-context` is a door.

**Active decisions.** v2 §4.1 (text tool-result projection) addresses ≤14 % of carry → demoted. The lever is
image carry: an image is re-read by every later call. Do not polish deferred_tools_delta (~800 tok) first.

**Next 3 actions.**
1. Intra-epoch governor, measurement leg (mod only, observe): per-row receipt at `session.append` (door, bytes,
   image count) + per-call usage → carry curve live, no transcript parsing.
2. Image-carry policy, decide by EVC: rotate the epoch after an image verdict is written (driver cadence fed by a
   CCR `rotate` advice file) vs inspect images in a subagent that returns words. Quality = Madzia reviewer parity.
3. Madzia R4 only at a driver boundary; KSR `boundary.py`/`ctx_ablation.py` only when clean and the driver stopped.

**Start.** `python tools/mission_spend.py goal-status --goal ccr`, `python tools/ccr_release.py status`, then action 1.
