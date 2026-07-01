# kClaude Cursor Profile + "Last session" Routing -- 2026-07-01

Status: **Shipped + verified** (P2 functional; P1 already-correct, Owner reload pending)
Mode: EXECUTION · Follows fec5c3a (startup fix)

## Two bugs

- **BUG 4:** kClaude profile not visible in the "+" menu.
- **BUG 5:** "Last session" doesn't route through the smart wrapper -> CO inactive.

## PASO -1 findings (primary source: %APPDATA%\Cursor\User\settings.json)

- **kClaude profile ALREADY EXISTS** (settings.json, key `" kClaude"`): args ->
  `bin\kclaude.cmd` -> `bin\kclaude.ps1` (smart W6 wrapper, CO active); icon
  `sparkle`, color `terminal.ansiMagenta` -- byte-identical to the Claude profile.
- **Sort verified (Node):** `" kClaude".localeCompare("Claude") = -1`. Cursor's
  `_sortProfileQuickPickItems` pins the default ("Last session") first, then sorts
  the rest alphabetically -> menu order **Last session / kClaude / Claude / ...**.
- **"Last session"** (settings.json:170) runs `lazarus-shell-autoresume.bat`, which
  resolved the session then launched the OLD `kclaude.bat` (no CO). BUG 5.
- kclaude: `~/.claude/bin/kclaude.ps1` (via `bin\kclaude.cmd`, 86 B).
- All touched files (settings.json, lazarus .bat) are GLOBAL, none in the repo.

## Premise correction (audit-disproves-premise)

**BUG 4 is already fixed in config.** The profile exists and sorts correctly;
the only reason the Owner doesn't see it is Cursor has not reloaded its window
since the profile was added earlier today. Re-adding it would risk a duplicate.
-> No settings.json edit. Action = **Owner reloads Cursor** (Ctrl+Shift+P ->
"Reload Window"). Contingency: if it still doesn't appear post-reload, the
leading-space key is the suspect (Cursor menu renderer) -- switch keys then.

## Fix (P2, BUG 5)

`~/.claude/hooks/lazarus-shell-autoresume.bat` (backed up
`.bak.20260701T131500Z`): the resume launch AND the doskey fallback now prefer
`bin\kclaude.cmd` (smart wrapper), falling back to `kclaude.bat` then bare
`claude`. Covers "Last session" + slots 1/2/3. Preserves lazarus crash-recovery /
termkey resolution; the smart wrapper honors the explicit `--resume <sid>`.

## Verification (observed)

- Batch nested-if structure: throwaway test -> LAUNCH=bin, DOSKEY=bin, STRUCTURE-OK.
- Real .bat ran in an empty dir / crash-only mode (NEXT empty -> doskey block ->
  goto :eof, no claude launch): **exit 0, no parse-error markers**.
- Static read: both edited blocks paren-balanced; old MC-LAZ-26 comment intact.
- Node sort sim: `Last session / kClaude / Claude / Claude (VPS) / ...`.

## Seal

- UKDL: T-CURSOR-PROFILE-ORDER-001 + T-LAST-SESSION-SMART-WRAPPER-001 + SCS C49 v2.

## Out of scope / follow-ups

- "Claude" profile keeps the old kclaude.bat (the legacy button, by design).
- "Last session (PS)" uses lazarus-shell-autoresume.ps1 (not edited) -- follow-up
  if the Owner uses the PS variant.
- Owner visual gate: reload Cursor, open "+", confirm Last session / kClaude /
  Claude; click kClaude -> prompt < 3s; open a "Last session" terminal -> CO active.
