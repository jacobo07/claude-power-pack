# Handoff to the gsd_mission / capsule-v2 owner: a pooled daemon pid blocks relay

From: Cognitive Economy gen 2 (TOK-18 v2), W2. Evidence: `../evidence/W2.md`.

Defect: when the Claude daemon hosts a background worker inside a pooled `claude bg-spare` process, a
host `done` row leaves that pid alive as a spare. The stop path refuses to kill it ("argv is not this worker"),
which is right, and then refuses to relay forever, which is wrong. Live instance: GEX44 mission
`m-f011d7fdebc9` (E1, Owner-authorized), first refusal 2026-10-05T10:04:18Z, repeating every pass.

Asked of the owner:
1. Released-not-killed branch for daemon pooled processes (semantics and three tests in `../evidence/W2.md`).
2. G23 stays green unchanged.
3. Deploying the fix to the GEX44 clone (`~/.claude/skills/claude-power-pack`, at `339ccaa9`) is a live-server
   change: Owner decision, read the DEPLOY hard-rules class first.

Reopen condition for gen 2: E1 relays again (sweep line for `m-f011d7fdebc9` with `action` other than `replace`
plus a new epoch), at which point W3 resumes.
