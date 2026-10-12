# RESUMPTION_FILE: prr (Physical Runtime Working Set)

**Identity.** Claude Power Pack worktree `C:\Users\User\Apps\pp-prr`, branch `prr/main` (off 983cca18). Goal `prr`,
cap 18,000,000. Plan + Owner decision: `vault/plans/prr-physical-working-set-2026-10-12.md`. Coordinator pane ce64704d.
Sibling programme `ccr` is owned by pane c13cda65: read its files, never write them.

**Thesis.** The laptop's RAM pressure comes from how many claude.exe are alive (33 main sessions x ~0.85 GB private),
not from session age (fleet r = 0.18). Within one session, growth follows context. The target architecture is a
logical session recycled across disposable physical processes (seal -> stop -> `--resume <sid>`), built on the
existing FASE A (`modules/cognitive_os/process_governor.py` + `hibernate_runner.py` + kclaude park/resume).

**State (coherence anchor: the commit that adds this file).** SEALED: reality scan, plan, Owner approval.
PENDING: everything from A0.

**Active decisions.** Laptop = read-only census, no new claude.exe, no trimmer. Canaries and benchmarks on GEX44.
Destructive actions only on processes this programme started. Every number names its plane.

**Next 3 actions.**
1. A0: read-only Windows census tool (per process tree: private, working set, parent, role, age) with a test
   that drives both a known-orphan and a known-live classification.
2. A1 on GEX44: identify the JS engine inside claude 2.1.296 (V8 vs JSC) and probe the Mods surface for any
   heap, process or MCP lifecycle API.
3. B on GEX44: hard resident floor for a fresh `claude -p` session plus a long-run synthetic fixture.

**Start.** `python tools/mission_spend.py goal-status --goal prr`, then action 1.
