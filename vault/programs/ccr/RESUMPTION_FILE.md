# RESUMPTION_FILE: ccr (CPP Cognitive Runtime as a Claude Code mod)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(shared tree, 1000+ foreign dirty files: pathspec-scoped commits only). Goal `ccr`, cap 36,880,000; at 2026-10-12
~12:00 used 5,171,864, remaining 31,708,136 (`goal-status`). The approved 66.2M raise stays unapplied: not needed.
Plans: `vault/plans/ccr-v2-enforcement-2026-10-11.md` + `ccr-v2-addendum-2026-10-11.md` + **`ccr-v2-addendum-umvm-2026-10-12.md`**
(multimodal addendum: liveness model, measurements, experiment arms).
**Owner: session c13cda65** (took over from 8f164910 on 2026-10-12; do not run both).

**State (coherence anchor: HEAD contains 226fcc12 "feat(ccr M1)").**
- SEALED: S1 369593ab, S2 1a0a62da, S3 781c4809, S4 51bbfc3b, **M1 226fcc12** (mod: `session.append` row receipt by
  door/modality, image hash + w*h + tokens; `turn.step` per-call ctx; rotate advice at `<state>/advice/<sid>.json`
  when carry above floor >= floor; observe only). Installed release is still 0.1.0-feaae8b0 (M1 is dev-only).
- S4 negative knowledge (do not reopen without new evidence): system prompt / per-tool guidance is not dominant.
- **Image cost truth (M2)**: tokens = ceil(w*h/750) as sent, no MP cap on Opus 5.5 (2000x1278 measured ~3,420).
  Madzia d6343597: image carry **16.8 %** (not 55 %: that was inferred), floor 31.4 %, text carry ~52 %.
  Same-bytes re-read is billed again in full. Live proof sid ea47d9c4: mod ctx == provider usage 4/4.

**Active decisions.** Pixels are not the dominant rent; text transcript growth is. Epoch rotation (arm B) sheds
both and leads (model: 36-45 % for 2-3 epochs per 26-call boundary, UNMEASURED). Visual subagent (C) fails Proof of
Agent Necessity on these numbers. Live pixel GC via plugin `session.compact` (D) is UNTESTED and caps at ~14 %.

**Next 3 actions.**
1. Arm B, measured: at a Madzia driver boundary (driver `boundary.py run` pid 19448 + worker 47480 p4p2a2 were live
   at 10:05; never touch KSR files while it runs), split one boundary at the CCR advice point; compare tokens per
   accepted transition and reviewer verdict vs A (d6343597 baseline, no re-run). Load the dev mod via --plugin-dir.
2. If B wins at reviewer parity: release M1 (`tools/ccr_release.py`), wire the driver to read the advice file.
3. Optional D probe (fixture only): does a `session.compact` plugin kept-set physically drop image blocks?

**Start.** `python tools/mission_spend.py goal-status --goal ccr`, check pid 19448, then action 1.
