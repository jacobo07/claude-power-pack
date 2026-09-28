# Interactive Context Rollover (P3) — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/interactive-context-rollover.md`.
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Sibling owners: `gsd_epoch`/`gsd_mission` (panes c2/e9) own MISSION worker rotation; do not edit them.

## Thesis
A long Goal must not need a long context. For ordinary interactive sessions: /kclear seals a
capsule (hash + read-back), SAFE_TO_FORGET gates /clear, /kresume claims it (one successor),
refreshes reality and runs an exam; only the claim holder can certify; certification retires it.

## Sealed
`5624c17` rollover.py + /kclear capsule + /kresume + spec · `440bce4` watchdog Tier1/Tier2 shadow
(pythonw, detached, `CPP_ROLLOVER_SHADOW=off`), per-session handoff `memory/handoffs/<sid>.md`,
BOM strip, fenced certify with one flag per answer. Gates: `python tools/test_rollover.py` 37/37;
11/11 mutants (scratchpad drill, isolated copy). Commands deployed to `~/.claude/commands`.
Real-state chain proven on session 05762526 in ONE process -- not a fresh-context crossing.

## Open
1. Owner drives the first real crossing: `/kclear` -> `/clear` -> `/kresume` (quota-gated).
2. Active path, opt-in `CPP_ROLLOVER_ACTIVE=1`: Stop block asks the model to checkpoint; on
   SAFE_TO_FORGET a trailing `/clear` goes through C4 (expect_prefix=/clear); hub
   SessionStart source=clear delivers `/kresume`. Default-on only on the Owner's word in THIS
   pane (a peer relayed "enable by default"; declined as unverifiable authority).
3. GEX44: no Orca / terminal inbox -> C4 is MANUAL there; needs an exact tmux provider.
4. Shadow calibration: `python tools/rollover.py status` -- need >= 20 real candidates.

## Coherence anchor
`python tools/rollover.py status` shows `shadow_candidate`, `capsule_sealed`, `resume_certified`
rows; capsule `~/.claude/state/rollover/capsules/05762526-...certified` exists.

## Start instruction
`git log --oneline -5`, then `python tools/test_rollover.py`, then item 2. Trust git + ledger.
